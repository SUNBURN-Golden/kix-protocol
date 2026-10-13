#[test_only]
/// Boundary matrix: 15/16/17, 1,023/1,024/1,025, page edges P-1, P, P+1, 2P-1, 2P, 2P+1,
/// page sizes 1/64/256/1024 and shard counts 1/2/4/8. The values are fixtures; none is
/// an operational default (profile section 4).
module kix_rights_scale::matrix_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage};
use kix_rights_scale::support as s;
use sui::test_scenario as ts;

fun add_edge(v: &mut vector<u64>, slot: u64, total: u64) {
    if (slot < total && !v.contains(&slot)) { v.push_back(slot); };
}

/// Slots 0, total-1 and the six page-edge slots around the first two boundaries.
fun edges(total: u64, p: u64): vector<u64> {
    let mut v = vector[];
    add_edge(&mut v, 0, total);
    add_edge(&mut v, total - 1, total);
    add_edge(&mut v, p - 1, total);
    add_edge(&mut v, p, total);
    add_edge(&mut v, p + 1, total);
    add_edge(&mut v, 2 * p - 1, total);
    add_edge(&mut v, 2 * p, total);
    add_edge(&mut v, 2 * p + 1, total);
    v
}

/// Issue every edge slot, refund them all, re-issue them with the next generation.
fun exercise(seated: u64, ga: u64, p: u64, shards: u64) {
    let total = seated + ga;
    let mut sc = s::begin();
    let show = s::ready(&mut sc, seated, ga, p, shards);
    let slots = edges(total, p);
    let mut tickets = vector[];
    let mut i = 0;
    while (i < slots.length()) {
        s::issue(&mut sc, show, slots[i], 0, s::b());
        tickets.push_back(s::latest_ticket(&mut sc));
        i = i + 1;
    };
    let (free, reserved, issued, retired) = s::totals(&mut sc, show);
    assert!(issued == slots.length() && reserved == 0 && retired == 0 && free == total - slots.length());
    // Each edge slot sits on the page the range table names, with generation 1.
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let pages = s::take_pages(&sc, &c);
    i = 0;
    while (i < slots.length()) {
        let page = &pages[rs::page_index_for_slot(&c, slots[i])];
        assert!(rs::page_occupied(page, slots[i]) && rs::page_generation(page, slots[i]) == 1);
        assert!(slots[i] >= rs::page_start(page) && slots[i] < rs::page_end(page));
        i = i + 1;
    };
    s::return_pages(pages);
    ts::return_shared(c);
    // Refund across the boundaries, then the same slots again with expected generation 1.
    i = 0;
    while (i < slots.length()) { s::refund(&mut sc, show, tickets[i], 1, s::b()); i = i + 1; };
    let (free, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == 0 && free == total);
    i = 0;
    while (i < slots.length()) { s::issue(&mut sc, show, slots[i], 1, s::c()); i = i + 1; };
    let (_, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == slots.length());
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let page = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, rs::page_index_for_slot(&c, slots[0])));
    assert!(rs::page_generation(&page, slots[0]) == 2 && rs::page_issuances(&page) >= 2);
    ts::return_shared(page); ts::return_shared(c);
    sc.end();
}

// 15 / 16 / 17: the 16-slot reference profile rejects 17; this profile does not.
#[test] fun capacity_15_one_page() { exercise(15, 0, 64, 1); }
#[test] fun capacity_16_one_page() { exercise(16, 0, 64, 1); }
#[test] fun capacity_17_one_page() { exercise(17, 0, 64, 1); }
#[test] fun capacity_15_pages_of_4() { exercise(15, 0, 4, 2); }
#[test] fun capacity_16_pages_of_4() { exercise(16, 0, 4, 2); }
#[test] fun capacity_17_pages_of_4() { exercise(17, 0, 4, 2); }

// 1,023 / 1,024 / 1,025 (no hidden 1,024 cap) at three page sizes.
#[test] fun slots_1023_pages_of_64() { exercise(1023, 0, 64, 4); }
#[test] fun slots_1024_pages_of_64() { exercise(1024, 0, 64, 4); }
#[test] fun slots_1025_pages_of_64() { exercise(1025, 0, 64, 4); }
#[test] fun slots_1023_pages_of_256() { exercise(1023, 0, 256, 4); }
#[test] fun slots_1024_pages_of_256() { exercise(1024, 0, 256, 4); }
#[test] fun slots_1025_pages_of_256() { exercise(1025, 0, 256, 4); }
#[test] fun slots_1023_pages_of_1024() { exercise(1023, 0, 1024, 4); }
#[test] fun slots_1024_pages_of_1024() { exercise(1024, 0, 1024, 4); }
#[test] fun slots_1025_pages_of_1024() { exercise(1025, 0, 1024, 4); }

// Page-size matrix at 1,024 slots; page size 1 is one object per seat.
#[test] fun page_size_1_at_1024_slots() { exercise(1024, 0, 1, 4); }
#[test] fun page_size_64_at_1024_slots_split_seated_and_ga() { exercise(960, 64, 64, 4); }
#[test] fun page_size_5_odd_split_with_ga_tail() { exercise(23, 9, 5, 3); }

// Shard matrix.
#[test] fun shard_count_1() { exercise(40, 0, 8, 1); }
#[test] fun shard_count_2() { exercise(40, 0, 8, 2); }
#[test] fun shard_count_8() { exercise(40, 0, 8, 8); }

/// A full 1,024-slot show: every slot issued in one transaction across 16 pages.
#[test]
fun full_show_of_1024_slots_conserves() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 1024, 0, 64, 4);
    s::issue_range(&mut sc, show, 0, 1024, 0, s::b());
    let (free, reserved, issued, retired) = s::totals(&mut sc, show);
    assert!(free == 0 && reserved == 0 && issued == 1024 && retired == 0);
    sc.end();
}

fun beyond(total: u64, p: u64) {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, total, 0, p, 1);
    s::issue(&mut sc, show, total, 0, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun slot_15_is_outside_a_15_slot_show() { beyond(15, 4); }
#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun slot_16_is_outside_a_16_slot_show() { beyond(16, 4); }
#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun slot_17_is_outside_a_17_slot_show() { beyond(17, 4); }
#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun slot_1023_is_outside_a_1023_slot_show() { beyond(1023, 64); }
#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun slot_1024_is_outside_a_1024_slot_show() { beyond(1024, 64); }
#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun slot_1025_is_outside_a_1025_slot_show() { beyond(1025, 64); }

/// The last seated slot and the first GA slot are neighbours that sit on different pages.
#[test]
fun seated_and_ga_neighbours_use_different_pages() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 8, 4, 1);
    s::issue(&mut sc, show, 7, 0, s::b());
    s::issue(&mut sc, show, 8, 0, s::b());
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(rs::page_index_for_slot(&c, 7) == 1 && rs::page_index_for_slot(&c, 8) == 2);
    let seated = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, 1));
    let ga = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, 2));
    assert!(rs::page_mode(&seated) == 0 && rs::page_mode(&ga) == 1);
    assert!(rs::page_issued(&seated) == 1 && rs::page_issued(&ga) == 1);
    ts::return_shared(ga); ts::return_shared(seated); ts::return_shared(c);
    sc.end();
}
