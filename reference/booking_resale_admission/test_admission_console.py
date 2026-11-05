"""Source-informed terminal composition tests; not independent FSM verification."""

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

from admission_console import main, run_console
from test_admission_session import assert_flags
from test_ticket_operations_session import direct_graph, direct_call, outcome, snapshot
from ticket_operations_client import TicketOperationsClient

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_admission_inputs_session.json'
CONSUME_TRANSCRIPT = HERE / 'fixtures/admission_console_consume.txt'
DECLINE_TRANSCRIPT = HERE / 'fixtures/admission_console_decline.txt'
AUTH_ARGS = ['entry-1', 'issue-1', '1', 'buyer-1', 'gate-a', '11' * 32, '1060000', 'entry-key']
AUTH = ['authorize_admission_inputs', *AUTH_ARGS, 'AUTHORIZE']
CONSUME = ['consume_inputs', 'consume-1', 'issue-1', '1', 'gate-a', '11' * 32, 'consume-key', 'CONSUME']
VIEW = ['view', 'issue-1']
CLOCK = ['set_clock', 'clock', '1060000', 'expire', 'SET_CLOCK']


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


class AdmissionConsoleTests(unittest.TestCase):
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
        with patch('admission_console.TicketOperationsClient.launch', return_value=client) as launch, \
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

    def test_eof_interrupt_and_input_failure_stop_and_close(self):
        for failure in (None, KeyboardInterrupt('interrupted'), OSError('input failed')):
            lines = script(AUTH)
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
                self.lines = script(AUTH[:-1])
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
                ({'type': 'BookingInputError', 'message': 'bad input'}, 'admission', 'authorize_admission_inputs')):
            client = Mock()
            reply = dict(surface=surface, operation=operation, error=detail)
            client.request.return_value = reply
            output, errors = io.StringIO(), io.StringIO()
            status = run_console(client, input_stream=script(AUTH + VIEW + ['quit']),
                                 output_stream=output, error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output.getvalue())
            self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'bad.json'
            bad.write_text('{')
            status, calls, _, output, errors = self.drive(AUTH + VIEW, fixture=bad)
            self.assertEqual((status, len(calls)), (2, 1))
            # A startup reply may race the child exit; either is terminal.
            self.assertIn('FENCED:', errors)

    def test_real_transport_uncertainty_stops_queued_action_and_reaps_child(self):
        worker = "import sys; sys.stdin.buffer.readline(); sys.stdout.buffer.write(b'{partial\\xff'); sys.stdout.buffer.flush()"
        process = subprocess.Popen([sys.executable, '-B', '-c', worker], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        client = TicketOperationsClient(process, cleanup_timeout=1)
        status, calls, replies, _, errors = self.drive(AUTH + VIEW + ['quit'], client=client)
        self.assertEqual((status, len(calls), replies), (2, 1, []))
        self.assertIsNotNone(client.uncertainty)
        self.assertEqual(client.uncertainty.reply_bytes, b'{partial\xff')
        self.assertIn('TicketDeskTransportUncertainty', errors)
        self.assertIn('reply_bytes', errors)
        self.assertIn('FixtureError', errors)
        self.assertEqual(client.uncertainty.request, calls[0])

    def test_output_failure_retains_reply_and_fences_even_with_broken_diagnostics(self):
        reply = dict(surface='admission', operation='view', view={'right_id': 'issue-1', 'phase': 'AUTHORIZED'})
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
        status = run_console(client, input_stream=script(AUTH + VIEW + ['quit']),
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
            "guard.start(); import admission_console"], cwd=HERE, capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        client = Mock()
        client.close.side_effect = OSError('cleanup failed')
        with patch('admission_console.TicketOperationsClient.launch', return_value=client), \
                patch('sys.stdin', script(['quit'])), patch('sys.stdout', io.StringIO()), \
                patch('sys.stderr', io.StringIO()) as errors:
            self.assertEqual(main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']), 2)
        client.close.assert_called_once_with()
        client.request.assert_not_called()
        self.assertIn('cleanup failed', errors.getvalue())

    def parity(self, calls, replies, output, setup=()):
        value = json.loads(FIXTURE.read_text())
        control = direct_graph(value['setup'])
        for row in setup:
            self.assertNotIn('error', outcome(lambda: direct_call(control, row, value)))
        displayed = [json.JSONDecoder().raw_decode(part)[0] for part in output.split('desk=')[1:]]
        self.assertEqual(displayed, replies)
        for row, reply in zip(calls, replies, strict=True):
            before = snapshot(control)
            expected = outcome(lambda: direct_call(control, row, value))
            if 'error' in expected:
                expected.update(surface=row['surface'], operation=row['operation'])
                self.assertEqual(before, snapshot(control))
            else:
                assert_flags(self, reply.get('receipt', reply.get('view')))
            self.assertEqual(reply, expected)
            self.assertEqual(set(row), {'surface', 'operation', 'arguments'})
            self.assertEqual(row['surface'], 'admission')
        proposed = [json.JSONDecoder().raw_decode(part)[0] for part in output.split('proposed=')[1:]]
        for row in calls:
            if row['operation'] not in {'view', 'view_credential'}:
                self.assertIn(row, proposed)
        self.assertIn('MOCK_GATE_ONLY', output)
        self.assertIn('IN_MEMORY_FSM', output)
        self.assertIn('UNDETERMINED', output)

    def test_live_admission_transcript(self):
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(CONSUME_TRANSCRIPT.read_text().splitlines())
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([c['operation'] for c in calls], ['view', 'view_credential', 'set_clock',
            'authorize_admission_inputs', 'view', 'consume_inputs', 'authorize_admission_inputs',
            'view', 'view_credential'])
        self.assertEqual(calls[3]['arguments'], dict(admission_id='entry-1', right_id='issue-1', version=1,
            holder_role='buyer-1', gate_role='gate-a', request='11' * 32, expires_ms=1060000,
            idempotency_key='entry-key'))
        self.assertEqual(calls[5]['arguments'], dict(consume_id='consume-1', right_id='issue-1', version=1,
            gate_role='gate-a', request='11' * 32, idempotency_key='consume-key'))
        self.parity(calls, replies, output)
        auth, authorized, consumed, replay, current = (replies[i] for i in (3, 4, 5, 6, 7))
        self.assertEqual(authorized['view']['phase'], 'AUTHORIZED')
        self.assertEqual(authorized['view']['version'], 1)
        self.assertIsNone(authorized['view']['consume_id'])
        self.assertEqual(consumed['receipt']['credential']['phase'], 'CONSUMED')
        self.assertEqual(replay['receipt'], auth['receipt'] | {'duplicate': True, 'applied': None})
        self.assertEqual(replay['receipt']['credential']['phase'], 'AUTHORIZED')
        self.assertEqual((current['view']['phase'], current['view']['version']), ('CONSUMED', 2))
        presentation = replies[-1]['view']['presentation']
        self.assertEqual((presentation['version'], presentation['holder_role']), (1, 'buyer-1'))
        self.assertFalse(presentation['fresh'])
        self.assertIn('Action snapshot: {"applied": null, "duplicate": true}', output)
        self.assertIn('Current local observation Stored credential=', output)
        self.assertIn('Action snapshot Authorization=', output)
        self.assertIn('Action snapshot Consumption=', output)
        self.assertIn('Current local observation Presentation=', output)

    def test_authorization_alone_never_consumes(self):
        status, calls, replies, output, errors = self.drive(AUTH + VIEW + ['quit'])
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([c['operation'] for c in calls], ['authorize_admission_inputs', 'view'])
        self.assertEqual((replies[-1]['view']['phase'], replies[-1]['view']['version']), ('AUTHORIZED', 1))
        self.assertIsNone(replies[-1]['view']['consume_id'])
        self.parity(calls, replies, output)

    def test_declined_consumption_submits_nothing(self):
        status, calls, replies, output, errors = self.drive(DECLINE_TRANSCRIPT.read_text().splitlines())
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([c['operation'] for c in calls], ['view', 'authorize_admission_inputs', 'view'])
        self.assertEqual(replies[-1]['view']['phase'], 'AUTHORIZED')
        self.assertIsNone(replies[-1]['view']['consume_id'])
        self.assertEqual(output.count('Declined; no request sent.'), 1)
        self.parity(calls, replies, output)

    def test_each_confirmation_is_literal_distinct_and_single_use(self):
        clock = ['set_clock', 'clock', '1000000', 'clock-key', 'SET_CLOCK']
        for action in (AUTH, CONSUME, clock):
            for answer in ('no', action[-1].lower(), 'SUBMIT', ' ' + action[-1],
                           'CONSUME' if action == AUTH else 'AUTHORIZE'):
                if answer == action[-1]:
                    continue
                status, calls, _, output, errors = self.drive(action[:-1] + [answer, 'quit'])
                self.assertEqual((status, calls, errors), (0, [], ''))
                self.assertIn('Declined; no request sent.', output)
        status, calls, replies, output, errors = self.drive(
            AUTH + CONSUME[:-1] + ['no'] + CONSUME[:-1] + ['AUTHORIZE'] + VIEW + ['quit'])
        self.assertEqual((status, len(calls), errors), (0, 2, ''))
        self.assertEqual(replies[-1]['view']['phase'], 'AUTHORIZED')
        # Consumption selection alone sends consumption only; it never authorizes.
        status, calls, replies, output, errors = self.drive(CONSUME + VIEW + ['quit'])
        self.assertEqual(status, 1)
        self.assertEqual(replies[0]['error'], {'code': 'ADMISSION_REQUIRED'})
        self.assertEqual([c['operation'] for c in calls], ['consume_inputs', 'view'])
        self.parity(calls, replies, output)

    def test_expiry_stale_holder_version_and_request_refusals_match_fsm(self):
        for index, value, code in ((2, '2', 'STALE_VERSION'), (3, 'other', 'NOT_HOLDER'),
                                   (5, 'BAD', 'ADMISSION_REQUEST'), (5, 'AA' * 32, 'ADMISSION_REQUEST')):
            args = AUTH_ARGS.copy()
            args[index] = value
            status, calls, replies, output, errors = self.drive(
                ['authorize_admission_inputs', *args, 'AUTHORIZE'] + VIEW + ['quit'])
            self.assertEqual(status, 1)
            self.assertEqual(replies[0]['error'], {'code': code})
            self.assertEqual(calls[0]['arguments'][('version' if index == 2 else
                'holder_role' if index == 3 else 'request')], int(value) if index == 2 else value)
            self.assertEqual(replies[-1]['view']['phase'], 'ELIGIBLE')
            self.parity(calls, replies, output)
        status, calls, replies, output, errors = self.drive(AUTH + CLOCK + CONSUME + VIEW + ['quit'])
        self.assertEqual(status, 1)
        self.assertEqual(replies[2]['error'], {'code': 'ADMISSION_EXPIRED'})
        self.assertEqual(replies[-1]['view']['phase'], 'AUTHORIZED')
        self.assertTrue(replies[-1]['view']['admission_expired'])
        self.assertIsNone(replies[-1]['view']['consume_id'])
        self.parity(calls, replies, output)

    def test_transferred_ticket_refusals_with_same_real_child(self):
        rows = [json.loads(line) for line in
                (HERE / 'fixtures/ticket_operations_admission_inputs.jsonl').read_text().splitlines()]
        setup = rows[9:14]  # Explicit existing resale selectors; no console setup/menu extension.
        answers = []
        for row in rows[14:18]:
            a = row['arguments']
            fields = (('admission_id', 'right_id', 'version', 'holder_role', 'gate_role', 'request', 'expires_ms')
                      if row['operation'] == 'authorize_admission_inputs' else
                      ('consume_id', 'right_id', 'version', 'gate_role', 'request'))
            answers += [row['operation'], *(str(a[k]) for k in fields), a['idempotency_key'],
                        'AUTHORIZE' if row['operation'] == 'authorize_admission_inputs' else 'CONSUME']
        answers += ['view_credential', 'issue-2', '2', 'buyer-3', 'view', 'issue-2', 'quit']
        client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
        try:
            for row in setup:
                self.assertNotIn('error', client.request(row))
            status, calls, replies, output, errors = self.drive(answers, client=client)
        finally:
            client.close()
        self.assertEqual(status, 1)
        self.assertEqual([r['error']['code'] for r in replies[:4]],
                         ['STALE_VERSION', 'NOT_HOLDER', 'STALE_VERSION', 'NOT_HOLDER'])
        # Stored adopted credential and current ownership/presentation must stay distinct.
        self.assertEqual(replies[-1]['view']['holder_role'], 'buyer-2')
        self.assertEqual(replies[-2]['view']['presentation']['holder_role'], 'buyer-3')
        self.assertFalse(replies[-2]['view']['presentation']['fresh'])
        self.parity(calls, replies, output, setup)

    def test_changed_binding_preserves_first_result_and_text(self):
        changed = AUTH.copy()
        changed[6] = '22' * 32
        status, calls, replies, output, errors = self.drive(AUTH + changed + AUTH + VIEW + ['quit'])
        self.assertEqual(status, 1)
        self.assertEqual(replies[1]['error'], {'code': 'IDEMPOTENCY_CONFLICT'})
        self.assertEqual(replies[2]['receipt'], replies[0]['receipt'] | {'duplicate': True, 'applied': None})
        self.assertEqual(calls[1]['arguments']['request'], '22' * 32)
        self.parity(calls, replies, output)
        # Accepted text and integer values are never derived from a prior reply or normalized.
        custom = AUTH.copy()
        custom[1], custom[6], custom[8] = 'Entry-Ω', 'ab' * 32, 'Key-Ω'
        status, calls, replies, output, errors = self.drive(custom + ['quit'])
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(calls[0]['arguments']['admission_id'], 'Entry-Ω')
        self.assertEqual(calls[0]['arguments']['idempotency_key'], 'Key-Ω')
        self.assertEqual(calls[0]['arguments']['request'], 'ab' * 32)
        self.parity(calls, replies, output)

    def test_malformed_terminal_fields_submit_nothing_and_do_not_infer(self):
        invalids = [(0, ''), (0, ' padded'), (2, '1.0'), (2, '1e3'), (2, '-1'), (2, '１'),
                    (2, '9' * 5000), (5, ' ' + '11' * 32), (6, '1.0'), (7, '')]
        for index, value in invalids:
            client, output = Mock(), io.StringIO()
            status = run_console(client, input_stream=script(
                ['authorize_admission_inputs', *AUTH_ARGS[:index], value, 'quit']),
                output_stream=output, error_stream=io.StringIO())
            self.assertEqual(status, 0)
            client.request.assert_not_called()
            self.assertIn('input_error=', output.getvalue())
        status, calls, replies, output, errors = self.drive(['authorize', 'consume', 'reconcile', 'quit'])
        self.assertEqual((status, calls, errors), (0, [], ''))
        # Integer above float's exact range goes unchanged to existing semantic validation.
        status, calls, replies, output, errors = self.drive(
            ['view_credential', 'issue-1', '9007199254740993', 'buyer-1', 'quit'])
        self.assertEqual(calls[0]['arguments']['version'], 9007199254740993)
        self.parity(calls, replies, output)

    def test_consumption_confirmation_eof_interrupt_and_read_failure_send_nothing(self):
        for failure in (None, KeyboardInterrupt('interrupted'), OSError('read failed')):
            lines = script(AUTH + CONSUME[:-1])
            class BrokenInput:
                def readline(self):
                    line = lines.readline()
                    if line:
                        return line
                    if failure:
                        raise failure
                    return ''
            status, calls, replies, output, errors = self.drive([], stream=BrokenInput())
            self.assertEqual((status, len(calls)), (2, 1))
            self.assertEqual(calls[0]['operation'], 'authorize_admission_inputs')
            self.assertEqual(json.JSONDecoder().raw_decode(errors.split('FENCED: ')[1])[0]['last_reply'], replies[0])

    def test_documented_transcripts_as_cli_subprocesses(self):
        for answers in (CONSUME_TRANSCRIPT, DECLINE_TRANSCRIPT):
            result = subprocess.run([sys.executable, '-B', str(HERE / 'admission_console.py'),
                '--fixture', str(FIXTURE), '--cleanup-timeout', '1'], input=answers.read_text(),
                text=True, capture_output=True, timeout=10, env=os.environ.copy())
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            self.assertIn('"phase": "CONSUMED"' if answers == CONSUME_TRANSCRIPT else '"phase": "AUTHORIZED"', result.stdout)
            self.assertIn('Action snapshot', result.stdout)
            self.assertIn('Current local observation', result.stdout)


if __name__ == '__main__':
    unittest.main()
