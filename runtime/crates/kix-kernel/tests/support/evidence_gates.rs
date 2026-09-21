//! Task 003-C1: narrow generated-evidence gates, separate from the source-informed model.
//! Histories live for one trace and use full typed identities. Kernel equality is
//! checked by the caller before these model-derived witnesses can be accepted.
use std::collections::BTreeMap;

use super::reference::{
    Action, EventIdentity, Model, ModelOrder, Reply, RetainedCapture, SlotReservation, Step,
};
use kix_kernel::{
    CaptureObservation, Kernel, KernelError, ObservationOutcome, OrderState, ProviderOperation,
    Reserve,
};
use kix_types::KixId;

pub const UNKNOWN_CHAIN: &str = "unknown_deadline_retry_then_late_capture";
pub const RETURN_CHAIN: &str = "return_duplicate_mismatch_reviewed_send_sequence";
pub const QUARANTINE_CHAIN: &str = "retained_two_bound_owner_expiry_cancel_send_sequence";
pub const FIELDS: [&str; 4] = ["order_id", "operation", "expiry", "selection"];
pub const CONTEXTS: [&str; 3] = ["normal", "stale_fence_only", "regressed_clock_only"];

pub fn matrix_key(field: &str, context: &str) -> String {
    format!("altered_{field}_{context}")
}
pub fn required(row: usize) -> Vec<String> {
    match row {
        1 => FIELDS
            .iter()
            .flat_map(|f| CONTEXTS.iter().map(move |c| matrix_key(f, c)))
            .collect(),
        4 => vec![UNKNOWN_CHAIN.into()],
        5 => vec![RETURN_CHAIN.into()],
        6 => vec![QUARANTINE_CHAIN.into()],
        _ => Vec::new(),
    }
}

fn event(o: &CaptureObservation) -> EventIdentity {
    EventIdentity {
        provider: o.operation.provider,
        account: o.operation.account,
        event_id: o.event_id,
    }
}
fn order(m: &Model, id: KixId) -> Option<&ModelOrder> {
    m.orders.iter().find(|o| o.input.order_id == id)
}
fn known_event(m: &Model, o: &CaptureObservation) -> bool {
    m.events.iter().any(|e| e.identity == event(o))
}
fn quantity(o: &ModelOrder) -> u32 {
    match o.input.selection {
        kix_kernel::Selection::Seats { count, .. } => u32::from(count),
        kix_kernel::Selection::GeneralAdmission { count } => count,
    }
}
fn require(ok: bool, message: &str) -> Result<(), String> {
    if ok { Ok(()) } else { Err(message.into()) }
}

/// Error/replay classification is contractual, not `Err => unchanged`: retained
/// event conflicts can quarantine and advance time even on Capacity.
pub fn must_be_read_only(pre: &Model, step: &Step, reply: &Reply) -> bool {
    match reply {
        Reply::Reserve(Ok(r)) => r.replayed,
        Reply::Reserve(Err(_)) | Reply::Unit(Err(_)) | Reply::Expire(Err(_)) => true,
        Reply::Capture(Err(KernelError::Capacity)) => {
            matches!(&step.action, Action::Capture(o) if !known_event(pre, o))
        }
        Reply::Capture(Err(_)) => true,
        _ => false,
    }
}
pub fn exact_read_only(
    pre: &Model,
    step: &Step,
    reply: &Reply,
    before: &Kernel,
    after: &Kernel,
) -> Result<(), String> {
    require(
        !must_be_read_only(pre, step, reply) || before == after,
        "contract read-only call changed whole Kernel state",
    )
}

/// Reset only the named field and compare the entire typed payload. This rejects
/// both multi-field changes and otherwise unnoticed quote/asset/epoch changes.
pub fn single_field(original: &Reserve, changed: &Reserve) -> Option<&'static str> {
    for field in FIELDS {
        let mut restored = changed.clone();
        match field {
            "order_id" => restored.order_id = original.order_id,
            "operation" => restored.payment.operation = original.payment.operation,
            "expiry" => restored.expires_at_ms = original.expires_at_ms,
            "selection" => restored.selection = original.selection,
            _ => unreachable!(),
        }
        if changed != original && restored == *original {
            return Some(field);
        }
    }
    None
}

#[derive(Clone, Debug)]
struct Retry {
    step: usize,
    slot: SlotReservation,
}
#[derive(Clone, Debug)]
struct ReturnHistory {
    operation: ProviderOperation,
    capture: RetainedCapture,
    first: usize,
    duplicate: Option<(usize, EventIdentity)>,
    mismatch: Option<(usize, EventIdentity)>,
}
#[derive(Clone, Debug)]
struct QuarantineHistory {
    operations: [ProviderOperation; 2],
    orders: [KixId; 2],
    evidence: CaptureObservation,
    steps: Vec<usize>,
}
#[derive(Clone, Debug, Default)]
pub struct Gates {
    /// All witnesses, not only first, so a reviewer can audit individual history.
    pub hits: BTreeMap<String, Vec<String>>,
    retries: BTreeMap<KixId, Retry>,
    returns: BTreeMap<KixId, ReturnHistory>,
    quarantines: BTreeMap<KixId, QuarantineHistory>,
}
impl Gates {
    fn hit(&mut self, key: &str, witness: String) {
        self.hits.entry(key.into()).or_default().push(witness);
    }
    pub fn count(&self, key: &str) -> usize {
        self.hits.get(key).map_or(0, Vec::len)
    }
    pub fn observe(
        &mut self,
        n: usize,
        pre: &Model,
        step: &Step,
        reply: &Reply,
        post: &Model,
    ) -> Result<(), String> {
        if let Action::Reserve(input) = &step.action
            && let Some((original, _)) = pre.commands.iter().find(|(r, _)| r.id == input.id)
            && let Some(field) = single_field(original, input)
            && step.ctx.semantics_version == 4
            && input.id.scope == pre.scope
        {
            let context = match (step.ctx.fence != pre.writer, step.ctx.now_ms < pre.time) {
                (false, false) => Some("normal"),
                (true, false) => Some("stale_fence_only"),
                (false, true) => Some("regressed_clock_only"),
                (true, true) => None,
            };
            if let Some(context) = context {
                require(
                    *reply == Reply::Reserve(Err(KernelError::CommandConflict)),
                    "single-field/guard matrix must return CommandConflict",
                )?;
                self.hit(&matrix_key(field, context), format!("step={n}; command={:?}; original={original:?}; changed={input:?}; context={:?}", input.id, step.ctx));
            }
        }
        match (&step.action, reply) {
            (Action::Send(id), Reply::Unit(Err(KernelError::InvalidTransition))) => {
                if let (Some(before), Some(after)) = (order(pre, *id), order(post, *id)) {
                    if before.phase == OrderState::PaymentUnknown
                        && !pre.cancelled
                        && !before.review
                        && step.ctx.fence == pre.writer
                        && step.ctx.semantics_version == 4
                        && step.ctx.now_ms >= pre.time
                        && step.ctx.now_ms >= before.input.expires_at_ms
                        && let Some(slot) = pre.reservation(before.input.payment)
                    {
                        require(
                            before.owns
                                && after.owns
                                && after.phase == before.phase
                                && post.reservation(before.input.payment) == Some(slot)
                                && pre.reservations == post.reservations
                                && pre.remaining() == post.remaining(),
                            "UNKNOWN retry lost exact reservation or inventory",
                        )?;
                        self.retries.entry(*id).or_insert(Retry { step: n, slot });
                    }
                    if let Some(h) = self.returns.get(id)
                        && let (Some(duplicate), Some(mismatch)) = (h.duplicate, h.mismatch)
                        && n > mismatch.0
                        && before.review
                    {
                        require(
                            before.input.payment == h.operation
                                && before.capture == Some(h.capture)
                                && after.capture == Some(h.capture)
                                && before.phase == OrderState::ReturnRequired
                                && after.phase == OrderState::ReturnRequired
                                && after.review
                                && !before.owns
                                && !after.owns,
                            "reviewed ReturnRequired send did not preserve phase/capture/review",
                        )?;
                        self.hit(RETURN_CHAIN, format!("order={id:?}; operation={:?}; first_step={}; first_event={:?}; duplicate={duplicate:?}; mismatch={mismatch:?}; refused_send_step={n}; review=true; kernel_eq=required", h.operation, h.first, h.capture.identity));
                    }
                    if let Some(h) = self.quarantines.get(id)
                        && h.steps.len() == 4
                        && before.phase == OrderState::Expired
                    {
                        require(
                            pre.cancelled
                                && before.phase == OrderState::Expired
                                && before.review
                                && after.review
                                && h.operations.iter().zip(h.orders).all(|(op, oid)| {
                                    post.quarantined
                                        .iter()
                                        .any(|q| q.operation == *op && q.order_id == oid)
                                        && order(post, oid).is_some_and(|o| o.review)
                                })
                                && post.conflicts.contains(&h.evidence),
                            "retained two-bound quarantine history lost provenance or sticky state",
                        )?;
                        self.hit(QUARANTINE_CHAIN, format!("order={id:?}; operations={:?}; orders={:?}; retained_conflict={:?}; origin_owner_expiry_cancel_steps={:?}; refused_send_step={n}; kernel_eq=required", h.operations, h.orders, h.evidence, h.steps));
                    }
                }
            }
            (Action::Capture(o), Reply::Capture(Ok(outcome))) => {
                if *outcome == ObservationOutcome::Conflict
                    && post.conflicts.contains(o)
                    && let Some(original) = pre.events.iter().find(|e| e.identity == event(o))
                    && original.observation != *o
                    && original.operation != o.operation
                    && let (Some(a), Some(b)) =
                        (pre.binding(original.operation), pre.binding(o.operation))
                    && a.order_id != b.order_id
                {
                    let operations = [a.operation, b.operation];
                    let orders = [a.order_id, b.order_id];
                    require(
                        operations.iter().zip(orders).all(|(op, oid)| {
                            post.quarantined
                                .iter()
                                .any(|q| q.operation == *op && q.order_id == oid)
                                && order(post, oid).is_some_and(|o| o.review)
                        }),
                        "retained two-bound conflict failed to quarantine both exact bindings",
                    )?;
                    for id in orders {
                        self.quarantines.entry(id).or_insert(QuarantineHistory {
                            operations,
                            orders,
                            evidence: o.clone(),
                            steps: vec![n],
                        });
                    }
                }
                if !known_event(pre, o)
                    && let Some(binding) = pre.binding(o.operation)
                    && let (Some(before), Some(after)) =
                        (order(pre, binding.order_id), order(post, binding.order_id))
                {
                    let id = binding.order_id;
                    if *outcome == ObservationOutcome::ReturnRequired && before.capture.is_none() {
                        require(
                            after.phase == OrderState::ReturnRequired
                                && after.capture.is_some()
                                && !after.owns,
                            "first ReturnRequired capture did not establish retained fact",
                        )?;
                        self.returns.entry(id).or_insert(ReturnHistory {
                            operation: o.operation,
                            capture: after.capture.unwrap(),
                            first: n,
                            duplicate: None,
                            mismatch: None,
                        });
                        if let Some(retry) = self.retries.get(&id)
                            && n > retry.step
                            && !pre.cancelled
                            && step.ctx.now_ms >= before.input.expires_at_ms
                            && retry.slot.operation == o.operation
                            && retry.slot.order_id == id
                        {
                            require(
                                pre.reservation(o.operation) == Some(retry.slot)
                                    && post.reservation(o.operation).is_none()
                                    && before.phase == OrderState::PaymentUnknown
                                    && before.owns
                                    && o.amount == before.input.amount
                                    && post.reservations.len() + 1 == pre.reservations.len()
                                    && post.events.len() == pre.events.len() + 1
                                    && post.budget() == pre.budget()
                                    && post.remaining() == pre.remaining() + quantity(before),
                                "late capture did not consume the retry's slot and release its inventory once",
                            )?;
                            self.hit(UNKNOWN_CHAIN, format!("order={id:?}; operation={:?}; slot={:?}; retry_step={}; capture_step={n}; event={:?}; expiry={}; capture_now={}; cancelled=false", o.operation, retry.slot, retry.step, event(o), before.input.expires_at_ms, step.ctx.now_ms));
                        }
                    }
                    if let Some(h) = self.returns.get_mut(&id)
                        && n > h.first
                    {
                        require(
                            before.phase == OrderState::ReturnRequired
                                && after.phase == before.phase
                                && before.capture == Some(h.capture)
                                && after.capture == before.capture
                                && !before.owns
                                && !after.owns
                                && pre.remaining() == post.remaining(),
                            "further ReturnRequired evidence changed capture/phase/inventory",
                        )?;
                        if *outcome == ObservationOutcome::DuplicateEffect
                            && o.amount == h.capture.amount
                            && event(o) != h.capture.identity
                        {
                            h.duplicate.get_or_insert((n, event(o)));
                        }
                        if *outcome == ObservationOutcome::Review
                            && !before.review
                            && o.amount != h.capture.amount
                            && let Some((duplicate_step, duplicate_event)) = h.duplicate
                            && n > duplicate_step
                            && event(o) != duplicate_event
                            && event(o) != h.capture.identity
                        {
                            require(
                                after.review,
                                "mismatching ReturnRequired evidence did not set review",
                            )?;
                            h.mismatch.get_or_insert((n, event(o)));
                        }
                    }
                }
            }
            (Action::Owner(_), Reply::Unit(Ok(()))) => {
                for h in self.quarantines.values_mut().filter(|h| h.steps.len() == 1) {
                    h.steps.push(n);
                }
            }
            (Action::Expire(id), Reply::Expire(Ok(true))) => {
                if let Some(h) = self.quarantines.get_mut(id)
                    && h.steps.len() == 2
                {
                    let before = order(pre, *id).ok_or("expiry missing order")?;
                    let after = order(post, *id).ok_or("expiry lost order")?;
                    require(
                        before.owns
                            && !after.owns
                            && before.phase == OrderState::Held
                            && after.phase == OrderState::Expired
                            && post.remaining() == pre.remaining() + quantity(before),
                        "quarantine sequence requires actual Held inventory release",
                    )?;
                    h.steps.push(n);
                }
            }
            (Action::Cancel(_), Reply::Unit(Ok(()))) => {
                for h in self.quarantines.values_mut().filter(|h| h.steps.len() == 3) {
                    h.steps.push(n);
                }
            }
            _ => {}
        }
        Ok(())
    }
}
