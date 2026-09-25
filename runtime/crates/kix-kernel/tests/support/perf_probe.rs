//! Memory-only, single-driver measurement apparatus. No backend or authority implementation.
//!
//! Summaries keep new-success, business-reject, same-command retry, Capacity, and
//! retained-conflict apart. Mixed nearest-rank p99 is labeled as a mixed-result
//! distribution and is not a purchase or product p99.
use std::fmt::Write as _;
use std::time::{Duration, Instant};

use kix_kernel::{
    CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, Limits,
    ObservationOutcome, ProviderOperation, Reserve, ReserveOutcome, Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

pub const INVENTORY_SEATS: usize = 4096;
pub const ORDER_LIMIT: usize = 4096;
pub const OBSERVATION_LIMIT: usize = 128;
pub const SCOPE: &str =
    "memory-only single-driver v4; not full-system, durable TPS, or product p99";
pub const NON_CLAIMS: &str = "no approved product TPS, p99, or fail-rate SLO; memory-only single-driver v4 is not full-system measurement; CI debug smoke is not production p99 or TPS; this apparatus does not compare PostgreSQL or select a backend";
pub const MIXED_P99_INTERPRETATION: &str =
    "mixed-result distribution across all call outcomes; not new-success, purchase, or product p99";
pub const GOODPUT_INTERPRETATION: &str = "integer new Held count times 1000000000 divided by elapsed_ns; memory-only workload-loop ratio; rate>0 includes scheduled waits; not product TPS";
pub const SERVICE_NS_MEANING: &str =
    "per-call kernel invocation plus outcome classification; no I/O";
pub const SCHEDULED_LATENCY_NS_MEANING: &str = "fixed scheduled arrival through completion; rate=0 uses the call-window delay and is not a separate queueing model";

#[derive(Clone, Copy, Debug)]
pub enum Workload {
    Uniform,
    HotSeat,
    Retry,
    Conflict,
}

impl Workload {
    pub fn name(self) -> &'static str {
        match self {
            Self::Uniform => "uniform",
            Self::HotSeat => "hot-seat",
            Self::Retry => "same-command-retry",
            Self::Conflict => "retained-conflict-growth",
        }
    }
}

/// Uniform control kept strictly under the command budget. Not a fifth kernel workload.
pub fn low_load_sample_count(command_limit: usize) -> usize {
    32.min(command_limit.saturating_sub(1)).max(1)
}

pub fn build_mode() -> &'static str {
    if cfg!(debug_assertions) {
        "debug"
    } else {
        "release"
    }
}

pub fn rate_meaning(rate: u64) -> &'static str {
    if rate == 0 {
        "service-time microbenchmark; not open-loop"
    } else {
        "fixed-origin i/rate schedule; a late driver does not shift the origin"
    }
}

#[derive(Clone, Copy, Debug)]
enum OutcomeKind {
    Held,
    Replayed,
    BusinessRejected,
    Capacity,
    ConflictRetained,
    OtherError,
    OtherObservation,
}

impl OutcomeKind {
    const ALL: [Self; 7] = [
        Self::Held,
        Self::Replayed,
        Self::BusinessRejected,
        Self::Capacity,
        Self::ConflictRetained,
        Self::OtherError,
        Self::OtherObservation,
    ];

    fn as_str(self) -> &'static str {
        match self {
            Self::Held => "held",
            Self::Replayed => "replayed",
            Self::BusinessRejected => "business_rejected",
            Self::Capacity => "capacity",
            Self::ConflictRetained => "conflict_retained",
            Self::OtherError => "other_error",
            Self::OtherObservation => "other_observation",
        }
    }

    fn role(self) -> &'static str {
        match self {
            Self::Held => "new-success",
            Self::Replayed => "same-command-retry",
            Self::BusinessRejected => "business-reject",
            Self::Capacity => "capacity",
            Self::ConflictRetained => "retained-conflict",
            Self::OtherError | Self::OtherObservation => "unclassified",
        }
    }

    fn index(self) -> usize {
        match self {
            Self::Held => 0,
            Self::Replayed => 1,
            Self::BusinessRejected => 2,
            Self::Capacity => 3,
            Self::ConflictRetained => 4,
            Self::OtherError => 5,
            Self::OtherObservation => 6,
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
        fence: ExecutionFence {
            owner: id(90),
            generation: 1,
        },
        now_ms: time,
        semantics_version: 4,
    }
}

fn request(number: u64, seat: u16) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(80),
            principal: id(81),
            request: id(number),
        },
        order_id: id(number + 10_000),
        expected_business_epoch: 1,
        selection: Selection::Seats {
            first: seat,
            count: 1,
        },
        amount: AssetAmount::checked(
            AssetId::from_bytes([10; 32]),
            1_000,
            u128::MAX,
            RegistryVersion::new(1).unwrap(),
            Hash32::from_bytes([11; 32]),
        )
        .unwrap(),
        quote_hash: Hash32::from_bytes([12; 32]),
        policy_hash: Hash32::from_bytes([13; 32]),
        expires_at_ms: u64::MAX,
        payment: ProviderOperation {
            provider: id(82),
            account: id(83),
            operation: id(number),
        },
    }
}

#[derive(Clone)]
enum Input {
    Reserve(Reserve),
    Capture(CaptureObservation),
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OutcomeSummary {
    pub outcome: &'static str,
    pub role: &'static str,
    pub count: usize,
    pub service_p99_ns: Option<u128>,
    pub scheduled_latency_p99_ns: Option<u128>,
}

pub struct Report {
    pub workload: &'static str,
    pub total: usize,
    pub held: usize,
    pub replay: usize,
    pub rejected: usize,
    pub capacity: usize,
    pub conflict_retained: usize,
    pub other_error: usize,
    pub other_observation: usize,
    /// Unclassified capture/reserve results. Excludes retained conflict.
    pub other: usize,
    pub first_capacity: Option<usize>,
    pub samples_after_first_capacity: usize,
    pub command_limit_requested: usize,
    pub remaining: u32,
    pub elapsed_ns: u128,
    pub mixed_p99_service_ns: u128,
    pub mixed_p99_scheduled_latency_ns: u128,
    pub outcomes: Vec<OutcomeSummary>,
    pub raw_csv: String,
}

fn percentile(values: &mut [u128], numerator: usize) -> u128 {
    values.sort_unstable();
    values[(values.len() * numerator).div_ceil(100).saturating_sub(1)]
}

fn classify(kernel: &mut Kernel, index: usize, input: Input) -> OutcomeKind {
    match input {
        Input::Reserve(value) => match kernel.reserve(context(index as u64 + 10), value) {
            Ok(applied) if applied.replayed => OutcomeKind::Replayed,
            Ok(applied) => match applied.original {
                ReserveOutcome::Held(_) => OutcomeKind::Held,
                ReserveOutcome::Rejected(_) => OutcomeKind::BusinessRejected,
            },
            Err(kix_kernel::KernelError::Capacity) => OutcomeKind::Capacity,
            Err(_) => OutcomeKind::OtherError,
        },
        Input::Capture(value) => match kernel.observe_capture(context(index as u64 + 10), value) {
            Ok(ObservationOutcome::Conflict) => OutcomeKind::ConflictRetained,
            Ok(_) => OutcomeKind::OtherObservation,
            Err(kix_kernel::KernelError::Capacity) => OutcomeKind::Capacity,
            Err(_) => OutcomeKind::OtherError,
        },
    }
}

/// rate=0 explicitly means a service-time microbenchmark, not an open-loop test.
/// rate>0 uses deadlines relative to a fixed origin. A late driver never shifts
/// the original deadline forward to hide queue delay (coordinated omission).
pub fn run(workload: Workload, count: usize, command_limit: usize, rate: u64) -> Report {
    assert!(count > 0 && count <= 100_000);
    assert!(command_limit > 0);
    let commands_budget = command_limit.max(2);
    let mut kernel = Kernel::new(
        id(80),
        context(0).fence,
        1,
        Inventory::seats(&[u16::try_from(INVENTORY_SEATS).expect("seat segment fits u16")])
            .unwrap(),
        Limits {
            commands: commands_budget,
            orders: ORDER_LIMIT,
            observations: OBSERVATION_LIMIT,
        },
    )
    .unwrap();
    let mut inputs = Vec::with_capacity(count);
    if matches!(workload, Workload::Conflict) {
        let a = request(1, 0);
        kernel.reserve(context(1), a.clone()).unwrap();
        let original = CaptureObservation {
            event_id: id(500),
            operation: a.payment,
            amount: a.amount,
            evidence_hash: Hash32::from_bytes([60; 32]),
        };
        kernel
            .observe_capture(context(2), original.clone())
            .unwrap();
        for i in 0..count {
            let mut value = original.clone();
            value.operation.operation = id(20_000 + i as u64);
            inputs.push(Input::Capture(value));
        }
    } else {
        for i in 0..count {
            let number = if matches!(workload, Workload::Retry) {
                1
            } else {
                i as u64 + 1
            };
            let seat = if matches!(workload, Workload::Uniform) {
                u16::try_from(i % INVENTORY_SEATS).expect("seat index fits u16")
            } else {
                0
            };
            inputs.push(Input::Reserve(request(number, seat)));
        }
    }
    let mut report = Report {
        workload: workload.name(),
        total: count,
        held: 0,
        replay: 0,
        rejected: 0,
        capacity: 0,
        conflict_retained: 0,
        other_error: 0,
        other_observation: 0,
        other: 0,
        first_capacity: None,
        samples_after_first_capacity: 0,
        command_limit_requested: command_limit,
        remaining: 0,
        elapsed_ns: 0,
        mixed_p99_service_ns: 0,
        mixed_p99_scheduled_latency_ns: 0,
        outcomes: Vec::new(),
        raw_csv: String::new(),
    };
    let mut rows = Vec::with_capacity(count);
    let mut service = Vec::with_capacity(count);
    let mut latency = Vec::with_capacity(count);
    let mut service_by: [Vec<u128>; 7] = std::array::from_fn(|_| Vec::new());
    let mut latency_by: [Vec<u128>; 7] = std::array::from_fn(|_| Vec::new());
    let origin = Instant::now();
    for (index, input) in inputs.into_iter().enumerate() {
        let scheduled = if rate == 0 {
            0
        } else {
            (index as u128 * 1_000_000_000) / u128::from(rate)
        };
        if rate > 0 {
            let elapsed = origin.elapsed().as_nanos();
            if scheduled > elapsed {
                std::thread::sleep(Duration::from_nanos(
                    (scheduled - elapsed).min(u128::from(u64::MAX)) as u64,
                ));
            }
        }
        let start = origin.elapsed().as_nanos();
        let begin = Instant::now();
        let kind = classify(&mut kernel, index, input);
        match kind {
            OutcomeKind::Held => report.held += 1,
            OutcomeKind::Replayed => report.replay += 1,
            OutcomeKind::BusinessRejected => report.rejected += 1,
            OutcomeKind::Capacity => report.capacity += 1,
            OutcomeKind::ConflictRetained => report.conflict_retained += 1,
            OutcomeKind::OtherError => report.other_error += 1,
            OutcomeKind::OtherObservation => report.other_observation += 1,
        }
        let duration = begin.elapsed().as_nanos();
        let end = origin.elapsed().as_nanos();
        if kind.as_str() == "capacity" && report.first_capacity.is_none() {
            report.first_capacity = Some(index);
        }
        let measured_latency = if rate == 0 {
            end - start
        } else {
            end.saturating_sub(scheduled)
        };
        rows.push((
            index,
            scheduled,
            start,
            end,
            duration,
            measured_latency,
            kind.as_str(),
        ));
        service.push(duration);
        latency.push(measured_latency);
        service_by[kind.index()].push(duration);
        latency_by[kind.index()].push(measured_latency);
    }
    report.elapsed_ns = origin.elapsed().as_nanos();
    report.remaining = kernel.remaining();
    report.other = report.other_error + report.other_observation;
    report.samples_after_first_capacity = report
        .first_capacity
        .map(|index| count.saturating_sub(index + 1))
        .unwrap_or(0);
    report.mixed_p99_service_ns = percentile(&mut service, 99);
    report.mixed_p99_scheduled_latency_ns = percentile(&mut latency, 99);
    report.outcomes = OutcomeKind::ALL
        .into_iter()
        .map(|kind| {
            let index = kind.index();
            OutcomeSummary {
                outcome: kind.as_str(),
                role: kind.role(),
                count: service_by[index].len(),
                service_p99_ns: (!service_by[index].is_empty())
                    .then(|| percentile(&mut service_by[index], 99)),
                scheduled_latency_p99_ns: (!latency_by[index].is_empty())
                    .then(|| percentile(&mut latency_by[index], 99)),
            }
        })
        .collect();
    report
        .raw_csv
        .push_str("index,scheduled_ns,start_ns,end_ns,service_ns,scheduled_latency_ns,outcome\n");
    for (i, scheduled, start, end, duration, observed, outcome) in rows {
        writeln!(
            &mut report.raw_csv,
            "{i},{scheduled},{start},{end},{duration},{observed},{outcome}"
        )
        .unwrap();
    }
    assert_eq!(
        report.held
            + report.replay
            + report.rejected
            + report.capacity
            + report.conflict_retained
            + report.other,
        count
    );
    report
}

fn json_u128(value: Option<u128>) -> String {
    value.map_or_else(|| "null".to_string(), |item| item.to_string())
}

fn json_bool(value: bool) -> &'static str {
    if value { "true" } else { "false" }
}

impl Report {
    /// Used by `performance_harness`. The example crate shares this file and does not call it.
    #[allow(dead_code)]
    pub fn outcome(&self, name: &str) -> Option<&OutcomeSummary> {
        self.outcomes.iter().find(|item| item.outcome == name)
    }

    pub fn low_load(&self) -> bool {
        self.workload == Workload::Uniform.name()
            && self.capacity == 0
            && self.rejected == 0
            && self.replay == 0
            && self.conflict_retained == 0
            && self.other == 0
            && self.first_capacity.is_none()
    }

    pub fn hot_seat(&self) -> bool {
        self.workload == Workload::HotSeat.name()
    }

    pub fn same_command_retry(&self) -> bool {
        self.workload == Workload::Retry.name()
    }

    pub fn history_growth(&self) -> bool {
        self.workload == Workload::Conflict.name()
    }

    pub fn saturation(&self) -> bool {
        self.first_capacity.is_some()
    }

    pub fn budget_phase(&self) -> &'static str {
        if self.saturation() {
            "includes-samples-after-first-capacity"
        } else {
            "under-budget"
        }
    }

    pub fn memory_only_new_held_per_elapsed_s(&self) -> Option<u128> {
        u128::try_from(self.held)
            .expect("held count fits u128")
            .checked_mul(1_000_000_000)?
            .checked_div(self.elapsed_ns)
    }

    pub fn json(&self, rate: u64, command_limit: usize) -> String {
        assert_eq!(command_limit, self.command_limit_requested);
        let mut outcomes = String::from("[");
        for (index, item) in self.outcomes.iter().enumerate() {
            if index > 0 {
                outcomes.push(',');
            }
            write!(
                &mut outcomes,
                "{{\"outcome\":\"{}\",\"role\":\"{}\",\"count\":{},\"service_p99_ns\":{},\"scheduled_latency_p99_ns\":{}}}",
                item.outcome,
                item.role,
                item.count,
                json_u128(item.service_p99_ns),
                json_u128(item.scheduled_latency_p99_ns),
            )
            .unwrap();
        }
        outcomes.push(']');
        format!(
            "{{\"workload\":\"{workload}\",\"workload_shape\":\"{workload}\",\"budget_phase\":\"{phase}\",\"low_load\":{low_load},\"hot_seat\":{hot_seat},\"same_command_retry\":{retry},\"history_growth\":{history},\"saturation\":{saturation},\"scope\":\"{scope}\",\"non_claims\":\"{non_claims}\",\"debug_assertions\":{debug},\"build_mode\":\"{build_mode}\",\"target_os\":\"{os}\",\"target_arch\":\"{arch}\",\"rate\":{rate},\"rate_meaning\":\"{rate_meaning}\",\"command_limit\":{command_limit},\"commands_budget\":{commands_budget},\"orders_limit\":{orders},\"observations_limit\":{observations},\"inventory_seats\":{seats},\"samples\":{samples},\"new_held\":{held},\"new_success_count\":{held},\"replayed\":{replay},\"business_rejected\":{rejected},\"capacity\":{capacity},\"conflict_retained\":{conflict},\"other_error\":{other_error},\"other_observation\":{other_observation},\"other\":{other},\"first_capacity_index\":{first_capacity},\"samples_after_first_capacity\":{after},\"remaining\":{remaining},\"elapsed_ns\":{elapsed},\"mixed_result_p99_service_ns\":{mixed_service},\"mixed_result_p99_scheduled_latency_ns\":{mixed_latency},\"p99_interpretation\":\"{p99}\",\"service_ns_meaning\":\"{service_meaning}\",\"scheduled_latency_ns_meaning\":\"{latency_meaning}\",\"memory_only_new_held_per_elapsed_s\":{goodput},\"goodput_interpretation\":\"{goodput_meaning}\",\"kernel_resets_during_workload\":0,\"outcomes\":{outcomes}}}\n",
            workload = self.workload,
            phase = self.budget_phase(),
            low_load = json_bool(self.low_load()),
            hot_seat = json_bool(self.hot_seat()),
            retry = json_bool(self.same_command_retry()),
            history = json_bool(self.history_growth()),
            saturation = json_bool(self.saturation()),
            scope = SCOPE,
            non_claims = NON_CLAIMS,
            debug = json_bool(cfg!(debug_assertions)),
            build_mode = build_mode(),
            os = std::env::consts::OS,
            arch = std::env::consts::ARCH,
            rate = rate,
            rate_meaning = rate_meaning(rate),
            command_limit = command_limit,
            commands_budget = command_limit.max(2),
            orders = ORDER_LIMIT,
            observations = OBSERVATION_LIMIT,
            seats = INVENTORY_SEATS,
            samples = self.total,
            held = self.held,
            replay = self.replay,
            rejected = self.rejected,
            capacity = self.capacity,
            conflict = self.conflict_retained,
            other_error = self.other_error,
            other_observation = self.other_observation,
            other = self.other,
            first_capacity = self
                .first_capacity
                .map_or_else(|| "null".to_string(), |index| index.to_string()),
            after = self.samples_after_first_capacity,
            remaining = self.remaining,
            elapsed = self.elapsed_ns,
            mixed_service = self.mixed_p99_service_ns,
            mixed_latency = self.mixed_p99_scheduled_latency_ns,
            p99 = MIXED_P99_INTERPRETATION,
            service_meaning = SERVICE_NS_MEANING,
            latency_meaning = SCHEDULED_LATENCY_NS_MEANING,
            goodput = json_u128(self.memory_only_new_held_per_elapsed_s()),
            goodput_meaning = GOODPUT_INTERPRETATION,
            outcomes = outcomes,
        )
    }
}

pub struct EvidenceBinding<'a> {
    pub commit: Option<&'a str>,
    pub tree: Option<&'a str>,
    pub kernel_blob: &'a str,
    pub quarantine_blob: &'a str,
    pub contract_edge_blob: &'a str,
    pub model_v4_blob: &'a str,
    pub probe_blob: Option<&'a str>,
    pub harness_blob: Option<&'a str>,
    pub example_blob: Option<&'a str>,
    pub toolchain: &'a str,
    pub host_uname: Option<&'a str>,
    pub os: &'a str,
    pub arch: &'a str,
    pub build_mode: &'a str,
    pub debug_assertions: bool,
    pub samples: usize,
    pub low_load_samples: usize,
    pub command_limit: usize,
    pub rate: u64,
    pub output_files: &'a [&'a str],
}

fn json_string(value: &str) -> String {
    let mut out = String::from("\"");
    for c in value.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c < ' ' => out.push_str(&format!("\\u{:04x}", u32::from(c))),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn json_opt_string(value: Option<&str>) -> String {
    value.map_or_else(|| "null".to_string(), json_string)
}

fn json_str_array(values: &[&str]) -> String {
    let mut out = String::from("[");
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        out.push_str(&json_string(value));
    }
    out.push(']');
    out
}

pub fn evidence_binding_json(binding: &EvidenceBinding<'_>) -> String {
    format!(
        "{{\"evidence_class\":\"local apparatus binding; not a product performance result\",\"commit\":{commit},\"tree\":{tree},\"locked_blobs\":{{\"kernel\":\"{kernel}\",\"quarantine_capacity\":\"{quarantine}\",\"contract_edge_cases\":\"{edge}\",\"model_v4\":\"{model}\"}},\"probe_blob\":{probe},\"harness_blob\":{harness},\"example_blob\":{example},\"toolchain\":{toolchain},\"host_uname\":{uname},\"target_os\":{os},\"target_arch\":{arch},\"build_mode\":{build_mode},\"debug_assertions\":{debug},\"samples\":{samples},\"low_load_samples\":{low_load_samples},\"command_limit\":{command_limit},\"orders_limit\":{orders},\"observations_limit\":{observations},\"inventory_seats\":{seats},\"rate\":{rate},\"rate_meaning\":{rate_meaning},\"output_files\":{files},\"kernel_resets_during_workload\":0,\"product_slo\":null,\"non_claims\":{non_claims}}}\n",
        commit = json_opt_string(binding.commit),
        tree = json_opt_string(binding.tree),
        kernel = binding.kernel_blob,
        quarantine = binding.quarantine_blob,
        edge = binding.contract_edge_blob,
        model = binding.model_v4_blob,
        probe = json_opt_string(binding.probe_blob),
        harness = json_opt_string(binding.harness_blob),
        example = json_opt_string(binding.example_blob),
        toolchain = json_string(binding.toolchain),
        uname = json_opt_string(binding.host_uname),
        os = json_string(binding.os),
        arch = json_string(binding.arch),
        build_mode = json_string(binding.build_mode),
        debug = json_bool(binding.debug_assertions),
        samples = binding.samples,
        low_load_samples = binding.low_load_samples,
        command_limit = binding.command_limit,
        orders = ORDER_LIMIT,
        observations = OBSERVATION_LIMIT,
        seats = INVENTORY_SEATS,
        rate = binding.rate,
        rate_meaning = json_string(rate_meaning(binding.rate)),
        files = json_str_array(binding.output_files),
        non_claims = json_string(NON_CLAIMS),
    )
}
