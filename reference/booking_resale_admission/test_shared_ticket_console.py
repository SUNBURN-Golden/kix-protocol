"""Source-informed composition evidence; real pipes, synthetic service graph."""

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import shared_ticket_console as console
from test_admission_session import assert_flags
from test_reservation_fsm import assert_not_final
from test_resale_fsm import assert_not_final as assert_resale_flags
from issued_ticket_adapter import IssuedTicketSourceError
from resale_payment_source import ResalePaymentSourceError
from statement_source import StatementSourceError
from ticket_operations_cli import _DOMAIN_ERRORS, _error
from ticket_operations_cli import dispatch_request
from test_ticket_operations_client import direct
from test_ticket_settlement_controls import settlement_flags
from ticket_operations_client import TicketOperationsClient, TicketDeskTransportUncertainty
from ticket_operations_fixture import load_fixture

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = HERE / 'fixtures/ticket_operations_payment_session.json'
QUOTE = HERE / 'fixtures/booking_console_quote.json'
JOURNEY = HERE / 'fixtures/shared_ticket_console_journey.txt'
FULFILLMENT = HERE / 'fixtures/ticket_operations_fulfillment_session.json'
BIND = ['bind_settlement', 'reserve-2', 'claim-2', 'second-bind', 'BIND_SETTLEMENT']
ISSUE = ['issue', 'issue-2', 'order-2', 'second-issue', 'ISSUE']
ADOPT = ['adopt_issued_from_booking', 'reserve-2', 'issue-2']
NEW_ACTIONS = [('booking', BIND), ('booking', ISSUE),
               ('admission', ADOPT + ['second-admission-adopt', 'ADOPT']),
               ('resale', ADOPT + ['second-resale-adopt', 'SUBMIT'])]
START_RESALE = HERE / 'fixtures/settlement_console_start_resale.txt'
GUIDED_RESALE = HERE / 'fixtures/settlement_console_guided_resale.txt'
INPUTS = HERE / 'fixtures/ticket_operations_settlement_inputs_session.json'
SURFACES = ('booking', 'resale', 'admission', 'settlement')
VIEWS = {'booking': ['view', 'reserve-1'], 'resale': ['view_right', 'issue-1'],
         'admission': ['view', 'issue-1'], 'settlement': ['view', 'resale-claim']}
QUEUE = [item for name in SURFACES for item in [name, *VIEWS[name], 'quit']] + ['quit']
PAYMENT_INPUT = ['observe_resale_payment', 'caller-listed', 'ef' * 32, '8000', 'null', 'caller-payment', 'SUBMIT']
PAYMENT_LIST = ['list_resale_inputs', 'caller-listed', 'issue-1', '1', 'buyer-1', 'buyer-2',
                '8000', '1120000', '"reserve-1"', 'caller-list', 'SUBMIT']
EXCEPTION_ACTIONS = [
    ('booking', ['reconcile', 'reserve-1', 'booking-reconcile', 'RECONCILE']),
    ('resale', ['reconcile', 'list-1', 'resale-reconcile', 'SUBMIT']),
    ('admission', ['reconcile', 'issue-1', 'admission-reconcile', 'RECONCILE']),
    ('settlement', ['reconcile', 'resale-claim', 'settlement-reconcile', 'SUBMIT']),
    ('settlement', ['fail', 'resale-claim', 'synthetic', 'settlement-fail', 'SUBMIT']),
    ('settlement', ['cancel', 'resale-claim', 'synthetic', 'settlement-cancel', 'SUBMIT']),
]
FAULT_ACTIONS = ([(name, VIEWS[name]) for name in SURFACES] + NEW_ACTIONS
                 + [('resale', PAYMENT_INPUT)] + EXCEPTION_ACTIONS)
CLOCK = ['set_clock', 'clock', '1000000', 'shared-clock']
HOLD = ['hold', 'shared-reservation', 'show-1', '1', 'shared-buyer', '1120000', 'shared-hold']
LOAD = ['load_quote', str(QUOTE)]
TARGET = ['target', 'shared-reservation', 'shared-order', 'shared-confirm']


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


def envelopes(output):
    return [json.loads(value) for value in re.findall(r'desk=(\{[^\n]+\})', output)]


class SharedTicketConsoleTests(unittest.TestCase):
    def drive(self, answers=(), *, client=None, stream=None, output=None, errors=None, fixture=FIXTURE):
        if client is None:
            client = TicketOperationsClient.launch(fixture, cleanup_timeout=1)
        output = io.StringIO() if output is None else output
        errors = io.StringIO() if errors is None else errors
        stream = script(answers) if stream is None else stream
        calls, replies = [], []
        original = client.request

        def record(row):
            calls.append(deepcopy(row))
            reply = original(row)
            replies.append(deepcopy(reply))
            return reply

        with patch.object(console.TicketOperationsClient, 'launch', return_value=client) as launch, \
                patch.object(client, 'request', side_effect=record), \
                patch.object(client, 'close', wraps=client.close) as close, \
                patch('sys.stdin', stream), patch('sys.stdout', output), patch('sys.stderr', errors):
            status = console.main(['--fixture', str(fixture), '--cleanup-timeout', '1'])
        launch.assert_called_once_with(fixture, cleanup_timeout=1)
        close.assert_called_once_with()
        if isinstance(client, TicketOperationsClient):
            self.assertTrue(client._process.stdin.closed)
            self.assertTrue(client._process.stdout.closed)
            self.assertIsNotNone(client._process.returncode)
        return status, calls, replies, output.getvalue(), errors.getvalue()

    def parity(self, calls, replies, output, fixture=FIXTURE):
        # Direct service methods share source with the desk; no independent FSM claim.
        control = load_fixture(fixture)
        expected = []
        for row in calls:
            try:
                if row['operation'] == 'adopt_issued_from_booking':
                    expected.append(dict(surface=row['surface'], operation=row['operation'], receipt=
                        control.adopt_issued_from_booking(surface=row['surface'], **row['arguments'])))
                else:
                    expected.append(direct(control, row))
            except _DOMAIN_ERRORS + (ResalePaymentSourceError, StatementSourceError, IssuedTicketSourceError) as error:
                expected.append(_error(row['surface'], row['operation'], error))
        self.assertEqual(replies, expected)
        self.assertEqual(envelopes(output), replies)
        for row in calls:
            self.assertEqual(set(row), {'surface', 'operation', 'arguments'})

    def test_live_cross_surface_reconciliation_history_current_views_and_conflicts(self):
        fixture = HERE / 'fixtures/ticket_operations_session.json'
        answers = (HERE / 'fixtures/shared_ticket_console_reconcile.txt').read_text().splitlines()
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(answers, fixture=fixture)
        launch.assert_called_once()
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.parity(calls, replies, output, fixture)
        for reply in replies:
            if 'error' not in reply:
                flags = {'booking': assert_not_final, 'resale': assert_resale_flags,
                         'admission': assert_flags, 'settlement': settlement_flags}[reply['surface']]
                flags(self, reply.get('receipt', reply.get('view')))
        for surface, key, fresh in [('booking', 'booking-history', 'booking-fresh'),
                ('resale', 'resale-recon', 'resale-current'),
                ('settlement', 'settlement-history', 'settlement-current')]:
            history = [reply['receipt'] for row, reply in zip(calls, replies, strict=True)
                if row['surface'] == surface and row['operation'] == 'reconcile'
                and row['arguments']['idempotency_key'] == key and 'receipt' in reply]
            self.assertEqual(len(history), 2)
            self.assertEqual(history[1], history[0] | dict(duplicate=True, applied=None))
            current = next(reply['receipt'] for row, reply in zip(calls, replies, strict=True)
                if row['surface'] == surface and row['arguments'].get('idempotency_key') == fresh)
            self.assertTrue(current['matched'])
            self.assertFalse(current['duplicate'])
            self.assertNotEqual(history[0]['state_digest'], current['state_digest'])
            self.assertGreater(current['entry_count'], history[0]['entry_count'])
        booking_views = [r['view'] for r in replies if r['surface'] == 'booking' and 'view' in r]
        self.assertEqual(booking_views[0]['phase'], 'RELEASED')
        resale_views = [r['view'] for r in replies if r['surface'] == 'resale' and 'view' in r]
        self.assertEqual(resale_views[0]['phase'], 'CLOSED')
        admission = [r for r in replies if r['surface'] == 'admission' and r['operation'] == 'reconcile']
        self.assertEqual(admission[1]['receipt'], admission[0]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual([r['error'] for r in admission[2:4]], [{'code': 'STALE_VERSION'}] * 2)
        self.assertEqual(admission[-1]['error'], {'code': 'IDEMPOTENCY_CONFLICT'})
        for surface in SURFACES:
            self.assertTrue(any(r['surface'] == surface and r.get('error') ==
                                {'code': 'IDEMPOTENCY_CONFLICT'} for r in replies))
        snapshots = sum('receipt' in r for r in replies)
        self.assertEqual(output.count('Historical action snapshot;'), snapshots)
        self.assertIn('not real refund completion', output)
        # No derived repair/compensation request: this is the exact selected sequence.
        self.assertEqual([r['operation'] for r in calls], [
            'set_clock', 'hold', 'reconcile', 'release', 'reconcile', 'view', 'reconcile', 'reconcile', 'reconcile',
            'authorize_admission_inputs', 'reconcile', 'set_clock', 'list_resale_inputs', 'reconcile',
            'hold_buy', 'observe_resale_payment', 'bind_settlement', 'accept_resale', 'close',
            'reconcile', 'reconcile', 'reconcile', 'reconcile', 'view', 'reconcile', 'view',
            'reconcile', 'reconcile', 'reconcile', 'reconcile', 'distribute', 'reconcile', 'view',
            'reconcile', 'reconcile', 'reconcile'])

    def test_shared_pre_capture_exceptions_preserve_booking_and_navigation(self):
        fixture = HERE / 'fixtures/ticket_operations_settlement_exceptions_session.json'
        actions = (HERE / 'fixtures/settlement_console_exceptions.txt').read_text().splitlines()
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(
                ['booking', 'view', 'reserve-2', 'quit', 'settlement', *actions,
                 'booking', 'view', 'reserve-2', 'quit', 'quit'], fixture=fixture)
        launch.assert_called_once()
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.parity(calls, replies, output, fixture)
        self.assertEqual(replies[0]['view'], replies[-1]['view'])
        self.assertEqual([replies[i]['receipt']['settlement']['phase'] for i in (1, 7, 13, 19)],
                         ['FAILED', 'CANCELLED', 'FAILED', 'CANCELLED'])
        for reply in replies[1:-1]:
            if 'error' not in reply:
                settlement_flags(self, reply.get('receipt', reply.get('view')))

    def test_already_fenced_client_rejects_exception_actions_before_writing_or_restarting(self):
        for name, action in EXCEPTION_ACTIONS:
            with self.subTest(surface=name, operation=action[0]):
                with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
                    client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
                    with patch.object(client._process.stdin, 'write', return_value=1):
                        with self.assertRaises(TicketDeskTransportUncertainty):
                            client.request(dict(surface='booking', operation='view',
                                                arguments=dict(reservation_id='reserve-1')))
                    uncertainty = client.uncertainty
                    self.assertIsNotNone(uncertainty)
                    pending = script([name, *action, *QUEUE])
                    with patch.object(client._process.stdin, 'write', side_effect=AssertionError('fenced write')) as write:
                        status, calls, replies, _, errors = self.drive(client=client, stream=pending)
                        write.assert_not_called()
                launch.assert_called_once()
                self.assertEqual((status, len(calls), replies), (2, 1, []))
                self.assertIs(client.uncertainty, uncertainty)
                self.assertEqual(pending.read(), script(QUEUE).read())
                self.assertIn('TicketDeskClientStateError', errors)

    def test_exception_declines_and_confirmation_interrupt_fence_queued_navigation(self):
        for name, action in EXCEPTION_ACTIONS:
            for failure in (None, KeyboardInterrupt('confirmation'), OSError('input')):
                with self.subTest(surface=name, operation=action[0], failure=failure):
                    prefix = script([name, *action[:-1]])
                    queued = script(QUEUE)

                    class BrokenInput:
                        broken = False

                        def readline(self):
                            line = prefix.readline()
                            if line:
                                return line
                            if not self.broken:
                                self.broken = True
                                if failure is None:
                                    return ''
                                raise failure
                            return queued.readline()

                    status, calls, _, _, errors = self.drive(stream=BrokenInput())
                    self.assertEqual((status, calls), (2, []))
                    self.assertEqual(queued.read(), script(QUEUE).read())
                    self.assertIn('FENCED:', errors)
            status, calls, _, output, errors = self.drive(
                [name, *action[:-1], 'no', 'quit', 'settlement', 'quit', 'quit'])
            self.assertEqual((status, calls, errors), (0, [], ''))
            self.assertIn('Declined; no request sent.', output)

    def test_reconciliation_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
            '--fixture', str(HERE / 'fixtures/ticket_operations_session.json'), '--cleanup-timeout', '1'],
            input=(HERE / 'fixtures/shared_ticket_console_reconcile.txt').read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (1, 'Child exit status=1\n'))
        self.assertEqual(len(envelopes(result.stdout)), 36)
        self.assertIn('STALE_VERSION', result.stdout)
        self.assertIn('Historical action snapshot;', result.stdout)

    def fulfillment(self, name):
        answers = (HERE / ('fixtures/shared_ticket_console_fulfillment' + name + '.txt')).read_text().splitlines()
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            result = self.drive(answers, fixture=FULFILLMENT)
        launch.assert_called_once()
        status, calls, replies, output, errors = result
        self.parity(calls, replies, output, FULFILLMENT)
        for reply in replies:
            if 'error' not in reply:
                flags = {'booking': assert_not_final, 'resale': assert_resale_flags,
                         'admission': assert_flags}[reply['surface']]
                flags(self, reply.get('receipt', reply.get('view')))
        return result

    def test_live_fulfillment_separate_actions_one_child_and_explicit_views(self):
        control = load_fixture(FULFILLMENT)
        prepared = control.booking.view('reserve-2')
        self.assertEqual(prepared['phase'], 'PAYMENT_NOTED')
        self.assertIsNone(prepared['issuance_id'])
        status, calls, replies, output, errors = self.fulfillment('')
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([(r['surface'], r['operation']) for r in calls], [
            ('booking', op) for op in ('view', 'set_clock', 'bind_settlement', 'view', 'issue', 'view')
        ] + [('admission', 'adopt_issued_from_booking'), ('admission', 'view'),
             ('resale', 'adopt_issued_from_booking'), ('resale', 'view_right'), ('booking', 'view')])
        for index, arguments in ((2, dict(reservation_id='reserve-2', settlement_id='claim-2',
                                         idempotency_key='second-bind')),
                                 (4, dict(issuance_id='issue-2', order_id='order-2',
                                          idempotency_key='second-issue'))):
            self.assertEqual(calls[index]['arguments'], arguments)
        for index, key in ((6, 'second-admission-adopt'), (8, 'second-resale-adopt')):
            self.assertEqual(calls[index]['arguments'], dict(reservation_id='reserve-2',
                                                           right_id='issue-2', idempotency_key=key))
        self.assertEqual(replies[3]['view']['phase'], 'PAYMENT_NOTED')
        self.assertIsNone(replies[3]['view']['right'])
        self.assertEqual(replies[5]['view']['phase'], 'ISSUED')
        self.assertEqual(replies[5]['view']['settlement_gate'], 'MOCK_COMMIT_OBSERVED')
        self.assertEqual(replies[7]['view']['phase'], 'ELIGIBLE')
        self.assertEqual(replies[9]['view']['right']['holder_role'], 'buyer-3')
        self.assertEqual(replies[5]['view'], replies[10]['view'])
        self.assertIn('Historical action snapshot', output)
        self.assertIn('Current service observation.', output)
        proposed = [json.loads(v) for v in re.findall(r'proposed=(\{[^\n]+\})', output)]
        self.assertEqual(proposed, [calls[i] for i in (2, 4, 6, 8)])

    def test_live_fulfillment_authorize_decline_consume_then_historical_replays(self):
        status, calls, replies, output, errors = self.fulfillment('_consume')
        self.assertEqual((status, errors), (0, ''))
        # First 11 requests are the issuance and separate adoption journey.
        self.assertEqual([(r['surface'], r['operation']) for r in calls[11:]], [
            ('admission', op) for op in ('authorize_admission_inputs', 'view', 'view', 'consume_inputs', 'view')
        ] + [('booking', 'issue'), ('booking', 'view'),
             ('admission', 'adopt_issued_from_booking'), ('admission', 'view'),
             ('resale', 'adopt_issued_from_booking'), ('resale', 'view_right')])
        self.assertEqual(replies[12]['view']['phase'], 'AUTHORIZED')
        self.assertEqual(replies[12]['view'], replies[13]['view'])
        self.assertEqual(replies[13]['view']['version'], 1)
        self.assertEqual(replies[15]['view']['phase'], 'CONSUMED')
        self.assertEqual(replies[15]['view']['version'], 2)
        for first, replay in ((4, 16), (6, 18), (8, 20)):
            self.assertEqual(calls[first], calls[replay])
            self.assertEqual(replies[replay]['receipt'], replies[first]['receipt'] |
                             {'duplicate': True, 'applied': None})
        self.assertEqual(replies[16]['receipt']['evidence']['version'], 1)
        self.assertEqual(replies[17]['view']['right']['version'], 2)
        self.assertEqual(replies[19]['view']['phase'], 'CONSUMED')
        self.assertEqual(replies[21]['view']['right']['version'], 1)
        self.assertEqual([r['operation'] for r in calls].count('consume_inputs'), 1)
        self.assertIn('Declined; no request sent.', output)
        self.assertIn('Action snapshot: {"applied": null, "duplicate": true}', output)

    def test_live_fulfillment_boundaries_preserve_source_domain_and_key_results(self):
        status, calls, replies, output, errors = self.fulfillment('_boundaries')
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual([r['error']['code'] for r in replies if 'code' in r.get('error', {})],
                         ['IDEMPOTENCY_CONFLICT'] * 4)
        source_errors = [r['error'] for r in replies if 'type' in r.get('error', {})]
        self.assertEqual(len(source_errors), 8)  # unissued, missing, two crossed pairs per target
        self.assertEqual({e['type'] for e in source_errors},
                         {'InvalidIssuedTicketRecord', 'IssuedTicketSourceError'})
        self.assertIn({'type': 'InvalidIssuedTicketRecord', 'message': 'issuance identity mismatch'}, source_errors)
        self.assertEqual(output.count('Declined; no request sent.'), 2)
        views = [r['view'] for r in replies if r['surface'] == 'booking' and 'view' in r]
        self.assertEqual([v['phase'] for v in views], ['PAYMENT_NOTED', 'ISSUED'])
        self.assertIsNone(views[0]['settlement_id'])
        self.assertIsNone(views[0]['issuance_id'])
        # Source refusal binds no target key; the same caller request later succeeds.
        for surface in ('admission', 'resale'):
            indices = [i for i, r in enumerate(calls) if r['surface'] == surface
                       and r['operation'] == 'adopt_issued_from_booking'
                       and r['arguments']['reservation_id'] == 'reserve-2'
                       and r['arguments']['right_id'] == 'issue-2']
            first, accepted, replay = indices
            self.assertEqual(calls[first], calls[accepted])
            self.assertIn('error', replies[first])
            self.assertFalse(replies[accepted]['receipt']['duplicate'])
            self.assertEqual(replies[replay]['receipt'], replies[accepted]['receipt'] |
                             {'duplicate': True, 'applied': None})

    def test_live_issue_without_payment_preserves_refusal_and_current_view(self):
        value = json.loads(FULFILLMENT.read_text())
        value['setup'] = [r for r in value['setup'] if not (
            r['operation'] == 'observe_payment' and r['subject_id'] == 'order-2')]
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / 'unpaid.json'
            fixture.write_text(json.dumps(value))
            status, calls, replies, output, errors = self.drive(
                ['booking', *CLOCK, *ISSUE, *ISSUE, 'view', 'reserve-2', 'quit',
                 'resale', 'view_right', 'issue-1', 'quit', 'quit'], fixture=fixture)
            self.parity(calls, replies, output, fixture)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(replies[1]['error'], {'code': 'ILLEGAL_TRANSITION'})
        self.assertEqual(replies[2], replies[1])
        self.assertEqual(replies[3]['view']['phase'], 'CONFIRMED')
        self.assertIsNone(replies[3]['view']['payment_ref'])
        self.assertIsNone(replies[3]['view']['right'])
        self.assertEqual(len(calls), 5)

    def test_fulfillment_requires_explicit_successful_booking_clock(self):
        for action in (BIND, ISSUE):
            with self.subTest(operation=action[0]):
                pending = script(['booking', *action, *QUEUE])
                status, calls, replies, output, errors = self.drive(stream=pending, fixture=FULFILLMENT)
                self.assertEqual((status, len(calls)), (2, 1))
                self.assertEqual(replies[0]['error'], {'type': 'BookingInputError',
                    'message': 'explicit successful session set_clock required before mutation'})
                self.assertEqual(envelopes(output), replies)
                self.assertEqual(pending.read(), script(QUEUE).read())
                self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], replies[0])

    def payment_parity(self, calls, replies, output):
        control = load_fixture(INPUTS)
        expected = []
        for row in calls:
            try:
                expected.append(dispatch_request(control, row))
            except _DOMAIN_ERRORS as error:
                expected.append(_error(row['surface'], row['operation'], error))
        self.assertEqual(replies, expected)
        self.assertEqual(envelopes(output), replies)
        proposals = [json.loads(v) for v in re.findall(r'proposed=(\{[^\n]+\})', output)]
        self.assertEqual(proposals, [r for r in calls if not r['operation'].startswith('view')])
        for reply in replies:
            if 'error' not in reply:
                flags = assert_resale_flags if reply['surface'] == 'resale' else settlement_flags
                flags(self, reply.get('receipt', reply.get('view')))

    def test_live_payment_inputs_listed_and_held_one_child_separate_settlement_and_transfer(self):
        fixture = json.loads(INPUTS.read_text())
        for held in (False, True):
            name = 'held' if held else 'listed'
            listing = 'caller-' + name
            self.assertNotIn(listing, [json.loads(p['recorded_text'])['listing_id']
                                       for p in fixture['payments']])
            answers = (HERE / f'fixtures/shared_ticket_console_payment_inputs_{name}.txt').read_text().splitlines()
            with self.subTest(held=held), \
                    patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
                status, calls, replies, output, errors = self.drive(answers, fixture=INPUTS)
            launch.assert_called_once()
            self.assertEqual((status, errors), (0, ''))
            self.payment_parity(calls, replies, output)
            operations = [('settlement', 'view'), ('resale', 'list_resale_inputs')]
            if held:
                operations += [('resale', 'hold_buy')]
            operations += [('resale', op) for op in ('view', 'observe_resale_payment', 'view', 'view_right')]
            operations += [('settlement', op) for op in ('view', 'initiate_from_resale', 'authorize', 'capture',
                'commit_recorded_statement', 'observe_recorded_statement', 'view')]
            operations += [('resale', op) for op in ('bind_settlement', 'accept_resale', 'view', 'view_right',
                'observe_resale_payment', 'view')]
            self.assertEqual([(r['surface'], r['operation']) for r in calls], operations)
            payment_indices = [i for i, r in enumerate(calls) if r['operation'] == 'observe_resale_payment']
            first, replay = payment_indices
            self.assertEqual(calls[first]['arguments'], dict(listing_id=listing, payment_ref='ef' * 32,
                amount=8000, buyer_role='buyer-2' if held else None, idempotency_key='caller-payment'))
            self.assertEqual(calls[first], calls[replay])
            noted = replies[first]['receipt']
            self.assertEqual(replies[first - 1]['view']['phase'], 'BUY_HELD' if held else 'LISTED')
            self.assertEqual(noted['listing']['phase'], 'PAYMENT_NOTED')
            self.assertIsNone(noted['listing']['settlement_id'])
            self.assertEqual(noted['listing']['settlement_gate'], 'UNBOUND')
            self.assertFalse(noted['listing']['ownership_transferred'])
            self.assertEqual((noted['right']['holder_role'], noted['right']['version']), ('buyer-1', 1))
            # Explicit views bracket payment: existing settlement remains identical.
            self.assertEqual(replies[0]['view'], replies[first + 3]['view'])
            self.assertEqual(replies[-4]['view']['phase'], 'TRANSFERRED')
            self.assertEqual(replies[-4]['view']['settlement_gate'], 'MOCK_COMMIT_OBSERVED')
            self.assertEqual((replies[-3]['view']['right']['holder_role'],
                              replies[-3]['view']['right']['version']), ('buyer-2', 2))
            self.assertEqual(replies[replay]['receipt'], noted | {'duplicate': True, 'applied': None})
            self.assertEqual(replies[-1]['view'], replies[-4]['view'])

    def test_payment_inputs_buyer_amount_refusals_replay_conflicts_and_unchanged_views(self):
        cases = [(False, 'null', '8000', None), (False, '"buyer-2"', '8000', None),
                 (False, '"wrong"', '8000', 'RECIPIENT_MISMATCH'),
                 (True, '"buyer-2"', '8000', None), (True, 'null', '8000', 'BUYER_MISMATCH'),
                 (True, '"wrong"', '8000', 'BUYER_MISMATCH'),
                 (False, 'null', '7999', 'RESALE_AMOUNT_MISMATCH'),
                 (True, '"buyer-2"', '8001', 'RESALE_AMOUNT_MISMATCH')]
        for held, buyer, amount, code in cases:
            with self.subTest(held=held, buyer=buyer, amount=amount):
                action = PAYMENT_INPUT.copy()
                action[3:5] = [amount, buyer]
                conflict = action.copy()
                conflict[2] = 'aa' * 32
                prefix = PAYMENT_LIST + (['hold_buy', 'caller-hold', 'caller-listed', 'buyer-2',
                                          'caller-hold-key', 'SUBMIT'] if held else [])
                answers = ['resale', *prefix, 'view', 'caller-listed', 'view_right', 'issue-1',
                    *action, 'view', 'caller-listed', 'view_right', 'issue-1', *action, *conflict,
                    'view', 'caller-listed', 'view_right', 'issue-1', 'quit', 'quit']
                status, calls, replies, output, errors = self.drive(answers, fixture=INPUTS)
                self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
                self.payment_parity(calls, replies, output)
                first = next(i for i, r in enumerate(calls) if r['operation'] == 'observe_resale_payment')
                if code is not None:
                    self.assertEqual(replies[first]['error'], {'code': code})
                    self.assertEqual(replies[first + 3], replies[first])
                    self.assertEqual(replies[first + 1]['view'], replies[first - 2]['view'])
                else:
                    self.assertEqual(replies[first + 3]['receipt'],
                                     replies[first]['receipt'] | {'duplicate': True, 'applied': None})
                self.assertEqual(replies[first + 4]['error'], {'code': 'IDEMPOTENCY_CONFLICT'})
                self.assertEqual(replies[-2]['view'], replies[first + 1]['view'])
                self.assertEqual(replies[-1]['view'], replies[first + 2]['view'])
                # view_right includes current listing phase as well as ownership.
                self.assertEqual(replies[first + 2]['view']['right'], replies[first - 1]['view']['right'])
                if code is not None:
                    self.assertEqual(replies[first + 2]['view'], replies[first - 1]['view'])

    def test_payment_inputs_bound_transfer_gates_and_retained_refusals(self):
        # Bind an absent claim first; create, capture and commit only when selected.
        transcript = (HERE / 'fixtures/shared_ticket_console_payment_inputs_listed.txt').read_text().splitlines()
        start = transcript.index('initiate_from_resale')
        finish = transcript.index('view', transcript.index('observe_recorded_statement'))
        settlement_actions = transcript[start:finish]
        initiate_end = settlement_actions.index('SUBMIT') + 1
        bind = ['bind_settlement', 'caller-listed', 'resale-claim', 'caller-bind', 'SUBMIT']
        missing = ['accept_resale', 'gate-transfer', 'caller-listed', 'missing-transfer-key', 'SUBMIT']
        uncommitted = ['accept_resale', 'gate-transfer', 'caller-listed', 'pending-transfer-key', 'SUBMIT']
        fresh = ['accept_resale', 'gate-transfer', 'caller-listed', 'committed-transfer-key', 'SUBMIT']
        answers = ['resale', *PAYMENT_LIST, *PAYMENT_INPUT, *bind, *missing, 'view', 'caller-listed',
            'quit', 'settlement', *settlement_actions[:initiate_end], 'quit', 'resale', *uncommitted,
            'view', 'caller-listed', 'quit', 'settlement', *settlement_actions[initiate_end:], 'quit',
            'resale', *missing, *uncommitted, 'view', 'caller-listed', *fresh, 'view', 'caller-listed',
            'view_right', 'issue-1', 'quit', 'quit']
        status, calls, replies, output, errors = self.drive(answers, fixture=INPUTS)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.payment_parity(calls, replies, output)
        transfers = [r for r in replies if r['operation'] == 'accept_resale']
        self.assertEqual([r['error']['code'] for r in transfers[:-1]],
            ['UNKNOWN_SETTLEMENT', 'SETTLEMENT_NOT_COMMITTED'] * 2)
        views = [r['view'] for r in replies if r['surface'] == 'resale' and r['operation'] == 'view']
        self.assertEqual([v['phase'] for v in views], ['PAYMENT_NOTED'] * 3 + ['TRANSFERRED'])
        self.assertTrue(all(v['current_version'] == 1 and not v['ownership_transferred'] for v in views[:-1]))
        self.assertEqual(replies[-1]['view']['right']['version'], 2)

    def test_received_payment_display_failure_retains_accepted_result_and_fences_navigation(self):
        class BrokenPaymentOutput(io.StringIO):
            def write(self, text):
                if text.startswith('desk=') and json.loads(text[5:])['operation'] == 'observe_resale_payment':
                    raise BrokenPipeError('payment display')
                return super().write(text)
        pending = script(['resale', *PAYMENT_LIST, *PAYMENT_INPUT, *QUEUE])
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, _, errors = self.drive(stream=pending,
                output=BrokenPaymentOutput(), fixture=INPUTS)
        launch.assert_called_once()
        self.assertEqual((status, len(calls), len(replies)), (2, 2, 2))
        self.assertEqual(replies[-1]['receipt']['listing']['phase'], 'PAYMENT_NOTED')
        self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], replies[-1])
        self.assertEqual(pending.read(), script(QUEUE).read())

    def test_payment_transcripts_as_cli_subprocess(self):
        for held in (False, True):
            name = 'held' if held else 'listed'
            answers = (HERE / f'fixtures/shared_ticket_console_payment_inputs_{name}.txt').read_text()
            result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
                '--fixture', str(INPUTS), '--cleanup-timeout', '1'], cwd=ROOT, input=answers,
                text=True, capture_output=True, timeout=10, env=os.environ.copy())
            self.assertEqual((result.returncode, result.stderr), (0, ''))
            replies = envelopes(result.stdout)
            self.assertEqual(len(replies), 19 + int(held))
            self.assertEqual(replies[-2]['receipt']['listing']['phase'], 'PAYMENT_NOTED')
            self.assertEqual(replies[-2]['receipt']['duplicate'], True)
            self.assertEqual(replies[-1]['view']['phase'], 'TRANSFERRED')
            self.assertEqual(replies[-3]['view']['right']['version'], 2)

    def test_payment_decline_and_confirmation_interrupt_fence_shared_navigation(self):
        pending = script(['resale', *PAYMENT_INPUT[:-1], 'no', 'quit', 'quit'])
        status, calls, _, output, errors = self.drive(stream=pending)
        self.assertEqual((status, calls, errors), (0, [], ''))
        self.assertIn('Declined; no request sent.', output)
        for failure in (None, KeyboardInterrupt('approval'), OSError('approval')):
            prefix = script(['resale', *PAYMENT_INPUT[:-1]])
            queued = script(QUEUE)
            class BrokenInput:
                failed = False
                def readline(self):
                    line = prefix.readline()
                    if line:
                        return line
                    if not self.failed:
                        self.failed = True
                        if failure is not None:
                            raise failure
                        return ''
                    return queued.readline()
            status, calls, _, _, errors = self.drive(stream=BrokenInput())
            self.assertEqual((status, calls), (2, []))
            self.assertEqual(queued.read(), script(QUEUE).read())
            self.assertIn('FENCED:', errors)

    def test_live_shared_journey_one_child(self):
        answers = JOURNEY.read_text().splitlines()
        answers[answers.index('reference/booking_resale_admission/fixtures/booking_console_quote.json')] = str(QUOTE)
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(answers)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([(r['surface'], r['operation']) for r in calls], [
            ('booking', op) for op in ('set_clock', 'hold', 'preview_calculated_quote',
                                      'confirm_calculated_quote', 'view')
        ] + [('resale', op) for op in ('list_resale_inputs', 'hold_buy', 'observe_recorded_payment',
                                      'bind_settlement', 'accept_resale')]
          + [('admission', 'view'), ('admission', 'view_credential'),
             ('settlement', 'distribute'), ('settlement', 'view'), ('booking', 'view'),
             ('resale', 'view'), ('resale', 'view_right'), ('settlement', 'view')])
        self.parity(calls, replies, output)
        self.assertEqual(replies[4]['view'], replies[14]['view'])
        self.assertEqual(replies[14]['view']['phase'], 'CONFIRMED')
        self.assertEqual(replies[15]['view']['phase'], 'TRANSFERRED')
        self.assertEqual(replies[16]['view']['right']['holder_role'], 'buyer-2')
        self.assertEqual(replies[16]['view']['right']['version'], 2)
        # Stored venue credential is intentionally not reissued after transfer.
        self.assertEqual(replies[10]['view']['holder_role'], 'buyer-1')
        self.assertEqual(replies[11]['view']['presentation']['decision'], 'STALE_VERSION')
        self.assertFalse(replies[11]['view']['presentation']['fresh'])
        self.assertEqual(replies[13]['view'], replies[17]['view'])
        self.assertEqual(replies[17]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[17]['view']['claim']['distribution_order'], ['organizer'])
        for i in (0, 1, 3):
            assert_not_final(self, replies[i]['receipt'])
        assert_not_final(self, replies[14]['view'])
        for i in range(5, 10):
            assert_resale_flags(self, replies[i]['receipt'])
        assert_flags(self, replies[10]['view'])
        assert_flags(self, replies[11]['view'])
        for i in (13, 17):
            settlement_flags(self, replies[i]['view'])
        for label in ('MOCK_GATE_ONLY', 'MOCK_SETTLEMENT_ONLY', 'CALCULATION_ONLY', 'IN_MEMORY_FSM',
                      'UNDETERMINED — Astra/User', 'UNDETERMINED — User/designated advisers'):
            self.assertIn(label, output)

    def test_resale_start_journey_creates_target_and_preserves_ticket_observations(self):
        from settlement_fsm import SettlementError
        from test_settlement_console import POLICY, SettlementConsoleTests
        control = load_fixture(INPUTS)
        for identity in ('claim-2', 'resale-claim'):
            with self.assertRaises(SettlementError) as error:
                control.settlement.view(identity)
            self.assertEqual(error.exception.code, 'UNKNOWN_SETTLEMENT')
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(
                START_RESALE.read_text().splitlines(), fixture=INPUTS)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        sequence = [('booking', 'view'), ('resale', 'list_resale_inputs'),
                    ('resale', 'view'), ('resale', 'view_right')]
        sequence += [('settlement', op) for action in ('initiate_from_resale', 'authorize',
            'capture', 'commit_recorded_statement', 'observe_recorded_statement', 'distribute',
            'initiate_from_resale') for op in (action, 'view')]
        sequence += [('booking', 'view'), ('resale', 'view'), ('resale', 'view_right')]
        self.assertEqual([(r['surface'], r['operation']) for r in calls], sequence)
        for row, reply in zip(calls, replies, strict=True):
            self.assertEqual(reply, dispatch_request(control, row))
        self.assertEqual(envelopes(output), replies)
        self.assertEqual([json.loads(s) for s in re.findall(r'proposed=(\{[^\n]+\})', output)],
                         [r for r in calls if not r['operation'].startswith('view')])
        self.assertEqual(calls[4]['arguments'], dict(settlement_id='resale-claim', listing_id='list-1',
            trade_id='explicit-resale-trade', debtor_role='explicit-debtor', policy=POLICY,
            idempotency_key='resale-input'))
        # All source views are explicit transcript actions, before and after settlement work.
        self.assertEqual(replies[0]['view'], replies[-3]['view'])
        self.assertEqual(replies[2]['view'], replies[-2]['view'])
        self.assertEqual(replies[3]['view'], replies[-1]['view'])
        self.assertEqual(replies[-2]['view']['phase'], 'LISTED')
        self.assertIsNone(replies[-2]['view']['settlement_id'])
        self.assertIsNone(replies[-2]['view']['payment_ref'])
        self.assertEqual(replies[-1]['view']['right']['holder_role'], 'buyer-1')
        self.assertEqual(replies[-1]['view']['right']['version'], 1)
        selected = replies[4:-3]
        self.assertEqual([selected[i]['view']['phase'] for i in (1, 3, 5, 7)],
                         ['INITIATED', 'AUTHORIZED', 'CAPTURED', 'COMMITTED'])
        for i in (0, 2):
            self.assertIsNone(selected[i]['receipt']['settlement']['claim'])
        self.assertEqual(selected[4]['receipt']['settlement']['claim']['confirmed_cash'], 0)
        for reply in selected:
            value = reply['view'] if 'view' in reply else reply['receipt']['settlement']
            self.assertEqual((value['gross'], value['currency']), (8000, 'KRW'))
            settlement_flags(self, value)
        SettlementConsoleTests.summaries(self, selected, output)
        self.assertEqual(selected[-1]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(selected[-2]['receipt'], selected[0]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual(selected[-1]['view'], selected[-3]['view'])
        assert_not_final(self, replies[-3]['view'])
        assert_resale_flags(self, replies[-2]['view'])
        assert_resale_flags(self, replies[-1]['view'])

    def test_navigation_sends_nothing(self):
        answers = ['unknown', '', 'BOOKING'] + [v for name in SURFACES for v in (name, 'quit')] + ['quit']
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(answers)
        launch.assert_called_once()
        self.assertEqual((status, calls, replies, errors), (0, [], [], ''))
        self.assertEqual(output.count('Unknown surface;'), 3)
        # Surface main() is never involved; each run_console receives identical objects.
        client, stream, output, errors = Mock(), script([*SURFACES, 'quit']), io.StringIO(), io.StringIO()
        from contextlib import ExitStack
        with ExitStack() as stack:
            delegates = [stack.enter_context(patch.object(console._SURFACES[name], 'run_console', return_value=0))
                         for name in SURFACES]
            self.assertEqual(console.run_console(client, input_stream=stream,
                output_stream=output, error_stream=errors), 0)
        for delegate in delegates:
            delegate.assert_called_once_with(client, input_stream=stream, output_stream=output, error_stream=errors)
        client.request.assert_not_called()
        client.close.assert_not_called()  # Embedded lifecycle belongs to caller.

    def test_guided_resale_matches_raw_on_one_child_and_preserves_ticket_observations(self):
        from test_settlement_console import SettlementConsoleTests
        raw = self.drive(START_RESALE.read_text().splitlines(), fixture=INPUTS)
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(
                GUIDED_RESALE.read_text().splitlines(), fixture=INPUTS)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual((status, calls, replies), raw[:3])
        control = load_fixture(INPUTS)
        self.assertEqual(replies, [dispatch_request(control, row) for row in calls])
        self.assertEqual(envelopes(output), replies)
        self.assertEqual([json.loads(s) for s in re.findall(r'proposed=(\{[^\n]+\})', output)],
                         [r for r in calls if not r['operation'].startswith('view')])
        self.assertEqual(replies[0]['view'], replies[-3]['view'])
        self.assertEqual(replies[2]['view'], replies[-2]['view'])
        self.assertEqual(replies[3]['view'], replies[-1]['view'])
        SettlementConsoleTests.summaries(self, replies[4:-3], output)
        self.assertEqual(replies[17]['view']['claim']['distributed_cash'], 8000)

    def test_guided_resale_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
            '--fixture', str(INPUTS), '--cleanup-timeout', '1'], cwd=ROOT, input=GUIDED_RESALE.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        replies = envelopes(result.stdout)
        self.assertEqual(len(replies), 21)
        self.assertEqual(replies[17]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[-2]['view']['phase'], 'LISTED')
        self.assertEqual(replies[-1]['view']['right']['holder_role'], 'buyer-1')

    def test_resale_initiation_conflict_preserves_current_view(self):
        from settlement_fsm import SettlementError
        answers = START_RESALE.read_text().splitlines()
        index = len(answers) - 1 - answers[::-1].index('initiate_from_resale')
        answers[index + 3] = 'changed-trade'
        status, calls, replies, output, errors = self.drive(answers, fixture=INPUTS)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        control = load_fixture(INPUTS)
        for row, reply in zip(calls, replies, strict=True):
            try:
                expected = dispatch_request(control, row)
            except SettlementError as error:
                expected = _error(row['surface'], row['operation'], error)
            self.assertEqual(reply, expected)
        self.assertEqual(envelopes(output), replies)
        self.assertEqual(replies[16]['error'], dict(code='IDEMPOTENCY_CONFLICT'))
        self.assertEqual(replies[15]['view'], replies[17]['view'])
        self.assertEqual(replies[2]['view'], replies[-2]['view'])

    def test_booking_reentry_discards_preview(self):
        answers = (['booking'] + CLOCK + HOLD + LOAD + TARGET + ['preview', 'quit',
            'admission', *VIEWS['admission'], 'quit', 'booking', 'confirm', 'preview']
            + LOAD + ['preview'] + TARGET + ['confirm', 'preview', 'confirm', 'decline',
            'confirm', 'preview', 'confirm', 'CONFIRM', 'view', 'shared-reservation', 'quit', 'quit'])
        status, calls, replies, output, errors = self.drive(answers)
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([row['operation'] for row in calls], ['set_clock', 'hold',
            'preview_calculated_quote', 'view', 'preview_calculated_quote',
            'preview_calculated_quote', 'confirm_calculated_quote', 'view'])
        self.assertEqual(output.count('Load quote text and set target before preview.'), 2)
        self.assertEqual(output.count('A new successful preview is required.'), 3)
        self.assertIn('Declined; no confirmation sent.', output)
        self.assertEqual(calls[-2]['arguments'], dict(request_text=QUOTE.read_text(),
            reservation_id='shared-reservation', order_id='shared-order', idempotency_key='shared-confirm'))
        self.assertEqual(replies[-1]['view']['phase'], 'CONFIRMED')
        self.parity(calls, replies, output)

    def test_actual_business_refusals_allow_explicit_switching(self):
        answers = [v for name in SURFACES for v in (name, 'view', 'missing', 'quit')]
        # Both source-error envelopes are from existing selectors, with caller-selected missing IDs.
        answers += ['resale', 'observe_recorded_payment', 'missing', 'list-1', 'missing-pay', 'SUBMIT',
                    'quit', 'settlement', 'observe_recorded_statement', 'resale-claim', 'missing',
                    'missing-statement', 'SUBMIT', 'quit', 'booking', 'view', 'reserve-1', 'quit', 'quit']
        status, calls, replies, output, errors = self.drive(answers)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertTrue(all(set(r['error']) == {'code'} for r in replies[:4]))
        self.assertTrue(all(set(r['error']) == {'type', 'message'} for r in replies[4:6]))
        self.assertIn('view', replies[-1])
        self.parity(calls, replies, output)

    def test_exact_refusal_envelope_matrix_and_sticky_status(self):
        for name in SURFACES:
            for detail in ({'code': 'STALE_VERSION'}, {'type': 'RecordedFactNotFound', 'message': 'missing "☀"\nrecord'}):
                with self.subTest(surface=name, detail=detail):
                    client = Mock()
                    client.close.return_value = 0
                    client.request.side_effect = lambda row: dict(surface=row['surface'], operation=row['operation'],
                                                                  error=deepcopy(detail))
                    status, calls, replies, output, errors = self.drive(
                        [name, *VIEWS[name], 'quit', 'admission', 'quit', 'quit'], client=client)
                    self.assertEqual((status, errors, len(calls)), (1, '', 1))
                    self.assertEqual(replies, [dict(surface=name, operation=VIEWS[name][0], error=detail)])
                    self.assertEqual(envelopes(output), replies)
                    self.assertEqual(output.count('Surfaces:'), 3)

    def test_terminal_envelopes_fence_every_surface(self):
        for name, action in FAULT_ACTIONS:
            for kind in ('FixtureError', 'BookingInputError', 'startup'):
                with self.subTest(surface=name, operation=action[0], kind=kind):
                    client = Mock()
                    client.close.return_value = 0
                    reply = dict(surface=None if kind == 'startup' else name,
                        operation=None if kind == 'startup' else action[0],
                        error=dict(type='FixtureError' if kind == 'startup' else kind, message='terminal original'))
                    client.request.return_value = reply
                    pending = script([name, *action, *QUEUE])
                    status, calls, replies, output, errors = self.drive(client=client, stream=pending)
                    self.assertEqual((status, len(calls), replies), (2, 1, [reply]))
                    self.assertEqual(envelopes(output), [reply])
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], reply)

    def test_real_malformed_truncated_and_eof_replies_fence_every_surface(self):
        for name, action in FAULT_ACTIONS:
            for raw in (b'not-json\n', b'{partial\xff', b''):
                with self.subTest(surface=name, operation=action[0], raw=raw):
                    worker = ('import sys; sys.stdin.buffer.readline(); '
                              'sys.stdout.buffer.write(' + repr(raw) + '); sys.stdout.buffer.flush()')
                    popen = subprocess.Popen
                    def launch_worker(command, **kwargs):
                        return popen([sys.executable, '-B', '-c', worker], **kwargs)
                    pending = script([name, *action, *QUEUE])
                    with patch('ticket_operations_client.subprocess.Popen', side_effect=launch_worker) as launch:
                        client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
                        status, calls, replies, _, errors = self.drive(client=client, stream=pending)
                    launch.assert_called_once()
                    self.assertEqual((status, len(calls), replies), (2, 1, []))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertEqual(client.uncertainty.request, calls[0])
                    self.assertEqual(client.uncertainty.reply_bytes, raw)
                    self.assertIn('TicketDeskTransportUncertainty', errors)
                    self.assertIn('reply_bytes', errors)

    def test_real_write_uncertainty_and_request_interruption_fence_every_surface(self):
        for name, action in FAULT_ACTIONS:
            for fault in ('broken', 'short', 'interrupted'):
                with self.subTest(surface=name, operation=action[0], fault=fault):
                    with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
                        client = TicketOperationsClient.launch(FIXTURE, cleanup_timeout=1)
                        if fault == 'interrupted':
                            context = patch.object(client._process.stdout, 'read', side_effect=KeyboardInterrupt('exchange'))
                        else:
                            context = patch.object(client._process.stdin, 'write', **(
                                {'return_value': 1} if fault == 'short' else {'side_effect': BrokenPipeError('write')}))
                        pending = script([name, *action, *QUEUE])
                        with context as transport:
                            status, calls, replies, _, errors = self.drive(client=client, stream=pending)
                            transport.assert_called_once()
                    launch.assert_called_once()
                    self.assertEqual((status, len(calls), replies), (2, 1, []))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertIsNotNone(client.uncertainty)
                    self.assertIn('TicketDeskTransportUncertainty', errors)

    def test_input_failures_at_menu_and_every_surface_fence_queued_navigation(self):
        for name in (None, *SURFACES):
            for failure in (EOFError('end'), KeyboardInterrupt('interrupt'), OSError('input')):
                with self.subTest(surface=name, failure=type(failure).__name__):
                    prefix = [] if name is None else [name, *VIEWS[name]]
                    pending = script([*prefix, *QUEUE])
                    class BrokenInput:
                        reads = 0
                        def readline(self):
                            if self.reads < len(prefix):
                                self.reads += 1
                                return pending.readline()
                            if self.reads == len(prefix):
                                self.reads += 1
                                if isinstance(failure, EOFError):
                                    return ''
                                raise failure
                            return pending.readline()
                    status, calls, replies, _, errors = self.drive(stream=BrokenInput())
                    self.assertEqual((status, len(calls)), (2, 0 if name is None else 1))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertIn(type(failure).__name__, errors)
                    if name is not None:
                        self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], replies[-1])

    def test_display_failures_fence_all_surfaces_even_with_broken_diagnostics(self):
        class BrokenOutput(io.StringIO):
            def write(self, text):
                if text.startswith('desk='):
                    raise BrokenPipeError('display')
                return super().write(text)
        class BrokenDiagnostics(io.StringIO):
            def write(self, text):
                raise OSError('diagnostics')
        for name, action in FAULT_ACTIONS:
            for broken_diagnostics in (False, True):
                with self.subTest(surface=name, operation=action[0], diagnostics=broken_diagnostics):
                    pending = script([name, *action, *QUEUE])
                    status, calls, replies, _, errors = self.drive(stream=pending,
                        output=BrokenOutput(), errors=BrokenDiagnostics() if broken_diagnostics else io.StringIO())
                    self.assertEqual((status, len(calls), len(replies)), (2, 1, 1))
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    if not broken_diagnostics:
                        self.assertEqual(json.loads(errors.split('FENCED: ')[1].splitlines()[0])['last_reply'], replies[-1])
        class BrokenMenu(io.StringIO):
            def write(self, text):
                raise OSError('menu output')
        status, calls, _, _, errors = self.drive(QUEUE, output=BrokenMenu())
        self.assertEqual((status, calls), (2, []))
        self.assertIn('menu output', errors)

    def test_unexpected_surface_results_and_exceptions_stop_without_more_input(self):
        for name in SURFACES:
            for fault in (None, False, -1, 3, '0', RuntimeError('surface failed'), KeyboardInterrupt('surface')):
                with self.subTest(surface=name, fault=fault):
                    pending = script([name, *QUEUE])
                    behavior = {'side_effect': fault} if isinstance(fault, BaseException) else {'return_value': fault}
                    with patch.object(console._SURFACES[name], 'run_console', **behavior) as delegate:
                        status, calls, _, _, errors = self.drive(stream=pending)
                    self.assertEqual((status, calls), (2, []))
                    delegate.assert_called_once()
                    self.assertEqual(pending.read(), script(QUEUE).read())
                    self.assertIn('FENCED:', errors)

    def test_cli_arguments_import_launch_and_cleanup_failures(self):
        for args in ([], ['--fixture', str(FIXTURE)], *(
                ['--fixture', str(FIXTURE), '--cleanup-timeout', value] for value in ('0', '-1', 'nan', 'inf'))):
            with patch('sys.stderr', io.StringIO()), patch('ticket_operations_client.subprocess.Popen') as launch:
                with self.assertRaises(SystemExit) as error:
                    console.main(args)
                self.assertEqual(error.exception.code, 2)
                launch.assert_not_called()
        probe = subprocess.run([sys.executable, '-B', '-c',
            "from unittest.mock import patch\nwith patch('subprocess.Popen', side_effect=AssertionError('import launched')):\n import shared_ticket_console\n"],
            cwd=HERE, capture_output=True, text=True, env=os.environ.copy(), timeout=10)
        self.assertEqual((probe.returncode, probe.stdout, probe.stderr), (0, '', ''))
        for failure in (OSError('launch failed'), KeyboardInterrupt('launch interrupted')):
            with patch.object(console.TicketOperationsClient, 'launch', side_effect=failure) as launch, \
                    patch('sys.stderr', io.StringIO()) as errors:
                self.assertEqual(console.main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']), 2)
            launch.assert_called_once()
            self.assertIn('FENCED:', errors.getvalue())
        for initial in (0, 1, 2):
            for cleanup in (0, 7, OSError('close failed'), KeyboardInterrupt('close interrupted')):
                with self.subTest(status=initial, cleanup=cleanup):
                    client = Mock()
                    if isinstance(cleanup, BaseException):
                        client.close.side_effect = cleanup
                    else:
                        client.close.return_value = cleanup
                    with patch.object(console, 'run_console', return_value=initial):
                        status, calls, _, _, _ = self.drive(client=client)
                    expected = 2 if isinstance(cleanup, BaseException) else (initial or int(cleanup != 0))
                    self.assertEqual((status, calls), (expected, []))

    def test_documented_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
            '--fixture', str(FIXTURE), '--cleanup-timeout', '1'], cwd=ROOT, input=JOURNEY.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        replies = envelopes(result.stdout)
        self.assertEqual(len(replies), 18)
        self.assertEqual({r['surface'] for r in replies}, set(SURFACES))
        self.assertEqual(replies[-1]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[14]['view']['phase'], 'CONFIRMED')
        self.assertEqual(replies[16]['view']['right']['holder_role'], 'buyer-2')

    def test_resale_start_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'shared_ticket_console.py'),
            '--fixture', str(INPUTS), '--cleanup-timeout', '1'], cwd=ROOT, input=START_RESALE.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        replies = envelopes(result.stdout)
        self.assertEqual(len(replies), 21)
        self.assertEqual(replies[17]['view']['claim']['distributed_cash'], 8000)
        self.assertEqual(replies[-2]['view']['phase'], 'LISTED')
        self.assertEqual(replies[-1]['view']['right']['holder_role'], 'buyer-1')


if __name__ == '__main__':
    unittest.main()
