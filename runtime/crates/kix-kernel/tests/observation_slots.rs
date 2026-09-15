use kix_kernel::*;
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

fn id(n: u8) -> KixId {
    KixId::from_bytes([n; 16])
}

fn fence() -> ExecutionFence {
    ExecutionFence {
        owner: id(1),
        generation: 1,
    }
}

fn ctx(now_ms: u64) -> Context {
    Context {
        fence: fence(),
        now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

fn amount(atoms: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([7; 32]),
        atoms,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([8; 32]),
    )
    .unwrap()
}

fn kernel(observations: usize) -> Kernel {
    Kernel::new(
        id(9),
        fence(),
        1,
        Inventory::seats(&[10]).unwrap(),
        Limits {
            commands: 32,
            orders: 32,
            observations,
        },
    )
    .unwrap()
}

fn request(n: u8, first: u16) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(9),
            principal: id(2),
            request: id(n),
        },
        order_id: id(n),
        expected_business_epoch: 1,
        selection: Selection::Seats { first, count: 1 },
        amount: amount(10_000),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: 100,
        payment: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(n),
        },
    }
}

fn capture(request: &Reserve, event: u8) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([event; 32]),
    }
}

#[test]
fn full_observation_budget_blocks_first_unknown_without_state_change() {
    let mut k = kernel(1);
    let first = request(3, 0);
    let second = request(4, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    k.reserve(ctx(2), second.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&first, 1)).unwrap();
    let before = k.clone();
    let result = k.mark_payment_unknown(ctx(4), second.order_id);
    println!("full budget: mark_payment_unknown -> {result:?}");
    assert_eq!(result, Err(KernelError::Capacity));
    assert_eq!(k, before);
    assert_eq!(k.order(second.order_id).unwrap().state, OrderState::Held);
    assert_eq!(k.reserved_observation_count(), 0);
}

#[test]
fn repeated_unknown_reserves_once_and_other_operation_cannot_take_slot() {
    let mut k = kernel(1);
    let first = request(3, 0);
    let second = request(4, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    k.reserve(ctx(2), second.clone()).unwrap();
    k.mark_payment_unknown(ctx(3), first.order_id).unwrap();
    assert_eq!(k.reserved_observation_count(), 1);
    k.mark_payment_unknown(ctx(4), first.order_id).unwrap();
    assert_eq!(k.reserved_observation_count(), 1);
    let before = k.clone();
    assert_eq!(
        k.mark_payment_unknown(ctx(5), second.order_id),
        Err(KernelError::Capacity)
    );
    assert_eq!(k, before);
    assert_eq!(
        k.observe_capture(ctx(6), capture(&first, 1)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(k.observation_count(), 1);
    assert_eq!(
        k.order(first.order_id).unwrap().captured,
        Some(first.amount)
    );
}

#[test]
fn unrelated_event_flood_cannot_starve_promised_capture() {
    let mut k = kernel(2);
    let promised = request(3, 0);
    let unrelated = request(4, 1);
    k.reserve(ctx(1), promised.clone()).unwrap();
    k.reserve(ctx(2), unrelated.clone()).unwrap();
    k.mark_payment_unknown(ctx(3), promised.order_id).unwrap();
    k.observe_capture(ctx(4), capture(&unrelated, 1)).unwrap();
    let before = k.clone();
    assert_eq!(
        k.observe_capture(ctx(5), capture(&unrelated, 2)),
        Err(KernelError::Capacity)
    );
    assert_eq!(k, before);
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(
        k.observe_capture(ctx(6), capture(&promised, 3)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.observation_count(), 2);
    assert_eq!(k.reserved_observation_count(), 0);
}

#[test]
fn conflicting_event_cannot_spend_slot_reserved_for_capture() {
    let mut k = kernel(2);
    let first = request(3, 0);
    let second = request(4, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    k.reserve(ctx(2), second.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&first, 1)).unwrap();
    k.mark_payment_unknown(ctx(4), second.order_id).unwrap();
    let before = k.clone();
    assert_eq!(
        k.observe_capture(ctx(5), capture(&second, 1)),
        Err(KernelError::Capacity)
    );
    assert_eq!(k, before);
    assert_eq!(k.reserved_observation_count(), 1);
    assert!(k.conflicts().is_empty());
    assert_eq!(k.order(second.order_id).unwrap().captured, None);
    assert_eq!(
        k.observe_capture(ctx(6), capture(&second, 2)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.reserved_observation_count(), 0);
}

#[test]
fn accepted_conflict_keeps_slot_until_fresh_capture_preserves_reviewed_fact() {
    let mut k = kernel(3);
    let first = request(3, 0);
    let second = request(4, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    k.reserve(ctx(2), second.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&first, 1)).unwrap();
    k.mark_payment_unknown(ctx(4), second.order_id).unwrap();
    let conflict = capture(&second, 1);
    assert_eq!(
        k.observe_capture(ctx(5), conflict.clone()).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(k.conflicts(), std::slice::from_ref(&conflict));
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(k.order(second.order_id).unwrap().captured, None);
    assert!(k.order(first.order_id).unwrap().review_required);
    assert!(k.order(second.order_id).unwrap().review_required);
    assert_eq!(
        k.observe_capture(ctx(6), conflict).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(
        k.observe_capture(ctx(7), capture(&second, 2)).unwrap(),
        ObservationOutcome::Review
    );
    assert_eq!(k.observation_count(), 2);
    assert_eq!(k.conflicts().len(), 1);
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(
        k.order(second.order_id).unwrap().captured,
        Some(second.amount)
    );
    assert!(k.order(second.order_id).unwrap().review_required);
}

#[test]
fn reserved_slot_survives_expiry_check_owner_change_and_cancellation() {
    let mut k = kernel(1);
    let request = request(3, 0);
    k.reserve(ctx(1), request.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), request.order_id).unwrap();
    assert!(!k.expire(ctx(100), request.order_id).unwrap());
    assert_eq!(k.reserved_observation_count(), 1);
    let next = ExecutionFence {
        owner: id(8),
        generation: 2,
    };
    k.replace_owner(ctx(101), next).unwrap();
    let next_ctx = |now_ms| Context {
        fence: next,
        ..ctx(now_ms)
    };
    k.cancel_scope(next_ctx(102), 2).unwrap();
    assert_eq!(k.reserved_observation_count(), 1);
    // Cancellation fences new work; this UNKNOWN inventory remains owned
    // until the late capture is classified as requiring a return.
    assert_eq!(k.remaining(), 9);
    assert_eq!(
        k.observe_capture(next_ctx(103), capture(&request, 1))
            .unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(
        k.order(request.order_id).unwrap().captured,
        Some(request.amount)
    );
    assert_eq!(
        k.order(request.order_id).unwrap().state,
        OrderState::ReturnRequired
    );
    assert_eq!(k.remaining(), 10);
}

#[test]
fn mismatched_amount_uses_reserved_slot_and_preserves_actual_capture_for_review() {
    let mut k = kernel(1);
    let request = request(3, 0);
    k.reserve(ctx(1), request.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), request.order_id).unwrap();
    let mut observation = capture(&request, 1);
    observation.amount = amount(123);
    assert_eq!(
        k.observe_capture(ctx(3), observation.clone()).unwrap(),
        ObservationOutcome::Review
    );
    assert_eq!(k.observation_count(), 1);
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(
        k.order(request.order_id).unwrap().captured,
        Some(observation.amount)
    );
    assert!(k.order(request.order_id).unwrap().review_required);
}

#[test]
fn captured_operation_does_not_reserve_again_and_exact_event_replay_needs_no_slot() {
    let mut k = kernel(1);
    let request = request(3, 0);
    k.reserve(ctx(1), request.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), request.order_id).unwrap();
    k.observe_capture(ctx(3), capture(&request, 1)).unwrap();
    let before = k.clone();
    assert_eq!(
        k.mark_payment_unknown(ctx(4), request.order_id),
        Err(KernelError::InvalidTransition)
    );
    assert_eq!(k, before);
    assert_eq!(
        k.observe_capture(ctx(5), capture(&request, 1)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.observation_count(), 1);
    assert_eq!(k.reserved_observation_count(), 0);
    let before = k.clone();
    assert_eq!(
        k.observe_capture(ctx(6), capture(&request, 2)),
        Err(KernelError::Capacity)
    );
    assert_eq!(k, before);
}

#[test]
fn full_budget_new_conflict_remains_rejected_without_quarantine() {
    // This records the remaining A limitation, rather than claiming the new
    // send admission reservation also persists conflicts at full capacity.
    let mut k = kernel(1);
    let first = request(3, 0);
    let second = request(4, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    k.reserve(ctx(2), second.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&first, 1)).unwrap();
    let before = k.clone();
    let result = k.observe_capture(ctx(4), capture(&second, 1));
    println!("A full-budget conflict -> {result:?}");
    println!(
        "A review flags: first={}, second={}; observations={}, conflicts={}",
        k.order(first.order_id).unwrap().review_required,
        k.order(second.order_id).unwrap().review_required,
        k.observation_count(),
        k.conflicts().len()
    );
    assert_eq!(result, Err(KernelError::Capacity));
    assert_eq!(k, before);
    assert!(!k.order(first.order_id).unwrap().review_required);
    assert!(!k.order(second.order_id).unwrap().review_required);
    assert!(k.conflicts().is_empty());
}

#[test]
fn fresh_unbound_capture_remains_unstored_and_later_binding_is_not_reconciled() {
    // This records the remaining B limitation: no unmatched-payment inbox is
    // implemented by reserving room for already-bound external operations.
    let mut k = kernel(1);
    let request = request(3, 0);
    let observation = capture(&request, 1);
    let before = k.clone();
    let result = k.observe_capture(ctx(1), observation.clone());
    println!("B fresh unbound capture -> {result:?}");
    println!(
        "B stored counts: orders={}, observations={}, conflicts={}, reserved={}",
        k.order_count(),
        k.observation_count(),
        k.conflicts().len(),
        k.reserved_observation_count()
    );
    assert_eq!(result, Err(KernelError::UnknownOperation));
    assert_eq!(k, before);
    assert_eq!(k.observation_count(), 0);
    assert!(k.conflicts().is_empty());
    assert_eq!(
        k.reserve(ctx(2), request.clone()).unwrap().original,
        ReserveOutcome::Held(request.order_id)
    );
    assert_eq!(k.order(request.order_id).unwrap().captured, None);
    k.mark_payment_unknown(ctx(3), request.order_id).unwrap();
    assert_eq!(
        k.observe_capture(ctx(4), observation).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
}

#[test]
fn previous_semantics_version_is_rejected_without_silent_replay_change() {
    assert_eq!(SEMANTICS_VERSION, 2);
    let mut k = kernel(1);
    let before = k.clone();
    assert_eq!(
        k.reserve(
            Context {
                semantics_version: 1,
                ..ctx(1)
            },
            request(3, 0)
        ),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(k, before);
}
