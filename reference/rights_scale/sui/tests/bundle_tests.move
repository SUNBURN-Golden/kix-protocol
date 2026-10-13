#[test_only]
/// RS-C04 and RS-C05: bundles are all-or-nothing, bounded by MAX_BUNDLE_CHAIN, and may
/// cross page boundaries inside one PTB.
module kix_rights_scale::bundle_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, IssuerCap};
use kix_rights_scale::support as s;
use sui::test_scenario::{Self as ts, Scenario};

fun fixture(): (Scenario, ID) {
    let mut sc = s::begin();
    // 12 seated + 4 GA slots in pages of 4, so a bundle at the limit spans several pages.
    let show = s::ready(&mut sc, 12, 4, 4, 2);
    (sc, show)
}

#[test]
fun constants_are_the_localnet_defaults() {
    assert!(rs::profile_version() == 1);
    assert!(rs::max_bundle_chain() == 8);
    assert!(rs::localnet_show_slots() == 1024);
    assert!(rs::localnet_page_slots() == 64);
    assert!(rs::localnet_payment_shards() == 4);
}

fun at(limit_delta: u64, minus: bool) {
    let (mut sc, show) = fixture();
    let n = if (minus) rs::max_bundle_chain() - limit_delta else rs::max_bundle_chain() + limit_delta;
    s::bundle(&mut sc, show, 1, n, n, s::b());
    sc.end();
}
#[test] fun c05_one_below_the_limit_succeeds() { at(1, true); }
#[test] fun c05_at_the_limit_succeeds() { at(0, true); }
#[test, expected_failure(abort_code = 10, location = kix_rights_scale::rights_scale)]
fun c05_one_above_the_limit_is_rejected_with_the_dedicated_error() { at(1, false); }

#[test]
fun c05_a_bundle_at_the_limit_issues_every_slot_across_three_pages() {
    let (mut sc, show) = fixture();
    // Slots 2..9 span pages 0, 1 and 2 (seated) and the first GA-boundary neighbour.
    s::bundle(&mut sc, show, 2, 8, 8, s::b());
    let (free, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == 8 && free == 8);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let pages = s::take_pages(&sc, &c);
    assert!(rs::page_issued(&pages[0]) == 2 && rs::page_issued(&pages[1]) == 4 && rs::page_issued(&pages[2]) == 2);
    s::return_pages(pages);
    ts::return_shared(c);
    sc.end();
}

#[test]
fun c04_a_bundle_across_the_seated_and_ga_boundary_is_atomic_in_one_ptb() {
    let (mut sc, show) = fixture();
    s::bundle(&mut sc, show, 10, 4, 4, s::b());
    let (_, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == 4);
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun c04_of_two_overlapping_bundles_the_second_aborts() {
    let (mut sc, show) = fixture();
    s::bundle(&mut sc, show, 1, 2, 2, s::b());
    // [2,3] reaches slot 2 with a view from before [1,2] and aborts there.
    s::bundle(&mut sc, show, 2, 2, 2, s::c());
    sc.end();
}

#[test]
fun c04_disjoint_bundles_both_succeed() {
    let (mut sc, show) = fixture();
    s::bundle(&mut sc, show, 1, 2, 2, s::b());
    s::bundle(&mut sc, show, 3, 2, 2, s::c());
    let (_, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == 4);
    sc.end();
}

#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun c05_an_empty_bundle_is_rejected() {
    let (mut sc, show) = fixture();
    s::bundle(&mut sc, show, 0, 0, 0, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 11, location = kix_rights_scale::rights_scale)]
fun c05_finishing_with_declared_slots_unissued_is_rejected() {
    let (mut sc, show) = fixture();
    s::bundle(&mut sc, show, 0, 3, 2, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 12, location = kix_rights_scale::rights_scale)]
fun c05_issuing_more_than_declared_is_rejected() {
    let (mut sc, show) = fixture();
    s::bundle(&mut sc, show, 0, 2, 3, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 12, location = kix_rights_scale::rights_scale)]
fun c05_a_bundle_cannot_issue_under_another_shows_control() {
    let (mut sc, x) = fixture();
    let y = s::ready(&mut sc, 12, 4, 4, 2);
    sc.next_tx(s::a());
    let cx = sc.take_shared_by_id<ShowControl>(x);
    let cy = sc.take_shared_by_id<ShowControl>(y);
    let mut py = sc.take_shared_by_id<InventoryPage>(s::page_id(&cy, 0));
    let cap = sc.take_from_sender<IssuerCap>();
    let mut b = rs::begin_bundle(&cx, 2);
    rs::bundle_issue(&mut b, &cy, &mut py, &cap, 0, 0, s::b(), sc.ctx());
    rs::finish_bundle(b);
    ts::return_shared(py); ts::return_shared(cy); ts::return_shared(cx);
    sc.return_to_sender(cap);
    sc.end();
}
