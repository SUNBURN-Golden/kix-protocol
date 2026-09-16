#![allow(clippy::disallowed_methods)] // Test-only evidence I/O; production lint rules are unchanged.
//! E-4: locked v4 versus an independently represented sequential model.
//! No retention, void, slot-release, chain grant or new kernel transition exists here.
#[path = "support/model_v4.rs"]
mod reference;

use std::fs;
use std::path::PathBuf;
use std::process::Command;

use kix_kernel::{
    CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, Limits, Reserve,
    ReserveOutcome, SEMANTICS_VERSION, Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};
use reference::{Action, InventoryCase, Model, Reply, Step};

const CASES: u64 = 256;
const STEPS: usize = 128;
const LOCKED_KERNEL: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
const LOCKED_TEST: &str = "b607996c83a119c349f1cc90469ac1ba82764e20";

fn id(number: u64) -> KixId {
    let mut bytes = [0_u8; 16];
    bytes[..8].copy_from_slice(&number.to_le_bytes());
    KixId::from_bytes(bytes)
}

fn writer(generation: u64) -> ExecutionFence {
    ExecutionFence { owner: id(900), generation }
}

fn amount(atoms: u128, variant: u64) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([10 + (variant % 2) as u8; 32]), atoms, u128::MAX,
        RegistryVersion::new(1 + (variant % 3) as u32).unwrap(),
        Hash32::from_bytes([20 + (variant % 5) as u8; 32]),
    ).unwrap()
}

fn request(number: u64, selection: Selection, expires: u64) -> Reserve {
    Reserve {
        id: CommandId { scope: id(800), principal: id(801), request: id(number) },
        order_id: id(10_000 + number), expected_business_epoch: 1, selection,
        amount: amount(1_000, 0), quote_hash: Hash32::from_bytes([31; 32]),
        policy_hash: Hash32::from_bytes([32; 32]), expires_at_ms: expires,
        payment: kix_kernel::ProviderOperation {
            provider: id(850), account: id(851), operation: id(number),
        },
    }
}

fn context(now: u64) -> Context {
    Context { fence: writer(1), now_ms: now, semantics_version: 4 }
}

#[derive(Clone, Debug)]
struct Case {
    layout: InventoryCase,
    limits: Limits,
}

fn initial(case: &Case) -> (Kernel, Model) {
    let inventory = match &case.layout {
        InventoryCase::Seats(lengths) => Inventory::seats(lengths).unwrap(),
        InventoryCase::Ga(total) => Inventory::general_admission(*total).unwrap(),
    };
    (
        Kernel::new(id(800), writer(1), 1, inventory, case.limits).unwrap(),
        Model::new(id(800), writer(1), case.layout.clone(), case.limits),
    )
}

fn apply(kernel: &mut Kernel, step: &Step) -> Reply {
    match &step.action {
        Action::Reserve(value) => Reply::Reserve(kernel.reserve(step.ctx, value.clone())),
        Action::Send(order) => Reply::Unit(kernel.mark_payment_unknown(step.ctx, *order)),
        Action::Expire(order) => Reply::Expire(kernel.expire(step.ctx, *order)),
        Action::Cancel(next) => Reply::Unit(kernel.cancel_scope(step.ctx, *next)),
        Action::Owner(next) => Reply::Unit(kernel.replace_owner(step.ctx, *next)),
        Action::Capture(value) => Reply::Capture(kernel.observe_capture(step.ctx, value.clone())),
    }
}

fn compare(kernel: &Kernel, model: &Model) -> Result<(), String> {
    if kernel.remaining() != model.remaining() || kernel.order_count() != model.orders.len()
        || kernel.observation_count() != model.events.len()
        || kernel.reserved_observation_count() != model.promised.len()
        || kernel.quarantined_operation_count() != model.quarantined.len()
        || kernel.conflicts() != model.conflicts
    {
        return Err(format!("observable counts differ: kernel remaining={} orders={} events={} slots={} quarantine={}; model remaining={} orders={} events={} slots={} quarantine={}",
            kernel.remaining(), kernel.order_count(), kernel.observation_count(), kernel.reserved_observation_count(), kernel.quarantined_operation_count(),
            model.remaining(), model.orders.len(), model.events.len(), model.promised.len(), model.quarantined.len()));
    }
    if model.budget() > model.limits.observations {
        return Err("reference evidence budget exceeded".into());
    }
    for expected in &model.orders {
        let actual = kernel.order(expected.input.order_id).ok_or("missing kernel order")?;
        if actual.request != expected.input || actual.submitted_under != expected.writer
            || actual.state != expected.phase || actual.inventory_owned != expected.owns
            || actual.captured != expected.amount || actual.review_required != expected.review
        {
            return Err(format!("order mismatch: actual={actual:?}; reference={expected:?}"));
        }
    }
    // Check inventory conservation independently from the kernel's bitmap representation.
    if let InventoryCase::Seats(_) = model.layout {
        let held: usize = model.orders.iter().filter(|o| o.owns).map(|o| match o.input.selection {
            Selection::Seats { count, .. } => usize::from(count),
            _ => 0,
        }).sum();
        if held + model.remaining() as usize != model.seats.len() {
            return Err("reference seat conservation failed".into());
        }
    }
    Ok(())
}

fn check_trace(case: &Case, trace: &[Step], bad_oracle: bool) -> Result<(), String> {
    let (mut kernel, mut model) = initial(case);
    model.omit_full_quarantine = bad_oracle;
    for (index, step) in trace.iter().enumerate() {
        let expected = model.apply(step);
        let actual = apply(&mut kernel, step);
        if actual != expected {
            return Err(format!("step {index}: {step:?}\nexpected {expected:?}, actual {actual:?}"));
        }
        compare(&kernel, &model).map_err(|error| format!("step {index}: {step:?}\n{error}"))?;
    }
    Ok(())
}

/// Fixed algorithm and explicit seed; no process/thread RNG or wall time.
struct Generator(u64);
impl Generator {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e3779b97f4a7c15);
        let mut x = self.0;
        x = (x ^ (x >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        x = (x ^ (x >> 27)).wrapping_mul(0x94d049bb133111eb);
        x ^ (x >> 31)
    }
    fn below(&mut self, n: u64) -> u64 { self.next() % n }
}

fn trace(case: &Case, seed: u64) -> Vec<Step> {
    let (_, mut model) = initial(case);
    let mut rng = Generator(seed);
    let mut result = Vec::new();
    for index in 0..STEPS {
        let mut ctx = Context {
            fence: model.writer, now_ms: model.time + rng.below(4), semantics_version: 4,
        };
        match rng.below(25) {
            0 => ctx.semantics_version = 1,
            1 => ctx.fence.generation = ctx.fence.generation.saturating_sub(1),
            2 => ctx.now_ms = model.time.saturating_sub(1),
            _ => {}
        }
        let choice = rng.below(100);
        let action = if choice < 43 {
            let selection = match case.layout {
                InventoryCase::Ga(_) => Selection::GeneralAdmission { count: 1 + rng.below(4) as u32 },
                InventoryCase::Seats(_) => Selection::Seats {
                    first: rng.below(model.seats.len() as u64 + 2) as u16,
                    count: 1 + rng.below(4) as u16,
                },
            };
            let mut input = if !model.commands.is_empty() && rng.below(3) == 0 {
                model.commands[rng.below(model.commands.len() as u64) as usize].0.clone()
            } else {
                request(1 + rng.below(48), selection, ctx.now_ms + 8 + rng.below(32))
            };
            input.expected_business_epoch = model.epoch;
            match rng.below(14) {
                0 => input.id.scope = id(999),
                1 => input.amount = amount(0, 0),
                2 => input.amount = amount(1_001, 1),
                3 => input.expires_at_ms = ctx.now_ms,
                4 => input.selection = Selection::Seats { first: u16::MAX, count: 2 },
                5 => input.payment.account = id(852),
                6 => input.expected_business_epoch = 0,
                _ => {}
            }
            Action::Reserve(input)
        } else if choice < 71 {
            let order = if !model.orders.is_empty() && rng.below(5) != 0 {
                model.orders[rng.below(model.orders.len() as u64) as usize].input.order_id
            } else { id(99_999) };
            if choice < 59 { Action::Send(order) } else { Action::Expire(order) }
        } else if choice < 94 {
            let mut observation = if !model.events.is_empty() && rng.below(3) == 0 {
                model.events[rng.below(model.events.len() as u64) as usize].0.clone()
            } else {
                let input = if model.orders.is_empty() {
                    request(500, Selection::GeneralAdmission { count: 1 }, 999)
                } else {
                    model.orders[rng.below(model.orders.len() as u64) as usize].input.clone()
                };
                CaptureObservation {
                    event_id: id(500 + rng.below(12)), operation: input.payment,
                    amount: input.amount, evidence_hash: Hash32::from_bytes([60; 32]),
                }
            };
            match rng.below(8) {
                0 => observation.operation.operation = id(700 + rng.below(8)),
                1 => observation.amount = amount(999, 1),
                2 => observation.evidence_hash = Hash32::from_bytes([61; 32]),
                3 if !model.orders.is_empty() => observation.operation = model.orders[rng.below(model.orders.len() as u64) as usize].input.payment,
                _ => {}
            }
            Action::Capture(observation)
        } else if index < STEPS * 3 / 4 || choice < 98 {
            Action::Owner(writer(model.writer.generation + 1))
        } else {
            Action::Cancel(model.epoch + 1)
        };
        let step = Step { ctx, action };
        model.apply(&step); // Generator consults only the independent model.
        result.push(step);
    }
    result
}

/// Deterministic deletion shrinker. It does not claim parameter or configuration minimization.
fn shrink(case: &Case, input: &[Step], bad_oracle: bool) -> Vec<Step> {
    let mut reduced = input.to_vec();
    let mut span = reduced.len().div_ceil(2).max(1);
    loop {
        let mut offset = 0;
        while offset < reduced.len() {
            let end = (offset + span).min(reduced.len());
            let mut trial = reduced.clone();
            trial.drain(offset..end);
            if check_trace(case, &trial, bad_oracle).is_err() {
                reduced = trial;
            } else {
                offset += span;
            }
        }
        if span == 1 { break; }
        span = span.div_ceil(2);
    }
    reduced
}

fn evidence_dir() -> PathBuf {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../.local/verification/ktx");
    fs::create_dir_all(&path).unwrap();
    path
}

#[test]
fn locked_v4_matches_independent_state_model() {
    assert_eq!(SEMANTICS_VERSION, 4);
    let cases = [
        Case { layout: InventoryCase::Seats(vec![70, 10]), limits: Limits { commands: 64, orders: 32, observations: 16 } },
        Case { layout: InventoryCase::Seats(vec![2, 2]), limits: Limits { commands: 2, orders: 16, observations: 2 } },
        Case { layout: InventoryCase::Ga(6), limits: Limits { commands: 32, orders: 16, observations: 4 } },
        Case { layout: InventoryCase::Seats(vec![1, 1, 2]), limits: Limits { commands: 16, orders: 8, observations: 1 } },
    ];
    let mut actions = [0_u64; 6];
    for (case_no, case) in cases.iter().enumerate() {
        for seed in 1..=CASES {
            let inputs = trace(case, seed);
            for step in &inputs {
                let index = match step.action {
                    Action::Reserve(_) => 0, Action::Send(_) => 1, Action::Expire(_) => 2,
                    Action::Capture(_) => 3, Action::Owner(_) => 4, Action::Cancel(_) => 5,
                };
                actions[index] += 1;
            }
            if let Err(error) = check_trace(case, &inputs, false) {
                let minimal = shrink(case, &inputs, false);
                fs::write(evidence_dir().join("e4-failure.txt"), format!("case={case_no}; seed={seed}; config={case:?}\n{error}\nshrunk={minimal:#?}\n")).unwrap();
                panic!("case={case_no} seed={seed}: {error}\nshrunk={minimal:#?}");
            }
        }
    }
    assert!(actions.iter().all(|n| *n > 0));
    fs::write(evidence_dir().join("e4-summary.json"), format!(
        "{{\"semantics\":4,\"kernel_blob\":\"{LOCKED_KERNEL}\",\"configurations\":{},\"seeds_per_configuration\":{CASES},\"first_seed\":1,\"last_seed\":{CASES},\"steps_per_sequence\":{STEPS},\"sequences\":{},\"compared_transitions\":{},\"action_counts\":{:?},\"scope\":\"public observable sequential v4 conformance, not durable replay or retention\",\"failures\":0}}\n",
        cases.len(), cases.len() as u64 * CASES, cases.len() as u64 * CASES * STEPS as u64, actions,
    )).unwrap();
}

#[test]
fn oracle_sensitivity_detects_and_shrinks_missing_full_budget_quarantine() {
    let case = Case { layout: InventoryCase::Seats(vec![4]), limits: Limits { commands: 8, orders: 8, observations: 1 } };
    let a = request(1, Selection::Seats { first: 0, count: 1 }, 100);
    let b = request(2, Selection::Seats { first: 1, count: 1 }, 100);
    let observation = |input: &Reserve| CaptureObservation {
        event_id: id(500), operation: input.payment, amount: input.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    };
    let inputs = vec![
        Step { ctx: context(1), action: Action::Expire(id(99_999)) },
        Step { ctx: context(2), action: Action::Reserve(a.clone()) },
        Step { ctx: context(3), action: Action::Reserve(b.clone()) },
        Step { ctx: context(4), action: Action::Expire(a.order_id) },
        Step { ctx: context(5), action: Action::Capture(observation(&a)) },
        Step { ctx: context(6), action: Action::Capture(observation(&b)) },
    ];
    check_trace(&case, &inputs, false).unwrap();
    assert!(check_trace(&case, &inputs, true).is_err());
    let minimal = shrink(&case, &inputs, true);
    assert!(minimal.len() < inputs.len());
    assert!(check_trace(&case, &minimal, true).is_err());
    fs::write(evidence_dir().join("e4-oracle-sensitivity.txt"), format!(
        "injection=independent-model-only; kernel unchanged\nexpected mismatch detected\noriginal_steps={}\nshrunk_steps={}\ntrace={minimal:#?}\n", inputs.len(), minimal.len(),
    )).unwrap();
}

#[test]
fn capacity_two_sequence_is_observed_not_repaired() {
    let case = Case { layout: InventoryCase::Seats(vec![1]), limits: Limits { commands: 2, orders: 8, observations: 8 } };
    let (mut kernel, _) = initial(&case);
    let a = request(1, Selection::Seats { first: 0, count: 1 }, 10);
    let b = request(2, Selection::Seats { first: 0, count: 1 }, 10);
    let c = request(3, Selection::Seats { first: 0, count: 1 }, 100);
    let first = kernel.reserve(context(1), a.clone());
    let second = kernel.reserve(context(2), b);
    let expired = kernel.expire(context(10), a.order_id);
    let remaining = kernel.remaining();
    let new_request = kernel.reserve(context(11), c);
    assert!(matches!(first.as_ref().unwrap().original, ReserveOutcome::Held(_)));
    assert_eq!(second.as_ref().unwrap().original, ReserveOutcome::Rejected(kix_kernel::Rejection::Unavailable));
    assert_eq!(expired, Ok(true));
    assert_eq!(remaining, 1);
    assert_eq!(new_request, Err(kix_kernel::KernelError::Capacity));
    fs::write(evidence_dir().join("e4-capacity-two.txt"), format!(
        "kernel_blob={LOCKED_KERNEL}\ncommand_limit=2\nreserve_1={first:?}\nreserve_2={second:?}\nexpire={expired:?}\nremaining={remaining}\nreserve_3={new_request:?}\n"
    )).unwrap();
}

#[test]
fn locked_sources_and_new_harness_sources_are_identified() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let mut evidence = String::new();
    for (relative, expected) in [("src/lib.rs", LOCKED_KERNEL), ("tests/quarantine_capacity.rs", LOCKED_TEST)] {
        let output = Command::new("git").arg("hash-object").arg(root.join(relative)).output().unwrap();
        assert!(output.status.success());
        let actual = String::from_utf8(output.stdout).unwrap();
        assert_eq!(actual.trim(), expected);
        evidence.push_str(&format!("{relative}\t{actual}"));
    }
    for relative in ["tests/e4_state_model.rs", "tests/support/model_v4.rs", "tests/performance_harness.rs", "tests/support/perf_probe.rs", "examples/r1_perf_probe.rs"] {
        let output = Command::new("git").arg("hash-object").arg(root.join(relative)).output().unwrap();
        assert!(output.status.success());
        evidence.push_str(&format!("{relative}\t{}", String::from_utf8(output.stdout).unwrap()));
        // Diagnostic formatted copies only. Never writes to repository source.
        // Existing CI remains responsible for checking committed formatting.
        if let Ok(formatted) = Command::new("rustfmt").args(["--edition", "2024", "--emit", "stdout", "--config", "skip_children=true"]).arg(root.join(relative)).output()
            && formatted.status.success()
        {
            fs::write(evidence_dir().join(format!("formatted-{}", relative.replace('/', "__"))), formatted.stdout).unwrap();
        }
    }
    fs::write(evidence_dir().join("first-batch-source-blobs.txt"), evidence).unwrap();
}
