"""Source-informed, test-only pre-draw Capital histories.

Complete public captures are constrained by separately stated literal arithmetic.
Tests read goldens, never regenerate them, and never mutate producer sources.
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

from credit_fixture import FixtureError, exact_fields  # noqa: E402
from credit_fsm import CreditError  # noqa: E402
from settlement_credit_boundary_vectors import (  # noqa: E402
    canonical, replay_scenario_with_state,
)
from shared_exposure import observe_shared_exposure  # noqa: E402
from test_capital_operation_replay_vectors import (  # noqa: E402
    PROVENANCE, SETUP_FIELDS as REUSED_SETUP_FIELDS,
    SOURCE_PATHS as REUSED_SOURCES, load, same, sha,
)

FIXTURE = HERE / 'fixtures/capital_predraw_terminal_v1.json'
VECTORS = HERE / 'fixtures/capital_predraw_terminal_vectors_v1.json'
FIXTURE_SHA256 = '538f9cb0123b518c34f2a5ff3916433ac69acd093c961943d04f314178f1e58d'
VECTORS_SHA256 = '2f08fc5d4d066c3a6dd5b774799fdcaddcd9b2e947d643b6d5eba7a4d6e7fb98'
VERSION = 'capital-predraw-terminal/1'
SCENARIO = 'P1_reject_cancel_before_draw'
ADVANCES = ['adv-p1-a', 'adv-p1-b', 'adv-p1-c']
CLAIM = 'claim-1'
CONTRACTS = [f'docs/contracts/CREDIT_ADVANCE_F04.md#7.{n}' for n in [1, 2, 3]]
CITATION = ('reference/credit_advance_f04/test_credit_fsm.py::'
            'CreditFsmTests.test_cancel_and_reject_are_terminal_before_exposure')
SOURCE_PATHS = REUSED_SOURCES + (
    'reference/credit_advance_f04/test_capital_operation_replay_vectors.py',
    'reference/credit_advance_f04/test_capital_terminal_capacity_vectors.py',
    'reference/credit_advance_f04/test_capital_cross_claim_history_vectors.py',
    'reference/credit_advance_f04/fixtures/capital_operation_replay_v1.json',
    'reference/credit_advance_f04/fixtures/capital_operation_replay_vectors_v1.json',
    'reference/credit_advance_f04/fixtures/capital_terminal_capacity_v1.json',
    'reference/credit_advance_f04/fixtures/capital_terminal_capacity_vectors_v1.json',
    'reference/credit_advance_f04/fixtures/capital_cross_claim_history_v1.json',
    'reference/credit_advance_f04/fixtures/capital_cross_claim_history_vectors_v1.json',
    'reference/credit_advance_f04/fixtures/settlement_credit_boundary_vectors_v1.json',
)
HISTORY_FIELDS = {
    ('credit', 'approve'): {'advance_id', 'idempotency_key'},
    ('credit', 'reject'): {'advance_id', 'idempotency_key', 'reason'},
    ('credit', 'cancel'): {'advance_id', 'idempotency_key', 'reason'},
    ('credit', 'draw'): {'advance_id', 'idempotency_key', 'draw_id'},
}
SETUP_FIELDS = {key: value for key, value in REUSED_SETUP_FIELDS.items()
                if key[0] == 'settlement' or key == ('credit', 'offer')}
# Fixed identities/order bound this test-local replay; no arbitrary dispatch.
HISTORY_ORDER = [
    ('reject-a', 'reject', ADVANCES[0]),
    ('approve-a-late', 'approve', ADVANCES[0]),
    ('draw-a-late', 'draw', ADVANCES[0]),
    ('approve-b', 'approve', ADVANCES[1]),
    ('cancel-b', 'cancel', ADVANCES[1]),
    ('approve-b-late', 'approve', ADVANCES[1]),
    ('draw-b-late', 'draw', ADVANCES[1]),
    ('replay-reject-a', 'reject', ADVANCES[0]),
    ('replay-cancel-b', 'cancel', ADVANCES[1]),
    ('repeat-draw-b', 'draw', ADVANCES[1]),
    ('approve-c', 'approve', ADVANCES[2]),
    ('draw-c', 'draw', ADVANCES[2]),
    ('cancel-c-late', 'cancel', ADVANCES[2]),
]
ADVANCE_FIELDS = {'advance_id', 'phase', 'note_status', 'draw_id', 'drawn_exposure',
                  'repaid_exposure', 'outstanding_exposure', 'reserved_open',
                  'residual_unreserved', 'snapshot_frozen'}
CLAIM_FIELDS = {'claim_id', 'open_face', 'reserved_open', 'residual_unreserved',
                'snapshot_frozen'}
TOTAL_FIELDS = {'group_drawn_exposure', 'group_repaid_exposure',
                'group_outstanding_exposure', 'group_open_face',
                'group_reserved_open', 'group_residual_unreserved'}
UNKNOWN = {'error': {'type': 'CreditError', 'code': 'UNKNOWN_CLAIM'}}


def validate_fixture(fixture):
    exact_fields(fixture, {'fixture_version', 'fixture_kind', 'synthetic_only',
                           'provenance', 'scenarios'}, 'fixture')
    same([VERSION, 'SYNTHETIC_PREDRAW_TERMINAL_VECTORS', True, PROVENANCE],
         [fixture['fixture_version'], fixture['fixture_kind'],
          fixture['synthetic_only'], fixture['provenance']])
    assert type(fixture['scenarios']) is list and len(fixture['scenarios']) == 1
    s = fixture['scenarios'][0]
    exact_fields(s, {'scenario_id', 'source_tests', 'contracts', 'setup_steps',
                     'advance_ids', 'claim_id', 'group_id', 'limit', 'steps',
                     'expected_arithmetic'}, 'scenario')
    same([SCENARIO, [CITATION], CONTRACTS, ADVANCES, CLAIM, 'pool-p1', 100_000],
         [s[k] for k in ['scenario_id', 'source_tests', 'contracts', 'advance_ids',
                         'claim_id', 'group_id', 'limit']])
    setup_order = [(op, 'settlement', op, CLAIM)
                   for op in ['initiate', 'authorize', 'capture', 'commit']]
    setup_order += [('offer-' + label, 'credit', 'offer', advance)
                    for label, advance in zip(['a', 'b', 'c'], ADVANCES)]
    history_order = [(name, 'credit', op, advance)
                     for name, op, advance in HISTORY_ORDER]
    all_ids = []
    for key, order, allowed in [('setup_steps', setup_order, SETUP_FIELDS),
                                ('steps', history_order, HISTORY_FIELDS)]:
        assert type(s[key]) is list
        same(len(order), len(s[key]))
        for step, (name, target, op, identifier) in zip(s[key], order):
            exact_fields(step, {'step_id', 'target', 'operation', 'arguments'}, 'step')
            same([name, target, op], [step[k] for k in ['step_id', 'target', 'operation']])
            exact_fields(step['arguments'], allowed[target, op], 'arguments')
            args = step['arguments']
            same(identifier, args['advance_id' if target == 'credit' else 'settlement_id'])
            for field in ['idempotency_key'] + (['reason'] if 'reason' in args else []) + (
                    ['draw_id'] if 'draw_id' in args else []):
                value = args[field]
                assert type(value) is str and 0 < len(value) <= 100 and value.strip() == value
            all_ids.append(name)
    same(len(all_ids), len(set(all_ids)))
    # Literal setup matches the earlier pack, including complete face bytes.
    prior = load(HERE / 'fixtures/capital_operation_replay_v1.json')['scenarios'][0]
    same(prior['setup_steps'][:4], s['setup_steps'][:4])
    for step, amount in zip(s['setup_steps'][4:], [40_000, 60_000, 100_000]):
        same(amount, step['arguments']['amount'])
        same(prior['setup_steps'][4]['arguments']['face'], step['arguments']['face'])
    same(['initial'] + [name for name, _, _ in HISTORY_ORDER],
         [row['step_id'] for row in s['expected_arithmetic']])
    for row in s['expected_arithmetic']:
        exact_fields(row, {'step_id', 'advances', 'claim', 'shared_exposure'}, 'arithmetic')
        same(ADVANCES, [v['advance_id'] for v in row['advances']])
        for view in row['advances']:
            exact_fields(view, ADVANCE_FIELDS, 'advance arithmetic')
        if 'error' in row['claim']:
            same(UNKNOWN, row['claim'])
        else:
            exact_fields(row['claim'], {'ok'}, 'claim outcome')
            exact_fields(row['claim']['ok'], CLAIM_FIELDS, 'claim arithmetic')
        if row['shared_exposure'] is not None:
            exact_fields(row['shared_exposure'], {'observable', 'advance_count',
                         'claim_count', 'within_limit'}, 'shared arithmetic')
            exact_fields(row['shared_exposure']['observable'], TOTAL_FIELDS, 'totals')


def verify_sources(pins, reader=None):
    reader = read_bootstrap_2_input if reader is None else reader
    assert type(pins) is list
    same(list(SOURCE_PATHS), [p['path'] for p in pins])
    for pin in pins:
        exact_fields(pin, {'path', 'sha256'}, 'source pin')
        same(pin['sha256'], sha(reader(pin['path'])))


def snapshot(s, settlement, credit):
    views = [credit.view(identifier) for identifier in s['advance_ids']]
    try:
        claim = {'ok': credit.view_claim(s['claim_id'])}
    except CreditError as error:
        claim = {'error': {'type': type(error).__name__, 'code': error.code}}
    # Only C's DRAWN frozen view is in the observer's defined domain. Null is
    # "not invoked", not an empty/zero group or a new observer mapping.
    exposed = [view for view in views if view['phase'] == 'DRAWN']
    shared = None
    if exposed:
        same([ADVANCES[2]], [view['advance_id'] for view in exposed])
        assert exposed[0]['snapshot_frozen'] is True
        shared = observe_shared_exposure(s['group_id'], exposed, limit=s['limit'])
    return {
        'settlement': {'view': settlement.view(s['claim_id']),
                       'journal': settlement.export_journal(),
                       'canonical_state': settlement.canonical_state(),
                       'state_digest': settlement.state_digest()},
        'credit': {'views': views, 'claim': claim, 'journal': credit.export_journal(),
                   'canonical_state': credit.canonical_state(),
                   'state_digest': credit.state_digest()},
        'shared_exposure': shared,
    }


def dispatch(credit, step):
    methods = {'approve': credit.approve, 'reject': credit.reject,
               'cancel': credit.cancel, 'draw': credit.draw}
    try:
        return {'ok': methods[step['operation']](**step['arguments'])}
    except CreditError as error:
        return {'error': {'type': type(error).__name__, 'code': error.code}}


def replay(s):
    def check_face(step, settlement, _credit):
        if step['target'] == 'credit':
            same('COMMITTED', settlement.view(s['claim_id'])['phase'])
            same(settlement.view(s['claim_id'])['claim'], step['arguments']['face'])
    setup, settlement, credit = replay_scenario_with_state(
        {'steps': s['setup_steps']}, observer=check_face)
    assert all('ok' in row['result'] for row in setup)
    initial = snapshot(s, settlement, credit)
    history = []
    for step in s['steps']:
        result = dispatch(credit, step)
        history.append({'step_id': step['step_id'], 'target': step['target'],
                        'operation': step['operation'], 'result': result,
                        'snapshot': snapshot(s, settlement, credit)})
    return {'scenario_id': s['scenario_id'], 'setup_results': setup,
            'initial_snapshot': initial, 'history': history}


def checkpoints(s):
    return [s['initial_snapshot']] + [row['snapshot'] for row in s['history']]


def verify_arithmetic(inputs, actual):
    current = checkpoints(actual)
    same(len(inputs['expected_arithmetic']), len(current))
    for expected, snap in zip(inputs['expected_arithmetic'], current):
        same(expected['advances'], [{k: view[k] for k in ADVANCE_FIELDS}
                                   for view in snap['credit']['views']])
        claim = snap['credit']['claim']
        projected = ({'ok': {k: claim['ok'][k] for k in CLAIM_FIELDS}}
                     if 'ok' in claim else claim)
        same(expected['claim'], projected)
        shared = snap['shared_exposure']
        same(expected['shared_exposure'], None if shared is None else
             {k: shared[k] for k in ['observable', 'advance_count', 'claim_count', 'within_limit']})


def verify_semantics(fixture, vectors):
    """Detached checks bypass artifact pins; fixture arithmetic is checked too."""
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


class CapitalPredrawTerminalVectorTests(unittest.TestCase):
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

    def test_coverage_inventory_and_citations(self):
        # Check the cited test and the prior packs' source-test citations via AST,
        # without importing their unittest classes into discovery.
        citations = [CITATION]
        for name, prefix, count in [('capital_operation_replay', 'R', 3),
                                     ('capital_terminal_capacity', 'T', 2),
                                     ('capital_cross_claim_history', 'H', 1),
                                     ('settlement_credit_boundary', 'S', 6)]:
            pack = load(HERE / f'fixtures/{name}_v1.json')
            same([f'{prefix}{i}' for i in range(1, count + 1)],
                 [s['scenario_id'].split('_')[0] for s in pack['scenarios']])
            for s in pack['scenarios']:
                citations.extend(s.get('source_tests', []))
        for citation in citations:
            path, selector = citation.split('::')
            class_name, method = selector.split('.')
            tree = ast.parse((ROOT / path).read_text())
            cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
            self.assertIn(method, [n.name for n in cls.body if isinstance(n, ast.FunctionDef)])

    def test_complete_history_vectors(self):
        same(self.actual, verify_semantics(self.fixture, self.vectors))

    def test_predraw_notes_and_claim_observation(self):
        for snap in checkpoints(self.actual[0])[:-2]:
            same(UNKNOWN, snap['credit']['claim'])
            self.assertIsNone(snap['shared_exposure'])
            for view in snap['credit']['views']:
                same([None, None, 0, 0, 0, 0, 100_000, False],
                     [view[k] for k in ['note_status', 'draw_id', 'drawn_exposure',
                      'repaid_exposure', 'outstanding_exposure', 'reserved_open',
                      'residual_unreserved', 'snapshot_frozen']])

    def test_refusals_preserve_public_state(self):
        before = self.actual[0]['initial_snapshot']
        codes = []
        for row in self.actual[0]['history']:
            if 'error' in row['result']:
                same(before, row['snapshot'])
                same('CreditError', row['result']['error']['type'])
                codes.append(row['result']['error']['code'])
            before = row['snapshot']
        same(['TERMINAL_IMMUTABLE'] * 5 + ['ILLEGAL_TRANSITION'], codes)
        # Public snapshots exclude the private remembered-error cache. Refusals
        # enter neither journal; repeating one is checked separately below.
        rejected_keys = {step['arguments']['idempotency_key'] for step, row in
                         zip(self.fixture['scenarios'][0]['steps'], self.actual[0]['history'])
                         if 'error' in row['result']}
        self.assertTrue(rejected_keys.isdisjoint(
            entry['idempotency_key'] for entry in before['credit']['journal']))

    def test_terminal_receipt_replay(self):
        rows = {row['step_id']: row for row in self.actual[0]['history']}
        for replay_name, first, previous in [('replay-reject-a', 'reject-a', 'draw-b-late'),
                                              ('replay-cancel-b', 'cancel-b', 'replay-reject-a')]:
            expected = copy.deepcopy(rows[first]['result']['ok'])
            expected.update(duplicate=True, applied=None)
            same(expected, rows[replay_name]['result']['ok'])
            same(rows[previous]['snapshot'], rows[replay_name]['snapshot'])
        same(rows['draw-b-late']['result'], rows['repeat-draw-b']['result'])
        same(rows['replay-cancel-b']['snapshot'], rows['repeat-draw-b']['snapshot'])

    def test_capacity_and_late_cancel(self):
        verify_arithmetic(self.fixture['scenarios'][0], self.actual[0])
        drawn, late = self.actual[0]['history'][-2:]
        same(drawn['snapshot'], late['snapshot'])
        a, b, c = late['snapshot']['credit']['views']
        same(['REJECTED', 'CANCELLED', 'DRAWN'], [v['phase'] for v in [a, b, c]])
        for view in [a, b]:
            same([None, None, 0, 100_000, 0, True], [view[k] for k in
                 ['note_status', 'draw_id', 'outstanding_exposure', 'reserved_open',
                  'residual_unreserved', 'snapshot_frozen']])
        same([100_000, 0, 100_000, 'NOTED', 'draw-p1-c'], [c[k] for k in
             ['drawn_exposure', 'repaid_exposure', 'outstanding_exposure', 'note_status', 'draw_id']])
        same(100_000, c['amount'])  # 95000+5000, not the 97000 confirmed cash.

    def test_observation_boundaries(self):
        initial = self.actual[0]['initial_snapshot']
        faces = [step['arguments']['face'] for step in self.fixture['scenarios'][0]['setup_steps'][4:]]
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
        # Exercise detached captured observations, not only regenerated views.
        for snap in checkpoints(self.vectors['scenarios'][0]):
            same(initial['settlement'], snap['settlement'])
            for face in faces:
                same(face, snap['settlement']['view']['claim'])
            for entry in snap['credit']['journal']:
                if entry['op'] == 'offer':
                    same(faces[0], entry['body']['face'])
            for producer in ['settlement', 'credit']:
                same(sha(snap[producer]['canonical_state'].encode()), snap[producer]['state_digest'])
            for view in snap['credit']['views']:
                same([100_000, 97_000, 0, 'UNBOUND', False], [view[k] for k in
                     ['open_face', 'confirmed_cash_on_face', 'recovery_due_on_face',
                      'settlement_gate', 'mock_settlement_commit_observed']])
                same(initial['credit']['views'][0]['open_terms'], view['open_terms'])
                same(['UNDETERMINED', None], [view['open_terms'][k] for k in
                                              ['policy_number_status', 'decided_value']])
            observed = snap['shared_exposure']
            if observed is not None:
                views = copy.deepcopy([snap['credit']['views'][2]])
                before = canonical(views)
                same(observed, observe_shared_exposure('pool-p1', views, limit=100_000))
                self.assertEqual(before, canonical(views))
                same({'code': 'SHARED_EXPOSURE_NOT_BOUND', 'contract_status': 'NOT_BOUND',
                      'repair': 'NONE'}, observed['mapping'])
                same([True, False, False, 'NOT_BOUND'], [observed[k] for k in
                     ['fail_closed', 'mutates_state', 'authorizes_exposure', 'refund_component']])

    def test_verifier_sensitivity(self):
        mutations = [
            lambda v: v['scenarios'][0]['history'][0]['snapshot']['credit']['views'][0].update(phase='OFFERED'),
            lambda v: v['scenarios'][0]['initial_snapshot']['credit'].update(
                claim={'ok': {'reserved_open': 0, 'residual_unreserved': 100_000}}),
            lambda v: v['scenarios'][0]['history'][1]['result']['error'].update(code='ILLEGAL_TRANSITION'),
            lambda v: v['scenarios'][0]['history'][-1]['result']['error'].update(code='TERMINAL_IMMUTABLE'),
            lambda v: v['scenarios'][0]['history'][7]['result']['ok'].update(duplicate=False),
            lambda v: v['scenarios'][0]['history'][7]['result']['ok'].update(applied='reject'),
            lambda v: v['scenarios'][0]['history'][-2]['snapshot']['credit']['views'][2].update(note_status=None),
            lambda v: v['scenarios'][0]['history'][-2]['snapshot']['credit']['views'][2].update(draw_id=None),
            lambda v: v['scenarios'][0]['history'][-1]['snapshot']['credit']['claim']['ok'].update(reserved_open=0),
            lambda v: v['scenarios'][0]['history'][-1]['snapshot']['credit']['claim']['ok'].update(residual_unreserved=100_000),
            lambda v: v['scenarios'][0]['history'][0]['snapshot']['credit']['journal'].pop(),
            lambda v: v['scenarios'][0]['history'][0]['snapshot']['settlement']['journal'].reverse(),
            lambda v: v['scenarios'][0]['setup_results'].pop(),
            lambda v: v['scenarios'][0]['setup_results'].reverse(),
            lambda v: v['scenarios'][0]['history'].pop(),
            lambda v: v['scenarios'][0]['history'].reverse(),
            lambda v: v['source_pins'][0].update(sha256='0' * 64),
            lambda v: v['source_pins'].reverse(),
            lambda v: v['source_pins'].pop(),
        ]
        for field in ['note_status', 'draw_id']:
            mutations.append(lambda v, field=field: v['scenarios'][0]['history'][4]
                             ['snapshot']['credit']['views'][1].update({field: 'fabricated'}))
        for field in ADVANCE_FIELDS - {'advance_id', 'phase', 'note_status', 'draw_id'}:
            mutations.append(lambda v, field=field: v['scenarios'][0]['history'][-1]
                             ['snapshot']['credit']['views'][2].update({field: 1}))
        for field in TOTAL_FIELDS:
            mutations.append(lambda v, field=field: v['scenarios'][0]['history'][-1]
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

        def omit(s):
            s['steps'].pop(1)
            s['expected_arithmetic'].pop(2)

        def reorder(s):
            s['steps'][1], s['steps'][5] = s['steps'][5], s['steps'][1]
            s['expected_arithmetic'][2], s['expected_arithmetic'][6] = (
                s['expected_arithmetic'][6], s['expected_arithmetic'][2])

        fixture_mutations = [omit, reorder,
            lambda s: s['setup_steps'].reverse(),
            lambda s: s['steps'][0].update(target='settlement'),
            lambda s: s['steps'][0].update(operation='default'),
            lambda s: s['steps'][0]['arguments'].update(product={}),
            lambda s: s['expected_arithmetic'][1]['advances'][0].update(phase='CANCELLED'),
            lambda s: s['expected_arithmetic'][1].update(claim={'ok': {
                'claim_id': CLAIM, 'open_face': 100_000, 'reserved_open': 0,
                'residual_unreserved': 100_000, 'snapshot_frozen': False}}),
            lambda s: s['expected_arithmetic'][-1]['claim']['ok'].update(reserved_open=0),
            lambda s: s['expected_arithmetic'][-1]['claim']['ok'].update(residual_unreserved=100_000),
        ]
        for field in ['note_status', 'draw_id', 'reserved_open', 'residual_unreserved',
                      'drawn_exposure', 'repaid_exposure', 'outstanding_exposure']:
            fixture_mutations.append(lambda s, field=field: s['expected_arithmetic'][1]
                                     ['advances'][0].update({field: 1}))
        for field in TOTAL_FIELDS:
            fixture_mutations.append(lambda s, field=field: s['expected_arithmetic'][-1]
                                     ['shared_exposure']['observable'].update({field: 1}))
        for index, mutate in enumerate(fixture_mutations):
            with self.subTest(fixture_mutation=index):
                changed = copy.deepcopy(self.fixture)
                mutate(changed['scenarios'][0])
                vectors = copy.deepcopy(self.vectors)
                vectors['fixture_sha256'] = sha(canonical(changed))
                with self.assertRaises((AssertionError, FixtureError)):
                    verify_semantics(changed, vectors)


if __name__ == '__main__':
    unittest.main()
