"""Source-informed shared-session parity against separately constructed FSMs."""

from contextlib import ExitStack
import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import admission_fixture  # Installs the existing sibling settlement reference path.
from reservation_fsm import ReservationError
from resale_fsm import ResaleError
from settlement_fsm import SettlementError, SettlementMachine
from settlement_input_adapter import InvalidSettlementInputRecord, SettlementInputSourceError
from test_admission_session import assert_flags
from test_resale_fsm import assert_not_final as resale_flags
from test_reservation_fsm import assert_not_final as booking_flags
from test_ticket_operations_session import direct_call, direct_graph, machines, snapshot
from test_ticket_settlement_controls import settlement_flags
from ticket_operations_cli import dispatch_request
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession, TicketSettlementSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_settlement_inputs_session.json'
SELECTORS = {'initiate_from_booking': ('booking', 'reservation_id', 1),
             'initiate_from_resale': ('resale', 'listing_id', 2)}


def path(name):
    return HERE / f'fixtures/ticket_operations_settlement_inputs_{name}.jsonl'


def rows(name='booking'):
    return [json.loads(line) for line in path(name).read_text().splitlines()]


def initiation(kind='booking', **changes):
    row = next(r for r in rows(kind) if r['operation'] == f'initiate_from_{kind}')
    return row | dict(arguments=row['arguments'] | changes)


def outcome(call):
    try:
        return call()
    except (ReservationError, ResaleError, SettlementError) as error:
        return dict(error=dict(code=error.code))
    except SettlementInputSourceError as error:
        return dict(error=dict(type=type(error).__name__, message=str(error)))


def direct_request(graph, row, value):
    """Use raw source views and target operations, bypassing all desk adapters."""
    op, args = row['operation'], dict(row['arguments'])
    if op in SELECTORS:
        _, field, index = SELECTORS[op]
        identity = args.pop(field)
        try:
            view = graph[index].view(identity)
        except (ReservationError, ResaleError) as error:
            raise SettlementInputSourceError('settlement input view failed') from error
        row = row | dict(operation='initiate', arguments=args | dict(gross=view['amount'],
                                                                   currency=view['currency']))
    elif op in ('commit_recorded_statement', 'observe_recorded_statement'):
        document = json.loads(next(e['recorded_text'] for e in value['statements']
            if (e['settlement_id'], e['movement_id']) == (args['settlement_id'], args['movement_id'])))
        row = row | dict(operation='commit' if op == 'commit_recorded_statement' else 'observe_statement',
                         arguments=document | dict(idempotency_key=args['idempotency_key']))
    result = direct_call(graph, row, value)
    return result | dict(operation=op)


class TicketSettlementInputsTests(unittest.TestCase):
    def graph(self):
        self.value = json.loads(FIXTURE.read_text())
        self.session, self.api = load_fixture(FIXTURE), load_fixture(FIXTURE)
        self.control = direct_graph(self.value['setup'])
        for session in (self.session, self.api):
            graph = machines(session)
            adapter = session.settlement._input_adapter
            self.assertIs(adapter._machine, graph[0])
            self.assertIs(adapter._sources['booking'], graph[1])
            self.assertIs(adapter._sources['resale'], graph[2])
            self.assertEqual(snapshot(graph), snapshot(self.control))

    def step(self, row):
        before = snapshot(machines(self.session))
        expected = outcome(lambda: direct_request(self.control, row, self.value))
        results = []
        for session, api in ((self.session, False), (self.api, True)):
            op = row['operation']
            with ExitStack() as stack:
                view = target = None
                if op in SELECTORS:
                    _, field, index = SELECTORS[op]
                    machine = machines(session)[index]
                    view = stack.enter_context(patch.object(machine, 'view', wraps=machine.view))
                    target = stack.enter_context(patch.object(machines(session)[0], 'initiate',
                                                              wraps=machines(session)[0].initiate))
                if api:
                    def call():
                        receipt = getattr(getattr(session, row['surface']), op)(**row['arguments'])
                        return dict(surface=row['surface'], operation=op,
                                    **{'view' if op.startswith('view') else 'receipt': receipt})
                else:
                    def call():
                        return dispatch_request(session, row)
                actual = outcome(call)
                self.assertEqual(actual, expected)
                if view is not None:
                    view.assert_called_once_with(row['arguments'][field])
                    self.assertEqual(target.call_count, 0 if 'type' in actual.get('error', {}) else 1)
            self.assertEqual(snapshot(machines(session)), snapshot(self.control))
            results.append(actual)
        if row['surface'] == 'settlement':
            self.assertEqual(snapshot(machines(self.session))[1:], before[1:])
        if 'error' in results[0]:
            self.assertEqual(snapshot(machines(self.session)), before)
        else:
            result = results[0].get('receipt', results[0].get('view'))
            {'settlement': settlement_flags, 'booking': booking_flags,
             'resale': resale_flags, 'admission': assert_flags}[row['surface']](self, result)
            if row['operation'] in SELECTORS:
                first = result['settlement']
                self.assertEqual(first['phase'], 'INITIATED')
                self.assertIs(first['mock_authorized'], False)
                self.assertIsNone(first['claim'])
        return results[0]

    def test_api_and_dispatch_journeys_match_receipts_errors_states_and_journals(self):
        for name in ('booking', 'resale', 'boundaries'):
            with self.subTest(name=name):
                self.graph()
                results = [self.step(row) for row in rows(name)]
                self.assertEqual(sum('error' in r for r in results), 5 if name == 'boundaries' else 0)
                if name == 'boundaries':
                    self.assertEqual([r['error'] for r in results if 'error' in r], [
                        dict(type='SettlementInputSourceError', message='settlement input view failed'),
                        dict(code='IDEMPOTENCY_CONFLICT'),
                        dict(type='SettlementInputSourceError', message='settlement input view failed'),
                        dict(code='POLICY_FIELDS'), dict(code='IDEMPOTENCY_CONFLICT')])
                    continue
                sid = 'claim-2' if name == 'booking' else 'resale-claim'
                claim = self.session.settlement.view(sid)['claim']
                self.assertEqual(claim['distributed_cash'], 9301 if name == 'booking' else 8000)
                self.assertEqual(claim['undistributed_cash'], 0)
                first = next(r['receipt'] for r in results if r.get('operation') == f'initiate_from_{name}')
                replay = [r['receipt'] for r in results if r.get('operation') == f'initiate_from_{name}'][-1]
                self.assertEqual(replay, first | dict(duplicate=True, applied=None))
                for session in (self.session, self.api):
                    self.assertEqual(session.admission._adapter._source.calls, ())
                    self.assertEqual(session.resale._adapter._source.calls, () if name == 'booking' else ('offer-1',))
                    self.assertEqual(session.resale._payment_adapter._source.calls,
                                     () if name == 'booking' else ('payment-1',))
                self.assertEqual(self.session.booking.view('reserve-2')['phase'],
                                 'ISSUED' if name == 'booking' else 'PAYMENT_NOTED')

    def test_missing_unconfirmed_malformed_and_faulting_sources_leave_graph_and_key_free(self):
        for kind in ('booking', 'resale'):
            faults = ('missing', 'mismatch', 'amount', 'currency', 'exception')
            for fault in faults + (('unconfirmed',) if kind == 'booking' else ()):
                with self.subTest(kind=kind, fault=fault):
                    self.graph()
                    if kind == 'resale':
                        self.step(rows('resale')[0])
                    row = initiation(kind)
                    args = row['arguments']
                    source = machines(self.session)[SELECTORS[row['operation']][2]]
                    field = SELECTORS[row['operation']][1]
                    valid = source.view(args[field])
                    bad = valid | {'mismatch': {field:'other'}, 'amount': dict(amount=True),
                                   'currency': dict(currency='USD'), 'unconfirmed': dict(order_id=None)}.get(fault, {})
                    before = snapshot(machines(self.session))
                    options = dict(side_effect=RuntimeError('synthetic')) if fault in ('missing','exception') else dict(return_value=bad)
                    with patch.object(source, 'view', **options) as read, \
                            patch.object(machines(self.session)[0], 'initiate', wraps=machines(self.session)[0].initiate) as target:
                        with self.assertRaises(SettlementInputSourceError):
                            dispatch_request(self.session, row)
                        read.assert_called_once_with(args[field])
                        target.assert_not_called()
                    self.assertEqual(snapshot(machines(self.session)), before)
                    self.assertFalse(getattr(self.session.settlement, row['operation'])(**args)['duplicate'])

    def test_real_unconfirmed_booking_and_confirmed_unpaid_booking(self):
        self.graph()
        setup = [e for e in self.value['setup'] if not(e['subject_id'] == 'order-2'
                 and e['operation'] in ('confirm', 'observe_payment'))]
        session = TicketOperationsSession(setup=setup, offer_source=Mock(), presentation_source=Mock())
        before = snapshot(machines(session))
        with self.assertRaises(InvalidSettlementInputRecord):
            session.settlement.initiate_from_booking(**initiation()['arguments'])
        self.assertEqual(snapshot(machines(session)), before)
        session.booking.set_clock('clock', now_ms=1000000, idempotency_key='ticket-clock')
        session.booking.confirm('order-2', reservation_id='reserve-2', amount=10001,
                                quote_ref='explicit-quote', idempotency_key='explicit-confirm')
        before = snapshot(machines(session))[1:]
        session.settlement.initiate_from_booking(**initiation()['arguments'])
        self.assertEqual(snapshot(machines(session))[1:], before)
        view = session.booking.view('reserve-2')
        self.assertEqual(view['phase'], 'CONFIRMED')
        self.assertIsNone(view['payment_ref'])
        self.assertIsNone(view['settlement_id'])

    def test_manual_source_alias_replay_changed_extraction_and_caller_body_conflicts(self):
        for kind in ('booking', 'resale'):
            for manual_first in (True, False):
                self.graph()
                if kind == 'resale':
                    self.step(rows(kind)[0])
                row = initiation(kind)
                args = dict(row['arguments'])
                field = SELECTORS[row['operation']][1]
                source = machines(self.session)[SELECTORS[row['operation']][2]]
                record = source.view(args.pop(field))
                manual = args | dict(gross=record['amount'], currency=record['currency'])
                calls = [lambda: self.session.settlement.initiate(**manual),
                         lambda: getattr(self.session.settlement, row['operation'])(**row['arguments'])]
                if not manual_first:
                    calls.reverse()
                first = calls[0]()
                self.session.settlement.authorize(args['settlement_id'], idempotency_key='later-auth')
                self.assertEqual(calls[1](), first | dict(duplicate=True, applied=None))
                before = snapshot(machines(self.session))
                for changes in (dict(trade_id='different'), dict(debtor_role='different'),
                                dict(settlement_id='different'), dict(policy=manual['policy'] | dict(fee_bps=1))):
                    with self.assertRaises(SettlementError) as caught:
                        getattr(self.session.settlement, row['operation'])(**(row['arguments'] | changes))
                    self.assertEqual(caught.exception.code, 'IDEMPOTENCY_CONFLICT')
                with patch.object(source, 'view', return_value=record | dict(amount=record['amount']-1)):
                    with self.assertRaises(SettlementError) as caught:
                        getattr(self.session.settlement, row['operation'])(**row['arguments'])
                    self.assertEqual(caught.exception.code, 'IDEMPOTENCY_CONFLICT')
                # Switching to a source alias with identical extracted body replays.
                with patch.object(source, 'view', return_value=record | {field:'alias'}):
                    self.assertEqual(getattr(self.session.settlement, row['operation'])(
                        **(row['arguments'] | {field:'alias'})), first | dict(duplicate=True, applied=None))
                self.assertEqual(snapshot(machines(self.session)), before)

    def test_switching_source_kind_uses_unchanged_target_fingerprint(self):
        self.graph()
        self.step(rows('resale')[0])
        row = initiation('resale')
        first = self.session.settlement.initiate_from_resale(**row['arguments'])
        args = {k:v for k,v in row['arguments'].items() if k != 'listing_id'}
        # A synthetic source record supplies identical target values. Source
        # identity/kind is deliberately absent from the existing FSM fingerprint.
        record = dict(reservation_id='alias', order_id='explicit-order', amount=8000, currency='KRW')
        before = snapshot(machines(self.session))
        with patch.object(machines(self.session)[1], 'view', return_value=record) as read:
            replay = self.session.settlement.initiate_from_booking(reservation_id='alias', **args)
            read.assert_called_once_with('alias')
        self.assertEqual(replay, first | dict(duplicate=True, applied=None))
        self.assertEqual(snapshot(machines(self.session)), before)

    def test_required_signatures_constructor_no_reads_and_exact_forwarding(self):
        for op, (kind, field, _) in SELECTORS.items():
            signature = inspect.signature(getattr(TicketSettlementSession, op))
            self.assertEqual(set(signature.parameters), {'self', 'settlement_id', field,
                             'idempotency_key', 'trade_id', 'debtor_role', 'policy'})
            for name, parameter in signature.parameters.items():
                self.assertIs(parameter.default, inspect.Parameter.empty)
                if name not in ('self', 'settlement_id'):
                    self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            machine, booking, resale = Mock(spec=SettlementMachine), Mock(), Mock()
            with patch('ticket_operations_session.SettlementInputAdapter') as ctor:
                desk = TicketSettlementSession(machine, booking_source=booking, resale_source=resale)
                ctor.assert_called_once_with(machine, booking_source=booking, resale_source=resale)
                adapter = ctor.return_value
                self.assertEqual(adapter.mock_calls + machine.mock_calls + booking.mock_calls + resale.mock_calls, [])
                args = {name:object() for name in signature.parameters if name != 'self'}
                expected = {k:v for k,v in args.items() if k != field} | dict(source_kind=kind, source_id=args[field])
                receipt = object()
                adapter.apply.return_value = receipt
                self.assertIs(getattr(desk, op)(**args), receipt)
                adapter.apply.assert_called_once_with(**expected)
                adapter.reset_mock()
                error = SettlementError('OPAQUE')
                adapter.apply.side_effect = error
                with self.assertRaises(SettlementError) as caught:
                    getattr(desk, op)(args['settlement_id'], **{k:v for k,v in args.items() if k!='settlement_id'})
                self.assertIs(caught.exception, error)
                adapter.apply.assert_called_once_with(**expected)
                self.assertEqual(machine.mock_calls, [])


if __name__ == '__main__':
    unittest.main()
