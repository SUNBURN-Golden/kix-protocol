"""Source-informed local composition evidence against unchanged direct FSMs."""

from contextlib import redirect_stdout
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
from fake_statement_source import FakeStatementSource, SyntheticStatementFault
from settlement_fsm import SettlementError, SettlementMachine
from settlement_property_support import check_claim_view
from statement_source import (InvalidStatementRecord, StatementIdentityMismatch,
                              StatementNotFound, StatementSourceError)
from test_ticket_operations_session import direct_call, direct_graph, machines, snapshot
from test_ticket_settlement_controls import settlement_flags
from ticket_operations_cli import dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession, TicketSettlementSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_statement_session.json'
SID = 'claim-2'
RECORDED = {'commit_recorded_statement': 'commit',
            'observe_recorded_statement': 'observe_statement'}
ORDER = ['platform', 'organizer']


def request(operation, **args):
    return dict(surface='settlement', operation=operation,
                arguments=dict(settlement_id=SID) | args)


def rows(name='distribution'):
    return [json.loads(line) for line in path(name).read_text().splitlines()]


def path(name):
    return HERE / f'fixtures/ticket_operations_statement_{name}.jsonl'


def outcome(call):
    try:
        return call()
    except SettlementError as error:
        return {'error': {'code': error.code}}


class TicketStatementDistributionTests(unittest.TestCase):
    def graph(self):
        self.value = json.loads(FIXTURE.read_text())
        self.session, self.api = load_fixture(FIXTURE), load_fixture(FIXTURE)
        self.control = direct_graph(self.value['setup'])
        self.calls = []
        for session in (self.session, self.api):
            graph = machines(session)
            adapter = session.settlement._statement_adapter
            self.assertIs(adapter._machine, graph[0])
            for consumer in graph[1:]:
                self.assertIs(consumer._settlement, graph[0])
            self.assertEqual(adapter._source.calls, ())
            self.assertEqual(snapshot(graph), snapshot(self.control))

    def document(self, movement='statement-1'):
        return json.loads(next(e['recorded_text'] for e in self.value['statements']
                               if e['movement_id'] == movement))

    def step(self, row, code=None, document=None):
        before = snapshot(machines(self.session))
        op, args = row['operation'], row['arguments']
        direct = row
        if op in RECORDED:
            document = self.document(args['movement_id']) if document is None else document
            direct = row | dict(operation=RECORDED[op], arguments=document |
                                dict(idempotency_key=args['idempotency_key']))
            self.calls.append((args['settlement_id'], args['movement_id']))
        expected = outcome(lambda: direct_call(self.control, direct, self.value))
        if 'error' not in expected:
            expected['operation'] = op
        actual = outcome(lambda: dispatch_request(self.session, row))
        api = outcome(lambda: getattr(getattr(self.api, row['surface']), op)(**args))
        key = 'view' if op.startswith('view') else 'receipt'
        self.assertEqual(actual, expected)
        self.assertEqual(api, expected if 'error' in expected else expected[key])
        for session in (self.session, self.api):
            self.assertEqual(snapshot(machines(session)), snapshot(self.control))
            self.assertEqual(session.settlement._statement_adapter._source.calls, tuple(self.calls))
            for source in (session.resale._adapter._source,
                           session.resale._payment_adapter._source,
                           session.admission._adapter._source):
                self.assertEqual(source.calls, ())
        if code:
            self.assertEqual(actual, {'error': {'code': code}})
        if 'error' in actual:
            self.assertEqual(snapshot(machines(self.session)), before)
            return dict(surface=row['surface'], operation=op, **actual)
        if row['surface'] == 'settlement':
            self.assertEqual(snapshot(machines(self.session))[1:], before[1:])
            settlement_flags(self, actual[key])
            claim = self.session.settlement.view(SID)['claim']
            check_claim_view(claim)
            if op in RECORDED:
                prior = self._claim_from_snapshot(before)
                self.assertEqual(claim['distributed_cash'], prior['distributed_cash'])
        return actual

    def _claim_from_snapshot(self, state):
        # Public restored view, rather than relying on canonical JSON layout.
        return SettlementMachine.restore(state[0][2]).view(SID)['claim']

    def cli(self, fixture=FIXTURE, selector='-', stdin=None):
        return subprocess.run([sys.executable, str(HERE/'ticket_operations_cli.py'),
            '--fixture', str(fixture), '--requests', str(selector)], input=stdin,
            capture_output=True, text=True, check=False)

    def test_file_stdin_and_api_journeys_match_direct_fsm_after_every_step(self):
        codes = ['DISTRIBUTION_ORDER_TYPE', 'DISTRIBUTION_ORDER_DUPLICATE',
                 'DISTRIBUTION_ORDER_MISMATCH', 'DISTRIBUTION_ORDER_MISMATCH',
                 'IDEMPOTENCY_CONFLICT', 'IDEMPOTENCY_CONFLICT', 'DISTRIBUTION_ORDER_FROZEN',
                 'DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED']
        for name in ('distribution', 'boundaries'):
            with self.subTest(name=name):
                self.graph()
                results = [self.step(row) for row in rows(name)]
                self.assertEqual([r['error']['code'] for r in results if 'error' in r],
                                 [] if name == 'distribution' else codes)
                claim = self.session.settlement.view(SID)['claim']
                self.assertEqual(claim['confirmed_cash'], 9301)
                self.assertEqual(claim['distributed_cash'], 9301)
                self.assertEqual(claim['undistributed_cash'], 0)
                self.assertEqual(claim['non_cash_accounted'], 700)
                self.assertEqual(claim['receivable_open'], 0)
                self.assertEqual(claim['distribution_order'], ORDER)
                self.assertEqual(sum(line['outstanding'] for line in claim['obligations']), 700)
                statements = [e['body'] for e in machines(self.session)[0].export_journal()
                              if e['op'] == 'commit' and e['settlement_id'] == SID]
                self.assertEqual((statements[0]['tax'], statements[0]['held']), (100, 100))
                if name == 'distribution':
                    self.assertEqual(results[4]['receipt']['effect'], {'platform': 500, 'organizer': 5000})
                    self.assertEqual(results[8]['receipt']['effect'], {'platform': 0, 'organizer': 3801})
                    self.assertEqual(results[3]['receipt']['reservation']['phase'], 'ISSUED')
                else:
                    for replay, first in ((6, 1), (12, 5), (13, 10)):
                        self.assertEqual(results[replay]['receipt'], results[first]['receipt'] |
                                         {'duplicate': True, 'applied': None})
                    self.assertEqual(claim['refund_bearer_policy'], 'UNDEFINED')
                restored = SettlementMachine.restore(machines(self.session)[0].export_journal())
                self.assertEqual(snapshot((restored,)), snapshot((self.control[0],)))
                for selector, stdin in ((path(name), None), ('-', path(name).read_text())):
                    result = self.cli(selector=selector, stdin=stdin)
                    self.assertEqual((result.returncode, result.stderr), (0 if name == 'distribution' else 1, ''))
                    self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], results)

    def test_retained_order_refusals_type_key_freedom_and_refund_block(self):
        self.graph()
        self.step(rows()[0])
        for i, (order, code) in enumerate(((None, 'DISTRIBUTION_ORDER_TYPE'),
                (['platform', 'platform'], 'DISTRIBUTION_ORDER_DUPLICATE'),
                ([], 'DISTRIBUTION_ORDER_MISMATCH'),
                (['platform', 'unknown'], 'DISTRIBUTION_ORDER_MISMATCH'))):
            key = f'bad-order-{i}'
            bad = request('distribute', idempotency_key=key, order=order)
            self.step(bad, code)
            good = request('distribute', idempotency_key=key, order=ORDER)
            self.step(good, None if order is None else 'IDEMPOTENCY_CONFLICT')
            self.step(bad, code)
        self.step(request('distribute', idempotency_key='frozen', order=list(reversed(ORDER))),
                  'DISTRIBUTION_ORDER_FROZEN')
        self.step(rows()[6])  # Later statement adds cash, never distributes it.
        prior = self.session.settlement.view(SID)['claim']
        self.assertEqual((prior['distributed_cash'], prior['undistributed_cash']), (5500, 3801))
        self.step(request('bind_refund', idempotency_key='refund', refund_id='refund', amount=1000,
                          beneficiary_role='buyer-3', reason='synthetic'))
        self.step(request('distribute', idempotency_key='blocked', order=ORDER),
                  'DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED')
        self.assertEqual(self.session.settlement.view(SID)['claim']['distributed_cash'], 5500)
        # Same accepted distribution key/body replays its first receipt despite refund block.
        self.step(request('distribute', idempotency_key='bad-order-0', order=ORDER))

    def test_direct_recorded_key_equivalence_conflicts_and_movement_characterization(self):
        self.graph()
        initial = self.step(rows()[0])
        self.step(request('commit', **{k:v for k,v in self.document().items() if k!='settlement_id'},
                          idempotency_key='recorded-commit'))
        self.step(rows()[4])
        replay = self.step(rows()[0])
        self.assertEqual(replay['receipt'], initial['receipt'] | {'duplicate': True, 'applied': None})
        self.assertEqual(replay['receipt']['settlement']['claim']['distributed_cash'], 0)
        self.step(request('observe_recorded_statement', movement_id='statement-1',
                          idempotency_key='recorded-commit'), 'IDEMPOTENCY_CONFLICT')
        before = self.session.settlement.view(SID)['claim']
        journal = machines(self.session)[0].export_journal()
        self.step(request('observe_recorded_statement', movement_id='statement-1', idempotency_key='inert'))
        self.assertEqual(self.session.settlement.view(SID)['claim'], before)
        self.assertEqual(len(machines(self.session)[0].export_journal()), len(journal)+1)
        changed = self.document() | dict(amount=5499, fee=201)
        for session in (self.session, self.api):
            session.settlement._statement_adapter._source = FakeStatementSource(recordings={
                (SID, 'statement-1'): json.dumps(changed)})
        self.calls = []
        self.step(rows()[0], 'IDEMPOTENCY_CONFLICT', document=changed)
        self.step(request('observe_recorded_statement', movement_id='statement-1', idempotency_key='binding'),
                  'STATEMENT_BINDING_CONFLICT', document=changed)

    def test_injection_no_construction_fetch_and_exact_adapter_forwarding(self):
        value = json.loads(FIXTURE.read_text())
        source = Mock()
        session = TicketOperationsSession(setup=value['setup'], offer_source=Mock(),
            presentation_source=Mock(), statement_source=source)
        self.assertEqual(source.mock_calls, [])
        self.assertIs(session.settlement._statement_adapter._source, source)
        self.assertIs(session.settlement._statement_adapter._machine, machines(session)[0])
        self.assertEqual(snapshot(machines(session)), snapshot(direct_graph(value['setup'])))
        for selector, operation in RECORDED.items():
            signature = inspect.signature(getattr(TicketSettlementSession, selector))
            self.assertEqual(set(signature.parameters), {'self','settlement_id','movement_id','idempotency_key'})
            for name, parameter in signature.parameters.items():
                self.assertIs(parameter.default, inspect.Parameter.empty)
                if name not in ('self','settlement_id'):
                    self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            machine = Mock(spec=SettlementMachine)
            with patch('ticket_operations_session.StatementAdapter') as construct:
                desk = TicketSettlementSession(machine, statement_source=source)
                construct.assert_called_once_with(machine, source)
                adapter = construct.return_value
                self.assertEqual(adapter.mock_calls, [])
                args = dict(settlement_id=object(), movement_id=object(), idempotency_key=object())
                receipt = object()
                adapter.apply.return_value = receipt
                self.assertIs(dispatch_request(Mock(settlement=desk), request(selector) |
                    dict(arguments=args))['receipt'], receipt)
                adapter.apply.assert_called_once_with(operation=operation, **args)
                adapter.reset_mock()
                error = StatementSourceError('synthetic')
                adapter.apply.side_effect = error
                with self.assertRaises(StatementSourceError) as caught:
                    getattr(desk, selector)(args['settlement_id'], movement_id=args['movement_id'],
                                            idempotency_key=args['idempotency_key'])
                self.assertIs(caught.exception, error)
                adapter.apply.assert_called_once_with(operation=operation, **args)
                self.assertEqual(machine.mock_calls, [])
        old = load_fixture(HERE/'fixtures/ticket_operations_session.json')
        self.assertIsNone(old.settlement._statement_adapter)
        for selector in RECORDED:
            with redirect_stdout(io.StringIO()) as output:
                status = run_requests(old, [json.dumps(request(selector, movement_id='absent',
                    idempotency_key='free')), json.dumps(request('view', settlement_id='claim-1'))])
            self.assertEqual(status, 1)
            self.assertEqual(json.loads(output.getvalue().splitlines()[0])['error']['type'], 'StatementSourceError')
            self.assertEqual(len(output.getvalue().splitlines()), 2)

    def test_source_failures_fetch_once_no_fsm_call_or_key_binding(self):
        self.value = json.loads(FIXTURE.read_text())
        document = self.document()
        missing = dict(document)
        del missing['tax']
        cases = [(None, StatementNotFound), ('{', InvalidStatementRecord),
                 ('[]', InvalidStatementRecord), (json.dumps(missing), InvalidStatementRecord),
                 (json.dumps(document | dict(extra=0)), InvalidStatementRecord),
                 (json.dumps(document | dict(settlement_id='other')), StatementIdentityMismatch),
                 (json.dumps(document | dict(movement_id='other')), StatementIdentityMismatch),
                 (json.dumps(document | dict(movement_id=1)), StatementIdentityMismatch),
                 (SyntheticStatementFault.ERROR, StatementSourceError),
                 (SyntheticStatementFault.TIMEOUT, StatementSourceError)]
        for selector in RECORDED:
            for recording, error_type in cases:
                with self.subTest(selector=selector, recording=recording):
                    session = load_fixture(FIXTURE)
                    book = machines(session)[0]
                    if selector == 'observe_recorded_statement':
                        # Seed a disjoint movement through the preserved direct commit method.
                        seed = document | dict(movement_id='seed', gross=1, amount=1,
                            fee=0, tax=0, held=0, adjustment=0, adjustment_reason=None)
                        session.settlement.commit(**seed, idempotency_key='seed')
                    source = FakeStatementSource(recordings={} if recording is None else {(SID,'statement-1'):recording})
                    session.settlement = TicketSettlementSession(book, statement_source=source)
                    before = snapshot(machines(session))
                    args = dict(settlement_id=SID, movement_id='statement-1', idempotency_key='free')
                    with patch.object(book, 'commit', wraps=book.commit) as commit, \
                            patch.object(book, 'observe_statement', wraps=book.observe_statement) as observe:
                        with self.assertRaises(error_type):
                            dispatch_request(session, request(selector) | dict(arguments=args))
                        commit.assert_not_called()
                        observe.assert_not_called()
                    self.assertEqual(source.calls, ((SID, 'statement-1'),))
                    self.assertEqual(snapshot(machines(session)), before)
                    # Replace only the source; the same live machine accepts the exact key.
                    valid = FakeStatementSource(recordings={(SID,'statement-1'):json.dumps(document)})
                    session.settlement = TicketSettlementSession(book, statement_source=valid)
                    self.assertFalse(getattr(session.settlement, selector)(**args)['duplicate'])
                    self.assertEqual(valid.calls, ((SID,'statement-1'),))
                    self.assertEqual(book.view(SID)['claim']['distributed_cash'], 0)

    def test_economic_invalid_records_reach_fsm_and_retain_refusals(self):
        for selector in RECORDED:
            self.graph()
            if selector == 'observe_recorded_statement':
                self.step(rows()[0])
                movement = 'statement-2'
            else:
                movement = 'statement-1'
            document = self.document(movement)
            bad = document | dict(amount=document['amount']-1)
            for session in (self.session, self.api):
                session.settlement._statement_adapter._source = FakeStatementSource(recordings={
                    (SID,movement):json.dumps(bad)})
            self.calls = []
            row = request(selector, movement_id=movement, idempotency_key='bad-record')
            self.step(row, 'SETTLEMENT_COMPONENT_MISMATCH', document=bad)
            for session in (self.session, self.api):
                session.settlement._statement_adapter._source = FakeStatementSource(recordings={
                    (SID,movement):json.dumps(document)})
            self.calls = []
            self.step(row, 'IDEMPOTENCY_CONFLICT')
            self.step(row | dict(arguments=row['arguments'] | dict(idempotency_key='corrected')))

    def test_strict_optional_fixture_schema_defers_record_decoding(self):
        value = json.loads(FIXTURE.read_text())
        entry = value['statements'][0]
        invalid = [None, {}, [None], [entry, entry], [entry | dict(extra=0)],
            [entry | dict(fault='synthetic_statement_timeout')],
            [{k:v for k,v in entry.items() if k!='recorded_text'}],
            [entry | dict(recorded_text=None)], [entry | dict(settlement_id='')],
            [entry | dict(movement_id=42)], [entry | dict(movement_id=' padded ')]]
        invalid += [[{k:v for k,v in entry.items() if k!='recorded_text'} | dict(fault=fault)]
                    for fault in (None, [], {}, 1, 'timeout')]
        invalid += [[{k:v for k,v in entry.items() if k!=field}] for field in ('settlement_id','movement_id')]
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'fixture.json'
            for recordings in invalid:
                file.write_text(json.dumps(value | dict(statements=recordings)))
                with self.subTest(recordings=recordings), patch('ticket_operations_fixture.TicketOperationsSession') as ctor:
                    with self.assertRaises(FixtureError):
                        load_fixture(file)
                    ctor.assert_not_called()
            for recordings in ([], [entry | dict(recorded_text='{')],
                    [entry, entry | dict(settlement_id='other')],
                    [entry, entry | dict(movement_id='other')],
                    [dict(settlement_id=SID,movement_id='fault',fault='synthetic_statement_error')],
                    [dict(settlement_id=SID,movement_id='fault',fault='synthetic_statement_timeout')]):
                file.write_text(json.dumps(value | dict(statements=recordings)))
                session = load_fixture(file)
                self.assertEqual(session.settlement._statement_adapter._source.calls, ())
            # Optional compatibility holds for every old shared-desk fixture.
            for file in (HERE/'fixtures').glob('ticket_operations*session.json'):
                if file != FIXTURE:
                    self.assertIsNone(load_fixture(file).settlement._statement_adapter)

    def test_cli_source_errors_continue_structural_errors_stop(self):
        value = json.loads(FIXTURE.read_text())
        entries = [dict(settlement_id=SID,movement_id='malformed',recorded_text='{'),
                   dict(settlement_id=SID,movement_id='mismatch',recorded_text=json.dumps(
                       dict(settlement_id='other',movement_id='mismatch',gross=1,amount=1,
                            fee=0,tax=0,held=0,adjustment=0,adjustment_reason=None))),
                   dict(settlement_id=SID,movement_id='timeout',fault='synthetic_statement_timeout')]
        with tempfile.TemporaryDirectory() as directory:
            file, requests = Path(directory)/'fixture.json', Path(directory)/'requests.jsonl'
            file.write_text(json.dumps(value | dict(statements=entries)))
            for selector in RECORDED:
                text = ''.join(json.dumps(request(selector, movement_id=movement,
                    idempotency_key='still-free'))+'\n' for movement in ('missing','malformed','mismatch','timeout'))
                text += json.dumps(request('view'))+'\n'
                for as_file in (False, True):
                    requests.write_text(text)
                    result = self.cli(file, requests if as_file else '-', None if as_file else text)
                    self.assertEqual((result.returncode, result.stderr), (1,''))
                    outputs = [json.loads(line) for line in result.stdout.splitlines()]
                    self.assertEqual([o['error']['type'] for o in outputs[:-1]],
                        ['StatementNotFound','InvalidStatementRecord','StatementIdentityMismatch','StatementSourceError'])
                    self.assertEqual(outputs[-1]['view']['phase'], 'CAPTURED')
            self.graph()
            before = snapshot(machines(self.session))
            for op, fields in [(op, {'settlement_id','movement_id','idempotency_key'}) for op in RECORDED] + [
                    ('distribute', {'settlement_id','idempotency_key','order'})]:
                args = dict.fromkeys(fields, 'x')
                for bad in (None, [], args | dict(extra=0),
                            *[{k:v for k,v in args.items() if k!=field} for field in fields]):
                    with redirect_stdout(io.StringIO()) as output:
                        status = run_requests(self.session, [json.dumps(request(op) | dict(arguments=bad)),
                                                             json.dumps(rows()[0])])
                    self.assertEqual(status, 2)
                    self.assertEqual(len(output.getvalue().splitlines()), 1)
                    self.assertEqual(snapshot(machines(self.session)), before)
                    self.assertEqual(self.session.settlement._statement_adapter._source.calls, ())
            text = json.dumps(request('view'))+'\n{}\n'+json.dumps(rows()[0])+'\n'
            for as_file in (False, True):
                requests.write_text(text)
                result = self.cli(FIXTURE, requests if as_file else '-', None if as_file else text)
                self.assertEqual((result.returncode, result.stderr), (2,''))
                self.assertEqual(len(result.stdout.splitlines()), 2)
