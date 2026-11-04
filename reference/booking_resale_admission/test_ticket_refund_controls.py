"""Source-informed desk composition; unchanged adapters/FSMs are direct controls."""

from contextlib import redirect_stdout
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
from cancel_acceptance_adapter import CancelAcceptanceAdapter
from cancel_acceptance_source import CancelAcceptanceSourceError
from fake_cancel_acceptance_source import FakeCancelAcceptanceSource, SyntheticCancelAcceptanceFault
from settlement_fsm import SettlementError, SettlementMachine
from test_ticket_operations_session import direct_call, direct_graph, machines, snapshot
from test_ticket_settlement_controls import settlement_flags
from ticket_operations_cli import dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession, TicketSettlementSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_refund_session.json'
SID = 'claim-1'


def request(operation, **arguments):
    return dict(surface='settlement', operation=operation,
                arguments={"settlement_id":SID} | arguments)


def bind(**changes):
    return request('bind_refund', **(dict(idempotency_key='refund-bind-1', refund_id='refund-1',
        amount=4000, beneficiary_role='fixture-buyer-1', reason='fixture-caller-request') | changes))


def observe(**changes):
    return request('observe_recorded_cancel_acceptance', **(
        dict(source_id='acceptance-1', idempotency_key='accept-1') | changes))


def record(**changes):
    return dict(settlement_id=SID, source_id='acceptance-1', amount=1000) | changes


def source(entries):
    # Independent fixture mapping for the unchanged adapter control.
    return FakeCancelAcceptanceSource(recordings={
        (e['settlement_id'], e['source_id']): e['recorded_text'] if 'recorded_text' in e
        else SyntheticCancelAcceptanceFault(e['fault']) for e in entries})


def outcome(invoke):
    try:
        return invoke()
    except SettlementError as error:
        return {'error': {'code': error.code}}
    except CancelAcceptanceSourceError as error:
        return {'error': {'type': type(error).__name__, 'message': str(error)}}


def load_value(value):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'fixture.json'
        path.write_text(json.dumps(value))
        return load_fixture(path)


def run(session, rows):
    with redirect_stdout(io.StringIO()) as output:
        status = run_requests(session, [json.dumps(r) for r in rows])
    return status, [json.loads(line) for line in output.getvalue().splitlines()]


class TicketRefundControlsTests(unittest.TestCase):
    def graph(self, value=None):
        self.value = json.loads(FIXTURE.read_text()) if value is None else value
        self.session = load_value(self.value)
        self.api = load_value(self.value)
        self.control = direct_graph(self.value['setup'])
        self.raw = direct_graph(self.value['setup'])
        self.control_source = source(self.value['cancel_acceptances'])
        self.adapter = CancelAcceptanceAdapter(self.control[0], self.control_source)
        for desk in (self.session, self.api):
            graph = machines(desk)
            self.assertEqual(snapshot(graph), snapshot(self.control))
            self.assertIs(desk.settlement._machine, graph[0])
            self.assertIs(desk.settlement._cancel_acceptance_adapter._machine, graph[0])
            self.assertEqual(desk.settlement._cancel_acceptance_adapter._source.calls, ())
            for consumer in graph[1:]:
                self.assertIs(consumer._settlement, graph[0])

    def step(self, row, code=None, *, raw=True):
        before = snapshot(machines(self.session))
        args, operation = row['arguments'], row['operation']
        if operation == 'observe_recorded_cancel_acceptance':
            expected = outcome(lambda: dict(surface='settlement', operation=operation,
                                            receipt=self.adapter.apply(**args)))
            if raw:
                document = self.control_source.recordings[(args['settlement_id'], args['source_id'])]
                document = json.loads(document)
                expected_raw = outcome(lambda: dict(surface='settlement', operation=operation,
                    receipt=self.raw[0].observe_mock_cancel_acceptance(
                        args['settlement_id'], source_id=args['source_id'], amount=document['amount'],
                        idempotency_key=args['idempotency_key'])))
        else:
            expected = outcome(lambda: direct_call(self.control, row, self.value))
            if raw:
                expected_raw = outcome(lambda: direct_call(self.raw, row, self.value))
        result = outcome(lambda: dispatch_request(self.session, row))
        key = 'view' if operation.startswith('view') else 'receipt'
        api_result = outcome(lambda: {key: getattr(getattr(self.api, row['surface']), operation)(**args)})
        self.assertEqual(result, expected)
        self.assertEqual(api_result, expected if 'error' in expected else {key: expected[key]})
        if code:
            self.assertEqual(result, {'error': {'code': code}})
        for desk in (self.session, self.api):
            graph = machines(desk)
            self.assertEqual(snapshot(graph), snapshot(self.control))
            self.assertEqual(desk.settlement._cancel_acceptance_adapter._source.calls,
                             self.control_source.calls)
            self.assertEqual(desk.resale._adapter._source.calls, ())
            self.assertEqual(desk.resale._payment_adapter._source.calls, ())
            self.assertEqual(desk.admission._adapter._source.calls, ())
        if raw:
            self.assertEqual(expected_raw, expected)
            self.assertEqual(snapshot(self.raw), snapshot(self.control))
        if row['surface'] == 'settlement':
            self.assertEqual(snapshot(machines(self.session))[1:], before[1:])
            if 'error' in result:
                self.assertEqual(snapshot(machines(self.session)), before)
            else:
                settlement_flags(self, result[key])
        return result

    def test_journeys_compare_api_cli_adapter_and_raw_fsm_after_every_step(self):
        for name in ('partial', 'full', 'replay'):
            with self.subTest(name=name):
                self.graph()
                path = HERE / f'fixtures/ticket_operations_refund_{name}.jsonl'
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                cash = self.control[0].view(SID)['claim']['confirmed_cash']
                results = [self.step(row) for row in rows]
                claim = self.session.settlement.view(SID)['claim']
                accepted = 10001 if name == 'full' else 1500
                self.assertEqual(claim['refund_accepted'], accepted)
                self.assertEqual(claim['refund_outstanding'], 0 if name == 'full' else 2500)
                self.assertEqual(claim['pg_adjustment_outstanding'], accepted)
                self.assertEqual(claim['confirmed_cash'], cash)
                self.assertEqual(claim['refund_bearer_policy'],
                                 'FIXTURE_FULL_GROSS_RECLASS' if name == 'full' else 'UNDEFINED')
                self.assertEqual(claim['fixture_reclassified'], name == 'full')
                if name == 'replay':
                    self.assertEqual(results[3]['receipt'], results[0]['receipt'] |
                                     {'duplicate': True, 'applied': None})
                    self.assertEqual(results[4]['receipt'], results[1]['receipt'] |
                                     {'duplicate': True, 'applied': None})
                    self.assertEqual(results[4]['receipt']['settlement']['claim']['refund_accepted'], 1000)
                for selector, stdin in ((str(path), None), ('-', path.read_text())):
                    result = self.cli(FIXTURE, selector, stdin)
                    self.assertEqual((result.returncode, result.stderr), (0, ''))
                    self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], results)

    def cli(self, fixture, selector='-', stdin=None):
        return subprocess.run([sys.executable, str(HERE/'ticket_operations_cli.py'),
            '--fixture', str(fixture), '--requests', selector], input=stdin,
            capture_output=True, text=True, check=False)

    def test_optional_injection_publication_forwarding_and_original_objects(self):
        value = json.loads(FIXTURE.read_text())
        injected = Mock()
        session = TicketOperationsSession(setup=value['setup'], offer_source=Mock(),
            presentation_source=Mock(), cancel_acceptance_source=injected)
        injected.assert_not_called()
        self.assertEqual(injected.mock_calls, [])
        self.assertIs(session.settlement._cancel_acceptance_adapter._source, injected)
        self.assertIs(session.settlement._cancel_acceptance_adapter._machine, machines(session)[0])
        self.assertEqual(snapshot(machines(session)), snapshot(direct_graph(value['setup'])))
        signature = inspect.signature(TicketSettlementSession.observe_recorded_cancel_acceptance)
        self.assertEqual(set(signature.parameters), {'self','settlement_id','source_id','idempotency_key'})
        for name in ('source_id', 'idempotency_key'):
            self.assertEqual(signature.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIs(signature.parameters[name].default, inspect.Parameter.empty)
        machine, injected = Mock(spec=SettlementMachine), Mock()
        with patch('ticket_operations_session.CancelAcceptanceAdapter') as construct:
            desk = TicketSettlementSession(machine, cancel_acceptance_source=injected)
            construct.assert_called_once_with(machine, injected)
            adapter = construct.return_value
            self.assertEqual(adapter.mock_calls, [])
            args = dict(settlement_id=object(), source_id=object(), idempotency_key=object())
            receipt = object()
            adapter.apply.return_value = receipt
            self.assertIs(dispatch_request(Mock(settlement=desk), dict(surface='settlement',
                operation='observe_recorded_cancel_acceptance', arguments=args))['receipt'], receipt)
            adapter.apply.assert_called_once_with(**args)
            adapter.reset_mock()
            failure = CancelAcceptanceSourceError('immediate synthetic fault')
            adapter.apply.side_effect = failure
            with self.assertRaises(CancelAcceptanceSourceError) as caught:
                desk.observe_recorded_cancel_acceptance(**args)
            self.assertIs(caught.exception, failure)
            adapter.apply.assert_called_once_with(**args)
            self.assertEqual(machine.mock_calls, [])
        # Optional old fixtures publish without any cancellation adapter or fetch.
        old = load_fixture(HERE/'fixtures/ticket_operations_session.json')
        before = snapshot(machines(old))
        self.assertIsNone(old.settlement._cancel_acceptance_adapter)
        status, rows = run(old, [observe(), request('view')])
        self.assertEqual(status, 1)
        self.assertEqual(rows[0]['error']['type'], 'CancelAcceptanceSourceError')
        self.assertIn('view', rows[1])
        self.assertEqual(snapshot(machines(old)), before)

    def test_source_failures_match_adapter_fetch_once_and_leave_key_free(self):
        cases = [(None, 'CancelAcceptanceNotFound'), ('{', 'InvalidCancelAcceptanceRecord'),
                 ('[]', 'InvalidCancelAcceptanceRecord'),
                 (json.dumps(record(extra=1)), 'InvalidCancelAcceptanceRecord')]
        for field in record():
            malformed = record()
            del malformed[field]
            cases.append((json.dumps(malformed), 'InvalidCancelAcceptanceRecord'))
        for field in ('settlement_id', 'source_id'):
            for invalid in ('other', 1, None):
                cases.append((json.dumps(record(**{field:invalid})), 'CancelAcceptanceIdentityMismatch'))
        cases += [(fault, 'CancelAcceptanceSourceError') for fault in SyntheticCancelAcceptanceFault]
        for recording, error_type in cases:
            with self.subTest(recording=recording):
                value = json.loads(FIXTURE.read_text())
                entry = dict(settlement_id=SID, source_id='acceptance-1')
                value['cancel_acceptances'] = ([] if recording is None else [entry | (
                    {'fault': recording.value} if isinstance(recording, SyntheticCancelAcceptanceFault)
                    else {'recorded_text': recording})])
                self.graph(value)
                self.step(bind(), raw=False)
                machine = machines(self.session)[0]
                with patch.object(machine, 'observe_mock_cancel_acceptance', wraps=machine.observe_mock_cancel_acceptance) as fsm:
                    for count in (1, 2):
                        result = self.step(observe(), raw=False)
                        self.assertEqual(result['error']['type'], error_type)
                        self.assertEqual(len(self.control_source.calls), count)
                    fsm.assert_not_called()
                # Next caller-supplied successful observation, same previously unused key.
                for desk, graph in ((self.session, machines(self.session)),
                                    (self.api, machines(self.api))):
                    desk.settlement = TicketSettlementSession(graph[0], cancel_acceptance_source=
                        FakeCancelAcceptanceSource(recordings={(SID,'acceptance-1'):json.dumps(record())}))
                self.control_source = FakeCancelAcceptanceSource(recordings={(SID,'acceptance-1'):json.dumps(record())})
                self.adapter = CancelAcceptanceAdapter(self.control[0], self.control_source)
                result = self.step(observe(), raw=False)
                self.assertFalse(result['receipt']['duplicate'])
                # Executable source error continues to the next explicit view, exit 1.
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory)/'fixture.json'
                    path.write_text(json.dumps(value))
                    text = '\n'.join(json.dumps(r) for r in [observe(),request('view')])+'\n'
                    result = self.cli(path, stdin=text)
                    self.assertEqual((result.returncode, result.stderr), (1,''))
                    output = [json.loads(line) for line in result.stdout.splitlines()]
                    self.assertEqual(output[0]['error']['type'], error_type)
                    self.assertIn('view', output[1])

    def test_economic_rejections_retained_keys_and_conflicts_at_both_phases(self):
        for phase in ('CAPTURED', 'COMMITTED'):
            self.graph()
            # Use explicit existing selectors to prepare a separate claim; preserve ticket anchor.
            sid = 'captured-refund'
            init = request('initiate', idempotency_key='extra-init', trade_id='extra-trade', gross=10001,
                debtor_role='extra-merchant', currency='KRW', policy=self.control[0].view(SID)['policy'])
            init['arguments']['settlement_id'] = sid
            self.step(init)
            for operation in ('authorize','capture'):
                row = request(operation, idempotency_key='extra-'+operation)
                row['arguments']['settlement_id'] = sid
                self.step(row)
            if phase == 'COMMITTED':
                self.step(request('commit', settlement_id=sid, idempotency_key='extra-commit',
                    movement_id='extra-movement', gross=10001, amount=10001, fee=0, tax=0,
                    held=0, adjustment=0, adjustment_reason=None))
            # New explicit source fixtures for the extra identity, no implicit copies in production.
            entries = [dict(settlement_id=sid, source_id=source_id,
                recorded_text=json.dumps(record(settlement_id=sid, source_id=source_id, amount=amount)))
                for source_id, amount in [('acceptance-1',1000),('too-much',4001),('bad-amount',True)]]
            for desk in (self.session,self.api):
                desk.settlement = TicketSettlementSession(machines(desk)[0], cancel_acceptance_source=source(entries))
            self.control_source = source(entries)
            self.adapter = CancelAcceptanceAdapter(self.control[0], self.control_source)
            def row_for(row):
                row['arguments']['settlement_id'] = sid
                return row
            rejected = row_for(observe(idempotency_key='missing-obligation'))
            self.step(rejected, 'REFUND_OBLIGATION_REQUIRED')
            self.step(row_for(bind()))
            self.step(rejected, 'REFUND_OBLIGATION_REQUIRED')
            self.step(row_for(observe(source_id='too-much',idempotency_key='too-much')),
                      'REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION')
            self.step(row_for(observe(source_id='bad-amount',idempotency_key='bad-amount')), 'INVALID_AMOUNT')
            first = self.step(row_for(observe()))
            claim = first['receipt']['settlement']['claim']
            self.assertEqual(claim['confirmed_cash'], 10001 if phase=='COMMITTED' else 0)
            self.assertEqual((claim['refund_outstanding'],claim['pg_adjustment_outstanding']), (3000,1000))
            for key in ('missing-obligation', 'too-much', 'bad-amount'):
                self.step(row_for(observe(idempotency_key=key)), 'IDEMPOTENCY_CONFLICT' if key!='missing-obligation'
                          else 'REFUND_OBLIGATION_REQUIRED')
            self.step(row_for(observe(source_id='too-much')), 'IDEMPOTENCY_CONFLICT')
            self.step(row_for(bind(amount=4001)), 'IDEMPOTENCY_CONFLICT')
            # Existing characterization: a repeated source under a new key journals no new economics.
            before = self.control[0].view(sid)['claim']
            length = len(self.control[0].export_journal())
            self.step(row_for(observe(idempotency_key='same-source-fresh-key')))
            self.assertEqual(self.control[0].view(sid)['claim'], before)
            self.assertEqual(len(self.control[0].export_journal()), length+1)

    def test_partial_obligation_fully_accepted_and_summed_bindings_keep_burden_undefined(self):
        self.graph()
        self.step(bind(amount=1000))
        self.step(observe())
        claim = self.control[0].view(SID)['claim']
        self.assertEqual(claim['refund_outstanding'],0)
        self.assertEqual(claim['refund_bearer_policy'],'UNDEFINED')
        self.step(bind(amount=9001, refund_id='refund-2', idempotency_key='refund-bind-2'))
        claim = self.control[0].view(SID)['claim']
        self.assertEqual(claim['refund_face'], 10001)
        self.assertFalse(claim['fixture_reclassified'])
        self.assertEqual(claim['refund_bearer_policy'],'UNDEFINED')
        for graph in (machines(self.session), machines(self.api), self.control, self.raw):
            before = snapshot(graph)
            self.assertEqual(outcome(lambda: graph[0].distribute(SID, idempotency_key='blocked',
                order=['organizer'])),
                {'error':{'code':'DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED'}})
            self.assertEqual(snapshot(graph),before)
        self.step(observe())

    def test_invalid_bindings_and_phases_preserve_direct_fsm_errors(self):
        self.graph()
        for index, change in enumerate([{'amount':True}, {'amount':0}, {'amount':10002},
                {'beneficiary_role':' bad '}, {'reason':None}, {'refund_id':''}]):
            row = bind(**(change | {'idempotency_key':f'bad-bind-{index}'}))
            expected = outcome(lambda: self.control[0].bind_refund(**row['arguments']))
            self.assertIn('error',expected)
            self.step(row, expected['error']['code'])
        init = request('initiate', settlement_id='early', idempotency_key='early-init', trade_id='early-trade',
            gross=10001, debtor_role='fixture-merchant', currency='KRW', policy=self.control[0].view(SID)['policy'])
        self.step(init)
        for row in (bind(), observe()):
            row['arguments']['settlement_id'] = 'early'
            row['arguments']['idempotency_key'] = 'early-'+row['operation']
            if row['operation']=='observe_recorded_cancel_acceptance':
                # A valid caller-supplied source is necessary to reach the FSM phase check.
                entries = [dict(settlement_id='early', source_id='acceptance-1',
                    recorded_text=json.dumps(record(settlement_id='early')))]
                for desk in (self.session,self.api):
                    desk.settlement = TicketSettlementSession(machines(desk)[0], cancel_acceptance_source=source(entries))
                self.control_source = source(entries)
                self.adapter = CancelAcceptanceAdapter(self.control[0], self.control_source)
            self.step(row,'ILLEGAL_TRANSITION')

    def test_strict_recording_fixture_schema_and_optional_compatibility(self):
        base = json.loads(FIXTURE.read_text())
        good = base['cancel_acceptances'][0]
        invalid = [None, {}, [None], [good|{'extra':1}], [good,good],
                   [good|{'fault':'synthetic_cancel_acceptance_error'}],
                   [good|{'recorded_text':None}]]
        invalid += [[{k:v for k,v in good.items() if k!=field}] for field in good]
        invalid += [[dict(settlement_id=SID,source_id='a',fault=fault)] for fault in (None,[],True,'bad')]
        invalid += [[good|{field:value}] for field in ('settlement_id','source_id')
                    for value in (None,[],True,' bad ','')]
        for entries in invalid:
            with self.subTest(entries=entries), patch('ticket_operations_session.SettlementMachine') as ctor:
                with self.assertRaises(FixtureError):
                    load_value(base|{'cancel_acceptances':entries})
                ctor.assert_not_called()
        for entries in ([], [good,good|{'source_id':'another'}],
                        [good,good|{'settlement_id':'another'}]):
            load_value(base|{'cancel_acceptances':entries})
        for path in HERE.glob('fixtures/ticket_operations*session.json'):
            desk = load_fixture(path)
            if 'cancel_acceptances' not in json.loads(path.read_text()):
                self.assertIsNone(desk.settlement._cancel_acceptance_adapter)
            else:
                self.assertEqual(desk.settlement._cancel_acceptance_adapter._source.calls, ())
        # Payload decoding belongs to explicit fetch, not fixture construction.
        desk = load_value(base|{'cancel_acceptances':[good|{'recorded_text':'{'}]})
        self.assertEqual(desk.settlement._cancel_acceptance_adapter._source.calls,())

    def test_cli_strict_json_exit_two_stops_after_prior_success(self):
        good = bind()
        variants = []
        for template in (bind(),observe()):
            for field in template['arguments']:
                row = deepcopy(template)
                del row['arguments'][field]
                variants.append(json.dumps(row))
            variants += [json.dumps(template|{'arguments':None}),
                         json.dumps(template|{'arguments':template['arguments']|{'extra':1}})]
        variants += [json.dumps(request(op)) for op in ('observe_external_payment','restore')]
        variants += [json.dumps(bind()).replace('4000',number) for number in ('NaN','Infinity','-Infinity','1e999')]
        variants += ['{"surface":"settlement","operation":"bind_refund","arguments":{"amount":1,"amount":2}}',
                     '{"surface":"settlement","surface":"booking","operation":"view","arguments":{}}']
        for bad in variants:
            desk = load_fixture(FIXTURE)
            before = snapshot(machines(desk))
            with redirect_stdout(io.StringIO()) as output:
                status = run_requests(desk,[bad,json.dumps(good)])
            self.assertEqual(status,2)
            self.assertEqual(len(output.getvalue().splitlines()),1)
            self.assertEqual(snapshot(machines(desk)),before)
            self.assertEqual(desk.settlement._cancel_acceptance_adapter._source.calls,())
        # Executable exits 2, preserves earlier output and stops at structural error.
        text = json.dumps(good)+'\n{}\n'+json.dumps(observe())+'\n'
        for file_mode in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'requests.jsonl'
                path.write_text(text)
                result = self.cli(FIXTURE,str(path) if file_mode else '-',None if file_mode else text)
                self.assertEqual((result.returncode,result.stderr),(2,''))
                self.assertEqual(len(result.stdout.splitlines()),2)
        # Structural fixture failures are also executable exit 2.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            path.write_text(json.dumps(json.loads(FIXTURE.read_text())|{'cancel_acceptances':{}}))
            result = self.cli(path,stdin='')
            self.assertEqual((result.returncode,result.stderr),(2,''))
            self.assertEqual(json.loads(result.stdout)['error']['type'],'FixtureError')
