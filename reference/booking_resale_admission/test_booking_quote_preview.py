"""Source-informed preview integration gaps; calculator and FSM controls are reused."""

import json
import unittest
from unittest.mock import patch

from booking_quote_source import BookingQuoteSourceError, InvalidBookingQuoteRecord
from booking_session import BookingInputError, BookingSession
from calculated_booking_quote_source import calculate_booking_quote
from reservation_fsm import ReservationMachine
from test_booking_calculation_inputs import calculated
from test_booking_quote_adapter import build, outcome
from test_booking_session import snapshot
from test_calculated_booking_quote_source import invalid_texts, request


class NoReservationAccess:
    def __getattribute__(self, name):
        raise AssertionError('preview accessed reservation machine: ' + name)


class BookingQuotePreviewTests(unittest.TestCase):
    def test_exact_single_calculation_unchanged_return_without_machine_clock_or_confirmation(self):
        session = BookingSession(NoReservationAccess())
        text = json.dumps(request())
        opaque = {'complete': object()}
        with patch('booking_session.calculate_booking_quote', return_value=opaque) as calc, \
                patch.object(session, '_require_clock', side_effect=AssertionError('clock accessed')), \
                patch.object(session, 'confirm', side_effect=AssertionError('confirmed')), \
                patch.object(session, 'confirm_calculated_quote', side_effect=AssertionError('confirmed')):
            self.assertIs(session.preview_calculated_quote(text), opaque)
            calc.assert_called_once_with(text)
        self.assertFalse(session._clock_initialized)

    def test_complete_quote_exact_atoms_hash_label_and_format_equivalence(self):
        session = BookingSession(NoReservationAccess())
        values = [request(str(v)) for v in (1, 10001, 10**12)]
        values.append(request() | {'orderVersion': 2**32-1, 'expiresAt': 2**53-1})
        for value in values:
            expected = calculate_booking_quote(json.dumps(value))
            for text in (json.dumps(value), json.dumps(value, indent=2, sort_keys=True)):
                with self.subTest(amount=value['lines'][0]['gross']['atoms']):
                    quote = session.preview_calculated_quote(text)
                    self.assertEqual(quote, expected)
                    self.assertEqual(quote['evidenceClass'], 'CALCULATION_ONLY')
                    self.assertEqual(set(quote), {'schemaVersion', 'evidenceClass', 'request',
                                                'asset', 'lines', 'totals', 'quoteHash'})
                    for amounts in (quote['totals'], quote['lines'][0]):
                        for field in ('grossAtoms', 'discountAtoms', 'payableAtoms'):
                            self.assertIs(type(amounts[field]), str)
                    self.assertEqual(quote['totals']['payableAtoms'], value['lines'][0]['gross']['atoms'])

    def test_all_calculator_refusals_leave_state_clock_and_future_confirmation_unchanged(self):
        machine, session = build()
        control_machine, control = build()
        before = snapshot(machine)
        untouched = BookingSession(NoReservationAccess())
        for text in [*invalid_texts(), None, True, 1, b'{}', [], {}]:
            with self.subTest(text=repr(text)[:80]), \
                    patch.object(session, 'confirm', side_effect=AssertionError('confirmed')):
                for target in (session, untouched):
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        target.preview_calculated_quote(text)
                self.assertEqual(snapshot(machine), before)
                self.assertTrue(session._clock_initialized)
                self.assertFalse(untouched._clock_initialized)
        actual = calculated(session)
        self.assertFalse(actual['duplicate'])
        self.assertEqual(actual, calculated(control))
        self.assertEqual(snapshot(machine), snapshot(control_machine))

    def test_detached_nested_results_and_failure_after_success_never_use_cached_success(self):
        machine, session = build()
        before = snapshot(machine)
        text = json.dumps(request())
        expected = calculate_booking_quote(text)
        first = session.preview_calculated_quote(text)
        first['request']['lines'][0]['gross']['asset']['reference'] = 'changed'
        first['asset'].clear()
        first['lines'][0]['discounts'].append({'changed': True})
        first['lines'][0]['payableAtoms'] = '0'
        first['totals'].clear()
        first['quoteHash'] = 'changed'
        with patch('booking_session.calculate_booking_quote', wraps=calculate_booking_quote) as calc:
            self.assertEqual(session.preview_calculated_quote(text), expected)
            self.assertEqual(session.preview_calculated_quote(text), expected)
            self.assertEqual(calc.call_count, 2)
        for error in (InvalidBookingQuoteRecord('refusal'), BookingQuoteSourceError('source'),
                      RuntimeError('unexpected')):
            with patch('booking_session.calculate_booking_quote', side_effect=error) as calc:
                with self.assertRaises(BookingQuoteSourceError) as caught:
                    session.preview_calculated_quote(text)
                if isinstance(error, BookingQuoteSourceError):
                    self.assertIs(caught.exception, error)
                else:
                    self.assertEqual(str(caught.exception), 'booking quote fetch failed')
                    self.assertIs(caught.exception.__cause__, error)
                calc.assert_called_once_with(text)
            self.assertEqual(snapshot(machine), before)
        receipt = calculated(session, text)
        self.assertEqual(receipt['reservation']['amount'], int(expected['totals']['payableAtoms']))
        self.assertEqual(receipt['reservation']['quote_ref'], expected['quoteHash'])
        self.assertFalse(receipt['duplicate'])

    def test_preview_does_not_initialize_clock_or_validate_reservation_currentness(self):
        machine = ReservationMachine()
        session = BookingSession(machine)
        before = snapshot(machine)
        value = request() | {'orderId': 'unrelated', 'expiresAt': 1,
                             'scope': {'issuerId': 'x', 'eventId': 'y', 'performanceId': 'z'}}
        text = json.dumps(value)
        self.assertEqual(session.preview_calculated_quote(text), calculate_booking_quote(text))
        self.assertFalse(session._clock_initialized)
        with self.assertRaises(BookingInputError):
            calculated(session, text)
        self.assertEqual(snapshot(machine), before)

    def test_explicit_confirmation_price_expiry_conflicts_and_historical_replay_match_no_preview(self):
        for amount, expired in (('10001', False), ('10000', False), ('10001', True)):
            machine, session = build()
            control_machine, control = build()
            if expired:
                for side in (session, control):
                    side.set_clock('clock', now_ms=1900000, idempotency_key='expiry')
            text = json.dumps(request(amount))
            before = snapshot(machine)
            quote = session.preview_calculated_quote(text)
            self.assertEqual(snapshot(machine), before)
            for _ in range(2):
                actual = outcome(lambda: calculated(session, text))
                self.assertEqual(actual, outcome(lambda: calculated(control, text)))
                self.assertEqual(snapshot(machine), snapshot(control_machine))
            if expired or amount == '10000':
                self.assertEqual(actual, {'error': 'RESERVATION_EXPIRED' if expired
                                         else 'PRIMARY_PRICE_MISMATCH'})
                continue
            self.assertEqual(actual['reservation']['amount'], int(quote['totals']['payableAtoms']))
            self.assertEqual(actual['reservation']['quote_ref'], quote['quoteHash'])
            changed = json.dumps(request() | {'orderVersion': 2})
            session.preview_calculated_quote(changed)
            for side in (session, control):
                self.assertEqual(outcome(lambda: calculated(side, changed)), {'error': 'IDEMPOTENCY_CONFLICT'})
                side.cancel('reserve-1', idempotency_key='cancel')
                side.set_clock('clock', now_ms=1900000, idempotency_key='later')
            session.preview_calculated_quote(text)
            replay = calculated(session, text)
            self.assertEqual(replay, calculated(control, text))
            self.assertTrue(replay['duplicate'])
            self.assertEqual(replay['reservation']['phase'], 'CONFIRMED')
            self.assertEqual(session.view('reserve-1')['phase'], 'CANCELLED')
            self.assertEqual(snapshot(machine), snapshot(control_machine))


if __name__ == '__main__':
    unittest.main()
