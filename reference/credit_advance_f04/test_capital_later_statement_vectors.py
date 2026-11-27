"""Replay the synthetic later-statement history and check its independent arithmetic."""
from __future__ import annotations

from pathlib import Path
import unittest

from scripts.bootstrap_2_fixtures import read_bootstrap_2_input

from credit_fixture import exact_fields
from settlement_credit_boundary_vectors import canonical, replay_scenario_with_state
from settlement_fsm import SettlementError
from test_capital_operation_replay_vectors import PROVENANCE, SETUP_FIELDS, load, same, sha
from test_capital_refund_composition_vectors import checkpoints, snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = HERE / 'fixtures/capital_later_statement_v1.json'
VECTORS = HERE / 'fixtures/capital_later_statement_vectors_v1.json'
FIXTURE_SHA256 = '1d0e7e806258b3bdaca08da0d4486fcdaf119fdb41470ac48f4df4602821ae4b'
VECTORS_SHA256 = '8d9949eec525ade2369437dde20f11f3aaa0a70b1d0a387af36bd64f33294317'
VERSION = 'capital-later-statement/1'
SCENARIO_ID = 'L1_later_statement_after_requester_refund'
SETTLEMENT_CONTRACT = 'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md'
CREDIT_CONTRACT = 'docs/contracts/CREDIT_ADVANCE_F04.md'
CONTRACTS = [f'{SETTLEMENT_CONTRACT}#{clause}' for clause in ('2', '3', '4', '5', '7.6', '9.2', '9.3')]
CONTRACTS += [f'{CREDIT_CONTRACT}#{clause}' for clause in ('7.2', '7.5', '7.11', '7.12')]
SOURCE_TESTS = [
    'reference/settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.'
    'test_later_statement_stays_on_commit_and_cases_do_not_share_cash',
    'reference/settlement_f01_f03/test_statement_adapter.py::StatementAdapterTests.'
    'test_replay_fetches_each_time_returns_first_snapshot_after_later_changes',
    'reference/settlement_f01_f03/test_mock_settlement.py::SettlementMockTests.'
    'test_f02_later_cash_continues_on_the_frozen_order',
    'reference/settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.'
    'test_partial_refund_distribution_survives_replay_and_is_not_a_clawback',
    'reference/credit_advance_f04/test_capital_refund_composition_vectors.py::CapitalRefundCompositionVectorTests.'
    'test_settlement_actions_preserve_credit',
    'reference/credit_advance_f04/test_settlement_variance_contract.py::SettlementVarianceContractTests.'
    'test_mapping_is_not_bound_and_companions_are_diagnostic',
    'reference/credit_advance_f04/test_shared_exposure_contract.py::SharedExposureContractTests.'
    'test_frozen_face_unchanged_after_settlement_refund',
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
    'reference/credit_advance_f04/test_capital_operation_replay_vectors.py',
    *dict.fromkeys(ref.split('::')[0] for ref in SOURCE_TESTS),
)
HISTORY = (
    ('distribute-initial', 'distribute'),
    ('refund-partial', 'bind_refund'),
    ('statement-later', 'observe_statement'),
    ('statement-replay', 'observe_statement'),
    ('distribute-later', 'distribute'),
)
HISTORY_FIELDS = {
    ('settlement', 'distribute'): {'settlement_id', 'idempotency_key', 'order'},
    ('settlement', 'bind_refund'): {'settlement_id', 'idempotency_key', 'refund_id',
                                   'amount', 'beneficiary_role', 'reason'},
    ('settlement', 'observe_statement'): SETUP_FIELDS['settlement', 'commit'],
}
CASH_FIELDS = ('receivable_open', 'confirmed_cash', 'non_cash_accounted',
               'undistributed_cash', 'distributed_cash')
REFUND_FIELDS = ('refund_face', 'refund_outstanding', 'refund_bearer_policy',
                 'refund_accepted', 'recovery_due', 'pg_adjustment_outstanding',
                 'fixture_reclassified', 'distribution_blocked')
EXECUTION_FLAGS = {
    'funds_executed', 'provider_authorization_executed', 'bank_debit_observed',
    'economic_finality_claimed', 'repayment_observed', 'legal_debtor_bound', 'durable',
    'underwriting_executed', 'kyc_executed', 'interest_defined', 'collateral_perfected',
    'priority_bound', 'ownership_mutated', 'ticket_ownership_authoritative',
    'admission_granted', 'external_return_closed', 'right_cancelled',
}


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_LATER_STATEMENT_VECTORS', True, PROVENANCE],
         [fixture[k] for k in ('fixture_version', 'fixture_kind', 'synthetic_only', 'provenance')])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 1
    scenario = fixture['scenarios'][0]
    exact_fields(scenario, {'scenario_id', 'contracts', 'source_tests', 'claim_id', 'advance_ids',
                            'group_id', 'limit', 'tolerance', 'setup_steps', 'steps',
                            'expected_arithmetic'}, 'scenario')
    same([SCENARIO_ID, CONTRACTS, SOURCE_TESTS, 'claim-1', ['adv-1'],
          'synthetic-later-statement-pool', 100_000, 0],
         [scenario[k] for k in ('scenario_id', 'contracts', 'source_tests', 'claim_id', 'advance_ids',
                                'group_id', 'limit', 'tolerance')])
    setup, history = scenario['setup_steps'], scenario['steps']
    assert type(setup) is list and type(history) is list
    for steps, fields in ((setup, SETUP_FIELDS), (history, HISTORY_FIELDS)):
        for step in steps:
            exact_fields(step, {'step_id', 'target', 'operation', 'arguments'}, 'step')
            selector = step['target'], step['operation']
            assert selector in fields, 'operation outside bounded replay'
            exact_fields(step['arguments'], fields[selector], 'arguments')
            for name, value in (('settlement_id', scenario['claim_id']),
                                ('advance_id', scenario['advance_ids'][0])):
                if name in step['arguments']:
                    same(value, step['arguments'][name])
    same([(op, target, op) for target, op in SETUP_FIELDS],
         [(s['step_id'], s['target'], s['operation']) for s in setup])
    same([(step, 'settlement', op) for step, op in HISTORY],
         [(s['step_id'], s['target'], s['operation']) for s in history])
    initial, _refund, statement, replayed, later = (s['arguments'] for s in history)
    same(statement, replayed)
    same(['organizer', 'platform'], initial['order'])
    same(initial['order'], later['order'])
    keys = [s['arguments']['idempotency_key'] for s in setup + history
            if s['step_id'] != 'statement-replay']
    same(len(keys), len(set(keys)))
    same(['initial'] + [step for step, _op in HISTORY],
         [row['step_id'] for row in scenario['expected_arithmetic']])
    return scenario


def source_pins():
    return [{'path': path, 'sha256': sha(read_bootstrap_2_input(path))} for path in SOURCE_PATHS]


def replay(inputs):
    def check_offer(step, settlement, _credit):
        if step['operation'] == 'offer':
            view = settlement.view(inputs['claim_id'])
            same('COMMITTED', view['phase'])
            same(view['claim'], step['arguments']['face'])

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': inputs['setup_steps']}, observer=check_offer)
    assert all('ok' in row['result'] for row in setup), 'setup must succeed'
    initial = snapshot(inputs, settlement, credit)
    methods = {'distribute': settlement.distribute, 'bind_refund': settlement.bind_refund,
               'observe_statement': settlement.observe_statement}
    history = []
    for step in inputs['steps']:
        try:
            result = {'ok': methods[step['operation']](**step['arguments'])}
        except SettlementError as error:
            result = {'error': {'type': type(error).__name__, 'code': error.code}}
        history.append({**{k: step[k] for k in ('step_id', 'target', 'operation')},
                        'result': result, 'snapshot': snapshot(inputs, settlement, credit)})
    return {'scenario_id': inputs['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history}


def check_execution_flags(test, value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in EXECUTION_FLAGS:
                test.assertIs(item, False, key)
            check_execution_flags(test, item)
    elif isinstance(value, list):
        for item in value:
            check_execution_flags(test, item)


class CapitalLaterStatementVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = validate_fixture(load(FIXTURE))
        cls.actual = replay(cls.inputs)

    def test_complete_history_vectors(self):
        same(FIXTURE_SHA256, sha(FIXTURE.read_bytes()))
        same(VECTORS_SHA256, sha(VECTORS.read_bytes()))
        self.assertEqual(VECTORS.read_bytes(), canonical({
            'vector_version': VERSION, 'fixture_sha256': sha(FIXTURE.read_bytes()),
            'source_pins': source_pins(), 'scenarios': [self.actual],
        }))

    def test_statement_identity_and_replay(self):
        states = checkpoints(self.actual)
        for state in states:
            view = state['settlement']['view']
            same(['COMMITTED', 'part-1'], [view['phase'], view['commit_movement_id']])
        history = self.actual['history']
        first, replayed = (history[i]['result']['ok'] for i in (2, 3))
        same(dict(first, duplicate=True, applied=None), replayed)
        same(states[3], states[4])

        journal = states[0]['settlement']['journal']
        same(['initiate', 'authorize', 'capture', 'commit'], [entry['op'] for entry in journal])
        same('part-1', journal[-1]['body']['movement_id'])
        for step, row in zip(self.inputs['steps'], history):
            current = row['snapshot']['settlement']
            receipt = row['result']['ok']
            same(current['view'], receipt['settlement'])
            if step['step_id'] == 'statement-replay':
                same(journal, current['journal'])
                continue
            operation = step['operation']
            same([False, operation], [receipt['duplicate'], receipt['applied']])
            same(journal, current['journal'][:-1])
            journal = current['journal']
            same([operation, step['arguments']['idempotency_key']],
                 [journal[-1]['op'], journal[-1]['idempotency_key']])
        same(['part-2'], [entry['body']['movement_id'] for entry in journal
                          if entry['op'] == 'observe_statement'])

    def test_checkpoint_arithmetic(self):
        states = checkpoints(self.actual)
        for expected, current in zip(self.inputs['expected_arithmetic'], states):
            with self.subTest(step=expected['step_id']):
                claim = current['settlement']['view']['claim']
                same(expected['cash'], {key: claim[key] for key in CASH_FIELDS})
                same(expected['refund'], {key: claim[key] for key in REFUND_FIELDS})
                same(expected['distribution_order'], claim['distribution_order'])
                obligations = {row['payee']: row for row in claim['obligations']}
                same(expected['payee_outstanding'], {p: row['outstanding'] for p, row in obligations.items()})
                for payee, face in (('organizer', 95_000), ('platform', 5_000)):
                    row = obligations[payee]
                    same([face, face - row['outstanding'], 0, 0],
                         [row[k] for k in ('face', 'distributed', 'cancelled_unpaid', 'recovery_due')])
                same(100_000, claim['gross'])
                same(claim['gross'], claim['confirmed_cash'] + claim['non_cash_accounted'] + claim['receivable_open'])
                same(claim['confirmed_cash'], claim['distributed_cash'] + claim['undistributed_cash'])

        for index, effect in ((0, {'organizer': 60_000, 'platform': 0}),
                              (4, {'organizer': 35_000, 'platform': 2_000})):
            same(effect, self.actual['history'][index]['result']['ok']['effect'])
            same(states[index]['settlement']['view']['claim']['undistributed_cash'], sum(effect.values()))

    def test_frozen_credit_and_observers(self):
        states = checkpoints(self.actual)
        for expected, current in zip(self.inputs['expected_arithmetic'], states):
            with self.subTest(step=expected['step_id']):
                same(states[0]['credit'], current['credit'])
                same(states[0]['shared_exposure'], current['shared_exposure'])
                for machine in ('settlement', 'credit'):
                    state = current[machine]
                    same(sha(state['canonical_state'].encode('utf-8')), state['state_digest'])

                credit = current['credit']['claim']
                advance = current['credit']['views'][0]
                same([True, 100_000, 60_000, 15_000, 85_000],
                     [credit[k] for k in ('snapshot_frozen', 'open_face', 'confirmed_cash_on_face',
                                          'reserved_open', 'residual_unreserved')])
                same(['DRAWN', 15_000, 0, 15_000],
                     [advance[k] for k in ('phase', 'drawn_exposure', 'repaid_exposure', 'outstanding_exposure')])
                exposure = current['shared_exposure']
                same({'group_drawn_exposure': 15_000, 'group_repaid_exposure': 0,
                      'group_outstanding_exposure': 15_000, 'group_open_face': 100_000,
                      'group_reserved_open': 15_000, 'group_residual_unreserved': 85_000}, exposure['observable'])
                same([1, 1, self.inputs['group_id'], self.inputs['limit'], True],
                     [exposure[k] for k in ('advance_count', 'claim_count', 'group_id', 'limit', 'within_limit')])

                claim = current['settlement']['view']['claim']
                outstanding = sum(row['outstanding'] for row in claim['obligations'])
                variance = current['variance']
                same(expected['variance'], variance['variance'])
                same({'settlement_outstanding': outstanding, 'credit_open_face': credit['open_face']},
                     variance['observable'])
                same(outstanding - credit['open_face'], variance['variance'])
                same([expected['sign'], self.inputs['tolerance'], expected['within_tolerance']],
                     [variance[k] for k in ('sign', 'tolerance', 'within_tolerance')])
                same(expected['cash_delta'], variance['companion']['cash_delta'])
                same(claim['confirmed_cash'] - credit['confirmed_cash_on_face'], variance['companion']['cash_delta'])
                same(0, variance['companion']['recovery_delta'])

                for observed, code in ((variance, 'SETTLEMENT_VARIANCE_NOT_BOUND'),
                                       (exposure, 'SHARED_EXPOSURE_NOT_BOUND')):
                    same({'code': code, 'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observed['mapping'])
                    same([True, False, False, 'NOT_BOUND'], [observed[k] for k in
                         ('fail_closed', 'mutates_state', 'authorizes_exposure', 'refund_component')])
        check_execution_flags(self, self.actual)
