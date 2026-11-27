mod common;

use common::page;
use kix_delegated_exec::{MappingError, PageKind, RangeTable};
use kix_kernel_v5::MAX_SEATS;

#[test]
fn empty_table_is_invalid() {
    assert_eq!(
        RangeTable::new(&[]),
        Err(MappingError::InvalidConfiguration)
    );
}

#[test]
fn empty_or_inverted_page_is_invalid() {
    assert_eq!(
        RangeTable::new(&[page(0, 4, 4, PageKind::Seat)]),
        Err(MappingError::InvalidConfiguration)
    );
    assert_eq!(
        RangeTable::new(&[page(0, 4, 3, PageKind::Seat)]),
        Err(MappingError::InvalidConfiguration)
    );
}

#[test]
fn overlapping_pages_are_invalid() {
    // Overlap between any two pages is invalid, regardless of kind: one slot
    // must have exactly one original authority.
    for pages in [
        [
            page(0, 0, 10, PageKind::Seat),
            page(1, 9, 20, PageKind::Seat),
        ],
        [page(0, 0, 10, PageKind::Seat), page(1, 9, 20, PageKind::Ga)],
        [page(0, 0, 10, PageKind::Ga), page(1, 0, 10, PageKind::Ga)],
    ] {
        assert_eq!(
            RangeTable::new(&pages),
            Err(MappingError::InvalidConfiguration)
        );
    }
}

#[test]
fn duplicate_page_indices_are_invalid() {
    assert_eq!(
        RangeTable::new(&[
            page(0, 0, 10, PageKind::Seat),
            page(0, 10, 20, PageKind::Seat),
        ]),
        Err(MappingError::InvalidConfiguration)
    );
}

#[test]
fn seat_page_is_bounded_by_kernel_max_seats() {
    let max = u32::from(MAX_SEATS);
    assert!(RangeTable::new(&[page(0, 0, max, PageKind::Seat)]).is_ok());
    assert_eq!(
        RangeTable::new(&[page(0, 0, max + 1, PageKind::Seat)]),
        Err(MappingError::InvalidConfiguration)
    );
    // GA pages are quantity counters, not seat bitmaps: a single GA page may
    // exceed MAX_SEATS.
    assert!(RangeTable::new(&[page(0, 0, max + 1, PageKind::Ga)]).is_ok());
}

#[test]
fn input_order_does_not_matter_and_lookup_uses_half_open_ranges() {
    let table = RangeTable::new(&[
        page(1, 4_096, 8_192, PageKind::Seat),
        page(0, 0, 4_096, PageKind::Seat),
        page(2, 8_192, 9_000, PageKind::Ga),
    ])
    .unwrap();
    assert_eq!(table.pages()[0].index, 0);
    assert_eq!(table.page_of(0).unwrap().index, 0);
    assert_eq!(table.page_of(4_095).unwrap().index, 0);
    assert_eq!(table.page_of(4_096).unwrap().index, 1);
    assert_eq!(table.page_of(8_999).unwrap().index, 2);
    assert_eq!(table.page_of(9_000), None);
}

#[test]
fn gaps_in_the_table_are_slots_without_an_owning_page() {
    // The contract requires pairwise non-overlap, not contiguity; a gap slot
    // simply has no owning page.
    let table = RangeTable::new(&[
        page(0, 0, 10, PageKind::Seat),
        page(1, 20, 30, PageKind::Seat),
    ])
    .unwrap();
    assert!(table.page_of(9).is_some());
    assert_eq!(table.page_of(15), None);
    assert!(table.page_of(20).is_some());
}
