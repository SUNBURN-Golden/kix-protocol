#[test_only]
/// The reference profile's public-path behaviour on the extended objects: direct and paid
/// issuance, gifts, resale, admission, refund and revoke.
module kix_rights_scale::public_path_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, PaymentRefShard, IssuerCap, Ticket,
    Issuance, Change, Allocation};
use kix_rights_scale::support as s;
use sui::event;
use sui::test_scenario::{Self as ts, Scenario};

fun fixture(): (Scenario, ID) {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 4, 4, 2);
    (sc, show)
}
fun issued_to_b(sc: &mut Scenario, show: ID, slot: u64): ID {
    s::issue(sc, show, slot, 0, s::b());
    s::latest_ticket(sc)
}

#[test]
fun direct_issue_records_no_payment() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::holder(&t) == s::b() && rs::state(&t) == 0 && rs::version(&t) == 1);
    assert!(rs::slot(&t) == 0 && rs::generation(&t) == 1);
    assert!(rs::last_amount(&t) == 0 && rs::last_payer(&t) == s::b() && rs::last_payment(&t).is_empty());
    ts::return_shared(t);
    sc.end();
}

#[test]
fun each_issue_emits_two_events() {
    let (mut sc, show) = fixture();
    s::issue_range(&mut sc, show, 0, 3, 0, s::b());
    assert!(event::events_by_type<Issuance>().length() == 3);
    assert!(event::events_by_type<Change>().length() == 3);
    sc.end();
}

#[test]
fun gift_then_gate_consumes_once() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 0);
    s::accept_gift(&mut sc, s::c(), show, t);
    s::authorize(&mut sc, s::c(), show, t, 2);
    s::consume(&mut sc, show, t, 2);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::holder(&t) == s::c() && rs::state(&t) == 1 && rs::version(&t) == 3);
    ts::return_shared(t);
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_consumed_ticket_cannot_be_consumed_again() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::authorize(&mut sc, s::b(), show, t, 1);
    s::consume(&mut sc, show, t, 1);
    s::consume(&mut sc, show, t, 2);
    sc.end();
}

#[test, expected_failure(abort_code = 2, location = kix_rights_scale::rights_scale)]
fun previous_holder_cannot_authorize_gate() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 0);
    s::accept_gift(&mut sc, s::c(), show, t);
    s::authorize(&mut sc, s::b(), show, t, 2);
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun unauthorized_recipient_cannot_accept() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 0);
    s::accept_gift(&mut sc, s::b(), show, t);
    sc.end();
}

#[test]
fun paid_issuance_mints_the_same_ticket_to_the_buyer() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    let (free, reserved, issued, _) = s::totals(&mut sc, show);
    assert!(free == 11 && reserved == 1 && issued == 0);
    s::pay(&mut sc, show);
    let t = s::latest_ticket(&mut sc);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::holder(&t) == s::b() && rs::state(&t) == 0 && rs::version(&t) == 1);
    assert!(rs::slot(&t) == 1 && rs::generation(&t) == 1);
    assert!(rs::last_amount(&t) == 50000 && rs::last_payer(&t) == s::b() && rs::last_payment(&t) == s::ref_bytes(1));
    ts::return_shared(t);
    let (free, reserved, issued, _) = s::totals(&mut sc, show);
    assert!(free == 11 && reserved == 0 && issued == 1);
    sc.end();
}

#[test]
fun paid_refund_frees_inventory_for_the_next_generation() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::pay(&mut sc, show);
    let t = s::latest_ticket(&mut sc);
    s::refund(&mut sc, show, t, 1, s::b());
    s::reserve(&mut sc, show, 1, 1, s::c(), 60000, s::ref_bytes(2));
    s::pay(&mut sc, show);
    let t2 = s::latest_ticket(&mut sc);
    sc.next_tx(s::a());
    let t2 = sc.take_shared_by_id<Ticket>(t2);
    assert!(rs::generation(&t2) == 2 && rs::holder(&t2) == s::c());
    ts::return_shared(t2);
    let (_, _, issued, retired) = s::totals(&mut sc, show);
    assert!(issued == 1 && retired == 0);
    sc.end();
}

#[test]
fun cancel_issuance_frees_the_slot_without_minting_and_releases_the_reference() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::unpaid(&mut sc, show);
    let (free, reserved, issued, _) = s::totals(&mut sc, show);
    assert!(free == 12 && reserved == 0 && issued == 0);
    // The same reference and slot can be reserved again after the release.
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun primary_payment_ref_cannot_be_reused() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::reserve(&mut sc, show, 2, 0, s::c(), 50000, s::ref_bytes(1));
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun primary_ref_cannot_reuse_a_resale_ref() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 100000);
    s::attest_payment(&mut sc, show, t, s::ref_bytes(5));
    s::reserve(&mut sc, show, 1, 0, s::c(), 50000, s::ref_bytes(5));
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun resale_ref_cannot_reuse_a_primary_ref() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::c(), 50000, s::ref_bytes(5));
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 100000);
    s::attest_payment(&mut sc, show, t, s::ref_bytes(5));
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun resale_ref_cannot_reuse_another_resale_ref() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    let t2 = issued_to_b(&mut sc, show, 1);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 100000);
    s::offer(&mut sc, s::b(), show, t2, 1, s::c(), 100000);
    s::attest_payment(&mut sc, show, t, s::ref_bytes(5));
    s::attest_payment(&mut sc, show, t2, s::ref_bytes(5));
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun short_primary_payment_ref_is_rejected() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, vector[1, 2, 3]);
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun zero_primary_amount_is_rejected() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 0, s::ref_bytes(1));
    sc.end();
}

#[test, expected_failure(abort_code = 4, location = kix_rights_scale::rights_scale)]
fun issuer_cannot_attest_its_own_primary_payment() {
    let (mut sc, show) = fixture();
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(s::page_id(&c, 0));
    let mut sh = sc.take_shared_by_id<PaymentRefShard>(s::shard_id(&c, rs::shard_index_for_ref(&c, s::ref_bytes(1))));
    rs::attest_issuance(&c, &mut p, &mut sh, 1, 0, s::b(), 50000, s::ref_bytes(1), sc.ctx());
    ts::return_shared(sh); ts::return_shared(p); ts::return_shared(c);
    sc.end();
}

#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun reserved_slot_cannot_be_directly_issued() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::issue(&mut sc, show, 1, 0, s::c());
    sc.end();
}

#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun reserved_slot_cannot_be_reserved_twice() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::reserve(&mut sc, show, 1, 0, s::c(), 50000, s::ref_bytes(2));
    sc.end();
}

#[test, expected_failure(abort_code = 7, location = kix_rights_scale::rights_scale)]
fun paid_issue_rejects_payment_from_another_show() {
    let (mut sc, show) = fixture();
    let other = s::ready(&mut sc, 8, 4, 4, 2);
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(1));
    s::pay(&mut sc, other);
    sc.end();
}

#[test, expected_failure(abort_code = 4, location = kix_rights_scale::rights_scale)]
fun another_publishers_cap_cannot_issue_on_this_show() {
    let (mut sc, show) = fixture();
    sc.next_tx(s::c());
    rs::init_for_testing(sc.ctx());
    s::issue_as(&mut sc, s::c(), show, 0, 0, s::c());
    sc.end();
}

#[test]
fun resale_pays_the_allocation_and_moves_the_right() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 100000);
    s::attest_payment(&mut sc, show, t, s::ref_bytes(5));
    s::accept_sale(&mut sc, s::c(), show, t);
    assert!(event::events_by_type<Allocation>().length() == 1);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::holder(&t) == s::c() && rs::version(&t) == 2 && rs::last_amount(&t) == 100000);
    assert!(rs::last_payer(&t) == s::c() && rs::last_payment(&t) == s::ref_bytes(5));
    ts::return_shared(t);
    sc.end();
}

#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun resale_above_the_cap_is_rejected() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 150001);
    sc.end();
}

#[test, expected_failure(abort_code = 5, location = kix_rights_scale::rights_scale)]
fun a_ticket_with_a_live_offer_cannot_be_refunded() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::offer(&mut sc, s::b(), show, t, 1, s::c(), 0);
    s::refund(&mut sc, show, t, 1, s::b());
    sc.end();
}

#[test]
fun revoke_retires_the_slot_and_does_not_reopen_inventory() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::revoke(&mut sc, show, t);
    let (free, _, issued, retired) = s::totals(&mut sc, show);
    assert!(free == 11 && issued == 0 && retired == 1);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::state(&t) == 2 && rs::version(&t) == 2);
    ts::return_shared(t);
    sc.end();
}

#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun a_revoked_slot_cannot_be_reissued() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::revoke(&mut sc, show, t);
    // Revocation bumped the generation to 2; the slot is still occupied.
    s::issue(&mut sc, show, 0, 2, s::c());
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_revoked_ticket_cannot_be_refunded() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::revoke(&mut sc, show, t);
    s::refund(&mut sc, show, t, 2, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun a_ticket_cannot_be_revoked_twice() {
    let (mut sc, show) = fixture();
    let t = issued_to_b(&mut sc, show, 0);
    s::revoke(&mut sc, show, t);
    s::revoke(&mut sc, show, t);
    sc.end();
}

