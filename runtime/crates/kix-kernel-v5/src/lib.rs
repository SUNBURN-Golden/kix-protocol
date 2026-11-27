#![forbid(unsafe_code)]
#![deny(
    clippy::disallowed_types,
    clippy::disallowed_methods,
    clippy::float_arithmetic
)]
//! KIX kernel semantics version 5. NOT a durable service.
//!
//! This crate forks the locked v4 transition logic and adds an in-memory
//! operational-termination record, a private conflict index, in-memory
//! legal/dispute/erasure hold references, and a read-only reclamation report.
//! It does not release observation slots, delete evidence, or clear review.
//! Those transitions stay stopped on open inputs (owner decision 2026-10-13).
//!
//! Inputs must come from an authenticated, ordered adapter. This crate does not
//! authenticate principals, registry claims, policies, provider observations,
//! or closure evidence. It performs no I/O, clock reads, random generation,
//! replication, or ACKs. An in-memory termination is not a durable approval.
//! The future durable driver must log validated commands before applying them
//! and must not turn these in-memory results into durability claims.

use std::collections::{BTreeMap, BTreeSet};

use kix_types::{AssetAmount, Hash32, KixId};

// V5 keeps the v4 quarantine rule: bound operations are quarantined
// independently of evidence capacity, and unbound identities block future
// binding only while their conflict evidence is retained. Version 4 inputs
// are rejected and must not be silently replayed under these semantics.
pub const SEMANTICS_VERSION: u16 = 5;
pub const MAX_SEATS: u16 = 4_096;
pub const MAX_BUNDLE: u16 = 64;

pub const HOUR_MS: u64 = 3_600_000;
pub const DAY_MS: u64 = 24 * HOUR_MS;

// Reclamation-report defaults set by the 2026-10-13 owner-delegate decision for
// this node. They are kernel defaults a caller may override through
// `ReclaimPolicy`; they are not a legal period, a provider fact, or a ratified
// Astra retention policy (I09 and I10 stay open). The 15-day retry-support
// default is a KIX value chosen by the owner delegate. It is not derived from
// the provider's public idempotency-key period and must not be read as one.
/// Retry support: from the command's first result.
pub const DEFAULT_RETRY_SUPPORT_WINDOW_MS: u64 = 15 * DAY_MS;
/// Memory residency: from the terminal state (the operational termination).
pub const DEFAULT_MEMORY_RESIDENCY_MS: u64 = 72 * HOUR_MS;
/// Memory residency cap, counted in terminated-order records.
pub const DEFAULT_MEMORY_RESIDENCY_CAP_RECORDS: usize = 10_000;
/// Reconciliation floor for terminated-order records: 5 years. Five calendar
/// years never exceed 1,827 days, so the floor is counted as 1,827 days and
/// never elapses early. The legal period is pending I10.
pub const DEFAULT_RETENTION_FLOOR_MS: u64 = 1_827 * DAY_MS;
/// Report SLO: synchronous, within this many milliseconds for this many records.
pub const REPORT_SLO_MS: u64 = 50;
pub const REPORT_SLO_RECORDS: usize = 10_000;

/// Stable business scope and caller identity. NEVER includes the owner fence.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct CommandId {
    pub scope: KixId,
    pub principal: KixId,
    pub request: KixId,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExecutionFence {
    pub owner: KixId,
    pub generation: u64,
}

/// Supplied by an ordered driver, not independently read from replica clocks.
/// Every accepted state command advances logical time, including an expiry
/// check that releases nothing and a duplicate observation. A conflict returning
/// Capacity still quarantines bound operations and advances time; its new
/// evidence and unbound identity are not retained. Other errors change no state.
/// A reservation lookup is read-only:
/// it checks scope,
/// semantics and payload equality, but neither checks nor advances time/fence.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Context {
    pub fence: ExecutionFence,
    pub now_ms: u64,
    pub semantics_version: u16,
}

/// The adapter maps bounded external identifiers to these persistent aliases.
/// This is a single capture operation, not an entire multi-capture payment.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct ProviderOperation {
    pub provider: KixId,
    pub account: KixId,
    pub operation: KixId,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Selection {
    Seats { first: u16, count: u16 },
    GeneralAdmission { count: u32 },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Reserve {
    pub id: CommandId,
    pub order_id: KixId,
    pub expected_business_epoch: u64,
    pub selection: Selection,
    pub amount: AssetAmount,
    pub quote_hash: Hash32,
    pub policy_hash: Hash32,
    pub expires_at_ms: u64,
    pub payment: ProviderOperation,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Rejection {
    InvalidRequest,
    BusinessFenced,
    Unavailable,
    OrderExists,
    OperationAlreadyBound,
    OperationQuarantined,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReserveOutcome {
    Held(KixId),
    Rejected(Rejection),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AppliedReservation {
    /// Original result. Current order state must be queried separately.
    pub original: ReserveOutcome,
    pub replayed: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KernelError {
    InvalidConfiguration,
    UnsupportedSemantics,
    ExecutionFenced,
    ClockRegression,
    WrongScope,
    CommandConflict,
    Capacity,
    UnknownOrder,
    InvalidTransition,
    UnknownOperation,
    /// At least one caller-supplied C1–C5 flag is false. The kernel does not
    /// decide provider facts.
    ConditionNotSatisfied,
    /// `Terminate::evaluated` is not the current operation snapshot.
    StaleEvaluation,
    /// Automatic approval scope is 0. No limit number is stored here.
    AutomaticApprovalDisabled,
    /// This operation already has one termination under a different decision.
    AlreadyTerminated,
    /// The order already carries a different hold reference.
    HoldExists,
    /// No hold with this identifier is placed.
    UnknownHold,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderState {
    Held,
    PaymentUnknown,
    PaymentConfirmed,
    Expired,
    ReturnRequired,
    Review,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Order {
    pub request: Reserve,
    /// Stable external intent identity, created in the reservation transition.
    pub submitted_under: ExecutionFence,
    pub state: OrderState,
    pub inventory_owned: bool,
    pub captured: Option<AssetAmount>,
    /// Sticky quarantine: no new external execution may be authorized while set.
    /// Historical observations remain admissible. A stored result or previously
    /// confirmed state alone does not authorize downstream rights or payments.
    pub review_required: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObservationOutcome {
    PaymentConfirmed,
    ReturnRequired,
    Review,
    DuplicateEffect,
    Conflict,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CaptureObservation {
    pub event_id: KixId,
    pub operation: ProviderOperation,
    pub amount: AssetAmount,
    pub evidence_hash: Hash32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Limits {
    pub commands: usize,
    pub orders: usize,
    pub observations: usize,
}

/// Names of the five caller-supplied closure conditions. Index 0 is C1.
/// The kernel stores the supplied flags and does not evaluate provider facts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Condition {
    C1 = 0,
    C2 = 1,
    C3 = 2,
    C4 = 3,
    C5 = 4,
}

impl Condition {
    pub const ALL: [Condition; 5] = [
        Condition::C1,
        Condition::C2,
        Condition::C3,
        Condition::C4,
        Condition::C5,
    ];

    pub const fn index(self) -> usize {
        self as usize
    }
}

/// One caller-supplied condition result. `evidence_hash` is recorded, not checked.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ConditionEvidence {
    pub holds: bool,
    pub evidence_hash: Hash32,
}

/// `c[0]` is C1 through `c[4]` is C5.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ClosureEvaluation {
    pub c: [ConditionEvidence; 5],
}

/// Evidence-changed test for one termination attempt.
///
/// `observations` is the kernel's stored observation count and
/// `retained_conflicts` is the retained-conflict count. Any newly retained
/// evidence changes every snapshot. STATE_LIFECYCLE §5.4.7 requires a changed
/// evaluation once evidence changes and does not define these fields; the
/// kernel-wide counts are a characterization, recorded in the validation note.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OperationSnapshot {
    pub state: OrderState,
    pub captured: Option<AssetAmount>,
    pub review_required: bool,
    pub reserved_slot: bool,
    pub observations: usize,
    pub retained_conflicts: usize,
}

/// Recorded actor. The kernel does not authenticate `principal`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ActorKind {
    Human,
    Automatic,
}

/// Recorded authority. Not a credential check and not a durable grant.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Authority {
    pub authority_id: KixId,
    pub generation: u64,
    pub actor: ActorKind,
    pub principal: KixId,
}

/// In-memory operational termination request. Not a wire or catalogue command.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Terminate {
    pub decision_id: KixId,
    pub order_id: KixId,
    pub evaluated: OperationSnapshot,
    pub evaluation: ClosureEvaluation,
    pub authority: Authority,
    pub rule_hash: Hash32,
}

/// Applied in-memory record. `applied_at_ms` is the caller's ordered time.
/// This is not the durable approval record required by STATE_LIFECYCLE §5.4.7.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Termination {
    pub request: Terminate,
    pub applied_at_ms: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AppliedTermination {
    pub original: Termination,
    pub replayed: bool,
}

/// Kind of an in-memory hold reference (owner decision, I10 shape).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HoldKind {
    Legal,
    Dispute,
    Erasure,
}

/// One hold reference on an order. Any hold makes the order ineligible. A hold
/// never expires on its own; only an explicit `clear_hold` removes it.
/// `placed_by` is recorded, never authenticated.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HoldRef {
    pub id: KixId,
    pub kind: HoldKind,
    pub placed_at_ms: u64,
    pub placed_by: KixId,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AppliedHold {
    /// Original placement. A replay does not move `placed_at_ms`.
    pub original: HoldRef,
    pub replayed: bool,
}

/// Result of `clear_hold`. Not stored: the ordered driver must log it. A
/// delayed duplicate placement after clearing re-places the hold (fails closed).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ClearedHold {
    pub hold: HoldRef,
    pub order_id: KixId,
    pub cleared_by: KixId,
    pub cleared_at_ms: u64,
}

/// Reclamation parameters. `Default` is the owner-delegate kernel default of
/// 2026-10-13; a caller may override each field. Nothing here deletes anything.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReclaimPolicy {
    /// I09 retry support, from the command's first result.
    pub retry_support_window_ms: u64,
    /// I09 memory residency, from the terminal state.
    pub memory_residency_ms: u64,
    /// I09 memory residency cap in terminated-order records. Only the batch
    /// report reads it, as `over_residency_cap`; no eviction exists.
    pub memory_residency_cap_records: usize,
    /// I09 reconciliation floor for terminated-order records. The legal period
    /// is pending I10.
    pub retention_floor_ms: u64,
}

impl Default for ReclaimPolicy {
    fn default() -> Self {
        Self {
            retry_support_window_ms: DEFAULT_RETRY_SUPPORT_WINDOW_MS,
            memory_residency_ms: DEFAULT_MEMORY_RESIDENCY_MS,
            memory_residency_cap_records: DEFAULT_MEMORY_RESIDENCY_CAP_RECORDS,
            retention_floor_ms: DEFAULT_RETENTION_FLOOR_MS,
        }
    }
}

/// References that block state-changing reclamation, in the fixed report order
/// (derived `Ord` follows declaration order). The report never deletes.
/// `I09`, `I10` and `I13` are always listed last: those input rows are open, so
/// no report can say an order is eligible.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Blocker {
    /// No operational termination exists for the order.
    ActiveOp,
    /// The operation's observation slot is still reserved.
    ReservedSlot,
    ReviewRequired,
    /// Retained conflict evidence names the candidate's operation identity. It
    /// fences binding of that identity independently of the order.
    UnboundFence,
    /// The order is `ReturnRequired`.
    ReturnObligation,
    /// The retry-support window from the first result has not elapsed.
    ReplayWindow,
    /// An explicit hold is placed, or the order is treated as held.
    Hold,
    /// Retry-support, residency and retention values are unratified defaults.
    I09,
    /// Legal and dispute retention is unassessed. UNDETERMINED · legal/privacy.
    I10,
    /// Archive custody and budget are undefined. Operations/security.
    I13,
}

/// Why an order without an explicit hold is still treated as held.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ImplicitHold {
    ReturnRequired,
    /// The operation is quarantined or has retained conflict evidence.
    OpenConflict,
}

/// Read-only report for one order. `blockers` always ends with I09, I10, I13,
/// so this value cannot say the order is eligible to delete.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReclaimReport {
    pub order_id: KixId,
    /// Applied time of the operational termination, if any.
    pub terminated_at_ms: Option<u64>,
    pub blockers: Vec<Blocker>,
    pub hold: Option<HoldRef>,
    pub implicit_hold: Vec<ImplicitHold>,
    /// Command first result plus the retry-support window.
    pub replay_window_ends_at_ms: u64,
    /// Termination plus the memory-residency window. `None` before termination.
    pub memory_residency_ends_at_ms: Option<u64>,
    /// Termination plus the retention floor. Informational: it is not a blocker
    /// of its own, because I09, I10 and I13 always remain.
    pub retention_floor_ends_at_ms: Option<u64>,
}

/// Reports for every terminated order, sorted by `(terminated_at, order_id)`
/// ascending. Internal only: no wire, OpenAPI or catalogue name.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReclaimBatch {
    pub now_ms: u64,
    pub terminated_records: usize,
    /// `terminated_records` exceeds the policy residency cap. No eviction exists.
    pub over_residency_cap: bool,
    pub reports: Vec<ReclaimReport>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Inventory {
    Seats {
        /// Each half-open interval is an actual contiguous segment.
        segments: Vec<(u16, u16)>,
        occupied: Vec<u64>,
    },
    GeneralAdmission {
        capacity: u32,
        remaining: u32,
    },
}

impl Inventory {
    pub fn seats(segment_lengths: &[u16]) -> Result<Self, KernelError> {
        if segment_lengths.is_empty() || segment_lengths.len() > usize::from(MAX_SEATS) {
            return Err(KernelError::InvalidConfiguration);
        }
        let mut end = 0_u16;
        let mut segments = Vec::with_capacity(segment_lengths.len());
        for &length in segment_lengths {
            let next = end
                .checked_add(length)
                .ok_or(KernelError::InvalidConfiguration)?;
            if length == 0 || next > MAX_SEATS {
                return Err(KernelError::InvalidConfiguration);
            }
            segments.push((end, next));
            end = next;
        }
        Ok(Self::Seats {
            segments,
            occupied: vec![0; usize::from(end).div_ceil(64)],
        })
    }

    pub fn general_admission(capacity: u32) -> Result<Self, KernelError> {
        if capacity == 0 {
            return Err(KernelError::InvalidConfiguration);
        }
        Ok(Self::GeneralAdmission {
            capacity,
            remaining: capacity,
        })
    }

    fn check(&self, selection: Selection) -> Result<(), Rejection> {
        match (self, selection) {
            (Self::Seats { segments, occupied }, Selection::Seats { first, count }) => {
                let end = first.checked_add(count).ok_or(Rejection::InvalidRequest)?;
                if count == 0
                    || count > MAX_BUNDLE
                    || !segments.iter().any(|&(lo, hi)| first >= lo && end <= hi)
                {
                    return Err(Rejection::InvalidRequest);
                }
                if (first..end)
                    .any(|seat| occupied[usize::from(seat) / 64] & (1_u64 << (seat % 64)) != 0)
                {
                    return Err(Rejection::Unavailable);
                }
                Ok(())
            }
            (Self::GeneralAdmission { remaining, .. }, Selection::GeneralAdmission { count }) => {
                if count == 0 {
                    Err(Rejection::InvalidRequest)
                } else if count > *remaining {
                    Err(Rejection::Unavailable)
                } else {
                    Ok(())
                }
            }
            _ => Err(Rejection::InvalidRequest),
        }
    }

    /// Only called with a previously checked selection from an owned order.
    fn adjust(&mut self, selection: Selection, acquire: bool) {
        match (self, selection) {
            (Self::Seats { occupied, .. }, Selection::Seats { first, count }) => {
                for seat in first..first + count {
                    let word = &mut occupied[usize::from(seat) / 64];
                    let mask = 1_u64 << (seat % 64);
                    if acquire {
                        *word |= mask;
                    } else {
                        *word &= !mask;
                    }
                }
            }
            (Self::GeneralAdmission { remaining, .. }, Selection::GeneralAdmission { count }) => {
                if acquire {
                    *remaining -= count;
                } else {
                    *remaining += count;
                }
            }
            _ => unreachable!("validated inventory selection"),
        }
    }

    pub fn remaining(&self) -> u32 {
        match self {
            Self::Seats { segments, occupied } => {
                let total: u32 = segments.iter().map(|&(lo, hi)| u32::from(hi - lo)).sum();
                total - occupied.iter().map(|word| word.count_ones()).sum::<u32>()
            }
            Self::GeneralAdmission { remaining, .. } => *remaining,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct CommandRecord {
    request: Reserve,
    result: ReserveOutcome,
    // Ordered time of the first result. Read only by the reclamation report.
    applied_at_ms: u64,
}

type EventKey = (KixId, KixId, KixId);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Kernel {
    scope: KixId,
    fence: ExecutionFence,
    business_epoch: u64,
    cancelled: bool,
    now_ms: u64,
    inventory: Inventory,
    limits: Limits,
    commands: BTreeMap<CommandId, CommandRecord>,
    orders: BTreeMap<KixId, Order>,
    operations: BTreeMap<ProviderOperation, KixId>,
    // Only bound operations: this is a subset of operations, hence bounded by
    // orders. Unbound identities are checked against retained conflicts at
    // reservation time; rejected evidence never grows this set.
    quarantined_operations: BTreeSet<ProviderOperation>,
    observations: BTreeMap<EventKey, (CaptureObservation, ObservationOutcome)>,
    conflicts: Vec<CaptureObservation>,
    // Same membership as `conflicts`, keyed by operation. Not a public layout.
    // Reclaim and release do not exist, so this index is not updated for them.
    conflict_index: BTreeMap<ProviderOperation, Vec<usize>>,
    // One first-capture slot per operation authorized for external sending.
    // Other observations/conflicts cannot consume this operation's reservation.
    reserved_observations: BTreeSet<ProviderOperation>,
    // At most one termination per bound operation. Keyed by decision for replay.
    // In-memory only: not a durable approval and not a send-log.
    terminations: BTreeMap<KixId, Termination>,
    terminated_orders: BTreeMap<KixId, KixId>,
    // `(applied_at_ms, order_id)` of every termination, for the sorted report.
    terminated_index: BTreeSet<(u64, KixId)>,
    // At most one hold per order, and hold identifiers are unique while placed.
    // Bounded by orders. In memory only, like every other field here.
    holds: BTreeMap<KixId, HoldRef>,
    hold_orders: BTreeMap<KixId, KixId>,
}

impl Kernel {
    pub fn new(
        scope: KixId,
        fence: ExecutionFence,
        business_epoch: u64,
        inventory: Inventory,
        limits: Limits,
    ) -> Result<Self, KernelError> {
        if fence.generation == 0
            || business_epoch == 0
            || limits.commands == 0
            || limits.orders == 0
            || limits.observations == 0
        {
            return Err(KernelError::InvalidConfiguration);
        }
        // Do not accept caller-constructed bitmap or capacity inconsistencies.
        match &inventory {
            Inventory::Seats { segments, occupied } => {
                let lengths: Vec<u16> = segments
                    .iter()
                    .map(|&(lo, hi)| hi.saturating_sub(lo))
                    .collect();
                if Inventory::seats(&lengths)? != inventory || occupied.iter().any(|&v| v != 0) {
                    return Err(KernelError::InvalidConfiguration);
                }
            }
            Inventory::GeneralAdmission {
                capacity,
                remaining,
            } => {
                if *capacity == 0 || capacity != remaining {
                    return Err(KernelError::InvalidConfiguration);
                }
            }
        }
        Ok(Self {
            scope,
            fence,
            business_epoch,
            cancelled: false,
            now_ms: 0,
            inventory,
            limits,
            commands: BTreeMap::new(),
            orders: BTreeMap::new(),
            operations: BTreeMap::new(),
            quarantined_operations: BTreeSet::new(),
            observations: BTreeMap::new(),
            conflicts: Vec::new(),
            conflict_index: BTreeMap::new(),
            reserved_observations: BTreeSet::new(),
            terminations: BTreeMap::new(),
            terminated_orders: BTreeMap::new(),
            terminated_index: BTreeSet::new(),
            holds: BTreeMap::new(),
            hold_orders: BTreeMap::new(),
        })
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

    pub fn reserve(
        &mut self,
        ctx: Context,
        request: Reserve,
    ) -> Result<AppliedReservation, KernelError> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Err(KernelError::UnsupportedSemantics);
        }
        if request.id.scope != self.scope {
            return Err(KernelError::WrongScope);
        }
        // Full typed payload equality is collision-free; wire fingerprints are
        // a future adapter optimization, never part of the command identity.
        if let Some(record) = self.commands.get(&request.id) {
            if record.request != request {
                return Err(KernelError::CommandConflict);
            }
            return Ok(AppliedReservation {
                original: record.result,
                replayed: true,
            });
        }
        self.context(ctx)?;
        if self.commands.len() >= self.limits.commands || self.orders.len() >= self.limits.orders {
            return Err(KernelError::Capacity);
        }
        let rejection = if self.cancelled || request.expected_business_epoch != self.business_epoch
        {
            Some(Rejection::BusinessFenced)
        } else if request.expires_at_ms <= ctx.now_ms || request.amount.atoms() == 0 {
            Some(Rejection::InvalidRequest)
        } else if self.orders.contains_key(&request.order_id) {
            Some(Rejection::OrderExists)
        } else if self.quarantined_operations.contains(&request.payment)
            || self.operation_has_retained_conflict(request.payment)
        {
            // Retained evidence blocks future binding of an unbound identity.
            // The inbox must reconcile evidence the kernel could not retain.
            Some(Rejection::OperationQuarantined)
        } else if self.operations.contains_key(&request.payment) {
            Some(Rejection::OperationAlreadyBound)
        } else {
            self.inventory.check(request.selection).err()
        };
        // Every fallible validation precedes all mutation. No whole-state clone.
        let result = if let Some(reason) = rejection {
            ReserveOutcome::Rejected(reason)
        } else {
            self.inventory.adjust(request.selection, true);
            self.operations.insert(request.payment, request.order_id);
            self.orders.insert(
                request.order_id,
                Order {
                    request: request.clone(),
                    submitted_under: ctx.fence,
                    state: OrderState::Held,
                    inventory_owned: true,
                    captured: None,
                    review_required: false,
                },
            );
            ReserveOutcome::Held(request.order_id)
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
        Ok(AppliedReservation {
            original: result,
            replayed: false,
        })
    }

    /// Must be committed before an adapter sends the external request. UNKNOWN
    /// is not failure, and expiry alone must not release this reservation.
    /// Reviewed orders cannot authorize a send, including a retry of UNKNOWN;
    /// observations of a request already sent must still be recorded separately.
    /// Reserve one observation slot before first send authorization. Retrying
    /// UNKNOWN reuses it. If no slot is available, leave the order unchanged.
    pub fn mark_payment_unknown(
        &mut self,
        ctx: Context,
        order_id: KixId,
    ) -> Result<(), KernelError> {
        self.context(ctx)?;
        let order = self
            .orders
            .get(&order_id)
            .ok_or(KernelError::UnknownOrder)?;
        // The only effect of termination is to refuse another send. The order
        // state, slot, inventory, review flag and evidence stay as they are.
        if self.terminated_orders.contains_key(&order_id) {
            return Err(KernelError::InvalidTransition);
        }
        if order.review_required
            || !matches!(order.state, OrderState::Held | OrderState::PaymentUnknown)
        {
            return Err(KernelError::InvalidTransition);
        }
        if self.cancelled || ctx.now_ms >= order.request.expires_at_ms {
            return Err(KernelError::InvalidTransition);
        }
        let operation = order.request.payment;
        if !self.reserved_observations.contains(&operation) {
            if self.observation_slots_used() >= self.limits.observations {
                return Err(KernelError::Capacity);
            }
            self.reserved_observations.insert(operation);
        }
        self.orders.get_mut(&order_id).unwrap().state = OrderState::PaymentUnknown;
        self.now_ms = ctx.now_ms;
        Ok(())
    }

    pub fn expire(&mut self, ctx: Context, order_id: KixId) -> Result<bool, KernelError> {
        self.context(ctx)?;
        let order = self
            .orders
            .get_mut(&order_id)
            .ok_or(KernelError::UnknownOrder)?;
        // A successful expiry check is an ordered command even before expiry.
        self.now_ms = ctx.now_ms;
        if ctx.now_ms < order.request.expires_at_ms {
            return Ok(false);
        }
        if order.state == OrderState::Held && order.inventory_owned {
            self.inventory.adjust(order.request.selection, false);
            order.inventory_owned = false;
            order.state = OrderState::Expired;
            return Ok(true);
        }
        Ok(false)
    }

    /// Local state-model fence only: NOT a cluster-wide cancellation barrier.
    pub fn cancel_scope(&mut self, ctx: Context, next_epoch: u64) -> Result<(), KernelError> {
        self.context(ctx)?;
        if next_epoch <= self.business_epoch {
            return Err(KernelError::InvalidTransition);
        }
        self.business_epoch = next_epoch;
        self.cancelled = true;
        self.now_ms = ctx.now_ms;
        Ok(())
    }

    /// Models ordered ownership replacement. Actual distributed handoff,
    /// membership, old-writer fencing, and state transfer are NOT implemented.
    pub fn replace_owner(&mut self, ctx: Context, next: ExecutionFence) -> Result<(), KernelError> {
        self.context(ctx)?;
        if next.generation <= self.fence.generation {
            return Err(KernelError::InvalidTransition);
        }
        self.fence = next;
        self.now_ms = ctx.now_ms;
        Ok(())
    }

    /// Accept a bound historical fact under the current driver's execution fence.
    /// Does not compare the intent's old owner generation to the new owner.
    /// A return marker is NOT an authorized or executed refund.
    /// On a conflicting event, Capacity means new evidence was not retained;
    /// bound-operation quarantine and its ordered time have still been applied.
    /// Unbound identities are blocked at reserve only if the conflict is retained.
    /// Callers must not interpret this error as rollback of the safety transition.
    pub fn observe_capture(
        &mut self,
        ctx: Context,
        observation: CaptureObservation,
    ) -> Result<ObservationOutcome, KernelError> {
        self.context(ctx)?;
        let key = (
            observation.operation.provider,
            observation.operation.account,
            observation.event_id,
        );
        if let Some((original, result)) = self.observations.get(&key) {
            if original == &observation {
                self.now_ms = ctx.now_ms;
                return Ok(*result);
            }
            let affected_operations = [original.operation, observation.operation];
            // Bound-order safety takes effect even if no evidence slot is available.
            for operation in affected_operations {
                self.quarantine_bound(operation);
            }
            self.now_ms = ctx.now_ms;
            if !self.conflict_is_retained(&observation) {
                // A conflicting event is not an applied first capture and
                // therefore may not spend any operation's promised slot.
                if self.observation_slots_used() >= self.limits.observations {
                    return Err(KernelError::Capacity);
                }
                // This retained record is also the reserve-time quarantine for
                // an unbound operation. No speculative identity set is grown.
                self.retain_conflict(observation);
            }
            return Ok(ObservationOutcome::Conflict);
        }
        let has_reserved_slot = self.reserved_observations.contains(&observation.operation);
        if !has_reserved_slot && self.observation_slots_used() >= self.limits.observations {
            return Err(KernelError::Capacity);
        }
        let order_id = self
            .operations
            .get(&observation.operation)
            .ok_or(KernelError::UnknownOperation)?;
        let order = self
            .orders
            .get_mut(order_id)
            .ok_or(KernelError::UnknownOrder)?;
        let result = if let Some(captured) = order.captured {
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
                    self.inventory.adjust(order.request.selection, false);
                    order.inventory_owned = false;
                }
                order.state = OrderState::ReturnRequired;
                ObservationOutcome::ReturnRequired
            } else if order.review_required {
                // A later matching fact does not resolve earlier conflicting
                // evidence or grant permission to issue rights automatically.
                order.state = OrderState::Review;
                ObservationOutcome::Review
            } else {
                order.state = OrderState::PaymentConfirmed;
                ObservationOutcome::PaymentConfirmed
            }
        };
        // Convert the reservation into retained evidence in this same transition.
        // Cancellation, expiry and owner changes never release it beforehand.
        self.reserved_observations.remove(&observation.operation);
        self.observations.insert(key, (observation, result));
        self.now_ms = ctx.now_ms;
        Ok(result)
    }

    pub fn order(&self, id: KixId) -> Option<&Order> {
        self.orders.get(&id)
    }
    pub fn remaining(&self) -> u32 {
        self.inventory.remaining()
    }
    pub fn order_count(&self) -> usize {
        self.orders.len()
    }
    pub fn observation_count(&self) -> usize {
        self.observations.len()
    }
    pub fn reserved_observation_count(&self) -> usize {
        self.reserved_observations.len()
    }
    /// Number of quarantined bound operations; unbound evidence lives in conflicts.
    pub fn quarantined_operation_count(&self) -> usize {
        self.quarantined_operations.len()
    }
    fn quarantine_bound(&mut self, operation: ProviderOperation) {
        if let Some(order_id) = self.operations.get(&operation)
            && let Some(order) = self.orders.get_mut(order_id)
        {
            order.review_required = true;
            self.quarantined_operations.insert(operation);
        }
    }
    fn observation_slots_used(&self) -> usize {
        self.observations
            .len()
            .saturating_add(self.conflicts.len())
            .saturating_add(self.reserved_observations.len())
    }
    pub fn conflicts(&self) -> &[CaptureObservation] {
        &self.conflicts
    }

    /// Current snapshot, or `None` when the order is unknown.
    /// Counts are kernel-wide; see [`OperationSnapshot`].
    pub fn operation_snapshot(&self, order_id: KixId) -> Option<OperationSnapshot> {
        let order = self.orders.get(&order_id)?;
        Some(OperationSnapshot {
            state: order.state,
            captured: order.captured,
            review_required: order.review_required,
            reserved_slot: self.reserved_observations.contains(&order.request.payment),
            observations: self.observations.len(),
            retained_conflicts: self.conflicts.len(),
        })
    }

    pub fn termination(&self, order_id: KixId) -> Option<&Termination> {
        let decision_id = self.terminated_orders.get(&order_id)?;
        self.terminations.get(decision_id)
    }

    /// One-time in-memory operational termination.
    ///
    /// Check order matches `reserve`: version, then read-only decision replay,
    /// then fence and clock, then the remaining predicates. Errors change no
    /// state. A successful apply stores the record and advances ordered time.
    /// It does not release a slot, inventory, review, or evidence, and it does
    /// not answer that the approval was durably stored.
    pub fn terminate(
        &mut self,
        ctx: Context,
        request: Terminate,
    ) -> Result<AppliedTermination, KernelError> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Err(KernelError::UnsupportedSemantics);
        }
        if let Some(existing) = self.terminations.get(&request.decision_id) {
            if existing.request != request {
                return Err(KernelError::CommandConflict);
            }
            return Ok(AppliedTermination {
                original: *existing,
                replayed: true,
            });
        }
        self.context(ctx)?;
        if request.authority.actor == ActorKind::Automatic {
            return Err(KernelError::AutomaticApprovalDisabled);
        }
        let order = self
            .orders
            .get(&request.order_id)
            .ok_or(KernelError::UnknownOrder)?;
        if self.terminated_orders.contains_key(&request.order_id) {
            return Err(KernelError::AlreadyTerminated);
        }
        // Absence path only: PaymentUnknown, a reserved slot, no capture, and
        // no review. ReturnRequired and a known capture stay on their own paths.
        let reserved_slot = self.reserved_observations.contains(&order.request.payment);
        if order.state != OrderState::PaymentUnknown
            || order.captured.is_some()
            || order.state == OrderState::ReturnRequired
            || order.review_required
            || !reserved_slot
        {
            return Err(KernelError::InvalidTransition);
        }
        if request
            .evaluation
            .c
            .iter()
            .any(|condition| !condition.holds)
        {
            return Err(KernelError::ConditionNotSatisfied);
        }
        let snapshot = self
            .operation_snapshot(request.order_id)
            .ok_or(KernelError::UnknownOrder)?;
        if request.evaluated != snapshot {
            return Err(KernelError::StaleEvaluation);
        }
        let record = Termination {
            request,
            applied_at_ms: ctx.now_ms,
        };
        self.terminated_orders
            .insert(record.request.order_id, record.request.decision_id);
        self.terminated_index
            .insert((record.applied_at_ms, record.request.order_id));
        self.terminations.insert(record.request.decision_id, record);
        self.now_ms = ctx.now_ms;
        Ok(AppliedTermination {
            original: record,
            replayed: false,
        })
    }

    /// Places the order's one in-memory hold. Any hold makes the order
    /// ineligible for reclamation and never expires by itself. The same
    /// placement again returns the original (`replayed`) and does not move
    /// `placed_at_ms`. `placed_by` is recorded, not authenticated. This is a
    /// crate-internal call, not a wire command.
    pub fn place_hold(
        &mut self,
        ctx: Context,
        order_id: KixId,
        hold_id: KixId,
        kind: HoldKind,
        placed_by: KixId,
    ) -> Result<AppliedHold, KernelError> {
        if ctx.semantics_version != SEMANTICS_VERSION {
            return Err(KernelError::UnsupportedSemantics);
        }
        if let Some(held_order) = self.hold_orders.get(&hold_id) {
            return match self.holds.get(held_order) {
                Some(existing)
                    if *held_order == order_id
                        && existing.kind == kind
                        && existing.placed_by == placed_by =>
                {
                    Ok(AppliedHold {
                        original: *existing,
                        replayed: true,
                    })
                }
                _ => Err(KernelError::CommandConflict),
            };
        }
        self.context(ctx)?;
        if !self.orders.contains_key(&order_id) {
            return Err(KernelError::UnknownOrder);
        }
        if self.holds.contains_key(&order_id) {
            return Err(KernelError::HoldExists);
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
        Ok(AppliedHold {
            original: hold,
            replayed: false,
        })
    }

    /// Explicit clearing of a placed hold. Releases nothing else: slot, review,
    /// evidence and the report's I09, I10 and I13 entries are unchanged.
    pub fn clear_hold(
        &mut self,
        ctx: Context,
        hold_id: KixId,
        by: KixId,
    ) -> Result<ClearedHold, KernelError> {
        self.context(ctx)?;
        let order_id = *self
            .hold_orders
            .get(&hold_id)
            .ok_or(KernelError::UnknownHold)?;
        let hold = self
            .holds
            .remove(&order_id)
            .ok_or(KernelError::UnknownHold)?;
        self.hold_orders.remove(&hold_id);
        self.now_ms = ctx.now_ms;
        Ok(ClearedHold {
            hold,
            order_id,
            cleared_by: by,
            cleared_at_ms: ctx.now_ms,
        })
    }

    pub fn hold(&self, order_id: KixId) -> Option<&HoldRef> {
        self.holds.get(&order_id)
    }

    /// Lists blocking references for one order as of the caller-supplied `now_ms`.
    /// Read-only: it deletes nothing, advances no time, and cannot report
    /// eligibility, because I09, I10 and I13 are always listed. `now_ms` must
    /// not precede the kernel's ordered time.
    pub fn reclaim_report(
        &self,
        now_ms: u64,
        order_id: KixId,
        policy: &ReclaimPolicy,
    ) -> Result<ReclaimReport, KernelError> {
        if now_ms < self.now_ms {
            return Err(KernelError::ClockRegression);
        }
        let order = self
            .orders
            .get(&order_id)
            .ok_or(KernelError::UnknownOrder)?;
        Ok(self.report_for(now_ms, order_id, order, policy))
    }

    /// Reports for every terminated order, ascending by `(terminated_at,
    /// order_id)`. Computed synchronously from the termination index with
    /// logarithmic per-order lookups.
    pub fn reclaim_reports(
        &self,
        now_ms: u64,
        policy: &ReclaimPolicy,
    ) -> Result<ReclaimBatch, KernelError> {
        if now_ms < self.now_ms {
            return Err(KernelError::ClockRegression);
        }
        let reports = self
            .terminated_index
            .iter()
            .filter_map(|(_, order_id)| {
                let order = self.orders.get(order_id)?;
                Some(self.report_for(now_ms, *order_id, order, policy))
            })
            .collect();
        Ok(ReclaimBatch {
            now_ms,
            terminated_records: self.terminated_index.len(),
            over_residency_cap: self.terminated_index.len() > policy.memory_residency_cap_records,
            reports,
        })
    }

    fn report_for(
        &self,
        now_ms: u64,
        order_id: KixId,
        order: &Order,
        policy: &ReclaimPolicy,
    ) -> ReclaimReport {
        let operation = order.request.payment;
        let terminated_at_ms = self.termination(order_id).map(|t| t.applied_at_ms);
        // Every order was created by a stored command. If that record were
        // missing, start the window now so the report errs toward blocking.
        let first_result_ms = self
            .commands
            .get(&order.request.id)
            .map_or(now_ms, |record| record.applied_at_ms);
        let replay_window_ends_at_ms =
            first_result_ms.saturating_add(policy.retry_support_window_ms);
        let hold = self.holds.get(&order_id).copied();
        let retained_conflict = self.operation_has_retained_conflict(operation);
        let mut implicit_hold = Vec::new();
        if order.state == OrderState::ReturnRequired {
            implicit_hold.push(ImplicitHold::ReturnRequired);
        }
        if retained_conflict || self.quarantined_operations.contains(&operation) {
            implicit_hold.push(ImplicitHold::OpenConflict);
        }
        let mut blockers = Vec::new();
        if terminated_at_ms.is_none() {
            blockers.push(Blocker::ActiveOp);
        }
        if self.reserved_observations.contains(&operation) {
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
                .map(|at| at.saturating_add(policy.memory_residency_ms)),
            retention_floor_ends_at_ms: terminated_at_ms
                .map(|at| at.saturating_add(policy.retention_floor_ms)),
        }
    }

    fn operation_has_retained_conflict(&self, operation: ProviderOperation) -> bool {
        self.conflict_index
            .get(&operation)
            .is_some_and(|indices| !indices.is_empty())
    }

    fn conflict_is_retained(&self, observation: &CaptureObservation) -> bool {
        self.conflict_index
            .get(&observation.operation)
            .is_some_and(|indices| {
                indices
                    .iter()
                    .any(|&index| self.conflicts.get(index) == Some(observation))
            })
    }

    fn retain_conflict(&mut self, observation: CaptureObservation) {
        let index = self.conflicts.len();
        self.conflicts.push(observation);
        let operation = self.conflicts[index].operation;
        self.conflict_index
            .entry(operation)
            .or_default()
            .push(index);
    }
}
