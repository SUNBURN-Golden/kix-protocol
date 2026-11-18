"""Request-time JSONL journeys on both local desks, with no startup quote source."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import unittest
from unittest.mock import patch

from admission_fixture import FixtureError
import booking_cli
from booking_quote_adapter import BookingQuoteAdapter
from booking_session import BookingSession
from calculated_booking_quote_source import CalculatedBookingQuoteSource, calculate_booking_quote
from reservation_fsm import ReservationMachine
from test_booking_session import snapshot as booking_snapshot
import test_calculated_booking_quote_cli as harness
from test_calculated_booking_quote_source import HERE, request
from test_reservation_fsm import assert_not_final
from test_ticket_operations_session import FIXTURE, machines, snapshot
from ticket_operations_fixture import load_fixture
import ticket_operations_cli


def rows(desk, scenario):
    path = HERE / 'fixtures' / f'{desk}_calculation_inputs_{scenario}.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines()]


def construct(shared):
    return load_fixture(FIXTURE) if shared else BookingSession(ReservationMachine())


def booking(desk, shared):
    return desk.booking if shared else desk


def snap(desk, shared):
    return snapshot(machines(desk)) if shared else booking_snapshot(desk._machine)


class BookingCalculationInputsCliTests(unittest.TestCase):
    def cli(self, desk, *args, stdin=''):
        return harness.CalculatedBookingQuoteCliTests.cli(self, desk, *args, stdin=stdin)

    def test_histories_match_source_adapter_receipts_errors_state_and_journals(self):
        for name, cli in (('booking', booking_cli), ('ticket_operations', ticket_operations_cli)):
            shared = name == 'ticket_operations'
            for scenario in ('confirm', 'boundaries'):
                desk, control = construct(shared), construct(shared)
                session, control_session = booking(desk, shared), booking(control, shared)
                before = snap(desk, shared)
                original = session.view('reserve-1') if shared else None
                for row in rows(name, scenario):
                    with self.subTest(desk=name, scenario=scenario, operation=row['operation']):
                        # Request-time dispatch never constructs or fetches a quote source.
                        with patch.object(CalculatedBookingQuoteSource, '__init__',
                                          side_effect=AssertionError('source constructed')), \
                                patch.object(CalculatedBookingQuoteSource, 'fetch',
                                             side_effect=AssertionError('source fetched')):
                            actual = harness.outcome(lambda: cli.dispatch_request(desk, row))
                        expected_row = deepcopy(row)
                        if row['operation'] == 'confirm_calculated_quote':
                            args = expected_row['arguments']
                            text = args.pop('request_text')
                            source = CalculatedBookingQuoteSource(requests={'chosen': {
                                'reservation_id': args['reservation_id'], 'request_text': text}})
                            adapter = BookingQuoteAdapter(control_session, source)
                            expected_row['operation'] = 'confirm_recorded_quote'
                            args['recording_id'] = 'chosen'
                            expected = harness.outcome(lambda: cli.dispatch_request(
                                control, expected_row, quote_adapter=adapter))
                            self.assertEqual(source.calls, ('chosen',))
                            if isinstance(expected, dict):
                                expected['operation'] = row['operation']
                        else:
                            expected = harness.outcome(lambda: cli.dispatch_request(control, expected_row))
                        self.assertEqual(actual, expected)
                        self.assertEqual(snap(desk, shared), snap(control, shared))
                        if isinstance(actual, dict):
                            assert_not_final(self, actual.get('receipt', actual.get('view')))
                view = session.view('desk-reserve-1' if shared else 'reserve-1')
                self.assertEqual(view['phase'], 'CONFIRMED' if scenario == 'confirm' else 'CANCELLED')
                for field in ('payment_ref', 'settlement_id', 'issuance_id', 'right'):
                    self.assertIsNone(view[field])
                if shared:
                    after = snap(desk, shared)
                    self.assertEqual((before[0], before[2:]), (after[0], after[2:]))
                    self.assertEqual(session.view('reserve-1'), original)
                    self.assertEqual(desk.resale._adapter._source.calls, ())
                    self.assertEqual(desk.admission._adapter._source.calls, ())

    def test_file_and_stdin_without_quote_flags_keep_existing_errors_exits_and_replay(self):
        for desk in ('booking', 'ticket_operations'):
            for scenario, status in (('confirm', 0), ('boundaries', 1)):
                path = HERE / 'fixtures' / f'{desk}_calculation_inputs_{scenario}.jsonl'
                outputs = []
                for selector, stdin in ((str(path), ''), ('-', path.read_text())):
                    child = self.cli(desk, '--requests', selector, stdin=stdin)
                    self.assertEqual(child.returncode, status, child.stdout + child.stderr)
                    self.assertEqual(child.stderr, '')
                    output = [json.loads(line) for line in child.stdout.splitlines()]
                    self.assertEqual(len(output), len(rows(desk, scenario)))
                    outputs.append(output)
                self.assertEqual(*outputs)
                output = outputs[0]
                if scenario == 'confirm':
                    quote = calculate_booking_quote(rows(desk, scenario)[3]['arguments']['request_text'])
                    self.assertEqual(output[3]['receipt']['reservation']['quote_ref'], quote['quoteHash'])
                    self.assertEqual(quote['evidenceClass'], 'CALCULATION_ONLY')
                    self.assertEqual(output[3]['receipt']['reservation']['amount'], 10001)
                    self.assertTrue(output[4]['receipt']['duplicate'])
                else:
                    errors = [r['error'] for r in output if 'error' in r]
                    self.assertEqual([e['code'] for e in errors if 'code' in e],
                        ['PRIMARY_PRICE_MISMATCH', 'IDEMPOTENCY_CONFLICT',
                         'IDEMPOTENCY_CONFLICT', 'RESERVATION_EXPIRED'])
                    self.assertEqual([e['type'] for e in errors if 'type' in e],
                                     ['InvalidBookingQuoteRecord'] * 5)
                    historical = next(r['receipt'] for r in reversed(output)
                                      if r.get('receipt', {}).get('duplicate'))
                    self.assertEqual(historical['reservation']['phase'], 'CONFIRMED')
                    self.assertEqual(output[-2]['view']['phase'], 'CANCELLED')

    def test_strict_envelopes_stop_before_calculation_with_no_state_change(self):
        for shared, cli in ((False, booking_cli), (True, ticket_operations_cli)):
            name = 'ticket_operations' if shared else 'booking'
            valid = rows(name, 'confirm')[3]
            variants = [valid | {'extra': 1}, valid | {'arguments': None},
                        valid | {'operation': []}, valid | {'arguments': valid['arguments'] | {'amount': 10001}}]
            variants += [valid | {'arguments': {k: v for k, v in valid['arguments'].items() if k != field}}
                         for field in valid['arguments']]
            if shared:
                variants += [{k: v for k, v in valid.items() if k != 'surface'}]
                variants += [valid | {'surface': s} for s in ('resale', 'admission', 'settlement', None)]
            else:
                variants.append(valid | {'surface': 'booking'})
            for row in variants:
                desk = construct(shared)
                before = snap(desk, shared)
                with self.subTest(shared=shared, row=row), \
                        patch('booking_session.calculate_booking_quote') as calc:
                    with self.assertRaises(FixtureError):
                        cli.dispatch_request(desk, row)
                    calc.assert_not_called()
                    self.assertEqual(snap(desk, shared), before)
                    output = io.StringIO()
                    with redirect_stdout(output):
                        status = cli.run_requests(desk, [json.dumps(row), json.dumps(valid)])
                    self.assertEqual(status, 2)
                    self.assertEqual(len(output.getvalue().splitlines()), 1)
                    calc.assert_not_called()
                    self.assertEqual(snap(desk, shared), before)

    def test_missing_clock_stops_but_source_refusal_continues_and_key_is_reusable(self):
        for name in ('booking', 'ticket_operations'):
            valid = rows(name, 'confirm')[3]
            # Shared fixture sets the FSM clock, but no session clock is inferred.
            child = self.cli(name, '--requests', '-', stdin=json.dumps(valid) + '\n' + json.dumps(valid))
            self.assertEqual(child.returncode, 2, child.stdout + child.stderr)
            output = list(map(json.loads, child.stdout.splitlines()))
            self.assertEqual(len(output), 1)
            self.assertEqual(output[0]['error']['type'], 'BookingInputError')
            prefix = rows(name, 'confirm')[:3]
            for bad in (None, 1, {}, '{', json.dumps(request() | {'discounts': [{}]})):
                bad_row = valid | {'arguments': valid['arguments'] | {'request_text': bad}}
                transcript = prefix + [bad_row, valid, valid]
                child = self.cli(name, '--requests', '-',
                                 stdin='\n'.join(map(json.dumps, transcript)))
                self.assertEqual(child.returncode, 1, child.stdout + child.stderr)
                output = list(map(json.loads, child.stdout.splitlines()))
                self.assertEqual(len(output), len(transcript))
                self.assertEqual(output[3]['error']['type'], 'InvalidBookingQuoteRecord')
                self.assertFalse(output[4]['receipt']['duplicate'])
                self.assertTrue(output[5]['receipt']['duplicate'])

    def test_cli_does_not_load_sources_without_quote_flags(self):
        for shared, cli in ((False, booking_cli), (True, ticket_operations_cli)):
            name = 'ticket_operations' if shared else 'booking'
            argv = ['--requests', str(HERE / 'fixtures' / f'{name}_calculation_inputs_confirm.jsonl')]
            if shared:
                argv += ['--fixture', str(FIXTURE)]
            with patch.object(cli, 'BookingQuoteAdapter', side_effect=AssertionError('adapter constructed')), \
                    patch.object(CalculatedBookingQuoteSource, '__init__',
                                 side_effect=AssertionError('source constructed')), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(argv), 0)


if __name__ == '__main__':
    unittest.main()
