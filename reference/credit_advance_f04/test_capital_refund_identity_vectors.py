"""Offline replay of the Capital refund and mock cancellation-acceptance history."""
import copy
from pathlib import Path
import unittest

from scripts.bootstrap_2_fixtures import read_bootstrap_2_input

from credit_fixture import exact_fields
from settlement_credit_boundary_vectors import PROVENANCE, replay_scenario_with_state
from settlement_fsm import SettlementError
from test_capital_operation_replay_vectors import load, same, sha
from test_capital_refund_composition_vectors import snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = HERE / 'fixtures/capital_refund_identity_v1.json'
VECTORS = HERE / 'fixtures/capital_refund_identity_vectors_v1.json'
VERSION = 'capital-refund-identity/1'
SCENARIO = 'I1_refund_acceptance_identity'
FIXTURE_SHA256 = '8c1b263186be587fdd7bc60861c3c3c4a5574ccf43f43dc67222b82a7e993af1'
VECTORS_SHA256 = '13e25673177aaf34828cb1472214c69ee824e994b3498883af64bf7b23b8787a'

CREDIT = 'reference/credit_advance_f04/'
SETTLEMENT = 'reference/settlement_f01_f03/'
SETUP_SOURCE = CREDIT + 'fixtures/capital_refund_composition_v1.json'
CONTRACTS = ['docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md#' + section
             for section in ('5', '9.3', '9.4')] + [
    'docs/contracts/CREDIT_ADVANCE_F04.md#7.11', 'docs/contracts/CREDIT_ADVANCE_F04.md#7.12']
SOURCE_TESTS = [
    SETTLEMENT + 'test_settlement_properties.py::BindingPropertyTests.' + method
    for method in ('test_d_refund_binding', 'test_d_acceptance_binding')
] + [
    SETTLEMENT + 'test_settlement_rejection_atomicity.py::SettlementRejectionAtomicityTests.' + method
    for method in ('test_bind_refund_binding_conflict_leaves_no_trace',
                   'test_acceptance_binding_conflict_leaves_no_trace',
                   'test_idempotency_conflict_leaves_no_trace',
                   'test_acceptance_exceeds_obligation_leaves_no_trace')
] + [SETTLEMENT + 'test_settlement_multi_payee_refund.py::RefundReplayTests.'
     'test_i_fsm_refund_key_replay_returns_the_first_result_verbatim',
     CREDIT + 'test_capital_refund_composition_vectors.py::CapitalRefundCompositionVectorTests.'
     'test_settlement_actions_preserve_credit']
SOURCE_PATHS = (
    'docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md', 'docs/contracts/CREDIT_ADVANCE_F04.md',
    SETTLEMENT + 'settlement_fsm.py', SETTLEMENT + 'mock_settlement.py',
    CREDIT + 'credit_fsm.py', CREDIT + 'mock_credit.py', CREDIT + 'open_terms.py',
    CREDIT + 'settlement_variance.py', CREDIT + 'shared_exposure.py',
    CREDIT + 'settlement_credit_boundary_vectors.py', CREDIT + 'credit_fixture.py',
    CREDIT + 'test_capital_operation_replay_vectors.py', SETUP_SOURCE,
    *dict.fromkeys(ref.split('::')[0] for ref in SOURCE_TESTS),
)

REFUND = 'bind_refund'
ACCEPT = 'observe_mock_cancel_acceptance'
REFUND_BODY = {'refund_id': 'R', 'amount': 30_000, 'beneficiary_role': 'buyer',
               'reason': 'synthetic-request'}
ACCEPT_BODY = {'source_id': 'A', 'amount': 10_000}
CHANGED_REFUND = dict(REFUND_BODY, reason='amended-request')
CHANGED_ACCEPTANCE = dict(ACCEPT_BODY, amount=10_001)

# (Step, operation, command key, business body). Deliberate reuse is part of the input.
CALLS = (
    ('first-refund', REFUND, 'i1-refund', REFUND_BODY),
    ('first-acceptance', ACCEPT, 'i1-accept', ACCEPT_BODY),
    ('fresh-refund', REFUND, 'i1-observe-refund', REFUND_BODY),
    ('fresh-acceptance', ACCEPT, 'i1-observe-accept', ACCEPT_BODY),
    ('refund-conflict', REFUND, 'i1-changed-refund', CHANGED_REFUND),
    ('acceptance-conflict', ACCEPT, 'i1-changed-accept', CHANGED_ACCEPTANCE),
    ('refund-key-conflict', REFUND, 'i1-refund', CHANGED_REFUND),
    ('acceptance-key-conflict', ACCEPT, 'i1-accept', CHANGED_ACCEPTANCE),
    ('above-ceiling', ACCEPT, 'i1-above', {'source_id': 'B', 'amount': 20_001}),
    ('at-ceiling', ACCEPT, 'i1-at', {'source_id': 'C', 'amount': 20_000}),
    ('replay-refund', REFUND, 'i1-refund', REFUND_BODY),
    ('replay-acceptance', ACCEPT, 'i1-accept', ACCEPT_BODY),
)
ERRORS = {
    'refund-conflict': 'REFUND_BINDING_CONFLICT',
    'acceptance-conflict': 'ACCEPTANCE_BINDING_CONFLICT',
    'refund-key-conflict': 'IDEMPOTENCY_CONFLICT',
    'acceptance-key-conflict': 'IDEMPOTENCY_CONFLICT',
    'above-ceiling': 'REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION',
}
REPLAYS = {'replay-refund': 'first-refund', 'replay-acceptance': 'first-acceptance'}
AMOUNTS = ('refund_face', 'refund_accepted', 'refund_outstanding', 'pg_adjustment_outstanding')


def replay(inputs):
    def check_offered_face(step, settlement, _credit):
        if step['operation'] == 'offer':
            view = settlement.view(inputs['claim_id'])
            same('COMMITTED', view['phase'])
            same(view['claim'], step['arguments']['face'])

    setup, settlement, credit = replay_scenario_with_state(
        {'steps': inputs['setup_steps']}, observer=check_offered_face)
    assert all('ok' in row['result'] for row in setup), 'setup must succeed'
    initial = snapshot(inputs, settlement, credit)
    methods = {REFUND: settlement.bind_refund, ACCEPT: settlement.observe_mock_cancel_acceptance}
    history = []
    for step in inputs['steps']:
        try:
            result = {'ok': methods[step['operation']](**step['arguments'])}
        except SettlementError as error:
            result = {'error': {'type': type(error).__name__, 'code': error.code}}
        history.append({'step_id': step['step_id'], 'target': step['target'],
                        'operation': step['operation'], 'result': result,
                        'snapshot': snapshot(inputs, settlement, credit)})
    return {'scenario_id': inputs['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history}


def check_checkpoint(expected, current, initial):
    view = current['settlement']['view']
    claim = view['claim']
    same(expected, {k: claim[k] for k in AMOUNTS})
    same(claim['refund_face'] - claim['refund_accepted'], claim['refund_outstanding'])
    same(claim['refund_accepted'], claim['pg_adjustment_outstanding'])
    same([100_000, 'KRW', 10_000], [claim[k] for k in ('gross', 'currency', 'confirmed_cash')])
    for public_view in (claim, view):
        same([False, False], [public_view['bank_debit_observed'], public_view['external_return_closed']])

    credit = current['credit']
    same(initial['credit'], credit)  # Both advance views, frozen claim, journal, state and digest.
    same([True, 100_000, 100_000, 0], [credit['claim'][k] for k in
         ('snapshot_frozen', 'open_face', 'reserved_open', 'residual_unreserved')])
    same([['DRAWN', True, amount, 0, amount] for amount in (60_000, 40_000)],
         [[advance[k] for k in ('phase', 'snapshot_frozen', 'drawn_exposure', 'repaid_exposure',
                                'outstanding_exposure')] for advance in credit['views']])
    exposure = current['shared_exposure']
    same(initial['shared_exposure'], exposure)
    same([2, 1, 100_000, True], [exposure[k] for k in ('advance_count', 'claim_count', 'limit', 'within_limit')])
    same({'group_drawn_exposure': 100_000, 'group_repaid_exposure': 0,
          'group_outstanding_exposure': 100_000, 'group_open_face': 100_000,
          'group_reserved_open': 100_000, 'group_residual_unreserved': 0}, exposure['observable'])
    for observer, code in [(current['variance'], 'SETTLEMENT_VARIANCE_NOT_BOUND'),
                           (exposure, 'SHARED_EXPOSURE_NOT_BOUND')]:
        same({'code': code, 'contract_status': 'NOT_BOUND', 'repair': 'NONE'}, observer['mapping'])
        same(['NOT_BOUND', True, False, False], [observer[k] for k in
             ('refund_component', 'fail_closed', 'mutates_state', 'authorizes_exposure')])
    for producer in (current['settlement'], credit):
        same(sha(producer['canonical_state'].encode()), producer['state_digest'])


def check_receipts(inputs, output):
    previous = output['initial_snapshot']['settlement']
    first_receipts = {}
    for step, row in zip(inputs['steps'], output['history'], strict=True):
        name, operation, args = step['step_id'], step['operation'], step['arguments']
        same([name, operation, 'settlement'], [row[k] for k in ('step_id', 'operation', 'target')])
        current = row['snapshot']['settlement']
        result = row['result']
        if name in ERRORS:
            same({'error': {'type': 'SettlementError', 'code': ERRORS[name]}}, result)
            same(previous, current)
        elif name in REPLAYS:
            same({'ok': dict(first_receipts[REPLAYS[name]], duplicate=True, applied=None)}, result)
            same(previous, current)
        else:
            receipt = result['ok']
            same([False, operation, current['view']], [receipt[k] for k in ('duplicate', 'applied', 'settlement')])
            body = {k: v for k, v in args.items() if k not in ('settlement_id', 'idempotency_key')}
            entry = {'settlement_id': args['settlement_id'], 'idempotency_key': args['idempotency_key'],
                     'op': operation, 'body': body}
            same(previous['journal'] + [entry], current['journal'])
            same(previous['view']['accepted_entries'] + 1, current['view']['accepted_entries'])
            if name in ('fresh-refund', 'fresh-acceptance'):
                same(previous['view']['claim'], current['view']['claim'])
            if name in ('first-refund', 'first-acceptance'):
                first_receipts[name] = receipt
        previous = current


class CapitalRefundIdentityVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load(FIXTURE)
        cls.vectors = load(VECTORS)
        cls.inputs, = cls.fixture['scenarios']
        cls.output, = cls.vectors['scenarios']

    def test_pins_and_literal_calls(self):
        self.assertEqual(sha(FIXTURE.read_bytes()), FIXTURE_SHA256)
        self.assertEqual(sha(VECTORS.read_bytes()), VECTORS_SHA256)
        exact_fields(self.vectors, {'vector_version', 'fixture_sha256', 'source_pins', 'scenarios'}, 'vectors')
        same([VERSION, FIXTURE_SHA256], [self.vectors['vector_version'], self.vectors['fixture_sha256']])
        same([{'path': path, 'sha256': sha(read_bootstrap_2_input(path))} for path in SOURCE_PATHS],
             self.vectors['source_pins'])
        exact_fields(self.fixture, {'fixture_version', 'fixture_kind', 'synthetic_only', 'provenance',
                                    'scenarios'}, 'fixture')
        same([VERSION, 'SYNTHETIC_REFUND_IDENTITY_VECTORS', True, PROVENANCE],
             [self.fixture[k] for k in ('fixture_version', 'fixture_kind', 'synthetic_only', 'provenance')])
        setup_fields = ('claim_id', 'group_id', 'advance_ids', 'limit', 'tolerance', 'setup_steps')
        exact_fields(self.inputs, {*setup_fields, 'scenario_id', 'source_tests', 'contracts',
                                   'steps', 'expected_arithmetic'}, 'scenario')
        setup = load(ROOT / SETUP_SOURCE)['scenarios'][0]
        same([setup[k] for k in setup_fields], [self.inputs[k] for k in setup_fields])
        same([SCENARIO, SOURCE_TESTS, CONTRACTS],
             [self.inputs[k] for k in ('scenario_id', 'source_tests', 'contracts')])
        same([{'step_id': step, 'target': 'settlement', 'operation': op,
               'arguments': dict(body, settlement_id=self.inputs['claim_id'], idempotency_key=key)}
              for step, op, key, body in CALLS], self.inputs['steps'])

    def test_complete_history_vectors(self):
        actual = replay(self.inputs)
        same(self.output, actual)
        check_receipts(self.inputs, actual)
        snapshots = [actual['initial_snapshot']] + [row['snapshot'] for row in actual['history']]
        names = ['initial'] + [step['step_id'] for step in self.inputs['steps']]
        at_first_acceptance = (30_000, 10_000, 20_000, 10_000)
        at_ceiling = (30_000, 30_000, 0, 30_000)
        amounts = [(0, 0, 0, 0), (30_000, 0, 30_000, 0)] + [at_first_acceptance] * 8 + [at_ceiling] * 3
        for name, values, expected, current in zip(names, amounts, self.inputs['expected_arithmetic'],
                                                   snapshots, strict=True):
            with self.subTest(step=name):
                same({'step_id': name, **dict(zip(AMOUNTS, values))}, expected)
                check_checkpoint({k: expected[k] for k in AMOUNTS}, current, actual['initial_snapshot'])

    def test_detached_checkpoint_controls(self):
        # Invoke economic predicates directly so neither a byte pin nor golden comparison can reject first.
        row = next(r for r in self.output['history'] if r['step_id'] == 'fresh-acceptance')
        expected = next(r for r in self.inputs['expected_arithmetic'] if r['step_id'] == row['step_id'])
        changes = (
            ('double acceptance', lambda s: s['settlement']['view']['claim'].update(
                refund_accepted=20_000, refund_outstanding=10_000, pg_adjustment_outstanding=20_000)),
            ('frozen credit', lambda s: s['credit']['claim'].update(open_face=70_000)),
            ('false closure', lambda s: s['settlement']['view']['claim'].update(external_return_closed=True)),
        )
        for label, change in changes:
            with self.subTest(label=label):
                detached = copy.deepcopy(row['snapshot'])
                change(detached)
                with self.assertRaises(AssertionError):
                    check_checkpoint({k: expected[k] for k in AMOUNTS}, detached, self.output['initial_snapshot'])

    def test_detached_receipt_controls(self):
        # Both a suppressed fresh-key journal entry and a replay reporting the latest view are observable.
        for name in ('fresh-refund', 'replay-acceptance'):
            with self.subTest(step=name):
                detached = copy.deepcopy(self.output)
                row = next(r for r in detached['history'] if r['step_id'] == name)
                if name == 'fresh-refund':
                    row['snapshot']['settlement']['journal'].pop()
                else:
                    row['result']['ok']['settlement'] = row['snapshot']['settlement']['view']
                with self.assertRaises(AssertionError):
                    check_receipts(self.inputs, detached)
