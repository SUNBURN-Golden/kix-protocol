"""Source-informed request-time composition gaps; source/adapter controls are retained."""

import json
import unittest
from unittest.mock import patch

from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_source import BookingQuoteSourceError, InvalidBookingQuoteRecord
from booking_session import BookingInputError, BookingSession
from calculated_booking_quote_source import calculate_booking_quote
from reservation_fsm import ReservationError, ReservationMachine
from test_booking_quote_adapter import build, confirm, outcome
from test_booking_session import requests, snapshot
from test_calculated_booking_quote_source import invalid_texts, request, source_for
from test_reservation_fsm import assert_not_final


def calculated(session, text=None, **changes):
    return session.confirm_calculated_quote(**(dict(
        request_text=json.dumps(request()) if text is None else text,
        reservation_id='reserve-1', order_id='order-1', idempotency_key='confirm-1') | changes))


class BookingCalculationInputsTests(unittest.TestCase):
    def test_calculate_once_delegate_once_return_identity_and_preserve_session_errors(self):
        _, session = build()
        text = json.dumps(request())
        quote = calculate_booking_quote(text)
        receipt = {'opaque': object()}
        for error in (None, BookingInputError('clock'), ReservationError('TEST'), RuntimeError('internal')):
            with patch('booking_session.calculate_booking_quote', wraps=calculate_booking_quote) as calc, \
                    patch.object(session, 'confirm', return_value=receipt, side_effect=error) as delegate:
                if error is None:
                    self.assertIs(calculated(session, text), receipt)
                else:
                    with self.assertRaises(type(error)) as caught:
                        calculated(session, text)
                    self.assertIs(caught.exception, error)
                calc.assert_called_once_with(text)
                delegate.assert_called_once_with('order-1', reservation_id='reserve-1', amount=10001,
                    quote_ref=quote['quoteHash'], idempotency_key='confirm-1')

    def test_rejection_corpus_never_confirms_mutates_or_binds_key(self):
        for text in [*invalid_texts(), None, True, 1, b'{}', [], {}]:
            with self.subTest(text=repr(text)[:90]):
                machine, session = build()
                before = snapshot(machine)
                with patch.object(session, 'confirm', wraps=session.confirm) as delegate:
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        calculated(session, request_text=text)
                    delegate.assert_not_called()
                self.assertEqual(snapshot(machine), before)
                self.assertFalse(calculated(session)['duplicate'])

    def test_invalid_identifiers_never_calculate_or_confirm(self):
        machine, session = build()
        before = snapshot(machine)
        for field in ('reservation_id', 'order_id', 'idempotency_key'):
            for value in (None, True, 1, '', ' ', [], {}):
                with self.subTest(field=field, value=value), \
                        patch('booking_session.calculate_booking_quote') as calc, \
                        patch.object(session, 'confirm') as delegate:
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        calculated(session, **{field: value})
                    calc.assert_not_called()
                    delegate.assert_not_called()
                self.assertEqual(snapshot(machine), before)

    def test_calculation_failure_after_success_has_no_cached_fallback(self):
        machine, session = build()
        first = calculated(session)
        before = snapshot(machine)
        for error in (InvalidBookingQuoteRecord('refusal'), BookingQuoteSourceError('source'),
                      RuntimeError('unexpected')):
            with patch('booking_session.calculate_booking_quote', side_effect=error) as calc, \
                    patch.object(session, 'confirm', wraps=session.confirm) as delegate:
                with self.assertRaises(BookingQuoteSourceError) as caught:
                    calculated(session)
                if isinstance(error, BookingQuoteSourceError):
                    self.assertIs(caught.exception, error)
                else:
                    self.assertEqual(str(caught.exception), 'booking quote fetch failed')
                    self.assertIs(caught.exception.__cause__, error)
                calc.assert_called_once()
                delegate.assert_not_called()
                self.assertEqual(snapshot(machine), before)
        replay = calculated(session)
        self.assertTrue(replay['duplicate'])
        self.assertEqual(replay['reservation'], first['reservation'])

    def test_adapter_parity_for_replay_changed_inputs_binding_clock_and_cancel(self):
        machine, session = build()
        control_machine, control = build()
        cases = [({}, None), ({'text': json.dumps(request(), indent=2)}, None),
                 ({'text': json.dumps(request() | {'orderVersion': 2})}, 'IDEMPOTENCY_CONFLICT'),
                 ({'text': json.dumps(request('10000'))}, 'IDEMPOTENCY_CONFLICT'),
                 ({'order_id': 'other'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'reservation_id': 'other'}, 'IDEMPOTENCY_CONFLICT'),
                 ({'text': json.dumps(request() | {'orderVersion': 2}),
                   'idempotency_key': 'changed-hash'}, 'ORDER_BINDING_CONFLICT'),
                 ({'idempotency_key': 'new-key'}, 'ILLEGAL_TRANSITION')]
        first = None
        with patch('booking_session.calculate_booking_quote', wraps=calculate_booking_quote) as calc, \
                patch.object(session, 'confirm', wraps=session.confirm) as delegate:
            for changes, code in cases:
                changes = dict(changes)
                text = changes.pop('text', json.dumps(request()))
                actual = outcome(lambda: calculated(session, text, **changes))
                source = source_for(text, reservation=changes.get('reservation_id', 'reserve-1'))
                expected = outcome(lambda: confirm(BookingQuoteAdapter(control, source), **changes))
                self.assertEqual(actual, expected)
                self.assertEqual(snapshot(machine), snapshot(control_machine))
                if code:
                    self.assertEqual(actual, {'error': code})
                else:
                    first = first or actual
                    assert_not_final(self, actual)
            self.assertEqual(calc.call_count, len(cases))
            self.assertEqual(delegate.call_count, len(cases))
        for side in (session, control):
            side.set_clock('clock', now_ms=1900000, idempotency_key='advance')
            side.cancel('reserve-1', idempotency_key='cancel')
        replay = calculated(session)
        self.assertEqual(replay, confirm(BookingQuoteAdapter(control, source_for())))
        self.assertEqual(replay['reservation'], first['reservation'])
        self.assertEqual(session.view('reserve-1')['phase'], 'CANCELLED')
        self.assertEqual(snapshot(machine), snapshot(control_machine))

    def test_price_expiry_and_amount_endpoints_match_adapter_with_retained_refusals(self):
        for amount, expired in (('1', False), ('10001', False), ('1000000000000', False),
                                ('10000', False), ('10001', True)):
            machine, session = build()
            control_machine, control = build()
            # Endpoint equality uses explicit caller show pricing, never a price default.
            if amount in ('1', '1000000000000'):
                machine, control_machine = ReservationMachine(), ReservationMachine()
                session, control = BookingSession(machine), BookingSession(control_machine)
                for side in (session, control):
                    for row in requests()[:3]:
                        args = dict(row['arguments'])
                        if row['operation'] == 'register_show':
                            args.update(primary_price=int(amount), resale_cap=int(amount))
                        getattr(side, row['operation'])(**args)
            if expired:
                for side in (session, control):
                    side.set_clock('clock', now_ms=1900000, idempotency_key='expiry')
            text = json.dumps(request(amount))
            adapter = BookingQuoteAdapter(control, source_for(text))
            for _ in range(2):
                actual = outcome(lambda: calculated(session, text))
                self.assertEqual(actual, outcome(lambda: confirm(adapter)))
                if expired:
                    self.assertEqual(actual, {'error': 'RESERVATION_EXPIRED'})
                elif amount == '10000':
                    self.assertEqual(actual, {'error': 'PRIMARY_PRICE_MISMATCH'})
                else:
                    self.assertEqual(actual['reservation']['amount'], int(amount))
                self.assertEqual(snapshot(machine), snapshot(control_machine))

    def test_no_implicit_clock_and_calculation_metadata_is_only_hash_bound(self):
        machine = ReservationMachine()
        session = BookingSession(machine)
        before = snapshot(machine)
        with self.assertRaises(BookingInputError):
            calculated(session)
        self.assertEqual(snapshot(machine), before)
        machine, session = build()
        value = request() | {'orderId': 'unrelated', 'expiresAt': 1,
                             'scope': {'issuerId': 'x', 'eventId': 'y', 'performanceId': 'z'}}
        receipt = calculated(session, json.dumps(value))
        self.assertEqual(receipt['reservation']['phase'], 'CONFIRMED')
        assert_not_final(self, receipt)
        for field in ('payment_ref', 'settlement_id', 'issuance_id', 'right'):
            self.assertIsNone(receipt['reservation'][field])


if __name__ == '__main__':
    unittest.main()
