"""Source-informed console composition evidence over the real local desk."""

from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from booking_console import decimal_amount, main, run_console
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


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


class BookingConsoleTests(unittest.TestCase):
    def drive(self, answers, *, stream=None, client=None):
        output, errors = io.StringIO(), io.StringIO()
        if client is None:
            client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
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
            status = main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1'])
        launch.assert_called_once_with(FIXTURE, cleanup_timeout=1)
        close.assert_called_once_with()
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)
        return status, calls, replies, output.getvalue(), errors.getvalue()

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
