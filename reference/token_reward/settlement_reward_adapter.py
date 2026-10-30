"""Internal, offline F4 observation from an explicitly bound local settlement.

Bindings are trusted synthetic fixture configuration, not authenticated commerce
provenance. No identity equivalence is inferred. Reads are in-process snapshots,
not atomic cross-machine transactions, durable records or finality evidence.
RewardMachine owns validation, arithmetic, identity and first-result semantics.
This adapter never retries, replaces identities or advances reward eligibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from reward_fsm import RewardMachine, _reward_key
from token_reward_model import _ident

if TYPE_CHECKING:
    from settlement_fsm import SettlementMachine


class SettlementRewardBindingError(Exception):
    """Adapter-local diagnostic; not a protocol catalogue error."""

    def __init__(self) -> None:
        super().__init__("BINDING_REQUIRED")
        self.code = "BINDING_REQUIRED"


class SettlementRewardAdapter:
    def __init__(
        self,
        settlements: SettlementMachine,
        rewards: RewardMachine,
        *,
        bindings: Mapping[str, str],
    ) -> None:
        if not isinstance(bindings, Mapping):
            raise TypeError("bindings must be a source operation ID to settlement ID mapping")
        self._bindings = MappingProxyType(
            {_ident(source_op_id): _ident(settlement_id)
             for source_op_id, settlement_id in bindings.items()}
        )
        self._settlements = settlements
        self._rewards = rewards

    def observe(
        self,
        reward_key: object,
        *,
        idempotency_key: object,
        rule_version: object,
        amount: object,
    ) -> dict:
        parsed = _reward_key(reward_key)
        source_op_id = parsed["source_op_id"]
        if source_op_id not in self._bindings:
            raise SettlementRewardBindingError()
        source_view = self._settlements.view(self._bindings[source_op_id])
        return self._rewards.observe(
            reward_key,
            idempotency_key=idempotency_key,
            source_view=source_view,
            source_kind="SETTLEMENT",
            rule_version=rule_version,
            amount=amount,
        )
