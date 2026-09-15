use kix_kernel::*;
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

fn id(n: u8) -> KixId {
    KixId::from_bytes([n; 16])
}

fn ctx(now_ms: u64) -> Context {
    Context {
        fence: ExecutionFence {
            owner: id(1),
            generation: 1,
        },
        now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

fn kernel(orders: usize, observations: usize) -> Kernel {
    Kernel::new(
        id(9),
        ctx(0).fence,
        1,
        Inventory::seats(&[10]).unwrap(),
        Limits {
            commands: 32,
            orders,
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
        amount: AssetAmount::checked(
            AssetId::from_bytes([7; 32]),
            10_000,
            u128::MAX,
            RegistryVersion::new(1).unwrap(),
            Hash32::from_bytes([8; 32]),
        )
        .unwrap(),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: 1_000,
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
fn full_evidence_budget_still_quarantines_both_bound_operations() {
    let mut k = kernel(3, 1);
    let a = request(3, 0);
    let b = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();

    let conflict = k.observe_capture(ctx(4), capture(&b, 1));
    let review_a = k.order(a.order_id).unwrap().review_required;
    let review_b = k.order(b.order_id).unwrap().review_required;
    let send_b = k.mark_payment_unknown(ctx(5), b.order_id);
    println!("A/full_budget_new_conflict={conflict:?}");
    println!("A/review_a={review_a},review_b={review_b},send_b={send_b:?}");
    println!(
        "A/observations={},conflicts={},reserved={}",
        k.observation_count(),
        k.conflicts().len(),
        k.reserved_observation_count()
    );
    assert_eq!(conflict, Err(KernelError::Capacity));
    assert!(review_a && review_b);
    assert_eq!(send_b, Err(KernelError::InvalidTransition));
    assert_eq!(k.observation_count(), 1);
    assert!(k.conflicts().is_empty());
    assert_eq!(k.quarantined_operation_count(), 2);
}

#[test]
fn full_budget_quarantine_preserves_the_already_promised_capture_slot() {
    let mut k = kernel(3, 2);
    let a = request(3, 0);
    let b = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
    k.mark_payment_unknown(ctx(4), b.order_id).unwrap();
    assert_eq!(
        k.observe_capture(ctx(5), capture(&b, 1)),
        Err(KernelError::Capacity)
    );
    assert!(k.order(a.order_id).unwrap().review_required);
    assert!(k.order(b.order_id).unwrap().review_required);
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(
        k.mark_payment_unknown(ctx(6), b.order_id),
        Err(KernelError::InvalidTransition)
    );
    assert_eq!(
        k.observe_capture(ctx(7), capture(&b, 2)),
        Ok(ObservationOutcome::Review)
    );
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(k.order(b.order_id).unwrap().captured, Some(b.amount));
    assert_eq!(k.order(b.order_id).unwrap().state, OrderState::Review);
    assert!(k.order(b.order_id).unwrap().review_required);
    assert_eq!(k.observation_count(), 2);
    assert!(k.conflicts().is_empty());
}

#[test]
fn many_unbound_conflicts_trip_bounded_scope_quarantine_without_losing_slots() {
    // Retain this former regression's name so the same test selector exercises
    // the repaired behavior: rejected unbound identities cannot fence the scope.
    let mut k = kernel(3, 2);
    let a = request(3, 0);
    let b = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
    k.mark_payment_unknown(ctx(4), b.order_id).unwrap();

    for n in 10_u8..30 {
        let unseen = request(n, 2);
        assert_eq!(
            k.observe_capture(ctx(u64::from(n)), capture(&unseen, 1)),
            Err(KernelError::Capacity)
        );
        assert_eq!(k.quarantined_operation_count(), 1);
    }
    let review_a = k.order(a.order_id).unwrap().review_required;
    let review_b = k.order(b.order_id).unwrap().review_required;
    let reserved_before_capture = k.reserved_observation_count();
    let send_b = k.mark_payment_unknown(ctx(30), b.order_id);
    // This operation has never been named in any conflict.
    let new_reservation = k.reserve(ctx(31), request(40, 2)).unwrap().original;
    println!(
        "unbound_conflicts/calls=20,quarantined_bound={}",
        k.quarantined_operation_count()
    );
    println!("unbound_conflicts/review_a={review_a},review_b={review_b},send_b={send_b:?}");
    println!(
        "unbound_conflicts/new_reservation={new_reservation:?},reserved_before_capture={reserved_before_capture}"
    );
    assert!(review_a);
    assert!(!review_b);
    assert_eq!(send_b, Ok(()));
    assert_eq!(new_reservation, ReserveOutcome::Held(id(40)));
    assert_eq!(reserved_before_capture, 1);
    assert_eq!(k.order_count(), 3);
    assert_eq!(
        k.observe_capture(ctx(32), capture(&b, 2)),
        Ok(ObservationOutcome::PaymentConfirmed)
    );
    println!(
        "unbound_conflicts/reserved_after_capture={}",
        k.reserved_observation_count()
    );
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(k.quarantined_operation_count(), 1);
    assert!(!k.order(b.order_id).unwrap().review_required);
    assert!(k.conflicts().is_empty());
}

#[test]
fn retained_unbound_conflict_blocks_future_binding_without_expanding_bound_set() {
    let mut k = kernel(4, 2);
    let a = request(3, 0);
    let unbound = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.observe_capture(ctx(2), capture(&a, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(3), capture(&unbound, 1)),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(k.conflicts().len(), 1);
    assert_eq!(k.quarantined_operation_count(), 1);
    assert_eq!(
        k.reserve(ctx(4), unbound.clone()).unwrap().original,
        ReserveOutcome::Rejected(Rejection::OperationQuarantined)
    );
    // The guard uses the complete provider/account/operation identity.
    let mut other_account = request(5, 1);
    other_account.payment = ProviderOperation {
        account: id(22),
        ..unbound.payment
    };
    assert_eq!(
        k.reserve(ctx(5), other_account.clone()).unwrap().original,
        ReserveOutcome::Held(other_account.order_id)
    );
    // Replaying the retained evidence cannot turn its identity into a new order.
    assert_eq!(
        k.observe_capture(ctx(6), capture(&unbound, 1)),
        Ok(ObservationOutcome::Conflict)
    );
    let replay = k.reserve(ctx(7), unbound.clone()).unwrap();
    assert!(replay.replayed);
    assert_eq!(
        replay.original,
        ReserveOutcome::Rejected(Rejection::OperationQuarantined)
    );
    assert!(k.order(unbound.order_id).is_none());
    assert_eq!(k.conflicts().len(), 1);
    assert_eq!(k.quarantined_operation_count(), 1);
}

#[test]
fn unretained_unbound_conflict_creates_no_speculative_binding_ban() {
    let mut k = kernel(3, 1);
    let a = request(3, 0);
    let unbound = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.observe_capture(ctx(2), capture(&a, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(3), capture(&unbound, 1)),
        Err(KernelError::Capacity)
    );
    assert!(k.order(a.order_id).unwrap().review_required);
    assert_eq!(k.quarantined_operation_count(), 1);
    assert!(k.conflicts().is_empty());
    assert_eq!(
        k.reserve(ctx(4), unbound.clone()).unwrap().original,
        ReserveOutcome::Held(unbound.order_id)
    );
    assert!(!k.order(unbound.order_id).unwrap().review_required);
    // Once bound, a repeated conflict must quarantine it despite full evidence.
    assert_eq!(
        k.observe_capture(ctx(5), capture(&unbound, 1)),
        Err(KernelError::Capacity)
    );
    assert!(k.order(unbound.order_id).unwrap().review_required);
    assert_eq!(k.quarantined_operation_count(), 2);
    assert_eq!(
        k.mark_payment_unknown(ctx(6), unbound.order_id),
        Err(KernelError::InvalidTransition)
    );
}

#[test]
fn rejected_evidence_that_quarantines_also_advances_logical_time() {
    let mut k = kernel(3, 1);
    let a = request(3, 0);
    let b = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(500), capture(&b, 1)),
        Err(KernelError::Capacity)
    );
    let before = k.clone();
    assert_eq!(
        k.reserve(ctx(499), request(5, 2)),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(
        k.mark_payment_unknown(ctx(499), b.order_id),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(k, before);
}

#[test]
fn original_event_and_command_replays_never_clear_quarantine() {
    let mut k = kernel(3, 1);
    let a = request(3, 0);
    let b = request(4, 1);
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(4), capture(&b, 1)),
        Err(KernelError::Capacity)
    );
    assert_eq!(
        k.observe_capture(ctx(5), capture(&a, 1)),
        Ok(ObservationOutcome::PaymentConfirmed)
    );
    let original = k.reserve(ctx(6), b.clone()).unwrap();
    assert!(original.replayed);
    assert_eq!(original.original, ReserveOutcome::Held(b.order_id));
    assert!(k.order(a.order_id).unwrap().review_required);
    assert!(k.order(b.order_id).unwrap().review_required);
    assert_eq!(
        k.mark_payment_unknown(ctx(7), b.order_id),
        Err(KernelError::InvalidTransition)
    );
    assert_eq!(k.quarantined_operation_count(), 2);
    assert_eq!(k.observation_count(), 1);
    assert!(k.conflicts().is_empty());
}

#[test]
fn v3_inputs_are_rejected_before_any_state_change() {
    assert_eq!(SEMANTICS_VERSION, 4);
    let mut k = kernel(3, 1);
    let before = k.clone();
    let v3 = Context {
        semantics_version: 3,
        ..ctx(1)
    };
    let a = request(3, 0);
    assert_eq!(
        k.reserve(v3, a.clone()),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(
        k.observe_capture(v3, capture(&a, 1)),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(k, before);
}
