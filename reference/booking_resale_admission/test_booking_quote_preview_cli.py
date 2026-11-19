"""Both JSONL preview surfaces: strict envelopes, shared isolation and explicit confirmation."""

from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from admission_fixture import FixtureError
import booking_cli
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_source import InvalidBookingQuoteRecord
from calculated_booking_quote_source import calculate_booking_quote
from fake_cancel_acceptance_source import FakeCancelAcceptanceSource
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from fake_resale_payment_source import FakeResalePaymentSource
from fake_statement_source import FakeStatementSource
from test_booking_calculation_inputs_cli import booking, construct, snap
import test_calculated_booking_quote_cli as harness
from test_calculated_booking_quote_cli import outcome
from test_calculated_booking_quote_source import HERE, invalid_texts, request, source_for
from test_reservation_fsm import assert_not_final
from test_ticket_operations_session import fixture
import ticket_operations_cli
from ticket_operations_session import TicketOperationsSession


def preview(text=None, shared=False):
    return dict(operation='preview_calculated_quote',
                arguments={'request_text': json.dumps(request()) if text is None else text},
                **({'surface': 'booking'} if shared else {}))


def rows(desk, scenario):
    return list(map(json.loads, (HERE / 'fixtures' /
                    f'{desk}_quote_preview_{scenario}.jsonl').read_text().splitlines()))


class BookingQuotePreviewCliTests(unittest.TestCase):
    def cli(self, desk, *args, stdin=''):
        return harness.CalculatedBookingQuoteCliTests.cli(self, desk, *args, stdin=stdin)

    def test_complete_calculator_output_and_rejection_corpus_on_both_dispatchers(self):
        for shared, cli in ((False, booking_cli), (True, ticket_operations_cli)):
            desk = construct(shared)
            before = snap(desk, shared)
            for amount in ('1', '10001', '1000000000000'):
                for indent in (None, 2):
                    text = json.dumps(request(amount), indent=indent)
                    self.assertEqual(cli.dispatch_request(desk, preview(text, shared)),
                                     dict(operation='preview_calculated_quote', quote=calculate_booking_quote(text),
                                          **({'surface': 'booking'} if shared else {})))
            for text in [*invalid_texts(), None, True, 1, [], {}]:
                row = preview(shared=shared)
                row['arguments']['request_text'] = text
                with self.subTest(shared=shared, text=repr(text)[:60]):
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        cli.dispatch_request(desk, row)
                    self.assertEqual(snap(desk, shared), before)
            self.assertFalse(booking(desk, shared)._clock_initialized)

    def test_shared_machines_journals_clocks_and_all_configured_sources_unchanged(self):
        sources = [cls(recordings={}) for cls in (FakeResaleOfferSource, FakePresentationSource,
                   FakeResalePaymentSource, FakeCancelAcceptanceSource, FakeStatementSource)]
        desk = TicketOperationsSession(setup=fixture()['setup'], offer_source=sources[0],
            presentation_source=sources[1], payment_source=sources[2],
            cancel_acceptance_source=sources[3], statement_source=sources[4])
        quote_source = source_for()
        sources.append(quote_source)
        adapter = BookingQuoteAdapter(desk.booking, quote_source)
        before, calls = snap(desk, True), [s.calls for s in sources]
        clock = desk.booking._clock_initialized
        with ExitStack() as guards:
            for source in sources:
                guards.enter_context(patch.object(source, 'fetch', side_effect=AssertionError('source fetched')))
            for name in ('confirm', 'confirm_calculated_quote', '_require_clock'):
                guards.enter_context(patch.object(desk.booking, name, side_effect=AssertionError(name)))
            first = ticket_operations_cli.dispatch_request(desk, preview(shared=True), quote_adapter=adapter)
            first['quote']['request'].clear()
            first['quote']['asset'].clear()
            first['quote']['totals'].clear()
            first['quote']['lines'].clear()
            second = ticket_operations_cli.dispatch_request(desk, preview(shared=True), quote_adapter=adapter)
            self.assertEqual(second['quote'], calculate_booking_quote(json.dumps(request())))
            with self.assertRaises(InvalidBookingQuoteRecord):
                ticket_operations_cli.dispatch_request(desk, preview('{', True), quote_adapter=adapter)
        self.assertEqual(snap(desk, True), before)
        self.assertEqual([s.calls for s in sources], calls)
        self.assertEqual(desk.booking._clock_initialized, clock)

    def test_fixture_histories_match_no_preview_control_after_every_step(self):
        for name, cli in (('booking', booking_cli), ('ticket_operations', ticket_operations_cli)):
            shared = name == 'ticket_operations'
            for scenario in ('confirm', 'boundaries'):
                desk, control = construct(shared), construct(shared)
                initial = snap(desk, shared)
                for row in rows(name, scenario):
                    before = snap(desk, shared)
                    clock = booking(desk, shared)._clock_initialized
                    actual = outcome(lambda: cli.dispatch_request(desk, row))
                    if row['operation'] == 'preview_calculated_quote':
                        def direct():
                            return dict(operation=row['operation'],
                                        quote=calculate_booking_quote(row['arguments']['request_text']),
                                        **({'surface': 'booking'} if shared else {}))
                        self.assertEqual(actual, outcome(direct))
                        self.assertEqual(snap(desk, shared), before)
                        self.assertEqual(booking(desk, shared)._clock_initialized, clock)
                    else:
                        self.assertEqual(actual, outcome(lambda: cli.dispatch_request(control, row)))
                        if isinstance(actual, dict):
                            assert_not_final(self, actual.get('receipt', actual.get('view')))
                    self.assertEqual(snap(desk, shared), snap(control, shared))
                if shared:
                    final = snap(desk, shared)
                    self.assertEqual((initial[0], initial[2:]), (final[0], final[2:]))
                reservation = booking(desk, shared).view('desk-reserve-1' if shared else 'reserve-1')
                for field in ('payment_ref', 'settlement_id', 'issuance_id', 'right'):
                    self.assertIsNone(reservation[field])

    def test_file_stdin_parity_without_source_flags_and_preview_then_explicit_confirmation(self):
        for name in ('booking', 'ticket_operations'):
            for scenario, status in (('confirm', 0), ('boundaries', 1)):
                path = HERE / 'fixtures' / f'{name}_quote_preview_{scenario}.jsonl'
                outputs = []
                for selector, stdin in ((str(path), ''), ('-', path.read_text())):
                    child = self.cli(name, '--requests', selector, stdin=stdin)
                    self.assertEqual(child.returncode, status, child.stdout + child.stderr)
                    self.assertEqual(child.stderr, '')
                    output = list(map(json.loads, child.stdout.splitlines()))
                    self.assertEqual(len(output), len(rows(name, scenario)))
                    outputs.append(output)
                self.assertEqual(*outputs)
                output = outputs[0]
                expected = calculate_booking_quote(rows(name, scenario)[0]['arguments']['request_text'])
                self.assertEqual(output[0]['quote'], expected)
                receipts = [r['receipt'] for r in output if r.get('receipt', {}).get('reservation', {}).get('phase') == 'CONFIRMED']
                self.assertEqual(receipts[0]['reservation']['quote_ref'], expected['quoteHash'])
                self.assertEqual(receipts[0]['reservation']['amount'], int(expected['totals']['payableAtoms']))
                self.assertFalse(receipts[0]['duplicate'])
                self.assertTrue(receipts[-1]['duplicate'])
                if scenario == 'boundaries':
                    codes = [r['error']['code'] for r in output if 'code' in r.get('error', {})]
                    self.assertEqual(codes, ['PRIMARY_PRICE_MISMATCH', 'IDEMPOTENCY_CONFLICT',
                                            'IDEMPOTENCY_CONFLICT', 'RESERVATION_EXPIRED'])
                    self.assertEqual(receipts[-1]['reservation']['phase'], 'CONFIRMED')
                    self.assertEqual(output[-2]['view']['phase'], 'CANCELLED')

    def test_strict_envelopes_stop_before_calculation_and_preserve_state(self):
        for shared, cli in ((False, booking_cli), (True, ticket_operations_cli)):
            valid = preview(shared=shared)
            variants = [valid | {'extra': 1}, valid | {'operation': []}]
            variants += [valid | {'arguments': value} for value in (None, [], {}, '')]
            variants += [{k: v for k, v in valid.items() if k != field} for field in valid]
            variants += [valid | {'arguments': valid['arguments'] | {field: 'forbidden'}}
                         for field in ('reservation_id', 'order_id', 'idempotency_key', 'now_ms', 'quoteHash', 'amount')]
            variants += ([valid | {'surface': s} for s in ('resale', 'admission', 'settlement', None)]
                         if shared else [valid | {'surface': 'booking'}])
            for row in variants:
                desk = construct(shared)
                before = snap(desk, shared)
                with self.subTest(shared=shared, row=row), patch('booking_session.calculate_booking_quote') as calc:
                    with self.assertRaises(FixtureError):
                        cli.dispatch_request(desk, row)
                    output = io.StringIO()
                    with redirect_stdout(output):
                        self.assertEqual(cli.run_requests(desk, [json.dumps(row), json.dumps(valid)]), 2)
                    self.assertEqual(len(output.getvalue().splitlines()), 1)
                    calc.assert_not_called()
                    self.assertEqual(snap(desk, shared), before)

    def test_malformed_file_and_stdin_stop_but_bad_inner_text_continues_without_clock(self):
        for name in ('booking', 'ticket_operations'):
            valid = preview(shared=name == 'ticket_operations')
            encoded = json.dumps(valid)
            bad_outer = ['{', '[]', encoded[:-1] + ',"operation":"preview_calculated_quote"}',
                         encoded.replace('"request_text":', '"request_text": "{}", "request_text":')]
            for bad in bad_outer:
                transcript = bad + '\n' + encoded + '\n'
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / 'malformed.jsonl'
                    path.write_text(transcript)
                    for selector, stdin in ((str(path), ''), ('-', transcript)):
                        child = self.cli(name, '--requests', selector, stdin=stdin)
                        self.assertEqual(child.returncode, 2, child.stdout + child.stderr)
                        output = list(map(json.loads, child.stdout.splitlines()))
                        self.assertEqual(len(output), 1)
                        self.assertEqual(output[0]['error']['type'], 'FixtureError')
            for bad in (None, True, 1, {}, '{', '{"a":1,"a":2}'):
                row = deepcopy(valid)
                row['arguments']['request_text'] = bad
                child = self.cli(name, '--requests', '-', stdin=json.dumps(row) + '\n' + encoded)
                self.assertEqual(child.returncode, 1, child.stdout + child.stderr)
                output = list(map(json.loads, child.stdout.splitlines()))
                self.assertEqual(len(output), 2)
                self.assertEqual(output[0]['error']['type'], 'InvalidBookingQuoteRecord')
                self.assertEqual(output[1]['quote'], calculate_booking_quote(valid['arguments']['request_text']))


if __name__ == '__main__':
    unittest.main()
