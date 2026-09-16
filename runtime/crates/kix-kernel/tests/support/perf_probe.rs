//! Memory-only, single-driver measurement apparatus. No backend or authority implementation.
use std::fmt::Write as _;
use std::time::{Duration, Instant};

use kix_kernel::{
    CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, Limits,
    ObservationOutcome, ProviderOperation, Reserve, ReserveOutcome, Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

#[derive(Clone, Copy, Debug)]
pub enum Workload { Uniform, HotSeat, Retry, Conflict }

impl Workload {
    pub fn name(self) -> &'static str {
        match self {
            Self::Uniform => "uniform", Self::HotSeat => "hot-seat",
            Self::Retry => "same-command-retry", Self::Conflict => "retained-conflict-growth",
        }
    }
}

fn id(number: u64) -> KixId {
    let mut value = [0_u8; 16];
    value[..8].copy_from_slice(&number.to_le_bytes());
    KixId::from_bytes(value)
}

fn context(time: u64) -> Context {
    Context {
        fence: ExecutionFence { owner: id(90), generation: 1 },
        now_ms: time, semantics_version: 4,
    }
}

fn request(number: u64, seat: u16) -> Reserve {
    Reserve {
        id: CommandId { scope: id(80), principal: id(81), request: id(number) },
        order_id: id(number + 10_000), expected_business_epoch: 1,
        selection: Selection::Seats { first: seat, count: 1 },
        amount: AssetAmount::checked(
            AssetId::from_bytes([10; 32]), 1_000, u128::MAX,
            RegistryVersion::new(1).unwrap(), Hash32::from_bytes([11; 32]),
        ).unwrap(),
        quote_hash: Hash32::from_bytes([12; 32]), policy_hash: Hash32::from_bytes([13; 32]),
        expires_at_ms: u64::MAX,
        payment: ProviderOperation { provider: id(82), account: id(83), operation: id(number) },
    }
}

#[derive(Clone)]
enum Input { Reserve(Reserve), Capture(CaptureObservation) }

pub struct Report {
    pub workload: &'static str,
    pub total: usize,
    pub held: usize,
    pub replay: usize,
    pub rejected: usize,
    pub capacity: usize,
    pub other: usize,
    pub first_capacity: Option<usize>,
    pub remaining: u32,
    pub elapsed_ns: u128,
    pub p99_service_ns: u128,
    pub p99_scheduled_latency_ns: u128,
    pub raw_csv: String,
}

fn percentile(values: &mut [u128], numerator: usize) -> u128 {
    values.sort_unstable();
    values[(values.len() * numerator).div_ceil(100).saturating_sub(1)]
}

/// rate=0 explicitly means a service-time microbenchmark, not an open-loop test.
/// rate>0 uses deadlines relative to a fixed origin. A late driver never shifts
/// the original deadline forward to hide queue delay (coordinated omission).
pub fn run(workload: Workload, count: usize, command_limit: usize, rate: u64) -> Report {
    assert!(count > 0 && count <= 100_000);
    assert!(command_limit > 0);
    let mut kernel = Kernel::new(
        id(80), context(0).fence, 1, Inventory::seats(&[4096]).unwrap(),
        Limits { commands: command_limit.max(2), orders: 4096, observations: 128 },
    ).unwrap();
    let mut inputs = Vec::with_capacity(count);
    if matches!(workload, Workload::Conflict) {
        let a = request(1, 0);
        kernel.reserve(context(1), a.clone()).unwrap();
        let original = CaptureObservation {
            event_id: id(500), operation: a.payment, amount: a.amount,
            evidence_hash: Hash32::from_bytes([60; 32]),
        };
        kernel.observe_capture(context(2), original.clone()).unwrap();
        for i in 0..count {
            let mut value = original.clone();
            value.operation.operation = id(20_000 + i as u64);
            inputs.push(Input::Capture(value));
        }
    } else {
        for i in 0..count {
            let number = if matches!(workload, Workload::Retry) { 1 } else { i as u64 + 1 };
            let seat = if matches!(workload, Workload::Uniform) { (i % 4096) as u16 } else { 0 };
            inputs.push(Input::Reserve(request(number, seat)));
        }
    }
    let mut report = Report {
        workload: workload.name(), total: count, held: 0, replay: 0, rejected: 0,
        capacity: 0, other: 0, first_capacity: None, remaining: 0, elapsed_ns: 0,
        p99_service_ns: 0, p99_scheduled_latency_ns: 0, raw_csv: String::new(),
    };
    let mut rows = Vec::with_capacity(count);
    let mut service = Vec::with_capacity(count);
    let mut latency = Vec::with_capacity(count);
    let origin = Instant::now();
    for (index, input) in inputs.into_iter().enumerate() {
        let scheduled = if rate == 0 { 0 } else { (index as u128 * 1_000_000_000) / u128::from(rate) };
        if rate > 0 {
            let elapsed = origin.elapsed().as_nanos();
            if scheduled > elapsed {
                std::thread::sleep(Duration::from_nanos((scheduled - elapsed).min(u128::from(u64::MAX)) as u64));
            }
        }
        let start = origin.elapsed().as_nanos();
        let begin = Instant::now();
        let outcome = match input {
            Input::Reserve(value) => match kernel.reserve(context(index as u64 + 10), value) {
                Ok(applied) if applied.replayed => { report.replay += 1; "replayed" }
                Ok(applied) => match applied.original {
                    ReserveOutcome::Held(_) => { report.held += 1; "held" }
                    ReserveOutcome::Rejected(_) => { report.rejected += 1; "business_rejected" }
                },
                Err(kix_kernel::KernelError::Capacity) => { report.capacity += 1; "capacity" }
                Err(_) => { report.other += 1; "other_error" }
            },
            Input::Capture(value) => match kernel.observe_capture(context(index as u64 + 10), value) {
                Ok(ObservationOutcome::Conflict) => { report.other += 1; "conflict_retained" }
                Err(kix_kernel::KernelError::Capacity) => { report.capacity += 1; "capacity" }
                _ => { report.other += 1; "other_observation" }
            },
        };
        let duration = begin.elapsed().as_nanos();
        let end = origin.elapsed().as_nanos();
        if outcome == "capacity" && report.first_capacity.is_none() {
            report.first_capacity = Some(index);
        }
        let measured_latency = if rate == 0 { end - start } else { end.saturating_sub(scheduled) };
        rows.push((index, scheduled, start, end, duration, measured_latency, outcome));
        service.push(duration);
        latency.push(measured_latency);
    }
    report.elapsed_ns = origin.elapsed().as_nanos();
    report.remaining = kernel.remaining();
    report.p99_service_ns = percentile(&mut service, 99);
    report.p99_scheduled_latency_ns = percentile(&mut latency, 99);
    report.raw_csv.push_str("index,scheduled_ns,start_ns,end_ns,service_ns,scheduled_latency_ns,outcome\n");
    for (i, scheduled, start, end, duration, observed, outcome) in rows {
        writeln!(&mut report.raw_csv, "{i},{scheduled},{start},{end},{duration},{observed},{outcome}").unwrap();
    }
    assert_eq!(report.held + report.replay + report.rejected + report.capacity + report.other, count);
    report
}

impl Report {
    pub fn json(&self, rate: u64, command_limit: usize) -> String {
        format!(
            "{{\"workload\":\"{}\",\"scope\":\"memory-only single-driver; no durable TPS claim\",\"debug_assertions\":{},\"rate\":{},\"command_limit\":{},\"samples\":{},\"new_held\":{},\"replayed\":{},\"business_rejected\":{},\"capacity\":{},\"other\":{},\"first_capacity_index\":{},\"remaining\":{},\"elapsed_ns\":{},\"p99_service_ns\":{},\"p99_scheduled_latency_ns\":{},\"kernel_resets_during_workload\":0}}\n",
            self.workload, cfg!(debug_assertions), rate, command_limit, self.total, self.held,
            self.replay, self.rejected, self.capacity, self.other,
            self.first_capacity.map(|v| v.to_string()).unwrap_or_else(|| "null".into()),
            self.remaining, self.elapsed_ns, self.p99_service_ns, self.p99_scheduled_latency_ns,
        )
    }
}
