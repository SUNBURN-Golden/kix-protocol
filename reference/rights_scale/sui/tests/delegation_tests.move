#[test_only]
/// RS-3a delegation: page-level grants, `GrantControl` currentness, the revocation
/// cut and the direct-path refusal of a delegated page (profile section 10).
module kix_rights_scale::delegation_tests;
use kix_rights_scale::rights_scale::{Self as rs, Ticket};
use kix_rights_scale::support as s;
use sui::test_scenario::{Self as ts, Scenario};

const EClosed: u64 = 1;
const ENotHolder: u64 = 2;
const EStale: u64 = 3;
const EAuthority: u64 = 4;
const EShard: u64 = 16;
const EDelegated: u64 = 23;
const EGrantClosed: u64 = 24;

fun fixture(): (Scenario, ID) {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 4, 4, 2);
    (sc, show)
}

/// Show plus one grant to DELE with page `index` delegated to it.
fun delegated(sc: &mut Scenario, show: ID, index: u64): ID {
    let g = s::create_grant(sc, show, s::dele());
    s::delegate(sc, show, index, g);
    g
}

#[test]
fun grant_created_open_at_generation_one() {
    let (mut sc, show) = fixture();
    let g = s::create_grant(&mut sc, show, s::dele());
    let (gshow, issuer, delegate, generation, open) = s::grant_fields(&mut sc, g);
    assert!(gshow == show && issuer == s::a() && delegate == s::dele());
    assert!(generation == 1 && open);
    sc.end();
}

#[test]
fun delegation_binds_page_to_grant_and_delegate_issues() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    assert!(s::page_grant(&mut sc, show, 0) == option::some(g));
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::holder(&t) == s::b() && rs::slot(&t) == 0 && rs::generation(&t) == 1);
    ts::return_shared(t);
    sc.end();
}

#[test]
fun cut_then_undelegate_restores_the_direct_path() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    s::revoke_grant(&mut sc, g);
    let (_, _, _, generation, open) = s::grant_fields(&mut sc, g);
    assert!(generation == 2 && !open);
    // A pre-cut ticket survives the cut; only its delegated release paths stop.
    s::undelegate(&mut sc, show, 0, g);
    assert!(s::page_grant(&mut sc, show, 0).is_none());
    s::refund(&mut sc, show, t, 1, s::b());          // direct refund works again
    s::issue(&mut sc, show, 0, 1, s::b());           // and direct issue resumes
    sc.end();
}

#[test]
fun delegated_paid_flow_mints_to_the_buyer() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::reserve_delegated(&mut sc, show, 1, 0, g, s::b(), 50000, s::ref_bytes(9));
    s::pay_delegated(&mut sc, show, g);
    let t = s::latest_ticket(&mut sc);
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(t);
    assert!(rs::holder(&t) == s::b() && rs::last_amount(&t) == 50000);
    assert!(rs::last_payment(&t) == s::ref_bytes(9));
    ts::return_shared(t);
    sc.end();
}

#[test]
fun delegated_cancel_releases_the_reservation() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::reserve_delegated(&mut sc, show, 1, 0, g, s::b(), 50000, s::ref_bytes(9));
    s::unpaid_delegated(&mut sc, show, g);
    s::issue_delegated(&mut sc, show, 1, 0, g, s::c());
    sc.end();
}

#[test]
fun delegated_refund_returns_the_slot() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    s::refund_delegated(&mut sc, show, t, 1, g, s::b());
    let (free, reserved, issued, retired) = s::totals(&mut sc, show);
    assert!(free == 12 && reserved == 0 && issued == 0 && retired == 0);
    sc.end();
}

#[test]
fun delegated_bundle_issues_across_the_page() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::bundle_delegated(&mut sc, show, 0, 3, 3, g, s::b());
    let (_, _, issued, _) = s::totals(&mut sc, show);
    assert!(issued == 3);
    sc.end();
}

#[test, expected_failure(abort_code = EAuthority, location = kix_rights_scale::rights_scale)]
fun only_the_issuer_creates_grants() {
    let (mut sc, show) = fixture();
    s::create_grant_as(&mut sc, s::b(), show, s::dele());
    sc.end();
}

#[test, expected_failure(abort_code = EAuthority, location = kix_rights_scale::rights_scale)]
fun only_the_grant_issuer_cuts_it() {
    let (mut sc, show) = fixture();
    let g = s::create_grant(&mut sc, show, s::dele());
    s::revoke_grant_as(&mut sc, s::b(), g);
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun a_grant_is_cut_once() {
    let (mut sc, show) = fixture();
    let g = s::create_grant(&mut sc, show, s::dele());
    s::revoke_grant(&mut sc, g);
    s::revoke_grant(&mut sc, g);
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_page_refuses_direct_issue() {
    let (mut sc, show) = fixture();
    delegated(&mut sc, show, 0);
    s::issue(&mut sc, show, 0, 0, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_page_refuses_direct_attest() {
    let (mut sc, show) = fixture();
    delegated(&mut sc, show, 0);
    s::reserve(&mut sc, show, 0, 0, s::b(), 50000, s::ref_bytes(9));
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_page_refuses_direct_pay() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::reserve_delegated(&mut sc, show, 1, 0, g, s::b(), 50000, s::ref_bytes(9));
    s::pay_direct_with(&mut sc, show, s::dele());
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_page_refuses_direct_cancel() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::reserve_delegated(&mut sc, show, 1, 0, g, s::b(), 50000, s::ref_bytes(9));
    s::unpaid_direct_with(&mut sc, show, s::dele());
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_page_refuses_direct_refund() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    s::refund(&mut sc, show, t, 1, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_page_refuses_a_direct_bundle() {
    let (mut sc, show) = fixture();
    delegated(&mut sc, show, 0);
    s::bundle(&mut sc, show, 0, 2, 2, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EAuthority, location = kix_rights_scale::rights_scale)]
fun only_the_delegate_uses_the_grant() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated_as(&mut sc, s::b(), show, 0, 0, g, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun the_wrong_grant_does_not_serve_a_delegated_page() {
    let (mut sc, show) = fixture();
    let _g0 = delegated(&mut sc, show, 0);
    let other = s::create_grant(&mut sc, show, s::dele());
    s::issue_delegated(&mut sc, show, 0, 0, other, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_grant_does_not_serve_an_undelegated_page() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 4, 0, g, s::b());   // slot 4 is on page 1
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_page_is_delegated_once() {
    let (mut sc, show) = fixture();
    let g0 = s::create_grant(&mut sc, show, s::dele());
    let g1 = s::create_grant(&mut sc, show, s::dele());
    s::delegate(&mut sc, show, 0, g0);
    s::delegate(&mut sc, show, 0, g1);
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_page_with_an_open_reservation_cannot_be_delegated() {
    let (mut sc, show) = fixture();
    s::reserve(&mut sc, show, 1, 0, s::b(), 50000, s::ref_bytes(9));
    let g = s::create_grant(&mut sc, show, s::dele());
    s::delegate(&mut sc, show, 0, g);
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun a_closed_grant_takes_no_new_pages() {
    let (mut sc, show) = fixture();
    let g = s::create_grant(&mut sc, show, s::dele());
    s::revoke_grant(&mut sc, g);
    s::delegate(&mut sc, show, 0, g);
    sc.end();
}

#[test, expected_failure(abort_code = EShard, location = kix_rights_scale::rights_scale)]
fun a_grant_of_another_show_does_not_delegate_here() {
    let (mut sc, show) = fixture();
    let other = s::ready(&mut sc, 4, 0, 4, 1);
    let foreign = s::create_grant(&mut sc, other, s::dele());
    s::delegate(&mut sc, show, 0, foreign);
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun the_cut_blocks_delegated_issue() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::revoke_grant(&mut sc, g);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun the_cut_blocks_delegated_attest() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::revoke_grant(&mut sc, g);
    s::reserve_delegated(&mut sc, show, 0, 0, g, s::b(), 50000, s::ref_bytes(9));
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun the_cut_blocks_delegated_refund() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    s::revoke_grant(&mut sc, g);
    s::refund_delegated(&mut sc, show, t, 1, g, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun the_cut_blocks_delegated_cancel() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::reserve_delegated(&mut sc, show, 1, 0, g, s::b(), 50000, s::ref_bytes(9));
    s::revoke_grant(&mut sc, g);
    s::unpaid_delegated(&mut sc, show, g);
    sc.end();
}

#[test, expected_failure(abort_code = EGrantClosed, location = kix_rights_scale::rights_scale)]
fun an_open_grant_cannot_be_undelegated() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::undelegate(&mut sc, show, 0, g);
    sc.end();
}

#[test, expected_failure(abort_code = ENotHolder, location = kix_rights_scale::rights_scale)]
fun delegated_refund_stays_holder_signed() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    s::refund_delegated(&mut sc, show, t, 1, g, s::dele());   // the delegate is not the holder
    sc.end();
}

#[test, expected_failure(abort_code = EStale, location = kix_rights_scale::rights_scale)]
fun delegated_issue_still_binds_the_generation() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    s::issue_delegated(&mut sc, show, 1, 1, g, s::b());   // generation is still 0
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_delegated_bundle_cannot_cross_the_delegation_boundary() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    // Slots 3|4 straddle the delegated page 0 / direct page 1 boundary. The abort
    // rolls the whole PTB back, as with a page crossing.
    s::bundle_delegated(&mut sc, show, 3, 2, 2, g, s::b());
    sc.end();
}

#[test]
fun revoke_works_on_a_delegated_page() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    let t = s::latest_ticket(&mut sc);
    s::revoke(&mut sc, show, t);   // issuer revoke is not in the delegated five-path list
    let (_, _, issued, retired) = s::totals(&mut sc, show);
    assert!(issued == 0 && retired == 1);
    sc.end();
}

#[test]
fun cancel_show_leaves_the_grant_but_blocks_it() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::cancel(&mut sc, show);
    let (_, _, _, _, open) = s::grant_fields(&mut sc, g);
    assert!(open);   // cancel_show does not revoke grants; the delegated paths check c.open
    sc.end();
}

#[test, expected_failure(abort_code = EDelegated, location = kix_rights_scale::rights_scale)]
fun a_page_with_a_stranded_reservation_cannot_be_reclaimed() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::reserve_delegated(&mut sc, show, 1, 0, g, s::b(), 50000, s::ref_bytes(9));
    s::revoke_grant(&mut sc, g);
    // The reservation outlived its grant: no path can present the delegate-owned
    // payment, so the page is not "validated unused" (profile section 10.4-10.5).
    s::undelegate(&mut sc, show, 0, g);
    sc.end();
}

#[test, expected_failure(abort_code = EClosed, location = kix_rights_scale::rights_scale)]
fun a_cancelled_show_blocks_delegated_issue() {
    let (mut sc, show) = fixture();
    let g = delegated(&mut sc, show, 0);
    s::cancel(&mut sc, show);
    s::issue_delegated(&mut sc, show, 0, 0, g, s::b());
    sc.end();
}
