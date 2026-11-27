mod common;

use common::{amount, ctx, engine, id, observation, open_unknown, reserve, terminate_for};
use kix_kernel_v5::{
    DAY_MS, HoldKind, Inventory, Kernel, KernelError, Limits, ObservationOutcome, OrderState,
    ReclaimPolicy,
};

#[test]
fn expiry_cancel_owner_change_and_termination_keep_the_reserved_slot() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    assert_eq!(kernel.reserved_observation_count(), 1);
    assert!(!kernel.expire(ctx(100), id(3)).unwrap());
    assert_eq!(kernel.reserved_observation_count(), 1);
    assert_eq!(
        kernel.order(id(3)).unwrap().state,
        OrderState::PaymentUnknown
    );

    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel.cancel_scope(ctx(3), 2).unwrap();
    assert_eq!(kernel.reserved_observation_count(), 1);

    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel
        .replace_owner(
            ctx(3),
            kix_kernel_v5::ExecutionFence {
                owner: id(8),
                generation: 2,
            },
        )
        .unwrap();
    assert_eq!(kernel.reserved_observation_count(), 1);

    let mut kernel = engine();
    open_unknown(&mut kernel);
    let remaining = kernel.remaining();
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    assert_eq!(kernel.reserved_observation_count(), 1);
    assert_eq!(kernel.remaining(), remaining);
    assert!(!kernel.order(id(3)).unwrap().review_required);
    assert!(kernel.order(id(3)).unwrap().inventory_owned);
}

#[test]
fn reserved_to_stored_capture_does_not_shrink_the_total_budget() {
    let mut kernel = Kernel::new(
        id(9),
        ctx(0).fence,
        1,
        Inventory::seats(&[4]).unwrap(),
        Limits {
            commands: 8,
            orders: 4,
            observations: 1,
        },
    )
    .unwrap();
    let first = reserve(3, 0, 1);
    let second = reserve(4, 1, 1);
    kernel.reserve(ctx(1), first.clone()).unwrap();
    kernel.reserve(ctx(2), second).unwrap();
    kernel.mark_payment_unknown(ctx(3), id(3)).unwrap();
    assert_eq!(kernel.reserved_observation_count(), 1);
    assert_eq!(kernel.observation_count(), 0);
    assert_eq!(
        kernel.mark_payment_unknown(ctx(4), id(4)),
        Err(KernelError::Capacity)
    );
    assert_eq!(
        kernel
            .observe_capture(ctx(5), observation(&first, 1))
            .unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(kernel.reserved_observation_count(), 0);
    assert_eq!(kernel.observation_count(), 1);
    assert!(kernel.conflicts().is_empty());
    assert_eq!(
        kernel.mark_payment_unknown(ctx(6), id(4)),
        Err(KernelError::Capacity)
    );
}

#[test]
fn redelivery_never_clears_review_required() {
    let mut kernel = engine();
    let first = reserve(3, 1, 1);
    let second = reserve(4, 2, 1);
    kernel.reserve(ctx(1), first.clone()).unwrap();
    kernel.reserve(ctx(2), second.clone()).unwrap();
    kernel
        .observe_capture(ctx(3), observation(&first, 1))
        .unwrap();
    let conflict = observation(&second, 1);
    assert_eq!(
        kernel.observe_capture(ctx(4), conflict.clone()).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(
        kernel.observe_capture(ctx(5), conflict).unwrap(),
        ObservationOutcome::Conflict
    );
    assert!(kernel.order(first.order_id).unwrap().review_required);
    assert!(kernel.order(second.order_id).unwrap().review_required);
    assert_eq!(
        kernel
            .observe_capture(ctx(6), observation(&second, 2))
            .unwrap(),
        ObservationOutcome::Review
    );
    assert!(kernel.order(second.order_id).unwrap().review_required);
    assert_eq!(
        kernel.order(second.order_id).unwrap().state,
        OrderState::Review
    );
}

#[test]
fn return_required_plus_late_mismatch_keeps_both_markers() {
    let mut kernel = engine();
    let first = reserve(3, 1, 1);
    let second = reserve(4, 2, 1);
    kernel.reserve(ctx(1), first.clone()).unwrap();
    kernel.reserve(ctx(2), second.clone()).unwrap();
    kernel
        .observe_capture(ctx(3), observation(&first, 1))
        .unwrap();
    assert_eq!(
        kernel
            .observe_capture(ctx(4), observation(&second, 1))
            .unwrap(),
        ObservationOutcome::Conflict
    );
    assert!(kernel.expire(ctx(100), second.order_id).unwrap());
    assert_eq!(
        kernel
            .observe_capture(ctx(101), observation(&second, 2))
            .unwrap(),
        ObservationOutcome::ReturnRequired
    );
    let mut mismatch = observation(&second, 3);
    mismatch.amount = amount(1);
    let remaining = kernel.remaining();
    assert_eq!(
        kernel.observe_capture(ctx(102), mismatch).unwrap(),
        ObservationOutcome::Review
    );
    let order = kernel.order(second.order_id).unwrap();
    assert_eq!(order.state, OrderState::ReturnRequired);
    assert!(order.review_required);
    assert_eq!(order.captured, Some(second.amount));
    assert!(!order.inventory_owned);
    assert_eq!(kernel.remaining(), remaining);
}

#[test]
fn hold_report_and_clear_release_no_slot_inventory_review_or_evidence() {
    let mut kernel = engine();
    let request = open_unknown(&mut kernel);
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    kernel
        .place_hold(ctx(4), id(3), id(60), HoldKind::Legal, id(50))
        .unwrap();
    let before = (
        kernel.order(id(3)).cloned(),
        kernel.remaining(),
        kernel.order_count(),
        kernel.observation_count(),
        kernel.reserved_observation_count(),
        kernel.conflicts().len(),
        kernel.quarantined_operation_count(),
    );
    let policy = ReclaimPolicy::default();
    // Far past every default window, with and without the hold.
    kernel
        .reclaim_report(9_000 * DAY_MS, id(3), &policy)
        .unwrap();
    kernel.reclaim_reports(9_000 * DAY_MS, &policy).unwrap();
    kernel.clear_hold(ctx(5), id(60), id(51)).unwrap();
    kernel
        .reclaim_report(9_000 * DAY_MS, id(3), &policy)
        .unwrap();
    let after = (
        kernel.order(id(3)).cloned(),
        kernel.remaining(),
        kernel.order_count(),
        kernel.observation_count(),
        kernel.reserved_observation_count(),
        kernel.conflicts().len(),
        kernel.quarantined_operation_count(),
    );
    assert_eq!(before, after);
    assert_eq!(kernel.reserved_observation_count(), 1);
    assert!(kernel.termination(id(3)).is_some());
    // The reservation still answers from the stored first result.
    assert!(kernel.reserve(ctx(6), request).unwrap().replayed);
}
