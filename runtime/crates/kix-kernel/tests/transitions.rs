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
fn limits() -> Limits {
    Limits {
        commands: 1_024,
        orders: 1_024,
        observations: 1_024,
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
fn engine() -> Kernel {
    Kernel::new(
        id(9),
        fence(),
        1,
        Inventory::seats(&[70, 10]).unwrap(),
        limits(),
    )
    .unwrap()
}
fn reserve(n: u8, first: u16, count: u16) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(9),
            principal: id(2),
            request: id(n),
        },
        order_id: id(n),
        expected_business_epoch: 1,
        selection: Selection::Seats { first, count },
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
fn observation(request: &Reserve, event: u8) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([event; 32]),
    }
}
fn held(result: AppliedReservation, order: u8) {
    assert_eq!(result.original, ReserveOutcome::Held(id(order)));
}

#[test]
fn reservation_has_inventory_order_and_stable_external_intent() {
    let mut k = engine();
    let r = reserve(3, 1, 2);
    held(k.reserve(ctx(1), r.clone()).unwrap(), 3);
    let order = k.order(id(3)).unwrap();
    assert_eq!(order.request, r);
    assert_eq!(order.submitted_under, fence());
    assert!(order.inventory_owned);
    assert_eq!(k.remaining(), 78);
    assert_eq!(k.order_count(), 1);
}

#[test]
fn overlapping_bundle_rejection_never_partially_allocates() {
    let mut k = engine();
    held(k.reserve(ctx(1), reserve(3, 1, 2)).unwrap(), 3);
    assert_eq!(
        k.reserve(ctx(2), reserve(4, 2, 2)).unwrap().original,
        ReserveOutcome::Rejected(Rejection::Unavailable)
    );
    assert_eq!(k.remaining(), 78);
    held(k.reserve(ctx(3), reserve(5, 3, 1)).unwrap(), 5);
}

#[test]
fn sixty_four_bit_word_boundary_is_not_an_aisle() {
    let mut k = engine();
    held(k.reserve(ctx(1), reserve(3, 63, 2)).unwrap(), 3);
    assert_eq!(
        k.reserve(ctx(2), reserve(4, 64, 1)).unwrap().original,
        ReserveOutcome::Rejected(Rejection::Unavailable)
    );
}

#[test]
fn actual_segment_boundary_is_an_aisle() {
    let mut k = engine();
    assert_eq!(
        k.reserve(ctx(1), reserve(3, 69, 2)).unwrap().original,
        ReserveOutcome::Rejected(Rejection::InvalidRequest)
    );
    assert_eq!(k.remaining(), 80);
}

#[test]
fn overflow_empty_and_oversize_selections_fail_without_inventory_change() {
    for (first, count) in [(u16::MAX, 2), (0, 0), (0, MAX_BUNDLE + 1), (80, 1)] {
        let mut k = engine();
        assert_eq!(
            k.reserve(ctx(1), reserve(3, first, count))
                .unwrap()
                .original,
            ReserveOutcome::Rejected(Rejection::InvalidRequest)
        );
        assert_eq!(k.remaining(), 80);
        assert_eq!(k.order_count(), 0);
    }
}

#[test]
fn general_admission_never_overdraws_and_expiry_is_single_release() {
    let mut k = Kernel::new(
        id(9),
        fence(),
        1,
        Inventory::general_admission(5).unwrap(),
        limits(),
    )
    .unwrap();
    let mut r = reserve(3, 0, 1);
    r.selection = Selection::GeneralAdmission { count: 4 };
    held(k.reserve(ctx(1), r).unwrap(), 3);
    let mut r2 = reserve(4, 0, 1);
    r2.selection = Selection::GeneralAdmission { count: 2 };
    assert_eq!(
        k.reserve(ctx(2), r2).unwrap().original,
        ReserveOutcome::Rejected(Rejection::Unavailable)
    );
    assert_eq!(k.remaining(), 1);
    assert!(k.expire(ctx(100), id(3)).unwrap());
    assert!(!k.expire(ctx(101), id(3)).unwrap());
    assert_eq!(k.remaining(), 5);
}

#[test]
fn response_loss_retry_returns_original_before_availability_check() {
    let mut k = engine();
    let r = reserve(3, 1, 2);
    let first = k.reserve(ctx(1), r.clone()).unwrap();
    let retry = k.reserve(ctx(2), r).unwrap();
    assert_eq!(retry.original, first.original);
    assert!(retry.replayed);
    assert_eq!(k.remaining(), 78);
}

#[test]
fn identical_id_with_changed_payload_is_a_conflict() {
    let mut k = engine();
    let mut r = reserve(3, 1, 2);
    k.reserve(ctx(1), r.clone()).unwrap();
    r.amount = amount(20_000);
    let before = k.clone();
    assert_eq!(k.reserve(ctx(2), r), Err(KernelError::CommandConflict));
    assert_eq!(k, before);
}

#[test]
fn ownership_generation_does_not_change_command_identity() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    let next = ExecutionFence {
        owner: id(8),
        generation: 2,
    };
    k.replace_owner(ctx(2), next).unwrap();
    assert!(
        k.reserve(
            Context {
                fence: next,
                ..ctx(3)
            },
            r.clone()
        )
        .unwrap()
        .replayed
    );
    // Stored immutable results remain available even on an old routed retry.
    assert!(k.reserve(ctx(3), r).unwrap().replayed);
    assert_eq!(
        k.reserve(ctx(3), reserve(4, 3, 1)),
        Err(KernelError::ExecutionFenced)
    );
}

#[test]
fn expired_hold_retry_keeps_original_result_and_separate_current_state() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.expire(ctx(100), id(3)).unwrap();
    held(k.reserve(ctx(101), r).unwrap(), 3);
    assert_eq!(k.order(id(3)).unwrap().state, OrderState::Expired);
    assert_eq!(k.remaining(), 80);
}

#[test]
fn unknown_payment_is_not_released_by_ttl() {
    let mut k = engine();
    k.reserve(ctx(1), reserve(3, 1, 1)).unwrap();
    k.mark_payment_unknown(ctx(2), id(3)).unwrap();
    assert!(!k.expire(ctx(100), id(3)).unwrap());
    assert_eq!(k.order(id(3)).unwrap().state, OrderState::PaymentUnknown);
    assert_eq!(k.remaining(), 79);
}

#[test]
fn local_cancellation_blocks_new_reservations_but_not_original_results() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.cancel_scope(ctx(2), 2).unwrap();
    assert!(k.reserve(ctx(3), r).unwrap().replayed);
    assert_eq!(
        k.reserve(ctx(4), reserve(4, 2, 1)).unwrap().original,
        ReserveOutcome::Rejected(Rejection::BusinessFenced)
    );
}

#[test]
fn historical_capture_after_owner_change_is_not_discarded() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), id(3)).unwrap();
    let next = ExecutionFence {
        owner: id(8),
        generation: 2,
    };
    k.replace_owner(ctx(3), next).unwrap();
    assert_eq!(
        k.observe_capture(
            Context {
                fence: next,
                ..ctx(4)
            },
            observation(&r, 1)
        )
        .unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.order(id(3)).unwrap().submitted_under, fence());
}

#[test]
fn late_capture_after_expiry_and_resale_does_not_release_new_buyer() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.expire(ctx(100), id(3)).unwrap();
    let mut next = reserve(4, 1, 1);
    next.expires_at_ms = 200;
    k.reserve(ctx(101), next).unwrap();
    assert_eq!(
        k.observe_capture(ctx(102), observation(&r, 1)).unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(k.remaining(), 79);
    assert!(k.order(id(4)).unwrap().inventory_owned);
    assert_eq!(k.order(id(3)).unwrap().captured, Some(r.amount));
}

#[test]
fn late_capture_after_cancellation_creates_return_marker_not_resurrection() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), id(3)).unwrap();
    k.cancel_scope(ctx(3), 2).unwrap();
    assert_eq!(
        k.observe_capture(ctx(4), observation(&r, 1)).unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(k.order(id(3)).unwrap().state, OrderState::ReturnRequired);
    assert_eq!(k.remaining(), 80);
}

#[test]
fn event_deduplication_and_economic_effect_deduplication_are_separate() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    assert_eq!(
        k.observe_capture(ctx(2), observation(&r, 1)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(
        k.observe_capture(ctx(3), observation(&r, 1)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(
        k.observe_capture(ctx(4), observation(&r, 2)).unwrap(),
        ObservationOutcome::DuplicateEffect
    );
    assert_eq!(k.observation_count(), 2);
    assert_eq!(k.order(id(3)).unwrap().captured, Some(r.amount));
}

#[test]
fn same_event_different_payload_preserves_conflicting_evidence() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.observe_capture(ctx(2), observation(&r, 1)).unwrap();
    let mut conflict = observation(&r, 1);
    conflict.amount = amount(1);
    assert_eq!(
        k.observe_capture(ctx(3), conflict.clone()).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(
        k.observe_capture(ctx(4), conflict.clone()).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(k.conflicts(), &[conflict]);
    assert!(k.order(id(3)).unwrap().review_required);
    assert_eq!(k.order(id(3)).unwrap().captured, Some(r.amount));
}

#[test]
fn mismatched_asset_or_registry_is_recorded_for_review_not_paid() {
    let mut k = engine();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    let mut obs = observation(&r, 1);
    obs.amount = AssetAmount::checked(
        AssetId::from_bytes([99; 32]),
        10_000,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([8; 32]),
    )
    .unwrap();
    assert_eq!(
        k.observe_capture(ctx(2), obs.clone()).unwrap(),
        ObservationOutcome::Review
    );
    assert_eq!(k.order(id(3)).unwrap().captured, Some(obs.amount));
    assert!(k.order(id(3)).unwrap().review_required);
}

#[test]
fn duplicate_external_operation_cannot_fund_two_orders() {
    let mut k = engine();
    let first = reserve(3, 1, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    let mut second = reserve(4, 2, 1);
    second.payment = first.payment;
    assert_eq!(
        k.reserve(ctx(2), second).unwrap().original,
        ReserveOutcome::Rejected(Rejection::OperationAlreadyBound)
    );
    assert_eq!(k.order_count(), 1);
}

#[test]
fn bounded_records_backpressure_without_evicting_old_results() {
    let mut cap = limits();
    cap.commands = 1;
    let mut k = Kernel::new(id(9), fence(), 1, Inventory::seats(&[10]).unwrap(), cap).unwrap();
    let r = reserve(3, 1, 1);
    k.reserve(ctx(1), r.clone()).unwrap();
    let before = k.clone();
    assert_eq!(
        k.reserve(ctx(2), reserve(4, 2, 1)),
        Err(KernelError::Capacity)
    );
    assert_eq!(k, before);
    assert!(k.reserve(ctx(3), r).unwrap().replayed);
}

#[test]
fn unknown_semantics_and_regressed_time_are_not_applied() {
    let mut k = engine();
    k.reserve(ctx(10), reserve(3, 1, 1)).unwrap();
    let before = k.clone();
    assert_eq!(
        k.reserve(ctx(9), reserve(4, 2, 1)),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(
        k.reserve(
            Context {
                semantics_version: 2,
                ..ctx(11)
            },
            reserve(4, 2, 1)
        ),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(k, before);
}

#[test]
fn u128_max_is_not_narrowed() {
    let mut k = engine();
    let mut r = reserve(3, 1, 1);
    r.amount = amount(u128::MAX);
    k.reserve(ctx(1), r.clone()).unwrap();
    k.observe_capture(ctx(2), observation(&r, 1)).unwrap();
    assert_eq!(k.order(id(3)).unwrap().captured.unwrap().atoms(), u128::MAX);
}

#[test]
fn replaying_ordered_inputs_reconstructs_identical_state() {
    fn replay() -> Kernel {
        let mut k = engine();
        let first = reserve(3, 63, 2);
        k.reserve(ctx(1), first.clone()).unwrap();
        k.reserve(ctx(2), reserve(4, 64, 2)).unwrap();
        k.mark_payment_unknown(ctx(3), id(3)).unwrap();
        k.cancel_scope(ctx(4), 2).unwrap();
        k.observe_capture(ctx(5), observation(&first, 1)).unwrap();
        k.reserve(ctx(6), first).unwrap();
        k
    }
    // This is semantic replay, NOT a disk or leader-crash test.
    assert_eq!(replay(), replay());
}

#[test]
fn invalid_inventory_configuration_is_rejected() {
    assert!(Inventory::seats(&[0]).is_err());
    assert!(Inventory::seats(&[MAX_SEATS, 1]).is_err());
    assert!(Inventory::general_admission(0).is_err());
    let forged = Inventory::GeneralAdmission {
        capacity: 1,
        remaining: 2,
    };
    assert_eq!(
        Kernel::new(id(9), fence(), 1, forged, limits()),
        Err(KernelError::InvalidConfiguration)
    );
}
