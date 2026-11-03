"""Source-informed shared-desk evidence against unchanged direct FSM controls."""

from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_ticket_operations_session import direct_call, direct_graph, machines, outcome, snapshot
from test_ticket_settlement_controls import settlement_flags
from fake_cancel_acceptance_source import FakeCancelAcceptanceSource
from fake_statement_source import FakeStatementSource
from settlement_fsm import SettlementMachine
from settlement_property_support import check_claim_view
from ticket_operations_cli import dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketSettlementSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_settlement_exceptions_session.json'
NEW = {'fail', 'cancel', 'reconcile'}


def request(operation, settlement_id='claim-2', **arguments):
    return dict(surface='settlement', operation=operation,
                arguments=dict(settlement_id=settlement_id, **arguments))


def path(name):
    return HERE / f'fixtures/ticket_operations_settlement_{name}.jsonl'


def rows(name):
    return [json.loads(line) for line in path(name).read_text().splitlines()]


class TicketSettlementExceptionsTests(unittest.TestCase):
    def graph(self):
        self.value = json.loads(FIXTURE.read_text())
        self.session, self.api = load_fixture(FIXTURE), load_fixture(FIXTURE)
        self.control = direct_graph(self.value['setup'])
        for desk in (self.session, self.api):
            self.assertEqual(snapshot(machines(desk)), snapshot(self.control))

    def sources(self, desk):
        return (desk.resale._adapter._source, desk.resale._payment_adapter._source,
                desk.admission._adapter._source, desk.settlement._statement_adapter._source,
                desk.settlement._cancel_acceptance_adapter._source)

    def step(self, row, code=None):
        before = snapshot(machines(self.session))
        fetches = [tuple(s.calls for s in self.sources(d)) for d in (self.session, self.api)]
        op, args = row['operation'], row['arguments']
        direct = deepcopy(row)
        if op in ('commit_recorded_statement', 'observe_recorded_statement'):
            document = json.loads(next(e['recorded_text'] for e in self.value['statements']
                if (e['settlement_id'], e['movement_id']) == (args['settlement_id'], args['movement_id'])))
            direct.update(operation='commit' if op == 'commit_recorded_statement' else 'observe_statement',
                          arguments=document | dict(idempotency_key=args['idempotency_key']))
        elif op == 'observe_recorded_cancel_acceptance':
            document = json.loads(next(e['recorded_text'] for e in self.value['cancel_acceptances']
                if (e['settlement_id'], e['source_id']) == (args['settlement_id'], args['source_id'])))
            direct.update(operation='observe_mock_cancel_acceptance',
                          arguments=document | dict(idempotency_key=args['idempotency_key']))
        expected = outcome(lambda: direct_call(self.control, direct, self.value))
        if 'error' not in expected:
            expected['operation'] = op
        actual = outcome(lambda: dispatch_request(self.session, row))
        api = outcome(lambda: getattr(self.api.settlement, op)(**args))
        key = 'view' if op == 'view' else 'receipt'
        self.assertEqual(actual, expected)
        self.assertEqual(api, expected if 'error' in expected else expected[key])
        for index, desk in enumerate((self.session, self.api)):
            self.assertEqual(snapshot(machines(desk)), snapshot(self.control))
            self.assertEqual(snapshot(machines(desk))[1:], before[1:])
            if op in NEW:
                self.assertEqual(tuple(s.calls for s in self.sources(desk)), fetches[index])
        if code:
            self.assertEqual(actual, {'error': {'code': code}})
        if 'error' in actual:
            self.assertEqual(snapshot(machines(self.session)), before)
            return dict(surface='settlement', operation=op, **actual)
        settlement_flags(self, actual[key])
        current = self.session.settlement.view(args['settlement_id'])
        if current['claim'] is not None:
            check_claim_view(current['claim'])
        if op == 'reconcile':
            self.assertEqual(snapshot(machines(self.session)), before)
            self.assertTrue(actual['receipt']['matched'])
            if not actual['receipt']['duplicate']:
                self.assertEqual(actual['receipt']['state_digest'], before[0][1])
                self.assertEqual(actual['receipt']['entry_count'], len(before[0][2]))
                self.assertEqual(actual['receipt']['settlement'], current)
        return actual

    def test_pre_capture_and_terminal_parity(self):
        for phase in ('INITIATED', 'AUTHORIZED', 'CAPTURED', 'COMMITTED'):
            for operation in ('fail', 'cancel'):
                with self.subTest(phase=phase, operation=operation):
                    self.graph()
                    sid = {'INITIATED': 'fail-init', 'AUTHORIZED': 'claim-2',
                           'CAPTURED': 'late-capture', 'COMMITTED': 'claim-1'}[phase]
                    self.step(request('reconcile', sid, idempotency_key='before'))
                    terminal = request(operation, sid, idempotency_key='terminate', reason='synthetic')
                    self.step(terminal, 'ILLEGAL_TRANSITION' if phase in ('CAPTURED','COMMITTED') else None)
                    if phase in ('CAPTURED','COMMITTED'):
                        continue
                    current = self.step(request('view', sid))['view']
                    self.assertEqual(current['phase'], 'FAILED' if operation == 'fail' else 'CANCELLED')
                    self.assertTrue(current['terminal'])
                    self.assertIsNone(current['claim'])
                    # Every currently exposed mutator reaches the original terminal guard.
                    variants = [request('initiate', sid, trade_id='terminal-trade', gross=10001,
                        debtor_role='fixture-merchant', currency='KRW', policy=current['policy']),
                        request('authorize', sid), request('capture', sid),
                        request('commit', sid, movement_id='terminal-move', gross=10001, amount=10001,
                                fee=0, tax=0, held=0, adjustment=0, adjustment_reason=None),
                        request('commit_recorded_statement', sid, movement_id='statement-1'),
                        request('observe_recorded_statement', sid, movement_id='statement-1'),
                        request('distribute', sid, order=['platform','organizer']),
                        request('bind_refund', sid, refund_id='terminal-refund', amount=1,
                                beneficiary_role='buyer-3', reason='synthetic'),
                        request('observe_recorded_cancel_acceptance', sid, source_id='acceptance-1'),
                        request('fail', sid, reason='synthetic'), request('cancel', sid, reason='synthetic')]
                    # Recorded selectors need a matching source to reach the FSM.
                    for table, identity in [('statements','movement_id'),('cancel_acceptances','source_id')]:
                        original = next(e for e in self.value[table] if e[identity] == ('statement-1' if table=='statements' else 'acceptance-1'))
                        entry = original | dict(settlement_id=sid,
                            recorded_text=json.dumps(json.loads(original['recorded_text']) | dict(settlement_id=sid)))
                        if not any(e['settlement_id']==sid and e[identity]==entry[identity] for e in self.value[table]):
                            self.value[table].append(entry)
                            for desk in (self.session, self.api):
                                adapter = desk.settlement._statement_adapter if table=='statements' else desk.settlement._cancel_acceptance_adapter
                                cls = FakeStatementSource if table=='statements' else FakeCancelAcceptanceSource
                                adapter._source = cls(recordings={(e['settlement_id'],e[identity]):e['recorded_text'] for e in self.value[table]})
                    for i, row in enumerate(variants):
                        row['arguments']['idempotency_key'] = 'terminal-'+str(i)
                        self.step(row, 'TERMINAL_IMMUTABLE')
                    self.step(request('reconcile', sid, idempotency_key='after'))

    def test_replay_and_retained_refusal_keys(self):
        for operation in ('fail','cancel'):
            self.graph()
            sid = 'new'
            initial = request('initiate', sid, idempotency_key='new-init', trade_id='new-trade',
                gross=10001, debtor_role='fixture-merchant', currency='KRW',
                policy=self.session.settlement.view('claim-2')['policy'])
            authorized = request('authorize', sid, idempotency_key='new-auth')
            first = self.step(initial)['receipt']
            auth = self.step(authorized)['receipt']
            # A retained phase refusal must remain a refusal after phase advancement.
            # Use a separate initiated case so this refusal precedes authorization.
            refused = request('capture', 'fail-init', idempotency_key='phase-refusal')
            self.step(refused, 'ILLEGAL_TRANSITION')
            self.step(request('authorize', 'fail-init', idempotency_key='advance-refused'))
            self.step(refused, 'ILLEGAL_TRANSITION')
            terminal = request(operation, sid, idempotency_key='terminal-key', reason='synthetic')
            accepted = self.step(terminal)['receipt']
            for row, receipt in ((initial,first),(authorized,auth),(terminal,accepted)):
                self.assertEqual(self.step(row)['receipt'], receipt | dict(duplicate=True, applied=None))
            for args in (dict(reason='changed'),dict(settlement_id='claim-1')):
                self.step(terminal | dict(arguments=terminal['arguments'] | args), 'IDEMPOTENCY_CONFLICT')
            self.step(terminal | dict(operation='cancel' if operation=='fail' else 'fail'), 'IDEMPOTENCY_CONFLICT')
            terminal_refusal = request('fail', sid, idempotency_key='retained', reason='synthetic')
            self.step(terminal_refusal, 'TERMINAL_IMMUTABLE')
            self.step(terminal_refusal, 'TERMINAL_IMMUTABLE')
            self.step(terminal_refusal | dict(arguments=terminal_refusal['arguments'] | dict(reason='changed')),
                      'IDEMPOTENCY_CONFLICT')
            self.step(request('reconcile', sid, idempotency_key='terminal-key'), 'IDEMPOTENCY_CONFLICT')
            self.step(request('reconcile', sid, idempotency_key='recon'))
            self.step(request('reconcile', 'claim-1', idempotency_key='recon'), 'IDEMPOTENCY_CONFLICT')
            # Journal restore forgets refusals and reconciliation keys, but retains accepted operations.
            restored = TicketSettlementSession(SettlementMachine.restore(machines(self.session)[0].export_journal()))
            self.assertFalse(restored.reconcile(sid, idempotency_key='recon')['duplicate'])
            self.assertFalse(restored.reconcile(sid, idempotency_key='retained')['duplicate'])
            self.assertTrue(getattr(restored, operation)(**terminal['arguments'])['duplicate'])
            self.assertFalse(restored.capture('fail-init', idempotency_key='phase-refusal')['duplicate'])

    def test_reconcile_history_and_restore(self):
        self.graph()
        results = [self.step(row) for row in rows('reconciliation')]
        historical = results[0]['receipt']
        self.assertEqual(historical['settlement']['phase'], 'AUTHORIZED')
        for row, result in zip(rows('reconciliation'), results):
            if row['operation']=='reconcile' and row['arguments']['idempotency_key']=='historical':
                if result is results[0]:
                    continue
                self.assertEqual(result['receipt'], historical | dict(duplicate=True, applied=None))
        current = self.session.settlement.view('claim-2')
        self.assertEqual(current['phase'], 'COMMITTED')
        self.assertEqual(current['claim']['distributed_cash'], 9301)
        self.assertEqual(current['claim']['refund_face'], 4000)
        self.assertNotEqual(historical['settlement'], current)
        journal = machines(self.session)[0].export_journal()
        self.assertNotIn('reconcile', [e['op'] for e in journal])
        restored = TicketSettlementSession(SettlementMachine.restore(journal))
        fresh = restored.reconcile('claim-2', idempotency_key='historical')
        self.assertFalse(fresh['duplicate'])
        self.assertEqual(fresh['settlement'], current)
        self.assertEqual(fresh['state_digest'], machines(self.session)[0].state_digest())
        self.assertEqual(restored._machine.export_journal(), journal)
        # Full synthetic acceptance also stays in COMMITTED and never closes an external return.
        self.graph()
        self.step(request('capture', idempotency_key='cap'))
        self.step(request('commit_recorded_statement', movement_id='statement-1', idempotency_key='commit'))
        self.step(request('bind_refund', refund_id='full', amount=10001, beneficiary_role='buyer-3',
                          reason='synthetic', idempotency_key='full-bind'))
        self.step(request('observe_recorded_cancel_acceptance', source_id='acceptance-full', idempotency_key='full-accept'))
        self.step(request('reconcile', idempotency_key='full-reconcile'))

    def test_settlement_exception_isolation(self):
        for operation in ('fail','cancel','reconcile'):
            self.graph()
            booking = self.session.booking.view('reserve-2')
            self.assertEqual(booking['settlement_id'], 'claim-2')
            self.assertEqual(self.session.settlement.view('claim-2')['phase'], 'AUTHORIZED')
            for desk in (self.session, self.api):
                self.assertEqual(tuple(s.calls for s in self.sources(desk)), ((),)*5)
            with ExitStack() as stack:
                spies = []
                for desk in (self.session, self.api):
                    for machine in machines(desk)[1:]:
                        # Fail immediately on any public mutation, even an economically inert one.
                        for name in dir(type(machine)):
                            if not name.startswith('_') and callable(getattr(machine,name)) and not name.startswith(('view','canonical','state_digest','export','restore')):
                                spies.append(stack.enter_context(patch.object(machine,name,side_effect=AssertionError(name))))
                    for source in self.sources(desk):
                        spies.append(stack.enter_context(patch.object(source,'fetch',side_effect=AssertionError('fetch'))))
                    book = machines(desk)[0]
                    for name in ('distribute','bind_refund','observe_mock_cancel_acceptance','reject_external'):
                        spies.append(stack.enter_context(patch.object(book,name,side_effect=AssertionError(name))))
                args = dict(idempotency_key='isolated')
                if operation!='reconcile':
                    args['reason'] = 'synthetic'
                self.step(request(operation,**args))
                for spy in spies:
                    spy.assert_not_called()
            self.assertEqual(self.session.booking.view('reserve-2'), booking)

    def cli(self, text, as_file):
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory)/'requests.jsonl'
            filename.write_text(text)
            return subprocess.run([sys.executable,str(HERE/'ticket_operations_cli.py'),
                '--fixture',str(FIXTURE),'--requests',str(filename) if as_file else '-'],
                input=None if as_file else text,text=True,capture_output=True,check=False)

    def test_file_stdin_and_strict_errors(self):
        for name, status in [('exceptions',1),('reconciliation',0)]:
            self.graph()
            expected = [self.step(row) for row in rows(name)]
            for as_file in (False,True):
                result = self.cli(path(name).read_text(),as_file)
                self.assertEqual((result.returncode,result.stderr),(status,''))
                self.assertEqual([json.loads(line) for line in result.stdout.splitlines()],expected)
        good = json.dumps(request('reconcile',idempotency_key='good'))
        variants = []
        for op in sorted(NEW):
            template = request(op,idempotency_key='strict')
            if op!='reconcile':
                template['arguments']['reason']='synthetic'
            args=template['arguments']
            variants += [json.dumps(template | dict(arguments=bad)) for bad in
                (None,[],args | dict(extra=1),*[{k:v for k,v in args.items() if k!=field} for field in args])]
            variants += [json.dumps(template).replace('"strict"','"strict", "idempotency_key":"duplicate"')]
            for field in args:
                variants += [json.dumps(template | dict(arguments=args | {field:float('inf')}))]
        variants += ['[]','null','{}',json.dumps(request('settlement_reconcile')),
                     '{"surface":"settlement","surface":"booking","operation":"reconcile","arguments":{}}']
        for bad in variants:
            self.graph()
            before=snapshot(machines(self.session))
            with redirect_stdout(io.StringIO()) as output:
                status=run_requests(self.session,[bad,good])
            self.assertEqual(status,2,bad)
            self.assertEqual(len(output.getvalue().splitlines()),1,bad)
            self.assertEqual(snapshot(machines(self.session)),before)
            for as_file in (False,True):
                result=self.cli(good+'\n'+bad+'\n'+good+'\n',as_file)
                self.assertEqual((result.returncode,result.stderr),(2,''),bad)
                self.assertEqual(len(result.stdout.splitlines()),2,bad)
        # Value errors retain FSM validation order and are domain refusals, not schema failures.
        for op in sorted(NEW):
            args=dict(idempotency_key='invalid')
            if op!='reconcile':
                args['reason']='synthetic'
            invalid = [request(op,**(args | {field:value}))
                for field in ('settlement_id','idempotency_key',*(() if op=='reconcile' else ('reason',)))
                for value in (None,[],True,'',' bad ')]
            invalid += [request(op,'missing',**args)]
            for bad in invalid:
                self.graph()
                expected=self.step(bad)
                self.assertIn('error',expected)
                for as_file in (False,True):
                    result=self.cli(json.dumps(bad)+'\n'+good+'\n',as_file)
                    self.assertEqual((result.returncode,result.stderr),(1,''))
                    emitted=[json.loads(line) for line in result.stdout.splitlines()]
                    self.assertEqual(emitted[0],expected)
                    self.assertTrue(emitted[1]['receipt']['matched'])
