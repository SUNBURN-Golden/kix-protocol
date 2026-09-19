//! Independent, sequential reference model. No Kernel calls, bitmaps or BTreeMap.
//! The shared public input/output types are a comparison boundary, not an oracle.
use kix_kernel::{
    AppliedReservation, CaptureObservation, Context, ExecutionFence, KernelError, Limits,
    ObservationOutcome, OrderState, ProviderOperation, Rejection, Reserve, ReserveOutcome,
    Selection,
};
use kix_types::{AssetAmount, KixId};

#[derive(Clone, Debug)]
pub enum InventoryCase {
    Seats(Vec<u16>),
    Ga(u32),
}

#[derive(Clone, Debug)]
pub enum Action {
    Reserve(Reserve),
    Send(KixId),
    Expire(KixId),
    Cancel(u64),
    Owner(ExecutionFence),
    Capture(CaptureObservation),
}

#[derive(Clone, Debug)]
pub struct Step {
    pub ctx: Context,
    pub action: Action,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Reply {
    Reserve(Result<AppliedReservation, KernelError>),
    Unit(Result<(), KernelError>),
    Expire(Result<bool, KernelError>),
    Capture(Result<ObservationOutcome, KernelError>),
}

/// Canonical v4 event identity boundary, kept separate from economic identity.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct EventIdentity {
    pub provider: KixId,
    pub account: KixId,
    pub event_id: KixId,
}

impl EventIdentity {
    fn of(value: &CaptureObservation) -> Self {
        Self {
            provider: value.operation.provider,
            account: value.operation.account,
            event_id: value.event_id,
        }
    }
}

/// Explicit one-to-one economic binding between an operation and an accepted order.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct OperationBinding {
    pub operation: ProviderOperation,
    pub order_id: KixId,
}

/// Stored accepted event: identity, full payload, named operation, binding and replay outcome.
#[derive(Clone, Debug)]
pub struct StoredEvent {
    pub identity: EventIdentity,
    pub observation: CaptureObservation,
    pub operation: ProviderOperation,
    pub bound_order: Option<KixId>,
    pub outcome: ObservationOutcome,
}

/// Reserved first-capture observation slot held by one bound operation.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SlotReservation {
    pub operation: ProviderOperation,
    pub order_id: KixId,
}

/// Quarantine of an operation that is already bound to an order.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BoundQuarantine {
    pub operation: ProviderOperation,
    pub order_id: KixId,
}

/// First retained economic capture effect of an order.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RetainedCapture {
    pub amount: AssetAmount,
    pub identity: EventIdentity,
}

#[derive(Clone, Debug)]
pub struct ModelOrder {
    pub input: Reserve,
    pub writer: ExecutionFence,
    /// Primary lifecycle phase; `review` is an orthogonal sticky predicate.
    pub phase: OrderState,
    pub owns: bool,
    pub capture: Option<RetainedCapture>,
    pub review: bool,
}

impl ModelOrder {
    pub fn captured_amount(&self) -> Option<AssetAmount> {
        self.capture.map(|c| c.amount)
    }
}

#[derive(Clone, Debug)]
pub struct Model {
    pub scope: KixId,
    pub writer: ExecutionFence,
    pub epoch: u64,
    pub cancelled: bool,
    pub time: u64,
    pub limits: Limits,
    pub layout: InventoryCase,
    /// One owner per individual seat, not a bitmap.
    pub seats: Vec<Option<KixId>>,
    segments: Vec<usize>,
    pub commands: Vec<(Reserve, ReserveOutcome)>,
    pub orders: Vec<ModelOrder>,
    /// Authoritative operation to order relation; `orders` keeps the redundant input.
    pub bindings: Vec<OperationBinding>,
    pub events: Vec<StoredEvent>,
    pub conflicts: Vec<CaptureObservation>,
    pub reservations: Vec<SlotReservation>,
    pub quarantined: Vec<BoundQuarantine>,
    /// Oracle-sensitivity control only. Never enabled for conformance tests.
    pub omit_full_quarantine: bool,
}

impl Model {
    pub fn new(
        scope: KixId,
        writer: ExecutionFence,
        layout: InventoryCase,
        limits: Limits,
    ) -> Self {
        let mut segments = Vec::new();
        if let InventoryCase::Seats(lengths) = &layout {
            for (number, &length) in lengths.iter().enumerate() {
                segments.extend(std::iter::repeat_n(number, usize::from(length)));
            }
        }
        Self {
            scope,
            writer,
            epoch: 1,
            cancelled: false,
            time: 0,
            limits,
            layout,
            seats: vec![None; segments.len()],
            segments,
            commands: Vec::new(),
            orders: Vec::new(),
            bindings: Vec::new(),
            events: Vec::new(),
            conflicts: Vec::new(),
            reservations: Vec::new(),
            quarantined: Vec::new(),
            omit_full_quarantine: false,
        }
    }

    pub fn remaining(&self) -> u32 {
        match self.layout {
            InventoryCase::Seats(_) => self.seats.iter().filter(|v| v.is_none()).count() as u32,
            InventoryCase::Ga(total) => {
                let used: u32 = self
                    .orders
                    .iter()
                    .filter(|o| o.owns)
                    .map(|o| match o.input.selection {
                        Selection::GeneralAdmission { count } => count,
                        _ => panic!("invalid reference GA order"),
                    })
                    .sum();
                total - used
            }
        }
    }

    pub fn budget(&self) -> usize {
        self.events.len() + self.conflicts.len() + self.reservations.len()
    }

    pub fn binding(&self, operation: ProviderOperation) -> Option<OperationBinding> {
        self.bindings
            .iter()
            .copied()
            .find(|b| b.operation == operation)
    }

    pub fn bound_quarantine_contains(&self, operation: ProviderOperation) -> bool {
        self.quarantined.iter().any(|q| q.operation == operation)
    }

    /// Retained conflict evidence naming an operation, bound or not.
    pub fn conflict_evidence_names(&self, operation: ProviderOperation) -> bool {
        self.conflicts.iter().any(|c| c.operation == operation)
    }

    /// Retained evidence about an operation that no order has bound. Never a
    /// scope-wide latch: it exists only while the conflict itself is retained.
    pub fn retained_unbound_blocked(&self, operation: ProviderOperation) -> bool {
        self.conflict_evidence_names(operation) && self.binding(operation).is_none()
    }

    pub fn retained_unbound_blocks(&self) -> Vec<ProviderOperation> {
        let mut result: Vec<ProviderOperation> = Vec::new();
        for conflict in &self.conflicts {
            if self.retained_unbound_blocked(conflict.operation)
                && !result.contains(&conflict.operation)
            {
                result.push(conflict.operation);
            }
        }
        result
    }

    /// Future binding is refused either by an explicit bound quarantine or by
    /// retained conflict evidence naming the operation. An unretained conflict
    /// leaves no ban behind.
    pub fn binding_blocked(&self, operation: ProviderOperation) -> bool {
        self.bound_quarantine_contains(operation) || self.conflict_evidence_names(operation)
    }

    pub fn reservation(&self, operation: ProviderOperation) -> Option<SlotReservation> {
        self.reservations
            .iter()
            .copied()
            .find(|r| r.operation == operation)
    }

    fn order(&self, id: KixId) -> Option<&ModelOrder> {
        self.orders.iter().find(|o| o.input.order_id == id)
    }

    fn check_context(&self, ctx: Context) -> Result<(), KernelError> {
        if ctx.semantics_version != 4 {
            return Err(KernelError::UnsupportedSemantics);
        }
        if ctx.fence != self.writer {
            return Err(KernelError::ExecutionFenced);
        }
        if ctx.now_ms < self.time {
            return Err(KernelError::ClockRegression);
        }
        Ok(())
    }

    fn index(&self, id: KixId) -> Result<usize, KernelError> {
        self.orders
            .iter()
            .position(|o| o.input.order_id == id)
            .ok_or(KernelError::UnknownOrder)
    }

    fn bound(&self, operation: ProviderOperation) -> Option<usize> {
        let binding = self.binding(operation)?;
        self.orders
            .iter()
            .position(|o| o.input.order_id == binding.order_id)
    }

    fn selection_rejection(&self, selection: Selection) -> Option<Rejection> {
        match (&self.layout, selection) {
            (InventoryCase::Seats(_), Selection::Seats { first, count }) => {
                let start = usize::from(first);
                let end = start + usize::from(count);
                if count == 0 || count > 64 || end > self.seats.len() {
                    return Some(Rejection::InvalidRequest);
                }
                if self.segments[start..end]
                    .iter()
                    .any(|v| *v != self.segments[start])
                {
                    return Some(Rejection::InvalidRequest);
                }
                if self.seats[start..end].iter().any(Option::is_some) {
                    return Some(Rejection::Unavailable);
                }
                None
            }
            (InventoryCase::Ga(_), Selection::GeneralAdmission { count }) => {
                if count == 0 {
                    Some(Rejection::InvalidRequest)
                } else if count > self.remaining() {
                    Some(Rejection::Unavailable)
                } else {
                    None
                }
            }
            _ => Some(Rejection::InvalidRequest),
        }
    }

    fn set_seat_owner(&mut self, request: &Reserve, owner: Option<KixId>) {
        if let Selection::Seats { first, count } = request.selection {
            for value in
                &mut self.seats[usize::from(first)..usize::from(first) + usize::from(count)]
            {
                if owner.is_none() {
                    assert_eq!(
                        *value,
                        Some(request.order_id),
                        "reference cannot release another owner"
                    );
                } else {
                    assert!(value.is_none(), "reference cannot overlap owners");
                }
                *value = owner;
            }
        }
    }

    fn reserve(
        &mut self,
        ctx: Context,
        request: Reserve,
    ) -> Result<AppliedReservation, KernelError> {
        if ctx.semantics_version != 4 {
            return Err(KernelError::UnsupportedSemantics);
        }
        if request.id.scope != self.scope {
            return Err(KernelError::WrongScope);
        }
        if let Some((input, result)) = self
            .commands
            .iter()
            .find(|(input, _)| input.id == request.id)
        {
            if input != &request {
                return Err(KernelError::CommandConflict);
            }
            return Ok(AppliedReservation {
                original: *result,
                replayed: true,
            });
        }
        self.check_context(ctx)?;
        if self.commands.len() >= self.limits.commands || self.orders.len() >= self.limits.orders {
            return Err(KernelError::Capacity);
        }
        let reason = if self.cancelled || request.expected_business_epoch != self.epoch {
            Some(Rejection::BusinessFenced)
        } else if request.amount.atoms() == 0 || request.expires_at_ms <= ctx.now_ms {
            Some(Rejection::InvalidRequest)
        } else if self
            .orders
            .iter()
            .any(|o| o.input.order_id == request.order_id)
        {
            Some(Rejection::OrderExists)
        } else if self.binding_blocked(request.payment) {
            Some(Rejection::OperationQuarantined)
        } else if self.bound(request.payment).is_some() {
            Some(Rejection::OperationAlreadyBound)
        } else {
            self.selection_rejection(request.selection)
        };
        let result = match reason {
            Some(reason) => ReserveOutcome::Rejected(reason),
            None => {
                self.set_seat_owner(&request, Some(request.order_id));
                self.orders.push(ModelOrder {
                    input: request.clone(),
                    writer: ctx.fence,
                    phase: OrderState::Held,
                    owns: true,
                    capture: None,
                    review: false,
                });
                self.bindings.push(OperationBinding {
                    operation: request.payment,
                    order_id: request.order_id,
                });
                ReserveOutcome::Held(request.order_id)
            }
        };
        self.commands.push((request, result));
        self.time = ctx.now_ms;
        Ok(AppliedReservation {
            original: result,
            replayed: false,
        })
    }

    fn send(&mut self, ctx: Context, id: KixId) -> Result<(), KernelError> {
        self.check_context(ctx)?;
        let i = self.index(id)?;
        let order = &self.orders[i];
        if order.review
            || !matches!(order.phase, OrderState::Held | OrderState::PaymentUnknown)
            || self.cancelled
            || ctx.now_ms >= order.input.expires_at_ms
        {
            return Err(KernelError::InvalidTransition);
        }
        let operation = order.input.payment;
        let order_id = order.input.order_id;
        if self.reservation(operation).is_none() {
            if self.budget() >= self.limits.observations {
                return Err(KernelError::Capacity);
            }
            self.reservations.push(SlotReservation {
                operation,
                order_id,
            });
        }
        self.orders[i].phase = OrderState::PaymentUnknown;
        self.time = ctx.now_ms;
        Ok(())
    }

    fn expire(&mut self, ctx: Context, id: KixId) -> Result<bool, KernelError> {
        self.check_context(ctx)?;
        let i = self.index(id)?;
        self.time = ctx.now_ms;
        let release = ctx.now_ms >= self.orders[i].input.expires_at_ms
            && self.orders[i].phase == OrderState::Held
            && self.orders[i].owns;
        if release {
            let input = self.orders[i].input.clone();
            self.set_seat_owner(&input, None);
            self.orders[i].owns = false;
            self.orders[i].phase = OrderState::Expired;
        }
        Ok(release)
    }

    fn control(&mut self, step: &Step) -> Result<(), KernelError> {
        self.check_context(step.ctx)?;
        match step.action {
            Action::Cancel(next) if next > self.epoch => {
                self.epoch = next;
                self.cancelled = true;
            }
            Action::Owner(next) if next.generation > self.writer.generation => self.writer = next,
            _ => return Err(KernelError::InvalidTransition),
        }
        self.time = step.ctx.now_ms;
        Ok(())
    }

    fn capture(
        &mut self,
        ctx: Context,
        value: CaptureObservation,
    ) -> Result<ObservationOutcome, KernelError> {
        self.check_context(ctx)?;
        let identity = EventIdentity::of(&value);
        let prior_event = self.events.iter().position(|old| old.identity == identity);
        if let Some(event) = prior_event {
            if self.events[event].observation == value {
                self.time = ctx.now_ms;
                return Ok(self.events[event].outcome);
            }
            // Error injection is in this independent oracle only, never in the locked kernel.
            if !(self.omit_full_quarantine && self.budget() >= self.limits.observations) {
                for operation in [self.events[event].operation, value.operation] {
                    if let Some(i) = self.bound(operation) {
                        self.orders[i].review = true;
                        if !self.bound_quarantine_contains(operation) {
                            let order_id = self.orders[i].input.order_id;
                            self.quarantined.push(BoundQuarantine {
                                operation,
                                order_id,
                            });
                        }
                    }
                }
            }
            self.time = ctx.now_ms;
            if !self.conflicts.contains(&value) {
                if self.budget() >= self.limits.observations {
                    return Err(KernelError::Capacity);
                }
                self.conflicts.push(value);
            }
            return Ok(ObservationOutcome::Conflict);
        }
        let reserved = self.reservation(value.operation).is_some();
        if !reserved && self.budget() >= self.limits.observations {
            return Err(KernelError::Capacity);
        }
        let i = self
            .bound(value.operation)
            .ok_or(KernelError::UnknownOperation)?;
        let existing = self.orders[i].captured_amount();
        let result = if let Some(first) = existing {
            if first == value.amount {
                ObservationOutcome::DuplicateEffect
            } else {
                self.orders[i].review = true;
                ObservationOutcome::Review
            }
        } else {
            self.orders[i].capture = Some(RetainedCapture {
                amount: value.amount,
                identity,
            });
            if value.amount != self.orders[i].input.amount {
                self.orders[i].phase = OrderState::Review;
                self.orders[i].review = true;
                ObservationOutcome::Review
            } else if self.cancelled
                || ctx.now_ms >= self.orders[i].input.expires_at_ms
                || self.orders[i].phase == OrderState::Expired
            {
                if self.orders[i].owns {
                    let input = self.orders[i].input.clone();
                    self.set_seat_owner(&input, None);
                    self.orders[i].owns = false;
                }
                self.orders[i].phase = OrderState::ReturnRequired;
                ObservationOutcome::ReturnRequired
            } else if self.orders[i].review {
                self.orders[i].phase = OrderState::Review;
                ObservationOutcome::Review
            } else {
                self.orders[i].phase = OrderState::PaymentConfirmed;
                ObservationOutcome::PaymentConfirmed
            }
        };
        self.reservations
            .retain(|reservation| reservation.operation != value.operation);
        let bound_order = self.binding(value.operation).map(|b| b.order_id);
        self.events.push(StoredEvent {
            identity,
            operation: value.operation,
            bound_order,
            observation: value,
            outcome: result,
        });
        self.time = ctx.now_ms;
        Ok(result)
    }

    /// Relational consistency of the model's own state. Reads no kernel state.
    pub fn check_relations(&self) -> Result<(), String> {
        for (index, binding) in self.bindings.iter().enumerate() {
            let order = self
                .order(binding.order_id)
                .ok_or_else(|| format!("binding {binding:?} has no accepted order"))?;
            if order.input.payment != binding.operation {
                return Err(format!(
                    "binding {binding:?} disagrees with {:?}",
                    order.input
                ));
            }
            if self.bindings[..index].iter().any(|other| {
                other.operation == binding.operation || other.order_id == binding.order_id
            }) {
                return Err(format!("binding {binding:?} is not one to one"));
            }
        }
        if self.bindings.len() != self.orders.len() {
            return Err(format!(
                "bindings={} but accepted orders={}",
                self.bindings.len(),
                self.orders.len()
            ));
        }
        for order in &self.orders {
            match self.binding(order.input.payment) {
                Some(binding) if binding.order_id == order.input.order_id => {}
                other => {
                    return Err(format!(
                        "accepted order {:?} has binding {other:?}",
                        order.input.order_id
                    ));
                }
            }
        }
        for (index, reservation) in self.reservations.iter().enumerate() {
            match self.binding(reservation.operation) {
                Some(binding) if binding.order_id == reservation.order_id => {}
                other => {
                    return Err(format!(
                        "reserved slot {reservation:?} has binding {other:?}"
                    ));
                }
            }
            if self.reservations[..index]
                .iter()
                .any(|other| other.operation == reservation.operation)
            {
                return Err(format!("reserved slot {reservation:?} is duplicated"));
            }
        }
        for (index, entry) in self.quarantined.iter().enumerate() {
            let order = match self.binding(entry.operation) {
                Some(binding) if binding.order_id == entry.order_id => {
                    self.order(entry.order_id)
                        .ok_or_else(|| format!("bound quarantine {entry:?} has no order"))?
                }
                other => return Err(format!("bound quarantine {entry:?} has binding {other:?}")),
            };
            if !order.review {
                return Err(format!(
                    "bound quarantine {entry:?} without review predicate"
                ));
            }
            if self.quarantined[..index]
                .iter()
                .any(|other| other.operation == entry.operation)
            {
                return Err(format!("bound quarantine {entry:?} is duplicated"));
            }
        }
        for operation in self.retained_unbound_blocks() {
            if self.binding(operation).is_some() {
                return Err(format!(
                    "unbound block {operation:?} has a speculative binding"
                ));
            }
            if !self.conflict_evidence_names(operation) {
                return Err(format!(
                    "unbound block {operation:?} has no retained evidence"
                ));
            }
            if self.bound_quarantine_contains(operation) {
                return Err(format!("{operation:?} is both bound and unbound blocked"));
            }
        }
        for (index, event) in self.events.iter().enumerate() {
            if event.identity != EventIdentity::of(&event.observation)
                || event.operation != event.observation.operation
            {
                return Err(format!("stored event {event:?} lost its identity relation"));
            }
            if self.events[..index]
                .iter()
                .any(|other| other.identity == event.identity)
            {
                return Err(format!("stored event {event:?} duplicates an identity"));
            }
            let order_id = event
                .bound_order
                .ok_or_else(|| format!("stored event {event:?} has no bound order"))?;
            match self.binding(event.operation) {
                Some(binding) if binding.order_id == order_id => {}
                other => return Err(format!("stored event {event:?} has binding {other:?}")),
            }
        }
        if self.budget() > self.limits.observations {
            return Err(format!(
                "observation budget {} exceeds {}",
                self.budget(),
                self.limits.observations
            ));
        }
        for order in &self.orders {
            let first = self
                .events
                .iter()
                .find(|event| event.bound_order == Some(order.input.order_id));
            match (order.capture, first) {
                (Some(capture), Some(event)) => {
                    if capture.amount != event.observation.amount
                        || capture.identity != event.identity
                    {
                        return Err(format!(
                            "retained capture {capture:?} disagrees with first event {event:?}"
                        ));
                    }
                }
                (None, None) => {}
                (capture, event) => {
                    return Err(format!(
                        "retained capture {capture:?} disagrees with stored events {event:?}"
                    ));
                }
            }
            // ReturnRequired is the primary phase; review is orthogonal and may coexist.
            if order.phase == OrderState::ReturnRequired && (order.capture.is_none() || order.owns)
            {
                return Err(format!(
                    "ReturnRequired order {:?} lost its retained capture or inventory release",
                    order.input.order_id
                ));
            }
        }
        Ok(())
    }

    pub fn apply(&mut self, step: &Step) -> Reply {
        match &step.action {
            Action::Reserve(request) => Reply::Reserve(self.reserve(step.ctx, request.clone())),
            Action::Send(id) => Reply::Unit(self.send(step.ctx, *id)),
            Action::Expire(id) => Reply::Expire(self.expire(step.ctx, *id)),
            Action::Cancel(_) | Action::Owner(_) => Reply::Unit(self.control(step)),
            Action::Capture(value) => Reply::Capture(self.capture(step.ctx, value.clone())),
        }
    }
}
