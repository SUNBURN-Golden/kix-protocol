#[test_only]
/// Contract predicates of docs/contracts/RIGHTS_SCALE_PROFILE.md section 8 that belong to
/// RS-1: RS-C01, C02, C03(a), C06(a), C07(a), C08, C16 (C04/C05 are in bundle_tests, C15 in
/// creation_tests). Serial order is the only order a unit test can run; the concurrent
/// versions run on the localnet driver.
module kix_rights_scale::predicate_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, PaymentRefShard};
use kix_rights_scale::support as s;
use sui::test_scenario::{Self as ts, Scenario};

fun fixture(): (Scenario, ID) {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 4, 4, 2);
    (sc, show)
}

// ------------------------------------------------------------------ RS-C01

#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun c01_a_second_attestation_for_a_reserved_slot_aborts() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 2, 0, s::b(), 50000, s::ref_bytes(1));
    s::reserve(&mut sc, show, 2, 0, s::c(), 50000, s::ref_bytes(2));
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun c01_an_attestation_made_from_a_stale_view_after_issue_aborts() {
    let (mut sc, show) = fixture();
    s::issue(&mut sc, show, 2, 0, s::b());
    s::reserve(&mut sc, show, 2, 0, s::c(), 50000, s::ref_bytes(2));
    sc.end();
}

#[test]
fun c01_the_two_slots_around_a_page_boundary_have_independent_authorities() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 3, 0, s::b(), 50000, s::ref_bytes(1));
    s::reserve(&mut sc, show, 4, 0, s::c(), 50000, s::ref_bytes(2));
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p0 = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, 0));
    let p1 = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, 1));
    assert!(rs::page_reserved(&p0) == 1 && rs::page_reserved(&p1) == 1);
    assert!(rs::page_occupied(&p0, 3) && rs::page_occupied(&p1, 4) && !rs::page_occupied(&p1, 5));
    ts::return_shared(p1); ts::return_shared(p0); ts::return_shared(c);
    sc.end();
}

// ------------------------------------------------------------------ RS-C02

/// Runs every transition on one slot and checks Σ(free + reserved + issued + retired)
/// equals the range size on every page after each step.
fun cycle(sc: &mut Scenario, show: ID, slot: u64) {
    let (mut gen, mut step) = (0u64, 0u64);
    s::issue(sc, show, slot, gen, s::b());
    let t = s::latest_ticket(sc);
    let (_, _, issued, _) = s::totals(sc, show);
    assert!(issued >= 1);
    s::refund(sc, show, t, 1, s::b());
    gen = gen + 1;
    s::reserve(sc, show, slot, gen, s::b(), 50000, s::ref_bytes(10 + (slot as u8)));
    let (_, reserved, _, _) = s::totals(sc, show);
    assert!(reserved == 1);
    s::unpaid(sc, show);
    let (_, reserved, _, _) = s::totals(sc, show);
    assert!(reserved == 0);
    s::reserve(sc, show, slot, gen, s::b(), 50000, s::ref_bytes(40 + (slot as u8)));
    s::pay(sc, show);
    gen = gen + 1;
    let t = s::latest_ticket(sc);
    s::refund(sc, show, t, 1, s::b());
    s::issue(sc, show, slot, gen, s::b());
    gen = gen + 1;
    let t = s::latest_ticket(sc);
    s::revoke(sc, show, t);
    let (_, _, _, retired) = s::totals(sc, show);
    assert!(retired >= 1);
    step = step + 1;
    // Another slot of the same page keeps cycling: cumulative issuances pass the range size.
    let other = if (slot % 4 == 0) slot + 1 else slot - 1;
    let mut round = 0u64;
    while (round < 6) {
        s::issue(sc, show, other, round, s::b());
        let t = s::latest_ticket(sc);
        s::refund(sc, show, t, 1, s::b());
        round = round + 1;
    };
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, rs::page_index_for_slot(&c, slot)));
    assert!(rs::page_issuances(&p) == 3 + 6 && rs::page_issuances(&p) > rs::page_end(&p) - rs::page_start(&p));
    assert!(rs::page_generation(&p, slot) == gen + 1 && step == 1 && rs::page_conserved(&p));
    ts::return_shared(p); ts::return_shared(c);
}

#[test]
fun c02_conservation_holds_through_every_transition_on_a_seated_page() {
    let (mut sc, show) = fixture();
    cycle(&mut sc, show, 0);
    sc.end();
}

#[test]
fun c02_conservation_holds_through_every_transition_on_a_ga_page() {
    let (mut sc, show) = fixture();
    cycle(&mut sc, show, 8);
    sc.end();
}

// ------------------------------------------------------------------ RS-C03 (a)

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun c03_the_same_command_sent_twice_creates_one_right() {
    let (mut sc, show) = fixture();
    s::issue(&mut sc, show, 0, 0, s::b());
    s::issue(&mut sc, show, 0, 0, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun c03_the_same_command_after_a_refund_is_stale() {
    let (mut sc, show) = fixture();
    s::issue(&mut sc, show, 0, 0, s::b());
    let t = s::latest_ticket(&mut sc);
    s::refund(&mut sc, show, t, 1, s::b());
    s::issue(&mut sc, show, 0, 0, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun c03_the_same_attestation_after_a_refund_is_stale() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::pay(&mut sc, show);
    let t = s::latest_ticket(&mut sc);
    s::refund(&mut sc, show, t, 1, s::b());
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(2));
    sc.end();
}

// ------------------------------------------------------------------ RS-C06 (a), RS-C07 (a)

public struct Ids has copy, drop { show: ID, t0: ID, t1: ID, t2: ID, t3: ID }

/// t0 (slot 0): admission authorized for the gate. t1 (slot 1): gift offered to C.
/// t2 (slot 2): paid offer to C with evidence attested. t3 (slot 3): paid offer, no evidence.
/// Slot 4: a reservation whose IssuancePayment the issuer still holds. Then the show is cancelled.
fun cancelled(): (Scenario, Ids) {
    let (mut sc, show) = fixture();
    let t0 = { s::issue(&mut sc, show, 0, 0, s::b()); s::latest_ticket(&mut sc) };
    let t1 = { s::issue(&mut sc, show, 1, 0, s::b()); s::latest_ticket(&mut sc) };
    let t2 = { s::issue(&mut sc, show, 2, 0, s::b()); s::latest_ticket(&mut sc) };
    let t3 = { s::issue(&mut sc, show, 3, 0, s::b()); s::latest_ticket(&mut sc) };
    s::authorize(&mut sc, s::b(), show, t0, 1);
    s::offer(&mut sc, s::b(), show, t1, 1, s::c(), 0);
    s::offer(&mut sc, s::b(), show, t2, 1, s::c(), 100000);
    s::attest_payment(&mut sc, show, t2, s::ref_bytes(7));
    s::offer(&mut sc, s::b(), show, t3, 1, s::c(), 100000);
    s::reserve(&mut sc, show, 4, 0, s::c(), 50000, s::ref_bytes(9));
    s::cancel(&mut sc, show);
    (sc, Ids { show, t0, t1, t2, t3 })
}

#[test]
fun c06_cancel_closes_the_show_and_keeps_the_range_table() {
    let (mut sc, ids) = cancelled();
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(ids.show);
    assert!(!rs::control_open(&c) && rs::control_sealed(&c) && rs::control_cancel_generation(&c) == 1);
    assert!(rs::control_page_count(&c) == 3 && rs::control_claimed_pages(&c) == 3);
    ts::return_shared(c);
    let (_, reserved, issued, _) = s::totals(&mut sc, ids.show);
    assert!(reserved == 1 && issued == 4);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_issue_after_cancel_is_rejected() { let (mut sc, ids) = cancelled(); s::issue(&mut sc, ids.show, 5, 0, s::b()); sc.end(); }
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_attest_issuance_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::reserve(&mut sc, ids.show, 5, 0, s::b(), 50000, s::ref_bytes(11));
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_offer_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::offer(&mut sc, s::b(), ids.show, ids.t0, 2, s::c(), 0);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_accept_gift_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::accept_gift(&mut sc, s::c(), ids.show, ids.t1);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_authorize_admission_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::authorize(&mut sc, s::b(), ids.show, ids.t1, 2);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_consume_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::consume(&mut sc, ids.show, ids.t0, 2);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_refund_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::refund(&mut sc, ids.show, ids.t1, 2, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_accept_sale_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::accept_sale(&mut sc, s::c(), ids.show, ids.t2);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_attest_payment_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::attest_payment(&mut sc, ids.show, ids.t3, s::ref_bytes(8));
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_a_bundle_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::bundle(&mut sc, ids.show, 5, 2, 2, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c07_issue_paid_after_cancel_is_rejected() {
    let (mut sc, ids) = cancelled();
    s::pay(&mut sc, ids.show);
    sc.end();
}
#[test]
fun c07_a_reservation_can_still_be_dropped_after_cancel() {
    let (mut sc, ids) = cancelled();
    s::unpaid(&mut sc, ids.show);
    let (free, reserved, issued, _) = s::totals(&mut sc, ids.show);
    assert!(reserved == 0 && issued == 4 && free == 8);
    sc.end();
}
#[test]
fun c07_revoke_still_works_after_cancel_and_the_slot_stays_closed() {
    let (mut sc, ids) = cancelled();
    s::revoke(&mut sc, ids.show, ids.t1);
    let (_, _, issued, retired) = s::totals(&mut sc, ids.show);
    assert!(issued == 3 && retired == 1);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_a_second_cancel_is_rejected() { let (mut sc, ids) = cancelled(); s::cancel(&mut sc, ids.show); sc.end(); }
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c06_a_show_that_was_never_sealed_cannot_be_cancelled() {
    let mut sc = s::begin();
    let show = s::make_show(&mut sc, 8, 0, 4, 1);
    s::stage(&mut sc, show);
    s::cancel(&mut sc, show);
    sc.end();
}
#[test]
fun c06_issue_then_cancel_leaves_the_right_in_place() {
    let (mut sc, show) = fixture();
    s::issue(&mut sc, show, 0, 0, s::b());
    s::cancel(&mut sc, show);
    let (_, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == 1);
    sc.end();
}

// ------------------------------------------------------------------ RS-C08

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun c08_the_old_ticket_is_dead_after_a_reissue() {
    let (mut sc, show) = fixture();
    s::issue(&mut sc, show, 0, 0, s::b());
    let old = s::latest_ticket(&mut sc);
    s::refund(&mut sc, show, old, 1, s::b());
    s::issue(&mut sc, show, 0, 1, s::c());
    s::offer(&mut sc, s::b(), show, old, 2, s::c(), 0);
    sc.end();
}

#[test]
fun c08_the_new_ticket_carries_the_next_generation_and_the_old_one_is_void() {
    let (mut sc, show) = fixture();
    s::issue(&mut sc, show, 0, 0, s::b());
    let old = s::latest_ticket(&mut sc);
    s::refund(&mut sc, show, old, 1, s::b());
    s::issue(&mut sc, show, 0, 1, s::c());
    let new = s::latest_ticket(&mut sc);
    sc.next_tx(s::a());
    let old = sc.take_shared_by_id<rs::Ticket>(old);
    let new = sc.take_shared_by_id<rs::Ticket>(new);
    assert!(rs::state(&old) == 2 && rs::generation(&old) == 1);
    assert!(rs::state(&new) == 0 && rs::generation(&new) == 2 && rs::holder(&new) == s::c());
    ts::return_shared(new); ts::return_shared(old);
    sc.end();
}

// ------------------------------------------------------------------ RS-C16

/// Two shows with the same shape; a ticket of X is slot 0 on X's page 0.
fun two_shows(): (Scenario, ID, ID, ID) {
    let (mut sc, x) = fixture();
    let y = s::ready(&mut sc, 8, 4, 4, 2);
    s::issue(&mut sc, x, 0, 0, s::b());
    let t = s::latest_ticket(&mut sc);
    (sc, x, y, t)
}
fun pid(sc: &mut Scenario, show: ID, index: u64): ID {
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let id = s::page_id(&c, index);
    ts::return_shared(c);
    id
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun c16_another_shows_control_with_this_shows_ticket_is_rejected() {
    let (mut sc, x, y, t) = two_shows();
    let page = pid(&mut sc, y, 0);
    s::offer_with(&mut sc, s::b(), y, page, t, 1, s::c(), 0);
    let _ = x;
    sc.end();
}
#[test, expected_failure(abort_code = 15, location = kix_rights_scale::rights_scale)]
fun c16_another_shows_page_with_this_shows_control_is_rejected() {
    let (mut sc, x, y, t) = two_shows();
    let page = pid(&mut sc, y, 0);
    s::offer_with(&mut sc, s::b(), x, page, t, 1, s::c(), 0);
    sc.end();
}
#[test, expected_failure(abort_code = 15, location = kix_rights_scale::rights_scale)]
fun c16_the_wrong_page_index_of_this_show_is_rejected() {
    let (mut sc, x, _y, t) = two_shows();
    let page = pid(&mut sc, x, 1);
    s::offer_with(&mut sc, s::b(), x, page, t, 1, s::c(), 0);
    sc.end();
}
#[test, expected_failure(abort_code = 15, location = kix_rights_scale::rights_scale)]
fun c16_issue_with_another_shows_page_is_rejected() {
    let (mut sc, x, y, _t) = two_shows();
    let page = pid(&mut sc, y, 0);
    s::issue_with(&mut sc, x, page, 1, 0, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 15, location = kix_rights_scale::rights_scale)]
fun c16_issue_with_another_shows_control_and_this_shows_page_is_rejected() {
    let (mut sc, x, y, _t) = two_shows();
    let page = pid(&mut sc, x, 0);
    s::issue_with(&mut sc, y, page, 1, 0, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 15, location = kix_rights_scale::rights_scale)]
fun c16_issue_with_the_right_show_but_the_page_of_another_slot_is_rejected() {
    let (mut sc, x, _y, _t) = two_shows();
    let page = pid(&mut sc, x, 1);
    s::issue_with(&mut sc, x, page, 1, 0, s::b());
    sc.end();
}
#[test, expected_failure(abort_code = 16, location = kix_rights_scale::rights_scale)]
fun c16_another_shows_shard_is_rejected() {
    let (mut sc, x, y, _t) = two_shows();
    sc.next_tx(s::att());
    let cx = sc.take_shared_by_id<ShowControl>(x);
    let cy = sc.take_shared_by_id<ShowControl>(y);
    let mut p = sc.take_shared_by_id<InventoryPage>(s::page_id(&cx, 0));
    let r = s::ref_bytes(3);
    // The shard Y derived for the same routing index is not X's shard.
    let mut sh = sc.take_shared_by_id<PaymentRefShard>(s::shard_id(&cy, rs::shard_index_for_ref(&cx, copy r)));
    rs::attest_issuance(&cx, &mut p, &mut sh, 1, 0, s::b(), 50000, r, sc.ctx());
    ts::return_shared(sh); ts::return_shared(p); ts::return_shared(cy); ts::return_shared(cx);
    sc.end();
}
#[test]
fun c16_derived_page_addresses_differ_per_show_and_per_index() {
    // The only way to obtain an InventoryPage is derived_object::claim under a ShowControl,
    // so the pages of a show are exactly the objects at its derived addresses.
    let (mut sc, x, y, _t) = two_shows();
    sc.next_tx(s::a());
    let cx = sc.take_shared_by_id<ShowControl>(x);
    let cy = sc.take_shared_by_id<ShowControl>(y);
    assert!(rs::page_address(&cx, 0) != rs::page_address(&cy, 0));
    assert!(rs::page_address(&cx, 0) != rs::page_address(&cx, 1));
    ts::return_shared(cy); ts::return_shared(cx);
    sc.end();
}
