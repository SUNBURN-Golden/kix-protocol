"""Compare overlapping caller groups from the same pinned E3 checkpoint."""

import copy
import hashlib
import unittest

from credit_fixture import decode_json, exact_fields
from shared_exposure import SharedExposureError, canonical, observe_shared_exposure
from test_capital_companion_evidence_index import FIXTURES, _read, _resolve


PACK = FIXTURES + 'capital_overlapping_exposure_groups_vectors_v1.json'
SOURCE = FIXTURES + 'shared_exposure_v1.json'
SOURCE_SHA256 = 'cdb001701376c02cd3515bcdd939193922c960bdcaebf80ca8d3f0d7732c1c03'
SCENARIO_ID = 'E3_pool_three_claims_default_still_aggregates'
SCENARIO_REF = SOURCE + '#/scenarios/2'
VIEWS_REF = SCENARIO_REF + '/credit_views'
CASE_MEMBERS = {
    'e3_ab': (0, 1),
    'e3_bc': (1, 2),
    'e3_abc': (0, 1, 2),
    'e3_duplicate_b': (0, 1, 1, 2),
}


class CapitalOverlappingExposureGroupsTests(unittest.TestCase):
    def setUp(self):
        raw = _read(PACK)
        self.pack = decode_json(raw.decode('utf-8'))
        self.assertEqual(canonical(self.pack), raw)
        exact_fields(self.pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                                 'contract', 'source_pins', 'cases'}, 'overlapping exposure groups pack')
        self.assertEqual(self.pack['fixture_version'], 'capital-overlapping-exposure-groups/1')
        self.assertEqual(self.pack['fixture_kind'], 'SYNTHETIC_OVERLAPPING_EXPOSURE_GROUPS')
        self.assertIs(self.pack['synthetic_only'], True)
        self.assertEqual(self.pack['contract'], 'docs/contracts/CREDIT_ADVANCE_F04.md#7.12')

    def _verified_source(self, read=_read):
        self.assertEqual(self.pack['source_pins'], [{'path': SOURCE, 'sha256': SOURCE_SHA256}])
        raw = read(SOURCE)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SOURCE_SHA256, 'source digest drift')
        return {SOURCE: decode_json(raw.decode('utf-8'))}

    def _resolve_cases(self, cases, documents):
        self.assertIs(type(cases), list)
        self.assertEqual([case['case_id'] for case in cases], list(CASE_MEMBERS))
        self.assertEqual(_resolve(documents, SCENARIO_REF + '/id'), SCENARIO_ID)
        all_views = _resolve(documents, VIEWS_REF)
        self.assertEqual([view['advance_id'] for view in all_views], ['adv-e3-a', 'adv-e3-b', 'adv-e3-c'])
        for view in all_views:
            self.assertIs(view['snapshot_frozen'], True)

        arguments = {}
        for case in cases:
            exact_fields(case, {'case_id', 'scenario_id', 'group_id_ref', 'limit_ref',
                                'view_refs', 'expected_result'}, 'overlapping exposure groups case')
            case_id = case['case_id']
            self.assertEqual(case['scenario_id'], SCENARIO_ID)
            self.assertEqual(case['group_id_ref'], SCENARIO_REF + '/group_id')
            self.assertEqual(case['limit_ref'], SCENARIO_REF + '/limit')
            self.assertEqual(case['view_refs'], [f'{VIEWS_REF}/{i}' for i in CASE_MEMBERS[case_id]],
                             f'view pointer identity: {case_id}')
            group_id = _resolve(documents, case['group_id_ref'])
            limit = _resolve(documents, case['limit_ref'])
            views = [_resolve(documents, ref) for ref in case['view_refs']]
            self.assertEqual(group_id, 'pool-e3')
            self.assertIs(type(limit), int)
            self.assertEqual(limit, 90_000)
            arguments[case_id] = (group_id, views, limit)
        return arguments

    def test_source_pins_and_pointer_identities(self):
        documents = self._verified_source()
        self._resolve_cases(self.pack['cases'], documents)

        with self.assertRaisesRegex(AssertionError, 'source digest drift'):
            self._verified_source(lambda path: _read(path) + b'\n')

        cases = copy.deepcopy(self.pack['cases'])
        cases[0]['view_refs'][1] = f'{VIEWS_REF}/2'
        with self.assertRaisesRegex(AssertionError, 'view pointer identity: e3_ab'):
            self._resolve_cases(cases, documents)

    def test_overlapping_groups(self):
        cases = self.pack['cases']
        documents = self._verified_source()
        arguments = self._resolve_cases(cases, documents)
        outstanding = {}
        advance_ids = {}
        for case in cases:
            case_id = case['case_id']
            group_id, views, limit = copy.deepcopy(arguments[case_id])
            args, kwargs = (group_id, views), {'limit': limit}
            before = canonical([args, kwargs])
            try:
                result = {'ok': observe_shared_exposure(*args, **kwargs)}
            except SharedExposureError as error:
                result = {'error': {'type': type(error).__name__, 'code': error.code}}
            finally:
                self.assertEqual(canonical([args, kwargs]), before, f'observer input mutation: {case_id}')
            self.assertEqual(canonical(result), canonical(case['expected_result']), case_id)
            if case_id == 'e3_duplicate_b':
                self.assertEqual(result, {'error': {'type': 'SharedExposureError', 'code': 'VIEW_INVALID'}})
                continue

            record = result['ok']
            self.assertEqual(record['limit'], limit, case_id)
            self.assertEqual(record['advance_count'], len(views), case_id)
            self.assertIs(record['within_limit'], True, case_id)
            self.assertEqual(record['mapping'], {
                'code': 'SHARED_EXPOSURE_NOT_BOUND', 'contract_status': 'NOT_BOUND', 'repair': 'NONE',
            }, case_id)
            self.assertEqual(record['refund_component'], 'NOT_BOUND', case_id)
            self.assertIs(record['fail_closed'], True, case_id)
            for flag in ('authorizes_exposure', 'mutates_state', 'legal_debtor_bound'):
                self.assertIs(record[flag], False, (case_id, flag))
            outstanding[case_id] = record['observable']['group_outstanding_exposure']
            advance_ids[case_id] = {advance_id for claim in record['claims'] for advance_id in claim['advance_ids']}

        self.assertEqual(outstanding, {'e3_ab': 70_000, 'e3_bc': 50_000, 'e3_abc': 90_000})
        self.assertEqual(advance_ids['e3_ab'] | advance_ids['e3_bc'], advance_ids['e3_abc'])
        defaulted_view = _resolve(documents, f'{VIEWS_REF}/1')
        self.assertEqual(defaulted_view['phase'], 'DEFAULTED')
        self.assertEqual(advance_ids['e3_ab'] & advance_ids['e3_bc'], {defaulted_view['advance_id']})
        self.assertEqual(outstanding['e3_ab'] + outstanding['e3_bc'] - outstanding['e3_abc'],
                         defaulted_view['outstanding_exposure'])
