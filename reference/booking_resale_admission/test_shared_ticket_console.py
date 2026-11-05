"""Source-informed composition evidence; real pipes, synthetic service graph."""

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import shared_ticket_console as console
from test_admission_session import assert_flags
from test_reservation_fsm import assert_not_final
from test_resale_fsm import assert_not_final as assert_resale_flags
from resale_payment_source import ResalePaymentSourceError
from statement_source import StatementSourceError
from ticket_operations_cli import _error
from ticket_operations_cli import dispatch_request
from test_ticket_operations_client import direct
from test_ticket_settlement_controls import settlement_flags
from ticket_operations_client import TicketOperationsClient
from ticket_operations_fixture import load_fixture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = HERE / 'fixtures/ticket_operations_payment_session.json'
QUOTE = HERE / 'fixtures/booking_console_quote.json'
JOURNEY = HERE / 'fixtures/shared_ticket_console_journey.txt'
START_RESALE = HERE / 'fixtures/settlement_console_start_resale.txt'
INPUTS = HERE / 'fixtures/ticket_operations_settlement_inputs_session.json'
SURFACES = ('booking', 'resale', 'admission', 'settlement')
VIEWS = {'booking': ['view', 'reserve-1'], 'resale': ['view_right', 'issue-1'],
         'admission': ['view', 'issue-1'], 'settlement': ['view', 'resale-claim']}
QUEUE = [item for name in SURFACES for item in [name, *VIEWS[name], 'quit']] + ['quit']
CLOCK = ['set_clock', 'clock', '1000000', 'shared-clock']
HOLD = ['hold', 'shared-reservation', 'show-1', '1', 'shared-buyer', '1120000', 'shared-hold']
LOAD = ['load_quote', str(QUOTE)]
TARGET = ['target', 'shared-reservation', 'shared-order', 'shared-confirm']


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


def envelopes(output):
    return [json.loads(value) for value in re.findall(r'desk=(\{[^\n]+\})', output)]


class SharedTicketConsoleTests(unittest.TestCase):
    def drive(self, answers=(), *, client=None, stream=None, output=None, errors=None, fixture=FIXTURE):
        if client is None:
            client = TicketOperationsClient.launch(fixture, cleanup_timeout=1)
        output = io.StringIO() if output is None else output
        errors = io.StringIO() if errors is None else errors
        stream = script(answers) if stream is None else stream
        calls, replies = [], []
        original = client.request

        def record(row):
            calls.append(deepcopy(row))
            reply = original(row)
            replies.append(deepcopy(reply))
            return reply

        with patch.object(console.TicketOperationsClient, 'launch', return_value=client) as launch, \
                patch.object(client, 'request', side_effect=record), \
                patch.object(client, 'close', wraps=client.close) as close, \
                patch('sys.stdin', stream), patch('sys.stdout', output), patch('sys.stderr', errors):
            status = console.main(['--fixture', str(fixture), '--cleanup-timeout', '1'])
        launch.assert_called_once_with(fixture, cleanup_timeout=1)
        close.assert_called_once_with()
        if isinstance(client, TicketOperationsClient):
            self.assertTrue(client._process.stdin.closed)
            self.assertTrue(client._process.stdout.closed)
            self.assertIsNotNone(client._process.returncode)
        return status, calls, replies, output.getvalue(), errors.getvalue()

    def parity(self, calls, replies, output):
        # Direct service methods share source with the desk; no independent FSM claim.
        control = load_fixture(FIXTURE)
        expected = []
        for row in calls:
            try:
                expected.append(direct(control, row))
            except (ResalePaymentSourceError, StatementSourceError) as error:
                expected.append(_error(row['surface'], row['operation'], error))
        self.assertEqual(replies, expected)
        self.assertEqual(envelopes(output), replies)
        for row in calls:
            self.assertEqual(set(row), {'surface', 'operation', 'arguments'})

    def test_live_shared_journey_one_child(self):
        answers = JOURNEY.read_text().splitlines()
        answers[answers.index('reference/booking_resale_admission/fixtures/booking_console_quote.json')] = str(QUOTE)
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(answers)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([(r['surface'], r['operation']) for r in calls], [
            ('booking', op) for op in ('set_clock', 'hold', 'preview_calculated_quote',
                                      'confirm_calculated_quote', 'view')
        ] + [('resale', op) for op in ('list_resale_inputs', 'hold_buy', 'observe_recorded_payment',
                                      'bind_settlement', 'accept_resale')]
          + [('admission', 'view'), ('admission', 'view_credential'),
             ('settlement', 'distribute'), ('settlement', 'view'), ('booking', 'view'),
             ('resale', 'view'), ('resale', 'view_right'), ('settlement', 'view')])
        self.parity(calls, replies, output)
        self.assertEqual(replies[4]['view'], replies[14]['view'])
        self.assertEqual(replies[14]['view']['phase'], 'CONFIRMED')
        self.assertEqual(replies[15]['view']['phase'], 'TRANSFERRED')
        self.assertEqual(replies[16]['view']['right']['holder_role'], 'buyer-2')
        self.assertEqual(replies[16]['view']['right']['version'], 2)
        # Stored venue credential is intentionally not reissued after transfer.
        self.assertEqual(replies[10]['view']['holder_role'], 'buyer-1')
        self.assertEqual(replies[11]['view']['presentation']['decision'], 'STALE_VERSION')
        self.assertFalse(replies[11]['view']['presentation']['fresh'])
        self.assertEqual(replies[13]['view'], replies[17]['view'])
        self.assertEqual(replies[17]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[17]['view']['claim']['distribution_order'], ['organizer'])
        for i in (0, 1, 3):
            assert_not_final(self, replies[i]['receipt'])
        assert_not_final(self, replies[14]['view'])
        for i in range(5, 10):
            assert_resale_flags(self, replies[i]['receipt'])
        assert_flags(self, replies[10]['view'])
        assert_flags(self, replies[11]['view'])
        for i in (13, 17):
            settlement_flags(self, replies[i]['view'])
        for label in ('MOCK_GATE_ONLY', 'MOCK_SETTLEMENT_ONLY', 'CALCULATION_ONLY', 'IN_MEMORY_FSM',
                      'UNDETERMINED — Astra/User', 'UNDETERMINED — User/designated advisers'):
            self.assertIn(label, output)

    def test_resale_start_journey_creates_target_and_preserves_ticket_observations(self):
        from settlement_fsm import SettlementError
        from test_settlement_console import POLICY, SettlementConsoleTests
        control = load_fixture(INPUTS)
        for identity in ('claim-2', 'resale-claim'):
            with self.assertRaises(SettlementError) as error:
                control.settlement.view(identity)
            self.assertEqual(error.exception.code, 'UNKNOWN_SETTLEMENT')
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(
                START_RESALE.read_text().splitlines(), fixture=INPUTS)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        sequence = [('booking', 'view'), ('resale', 'list_resale_inputs'),
                    ('resale', 'view'), ('resale', 'view_right')]
        sequence += [('settlement', op) for action in ('initiate_from_resale', 'authorize',
            'capture', 'commit_recorded_statement', 'observe_recorded_statement', 'distribute',
            'initiate_from_resale') for op in (action, 'view')]
        sequence += [('booking', 'view'), ('resale', 'view'), ('resale', 'view_right')]
        self.assertEqual([(r['surface'], r['operation']) for r in calls], sequence)
        for row, reply in zip(calls, replies, strict=True):
            self.assertEqual(reply, dispatch_request(control, row))
        self.assertEqual(envelopes(output), replies)
        self.assertEqual([json.loads(s) for s in re.findall(r'proposed=(\{[^\n]+\})', output)],
                         [r for r in calls if not r['operation'].startswith('view')])
        self.assertEqual(calls[4]['arguments'], dict(settlement_id='resale-claim', listing_id='list-1',
            trade_id='explicit-resale-trade', debtor_role='explicit-debtor', policy=POLICY,
            idempotency_key='resale-input'))
        # All source views are explicit transcript actions, before and after settlement work.
        self.assertEqual(replies[0]['view'], replies[-3]['view'])
        self.assertEqual(replies[2]['view'], replies[-2]['view'])
        self.assertEqual(replies[3]['view'], replies[-1]['view'])
        self.assertEqual(replies[-2]['view']['phase'], 'LISTED')
        self.assertIsNone(replies[-2]['view']['settlement_id'])
        self.assertIsNone(replies[-2]['view']['payment_ref'])
        self.assertEqual(replies[-1]['view']['right']['holder_role'], 'buyer-1')
        self.assertEqual(replies[-1]['view']['right']['version'], 1)
        selected = replies[4:-3]
        self.assertEqual([selected[i]['view']['phase'] for i in (1, 3, 5, 7)],
                         ['INITIATED', 'AUTHORIZED', 'CAPTURED', 'COMMITTED'])
        for i in (0, 2):
            self.assertIsNone(selected[i]['receipt']['settlement']['claim'])
        self.assertEqual(selected[4]['receipt']['settlement']['claim']['confirmed_cash'], 0)
        for reply in selected:
            value = reply['view'] if 'view' in reply else reply['receipt']['settlement']
            self.assertEqual((value['gross'], value['currency']), (8000, 'KRW'))
            settlement_flags(self, value)
        SettlementConsoleTests.summaries(self, selected, output)
        self.assertEqual(selected[-1]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(selected[-2]['receipt'], selected[0]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual(selected[-1]['view'], selected[-3]['view'])
        assert_not_final(self, replies[-3]['view'])
        assert_resale_flags(self, replies[-2]['view'])
        assert_resale_flags(self, replies[-1]['view'])

    def test_navigation_sends_nothing(self):
        answers = ['unknown', '', 'BOOKING'] + [v for name in SURFACES for v in (name, 'quit')] + ['quit']
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(answers)
        launch.assert_called_once()
        self.assertEqual((status, calls, replies, errors), (0, [], [], ''))
        self.assertEqual(output.count('Unknown surface;'), 3)
        # Surface main() is never involved; each run_console receives identical objects.
        client, stream, output, errors = Mock(), script([*SURFACES, 'quit']), io.StringIO(), io.StringIO()
        from contextlib import ExitStack
        with ExitStack() as stack:
            delegates = [stack.enter_context(patch.object(console._SURFACES[name], 'run_console', return_value=0))
                         for name in SURFACES]
            self.assertEqual(console.run_console(client, input_stream=stream,
                output_stream=output, error_stream=errors), 0)
        for delegate in delegates:
            delegate.assert_called_once_with(client, input_stream=stream, output_stream=output, error_stream=errors)
        client.request.assert_not_called()
        client.close.assert_not_called()  # Embedded lifecycle belongs to caller.

    def test_resale_initiation_conflict_preserves_current_view(self):
        from settlement_fsm import SettlementError
        answers = START_RESALE.read_text().splitlines()
        index = len(answers) - 1 - answers[::-1].index('initiate_from_resale')
        answers[index + 3] = 'changed-trade'
        status, calls, replies, output, errors = self.drive(answers, fixture=INPUTS)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        control = load_fixture(INPUTS)
        for row, reply in zip(calls, replies, strict=True):
            try:
                expected = dispatch_request(control, row)
            except SettlementError as error:
                expected = _error(row['surface'], row['operation'], error)
            self.assertEqual(reply, expected)
        self.assertEqual(envelopes(output), replies)
        self.assertEqual(replies[16]['error'], dict(code='IDEMPOTENCY_CONFLICT'))
        self.assertEqual(replies[15]['view'], replies[17]['view'])
        self.assertEqual(replies[2]['view'], replies[-2]['view'])

    def test_booking_reentry_discards_preview(self):
        answers = (['booking'] + CLOCK + HOLD + LOAD + TARGET + ['preview', 'quit',
            'admission', *VIEWS['admission'], 'quit', 'booking', 'confirm', 'preview']
            + LOAD + ['preview'] + TARGET + ['confirm', 'preview', 'confirm', 'decline',
            'confirm', 'preview', 'confirm', 'CONFIRM', 'view', 'shared-reservation', 'quit', 'quit'])
        status, calls, replies, output, errors = self.drive(answers)
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([row['operation'] for row in calls], ['set_clock', 'hold',
            'preview_calculated_quote', 'view', 'preview_calculated_quote',
            'preview_calculated_quote', 'confirm_calculated_quote', 'view'])
        self.assertEqual(output.count('Load quote text and set target before preview.'), 2)
        self.assertEqual(output.count('A new successful preview is required.'), 3)
        self.assertIn('Declined; no confirmation sent.', output)
        self.assertEqual(calls[-2]['arguments'], dict(request_text=QUOTE.read_text(),
            reservation_id='shared-reservation', order_id='shared-order', idempotency_key='shared-confirm'))
        self.assertEqual(replies[-1]['view']['phase'], 'CONFIRMED')
        self.parity(calls, replies, output)

    def test_actual_business_refusals_allow_explicit_switching(self):
        answers = [v for name in SURFACES for v in (name, 'view', 'missing', 'quit')]
        # Both source-error envelopes are from existing selectors, with caller-selected missing IDs.
        answers += ['resale', 'observe_recorded_payment', 'missing', 'list-1', 'missing-pay', 'SUBMIT',
                    'quit', 'settlement', 'observe_recorded_statement', 'resale-claim', 'missing',
                    'missing-statement', 'SUBMIT', 'quit', 'booking', 'view', 'reserve-1', 'quit', 'quit']
        status, calls, replies, output, errors = self.drive(answers)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertTrue(all(set(r['error']) == {'code'} for r in replies[:4]))
        self.assertTrue(all(set(r['error']) == {'type', 'message'} for r in replies[4:6]))
        self.assertIn('view', replies[-1])
        self.parity(calls, replies, output)

    def test_exact_refusal_envelope_matrix_and_sticky_status(self):
        for name in SURFACES:
            for detail in ({'code': 'STALE_VERSION'}, {'type': 'RecordedFactNotFound', 'message': 'missing "☀"\nrecord'}):
                with self.subTest(surface=name, detail=detail):
                    client = Mock()
                    client.close.return_value = 0
                    client.request.side_effect = lambda row: dict(surface=row['surface'], operation=row['operation'],
                                                                  error=deepcopy(detail))
                    status, calls, replies, output, errors = self.drive(
                        [name, *VIEWS[name], 'quit', 'admission', 'quit', 'quit'], client=client)
                    self.assertEqual((status, errors, len(calls)), (1, '', 1))
                    self.assertEqual(replies, [dict(surface=name, operation=VIEWS[name][0], error=detail)])
                    self.assertEqual(envelopes(output), replies)
                    self.assertEqual(output.count('Surfaces:'), 3)

    def test_terminal_envelopes_fence_every_surface(self):
        for name in SURFACES:
            for kind in ('FixtureError', 'BookingInputError', 'startup'):
                with self.subTest(surface=name, kind=kind):
                    client = Mock()
                    client.close.return_value = 0
                    reply = dict(surface=None if kind == 'startup' else name,
                        operation=None if kind == 'startup' else VIEWS[name][0],
                        error=dict(type='FixtureError' if kind == 'startup' else kind, message='terminal original'))
                    client.request.return_value = reply
                    pending = script([name, *VIEWS[name], *QUEUE])
                    status, calls, replies, output, errors = self.drive(client=client, stream=pending)
                    self.assertEqual((status, len(calls), replies), (2, 1, [reply]))
                    self.assertEqual(envelopes(output), [reply])
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], reply)

    def test_real_malformed_truncated_and_eof_replies_fence_every_surface(self):
        for name in SURFACES:
            for raw in (b'not-json\n', b'{partial\xff', b''):
                with self.subTest(surface=name, raw=raw):
                    worker = ('import sys; sys.stdin.buffer.readline(); '
                              'sys.stdout.buffer.write(' + repr(raw) + '); sys.stdout.buffer.flush()')
                    popen = subprocess.Popen
                    def launch_worker(command, **kwargs):
                        return popen([sys.executable, '-B', '-c', worker], **kwargs)
                    pending = script([name, *VIEWS[name], *QUEUE])
                    with patch('ticket_operations_client.subprocess.Popen', side_effect=launch_worker) as launch:
                        client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
                        status, calls, replies, _, errors = self.drive(client=client, stream=pending)
                    launch.assert_called_once()
                    self.assertEqual((status, len(calls), replies), (2, 1, []))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertEqual(client.uncertainty.request, calls[0])
                    self.assertEqual(client.uncertainty.reply_bytes, raw)
                    self.assertIn('TicketDeskTransportUncertainty', errors)
                    self.assertIn('reply_bytes', errors)

    def test_real_write_uncertainty_and_request_interruption_fence_every_surface(self):
        for name in SURFACES:
            for fault in ('broken', 'short', 'interrupted'):
                with self.subTest(surface=name, fault=fault):
                    with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
                        client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
                        if fault == 'interrupted':
                            context = patch.object(client._process.stdout, 'read', side_effect=KeyboardInterrupt('exchange'))
                        else:
                            context = patch.object(client._process.stdin, 'write', **(
                                {'return_value': 1} if fault == 'short' else {'side_effect': BrokenPipeError('write')}))
                        pending = script([name, *VIEWS[name], *QUEUE])
                        with context as transport:
                            status, calls, replies, _, errors = self.drive(client=client, stream=pending)
                            transport.assert_called_once()
                    launch.assert_called_once()
                    self.assertEqual((status, len(calls), replies), (2, 1, []))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertIsNotNone(client.uncertainty)
                    self.assertIn('TicketDeskTransportUncertainty', errors)

    def test_input_failures_at_menu_and_every_surface_fence_queued_navigation(self):
        for name in (None, *SURFACES):
            for failure in (EOFError('end'), KeyboardInterrupt('interrupt'), OSError('input')):
                with self.subTest(surface=name, failure=type(failure).__name__):
                    prefix = [] if name is None else [name, *VIEWS[name]]
                    pending = script([*prefix, *QUEUE])
                    class BrokenInput:
                        reads = 0
                        def readline(self):
                            if self.reads < len(prefix):
                                self.reads += 1
                                return pending.readline()
                            if self.reads == len(prefix):
                                self.reads += 1
                                if isinstance(failure, EOFError):
                                    return ''
                                raise failure
                            return pending.readline()
                    status, calls, replies, _, errors = self.drive(stream=BrokenInput())
                    self.assertEqual((status, len(calls)), (2, 0 if name is None else 1))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertIn(type(failure).__name__, errors)
                    if name is not None:
                        self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], replies[-1])

    def test_display_failures_fence_all_surfaces_even_with_broken_diagnostics(self):
        class BrokenOutput(io.StringIO):
            def write(self, text):
                if text.startswith('desk='):
                    raise BrokenPipeError('display')
                return super().write(text)
        class BrokenDiagnostics(io.StringIO):
            def write(self, text):
                raise OSError('diagnostics')
        for name in SURFACES:
            for broken_diagnostics in (False, True):
                with self.subTest(surface=name, diagnostics=broken_diagnostics):
                    pending = script([name, *VIEWS[name], *QUEUE])
                    status, calls, replies, _, errors = self.drive(stream=pending,
                        output=BrokenOutput(), errors=BrokenDiagnostics() if broken_diagnostics else io.StringIO())
                    self.assertEqual((status, len(calls), len(replies)), (2, 1, 1))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    if not broken_diagnostics:
                        self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], replies[-1])
        class BrokenMenu(io.StringIO):
            def write(self, text):
                raise OSError('menu output')
        status, calls, _, _, errors = self.drive(QUEUE, output=BrokenMenu())
        self.assertEqual((status, calls), (2, []))
        self.assertIn('menu output', errors)

    def test_unexpected_surface_results_and_exceptions_stop_without_more_input(self):
        for name in SURFACES:
            for fault in (None, False, -1, 3, '0', RuntimeError('surface failed'), KeyboardInterrupt('surface')):
                with self.subTest(surface=name, fault=fault):
                    pending = script([name, *QUEUE])
                    behavior = {'side_effect': fault} if isinstance(fault, BaseException) else {'return_value': fault}
                    with patch.object(console._SURFACES[name], 'run_console', **behavior) as delegate:
                        status, calls, _, _, errors = self.drive(stream=pending)
                    self.assertEqual((status, calls), (2, []))
                    delegate.assert_called_once()
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertIn('FENCED:', errors)

    def test_cli_arguments_import_launch_and_cleanup_failures(self):
        for args in ([], ['--fixture', str(FIXTURE)], *(
                ['--fixture', str(FIXTURE), '--cleanup-timeout', value] for value in ('0', '-1', 'nan', 'inf'))):
            with patch('sys.stderr', io.StringIO()), patch('ticket_operations_client.subprocess.Popen') as launch:
                with self.assertRaises(SystemExit) as error:
                    console.main(args)
                self.assertEqual(error.exception.code, 2)
                launch.assert_not_called()
        probe = subprocess.run([sys.executable, '-B', '-c',
            "from unittest.mock import patch\nwith patch('subprocess.Popen', side_effect=AssertionError('import launched')):\n import shared_ticket_console\n"],
            cwd=HERE, capture_output=True, text=True, env=os.environ.copy(), timeout=10)
        self.assertEqual((probe.returncode, probe.stdout, probe.stderr), (0, '', ''))
        for failure in (OSError('launch failed'), KeyboardInterrupt('launch interrupted')):
            with patch.object(console.TicketOperationsClient, 'launch', side_effect=failure) as launch, \
                    patch('sys.stderr', io.StringIO()) as errors:
                self.assertEqual(console.main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']), 2)
            launch.assert_called_once()
            self.assertIn('FENCED:', errors.getvalue())
        for initial in (0, 1, 2):
            for cleanup in (0, 7, OSError('close failed'), KeyboardInterrupt('close interrupted')):
                with self.subTest(status=initial, cleanup=cleanup):
                    client = Mock()
                    if isinstance(cleanup, BaseException):
                        client.close.side_effect = cleanup
                    else:
                        client.close.return_value = cleanup
                    with patch.object(console, 'run_console', return_value=initial):
                        status, calls, _, _, _ = self.drive(client=client)
                    expected = 2 if isinstance(cleanup, BaseException) else (initial or int(cleanup != 0))
                    self.assertEqual((status, calls), (expected, []))

    def test_documented_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
            '--fixture', str(FIXTURE), '--cleanup-timeout', '1'], cwd=ROOT, input=JOURNEY.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        replies = envelopes(result.stdout)
        self.assertEqual(len(replies), 18)
        self.assertEqual({r['surface'] for r in replies}, set(SURFACES))
        self.assertEqual(replies[-1]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[14]['view']['phase'], 'CONFIRMED')
        self.assertEqual(replies[16]['view']['right']['holder_role'], 'buyer-2')

    def test_resale_start_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
            '--fixture', str(INPUTS), '--cleanup-timeout', '1'], cwd=ROOT, input=START_RESALE.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        replies = envelopes(result.stdout)
        self.assertEqual(len(replies), 21)
        self.assertEqual(replies[17]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[-2]['view']['phase'], 'LISTED')
        self.assertEqual(replies[-1]['view']['right']['holder_role'], 'buyer-1')


if __name__ == '__main__':
    unittest.main()
