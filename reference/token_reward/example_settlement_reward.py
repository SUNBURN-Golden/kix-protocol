"""Run with python3 reference/token_reward/example_settlement_reward.py.

Deterministic synthetic fixture only. No approval or chargeback window is chosen.
Product values remain UNDETERMINED — Astra; approver designation belongs to the
User; chargeback periods remain UNDETERMINED — payment provider.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

from reward_fsm import RewardMachine
from settlement_reward_adapter import SettlementRewardAdapter
from token_reward_model import POOLS

# Sibling reference suites are intentionally discovered on isolated paths.
_suite = str(Path(__file__).resolve().parents[1] / "settlement_f01_f03")
_prior_path = sys.path[:]
sys.path.insert(1, _suite)
try:
    from settlement_fsm import SettlementMachine
finally:
    sys.path[:] = _prior_path


def run_example() -> dict:
    settlements = SettlementMachine()
    settlements.initiate(
        "settlement-1",
        idempotency_key="fixture-init-1",
        trade_id="trade-1",
        gross=100_000,
        debtor_role="fixture-merchant",
        policy={
            "kind": "PRIMARY_FEE_BPS",
            "fee_bps": 500,
            "residual_payee": "organizer",
            "fee_payee": "platform",
        },
    )
    settlements.authorize("settlement-1", idempotency_key="fixture-auth-1")
    settlements.capture("settlement-1", idempotency_key="fixture-capture-1")
    settlements.commit(
        "settlement-1",
        idempotency_key="fixture-commit-1",
        movement_id="fixture-movement-1",
        gross=100_000,
        amount=97_000,
        fee=3_000,
        tax=0,
        held=0,
        adjustment=0,
    )
    bindings = {"source-op-1": "settlement-1"}
    rewards = RewardMachine({pool: 0 for pool in POOLS})
    adapter = SettlementRewardAdapter(settlements, rewards, bindings=bindings)
    response = adapter.observe(
        {
            "program": "synthetic-program",
            "source_op_id": "source-op-1",
            "recipient": "fixture-recipient",
            "kind": "participation",
        },
        idempotency_key="fixture-observe-1",
        rule_version="synthetic-rule-v1",
        amount=7,  # Explicit synthetic POINT_F4 input; not derived from KRW.
    )
    return {
        "synthetic_fixture_only": True,
        "bindings": bindings,
        "settlement_view": settlements.view("settlement-1"),
        "reward_response": response,
        "pool_view": rewards.pool_view(),
    }


if __name__ == "__main__":
    print(json.dumps(run_example(), sort_keys=True, indent=2, ensure_ascii=False))
