"""Source-informed portable mutation histories; all replay helpers are test-only.

Golden outputs are captured public results, not an independent implementation.
Separately stated arithmetic and invariant checks constrain those captures.
Tests read fixtures; they never regenerate them or mutate producer files.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from credit_fixture import decode_json, exact_fields  # noqa: E402
from credit_fsm import CreditError, CreditMachine  # noqa: E402
from settlement_credit_boundary_vectors import (  # noqa: E402
    canonical, replay_scenario_with_state,
)
from shared_exposure import EXPOSURE_PHASES, observe_shared_exposure  # noqa: E402

FIXTURE = HERE / 'fixtures/capital_operation_replay_v1.json'
VECTORS = HERE / 'fixtures/capital_operation_replay_vectors_v1.json'
FIXTURE_SHA256 = '831125251e5e0b1767cda4dba444f2c6d391403ba975ef05f17b475eeb124599'
VECTORS_SHA256 = 'a1562367abf9f4de1fcb180786423b9df4a7740da9563c7de2daeebc397005c7'
VERSION = 'capital-operation-replay/1'
PROVENANCE = {'settlement': 'MOCK_SETTLEMENT_ONLY', 'credit': 'MOCK_CREDIT_F04_ONLY'}
SOURCE_PATHS = (
    'docs/contracts/CREDIT_ADVANCE_F04.md',
    'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md',
    'reference/settlement_f01_f03/mock_settlement.py',
    'reference/settlement_f01_f03/settlement_fsm.py',
    'reference/credit_advance_f04/mock_credit.py',
    'reference/credit_advance_f04/credit_fsm.py',
    'reference/credit_advance_f04/open_terms.py',
    'reference/credit_advance_f04/credit_fixture.py',
    'reference/credit_advance_f04/credit_session.py',
    'reference/credit_advance_f04/settlement_credit_boundary_vectors.py',
    'reference/credit_advance_f04/shared_exposure.py',
    'reference/credit_advance_f04/test_credit_fsm.py',
    'reference/credit_advance_f04/test_credit_rejection_atomicity.py',
    'reference/credit_advance_f04/test_settlement_credit_boundary.py',
    'reference/credit_advance_f04/test_shared_exposure_contract.py',
    'reference/credit_advance_f04/fixtures/settlement_credit_boundary_v1.json',
)
INVENTORY = (
    ('R1_note_identity_and_historical_receipts',
     'test_same_draw_and_repay_notes_do_not_apply_twice'),
    ('R2_repayment_sequence_refusals',
     'test_repayment_order_partial_and_double_application'),
    ('R3_reconcile_restore_replay',
     'test_reconcile_replays_the_journal_without_a_second_draw'),
)
CONTRACTS = ['docs/contracts/CREDIT_ADVANCE_F04.md#7.2',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.3',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.4',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.5',
             'docs/contracts/CREDIT_ADVANCE_F04.md#7.12',
             'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md']
HISTORY_FIELDS = {
    'draw': {'advance_id', 'idempotency_key', 'draw_id'},
    'repay': {'advance_id', 'idempotency_key', 'repay_id', 'sequence', 'amount'},
    'reconcile': {'advance_id', 'idempotency_key'},
}
SETUP_FIELDS = {
    ('settlement', 'initiate'): {'settlement_id', 'idempotency_key', 'trade_id',
                               'gross', 'debtor_role', 'policy', 'currency'},
    ('settlement', 'authorize'): {'settlement_id', 'idempotency_key'},
    ('settlement', 'capture'): {'settlement_id', 'idempotency_key'},
    ('settlement', 'commit'): {'settlement_id', 'idempotency_key', 'movement_id',
                             'gross', 'amount', 'fee', 'tax', 'held', 'adjustment'},
    ('credit', 'offer'): {'advance_id', 'idempotency_key', 'face', 'amount',
                          'beneficiary_role'},
    ('credit', 'approve'): {'advance_id', 'idempotency_key'},
    ('credit', 'bind_settlement'): {'advance_id', 'idempotency_key', 'settlement_id'},
    ('credit', 'draw'): HISTORY_FIELDS['draw'],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def same(expected, actual):
    """Canonical equality also distinguishes JSON booleans from integers."""
    if canonical(expected) != canonical(actual):
        raise AssertionError('complete canonical value mismatch')


def load(path):
    raw = path.read_bytes()
    value = decode_json(raw.decode('utf-8'))
    if raw != canonical(value):
        raise AssertionError(f'{path.name} is not canonical JSON')
    return value


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_OPERATION_REPLAY_VECTORS', True, PROVENANCE],
         [fixture['fixture_version'], fixture['fixture_kind'],
          fixture['synthetic_only'], fixture['provenance']])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 3
    for scenario, (identifier, method) in zip(fixture['scenarios'], INVENTORY):
        exact_fields(scenario, {'scenario_id', 'source_tests', 'contracts',
                                'setup_steps', 'advance_ids', 'claim_id',
                                'group_id', 'limit', 'steps', 'expected_arithmetic'},
                     identifier)
        same(identifier, scenario['scenario_id'])
        same([f'reference/credit_advance_f04/test_credit_fsm.py::CreditFsmTests.{method}'],
             scenario['source_tests'])
        same(CONTRACTS, scenario['contracts'])
        assert type(scenario['limit']) is int and scenario['limit'] >= 0
        ids = scenario['advance_ids']
        assert type(ids) is list and 1 <= len(ids) <= 2 and len(set(ids)) == len(ids)
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
                op = step['operation']
                selector = (step['target'], op) if key == 'setup_steps' else op
                allowed = SETUP_FIELDS if key == 'setup_steps' else HISTORY_FIELDS
                assert selector in allowed, 'operation outside bounded replay'
                exact_fields(step['arguments'], allowed[selector], 'arguments')
                assert type(step['step_id']) is str and step['step_id']
                if 'advance_id' in step['arguments']:
                    assert step['arguments']['advance_id'] in ids
                if 'settlement_id' in step['arguments']:
                    assert step['arguments']['settlement_id'] == scenario['claim_id']
        same(['initial'] + [step['step_id'] for step in scenario['steps']],
             [row['step_id'] for row in scenario['expected_arithmetic']])


def verify_sources(pins, reader=None):
    reader = (lambda path: (ROOT / path).read_bytes()) if reader is None else reader
    assert type(pins) is list
    same(list(SOURCE_PATHS), [pin['path'] for pin in pins])
    for pin in pins:
        exact_fields(pin, {'path', 'sha256'}, 'source pin')
        same(pin['sha256'], sha(reader(pin['path'])))


def snapshot(scenario, settlement, credit):
    # Capture every advance at this one observation point before aggregating.
    views = [credit.view(identifier) for identifier in scenario['advance_ids']]
    frozen = [view for view in views
              if view['snapshot_frozen'] is True and view['phase'] in EXPOSURE_PHASES]
    return {
        'settlement': {
            'view': settlement.view(scenario['claim_id']),
            'journal': settlement.export_journal(),
            'canonical_state': settlement.canonical_state(),
            'state_digest': settlement.state_digest(),
        },
        'credit': {
            'views': views,
            'claim': credit.view_claim(scenario['claim_id']),
            'journal': credit.export_journal(),
            'canonical_state': credit.canonical_state(),
            'state_digest': credit.state_digest(),
        },
        'shared_exposure': observe_shared_exposure(
            scenario['group_id'], frozen, limit=scenario['limit']),
    }


def dispatch(credit, step):
    # Explicit selectors: no arbitrary attribute dispatch, adapter or command.
    methods = {'draw': credit.draw, 'repay': credit.repay, 'reconcile': credit.reconcile}
    try:
        return {'ok': methods[step['operation']](**step['arguments'])}
    except CreditError as error:
        return {'error': {'type': type(error).__name__, 'code': error.code}}


def replay(scenario):
    def check_face(step, settlement, _credit):
        if step['target'] == 'credit' and step['operation'] == 'offer':
            assert settlement.view(scenario['claim_id'])['phase'] == 'COMMITTED'
            same(settlement.view(scenario['claim_id'])['claim'], step['arguments']['face'])

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': scenario['setup_steps']}, observer=check_face)
    assert all('ok' in row['result'] for row in setup), 'setup must be accepted'
    initial = snapshot(scenario, settlement, credit)
    records = []
    for step in scenario['steps']:
        result = dispatch(credit, step)
        records.append({'step_id': step['step_id'], 'result': result,
                        'snapshot': snapshot(scenario, settlement, credit)})
    journal = credit.export_journal()
    restored = CreditMachine.restore(journal, settlement_source=settlement)
    restored_before = snapshot(scenario, settlement, restored)
    original_draw = next(step for step in scenario['setup_steps']
                         if step['target'] == 'credit' and step['operation'] == 'draw')
    result = dispatch(restored, original_draw)
    restored_after = snapshot(scenario, settlement, restored)
    try:
        CreditMachine.restore(journal)
    except CreditError as error:
        missing_source = {'error': {'type': type(error).__name__, 'code': error.code}}
    else:
        raise AssertionError('bound draw restored without settlement source')
    return {'scenario_id': scenario['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': records,
            'restore_checks': {'before': restored_before, 'draw_replay': result,
                               'after': restored_after, 'without_source': missing_source}}


def verify_semantics(fixture, vectors):
    """Verify detached expected copies without relying on outer artifact hashes."""
    validate_fixture(fixture)
    exact_fields(vectors, {'vector_version', 'fixture_sha256', 'source_pins',
                           'scenarios'}, 'vectors')
    same(VERSION, vectors['vector_version'])
    same(sha(canonical(fixture)), vectors['fixture_sha256'])
    verify_sources(vectors['source_pins'])
    actual = [replay(scenario) for scenario in fixture['scenarios']]
    same(vectors['scenarios'], actual)
    return actual


class CapitalOperationReplayVectorTests(unittest.TestCase):
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
        tree = ast.parse((ROOT / SOURCE_PATHS[11]).read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == 'CreditFsmTests')
        methods = {node.name for node in cls.body if isinstance(node, ast.FunctionDef)}
        for _identifier, method in INVENTORY:
            self.assertIn(method, methods)
        same([identifier for identifier, _method in INVENTORY],
             [scenario['scenario_id'] for scenario in self.actual])
        bool_step = next(step for step in self.fixture['scenarios'][1]['steps']
                         if step['step_id'] == 'bool-seq')
        self.assertIs(bool_step['arguments']['sequence'], True)

    def test_complete_history_vectors(self):
        same(self.actual, verify_semantics(self.fixture, self.vectors))

    def test_duplicates_preserve_current_state(self):
        count = 0
        for scenario in self.actual:
            before = scenario['initial_snapshot']
            for row in scenario['history']:
                receipt = row['result'].get('ok', {})
                if receipt.get('duplicate') is True:
                    same(before, row['snapshot'])
                    self.assertIsNone(receipt['applied'])
                    count += 1
                before = row['snapshot']
        self.assertGreaterEqual(count, 9)

    def test_refusals_preserve_public_state(self):
        codes = []
        for scenario in self.actual:
            before = scenario['initial_snapshot']
            for row in scenario['history']:
                if 'error' in row['result']:
                    same(before, row['snapshot'])
                    self.assertEqual(row['result']['error']['type'], 'CreditError')
                    codes.append(row['result']['error']['code'])
                before = row['snapshot']
        same(['IDEMPOTENCY_CONFLICT', 'DUPLICATE_DRAW', 'REPAY_BINDING_CONFLICT',
              'IDEMPOTENCY_CONFLICT', 'REPAYMENT_ORDER', 'REPAYMENT_ORDER',
              'REPAYMENT_ORDER', 'REPAYMENT_ORDER', 'REPAYMENT_EXCEEDS_OUTSTANDING',
              'REPAYMENT_EXCEEDS_OUTSTANDING'], codes)

    def test_historical_receipts_after_later_repayment(self):
        scenario = self.actual[0]
        rows = {row['step_id']: row for row in scenario['history']}
        first_draw = next(row['result']['ok'] for row in scenario['setup_results']
                          if row['step_id'] == 'draw-1')
        first_repay = rows['repay-1']['result']['ok']
        for name, original in [('late-draw-replay', first_draw),
                               ('late-repay-replay', first_repay)]:
            expected = copy.deepcopy(original)
            expected.update(duplicate=True, applied=None)
            same(expected, rows[name]['result']['ok'])
            exposure = rows[name]['snapshot']['shared_exposure']['observable']
            self.assertEqual(exposure['group_outstanding_exposure'], 50_000)
            self.assertEqual(rows[name]['snapshot']['credit']['views'][0]
                             ['outstanding_exposure'], 20_000)
        self.assertEqual(first_draw['credit']['outstanding_exposure'], 40_000)
        self.assertEqual(first_repay['credit']['outstanding_exposure'], 30_000)
        for name in ['draw-note-new-key', 'repay-note-new-key', 'late-note-new-key']:
            result = rows[name]['result']['ok']
            self.assertIsNone(result['effect'])
            same(rows[name]['snapshot']['credit']['views'][0], result['credit'])

    def test_reconcile_restore_replay(self):
        for scenario in self.actual:
            checks = scenario['restore_checks']
            same(scenario['history'][-1]['snapshot'], checks['before'])
            same(checks['before'], checks['after'])
            self.assertIs(checks['draw_replay']['ok']['duplicate'], True)
            self.assertIsNone(checks['draw_replay']['ok']['applied'])
            same({'error': {'type': 'CreditError', 'code': 'SETTLEMENT_SOURCE_REQUIRED'}},
                 checks['without_source'])
            original = next(row['result']['ok'] for row in scenario['setup_results']
                            if row['operation'] == 'draw')
            expected = copy.deepcopy(original)
            expected.update(duplicate=True, applied=None)
            same(expected, checks['draw_replay']['ok'])
        scenario = self.actual[2]
        for row in scenario['history'][1:]:
            self.assertTrue(row['result']['ok']['matched'])
            same(scenario['history'][0]['snapshot'], row['snapshot'])
        self.assertEqual(scenario['restore_checks']['after']['credit']['views'][0]
                         ['outstanding_exposure'], 10_000)

    def test_frozen_face_and_shared_capacity(self):
        for inputs, scenario in zip(self.fixture['scenarios'], self.actual):
            snapshots = [scenario['initial_snapshot']] + [row['snapshot'] for row in scenario['history']]
            for arithmetic, current in zip(inputs['expected_arithmetic'], snapshots):
                exact_fields(arithmetic, {'step_id', 'observable', 'advance_count',
                                          'claim_count', 'within_limit'}, 'arithmetic')
                observed = current['shared_exposure']
                for field in ['observable', 'advance_count', 'claim_count', 'within_limit']:
                    same(arithmetic[field], observed[field])
                same(scenario['initial_snapshot']['settlement'], current['settlement'])
                claim = current['credit']['claim']
                same(scenario['initial_snapshot']['credit']['claim'], claim)
                self.assertIs(claim['snapshot_frozen'], True)
                for view in current['credit']['views']:
                    self.assertEqual(view['open_face'], 100_000)
                    self.assertEqual(view['confirmed_cash_on_face'], 97_000)
                    self.assertEqual(view['reserved_open'], claim['reserved_open'])
                for entry in current['credit']['journal']:
                    if entry['op'] == 'offer':
                        same(current['settlement']['view']['claim'], entry['body']['face'])
                state = current['credit']['canonical_state']
                same(sha(state.encode('utf-8')), current['credit']['state_digest'])

    def test_observation_boundaries(self):
        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {'funds_executed', 'bank_debit_observed', 'economic_finality_claimed',
                               'repayment_observed', 'legal_debtor_bound', 'durable',
                               'underwriting_executed', 'kyc_executed', 'interest_defined',
                               'collateral_perfected', 'priority_bound', 'ownership_mutated',
                               'ticket_ownership_authoritative', 'admission_granted'}:
                        self.assertIs(item, False, key)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(self.actual)
        for scenario in self.actual:
            snapshots = [scenario['initial_snapshot']] + [row['snapshot'] for row in scenario['history']]
            for current in snapshots:
                observer = current['shared_exposure']
                same({'code': 'SHARED_EXPOSURE_NOT_BOUND',
                      'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observer['mapping'])
                self.assertIs(observer['fail_closed'], True)
                self.assertIs(observer['mutates_state'], False)
                self.assertIs(observer['authorizes_exposure'], False)
                self.assertEqual(observer['refund_component'], 'NOT_BOUND')

    def test_verifier_sensitivity(self):
        # Each detached mutation must fail without the outer VECTORS_SHA256 check.
        mutations = [
            lambda v: v['scenarios'][0]['history'][2]['result']['error'].update(code='ALTERED'),
            lambda v: v['scenarios'][0]['history'][0]['result']['ok'].update(duplicate=False),
            lambda v: v['scenarios'][0]['history'][0]['result']['ok'].update(applied='draw'),
            lambda v: v['scenarios'][0]['history'][0]['snapshot']['shared_exposure']
                         ['observable'].update(group_outstanding_exposure=70_001),
            lambda v: v['source_pins'][0].update(sha256='0' * 64),
            lambda v: v['source_pins'].pop(),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
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
        for selector in [('steps', 'close'), ('setup_steps', 'default')]:
            changed = copy.deepcopy(self.fixture)
            changed['scenarios'][0][selector[0]][0]['operation'] = selector[1]
            with self.assertRaises(AssertionError):
                validate_fixture(changed)


if __name__ == '__main__':
    unittest.main()
