"""Unit tests for load_plan.py — the RS-4 L1 workload generator.

These check the generated workload document itself (determinism, capacity
bounds, phase/seq integrity, expectation sanity and the generator's own
end-state model). They run offline under `python3 -m unittest discover`
with no localnet, node or Move toolchain.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import load_plan  # noqa: E402

FILL_OPS = {'issue', 'bundle', 'issue_delegated', 'bundle_delegated'}


def _ops(doc, path, op=None):
    return [s for s in doc['paths'][path] if op is None or s['op'] == op]


class TestDeterminism(unittest.TestCase):
    def test_same_seed_same_doc(self):
        a = load_plan.assign_phases(load_plan.expand({'seed': 7}))
        b = load_plan.assign_phases(load_plan.expand({'seed': 7}))
        self.assertEqual(a, b)

    def test_different_seed_differs(self):
        a = load_plan.expand({'seed': 7})
        b = load_plan.expand({'seed': 8})
        self.assertNotEqual(a['paths']['public'], b['paths']['public'])

    def test_default_seed_stable(self):
        a = load_plan.expand()
        b = load_plan.expand()
        self.assertEqual(a, b)


class TestStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_plan.assign_phases(load_plan.expand())

    def test_three_paths_present(self):
        self.assertEqual(set(self.doc['paths']), {'public', 'private', 'delegated'})

    def test_seq_is_global_dense_order(self):
        seqs = [s['seq'] for path in self.doc['paths'].values() for s in path]
        self.assertEqual(seqs, list(range(len(seqs))))

    def test_every_step_phased_and_in_doc_order(self):
        declared = []
        for name, labels in self.doc['phases'].items():
            declared += labels
            seen = [s['phase'] for s in self.doc['paths'][name]]
            self.assertEqual(seen, sorted(seen, key=labels.index))
        for path in self.doc['paths'].values():
            for step in path:
                self.assertIn(step['phase'], declared)
                self.assertIn('expect', step)

    def test_capacity_respected(self):
        for name, path in self.doc['paths'].items():
            for step in path:
                slots = step.get('slots') or ([step['slot']] if 'slot' in step else [])
                for slot in slots:
                    self.assertGreaterEqual(slot, 0)
                    self.assertLess(slot, 1024, (name, step))

    def test_bundle_and_claim_bounds(self):
        for path in self.doc['paths'].values():
            for step in path:
                if 'bundle' in step['op']:
                    self.assertLessEqual(len(step['slots']), load_plan.MAX_BUNDLE)
                if step['op'] in ('claim_pages', 'claim_shards'):
                    self.assertLessEqual(step['count'], load_plan.MAX_CLAIM)

    def test_expected_pages_conserve(self):
        for name, expected in self.doc['expected'].items():
            total = 0
            for index, page in expected['pages'].items():
                size = min((index + 1) * load_plan.PAGE_SIZE, load_plan.SEATS) - index * load_plan.PAGE_SIZE
                self.assertEqual(page['free'] + page['reserved'] + page['issued']
                                 + page['retired'], size, (name, index))
                total += size
            self.assertEqual(total, load_plan.SEATS)


class TestSlotAccounting(unittest.TestCase):
    """Replays the generator's own step list against an occupancy model and
    confirms every expect-ok fill step lands on a slot that can take it."""

    @classmethod
    def setUpClass(cls):
        cls.doc = load_plan.assign_phases(load_plan.expand())

    def _check_path(self, name):
        state = ['free'] * load_plan.SEATS
        for step in self.doc['paths'][name]:
            expect = step['expect']
            for slot in step.get('slots') or ([] if 'slot' not in step else [step['slot']]):
                if step['op'] in FILL_OPS and expect == 'ok':
                    self.assertEqual(state[slot], 'free', (name, step))
                    state[slot] = 'issued'
            if step['op'] == 'parallel':
                for branch in step['of']:
                    if branch['op'] in FILL_OPS:
                        for slot in branch.get('slots') or [branch['slot']]:
                            self.assertIn(state[slot], ('free', 'issued'))
            if step['op'] == 'refund' and expect == 'ok':
                state[step['slot']] = 'free'
            if step['op'] == 'revoke' and expect == 'ok':
                state[step['slot']] = 'retired'
            if step['op'] in ('issue', 'issue_paid', 'issue_delegated') and expect == 'any':
                state[step['slot']] = 'issued'

    def test_public(self):
        self._check_path('public')

    def test_private(self):
        self._check_path('private')

    def test_delegated(self):
        self._check_path('delegated')

    def test_public_fill_covers_all_slots(self):
        # Before stage.ops, every one of the 1,024 slots is issued or retired.
        covered = set()
        for step in self.doc['paths']['public']:
            if step['phase'] == 'stage.ops':
                break
            for slot in step.get('slots') or ([] if 'slot' not in step else [step['slot']]):
                if step['op'] in FILL_OPS or step['op'] in ('issue_paid',):
                    covered.add(slot)
            if step['op'] == 'parallel':
                for branch in step['of']:
                    for slot in branch.get('slots') or [branch['slot']]:
                        covered.add(slot)
        self.assertEqual(len(covered), load_plan.SEATS)

    def test_expected_totals_match_emitted_ops(self):
        # The generator's expected page totals equal what the emitted expect-ok
        # steps produce when replayed on the same model.
        for name in ('public', 'delegated'):
            state = load_plan.Slots(load_plan.SEATS)
            for step in self.doc['paths'][name]:
                if step['op'] in FILL_OPS and step['expect'] == 'any':
                    for slot in step.get('slots') or [step['slot']]:
                        state.force_issued(slot)
                    continue
                if step['op'] in ('issue_paid', 'issue_paid_delegated',
                                  'revoke_with_root') and step['expect'] == 'any':
                    if state.state[step['slot']] != 'retired':
                        (state.force_issued if 'paid' in step['op'] else state.revoke)(step['slot'])
                    continue
                if step['expect'] != 'ok':
                    continue
                for slot in step.get('slots') or ([] if 'slot' not in step else [step['slot']]):
                    if step['op'] in FILL_OPS:
                        state.issue(slot, 'x')
                if step['op'] == 'attest_issuance':
                    state.reserve(step['slot'])
                if step['op'] == 'issue_paid':
                    state.complete(step['slot'], 'x')
                if step['op'] == 'attest_issuance_delegated':
                    state.reserve(step['slot'])
                if step['op'] == 'issue_paid_delegated':
                    state.complete(step['slot'], 'x')
                if step['op'] in ('refund', 'refund_delegated'):
                    state.refund(step['slot'])
                if step['op'] == 'cancel_issuance':
                    state.release(step['slot'])
                if step['op'] in ('revoke',):
                    state.revoke(step['slot'])
            for index, page in state.page_totals().items():
                self.assertEqual(self.doc['expected'][name]['pages'][index], page,
                                 (name, index))


class TestPrivatePath(unittest.TestCase):
    def test_shield_count_parameter(self):
        for count in (16, 64, 1024):
            doc = load_plan.expand({'shield_count': count})
            shields = _ops(doc, 'private', 'shield')
            self.assertEqual(len(shields), count)
            self.assertEqual(doc['expected']['private']['leaf_count'], count)
            self.assertEqual(doc['requested']['shield_count'], count)

    def test_shield_count_too_small_rejected(self):
        with self.assertRaises(ValueError):
            load_plan.expand({'shield_count': 4})

    def test_private_issue_covers_capacity(self):
        doc = load_plan.expand()
        bundled = set()
        for step in _ops(doc, 'private', 'bundle'):
            bundled.update(step['slots'])
        self.assertEqual(len(bundled), load_plan.SEATS)

    def test_invalidation_and_boundary_expects(self):
        doc = load_plan.expand()
        stale = [s for s in _ops(doc, 'private', 'consume_private')
                 if s.get('comment') == 'invalidated_by_revocation']
        self.assertEqual(len(stale), doc['settings']['invalidation_count'])
        for s in stale:
            self.assertEqual(s['expect'], {'abort': load_plan.ZK_GATE_REJECT})
        evicted = [s for s in _ops(doc, 'private', 'consume_private')
                   if s.get('comment') == 'root_evicted_after_k_writes']
        self.assertEqual(len(evicted), 1)
        self.assertEqual(evicted[0]['expect'], {'abort': load_plan.E_ROOT})

    def test_revoked_note_client_refusals(self):
        doc = load_plan.expand()
        refused = [s for s in _ops(doc, 'private', 'consume_private')
                   if isinstance(s['expect'], dict) and 'client' in s['expect']]
        self.assertEqual(len(refused), 2)


class TestDelegatedPath(unittest.TestCase):
    def test_cut_and_reclaim_sequence(self):
        doc = load_plan.expand()
        ops = [s['op'] for s in doc['paths']['delegated']]
        i_cut = ops.index('revoke_grant')
        i_undelegate = ops.index('undelegate_page')
        self.assertLess(i_cut, i_undelegate)
        closed = [s for s in doc['paths']['delegated']
                  if s.get('expect') == {'abort': load_plan.E_GRANT_CLOSED}]
        self.assertGreaterEqual(len(closed), 4)
        stranded = [s for s in doc['paths']['delegated']
                    if s.get('comment') == 'unreclaimable_reserved_page']
        self.assertEqual(len(stranded), 1)
        self.assertEqual(stranded[0]['expect'], {'abort': load_plan.E_DELEGATED})

    def test_expected_grant_states(self):
        doc = load_plan.expand()
        grants = doc['expected']['delegated']['grants']
        for g in grants.values():
            self.assertFalse(g['open'])
            self.assertEqual(g['generation'], 2)


if __name__ == '__main__':
    unittest.main()
