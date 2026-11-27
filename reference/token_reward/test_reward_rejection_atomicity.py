"""Rejection-atomicity audit for the reward state machine.

Existing coverage map (test_reward_fsm.py): every deterministic rejection
code is already exercised — REWARD_ALREADY_OBSERVED,
RULE_VERSION_REPAY_FORBIDDEN, the SOURCE_* family, the APPROVAL_* family,
AI_APPROVAL_REJECTED, APPROVAL_RECORD_REUSED, BUDGET_EXCEEDED_PAUSED,
POOL_UNKNOWN / POOL_FORBIDDEN_FOR_TOKEN_SPEND / POOL_EXHAUSTED_PAUSED,
CAP_EXHAUSTED_PAUSED, WINDOW_OPEN, ABUSE_BLOCKED, TOKEN_EFFECT_CLOSED,
KRW_EFFECT_ALREADY_NOTED, TERMINAL_IMMUTABLE, ILLEGAL_TRANSITION,
IDEMPOTENCY_CONFLICT, INVALID_JOURNAL and the resend codes. The
``unchanged`` helper compares the rejecting machine's own
canonical_state and journal before and after the call — a same-machine
comparison. This file adds what that helper cannot see: an untouched
control machine, the ``restore(export_journal())`` round trip on both
sides, and a test-owned late-failure seam.

Each ``*_leaves_no_trace`` case compares the machine that saw the
rejected call with the control: state_digest, canonical_state,
export_journal and the restore round trip. A stored rejection — same
key, same canonical arguments, same error replayed — is the only trace
the comparison allows; ``_idempotency`` and ``_approval_ids`` are
outside canonical_state, so the boundary pins at the bottom cover them
observably.

Contract status: no contract document states a reward-side
rejection-atomicity clause. BOOKING_RESALE_ADMISSION_GATES.md §9.4 (a
rejected command does not enter the journal; restore does not restore
the rejection) covers the reservation machine only. For RewardMachine
the property is contract-undefined but implemented, so the umbrella
row and the findings below are class B characterizations, not contract
assertions. The deterministic cases pin observed behavior; they do not
invent semantics.

Not-applicable rows: ``view``, ``reward_ids``, ``pool_view``,
``export_journal``, ``canonical_state`` and ``state_digest`` are
read-only and have no mutation boundary. ``restore`` is a classmethod;
its ``INVALID_JOURNAL`` cases are asserted to fail on a fresh build
without touching a live machine. ``reject_external`` mutates nothing
and journals nothing by construction; its case compares against a
control anyway. The internal ``MOCK_INVARIANT`` checks inside
``submit``/``_resend``/``_apply_outcome``/``supersede`` and the
``POOL_FORBIDDEN_FOR_TOKEN_SPEND`` recheck inside ``_apply_outcome``
have no deterministic caller input at this layer (their guards are
established earlier), so they get fault-seam coverage instead of a
deterministic case.

Late-failure seam (``test_fault_*``): RewardMachine applies every
reward mutation before calling ``self._invariant`` and keeps no
rollback wrapper, so a fault raised at the invariant leaves the
mutation applied but unjournaled. These are labeled characterization
tests: they pin the observed divergence (journal still equal to the
control, canonical_state and state_digest divergent,
restore(export_journal()) equal to the control rather than to the
machine, and a later valid op diverging permanently). The pool seam
``test_fault_pool_*`` injects at ``PoolLedger._conserve`` after the
balance moved and shows the spend leaving no journal entry either.
Each is a class B finding in the validation record; none is fixed here.
"""

import unittest
from unittest import mock

from reward_fsm import RewardMachine
from token_reward_model import PoolLedger, TokenRewardError
from tl4_support import (
    codes,
    committed_view,
    funded_opening,
    hex_digest,
    human_approval,
    opening,
    reward_key,
)

DIGEST = hex_digest(0xAB)
DIGEST_B = hex_digest(0xCD)
EFFECTS = hex_digest(0xEF)

# Synthetic point amount and pool balances. Not policy values.
AMOUNT = 4


class RewardRejectionAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.opening = funded_opening()
        self.key = reward_key()
        self.view = committed_view()

    def fresh(self, balances=None):
        return RewardMachine(self.opening if balances is None else balances)

    # --- command helpers ------------------------------------------------

    def observe(self, machine, reward_key_value=None, idem="obs-1", **changes):
        body = dict(
            reward_key=self.key if reward_key_value is None else reward_key_value,
            source_view=self.view,
            rule_version="rule-v1",
            amount=AMOUNT,
            source_kind="SETTLEMENT",
        )
        body.update(changes)
        return machine.observe(body.pop("reward_key"), idempotency_key=idem, **body)

    def hold(self, machine, reward, idem="hold-1"):
        return machine.hold(reward, idempotency_key=idem)

    def eligible(self, machine, reward, idem="elig-1", **changes):
        body = dict(window_closed=True, source_view=self.view, abuse_clear=True)
        body.update(changes)
        return machine.mark_eligible(reward, idempotency_key=idem, **body)

    def submit(self, machine, reward, idem="sub-1", **changes):
        body = dict(
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
        )
        body.update(changes)
        return machine.submit(reward, idempotency_key=idem, **body)

    def resend(self, machine, reward, idem="resend-1", **changes):
        body = dict(
            approval_ref=human_approval(),
            signed_bytes_digest=DIGEST,
            spend_pool="PROTOCOL_REVENUE",
            execution_permit={"fence_ref": "fence-slot", "signed_bytes_digest": DIGEST},
        )
        body.update(changes)
        return machine.submit(reward, idempotency_key=idem, **body)

    def effects(self, machine, reward, idem="fx-1", **changes):
        body = dict(effects_digest=EFFECTS, outcome="SUCCESS")
        body.update(changes)
        return machine.observe_transfer_effects(reward, idempotency_key=idem, **body)

    def reconcile(self, machine, reward, idem="recon-1", **changes):
        body = dict(same_digest=DIGEST, resolution="SUCCESS")
        body.update(changes)
        return machine.reconcile_unknown(reward, idempotency_key=idem, **body)

    def cancel(self, machine, reward, idem="cancel-1", **changes):
        body = dict(source_view=self.view, reason="SOURCE_CANCELLED")
        body.update(changes)
        return machine.observe_source_cancel(reward, idempotency_key=idem, **body)

    def refund(self, machine, reward, idem="krw-1", **changes):
        body = dict(source_view=self.view, reason="KRW_REFUND")
        body.update(changes)
        return machine.observe_krw_refund(reward, idempotency_key=idem, **body)

    def supersede(self, machine, reward, idem="sup-1", **changes):
        body = dict(approval_ref=human_approval("approval-2"), rule_version="rule-v2")
        body.update(changes)
        return machine.supersede(reward, idempotency_key=idem, **body)

    # --- machine/control pair builders -----------------------------------

    def observed_pair(self, balances=None):
        machine, control = self.fresh(balances), self.fresh(balances)
        opened = self.observe(machine)
        self.observe(control)
        return machine, control, opened["reward"]["reward_id"]

    def held_pair(self, balances=None):
        machine, control, reward = self.observed_pair(balances)
        for side in (machine, control):
            self.hold(side, reward)
        return machine, control, reward

    def eligible_pair(self, balances=None):
        machine, control, reward = self.held_pair(balances)
        for side in (machine, control):
            self.eligible(side, reward)
        return machine, control, reward

    def issuing_pair(self, balances=None):
        machine, control, reward = self.eligible_pair(balances)
        for side in (machine, control):
            self.submit(side, reward)
        return machine, control, reward

    def unknown_pair(self, balances=None):
        machine, control, reward = self.issuing_pair(balances)
        for side in (machine, control):
            self.effects(side, reward, outcome="UNKNOWN")
        return machine, control, reward

    def issued_pair(self, balances=None):
        machine, control, reward = self.issuing_pair(balances)
        for side in (machine, control):
            self.effects(side, reward)
        return machine, control, reward

    def reversed_pair(self, balances=None):
        machine, control, reward = self.held_pair(balances)
        for side in (machine, control):
            self.cancel(side, reward)
        return machine, control, reward

    def clawback_pair(self, balances=None):
        machine, control, reward = self.issued_pair(balances)
        for side in (machine, control):
            self.cancel(side, reward)
        return machine, control, reward

    def refund_noted_pair(self, balances=None):
        machine, control, reward = self.issued_pair(balances)
        for side in (machine, control):
            self.refund(side, reward)
        return machine, control, reward

    def second_reward(self, machine, through="eligible"):
        opened = self.observe(
            machine, reward_key(source_op_id="op-2"), idem="obs-2"
        )
        reward = opened["reward"]["reward_id"]
        if through == "observed":
            return reward
        self.hold(machine, reward, idem="hold-2")
        if through == "held":
            return reward
        self.eligible(machine, reward, idem="elig-2")
        return reward

    # --- comparison harness -----------------------------------------------

    def assert_same_as(self, machine, control, balances=None):
        balances = self.opening if balances is None else balances
        self.assertEqual(machine.state_digest(), control.state_digest())
        self.assertEqual(machine.canonical_state(), control.canonical_state())
        self.assertEqual(machine.export_journal(), control.export_journal())
        for side in (machine, control):
            restored = RewardMachine.restore(
                side.export_journal(), opening_balances=balances
            )
            self.assertEqual(restored.canonical_state(), side.canonical_state())
            self.assertEqual(restored.state_digest(), side.state_digest())

    def assert_unapplied_mutation(self, machine, control, balances=None):
        """Pin the fault-seam characterization: mutation applied, not journaled."""
        balances = self.opening if balances is None else balances
        self.assertEqual(machine.export_journal(), control.export_journal())
        self.assertNotEqual(machine.canonical_state(), control.canonical_state())
        self.assertNotEqual(machine.state_digest(), control.state_digest())
        restored = RewardMachine.restore(
            machine.export_journal(), opening_balances=balances
        )
        self.assertEqual(restored.canonical_state(), control.canonical_state())
        self.assertNotEqual(restored.canonical_state(), machine.canonical_state())

    def reject(self, code, fn):
        self.assertEqual(codes(fn), code)
        # The same key with the same canonical arguments replays the stored
        # error; that idempotency record is the only trace a rejection may
        # leave, and it sits outside canonical_state.
        self.assertEqual(codes(fn), code)

    def fault(self):
        return mock.patch.object(
            RewardMachine, "_invariant", side_effect=[TokenRewardError("MOCK_INVARIANT")]
        )

    def pool_fault(self):
        return mock.patch.object(
            PoolLedger, "_conserve", side_effect=[TokenRewardError("MOCK_INVARIANT")]
        )

    # --- observe -----------------------------------------------------------

    def test_observe_already_observed_leaves_no_trace(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "REWARD_ALREADY_OBSERVED",
            lambda: self.observe(machine, idem="obs-again"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.hold(machine, reward), self.hold(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_rule_version_repay_leaves_no_trace(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "RULE_VERSION_REPAY_FORBIDDEN",
            lambda: self.observe(machine, idem="obs-v2", rule_version="rule-v2"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.hold(machine, reward), self.hold(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_source_not_committed_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        bad = dict(self.view, phase="HELD")
        self.reject(
            "SOURCE_NOT_COMMITTED",
            lambda: self.observe(machine, idem="obs-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_source_view_rejected_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        bad = dict(self.view, funds_executed=True)
        self.reject(
            "SOURCE_VIEW_REJECTED",
            lambda: self.observe(machine, idem="obs-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_currency_unsupported_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        bad = dict(self.view, currency="USD")
        self.reject(
            "CURRENCY_UNSUPPORTED",
            lambda: self.observe(machine, idem="obs-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_source_kind_unsupported_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "SOURCE_KIND_UNSUPPORTED",
            lambda: self.observe(machine, idem="obs-bad", source_kind="AIRDROP"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_reward_key_fields_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        bad = {"program": "program-1", "source_op_id": "op-1", "recipient": "recipient-1"}
        self.reject(
            "REWARD_KEY_FIELDS",
            lambda: self.observe(machine, bad, idem="obs-bad"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_invalid_amount_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "INVALID_AMOUNT",
            lambda: self.observe(machine, idem="obs-bad", amount=0),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_invalid_id_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "INVALID_ID",
            lambda: self.observe(machine, idem=" "),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    def test_observe_invalid_rule_version_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "INVALID_RULE_VERSION",
            lambda: self.observe(machine, idem="obs-bad", rule_version=""),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    # --- hold --------------------------------------------------------------

    def test_hold_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: machine.hold("ghost", idempotency_key="hold-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.hold(machine, reward), self.hold(control, reward))
        self.assert_same_as(machine, control)

    def test_hold_illegal_transition_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: machine.hold(reward, idempotency_key="hold-again"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_hold_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.reversed_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: machine.hold(reward, idempotency_key="hold-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    # --- mark_eligible ------------------------------------------------------

    def test_mark_eligible_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.eligible(machine, "ghost", idem="elig-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_illegal_transition_leaves_no_trace(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.eligible(machine, reward, idem="elig-bad"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.hold(side, reward)
            self.eligible(side, reward, idem="elig-ok")
        self.assert_same_as(machine, control)

    def test_mark_eligible_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.reversed_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.eligible(machine, reward, idem="elig-bad"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    def test_mark_eligible_window_open_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "WINDOW_OPEN",
            lambda: self.eligible(machine, reward, idem="elig-bad", window_closed=False),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_abuse_blocked_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "ABUSE_BLOCKED",
            lambda: self.eligible(
                machine, reward, idem="elig-bad", abuse_clear=False, abuse_kind="SELF_TRADE"
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_abuse_kind_unexpected_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "ABUSE_KIND_UNEXPECTED",
            lambda: self.eligible(machine, reward, idem="elig-bad", abuse_kind="SELF_TRADE"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_abuse_kind_unsupported_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "ABUSE_KIND_UNSUPPORTED",
            lambda: self.eligible(
                machine, reward, idem="elig-bad", abuse_clear=False, abuse_kind="BOTNET"
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_cap_exhausted_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "CAP_EXHAUSTED_PAUSED",
            lambda: self.eligible(machine, reward, idem="elig-bad", recipient_cap=AMOUNT - 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_flag_type_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "FLAG_TYPE",
            lambda: self.eligible(machine, reward, idem="elig-bad", window_closed="yes"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_source_not_committed_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        bad = dict(self.view, phase="AUTHORIZED")
        self.reject(
            "SOURCE_NOT_COMMITTED",
            lambda: self.eligible(machine, reward, idem="elig-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    def test_mark_eligible_invalid_cap_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "INVALID_NONNEGATIVE",
            lambda: self.eligible(machine, reward, idem="elig-bad", program_cap=-1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.eligible(machine, reward), self.eligible(control, reward))
        self.assert_same_as(machine, control)

    # --- submit -------------------------------------------------------------

    def test_submit_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.submit(machine, "ghost", idem="sub-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_illegal_transition_leaves_no_trace(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.submit(machine, reward, idem="sub-bad"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.hold(side, reward)
            self.eligible(side, reward, idem="elig-1")
        self.assert_same_as(machine, control)

    def test_submit_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.submit(machine, reward, idem="sub-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.refund(side, reward)
        self.assert_same_as(machine, control)

    def test_submit_ai_approval_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "AI_APPROVAL_REJECTED",
            lambda: self.submit(
                machine,
                reward,
                idem="sub-bad",
                approval_ref={**human_approval("approval-ai"), "actor_type": "AI"},
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_approval_fields_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        bad = human_approval()
        bad.pop("scope_ref")
        self.reject(
            "APPROVAL_FIELDS",
            lambda: self.submit(machine, reward, idem="sub-bad", approval_ref=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_actor_type_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "ACTOR_TYPE_REJECTED",
            lambda: self.submit(
                machine,
                reward,
                idem="sub-bad",
                approval_ref={**human_approval(), "actor_type": "ROBOT"},
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_approval_generation_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "APPROVAL_GENERATION",
            lambda: self.submit(
                machine, reward, idem="sub-bad", approval_ref=human_approval(generation=0)
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_approval_evidence_required_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        bad = {**human_approval(), "evidence_refs": []}
        self.reject(
            "APPROVAL_EVIDENCE_REQUIRED",
            lambda: self.submit(machine, reward, idem="sub-bad", approval_ref=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_approval_evidence_unknown_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        bad = {**human_approval(), "evidence_refs": ["UNKNOWN"]}
        self.reject(
            "APPROVAL_EVIDENCE_UNKNOWN",
            lambda: self.submit(machine, reward, idem="sub-bad", approval_ref=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_approval_record_reused_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        for side in (machine, control):
            self.submit(side, reward)
            second = self.second_reward(side)
        self.reject(
            "APPROVAL_RECORD_REUSED",
            lambda: self.submit(machine, second, idem="sub-2"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.submit(machine, second, idem="sub-ok", approval_ref=human_approval("approval-2")),
            self.submit(control, second, idem="sub-ok", approval_ref=human_approval("approval-2")),
        )
        self.assert_same_as(machine, control)

    def test_submit_budget_exceeded_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "BUDGET_EXCEEDED_PAUSED",
            lambda: self.submit(machine, reward, idem="sub-bad", budget_ceiling=AMOUNT - 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_permit_unexpected_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        permit = {"fence_ref": "fence-slot", "signed_bytes_digest": DIGEST}
        self.reject(
            "PERMIT_UNEXPECTED",
            lambda: self.submit(machine, reward, idem="sub-bad", execution_permit=permit),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_pool_unknown_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "POOL_UNKNOWN",
            lambda: self.submit(machine, reward, idem="sub-bad", spend_pool="MARKETING"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_pool_forbidden_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "POOL_FORBIDDEN_FOR_TOKEN_SPEND",
            lambda: self.submit(machine, reward, idem="sub-bad", spend_pool="CUSTOMER_DEPOSIT"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_digest_invalid_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "DIGEST_INVALID",
            lambda: self.submit(machine, reward, idem="sub-bad", signed_bytes_digest="zz"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_submit_invalid_ceiling_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "INVALID_NONNEGATIVE",
            lambda: self.submit(machine, reward, idem="sub-bad", budget_ceiling=-1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    # --- submit resend path (phase UNKNOWN) ---------------------------------

    def test_resend_permit_required_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "RESEND_PERMIT_REQUIRED",
            lambda: self.submit(machine, reward, idem="resend-no-permit"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.resend(machine, reward), self.resend(control, reward))
        self.assert_same_as(machine, control)

    def test_resend_digest_mismatch_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        permit = {"fence_ref": "fence-slot", "signed_bytes_digest": DIGEST_B}
        self.reject(
            "DIGEST_MISMATCH",
            lambda: self.submit(
                machine, reward, idem="resend-bad", execution_permit=permit
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.resend(machine, reward), self.resend(control, reward))
        self.assert_same_as(machine, control)

    def test_resend_spend_pool_conflict_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "SPEND_POOL_CONFLICT",
            lambda: self.resend(
                machine, reward, idem="resend-bad", spend_pool="TOKEN_TREASURY_REWARD"
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.resend(machine, reward), self.resend(control, reward))
        self.assert_same_as(machine, control)

    def test_resend_budget_exceeded_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "BUDGET_EXCEEDED_PAUSED",
            lambda: self.resend(machine, reward, idem="resend-bad", budget_ceiling=AMOUNT - 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.resend(machine, reward), self.resend(control, reward))
        self.assert_same_as(machine, control)

    # --- observe_transfer_effects --------------------------------------------

    def test_observe_transfer_effects_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.issuing_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.effects(machine, "ghost", idem="fx-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.effects(machine, reward), self.effects(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_illegal_transition_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.effects(machine, reward, idem="fx-bad"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.effects(machine, reward, idem="fx-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.refund(side, reward)
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_reversed_leaves_no_trace(self):
        machine, control, reward = self.reversed_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.effects(machine, reward, idem="fx-late"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_digest_invalid_leaves_no_trace(self):
        machine, control, reward = self.issuing_pair()
        self.reject(
            "DIGEST_INVALID",
            lambda: self.effects(machine, reward, idem="fx-bad", effects_digest="qq"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.effects(machine, reward), self.effects(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_outcome_unsupported_leaves_no_trace(self):
        machine, control, reward = self.issuing_pair()
        self.reject(
            "OUTCOME_UNSUPPORTED",
            lambda: self.effects(machine, reward, idem="fx-bad", outcome="MAYBE"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.effects(machine, reward), self.effects(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_token_effect_closed_leaves_no_trace(self):
        machine, control, reward = self.issuing_pair()
        for side in (machine, control):
            self.effects(side, reward, outcome="FAILED")
        self.reject(
            "TOKEN_EFFECT_CLOSED",
            lambda: self.effects(machine, reward, idem="fx-retry"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.refund(machine, reward), self.refund(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_transfer_effects_pool_exhausted_leaves_no_trace(self):
        short = opening(PROTOCOL_REVENUE=AMOUNT - 1)
        machine, control, reward = self.issuing_pair(balances=short)
        self.reject(
            "POOL_EXHAUSTED_PAUSED",
            lambda: self.effects(machine, reward, idem="fx-bad"),
        )
        self.assert_same_as(machine, control, balances=short)
        self.assertEqual(
            self.effects(machine, reward, outcome="FAILED"),
            self.effects(control, reward, outcome="FAILED"),
        )
        self.assert_same_as(machine, control, balances=short)

    # --- reconcile_unknown -----------------------------------------------------

    def test_reconcile_unknown_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.reconcile(machine, "ghost", idem="recon-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.reconcile(machine, reward), self.reconcile(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_reconcile_unknown_illegal_transition_leaves_no_trace(self):
        machine, control, reward = self.issuing_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.reconcile(machine, reward, idem="recon-bad"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.effects(machine, reward), self.effects(control, reward))
        self.assert_same_as(machine, control)

    def test_reconcile_unknown_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.reconcile(machine, reward, idem="recon-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.refund(side, reward)
        self.assert_same_as(machine, control)

    def test_reconcile_unknown_digest_invalid_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "DIGEST_INVALID",
            lambda: self.reconcile(machine, reward, idem="recon-bad", same_digest="qq"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.reconcile(machine, reward), self.reconcile(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_reconcile_unknown_outcome_unsupported_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "OUTCOME_UNSUPPORTED",
            lambda: self.reconcile(machine, reward, idem="recon-bad", resolution="MAYBE"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.reconcile(machine, reward), self.reconcile(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_reconcile_unknown_digest_mismatch_leaves_no_trace(self):
        machine, control, reward = self.unknown_pair()
        self.reject(
            "DIGEST_MISMATCH",
            lambda: self.reconcile(machine, reward, idem="recon-bad", same_digest=DIGEST_B),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.reconcile(machine, reward), self.reconcile(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_reconcile_unknown_pool_exhausted_leaves_no_trace(self):
        drained = opening(PROTOCOL_REVENUE=8)
        machine, control, reward = self.unknown_pair(balances=drained)
        for side in (machine, control):
            second = self.observe(
                side, reward_key(source_op_id="op-2"), idem="obs-2", amount=5
            )["reward"]["reward_id"]
            self.hold(side, second, idem="hold-2")
            self.eligible(side, second, idem="elig-2")
            self.submit(
                side,
                second,
                idem="sub-2",
                approval_ref=human_approval("approval-2"),
                signed_bytes_digest=DIGEST_B,
            )
            self.effects(side, second, idem="fx-2")
        # The second payout leaves 8 - 5 = 3 < the first reward's 4.
        self.reject(
            "POOL_EXHAUSTED_PAUSED",
            lambda: self.reconcile(machine, reward, idem="recon-bad"),
        )
        self.assert_same_as(machine, control, balances=drained)
        self.assertEqual(
            self.reconcile(machine, reward, resolution="FAILED"),
            self.reconcile(control, reward, resolution="FAILED"),
        )
        self.assert_same_as(machine, control, balances=drained)

    # --- observe_source_cancel -------------------------------------------------

    def test_observe_source_cancel_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.cancel(machine, "ghost", idem="cancel-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.cancel(machine, reward), self.cancel(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_source_cancel_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.reversed_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.cancel(machine, reward, idem="cancel-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    def test_observe_source_cancel_clawback_terminal_leaves_no_trace(self):
        machine, control, reward = self.clawback_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.cancel(machine, reward, idem="cancel-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    def test_observe_source_cancel_source_not_committed_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        bad = dict(self.view, phase="AUTHORIZED")
        self.reject(
            "SOURCE_NOT_COMMITTED",
            lambda: self.cancel(machine, reward, idem="cancel-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.cancel(machine, reward), self.cancel(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_source_cancel_invalid_reason_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "INVALID_ID",
            lambda: self.cancel(machine, reward, idem="cancel-bad", reason=""),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.cancel(machine, reward), self.cancel(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_source_cancel_source_view_rejected_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        bad = dict(self.view, bank_debit_observed=True)
        self.reject(
            "SOURCE_VIEW_REJECTED",
            lambda: self.cancel(machine, reward, idem="cancel-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.cancel(machine, reward), self.cancel(control, reward))
        self.assert_same_as(machine, control)

    # --- observe_krw_refund ------------------------------------------------------

    def test_observe_krw_refund_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.refund(machine, "ghost", idem="krw-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.refund(machine, reward), self.refund(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_krw_refund_already_noted_leaves_no_trace(self):
        machine, control, reward = self.refund_noted_pair()
        self.reject(
            "KRW_EFFECT_ALREADY_NOTED",
            lambda: self.refund(machine, reward, idem="krw-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    def test_observe_krw_refund_source_not_committed_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        bad = dict(self.view, phase="AUTHORIZED")
        self.reject(
            "SOURCE_NOT_COMMITTED",
            lambda: self.refund(machine, reward, idem="krw-bad", source_view=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.refund(machine, reward), self.refund(control, reward))
        self.assert_same_as(machine, control)

    def test_observe_krw_refund_invalid_reason_leaves_no_trace(self):
        machine, control, reward = self.held_pair()
        self.reject(
            "INVALID_ID",
            lambda: self.refund(machine, reward, idem="krw-bad", reason=""),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.refund(machine, reward), self.refund(control, reward))
        self.assert_same_as(machine, control)

    # --- supersede -----------------------------------------------------------------

    def test_supersede_unknown_reward_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "UNKNOWN_REWARD",
            lambda: self.supersede(machine, "ghost", idem="sup-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.supersede(machine, reward), self.supersede(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_supersede_illegal_transition_leaves_no_trace(self):
        machine, control, reward = self.eligible_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.supersede(machine, reward, idem="sup-bad"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.submit(machine, reward), self.submit(control, reward))
        self.assert_same_as(machine, control)

    def test_supersede_terminal_immutable_leaves_no_trace(self):
        machine, control, reward = self.clawback_pair()
        self.reject(
            "TERMINAL_IMMUTABLE",
            lambda: self.supersede(machine, reward, idem="sup-again"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_reward(side)
        self.assert_same_as(machine, control)

    def test_supersede_rule_version_unchanged_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "RULE_VERSION_UNCHANGED",
            lambda: self.supersede(machine, reward, idem="sup-bad", rule_version="rule-v1"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.supersede(machine, reward), self.supersede(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_supersede_approval_record_reused_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        # approval-1 was consumed by the submit that opened the payout.
        self.reject(
            "APPROVAL_RECORD_REUSED",
            lambda: self.supersede(
                machine, reward, idem="sup-bad", approval_ref=human_approval()
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.supersede(machine, reward), self.supersede(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_supersede_ai_approval_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "AI_APPROVAL_REJECTED",
            lambda: self.supersede(
                machine,
                reward,
                idem="sup-bad",
                approval_ref={**human_approval("approval-ai"), "actor_type": "AI"},
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.supersede(machine, reward), self.supersede(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_supersede_approval_fields_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        bad = {**human_approval("approval-9"), "unexpected": "field"}
        self.reject(
            "APPROVAL_FIELDS",
            lambda: self.supersede(machine, reward, idem="sup-bad", approval_ref=bad),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.supersede(machine, reward), self.supersede(control, reward)
        )
        self.assert_same_as(machine, control)

    def test_supersede_invalid_rule_version_leaves_no_trace(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "INVALID_RULE_VERSION",
            lambda: self.supersede(machine, reward, idem="sup-bad", rule_version=""),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.supersede(machine, reward), self.supersede(control, reward)
        )
        self.assert_same_as(machine, control)

    # --- reject_external -------------------------------------------------------------

    def test_reject_external_journals_nothing(self):
        machine, control, reward = self.issued_pair()
        self.reject(
            "EXTERNAL_EXECUTION_UNSUPPORTED",
            lambda: machine.reject_external("chain-submit"),
        )
        self.assertEqual(
            codes(lambda: machine.reject_external(" ")), "INVALID_ID"
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.refund(side, reward)
        self.assert_same_as(machine, control)

    # --- idempotency boundaries ---------------------------------------------------------

    def test_idempotency_conflict_leaves_no_trace(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "IDEMPOTENCY_CONFLICT",
            lambda: self.observe(machine, amount=AMOUNT + 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.hold(machine, reward), self.hold(control, reward))
        self.assert_same_as(machine, control)

    def test_unfingerprintable_rejection_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "INVALID_AMOUNT",
            lambda: self.observe(machine, amount=object()),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.observe(machine), self.observe(control))
        self.assert_same_as(machine, control)

    # --- restore boundary (classmethod; no live machine touched) -------------------------

    def test_restore_invalid_journal_variants(self):
        self.assertEqual(
            codes(
                lambda: RewardMachine.restore(
                    {"op": "observe"}, opening_balances=self.opening
                )
            ),
            "INVALID_JOURNAL",
        )
        self.assertEqual(
            codes(
                lambda: RewardMachine.restore(
                    [{"op": "hold"}], opening_balances=self.opening
                )
            ),
            "INVALID_JOURNAL",
        )
        self.assertEqual(
            codes(
                lambda: RewardMachine.restore(
                    [
                        {
                            "op": "bogus",
                            "idempotency_key": "k",
                            "reward_id": "r",
                            "body": {},
                        }
                    ],
                    opening_balances=self.opening,
                )
            ),
            "INVALID_JOURNAL",
        )

    # --- non-canonical boundary pins ------------------------------------------------------

    def test_restore_forgets_stored_rejections(self):
        machine, control, reward = self.observed_pair()
        self.reject(
            "INVALID_AMOUNT",
            lambda: self.observe(
                machine,
                reward_key(source_op_id="op-bad"),
                idem="obs-bad",
                amount=0,
            ),
        )
        self.assert_same_as(machine, control)
        restored = RewardMachine.restore(
            machine.export_journal(), opening_balances=self.opening
        )
        # The stored rejection is not journaled. On the live machine the same
        # key under different canonical arguments conflicts; on the restored
        # machine the key is free and the command re-executes to acceptance.
        self.assertEqual(
            codes(
                lambda: self.observe(
                    machine, reward_key(source_op_id="op-bad"), idem="obs-bad"
                )
            ),
            "IDEMPOTENCY_CONFLICT",
        )
        accepted = self.observe(
            restored, reward_key(source_op_id="op-bad"), idem="obs-bad"
        )
        self.assertFalse(accepted["duplicate"])

    def test_submit_resend_does_not_consume_the_approval_record(self):
        machine, control, reward = self.unknown_pair()
        # Two resends carrying the same approval record both succeed on both
        # machines: the resend path never adds record_id to _approval_ids.
        # The first submit path does add it, so this is a boundary
        # characterization, not a contract assertion.
        for index in (1, 2):
            for side in (machine, control):
                resent = self.submit(
                    side,
                    reward,
                    idem="resend-%s" % index,
                    approval_ref=human_approval("approval-9"),
                    execution_permit={
                        "fence_ref": "fence-slot",
                        "signed_bytes_digest": DIGEST,
                    },
                )
            self.assertEqual(resent["reward"]["resend_count"], index)
        self.assert_same_as(machine, control)

    # --- late-failure seam: RewardMachine._invariant (class B characterizations) -----------

    def test_fault_observe_late_rejection_leaves_unapplied_mutation(self):
        machine, control = self.fresh(), self.fresh()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.observe(machine)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        # The unjournaled reward still occupies the derived id.
        self.assertEqual(
            codes(lambda: self.observe(machine, idem="obs-2")),
            "REWARD_ALREADY_OBSERVED",
        )
        self.assertEqual(
            self.observe(control, reward_key(source_op_id="op-2"), idem="obs-2")[
                "reward"
            ]["phase"],
            "OBSERVED",
        )

    def test_fault_hold_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.observed_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.hold(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        self.assertEqual(
            codes(lambda: self.hold(machine, reward, idem="hold-2")),
            "ILLEGAL_TRANSITION",
        )
        self.assertEqual(
            self.hold(control, reward, idem="hold-2")["reward"]["phase"], "HELD"
        )

    def test_fault_mark_eligible_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.held_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.eligible(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        self.assertEqual(
            codes(lambda: self.eligible(machine, reward, idem="elig-2")),
            "ILLEGAL_TRANSITION",
        )
        self.assertEqual(
            self.eligible(control, reward, idem="elig-2")["reward"]["phase"],
            "ELIGIBLE",
        )

    def test_fault_submit_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.eligible_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.submit(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        # The approval record was consumed by the unjournaled mutation.
        second = self.second_reward(machine)
        second_control = self.second_reward(control)
        self.assertEqual(second, second_control)
        self.assertEqual(
            codes(
                lambda: self.submit(machine, second, idem="sub-2")
            ),
            "APPROVAL_RECORD_REUSED",
        )
        self.assertEqual(
            self.submit(control, second_control, idem="sub-2")["reward"]["phase"],
            "ISSUING",
        )

    def test_fault_submit_resend_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.unknown_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.resend(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        # resend_count moved without a journal entry.
        self.assertEqual(machine.view(reward)["resend_count"], 1)
        self.assertEqual(control.view(reward)["resend_count"], 0)
        resent_machine = self.resend(machine, reward, idem="resend-2")
        resent_control = self.resend(control, reward, idem="resend-2")
        self.assertNotEqual(
            resent_machine["reward"]["resend_count"],
            resent_control["reward"]["resend_count"],
        )

    def test_fault_observe_transfer_effects_late_rejection_leaves_unapplied_mutation(
        self,
    ):
        machine, control, reward = self.issuing_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.effects(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        # The pool spend and the payout effect are unjournaled.
        self.assertNotEqual(
            machine.pool_view()["balances"], control.pool_view()["balances"]
        )
        self.assertEqual(
            codes(lambda: self.effects(machine, reward, idem="fx-2")),
            "TERMINAL_IMMUTABLE",
        )
        self.assertEqual(
            self.effects(control, reward, idem="fx-2")["reward"]["phase"], "ISSUED"
        )

    def test_fault_reconcile_unknown_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.unknown_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.reconcile(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        self.assertEqual(
            codes(lambda: self.reconcile(machine, reward, idem="recon-2")),
            "TERMINAL_IMMUTABLE",
        )
        self.assertEqual(
            self.reconcile(control, reward, idem="recon-2")["reward"]["phase"],
            "ISSUED",
        )

    def test_fault_observe_source_cancel_late_rejection_leaves_unapplied_mutation(
        self,
    ):
        machine, control, reward = self.held_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.cancel(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        self.assertEqual(
            codes(lambda: self.cancel(machine, reward, idem="cancel-2")),
            "TERMINAL_IMMUTABLE",
        )
        self.assertEqual(
            self.cancel(control, reward, idem="cancel-2")["reward"]["phase"],
            "REVERSED",
        )

    def test_fault_observe_krw_refund_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.held_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.refund(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        self.assertEqual(
            codes(lambda: self.refund(machine, reward, idem="krw-2")),
            "KRW_EFFECT_ALREADY_NOTED",
        )
        self.assertEqual(
            self.refund(control, reward, idem="krw-2")["reward"]["krw_phase"],
            "KRW_REFUND_NOTED",
        )

    def test_fault_supersede_late_rejection_leaves_unapplied_mutation(self):
        machine, control, reward = self.issued_pair()
        with self.fault():
            self.assertEqual(
                codes(lambda: self.supersede(machine, reward)), "MOCK_INVARIANT"
            )
        self.assert_unapplied_mutation(machine, control)
        self.assertEqual(
            codes(lambda: self.supersede(machine, reward, idem="sup-2")),
            "ILLEGAL_TRANSITION",
        )
        self.assertEqual(
            self.supersede(control, reward, idem="sup-2")["reward"]["phase"],
            "ELIGIBLE",
        )

    # --- late-failure seam: PoolLedger._conserve on the spend path --------------------------

    def test_fault_pool_observe_transfer_effects_spend_leaves_unapplied_mutation(self):
        machine, control, reward = self.issuing_pair()
        with self.pool_fault():
            self.assertEqual(
                codes(lambda: self.effects(machine, reward)), "MOCK_INVARIANT"
            )
        # The pool balance moved and the spend was recorded; the reward did
        # not move and nothing was journaled.
        self.assertEqual(machine.export_journal(), control.export_journal())
        self.assertNotEqual(machine.canonical_state(), control.canonical_state())
        self.assertEqual(
            machine.view(reward)["phase"], control.view(reward)["phase"]
        )
        self.assertNotEqual(
            machine.pool_view()["balances"], control.pool_view()["balances"]
        )
        # The unjournaled spend is repeatable: a later FAILED outcome still
        # lands, while the restored machine replays without the first spend.
        self.assertEqual(
            self.effects(machine, reward, idem="fx-2", outcome="FAILED"),
            self.effects(control, reward, idem="fx-2", outcome="FAILED"),
        )
        self.assertNotEqual(machine.canonical_state(), control.canonical_state())

    def test_fault_pool_reconcile_unknown_spend_leaves_unapplied_mutation(self):
        machine, control, reward = self.unknown_pair()
        with self.pool_fault():
            self.assertEqual(
                codes(lambda: self.reconcile(machine, reward)), "MOCK_INVARIANT"
            )
        self.assertEqual(machine.export_journal(), control.export_journal())
        self.assertNotEqual(machine.canonical_state(), control.canonical_state())
        self.assertEqual(
            machine.view(reward)["phase"], control.view(reward)["phase"]
        )
        self.assertNotEqual(
            machine.pool_view()["balances"], control.pool_view()["balances"]
        )
        self.assertEqual(
            self.reconcile(machine, reward, idem="recon-2", resolution="FAILED"),
            self.reconcile(control, reward, idem="recon-2", resolution="FAILED"),
        )
        self.assertNotEqual(machine.canonical_state(), control.canonical_state())


if __name__ == "__main__":
    unittest.main()
