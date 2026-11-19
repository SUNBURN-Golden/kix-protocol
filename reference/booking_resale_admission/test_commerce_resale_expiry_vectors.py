"""Portable, source-informed resale expiry histories; no golden update mode.

Only published FsmHost commands execute. Detached diagnostics are local views,
not read APIs. Import helper modules, never their TestCase classes.
"""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
import test_commerce_historical_receipt_vectors as historical
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = 'reference/booking_resale_admission/fixtures/commerce_resale_expiry_inputs_v1.json'
GOLDEN = ROOT / 'reference/booking_resale_admission/fixtures/commerce_resale_expiry_receipts_v1.json'
SOURCE_PATHS = historical.SOURCE_PATHS | frozenset({
    'reference/booking_resale_admission/test_commerce_historical_receipt_vectors.py',
    'reference/booking_resale_admission/test_resale_rejection_atomicity.py',
    'reference/booking_resale_admission/fixtures/commerce_historical_inputs_v1.json',
    'reference/booking_resale_admission/fixtures/commerce_historical_receipts_v1.json',
})
SETUP = ('reservation-clock', 'show', 'hold', 'confirm', 'payment', 'issue',
         'resale-clock', 'resale-adopt', 'list')
# Literal independent identities/order and refusal maps, never inferred from JSON.
ORDERS = {
    'unpaid-listing-expiry': SETUP + ('resale-expire', 'replay-list', 'payment-late'),
    'paid-listing-expiry': SETUP + ('resale-payment', 'resale-expire', 'replay-list',
                                     'replay-payment', 'transfer-late', 'cancel-late'),
}
REFUSALS = {
    'unpaid-listing-expiry': {'payment-late': 'LISTING_NOT_OPEN'},
    'paid-listing-expiry': {'transfer-late': 'LISTING_NOT_OPEN',
                            'cancel-late': 'COMPENSATION_UNDEFINED'},
}
REPLAYS = {
    'unpaid-listing-expiry': {'replay-list': 'list'},
    'paid-listing-expiry': {'replay-list': 'list', 'replay-payment': 'resale-payment'},
}
_assert_paths = historical._assert_paths
_snapshot = historical._snapshot
_views = historical._views
_assert_views = historical._assert_views


def _read(path):
    return (ROOT / path).read_bytes()


def _validate(fixture):
    journey._check(type(fixture['fixture_version']) is int and fixture['fixture_version'] == 1,
                   'fixture version')
    journey._check(fixture['provenance'] == 'OFFLINE_CONFORMANCE_FIXTURE_ONLY', 'provenance')
    catalogue = load_catalogue(ROOT)
    journey._check(fixture['domain'] == catalogue.fsm_domain, 'fixture domain')
    journey._check(tuple(c['id'] for c in fixture['cases']) == tuple(ORDERS), 'case order')
    machines = {'settlement', 'reservation', 'resale', 'admission', 'credit'}
    for case in fixture['cases']:
        name = case['id']
        journey._check(tuple(s['id'] for s in case['steps']) == ORDERS[name], 'step order')
        journey._check({s['id']: s['expect_error'] for s in case['steps'] if 'expect_error' in s}
                       == REFUSALS[name], 'refusal mapping')
        journey._check({s['id']: s['replay_of'] for s in case['steps'] if 'replay_of' in s}
                       == REPLAYS[name], 'replay mapping')
        journey._check(case['clocks'] == {
            'T0': 1000000, 'listing_expires_ms': 1900000,
            'meaning': 'SYNTHETIC_FIXTURE_INPUTS_ONLY'}, 'synthetic clocks')
        seen, keys = {}, set()
        for step in case['steps']:
            journey._check(('expect' in step) != ('expect_error' in step), 'one expectation')
            action, body = step['action'], step['body']
            journey._check(action in catalogue.fsm_names, 'unpublished action')
            spec = catalogue.fsm['commands'][action]
            journey._check(not problems(body, spec['schema']), 'command schema: ' + step['id'])
            journey._check(spec['subject_field'] in body and 'domain' not in body, 'subject/domain')
            key = body['idempotency_key']
            if 'replay_of' in step:
                first = seen[step['replay_of']]
                journey._check(action == first['action'] and _canonical(body) == _canonical(first['body']),
                               'replay binding')
            else:
                journey._check(key not in keys, 'fresh key required')
            keys.add(key)
            if 'expect' in step:
                expect = step['expect']
                replay = 'replay_of' in step
                journey._check(expect['duplicate'] is replay and
                               expect['applied'] == (None if replay else spec['op']), 'accepted expectation')
                journals = expect['journal']
                journey._check(len(journals) == 5 and {j['machine'] for j in journals} == machines,
                               'journal expectation coverage')
                journey._check(all(type(j['delta']) is int and j['delta'] in (0, 1) for j in journals),
                               'journal delta type')
            seen[step['id']] = step


def _drive(case):
    host = FsmHost()
    accepted, receipts, refusals, snapshots = set(), {}, {}, {}
    flags = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
        'economic_finality_claimed', 'chain_issued', 'venue_credential_reissued', 'offline_admission'}
    for step in case['steps']:
        before = _snapshot(host, accepted)
        try:
            receipt = host.call(step['action'], copy.deepcopy(step['body']))
        except FsmRejected as exc:
            journey._check(exc.code == step.get('expect_error'), 'unexpected refusal: ' + exc.code)
            journey._check(_canonical(before) == _canonical(_snapshot(host, accepted)),
                           'refusal mutated state/digest/journal/views')
            refusals[step['id']] = exc.code
        else:
            journey._check('expect' in step, 'expected refusal was accepted')
            expect = step['expect']
            _assert_paths(receipt, {'duplicate': expect['duplicate'], 'applied': expect['applied'],
                                    **expect['paths']})
            for journal in expect['journal']:
                name = journal['machine']
                journey._check(len(host.machines[name].export_journal()) -
                               len(before['machines'][name]['journal']) == journal['delta'],
                               'journal delta: ' + step['id'] + '/' + name)
            if 'replay_of' in step:
                first = receipts[step['replay_of']]
                journey._check(_canonical(journey._without_replay_keys(receipt)) ==
                               _canonical(journey._without_replay_keys(first)), 'immutable replay result')
                journey._check(_canonical(before) == _canonical(_snapshot(host, accepted)),
                               'replay mutated state/digest/journal/views')
            receipts[step['id']] = copy.deepcopy(receipt)
            accepted.add(step['action'])
        snapshots[step['id']] = _snapshot(host, accepted)
        for node in journey._walk([receipts.get(step['id'], {}), snapshots[step['id']]['views']]):
            for flag in flags & node.keys():
                journey._check(node[flag] is False, 'authority flag: ' + flag)
        _assert_views(host, accepted, step['observe'])
    _assert_views(host, accepted, case['final_expect']['views'])
    for fact in case['final_expect']['separate_facts']:
        _assert_paths(receipts[fact['step']], {fact['path']: fact['value']})
    journey._check(refusals == REFUSALS[case['id']], 'refusals')
    return host, receipts, refusals, snapshots


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    journey._check(_canonical(fixture).encode() == fixture_raw, 'canonical input bytes differ')
    _validate(fixture)
    cases = []
    for i, case in enumerate(fixture['cases']):
        _host, receipts, refusals, snapshots = _drive(case)
        journey._check(not receipts.keys() & refusals.keys() and
                       receipts.keys() | refusals.keys() == {s['id'] for s in case['steps']}, 'outcome coverage')
        steps = []
        for j, step in enumerate(case['steps']):
            outcome = dict(id=step['id'], action=step['action'],
                           input_ref=FIXTURE + '#/cases/%d/steps/%d/body' % (i, j),
                           diagnostic_snapshot=copy.deepcopy(snapshots[step['id']]['views']))
            key = 'receipt' if step['id'] in receipts else 'rejection_code'
            outcome[key] = (receipts if key == 'receipt' else refusals)[step['id']]
            steps.append(outcome)
        cases.append(dict(id=case['id'], steps=steps))
    return dict(record_schema_version='kix-commerce-resale-expiry-receipts/1',
                record_kind='IN_PROCESS_MOCK_RECEIPT_VECTORS', normative=False,
                fixture=fixture_pin, sources=sources, cases=cases)


def compare_receipts(raw, read=_read):
    expected = goldens._decode(raw)
    fixture_raw = read(FIXTURE)
    fixture_pin = goldens._pin(FIXTURE, fixture_raw)
    sources = [goldens._pin(path, read(path)) for path in sorted(SOURCE_PATHS)]
    journey._check(expected['fixture'] == fixture_pin, 'fixture pin drift')
    journey._check(expected['sources'] == sources, 'source pin drift/set/order')
    observed = _observe(fixture_raw, fixture_pin, sources)
    journey._check(_canonical(observed).encode() == raw, 'complete canonical receipt bytes differ')
    return observed


class CommerceResaleExpiryVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = GOLDEN.read_bytes()
        cls.document = goldens._decode(cls.raw)
        cls.fixture = goldens._decode(_read(FIXTURE))

    def test_complete_output_bytes_and_references(self):
        observed = compare_receipts(self.raw)
        for i, (case, vector) in enumerate(zip(self.fixture['cases'], observed['cases'])):
            self.assertEqual(case['id'], vector['id'])
            for j, (step, outcome) in enumerate(zip(case['steps'], vector['steps'])):
                ref = FIXTURE + '#/cases/%d/steps/%d/body' % (i, j)
                self.assertEqual(outcome['input_ref'], ref)
                resolved = self.fixture
                for part in ref.split('#/')[1].split('/'):
                    resolved = resolved[int(part)] if isinstance(resolved, list) else resolved[part]
                self.assertEqual(_canonical(resolved), _canonical(step['body']))
                key = 'rejection_code' if 'expect_error' in step else 'receipt'
                self.assertEqual(set(outcome), {'id', 'action', 'input_ref', key, 'diagnostic_snapshot'})

    def test_schemas_sources_and_unbound_reads(self):
        _validate(self.fixture)
        catalogue, host = load_catalogue(ROOT), FsmHost()
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.names)
            self.assertNotIn(name, host._commands)
        # Atomicity tests are dynamically installed; validate their executable symbol.
        import test_resale_rejection_atomicity as atomicity
        for case in self.fixture['cases']:
            for source in [case['source_test'], *case['related_source_tests']]:
                path, symbol = source.split('::')
                self.assertIn(path, SOURCE_PATHS)
                if path.endswith('test_resale_rejection_atomicity.py'):
                    cls, method = symbol.split('.')
                    self.assertTrue(callable(getattr(getattr(atomicity, cls), method)))
                else:
                    self.assertIn('def ' + symbol.split('.')[1] + '(', _read(path).decode())
            self.assertEqual(case['contract_predicates'], [
                'docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10.%d' % n for n in range(1, 5)])

    def test_expiry_preserves_facts_and_historical_receipts(self):
        for case in self.fixture['cases']:
            paid = case['id'] == 'paid-listing-expiry'
            _host, receipts, refusals, snapshots = _drive(case)
            self.assertEqual(refusals, REFUSALS[case['id']])
            for sid in ORDERS[case['id']][8:]:
                views = snapshots[sid]['views']
                _assert_paths(views, {
                    'reservation.phase': 'ISSUED', 'reservation.right.holder_role': 'buyer-1',
                    'reservation.right.version': 1, 'reservation.payment_ref': 'ab' * 32,
                    'resale_right.right.holder_role': 'buyer-1', 'resale_right.right.version': 1,
                    'listing.current_version': 1, 'listing.holder_role': 'buyer-1',
                    'listing.transfer_id': None, 'listing.compensation_defined': False,
                    'listing.funds_executed': False, 'listing.chain_owner_current': False,
                    'listing.ownership_transferred': False})
            last = snapshots[case['steps'][-1]['id']]['views']['listing']
            _assert_paths(last, {'phase': 'PAYMENT_NOTED' if paid else 'LISTED', 'expired': True,
                                 'payment_ref': 'cd' * 32 if paid else None,
                                 'amount': 10001})
            # Amount is published as listing.amount; the accepted payment journal
            # retains the exact observed payment reference and amount separately.
            journal = snapshots[case['steps'][-1]['id']]['machines']['resale']['journal']
            payments = [entry for entry in journal if entry['op'] == 'observe_resale_payment']
            self.assertEqual(len(payments), int(paid))
            if paid:
                self.assertEqual(payments[0]['body']['payment_ref'], 'cd' * 32)
                self.assertEqual(payments[0]['body']['amount'], 10001)
            for replay, first in REPLAYS[case['id']].items():
                self.assertIs(receipts[replay]['listing']['expired'], False)
                self.assertIs(snapshots[replay]['views']['listing']['expired'], True)
                self.assertEqual(_canonical(journey._without_replay_keys(receipts[replay])),
                                 _canonical(journey._without_replay_keys(receipts[first])))
            self.assertEqual(receipts['replay-list']['listing']['phase'], 'LISTED')
            if paid:
                self.assertEqual(receipts['replay-payment']['listing']['phase'], 'PAYMENT_NOTED')
                self.assertIsNone(receipts['replay-list']['listing']['payment_ref'])

    def test_refusals_and_replays_do_not_mutate_any_machine(self):
        for case in self.fixture['cases']:
            _host, _receipts, _errors, snapshots = _drive(case)
            for i, step in enumerate(case['steps']):
                if 'expect_error' in step or 'replay_of' in step:
                    previous = snapshots[case['steps'][i - 1]['id']]
                    self.assertIsNot(previous, snapshots[step['id']])
                    self.assertEqual(_canonical(previous), _canonical(snapshots[step['id']]))

    def test_detached_output_corruption_controls(self):
        mutations = (
            lambda s: s[-1].update(rejection_code='CHANGED'),
            lambda s: s[9]['receipt']['listing'].update(payment_ref=None),
            lambda s: s[9]['receipt']['listing'].update(amount=0),
            lambda s: s[11]['receipt']['listing'].update(expired=True),
            lambda s: s[12]['receipt'].update(applied='observe_resale_payment'),
            lambda s: s[-1]['diagnostic_snapshot']['listing'].update(phase='CANCELLED'),
            lambda s: s[-1]['diagnostic_snapshot']['listing'].update(payment_ref=None),
            lambda s: s[-1]['diagnostic_snapshot']['listing'].update(amount=0),
            lambda s: s[-1]['diagnostic_snapshot']['listing'].update(compensation_defined=True),
            lambda s: s[-1]['diagnostic_snapshot']['listing'].update(transfer_id='invented'),
            lambda s: s[-1]['diagnostic_snapshot']['resale_right']['right'].update(holder_role='buyer-2'),
            lambda s: s[-1]['diagnostic_snapshot']['resale_right']['right'].update(version=2),
            lambda s: s[5]['receipt']['evidence'].update(chain_issued=0),
            lambda s: s.pop(), lambda s: s.append(copy.deepcopy(s[0])), lambda s: s.reverse(),
            lambda s: s[0].update(input_ref=FIXTURE + '#/cases/0/steps/0/body'),
            lambda s: s[0].update(action='settlement_commit'),
            lambda s: s[0].update(id='changed'),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document['cases'][1]['steps'])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(AssertionError, 'canonical receipt bytes differ'):
                compare_receipts(_canonical(document).encode())

    def test_repinned_input_controls_fail_before_execution(self):
        mutations = (
            ('step order', lambda c: c['steps'].pop()),
            ('step order', lambda c: c['steps'].append(copy.deepcopy(c['steps'][0]))),
            ('step order', lambda c: c['steps'].reverse()),
            ('refusal mapping', lambda c: c['steps'][-1].update(expect_error='CHANGED')),
            ('replay mapping', lambda c: c['steps'][10].pop('replay_of')),
            ('replay binding', lambda c: c['steps'][10]['body'].update(idempotency_key='new-key')),
            ('fresh key', lambda c: c['steps'][-1]['body'].update(idempotency_key='list')),
            ('command schema', lambda c: c['steps'][1]['body'].update(capacity=True)),
        )
        for reason, mutate in mutations:
            fixture = copy.deepcopy(self.fixture)
            mutate(fixture['cases'][0])
            raw = _canonical(fixture).encode()
            document = copy.deepcopy(self.document)
            document['fixture'] = goldens._pin(FIXTURE, raw)
            with self.subTest(reason=reason), patch(__name__ + '.FsmHost') as host:
                with self.assertRaisesRegex(AssertionError, reason):
                    compare_receipts(_canonical(document).encode(), read=lambda p: raw if p == FIXTURE else _read(p))
                host.assert_not_called()

    def test_injected_effects_on_refusal_or_replay_are_detected(self):
        real_call = FsmHost.call
        for case in self.fixture['cases']:
            for target in (s for s in case['steps'] if 'expect_error' in s or 'replay_of' in s):
                def corrupting_call(host, action, body):
                    try:
                        return real_call(host, action, body)
                    finally:
                        # Replays share the original body: inject only after expiry.
                        if (action == target['action'] and body == target['body'] and
                                host.machines['resale'].view('list-1')['expired']):
                            real_call(host, 'resale_set_clock', {
                                'subject_id': 'clock', 'idempotency_key': 'injected-effect', 'now_ms': 1900001})
                with self.subTest(case=case['id'], target=target['id']), patch.object(FsmHost, 'call', corrupting_call):
                    with self.assertRaisesRegex(AssertionError, 'mutated state/digest/journal/views|journal delta'):
                        _drive(case)

    def test_pins_and_strict_json_controls(self):
        for mutate in (
            lambda d: d['fixture'].update(sha256='0' * 64),
            lambda d: d['fixture'].update(gitBlob='0' * 40),
            lambda d: d['sources'].pop(), lambda d: d['sources'].append(d['sources'][0]),
            lambda d: d['sources'].reverse(),
            lambda d: d['sources'][0].update(sha256='0' * 64),
            lambda d: d['sources'][0].update(gitBlob='0' * 40),
        ):
            document = copy.deepcopy(self.document)
            mutate(document)
            with self.subTest(mutate=mutate), patch(__name__ + '._drive') as drive:
                with self.assertRaisesRegex(AssertionError, 'pin drift'):
                    compare_receipts(_canonical(document).encode())
                drive.assert_not_called()
        for path in (FIXTURE, *sorted(SOURCE_PATHS)):
            with self.subTest(path=path), patch(__name__ + '._drive') as drive:
                with self.assertRaisesRegex(AssertionError, 'pin drift'):
                    compare_receipts(self.raw, read=lambda p: _read(p) + (b'\n' if p == path else b''))
                drive.assert_not_called()
        for raw in (b'{', b'\xff', b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', self.raw + b'{}'):
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, UnicodeError)):
                goldens._decode(raw)


if __name__ == '__main__':
    unittest.main()
