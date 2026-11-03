"""Builder-authored differential and boundary evidence; no policy or authority."""

from copy import deepcopy
import json
import unittest
from unittest.mock import Mock

from credit_fsm import CreditError, CreditMachine
from example_settlement_claim_adapter import run_example
from fake_settlement_claim_source import FakeSettlementClaimSource, SyntheticSettlementClaimFault
from mock_credit import open_terms
from settlement_claim_adapter import SettlementClaimAdapter
from settlement_claim_source import (
    InvalidSettlementClaimRecord, LocalSettlementClaimSource,
    SettlementClaimIdentityMismatch, SettlementClaimNotFound, SettlementClaimSourceError,
)
from test_credit_fsm import assert_not_lending, policy, settlement_book
from settlement_fsm import SettlementError

SID = "claim-1"


def observables(machine):
    return machine.canonical_state(), machine.state_digest(), machine.export_journal()


def request(**changes):
    body = dict(settlement_id=SID, advance_id="advance", idempotency_key="offer",
                amount=40_000, beneficiary_role="fixture-beneficiary")
    body.update(changes)
    return body


class SettlementClaimAdapterTests(unittest.TestCase):
    def assert_receipt(self, receipt):
        assert_not_lending(self, receipt)
        self.assertEqual(receipt["credit"]["open_terms"], open_terms())

    def parity(self, adapted, direct, document, *, code=None, **changes):
        source = Mock()
        source.fetch.return_value = document
        body = request(**changes)
        direct_body = {k: v for k, v in body.items() if k != "settlement_id"}
        advance = direct_body.pop("advance_id")
        calls = (
            lambda: SettlementClaimAdapter(adapted, source).offer(**body),
            lambda: direct.offer(advance, face=deepcopy(document["claim"]), **direct_body),
        )
        if code is None:
            receipt, control = (invoke() for invoke in calls)
            self.assertEqual(receipt, control)
            self.assert_receipt(receipt)
        else:
            for invoke in calls:
                with self.assertRaises(CreditError) as caught:
                    invoke()
                self.assertEqual(caught.exception.code, code)
            receipt = None
        source.fetch.assert_called_once_with(body["settlement_id"])
        self.assertEqual(observables(adapted), observables(direct))
        return receipt

    def test_one_read_one_offer_detached_forwarding_and_exact_result_or_exception(self):
        book, _ = settlement_book("COMMITTED")
        document = book.view(SID)
        document["claim"]["caller_metadata"] = {"nested": [1, True, None]}
        document["extra_view_field"] = "preserved source"
        original = deepcopy(document)
        for fails in (False, True):
            with self.subTest(fails=fails):
                source, credit = Mock(), Mock(spec_set=CreditMachine)
                source.fetch.return_value = document
                receipt = {"fixture": [1]}
                error = CreditError("fixture-error")

                def offer(*args, **kwargs):
                    self.assertEqual(args, ("advance",))
                    face = kwargs.pop("face")
                    self.assertEqual(kwargs, dict(idempotency_key="offer", amount=40_000,
                                                  beneficiary_role="fixture-beneficiary"))
                    self.assertEqual(face, document["claim"])
                    self.assertIsNot(face, document["claim"])
                    face["caller_metadata"]["nested"].append("changed by callee")
                    if fails:
                        raise error
                    return receipt

                credit.offer.side_effect = offer
                adapter = SettlementClaimAdapter(credit, source)
                if fails:
                    with self.assertRaises(CreditError) as caught:
                        adapter.offer(**request())
                    self.assertIs(caught.exception, error)
                else:
                    self.assertIs(adapter.offer(**request()), receipt)
                source.fetch.assert_called_once_with(SID)
                self.assertEqual(len(credit.mock_calls), 1)
                self.assertEqual(document, original)

    def test_missing_identity_envelope_and_fault_failures_never_offer_or_bind_key(self):
        book, _ = settlement_book("COMMITTED")
        valid = book.view(SID)
        cases = [(None, SettlementClaimNotFound), ([], InvalidSettlementClaimRecord),
                 ({"settlement": valid}, InvalidSettlementClaimRecord)]
        for field in valid:
            if field in ("settlement_id", "provenance", "lifecycle_authority", "claim",
                         "provider_authorization_executed", "legal_debtor_bound", "admission_granted",
                         "right_cancelled", "bank_debit_observed", "external_return_closed",
                         "funds_executed", "durable"):
                missing = deepcopy(valid)
                del missing[field]
                cases.append((missing, InvalidSettlementClaimRecord))
        for field in ("provider_authorization_executed", "legal_debtor_bound", "admission_granted",
                      "right_cancelled", "bank_debit_observed", "external_return_closed",
                      "funds_executed", "durable"):
            for value in (True, 0, None, "false"):
                cases.append((dict(valid, **{field: value}), InvalidSettlementClaimRecord))
        for field, value, error in (
            ("settlement_id", "other", SettlementClaimIdentityMismatch),
            ("settlement_id", 1, SettlementClaimIdentityMismatch),
            ("provenance", "REAL", InvalidSettlementClaimRecord),
            ("lifecycle_authority", "CHAIN", InvalidSettlementClaimRecord),
            ("claim", None, SettlementClaimNotFound),
            ("claim", [], InvalidSettlementClaimRecord),
            ("claim", {}, SettlementClaimIdentityMismatch),
            ("claim", dict(valid["claim"], claim_id="other"), SettlementClaimIdentityMismatch),
            ("claim", dict(valid["claim"], claim_id=1), SettlementClaimIdentityMismatch),
        ):
            cases.append((dict(valid, **{field: value}), error))
        for document, error in cases:
            with self.subTest(document=document):
                machine = CreditMachine()
                spy = Mock(wraps=machine, spec_set=CreditMachine)
                source = Mock()
                source.fetch.return_value = document
                before = observables(machine)
                with self.assertRaises(error):
                    SettlementClaimAdapter(spy, source).offer(**request())
                source.fetch.assert_called_once_with(SID)
                self.assertEqual(spy.mock_calls, [])
                self.assertEqual(observables(machine), before)
                # Different valid payload under the same key proves it stayed unbound.
                self.parity(machine, CreditMachine(), valid, amount=1)

        for fault in SyntheticSettlementClaimFault:
            source = FakeSettlementClaimSource(recordings={SID: fault})
            spy = Mock(spec_set=CreditMachine)
            with self.assertRaises(SettlementClaimSourceError):
                SettlementClaimAdapter(spy, source).offer(**request())
            self.assertEqual(source.calls, (SID,))
            self.assertEqual(spy.mock_calls, [])
        fault = RuntimeError("fixture-source-fault")
        source = Mock()
        source.fetch.side_effect = fault
        spy = Mock(spec_set=CreditMachine)
        with self.assertRaises(RuntimeError) as caught:
            SettlementClaimAdapter(spy, source).offer(**request())
        self.assertIs(caught.exception, fault)
        source.fetch.assert_called_once_with(SID)
        self.assertEqual(spy.mock_calls, [])

    def test_local_unknown_and_preclaim_phases_never_offer(self):
        for phase in ("INITIATED", "FAILED"):
            book, _ = settlement_book(phase)
            spy = Mock(spec_set=CreditMachine)
            with self.assertRaises(SettlementClaimNotFound):
                SettlementClaimAdapter(spy, LocalSettlementClaimSource(book)).offer(**request())
            self.assertEqual(spy.mock_calls, [])
        with self.assertRaises(SettlementError) as caught:
            SettlementClaimAdapter(spy, LocalSettlementClaimSource(book)).offer(
                **request(settlement_id="missing"))
        self.assertEqual(caught.exception.code, "UNKNOWN_SETTLEMENT")
        self.assertEqual(spy.mock_calls, [])

    def test_credit_validation_and_rejection_replay_match_direct_offer(self):
        book, _ = settlement_book("COMMITTED")
        valid = book.view(SID)
        variants = [({}, dict(amount=True), "INVALID_AMOUNT"),
                    ({}, dict(advance_id=" spaced"), "INVALID_ID"),
                    ({}, dict(beneficiary_role=""), "INVALID_ID"),
                    ({}, dict(idempotency_key=""), "INVALID_ID"),
                    ({"provenance": "other"}, {}, "SETTLEMENT_FACE_NOT_MOCK"),
                    ({"currency": "USD"}, {}, "CURRENCY_UNSUPPORTED"),
                    ({"gross": "100000"}, {}, "SETTLEMENT_FACE_MISMATCH"),
                    ({"funds_executed": True}, {}, "SETTLEMENT_FACE_NOT_MOCK")]
        for face_changes, changes, code in variants:
            with self.subTest(code=code, changes=changes):
                adapted, direct = CreditMachine(), CreditMachine()
                document = deepcopy(valid)
                document["claim"].update(face_changes)
                self.parity(adapted, direct, document, code=code, **changes)
                self.parity(adapted, direct, document, code=code, **changes)
                # The FSM owns whether this rejection binds the caller key.
                expected = "IDEMPOTENCY_CONFLICT" if changes.get("idempotency_key") != "" else None
                self.parity(adapted, direct, valid, code=expected, amount=1)

        book.bind_refund(SID, idempotency_key="refund", refund_id="refund",
                         amount=1, beneficiary_role="buyer", reason="fixture")
        self.parity(CreditMachine(), CreditMachine(), book.view(SID), code="REFUND_OBLIGATION_OPEN")

    def test_replay_after_transitions_and_changed_snapshot_conflicts_do_not_refresh(self):
        book, _ = settlement_book("CAPTURED")
        adapted, direct = CreditMachine(book), CreditMachine(book)
        source = Mock(wraps=LocalSettlementClaimSource(book))
        adapter = SettlementClaimAdapter(adapted, source)
        original = book.view(SID)
        offered = adapter.offer(**request())
        control = direct.offer("advance", idempotency_key="offer", face=original["claim"],
                               amount=40_000, beneficiary_role="fixture-beneficiary")
        self.assertEqual(offered, control)
        for machine in (adapted, direct):
            machine.approve("advance", idempotency_key="approve")
            machine.draw("advance", idempotency_key="draw", draw_id="draw")
        replay = adapter.offer(**request())
        expected = deepcopy(offered)
        expected.update(duplicate=True, applied=None)
        self.assertEqual(replay, expected)
        self.assert_receipt(replay)
        self.assertEqual(replay, direct.offer("advance", idempotency_key="offer", face=original["claim"],
                                             amount=40_000, beneficiary_role="fixture-beneficiary"))
        self.assertEqual(source.fetch.call_count, 2)
        frozen = adapted.view_claim(SID)
        book.commit(SID, idempotency_key="commit", movement_id="move", gross=100_000,
                    amount=90_000, fee=10_000, tax=0, held=0, adjustment=0)
        for key, code in (("offer", "IDEMPOTENCY_CONFLICT"), ("new", "ADVANCE_BINDING_CONFLICT")):
            with self.assertRaises(CreditError) as caught:
                adapter.offer(**request(idempotency_key=key))
            self.assertEqual(caught.exception.code, code)
            with self.assertRaises(CreditError) as control_error:
                direct.offer("advance", idempotency_key=key, face=book.view(SID)["claim"],
                             amount=40_000, beneficiary_role="fixture-beneficiary")
            self.assertEqual(control_error.exception.code, code)
        self.assertEqual(source.fetch.call_count, 4)
        self.assertEqual(adapted.view_claim(SID), frozen)
        self.assertEqual(observables(adapted), observables(direct))
        # Original snapshot still replays first OFFERED receipt after the conflicts.
        self.parity(adapted, direct, original)

    def test_explicit_bound_draw_retains_committed_gate_and_original_face(self):
        book, _ = settlement_book("CAPTURED")
        machine = CreditMachine(book)
        before = book.canonical_state()
        offered = SettlementClaimAdapter(machine, LocalSettlementClaimSource(book)).offer(**request())
        self.assertEqual(offered["credit"]["phase"], "OFFERED")
        self.assertEqual(offered["credit"]["drawn_exposure"], 0)
        self.assertEqual(offered["credit"]["settlement_gate"], "UNBOUND")
        self.assertEqual([e["op"] for e in machine.export_journal()], ["offer"])
        machine.bind_settlement("advance", idempotency_key="bind", settlement_id=SID)
        machine.approve("advance", idempotency_key="approve")
        for _ in range(2):
            with self.assertRaises(CreditError) as caught:
                machine.draw("advance", idempotency_key="early", draw_id="draw")
            self.assertEqual(caught.exception.code, "SETTLEMENT_NOT_COMMITTED")
        self.assertEqual(book.canonical_state(), before)
        book.commit(SID, idempotency_key="commit", movement_id="move", gross=100_000,
                    amount=90_000, fee=10_000, tax=0, held=0, adjustment=0)
        with self.assertRaises(CreditError) as caught:
            machine.draw("advance", idempotency_key="early", draw_id="draw")
        self.assertEqual(caught.exception.code, "SETTLEMENT_NOT_COMMITTED")
        committed = book.canonical_state()
        drawn = machine.draw("advance", idempotency_key="later", draw_id="draw")
        self.assert_receipt(drawn)
        self.assertEqual(drawn["credit"]["settlement_gate"], "MOCK_COMMIT_OBSERVED")
        self.assertEqual(drawn["credit"]["confirmed_cash_on_face"], 0)
        self.assertEqual(book.canonical_state(), committed)

    def test_shared_capacity_and_changed_face_are_still_draw_time_checks(self):
        book, _ = settlement_book("COMMITTED")
        adapted, direct = CreditMachine(book), CreditMachine(book)
        document = book.view(SID)
        for aid, amount in (("first", 60_000), ("second", 40_001)):
            result = self.parity(adapted, direct, document, advance_id=aid,
                                 idempotency_key="offer-" + aid, amount=amount)
            self.assertEqual(result["credit"]["drawn_exposure"], 0)
            for machine in (adapted, direct):
                machine.approve(aid, idempotency_key="approve-" + aid)
        for machine in (adapted, direct):
            self.assert_receipt(machine.draw("first", idempotency_key="draw-first", draw_id="first"))
            with self.assertRaises(CreditError) as caught:
                machine.draw("second", idempotency_key="draw-second", draw_id="second")
            self.assertEqual(caught.exception.code, "ADVANCE_EXCEEDS_OPEN_FACE")
        frozen = adapted.view_claim(SID)
        book.distribute(SID, idempotency_key="later-distribution", order=["platform", "organizer"])
        # Retain extra caller data in the forwarded changed face as well.
        changed = book.view(SID)
        changed["claim"]["caller_mark"] = {"nested": ["later"]}
        self.parity(adapted, direct, changed, advance_id="third", idempotency_key="third", amount=1)
        for machine in (adapted, direct):
            machine.approve("third", idempotency_key="approve-third")
            with self.assertRaises(CreditError) as caught:
                machine.draw("third", idempotency_key="draw-third", draw_id="third")
            self.assertEqual(caught.exception.code, "FACE_SNAPSHOT_FROZEN")
        self.assertEqual(adapted.view_claim(SID), frozen)
        self.assertEqual(observables(adapted), observables(direct))


class SettlementClaimExampleTests(unittest.TestCase):
    def test_statement_backed_offer_and_separate_explicit_draw(self):
        result = run_example(policy=policy(), amount=40_000, beneficiary_role="fixture-beneficiary")
        self.assertEqual(result["offered"]["credit"]["phase"], "OFFERED")
        self.assertEqual(result["offered"]["credit"]["drawn_exposure"], 0)
        self.assertEqual(result["offered"]["credit"]["confirmed_cash_on_face"], 93_000)
        self.assertEqual(result["drawn"]["credit"]["phase"], "DRAWN")
        self.assertEqual(result["drawn"]["credit"]["settlement_gate"], "MOCK_COMMIT_OBSERVED")
        self.assertEqual([e["op"] for e in result["credit_journal"]],
                         ["offer", "bind_settlement", "approve", "draw"])
        self.assertEqual(result["statement_calls"], (("fixture-settlement", "fixture-movement"),))
        self.assertEqual(result["settlement"]["claim"]["distributed_cash"], 0)
        for key in ("offered", "bound", "approved", "drawn"):
            assert_not_lending(self, result[key])
            self.assertEqual(result[key]["credit"]["open_terms"], open_terms())
        json.dumps(result, allow_nan=False)
        for missing in ("policy", "amount", "beneficiary_role"):
            kwargs = dict(policy=policy(), amount=1, beneficiary_role="fixture")
            del kwargs[missing]
            with self.assertRaises(TypeError):
                run_example(**kwargs)
