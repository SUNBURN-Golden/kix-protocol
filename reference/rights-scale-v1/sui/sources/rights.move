/// Public, localnet-only scale profile. Legacy kix::rights is unchanged.
module kix_scale::rights;
use sui::clock::{Self, Clock};
use sui::event;
use sui::derived_object;
use sui::table::{Self, Table};

const EClosed: u64 = 1;
const ENotHolder: u64 = 2;
const EStale: u64 = 3;
const EAuthority: u64 = 4;
const ELocked: u64 = 5;
const EPolicy: u64 = 6;
const EPayment: u64 = 7;
const EShard: u64 = 8;
const EInventory: u64 = 9;
const ACTIVE: u8 = 0;
const CONSUMED: u8 = 1;
const VOID: u8 = 2;
const ESetup: u64 = 10;
const PAGE_SIZE: u64 = 256;
const SHARD_COUNT: u64 = 16;
const MAX_CAPACITY: u64 = 65536;
const DIRECT: u8 = 0;
const PAID: u8 = 1;


/// Construction writes this object; active issuance only reads it.
public struct ShowControl has key {
    id: UID, issuer: address, open: bool, sealed: bool, capacity: u64,
    pages_created: u64, shards_created: u64,
    gates: vector<address>, payment_attesters: vector<address>,
    resale_cap: u64, organizer_bps: u64, platform_bps: u64,
}
public struct PageKey has copy, drop, store { index: u64 }
public struct ShardKey has copy, drop, store { index: u64 }
public struct InventoryPage has key {
    id: UID, show: ID, index: u64, start: u64,
    generations: vector<u64>, occupied: vector<bool>, issued: u64,
}
public struct PaymentRefShard has key {
    id: UID, show: ID, index: u64, refs: Table<vector<u8>, bool>,
}
public struct PageCreated has copy, drop { show: ID, page: ID, index: u64, start: u64, length: u64 }
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
public struct RefundDutyRequested has copy, drop {
    show: ID, ticket: ID, beneficiary: address, amount: u64, payment_ref: vector<u8>,
}
/// Observes a minted right. `kind` 0 is a direct grant; `kind` 1 is primary
/// issuance bound to an attester assertion. Not a fungible coin and not cash.
public struct Issuance has copy, drop {
    show: ID, ticket: ID, slot: u64, generation: u64, holder: address,
    kind: u8, amount: u64, payment_ref: vector<u8>,
}
/// Slot reservation for primary issuance. Owned by the show issuer until
/// `issue_paid` or `cancel_issuance`. Not transferable outside this module.
public struct IssuancePayment has key {
    id: UID, show: ID, slot: u64, generation: u64, buyer: address, amount: u64, payment_ref: vector<u8>,
}

public fun create_show(capacity: u64, gates: vector<address>, payment_attesters: vector<address>,
    resale_cap: u64, organizer_bps: u64, platform_bps: u64, ctx: &mut TxContext) {
    assert!(capacity > 0 && capacity <= MAX_CAPACITY && !gates.is_empty(), EPolicy);
    assert!(gates.length() <= 16 && payment_attesters.length() <= 16, EPolicy);
    assert!(organizer_bps <= 10000 && platform_bps <= 10000 && organizer_bps + platform_bps <= 10000, EPolicy);
    let id = object::new(ctx); let show = id.to_inner();
    transfer::transfer(IssuerCap { id: object::new(ctx), show }, ctx.sender());
    transfer::share_object(ShowControl { id, issuer: ctx.sender(), open: false, sealed: false,
        capacity, pages_created: 0, shards_created: 0, gates, payment_attesters,
        resale_cap, organizer_bps, platform_bps });
}
fun authority(s: &ShowControl, cap: &IssuerCap) { assert!(cap.show == object::id(s), EAuthority); }
fun issuer(s: &ShowControl, ctx: &TxContext) { assert!(ctx.sender() == s.issuer, EAuthority); }
public fun page_count(s: &ShowControl): u64 { (s.capacity + PAGE_SIZE - 1) / PAGE_SIZE }
public fun page_id(s: &ShowControl, index: u64): ID {
    object::id_from_address(derived_object::derive_address(object::id(s), PageKey { index }))
}
public fun shard_id(s: &ShowControl, index: u64): ID {
    object::id_from_address(derived_object::derive_address(object::id(s), ShardKey { index }))
}
public fun payment_shard(payment_ref: &vector<u8>): u64 {
    assert!(payment_ref.length() == 32, EPayment);
    let hash = sui::hash::blake2b256(payment_ref);
    (hash[0] as u64) % SHARD_COUNT
}
public fun create_page(s: &mut ShowControl, cap: &IssuerCap, index: u64) {
    authority(s, cap); assert!(!s.sealed && index < page_count(s), ESetup);
    let show = object::id(s); let start = index * PAGE_SIZE;
    let length = if (s.capacity - start < PAGE_SIZE) s.capacity - start else PAGE_SIZE;
    let mut generations = vector[]; let mut occupied = vector[]; let mut i = 0;
    while (i < length) { generations.push_back(0); occupied.push_back(false); i = i + 1; };
    let id = derived_object::claim(&mut s.id, PageKey { index });
    event::emit(PageCreated { show, page: id.to_inner(), index, start, length });
    s.pages_created = s.pages_created + 1;
    transfer::share_object(InventoryPage { id, show, index, start, generations, occupied, issued: 0 });
}
public fun create_payment_shard(s: &mut ShowControl, cap: &IssuerCap, index: u64, ctx: &mut TxContext) {
    authority(s, cap); assert!(!s.sealed && index < SHARD_COUNT, ESetup);
    let show = object::id(s); let id = derived_object::claim(&mut s.id, ShardKey { index });
    s.shards_created = s.shards_created + 1;
    transfer::share_object(PaymentRefShard { id, show, index, refs: table::new(ctx) });
}
public fun seal(s: &mut ShowControl, cap: &IssuerCap) {
    authority(s, cap);
    assert!(!s.sealed && s.pages_created == page_count(s) && s.shards_created == SHARD_COUNT, ESetup);
    s.sealed = true; s.open = true;
}
fun offset(s: &ShowControl, p: &InventoryPage, slot: u64): u64 {
    assert!(p.show == object::id(s) && object::id(p) == page_id(s, p.index), EStale);
    assert!(slot < s.capacity && slot >= p.start && slot - p.start < p.generations.length(), EInventory);
    slot - p.start
}
fun check_shard(s: &ShowControl, shard: &PaymentRefShard, payment_ref: &vector<u8>) {
    assert!(shard.show == object::id(s) && shard.index == payment_shard(payment_ref)
        && object::id(shard) == shard_id(s, shard.index), EShard);
}
fun live(s: &ShowControl, p: &InventoryPage, t: &Ticket, version: u64) {
    let i = offset(s, p, t.slot);
    assert!(s.open && t.state == ACTIVE, EClosed);
    assert!(t.show == object::id(s) && t.generation == p.generations[i] && t.version == version, EStale);
}
fun changed(t: &Ticket, kind: u8) {
    event::emit(Change { show: t.show, ticket: object::id(t), version: t.version,
        state: t.state, holder: t.holder, kind });
}
fun idle(t: &Ticket, c: &Clock) {
    assert!(t.offer.is_none() || c.timestamp_ms() >= t.offer.borrow().expires_ms, ELocked);
    assert!(t.admission.is_none() || c.timestamp_ms() >= t.admission.borrow().expires_ms, ELocked);
}

fun finish_issue(s: &ShowControl, p: &mut InventoryPage, slot: u64, holder: address, payment_ref: vector<u8>, amount: u64,
    payer: address, kind: u8, ctx: &mut TxContext) {
    let i = offset(s, p, slot);
    let next_generation = p.generations[i] + 1;
    *p.generations.borrow_mut(i) = next_generation;
    p.issued = p.issued + 1;
    let t = Ticket { id: object::new(ctx), show: object::id(s), slot, generation: next_generation, holder,
        version: 1, state: ACTIVE, offer: option::none(), admission: option::none(),
        last_payment: payment_ref, last_amount: amount, last_payer: payer };
    event::emit(Issuance { show: t.show, ticket: object::id(&t), slot: t.slot, generation: t.generation,
        holder: t.holder, kind, amount: t.last_amount, payment_ref: t.last_payment });
    changed(&t, 0);
    transfer::share_object(t);
}
public fun issue(s: &ShowControl, p: &mut InventoryPage, slot: u64, expected_generation: u64, holder: address, ctx: &mut TxContext) {
    issuer(s, ctx);
    let i = offset(s, p, slot);
    assert!(s.open && !p.occupied[i], EInventory);
    assert!(p.generations[i] == expected_generation, EStale);
    *p.occupied.borrow_mut(i) = true;
    finish_issue(s, p, slot, holder, vector[], 0, holder, DIRECT, ctx);
}

/// Reserves a free slot for primary issuance. Does not mint a Ticket.
/// The attester is trusted only for the asserted fiat fact.
public fun attest_issuance(s: &ShowControl, p: &mut InventoryPage, shard: &mut PaymentRefShard,
    slot: u64, expected_generation: u64, buyer: address, amount: u64,
    payment_ref: vector<u8>, ctx: &mut TxContext) {
    assert!(s.payment_attesters.contains(&ctx.sender()), EAuthority);
    assert!(s.open, EClosed);
    let i = offset(s, p, slot);
    assert!(!p.occupied[i] && p.generations[i] == expected_generation, EInventory);
    assert!(amount > 0 && payment_ref.length() == 32, EPayment);
    check_shard(s, shard, &payment_ref);
    assert!(!shard.refs.contains(payment_ref), EPayment);
    *p.occupied.borrow_mut(i) = true;
    shard.refs.add(payment_ref, true);
    transfer::transfer(IssuancePayment { id: object::new(ctx), show: object::id(s), slot, generation: expected_generation, buyer,
        amount, payment_ref }, s.issuer);
}
public fun cancel_issuance(s: &ShowControl, p: &mut InventoryPage, shard: &mut PaymentRefShard,
    payment: IssuancePayment, ctx: &TxContext) {
    issuer(s, ctx);
    let IssuancePayment { id, show, slot, generation, buyer: _, amount: _, payment_ref } = payment;
    assert!(show == object::id(s), EPayment);
    let i = offset(s, p, slot);
    assert!(p.occupied[i] && p.generations[i] == generation, EInventory);
    check_shard(s, shard, &payment_ref);
    let _ = shard.refs.remove(payment_ref);
    // Consume this reservation generation even if it never minted a ticket.
    *p.generations.borrow_mut(i) = generation + 1;
    object::delete(id);
    *p.occupied.borrow_mut(i) = false;
}
/// Mints the same public Ticket used by gifts, resale, admission and refund.
/// This public profile does not expose shield or private consumption.
public fun issue_paid(s: &ShowControl, p: &mut InventoryPage, shard: &PaymentRefShard, payment: IssuancePayment, ctx: &mut TxContext) {
    issuer(s, ctx);
    let IssuancePayment { id, show, slot, generation, buyer, amount, payment_ref } = payment;
    assert!(show == object::id(s), EPayment);
    assert!(s.open, EClosed);
    let i = offset(s, p, slot);
    assert!(p.occupied[i] && p.generations[i] == generation, EInventory);
    check_shard(s, shard, &payment_ref);
    assert!(amount > 0 && shard.refs.contains(payment_ref), EPayment);
    object::delete(id);
    finish_issue(s, p, slot, buyer, payment_ref, amount, buyer, PAID, ctx);
}

public fun offer(s: &ShowControl, p: &InventoryPage, t: &mut Ticket, version: u64, recipient: address, amount: u64,
    expires_ms: u64, c: &Clock, ctx: &TxContext) {
    live(s,p,t,version); assert!(t.holder == ctx.sender(), ENotHolder); idle(t,c);
    assert!(recipient != t.holder && amount <= s.resale_cap && expires_ms > c.timestamp_ms()
        && expires_ms - c.timestamp_ms() <= 900000, EPolicy);
    let terms = sui::hash::blake2b256(&std::bcs::to_bytes(&Terms { show: object::id(s), ticket: object::id(t), version,
        seller: t.holder, buyer: recipient, amount, expires_ms, organizer_bps: s.organizer_bps, platform_bps: s.platform_bps }));
    t.offer = option::some(Offer { recipient, amount, expires_ms, version, terms });
    t.admission = option::none();
}
fun accepted(s: &ShowControl, p: &InventoryPage, t: &Ticket, c: &Clock, ctx: &TxContext): Offer {
    live(s,p,t,t.version); assert!(t.offer.is_some(), ELocked);
    let o = *t.offer.borrow();
    assert!(o.recipient == ctx.sender() && o.version == t.version && c.timestamp_ms() < o.expires_ms, EStale);
    o
}
fun transfer_right(t: &mut Ticket, recipient: address) {
    t.holder = recipient; t.version = t.version + 1;
    t.offer = option::none(); t.admission = option::none(); changed(t,1);
}
public fun accept_gift(s: &ShowControl, p: &InventoryPage, t: &mut Ticket, c: &Clock, ctx: &TxContext) {
    let o = accepted(s,p,t,c,ctx); assert!(o.amount == 0, EPayment);
    transfer_right(t,o.recipient);
}
public fun cancel_offer(t: &mut Ticket, ctx: &TxContext) {
    assert!(t.holder == ctx.sender(), ENotHolder); t.offer = option::none();
}

/// An external attester is trusted ONLY for the asserted fiat fact.
/// The chain prevents reusing the evidence object and checks all offer bindings.
public fun attest_payment(s: &ShowControl, p: &InventoryPage, shard: &mut PaymentRefShard, t: &Ticket, payment_ref: vector<u8>, c: &Clock, ctx: &mut TxContext) {
    assert!(s.payment_attesters.contains(&ctx.sender()), EAuthority);
    live(s,p,t,t.version); assert!(t.offer.is_some(), EPayment);
    let o = *t.offer.borrow(); assert!(o.amount > 0 && c.timestamp_ms() < o.expires_ms && payment_ref.length() == 32, EPayment);
    check_shard(s, shard, &payment_ref);
    assert!(!shard.refs.contains(payment_ref), EPayment);
    shard.refs.add(payment_ref, true);
    transfer::transfer(PaymentEvidence { id: object::new(ctx), show: t.show, ticket: object::id(t),
        version: t.version, buyer: o.recipient, seller: t.holder, amount: o.amount, terms: o.terms, payment_ref }, o.recipient);
}
public fun accept_sale(s: &ShowControl, p: &InventoryPage, t: &mut Ticket, payment: PaymentEvidence, c: &Clock, ctx: &TxContext) {
    let o = accepted(s,p,t,c,ctx);
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

public fun authorize_admission(s: &ShowControl, p: &InventoryPage, t: &mut Ticket, version: u64, gate: address,
    request: vector<u8>, expires_ms: u64, c: &Clock, ctx: &TxContext) {
    live(s,p,t,version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t,c);
    assert!(s.gates.contains(&gate) && request.length() == 32 && expires_ms > c.timestamp_ms()
        && expires_ms - c.timestamp_ms() <= 120000, EPolicy);
    t.offer = option::none(); t.admission = option::some(Admission { gate, expires_ms, version, request });
}
public fun consume(s: &ShowControl, p: &InventoryPage, t: &mut Ticket, version: u64, request: vector<u8>, c: &Clock, ctx: &TxContext) {
    live(s,p,t,version); assert!(s.gates.contains(&ctx.sender()) && t.admission.is_some(), EAuthority);
    let a = *t.admission.borrow();
    assert!(a.gate == ctx.sender() && a.version == version && a.request == request && c.timestamp_ms() < a.expires_ms, EStale);
    t.state = CONSUMED; t.version = t.version + 1; t.admission = option::none(); t.offer = option::none(); changed(t,2);
}
public fun refund(s: &ShowControl, p: &mut InventoryPage, t: &mut Ticket, version: u64, c: &Clock, ctx: &TxContext) {
    live(s,p,t,version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t,c);
    t.state = VOID; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    let i = offset(s, p, t.slot);
    *p.occupied.borrow_mut(i) = false;
    event::emit(RefundDutyRequested { show: t.show, ticket: object::id(t), beneficiary: t.last_payer,
        amount: t.last_amount, payment_ref: t.last_payment });
    changed(t,3);
}
public fun cancel_show(s: &mut ShowControl, cap: &IssuerCap) { authority(s,cap); assert!(s.sealed, ESetup); s.open = false; }
public fun revoke(s: &ShowControl, p: &mut InventoryPage, t: &mut Ticket, ctx: &TxContext) {
    issuer(s,ctx); let i = offset(s, p, t.slot);
    assert!(t.show == object::id(s) && t.generation == p.generations[i], EStale);
    *p.generations.borrow_mut(i) = p.generations[i] + 1;
    t.state = VOID; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    // Revocation does NOT reopen inventory: private/physical use could be unknown.
    changed(t,4);
}

public fun holder(t: &Ticket): address { t.holder }
public fun version(t: &Ticket): u64 { t.version }
public fun state(t: &Ticket): u8 { t.state }
public fun slot(t: &Ticket): u64 { t.slot }
public fun generation(t: &Ticket): u64 { t.generation }
public fun last_amount(t: &Ticket): u64 { t.last_amount }
public fun last_payer(t: &Ticket): address { t.last_payer }
public fun last_payment(t: &Ticket): vector<u8> { t.last_payment }


public fun capacity(s: &ShowControl): u64 { s.capacity }
public fun is_open(s: &ShowControl): bool { s.open }
public fun page_start(p: &InventoryPage): u64 { p.start }
public fun page_length(p: &InventoryPage): u64 { p.generations.length() }
public fun slot_generation(s: &ShowControl, p: &InventoryPage, slot: u64): u64 { p.generations[offset(s,p,slot)] }
public fun occupied(s: &ShowControl, p: &InventoryPage, slot: u64): bool { p.occupied[offset(s,p,slot)] }
