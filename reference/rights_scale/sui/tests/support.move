#[test_only]
/// Shared fixtures for the extended-profile tests. Each helper is one transaction and
/// begins with `next_tx(sender)`, which also ends the previous one.
module kix_rights_scale::support;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, PaymentRefShard, IssuerCap, Ticket, IssuancePayment};
use sui::clock::{Self, Clock};
use sui::test_scenario::{Self as ts, Scenario};
use kix_rights_scale::rights_scale::{PaymentEvidence, Bundle};

const A: address = @0xA;
const B: address = @0xB;
const C: address = @0xC;
const GATE: address = @0xD;
const ATT: address = @0xE;
const STAGE_BATCH: u64 = 128;
const ISSUE_BATCH: u64 = 128;

public fun a(): address { A }
public fun b(): address { B }
public fun c(): address { C }
public fun gate(): address { GATE }
public fun att(): address { ATT }

public fun ref_bytes(tag: u8): vector<u8> {
    let mut out = vector[];
    let mut i = 0u64;
    while (i < 32) { out.push_back(tag); i = i + 1; };
    out
}
public fun request(): vector<u8> { ref_bytes(1) }

/// Publisher A holds the one IssuerCap; the clock is shared.
public fun begin(): Scenario {
    let mut sc = ts::begin(A);
    rs::init_for_testing(sc.ctx());
    clock::share_for_testing(clock::create_for_testing(sc.ctx()));
    sc
}

public fun make_show(sc: &mut Scenario, seated: u64, ga: u64, page_size: u64, shards: u64): ID {
    sc.next_tx(A);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::create_show_control(&cap, seated, ga, page_size, shards, vector[GATE], vector[ATT],
        150000, 200, 300, object::id_from_address(@0x0), sc.ctx());
    sc.return_to_sender(cap);
    sc.next_tx(A);
    ts::most_recent_id_shared<ShowControl>().destroy_some()
}

/// Claims every page and shard, at most `STAGE_BATCH` pages per transaction (profile
/// section 7: new-ID and event limits make staging a multi-transaction job).
public fun stage(sc: &mut Scenario, show: ID) {
    sc.next_tx(A);
    let pages = {
        let c = sc.take_shared_by_id<ShowControl>(show);
        let n = rs::control_page_count(&c);
        ts::return_shared(c);
        n
    };
    let mut from = 0;
    while (from < pages) {
        let count = if (pages - from > STAGE_BATCH) STAGE_BATCH else pages - from;
        sc.next_tx(A);
        let mut c = sc.take_shared_by_id<ShowControl>(show);
        let cap = sc.take_from_sender<IssuerCap>();
        rs::claim_pages(&mut c, &cap, from, count, sc.ctx());
        ts::return_shared(c);
        sc.return_to_sender(cap);
        from = from + count;
    };
    sc.next_tx(A);
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    let shards = rs::control_shard_count(&c);
    rs::claim_shards(&mut c, &cap, 0, shards, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
}

public fun seal(sc: &mut Scenario, show: ID) {
    sc.next_tx(A);
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::seal(&mut c, &cap, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
}

/// Creates, stages and seals one show. The scenario is left inside an open transaction.
public fun ready(sc: &mut Scenario, seated: u64, ga: u64, page_size: u64, shards: u64): ID {
    let show = make_show(sc, seated, ga, page_size, shards);
    stage(sc, show);
    seal(sc, show);
    show
}

public fun page_id(c: &ShowControl, index: u64): ID { object::id_from_address(rs::page_address(c, index)) }
public fun shard_id(c: &ShowControl, index: u64): ID { object::id_from_address(rs::shard_address(c, index)) }

public fun cancel(sc: &mut Scenario, show: ID) {
    sc.next_tx(A);
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::cancel_show(&mut c, &cap, sc.ctx());
    ts::return_shared(c);
    sc.return_to_sender(cap);
}

public fun issue(sc: &mut Scenario, show: ID, slot: u64, generation: u64, holder: address) {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, slot)));
    let cap = sc.take_from_sender<IssuerCap>();
    rs::issue(&c, &mut p, &cap, slot, generation, holder, sc.ctx());
    ts::return_shared(p);
    ts::return_shared(c);
    sc.return_to_sender(cap);
}

public fun latest_ticket(sc: &mut Scenario): ID {
    sc.next_tx(A);
    ts::most_recent_id_shared<Ticket>().destroy_some()
}

public fun refund(sc: &mut Scenario, show: ID, ticket: ID, version: u64, sender: address) {
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, rs::slot(&t))));
    let clk = sc.take_shared<Clock>();
    rs::refund(&c, &mut p, &mut t, version, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(p); ts::return_shared(t); ts::return_shared(c);
}

public fun reserve(sc: &mut Scenario, show: ID, slot: u64, generation: u64, buyer: address, amount: u64,
    payment_ref: vector<u8>) {
    sc.next_tx(ATT);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, slot)));
    let mut s = sc.take_shared_by_id<PaymentRefShard>(shard_id(&c, rs::shard_index_for_ref(&c, copy payment_ref)));
    rs::attest_issuance(&c, &mut p, &mut s, slot, generation, buyer, amount, payment_ref, sc.ctx());
    ts::return_shared(s); ts::return_shared(p); ts::return_shared(c);
}

public fun pay(sc: &mut Scenario, show: ID) {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, payment_slot(&payment))));
    let s = sc.take_shared_by_id<PaymentRefShard>(shard_id(&c, rs::shard_index_for_ref(&c, payment_ref_of(&payment))));
    rs::issue_paid(&c, &mut p, &s, &cap, payment, sc.ctx());
    ts::return_shared(s); ts::return_shared(p); ts::return_shared(c);
    sc.return_to_sender(cap);
}
public fun unpaid(sc: &mut Scenario, show: ID) {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    let payment = sc.take_from_sender<IssuancePayment>();
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, payment_slot(&payment))));
    let mut s = sc.take_shared_by_id<PaymentRefShard>(shard_id(&c, rs::shard_index_for_ref(&c, payment_ref_of(&payment))));
    rs::cancel_issuance(&c, &mut p, &mut s, &cap, payment, sc.ctx());
    ts::return_shared(s); ts::return_shared(p); ts::return_shared(c);
    sc.return_to_sender(cap);
}

// IssuancePayment fields are private to the package module; read them back by value
// through its public view functions.
fun payment_slot(p: &IssuancePayment): u64 { rs::payment_slot(p) }
fun payment_ref_of(p: &IssuancePayment): vector<u8> { rs::payment_ref(p) }

// ---------------------------------------------------------------- more fixtures

public fun take_pages(sc: &Scenario, c: &ShowControl): vector<InventoryPage> {
    let mut pages = vector[];
    let mut i = 0;
    while (i < rs::control_page_count(c)) {
        pages.push_back(sc.take_shared_by_id<InventoryPage>(page_id(c, i)));
        i = i + 1;
    };
    pages
}
public fun return_pages(mut pages: vector<InventoryPage>) {
    while (!pages.is_empty()) { ts::return_shared(pages.pop_back()); };
    pages.destroy_empty();
}

/// Issues slots [from, to), at most `ISSUE_BATCH` per transaction (two events each, against
/// the per-transaction event limit), all with expected generation `generation`.
public fun issue_range(sc: &mut Scenario, show: ID, from: u64, to: u64, generation: u64, holder: address) {
    let mut at = from;
    while (at < to) {
        let end = if (to - at > ISSUE_BATCH) at + ISSUE_BATCH else to;
        sc.next_tx(A);
        let c = sc.take_shared_by_id<ShowControl>(show);
        let cap = sc.take_from_sender<IssuerCap>();
        let mut pages = take_pages(sc, &c);
        let mut slot = at;
        while (slot < end) {
            let idx = rs::page_index_for_slot(&c, slot);
            rs::issue(&c, pages.borrow_mut(idx), &cap, slot, generation, holder, sc.ctx());
            slot = slot + 1;
        };
        return_pages(pages);
        ts::return_shared(c);
        sc.return_to_sender(cap);
        at = end;
    };
}

/// One PTB-shaped bundle: declares `declared`, then issues `issues` consecutive slots.
public fun bundle(sc: &mut Scenario, show: ID, first: u64, declared: u64, issues: u64, holder: address) {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    let mut pages = take_pages(sc, &c);
    let mut b: Bundle = rs::begin_bundle(&c, declared);
    let mut i = 0;
    while (i < issues) {
        let slot = first + i;
        let idx = rs::page_index_for_slot(&c, slot);
        rs::bundle_issue(&mut b, &c, pages.borrow_mut(idx), &cap, slot, 0, holder, sc.ctx());
        i = i + 1;
    };
    rs::finish_bundle(b);
    return_pages(pages);
    ts::return_shared(c);
    sc.return_to_sender(cap);
}

public fun issue_as(sc: &mut Scenario, sender: address, show: ID, slot: u64, generation: u64, holder: address) {
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, slot)));
    let cap = sc.take_from_sender<IssuerCap>();
    rs::issue(&c, &mut p, &cap, slot, generation, holder, sc.ctx());
    ts::return_shared(p); ts::return_shared(c);
    sc.return_to_sender(cap);
}

/// Explicit object choice, for the cross-show and wrong-page predicates.
public fun issue_with(sc: &mut Scenario, control: ID, page: ID, slot: u64, generation: u64, holder: address) {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(control);
    let mut p = sc.take_shared_by_id<InventoryPage>(page);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::issue(&c, &mut p, &cap, slot, generation, holder, sc.ctx());
    ts::return_shared(p); ts::return_shared(c);
    sc.return_to_sender(cap);
}

public fun offer_with(sc: &mut Scenario, sender: address, control: ID, page: ID, ticket: ID, version: u64,
    recipient: address, amount: u64) {
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(control);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let clk = sc.take_shared<Clock>();
    rs::offer(&c, &p, &mut t, version, recipient, amount, 600000, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(t); ts::return_shared(p); ts::return_shared(c);
}
public fun page_of(sc: &mut Scenario, show: ID, ticket: ID): ID {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let t = sc.take_shared_by_id<Ticket>(ticket);
    let id = page_id(&c, rs::page_index_for_slot(&c, rs::slot(&t)));
    ts::return_shared(t); ts::return_shared(c);
    id
}
public fun offer(sc: &mut Scenario, sender: address, show: ID, ticket: ID, version: u64, recipient: address,
    amount: u64) {
    let page = page_of(sc, show, ticket);
    offer_with(sc, sender, show, page, ticket, version, recipient, amount);
}
public fun accept_gift(sc: &mut Scenario, sender: address, show: ID, ticket: ID) {
    let page = page_of(sc, show, ticket);
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let clk = sc.take_shared<Clock>();
    rs::accept_gift(&c, &p, &mut t, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(t); ts::return_shared(p); ts::return_shared(c);
}
public fun authorize(sc: &mut Scenario, sender: address, show: ID, ticket: ID, version: u64) {
    let page = page_of(sc, show, ticket);
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let clk = sc.take_shared<Clock>();
    rs::authorize_admission(&c, &p, &mut t, version, GATE, request(), 100000, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(t); ts::return_shared(p); ts::return_shared(c);
}
public fun consume(sc: &mut Scenario, show: ID, ticket: ID, version: u64) {
    let page = page_of(sc, show, ticket);
    sc.next_tx(GATE);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let clk = sc.take_shared<Clock>();
    rs::consume(&c, &p, &mut t, version, request(), &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(t); ts::return_shared(p); ts::return_shared(c);
}
public fun attest_payment(sc: &mut Scenario, show: ID, ticket: ID, payment_ref: vector<u8>) {
    let page = page_of(sc, show, ticket);
    sc.next_tx(ATT);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut s = sc.take_shared_by_id<PaymentRefShard>(shard_id(&c, rs::shard_index_for_ref(&c, copy payment_ref)));
    let t = sc.take_shared_by_id<Ticket>(ticket);
    let clk = sc.take_shared<Clock>();
    rs::attest_payment(&c, &p, &mut s, &t, payment_ref, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(t); ts::return_shared(s); ts::return_shared(p); ts::return_shared(c);
}
public fun accept_sale(sc: &mut Scenario, sender: address, show: ID, ticket: ID) {
    let page = page_of(sc, show, ticket);
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let evidence = sc.take_from_sender<PaymentEvidence>();
    let clk = sc.take_shared<Clock>();
    rs::accept_sale(&c, &p, &mut t, evidence, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_shared(t); ts::return_shared(p); ts::return_shared(c);
}
public fun revoke(sc: &mut Scenario, show: ID, ticket: ID) {
    let page = page_of(sc, show, ticket);
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(page);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::revoke(&c, &mut p, &cap, &mut t, sc.ctx());
    ts::return_shared(t); ts::return_shared(p); ts::return_shared(c);
    sc.return_to_sender(cap);
}
/// Reserve against an explicitly chosen shard (EShard when it is not the routed one).
public fun reserve_in_shard(sc: &mut Scenario, show: ID, slot: u64, buyer: address, payment_ref: vector<u8>,
    shard_index: u64) {
    sc.next_tx(ATT);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(page_id(&c, rs::page_index_for_slot(&c, slot)));
    let mut s = sc.take_shared_by_id<PaymentRefShard>(shard_id(&c, shard_index));
    rs::attest_issuance(&c, &mut p, &mut s, slot, 0, buyer, 50000, payment_ref, sc.ctx());
    ts::return_shared(s); ts::return_shared(p); ts::return_shared(c);
}

/// Checks the conservation sum on every page and returns (free, reserved, issued, retired).
public fun totals(sc: &mut Scenario, show: ID): (u64, u64, u64, u64) {
    sc.next_tx(A);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let pages = take_pages(sc, &c);
    let (mut free, mut reserved, mut issued, mut retired, mut size) = (0, 0, 0, 0, 0);
    let mut i = 0;
    while (i < pages.length()) {
        let p = &pages[i];
        assert!(rs::page_conserved(p));
        free = free + rs::page_free(p); reserved = reserved + rs::page_reserved(p);
        issued = issued + rs::page_issued(p); retired = retired + rs::page_retired(p);
        size = size + rs::page_end(p) - rs::page_start(p);
        i = i + 1;
    };
    assert!(size == rs::control_capacity(&c));
    return_pages(pages);
    ts::return_shared(c);
    (free, reserved, issued, retired)
}
