"""Portable source-informed expired hold/release histories; no golden update mode.

Only existing published FsmHost commands execute. Snapshots are detached local
diagnostics, excluding rejected-key bookkeeping; they are not read interfaces.
Import helper modules rather than TestCase classes to keep discovery unique.
"""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
import test_commerce_temporal_vectors as temporal
from integration_gate.catalogue import load_catalogue
from scripts.bootstrap_2_fixtures import read_bootstrap_2_input
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = 'reference/booking_resale_admission/fixtures/commerce_hold_release_inputs_v1.json'
GOLDEN = ROOT / 'reference/booking_resale_admission/fixtures/commerce_hold_release_receipts_v1.json'
SOURCE_PATHS = temporal.SOURCE_PATHS | frozenset({
    'reference/booking_resale_admission/test_commerce_temporal_vectors.py',
    'reference/booking_resale_admission/test_reservation_rejection_atomicity.py',
})
# Independent literal identities, actions and refusal/replay associations.
ORDER = ('clock', 'show', 'hold-a', 'expire', 'confirm-expired', 'hold-b-occupied',
         'release-a', 'retry-b-free', 'hold-b-fresh', 'replay-hold-a',
         'replay-release-a', 'replay-hold-b', 'retry-b-reused', 'retry-confirm',
         'conflict-b')
ACTIONS = ('reservation_set_clock', 'reservation_register_show', 'reservation_hold',
           'reservation_set_clock', 'reservation_confirm', 'reservation_hold',
           'reservation_release', 'reservation_hold', 'reservation_hold',
           'reservation_hold', 'reservation_release', 'reservation_hold',
           'reservation_hold', 'reservation_confirm', 'reservation_hold')
ORDERS = {'expired-held-at-boundary': ORDER, 'expired-held-after-boundary': ORDER}
REFUSALS = {'confirm-expired': 'RESERVATION_EXPIRED', 'hold-b-occupied': 'SLOT_OCCUPIED',
            'retry-b-free': 'SLOT_OCCUPIED', 'retry-b-reused': 'SLOT_OCCUPIED',
            'retry-confirm': 'RESERVATION_EXPIRED', 'conflict-b': 'IDEMPOTENCY_CONFLICT'}
REPLAYS = {'replay-hold-a': 'hold-a', 'replay-release-a': 'release-a',
           'replay-hold-b': 'hold-b-fresh'}
RETRIES = {'retry-b-free': 'hold-b-occupied', 'retry-b-reused': 'hold-b-occupied',
           'retry-confirm': 'confirm-expired', 'conflict-b': 'hold-b-occupied'}
_assert_paths = temporal._assert_paths


def _read(path):
    return read_bootstrap_2_input(path)


def _snapshot(host):
    # Use public canonical state to find available views, including both reservations.
    machine = host.machines['reservation']
    state = goldens._decode(machine.canonical_state().encode())
    views = {'reservations': {r['reservation_id']: machine.view(r['reservation_id'])
                              for r in state['reservations']}}
    if state['shows']:
        views['show'] = machine.view_show('show-1')
    return copy.deepcopy({
        'machines': {name: {'state': m.canonical_state(), 'digest': m.state_digest(),
                            'journal': m.export_journal()} for name, m in host.machines.items()},
        'views': views,
    })


def _validate(fixture):
    journey._check(type(fixture['fixture_version']) is int and fixture['fixture_version'] == 1,
                   'fixture version')
    journey._check(fixture['provenance'] == 'OFFLINE_CONFORMANCE_FIXTURE_ONLY', 'provenance')
    catalogue = load_catalogue(ROOT)
    journey._check(fixture['domain'] == catalogue.fsm_domain, 'fixture domain')
    journey._check(tuple(c['id'] for c in fixture['cases']) == tuple(ORDERS), 'case order')
    for i, case in enumerate(fixture['cases']):
        journey._check(tuple(s['id'] for s in case['steps']) == ORDER, 'step order')
        journey._check(tuple(s['action'] for s in case['steps']) == ACTIONS, 'action mapping')
        journey._check({s['id']: s['expect_error'] for s in case['steps'] if 'expect_error' in s}
                       == REFUSALS, 'refusal mapping')
        journey._check({s['id']: s['replay_of'] for s in case['steps'] if 'replay_of' in s}
                       == REPLAYS, 'replay mapping')
        clocks = case['clocks']
        journey._check(clocks == {
            'T0': 1000000, 'a_expires_ms': 1001000, 'observation_ms': 1001000 + i,
            'b_expires_ms': 1900000, 'meaning': 'SYNTHETIC_FIXTURE_INPUTS_ONLY'}, 'synthetic clocks')
        seen, keys = {}, set()
        for step in case['steps']:
            sid, action, body = step['id'], step['action'], step['body']
            journey._check(('expect' in step) != ('expect_error' in step), 'one expectation')
            spec = catalogue.fsm['commands'][action]
            journey._check(not problems(body, spec['schema']), 'command schema: ' + sid)
            journey._check(spec['subject_field'] in body and 'domain' not in body, 'subject/domain')
            key = body['idempotency_key']
            original = REPLAYS.get(sid, RETRIES.get(sid))
            if original:
                first = seen[original]
                journey._check(action == first['action'] and key == first['body']['idempotency_key'],
                               'replay/retry key binding')
                expected = copy.deepcopy(first['body'])
                if sid == 'conflict-b':
                    expected['buyer_role'] = 'buyer-changed'
                journey._check(_canonical(body) == _canonical(expected), 'replay/retry body binding')
            else:
                journey._check(key not in keys, 'fresh key required')
            if sid == 'hold-b-fresh':
                expected = dict(seen['hold-b-occupied']['body'], idempotency_key=key)
                journey._check(_canonical(body) == _canonical(expected), 'fresh hold body binding')
            keys.add(key)
            if 'expect' in step:
                expect, replay = step['expect'], sid in REPLAYS
                journey._check(expect['duplicate'] is replay and
                               expect['applied'] == (None if replay else spec['op']), 'accepted expectation')
                journals = expect['journal']
                journey._check(len(journals) == 5 and {j['machine'] for j in journals} ==
                               {'reservation', 'settlement', 'resale', 'admission', 'credit'},
                               'journal expectation coverage')
                journey._check(all(type(j['delta']) is int and j['delta'] ==
                                   int(j['machine'] == 'reservation' and not replay) for j in journals),
                               'journal delta expectation')
            seen[sid] = step
        for sid, field, clock in (
            ('clock', 'now_ms', 'T0'),
            ('expire', 'now_ms', 'observation_ms'),
            ('hold-a', 'expires_ms', 'a_expires_ms'),
            ('hold-b-occupied', 'expires_ms', 'b_expires_ms'),
        ):
            journey._check(seen[sid]['body'][field] == clocks[clock], 'clock body association: ' + sid)


def _drive(case):
    host = FsmHost()
    receipts, refusals, snapshots = {}, {}, {}
    flags = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
        'economic_finality_claimed', 'chain_issued', 'venue_credential_reissued', 'offline_admission'}
    before = _snapshot(host)
    for step in case['steps']:
        sid = step['id']
        try:
            receipt = host.call(step['action'], copy.deepcopy(step['body']))
        except FsmRejected as exc:
            after = _snapshot(host)
            journey._check(exc.code == step.get('expect_error'), 'unexpected refusal: ' + exc.code)
            journey._check(_canonical(before) == _canonical(after),
                           'refusal mutated state/digest/journal/views')
            refusals[sid] = exc.code
        else:
            after = _snapshot(host)
            journey._check('expect' in step, 'expected refusal was accepted')
            expect = step['expect']
            _assert_paths(receipt, {'duplicate': expect['duplicate'], 'applied': expect['applied'],
                                    **expect['paths']})
            if sid in REPLAYS:
                first = receipts[REPLAYS[sid]]
                journey._check(_canonical(journey._without_replay_keys(receipt)) ==
                               _canonical(journey._without_replay_keys(first)), 'immutable replay result')
                journey._check(_canonical(before) == _canonical(after),
                               'replay mutated state/digest/journal/views')
            for journal in expect['journal']:
                name = journal['machine']
                journey._check(len(after['machines'][name]['journal']) -
                               len(before['machines'][name]['journal']) == journal['delta'],
                               'journal delta: ' + sid + '/' + name)
            receipts[sid] = copy.deepcopy(receipt)
        snapshots[sid] = after
        for node in journey._walk([receipts.get(sid, {}), snapshots[sid]['views']]):
            for flag in flags & node.keys():
                journey._check(node[flag] is False, 'authority flag: ' + flag)
        _assert_paths(snapshots[sid]['views'], step.get('observe', {}))
        before = after
    _assert_paths(snapshots[ORDER[-1]]['views'], case['final_expect']['views'])
    journey._check(refusals == REFUSALS, 'refusals')
    return host, receipts, refusals, snapshots


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    journey._check(_canonical(fixture).encode() == fixture_raw, 'canonical input bytes differ')
    _validate(fixture)
    cases = []
    for i, case in enumerate(fixture['cases']):
        _host, receipts, refusals, snapshots = _drive(case)
        journey._check(not receipts.keys() & refusals.keys() and
                       receipts.keys() | refusals.keys() == set(ORDER), 'outcome coverage')
        steps = []
        for j, step in enumerate(case['steps']):
            outcome = dict(id=step['id'], action=step['action'],
                           input_ref=FIXTURE + '#/cases/%d/steps/%d/body' % (i, j),
                           diagnostic_snapshot=snapshots[step['id']])
            key = 'receipt' if step['id'] in receipts else 'rejection_code'
            outcome[key] = (receipts if key == 'receipt' else refusals)[step['id']]
            steps.append(outcome)
        cases.append(dict(id=case['id'], steps=steps))
    return dict(record_schema_version='kix-commerce-hold-release-receipts/1',
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


class CommerceHoldReleaseVectorTests(unittest.TestCase):
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

    def test_sources_schemas_and_unbound_reads(self):
        _validate(self.fixture)
        catalogue, host = load_catalogue(ROOT), FsmHost()
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.core_names + catalogue.fsm_names)
            self.assertNotIn(name, host._commands)
        for case in self.fixture['cases']:
            path, symbol = case['source_test'].split('::')
            self.assertIn(path, SOURCE_PATHS)
            self.assertEqual(symbol, 'ReservationFsmTests.test_expiry_does_not_release_until_an_explicit_release')
            self.assertIn('def ' + symbol.split('.')[1] + '(', _read(path).decode())
            self.assertEqual(case['contract_predicates'], [
                'docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#9.%d' % n for n in (2, 3, 4)])

    def test_expired_slot_retention_release_reuse_and_historical_replay(self):
        for case in self.fixture['cases']:
            host, receipts, refusals, snapshots = _drive(case)
            self.assertEqual(refusals, REFUSALS)
            for sid in ('expire', 'confirm-expired', 'hold-b-occupied'):
                views = snapshots[sid]['views']
                _assert_paths(views, {'reservations.reserve-a.phase': 'HELD',
                                      'reservations.reserve-a.expired': True,
                                      'reservations.reserve-a.slot_state': 'RESERVED',
                                      'reservations.reserve-a.slot_reservation_id': 'reserve-a'})
                self.assertEqual(set(views['reservations']), {'reserve-a'})
            for sid in ('release-a', 'retry-b-free'):
                _assert_paths(snapshots[sid]['views'], {
                    'reservations.reserve-a.phase': 'RELEASED',
                    'reservations.reserve-a.slot_state': 'FREE',
                    'reservations.reserve-a.slot_reservation_id': None})
            for sid in ORDER[8:]:
                views = snapshots[sid]['views']
                _assert_paths(views, {'reservations.reserve-a.phase': 'RELEASED',
                                      'reservations.reserve-a.slot_state': 'RESERVED',
                                      'reservations.reserve-a.slot_reservation_id': 'reserve-b',
                                      'reservations.reserve-b.phase': 'HELD',
                                      'reservations.reserve-b.expired': False,
                                      'reservations.reserve-b.slot_reservation_id': 'reserve-b'})
                self.assertEqual(views['show']['show']['slots'], [{
                    'slot': 0, 'state': 'RESERVED', 'reservation_id': 'reserve-b', 'right_id': None}])
            _assert_paths(receipts['replay-hold-a'], {'reservation.phase': 'HELD',
                'reservation.expired': False, 'reservation.slot_reservation_id': 'reserve-a'})
            _assert_paths(receipts['replay-release-a'], {'reservation.phase': 'RELEASED',
                'reservation.slot_state': 'FREE', 'reservation.slot_reservation_id': None})
            for replay, first in REPLAYS.items():
                self.assertEqual(_canonical(journey._without_replay_keys(receipts[replay])),
                                 _canonical(journey._without_replay_keys(receipts[first])))
            journal = host.machines['reservation'].export_journal()
            self.assertEqual([entry['op'] for entry in journal],
                             ['set_clock', 'register_show', 'hold', 'set_clock', 'release', 'hold'])

    def test_refusals_and_replays_preserve_all_machine_observations(self):
        for case in self.fixture['cases']:
            _host, _receipts, _errors, snapshots = _drive(case)
            for i, step in enumerate(case['steps']):
                if 'expect_error' in step or 'replay_of' in step:
                    before, after = snapshots[ORDER[i - 1]], snapshots[step['id']]
                    self.assertIsNot(before, after)
                    self.assertEqual(_canonical(before), _canonical(after))

    def test_detached_outcome_sensitivity_controls(self):
        mutations = (
            # Premature free before explicit release, and double occupancy after reuse.
            lambda s: s[3]['diagnostic_snapshot']['views']['show']['show']['slots'][0].update(state='FREE'),
            lambda s: s[8]['diagnostic_snapshot']['views']['reservations']['reserve-a'].update(phase='HELD'),
            lambda s: s[8]['diagnostic_snapshot']['views']['show']['show']['slots'].append(
                {'slot': 0, 'state': 'RESERVED', 'reservation_id': 'reserve-a', 'right_id': None}),
            lambda s: s[4].update(rejection_code='CHANGED'),
            lambda s: s[5].update(rejection_code='RESERVATION_EXPIRED'),
            lambda s: s[6]['receipt']['reservation'].update(slot_state='RESERVED'),
            lambda s: s[9]['receipt']['reservation'].update(phase='RELEASED'),
            lambda s: s[10]['receipt']['reservation'].update(slot_state='RESERVED'),
            lambda s: s[11]['receipt'].update(duplicate=1),
            lambda s: s[8]['diagnostic_snapshot']['machines']['reservation'].update(digest='0' * 64),
            lambda s: s[8]['diagnostic_snapshot']['machines']['reservation']['journal'].pop(),
            lambda s: s.pop(), lambda s: s.append(copy.deepcopy(s[0])), lambda s: s.reverse(),
            lambda s: s[0].update(input_ref=FIXTURE + '#/cases/0/steps/0/body'),
            lambda s: s[0].update(action='settlement_commit'), lambda s: s[0].update(id='changed'),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document['cases'][1]['steps'])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(AssertionError, 'canonical receipt bytes differ'):
                compare_receipts(_canonical(document).encode())

    def test_repinned_input_controls_fail_before_execution(self):
        mutations = (
            ('step order', lambda c: c['steps'].pop()),
            ('step order', lambda c: c['steps'].reverse()),
            ('action mapping', lambda c: c['steps'][0].update(action='resale_set_clock')),
            ('refusal mapping', lambda c: c['steps'][4].update(expect_error='CHANGED')),
            ('replay mapping', lambda c: c['steps'][9].pop('replay_of')),
            ('replay/retry key binding', lambda c: c['steps'][9]['body'].update(idempotency_key='fresh')),
            ('replay/retry body binding', lambda c: c['steps'][7]['body'].update(buyer_role='changed')),
            ('fresh key', lambda c: c['steps'][8]['body'].update(idempotency_key='hold-b-occupied')),
            ('fresh hold body', lambda c: c['steps'][8]['body'].update(buyer_role='changed')),
            ('command schema', lambda c: c['steps'][1]['body'].update(capacity=True)),
            ('journal delta expectation', lambda c: c['steps'][0]['expect']['journal'][0].update(delta=True)),
            ('clock body association', lambda c: c['steps'][3]['body'].update(now_ms=1001001)),
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

    def test_injected_refusal_and_replay_effects_are_detected(self):
        real_call = FsmHost.call
        for case in self.fixture['cases']:
            for target in (s for s in case['steps'] if 'expect_error' in s or 'replay_of' in s):
                calls = 0
                target_position = ORDER.index(target['id'])

                def corrupting_call(host, action, body):
                    nonlocal calls
                    position = calls
                    calls += 1
                    try:
                        return real_call(host, action, body)
                    finally:
                        if position == target_position:
                            # Inject an existing command into another machine, including a
                            # journal-only effect. No protected code or host is edited.
                            real_call(host, 'resale_set_clock', {
                                'subject_id': 'clock', 'idempotency_key': 'injected', 'now_ms': 1000000})

                with self.subTest(case=case['id'], target=target['id']), patch.object(FsmHost, 'call', corrupting_call):
                    with self.assertRaisesRegex(AssertionError, 'mutated state/digest/journal/views'):
                        _drive(case)

    def test_pins_and_strict_json_controls(self):
        for mutate in (
            lambda d: d['fixture'].update(sha256='0' * 64),
            lambda d: d['fixture'].update(gitBlob='0' * 40),
            lambda d: d['sources'].pop(), lambda d: d['sources'].append(d['sources'][0]),
            lambda d: d['sources'].reverse(), lambda d: d['sources'][0].update(sha256='0' * 64),
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
