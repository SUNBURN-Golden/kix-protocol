#[test_only]
/// Fixtures for the private-path tests. A unit test cannot build a valid proof, so the
/// shield and consume helpers call the `*_unproven_for_testing` entry points, which run
/// every check and state change of the real functions except the Groth16 step.
module kix_rights_scale::zk_support;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, IssuerCap, Ticket, NoteTree,
    RevocationState, NullifierShard, ChallengeShard};
use kix_rights_scale::support as s;
use kix_rights_scale::zk_gate::{Self, Verifier};
use sui::clock::Clock;
use sui::test_scenario::{Self as ts, Scenario};

public fun manifest_hash(): vector<u8> {
    x"1111111111111111111111111111111111111111111111111111111111111111"
}
public fun other_manifest_hash(): vector<u8> {
    x"2222222222222222222222222222222222222222222222222222222222222222"
}

/// Freezes a Verifier with the given manifest hash and returns its ID.
public fun verifier(sc: &mut Scenario, hash: vector<u8>): ID {
    sc.next_tx(s::a());
    zk_gate::freeze_for_testing(hash, sc.ctx());
    sc.next_tx(s::a());
    ts::most_recent_immutable_id<Verifier>().destroy_some()
}

/// Control pinned to `verifier`, not yet staged.
public fun make_show(sc: &mut Scenario, seated: u64, ga: u64, page_size: u64, shards: u64, verifier: ID): ID {
    sc.next_tx(s::a());
    let cap = sc.take_from_sender<IssuerCap>();
    rs::create_show_control(&cap, seated, ga, page_size, shards, vector[s::gate(), s::c()], vector[s::att()],
        150000, 200, 300, verifier, sc.ctx());
    sc.return_to_sender(cap);
    sc.next_tx(s::a());
    ts::most_recent_id_shared<ShowControl>().destroy_some()
}

public fun claim_zk(sc: &mut Scenario, show: ID, verifier: ID) {
    sc.next_tx(s::a());
    let mut c = sc.take_shared_by_id<ShowControl>(show);
    let cap = sc.take_from_sender<IssuerCap>();
    let v = sc.take_immutable_by_id<Verifier>(verifier);
    rs::claim_zk(&mut c, &cap, &v, sc.ctx());
    ts::return_immutable(v);
    ts::return_shared(c);
    sc.return_to_sender(cap);
}

/// Creates, claims the private objects, stages and seals one show.
public fun ready(sc: &mut Scenario, seated: u64, ga: u64, page_size: u64, shards: u64, verifier: ID): ID {
    let show = make_show(sc, seated, ga, page_size, shards, verifier);
    claim_zk(sc, show, verifier);
    s::stage(sc, show);
    s::seal(sc, show);
    show
}

public fun tree_id(c: &ShowControl): ID { object::id_from_address(rs::tree_address(c)) }
public fun revocation_id(c: &ShowControl): ID { object::id_from_address(rs::revocation_address(c)) }
public fun nullifier_shard_id(c: &ShowControl, index: u64): ID { object::id_from_address(rs::nullifier_shard_address(c, index)) }
public fun challenge_shard_id(c: &ShowControl, index: u64): ID { object::id_from_address(rs::challenge_shard_address(c, index)) }

/// Issues `slot` to `holder` and returns the ticket ID.
public fun issued(sc: &mut Scenario, show: ID, slot: u64, holder: address): ID {
    s::issue(sc, show, slot, 0, holder);
    s::latest_ticket(sc)
}

public fun shield_with(sc: &mut Scenario, sender: address, control: ID, tree: ID, ticket: ID, version: u64,
    commitment: u256, verifier: ID): vector<u256> {
    let page = s::page_of(sc, control, ticket);
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(control);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut tr = sc.take_shared_by_id<NoteTree>(tree);
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let v = sc.take_immutable_by_id<Verifier>(verifier);
    let clk = sc.take_shared<Clock>();
    let inputs = rs::shield_unproven_for_testing(&c, &p, &mut tr, &mut t, version, commitment, &v, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_immutable(v); ts::return_shared(t); ts::return_shared(tr);
    ts::return_shared(p); ts::return_shared(c);
    inputs
}
/// The ticket's holder shields with the show's own tree.
public fun shield(sc: &mut Scenario, sender: address, show: ID, ticket: ID, version: u64, commitment: u256,
    verifier: ID): vector<u256> {
    let tree = {
        sc.next_tx(s::a());
        let c = sc.take_shared_by_id<ShowControl>(show);
        let id = tree_id(&c);
        ts::return_shared(c);
        id
    };
    shield_with(sc, sender, show, tree, ticket, version, commitment, verifier)
}

/// The real `shield`, which must stop at the Groth16 step once every check has passed.
public fun shield_proved(sc: &mut Scenario, sender: address, show: ID, ticket: ID, version: u64,
    commitment: u256, verifier: ID) {
    let page = s::page_of(sc, show, ticket);
    sc.next_tx(sender);
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(page);
    let mut tr = sc.take_shared_by_id<NoteTree>(tree_id(&c));
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let v = sc.take_immutable_by_id<Verifier>(verifier);
    let clk = sc.take_shared<Clock>();
    rs::shield(&c, &p, &mut tr, &mut t, version, commitment, vector[], &v, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_immutable(v); ts::return_shared(t); ts::return_shared(tr);
    ts::return_shared(p); ts::return_shared(c);
}

public fun note_root(sc: &mut Scenario, show: ID): u256 {
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let tr = sc.take_shared_by_id<NoteTree>(tree_id(&c));
    let root = rs::tree_root(&tr);
    ts::return_shared(tr); ts::return_shared(c);
    root
}
public fun revocation_root(sc: &mut Scenario, show: ID): u256 {
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let r = sc.take_shared_by_id<RevocationState>(revocation_id(&c));
    let root = rs::revocation_root(&r);
    ts::return_shared(r); ts::return_shared(c);
    root
}

/// Objects chosen explicitly so the wrong-object predicates can be tested.
public struct Choice has copy, drop {
    control: ID, tree: ID, revocation: ID, nullifier_shard: ID, challenge_shard: ID, verifier: ID,
}
/// The show's own objects, with the shards its routing assigns to (nullifier, challenge).
public fun own(sc: &mut Scenario, show: ID, nullifier: u256, challenge: u256, verifier: ID): Choice {
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let choice = Choice { control: show, tree: tree_id(&c), revocation: revocation_id(&c),
        nullifier_shard: nullifier_shard_id(&c, rs::nullifier_shard_index(&c, nullifier)),
        challenge_shard: challenge_shard_id(&c, rs::challenge_shard_index(&c, challenge)), verifier };
    ts::return_shared(c);
    choice
}
public fun nullifier_shard_of(c: &Choice): ID { c.nullifier_shard }
public fun with_tree(mut c: Choice, tree: ID): Choice { c.tree = tree; c }
public fun with_revocation(mut c: Choice, revocation: ID): Choice { c.revocation = revocation; c }
public fun with_nullifier_shard(mut c: Choice, shard: ID): Choice { c.nullifier_shard = shard; c }
public fun with_challenge_shard(mut c: Choice, shard: ID): Choice { c.challenge_shard = shard; c }
public fun with_verifier(mut c: Choice, verifier: ID): Choice { c.verifier = verifier; c }

public fun consume_with(sc: &mut Scenario, sender: address, c: Choice, note_root: u256, nullifier: u256,
    challenge: u256, expires_offset_ms: u64): vector<u256> {
    sc.next_tx(sender);
    let control = sc.take_shared_by_id<ShowControl>(c.control);
    let tree = sc.take_shared_by_id<NoteTree>(c.tree);
    let rev = sc.take_shared_by_id<RevocationState>(c.revocation);
    let mut ns = sc.take_shared_by_id<NullifierShard>(c.nullifier_shard);
    let mut cs = sc.take_shared_by_id<ChallengeShard>(c.challenge_shard);
    let v = sc.take_immutable_by_id<Verifier>(c.verifier);
    let clk = sc.take_shared<Clock>();
    let inputs = rs::consume_private_unproven_for_testing(&control, &tree, &rev, &mut ns, &mut cs, &v,
        note_root, nullifier, challenge, clk.timestamp_ms() + expires_offset_ms, &clk, sc.ctx());
    ts::return_shared(clk); ts::return_immutable(v); ts::return_shared(cs); ts::return_shared(ns);
    ts::return_shared(rev); ts::return_shared(tree); ts::return_shared(control);
    inputs
}
/// A gate consumes with the show's own objects.
public fun consume(sc: &mut Scenario, show: ID, note_root: u256, nullifier: u256, challenge: u256,
    verifier: ID): vector<u256> {
    let choice = own(sc, show, nullifier, challenge, verifier);
    consume_with(sc, s::gate(), choice, note_root, nullifier, challenge, 90000)
}

/// The real `consume_private`, which must stop at the Groth16 step.
public fun consume_proved(sc: &mut Scenario, show: ID, note_root: u256, nullifier: u256, challenge: u256,
    verifier: ID) {
    let choice = own(sc, show, nullifier, challenge, verifier);
    sc.next_tx(s::gate());
    let control = sc.take_shared_by_id<ShowControl>(choice.control);
    let tree = sc.take_shared_by_id<NoteTree>(choice.tree);
    let rev = sc.take_shared_by_id<RevocationState>(choice.revocation);
    let mut ns = sc.take_shared_by_id<NullifierShard>(choice.nullifier_shard);
    let mut cs = sc.take_shared_by_id<ChallengeShard>(choice.challenge_shard);
    let v = sc.take_immutable_by_id<Verifier>(choice.verifier);
    let clk = sc.take_shared<Clock>();
    rs::consume_private(&control, &tree, &rev, &mut ns, &mut cs, &v, note_root, nullifier, challenge,
        clk.timestamp_ms() + 90000, vector[], &clk, sc.ctx());
    ts::return_shared(clk); ts::return_immutable(v); ts::return_shared(cs); ts::return_shared(ns);
    ts::return_shared(rev); ts::return_shared(tree); ts::return_shared(control);
}

/// `revoke_with_root` with an explicit witness.
public fun revoke_rooted(sc: &mut Scenario, show: ID, ticket: ID, prior: u64, siblings: vector<u256>) {
    let page = s::page_of(sc, show, ticket);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut p = sc.take_shared_by_id<InventoryPage>(page);
    let mut rev = sc.take_shared_by_id<RevocationState>(revocation_id(&c));
    let mut t = sc.take_shared_by_id<Ticket>(ticket);
    let cap = sc.take_from_sender<IssuerCap>();
    rs::revoke_with_root(&c, &mut p, &mut rev, &cap, &mut t, prior, siblings, sc.ctx());
    ts::return_shared(t); ts::return_shared(rev); ts::return_shared(p); ts::return_shared(c);
    sc.return_to_sender(cap);
}

public fun state_of(sc: &mut Scenario, ticket: ID): (u8, u64) {
    sc.next_tx(s::a());
    let t = sc.take_shared_by_id<Ticket>(ticket);
    let state = rs::state(&t);
    let version = rs::version(&t);
    ts::return_shared(t);
    (state, version)
}

public fun gate_context(gate: address, challenge: u256, expires_ms: u64): u256 {
    let g = sui::address::to_u256(gate);
    sui::poseidon::poseidon_bn254(&vector[g % 340282366920938463463374607431768211456,
        g / 340282366920938463463374607431768211456, challenge, (expires_ms as u256), 1])
}

public fun page_id_of(c: &ShowControl, slot: u64): ID { s::page_id(c, rs::page_index_for_slot(c, slot)) }
