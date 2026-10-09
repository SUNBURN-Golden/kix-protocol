"""Shared fixtures for the TL-4 author-side harness.

unittest discover collects test*.py only, so this module is not a test.
Labels and helpers are harness-local. They are not protocol commands.
Numbers here are synthetic fixtures, not product policy values.
The author of this harness is the builder. A run is not an independent PASS.
"""

from __future__ import annotations

import random

from token_reward_model import TokenRewardError

# TOKEN_ROLE_AND_SUPPLY.md §6. Five pools. Not copied from an oracle result.
CONTRACT_POOLS = (
    "CUSTOMER_DEPOSIT",
    "ORGANIZER_SETTLEMENT",
    "REFUND_RESERVE",
    "PROTOCOL_REVENUE",
    "TOKEN_TREASURY_REWARD",
)
OBLIGATION_POOLS = frozenset(
    {"CUSTOMER_DEPOSIT", "ORGANIZER_SETTLEMENT", "REFUND_RESERVE"}
)
SPENDABLE_POOLS = frozenset({"PROTOCOL_REVENUE", "TOKEN_TREASURY_REWARD"})

SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)
POOL_SCRIPT_STEPS = 24
FSM_STEPS = 36
SUPPLY_STREAM_LENGTH = 8

# Fixed corpus. No clock and no os.urandom.
JUNK = (
    None,
    True,
    False,
    0,
    -1,
    1,
    10**12,
    10**12 + 1,
    1.5,
    float("nan"),
    float("inf"),
    "",
    " ",
    "x",
    "UNKNOWN",
    "AI",
    '"',
    ",",
    "a" * 100,
    "a" * 101,
    "한글",
    "a,b",
    [],
    {},
    (),
    set(),
    b"x",
    object(),
)


def rng(seed: int) -> random.Random:
    return random.Random(seed)


def codes(fn):
    try:
        fn()
    except TokenRewardError as error:
        return error.code
    raise AssertionError("expected TokenRewardError")


def opening(**overrides):
    """Synthetic opening balances. Not a policy value."""

    base = {pool: 0 for pool in CONTRACT_POOLS}
    base.update(overrides)
    return base


def funded_opening():
    """Spendable pools hold a synthetic fixture balance. Not a policy value."""

    balances = opening()
    balances["PROTOCOL_REVENUE"] = 500
    balances["TOKEN_TREASURY_REWARD"] = 500
    return balances


def committed_view():
    return {
        "phase": "COMMITTED",
        "currency": "KRW",
        "funds_executed": False,
        "bank_debit_observed": False,
        "legal_debtor_bound": False,  # not a claim; source-view field name
        "external_return_closed": False,  # not a claim; source-view field name
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
    """Structural slot. Names no approver. generation is not a quorum or a timelock."""

    return {
        "record_id": record_id,
        "generation": generation,
        "authority_id": "authority-slot",
        "actor_type": "HUMAN",
        "action": "point-payout",
        "scope_ref": "program-1",
        "evidence_refs": ["evidence-1"],
    }


def hex_digest(n: int) -> str:
    return f"{n:064x}"
