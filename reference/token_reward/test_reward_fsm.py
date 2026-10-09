"""Scenario checks for the reward state machine.

Fixture numbers, caps, ceilings, and digests are not policy values.
TK-7 and TK-8 are exercised here. They are not independently verified.

This suite runs in the protocol workflow's offline reference loop
(.github/workflows/protocol.yml). A passing run is not an independent
verification.
"""

import inspect
import json
import sys
import unittest
from pathlib import Path

from reward_fsm import (
    CLAWBACK_CLAIM,
    ELIGIBLE,
    HELD,
    ISSUED,
    ISSUING,
    OBSERVED,
    REVERSED,
    UNKNOWN,
    RewardMachine,
)
from token_reward_model import (
    ALWAYS_FALSE_FLAGS,
    LIFECYCLE,
    POOLS,
    PROVENANCE,
    UNIT,
    TokenRewardError,
    net_residual_revenue,
    reward_budget,
    reward_id,
)

DIGEST = "ab" * 32
DIGEST_B = "cd" * 32
EFFECTS = "ef" * 32

# Synthetic pool balances and point amounts. Not policy values.
AMOUNT = 4


def codes(fn):
    try:
        fn()
    except TokenRewardError as error:
        return error.code
    raise AssertionError("expected TokenRewardError")


def opening(**overrides):
    base = {pool: 7 for pool in POOLS}
    base["PROTOCOL_REVENUE"] = 50
    base["TOKEN_TREASURY_REWARD"] = 50
    base.update(overrides)
    return base


def committed_view():
    return {
        "phase": "COMMITTED",
        "currency": "KRW",
        "funds_executed": False,
        "bank_debit_observed": False,
        "legal_debtor_bound": False,
        "external_return_closed": False,
        "durable": False,
    }


def reward_key(source_op_id="op-1", recipient="recipient-1", program="program-1", kind="participation"):
    return {
        "program": program,
        "source_op_id": source_op_id,
        "recipient": recipient,
        "kind": kind,
    }


def human_approval(record_id="approval-1", generation=1):
    """Structural fixture. generation is not a quorum or a timelock."""

    return {
        "record_id": record_id,
        "generation": generation,
        "authority_id": "authority-slot",
        "actor_type": "HUMAN",
        "action": "point-payout",
        "scope_ref": "program-1",
        "evidence_refs": ["evidence-1"],
    }


def assert_false_flags(test, view):
    for name in ALWAYS_FALSE_FLAGS:
        test.assertIs(view[name], False)
    test.assertEqual(view["provenance"], PROVENANCE)
    test.assertEqual(view["lifecycle"], LIFECYCLE)
    test.assertEqual(view["unit"], UNIT)
    test.assertIs(view["non_transferable_until_chargeback_end"], True)
    test.assertNotIn("chargeback_window", view)
    test.assertNotIn("hold_length", view)


class RewardFsmTests(unittest.TestCase):
    def setUp(self):
        self.opening = opening()
        self.machine = RewardMachine(self.opening)
        self.key = reward_key()
        self.view = committed_view()

    def unchanged(self, fn, code):
        before = self.machine.canonical_state()
        journal = self.machine.export_journal()
        self.assertEqual(codes(fn), code)
        self.assertEqual(self.machine.canonical_state(), before)
        self.assertEqual(self.machine.export_journal(), journal)

    def observe(self, machine=None, key=None, **changes):
        machine = self.machine if machine is None else machine
        body = dict(
            reward_key=self.key if key is None else key,
            idempotency_key="obs-1",
            source_view=self.view,
            rule_version="rule-v1",
            amount=AMOUNT,
            source_kind="SETTLEMENT",
        )
        body.update(changes)
        reward_key_value = body.pop("reward_key")
        idem = body.pop("idempotency_key")
        return machine.observe(reward_key_value, idempotency_key=idem, **body)

    def hold(self, reward):
        return self.machine.hold(reward, idempotency_key="hold-1")

    def eligible(self, reward, **changes):
        body = dict(
            idempotency_key="elig-1",
            window_closed=True,
            source_view=self.view,
            abuse_clear=True,
        )
        body.update(changes)
        idem = body.pop("idempotency_key")
        return self.machine.mark_eligible(reward, idempotency_key=idem, **body)

    def submit(self, reward, **changes):
        body = dict(
            idempotency_key="sub-1",
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
        )
        body.update(changes)
        idem = body.pop("idempotency_key")
        return self.machine.submit(reward, idempotency_key=idem, **body)

    def succeed(self, reward, **changes):
        body = dict(idempotency_key="fx-1", effects_digest=EFFECTS, outcome="SUCCESS")
        body.update(changes)
        idem = body.pop("idempotency_key")
        return self.machine.observe_transfer_effects(reward, idempotency_key=idem, **body)

    def advance(self, target):
        opened = self.observe()
        reward = opened["reward"]["reward_id"]
        if target == OBSERVED:
            return reward
        self.hold(reward)
        if target == HELD:
            return reward
        self.eligible(reward)
        if target == ELIGIBLE:
            return reward
        self.submit(reward)
        if target == ISSUING:
            return reward
        self.succeed(reward)
        if target == ISSUED:
            return reward
        raise AssertionError(target)

    def test_flags_and_points_stay_non_transferable_on_every_phase(self):
        reward = self.advance(ISSUED)
        view = self.machine.view(reward)
        assert_false_flags(self, view)
        self.assertEqual(view["phase"], ISSUED)
        self.assertIs(view["krw_paid"], False)
        self.assertIs(view["token_issued"], False)
        self.assertEqual(view["krw_phase"], "KRW_UNPAID")
        self.assertIsNone(inspect.signature(RewardMachine.observe).parameters.get("now"))
        self.assertNotIn("timestamp", inspect.signature(RewardMachine.observe_source_cancel).parameters)

    def test_TL0_TK07_T1_one_payout_effect_under_retry_delay_and_reencoding(self):
        reward = self.advance(OBSERVED)
        again = self.observe()
        self.assertTrue(again["duplicate"])
        self.assertIsNone(again["applied"])
        self.assertEqual(len(self.machine.export_journal()), 1)
        for index in range(5):
            self.unchanged(
                lambda index=index: self.machine.observe(
                    self.key,
                    idempotency_key="obs-repeat-%s" % index,
                    source_view=self.view,
                    rule_version="rule-v1",
                    amount=AMOUNT,
                    source_kind="SETTLEMENT",
                ),
                "REWARD_ALREADY_OBSERVED",
            )
        self.unchanged(
            lambda: self.machine.observe(
                self.key,
                idempotency_key="obs-1",
                source_view=self.view,
                rule_version="rule-v1",
                amount=AMOUNT + 1,
                source_kind="SETTLEMENT",
            ),
            "IDEMPOTENCY_CONFLICT",
        )
        self.hold(reward)
        self.unchanged(
            lambda: self.machine.submit(
                reward,
                idempotency_key="sub-early",
                approval_ref=human_approval(),
                signed_bytes_digest=DIGEST,
                spend_pool="PROTOCOL_REVENUE",
            ),
            "ILLEGAL_TRANSITION",
        )
        self.eligible(reward)
        submitted = self.submit(reward)
        token_effect = submitted["reward"]["token_effect_id"]
        self.assertIsNotNone(token_effect)
        self.assertNotEqual(token_effect, submitted["reward"]["krw_effect_id"])
        self.unchanged(
            lambda: self.machine.submit(
                reward,
                idempotency_key="sub-other",
                approval_ref=human_approval("approval-other"),
                signed_bytes_digest=DIGEST_B,
                spend_pool="PROTOCOL_REVENUE",
            ),
            "ILLEGAL_TRANSITION",
        )
        paid = self.succeed(reward)
        self.assertEqual(paid["reward"]["payout_effect_count"], 1)
        self.assertEqual(paid["reward"]["phase"], ISSUED)
        self.assertFalse(paid["reward"]["payout_effects"][0]["supersession"])
        for index in range(5):
            self.unchanged(
                lambda index=index: self.machine.observe_transfer_effects(
                    reward,
                    idempotency_key="fx-repeat-%s" % index,
                    effects_digest=EFFECTS,
                    outcome="SUCCESS",
                ),
                "TERMINAL_IMMUTABLE",
            )
        self.assertEqual(self.machine.view(reward)["payout_effect_count"], 1)
        self.assertEqual(self.machine.view(reward)["token_effect_id"], token_effect)
        replayed = self.succeed(reward)
        self.assertTrue(replayed["duplicate"])
        self.assertEqual(len(self.machine.reward_ids()), 1)

    def test_rule_version_change_pays_once_unless_superseded(self):
        reward = self.advance(ISSUED)
        derived = reward_id(**self.key)
        self.assertEqual(reward, derived)
        self.unchanged(
            lambda: self.machine.observe(
                self.key,
                idempotency_key="obs-v2",
                source_view=self.view,
                rule_version="rule-v2",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            ),
            "RULE_VERSION_REPAY_FORBIDDEN",
        )
        self.assertEqual(self.machine.view(reward)["rule_version"], "rule-v1")
        self.assertEqual(self.machine.view(reward)["payout_effect_count"], 1)
        self.unchanged(
            lambda: self.machine.supersede(
                reward,
                idempotency_key="sup-ai",
                approval_ref={**human_approval("approval-ai"), "actor_type": "AI"},
                rule_version="rule-v2",
            ),
            "AI_APPROVAL_REJECTED",
        )
        superseded = self.machine.supersede(
            reward,
            idempotency_key="sup-1",
            approval_ref=human_approval("approval-2"),
            rule_version="rule-v2",
        )
        self.assertEqual(superseded["reward"]["rule_version"], "rule-v2")
        self.assertEqual(superseded["reward"]["phase"], ELIGIBLE)
        self.assertEqual(superseded["reward"]["payout_effect_count"], 1)
        self.assertEqual(len(self.machine.reward_ids()), 1)
        self.submit(reward, idempotency_key="sub-2", approval_ref=human_approval("approval-3"), signed_bytes_digest=DIGEST_B)
        second = self.succeed(reward, idempotency_key="fx-2", effects_digest=DIGEST_B)
        self.assertEqual(second["reward"]["payout_effect_count"], 2)
        self.assertTrue(second["reward"]["payout_effects"][1]["supersession"])
        self.assertFalse(second["reward"]["payout_effects"][0]["supersession"])
        self.assertEqual(second["reward"]["payout_effects"][0]["rule_version"], "rule-v1")
        self.assertEqual(second["reward"]["payout_effects"][1]["rule_version"], "rule-v2")

    def test_observe_under_a_new_rule_before_payout_does_not_create_a_second_id(self):
        reward = self.advance(OBSERVED)
        self.unchanged(
            lambda: self.machine.observe(
                self.key,
                idempotency_key="obs-v2",
                source_view=self.view,
                rule_version="rule-v2",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            ),
            "RULE_VERSION_REPAY_FORBIDDEN",
        )
        self.assertEqual(self.machine.reward_ids(), [reward])
        self.assertEqual(self.machine.view(reward)["payout_effect_count"], 0)

    def test_TL0_TK08_T1_token_and_krw_effects_stay_apart(self):
        reward = self.advance(ISSUED)
        issued = self.machine.view(reward)
        self.assertEqual(issued["phase"], ISSUED)
        self.assertEqual(issued["krw_phase"], "KRW_UNPAID")
        self.assertIs(issued["krw_paid"], False)
        self.assertNotEqual(issued["token_effect_id"], issued["krw_effect_id"])
        refunded = self.machine.observe_krw_refund(
            reward,
            idempotency_key="krw-1",
            source_view=self.view,
            reason="KRW_REFUND",
        )
        self.assertEqual(refunded["reward"]["phase"], ISSUED)
        self.assertEqual(refunded["reward"]["krw_phase"], "KRW_REFUND_NOTED")
        self.assertIs(refunded["reward"]["krw_paid"], False)
        self.assertEqual(refunded["effect"]["krw_effect_id"], issued["krw_effect_id"])
        self.assertNotEqual(refunded["effect"]["krw_effect_id"], issued["token_effect_id"])

    def test_token_failure_does_not_block_or_reverse_a_krw_refund(self):
        reward = self.advance(ISSUING)
        failed = self.machine.observe_transfer_effects(
            reward,
            idempotency_key="fx-fail",
            effects_digest=EFFECTS,
            outcome="FAILED",
        )
        self.assertEqual(failed["reward"]["phase"], ISSUING)
        self.assertEqual(failed["reward"]["token_outcome"], "FAILED")
        self.assertEqual(failed["reward"]["payout_effect_count"], 0)
        self.assertEqual(self.machine.pool_view()["balances"]["PROTOCOL_REVENUE"], 50)
        refunded = self.machine.observe_krw_refund(
            reward,
            idempotency_key="krw-fail",
            source_view=self.view,
            reason="KRW_REFUND",
        )
        self.assertEqual(refunded["reward"]["phase"], ISSUING)
        self.assertEqual(refunded["reward"]["token_outcome"], "FAILED")
        self.assertNotEqual(refunded["reward"]["phase"], REVERSED)
        self.assertEqual(refunded["reward"]["krw_phase"], "KRW_REFUND_NOTED")
        self.assertIs(refunded["krw_paid"], False)
        self.assertIs(refunded["funds_executed"], False)

    def test_krw_refund_does_not_reverse_the_token_until_source_cancel(self):
        reward = self.advance(HELD)
        refunded = self.machine.observe_krw_refund(
            reward,
            idempotency_key="krw-held",
            source_view=self.view,
            reason="KRW_REFUND",
        )
        self.assertEqual(refunded["reward"]["phase"], HELD)
        self.assertEqual(refunded["reward"]["krw_phase"], "KRW_REFUND_NOTED")
        cancelled = self.machine.observe_source_cancel(
            reward,
            idempotency_key="cancel-held",
            source_view=self.view,
            reason="SOURCE_CANCELLED",
        )
        self.assertEqual(cancelled["reward"]["phase"], REVERSED)
        self.assertEqual(cancelled["reward"]["krw_phase"], "KRW_REFUND_NOTED")

    def test_cancel_before_issuing_reverses_and_after_issued_is_clawback(self):
        early = RewardMachine(self.opening)
        opened = early.observe(
            self.key,
            idempotency_key="obs-early",
            source_view=self.view,
            rule_version="rule-v1",
            amount=AMOUNT,
            source_kind="RESALE",
        )
        reward = opened["reward"]["reward_id"]
        early.hold(reward, idempotency_key="hold-early")
        reversed_view = early.observe_source_cancel(
            reward,
            idempotency_key="cancel-early",
            source_view=self.view,
            reason="SOURCE_CANCELLED",
        )
        self.assertEqual(reversed_view["reward"]["phase"], REVERSED)
        self.assertFalse(reversed_view["reward"]["clawback_claim"])

        late = self.advance(ISSUED)
        clawback = self.machine.observe_source_cancel(
            late,
            idempotency_key="cancel-late",
            source_view=self.view,
            reason="LATE_REFUND",
        )
        self.assertEqual(clawback["reward"]["phase"], CLAWBACK_CLAIM)
        self.assertTrue(clawback["reward"]["clawback_claim"])
        self.assertEqual(clawback["reward"]["payout_effect_count"], 1)
        self.unchanged(
            lambda: self.machine.observe_source_cancel(
                late,
                idempotency_key="cancel-again",
                source_view=self.view,
                reason="LATE_REFUND",
            ),
            "TERMINAL_IMMUTABLE",
        )

    def test_unknown_creates_no_new_reward_and_resolves_only_on_the_same_digest(self):
        reward = self.advance(ISSUING)
        self.assertEqual(len(self.machine.reward_ids()), 1)
        unknown = self.machine.observe_transfer_effects(
            reward,
            idempotency_key="fx-unknown",
            effects_digest=EFFECTS,
            outcome="UNKNOWN",
        )
        self.assertEqual(unknown["reward"]["phase"], UNKNOWN)
        self.assertEqual(self.machine.reward_ids(), [reward])
        self.assertEqual(unknown["reward"]["payout_effect_count"], 0)
        self.unchanged(
            lambda: self.machine.reconcile_unknown(
                reward,
                idempotency_key="recon-bad",
                same_digest=DIGEST_B,
                resolution="SUCCESS",
            ),
            "DIGEST_MISMATCH",
        )
        self.unchanged(
            lambda: self.machine.submit(
                reward,
                idempotency_key="resend-no-permit",
                approval_ref=human_approval(),
                signed_bytes_digest=DIGEST,
                spend_pool="PROTOCOL_REVENUE",
            ),
            "RESEND_PERMIT_REQUIRED",
        )
        resent = self.machine.submit(
            reward,
            idempotency_key="resend-1",
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
            execution_permit={"fence_ref": "fence-slot", "signed_bytes_digest": DIGEST},
        )
        self.assertEqual(resent["reward"]["phase"], UNKNOWN)
        self.assertEqual(resent["reward"]["token_effect_id"], unknown["reward"]["token_effect_id"])
        self.assertEqual(resent["reward"]["payout_effect_count"], 0)
        self.assertEqual(resent["reward"]["resend_count"], 1)
        self.assertEqual(self.machine.reward_ids(), [reward])
        resolved = self.machine.reconcile_unknown(
            reward,
            idempotency_key="recon-1",
            same_digest=DIGEST,
            resolution="SUCCESS",
        )
        self.assertEqual(resolved["reward"]["phase"], ISSUED)
        self.assertEqual(resolved["reward"]["payout_effect_count"], 1)
        self.assertEqual(self.machine.reward_ids(), [reward])
        self.assertEqual(self.machine.pool_view()["balances"]["PROTOCOL_REVENUE"], 46)

    def test_issuing_cancel_is_clawback_and_unknown_cancel_is_clawback(self):
        issuing = self.advance(ISSUING)
        moved = self.machine.observe_source_cancel(
            issuing,
            idempotency_key="cancel-issuing",
            source_view=self.view,
            reason="SOURCE_CANCELLED",
        )
        self.assertEqual(moved["reward"]["phase"], CLAWBACK_CLAIM)
        other = RewardMachine(self.opening)
        opened = other.observe(
            reward_key(source_op_id="op-unknown"),
            idempotency_key="obs-u",
            source_view=self.view,
            rule_version="rule-v1",
            amount=AMOUNT,
            source_kind="RESERVATION",
        )
        reward = opened["reward"]["reward_id"]
        other.hold(reward, idempotency_key="hold-u")
        other.mark_eligible(
            reward,
            idempotency_key="elig-u",
            window_closed=True,
            source_view=self.view,
            abuse_clear=True,
        )
        other.submit(
            reward,
            idempotency_key="sub-u",
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="TOKEN_TREASURY_REWARD",
        )
        other.observe_transfer_effects(
            reward,
            idempotency_key="fx-u",
            effects_digest=EFFECTS,
            outcome="UNKNOWN",
        )
        clawback = other.observe_source_cancel(
            reward,
            idempotency_key="cancel-u",
            source_view=self.view,
            reason="SOURCE_CANCELLED",
        )
        self.assertEqual(clawback["reward"]["phase"], CLAWBACK_CLAIM)

    def test_abuse_blocks_eligibility_and_caps_pause(self):
        for kind in ("SELF_TRADE", "DUPLICATED_ACCOUNTS", "REFERRAL_FARMING"):
            machine = RewardMachine(self.opening)
            opened = machine.observe(
                reward_key(source_op_id="op-" + kind),
                idempotency_key="obs-" + kind,
                source_view=self.view,
                rule_version="rule-v1",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            )
            reward = opened["reward"]["reward_id"]
            machine.hold(reward, idempotency_key="hold-" + kind)
            before = machine.canonical_state()
            self.assertEqual(
                codes(
                    lambda machine=machine, reward=reward, kind=kind: machine.mark_eligible(
                        reward,
                        idempotency_key="elig-" + kind,
                        window_closed=True,
                        source_view=self.view,
                        abuse_clear=False,
                        abuse_kind=kind,
                    )
                ),
                "ABUSE_BLOCKED",
            )
            self.assertEqual(machine.view(reward)["phase"], HELD)
            self.assertEqual(machine.view(reward)["payout_effect_count"], 0)
            self.assertEqual(machine.pool_view()["balances"], opening())
            self.assertEqual(machine.canonical_state(), before)

        first = self.advance(ISSUED)
        self.assertEqual(self.machine.view(first)["recipient"], "recipient-1")
        second_key = reward_key(source_op_id="op-2")
        second = self.observe(key=second_key, idempotency_key="obs-2")["reward"]["reward_id"]
        self.machine.hold(second, idempotency_key="hold-2")
        self.unchanged(
            lambda: self.machine.mark_eligible(
                second,
                idempotency_key="elig-cap",
                window_closed=True,
                source_view=self.view,
                abuse_clear=True,
                recipient_cap=6,
            ),
            "CAP_EXHAUSTED_PAUSED",
        )
        self.assertEqual(self.machine.view(second)["phase"], HELD)
        program_machine = RewardMachine(self.opening)
        for index, recipient in enumerate(("recipient-a", "recipient-b")):
            opened = program_machine.observe(
                reward_key(source_op_id="op-p-%s" % index, recipient=recipient),
                idempotency_key="obs-p-%s" % index,
                source_view=self.view,
                rule_version="rule-v1",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            )
            reward = opened["reward"]["reward_id"]
            program_machine.hold(reward, idempotency_key="hold-p-%s" % index)
            if index == 0:
                program_machine.mark_eligible(
                    reward,
                    idempotency_key="elig-p-0",
                    window_closed=True,
                    source_view=self.view,
                    abuse_clear=True,
                    program_cap=6,
                )
                program_machine.submit(
                    reward,
                    idempotency_key="sub-p-0",
                    approval_ref=human_approval(),
                    signed_bytes_digest=DIGEST,
                    spend_pool="PROTOCOL_REVENUE",
                )
                program_machine.observe_transfer_effects(
                    reward,
                    idempotency_key="fx-p-0",
                    effects_digest=EFFECTS,
                    outcome="SUCCESS",
                )
            else:
                self.assertEqual(
                    codes(
                        lambda: program_machine.mark_eligible(
                            reward,
                            idempotency_key="elig-p-1",
                            window_closed=True,
                            source_view=self.view,
                            abuse_clear=True,
                            program_cap=6,
                        )
                    ),
                    "CAP_EXHAUSTED_PAUSED",
                )
                self.assertEqual(program_machine.view(reward)["phase"], HELD)

    def test_window_must_be_closed_before_eligibility(self):
        reward = self.advance(HELD)
        self.unchanged(
            lambda: self.machine.mark_eligible(
                reward,
                idempotency_key="elig-open",
                window_closed=False,
                source_view=self.view,
                abuse_clear=True,
            ),
            "WINDOW_OPEN",
        )
        self.assertEqual(self.machine.view(reward)["phase"], HELD)

    def test_ai_approval_is_rejected_and_external_execution_is_unsupported(self):
        reward = self.advance(ELIGIBLE)
        before = self.machine.state_digest()
        self.unchanged(
            lambda: self.machine.submit(
                reward,
                idempotency_key="sub-ai",
                approval_ref={**human_approval("approval-ai"), "actor_type": "AI"},
                signed_bytes_digest=DIGEST,
                spend_pool="PROTOCOL_REVENUE",
            ),
            "AI_APPROVAL_REJECTED",
        )
        self.assertEqual(self.machine.view(reward)["phase"], ELIGIBLE)
        self.assertIsNone(self.machine.view(reward)["approval_ref"])
        journal = self.machine.export_journal()
        self.assertEqual(codes(lambda: self.machine.reject_external("chain-submit")), "EXTERNAL_EXECUTION_UNSUPPORTED")
        self.assertEqual(codes(lambda: self.machine.reject_external(" ")), "INVALID_ID")
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.state_digest(), before)

    def test_budget_ceiling_pauses_and_pool_shortfall_does_not_borrow(self):
        residual = net_residual_revenue(
            gross_revenue=100,
            refundable_window_revenue=40,
            customer_deposit_outlay=3,
            organizer_settlement_outlay=4,
            refund_reserve_outlay=3,
            operating_cost=5,
            loss_provision=5,
        )
        ceiling = reward_budget(cap=3, ratio_numerator=1, ratio_denominator=2, net_residual=residual, periods=4)
        self.assertEqual(ceiling, 3)
        reward = self.advance(ELIGIBLE)
        self.unchanged(
            lambda: self.machine.submit(
                reward,
                idempotency_key="sub-budget",
                approval_ref=human_approval(),
                signed_bytes_digest=DIGEST,
                spend_pool="PROTOCOL_REVENUE",
                budget_ceiling=ceiling,
            ),
            "BUDGET_EXCEEDED_PAUSED",
        )
        self.assertEqual(self.machine.view(reward)["phase"], ELIGIBLE)
        paid = self.submit(reward, budget_ceiling=AMOUNT)
        self.assertEqual(paid["reward"]["phase"], ISSUING)
        short = RewardMachine(opening(PROTOCOL_REVENUE=2, TOKEN_TREASURY_REWARD=50))
        opened = short.observe(
            self.key,
            idempotency_key="obs-short",
            source_view=self.view,
            rule_version="rule-v1",
            amount=AMOUNT,
            source_kind="SETTLEMENT",
        )
        reward_id_value = opened["reward"]["reward_id"]
        short.hold(reward_id_value, idempotency_key="hold-short")
        short.mark_eligible(
            reward_id_value,
            idempotency_key="elig-short",
            window_closed=True,
            source_view=self.view,
            abuse_clear=True,
        )
        short.submit(
            reward_id_value,
            idempotency_key="sub-short",
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
        )
        before = short.pool_view()["balances"]
        self.assertEqual(
            codes(
                lambda: short.observe_transfer_effects(
                    reward_id_value,
                    idempotency_key="fx-short",
                    effects_digest=EFFECTS,
                    outcome="SUCCESS",
                )
            ),
            "POOL_EXHAUSTED_PAUSED",
        )
        self.assertEqual(short.pool_view()["balances"], before)
        self.assertEqual(short.view(reward_id_value)["phase"], ISSUING)
        self.assertEqual(short.view(reward_id_value)["payout_effect_count"], 0)

    def test_forbidden_pool_is_rejected_on_submit(self):
        reward = self.advance(ELIGIBLE)
        balances = self.machine.pool_view()["balances"]
        self.unchanged(
            lambda: self.machine.submit(
                reward,
                idempotency_key="sub-deposit",
                approval_ref=human_approval(),
                signed_bytes_digest=DIGEST,
                spend_pool="CUSTOMER_DEPOSIT",
            ),
            "POOL_FORBIDDEN_FOR_TOKEN_SPEND",
        )
        self.assertEqual(self.machine.pool_view()["balances"], balances)
        self.assertEqual(self.machine.view(reward)["phase"], ELIGIBLE)

    def test_source_kinds_require_a_committed_krw_snapshot(self):
        for kind in ("SETTLEMENT", "RESALE", "RESERVATION"):
            machine = RewardMachine(self.opening)
            opened = machine.observe(
                reward_key(source_op_id="op-" + kind),
                idempotency_key="obs-" + kind,
                source_view=self.view,
                rule_version="rule-v1",
                amount=AMOUNT,
                source_kind=kind,
            )
            self.assertEqual(opened["reward"]["source_kind"], kind)
            self.assertEqual(opened["reward"]["source_view"]["phase"], "COMMITTED")
        bad = dict(self.view)
        bad["phase"] = "HELD"
        self.unchanged(
            lambda: self.machine.observe(
                reward_key(source_op_id="op-held"),
                idempotency_key="obs-held",
                source_view=bad,
                rule_version="rule-v1",
                amount=AMOUNT,
                source_kind="RESERVATION",
            ),
            "SOURCE_NOT_COMMITTED",
        )
        executed = dict(self.view)
        executed["funds_executed"] = True
        self.unchanged(
            lambda: self.machine.observe(
                reward_key(source_op_id="op-exec"),
                idempotency_key="obs-exec",
                source_view=executed,
                rule_version="rule-v1",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            ),
            "SOURCE_VIEW_REJECTED",
        )

    def test_live_settlement_view_field_names_match_and_can_be_read(self):
        live = committed_settlement_view()
        required = {
            "phase",
            "currency",
            "funds_executed",
            "bank_debit_observed",
            "legal_debtor_bound",
            "external_return_closed",
            "durable",
        }
        self.assertTrue(required <= set(live))
        for name in required - {"phase", "currency"}:
            self.assertIs(live[name], False)
        self.assertEqual(live["phase"], "COMMITTED")
        self.assertEqual(live["currency"], "KRW")
        opened = self.observe(source_view=live, idempotency_key="obs-live")
        self.assertEqual(opened["reward"]["phase"], OBSERVED)
        self.assertEqual(opened["reward"]["source_view"]["phase"], "COMMITTED")
        caller = committed_view()
        detached = self.observe(key=reward_key(source_op_id="op-detach"), source_view=caller, idempotency_key="obs-detach")
        caller["phase"] = "MUTATED"
        self.assertEqual(self.machine.view(detached["reward"]["reward_id"])["source_view"]["phase"], "COMMITTED")

    def test_restore_replays_the_same_digest(self):
        reward = self.advance(ISSUED)
        self.machine.observe_krw_refund(
            reward,
            idempotency_key="krw-restore",
            source_view=self.view,
            reason="KRW_REFUND",
        )
        journal = json.loads(json.dumps(self.machine.export_journal()))
        before = self.machine.canonical_state()
        digest = self.machine.state_digest()
        restored = RewardMachine.restore(journal, opening_balances=self.opening)
        self.assertEqual(restored.canonical_state(), before)
        self.assertEqual(restored.state_digest(), digest)
        self.assertEqual(restored.view(reward)["payout_effect_count"], 1)
        self.assertEqual(restored.view(reward)["krw_phase"], "KRW_REFUND_NOTED")
        replayed = restored.observe_transfer_effects(
            reward,
            idempotency_key="fx-1",
            effects_digest=EFFECTS,
            outcome="SUCCESS",
        )
        self.assertTrue(replayed["duplicate"])
        self.assertEqual(restored.state_digest(), digest)
        other = RewardMachine(self.opening)
        self.observe(machine=other)
        other.hold(reward, idempotency_key="hold-1")
        other.mark_eligible(
            reward,
            idempotency_key="elig-1",
            window_closed=True,
            source_view=self.view,
            abuse_clear=True,
        )
        other.submit(
            reward,
            idempotency_key="sub-1",
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
        )
        other.observe_transfer_effects(
            reward,
            idempotency_key="fx-1",
            effects_digest=EFFECTS,
            outcome="SUCCESS",
        )
        other.observe_krw_refund(
            reward,
            idempotency_key="krw-restore",
            source_view=self.view,
            reason="KRW_REFUND",
        )
        self.assertEqual(other.state_digest(), digest)
        empty = RewardMachine.restore([], opening_balances=self.opening)
        self.assertEqual(empty.state_digest(), RewardMachine(self.opening).state_digest())
        self.assertEqual(codes(lambda: RewardMachine.restore({"op": "observe"}, opening_balances=self.opening)), "INVALID_JOURNAL")

    def test_exported_journal_is_detached(self):
        self.advance(OBSERVED)
        exported = self.machine.export_journal()
        exported.append({"op": "hold"})
        self.assertEqual(len(self.machine.export_journal()), 1)
        view = self.machine.view(self.machine.reward_ids()[0])
        view["phase"] = "MUTATED"
        self.assertEqual(self.machine.view(self.machine.reward_ids()[0])["phase"], OBSERVED)

    def test_repeat_sequence_digest_is_stable(self):
        first = self.machine.state_digest()
        reward = self.advance(ISSUED)
        digest = self.machine.state_digest()
        self.assertNotEqual(digest, first)
        self.assertEqual(len(digest), 64)
        twin = RewardMachine(opening())
        self.assertEqual(twin.state_digest(), RewardMachine(dict(reversed(list(opening().items())))).state_digest())
        opened = twin.observe(
            self.key,
            idempotency_key="obs-1",
            source_view=committed_view(),
            rule_version="rule-v1",
            amount=AMOUNT,
            source_kind="SETTLEMENT",
        )
        self.assertEqual(opened["reward"]["reward_id"], reward)
        twin.hold(reward, idempotency_key="hold-1")
        twin.mark_eligible(
            reward,
            idempotency_key="elig-1",
            window_closed=True,
            source_view=committed_view(),
            abuse_clear=True,
        )
        twin.submit(
            reward,
            idempotency_key="sub-1",
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
        )
        twin.observe_transfer_effects(
            reward,
            idempotency_key="fx-1",
            effects_digest=EFFECTS,
            outcome="SUCCESS",
        )
        self.assertEqual(twin.state_digest(), digest)


def committed_settlement_view():
    suite = str(Path(__file__).resolve().parents[1] / "settlement_f01_f03")
    sys.path.insert(0, suite)
    try:
        from settlement_fsm import SettlementMachine
    finally:
        while suite in sys.path:
            sys.path.remove(suite)
    machine = SettlementMachine()
    policy = {
        "kind": "PRIMARY_FEE_BPS",
        "fee_bps": 500,
        "residual_payee": "organizer",
        "fee_payee": "platform",
    }
    machine.initiate(
        "claim-1",
        idempotency_key="init-1",
        trade_id="trade-1",
        gross=100_000,
        debtor_role="fixture-merchant",
        policy=policy,
    )
    machine.authorize("claim-1", idempotency_key="auth-1")
    machine.capture("claim-1", idempotency_key="cap-1")
    machine.commit(
        "claim-1",
        idempotency_key="commit-1",
        movement_id="move-1",
        gross=100_000,
        amount=97_000,
        fee=3_000,
        tax=0,
        held=0,
        adjustment=0,
    )
    return machine.view("claim-1")


if __name__ == "__main__":
    unittest.main()
