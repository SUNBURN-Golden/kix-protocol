"""Source-informed terminal composition evidence using actual local subprocesses."""

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from resale_console import main, run_console
from ticket_operations_client import TicketOperationsClient
from ticket_operations_cli import dispatch_request
from ticket_operations_fixture import load_fixture

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_payment_session.json'
TRANSFER = HERE / 'fixtures/resale_console_transfer.txt'
CANCEL = HERE / 'fixtures/resale_console_cancel.txt'
LIST_ARGS = ['list-1', 'issue-1', '1', 'buyer-1', 'buyer-2', '8000', '1120000', '"reserve-1"', 'console-list']
LIST = ['list_resale_inputs', *LIST_ARGS, 'SUBMIT']
PAY = ['observe_recorded_payment', 'payment-1', 'list-1', 'pay', 'SUBMIT']
ACCEPT = ['accept_resale', 'transfer', 'list-1', 'transfer-key', 'SUBMIT']
VIEW = ['view', 'list-1']


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


class ResaleConsoleTests(unittest.TestCase):
    def drive(self, answers, *, fixture=FIXTURE, stream=None, client=None):
        output, errors = io.StringIO(), io.StringIO()
        if client is None:
            client = TicketOperationsClient.launch(fixture, cleanup_timeout=1)
        calls, replies = [], []
        original = client.request
        def record(row):
            calls.append(deepcopy(row))
            reply = original(row)
            replies.append(deepcopy(reply))
            return reply
        with patch('resale_console.TicketOperationsClient.launch', return_value=client) as launch, \
                patch.object(client, 'request', side_effect=record), \
                patch.object(client, 'close', wraps=client.close) as close, \
                patch('sys.stdin', stream if stream is not None else script(answers)), \
                patch('sys.stdout', output), patch('sys.stderr', errors):
            status = main(['--fixture', str(fixture), '--cleanup-timeout', '1'])
        launch.assert_called_once_with(fixture, cleanup_timeout=1)
        close.assert_called_once_with()
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)
        self.assertIsNotNone(client._process.poll())
        return status, calls, replies, output.getvalue(), errors.getvalue()

    def parity(self, calls, replies, output, fixture=FIXTURE):
        control = load_fixture(fixture)
        for row, reply in zip(calls, replies, strict=True):
            self.assertEqual(reply, dispatch_request(control, row))
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output)
            self.assertEqual(set(row), {'surface', 'operation', 'arguments'})
            self.assertEqual(row['surface'], 'resale')
        self.assertIn('MOCK_GATE_ONLY', output)
        self.assertIn('UNDETERMINED', output)

    def test_live_transfer_transcript(self):
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(TRANSFER.read_text().splitlines())
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([c['operation'] for c in calls], ['set_clock', 'list_resale_inputs', 'hold_buy',
            'view', 'observe_recorded_payment', 'view_right', 'bind_settlement', 'accept_resale',
            'view_presentation', 'close', 'accept_resale', 'view', 'view_right'])
        self.assertEqual(calls[1]['arguments'], dict(listing_id='list-1', right_id='issue-1', version=1,
            seller_role='buyer-1', recipient_role='buyer-2', amount=8000, expires_ms=1120000,
            reservation_id='reserve-1', idempotency_key='console-list'))
        self.parity(calls, replies, output)
        self.assertEqual(replies[4]['receipt']['right']['holder_role'], 'buyer-1')
        self.assertEqual(replies[5]['view']['right']['version'], 1)
        transfer = replies[7]['receipt']
        self.assertTrue(transfer['listing']['ownership_transferred'])
        self.assertEqual(transfer['listing']['settlement_gate'], 'MOCK_COMMIT_OBSERVED')
        self.assertFalse(transfer['venue_credential_reissued'])
        self.assertFalse(transfer['funds_executed'])
        self.assertFalse(transfer['economic_finality_claimed'])
        self.assertFalse(replies[8]['view']['presentation']['matches_current_right'])
        self.assertEqual(replies[10]['receipt'], transfer | {'duplicate': True, 'applied': None})
        self.assertEqual(replies[10]['receipt']['listing']['phase'], 'TRANSFERRED')
        self.assertEqual(replies[11]['view']['phase'], 'CLOSED')
        self.assertEqual(replies[12]['view']['right']['holder_role'], 'buyer-2')
        self.assertIn('Action snapshot: {"applied": null, "duplicate": true}', output)
        self.assertIn('Current service observation Listing={"amount": 8000', output)
        self.assertIn('Action snapshot Payment=', output)
        self.assertIn('Action snapshot Ownership=', output)

    def test_live_cancel_transcript(self):
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(CANCEL.read_text().splitlines())
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([c['operation'] for c in calls], ['list_resale_inputs', 'hold_buy',
            'release_hold', 'cancel_listing', 'list_resale_inputs', 'view', 'view_right', 'view_presentation'])
        self.assertIsNone(calls[0]['arguments']['reservation_id'])
        self.parity(calls, replies, output)
        self.assertEqual(replies[4]['receipt'], replies[0]['receipt'] | {'duplicate': True, 'applied': None})
        self.assertEqual(replies[4]['receipt']['listing']['phase'], 'LISTED')
        self.assertEqual(replies[5]['view']['phase'], 'CANCELLED')
        self.assertIsNone(replies[5]['view']['payment_ref'])
        self.assertFalse(replies[5]['view']['ownership_transferred'])
        self.assertEqual(replies[6]['view']['right']['version'], 1)
        self.assertTrue(replies[7]['view']['presentation']['matches_current_right'])

    def test_price_and_ownership_refusals_are_exact_and_do_not_correct(self):
        for field, value, code in ((5, '20001', 'RESALE_CAP'), (3, 'other', 'NOT_HOLDER'),
                                   (2, '2', 'STALE_VERSION')):
            args = LIST_ARGS.copy()
            args[field] = value
            status, calls, replies, output, errors = self.drive(
                ['list_resale_inputs', *args, 'SUBMIT', 'view_right', 'issue-1', 'quit'])
            self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
            self.assertEqual(len(calls), 2)
            self.assertEqual(replies[0], dict(surface='resale', operation='list_resale_inputs',
                                            error={'code': code}))
            self.assertIn('desk=' + json.dumps(replies[0], sort_keys=True), output)
            self.assertIsNone(replies[1]['view']['right']['listing_id'])

    def test_missing_payment_unknown_record_and_explicit_unbound_transfer(self):
        status, calls, replies, output, errors = self.drive(LIST + ACCEPT +
            ['observe_recorded_payment', 'absent', 'list-1', 'absent-pay', 'SUBMIT'] + VIEW + PAY +
            ['accept_resale', 'transfer', 'list-1', 'fresh-transfer', 'SUBMIT'] + VIEW + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(replies[1]['error'], {'code': 'ILLEGAL_TRANSITION'})
        self.assertEqual(replies[2]['error']['type'], 'ResalePaymentNotFound')
        self.assertEqual(replies[3]['view']['phase'], 'LISTED')
        self.assertEqual(replies[-1]['view']['phase'], 'TRANSFERRED')
        self.assertEqual(replies[-1]['view']['settlement_gate'], 'UNBOUND')
        self.assertFalse(replies[-1]['view']['mock_settlement_commit_observed'])
        self.assertEqual(len(calls), 7)
        self.assertIn('desk=' + json.dumps(replies[2], sort_keys=True), output)

    def test_unknown_and_uncommitted_bound_settlement_preserve_errors(self):
        for settlement in ('missing', 'resale-claim'):
            with self.subTest(settlement=settlement), tempfile.TemporaryDirectory() as temp:
                body = json.loads(FIXTURE.read_text())
                body['setup'] = [r for r in body['setup'] if not (
                    r['machine'] == 'settlement' and r['subject_id'] == 'resale-claim'
                    and r['operation'] == 'commit')]
                fixture = Path(temp) / 'desk.json'
                fixture.write_text(json.dumps(body))
                status, calls, replies, output, errors = self.drive(LIST + PAY +
                    ['bind_settlement', 'list-1', settlement, 'bind', 'SUBMIT'] + ACCEPT + VIEW +
                    ['quit'], fixture=fixture)
                self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
                self.assertEqual(len(calls), 5)
                self.assertEqual(replies[3]['error']['code'],
                                 'UNKNOWN_SETTLEMENT' if settlement == 'missing' else 'SETTLEMENT_NOT_COMMITTED')
                self.assertEqual(replies[-1]['view']['phase'], 'PAYMENT_NOTED')
                self.assertFalse(replies[-1]['view']['ownership_transferred'])
                self.assertIn('desk=' + json.dumps(replies[3], sort_keys=True), output)

    def test_every_mutation_requires_literal_single_use_submission(self):
        actions = [LIST[:-1], ['hold_buy', 'h', 'list-1', 'buyer-2', 'h-key'],
            ['release_hold', 'h', 'buyer-2', 'release'], ['cancel_listing', 'list-1', 'buyer-1', 'cancel'],
            PAY[:-1], ['bind_settlement', 'list-1', 'resale-claim', 'bind'], ACCEPT[:-1],
            ['close', 'list-1', 'close'], ['set_clock', 'clock', '1000000', 'clock-key']]
        answers = [v for action in actions for v in [*action, 'submit']]
        status, calls, _, output, errors = self.drive(answers + ['quit'])
        self.assertEqual((status, calls, errors), (0, [], ''))
        self.assertEqual(output.count('Declined; no request sent.'), len(actions))
        # Approval from the first selection cannot authorize another selection.
        status, calls, _, output, errors = self.drive(LIST + LIST[:-1] + ['no', 'quit'])
        self.assertEqual((status, len(calls), errors), (0, 1, ''))
        proposed = json.loads(output.split('proposed=')[1].splitlines()[0])
        self.assertEqual(proposed, calls[0])

    def test_invalid_inputs_never_submit_or_generate_values(self):
        invalids = [(2, '1.0'), (5, '1e3'), (6, '-1'), (7, ''), (7, 'reserve-1'),
                    (7, 'false'), (7, '0'), (7, '""'), (0, ''), (8, '')]
        for index, value in invalids:
            args = LIST_ARGS.copy()
            args[index] = value
            client, output = Mock(), io.StringIO()
            status = run_console(client, input_stream=script(['list_resale_inputs', *args[:index], value, 'quit']),
                                 output_stream=output, error_stream=io.StringIO())
            self.assertEqual(status, 0)
            client.request.assert_not_called()
            self.assertIn('input_error=', output.getvalue())

    def test_large_supported_integer_round_trip_and_current_ownership_rendering(self):
        with tempfile.TemporaryDirectory() as temp:
            body = json.loads(FIXTURE.read_text())
            huge = 999999999999
            for row in body['setup']:
                if 'resale_cap' in row['body']:
                    row['body']['resale_cap'] = huge
            fixture = Path(temp) / 'desk.json'
            fixture.write_text(json.dumps(body))
            args = LIST_ARGS.copy()
            args[5] = str(huge)
            status, calls, replies, output, errors = self.drive(
                ['list_resale_inputs', *args, 'SUBMIT'] + VIEW + ['quit'], fixture=fixture)
            self.assertEqual((status, errors), (0, ''))
            self.assertEqual(calls[0]['arguments']['amount'], huge)
            self.assertEqual(replies[-1]['view']['amount'], huge)
            self.assertIn('amount=999999999999 integer KRW', output)
            self.assertIn('"current_version": 1', output)
            self.assertNotIn('999999999999.0', output)
            self.parity(calls, replies, output, fixture)

    def test_eof_interrupt_and_input_failure_stop_and_close(self):
        for failure in (None, KeyboardInterrupt('interrupted'), OSError('input failed')):
            lines = script(LIST)
            class BrokenInput:
                def readline(self):
                    line = lines.readline()
                    if line:
                        return line
                    if failure is not None:
                        raise failure
                    return ''
            status, calls, replies, _, errors = self.drive([], stream=BrokenInput())
            self.assertEqual((status, len(calls)), (2, 1))
            self.assertIn('FENCED:', errors)
            self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], replies[0])
        class InterruptApproval:
            def __init__(self):
                self.lines = script(LIST[:-1])
            def readline(self):
                line = self.lines.readline()
                if not line:
                    raise KeyboardInterrupt('approval interrupted')
                return line
        status, calls, _, _, errors = self.drive([], stream=InterruptApproval())
        self.assertEqual((status, calls), (2, []))
        self.assertIn('KeyboardInterrupt', errors)

    def test_terminal_envelopes_preserved_before_queued_action(self):
        for detail, surface, operation in (({'type': 'FixtureError', 'message': 'bad fixture'}, None, None),
                ({'type': 'BookingInputError', 'message': 'bad input'}, 'resale', 'list_resale_inputs')):
            client = Mock()
            reply = dict(surface=surface, operation=operation, error=detail)
            client.request.return_value = reply
            output, errors = io.StringIO(), io.StringIO()
            status = run_console(client, input_stream=script(LIST + VIEW + ['quit']),
                                 output_stream=output, error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output.getvalue())
            self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'bad.json'
            bad.write_text('{')
            status, calls, _, output, errors = self.drive(LIST + VIEW, fixture=bad)
            self.assertEqual((status, len(calls)), (2, 1))
            # A startup reply may race the child exit; either is terminal.
            self.assertIn('FENCED:', errors)

    def test_real_transport_uncertainty_stops_queued_action_and_reaps_child(self):
        worker = "import sys; sys.stdin.buffer.readline(); sys.stdout.buffer.write(b'{partial\\xff'); sys.stdout.buffer.flush()"
        process = subprocess.Popen([sys.executable, '-B', '-c', worker], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        client = TicketOperationsClient(process, cleanup_timeout=1)
        status, calls, replies, _, errors = self.drive(LIST + VIEW + ['quit'], client=client)
        self.assertEqual((status, len(calls), replies), (2, 1, []))
        self.assertIsNotNone(client.uncertainty)
        self.assertEqual(client.uncertainty.reply_bytes, b'{partial\xff')
        self.assertIn('TicketDeskTransportUncertainty', errors)
        self.assertIn('reply_bytes', errors)
        self.assertIn('FixtureError', errors)
        self.assertEqual(client.uncertainty.request, calls[0])

    def test_output_failure_retains_reply_and_fences_even_with_broken_diagnostics(self):
        reply = dict(surface='resale', operation='view', view={'listing_id': 'list-1', 'phase': 'LISTED'})
        class BrokenOutput(io.StringIO):
            def write(self, text):
                if text.startswith('desk='):
                    raise BrokenPipeError('display failed')
                return super().write(text)
        class BrokenDiagnostics(io.StringIO):
            def write(self, text):
                raise OSError('diagnostics failed')
        for errors in (io.StringIO(), BrokenDiagnostics()):
            client = Mock()
            client.request.return_value = reply
            status = run_console(client, input_stream=script(VIEW + VIEW + ['quit']),
                                 output_stream=BrokenOutput(), error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            if not isinstance(errors, BrokenDiagnostics):
                self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)

    def test_request_interruption_fences_before_queued_action(self):
        client = Mock()
        client.request.side_effect = KeyboardInterrupt('submitted exchange interrupted')
        errors = io.StringIO()
        status = run_console(client, input_stream=script(LIST + VIEW + ['quit']),
                             output_stream=io.StringIO(), error_stream=errors)
        self.assertEqual(status, 2)
        client.request.assert_called_once()
        self.assertIn('KeyboardInterrupt', errors.getvalue())

    def test_required_arguments_cleanup_budgets_import_and_cleanup_failure(self):
        for args in ([], ['--fixture', str(FIXTURE)], *(
                ['--fixture', str(FIXTURE), '--cleanup-timeout', value]
                for value in ('0', '-1', 'nan', 'inf'))):
            with patch('sys.stderr', io.StringIO()), patch('ticket_operations_client.subprocess.Popen') as launch:
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
                launch.assert_not_called()
        result = subprocess.run([sys.executable, '-B', '-c',
            "import subprocess; from unittest.mock import patch; "
            "guard=patch.object(subprocess, 'Popen', side_effect=AssertionError('import launched')); "
            "guard.start(); import resale_console"], cwd=HERE, capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        client = Mock()
        client.close.side_effect = OSError('cleanup failed')
        with patch('resale_console.TicketOperationsClient.launch', return_value=client), \
                patch('sys.stdin', script(['quit'])), patch('sys.stdout', io.StringIO()), \
                patch('sys.stderr', io.StringIO()) as errors:
            self.assertEqual(main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']), 2)
        client.close.assert_called_once_with()
        client.request.assert_not_called()
        self.assertIn('cleanup failed', errors.getvalue())

    def test_documented_transcripts_as_cli_subprocesses(self):
        for answers in (TRANSFER, CANCEL):
            result = subprocess.run([sys.executable, '-B', str(HERE / 'resale_console.py'),
                '--fixture', str(FIXTURE), '--cleanup-timeout', '1'], input=answers.read_text(),
                text=True, capture_output=True, timeout=10, env=os.environ.copy())
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            self.assertIn('"phase": "CLOSED"' if answers == TRANSFER else '"phase": "CANCELLED"', result.stdout)
            self.assertIn('Action snapshot', result.stdout)
            self.assertIn('Current service observation', result.stdout)


if __name__ == '__main__':
    unittest.main()
