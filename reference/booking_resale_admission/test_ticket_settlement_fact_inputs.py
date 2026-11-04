"""Source-informed request-time composition against direct public FSM controls."""

from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import admission_fixture  # Installs the sibling settlement reference path.
from fake_cancel_acceptance_source import FakeCancelAcceptanceSource
from fake_statement_source import FakeStatementSource
from settlement_fsm import SettlementMachine
from settlement_property_support import check_claim_view
from test_ticket_operations_session import direct_call, direct_graph, machines, outcome, snapshot
from test_ticket_settlement_controls import settlement_flags
from ticket_operations_cli import dispatch_request, run_requests
from ticket_operations_fixture import load_fixture

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures/ticket_operations_settlement_fact_inputs_session.json'
OBSERVATIONS = ('observe_statement', 'observe_mock_cancel_acceptance')
RECORDED = {'observe_recorded_statement': ('observe_statement', 'statements', 'movement_id'),
            'observe_recorded_cancel_acceptance': ('observe_mock_cancel_acceptance',
                                                  'cancel_acceptances', 'source_id')}


def path(name):
    return HERE / f'fixtures/ticket_operations_settlement_fact_inputs_{name}.jsonl'


def rows(name='journey'):
    return [json.loads(line) for line in path(name).read_text().splitlines()]


def changed(row, **args):
    return row | dict(arguments=row['arguments'] | args)


def request(operation, **args):
    return dict(surface='settlement', operation=operation,
                arguments=dict(settlement_id='claim-2') | args)


class FactInputEvidence:
    """Shared helpers only: importing this mixin does not duplicate test discovery."""

    def graph(self, value=None):
        self.value = deepcopy(value) if value is not None else json.loads(FIXTURE.read_text())
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'session.json'
            fixture.write_text(json.dumps(self.value))
            self.session, self.api = load_fixture(fixture), load_fixture(fixture)
        self.control = direct_graph(self.value['setup'])
        for session in (self.session, self.api):
            self.assertEqual(snapshot(machines(session)), snapshot(self.control))
        self.assert_sources_idle()

    def sources(self, session):
        return [adapter._source for adapter in (
            session.resale._adapter, session.resale._payment_adapter,
            session.admission._adapter, session.settlement._statement_adapter,
            session.settlement._cancel_acceptance_adapter) if adapter is not None]

    def assert_sources_idle(self):
        for session in (self.session, self.api):
            self.assertTrue(all(source.calls == () for source in self.sources(session)))

    def step(self, row, code=None):
        op, args = row['operation'], row['arguments']
        direct = row
        if op in RECORDED:
            method, table, identity = RECORDED[op]
            document = json.loads(next(e['recorded_text'] for e in self.value[table]
                if (e['settlement_id'], e[identity]) == (args['settlement_id'], args[identity])))
            direct = row | dict(operation=method,
                                arguments=document | dict(idempotency_key=args['idempotency_key']))
        expected = outcome(lambda: direct_call(self.control, direct, self.value))
        if 'error' not in expected:
            expected['operation'] = op
        for session, dispatch in ((self.session, True), (self.api, False)):
            graph = machines(session)
            before = snapshot(graph)
            fetches = [source.calls for source in self.sources(session)]
            with ExitStack() as stack:
                spy = None
                if op in OBSERVATIONS:
                    spy = stack.enter_context(patch.object(graph[0], op, wraps=getattr(graph[0], op)))
                    for other in ('distribute', 'bind_refund', 'commit', 'reconcile'):
                        stack.enter_context(patch.object(graph[0], other, side_effect=AssertionError(other)))
                    for machine in graph[1:]:
                        # Forbid clock adjustment and all public ticket mutators.
                        for name in ('set_clock', 'hold', 'release', 'confirm', 'cancel', 'observe_payment',
                                     'bind_settlement', 'issue', 'adopt_issued', 'list_resale',
                                     'observe_resale_payment', 'accept_resale', 'authorize_admission', 'consume'):
                            if hasattr(machine, name):
                                stack.enter_context(patch.object(machine, name, side_effect=AssertionError(name)))
                actual = outcome(lambda: dispatch_request(session, row) if dispatch else
                                 getattr(session.settlement, op)(**args))
                if spy is not None:
                    body = dict(args)
                    sid = body.pop('settlement_id')
                    spy.assert_called_once_with(sid, **body)
            key = 'view' if op == 'view' else 'receipt'
            self.assertEqual(actual, expected if dispatch or 'error' in expected else expected[key])
            self.assertEqual(snapshot(graph), snapshot(self.control))
            self.assertEqual(snapshot(graph)[1:], before[1:])
            if op not in RECORDED:
                self.assertEqual([source.calls for source in self.sources(session)], fetches)
            if 'error' in expected:
                self.assertEqual(snapshot(graph), before)
            else:
                settlement_flags(self, expected[key])
                claim = session.settlement.view(args['settlement_id'])['claim']
                if claim is not None:
                    check_claim_view(claim)
        if code is not None:
            self.assertEqual(expected, {'error': {'code': code}})
        return dict(surface='settlement', operation=op, **expected) if 'error' in expected else expected


class TicketSettlementFactInputsTests(FactInputEvidence, unittest.TestCase):
    def test_empty_and_omitted_sources_complete_explicit_journey(self):
        for omitted in (False, True):
            self.graph()
            value = self.value
            if omitted:
                for field in ('statements', 'cancel_acceptances'):
                    del value[field]
                self.graph(value)
                self.assertIsNone(self.session.settlement._statement_adapter)
                self.assertIsNone(self.session.settlement._cancel_acceptance_adapter)
            for i, row in enumerate(rows()):
                self.step(row)
                claim = self.session.settlement.view('claim-2')['claim']
                if i == 2:
                    self.assertEqual((claim['confirmed_cash'], claim['distributed_cash'],
                                      claim['refund_face']), (9301, 0, 0))
                if i == 5:
                    self.assertEqual((claim['refund_outstanding'], claim['refund_accepted']), (4000, 0))
            self.assertEqual({k: claim[k] for k in ('confirmed_cash', 'distributed_cash',
                'non_cash_accounted', 'receivable_open', 'refund_outstanding',
                'pg_adjustment_outstanding')}, dict(confirmed_cash=9301, distributed_cash=9301,
                non_cash_accounted=700, receivable_open=0, refund_outstanding=3000,
                pg_adjustment_outstanding=1000))
            self.assertEqual(claim['refund_bearer_policy'], 'UNDEFINED')
            # Completing the synthetic observation does not complete an external return.
            self.step(changed(rows()[6], idempotency_key='remaining', source_id='remaining', amount=3000))
            view = self.session.settlement.view('claim-2')
            self.assertEqual(view['claim']['refund_outstanding'], 0)
            settlement_flags(self, view)
            self.assert_sources_idle()
            restored = SettlementMachine.restore(self.control[0].export_journal())
            self.assertEqual(snapshot((restored,)), snapshot((self.control[0],)))

    def test_boundary_transcript_matches_direct_fsm(self):
        self.graph()
        results = [self.step(row) for row in rows('boundaries')]
        self.assertEqual([r['error']['code'] for r in results if 'error' in r], [
            'ILLEGAL_TRANSITION', 'REFUND_OBLIGATION_REQUIRED', 'ILLEGAL_TRANSITION',
            'IDEMPOTENCY_CONFLICT', 'STATEMENT_BINDING_CONFLICT', 'SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE',
            'REFUND_OBLIGATION_REQUIRED', 'IDEMPOTENCY_CONFLICT', 'ACCEPTANCE_BINDING_CONFLICT',
            'REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION'])
        for first, replay in ((4, 5), (12, 13)):
            self.assertEqual(results[replay]['receipt'], results[first]['receipt'] |
                             dict(duplicate=True, applied=None))
        self.assert_sources_idle()

    def test_recorded_direct_replay_both_directions_and_identity_conflicts(self):
        for recorded_op, (direct_op, table, identity) in RECORDED.items():
            for recorded_first in (False, True):
                self.graph()
                direct = rows()[2 if direct_op == 'observe_statement' else 6]
                document = {k: v for k, v in direct['arguments'].items() if k != 'idempotency_key'}
                value = self.value | {table: [document | dict(recorded_text=json.dumps(document))]}
                # Source envelope contains only identity fields and recorded text.
                value[table] = [{k: v for k, v in value[table][0].items()
                                 if k in ('settlement_id', identity, 'recorded_text')}]
                self.graph(value)
                self.step(rows()[0])
                if direct_op != 'observe_statement':
                    self.step(rows()[5])
                recorded = request(recorded_op, **{k: v for k, v in direct['arguments'].items()
                                                   if k in ('idempotency_key', identity)})
                first, second = (recorded, direct) if recorded_first else (direct, recorded)
                accepted = self.step(first)['receipt']
                if direct_op == 'observe_statement':
                    self.step(rows()[4])
                else:
                    self.step(changed(direct, idempotency_key='later-accept', source_id='later', amount=500))
                replay = self.step(second)['receipt']
                self.assertEqual(replay, accepted | dict(duplicate=True, applied=None))
                self.step(first)  # First source path still replays its original receipt.
                for changes in (dict(amount=999), dict(settlement_id='claim-1')):
                    self.step(changed(direct, **changes), 'IDEMPOTENCY_CONFLICT')
                self.step(request('reconcile', idempotency_key=direct['arguments']['idempotency_key']),
                          'IDEMPOTENCY_CONFLICT')
                # Fresh keys cannot change an established movement/source body.
                conflict = (dict(amount=3800, fee=201) if direct_op == 'observe_statement' else dict(amount=999))
                self.step(changed(direct, idempotency_key='identity-conflict', **conflict),
                          'STATEMENT_BINDING_CONFLICT' if direct_op == 'observe_statement' else 'ACCEPTANCE_BINDING_CONFLICT')
                # Movement/source identities are scoped per settlement.
                self.step(request('initiate', settlement_id='scope', idempotency_key='scope-init',
                    trade_id='scope-trade', gross=10001, debtor_role='fixture-merchant', currency='KRW',
                    policy=self.session.settlement.view('claim-2')['policy']))
                for op in ('authorize', 'capture'):
                    self.step(request(op, settlement_id='scope', idempotency_key='scope-'+op))
                self.step(changed(rows()[0], settlement_id='scope', idempotency_key='scope-commit'))
                self.step(changed(rows()[5], settlement_id='scope', idempotency_key='scope-refund'))
                self.step(changed(direct, settlement_id='scope', idempotency_key='scope-fact'))
                for session in (self.session, self.api):
                    adapter = (session.settlement._statement_adapter if table == 'statements'
                               else session.settlement._cancel_acceptance_adapter)
                    self.assertEqual(adapter._source.calls,
                        ((document['settlement_id'], document[identity]),) * (2 if recorded_first else 1))
                # A source returning changed fields must conflict in the same FSM key space.
                altered = document | conflict
                self.value[table][0]['recorded_text'] = json.dumps(altered)
                for session in (self.session, self.api):
                    adapter = (session.settlement._statement_adapter if table == 'statements'
                               else session.settlement._cancel_acceptance_adapter)
                    source = FakeStatementSource if table == 'statements' else FakeCancelAcceptanceSource
                    adapter._source = source(recordings={
                        (document['settlement_id'], document[identity]): json.dumps(altered)})
                self.step(recorded, 'IDEMPOTENCY_CONFLICT')
                self.step(changed(recorded, idempotency_key='recorded-binding-conflict'),
                          'STATEMENT_BINDING_CONFLICT' if direct_op == 'observe_statement'
                          else 'ACCEPTANCE_BINDING_CONFLICT')

    def test_invalid_components_retain_original_refusals(self):
        cases = [(dict(amount=True), 'INVALID_NONNEGATIVE'), (dict(gross=True), 'INVALID_AMOUNT'),
                 (dict(gross=10**12+1), 'INVALID_AMOUNT'), (dict(fee=-1), 'INVALID_NONNEGATIVE'),
                 (dict(tax='0'), 'INVALID_NONNEGATIVE'), (dict(held=None), 'INVALID_NONNEGATIVE'),
                 (dict(adjustment=True), 'INVALID_NONNEGATIVE'),
                 (dict(amount=3800), 'SETTLEMENT_COMPONENT_MISMATCH'),
                 (dict(adjustment_reason='unexpected'), 'ADJUSTMENT_REASON_UNEXPECTED'),
                 (dict(adjustment=1, amount=3800), 'ADJUSTMENT_REASON_REQUIRED'),
                 (dict(movement_id=''), 'INVALID_ID')]
        for changes, code in cases:
            with self.subTest(changes=changes):
                self.graph()
                self.step(rows()[0])
                bad = changed(rows()[2], idempotency_key='refused', **changes)
                self.step(bad, code)
                self.step(changed(rows()[2], idempotency_key='refused'), 'IDEMPOTENCY_CONFLICT')
                self.step(rows()[2])
                self.step(bad, code)
        for amount in (True, 0, -1, '1', None, 10**12+1):
            with self.subTest(amount=amount):
                self.graph()
                self.step(rows()[5])  # Refund binding is already legal while CAPTURED.
                bad = changed(rows()[6], amount=amount, idempotency_key='refused')
                self.step(bad, 'INVALID_AMOUNT')
                self.step(changed(rows()[6], idempotency_key='refused'), 'IDEMPOTENCY_CONFLICT')
                self.step(rows()[0])
                self.step(rows()[6])
                self.step(bad, 'INVALID_AMOUNT')

    def test_unknown_and_pre_capture_phases_match_and_retain_keys(self):
        for phase in ('INITIATED', 'AUTHORIZED'):
            self.graph()
            value = self.value
            removed = ('authorize', 'capture') if phase == 'INITIATED' else ('capture',)
            value['setup'] = [e for e in value['setup'] if not (
                e['machine'] == 'settlement' and e['subject_id'] == 'claim-2' and e['operation'] in removed)]
            self.graph(value)
            for row in (rows()[2], rows()[6]):
                self.step(row, 'ILLEGAL_TRANSITION')
            if phase == 'INITIATED':
                self.step(request('authorize', idempotency_key='advance-auth'))
            self.step(request('capture', idempotency_key='advance-capture'))
            self.step(rows()[0])
            self.step(rows()[5])
            for row in (rows()[2], rows()[6]):
                self.step(row, 'ILLEGAL_TRANSITION')
                self.step(changed(row, idempotency_key='fresh-'+row['operation']))
        for row in (rows()[2], rows()[6]):
            self.graph()
            missing = changed(row, settlement_id='missing')
            self.step(missing, 'UNKNOWN_SETTLEMENT')
            self.step(row, 'IDEMPOTENCY_CONFLICT')

    def test_structural_rejections_do_not_delegate_or_bind_keys(self):
        for row in (rows()[2], rows()[6]):
            args = row['arguments']
            variants = [row | dict(arguments=bad) for bad in (
                None, [], args | dict(extra=1), *[{k: v for k, v in args.items() if k != field} for field in args])]
            texts = [json.dumps(v) for v in variants]
            text = json.dumps(row)
            texts += [text.replace('"amount": '+str(args['amount']), '"amount": '+number)
                      for number in ('NaN', 'Infinity', '-Infinity', '1e999')]
            texts += [text.replace('"amount":', '"amount": 1, "amount":'), '{', '[]']
            for text in texts:
                self.graph()
                self.step(rows()[0])
                self.step(rows()[5])
                before = snapshot(machines(self.session))
                with patch.object(machines(self.session)[0], row['operation']) as delegate, \
                        redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(run_requests(self.session, [text, json.dumps(row)]), 2)
                    delegate.assert_not_called()
                self.assertEqual(len(output.getvalue().splitlines()), 1)
                self.assertEqual(json.loads(output.getvalue())['error']['type'], 'FixtureError')
                self.assertEqual(snapshot(machines(self.session)), before)
                self.assertFalse(self.step(row)['receipt']['duplicate'])
