"""Source-informed tests of local extraction, not settlement arithmetic."""

from copy import deepcopy
import unittest
from unittest.mock import Mock

import admission_fixture  # Installs the existing sibling settlement reference path.
from settlement_fsm import SettlementError
from settlement_input_adapter import (
    InvalidSettlementInputRecord, SettlementInputAdapter, SettlementInputSourceError,
)


class SettlementInputAdapterTests(unittest.TestCase):
    def graph(self, kind):
        self.source, self.other, self.machine = Mock(), Mock(), Mock()
        self.record = dict(amount=10001, currency='KRW', order_id='order', extra='allowed')
        self.record['reservation_id' if kind == 'booking' else 'listing_id'] = 'source'
        self.source.view.return_value = self.record
        sources = dict(booking_source=self.source, resale_source=self.other)
        if kind == 'resale':
            sources = dict(booking_source=self.other, resale_source=self.source)
        self.adapter = SettlementInputAdapter(self.machine, **sources)
        self.assertEqual(self.source.mock_calls + self.other.mock_calls + self.machine.mock_calls, [])
        self.args = dict(source_kind=kind, source_id='source', settlement_id=object(),
                         idempotency_key=object(), trade_id=object(), debtor_role=object(), policy=object())

    def test_one_selected_read_and_one_target_call_with_opaque_arguments_and_result(self):
        for kind in ('booking', 'resale'):
            for amount in (1, 10001, 10**12):
                self.graph(kind)
                self.record['amount'] = amount
                before = deepcopy(self.record)
                receipt = object()
                self.machine.initiate.return_value = receipt
                self.assertIs(self.adapter.apply(**self.args), receipt)
                self.source.view.assert_called_once_with('source')
                self.other.assert_not_called()
                self.assertEqual(self.other.mock_calls, [])
                target = {k:v for k,v in self.args.items() if k not in ('source_kind', 'source_id', 'settlement_id')}
                self.machine.initiate.assert_called_once_with(
                    self.args['settlement_id'], **target, gross=amount, currency='KRW')
                self.assertEqual(len(self.machine.mock_calls), 1)
                self.assertEqual(self.record, before)

    def test_bad_selection_identity_and_unconfigured_sources_precede_target(self):
        for kind in ('booking', 'resale'):
            self.graph(kind)
            for bad in (None, [], 'other', 1):
                with self.assertRaises(InvalidSettlementInputRecord):
                    self.adapter.apply(**(self.args | dict(source_kind=bad)))
            for bad in (None, [], True, 1, '', ' source', 'x'*101):
                with self.assertRaises(InvalidSettlementInputRecord):
                    self.adapter.apply(**(self.args | dict(source_id=bad)))
            self.assertEqual(self.source.mock_calls + self.other.mock_calls + self.machine.mock_calls, [])
            with self.assertRaises(SettlementInputSourceError):
                SettlementInputAdapter(self.machine).apply(**self.args)
            self.assertEqual(self.machine.mock_calls, [])

    def test_malformed_records_never_delegate_and_explicit_repair_reads_again(self):
        for kind in ('booking', 'resale'):
            self.graph(kind)
            field = 'reservation_id' if kind == 'booking' else 'listing_id'
            fields = (field, 'amount', 'currency') + (('order_id',) if kind == 'booking' else ())
            valid = dict(self.record)
            bad = [None, [], '', 0, True, *[{k:v for k,v in valid.items() if k != f} for f in fields]]
            for name in (field,) + (('order_id',) if kind == 'booking' else ()):
                bad += [valid | {name:v} for v in (None, '', ' space', 'x'*101, 1, True, [])]
            bad += [valid | {field:'mismatched'}]
            bad += [valid | dict(amount=v) for v in (None, True, False, 0, -1, 10**12+1, 1.0, '1', [])]
            bad += [valid | dict(currency=v) for v in (None, True, 1, '', 'krw', 'USD', 'KRW ', [])]
            for record in bad:
                with self.subTest(kind=kind, record=record):
                    self.source.reset_mock()
                    self.source.view.return_value = record
                    with self.assertRaises(InvalidSettlementInputRecord):
                        self.adapter.apply(**self.args)
                    self.source.view.assert_called_once_with('source')
                    self.assertEqual(self.machine.mock_calls + self.other.mock_calls, [])
            self.source.view.return_value = valid
            self.adapter.apply(**self.args)
            self.assertEqual(self.source.view.call_count, 2)
            self.assertEqual(self.machine.initiate.call_count, 1)

    def test_source_exceptions_wrap_once_target_errors_propagate_with_identity(self):
        for kind in ('booking', 'resale'):
            for error in (RuntimeError('synthetic'), TimeoutError('immediate'),
                          SettlementInputSourceError('already local')):
                self.graph(kind)
                self.source.view.side_effect = error
                with self.assertRaises(SettlementInputSourceError) as caught:
                    self.adapter.apply(**self.args)
                if isinstance(error, SettlementInputSourceError):
                    self.assertIs(caught.exception, error)
                else:
                    self.assertIs(caught.exception.__cause__, error)
                self.source.view.assert_called_once_with('source')
                self.assertEqual(self.machine.mock_calls + self.other.mock_calls, [])
            # Even a target error with the local exception type is not wrapped.
            for error in (SettlementError('OPAQUE'), RuntimeError('target'),
                          InvalidSettlementInputRecord('target-local')):
                self.graph(kind)
                self.machine.initiate.side_effect = error
                with self.assertRaises(type(error)) as caught:
                    self.adapter.apply(**self.args)
                self.assertIs(caught.exception, error)
                self.source.view.assert_called_once_with('source')
                self.assertEqual(self.machine.initiate.call_count, 1)


if __name__ == '__main__':
    unittest.main()
