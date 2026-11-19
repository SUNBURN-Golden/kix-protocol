"""Source-informed, test-only ordered two-claim Capital consumer evidence.

Goldens capture public outputs; independent fixture literals constrain the
arithmetic. Tests never regenerate artifacts or change producer sources.
"""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_fixture import exact_fields  # noqa: E402
from credit_fsm import CreditError  # noqa: E402
from settlement_credit_boundary_vectors import (  # noqa: E402
    canonical, replay_scenario_with_state,
)
from settlement_fsm import SettlementError  # noqa: E402
from settlement_variance import observe_settlement_variance  # noqa: E402
from shared_exposure import observe_shared_exposure  # noqa: E402
from test_capital_operation_replay_vectors import (  # noqa: E402
    PROVENANCE, SETUP_FIELDS, SOURCE_PATHS as REUSED_SOURCES, load, same, sha,
)

FIXTURE = HERE / 'fixtures/capital_cross_claim_history_v1.json'
VECTORS = HERE / 'fixtures/capital_cross_claim_history_vectors_v1.json'
VERSION = 'capital-cross-claim-history/1'
FIXTURE_SHA256 = '60d6625b602743f0d4ee6a6a3f0bc7b7d9ed33f9604fdca69af51d45190e5d41'
VECTORS_SHA256 = '561d213760e60f44a7debaa5901494387d7fd9d4b022c43e03084293fd65d673'
SOURCE_PATHS = REUSED_SOURCES + (
    'reference/credit_advance_f04/settlement_variance.py',
    'reference/credit_advance_f04/test_capital_operation_replay_vectors.py',
    'reference/credit_advance_f04/test_capital_terminal_capacity_vectors.py',
    'reference/credit_advance_f04/test_economics_credit_consumer_vectors.py',
)
CLAIMS = ['claim-h1-a', 'claim-h1-b']
ADVANCES = ['adv-h1-a1', 'adv-h1-a2', 'adv-h1-b1']
CONTRACTS = [f'docs/contracts/CREDIT_ADVANCE_F04.md#7.{n}'
             for n in [2, 3, 11, 12]] + [
                 'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md']
CITATIONS = [
    'test_shared_exposure_contract.py::SharedExposureContractTests.test_aggregation_formulas_over_exposed_values_only',
    'test_shared_exposure_contract.py::SharedExposureContractTests.test_frozen_face_unchanged_after_settlement_refund',
    'test_capital_terminal_capacity_vectors.py::CapitalTerminalCapacityVectorTests.test_repayment_close_capacity_arithmetic',
    'test_capital_operation_replay_vectors.py::CapitalOperationReplayVectorTests.test_complete_history_vectors',
    'test_economics_credit_consumer_vectors.py::EconomicsCreditConsumerTests.test_frozen_credit_bytes_survive_all_economics_actions',
]
CITATIONS = ['reference/credit_advance_f04/' + path for path in CITATIONS]
HISTORY_FIELDS = {
    ('credit', 'repay'): {'advance_id', 'idempotency_key', 'repay_id', 'sequence', 'amount'},
    ('credit', 'close'): {'advance_id', 'idempotency_key'},
    ('credit', 'default'): {'advance_id', 'idempotency_key', 'reason'},
    ('credit', 'draw'): SETUP_FIELDS['credit', 'draw'],
    ('settlement', 'bind_refund'): {'settlement_id', 'idempotency_key', 'refund_id',
                                   'amount', 'beneficiary_role', 'reason'},
    ('settlement', 'observe_mock_cancel_acceptance'): {
        'settlement_id', 'idempotency_key', 'source_id', 'amount'},
}
SETUP_ORDER = [
    (op + '-' + label, 'settlement', op, claim)
    for label, claim in zip(['a', 'b'], CLAIMS)
    for op in ['initiate', 'authorize', 'capture', 'commit']
] + [
    (op + '-' + label, 'credit', op, advance)
    for label, advance in zip(['a1', 'a2', 'b1'], ADVANCES)
    for op in ['offer', 'approve', 'bind_settlement', 'draw']
]
HISTORY_ORDER = [
    ('repay-a1-part', 'credit', 'repay', ADVANCES[0]),
    ('repay-a1-rest', 'credit', 'repay', ADVANCES[0]),
    ('close-a1', 'credit', 'close', ADVANCES[0]),
    ('refund-b', 'settlement', 'bind_refund', CLAIMS[1]),
    ('accept-b', 'settlement', 'observe_mock_cancel_acceptance', CLAIMS[1]),
    ('default-b1', 'credit', 'default', ADVANCES[2]),
    ('replay-a1', 'credit', 'draw', ADVANCES[0]),
]
TOTAL_FIELDS = {'group_drawn_exposure', 'group_repaid_exposure',
                'group_outstanding_exposure', 'group_open_face',
                'group_reserved_open', 'group_residual_unreserved'}
ADVANCE_FIELDS = {'advance_id', 'claim_id', 'phase', 'note_status', 'drawn_exposure',
                  'repaid_exposure', 'outstanding_exposure'}
CLAIM_FIELDS = {'claim_id', 'trade_id', 'advance_ids', 'open_face', 'reserved_open',
                'residual_unreserved'}
VARIANCE_FIELDS = {'settlement_outstanding', 'credit_open_face', 'variance', 'sign',
                   'within_tolerance', 'cash_delta', 'recovery_delta'}


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_CROSS_CLAIM_HISTORY_VECTORS', True, PROVENANCE],
         [fixture['fixture_version'], fixture['fixture_kind'], fixture['synthetic_only'],
          fixture['provenance']])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 1
    scenario = fixture['scenarios'][0]
    exact_fields(scenario, {'scenario_id', 'source_tests', 'contracts', 'setup_steps',
                            'claim_ids', 'advance_ids', 'group_id', 'limit', 'tolerance',
                            'steps', 'expected_arithmetic'}, 'scenario')
    same('H1_two_claims_refund_default', scenario['scenario_id'])
    same(CITATIONS, scenario['source_tests'])
    same(CONTRACTS, scenario['contracts'])
    same(CLAIMS, scenario['claim_ids'])
    same(ADVANCES, scenario['advance_ids'])
    same(['synthetic-h1-pool', 120_000, 0],
         [scenario['group_id'], scenario['limit'], scenario['tolerance']])
    for key, order, fields in [('setup_steps', SETUP_ORDER, SETUP_FIELDS),
                                ('steps', HISTORY_ORDER, HISTORY_FIELDS)]:
        steps = scenario[key]
        assert type(steps) is list and len(steps) == len(order)
        for step, (step_id, target, operation, identifier) in zip(steps, order):
            exact_fields(step, {'step_id', 'target', 'operation', 'arguments'}, 'step')
            same([step_id, target, operation],
                 [step['step_id'], step['target'], step['operation']])
            arguments = step['arguments']
            exact_fields(arguments, fields[target, operation], 'arguments')
            same(identifier, arguments['advance_id' if target == 'credit' else 'settlement_id'])
            for name in ['idempotency_key', 'draw_id', 'repay_id', 'refund_id',
                         'source_id', 'movement_id', 'reason', 'beneficiary_role']:
                if name in arguments:
                    value = arguments[name]
                    assert type(value) is str and 0 < len(value) <= 100 and value.strip() == value
    all_steps = scenario['setup_steps'] + scenario['steps']
    same(27, len({step['step_id'] for step in all_steps}))
    keys = [step['arguments']['idempotency_key'] for step in all_steps]
    same(26, len(set(keys)))  # Only the final original-key draw is a duplicate.
    same(scenario['setup_steps'][11]['arguments'], scenario['steps'][-1]['arguments'])
    for i, step in enumerate(scenario['setup_steps'][8:]):
        claim = CLAIMS[0 if i < 8 else 1]
        if step['operation'] == 'offer':
            same(claim, step['arguments']['face']['claim_id'])
        if step['operation'] == 'bind_settlement':
            same(claim, step['arguments']['settlement_id'])
    rows = scenario['expected_arithmetic']
    assert type(rows) is list and len(rows) == 8
    same(['initial'] + [step['step_id'] for step in scenario['steps']],
         [row['step_id'] for row in rows])
    for row in rows:
        exact_fields(row, {'step_id', 'observable', 'advance_count', 'claim_count',
                           'within_limit', 'claims', 'advances', 'variance'}, 'arithmetic')
        exact_fields(row['observable'], TOTAL_FIELDS, 'totals')
        same([3, 2, True], [row[k] for k in ['advance_count', 'claim_count', 'within_limit']])
        same(CLAIMS, [entry['claim_id'] for entry in row['claims']])
        same(ADVANCES, [entry['advance_id'] for entry in row['advances']])
        for entry in row['claims']:
            exact_fields(entry, CLAIM_FIELDS, 'claim arithmetic')
        for entry in row['advances']:
            exact_fields(entry, ADVANCE_FIELDS, 'advance arithmetic')
        exact_fields(row['variance'], set(CLAIMS), 'variance arithmetic')
        for entry in row['variance'].values():
            exact_fields(entry, VARIANCE_FIELDS, 'variance arithmetic')


def verify_sources(pins, reader=None):
    reader = (lambda path: (ROOT / path).read_bytes()) if reader is None else reader
    same(list(SOURCE_PATHS), [pin['path'] for pin in pins])
    for pin in pins:
        exact_fields(pin, {'path', 'sha256'}, 'source pin')
        same(pin['sha256'], sha(reader(pin['path'])))


def snapshot(scenario, settlement, credit):
    # Public snapshots at one checkpoint, including CLOSED and DEFAULTED advances.
    views = [credit.view(identifier) for identifier in scenario['advance_ids']]
    claims = {identifier: credit.view_claim(identifier) for identifier in scenario['claim_ids']}
    settlements = {identifier: settlement.view(identifier) for identifier in scenario['claim_ids']}
    before = canonical([settlements, views, claims])
    variance = {identifier: observe_settlement_variance(
        settlements[identifier]['claim'], claims[identifier], tolerance=scenario['tolerance'])
        for identifier in scenario['claim_ids']}
    exposure = observe_shared_exposure(scenario['group_id'], views, limit=scenario['limit'])
    assert before == canonical([settlements, views, claims])
    return {
        'settlement': {'views': settlements, 'journal': settlement.export_journal(),
                       'canonical_state': settlement.canonical_state(),
                       'state_digest': settlement.state_digest()},
        'credit': {'views': views, 'claims': claims, 'journal': credit.export_journal(),
                   'canonical_state': credit.canonical_state(), 'state_digest': credit.state_digest()},
        'variance': variance, 'shared_exposure': exposure,
    }


def replay(scenario):
    def check_face(step, settlement, _credit):
        if step['target'] == 'credit' and step['operation'] == 'offer':
            face = step['arguments']['face']
            current = settlement.view(face['claim_id'])
            same('COMMITTED', current['phase'])
            same(current['claim'], face)

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': scenario['setup_steps']}, observer=check_face)
    assert all('ok' in row['result'] for row in setup)
    initial = snapshot(scenario, settlement, credit)
    methods = {('credit', 'repay'): credit.repay, ('credit', 'close'): credit.close,
               ('credit', 'default'): credit.default, ('credit', 'draw'): credit.draw,
               ('settlement', 'bind_refund'): settlement.bind_refund,
               ('settlement', 'observe_mock_cancel_acceptance'): settlement.observe_mock_cancel_acceptance}
    history = []
    for step in scenario['steps']:
        try:
            result = {'ok': methods[step['target'], step['operation']](**step['arguments'])}
        except (CreditError, SettlementError) as error:
            result = {'error': {'type': type(error).__name__, 'code': error.code}}
        history.append({key: step[key] for key in ['step_id', 'target', 'operation']})
        history[-1].update(result=result, snapshot=snapshot(scenario, settlement, credit))
    assert all('ok' in row['result'] for row in history)
    return {'scenario_id': scenario['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history}


def checkpoints(scenario):
    return [scenario['initial_snapshot']] + [row['snapshot'] for row in scenario['history']]


def verify_arithmetic(inputs, scenario):
    same(len(inputs['expected_arithmetic']), len(checkpoints(scenario)))
    for expected, current in zip(inputs['expected_arithmetic'], checkpoints(scenario)):
        exposure = current['shared_exposure']
        for field in ['observable', 'claims', 'advance_count', 'claim_count', 'within_limit']:
            same(expected[field], exposure[field])
        same(expected['advances'], [{key: view[key] for key in ADVANCE_FIELDS}
                                    for view in current['credit']['views']])
        for entry in expected['claims']:
            claim = current['credit']['claims'][entry['claim_id']]
            for key in ['claim_id', 'trade_id', 'open_face', 'reserved_open', 'residual_unreserved']:
                same(entry[key], claim[key])
            same(entry['advance_ids'], sorted(view['advance_id'] for view in current['credit']['views']
                                             if view['claim_id'] == entry['claim_id']))
        for identifier, arithmetic in expected['variance'].items():
            observed = current['variance'][identifier]
            same(arithmetic, {**observed['observable'],
                              **{key: observed[key] for key in ['variance', 'sign', 'within_tolerance']},
                              **{key: observed['companion'][key] for key in ['cash_delta', 'recovery_delta']}})


def verify_semantics(fixture, vectors):
    """Detached verification bypasses outer byte pins, retaining ordered replay."""
    validate_fixture(fixture)
    exact_fields(vectors, {'vector_version', 'fixture_sha256', 'source_pins', 'scenarios'}, 'vectors')
    same(VERSION, vectors['vector_version'])
    same(sha(canonical(fixture)), vectors['fixture_sha256'])
    verify_sources(vectors['source_pins'])
    actual = [replay(scenario) for scenario in fixture['scenarios']]
    same(vectors['scenarios'], actual)
    for inputs, scenario in zip(fixture['scenarios'], actual):
        verify_arithmetic(inputs, scenario)
    return actual


class CapitalCrossClaimHistoryVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(FIXTURE)
        cls.vectors = load(VECTORS)
        validate_fixture(cls.fixture)
        cls.actual = replay(cls.fixture['scenarios'][0])

    def test_artifact_and_source_pins(self):
        same(FIXTURE_SHA256, sha(FIXTURE.read_bytes()))
        same(VECTORS_SHA256, sha(VECTORS.read_bytes()))
        same(FIXTURE_SHA256, self.vectors['fixture_sha256'])
        verify_sources(self.vectors['source_pins'])
        # Verify citations exist without importing/rerunning those test classes.
        import ast
        for citation in CITATIONS:
            path, name = citation.split('::')
            class_name, method = name.split('.')
            tree = ast.parse((ROOT / path).read_text())
            node = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                        and node.name == class_name)
            self.assertIn(method, {node.name for node in node.body if isinstance(node, ast.FunctionDef)})

    def test_complete_history_vectors(self):
        same([self.actual], verify_semantics(self.fixture, self.vectors))

    def test_checkpoint_arithmetic(self):
        verify_arithmetic(self.fixture['scenarios'][0], self.actual)
        states = checkpoints(self.actual)
        # Repayment retains reservation; close releases only A1's 40000.
        same([120_000, 120_000, 120_000, 80_000],
             [s['shared_exposure']['observable']['group_reserved_open'] for s in states[:4]])
        same(states[2]['credit']['claims'][CLAIMS[1]], states[3]['credit']['claims'][CLAIMS[1]])
        same(states[5]['shared_exposure'], states[6]['shared_exposure'])
        for current in states:
            views = current['credit']['views']
            claims = current['credit']['claims']
            totals = current['shared_exposure']['observable']
            for suffix in ['drawn_exposure', 'repaid_exposure', 'outstanding_exposure']:
                same(sum(view[suffix] for view in views), totals['group_' + suffix])
            for suffix in ['open_face', 'reserved_open', 'residual_unreserved']:
                same(sum(claim[suffix] for claim in claims.values()), totals['group_' + suffix])
            same(180_000, totals['group_open_face'])
            for view in views:
                same(view['drawn_exposure'] - view['repaid_exposure'], view['outstanding_exposure'])
                same(view['open_face'] - view['reserved_open'], view['residual_unreserved'])

    def test_refund_preserves_credit_and_gap(self):
        states = checkpoints(self.actual)
        for index in [4, 5]:
            same(states[3]['credit'], states[index]['credit'])
        before = states[3]['settlement']['views'][CLAIMS[1]]['claim']
        refund = states[4]['settlement']['views'][CLAIMS[1]]['claim']
        accepted = states[5]['settlement']['views'][CLAIMS[1]]['claim']
        same([76_000, 4_000], [x['outstanding'] for x in before['obligations']])
        same([76_000, 4_000], [x['cancelled_unpaid'] for x in refund['obligations']])
        same([80_000, 0, 80_000, 0],
             [refund[k] for k in ['refund_face', 'refund_accepted', 'refund_outstanding',
                                  'pg_adjustment_outstanding']])
        same([80_000, 80_000, 0, 80_000],
             [accepted[k] for k in ['refund_face', 'refund_accepted', 'refund_outstanding',
                                    'pg_adjustment_outstanding']])
        for current in states:
            for identifier in CLAIMS:
                initial = states[0]['credit']['claims'][identifier]
                claim = current['credit']['claims'][identifier]
                same({k: v for k, v in initial.items() if k not in ['reserved_open', 'residual_unreserved']},
                     {k: v for k, v in claim.items() if k not in ['reserved_open', 'residual_unreserved']})
                self.assertIs(claim['snapshot_frozen'], True)
            same(0, current['variance'][CLAIMS[0]]['variance'])
        for current in states[4:]:
            same(-80_000, current['variance'][CLAIMS[1]]['variance'])
            same([0, 0], [current['variance'][CLAIMS[1]]['companion'][k]
                         for k in ['cash_delta', 'recovery_delta']])

    def test_cross_claim_original_key_replay(self):
        original = self.actual['setup_results'][11]['result']['ok']
        expected = copy.deepcopy(original)
        expected.update(duplicate=True, applied=None)
        last = self.actual['history'][-1]
        same(expected, last['result']['ok'])
        same(self.actual['history'][-2]['snapshot'], last['snapshot'])
        same('DRAWN', last['result']['ok']['credit']['phase'])
        same(40_000, last['result']['ok']['credit']['outstanding_exposure'])
        same('CLOSED', last['snapshot']['credit']['views'][0]['phase'])
        same(0, last['snapshot']['credit']['views'][0]['outstanding_exposure'])
        same(['DEFAULTED', 'NOTED', 50_000],
             [last['snapshot']['credit']['views'][2][k]
              for k in ['phase', 'note_status', 'outstanding_exposure']])
        same(0, last['snapshot']['settlement']['views'][CLAIMS[1]]['claim']['refund_outstanding'])

    def test_observation_boundaries(self):
        false_flags = {'funds_executed', 'bank_debit_observed', 'economic_finality_claimed',
                       'repayment_observed', 'legal_debtor_bound', 'durable',
                       'underwriting_executed', 'kyc_executed', 'interest_defined',
                       'collateral_perfected', 'priority_bound', 'ownership_mutated',
                       'ticket_ownership_authoritative', 'admission_granted',
                       'license_granted', 'regulated_product', 'disposal_controlled',
                       'revenue_assigned', 'external_pledge_complete',
                       'external_return_closed', 'right_cancelled'}

        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in false_flags:
                        self.assertIs(item, False, key)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(self.actual)
        for current in checkpoints(self.actual):
            for observed, code in [(current['shared_exposure'], 'SHARED_EXPOSURE_NOT_BOUND')] + [
                    (value, 'SETTLEMENT_VARIANCE_NOT_BOUND') for value in current['variance'].values()]:
                same({'code': code, 'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observed['mapping'])
                same([True, False, False, 'NOT_BOUND'],
                     [observed[k] for k in ['fail_closed', 'mutates_state', 'authorizes_exposure', 'refund_component']])

    def test_detached_observations_and_digests(self):
        inputs = self.fixture['scenarios'][0]
        for current in checkpoints(self.vectors['scenarios'][0]):
            detached = copy.deepcopy(current)
            same(current['shared_exposure'], observe_shared_exposure(
                inputs['group_id'], detached['credit']['views'], limit=inputs['limit']))
            for identifier in CLAIMS:
                same(current['variance'][identifier], observe_settlement_variance(
                    detached['settlement']['views'][identifier]['claim'],
                    detached['credit']['claims'][identifier], tolerance=inputs['tolerance']))
            same(current, detached)
            for producer in ['settlement', 'credit']:
                same(sha(current[producer]['canonical_state'].encode()), current[producer]['state_digest'])

    def test_verifier_sensitivity(self):
        def history(v):
            return v['scenarios'][0]['history']

        mutations = [
            lambda v: history(v).pop(3),
            lambda v: history(v).reverse(),
            lambda v: v['scenarios'][0]['setup_results'].reverse(),
            lambda v: history(v)[-1]['result']['ok'].update(duplicate=False),
            lambda v: history(v)[-1]['snapshot']['credit']['views'].__setitem__(
                0, copy.deepcopy(history(v)[-1]['result']['ok']['credit'])),
            lambda v: history(v)[-1]['result']['ok'].__setitem__(
                'credit', copy.deepcopy(history(v)[-1]['snapshot']['credit']['views'][0])),
            lambda v: history(v)[4]['snapshot']['variance'].__setitem__(
                CLAIMS[1], copy.deepcopy(v['scenarios'][0]['initial_snapshot']['variance'][CLAIMS[1]])),
            lambda v: history(v)[4]['snapshot']['settlement'].__setitem__(
                'views', copy.deepcopy(v['scenarios'][0]['initial_snapshot']['settlement']['views'])),
            lambda v: history(v)[0]['snapshot']['shared_exposure']['claims'][0]
                         .update(advance_ids=ADVANCES),
            lambda v: history(v)[0]['snapshot']['credit']['views'][2].update(claim_id=CLAIMS[0]),
            lambda v: history(v)[0]['snapshot']['shared_exposure']['observable']
                         .update(group_open_face=280_000, group_reserved_open=190_000,
                                 group_residual_unreserved=90_000),
            lambda v: v['source_pins'].pop(),
            lambda v: v['source_pins'][0].update(sha256='0' * 64),
        ]
        for field in sorted(TOTAL_FIELDS):
            mutations.append(lambda v, field=field: history(v)[0]['snapshot']['shared_exposure']
                             ['observable'].update({field: 1}))
        for index, mutate in enumerate(mutations):
            with self.subTest(vector_mutation=index):
                changed = copy.deepcopy(self.vectors)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    verify_semantics(self.fixture, changed)
        for path in SOURCE_PATHS:
            with self.subTest(source_bytes=path):
                def altered_reader(candidate):
                    raw = (ROOT / candidate).read_bytes()
                    return raw + b'\n' if candidate == path else raw
                with self.assertRaises(AssertionError):
                    verify_sources(self.vectors['source_pins'], altered_reader)
        # Update the inner fixture hash: these failures cannot be outer pin failures.
        mutations = [
            lambda s: s['steps'].pop(3),
            lambda s: s['steps'].reverse(),
            lambda s: s['setup_steps'].reverse(),
            lambda s: s['setup_steps'][12]['arguments']['face'].update(claim_id=CLAIMS[1]),
            lambda s: s['expected_arithmetic'][0]['claims'][0].update(advance_ids=ADVANCES),
            lambda s: s['expected_arithmetic'][0]['advances'][2].update(claim_id=CLAIMS[0]),
            lambda s: s['expected_arithmetic'][0]['variance'][CLAIMS[1]].update(variance=-80_000),
            lambda s: s['steps'][3]['arguments'].update(amount=40_000),
        ]
        for field in sorted(TOTAL_FIELDS):
            mutations.append(lambda s, field=field: s['expected_arithmetic'][0]['observable'].update({field: 1}))
        for index, mutate in enumerate(mutations):
            with self.subTest(fixture_mutation=index):
                changed = copy.deepcopy(self.fixture)
                mutate(changed['scenarios'][0])
                vectors = copy.deepcopy(self.vectors)
                vectors['fixture_sha256'] = sha(canonical(changed))
                with self.assertRaises(AssertionError):
                    verify_semantics(changed, vectors)
        for key in ['setup_steps', 'steps']:
            changed = copy.deepcopy(self.fixture)
            changed['scenarios'][0][key][0]['operation'] = 'reconcile'
            with self.assertRaises(AssertionError):
                validate_fixture(changed)


if __name__ == '__main__':
    unittest.main()
