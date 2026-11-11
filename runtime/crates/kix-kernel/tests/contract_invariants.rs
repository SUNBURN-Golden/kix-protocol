#![allow(clippy::disallowed_methods)] // Test evidence I/O only; no production lint change.
//! Contract predicates over ONE locked kernel and its observed public history.
//! Does not import model_v4, its generator, check_context or rejection decision tree.
//! Derivations: docs/contracts/CONTRACT_INVARIANTS.md (INV-1..INV-5).

use std::fs;
use std::path::PathBuf;
use std::process::Command;

use kix_kernel::{
    AppliedReservation, CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel,
    KernelError, Limits, ObservationOutcome, Order, OrderState, ProviderOperation, Rejection,
    Reserve, ReserveOutcome, Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

const LOCKED: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";

fn id(n: u64) -> KixId {
    let mut bytes = [0; 16];
    bytes[..8].copy_from_slice(&n.to_le_bytes());
    KixId::from_bytes(bytes)
}

fn money(n: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([10; 32]),
        n,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([11; 32]),
    )
    .unwrap()
}

fn ctx(time: u64, generation: u64) -> Context {
    Context {
        fence: ExecutionFence {
            owner: id(90),
            generation,
        },
        now_ms: time,
        semantics_version: 4,
    }
}

#[derive(Clone, Copy, Debug)]
struct Fixture {
    ga: bool,
    limits: Limits,
}

impl Fixture {
    fn total(self) -> u32 {
        if self.ga { 6 } else { 70 }
    }
    fn kernel(self) -> Kernel {
        let inventory = if self.ga {
            Inventory::general_admission(6).unwrap()
        } else {
            Inventory::seats(&[65, 5]).unwrap()
        };
        Kernel::new(id(80), ctx(0, 1).fence, 1, inventory, self.limits).unwrap()
    }
    fn selection(self, first: u16, count: u16) -> Selection {
        if self.ga {
            Selection::GeneralAdmission {
                count: u32::from(count),
            }
        } else {
            Selection::Seats { first, count }
        }
    }
    fn request(self, n: u64, first: u16, count: u16, expiry: u64) -> Reserve {
        Reserve {
            id: CommandId {
                scope: id(80),
                principal: id(81),
                request: id(n),
            },
            order_id: id(10_000 + n),
            expected_business_epoch: 1,
            selection: self.selection(first, count),
            amount: money(1_000),
            quote_hash: Hash32::from_bytes([12; 32]),
            policy_hash: Hash32::from_bytes([13; 32]),
            expires_at_ms: expiry,
            payment: ProviderOperation {
                provider: id(82),
                account: id(83),
                operation: id(n),
            },
        }
    }
}

#[derive(Clone, Debug)]
enum Input {
    Reserve(Reserve),
    Send(KixId),
    Expire(KixId),
    Capture(CaptureObservation),
    Owner(ExecutionFence),
    Cancel(u64),
}

#[derive(Debug)]
enum Reply {
    Reserve(Result<AppliedReservation, KernelError>),
    Unit(Result<(), KernelError>),
    Expire(Result<bool, KernelError>),
    Capture(Result<ObservationOutcome, KernelError>),
}

/// Source-informed reply oracle; author knew kernel source. Not clean-room.
/// Contract anchors and class B exact-value/precedence characterizations are
/// distinguished in validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md.
/// Uses public observations and our input/reply history, never the E-4 model.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Expected {
    Unit(Result<(), KernelError>),
    Expire(Result<bool, KernelError>),
    Capture(Result<ObservationOutcome, KernelError>),
}

fn check_reply(expected: &Expected, reply: &Reply) -> Result<(), String> {
    let equal = match (expected, reply) {
        (Expected::Unit(expected), Reply::Unit(actual)) => expected == actual,
        (Expected::Expire(expected), Reply::Expire(actual)) => expected == actual,
        (Expected::Capture(expected), Reply::Capture(actual)) => expected == actual,
        _ => return Err("S4-REPLY kind differs".into()),
    };
    if !equal {
        return Err("S4-REPLY value differs".into());
    }
    Ok(())
}

fn hit(hits: &mut Vec<(&'static str, usize)>, branch: &'static str, count: usize) {
    if let Some((_, total)) = hits.iter_mut().find(|(label, _)| *label == branch) {
        *total += count;
    } else {
        hits.push((branch, count));
    }
}

#[derive(Clone, Default)]
struct Observer {
    known_orders: Vec<KixId>,
    originals: Vec<(Context, Reserve, ReserveOutcome)>,
    captured: Vec<(ProviderOperation, KixId, AssetAmount)>,
    capture_transitions: Vec<(ProviderOperation, usize)>,
    primary_calls: usize,
    replay_probes: usize,
    action_counts: [usize; 6],
    fence: Option<ExecutionFence>,
    epoch: Option<u64>,
    cancelled: bool,
    max_now: u64,
    reserved_ops: Vec<ProviderOperation>,
    retained_events: Vec<(CaptureObservation, ObservationOutcome)>,
    reply_checks: [usize; 6],
    branch_hits: Vec<(&'static str, usize)>,
}

#[derive(Clone, Debug, PartialEq)]
struct View {
    orders: Vec<Order>,
    remaining: u32,
    order_count: usize,
    events: usize,
    conflicts: usize,
    reserved: usize,
    quarantined: usize,
}

/// One observed read-only replay of a recorded first result (INV-3).
#[derive(Clone, Debug)]
struct ReplayProbe {
    recorded: ReserveOutcome,
    reply: Result<AppliedReservation, KernelError>,
    before: View,
    after: View,
    kernel_unchanged: bool,
}

// INV-3 predicate over an OBSERVED probe; never predicts guard order.
fn check_replay(probe: &ReplayProbe) -> Result<(), String> {
    if probe.reply
        != Ok(AppliedReservation {
            original: probe.recorded,
            replayed: true,
        })
    {
        return Err("INV-3 replay reply differs from recorded first result".into());
    }
    if probe.before != probe.after {
        return Err("INV-3 replay changed public state".into());
    }
    if !probe.kernel_unchanged {
        return Err("INV-3 replay mutated kernel or advanced admitted time".into());
    }
    Ok(())
}

impl Observer {
    fn expected_reply(
        &self,
        k: &Kernel,
        f: Fixture,
        context: Context,
        input: &Input,
    ) -> Option<(Expected, &'static str)> {
        if matches!(input, Input::Reserve(_)) {
            return None;
        }
        // max_now is the largest emitted time, a conservative upper bound on
        // admitted time. This corpus needs no prediction of failed-call clock updates.
        assert!(
            context.semantics_version == 4
                && context.fence == self.fence.unwrap_or(ctx(0, 1).fence)
                && context.now_ms >= self.max_now,
            "S4-REPLY undetermined context"
        );
        let full = k.observation_count() + k.conflicts().len() + k.reserved_observation_count()
            >= f.limits.observations;
        Some(match input {
            // README: UNKNOWN retry reuses its promised slot; quarantine blocks
            // sending. Exact InvalidTransition/UnknownOrder and overlapping-guard
            // precedence are class B characterizations, not invented contract rules.
            Input::Send(key) => match k.order(*key) {
                None => (
                    Expected::Unit(Err(KernelError::UnknownOrder)),
                    "send.unknown-order",
                ),
                Some(order)
                    if order.review_required
                        || !matches!(
                            order.state,
                            OrderState::Held | OrderState::PaymentUnknown
                        ) =>
                {
                    (
                        Expected::Unit(Err(KernelError::InvalidTransition)),
                        "send.invalid-state",
                    )
                }
                Some(order) if self.cancelled || context.now_ms >= order.request.expires_at_ms => (
                    Expected::Unit(Err(KernelError::InvalidTransition)),
                    "send.closed",
                ),
                Some(order) if !self.reserved_ops.contains(&order.request.payment) && full => {
                    (Expected::Unit(Err(KernelError::Capacity)), "send.capacity")
                }
                Some(_) => (Expected::Unit(Ok(())), "send.ok"),
            },
            // Lifecycle §5.7: only Held releases, UNKNOWN does not. The bool
            // encoding and UnknownOrder reply are class B characterizations.
            Input::Expire(key) => match k.order(*key) {
                None => (
                    Expected::Expire(Err(KernelError::UnknownOrder)),
                    "expire.unknown-order",
                ),
                Some(order) if context.now_ms < order.request.expires_at_ms => {
                    (Expected::Expire(Ok(false)), "expire.early")
                }
                Some(order) if order.state == OrderState::Held && order.inventory_owned => {
                    (Expected::Expire(Ok(true)), "expire.released")
                }
                Some(_) => (Expected::Expire(Ok(false)), "expire.noop"),
            },
            Input::Capture(value) => {
                // ADR §6 / review addendum A: event identity is provider/account/event;
                // preserve the first payload/result, retain conflicting evidence.
                if let Some((original, outcome)) = self.retained_events.iter().find(|(old, _)| {
                    old.operation.provider == value.operation.provider
                        && old.operation.account == value.operation.account
                        && old.event_id == value.event_id
                }) {
                    if original == value {
                        (Expected::Capture(Ok(*outcome)), "capture.dup-event")
                    } else if k.conflicts().contains(value) {
                        (
                            Expected::Capture(Ok(ObservationOutcome::Conflict)),
                            "capture.conflict",
                        )
                    } else if full {
                        (
                            Expected::Capture(Err(KernelError::Capacity)),
                            "capture.conflict-capacity",
                        )
                    } else {
                        (
                            Expected::Capture(Ok(ObservationOutcome::Conflict)),
                            "capture.conflict",
                        )
                    }
                } else if !self.reserved_ops.contains(&value.operation) && full {
                    // README Observation reservation: a fresh capture spends only
                    // its own promised slot, including after expiry/cancellation.
                    (
                        Expected::Capture(Err(KernelError::Capacity)),
                        "capture.capacity",
                    )
                } else if let Some(order) = self
                    .known_orders
                    .iter()
                    .filter_map(|id| k.order(*id))
                    .find(|order| order.request.payment == value.operation)
                {
                    if let Some(amount) = order.captured {
                        if amount == value.amount {
                            (
                                Expected::Capture(Ok(ObservationOutcome::DuplicateEffect)),
                                "capture.duplicate-effect",
                            )
                        } else {
                            (
                                Expected::Capture(Ok(ObservationOutcome::Review)),
                                "capture.review-mismatch",
                            )
                        }
                    } else if value.amount != order.request.amount {
                        (
                            Expected::Capture(Ok(ObservationOutcome::Review)),
                            "capture.review-mismatch",
                        )
                    } else if self.cancelled
                        || context.now_ms >= order.request.expires_at_ms
                        || order.state == OrderState::Expired
                    {
                        // ADR §6 / Lifecycle §5.7: matching late facts require return;
                        // review is orthogonal (Lifecycle §5.7.1), never auto-cleared.
                        (
                            Expected::Capture(Ok(ObservationOutcome::ReturnRequired)),
                            "capture.return-required",
                        )
                    } else if order.review_required {
                        (
                            Expected::Capture(Ok(ObservationOutcome::Review)),
                            "capture.review-sticky",
                        )
                    } else {
                        (
                            Expected::Capture(Ok(ObservationOutcome::PaymentConfirmed)),
                            "capture.confirmed",
                        )
                    }
                } else {
                    (
                        Expected::Capture(Err(KernelError::UnknownOperation)),
                        "capture.unknown-operation",
                    )
                }
            }
            // ADR §7 supplies local fences, not exact generation/epoch admission
            // replies: these exact comparisons are class B characterizations.
            Input::Owner(next)
                if next.generation > self.fence.unwrap_or(ctx(0, 1).fence).generation =>
            {
                (Expected::Unit(Ok(())), "owner.ok")
            }
            Input::Owner(_) => (
                Expected::Unit(Err(KernelError::InvalidTransition)),
                "owner.invalid",
            ),
            Input::Cancel(epoch) if *epoch > self.epoch.unwrap_or(1) => {
                (Expected::Unit(Ok(())), "cancel.ok")
            }
            Input::Cancel(_) => (
                Expected::Unit(Err(KernelError::InvalidTransition)),
                "cancel.invalid",
            ),
            Input::Reserve(_) => unreachable!(),
        })
    }

    fn remember_reply(
        &mut self,
        context: Context,
        input: &Input,
        reply: &Reply,
        before: &View,
        after: &View,
    ) {
        let mut reserved = before.reserved;
        let mut events = before.events;
        match (input, reply) {
            (Input::Owner(next), Reply::Unit(Ok(()))) => self.fence = Some(*next),
            (Input::Cancel(epoch), Reply::Unit(Ok(()))) => {
                self.epoch = Some(*epoch);
                self.cancelled = true;
            }
            (Input::Send(key), Reply::Unit(Ok(()))) if after.reserved == before.reserved + 1 => {
                let operation = before
                    .orders
                    .iter()
                    .find(|o| o.request.order_id == *key)
                    .expect("S4-REPLY history missing send order")
                    .request
                    .payment;
                assert!(
                    !self.reserved_ops.contains(&operation),
                    "S4-REPLY history duplicate slot"
                );
                self.reserved_ops.push(operation);
                reserved += 1;
            }
            (Input::Capture(value), Reply::Capture(Ok(outcome)))
                if after.events == before.events + 1 =>
            {
                self.retained_events.push((value.clone(), *outcome));
                if self.reserved_ops.contains(&value.operation) {
                    self.reserved_ops.retain(|op| *op != value.operation);
                    reserved -= 1;
                }
                events += 1;
            }
            _ => {}
        }
        assert_eq!(
            (after.reserved, after.events),
            (reserved, events),
            "S4-REPLY history public deltas"
        );
        assert_eq!(
            self.reserved_ops.len(),
            after.reserved,
            "S4-REPLY history slots"
        );
        assert_eq!(
            self.retained_events.len(),
            after.events,
            "S4-REPLY history events"
        );
        self.max_now = self.max_now.max(context.now_ms);
    }

    fn view(&self, k: &Kernel) -> View {
        View {
            orders: self
                .known_orders
                .iter()
                .filter_map(|key| k.order(*key).cloned())
                .collect(),
            remaining: k.remaining(),
            order_count: k.order_count(),
            events: k.observation_count(),
            conflicts: k.conflicts().len(),
            reserved: k.reserved_observation_count(),
            quarantined: k.quarantined_operation_count(),
        }
    }

    fn probe_replay(
        &self,
        k: &mut Kernel,
        entry: &(Context, Reserve, ReserveOutcome),
    ) -> ReplayProbe {
        let before = self.view(k);
        let unchanged = k.clone(); // Read-only sentinel, NOT recovery evidence.
        let reply = k.reserve(entry.0, entry.1.clone());
        ReplayProbe {
            recorded: entry.2,
            reply,
            before,
            after: self.view(k),
            kernel_unchanged: *k == unchanged,
        }
    }

    // These predicates do not predict the next reply or duplicate reserve's guard order.
    fn check(&self, view: &View, f: Fixture) -> Result<(), String> {
        // INV-1: all active owners are read from the SUT, not maintained as a shadow model.
        if view.order_count != view.orders.len() {
            return Err("INV-1 unobserved order".into());
        }
        let mut seats = vec![None; f.total() as usize];
        let mut ga_used = 0_u64;
        for order in &view.orders {
            if !order.inventory_owned {
                continue;
            }
            match order.request.selection {
                Selection::Seats { first, count } if !f.ga => {
                    let end = u32::from(first) + u32::from(count);
                    if count == 0 || count > 64 || end > 70 || (first < 65 && end > 65) {
                        return Err("INV-1 invalid occupied segment".into());
                    }
                    for slot in &mut seats[usize::from(first)..end as usize] {
                        if slot.replace(order.request.order_id).is_some() {
                            return Err("INV-1 two active owners for one seat".into());
                        }
                    }
                }
                Selection::GeneralAdmission { count } if f.ga => {
                    ga_used += u64::from(count);
                }
                _ => return Err("INV-1 inventory type mismatch".into()),
            }
        }
        let used = if f.ga {
            ga_used
        } else {
            seats.iter().filter(|v| v.is_some()).count() as u64
        };
        if used + u64::from(view.remaining) != u64::from(f.total()) {
            return Err("INV-1 inventory conservation".into());
        }
        // INV-2: observation budget is the SUM, not three independent caps.
        let budget = view
            .events
            .checked_add(view.conflicts)
            .and_then(|v| v.checked_add(view.reserved));
        if budget.is_none_or(|v| v > f.limits.observations)
            || view.order_count > f.limits.orders
            || self.originals.len() > f.limits.commands
            || view.quarantined > view.order_count
        {
            return Err("INV-2 bounded records violated".into());
        }
        // INV-4: a full provider/account/operation has at most one economic binding.
        let mut operations = Vec::new();
        for order in &view.orders {
            if operations.contains(&order.request.payment) {
                return Err("INV-4 operation rebound".into());
            }
            operations.push(order.request.payment);
        }
        if self.capture_transitions.iter().any(|(_, n)| *n > 1) {
            return Err("INV-4 capture applied more than once".into());
        }
        // INV-5: previously observed capture facts must persist with full asset context.
        for (operation, order_id, amount) in &self.captured {
            let current = view
                .orders
                .iter()
                .find(|o| o.request.order_id == *order_id)
                .ok_or("INV-5 captured order disappeared")?;
            if current.request.payment != *operation || current.captured != Some(*amount) {
                return Err("INV-5 captured fact changed or disappeared".into());
            }
        }
        Ok(())
    }

    fn run(&mut self, k: &mut Kernel, f: Fixture, context: Context, input: Input) -> Reply {
        if let Input::Reserve(request) = &input
            && !self.known_orders.contains(&request.order_id)
        {
            self.known_orders.push(request.order_id);
        }
        let before = self.view(k);
        let family = match &input {
            Input::Reserve(_) => 0,
            Input::Send(_) => 1,
            Input::Expire(_) => 2,
            Input::Capture(_) => 3,
            Input::Owner(_) => 4,
            Input::Cancel(_) => 5,
        };
        self.action_counts[family] += 1;
        let expected = self.expected_reply(k, f, context, &input);
        let reply = match &input {
            Input::Reserve(value) => Reply::Reserve(k.reserve(context, value.clone())),
            Input::Send(key) => Reply::Unit(k.mark_payment_unknown(context, *key)),
            Input::Expire(key) => Reply::Expire(k.expire(context, *key)),
            Input::Capture(value) => Reply::Capture(k.observe_capture(context, value.clone())),
            Input::Owner(next) => Reply::Unit(k.replace_owner(context, *next)),
            Input::Cancel(epoch) => Reply::Unit(k.cancel_scope(context, *epoch)),
        };
        // Record an OBSERVED first result. No expected rejection is computed here.
        if let (Input::Reserve(request), Reply::Reserve(Ok(applied))) = (&input, &reply) {
            if let Some((_, original, result)) = self
                .originals
                .iter()
                .find(|(_, old, _)| old.id == request.id)
            {
                assert_eq!(request, original, "INV-3 successful replay changed payload");
                assert_eq!(applied.original, *result, "INV-3 changed original result");
                assert!(applied.replayed, "INV-3 repeated command re-applied");
            } else {
                assert!(
                    !applied.replayed,
                    "INV-3 replay without an earlier observed result"
                );
                self.originals
                    .push((context, request.clone(), applied.original));
            }
        }
        if let Some((expected, branch)) = expected {
            check_reply(&expected, &reply).unwrap_or_else(|e| {
                panic!("{e}; branch={branch}; call={}; input={input:?}; expected={expected:?}; reply={reply:?}", self.primary_calls)
            });
            self.reply_checks[family] += 1;
            hit(&mut self.branch_hits, branch, 1);
        } else if let Reply::Reserve(value) = &reply {
            let _ = value.is_ok();
        }
        let after = self.view(k);
        self.remember_reply(context, &input, &reply, &before, &after);
        for order in &after.orders {
            let old = before
                .orders
                .iter()
                .find(|o| o.request.order_id == order.request.order_id);
            if order.captured.is_some() && old.is_none_or(|o| o.captured.is_none()) {
                assert!(
                    matches!(&input, Input::Capture(value) if value.operation == order.request.payment),
                    "INV-4 capture appeared without its observation"
                );
                if let Some((_, n)) = self
                    .capture_transitions
                    .iter_mut()
                    .find(|(op, _)| *op == order.request.payment)
                {
                    *n += 1;
                } else {
                    self.capture_transitions.push((order.request.payment, 1));
                }
            }
        }
        if let Input::Capture(value) = &input {
            for previous in &before.orders {
                if previous.request.payment == value.operation && previous.captured.is_some() {
                    let current = after
                        .orders
                        .iter()
                        .find(|o| o.request.order_id == previous.request.order_id)
                        .expect("INV-4 captured operation disappeared");
                    assert_eq!(
                        current.inventory_owned, previous.inventory_owned,
                        "INV-4 repeated capture changed inventory again"
                    );
                }
            }
        }
        // Check history BEFORE adding new capture observations to that history.
        self.check(&after, f).unwrap_or_else(|e| {
            panic!(
                "{e}; call={}; input={input:?}; reply={reply:?}",
                self.primary_calls
            )
        });
        for order in &after.orders {
            if let Some(value) = order.captured
                && !self
                    .captured
                    .iter()
                    .any(|(op, _, _)| *op == order.request.payment)
            {
                self.captured
                    .push((order.request.payment, order.request.order_id, value));
            }
        }
        // INV-3: a contract probe, not reference-model prediction. This covers original
        // rejections as well as success and uses the ORIGINAL (possibly stale) context.
        for entry in &self.originals {
            let probe = self.probe_replay(k, entry);
            check_replay(&probe).unwrap_or_else(|e| panic!("{e}; call={}", self.primary_calls));
        }
        self.replay_probes += self.originals.len();
        self.check(&self.view(k), f).unwrap();
        self.primary_calls += 1;
        reply
    }
}

fn capture(request: &Reserve, event: u64) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    }
}

struct Generator(u64);
impl Generator {
    fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        self.0 ^ (self.0 >> 33)
    }
}

fn output() -> PathBuf {
    let out = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../.local/verification/ktx");
    fs::create_dir_all(&out).unwrap();
    out
}

#[test]
fn five_contract_invariants_on_kernel_only_generated_histories() {
    let mut primary = 0;
    let mut probes = 0;
    let mut captures = 0;
    let mut totals = [0_usize; 6];
    let mut reply_checks = [0_usize; 6];
    let mut branch_hits = Vec::new();
    for (fixture_id, f) in [
        Fixture {
            ga: false,
            limits: Limits {
                commands: 48,
                orders: 24,
                observations: 24,
            },
        },
        Fixture {
            ga: false,
            limits: Limits {
                commands: 2,
                orders: 8,
                observations: 1,
            },
        },
        Fixture {
            ga: true,
            limits: Limits {
                commands: 48,
                orders: 24,
                observations: 24,
            },
        },
        Fixture {
            ga: true,
            limits: Limits {
                commands: 8,
                orders: 3,
                observations: 2,
            },
        },
    ]
    .into_iter()
    .enumerate()
    {
        for seed in 1..=64_u64 {
            let mut k = f.kernel();
            let mut observer = Observer::default();
            let a = f.request(1, 0, 1, 40);
            let b = f.request(2, 1, 1, 80);
            let first = capture(&a, 500);
            let mut conflicting = first.clone();
            conflicting.operation = b.payment;
            let mut inputs = vec![
                (ctx(1, 1), Input::Reserve(a.clone())),
                (ctx(2, 1), Input::Send(a.order_id)),
                (ctx(3, 1), Input::Capture(first.clone())),
                (ctx(4, 1), Input::Reserve(b.clone())),
                (ctx(5, 1), Input::Capture(first.clone())),
                (ctx(6, 1), Input::Capture(conflicting)),
            ];
            let mut rng = Generator(seed);
            let mut generation = 1;
            // Stimuli depend only on seed and previously emitted inputs, never on Model.
            for index in 0..90_u64 {
                let time = index + 10;
                let n = 1 + rng.next() % 24;
                let mut request = f.request(
                    n,
                    (rng.next() % 72) as u16,
                    (rng.next() % 5) as u16,
                    time + 10,
                );
                if rng.next().is_multiple_of(13) {
                    request.amount = money(0);
                }
                let input = match index % 12 {
                    0..=3 => Input::Reserve(request),
                    4 => Input::Send(id(10_000 + n)),
                    5 => Input::Capture(capture(&request, 501 + n)),
                    6 => Input::Capture(first.clone()),
                    7 => {
                        let mut value = first.clone();
                        value.amount = money(999 + (rng.next() % 3) as u128);
                        value.operation = request.payment;
                        Input::Capture(value)
                    }
                    8 => Input::Expire(id(10_000 + n)),
                    9 => Input::Reserve(a.clone()),
                    10 => Input::Owner(ExecutionFence {
                        owner: id(90),
                        generation: generation + 1,
                    }),
                    _ if index > 72 => Input::Cancel(2 + index),
                    _ => Input::Capture(capture(&a, 900 + index)),
                };
                let mut context = ctx(time, generation);
                if index % 12 == 9 {
                    context = ctx(1, 1);
                }
                if index % 12 == 2 {
                    context.semantics_version = 1;
                }
                if matches!(input, Input::Owner(_)) {
                    generation += 1;
                }
                inputs.push((context, input));
            }
            for (context, input) in inputs {
                observer.run(&mut k, f, context, input);
            }
            assert!(
                !observer.captured.is_empty(),
                "fixture={fixture_id} seed={seed}: vacuous capture checks"
            );
            primary += observer.primary_calls;
            probes += observer.replay_probes;
            captures += observer.captured.len();
            for (sum, count) in reply_checks.iter_mut().zip(observer.reply_checks) {
                *sum += count;
            }
            for (branch, count) in observer.branch_hits {
                hit(&mut branch_hits, branch, count);
            }
            for (sum, count) in totals.iter_mut().zip(observer.action_counts) {
                *sum += count;
            }
        }
    }
    assert_eq!(primary, 4 * 64 * 96);
    assert!(totals.iter().all(|n| *n > 0));
    for family in 1..=5 {
        assert_eq!(
            reply_checks[family], totals[family],
            "S4-REPLY unchecked family={family}"
        );
    }
    assert_eq!(
        branch_hits.iter().map(|(_, n)| n).sum::<usize>(),
        reply_checks.iter().sum()
    );
    branch_hits.sort_by_key(|(branch, _)| *branch);
    let branches = branch_hits
        .iter()
        .map(|(branch, n)| format!("\"{branch}\":{n}"))
        .collect::<Vec<_>>()
        .join(",");
    fs::write(output().join("contract-reply-oracle-summary.json"), format!(
        "{{\"source_informed\":true,\"clean_room\":false,\"reply_checks\":{reply_checks:?},\"branch_hits\":{{{branches}}}}}\n"
    )).unwrap();
    fs::write(output().join("contract-invariants-summary.json"), format!(
        "{{\"kernel_blob\":\"{LOCKED}\",\"reference_model_used\":false,\"sequences\":256,\"primary_steps\":{primary},\"readonly_replay_probes\":{probes},\"capture_facts_observed\":{captures},\"action_counts\":{totals:?},\"properties\":[\"INV-1\",\"INV-2\",\"INV-3\",\"INV-4\",\"INV-5\"],\"failures\":0,\"scope\":\"finite kernel-only public-state/history predicates; not external ledger or proof of completeness\"}}\n"
    )).unwrap();
}

#[test]
fn contract_predicates_reject_corrupted_observations_not_kernel_mutations() {
    let f = Fixture {
        ga: false,
        limits: Limits {
            commands: 8,
            orders: 8,
            observations: 2,
        },
    };
    let mut k = f.kernel();
    let mut observer = Observer::default();
    let a = f.request(1, 0, 1, 100);
    observer.run(&mut k, f, ctx(1, 1), Input::Reserve(a.clone()));
    observer.run(&mut k, f, ctx(2, 1), Input::Capture(capture(&a, 500)));
    let view = observer.view(&k);
    let mut overlap = view.clone();
    let mut second = overlap.orders[0].clone();
    second.request.order_id = id(99_999);
    second.request.payment.operation = id(99_999);
    overlap.orders.push(second);
    overlap.order_count += 1;
    assert!(
        observer
            .check(&overlap, f)
            .unwrap_err()
            .starts_with("INV-1")
    );
    let mut budget = view.clone();
    budget.events = 3;
    assert!(observer.check(&budget, f).unwrap_err().starts_with("INV-2"));
    let mut lost = view.clone();
    lost.orders[0].captured = None;
    assert!(observer.check(&lost, f).unwrap_err().starts_with("INV-5"));
    observer.capture_transitions[0].1 = 2;
    assert!(observer.check(&view, f).unwrap_err().starts_with("INV-4"));
    fs::write(output().join("contract-predicate-sensitivity.txt"),
        "Synthetic observer views rejected: seat overlap, budget overflow, capture disappearance, double capture count. Neither kernel nor reference-model source was mutated. No claim of production fault injection.\n").unwrap();
}

/// Source-informed sensitivity fixture: author knew kernel source; corrupts observer
/// copies only; not independent proof or fault injection.
#[test]
fn inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations() {
    let f = Fixture {
        ga: false,
        limits: Limits {
            commands: 8,
            orders: 8,
            observations: 2,
        },
    };
    let mut k = f.kernel();
    let mut observer = Observer::default();
    let a = f.request(1, 0, 1, 100);
    let b = f.request(2, 0, 1, 100);
    observer.run(&mut k, f, ctx(1, 1), Input::Reserve(a.clone()));
    observer.run(&mut k, f, ctx(2, 1), Input::Reserve(b));
    assert_eq!(observer.originals.len(), 2);
    assert_eq!(observer.originals[0].2, ReserveOutcome::Held(a.order_id));
    assert!(matches!(
        observer.originals[1].2,
        ReserveOutcome::Rejected(_)
    ));
    observer.run(&mut k, f, ctx(3, 1), Input::Send(a.order_id));
    observer.run(&mut k, f, ctx(4, 1), Input::Capture(capture(&a, 500)));
    assert_eq!(k.order(a.order_id).unwrap().captured, Some(a.amount));
    let snapshot = k.clone();

    for (index, entry) in observer.originals.iter().enumerate() {
        let probe = observer.probe_replay(&mut k, entry);
        assert_eq!(check_replay(&probe), Ok(()));
        assert_eq!(observer.check(&observer.view(&k), f), Ok(()));

        // (a) Alter only the observed reply, including its replay flag/error shape.
        for reply in [
            Ok(AppliedReservation {
                original: observer.originals[1 - index].2,
                replayed: true,
            }),
            Ok(AppliedReservation {
                original: entry.2,
                replayed: false,
            }),
            Err(KernelError::CommandConflict),
        ] {
            let mut altered = probe.clone();
            altered.reply = reply;
            assert!(
                check_replay(&altered)
                    .unwrap_err()
                    .starts_with("INV-3 replay reply differs from recorded first result")
            );
        }

        // (b) Corrupt the public-state copy and the read-only sentinel separately.
        let mut changed_state = probe.clone();
        changed_state.after.remaining -= 1;
        assert!(
            check_replay(&changed_state)
                .unwrap_err()
                .starts_with("INV-3 replay changed public state")
        );
        // The whole-kernel Eq sentinel is the only observable for private now_ms;
        // flipping this observer boolean does not inject an actual clock mutation.
        let mut advanced_time = probe.clone();
        advanced_time.kernel_unchanged = false;
        assert!(
            check_replay(&advanced_time)
                .unwrap_err()
                .starts_with("INV-3 replay mutated kernel or advanced admitted time")
        );
    }

    // (c) Rewrite only saved first-result copies after Send and Capture changed state.
    let mut rewritten = observer.originals.clone();
    for entry in &mut rewritten {
        entry.2 = match entry.2 {
            ReserveOutcome::Held(_) => ReserveOutcome::Rejected(Rejection::Unavailable),
            ReserveOutcome::Rejected(_) => ReserveOutcome::Held(a.order_id),
        };
        let probe = observer.probe_replay(&mut k, entry);
        assert!(
            check_replay(&probe)
                .unwrap_err()
                .starts_with("INV-3 replay reply differs from recorded first result")
        );
    }
    assert_eq!(k, snapshot, "fixture mutated the kernel");
    fs::write(output().join("contract-inv3-sensitivity.txt"),
        "Synthetic INV-3 observer copies rejected: altered replay reply, public-state change, Eq-sentinel/admitted-time change, rewritten first result. Kernel unchanged. Source-informed; no production fault injection.\n").unwrap();
}

/// In-memory negative controls; source-informed, no kernel mutation.
#[test]
fn reply_oracle_rejects_deliberately_wrong_expected_replies() {
    let f = Fixture {
        ga: false,
        limits: Limits {
            commands: 8,
            orders: 8,
            observations: 1,
        },
    };
    let mut k = f.kernel();
    let mut observer = Observer::default();
    let a = f.request(1, 0, 1, 100);
    observer.run(&mut k, f, ctx(1, 1), Input::Reserve(a.clone()));
    let send = observer.run(&mut k, f, ctx(2, 1), Input::Send(a.order_id));
    let before_capture = k.clone();
    let capture_history = observer.clone();
    let fact = capture(&a, 500);
    let captured = observer.run(&mut k, f, ctx(3, 1), Input::Capture(fact.clone()));
    let expired = observer.run(&mut k, f, ctx(4, 1), Input::Expire(id(99_999)));
    let next = ctx(0, 2).fence;
    let owner = observer.run(&mut k, f, ctx(5, 1), Input::Owner(next));
    let cancel = observer.run(&mut k, f, ctx(6, 2), Input::Cancel(2));
    let snapshot = k.clone();

    // Positive controls cover each issued non-reserve family and all reply kinds.
    for (expected, reply) in [
        (Expected::Unit(Ok(())), &send),
        (
            Expected::Capture(Ok(ObservationOutcome::PaymentConfirmed)),
            &captured,
        ),
        (Expected::Expire(Err(KernelError::UnknownOrder)), &expired),
        (Expected::Unit(Ok(())), &owner),
        (Expected::Unit(Ok(())), &cancel),
    ] {
        assert_eq!(check_reply(&expected, reply), Ok(()));
    }
    // Wrong Ok payload, Ok-vs-Err, wrong error, and wrong kind. Every reply
    // kind has a value mismatch and a kind mismatch; no SUT mutation is needed.
    for (wrong, reply) in [
        (Expected::Unit(Err(KernelError::Capacity)), &send),
        (
            Expected::Capture(Ok(ObservationOutcome::DuplicateEffect)),
            &captured,
        ),
        (Expected::Capture(Err(KernelError::Capacity)), &captured),
        (Expected::Expire(Ok(false)), &expired),
        (Expected::Expire(Err(KernelError::Capacity)), &expired),
        (Expected::Expire(Ok(true)), &send),
        (Expected::Unit(Ok(())), &expired),
        (Expected::Unit(Ok(())), &captured),
    ] {
        assert!(
            check_reply(&wrong, reply)
                .unwrap_err()
                .starts_with("S4-REPLY")
        );
    }
    assert!(
        check_reply(&Expected::Expire(Ok(true)), &Reply::Expire(Ok(false)))
            .unwrap_err()
            .starts_with("S4-REPLY value")
    );

    // Clear only copies of tracked history. Without the promised slot the
    // same pre-call public full budget predicts Capacity instead of confirmation.
    let mut lost_slot = capture_history.clone();
    lost_slot.reserved_ops.clear();
    let input = Input::Capture(fact.clone());
    let (correct, _) = capture_history
        .expected_reply(&before_capture, f, ctx(3, 1), &input)
        .unwrap();
    let (wrong, _) = lost_slot
        .expected_reply(&before_capture, f, ctx(3, 1), &input)
        .unwrap();
    assert_eq!(check_reply(&correct, &captured), Ok(()));
    assert!(
        check_reply(&wrong, &captured)
            .unwrap_err()
            .starts_with("S4-REPLY")
    );

    // Without retained event history an exact replay looks like a fresh event
    // at capacity. The real observer still expects the original confirmed reply.
    let mut lost_event = observer.clone();
    lost_event.retained_events.clear();
    let (correct, _) = observer.expected_reply(&k, f, ctx(7, 2), &input).unwrap();
    let (wrong, _) = lost_event.expected_reply(&k, f, ctx(7, 2), &input).unwrap();
    assert_eq!(check_reply(&correct, &captured), Ok(()));
    assert!(
        check_reply(&wrong, &captured)
            .unwrap_err()
            .starts_with("S4-REPLY")
    );
    assert_eq!(k, snapshot, "negative controls mutated the kernel");
    fs::write(output().join("contract-reply-oracle-sensitivity.txt"),
        "Wrong expected values/kinds and lost slot/event history rejected; observer copies only; no kernel mutation; source-informed, not clean-room.\n").unwrap();
}

#[test]
fn contract_test_source_identity_and_format_diagnostic() {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/contract_invariants.rs");
    let hash = Command::new("git")
        .arg("hash-object")
        .arg(&path)
        .output()
        .unwrap();
    assert!(hash.status.success());
    fs::write(
        output().join("contract-invariants-source-blob.txt"),
        hash.stdout,
    )
    .unwrap();
    let formatted = Command::new("rustfmt")
        .args([
            "--edition",
            "2024",
            "--emit",
            "stdout",
            "--config",
            "skip_children=true",
        ])
        .arg(&path)
        .output()
        .unwrap();
    assert!(formatted.status.success());
    fs::write(
        output().join("formatted-tests__contract_invariants.rs"),
        formatted.stdout,
    )
    .unwrap();
}
