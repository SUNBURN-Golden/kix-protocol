"""Live subprocess and fault evidence, synthetic only; no sockets or retries."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from ticket_operations_client import (TicketOperationsClient, TicketDeskClientStateError,
                                      TicketDeskTransportUncertainty)
from ticket_operations_fixture import load_fixture
from ticket_operations_cli import _DOMAIN_ERRORS, _error
from admission_fixture import FixtureError
from test_ticket_operations_session import FIXTURE, HERE, requests
from test_ticket_settlement_fact_inputs import FIXTURE as FACTS, rows as fact_rows
from test_ticket_settlement_controls import settlement_flags
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture as load_quotes
from calculated_booking_quote_fixture import load_fixture as load_calculated


LIST = requests('cancel')[0]
VIEW = dict(surface='resale', operation='view', arguments=dict(listing_id='list-1'))


def direct(session, row, adapter=None):
    """Session methods directly, bypassing CLI dispatch and subprocess client."""
    surface, operation, args = (row[k] for k in ('surface', 'operation', 'arguments'))
    try:
        target = adapter if operation == 'confirm_recorded_quote' else getattr(session, surface)
        value = getattr(target, operation)(**args)
        key = ('quote' if operation == 'preview_calculated_quote' else
               'view' if operation.startswith('view') else 'receipt')
        return dict(surface=surface, operation=operation, **{key: value})
    except _DOMAIN_ERRORS as error:
        return _error(surface, operation, error)


class TicketOperationsClientTests(unittest.TestCase):
    def launch(self, fixture=FIXTURE, **options):
        client = TicketOperationsClient.launch(fixture, cleanup_timeout=1, **options)
        self.addCleanup(client.close)
        return client

    def exchange(self, client, row):
        # Deadline is solely a test safeguard. No sleeps, polling or product timeout.
        done = threading.Event()
        result = []
        def call():
            try:
                result.append(client.request(row))
            except BaseException as error:
                result.append(error)
            finally:
                done.set()
        thread = threading.Thread(target=call)
        thread.start()
        completed = done.wait(10)
        if not completed:
            client._process.kill()
        thread.join(10)
        self.assertFalse(thread.is_alive(), 'request harness failed to stop')
        self.assertTrue(completed, 'response must arrive with child stdin still open')
        if isinstance(result[0], BaseException):
            raise result[0]
        return result[0]

    def test_buffered_child_reply_before_stdin_eof_and_response_derived_journey(self):
        environment = dict(os.environ)
        environment.pop('PYTHONUNBUFFERED', None)
        with patch.dict(os.environ, environment, clear=True), \
                patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            client = self.launch()
            session = load_fixture(FIXTURE)
            first = self.exchange(client, LIST)
            self.assertEqual(first, direct(session, LIST))
            self.assertFalse(client._process.stdin.closed)
            listing = first['receipt']['listing']
            view = dict(surface='resale', operation='view',
                        arguments=dict(listing_id=listing['listing_id']))
            cancel = dict(surface='resale', operation='cancel_listing', arguments=dict(
                listing_id=listing['listing_id'], seller_role=listing['seller_role'],
                idempotency_key='caller-cancel'))
            for row in (view, cancel, view, LIST, view):
                self.assertEqual(self.exchange(client, row), direct(session, row))
            self.assertEqual(self.exchange(client, view)['view']['phase'], 'CANCELLED')
            self.assertEqual(client.close(), 0)
            self.assertEqual(client.close(), 0)
            launch.assert_called_once()
            command = launch.call_args.args[0]
            self.assertEqual(command[0], sys.executable)
            self.assertNotIn('-u', command)
            self.assertTrue(Path(command[1]).is_absolute())
            self.assertFalse(launch.call_args.kwargs['shell'])
            self.assertNotIn('stderr', launch.call_args.kwargs)

    def test_settlement_fact_inputs_and_response_derived_current_view(self):
        session = load_fixture(FACTS)
        client = self.launch(FACTS)
        for row in fact_rows():
            reply = self.exchange(client, row)
            self.assertEqual(reply, direct(session, row))
            if 'receipt' in reply:
                settlement = reply['receipt']['settlement']
                derived = dict(surface='settlement', operation='view',
                               arguments=dict(settlement_id=settlement['settlement_id']))
                current = self.exchange(client, derived)
                self.assertEqual(current, direct(session, derived))
                settlement_flags(self, current['view'])
        self.assertEqual(client.close(), 0)

    def test_domain_and_source_errors_allow_explicit_continuation(self):
        client = self.launch()
        missing = deepcopy(LIST)
        missing['arguments']['offer_id'] = 'missing'
        self.assertIn('type', self.exchange(client, missing)['error'])
        bad = dict(surface='resale', operation='cancel_listing', arguments=dict(
            listing_id='missing', seller_role='buyer-1', idempotency_key='explicit-refusal'))
        self.assertIn('code', self.exchange(client, bad)['error'])
        self.assertEqual(self.exchange(client, LIST), direct(load_fixture(FIXTURE), LIST))
        self.assertEqual(client.close(), 1)

    def test_structural_and_booking_input_errors_are_terminal(self):
        for row, kind in ((LIST | {'extra': 1}, 'FixtureError'),
                          (requests('booking')[6], 'BookingInputError')):
            with self.subTest(kind=kind):
                client = self.launch()
                self.assertEqual(self.exchange(client, row)['error']['type'], kind)
                with self.assertRaises(TicketDeskClientStateError):
                    client.request(LIST)
                self.assertIsNone(client.uncertainty)
                self.assertEqual(client.close(), 2)

    def test_startup_failure_returns_existing_null_selector_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'bad.json'
            fixture.write_text('{}')
            try:
                load_fixture(fixture)
            except FixtureError as error:
                expected = _error(None, None, error)
            # A controlled worker guarantees delivery of this existing envelope.
            # A real startup failure can race submission and close its pipe first.
            log, worker = self.fault_worker(json.dumps(expected).encode() + b'\n')
            with patch('ticket_operations_client.subprocess.Popen', side_effect=worker) as launch:
                client = self.launch()
                self.assertEqual(self.exchange(client, LIST), expected)
                with self.assertRaises(TicketDeskClientStateError):
                    client.request(LIST)
                self.assertEqual(client.close(), 0)
                self.assertEqual(json.loads(log.read_bytes()), LIST)
                launch.assert_called_once()
            client = self.launch(fixture)
            try:
                reply = self.exchange(client, LIST)
            except TicketDeskTransportUncertainty as error:
                self.assertIsInstance(error.__cause__, BrokenPipeError)
                self.assertEqual(error.reply_bytes, b'')
            else:
                self.assertEqual(reply, expected)
            with self.assertRaises(TicketDeskClientStateError):
                client.request(LIST)
            self.assertEqual(client.close(), 2)

    def test_quote_payload_and_both_existing_quote_fixture_options(self):
        client = self.launch()
        session = load_fixture(FIXTURE)
        row = requests('quote_preview_confirm')[0]
        self.assertEqual(self.exchange(client, row), direct(session, row))
        self.assertEqual(self.exchange(client, row)['quote']['evidenceClass'], 'CALCULATION_ONLY')
        self.assertEqual(client.close(), 0)
        for option, scenario, filename, loader in (
                ('quotes', 'recorded_confirm', 'ticket_operations_booking_quotes.json', load_quotes),
                ('calculated_quotes', 'calculated_confirm', 'calculated_booking_quotes.json', load_calculated)):
            with self.subTest(option=option):
                fixture = HERE / 'fixtures' / filename
                session = load_fixture(FIXTURE)
                adapter = BookingQuoteAdapter(session.booking, loader(fixture))
                client = self.launch(**{option: fixture})
                # Compare the existing successful transcript with direct methods.
                for row in requests(scenario):
                    self.assertEqual(self.exchange(client, row), direct(session, row, adapter))
                self.assertEqual(client.close(), 0)

    def test_local_validation_before_write_and_context_exception_cleanup(self):
        with patch('ticket_operations_client.subprocess.Popen') as launch:
            for options in ({'cleanup_timeout': 0}, {'cleanup_timeout': float('nan')},
                            {'cleanup_timeout': True}, {'cleanup_timeout': 1, 'quotes': 'a',
                                                       'calculated_quotes': 'b'}):
                with self.assertRaises(ValueError):
                    TicketOperationsClient.launch(FIXTURE, **options)
            launch.assert_not_called()
        client = self.launch()
        with patch.object(client._process.stdin, 'write', wraps=client._process.stdin.write) as write:
            for bad in ([], LIST | {'extra': float('nan')}, LIST | {'extra': object()}):
                with self.assertRaises((ValueError, TypeError)):
                    client.request(bad)
            write.assert_not_called()
        self.assertEqual(self.exchange(client, LIST), direct(load_fixture(FIXTURE), LIST))
        original_write = client._process.stdin.write
        def reentrant_write(wire):
            with self.assertRaises(TicketDeskClientStateError):
                client.request(VIEW)
            return original_write(wire)
        with patch.object(client._process.stdin, 'write', side_effect=reentrant_write) as write:
            self.assertEqual(self.exchange(client, VIEW), direct_view_after_list())
            write.assert_called_once()
        with self.assertRaisesRegex(RuntimeError, 'caller failure'):
            with client:
                raise RuntimeError('caller failure')
        self.assertEqual(client.close(), 0)
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)
        with self.assertRaises(TicketDeskClientStateError):
            client.request(LIST)

    def test_concurrent_or_reentrant_requests_and_cleanup_rejected_before_write(self):
        client = self.launch()
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        original = client._process.stdout.read
        result = []
        def read(size):
            if not entered.is_set():
                entered.set()
                if not release.wait(10):
                    raise AssertionError('test release deadline')
            return original(size)
        def request():
            try:
                result.append(client.request(LIST))
            except BaseException as error:
                result.append(error)
            finally:
                finished.set()
        with patch.object(client._process.stdout, 'read', side_effect=read), \
                patch.object(client._process.stdin, 'write', wraps=client._process.stdin.write) as write:
            thread = threading.Thread(target=request)
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaises(TicketDeskClientStateError):
                    client.request(VIEW)
                with self.assertRaises(TicketDeskClientStateError):
                    client.close()
                self.assertEqual(write.call_count, 1)
            finally:
                release.set()
                if not finished.wait(10):
                    client._process.kill()
                thread.join(10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(result, [direct(load_fixture(FIXTURE), LIST)])
        self.assertEqual(self.exchange(client, VIEW), direct_view_after_list())

    def fault_worker(self, reply, *, exit_after=False, stubborn=False, linger=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        log = Path(temporary.name) / 'received'
        script = Path(temporary.name) / 'worker.py'
        script.write_text('import os, sys, signal\nfrom pathlib import Path\n'
            + ('signal.signal(signal.SIGTERM, signal.SIG_IGN)\n' if stubborn else '')
            + 'line = sys.stdin.buffer.readline()\n'
            + f'log = Path({str(log)!r})\nlog.write_bytes(line)\n'
            + ('os._exit(7)\n' if exit_after else
               f'sys.stdout.buffer.write({reply!r})\nsys.stdout.buffer.flush()\nos.close(1)\n')
            + ('while True: signal.pause()\n' if stubborn or linger else
               'log.write_bytes(line + sys.stdin.buffer.read())\n'))
        popen = subprocess.Popen
        def worker(command, **kwargs):
            return popen([sys.executable, str(script)], **kwargs)
        return log, worker

    def test_malformed_truncated_mismatched_and_exited_workers_never_resend(self):
        valid = dict(surface='resale', operation='list_resale', receipt={})
        faults = [b'', b'{', json.dumps(valid).encode(), b'\xff\n', b'[]\n', b'NaN\n',
                  b'{"surface":"resale","surface":"resale"}\n',
                  json.dumps(valid | {'operation': 'view'}).encode() + b'\n',
                  json.dumps(valid | {'error': {'code': 'X'}}).encode() + b'\n',
                  json.dumps(valid | {'receipt': []}).encode() + b'\n',
                  b'{"surface":"resale","operation":"list_resale","error":{"code":2}}\n',
                  b'{"surface":"resale","operation":"list_resale","error":{"type":"X"}}\n']
        for reply, exited in [(raw, False) for raw in faults] + [(b'', True)]:
            with self.subTest(reply=reply, exited=exited):
                log, worker = self.fault_worker(reply, exit_after=exited)
                with patch('ticket_operations_client.subprocess.Popen', side_effect=worker) as launch:
                    client = self.launch()
                    original = deepcopy(LIST)
                    with self.assertRaises(TicketDeskTransportUncertainty) as caught:
                        self.exchange(client, original)
                    uncertainty = caught.exception
                    self.assertEqual(uncertainty.request, LIST)
                    self.assertEqual(uncertainty.reply_bytes, reply)
                    original['arguments']['listing_id'] = 'mutated'
                    self.assertEqual(uncertainty.request, LIST)
                    for _ in range(2):
                        with self.assertRaises(TicketDeskClientStateError):
                            client.request(VIEW)
                    self.assertEqual(client.close(), 7 if exited else 0)
                    self.assertIs(client.uncertainty, uncertainty)
                    self.assertEqual(log.read_bytes(), uncertainty.request_bytes)
                    launch.assert_called_once()

    def test_short_write_broken_pipe_and_interruption_fence_without_remainder_write(self):
        for fault in ('short', 'broken', 'interrupted'):
            with self.subTest(fault=fault):
                client = self.launch()
                if fault == 'interrupted':
                    context = patch.object(client._process.stdout, 'read',
                                           side_effect=[b'{', KeyboardInterrupt()])
                else:
                    context = patch.object(client._process.stdin, 'write',
                        **({'return_value': 1} if fault == 'short' else {'side_effect': BrokenPipeError()}))
                with context as transport:
                    with self.assertRaises(TicketDeskTransportUncertainty) as caught:
                        client.request(LIST)
                    with self.assertRaises(TicketDeskClientStateError):
                        client.request(LIST)
                    self.assertEqual(transport.call_count, 2 if fault == 'interrupted' else 1)
                self.assertEqual(caught.exception.reply_bytes, b'{' if fault == 'interrupted' else b'')
                client.close()
                self.assertIs(client.uncertainty, caught.exception)

    def test_cleanup_deadline_kills_and_reaps_owned_stubborn_child(self):
        reply = json.dumps(dict(surface='resale', operation='list_resale', receipt={})).encode() + b'\n'
        _, worker = self.fault_worker(reply, stubborn=True)
        with patch('ticket_operations_client.subprocess.Popen', side_effect=worker) as launch:
            client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=0.1)
            self.addCleanup(client.close)
            self.exchange(client, LIST)  # signal handler installed before response
            with patch.object(client._process, 'terminate', wraps=client._process.terminate) as terminate, \
                    patch.object(client._process, 'kill', wraps=client._process.kill) as kill:
                self.assertEqual(client.close(), -9)
                self.assertEqual(client.close(), -9)
                terminate.assert_called_once()
                kill.assert_called_once()
            launch.assert_called_once()
            with self.assertRaises(ChildProcessError):
                os.waitpid(client._process.pid, os.WNOHANG)

    def test_cleanup_deadline_terminates_child_that_does_not_consume_eof(self):
        reply = json.dumps(dict(surface='resale', operation='list_resale', receipt={})).encode() + b'\n'
        _, worker = self.fault_worker(reply, linger=True)
        with patch('ticket_operations_client.subprocess.Popen', side_effect=worker) as launch:
            client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=0.1)
            self.addCleanup(client.close)
            self.exchange(client, LIST)
            with patch.object(client._process, 'terminate', wraps=client._process.terminate) as terminate, \
                    patch.object(client._process, 'kill', wraps=client._process.kill) as kill:
                self.assertEqual(client.close(), -15)
                terminate.assert_called_once()
                kill.assert_not_called()
            launch.assert_called_once()

    def test_import_launches_nothing_and_example_matches_direct_session(self):
        probe = subprocess.run([sys.executable, '-c',
            'from unittest.mock import patch\n'
            'with patch("subprocess.Popen", side_effect=AssertionError("import launched")):\n'
            ' import ticket_operations_client\n'], cwd=HERE, capture_output=True, timeout=10)
        self.assertEqual((probe.returncode, probe.stdout, probe.stderr), (0, b'', b''))
        command = [sys.executable, str(HERE / 'example_ticket_operations_client.py'),
                   '--fixture', str(FIXTURE), '--offer-id', 'offer-1', '--listing-id', 'list-1',
                   '--list-key', 'list-key', '--cancel-key', 'cancel-key', '--cleanup-timeout', '1']
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual((result.returncode, result.stderr), (0, b''))
        session = load_fixture(FIXTURE)
        cancel = requests('cancel')[2]
        expected = [direct(session, row) for row in (LIST, VIEW, cancel, VIEW)]
        self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
        command[command.index('offer-1')] = 'missing'
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn('error', json.loads(result.stdout))


def direct_view_after_list():
    session = load_fixture(FIXTURE)
    direct(session, LIST)
    return direct(session, VIEW)


if __name__ == '__main__':
    unittest.main()
