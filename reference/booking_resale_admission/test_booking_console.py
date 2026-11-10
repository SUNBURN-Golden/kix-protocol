"""Source-informed console composition evidence over the real local desk."""

from copy import deepcopy
import io
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from booking_console import decimal_amount, main, run_console
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture as load_recorded
from calculated_booking_quote_fixture import load_fixture as load_calculated
from booking_quote_source import BookingQuoteSourceError
from ticket_operations_cli import _DOMAIN_ERRORS, _error, dispatch_request
from ticket_operations_fixture import load_fixture
from test_calculated_booking_quote_source import request
from test_reservation_fsm import assert_not_final
from test_ticket_operations_session import FIXTURE
from ticket_operations_client import TicketOperationsClient, TicketDeskTransportUncertainty

HERE = Path(__file__).resolve().parent
QUOTE = HERE / 'fixtures/booking_console_quote.json'
ANSWERS = HERE / 'fixtures/booking_console_confirm.txt'
CLOCK = ['set_clock', 'clock', '1000000', 'console-clock-1']
HOLD = ['hold', 'console-reservation', 'show-1', '1', 'console-buyer', '1120000', 'console-hold-1']
TARGET = ['target', 'console-reservation', 'console-order', 'console-confirm-1']
LOAD = ['load_quote', str(QUOTE)]
PREVIEW = LOAD + TARGET + ['preview']
VIEW = ['view', 'console-reservation']


SOURCE_OPTIONS = {
    'recorded': {'quotes': HERE / 'fixtures/ticket_operations_booking_quotes.json'},
    'calculated': {'calculated_quotes': HERE / 'fixtures/calculated_booking_quotes.json'},
}
SOURCE_CONFIRM = ['confirm_recorded_quote', 'desk-record-1', 'desk-reserve-1',
                  'console-source-order', 'console-source-confirm', 'CONFIRM_RECORDED_QUOTE']


def source_requests(kind):
    """Explicit control requests for the documented source-console answer files."""
    rows = []
    def add(operation, **arguments):
        rows.append(dict(surface='booking', operation=operation, arguments=arguments))
    def view(reservation_id='desk-reserve-1'):
        add('view', reservation_id=reservation_id)
    def confirm(recording_id, reservation_id='desk-reserve-1',
                order_id='console-source-order', idempotency_key='console-source-confirm'):
        add('confirm_recorded_quote', recording_id=recording_id, reservation_id=reservation_id,
            order_id=order_id, idempotency_key=idempotency_key)
    base = 'desk-record-1' if kind == 'recorded' else 'desk-calc-1'
    prefix = 'desk-' if kind == 'recorded' else 'desk-calc-'
    add('view_show', show_id='show-1')
    add('set_clock', subject_id='clock', now_ms=1000000, idempotency_key='console-source-clock')
    add('hold', reservation_id='desk-reserve-1', show_id='show-1', slot=1,
        buyer_role='console-source-buyer', expires_ms=1120000, idempotency_key='console-source-hold')
    # Source rejection must not reserve this caller's key; every view stays HELD.
    selectors = [prefix + name for name in ('absent', 'malformed', 'mismatch')]
    if kind == 'recorded':
        selectors += ['desk-source-error', 'desk-source-timeout', 'desk-bad-json',
                      'desk-duplicate', 'desk-nonfinite']
    else:
        selectors += [prefix + name for name in ('asset', 'discount', 'multiple')]
    for selector in selectors:
        confirm(selector)
        view()
    price = 'desk-off-price' if kind == 'recorded' else 'desk-calc-price'
    confirm(price, idempotency_key='console-source-price')
    view()
    confirm(base, idempotency_key='console-source-price')  # retained price refusal
    confirm(base)
    view()
    add('cancel', reservation_id='desk-reserve-1', idempotency_key='console-source-cancel')
    view()
    confirm(base)  # historical replay; explicit view remains CANCELLED
    view()
    confirm(base, order_id='console-source-other-order')
    confirm(prefix + 'changed')
    view()
    add('hold', reservation_id='desk-reserve-2', show_id='show-1', slot=1,
        buyer_role='console-source-buyer', expires_ms=1120000, idempotency_key='console-source-hold-2')
    add('set_clock', subject_id='clock', now_ms=1120000, idempotency_key='console-source-expiry')
    confirm(prefix + 'expired', reservation_id='desk-reserve-2', order_id='console-source-order-2',
            idempotency_key='console-source-expired')
    view('desk-reserve-2')
    return rows


def source_parity(case, kind, calls, replies, output):
    """Source-informed full-envelope parity against a separately loaded desk."""
    control = load_fixture(FIXTURE)
    options = SOURCE_OPTIONS[kind]
    loader = load_recorded if kind == 'recorded' else load_calculated
    adapter = BookingQuoteAdapter(control.booking, loader(next(iter(options.values()))))
    expected = []
    for row in calls:
        try:
            reply = dispatch_request(control, row, quote_adapter=adapter)
        except (*_DOMAIN_ERRORS, BookingQuoteSourceError) as error:
            reply = _error(row['surface'], row['operation'], error)
        expected.append(reply)
        if row['surface'] == 'booking' and ('receipt' in reply or 'view' in reply):
            assert_not_final(case, reply.get('receipt', reply.get('view')))
    case.assertEqual(replies, expected)
    case.assertEqual([json.loads(value) for value in re.findall(r'desk=(\{[^\n]+\})', output)], expected)
    return expected


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


class BookingConsoleTests(unittest.TestCase):
    def drive(self, answers, *, stream=None, client=None, source_options=None):
        source_options = source_options or {}
        output, errors = io.StringIO(), io.StringIO()
        if client is None:
            client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1, **source_options)
        calls, replies = [], []
        original_request = client.request
        def record(row):
            calls.append(deepcopy(row))
            reply = original_request(row)
            replies.append(deepcopy(reply))
            return reply
        with patch('booking_console.TicketOperationsClient.launch', return_value=client) as launch, \
                patch.object(client, 'request', side_effect=record), \
                patch.object(client, 'close', wraps=client.close) as close, \
                patch('sys.stdin', stream if stream is not None else script(answers)), \
                patch('sys.stdout', output), patch('sys.stderr', errors):
            status = main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1',
                           *(item for name, path in source_options.items()
                             for item in ('--' + name.replace('_', '-'), str(path)))])
        launch.assert_called_once_with(FIXTURE, cleanup_timeout=1, **source_options)
        close.assert_called_once_with()
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)
        return status, calls, replies, output.getvalue(), errors.getvalue()


    def test_source_journeys_complete_parity_history_and_refusals(self):
        for kind, options in SOURCE_OPTIONS.items():
            with self.subTest(kind=kind), patch('ticket_operations_client.subprocess.Popen',
                                               wraps=subprocess.Popen) as launch:
                answers = (HERE / f'fixtures/booking_console_source_{kind}.txt').read_text().splitlines()
                status, calls, replies, output, errors = self.drive(answers, source_options=options)
                launch.assert_called_once()
                self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
                self.assertEqual(calls, source_requests(kind))
                source_parity(self, kind, calls, replies, output)
                successes = [r['receipt'] for r in replies if r['operation'] == 'confirm_recorded_quote'
                             and 'receipt' in r]
                self.assertEqual(len(successes), 2)
                self.assertFalse(successes[0]['duplicate'])
                self.assertEqual(successes[1], successes[0] | {'duplicate': True, 'applied': None})
                self.assertEqual(successes[1]['reservation']['phase'], 'CONFIRMED')
                views = [r['view']['phase'] for r in replies if r['operation'] == 'view']
                self.assertEqual(views[-5:], ['CONFIRMED', 'CANCELLED', 'CANCELLED', 'CANCELLED', 'HELD'])
                codes = [r['error']['code'] for r in replies if 'code' in r.get('error', {})]
                self.assertEqual(codes, ['PRIMARY_PRICE_MISMATCH', 'IDEMPOTENCY_CONFLICT',
                                        'IDEMPOTENCY_CONFLICT', 'IDEMPOTENCY_CONFLICT', 'RESERVATION_EXPIRED'])
                for row in calls:
                    if row['operation'] == 'confirm_recorded_quote':
                        self.assertIn('proposed=' + json.dumps(row, sort_keys=True), output)

    def test_source_clean_success_and_absent_source_terminal_error(self):
        for kind, options in SOURCE_OPTIONS.items():
            rows = source_requests(kind)
            confirm = next(r for r in rows if r['operation'] == 'confirm_recorded_quote'
                           and r['arguments']['recording_id'] in {'desk-record-1', 'desk-calc-1'}
                           and r['arguments']['idempotency_key'] == 'console-source-confirm')
            selected = rows[:3] + [confirm, dict(surface='booking', operation='view',
                                               arguments={'reservation_id': 'desk-reserve-1'})]
            answers = []
            for row in selected:
                answers += [row['operation'], *(str(v) for v in row['arguments'].values())]
                if row['operation'] == 'confirm_recorded_quote':
                    answers += ['CONFIRM_RECORDED_QUOTE']
            status, calls, replies, output, errors = self.drive(answers + ['quit'], source_options=options)
            self.assertEqual((status, errors), (0, ''))
            source_parity(self, kind, calls, replies, output)
        pending = script(SOURCE_CONFIRM + ['view_show', 'show-1', 'quit'])
        status, calls, replies, output, errors = self.drive([], stream=pending)
        self.assertEqual((status, len(calls)), (2, 1))
        self.assertEqual(replies[0]['error']['type'], 'FixtureError')
        self.assertEqual(pending.read(), script(['view_show', 'show-1', 'quit']).read())
        self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], replies[0])

    def test_source_prompt_decline_exact_escaped_request_and_incomplete_fields(self):
        values = ['caller-"☀"', 'caller-reservation', 'caller-order', 'caller-key']
        row = dict(surface='booking', operation='confirm_recorded_quote',
                   arguments=dict(zip(('recording_id', 'reservation_id', 'order_id', 'idempotency_key'), values)))
        client = Mock()
        client.request.return_value = dict(surface='booking', operation='confirm_recorded_quote',
                                          receipt={'duplicate': False, 'applied': True})
        output, errors = io.StringIO(), io.StringIO()
        status = run_console(client, input_stream=script(
            ['confirm_recorded_quote', *values, 'confirm_recorded_quote',
             'confirm_recorded_quote', *values, 'CONFIRM_RECORDED_QUOTE', 'quit']),
            output_stream=output, error_stream=errors)
        self.assertEqual((status, errors.getvalue()), (0, ''))
        client.request.assert_called_once_with(row)
        self.assertEqual(output.getvalue().count('proposed=' + json.dumps(row, sort_keys=True)), 2)
        positions = [output.getvalue().index(name + ' (synthetic):') for name in row['arguments']]
        self.assertEqual(positions, sorted(positions))
        for index in range(4):
            for invalid in ('', ' ', ' padded '):
                with self.subTest(index=index, invalid=invalid):
                    client = Mock()
                    out = io.StringIO()
                    self.assertEqual(run_console(client, input_stream=script(
                        ['confirm_recorded_quote', *values[:index], invalid, 'quit']),
                        output_stream=out, error_stream=io.StringIO()), 0)
                    client.request.assert_not_called()
                    self.assertIn('input_error=', out.getvalue())
                    self.assertNotIn('proposed=', out.getvalue())

    def test_source_selection_invalidates_preview_before_decline_or_bad_input(self):
        for attempt in (SOURCE_CONFIRM[:-1] + ['no'], ['confirm_recorded_quote', ' ']):
            status, calls, replies, output, errors = self.drive(
                CLOCK + HOLD + PREVIEW + attempt + ['confirm', 'preview', 'confirm', 'CONFIRM'] + VIEW + ['quit'])
            self.assertEqual((status, errors), (0, ''))
            self.assertEqual([c['operation'] for c in calls].count('preview_calculated_quote'), 2)
            self.assertEqual([c['operation'] for c in calls].count('confirm_calculated_quote'), 1)
            self.assertNotIn('confirm_recorded_quote', [c['operation'] for c in calls])
            self.assertIn('A new successful preview is required.', output)
            self.assertEqual(replies[-1]['view']['phase'], 'CONFIRMED')

    def test_source_collection_and_confirmation_interruptions_submit_nothing(self):
        for count in range(1, len(SOURCE_CONFIRM)):
            for failure in (None, KeyboardInterrupt('approval'), OSError('terminal input')):
                with self.subTest(count=count, failure=type(failure).__name__):
                    lines = script(SOURCE_CONFIRM[:count])
                    class BrokenInput:
                        def readline(self):
                            line = lines.readline()
                            if not line and failure is not None:
                                raise failure
                            return line
                    client = Mock()
                    errors = io.StringIO()
                    self.assertEqual(run_console(client, input_stream=BrokenInput(),
                        output_stream=io.StringIO(), error_stream=errors), 2)
                    client.request.assert_not_called()
                    self.assertIn('FENCED:', errors.getvalue())

    def test_source_flags_conflict_before_launch(self):
        with patch('booking_console.TicketOperationsClient.launch') as launch, \
                patch('sys.stderr', io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1',
                      '--quotes', 'a', '--calculated-quotes', 'b'])
            self.assertEqual(result.exception.code, 2)
            launch.assert_not_called()

    def test_fulfillment_prompt_exact_request_decline_and_original_errors(self):
        # Opaque caller values prove the UI neither checks eligibility nor assembles
        # adapter fields. Full service behavior is covered by real-child journeys.
        operations = [
            ('bind_settlement', ('reservation_id', 'settlement_id', 'idempotency_key'), 'BIND_SETTLEMENT'),
            ('issue', ('issuance_id', 'order_id', 'idempotency_key'), 'ISSUE')]
        for operation, names, confirmation in operations:
            arguments = dict(zip(names, ('caller-subject', 'caller-binding', 'caller-key'), strict=True))
            request = dict(surface='booking', operation=operation, arguments=arguments)
            action = [operation, *arguments.values()]
            for detail in (None, {'code': 'IDEMPOTENCY_CONFLICT'},
                           {'type': 'InvalidIssuedTicketRecord', 'message': 'original "☀"\nerror'}):
                with self.subTest(operation=operation, detail=detail):
                    client = Mock()
                    reply = dict(surface='booking', operation=operation,
                                 **({'receipt': {'duplicate': False, 'applied': True}}
                                    if detail is None else {'error': detail}))
                    client.request.return_value = reply
                    out, err = io.StringIO(), io.StringIO()
                    status = run_console(client, input_stream=script(
                        action + [confirmation.lower(), *action, confirmation, 'quit']),
                        output_stream=out, error_stream=err)
                    self.assertEqual((status, err.getvalue()), (int(detail is not None), ''))
                    client.request.assert_called_once_with(request)
                    self.assertEqual(out.getvalue().count('proposed=' + json.dumps(request, sort_keys=True)), 2)
                    self.assertIn('Declined; no request sent.', out.getvalue())
                    self.assertIn('desk=' + json.dumps(reply, sort_keys=True), out.getvalue())
                    positions = [out.getvalue().index(name + ' (synthetic):') for name in names]
                    self.assertEqual(positions, sorted(positions))

    def test_fulfillment_confirmation_interruption_sends_nothing(self):
        for operation, names in (
                ('bind_settlement', ('reservation_id', 'settlement_id', 'idempotency_key')),
                ('issue', ('issuance_id', 'order_id', 'idempotency_key'))):
            for failure in (None, KeyboardInterrupt('approval'), OSError('terminal input')):
                with self.subTest(operation=operation, failure=type(failure).__name__):
                    lines = script([operation, *('caller-' + name for name in names)])
                    class BrokenInput:
                        def readline(self):
                            line = lines.readline()
                            if not line and failure is not None:
                                raise failure
                            return line
                    client = Mock()
                    out, err = io.StringIO(), io.StringIO()
                    self.assertEqual(run_console(client, input_stream=BrokenInput(),
                        output_stream=out, error_stream=err), 2)
                    client.request.assert_not_called()
                    self.assertIn('FENCED:', err.getvalue())

    def test_live_guided_booking(self):
        answers = ANSWERS.read_text().splitlines()
        # Confirm the documented root-relative transcript also runs from any test cwd.
        answers[answers.index('reference/booking_resale_admission/fixtures/booking_console_quote.json')] = str(QUOTE)
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(answers)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([r['operation'] for r in calls], ['view_show', 'set_clock', 'hold',
                         'preview_calculated_quote', 'confirm_calculated_quote', 'view'])
        self.assertTrue(all(set(r) == {'surface', 'operation', 'arguments'} and
                            r['surface'] == 'booking' for r in calls))
        self.assertEqual(calls[1]['arguments'], dict(subject_id='clock', now_ms=1000000,
                                                  idempotency_key='console-clock-1'))
        self.assertEqual(calls[2]['arguments'], dict(reservation_id='console-reservation',
                         show_id='show-1', slot=1, buyer_role='console-buyer', expires_ms=1120000,
                         idempotency_key='console-hold-1'))
        quote = replies[3]['quote']
        preview_text = calls[3]['arguments']['request_text']
        self.assertEqual(preview_text, QUOTE.read_bytes().decode('utf-8'))
        self.assertEqual(calls[4]['arguments'], dict(request_text=preview_text,
                         reservation_id='console-reservation', order_id='console-order',
                         idempotency_key='console-confirm-1'))
        reservation = replies[4]['receipt']['reservation']
        self.assertEqual(reservation['amount'], int(quote['totals']['payableAtoms']))
        self.assertEqual(reservation['quote_ref'], quote['quoteHash'])
        self.assertEqual(replies[-1]['view']['reservation_id'], reservation['reservation_id'])
        self.assertEqual(replies[-1]['view']['phase'], 'CONFIRMED')
        self.assertIn('payableAtoms=10001 (decimal=10001)', output)
        self.assertIn('quoteHash=' + reservation['quote_ref'], output)
        self.assertIn('CALCULATION_ONLY', output)
        self.assertIn('MOCK_GATE_ONLY', output)
        self.assertIn('Mock reservation confirmation target=', output)
        for reply in replies:
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output)
            if 'receipt' in reply:
                assert_not_final(self, reply['receipt'])
        self.assertIsNone(replies[-1]['view']['payment_ref'])
        self.assertIsNone(replies[-1]['view']['issuance_id'])

    def test_decline_consumes_preview_without_confirmation_or_cleanup_mutation(self):
        status, calls, replies, output, errors = self.drive(
            CLOCK + HOLD + PREVIEW + ['confirm', 'no', 'confirm'] + VIEW + ['quit'])
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(replies[-1]['view']['phase'], 'HELD')
        self.assertNotIn('confirm_calculated_quote', [r['operation'] for r in calls])
        self.assertNotIn('release', [r['operation'] for r in calls])
        self.assertIn('Declined; no confirmation sent.', output)
        self.assertIn('A new successful preview is required.', output)

    def test_reloading_even_whitespace_and_editing_identifiers_require_new_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            changed = Path(temp) / 'quote.json'
            # CRLF and whitespace must survive exactly; no universal newline normalization.
            text = '\r\n' + json.dumps(request(), indent=2).replace('\n', '\r\n') + ' \r\n'
            changed.write_bytes(text.encode('utf-8'))
            status, calls, replies, output, errors = self.drive(CLOCK + HOLD + PREVIEW +
                ['load_quote', str(changed), 'confirm', 'preview', 'target', 'console-reservation',
                 'edited-order', 'edited-confirm', 'confirm', 'preview', 'confirm', 'CONFIRM',
                 'confirm'] + VIEW + ['quit'])
        self.assertEqual((status, errors), (0, ''))
        previews = [c for c in calls if c['operation'] == 'preview_calculated_quote']
        confirms = [c for c in calls if c['operation'] == 'confirm_calculated_quote']
        self.assertEqual(len(previews), 3)
        self.assertEqual(len(confirms), 1)
        self.assertEqual(previews[1]['arguments']['request_text'], text)
        self.assertEqual(confirms[0]['arguments'], dict(request_text=text, reservation_id='console-reservation',
                                                      order_id='edited-order', idempotency_key='edited-confirm'))
        self.assertEqual(output.count('A new successful preview is required.'), 3)
        self.assertEqual(replies[-1]['view']['phase'], 'CONFIRMED')

    def test_failed_replacement_preview_and_failed_load_cannot_use_prior_success(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'bad.json'
            bad.write_text('{')
            status, calls, replies, output, errors = self.drive(CLOCK + HOLD + PREVIEW +
                ['load_quote', str(bad), 'preview', 'confirm'] + LOAD + ['preview',
                 'load_quote', str(bad) + '.absent', 'confirm'] + VIEW + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertNotIn('confirm_calculated_quote', [c['operation'] for c in calls])
        self.assertEqual(replies[-1]['view']['phase'], 'HELD')
        refusal = next(r for r in replies if 'error' in r)
        self.assertEqual(refusal['error']['type'], 'InvalidBookingQuoteRecord')
        self.assertIn('desk=' + json.dumps(refusal, sort_keys=True), output)
        self.assertIn('FileNotFoundError', output)

    def test_external_file_edit_does_not_change_pending_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'quote.json'
            text = QUOTE.read_bytes()
            path.write_bytes(text)
            lines = script(CLOCK + HOLD + ['load_quote', str(path)] + TARGET +
                           ['preview', 'confirm', 'CONFIRM'] + VIEW + ['quit'])
            class EditingInput:
                def readline(self):
                    line = lines.readline()
                    if line == 'confirm\n':
                        path.write_text('{')
                    return line
            status, calls, _, _, errors = self.drive([], stream=EditingInput())
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(calls[-2]['arguments']['request_text'], text.decode('utf-8'))

    def test_occupied_seat_error_exact_and_expired_hold_requires_explicit_release(self):
        occupied = ['hold', 'occupied-reservation', 'show-1', '0', 'console-buyer', '1120000', 'occupied-key']
        status, calls, replies, output, errors = self.drive(CLOCK + occupied + HOLD + PREVIEW +
            ['set_clock', 'clock', '1120000', 'expiry-key', 'confirm', 'CONFIRM', 'confirm'] + VIEW +
            ['release', 'console-reservation', 'release-key'] + VIEW + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        refused = [r for r in replies if 'error' in r]
        self.assertEqual([r['error'] for r in refused], [{'code': 'SLOT_OCCUPIED'}, {'code': 'RESERVATION_EXPIRED'}])
        for reply in refused:
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output)
        self.assertEqual(replies[-3]['view']['phase'], 'HELD')
        self.assertEqual(replies[-1]['view']['phase'], 'RELEASED')
        self.assertEqual([c['operation'] for c in calls].count('release'), 1)
        self.assertEqual([c['operation'] for c in calls].count('confirm_calculated_quote'), 1)
        self.assertIn('A new successful preview is required.', output)

    def test_explicit_cancel_confirmed_and_explicit_release_held(self):
        for confirmed, action, phase in ((False, 'release', 'RELEASED'), (True, 'cancel', 'CANCELLED')):
            with self.subTest(action=action):
                confirm = PREVIEW + ['confirm', 'CONFIRM'] if confirmed else []
                status, calls, replies, _, errors = self.drive(CLOCK + HOLD + confirm +
                    [action, 'console-reservation', action + '-key'] + VIEW + ['quit'])
                self.assertEqual((status, errors), (0, ''))
                self.assertEqual(replies[-1]['view']['phase'], phase)
                self.assertEqual(calls[-2]['arguments'], dict(reservation_id='console-reservation',
                                                          idempotency_key=action + '-key'))

    def test_booking_input_terminal_error_fences_and_preserves_envelope(self):
        status, calls, replies, output, errors = self.drive(HOLD + ['view_show', 'show-1', 'quit'])
        self.assertEqual(status, 2)
        self.assertEqual(len(calls), 1)
        self.assertEqual(replies[0]['error'], {'type': 'BookingInputError',
                         'message': 'explicit successful session set_clock required before mutation'})
        self.assertIn('desk=' + json.dumps(replies[0], sort_keys=True), output)
        self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], replies[0])

    def test_startup_and_fixture_terminal_envelopes_stop_before_next_action(self):
        for reply in (dict(surface=None, operation=None, error=dict(type='FixtureError', message='bad\nfixture')),
                      dict(surface='booking', operation='view_show',
                           error=dict(type='FixtureError', message='exact "structural" error'))):
            client = Mock()
            client.request.return_value = reply
            out, err = io.StringIO(), io.StringIO()
            status = run_console(client, input_stream=script(['view_show', 'show-1', 'view_show', 'show-1']),
                                 output_stream=out, error_stream=err)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            self.assertEqual(json.loads(out.getvalue().split('desk=')[1].splitlines()[0]), reply)
            self.assertEqual(json.loads(err.getvalue().split('FENCED: ')[1])['last_reply'], reply)

    def test_uncertain_real_transport_preserves_bytes_cause_and_closes_without_resubmit(self):
        # A real child emits an invalid partial UTF-8 reply, then exits. The ordinary
        # client retains the wire snapshot; the console must neither recover nor retry.
        worker = subprocess.Popen([sys.executable, '-B', '-c',
            "import sys; sys.stdin.buffer.readline(); sys.stdout.buffer.write(b'partial\\xff'); sys.stdout.buffer.flush()"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        client = TicketOperationsClient(worker, 1)
        status, calls, _, _, errors = self.drive(['view_show', 'show-1', 'view_show', 'show-1'], client=client)
        self.assertEqual(status, 2)
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(client.uncertainty, TicketDeskTransportUncertainty)
        diagnostic = json.loads(errors.split('FENCED: ')[1].splitlines()[0])
        self.assertEqual(diagnostic['exceptions'][0]['request_bytes'], repr(client.uncertainty.request_bytes))
        self.assertEqual(diagnostic['exceptions'][0]['reply_bytes'], repr(b'partial\xff'))
        self.assertEqual(diagnostic['exceptions'][1]['type'], 'FixtureError')
        self.assertIsNotNone(worker.returncode)

    def test_eof_interrupt_and_terminal_read_error_stop_and_close_without_compensation(self):
        for failure in (None, KeyboardInterrupt('caller stop'), OSError('terminal read failed')):
            with self.subTest(failure=failure):
                lines = script(CLOCK + HOLD)
                class BrokenInput:
                    def readline(self):
                        line = lines.readline()
                        if line:
                            return line
                        if failure is not None:
                            raise failure
                        return ''
                status, calls, _, _, errors = self.drive([], stream=BrokenInput())
                self.assertEqual(status, 2)
                self.assertEqual([c['operation'] for c in calls], ['set_clock', 'hold'])
                self.assertIn('FENCED:', errors)

    def test_output_failure_after_reply_retains_result_and_stops(self):
        client = Mock()
        reply = dict(surface='booking', operation='view_show', view={'show_id': 'show-1'})
        client.request.return_value = reply
        class BrokenOutput(io.StringIO):
            def write(self, value):
                if value.startswith('desk='):
                    raise BrokenPipeError('display failed')
                return super().write(value)
        errors = io.StringIO()
        status = run_console(client, input_stream=script(['view_show', 'show-1', 'view_show', 'show-1']),
                             output_stream=BrokenOutput(), error_stream=errors)
        self.assertEqual(status, 2)
        client.request.assert_called_once()
        self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)

    def test_required_arguments_cleanup_budget_and_import_safety(self):
        for args in ([], ['--fixture', str(FIXTURE)],
                     ['--fixture', str(FIXTURE), '--cleanup-timeout', '0']):
            with self.subTest(args=args), patch('sys.stderr', io.StringIO()), \
                    patch('ticket_operations_client.subprocess.Popen') as launch:
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
                launch.assert_not_called()
        result = subprocess.run([sys.executable, '-B', '-c',
            "import subprocess; from unittest.mock import patch; "
            "guard=patch.object(subprocess, 'Popen', side_effect=AssertionError('import launched')); "
            "guard.start(); import booking_console"], cwd=HERE, capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_documented_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'booking_console.py'),
                                 '--fixture', str(FIXTURE), '--cleanup-timeout', '1'],
                                input=ANSWERS.read_text(), text=True, capture_output=True,
                                cwd=HERE.parents[1], timeout=10)
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertIn('"phase": "CONFIRMED"', result.stdout)
        self.assertIn('quoteHash=', result.stdout)

    def test_interruption_at_confirmation_prompt_submits_no_confirmation(self):
        lines = script(CLOCK + HOLD + PREVIEW + ['confirm'])
        class InterruptInput:
            def readline(self):
                line = lines.readline()
                if not line:
                    raise KeyboardInterrupt('declined by interruption')
                return line
        status, calls, _, _, errors = self.drive([], stream=InterruptInput())
        self.assertEqual(status, 2)
        self.assertNotIn('confirm_calculated_quote', [c['operation'] for c in calls])
        self.assertIn('KeyboardInterrupt', errors)

    def test_exact_decimal_renderer_without_floats(self):
        for atoms, decimals, expected in (('10001', 0, '10001'), ('10001', 2, '100.01'),
                                          ('1', 3, '0.001'), ('9007199254740993', 2, '90071992547409.93')):
            self.assertEqual(decimal_amount(atoms, decimals), expected)


if __name__ == '__main__':
    unittest.main()
