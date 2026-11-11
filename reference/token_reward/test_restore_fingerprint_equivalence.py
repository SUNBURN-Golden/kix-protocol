"""Source-informed offline reward fingerprint characterizations (B).

No contract defines normalized-argument retry responses after restore. TK-7
payout bounds are checked separately as class A predicates in each probe.
Synthetic amounts, balances and periods; owner policy stays UNDETERMINED.
"""

from copy import deepcopy
import unittest

from reward_fsm import RewardMachine
from token_reward_model import TokenRewardError, reward_id
from tl4_support import funded_opening, committed_view, reward_key, human_approval, hex_digest

RID = reward_id(**reward_key())
DUPLICATE = ("ok", True, None)
CONFLICT = ("error", "IDEMPOTENCY_CONFLICT")


def outcome(fn):
    try:
        result = fn()
    except TokenRewardError as error:
        return ("error", error.code)
    return ("ok", result["duplicate"], result["applied"])


def invoke(machine, op, body, key="probe"):
    return getattr(machine, op)(RID, idempotency_key=key, **deepcopy(body))


def eligible_body():
    return dict(window_closed=True, source_view=committed_view(), abuse_clear=True)


def approval(prior=None):
    return dict(human_approval(), prior_record=prior)


def submit_body():
    return dict(approval_ref=approval(), signed_bytes_digest=hex_digest(1), spend_pool="PROTOCOL_REVENUE")


def pay(machine):
    machine.observe_transfer_effects(RID, idempotency_key="effects",
                                     effects_digest=hex_digest(2), outcome="SUCCESS")


def fixture(stage):
    machine = RewardMachine(funded_opening())
    machine.observe(reward_key(), idempotency_key="observe", source_view=committed_view(),
                    rule_version="v1", amount=4, source_kind="SETTLEMENT")
    machine.hold(RID, idempotency_key="hold")
    if stage != "held":
        invoke(machine, "mark_eligible", eligible_body(), "eligible")
    if stage == "issued":
        invoke(machine, "submit", submit_body(), "submit")
        pay(machine)
    return machine


def assert_payout_bounds(test, machine):
    """Class A: TOKEN_ROLE_AND_SUPPLY TK-7 / TL_PREDICATE_EVIDENCE_MAP TK-7.

    Each fixture completes exactly one first payout, never a successor payout.
    Replaying an earlier eligibility/submit/supersede must not pay again.
    """
    test.assertEqual(machine.view(RID)["payout_effect_count"], 1)
    pools = machine.pool_view()
    test.assertEqual(len(pools["spends"]), 1)
    test.assertEqual(pools["spends"][0]["amount"], 4)
    test.assertEqual(pools["balances"]["PROTOCOL_REVENUE"],
                     funded_opening()["PROTOCOL_REVENUE"] - 4)


def probe(test, stage, op, first, retries):
    machine = fixture(stage)
    test.assertEqual(outcome(lambda: invoke(machine, op, first)), ("ok", False, op))
    # Retry a historical success after its first payout, so TK-7 is non-vacuous.
    if op == "mark_eligible":
        invoke(machine, "submit", submit_body(), "submit")
    if op != "supersede":
        pay(machine)
    assert_payout_bounds(test, machine)
    state, journal, pools = machine.canonical_state(), machine.export_journal(), machine.pool_view()
    for retry, before, after in retries:
        with test.subTest(op=op, first=first, retry=retry):
            test.assertEqual(outcome(lambda: invoke(machine, op, retry)), before)
            test.assertEqual(machine.canonical_state(), state)
            test.assertEqual(machine.export_journal(), journal)
            test.assertEqual(machine.pool_view(), pools)
            assert_payout_bounds(test, machine)
            restored = RewardMachine.restore(deepcopy(journal), opening_balances=funded_opening())
            test.assertEqual(restored.canonical_state(), state)
            test.assertEqual(restored.state_digest(), machine.state_digest())
            test.assertEqual(outcome(lambda: invoke(restored, op, retry)), after)
            test.assertEqual(restored.canonical_state(), state)
            test.assertEqual(restored.export_journal(), journal)
            test.assertEqual(restored.pool_view(), pools)
            assert_payout_bounds(test, restored)


class RewardRestoreFingerprintCharacterizationTests(unittest.TestCase):
    """Retry response semantics contract undefined (B); probe also checks TK-7 (A)."""

    def check_approval(self, op):
        base = submit_body() if op == "submit" else dict(rule_version="v2")
        raw_approvals = [human_approval(), approval(), approval("approval-0")]
        if op == "supersede":
            for item in raw_approvals:
                item.update(record_id="approval-2", generation=2)
        variants = [dict(base, approval_ref=item) for item in raw_approvals]
        for index, first in enumerate(variants):
            # Restore uses the normalized journal body: missing prior_record is None.
            restored_index = 1 if index == 0 else index
            retries = [(retry, DUPLICATE if n == index else CONFLICT,
                        DUPLICATE if n == restored_index else CONFLICT)
                       for n, retry in enumerate(variants)]
            probe(self, "eligible" if op == "submit" else "issued", op, first, retries)

    def test_submit_approval_prior_record(self):
        self.check_approval("submit")

    def test_supersede_approval_prior_record(self):
        self.check_approval("supersede")

    def test_mark_eligible_optional_fields(self):
        for field in ("abuse_kind", "recipient_cap", "program_cap"):
            variants = [eligible_body(), dict(eligible_body(), **{field: None})]
            for first in variants:
                probe(self, "held", "mark_eligible", first,
                      [(retry, DUPLICATE, DUPLICATE) for retry in variants])

    def test_submit_optional_fields(self):
        for field in ("budget_ceiling", "execution_permit"):
            variants = [submit_body(), dict(submit_body(), **{field: None})]
            for first in variants:
                probe(self, "eligible", "submit", first,
                      [(retry, DUPLICATE, DUPLICATE) for retry in variants])


if __name__ == "__main__":
    unittest.main()
