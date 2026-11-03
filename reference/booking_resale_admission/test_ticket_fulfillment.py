"""Source-informed explicit fulfillment composition; no sockets or live providers."""

from contextlib import redirect_stdout
from copy import deepcopy
import inspect
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

import admission_cli
import booking_cli
import resale_cli
from admission_fixture import FixtureError
from admission_fsm import AdmissionError, AdmissionMachine
from admission_session import AdmissionSession
from booking_session import BookingInputError, BookingSession
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine
from resale_session import ResaleSession
from test_admission_session import assert_flags
from test_resale_fsm import assert_not_final as resale_flags
from test_reservation_fsm import assert_not_final as booking_flags
from test_ticket_operations_session import direct_call, direct_graph, machines, outcome, snapshot
from ticket_operations_cli import dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_fulfillment_session.json'
TRANSCRIPT = HERE / 'fixtures/ticket_operations_fulfillment.jsonl'


def fixture():
    return json.loads(FIXTURE.read_text())


def requests():
    return [json.loads(line) for line in TRANSCRIPT.read_text().splitlines()]


def session_from(value):
    return TicketOperationsSession(
        setup=value['setup'],
        offer_source=FakeResaleOfferSource(recordings={e['offer_id']: e['recorded_text']
                                                     for e in value['offers']}),
        presentation_source=FakePresentationSource(recordings={
            (e['operation'], e['presentation_id']): e['recorded_text']
            for e in value['presentations']}))


def run(session, rows):
    output = io.StringIO()
    with redirect_stdout(output):
        status = run_requests(session, [json.dumps(row) for row in rows])
    return status, [json.loads(line) for line in output.getvalue().splitlines()]


class TicketFulfillmentTests(unittest.TestCase):
    def graph(self, value=None):
        self.value = fixture() if value is None else value
        self.session = session_from(self.value)
        self.control = direct_graph(self.value['setup'])
        self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))

    def step(self, row, code=None):
        before = snapshot(machines(self.session))
        expected = outcome(lambda: direct_call(self.control, row, self.value))
        result = outcome(lambda: dispatch_request(self.session, row))
        self.assertEqual(result, expected)
        self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))
        if code is not None:
            self.assertEqual(result, {'error': {'code': code}})
        if 'error' in result:
            self.assertEqual(snapshot(machines(self.session)), before)
        else:
            flags = {'booking': booking_flags, 'resale': resale_flags, 'admission': assert_flags}
            flags[row['surface']](self, result.get('receipt', result.get('view')))
        return result

    def test_prepared_second_ticket_matches_direct_graph(self):
        self.graph()
        graph = machines(self.session)
        rows, results = requests(), []
        self.assertEqual(self.session.booking.view('reserve-2')['phase'], 'PAYMENT_NOTED')
        for desk in (self.session.resale, self.session.admission):
            self.assertEqual(outcome(lambda: desk._machine.view_right('issue-2')
                             if desk is self.session.resale else desk.view('issue-2')),
                             {'error': {'code': 'UNKNOWN_RIGHT'}})
        offers, presentations = [], []
        for index, row in enumerate(rows):
            before = snapshot(graph)
            result = self.step(row)
            results.append(result)
            allowed = ({1} if row['surface'] == 'booking' else
                       {2} if row['surface'] == 'resale' else
                       {1, 3} if row['operation'] in ('authorize_admission', 'consume') else {3})
            after = snapshot(graph)
            for n in set(range(4)) - allowed:
                self.assertEqual(after[n], before[n], (index, n))
            if row['operation'] == 'list_resale':
                offers.append(row['arguments']['offer_id'])
            if row['operation'] in ('authorize_admission', 'consume'):
                presentations.append((row['operation'], row['arguments']['presentation_id']))
            self.assertEqual(self.session.resale._adapter._source.calls, tuple(offers))
            self.assertEqual(self.session.admission._adapter._source.calls, tuple(presentations))
            if index == 1:  # binding doesn't issue, adopt, or call settlement commands
                view = self.session.booking.view('reserve-2')
                self.assertEqual(view['phase'], 'PAYMENT_NOTED')
                self.assertIsNone(view['right'])
                self.assertEqual(view['settlement_gate'], 'BOUND')
            if index == 2:
                self.assertEqual(result['receipt']['reservation']['phase'], 'ISSUED')
                self.assertEqual(result['receipt']['reservation']['settlement_gate'], 'MOCK_COMMIT_OBSERVED')
                self.assertIsNone(result['receipt']['reservation']['right']['listing_id'])
            if index == 3:
                self.assertEqual(outcome(lambda: self.session.admission.view('issue-2')),
                                 {'error': {'code': 'UNKNOWN_RIGHT'}})
            if index == 4:
                self.assertIsNone(self.session.resale.view_right('issue-2')['ticket']['active_listing_id'])
                self.assertEqual(self.session.admission.view('issue-2')['phase'], 'ELIGIBLE')
            if index == 9:  # authorization doesn't consume
                self.assertEqual(self.session.admission.view('issue-2')['phase'], 'AUTHORIZED')
                self.assertEqual(self.session.booking.view('reserve-2')['right']['version'], 1)
        self.assertEqual([r['error']['code'] for r in results if 'error' in r],
                         ['LISTING_LOCKED', 'LISTING_LOCKED'])
        for first, replay in ((2, 12), (3, 13), (4, 14)):
            self.assertEqual(results[replay]['receipt'],
                             results[first]['receipt'] | {'duplicate': True, 'applied': None})
        self.assertEqual(results[12]['receipt']['evidence']['version'], 1)
        self.assertEqual(results[15]['view']['right']['version'], 2)
        self.assertEqual(results[17]['view']['phase'], 'CONSUMED')
        self.assertEqual(results[17]['view']['version'], 2)
        self.assertEqual(results[16]['view']['right']['version'], 1)  # resale doesn't synchronize

    def test_fulfillment_file_and_stdin(self):
        self.graph()
        expected = []
        for row in requests():
            result = self.step(row)
            expected.append(result | {'surface': row['surface'], 'operation': row['operation']})
        for selector, stdin in ((str(TRANSCRIPT), None), ('-', TRANSCRIPT.read_text())):
            result = subprocess.run([sys.executable, str(HERE/'ticket_operations_cli.py'),
                                     '--fixture', str(FIXTURE), '--requests', selector],
                                    input=stdin, text=True, capture_output=True, check=False)
            self.assertEqual((result.returncode, result.stderr), (1, ''))
            self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
        self.assertEqual(run(load_fixture(FIXTURE), requests()[:6])[0], 0)
        self.assertEqual(run(load_fixture(FIXTURE), [requests()[2], requests()[0]])[0], 2)

    def test_booking_clock_successful_replay_and_no_key_on_local_refusal(self):
        for row in requests()[1:3]:
            self.graph()
            before = snapshot(machines(self.session))
            with self.assertRaises(BookingInputError):
                dispatch_request(self.session, row)
            self.assertEqual(snapshot(machines(self.session)), before)
            with self.assertRaises(ReservationError):
                self.session.booking.set_clock('wrong', now_ms=1000000, idempotency_key='bad-clock')
            with self.assertRaises(BookingInputError):
                dispatch_request(self.session, row)
            self.assertTrue(self.step(requests()[0])['receipt']['duplicate'])
            self.step(row)  # the formerly locally refused key is still available

    def test_issuance_before_payment_and_retained_refusal(self):
        value = fixture()
        value['setup'] = [e for e in value['setup']
                          if not (e['operation'] == 'observe_payment' and e['subject_id'] == 'order-2')]
        self.graph(value)
        self.step(requests()[0])
        self.step(requests()[2], 'ILLEGAL_TRANSITION')
        for tickets in (machines(self.session)[1], self.control[1]):
            tickets.observe_payment('order-2', payment_ref='cd'*32, amount=10001, idempotency_key='later-pay')
        self.step(requests()[2], 'ILLEGAL_TRANSITION')
        result = self.step(requests()[2] | {'arguments': requests()[2]['arguments'] |
                                           {'idempotency_key': 'unbound-fresh'}})
        self.assertEqual(result['receipt']['reservation']['settlement_gate'], 'UNBOUND')
        self.assertIs(result['receipt']['reservation']['mock_settlement_commit_observed'], False)

    def test_uncommitted_mismatched_and_expired_issuance(self):
        for kind, code in (('uncommitted', 'SETTLEMENT_NOT_COMMITTED'),
                           ('mismatch', 'SETTLEMENT_AMOUNT_MISMATCH'),
                           ('expired', 'RESERVATION_EXPIRED')):
            with self.subTest(kind=kind):
                value = fixture()
                commit = next(e for e in value['setup'] if e['subject_id'] == 'claim-2'
                              and e['operation'] == 'commit')
                if kind == 'uncommitted':
                    value['setup'].remove(commit)
                if kind == 'mismatch':
                    for e in value['setup']:
                        if e['subject_id'] == 'claim-2':
                            for field in ('gross', 'amount'):
                                if field in e['body']:
                                    e['body'][field] = 10000
                self.graph(value)
                for row in requests()[:2]:
                    self.step(row)
                if kind == 'expired':
                    self.step(requests()[0] | {'arguments': dict(subject_id='clock', now_ms=1120001,
                                                               idempotency_key='expired-clock')})
                self.step(requests()[2], code)
                if kind == 'uncommitted':
                    for book in (machines(self.session)[0], self.control[0]):
                        book.commit(commit['subject_id'], idempotency_key=commit['idempotency_key'],
                                    **commit['body'])
                    self.step(requests()[2], code)
                    self.step(requests()[2] | {'arguments': requests()[2]['arguments'] |
                                               {'idempotency_key': 'committed-fresh'}})
                self.assertIsNone(self.session.resale.view_right('issue-1')['ticket']['active_listing_id'])

    def test_adoption_refusals_are_atomic_and_require_explicit_fresh_keys(self):
        for index in (3, 4):
            with self.subTest(surface=requests()[index]['surface']):
                self.graph()
                adopt = requests()[index]
                self.step(adopt, 'TICKET_NOT_ISSUED')
                for row in requests()[:3]:
                    self.step(row)
                self.step(adopt, 'TICKET_NOT_ISSUED')
                for field, changed, code in (
                    ('quote_ref', 'other-quote', 'ORDER_BINDING_CONFLICT'),
                    ('payment_ref', 'ef'*32, 'PAYMENT_BINDING_CONFLICT')):
                    bad = adopt | {'arguments': adopt['arguments'] |
                                   {field: changed, 'idempotency_key': 'bad-' + field}}
                    self.step(bad, code)
                    self.step(bad, code)
                fresh = adopt | {'arguments': adopt['arguments'] | {'idempotency_key': 'fresh-adopt'}}
                self.step(fresh)
                self.step(fresh)
                self.step(fresh | {'arguments': fresh['arguments'] | {'quote_ref': 'changed'}},
                          'IDEMPOTENCY_CONFLICT')
                self.step(fresh | {'arguments': fresh['arguments'] |
                                   {'quote_ref': 'changed', 'idempotency_key': 'conflicting-adopt'}},
                          'ISSUANCE_BINDING_CONFLICT')

    def test_same_key_changed_subject_body_or_operation(self):
        self.graph()
        for row in requests()[:5]:
            self.step(row)
        bind, issue = requests()[1:3]
        self.step(bind)
        self.step(issue)
        for row in (
            bind | {'arguments': bind['arguments'] | {'settlement_id': 'claim-1'}},
            issue | {'arguments': issue['arguments'] | {'issuance_id': 'other-issue'}},
            issue | {'arguments': issue['arguments'] | {'order_id': 'order-1'}},
            issue | {'arguments': issue['arguments'] | {'idempotency_key': bind['arguments']['idempotency_key']}},
        ):
            self.step(row, 'IDEMPOTENCY_CONFLICT')

    def test_all_new_operations_forward_opaque_arguments_once_without_defaults(self):
        for surface, cli, cls, fsm, error_cls, indices in (
            ('booking', booking_cli, BookingSession, ReservationMachine, ReservationError, (1, 2)),
            ('resale', resale_cli, ResaleSession, ResaleMachine, ResaleError, (3,)),
            ('admission', admission_cli, AdmissionSession, AdmissionMachine, AdmissionError, (4,)),
        ):
            for index in indices:
                row = requests()[index]
                operation = row['operation']
                fields = set(row['arguments'])
                self.assertEqual(set(inspect.signature(getattr(cls, operation)).parameters) - {'self'}, fields)
                self.assertEqual(cli._DISPATCH[operation][1:], (fields, 'receipt'))
                for nulls in (False, True):
                    machine = Mock(spec=fsm)
                    session = cls(machine) if surface == 'booking' else cls(machine, Mock())
                    if surface == 'booking':
                        session.set_clock('clock', now_ms=0, idempotency_key='clock')
                        machine.reset_mock()
                    args = {field: object() for field in fields}
                    if nulls and surface != 'booking':
                        args.update(reservation_id=None, quote_ref=None)
                    original = args.copy()
                    receipt = {'opaque': object()}
                    method = getattr(machine, operation)
                    method.return_value = receipt
                    result = cli.dispatch_request(session, dict(operation=operation, arguments=args))
                    self.assertIs(result['receipt'], receipt)
                    subject = args.pop({'booking': 'issuance_id' if operation == 'issue' else 'reservation_id',
                                        'resale': 'right_id', 'admission': 'right_id'}[surface])
                    method.assert_called_once_with(subject, **args)
                    self.assertEqual(len(machine.mock_calls), 1)
                    error = error_cls('OPAQUE_REFUSAL')
                    method.side_effect = error
                    machine.reset_mock()
                    with self.assertRaises(error_cls) as caught:
                        getattr(session, operation)(**original)
                    self.assertIs(caught.exception, error)
                    method.assert_called_once_with(subject, **args)
                    self.assertEqual(len(machine.mock_calls), 1)

    def test_new_selectors_strict_standalone_and_shared_arguments(self):
        for row in requests()[1:5]:
            cli = {'booking': booking_cli, 'resale': resale_cli, 'admission': admission_cli}[row['surface']]
            args = row['arguments']
            variants = [{k: v for k, v in args.items() if k != missing} for missing in args]
            variants += [args | {'extra': None}, [], None]
            for bad in variants:
                for shared in (False, True):
                    self.graph()
                    before = snapshot(machines(self.session))
                    request = row | {'arguments': bad}
                    if shared:
                        status, output = run(self.session, [request, requests()[0]])
                    else:
                        out = io.StringIO()
                        with redirect_stdout(out):
                            status = cli.run_requests(getattr(self.session, row['surface']),
                                                      [json.dumps({k: v for k, v in request.items()
                                                                   if k != 'surface'})])
                        output = [json.loads(line) for line in out.getvalue().splitlines()]
                    self.assertEqual((status, len(output)), (2, 1))
                    self.assertEqual(output[0]['error']['type'], 'FixtureError')
                    self.assertEqual(snapshot(machines(self.session)), before)
            for text in (
                json.dumps(row).replace('"operation":', '"operation":"issue","operation":', 1),
                json.dumps(row).replace('"arguments": {', '"arguments": {"extra":NaN,', 1),
                json.dumps(row).replace('"arguments": {', '"arguments": {"extra":1e999,', 1),
            ):
                out = io.StringIO()
                with redirect_stdout(out):
                    status = run_requests(load_fixture(FIXTURE), [text, json.dumps(requests()[0])])
                self.assertEqual((status, len(out.getvalue().splitlines())), (2, 1))

    def test_new_fixture_retains_anchor_and_exact_setup_validation(self):
        for remove in (
            lambda e: e['operation'] == 'issue',
            lambda e: e['operation'] == 'bind_settlement',
            lambda e: e['machine'] == 'resale' and e['operation'] == 'adopt_issued',
            lambda e: e['machine'] == 'admission' and e['operation'] == 'set_clock',
        ):
            value = fixture()
            value['setup'] = [e for e in value['setup'] if not remove(e)]
            with self.assertRaises(FixtureError):
                session_from(value)
