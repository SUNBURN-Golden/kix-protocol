#[test_only]
module kix::rights_tests;
use kix::rights::{Self, Show, Ticket, IssuerCap, IssuancePayment};
use sui::test_scenario::{Self, Scenario};
use sui::clock::{Self, Clock};

const A: address = @0xA;
const B: address = @0xB;
const GATE: address = @0xC;
const ATT: address = @0xD;

fun setup(): test_scenario::Scenario {
    let mut sc = test_scenario::begin(A);
    rights::create_show(2,vector[GATE],vector[@0xD],150000,200,300,object::id_from_address(@0x0),sc.ctx());
    let c = clock::create_for_testing(sc.ctx()); clock::share_for_testing(c);
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>(); let cap = sc.take_from_sender<IssuerCap>();
    rights::issue(&mut s,&cap,0,A,sc.ctx());
    test_scenario::return_shared(s); sc.return_to_sender(cap);
    sc
}
fun transfer_to_b(sc: &mut test_scenario::Scenario) {
    sc.next_tx(A);
    let s = sc.take_shared<Show>(); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    rights::offer(&s,&mut t,1,B,0,900000,&c,sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    sc.next_tx(B);
    let s = sc.take_shared<Show>(); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    rights::accept_gift(&s,&mut t,&c,sc.ctx());
    assert!(rights::holder(&t) == B && rights::version(&t) == 2);
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
}
#[test]
fun independent_gate_consumes_once() {
    let mut sc = setup(); transfer_to_b(&mut sc);
    sc.next_tx(B);
    let s = sc.take_shared<Show>(); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    let request = x"0101010101010101010101010101010101010101010101010101010101010101";
    rights::authorize_admission(&s,&mut t,2,GATE,request,120000,&c,sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    sc.next_tx(GATE);
    let s = sc.take_shared<Show>(); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    rights::consume(&s,&mut t,2,request,&c,sc.ctx());
    assert!(rights::state(&t) == 1 && rights::version(&t) == 3);
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    sc.end();
}
#[test, expected_failure(abort_code = 2, location = kix::rights)]
fun previous_holder_cannot_authorize_gate() {
    let mut sc = setup(); transfer_to_b(&mut sc); sc.next_tx(A);
    let s = sc.take_shared<Show>(); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    rights::authorize_admission(&s,&mut t,2,GATE,x"0101010101010101010101010101010101010101010101010101010101010101",120000,&c,sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c); sc.end();
}
#[test, expected_failure(abort_code = 3, location = kix::rights)]
fun unauthorized_recipient_cannot_accept() {
    let mut sc = setup(); sc.next_tx(A);
    let s = sc.take_shared<Show>(); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    rights::offer(&s,&mut t,1,B,0,900000,&c,sc.ctx());
    // Current sender A is not the intended accepting recipient B.
    rights::accept_gift(&s,&mut t,&c,sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c); sc.end();
}

fun ref_bytes(tag: u8): vector<u8> {
    let mut out = vector[];
    let mut i = 0u64;
    while (i < 32) { out.push_back(tag); i = i + 1; };
    out
}
fun open(sender: address): Scenario {
    let mut sc = test_scenario::begin(sender);
    rights::create_show(2, vector[GATE], vector[ATT], 150000, 200, 300, object::id_from_address(@0x0), sc.ctx());
    let c = clock::create_for_testing(sc.ctx());
    clock::share_for_testing(c);
    sc
}
fun reserve(sc: &mut Scenario, slot: u64, buyer: address, amount: u64, payment_ref: vector<u8>) {
    sc.next_tx(ATT);
    let mut s = sc.take_shared<Show>();
    rights::attest_issuance(&mut s, slot, buyer, amount, payment_ref, sc.ctx());
    test_scenario::return_shared(s);
}
fun pay(sc: &mut Scenario) {
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    rights::issue_paid(&mut s, &cap, payment, sc.ctx());
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
}
#[test]
fun direct_issue_records_no_payment() {
    let mut sc = setup();
    sc.next_tx(A);
    let t = sc.take_shared<Ticket>();
    assert!(rights::holder(&t) == A && rights::state(&t) == 0 && rights::version(&t) == 1);
    assert!(rights::slot(&t) == 0 && rights::generation(&t) == 1);
    assert!(rights::last_amount(&t) == 0 && rights::last_payer(&t) == A && rights::last_payment(&t).is_empty());
    test_scenario::return_shared(t);
    sc.end();
}
#[test]
fun paid_issuance_mints_the_same_ticket_to_the_buyer() {
    let mut sc = open(A);
    reserve(&mut sc, 1, B, 50000, ref_bytes(1));
    pay(&mut sc);
    sc.next_tx(A);
    let t = sc.take_shared<Ticket>();
    assert!(rights::holder(&t) == B && rights::state(&t) == 0 && rights::version(&t) == 1);
    assert!(rights::slot(&t) == 1 && rights::generation(&t) == 1);
    assert!(rights::last_amount(&t) == 50000 && rights::last_payer(&t) == B);
    assert!(rights::last_payment(&t) == ref_bytes(1));
    test_scenario::return_shared(t);
    sc.end();
}
#[test]
fun paid_ticket_is_admitted_once_by_the_gate() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 42000, ref_bytes(2));
    pay(&mut sc);
    sc.next_tx(B);
    let s = sc.take_shared<Show>();
    let mut t = sc.take_shared<Ticket>();
    let c = sc.take_shared<Clock>();
    let request = x"0101010101010101010101010101010101010101010101010101010101010101";
    rights::authorize_admission(&s, &mut t, 1, GATE, request, 120000, &c, sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    sc.next_tx(GATE);
    let s = sc.take_shared<Show>();
    let mut t = sc.take_shared<Ticket>();
    let c = sc.take_shared<Clock>();
    rights::consume(&s, &mut t, 1, request, &c, sc.ctx());
    assert!(rights::state(&t) == 1 && rights::version(&t) == 2 && rights::last_amount(&t) == 42000);
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    sc.end();
}
#[test]
fun cancel_issuance_frees_the_slot_without_minting() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 900, ref_bytes(3));
    sc.next_tx(A);
    assert!(!test_scenario::has_most_recent_shared<Ticket>());
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    rights::cancel_issuance(&mut s, &cap, payment);
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.next_tx(A);
    assert!(!test_scenario::has_most_recent_shared<Ticket>());
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    rights::issue(&mut s, &cap, 0, A, sc.ctx());
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.next_tx(A);
    let t = sc.take_shared<Ticket>();
    assert!(rights::generation(&t) == 1 && rights::last_amount(&t) == 0 && rights::holder(&t) == A);
    test_scenario::return_shared(t);
    sc.end();
}
#[test]
fun paid_refund_frees_inventory_for_the_next_generation() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 7000, ref_bytes(4));
    pay(&mut sc);
    sc.next_tx(B);
    let mut s = sc.take_shared<Show>();
    let mut t = sc.take_shared<Ticket>();
    let c = sc.take_shared<Clock>();
    rights::refund(&mut s, &mut t, 1, &c, sc.ctx());
    assert!(rights::state(&t) == 2 && rights::last_amount(&t) == 7000 && rights::last_payer(&t) == B);
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    reserve(&mut sc, 0, A, 7100, ref_bytes(5));
    pay(&mut sc);
    sc.next_tx(A);
    let t = sc.take_shared<Ticket>();
    assert!(rights::holder(&t) == A && rights::generation(&t) == 2 && rights::last_amount(&t) == 7100);
    test_scenario::return_shared(t);
    sc.end();
}
#[test, expected_failure(abort_code = 4, location = kix::rights)]
fun issuer_cannot_attest_its_own_primary_payment() {
    let mut sc = open(A);
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    rights::attest_issuance(&mut s, 0, B, 1000, ref_bytes(6), sc.ctx());
    test_scenario::return_shared(s);
    sc.end();
}
#[test, expected_failure(abort_code = 9, location = kix::rights)]
fun reserved_slot_cannot_be_directly_issued() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 1000, ref_bytes(7));
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    rights::issue(&mut s, &cap, 0, A, sc.ctx());
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.end();
}
#[test, expected_failure(abort_code = 7, location = kix::rights)]
fun zero_primary_amount_is_rejected() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 0, ref_bytes(8));
    sc.end();
}
#[test, expected_failure(abort_code = 7, location = kix::rights)]
fun short_primary_payment_ref_is_rejected() {
    let mut sc = open(A);
    sc.next_tx(ATT);
    let mut s = sc.take_shared<Show>();
    rights::attest_issuance(&mut s, 0, B, 1000, x"aa", sc.ctx());
    test_scenario::return_shared(s);
    sc.end();
}
#[test, expected_failure(abort_code = 7, location = kix::rights)]
fun primary_ref_cannot_reuse_a_resale_ref() {
    let mut sc = setup();
    sc.next_tx(A);
    let s = sc.take_shared<Show>();
    let mut t = sc.take_shared<Ticket>();
    let c = sc.take_shared<Clock>();
    rights::offer(&s, &mut t, 1, B, 1000, 900000, &c, sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    sc.next_tx(ATT);
    let mut s = sc.take_shared<Show>();
    let t = sc.take_shared<Ticket>();
    let c = sc.take_shared<Clock>();
    rights::attest_payment(&mut s, &t, ref_bytes(13), &c, sc.ctx());
    test_scenario::return_shared(t); test_scenario::return_shared(s); test_scenario::return_shared(c);
    reserve(&mut sc, 1, B, 1000, ref_bytes(13));
    sc.end();
}
#[test, expected_failure(abort_code = 7, location = kix::rights)]
fun primary_payment_ref_cannot_be_reused() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 1000, ref_bytes(9));
    pay(&mut sc);
    reserve(&mut sc, 1, B, 1000, ref_bytes(9));
    sc.end();
}
#[test]
fun closed_show_can_drop_a_primary_reservation() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 1000, ref_bytes(14));
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    rights::cancel_show(&mut s, &cap);
    let payment = sc.take_from_sender<IssuancePayment>();
    rights::cancel_issuance(&mut s, &cap, payment);
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.next_tx(A);
    assert!(!test_scenario::has_most_recent_shared<Ticket>());
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix::rights)]
fun closed_show_cannot_reserve_primary() {
    let mut sc = open(A);
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    rights::cancel_show(&mut s, &cap);
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.next_tx(ATT);
    let mut s = sc.take_shared<Show>();
    rights::attest_issuance(&mut s, 0, B, 1000, ref_bytes(15), sc.ctx());
    test_scenario::return_shared(s);
    sc.end();
}
#[test, expected_failure(abort_code = 1, location = kix::rights)]
fun closed_show_cannot_mint_paid() {
    let mut sc = open(A);
    reserve(&mut sc, 0, B, 1000, ref_bytes(10));
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    rights::cancel_show(&mut s, &cap);
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.next_tx(A);
    let mut s = sc.take_shared<Show>();
    let cap = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    rights::issue_paid(&mut s, &cap, payment, sc.ctx());
    test_scenario::return_shared(s);
    sc.return_to_sender(cap);
    sc.end();
}
#[test, expected_failure(abort_code = 4, location = kix::rights)]
fun paid_issue_rejects_cap_from_another_show() {
    let mut sc = test_scenario::begin(A);
    rights::create_show(1, vector[GATE], vector[ATT], 150000, 200, 300, object::id_from_address(@0x0), sc.ctx());
    let e1 = sc.next_tx(A);
    let show1 = test_scenario::shared(&e1)[0];
    rights::create_show(1, vector[GATE], vector[ATT], 150000, 200, 300, object::id_from_address(@0x0), sc.ctx());
    sc.next_tx(ATT);
    let mut s1 = test_scenario::take_shared_by_id<Show>(&sc, show1);
    rights::attest_issuance(&mut s1, 0, B, 1000, ref_bytes(11), sc.ctx());
    test_scenario::return_shared(s1);
    sc.next_tx(A);
    let mut s1 = test_scenario::take_shared_by_id<Show>(&sc, show1);
    let cap2 = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    rights::issue_paid(&mut s1, &cap2, payment, sc.ctx());
    test_scenario::return_shared(s1);
    sc.return_to_sender(cap2);
    sc.end();
}
#[test, expected_failure(abort_code = 7, location = kix::rights)]
fun paid_issue_rejects_payment_from_another_show() {
    let mut sc = test_scenario::begin(A);
    rights::create_show(1, vector[GATE], vector[ATT], 150000, 200, 300, object::id_from_address(@0x0), sc.ctx());
    let e1 = sc.next_tx(A);
    let show1 = test_scenario::shared(&e1)[0];
    rights::create_show(1, vector[GATE], vector[ATT], 150000, 200, 300, object::id_from_address(@0x0), sc.ctx());
    let e2 = sc.next_tx(ATT);
    let show2 = test_scenario::shared(&e2)[0];
    let mut s1 = test_scenario::take_shared_by_id<Show>(&sc, show1);
    rights::attest_issuance(&mut s1, 0, B, 1000, ref_bytes(12), sc.ctx());
    test_scenario::return_shared(s1);
    sc.next_tx(A);
    let mut s2 = test_scenario::take_shared_by_id<Show>(&sc, show2);
    let cap2 = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    rights::issue_paid(&mut s2, &cap2, payment, sc.ctx());
    test_scenario::return_shared(s2);
    sc.return_to_sender(cap2);
    sc.end();
}
