"""Replay complete fixture groups and their one-member subsets at the same checkpoint."""

import copy
import hashlib
import unittest

from credit_fixture import decode_json, exact_fields
from shared_exposure import canonical, observe_shared_exposure
from test_capital_companion_evidence_index import FIXTURES, _read, _resolve


PACK = FIXTURES + 'capital_omitted_exposure_members_vectors_v1.json'
SOURCE = FIXTURES + 'shared_exposure_v1.json'
SOURCE_SHA256 = 'cdb001701376c02cd3515bcdd939193922c960bdcaebf80ca8d3f0d7732c1c03'
SCENARIOS = (
    ('e1', 'E1_two_advances_one_claim_exact_limit', 'group-e1', 70_000, ('adv-e1-1', 'adv-e1-2')),
    ('e2', 'E2_two_claims_one_debtor_label_over_limit', 'debtor-e2', 100_000, ('adv-e2-a', 'adv-e2-b')),
)
MEMBERSHIPS = (('full', 2), ('omit_second', 1))


class CapitalOmittedExposureMembersTests(unittest.TestCase):
    def setUp(self):
        raw = _read(PACK)
        self.pack = decode_json(raw.decode('utf-8'))
        self.assertEqual(canonical(self.pack), raw)
        exact_fields(self.pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                                 'contract', 'source_pins', 'cases'}, 'omitted exposure members pack')
        self.assertEqual(self.pack['fixture_version'], 'capital-omitted-exposure-members/1')
        self.assertEqual(self.pack['fixture_kind'], 'SYNTHETIC_OMITTED_EXPOSURE_MEMBERS')
        self.assertIs(self.pack['synthetic_only'], True)
        self.assertEqual(self.pack['contract'], 'docs/contracts/CREDIT_ADVANCE_F04.md#7.12')

    def _verified_source(self, read=_read):
        self.assertEqual(self.pack['source_pins'], [{'path': SOURCE, 'sha256': SOURCE_SHA256}])
        raw = read(SOURCE)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SOURCE_SHA256, 'source digest drift')
        return {SOURCE: decode_json(raw.decode('utf-8'))}

    def _resolve_cases(self, cases, documents):
        self.assertIs(type(cases), list)
        self.assertEqual([case['case_id'] for case in cases], [
            f'{prefix}_{membership}' for prefix, *_ in SCENARIOS for membership, _ in MEMBERSHIPS
        ])
        cases_by_id = {case['case_id']: case for case in cases}
        arguments = {}
        for index, (prefix, scenario_id, group, fixture_limit, advances) in enumerate(SCENARIOS):
            scenario_ref = SOURCE + f'#/scenarios/{index}'
            self.assertEqual(_resolve(documents, scenario_ref + '/id'), scenario_id)
            all_views = _resolve(documents, scenario_ref + '/credit_views')
            self.assertEqual(tuple(view['advance_id'] for view in all_views), advances)
            for membership, count in MEMBERSHIPS:
                case_id = f'{prefix}_{membership}'
                case = cases_by_id[case_id]
                exact_fields(case, {'case_id', 'scenario_id', 'group_id_ref', 'limit_ref',
                                    'view_refs', 'expected_result'}, 'omitted exposure members case')
                self.assertEqual(case['scenario_id'], scenario_id)
                self.assertEqual(case['group_id_ref'], scenario_ref + '/group_id')
                self.assertEqual(case['limit_ref'], scenario_ref + '/limit')
                self.assertEqual(case['view_refs'], [
                    scenario_ref + f'/credit_views/{i}' for i in range(count)
                ], f'view pointer identity: {case_id}')

                group_id = _resolve(documents, case['group_id_ref'])
                limit = _resolve(documents, case['limit_ref'])
                views = [_resolve(documents, ref) for ref in case['view_refs']]
                self.assertEqual(group_id, group)
                self.assertIs(type(limit), int)
                self.assertEqual(limit, fixture_limit)
                self.assertEqual(tuple(view['advance_id'] for view in views), advances[:count])
                for view in views:
                    self.assertIs(view['snapshot_frozen'], True)
                arguments[case_id] = (group_id, views, limit)
        return arguments

    def test_source_pins_and_pointer_identities(self):
        documents = self._verified_source()
        self._resolve_cases(self.pack['cases'], documents)

        with self.assertRaisesRegex(AssertionError, 'source digest drift'):
            self._verified_source(lambda path: _read(path) + b'\n')

        cases = copy.deepcopy(self.pack['cases'])
        e2_full = next(case for case in cases if case['case_id'] == 'e2_full')
        e5_view = SOURCE + '#/scenarios/4/credit_views/0'
        self.assertEqual(canonical(_resolve(documents, e2_full['view_refs'][0])),
                         canonical(_resolve(documents, e5_view)))
        e2_full['view_refs'][0] = e5_view
        with self.assertRaisesRegex(AssertionError, 'view pointer identity: e2_full'):
            self._resolve_cases(cases, documents)

    def test_membership_pairs(self):
        cases = self.pack['cases']
        arguments = self._resolve_cases(cases, self._verified_source())
        observed = {}
        for case in cases:
            case_id = case['case_id']
            with self.subTest(case=case_id):
                group_id, views, limit = copy.deepcopy(arguments[case_id])
                args, kwargs = (group_id, views), {'limit': limit}
                before = canonical([args, kwargs])
                try:
                    record = observe_shared_exposure(*args, **kwargs)
                finally:
                    self.assertEqual(canonical([args, kwargs]), before, 'observer input mutation')
                observed[case_id] = record
                self.assertEqual(canonical({'ok': record}), canonical(case['expected_result']))
                self.assertEqual(record['mapping'], {
                    'code': 'SHARED_EXPOSURE_NOT_BOUND', 'contract_status': 'NOT_BOUND', 'repair': 'NONE',
                })
                self.assertEqual(record['refund_component'], 'NOT_BOUND')
                self.assertIs(record['fail_closed'], True)
                for flag in ('mutates_state', 'authorizes_exposure', 'legal_debtor_bound'):
                    self.assertIs(record[flag], False, flag)

        for prefix, amount in (('e1', 30_000), ('e2', 50_000)):
            with self.subTest(pair=prefix):
                full = observed[prefix + '_full']
                subset = observed[prefix + '_omit_second']
                metric = 'group_outstanding_exposure'
                self.assertEqual(full['observable'][metric] - subset['observable'][metric], amount)
        for case_id in ('e1_full', 'e1_omit_second'):
            claim, = observed[case_id]['claims']
            self.assertEqual(claim['reserved_open'], 70_000)
        self.assertIs(observed['e2_full']['within_limit'], False)
        self.assertIs(observed['e2_omit_second']['within_limit'], True)
