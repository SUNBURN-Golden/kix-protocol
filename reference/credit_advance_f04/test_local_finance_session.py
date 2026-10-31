"""Boundary parity over actual FSMs; existing suites own economic predicates."""

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from local_finance_session import (
    CREDIT_OPERATIONS, SETTLEMENT_OPERATIONS, LocalFinanceSession,
)
from local_finance_cli import decode_fixture, validate_fixture
from credit_fsm import CreditError, CreditMachine
from settlement_fsm import SettlementError, SettlementMachine
from fake_statement_source import SyntheticStatementFault
from statement_source import StatementSourceError

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name="journey"):
    return decode_fixture((FIXTURES / ("finance_" + name + ".synthetic.json")).read_text())


def outcome(call):
    try:
        return ("value", call())
    except (CreditError, SettlementError, StatementSourceError) as error:
        return (type(error).__name__, getattr(error, "code", None), str(error))


class LocalFinanceSessionTests(unittest.TestCase):
    def test_fixtures_match_direct_fsm_at_every_step_and_credit_is_read_only(self):
        for name in ("journey", "isolation"):
            with self.subTest(fixture=name):
                fixture = load_fixture(name)
                recordings, steps = validate_fixture(fixture)
                session = LocalFinanceSession(recordings=recordings)
                settlement = SettlementMachine()
                credit = CreditMachine(settlement_source=settlement)
                snapshots = {}
                source_calls = []
                for index, step in enumerate(steps):
                    with self.subTest(step=index):
                        before = (session.settlement_machine.canonical_state(), session.settlement_machine.export_journal())
                        op, target = step["operation"], step["target"]
                        if op == "view":
                            sid = step.get("settlement_id", step.get("advance_id"))
                            actual = session.settlement_view(sid) if target == "settlement" else session.credit_view(sid)
                            expected = settlement.view(sid) if target == "settlement" else credit.view(sid)
                            self.assertEqual(actual, expected)
                            if "save_claim_as" in step:
                                snapshots[step["save_claim_as"]] = copy.deepcopy(expected["claim"])
                                # Later output edits must not affect either machine or saved face.
                                actual["claim"]["gross"] = -1
                        elif op == "view_claim":
                            self.assertEqual(session.credit_claim_view(step["claim_id"]), credit.view_claim(step["claim_id"]))
                        else:
                            body = copy.deepcopy(step["body"])
                            if "face_ref" in step:
                                body["face"] = copy.deepcopy(snapshots[step["face_ref"]])
                            key = step["idempotency_key"]
                            if target == "settlement":
                                sid = step["settlement_id"]
                                actual = outcome(lambda: session.settlement(op, sid, idempotency_key=key, **body))
                                if op in ("commit", "observe_statement"):
                                    source_calls.append((sid, body["movement_id"]))
                                    record = json.loads(recordings[(sid, body["movement_id"])])
                                    body = {k: v for k, v in record.items() if k != "settlement_id"}
                                    direct = {"commit": SettlementMachine.commit, "observe_statement": SettlementMachine.observe_statement}[op]
                                else:
                                    direct = SETTLEMENT_OPERATIONS[op]
                                expected = outcome(lambda: direct(settlement, sid, idempotency_key=key, **body))
                            else:
                                aid = step["advance_id"]
                                actual = outcome(lambda: session.credit(op, aid, idempotency_key=key, **body))
                                expected = outcome(lambda: CREDIT_OPERATIONS[op](credit, aid, idempotency_key=key, **body))
                            self.assertEqual(actual, expected)
                        if target == "credit":
                            self.assertEqual(before, (session.settlement_machine.canonical_state(), session.settlement_machine.export_journal()))
                        self.assertEqual(session.settlement_machine.canonical_state(), settlement.canonical_state())
                        self.assertEqual(session.credit_machine.canonical_state(), credit.canonical_state())
                        self.assertEqual(session.statement_source.calls, tuple(source_calls))
                if name == "journey":
                    final = session.credit_view("journey-credit")
                    self.assertEqual((final["phase"], final["repaid_exposure"], final["outstanding_exposure"]), ("CLOSED", 40000, 0))
                    self.assertEqual(final["confirmed_cash_on_face"], 0)  # saved before statements
                    self.assertEqual(session.settlement_view("journey-settlement")["claim"]["confirmed_cash"], 93000)
                else:
                    a = session.settlement_view("isolation-a")["claim"]
                    b = session.settlement_view("isolation-b")["claim"]
                    self.assertEqual((a["confirmed_cash"], b["confirmed_cash"]), (97000, 70000))
                    self.assertEqual((a["distributed_cash"], b["distributed_cash"]), (97000, 0))
                    self.assertEqual(session.credit_claim_view("isolation-a")["reserved_open"], 40000)
                    self.assertEqual(session.credit_claim_view("isolation-b")["reserved_open"], 40000)

    def test_allowlisted_calls_forward_once_and_return_or_raise_original_objects(self):
        session = LocalFinanceSession(recordings={})
        for target, table, machine in (("settlement", SETTLEMENT_OPERATIONS, session.settlement_machine), ("credit", CREDIT_OPERATIONS, session.credit_machine)):
            for op, method in list(table.items()):
                self.assertEqual(method.__name__, op)
                import inspect
                body = {name: object() for name, p in inspect.signature(method).parameters.items()
                        if name not in ("self", "settlement_id" if target == "settlement" else "advance_id", "idempotency_key")
                        and p.default is inspect.Parameter.empty}
                result = object()
                spy = Mock(spec=method, return_value=result)
                spy.__signature__ = inspect.signature(method)
                error = CreditError("MOCK_INVARIANT") if target == "credit" else SettlementError("MOCK_INVARIANT")
                with patch.dict(table, {op: spy}):
                    call = session.credit if target == "credit" else session.settlement
                    self.assertIs(call(op, "id", idempotency_key="caller-key", **body), result)
                    spy.assert_called_once_with(machine, "id", idempotency_key="caller-key", **body)
                    spy.reset_mock()
                    spy.side_effect = error
                    with self.assertRaises(type(error)) as raised:
                        call(op, "id", idempotency_key="same-caller-key", **body)
                    self.assertIs(raised.exception, error)
                    spy.assert_called_once_with(machine, "id", idempotency_key="same-caller-key", **body)
        for op in ("commit", "observe_statement"):
            with patch.object(session.statement_adapter, "apply", return_value={}) as spy:
                self.assertIs(session.settlement(op, "id", idempotency_key="key", movement_id="movement"), spy.return_value)
                spy.assert_called_once_with(operation=op, settlement_id="id", idempotency_key="key", movement_id="movement")

    def test_source_fault_is_one_fetch_and_does_not_bind_or_replace_the_key(self):
        session = LocalFinanceSession(recordings={("s", "fault"): SyntheticStatementFault.TIMEOUT})
        before = session.settlement_machine.canonical_state()
        with self.assertRaises(StatementSourceError):
            session.settlement("commit", "s", idempotency_key="original", movement_id="fault")
        self.assertEqual(session.statement_source.calls, (("s", "fault"),))
        self.assertEqual(before, session.settlement_machine.canonical_state())
        # A source failure never reached the FSM, so this original key is still free.
        session.settlement("initiate", "s", idempotency_key="original", trade_id="trade", gross=100000,
                           debtor_role="synthetic", policy=load_fixture()["steps"][0]["body"]["policy"])
        self.assertEqual(len(session.settlement_machine.export_journal()), 1)

    def test_unsupported_and_bad_adapter_signature_do_not_fetch_or_dispatch(self):
        session = LocalFinanceSession(recordings={})
        for op in ("restore", "attempt_execution", "__init__", "DISBURSE", [], None):
            for call in (session.settlement, session.credit):
                with self.assertRaises(ValueError):
                    call(op, "id", idempotency_key="key")
        for body in ({}, {"movement_id": "m", "amount": 1}):
            with self.assertRaises(TypeError):
                session.settlement("commit", "id", idempotency_key="key", **body)
        self.assertEqual(session.statement_source.calls, ())
        self.assertEqual(session.settlement_machine.export_journal(), [])
        self.assertEqual(session.credit_machine.export_journal(), [])


if __name__ == "__main__":
    unittest.main()
