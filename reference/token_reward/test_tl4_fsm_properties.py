"""Author-side property checks for the reward state machine.

Invariants are checked after every command. Labels are harness-local, not
protocol commands. Fixture numbers are not policy values. The builder wrote
this file. A pass is not an independent PASS.

Terminal reading used here: REVERSED and CLAWBACK_CLAIM do not change phase.
ISSUED leaves only through an accepted supersede or observe_source_cancel,
which is the machine's defined exit. That reading is harness-local.
"""

from __future__ import annotations

import unittest

from reward_fsm import RewardMachine
from tl4_support import (
    FSM_STEPS,
    SEEDS,
    codes,
    committed_view,
    funded_opening,
    hex_digest,
    human_approval,
    reward_key,
    rng,
)
from token_reward_model import ALWAYS_FALSE_FLAGS, SPENDABLE_POOLS, TokenRewardError

AMOUNT = 4


def _invariants(test, machine, frozen):
    view = machine.pool_view()
    spent = sum(item["amount"] for item in view["spends"])
    for item in view["spends"]:
        test.assertIn(item["pool"], SPENDABLE_POOLS)
    expected = 0
    for reward_id_value in machine.reward_ids():
        reward = machine.view(reward_id_value)
        test.assertLessEqual(reward["payout_effect_count"], 1 + reward["supersession_count"])
        expected += reward["amount"] * reward["payout_effect_count"]
        test.assertNotEqual(reward["token_effect_id"], reward["krw_effect_id"])
        for name in ALWAYS_FALSE_FLAGS:
            test.assertIs(reward[name], False)
        test.assertIs(reward["non_transferable_until_chargeback_end"], True)
        if reward["phase"] in {"REVERSED", "CLAWBACK_CLAIM"}:
            frozen.setdefault(reward_id_value, reward["phase"])
        if reward_id_value in frozen:
            test.assertEqual(reward["phase"], frozen[reward_id_value])
    test.assertEqual(spent, expected)


class MachineScript:
    def __init__(self, test, seed):
        self.test = test
        self.seed = seed
        self.random = rng(seed)
        self.opening = funded_opening()
        self.machine = RewardMachine(self.opening)
        self.view = committed_view()
        self.ids = []
        self.meta = {}
        self.frozen = {}
        self.step = 0

    def attempt(self, fn, *, reward_id_value=None, krw=False):
        before = self.machine.canonical_state()
        journal = self.machine.export_journal()
        ids_before = list(self.machine.reward_ids())
        phase = outcome = None
        if reward_id_value in ids_before:
            current = self.machine.view(reward_id_value)
            phase = current["phase"]
            outcome = current["token_outcome"]
        try:
            result = fn()
        except TokenRewardError:
            self.test.assertEqual(self.machine.canonical_state(), before)
            self.test.assertEqual(self.machine.export_journal(), journal)
            _invariants(self.test, self.machine, self.frozen)
            return None
        self.test.assertEqual(journal, self.machine.export_journal()[: len(journal)])
        if result["duplicate"]:
            self.test.assertIs(result["duplicate"], True)
            self.test.assertIsNone(result["applied"])
            self.test.assertEqual(self.machine.export_journal(), journal)
        else:
            self.test.assertEqual(len(self.machine.export_journal()), len(journal) + 1)
        for name in ALWAYS_FALSE_FLAGS:
            self.test.assertIs(result[name], False)
        if krw and result["duplicate"] is False and reward_id_value in self.machine.reward_ids():
            current = self.machine.view(reward_id_value)
            self.test.assertEqual(current["phase"], phase)
            self.test.assertEqual(current["token_outcome"], outcome)
        _invariants(self.test, self.machine, self.frozen)
        return result

    def _fresh_key(self):
        self.step += 1
        return reward_key(source_op_id="op-%s-%s" % (self.seed, self.step), recipient="recipient-%s" % (self.step % 3))

    def _pick(self):
        if not self.ids:
            return None
        return self.ids[self.random.randrange(len(self.ids))]

    def observe_new(self):
        key = self._fresh_key()
        idem = "obs-%s-%s" % (self.seed, self.step)
        result = self.attempt(
            lambda: self.machine.observe(
                key,
                idempotency_key=idem,
                source_view=self.view,
                rule_version="rule-a",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            )
        )
        if result and result["duplicate"] is False:
            reward_id_value = result["reward"]["reward_id"]
            self.ids.append(reward_id_value)
            self.meta[reward_id_value] = {"key": key, "idem": idem}

    def observe_duplicate(self):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        meta = self.meta[reward_id_value]
        reordered = {
            "kind": meta["key"]["kind"],
            "recipient": meta["key"]["recipient"],
            "source_op_id": meta["key"]["source_op_id"],
            "program": meta["key"]["program"],
        }
        result = self.attempt(
            lambda: self.machine.observe(
                reordered,
                idempotency_key=meta["idem"],
                source_view=self.view,
                rule_version="rule-a",
                amount=AMOUNT,
                source_kind="SETTLEMENT",
            )
        )
        self.test.assertIsNotNone(result)
        self.test.assertIs(result["duplicate"], True)

    def observe_conflict(self):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        meta = self.meta[reward_id_value]
        result = self.attempt(
            lambda: self.machine.observe(
                meta["key"],
                idempotency_key=meta["idem"],
                source_view=self.view,
                rule_version="rule-a",
                amount=AMOUNT + 1,
                source_kind="SETTLEMENT",
            )
        )
        self.test.assertIsNone(result)

    def hold(self):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        self.attempt(lambda: self.machine.hold(reward_id_value, idempotency_key="hold-%s" % self.step), reward_id_value=reward_id_value)

    def eligible(self, *, clear=True):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        kind = None if clear else "SELF_TRADE"
        self.attempt(
            lambda: self.machine.mark_eligible(
                reward_id_value,
                idempotency_key="elig-%s" % self.step,
                window_closed=True,
                source_view=self.view,
                abuse_clear=clear,
                abuse_kind=kind,
            ),
            reward_id_value=reward_id_value,
        )

    def submit(self, *, actor="HUMAN", evidence=("evidence-1",), permit=None, digest=None, record_id=None):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        approval = human_approval(record_id or ("rec-%s-%s" % (self.seed, self.step)))
        approval["actor_type"] = actor
        approval["evidence_refs"] = list(evidence)
        signed = digest or hex_digest(1000 + self.step)
        self.attempt(
            lambda: self.machine.submit(
                reward_id_value,
                idempotency_key="sub-%s" % self.step,
                approval_ref=approval,
                signed_bytes_digest=signed,
                spend_pool="PROTOCOL_REVENUE",
                execution_permit=permit,
            ),
            reward_id_value=reward_id_value,
        )

    def transfer(self, outcome):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        self.attempt(
            lambda: self.machine.observe_transfer_effects(
                reward_id_value,
                idempotency_key="fx-%s" % self.step,
                effects_digest=hex_digest(2000 + self.step),
                outcome=outcome,
            ),
            reward_id_value=reward_id_value,
        )

    def reconcile(self, *, same=True, resolution="SUCCESS"):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        ids_before = list(self.machine.reward_ids())
        current = self.machine.view(reward_id_value)
        digest = current["signed_bytes_digest"] or hex_digest(1)
        if not same:
            digest = hex_digest(9)
        self.step += 1
        self.attempt(
            lambda: self.machine.reconcile_unknown(
                reward_id_value,
                idempotency_key="rc-%s" % self.step,
                same_digest=digest,
                resolution=resolution,
            ),
            reward_id_value=reward_id_value,
        )
        self.test.assertEqual(list(self.machine.reward_ids()), ids_before)

    def cancel(self):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        self.attempt(
            lambda: self.machine.observe_source_cancel(
                reward_id_value,
                idempotency_key="cancel-%s" % self.step,
                source_view=self.view,
                reason="source-cancel",
            ),
            reward_id_value=reward_id_value,
        )

    def refund(self):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        self.attempt(
            lambda: self.machine.observe_krw_refund(
                reward_id_value,
                idempotency_key="krw-%s" % self.step,
                source_view=self.view,
                reason="krw-note",
            ),
            reward_id_value=reward_id_value,
            krw=True,
        )

    def supersede(self):
        reward_id_value = self._pick()
        if reward_id_value is None:
            self.observe_new()
            return
        self.step += 1
        self.attempt(
            lambda: self.machine.supersede(
                reward_id_value,
                idempotency_key="sup-%s" % self.step,
                approval_ref=human_approval("sup-%s-%s" % (self.seed, self.step)),
                rule_version="rule-b-%s" % self.step,
            ),
            reward_id_value=reward_id_value,
        )

    def reject(self):
        before = self.machine.canonical_state()
        journal = self.machine.export_journal()
        self.test.assertEqual(codes(lambda: self.machine.reject_external("outside")), "EXTERNAL_EXECUTION_UNSUPPORTED")
        self.test.assertEqual(self.machine.canonical_state(), before)
        self.test.assertEqual(self.machine.export_journal(), journal)

    def run(self):
        commands = (
            self.observe_new,
            self.observe_duplicate,
            self.observe_conflict,
            self.hold,
            self.eligible,
            lambda: self.eligible(clear=False),
            self.submit,
            lambda: self.submit(actor="AI"),
            lambda: self.submit(evidence=("UNKNOWN",)),
            lambda: self.transfer("SUCCESS"),
            lambda: self.transfer("UNKNOWN"),
            lambda: self.transfer("FAILED"),
            self.reconcile,
            lambda: self.reconcile(same=False),
            self.cancel,
            self.refund,
            self.supersede,
            self.reject,
        )
        for _ in range(FSM_STEPS):
            if not self.ids or self.random.randrange(5) == 0:
                self.observe_new()
                continue
            if self.random.randrange(2) == 0:
                self._forward()
            else:
                commands[self.random.randrange(len(commands))]()
        restored = RewardMachine.restore(self.machine.export_journal(), opening_balances=self.opening)
        self.test.assertEqual(restored.state_digest(), self.machine.state_digest())
        _invariants(self.test, restored, {})

    def _forward(self):
        reward_id_value = self._pick()
        phase = self.machine.view(reward_id_value)["phase"]
        if phase == "OBSERVED":
            self.hold()
        elif phase == "HELD":
            self.eligible()
        elif phase == "ELIGIBLE":
            self.submit()
        elif phase == "ISSUING":
            self.transfer("SUCCESS" if self.random.randrange(2) == 0 else "UNKNOWN")
        elif phase == "UNKNOWN":
            which = self.random.randrange(3)
            if which == 0:
                self.reconcile()
            elif which == 1:
                current = self.machine.view(reward_id_value)
                self.submit(permit=None, digest=current["signed_bytes_digest"])
            else:
                current = self.machine.view(reward_id_value)
                self.submit(
                    permit={
                        "fence_ref": "fence-slot",
                        "signed_bytes_digest": current["signed_bytes_digest"],
                    },
                    digest=current["signed_bytes_digest"],
                )
        elif phase == "ISSUED":
            self.supersede() if self.random.randrange(2) == 0 else self.refund()
        else:
            self.hold()


class RewardFsmPropertyTests(unittest.TestCase):
    def setUp(self):
        self.opening = funded_opening()
        self.machine = RewardMachine(self.opening)
        self.view = committed_view()

    def _advance_to_issuing(self, source="op-scripted"):
        opened = self.machine.observe(
            reward_key(source_op_id=source),
            idempotency_key="obs-%s" % source,
            source_view=self.view,
            rule_version="rule-a",
            amount=AMOUNT,
            source_kind="RESALE",
        )
        reward_id_value = opened["reward"]["reward_id"]
        self.machine.hold(reward_id_value, idempotency_key="hold-%s" % source)
        self.machine.mark_eligible(
            reward_id_value,
            idempotency_key="elig-%s" % source,
            window_closed=True,
            source_view=self.view,
            abuse_clear=True,
        )
        submitted = self.machine.submit(
            reward_id_value,
            idempotency_key="sub-%s" % source,
            approval_ref=human_approval("approval-%s" % source),
            signed_bytes_digest=hex_digest(42),
            spend_pool="TOKEN_TREASURY_REWARD",
        )
        self.assertNotEqual(submitted["reward"]["token_effect_id"], submitted["reward"]["krw_effect_id"])
        return reward_id_value

    def test_TL4_TK07_replay_idempotency_and_supersede_bound_payouts(self):
        """TL0-TK07-T1. One payout effect, then one more only after supersede."""

        reward_id_value = self._advance_to_issuing()
        again = self.machine.observe(
            reward_key(source_op_id="op-scripted"),
            idempotency_key="obs-op-scripted",
            source_view=self.view,
            rule_version="rule-a",
            amount=AMOUNT,
            source_kind="RESALE",
        )
        self.assertIs(again["duplicate"], True)
        self.assertEqual(len(self.machine.export_journal()), 4)
        reordered = {
            "kind": "participation",
            "recipient": "recipient-1",
            "program": "program-1",
            "source_op_id": "op-scripted",
        }
        same = self.machine.observe(
            reordered,
            idempotency_key="obs-op-scripted",
            source_view=self.view,
            rule_version="rule-a",
            amount=AMOUNT,
            source_kind="RESALE",
        )
        self.assertIs(same["duplicate"], True)
        before = self.machine.canonical_state()
        journal = self.machine.export_journal()
        self.assertEqual(
            codes(
                lambda: self.machine.observe(
                    reward_key(source_op_id="op-scripted"),
                    idempotency_key="obs-op-scripted",
                    source_view=self.view,
                    rule_version="rule-a",
                    amount=AMOUNT + 1,
                    source_kind="RESALE",
                )
            ),
            "IDEMPOTENCY_CONFLICT",
        )
        self.assertEqual(self.machine.canonical_state(), before)
        self.assertEqual(self.machine.export_journal(), journal)
        self.machine.observe_transfer_effects(
            reward_id_value,
            idempotency_key="fx-scripted",
            effects_digest=hex_digest(7),
            outcome="SUCCESS",
        )
        issued = self.machine.view(reward_id_value)
        self.assertEqual(issued["payout_effect_count"], 1)
        self.assertEqual(issued["supersession_count"], 0)
        self.machine.supersede(
            reward_id_value,
            idempotency_key="sup-scripted",
            approval_ref=human_approval("approval-sup"),
            rule_version="rule-b",
        )
        self.machine.submit(
            reward_id_value,
            idempotency_key="sub-2",
            approval_ref=human_approval("approval-2"),
            signed_bytes_digest=hex_digest(43),
            spend_pool="TOKEN_TREASURY_REWARD",
        )
        self.machine.observe_transfer_effects(
            reward_id_value,
            idempotency_key="fx-2",
            effects_digest=hex_digest(8),
            outcome="SUCCESS",
        )
        twice = self.machine.view(reward_id_value)
        self.assertEqual(twice["payout_effect_count"], 2)
        self.assertEqual(twice["supersession_count"], 1)
        self.assertLessEqual(twice["payout_effect_count"], 1 + twice["supersession_count"])
        spent = sum(item["amount"] for item in self.machine.pool_view()["spends"])
        self.assertEqual(spent, AMOUNT * twice["payout_effect_count"])
        restored = RewardMachine.restore(self.machine.export_journal(), opening_balances=self.opening)
        self.assertEqual(restored.state_digest(), self.machine.state_digest())

    def test_TL4_TK07_unknown_reconcile_creates_no_reward(self):
        """TL0-TK07-T1 slice. UNKNOWN stays a query until the same digest is reconciled."""

        reward_id_value = self._advance_to_issuing("op-unknown")
        ids_before = list(self.machine.reward_ids())
        self.machine.observe_transfer_effects(
            reward_id_value,
            idempotency_key="fx-unknown",
            effects_digest=hex_digest(11),
            outcome="UNKNOWN",
        )
        self.assertEqual(self.machine.view(reward_id_value)["phase"], "UNKNOWN")
        before = self.machine.canonical_state()
        self.assertEqual(
            codes(
                lambda: self.machine.submit(
                    reward_id_value,
                    idempotency_key="resend-none",
                    approval_ref=human_approval("approval-resend"),
                    signed_bytes_digest=hex_digest(42),
                    spend_pool="TOKEN_TREASURY_REWARD",
                )
            ),
            "RESEND_PERMIT_REQUIRED",
        )
        self.assertEqual(self.machine.canonical_state(), before)
        self.assertEqual(
            codes(
                lambda: self.machine.submit(
                    reward_id_value,
                    idempotency_key="resend-bad",
                    approval_ref=human_approval("approval-resend-b"),
                    signed_bytes_digest=hex_digest(99),
                    spend_pool="TOKEN_TREASURY_REWARD",
                    execution_permit={"fence_ref": "fence-slot", "signed_bytes_digest": hex_digest(99)},
                )
            ),
            "DIGEST_MISMATCH",
        )
        self.assertEqual(
            codes(
                lambda: self.machine.reconcile_unknown(
                    reward_id_value,
                    idempotency_key="rc-bad",
                    same_digest=hex_digest(98),
                    resolution="FAILED",
                )
            ),
            "DIGEST_MISMATCH",
        )
        self.machine.reconcile_unknown(
            reward_id_value,
            idempotency_key="rc-ok",
            same_digest=hex_digest(42),
            resolution="SUCCESS",
        )
        self.assertEqual(list(self.machine.reward_ids()), ids_before)
        self.assertEqual(self.machine.view(reward_id_value)["phase"], "ISSUED")
        self.assertEqual(self.machine.view(reward_id_value)["payout_effect_count"], 1)

    def test_TL4_TK08_krw_refund_does_not_move_the_token_phase(self):
        """TL0-TK08-T1. The KRW note is a different effect id and does not move the token phase."""

        reward_id_value = self._advance_to_issuing("op-krw")
        before = self.machine.view(reward_id_value)
        noted = self.machine.observe_krw_refund(
            reward_id_value,
            idempotency_key="krw-1",
            source_view=self.view,
            reason="window",
        )
        after = self.machine.view(reward_id_value)
        self.assertEqual(after["phase"], before["phase"])
        self.assertEqual(after["token_outcome"], before["token_outcome"])
        self.assertNotEqual(after["token_effect_id"], after["krw_effect_id"])
        self.assertEqual(noted["effect"]["krw_effect_id"], after["krw_effect_id"])
        self.assertIs(after["krw_paid"], False)
        self.assertIs(after["token_issued"], False)
        self.assertEqual(after["krw_phase"], "KRW_REFUND_NOTED")

    def test_TL4_TK06_T6_slice_ai_unknown_evidence_and_reused_record_are_rejected(self):
        """TL1-TK06-T6 slice. The slot stays structural. No approver is named.

        Labels are harness-local, not protocol commands.
        """

        reward_id_value = self._advance_to_issuing("op-ai")
        # Return the machine to ELIGIBLE is not required: approval is parsed first.
        before = self.machine.canonical_state()
        ai = human_approval("approval-ai")
        ai["actor_type"] = "AI"
        self.assertEqual(
            codes(
                lambda: self.machine.submit(
                    reward_id_value,
                    idempotency_key="sub-ai",
                    approval_ref=ai,
                    signed_bytes_digest=hex_digest(3),
                    spend_pool="PROTOCOL_REVENUE",
                )
            ),
            "AI_APPROVAL_REJECTED",
        )
        other = human_approval("approval-other-actor")
        other["actor_type"] = "OTHER"
        self.assertEqual(
            codes(
                lambda: self.machine.submit(
                    reward_id_value,
                    idempotency_key="sub-other",
                    approval_ref=other,
                    signed_bytes_digest=hex_digest(4),
                    spend_pool="PROTOCOL_REVENUE",
                )
            ),
            "ACTOR_TYPE_REJECTED",
        )
        unknown = human_approval("approval-unknown-evidence")
        unknown["evidence_refs"] = ["UNKNOWN"]
        self.assertEqual(
            codes(
                lambda: self.machine.submit(
                    reward_id_value,
                    idempotency_key="sub-unk",
                    approval_ref=unknown,
                    signed_bytes_digest=hex_digest(5),
                    spend_pool="PROTOCOL_REVENUE",
                )
            ),
            "APPROVAL_EVIDENCE_UNKNOWN",
        )
        self.assertEqual(self.machine.canonical_state(), before)
        opened = self.machine.observe(
            reward_key(source_op_id="op-reuse"),
            idempotency_key="obs-op-reuse",
            source_view=self.view,
            rule_version="rule-a",
            amount=AMOUNT,
            source_kind="RESALE",
        )
        second = opened["reward"]["reward_id"]
        self.machine.hold(second, idempotency_key="hold-op-reuse")
        self.machine.mark_eligible(
            second,
            idempotency_key="elig-op-reuse",
            window_closed=True,
            source_view=self.view,
            abuse_clear=True,
        )
        self.assertEqual(
            codes(
                lambda: self.machine.submit(
                    second,
                    idempotency_key="sub-reuse",
                    approval_ref=human_approval("approval-op-ai"),
                    signed_bytes_digest=hex_digest(6),
                    spend_pool="PROTOCOL_REVENUE",
                )
            ),
            "APPROVAL_RECORD_REUSED",
        )

    def test_TL4_TK07_random_command_sequences_hold_invariants(self):
        """TL0-TK07-T1 and TL0-TK08-T1. Seeded sequences, including duplicates and rejects."""

        for seed in SEEDS:
            MachineScript(self, seed).run()


if __name__ == "__main__":
    unittest.main()
