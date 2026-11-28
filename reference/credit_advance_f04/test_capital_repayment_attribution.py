"""Replay two repayment targets from the same pinned H1 checkpoint."""
import copy
from pathlib import Path
import unittest

from credit_fixture import exact_fields
from credit_fsm import CreditError
from settlement_credit_boundary_vectors import replay_scenario_with_state
from test_capital_cross_claim_history_vectors import (
    ADVANCES, CLAIMS, FIXTURE as H1_INPUT, FIXTURE_SHA256, ROOT,
    VECTORS as H1_OUTPUT, VECTORS_SHA256, snapshot, validate_fixture,
)
from test_capital_operation_replay_vectors import PROVENANCE, load, same, sha

PACK = Path(__file__).resolve().parent / 'fixtures/capital_repayment_attribution_vectors_v1.json'
SOURCE_PINS = ((H1_INPUT, FIXTURE_SHA256), (H1_OUTPUT, VECTORS_SHA256))
CASES = (
    ('repay_a1', 'adv-h1-a1', 'claim-h1-a', (30_000, 30_000, 50_000)),
    ('repay_b1', 'adv-h1-b1', 'claim-h1-b', (40_000, 30_000, 40_000)),
)
REPAYMENT_BODY = {'repay_id': 'repay-a1-part', 'sequence': 1, 'amount': 10_000}
CONFLICT = {'error': {'type': 'CreditError', 'code': 'IDEMPOTENCY_CONFLICT'}}


def _check_offer_face(step, settlement, _credit):
    if step['target'] == 'credit' and step['operation'] == 'offer':
        face = step['arguments']['face']
        current = settlement.view(face['claim_id'])
        same('COMMITTED', current['phase'])
        same(current['claim'], face)


class CapitalRepaymentAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load(PACK)
        same([{'path': path.relative_to(ROOT).as_posix(), 'sha256': digest}
              for path, digest in SOURCE_PINS], cls.pack['source_pins'])
        for path, digest in SOURCE_PINS:
            same(digest, sha(path.read_bytes()))
        source = load(H1_INPUT)
        validate_fixture(source)
        cls.inputs = source['scenarios'][0]
        cls.h1 = load(H1_OUTPUT)['scenarios'][0]

    def assert_repayment_attribution(self, pack):
        exact_fields(pack, {'fixture_version', 'fixture_kind', 'synthetic_only', 'provenance',
                            'source_pins', 'checkpoint_ref', 'repayment_ref', 'cases'}, 'pack')
        same(['capital-repayment-attribution/1', 'SYNTHETIC_REPAYMENT_ATTRIBUTION', True, PROVENANCE],
             [pack[k] for k in ('fixture_version', 'fixture_kind', 'synthetic_only', 'provenance')])
        same(H1_OUTPUT.relative_to(ROOT).as_posix() + '#/scenarios/0/initial_snapshot',
             pack['checkpoint_ref'])
        same(H1_INPUT.relative_to(ROOT).as_posix() + '#/scenarios/0/steps/0', pack['repayment_ref'])
        original = self.inputs['steps'][0]['arguments']
        same({'advance_id': 'adv-h1-a1', 'idempotency_key': 'repay-a1-part', **REPAYMENT_BODY}, original)
        same([case_id for case_id, *_ in CASES], [case['case_id'] for case in pack['cases']])

        for i, (case, (case_id, advance_id, claim_id, outstanding)) in enumerate(zip(pack['cases'], CASES, strict=True)):
            exact_fields(case, {'case_id', 'arguments', 'expected_result', 'after', 'conflict'}, case_id)
            exact_fields(case['conflict'], {'arguments', 'expected_result'}, 'conflict')
            same({**original, 'advance_id': advance_id}, case['arguments'])
            same({**original, 'advance_id': CASES[1 - i][1]}, case['conflict']['arguments'])
            same(CONFLICT, case['conflict']['expected_result'])

            setup, settlement, credit = replay_scenario_with_state(
                {'steps': self.inputs['setup_steps']}, observer=_check_offer_face)
            same(self.h1['setup_results'], setup)
            before = snapshot(self.inputs, settlement, credit)
            same(self.h1['initial_snapshot'], before)
            self.assertEqual(len(before['credit']['journal']), 12)
            self.assertEqual(len(before['settlement']['journal']), 8)

            receipt = credit.repay(**case['arguments'])
            after = snapshot(self.inputs, settlement, credit)
            expected_view = case['expected_result']['ok']['credit']
            self.assertEqual(expected_view['advance_id'], advance_id, f'{case_id} repayment receipt target')
            self.assertEqual(case['after']['credit']['journal'][-1]['advance_id'], advance_id,
                             f'{case_id} repayment journal target')
            same(case['expected_result'], {'ok': receipt})
            same(case['after'], after)
            same(['repay', False, advance_id, claim_id],
                 [receipt['applied'], receipt['duplicate'], receipt['credit']['advance_id'], receipt['credit']['claim_id']])
            if i == 0:
                same(self.h1['history'][0]['result'], {'ok': receipt})
                same(self.h1['history'][0]['snapshot'], after)

            views = {view['advance_id']: view['outstanding_exposure'] for view in after['credit']['views']}
            same(dict(zip(ADVANCES, outstanding, strict=True)), views)
            exposure = after['shared_exposure']
            same(['synthetic-h1-pool', 120_000, 3, 2, True, 110_000],
                 [exposure['group_id'], exposure['limit'], exposure['advance_count'], exposure['claim_count'],
                  exposure['within_limit'], exposure['observable']['group_outstanding_exposure']])
            same(self.h1['history'][0]['snapshot']['shared_exposure'], exposure)

            journal_entry = {'op': 'repay', 'advance_id': advance_id, 'idempotency_key': original['idempotency_key'],
                             'body': REPAYMENT_BODY}
            same(before['credit']['journal'] + [journal_entry], after['credit']['journal'])
            same(before['settlement'], after['settlement'])
            same(before['credit']['claims'], after['credit']['claims'])
            same([[100_000, 70_000, True], [80_000, 50_000, True]],
                 [[after['credit']['claims'][claim][field] for field in ('open_face', 'reserved_open', 'snapshot_frozen')]
                  for claim in CLAIMS])

            with self.assertRaises(CreditError) as refused:
                credit.repay(**case['conflict']['arguments'])
            same(case['conflict']['expected_result'],
                 {'error': {'type': type(refused.exception).__name__, 'code': refused.exception.code}})
            same(after, snapshot(self.inputs, settlement, credit))

    def test_repayment_attribution(self):
        self.assert_repayment_attribution(self.pack)

    def test_detached_attribution_swap(self):
        self.assert_repayment_attribution(self.pack)
        detached = copy.deepcopy(self.pack)
        a1, b1 = detached['cases']
        for field in ('expected_result', 'after'):
            a1[field], b1[field] = b1[field], a1[field]
        same([110_000, 110_000],
             [case['after']['shared_exposure']['observable']['group_outstanding_exposure'] for case in (a1, b1)])
        with self.assertRaisesRegex(AssertionError, 'repay_a1 repayment receipt target'):
            self.assert_repayment_attribution(detached)
