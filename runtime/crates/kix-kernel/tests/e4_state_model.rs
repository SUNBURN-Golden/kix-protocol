#![allow(clippy::disallowed_methods)] // Test-only evidence I/O; production lint rules are unchanged.
//! E-4: locked v4 versus an independently represented sequential model.
//! No retention, void, slot-release, chain grant or new kernel transition exists here.
#[path = "support/coverage_v4.rs"]
mod coverage;
#[path = "support/evidence_gates.rs"]
mod evidence_gates;
#[path = "support/model_v4.rs"]
mod reference;

use std::fs;
use std::path::PathBuf;
use std::process::Command;

use coverage::{Coverage, FAMILIES, Family};
use kix_kernel::{
    CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, Limits, Reserve,
    ReserveOutcome, SEMANTICS_VERSION, Selection,
};
use kix_kernel::{OrderState, ProviderOperation};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};
use reference::{Action, InventoryCase, Model, Reply, Step};

// Historical baseline workload (Task 003-A freeze). Do not retune to satisfy a coverage goal.
const CASES: u64 = 256;
const STEPS: usize = 128;
// Additive relation-aware workload (Task 003-B). Separate constants keep the baseline reproducible.
const RELATION_SEEDS: u64 = 64;
const RELATION_STEPS: usize = 48;
const LOCKED_KERNEL: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
const LOCKED_TEST: &str = "b607996c83a119c349f1cc90469ac1ba82764e20";

fn id(number: u64) -> KixId {
    let mut bytes = [0_u8; 16];
    bytes[..8].copy_from_slice(&number.to_le_bytes());
    KixId::from_bytes(bytes)
}

fn writer(generation: u64) -> ExecutionFence {
    ExecutionFence {
        owner: id(900),
        generation,
    }
}

fn amount(atoms: u128, variant: u64) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([10 + (variant % 2) as u8; 32]),
        atoms,
        u128::MAX,
        RegistryVersion::new(1 + (variant % 3) as u32).unwrap(),
        Hash32::from_bytes([20 + (variant % 5) as u8; 32]),
    )
    .unwrap()
}

fn request(number: u64, selection: Selection, expires: u64) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(800),
            principal: id(801),
            request: id(number),
        },
        order_id: id(10_000 + number),
        expected_business_epoch: 1,
        selection,
        amount: amount(1_000, 0),
        quote_hash: Hash32::from_bytes([31; 32]),
        policy_hash: Hash32::from_bytes([32; 32]),
        expires_at_ms: expires,
        payment: kix_kernel::ProviderOperation {
            provider: id(850),
            account: id(851),
            operation: id(number),
        },
    }
}

fn context(now: u64) -> Context {
    Context {
        fence: writer(1),
        now_ms: now,
        semantics_version: 4,
    }
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
    if kernel.remaining() != model.remaining()
        || kernel.order_count() != model.orders.len()
        || kernel.observation_count() != model.events.len()
        || kernel.reserved_observation_count() != model.reservations.len()
        || kernel.quarantined_operation_count() != model.quarantined.len()
        || kernel.conflicts() != model.conflicts
    {
        return Err(format!(
            "observable counts differ: kernel remaining={} orders={} events={} slots={} quarantine={}; model remaining={} orders={} events={} slots={} quarantine={}",
            kernel.remaining(),
            kernel.order_count(),
            kernel.observation_count(),
            kernel.reserved_observation_count(),
            kernel.quarantined_operation_count(),
            model.remaining(),
            model.orders.len(),
            model.events.len(),
            model.reservations.len(),
            model.quarantined.len()
        ));
    }
    if model.budget() > model.limits.observations {
        return Err("reference evidence budget exceeded".into());
    }
    for expected in &model.orders {
        let actual = kernel
            .order(expected.input.order_id)
            .ok_or("missing kernel order")?;
        if actual.request != expected.input
            || actual.submitted_under != expected.writer
            || actual.state != expected.phase
            || actual.inventory_owned != expected.owns
            || actual.captured != expected.captured_amount()
            || actual.review_required != expected.review
        {
            return Err(format!(
                "order mismatch: actual={actual:?}; reference={expected:?}"
            ));
        }
    }
    // Check inventory conservation independently from the kernel's bitmap representation.
    if let InventoryCase::Seats(_) = model.layout {
        let held: usize = model
            .orders
            .iter()
            .filter(|o| o.owns)
            .map(|o| match o.input.selection {
                Selection::Seats { count, .. } => usize::from(count),
                _ => 0,
            })
            .sum();
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
            return Err(format!(
                "step {index}: {step:?}\nexpected {expected:?}, actual {actual:?}"
            ));
        }
        model
            .check_relations()
            .map_err(|error| format!("step {index}: {step:?}\nmodel relation: {error}"))?;
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
    fn below(&mut self, n: u64) -> u64 {
        self.next() % n
    }
}

fn trace(case: &Case, seed: u64) -> Vec<Step> {
    let (_, mut model) = initial(case);
    let mut rng = Generator(seed);
    let mut result = Vec::new();
    for index in 0..STEPS {
        let mut ctx = Context {
            fence: model.writer,
            now_ms: model.time + rng.below(4),
            semantics_version: 4,
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
                InventoryCase::Ga(_) => Selection::GeneralAdmission {
                    count: 1 + rng.below(4) as u32,
                },
                InventoryCase::Seats(_) => Selection::Seats {
                    first: rng.below(model.seats.len() as u64 + 2) as u16,
                    count: 1 + rng.below(4) as u16,
                },
            };
            let mut input = if !model.commands.is_empty() && rng.below(3) == 0 {
                model.commands[rng.below(model.commands.len() as u64) as usize]
                    .0
                    .clone()
            } else {
                request(1 + rng.below(48), selection, ctx.now_ms + 8 + rng.below(32))
            };
            input.expected_business_epoch = model.epoch;
            match rng.below(14) {
                0 => input.id.scope = id(999),
                1 => input.amount = amount(0, 0),
                2 => input.amount = amount(1_001, 1),
                3 => input.expires_at_ms = ctx.now_ms,
                4 => {
                    input.selection = Selection::Seats {
                        first: u16::MAX,
                        count: 2,
                    }
                }
                5 => input.payment.account = id(852),
                6 => input.expected_business_epoch = 0,
                _ => {}
            }
            Action::Reserve(input)
        } else if choice < 71 {
            let order = if !model.orders.is_empty() && rng.below(5) != 0 {
                model.orders[rng.below(model.orders.len() as u64) as usize]
                    .input
                    .order_id
            } else {
                id(99_999)
            };
            if choice < 59 {
                Action::Send(order)
            } else {
                Action::Expire(order)
            }
        } else if choice < 94 {
            let mut observation = if !model.events.is_empty() && rng.below(3) == 0 {
                model.events[rng.below(model.events.len() as u64) as usize]
                    .observation
                    .clone()
            } else {
                let input = if model.orders.is_empty() {
                    request(500, Selection::GeneralAdmission { count: 1 }, 999)
                } else {
                    model.orders[rng.below(model.orders.len() as u64) as usize]
                        .input
                        .clone()
                };
                CaptureObservation {
                    event_id: id(500 + rng.below(12)),
                    operation: input.payment,
                    amount: input.amount,
                    evidence_hash: Hash32::from_bytes([60; 32]),
                }
            };
            match rng.below(8) {
                0 => observation.operation.operation = id(700 + rng.below(8)),
                1 => observation.amount = amount(999, 1),
                2 => observation.evidence_hash = Hash32::from_bytes([61; 32]),
                3 if !model.orders.is_empty() => {
                    observation.operation = model.orders
                        [rng.below(model.orders.len() as u64) as usize]
                        .input
                        .payment
                }
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
    shrink_with(input, |trial| check_trace(case, trial, bad_oracle).is_err())
}

/// Same deletion strategy against any failing predicate over a trace prefix/subsequence.
fn shrink_with(input: &[Step], still_fails: impl Fn(&[Step]) -> bool) -> Vec<Step> {
    let mut reduced = input.to_vec();
    let mut span = reduced.len().div_ceil(2).max(1);
    loop {
        let mut offset = 0;
        while offset < reduced.len() {
            let end = (offset + span).min(reduced.len());
            let mut trial = reduced.clone();
            trial.drain(offset..end);
            if still_fails(&trial) {
                reduced = trial;
            } else {
                offset += span;
            }
        }
        if span == 1 {
            break;
        }
        span = span.div_ceil(2);
    }
    reduced
}

// ---------------------------------------------------------------------------
// Task 003-B: relation-aware generated coverage (additive; baseline above unchanged).
// ---------------------------------------------------------------------------

/// A failure of the differential comparison or of a relation property, with
/// everything needed to replay it from the explicit seed.
#[derive(Debug)]
struct RelationFailure {
    step: usize,
    kind: &'static str,
    detail: String,
}

/// Differential check plus relation-property observation. `kernel` may be `None`
/// to run the property layer on the model alone (used for checker sensitivity).
fn check_relations_trace(
    case: &Case,
    trace: &[Step],
    bad_oracle: bool,
    with_kernel: bool,
) -> Result<Coverage, RelationFailure> {
    let (mut kernel, mut model) = initial(case);
    model.omit_full_quarantine = bad_oracle;
    let mut coverage = Coverage::new();
    for (index, step) in trace.iter().enumerate() {
        let pre = model.clone();
        let expected = model.apply(step);
        if with_kernel {
            let before = kernel.clone();
            let actual = apply(&mut kernel, step);
            evidence_gates::exact_read_only(&pre, step, &actual, &before, &kernel).map_err(
                |detail| RelationFailure {
                    step: index,
                    kind: "whole_kernel_read_only",
                    detail,
                },
            )?;
            if evidence_gates::must_be_read_only(&pre, step, &actual) {
                coverage.exact_read_only_checks += 1;
            }
            if actual != expected {
                return Err(RelationFailure {
                    step: index,
                    kind: "differential",
                    detail: format!("{step:?}\nexpected {expected:?}, actual {actual:?}"),
                });
            }
            compare(&kernel, &model).map_err(|error| RelationFailure {
                step: index,
                kind: "observable_state",
                detail: format!("{step:?}\n{error}"),
            })?;
        }
        model.check_relations().map_err(|error| RelationFailure {
            step: index,
            kind: "model_relation",
            detail: format!("{step:?}\n{error}"),
        })?;
        coverage
            .observe(&pre, step, &expected, &model)
            .map_err(|error| RelationFailure {
                step: index,
                kind: "transition_property",
                detail: format!("{step:?}\nreply {expected:?}\n{error}"),
            })?;
    }
    Ok(coverage)
}

/// Generator-side bookkeeping that only the generator needs (never a model fact).
#[derive(Default)]
struct Planner {
    fresh: u64,
    /// Operations named by a conflict that was refused for capacity while unbound.
    unretained: Vec<ProviderOperation>,
}

fn operation(number: u64) -> ProviderOperation {
    ProviderOperation {
        provider: id(850),
        account: id(851),
        operation: id(number),
    }
}

fn pick<'a, T>(rng: &mut Generator, items: &'a [T]) -> Option<&'a T> {
    if items.is_empty() {
        None
    } else {
        Some(&items[rng.below(items.len() as u64) as usize])
    }
}

fn free_selection(rng: &mut Generator, model: &Model) -> Option<Selection> {
    match &model.layout {
        InventoryCase::Ga(_) => (model.remaining() > 0).then(|| Selection::GeneralAdmission {
            count: 1 + rng.below(u64::from(model.remaining().min(2))) as u32,
        }),
        InventoryCase::Seats(_) => {
            let free: Vec<u16> = model
                .seats
                .iter()
                .enumerate()
                .filter(|(_, s)| s.is_none())
                .map(|(i, _)| i as u16)
                .collect();
            pick(rng, &free).map(|first| Selection::Seats {
                first: *first,
                count: 1,
            })
        }
    }
}

fn fresh_request(planner: &mut Planner, rng: &mut Generator, model: &Model, now: u64) -> Reserve {
    planner.fresh += 1;
    let number = 1_000 + planner.fresh;
    let selection = free_selection(rng, model).unwrap_or(Selection::Seats {
        first: u16::MAX,
        count: 1,
    });
    let mut input = request(number, selection, now + 4 + rng.below(24));
    input.expected_business_epoch = model.epoch;
    input
}

fn capture_for(input: &Reserve, event: u64) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: input.payment,
        amount: input.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    }
}

fn orders_where(
    model: &Model,
    predicate: impl Fn(&reference::ModelOrder) -> bool,
) -> Vec<&reference::ModelOrder> {
    model.orders.iter().filter(|o| predicate(o)).collect()
}

/// Family-directed move. Each arm builds an action whose *intended* relation is
/// named by the family; whether it is reached is decided by the observer, not here.
fn relation_action(
    family: Family,
    planner: &mut Planner,
    rng: &mut Generator,
    model: &Model,
    ctx: &mut Context,
) -> Action {
    let fresh_capture_event = |planner: &mut Planner| {
        planner.fresh += 1;
        5_000 + planner.fresh
    };
    let background = |planner: &mut Planner, rng: &mut Generator| match rng.below(6) {
        0 | 1 => Action::Reserve(fresh_request(planner, rng, model, ctx.now_ms)),
        2 => Action::Send(
            pick(rng, &model.orders)
                .map(|o| o.input.order_id)
                .unwrap_or(id(99_999)),
        ),
        3 => Action::Expire(
            pick(rng, &model.orders)
                .map(|o| o.input.order_id)
                .unwrap_or(id(99_999)),
        ),
        4 => Action::Owner(writer(model.writer.generation + 1)),
        _ => {
            let event = fresh_capture_event(planner);
            match pick(rng, &model.orders) {
                Some(order) => Action::Capture(capture_for(&order.input, event)),
                None => Action::Capture(capture_for(
                    &request(1, Selection::GeneralAdmission { count: 1 }, 9),
                    event,
                )),
            }
        }
    };
    match family {
        Family::P1CommandIdentity => match (rng.below(8), pick(rng, &model.commands)) {
            (0..=2, Some((known, _))) => {
                if rng.below(3) == 0 {
                    match rng.below(4) {
                        0 => ctx.semantics_version = 1,
                        1 => ctx.fence.generation = ctx.fence.generation.saturating_sub(1),
                        2 => ctx.now_ms = model.time.saturating_sub(1),
                        _ => {
                            let mut foreign = known.clone();
                            foreign.id.scope = id(999);
                            return Action::Reserve(foreign);
                        }
                    }
                }
                Action::Reserve(known.clone())
            }
            (3..=5, Some((known, _))) => {
                let mut altered = known.clone();
                match rng.below(5) {
                    0 => altered.order_id = id(20_000 + planner.fresh),
                    1 => altered.amount = amount(1_001, 1),
                    2 => altered.payment.operation = id(30_000 + planner.fresh),
                    3 => altered.expires_at_ms += 1,
                    _ => {
                        altered.selection = Selection::Seats {
                            first: u16::MAX,
                            count: 1,
                        }
                    }
                }
                match rng.below(4) {
                    0 => ctx.fence.generation = ctx.fence.generation.saturating_sub(1),
                    1 => ctx.now_ms = model.time.saturating_sub(1),
                    _ => {}
                }
                Action::Reserve(altered)
            }
            (6, _) => match rng.below(4) {
                3 => {
                    // New identity reusing the selection and operation of an earlier
                    // Unavailable rejection once the blocking hold may have cleared.
                    let rejected: Vec<&Reserve> = model
                        .commands
                        .iter()
                        .filter(|(_, o)| {
                            *o == ReserveOutcome::Rejected(kix_kernel::Rejection::Unavailable)
                        })
                        .map(|(r, _)| r)
                        .collect();
                    match pick(rng, &rejected) {
                        Some(earlier) => {
                            let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                            input.selection = earlier.selection;
                            input.payment = earlier.payment;
                            Action::Reserve(input)
                        }
                        None => background(planner, rng),
                    }
                }
                0 => {
                    // Unavailable rejection: ask for a selection another order still owns.
                    let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                    input.selection = pick(rng, &orders_where(model, |o| o.owns))
                        .map(|o| o.input.selection)
                        .unwrap_or(Selection::Seats {
                            first: u16::MAX,
                            count: 1,
                        });
                    Action::Reserve(input)
                }
                1 => match pick(rng, &orders_where(model, |o| o.phase == OrderState::Held)) {
                    Some(order) => {
                        ctx.now_ms = ctx.now_ms.max(order.input.expires_at_ms);
                        Action::Expire(order.input.order_id)
                    }
                    None => background(planner, rng),
                },
                _ => {
                    let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                    input.selection = Selection::Seats {
                        first: u16::MAX,
                        count: 1,
                    };
                    Action::Reserve(input)
                }
            },
            _ => background(planner, rng),
        },
        Family::P2OperationBinding => match rng.below(8) {
            0 | 1 => {
                let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                if let Some(binding) = pick(rng, &model.bindings) {
                    input.payment = binding.operation;
                }
                Action::Reserve(input)
            }
            2 | 3 => {
                let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                let blocked: Vec<ProviderOperation> = model
                    .retained_unbound_blocks()
                    .into_iter()
                    .chain(model.quarantined.iter().map(|q| q.operation))
                    .chain(planner.unretained.iter().copied())
                    .collect();
                if let Some(op) = pick(rng, &blocked) {
                    input.payment = *op;
                }
                Action::Reserve(input)
            }
            4 | 5 => conflict_action(planner, rng, model),
            _ => background(planner, rng),
        },
        Family::P3SlotLifecycle => match rng.below(10) {
            0..=2 => Action::Send(
                pick(
                    rng,
                    &orders_where(model, |o| {
                        matches!(o.phase, OrderState::Held | OrderState::PaymentUnknown)
                    }),
                )
                .map(|o| o.input.order_id)
                .unwrap_or(id(99_999)),
            ),
            3 => {
                if let Some(order) = pick(
                    rng,
                    &orders_where(model, |o| o.phase == OrderState::PaymentUnknown),
                ) {
                    ctx.now_ms = ctx.now_ms.max(order.input.expires_at_ms);
                    Action::Expire(order.input.order_id)
                } else {
                    background(planner, rng)
                }
            }
            4 => Action::Cancel(model.epoch + 1),
            5 => Action::Owner(writer(model.writer.generation + 1)),
            6 | 7 => {
                let event = fresh_capture_event(planner);
                match pick(rng, &model.reservations) {
                    Some(reservation) => {
                        let order = model
                            .orders
                            .iter()
                            .find(|o| o.input.order_id == reservation.order_id)
                            .unwrap();
                        Action::Capture(capture_for(&order.input, event))
                    }
                    None => background(planner, rng),
                }
            }
            8 => {
                let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                input.expires_at_ms = ctx.now_ms;
                Action::Reserve(input)
            }
            _ => background(planner, rng),
        },
        Family::P4EventVsEconomic => match rng.below(8) {
            0 | 1 => match pick(rng, &model.events) {
                Some(event) => Action::Capture(event.observation.clone()),
                None => background(planner, rng),
            },
            2 | 3 => conflict_action(planner, rng, model),
            4 | 5 => {
                let event = fresh_capture_event(planner);
                match pick(rng, &orders_where(model, |o| o.capture.is_some())) {
                    Some(order) => {
                        let mut observation = capture_for(&order.input, event);
                        if rng.below(2) == 0 {
                            observation.amount = amount(999, 1);
                        }
                        Action::Capture(observation)
                    }
                    None => background(planner, rng),
                }
            }
            6 => {
                let event = fresh_capture_event(planner);
                let mut observation = capture_for(
                    &request(1, Selection::GeneralAdmission { count: 1 }, 9),
                    event,
                );
                observation.operation = operation(40_000 + planner.fresh);
                Action::Capture(observation)
            }
            _ => background(planner, rng),
        },
        Family::P5QuarantineEvidence => match rng.below(9) {
            0..=2 => conflict_action(planner, rng, model),
            3 => {
                let mut input = fresh_request(planner, rng, model, ctx.now_ms);
                let blocked: Vec<ProviderOperation> = model
                    .retained_unbound_blocks()
                    .into_iter()
                    .chain(planner.unretained.iter().copied())
                    .collect();
                if let Some(op) = pick(rng, &blocked) {
                    input.payment = *op;
                }
                Action::Reserve(input)
            }
            4 => Action::Send(
                pick(rng, &orders_where(model, |o| o.review))
                    .map(|o| o.input.order_id)
                    .unwrap_or(id(99_999)),
            ),
            5 => Action::Owner(writer(model.writer.generation + 1)),
            6 => Action::Cancel(model.epoch + 1),
            7 => Action::Expire(
                pick(rng, &model.quarantined)
                    .map(|q| q.order_id)
                    .unwrap_or(id(99_999)),
            ),
            _ => background(planner, rng),
        },
        Family::P6ReturnRequiredReview => match rng.below(10) {
            0 | 1 => {
                // Late matching capture: past the deadline, after expiry release or after cancellation.
                let event = fresh_capture_event(planner);
                match pick(rng, &orders_where(model, |o| o.capture.is_none())) {
                    Some(order) => {
                        match rng.below(3) {
                            0 => ctx.now_ms = ctx.now_ms.max(order.input.expires_at_ms),
                            1 if order.phase == OrderState::Held && !model.cancelled => {
                                return Action::Cancel(model.epoch + 1);
                            }
                            _ => {}
                        }
                        Action::Capture(capture_for(&order.input, event))
                    }
                    None => background(planner, rng),
                }
            }
            2 => {
                if let Some(order) =
                    pick(rng, &orders_where(model, |o| o.phase == OrderState::Held))
                {
                    ctx.now_ms = ctx.now_ms.max(order.input.expires_at_ms);
                    Action::Expire(order.input.order_id)
                } else {
                    background(planner, rng)
                }
            }
            3..=5 => {
                let event = fresh_capture_event(planner);
                match pick(
                    rng,
                    &orders_where(model, |o| o.phase == OrderState::ReturnRequired),
                ) {
                    Some(order) => {
                        let mut observation = capture_for(&order.input, event);
                        match rng.below(3) {
                            0 => observation.amount = amount(999, 1),
                            1 => {
                                if let Some(stored) = model
                                    .events
                                    .iter()
                                    .find(|e| e.bound_order == Some(order.input.order_id))
                                {
                                    observation = stored.observation.clone();
                                }
                            }
                            _ => {}
                        }
                        Action::Capture(observation)
                    }
                    None => background(planner, rng),
                }
            }
            6 => conflict_action(planner, rng, model),
            _ => background(planner, rng),
        },
        Family::P7ObservationBudget => match rng.below(9) {
            0 | 1 => Action::Send(
                pick(
                    rng,
                    &orders_where(model, |o| {
                        matches!(o.phase, OrderState::Held | OrderState::PaymentUnknown)
                    }),
                )
                .map(|o| o.input.order_id)
                .unwrap_or(id(99_999)),
            ),
            2 | 3 => conflict_action(planner, rng, model),
            4 | 5 => {
                let event = fresh_capture_event(planner);
                match pick(rng, &model.orders) {
                    Some(order) => Action::Capture(capture_for(&order.input, event)),
                    None => background(planner, rng),
                }
            }
            6 => {
                let event = fresh_capture_event(planner);
                match pick(rng, &model.reservations) {
                    Some(reservation) => {
                        let order = model
                            .orders
                            .iter()
                            .find(|o| o.input.order_id == reservation.order_id)
                            .unwrap();
                        Action::Capture(capture_for(&order.input, event))
                    }
                    None => background(planner, rng),
                }
            }
            _ => background(planner, rng),
        },
    }
}

/// Same event identity as a stored event, different payload: names one bound
/// operation, two bound operations, or a bound plus an unbound operation.
fn conflict_action(planner: &mut Planner, rng: &mut Generator, model: &Model) -> Action {
    planner.fresh += 1;
    let fallback_event = 5_000 + planner.fresh;
    match pick(rng, &model.events) {
        Some(event) => {
            let mut observation = event.observation.clone();
            match rng.below(4) {
                0 => observation.evidence_hash = Hash32::from_bytes([61; 32]),
                1 => observation.amount = amount(999, 1),
                2 => {
                    if let Some(binding) = pick(rng, &model.bindings) {
                        observation.operation = binding.operation;
                    }
                    observation.evidence_hash = Hash32::from_bytes([62; 32]);
                }
                _ => {
                    planner.fresh += 1;
                    observation.operation = operation(40_000 + planner.fresh);
                }
            }
            Action::Capture(observation)
        }
        None => match pick(rng, &model.orders) {
            Some(order) => Action::Capture(capture_for(&order.input, fallback_event)),
            None => Action::Capture(capture_for(
                &request(1, Selection::GeneralAdmission { count: 1 }, 9),
                fallback_event,
            )),
        },
    }
}

/// Relation-aware trace: family-directed moves consult only the independent model.
fn relation_trace(case: &Case, family: Family, seed: u64) -> Vec<Step> {
    let (_, mut model) = initial(case);
    let mut rng = Generator(seed ^ ((family as u64 + 1) << 56));
    let mut planner = Planner::default();
    let mut result = Vec::new();
    for _ in 0..RELATION_STEPS {
        let mut ctx = Context {
            fence: model.writer,
            now_ms: model.time + rng.below(3),
            semantics_version: 4,
        };
        let action = relation_action(family, &mut planner, &mut rng, &model, &mut ctx);
        let step = Step { ctx, action };
        if let (
            Action::Capture(observation),
            Reply::Capture(Err(kix_kernel::KernelError::Capacity)),
        ) = (&step.action, model.apply(&step))
        {
            let prior = model.events.iter().any(|e| {
                e.identity.event_id == observation.event_id
                    && e.identity.provider == observation.operation.provider
                    && e.identity.account == observation.operation.account
            });
            if prior
                && model.binding(observation.operation).is_none()
                && !planner.unretained.contains(&observation.operation)
            {
                planner.unretained.push(observation.operation);
            }
        }
        result.push(step);
    }
    result
}

fn relation_cases() -> [Case; 4] {
    [
        Case {
            layout: InventoryCase::Seats(vec![6, 4]),
            limits: Limits {
                commands: 64,
                orders: 24,
                observations: 12,
            },
        },
        Case {
            layout: InventoryCase::Ga(5),
            limits: Limits {
                commands: 64,
                orders: 16,
                observations: 4,
            },
        },
        Case {
            layout: InventoryCase::Seats(vec![3]),
            limits: Limits {
                commands: 64,
                orders: 8,
                observations: 2,
            },
        },
        Case {
            layout: InventoryCase::Seats(vec![2, 2]),
            limits: Limits {
                commands: 6,
                orders: 4,
                observations: 6,
            },
        },
    ]
}

/// Classes that must be reached for a family to count as deliberately exercised.
fn required_classes(family: Family) -> &'static [&'static str] {
    match family {
        Family::P1CommandIdentity => &[
            "first_result_held",
            "first_result_rejected",
            "replay_exact",
            "replay_of_accepted_first_result",
            "replay_of_rejected_first_result",
            "replay_after_state_changed",
            "replay_under_stale_context",
            "altered_payload_conflict",
            "altered_payload_conflict_under_stale_context",
            "altered_field_order_id",
            "altered_field_amount",
            "altered_field_operation",
            "altered_field_expiry",
            "altered_field_selection",
            "replay_lookup_outranked_by_scope_or_semantics",
        ],
        Family::P2OperationBinding => &[
            "binding_created",
            "rejected_no_binding",
            "reuse_of_bound_operation_rejected",
            "retained_unbound_operation_refused",
            "bound_quarantined_operation_refused",
            "sibling_operation_bound_independently",
            "unretained_conflict_operation_bound_later",
            "reserve_refused_for_capacity",
        ],
        Family::P3SlotLifecycle => &[
            "send_reserves_one_slot",
            "unknown_retry_reuses_reservation",
            "slot_capacity_refused",
            "expiry_check_keeps_reservation",
            "unknown_order_not_released_by_ttl",
            "held_order_expired",
            "owner_replacement_keeps_reservation",
            "scope_cancellation_keeps_reservation",
            "capture_consumes_own_reservation",
            "capture_leaves_other_reservations_intact",
        ],
        Family::P4EventVsEconomic => &[
            "identical_event_replay",
            "same_identity_altered_payload_conflict",
            "retained_conflict_replayed_without_new_evidence",
            "conflict_names_one_bound_operation",
            "conflict_names_two_bound_operations",
            "conflict_names_bound_and_unbound",
            "same_operation_new_event_identity",
            "duplicate_economic_effect",
            "later_mismatch_raises_review",
            "first_capture_confirmed",
            "first_capture_reviewed",
            "unbound_capture_not_stored",
        ],
        Family::P5QuarantineEvidence => &[
            "bound_conflict_quarantines_order",
            "bound_quarantine_reconfirmed",
            "retained_unbound_evidence_present",
            "retained_unbound_blocks_binding",
            "retained_unbound_ban_coexists_with_bound_sibling",
            "unretained_unbound_conflict_at_full_budget",
            "unretained_conflict_left_no_ban",
            "binding_accepted_while_others_quarantined",
            "reviewed_order_cannot_send",
            "bound_quarantine_survives_owner_replacement",
            "bound_quarantine_survives_scope_cancellation",
            "bound_quarantine_survives_expiry_check",
        ],
        Family::P6ReturnRequiredReview => &[
            "late_matching_capture_return_required",
            "return_required_past_deadline",
            "return_required_after_expiry_release",
            "return_required_after_cancellation",
            "return_required_on_already_reviewed_order",
            "mismatch_after_return_required_keeps_phase",
            "retained_capture_preserved_under_mismatch",
            "duplicate_effect_after_return_required",
            "no_second_inventory_release",
            "event_replay_after_return_required",
            "review_set_while_return_required_persists",
            "review_predicate_sticky_across_step",
        ],
        Family::P7ObservationBudget => &[
            "reserved_slot_charged_to_budget",
            "send_refused_at_limit",
            "conflict_retained",
            "conflict_admitted_at_last_unit",
            "conflict_refused_at_limit",
            "reserved_slot_converted_to_stored_event",
            "promised_capacity_honoured_at_full_budget",
            "unreserved_event_stored_within_budget",
            "unreserved_capture_refused_at_limit",
            "budget_full_after_step",
        ],
    }
}

#[test]
fn relation_aware_generated_traces_reach_every_property_family() {
    assert_eq!(SEMANTICS_VERSION, 4);
    let cases = relation_cases();
    let mut total = Coverage::new();
    let mut per_family = String::new();
    for family in FAMILIES {
        let mut family_coverage = Coverage::new();
        let mut transitions = 0_u64;
        for (case_no, case) in cases.iter().enumerate() {
            for seed in 1..=RELATION_SEEDS {
                let inputs = relation_trace(case, family, seed);
                transitions += inputs.len() as u64;
                match check_relations_trace(case, &inputs, false, true) {
                    Ok(coverage) => family_coverage.merge(&coverage),
                    Err(failure) => {
                        let minimal = shrink_with(&inputs, |trial| {
                            check_relations_trace(case, trial, false, true).is_err()
                        });
                        let report = format!(
                            "family={}; case={case_no}; seed={seed}; config={case:?}\nstep={}; kind={}\n{}\nshrunk_steps={}\nshrunk={minimal:#?}\n",
                            family.tag(),
                            failure.step,
                            failure.kind,
                            failure.detail,
                            minimal.len(),
                        );
                        fs::write(evidence_dir().join("e4-relation-failure.txt"), &report).unwrap();
                        panic!("{report}");
                    }
                }
            }
        }
        let missing: Vec<&str> = required_classes(family)
            .iter()
            .copied()
            .filter(|class| family_coverage.count(family, class) == 0)
            .collect();
        assert!(
            missing.is_empty(),
            "{} traces did not reach {missing:?}; reached {:?}",
            family.tag(),
            family_coverage.classes(family)
        );
        per_family.push_str(&format!(
            "{{\"family\":\"{}\",\"configurations\":{},\"seeds_per_configuration\":{RELATION_SEEDS},\"steps_per_sequence\":{RELATION_STEPS},\"compared_transitions\":{transitions},\"required_classes\":{},\"reached\":{}}},",
            family.tag(),
            cases.len(),
            required_classes(family).len(),
            family_coverage.to_json(),
        ));
        total.merge(&family_coverage);
    }
    for family in FAMILIES {
        assert!(total.family_total(family) > 0);
    }
    per_family.pop();
    fs::write(evidence_dir().join("e4-relation-coverage.json"), format!(
        "{{\"semantics\":4,\"kernel_blob\":\"{LOCKED_KERNEL}\",\"generator\":\"family-directed SplitMix, seed xor family tag; consults the independent model only\",\"baseline_unchanged\":{{\"cases\":{CASES},\"steps\":{STEPS}}},\"families\":[{per_family}],\"total\":{},\"scope\":\"reachability of transition classes in the generated corpus; not completeness, not durability\",\"failures\":0}}\n",
        total.to_json(),
    )).unwrap();
}

/// The baseline corpus is unchanged; this records which relation classes it
/// reaches only incidentally, so the additive suite can be compared against it.
#[test]
fn baseline_corpus_relation_coverage_is_inventoried_not_retuned() {
    let cases = baseline_cases();
    let mut total = Coverage::new();
    for case in &cases {
        for seed in 1..=CASES {
            let inputs = trace(case, seed);
            assert_eq!(inputs.len(), STEPS);
            let coverage = check_relations_trace(case, &inputs, false, true)
                .unwrap_or_else(|failure| panic!("baseline seed {seed}: {failure:?}"));
            total.merge(&coverage);
        }
    }
    let mut unreached = String::new();
    for family in FAMILIES {
        for class in required_classes(family) {
            if total.count(family, class) == 0 {
                unreached.push_str(&format!("{}:{class}\n", family.tag()));
            }
        }
    }
    fs::write(
        evidence_dir().join("e4-baseline-relation-inventory.txt"),
        format!("baseline cases={CASES} steps={STEPS}\nreached={}\nrequired_classes_not_reached_by_baseline:\n{unreached}", total.to_json()),
    )
    .unwrap();
}

/// One row of the Task 003-C crosswalk: a frozen Task 001 deterministic test in
/// `contract_edge_cases.rs` mapped to the observer classes whose generated
/// witnesses establish the same contract predicate on the reference model.
struct CrosswalkRow {
    deterministic_test: &'static str,
    predicate: &'static str,
    /// Observer classes that together cover the predicate (family, class).
    classes: &'static [(Family, &'static str)],
    /// Subset of `classes` added by Task 003-C; empty when pre-existing evidence sufficed.
    anchors: &'static [(Family, &'static str)],
}

fn crosswalk_rows() -> [CrosswalkRow; 8] {
    use Family::*;
    [
        CrosswalkRow {
            deterministic_test: "rejection_replay_stays_immutable_after_the_blocking_hold_is_released",
            predicate: "a rejected first result replays read-only even after the blocking hold was released and the selection is free again; only a new command identity can take the released seat",
            classes: &[
                (P1CommandIdentity, "replay_of_rejected_first_result"),
                (P1CommandIdentity, "replay_after_state_changed"),
                (
                    P1CommandIdentity,
                    "rejected_replay_after_unavailable_cause_cleared",
                ),
                (
                    P1CommandIdentity,
                    "new_identity_holds_selection_rejected_earlier",
                ),
                (
                    P1CommandIdentity,
                    "new_identity_reholds_same_operation_rejected_unavailable_earlier",
                ),
                (P2OperationBinding, "rejected_no_binding"),
            ],
            anchors: &[
                (
                    P1CommandIdentity,
                    "rejected_replay_after_unavailable_cause_cleared",
                ),
                (
                    P1CommandIdentity,
                    "new_identity_reholds_same_operation_rejected_unavailable_earlier",
                ),
            ],
        },
        CrosswalkRow {
            deterministic_test: "altered_payload_conflicts_before_fence_and_clock_guards",
            predicate: "same identity with an altered payload is CommandConflict and leaves state unchanged even under a stale execution fence or a regressed clock; the unchanged payload still replays",
            classes: &[
                (P1CommandIdentity, "altered_payload_conflict"),
                (P1CommandIdentity, "altered_field_order_id"),
                (P1CommandIdentity, "altered_field_operation"),
                (P1CommandIdentity, "altered_field_expiry"),
                (P1CommandIdentity, "altered_field_selection"),
                (
                    P1CommandIdentity,
                    "altered_payload_conflict_under_stale_fence",
                ),
                (
                    P1CommandIdentity,
                    "altered_payload_conflict_under_regressed_clock",
                ),
                (P1CommandIdentity, "replay_exact"),
            ],
            anchors: &[
                (
                    P1CommandIdentity,
                    "altered_payload_conflict_under_stale_fence",
                ),
                (
                    P1CommandIdentity,
                    "altered_payload_conflict_under_regressed_clock",
                ),
            ],
        },
        CrosswalkRow {
            deterministic_test: "replay_lookup_is_guarded_by_scope_and_semantics_only",
            predicate: "a known identity under a foreign scope is WrongScope and under another semantics version is UnsupportedSemantics without state change; a regressed clock or a foreign fence does not stop the read-only replay",
            classes: &[
                (P1CommandIdentity, "replay_lookup_outranked_by_scope"),
                (P1CommandIdentity, "replay_lookup_outranked_by_semantics"),
                (P1CommandIdentity, "replay_under_regressed_clock"),
                (P1CommandIdentity, "replay_under_stale_fence"),
            ],
            anchors: &[
                (P1CommandIdentity, "replay_lookup_outranked_by_scope"),
                (P1CommandIdentity, "replay_lookup_outranked_by_semantics"),
                (P1CommandIdentity, "replay_under_regressed_clock"),
                (P1CommandIdentity, "replay_under_stale_fence"),
            ],
        },
        CrosswalkRow {
            deterministic_test: "expiry_instant_is_treated_consistently_by_every_entry_point",
            predicate: "at now == expires_at the expiry check releases a Held order, a reservation expiring now is InvalidRequest, an external send is InvalidTransition without state change, and a matching capture is ReturnRequired",
            classes: &[
                (P3SlotLifecycle, "held_order_expired_at_exact_instant"),
                (
                    P3SlotLifecycle,
                    "reservation_refused_at_exact_expiry_instant",
                ),
                (P3SlotLifecycle, "send_refused_at_exact_deadline"),
                (P3SlotLifecycle, "held_send_refused_at_exact_deadline"),
                (P6ReturnRequiredReview, "return_required_at_exact_deadline"),
                (
                    P6ReturnRequiredReview,
                    "held_return_required_at_exact_deadline",
                ),
            ],
            anchors: &[
                (P3SlotLifecycle, "held_order_expired_at_exact_instant"),
                (
                    P3SlotLifecycle,
                    "reservation_refused_at_exact_expiry_instant",
                ),
                (P3SlotLifecycle, "held_send_refused_at_exact_deadline"),
                (
                    P6ReturnRequiredReview,
                    "held_return_required_at_exact_deadline",
                ),
            ],
        },
        CrosswalkRow {
            deterministic_test: "unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot",
            predicate: "an UNKNOWN send retry at or after the deadline is InvalidTransition and keeps phase, inventory and the reserved slot; the expiry check does not release the UNKNOWN order; a later matching capture consumes that slot into ReturnRequired",
            classes: &[
                (
                    P3SlotLifecycle,
                    "unknown_retry_refused_past_deadline_keeps_reservation",
                ),
                (
                    P3SlotLifecycle,
                    "unknown_retry_refused_at_exact_deadline_keeps_reservation",
                ),
                (
                    P3SlotLifecycle,
                    "unknown_retry_refused_strictly_after_deadline_keeps_reservation",
                ),
                (P3SlotLifecycle, "unknown_order_not_released_by_ttl"),
                (P3SlotLifecycle, "expiry_check_keeps_reservation"),
                (
                    P3SlotLifecycle,
                    "late_capture_converts_reservation_to_return_required",
                ),
            ],
            anchors: &[
                (
                    P3SlotLifecycle,
                    "unknown_retry_refused_past_deadline_keeps_reservation",
                ),
                (
                    P3SlotLifecycle,
                    "unknown_retry_refused_at_exact_deadline_keeps_reservation",
                ),
                (
                    P3SlotLifecycle,
                    "unknown_retry_refused_strictly_after_deadline_keeps_reservation",
                ),
                (
                    P3SlotLifecycle,
                    "late_capture_converts_reservation_to_return_required",
                ),
            ],
        },
        CrosswalkRow {
            deterministic_test: "return_required_is_stable_under_further_late_evidence",
            predicate: "after ReturnRequired a duplicate matching event is DuplicateEffect without a second inventory release, a mismatching event is Review that sets review while phase and retained capture persist, and an external send is refused without state change",
            classes: &[
                (
                    P6ReturnRequiredReview,
                    "duplicate_effect_after_return_required",
                ),
                (P6ReturnRequiredReview, "no_second_inventory_release"),
                (
                    P6ReturnRequiredReview,
                    "mismatch_after_return_required_keeps_phase",
                ),
                (
                    P6ReturnRequiredReview,
                    "retained_capture_preserved_under_mismatch",
                ),
                (
                    P6ReturnRequiredReview,
                    "review_set_while_return_required_persists",
                ),
                (P6ReturnRequiredReview, "return_required_order_cannot_send"),
            ],
            anchors: &[(P6ReturnRequiredReview, "return_required_order_cannot_send")],
        },
        CrosswalkRow {
            deterministic_test: "bound_quarantine_survives_owner_change_expiry_and_cancellation",
            predicate: "a conflict naming two bound operations quarantines both orders; owner replacement, an expiry that actually releases the order, and scope cancellation keep the quarantine set and review; the quarantined order still cannot send",
            classes: &[
                (P4EventVsEconomic, "conflict_names_two_bound_operations"),
                (
                    P5QuarantineEvidence,
                    "bound_quarantine_survives_owner_replacement",
                ),
                (
                    P5QuarantineEvidence,
                    "bound_quarantine_survives_expiry_release",
                ),
                (
                    P5QuarantineEvidence,
                    "bound_quarantine_survives_scope_cancellation",
                ),
                (
                    P5QuarantineEvidence,
                    "quarantined_order_cannot_send_after_expiry_or_cancellation",
                ),
                (
                    P5QuarantineEvidence,
                    "quarantined_order_unsendable_after_owner_expiry_cancellation_sequence",
                ),
            ],
            anchors: &[
                (
                    P5QuarantineEvidence,
                    "bound_quarantine_survives_expiry_release",
                ),
                (
                    P5QuarantineEvidence,
                    "quarantined_order_unsendable_after_owner_expiry_cancellation_sequence",
                ),
            ],
        },
        CrosswalkRow {
            deterministic_test: "retained_unbound_conflict_bans_the_identity_for_any_future_order",
            predicate: "a retained conflict naming a bound and an unbound operation quarantines only the bound order; any future order reusing the unbound identity is OperationQuarantined without creating an order or binding; a sibling operation of the same provider/account still binds",
            classes: &[
                (P4EventVsEconomic, "conflict_names_bound_and_unbound"),
                (P5QuarantineEvidence, "retained_unbound_evidence_present"),
                (P2OperationBinding, "retained_unbound_operation_refused"),
                (
                    P5QuarantineEvidence,
                    "retained_unbound_ban_coexists_with_bound_sibling",
                ),
                (
                    P5QuarantineEvidence,
                    "sibling_of_retained_unbound_ban_bound_independently",
                ),
            ],
            anchors: &[(
                P5QuarantineEvidence,
                "sibling_of_retained_unbound_ban_bound_independently",
            )],
        },
    ]
}

#[derive(Clone, Debug)]
struct Witness {
    corpus: String,
    case: usize,
    seed: u64,
    step: u64,
}

#[derive(Default)]
struct ClassEvidence {
    relation_count: u64,
    relation_first: Option<Witness>,
    baseline_count: u64,
    baseline_first: Option<Witness>,
}

fn record_class_evidence(
    evidence: &mut std::collections::BTreeMap<(Family, &'static str), ClassEvidence>,
    coverage: &Coverage,
    corpus: &str,
    case: usize,
    seed: u64,
    baseline: bool,
) {
    for (key, entry) in evidence.iter_mut() {
        let n = coverage.count(key.0, key.1);
        if n == 0 {
            continue;
        }
        let witness = Witness {
            corpus: corpus.to_string(),
            case,
            seed,
            step: coverage.first_step(key.0, key.1).unwrap(),
        };
        if baseline {
            entry.baseline_count += n;
            entry.baseline_first.get_or_insert(witness);
        } else {
            entry.relation_count += n;
            entry.relation_first.get_or_insert(witness);
        }
    }
}

/// Task 003-C: every frozen Task 001 deterministic predicate must be reached by
/// the relation-aware generated corpus (unchanged parameters) with a stable
/// first witness `family/config/seed/step`. The historical baseline corpus is
/// inventoried alongside, never retuned. No deterministic trace is replayed here.
#[test]
fn task_001_deterministic_edge_cases_are_cross_validated_by_generated_witnesses() {
    let rows = crosswalk_rows();
    let mut evidence = std::collections::BTreeMap::new();
    for row in &rows {
        for key in row.classes {
            evidence.entry(*key).or_insert_with(ClassEvidence::default);
        }
    }
    let mut extra = std::collections::BTreeMap::<String, GateEvidence>::new();
    for row in 0..8 {
        for key in evidence_gates::required(row) {
            extra.entry(key).or_default();
        }
    }
    let mut readonly = [0_u64; 2];
    let cases = relation_cases();
    for family in FAMILIES {
        for (case_no, case) in cases.iter().enumerate() {
            for seed in 1..=RELATION_SEEDS {
                let inputs = relation_trace(case, family, seed);
                let coverage = check_relations_trace(case, &inputs, false, true)
                    .unwrap_or_else(|failure| panic!("{} seed {seed}: {failure:?}", family.tag()));
                record_class_evidence(&mut evidence, &coverage, family.tag(), case_no, seed, false);
                record_gate_evidence(&mut extra, &coverage, family.tag(), case_no, seed, false);
                readonly[0] += coverage.exact_read_only_checks;
            }
        }
    }
    for (case_no, case) in baseline_cases().iter().enumerate() {
        for seed in 1..=CASES {
            let inputs = trace(case, seed);
            let coverage = check_relations_trace(case, &inputs, false, true)
                .unwrap_or_else(|failure| panic!("baseline seed {seed}: {failure:?}"));
            record_class_evidence(&mut evidence, &coverage, "baseline", case_no, seed, true);
            record_gate_evidence(&mut extra, &coverage, "baseline", case_no, seed, true);
            readonly[1] += coverage.exact_read_only_checks;
        }
    }
    let witness_json = |w: &Option<Witness>| match w {
        Some(w) => format!(
            "{{\"corpus\":\"{}\",\"config\":{},\"seed\":{},\"step\":{}}}",
            w.corpus, w.case, w.seed, w.step
        ),
        None => "null".to_string(),
    };
    let mut unreached = Vec::new();
    let mut rows_json = String::new();
    for (row_no, row) in rows.iter().enumerate() {
        let extra_keys = evidence_gates::required(row_no);
        let mut extra_json = Vec::new();
        for key in &extra_keys {
            let e = &extra[key];
            if e.relation_count == 0 {
                unreached.push(format!("{}:{key}", row.deterministic_test));
            }
            extra_json.push(format!("{{\"gate\":{},\"relation_count\":{},\"relation_first\":{},\"baseline_count\":{},\"baseline_first\":{}}}", json_string(key), e.relation_count, optional_json(&e.relation_first), e.baseline_count, optional_json(&e.baseline_first)));
        }
        let row_proven = row
            .classes
            .iter()
            .all(|key| evidence[key].relation_count > 0)
            && extra_keys.iter().all(|key| extra[key].relation_count > 0);
        let strength = if row_proven { "sufficient" } else { "partial" };
        let mut classes_json = String::new();
        for (family, class) in row.classes {
            let entry = &evidence[&(*family, *class)];
            if entry.relation_count == 0 {
                unreached.push(format!(
                    "{}:{}:{class}",
                    row.deterministic_test,
                    family.tag()
                ));
            }
            classes_json.push_str(&format!(
                "{{\"family\":\"{}\",\"class\":\"{class}\",\"anchor\":{},\"relation_count\":{},\"relation_first_witness\":{},\"baseline_count\":{},\"baseline_first_witness\":{}}},",
                family.tag(),
                row.anchors.contains(&(*family, *class)),
                entry.relation_count,
                witness_json(&entry.relation_first),
                entry.baseline_count,
                witness_json(&entry.baseline_first),
            ));
        }
        classes_json.pop();
        rows_json.push_str(&format!(
            "{{\"deterministic_test\":\"{}\",\"predicate\":\"{}\",\"strength\":\"{strength}\",\"classes\":[{classes_json}],\"additional_required_gates\":[{}]}},",
            row.deterministic_test, row.predicate, extra_json.join(",")
        ));
    }
    rows_json.pop();
    fs::write(evidence_dir().join("e4-deterministic-crosswalk.json"), format!(
        "{{\"semantics\":4,\"kernel_blob\":\"{LOCKED_KERNEL}\",\"deterministic_source\":\"runtime/crates/kix-kernel/tests/contract_edge_cases.rs\",\"relation_corpus\":{{\"configurations\":{},\"seeds_per_configuration\":{RELATION_SEEDS},\"steps_per_sequence\":{RELATION_STEPS}}},\"baseline_corpus\":{{\"cases\":{CASES},\"steps\":{STEPS}}},\"rows\":[{rows_json}],\"unreached_in_relation_corpus\":{unreached:?},\"scope\":\"generated witnesses reach each mapped predicate class on the source-informed model; not independence, completeness or durability\"}}\n",
        cases.len(),
    )).unwrap();
    let summary = extra
        .iter()
        .map(|(key, e)| {
            format!(
                "gate={key} relation={} baseline={} first={}\n",
                e.relation_count,
                e.baseline_count,
                e.relation_first
                    .as_deref()
                    .unwrap_or("none")
                    .split(';')
                    .next()
                    .unwrap()
            )
        })
        .collect::<String>();
    let summary = format!(
        "whole_kernel_read_only_checks relation={} baseline={}\n{summary}",
        readonly[0], readonly[1]
    );
    fs::write(evidence_dir().join("e4-evidence-gates.txt"), &summary).unwrap();
    // Bypass libtest capture so exact-head CI logs contain the compact evidence.
    use std::io::Write as _;
    std::io::stdout()
        .lock()
        .write_all(summary.as_bytes())
        .unwrap();
    export_row8_generated_identity_evidence(&cases[0]);
    assert!(
        unreached.is_empty(),
        "crosswalk classes not reached by the relation-aware corpus: {unreached:#?}"
    );
}

fn baseline_cases() -> [Case; 4] {
    [
        Case {
            layout: InventoryCase::Seats(vec![70, 10]),
            limits: Limits {
                commands: 64,
                orders: 32,
                observations: 16,
            },
        },
        Case {
            layout: InventoryCase::Seats(vec![2, 2]),
            limits: Limits {
                commands: 2,
                orders: 16,
                observations: 2,
            },
        },
        Case {
            layout: InventoryCase::Ga(6),
            limits: Limits {
                commands: 32,
                orders: 16,
                observations: 4,
            },
        },
        Case {
            layout: InventoryCase::Seats(vec![1, 1, 2]),
            limits: Limits {
                commands: 16,
                orders: 8,
                observations: 1,
            },
        },
    ]
}

/// The property layer is itself sensitive: with the model-only quarantine
/// omission and no kernel in the loop, a generated P5 trace fails on the
/// `bound conflict did not quarantine` property and the failure shrinks.
#[test]
fn relation_properties_detect_model_only_quarantine_omission_and_shrink() {
    let case = relation_cases()[2].clone();
    let mut detected = None;
    for seed in 1..=RELATION_SEEDS {
        let inputs = relation_trace(&case, Family::P5QuarantineEvidence, seed);
        assert!(check_relations_trace(&case, &inputs, false, false).is_ok());
        if let Err(failure) = check_relations_trace(&case, &inputs, true, false) {
            detected = Some((seed, inputs, failure));
            break;
        }
    }
    let (seed, inputs, failure) = detected.expect("a P5 trace reaches the injected omission");
    assert_eq!(failure.kind, "transition_property");
    let minimal = shrink_with(&inputs, |trial| {
        check_relations_trace(&case, trial, true, false).is_err()
    });
    assert!(minimal.len() < inputs.len());
    assert!(check_relations_trace(&case, &minimal, false, false).is_ok());
    fs::write(evidence_dir().join("e4-relation-property-sensitivity.txt"), format!(
        "injection=independent-model-only; kernel not in loop; kernel unchanged\nseed={seed}\nfailure={failure:?}\noriginal_steps={}\nshrunk_steps={}\ntrace={minimal:#?}\n", inputs.len(), minimal.len(),
    )).unwrap();
}

fn evidence_dir() -> PathBuf {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../.local/verification/ktx");
    fs::create_dir_all(&path).unwrap();
    path
}

#[test]
fn locked_v4_matches_independent_state_model() {
    assert_eq!(SEMANTICS_VERSION, 4);
    let cases = baseline_cases();
    let mut actions = [0_u64; 6];
    for (case_no, case) in cases.iter().enumerate() {
        for seed in 1..=CASES {
            let inputs = trace(case, seed);
            for step in &inputs {
                let index = match step.action {
                    Action::Reserve(_) => 0,
                    Action::Send(_) => 1,
                    Action::Expire(_) => 2,
                    Action::Capture(_) => 3,
                    Action::Owner(_) => 4,
                    Action::Cancel(_) => 5,
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
    let case = Case {
        layout: InventoryCase::Seats(vec![4]),
        limits: Limits {
            commands: 8,
            orders: 8,
            observations: 1,
        },
    };
    let a = request(1, Selection::Seats { first: 0, count: 1 }, 100);
    let b = request(2, Selection::Seats { first: 1, count: 1 }, 100);
    let observation = |input: &Reserve| CaptureObservation {
        event_id: id(500),
        operation: input.payment,
        amount: input.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    };
    let inputs = vec![
        Step {
            ctx: context(1),
            action: Action::Expire(id(99_999)),
        },
        Step {
            ctx: context(2),
            action: Action::Reserve(a.clone()),
        },
        Step {
            ctx: context(3),
            action: Action::Reserve(b.clone()),
        },
        Step {
            ctx: context(4),
            action: Action::Expire(a.order_id),
        },
        Step {
            ctx: context(5),
            action: Action::Capture(observation(&a)),
        },
        Step {
            ctx: context(6),
            action: Action::Capture(observation(&b)),
        },
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

/// Model-only: the explicit schema relations and their consistency checker.
/// No Kernel call; this is not a second copy of the kernel regressions.
#[test]
fn model_schema_relations_are_explicit_and_corruption_is_detected() {
    let case = Case {
        layout: InventoryCase::Seats(vec![4]),
        limits: Limits {
            commands: 8,
            orders: 8,
            observations: 4,
        },
    };
    let (_, mut model) = initial(&case);
    let held = request(1, Selection::Seats { first: 0, count: 1 }, 100);
    let unbound = kix_kernel::ProviderOperation {
        provider: id(850),
        account: id(851),
        operation: id(77),
    };
    let mut blocked = request(2, Selection::Seats { first: 1, count: 1 }, 100);
    blocked.payment = unbound;
    let step = |model: &mut Model, now: u64, action: Action| {
        let ctx = Context {
            fence: model.writer,
            now_ms: now,
            semantics_version: 4,
        };
        model.apply(&Step { ctx, action });
        model.check_relations().unwrap();
    };

    step(&mut model, 1, Action::Reserve(held.clone()));
    assert_eq!(
        model.binding(held.payment).map(|b| b.order_id),
        Some(held.order_id)
    );

    step(&mut model, 2, Action::Send(held.order_id));
    let reservation = model.reservation(held.payment).expect("reserved slot");
    assert_eq!(reservation.order_id, held.order_id);
    step(&mut model, 3, Action::Expire(held.order_id));
    step(&mut model, 4, Action::Owner(writer(2)));
    assert_eq!(model.reservation(held.payment), Some(reservation));

    let first = CaptureObservation {
        event_id: id(500),
        operation: held.payment,
        amount: held.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    };
    step(&mut model, 200, Action::Capture(first.clone()));
    assert_eq!(model.reservation(held.payment), None);
    assert_eq!(model.events.len(), 1);
    assert_eq!(model.events[0].bound_order, Some(held.order_id));
    let order = |model: &Model| model.orders[0].clone();
    assert_eq!(order(&model).phase, kix_kernel::OrderState::ReturnRequired);
    assert_eq!(order(&model).captured_amount(), Some(held.amount));

    // Later mismatching evidence: review coexists with ReturnRequired (0.6 §5.7.1).
    let mismatch = CaptureObservation {
        event_id: id(501),
        amount: amount(999, 1),
        ..first.clone()
    };
    step(&mut model, 201, Action::Capture(mismatch));
    assert!(order(&model).review);
    assert_eq!(order(&model).phase, kix_kernel::OrderState::ReturnRequired);
    assert_eq!(order(&model).captured_amount(), Some(held.amount));

    // Same event identity, different unbound operation: bound quarantine plus
    // retained-unbound blocking, without a speculative binding for the identity.
    let conflict = CaptureObservation {
        operation: unbound,
        ..first
    };
    step(&mut model, 202, Action::Capture(conflict));
    assert_eq!(
        model.quarantined,
        vec![reference::BoundQuarantine {
            operation: held.payment,
            order_id: held.order_id
        }]
    );
    assert_eq!(model.retained_unbound_blocks(), vec![unbound]);
    assert!(model.retained_unbound_blocked(unbound));
    assert!(!model.bound_quarantine_contains(unbound));
    step(&mut model, 203, Action::Reserve(blocked));
    assert_eq!(model.orders.len(), 1);
    assert!(model.binding(unbound).is_none());

    // Checker sensitivity on corrupted copies of the model state only.
    let mut corrupt = model.clone();
    corrupt.bindings.push(reference::OperationBinding {
        operation: unbound,
        order_id: id(4242),
    });
    assert!(corrupt.check_relations().is_err());

    let mut corrupt = model.clone();
    corrupt.reservations.push(reference::SlotReservation {
        operation: held.payment,
        order_id: held.order_id,
    });
    corrupt.reservations.push(reference::SlotReservation {
        operation: held.payment,
        order_id: held.order_id,
    });
    assert!(corrupt.check_relations().is_err());

    let mut corrupt = model.clone();
    corrupt.orders[0].capture = None;
    assert!(corrupt.check_relations().is_err());

    let mut corrupt = model.clone();
    corrupt.quarantined.push(reference::BoundQuarantine {
        operation: unbound,
        order_id: held.order_id,
    });
    assert!(corrupt.check_relations().is_err());

    fs::write(
        evidence_dir().join("e4-model-schema-relations.txt"),
        format!(
            "kernel_calls=0\nbindings={:?}\nreservations={:?}\nbound_quarantine={:?}\nretained_unbound_blocks={:?}\nstored_events={:?}\norders={:?}\n",
            model.bindings,
            model.reservations,
            model.quarantined,
            model.retained_unbound_blocks(),
            model.events,
            model.orders
        ),
    )
    .unwrap();
}

#[test]
fn capacity_two_sequence_is_observed_not_repaired() {
    let case = Case {
        layout: InventoryCase::Seats(vec![1]),
        limits: Limits {
            commands: 2,
            orders: 8,
            observations: 8,
        },
    };
    let (mut kernel, _) = initial(&case);
    let a = request(1, Selection::Seats { first: 0, count: 1 }, 10);
    let b = request(2, Selection::Seats { first: 0, count: 1 }, 10);
    let c = request(3, Selection::Seats { first: 0, count: 1 }, 100);
    let first = kernel.reserve(context(1), a.clone());
    let second = kernel.reserve(context(2), b);
    let expired = kernel.expire(context(10), a.order_id);
    let remaining = kernel.remaining();
    let new_request = kernel.reserve(context(11), c);
    assert!(matches!(
        first.as_ref().unwrap().original,
        ReserveOutcome::Held(_)
    ));
    assert_eq!(
        second.as_ref().unwrap().original,
        ReserveOutcome::Rejected(kix_kernel::Rejection::Unavailable)
    );
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
    for (relative, expected) in [
        ("src/lib.rs", LOCKED_KERNEL),
        ("tests/quarantine_capacity.rs", LOCKED_TEST),
    ] {
        let output = Command::new("git")
            .arg("hash-object")
            .arg(root.join(relative))
            .output()
            .unwrap();
        assert!(output.status.success());
        let actual = String::from_utf8(output.stdout).unwrap();
        assert_eq!(actual.trim(), expected);
        evidence.push_str(&format!("{relative}\t{actual}"));
    }
    for relative in [
        "tests/e4_state_model.rs",
        "tests/support/model_v4.rs",
        "tests/support/coverage_v4.rs",
        "tests/performance_harness.rs",
        "tests/support/perf_probe.rs",
        "examples/r1_perf_probe.rs",
    ] {
        let output = Command::new("git")
            .arg("hash-object")
            .arg(root.join(relative))
            .output()
            .unwrap();
        assert!(output.status.success());
        evidence.push_str(&format!(
            "{relative}\t{}",
            String::from_utf8(output.stdout).unwrap()
        ));
        // Diagnostic formatted copies only. Never writes to repository source.
        // Existing CI remains responsible for checking committed formatting.
        if let Ok(formatted) = Command::new("rustfmt")
            .args([
                "--edition",
                "2024",
                "--emit",
                "stdout",
                "--config",
                "skip_children=true",
            ])
            .arg(root.join(relative))
            .output()
            && formatted.status.success()
        {
            fs::write(
                evidence_dir().join(format!("formatted-{}", relative.replace('/', "__"))),
                formatted.stdout,
            )
            .unwrap();
        }
    }
    fs::write(
        evidence_dir().join("first-batch-source-blobs.txt"),
        evidence,
    )
    .unwrap();
}

// Task 003-C1 evidence serialization and narrowly scoped checker sensitivity.
#[derive(Default)]
struct GateEvidence {
    relation_count: usize,
    relation_first: Option<String>,
    baseline_count: usize,
    baseline_first: Option<String>,
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
fn optional_json(value: &Option<String>) -> String {
    value.as_deref().map_or_else(|| "null".into(), json_string)
}
fn record_gate_evidence(
    out: &mut std::collections::BTreeMap<String, GateEvidence>,
    coverage: &Coverage,
    corpus: &str,
    case: usize,
    seed: u64,
    baseline: bool,
) {
    for (key, e) in out {
        if let Some(witnesses) = coverage.gates.hits.get(key) {
            let first = format!("{corpus}/config{case}/seed{seed}: {}", witnesses[0]);
            if baseline {
                e.baseline_count += witnesses.len();
                e.baseline_first.get_or_insert(first);
            } else {
                e.relation_count += witnesses.len();
                e.relation_first.get_or_insert(first);
            }
        }
    }
}
fn export_row8_generated_identity_evidence(case: &Case) {
    let inputs = relation_trace(case, Family::P2OperationBinding, 1);
    let (mut kernel, mut model) = initial(case);
    let mut evidence = String::from(
        "Generated P2/config0/seed1, existing corpus; zero-based steps. Full typed IDs.\n",
    );
    for (n, step) in inputs.iter().enumerate() {
        let pre = model.clone();
        let reply = model.apply(step);
        assert_eq!(apply(&mut kernel, step), reply);
        compare(&kernel, &model).unwrap();
        if [18, 20, 23].contains(&n) {
            evidence.push_str(&format!("step={n}\ninput={step:?}\nreply={reply:?}\npre_bindings={:?}\npost_bindings={:?}\npre_events={:?}\npost_conflicts={:?}\n", pre.bindings, model.bindings, pre.events, model.conflicts));
        }
    }
    fs::write(
        evidence_dir().join("e4-row8-generated-identities.txt"),
        evidence,
    )
    .unwrap();
}

#[test]
fn exact_read_only_gate_detects_public_api_clock_only_perturbation() {
    let case = &relation_cases()[0];
    let inputs = relation_trace(case, Family::P1CommandIdentity, 1);
    let (mut kernel, mut model) = initial(case);
    for step in &inputs {
        let expected = model.apply(step);
        assert_eq!(apply(&mut kernel, step), expected);
        if let Some(held) = model
            .orders
            .iter()
            .find(|o| o.phase == OrderState::Held && o.input.expires_at_ms > model.time + 1)
        {
            let held = held.clone();
            let mut altered = held.input.clone();
            altered.order_id = id(u64::MAX);
            let ctx = Context {
                fence: model.writer,
                now_ms: model.time,
                semantics_version: 4,
            };
            let attempt = Step {
                ctx,
                action: Action::Reserve(altered),
            };
            let pre = model.clone();
            let before = kernel.clone();
            let expected = model.apply(&attempt);
            let actual = apply(&mut kernel, &attempt);
            assert_eq!(
                actual,
                Reply::Reserve(Err(kix_kernel::KernelError::CommandConflict))
            );
            assert_eq!(actual, expected);
            evidence_gates::exact_read_only(&pre, &attempt, &actual, &before, &kernel).unwrap();
            // This is an extra public API call on the test instance, not a
            // mutation of the frozen implementation or reference-model file.
            assert_eq!(
                kernel.expire(
                    Context {
                        now_ms: ctx.now_ms + 1,
                        ..ctx
                    },
                    held.input.order_id
                ),
                Ok(false)
            );
            assert!(
                compare(&kernel, &model).is_ok(),
                "old observable comparison ignores clock-only changes"
            );
            assert!(
                evidence_gates::exact_read_only(&pre, &attempt, &actual, &before, &kernel).is_err()
            );
            fs::write(evidence_dir().join("e4-read-only-sensitivity.txt"), "injection=extra public expire call after CommandConflict; frozen sources unchanged\nold_compare=Ok\nwhole_kernel_read_only=Err\nnot a reproduction of the unavailable Devin injection patch\n").unwrap();
            return;
        }
    }
    panic!("generated trace must supply a live Held order");
}

/// Perturb only the observer's input stream; the actual generated kernel/model
/// execution remains unchanged. This tests exclusion of nearby false witnesses.
fn gate_count_with_filter(family: Family, seed: u64, key: &str, filter: &str) -> usize {
    let case = &relation_cases()[0];
    let inputs = relation_trace(case, family, seed);
    let (mut kernel, mut model) = initial(case);
    let mut gates = evidence_gates::Gates::default();
    for (n, step) in inputs.iter().enumerate() {
        let mut pre = model.clone();
        let actual = apply(&mut kernel, step);
        let mut reply = model.apply(step);
        assert_eq!(actual, reply);
        compare(&kernel, &model).unwrap();
        match filter {
            "omit_retry" if matches!(step.action, Action::Send(_)) => continue,
            "omit_duplicate"
                if reply == Reply::Capture(Ok(kix_kernel::ObservationOutcome::DuplicateEffect)) =>
            {
                continue;
            }
            "omit_owner" if matches!(step.action, Action::Owner(_)) => continue,
            "fresh_trace_each_step" => gates = evidence_gates::Gates::default(),
            "capacity_origin"
                if reply == Reply::Capture(Ok(kix_kernel::ObservationOutcome::Conflict)) =>
            {
                reply = Reply::Capture(Err(kix_kernel::KernelError::Capacity))
            }
            "cancelled_capture" if matches!(step.action, Action::Capture(_)) => {
                pre.cancelled = true
            }
            "already_reviewed_mismatch"
                if reply == Reply::Capture(Ok(kix_kernel::ObservationOutcome::Review)) =>
            {
                if let Action::Capture(o) = &step.action
                    && let Some(order) = pre
                        .orders
                        .iter_mut()
                        .find(|order| order.input.payment == o.operation)
                {
                    order.review = true;
                }
            }
            "unreviewed_send" => {
                if let Action::Send(id) = step.action
                    && let Some(o) = pre.orders.iter_mut().find(|o| o.input.order_id == id)
                {
                    o.review = false;
                }
            }
            _ => {}
        }
        gates.observe(n, &pre, step, &reply, &model).unwrap();
    }
    gates.count(key)
}

#[test]
fn history_gates_reject_missing_or_wrong_causal_provenance() {
    for (family, seed, gate, filters) in [
        (
            Family::P3SlotLifecycle,
            12,
            evidence_gates::UNKNOWN_CHAIN,
            vec!["omit_retry", "cancelled_capture"],
        ),
        (
            Family::P6ReturnRequiredReview,
            30,
            evidence_gates::RETURN_CHAIN,
            vec![
                "omit_duplicate",
                "unreviewed_send",
                "already_reviewed_mismatch",
            ],
        ),
        (
            Family::P5QuarantineEvidence,
            15,
            evidence_gates::QUARANTINE_CHAIN,
            vec!["capacity_origin", "omit_owner"],
        ),
    ] {
        assert!(
            gate_count_with_filter(family, seed, gate, "unchanged") > 0,
            "positive generated witness for {gate}"
        );
        assert_eq!(
            gate_count_with_filter(family, seed, gate, "fresh_trace_each_step"),
            0,
            "history cannot be composed across trace boundaries"
        );
        for filter in filters {
            assert_eq!(
                gate_count_with_filter(family, seed, gate, filter),
                0,
                "{gate}: {filter} must not qualify"
            );
        }
    }
}

#[test]
fn altered_payload_matrix_excludes_multiple_fields_and_other_payload_changes() {
    let original = request(1, Selection::Seats { first: 0, count: 1 }, 100);
    let mut changed = original.clone();
    changed.order_id = id(99);
    assert_eq!(
        evidence_gates::single_field(&original, &changed),
        Some("order_id")
    );
    changed.payment.operation = id(98);
    assert_eq!(evidence_gates::single_field(&original, &changed), None);
    changed.payment.operation = original.payment.operation;
    changed.expected_business_epoch += 1;
    assert_eq!(evidence_gates::single_field(&original, &changed), None);
}
