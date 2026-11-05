"""Source-informed console composition, exact service envelopes and local children."""

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from settlement_console import main, run_console
from ticket_operations_client import TicketOperationsClient
from ticket_operations_cli import dispatch_request
from ticket_operations_fixture import load_fixture
from settlement_fsm import SettlementError
from statement_source import StatementSourceError
from cancel_acceptance_source import CancelAcceptanceSourceError

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_settlement_fact_inputs_session.json'
JOURNEY = HERE / 'fixtures/settlement_console_journey.txt'
STATEMENTS = HERE / 'fixtures/ticket_operations_statement_session.json'
REFUNDS = HERE / 'fixtures/ticket_operations_refund_session.json'
VIEW = ['view', 'claim-2']
COMMIT = ['commit', 'claim-2', 'initial', '6000', '5500', '200', '100', '100',
          '100', '"synthetic"', 'manual-commit', 'SUBMIT']
OBSERVE = ['observe_statement', 'claim-2', 'later', '4001', '3801', '200', '0', '0',
           '0', 'null', 'later', 'SUBMIT']
DISTRIBUTE = ['distribute', 'claim-2', '["platform","organizer"]', 'distribution', 'SUBMIT']
REFUND = ['bind_refund', 'claim-2', 'refund', '4000', 'buyer-3', 'synthetic', 'refund', 'SUBMIT']
ACCEPT = ['observe_mock_cancel_acceptance', 'claim-2', 'accept', '1000', 'accept', 'SUBMIT']


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


class SettlementConsoleTests(unittest.TestCase):
    def drive(self, answers, *, fixture=FIXTURE, client=None, stream=None):
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

        with patch('settlement_console.TicketOperationsClient.launch', return_value=client) as launch, \
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
            try:
                expected = dispatch_request(control, row)
            except (SettlementError, StatementSourceError, CancelAcceptanceSourceError) as error:
                detail = ({'code': error.code} if isinstance(error, SettlementError) else
                          {'type': type(error).__name__, 'message': str(error)})
                expected = dict(surface='settlement', operation=row['operation'], error=detail)
            self.assertEqual(reply, expected)
            self.assertEqual(row['surface'], 'settlement')
            self.assertEqual(set(row), {'surface', 'operation', 'arguments'})
        # Also prove the complete printed envelope stream equals the received stream.
        self.assertEqual([json.loads(s) for s in re.findall(r'desk=(\{[^\n]+\})', output)], replies)
        self.assertIn('UNDETERMINED — Astra/User', output)
        self.assertIn('UNDETERMINED — User/designated advisers', output)

    def summaries(self, replies, output):
        for reply in replies:
            if 'error' in reply:
                continue
            snapshot = 'receipt' in reply
            label = 'Action snapshot' if snapshot else 'Current service observation'
            view = reply['receipt']['settlement'] if snapshot else reply['view']
            claim = view['claim']
            if claim is None:
                self.assertIn(label + ' claim data unavailable (claim=null).', output)
                continue
            for name, fields in (
                ('Cash', ('confirmed_cash', 'distributed_cash', 'undistributed_cash')),
                ('Statement position', ('receivable_open', 'non_cash_accounted')),
                ('Refund', ('refund_face', 'refund_accepted', 'refund_outstanding',
                            'refund_bearer_policy', 'distribution_blocked')),
                ('PG adjustment', ('pg_adjustment_outstanding',)),
                ('Distribution', ('distribution_order',)),
            ):
                self.assertIn(label + ' ' + name + '=' + json.dumps(
                    {k: claim[k] for k in fields}, sort_keys=True), output)
            for obligation in claim['obligations']:
                self.assertIn(label + ' Allocation=' + json.dumps(obligation, sort_keys=True), output)
            for key in ('funds_executed', 'bank_debit_observed', 'external_return_closed', 'durable'):
                self.assertIs(view[key], False)

    def test_live_journey(self):
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(JOURNEY.read_text().splitlines())
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([r['operation'] for r in calls], ['commit', 'view', 'observe_statement',
            'view', 'distribute', 'view', 'bind_refund', 'view', 'observe_mock_cancel_acceptance',
            'view', 'commit', 'view'])
        source = HERE / 'fixtures/ticket_operations_settlement_fact_inputs_journey.jsonl'
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        self.assertEqual(calls[0::2], [rows[i] for i in (0, 2, 4, 5, 6, 0)])
        self.parity(calls, replies, output)
        self.summaries(replies, output)
        self.assertEqual(replies[1]['view']['claim']['receivable_open'], 4001)
        current = replies[9]['view']['claim']
        self.assertEqual({k: current[k] for k in ('confirmed_cash', 'refund_outstanding',
            'pg_adjustment_outstanding')}, dict(confirmed_cash=9301, refund_outstanding=3000,
                                               pg_adjustment_outstanding=1000))
        self.assertEqual(current['refund_bearer_policy'], 'UNDEFINED')
        self.assertTrue(current['distribution_blocked'])
        self.assertEqual(replies[10]['receipt'], replies[0]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual(replies[10]['receipt']['settlement']['claim']['confirmed_cash'], 5500)
        self.assertEqual(replies[11]['view']['claim'], current)
        self.assertIn('Action snapshot: {"applied": null, "duplicate": true}', output)
        self.assertIn('synthetic cancellation acceptance; not real refund completion', output)

    def test_insufficient_cash_keeps_service_obligations_and_explicit_order(self):
        # Console composition only: existing settlement tests own the arithmetic predicates.
        status, calls, replies, output, errors = self.drive(COMMIT + DISTRIBUTE + VIEW + ['quit'])
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(calls[1]['arguments']['order'], ['platform', 'organizer'])
        self.parity(calls, replies, output)
        self.summaries(replies, output)
        claim = replies[-1]['view']['claim']
        self.assertGreater(claim['obligations'][0]['outstanding'], 0)
        self.assertEqual([o['face'] for o in claim['obligations']],
                         [o['face'] for o in replies[0]['receipt']['settlement']['claim']['obligations']])

    def test_over_refund_acceptance_and_conflicting_keys_preserve_current_view(self):
        over_refund = REFUND.copy()
        over_refund[2:4] = ['too-much', '10002']
        over_refund[-2] = 'too-much'
        over_accept = ACCEPT.copy()
        over_accept[2:5] = ['too-much', '4001', 'too-much-accept']
        conflict = ACCEPT.copy()
        conflict[3] = '1001'
        sequence = COMMIT + REFUND + ACCEPT + VIEW + over_refund + VIEW + over_accept + VIEW + conflict + VIEW
        status, calls, replies, output, errors = self.drive(sequence + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual([r['error']['code'] for r in replies if 'error' in r],
                         ['REFUND_CEILING', 'REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION', 'IDEMPOTENCY_CONFLICT'])
        self.assertTrue(all(replies[i]['view'] == replies[3]['view'] for i in (5, 7, 9)))
        self.parity(calls, replies, output)

    def test_recorded_statement_and_acceptance_selectors_and_source_refusal(self):
        statements = ['commit_recorded_statement', 'claim-2', 'statement-1', 'recorded-commit', 'SUBMIT',
                      'observe_recorded_statement', 'claim-2', 'statement-2', 'recorded-later', 'SUBMIT']
        status, calls, replies, output, errors = self.drive(statements + VIEW + ['quit'], fixture=STATEMENTS)
        self.assertEqual((status, errors), (0, ''))
        self.parity(calls, replies, output, STATEMENTS)
        self.summaries(replies, output)
        answers = ['bind_refund', 'claim-1', 'r', '4000', 'buyer', 'synthetic', 'r', 'SUBMIT',
                   'observe_recorded_cancel_acceptance', 'claim-1', 'missing', 'missing', 'SUBMIT',
                   'observe_recorded_cancel_acceptance', 'claim-1', 'acceptance-1', 'accept', 'SUBMIT',
                   'view', 'claim-1', 'quit']
        status, calls, replies, output, errors = self.drive(answers, fixture=REFUNDS)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(replies[1]['error']['type'], 'CancelAcceptanceNotFound')
        self.assertIn('receipt', replies[2])
        self.parity(calls, replies, output, REFUNDS)
        self.summaries(replies, output)

    def test_every_mutation_requires_literal_single_use_submit(self):
        actions = [COMMIT, OBSERVE, DISTRIBUTE, REFUND, ACCEPT,
            ['commit_recorded_statement', 'claim-2', 'statement-1', 'key', 'SUBMIT'],
            ['observe_recorded_statement', 'claim-2', 'statement-2', 'key', 'SUBMIT'],
            ['observe_recorded_cancel_acceptance', 'claim-2', 'source', 'key', 'SUBMIT']]
        answers = [v for action in actions for v in [*action[:-1], 'submit']]
        status, calls, _, output, errors = self.drive(answers + ['quit'])
        self.assertEqual((status, calls, errors), (0, [], ''))
        self.assertEqual(output.count('Declined; no request sent.'), len(actions))
        status, calls, _, output, errors = self.drive(COMMIT + OBSERVE[:-1] + ['no', 'quit'])
        self.assertEqual((status, len(calls), errors), (0, 1, ''))
        self.assertEqual(json.loads(output.split('proposed=')[1].splitlines()[0]), calls[0])

    def test_invalid_syntax_never_submits_or_invents_defaults(self):
        bad_inputs = [COMMIT[:i] + [v] for i, v in (
            (1, ''), (3, '1.0'), (4, '1e3'), (5, 'true'), (6, ''), (7, ' 1'),
            (8, '+1'), (9, ''), (9, 'false'), (9, '{}'), (10, ''))]
        bad_inputs += [['distribute', 'claim-2', value] for value in ('null', '"platform"', '[1]', '{', '')]
        for answers in bad_inputs:
            with self.subTest(answers=answers):
                client, output = Mock(), io.StringIO()
                status = run_console(client, input_stream=script(answers + ['quit']),
                                     output_stream=output, error_stream=io.StringIO())
                self.assertEqual(status, 0)
                client.request.assert_not_called()
                self.assertIn('input_error=', output.getvalue())

    def test_economic_validation_and_duplicate_order_are_left_to_service(self):
        duplicate = DISTRIBUTE.copy()
        duplicate[2] = '["platform", "platform"]'
        negative = ACCEPT.copy()
        negative[3] = '-1'
        status, calls, replies, output, errors = self.drive(COMMIT + duplicate + negative + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(calls[1]['arguments']['order'], ['platform', 'platform'])
        self.assertEqual(calls[2]['arguments']['amount'], -1)
        self.assertIn('error', replies[1])
        self.assertIn('error', replies[2])
        self.parity(calls, replies, output)

    def test_null_claim_has_no_manufactured_cash(self):
        with tempfile.TemporaryDirectory() as temp:
            value = json.loads(FIXTURE.read_text())
            value['setup'] = [r for r in value['setup'] if not (
                r['machine'] == 'settlement' and r['subject_id'] == 'claim-2'
                and r['operation'] in {'authorize', 'capture'})]
            fixture = Path(temp) / 'initiated.json'
            fixture.write_text(json.dumps(value))
            status, calls, replies, output, errors = self.drive(VIEW + ['quit'], fixture=fixture)
            self.assertEqual((status, errors), (0, ''))
            self.assertIsNone(replies[0]['view']['claim'])
            self.parity(calls, replies, output, fixture)
            self.summaries(replies, output)
            self.assertNotIn('Cash=', output)

    def test_large_integer_is_forwarded_without_float_conversion(self):
        answers = REFUND.copy()
        answers[3] = '999999999999'
        status, calls, replies, output, errors = self.drive(answers + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(calls[0]['arguments']['amount'], 999999999999)
        self.assertIn('"amount": 999999999999', output)
        self.assertNotIn('999999999999.0', output)
        self.parity(calls, replies, output)

    def test_eof_interruption_and_input_failure_fence_and_close(self):
        for failure in (None, KeyboardInterrupt('interrupted'), OSError('input failed')):
            lines = script(COMMIT)

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
            self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], replies[0])
        status, calls, _, _, errors = self.drive(COMMIT[:-1])
        self.assertEqual((status, calls), (2, []))
        self.assertIn('EOFError', errors)

    def test_terminal_envelopes_stop_before_queued_action(self):
        for detail, surface, op in (({'type': 'FixtureError', 'message': 'bad fixture'}, None, None),
                ({'type': 'BookingInputError', 'message': 'bad input'}, 'settlement', 'commit')):
            client = Mock()
            reply = dict(surface=surface, operation=op, error=detail)
            client.request.return_value = reply
            output, errors = io.StringIO(), io.StringIO()
            status = run_console(client, input_stream=script(COMMIT + VIEW + ['quit']),
                                 output_stream=output, error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output.getvalue())
            self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'bad.json'
            bad.write_text('{')
            status, calls, _, _, errors = self.drive(COMMIT + VIEW, fixture=bad)
            self.assertEqual((status, len(calls)), (2, 1))
            self.assertIn('FENCED:', errors)

    def test_real_transport_uncertainty_does_not_resubmit_or_consume_queued_actions(self):
        for raw in (b'{partial\xff', b'not-json\n'):
            worker = ('import sys; sys.stdin.buffer.readline(); '
                      'sys.stdout.buffer.write(' + repr(raw) + '); sys.stdout.buffer.flush()')
            process = subprocess.Popen([sys.executable, '-B', '-c', worker], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
            client = TicketOperationsClient(process, cleanup_timeout=1)
            pending = script(COMMIT + COMMIT + VIEW + ['quit'])
            status, calls, replies, _, errors = self.drive([], stream=pending, client=client)
            self.assertEqual((status, len(calls), replies), (2, 1, []))
            self.assertEqual(pending.readline(), 'commit\n')
            self.assertEqual(client.uncertainty.reply_bytes, raw)
            self.assertEqual(client.uncertainty.request, calls[0])
            self.assertIn('TicketDeskTransportUncertainty', errors)
            self.assertIn('reply_bytes', errors)
            self.assertIn('FixtureError', errors)

    def test_output_failure_retains_reply_even_if_diagnostics_fail(self):
        reply = dict(surface='settlement', operation='view', view={'claim': None})

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

    def test_request_interruption_is_terminal(self):
        client = Mock()
        client.request.side_effect = KeyboardInterrupt('exchange interrupted')
        errors = io.StringIO()
        status = run_console(client, input_stream=script(COMMIT + COMMIT + ['quit']),
                             output_stream=io.StringIO(), error_stream=errors)
        self.assertEqual(status, 2)
        client.request.assert_called_once()
        self.assertIn('KeyboardInterrupt', errors.getvalue())

    def test_required_arguments_import_and_lifecycle_failures(self):
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
            "guard.start(); import settlement_console"], cwd=HERE, capture_output=True, text=True,
            env=os.environ.copy(), timeout=10)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        for close_result in (7, OSError('cleanup failed')):
            client = Mock()
            if isinstance(close_result, Exception):
                client.close.side_effect = close_result
            else:
                client.close.return_value = close_result
            with patch('settlement_console.TicketOperationsClient.launch', return_value=client), \
                    patch('sys.stdin', script(['quit'])), patch('sys.stdout', io.StringIO()), \
                    patch('sys.stderr', io.StringIO()):
                self.assertEqual(main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']),
                                 2 if isinstance(close_result, Exception) else 1)
            client.close.assert_called_once_with()
            client.request.assert_not_called()
        with patch('settlement_console.TicketOperationsClient.launch', side_effect=OSError('launch failed')), \
                patch('sys.stderr', io.StringIO()) as errors:
            self.assertEqual(main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']), 2)
        self.assertIn('launch failed', errors.getvalue())

    def test_documented_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'settlement_console.py'),
            '--fixture', str(FIXTURE), '--cleanup-timeout', '1'], input=JOURNEY.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(len(re.findall(r'desk=', result.stdout)), 12)
        self.assertIn('"refund_outstanding": 3000', result.stdout)
        self.assertIn('Action snapshot', result.stdout)
        self.assertIn('Current service observation', result.stdout)


if __name__ == '__main__':
    unittest.main()
