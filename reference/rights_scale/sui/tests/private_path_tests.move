#[test_only]
/// The private path of the extended profile on actual shared objects: shield (RS-C10),
/// consume_private (RS-C09, RS-C11, RS-C17), the root rules (RR-1, RR-2, RR-3, RR-5, RR-6).
/// Proofs are not verifiable in a unit test, so the helpers run every check and state change
/// except the Groth16 call; `real_*` tests show the real functions fail closed at that call.
/// The Groth16 acceptance and rejection predicates run on the localnet (private-localnet.mjs).
module kix_rights_scale::private_path_tests;
use kix_rights_scale::rights_scale::{Self as rs, ShowControl, InventoryPage, NoteTree, RevocationState, NullifierShard,
    ChallengeShard, Ticket, NoteAdded, PrivateAdmission, RevocationLeaf};
use kix_rights_scale::root_math_tests as vectors;
use kix_rights_scale::support as s;
use kix_rights_scale::zk_support as z;
use sui::event;
use sui::test_scenario::{Self as ts, Scenario};

const FR: u256 = 21888242871839275222246405745257275088548364400416034343698204186575808495617;

fun fixture(): (Scenario, ID, ID) {
    let mut sc = s::begin();
    let verifier = z::verifier(&mut sc, z::manifest_hash());
    let show = z::ready(&mut sc, 12, 0, 4, 2, verifier);
    (sc, show, verifier)
}
/// Issues `slot` to B and shields it with `commitment` (commitments are arbitrary field values
/// here; their relation to a secret is the circuit's job).
fun shielded(sc: &mut Scenario, show: ID, verifier: ID, slot: u64, commitment: u256): ID {
    let t = z::issued(sc, show, slot, s::b());
    z::shield(sc, s::b(), show, t, 1, commitment, verifier);
    t
}

// ---------------------------------------------------------------- shield (RS-C10)

#[test]
fun shield_keeps_the_slot_occupied_marks_the_ticket_shielded_and_adds_one_note() {
    let (mut sc, show, verifier) = fixture();
    let before = z::note_root(&mut sc, show);
    let t = z::issued(&mut sc, show, 2, s::b());
    let (free0, reserved0, issued0, retired0) = s::totals(&mut sc, show);
    let inputs = z::shield(&mut sc, s::b(), show, t, 1, 4242, verifier);
    // Events are those of the latest transaction, so read them before the next one starts.
    assert!(event::events_by_type<NoteAdded>().length() == 1);
    // The mint proof's public inputs: commitment, slot, generation, domain.
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    assert!(inputs == vector[4242u256, 2u256, 1u256, rs::control_domain(&c)]);
    ts::return_shared(c);
    let (state, version) = z::state_of(&mut sc, t);
    assert!(state == rs::shielded_state() && version == 2);
    // Occupancy and the page counts do not change: the right is the same right.
    let (free1, reserved1, issued1, retired1) = s::totals(&mut sc, show);
    assert!(free0 == free1 && reserved0 == reserved1 && issued0 == issued1 && retired0 == retired1);
    assert!(z::note_root(&mut sc, show) != before);
    sc.end();
}

#[test]
fun shield_appends_in_insertion_order_and_the_page_is_not_written() {
    let (mut sc, show, verifier) = fixture();
    let mut slot = 0;
    while (slot < 3) {
        shielded(&mut sc, show, verifier, slot, 100 + (slot as u256));
        assert!(event::events_by_type<NoteAdded>().length() == 1);
        slot = slot + 1;
    };
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let tree = sc.take_shared_by_id<NoteTree>(z::tree_id(&c));
    assert!(rs::tree_leaf_count(&tree) == 3);
    ts::return_shared(tree); ts::return_shared(c);
    sc.end();
}

/// RS-C09: public consumption closes the ticket before the real shield's proof step.
#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_publicly_consumed_ticket_cannot_be_shielded() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    let (free0, reserved0, issued0, retired0) = s::totals(&mut sc, show);
    s::authorize(&mut sc, s::b(), show, t, 1);
    s::consume(&mut sc, show, t, 1);
    let (state, version) = z::state_of(&mut sc, t);
    assert!(state == 1 && version == 2);
    let (free1, reserved1, issued1, retired1) = s::totals(&mut sc, show);
    assert!(free0 == free1 && reserved0 == reserved1 && issued0 == issued1 && retired0 == retired1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let tree = sc.take_shared_by_id<NoteTree>(z::tree_id(&c));
    assert!(rs::tree_leaf_count(&tree) == 0 && rs::tree_root(&tree) == vectors::empty_root());
    ts::return_shared(tree); ts::return_shared(c);
    // Use the current version, pinned verifier and nonzero commitment: EClosed wins.
    z::shield_proved(&mut sc, s::b(), show, t, 2, 100, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_shielded_ticket_cannot_be_shielded_again() {
    let (mut sc, show, verifier) = fixture();
    let t = shielded(&mut sc, show, verifier, 0, 100);
    z::shield(&mut sc, s::b(), show, t, 2, 101, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_shielded_ticket_cannot_be_offered() {
    let (mut sc, show, verifier) = fixture();
    let t = shielded(&mut sc, show, verifier, 0, 100);
    s::offer(&mut sc, s::b(), show, t, 2, s::c(), 0);
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_shielded_ticket_cannot_authorize_a_public_admission() {
    let (mut sc, show, verifier) = fixture();
    let t = shielded(&mut sc, show, verifier, 0, 100);
    s::authorize(&mut sc, s::b(), show, t, 2);
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun a_shielded_ticket_cannot_be_refunded() {
    let (mut sc, show, verifier) = fixture();
    let t = shielded(&mut sc, show, verifier, 0, 100);
    s::refund(&mut sc, show, t, 2, s::b());
    sc.end();
}

#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun a_shielded_slot_cannot_be_issued_again() {
    let (mut sc, show, verifier) = fixture();
    shielded(&mut sc, show, verifier, 0, 100);
    s::issue(&mut sc, show, 0, 1, s::c());
    sc.end();
}

#[test, expected_failure(abort_code = 9, location = kix_rights_scale::rights_scale)]
fun a_shielded_slot_cannot_be_reserved_for_sale() {
    let (mut sc, show, verifier) = fixture();
    shielded(&mut sc, show, verifier, 0, 100);
    s::reserve(&mut sc, show, 0, 1, s::c(), 5000, s::ref_bytes(7));
    sc.end();
}

#[test, expected_failure(abort_code = 2, location = kix_rights_scale::rights_scale)]
fun only_the_holder_can_shield() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    z::shield(&mut sc, s::c(), show, t, 1, 100, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun shield_needs_the_current_ticket_version() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    z::shield(&mut sc, s::b(), show, t, 2, 100, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun a_zero_commitment_is_rejected() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    z::shield(&mut sc, s::b(), show, t, 1, 0, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun a_commitment_outside_the_field_is_rejected() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    z::shield(&mut sc, s::b(), show, t, 1, FR, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 1, location = kix_rights_scale::rights_scale)]
fun shield_is_refused_after_the_show_is_cancelled() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    s::cancel(&mut sc, show);
    z::shield(&mut sc, s::b(), show, t, 1, 100, verifier);
    sc.end();
}

/// RS-C16 / RR-5: the one note tree of THIS show. Another show's tree is refused.
#[test, expected_failure(abort_code = 18, location = kix_rights_scale::rights_scale)]
fun shield_with_another_shows_tree_aborts() {
    let (mut sc, show, verifier) = fixture();
    let other = z::ready(&mut sc, 4, 0, 4, 1, verifier);
    let t = z::issued(&mut sc, show, 0, s::b());
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(other);
    let foreign = z::tree_id(&c);
    ts::return_shared(c);
    z::shield_with(&mut sc, s::b(), show, foreign, t, 1, 100, verifier);
    sc.end();
}

/// IM-13: the Verifier is the show's pinned one.
#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun shield_with_a_verifier_other_than_the_pinned_one_aborts() {
    let (mut sc, show, verifier) = fixture();
    let other = z::verifier(&mut sc, z::other_manifest_hash());
    let t = z::issued(&mut sc, show, 0, s::b());
    let _ = verifier;
    z::shield(&mut sc, s::b(), show, t, 1, 100, other);
    sc.end();
}

/// The real `shield` passes every check above and then stops at Groth16 (an empty test key
/// cannot verify): the proof step cannot be skipped.
#[test, expected_failure]
fun the_real_shield_fails_closed_at_the_proof_step() {
    let (mut sc, show, verifier) = fixture();
    let t = z::issued(&mut sc, show, 0, s::b());
    z::shield_proved(&mut sc, s::b(), show, t, 1, 100, verifier);
    sc.end();
}

// ---------------------------------------------------------------- consume_private

fun two_notes(): (Scenario, ID, ID, u256, u256) {
    let (mut sc, show, verifier) = fixture();
    shielded(&mut sc, show, verifier, 0, 111);
    let root_one = z::note_root(&mut sc, show);
    shielded(&mut sc, show, verifier, 1, 222);
    let root_two = z::note_root(&mut sc, show);
    (sc, show, verifier, root_one, root_two)
}

#[test]
fun consume_private_binds_roots_domain_and_gate_context_and_records_both_values() {
    let (mut sc, show, verifier, _root_one, root_two) = two_notes();
    let rev_root = z::revocation_root(&mut sc, show);
    let inputs = z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    assert!(event::events_by_type<PrivateAdmission>().length() == 1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    // [noteRoot, revocationRoot, nullifier, context, domain, action]
    assert!(inputs.length() == 6);
    assert!(inputs[0] == root_two && inputs[1] == rev_root && inputs[2] == 7001);
    assert!(inputs[3] == z::gate_context(s::gate(), 8001, 90000));
    assert!(inputs[4] == rs::control_domain(&c) && inputs[5] == 1);
    let ns = sc.take_shared_by_id<NullifierShard>(z::nullifier_shard_id(&c, rs::nullifier_shard_index(&c, 7001)));
    let cs = sc.take_shared_by_id<ChallengeShard>(z::challenge_shard_id(&c, rs::challenge_shard_index(&c, 8001)));
    assert!(rs::nullifier_spent(&ns, 7001) && rs::challenge_used(&cs, 8001));
    assert!(!rs::nullifier_spent(&ns, 7002) && !rs::challenge_used(&cs, 8002));
    ts::return_shared(cs); ts::return_shared(ns); ts::return_shared(c);
    sc.end();
}

/// IM-18: a later show pins manifest B while show A keeps its original domain/verifier.
/// The unproven helper checks Move state and bindings, not Groth16 acceptance.
#[test]
fun a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed() {
    let (mut sc, show, verifier, root_one, root_two) = two_notes();
    let before = z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    let domain = before[4];
    assert!(domain == rs::domain_of(show, rs::profile_version(), z::manifest_hash()));
    let other_verifier = z::verifier(&mut sc, z::other_manifest_hash());
    let other = z::ready(&mut sc, 4, 0, 4, 1, other_verifier);
    sc.next_tx(s::a());
    let ca = sc.take_shared_by_id<ShowControl>(show);
    let cb = sc.take_shared_by_id<ShowControl>(other);
    assert!(rs::control_domain(&cb) == rs::domain_of(other, rs::profile_version(), z::other_manifest_hash()));
    assert!(rs::control_domain(&cb) != domain && rs::control_domain(&ca) == domain);
    ts::return_shared(cb); ts::return_shared(ca);
    let after = z::consume(&mut sc, show, root_one, 7002, 8002, verifier);
    assert!(after[4] == domain);
    assert!(event::events_by_type<PrivateAdmission>().length() == 1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let ns = sc.take_shared_by_id<NullifierShard>(z::nullifier_shard_id(&c, rs::nullifier_shard_index(&c, 7002)));
    let cs = sc.take_shared_by_id<ChallengeShard>(z::challenge_shard_id(&c, rs::challenge_shard_index(&c, 8002)));
    assert!(rs::nullifier_spent(&ns, 7002) && rs::challenge_used(&cs, 8002));
    ts::return_shared(cs); ts::return_shared(ns); ts::return_shared(c);
    sc.end();
}

#[test]
fun consume_private_changes_no_ticket_and_no_page() {
    let (mut sc, show, verifier, _root_one, root_two) = two_notes();
    let (free0, reserved0, issued0, retired0) = s::totals(&mut sc, show);
    z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    let (free1, reserved1, issued1, retired1) = s::totals(&mut sc, show);
    assert!(free0 == free1 && reserved0 == reserved1 && issued0 == issued1 && retired0 == retired1);
    sc.end();
}

/// RS-C09: the same nullifier is refused, whichever challenge accompanies it.
#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun a_replayed_nullifier_is_rejected() {
    let (mut sc, show, verifier, _root_one, root_two) = two_notes();
    z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    z::consume(&mut sc, show, root_two, 7001, 8002, verifier);
    sc.end();
}

/// RS-C17: the same challenge with a different nullifier (a different shard family entry) is
/// refused; challenge uniqueness is show-wide, not per nullifier shard.
#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun a_replayed_challenge_with_another_nullifier_is_rejected() {
    let (mut sc, show, verifier, _root_one, root_two) = two_notes();
    z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    z::consume(&mut sc, show, root_two, 7002, 8001, verifier);
    sc.end();
}

#[test]
fun different_nullifiers_and_challenges_are_accepted_independently() {
    let (mut sc, show, verifier, root_one, root_two) = two_notes();
    z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    z::consume(&mut sc, show, root_one, 7002, 8002, verifier);
    assert!(event::events_by_type<PrivateAdmission>().length() == 1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let first = sc.take_shared_by_id<NullifierShard>(z::nullifier_shard_id(&c, rs::nullifier_shard_index(&c, 7001)));
    assert!(rs::nullifier_spent(&first, 7001));
    ts::return_shared(first);
    let second = sc.take_shared_by_id<NullifierShard>(z::nullifier_shard_id(&c, rs::nullifier_shard_index(&c, 7002)));
    assert!(rs::nullifier_spent(&second, 7002));
    ts::return_shared(second); ts::return_shared(c);
    sc.end();
}

#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun a_zero_nullifier_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    z::consume(&mut sc, show, root_two, 0, 8001, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 8, location = kix_rights_scale::rights_scale)]
fun a_challenge_outside_the_field_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    z::consume(&mut sc, show, root_two, 7001, FR, verifier);
    sc.end();
}

// RS-C11: the shard is the one the value routes to; any other shard is refused.
fun other_than(index: u64): u64 { (index + 1) % rs::localnet_nullifier_shards() }

#[test, expected_failure(abort_code = 16, location = kix_rights_scale::rights_scale)]
fun a_proof_submitted_to_a_different_nullifier_shard_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let wrong = z::nullifier_shard_id(&c, other_than(rs::nullifier_shard_index(&c, 7001)));
    ts::return_shared(c);
    z::consume_with(&mut sc, s::gate(), z::with_nullifier_shard(choice, wrong), root_two, 7001, 8001, 90000);
    sc.end();
}

#[test, expected_failure(abort_code = 16, location = kix_rights_scale::rights_scale)]
fun a_challenge_recorded_in_a_different_challenge_shard_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let wrong = z::challenge_shard_id(&c, other_than(rs::challenge_shard_index(&c, 8001)));
    ts::return_shared(c);
    z::consume_with(&mut sc, s::gate(), z::with_challenge_shard(choice, wrong), root_two, 7001, 8001, 90000);
    sc.end();
}

/// A nullifier shard in the challenge family's slot (and vice versa) is another type, so it
/// cannot even be passed; but the right type of another show is refused as well.
#[test, expected_failure(abort_code = 16, location = kix_rights_scale::rights_scale)]
fun another_shows_shard_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let other = z::ready(&mut sc, 4, 0, 4, 1, verifier);
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    let foreign = z::own(&mut sc, other, 7001, 8001, verifier);
    let wrong = z::nullifier_shard_of(&foreign);
    z::consume_with(&mut sc, s::gate(), z::with_nullifier_shard(choice, wrong), root_two, 7001, 8001, 90000);
    sc.end();
}

#[test, expected_failure(abort_code = 18, location = kix_rights_scale::rights_scale)]
fun another_shows_note_tree_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let other = z::ready(&mut sc, 4, 0, 4, 1, verifier);
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(other);
    let foreign = z::tree_id(&c);
    ts::return_shared(c);
    z::consume_with(&mut sc, s::gate(), z::with_tree(choice, foreign), root_two, 7001, 8001, 90000);
    sc.end();
}

#[test, expected_failure(abort_code = 18, location = kix_rights_scale::rights_scale)]
fun another_shows_revocation_state_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let other = z::ready(&mut sc, 4, 0, 4, 1, verifier);
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(other);
    let foreign = z::revocation_id(&c);
    ts::return_shared(c);
    z::consume_with(&mut sc, s::gate(), z::with_revocation(choice, foreign), root_two, 7001, 8001, 90000);
    sc.end();
}

/// IM-13 / RS-C11: a Verifier object other than the show's pinned one is refused before any
/// proof is looked at, so the caller cannot pick the key.
#[test, expected_failure(abort_code = 4, location = kix_rights_scale::rights_scale)]
fun a_verifier_other_than_the_pinned_one_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    z::consume(&mut sc, show, root_two, 7000, 8000, verifier);
    let other = z::verifier(&mut sc, z::other_manifest_hash());
    let _other_show = z::ready(&mut sc, 4, 0, 4, 1, other);
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    z::consume_with(&mut sc, s::gate(), z::with_verifier(choice, other), root_two, 7001, 8001, 90000);
    sc.end();
}

#[test, expected_failure(abort_code = 4, location = kix_rights_scale::rights_scale)]
fun only_a_listed_gate_can_consume_privately() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    z::consume_with(&mut sc, s::b(), choice, root_two, 7001, 8001, 90000);
    sc.end();
}

#[test, expected_failure(abort_code = 4, location = kix_rights_scale::rights_scale)]
fun private_consumption_is_refused_after_the_show_is_cancelled() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    s::cancel(&mut sc, show);
    z::consume(&mut sc, show, root_two, 7001, 8001, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun an_expiry_in_the_past_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    z::consume_with(&mut sc, s::gate(), choice, root_two, 7001, 8001, 0);
    sc.end();
}

#[test, expected_failure(abort_code = 6, location = kix_rights_scale::rights_scale)]
fun an_expiry_beyond_two_minutes_is_rejected() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    z::consume_with(&mut sc, s::gate(), choice, root_two, 7001, 8001, 120001);
    sc.end();
}

#[test]
fun an_expiry_of_exactly_two_minutes_is_accepted() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    let choice = z::own(&mut sc, show, 7001, 8001, verifier);
    z::consume_with(&mut sc, s::gate(), choice, root_two, 7001, 8001, 120000);
    sc.end();
}

#[test, expected_failure]
fun the_real_consume_private_fails_closed_at_the_proof_step() {
    let (mut sc, show, verifier, _r, root_two) = two_notes();
    z::consume_proved(&mut sc, show, root_two, 7001, 8001, verifier);
    sc.end();
}

// ---------------------------------------------------------------- RR-1: the root history

/// K = 4 in this package. After n notes the current root has age 0; a root is accepted while
/// its age is below K and refused from age K on. Roots are those of the tree after each shield.
fun five_notes(): (Scenario, ID, ID, vector<u256>) {
    let (mut sc, show, verifier) = fixture();
    let mut roots = vector[];
    let mut slot = 0;
    while (slot < 5) {
        shielded(&mut sc, show, verifier, slot, 300 + (slot as u256));
        roots.push_back(z::note_root(&mut sc, show));
        slot = slot + 1;
    };
    (sc, show, verifier, roots)
}

#[test]
fun a_root_of_age_k_minus_one_is_accepted() {
    let (mut sc, show, verifier, roots) = five_notes();
    // roots[4] is current (age 0); roots[1] has age 3 = K - 1.
    z::consume(&mut sc, show, roots[1], 7001, 8001, verifier);
    z::consume(&mut sc, show, roots[4], 7002, 8002, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_root_of_age_k_is_rejected() {
    let (mut sc, show, verifier, roots) = five_notes();
    // roots[0] was current five shields ago minus four: age 4 = K.
    z::consume(&mut sc, show, roots[0], 7001, 8001, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun the_empty_root_ages_out_too() {
    let (mut sc, show, verifier, _roots) = five_notes();
    z::consume(&mut sc, show, vectors::empty_root(), 7001, 8001, verifier);
    sc.end();
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_root_that_never_existed_is_rejected() {
    let (mut sc, show, verifier, _roots) = five_notes();
    z::consume(&mut sc, show, 999999, 7001, 8001, verifier);
    sc.end();
}

// ---------------------------------------------------------------- RR-2 / RR-3: revocation root

fun revocable(): (Scenario, ID, ID, ID, ID) {
    let (mut sc, show, verifier) = fixture();
    let t5 = z::issued(&mut sc, show, 5, s::b());
    let t6 = z::issued(&mut sc, show, 6, s::b());
    (sc, show, verifier, t5, t6)
}

/// RR-2-T1: issuance and refund never write the revocation root; `revoke_with_root` does.
#[test]
fun issue_and_refund_do_not_change_the_revocation_root_but_revoke_does() {
    let (mut sc, show, verifier, t5, t6) = revocable();
    let empty = z::revocation_root(&mut sc, show);
    assert!(empty == vectors::empty_root());
    // Issue, refund and reissue another slot, and shield a third: the root stays put.
    let t7 = z::issued(&mut sc, show, 7, s::b());
    s::refund(&mut sc, show, t7, 1, s::b());
    s::issue(&mut sc, show, 7, 1, s::b());
    shielded(&mut sc, show, verifier, 8, 777);
    assert!(z::revocation_root(&mut sc, show) == empty);
    // Revoking slot 5 (generation 1) moves it to the known-answer root.
    z::revoke_rooted(&mut sc, show, t5, 0, vectors::rev_siblings_5());
    assert!(z::revocation_root(&mut sc, show) == vectors::rev_root_slot5_gen1());
    // A second revocation built from the updated tree reaches the combined root.
    z::revoke_rooted(&mut sc, show, t6, 0, vectors::rev_siblings_6_after_5());
    assert!(event::events_by_type<RevocationLeaf>().length() == 1);
    assert!(z::revocation_root(&mut sc, show) == vectors::rev_root_slot5_gen1_slot6_gen1());
    sc.end();
}

#[test]
fun revoke_with_root_voids_the_ticket_and_retires_the_slot_without_reopening_it() {
    let (mut sc, show, _verifier, t5, _t6) = revocable();
    let (free0, _reserved0, issued0, retired0) = s::totals(&mut sc, show);
    z::revoke_rooted(&mut sc, show, t5, 0, vectors::rev_siblings_5());
    let (state, version) = z::state_of(&mut sc, t5);
    assert!(state == 2 && version == 2);
    let (free1, _reserved1, issued1, retired1) = s::totals(&mut sc, show);
    assert!(free1 == free0 && issued1 == issued0 - 1 && retired1 == retired0 + 1);
    sc.next_tx(s::a());
    let c = sc.take_shared_by_id<ShowControl>(show);
    let p = sc.take_shared_by_id<InventoryPage>(z::page_id_of(&c, 5));
    assert!(rs::page_generation(&p, 5) == 2 && rs::page_occupied(&p, 5));
    ts::return_shared(p); ts::return_shared(c);
    sc.end();
}

#[test]
fun a_shielded_ticket_can_be_revoked() {
    let (mut sc, show, verifier) = fixture();
    let t = shielded(&mut sc, show, verifier, 5, 555);
    z::revoke_rooted(&mut sc, show, t, 0, vectors::rev_siblings_5());
    assert!(z::revocation_root(&mut sc, show) == vectors::rev_root_slot5_gen1());
    let (state, _version) = z::state_of(&mut sc, t);
    assert!(state == 2);
    sc.end();
}

/// RR-3 (W = 0): the chain feeds the CURRENT revocation root to the verifier, so a proof made
/// against the root from before a revoke no longer verifies after it.
#[test]
fun consume_private_uses_the_current_revocation_root_never_one_from_the_caller() {
    let (mut sc, show, verifier) = fixture();
    let t = shielded(&mut sc, show, verifier, 5, 555);
    shielded(&mut sc, show, verifier, 6, 666);
    let root = z::note_root(&mut sc, show);
    let before = z::consume(&mut sc, show, root, 7001, 8001, verifier);
    assert!(before[1] == vectors::empty_root());
    z::revoke_rooted(&mut sc, show, t, 0, vectors::rev_siblings_5());
    let after = z::consume(&mut sc, show, root, 7002, 8002, verifier);
    assert!(after[1] == vectors::rev_root_slot5_gen1() && after[1] != before[1]);
    sc.end();
}

/// RR-2 storage (b): two revocations built on the same root conflict; the second is rebuilt.
#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_revocation_built_on_a_stale_root_is_rejected() {
    let (mut sc, show, _verifier, t5, t6) = revocable();
    z::revoke_rooted(&mut sc, show, t5, 0, vectors::rev_siblings_5());
    // Slot 6's path in the EMPTY tree (all siblings are the empty-subtree roots).
    z::revoke_rooted(&mut sc, show, t6, 0, vectors::rev_siblings_5());
    sc.end();
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_revocation_with_a_tampered_sibling_is_rejected() {
    let (mut sc, show, _verifier, t5, _t6) = revocable();
    let mut siblings = vectors::rev_siblings_5();
    *siblings.borrow_mut(3) = 1;
    z::revoke_rooted(&mut sc, show, t5, 0, siblings);
    sc.end();
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_revocation_claiming_a_wrong_prior_leaf_is_rejected() {
    let (mut sc, show, _verifier, t5, _t6) = revocable();
    // The slot was never revoked, so the prior leaf is 0; 5 is not a smaller generation than 1.
    z::revoke_rooted(&mut sc, show, t5, 5, vectors::rev_siblings_5());
    sc.end();
}

#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_revocation_cannot_lower_the_recorded_generation() {
    let (mut sc, show, _verifier, t5, _t6) = revocable();
    // prior == the ticket's own generation means the slot would not move forward.
    z::revoke_rooted(&mut sc, show, t5, 1, vectors::rev_siblings_5());
    sc.end();
}

#[test, expected_failure(abort_code = 3, location = kix_rights_scale::rights_scale)]
fun revoking_another_shows_ticket_aborts() {
    let (mut sc, show, verifier, _t5, _t6) = revocable();
    let other = z::ready(&mut sc, 8, 0, 4, 1, verifier);
    let foreign = z::issued(&mut sc, other, 5, s::b());
    z::revoke_rooted(&mut sc, show, foreign, 0, vectors::rev_siblings_5());
    sc.end();
}

/// An honest second witness for the same ticket names prior leaf 1, which is not below the
/// ticket's generation, so the leaf can never be moved backwards or revoked twice.
#[test, expected_failure(abort_code = 19, location = kix_rights_scale::rights_scale)]
fun a_ticket_cannot_be_revoked_twice() {
    let (mut sc, show, _verifier, t5, _t6) = revocable();
    z::revoke_rooted(&mut sc, show, t5, 0, vectors::rev_siblings_5());
    z::revoke_rooted(&mut sc, show, t5, 1, vectors::rev_siblings_5());
    sc.end();
}
