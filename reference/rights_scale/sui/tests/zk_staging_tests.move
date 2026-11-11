#[test_only]
/// `claim_zk`: the private objects, the domain, their derived identities, and the rule that a
/// show without them keeps the RS-1 public path exactly as it was.
module kix_rights_scale::zk_staging_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, NoteTree, RevocationState, NullifierShard, ChallengeShard,
    ZkClaimed};
use kix_rights_scale::support as s;
use kix_rights_scale::zk_support as z;
use sui::bcs;
use sui::event;
use sui::test_scenario::{Self as ts};

const EMPTY_ROOT_10: u256 = 12413880268183407374852357075976609371175688755676981206018884971008854919922;

#[test]
fun claim_zk_fixes_the_domain_and_creates_one_tree_one_revocation_state_and_the_shard_families() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::make_show(&mut sc, 8, 0, 4, 2, verifier);
    z::claim_zk(&mut sc, show, verifier);
    assert!(event::events_by_type<ZkClaimed>().length() == 1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(rs::control_zk_enabled(&c) && !rs::control_sealed(&c));
    assert!(rs::control_domain(&c) == rs::domain_of(show, rs::profile_version(), z::manifest_hash()));
    // 1 tree + 1 revocation state + 4 + 4 shards, one claim sequence number each.
    assert!(rs::control_claim_sequence(&c) == 10);
    let tree = sc.take_shared_by_id<NoteTree>(z::tree_id(&c));
    assert!(rs::tree_depth(&tree) == 10 && rs::tree_history_k(&tree) == rs::localnet_root_history_k());
    assert!(rs::tree_leaf_count(&tree) == 0 && rs::tree_root(&tree) == EMPTY_ROOT_10);
    assert!(rs::tree_roots(&tree) == vector[EMPTY_ROOT_10]);
    let rev = sc.take_shared_by_id<RevocationState>(z::revocation_id(&c));
    assert!(rs::revocation_root(&rev) == EMPTY_ROOT_10 && rs::revocation_count(&rev) == 0);
    let mut i = 0;
    while (i < rs::localnet_nullifier_shards()) {
        let ns = sc.take_shared_by_id<NullifierShard>(z::nullifier_shard_id(&c, i));
        assert!(rs::nullifier_shard_size(&ns) == 0);
        ts::return_shared(ns);
        i = i + 1;
    };
    i = 0;
    while (i < rs::localnet_challenge_shards()) {
        let cs = sc.take_shared_by_id<ChallengeShard>(z::challenge_shard_id(&c, i));
        assert!(rs::challenge_shard_size(&cs) == 0);
        ts::return_shared(cs);
        i = i + 1;
    };
    ts::return_shared(rev); ts::return_shared(tree); ts::return_shared(c);
    sc.end();
}

#[test]
fun a_sealed_zk_show_is_open_with_the_same_pages_as_the_public_profile() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 8, 4, 4, 2, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(rs::control_open(&c) && rs::control_sealed(&c));
    assert!(rs::control_claimed_pages(&c) == rs::control_page_count(&c));
    ts::return_shared(c);
    sc.end();
}

#[test, expected_failure(abort_code = 18, location = kix_rights_scale::rights_scale)]
fun claim_zk_twice_aborts() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::make_show(&mut sc, 8, 0, 4, 2, verifier);
    z::claim_zk(&mut sc, show, verifier);
    z::claim_zk(&mut sc, show, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 13, location = kix_rights_scale::rights_scale)]
fun claim_zk_after_seal_aborts() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::make_show(&mut sc, 8, 0, 4, 2, verifier);
    s::stage(&mut sc, show);
    s::seal(&mut sc, show);
    z::claim_zk(&mut sc, show, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 13, location = kix_rights_scale::rights_scale)]
fun claim_zk_after_cancel_aborts() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 8, 0, 4, 2, verifier);
    s::cancel(&mut sc, show);
    z::claim_zk(&mut sc, show, verifier);
    sc.end();
}

/// IM-13: the show pinned one verifier at creation; another frozen Verifier cannot stand in.
#[test, expected_failure(abort_code = 22, location = kix_rights_scale::rights_scale)]
fun claim_zk_with_a_verifier_other_than_the_pinned_one_aborts() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let other = z::verifier(&mut sc, z::other_manifest_hash());
    let show = z::make_show(&mut sc, 8, 0, 4, 2, verifier);
    z::claim_zk(&mut sc, show, other);
    sc.end();
}

#[test]
fun claim_zk_accepts_exactly_the_tree_capacity() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::make_show(&mut sc, 1000, 24, 64, 2, verifier);
    z::claim_zk(&mut sc, show, verifier);
    sc.end();
}

/// The circuit range-checks the slot to 10 bits and both trees hold 1,024 leaves.
#[test, expected_failure(abort_code = 17, location = kix_rights_scale::rights_scale)]
fun claim_zk_rejects_a_show_larger_than_the_tree() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::make_show(&mut sc, 1000, 25, 64, 2, verifier);
    z::claim_zk(&mut sc, show, verifier);
    sc.end();
}

/// RS-C11: a different circuit manifest hash gives a different domain for the same show ID
/// semantics, so no proof carries over between the two.
#[test]
fun two_shows_pinning_different_manifests_have_different_domains() {
    let mut sc = s::begin();
    let v1 = z::verifier(&mut sc, z::manifest_hash());
    let v2 = z::verifier(&mut sc, z::other_manifest_hash());
    let a = z::ready(&mut sc, 4, 0, 4, 1, v1);
    let b = z::ready(&mut sc, 4, 0, 4, 1, v2);
    sc.next_tx(s::a());
    let ca = sc.take_shared_by_id<ShowControl>(a);
    let cb = sc.take_shared_by_id<ShowControl>(b);
    assert!(rs::control_domain(&ca) != rs::control_domain(&cb));
    assert!(rs::control_domain(&cb) == rs::domain_of(b, rs::profile_version(), z::other_manifest_hash()));
    ts::return_shared(cb); ts::return_shared(ca);
    sc.end();
}

// ---------------------------------------------------------------- opt-in: the RS-1 path is untouched

#[test]
fun a_show_without_claim_zk_seals_and_revokes_exactly_as_in_rs1() {
    let mut sc = s::begin();
    let show = s::ready(&mut sc, 8, 0, 4, 2);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(!rs::control_zk_enabled(&c) && rs::control_domain(&c) == 0);
    ts::return_shared(c);
    s::issue(&mut sc, show, 3, 0, s::b());
    let t = s::latest_ticket(&mut sc);
    s::revoke(&mut sc, show, t);
    let (free, reserved, issued, retired) = s::totals(&mut sc, show);
    assert!(free == 7 && reserved == 0 && issued == 0 && retired == 1);
    sc.end();
}

/// RR-2: with a revocation root, a revoke that does not move the root would leave the note
/// valid, so the plain function refuses.
#[test, expected_failure(abort_code = 21, location = kix_rights_scale::rights_scale)]
fun plain_revoke_is_refused_on_a_show_with_a_revocation_root() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 8, 0, 4, 2, verifier);
    s::issue(&mut sc, show, 3, 0, s::b());
    let t = s::latest_ticket(&mut sc);
    s::revoke(&mut sc, show, t);
    sc.end();
}

// ---------------------------------------------------------------- identities and routing

#[test]
fun private_object_addresses_are_distinct_from_each_other_pages_and_payment_shards() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 8, 4, 4, 2, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut all = vector[rs::tree_address(&c), rs::revocation_address(&c)];
    let mut i = 0;
    while (i < 4) { all.push_back(rs::nullifier_shard_address(&c, i)); all.push_back(rs::challenge_shard_address(&c, i)); i = i + 1; };
    i = 0;
    while (i < rs::control_page_count(&c)) { all.push_back(rs::page_address(&c, i)); i = i + 1; };
    i = 0;
    while (i < rs::control_shard_count(&c)) { all.push_back(rs::shard_address(&c, i)); i = i + 1; };
    let mut a = 0;
    while (a < all.length()) {
        let mut b = a + 1;
        while (b < all.length()) { assert!(all[a] != all[b]); b = b + 1; };
        a = a + 1;
    };
    ts::return_shared(c);
    sc.end();
}

/// RS-C09 / RS-C11 / RS-C17: routing is a function of the value alone (within the show), so the
/// same nullifier or challenge always reaches the same shard, and different values spread.
#[test]
fun routing_is_a_function_of_the_value_alone() {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 8, 0, 4, 2, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let mut seen_n = vector[0, 0, 0, 0];
    let mut seen_c = vector[0, 0, 0, 0];
    let mut v = 1u256;
    while (v <= 64) {
        let n = rs::nullifier_shard_index(&c, v);
        let k = rs::challenge_shard_index(&c, v);
        assert!(n == rs::route_index(show, bcs::to_bytes(&v), rs::profile_version(), 4));
        assert!(k == rs::route_index(show, bcs::to_bytes(&v), rs::profile_version(), 4));
        assert!(n == rs::nullifier_shard_index(&c, v));
        *seen_n.borrow_mut(n) = *seen_n.borrow(n) + 1;
        *seen_c.borrow_mut(k) = *seen_c.borrow(k) + 1;
        v = v + 1;
    };
    let mut i = 0;
    while (i < 4) { assert!(seen_n[i] > 0 && seen_c[i] > 0); i = i + 1; };
    ts::return_shared(c);
    sc.end();
}

/// The routing input holds no slot and no section: it is the 32-byte value only (plus the
/// show-wide constants), so two values never route differently because of a slot.
#[test]
fun routing_bytes_are_the_value_bytes_only() {
    let v = 777u256;
    assert!(bcs::to_bytes(&v).length() == 32);
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 8, 0, 4, 2, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(rs::nullifier_shard_index(&c, v) == rs::route_index(show, bcs::to_bytes(&v), 1, 4));
    ts::return_shared(c);
    sc.end();
}
