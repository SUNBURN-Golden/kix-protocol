mod common;

use std::collections::BTreeSet;

use common::{ctx, ga_reserve, id, page, reserve, show};
use kix_delegated_exec::{DelegatedShow, MappingError, PageKind, RangeTable};

/// Seat page [0, 4,096) plus GA page [4,096, 4,104): capacity 8.
fn seat_and_ga_show() -> DelegatedShow {
    show(
        RangeTable::new(&[
            page(0, 0, 4_096, PageKind::Seat),
            page(1, 4_096, 4_104, PageKind::Ga),
        ])
        .unwrap(),
    )
}

fn held_slots(show: &DelegatedShow, page_index: u32) -> BTreeSet<u32> {
    (0_u8..=255)
        .map(id)
        .filter_map(|order| show.slot_hold(order))
        .filter(|hold| hold.page_index == page_index)
        .flat_map(|hold| hold.slots.iter().copied())
        .collect()
}

fn assert_conservation(show: &DelegatedShow, page_index: u32, size: u32) {
    let free = show.ga_free_slots(page_index).unwrap();
    let held = held_slots(show, page_index);
    assert!(free.is_disjoint(&held));
    assert_eq!(free.len() + held.len(), usize::try_from(size).unwrap());
}

#[test]
fn lowest_free_slots_are_assigned_deterministically() {
    let mut show = seat_and_ga_show();
    show.reserve(ctx(1), &ga_reserve(1, 3)).unwrap();
    let hold = show.slot_hold(id(1)).unwrap();
    assert_eq!(hold.page_index, 1);
    assert_eq!(hold.slots, BTreeSet::from([4_096, 4_097, 4_098]));
    // The kernel counter and the map's free set agree.
    assert_eq!(show.remaining(1), Some(5));
    assert_eq!(
        *show.ga_free_slots(1).unwrap(),
        BTreeSet::from([4_099, 4_100, 4_101, 4_102, 4_103])
    );

    show.reserve(ctx(2), &ga_reserve(2, 2)).unwrap();
    assert_eq!(
        show.slot_hold(id(2)).unwrap().slots,
        BTreeSet::from([4_099, 4_100])
    );
    assert_conservation(&show, 1, 8);
}

#[test]
fn expire_returns_the_slots_to_the_page_free_set() {
    let mut show = seat_and_ga_show();
    show.reserve(ctx(1), &ga_reserve(1, 3)).unwrap();
    // Before expiry the check releases nothing and frees no slots.
    assert!(!show.expire(ctx(50), id(1)).unwrap());
    assert_eq!(show.ga_free_slots(1).unwrap().len(), 5);

    assert!(show.expire(ctx(100), id(1)).unwrap());
    assert_eq!(
        *show.ga_free_slots(1).unwrap(),
        BTreeSet::from([4_096, 4_097, 4_098, 4_099, 4_100, 4_101, 4_102, 4_103])
    );
    assert_eq!(show.remaining(1), Some(8));
    assert!(show.slot_hold(id(1)).is_none());
    assert_conservation(&show, 1, 8);

    // The freed lowest slots are reassigned first.
    let mut next = ga_reserve(2, 2);
    next.expires_at_ms = 200;
    show.reserve(ctx(101), &next).unwrap();
    assert_eq!(
        show.slot_hold(id(2)).unwrap().slots,
        BTreeSet::from([4_096, 4_097])
    );
}

#[test]
fn a_ga_request_spanning_pages_is_refused_before_any_kernel_call() {
    let mut mapped = show(
        RangeTable::new(&[page(1, 0, 5, PageKind::Ga), page(2, 5, 10, PageKind::Ga)]).unwrap(),
    );
    // Leave one free on page 1 and two on page 2: three slots remain across
    // the pages but no single page can serve 3; the map does not split a
    // request.
    mapped.reserve(ctx(1), &ga_reserve(1, 4)).unwrap();
    mapped.reserve(ctx(2), &ga_reserve(2, 3)).unwrap();
    let before = (mapped.remaining(1), mapped.remaining(2));
    assert_eq!(before, (Some(1), Some(2)));
    assert_eq!(
        mapped.reserve(ctx(3), &ga_reserve(3, 3)),
        Err(MappingError::GaSpanningPages)
    );
    assert_eq!((mapped.remaining(1), mapped.remaining(2)), before);
    // A show without GA pages cannot serve GA at all.
    let mut seats_only = show(RangeTable::new(&[page(0, 0, 100, PageKind::Seat)]).unwrap());
    seats_only.reserve(ctx(1), &reserve(1, 0, 1)).unwrap();
    assert_eq!(
        seats_only.reserve(ctx(2), &ga_reserve(2, 1)),
        Err(MappingError::GaSpanningPages)
    );
}

#[test]
fn ga_conservation_holds_across_mixed_sequences() {
    let mut show = seat_and_ga_show();
    show.reserve(ctx(1), &ga_reserve(1, 8)).unwrap();
    assert_conservation(&show, 1, 8);
    // Page full: the next GA request cannot be served by any single page.
    assert_eq!(
        show.reserve(ctx(2), &ga_reserve(2, 1)),
        Err(MappingError::GaSpanningPages)
    );
    // Seat inventory is independent of the GA free set.
    show.reserve(ctx(3), &reserve(3, 10, 2)).unwrap();
    assert_eq!(show.remaining(0), Some(4_094));
    assert_conservation(&show, 1, 8);
    // Releasing six of eight makes room again.
    assert!(show.expire(ctx(100), id(1)).unwrap());
    assert_conservation(&show, 1, 8);
}
