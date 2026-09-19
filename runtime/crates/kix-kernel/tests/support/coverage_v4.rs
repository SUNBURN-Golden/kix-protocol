//! Relation-aware coverage observer and transition properties for the E-4 model.
//!
//! Every step is classified from the independent model's state before and after
//! the step plus the reply both implementations agreed on. No `Kernel` method is
//! called and no kernel state is read: the differential comparison in the test
//! file already establishes that the model state equals the kernel's public
//! state, so a property asserted here on the model holds for the kernel too.
//!
//! Counters are keyed by family (P1–P7 of Task 003-B) and by transition class.
//! They only prove reachability of each class inside a generated corpus; they are
//! not a score, a mutation campaign or a proof of completeness.
use std::collections::BTreeMap;

use kix_kernel::{
    CommandId, KernelError, ObservationOutcome, OrderState, ProviderOperation, Rejection,
    ReserveOutcome, Selection,
};
use kix_types::KixId;

use super::reference::{Action, Model, ModelOrder, Reply, Step};

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Family {
    P1CommandIdentity,
    P2OperationBinding,
    P3SlotLifecycle,
    P4EventVsEconomic,
    P5QuarantineEvidence,
    P6ReturnRequiredReview,
    P7ObservationBudget,
}

pub const FAMILIES: [Family; 7] = [
    Family::P1CommandIdentity,
    Family::P2OperationBinding,
    Family::P3SlotLifecycle,
    Family::P4EventVsEconomic,
    Family::P5QuarantineEvidence,
    Family::P6ReturnRequiredReview,
    Family::P7ObservationBudget,
];

impl Family {
    pub fn tag(self) -> &'static str {
        match self {
            Family::P1CommandIdentity => "P1",
            Family::P2OperationBinding => "P2",
            Family::P3SlotLifecycle => "P3",
            Family::P4EventVsEconomic => "P4",
            Family::P5QuarantineEvidence => "P5",
            Family::P6ReturnRequiredReview => "P6",
            Family::P7ObservationBudget => "P7",
        }
    }
}

/// Deterministic reachability counters plus the bookkeeping the properties need.
#[derive(Clone, Debug, Default)]
pub struct Coverage {
    counts: BTreeMap<(Family, &'static str), u64>,
    /// Zero-based index of the observed step at which each class was first hit.
    first_step: BTreeMap<(Family, &'static str), u64>,
    /// Number of `observe` calls so far.
    steps: u64,
    /// Number of state-changing accepted steps seen so far.
    mutations: u64,
    /// Mutation counter at the moment each command identity was first recorded.
    recorded: Vec<(CommandId, u64)>,
    /// Operations named by a conflicting event whose evidence was refused for
    /// capacity while the operation was unbound (unretained unbound conflict).
    unretained: Vec<ProviderOperation>,
}

fn order(model: &Model, id: KixId) -> Option<&ModelOrder> {
    model.orders.iter().find(|o| o.input.order_id == id)
}

fn bound_order(model: &Model, operation: ProviderOperation) -> Option<&ModelOrder> {
    let binding = model.binding(operation)?;
    order(model, binding.order_id)
}

fn selection_free(model: &Model, selection: Selection) -> bool {
    match selection {
        Selection::Seats { first, count } => {
            let start = usize::from(first);
            let end = start + usize::from(count);
            count > 0
                && end <= model.seats.len()
                && model.seats[start..end].iter().all(Option::is_none)
        }
        Selection::GeneralAdmission { count } => count > 0 && count <= model.remaining(),
    }
}

fn same_provider_account(a: ProviderOperation, b: ProviderOperation) -> bool {
    a.provider == b.provider && a.account == b.account
}

fn public_counts(model: &Model) -> (u32, usize, usize, usize, usize, usize) {
    (
        model.remaining(),
        model.orders.len(),
        model.events.len(),
        model.conflicts.len(),
        model.reservations.len(),
        model.quarantined.len(),
    )
}

impl Coverage {
    pub fn new() -> Self {
        Self::default()
    }

    fn hit(&mut self, family: Family, class: &'static str) {
        *self.counts.entry((family, class)).or_insert(0) += 1;
        self.first_step
            .entry((family, class))
            .or_insert(self.steps.saturating_sub(1));
    }

    /// Zero-based step index of the first hit of `class` within this observer.
    pub fn first_step(&self, family: Family, class: &str) -> Option<u64> {
        self.first_step
            .iter()
            .find(|((f, c), _)| *f == family && *c == class)
            .map(|(_, s)| *s)
    }

    pub fn count(&self, family: Family, class: &str) -> u64 {
        self.counts
            .iter()
            .filter(|((f, c), _)| *f == family && *c == class)
            .map(|(_, n)| *n)
            .sum()
    }

    pub fn family_total(&self, family: Family) -> u64 {
        self.counts
            .iter()
            .filter(|((f, _), _)| *f == family)
            .map(|(_, n)| *n)
            .sum()
    }

    pub fn classes(&self, family: Family) -> Vec<(&'static str, u64)> {
        self.counts
            .iter()
            .filter(|((f, _), _)| *f == family)
            .map(|((_, c), n)| (*c, *n))
            .collect()
    }

    pub fn merge(&mut self, other: &Coverage) {
        for (key, n) in &other.counts {
            *self.counts.entry(*key).or_insert(0) += n;
        }
    }

    /// Stable JSON rendering: families and classes in sorted order.
    pub fn to_json(&self) -> String {
        let mut out = String::from("{");
        for (i, family) in FAMILIES.iter().enumerate() {
            if i > 0 {
                out.push(',');
            }
            out.push_str(&format!("\"{}\":{{", family.tag()));
            for (j, (class, n)) in self.classes(*family).iter().enumerate() {
                if j > 0 {
                    out.push(',');
                }
                out.push_str(&format!("\"{class}\":{n}"));
            }
            out.push('}');
        }
        out.push('}');
        out
    }

    /// Classify one agreed transition and check the relation properties it
    /// touches. `pre` and `post` are the independent model before and after the
    /// step; `reply` is the reply both implementations produced.
    pub fn observe(
        &mut self,
        pre: &Model,
        step: &Step,
        reply: &Reply,
        post: &Model,
    ) -> Result<(), String> {
        self.steps += 1;
        let stale_context = step.ctx.fence != pre.writer
            || step.ctx.now_ms < pre.time
            || step.ctx.semantics_version != 4;
        match (&step.action, reply) {
            (Action::Reserve(request), Reply::Reserve(result)) => {
                self.observe_reserve(pre, step, request, result, post, stale_context)?
            }
            (Action::Send(order_id), Reply::Unit(result)) => {
                self.observe_send(pre, step.ctx.now_ms, *order_id, result, post)?
            }
            (Action::Expire(order_id), Reply::Expire(result)) => {
                self.observe_expire(pre, step.ctx.now_ms, *order_id, result, post)?
            }
            (Action::Owner(_), Reply::Unit(result)) => {
                self.observe_control(pre, "owner_replacement", result, post)?
            }
            (Action::Cancel(_), Reply::Unit(result)) => {
                self.observe_control(pre, "scope_cancellation", result, post)?
            }
            (Action::Capture(observation), Reply::Capture(result)) => {
                self.observe_capture(pre, step, observation, result, post)?
            }
            (action, reply) => {
                return Err(format!("reply {reply:?} does not fit action {action:?}"));
            }
        }
        self.observe_sticky_facts(pre, post)?;
        if post.budget() > post.limits.observations {
            return Err("observation budget exceeded".into());
        }
        if post.budget() == post.limits.observations {
            self.hit(Family::P7ObservationBudget, "budget_full_after_step");
        }
        Ok(())
    }

    fn observe_reserve(
        &mut self,
        pre: &Model,
        step: &Step,
        request: &kix_kernel::Reserve,
        result: &Result<kix_kernel::AppliedReservation, KernelError>,
        post: &Model,
        stale_context: bool,
    ) -> Result<(), String> {
        let known = pre
            .commands
            .iter()
            .find(|(input, _)| input.id == request.id);
        let stale_fence = step.ctx.fence != pre.writer;
        let regressed_clock = step.ctx.now_ms < pre.time;
        match result {
            Ok(applied) if applied.replayed => {
                let (original_input, original) =
                    known.ok_or("replayed a command the model never recorded")?;
                if original_input != request || applied.original != *original {
                    return Err("replay changed the original payload or result".into());
                }
                if public_counts(pre) != public_counts(post) || pre.time != post.time {
                    return Err("original-result replay was not read-only".into());
                }
                self.hit(Family::P1CommandIdentity, "replay_exact");
                match original {
                    ReserveOutcome::Held(_) => {
                        self.hit(Family::P1CommandIdentity, "replay_of_accepted_first_result")
                    }
                    ReserveOutcome::Rejected(_) => {
                        self.hit(Family::P1CommandIdentity, "replay_of_rejected_first_result")
                    }
                }
                let recorded_at = self
                    .recorded
                    .iter()
                    .find(|(id, _)| *id == request.id)
                    .map(|(_, at)| *at)
                    .unwrap_or(0);
                if self.mutations > recorded_at {
                    self.hit(Family::P1CommandIdentity, "replay_after_state_changed");
                }
                if stale_context {
                    self.hit(Family::P1CommandIdentity, "replay_under_stale_context");
                }
                if stale_fence {
                    self.hit(Family::P1CommandIdentity, "replay_under_stale_fence");
                }
                if regressed_clock {
                    self.hit(Family::P1CommandIdentity, "replay_under_regressed_clock");
                }
                if *original == ReserveOutcome::Rejected(Rejection::Unavailable)
                    && selection_free(pre, request.selection)
                {
                    self.hit(
                        Family::P1CommandIdentity,
                        "rejected_replay_after_unavailable_cause_cleared",
                    );
                }
            }
            Ok(applied) => {
                if known.is_some() {
                    return Err("known command identity executed as new".into());
                }
                self.recorded.push((request.id, self.mutations));
                self.mutations += 1;
                match applied.original {
                    ReserveOutcome::Held(order_id) => {
                        if order_id != request.order_id {
                            return Err("held order id differs from request".into());
                        }
                        self.hit(Family::P1CommandIdentity, "first_result_held");
                        if post.bindings.len() != pre.bindings.len() + 1
                            || post.binding(request.payment).map(|b| b.order_id)
                                != Some(request.order_id)
                        {
                            return Err("accepted order did not create exactly one binding".into());
                        }
                        self.hit(Family::P2OperationBinding, "binding_created");
                        if pre.bindings.iter().any(|b| {
                            b.operation.provider == request.payment.provider
                                && b.operation.account == request.payment.account
                                && b.operation != request.payment
                        }) {
                            self.hit(
                                Family::P2OperationBinding,
                                "sibling_operation_bound_independently",
                            );
                        }
                        if self.unretained.contains(&request.payment) {
                            self.hit(
                                Family::P2OperationBinding,
                                "unretained_conflict_operation_bound_later",
                            );
                            self.hit(
                                Family::P5QuarantineEvidence,
                                "unretained_conflict_left_no_ban",
                            );
                        }
                        if !pre.quarantined.is_empty() || !pre.conflicts.is_empty() {
                            self.hit(
                                Family::P5QuarantineEvidence,
                                "binding_accepted_while_others_quarantined",
                            );
                        }
                        if pre.commands.iter().any(|(input, outcome)| {
                            input.id != request.id
                                && input.selection == request.selection
                                && *outcome == ReserveOutcome::Rejected(Rejection::Unavailable)
                        }) {
                            self.hit(
                                Family::P1CommandIdentity,
                                "new_identity_holds_selection_rejected_earlier",
                            );
                        }
                        if pre.conflicts.iter().any(|c| {
                            c.operation != request.payment
                                && same_provider_account(c.operation, request.payment)
                                && pre.retained_unbound_blocked(c.operation)
                        }) {
                            self.hit(
                                Family::P5QuarantineEvidence,
                                "sibling_of_retained_unbound_ban_bound_independently",
                            );
                        }
                    }
                    ReserveOutcome::Rejected(reason) => {
                        self.hit(Family::P1CommandIdentity, "first_result_rejected");
                        if post.bindings != pre.bindings || post.orders.len() != pre.orders.len() {
                            return Err("rejected reservation changed bindings or orders".into());
                        }
                        self.hit(Family::P2OperationBinding, "rejected_no_binding");
                        match reason {
                            Rejection::InvalidRequest
                                if request.expires_at_ms == step.ctx.now_ms
                                    && request.amount.atoms() > 0 =>
                            {
                                self.hit(
                                    Family::P3SlotLifecycle,
                                    "reservation_refused_at_exact_expiry_instant",
                                );
                            }
                            Rejection::OperationAlreadyBound => {
                                if pre.binding(request.payment).is_none() {
                                    return Err("AlreadyBound without a binding".into());
                                }
                                self.hit(
                                    Family::P2OperationBinding,
                                    "reuse_of_bound_operation_rejected",
                                );
                            }
                            Rejection::OperationQuarantined => {
                                if pre.retained_unbound_blocked(request.payment) {
                                    self.hit(
                                        Family::P2OperationBinding,
                                        "retained_unbound_operation_refused",
                                    );
                                    self.hit(
                                        Family::P5QuarantineEvidence,
                                        "retained_unbound_blocks_binding",
                                    );
                                    if pre.bindings.iter().any(|b| {
                                        b.operation.provider == request.payment.provider
                                            && b.operation.account == request.payment.account
                                    }) {
                                        self.hit(
                                            Family::P5QuarantineEvidence,
                                            "retained_unbound_ban_coexists_with_bound_sibling",
                                        );
                                    }
                                } else if pre.bound_quarantine_contains(request.payment) {
                                    self.hit(
                                        Family::P2OperationBinding,
                                        "bound_quarantined_operation_refused",
                                    );
                                } else {
                                    return Err("OperationQuarantined without quarantine or retained evidence".into());
                                }
                            }
                            _ => {}
                        }
                    }
                }
            }
            Err(KernelError::CommandConflict) => {
                let (original_input, _) =
                    known.ok_or("CommandConflict without a recorded command")?;
                if original_input == request {
                    return Err("CommandConflict on an identical payload".into());
                }
                if public_counts(pre) != public_counts(post)
                    || pre.commands.len() != post.commands.len()
                {
                    return Err("altered payload executed as a new command".into());
                }
                self.hit(Family::P1CommandIdentity, "altered_payload_conflict");
                if stale_context {
                    self.hit(
                        Family::P1CommandIdentity,
                        "altered_payload_conflict_under_stale_context",
                    );
                }
                if stale_fence {
                    self.hit(
                        Family::P1CommandIdentity,
                        "altered_payload_conflict_under_stale_fence",
                    );
                }
                if regressed_clock {
                    self.hit(
                        Family::P1CommandIdentity,
                        "altered_payload_conflict_under_regressed_clock",
                    );
                }
                if original_input.order_id != request.order_id {
                    self.hit(Family::P1CommandIdentity, "altered_field_order_id");
                }
                if original_input.amount != request.amount {
                    self.hit(Family::P1CommandIdentity, "altered_field_amount");
                }
                if original_input.payment != request.payment {
                    self.hit(Family::P1CommandIdentity, "altered_field_operation");
                }
                if original_input.expires_at_ms != request.expires_at_ms {
                    self.hit(Family::P1CommandIdentity, "altered_field_expiry");
                }
                if original_input.selection != request.selection {
                    self.hit(Family::P1CommandIdentity, "altered_field_selection");
                }
            }
            Err(KernelError::Capacity) => {
                if post.bindings != pre.bindings {
                    return Err("capacity refusal changed bindings".into());
                }
                self.hit(Family::P2OperationBinding, "reserve_refused_for_capacity");
            }
            Err(_) => {
                if known.is_some()
                    && !matches!(
                        result,
                        Err(KernelError::WrongScope | KernelError::UnsupportedSemantics)
                    )
                {
                    return Err("known command identity failed a later guard".into());
                }
                if known.is_some() {
                    if public_counts(pre) != public_counts(post)
                        || pre.commands.len() != post.commands.len()
                    {
                        return Err("scope/semantics guard changed state".into());
                    }
                    self.hit(
                        Family::P1CommandIdentity,
                        "replay_lookup_outranked_by_scope_or_semantics",
                    );
                    if matches!(result, Err(KernelError::UnsupportedSemantics)) {
                        self.hit(
                            Family::P1CommandIdentity,
                            "replay_lookup_outranked_by_semantics",
                        );
                    }
                }
                // A foreign scope changes the command identity itself, so the
                // recorded command is found by principal/request only.
                if matches!(result, Err(KernelError::WrongScope))
                    && pre.commands.iter().any(|(input, _)| {
                        input.id.scope != request.id.scope
                            && input.id.principal == request.id.principal
                            && input.id.request == request.id.request
                    })
                {
                    if public_counts(pre) != public_counts(post)
                        || pre.commands.len() != post.commands.len()
                    {
                        return Err("scope guard changed state".into());
                    }
                    self.hit(
                        Family::P1CommandIdentity,
                        "replay_lookup_outranked_by_scope",
                    );
                }
            }
        }
        Ok(())
    }

    fn observe_send(
        &mut self,
        pre: &Model,
        step_now: u64,
        order_id: KixId,
        result: &Result<(), KernelError>,
        post: &Model,
    ) -> Result<(), String> {
        let Some(before) = order(pre, order_id) else {
            return Ok(());
        };
        let operation = before.input.payment;
        match result {
            Ok(()) => {
                self.mutations += 1;
                let reserved = post
                    .reservation(operation)
                    .ok_or("accepted send left no reservation")?;
                if reserved.order_id != order_id {
                    return Err("reservation belongs to another order".into());
                }
                if pre.reservation(operation).is_some() {
                    if post.reservations.len() != pre.reservations.len() {
                        return Err("UNKNOWN retry changed the slot count".into());
                    }
                    self.hit(Family::P3SlotLifecycle, "unknown_retry_reuses_reservation");
                } else {
                    if post.reservations.len() != pre.reservations.len() + 1 {
                        return Err("first send did not reserve exactly one slot".into());
                    }
                    self.hit(Family::P3SlotLifecycle, "send_reserves_one_slot");
                    self.hit(
                        Family::P7ObservationBudget,
                        "reserved_slot_charged_to_budget",
                    );
                }
            }
            Err(KernelError::Capacity) => {
                if pre.reservation(operation).is_some() || pre.budget() < pre.limits.observations {
                    return Err("slot capacity refusal without a full budget".into());
                }
                if post.reservations != pre.reservations
                    || order(post, order_id).map(|o| o.phase) != Some(before.phase)
                {
                    return Err("slot capacity refusal changed state".into());
                }
                self.hit(Family::P3SlotLifecycle, "slot_capacity_refused");
                self.hit(Family::P7ObservationBudget, "send_refused_at_limit");
            }
            Err(KernelError::InvalidTransition) => {
                let after = order(post, order_id).ok_or("order vanished")?;
                if post.reservations != pre.reservations
                    || after.phase != before.phase
                    || after.owns != before.owns
                    || after.review != before.review
                    || post.remaining() != pre.remaining()
                {
                    return Err("refused send changed state".into());
                }
                let live = matches!(before.phase, OrderState::Held | OrderState::PaymentUnknown);
                if before.review && live && !pre.cancelled && step_now < before.input.expires_at_ms
                {
                    self.hit(Family::P5QuarantineEvidence, "reviewed_order_cannot_send");
                }
                if !before.review
                    && live
                    && !pre.cancelled
                    && step_now >= before.input.expires_at_ms
                {
                    self.hit(Family::P3SlotLifecycle, "send_refused_past_deadline");
                    if step_now == before.input.expires_at_ms {
                        self.hit(Family::P3SlotLifecycle, "send_refused_at_exact_deadline");
                    }
                    if before.phase == OrderState::PaymentUnknown
                        && pre.reservation(operation).is_some()
                    {
                        self.hit(
                            Family::P3SlotLifecycle,
                            "unknown_retry_refused_past_deadline_keeps_reservation",
                        );
                        if step_now == before.input.expires_at_ms {
                            self.hit(
                                Family::P3SlotLifecycle,
                                "unknown_retry_refused_at_exact_deadline_keeps_reservation",
                            );
                        } else {
                            self.hit(
                                Family::P3SlotLifecycle,
                                "unknown_retry_refused_strictly_after_deadline_keeps_reservation",
                            );
                        }
                    }
                }
                if before.phase == OrderState::ReturnRequired {
                    self.hit(
                        Family::P6ReturnRequiredReview,
                        "return_required_order_cannot_send",
                    );
                }
                if pre.bound_quarantine_contains(operation)
                    && (pre.cancelled || before.phase == OrderState::Expired)
                {
                    self.hit(
                        Family::P5QuarantineEvidence,
                        "quarantined_order_cannot_send_after_expiry_or_cancellation",
                    );
                }
            }
            Err(_) => {}
        }
        Ok(())
    }

    fn observe_expire(
        &mut self,
        pre: &Model,
        step_now: u64,
        order_id: KixId,
        result: &Result<bool, KernelError>,
        post: &Model,
    ) -> Result<(), String> {
        let Some(before) = order(pre, order_id) else {
            return Ok(());
        };
        if let Ok(released) = result {
            self.mutations += 1;
            if pre.reservation(before.input.payment).is_some() {
                if post.reservations != pre.reservations {
                    return Err("expiry check released a reserved slot".into());
                }
                self.hit(Family::P3SlotLifecycle, "expiry_check_keeps_reservation");
            }
            if *released {
                self.hit(Family::P3SlotLifecycle, "held_order_expired");
                if step_now == before.input.expires_at_ms {
                    self.hit(
                        Family::P3SlotLifecycle,
                        "held_order_expired_at_exact_instant",
                    );
                }
                if pre.bound_quarantine_contains(before.input.payment) {
                    self.hit(
                        Family::P5QuarantineEvidence,
                        "bound_quarantine_survives_expiry_release",
                    );
                }
            }
            if before.phase == OrderState::PaymentUnknown
                && step_now >= before.input.expires_at_ms
                && !released
            {
                self.hit(Family::P3SlotLifecycle, "unknown_order_not_released_by_ttl");
            }
            if pre.bound_quarantine_contains(before.input.payment) {
                self.hit(
                    Family::P5QuarantineEvidence,
                    "bound_quarantine_survives_expiry_check",
                );
            }
        }
        Ok(())
    }

    fn observe_control(
        &mut self,
        pre: &Model,
        kind: &'static str,
        result: &Result<(), KernelError>,
        post: &Model,
    ) -> Result<(), String> {
        if result.is_ok() {
            self.mutations += 1;
            if post.reservations != pre.reservations {
                return Err(format!("{kind} released a reserved slot"));
            }
            if post.quarantined != pre.quarantined {
                return Err(format!("{kind} changed the bound quarantine set"));
            }
            if !pre.reservations.is_empty() {
                self.hit(
                    Family::P3SlotLifecycle,
                    match kind {
                        "owner_replacement" => "owner_replacement_keeps_reservation",
                        _ => "scope_cancellation_keeps_reservation",
                    },
                );
            }
            if !pre.quarantined.is_empty() {
                self.hit(
                    Family::P5QuarantineEvidence,
                    match kind {
                        "owner_replacement" => "bound_quarantine_survives_owner_replacement",
                        _ => "bound_quarantine_survives_scope_cancellation",
                    },
                );
            }
        }
        Ok(())
    }

    fn observe_capture(
        &mut self,
        pre: &Model,
        step: &Step,
        observation: &kix_kernel::CaptureObservation,
        result: &Result<ObservationOutcome, KernelError>,
        post: &Model,
    ) -> Result<(), String> {
        let identity = (
            observation.operation.provider,
            observation.operation.account,
            observation.event_id,
        );
        let prior = pre
            .events
            .iter()
            .find(|e| (e.identity.provider, e.identity.account, e.identity.event_id) == identity);
        let bound_before = bound_order(pre, observation.operation);
        let other_reservations: Vec<_> = pre
            .reservations
            .iter()
            .filter(|r| r.operation != observation.operation)
            .copied()
            .collect();
        if !other_reservations.is_empty() {
            if other_reservations
                .iter()
                .any(|r| post.reservation(r.operation) != Some(*r))
            {
                return Err("capture consumed another operation's reservation".into());
            }
            self.hit(
                Family::P3SlotLifecycle,
                "capture_leaves_other_reservations_intact",
            );
        }
        match (prior, result) {
            (Some(event), Ok(outcome)) if event.observation == *observation => {
                if *outcome != event.outcome || public_counts(pre) != public_counts(post) {
                    return Err("identical event replay was not read-only".into());
                }
                self.hit(Family::P4EventVsEconomic, "identical_event_replay");
                if bound_before.is_some_and(|o| o.phase == OrderState::ReturnRequired) {
                    self.hit(
                        Family::P6ReturnRequiredReview,
                        "event_replay_after_return_required",
                    );
                }
            }
            (Some(event), Ok(ObservationOutcome::Conflict)) => {
                self.mutations += 1;
                self.hit(
                    Family::P4EventVsEconomic,
                    "same_identity_altered_payload_conflict",
                );
                if post.events.len() != pre.events.len() {
                    return Err("conflict stored a second event under one identity".into());
                }
                self.classify_conflict(pre, post, event.operation, observation.operation)?;
                if !pre.conflicts.contains(observation) {
                    if pre.budget() >= pre.limits.observations {
                        return Err("conflict retained beyond the budget".into());
                    }
                    if pre.budget() + 1 == pre.limits.observations {
                        self.hit(
                            Family::P7ObservationBudget,
                            "conflict_admitted_at_last_unit",
                        );
                    }
                    self.hit(Family::P7ObservationBudget, "conflict_retained");
                } else {
                    self.hit(
                        Family::P4EventVsEconomic,
                        "retained_conflict_replayed_without_new_evidence",
                    );
                }
            }
            (Some(event), Err(KernelError::Capacity)) => {
                self.mutations += 1;
                if pre.budget() < pre.limits.observations {
                    return Err("conflict refused below the budget".into());
                }
                if post.conflicts != pre.conflicts {
                    return Err("refused conflict retained evidence".into());
                }
                self.hit(Family::P7ObservationBudget, "conflict_refused_at_limit");
                self.classify_conflict(pre, post, event.operation, observation.operation)?;
                for operation in [event.operation, observation.operation] {
                    if pre.binding(operation).is_none() {
                        if post.binding_blocked(operation) != pre.binding_blocked(operation) {
                            return Err("unretained unbound conflict created a ban".into());
                        }
                        self.hit(
                            Family::P5QuarantineEvidence,
                            "unretained_unbound_conflict_at_full_budget",
                        );
                        if !self.unretained.contains(&operation) {
                            self.unretained.push(operation);
                        }
                    }
                }
            }
            (None, Ok(outcome)) => {
                self.mutations += 1;
                let before = bound_before.ok_or("accepted capture for unbound operation")?;
                let after = order(post, before.input.order_id).ok_or("order vanished")?;
                if pre.reservation(observation.operation).is_some() {
                    if post.reservation(observation.operation).is_some() {
                        return Err("accepted capture kept its reservation".into());
                    }
                    if post.budget() != pre.budget() {
                        return Err("reservation conversion changed the budget".into());
                    }
                    self.hit(Family::P3SlotLifecycle, "capture_consumes_own_reservation");
                    self.hit(
                        Family::P7ObservationBudget,
                        "reserved_slot_converted_to_stored_event",
                    );
                    if pre.budget() >= pre.limits.observations {
                        self.hit(
                            Family::P7ObservationBudget,
                            "promised_capacity_honoured_at_full_budget",
                        );
                    }
                } else {
                    if pre.budget() >= pre.limits.observations {
                        return Err("unreserved capture stored beyond the budget".into());
                    }
                    self.hit(
                        Family::P7ObservationBudget,
                        "unreserved_event_stored_within_budget",
                    );
                }
                if before.capture.is_some() {
                    self.hit(
                        Family::P4EventVsEconomic,
                        "same_operation_new_event_identity",
                    );
                    if after.capture != before.capture || after.phase != before.phase {
                        return Err("second event changed the retained capture or phase".into());
                    }
                    if after.owns != before.owns || post.remaining() != pre.remaining() {
                        return Err("second capture released inventory again".into());
                    }
                    match outcome {
                        ObservationOutcome::DuplicateEffect => {
                            self.hit(Family::P4EventVsEconomic, "duplicate_economic_effect");
                            if before.phase == OrderState::ReturnRequired {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "duplicate_effect_after_return_required",
                                );
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "no_second_inventory_release",
                                );
                            }
                            if before.review && !after.review {
                                return Err("duplicate effect cleared review".into());
                            }
                        }
                        ObservationOutcome::Review => {
                            if !after.review {
                                return Err("mismatching later evidence did not set review".into());
                            }
                            self.hit(Family::P4EventVsEconomic, "later_mismatch_raises_review");
                            if before.phase == OrderState::ReturnRequired {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "mismatch_after_return_required_keeps_phase",
                                );
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "retained_capture_preserved_under_mismatch",
                                );
                            }
                        }
                        other => return Err(format!("second capture produced {other:?}")),
                    }
                } else {
                    if after.capture.map(|c| c.amount) != Some(observation.amount) {
                        return Err("first capture not retained".into());
                    }
                    match outcome {
                        ObservationOutcome::ReturnRequired => {
                            if after.owns || after.phase != OrderState::ReturnRequired {
                                return Err("ReturnRequired without inventory release".into());
                            }
                            self.hit(
                                Family::P6ReturnRequiredReview,
                                "late_matching_capture_return_required",
                            );
                            if pre.reservation(observation.operation).is_some() {
                                self.hit(
                                    Family::P3SlotLifecycle,
                                    "late_capture_converts_reservation_to_return_required",
                                );
                            }
                            if before.phase != OrderState::Expired
                                && !pre.cancelled
                                && step.ctx.now_ms == before.input.expires_at_ms
                            {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "return_required_at_exact_deadline",
                                );
                            }
                            if before.phase == OrderState::Expired {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "return_required_after_expiry_release",
                                );
                            } else if pre.cancelled {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "return_required_after_cancellation",
                                );
                            } else if step.ctx.now_ms >= before.input.expires_at_ms {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "return_required_past_deadline",
                                );
                            }
                            if before.review {
                                self.hit(
                                    Family::P6ReturnRequiredReview,
                                    "return_required_on_already_reviewed_order",
                                );
                            }
                        }
                        ObservationOutcome::PaymentConfirmed => {
                            self.hit(Family::P4EventVsEconomic, "first_capture_confirmed");
                        }
                        ObservationOutcome::Review => {
                            self.hit(Family::P4EventVsEconomic, "first_capture_reviewed");
                        }
                        other => return Err(format!("first capture produced {other:?}")),
                    }
                }
            }
            (None, Err(KernelError::UnknownOperation)) => {
                if bound_before.is_some() {
                    return Err("UnknownOperation for a bound operation".into());
                }
                if post.events.len() != pre.events.len() || post.conflicts != pre.conflicts {
                    return Err("unbound capture stored evidence".into());
                }
                self.hit(Family::P4EventVsEconomic, "unbound_capture_not_stored");
            }
            (None, Err(KernelError::Capacity)) => {
                if pre.reservation(observation.operation).is_some() {
                    return Err("reserved operation refused for capacity".into());
                }
                self.hit(
                    Family::P7ObservationBudget,
                    "unreserved_capture_refused_at_limit",
                );
            }
            (_, Err(_)) => {}
            (Some(_), Ok(other)) => {
                return Err(format!("known event identity produced {other:?}"));
            }
        }
        Ok(())
    }

    fn classify_conflict(
        &mut self,
        pre: &Model,
        post: &Model,
        original: ProviderOperation,
        incoming: ProviderOperation,
    ) -> Result<(), String> {
        let bound = |op| pre.binding(op).is_some();
        match (bound(original), bound(incoming)) {
            (true, true) if original != incoming => self.hit(
                Family::P4EventVsEconomic,
                "conflict_names_two_bound_operations",
            ),
            (true, true) => self.hit(
                Family::P4EventVsEconomic,
                "conflict_names_one_bound_operation",
            ),
            (true, false) | (false, true) => self.hit(
                Family::P4EventVsEconomic,
                "conflict_names_bound_and_unbound",
            ),
            (false, false) => return Err("stored event belongs to an unbound operation".into()),
        }
        for operation in [original, incoming] {
            if bound(operation) {
                if !post.bound_quarantine_contains(operation) {
                    return Err("bound conflict did not quarantine".into());
                }
                let order = bound_order(post, operation).ok_or("quarantined order missing")?;
                if !order.review {
                    return Err("quarantined bound order lacks review".into());
                }
                if pre.bound_quarantine_contains(operation) {
                    self.hit(Family::P5QuarantineEvidence, "bound_quarantine_reconfirmed");
                } else {
                    self.hit(
                        Family::P5QuarantineEvidence,
                        "bound_conflict_quarantines_order",
                    );
                }
            } else if post.binding(operation).is_some() {
                return Err("conflict created a speculative binding".into());
            }
        }
        if post.binding(incoming).is_none() && post.conflict_evidence_names(incoming) {
            self.hit(
                Family::P5QuarantineEvidence,
                "retained_unbound_evidence_present",
            );
        }
        Ok(())
    }

    /// Facts that no tested transition may undo: review is sticky, a retained
    /// capture and a bound quarantine never disappear, ReturnRequired stays.
    fn observe_sticky_facts(&mut self, pre: &Model, post: &Model) -> Result<(), String> {
        let mut reviewed = false;
        for before in &pre.orders {
            let after = order(post, before.input.order_id).ok_or("order vanished")?;
            if before.review {
                reviewed = true;
                if !after.review {
                    return Err("review predicate was cleared".into());
                }
            }
            if before.capture.is_some() && after.capture != before.capture {
                return Err("retained capture changed".into());
            }
            if before.phase == OrderState::ReturnRequired
                && after.phase != OrderState::ReturnRequired
            {
                return Err("ReturnRequired phase was replaced".into());
            }
            if before.phase == OrderState::ReturnRequired && after.review && !before.review {
                self.hit(
                    Family::P6ReturnRequiredReview,
                    "review_set_while_return_required_persists",
                );
            }
        }
        if reviewed {
            self.hit(
                Family::P6ReturnRequiredReview,
                "review_predicate_sticky_across_step",
            );
        }
        for entry in &pre.quarantined {
            if !post.quarantined.contains(entry) {
                return Err("bound quarantine entry vanished".into());
            }
        }
        Ok(())
    }
}
