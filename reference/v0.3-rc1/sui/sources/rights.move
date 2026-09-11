/// PROTOTYPE SOURCE: not compiled or deployed in the authoring environment.
/// 16 inventory slots. Public gifts/resale + optional private admission only.
/// Fiat evidence is an authorized attester assertion, never proof of bank funds.
module kix::rights;
use sui::clock::{Self, Clock};
use sui::event;
use sui::poseidon;
use kix::zk_gate::{Self, Verifier};

const EClosed: u64 = 1;
const ENotHolder: u64 = 2;
const EStale: u64 = 3;
const EAuthority: u64 = 4;
const ELocked: u64 = 5;
const EPolicy: u64 = 6;
const EPayment: u64 = 7;
const EProof: u64 = 8;
const EInventory: u64 = 9;
const ACTIVE: u8 = 0;
const CONSUMED: u8 = 1;
const VOID: u8 = 2;
const SHIELDED: u8 = 3;
const FR: u256 = 21888242871839275222246405745257275088548364400416034343698204186575808495617;

public struct Show has key {
    id: UID,
    issuer: address,
    open: bool,
    capacity: u64,
    issued: u64,
    generations: vector<u64>,
    occupied: vector<bool>,
    gates: vector<address>,
    payment_attesters: vector<address>,
    payment_refs: vector<vector<u8>>,
    resale_cap: u64,
    organizer_bps: u64,
    platform_bps: u64,
    verifier: ID,
    domain: u256,
    notes: vector<u256>,
    nullifiers: vector<u256>,
    spent_challenges: vector<u256>,
}
public struct IssuerCap has key { id: UID, show: ID }
public struct Terms has copy, drop {
    show: ID, ticket: ID, version: u64, seller: address, buyer: address, amount: u64,
    expires_ms: u64, organizer_bps: u64, platform_bps: u64,
}
public struct Offer has copy, drop, store {
    recipient: address, amount: u64, expires_ms: u64, version: u64, terms: vector<u8>,
}
public struct Admission has copy, drop, store {
    gate: address, expires_ms: u64, version: u64, request: vector<u8>,
}
public struct Ticket has key {
    id: UID, show: ID, slot: u64, generation: u64, holder: address,
    version: u64, state: u8, offer: Option<Offer>, admission: Option<Admission>,
    last_payment: vector<u8>, last_amount: u64, last_payer: address,
}
public struct PaymentEvidence has key {
    id: UID, show: ID, ticket: ID, version: u64, buyer: address, seller: address,
    amount: u64, terms: vector<u8>, payment_ref: vector<u8>,
}
public struct Change has copy, drop {
    show: ID, ticket: ID, version: u64, state: u8, holder: address, kind: u8,
}
public struct Allocation has copy, drop {
    show: ID, ticket: ID, payment: vector<u8>, seller: address,
    total: u64, seller_due: u64, organizer_due: u64, platform_due: u64,
}
public struct PrivateAdmission has copy, drop {
    show: ID, nullifier: u256, gate: address, challenge: u256,
}
public struct RefundDutyRequested has copy, drop {
    show: ID, ticket: ID, beneficiary: address, amount: u64, payment_ref: vector<u8>,
}

public fun create_show(capacity: u64, gates: vector<address>, payment_attesters: vector<address>,
    payment_refs: vector<vector<u8>>,
    resale_cap: u64, organizer_bps: u64, platform_bps: u64, verifier: ID, ctx: &mut TxContext) {
    assert!(capacity > 0 && capacity <= 16 && !gates.is_empty(), EPolicy);
    assert!(organizer_bps <= 10000 && platform_bps <= 10000 && organizer_bps + platform_bps <= 10000, EPolicy);
    let id = object::new(ctx);
    let show_id = object::uid_to_inner(&id);
    let domain = sui::address::to_u256(object::id_to_address(&show_id)) % FR;
    let mut generations = vector[];
    let mut occupied = vector[];
    let mut i = 0;
    while (i < 16) { generations.push_back(0); occupied.push_back(false); i = i + 1; };
    transfer::transfer(IssuerCap { id: object::new(ctx), show: show_id }, ctx.sender());
    transfer::share_object(Show { id, issuer: ctx.sender(), open: true, capacity, issued: 0,
        generations, occupied, gates, payment_attesters, payment_refs: vector[], resale_cap, organizer_bps, platform_bps,
        verifier, domain, notes: vector[], nullifiers: vector[], spent_challenges: vector[] });
}

fun authority(s: &Show, cap: &IssuerCap) { assert!(cap.show == object::id(s), EAuthority); }
fun live(s: &Show, t: &Ticket, version: u64) {
    assert!(s.open && t.state == ACTIVE, EClosed);
    assert!(t.show == object::id(s) && t.generation == s.generations[t.slot] && t.version == version, EStale);
}
fun changed(t: &Ticket, kind: u8) {
    event::emit(Change { show: t.show, ticket: object::id(t), version: t.version,
        state: t.state, holder: t.holder, kind });
}
fun idle(t: &Ticket, c: &Clock) {
    assert!(t.offer.is_none() || c.timestamp_ms() >= t.offer.borrow().expires_ms, ELocked);
    assert!(t.admission.is_none() || c.timestamp_ms() >= t.admission.borrow().expires_ms, ELocked);
}

public fun issue(s: &mut Show, cap: &IssuerCap, slot: u64, holder: address, ctx: &mut TxContext) {
    authority(s,cap);
    assert!(s.open && slot < s.capacity && !s.occupied[slot], EInventory);
    s.occupied[slot] = true; s.generations[slot] = s.generations[slot] + 1; s.issued = s.issued + 1;
    let t = Ticket { id: object::new(ctx), show: object::id(s), slot, generation: s.generations[slot], holder,
        version: 1, state: ACTIVE, offer: option::none(), admission: option::none(), last_payment: vector[], last_amount: 0, last_payer: holder };
    changed(&t,0); transfer::share_object(t);
}

public fun offer(s: &Show, t: &mut Ticket, version: u64, recipient: address, amount: u64,
    expires_ms: u64, c: &Clock, ctx: &TxContext) {
    live(s,t,version); assert!(t.holder == ctx.sender(), ENotHolder); idle(t,c);
    assert!(recipient != t.holder && amount <= s.resale_cap && expires_ms > c.timestamp_ms()
        && expires_ms - c.timestamp_ms() <= 900000, EPolicy);
    let terms = sui::hash::blake2b256(&std::bcs::to_bytes(&Terms { show: object::id(s), ticket: object::id(t), version,
        seller: t.holder, buyer: recipient, amount, expires_ms, organizer_bps: s.organizer_bps, platform_bps: s.platform_bps }));
    t.offer = option::some(Offer { recipient, amount, expires_ms, version, terms });
    t.admission = option::none();
}
fun accepted(s: &Show, t: &Ticket, c: &Clock, ctx: &TxContext): Offer {
    live(s,t,t.version); assert!(t.offer.is_some(), ELocked);
    let o = *t.offer.borrow();
    assert!(o.recipient == ctx.sender() && o.version == t.version && c.timestamp_ms() < o.expires_ms, EStale);
    o
}
fun transfer_right(t: &mut Ticket, recipient: address) {
    t.holder = recipient; t.version = t.version + 1;
    t.offer = option::none(); t.admission = option::none(); changed(t,1);
}
public fun accept_gift(s: &Show, t: &mut Ticket, c: &Clock, ctx: &TxContext) {
    let o = accepted(s,t,c,ctx); assert!(o.amount == 0, EPayment);
    transfer_right(t,o.recipient);
}
public fun cancel_offer(t: &mut Ticket, ctx: &TxContext) {
    assert!(t.holder == ctx.sender(), ENotHolder); t.offer = option::none();
}

/// An external attester is trusted ONLY for the asserted fiat fact.
/// The chain prevents reusing the evidence object and checks all offer bindings.
public fun attest_payment(s: &mut Show, t: &Ticket, payment_ref: vector<u8>, c: &Clock, ctx: &mut TxContext) {
    assert!(s.payment_attesters.contains(&ctx.sender()), EAuthority);
    live(s,t,t.version); assert!(t.offer.is_some(), EPayment);
    let o = *t.offer.borrow(); assert!(o.amount > 0 && c.timestamp_ms() < o.expires_ms && payment_ref.length() == 32, EPayment);
    assert!(!s.payment_refs.contains(&payment_ref), EPayment);
    s.payment_refs.push_back(payment_ref);
    transfer::transfer(PaymentEvidence { id: object::new(ctx), show: t.show, ticket: object::id(t),
        version: t.version, buyer: o.recipient, seller: t.holder, amount: o.amount, terms: o.terms, payment_ref }, o.recipient);
}
public fun accept_sale(s: &Show, t: &mut Ticket, payment: PaymentEvidence, c: &Clock, ctx: &TxContext) {
    let o = accepted(s,t,c,ctx);
    let PaymentEvidence { id, show, ticket, version, buyer, seller, amount, terms, payment_ref } = payment;
    assert!(show == t.show && ticket == object::id(t) && version == t.version && buyer == o.recipient
        && seller == t.holder && amount == o.amount && amount > 0 && terms == o.terms, EPayment);
    object::delete(id);
    let organizer_due = ((amount as u128) * (s.organizer_bps as u128) / 10000) as u64;
    let platform_due = ((amount as u128) * (s.platform_bps as u128) / 10000) as u64;
    event::emit(Allocation { show, ticket, payment: payment_ref, seller, total: amount,
        seller_due: amount - organizer_due - platform_due, organizer_due, platform_due });
    t.last_payment = payment_ref; t.last_amount = amount; t.last_payer = buyer; transfer_right(t,buyer);
}

public fun authorize_admission(s: &Show, t: &mut Ticket, version: u64, gate: address,
    request: vector<u8>, expires_ms: u64, c: &Clock, ctx: &TxContext) {
    live(s,t,version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t,c);
    assert!(s.gates.contains(&gate) && request.length() == 32 && expires_ms > c.timestamp_ms()
        && expires_ms - c.timestamp_ms() <= 120000, EPolicy);
    t.offer = option::none(); t.admission = option::some(Admission { gate, expires_ms, version, request });
}
public fun consume(s: &Show, t: &mut Ticket, version: u64, request: vector<u8>, c: &Clock, ctx: &TxContext) {
    live(s,t,version); assert!(s.gates.contains(&ctx.sender()) && t.admission.is_some(), EAuthority);
    let a = *t.admission.borrow();
    assert!(a.gate == ctx.sender() && a.version == version && a.request == request && c.timestamp_ms() < a.expires_ms, EStale);
    t.state = CONSUMED; t.version = t.version + 1; t.admission = option::none(); t.offer = option::none(); changed(t,2);
}
public fun refund(s: &mut Show, t: &mut Ticket, version: u64, c: &Clock, ctx: &TxContext) {
    live(s,t,version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t,c);
    t.state = VOID; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    s.occupied[t.slot] = false;
    event::emit(RefundDutyRequested { show: t.show, ticket: object::id(t), beneficiary: t.last_payer,
        amount: t.last_amount, payment_ref: t.last_payment });
    changed(t,3);
}
public fun cancel_show(s: &mut Show, cap: &IssuerCap) { authority(s,cap); s.open = false; }
public fun revoke(s: &mut Show, cap: &IssuerCap, t: &mut Ticket) {
    authority(s,cap); assert!(t.show == object::id(s) && t.generation == s.generations[t.slot], EStale);
    s.generations[t.slot] = s.generations[t.slot] + 1;
    t.state = VOID; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    // Revocation does NOT reopen inventory: private/physical use could be unknown.
    changed(t,4);
}

fun merkle(mut leaves: vector<u256>): u256 {
    while (leaves.length() < 16) { leaves.push_back(0); };
    while (leaves.length() > 1) {
        let mut next = vector[]; let mut i = 0;
        while (i < leaves.length()) {
            next.push_back(poseidon::poseidon_bn254(&vector[leaves[i], leaves[i+1]])); i = i + 2;
        };
        leaves = next;
    };
    leaves[0]
}
public fun note_root(s: &Show): u256 { merkle(s.notes) }
public fun revocation_root(s: &Show): u256 {
    let mut leaves = vector[]; let mut i = 0;
    while (i < 16) {
        leaves.push_back(poseidon::poseidon_bn254(&vector[(i as u256), (s.generations[i] as u256), s.domain, 3]));
        i = i + 1;
    };
    merkle(leaves)
}
public fun shield(s: &mut Show, t: &mut Ticket, version: u64, commitment: u256,
    proof: vector<u8>, v: &Verifier, c: &Clock, ctx: &TxContext) {
    live(s,t,version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t,c);
    assert!(s.verifier == object::id(v) && s.notes.length() < 16 && commitment > 0 && commitment < FR, EProof);
    zk_gate::mint(v,vector[commitment,(t.slot as u256),(t.generation as u256),s.domain],proof);
    t.state = SHIELDED; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    s.notes.push_back(commitment); changed(t,5);
}
public fun consume_private(s: &mut Show, v: &Verifier, nullifier: u256, challenge: u256,
    expires_ms: u64, proof: vector<u8>, c: &Clock, ctx: &TxContext) {
    assert!(s.open && s.gates.contains(&ctx.sender()) && s.verifier == object::id(v), EAuthority);
    assert!(nullifier > 0 && nullifier < FR && challenge > 0 && challenge < FR
        && !s.nullifiers.contains(&nullifier) && !s.spent_challenges.contains(&challenge), EProof);
    assert!(expires_ms > c.timestamp_ms() && expires_ms - c.timestamp_ms() <= 120000, EPolicy);
    let gate = sui::address::to_u256(ctx.sender());
    let context = poseidon::poseidon_bn254(&vector[gate % 340282366920938463463374607431768211456,
        gate / 340282366920938463463374607431768211456, challenge, (expires_ms as u256), 1]);
    zk_gate::spend(v,vector[note_root(s), revocation_root(s), nullifier, context, s.domain, 1],proof);
    s.nullifiers.push_back(nullifier); s.spent_challenges.push_back(challenge);
    event::emit(PrivateAdmission { show: object::id(s), nullifier, gate: ctx.sender(), challenge });
    // No public ticketId is needed for private admission. A SHIELDED inventory
    // slot cannot be resold/refunded/reissued by this deliberately limited profile.
}

public fun holder(t: &Ticket): address { t.holder }
public fun version(t: &Ticket): u64 { t.version }
public fun state(t: &Ticket): u8 { t.state }
