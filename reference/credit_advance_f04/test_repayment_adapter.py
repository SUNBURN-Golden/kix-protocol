"""Source-informed boundary evidence over actual, unchanged local FSMs."""

from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch

from credit_fsm import CreditError, CreditMachine
from credit_property_support import check_terms
from example_repayment_adapter import run_example
from fake_repayment_source import FakeRepaymentSource, SyntheticRepaymentFault
from repayment_adapter import RepaymentAdapter
from repayment_source import (
    InvalidRepaymentRecord, RepaymentIdentityMismatch, RepaymentNotFound, RepaymentSourceError,
)
from test_credit_fsm import assert_not_lending, policy, settlement_book


AID, RID = "fixture-advance", "fixture-note"


def record(**changes):
    document = dict(advance_id=AID, repay_id=RID, sequence=1, amount=30_000)
    document.update(changes)
    return document


def prepared(phase="DRAWN"):
    settlement, face = settlement_book("COMMITTED")
    machine = CreditMachine(settlement)
    if phase == "ABSENT":
        return machine, settlement
    machine.offer(AID, idempotency_key="offer", face=face, amount=80_000,
                  beneficiary_role="fixture-beneficiary")
    if phase == "OFFERED":
        return machine, settlement
    machine.approve(AID, idempotency_key="approve")
    machine.bind_settlement(AID, idempotency_key="bind", settlement_id="claim-1")
    if phase == "APPROVED":
        return machine, settlement
    machine.draw(AID, idempotency_key="draw", draw_id="fixture-draw")
    if phase == "DEFAULTED":
        machine.default(AID, idempotency_key="default", reason="fixture-default")
    if phase == "CLOSED":
        machine.repay(AID, idempotency_key="seed", repay_id="seed", sequence=1, amount=80_000)
        machine.close(AID, idempotency_key="close")
    return machine, settlement


def observables(machine):
    return machine.canonical_state(), machine.state_digest(), machine.export_journal()


def apply(machine, document, key="caller-key"):
    source = FakeRepaymentSource(recordings={
        (document["advance_id"], document["repay_id"]): json.dumps(document),
    })
    return RepaymentAdapter(machine, source).apply(
        advance_id=document["advance_id"], repay_id=document["repay_id"], idempotency_key=key,
    )


def direct(machine, document, key="caller-key"):
    return machine.repay(document["advance_id"], idempotency_key=key,
                         repay_id=document["repay_id"], sequence=document["sequence"],
                         amount=document["amount"])


class RepaymentAdapterTests(unittest.TestCase):
    def assert_parity(self, adapted, control, document, key, code=None):
        before = observables(adapted)
        if code is None:
            result = apply(adapted, document, key)
            self.assertEqual(result, direct(control, document, key))
            assert_not_lending(self, result)
            check_terms(result["credit"])
        else:
            for invoke in (lambda: apply(adapted, document, key),
                           lambda: direct(control, document, key)):
                with self.assertRaises(CreditError) as caught:
                    invoke()
                self.assertEqual(caught.exception.code, code)
            self.assertEqual(observables(adapted), before)
            result = None
        self.assertEqual(observables(adapted), observables(control))
        return result

    def test_one_fetch_exact_forwarding_and_same_response_or_error_object(self):
        for changes, code in (({}, None), ({"amount": True}, "INVALID_AMOUNT"),
                              ({"sequence": [1]}, "REPAYMENT_ORDER")):
            with self.subTest(changes=changes):
                machine, _ = prepared()
                document = record(**changes)
                original = deepcopy(document)
                source, spy = Mock(), Mock(wraps=machine, spec_set=CreditMachine)
                source.fetch.return_value = document
                retained = []

                def invoke(*args, **kwargs):
                    try:
                        result = machine.repay(*args, **kwargs)
                    except CreditError as error:
                        retained.append(error)
                        raise
                    retained.append(result)
                    return result

                spy.repay.side_effect = invoke
                adapter = RepaymentAdapter(spy, source)
                caller_key = "caller-key-unchanged"
                if code:
                    with self.assertRaises(CreditError) as caught:
                        adapter.apply(advance_id=AID, repay_id=RID, idempotency_key=caller_key)
                    self.assertIs(caught.exception, retained[0])
                    self.assertEqual(caught.exception.code, code)
                else:
                    result = adapter.apply(advance_id=AID, repay_id=RID, idempotency_key=caller_key)
                    self.assertIs(result, retained[0])
                    assert_not_lending(self, result)
                source.fetch.assert_called_once_with(AID, RID)
                spy.repay.assert_called_once_with(
                    AID, idempotency_key=caller_key, repay_id=RID,
                    sequence=document["sequence"], amount=document["amount"],
                )
                self.assertIs(spy.repay.call_args.args[0], AID)
                self.assertIs(spy.repay.call_args.kwargs["idempotency_key"], caller_key)
                for field in ("repay_id", "sequence", "amount"):
                    self.assertIs(spy.repay.call_args.kwargs[field], document[field])
                self.assertEqual(len(spy.mock_calls), 1)
                self.assertEqual(document, original)

    def test_local_failures_make_zero_fsm_calls_and_leave_key_available(self):
        missing_field = record()
        missing_field.pop("sequence")
        cases = [
            (None, RepaymentNotFound),
            (SyntheticRepaymentFault.ERROR, RepaymentSourceError),
            (SyntheticRepaymentFault.TIMEOUT, RepaymentSourceError),
            ("{", InvalidRepaymentRecord),
            ("null", InvalidRepaymentRecord),
            ("[]", InvalidRepaymentRecord),
            (json.dumps(missing_field), InvalidRepaymentRecord),
            (json.dumps(record(extra=1)), InvalidRepaymentRecord),
            (json.dumps(record(advance_id="other")), RepaymentIdentityMismatch),
            (json.dumps(record(repay_id="other")), RepaymentIdentityMismatch),
            (json.dumps(record(advance_id=1)), RepaymentIdentityMismatch),
            (json.dumps(record(repay_id=None)), RepaymentIdentityMismatch),
        ]
        for recording, error in cases:
            with self.subTest(recording=recording):
                machine, settlement = prepared()
                before, settlement_before = observables(machine), observables(settlement)
                spy = Mock(wraps=machine, spec_set=CreditMachine)
                source = FakeRepaymentSource(recordings={}
                                             if recording is None else {(AID, RID): recording})
                with self.assertRaises(error):
                    RepaymentAdapter(spy, source).apply(
                        advance_id=AID, repay_id=RID, idempotency_key="still-free")
                self.assertEqual(source.calls, ((AID, RID),))
                self.assertEqual(spy.mock_calls, [])
                self.assertEqual(observables(machine), before)
                result = apply(machine, record(), "still-free")
                self.assertFalse(result["duplicate"])
                self.assertEqual(result["credit"]["outstanding_exposure"], 50_000)
                self.assertEqual(observables(settlement), settlement_before)

    def test_custom_source_shape_and_fault_do_not_retry_or_call_fsm(self):
        class DictSubclass(dict):
            pass

        class StrSubclass(str):
            pass

        for value, error_type in (
            ([], InvalidRepaymentRecord), ("text", InvalidRepaymentRecord),
            (42, InvalidRepaymentRecord), ({}, InvalidRepaymentRecord),
            (DictSubclass(record()), InvalidRepaymentRecord),
            (record(advance_id=StrSubclass(AID)), RepaymentIdentityMismatch),
            (record(repay_id=StrSubclass(RID)), RepaymentIdentityMismatch),
        ):
            with self.subTest(value=value):
                source, machine = Mock(), Mock(spec_set=CreditMachine)
                source.fetch.return_value = value
                with self.assertRaises(error_type):
                    RepaymentAdapter(machine, source).apply(
                        advance_id=AID, repay_id=RID, idempotency_key="key")
                source.fetch.assert_called_once_with(AID, RID)
                self.assertEqual(machine.mock_calls, [])
        source, machine = Mock(), Mock(spec_set=CreditMachine)
        error = RepaymentSourceError("fixture failure")
        source.fetch.side_effect = error
        with self.assertRaises(RepaymentSourceError) as caught:
            RepaymentAdapter(machine, source).apply(
                advance_id=AID, repay_id=RID, idempotency_key="key")
        self.assertIs(caught.exception, error)
        source.fetch.assert_called_once_with(AID, RID)
        self.assertEqual(machine.mock_calls, [])

    def test_duplicate_invocations_each_fetch_once_without_second_effect(self):
        machine, settlement = prepared()
        before = observables(settlement)
        source = FakeRepaymentSource(recordings={(AID, RID): json.dumps(record())})
        spy = Mock(wraps=machine, spec_set=CreditMachine)
        adapter = RepaymentAdapter(spy, source)
        first = adapter.apply(advance_id=AID, repay_id=RID, idempotency_key="key")
        accepted = observables(machine)
        for key in ("key", "new-key"):
            result = adapter.apply(advance_id=AID, repay_id=RID, idempotency_key=key)
            self.assertTrue(result["duplicate"])
            self.assertIsNone(result["applied"])
            self.assertEqual(result["credit"], first["credit"])
            assert_not_lending(self, result)
            check_terms(result["credit"])
            self.assertEqual(observables(machine), accepted)
        self.assertEqual(source.calls, ((AID, RID),) * 3)
        self.assertEqual(spy.repay.call_count, 3)
        self.assertEqual(len(spy.mock_calls), 3)
        self.assertEqual(observables(settlement), before)

    def test_partial_duplicate_and_changed_binding_match_direct_histories(self):
        adapted, settlement = prepared()
        control, _ = prepared()
        before = observables(settlement)
        first = self.assert_parity(adapted, control, record(), "first")
        self.assertEqual(first["credit"]["outstanding_exposure"], 50_000)
        self.assert_parity(adapted, control, record(), "first")
        self.assert_parity(adapted, control, record(), "duplicate-note")
        for changed, conflict_key in ((record(amount=29_999), "amount-conflict"),
                                      (record(sequence=2), "sequence-conflict")):
            self.assert_parity(adapted, control, changed, "first", "IDEMPOTENCY_CONFLICT")
            self.assert_parity(adapted, control, changed, conflict_key, "REPAY_BINDING_CONFLICT")
            self.assert_parity(adapted, control, changed, conflict_key, "REPAY_BINDING_CONFLICT")
            self.assert_parity(adapted, control, record(), conflict_key, "IDEMPOTENCY_CONFLICT")
        self.assert_parity(adapted, control, record(repay_id="next", sequence=2, amount=20_000),
                           "next")
        self.assertEqual(adapted.view(AID)["reserved_open"], 80_000)
        self.assertEqual(observables(settlement), before)

    def test_sequence_gap_stays_rejected_after_gap_filled_then_fresh_key_succeeds(self):
        adapted, _ = prepared()
        control, _ = prepared()
        gap = record(repay_id="next", sequence=2, amount=20_000)
        self.assert_parity(adapted, control, gap, "gap", "REPAYMENT_ORDER")
        self.assert_parity(adapted, control, record(), "first")
        self.assert_parity(adapted, control, gap, "gap", "REPAYMENT_ORDER")
        self.assert_parity(adapted, control, record(), "gap", "IDEMPOTENCY_CONFLICT")
        self.assert_parity(adapted, control, gap, "fresh")

    def test_excess_and_invalid_numeric_values_use_fsm_errors_and_retained_keys(self):
        cases = [(record(amount=80_001), "REPAYMENT_EXCEEDS_OUTSTANDING")]
        cases += [(record(amount=value), "INVALID_AMOUNT")
                  for value in (True, 0, -1, "30000", 1.5, None, [], {})]
        cases += [(record(sequence=value), "REPAYMENT_ORDER")
                  for value in (True, 0, -1, "1", 1.5, None, [], {})]
        for document, code in cases:
            with self.subTest(document=document):
                adapted, _ = prepared()
                control, _ = prepared()
                self.assert_parity(adapted, control, document, "rejected", code)
                self.assert_parity(adapted, control, document, "rejected", code)
                self.assert_parity(adapted, control, record(), "rejected", "IDEMPOTENCY_CONFLICT")
                self.assert_parity(adapted, control, record(), "fresh")

    def test_phase_and_identity_rejections_match_direct_fsm(self):
        for phase, code in (("ABSENT", "UNKNOWN_ADVANCE"), ("OFFERED", "ILLEGAL_TRANSITION"),
                            ("APPROVED", "ILLEGAL_TRANSITION"),
                            ("DEFAULTED", "TERMINAL_IMMUTABLE"),
                            ("CLOSED", "TERMINAL_IMMUTABLE")):
            with self.subTest(phase=phase):
                adapted, _ = prepared(phase)
                control, _ = prepared(phase)
                self.assert_parity(adapted, control, record(), "rejected", code)
        for document, key in ((record(advance_id=""), "key"),
                              (record(repay_id=""), "key"), (record(), "")):
            adapted, _ = prepared()
            control, _ = prepared()
            self.assert_parity(adapted, control, document, key, "INVALID_ID")

    def test_result_isolation_historical_replay_and_restore_without_source_fetch(self):
        machine, settlement = prepared()
        source = FakeRepaymentSource(recordings={(AID, RID): json.dumps(record())})
        adapter = RepaymentAdapter(machine, source)
        first = adapter.apply(advance_id=AID, repay_id=RID, idempotency_key="first")
        retained = deepcopy(first)
        expected = deepcopy(first)
        first["credit"]["repayments"][0]["amount"] = -1
        first["credit"]["open_terms"].clear()
        first["effect"]["amount"] = -1
        first["funds_executed"] = True
        apply(machine, record(repay_id="last", sequence=2, amount=50_000), "last")
        machine.close(AID, idempotency_key="close")
        before = observables(machine)
        expected.update(duplicate=True, applied=None)
        replay = adapter.apply(advance_id=AID, repay_id=RID, idempotency_key="first")
        self.assertEqual(replay, expected)
        replay["credit"]["repayments"].clear()
        replay["credit"]["repayment_observed"] = True
        self.assertEqual(adapter.apply(advance_id=AID, repay_id=RID, idempotency_key="first"),
                         expected)
        self.assertEqual(retained["credit"]["phase"], "DRAWN")
        self.assertEqual(retained["credit"]["outstanding_exposure"], 50_000)
        self.assertEqual(observables(machine), before)
        calls = source.calls
        restored = CreditMachine.restore(machine.export_journal(), settlement_source=settlement)
        self.assertEqual(observables(restored), before)
        self.assertEqual(source.calls, calls)
        replay = RepaymentAdapter(restored, source).apply(
            advance_id=AID, repay_id=RID, idempotency_key="first")
        self.assertEqual(replay, expected)
        assert_not_lending(self, replay)
        check_terms(replay["credit"])
        assert_not_lending(self, restored.view(AID))
        check_terms(restored.view(AID))

    def test_example_exposure_reservation_and_separately_requested_close_without_sockets(self):
        with patch("socket.socket", side_effect=AssertionError("sockets forbidden")):
            example = run_example(policy=policy())
        stages = [example["drawn"], *example["repayments"]]
        self.assertEqual([stage["credit"]["outstanding_exposure"] for stage in stages],
                         [80_000, 50_000, 30_000, 0])
        for stage in [example["offered"], example["approved"], example["bound"],
                      *stages, example["closed"]]:
            assert_not_lending(self, stage)
            check_terms(stage["credit"])
        for stage in stages:
            self.assertEqual(stage["credit"]["phase"], "DRAWN")
            self.assertEqual(stage["credit"]["reserved_open"], 80_000)
            self.assertEqual(stage["credit"]["note_status"], "NOTED")
            self.assertTrue(stage["credit"]["mock_settlement_commit_observed"])
        self.assertEqual(example["before_close"], example["repayments"][-1]["credit"])
        closed = example["closed"]["credit"]
        self.assertEqual((closed["phase"], closed["note_status"], closed["reserved_open"]),
                         ("CLOSED", "RELEASED", 0))
        self.assertEqual(example["settlement_before"], example["settlement_after"])
        self.assertEqual(example["settlement_journal_before"], example["settlement_journal"])
        for receipt in example["settlement_receipts"]:
            self.assertEqual(receipt["provenance"], "MOCK_SETTLEMENT_ONLY")
            self.assertIs(receipt["funds_executed"], False)
        self.assertEqual([entry["op"] for entry in example["credit_journal"]],
                         ["offer", "approve", "bind_settlement", "draw", "repay", "repay",
                          "repay", "close"])
        self.assertEqual(example["repayment_source_calls"], tuple(
            ("fixture-advance", f"fixture-note-{index}") for index in (1, 2, 3)))
        self.assertEqual(example["statement_source_calls"],
                         (("fixture-settlement", "fixture-statement"),))
