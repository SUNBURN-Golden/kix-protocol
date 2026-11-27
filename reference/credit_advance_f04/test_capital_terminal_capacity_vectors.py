"""Source-informed, test-only portable F04 close/default histories.

Golden captures are constrained by separately stated arithmetic, not an
independent FSM. Tests read artifacts and never regenerate expected outputs.
"""
from __future__ import annotations

import ast
import copy
import sys
import unittest

from scripts.bootstrap_2_fixtures import read_bootstrap_2_input
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_fixture import exact_fields  # noqa: E402
from credit_fsm import CreditError, CreditMachine  # noqa: E402
from settlement_credit_boundary_vectors import (  # noqa: E402
    canonical, replay_scenario_with_state,
)
from shared_exposure import EXPOSURE_PHASES, observe_shared_exposure  # noqa: E402
from test_capital_operation_replay_vectors import (  # noqa: E402
    PROVENANCE, SETUP_FIELDS, SOURCE_PATHS as REUSED_SOURCES,
    load, same, sha, snapshot,
)

FIXTURE = HERE / 'fixtures/capital_terminal_capacity_v1.json'
VECTORS = HERE / 'fixtures/capital_terminal_capacity_vectors_v1.json'
VERSION = 'capital-terminal-capacity/1'
FIXTURE_SHA256 = '6141cdd29e398856c8be91b4edc369742f654446b771662b53129aa471ea03a7'
VECTORS_SHA256 = 'a2af57887d5fa17679a0634da9e320d6362e7df24c44695791971b97a336bd69'
SOURCE_PATHS = REUSED_SOURCES + (
    'reference/credit_advance_f04/test_capital_operation_replay_vectors.py',
    'reference/credit_advance_f04/fixtures/capital_operation_replay_v1.json',
    'reference/credit_advance_f04/fixtures/capital_operation_replay_vectors_v1.json',
    'reference/credit_advance_f04/fixtures/shared_exposure_v1.json',
)
CONTRACTS = ['docs/contracts/CREDIT_ADVANCE_F04.md#7.2',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.3',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.4',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.12',
             'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md']
INVENTORY = (
    ('T1_repay_close_capacity_reuse', (
        'test_close_rejects_remaining_exposure_before_release',
        'test_repayment_order_partial_and_double_application',
        'test_limit_race_is_ordered_and_cash_is_not_capacity')),
    ('T2_default_retains_capacity', (
        'test_default_keeps_the_reservation_and_does_not_foreclose',)),
)
HISTORY_FIELDS = {
    'draw': {'advance_id', 'idempotency_key', 'draw_id'},
    'repay': {'advance_id', 'idempotency_key', 'repay_id', 'sequence', 'amount'},
    'close': {'advance_id', 'idempotency_key'},
    'default': {'advance_id', 'idempotency_key', 'reason'},
    'reconcile': {'advance_id', 'idempotency_key'},
}
VIEW_FIELDS = {'advance_id', 'phase', 'note_status', 'drawn_exposure',
               'repaid_exposure', 'outstanding_exposure'}
TOTAL_FIELDS = {'group_drawn_exposure', 'group_repaid_exposure',
                'group_outstanding_exposure', 'group_open_face',
                'group_reserved_open', 'group_residual_unreserved'}


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_TERMINAL_CAPACITY_VECTORS', True, PROVENANCE],
         [fixture['fixture_version'], fixture['fixture_kind'],
          fixture['synthetic_only'], fixture['provenance']])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 2
    for scenario, (identifier, methods), limit in zip(fixture['scenarios'], INVENTORY,
                                                     [70_000, 80_000]):
        exact_fields(scenario, {'scenario_id', 'source_tests', 'contracts', 'setup_steps',
                                'advance_ids', 'claim_id', 'group_id', 'limit', 'steps',
                                'expected_arithmetic'}, identifier)
        same(identifier, scenario['scenario_id'])
        same([f'reference/credit_advance_f04/test_credit_fsm.py::CreditFsmTests.{method}'
              for method in methods], scenario['source_tests'])
        same(CONTRACTS, scenario['contracts'])
        same(limit, scenario['limit'])
        ids = scenario['advance_ids']
        assert type(ids) is list and len(ids) == 3 and len(set(ids)) == 3
        for label in [*ids, scenario['claim_id'], scenario['group_id']]:
            assert type(label) is str and 0 < len(label) <= 100 and label.strip() == label
        for key, maximum in [('setup_steps', 16), ('steps', 32)]:
            steps = scenario[key]
            assert type(steps) is list and 0 < len(steps) <= maximum
            assert len({step['step_id'] for step in steps}) == len(steps)
            for step in steps:
                fields = {'step_id', 'operation', 'arguments'}
                if key == 'setup_steps':
                    fields.add('target')
                exact_fields(step, fields, 'step')
                selector = ((step['target'], step['operation']) if key == 'setup_steps'
                            else step['operation'])
                allowed = SETUP_FIELDS if key == 'setup_steps' else HISTORY_FIELDS
                assert selector in allowed, 'operation outside bounded replay'
                exact_fields(step['arguments'], allowed[selector], 'arguments')
                assert type(step['step_id']) is str and step['step_id']
                if 'advance_id' in step['arguments']:
                    assert step['arguments']['advance_id'] in ids
                if 'settlement_id' in step['arguments']:
                    same(scenario['claim_id'], step['arguments']['settlement_id'])
        same(['initial'] + [step['step_id'] for step in scenario['steps']],
             [row['step_id'] for row in scenario['expected_arithmetic']])
        for row in scenario['expected_arithmetic']:
            exact_fields(row, {'step_id', 'observable', 'advance_count', 'claim_count',
                               'within_limit', 'advances'}, 'arithmetic')
            exact_fields(row['observable'], TOTAL_FIELDS, 'observable')
            same(ids, [view['advance_id'] for view in row['advances']])
            for view in row['advances']:
                exact_fields(view, VIEW_FIELDS, 'advance arithmetic')


def verify_sources(pins, reader=None):
    reader = read_bootstrap_2_input if reader is None else reader
    assert type(pins) is list
    same(list(SOURCE_PATHS), [pin['path'] for pin in pins])
    for pin in pins:
        exact_fields(pin, {'path', 'sha256'}, 'source pin')
        same(pin['sha256'], sha(reader(pin['path'])))


def dispatch(credit, step):
    methods = {'draw': credit.draw, 'repay': credit.repay, 'close': credit.close,
               'default': credit.default, 'reconcile': credit.reconcile}
    try:
        return {'ok': methods[step['operation']](**step['arguments'])}
    except CreditError as error:
        return {'error': {'type': type(error).__name__, 'code': error.code}}


def replay(scenario):
    def check_face(step, settlement, _credit):
        if step['target'] == 'credit' and step['operation'] == 'offer':
            same('COMMITTED', settlement.view(scenario['claim_id'])['phase'])
            same(settlement.view(scenario['claim_id'])['claim'], step['arguments']['face'])

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': scenario['setup_steps']}, observer=check_face)
    assert all('ok' in row['result'] for row in setup)
    initial = snapshot(scenario, settlement, credit)
    history = []
    for step in scenario['steps']:
        result = dispatch(credit, step)
        history.append({'step_id': step['step_id'], 'result': result,
                        'snapshot': snapshot(scenario, settlement, credit)})
    restored = CreditMachine.restore(credit.export_journal(), settlement_source=settlement)
    before = snapshot(scenario, settlement, restored)
    accepted_replays = []
    for step, row in zip(scenario['setup_steps'] + scenario['steps'], setup + history):
        result = row['result'].get('ok', {})
        if (step['operation'] in HISTORY_FIELDS and step['operation'] != 'reconcile'
                and result.get('duplicate') is False):
            accepted_replays.append({'step_id': step['step_id'],
                                     'result': dispatch(restored, step)})
    after = snapshot(scenario, settlement, restored)
    try:
        CreditMachine.restore(credit.export_journal())
    except CreditError as error:
        missing_source = {'error': {'type': type(error).__name__, 'code': error.code}}
    else:
        raise AssertionError('bound draw restored without settlement source')
    return {'scenario_id': scenario['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history,
            'restore_checks': {'before': before, 'accepted_replays': accepted_replays,
                               'after': after, 'without_source': missing_source}}


def checkpoints(scenario):
    return [scenario['initial_snapshot']] + [row['snapshot'] for row in scenario['history']]


def verify_arithmetic(inputs, scenario):
    for expected, current in zip(inputs['expected_arithmetic'], checkpoints(scenario)):
        observed = current['shared_exposure']
        for field in ['observable', 'advance_count', 'claim_count', 'within_limit']:
            same(expected[field], observed[field])
        same(expected['advances'], [{key: view[key] for key in VIEW_FIELDS}
                                    for view in current['credit']['views']])
        same(expected['observable']['group_reserved_open'],
             current['credit']['claim']['reserved_open'])
        same(expected['observable']['group_residual_unreserved'],
             current['credit']['claim']['residual_unreserved'])


def verify_semantics(fixture, vectors):
    """Detached semantic checks deliberately bypass the outer artifact hashes."""
    validate_fixture(fixture)
    exact_fields(vectors, {'vector_version', 'fixture_sha256', 'source_pins',
                           'scenarios'}, 'vectors')
    same(VERSION, vectors['vector_version'])
    same(sha(canonical(fixture)), vectors['fixture_sha256'])
    verify_sources(vectors['source_pins'])
    actual = [replay(scenario) for scenario in fixture['scenarios']]
    same(vectors['scenarios'], actual)
    for inputs, scenario in zip(fixture['scenarios'], actual):
        verify_arithmetic(inputs, scenario)
    return actual


class CapitalTerminalCapacityVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(FIXTURE)
        cls.vectors = load(VECTORS)
        validate_fixture(cls.fixture)
        cls.actual = [replay(scenario) for scenario in cls.fixture['scenarios']]

    def test_artifact_and_source_pins(self):
        same(FIXTURE_SHA256, sha(FIXTURE.read_bytes()))
        same(VECTORS_SHA256, sha(VECTORS.read_bytes()))
        same(FIXTURE_SHA256, self.vectors['fixture_sha256'])
        verify_sources(self.vectors['source_pins'])

    def test_history_inventory_and_citations(self):
        tree = ast.parse((HERE / 'test_credit_fsm.py').read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'CreditFsmTests')
        methods = {node.name for node in cls.body if isinstance(node, ast.FunctionDef)}
        for _identifier, citations in INVENTORY:
            for method in citations:
                self.assertIn(method, methods)

    def test_complete_history_vectors(self):
        same(self.actual, verify_semantics(self.fixture, self.vectors))

    def test_terminal_refusals_preserve_public_state(self):
        expected_codes = [
            ['ADVANCE_EXCEEDS_OPEN_FACE', 'OUTSTANDING_REMAINS',
             'ADVANCE_EXCEEDS_OPEN_FACE', 'DEFAULT_REQUIRES_EXPOSURE',
             'OUTSTANDING_REMAINS', 'ADVANCE_EXCEEDS_OPEN_FACE',
             'TERMINAL_IMMUTABLE', 'TERMINAL_IMMUTABLE', 'TERMINAL_IMMUTABLE',
             'TERMINAL_IMMUTABLE'],
            ['ADVANCE_EXCEEDS_OPEN_FACE', 'TERMINAL_IMMUTABLE',
             'TERMINAL_IMMUTABLE', 'TERMINAL_IMMUTABLE', 'TERMINAL_IMMUTABLE'],
        ]
        for scenario, codes in zip(self.actual, expected_codes):
            before = scenario['initial_snapshot']
            actual_codes = []
            for row in scenario['history']:
                result = row['result']
                if 'error' in result or result.get('ok', {}).get('duplicate') is True:
                    same(before, row['snapshot'])
                if 'error' in result:
                    same('CreditError', result['error']['type'])
                    actual_codes.append(result['error']['code'])
                before = row['snapshot']
            same(codes, actual_codes)

    def test_repayment_close_capacity_arithmetic(self):
        for inputs, scenario in zip(self.fixture['scenarios'], self.actual):
            verify_arithmetic(inputs, scenario)
        rows = {row['step_id']: row for row in self.actual[0]['history']}
        paid = rows['repay-rest']['snapshot']['credit']
        closed = rows['close-fresh']['snapshot']['credit']
        same(70_000, paid['claim']['reserved_open'])
        same(30_000, closed['claim']['reserved_open'])
        same(40_000, paid['claim']['reserved_open'] - closed['claim']['reserved_open'])
        same(paid['views'][1]['outstanding_exposure'], closed['views'][1]['outstanding_exposure'])
        same([110_000, 40_000, 70_000, 70_000],
             [rows['draw-c-fresh']['snapshot']['shared_exposure']['observable'][key]
              for key in ['group_drawn_exposure', 'group_repaid_exposure',
                          'group_outstanding_exposure', 'group_reserved_open']])

    def test_default_retains_shared_exposure(self):
        rows = {row['step_id']: row for row in self.actual[1]['history']}
        before = rows['repay-part']['snapshot']
        after = rows['default-a']['snapshot']
        same(before['shared_exposure'], after['shared_exposure'])
        view = after['credit']['views'][0]
        same(['DEFAULTED', 'NOTED', 50_000, 100_000],
             [view[key] for key in ['phase', 'note_status', 'outstanding_exposure', 'reserved_open']])
        same(80_000, after['shared_exposure']['observable']['group_outstanding_exposure'])

    def test_historical_receipts_and_restore(self):
        for inputs, scenario in zip(self.fixture['scenarios'], self.actual):
            first_by_key = {}
            for step, row in zip(inputs['setup_steps'] + inputs['steps'],
                                 scenario['setup_results'] + scenario['history']):
                key = step['arguments']['idempotency_key']
                receipt = row['result'].get('ok')
                if receipt is None:
                    continue
                if key in first_by_key:
                    expected = copy.deepcopy(first_by_key[key])
                    expected.update(duplicate=True, applied=None)
                    same(expected, receipt)
                else:
                    first_by_key[key] = receipt
            checks = scenario['restore_checks']
            same(scenario['history'][-1]['snapshot'], checks['before'])
            same(checks['before'], checks['after'])
            same({'error': {'type': 'CreditError', 'code': 'SETTLEMENT_SOURCE_REQUIRED'}},
                 checks['without_source'])
            steps = {step['step_id']: step for step in inputs['setup_steps'] + inputs['steps']}
            for row in checks['accepted_replays']:
                original = first_by_key[steps[row['step_id']]['arguments']['idempotency_key']]
                expected = copy.deepcopy(original)
                expected.update(duplicate=True, applied=None)
                same(expected, row['result']['ok'])
            rejected = {step['arguments']['idempotency_key']
                        for step, row in zip(inputs['steps'], scenario['history'])
                        if 'error' in row['result']}
            self.assertTrue(rejected.isdisjoint(
                entry['idempotency_key'] for entry in checks['before']['credit']['journal']))
        rows = {row['step_id']: row for row in self.actual[0]['history']}
        same('DRAWN', rows['late-draw-replay']['result']['ok']['credit']['phase'])
        same(40_000, rows['late-draw-replay']['result']['ok']['credit']['outstanding_exposure'])
        same('CLOSED', rows['late-draw-replay']['snapshot']['credit']['views'][0]['phase'])
        same(0, rows['late-draw-replay']['snapshot']['credit']['views'][0]['outstanding_exposure'])
        rows = {row['step_id']: row for row in self.actual[1]['history']}
        same(80_000, rows['default-a']['snapshot']['shared_exposure']['observable']
             ['group_outstanding_exposure'])
        same(70_000, rows['late-default-replay']['snapshot']['shared_exposure']['observable']
             ['group_outstanding_exposure'])
        same(30_000, rows['default-a']['snapshot']['credit']['views'][1]['outstanding_exposure'])
        same(20_000, rows['late-default-replay']['snapshot']['credit']['views'][1]
             ['outstanding_exposure'])

    def test_frozen_faces_and_captured_observations(self):
        # Observe detached golden views directly, not only regenerated machine views.
        for inputs, scenario in zip(self.fixture['scenarios'], self.vectors['scenarios']):
            offered_faces = [step['arguments']['face'] for step in inputs['setup_steps']
                             if step['operation'] == 'offer']
            capacity_fields = {'reserved_open', 'residual_unreserved'}
            frozen_claim = {key: value for key, value in
                            scenario['initial_snapshot']['credit']['claim'].items()
                            if key not in capacity_fields}
            for current in checkpoints(scenario):
                same(scenario['initial_snapshot']['settlement'], current['settlement'])
                for face in offered_faces:
                    same(current['settlement']['view']['claim'], face)
                claim = current['credit']['claim']
                self.assertIs(claim['snapshot_frozen'], True)
                same(frozen_claim, {key: value for key, value in claim.items()
                                    if key not in capacity_fields})
                for view in current['credit']['views']:
                    same([100_000, 97_000, claim['reserved_open'], claim['residual_unreserved']],
                         [view[key] for key in ['open_face', 'confirmed_cash_on_face',
                                              'reserved_open', 'residual_unreserved']])
                for entry in current['credit']['journal']:
                    if entry['op'] == 'offer':
                        same(offered_faces[0], entry['body']['face'])
                for producer in ['settlement', 'credit']:
                    same(sha(current[producer]['canonical_state'].encode('utf-8')),
                         current[producer]['state_digest'])
                views = copy.deepcopy([view for view in current['credit']['views']
                                       if view['snapshot_frozen'] is True
                                       and view['phase'] in EXPOSURE_PHASES])
                before = canonical(views)
                observed = observe_shared_exposure(inputs['group_id'], views, limit=inputs['limit'])
                same(current['shared_exposure'], observed)
                self.assertEqual(before, canonical(views))
                same(1, observed['claim_count'])
                same(100_000, observed['observable']['group_open_face'])

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
        for scenario in self.actual:
            for current in checkpoints(scenario):
                observed = current['shared_exposure']
                same({'code': 'SHARED_EXPOSURE_NOT_BOUND', 'contract_status': 'NOT_BOUND',
                      'repair': 'NONE'}, observed['mapping'])
                same([True, False, False, 'NOT_BOUND'],
                     [observed[key] for key in ['fail_closed', 'mutates_state',
                                               'authorizes_exposure', 'refund_component']])

    def test_verifier_sensitivity(self):
        mutations = [
            lambda v: v['scenarios'][0]['history'][0]['result']['error'].update(code='ALTERED'),
            lambda v: v['scenarios'][0]['history'][1]['result']['ok'].update(duplicate=True),
            lambda v: v['scenarios'][0]['history'][1]['result']['ok'].update(applied=None),
            lambda v: v['scenarios'][0]['history'][1]['snapshot']['credit']['views'][0]
                         .update(phase='CLOSED'),
            lambda v: v['scenarios'][0]['history'][1]['snapshot']['credit']['claim']
                         .update(reserved_open=55_000),
            lambda v: v['source_pins'][0].update(sha256='0' * 64),
            lambda v: v['source_pins'].pop(),
            lambda v: v['scenarios'][0]['history'].pop(1),
            lambda v: v['scenarios'][0]['history'].reverse(),
        ]
        for field in TOTAL_FIELDS:
            mutations.append(lambda v, field=field: v['scenarios'][0]['history'][1]
                             ['snapshot']['shared_exposure']['observable'].update({field: 1}))
        for index, mutate in enumerate(mutations):
            with self.subTest(vector_mutation=index):
                changed = copy.deepcopy(self.vectors)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    verify_semantics(self.fixture, changed)
        for path in SOURCE_PATHS:
            with self.subTest(source_bytes=path):
                def altered_reader(candidate):
                    raw = read_bootstrap_2_input(candidate)
                    return raw + b'\n' if candidate == path else raw
                with self.assertRaises(AssertionError):
                    verify_sources(self.vectors['source_pins'], altered_reader)
        # Keep fixture-hash consistency for these controls so arithmetic/ordering
        # checks, rather than an outer digest mismatch, must detect the mutation.
        def omit_step(scenario):
            scenario['steps'].pop(1)
            scenario['expected_arithmetic'].pop(2)

        def reorder_steps(scenario):
            for key, offset in [('steps', 0), ('expected_arithmetic', 1)]:
                rows = scenario[key]
                rows[1 + offset], rows[3 + offset] = rows[3 + offset], rows[1 + offset]

        fixture_mutations = [
            omit_step,
            reorder_steps,
            lambda s: s['expected_arithmetic'][1]['observable'].update(group_reserved_open=1),
            lambda s: s['expected_arithmetic'][1]['advances'][0].update(phase='CLOSED'),
        ]
        for index, mutate in enumerate(fixture_mutations):
            with self.subTest(fixture_mutation=index):
                changed = copy.deepcopy(self.fixture)
                mutate(changed['scenarios'][0])
                vectors = copy.deepcopy(self.vectors)
                vectors['fixture_sha256'] = sha(canonical(changed))
                with self.assertRaises(AssertionError):
                    verify_semantics(changed, vectors)
        for key, operation in [('steps', 'cancel'), ('setup_steps', 'default')]:
            changed = copy.deepcopy(self.fixture)
            changed['scenarios'][0][key][0]['operation'] = operation
            with self.assertRaises(AssertionError):
                validate_fixture(changed)


if __name__ == '__main__':
    unittest.main()
