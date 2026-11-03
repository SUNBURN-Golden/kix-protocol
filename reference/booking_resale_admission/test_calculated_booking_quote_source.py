"""Source-informed bridge tests; direct calculator control runs in isolation."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_source import BookingQuoteSourceError, InvalidBookingQuoteRecord
from calculated_booking_quote_fixture import load_fixture
from calculated_booking_quote_source import CalculatedBookingQuoteSource, calculate_booking_quote
from test_booking_quote_adapter import build, confirm, outcome
from test_booking_session import snapshot

HERE = Path(__file__).resolve().parent
QUOTES = HERE / 'fixtures/calculated_booking_quotes.json'


def request(amount='10001'):
    value = json.loads(json.loads(QUOTES.read_text())['calculations'][0]['request_text'])
    value['lines'][0]['gross']['atoms'] = amount
    return value


def source_for(text=None, reservation='reserve-1'):
    return CalculatedBookingQuoteSource(requests={'record-1': {
        'reservation_id': reservation,
        'request_text': json.dumps(request()) if text is None else text}})


def invalid_texts():
    valid = request()
    values = [None, True, 1, [], {}, valid | {'extra': 1}]
    values += [{k: v for k, v in valid.items() if k != key} for key in valid]
    for field in ('lines', 'discounts', 'scope', 'orderVersion', 'expiresAt', 'schemaVersion'):
        values += [valid | {field: v} for v in (None, True, '1', {}, 1.5)]
    values += [valid | {'lines': []}]
    two = deepcopy(valid)
    two['lines'].append(deepcopy(two['lines'][0]) | {'lineId': 'L2', 'inventoryId': 'inv-2'})
    values.append(two)
    for field, value in (('namespace', 'other'), ('reference', 'USD'), ('decimals', 2),
                         ('maxAtoms', str(2**128-2)), ('decimals', False)):
        variant = deepcopy(valid)
        variant['lines'][0]['gross']['asset'][field] = value
        values.append(variant)
    for atom in ('0', '1000000000001', str(2**53+1), str(2**128-1), str(2**128),
                 '01', '-1', '1e3', '1.0', '١', True, None, 1, 1.0):
        values.append(request(atom))
    for kind in ('FIXED', 'BPS'):
        values.append(valid | {'discounts': [dict(ruleId='zero', bearerRef='caller', kind=kind,
                      value='0', eligibleLineIds=['L1'], capAtoms=None)]})
    values += [valid | {'orderVersion': v} for v in (0, 2**32, 2**53)]
    values += [valid | {'expiresAt': v} for v in (0, -1, 2**53)]
    texts = [json.dumps(v) for v in values]
    texts += ['{', 'NaN', 'Infinity', '-Infinity', '{"a":1,"a":2}',
              '[' * 66 + '0' + ']' * 66, ' ' * (256 * 1024 + 1), '\ud800',
              json.dumps(valid).replace('"orderVersion": 1', '"orderVersion": -0'),
              json.dumps(valid).replace('"orderVersion": 1', '"orderVersion": 1e0'),
              json.dumps(valid).replace('"orderVersion": 1', '"orderVersion": 1.0'),
              json.dumps(valid).replace('"orderVersion": 1', '"orderVersion": 1e400')]
    return texts


class CalculatedBookingQuoteSourceTests(unittest.TestCase):
    def test_complete_output_matches_direct_unchanged_calculator_and_boundaries(self):
        inputs = [request(str(amount)) for amount in (1, 10001, 10**12)]
        inputs.append(request() | {'orderVersion': 2**32-1, 'expiresAt': 2**53-1})
        env = dict(os.environ)
        # Keep any socket-denial sitecustomize inherited by subprocesses.
        env['PYTHONPATH'] = str(HERE.parent / 'v0.3-rc1') + os.pathsep + env.get('PYTHONPATH', '')
        control = subprocess.run([sys.executable, '-B', '-c',
            'import json,sys; from commerce import build_quote; '
            'print(json.dumps([build_quote(v) for v in json.load(sys.stdin)]))'],
            input=json.dumps(inputs), text=True, capture_output=True, env=env, check=True)
        expected = json.loads(control.stdout)
        for value, quote in zip(inputs, expected):
            text = json.dumps(value)
            self.assertEqual(calculate_booking_quote(text), quote)
            self.assertEqual(quote['evidenceClass'], 'CALCULATION_ONLY')
            source = source_for(text)
            self.assertEqual(source.fetch('record-1'), dict(reservation_id='reserve-1',
                             amount=int(quote['totals']['payableAtoms']), quote_ref=quote['quoteHash']))
        self.assertEqual(inputs[0]['lines'][0]['gross']['atoms'], '1')

    def test_all_source_rejections_do_not_delegate_mutate_or_bind_key(self):
        for text in invalid_texts():
            with self.subTest(text=text[:100]):
                machine, session = build()
                before = snapshot(machine)
                source = source_for(text)
                with patch.object(session, 'confirm', wraps=session.confirm) as delegate:
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        confirm(BookingQuoteAdapter(session, source))
                    delegate.assert_not_called()
                self.assertEqual(snapshot(machine), before)
                self.assertEqual(source.calls, ('record-1',))
                self.assertFalse(confirm(BookingQuoteAdapter(session, source_for()))['duplicate'])
        for text in (None, True, 1, b'\xff', [], {}):
            with self.assertRaises(InvalidBookingQuoteRecord):
                calculate_booking_quote(text)

    def test_storage_results_and_calls_are_detached_and_fetch_recalculates(self):
        entry = {'reservation_id': 'reserve-1', 'request_text': json.dumps(request())}
        caller = {'record-1': entry}
        with patch('calculated_booking_quote_source.calculate_booking_quote',
                   wraps=calculate_booking_quote) as calculate:
            source = CalculatedBookingQuoteSource(requests=caller)
            calculate.assert_not_called()
            old_calls = source.calls
            entry['request_text'] = '{}'
            caller.clear()
            first = source.fetch('record-1')
            first.clear()
            self.assertEqual(source.fetch('record-1')['amount'], 10001)
            self.assertEqual(calculate.call_count, 2)
            self.assertEqual(source.fetch('absent'), None)
            self.assertEqual(calculate.call_count, 2)
        with self.assertRaises(TypeError):
            source.requests['record-1']['request_text'] = '{}'
        with self.assertRaises(TypeError):
            source.requests['other'] = entry
        self.assertEqual(old_calls, ())
        self.assertEqual(source.calls, ('record-1', 'record-1', 'absent'))
        self.assertEqual(source.provenance, 'CALCULATION_ONLY')
        quote = calculate_booking_quote(json.dumps(request()))
        quote['request']['lines'].clear()
        self.assertEqual(len(calculate_booking_quote(json.dumps(request()))['request']['lines']), 1)

    def test_constructor_rejects_invalid_structure_but_calculation_is_lazy(self):
        valid = {'reservation_id': 'reserve-1', 'request_text': '{}'}
        for entries in (None, [], {'': valid}, {True: valid}, {'a': None},
                        {'a': valid | {'extra': 1}}, {'a': {'request_text': '{}'}},
                        {'a': valid | {'reservation_id': None}},
                        {'a': valid | {'request_text': b'{}'}}):
            with self.subTest(entries=entries), self.assertRaises(InvalidBookingQuoteRecord):
                CalculatedBookingQuoteSource(requests=entries)
        source = CalculatedBookingQuoteSource(requests={'a': valid})
        self.assertEqual(source.calls, ())
        with self.assertRaises(InvalidBookingQuoteRecord):
            source.fetch('a')

    def test_receipts_replay_price_expiry_and_historical_result_match_direct_session(self):
        for amount, expired in (('10001', False), ('10000', False), ('10001', True)):
            machine, session = build()
            direct_machine, direct = build()
            if expired:
                for side in (session, direct):
                    side.set_clock('clock', now_ms=1900000, idempotency_key='expiry')
            text = json.dumps(request(amount))
            quote = calculate_booking_quote(text)
            record = dict(reservation_id='reserve-1', amount=int(amount), quote_ref=quote['quoteHash'])
            source = source_for(text)
            adapter = BookingQuoteAdapter(session, source)
            for _ in range(2):
                self.assertEqual(outcome(lambda: confirm(adapter)), outcome(lambda: direct.confirm(
                    'order-1', idempotency_key='confirm-1', **record)))
                self.assertEqual(snapshot(machine), snapshot(direct_machine))
            if amount == '10001' and not expired:
                changed = source_for(json.dumps(request() | {'orderVersion': 2}))
                self.assertEqual(outcome(lambda: confirm(BookingQuoteAdapter(session, changed))),
                                 {'error': 'IDEMPOTENCY_CONFLICT'})
                direct_changed = record | {'quote_ref': calculate_booking_quote(
                    json.dumps(request() | {'orderVersion': 2}))['quoteHash']}
                self.assertEqual(outcome(lambda: direct.confirm('order-1',
                    idempotency_key='confirm-1', **direct_changed)), {'error': 'IDEMPOTENCY_CONFLICT'})
                for side in (session, direct):
                    side.cancel('reserve-1', idempotency_key='cancel')
                self.assertEqual(confirm(adapter), direct.confirm('order-1',
                                 idempotency_key='confirm-1', **record))
                self.assertEqual(snapshot(machine), snapshot(direct_machine))

    def test_invalid_callers_fetch_zero_and_failure_after_success_has_no_fallback(self):
        machine, session = build()
        source = source_for()
        adapter = BookingQuoteAdapter(session, source)
        for field in ('recording_id', 'reservation_id', 'order_id', 'idempotency_key'):
            with self.assertRaises(InvalidBookingQuoteRecord):
                confirm(adapter, **{field: None})
        self.assertEqual(source.calls, ())
        confirm(adapter)
        before = snapshot(machine)
        error = InvalidBookingQuoteRecord('synthetic calculator refusal')
        with patch('calculated_booking_quote_source.calculate_booking_quote', side_effect=error) as calculate, \
                patch.object(session, 'confirm', wraps=session.confirm) as delegate:
            with self.assertRaises(BookingQuoteSourceError) as caught:
                confirm(adapter)
            self.assertIs(caught.exception, error)
            calculate.assert_called_once()
            delegate.assert_not_called()
        self.assertEqual(snapshot(machine), before)
        self.assertTrue(confirm(adapter)['duplicate'])
        self.assertEqual(source.calls, ('record-1',) * 3)

    def test_import_and_lazy_load_preserve_public_modules_and_paths(self):
        code = '''
import sys, types
import calculated_booking_quote_source as source
assert 'commerce' not in sys.modules
before = list(sys.path)
names = ('common', 'canonical_encoding', 'assets', 'execution_contracts', 'commerce')
sentinels = {name: types.ModuleType(name) for name in names}
sys.modules.update(sentinels)
source.calculate_booking_quote(sys.stdin.read())
assert sys.path == before
assert all(sys.modules[name] is value for name, value in sentinels.items())
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], input=json.dumps(request()),
                                text=True, capture_output=True, cwd=HERE)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
