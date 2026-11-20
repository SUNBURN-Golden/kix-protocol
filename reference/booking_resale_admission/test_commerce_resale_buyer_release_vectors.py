"""Replay the synthetic buyer-hold release history through published commands."""
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
FIXTURE = f'{BRA}/fixtures/commerce_resale_buyer_release_inputs_v1.json'
GOLDEN = ROOT / f'{BRA}/fixtures/commerce_resale_buyer_release_receipts_v1.json'
SETUP_INPUT = f'{BRA}/fixtures/commerce_payment_ref_scope_inputs_v1.json'
CONTRACT = 'docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md'
SOURCE_TESTS = (
    f'{BRA}/test_resale_rejection_atomicity.py::ResaleRejectionAtomicityTests.'
    'test_release_hold_buyer_mismatch_leaves_no_trace',
    f'{BRA}/test_resale_fsm.py::ResaleFsmTests.test_buy_hold_is_optional_and_cancel_order_decides_the_race',
    f'{BRA}/test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential',
)
SOURCE_PATHS = goldens.SOURCE_PATHS | {
    CONTRACT, SETUP_INPUT,
    f'{BRA}/test_commerce_historical_receipt_vectors.py',
    f'{BRA}/test_commerce_temporal_vectors.py',
    f'{BRA}/test_commerce_journey_receipts.py',
    *(source.split('::')[0] for source in SOURCE_TESTS),
}
CASE_ID = 'resale-buyer-release'
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
    ('resale-hold', 'resale_hold_buy'),
    ('release-wrong-buyer', 'resale_release_hold'),
    ('release-hold', 'resale_release_hold'),
    ('resale-hold-fresh', 'resale_hold_buy'),
    ('replay-release-hold', 'resale_release_hold'),
    ('resale-payment', 'resale_observe_resale_payment'),
    ('transfer', 'resale_accept_resale'),
)
MACHINES = ('settlement', 'reservation', 'resale', 'admission', 'credit')
FALSE_FLAGS = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
    'economic_finality_claimed', 'chain_issued', 'mock_settlement_commit_observed',
    'venue_credential_reissued',
}
_assert_paths = historical._assert_paths


def _validate(fixture):
    catalogue = load_catalogue(ROOT)
    _assert_paths(fixture, {'fixture_version': 1, 'domain': catalogue.fsm_domain,
                            'provenance': 'OFFLINE_CONFORMANCE_FIXTURE_ONLY'})
    journey._check(type(fixture['fixture_version']) is int, 'fixture version type')
    journey._check([case['id'] for case in fixture['cases']] == [CASE_ID], 'case identity')
    case = fixture['cases'][0]
    _assert_paths(case, {'source_tests': list(SOURCE_TESTS),
                         'contract_predicates': [CONTRACT + '#10.2', CONTRACT + '#10.7']})
    steps = case['steps']
    journey._check(tuple((step['id'], step['action']) for step in steps) == STEPS, 'step identity/order')
    setup = goldens._decode((ROOT / SETUP_INPUT).read_bytes())['cases'][0]['steps'][:9]
    journey._check(_canonical(steps[:9]) == _canonical(setup), 'listing setup drift')

    keys = set()
    for step in steps:
        step_id, action, body = step['id'], step['action'], step['body']
        spec = catalogue.fsm['commands'][action]
        errors = problems(body, spec['schema'])
        journey._check(action in catalogue.fsm_names and not errors, f'{step_id}: command schema {errors}')
        replay = step_id == 'replay-release-hold'
        refusal = step_id == 'release-wrong-buyer'
        fields = {'id', 'action', 'body', 'expect_error' if refusal else 'expect'}
        if replay:
            fields.add('replay_of')
            _assert_paths(step, {'replay_of': 'release-hold', 'body': steps[11]['body']})
        else:
            key = body['idempotency_key']
            journey._check(key not in keys, f'{step_id}: fresh idempotency key required')
            keys.add(key)
        journey._check(set(step) == fields, f'{step_id}: step fields')
        if refusal:
            _assert_paths(step, {'expect_error': 'BUYER_MISMATCH', 'body.hold_id': 'hold-1',
                                 'body.buyer_role': 'buyer-3'})
        else:
            _assert_paths(step['expect'], {
                'duplicate': replay, 'applied': None if replay else spec['op'],
                'journal': [{'machine': name, 'delta': int(not replay and name == spec['machine'])}
                            for name in MACHINES],
            })


def _drive(case):
    host = FsmHost()
    accepted, receipts, outcomes = set(), {}, []
    before = historical._snapshot(host, accepted)
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
            if 'replay_of' in step:
                first = receipts[step['replay_of']]
                journey._check(_canonical(journey._without_replay_keys(receipt)) ==
                               _canonical(journey._without_replay_keys(first)), f'{step_id}: first receipt changed')
            receipts[step_id] = outcome['receipt'] = copy.deepcopy(receipt)
            accepted.add(action)

        after = historical._snapshot(host, accepted)
        if 'rejection_code' in outcome or 'replay_of' in step:
            journey._check(_canonical(before) == _canonical(after),
                           f'{step_id}: changed state, digests, journals or views')
        if 'receipt' in outcome:
            for entry in step['expect']['journal']:
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
        'record_schema_version': 'kix-commerce-resale-buyer-release-receipts/1',
        'record_kind': 'IN_PROCESS_MOCK_RECEIPT_VECTORS',
        'normative': False,
        'fixture': goldens._pin(FIXTURE, fixture_raw),
        'sources': [goldens._pin(path, (ROOT / path).read_bytes()) for path in sorted(SOURCE_PATHS)],
        'cases': [{'id': CASE_ID, 'steps': _drive(fixture['cases'][0])}],
    }


class CommerceResaleBuyerReleaseVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observed = _observe()
        cls.steps = {step['id']: step for step in cls.observed['cases'][0]['steps']}

    def test_complete_output_bytes_and_references(self):
        self.assertEqual(_canonical(self.observed).encode('utf-8'), GOLDEN.read_bytes())
        fixture = goldens._decode((ROOT / FIXTURE).read_bytes())
        outcomes = self.observed['cases'][0]['steps']
        self.assertEqual(sum('receipt' in step for step in outcomes), 15)
        for step, outcome in zip(fixture['cases'][0]['steps'], outcomes, strict=True):
            with self.subTest(step=step['id']):
                path, pointer = outcome['input_ref'].split('#/')
                self.assertEqual(path, FIXTURE)
                resolved = fixture
                for part in pointer.split('/'):
                    resolved = resolved[int(part)] if isinstance(resolved, list) else resolved[part]
                self.assertIs(resolved, step['body'])
                key = 'rejection_code' if 'expect_error' in step else 'receipt'
                self.assertEqual(set(outcome), {'id', 'action', 'input_ref', key, 'diagnostic_snapshot'})

    def test_release_and_replay_preserve_the_correct_current_hold(self):
        refused = self.steps['release-wrong-buyer']
        self.assertEqual(refused['rejection_code'], 'BUYER_MISMATCH')
        _assert_paths(refused['diagnostic_snapshot'], {'listing.phase': 'BUY_HELD',
                      'listing.hold_id': 'hold-1', 'listing.buyer_role': 'buyer-2'})

        released = self.steps['release-hold']
        replayed = self.steps['replay-release-hold']
        for outcome, duplicate, applied in ((released, False, 'release_hold'), (replayed, True, None)):
            _assert_paths(outcome['receipt'], {
                'duplicate': duplicate, 'applied': applied, 'listing.phase': 'LISTED',
                'listing.hold_id': None, 'listing.buyer_role': None, 'listing.payment_ref': None,
                'listing.transfer_id': None, 'listing.listing_id': 'list-1', 'listing.attached': True,
                'listing.recipient_role': 'buyer-2', 'listing.expired': False,
                'right.right_id': 'issue-1', 'right.holder_role': 'buyer-1', 'right.version': 1,
            })
        self.assertEqual(released['diagnostic_snapshot']['listing'], released['receipt']['listing'])
        for name in ('resale-hold-fresh', 'replay-release-hold'):
            _assert_paths(self.steps[name]['diagnostic_snapshot'], {
                'listing.phase': 'BUY_HELD', 'listing.hold_id': 'hold-2', 'listing.buyer_role': 'buyer-2',
                'listing.listing_id': 'list-1', 'listing.payment_ref': None,
            })

    def test_payment_and_transfer_remain_explicit(self):
        for name, _action in STEPS[7:-1]:
            with self.subTest(step=name):
                _assert_paths(self.steps[name]['diagnostic_snapshot'], {
                    'resale_right.right.right_id': 'issue-1', 'resale_right.right.holder_role': 'buyer-1',
                    'resale_right.right.version': 1,
                })
        payment = self.steps['resale-payment']
        _assert_paths(payment['receipt'], {
            'listing.phase': 'PAYMENT_NOTED', 'listing.amount': 10001, 'listing.payment_ref': 'cd' * 32,
            'listing.transfer_id': None, 'listing.ownership_transferred': False, 'funds_executed': False,
        })
        _assert_paths(payment['diagnostic_snapshot'], {'reservation.payment_ref': 'ab' * 32})
        transfer = self.steps['transfer']
        _assert_paths(transfer['receipt'], {
            'listing.phase': 'TRANSFERRED', 'listing.transfer_id': 'transfer-1',
            'listing.ownership_transferred': True, 'listing.settlement_gate': 'UNBOUND',
            'evidence.payment_ref': 'cd' * 32, 'funds_executed': False,
        })
        _assert_paths(transfer['diagnostic_snapshot'], {
            'resale_right.right.right_id': 'issue-1', 'resale_right.right.holder_role': 'buyer-2',
            'resale_right.right.version': 2, 'resale_right.right.generation': 1,
        })


if __name__ == '__main__':
    unittest.main()
