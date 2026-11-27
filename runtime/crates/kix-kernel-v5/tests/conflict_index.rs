mod common;

use common::{ctx, id, observation, reserve};
use kix_kernel_v5::{
    Inventory, Kernel, KernelError, Limits, ObservationOutcome, Rejection, ReserveOutcome,
};

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

fn request(n: u8, first: u16) -> kix_kernel_v5::Reserve {
    let mut value = reserve(n, first, 1);
    value.expires_at_ms = 1_000;
    value
}

#[test]
fn capacity_on_conflict_matches_the_v4_quarantine_rule() {
    let mut kernel = kernel(3, 1);
    let a = request(3, 0);
    let b = request(4, 1);
    kernel.reserve(ctx(1), a.clone()).unwrap();
    kernel.reserve(ctx(2), b.clone()).unwrap();
    kernel.observe_capture(ctx(3), observation(&a, 1)).unwrap();
    assert_eq!(
        kernel.observe_capture(ctx(4), observation(&b, 1)),
        Err(KernelError::Capacity)
    );
    assert!(kernel.order(a.order_id).unwrap().review_required);
    assert!(kernel.order(b.order_id).unwrap().review_required);
    assert_eq!(
        kernel.mark_payment_unknown(ctx(5), b.order_id),
        Err(KernelError::InvalidTransition)
    );
    assert_eq!(kernel.observation_count(), 1);
    assert!(kernel.conflicts().is_empty());
    assert_eq!(kernel.quarantined_operation_count(), 2);
}

#[test]
fn retained_unbound_identity_blocks_only_that_operation() {
    let mut kernel = kernel(4, 2);
    let a = request(3, 0);
    let unbound = request(4, 1);
    kernel.reserve(ctx(1), a.clone()).unwrap();
    kernel.observe_capture(ctx(2), observation(&a, 1)).unwrap();
    assert_eq!(
        kernel.observe_capture(ctx(3), observation(&unbound, 1)),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(kernel.conflicts().len(), 1);
    assert_eq!(kernel.quarantined_operation_count(), 1);
    assert_eq!(
        kernel.reserve(ctx(4), unbound.clone()).unwrap().original,
        ReserveOutcome::Rejected(Rejection::OperationQuarantined)
    );
    let mut other_account = request(5, 1);
    other_account.payment.account = id(22);
    assert_eq!(
        kernel
            .reserve(ctx(5), other_account.clone())
            .unwrap()
            .original,
        ReserveOutcome::Held(other_account.order_id)
    );
    assert_eq!(
        kernel.observe_capture(ctx(6), observation(&unbound, 1)),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(kernel.conflicts().len(), 1);
    assert!(kernel.order(unbound.order_id).is_none());
}

#[test]
fn unretained_unbound_identity_does_not_block_later_binding() {
    let mut kernel = kernel(3, 1);
    let a = request(3, 0);
    let unbound = request(4, 1);
    kernel.reserve(ctx(1), a.clone()).unwrap();
    kernel.observe_capture(ctx(2), observation(&a, 1)).unwrap();
    assert_eq!(
        kernel.observe_capture(ctx(3), observation(&unbound, 1)),
        Err(KernelError::Capacity)
    );
    assert!(kernel.conflicts().is_empty());
    assert_eq!(
        kernel.reserve(ctx(4), unbound.clone()).unwrap().original,
        ReserveOutcome::Held(unbound.order_id)
    );
    assert_eq!(
        kernel.observe_capture(ctx(5), observation(&unbound, 1)),
        Err(KernelError::Capacity)
    );
    assert!(kernel.order(unbound.order_id).unwrap().review_required);
    assert_eq!(kernel.quarantined_operation_count(), 2);
}

#[test]
fn index_keeps_distinct_conflicts_in_vector_order_and_replays_in_place() {
    let mut kernel = kernel(4, 8);
    let a = request(3, 0);
    kernel.reserve(ctx(1), a.clone()).unwrap();
    kernel.observe_capture(ctx(2), observation(&a, 1)).unwrap();
    let first = observation(&request(4, 1), 1);
    let mut second = observation(&request(4, 1), 1);
    second.amount = common::amount(1);
    let third = observation(&request(5, 2), 1);
    assert_eq!(
        kernel.observe_capture(ctx(3), first.clone()),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(
        kernel.observe_capture(ctx(4), second.clone()),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(
        kernel.observe_capture(ctx(5), third.clone()),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(
        kernel.observe_capture(ctx(6), second.clone()),
        Ok(ObservationOutcome::Conflict)
    );
    assert_eq!(kernel.conflicts(), &[first, second, third]);
    assert_eq!(
        kernel.reserve(ctx(7), request(4, 1)).unwrap().original,
        ReserveOutcome::Rejected(Rejection::OperationQuarantined)
    );
    assert_eq!(
        kernel.reserve(ctx(8), request(6, 3)).unwrap().original,
        ReserveOutcome::Held(id(6))
    );
}
