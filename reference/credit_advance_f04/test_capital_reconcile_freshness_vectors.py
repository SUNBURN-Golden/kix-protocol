"""Process-local reconcile receipts and current variance, captured from public APIs."""
from __future__ import annotations

import copy
from pathlib import Path
import unittest

from scripts.bootstrap_2_fixtures import read_bootstrap_2_input

from credit_fixture import exact_fields
from credit_fsm import CreditError
from settlement_credit_boundary_vectors import canonical, replay_scenario_with_state
from settlement_fsm import SettlementError
from test_capital_operation_replay_vectors import (
    FIXTURE as SETUP_SOURCE, PROVENANCE, SETUP_FIELDS, load, same, sha,
)
from test_capital_refund_composition_vectors import snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = HERE / 'fixtures/capital_reconcile_freshness_v1.json'
VECTORS = HERE / 'fixtures/capital_reconcile_freshness_vectors_v1.json'
FIXTURE_SHA256 = 'f5a59872cb5c5a72028df4803666b990e86eb615f853db37c4a2267530b1d035'
VECTORS_SHA256 = '528b40f910a21c049a6d58e7cd71c51d8f34e98b1a88f296609857a45a7bf4dd'
VERSION = 'capital-reconcile-freshness/1'
SCENARIO_ID = 'F1_historical_reconcile_current_gap'
SETTLEMENT_CONTRACT = 'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md'
CREDIT_CONTRACT = 'docs/contracts/CREDIT_ADVANCE_F04.md'
CONTRACTS = [f'{SETTLEMENT_CONTRACT}#{clause}' for clause in ('5', '9.3', '9.4')] + [
    f'{CREDIT_CONTRACT}#{clause}' for clause in ('7.3', '7.4', '7.5', '7.11', '7.12')]
SOURCE_TESTS = [
    'reference/settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.'
    'test_reconcile_matches_restore_and_does_not_enter_the_economic_journal',
    'reference/credit_advance_f04/test_credit_fsm.py::CreditFsmTests.'
    'test_reconcile_replays_the_journal_without_a_second_draw',
    'reference/credit_advance_f04/test_settlement_credit_boundary.py::SettlementCreditBoundaryTests.'
    'test_s6_reconciliation_gap_is_reported_without_repair',
    'reference/credit_advance_f04/test_settlement_variance_contract.py::SettlementVarianceContractTests.'
    'test_mapping_is_not_bound_and_companions_are_diagnostic',
    'reference/credit_advance_f04/test_capital_refund_composition_vectors.py::CapitalRefundCompositionVectorTests.'
    'test_settlement_actions_preserve_credit',
]
SOURCE_PATHS = (
    SETTLEMENT_CONTRACT,
    CREDIT_CONTRACT,
    'reference/settlement_f01_f03/mock_settlement.py',
    'reference/settlement_f01_f03/settlement_fsm.py',
    'reference/credit_advance_f04/mock_credit.py',
    'reference/credit_advance_f04/credit_fsm.py',
    'reference/credit_advance_f04/open_terms.py',
    'reference/credit_advance_f04/credit_fixture.py',
    'reference/credit_advance_f04/settlement_credit_boundary_vectors.py',
    'reference/credit_advance_f04/settlement_variance.py',
    'reference/credit_advance_f04/shared_exposure.py',
    SETUP_SOURCE.relative_to(ROOT).as_posix(),
    'reference/credit_advance_f04/test_capital_operation_replay_vectors.py',
    *(ref.split('::')[0] for ref in SOURCE_TESTS),
)
STEP_FIELDS = {'step_id', 'target', 'operation', 'arguments'}
HISTORY = (
    ('settlement-first', 'settlement', 'reconcile'),
    ('credit-first', 'credit', 'reconcile'),
    ('refund-full', 'settlement', 'bind_refund'),
    ('settlement-replay', 'settlement', 'reconcile'),
    ('credit-replay', 'credit', 'reconcile'),
    ('settlement-fresh', 'settlement', 'reconcile'),
    ('credit-fresh', 'credit', 'reconcile'),
)
HISTORY_FIELDS = {
    ('settlement', 'reconcile'): {'settlement_id', 'idempotency_key'},
    ('credit', 'reconcile'): {'advance_id', 'idempotency_key'},
    ('settlement', 'bind_refund'): {'settlement_id', 'idempotency_key', 'refund_id',
                                   'amount', 'beneficiary_role', 'reason'},
}
ARITHMETIC_FIELDS = {
    'step_id', 'payee_outstanding', 'refund_face', 'fixture_reclassified',
    'refund_bearer_policy', 'settlement_outstanding', 'credit_open_face',
    'outstanding_exposure', 'variance', 'sign', 'within_tolerance',
}


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_RECONCILE_FRESHNESS_VECTORS', True, PROVENANCE],
         [fixture[k] for k in ('fixture_version', 'fixture_kind', 'synthetic_only', 'provenance')])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 1
    scenario = fixture['scenarios'][0]
    exact_fields(scenario, {'scenario_id', 'source_tests', 'contracts', 'claim_id',
                            'advance_ids', 'group_id', 'limit', 'tolerance', 'setup_steps',
                            'steps', 'expected_arithmetic'}, 'scenario')
    same([SCENARIO_ID, SOURCE_TESTS, CONTRACTS, 'claim-1', ['adv-1'],
          'synthetic-freshness-pool', 100_000, 0],
         [scenario[k] for k in ('scenario_id', 'source_tests', 'contracts', 'claim_id',
                                'advance_ids', 'group_id', 'limit', 'tolerance')])
    setup, steps = scenario['setup_steps'], scenario['steps']
    assert type(setup) is list and type(steps) is list
    for records, allowed in ((setup, SETUP_FIELDS), (steps, HISTORY_FIELDS)):
        for step in records:
            exact_fields(step, STEP_FIELDS, 'step')
            selector = step['target'], step['operation']
            assert selector in allowed, 'operation outside bounded replay'
            args = step['arguments']
            exact_fields(args, allowed[selector], 'arguments')
            if 'settlement_id' in args:
                same(scenario['claim_id'], args['settlement_id'])
            if 'advance_id' in args:
                same(scenario['advance_ids'][0], args['advance_id'])
    same(list(SETUP_FIELDS), [(s['target'], s['operation']) for s in setup])
    same(list(HISTORY), [(s['step_id'], s['target'], s['operation']) for s in steps])
    all_ids = [s['step_id'] for s in setup + steps]
    same(len(all_ids), len(set(all_ids)))
    first_settlement, first_credit, refund, replay_settlement, replay_credit, fresh_settlement, fresh_credit = (
        s['arguments'] for s in steps)
    same(first_settlement, replay_settlement)
    same(first_credit, replay_credit)
    same(100_000, refund['amount'])
    keys = [s['arguments']['idempotency_key'] for s in setup] + [
        args['idempotency_key'] for args in (first_settlement, first_credit, refund,
                                             fresh_settlement, fresh_credit)]
    same(len(keys), len(set(keys)))
    arithmetic = scenario['expected_arithmetic']
    assert type(arithmetic) is list
    for row in arithmetic:
        exact_fields(row, ARITHMETIC_FIELDS, 'arithmetic')
    same(['initial'] + [s['step_id'] for s in steps], [r['step_id'] for r in arithmetic])
    return scenario


def source_pins():
    return [{'path': path, 'sha256': sha(read_bootstrap_2_input(path))} for path in SOURCE_PATHS]


def replay(inputs):
    def check_face(step, settlement, _credit):
        if (step['target'], step['operation']) == ('credit', 'offer'):
            view = settlement.view(inputs['claim_id'])
            same('COMMITTED', view['phase'])
            same(view['claim'], step['arguments']['face'])

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': inputs['setup_steps']}, observer=check_face)
    assert all('ok' in row['result'] for row in setup), 'setup must be accepted'
    initial = snapshot(inputs, settlement, credit)
    methods = {
        ('settlement', 'reconcile'): settlement.reconcile,
        ('credit', 'reconcile'): credit.reconcile,
        ('settlement', 'bind_refund'): settlement.bind_refund,
    }
    history = []
    for step in inputs['steps']:
        selector = step['target'], step['operation']
        try:
            result = {'ok': methods[selector](**step['arguments'])}
        except (SettlementError, CreditError) as error:
            result = {'error': {'type': type(error).__name__, 'code': error.code}}
        history.append({'step_id': step['step_id'], 'target': step['target'],
                        'operation': step['operation'], 'result': result,
                        'snapshot': snapshot(inputs, settlement, credit)})
    return {'scenario_id': inputs['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history}


def verify_receipts(capture):
    rows = {row['step_id']: row for row in capture['history']}
    for machine in ('settlement', 'credit'):
        first, replayed, fresh = (rows[machine + '-' + point]
                                  for point in ('first', 'replay', 'fresh'))
        first_receipt = first['result']['ok']
        same({'ok': dict(first_receipt, duplicate=True, applied=None)}, replayed['result'])
        for row, count in ((first, 4), (fresh, 5 if machine == 'settlement' else 4)):
            receipt = row['result']['ok']
            current = row['snapshot'][machine]
            view = current['view'] if machine == 'settlement' else current['views'][0]
            same([False, 'reconcile', True, None, False, current['state_digest'], count, view],
                 [receipt[k] for k in ('duplicate', 'applied', 'matched', 'effect', 'funds_executed',
                                      'state_digest', 'entry_count', machine)])
            same(len(current['journal']), count)
        fresh_digest = fresh['result']['ok']['state_digest']
        if machine == 'settlement':
            assert fresh_digest != first_receipt['state_digest']
        else:
            same(first_receipt['state_digest'], fresh_digest)


def verify_state(inputs, capture):
    initial = capture['initial_snapshot']
    history = capture['history']
    checkpoints = [initial] + [row['snapshot'] for row in history]
    step_ids = ['initial'] + [row['step_id'] for row in history]
    same(len(inputs['expected_arithmetic']), len(checkpoints))
    for expected, current, step_id in zip(inputs['expected_arithmetic'], checkpoints, step_ids):
        same(initial['credit'], current['credit'])
        same(initial['shared_exposure'], current['shared_exposure'])
        same('COMMITTED', current['settlement']['view']['phase'])
        for machine in ('settlement', 'credit'):
            state = current[machine]
            same(sha(state['canonical_state'].encode('utf-8')), state['state_digest'])

        claim = current['settlement']['view']['claim']
        credit = current['credit']['claim']
        advance = current['credit']['views'][0]
        same([100_000, True, 'DRAWN', 15_000],
             [claim['gross'], credit['snapshot_frozen'], advance['phase'], advance['drawn_exposure']])
        payees = {obligation['payee']: obligation['outstanding'] for obligation in claim['obligations']}
        variance = current['variance']
        same(expected, {
            'step_id': step_id, 'payee_outstanding': payees,
            **{key: claim[key] for key in ('refund_face', 'fixture_reclassified', 'refund_bearer_policy')},
            **variance['observable'],
            **{key: variance[key] for key in ('variance', 'sign', 'within_tolerance')},
            'outstanding_exposure': advance['outstanding_exposure'],
        })
        outstanding, open_face = sum(payees.values()), credit['open_face']
        same([outstanding, open_face, outstanding - open_face, inputs['tolerance']],
             [variance['observable']['settlement_outstanding'], variance['observable']['credit_open_face'],
              variance['variance'], variance['tolerance']])
        exposure = current['shared_exposure']
        same([15_000, 100_000, True], [exposure['observable']['group_outstanding_exposure'],
                                      exposure['limit'], exposure['within_limit']])
        for observation, code in ((variance, 'SETTLEMENT_VARIANCE_NOT_BOUND'),
                                  (exposure, 'SHARED_EXPOSURE_NOT_BOUND')):
            same({'code': code, 'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observation['mapping'])
            same([True, False, False, 'NOT_BOUND'], [observation[k] for k in
                 ('fail_closed', 'mutates_state', 'authorizes_exposure', 'refund_component')])

    for before, after, row in zip(checkpoints, checkpoints[1:], history):
        if row['operation'] == 'reconcile':
            same(before, after)
        else:
            same('refund-full', row['step_id'])
            prior = before['settlement']['journal']
            current = after['settlement']['journal']
            same(prior, current[:-1])
            same(['bind_refund', 5], [current[-1]['op'], len(current)])
            same(row['result']['ok']['settlement'], after['settlement']['view'])


class CapitalReconcileFreshnessVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(FIXTURE)
        cls.vectors = load(VECTORS)
        cls.inputs = validate_fixture(cls.fixture)
        cls.actual = replay(cls.inputs)

    def test_artifact_and_source_pins(self):
        same(FIXTURE_SHA256, sha(FIXTURE.read_bytes()))
        same(VECTORS_SHA256, sha(VECTORS.read_bytes()))
        same(source_pins(), self.vectors['source_pins'])
        original = next(s for s in load(SETUP_SOURCE)['scenarios']
                        if s['scenario_id'] == 'R3_reconcile_restore_replay')
        same(original['setup_steps'], self.inputs['setup_steps'])

    def test_complete_history_vectors(self):
        same(self.vectors, {'vector_version': VERSION, 'fixture_sha256': sha(canonical(self.fixture)),
                            'source_pins': source_pins(), 'scenarios': [self.actual]})

    def test_historical_and_fresh_receipts(self):
        verify_receipts(self.actual)

    def test_current_variance_and_state(self):
        verify_state(self.inputs, self.actual)

    def test_detached_semantic_controls(self):
        detached = copy.deepcopy(self.actual)
        first = detached['history'][0]['result']['ok']
        # Keep the fresh flags and replace only the fresh state with the historical state.
        detached['history'][5]['result']['ok'].update(
            {k: first[k] for k in ('settlement', 'state_digest', 'entry_count')})
        with self.assertRaises(AssertionError):
            verify_receipts(detached)

        for field, value in (('variance', 0), ('within_tolerance', True),
                             ('authorizes_exposure', True),
                             ('mapping', {'code': 'SETTLEMENT_VARIANCE_NOT_BOUND',
                                          'contract_status': 'NOT_BOUND', 'repair': 'AUTOMATIC'})):
            with self.subTest(field=field):
                detached = copy.deepcopy(self.actual)
                detached['history'][-1]['snapshot']['variance'][field] = value
                with self.assertRaises(AssertionError):
                    verify_state(self.inputs, detached)
