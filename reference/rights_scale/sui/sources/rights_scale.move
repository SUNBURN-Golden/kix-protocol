/// LOCALNET PROTOTYPE, RS-1 + RS-2: the public and private paths of the extended rights
/// profile (docs/contracts/RIGHTS_SCALE_PROFILE.md, draft 0.1). Not production, not measured.
///
/// Authority is split into independent shared objects: a read-mostly `ShowControl`,
/// `InventoryPage`s whose IDs are `derived_object` claims on the control's UID, and
/// `PaymentRefShard`s routed by payment-reference bytes. RS-2 adds the private path:
/// one `NoteTree` (RR-1, RR-5), one `RevocationState` holding only the sparse revocation
/// root (RR-2, RR-3, RR-6), and `NullifierShard`s / `ChallengeShard`s routed by the hash
/// of the nullifier or challenge alone (RS-C09, RS-C11, RS-C17). The private objects are
/// opt-in per show (`claim_zk`, before `seal`), so the RS-1 public path is unchanged.
/// RS-3a adds page-level delegation (profile section 10): one shared `GrantControl`
/// per grant, the page's `delegated_to` binding, grant-checked delegated
/// consumption paths and the revocation cut as a single write on the grant.
/// GA redistribution remains deliberately absent (RS-C02 sentence 2:
/// DECISION_REQUIRED, Astra).
/// Fiat evidence is an authorized attester assertion, never proof of bank funds.
/// No coin, TIX or other economic-asset type is defined by this package.
module kix_rights_scale::rights_scale;
use sui::bcs;
use sui::clock::Clock;
use sui::derived_object;
use sui::event;
use sui::hash;
use sui::poseidon;
use sui::table::{Self, Table};
use kix_rights_scale::zk_gate::{Self, Verifier};

const EClosed: u64 = 1;
const ENotHolder: u64 = 2;
const EStale: u64 = 3;
const EAuthority: u64 = 4;
const ELocked: u64 = 5;
const EPolicy: u64 = 6;
const EPayment: u64 = 7;
const EProof: u64 = 8;
const EInventory: u64 = 9;
const EBundleTooLarge: u64 = 10;
const EBundleIncomplete: u64 = 11;
const EBundleMismatch: u64 = 12;
const ESealed: u64 = 13;
const ENotComplete: u64 = 14;
const EPage: u64 = 15;
const EShard: u64 = 16;
const ERange: u64 = 17;
// RS-2. A proof the verifier rejects aborts inside kix_rights_scale::zk_gate (code 2).
const EZk: u64 = 18;           // private path not enabled, or a wrong / missing private-path object
const ERoot: u64 = 19;         // note root outside the history, or a revocation witness not matching the root
const ETreeFull: u64 = 20;     // note tree leaf capacity reached
const ERootRequired: u64 = 21; // plain `revoke` on a show whose revocation root must be updated
const EVerifier: u64 = 22;     // `claim_zk` with a verifier object that is not the one pinned at creation
const EDelegated: u64 = 23;    // RS-3a: direct call on a delegated page, or a delegated call with the wrong grant/page
const EGrantClosed: u64 = 24;  // RS-3a: delegated path after the revocation cut, or a cut/reclaim in the wrong state

const ACTIVE: u8 = 0;
const CONSUMED: u8 = 1;
const VOID: u8 = 2;
const SHIELDED: u8 = 3;
const DIRECT: u8 = 0;
const PAID: u8 = 1;
const SEATED: u8 = 0;
const GA: u8 = 1;
const REF_PRIMARY: u8 = 1;
const REF_SECONDARY: u8 = 2;
const FR: u256 = 21888242871839275222246405745257275088548364400416034343698204186575808495617;

// Localnet defaults; Astra-owned. These are not protocol values; the operational
// values stay UNDETERMINED (profile section 13). Owner decision 2026-10-13.
// `LOCALNET_SHOW_SLOTS` is the owner's "P" (slots per show) and `LOCALNET_PAGE_SLOTS`
// the owner's "S" (slots per page). The profile contract uses P for page size and S
// for the shard count, so the names here spell the meaning out.
const PROFILE_VERSION: u64 = 1;
const MAX_BUNDLE_CHAIN: u64 = 8;
const LOCALNET_SHOW_SLOTS: u64 = 1024;
const LOCALNET_PAGE_SLOTS: u64 = 64;
// Not set by the owner decision: a fixture value chosen in RS-1's test matrix (1, 2, 4, 8).
const LOCALNET_PAYMENT_SHARDS: u64 = 4;
// RS-2 localnet fixture values; Astra-owned. None is a protocol value and none is an
// operational default: K, the shard counts and the depth stay UNDETERMINED for mainnet
// (profile sections 4 and 13). `ZK_DEPTH` is the depth of both trees and the width of the
// circuit's slot range check, so it also caps the slots of a show that enables the private path.
const ZK_DEPTH: u64 = 10;
const LOCALNET_ROOT_HISTORY_K: u64 = 4;
const LOCALNET_NULLIFIER_SHARDS: u64 = 4;
const LOCALNET_CHALLENGE_SHARDS: u64 = 4;

/// Key space of page claims. A different type from `ShardKey`, so the two derived
/// address spaces cannot collide even though both use small integers.
public struct PageKey has copy, drop, store { index: u64 }
public struct ShardKey has copy, drop, store { index: u64 }
/// RS-2 key spaces, each a type of its own so they cannot collide with pages, payment
/// shards or each other. `TreeKey` 0 is the note tree and 1 the revocation state.
public struct TreeKey has copy, drop, store { index: u64 }
public struct NullifierKey has copy, drop, store { index: u64 }
public struct ChallengeKey has copy, drop, store { index: u64 }

/// Temporary owned input of the issuer-signed operations (profile section 3 and 13).
/// Minted once to the publisher in `init`; `key` only, so no `public_transfer`, and
/// this package defines no transfer or burn function.
public struct IssuerCap has key { id: UID }

/// Shared, read-only after seal except for `cancel_show`. Holds no page ID list: page
/// and shard IDs are derived from this UID and a key.
public struct ShowControl has key {
    id: UID,
    issuer: address,
    profile_version: u64,
    open: bool,
    sealed: bool,
    cancel_generation: u64,
    verifier: ID,
    gates: vector<address>,
    payment_attesters: vector<address>,
    resale_cap: u64,
    organizer_bps: u64,
    platform_bps: u64,
    // Immutable range table. Seated slots are [0, seated_capacity) in pages of
    // `page_size`; GA slots are [seated_capacity, seated_capacity + ga_capacity).
    page_size: u64,
    seated_capacity: u64,
    ga_capacity: u64,
    seated_pages: u64,
    page_count: u64,
    shard_count: u64,
    // Creation staging.
    claimed_pages: u64,
    claimed_shards: u64,
    claim_sequence: u64,
    // RS-C11: Poseidon(show id mod FR, profile_version, manifest hash mod FR). Zero until
    // `claim_zk` enables the private path; fixed afterwards.
    domain: u256,
}

/// Owns the half-open slot range [start, end). Conservation: free + reserved +
/// issued + retired == end - start after every transition.
public struct InventoryPage has key {
    id: UID,
    show: ID,
    index: u64,
    start: u64,
    end: u64,
    mode: u8,
    generations: vector<u64>,
    occupied: vector<bool>,
    // Cumulative issuances on this page (u64); re-issuance makes it exceed the range.
    issuances: u64,
    free: u64,
    reserved: u64,
    issued: u64,
    retired: u64,
    // RS-3a: the id of the `GrantControl` this page is delegated to; `none` is the
    // direct issuer path. Set by `delegate_page`, cleared by `undelegate_page`.
    delegated_to: Option<ID>,
}

public struct PaymentRefShard has key {
    id: UID,
    show: ID,
    index: u64,
    refs: Table<vector<u8>, u8>,
}

/// RR-1 / RR-5: the one append-only incremental note tree of a show. Holds the frontier,
/// the root and the K most recent roots; leaves live in `NoteAdded` events.
public struct NoteTree has key {
    id: UID,
    show: ID,
    depth: u64,
    history_k: u64,
    leaf_count: u64,
    // Frontier: the left node pending at each level. `zeros[l]` is the root of an empty
    // subtree of height l (zeros[0] = 0), so `zeros[depth]` is the empty-tree root.
    frontier: vector<u256>,
    zeros: vector<u256>,
    root: u256,
    // The K most recent roots, current included. `head` is the oldest once the ring is full.
    roots: vector<u256>,
    head: u64,
}

/// RR-2 / RR-3 / RR-6: only the root of the slot-indexed sparse revocation tree is stored.
/// The leaf at a slot is the highest revoked generation of that slot (default 0). Only
/// `revoke_with_root` writes it; the caller supplies the sibling path.
public struct RevocationState has key {
    id: UID,
    show: ID,
    depth: u64,
    root: u256,
    revocations: u64,
}

public struct NullifierShard has key {
    id: UID,
    show: ID,
    index: u64,
    spent: Table<u256, bool>,
}

/// RS-C17: challenges are unique show-wide through their own hash-routed family, not
/// through the nullifier shard.
public struct ChallengeShard has key {
    id: UID,
    show: ID,
    index: u64,
    used: Table<u256, bool>,
}

/// RS-3a: one shared `GrantControl` per grant — the single chain-side record of grant
/// currentness (profile section 10.4). Pages hold only the grant id; every delegated
/// consumption/release path reads this object, and the revocation cut is one write
/// on it. `generation` starts at 1 and bumps once, at the cut — the generation the
/// grant's affected commitments are retired into (authority model 1, A-4).
public struct GrantControl has key {
    id: UID,
    show: ID,
    issuer: address,
    delegate: address,
    generation: u64,
    open: bool,
}

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
/// Slot reservation for primary issuance, owned by the show issuer until `issue_paid`
/// or `cancel_issuance`. `expected_generation` is the slot generation the reservation
/// was made against.
public struct IssuancePayment has key {
    id: UID, show: ID, slot: u64, expected_generation: u64, buyer: address,
    amount: u64, payment_ref: vector<u8>,
}
/// Hot potato: no abilities, so a PTB must end it with `finish_bundle`.
public struct Bundle { show: ID, remaining: u64 }

public struct ShowControlCreated has copy, drop {
    show: ID, issuer: address, profile_version: u64, page_count: u64, shard_count: u64,
}
public struct PageClaimed has copy, drop { show: ID, index: u64, page: ID, claim_sequence: u64 }
public struct ShardClaimed has copy, drop { show: ID, index: u64, shard: ID, claim_sequence: u64 }
public struct ZkClaimed has copy, drop {
    show: ID, domain: u256, note_tree: ID, revocation: ID, nullifier_shards: vector<ID>,
    challenge_shards: vector<ID>, depth: u64, history_k: u64, claim_sequence: u64,
}
/// The public tree data a witness is rebuilt from (RR-4): `index` is the insertion index.
public struct NoteAdded has copy, drop { show: ID, index: u64, commitment: u256, root: u256 }
public struct RevocationLeaf has copy, drop { show: ID, slot: u64, generation: u64, root: u256 }
public struct PrivateAdmission has copy, drop {
    show: ID, nullifier: u256, gate: address, challenge: u256, note_root: u256,
}
public struct ShowSealed has copy, drop { show: ID }
public struct ShowCancelled has copy, drop { show: ID, cancel_generation: u64 }
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
/// Observes a minted right. `kind` 0 is a direct grant; `kind` 1 is primary issuance
/// bound to an attester assertion. Not a fungible coin and not cash.
public struct Issuance has copy, drop {
    show: ID, ticket: ID, slot: u64, generation: u64, holder: address,
    kind: u8, amount: u64, payment_ref: vector<u8>,
}
/// RS-3a grant lifecycle events. `GrantCreated` records the grant's first
/// generation; `GrantRevoked` is the durable record of the cut — the generation the
/// grant's affected commitments are retired into.
public struct GrantCreated has copy, drop { show: ID, grant: ID, delegate: address, generation: u64 }
public struct PageDelegated has copy, drop { show: ID, page: ID, grant: ID }
public struct GrantRevoked has copy, drop { show: ID, grant: ID, generation: u64 }
public struct PageUndelegated has copy, drop { show: ID, page: ID, grant: ID }

fun init(ctx: &mut TxContext) {
    transfer::transfer(IssuerCap { id: object::new(ctx) }, ctx.sender());
}

// ---------------------------------------------------------------- creation staging

/// Creates the control with `open == false`. Pages and shards are claimed afterwards
/// (`claim_pages`, `claim_shards`) and the show opens only at `seal`.
public fun create_show_control(_cap: &IssuerCap, seated_capacity: u64, ga_capacity: u64,
    page_size: u64, shard_count: u64, gates: vector<address>, payment_attesters: vector<address>,
    resale_cap: u64, organizer_bps: u64, platform_bps: u64, verifier: ID, ctx: &mut TxContext) {
    assert!(page_size > 0 && shard_count > 0 && seated_capacity + ga_capacity > 0 && !gates.is_empty(), EPolicy);
    assert!(organizer_bps <= 10000 && platform_bps <= 10000 && organizer_bps + platform_bps <= 10000, EPolicy);
    let seated_pages = ceil_div(seated_capacity, page_size);
    let page_count = seated_pages + ceil_div(ga_capacity, page_size);
    let id = object::new(ctx);
    let show = id.to_inner();
    event::emit(ShowControlCreated { show, issuer: ctx.sender(), profile_version: PROFILE_VERSION,
        page_count, shard_count });
    transfer::share_object(ShowControl { id, issuer: ctx.sender(), profile_version: PROFILE_VERSION,
        open: false, sealed: false, cancel_generation: 0, verifier, gates, payment_attesters,
        resale_cap, organizer_bps, platform_bps, page_size, seated_capacity, ga_capacity,
        seated_pages, page_count, shard_count, claimed_pages: 0, claimed_shards: 0, claim_sequence: 0,
        domain: 0 });
}

/// Claims, builds and shares pages `[from, from + count)`. A second claim of any index
/// aborts inside `derived_object::claim`, so a lost-response retry cannot create a
/// second authority for a range. Claim, creation and sharing are one transaction.
public fun claim_pages(c: &mut ShowControl, cap: &IssuerCap, from: u64, count: u64, ctx: &mut TxContext) {
    authority(c, cap, ctx);
    assert!(!c.sealed && c.cancel_generation == 0, ESealed);
    assert!(count > 0 && from + count <= c.page_count, ERange);
    let mut index = from;
    while (index < from + count) {
        let (start, end, mode) = range_of(c, index);
        let uid = derived_object::claim(&mut c.id, PageKey { index });
        let mut generations = vector[];
        let mut occupied = vector[];
        let mut slot = start;
        while (slot < end) { generations.push_back(0); occupied.push_back(false); slot = slot + 1; };
        c.claimed_pages = c.claimed_pages + 1;
        c.claim_sequence = c.claim_sequence + 1;
        event::emit(PageClaimed { show: object::id(c), index, page: uid.to_inner(), claim_sequence: c.claim_sequence });
        transfer::share_object(InventoryPage { id: uid, show: object::id(c), index, start, end, mode,
            generations, occupied, issuances: 0, free: end - start, reserved: 0, issued: 0, retired: 0,
            delegated_to: option::none() });
        index = index + 1;
    };
}

public fun claim_shards(c: &mut ShowControl, cap: &IssuerCap, from: u64, count: u64, ctx: &mut TxContext) {
    authority(c, cap, ctx);
    assert!(!c.sealed && c.cancel_generation == 0, ESealed);
    assert!(count > 0 && from + count <= c.shard_count, ERange);
    let mut index = from;
    while (index < from + count) {
        let uid = derived_object::claim(&mut c.id, ShardKey { index });
        c.claimed_shards = c.claimed_shards + 1;
        c.claim_sequence = c.claim_sequence + 1;
        event::emit(ShardClaimed { show: object::id(c), index, shard: uid.to_inner(), claim_sequence: c.claim_sequence });
        transfer::share_object(PaymentRefShard { id: uid, show: object::id(c), index,
            refs: table::new(ctx) });
        index = index + 1;
    };
}

/// Enables the private path (RS-2). Claims, builds and shares the one `NoteTree`, the one
/// `RevocationState`, and the nullifier and challenge shard families, and fixes the show's
/// domain from its ID, `profile_version` and the pinned verifier's manifest hash (RS-C11).
/// Creation stage only, like the other claims; a second call aborts. A show that never
/// calls it keeps the RS-1 public path unchanged and has no private operation.
public fun claim_zk(c: &mut ShowControl, cap: &IssuerCap, v: &Verifier, ctx: &mut TxContext) {
    authority(c, cap, ctx);
    assert!(!c.sealed && c.cancel_generation == 0, ESealed);
    assert!(c.domain == 0, EZk);
    assert!(c.verifier == object::id(v), EVerifier);
    // The circuit range-checks the slot to ZK_DEPTH bits and both trees have 2^ZK_DEPTH leaves.
    assert!(c.seated_capacity + c.ga_capacity <= (1u64 << (ZK_DEPTH as u8)), ERange);
    let show = object::id(c);
    c.domain = domain_of(show, c.profile_version, zk_gate::manifest_hash(v));
    assert!(c.domain != 0, EZk);

    let tree_uid = derived_object::claim(&mut c.id, TreeKey { index: 0 });
    c.claim_sequence = c.claim_sequence + 1;
    let (zeros, frontier) = empty_tree(ZK_DEPTH, LOCALNET_ROOT_HISTORY_K);
    let empty_root = zeros[ZK_DEPTH];
    let tree = NoteTree { id: tree_uid, show, depth: ZK_DEPTH, history_k: LOCALNET_ROOT_HISTORY_K, leaf_count: 0,
        frontier, zeros, root: empty_root, roots: vector[empty_root], head: 0 };
    let note_tree = object::id(&tree);

    let rev_uid = derived_object::claim(&mut c.id, TreeKey { index: 1 });
    c.claim_sequence = c.claim_sequence + 1;
    let revocation = RevocationState { id: rev_uid, show, depth: ZK_DEPTH, root: empty_root, revocations: 0 };
    let revocation_id = object::id(&revocation);

    let mut nullifier_shards = vector[];
    let mut index = 0;
    while (index < LOCALNET_NULLIFIER_SHARDS) {
        let uid = derived_object::claim(&mut c.id, NullifierKey { index });
        c.claim_sequence = c.claim_sequence + 1;
        nullifier_shards.push_back(uid.to_inner());
        transfer::share_object(NullifierShard { id: uid, show, index, spent: table::new(ctx) });
        index = index + 1;
    };
    let mut challenge_shards = vector[];
    index = 0;
    while (index < LOCALNET_CHALLENGE_SHARDS) {
        let uid = derived_object::claim(&mut c.id, ChallengeKey { index });
        c.claim_sequence = c.claim_sequence + 1;
        challenge_shards.push_back(uid.to_inner());
        transfer::share_object(ChallengeShard { id: uid, show, index, used: table::new(ctx) });
        index = index + 1;
    };
    event::emit(ZkClaimed { show, domain: c.domain, note_tree, revocation: revocation_id, nullifier_shards,
        challenge_shards, depth: ZK_DEPTH, history_k: LOCALNET_ROOT_HISTORY_K, claim_sequence: c.claim_sequence });
    transfer::share_object(tree);
    transfer::share_object(revocation);
}

/// Opens the show once every page and shard of the range table is claimed. After this
/// no function changes the verifier or the range table, and no page can be added.
public fun seal(c: &mut ShowControl, cap: &IssuerCap, ctx: &TxContext) {
    authority(c, cap, ctx);
    assert!(!c.sealed && c.cancel_generation == 0, ESealed);
    assert!(c.claimed_pages == c.page_count && c.claimed_shards == c.shard_count, ENotComplete);
    c.sealed = true;
    c.open = true;
    event::emit(ShowSealed { show: object::id(c) });
}

/// Closes the show. A show that is not open (unsealed or already cancelled) is rejected.
public fun cancel_show(c: &mut ShowControl, cap: &IssuerCap, ctx: &TxContext) {
    authority(c, cap, ctx);
    assert!(c.open, EClosed);
    c.open = false;
    c.cancel_generation = 1;
    event::emit(ShowCancelled { show: object::id(c), cancel_generation: 1 });
}

// ---------------------------------------------------------------- helpers

fun ceil_div(n: u64, d: u64): u64 { if (n == 0) 0 else (n - 1) / d + 1 }
fun min(a: u64, b: u64): u64 { if (a < b) a else b }
fun h2(a: u256, b: u256): u256 { poseidon::poseidon_bn254(&vector[a, b]) }

/// RS-C11: the domain binds the show, the profile version and the circuit manifest hash.
/// Both 32-byte inputs are read big-endian and reduced modulo FR, as the reference
/// profile does for the show ID.
public fun domain_of(show: ID, profile_version: u64, manifest_hash: vector<u8>): u256 {
    assert!(manifest_hash.length() == 32, EZk);
    let show_field = sui::address::to_u256(object::id_to_address(&show)) % FR;
    let manifest_field = sui::address::to_u256(sui::address::from_bytes(manifest_hash)) % FR;
    poseidon::poseidon_bn254(&vector[show_field, (profile_version as u256), manifest_field])
}

// ---------------------------------------------------------------- root rules

/// Empty-subtree roots `zeros[0..=depth]` (zeros[0] = 0) and the initial frontier.
fun empty_tree(depth: u64, history_k: u64): (vector<u256>, vector<u256>) {
    assert!(depth > 0 && depth < 32 && history_k > 0, EZk);
    let mut zeros = vector[0u256];
    let mut frontier = vector[];
    let mut level = 0;
    while (level < depth) {
        let below = zeros[level];
        zeros.push_back(h2(below, below));
        frontier.push_back(0u256);
        level = level + 1;
    };
    (zeros, frontier)
}

/// RR-1: appends one leaf, updates the frontier and the root, and records the new root in
/// the K-entry history. Leaves are never changed or removed, so an inclusion proof against
/// any recorded root stays true for every later root.
fun tree_insert(tree: &mut NoteTree, leaf: u256) {
    assert!(tree.leaf_count < (1u64 << (tree.depth as u8)), ETreeFull);
    let mut index = tree.leaf_count;
    let mut node = leaf;
    let mut level = 0;
    while (level < tree.depth) {
        if (index % 2 == 0) {
            *tree.frontier.borrow_mut(level) = node;
            node = h2(node, tree.zeros[level]);
        } else {
            node = h2(tree.frontier[level], node);
        };
        index = index / 2;
        level = level + 1;
    };
    tree.leaf_count = tree.leaf_count + 1;
    tree.root = node;
    if (tree.roots.length() < tree.history_k) {
        tree.roots.push_back(node);
    } else {
        *tree.roots.borrow_mut(tree.head) = node;
        tree.head = (tree.head + 1) % tree.history_k;
    };
}

/// RR-2: root of a sparse tree whose only non-default leaf on the path is `leaf` at index
/// `slot`; `siblings[l]` is the sibling at level l. Default leaves are 0.
fun sparse_root(depth: u64, leaf: u256, slot: u64, siblings: &vector<u256>): u256 {
    assert!(siblings.length() == depth && slot < (1u64 << (depth as u8)), ERoot);
    let mut node = leaf;
    let mut index = slot;
    let mut level = 0;
    while (level < depth) {
        let sibling = siblings[level];
        assert!(sibling < FR, ERoot);
        node = if (index % 2 == 0) h2(node, sibling) else h2(sibling, node);
        index = index / 2;
        level = level + 1;
    };
    node
}

fun check_tree(c: &ShowControl, tree: &NoteTree) {
    assert!(c.domain != 0 && tree.show == object::id(c)
        && object::id(tree).to_address() == derived_object::derive_address(object::id(c), TreeKey { index: 0 }), EZk);
}
fun check_revocation(c: &ShowControl, rev: &RevocationState) {
    assert!(c.domain != 0 && rev.show == object::id(c)
        && object::id(rev).to_address() == derived_object::derive_address(object::id(c), TreeKey { index: 1 }), EZk);
}
fun check_nullifier_shard(c: &ShowControl, s: &NullifierShard, nullifier: u256) {
    let index = route(object::id(c), &bcs::to_bytes(&nullifier), c.profile_version, LOCALNET_NULLIFIER_SHARDS);
    assert!(object::id(s).to_address() == derived_object::derive_address(object::id(c), NullifierKey { index }), EShard);
    assert!(s.show == object::id(c) && s.index == index, EShard);
}
fun check_challenge_shard(c: &ShowControl, s: &ChallengeShard, challenge: u256) {
    let index = route(object::id(c), &bcs::to_bytes(&challenge), c.profile_version, LOCALNET_CHALLENGE_SHARDS);
    assert!(object::id(s).to_address() == derived_object::derive_address(object::id(c), ChallengeKey { index }), EShard);
    assert!(s.show == object::id(c) && s.index == index, EShard);
}

fun authority(c: &ShowControl, _cap: &IssuerCap, ctx: &TxContext) {
    assert!(ctx.sender() == c.issuer, EAuthority);
}

/// RS-3a: the grant-currentness check every delegated path runs. The grant belongs
/// to this show, has not been cut, and is the grant `p` is delegated to. Read-only
/// on `g` (profile section 10.3).
fun check_grant(c: &ShowControl, p: &InventoryPage, g: &GrantControl) {
    assert!(g.show == object::id(c), EShard);
    assert!(g.open, EGrantClosed);
    assert!(p.delegated_to == option::some(object::id(g)), EDelegated);
}

/// RS-3a: `p` is a claimed page of this show — its id is the derived claim for its
/// own index and it points back at `c`. The delegation calls have no slot to pin
/// the page with, so they check the binding directly.
fun check_page(c: &ShowControl, p: &InventoryPage) {
    assert!(object::id(p).to_address() == derived_object::derive_address(object::id(c), PageKey { index: p.index })
        && p.show == object::id(c), EPage);
}

fun range_of(c: &ShowControl, index: u64): (u64, u64, u8) {
    if (index < c.seated_pages) {
        let start = index * c.page_size;
        (start, min(start + c.page_size, c.seated_capacity), SEATED)
    } else {
        let start = c.seated_capacity + (index - c.seated_pages) * c.page_size;
        (start, min(start + c.page_size, c.seated_capacity + c.ga_capacity), GA)
    }
}

fun page_index_of(c: &ShowControl, slot: u64): u64 {
    assert!(slot < c.seated_capacity + c.ga_capacity, EInventory);
    if (slot < c.seated_capacity) { slot / c.page_size }
    else { c.seated_pages + (slot - c.seated_capacity) / c.page_size }
}

/// Checks that `p` is the page the range table assigns `slot` to, under this control,
/// and returns the slot's offset inside it. Does not check `open`.
fun offset(c: &ShowControl, p: &InventoryPage, slot: u64): u64 {
    let index = page_index_of(c, slot);
    assert!(object::id(p).to_address() == derived_object::derive_address(object::id(c), PageKey { index }), EPage);
    assert!(p.show == object::id(c) && p.index == index && slot >= p.start && slot < p.end, EPage);
    slot - p.start
}

/// Routing hash of a payment reference: blake2b256(show id || reference bytes ||
/// profile_version as little-endian u64), first 8 bytes little-endian, modulo the shard
/// count. Same bytes always reach the same shard, so a shard-local existence check is the
/// show-wide existence check. Localnet default; Astra-owned.
fun route(show: ID, payment_ref: &vector<u8>, profile_version: u64, shard_count: u64): u64 {
    let mut buf = object::id_to_bytes(&show);
    buf.append(*payment_ref);
    buf.append(bcs::to_bytes(&profile_version));
    let mut digest = bcs::new(hash::blake2b256(&buf));
    digest.peel_u64() % shard_count
}
fun routed(c: &ShowControl, payment_ref: &vector<u8>): u64 {
    route(object::id(c), payment_ref, c.profile_version, c.shard_count)
}

fun check_shard(c: &ShowControl, s: &PaymentRefShard, payment_ref: &vector<u8>) {
    let index = routed(c, payment_ref);
    assert!(object::id(s).to_address() == derived_object::derive_address(object::id(c), ShardKey { index }), EShard);
    assert!(s.show == object::id(c) && s.index == index, EShard);
}

fun live(c: &ShowControl, p: &InventoryPage, t: &Ticket, version: u64) {
    assert!(c.open && t.state == ACTIVE, EClosed);
    assert!(t.show == object::id(c), EStale);
    let off = offset(c, p, t.slot);
    assert!(t.generation == p.generations[off] && t.version == version, EStale);
}

fun changed(t: &Ticket, kind: u8) {
    event::emit(Change { show: t.show, ticket: object::id(t), version: t.version,
        state: t.state, holder: t.holder, kind });
}
fun idle(t: &Ticket, c: &Clock) {
    assert!(t.offer.is_none() || c.timestamp_ms() >= t.offer.borrow().expires_ms, ELocked);
    assert!(t.admission.is_none() || c.timestamp_ms() >= t.admission.borrow().expires_ms, ELocked);
}

fun mint(c: &ShowControl, p: &mut InventoryPage, off: u64, slot: u64, holder: address,
    payment_ref: vector<u8>, amount: u64, payer: address, kind: u8, ctx: &mut TxContext) {
    let next_generation = p.generations[off] + 1;
    *p.generations.borrow_mut(off) = next_generation;
    p.issuances = p.issuances + 1;
    let t = Ticket { id: object::new(ctx), show: object::id(c), slot, generation: next_generation, holder,
        version: 1, state: ACTIVE, offer: option::none(), admission: option::none(),
        last_payment: payment_ref, last_amount: amount, last_payer: payer };
    event::emit(Issuance { show: t.show, ticket: object::id(&t), slot: t.slot, generation: t.generation,
        holder: t.holder, kind, amount: t.last_amount, payment_ref: t.last_payment });
    changed(&t, 0);
    transfer::share_object(t);
}

// ---------------------------------------------------------------- issuance

/// The command binds (slot, expected generation). Re-sending it, even with new
/// transaction bytes and even after a refund, aborts with `EStale` instead of
/// creating a second right.
public fun issue(c: &ShowControl, p: &mut InventoryPage, cap: &IssuerCap, slot: u64,
    expected_generation: u64, holder: address, ctx: &mut TxContext) {
    authority(c, cap, ctx);
    // RS-3a: a delegated page refuses the direct path; the grant-checked variant serves it.
    assert!(p.delegated_to.is_none(), EDelegated);
    issue_body(c, p, slot, expected_generation, holder, ctx);
}

/// The tail of `issue` after the caller's authority gate (`IssuerCap` on the direct
/// path, the grant on the delegated path).
fun issue_body(c: &ShowControl, p: &mut InventoryPage, slot: u64, expected_generation: u64,
    holder: address, ctx: &mut TxContext) {
    assert!(c.open, EClosed);
    let off = offset(c, p, slot);
    assert!(p.generations[off] == expected_generation, EStale);
    assert!(!p.occupied[off], EInventory);
    *p.occupied.borrow_mut(off) = true;
    p.free = p.free - 1;
    p.issued = p.issued + 1;
    mint(c, p, off, slot, holder, vector[], 0, holder, DIRECT, ctx);
}

/// Reserves a free slot for primary issuance. Does not mint a Ticket and has no owned
/// input. The attester is trusted only for the asserted fiat fact.
public fun attest_issuance(c: &ShowControl, p: &mut InventoryPage, s: &mut PaymentRefShard, slot: u64,
    expected_generation: u64, buyer: address, amount: u64, payment_ref: vector<u8>, ctx: &mut TxContext) {
    assert!(c.payment_attesters.contains(&ctx.sender()), EAuthority);
    // RS-3a: a delegated page refuses the direct path; the grant-checked variant serves it.
    assert!(p.delegated_to.is_none(), EDelegated);
    attest_issuance_body(c, p, s, slot, expected_generation, buyer, amount, payment_ref, c.issuer, ctx);
}

/// The tail of `attest_issuance` after the caller's authority gate. `payment_holder`
/// receives the `IssuancePayment`: the issuer on the direct path, the delegate on
/// the delegated path (only the delegate can present it to `issue_paid_delegated`).
fun attest_issuance_body(c: &ShowControl, p: &mut InventoryPage, s: &mut PaymentRefShard, slot: u64,
    expected_generation: u64, buyer: address, amount: u64, payment_ref: vector<u8>, payment_holder: address,
    ctx: &mut TxContext) {
    assert!(c.open, EClosed);
    let off = offset(c, p, slot);
    assert!(p.generations[off] == expected_generation, EStale);
    assert!(!p.occupied[off], EInventory);
    assert!(amount > 0 && payment_ref.length() == 32, EPayment);
    check_shard(c, s, &payment_ref);
    assert!(!s.refs.contains(payment_ref), EPayment);
    *p.occupied.borrow_mut(off) = true;
    p.free = p.free - 1;
    p.reserved = p.reserved + 1;
    s.refs.add(payment_ref, REF_PRIMARY);
    transfer::transfer(IssuancePayment { id: object::new(ctx), show: object::id(c), slot, expected_generation,
        buyer, amount, payment_ref }, payment_holder);
}

/// Allowed on a cancelled show: a reservation can always be dropped.
public fun cancel_issuance(c: &ShowControl, p: &mut InventoryPage, s: &mut PaymentRefShard,
    cap: &IssuerCap, payment: IssuancePayment, ctx: &TxContext) {
    authority(c, cap, ctx);
    // RS-3a: a delegated page refuses the direct path; the grant-checked variant serves it.
    assert!(p.delegated_to.is_none(), EDelegated);
    cancel_issuance_body(c, p, s, payment);
}
fun cancel_issuance_body(c: &ShowControl, p: &mut InventoryPage, s: &mut PaymentRefShard,
    payment: IssuancePayment) {
    let IssuancePayment { id, show, slot, expected_generation: _, buyer: _, amount: _, payment_ref } = payment;
    assert!(show == object::id(c), EPayment);
    let off = offset(c, p, slot);
    assert!(p.occupied[off] && p.reserved > 0, EInventory);
    check_shard(c, s, &payment_ref);
    assert!(s.refs.contains(payment_ref), EPayment);
    s.refs.remove(payment_ref);
    object::delete(id);
    *p.occupied.borrow_mut(off) = false;
    p.reserved = p.reserved - 1;
    p.free = p.free + 1;
}

/// Mints the same public Ticket used by gifts, resale, admission and refund.
public fun issue_paid(c: &ShowControl, p: &mut InventoryPage, s: &PaymentRefShard, cap: &IssuerCap,
    payment: IssuancePayment, ctx: &mut TxContext) {
    authority(c, cap, ctx);
    // RS-3a: a delegated page refuses the direct path; the grant-checked variant serves it.
    assert!(p.delegated_to.is_none(), EDelegated);
    issue_paid_body(c, p, s, payment, ctx);
}
fun issue_paid_body(c: &ShowControl, p: &mut InventoryPage, s: &PaymentRefShard,
    payment: IssuancePayment, ctx: &mut TxContext) {
    let IssuancePayment { id, show, slot, expected_generation, buyer, amount, payment_ref } = payment;
    assert!(show == object::id(c), EPayment);
    assert!(c.open, EClosed);
    let off = offset(c, p, slot);
    assert!(p.occupied[off] && p.reserved > 0, EInventory);
    assert!(p.generations[off] == expected_generation, EStale);
    check_shard(c, s, &payment_ref);
    assert!(amount > 0 && payment_ref.length() == 32 && s.refs.contains(payment_ref), EPayment);
    object::delete(id);
    p.reserved = p.reserved - 1;
    p.issued = p.issued + 1;
    mint(c, p, off, slot, buyer, payment_ref, amount, buyer, PAID, ctx);
}

// ---------------------------------------------------------------- bundles

/// Begins a run of `n` issuances in one PTB. `n` above `MAX_BUNDLE_CHAIN` is rejected
/// with `EBundleTooLarge`. The bundle is a hot potato and must end in `finish_bundle`
/// after exactly `n` `bundle_issue` calls. A PTB is atomic, so a bundle that crosses
/// pages either issues every slot or none. Prepare/finalize across PTBs is not offered.
public fun begin_bundle(c: &ShowControl, n: u64): Bundle {
    assert!(n > 0, EPolicy);
    assert!(n <= MAX_BUNDLE_CHAIN, EBundleTooLarge);
    assert!(c.open, EClosed);
    Bundle { show: object::id(c), remaining: n }
}
public fun bundle_issue(b: &mut Bundle, c: &ShowControl, p: &mut InventoryPage, cap: &IssuerCap,
    slot: u64, expected_generation: u64, holder: address, ctx: &mut TxContext) {
    assert!(b.show == object::id(c) && b.remaining > 0, EBundleMismatch);
    b.remaining = b.remaining - 1;
    issue(c, p, cap, slot, expected_generation, holder, ctx);
}
/// RS-3a: `bundle_issue` on a delegated page, signed by the grant's delegate. A
/// bundle that crosses the delegation boundary aborts atomically like a page
/// crossing does (profile section 5).
public fun bundle_issue_delegated(b: &mut Bundle, c: &ShowControl, p: &mut InventoryPage, g: &GrantControl,
    slot: u64, expected_generation: u64, holder: address, ctx: &mut TxContext) {
    assert!(b.show == object::id(c) && b.remaining > 0, EBundleMismatch);
    b.remaining = b.remaining - 1;
    issue_delegated(c, p, g, slot, expected_generation, holder, ctx);
}
public fun finish_bundle(b: Bundle) {
    let Bundle { show: _, remaining } = b;
    assert!(remaining == 0, EBundleIncomplete);
}

// ---------------------------------------------------------------- holder operations

public fun offer(c: &ShowControl, p: &InventoryPage, t: &mut Ticket, version: u64, recipient: address,
    amount: u64, expires_ms: u64, clk: &Clock, ctx: &TxContext) {
    live(c, p, t, version); assert!(t.holder == ctx.sender(), ENotHolder); idle(t, clk);
    assert!(recipient != t.holder && amount <= c.resale_cap && expires_ms > clk.timestamp_ms()
        && expires_ms - clk.timestamp_ms() <= 900000, EPolicy);
    let terms = hash::blake2b256(&bcs::to_bytes(&Terms { show: object::id(c), ticket: object::id(t), version,
        seller: t.holder, buyer: recipient, amount, expires_ms, organizer_bps: c.organizer_bps,
        platform_bps: c.platform_bps }));
    t.offer = option::some(Offer { recipient, amount, expires_ms, version, terms });
    t.admission = option::none();
}
fun accepted(c: &ShowControl, p: &InventoryPage, t: &Ticket, clk: &Clock, ctx: &TxContext): Offer {
    live(c, p, t, t.version); assert!(t.offer.is_some(), ELocked);
    let o = *t.offer.borrow();
    assert!(o.recipient == ctx.sender() && o.version == t.version && clk.timestamp_ms() < o.expires_ms, EStale);
    o
}
fun transfer_right(t: &mut Ticket, recipient: address) {
    t.holder = recipient; t.version = t.version + 1;
    t.offer = option::none(); t.admission = option::none(); changed(t, 1);
}
public fun accept_gift(c: &ShowControl, p: &InventoryPage, t: &mut Ticket, clk: &Clock, ctx: &TxContext) {
    let o = accepted(c, p, t, clk, ctx); assert!(o.amount == 0, EPayment);
    transfer_right(t, o.recipient);
}

/// An external attester is trusted ONLY for the asserted fiat fact. The chain prevents
/// reusing the evidence object and checks all offer bindings.
public fun attest_payment(c: &ShowControl, p: &InventoryPage, s: &mut PaymentRefShard, t: &Ticket,
    payment_ref: vector<u8>, clk: &Clock, ctx: &mut TxContext) {
    assert!(c.payment_attesters.contains(&ctx.sender()), EAuthority);
    live(c, p, t, t.version); assert!(t.offer.is_some(), EPayment);
    let o = *t.offer.borrow();
    assert!(o.amount > 0 && clk.timestamp_ms() < o.expires_ms && payment_ref.length() == 32, EPayment);
    check_shard(c, s, &payment_ref);
    assert!(!s.refs.contains(payment_ref), EPayment);
    s.refs.add(payment_ref, REF_SECONDARY);
    transfer::transfer(PaymentEvidence { id: object::new(ctx), show: t.show, ticket: object::id(t),
        version: t.version, buyer: o.recipient, seller: t.holder, amount: o.amount, terms: o.terms,
        payment_ref }, o.recipient);
}
public fun accept_sale(c: &ShowControl, p: &InventoryPage, t: &mut Ticket, payment: PaymentEvidence,
    clk: &Clock, ctx: &TxContext) {
    let o = accepted(c, p, t, clk, ctx);
    let PaymentEvidence { id, show, ticket, version, buyer, seller, amount, terms, payment_ref } = payment;
    assert!(show == t.show && ticket == object::id(t) && version == t.version && buyer == o.recipient
        && seller == t.holder && amount == o.amount && amount > 0 && terms == o.terms, EPayment);
    object::delete(id);
    let organizer_due = ((amount as u128) * (c.organizer_bps as u128) / 10000) as u64;
    let platform_due = ((amount as u128) * (c.platform_bps as u128) / 10000) as u64;
    event::emit(Allocation { show, ticket, payment: payment_ref, seller, total: amount,
        seller_due: amount - organizer_due - platform_due, organizer_due, platform_due });
    t.last_payment = payment_ref; t.last_amount = amount; t.last_payer = buyer; transfer_right(t, buyer);
}

public fun authorize_admission(c: &ShowControl, p: &InventoryPage, t: &mut Ticket, version: u64,
    gate: address, request: vector<u8>, expires_ms: u64, clk: &Clock, ctx: &TxContext) {
    live(c, p, t, version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t, clk);
    assert!(c.gates.contains(&gate) && request.length() == 32 && expires_ms > clk.timestamp_ms()
        && expires_ms - clk.timestamp_ms() <= 120000, EPolicy);
    t.offer = option::none(); t.admission = option::some(Admission { gate, expires_ms, version, request });
}
public fun consume(c: &ShowControl, p: &InventoryPage, t: &mut Ticket, version: u64, request: vector<u8>,
    clk: &Clock, ctx: &TxContext) {
    live(c, p, t, version); assert!(c.gates.contains(&ctx.sender()) && t.admission.is_some(), EAuthority);
    let a = *t.admission.borrow();
    assert!(a.gate == ctx.sender() && a.version == version && a.request == request
        && clk.timestamp_ms() < a.expires_ms, EStale);
    t.state = CONSUMED; t.version = t.version + 1; t.admission = option::none(); t.offer = option::none();
    changed(t, 2);
}

/// Returns the slot to the page. Not possible once the show is cancelled: the refund
/// obligation is off-chain (reference profile behaviour, IM-08).
public fun refund(c: &ShowControl, p: &mut InventoryPage, t: &mut Ticket, version: u64, clk: &Clock,
    ctx: &TxContext) {
    live(c, p, t, version); assert!(ctx.sender() == t.holder, ENotHolder);
    // RS-3a: a delegated page refuses the direct path; the grant-checked variant serves it.
    assert!(p.delegated_to.is_none(), EDelegated);
    idle(t, clk);
    refund_apply(c, p, t);
}
fun refund_apply(c: &ShowControl, p: &mut InventoryPage, t: &mut Ticket) {
    let off = offset(c, p, t.slot);
    t.state = VOID; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    *p.occupied.borrow_mut(off) = false;
    p.issued = p.issued - 1;
    p.free = p.free + 1;
    event::emit(RefundDutyRequested { show: t.show, ticket: object::id(t), beneficiary: t.last_payer,
        amount: t.last_amount, payment_ref: t.last_payment });
    changed(t, 3);
}

/// Bumps the slot generation and retires the slot. Does NOT reopen inventory: private
/// or physical use could be unknown. For a show that enabled the private path the
/// revocation root must move with the generation, so only `revoke_with_root` serves it.
public fun revoke(c: &ShowControl, p: &mut InventoryPage, cap: &IssuerCap, t: &mut Ticket, ctx: &TxContext) {
    assert!(c.domain == 0, ERootRequired);
    revoke_ticket(c, p, cap, t, ctx);
}

/// RR-2: `revoke` for a show with a revocation root. The caller supplies the leaf value
/// the slot currently has (`prior_revoked`, 0 if never revoked) and the sibling path; the
/// chain checks them against the stored root and stores the root for the leaf
/// `t.generation`, the highest revoked generation of the slot. Two revocations built on
/// the same root conflict: the second fails with `ERoot` and is rebuilt (RR-2 storage (b)).
/// Issuance and refund never touch the root.
public fun revoke_with_root(c: &ShowControl, p: &mut InventoryPage, rev: &mut RevocationState, cap: &IssuerCap,
    t: &mut Ticket, prior_revoked: u64, siblings: vector<u256>, ctx: &TxContext) {
    check_revocation(c, rev);
    assert!(t.generation > prior_revoked, ERoot);
    assert!(sparse_root(rev.depth, (prior_revoked as u256), t.slot, &siblings) == rev.root, ERoot);
    revoke_ticket(c, p, cap, t, ctx);
    rev.root = sparse_root(rev.depth, (t.generation as u256), t.slot, &siblings);
    rev.revocations = rev.revocations + 1;
    event::emit(RevocationLeaf { show: t.show, slot: t.slot, generation: t.generation, root: rev.root });
}

fun revoke_ticket(c: &ShowControl, p: &mut InventoryPage, cap: &IssuerCap, t: &mut Ticket, ctx: &TxContext) {
    authority(c, cap, ctx);
    assert!(t.show == object::id(c), EStale);
    let off = offset(c, p, t.slot);
    assert!(t.generation == p.generations[off] && p.occupied[off] && t.state != VOID, EStale);
    let next_generation = p.generations[off] + 1;
    *p.generations.borrow_mut(off) = next_generation;
    p.issued = p.issued - 1;
    p.retired = p.retired + 1;
    t.state = VOID; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    changed(t, 4);
}

// ---------------------------------------------------------------- delegation (RS-3a)

/// Creates and shares one grant for `delegate`. Grants are dynamic, not derived
/// claims: an ordinary shared object, one per grant (profile section 3). Requires
/// an open show. No expiry and no allowed-operation set are defined — adding
/// either is a profile decision, not a fixture.
public fun create_grant(c: &ShowControl, cap: &IssuerCap, delegate: address, ctx: &mut TxContext) {
    authority(c, cap, ctx);
    assert!(c.open, EClosed);
    assert!(delegate != @0x0, EPolicy);
    let g = GrantControl { id: object::new(ctx), show: object::id(c), issuer: c.issuer, delegate,
        generation: 1, open: true };
    event::emit(GrantCreated { show: g.show, grant: object::id(&g), delegate, generation: 1 });
    transfer::share_object(g);
}

/// The revocation cut (profile section 10.4–10.5): a single write on the grant.
/// `open` flips, `generation` bumps to the generation the grant's affected
/// commitments are retired into, and `GrantRevoked` is the durable record. Pre-cut
/// obligations — live tickets, refund duties — are not touched; every delegated
/// path aborts with `EGrantClosed` from this write on.
public fun revoke_grant(g: &mut GrantControl, _cap: &IssuerCap, ctx: &TxContext) {
    assert!(ctx.sender() == g.issuer, EAuthority);
    assert!(g.open, EGrantClosed);
    g.open = false;
    g.generation = g.generation + 1;
    event::emit(GrantRevoked { show: g.show, grant: object::id(g), generation: g.generation });
}

/// Page-level grant assignment: the delegation unit (profile section 10.2). A page
/// holding an unresolved reservation (`reserved > 0`) cannot be delegated — the
/// direct-path `IssuancePayment` would be stranded (RS-C07b) — and neither can a
/// page already delegated. `revoke` keeps working on a delegated page: it is not
/// in the delegated five-path list, and a revoked slot stays retired either way.
public fun delegate_page(c: &ShowControl, p: &mut InventoryPage, g: &GrantControl, cap: &IssuerCap,
    ctx: &TxContext) {
    authority(c, cap, ctx);
    assert!(c.open, EClosed);
    assert!(g.show == object::id(c), EShard);
    assert!(g.open, EGrantClosed);
    check_page(c, p);
    assert!(p.delegated_to.is_none() && p.reserved == 0, EDelegated);
    p.delegated_to = option::some(object::id(g));
    event::emit(PageDelegated { show: object::id(c), page: object::id(p), grant: object::id(g) });
}

/// Reclaims the page after the cut: clears `delegated_to` so the direct paths
/// serve it again (profile section 10.4, the per-page write after the cut). An
/// open grant cannot be undelegated — `revoke_grant` first — and a page holding a
/// stranded pre-cut reservation (`reserved > 0`, whose delegate-owned payment no
/// path can present) is not "validated unused" and cannot be reclaimed.
public fun undelegate_page(c: &ShowControl, p: &mut InventoryPage, g: &GrantControl, cap: &IssuerCap,
    ctx: &TxContext) {
    authority(c, cap, ctx);
    assert!(g.show == object::id(c), EShard);
    assert!(!g.open, EGrantClosed);
    check_page(c, p);
    assert!(p.delegated_to == option::some(object::id(g)) && p.reserved == 0, EDelegated);
    p.delegated_to = option::none();
    event::emit(PageUndelegated { show: object::id(c), page: object::id(p), grant: object::id(g) });
}

/// `issue` on a delegated page, signed by the grant's delegate.
public fun issue_delegated(c: &ShowControl, p: &mut InventoryPage, g: &GrantControl, slot: u64,
    expected_generation: u64, holder: address, ctx: &mut TxContext) {
    assert!(ctx.sender() == g.delegate, EAuthority);
    check_grant(c, p, g);
    issue_body(c, p, slot, expected_generation, holder, ctx);
}

/// `attest_issuance` on a delegated page, signed by the grant's delegate. The
/// `IssuancePayment` is minted to the delegate, not the issuer.
public fun attest_issuance_delegated(c: &ShowControl, p: &mut InventoryPage, s: &mut PaymentRefShard,
    g: &GrantControl, slot: u64, expected_generation: u64, buyer: address, amount: u64,
    payment_ref: vector<u8>, ctx: &mut TxContext) {
    assert!(ctx.sender() == g.delegate, EAuthority);
    check_grant(c, p, g);
    attest_issuance_body(c, p, s, slot, expected_generation, buyer, amount, payment_ref, g.delegate, ctx);
}

/// `issue_paid` on a delegated page. Only the delegate holds the payment object a
/// delegated `attest_issuance` minted, so only it can complete the reservation.
public fun issue_paid_delegated(c: &ShowControl, p: &mut InventoryPage, s: &PaymentRefShard, g: &GrantControl,
    payment: IssuancePayment, ctx: &mut TxContext) {
    assert!(ctx.sender() == g.delegate, EAuthority);
    check_grant(c, p, g);
    issue_paid_body(c, p, s, payment, ctx);
}

/// `cancel_issuance` on a delegated page, signed by the delegate holding the
/// payment object. Still allowed on a cancelled show, like the direct path.
public fun cancel_issuance_delegated(c: &ShowControl, p: &mut InventoryPage, s: &mut PaymentRefShard,
    g: &GrantControl, payment: IssuancePayment, ctx: &TxContext) {
    assert!(ctx.sender() == g.delegate, EAuthority);
    check_grant(c, p, g);
    cancel_issuance_body(c, p, s, payment);
}

/// `refund` on a delegated page. The caller stays the ticket holder — the grant
/// check replaces the `delegated_to.is_none()` gate, it does not re-bind the
/// sender (profile section 10.3 includes `refund` in the grant-checked set).
/// After the cut this aborts with `EGrantClosed`; the release obligation is then
/// off-chain like a cancelled show's (IM-08).
public fun refund_delegated(c: &ShowControl, p: &mut InventoryPage, g: &GrantControl, t: &mut Ticket,
    version: u64, clk: &Clock, ctx: &TxContext) {
    assert!(ctx.sender() == t.holder, ENotHolder);
    check_grant(c, p, g);
    live(c, p, t, version);
    idle(t, clk);
    refund_apply(c, p, t);
}

// ---------------------------------------------------------------- private path

/// Public to private: keeps the slot occupied, marks the ticket SHIELDED (so every public
/// operation, refund and reissue is refused, RS-C10) and appends the note commitment.
/// The mint proof binds (commitment, slot, generation, domain); the holder and the slot
/// stay public at this step.
public fun shield(c: &ShowControl, p: &InventoryPage, tree: &mut NoteTree, t: &mut Ticket, version: u64,
    commitment: u256, proof: vector<u8>, v: &Verifier, clk: &Clock, ctx: &TxContext) {
    let inputs = shield_inputs(c, p, tree, t, version, commitment, v, clk, ctx);
    zk_gate::mint(v, inputs, proof);
    shield_apply(tree, t, commitment);
}
fun shield_inputs(c: &ShowControl, p: &InventoryPage, tree: &NoteTree, t: &Ticket, version: u64,
    commitment: u256, v: &Verifier, clk: &Clock, ctx: &TxContext): vector<u256> {
    live(c, p, t, version); assert!(ctx.sender() == t.holder, ENotHolder); idle(t, clk);
    assert!(c.verifier == object::id(v) && commitment > 0 && commitment < FR, EProof);
    check_tree(c, tree);
    assert!(tree.leaf_count < (1u64 << (tree.depth as u8)), ETreeFull);
    vector[commitment, (t.slot as u256), (t.generation as u256), c.domain]
}
fun shield_apply(tree: &mut NoteTree, t: &mut Ticket, commitment: u256) {
    let index = tree.leaf_count;
    tree_insert(tree, commitment);
    t.state = SHIELDED; t.version = t.version + 1; t.offer = option::none(); t.admission = option::none();
    event::emit(NoteAdded { show: t.show, index, commitment, root: tree.root });
    changed(t, 5);
}

/// Private admission, sent by a gate. `note_root` is the note-tree root the proof was made
/// against: it must be one of the K most recent (RR-1). The revocation root is not a
/// parameter: the chain supplies its current value, so a proof made before a `revoke`
/// is rejected after it (RR-3, W = 0). The context binds the gate address, challenge and
/// expiry. Nullifier and challenge are each recorded in their own hash-routed shard.
public fun consume_private(c: &ShowControl, tree: &NoteTree, rev: &RevocationState, ns: &mut NullifierShard,
    cs: &mut ChallengeShard, v: &Verifier, note_root: u256, nullifier: u256, challenge: u256, expires_ms: u64,
    proof: vector<u8>, clk: &Clock, ctx: &TxContext) {
    let inputs = private_inputs(c, tree, rev, ns, cs, v, note_root, nullifier, challenge, expires_ms, clk, ctx);
    zk_gate::spend(v, inputs, proof);
    private_apply(c, ns, cs, note_root, nullifier, challenge, ctx);
}
fun private_inputs(c: &ShowControl, tree: &NoteTree, rev: &RevocationState, ns: &NullifierShard,
    cs: &ChallengeShard, v: &Verifier, note_root: u256, nullifier: u256, challenge: u256, expires_ms: u64,
    clk: &Clock, ctx: &TxContext): vector<u256> {
    assert!(c.open && c.gates.contains(&ctx.sender()) && c.verifier == object::id(v), EAuthority);
    check_tree(c, tree);
    check_revocation(c, rev);
    check_nullifier_shard(c, ns, nullifier);
    check_challenge_shard(c, cs, challenge);
    assert!(nullifier > 0 && nullifier < FR && challenge > 0 && challenge < FR
        && !ns.spent.contains(nullifier) && !cs.used.contains(challenge), EProof);
    assert!(expires_ms > clk.timestamp_ms() && expires_ms - clk.timestamp_ms() <= 120000, EPolicy);
    assert!(tree.roots.contains(&note_root), ERoot);
    let gate = sui::address::to_u256(ctx.sender());
    let context = poseidon::poseidon_bn254(&vector[gate % 340282366920938463463374607431768211456,
        gate / 340282366920938463463374607431768211456, challenge, (expires_ms as u256), 1]);
    vector[note_root, rev.root, nullifier, context, c.domain, 1]
}
fun private_apply(c: &ShowControl, ns: &mut NullifierShard, cs: &mut ChallengeShard, note_root: u256,
    nullifier: u256, challenge: u256, ctx: &TxContext) {
    ns.spent.add(nullifier, true);
    cs.used.add(challenge, true);
    // No public ticket ID is needed for private admission. A SHIELDED slot cannot be
    // resold, refunded or reissued by this deliberately limited profile (RS-C14).
    event::emit(PrivateAdmission { show: object::id(c), nullifier, gate: ctx.sender(), challenge, note_root });
}

// ---------------------------------------------------------------- read-only views

public fun profile_version(): u64 { PROFILE_VERSION }
public fun max_bundle_chain(): u64 { MAX_BUNDLE_CHAIN }
public fun localnet_show_slots(): u64 { LOCALNET_SHOW_SLOTS }
public fun localnet_page_slots(): u64 { LOCALNET_PAGE_SLOTS }
public fun localnet_payment_shards(): u64 { LOCALNET_PAYMENT_SHARDS }

public fun control_open(c: &ShowControl): bool { c.open }
public fun control_sealed(c: &ShowControl): bool { c.sealed }
public fun control_issuer(c: &ShowControl): address { c.issuer }
public fun control_cancel_generation(c: &ShowControl): u64 { c.cancel_generation }
public fun control_page_count(c: &ShowControl): u64 { c.page_count }
public fun control_shard_count(c: &ShowControl): u64 { c.shard_count }
public fun control_claimed_pages(c: &ShowControl): u64 { c.claimed_pages }
public fun control_claimed_shards(c: &ShowControl): u64 { c.claimed_shards }
public fun control_capacity(c: &ShowControl): u64 { c.seated_capacity + c.ga_capacity }
public fun page_address(c: &ShowControl, index: u64): address {
    derived_object::derive_address(object::id(c), PageKey { index })
}
public fun shard_address(c: &ShowControl, index: u64): address {
    derived_object::derive_address(object::id(c), ShardKey { index })
}
public fun page_index_for_slot(c: &ShowControl, slot: u64): u64 { page_index_of(c, slot) }
public fun shard_index_for_ref(c: &ShowControl, payment_ref: vector<u8>): u64 { routed(c, &payment_ref) }
public fun route_index(show: ID, payment_ref: vector<u8>, profile_version: u64, shard_count: u64): u64 {
    route(show, &payment_ref, profile_version, shard_count)
}
public fun control_claim_sequence(c: &ShowControl): u64 { c.claim_sequence }

public fun page_start(p: &InventoryPage): u64 { p.start }
public fun page_end(p: &InventoryPage): u64 { p.end }
public fun page_mode(p: &InventoryPage): u8 { p.mode }
public fun page_free(p: &InventoryPage): u64 { p.free }
public fun page_reserved(p: &InventoryPage): u64 { p.reserved }
public fun page_issued(p: &InventoryPage): u64 { p.issued }
public fun page_retired(p: &InventoryPage): u64 { p.retired }
public fun page_issuances(p: &InventoryPage): u64 { p.issuances }
public fun page_generation(p: &InventoryPage, slot: u64): u64 { p.generations[slot - p.start] }
public fun page_occupied(p: &InventoryPage, slot: u64): bool { p.occupied[slot - p.start] }
public fun page_delegated(p: &InventoryPage): bool { p.delegated_to.is_some() }
public fun page_grant(p: &InventoryPage): Option<ID> { p.delegated_to }
public fun page_conserved(p: &InventoryPage): bool {
    p.free + p.reserved + p.issued + p.retired == p.end - p.start
}
public fun shard_size(s: &PaymentRefShard): u64 { s.refs.length() }
public fun shard_has(s: &PaymentRefShard, payment_ref: vector<u8>): bool { s.refs.contains(payment_ref) }

public fun payment_slot(p: &IssuancePayment): u64 { p.slot }
public fun payment_ref(p: &IssuancePayment): vector<u8> { p.payment_ref }
public fun payment_expected_generation(p: &IssuancePayment): u64 { p.expected_generation }

public fun grant_show(g: &GrantControl): ID { g.show }
public fun grant_issuer(g: &GrantControl): address { g.issuer }
public fun grant_delegate(g: &GrantControl): address { g.delegate }
public fun grant_generation(g: &GrantControl): u64 { g.generation }
public fun grant_open(g: &GrantControl): bool { g.open }

public fun holder(t: &Ticket): address { t.holder }
public fun version(t: &Ticket): u64 { t.version }
public fun state(t: &Ticket): u8 { t.state }
public fun slot(t: &Ticket): u64 { t.slot }
public fun generation(t: &Ticket): u64 { t.generation }
public fun last_amount(t: &Ticket): u64 { t.last_amount }
public fun last_payer(t: &Ticket): address { t.last_payer }
public fun last_payment(t: &Ticket): vector<u8> { t.last_payment }

public fun zk_depth(): u64 { ZK_DEPTH }
public fun localnet_root_history_k(): u64 { LOCALNET_ROOT_HISTORY_K }
public fun localnet_nullifier_shards(): u64 { LOCALNET_NULLIFIER_SHARDS }
public fun localnet_challenge_shards(): u64 { LOCALNET_CHALLENGE_SHARDS }
public fun shielded_state(): u8 { SHIELDED }

public fun control_domain(c: &ShowControl): u256 { c.domain }
public fun control_zk_enabled(c: &ShowControl): bool { c.domain != 0 }
public fun tree_address(c: &ShowControl): address { derived_object::derive_address(object::id(c), TreeKey { index: 0 }) }
public fun revocation_address(c: &ShowControl): address { derived_object::derive_address(object::id(c), TreeKey { index: 1 }) }
public fun nullifier_shard_address(c: &ShowControl, index: u64): address {
    derived_object::derive_address(object::id(c), NullifierKey { index })
}
public fun challenge_shard_address(c: &ShowControl, index: u64): address {
    derived_object::derive_address(object::id(c), ChallengeKey { index })
}
public fun nullifier_shard_index(c: &ShowControl, nullifier: u256): u64 {
    route(object::id(c), &bcs::to_bytes(&nullifier), c.profile_version, LOCALNET_NULLIFIER_SHARDS)
}
public fun challenge_shard_index(c: &ShowControl, challenge: u256): u64 {
    route(object::id(c), &bcs::to_bytes(&challenge), c.profile_version, LOCALNET_CHALLENGE_SHARDS)
}

public fun tree_depth(t: &NoteTree): u64 { t.depth }
public fun tree_history_k(t: &NoteTree): u64 { t.history_k }
public fun tree_leaf_count(t: &NoteTree): u64 { t.leaf_count }
public fun tree_root(t: &NoteTree): u256 { t.root }
public fun tree_roots(t: &NoteTree): vector<u256> { t.roots }
public fun tree_zero(t: &NoteTree, level: u64): u256 { t.zeros[level] }
public fun tree_frontier(t: &NoteTree, level: u64): u256 { t.frontier[level] }
public fun root_in_history(t: &NoteTree, root: u256): bool { t.roots.contains(&root) }
public fun revocation_root(r: &RevocationState): u256 { r.root }
public fun revocation_count(r: &RevocationState): u64 { r.revocations }
public fun nullifier_spent(s: &NullifierShard, nullifier: u256): bool { s.spent.contains(nullifier) }
public fun nullifier_shard_size(s: &NullifierShard): u64 { s.spent.length() }
public fun challenge_used(s: &ChallengeShard, challenge: u256): bool { s.used.contains(challenge) }
public fun challenge_shard_size(s: &ChallengeShard): u64 { s.used.length() }

#[test_only]
public fun init_for_testing(ctx: &mut TxContext) { init(ctx) }

/// Test-only: the same checks as `shield`, then the same state change, with the proof step
/// removed (a unit test cannot build a valid proof). Returns the public inputs.
#[test_only]
public fun shield_unproven_for_testing(c: &ShowControl, p: &InventoryPage, tree: &mut NoteTree, t: &mut Ticket,
    version: u64, commitment: u256, v: &Verifier, clk: &Clock, ctx: &TxContext): vector<u256> {
    let inputs = shield_inputs(c, p, tree, t, version, commitment, v, clk, ctx);
    shield_apply(tree, t, commitment);
    inputs
}

/// Test-only: the same checks as `consume_private` and the same recording, without the
/// proof step. Returns the six public inputs the verifier would receive.
#[test_only]
public fun consume_private_unproven_for_testing(c: &ShowControl, tree: &NoteTree, rev: &RevocationState,
    ns: &mut NullifierShard, cs: &mut ChallengeShard, v: &Verifier, note_root: u256, nullifier: u256,
    challenge: u256, expires_ms: u64, clk: &Clock, ctx: &TxContext): vector<u256> {
    let inputs = private_inputs(c, tree, rev, ns, cs, v, note_root, nullifier, challenge, expires_ms, clk, ctx);
    private_apply(c, ns, cs, note_root, nullifier, challenge, ctx);
    inputs
}

/// Test-only: a tree of any small depth, to reach the leaf capacity and wrap the ring.
#[test_only]
public fun new_tree_for_testing(show: ID, depth: u64, history_k: u64, ctx: &mut TxContext): NoteTree {
    let (zeros, frontier) = empty_tree(depth, history_k);
    let root = zeros[depth];
    NoteTree { id: object::new(ctx), show, depth, history_k, leaf_count: 0, frontier, zeros, root,
        roots: vector[root], head: 0 }
}
#[test_only]
public fun tree_insert_for_testing(tree: &mut NoteTree, leaf: u256) { tree_insert(tree, leaf) }
#[test_only]
public fun destroy_tree_for_testing(tree: NoteTree) {
    let NoteTree { id, show: _, depth: _, history_k: _, leaf_count: _, frontier: _, zeros: _, root: _, roots: _, head: _ } = tree;
    object::delete(id);
}
#[test_only]
public fun sparse_root_for_testing(depth: u64, leaf: u256, slot: u64, siblings: vector<u256>): u256 {
    sparse_root(depth, leaf, slot, &siblings)
}
