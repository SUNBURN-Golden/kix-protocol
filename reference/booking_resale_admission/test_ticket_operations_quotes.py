"""Source-informed shared quote composition evidence; all invocations are explicit."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from admission_fixture import FixtureError
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture as load_quotes
from booking_quote_source import BookingQuoteNotFound, BookingQuoteSourceError, InvalidBookingQuoteRecord
from booking_session import BookingInputError, BookingSession
from fake_booking_quote_source import FakeBookingQuoteSource
from reservation_fsm import ReservationError, ReservationMachine
from test_reservation_fsm import assert_not_final
from test_ticket_operations_session import FIXTURE, HERE, direct_graph, fixture, machines, requests, snapshot
from ticket_operations_cli import dispatch_request, main, run_requests
from ticket_operations_fixture import load_fixture

QUOTES = HERE / 'fixtures' / 'ticket_operations_booking_quotes.json'


def quote_request(**changes):
    row = deepcopy(requests('recorded_confirm')[3])
    row['arguments'].update(changes)
    return row


def run(desk, texts, adapter=None):
    output = io.StringIO()
    with redirect_stdout(output):
        status = run_requests(desk, texts, quote_adapter=adapter)
    return status, [json.loads(line) for line in output.getvalue().splitlines()]


def outcome(call):
    try:
        return call()
    except ReservationError as error:
        return {'error': {'code': error.code}}
    except BookingQuoteSourceError as error:
        return {'error': {'type': type(error).__name__, 'message': str(error)}}


def build():
    desk = load_fixture(FIXTURE)
    source = load_quotes(QUOTES)
    adapter = BookingQuoteAdapter(desk.booking, source)
    for row in requests('recorded_confirm')[:3]:
        dispatch_request(desk, row, quote_adapter=adapter)
    return desk, source, adapter


def direct_call(session, adapter, row):
    operation, args = row['operation'], row['arguments']
    if operation == 'confirm_recorded_quote':
        result = adapter.confirm_recorded_quote(**args)
    else:
        result = getattr(session, operation)(**args)
    key = 'view' if operation.startswith('view') else 'receipt'
    return {'surface': 'booking', 'operation': operation, key: result}


class TicketOperationsQuoteTests(unittest.TestCase):
    def test_main_binds_adapter_to_the_only_booking_graph_without_fetch_or_clock(self):
        with patch('ticket_operations_session.ReservationMachine', wraps=ReservationMachine) as ctor, \
                patch.object(FakeBookingQuoteSource, 'fetch', side_effect=AssertionError('construction fetch')), \
                patch('ticket_operations_cli.run_requests', return_value=0) as runner, \
                patch('sys.stdin', io.StringIO('')):
            self.assertEqual(main(['--fixture', str(FIXTURE), '--quotes', str(QUOTES), '--requests', '-']), 0)
        ctor.assert_called_once()
        desk, _ = runner.call_args.args
        adapter = runner.call_args.kwargs['quote_adapter']
        self.assertIs(adapter._session, desk.booking)
        self.assertIs(desk.booking._machine, machines(desk)[1])
        self.assertEqual(adapter._source.calls, ())
        self.assertEqual(snapshot(machines(desk)), snapshot(direct_graph(fixture()['setup'])))
        # Fixture clocks do not implicitly initialize BookingSession.
        with self.assertRaises(BookingInputError):
            dispatch_request(desk, quote_request(), quote_adapter=adapter)
        self.assertEqual(adapter._source.calls, ('desk-record-1',))
        for row in requests('recorded_confirm'):
            dispatch_request(desk, row, quote_adapter=adapter)
        self.assertEqual(desk.booking.view('desk-reserve-1')['phase'], 'CONFIRMED')

    def test_only_booking_dispatch_receives_the_explicit_adapter(self):
        adapter, desk = Mock(), Mock()
        for surface, row in (('booking', quote_request()), ('resale', requests('cancel')[0]),
                             ('admission', requests('admission')[0])):
            nested = {key: row[key] for key in ('operation', 'arguments')}
            result = {'operation': row['operation'], 'receipt': object()}
            with patch('ticket_operations_cli._' + surface, return_value=result) as delegate:
                actual = dispatch_request(desk, row, quote_adapter=adapter)
                self.assertEqual(actual, {'surface': surface, **result})
                kwargs = {'quote_adapter': adapter} if surface == 'booking' else {}
                delegate.assert_called_once_with(getattr(desk, surface), nested, **kwargs)
                self.assertIs(delegate.call_args.args[1]['arguments'], row['arguments'])
        adapter.assert_not_called()

    def test_transcripts_match_direct_adapter_receipts_errors_and_graph_after_every_line(self):
        for scenario in ('recorded_confirm', 'recorded_boundaries'):
            desk = load_fixture(FIXTURE)
            source, control_source = load_quotes(QUOTES), load_quotes(QUOTES)
            adapter = BookingQuoteAdapter(desk.booking, source)
            control = direct_graph(fixture()['setup'])
            session = BookingSession(control[1])
            direct_adapter = BookingQuoteAdapter(session, control_source)
            initial = snapshot(machines(desk))
            original = desk.booking.view('reserve-1')
            results, fetches = [], []
            for row in requests(scenario):
                with self.subTest(scenario=scenario, row=row):
                    actual = outcome(lambda: dispatch_request(desk, row, quote_adapter=adapter))
                    expected = outcome(lambda: direct_call(session, direct_adapter, row))
                    self.assertEqual(actual, expected)
                    self.assertEqual(snapshot(machines(desk)), snapshot(control))
                    after = snapshot(machines(desk))
                    self.assertEqual((after[0], after[2:]), (initial[0], initial[2:]))
                    if row['operation'] == 'confirm_recorded_quote':
                        fetches.append(row['arguments']['recording_id'])
                    self.assertEqual(source.calls, tuple(fetches))
                    self.assertEqual(control_source.calls, source.calls)
                    if 'error' not in actual:
                        assert_not_final(self, actual.get('receipt', actual.get('view')))
                    results.append(actual)
            self.assertEqual(desk.booking.view('reserve-1'), original)
            self.assertEqual(desk.resale._adapter._source.calls, ())
            self.assertEqual(desk.admission._adapter._source.calls, ())
            self.assertEqual(results[-2]['view']['phase'], 'CONFIRMED' if scenario == 'recorded_confirm' else 'CANCELLED')
            for field in ('payment_ref', 'settlement_id', 'issuance_id', 'right'):
                self.assertIsNone(results[-2]['view'][field])
            self.assertEqual(results[-1]['view']['show']['payment_ref_count'], 0)
            new_entries = machines(desk)[1].export_journal()[len(initial[1][2]):]
            self.assertLessEqual({entry['op'] for entry in new_entries},
                                 {'set_clock', 'register_show', 'hold', 'confirm', 'cancel'})
            self.assertEqual(sum(entry['op'] == 'confirm' for entry in new_entries), 1)
            if scenario == 'recorded_confirm':
                self.assertEqual(results[4]['receipt'], results[3]['receipt'] | {'duplicate': True, 'applied': None})
            else:
                self.assertEqual(results[14]['receipt'], results[10]['receipt'] | {'duplicate': True, 'applied': None})
                self.assertEqual(results[14]['receipt']['reservation']['phase'], 'CONFIRMED')
                self.assertEqual([r['error'].get('type', r['error'].get('code')) for r in results if 'error' in r],
                                 ['BookingQuoteNotFound', 'InvalidBookingQuoteRecord', 'InvalidBookingQuoteRecord',
                                  'BookingQuoteSourceError', 'BookingQuoteSourceError', 'PRIMARY_PRICE_MISMATCH',
                                  'IDEMPOTENCY_CONFLICT', 'BookingQuoteSourceError', 'IDEMPOTENCY_CONFLICT',
                                  'RESERVATION_EXPIRED'])

    def test_alias_conflicts_retained_refusals_and_shared_key_collisions(self):
        desk, source, adapter = build()
        graph = direct_graph(fixture()['setup'])
        session = BookingSession(graph[1])
        control_adapter = BookingQuoteAdapter(session, load_quotes(QUOTES))
        for row in requests('recorded_confirm')[:3]:
            direct_call(session, control_adapter, row)
        cases = [({}, None), ({'recording_id': 'desk-alias'}, None),
                 ({'recording_id': 'desk-changed'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'recording_id': 'desk-off-price'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'order_id': 'desk-other-order'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'idempotency_key': 'desk-hold-1'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'idempotency_key': 'hold-1'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'idempotency_key': 'desk-clock-1'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'recording_id': 'desk-changed', 'idempotency_key': 'binding'}, 'ORDER_BINDING_CONFLICT'),
                 ({'idempotency_key': 'fresh'}, 'ILLEGAL_TRANSITION')]
        for changes, error in cases:
            row = quote_request(**changes)
            actual = outcome(lambda: dispatch_request(desk, row, quote_adapter=adapter))
            self.assertEqual(actual, outcome(lambda: direct_call(session, control_adapter, row)))
            if error:
                self.assertEqual(actual, {'error': {'code': error}})
            self.assertEqual(snapshot(machines(desk)), snapshot(graph))
        self.assertEqual(len(source.calls), len(cases))
        # Admission's delegated key also lives on this same reservation machine.
        admission = requests('admission')[0]
        dispatch_request(desk, admission)
        before = snapshot(machines(desk))
        collision = quote_request(idempotency_key=admission['arguments']['idempotency_key'])
        self.assertEqual(outcome(lambda: dispatch_request(desk, collision, quote_adapter=adapter)),
                         {'error': {'code': 'IDEMPOTENCY_CONFLICT'}})
        self.assertEqual(snapshot(machines(desk)), before)
        # An FSM refusal is retained; source refusals in the next test are not.
        desk, source, adapter = build()
        refused = quote_request(recording_id='desk-off-price')
        for row, code in ((refused, 'PRIMARY_PRICE_MISMATCH'), (refused, 'PRIMARY_PRICE_MISMATCH'),
                          (quote_request(), 'IDEMPOTENCY_CONFLICT')):
            self.assertEqual(outcome(lambda: dispatch_request(desk, row, quote_adapter=adapter)),
                             {'error': {'code': code}})
        self.assertEqual(source.calls, ('desk-off-price', 'desk-off-price', 'desk-record-1'))

    def test_source_rejections_do_not_delegate_mutate_or_bind_the_confirmation_key(self):
        cases = [('desk-absent', BookingQuoteNotFound), ('desk-malformed', InvalidBookingQuoteRecord),
                 ('desk-mismatch', InvalidBookingQuoteRecord), ('desk-bad-json', InvalidBookingQuoteRecord),
                 ('desk-duplicate', InvalidBookingQuoteRecord), ('desk-nonfinite', InvalidBookingQuoteRecord),
                 ('desk-source-error', BookingQuoteSourceError), ('desk-source-timeout', BookingQuoteSourceError)]
        for selector, error in cases:
            with self.subTest(selector=selector):
                desk, source, adapter = build()
                before = snapshot(machines(desk))
                with patch.object(desk.booking, 'confirm', wraps=desk.booking.confirm) as confirm:
                    with self.assertRaises(error):
                        dispatch_request(desk, quote_request(recording_id=selector), quote_adapter=adapter)
                    confirm.assert_not_called()
                self.assertEqual(source.calls, (selector,))
                self.assertEqual(snapshot(machines(desk)), before)
                receipt = dispatch_request(desk, quote_request(), quote_adapter=adapter)['receipt']
                self.assertFalse(receipt['duplicate'])  # exact rejected caller key can still succeed
                self.assertEqual(source.calls, (selector, 'desk-record-1'))

    def test_invalid_callers_do_not_fetch_and_structural_requests_stop_without_delegation(self):
        for field in quote_request()['arguments']:
            desk, source, adapter = build()
            before = snapshot(machines(desk))
            for value in (None, True, 1, [], '', ' bad '):
                with self.subTest(field=field, value=value):
                    row = quote_request(**{field: value})
                    status, output = run(desk, [json.dumps(row)], adapter)
                    self.assertEqual(status, 1)
                    self.assertEqual(output[0]['error'], {'type': 'InvalidBookingQuoteRecord', 'message': 'INVALID_ID'})
            self.assertEqual(source.calls, ())
            self.assertEqual(snapshot(machines(desk)), before)
            self.assertFalse(dispatch_request(desk, quote_request(), quote_adapter=adapter)['receipt']['duplicate'])
        valid = quote_request()
        bad = [valid | {'extra': 1}, valid | {'arguments': []},
               valid | {'arguments': valid['arguments'] | {'amount': 10001}}]
        bad += [valid | {'arguments': {k: v for k, v in valid['arguments'].items() if k != field}}
                for field in valid['arguments']]
        for row in bad:
            desk, source, adapter = build()
            before = snapshot(machines(desk))
            status, output = run(desk, [json.dumps(row), json.dumps(valid)], adapter)
            self.assertEqual((status, len(output)), (2, 1))
            self.assertEqual(output[0]['error']['type'], 'FixtureError')
            self.assertEqual(source.calls, ())
            self.assertEqual(snapshot(machines(desk)), before)

    def test_failure_after_success_fetches_once_each_time_and_never_falls_back(self):
        desk, original, _ = build()
        record = json.loads(original.recordings['desk-record-1'])
        source = Mock()
        timeout = TimeoutError('synthetic')
        local = BookingQuoteSourceError('synthetic source failure')
        source.fetch.side_effect = [record, None, timeout, local, record]
        adapter = BookingQuoteAdapter(desk.booking, source)
        with patch.object(desk.booking, 'confirm', wraps=desk.booking.confirm) as confirm:
            first = dispatch_request(desk, quote_request(), quote_adapter=adapter)
            before = snapshot(machines(desk))
            for index, expected in enumerate((BookingQuoteNotFound, BookingQuoteSourceError, BookingQuoteSourceError), 2):
                with self.assertRaises(expected) as caught:
                    dispatch_request(desk, quote_request(), quote_adapter=adapter)
                self.assertEqual(source.fetch.call_count, index)
                if index == 3:
                    self.assertIs(caught.exception.__cause__, timeout)
                elif index == 4:
                    self.assertIs(caught.exception, local)
                self.assertEqual(confirm.call_count, 1)
                self.assertEqual(snapshot(machines(desk)), before)
            replay = dispatch_request(desk, quote_request(), quote_adapter=adapter)
            self.assertEqual(replay['receipt'], first['receipt'] | {'duplicate': True, 'applied': None})
            self.assertEqual(confirm.call_count, 2)
        self.assertEqual(source.fetch.call_count, 5)
        self.assertEqual(snapshot(machines(desk)), before)

    def test_session_domain_and_programming_exception_identity_is_unchanged(self):
        desk, source, adapter = build()
        for error in (BookingInputError('clock'), ReservationError('TEST'), RuntimeError('programming fault')):
            with patch.object(desk.booking, 'confirm', side_effect=error) as confirm:
                with self.assertRaises(type(error)) as caught:
                    dispatch_request(desk, quote_request(), quote_adapter=adapter)
                self.assertIs(caught.exception, error)
                confirm.assert_called_once()
        self.assertEqual(source.calls, ('desk-record-1',) * 3)
        with patch.object(desk.booking, 'confirm', side_effect=RuntimeError('programming fault')):
            with self.assertRaisesRegex(RuntimeError, 'programming fault'):
                run(desk, [json.dumps(quote_request())], adapter)

    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(HERE / 'ticket_operations_cli.py'),
                               '--fixture', str(FIXTURE), *args], input=stdin, text=True,
                              capture_output=True, check=False)

    def test_file_and_stdin_transcripts_assert_every_row_and_status(self):
        for scenario, status in (('recorded_confirm', 0), ('recorded_boundaries', 1)):
            desk = load_fixture(FIXTURE)
            adapter = BookingQuoteAdapter(desk.booking, load_quotes(QUOTES))
            path = HERE / 'fixtures' / f'ticket_operations_{scenario}.jsonl'
            code, expected = run(desk, path.read_text().splitlines(), adapter)
            self.assertEqual(code, status)
            outputs = []
            for selector, stdin in ((str(path), None), ('-', path.read_text())):
                result = self.cli('--quotes', str(QUOTES), '--requests', selector, stdin=stdin)
                self.assertEqual((result.returncode, result.stderr), (status, ''))
                self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
                outputs.append(result.stdout)
            self.assertEqual(*outputs)

    def test_exit_two_stops_after_prior_refusal_and_keeps_prior_effects(self):
        bad_texts = ['{', '{"surface":"booking","surface":"booking"}',
                     '{"surface":"booking","operation":"confirm_recorded_quote","arguments":{"recording_id":"a","recording_id":"b"}}']
        prefix = [json.dumps(row) for row in requests('recorded_confirm')[:3]]
        refused = json.dumps(quote_request(recording_id='desk-source-error'))
        for text in bad_texts:
            desk = load_fixture(FIXTURE)
            source = load_quotes(QUOTES)
            adapter = BookingQuoteAdapter(desk.booking, source)
            texts = prefix + [refused, text, json.dumps(quote_request())]
            code, expected = run(desk, [line + '\n' for line in texts], adapter)
            self.assertEqual((code, len(expected)), (2, 5))
            self.assertEqual(expected[-2]['error']['type'], 'BookingQuoteSourceError')
            self.assertEqual(expected[-1]['error']['type'], 'FixtureError')
            self.assertEqual(source.calls, ('desk-source-error',))
            self.assertEqual(desk.booking.view('desk-reserve-1')['phase'], 'HELD')
            self.assertFalse(dispatch_request(desk, quote_request(), quote_adapter=adapter)['receipt']['duplicate'])
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'requests.jsonl'
                path.write_text('\n'.join(texts) + '\n')
                for selector, stdin in ((str(path), None), ('-', path.read_text())):
                    result = self.cli('--quotes', str(QUOTES), '--requests', selector, stdin=stdin)
                    self.assertEqual((result.returncode, result.stderr), (2, ''))
                    self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
        # A valid recording still cannot bypass explicit BookingSession initialization.
        result = self.cli('--quotes', str(QUOTES), '--requests', '-',
                          stdin=refused + '\n' + json.dumps(quote_request()) + '\n' + prefix[0])
        self.assertEqual((result.returncode, result.stderr), (2, ''))
        self.assertEqual([json.loads(line)['error']['type'] for line in result.stdout.splitlines()],
                         ['BookingQuoteSourceError', 'BookingInputError'])

    def test_quote_file_errors_are_exit_two_and_embedded_validation_is_lazy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'quotes.json'
            for contents in (b'{', b'\xff', b'{}', b'{"fixture_version":true,"provenance":"MOCK_GATE_ONLY","quotes":[]}'):
                path.write_bytes(contents)
                result = self.cli('--quotes', str(path), '--requests', '-', stdin='')
                self.assertEqual((result.returncode, result.stderr), (2, ''))
                row = json.loads(result.stdout)
                self.assertIsNone(row['surface'])
                self.assertIsNone(row['operation'])
            path.write_text(json.dumps(dict(fixture_version=1, provenance='MOCK_GATE_ONLY', quotes=[
                dict(recording_id='desk-record-1', recorded_text='{')])))
            result = self.cli('--quotes', str(path), '--requests', '-', stdin='')
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            result = self.cli('--quotes', str(path), '--requests', '-', stdin=json.dumps(quote_request()))
            self.assertEqual((result.returncode, result.stderr), (1, ''))
            self.assertEqual(json.loads(result.stdout)['error']['type'], 'InvalidBookingQuoteRecord')
            for args in (('--quotes', str(path) + '.missing', '--requests', '-'),
                         ('--quotes', str(path), '--requests', str(path) + '.missing')):
                self.assertEqual(self.cli(*args, stdin='').returncode, 2)

    def test_unconfigured_selector_and_all_existing_transcripts_remain_compatible(self):
        desk = load_fixture(FIXTURE)
        before = snapshot(machines(desk))
        with self.assertRaises(FixtureError):
            dispatch_request(desk, quote_request())
        self.assertEqual(snapshot(machines(desk)), before)
        for scenario in ('cancel', 'admission', 'transfer', 'reconcile', 'booking', 'booking_admission',
                         'payment_held', 'payment_listed'):
            path = HERE / 'fixtures' / ('ticket_operations_payment_session.json'
                                     if scenario.startswith('payment_') else FIXTURE.name)
            plain, configured = load_fixture(path), load_fixture(path)
            source = load_quotes(QUOTES)
            adapter = BookingQuoteAdapter(configured.booking, source)
            texts = [json.dumps(row) for row in requests(scenario)]
            self.assertEqual(run(configured, texts, adapter), run(plain, texts))
            self.assertEqual(snapshot(machines(configured)), snapshot(machines(plain)))
            self.assertEqual(source.calls, ())
        path = HERE / 'fixtures' / 'ticket_operations_admission.jsonl'
        plain = self.cli('--requests', str(path))
        configured = self.cli('--quotes', str(QUOTES), '--requests', str(path))
        self.assertEqual((configured.returncode, configured.stdout, configured.stderr),
                         (plain.returncode, plain.stdout, plain.stderr))
