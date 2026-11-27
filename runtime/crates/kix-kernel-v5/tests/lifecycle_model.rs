//! Seeded model test for the v5-only lifecycle surface.
//!
//! A deterministic generator produces mixed sequences over the shared commands
//! (reserve, send, expire, capture, owner change, scope cancel) and the v5-only
//! commands (`terminate`, `place_hold`, `clear_hold`, `reclaim_report`,
//! `reclaim_reports`). After every step the kernel's result and public view are
//! compared with a test-local oracle written from
//! `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md` sections 5-6 and
//! `validation/2026-10-13-k-stage2-v5-impl/README.md`: blocker order,
//! boundary-exact windows, one hold per order, termination once and replayed by
//! `decision_id`, termination blocking only `mark_payment_unknown`, a read-only
//! report, and batch order `(terminated_at, order_id)`.
//!
//! The oracle never calls `operation_snapshot`, `reclaim_report` or
//! `reclaim_reports` to compute an expectation. It was written with the v5
//! source in view, so agreement is not an independence proof. Every rejected
//! command must leave the kernel unchanged; the single documented exception is
//! `observe_capture` answering `Capacity` on a conflicting event, which still
//! quarantines bound operations and advances ordered time.

mod common;

use std::collections::{BTreeMap, BTreeSet};

use common::{amount, closure, human, id};
use kix_kernel_v5::{
    ActorKind, AppliedHold, AppliedReservation, AppliedTermination, Blocker, CaptureObservation,
    ClearedHold, CommandId, Context, DAY_MS, ExecutionFence, HoldKind, HoldRef, ImplicitHold,
    Inventory, Kernel, KernelError, Limits, MAX_BUNDLE, ObservationOutcome, OperationSnapshot,
    Order, OrderState, ProviderOperation, ReclaimBatch, ReclaimPolicy, ReclaimReport, Rejection,
    Reserve, ReserveOutcome, SEMANTICS_VERSION, Selection, Terminate, Termination,
};
use kix_types::{Hash32, KixId};

type EventKey = (KixId, KixId, KixId);

fn limits() -> Limits {
    Limits {
        commands: 12,
        orders: 6,
        observations: 5,
    }
}

fn engine() -> Kernel {
    Kernel::new(
        id(9),
        ExecutionFence {
            owner: id(1),
            generation: 1,
        },
        1,
        Inventory::seats(&[8]).unwrap(),
        limits(),
    )
    .unwrap()
}

/// `tight` shrinks every window so boundary-exact report times stay reachable
/// inside a short history. The values are test fixtures, not policy choices.
fn policy(tight: bool) -> ReclaimPolicy {
    if tight {
        ReclaimPolicy {
            retry_support_window_ms: 100,
            memory_residency_ms: 40,
            memory_residency_cap_records: 2,
            retention_floor_ms: 300,
        }
    } else {
        ReclaimPolicy::default()
    }
}

// ---------- generator ----------

struct Gen {
    state: u64,
    now: u64,
    owner: u8,
    generation: u64,
    epoch: u64,
}

impl Gen {
    fn below(&mut self, n: u64) -> u64 {
        self.state = self
            .state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        self.state % n
    }
}

/// How a report/batch step picks its `now_ms`. Boundary variants resolve
/// against the model so boundary-exact reads are generated, not hoped for.
#[derive(Clone, Copy, Debug)]
enum NowSel {
    Step,
    Current,
    Previous,
    ReplayMinus(()),
    ReplayAt(()),
    Residency(()),
    Far,
    Max,
}

/// The generator's `order`/`decision` bytes are hints: the driver resolves
/// them against the model so rare branches are hit deterministically (a stale
/// request on a terminatable order, a second decision on a terminated one).
/// Selection stays a pure function of the seed because the model is one.
#[derive(Clone, Copy, Debug)]
enum TermVariant {
    Fresh,
    /// Resend a stored request verbatim: the identical-payload replay.
    SameAsStored,
    /// Same `decision_id`, changed payload: `CommandConflict` once stored.
    Mutated,
    /// A second decision on an already-terminated order: `AlreadyTerminated`.
    Again,
    /// An earlier model snapshot (or a perturbed one): `StaleEvaluation`.
    Stale,
    Automatic,
    FalseCondition(usize),
}

/// Like [`TermVariant`], a hint resolved against the model at apply time.
#[derive(Clone, Copy, Debug)]
enum HoldMode {
    Fresh,
    /// Exact stored placement: `replayed`.
    Replay,
    /// A second hold id on a held order: `HoldExists`.
    Second,
    /// Same hold id, different payload: `CommandConflict`.
    Conflict,
}

#[derive(Clone, Debug)]
enum Op {
    Reserve {
        req: u8,
        order: u8,
        op: u8,
        first: u16,
        count: u16,
        expiry: u64,
        atoms: u128,
    },
    Send(u8),
    Expire(u8),
    Capture {
        op: u8,
        event: u8,
        atoms: u128,
    },
    Terminate {
        decision: u8,
        order: u8,
        variant: TermVariant,
    },
    PlaceHold {
        hold: u8,
        order: u8,
        kind: HoldKind,
        by: u8,
        mode: HoldMode,
    },
    ClearHold {
        hold: u8,
        by: u8,
    },
    Report {
        order: u8,
        at: NowSel,
        tight: bool,
    },
    Batch {
        order: u8,
        at: NowSel,
        tight: bool,
    },
    Owner {
        owner: u8,
        generation: u64,
    },
    Cancel(u64),
}

#[derive(Clone, Debug)]
struct Step {
    now_ms: u64,
    owner: u8,
    generation: u64,
    op: Op,
}

fn now_sel(source: &mut Gen) -> NowSel {
    match source.below(10) {
        0 => NowSel::Step,
        1 => NowSel::Current,
        2 => NowSel::Previous,
        3 | 4 => NowSel::ReplayMinus(()),
        5 | 6 => NowSel::ReplayAt(()),
        7 => NowSel::Residency(()),
        8 => NowSel::Far,
        _ => NowSel::Max,
    }
}

fn history(seed: u64, steps: usize) -> Vec<Step> {
    let mut source = Gen {
        state: seed,
        now: 0,
        owner: 1,
        generation: 1,
        epoch: 1,
    };
    let mut out = Vec::with_capacity(steps);
    for _ in 0..steps {
        // Mostly monotone: a rare one-step regression exercises ClockRegression
        // on commands without poisoning the planned owner fence for the tail,
        // and occasional large jumps carry time past short expiries.
        let now_ms = if source.below(23) == 0 {
            source.now.saturating_sub(1)
        } else if source.below(9) == 0 {
            source.now.saturating_add(50 + source.below(500))
        } else {
            source.now.saturating_add(1 + source.below(3))
        };
        source.now = now_ms;
        let owner = source.owner;
        let generation = source.generation;
        let kind = source.below(28);
        let op = match kind {
            0..=3 => {
                let req = 1 + source.below(6) as u8;
                let order = 1 + source.below(6) as u8;
                let op = if source.below(4) == 0 {
                    1 + source.below(6) as u8
                } else {
                    order
                };
                let atoms = [10_000_u128, 1, 20_000, 0][source.below(4) as usize];
                let expiry = match source.below(6) {
                    0 => now_ms,
                    1 | 2 => now_ms + 1 + source.below(300),
                    _ => 50_000,
                };
                Op::Reserve {
                    req,
                    order,
                    op,
                    first: source.below(8) as u16,
                    count: 1,
                    expiry,
                    atoms,
                }
            }
            4..=8 => Op::Send(1 + source.below(6) as u8),
            9 | 10 => Op::Expire(1 + source.below(6) as u8),
            11..=14 => Op::Capture {
                op: 1 + source.below(6) as u8,
                event: 1 + source.below(4) as u8,
                atoms: match source.below(3) {
                    0 | 1 => 10_000_u128,
                    _ => [1, 20_000][source.below(2) as usize],
                },
            },
            15..=18 => {
                let variant = match source.below(12) {
                    0..=2 => TermVariant::Fresh,
                    3 | 4 => TermVariant::Again,
                    5 => TermVariant::SameAsStored,
                    6 => TermVariant::Mutated,
                    7 | 8 => TermVariant::Stale,
                    9 => TermVariant::Automatic,
                    _ => TermVariant::FalseCondition(source.below(5) as usize),
                };
                Op::Terminate {
                    decision: 60 + source.below(16) as u8,
                    order: 1 + source.below(6) as u8,
                    variant,
                }
            }
            19..=21 => Op::PlaceHold {
                hold: 70 + source.below(3) as u8,
                order: 1 + source.below(6) as u8,
                kind: [HoldKind::Legal, HoldKind::Dispute, HoldKind::Erasure]
                    [source.below(3) as usize],
                by: 50 + source.below(2) as u8,
                mode: match source.below(4) {
                    0 => HoldMode::Replay,
                    1 => HoldMode::Second,
                    2 => HoldMode::Conflict,
                    _ => HoldMode::Fresh,
                },
            },
            22 => Op::ClearHold {
                hold: 70 + source.below(3) as u8,
                by: 51 + source.below(3) as u8,
            },
            23 | 24 => Op::Report {
                order: 1 + source.below(6) as u8,
                at: now_sel(&mut source),
                tight: source.below(4) == 0,
            },
            25 => Op::Batch {
                order: 1 + source.below(6) as u8,
                at: now_sel(&mut source),
                tight: source.below(4) == 0,
            },
            _ => {
                if source.below(2) == 0 {
                    let next_owner = if source.below(2) == 0 {
                        source.owner
                    } else {
                        8
                    };
                    let next_gen = source.generation.saturating_add(1);
                    source.owner = next_owner;
                    source.generation = next_gen;
                    Op::Owner {
                        owner: next_owner,
                        generation: next_gen,
                    }
                } else {
                    let same = source.below(4) == 0;
                    let next = if same {
                        source.epoch
                    } else {
                        source.epoch.saturating_add(1)
                    };
                    if next > source.epoch {
                        source.epoch = next;
                    }
                    Op::Cancel(next)
                }
            }
        };
        out.push(Step {
            now_ms,
            owner,
            generation,
            op,
        });
    }
    out
}

// ---------- request builders ----------

fn reserve_request(
    req: u8,
    order: u8,
    op: u8,
    first: u16,
    count: u16,
    expiry: u64,
    atoms: u128,
) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(9),
            principal: id(2),
            request: id(req),
        },
        order_id: id(order),
        expected_business_epoch: 1,
        selection: Selection::Seats { first, count },
        amount: amount(atoms),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: expiry,
        payment: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(op),
        },
    }
}

fn capture_observation(op: u8, event: u8, atoms: u128) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(op),
        },
        amount: amount(atoms),
        evidence_hash: Hash32::from_bytes([event; 32]),
    }
}

/// `evaluated` comes from the model's own snapshot, never the kernel's.
fn terminate_request(model: &Model, decision: u8, order: u8) -> Terminate {
    terminate_request_with(model, id(decision), id(order))
}

fn terminate_request_with(model: &Model, decision: KixId, order_id: KixId) -> Terminate {
    Terminate {
        decision_id: decision,
        order_id,
        evaluated: model.snapshot(order_id).unwrap_or(EMPTY_SNAPSHOT),
        evaluation: closure([true; 5]),
        authority: human(40),
        rule_hash: Hash32::from_bytes([6; 32]),
    }
}

const EMPTY_SNAPSHOT: OperationSnapshot = OperationSnapshot {
    state: OrderState::Held,
    captured: None,
    review_required: false,
    reserved_slot: false,
    observations: 0,
    retained_conflicts: 0,
};

// ---------- oracle ----------

struct Out<T> {
    result: Result<T, KernelError>,
    /// Whether the kernel is expected to differ after the call. `Err` changes
    /// nothing, except `observe_capture` answering `Capacity` on a conflict.
    changed: bool,
}

impl<T> Out<T> {
    fn same(result: Result<T, KernelError>) -> Self {
        Self {
            result,
            changed: false,
        }
    }
    fn moved(result: Result<T, KernelError>) -> Self {
        Self {
            result,
            changed: true,
        }
    }
}

#[derive(Debug, Clone)]
struct CommandRecord {
    request: Reserve,
    result: ReserveOutcome,
    applied_at_ms: u64,
}

/// Test-local oracle over the crate's public data types. It mirrors the
/// documented check order and builds every expectation (including the
/// `Terminate::evaluated` snapshot and every `ReclaimReport` field) from its
/// own maps; it never calls the kernel's report or snapshot code paths.
struct Model {
    scope: KixId,
    fence: ExecutionFence,
    epoch: u64,
    cancelled: bool,
    now_ms: u64,
    segments: Vec<(u16, u16)>,
    occupied: BTreeSet<u16>,
    limits: Limits,
    commands: BTreeMap<CommandId, CommandRecord>,
    orders: BTreeMap<KixId, Order>,
    operations: BTreeMap<ProviderOperation, KixId>,
    quarantined: BTreeSet<ProviderOperation>,
    observations: BTreeMap<EventKey, (CaptureObservation, ObservationOutcome)>,
    conflicts: Vec<CaptureObservation>,
    reserved: BTreeSet<ProviderOperation>,
    terminations: BTreeMap<KixId, Termination>,
    terminated_orders: BTreeMap<KixId, KixId>,
    terminated_index: BTreeSet<(u64, KixId)>,
    holds: BTreeMap<KixId, HoldRef>,
    hold_orders: BTreeMap<KixId, KixId>,
    /// First snapshot recorded per order, used to build stale evaluations.
    first_snapshot: BTreeMap<KixId, OperationSnapshot>,
}

impl Model {
    fn new() -> Self {
        Self {
            scope: id(9),
            fence: ExecutionFence {
                owner: id(1),
                generation: 1,
            },
            epoch: 1,
            cancelled: false,
            now_ms: 0,
            segments: vec![(0, 8)],
            occupied: BTreeSet::new(),
            limits: limits(),
            commands: BTreeMap::new(),
            orders: BTreeMap::new(),
            operations: BTreeMap::new(),
            quarantined: BTreeSet::new(),
            observations: BTreeMap::new(),
            conflicts: Vec::new(),
            reserved: BTreeSet::new(),
            terminations: BTreeMap::new(),
            terminated_orders: BTreeMap::new(),
            terminated_index: BTreeSet::new(),
            holds: BTreeMap::new(),
            hold_orders: BTreeMap::new(),
            first_snapshot: BTreeMap::new(),
        }
    }

    fn context(&self, ctx: Context) -> Result<(), KernelError> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Err(KernelError::UnsupportedSemantics);
        }
        if ctx.fence != self.fence {
            return Err(KernelError::ExecutionFenced);
        }
        if ctx.now_ms < self.now_ms {
            return Err(KernelError::ClockRegression);
        }
        Ok(())
    }

    fn slots_used(&self) -> usize {
        self.observations
            .len()
            .saturating_add(self.conflicts.len())
            .saturating_add(self.reserved.len())
    }

    fn has_retained_conflict(&self, operation: ProviderOperation) -> bool {
        self.conflicts
            .iter()
            .any(|conflict| conflict.operation == operation)
    }

    fn conflict_is_retained(&self, observation: &CaptureObservation) -> bool {
        self.conflicts.contains(observation)
    }

    fn retain_conflict(&mut self, observation: CaptureObservation) {
        self.conflicts.push(observation);
    }

    fn quarantine_bound(&mut self, operation: ProviderOperation) {
        if let Some(&order_id) = self.operations.get(&operation)
            && let Some(order) = self.orders.get_mut(&order_id)
        {
            order.review_required = true;
            self.quarantined.insert(operation);
        }
    }

    fn check_selection(&self, selection: Selection) -> Result<(), Rejection> {
        match selection {
            Selection::Seats { first, count } => {
                let Some(end) = first.checked_add(count) else {
                    return Err(Rejection::InvalidRequest);
                };
                if count == 0
                    || count > MAX_BUNDLE
                    || !self
                        .segments
                        .iter()
                        .any(|&(lo, hi)| first >= lo && end <= hi)
                {
                    return Err(Rejection::InvalidRequest);
                }
                if (first..end).any(|seat| self.occupied.contains(&seat)) {
                    return Err(Rejection::Unavailable);
                }
                Ok(())
            }
            _ => Err(Rejection::InvalidRequest),
        }
    }

    fn adjust(&mut self, selection: Selection, acquire: bool) {
        if let Selection::Seats { first, count } = selection {
            for seat in first..first + count {
                if acquire {
                    self.occupied.insert(seat);
                } else {
                    self.occupied.remove(&seat);
                }
            }
        }
    }

    fn remaining(&self) -> u32 {
        let total: u32 = self
            .segments
            .iter()
            .map(|&(lo, hi)| u32::from(hi - lo))
            .sum();
        total - u32::try_from(self.occupied.len()).unwrap_or(0)
    }

    fn snapshot(&self, order_id: KixId) -> Option<OperationSnapshot> {
        let order = self.orders.get(&order_id)?;
        Some(OperationSnapshot {
            state: order.state,
            captured: order.captured,
            review_required: order.review_required,
            reserved_slot: self.reserved.contains(&order.request.payment),
            observations: self.observations.len(),
            retained_conflicts: self.conflicts.len(),
        })
    }

    fn reserve(&mut self, ctx: Context, request: Reserve) -> Out<AppliedReservation> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Out::same(Err(KernelError::UnsupportedSemantics));
        }
        if request.id.scope != self.scope {
            return Out::same(Err(KernelError::WrongScope));
        }
        if let Some(record) = self.commands.get(&request.id) {
            if record.request != request {
                return Out::same(Err(KernelError::CommandConflict));
            }
            return Out::same(Ok(AppliedReservation {
                original: record.result,
                replayed: true,
            }));
        }
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        if self.commands.len() >= self.limits.commands || self.orders.len() >= self.limits.orders {
            return Out::same(Err(KernelError::Capacity));
        }
        let rejection = if self.cancelled || request.expected_business_epoch != self.epoch {
            Some(Rejection::BusinessFenced)
        } else if request.expires_at_ms <= ctx.now_ms || request.amount.atoms() == 0 {
            Some(Rejection::InvalidRequest)
        } else if self.orders.contains_key(&request.order_id) {
            Some(Rejection::OrderExists)
        } else if self.quarantined.contains(&request.payment)
            || self.has_retained_conflict(request.payment)
        {
            Some(Rejection::OperationQuarantined)
        } else if self.operations.contains_key(&request.payment) {
            Some(Rejection::OperationAlreadyBound)
        } else {
            self.check_selection(request.selection).err()
        };
        let result = if let Some(reason) = rejection {
            ReserveOutcome::Rejected(reason)
        } else {
            self.adjust(request.selection, true);
            self.operations.insert(request.payment, request.order_id);
            let order_id = request.order_id;
            self.orders.insert(
                order_id,
                Order {
                    request: request.clone(),
                    submitted_under: ctx.fence,
                    state: OrderState::Held,
                    inventory_owned: true,
                    captured: None,
                    review_required: false,
                },
            );
            self.first_snapshot
                .entry(order_id)
                .or_insert_with(|| OperationSnapshot {
                    state: OrderState::Held,
                    captured: None,
                    review_required: false,
                    reserved_slot: self.reserved.contains(&request.payment),
                    observations: self.observations.len(),
                    retained_conflicts: self.conflicts.len(),
                });
            ReserveOutcome::Held(order_id)
        };
        self.commands.insert(
            request.id,
            CommandRecord {
                request,
                result,
                applied_at_ms: ctx.now_ms,
            },
        );
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(AppliedReservation {
            original: result,
            replayed: false,
        }))
    }

    fn mark_payment_unknown(&mut self, ctx: Context, order_id: KixId) -> Out<()> {
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        let Some(order) = self.orders.get(&order_id) else {
            return Out::same(Err(KernelError::UnknownOrder));
        };
        if self.terminated_orders.contains_key(&order_id) {
            return Out::same(Err(KernelError::InvalidTransition));
        }
        if order.review_required
            || !matches!(order.state, OrderState::Held | OrderState::PaymentUnknown)
        {
            return Out::same(Err(KernelError::InvalidTransition));
        }
        if self.cancelled || ctx.now_ms >= order.request.expires_at_ms {
            return Out::same(Err(KernelError::InvalidTransition));
        }
        let operation = order.request.payment;
        if !self.reserved.contains(&operation) {
            if self.slots_used() >= self.limits.observations {
                return Out::same(Err(KernelError::Capacity));
            }
            self.reserved.insert(operation);
        }
        if let Some(order) = self.orders.get_mut(&order_id) {
            order.state = OrderState::PaymentUnknown;
        }
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(()))
    }

    fn expire(&mut self, ctx: Context, order_id: KixId) -> Out<bool> {
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        let Some(order) = self.orders.get_mut(&order_id) else {
            return Out::same(Err(KernelError::UnknownOrder));
        };
        self.now_ms = ctx.now_ms;
        if ctx.now_ms < order.request.expires_at_ms {
            return Out::moved(Ok(false));
        }
        if order.state == OrderState::Held && order.inventory_owned {
            let selection = order.request.selection;
            order.inventory_owned = false;
            order.state = OrderState::Expired;
            self.adjust(selection, false);
            return Out::moved(Ok(true));
        }
        Out::moved(Ok(false))
    }

    fn cancel_scope(&mut self, ctx: Context, next_epoch: u64) -> Out<()> {
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        if next_epoch <= self.epoch {
            return Out::same(Err(KernelError::InvalidTransition));
        }
        self.epoch = next_epoch;
        self.cancelled = true;
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(()))
    }

    fn replace_owner(&mut self, ctx: Context, next: ExecutionFence) -> Out<()> {
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        if next.generation <= self.fence.generation {
            return Out::same(Err(KernelError::InvalidTransition));
        }
        self.fence = next;
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(()))
    }

    fn observe_capture(
        &mut self,
        ctx: Context,
        observation: CaptureObservation,
    ) -> Out<ObservationOutcome> {
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        let key = (
            observation.operation.provider,
            observation.operation.account,
            observation.event_id,
        );
        if let Some((original, result)) = self.observations.get(&key) {
            if *original == observation {
                self.now_ms = ctx.now_ms;
                return Out::moved(Ok(*result));
            }
            let affected = [original.operation, observation.operation];
            for operation in affected {
                self.quarantine_bound(operation);
            }
            self.now_ms = ctx.now_ms;
            if !self.conflict_is_retained(&observation) {
                if self.slots_used() >= self.limits.observations {
                    // Documented exception: the conflict already quarantined
                    // bound operations and advanced ordered time.
                    return Out::moved(Err(KernelError::Capacity));
                }
                self.retain_conflict(observation);
            }
            return Out::moved(Ok(ObservationOutcome::Conflict));
        }
        let has_reserved_slot = self.reserved.contains(&observation.operation);
        if !has_reserved_slot && self.slots_used() >= self.limits.observations {
            return Out::same(Err(KernelError::Capacity));
        }
        let Some(&order_id) = self.operations.get(&observation.operation) else {
            return Out::same(Err(KernelError::UnknownOperation));
        };
        let mut release: Option<Selection> = None;
        let result = {
            let Some(order) = self.orders.get_mut(&order_id) else {
                return Out::same(Err(KernelError::UnknownOrder));
            };
            if let Some(captured) = order.captured {
                if captured == observation.amount {
                    ObservationOutcome::DuplicateEffect
                } else {
                    order.review_required = true;
                    ObservationOutcome::Review
                }
            } else {
                order.captured = Some(observation.amount);
                if observation.amount != order.request.amount {
                    order.state = OrderState::Review;
                    order.review_required = true;
                    ObservationOutcome::Review
                } else if self.cancelled
                    || ctx.now_ms >= order.request.expires_at_ms
                    || order.state == OrderState::Expired
                {
                    if order.inventory_owned {
                        release = Some(order.request.selection);
                        order.inventory_owned = false;
                    }
                    order.state = OrderState::ReturnRequired;
                    ObservationOutcome::ReturnRequired
                } else if order.review_required {
                    order.state = OrderState::Review;
                    ObservationOutcome::Review
                } else {
                    order.state = OrderState::PaymentConfirmed;
                    ObservationOutcome::PaymentConfirmed
                }
            }
        };
        if let Some(selection) = release {
            self.adjust(selection, false);
        }
        self.reserved.remove(&observation.operation);
        self.observations.insert(key, (observation, result));
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(result))
    }

    fn terminate(&mut self, ctx: Context, request: Terminate) -> Out<AppliedTermination> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Out::same(Err(KernelError::UnsupportedSemantics));
        }
        if let Some(existing) = self.terminations.get(&request.decision_id) {
            if existing.request != request {
                return Out::same(Err(KernelError::CommandConflict));
            }
            return Out::same(Ok(AppliedTermination {
                original: *existing,
                replayed: true,
            }));
        }
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        if request.authority.actor == ActorKind::Automatic {
            return Out::same(Err(KernelError::AutomaticApprovalDisabled));
        }
        let Some(order) = self.orders.get(&request.order_id) else {
            return Out::same(Err(KernelError::UnknownOrder));
        };
        if self.terminated_orders.contains_key(&request.order_id) {
            return Out::same(Err(KernelError::AlreadyTerminated));
        }
        let reserved_slot = self.reserved.contains(&order.request.payment);
        if order.state != OrderState::PaymentUnknown
            || order.captured.is_some()
            || order.state == OrderState::ReturnRequired
            || order.review_required
            || !reserved_slot
        {
            return Out::same(Err(KernelError::InvalidTransition));
        }
        if request
            .evaluation
            .c
            .iter()
            .any(|condition| !condition.holds)
        {
            return Out::same(Err(KernelError::ConditionNotSatisfied));
        }
        let snapshot = OperationSnapshot {
            state: order.state,
            captured: order.captured,
            review_required: order.review_required,
            reserved_slot,
            observations: self.observations.len(),
            retained_conflicts: self.conflicts.len(),
        };
        if request.evaluated != snapshot {
            return Out::same(Err(KernelError::StaleEvaluation));
        }
        let record = Termination {
            request,
            applied_at_ms: ctx.now_ms,
        };
        self.terminated_orders
            .insert(request.order_id, request.decision_id);
        self.terminated_index
            .insert((record.applied_at_ms, request.order_id));
        self.terminations.insert(request.decision_id, record);
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(AppliedTermination {
            original: record,
            replayed: false,
        }))
    }

    fn place_hold(
        &mut self,
        ctx: Context,
        order_id: KixId,
        hold_id: KixId,
        kind: HoldKind,
        placed_by: KixId,
    ) -> Out<AppliedHold> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Out::same(Err(KernelError::UnsupportedSemantics));
        }
        if let Some(&held_order) = self.hold_orders.get(&hold_id) {
            return match self.holds.get(&held_order) {
                Some(existing)
                    if held_order == order_id
                        && existing.kind == kind
                        && existing.placed_by == placed_by =>
                {
                    Out::same(Ok(AppliedHold {
                        original: *existing,
                        replayed: true,
                    }))
                }
                _ => Out::same(Err(KernelError::CommandConflict)),
            };
        }
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        if !self.orders.contains_key(&order_id) {
            return Out::same(Err(KernelError::UnknownOrder));
        }
        if self.holds.contains_key(&order_id) {
            return Out::same(Err(KernelError::HoldExists));
        }
        let hold = HoldRef {
            id: hold_id,
            kind,
            placed_at_ms: ctx.now_ms,
            placed_by,
        };
        self.holds.insert(order_id, hold);
        self.hold_orders.insert(hold_id, order_id);
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(AppliedHold {
            original: hold,
            replayed: false,
        }))
    }

    fn clear_hold(&mut self, ctx: Context, hold_id: KixId, by: KixId) -> Out<ClearedHold> {
        if let Err(error) = self.context(ctx) {
            return Out::same(Err(error));
        }
        let Some(&order_id) = self.hold_orders.get(&hold_id) else {
            return Out::same(Err(KernelError::UnknownHold));
        };
        let Some(hold) = self.holds.remove(&order_id) else {
            return Out::same(Err(KernelError::UnknownHold));
        };
        self.hold_orders.remove(&hold_id);
        self.now_ms = ctx.now_ms;
        Out::moved(Ok(ClearedHold {
            hold,
            order_id,
            cleared_by: by,
            cleared_at_ms: ctx.now_ms,
        }))
    }

    fn first_result_ms(&self, order_id: KixId) -> Option<u64> {
        self.orders
            .get(&order_id)
            .and_then(|order| self.commands.get(&order.request.id))
            .map(|record| record.applied_at_ms)
    }

    fn terminated_at_ms(&self, order_id: KixId) -> Option<u64> {
        self.terminated_orders
            .get(&order_id)
            .and_then(|decision| self.terminations.get(decision))
            .map(|record| record.applied_at_ms)
    }

    fn terminatable(&self, order_id: KixId) -> bool {
        match self.orders.get(&order_id) {
            None => false,
            Some(order) => {
                order.state == OrderState::PaymentUnknown
                    && order.captured.is_none()
                    && !order.review_required
                    && self.reserved.contains(&order.request.payment)
                    && !self.terminated_orders.contains_key(&order_id)
            }
        }
    }

    fn pick_where(&self, hint: u8, pred: impl Fn(&Self, KixId) -> bool) -> Option<KixId> {
        let matches: Vec<KixId> = self
            .orders
            .keys()
            .copied()
            .filter(|order_id| pred(self, *order_id))
            .collect();
        if matches.is_empty() {
            None
        } else {
            Some(matches[usize::from(hint) % matches.len()])
        }
    }

    fn pick_terminatable(&self, hint: u8) -> Option<KixId> {
        self.pick_where(hint, Self::terminatable)
    }

    fn pick_terminated(&self, hint: u8) -> Option<KixId> {
        self.pick_where(hint, |model, order_id| {
            model.terminated_orders.contains_key(&order_id)
        })
    }

    /// A `decision_id` not yet stored, so a fresh request reaches the order
    /// checks instead of the replay/conflict branch.
    fn free_decision(&self, hint: u8) -> KixId {
        for offset in 0..16_u8 {
            let candidate = id(60 + hint.wrapping_add(offset) % 16);
            if !self.terminations.contains_key(&candidate) {
                return candidate;
            }
        }
        id(60 + hint % 16)
    }

    fn pick_held(&self, hint: u8) -> Option<(KixId, HoldRef)> {
        let held: Vec<(KixId, HoldRef)> = self
            .holds
            .iter()
            .map(|(order, hold)| (*order, *hold))
            .collect();
        if held.is_empty() {
            None
        } else {
            Some(held[usize::from(hint) % held.len()])
        }
    }

    /// A `hold_id` not currently placed, so `HoldExists` — not a replay or a
    /// conflict — is what the order check returns.
    fn free_hold(&self, hint: u8) -> KixId {
        for offset in 0..16_u8 {
            let candidate = id(70 + hint.wrapping_add(offset) % 16);
            if !self.hold_orders.contains_key(&candidate) {
                return candidate;
            }
        }
        id(70 + hint % 16)
    }

    /// Boundary variants resolve against the reported order itself, so a hit
    /// is exact whenever that order exists and the time is not regressed.
    fn resolve_now(
        &self,
        at: NowSel,
        order_id: KixId,
        step_now: u64,
        policy: &ReclaimPolicy,
    ) -> u64 {
        match at {
            NowSel::Step => step_now,
            NowSel::Current => self.now_ms,
            NowSel::Previous => self.now_ms.saturating_sub(1),
            NowSel::ReplayMinus(_) => self
                .first_result_ms(order_id)
                .map(|first| first.saturating_add(policy.retry_support_window_ms))
                .map_or(self.now_ms, |end| end.saturating_sub(1)),
            NowSel::ReplayAt(_) => self.first_result_ms(order_id).map_or(self.now_ms, |first| {
                first.saturating_add(policy.retry_support_window_ms)
            }),
            NowSel::Residency(_) => self.terminated_at_ms(order_id).map_or(self.now_ms, |at| {
                at.saturating_add(policy.memory_residency_ms)
            }),
            NowSel::Far => self.now_ms.saturating_add(30 * DAY_MS),
            NowSel::Max => u64::MAX,
        }
    }

    fn report(
        &self,
        now_ms: u64,
        order_id: KixId,
        reclaim: &ReclaimPolicy,
    ) -> Result<ReclaimReport, KernelError> {
        if now_ms < self.now_ms {
            return Err(KernelError::ClockRegression);
        }
        let order = self
            .orders
            .get(&order_id)
            .ok_or(KernelError::UnknownOrder)?;
        Ok(self.report_for(now_ms, order_id, order, reclaim))
    }

    fn batch(&self, now_ms: u64, reclaim: &ReclaimPolicy) -> Result<ReclaimBatch, KernelError> {
        if now_ms < self.now_ms {
            return Err(KernelError::ClockRegression);
        }
        let reports = self
            .terminated_index
            .iter()
            .filter_map(|(_, order_id)| {
                let order = self.orders.get(order_id)?;
                Some(self.report_for(now_ms, *order_id, order, reclaim))
            })
            .collect();
        Ok(ReclaimBatch {
            now_ms,
            terminated_records: self.terminated_index.len(),
            over_residency_cap: self.terminated_index.len() > reclaim.memory_residency_cap_records,
            reports,
        })
    }

    /// The report, built only from model fields. `UnboundFence` is read as
    /// retained conflict evidence for the candidate's own operation identity;
    /// "open conflict" is a quarantined operation or retained conflict.
    fn report_for(
        &self,
        now_ms: u64,
        order_id: KixId,
        order: &Order,
        reclaim: &ReclaimPolicy,
    ) -> ReclaimReport {
        let operation = order.request.payment;
        let terminated_at_ms = self.terminated_at_ms(order_id);
        let first_result_ms = self
            .commands
            .get(&order.request.id)
            .map_or(now_ms, |record| record.applied_at_ms);
        let replay_window_ends_at_ms =
            first_result_ms.saturating_add(reclaim.retry_support_window_ms);
        let hold = self.holds.get(&order_id).copied();
        let retained_conflict = self.has_retained_conflict(operation);
        let mut implicit_hold = Vec::new();
        if order.state == OrderState::ReturnRequired {
            implicit_hold.push(ImplicitHold::ReturnRequired);
        }
        if retained_conflict || self.quarantined.contains(&operation) {
            implicit_hold.push(ImplicitHold::OpenConflict);
        }
        let mut blockers = Vec::new();
        if terminated_at_ms.is_none() {
            blockers.push(Blocker::ActiveOp);
        }
        if self.reserved.contains(&operation) {
            blockers.push(Blocker::ReservedSlot);
        }
        if order.review_required {
            blockers.push(Blocker::ReviewRequired);
        }
        if retained_conflict {
            blockers.push(Blocker::UnboundFence);
        }
        if order.state == OrderState::ReturnRequired {
            blockers.push(Blocker::ReturnObligation);
        }
        if now_ms < replay_window_ends_at_ms {
            blockers.push(Blocker::ReplayWindow);
        }
        if hold.is_some() || !implicit_hold.is_empty() {
            blockers.push(Blocker::Hold);
        }
        blockers.extend([Blocker::I09, Blocker::I10, Blocker::I13]);
        ReclaimReport {
            order_id,
            terminated_at_ms,
            blockers,
            hold,
            implicit_hold,
            replay_window_ends_at_ms,
            memory_residency_ends_at_ms: terminated_at_ms
                .map(|at| at.saturating_add(reclaim.memory_residency_ms)),
            retention_floor_ends_at_ms: terminated_at_ms
                .map(|at| at.saturating_add(reclaim.retention_floor_ms)),
        }
    }

    fn view(&self) -> String {
        let mut rows = String::new();
        for n in 1_u8..=8 {
            let order_id = id(n);
            match self.orders.get(&order_id) {
                None => rows.push_str(&format!("{n}:none;")),
                Some(order) => rows.push_str(&format!("{n}:{};", order_row(order))),
            }
            let termination = self
                .terminated_orders
                .get(&order_id)
                .and_then(|decision| self.terminations.get(decision));
            rows.push_str(&format!(
                "t{n}={termination:?};h{n}={:?};",
                self.holds.get(&order_id)
            ));
        }
        let mut conflicts = String::new();
        for conflict in &self.conflicts {
            conflicts.push_str(&format!("{conflict:?};"));
        }
        format!(
            "rem={} orders={} obs={} res={} quar={} conflicts={conflicts} rows={rows}",
            self.remaining(),
            self.orders.len(),
            self.observations.len(),
            self.reserved.len(),
            self.quarantined.len()
        )
    }
}

// ---------- kernel view ----------

fn order_row(order: &Order) -> String {
    format!(
        "{:?}|{}|{}|{}|{:?}|{}",
        order.state,
        order.inventory_owned,
        order.review_required,
        order.captured.map(|amount| amount.atoms()).unwrap_or(0),
        order.submitted_under.owner,
        order.submitted_under.generation
    )
}

fn kernel_view(kernel: &Kernel) -> String {
    let mut rows = String::new();
    for n in 1_u8..=8 {
        let order_id = id(n);
        match kernel.order(order_id) {
            None => rows.push_str(&format!("{n}:none;")),
            Some(order) => rows.push_str(&format!("{n}:{};", order_row(order))),
        }
        rows.push_str(&format!(
            "t{n}={:?};h{n}={:?};",
            kernel.termination(order_id),
            kernel.hold(order_id)
        ));
    }
    let mut conflicts = String::new();
    for conflict in kernel.conflicts() {
        conflicts.push_str(&format!("{conflict:?};"));
    }
    format!(
        "rem={} orders={} obs={} res={} quar={} conflicts={conflicts} rows={rows}",
        kernel.remaining(),
        kernel.order_count(),
        kernel.observation_count(),
        kernel.reserved_observation_count(),
        kernel.quarantined_operation_count()
    )
}

// ---------- coverage ----------

#[derive(Debug, Default)]
struct Coverage {
    reserve: u64,
    send: u64,
    expire: u64,
    capture: u64,
    terminate: u64,
    place_hold: u64,
    clear_hold: u64,
    report: u64,
    batch: u64,
    owner_or_cancel: u64,
    reserve_replayed: u64,
    conflict_outcome: u64,
    conflict_capacity_mutated: u64,
    term_applied: u64,
    term_replayed: u64,
    term_already: u64,
    term_stale: u64,
    term_condition: u64,
    term_automatic: u64,
    term_invalid: u64,
    term_conflict: u64,
    send_after_terminate: u64,
    hold_placed: u64,
    hold_replayed: u64,
    hold_exists: u64,
    hold_conflict: u64,
    clear_ok: u64,
    clear_unknown: u64,
    implicit_return: u64,
    implicit_conflict: u64,
    boundary_below: u64,
    boundary_at: u64,
    report_regression: u64,
}

impl Coverage {
    fn merge(&mut self, other: &Coverage) {
        for (total, extra) in [
            (&mut self.reserve, other.reserve),
            (&mut self.send, other.send),
            (&mut self.expire, other.expire),
            (&mut self.capture, other.capture),
            (&mut self.terminate, other.terminate),
            (&mut self.place_hold, other.place_hold),
            (&mut self.clear_hold, other.clear_hold),
            (&mut self.report, other.report),
            (&mut self.batch, other.batch),
            (&mut self.owner_or_cancel, other.owner_or_cancel),
            (&mut self.reserve_replayed, other.reserve_replayed),
            (&mut self.conflict_outcome, other.conflict_outcome),
            (
                &mut self.conflict_capacity_mutated,
                other.conflict_capacity_mutated,
            ),
            (&mut self.term_applied, other.term_applied),
            (&mut self.term_replayed, other.term_replayed),
            (&mut self.term_already, other.term_already),
            (&mut self.term_stale, other.term_stale),
            (&mut self.term_condition, other.term_condition),
            (&mut self.term_automatic, other.term_automatic),
            (&mut self.term_invalid, other.term_invalid),
            (&mut self.term_conflict, other.term_conflict),
            (&mut self.send_after_terminate, other.send_after_terminate),
            (&mut self.hold_placed, other.hold_placed),
            (&mut self.hold_replayed, other.hold_replayed),
            (&mut self.hold_exists, other.hold_exists),
            (&mut self.hold_conflict, other.hold_conflict),
            (&mut self.clear_ok, other.clear_ok),
            (&mut self.clear_unknown, other.clear_unknown),
            (&mut self.implicit_return, other.implicit_return),
            (&mut self.implicit_conflict, other.implicit_conflict),
            (&mut self.boundary_below, other.boundary_below),
            (&mut self.boundary_at, other.boundary_at),
            (&mut self.report_regression, other.report_regression),
        ] {
            *total += extra;
        }
    }

    /// The guard exists so a seed set cannot pass vacuously: every listed
    /// behaviour must occur at least once across all seeds.
    fn assert_covered(&self) {
        for (name, count) in [
            ("applied termination", self.term_applied),
            ("termination replay", self.term_replayed),
            ("AlreadyTerminated", self.term_already),
            ("StaleEvaluation", self.term_stale),
            ("ConditionNotSatisfied", self.term_condition),
            ("AutomaticApprovalDisabled", self.term_automatic),
            ("terminate InvalidTransition", self.term_invalid),
            ("terminate CommandConflict", self.term_conflict),
            ("send after terminate", self.send_after_terminate),
            ("place hold", self.hold_placed),
            ("place hold replay", self.hold_replayed),
            ("HoldExists", self.hold_exists),
            ("hold CommandConflict", self.hold_conflict),
            ("clear hold", self.clear_ok),
            ("UnknownHold", self.clear_unknown),
            ("ReturnRequired implicit hold", self.implicit_return),
            ("OpenConflict implicit hold", self.implicit_conflict),
            ("replay-window boundary below", self.boundary_below),
            ("replay-window boundary at", self.boundary_at),
            ("report ClockRegression", self.report_regression),
            ("reserve replay", self.reserve_replayed),
            ("conflict outcome", self.conflict_outcome),
        ] {
            assert!(count > 0, "seeded lifecycle coverage missing: {name}");
        }
    }
}

// ---------- driver ----------

fn context_of(step: &Step) -> Context {
    Context {
        fence: ExecutionFence {
            owner: id(step.owner),
            generation: step.generation,
        },
        now_ms: step.now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

fn apply(
    kernel: &mut Kernel,
    model: &mut Model,
    ctx: Context,
    step: &Step,
    cov: &mut Coverage,
) -> Result<bool, String> {
    match &step.op {
        Op::Reserve {
            req,
            order,
            op,
            first,
            count,
            expiry,
            atoms,
        } => {
            cov.reserve += 1;
            let request = reserve_request(*req, *order, *op, *first, *count, *expiry, *atoms);
            let expected = model.reserve(ctx, request.clone());
            let actual = kernel.reserve(ctx, request);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            if let Ok(applied) = &expected.result
                && applied.replayed
            {
                cov.reserve_replayed += 1;
            }
            Ok(expected.changed)
        }
        Op::Send(n) => {
            cov.send += 1;
            let order_id = id(*n);
            let expected = model.mark_payment_unknown(ctx, order_id);
            let actual = kernel.mark_payment_unknown(ctx, order_id);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            if expected.result == Err(KernelError::InvalidTransition)
                && model.terminated_orders.contains_key(&order_id)
            {
                cov.send_after_terminate += 1;
            }
            Ok(expected.changed)
        }
        Op::Expire(n) => {
            cov.expire += 1;
            let expected = model.expire(ctx, id(*n));
            let actual = kernel.expire(ctx, id(*n));
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            Ok(expected.changed)
        }
        Op::Capture { op, event, atoms } => {
            cov.capture += 1;
            let observation = capture_observation(*op, *event, *atoms);
            let expected = model.observe_capture(ctx, observation.clone());
            let actual = kernel.observe_capture(ctx, observation);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            match expected.result {
                Ok(ObservationOutcome::Conflict) => cov.conflict_outcome += 1,
                Err(KernelError::Capacity) if expected.changed => {
                    cov.conflict_capacity_mutated += 1;
                }
                _ => {}
            }
            Ok(expected.changed)
        }
        Op::Terminate {
            decision,
            order,
            variant,
        } => {
            cov.terminate += 1;
            let mut request = match variant {
                // Prefer a stored decision so the replay/conflict branches are
                // exercised deterministically once a termination exists.
                TermVariant::SameAsStored | TermVariant::Mutated => model
                    .terminations
                    .get(&id(*decision))
                    .or_else(|| model.terminations.values().next())
                    .map(|record| record.request)
                    .unwrap_or_else(|| terminate_request(model, *decision, *order)),
                // Prefer an already-terminated order and a fresh decision so
                // the AlreadyTerminated check fires deterministically.
                TermVariant::Again => {
                    let order_id = model.pick_terminated(*order).unwrap_or(id(*order));
                    terminate_request_with(model, model.free_decision(*decision), order_id)
                }
                // Prefer a terminatable order and a fresh decision so the
                // request reaches the predicate checks it is built for.
                TermVariant::Stale | TermVariant::FalseCondition(_) | TermVariant::Fresh => {
                    let order_id = model.pick_terminatable(*order).unwrap_or(id(*order));
                    terminate_request_with(model, model.free_decision(*decision), order_id)
                }
                TermVariant::Automatic => terminate_request(model, *decision, *order),
            };
            let order_id = request.order_id;
            match variant {
                TermVariant::Mutated => {
                    request.rule_hash = Hash32::from_bytes([0xEE; 32]);
                }
                TermVariant::Stale => match model.first_snapshot.get(&order_id) {
                    Some(&earlier) if earlier != request.evaluated => {
                        request.evaluated = earlier;
                    }
                    _ => {
                        request.evaluated.observations =
                            request.evaluated.observations.saturating_add(1);
                    }
                },
                TermVariant::Automatic => {
                    request.authority.actor = ActorKind::Automatic;
                }
                TermVariant::FalseCondition(index) => {
                    let mut holds = [true; 5];
                    holds[*index] = false;
                    request.evaluation = closure(holds);
                }
                _ => {}
            }
            let expected = model.terminate(ctx, request);
            let actual = kernel.terminate(ctx, request);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            match &expected.result {
                Ok(applied) if applied.replayed => cov.term_replayed += 1,
                Ok(_) => cov.term_applied += 1,
                Err(KernelError::AlreadyTerminated) => cov.term_already += 1,
                Err(KernelError::StaleEvaluation) => cov.term_stale += 1,
                Err(KernelError::ConditionNotSatisfied) => cov.term_condition += 1,
                Err(KernelError::AutomaticApprovalDisabled) => cov.term_automatic += 1,
                Err(KernelError::InvalidTransition) => cov.term_invalid += 1,
                Err(KernelError::CommandConflict) => cov.term_conflict += 1,
                _ => {}
            }
            Ok(expected.changed)
        }
        Op::PlaceHold {
            hold,
            order,
            kind,
            by,
            mode,
        } => {
            cov.place_hold += 1;
            // Resolve the hint so each hold branch is hit deterministically
            // once a placement exists.
            let (order_id, hold_id, hold_kind, placed_by) = match mode {
                HoldMode::Replay => match model.pick_held(*order) {
                    Some((held_order, existing)) => {
                        (held_order, existing.id, existing.kind, existing.placed_by)
                    }
                    None => (id(*order), id(*hold), *kind, id(*by)),
                },
                HoldMode::Second => match model.pick_held(*order) {
                    Some((held_order, _)) => (held_order, model.free_hold(*hold), *kind, id(*by)),
                    None => (id(*order), id(*hold), *kind, id(*by)),
                },
                HoldMode::Conflict => match model.pick_held(*order) {
                    Some((_, existing)) => {
                        let kind = match existing.kind {
                            HoldKind::Legal => HoldKind::Dispute,
                            _ => HoldKind::Legal,
                        };
                        (id(*order), existing.id, kind, id(*by))
                    }
                    None => (id(*order), id(*hold), *kind, id(*by)),
                },
                HoldMode::Fresh => (id(*order), id(*hold), *kind, id(*by)),
            };
            let expected = model.place_hold(ctx, order_id, hold_id, hold_kind, placed_by);
            let actual = kernel.place_hold(ctx, order_id, hold_id, hold_kind, placed_by);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            match &expected.result {
                Ok(applied) if applied.replayed => cov.hold_replayed += 1,
                Ok(_) => cov.hold_placed += 1,
                Err(KernelError::HoldExists) => cov.hold_exists += 1,
                Err(KernelError::CommandConflict) => cov.hold_conflict += 1,
                _ => {}
            }
            Ok(expected.changed)
        }
        Op::ClearHold { hold, by } => {
            cov.clear_hold += 1;
            let expected = model.clear_hold(ctx, id(*hold), id(*by));
            let actual = kernel.clear_hold(ctx, id(*hold), id(*by));
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            match &expected.result {
                Ok(_) => cov.clear_ok += 1,
                Err(KernelError::UnknownHold) => cov.clear_unknown += 1,
                _ => {}
            }
            Ok(expected.changed)
        }
        Op::Report { order, at, tight } => {
            cov.report += 1;
            let reclaim = policy(*tight);
            // For boundary selectors prefer an order whose boundary is still
            // ahead of ordered time, so the read lands exactly on it.
            let order_id = match at {
                NowSel::ReplayMinus(_) => model
                    .pick_where(*order, |model, oid| {
                        model.first_result_ms(oid).is_some_and(|first| {
                            first
                                .saturating_add(reclaim.retry_support_window_ms)
                                .saturating_sub(1)
                                >= model.now_ms
                        })
                    })
                    .unwrap_or(id(*order)),
                NowSel::ReplayAt(_) => model
                    .pick_where(*order, |model, oid| {
                        model.first_result_ms(oid).is_some_and(|first| {
                            first.saturating_add(reclaim.retry_support_window_ms) >= model.now_ms
                        })
                    })
                    .unwrap_or(id(*order)),
                NowSel::Residency(_) => model
                    .pick_where(*order, |model, oid| model.terminated_at_ms(oid).is_some())
                    .unwrap_or(id(*order)),
                _ => id(*order),
            };
            let now_ms = model.resolve_now(*at, order_id, step.now_ms, &reclaim);
            let expected = model.report(now_ms, order_id, &reclaim);
            let actual = kernel.reclaim_report(now_ms, order_id, &reclaim);
            if actual != expected {
                return Err(format!("model={expected:?} kernel={actual:?}"));
            }
            if let Ok(report) = &expected {
                if let Some(first) = model.first_result_ms(order_id) {
                    let end = first.saturating_add(reclaim.retry_support_window_ms);
                    if now_ms == end.saturating_sub(1)
                        && report.blockers.contains(&Blocker::ReplayWindow)
                    {
                        cov.boundary_below += 1;
                    }
                    if now_ms == end && !report.blockers.contains(&Blocker::ReplayWindow) {
                        cov.boundary_at += 1;
                    }
                }
                if report.implicit_hold.contains(&ImplicitHold::ReturnRequired) {
                    cov.implicit_return += 1;
                }
                if report.implicit_hold.contains(&ImplicitHold::OpenConflict) {
                    cov.implicit_conflict += 1;
                }
            }
            if expected == Err(KernelError::ClockRegression) {
                cov.report_regression += 1;
            }
            Ok(false)
        }
        Op::Batch { order, at, tight } => {
            cov.batch += 1;
            let reclaim = policy(*tight);
            let now_ms = model.resolve_now(*at, id(*order), step.now_ms, &reclaim);
            let expected = model.batch(now_ms, &reclaim);
            let actual = kernel.reclaim_reports(now_ms, &reclaim);
            if actual != expected {
                return Err(format!("model={expected:?} kernel={actual:?}"));
            }
            if expected == Err(KernelError::ClockRegression) {
                cov.report_regression += 1;
            }
            let _ = order;
            Ok(false)
        }
        Op::Owner { owner, generation } => {
            cov.owner_or_cancel += 1;
            let next = ExecutionFence {
                owner: id(*owner),
                generation: *generation,
            };
            let expected = model.replace_owner(ctx, next);
            let actual = kernel.replace_owner(ctx, next);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            Ok(expected.changed)
        }
        Op::Cancel(epoch) => {
            cov.owner_or_cancel += 1;
            let expected = model.cancel_scope(ctx, *epoch);
            let actual = kernel.cancel_scope(ctx, *epoch);
            if actual != expected.result {
                return Err(format!("model={:?} kernel={actual:?}", expected.result));
            }
            Ok(expected.changed)
        }
    }
}

fn execute(steps: &[Step]) -> Result<Coverage, String> {
    let mut kernel = engine();
    let mut model = Model::new();
    let mut cov = Coverage::default();
    let default_policy = policy(false);
    for (index, step) in steps.iter().enumerate() {
        let ctx = context_of(step);
        let before = kernel.clone();
        let changed = apply(&mut kernel, &mut model, ctx, step, &mut cov)
            .map_err(|detail| format!("step {index} result\n step={step:?}\n{detail}"))?;
        if (kernel == before) == changed {
            return Err(format!(
                "step {index} mutation\n step={step:?}\n kernel_changed={} expected_changed={changed}",
                kernel != before
            ));
        }
        let kernel_rows = kernel_view(&kernel);
        let model_rows = model.view();
        if kernel_rows != model_rows {
            return Err(format!(
                "step {index} view\n step={step:?}\n model={model_rows}\n kernel={kernel_rows}"
            ));
        }
        // `now` and `now - 1` probes pin the ordered clock exactly: a report at
        // `now` rejects iff kernel time is ahead, one at `now - 1` accepts iff
        // kernel time is behind.
        for probe in [model.now_ms, model.now_ms.saturating_sub(1)] {
            for n in 1_u8..=8 {
                let order_id = id(n);
                let actual = kernel.reclaim_report(probe, order_id, &default_policy);
                let expected = model.report(probe, order_id, &default_policy);
                if actual != expected {
                    return Err(format!(
                        "step {index} report order={order_id:?} at={probe}\n step={step:?}\n model={expected:?}\n kernel={actual:?}"
                    ));
                }
            }
            let actual = kernel.reclaim_reports(probe, &default_policy);
            let expected = model.batch(probe, &default_policy);
            if actual != expected {
                return Err(format!(
                    "step {index} batch at={probe}\n step={step:?}\n model={expected:?}\n kernel={actual:?}"
                ));
            }
        }
        for n in 1_u8..=8 {
            if let Ok(report) = model.report(model.now_ms, id(n), &default_policy) {
                if report.implicit_hold.contains(&ImplicitHold::ReturnRequired) {
                    cov.implicit_return += 1;
                }
                if report.implicit_hold.contains(&ImplicitHold::OpenConflict) {
                    cov.implicit_conflict += 1;
                }
            }
        }
    }
    Ok(cov)
}

fn shrink(steps: &[Step]) -> Vec<Step> {
    let mut current = steps.to_vec();
    let mut changed = true;
    while changed {
        changed = false;
        let mut index = 0;
        while index < current.len() {
            let mut trial = current.clone();
            trial.remove(index);
            if execute(&trial).is_err() {
                current = trial;
                changed = true;
            } else {
                index += 1;
            }
        }
    }
    current
}

#[test]
fn seeded_lifecycle_histories_match_oracle() {
    const SEEDS: [u64; 8] = [1, 2, 7, 11, 42, 99, 0x51A6_E25B, 0x00C0_FFEE];
    const STEPS: usize = 128;
    let mut totals = Coverage::default();
    for seed in SEEDS {
        let steps = history(seed, STEPS);
        match execute(&steps) {
            Ok(cov) => totals.merge(&cov),
            Err(detail) => {
                let shrunk = shrink(&steps);
                panic!(
                    "lifecycle model mismatch seed={seed}\n{detail}\nshrunk {} steps: {shrunk:#?}",
                    shrunk.len()
                );
            }
        }
    }
    eprintln!("lifecycle_model coverage: {totals:?}");
    totals.assert_covered();
}
