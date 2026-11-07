"""Source-informed console/client composition; reuse existing synthetic desk vectors."""

from copy import deepcopy
import io
import json
import os
import subprocess
import sys
import threading
import unittest
from unittest.mock import Mock, patch

from reward_client import RewardClient, RewardClientStateError, RewardTransportUncertainty
from reward_console import main, run_subprocess_console
from reward_fixture import load_fixture
import test_reward_client as client_tests
from test_reward_console import (CONSOLE, FIXTURE, READS, answers, mutation_examples,
                                 printed, script)
from test_reward_session import FIXTURES, OPERATIONS, requests
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE


IDS = {'operation': 'reward_ids', 'arguments': {}}


def diagnostics(output):
    return [json.loads(line.removeprefix('FENCED: ')) for line in output.splitlines()]


class RewardConsoleSubprocessTests(unittest.TestCase):
    def drive(self, lines=(), *, input_stream=None, output=None, configure=None, fixture=FIXTURE):
        """Run with a test-only deadline and deterministic child teardown, never polling."""
        output = io.StringIO() if output is None else output
        errors, calls, clients, result = io.StringIO(), [], [], []
        launch = RewardClient.launch

        def owned(*args, **kwargs):
            client = launch(*args, **kwargs)
            clients.append(client)
            self.addCleanup(client.close)
            request = client.request
            def record(row):
                calls.append(deepcopy(row))
                return request(row)
            client.request = record
            if configure:
                configure(client)
            return client

        done = threading.Event()
        def run():
            try:
                with patch('sys.stdin', input_stream if input_stream is not None else script(lines)), \
                        patch('sys.stdout', output), patch('sys.stderr', errors):
                    result.append(main(['--fixture', str(fixture), '--mode', 'subprocess',
                                        '--cleanup-timeout', '1']))
            except BaseException as error:
                result.append(error)
            finally:
                done.set()

        with patch('reward_console.RewardClient.launch', side_effect=owned) as launched, \
                patch('reward_console.load_fixture', side_effect=AssertionError('in-process fallback')), \
                patch('reward_console.dispatch_request', side_effect=AssertionError('in-process dispatch')), \
                patch('socket.socket', side_effect=AssertionError('socket')), \
                patch('socket.create_connection', side_effect=AssertionError('connection')):
            thread = threading.Thread(target=run)
            thread.start()
            completed = done.wait(10)
            if not completed:
                for client in clients:
                    client._process.kill()
            thread.join(10)
            self.assertFalse(thread.is_alive(), 'console did not stop within harness deadline')
            self.assertTrue(completed, 'console reply must arrive before input EOF')
            launched.assert_called_once_with(fixture, cleanup_timeout=1.0)
        if isinstance(result[0], BaseException):
            raise result[0]
        self.assertEqual(len(clients), 1)
        process = clients[0]._process
        self.assertIsNotNone(process.returncode)
        self.assertTrue(process.stdin.closed)
        self.assertTrue(process.stdout.closed)
        if os.name == 'posix':
            with self.assertRaises(ChildProcessError):
                os.waitpid(process.pid, os.WNOHANG)
        return result[0], calls, output.getvalue(), errors.getvalue(), clients[0]

    def parity(self, calls, output):
        session = load_fixture(FIXTURE)
        expected = [client_tests.direct(session, row) for row in calls]
        replies = printed('desk', output)
        self.assertEqual(replies, expected)
        for reply in replies:
            self.assertEqual(reply['provenance'], PROVENANCE)
            receipt = reply.get('receipt')
            reward = reply.get('view') or (receipt or {}).get('reward')
            if reward:
                self.assertEqual(reward['unit'], 'POINT_F4')
                self.assertTrue(reward['non_transferable_until_chargeback_end'])
            for value in (receipt, reward):
                if value:
                    for flag in ALWAYS_FALSE_FLAGS:
                        self.assertIs(value[flag], False)
        return replies

    def test_live_console_journey_before_eof(self):
        rows = requests('participation')
        output, children = io.StringIO(), []
        environment = dict(os.environ)
        environment.pop('PYTHONUNBUFFERED', None)

        def incremental():
            # Generate the next selection only after observing the previous reply.
            for index, row in enumerate(rows):
                self.assertEqual(len(printed('desk', output.getvalue())), index)
                self.assertFalse(children[0]._process.stdin.closed)
                if row['operation'] == 'view':
                    row = deepcopy(row)
                    row['arguments']['reward_id_value'] = printed('desk', output.getvalue())[0]['receipt']['reward']['reward_id']
                yield from answers(row)
            self.assertEqual(len(printed('desk', output.getvalue())), len(rows))
            self.assertFalse(children[0]._process.stdin.closed)
            yield 'quit'
        pending = incremental()
        class Input:
            def readline(self):
                return next(pending) + '\n'
        with patch.dict(os.environ, environment, clear=True), \
                patch('reward_client.subprocess.Popen', wraps=subprocess.Popen) as launched:
            status, calls, text, errors, _ = self.drive(input_stream=Input(), output=output,
                                                       configure=children.append)
        self.assertEqual((status, calls, errors), (0, rows, ''))
        replies = self.parity(calls, text)
        self.assertEqual(printed('proposed', text), [row for row in rows if row['operation'] not in READS])
        self.assertEqual(replies[5]['receipt']['reward']['phase'], 'OBSERVED')
        self.assertTrue(replies[5]['receipt']['duplicate'])
        self.assertEqual(replies[-3]['view']['phase'], 'ISSUED')
        self.assertEqual(len(replies[-1]['pool_view']['spends']), 1)
        launched.assert_called_once()

    def test_live_console_scenario_parity(self):
        scenarios = [requests('cancellation'), requests('unknown_pending'),
                     requests('unknown_pending') + requests('unknown_resolution'),
                     requests('boundaries'), requests('participation')[:5] + mutation_examples()[-1:]]
        seen = set()
        for rows in scenarios:
            with self.subTest(operations=[r['operation'] for r in rows]):
                status, calls, output, errors, _ = self.drive([v for row in rows for v in answers(row)] + ['quit'])
                self.assertEqual((calls, errors), (rows, ''))
                replies = self.parity(calls, output)
                self.assertEqual(status, int(any('error' in r for r in replies)))
                seen.update(r['operation'] for r in calls)
                if rows == requests('unknown_pending'):
                    self.assertEqual([r['view']['phase'] for r in replies if 'view' in r], ['UNKNOWN', 'UNKNOWN'])
                    self.assertEqual(replies[-1]['pool_view']['spends'], [])
                if rows == requests('unknown_pending') + requests('unknown_resolution'):
                    self.assertEqual([r['view']['phase'] for r in replies if 'view' in r], ['UNKNOWN', 'UNKNOWN', 'ISSUED'])
                    self.assertEqual(len(replies[-1]['pool_view']['spends']), 1)
                if rows == requests('cancellation'):
                    self.assertEqual([r['view']['phase'] for r in replies if 'view' in r], ['REVERSED', 'CLAWBACK_CLAIM'])
                    refund = next(r['receipt'] for r in replies if r['operation'] == 'observe_krw_refund')
                    self.assertEqual(refund['reward']['phase'], 'ISSUED')
                    self.assertEqual(refund['reward']['krw_phase'], 'KRW_REFUND_NOTED')
                    self.assertNotEqual(refund['effect']['krw_effect_id'], refund['reward']['token_effect_id'])
        self.assertEqual(seen, set(OPERATIONS))

    def test_client_confirmation_dispatch_counts(self):
        # Every mutation is proposed three times, but only the middle selection sends.
        rows = mutation_examples()
        lines = [v for row in rows for confirm in (' SUBMIT', 'SUBMIT', 'no')
                 for v in answers(row, confirm)]
        status, calls, output, errors, _ = self.drive(lines + ['reward_ids', 'quit'])
        self.assertEqual((calls, errors), (rows + [IDS], ''))
        self.assertEqual(printed('proposed', output), [row for row in rows for _ in range(3)])
        self.assertEqual(output.count('Declined; no request sent.'), len(rows) * 2)
        self.parity(calls, output)
        self.assertEqual(status, 1)  # Explicitly selected invalid transitions stay visible.

    def test_optional_omission_null_and_opaque_inputs_reach_child(self):
        for explicit_null in (False, True):
            rows = requests('participation')[:4]
            rows[0]['arguments']['source_view']['metadata']['opaque'] = {'nested': [False, None, '한글']}
            for row, names in ((rows[2], ('abuse_kind', 'recipient_cap', 'program_cap')),
                               (rows[3], ('budget_ceiling', 'execution_permit'))):
                for name in names:
                    row['arguments'].pop(name, None)
                    if explicit_null:
                        row['arguments'][name] = None
            if explicit_null:
                rows[-1]['arguments']['approval_ref']['prior_record'] = None
            sent = []
            def capture(client):
                original = client._process.stdin.write
                def write(raw):
                    sent.append(json.loads(raw))
                    return original(raw)
                client._process.stdin.write = write
            status, calls, output, errors, _ = self.drive([v for r in rows for v in answers(r)] + ['quit'], configure=capture)
            self.assertEqual((status, calls, sent, errors), (0, rows, rows, ''))
            self.parity(calls, output)

    def test_client_error_envelopes_and_status(self):
        row = requests('participation')[0]
        for operation, error in ((None, {'code': 'INVALID_AMOUNT'}),
                                 (None, {'type': 'OSError', 'message': 'setup failed'}),
                                 ('observe', {'type': 'FixtureError', 'message': 'bad shape'})):
            reply = {'operation': operation, 'provenance': PROVENANCE, 'error': error}
            log, worker = client_tests.RewardClientTests.fault_worker(self, client_tests.wire(reply))
            with patch('reward_client.subprocess.Popen', side_effect=worker):
                status, calls, output, errors, client = self.drive(answers(row) + ['reward_ids', 'quit'])
            self.assertEqual((status, calls, printed('desk', output)), (2, [row], [reply]))
            self.assertEqual(diagnostics(errors)[0]['last_reply'], reply)
            self.assertIsNone(client.uncertainty)
            self.assertEqual(json.loads(log.read_bytes()), row)
            self.assertEqual(output.count('Actions:'), 1)

    def test_uncertainty_stops_and_preserves_evidence(self):
        row = requests('participation')[0]
        for raw in (b'{', b'\xff\n', b'not-json\n'):
            log, worker = client_tests.RewardClientTests.fault_worker(self, raw)
            with patch('reward_client.subprocess.Popen', side_effect=worker) as launched:
                status, calls, output, errors, client = self.drive(answers(row) + ['reward_ids'] + answers(row) + ['quit'])
            self.assertEqual((status, calls, printed('desk', output)), (2, [row], []))
            detail = diagnostics(errors)[0]
            self.assertEqual(detail['request'], row)
            self.assertEqual(bytes.fromhex(detail['request_bytes_hex']), log.read_bytes())
            self.assertEqual(bytes.fromhex(detail['reply_bytes_hex']), raw)
            self.assertIsNone(detail['last_reply'])
            self.assertEqual(detail['exceptions'][0]['type'], 'RewardTransportUncertainty')
            self.assertGreater(len(detail['exceptions']), 1)
            self.assertEqual(client.uncertainty.reply_bytes, raw)
            with self.assertRaises(RewardClientStateError):
                client.request(IDS)
            launched.assert_called_once()

    def test_partial_reply_interruption_and_short_write_stop(self):
        row = requests('participation')[0]
        for interrupted in (False, True):
            def fault(client):
                if interrupted:
                    read = Mock(side_effect=[b'{', KeyboardInterrupt('caller interrupt')])
                    client._process.stdout.read = read
                else:
                    client._process.stdin.write = Mock(return_value=1)
            status, calls, output, errors, client = self.drive(answers(row) + ['pool_view', 'quit'], configure=fault)
            self.assertEqual((status, calls), (2, [row]))
            detail = diagnostics(errors)[0]
            self.assertEqual(detail['request'], row)
            self.assertEqual(bytes.fromhex(detail['reply_bytes_hex']), b'{' if interrupted else b'')
            self.assertEqual(detail['exceptions'][-1]['type'], 'KeyboardInterrupt' if interrupted else 'OSError')
            self.assertIsNotNone(client.uncertainty)

    def test_subprocess_options_and_mode_isolation(self):
        cases = [['--mode', 'subprocess'], ['--cleanup-timeout', '1'],
                 ['--mode', 'in-process', '--cleanup-timeout', '1'], ['--mode', 'other']]
        with patch('reward_console.load_fixture') as load, patch('reward_console.RewardClient.launch') as launch, \
                patch('reward_client.subprocess.Popen') as popen, patch('sys.stderr', io.StringIO()):
            for options in cases:
                with self.assertRaises(SystemExit) as error:
                    main(['--fixture', str(FIXTURE)] + options)
                self.assertEqual(error.exception.code, 2)
            with self.assertRaises(SystemExit):
                main(['--mode', 'subprocess', '--cleanup-timeout', '1'])
            load.assert_not_called()
            launch.assert_not_called()
            popen.assert_not_called()
        with patch('reward_console.load_fixture') as load, patch('reward_client.subprocess.Popen') as popen, \
                patch('sys.stderr', io.StringIO()) as errors:
            for timeout in ('0', '-1', 'nan', 'inf', '-inf', 'bad'):
                try:
                    status = main(['--fixture', str(FIXTURE), '--mode', 'subprocess', '--cleanup-timeout=' + timeout])
                except SystemExit as error:
                    status = error.code
                self.assertEqual(status, 2)
            load.assert_not_called()
            popen.assert_not_called()
        for options in ([], ['--mode', 'in-process']):
            with patch('reward_console.load_fixture', wraps=load_fixture) as load, \
                    patch('reward_console.RewardClient.launch') as launch, \
                    patch('sys.stdin', script(['quit'])), patch('sys.stdout', io.StringIO()):
                self.assertEqual(main(['--fixture', str(FIXTURE)] + options), 0)
            load.assert_called_once_with(FIXTURE)
            launch.assert_not_called()

    def test_quit_eof_interrupt_and_render_failure_reap(self):
        for ending in ('quit', 'eof', 'interrupt', 'dispatch', 'proposal', 'render'):
            class BrokenOutput(io.StringIO):
                def write(self, text):
                    if text.startswith('proposed=' if ending == 'proposal' else 'desk='):
                        raise OSError('render failed')
                    return super().write(text)
            pending = iter(answers(requests('participation')[0]))
            class InterruptedInput:
                def readline(self):
                    try:
                        return next(pending) + '\n'
                    except StopIteration:
                        raise KeyboardInterrupt('input interrupt')
            def configure(client):
                if ending == 'dispatch':
                    client.request = Mock(side_effect=RuntimeError('dispatch failed'))
            kwargs = {'configure': configure}
            if ending == 'interrupt':
                kwargs['input_stream'] = InterruptedInput()
            if ending in ('proposal', 'render'):
                kwargs['output'] = BrokenOutput()
            status, calls, output, errors, _ = self.drive(answers(requests('participation')[0]) +
                ([] if ending == 'eof' else ['quit']), **kwargs)
            self.assertEqual(status, 0 if ending == 'quit' else 2)
            if ending == 'proposal':
                self.assertEqual(calls, [])
            if ending in ('render', 'interrupt', 'eof'):
                self.assertIsNotNone(diagnostics(errors)[0]['last_reply'])
        # Diagnostic sink failure itself must neither escape ownership nor resume dispatch.
        class BrokenDiagnostic(io.StringIO):
            def write(self, text):
                raise OSError('diagnostic failed')
        client = RewardClient.launch(FIXTURE, cleanup_timeout=1)
        with patch('reward_console.RewardClient.launch', return_value=client):
            self.assertEqual(run_subprocess_console(FIXTURE, cleanup_timeout=1, input_stream=io.StringIO(),
                output_stream=io.StringIO(), error_stream=BrokenDiagnostic()), 2)
        self.assertIsNotNone(client._process.returncode)
        self.assertTrue(client._process.stdout.closed)

    def test_eof_at_confirmation_reaps_without_sending(self):
        status, calls, output, errors, _ = self.drive(answers(requests('participation')[0])[:-1])
        self.assertEqual((status, calls, printed('desk', output)), (2, [], []))
        self.assertIn('EOFError', errors)

    def test_invalid_fixture_is_terminal_and_reaped_without_fallback(self):
        missing = FIXTURE.with_name('absent-live-console-fixture.json')
        status, calls, output, errors, client = self.drive(['reward_ids', 'pool_view', 'quit'], fixture=missing)
        self.assertEqual((status, calls), (2, [IDS]))
        self.assertEqual(client._process.returncode, 2)
        replies = printed('desk', output)
        if replies:
            self.assertEqual(len(replies), 1)
            self.assertIsNone(replies[0]['operation'])
            self.assertEqual(replies[0]['error']['type'], 'FileNotFoundError')
            self.assertEqual(diagnostics(errors)[0]['last_reply'], replies[0])
        else:
            self.assertIsNotNone(client.uncertainty)  # Existing startup/write race.

    def test_cleanup_failure_preserves_primary_diagnostics_and_last_reply(self):
        row = requests('participation')[0]
        prior = {'operation': 'reward_ids', 'provenance': PROVENANCE, 'reward_ids': []}
        uncertainty = RewardTransportUncertainty(row, client_tests.wire(row), b'{\xff')
        uncertainty.__cause__ = OSError('lost response')
        client = Mock()
        client.request.side_effect = [prior, uncertainty]
        client.close.side_effect = OSError('cleanup failed')
        output, errors = io.StringIO(), io.StringIO()
        with patch('reward_console.RewardClient.launch', return_value=client) as launched:
            status = run_subprocess_console(FIXTURE, cleanup_timeout=1,
                input_stream=script(['reward_ids'] + answers(row) + ['pool_view', 'quit']),
                output_stream=output, error_stream=errors)
        self.assertEqual(status, 2)
        self.assertEqual([call.args[0] for call in client.request.call_args_list], [IDS, row])
        first, cleanup = diagnostics(errors.getvalue())
        self.assertEqual(first['last_reply'], prior)
        self.assertEqual(first['reply_bytes_hex'], '7bff')
        self.assertEqual(first['exceptions'][-1]['message'], 'lost response')
        self.assertEqual(cleanup['last_reply'], prior)
        self.assertEqual(cleanup['exceptions'][0]['message'], 'cleanup failed')
        client.close.assert_called_once()
        launched.assert_called_once()

    def test_client_state_failure_stops_queued_actions(self):
        client = Mock()
        client.request.side_effect = RewardClientStateError('client already fenced')
        client.close.return_value = 0
        output, errors = io.StringIO(), io.StringIO()
        with patch('reward_console.RewardClient.launch', return_value=client):
            status = run_subprocess_console(FIXTURE, cleanup_timeout=1,
                input_stream=script(['reward_ids', 'pool_view', 'quit']),
                output_stream=output, error_stream=errors)
        self.assertEqual(status, 2)
        client.request.assert_called_once_with(IDS)
        client.close.assert_called_once()
        self.assertEqual(output.getvalue().count('Actions:'), 1)
        self.assertEqual(diagnostics(errors.getvalue())[0]['exceptions'][0]['type'], 'RewardClientStateError')

    def test_unexpected_child_exit_is_not_clean_quit(self):
        for code in (1, 2, 7, -15):
            client = Mock()
            client.close.return_value = code
            errors = io.StringIO()
            with patch('reward_console.RewardClient.launch', return_value=client):
                status = run_subprocess_console(FIXTURE, cleanup_timeout=1,
                    input_stream=script(['quit']), output_stream=io.StringIO(), error_stream=errors)
            self.assertEqual(status, 2)
            self.assertIn(f'exited with status {code}', errors.getvalue())
            client.request.assert_not_called()
            client.close.assert_called_once()
        log, worker = client_tests.RewardClientTests.fault_worker(self, b'', exited=True)
        with patch('reward_client.subprocess.Popen', side_effect=worker):
            status, calls, _, errors, client = self.drive(answers(requests('participation')[0]) + ['quit'])
        self.assertEqual(status, 2)
        self.assertIsNotNone(client.uncertainty)
        self.assertIn('exited with status 7', errors)
        self.assertEqual(len(log.read_bytes().splitlines()), 1)

    def test_cli_transcripts_match_default_in_process(self):
        for name, expected_code in (('reward_console_journey.txt', 0), ('reward_console_boundaries.txt', 1)):
            text = (FIXTURES / name).read_text(encoding='utf-8')
            command = [sys.executable, '-B', str(CONSOLE), '--fixture', str(FIXTURE)]
            direct = subprocess.run(command, input=text, text=True, capture_output=True, timeout=10)
            live = subprocess.run(command + ['--mode', 'subprocess', '--cleanup-timeout', '1'],
                                  input=text, text=True, capture_output=True, timeout=10)
            self.assertEqual((live.returncode, live.stderr, live.stdout),
                             (expected_code, '', direct.stdout))
            self.assertEqual(direct.returncode, expected_code)


if __name__ == '__main__':
    unittest.main()
