"""Source-informed integration evidence using real local FSMs, no external IO."""

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from example_settlement_reward import SettlementMachine, run_example
from reward_fsm import HELD, OBSERVED, RewardMachine
from settlement_reward_adapter import SettlementRewardAdapter, SettlementRewardBindingError
from tl4_support import codes, opening, reward_key
from token_reward_model import ALWAYS_FALSE_FLAGS, SOURCE_FINALITY_FLAGS, reward_id
from mock_settlement import SettlementError


def prepare_settlement(machine, settlement_id="settlement-1", phase="COMMITTED"):
    """Independent synthetic fixture, not a product fee or settlement policy."""
    machine.initiate(
        settlement_id,
        idempotency_key=settlement_id + "-init",
        trade_id=settlement_id + "-trade",
        gross=100_000,
        debtor_role="fixture-merchant",
        policy={"kind": "PRIMARY_FEE_BPS", "fee_bps": 500,
                "residual_payee": "organizer", "fee_payee": "platform"},
    )
    if phase == "INITIATED":
        return
    if phase in {"FAILED", "CANCELLED"}:
        method = machine.fail if phase == "FAILED" else machine.cancel
        method(settlement_id, idempotency_key=settlement_id + "-terminal", reason="fixture")
        return
    machine.authorize(settlement_id, idempotency_key=settlement_id + "-auth")
    if phase == "AUTHORIZED":
        return
    machine.capture(settlement_id, idempotency_key=settlement_id + "-capture")
    if phase == "CAPTURED":
        return
    commit_settlement(machine, settlement_id)


def commit_settlement(machine, settlement_id="settlement-1"):
    machine.commit(
        settlement_id, idempotency_key=settlement_id + "-commit",
        movement_id=settlement_id + "-movement", gross=100_000,
        amount=97_000, fee=3_000, tax=0, held=0, adjustment=0,
    )


class SettlementRewardAdapterTests(unittest.TestCase):
    def setUp(self):
        self.settlements = SettlementMachine()
        self.rewards = RewardMachine(opening(
            CUSTOMER_DEPOSIT=11, ORGANIZER_SETTLEMENT=23, REFUND_RESERVE=31,
            PROTOCOL_REVENUE=500, TOKEN_TREASURY_REWARD=500,
        ))
        self.key = reward_key(source_op_id="source-op-1")
        self.bindings = {"source-op-1": "settlement-1"}
        self.adapter = SettlementRewardAdapter(
            self.settlements, self.rewards, bindings=self.bindings,
        )

    def observe(self, **overrides):
        args = {"idempotency_key": "observe-1", "rule_version": "synthetic-rule-v1", "amount": 7}
        args.update(overrides)
        return self.read_only(lambda: self.adapter.observe(self.key, **args))

    def read_only(self, call):
        state = self.settlements.canonical_state()
        journal = self.settlements.export_journal()
        pools = self.rewards.pool_view()
        try:
            return call()
        finally:
            self.assertEqual(self.settlements.canonical_state(), state)
            self.assertEqual(self.settlements.export_journal(), journal)
            self.assertEqual(self.rewards.pool_view(), pools)

    def test_committed_bound_source_is_observed(self):
        prepare_settlement(self.settlements)
        views, responses = [], []
        real_view, real_observe = self.settlements.view, self.rewards.observe

        def read(*args, **kwargs):
            views.append(real_view(*args, **kwargs))
            return views[-1]

        def dispatch(*args, **kwargs):
            self.assertIs(kwargs["source_view"], views[-1])
            responses.append(real_observe(*args, **kwargs))
            return responses[-1]

        with patch.object(self.settlements, "view", side_effect=read) as view_call:
            with patch.object(self.rewards, "observe", side_effect=dispatch) as reward_call:
                response = self.observe()
        view_call.assert_called_once_with("settlement-1")
        self.assertEqual(reward_call.call_count, 1)
        self.assertIs(response, responses[0])
        reward = response["reward"]
        self.assertEqual(reward["reward_id"], reward_id(**self.key))
        self.assertEqual(reward["source_view"], real_view("settlement-1"))
        self.assertEqual(reward["source_kind"], "SETTLEMENT")
        self.assertEqual(reward["phase"], OBSERVED)
        self.assertEqual(reward["amount"], 7)
        self.assertEqual(reward["payout_effect_count"], 0)
        self.assertIsNone(reward["token_effect_id"])
        self.assertIsNone(reward["approval_ref"])
        self.assertEqual([entry["op"] for entry in self.rewards.export_journal()], ["observe"])

    def test_missing_binding_and_unknown_settlement_create_no_reward(self):
        initial = self.rewards.canonical_state()
        unbound = SettlementRewardAdapter(self.settlements, self.rewards, bindings={})
        with patch.object(self.rewards, "observe", wraps=self.rewards.observe) as dispatch:
            with self.assertRaises(SettlementRewardBindingError) as missing:
                self.read_only(lambda: unbound.observe(
                    self.key, idempotency_key="observe-1", rule_version="synthetic-rule-v1", amount=7,
                ))
            self.assertEqual(missing.exception.code, "BINDING_REQUIRED")
            with self.assertRaises(SettlementError) as unknown:
                self.observe()
            self.assertEqual(unknown.exception.code, "UNKNOWN_SETTLEMENT")
            dispatch.assert_not_called()
        self.assertEqual(self.rewards.reward_ids(), [])
        self.assertEqual(self.rewards.export_journal(), [])
        self.assertEqual(self.rewards.canonical_state(), initial)
        # Neither lookup failure consumed the observation key.
        prepare_settlement(self.settlements)
        self.assertFalse(self.observe()["duplicate"])

    def test_non_committed_sources_create_no_reward(self):
        for phase in ("INITIATED", "AUTHORIZED", "CAPTURED", "FAILED", "CANCELLED"):
            with self.subTest(phase=phase):
                settlement_id = "settlement-" + phase
                prepare_settlement(self.settlements, settlement_id, phase)
                adapter = SettlementRewardAdapter(
                    self.settlements, self.rewards, bindings={"source-op-1": settlement_id},
                )
                before = self.rewards.canonical_state()
                self.assertEqual(codes(lambda: self.read_only(lambda: adapter.observe(
                    self.key, idempotency_key="observe-" + phase,
                    rule_version="synthetic-rule-v1", amount=7,
                ))), "SOURCE_NOT_COMMITTED")
                self.assertEqual(self.rewards.canonical_state(), before)
                self.assertEqual(self.rewards.reward_ids(), [])
                self.assertEqual(self.rewards.export_journal(), [])

    def test_source_selection_is_configuration_only(self):
        prepare_settlement(self.settlements)
        prepare_settlement(self.settlements, "settlement-2")
        self.bindings["source-op-1"] = "settlement-2"
        self.bindings["settlement-2"] = "settlement-2"
        for source in ("settlement-2", "settlement-1-trade", "settlement-1-init"):
            with self.subTest(source=source), self.assertRaises(SettlementRewardBindingError):
                self.read_only(lambda: self.adapter.observe(
                    reward_key(source_op_id=source), idempotency_key="unbound",
                    rule_version="synthetic-rule-v1", amount=7,
                ))
        for name, value in {
            "settlement_id": "settlement-2",
            "source_view": self.settlements.view("settlement-2"),
            "source_kind": "RESALE",
            "settlements": self.settlements,
            "rewards": self.rewards,
        }.items():
            with self.subTest(keyword=name), self.assertRaises(TypeError):
                self.observe(**{name: value})
        self.assertEqual(self.rewards.reward_ids(), [])
        self.assertEqual(self.observe()["reward"]["source_view"]["settlement_id"], "settlement-1")

    def test_binding_identifiers_and_reward_key_reuse_existing_validation(self):
        for bindings in ({"": "settlement-1"}, {"source-op-1": " bad "}, {1: "settlement-1"}):
            with self.subTest(bindings=bindings):
                self.assertEqual(codes(lambda: SettlementRewardAdapter(
                    self.settlements, self.rewards, bindings=bindings,
                )), "INVALID_ID")
        with self.assertRaises(TypeError):
            SettlementRewardAdapter(self.settlements, self.rewards, bindings=[])
        with patch.object(self.settlements, "view", wraps=self.settlements.view) as lookup:
            for key, code in (({}, "REWARD_KEY_FIELDS"),
                              ({**self.key, "source_op_id": " "}, "INVALID_ID")):
                self.assertEqual(codes(lambda: self.adapter.observe(
                    key, idempotency_key="invalid", rule_version="synthetic-rule-v1", amount=7,
                )), code)
            lookup.assert_not_called()

    def test_reward_inputs_are_validated_by_reward_machine(self):
        prepare_settlement(self.settlements)
        for name, value, code in (("amount", True, "INVALID_AMOUNT"),
                                  ("rule_version", " ", "INVALID_RULE_VERSION"),
                                  ("idempotency_key", "", "INVALID_ID")):
            with self.subTest(name=name):
                before = self.rewards.canonical_state()
                args = {"idempotency_key": "invalid-" + name, name: value}
                self.assertEqual(codes(lambda: self.observe(**args)), code)
                self.assertEqual(self.rewards.canonical_state(), before)

    def test_unchanged_source_replays_first_result(self):
        prepare_settlement(self.settlements)
        first = self.observe()
        expected = {**first, "duplicate": True, "applied": None}
        before = self.rewards.canonical_state()
        self.assertEqual(self.observe(), expected)
        self.assertEqual(self.rewards.canonical_state(), before)
        reward = first["reward"]["reward_id"]
        # Explicit separate machine transition; never driven by the adapter.
        self.rewards.hold(reward, idempotency_key="hold-1")
        before = self.rewards.canonical_state()
        self.assertEqual(self.observe(), expected)
        self.assertEqual(self.rewards.canonical_state(), before)
        self.assertEqual(self.rewards.view(reward)["phase"], HELD)
        self.assertEqual(expected["reward"]["phase"], OBSERVED)

    def test_changed_live_snapshot_conflicts(self):
        prepare_settlement(self.settlements)
        first = self.observe()
        self.settlements.distribute(
            "settlement-1", idempotency_key="explicit-distribution", order=["organizer", "platform"],
        )
        self.assertNotEqual(self.settlements.view("settlement-1"), first["reward"]["source_view"])
        before = self.rewards.canonical_state()
        self.assertEqual(codes(self.observe), "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.rewards.canonical_state(), before)
        self.assertEqual(self.rewards.view(first["reward"]["reward_id"]), first["reward"])

    def test_rule_version_cannot_replace_reward(self):
        prepare_settlement(self.settlements)
        first = self.observe()
        before = self.rewards.canonical_state()
        for kwargs, code in (
            ({"rule_version": "synthetic-rule-v2"}, "IDEMPOTENCY_CONFLICT"),
            ({"rule_version": "synthetic-rule-v2", "idempotency_key": "explicit-other-key"},
             "RULE_VERSION_REPAY_FORBIDDEN"),
            ({"idempotency_key": "explicit-same-rule-key"}, "REWARD_ALREADY_OBSERVED"),
        ):
            with self.subTest(code=code):
                self.assertEqual(codes(lambda: self.observe(**kwargs)), code)
                self.assertEqual(self.rewards.canonical_state(), before)
        self.assertEqual(self.rewards.reward_ids(), [first["reward"]["reward_id"]])

    def test_rejected_first_result_survives_source_advancement(self):
        prepare_settlement(self.settlements, phase="CAPTURED")
        before = self.rewards.canonical_state()
        for _ in range(2):  # Explicit test calls; adapter has no retry loop.
            self.assertEqual(codes(self.observe), "SOURCE_NOT_COMMITTED")
            self.assertEqual(self.rewards.canonical_state(), before)
        commit_settlement(self.settlements)
        self.assertEqual(codes(self.observe), "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.rewards.canonical_state(), before)
        self.assertEqual(self.rewards.reward_ids(), [])

    def test_offline_example_output_and_flags(self):
        script = Path(__file__).with_name("example_settlement_reward.py")
        output = subprocess.check_output([sys.executable, str(script)], text=True)
        example = json.loads(output)
        self.assertEqual(example, run_example())
        self.assertIs(example["synthetic_fixture_only"], True)
        self.assertEqual(example["bindings"], {"source-op-1": "settlement-1"})
        source, response = example["settlement_view"], example["reward_response"]
        reward = response["reward"]
        self.assertEqual(source["provenance"], "MOCK_SETTLEMENT_ONLY")
        self.assertEqual(reward["source_view"], source)
        self.assertEqual(reward["phase"], OBSERVED)
        self.assertEqual(reward["payout_effect_count"], 0)
        self.assertIs(reward["non_transferable_until_chargeback_end"], True)
        self.assertEqual(example["pool_view"], RewardMachine(opening()).pool_view())
        for view in (response, reward):
            self.assertEqual(view["provenance"], "MOCK_TOKEN_REWARD_ONLY")
            self.assertEqual(view["unit"], "POINT_F4")
            for name in ALWAYS_FALSE_FLAGS:
                self.assertIs(view[name], False)
        self.assertEqual(response["lifecycle"], "IN_MEMORY_FSM")
        self.assertEqual(response["external_execution"], "UNSUPPORTED")
        for name in SOURCE_FINALITY_FLAGS + ("provider_authorization_executed", "admission_granted", "right_cancelled"):
            self.assertIs(source[name], False)

    def test_sibling_import_origins_and_path_cleanup(self):
        here = Path(__file__).resolve().parent
        sibling = here.parent / "settlement_f01_f03"
        for name in ("settlement_fsm", "mock_settlement"):
            self.assertEqual(Path(sys.modules[name].__file__).resolve().parent, sibling)
        for name in ("reward_fsm", "token_reward_model", "settlement_reward_adapter"):
            self.assertEqual(Path(sys.modules[name].__file__).resolve().parent, here)
        self.assertNotIn(str(sibling), sys.path)


if __name__ == "__main__":
    unittest.main()
