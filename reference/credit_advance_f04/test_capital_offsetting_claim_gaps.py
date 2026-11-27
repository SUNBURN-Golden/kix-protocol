"""Replay two pinned claim observations whose signed variances sum to zero."""

import copy
from hashlib import sha256
import unittest

from credit_fixture import decode_json, exact_fields
from settlement_variance import canonical, load_fixture, observe_settlement_variance
from test_capital_companion_evidence_index import BASE, FIXTURES, ROOT, _read, _resolve


PACK = FIXTURES + 'capital_offsetting_claim_gaps_vectors_v1.json'
SOURCE = FIXTURES + 'settlement_variance_v1.json'
OBSERVER = BASE + 'settlement_variance.py'
SOURCE_PINS = [
    {'path': SOURCE, 'sha256': 'f2db31f337bc44d5931e97f0e5c57d529e8f1f444339366b50178c304df38b76'},
    {'path': OBSERVER, 'sha256': 'af5db942825f8268bde42142d343454bca3e0bb43ca417fdfb86d590e347005d'},
]
SCENARIOS = (
    # Case ID, source index and ID, claim and trade, expected observer row.
    # The row is (outstanding, frozen face, tolerance, variance, sign).
    ('v4_claim_gap', 3, 'V4_positive_observation_sign', 'claim-v4', 'trade-v4',
     (100_000, 60_000, 0, 40_000, 'POSITIVE')),
    ('v6_claim_gap', 5, 'V6_boundary_plus_one_out_of_tolerance', 'claim-v2', 'trade-v2',
     (60_000, 100_000, 39_999, -40_000, 'NEGATIVE')),
)


class CapitalOffsettingClaimGapsTests(unittest.TestCase):
    def setUp(self):
        raw = _read(PACK)
        self.pack = decode_json(raw.decode('utf-8'))
        self.assertEqual(canonical(self.pack), raw)
        exact_fields(self.pack, {'fixture_version', 'fixture_kind', 'synthetic_only',
                                 'contract', 'source_pins', 'cases', 'diagnostic_sum_krw'},
                     'offsetting claim gaps pack')
        self.assertEqual(self.pack['fixture_version'], 'capital-offsetting-claim-gaps/1')
        self.assertEqual(self.pack['fixture_kind'], 'SYNTHETIC_OFFSETTING_CLAIM_GAPS')
        self.assertIs(self.pack['synthetic_only'], True)
        self.assertEqual(self.pack['contract'], 'docs/contracts/CREDIT_ADVANCE_F04.md#7.11')
        self.assertEqual(self.pack['source_pins'], SOURCE_PINS)
        for pin in SOURCE_PINS:
            self.assertEqual(sha256(_read(pin['path'])).hexdigest(), pin['sha256'], pin['path'])
        self.documents = {SOURCE: load_fixture(ROOT / SOURCE)}
        self.assertIs(type(self.pack['diagnostic_sum_krw']), int)
        self.assertEqual(self.pack['diagnostic_sum_krw'], 0)
        self.assertIs(type(self.pack['cases']), list)
        self.assertEqual([case['case_id'] for case in self.pack['cases']],
                         [scenario[0] for scenario in SCENARIOS])

    def _replay_case(self, case, specification):
        case_id, index, scenario_id, claim_id, trade_id, expected_row = specification
        exact_fields(case, {'case_id', 'scenario_id', 'claim_id', 'trade_id',
                            'settlement_view_ref', 'credit_view_ref', 'tolerance_ref',
                            'settlement_view_sha256', 'credit_view_sha256', 'expected_result'},
                     case_id)
        self.assertEqual((case['case_id'], case['scenario_id'], case['claim_id'], case['trade_id']),
                         (case_id, scenario_id, claim_id, trade_id))

        prefix = f'{SOURCE}#/scenarios/{index}'
        scenario = _resolve(self.documents, prefix)
        self.assertEqual((scenario['id'], scenario['claim_id'], scenario['trade_id']),
                         (scenario_id, claim_id, trade_id), case_id)
        for field in ('settlement_view', 'credit_view', 'tolerance'):
            self.assertEqual(case[field + '_ref'], f'{prefix}/{field}', case_id)

        settlement = _resolve(self.documents, case['settlement_view_ref'])
        credit = _resolve(self.documents, case['credit_view_ref'])
        tolerance = _resolve(self.documents, case['tolerance_ref'])
        for field, view in (('settlement_view', settlement), ('credit_view', credit)):
            self.assertEqual((view['claim_id'], view['trade_id'], view['currency']),
                             (claim_id, trade_id, 'KRW'), field)
            self.assertEqual(sha256(canonical(view)).hexdigest(), case[field + '_sha256'], field)
        self.assertIs(credit['snapshot_frozen'], True, case_id)

        result = observe_settlement_variance(settlement, credit, tolerance=tolerance)
        self.assertEqual(canonical({'ok': result}), canonical(case['expected_result']),
                         f'{claim_id} replay result mismatch')
        self.assertEqual((result['claim_id'], result['trade_id']), (claim_id, trade_id))
        observed = result['observable']
        self.assertEqual((observed['settlement_outstanding'], observed['credit_open_face'],
                          result['tolerance'], result['variance'], result['sign']),
                         expected_row, claim_id)
        self.assertIs(result['within_tolerance'], False, claim_id)
        self.assertEqual(result['mapping'], {'code': 'SETTLEMENT_VARIANCE_NOT_BOUND',
                                             'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, claim_id)
        self.assertEqual(result['refund_component'], 'NOT_BOUND', claim_id)
        self.assertIs(result['fail_closed'], True, claim_id)
        self.assertIs(result['mutates_state'], False, claim_id)
        self.assertIs(result['authorizes_exposure'], False, claim_id)
        return result['variance']

    def test_claim_pair(self):
        diagnostic_sum = sum(self._replay_case(case, spec)
                             for case, spec in zip(self.pack['cases'], SCENARIOS))
        self.assertEqual(diagnostic_sum, self.pack['diagnostic_sum_krw'])

    def test_swapped_claim_attributions(self):
        cases = copy.deepcopy(self.pack['cases'])
        first, second = [case['expected_result']['ok'] for case in cases]
        for field in ('variance', 'sign'):
            first[field], second[field] = second[field], first[field]
        self.assertEqual(first['variance'] + second['variance'], self.pack['diagnostic_sum_krw'])
        for case, spec in zip(cases, SCENARIOS):
            with self.assertRaisesRegex(AssertionError, f"{case['claim_id']} replay result mismatch"):
                self._replay_case(case, spec)
