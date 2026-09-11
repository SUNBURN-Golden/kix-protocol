#[test_only]
module kix::rights_tests;
use kix::rights::{Self, Show, Ticket, IssuerCap};
use sui::test_scenario;
use sui::clock::{Self, Clock};

const A: address = @0xA;
const B: address = @0xB;
const GATE: address = @0xC;

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
