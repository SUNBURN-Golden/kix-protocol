#![forbid(unsafe_code)]
//! KTX-R1 deterministic, single-shard transition kernel. NOT a durable service.
//!
//! Inputs must come from an authenticated, ordered adapter. This crate does not
//! authenticate principals, registry claims, policies, or provider observations.
//! It performs no I/O, clock reads, random generation, replication, or ACKs.
//! The future durable driver must log validated commands before applying them
//! and must not turn these in-memory results into durability claims.

use std::collections::{BTreeMap, BTreeSet};

use kix_types::{AssetAmount, Hash32, KixId};

pub const SEMANTICS_VERSION: u16 = 1;
pub const MAX_SEATS: u16 = 4_096;
pub const MAX_BUNDLE: u16 = 64;

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
/// check that releases nothing and a duplicate observation. Errors change no
/// state. An existing reservation result lookup is read-only: it checks scope,
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
    // Each retained conflict contributes at most two identities. The observation
    // limit therefore bounds this sticky set even when an operation is unbound.
    quarantined_operations: BTreeSet<ProviderOperation>,
    observations: BTreeMap<EventKey, (CaptureObservation, ObservationOutcome)>,
    conflicts: Vec<CaptureObservation>,
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
        } else if self.quarantined_operations.contains(&request.payment) {
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
        self.commands
            .insert(request.id, CommandRecord { request, result });
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
    pub fn mark_payment_unknown(
        &mut self,
        ctx: Context,
        order_id: KixId,
    ) -> Result<(), KernelError> {
        self.context(ctx)?;
        let order = self
            .orders
            .get_mut(&order_id)
            .ok_or(KernelError::UnknownOrder)?;
        if order.review_required
            || !matches!(order.state, OrderState::Held | OrderState::PaymentUnknown)
        {
            return Err(KernelError::InvalidTransition);
        }
        if self.cancelled || ctx.now_ms >= order.request.expires_at_ms {
            return Err(KernelError::InvalidTransition);
        }
        order.state = OrderState::PaymentUnknown;
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
            if !self.conflicts.contains(&observation) {
                if self.observations.len() + self.conflicts.len() >= self.limits.observations {
                    return Err(KernelError::Capacity);
                }
                self.conflicts.push(observation);
            }
            // Retain the original fact and quarantine every bound order named
            // by the conflict. Unbound operations must not later gain a fresh
            // order binding. Repeated evidence consumes no additional capacity.
            for operation in affected_operations {
                self.quarantined_operations.insert(operation);
                if let Some(order_id) = self.operations.get(&operation)
                    && let Some(order) = self.orders.get_mut(order_id)
                {
                    order.review_required = true;
                }
            }
            self.now_ms = ctx.now_ms;
            return Ok(ObservationOutcome::Conflict);
        }
        if self.observations.len() + self.conflicts.len() >= self.limits.observations {
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
    pub fn conflicts(&self) -> &[CaptureObservation] {
        &self.conflicts
    }
}
