"""Source-informed console composition, exact service envelopes and local children."""

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

from settlement_console import main, run_console
from ticket_operations_client import TicketOperationsClient
from ticket_operations_cli import dispatch_request
from ticket_operations_fixture import load_fixture
from settlement_fsm import SettlementError
from statement_source import StatementSourceError
from cancel_acceptance_source import CancelAcceptanceSourceError
from settlement_input_adapter import SettlementInputSourceError
from test_ticket_settlement_controls import settlement_flags

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_settlement_fact_inputs_session.json'
JOURNEY = HERE / 'fixtures/settlement_console_journey.txt'
STATEMENTS = HERE / 'fixtures/ticket_operations_statement_session.json'
REFUNDS = HERE / 'fixtures/ticket_operations_refund_session.json'
VIEW = ['view', 'claim-2']
COMMIT = ['commit', 'claim-2', 'initial', '6000', '5500', '200', '100', '100',
          '100', '"synthetic"', 'manual-commit', 'SUBMIT']
OBSERVE = ['observe_statement', 'claim-2', 'later', '4001', '3801', '200', '0', '0',
           '0', 'null', 'later', 'SUBMIT']
DISTRIBUTE = ['distribute', 'claim-2', '["platform","organizer"]', 'distribution', 'SUBMIT']
REFUND = ['bind_refund', 'claim-2', 'refund', '4000', 'buyer-3', 'synthetic', 'refund', 'SUBMIT']
ACCEPT = ['observe_mock_cancel_acceptance', 'claim-2', 'accept', '1000', 'accept', 'SUBMIT']
INPUTS = HERE / 'fixtures/ticket_operations_settlement_inputs_session.json'
START_BOOKING = HERE / 'fixtures/settlement_console_start_booking.txt'
GUIDED_BOOKING = HERE / 'fixtures/settlement_console_guided_booking.txt'
POLICY = dict(kind='PRIMARY_FEE_BPS', fee_bps=500, residual_payee='organizer', fee_payee='platform')
INIT = ['initiate_from_booking', 'claim-2', 'reserve-2', 'explicit-booking-trade',
        'explicit-debtor', json.dumps(POLICY), 'booking-input', 'SUBMIT']
AUTH = ['authorize', 'claim-2', 'auth-input', 'SUBMIT']
CAPTURE = ['capture', 'claim-2', 'capture-input', 'SUBMIT']


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


def guided_init(policy):
    return [*INIT[:5], 'guided', policy['kind'], str(policy['fee_bps']),
            policy['residual_payee'], policy['fee_payee'], *INIT[-2:]]


def guided_order(order, key):
    return ['distribute', 'claim-2', 'guided', str(len(order)), *order, key, 'SUBMIT']


class SettlementConsoleTests(unittest.TestCase):
    def drive(self, answers, *, fixture=FIXTURE, client=None, stream=None, unchanged=()):
        output, errors = io.StringIO(), io.StringIO()
        if client is None:
            client = TicketOperationsClient.launch(fixture, cleanup_timeout=1)
        calls, replies = [], []
        original = client.request
        # Test-only source observations bracket the console, outside its request stream.
        before = [original(row) for row in unchanged]
        original_close = client.close

        def checked_close():
            try:
                self.assertEqual([original(row) for row in unchanged], before)
            finally:
                child_status = original_close()
            return child_status

        def record(row):
            calls.append(deepcopy(row))
            reply = original(row)
            replies.append(deepcopy(reply))
            return reply

        with patch('settlement_console.TicketOperationsClient.launch', return_value=client) as launch, \
                patch.object(client, 'request', side_effect=record), \
                patch.object(client, 'close', wraps=checked_close) as close, \
                patch('sys.stdin', stream if stream is not None else script(answers)), \
                patch('sys.stdout', output), patch('sys.stderr', errors):
            status = main(['--fixture', str(fixture), '--cleanup-timeout', '1'])
        launch.assert_called_once_with(fixture, cleanup_timeout=1)
        close.assert_called_once_with()
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)
        self.assertIsNotNone(client._process.poll())
        return status, calls, replies, output.getvalue(), errors.getvalue()

    def parity(self, calls, replies, output, fixture=FIXTURE):
        control = load_fixture(fixture)
        for row, reply in zip(calls, replies, strict=True):
            try:
                expected = dispatch_request(control, row)
            except (SettlementError, StatementSourceError, CancelAcceptanceSourceError,
                    SettlementInputSourceError) as error:
                detail = ({'code': error.code} if isinstance(error, SettlementError) else
                          {'type': type(error).__name__, 'message': str(error)})
                expected = dict(surface='settlement', operation=row['operation'], error=detail)
            self.assertEqual(reply, expected)
            self.assertEqual(row['surface'], 'settlement')
            self.assertEqual(set(row), {'surface', 'operation', 'arguments'})
        # Also prove the complete printed envelope stream equals the received stream.
        self.assertEqual([json.loads(s) for s in re.findall(r'desk=(\{[^\n]+\})', output)], replies)
        self.assertIn('UNDETERMINED — Astra/User', output)
        self.assertIn('UNDETERMINED — User/designated advisers', output)
        self.assertEqual([json.loads(s) for s in re.findall(r'proposed=(\{[^\n]+\})', output)],
                         [r for r in calls if r['operation'] != 'view'])

    def summaries(self, replies, output):
        for reply in replies:
            if 'error' in reply:
                continue
            snapshot = 'receipt' in reply
            label = 'Action snapshot' if snapshot else 'Current service observation'
            view = reply['receipt']['settlement'] if snapshot else reply['view']
            claim = view['claim']
            if claim is None:
                self.assertIn(label + ' claim data unavailable (claim=null).', output)
                continue
            for name, fields in (
                ('Cash', ('confirmed_cash', 'distributed_cash', 'undistributed_cash')),
                ('Statement position', ('receivable_open', 'non_cash_accounted')),
                ('Refund', ('refund_face', 'refund_accepted', 'refund_outstanding',
                            'refund_bearer_policy', 'distribution_blocked')),
                ('PG adjustment', ('pg_adjustment_outstanding',)),
                ('Distribution', ('distribution_order',)),
            ):
                self.assertIn(label + ' ' + name + '=' + json.dumps(
                    {k: claim[k] for k in fields}, sort_keys=True), output)
            for obligation in claim['obligations']:
                self.assertIn(label + ' Allocation=' + json.dumps(obligation, sort_keys=True), output)
            for key in ('funds_executed', 'bank_debit_observed', 'external_return_closed', 'durable'):
                self.assertIs(view[key], False)

    def test_live_journey(self):
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(JOURNEY.read_text().splitlines())
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([r['operation'] for r in calls], ['commit', 'view', 'observe_statement',
            'view', 'distribute', 'view', 'bind_refund', 'view', 'observe_mock_cancel_acceptance',
            'view', 'commit', 'view'])
        source = HERE / 'fixtures/ticket_operations_settlement_fact_inputs_journey.jsonl'
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        self.assertEqual(calls[0::2], [rows[i] for i in (0, 2, 4, 5, 6, 0)])
        self.parity(calls, replies, output)
        self.summaries(replies, output)
        self.assertEqual(replies[1]['view']['claim']['receivable_open'], 4001)
        current = replies[9]['view']['claim']
        self.assertEqual({k: current[k] for k in ('confirmed_cash', 'refund_outstanding',
            'pg_adjustment_outstanding')}, dict(confirmed_cash=9301, refund_outstanding=3000,
                                               pg_adjustment_outstanding=1000))
        self.assertEqual(current['refund_bearer_policy'], 'REQUESTER')
        self.assertFalse(current['distribution_blocked'])
        self.assertEqual(replies[10]['receipt'], replies[0]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual(replies[10]['receipt']['settlement']['claim']['confirmed_cash'], 5500)
        self.assertEqual(replies[11]['view']['claim'], current)
        self.assertIn('Action snapshot: {"applied": null, "duplicate": true}', output)
        self.assertIn('synthetic cancellation acceptance; not real refund completion', output)

    def test_insufficient_cash_keeps_service_obligations_and_explicit_order(self):
        # Console composition only: existing settlement tests own the arithmetic predicates.
        status, calls, replies, output, errors = self.drive(COMMIT + DISTRIBUTE + VIEW + ['quit'])
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(calls[1]['arguments']['order'], ['platform', 'organizer'])
        self.parity(calls, replies, output)
        self.summaries(replies, output)
        claim = replies[-1]['view']['claim']
        self.assertGreater(claim['obligations'][0]['outstanding'], 0)
        self.assertEqual([o['face'] for o in claim['obligations']],
                         [o['face'] for o in replies[0]['receipt']['settlement']['claim']['obligations']])

    def test_over_refund_acceptance_and_conflicting_keys_preserve_current_view(self):
        over_refund = REFUND.copy()
        over_refund[2:4] = ['too-much', '10002']
        over_refund[-2] = 'too-much'
        over_accept = ACCEPT.copy()
        over_accept[2:5] = ['too-much', '4001', 'too-much-accept']
        conflict = ACCEPT.copy()
        conflict[3] = '1001'
        sequence = COMMIT + REFUND + ACCEPT + VIEW + over_refund + VIEW + over_accept + VIEW + conflict + VIEW
        status, calls, replies, output, errors = self.drive(sequence + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual([r['error']['code'] for r in replies if 'error' in r],
                         ['REFUND_CEILING', 'REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION', 'IDEMPOTENCY_CONFLICT'])
        self.assertTrue(all(replies[i]['view'] == replies[3]['view'] for i in (5, 7, 9)))
        self.parity(calls, replies, output)

    def test_recorded_statement_and_acceptance_selectors_and_source_refusal(self):
        statements = ['commit_recorded_statement', 'claim-2', 'statement-1', 'recorded-commit', 'SUBMIT',
                      'observe_recorded_statement', 'claim-2', 'statement-2', 'recorded-later', 'SUBMIT']
        status, calls, replies, output, errors = self.drive(statements + VIEW + ['quit'], fixture=STATEMENTS)
        self.assertEqual((status, errors), (0, ''))
        self.parity(calls, replies, output, STATEMENTS)
        self.summaries(replies, output)
        answers = ['bind_refund', 'claim-1', 'r', '4000', 'buyer', 'synthetic', 'r', 'SUBMIT',
                   'observe_recorded_cancel_acceptance', 'claim-1', 'missing', 'missing', 'SUBMIT',
                   'observe_recorded_cancel_acceptance', 'claim-1', 'acceptance-1', 'accept', 'SUBMIT',
                   'view', 'claim-1', 'quit']
        status, calls, replies, output, errors = self.drive(answers, fixture=REFUNDS)
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(replies[1]['error']['type'], 'CancelAcceptanceNotFound')
        self.assertIn('receipt', replies[2])
        self.parity(calls, replies, output, REFUNDS)
        self.summaries(replies, output)

    def test_booking_start_journey_one_child_source_owned_amount_and_no_ticket_effects(self):
        control = load_fixture(INPUTS)
        for identity in ('claim-2', 'resale-claim'):
            with self.assertRaises(SettlementError) as error:
                control.settlement.view(identity)
            self.assertEqual(error.exception.code, 'UNKNOWN_SETTLEMENT')
        probes = [dict(surface=surface, operation=op, arguments={field: identity})
                  for surface, op, field, identity in (
                      ('booking', 'view', 'reservation_id', 'reserve-2'),
                      ('resale', 'view_right', 'right_id', 'issue-1'),
                      ('admission', 'view', 'right_id', 'issue-1'))]
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(
                START_BOOKING.read_text().splitlines(), fixture=INPUTS, unchanged=probes)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual([r['operation'] for r in calls], [
            op for action in ('initiate_from_booking', 'authorize', 'capture',
                'commit_recorded_statement', 'observe_recorded_statement', 'distribute',
                'bind_refund', 'observe_mock_cancel_acceptance', 'initiate_from_booking')
            for op in (action, 'view')])
        self.parity(calls, replies, output, INPUTS)
        self.summaries(replies, output)
        self.assertEqual(calls[0]['arguments'], dict(settlement_id='claim-2',
            reservation_id='reserve-2', trade_id='explicit-booking-trade',
            debtor_role='explicit-debtor', policy=POLICY, idempotency_key='booking-input'))
        self.assertEqual([replies[i]['view']['phase'] for i in (1, 3, 5, 7)],
                         ['INITIATED', 'AUTHORIZED', 'CAPTURED', 'COMMITTED'])
        for i in (0, 2):
            self.assertIsNone(replies[i]['receipt']['settlement']['claim'])
        self.assertEqual(replies[4]['receipt']['settlement']['claim']['confirmed_cash'], 0)
        for reply in replies:
            value = reply['view'] if 'view' in reply else reply['receipt']['settlement']
            self.assertEqual((value['gross'], value['currency']), (10001, 'KRW'))
            settlement_flags(self, value)
        claim = replies[-1]['view']['claim']
        self.assertEqual((claim['confirmed_cash'], claim['distributed_cash'],
                          claim['refund_outstanding'], claim['pg_adjustment_outstanding']),
                         (9301, 9301, 3000, 1000))
        self.assertEqual(replies[-2]['receipt'], replies[0]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual(replies[-1]['view'], replies[-3]['view'])

    def test_missing_sources_and_invalid_transition_continue_only_when_selected(self):
        for kind in ('booking', 'resale'):
            with self.subTest(source=kind):
                missing = INIT.copy()
                missing[0], missing[2] = 'initiate_from_' + kind, 'missing'
                # Source errors leave the key free; only the subsequent explicit booking action uses it.
                status, calls, replies, output, errors = self.drive(
                    missing + INIT + VIEW + CAPTURE + VIEW + AUTH + VIEW + ['quit'], fixture=INPUTS)
                self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
                self.parity(calls, replies, output, INPUTS)
                self.assertEqual(replies[0]['error'], dict(type='SettlementInputSourceError',
                    message='settlement input view failed'))
                self.assertEqual(replies[3]['error'], dict(code='ILLEGAL_TRANSITION'))
                self.assertEqual(replies[2]['view'], replies[4]['view'])
                self.assertEqual(replies[-1]['view']['phase'], 'AUTHORIZED')

    def test_guided_booking_journey_matches_raw_requests_results_and_ticket_observations(self):
        raw = self.drive(START_BOOKING.read_text().splitlines(), fixture=INPUTS)
        probes = [dict(surface=surface, operation=op, arguments={field: identity})
                  for surface, op, field, identity in (
                      ('booking', 'view', 'reservation_id', 'reserve-2'),
                      ('resale', 'view_right', 'right_id', 'issue-1'),
                      ('admission', 'view', 'right_id', 'issue-1'))]
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            status, calls, replies, output, errors = self.drive(
                GUIDED_BOOKING.read_text().splitlines(), fixture=INPUTS, unchanged=probes)
        launch.assert_called_once()
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual((status, calls, replies), raw[:3])
        self.parity(calls, replies, output, INPUTS)
        self.summaries(replies, output)
        self.assertEqual(replies[11]['view']['claim']['distributed_cash'], 9301)

    def test_guided_policy_boundaries_and_service_refusals_match_raw(self):
        policies = [(POLICY | {'fee_bps': bps}, None if 0 <= bps <= 10000 else 'POLICY_FEE_BPS')
                    for bps in (0, 1, 9999, 10000, -1, 10001)]
        policies += [(POLICY | {'fee_payee': 'organizer'}, 'POLICY_PAYEE_COLLISION'),
                     (POLICY | {'kind': 'UNSUPPORTED'}, 'POLICY_KIND')]
        for policy, code in policies:
            with self.subTest(policy=policy):
                tail = ['quit']
                if code is None:
                    # The caller explicitly chooses the sole nonzero payee at endpoints.
                    order = (['organizer'] if policy['fee_bps'] == 0 else
                             ['platform'] if policy['fee_bps'] == 10000 else ['platform', 'organizer'])
                    tail = AUTH + CAPTURE + ['commit_recorded_statement', 'claim-2',
                        'statement-1', 'commit', 'SUBMIT'] + guided_order(order, 'dist') + VIEW + tail
                raw = INIT.copy()
                raw[5] = json.dumps(policy)
                baseline = self.drive(raw + tail, fixture=INPUTS)
                status, calls, replies, output, errors = self.drive(guided_init(policy) + tail, fixture=INPUTS)
                self.assertEqual((status, calls, replies), baseline[:3])
                self.assertEqual(calls[0]['arguments']['policy'], policy)
                self.assertIs(type(calls[0]['arguments']['policy']['fee_bps']), int)
                self.assertEqual((status, errors), (1, 'Child exit status=1\n') if code else (0, ''))
                if code:
                    self.assertEqual(replies[0]['error'], {'code': code})
                else:
                    self.assertEqual(calls[-2]['arguments']['order'], order)
                self.parity(calls, replies, output, INPUTS)

    def test_guided_order_preserves_empty_duplicates_extra_payees_and_frozen_order(self):
        cases = [([], 'empty'), (['platform', 'platform'], 'duplicate'),
                 (['platform', 'organizer', 'extra'], 'extra'),
                 (['platform', 'organizer'], 'duplicate'),
                 (['platform', 'organizer'], 'accepted'),
                 (['organizer', 'platform'], 'changed'),
                 (['organizer', 'platform'], 'accepted'),
                 (['platform', 'organizer'], 'accepted')]
        guided = COMMIT + VIEW
        raw = COMMIT + VIEW
        for order, key in cases:
            guided += guided_order(order, key) + VIEW
            raw += ['distribute', 'claim-2', json.dumps(order), key, 'SUBMIT'] + VIEW
        baseline = self.drive(raw + ['quit'])
        status, calls, replies, output, errors = self.drive(guided + ['quit'])
        self.assertEqual((status, calls, replies), baseline[:3])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual([r['arguments']['order'] for r in calls[2::2]], [o for o, _ in cases])
        self.assertEqual([r['error']['code'] for r in replies if 'error' in r], [
            'DISTRIBUTION_ORDER_MISMATCH', 'DISTRIBUTION_ORDER_DUPLICATE',
            'DISTRIBUTION_ORDER_MISMATCH', 'IDEMPOTENCY_CONFLICT',
            'DISTRIBUTION_ORDER_FROZEN', 'IDEMPOTENCY_CONFLICT'])
        self.assertTrue(all(replies[i]['view'] == replies[1]['view'] for i in (3, 5, 7, 9)))
        self.assertTrue(all(replies[i]['view'] == replies[11]['view'] for i in (13, 15, 17)))
        self.assertEqual(replies[16]['receipt'], replies[10]['receipt'] | dict(duplicate=True, applied=None))
        self.parity(calls, replies, output)

    def test_guided_malformed_fields_discard_without_submission_or_defaults(self):
        actions = []
        for op in ('initiate_from_booking', 'initiate_from_resale'):
            action = guided_init(POLICY)
            action[0] = op
            actions += [action[:i] + [value] for i, values in (
                (6, ('', ' PRIMARY_FEE_BPS')), (8, ('', ' organizer')),
                (9, ('', 'platform ')), (10, ('', ' key')),
                (7, ('', '1.0', '1e3', 'true', '+1', ' 0', '0 ', '−1', '9' * 5000)))
                for value in values]
        order = guided_order(['platform', 'organizer'], 'key')
        actions += [order[:i] + [value] for i, values in (
            (3, ('', '-1', '-0', '+2', '2.0', 'true', ' 2', '9' * 5000)),
            (4, ('', ' platform')), (5, ('', 'organizer ')), (6, ('',))) for value in values]
        for action in actions:
            with self.subTest(field=action[-2] if len(action) > 1 else action):
                client, output = Mock(), io.StringIO()
                errors = io.StringIO()
                status = run_console(client, input_stream=script(action + ['quit']),
                                     output_stream=output, error_stream=errors)
                self.assertEqual((status, errors.getvalue()), (0, ''))
                client.request.assert_not_called()
                self.assertIn('input_error=', output.getvalue())
                self.assertNotIn('proposed=', output.getvalue())

    def test_guided_declines_do_not_reuse_approval(self):
        resale = guided_init(POLICY)
        resale[0] = 'initiate_from_resale'
        actions = [guided_init(POLICY), resale, guided_order(['platform', 'organizer'], 'dist')]
        answers = INIT + [v for action in actions for v in [*action[:-1], 'submit']] + ['quit']
        status, calls, _, output, errors = self.drive(answers, fixture=INPUTS)
        self.assertEqual((status, len(calls), errors), (0, 1, ''))
        self.assertEqual(output.count('Declined; no request sent.'), len(actions))
        self.assertEqual(output.count('proposed='), len(actions) + 1)

    def test_guided_eof_at_each_composition_and_confirmation_boundary_closes_once(self):
        resale = guided_init(POLICY)
        resale[0] = 'initiate_from_resale'
        for action, start in ((guided_init(POLICY), 6), (resale, 6),
                              (guided_order(['platform', 'organizer'], 'dist'), 3)):
            for end in range(start, len(action)):
                with self.subTest(operation=action[0], end=end):
                    status, calls, _, _, errors = self.drive(action[:end], fixture=INPUTS)
                    self.assertEqual((status, calls), (2, []))
                    self.assertIn('EOFError', errors)

    def test_guided_transport_uncertainty_fences_before_queued_action_and_closes_once(self):
        resale = guided_init(POLICY)
        resale[0] = 'initiate_from_resale'
        for action in (guided_init(POLICY), resale, guided_order(['platform', 'organizer'], 'dist')):
            for raw in (b'not-json\n', b'{partial\xff', b''):
                with self.subTest(operation=action[0], reply=raw):
                    worker = ('import sys; sys.stdin.buffer.readline(); '
                              'sys.stdout.buffer.write(' + repr(raw) + '); sys.stdout.buffer.flush()')
                    process = subprocess.Popen([sys.executable, '-B', '-c', worker], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
                    client = TicketOperationsClient(process, cleanup_timeout=1)
                    pending = script(action + VIEW + ['quit'])
                    status, calls, replies, _, errors = self.drive([], stream=pending, client=client)
                    self.assertEqual((status, len(calls), replies), (2, 1, []))
                    self.assertEqual(pending.read(), script(VIEW + ['quit']).read())
                    self.assertEqual(client.uncertainty.request, calls[0])
                    self.assertEqual(client.uncertainty.reply_bytes, raw)
                    self.assertIn('TicketDeskTransportUncertainty', errors)

    def test_guided_booking_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'settlement_console.py'),
            '--fixture', str(INPUTS), '--cleanup-timeout', '1'], input=GUIDED_BOOKING.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        replies = [json.loads(s) for s in re.findall(r'desk=(\{[^\n]+\})', result.stdout)]
        self.assertEqual(len(replies), 18)
        self.assertEqual(replies[11]['view']['claim']['distributed_cash'], 9301)

    def test_policy_syntax_errors_discard_selection_without_any_submission(self):
        bad = ('{', '', 'null', '[]', '1', 'true', '"policy"',
               '{"fee_bps":1,"fee_bps":2}', '{"nested":{"k":1,"k":2}}',
               '{"fee_bps":NaN}', '{"fee_bps":Infinity}', '{"fee_bps":-Infinity}',
               '{"fee_bps":1e9999}')
        for op in ('initiate_from_booking', 'initiate_from_resale'):
            for value in bad:
                with self.subTest(operation=op, policy=value):
                    client, output, errors = Mock(), io.StringIO(), io.StringIO()
                    status = run_console(client, input_stream=script(
                        [op, *INIT[1:5], value, 'quit']), output_stream=output, error_stream=errors)
                    self.assertEqual((status, errors.getvalue()), (0, ''))
                    client.request.assert_not_called()
                    self.assertIn('input_error=', output.getvalue())
                    self.assertNotIn('proposed=', output.getvalue())

    def test_policy_objects_are_forwarded_unchanged_and_retained_keys_conflict(self):
        for policy, code in (({}, 'POLICY_FIELDS'), (POLICY | {'extra': 'explicit'}, 'POLICY_FIELDS'),
                (POLICY | {'kind': 'UNSUPPORTED'}, 'POLICY_KIND'),
                (POLICY | {'fee_bps': 10001}, 'POLICY_FEE_BPS'),
                (POLICY | {'fee_bps': True}, 'POLICY_FEE_BPS'),
                (POLICY | {'fee_bps': 0.5}, 'POLICY_FEE_BPS'),
                (POLICY | {'fee_payee': 'organizer'}, 'POLICY_PAYEE_COLLISION')):
            with self.subTest(policy=policy):
                invalid = INIT.copy()
                invalid[5] = json.dumps(policy)
                fresh = INIT.copy()
                fresh[-2] = 'fresh-init'
                conflict = INIT.copy()
                conflict[3] = 'changed-trade'
                conflict[-2] = 'fresh-init'
                status, calls, replies, output, errors = self.drive(
                    invalid + INIT + fresh + AUTH + CAPTURE + VIEW + fresh + conflict + VIEW + ['quit'],
                    fixture=INPUTS)
                self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
                self.assertEqual(calls[0]['arguments']['policy'], policy)
                self.assertEqual(replies[0]['error'], dict(code=code))
                self.assertEqual(replies[1]['error'], dict(code='IDEMPOTENCY_CONFLICT'))
                self.assertEqual(replies[-2]['error'], dict(code='IDEMPOTENCY_CONFLICT'))
                self.assertEqual(replies[-3]['receipt'], replies[2]['receipt'] | dict(duplicate=True, applied=None))
                self.assertEqual(replies[-1]['view'], replies[5]['view'])
                self.assertEqual(replies[-1]['view']['phase'], 'CAPTURED')
                self.parity(calls, replies, output, INPUTS)

    def test_every_mutation_requires_literal_single_use_submit(self):
        resale = INIT.copy()
        resale[0] = 'initiate_from_resale'
        resale[2] = 'list-1'
        actions = [INIT, resale, AUTH, CAPTURE, COMMIT, OBSERVE, DISTRIBUTE, REFUND, ACCEPT,
            ['commit_recorded_statement', 'claim-2', 'statement-1', 'key', 'SUBMIT'],
            ['observe_recorded_statement', 'claim-2', 'statement-2', 'key', 'SUBMIT'],
            ['observe_recorded_cancel_acceptance', 'claim-2', 'source', 'key', 'SUBMIT']]
        answers = [v for action in actions for v in [*action[:-1], 'submit']]
        status, calls, _, output, errors = self.drive(answers + ['quit'])
        self.assertEqual((status, calls, errors), (0, [], ''))
        self.assertEqual(output.count('Declined; no request sent.'), len(actions))
        status, calls, _, output, errors = self.drive(COMMIT + OBSERVE[:-1] + ['no', 'quit'])
        self.assertEqual((status, len(calls), errors), (0, 1, ''))
        self.assertEqual(json.loads(output.split('proposed=')[1].splitlines()[0]), calls[0])
        for action in (INIT, resale, AUTH, CAPTURE):
            with self.subTest(action=action[0]):
                # Approval of one selection cannot authorize the next transition.
                status, calls, _, _, errors = self.drive(
                    INIT + action[:-1] + ['no', 'quit'], fixture=INPUTS)
                self.assertEqual((status, len(calls), errors), (0, 1, ''))

    def test_invalid_syntax_never_submits_or_invents_defaults(self):
        bad_inputs = [COMMIT[:i] + [v] for i, v in (
            (1, ''), (3, '1.0'), (4, '1e3'), (5, 'true'), (6, ''), (7, ' 1'),
            (8, '+1'), (9, ''), (9, 'false'), (9, '{}'), (10, ''))]
        bad_inputs += [['distribute', 'claim-2', value] for value in ('null', '"platform"', '[1]', '{', '')]
        for answers in bad_inputs:
            with self.subTest(answers=answers):
                client, output = Mock(), io.StringIO()
                status = run_console(client, input_stream=script(answers + ['quit']),
                                     output_stream=output, error_stream=io.StringIO())
                self.assertEqual(status, 0)
                client.request.assert_not_called()
                self.assertIn('input_error=', output.getvalue())

    def test_economic_validation_and_duplicate_order_are_left_to_service(self):
        duplicate = DISTRIBUTE.copy()
        duplicate[2] = '["platform", "platform"]'
        negative = ACCEPT.copy()
        negative[3] = '-1'
        status, calls, replies, output, errors = self.drive(COMMIT + duplicate + negative + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(calls[1]['arguments']['order'], ['platform', 'platform'])
        self.assertEqual(calls[2]['arguments']['amount'], -1)
        self.assertIn('error', replies[1])
        self.assertIn('error', replies[2])
        self.parity(calls, replies, output)

    def test_null_claim_has_no_manufactured_cash(self):
        with tempfile.TemporaryDirectory() as temp:
            value = json.loads(FIXTURE.read_text())
            value['setup'] = [r for r in value['setup'] if not (
                r['machine'] == 'settlement' and r['subject_id'] == 'claim-2'
                and r['operation'] in {'authorize', 'capture'})]
            fixture = Path(temp) / 'initiated.json'
            fixture.write_text(json.dumps(value))
            status, calls, replies, output, errors = self.drive(VIEW + ['quit'], fixture=fixture)
            self.assertEqual((status, errors), (0, ''))
            self.assertIsNone(replies[0]['view']['claim'])
            self.parity(calls, replies, output, fixture)
            self.summaries(replies, output)
            self.assertNotIn('Cash=', output)

    def test_large_integer_is_forwarded_without_float_conversion(self):
        answers = REFUND.copy()
        answers[3] = '999999999999'
        status, calls, replies, output, errors = self.drive(answers + ['quit'])
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        self.assertEqual(calls[0]['arguments']['amount'], 999999999999)
        self.assertIn('"amount": 999999999999', output)
        self.assertNotIn('999999999999.0', output)
        self.parity(calls, replies, output)

    def test_eof_interruption_and_input_failure_fence_and_close(self):
        for failure in (None, KeyboardInterrupt('interrupted'), OSError('input failed')):
            lines = script(COMMIT)

            class BrokenInput:
                def readline(self):
                    line = lines.readline()
                    if line:
                        return line
                    if failure is not None:
                        raise failure
                    return ''

            status, calls, replies, _, errors = self.drive([], stream=BrokenInput())
            self.assertEqual((status, len(calls)), (2, 1))
            self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], replies[0])
        status, calls, _, _, errors = self.drive(COMMIT[:-1])
        self.assertEqual((status, calls), (2, []))
        self.assertIn('EOFError', errors)

    def test_terminal_envelopes_stop_before_queued_action(self):
        for detail, surface, op in (({'type': 'FixtureError', 'message': 'bad fixture'}, None, None),
                ({'type': 'BookingInputError', 'message': 'bad input'}, 'settlement', 'commit')):
            client = Mock()
            reply = dict(surface=surface, operation=op, error=detail)
            client.request.return_value = reply
            output, errors = io.StringIO(), io.StringIO()
            status = run_console(client, input_stream=script(COMMIT + VIEW + ['quit']),
                                 output_stream=output, error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            self.assertIn('desk=' + json.dumps(reply, sort_keys=True), output.getvalue())
            self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / 'bad.json'
            bad.write_text('{')
            status, calls, _, _, errors = self.drive(COMMIT + VIEW, fixture=bad)
            self.assertEqual((status, len(calls)), (2, 1))
            self.assertIn('FENCED:', errors)

    def test_real_transport_uncertainty_does_not_resubmit_or_consume_queued_actions(self):
        for raw in (b'{partial\xff', b'not-json\n'):
            worker = ('import sys; sys.stdin.buffer.readline(); '
                      'sys.stdout.buffer.write(' + repr(raw) + '); sys.stdout.buffer.flush()')
            process = subprocess.Popen([sys.executable, '-B', '-c', worker], stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
            client = TicketOperationsClient(process, cleanup_timeout=1)
            pending = script(COMMIT + COMMIT + VIEW + ['quit'])
            status, calls, replies, _, errors = self.drive([], stream=pending, client=client)
            self.assertEqual((status, len(calls), replies), (2, 1, []))
            self.assertEqual(pending.readline(), 'commit\n')
            self.assertEqual(client.uncertainty.reply_bytes, raw)
            self.assertEqual(client.uncertainty.request, calls[0])
            self.assertIn('TicketDeskTransportUncertainty', errors)
            self.assertIn('reply_bytes', errors)
            self.assertIn('FixtureError', errors)

    def test_output_failure_retains_reply_even_if_diagnostics_fail(self):
        reply = dict(surface='settlement', operation='view', view={'claim': None})

        class BrokenOutput(io.StringIO):
            def write(self, text):
                if text.startswith('desk='):
                    raise BrokenPipeError('display failed')
                return super().write(text)

        class BrokenDiagnostics(io.StringIO):
            def write(self, text):
                raise OSError('diagnostics failed')

        for errors in (io.StringIO(), BrokenDiagnostics()):
            client = Mock()
            client.request.return_value = reply
            status = run_console(client, input_stream=script(VIEW + VIEW + ['quit']),
                                 output_stream=BrokenOutput(), error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once()
            if not isinstance(errors, BrokenDiagnostics):
                self.assertEqual(json.loads(errors.getvalue().split('FENCED: ')[1])['last_reply'], reply)

    def test_request_interruption_is_terminal(self):
        client = Mock()
        client.request.side_effect = KeyboardInterrupt('exchange interrupted')
        errors = io.StringIO()
        status = run_console(client, input_stream=script(COMMIT + COMMIT + ['quit']),
                             output_stream=io.StringIO(), error_stream=errors)
        self.assertEqual(status, 2)
        client.request.assert_called_once()
        self.assertIn('KeyboardInterrupt', errors.getvalue())

    def test_required_arguments_import_and_lifecycle_failures(self):
        for args in ([], ['--fixture', str(FIXTURE)], *(
                ['--fixture', str(FIXTURE), '--cleanup-timeout', value]
                for value in ('0', '-1', 'nan', 'inf'))):
            with patch('sys.stderr', io.StringIO()), patch('ticket_operations_client.subprocess.Popen') as launch:
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
                launch.assert_not_called()
        result = subprocess.run([sys.executable, '-B', '-c',
            "import subprocess; from unittest.mock import patch; "
            "guard=patch.object(subprocess, 'Popen', side_effect=AssertionError('import launched')); "
            "guard.start(); import settlement_console"], cwd=HERE, capture_output=True, text=True,
            env=os.environ.copy(), timeout=10)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
        for close_result in (7, OSError('cleanup failed')):
            client = Mock()
            if isinstance(close_result, Exception):
                client.close.side_effect = close_result
            else:
                client.close.return_value = close_result
            with patch('settlement_console.TicketOperationsClient.launch', return_value=client), \
                    patch('sys.stdin', script(['quit'])), patch('sys.stdout', io.StringIO()), \
                    patch('sys.stderr', io.StringIO()):
                self.assertEqual(main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']),
                                 2 if isinstance(close_result, Exception) else 1)
            client.close.assert_called_once_with()
            client.request.assert_not_called()
        with patch('settlement_console.TicketOperationsClient.launch', side_effect=OSError('launch failed')), \
                patch('sys.stderr', io.StringIO()) as errors:
            self.assertEqual(main(['--fixture', str(FIXTURE), '--cleanup-timeout', '1']), 2)
        self.assertIn('launch failed', errors.getvalue())

    def exception_journey(self, name):
        fixture = HERE / 'fixtures/ticket_operations_settlement_exceptions_session.json'
        probes = [dict(surface=surface, operation=op, arguments={field: identity})
            for surface, op, field, identity in (
                ('booking', 'view', 'reservation_id', 'reserve-2'),
                ('resale', 'view_right', 'right_id', 'issue-1'),
                ('admission', 'view', 'right_id', 'issue-1'))]
        answers = (HERE / ('fixtures/settlement_console_' + name + '.txt')).read_text().splitlines()
        with patch('ticket_operations_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
            result = self.drive(answers, fixture=fixture, unchanged=probes)
        launch.assert_called_once()
        status, calls, replies, output, errors = result
        self.parity(calls, replies, output, fixture)
        for reply in replies:
            if 'error' not in reply:
                settlement_flags(self, reply.get('receipt', reply.get('view')))
        self.assertEqual(output.count('Historical action snapshot;'), sum('receipt' in r for r in replies))
        self.assertIn('not real refund completion', output)
        return result

    def test_live_pre_capture_failure_cancellation_terminal_replays_and_post_capture_refusals(self):
        status, calls, replies, output, errors = self.exception_journey('exceptions')
        self.assertEqual((status, errors), (1, 'Child exit status=1\n'))
        for i, phase in ((0, 'FAILED'), (6, 'CANCELLED'), (12, 'FAILED'), (18, 'CANCELLED')):
            first = replies[i]['receipt']
            self.assertEqual(first['settlement']['phase'], phase)
            self.assertTrue(first['settlement']['terminal'])
            self.assertIsNone(first['settlement']['claim'])
            self.assertEqual(replies[i+1]['view'], first['settlement'])
            self.assertTrue(replies[i+2]['receipt']['matched'])
            self.assertEqual(replies[i+3]['receipt'], first | dict(duplicate=True, applied=None))
            self.assertEqual(replies[i+4]['error'], {'code': 'IDEMPOTENCY_CONFLICT'})
            self.assertEqual(replies[i+5]['error'], {'code': 'TERMINAL_IMMUTABLE'})
        self.assertEqual([r['error'] for r in replies[24:28]], [{'code': 'ILLEGAL_TRANSITION'}] * 4)
        self.assertEqual(replies[28]['receipt'], replies[20]['receipt'] | dict(duplicate=True, applied=None))
        self.assertEqual(replies[29]['view'], replies[19]['view'])
        self.assertEqual(replies[30]['error'], {'code': 'ILLEGAL_TRANSITION'})
        self.assertEqual([r['error'] for r in replies[31:]], [{'code': 'IDEMPOTENCY_CONFLICT'}] * 3)
        # This exact selection does not ask for capture, refund, distribution or repair.
        self.assertEqual(set(r['operation'] for r in calls), {'fail', 'cancel', 'view', 'reconcile', 'authorize'})

    def test_live_reconciliation_around_statements_distribution_refund_and_acceptance(self):
        status, calls, replies, output, errors = self.exception_journey('reconcile')
        self.assertEqual((status, errors), (0, ''))
        first = replies[0]['receipt']
        self.assertEqual(first['settlement']['phase'], 'AUTHORIZED')
        for row, reply in zip(calls, replies, strict=True):
            if row['arguments'].get('idempotency_key') == 'historical' and reply is not replies[0]:
                self.assertEqual(reply['receipt'], first | dict(duplicate=True, applied=None))
        claim = replies[-1]['view']['claim']
        self.assertEqual((claim['distributed_cash'], claim['refund_face'], claim['refund_outstanding']),
                         (9301, 4000, 3000))
        self.assertNotEqual(replies[-2]['receipt']['settlement'], replies[-1]['view'])
        self.assertEqual(replies[-3]['receipt']['settlement'], replies[-1]['view'])
        expected = [json.loads(line) for line in (HERE /
            'fixtures/ticket_operations_settlement_reconciliation.jsonl').read_text().splitlines()]
        self.assertEqual(calls, expected)

    def test_exception_answer_files_as_standalone_cli_subprocesses(self):
        for name, expected_status, count in (('exceptions', 1, 34), ('reconcile', 0, 26)):
            with self.subTest(transcript=name):
                result = subprocess.run([sys.executable, '-B', str(HERE / 'settlement_console.py'),
                    '--fixture', str(HERE / 'fixtures/ticket_operations_settlement_exceptions_session.json'),
                    '--cleanup-timeout', '1'],
                    input=(HERE / ('fixtures/settlement_console_' + name + '.txt')).read_text(),
                    text=True, capture_output=True, timeout=10, env=os.environ.copy())
                self.assertEqual(result.returncode, expected_status)
                self.assertEqual(result.stderr, 'Child exit status=1\n' if expected_status else '')
                self.assertEqual(len(re.findall(r'desk=', result.stdout)), count)
                self.assertIn('Historical action snapshot;', result.stdout)
                self.assertIn('not real refund completion', result.stdout)

    def test_documented_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'settlement_console.py'),
            '--fixture', str(FIXTURE), '--cleanup-timeout', '1'], input=JOURNEY.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(len(re.findall(r'desk=', result.stdout)), 12)
        self.assertIn('"refund_outstanding": 3000', result.stdout)
        self.assertIn('Action snapshot', result.stdout)
        self.assertIn('Current service observation', result.stdout)

    def test_booking_start_transcript_as_cli_subprocess(self):
        result = subprocess.run([sys.executable, '-B', str(HERE / 'settlement_console.py'),
            '--fixture', str(INPUTS), '--cleanup-timeout', '1'], input=START_BOOKING.read_text(),
            text=True, capture_output=True, timeout=10, env=os.environ.copy())
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(len(re.findall(r'desk=', result.stdout)), 18)
        self.assertIn('"refund_outstanding": 3000', result.stdout)
        self.assertIn('claim data unavailable (claim=null)', result.stdout)


if __name__ == '__main__':
    unittest.main()
