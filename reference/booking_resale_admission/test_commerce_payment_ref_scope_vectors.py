"""Replay a synthetic payment-reference history through published FSM commands."""
from __future__ import annotations

import copy
import unittest

import test_commerce_historical_receipt_vectors as historical
import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
BRA = 'reference/booking_resale_admission'
FIXTURE = f'{BRA}/fixtures/commerce_payment_ref_scope_inputs_v1.json'
GOLDEN = ROOT / f'{BRA}/fixtures/commerce_payment_ref_scope_receipts_v1.json'
CONTRACT = 'docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md'
SOURCE_TESTS = (
    f'{BRA}/test_resale_rejection_atomicity.py::ResaleRejectionAtomicityTests.'
    'test_observe_resale_payment_payment_binding_conflict_leaves_no_trace',
    f'{BRA}/test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential',
    f'{BRA}/test_mock_gates.py::GateTests.test_payment_fact_is_not_funds_and_expiry_does_not_compensate',
)
SOURCE_PATHS = goldens.SOURCE_PATHS | {
    CONTRACT,
    f'{BRA}/test_commerce_historical_receipt_vectors.py',
    f'{BRA}/test_commerce_temporal_vectors.py',
    f'{BRA}/test_commerce_journey_receipts.py',
    f'{BRA}/fixtures/commerce_resale_expiry_inputs_v1.json',
    *(source.split('::')[0] for source in SOURCE_TESTS),
}
CASE_ID = 'payment-ref-scope'
STEPS = (
    ('reservation-clock', 'reservation_set_clock'),
    ('show', 'reservation_register_show'),
    ('hold', 'reservation_hold'),
    ('confirm', 'reservation_confirm'),
    ('payment', 'reservation_observe_payment'),
    ('issue', 'reservation_issue'),
    ('resale-clock', 'resale_set_clock'),
    ('resale-adopt', 'resale_adopt_issued'),
    ('list', 'resale_list_resale'),
    ('reuse-primary', 'resale_observe_resale_payment'),
    ('resale-payment', 'resale_observe_resale_payment'),
    ('transfer', 'resale_accept_resale'),
    ('show-2', 'reservation_register_show'),
    ('hold-2', 'reservation_hold'),
    ('confirm-2', 'reservation_confirm'),
    ('payment-2', 'reservation_observe_payment'),
)
PRIMARY_REF = 'ab' * 32
RESALE_REF = 'cd' * 32
CONFLICT = 'PAYMENT_BINDING_CONFLICT'
MACHINES = ('settlement', 'reservation', 'resale', 'admission', 'credit')
FALSE_FLAGS = set(NON_CLAIMS) | {
    'economic_finality_claimed', 'chain_issued', 'mock_settlement_commit_observed',
    'venue_credential_reissued',
}
_assert_paths = historical._assert_paths


def _validate(fixture):
    catalogue = load_catalogue(ROOT)
    _assert_paths(fixture, {'fixture_version': 1, 'domain': catalogue.fsm_domain,
                            'provenance': 'OFFLINE_CONFORMANCE_FIXTURE_ONLY'})
    journey._check([case['id'] for case in fixture['cases']] == [CASE_ID], 'case identity')
    case = fixture['cases'][0]
    _assert_paths(case, {'source_tests': list(SOURCE_TESTS),
                         'contract_predicates': [CONTRACT + '#3', CONTRACT + '#4']})
    steps = case['steps']
    journey._check(tuple((s['id'], s['action']) for s in steps) == STEPS, 'step identity/order')
    keys = set()
    for step in steps:
        step_id, action, body = step['id'], step['action'], step['body']
        machine = action.split('_', 1)[0]
        spec = catalogue.fsm['commands'][action]
        errors = problems(body, spec['schema'])
        journey._check(not errors, f'command schema: {step_id}: {errors}')
        key = body['idempotency_key']
        journey._check(key not in keys, f'fresh idempotency key: {step_id}')
        keys.add(key)
        expected_field = 'expect_error' if step_id == 'reuse-primary' else 'expect'
        journey._check(set(step) == {'id', 'action', 'body', expected_field}, 'step fields: ' + step_id)
        if expected_field == 'expect_error':
            journey._check(step['expect_error'] == CONFLICT, 'refusal code')
        else:
            _assert_paths(step['expect'], {
                'duplicate': False, 'applied': spec['op'],
                'journal': [{'machine': name, 'delta': int(name == machine)} for name in MACHINES],
            })

    bodies = {step['id']: step['body'] for step in steps}
    for name in ('payment', 'resale-adopt', 'reuse-primary', 'payment-2'):
        _assert_paths(bodies[name], {'payment_ref': PRIMARY_REF, 'amount': 10001})
    _assert_paths(bodies['resale-payment'], {'payment_ref': RESALE_REF})
    for name in ('reuse-primary', 'resale-payment'):
        _assert_paths(bodies[name], {'listing_id': 'list-1', 'buyer_role': 'buyer-2', 'amount': 10001})


def _snapshot(host, accepted):
    snapshot = historical._snapshot(host, set(accepted.values()))
    reservation = host.machines['reservation']
    if 'show-2' in accepted:
        snapshot['views']['show_2'] = copy.deepcopy(reservation.view_show('show-2'))
    if 'hold-2' in accepted:
        snapshot['views']['reservation_2'] = copy.deepcopy(reservation.view('reserve-2'))
    return snapshot


def _drive(case):
    # Both shows share one host and all accepted business state.
    host = FsmHost()
    accepted, outcomes = {}, []
    before = _snapshot(host, accepted)
    journey._check(set(before['machines']) == set(MACHINES), 'machine coverage')
    for index, step in enumerate(case['steps']):
        step_id, action = step['id'], step['action']
        outcome = {'id': step_id, 'action': action, 'input_ref': f'{FIXTURE}#/cases/0/steps/{index}/body'}
        try:
            receipt = host.call(action, copy.deepcopy(step['body']))
        except FsmRejected as exc:
            journey._check(exc.code == step.get('expect_error'), f'{step_id}: unexpected refusal {exc.code}')
            outcome['rejection_code'] = exc.code
        else:
            journey._check('expect' in step, f'{step_id}: expected refusal was accepted')
            expect = step['expect']
            _assert_paths(receipt, dict(expect['paths'], duplicate=expect['duplicate'], applied=expect['applied']))
            outcome['receipt'] = copy.deepcopy(receipt)
            accepted[step_id] = action

        after = _snapshot(host, accepted)
        if 'rejection_code' in outcome:
            journey._check(_canonical(before) == _canonical(after),
                           f'{step_id}: refusal changed state, digests, journals or views')
        else:
            for entry in expect['journal']:
                name, delta = entry['machine'], entry['delta']
                old, new = before['machines'][name]['journal'], after['machines'][name]['journal']
                journey._check(len(new) == len(old) + delta and _canonical(new[:len(old)]) == _canonical(old),
                               f'{step_id}: unexpected journal append for {name}')
        outcome['diagnostic_snapshot'] = after['views']
        for node in journey._walk([outcome.get('receipt', {}), after['views']]):
            for flag in FALSE_FLAGS & node.keys():
                journey._check(node[flag] is False, f'{step_id}: authority flag {flag}')
        outcomes.append(outcome)
        before = after
    return outcomes


def _observe():
    fixture_raw = (ROOT / FIXTURE).read_bytes()
    fixture = goldens._decode(fixture_raw)
    journey._check(_canonical(fixture).encode('utf-8') == fixture_raw, 'canonical input bytes differ')
    _validate(fixture)
    return {
        'record_schema_version': 'kix-commerce-payment-ref-scope-receipts/1',
        'record_kind': 'IN_PROCESS_MOCK_RECEIPT_VECTORS',
        'normative': False,
        'fixture': goldens._pin(FIXTURE, fixture_raw),
        'sources': [goldens._pin(path, (ROOT / path).read_bytes()) for path in sorted(SOURCE_PATHS)],
        'cases': [{'id': CASE_ID, 'steps': _drive(fixture['cases'][0])}],
    }


class CommercePaymentRefScopeVectorTests(unittest.TestCase):
    def test_complete_output_bytes_and_references(self):
        observed = _observe()
        self.assertEqual(_canonical(observed).encode('utf-8'), GOLDEN.read_bytes())
        fixture = goldens._decode((ROOT / FIXTURE).read_bytes())
        for step, outcome in zip(fixture['cases'][0]['steps'], observed['cases'][0]['steps'], strict=True):
            with self.subTest(step=step['id']):
                path, pointer = outcome['input_ref'].split('#/')
                self.assertEqual(path, FIXTURE)
                resolved = fixture
                for part in pointer.split('/'):
                    resolved = resolved[int(part)] if isinstance(resolved, list) else resolved[part]
                self.assertIs(resolved, step['body'])
                key = 'rejection_code' if 'expect_error' in step else 'receipt'
                self.assertEqual(set(outcome), {'id', 'action', 'input_ref', key, 'diagnostic_snapshot'})

    def test_refusal_payment_and_transfer_are_separate(self):
        steps = {step['id']: step for step in _observe()['cases'][0]['steps']}
        self.assertEqual(steps['reuse-primary']['rejection_code'], CONFLICT)
        for name, phase, reference in (('reuse-primary', 'LISTED', None),
                                       ('resale-payment', 'PAYMENT_NOTED', RESALE_REF)):
            with self.subTest(step=name):
                _assert_paths(steps[name]['diagnostic_snapshot'], {
                    'reservation.order_id': 'order-1', 'reservation.payment_ref': PRIMARY_REF,
                    'listing.phase': phase, 'listing.payment_ref': reference,
                    'listing.transfer_id': None, 'listing.ownership_transferred': False,
                    'listing.show_id': 'show-1', 'listing.settlement_gate': 'UNBOUND',
                    'resale_right.right.right_id': 'issue-1', 'resale_right.right.holder_role': 'buyer-1',
                    'resale_right.right.version': 1,
                })
        _assert_paths(steps['transfer']['receipt'], {
            'listing.phase': 'TRANSFERRED', 'listing.transfer_id': 'transfer-1',
            'listing.ownership_transferred': True, 'listing.settlement_gate': 'UNBOUND',
            'evidence.payment_ref': RESALE_REF, 'right.right_id': 'issue-1',
            'right.holder_role': 'buyer-2', 'right.version': 2,
        })

    def test_same_reference_is_recorded_on_another_show(self):
        control = _observe()['cases'][0]['steps'][-1]
        _assert_paths(control['receipt'], {
            'duplicate': False, 'applied': 'observe_payment', 'show.show_id': 'show-2',
            'reservation.order_id': 'order-2', 'reservation.phase': 'PAYMENT_NOTED',
            'reservation.payment_ref': PRIMARY_REF, 'reservation.right': None,
        })
        _assert_paths(control['diagnostic_snapshot'], {
            'show.show.show_id': 'show-1', 'show_2.show.show_id': 'show-2',
            'reservation.order_id': 'order-1', 'reservation.phase': 'ISSUED',
            'reservation.payment_ref': PRIMARY_REF,
            'reservation_2.order_id': 'order-2', 'reservation_2.payment_ref': PRIMARY_REF,
            'show.show.payment_ref_count': 1, 'show_2.show.payment_ref_count': 1,
        })


if __name__ == '__main__':
    unittest.main()
