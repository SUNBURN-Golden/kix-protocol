"""Source-informed shared-ticket composition evidence, not clean-room verification."""

from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import inspect
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from admission_fixture import FixtureError
from reservation_fsm import ReservationError
from settlement_fsm import SettlementError, SettlementMachine
from test_admission_session import assert_flags
from test_resale_fsm import assert_not_final as resale_flags
from test_reservation_fsm import assert_not_final as booking_flags
from test_ticket_operations_session import direct_call, direct_graph, machines, outcome, snapshot
from ticket_operations_cli import _SETTLEMENT_DISPATCH, dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketSettlementSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_settlement_session.json'


def rows(scenario='booking'):
    return [json.loads(line) for line in transcript(scenario).read_text().splitlines()]


def transcript(scenario):
    return HERE / f'fixtures/ticket_operations_settlement_{scenario}.jsonl'


def changed(row, **arguments):
    return row | {'arguments': row['arguments'] | arguments}


def settlement_flags(test, result):
    value = result.get('settlement', result)
    test.assertEqual(value['provenance'], 'MOCK_SETTLEMENT_ONLY')
    test.assertEqual(value['lifecycle_authority'], 'IN_MEMORY_FSM')
    test.assertEqual(value['external_payment'], 'UNSUPPORTED')
    for key in ('provider_authorization_executed', 'legal_debtor_bound', 'admission_granted',
                'right_cancelled', 'bank_debit_observed', 'external_return_closed',
                'funds_executed', 'durable'):
        test.assertIs(value[key], False, key)


class TicketSettlementControlsTests(unittest.TestCase):
    def graph(self):
        self.value = json.loads(FIXTURE.read_text())
        self.session = load_fixture(FIXTURE)
        self.control = direct_graph(self.value['setup'])
        self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))
        book, tickets, resale, admission = machines(self.session)
        self.assertIs(self.session.settlement._machine, book)
        for consumer in (tickets, resale, admission):
            self.assertIs(consumer._settlement, book)

    def step(self, row, code=None):
        graph = machines(self.session)
        before = snapshot(graph)
        sources = (self.session.resale._adapter._source,
                   self.session.resale._payment_adapter._source,
                   self.session.admission._adapter._source)
        fetches = tuple(source.calls for source in sources)
        expected = outcome(lambda: direct_call(self.control, row, self.value))
        result = outcome(lambda: dispatch_request(self.session, row))
        self.assertEqual(result, expected)
        self.assertEqual(snapshot(graph), snapshot(self.control))
        if code:
            self.assertEqual(result, {'error': {'code': code}})
        if 'error' in result:
            self.assertEqual(snapshot(graph), before)
        else:
            value = result.get('receipt', result.get('view'))
            {'settlement': settlement_flags, 'booking': booking_flags,
             'resale': resale_flags, 'admission': assert_flags}[row['surface']](self, value)
        if row['surface'] == 'settlement':
            self.assertEqual(snapshot(graph)[1:], before[1:])
            self.assertEqual(tuple(source.calls for source in sources), fetches)
        return result

    def test_transcripts_compare_every_step_and_preserve_refused_keys(self):
        for scenario in ('booking', 'resale'):
            with self.subTest(scenario=scenario):
                self.graph()
                results = [self.step(row) for row in rows(scenario)]
                refused = [r for r in results if 'error' in r]
                self.assertEqual(refused, [{'error': {'code': 'SETTLEMENT_NOT_COMMITTED'}}] * 2)
                # First receipt remains INITIATED after explicit COMMITTED progress.
                first, replay, current = ((1, 10, 11) if scenario == 'booking' else (3, 12, 13))
                self.assertEqual(results[replay]['receipt'], results[first]['receipt'] |
                                 {'duplicate': True, 'applied': None})
                self.assertEqual(results[replay]['receipt']['settlement']['phase'], 'INITIATED')
                self.assertEqual(results[current]['view']['phase'], 'COMMITTED')
                if scenario == 'booking':
                    self.assertEqual(results[4]['view']['phase'], 'INITIATED')
                    self.assertEqual(results[9]['receipt']['reservation']['phase'], 'ISSUED')
                    self.assertEqual(results[-1]['view']['settlement_gate'], 'MOCK_COMMIT_OBSERVED')
                    # Separate issuance has not adopted the second ticket anywhere.
                    self.assertEqual(outcome(lambda: self.session.resale.view_right('issue-2')),
                                     {'error': {'code': 'UNKNOWN_RIGHT'}})
                    self.assertEqual(outcome(lambda: self.session.admission.view('issue-2')),
                                     {'error': {'code': 'UNKNOWN_RIGHT'}})
                    self.assertEqual(self.session.resale._payment_adapter._source.calls, ())
                    self.assertEqual(self.session.resale._adapter._source.calls, ())
                else:
                    self.assertEqual(results[2]['view']['phase'], 'PAYMENT_NOTED')
                    self.assertEqual(results[11]['receipt']['listing']['phase'], 'TRANSFERRED')
                    self.assertEqual(results[-1]['view']['right']['version'], 2)
                    self.assertEqual(self.session.resale._payment_adapter._source.calls, ('payment-1',))
                    self.assertEqual(self.session.resale._adapter._source.calls, ('offer-1',))
                    self.assertEqual(self.session.admission.view('issue-1')['version'], 1)
                self.assertEqual(self.session.admission._adapter._source.calls, ())

    def test_file_stdin_and_executable_exits_zero_one_two(self):
        for scenario in ('booking', 'resale'):
            self.graph()
            expected = [self.step(row) | {'surface': row['surface'], 'operation': row['operation']}
                        for row in rows(scenario)]
            for selector, stdin in ((str(transcript(scenario)), None),
                                    ('-', transcript(scenario).read_text())):
                result = self.cli(selector, stdin)
                self.assertEqual((result.returncode, result.stderr), (1, ''))
                self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
        success = json.dumps(rows()[1]) + '\n'
        for status, text in ((0, success), (2, '{}\n' + success),
                             (2, json.dumps(rows()[1]) + '\n{}\n' + success)):
            for as_file in (False, True):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / 'requests.jsonl'
                    path.write_text(text)
                    result = self.cli(str(path) if as_file else '-', None if as_file else text)
                    self.assertEqual((result.returncode, result.stderr), (status, ''))
                    self.assertEqual(len(result.stdout.splitlines()), 2 if text.startswith(success+'{}') else 1)

    def cli(self, selector, stdin):
        return subprocess.run([sys.executable, str(HERE/'ticket_operations_cli.py'),
                               '--fixture', str(FIXTURE), '--requests', selector],
                              input=stdin, text=True, capture_output=True, check=False)

    def test_fsm_methods_forward_once_with_exact_objects_receipts_and_errors(self):
        self.assertEqual(set(_SETTLEMENT_DISPATCH), {'initiate', 'authorize', 'capture', 'commit', 'view',
                                                          'bind_refund', 'observe_recorded_cancel_acceptance'})
        for operation, (_, fields, key) in _SETTLEMENT_DISPATCH.items():
            if operation == 'observe_recorded_cancel_acceptance':
                continue  # Adapter forwarding is covered in test_ticket_refund_controls.
            signature = inspect.signature(getattr(TicketSettlementSession, operation))
            self.assertEqual(set(signature.parameters) - {'self'}, fields)
            for name, parameter in signature.parameters.items():
                if name not in ('self', 'settlement_id'):
                    self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
                self.assertIs(parameter.default, inspect.Parameter.empty)
            for positional in (False, True):
                machine = Mock(spec=SettlementMachine)
                desk = TicketSettlementSession(machine)
                machine.assert_not_called()
                arguments = {field: object() for field in fields}
                receipt = {'opaque': object()}
                method = getattr(machine, operation)
                method.return_value = receipt
                if positional:
                    forwarded = dict(arguments)
                    subject = forwarded.pop('settlement_id')
                    actual = getattr(desk, operation)(subject, **forwarded)
                else:
                    shared = Mock(settlement=desk)
                    actual = dispatch_request(shared, dict(surface='settlement', operation=operation,
                                                           arguments=arguments))[key]
                self.assertIs(actual, receipt)
                forwarded = dict(arguments)
                subject = forwarded.pop('settlement_id')
                method.assert_called_once_with(subject, **forwarded)
                self.assertEqual(len(machine.mock_calls), 1)
                machine.reset_mock()
                error = SettlementError('OPAQUE_REFUSAL')
                method.side_effect = error
                with self.assertRaises(SettlementError) as caught:
                    dispatch_request(Mock(settlement=desk), dict(surface='settlement', operation=operation,
                                                               arguments=arguments))
                self.assertIs(caught.exception, error)
                method.assert_called_once_with(subject, **forwarded)
                self.assertEqual(len(machine.mock_calls), 1)

    def test_publication_calls_no_settlement_method(self):
        from ticket_operations_session import TicketOperationsSession
        def publish(machine, **kwargs):
            with ExitStack() as stack:
                for name in dir(SettlementMachine):
                    if not name.startswith('_') and callable(getattr(machine, name)):
                        stack.enter_context(patch.object(machine, name, side_effect=AssertionError(name)))
                return TicketSettlementSession(machine, **kwargs)
        with patch('ticket_operations_session.TicketSettlementSession', side_effect=publish):
            self.graph()
        value = self.value
        value['setup'] = deepcopy(value['setup'])
        next(e for e in value['setup'] if e['operation'] == 'hold')['body']['slot'] = 99
        with patch('ticket_operations_session.TicketSettlementSession') as publish:
            with self.assertRaises(ReservationError) as error:
                TicketOperationsSession(setup=value['setup'], offer_source=Mock(), presentation_source=Mock())
            self.assertEqual(error.exception.code, 'SLOT')
            publish.assert_not_called()

    def test_illegal_phases_amount_mismatch_replay_and_historical_receipts(self):
        self.graph()
        init, auth, capture, commit = [r for r in rows() if r['surface']=='settlement'
                                       and r['operation'] != 'view'][:4]
        self.step(init)
        self.step(changed(capture, idempotency_key='early-capture'), 'ILLEGAL_TRANSITION')
        self.step(changed(commit, idempotency_key='early-commit'), 'ILLEGAL_TRANSITION')
        authorized = self.step(auth)
        self.step(changed(auth, idempotency_key='repeat-auth'), 'ILLEGAL_TRANSITION')
        self.step(capture)
        self.step(changed(capture, idempotency_key='repeat-capture'), 'ILLEGAL_TRANSITION')
        bad_statement = changed(commit, amount=commit['arguments']['amount']-1, idempotency_key='bad-statement')
        self.step(bad_statement, 'SETTLEMENT_COMPONENT_MISMATCH')
        self.step(commit)
        for row in (changed(capture, idempotency_key='early-capture'),
                    changed(commit, idempotency_key='early-commit'), bad_statement):
            self.step(row, 'SETTLEMENT_COMPONENT_MISMATCH' if row is bad_statement else 'ILLEGAL_TRANSITION')
        self.assertEqual(self.step(auth)['receipt'], authorized['receipt'] | {'duplicate': True, 'applied': None})
        self.step(changed(commit, idempotency_key='repeat-commit'), 'ILLEGAL_TRANSITION')
        for row in (changed(init, settlement_id='other'), changed(init, gross=999),
                    changed(auth, idempotency_key=init['arguments']['idempotency_key'])):
            self.step(row, 'IDEMPOTENCY_CONFLICT')
        self.step(dict(surface='settlement', operation='view', arguments={'settlement_id':'absent'}),
                  'UNKNOWN_SETTLEMENT')

    def test_committed_gross_mismatch_at_both_ticket_gates(self):
        for scenario in ('booking', 'resale'):
            self.graph()
            for row in rows(scenario):
                if row['surface']=='settlement' and row['operation'] in ('initiate', 'commit'):
                    gross = row['arguments']['gross'] - 1
                    row = changed(row, gross=gross)
                    if row['operation'] == 'commit':
                        row = changed(row, amount=gross)
                if row['operation'] in ('issue', 'accept_resale'):
                    self.step(row, 'SETTLEMENT_NOT_COMMITTED' if 'fresh' not in row['arguments']['idempotency_key']
                              else 'SETTLEMENT_AMOUNT_MISMATCH')
                    if 'fresh' in row['arguments']['idempotency_key']:
                        break
                else:
                    self.step(row)

    def test_strict_json_and_policy_errors_stop_or_continue_without_side_effects(self):
        self.graph()
        before = snapshot(machines(self.session))
        variants = []
        for operation, (_, fields, _) in _SETTLEMENT_DISPATCH.items():
            args = dict.fromkeys(fields, 'x')
            variants += [dict(surface='settlement', operation=operation, arguments=bad)
                         for bad in [None, [], args | {'extra': None},
                                     *[{k:v for k,v in args.items() if k != field} for field in fields]]]
        variants += [dict(surface='settlement', operation=op, arguments={})
                     for op in ('fail', 'cancel', 'observe_statement', 'distribute',
                                'observe_mock_cancel_acceptance', 'observe_external_payment', 'reconcile',
                                'restore', 'canonical_state', 'export_journal', '__init__', [], None)]
        texts = [json.dumps(row) for row in variants]
        texts += ['{"surface":"settlement","operation":"view","arguments":{"settlement_id":"a","settlement_id":"b"}}',
                  '{"surface":"settlement","operation":"initiate","arguments":{"policy":{"fee_bps":0,"fee_bps":1}}}']
        texts += [json.dumps(rows()[1]).replace('"gross": 10001', '"gross": '+number)
                  for number in ('NaN', 'Infinity', '-Infinity', '1e999')]
        for text in texts:
            with self.subTest(text=text), redirect_stdout(io.StringIO()) as output:
                status = run_requests(self.session, [text, json.dumps(rows()[1])])
                self.assertEqual(status, 2)
                self.assertEqual(len(output.getvalue().splitlines()), 1)
                self.assertEqual(json.loads(output.getvalue())['error']['type'], 'FixtureError')
                self.assertEqual(snapshot(machines(self.session)), before)
        for policy in (None, {}, {'kind':'OTHER'}, rows()[1]['arguments']['policy'] | {'fee_bps': True},
                       rows()[1]['arguments']['policy'] | {'extra': 0}):
            self.graph()
            bad = changed(rows()[1], policy=policy, idempotency_key='bad-policy')
            expected = outcome(lambda: direct_call(self.control, bad, self.value))
            self.assertIn('error', expected)
            self.step(bad, expected['error']['code'])
            with redirect_stdout(io.StringIO()) as output:
                status = run_requests(self.session, [json.dumps(bad), json.dumps(rows()[1])])
            self.assertEqual(status, 1)
            self.assertEqual(json.loads(output.getvalue().splitlines()[0])['error'], expected['error'])
            self.assertEqual(json.loads(output.getvalue().splitlines()[1])['receipt']['settlement']['phase'], 'INITIATED')

    def test_fixture_retains_required_anchor(self):
        value = json.loads(FIXTURE.read_text())
        for predicate in (lambda e: e['operation']=='issue',
                          lambda e: e['operation']=='bind_settlement',
                          lambda e: e['operation']=='adopt_issued' and e['machine']=='resale',
                          lambda e: e['operation']=='adopt_issued' and e['machine']=='admission',
                          lambda e: e['operation']=='set_clock' and e['machine']=='admission'):
            bad = value | {'setup':[e for e in value['setup'] if not predicate(e)]}
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'fixture.json'
                path.write_text(json.dumps(bad))
                with self.assertRaises(FixtureError):
                    load_fixture(path)
