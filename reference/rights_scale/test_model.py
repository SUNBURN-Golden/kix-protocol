"""Unit tests of the RS-1 reference model and of its agreement with the Move package.

Run: python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale
"""
import hashlib
import random
import re
import struct
import unittest
from pathlib import Path

import model
import replay
from model import Abort, Show

HERE = Path(__file__).resolve().parent
MOVE = (HERE / 'sui' / 'sources' / 'rights_scale.move').read_text()
REF = lambda tag: bytes([tag]) * 32  # noqa: E731


def make(seated=8, ga=4, page_size=4, shards=2, claim=True, seal=True, **kw):
    show = Show('issuer', seated, ga, page_size, shards, gates=['gate'], payment_attesters=['attester'], **kw)
    if claim:
        show.claim_pages('issuer', 0, show.page_count)
        show.claim_shards('issuer', 0, show.shard_count)
    if seal:
        show.seal('issuer')
    return show


def aborts(code, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Abort as abort:
        return abort.code == code
    return False


class MoveParity(unittest.TestCase):
    """The model and the Move source must not drift apart."""

    def constant(self, name):
        return int(re.search(rf'^const {name}: u64 = (\d+);', MOVE, re.M).group(1))

    def test_constants_match_the_move_source(self):
        self.assertEqual(self.constant('PROFILE_VERSION'), model.PROFILE_VERSION)
        self.assertEqual(self.constant('MAX_BUNDLE_CHAIN'), model.MAX_BUNDLE_CHAIN)
        self.assertEqual(self.constant('LOCALNET_SHOW_SLOTS'), model.LOCALNET_SHOW_SLOTS)
        self.assertEqual(self.constant('LOCALNET_PAGE_SLOTS'), model.LOCALNET_PAGE_SLOTS)
        self.assertEqual(self.constant('LOCALNET_PAYMENT_SHARDS'), model.LOCALNET_PAYMENT_SHARDS)
        self.assertEqual((model.PROFILE_VERSION, model.MAX_BUNDLE_CHAIN, model.LOCALNET_SHOW_SLOTS,
                          model.LOCALNET_PAGE_SLOTS), (1, 8, 1024, 64))

    def test_localnet_constants_are_declared_together_and_labelled(self):
        block = MOVE[MOVE.index('// Localnet defaults; Astra-owned.'):MOVE.index('/// Key space of page claims.')]
        for name in ('PROFILE_VERSION', 'MAX_BUNDLE_CHAIN', 'LOCALNET_SHOW_SLOTS', 'LOCALNET_PAGE_SLOTS',
                     'LOCALNET_PAYMENT_SHARDS'):
            self.assertIn(f'const {name}: u64', block)

    def test_error_codes_match_the_move_source(self):
        for name in ('EClosed', 'ENotHolder', 'EStale', 'EAuthority', 'ELocked', 'EPolicy', 'EPayment', 'EInventory',
                     'EBundleTooLarge', 'EBundleIncomplete', 'EBundleMismatch', 'ESealed', 'ENotComplete', 'EPage',
                     'EShard', 'ERange', 'EDelegated', 'EGrantClosed'):
            self.assertEqual(self.constant(name), getattr(model, name), name)

    def test_routing_known_answers_match_the_move_test(self):
        show = b'\x00' * 31 + b'\xab'
        expected = {1: [0, 0, 2, 2, 18], 2: [0, 0, 0, 4, 20], 3: [0, 1, 3, 7, 31], 4: [0, 0, 0, 4, 44],
                    5: [0, 1, 1, 5, 37], 6: [0, 0, 2, 2, 50], 7: [0, 1, 3, 7, 39], 8: [0, 0, 0, 4, 44]}
        for tag, row in expected.items():
            self.assertEqual([model.route(show, REF(tag), 1, n) for n in (1, 2, 4, 8, 64)], row)
        self.assertEqual(model.route(show, REF(1), 2, 4), 0)
        # The Move tests hard-code the same numbers.
        move_test = (HERE / 'sui' / 'tests' / 'routing_tests.move').read_text()
        for needle in ('vector[2u64, 0, 3, 0, 1, 2, 3, 0]', 'vector[2u64, 4, 7, 4, 5, 2, 7, 4]',
                       'vector[18u64, 20, 31, 44, 37, 50, 39, 44]', 'vector[0u64, 0, 1, 0, 1, 0, 1, 0]'):
            self.assertIn(needle, move_test)

    def test_routing_hash_is_blake2b_256_of_show_ref_and_version(self):
        show = bytes(range(32))
        digest = hashlib.blake2b(show + REF(9) + struct.pack('<Q', 1), digest_size=32).digest()
        self.assertEqual(model.route(show, REF(9), 1, 7), int.from_bytes(digest[:8], 'little') % 7)

    def public_functions(self):
        out = []
        pending_test_only = False
        for line in MOVE.splitlines():
            if line.startswith('#[test_only]'):
                pending_test_only = True
                continue
            m = re.match(r'(public )?(entry )?fun (\w+)', line)
            if m:
                if m.group(1) and not pending_test_only:
                    out.append(m.group(3))
                pending_test_only = False
        return out

    OPERATIONS = ['create_show_control', 'claim_pages', 'claim_shards', 'seal', 'cancel_show', 'issue',
                  'attest_issuance', 'cancel_issuance', 'issue_paid', 'begin_bundle', 'bundle_issue',
                  'finish_bundle', 'offer', 'accept_gift', 'attest_payment', 'accept_sale', 'authorize_admission',
                  'consume', 'refund', 'revoke',
                  # RS-2: the private path (section 3 shield / consume_private, and revoke with a root).
                  'claim_zk', 'revoke_with_root', 'shield', 'consume_private',
                  # RS-3a: grant lifecycle and the delegated inventory paths.
                  'create_grant', 'revoke_grant', 'delegate_page', 'undelegate_page',
                  'issue_delegated', 'bundle_issue_delegated', 'attest_issuance_delegated',
                  'issue_paid_delegated', 'cancel_issuance_delegated', 'refund_delegated']

    def test_the_package_surface_is_exactly_the_section_3_operations_plus_read_only_views(self):
        names = self.public_functions()
        operations = [n for n in names if n in self.OPERATIONS]
        self.assertEqual(sorted(operations), sorted(self.OPERATIONS))
        views = [n for n in names if n not in self.OPERATIONS]
        for name in views:
            self.assertRegex(name, r'^(profile_version|max_bundle_chain|localnet_\w+|control_\w+|page_\w+|shard_\w+|'
                                   r'route_index|payment_\w+|holder|version|state|slot|generation|last_\w+|'
                                   r'zk_depth|shielded_state|domain_of|tree_\w+|root_in_history|revocation_\w+|'
                                   r'nullifier_\w+|challenge_\w+|grant_\w+)$', name)
        # No view mutates: read-only views never take a mutable reference or a TxContext.
        for m in re.finditer(r'^public fun (\w+)\(([^)]*)\)', MOVE, re.M):
            if m.group(1) in views:
                self.assertNotIn('&mut', m.group(2), m.group(1))
                self.assertNotIn('TxContext', m.group(2), m.group(1))

    def test_no_ga_redistribution_entry_exists_in_the_package(self):
        # RS-C02 sentence 2 (moving two pages in one PTB) is DECISION_REQUIRED for Astra.
        names = self.public_functions()
        for name in names:
            self.assertIsNone(re.search(r'redistribut|rebalanc|move_range|move_page|transfer_page|migrate|merge_page|split_page',
                                        name), name)
        # The range table is immutable after creation: nothing writes these fields outside creation.
        for field in ('page_size', 'seated_capacity', 'ga_capacity', 'seated_pages', 'page_count', 'shard_count',
                      'verifier', 'issuer', 'profile_version'):
            writes = re.findall(rf'\bc\.{field} = ', MOVE)
            self.assertEqual(writes, [], field)

    def test_the_package_defines_no_coin_or_token_module(self):
        # RS-1 also asserted "no proof path" here; RS-2 adds that path (poseidon, zk_gate), so only the
        # economic-asset exclusion remains. test_private_model.py pins the private surface.
        for needle in ('coin::', 'balance::', 'TreasuryCap', 'sui::token'):
            self.assertNotIn(needle, MOVE)
        self.assertEqual(len(re.findall(r'^module ', MOVE, re.M)), 1)

    def test_the_issuer_cap_has_no_transfer_or_burn_function(self):
        self.assertRegex(MOVE, r'public struct IssuerCap has key \{ id: UID \}')
        # The declaration plus the one mint in init; no other construction or hand-out.
        self.assertEqual(len(re.findall(r'IssuerCap(?: has key)? \{', MOVE)), 2)
        self.assertNotRegex(MOVE, r'public_transfer\(|transfer::freeze\(|object::delete\(\s*cap')


class RangeTable(unittest.TestCase):
    def test_capacities_15_16_17_are_accepted(self):
        for n in (15, 16, 17):
            show = make(seated=n, ga=0, page_size=4)
            show.issue('issuer', n - 1, 0, 'a')
            self.assertTrue(aborts(model.EInventory, show.issue, 'issuer', n, 0, 'a'))
            show.check_invariants()

    def test_capacities_1023_1024_1025_are_accepted(self):
        for n in (1023, 1024, 1025):
            for p in (64, 256, 1024):
                show = make(seated=n, ga=0, page_size=p, shards=2)
                show.issue('issuer', n - 1, 0, 'a')
                self.assertTrue(aborts(model.EInventory, show.issue, 'issuer', n, 0, 'a'))
                self.assertEqual(show.capacity, n)
                self.assertEqual(sum(pg.end - pg.start for pg in show.pages.values()), n)

    def test_pages_are_contiguous_disjoint_and_never_straddle_the_ga_boundary(self):
        for seated, ga, p in ((10, 6, 4), (0, 8, 4), (3, 0, 1024), (17, 5, 5), (64, 64, 64)):
            show = make(seated=seated, ga=ga, page_size=p, shards=1)
            expected = 0
            for index in range(show.page_count):
                pg = show.pages[index]
                self.assertEqual(pg.start, expected)
                self.assertTrue(pg.start >= seated or pg.end <= seated)
                self.assertEqual(pg.mode, model.GA if pg.start >= seated else model.SEATED)
                self.assertEqual(show.page_index_of(pg.start), index)
                self.assertEqual(show.page_index_of(pg.end - 1), index)
                expected = pg.end
            self.assertEqual(expected, seated + ga)

    def test_create_policy_checks(self):
        for kwargs in (dict(page_size=0), dict(shard_count=0), dict(seated_capacity=0, ga_capacity=0),
                       dict(gates=[]), dict(organizer_bps=9000, platform_bps=1001), dict(organizer_bps=10001)):
            args = dict(issuer='issuer', seated_capacity=8, ga_capacity=0, page_size=4, shard_count=1,
                        gates=['gate'], payment_attesters=['attester'])
            args.update(kwargs)
            self.assertTrue(aborts(model.EPolicy, Show, **args), kwargs)


class Creation(unittest.TestCase):
    def test_nothing_can_be_consumed_before_seal(self):
        show = make(claim=True, seal=False)
        self.assertTrue(aborts(model.EClosed, show.issue, 'issuer', 0, 0, 'a'))
        self.assertFalse(show.open)

    def test_second_claim_of_a_page_aborts_and_keeps_one_authority(self):
        show = make(claim=False, seal=False)
        show.claim_pages('issuer', 0, 2)
        before = show.snapshot()
        self.assertTrue(aborts(model.EObjectAlreadyExists, show.claim_pages, 'issuer', 1, 2))
        self.assertEqual(show.snapshot(), before)
        show.claim_pages('issuer', 2, show.page_count - 2)
        self.assertEqual(show.claimed_pages, show.page_count)

    def test_seal_needs_every_page_and_shard_and_closes_claiming(self):
        show = make(claim=False, seal=False)
        show.claim_pages('issuer', 0, show.page_count)
        self.assertTrue(aborts(model.ENotComplete, show.seal, 'issuer'))
        show.claim_shards('issuer', 0, show.shard_count)
        show.seal('issuer')
        self.assertTrue(aborts(model.ESealed, show.seal, 'issuer'))
        self.assertTrue(aborts(model.ESealed, show.claim_pages, 'issuer', 0, 1))
        self.assertTrue(aborts(model.ESealed, show.claim_shards, 'issuer', 0, 1))

    def test_claim_range_and_authority(self):
        show = make(claim=False, seal=False)
        self.assertTrue(aborts(model.ERange, show.claim_pages, 'issuer', show.page_count - 1, 2))
        self.assertTrue(aborts(model.ERange, show.claim_shards, 'issuer', 0, 0))
        self.assertTrue(aborts(model.EAuthority, show.claim_pages, 'attester', 0, 1))

    def test_claim_sequence_orders_claims_by_page_index_then_sequence(self):
        # Owner decision: sort key (page_index asc, claim_sequence asc).
        show = make(seated=16, ga=4, page_size=4, claim=False, seal=False)
        show.claim_pages('issuer', 3, 2)
        show.claim_pages('issuer', 0, 3)
        events = [e for e in show.events if e[0] == 'PageClaimed']
        ordered = sorted(events, key=lambda e: (e[1], e[2]))
        self.assertEqual([e[1] for e in ordered], [0, 1, 2, 3, 4])
        self.assertEqual(sorted(e[2] for e in events), [1, 2, 3, 4, 5])


class Predicates(unittest.TestCase):
    def test_c01_one_winner_per_slot_and_independent_authorities_at_a_boundary(self):
        show = make()
        show.attest_issuance('attester', 2, 0, 'a', 5, REF(1))
        self.assertTrue(aborts(model.EInventory, show.attest_issuance, 'attester', 2, 0, 'b', 5, REF(2)))
        show.attest_issuance('attester', 3, 0, 'a', 5, REF(3))
        show.attest_issuance('attester', 4, 0, 'b', 5, REF(4))   # the other side of the 3|4 page boundary
        self.assertEqual(show.pages[0].reserved, 2)
        self.assertEqual(show.pages[1].reserved, 1)
        show.issue('issuer', 5, 0, 'a')
        self.assertTrue(aborts(model.EStale, show.attest_issuance, 'attester', 5, 0, 'b', 5, REF(5)))

    def test_c02_conservation_through_every_transition(self):
        for slot in (0, 8):   # a seated page and a GA page
            show = make()
            t = show.issue('issuer', slot, 0, 'a')
            show.refund('a', t.id, 1)
            show.attest_issuance('attester', slot, 1, 'b', 5, REF(10))
            show.cancel_issuance('issuer', slot)
            show.attest_issuance('attester', slot, 1, 'b', 5, REF(11))
            p = show.issue_paid('issuer', slot)
            show.refund('b', p.id, 1)
            r = show.issue('issuer', slot, 2, 'a')
            show.revoke('issuer', r.id)
            show.check_invariants()
            self.assertEqual(show.totals()[3], 1)
            for i in range(6):
                t = show.issue('issuer', slot ^ 1, i, 'a')
                show.refund('a', t.id, 1)
            page = show.pages[show.page_index_of(slot)]
            self.assertGreater(page.issuances, page.end - page.start)
            self.assertTrue(page.conserved())

    def test_c03a_same_command_twice_and_after_refund(self):
        show = make()
        t = show.issue('issuer', 0, 0, 'a')
        self.assertTrue(aborts(model.EStale, show.issue, 'issuer', 0, 0, 'a'))
        show.refund('a', t.id, 1)
        self.assertTrue(aborts(model.EStale, show.issue, 'issuer', 0, 0, 'a'))
        self.assertEqual(show.totals()[2], 0)
        show.issue('issuer', 0, 1, 'a')
        self.assertEqual(show.pages[0].generations[0], 2)

    def test_c04_overlapping_bundles_leave_no_partial_state(self):
        show = make(seated=12, ga=4)
        show.bundle('issuer', 1, 2, 2, 'a')
        before = show.snapshot()
        self.assertTrue(aborts(model.EStale, show.bundle, 'issuer', 2, 2, 2, 'b'))
        self.assertEqual(show.snapshot(), before)
        self.assertFalse(show.pages[0].occupied[3])

    def test_c05_limit_minus_one_limit_limit_plus_one(self):
        for n, outcome in ((model.MAX_BUNDLE_CHAIN - 1, None), (model.MAX_BUNDLE_CHAIN, None),
                           (model.MAX_BUNDLE_CHAIN + 1, model.EBundleTooLarge)):
            show = make(seated=16, ga=0)
            if outcome:
                self.assertTrue(aborts(outcome, show.bundle, 'issuer', 0, n, n, 'a'))
                self.assertEqual(show.totals()[2], 0)
            else:
                self.assertEqual(len(show.bundle('issuer', 0, n, n, 'a')), n)
        show = make(seated=16, ga=0)
        self.assertTrue(aborts(model.EBundleIncomplete, show.bundle, 'issuer', 0, 3, 2, 'a'))
        self.assertTrue(aborts(model.EBundleMismatch, show.bundle, 'issuer', 0, 2, 3, 'a'))
        self.assertTrue(aborts(model.EPolicy, show.bundle, 'issuer', 0, 0, 0, 'a'))
        self.assertEqual(show.totals()[2], 0)

    def test_c05_the_bundle_limit_is_not_the_kernel_seat_bundle(self):
        # The locked kernel's MAX_BUNDLE is 64 for seats; this constant is a different limit.
        self.assertNotEqual(model.MAX_BUNDLE_CHAIN, 64)
        kernel = Path(__file__).resolve().parents[2] / 'runtime/crates/kix-kernel/src/lib.rs'
        self.assertRegex(kernel.read_text(), r'MAX_BUNDLE[^=\n]*=\s*64')

    def test_c06a_c07a_after_cancel(self):
        show = make()
        t0 = show.issue('issuer', 0, 0, 'a')
        t1 = show.issue('issuer', 1, 0, 'a')
        show.authorize_admission('a', t0.id, 1, 'gate', REF(1), 1000)
        show.offer('a', t1.id, 1, 'b', 0, 1000)
        show.attest_issuance('attester', 4, 0, 'b', 5, REF(9))
        show.cancel_show('issuer')
        for fn, args in ((show.issue, ('issuer', 5, 0, 'a')), (show.attest_issuance, ('attester', 5, 0, 'a', 5, REF(2))),
                         (show.offer, ('a', t1.id, 1, 'b', 0, 1000)), (show.accept_gift, ('b', t1.id)),
                         (show.authorize_admission, ('a', t1.id, 1, 'gate', REF(1), 1000)),
                         (show.consume, ('gate', t0.id, 1, REF(1))), (show.refund, ('a', t1.id, 1)),
                         (show.issue_paid, ('issuer', 4)), (show.bundle, ('issuer', 6, 2, 2, 'a'))):
            self.assertTrue(aborts(model.EClosed, fn, *args), fn.__name__)
        self.assertTrue(aborts(model.EClosed, show.cancel_show, 'issuer'))
        show.cancel_issuance('issuer', 4)       # a reservation can always be dropped
        show.revoke('issuer', t1.id)            # reference behaviour: revoke is not a consumption
        show.check_invariants()
        self.assertEqual(show.cancel_generation, 1)
        self.assertEqual(show.page_count, 3)

    def test_c06a_an_unsealed_show_cannot_be_cancelled(self):
        show = make(claim=True, seal=False)
        self.assertTrue(aborts(model.EClosed, show.cancel_show, 'issuer'))

    def test_c08_reissue_voids_the_old_ticket(self):
        show = make()
        old = show.issue('issuer', 0, 0, 'a')
        show.refund('a', old.id, 1)
        new = show.issue('issuer', 0, 1, 'b')
        self.assertTrue(aborts(model.EClosed, show.offer, 'a', old.id, 2, 'b', 0, 1000))
        self.assertEqual((old.state, new.state, new.generation), (model.VOID, model.ACTIVE, 2))

    def test_c15_pages_equal_the_table_after_retried_creation(self):
        show = make(claim=False, seal=False, seated=1024, ga=0, page_size=64)
        for start, count in ((0, 8), (4, 8), (8, 8), (0, 1)):
            try:
                show.claim_pages('issuer', start, count)
            except Abort as abort:
                self.assertEqual(abort.code, model.EObjectAlreadyExists)
        show.claim_shards('issuer', 0, show.shard_count)
        show.seal('issuer')
        self.assertEqual(len(show.pages), 16)
        self.assertEqual(show.claimed_pages, 16)

    def test_c16_wrong_page_is_rejected_everywhere(self):
        show = make()
        t = show.issue('issuer', 0, 0, 'a')
        self.assertTrue(aborts(model.EPage, show.issue, 'issuer', 1, 0, 'a', page_index=1))
        self.assertTrue(aborts(model.EPage, show.offer, 'a', t.id, 1, 'b', 0, 1000, page_index=1))
        self.assertTrue(aborts(model.EPage, show.refund, 'a', t.id, 1, page_index=2))
        self.assertTrue(aborts(model.EShard, show.attest_issuance, 'attester', 2, 0, 'a', 5, REF(1),
                               shard_index=1 - show.routed(REF(1))))

    def test_revoke_retires_the_slot_and_does_not_reopen_it(self):
        show = make()
        t = show.issue('issuer', 0, 0, 'a')
        show.revoke('issuer', t.id)
        self.assertEqual(show.totals(), (11, 0, 0, 1))
        self.assertTrue(aborts(model.EInventory, show.issue, 'issuer', 0, 2, 'b'))
        self.assertTrue(aborts(model.EStale, show.revoke, 'issuer', t.id))
        self.assertTrue(aborts(model.EClosed, show.refund, 'a', t.id, 2))

    def test_payment_reference_is_unique_show_wide_whatever_the_shard_count(self):
        for shards in (1, 2, 4, 8):
            show = make(shards=shards)
            show.attest_issuance('attester', 0, 0, 'a', 5, REF(3))
            self.assertTrue(aborts(model.EPayment, show.attest_issuance, 'attester', 1, 0, 'b', 5, REF(3)))
            t = show.issue('issuer', 2, 0, 'a')
            show.offer('a', t.id, 1, 'b', 100, 1000)
            self.assertTrue(aborts(model.EPayment, show.attest_payment, 'attester', t.id, REF(3)))
            show.check_invariants()

    def test_resale_moves_the_right_and_emits_the_allocation(self):
        show = make()
        t = show.issue('issuer', 0, 0, 'a')
        show.offer('a', t.id, 1, 'b', 100000, 1000)
        show.attest_payment('attester', t.id, REF(5))
        show.accept_sale('b', t.id)
        self.assertEqual((t.holder, t.version, t.last_amount), ('b', 2, 100000))
        allocation = [e for e in show.events if e[0] == 'Allocation'][0]
        self.assertEqual(allocation[3:], (100000, 95000, 2000, 3000))

    def test_each_issue_emits_two_events(self):
        show = make()
        before = len(show.events)
        show.bundle('issuer', 0, 3, 3, 'a')
        self.assertEqual(len(show.events) - before, 6)

    def test_the_issuance_event_carries_the_slot_and_the_generation(self):
        # IM-04 and IM-29: the Issuance event keeps its slot and generation
        # fields, and the Change event still accompanies each issue.
        show = make()
        first = show.issue('issuer', 2, 0, 'a')
        issuances = [e for e in show.events if e[0] == 'Issuance']
        self.assertEqual(issuances[-1][:4], ('Issuance', first.id, 2, 1))
        show.refund('a', first.id, 1)
        second = show.issue('issuer', 2, 1, 'b')
        issuances = [e for e in show.events if e[0] == 'Issuance']
        self.assertEqual(issuances[-1][:4], ('Issuance', second.id, 2, 2))
        self.assertEqual(second.generation, show.pages[0].generations[2])
        for index, event in enumerate(show.events):
            if event[0] == 'Issuance':
                self.assertEqual(show.events[index + 1][0], 'Change')

    def test_offer_accept_gift_authorize_admission_and_consume_write_only_the_ticket(self):
        # IM-03: the transfer, the check-in permit and the public check-in
        # write only the Ticket — ShowControl, the pages, the shards and the
        # grants are left unwritten.
        show = make()
        t = show.issue('issuer', 0, 0, 'a')
        untouchables = lambda: {k: show.snapshot()[k]  # noqa: E731
                                for k in ('control', 'pages', 'shards', 'grants')}
        before = untouchables()
        show.offer('a', t.id, 1, 'b', 0, 1000)
        self.assertEqual(untouchables(), before)
        show.accept_gift('b', t.id)
        self.assertEqual(untouchables(), before)
        self.assertEqual((t.holder, t.version), ('b', 2))
        show.authorize_admission('b', t.id, 2, 'gate', REF(3), 1000)
        self.assertEqual(untouchables(), before)
        show.consume('gate', t.id, 2, REF(3))
        self.assertEqual(untouchables(), before)
        self.assertEqual(t.state, model.CONSUMED)


class Delegation(unittest.TestCase):
    """RS-3a: page-level grants, GrantControl currentness and the revocation cut."""

    def test_delegation_lifecycle(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        self.assertEqual((g.delegate, g.generation, g.open), ('dele', 1, True))
        show.delegate_page('issuer', 0, g)
        self.assertEqual(show.pages[0].delegated_to, g.id)
        t = show.issue_delegated('dele', 0, 0, 'a', g)
        self.assertEqual((t.holder, t.generation), ('a', 1))
        show.check_invariants()

    def test_only_the_delegate_and_the_grant_issuer(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        self.assertTrue(aborts(model.EAuthority, show.create_grant, 'b', 'dele2'))
        self.assertTrue(aborts(model.EAuthority, show.revoke_grant, 'b', g))
        show.delegate_page('issuer', 0, g)
        self.assertTrue(aborts(model.EAuthority, show.issue_delegated, 'b', 0, 0, 'a', g))
        self.assertTrue(aborts(model.EAuthority, show.attest_issuance_delegated, 'attester', 1, 0, 'b', 5,
                               REF(60), g))

    def test_delegated_page_refuses_the_direct_paths(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        for fn, args in ((show.issue, ('issuer', 0, 0, 'a')),
                         (show.attest_issuance, ('attester', 0, 0, 'b', 5, REF(60))),
                         (show.bundle, ('issuer', 0, 2, 2, 'a'))):
            self.assertTrue(aborts(model.EDelegated, fn, *args), fn.__name__)
        t = show.issue_delegated('dele', 0, 0, 'a', g)
        self.assertTrue(aborts(model.EDelegated, show.refund, 'a', t.id, 1))
        show.check_invariants()

    def test_wrong_grant_wrong_page_and_double_delegation(self):
        show = make()
        g0 = show.create_grant('issuer', 'dele')
        g1 = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g0)
        self.assertTrue(aborts(model.EDelegated, show.issue_delegated, 'dele', 0, 0, 'a', g1))
        self.assertTrue(aborts(model.EDelegated, show.issue_delegated, 'dele', 4, 0, 'a', g0))
        self.assertTrue(aborts(model.EDelegated, show.delegate_page, 'issuer', 0, g1))
        other = make(show_id=b'\xff' * 32)  # a different show: every on-chain object id is unique
        foreign = other.create_grant('issuer', 'dele')
        self.assertTrue(aborts(model.EShard, show.delegate_page, 'issuer', 1, foreign))

    def test_an_open_reservation_blocks_delegation(self):
        show = make()
        show.attest_issuance('attester', 0, 0, 'b', 5, REF(60))
        g = show.create_grant('issuer', 'dele')
        self.assertTrue(aborts(model.EDelegated, show.delegate_page, 'issuer', 0, g))
        show.cancel_issuance('issuer', 0)
        show.delegate_page('issuer', 0, g)

    def test_the_cut_blocks_every_delegated_path_and_delegation(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        t = show.issue_delegated('dele', 0, 0, 'a', g)
        show.attest_issuance_delegated('dele', 1, 0, 'b', 5, REF(60), g)
        show.revoke_grant('issuer', g)
        self.assertEqual((g.open, g.generation), (False, 2))
        for fn, args in ((show.issue_delegated, ('dele', 2, 0, 'a', g)),
                         (show.attest_issuance_delegated, ('dele', 2, 0, 'b', 5, REF(61), g)),
                         (show.issue_paid_delegated, ('dele', 1, g)),
                         (show.cancel_issuance_delegated, ('dele', 1, g)),
                         (show.refund_delegated, ('a', t.id, 1, g)),
                         (show.delegate_page, ('issuer', 1, g)),
                         (show.revoke_grant, ('issuer', g))):
            self.assertTrue(aborts(model.EGrantClosed, fn, *args), fn.__name__)
        # The stranded reservation blocks the reclaim.
        self.assertTrue(aborts(model.EDelegated, show.undelegate_page, 'issuer', 0, g))
        show.check_invariants()

    def test_the_cut_orders_a_delegated_consume_and_paid_issue_both_ways(self):
        # RS-C06(b) and RS-C07: the grant cut against a delegated consume and
        # against a paid issue resolves as the serial order, in both
        # directions, and the unissued commitment survives the cut.
        #
        # Consume first, cut second: what committed pre-cut stands, the
        # stranded paid issue is preserved, and every consume under the old
        # grant is refused from the cut on.
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        t = show.issue_delegated('dele', 0, 0, 'a', g)
        show.attest_issuance_delegated('dele', 1, 0, 'b', 5, REF(60), g)
        paid = show.issue_paid_delegated('dele', 1, g)
        show.attest_issuance_delegated('dele', 2, 0, 'c', 5, REF(61), g)
        show.revoke_grant('issuer', g)
        self.assertEqual((t.state, paid.state), (model.ACTIVE, model.ACTIVE))
        self.assertIn(2, show.payments)
        self.assertEqual(show.payments[2].holder, 'dele')
        for fn, args in ((show.refund_delegated, ('a', t.id, 1, g)),
                         (show.issue_paid_delegated, ('dele', 2, g)),
                         (show.cancel_issuance_delegated, ('dele', 2, g)),
                         (show.issue_delegated, ('dele', 3, 0, 'a', g)),
                         (show.attest_issuance_delegated,
                          ('dele', 3, 0, 'c', 5, REF(62), g))):
            self.assertTrue(aborts(model.EGrantClosed, fn, *args), fn.__name__)
        # The stranded reservation still blocks the reclaim.
        self.assertTrue(aborts(model.EDelegated, show.undelegate_page, 'issuer', 0, g))
        show.check_invariants()

        # Cut first, consume second: the same calls in the other order are
        # refused the same way and leave nothing behind; with nothing
        # stranded the page reclaims cleanly.
        show = make()
        other = show.issue('issuer', 4, 0, 'a')  # a ticket outside the delegated page
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        show.revoke_grant('issuer', g)
        for fn, args in ((show.attest_issuance_delegated,
                          ('dele', 1, 0, 'b', 5, REF(60), g)),
                         (show.issue_paid_delegated, ('dele', 1, g)),
                         (show.cancel_issuance_delegated, ('dele', 1, g)),
                         (show.issue_delegated, ('dele', 1, 0, 'a', g)),
                         (show.refund_delegated, ('a', other.id, 1, g))):
            self.assertTrue(aborts(model.EGrantClosed, fn, *args), fn.__name__)
        self.assertEqual(show.payments, {})
        show.undelegate_page('issuer', 0, g)
        show.check_invariants()

    def test_undelegate_restores_the_direct_path(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        t = show.issue_delegated('dele', 0, 0, 'a', g)
        show.revoke_grant('issuer', g)
        show.undelegate_page('issuer', 0, g)
        self.assertIsNone(show.pages[0].delegated_to)
        show.refund('a', t.id, 1)          # pre-cut ticket releases on the direct path
        show.issue('issuer', 0, 1, 'a')    # and the issuer resumes
        show.check_invariants()

    def test_undelegate_requires_the_grant_closed_first(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        self.assertTrue(aborts(model.EGrantClosed, show.undelegate_page, 'issuer', 0, g))

    def test_delegated_paid_flow_and_cancel(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        show.attest_issuance_delegated('dele', 0, 0, 'b', 5, REF(60), g)
        self.assertEqual(show.payments[0].holder, 'dele')
        t = show.issue_paid_delegated('dele', 0, g)
        self.assertEqual(t.holder, 'b')
        show.attest_issuance_delegated('dele', 1, 0, 'b', 5, REF(61), g)
        show.cancel_issuance_delegated('dele', 1, g)
        show.check_invariants()
        self.assertEqual(show.totals()[0], 12 - 1)

    def test_cancel_show_does_not_revoke_a_grant(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        show.cancel_show('issuer')
        self.assertTrue(g.open)
        self.assertTrue(aborts(model.EClosed, show.issue_delegated, 'dele', 0, 0, 'a', g))

    def test_revoke_still_works_on_a_delegated_page(self):
        show = make()
        g = show.create_grant('issuer', 'dele')
        show.delegate_page('issuer', 0, g)
        t = show.issue_delegated('dele', 0, 0, 'a', g)
        show.revoke('issuer', t.id)
        self.assertEqual(show.totals(), (11, 0, 0, 1))
        show.check_invariants()


class Scripts(unittest.TestCase):
    """The scripts the localnet driver replays, run against the model."""

    def test_scripted_scenarios_end_in_a_consistent_state(self):
        doc = replay.load()
        for scenario in doc['scenarios']:
            show, labels, outcomes = replay.run_scenario(scenario)
            self.assertGreaterEqual(len([o for o in outcomes if o != 'ok']), 3)
            show.check_invariants()
        l1 = replay.run_scenario(doc['scenarios'][0])[0]
        self.assertEqual(l1.capacity, 1024)
        self.assertEqual(l1.page_count, 16)
        self.assertEqual(l1.cancel_generation, 1)

    def test_matrix_cases(self):
        doc = replay.load()
        self.assertEqual(sorted({c['seated'] for c in doc['matrix']['cases']}),
                         [15, 16, 17, 1023, 1024, 1025])
        for case in doc['matrix']['cases']:
            scenario = replay.matrix_scenario(case)
            show, _, outcomes = replay.run_scenario(scenario)
            self.assertEqual(outcomes[-1], {'abort': model.EInventory})
            self.assertEqual(show.totals()[2], len(scenario['edges']))

    def test_every_scripted_abort_code_is_one_the_model_can_raise(self):
        doc = replay.load()
        known = {v for k, v in vars(model).items() if re.fullmatch(r'E[A-Za-z]+', k)}
        for scenario in doc['scenarios']:
            for step in scenario['steps']:
                if 'expect' in step:
                    self.assertIn(step['expect']['abort'], known)


class Fuzz(unittest.TestCase):
    """Seeded random operation sequences keep every structural invariant (RS-C01, C02)."""

    def test_random_sequences_conserve_and_never_double_occupy(self):
        for seed in range(8):
            rng = random.Random(seed)
            show = make(seated=20, ga=8, page_size=4, shards=3)
            tickets, ref_tag = [], 0
            for _ in range(600):
                op = rng.choice(['issue', 'bundle', 'attest', 'pay', 'cancel', 'refund', 'revoke', 'offer',
                                 'gift', 'cancel_show'])
                slot = rng.randrange(show.capacity + 1)
                gen_pool = [0, 0, 1, 2, 3]
                if slot < show.capacity:
                    pg = show.pages.get(show.page_index_of(slot))
                    if pg is not None:
                        gen_pool.append(pg.generations[slot - pg.start])
                gen = rng.choice(gen_pool)
                try:
                    if op == 'issue':
                        tickets.append(show.issue('issuer', slot, gen, 'a').id)
                    elif op == 'bundle':
                        n = rng.randrange(0, model.MAX_BUNDLE_CHAIN + 2)
                        tickets += [t.id for t in show.bundle('issuer', slot, n, n, 'a')]
                    elif op == 'attest':
                        ref_tag += 1
                        show.attest_issuance('attester', slot, gen, 'b', 5, REF(ref_tag % 250 + 1))
                    elif op == 'pay' and show.payments:
                        tickets.append(show.issue_paid('issuer', rng.choice(sorted(show.payments))).id)
                    elif op == 'cancel' and show.payments:
                        show.cancel_issuance('issuer', rng.choice(sorted(show.payments)))
                    elif op == 'refund' and tickets:
                        t = show.tickets[rng.choice(tickets)]
                        show.refund(t.holder, t.id, t.version)
                    elif op == 'revoke' and tickets:
                        show.revoke('issuer', rng.choice(tickets))
                    elif op == 'offer' and tickets:
                        t = show.tickets[rng.choice(tickets)]
                        show.offer(t.holder, t.id, t.version, 'c' if t.holder != 'c' else 'a', 0, 1000)
                    elif op == 'gift' and tickets:
                        t = show.tickets[rng.choice(tickets)]
                        if t.offer:
                            show.accept_gift(t.offer['recipient'], t.id)
                    elif op == 'cancel_show' and rng.random() < 0.02 \
                            and sum(p.issuances for p in show.pages.values()) >= 20:
                        show.cancel_show('issuer')
                except Abort:
                    pass
                show.check_invariants()
            self.assertGreater(sum(p.issuances for p in show.pages.values()), 5)


if __name__ == '__main__':
    unittest.main()
