"""One fresh, synthetic, in-memory reward desk; no restoration or execution."""

from __future__ import annotations

from reward_fsm import RewardMachine


class RewardSession:
    """Forward explicit caller inputs to an unchanged RewardMachine.

    Optional None values have exactly the machine's existing meaning. This
    wrapper supplies no policy values, source facts, approvals or automation.
    """

    def __init__(self, opening_balances: object) -> None:
        self._machine = RewardMachine(opening_balances)

    def observe(self, reward_key: object, *, idempotency_key: object,
                source_view: object, rule_version: object, amount: object,
                source_kind: object) -> dict:
        return self._machine.observe(
            reward_key, idempotency_key=idempotency_key, source_view=source_view,
            rule_version=rule_version, amount=amount, source_kind=source_kind)

    def hold(self, reward_id_value: object, *, idempotency_key: object) -> dict:
        return self._machine.hold(reward_id_value, idempotency_key=idempotency_key)

    def mark_eligible(self, reward_id_value: object, *, idempotency_key: object,
                      window_closed: object, source_view: object, abuse_clear: object,
                      abuse_kind: object = None, recipient_cap: object = None,
                      program_cap: object = None) -> dict:
        return self._machine.mark_eligible(
            reward_id_value, idempotency_key=idempotency_key,
            window_closed=window_closed, source_view=source_view,
            abuse_clear=abuse_clear, abuse_kind=abuse_kind,
            recipient_cap=recipient_cap, program_cap=program_cap)

    def submit(self, reward_id_value: object, *, idempotency_key: object,
               approval_ref: object, signed_bytes_digest: object, spend_pool: object,
               budget_ceiling: object = None, execution_permit: object = None) -> dict:
        return self._machine.submit(
            reward_id_value, idempotency_key=idempotency_key,
            approval_ref=approval_ref, signed_bytes_digest=signed_bytes_digest,
            spend_pool=spend_pool, budget_ceiling=budget_ceiling,
            execution_permit=execution_permit)

    def observe_transfer_effects(self, reward_id_value: object, *, idempotency_key: object,
                                 effects_digest: object, outcome: object) -> dict:
        return self._machine.observe_transfer_effects(
            reward_id_value, idempotency_key=idempotency_key,
            effects_digest=effects_digest, outcome=outcome)

    def reconcile_unknown(self, reward_id_value: object, *, idempotency_key: object,
                          same_digest: object, resolution: object) -> dict:
        return self._machine.reconcile_unknown(
            reward_id_value, idempotency_key=idempotency_key,
            same_digest=same_digest, resolution=resolution)

    def observe_source_cancel(self, reward_id_value: object, *, idempotency_key: object,
                              source_view: object, reason: object) -> dict:
        return self._machine.observe_source_cancel(
            reward_id_value, idempotency_key=idempotency_key,
            source_view=source_view, reason=reason)

    def observe_krw_refund(self, reward_id_value: object, *, idempotency_key: object,
                           source_view: object, reason: object) -> dict:
        return self._machine.observe_krw_refund(
            reward_id_value, idempotency_key=idempotency_key,
            source_view=source_view, reason=reason)

    def supersede(self, reward_id_value: object, *, idempotency_key: object,
                  approval_ref: object, rule_version: object) -> dict:
        return self._machine.supersede(
            reward_id_value, idempotency_key=idempotency_key,
            approval_ref=approval_ref, rule_version=rule_version)

    def view(self, reward_id_value: object) -> dict:
        return self._machine.view(reward_id_value)

    def reward_ids(self) -> list:
        return self._machine.reward_ids()

    def pool_view(self) -> dict:
        return self._machine.pool_view()
