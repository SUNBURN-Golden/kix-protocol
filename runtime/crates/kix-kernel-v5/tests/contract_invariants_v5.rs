//! Contract predicates INV-1..INV-5 over ONE v5 kernel and its observed public history.
//!
//! Derivations: docs/contracts/CONTRACT_INVARIANTS.md §3 (INV-1..INV-5) and
//! docs/contracts/STATE_LIFECYCLE.md §3 LC-FACT, §5.6 and §5.7.1.
//! No reference model, reply oracle or state machine is used: no reply is
//! predicted. Stimuli depend on the seed, earlier emitted inputs and public
//! getters only. Does not import lifecycle_model.rs, v4_differential.rs or the
//! v4 kix_kernel crate.
//!
//! Source-informed: the author knew the v5 source. Not clean-room.
//! CONTRACT_INVARIANTS is scoped to the locked v4 kernel, so running its
//! predicates over v5 is a class B characterization (AGENTS §8), recorded in
//! validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md.
//! "Send" means `mark_payment_unknown`, as in the v4 contract_invariants.rs.

mod common;

use common::{amount, closure, human};
use kix_kernel_v5::{
    ActorKind, AppliedHold, AppliedReservation, AppliedTermination, CaptureObservation,
    ClearedHold, CommandId, Context, ExecutionFence, HoldKind, HoldRef, Inventory, Kernel,
    KernelError, Limits, ObservationOutcome, OperationSnapshot, Order, OrderState,
    ProviderOperation, ReclaimBatch, ReclaimPolicy, ReclaimReport, Rejection, Reserve,
    ReserveOutcome, SEMANTICS_VERSION, Selection, Terminate, Termination,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

const FAMILIES: [&str; 11] = [
    "reserve",
    "send",
    "expire",
    "capture",
    "replace_owner",
    "cancel_scope",
    "terminate",
    "place_hold",
    "clear_hold",
    "reclaim_report",
    "reclaim_reports",
];
const SEEDS: u64 = 32;
const PREFIX_STEPS: usize = 14;
const SEEDED_STEPS: u64 = 114;

/// Placeholder snapshot for a terminate aimed at an order the kernel does not know.
const UNKNOWN_SNAPSHOT: OperationSnapshot = OperationSnapshot {
    state: OrderState::Held,
    captured: None,
    review_required: false,
    reserved_slot: false,
    observations: 0,
    retained_conflicts: 0,
};

fn kid(n: u64) -> KixId {
    let mut bytes = [0; 16];
    bytes[..8].copy_from_slice(&n.to_le_bytes());
    KixId::from_bytes(bytes)
}

fn fence(generation: u64) -> ExecutionFence {
    ExecutionFence {
        owner: kid(90),
        generation,
    }
}

fn ctx(time: u64, generation: u64) -> Context {
    Context {
        fence: fence(generation),
        now_ms: time,
        semantics_version: SEMANTICS_VERSION,
    }
}

#[derive(Clone, Copy, Debug)]
struct Fixture {
    ga: bool,
    limits: Limits,
}

// Tight budgets still leave room for the prefix to terminate an order.
const FIXTURES: [Fixture; 4] = [
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
            commands: 8,
            orders: 4,
            observations: 3,
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
            observations: 3,
        },
    },
];

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
        Kernel::new(kid(80), fence(1), 1, inventory, self.limits).unwrap()
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
                scope: kid(80),
                principal: kid(81),
                request: kid(n),
            },
            order_id: kid(100 + n),
            expected_business_epoch: 1,
            selection: self.selection(first, count),
            amount: amount(1_000),
            quote_hash: Hash32::from_bytes([12; 32]),
            policy_hash: Hash32::from_bytes([13; 32]),
            expires_at_ms: expiry,
            payment: ProviderOperation {
                provider: kid(82),
                account: kid(83),
                operation: kid(n),
            },
        }
    }
}

fn capture(request: &Reserve, event: u64) -> CaptureObservation {
    CaptureObservation {
        event_id: kid(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([60; 32]),
    }
}

/// A human decision with all five caller-supplied flags true, evaluated on the
/// current public snapshot. The kernel decides nothing about provider facts.
fn decision(k: &Kernel, decision: u64, order: KixId) -> Terminate {
    Terminate {
        decision_id: kid(decision),
        order_id: order,
        evaluated: k.operation_snapshot(order).unwrap_or(UNKNOWN_SNAPSHOT),
        evaluation: closure([true; 5]),
        authority: human(40),
        rule_hash: Hash32::from_bytes([6; 32]),
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
    Terminate(Terminate),
    PlaceHold {
        order: KixId,
        hold: KixId,
        kind: HoldKind,
        by: KixId,
    },
    ClearHold {
        hold: KixId,
        by: KixId,
    },
    Report {
        now: u64,
        order: KixId,
    },
    Reports {
        now: u64,
    },
}

impl Input {
    fn family(&self) -> usize {
        match self {
            Input::Reserve(_) => 0,
            Input::Send(_) => 1,
            Input::Expire(_) => 2,
            Input::Capture(_) => 3,
            Input::Owner(_) => 4,
            Input::Cancel(_) => 5,
            Input::Terminate(_) => 6,
            Input::PlaceHold { .. } => 7,
            Input::ClearHold { .. } => 8,
            Input::Report { .. } => 9,
            Input::Reports { .. } => 10,
        }
    }
}

#[derive(Debug)]
enum Reply {
    Reserve(Result<AppliedReservation, KernelError>),
    Unit(Result<(), KernelError>),
    Expire(Result<bool, KernelError>),
    Capture(Result<ObservationOutcome, KernelError>),
    // Boxed: the termination record is large next to the other replies.
    Terminate(Box<Result<AppliedTermination, KernelError>>),
    Hold(Result<AppliedHold, KernelError>),
    Clear(Result<ClearedHold, KernelError>),
    Report(Result<ReclaimReport, KernelError>),
    Reports(Result<ReclaimBatch, KernelError>),
}

impl Reply {
    fn is_ok(&self) -> bool {
        match self {
            Reply::Reserve(r) => r.is_ok(),
            Reply::Unit(r) => r.is_ok(),
            Reply::Expire(r) => r.is_ok(),
            Reply::Capture(r) => r.is_ok(),
            Reply::Terminate(r) => r.is_ok(),
            Reply::Hold(r) => r.is_ok(),
            Reply::Clear(r) => r.is_ok(),
            Reply::Report(r) => r.is_ok(),
            Reply::Reports(r) => r.is_ok(),
        }
    }
}

/// Built only from public getters over every attempted order id.
#[derive(Clone, Debug, PartialEq)]
struct View {
    orders: Vec<Order>,
    remaining: u32,
    order_count: usize,
    events: usize,
    conflicts: usize,
    reserved: usize,
    quarantined: usize,
    terminations: Vec<(KixId, Termination)>,
    holds: Vec<(KixId, HoldRef)>,
    terminated_records: usize,
}

/// One observed read-only replay of a recorded first result (INV-3).
#[derive(Clone, Debug)]
struct ReplayProbe<R> {
    expected: R,
    reply: Result<R, KernelError>,
    before: View,
    after: View,
    kernel_unchanged: bool,
}

// INV-3 predicate over an OBSERVED probe; never predicts guard order.
fn check_replay<R: PartialEq>(probe: &ReplayProbe<R>) -> Result<(), String> {
    if probe.reply.as_ref() != Ok(&probe.expected) {
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

#[derive(Clone, Debug)]
struct Observer {
    known_orders: Vec<KixId>,
    reserve_originals: Vec<(Context, Reserve, ReserveOutcome)>,
    term_originals: Vec<(Context, Terminate, Termination)>,
    /// (context, order, first placement, placed_by); removed on a successful clear.
    hold_originals: Vec<(Context, KixId, HoldRef, KixId)>,
    captured: Vec<(ProviderOperation, KixId, AssetAmount)>,
    capture_transitions: Vec<(ProviderOperation, usize)>,
    fence: ExecutionFence,
    max_now: u64,
    action_counts: [usize; 11],
    ok_counts: [usize; 11],
    /// Main-step replays observed for reserve, terminate and place_hold.
    main_replays: [usize; 3],
    holds_cleared: usize,
    primary_calls: usize,
    replay_probes: usize,
}

impl Observer {
    fn new() -> Self {
        Self {
            known_orders: Vec::new(),
            reserve_originals: Vec::new(),
            term_originals: Vec::new(),
            hold_originals: Vec::new(),
            captured: Vec::new(),
            capture_transitions: Vec::new(),
            fence: fence(1),
            max_now: 0,
            action_counts: [0; 11],
            ok_counts: [0; 11],
            main_replays: [0; 3],
            holds_cleared: 0,
            primary_calls: 0,
            replay_probes: 0,
        }
    }

    fn view(&self, k: &Kernel) -> View {
        // max_now is the largest emitted context time, never behind admitted time.
        let batch = k
            .reclaim_reports(self.max_now, &ReclaimPolicy::default())
            .expect("view: the largest emitted time admits the batch report");
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
            terminations: self
                .known_orders
                .iter()
                .filter_map(|key| k.termination(*key).map(|t| (*key, *t)))
                .collect(),
            holds: self
                .known_orders
                .iter()
                .filter_map(|key| k.hold(*key).map(|h| (*key, *h)))
                .collect(),
            terminated_records: batch.terminated_records,
        }
    }

    fn probe<R>(
        &self,
        k: &mut Kernel,
        expected: R,
        call: impl FnOnce(&mut Kernel) -> Result<R, KernelError>,
    ) -> ReplayProbe<R> {
        let before = self.view(k);
        let unchanged = k.clone(); // Read-only sentinel, NOT recovery evidence.
        let reply = call(k);
        ReplayProbe {
            expected,
            reply,
            before,
            after: self.view(k),
            kernel_unchanged: *k == unchanged,
        }
    }

    fn probe_reserve(
        &self,
        k: &mut Kernel,
        entry: &(Context, Reserve, ReserveOutcome),
    ) -> ReplayProbe<AppliedReservation> {
        let expected = AppliedReservation {
            original: entry.2,
            replayed: true,
        };
        self.probe(k, expected, |k| k.reserve(entry.0, entry.1.clone()))
    }

    fn probe_terminate(
        &self,
        k: &mut Kernel,
        entry: &(Context, Terminate, Termination),
    ) -> ReplayProbe<AppliedTermination> {
        let expected = AppliedTermination {
            original: entry.2,
            replayed: true,
        };
        self.probe(k, expected, |k| k.terminate(entry.0, entry.1))
    }

    // Class B: a hold placement replays only while that hold is placed.
    fn probe_hold(
        &self,
        k: &mut Kernel,
        entry: &(Context, KixId, HoldRef, KixId),
    ) -> ReplayProbe<AppliedHold> {
        let (context, order, hold, by) = *entry;
        let expected = AppliedHold {
            original: hold,
            replayed: true,
        };
        self.probe(k, expected, |k| {
            k.place_hold(context, order, hold.id, hold.kind, by)
        })
    }

    // These predicates do not predict the next reply or any guard order.
    fn check(&self, view: &View, f: Fixture) -> Result<(), String> {
        // INV-1: all active owners are read from the SUT, not a shadow model.
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
            || self.reserve_originals.len() > f.limits.commands
            || view.quarantined > view.order_count
        {
            return Err("INV-2 bounded records violated".into());
        }
        // Class B v5 extension: termination and hold records stay per-order bounded.
        if view.terminated_records != view.terminations.len()
            || view.terminations.len() > view.order_count
            || view.holds.len() > view.order_count
        {
            return Err("INV-2 v5 termination or hold records exceed orders".into());
        }
        // INV-3: a recorded termination never changes; a placed hold keeps its
        // first placement until an explicit clear (class B for holds).
        for (_, request, original) in &self.term_originals {
            if !view.terminations.contains(&(request.order_id, *original)) {
                return Err("INV-3 recorded termination changed or disappeared".into());
            }
        }
        for (_, order, hold, _) in &self.hold_originals {
            if !view.holds.contains(&(*order, *hold)) {
                return Err("INV-3 placed hold changed or disappeared".into());
            }
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
        // INV-5 (LC-FACT, LC-TERM §5.6): a retained capture persists with full
        // asset context through terminate, hold and report steps alike.
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

    /// Records OBSERVED first results. No expected reply is computed here.
    fn remember(&mut self, context: Context, input: &Input, reply: &Reply, call: usize) {
        match (input, reply) {
            (Input::Reserve(request), Reply::Reserve(Ok(applied))) => {
                if let Some((_, original, result)) = self
                    .reserve_originals
                    .iter()
                    .find(|(_, old, _)| old.id == request.id)
                {
                    assert_eq!(
                        request, original,
                        "INV-3 successful replay changed payload; call={call}"
                    );
                    assert_eq!(
                        *applied,
                        AppliedReservation {
                            original: *result,
                            replayed: true
                        },
                        "INV-3 reserve replay differs from first result; call={call}"
                    );
                    self.main_replays[0] += 1;
                } else {
                    assert!(
                        !applied.replayed,
                        "INV-3 reserve replay without an earlier observed result; call={call}"
                    );
                    self.reserve_originals
                        .push((context, request.clone(), applied.original));
                }
            }
            (Input::Terminate(request), Reply::Terminate(result)) if result.is_ok() => {
                let applied = result.as_ref().as_ref().unwrap();
                if let Some((_, _, original)) = self
                    .term_originals
                    .iter()
                    .find(|(_, old, _)| old.decision_id == request.decision_id)
                {
                    assert_eq!(
                        *applied,
                        AppliedTermination {
                            original: *original,
                            replayed: true
                        },
                        "INV-3 terminate replay differs from first result; call={call}"
                    );
                    self.main_replays[1] += 1;
                } else {
                    assert!(
                        !applied.replayed,
                        "INV-3 terminate replay without an earlier observed result; call={call}"
                    );
                    self.term_originals
                        .push((context, *request, applied.original));
                }
            }
            (
                Input::PlaceHold {
                    order, hold, by, ..
                },
                Reply::Hold(Ok(applied)),
            ) => {
                if let Some((_, _, original, _)) = self
                    .hold_originals
                    .iter()
                    .find(|(_, _, old, _)| old.id == *hold)
                {
                    assert_eq!(
                        *applied,
                        AppliedHold {
                            original: *original,
                            replayed: true
                        },
                        "INV-3 hold replay differs from first placement; call={call}"
                    );
                    self.main_replays[2] += 1;
                } else {
                    assert!(
                        !applied.replayed,
                        "INV-3 hold replay without an observed placement; call={call}"
                    );
                    self.hold_originals
                        .push((context, *order, applied.original, *by));
                }
            }
            (Input::ClearHold { hold, .. }, Reply::Clear(Ok(cleared))) => {
                // Class B: a clear reports the placement it removed.
                let index = self
                    .hold_originals
                    .iter()
                    .position(|(_, _, old, _)| old.id == *hold)
                    .unwrap_or_else(|| panic!("cleared an unobserved hold; call={call}"));
                let (_, order, original, _) = self.hold_originals.remove(index);
                assert_eq!(
                    (cleared.hold, cleared.order_id),
                    (original, order),
                    "clear reported another placement; call={call}"
                );
                self.holds_cleared += 1;
            }
            (Input::Owner(next), Reply::Unit(Ok(()))) => self.fence = *next,
            _ => {}
        }
    }

    fn run(&mut self, k: &mut Kernel, f: Fixture, context: Context, input: Input) -> Reply {
        if let Input::Reserve(request) = &input
            && !self.known_orders.contains(&request.order_id)
        {
            self.known_orders.push(request.order_id);
        }
        let call = self.primary_calls;
        let before = self.view(k);
        let pre = k.clone(); // Read-only sentinel for report steps and terminate errors.
        let family = input.family();
        self.action_counts[family] += 1;
        let policy = ReclaimPolicy::default();
        let reply = match &input {
            Input::Reserve(value) => Reply::Reserve(k.reserve(context, value.clone())),
            Input::Send(key) => Reply::Unit(k.mark_payment_unknown(context, *key)),
            Input::Expire(key) => Reply::Expire(k.expire(context, *key)),
            Input::Capture(value) => Reply::Capture(k.observe_capture(context, value.clone())),
            Input::Owner(next) => Reply::Unit(k.replace_owner(context, *next)),
            Input::Cancel(epoch) => Reply::Unit(k.cancel_scope(context, *epoch)),
            Input::Terminate(request) => Reply::Terminate(Box::new(k.terminate(context, *request))),
            Input::PlaceHold {
                order,
                hold,
                kind,
                by,
            } => Reply::Hold(k.place_hold(context, *order, *hold, *kind, *by)),
            Input::ClearHold { hold, by } => Reply::Clear(k.clear_hold(context, *hold, *by)),
            Input::Report { now, order } => Reply::Report(k.reclaim_report(*now, *order, &policy)),
            Input::Reports { now } => Reply::Reports(k.reclaim_reports(*now, &policy)),
        };
        if !matches!(input, Input::Report { .. } | Input::Reports { .. }) {
            self.max_now = self.max_now.max(context.now_ms);
        }
        if reply.is_ok() {
            self.ok_counts[family] += 1;
        }
        self.remember(context, &input, &reply, call);
        match (&input, &reply) {
            (Input::Report { .. } | Input::Reports { .. }, _) => {
                assert!(*k == pre, "report step mutated the kernel; call={call}");
            }
            // Class B: terminate errors change no state, so there is no first result.
            (Input::Terminate(_), Reply::Terminate(result)) if result.is_err() => {
                assert!(*k == pre, "terminate error changed state; call={call}");
            }
            _ => {}
        }
        let after = self.view(k);
        for order in &after.orders {
            let old = before
                .orders
                .iter()
                .find(|o| o.request.order_id == order.request.order_id);
            if order.captured.is_some() && old.is_none_or(|o| o.captured.is_none()) {
                // Terminate, hold and report steps never create a capture.
                assert!(
                    matches!(&input, Input::Capture(value) if value.operation == order.request.payment),
                    "INV-4 capture appeared without its observation; call={call}"
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
                        "INV-4 repeated capture changed inventory again; call={call}"
                    );
                }
            }
        }
        // Check history BEFORE adding new capture observations to that history.
        self.check(&after, f)
            .unwrap_or_else(|e| panic!("{e}; call={call}; input={input:?}; reply={reply:?}"));
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
        // INV-3: contract probes with the ORIGINAL (possibly stale) context.
        for entry in &self.reserve_originals {
            check_replay(&self.probe_reserve(k, entry))
                .unwrap_or_else(|e| panic!("{e}; reserve; call={call}"));
        }
        for entry in &self.term_originals {
            check_replay(&self.probe_terminate(k, entry))
                .unwrap_or_else(|e| panic!("{e}; terminate; call={call}"));
        }
        for entry in &self.hold_originals {
            check_replay(&self.probe_hold(k, entry))
                .unwrap_or_else(|e| panic!("{e}; place_hold; call={call}"));
        }
        self.replay_probes +=
            self.reserve_originals.len() + self.term_originals.len() + self.hold_originals.len();
        self.check(&self.view(k), f)
            .unwrap_or_else(|e| panic!("{e}; after probes; call={call}"));
        self.primary_calls += 1;
        reply
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

/// Kernel and observer after the prefix, with prefix requests a and c.
struct Prefix {
    kernel: Kernel,
    observer: Observer,
    a: Reserve,
    c: Reserve,
}

/// Ten fixed actions, then hold place/clear/place and one batch report.
/// c is sent, terminated, then captured after its expiry (LC-TERM §5.6).
fn prefix(f: Fixture) -> Prefix {
    let mut k = f.kernel();
    let mut o = Observer::new();
    let a = f.request(1, 0, 1, 40);
    let b = f.request(2, 1, 1, 80);
    let c = f.request(3, 2, 1, 9);
    let first = capture(&a, 500);
    let mut conflicting = first.clone();
    conflicting.operation = b.payment;
    o.run(&mut k, f, ctx(1, 1), Input::Reserve(a.clone()));
    o.run(&mut k, f, ctx(2, 1), Input::Send(a.order_id));
    o.run(&mut k, f, ctx(3, 1), Input::Capture(first.clone()));
    o.run(&mut k, f, ctx(4, 1), Input::Reserve(b));
    o.run(&mut k, f, ctx(5, 1), Input::Capture(first));
    o.run(&mut k, f, ctx(6, 1), Input::Capture(conflicting));
    o.run(&mut k, f, ctx(7, 1), Input::Reserve(c.clone()));
    o.run(&mut k, f, ctx(8, 1), Input::Send(c.order_id));
    let terminate = decision(&k, 300, c.order_id);
    o.run(&mut k, f, ctx(9, 1), Input::Terminate(terminate));
    o.run(&mut k, f, ctx(10, 1), Input::Capture(capture(&c, 501)));
    o.run(
        &mut k,
        f,
        ctx(11, 1),
        Input::PlaceHold {
            order: a.order_id,
            hold: kid(200),
            kind: HoldKind::Legal,
            by: kid(210),
        },
    );
    o.run(
        &mut k,
        f,
        ctx(12, 1),
        Input::ClearHold {
            hold: kid(200),
            by: kid(212),
        },
    );
    o.run(
        &mut k,
        f,
        ctx(13, 1),
        Input::PlaceHold {
            order: c.order_id,
            hold: kid(201),
            kind: HoldKind::Dispute,
            by: kid(210),
        },
    );
    o.run(&mut k, f, ctx(13, 1), Input::Reports { now: 13 });
    assert_eq!(o.primary_calls, PREFIX_STEPS);
    // Vacuity guards on OBSERVED state, not predictions.
    assert!(!o.captured.is_empty(), "vacuous INV-5: no capture observed");
    assert!(
        !o.term_originals.is_empty(),
        "vacuous INV-3: no termination"
    );
    assert!(
        o.term_originals
            .iter()
            .any(|(_, t, _)| o.captured.iter().any(|(_, order, _)| *order == t.order_id)),
        "vacuous INV-5: no captured order is terminated"
    );
    assert!(
        o.holds_cleared > 0 && !o.hold_originals.is_empty(),
        "vacuous hold coverage"
    );
    Prefix {
        kernel: k,
        observer: o,
        a,
        c,
    }
}

/// Terminate stimuli: current snapshot (weight 3), stale snapshot, one false
/// condition, automatic actor, exact replay, altered replay or an unknown order.
fn terminate_stimulus(
    k: &Kernel,
    o: &Observer,
    rng: &mut Generator,
    stale: &mut Option<(KixId, OperationSnapshot)>,
    target: KixId,
) -> Terminate {
    let mut request = decision(k, 301 + rng.next() % 12, target);
    match rng.next() % 9 {
        0..=2 => {}
        3 => {
            if let Some((order, snapshot)) = *stale {
                request.order_id = order;
                request.evaluated = snapshot;
            }
        }
        4 => request.evaluation.c[(rng.next() % 5) as usize].holds = false,
        5 => request.authority.actor = ActorKind::Automatic,
        variant @ (6 | 7) if !o.term_originals.is_empty() => {
            let pick = (rng.next() % o.term_originals.len() as u64) as usize;
            request = o.term_originals[pick].1;
            if variant == 7 {
                request.rule_hash = Hash32::from_bytes([7; 32]);
            }
        }
        8 => {
            request.order_id = kid(999);
            request.evaluated = UNKNOWN_SNAPSHOT;
        }
        _ => {}
    }
    if let Some(snapshot) = k.operation_snapshot(target) {
        *stale = Some((target, snapshot));
    }
    request
}

const KINDS: [HoldKind; 3] = [HoldKind::Legal, HoldKind::Dispute, HoldKind::Erasure];

/// Seeded phase. Stimuli depend on seed, emitted inputs and public getters only.
fn seeded(p: &mut Prefix, f: Fixture, seed: u64) {
    let (k, o) = (&mut p.kernel, &mut p.observer);
    let first = capture(&p.a, 500);
    let c = p.c.order_id;
    let mut rng = Generator(seed);
    let mut last_sent = p.a.order_id;
    let mut stale = None;
    for index in 0..SEEDED_STEPS {
        let time = index + 20;
        let generation = o.fence.generation;
        let n = 1 + rng.next() % 24;
        let mut request = f.request(
            n,
            (rng.next() % 72) as u16,
            (rng.next() % 5) as u16,
            time + 10,
        );
        if rng.next().is_multiple_of(13) {
            request.amount = amount(0);
        }
        let order = kid(100 + n);
        let mut context = ctx(time, generation);
        let input = match index % 16 {
            0 | 1 if rng.next().is_multiple_of(7) => {
                // Another command binds the same payment to another order id.
                let other = 1 + (n + rng.next() % 23) % 24; // never n
                request.id.request = kid(50 + n);
                request.order_id = kid(100 + other);
                Input::Reserve(request)
            }
            0..=2 => Input::Reserve(request),
            3 => {
                // Input selection only: half the sends aim at the latest Held order.
                let held = o.known_orders.iter().rev().copied().find(|key| {
                    k.order(*key)
                        .is_some_and(|value| value.state == OrderState::Held)
                });
                last_sent = if rng.next().is_multiple_of(2) {
                    held.unwrap_or(order)
                } else {
                    order
                };
                Input::Send(last_sent)
            }
            4 => Input::Capture(capture(&request, 501 + n)),
            5 => Input::Capture(first.clone()),
            6 => {
                let mut value = first.clone();
                value.amount = amount(999 + u128::from(rng.next() % 3));
                value.operation = request.payment;
                Input::Capture(value)
            }
            7 => Input::Expire(order),
            8 => {
                context = ctx(1, 1);
                Input::Reserve(p.a.clone())
            }
            9 => Input::Owner(fence(generation + 1)),
            10 => {
                // Input selection only, no reply prediction: prefer an order whose
                // public snapshot is on the absence path, else the last sent one.
                let open = o.known_orders.iter().copied().find(|key| {
                    k.operation_snapshot(*key).is_some_and(|s| {
                        s.state == OrderState::PaymentUnknown
                            && s.reserved_slot
                            && !s.review_required
                            && s.captured.is_none()
                    }) && k.termination(*key).is_none()
                });
                let target = if rng.next().is_multiple_of(2) {
                    open.unwrap_or(last_sent)
                } else {
                    order
                };
                Input::Terminate(terminate_stimulus(k, o, &mut rng, &mut stale, target))
            }
            11 => Input::PlaceHold {
                order: if rng.next().is_multiple_of(3) {
                    c
                } else {
                    order
                },
                hold: kid(200 + rng.next() % 6),
                kind: KINDS[(rng.next() % 3) as usize],
                by: kid(210 + rng.next() % 2),
            },
            12 => Input::ClearHold {
                hold: kid(200 + rng.next() % 6),
                by: kid(212),
            },
            13 => Input::Report {
                now: if rng.next().is_multiple_of(8) {
                    0
                } else {
                    o.max_now + rng.next() % 3
                },
                order: if rng.next().is_multiple_of(2) {
                    order
                } else {
                    c
                },
            },
            14 => Input::Reports {
                now: o.max_now + rng.next() % 3,
            },
            _ if index > 85 => Input::Cancel(2 + index),
            _ => Input::Capture(capture(&p.a, 900 + index)),
        };
        if index % 16 == 2 {
            context.semantics_version = 4;
        }
        o.run(k, f, context, input);
    }
}

#[test]
fn five_contract_invariants_on_v5_kernel_only_generated_histories() {
    let mut primary = 0;
    let mut probes = 0;
    let mut totals = [0_usize; 11];
    let mut oks = [0_usize; 11];
    let mut replays = [0_usize; 3];
    let mut terminations = 0;
    let mut captured = 0;
    let mut captured_terminated = 0;
    let mut cleared = 0;
    for (fixture_id, f) in FIXTURES.into_iter().enumerate() {
        let mut fixture_primary = 0;
        let mut fixture_terminations = 0;
        for seed in 1..=SEEDS {
            let mut p = prefix(f);
            seeded(&mut p, f, seed);
            let o = p.observer;
            fixture_primary += o.primary_calls;
            primary += o.primary_calls;
            probes += o.replay_probes;
            captured += o.captured.len();
            fixture_terminations += o.term_originals.len();
            captured_terminated += o
                .term_originals
                .iter()
                .filter(|(_, t, _)| o.captured.iter().any(|(_, order, _)| *order == t.order_id))
                .count();
            cleared += o.holds_cleared;
            for (sum, n) in totals.iter_mut().zip(o.action_counts) {
                *sum += n;
            }
            for (sum, n) in oks.iter_mut().zip(o.ok_counts) {
                *sum += n;
            }
            for (sum, n) in replays.iter_mut().zip(o.main_replays) {
                *sum += n;
            }
        }
        terminations += fixture_terminations;
        eprintln!(
            "fixture={fixture_id} {f:?} seeds={SEEDS} steps={fixture_primary} applied_terminations={fixture_terminations}"
        );
    }
    for (index, name) in FAMILIES.iter().enumerate() {
        eprintln!("family {name}: calls={} ok={}", totals[index], oks[index]);
    }
    eprintln!(
        "primary_steps={primary} readonly_replay_probes={probes} captured_facts={captured} applied_terminations={terminations} captured_and_terminated={captured_terminated} holds_cleared={cleared} main_replays(reserve,terminate,hold)={replays:?}"
    );
    let histories = FIXTURES.len() * SEEDS as usize;
    assert_eq!(primary, histories * (PREFIX_STEPS + SEEDED_STEPS as usize));
    assert_eq!(primary, 16_384);
    // Vacuity guards: every family ran and some ran successfully.
    assert!(totals.iter().all(|n| *n > 0), "a family never ran");
    assert!(oks.iter().all(|n| *n > 0), "a family never succeeded");
    assert!(
        terminations > histories,
        "no seeded terminate applied beyond the prefix"
    );
    assert!(
        replays.iter().all(|n| *n > 0),
        "a main-step replay kind never ran"
    );
}

/// Sensitivity fixtures corrupt observer copies only; the kernel is never mutated.
#[test]
fn inv1_rejects_corrupted_overlap_and_conservation_views() {
    for f in FIXTURES {
        let p = prefix(f);
        let snapshot = p.kernel.clone();
        let view = p.observer.view(&p.kernel);
        assert_eq!(p.observer.check(&view, f), Ok(()));
        if !f.ga {
            let mut overlap = view.clone();
            let mut second = view
                .orders
                .iter()
                .find(|o| o.inventory_owned)
                .expect("an owning order")
                .clone();
            second.request.order_id = kid(9_999);
            second.request.payment.operation = kid(9_999);
            overlap.orders.push(second);
            overlap.order_count += 1;
            assert!(
                p.observer
                    .check(&overlap, f)
                    .unwrap_err()
                    .starts_with("INV-1 two active owners")
            );
        }
        let mut lost = view.clone();
        lost.remaining -= 1;
        assert!(
            p.observer
                .check(&lost, f)
                .unwrap_err()
                .starts_with("INV-1 inventory conservation")
        );
        assert_eq!(p.kernel, snapshot, "fixture mutated the kernel");
    }
}

#[test]
fn inv2_rejects_corrupted_budget_and_termination_count_views() {
    let f = FIXTURES[1];
    let p = prefix(f);
    let snapshot = p.kernel.clone();
    let view = p.observer.view(&p.kernel);
    assert_eq!(p.observer.check(&view, f), Ok(()));
    let mut budget = view.clone();
    budget.events = f.limits.observations + 1;
    assert!(
        p.observer
            .check(&budget, f)
            .unwrap_err()
            .starts_with("INV-2")
    );
    let mut records = view.clone();
    records.terminated_records += 1;
    assert!(
        p.observer
            .check(&records, f)
            .unwrap_err()
            .starts_with("INV-2")
    );
    assert_eq!(p.kernel, snapshot, "fixture mutated the kernel");
}

/// F-B2 style: alter only the observed reply, the public-state copy, the Eq
/// sentinel flag, or the saved first result.
fn assert_probe_sensitivity<R: Clone + PartialEq>(
    probe: &ReplayProbe<R>,
    wrong_replies: [Result<R, KernelError>; 3],
) {
    assert_eq!(check_replay(probe), Ok(()));
    for reply in wrong_replies {
        let mut altered = probe.clone();
        altered.reply = reply;
        assert!(
            check_replay(&altered)
                .unwrap_err()
                .starts_with("INV-3 replay reply differs from recorded first result")
        );
    }
    let mut changed_state = probe.clone();
    changed_state.after.remaining -= 1;
    assert!(
        check_replay(&changed_state)
            .unwrap_err()
            .starts_with("INV-3 replay changed public state")
    );
    // Flipping this flag does not inject an actual clock mutation.
    let mut advanced_time = probe.clone();
    advanced_time.kernel_unchanged = false;
    assert!(
        check_replay(&advanced_time)
            .unwrap_err()
            .starts_with("INV-3 replay mutated kernel or advanced admitted time")
    );
}

#[test]
fn inv3_rejects_corrupted_reserve_terminate_and_hold_replay_probes() {
    let f = FIXTURES[0];
    let mut p = prefix(f);
    let snapshot = p.kernel.clone();
    let o = p.observer.clone();
    let k = &mut p.kernel;
    assert_eq!(o.reserve_originals.len(), 3);
    assert_eq!(o.term_originals.len(), 1);
    assert_eq!(o.hold_originals.len(), 1);

    for (index, entry) in o.reserve_originals.iter().enumerate() {
        let other = o.reserve_originals[(index + 1) % 3].2;
        assert_ne!(other, entry.2);
        let probe = o.probe_reserve(k, entry);
        assert_probe_sensitivity(
            &probe,
            [
                Ok(AppliedReservation {
                    original: other,
                    replayed: true,
                }),
                Ok(AppliedReservation {
                    original: entry.2,
                    replayed: false,
                }),
                Err(KernelError::CommandConflict),
            ],
        );
    }
    let entry = &o.term_originals[0];
    let mut moved = entry.2;
    moved.applied_at_ms += 1;
    let probe = o.probe_terminate(k, entry);
    assert_probe_sensitivity(
        &probe,
        [
            Ok(AppliedTermination {
                original: moved,
                replayed: true,
            }),
            Ok(AppliedTermination {
                original: entry.2,
                replayed: false,
            }),
            Err(KernelError::CommandConflict),
        ],
    );
    let entry = &o.hold_originals[0];
    let mut moved_hold = entry.2;
    moved_hold.placed_at_ms += 1;
    let probe = o.probe_hold(k, entry);
    assert_probe_sensitivity(
        &probe,
        [
            Ok(AppliedHold {
                original: moved_hold,
                replayed: true,
            }),
            Ok(AppliedHold {
                original: entry.2,
                replayed: false,
            }),
            Err(KernelError::CommandConflict),
        ],
    );

    // Rewrite only saved first-result copies, then re-probe the real kernel.
    let mut rewritten = o.clone();
    rewritten.reserve_originals[0].2 = ReserveOutcome::Rejected(Rejection::Unavailable);
    rewritten.term_originals[0].2.applied_at_ms += 1;
    rewritten.hold_originals[0].2.placed_at_ms += 1;
    for message in [
        check_replay(&rewritten.probe_reserve(k, &rewritten.reserve_originals[0])),
        check_replay(&rewritten.probe_terminate(k, &rewritten.term_originals[0])),
        check_replay(&rewritten.probe_hold(k, &rewritten.hold_originals[0])),
    ] {
        assert!(
            message
                .unwrap_err()
                .starts_with("INV-3 replay reply differs from recorded first result")
        );
    }

    // The same saved copies fail the per-step record check, and so do corrupted views.
    let view = o.view(k);
    assert_eq!(o.check(&view, f), Ok(()));
    let mut terminate_only = o.clone();
    terminate_only.term_originals[0].2.applied_at_ms += 1;
    assert!(
        terminate_only
            .check(&view, f)
            .unwrap_err()
            .starts_with("INV-3 recorded termination")
    );
    let mut hold_only = o.clone();
    hold_only.hold_originals[0].2.placed_at_ms += 1;
    assert!(
        hold_only
            .check(&view, f)
            .unwrap_err()
            .starts_with("INV-3 placed hold")
    );
    let mut moved_record = view.clone();
    moved_record.terminations[0].1.applied_at_ms += 1;
    assert!(
        o.check(&moved_record, f)
            .unwrap_err()
            .starts_with("INV-3 recorded termination")
    );
    let mut lost_hold = view.clone();
    lost_hold.holds.clear();
    assert!(
        o.check(&lost_hold, f)
            .unwrap_err()
            .starts_with("INV-3 placed hold")
    );
    assert_eq!(*k, snapshot, "fixture mutated the kernel");
}

#[test]
fn inv4_rejects_corrupted_rebinding_and_double_capture_views() {
    let f = FIXTURES[0];
    let p = prefix(f);
    let snapshot = p.kernel.clone();
    let view = p.observer.view(&p.kernel);
    assert_eq!(p.observer.check(&view, f), Ok(()));
    // A second order bound to an existing payment, owning no inventory.
    let mut rebound = view.clone();
    let mut second = view.orders[0].clone();
    second.request.order_id = kid(9_999);
    second.inventory_owned = false;
    rebound.orders.push(second);
    rebound.order_count += 1;
    assert!(
        p.observer
            .check(&rebound, f)
            .unwrap_err()
            .starts_with("INV-4 operation rebound")
    );
    let mut doubled = p.observer.clone();
    doubled.capture_transitions[0].1 = 2;
    assert!(
        doubled
            .check(&view, f)
            .unwrap_err()
            .starts_with("INV-4 capture applied more than once")
    );
    assert_eq!(p.kernel, snapshot, "fixture mutated the kernel");
}

#[test]
fn inv5_rejects_corrupted_capture_on_terminated_and_held_orders() {
    for f in FIXTURES {
        let p = prefix(f);
        let snapshot = p.kernel.clone();
        let c = p.c.order_id;
        // Real kernel: c is terminated, held and carries a late capture.
        assert!(p.kernel.termination(c).is_some());
        assert!(p.kernel.hold(c).is_some());
        assert!(p.kernel.order(c).unwrap().captured.is_some());
        let view = p.observer.view(&p.kernel);
        assert_eq!(p.observer.check(&view, f), Ok(()));
        let position = view
            .orders
            .iter()
            .position(|o| o.request.order_id == c)
            .unwrap();
        let other_asset = AssetAmount::checked(
            AssetId::from_bytes([9; 32]),
            1_000,
            u128::MAX,
            RegistryVersion::new(1).unwrap(),
            Hash32::from_bytes([8; 32]),
        )
        .unwrap();
        for corrupted in [None, Some(amount(999)), Some(other_asset)] {
            let mut wrong = view.clone();
            wrong.orders[position].captured = corrupted;
            assert!(
                p.observer
                    .check(&wrong, f)
                    .unwrap_err()
                    .starts_with("INV-5")
            );
        }
        assert_eq!(p.kernel, snapshot, "fixture mutated the kernel");
    }
}
