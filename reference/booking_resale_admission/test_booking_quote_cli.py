"""Strict source fixture and file/stdin confirmation, preserving the original desk."""

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
from booking_cli import dispatch_request, run_requests
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture
from booking_session import BookingSession
from reservation_fsm import ReservationMachine
from test_booking_quote_adapter import build
from test_booking_quote_source import source_for
from test_booking_session import HERE, requests
from test_reservation_fsm import assert_not_final

QUOTES = HERE / 'fixtures' / 'booking_quotes.json'


def rows(name='booking_recorded_confirm'):
    return [json.loads(line) for line in (HERE / 'fixtures' / f'{name}.jsonl').read_text().splitlines()]


def run(session, texts, adapter=None):
    output = io.StringIO()
    with redirect_stdout(output):
        status = run_requests(session, texts, quote_adapter=adapter)
    return status, [json.loads(line) for line in output.getvalue().splitlines()]


class BookingQuoteCliTests(unittest.TestCase):
    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(HERE / 'booking_cli.py'), *args],
                              input=stdin, text=True, capture_output=True, check=False)

    def test_file_and_stdin_transcripts_reach_confirmed_without_downstream_effects(self):
        for name, status in (('booking_recorded_confirm', 0), ('booking_recorded_boundaries', 1)):
            path = HERE / 'fixtures' / f'{name}.jsonl'
            outputs = []
            for selector, stdin in ((str(path), None), ('-', path.read_text())):
                result = self.cli('--quotes', str(QUOTES), '--requests', selector, stdin=stdin)
                self.assertEqual((result.returncode, result.stderr), (status, ''))
                output = [json.loads(line) for line in result.stdout.splitlines()]
                self.assertEqual(len(output), len(rows(name)))
                outputs.append(output)
                for row in output:
                    if 'error' not in row:
                        assert_not_final(self, row.get('receipt', row.get('view')))
            self.assertEqual(*outputs)
            output = outputs[0]
            if status == 0:
                self.assertEqual(output[-2]['view']['phase'], 'CONFIRMED')
                self.assertTrue(output[4]['receipt']['duplicate'])
            else:
                errors = [row['error'] for row in output if 'error' in row]
                self.assertEqual([error.get('type', error.get('code')) for error in errors],
                                 ['BookingQuoteNotFound', 'InvalidBookingQuoteRecord',
                                  'InvalidBookingQuoteRecord', 'BookingQuoteSourceError',
                                  'BookingQuoteSourceError', 'PRIMARY_PRICE_MISMATCH',
                                  'IDEMPOTENCY_CONFLICT', 'BookingQuoteSourceError',
                                  'IDEMPOTENCY_CONFLICT', 'RESERVATION_EXPIRED'])
                self.assertEqual(output[10]['receipt']['reservation']['phase'], 'CONFIRMED')
            for field in ('payment_ref', 'settlement_id', 'issuance_id', 'right'):
                self.assertIsNone(output[-2]['view'][field])
            self.assertEqual(output[-1]['view']['show']['payment_ref_count'], 0)
            machine = ReservationMachine()
            session = BookingSession(machine)
            source = load_fixture(QUOTES)
            adapter = BookingQuoteAdapter(session, source)
            actual = []
            for row in rows(name):
                line_status, result = run(session, [json.dumps(row)], adapter)
                actual += result
                self.assertIn(line_status, (0, 1))
            self.assertEqual(actual, outputs[0])
            self.assertEqual(source.calls, tuple(row['arguments']['recording_id'] for row in rows(name)
                                                if row['operation'] == 'confirm_recorded_quote'))
            self.assertLessEqual({entry['op'] for entry in machine.export_journal()},
                                 {'set_clock', 'register_show', 'hold', 'confirm', 'cancel'})
            self.assertEqual(sum(entry['op'] == 'confirm' for entry in machine.export_journal()), 1)

    def test_quote_selector_is_opt_in_and_ticket_desk_does_not_receive_adapter(self):
        session = Mock()
        with self.assertRaises(FixtureError):
            dispatch_request(session, rows()[3])
        self.assertEqual(session.mock_calls, [])
        # Existing calls behave identically, with and without a source fixture.
        path = HERE / 'fixtures' / 'booking_confirm.jsonl'
        without = self.cli('--requests', str(path))
        with_source = self.cli('--requests', str(path), '--quotes', str(QUOTES))
        self.assertEqual((with_source.returncode, with_source.stdout, with_source.stderr),
                         (without.returncode, without.stdout, without.stderr))
        from ticket_operations_cli import dispatch_request as ticket_dispatch
        desk = Mock()
        with self.assertRaises(FixtureError):
            ticket_dispatch(desk, {'surface': 'booking', **rows()[3]})
        self.assertEqual(desk.mock_calls, [])

    def test_strict_recorded_request_fields_and_duplicate_keys_stop_without_fetch(self):
        valid = rows()[3]
        bad_rows = [None, [], True, valid | {'extra': 1},
                    valid | {'arguments': []}, valid | {'operation': []},
                    valid | {'arguments': valid['arguments'] | {'amount': 10001}}]
        bad_rows += [valid | {'arguments': {k: v for k, v in valid['arguments'].items() if k != field}}
                     for field in valid['arguments']]
        texts = [json.dumps(row) for row in bad_rows]
        texts += ['{"operation":"confirm_recorded_quote","operation":"view","arguments":{}}',
                  '{"operation":"confirm_recorded_quote","arguments":{"recording_id":"a","recording_id":"b"}}']
        for text in texts:
            session, adapter = Mock(), Mock()
            status, output = run(session, [text, json.dumps(requests()[0])], adapter)
            self.assertEqual((status, len(output)), (2, 1))
            self.assertEqual(output[0]['error']['type'], 'FixtureError')
            self.assertEqual(session.mock_calls, [])
            self.assertEqual(adapter.mock_calls, [])

    def test_invalid_caller_scalars_are_local_errors_and_only_explicit_lines_continue(self):
        for field in rows()[3]['arguments']:
            for value in (None, True, 1, 1.0, [], {}, ''):
                source = source_for()
                session = Mock()
                session._machine.view.return_value = {'explicit_view': True}
                adapter = BookingQuoteAdapter(session, source)
                row = deepcopy(rows()[3])
                row['arguments'][field] = value
                status, output = run(session, [json.dumps(row), json.dumps(rows()[5])], adapter)
                self.assertEqual((status, len(output)), (1, 2))
                self.assertEqual(output[0]['error']['type'], 'InvalidBookingQuoteRecord')
                self.assertEqual(source.calls, ())
                session.confirm.assert_not_called()
        # Source failure continues, but missing clock and malformed JSON stop with 2.
        session = BookingSession(ReservationMachine())
        adapter = BookingQuoteAdapter(session, load_fixture(QUOTES))
        status, output = run(session, [json.dumps(rows('booking_recorded_boundaries')[3]),
                                      json.dumps(rows()[3]), json.dumps(rows()[0])], adapter)
        self.assertEqual((status, len(output)), (2, 2))
        self.assertEqual(output[-1]['error']['type'], 'BookingInputError')
        machine, session = build()
        status, output = run(session, [json.dumps(rows('booking_recorded_boundaries')[3]), '{'],
                             BookingQuoteAdapter(session, load_fixture(QUOTES)))
        self.assertEqual((status, len(output)), (2, 2))
        self.assertEqual(output[-1]['error']['type'], 'FixtureError')

    def test_fixture_strict_structure_scalars_duplicates_and_lazy_record_validation(self):
        valid = dict(fixture_version=1, provenance='MOCK_GATE_ONLY', quotes=[
            dict(recording_id='record-1', recorded_text='not JSON yet')])
        variants = [None, [], True, {}, valid | {'extra': 1}]
        variants += [{k: v for k, v in valid.items() if k != field} for field in valid]
        variants += [valid | {'fixture_version': value} for value in (True, 1.0, '1', 0, 2, None, [])]
        variants += [valid | {'provenance': value} for value in (None, True, 1, [], {}, 'LIVE')]
        variants += [valid | {'quotes': value} for value in (None, True, 1, {}, 'text')]
        entry = valid['quotes'][0]
        entries = [None, [], True, {}, {'recording_id': 'x'}, entry | {'extra': 1},
                   entry | {'fault': 'synthetic_booking_quote_error'}]
        entries += [entry | {'recording_id': value} for value in (None, True, 1, [], {}, '', ' bad ', 'x' * 101)]
        entries += [entry | {'recorded_text': value} for value in (None, True, 1, [], {})]
        entries += [dict(recording_id='x', fault=value) for value in (None, True, 1, [], {}, 'timeout')]
        variants += [valid | {'quotes': [value]} for value in entries]
        variants += [valid | {'quotes': [entry, entry]}]
        texts = [json.dumps(value) for value in variants]
        texts += ['{"fixture_version":1,"fixture_version":1,"provenance":"MOCK_GATE_ONLY","quotes":[]}',
                  '{"fixture_version":1,"provenance":"MOCK_GATE_ONLY","quotes":[{"recording_id":"a","recording_id":"b","recorded_text":"{}"}]}']
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'quotes.json'
            for text in texts:
                path.write_text(text)
                with self.subTest(text=text), patch('booking_quote_fixture.FakeBookingQuoteSource') as fake:
                    with self.assertRaises(FixtureError):
                        load_fixture(path)
                    fake.assert_not_called()
            path.write_text(json.dumps(valid))
            source = load_fixture(path)  # text is deliberately decoded only upon fetch
            self.assertEqual(source.calls, ())
            from booking_quote_source import InvalidBookingQuoteRecord
            with self.assertRaises(InvalidBookingQuoteRecord):
                source.fetch('record-1')
            path.write_text(json.dumps(valid | {'quotes': []}))
            self.assertEqual(dict(load_fixture(path).recordings), {})

    def test_fixture_errors_encoding_and_import_have_no_setup_side_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'quotes.json'
            for content in (b'{', b'\xff'):
                path.write_bytes(content)
                result = self.cli('--quotes', str(path), '--requests', '-')
                self.assertEqual((result.returncode, result.stderr), (2, ''))
                self.assertIsNone(json.loads(result.stdout)['operation'])
            result = self.cli('--quotes', str(path) + '.missing', '--requests', '-')
            self.assertEqual(result.returncode, 2)
        result = subprocess.run([sys.executable, '-c',
                                 'import booking_quote_source, fake_booking_quote_source, '
                                 'booking_quote_adapter, booking_quote_fixture, booking_cli'],
                                cwd=HERE, capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
