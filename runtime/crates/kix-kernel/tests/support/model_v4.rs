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

#[derive(Clone, Debug)]
pub struct ModelOrder {
    pub input: Reserve,
    pub writer: ExecutionFence,
    pub phase: OrderState,
    pub owns: bool,
    pub amount: Option<AssetAmount>,
    pub review: bool,
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
    pub events: Vec<(CaptureObservation, ObservationOutcome)>,
    pub conflicts: Vec<CaptureObservation>,
    pub promised: Vec<ProviderOperation>,
    pub quarantined: Vec<ProviderOperation>,
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
            events: Vec::new(),
            conflicts: Vec::new(),
            promised: Vec::new(),
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
        self.events.len() + self.conflicts.len() + self.promised.len()
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
        self.orders
            .iter()
            .position(|o| o.input.payment == operation)
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
        } else if self.quarantined.contains(&request.payment)
            || self
                .conflicts
                .iter()
                .any(|c| c.operation == request.payment)
        {
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
                    amount: None,
                    review: false,
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
        if !self.promised.contains(&operation) {
            if self.budget() >= self.limits.observations {
                return Err(KernelError::Capacity);
            }
            self.promised.push(operation);
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
        let prior_event = self.events.iter().position(|(old, _)| {
            old.operation.provider == value.operation.provider
                && old.operation.account == value.operation.account
                && old.event_id == value.event_id
        });
        if let Some(event) = prior_event {
            if self.events[event].0 == value {
                self.time = ctx.now_ms;
                return Ok(self.events[event].1);
            }
            // Error injection is in this independent oracle only, never in the locked kernel.
            if !(self.omit_full_quarantine && self.budget() >= self.limits.observations) {
                for operation in [self.events[event].0.operation, value.operation] {
                    if let Some(i) = self.bound(operation) {
                        self.orders[i].review = true;
                        if !self.quarantined.contains(&operation) {
                            self.quarantined.push(operation);
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
        let reserved = self.promised.contains(&value.operation);
        if !reserved && self.budget() >= self.limits.observations {
            return Err(KernelError::Capacity);
        }
        let i = self
            .bound(value.operation)
            .ok_or(KernelError::UnknownOperation)?;
        let existing = self.orders[i].amount;
        let result = if let Some(first) = existing {
            if first == value.amount {
                ObservationOutcome::DuplicateEffect
            } else {
                self.orders[i].review = true;
                ObservationOutcome::Review
            }
        } else {
            self.orders[i].amount = Some(value.amount);
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
        self.promised
            .retain(|operation| *operation != value.operation);
        self.events.push((value, result));
        self.time = ctx.now_ms;
        Ok(result)
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
