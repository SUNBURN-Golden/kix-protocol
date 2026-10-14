mod common;

use common::{amount, ctx, ga_reserve, id, page, reserve, show};
use kix_delegated_exec::{DelegatedShow, MappingError, PageKind, RangeTable};
use kix_kernel_v5::{
    CaptureObservation, KernelError, MAX_BUNDLE, ObservationOutcome, OrderState, ProviderOperation,
    Rejection, ReserveOutcome, Selection,
};
use kix_types::Hash32;

fn two_page_seat_show() -> DelegatedShow {
    // A 7,000-seat show: two seat pages, each legal for one kernel.
    show(
        RangeTable::new(&[
            page(0, 0, 4_096, PageKind::Seat),
            page(1, 4_096, 7_000, PageKind::Seat),
        ])
        .unwrap(),
    )
}

#[test]
fn show_above_max_seats_routes_to_the_owning_page() {
    let mut show = two_page_seat_show();

    // Both sides of the page boundary hold independently.
    let held = show.reserve(ctx(1), &reserve(1, 4_095, 1)).unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(1)));
    let held = show.reserve(ctx(2), &reserve(2, 4_096, 2)).unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(2)));

    // The stored kernel command carries the page scope and a kernel-local
    // seat index: show slot 4,095 is seat 4,095 of page 0, and show slot
    // 4,096 is seat 0 of page 1.
    let first = show.order(id(1)).unwrap();
    assert_eq!(
        first.request.selection,
        Selection::Seats {
            first: 4_095,
            count: 1
        }
    );
    assert_eq!(first.request.id.scope, id(100)); // page 0 scope
    let second = show.order(id(2)).unwrap();
    assert_eq!(
        second.request.selection,
        Selection::Seats { first: 0, count: 2 }
    );
    assert_eq!(second.request.id.scope, id(101)); // page 1 scope

    assert_eq!(show.remaining(0), Some(4_095));
    assert_eq!(show.remaining(1), Some(2_904 - 2));
    assert_eq!(show.total_remaining(), 7_000 - 3);
}

#[test]
fn bundle_bound_is_the_kernel_max_bundle() {
    let mut show = two_page_seat_show();
    show.reserve(ctx(1), &reserve(1, 0, MAX_BUNDLE)).unwrap();

    let before = (show.remaining(0), show.remaining(1));
    assert_eq!(
        show.reserve(ctx(2), &reserve(2, 0, MAX_BUNDLE + 1)),
        Err(MappingError::BundleTooLarge)
    );
    assert_eq!((show.remaining(0), show.remaining(1)), before);
}

#[test]
fn a_bundle_may_not_cross_a_page_boundary() {
    let mut show = two_page_seat_show();
    let before = (
        show.remaining(0),
        show.remaining(1),
        show.page_kernel(0).unwrap().order_count(),
        show.page_kernel(1).unwrap().order_count(),
    );
    // Slots 4,095 and 4,096 are held by different pages; no partial effects.
    assert_eq!(
        show.reserve(ctx(1), &reserve(1, 4_095, 2)),
        Err(MappingError::CrossPageBundle)
    );
    assert_eq!(
        (
            show.remaining(0),
            show.remaining(1),
            show.page_kernel(0).unwrap().order_count(),
            show.page_kernel(1).unwrap().order_count(),
        ),
        before
    );
}

#[test]
fn slots_without_a_seat_page_are_unknown() {
    let mut show = show(
        RangeTable::new(&[
            page(0, 0, 100, PageKind::Seat),
            page(1, 100, 200, PageKind::Ga),
        ])
        .unwrap(),
    );
    // Outside every range.
    assert_eq!(
        show.reserve(ctx(1), &reserve(1, 300, 1)),
        Err(MappingError::UnknownSlot)
    );
    // Covered, but by a GA page: the slot is not a seat.
    assert_eq!(
        show.reserve(ctx(2), &reserve(2, 150, 1)),
        Err(MappingError::UnknownSlot)
    );
}

#[test]
fn ga_requests_route_to_the_lowest_start_page_that_can_serve_them() {
    let mut show = show(
        RangeTable::new(&[
            page(0, 0, 4_096, PageKind::Seat),
            page(1, 4_096, 4_100, PageKind::Ga), // capacity 4
            page(2, 4_100, 4_300, PageKind::Ga), // capacity 200
        ])
        .unwrap(),
    );
    // Page 1 can serve 2; page 2 is untouched.
    show.reserve(ctx(1), &ga_reserve(1, 2)).unwrap();
    assert_eq!(show.remaining(1), Some(2));
    assert_eq!(show.remaining(2), Some(200));
    // Page 1 cannot serve 5; the request lands on page 2.
    show.reserve(ctx(2), &ga_reserve(2, 5)).unwrap();
    assert_eq!(show.remaining(1), Some(2));
    assert_eq!(show.remaining(2), Some(195));
}

#[test]
fn a_command_scope_other_than_the_shows_is_wrong_scope() {
    let mut show = two_page_seat_show();
    let mut request = reserve(1, 0, 1);
    request.id.scope = id(99);
    assert_eq!(
        show.reserve(ctx(1), &request),
        Err(MappingError::WrongScope)
    );
    assert_eq!(show.total_remaining(), 7_000);
}

#[test]
fn kernel_rejections_pass_through_with_the_command_record() {
    let mut show = two_page_seat_show();
    // Wrong expected business epoch is a stored kernel rejection, not a
    // mapping error; an identical retry replays it.
    let mut request = reserve(1, 0, 1);
    request.expected_business_epoch = 2;
    let rejected = show.reserve(ctx(1), &request).unwrap();
    assert_eq!(
        rejected.original,
        ReserveOutcome::Rejected(kix_kernel_v5::Rejection::BusinessFenced)
    );
    assert!(!rejected.replayed);
    let replay = show.reserve(ctx(2), &request).unwrap();
    assert_eq!(replay.original, rejected.original);
    assert!(replay.replayed);
    assert_eq!(show.page_kernel(0).unwrap().order_count(), 0);
}

#[test]
fn a_payment_operation_binds_at_most_one_order_across_pages() {
    let mut show = two_page_seat_show();
    // The first reserve binds the operation on page 0.
    let held = show.reserve(ctx(1), &reserve(1, 0, 1)).unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(1)));

    // A different command carrying the same payment operation routed to a
    // different page gets the kernel's own rejection value, binds nothing
    // on page 1, and stores no record there.
    let mut second = reserve(2, 4_096, 1);
    second.payment = reserve(1, 0, 1).payment;
    let rejected = show.reserve(ctx(2), &second).unwrap();
    assert_eq!(
        rejected.original,
        ReserveOutcome::Rejected(Rejection::OperationAlreadyBound)
    );
    assert!(!rejected.replayed);
    assert!(show.order(id(2)).is_none());
    assert_eq!(show.remaining(1), Some(2_904));
    assert_eq!(show.page_kernel(1).unwrap().order_count(), 0);
    // A kernel never unbinds an operation, so an identical retry answers
    // the same synthesized rejection.
    let retry = show.reserve(ctx(3), &second).unwrap();
    assert_eq!(retry.original, rejected.original);
    assert!(!retry.replayed);

    // On the bound page itself the kernel's own stored rejection answers
    // and replays.
    let mut third = reserve(3, 5, 1);
    third.payment = reserve(1, 0, 1).payment;
    let rejected = show.reserve(ctx(4), &third).unwrap();
    assert_eq!(
        rejected.original,
        ReserveOutcome::Rejected(Rejection::OperationAlreadyBound)
    );
    assert!(!rejected.replayed);
    assert!(show.reserve(ctx(5), &third).unwrap().replayed);

    // Observations still route only to the bound page: the order on page 0
    // reconciles and nothing is stranded on page 1.
    show.mark_payment_unknown(ctx(6), id(1)).unwrap();
    let outcome = show
        .observe_capture(
            ctx(7),
            CaptureObservation {
                event_id: id(40),
                operation: reserve(1, 0, 1).payment,
                amount: amount(10_000),
                evidence_hash: Hash32::from_bytes([40; 32]),
            },
        )
        .unwrap();
    assert_eq!(outcome, ObservationOutcome::PaymentConfirmed);
    assert_eq!(
        show.order(id(1)).unwrap().state,
        OrderState::PaymentConfirmed
    );
    assert!(show.order(id(2)).is_none());
}

#[test]
fn capture_observations_route_to_the_bound_operations_page() {
    let mut show = show(
        RangeTable::new(&[
            page(0, 0, 100, PageKind::Seat),
            page(1, 100, 200, PageKind::Seat),
        ])
        .unwrap(),
    );
    show.reserve(ctx(1), &reserve(1, 0, 1)).unwrap();
    show.reserve(ctx(2), &reserve(2, 100, 1)).unwrap();
    show.mark_payment_unknown(ctx(3), id(1)).unwrap();

    // Page 0's operation confirms on page 0; page 1's order is untouched.
    let outcome = show
        .observe_capture(
            ctx(4),
            CaptureObservation {
                event_id: id(40),
                operation: reserve(1, 0, 1).payment,
                amount: amount(10_000),
                evidence_hash: Hash32::from_bytes([40; 32]),
            },
        )
        .unwrap();
    assert_eq!(outcome, ObservationOutcome::PaymentConfirmed);
    assert_eq!(
        show.order(id(1)).unwrap().state,
        OrderState::PaymentConfirmed
    );
    assert_eq!(show.order(id(2)).unwrap().state, OrderState::Held);

    // An operation bound on no page cannot be routed.
    assert_eq!(
        show.observe_capture(
            ctx(5),
            CaptureObservation {
                event_id: id(41),
                operation: ProviderOperation {
                    provider: id(20),
                    account: id(21),
                    operation: id(99),
                },
                amount: amount(10_000),
                evidence_hash: Hash32::from_bytes([41; 32]),
            },
        ),
        Err(MappingError::UnknownOperation)
    );

    // A confirmed order is not an unresolved reservation: page 0 is still
    // delegatable while page 1's Held order is not.
    show.create_grant(id(50), id(60)).unwrap();
    show.delegate_page(6, id(50), 0).unwrap();
    assert_eq!(
        show.delegate_page(6, id(50), 1),
        Err(MappingError::OutstandingReservations)
    );
}

#[test]
fn a_kernel_capacity_error_pins_no_route() {
    // A kernel error stores no command record, so the same command identity
    // may later succeed on a different page.
    let mut show = DelegatedShow::new(
        id(9),
        id(1),
        RangeTable::new(&[page(0, 0, 1, PageKind::Seat), page(1, 1, 3, PageKind::Seat)]).unwrap(),
        1,
        kix_kernel_v5::Limits {
            commands: 1,
            orders: 1,
            observations: 1,
        },
        |index| common::id(index as u8 + 1),
    )
    .unwrap();
    show.reserve(ctx(1), &reserve(1, 0, 1)).unwrap();
    // Page 0's command table is full: a second distinct command gets
    // Kernel(Capacity) and pins nothing.
    assert_eq!(
        show.reserve(ctx(2), &reserve(2, 0, 1)),
        Err(MappingError::Kernel(KernelError::Capacity))
    );
    // Because nothing was stored, the same identity may still commit on
    // another page.
    let held = show.reserve(ctx(3), &reserve(2, 1, 1)).unwrap();
    assert_eq!(held.original, ReserveOutcome::Held(id(2)));
}
