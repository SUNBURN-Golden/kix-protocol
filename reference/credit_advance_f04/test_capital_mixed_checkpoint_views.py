"""Replay exact checkpoint pairs from the pinned terminal-capacity history."""

import copy
import hashlib
import unittest

from credit_fixture import decode_json, exact_fields
from shared_exposure import SharedExposureError, canonical, observe_shared_exposure
from test_capital_companion_evidence_index import FIXTURES, _read, _resolve


PACK = FIXTURES + 'capital_mixed_checkpoint_views_vectors_v1.json'
SOURCE = FIXTURES + 'capital_terminal_capacity_v1.json'
VECTORS = FIXTURES + 'capital_terminal_capacity_vectors_v1.json'
SOURCE_PINS = {
    SOURCE: '6141cdd29e398856c8be91b4edc369742f654446b771662b53129aa471ea03a7',
    VECTORS: 'a2af57887d5fa17679a0634da9e320d6362e7df24c44695791971b97a336bd69',
}
SCENARIO_ID = 'T1_repay_close_capacity_reuse'
SCENARIO = '#/scenarios/0'
INITIAL_VIEWS = VECTORS + SCENARIO + '/initial_snapshot/credit/views/'
REPAY_VIEWS = VECTORS + SCENARIO + '/history/1/snapshot/credit/views/'
CLOSE_VIEWS = VECTORS + SCENARIO + '/history/7/snapshot/credit/views/'
CASE_REFS = {
    'repay_mixed': [INITIAL_VIEWS + '0', REPAY_VIEWS + '1'],
    'repay_same': [REPAY_VIEWS + '0', REPAY_VIEWS + '1'],
    'close_mixed': [INITIAL_VIEWS + '0', CLOSE_VIEWS + '1'],
    'close_same': [CLOSE_VIEWS + '0', CLOSE_VIEWS + '1'],
}


class CapitalMixedCheckpointViewsTests(unittest.TestCase):
    def setUp(self):
        raw = _read(PACK)
        self.pack = decode_json(raw.decode('utf-8'))
        self.assertEqual(canonical(self.pack), raw)
        exact_fields(self.pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                                 'contract', 'source_pins', 'scenario_id', 'group_id_ref',
                                 'limit_ref', 'cases'}, 'mixed-checkpoint pack')
        self.assertEqual(self.pack['fixture_version'], 'capital-mixed-checkpoint-views/1')
        self.assertEqual(self.pack['fixture_kind'], 'SYNTHETIC_MIXED_CHECKPOINT_VIEWS')
        self.assertIs(self.pack['synthetic_only'], True)
        self.assertEqual(self.pack['contract'], 'docs/contracts/CREDIT_ADVANCE_F04.md#7.12')
        self.assertEqual(self.pack['scenario_id'], SCENARIO_ID)

    def _verified_sources(self, read=_read):
        self.assertEqual(self.pack['source_pins'], [
            {'path': path, 'sha256': digest} for path, digest in SOURCE_PINS.items()
        ])
        documents = {}
        for pin in self.pack['source_pins']:
            path = pin['path']
            raw = read(path)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), pin['sha256'],
                             f'source digest drift: {path}')
            documents[path] = decode_json(raw.decode('utf-8'))
            self.assertEqual(_resolve(documents, path + SCENARIO + '/scenario_id'), SCENARIO_ID)
        self.assertEqual(documents[VECTORS]['fixture_sha256'], SOURCE_PINS[SOURCE])
        for index, step_id in ((1, 'repay-part'), (7, 'close-fresh')):
            self.assertEqual(_resolve(documents, SOURCE + SCENARIO + f'/steps/{index}/step_id'), step_id)
            self.assertEqual(_resolve(documents, VECTORS + SCENARIO + f'/history/{index}/step_id'), step_id)
        return documents

    def _resolve_arguments(self, documents):
        self.assertEqual(self.pack['group_id_ref'], SOURCE + SCENARIO + '/group_id')
        self.assertEqual(self.pack['limit_ref'], SOURCE + SCENARIO + '/limit')
        group_id = _resolve(documents, self.pack['group_id_ref'])
        limit = _resolve(documents, self.pack['limit_ref'])
        self.assertEqual(group_id, 'fixture-terminal-pool-1')
        self.assertIs(type(limit), int)
        self.assertEqual(limit, 70_000)
        return group_id, limit

    def _resolve_views(self, cases, documents):
        self.assertIs(type(cases), list)
        self.assertEqual([case['case_id'] for case in cases], list(CASE_REFS))
        views_by_case = {}
        for case in cases:
            exact_fields(case, {'case_id', 'view_refs', 'expected_result'}, 'mixed-checkpoint case')
            case_id = case['case_id']
            self.assertEqual(case['view_refs'], CASE_REFS[case_id], f'view pointer identity: {case_id}')
            views = [_resolve(documents, ref) for ref in case['view_refs']]
            self.assertEqual([view['advance_id'] for view in views], ['adv-1', 'adv-2'])
            self.assertEqual([view['claim_id'] for view in views], ['claim-1', 'claim-1'])
            self.assertEqual([view['trade_id'] for view in views], ['trade-claim-1', 'trade-claim-1'])
            views_by_case[case_id] = views
        return views_by_case

    def test_source_pins_and_pointer_identities(self):
        documents = self._verified_sources()
        self._resolve_arguments(documents)
        self._resolve_views(self.pack['cases'], documents)

        for path in SOURCE_PINS:
            with self.subTest(path=path), self.assertRaisesRegex(AssertionError, 'source digest drift'):
                self._verified_sources(lambda p: _read(p) + b'\n' if p == path else _read(p))

        cases = copy.deepcopy(self.pack['cases'])
        initial_adv2 = INITIAL_VIEWS + '1'
        self.assertEqual(canonical(_resolve(documents, initial_adv2)),
                         canonical(_resolve(documents, cases[0]['view_refs'][1])))
        cases[0]['view_refs'][1] = initial_adv2
        with self.assertRaisesRegex(AssertionError, 'view pointer identity: repay_mixed'):
            self._resolve_views(cases, documents)

    def test_checkpoint_pairs(self):
        documents = self._verified_sources()
        group_id, limit = self._resolve_arguments(documents)
        views_by_case = self._resolve_views(self.pack['cases'], documents)
        for case in self.pack['cases']:
            case_id = case['case_id']
            with self.subTest(case=case_id):
                views = copy.deepcopy(views_by_case[case_id])
                if case_id == 'close_mixed':
                    self.assertEqual([view['reserved_open'] for view in views], [70_000, 30_000])
                args, kwargs = (group_id, views), {'limit': limit}
                before = canonical([args, kwargs])
                try:
                    observed = observe_shared_exposure(*args, **kwargs)
                except SharedExposureError as error:
                    result = {'error': {'type': type(error).__name__, 'code': error.code}}
                else:
                    result = {'ok': observed}
                    self.assertEqual(observed['advance_count'], 2)
                    self.assertEqual(observed['claim_count'], 1)
                    claim, = observed['claims']
                    self.assertEqual(claim['claim_id'], 'claim-1')
                    self.assertEqual(claim['advance_ids'], ['adv-1', 'adv-2'])
                    self.assertIs(observed['within_limit'], True)
                    self.assertIs(observed['authorizes_exposure'], False)
                    self.assertIs(observed['mutates_state'], False)
                    self.assertIs(observed['fail_closed'], True)
                    self.assertEqual(observed['mapping'], {
                        'code': 'SHARED_EXPOSURE_NOT_BOUND', 'contract_status': 'NOT_BOUND', 'repair': 'NONE',
                    })
                finally:
                    self.assertEqual(canonical([args, kwargs]), before, 'observer input mutation')
                self.assertEqual(canonical(result), canonical(case['expected_result']))
