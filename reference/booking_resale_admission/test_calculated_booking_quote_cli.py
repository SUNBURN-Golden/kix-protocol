"""Socket-free calculated-source journeys across both existing local desks."""

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from admission_fixture import FixtureError
import booking_cli
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_source import BookingQuoteNotFound, BookingQuoteSourceError, InvalidBookingQuoteRecord
from booking_session import BookingSession
from calculated_booking_quote_fixture import load_fixture as load_quotes
from calculated_booking_quote_source import CalculatedBookingQuoteSource, calculate_booking_quote
from reservation_fsm import ReservationError, ReservationMachine
from test_booking_session import snapshot as booking_snapshot
from test_calculated_booking_quote_source import HERE, QUOTES
from test_reservation_fsm import assert_not_final
from test_ticket_operations_session import FIXTURE, machines, snapshot
from ticket_operations_fixture import load_fixture as load_desk
import ticket_operations_cli


def rows(desk, scenario):
    return [json.loads(line) for line in (HERE / 'fixtures' /
            f'{desk}_calculated_{scenario}.jsonl').read_text().splitlines()]


def outcome(call):
    try:
        return call()
    except (ReservationError, BookingQuoteSourceError) as error:
        return (type(error).__name__, getattr(error, 'code', str(error)))


class CalculatedBookingQuoteCliTests(unittest.TestCase):
    def cli(self, desk, *args, stdin=''):
        # Enforced inside this child before importing the CLI, independent of env.
        code = '''
import runpy, sys
def deny(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden: ' + event)
sys.addaudithook(deny)
runpy.run_module(sys.argv.pop(1), run_name='__main__')
'''
        extra = ['--fixture', str(FIXTURE)] if desk == 'ticket_operations' else []
        return subprocess.run([sys.executable, '-B', '-c', code, desk + '_cli', *extra, *args],
                              input=stdin, text=True, capture_output=True)

    def test_each_transcript_matches_direct_session_and_keeps_other_surfaces_unchanged(self):
        for name, cli in (('booking', booking_cli), ('ticket_operations', ticket_operations_cli)):
            for scenario in ('confirm', 'boundaries'):
                shared = name == 'ticket_operations'
                desk = load_desk(FIXTURE) if shared else BookingSession(ReservationMachine())
                direct = load_desk(FIXTURE) if shared else BookingSession(ReservationMachine())
                session = desk.booking if shared else desk
                control = direct.booking if shared else direct
                snap = (lambda d: snapshot(machines(d))) if shared else (lambda d: booking_snapshot(d._machine))
                before = snap(desk)
                original = session.view('reserve-1') if shared else None
                source = load_quotes(QUOTES)
                adapter = BookingQuoteAdapter(session, source)
                expected_calls = []
                for row in rows(name, scenario):
                    with self.subTest(desk=name, scenario=scenario, row=row):
                        actual = outcome(lambda: cli.dispatch_request(desk, row, quote_adapter=adapter))
                        def direct_call():
                            operation, args = row['operation'], dict(row['arguments'])
                            if operation == 'confirm_recorded_quote':
                                recording_id = args.pop('recording_id')
                                entry = source.requests.get(recording_id)
                                if entry is None:
                                    raise BookingQuoteNotFound(recording_id)
                                quote = calculate_booking_quote(entry['request_text'])
                                if entry['reservation_id'] != args['reservation_id']:
                                    raise InvalidBookingQuoteRecord('reservation_id does not match expected reservation')
                                args.update(amount=int(quote['totals']['payableAtoms']), quote_ref=quote['quoteHash'])
                                result = control.confirm(**args)
                            else:
                                result = getattr(control, operation)(**args)
                            return dict(operation=operation,
                                        **({'surface': 'booking'} if shared else {}),
                                        **{'view' if operation.startswith('view') else 'receipt': result})
                        self.assertEqual(actual, outcome(direct_call))
                        self.assertEqual(snap(desk), snap(direct))
                        if row['operation'] == 'confirm_recorded_quote':
                            expected_calls.append(row['arguments']['recording_id'])
                        self.assertEqual(source.calls, tuple(expected_calls))
                        if isinstance(actual, dict):
                            assert_not_final(self, actual.get('receipt', actual.get('view')))
                reservation = session.view('desk-reserve-1' if shared else 'reserve-1')
                self.assertEqual(reservation['phase'], 'CONFIRMED' if scenario == 'confirm' else 'CANCELLED')
                for field in ('payment_ref', 'settlement_id', 'issuance_id', 'right'):
                    self.assertIsNone(reservation[field])
                if shared:
                    after = snap(desk)
                    self.assertEqual((before[0], before[2:]), (after[0], after[2:]))
                    self.assertEqual(session.view('reserve-1'), original)
                    self.assertEqual(desk.resale._adapter._source.calls, ())
                    self.assertEqual(desk.admission._adapter._source.calls, ())

    def test_both_desks_file_and_stdin_rows_exits_and_computed_hash(self):
        for desk in ('booking', 'ticket_operations'):
            for scenario, status in (('confirm', 0), ('boundaries', 1)):
                path = HERE / 'fixtures' / f'{desk}_calculated_{scenario}.jsonl'
                outputs = []
                for selector, stdin in ((str(path), ''), ('-', path.read_text())):
                    child = self.cli(desk, '--calculated-quotes', str(QUOTES), '--requests', selector, stdin=stdin)
                    self.assertEqual(child.returncode, status, child.stdout + child.stderr)
                    self.assertEqual(child.stderr, '')
                    result = [json.loads(line) for line in child.stdout.splitlines()]
                    self.assertEqual(len(result), len(rows(desk, scenario)))
                    outputs.append(result)
                self.assertEqual(*outputs)
                result = outputs[0]
                if scenario == 'confirm':
                    self.assertEqual(result[3]['receipt']['reservation']['quote_ref'],
                                     load_quotes(QUOTES).fetch('calc-1')['quote_ref'])
                    self.assertEqual(result[3]['receipt']['reservation']['amount'], 10001)
                    self.assertTrue(result[4]['receipt']['duplicate'])
                else:
                    errors = [row['error'] for row in result if 'error' in row]
                    self.assertEqual([e['code'] for e in errors if 'code' in e],
                                     ['PRIMARY_PRICE_MISMATCH', 'IDEMPOTENCY_CONFLICT',
                                      'IDEMPOTENCY_CONFLICT', 'RESERVATION_EXPIRED'])
                    self.assertEqual(len(errors), 11)

    def test_opt_in_mutual_exclusion_and_unchanged_recorded_and_unconfigured_behavior(self):
        for desk in ('booking', 'ticket_operations'):
            both = self.cli(desk, '--quotes', str(QUOTES), '--calculated-quotes', str(QUOTES), '--requests', '-')
            self.assertEqual(both.returncode, 2)
            self.assertIn('not allowed with argument', both.stderr)
            transcript = HERE / 'fixtures' / f'{desk}_recorded_confirm.jsonl'
            recorded = HERE / 'fixtures' / ('booking_quotes.json' if desk == 'booking'
                                            else 'ticket_operations_booking_quotes.json')
            self.assertEqual(self.cli(desk, '--quotes', str(recorded), '--requests', str(transcript)).returncode, 0)
            self.assertEqual(self.cli(desk, '--requests', str(transcript)).returncode, 2)
            plain = HERE / 'fixtures' / ('booking_confirm.jsonl' if desk == 'booking'
                                        else 'ticket_operations_booking.jsonl')
            without = self.cli(desk, '--requests', str(plain))
            with_source = self.cli(desk, '--calculated-quotes', str(QUOTES), '--requests', str(plain))
            self.assertEqual((without.returncode, without.stdout, without.stderr),
                             (with_source.returncode, with_source.stdout, with_source.stderr))
            self.assertEqual(without.returncode, 0 if desk == 'booking' else 1)

    def test_loading_has_no_calculation_fetch_or_clock_and_shared_binding_is_exact(self):
        with patch('calculated_booking_quote_source.calculate_booking_quote', side_effect=AssertionError('calculate')), \
                patch.object(CalculatedBookingQuoteSource, 'fetch', side_effect=AssertionError('fetch')):
            source = load_quotes(QUOTES)
            self.assertEqual(source.calls, ())
            for cli in (booking_cli, ticket_operations_cli):
                args = ['--calculated-quotes', str(QUOTES), '--requests', '-']
                if cli is ticket_operations_cli:
                    args += ['--fixture', str(FIXTURE)]
                with patch.object(cli, 'run_requests', return_value=0) as runner, patch('sys.stdin', io.StringIO('')):
                    self.assertEqual(cli.main(args), 0)
                session = runner.call_args.args[0]
                adapter = runner.call_args.kwargs['quote_adapter']
                self.assertIs(adapter._session, session.booking if cli is ticket_operations_cli else session)
                self.assertEqual(adapter._source.calls, ())

    def test_strict_fixture_schema_encoding_lazy_failure_and_cli_exits(self):
        valid = json.loads(QUOTES.read_text())
        entry = valid['calculations'][0]
        variants = [None, [], {}, valid | {'extra': 1}]
        variants += [valid | {'fixture_version': v} for v in (True, 2, '1', None)]
        variants += [valid | {'provenance': v} for v in ('MOCK_GATE_ONLY', None)]
        variants += [valid | {'calculations': v} for v in (None, {}, True, 'text')]
        entries = [None, [], {}, entry | {'extra': 1}]
        entries += [{k: v for k, v in entry.items() if k != field} for field in entry]
        entries += [entry | {field: v} for field in entry for v in (None, True, 1, [], {})]
        entries += [entry | {field: ''} for field in ('recording_id', 'reservation_id')]
        variants += [valid | {'calculations': [e]} for e in entries]
        variants += [valid | {'calculations': [entry, entry]}]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.json'
            for value in variants:
                path.write_text(json.dumps(value))
                with self.subTest(value=value), self.assertRaises(FixtureError):
                    load_quotes(path)
            for text in ('{', '{"fixture_version":1,"fixture_version":1}', 'NaN'):
                path.write_text(text)
                with self.assertRaises(FixtureError):
                    load_quotes(path)
            path.write_text(json.dumps(valid | {'calculations': []}))
            self.assertIsNone(load_quotes(path).fetch('absent'))
            for payload in (b'\xff', b'{'):
                path.write_bytes(payload)
                for desk in ('booking', 'ticket_operations'):
                    self.assertEqual(self.cli(desk, '--calculated-quotes', str(path), '--requests', '-').returncode, 2)
            for desk in ('booking', 'ticket_operations'):
                for fixture_path in (str(path) + '.missing', str(QUOTES)):
                    result = self.cli(desk, '--calculated-quotes', fixture_path, '--requests', '-', stdin='{\n')
                    self.assertEqual(result.returncode, 2)
                journey = rows(desk, 'confirm')
                missing_clock = journey[3]
                result = self.cli(desk, '--calculated-quotes', str(QUOTES), '--requests', '-', stdin=json.dumps(missing_clock))
                self.assertEqual(result.returncode, 2)
                self.assertIn('BookingInputError', result.stdout)
                refused_then_structural = rows(desk, 'boundaries')[:5]
                result = self.cli(desk, '--calculated-quotes', str(QUOTES), '--requests', '-',
                                  stdin=''.join(json.dumps(r)+'\n' for r in refused_then_structural)+'{\n')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(len(result.stdout.splitlines()), 6)


if __name__ == '__main__':
    unittest.main()
