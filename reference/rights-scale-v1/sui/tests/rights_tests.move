#[test_only]
module kix_scale::rights_tests;
use kix_scale::rights::{Self, ShowControl, InventoryPage, PaymentRefShard, Ticket, IssuerCap, IssuancePayment, PaymentEvidence};
use sui::test_scenario::{Self, Scenario};
use sui::clock::{Self, Clock};
const A: address = @0xA;
const B: address = @0xB;
const G: address = @0xC;
const ATT: address = @0xD;
fun bytes(tag: u8): vector<u8> { let mut v = vector[]; let mut i = 0u64; while(i < 32) { v.push_back(tag); i = i+1; }; v }
fun setup(capacity: u64, seal: bool): Scenario {
    let mut sc = test_scenario::begin(A);
    rights::create_show(capacity,vector[G],vector[ATT],150000,200,300,sc.ctx());
    let clock = clock::create_for_testing(sc.ctx()); clock::share_for_testing(clock);
    sc.next_tx(A);
    let s = sc.take_shared<ShowControl>(); let pages = rights::page_count(&s); test_scenario::return_shared(s);
    let mut index = 0;
    while(index < pages) {
        sc.next_tx(A); let mut s = sc.take_shared<ShowControl>(); let cap = sc.take_from_sender<IssuerCap>();
        rights::create_page(&mut s,&cap,index);
        test_scenario::return_shared(s); sc.return_to_sender(cap); index = index+1;
    };
    index = 0;
    while(index < 16) {
        sc.next_tx(A); let mut s = sc.take_shared<ShowControl>(); let cap = sc.take_from_sender<IssuerCap>();
        rights::create_payment_shard(&mut s,&cap,index,sc.ctx());
        test_scenario::return_shared(s); sc.return_to_sender(cap); index = index+1;
    };
    if(seal) { sc.next_tx(A); let mut s = sc.take_shared<ShowControl>(); let cap = sc.take_from_sender<IssuerCap>();
        rights::seal(&mut s,&cap); test_scenario::return_shared(s); sc.return_to_sender(cap); };
    sc
}
fun page(sc: &Scenario,s: &ShowControl,slot: u64): InventoryPage { sc.take_shared_by_id<InventoryPage>(rights::page_id(s,slot/256)) }
fun shard(sc: &Scenario,s: &ShowControl,r: &vector<u8>): PaymentRefShard { sc.take_shared_by_id<PaymentRefShard>(rights::shard_id(s,rights::payment_shard(r))) }
fun issue(sc: &mut Scenario,slot: u64,generation: u64) {
    sc.next_tx(A); let s = sc.take_shared<ShowControl>(); let mut p = page(sc,&s,slot);
    rights::issue(&s,&mut p,slot,generation,A,sc.ctx()); test_scenario::return_shared(p); test_scenario::return_shared(s);
}
fun reserve(sc: &mut Scenario,slot: u64,r: vector<u8>) {
    sc.next_tx(ATT); let s = sc.take_shared<ShowControl>(); let mut p = page(sc,&s,slot); let mut sh = shard(sc,&s,&r);
    rights::attest_issuance(&s,&mut p,&mut sh,slot,0,A,1000,r,sc.ctx());
    test_scenario::return_shared(sh); test_scenario::return_shared(p); test_scenario::return_shared(s);
}
fun paid(sc: &mut Scenario,slot: u64,r: vector<u8>) {
    sc.next_tx(A); let s = sc.take_shared<ShowControl>(); let mut p = page(sc,&s,slot); let sh = shard(sc,&s,&r);
    let pay = sc.take_from_sender<IssuancePayment>(); rights::issue_paid(&s,&mut p,&sh,pay,sc.ctx());
    test_scenario::return_shared(sh); test_scenario::return_shared(p); test_scenario::return_shared(s);
}
fun refund(sc: &mut Scenario,slot: u64) {
    sc.next_tx(A); let s = sc.take_shared<ShowControl>(); let mut p = page(sc,&s,slot); let mut t = sc.take_shared<Ticket>(); let c = sc.take_shared<Clock>();
    rights::refund(&s,&mut p,&mut t,1,&c,sc.ctx());
    assert!(!rights::occupied(&s,&p,slot));
    test_scenario::return_shared(c); test_scenario::return_shared(t); test_scenario::return_shared(p); test_scenario::return_shared(s);
}
fun cancel(sc: &mut Scenario) {
    sc.next_tx(A); let mut s = sc.take_shared<ShowControl>(); let cap = sc.take_from_sender<IssuerCap>();
    rights::cancel_show(&mut s,&cap); test_scenario::return_shared(s); sc.return_to_sender(cap);
}
fun boundaries(capacity: u64) {
    let mut sc = setup(capacity,true); issue(&mut sc,capacity-1,0);
    sc.next_tx(A); let s = sc.take_shared<ShowControl>(); let p = page(&sc,&s,capacity-1); let t = sc.take_shared<Ticket>();
    assert!(rights::capacity(&s)==capacity && rights::slot(&t)==capacity-1 && rights::generation(&t)==1);
    assert!(rights::page_length(&p)<=256 && rights::occupied(&s,&p,capacity-1));
    test_scenario::return_shared(t); test_scenario::return_shared(p); test_scenario::return_shared(s); sc.end();
}
#[test] fun capacity_15() { boundaries(15); }
#[test] fun capacity_16() { boundaries(16); }
#[test] fun capacity_17() { boundaries(17); }
#[test] fun capacity_255() { boundaries(255); }
#[test] fun capacity_256() { boundaries(256); }
#[test] fun capacity_257() { boundaries(257); }
#[test] fun capacity_1024() { boundaries(1024); }
#[test] fun capacity_16384() { boundaries(16384); }
#[test] fun capacity_65536() { boundaries(65536); }
#[test, expected_failure(abort_code=6,location=kix_scale::rights)] fun capacity_zero_rejected() { let sc=setup(0,true); sc.end(); }
#[test, expected_failure(abort_code=6,location=kix_scale::rights)] fun capacity_over_limit_rejected() { let sc=setup(65537,true); sc.end(); }
#[test, expected_failure(abort_code=9,location=kix_scale::rights)] fun duplicate_issue() { let mut sc=setup(257,true); issue(&mut sc,256,0); issue(&mut sc,256,0); sc.end(); }
#[test, expected_failure(abort_code=9,location=kix_scale::rights)] fun unsealed_issue() { let mut sc=setup(17,false); issue(&mut sc,16,0); sc.end(); }
#[test, expected_failure(abort_code=10,location=kix_scale::rights)] fun incomplete_seal() {
 let mut sc=test_scenario::begin(A); rights::create_show(257,vector[G],vector[ATT],1000,0,0,sc.ctx()); sc.next_tx(A);
 let mut s=sc.take_shared<ShowControl>();let cap=sc.take_from_sender<IssuerCap>();rights::seal(&mut s,&cap);
 test_scenario::return_shared(s);sc.return_to_sender(cap);sc.end();
}
#[test, expected_failure] fun duplicate_page() {
 let mut sc=setup(17,false);sc.next_tx(A);let mut s=sc.take_shared<ShowControl>();let cap=sc.take_from_sender<IssuerCap>();rights::create_page(&mut s,&cap,0);
 test_scenario::return_shared(s);sc.return_to_sender(cap);sc.end();
}
#[test, expected_failure(abort_code=9,location=kix_scale::rights)] fun wrong_page() {
 let mut sc=setup(257,true);sc.next_tx(A);let s=sc.take_shared<ShowControl>();let mut p=page(&sc,&s,0);rights::issue(&s,&mut p,256,0,A,sc.ctx());
 test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
#[test, expected_failure(abort_code=3,location=kix_scale::rights)] fun late_issue_after_refund() { let mut sc=setup(257,true);issue(&mut sc,256,0);refund(&mut sc,256);issue(&mut sc,256,0);sc.end(); }
#[test] fun paid_refund_next_generation() { let mut sc=setup(257,true);reserve(&mut sc,256,bytes(1));paid(&mut sc,256,bytes(1));refund(&mut sc,256);issue(&mut sc,256,1);sc.end(); }
#[test, expected_failure(abort_code=7,location=kix_scale::rights)] fun cross_page_payment_ref_reuse() { let mut sc=setup(257,true);reserve(&mut sc,0,bytes(1));reserve(&mut sc,256,bytes(1));sc.end(); }
#[test, expected_failure(abort_code=9,location=kix_scale::rights)] fun reserved_cannot_direct_issue() { let mut sc=setup(257,true);reserve(&mut sc,256,bytes(1));issue(&mut sc,256,0);sc.end(); }
#[test, expected_failure(abort_code=1,location=kix_scale::rights)] fun cancelled_paid_issue() { let mut sc=setup(257,true);reserve(&mut sc,256,bytes(1));cancel(&mut sc);paid(&mut sc,256,bytes(1));sc.end(); }
#[test] fun cancel_preserves_reservation_cleanup() {
 let mut sc=setup(257,true);reserve(&mut sc,256,bytes(1));cancel(&mut sc);sc.next_tx(A);
 let s=sc.take_shared<ShowControl>();let mut p=page(&sc,&s,256);let mut sh=shard(&sc,&s,&bytes(1));let pay=sc.take_from_sender<IssuancePayment>();
 rights::cancel_issuance(&s,&mut p,&mut sh,pay,sc.ctx());assert!(!rights::occupied(&s,&p,256));assert!(rights::slot_generation(&s,&p,256)==1);
 test_scenario::return_shared(sh);test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
#[test, expected_failure(abort_code=8,location=kix_scale::rights)] fun wrong_payment_shard() {
 let mut sc=setup(257,true);sc.next_tx(ATT);let s=sc.take_shared<ShowControl>();let mut p=page(&sc,&s,256);
 let wrong=(rights::payment_shard(&bytes(1))+1)%16;let mut sh=sc.take_shared_by_id<PaymentRefShard>(rights::shard_id(&s,wrong));
 rights::attest_issuance(&s,&mut p,&mut sh,256,0,A,1000,bytes(1),sc.ctx());
 test_scenario::return_shared(sh);test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
fun gift(sc: &mut Scenario) {
 sc.next_tx(A);let s=sc.take_shared<ShowControl>();let p=page(sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();
 rights::offer(&s,&p,&mut t,1,B,0,900000,&c,sc.ctx());test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);
 sc.next_tx(B);let s=sc.take_shared<ShowControl>();let p=page(sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();
 rights::accept_gift(&s,&p,&mut t,&c,sc.ctx());assert!(rights::holder(&t)==B && rights::version(&t)==2);
 test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);
}
fun admit(sc: &mut Scenario) {
 sc.next_tx(B);let s=sc.take_shared<ShowControl>();let p=page(sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();
 rights::authorize_admission(&s,&p,&mut t,2,G,bytes(2),120000,&c,sc.ctx());test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);
 sc.next_tx(G);let s=sc.take_shared<ShowControl>();let p=page(sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();
 rights::consume(&s,&p,&mut t,2,bytes(2),&c,sc.ctx());assert!(rights::state(&t)==1);
 test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);
}
#[test] fun gift_admission() { let mut sc=setup(257,true);issue(&mut sc,256,0);gift(&mut sc);admit(&mut sc);sc.end(); }
#[test, expected_failure(abort_code=1,location=kix_scale::rights)] fun double_admission() {
 let mut sc=setup(257,true);issue(&mut sc,256,0);gift(&mut sc);admit(&mut sc);
 sc.next_tx(G);let s=sc.take_shared<ShowControl>();let p=page(&sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();
 rights::consume(&s,&p,&mut t,3,bytes(2),&c,sc.ctx());test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
#[test] fun resale() {
 let mut sc=setup(257,true);issue(&mut sc,256,0);sc.next_tx(A);
 let s=sc.take_shared<ShowControl>();let p=page(&sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();
 rights::offer(&s,&p,&mut t,1,B,1000,900000,&c,sc.ctx());test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);
 sc.next_tx(ATT);let s=sc.take_shared<ShowControl>();let p=page(&sc,&s,256);let t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();let mut sh=shard(&sc,&s,&bytes(3));
 rights::attest_payment(&s,&p,&mut sh,&t,bytes(3),&c,sc.ctx());test_scenario::return_shared(sh);test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);
 sc.next_tx(B);let s=sc.take_shared<ShowControl>();let p=page(&sc,&s,256);let mut t=sc.take_shared<Ticket>();let c=sc.take_shared<Clock>();let pay=sc.take_from_sender<PaymentEvidence>();
 rights::accept_sale(&s,&p,&mut t,pay,&c,sc.ctx());assert!(rights::holder(&t)==B && rights::last_amount(&t)==1000);
 test_scenario::return_shared(t);test_scenario::return_shared(c);test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
#[test, expected_failure(abort_code=4,location=kix_scale::rights)] fun unauthorized_issuer() {
 let mut sc=setup(257,true);sc.next_tx(B);let s=sc.take_shared<ShowControl>();let mut p=page(&sc,&s,256);
 rights::issue(&s,&mut p,256,0,B,sc.ctx());test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
#[test, expected_failure(abort_code=3,location=kix_scale::rights)] fun other_show_page() {
 let mut sc=setup(257,true);sc.next_tx(A);let old=sc.take_shared<ShowControl>();let oldpage=rights::page_id(&old,1);test_scenario::return_shared(old);
 rights::create_show(257,vector[G],vector[ATT],1000,0,0,sc.ctx());sc.next_tx(A);
 let s=sc.take_shared<ShowControl>();let mut p=sc.take_shared_by_id<InventoryPage>(oldpage);
 rights::issue(&s,&mut p,256,0,A,sc.ctx());test_scenario::return_shared(p);test_scenario::return_shared(s);sc.end();
}
#[test, expected_failure(abort_code=9,location=kix_scale::rights)] fun revoke_keeps_inventory_closed() {
 let mut sc=setup(257,true);issue(&mut sc,256,0);sc.next_tx(A);
 let s=sc.take_shared<ShowControl>();let mut p=page(&sc,&s,256);let mut t=sc.take_shared<Ticket>();rights::revoke(&s,&mut p,&mut t,sc.ctx());
 assert!(rights::occupied(&s,&p,256));test_scenario::return_shared(t);test_scenario::return_shared(p);test_scenario::return_shared(s);
 issue(&mut sc,256,2);sc.end();
}
#[test, expected_failure(abort_code=10,location=kix_scale::rights)] fun cannot_reopen_cancelled_show() {
 let mut sc=setup(257,true);cancel(&mut sc);sc.next_tx(A);let mut s=sc.take_shared<ShowControl>();let cap=sc.take_from_sender<IssuerCap>();rights::seal(&mut s,&cap);
 test_scenario::return_shared(s);sc.return_to_sender(cap);sc.end();
}
#[test, expected_failure(abort_code=9,location=kix_scale::rights)] fun cancelled_reservation_stale_attestation() {
 let mut sc=setup(257,true);reserve(&mut sc,256,bytes(1));sc.next_tx(A);
 let s=sc.take_shared<ShowControl>();let mut p=page(&sc,&s,256);let mut sh=shard(&sc,&s,&bytes(1));let pay=sc.take_from_sender<IssuancePayment>();
 rights::cancel_issuance(&s,&mut p,&mut sh,pay,sc.ctx());test_scenario::return_shared(sh);test_scenario::return_shared(p);test_scenario::return_shared(s);
 reserve(&mut sc,256,bytes(1));sc.end();
}
