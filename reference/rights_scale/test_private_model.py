"""Unit tests of the RS-2 private-path model and of its agreement with the Move package.

Run: python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale

The model has no hashes and no proofs (see model.py), so these tests pin the rules that do not
need them: the root-history window, the revocation counter, SHIELDED, the sets, and the order
of checks. Root arithmetic is pinned by sui/tests/root_math_tests.move against circomlibjs, and
proof acceptance by client/private-localnet.mjs against an actual chain.
"""
import re
import unittest
from pathlib import Path

import model
import replay_private as rp
from model import Abort, Show

HERE = Path(__file__).resolve().parent
MOVE = (HERE / 'sui' / 'sources' / 'rights_scale.move').read_text()
DRIVER = (HERE / 'client' / 'private-localnet.mjs').read_text()
CONSTANTS = (HERE / 'client' / 'profile-constants.mjs').read_text()
VECTORS = rp.load()


def aborts(code, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Abort as abort:
        return abort.code == code
    return False


def zk_show(seated=12, page_size=4, shards=1, seal=True, claim_zk=True, verifier='v1', show_id=None):
    extra = {} if show_id is None else {'show_id': show_id}
    show = Show('issuer', seated, 0, page_size, shards, gates=['gate', 'gate2'], payment_attesters=['attester'],
                verifier=verifier, **extra)
    show.claim_pages('issuer', 0, show.page_count)
    show.claim_shards('issuer', 0, show.shard_count)
    if claim_zk:
        show.claim_zk('issuer', verifier, 'm1')
    if seal:
        show.seal('issuer')
    return show


def shielded(show, count):
    """Issues and shields `count` slots; returns the notes' labels."""
    notes = []
    for slot in range(count):
        t = show.issue('issuer', slot, 0, 'a')
        show.shield('a', t.id, 1, f'n{slot}')
        notes.append(f'n{slot}')
    return notes


def proof(show, note, **kw):
    """What the prover commits to for `note` against the show's state now."""
    base = dict(nullifier=('nf', note), challenge=('challenge', note), domain=show.domain, show=show.show_id,
                note_count=len(show.leaves), revocations=show.revocations, gate='gate', ttl_ms=90000)
    base.update(kw)
    return base


class MoveParity(unittest.TestCase):
    def constant(self, name, source=MOVE):
        return int(re.search(rf'^const {name}: u(?:64|8) = (\d+);', source, re.M).group(1))

    def test_constants_match_the_move_source(self):
        for name in ('ZK_DEPTH', 'LOCALNET_ROOT_HISTORY_K', 'LOCALNET_NULLIFIER_SHARDS', 'LOCALNET_CHALLENGE_SHARDS'):
            self.assertEqual(self.constant(name), getattr(model, name), name)
        self.assertEqual(self.constant('SHIELDED'), model.SHIELDED)
        self.assertEqual(model.LOCALNET_ROOT_HISTORY_K, 4)  # vectors/private_path.json is written for K = 4

    def test_the_client_constants_equal_the_move_constants(self):
        js = {name: int(value) for name, value in re.findall(r'^export const (\w+)=(\d+);', CONSTANTS, re.M)}
        self.assertEqual(js['DEPTH'], model.ZK_DEPTH)
        self.assertEqual(js['SLOT_BITS'], model.ZK_DEPTH)
        self.assertEqual(js['ROOT_HISTORY_K'], model.LOCALNET_ROOT_HISTORY_K)
        self.assertEqual(js['NULLIFIER_SHARDS'], model.LOCALNET_NULLIFIER_SHARDS)
        self.assertEqual(js['CHALLENGE_SHARDS'], model.LOCALNET_CHALLENGE_SHARDS)
        self.assertEqual(js['PROFILE_VERSION'], model.PROFILE_VERSION)
        self.assertEqual(js['SHIELDED'], model.SHIELDED)

    def test_rs2_error_codes_match_the_move_source(self):
        for name in ('EProof', 'EZk', 'ERoot', 'ETreeFull', 'ERootRequired', 'EVerifier'):
            self.assertEqual(self.constant(name), getattr(model, name), name)

    def test_the_rs2_constants_are_labelled_localnet_and_astra_owned(self):
        block = MOVE[MOVE.index('// RS-2 localnet fixture values; Astra-owned.'):MOVE.index('/// Key space of page claims.')]
        for name in ('ZK_DEPTH', 'LOCALNET_ROOT_HISTORY_K', 'LOCALNET_NULLIFIER_SHARDS', 'LOCALNET_CHALLENGE_SHARDS'):
            self.assertIn(f'const {name}: u64', block)
        self.assertIn('operational default', block)

    def test_private_operations_are_in_the_move_source_with_the_modelled_check_order(self):
        # shield: live, holder, idle, verifier, range, tree, capacity - then the proof - then the state change.
        shield = MOVE[MOVE.index('fun shield_inputs'):MOVE.index('fun shield_apply')]
        order = [shield.index(x) for x in ('live(c, p, t, version)', 'ENotHolder', 'idle(t, clk)',
                                            'c.verifier == object::id(v)', 'check_tree(c, tree)', 'ETreeFull')]
        self.assertEqual(order, sorted(order))
        # consume_private: authority, objects, shards, field/replay, expiry, root history, then the proof.
        consume = MOVE[MOVE.index('fun private_inputs'):MOVE.index('fun private_apply')]
        order = [consume.index(x) for x in ('EAuthority', 'check_tree', 'check_revocation', 'check_nullifier_shard',
                                             'check_challenge_shard', 'EProof', 'EPolicy', 'ERoot')]
        self.assertEqual(order, sorted(order))
        spend = MOVE[MOVE.index('public fun consume_private'):MOVE.index('fun private_inputs')]
        self.assertLess(spend.index('private_inputs('), spend.index('zk_gate::spend('))
        self.assertLess(spend.index('zk_gate::spend('), spend.index('private_apply('))

    def test_the_verifier_is_never_a_caller_supplied_key(self):
        zk_gate = (HERE / 'sui' / 'sources' / 'zk_gate.move').read_text()
        self.assertRegex(zk_gate, r'public\(package\) fun mint\(v: &Verifier')
        self.assertRegex(zk_gate, r'public\(package\) fun spend\(v: &Verifier')
        self.assertNotRegex(zk_gate, r'public fun (mint|spend)\(')
        self.assertIn('transfer::freeze_object', zk_gate)
        self.assertEqual(len(re.findall(r'freeze_object', zk_gate)), 2)  # create, and the test_only helper

    def test_every_vector_op_is_handled_by_the_driver(self):
        ops = {step['op'] for scenario in VECTORS['scenarios'] for step in scenario['steps']}
        for op in ops:
            self.assertIn(f"case '{op}'", DRIVER, op)

    def test_the_package_defines_no_coin_or_token_module(self):
        for source in (MOVE, (HERE / 'sui' / 'sources' / 'zk_gate.move').read_text()):
            for needle in ('coin::', 'balance::', 'TreasuryCap', 'sui::token'):
                self.assertNotIn(needle, source)


class ClaimZk(unittest.TestCase):
    def test_claim_zk_fixes_the_domain_and_takes_ten_claim_numbers(self):
        show = zk_show(seal=False, claim_zk=False)
        before = show.claim_sequence
        show.claim_zk('issuer', 'v1', 'm1')
        self.assertEqual(show.domain, (show.show_id, model.PROFILE_VERSION, 'm1'))
        self.assertEqual(show.claim_sequence - before, 2 + model.LOCALNET_NULLIFIER_SHARDS + model.LOCALNET_CHALLENGE_SHARDS)

    def test_the_domain_binds_show_profile_and_manifest(self):
        a = zk_show(seal=False, claim_zk=False)
        b = Show('issuer', 12, 0, 4, 1, gates=['gate'], payment_attesters=[], verifier='v1', show_id=b'\x00' * 31 + b'\x09')
        c = zk_show(seal=False, claim_zk=False)
        a.claim_zk('issuer', 'v1', 'm1')
        b.claim_zk('issuer', 'v1', 'm1')
        c.claim_zk('issuer', 'v1', 'm2')
        self.assertEqual(len({a.domain, b.domain, c.domain}), 3)

    def test_a_second_claim_after_seal_cancel_or_with_another_verifier_aborts(self):
        show = zk_show(seal=False)
        self.assertTrue(aborts(model.EZk, show.claim_zk, 'issuer', 'v1', 'm1'))
        fresh = zk_show(seal=False, claim_zk=False)
        self.assertTrue(aborts(model.EVerifier, fresh.claim_zk, 'issuer', 'v2', 'm2'))
        show.seal('issuer')
        self.assertTrue(aborts(model.ESealed, show.claim_zk, 'issuer', 'v1', 'm1'))

    def test_the_slot_bit_bound_is_the_log_ceiling_at_several_sizes(self):
        # IM-14: the model exposes the slot-bit rule only through the claim_zk
        # capacity bound `capacity <= 2 ** ZK_DEPTH`; (n - 1).bit_length() is
        # the log ceiling of n slots.
        for capacity in (1, 15, 16, 17, 255, 256, 257, 1023, 1024, 1025, 2000):
            show = zk_show(seated=capacity, page_size=64, seal=False, claim_zk=False)
            if (capacity - 1).bit_length() <= model.ZK_DEPTH:
                show.claim_zk('issuer', 'v1', 'm1')
                self.assertIsNotNone(show.domain, capacity)
            else:
                self.assertTrue(aborts(model.ERange, show.claim_zk, 'issuer', 'v1', 'm1'),
                                capacity)

    def test_a_show_larger_than_the_tree_cannot_enable_the_private_path(self):
        show = zk_show(seated=1025, page_size=64, seal=False, claim_zk=False)
        self.assertTrue(aborts(model.ERange, show.claim_zk, 'issuer', 'v1', 'm1'))
        zk_show(seated=1024, page_size=64, seal=False)

    def test_only_the_issuer_claims(self):
        show = zk_show(seal=False, claim_zk=False)
        self.assertTrue(aborts(model.EAuthority, show.claim_zk, 'a', 'v1', 'm1'))

    def test_the_private_path_is_opt_in_and_the_public_path_is_unchanged_without_it(self):
        show = zk_show(claim_zk=False)
        t = show.issue('issuer', 0, 0, 'a')
        self.assertTrue(aborts(model.EZk, show.shield, 'a', t.id, 1, 'n0'))
        show.revoke('issuer', t.id)  # the plain revoke still works
        self.assertEqual(show.private_snapshot()['zk_enabled'], False)


class Shield(unittest.TestCase):
    def test_shield_keeps_occupancy_and_adds_one_note(self):  # RS-C10
        show = zk_show()
        t = show.issue('issuer', 2, 0, 'a')
        before = show.totals()
        show.shield('a', t.id, 1, 'n2')
        self.assertEqual((t.state, t.version), (model.SHIELDED, 2))
        self.assertEqual(show.totals(), before)
        self.assertEqual(show.leaves, ['n2'])
        show.check_invariants()

    def test_a_shielded_slot_cannot_be_resold_refunded_or_reissued(self):  # RS-C10
        show = zk_show()
        t = show.issue('issuer', 0, 0, 'a')
        show.shield('a', t.id, 1, 'n0')
        self.assertTrue(aborts(model.EClosed, show.shield, 'a', t.id, 2, 'again'))
        self.assertTrue(aborts(model.EClosed, show.offer, 'a', t.id, 2, 'b', 0, 600000))
        self.assertTrue(aborts(model.EClosed, show.authorize_admission, 'a', t.id, 2, 'gate', b'\x01' * 32, 60000))
        self.assertTrue(aborts(model.EClosed, show.refund, 'a', t.id, 2))
        self.assertTrue(aborts(model.EInventory, show.issue, 'issuer', 0, 1, 'b'))
        self.assertTrue(aborts(model.EInventory, show.attest_issuance, 'attester', 0, 1, 'b', 5, b'\x07' * 32))

    def test_shield_checks_holder_version_verifier_and_the_proof_binding(self):
        show = zk_show()
        t = show.issue('issuer', 0, 0, 'a')
        self.assertTrue(aborts(model.ENotHolder, show.shield, 'b', t.id, 1, 'n0'))
        self.assertTrue(aborts(model.EStale, show.shield, 'a', t.id, 2, 'n0'))
        self.assertTrue(aborts(model.EProof, show.shield, 'a', t.id, 1, 'n0', verifier='v2'))
        self.assertTrue(aborts(model.EBadProof, show.shield, 'a', t.id, 1, 'n0', proof_domain=('foreign',)))
        self.assertTrue(aborts(model.EBadProof, show.shield, 'a', t.id, 1, 'n0', proof_commitment='other'))
        self.assertEqual(show.leaves, [])  # every rejection left nothing behind

    def test_shield_is_refused_after_the_show_is_cancelled(self):
        show = zk_show()
        t = show.issue('issuer', 0, 0, 'a')
        show.cancel_show('issuer')
        self.assertTrue(aborts(model.EClosed, show.shield, 'a', t.id, 1, 'n0'))

    def test_a_publicly_consumed_ticket_cannot_be_shielded(self):  # RS-C09
        # The other half of "once in total": a ticket consumed publicly first
        # cannot move into the private path. The model cannot construct a
        # private spend for it at all — a spend needs a note, and the only
        # note-creating step refuses the consumed ticket.
        show = zk_show()
        t = show.issue('issuer', 0, 0, 'a')
        show.authorize_admission('a', t.id, 1, 'gate', b'\x07' * 32, 60000)
        show.consume('gate', t.id, 1, b'\x07' * 32)
        self.assertEqual((t.state, t.version), (model.CONSUMED, 2))
        self.assertTrue(aborts(model.EClosed, show.shield, 'a', t.id, 2, 'n0'))
        self.assertEqual(show.leaves, [])
        self.assertEqual(show.private_snapshot()['nullifiers'], 0)
        # The consumed slot stays occupied: nothing reissues it into the tree.
        self.assertTrue(aborts(model.EInventory, show.issue, 'issuer', 0, 1, 'b'))
        self.assertTrue(aborts(model.EClosed, show.offer, 'a', t.id, 2, 'b', 0, 600000))
        self.assertTrue(aborts(model.EClosed, show.authorize_admission, 'a', t.id, 2,
                               'gate', b'\x01' * 32, 60000))
        show.check_invariants()

    def test_notes_never_exceed_the_slots(self):  # RS-C10: the next shield after "slots" is refused
        show = zk_show(seated=4, page_size=4)
        shielded(show, 4)
        self.assertEqual(len(show.leaves), 4)
        self.assertTrue(aborts(model.EClosed, show.shield, 'a', 'T1', 2, 'extra'))
        show.check_invariants()


class RootHistory(unittest.TestCase):
    """RR-1 with K = 4: the roots of the last K states, current included, are accepted."""

    def test_the_window_is_the_last_k_roots(self):
        show = zk_show()
        shielded(show, 3)
        self.assertEqual(list(show.history()), [0, 1, 2, 3])  # the empty root is still inside
        shielded_more = show.issue('issuer', 3, 0, 'a')
        show.shield('a', shielded_more.id, 1, 'n3')
        self.assertEqual(list(show.history()), [1, 2, 3, 4])
        self.assertEqual(show.private_snapshot()['history_len'], model.LOCALNET_ROOT_HISTORY_K)

    def test_age_k_minus_one_passes_and_age_k_is_refused(self):
        show = zk_show()
        shielded(show, 5)
        self.assertEqual(list(show.history()), [2, 3, 4, 5])
        self.assertTrue(aborts(model.ERoot, show.consume_private, 'gate', proof(show, 'n0', note_count=1)))
        show.consume_private('gate', proof(show, 'n1', note_count=2))

    def test_a_root_that_was_never_a_root_is_refused(self):
        show = zk_show()
        shielded(show, 2)
        self.assertTrue(aborts(model.ERoot, show.consume_private, 'gate', proof(show, 'n0'), note_root=99))


class ConsumePrivate(unittest.TestCase):
    def setUp(self):
        self.show = zk_show()
        shielded(self.show, 3)

    def test_an_honest_proof_is_recorded_once(self):  # RS-C09
        p = proof(self.show, 'n0')
        self.show.consume_private('gate', p)
        self.assertEqual(self.show.private_snapshot()['nullifiers'], 1)
        self.assertTrue(aborts(model.EProof, self.show.consume_private, 'gate', p))
        self.show.check_invariants()

    def test_the_same_note_cannot_be_spent_with_a_new_challenge(self):
        self.show.consume_private('gate', proof(self.show, 'n0'))
        self.assertTrue(aborts(model.EProof, self.show.consume_private, 'gate',
                               proof(self.show, 'n0', challenge=('challenge', 'other'))))

    def test_one_challenge_cannot_be_used_with_two_nullifiers(self):  # RS-C17
        self.show.consume_private('gate', proof(self.show, 'n0', challenge=('challenge', 1)))
        self.assertTrue(aborts(model.EProof, self.show.consume_private, 'gate',
                               proof(self.show, 'n1', challenge=('challenge', 1))))

    def test_call_bindings_are_enforced_in_the_move_order(self):
        s, p = self.show, proof(self.show, 'n0')
        self.assertTrue(aborts(model.EAuthority, s.consume_private, 'a', p))
        self.assertTrue(aborts(model.EAuthority, s.consume_private, 'gate', p, verifier='v2'))
        self.assertTrue(aborts(model.EShard, s.consume_private, 'gate', p, wrong_shard='nullifier'))
        self.assertTrue(aborts(model.EShard, s.consume_private, 'gate', p, wrong_shard='challenge'))
        self.assertTrue(aborts(model.EPolicy, s.consume_private, 'gate', p, ttl_ms=-1))
        self.assertTrue(aborts(model.EPolicy, s.consume_private, 'gate', p, ttl_ms=model.MAX_ADMISSION_MS + 1))
        # In range but not the expiry the proof commits to: only the verifier can tell.
        self.assertTrue(aborts(model.EBadProof, s.consume_private, 'gate', p, ttl_ms=60000))
        self.assertTrue(aborts(model.EBadProof, s.consume_private, 'gate2', p))
        self.assertEqual(s.private_snapshot()['nullifiers'], 0)

    def test_a_proof_of_another_show_or_manifest_is_refused_by_the_verifier(self):  # RS-C11
        other = zk_show(show_id=b'\x00' * 31 + b'\x09')
        shielded(other, 3)
        foreign = proof(other, 'n0')
        self.assertTrue(aborts(model.EBadProof, self.show.consume_private, 'gate', foreign, note_root=3))
        self.assertTrue(aborts(model.EBadProof, self.show.consume_private, 'gate', dict(proof(self.show, 'n0'),
                                                                                       domain=(b'x', 1, 'm2'))))

    def test_a_cancelled_show_refuses_private_admission(self):
        p = proof(self.show, 'n0')
        self.show.cancel_show('issuer')
        self.assertTrue(aborts(model.EAuthority, self.show.consume_private, 'gate', p))


class RevocationRoot(unittest.TestCase):
    def setUp(self):
        self.show = zk_show()
        shielded(self.show, 3)
        self.public = self.show.issue('issuer', 5, 0, 'b')

    def test_issue_and_refund_do_not_move_the_revocation_root(self):  # RR-2
        before = self.show.revocations
        t = self.show.issue('issuer', 6, 0, 'b')
        self.show.refund('b', t.id, 1)
        self.show.issue('issuer', 6, 1, 'b')
        self.assertEqual(self.show.revocations, before)
        p = proof(self.show, 'n0')
        self.show.consume_private('gate', p)  # still valid after the issuance traffic

    def test_revoke_moves_it_and_a_proof_made_before_is_refused(self):  # RR-2, RR-3
        p = proof(self.show, 'n1')
        self.show.revoke_with_root('issuer', self.public.id)
        self.assertEqual(self.show.revocations, 1)
        self.assertTrue(aborts(model.EBadProof, self.show.consume_private, 'gate', p))
        self.show.consume_private('gate', proof(self.show, 'n1'))  # re-proved against the new root

    def test_the_revoked_generation_is_recorded_and_never_lowered(self):
        t = self.show.tickets['T1']
        self.show.revoke_with_root('issuer', t.id)
        self.assertEqual(self.show.revoked, {0: 1})
        self.assertTrue(aborts(model.ERoot, self.show.revoke_with_root, 'issuer', t.id))

    def test_plain_revoke_is_refused_and_a_stale_witness_loses_the_race(self):
        self.assertTrue(aborts(model.ERootRequired, self.show.revoke, 'issuer', self.public.id))
        self.show.revoke_with_root('issuer', self.public.id)
        other = self.show.issue('issuer', 7, 0, 'b')
        self.assertTrue(aborts(model.ERoot, self.show.revoke_with_root, 'issuer', other.id, stale_witness=True))
        self.show.revoke_with_root('issuer', other.id)
        self.assertEqual(self.show.private_snapshot()['revoked'], {'5': 1, '7': 1})

    def test_a_shielded_ticket_can_be_revoked_and_then_has_no_witness(self):
        note_ticket = self.show.tickets['T1']
        self.show.revoke_with_root('issuer', note_ticket.id)
        world = rp.World(VECTORS['scenarios'][2], VECTORS)
        world.shows['S1'] = self.show
        world.notes['n0'] = dict(show='S1', slot=0, generation=1, commitment='n0')
        with self.assertRaises(rp.ClientRefusal) as raised:
            rp.prove(world, {'label': 'x', 'note': 'n0'})
        self.assertEqual(raised.exception.code, 'PRIVATE_NOTE_REVOKED')

    def test_only_the_issuer_revokes(self):
        self.assertTrue(aborts(model.EAuthority, self.show.revoke_with_root, 'a', self.public.id))


class RevocationEquivalence(unittest.TestCase):
    """RR-2 equivalence lemma, checked on random operation sequences of the model.

    The reference profile accepts a note iff its generation equals the slot's CURRENT generation.
    The extended profile accepts it iff its generation exceeds the slot's recorded revoked
    generation. In this profile only `revoke` raises a slot's generation after a note exists
    (a SHIELDED slot cannot be refunded or reissued), so the two verdicts must always agree.
    """

    def test_both_rules_give_the_same_verdict_for_every_note_after_every_operation(self):
        import random
        for seed in range(40):
            rng = random.Random(seed)
            show = zk_show(seated=12, page_size=4)
            tickets, notes = [], {}
            for _ in range(80):
                action = rng.choice(['issue', 'issue', 'shield', 'refund', 'revoke', 'revoke_public'])
                try:
                    if action == 'issue':
                        slot = rng.randrange(12)
                        page = show.pages[slot // 4]
                        tickets.append(show.issue('issuer', slot, page.generations[slot % 4], 'a'))
                    elif tickets:
                        t = rng.choice(tickets)
                        if action == 'shield':
                            label = f'n{len(notes)}'
                            show.shield('a', t.id, t.version, label)
                            notes[label] = t
                        elif action == 'refund':
                            show.refund('a', t.id, t.version)
                        else:
                            show.revoke_with_root('issuer', t.id)
                except Abort:
                    pass
                for label, t in notes.items():
                    page = show.pages[t.slot // 4]
                    reference_rule = t.generation == page.generations[t.slot % 4]
                    extended_rule = t.generation > show.revoked.get(t.slot, 0)
                    self.assertEqual(reference_rule, extended_rule, (seed, label, t))
                show.check_invariants()

    def test_issuance_and_refund_alone_never_move_the_revocation_counter(self):
        import random
        for seed in range(20):
            rng = random.Random(1000 + seed)
            show = zk_show(seated=12, page_size=4)
            live = []
            for _ in range(60):
                try:
                    if live and rng.random() < 0.4:
                        t = live.pop(rng.randrange(len(live)))
                        show.refund('a', t.id, t.version)
                    else:
                        slot = rng.randrange(12)
                        live.append(show.issue('issuer', slot, show.pages[slot // 4].generations[slot % 4], 'a'))
                except Abort:
                    pass
                self.assertEqual((show.revocations, show.revoked), (0, {}))


class Privacy(unittest.TestCase):
    """RS-C13: the candidate set an observer is left with, from public data only."""

    def test_routing_inputs_hold_no_slot_or_section(self):
        # The Move routing function takes (show id, value bytes, profile version, shard count): no slot.
        signature = re.search(r'^fun route\(([^)]*)\)', MOVE, re.M).group(1)
        self.assertNotRegex(signature, r'slot|section|page')
        for name in ('check_nullifier_shard', 'check_challenge_shard'):
            body = MOVE[MOVE.index(f'fun {name}'):].split('\n}\n', 1)[0]
            self.assertIn('bcs::to_bytes(&', body)
            self.assertNotRegex(body.split('route(', 1)[1].split(';', 1)[0], r'slot|\.index_of|page')

    def test_candidate_sets_of_the_main_scenario(self):
        rows = rp.observer_candidates(VECTORS['scenarios'][0], VECTORS)
        self.assertTrue(all(r['candidates'] >= 1 for r in rows))
        # Early admissions leave a tiny set: the first accepted admission has 2 candidates, not 1024.
        self.assertEqual(rows[0]['candidates'], 2)
        self.assertLessEqual(max(r['candidates'] for r in rows), 8)
        # No admission is hidden among more notes than the show has shielded.
        self.assertTrue(all(r['candidates'] <= r['notesInTree'] for r in rows))


class Vectors(unittest.TestCase):
    def test_every_scenario_replays_with_its_scripted_outcomes_and_invariants(self):
        for scenario in VECTORS['scenarios']:
            with self.subTest(scenario['name']):
                world, outcomes = rp.run_scenario(scenario, VECTORS)
                self.assertEqual(len(outcomes), len(scenario['steps']))

    def test_the_main_scenario_ends_where_the_script_says(self):
        world, _ = rp.run_scenario(VECTORS['scenarios'][0], VECTORS)
        snap = world.shows['S1'].private_snapshot()
        self.assertEqual((snap['leaf_count'], snap['revocations'], snap['revoked']), (8, 2, {'7': 1, '8': 1}))

    def test_the_scripts_cover_the_private_predicates(self):
        text = (HERE / 'vectors' / 'private_path.json').read_text()
        for needle in ('"claim_zk"', '"shield"', '"prove"', '"consume_private"', '"revoke"', '"revoke_plain"',
                       '"reconstruct"', '"foreign_domain"', '"wrong_commitment"', '"wrong_shard"', '"zk_gate:2"',
                       '"PRIVATE_NOTE_REVOKED"', '"witness": "stale"', '"source": "events"'):
            self.assertIn(needle, text)

    def test_a_model_that_ignores_the_revocation_root_fails_the_scripts(self):
        """Mutation check: the revocation binding is what makes the RR-3 steps refuse."""
        original = Show.consume_private
        try:
            def lax(self, sender, proof_, **kw):
                return original(self, sender, dict(proof_, revocations=self.revocations), **kw)
            Show.consume_private = lax
            with self.assertRaises(AssertionError):
                rp.run_scenario(VECTORS['scenarios'][0], VECTORS)
        finally:
            Show.consume_private = original


if __name__ == '__main__':
    unittest.main()
