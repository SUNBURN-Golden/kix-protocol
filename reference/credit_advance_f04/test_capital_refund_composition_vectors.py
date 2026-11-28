"""Source-informed, offline Capital refund composition evidence.

Public output captures are constrained by separately stated arithmetic literals.
Tests never regenerate goldens; no producer, helper or prior pack is changed.
"""
from __future__ import annotations

import ast
import copy
from pathlib import Path
import sys
import unittest

from scripts.bootstrap_2_fixtures import read_bootstrap_2_input

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_fixture import FixtureError, decode_json, exact_fields  # noqa: E402
from settlement_fsm import SettlementError  # noqa: E402
from settlement_credit_boundary_vectors import canonical, replay_scenario_with_state  # noqa: E402
from settlement_variance import observe_settlement_variance  # noqa: E402
from shared_exposure import observe_shared_exposure  # noqa: E402
from test_capital_operation_replay_vectors import (  # noqa: E402
    PROVENANCE, SETUP_FIELDS, SOURCE_PATHS as REUSED_SOURCES, load, same, sha,
)

FIXTURE = HERE / 'fixtures/capital_refund_composition_v1.json'
VECTORS = HERE / 'fixtures/capital_refund_composition_vectors_v1.json'
VERSION = 'capital-refund-composition/1'
FIXTURE_SHA256 = 'edc0fd50eea445a4fdd135ff942733548a1c3cd830af2ade9ff3e7cd03e43026'
VECTORS_SHA256 = '5ec920d005e918a7de64577f23daa0625fe2db9a1f62f199a8070f57258cd87b'
SOURCE_PATHS = REUSED_SOURCES + (
    'reference/credit_advance_f04/settlement_variance.py',
    'reference/credit_advance_f04/test_settlement_variance_contract.py',
    'reference/credit_advance_f04/test_capital_operation_replay_vectors.py',
    'reference/credit_advance_f04/test_capital_cross_claim_history_vectors.py',
    'reference/credit_advance_f04/test_economics_credit_consumer_vectors.py',
    'reference/settlement_f01_f03/test_settlement_multi_payee_refund.py',
    'reference/credit_advance_f04/fixtures/settlement_credit_boundary_vectors_v1.json',
    'reference/credit_advance_f04/fixtures/economics_credit_consumer_v1.json',
    'reference/credit_advance_f04/fixtures/economics_credit_consumer_vectors_v1.json',
    'reference/credit_advance_f04/fixtures/capital_cross_claim_history_v1.json',
    'reference/credit_advance_f04/fixtures/capital_cross_claim_history_vectors_v1.json',
)
INVENTORY = [
    ('R1_full_refund_after_partial_distribution',
     'test_g_reservation_at_partial_distribution_is_per_payee'),
    ('R2_partial_refunds_summing_to_gross',
     'test_g_partial_refunds_summing_to_gross_never_reclassify'),
]
CONTRACTS = [f'docs/contracts/CREDIT_ADVANCE_F04.md#7.{n}' for n in [2, 3, 5, 11, 12]] + [
    'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md']
HISTORY_FIELDS = {
    ('settlement', 'distribute'): {'settlement_id', 'idempotency_key', 'order'},
    ('settlement', 'bind_refund'): {'settlement_id', 'idempotency_key', 'refund_id',
                                   'amount', 'beneficiary_role', 'reason'},
    ('settlement', 'observe_mock_cancel_acceptance'): {
        'settlement_id', 'idempotency_key', 'source_id', 'amount'},
}
HISTORY_ORDERS = [
    [('distribute', 'distribute'), ('refund-full', 'bind_refund'),
     ('accept-full', 'observe_mock_cancel_acceptance')],
    [('distribute', 'distribute'), ('refund-30', 'bind_refund'),
     ('refund-70', 'bind_refund'), ('accept-30', 'observe_mock_cancel_acceptance'),
     ('accept-70', 'observe_mock_cancel_acceptance'), ('redistribute', 'distribute')],
]
PAYEE_FIELDS = {'payee', 'face', 'distributed', 'cancelled_unpaid', 'recovery_due', 'outstanding'}
REFUND_FIELDS = {'refund_face', 'refund_accepted', 'refund_outstanding',
                 'pg_adjustment_outstanding', 'refund_bearer_policy',
                 'fixture_reclassified', 'distribution_blocked'}
TOTAL_FIELDS = {'group_drawn_exposure', 'group_repaid_exposure', 'group_outstanding_exposure',
                'group_open_face', 'group_reserved_open', 'group_residual_unreserved'}
VARIANCE_FIELDS = {'settlement_outstanding', 'credit_open_face', 'variance', 'sign',
                   'within_tolerance', 'cash_delta', 'recovery_delta'}


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_REFUND_COMPOSITION_VECTORS', True, PROVENANCE],
         [fixture['fixture_version'], fixture['fixture_kind'], fixture['synthetic_only'],
          fixture['provenance']])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 2
    for number, (scenario, (identifier, method)) in enumerate(zip(fixture['scenarios'], INVENTORY), 1):
        exact_fields(scenario, {'scenario_id', 'source_tests', 'contracts', 'setup_steps',
                                'claim_id', 'advance_ids', 'group_id', 'limit', 'tolerance',
                                'steps', 'expected_arithmetic'}, 'scenario')
        same(identifier, scenario['scenario_id'])
        same(['reference/settlement_f01_f03/test_settlement_multi_payee_refund.py::'
              'RefundReservationPerPayeeTests.' + method], scenario['source_tests'])
        same(CONTRACTS, scenario['contracts'])
        claim = f'claim-r{number}'
        advances = [f'adv-r{number}-1', f'adv-r{number}-2']
        same([claim, advances, f'synthetic-r{number}-pool', 100_000, 0],
             [scenario[k] for k in ['claim_id', 'advance_ids', 'group_id', 'limit', 'tolerance']])
        order = [(op, 'settlement', op, claim)
                 for op in ['initiate', 'authorize', 'capture', 'commit']]
        order += [(op + f'-{i}', 'credit', op, advance)
                  for i, advance in enumerate(advances, 1)
                  for op in ['offer', 'approve', 'bind_settlement', 'draw']]
        history = [(step, 'settlement', op, claim) for step, op in HISTORY_ORDERS[number - 1]]
        for key, inventory, fields in [('setup_steps', order, SETUP_FIELDS),
                                        ('steps', history, HISTORY_FIELDS)]:
            steps = scenario[key]
            assert type(steps) is list and len(steps) == len(inventory)
            for step, (step_id, target, operation, entity) in zip(steps, inventory):
                exact_fields(step, {'step_id', 'target', 'operation', 'arguments'}, 'step')
                same([step_id, target, operation], [step[k] for k in ['step_id', 'target', 'operation']])
                args = step['arguments']
                exact_fields(args, fields[target, operation], 'arguments')
                same(entity, args['advance_id' if target == 'credit' else 'settlement_id'])
                for name in ['idempotency_key', 'draw_id', 'refund_id', 'source_id', 'movement_id',
                             'trade_id', 'debtor_role', 'beneficiary_role', 'reason']:
                    if name in args:
                        value = args[name]
                        assert type(value) is str and 0 < len(value) <= 100 and value.strip() == value
                if 'amount' in args:
                    assert type(args['amount']) is int and args['amount'] > 0
                if operation == 'bind_settlement':
                    same(claim, args['settlement_id'])
                if operation == 'offer':
                    same(claim, args['face']['claim_id'])
        steps = scenario['setup_steps'] + scenario['steps']
        same(len(steps), len({s['step_id'] for s in steps}))
        same(len(steps), len({s['arguments']['idempotency_key'] for s in steps}))
        for field in ['refund_id', 'source_id']:
            values = [s['arguments'][field] for s in steps if field in s['arguments']]
            same(len(values), len(set(values)))
        rows = scenario['expected_arithmetic']
        assert type(rows) is list
        same(['initial'] + [s['step_id'] for s in scenario['steps']], [r['step_id'] for r in rows])
        for row in rows:
            exact_fields(row, {'step_id', 'payees', 'refund', 'credit', 'variance',
                               'advance_count', 'claim_count', 'within_limit'}, 'arithmetic')
            same([2, 1, True], [row[k] for k in ['advance_count', 'claim_count', 'within_limit']])
            exact_fields(row['refund'], REFUND_FIELDS, 'refund arithmetic')
            exact_fields(row['credit'], TOTAL_FIELDS, 'credit arithmetic')
            exact_fields(row['variance'], VARIANCE_FIELDS, 'variance arithmetic')
            assert type(row['payees']) is list and len(row['payees']) == 2
            same([f'fee-r{number}', f'res-r{number}'], [r['payee'] for r in row['payees']])
            for payee in row['payees']:
                exact_fields(payee, PAYEE_FIELDS, 'payee arithmetic')


def verify_sources(pins, reader=None):
    reader = read_bootstrap_2_input if reader is None else reader
    assert type(pins) is list
    same(list(SOURCE_PATHS), [pin['path'] for pin in pins])
    for pin in pins:
        exact_fields(pin, {'path', 'sha256'}, 'source pin')
        same(pin['sha256'], sha(reader(pin['path'])))


def snapshot(inputs, settlement, credit):
    view = settlement.view(inputs['claim_id'])
    views = [credit.view(identifier) for identifier in inputs['advance_ids']]
    claim = credit.view_claim(inputs['claim_id'])
    before = canonical([settlement.canonical_state(), settlement.export_journal(),
                        credit.canonical_state(), credit.export_journal(), view, views, claim])
    variance = observe_settlement_variance(view['claim'], claim, tolerance=inputs['tolerance'])
    exposure = observe_shared_exposure(inputs['group_id'], views, limit=inputs['limit'])
    assert before == canonical([settlement.canonical_state(), settlement.export_journal(),
                                credit.canonical_state(), credit.export_journal(), view, views, claim])
    return {'settlement': {'view': view, 'journal': settlement.export_journal(),
                            'canonical_state': settlement.canonical_state(), 'state_digest': settlement.state_digest()},
            'credit': {'views': views, 'claim': claim, 'journal': credit.export_journal(),
                       'canonical_state': credit.canonical_state(), 'state_digest': credit.state_digest()},
            'variance': variance, 'shared_exposure': exposure}


def replay(inputs):
    def check_face(step, settlement, _credit):
        if step['target'] == 'credit' and step['operation'] == 'offer':
            view = settlement.view(inputs['claim_id'])
            same('COMMITTED', view['phase'])
            same(view['claim'], step['arguments']['face'])

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': inputs['setup_steps']}, observer=check_face)
    assert all('ok' in row['result'] for row in setup), 'setup must succeed'
    initial = snapshot(inputs, settlement, credit)
    methods = {'distribute': settlement.distribute, 'bind_refund': settlement.bind_refund,
               'observe_mock_cancel_acceptance': settlement.observe_mock_cancel_acceptance}
    history = []
    for step in inputs['steps']:
        try:
            result = {'ok': methods[step['operation']](**step['arguments'])}
        except SettlementError as error:
            result = {'error': {'type': type(error).__name__, 'code': error.code}}
        history.append({k: step[k] for k in ['step_id', 'target', 'operation']})
        history[-1].update(result=result, snapshot=snapshot(inputs, settlement, credit))
    assert all('ok' in row['result'] for row in history), 'history must succeed'
    return {'scenario_id': inputs['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history}


def checkpoints(scenario):
    return [scenario['initial_snapshot']] + [r['snapshot'] for r in scenario['history']]


def verify_arithmetic(inputs, scenario):
    states = checkpoints(scenario)
    same(len(inputs['expected_arithmetic']), len(states))
    for expected, current in zip(inputs['expected_arithmetic'], states):
        claim = current['settlement']['view']['claim']
        same(expected['payees'], sorted(claim['obligations'], key=lambda p: p['payee']))
        same(expected['refund'], {k: claim[k] for k in REFUND_FIELDS})
        exposure = current['shared_exposure']
        same(expected['credit'], exposure['observable'])
        for key in ['advance_count', 'claim_count', 'within_limit']:
            same(expected[key], exposure[key])
        observed = current['variance']
        same(expected['variance'], {**observed['observable'],
             **{k: observed[k] for k in ['variance', 'sign', 'within_tolerance']},
             **{k: observed['companion'][k] for k in ['cash_delta', 'recovery_delta']}})
        for payee in claim['obligations']:
            same(payee['face'], payee['distributed'] + payee['cancelled_unpaid'] + payee['outstanding'])
            assert 0 <= payee['recovery_due'] <= payee['distributed']
        same(100_000, sum(p['face'] for p in claim['obligations']))
        same(claim['refund_face'] - claim['refund_accepted'], claim['refund_outstanding'])
        same(100_000, current['credit']['claim']['open_face'])
        same(100_000, current['credit']['claim']['reserved_open'])
        same(0, current['credit']['claim']['residual_unreserved'])
        for amount, view in zip([60_000, 40_000], current['credit']['views']):
            same(['DRAWN', True, amount, 0, amount, 100_000, 100_000, 0],
                 [view[k] for k in ['phase', 'snapshot_frozen', 'drawn_exposure', 'repaid_exposure',
                                    'outstanding_exposure', 'open_face', 'reserved_open', 'residual_unreserved']])
        same(states[0]['credit'], current['credit'])
        same(states[0]['shared_exposure'], exposure)


def verify_semantics(fixture, vectors):
    """Detached checks: no outer fixture/vector byte pins are needed here."""
    validate_fixture(fixture)
    exact_fields(vectors, {'vector_version', 'fixture_sha256', 'source_pins', 'scenarios'}, 'vectors')
    same(VERSION, vectors['vector_version'])
    same(sha(canonical(fixture)), vectors['fixture_sha256'])
    verify_sources(vectors['source_pins'])
    actual = [replay(s) for s in fixture['scenarios']]
    same(vectors['scenarios'], actual)
    for inputs, scenario in zip(fixture['scenarios'], actual):
        verify_arithmetic(inputs, scenario)
    return actual


class CapitalRefundCompositionVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(FIXTURE)
        cls.vectors = load(VECTORS)
        validate_fixture(cls.fixture)
        cls.actual = [replay(s) for s in cls.fixture['scenarios']]

    def test_artifact_and_source_pins(self):
        same(FIXTURE_SHA256, sha(FIXTURE.read_bytes()))
        same(VECTORS_SHA256, sha(VECTORS.read_bytes()))
        same(FIXTURE_SHA256, self.vectors['fixture_sha256'])
        verify_sources(self.vectors['source_pins'])
        for inputs in self.fixture['scenarios']:
            for citation in inputs['source_tests']:
                path, name = citation.split('::')
                cls, method = name.split('.')
                tree = ast.parse((ROOT / path).read_text())
                node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
                self.assertIn(method, {n.name for n in node.body if isinstance(n, ast.FunctionDef)})
        with self.assertRaises(FixtureError):
            decode_json('{"duplicate":1,"duplicate":2}')

    def test_complete_history_vectors(self):
        same(self.actual, verify_semantics(self.fixture, self.vectors))

    def test_full_refund_per_payee(self):
        states = checkpoints(self.actual[0])
        same([0, -10_000, -100_000, -100_000], [s['variance']['variance'] for s in states])
        same([0, 0, 10_000, 10_000], [s['variance']['companion']['recovery_delta'] for s in states])
        for current in states[2:]:
            claim = current['settlement']['view']['claim']
            same('FIXTURE_FULL_GROSS_RECLASS', claim['refund_bearer_policy'])
            self.assertIs(claim['fixture_reclassified'], True)
            payees = {p['payee']: p for p in claim['obligations']}
            same([5000, 0, 5000, 0], [payees['fee-r1'][k] for k in
                                     ['distributed', 'cancelled_unpaid', 'recovery_due', 'outstanding']])
            same([5000, 90_000, 5000, 0], [payees['res-r1'][k] for k in
                                         ['distributed', 'cancelled_unpaid', 'recovery_due', 'outstanding']])

    def test_cumulative_refunds_remain_requester(self):
        states = checkpoints(self.actual[1])
        same([0] + [-60_000] * 6, [s['variance']['variance'] for s in states])
        for current in states[2:]:
            claim = current['settlement']['view']['claim']
            same(['REQUESTER', False, False], [claim[k] for k in
                 ['refund_bearer_policy', 'fixture_reclassified', 'distribution_blocked']])
            same([0, 0], [p['recovery_due'] for p in claim['obligations']])
            same([0, 0], [p['cancelled_unpaid'] for p in claim['obligations']])
        # Claim-level acceptance never invents a refund_id allocation.
        for inputs, actual in zip(self.fixture['scenarios'], self.actual):
            journal = actual['history'][-1]['snapshot']['settlement']['journal']
            for operation in ['bind_refund', 'observe_mock_cancel_acceptance']:
                expected = [{k: v for k, v in s['arguments'].items()
                             if k not in ['settlement_id', 'idempotency_key']}
                            for s in inputs['steps'] if s['operation'] == operation]
                same(expected, [r['body'] for r in journal if r['op'] == operation])
        same({'fee-r2': 0, 'res-r2': 0}, self.actual[1]['history'][-1]['result']['ok']['effect'])

    def test_settlement_actions_preserve_credit(self):
        for inputs, actual in zip(self.fixture['scenarios'], self.actual):
            verify_arithmetic(inputs, actual)
            initial = actual['initial_snapshot']
            offers = [s for s in inputs['setup_steps'] if s['operation'] == 'offer']
            for entry, offer in zip([r for r in initial['credit']['journal'] if r['op'] == 'offer'], offers):
                same(initial['settlement']['view']['claim'], entry['body']['face'])
                same(offer['arguments']['face'], entry['body']['face'])
            for current in checkpoints(actual):
                same(initial['credit'], current['credit'])
                same(initial['shared_exposure'], current['shared_exposure'])
                for producer in ['settlement', 'credit']:
                    same(sha(current[producer]['canonical_state'].encode()), current[producer]['state_digest'])
            self.assertNotEqual(initial['settlement']['journal'], actual['history'][-1]['snapshot']['settlement']['journal'])

    def test_observation_boundaries(self):
        flags = {'funds_executed', 'bank_debit_observed', 'economic_finality_claimed',
                 'repayment_observed', 'legal_debtor_bound', 'durable', 'underwriting_executed',
                 'kyc_executed', 'interest_defined', 'collateral_perfected', 'priority_bound',
                 'ownership_mutated', 'ticket_ownership_authoritative', 'admission_granted',
                 'external_return_closed', 'right_cancelled'}

        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in flags:
                        self.assertIs(item, False, key)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(self.actual)
        for inputs, actual in zip(self.fixture['scenarios'], self.actual):
            for current in checkpoints(actual):
                detached = copy.deepcopy(current)
                same(current['variance'], observe_settlement_variance(
                    detached['settlement']['view']['claim'], detached['credit']['claim'],
                    tolerance=inputs['tolerance']))
                same(current['shared_exposure'], observe_shared_exposure(
                    inputs['group_id'], detached['credit']['views'], limit=inputs['limit']))
                same(current, detached)
                for name, code in [('variance', 'SETTLEMENT_VARIANCE_NOT_BOUND'),
                                    ('shared_exposure', 'SHARED_EXPOSURE_NOT_BOUND')]:
                    observed = current[name]
                    same({'code': code, 'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observed['mapping'])
                    same([True, False, False, 'NOT_BOUND'], [observed[k] for k in
                         ['fail_closed', 'mutates_state', 'authorizes_exposure', 'refund_component']])

    def test_verifier_sensitivity(self):
        def history(v, i=0):
            return v['scenarios'][i]['history']

        def allocations(v):
            # Preserve aggregate totals while lying about each payee's recovery.
            lines = history(v)[1]['snapshot']['settlement']['view']['claim']['obligations']
            lines[0].update(distributed=4999, cancelled_unpaid=1, recovery_due=4999)
            lines[1].update(distributed=5001, cancelled_unpaid=89999, recovery_due=5001)

        mutations = [
            allocations,
            lambda v: history(v, 1)[2]['snapshot']['settlement']['view']['claim'].update(
                fixture_reclassified=True, refund_bearer_policy='FIXTURE_FULL_GROSS_RECLASS'),
            lambda v: history(v)[1]['snapshot']['credit']['claim'].update(open_face=0),
            lambda v: history(v)[1]['snapshot']['credit']['views'][0].update(snapshot_frozen=False),
            lambda v: history(v)[1]['snapshot']['credit']['journal'].pop(),
            lambda v: history(v)[1]['snapshot']['shared_exposure']['observable'].update(group_open_face=200_000),
            lambda v: history(v, 1).pop(2),
            lambda v: history(v, 1).pop(3),
            lambda v: history(v, 1).reverse(),
            lambda v: v['scenarios'][0]['setup_results'].reverse(),
            lambda v: v['source_pins'].pop(),
            lambda v: v['source_pins'][0].update(sha256='0' * 64),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(vector_mutation=index):
                changed = copy.deepcopy(self.vectors)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    verify_semantics(self.fixture, changed)
        # These also fail the literal arithmetic/invariance verifier directly,
        # independent of both byte pins and complete replay equality.
        for mutate, index in [(allocations, 0), (mutations[1], 1),
                              (mutations[2], 0), (mutations[3], 0),
                              (mutations[4], 0), (mutations[5], 0)]:
            changed = copy.deepcopy(self.vectors)
            mutate(changed)
            with self.assertRaises(AssertionError):
                verify_arithmetic(self.fixture['scenarios'][index], changed['scenarios'][index])
        for path in SOURCE_PATHS:
            with self.subTest(source=path):
                def reader(candidate):
                    raw = read_bootstrap_2_input(candidate)
                    return raw + b'\n' if candidate == path else raw
                with self.assertRaises(AssertionError):
                    verify_sources(self.vectors['source_pins'], reader)
        mutations = [
            lambda s: s['steps'].pop(1),
            lambda s: s['steps'].reverse(),
            lambda s: s['steps'][0]['arguments']['order'].reverse(),
            lambda s: s['setup_steps'][4]['arguments']['face'].update(confirmed_cash=1),
            lambda s: s['expected_arithmetic'][1]['payees'][0].update(distributed=4999),
            lambda s: s['expected_arithmetic'][2]['refund'].update(fixture_reclassified=False),
            lambda s: s['steps'][1]['arguments'].update(amount=30_000),
            lambda s: s['steps'][2]['arguments'].update(source_id='altered-acceptance'),
            lambda s: s['steps'][0].update(operation='reconcile'),
            lambda s: s['steps'][1]['arguments'].update(idempotency_key=s['steps'][0]['arguments']['idempotency_key']),
            lambda s: s['expected_arithmetic'][0]['credit'].update(group_open_face=True),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(fixture_mutation=index):
                changed = copy.deepcopy(self.fixture)
                mutate(changed['scenarios'][0])
                vectors = copy.deepcopy(self.vectors)
                vectors['fixture_sha256'] = sha(canonical(changed))
                with self.assertRaises((AssertionError, FixtureError)):
                    verify_semantics(changed, vectors)
        for step_index in [1, 2, 3, 4]:
            with self.subTest(r2_omitted_refund_or_acceptance=step_index):
                changed = copy.deepcopy(self.fixture)
                changed['scenarios'][1]['steps'].pop(step_index)
                vectors = copy.deepcopy(self.vectors)
                vectors['fixture_sha256'] = sha(canonical(changed))
                with self.assertRaises(AssertionError):
                    verify_semantics(changed, vectors)
        for a, b in [(1, 2), (3, 4)]:
            with self.subTest(r2_reordered_refunds_or_acceptance=(a, b)):
                changed = copy.deepcopy(self.fixture)
                steps = changed['scenarios'][1]['steps']
                steps[a], steps[b] = steps[b], steps[a]
                vectors = copy.deepcopy(self.vectors)
                vectors['fixture_sha256'] = sha(canonical(changed))
                with self.assertRaises(AssertionError):
                    verify_semantics(changed, vectors)


if __name__ == '__main__':
    unittest.main()
