"""Source-informed portable §11.4 cancellation evidence; no golden update mode.

Helper modules are imported without importing TestCase classes. Diagnostic
snapshots are detached Python observations, never published read responses.
"""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
import test_commerce_entry_resale_order_vectors as ordering
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_admission_cancellation_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_admission_cancellation_receipts_v1.json"
SOURCE_PATHS = ordering.SOURCE_PATHS | frozenset({
    "reference/booking_resale_admission/test_commerce_entry_resale_order_vectors.py",
    "reference/booking_resale_admission/test_admission_rejection_atomicity.py",
})
# Independent case/step/action and refusal maps, not derived from input JSON.
SETUP = ("reservation-clock", "show", "hold", "confirm")
ORDERS = {
    "cancel-before-issue": SETUP + ("cancel-before-issue", "admission-clock", "admission-adopt"),
    "payment-without-issue": SETUP + ("payment", "admission-clock", "admission-adopt"),
    "cancel-after-issue-and-consume": SETUP + (
        "payment", "issue", "admission-clock", "admission-adopt", "cancel-issued",
        "authorize", "consume", "cancel-consumed"),
}
REFUSALS = {
    "cancel-before-issue": {"admission-adopt": "TICKET_CANCELLED"},
    "payment-without-issue": {"admission-adopt": "TICKET_NOT_ISSUED"},
    "cancel-after-issue-and-consume": {
        "cancel-issued": "CANCEL_AFTER_ISSUE", "cancel-consumed": "CANCEL_AFTER_ISSUE"},
}
ACTIONS = dict(zip(
    ("reservation-clock", "show", "hold", "confirm", "payment", "issue", "admission-clock",
     "admission-adopt", "authorize", "consume", "cancel-before-issue", "cancel-issued", "cancel-consumed"),
    ("reservation_set_clock", "reservation_register_show", "reservation_hold", "reservation_confirm",
     "reservation_observe_payment", "reservation_issue", "admission_set_clock", "admission_adopt_issued",
     "admission_authorize_admission", "admission_consume", "reservation_cancel", "reservation_cancel", "reservation_cancel")))
SOURCE_TEST = ("reference/booking_resale_admission/test_admission_fsm.py::AdmissionFsmTests."
               "test_cancel_before_issue_blocks_entry_and_cancel_after_issue_does_not_void_it")
CLOCKS = {"T0": 1000000, "amount": 10001, "authorization_expires_ms": 1120000,
          "reservation_expires_ms": 1900000, "meaning": "SYNTHETIC_FIXTURE_INPUTS_ONLY"}
_assert_paths = ordering._assert_paths
_snapshot = ordering._snapshot
_assert_views = ordering._assert_views


def _read(path):
    return (ROOT / path).read_bytes()


def _validate(fixture):
    journey._check(type(fixture["fixture_version"]) is int and fixture["fixture_version"] == 1,
                   "fixture version")
    journey._check(fixture["provenance"] == "OFFLINE_CONFORMANCE_FIXTURE_ONLY", "provenance")
    catalogue = load_catalogue(ROOT)
    journey._check(fixture["domain"] == catalogue.fsm_domain, "fixture domain")
    journey._check(tuple(c["id"] for c in fixture["cases"]) == tuple(ORDERS), "case order")
    for case in fixture["cases"]:
        ids = tuple(s["id"] for s in case["steps"])
        journey._check(ids == ORDERS[case["id"]] and len(set(ids)) == len(ids), "step order")
        errors = {s["id"]: s["expect_error"] for s in case["steps"] if "expect_error" in s}
        journey._check(errors == REFUSALS[case["id"]], "refusal mapping")
        journey._check(case["source_test"] == SOURCE_TEST, "source regression")
        journey._check(case["contract_predicates"] == [
            "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#11.4"], "contract predicates")
        journey._check(_canonical(case["clocks"]) == _canonical(CLOCKS), "synthetic clocks")
        keys = set()
        for step in case["steps"]:
            journey._check(("expect" in step) != ("expect_error" in step), "one expectation")
            action, body = step["action"], step["body"]
            journey._check(action in catalogue.fsm_names, "unpublished action")
            journey._check(action == ACTIONS[step["id"]], "step action association")
            spec = catalogue.fsm["commands"][action]
            journey._check(not problems(body, spec["schema"]), "command schema: " + step["id"])
            journey._check(spec["subject_field"] in body and "domain" not in body,
                           "subject/domain")
            key = body["idempotency_key"]
            journey._check(key not in keys, "fresh key required")
            keys.add(key)
            if "expect" in step:
                expect = step["expect"]
                journey._check(expect["duplicate"] is False and expect["applied"] == spec["op"],
                               "accepted expectation")
                touched = {spec["machine"]}
                if action in {"admission_set_clock", "admission_authorize_admission", "admission_consume"}:
                    touched.add("reservation")
                expected_deltas = {m: int(m in touched) for m in
                                   ("settlement", "reservation", "resale", "admission", "credit")}
                journals = expect["journal"]
                journey._check(len(journals) == 5 and
                               {j["machine"] for j in journals} == set(expected_deltas) and
                               all(type(j["delta"]) is int and j["delta"] == expected_deltas[j["machine"]]
                                   for j in journals), "journal expectation coverage/deltas")
            if action == "reservation_cancel":
                journey._check(set(body) == {"reservation_id", "idempotency_key"}, "published cancel body")



def _drive(case):
    host = FsmHost()
    accepted, receipts, refusals, snapshots = set(), {}, {}, {}
    flags = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
        "economic_finality_claimed", "chain_issued", "venue_credential_reissued", "offline_admission"}
    for step in case["steps"]:
        before = _snapshot(host, accepted)
        try:
            receipt = host.call(step["action"], copy.deepcopy(step["body"]))
        except FsmRejected as exc:
            journey._check(exc.code == step.get("expect_error"), "unexpected refusal: " + exc.code)
            journey._check(_canonical(before) == _canonical(_snapshot(host, accepted)),
                           "refusal mutated state/digest/journal/views")
            refusals[step["id"]] = exc.code
        else:
            journey._check("expect" in step, "expected refusal was accepted")
            expect = step["expect"]
            _assert_paths(receipt, {"duplicate": expect["duplicate"], "applied": expect["applied"],
                                    **expect["paths"]})
            for journal in expect["journal"]:
                name = journal["machine"]
                journey._check(len(host.machines[name].export_journal()) -
                               len(before["machines"][name]["journal"]) == journal["delta"],
                               "journal delta: " + step["id"] + "/" + name)
            receipts[step["id"]] = copy.deepcopy(receipt)
            accepted.add(step["action"])
        snapshot = _snapshot(host, accepted)
        for node in journey._walk([receipts.get(step["id"], {}), snapshot["views"]]):
            for flag in flags & node.keys():
                journey._check(node[flag] is False, "authority flag: " + flag)
        snapshots[step["id"]] = snapshot
        _assert_views(host, accepted, step.get("observe", {}))
    _assert_views(host, accepted, case["final_expect"]["views"])
    for fact in case["final_expect"]["separate_facts"]:
        _assert_paths(receipts[fact["step"]], {fact["path"]: fact["value"]})
    journey._check(refusals == REFUSALS[case["id"]], "refusals")
    return host, receipts, refusals, snapshots


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    journey._check(_canonical(fixture).encode("utf-8") == fixture_raw, "canonical input bytes differ")
    _validate(fixture)
    cases = []
    for i, case in enumerate(fixture["cases"]):
        _host, receipts, refusals, snapshots = _drive(case)
        ids = {step["id"] for step in case["steps"]}
        journey._check(not receipts.keys() & refusals.keys() and
                       receipts.keys() | refusals.keys() == ids, "outcome coverage")
        steps = []
        for j, step in enumerate(case["steps"]):
            outcome = dict(id=step["id"], action=step["action"],
                           input_ref=FIXTURE + "#/cases/%d/steps/%d/body" % (i, j),
                           diagnostic_snapshot=snapshots[step["id"]])
            key = "receipt" if step["id"] in receipts else "rejection_code"
            outcome[key] = (receipts if key == "receipt" else refusals)[step["id"]]
            steps.append(outcome)
        cases.append(dict(id=case["id"], steps=steps))
    return dict(record_schema_version="kix-commerce-admission-cancellation-receipts/1",
                record_kind="IN_PROCESS_MOCK_RECEIPT_VECTORS", normative=False,
                fixture=fixture_pin, sources=sources, cases=cases)


def compare_receipts(raw, read=_read):
    expected = goldens._decode(raw)
    fixture_raw = read(FIXTURE)
    fixture_pin = goldens._pin(FIXTURE, fixture_raw)
    sources = [goldens._pin(path, read(path)) for path in sorted(SOURCE_PATHS)]
    journey._check(expected["fixture"] == fixture_pin, "fixture pin drift")
    journey._check(expected["sources"] == sources, "source pin drift/set/order")
    observed = _observe(fixture_raw, fixture_pin, sources)
    journey._check(_canonical(observed).encode("utf-8") == raw,
                   "complete canonical receipt bytes differ")
    return observed


class CommerceAdmissionCancellationVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = GOLDEN.read_bytes()
        cls.document = goldens._decode(cls.raw)
        cls.fixture = goldens._decode(_read(FIXTURE))

    def test_complete_output_bytes_and_references(self):
        observed = compare_receipts(self.raw)
        self.assertEqual(sum(len(c['steps']) for c in observed['cases']), 26)
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
                self.assertEqual(set(outcome['diagnostic_snapshot']['machines']),
                                 {'reservation', 'resale', 'admission', 'settlement', 'credit'})

    def test_schemas_sources_and_unbound_reads(self):
        _validate(self.fixture)
        path, symbol = SOURCE_TEST.split('::')
        self.assertIn(path, SOURCE_PATHS)
        self.assertIn('def ' + symbol.split('.')[1] + '(', _read(path).decode())
        catalogue, host = load_catalogue(ROOT), FsmHost()
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.names)
            self.assertNotIn(name, host._commands)

    def test_cancellation_before_issuance_and_payment_are_not_issuance(self):
        for case, phase, code in zip(self.fixture['cases'][:2],
                                     ('CANCELLED', 'PAYMENT_NOTED'),
                                     ('TICKET_CANCELLED', 'TICKET_NOT_ISSUED')):
            host, receipts, refusals, snapshots = _drive(case)
            self.assertEqual(refusals, {'admission-adopt': code})
            _assert_paths(snapshots['admission-adopt']['views'], {
                'reservation.phase': phase, 'reservation.issuance_id': None,
                'reservation.right': None, 'reservation.admission_id': None,
                'reservation.consume_id': None,
                'reservation.payment_ref': None if phase == 'CANCELLED' else 'ab' * 32})
            self.assertNotIn('credential', snapshots['admission-adopt']['views'])
            state = goldens._decode(host.machines['admission'].canonical_state().encode())
            self.assertEqual(state['credentials'], [])
            self.assertNotIn('issue', receipts)

    def test_issued_credential_survives_cancellation_and_explicit_entry_stages(self):
        _host, receipts, refusals, ss = _drive(self.fixture['cases'][2])
        self.assertEqual(refusals, REFUSALS['cancel-after-issue-and-consume'])
        _assert_paths(receipts['payment'], {'reservation.phase': 'PAYMENT_NOTED',
                                           'reservation.issuance_id': None, 'reservation.right': None})
        _assert_paths(receipts['issue'], {'reservation.phase': 'ISSUED', 'evidence.version': 1})
        self.assertNotIn('credential', ss['issue']['views'])
        for sid in ('admission-adopt', 'cancel-issued'):
            _assert_paths(ss[sid]['views'], {
                'reservation.phase': 'ISSUED', 'reservation.right.version': 1,
                'credential.phase': 'ELIGIBLE', 'credential.version': 1,
                'credential.admission_id': None, 'credential.consume_id': None})
        _assert_paths(ss['authorize']['views'], {
            'reservation.phase': 'ADMISSION_AUTHORIZED', 'reservation.right.version': 1,
            'credential.phase': 'AUTHORIZED', 'credential.admission_id': 'admit-1',
            'credential.consume_id': None})
        for sid in ('consume', 'cancel-consumed'):
            _assert_paths(ss[sid]['views'], {
                'reservation.phase': 'CONSUMED', 'reservation.right.version': 2,
                'reservation.consume_id': 'consume-1', 'credential.phase': 'CONSUMED',
                'credential.admission_id': None, 'credential.consume_id': 'consume-1',
                'credential.version_after': 2})
        for sid in ORDERS['cancel-after-issue-and-consume'][5:]:
            _assert_paths(ss[sid]['views'], {
                'reservation.issuance_id': 'issue-1', 'reservation.payment_ref': 'ab' * 32,
                'reservation.right.holder_role': 'buyer-1'})
        _assert_paths(receipts['consume'], {'evidence.decision': 'CONSUMED_ONCE',
                                           'evidence.version_after': 2})
        # Earlier detached receipts retain their original phase after consumption.
        self.assertEqual(receipts['admission-adopt']['credential']['phase'], 'ELIGIBLE')
        self.assertEqual(receipts['authorize']['credential']['phase'], 'AUTHORIZED')

    def test_refusals_preserve_all_business_snapshots(self):
        for case in self.fixture['cases']:
            _host, _receipts, refusals, ss = _drive(case)
            for i, step in enumerate(case['steps']):
                if step['id'] in refusals:
                    before, after = ss[case['steps'][i - 1]['id']], ss[step['id']]
                    self.assertIsNot(before, after)
                    self.assertEqual(_canonical(before), _canonical(after))
        # Snapshots intentionally exclude process-local rejected-key retention.
        # The existing machines retain refusal bindings outside canonical state
        # and accepted journals; these vectors promise no restart persistence.

    def test_rejected_keys_are_retained_only_as_process_local_bindings(self):
        for case in self.fixture['cases']:
            host, receipts, refusals, _ss = _drive(case)
            accepted = {s['action'] for s in case['steps'] if s['id'] in receipts}
            for step in case['steps']:
                if step['id'] not in refusals:
                    continue
                before = _snapshot(host, accepted)
                with self.subTest(case=case['id'], step=step['id']):
                    with self.assertRaises(FsmRejected) as repeated:
                        host.call(step['action'], copy.deepcopy(step['body']))
                    self.assertEqual(repeated.exception.code, step['expect_error'])
                    changed = copy.deepcopy(step['body'])
                    subject = 'reservation_id' if step['action'] == 'reservation_cancel' else 'right_id'
                    changed[subject] = 'different-subject'
                    with self.assertRaises(FsmRejected) as conflict:
                        host.call(step['action'], changed)
                    self.assertEqual(conflict.exception.code, 'IDEMPOTENCY_CONFLICT')
                    self.assertEqual(_canonical(before), _canonical(_snapshot(host, accepted)))
        # This checks only the same live host. Accepted journals do not restore
        # these rejected bindings; no durable retention claim follows.

    def test_detached_output_corruption_controls(self):
        mutations = (
            lambda s: s[8].update(rejection_code='TICKET_CANCELLED'),
            lambda s: s[-1].update(rejection_code='TICKET_NOT_ISSUED'),
            lambda s: s[4]['receipt']['reservation'].update(issuance_id='issue-1'),
            lambda s: s[5]['receipt']['evidence'].update(chain_issued=0),
            lambda s: s[7]['receipt']['credential'].update(phase='AUTHORIZED'),
            lambda s: s[9]['receipt']['credential'].update(consume_id='invented'),
            lambda s: s[10]['receipt']['evidence'].update(version_after=1),
            lambda s: s[10]['receipt']['credential'].pop('consume_id'),
            lambda s: s[10]['receipt'].update(extra=None),
            lambda s: s[-1]['diagnostic_snapshot']['views']['reservation']['right'].update(holder_role='buyer-2'),
            lambda s: s[-1]['diagnostic_snapshot']['views']['credential'].update(phase='CANCELLED'),
            lambda s: s[-1]['diagnostic_snapshot']['machines']['reservation'].update(state='changed'),
            lambda s: s[-1]['diagnostic_snapshot']['machines']['resale'].update(digest='0' * 64),
            lambda s: s[-1]['diagnostic_snapshot']['machines']['admission']['journal'].pop(),
            lambda s: s.pop(), lambda s: s.append(copy.deepcopy(s[0])), lambda s: s.reverse(),
            lambda s: s[0].update(input_ref=FIXTURE + '#/cases/0/steps/0/body'),
            lambda s: s[0].update(action='settlement_commit'), lambda s: s[0].update(id='changed'),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document['cases'][2]['steps'])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(AssertionError, 'canonical receipt bytes differ'):
                compare_receipts(_canonical(document).encode())
        for i, wrong in ((0, 'TICKET_NOT_ISSUED'), (1, 'TICKET_CANCELLED')):
            document = copy.deepcopy(self.document)
            document['cases'][i]['steps'][-1]['rejection_code'] = wrong
            with self.subTest(case=i), self.assertRaisesRegex(AssertionError, 'canonical receipt bytes differ'):
                compare_receipts(_canonical(document).encode())

    def test_repinned_input_controls_fail_before_execution(self):
        mutations = (
            ('step order', lambda c: c['steps'].pop()),
            ('step order', lambda c: c['steps'].append(copy.deepcopy(c['steps'][0]))),
            ('step order', lambda c: c['steps'].reverse()),
            ('refusal mapping', lambda c: c['steps'][-1].update(expect_error='CHANGED')),
            ('step action association', lambda c: c['steps'][0].update(action='resale_set_clock')),
            ('fresh key', lambda c: c['steps'][-1]['body'].update(idempotency_key='hold')),
            ('command schema', lambda c: c['steps'][1]['body'].update(capacity=True)),
            ('command schema', lambda c: c['steps'][4]['body'].update(domain='invented')),
            ('journal expectation', lambda c: c['steps'][0]['expect']['journal'][0].update(delta=True)),
            ('journal expectation', lambda c: c['steps'][0]['expect']['journal'].pop()),
            ('accepted expectation', lambda c: c['steps'][0]['expect'].update(duplicate=0)),
            ('source regression', lambda c: c.update(source_test='invented')),
            ('contract predicates', lambda c: c.update(contract_predicates=[])),
            ('synthetic clocks', lambda c: c['clocks'].update(T0=True)),
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

    def test_injected_effect_on_each_refusal_is_detected(self):
        real_call = FsmHost.call
        for case in self.fixture['cases']:
            for target in (s for s in case['steps'] if 'expect_error' in s):
                def corrupting_call(host, action, body):
                    try:
                        return real_call(host, action, body)
                    finally:
                        if action == target['action'] and body == target['body']:
                            real_call(host, 'resale_set_clock', {
                                'subject_id': 'clock', 'idempotency_key': 'injected-effect', 'now_ms': 1000001})
                with self.subTest(case=case['id'], target=target['id']), patch.object(FsmHost, 'call', corrupting_call):
                    with self.assertRaisesRegex(AssertionError, 'mutated state/digest/journal/views'):
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
            with self.subTest(mutate=mutate), patch(__name__ + '.FsmHost') as host:
                with self.assertRaisesRegex(AssertionError, 'pin drift'):
                    compare_receipts(_canonical(document).encode())
                host.assert_not_called()
        for path in (FIXTURE, *sorted(SOURCE_PATHS)):
            with self.subTest(path=path), patch(__name__ + '.FsmHost') as host:
                with self.assertRaisesRegex(AssertionError, 'pin drift'):
                    compare_receipts(self.raw, read=lambda p: _read(p) + (b'\n' if p == path else b''))
                host.assert_not_called()
        for raw in (b'{', b'\xff', b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', self.raw + b'{}'):
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, UnicodeError)):
                goldens._decode(raw)
        with patch(__name__ + '.FsmHost') as host:
            fixture = copy.deepcopy(self.fixture)
            fixture['cases'].reverse()
            with self.assertRaisesRegex(AssertionError, 'case order'):
                _validate(fixture)
            host.assert_not_called()


if __name__ == '__main__':
    unittest.main()
