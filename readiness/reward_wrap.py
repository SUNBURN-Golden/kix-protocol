"""Local journal wrap around the in-memory token-reward FSM.

The FSM stays the semantic source. This wrap records an explicit open of the
caller-supplied opening balances and later public commands whose state digest
changed. Restart replays those entries through the same public methods. It
does not move funds, flip durable, or treat the file as a payout record.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from readiness.codec import CodecError, canonical_json

ROOT = Path(__file__).resolve().parents[1]
_TOKEN_REWARD = str(ROOT / 'reference' / 'token_reward')
if _TOKEN_REWARD not in sys.path:
    sys.path.insert(0, _TOKEN_REWARD)

from reward_fsm import RewardMachine  # noqa: E402
from token_reward_model import TokenRewardError  # noqa: E402

_UNOPENED = hashlib.sha256(b'{"machine":"reward","opened":false}').hexdigest()
_CALLS = (
    'observe', 'hold', 'mark_eligible', 'submit', 'observe_transfer_effects',
    'reconcile_unknown', 'observe_source_cancel', 'observe_krw_refund',
    'supersede',
)


class WrapError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _entry(op, fields):
    body = {'op': op}
    body.update(fields)
    try:
        return json.loads(canonical_json(body))
    except CodecError as exc:
        raise WrapError('JOURNAL_RECORD') from exc


class RewardWrap:
    """Public restore target for readiness journals. Not a protocol command."""

    def __init__(self):
        self._inner = None
        self._journal = []

    def open(self, opening_balances):
        if self._inner is not None:
            raise WrapError('ALREADY_OPEN')
        inner = RewardMachine(opening_balances)
        entry = _entry('open', {'opening_balances': opening_balances})
        self._inner = inner
        self._journal.append(entry)
        return {'opened': True, 'durable': False}

    def observe(self, reward_key, *, idempotency_key, source_view, rule_version,
                amount, source_kind):
        return self._call('observe', {
            'reward_key': reward_key,
            'idempotency_key': idempotency_key,
            'source_view': source_view,
            'rule_version': rule_version,
            'amount': amount,
            'source_kind': source_kind,
        })

    def hold(self, reward_id_value, *, idempotency_key):
        return self._call('hold', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
        })

    def mark_eligible(self, reward_id_value, *, idempotency_key, window_closed,
                      source_view, abuse_clear, abuse_kind=None,
                      recipient_cap=None, program_cap=None):
        return self._call('mark_eligible', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'window_closed': window_closed,
            'source_view': source_view,
            'abuse_clear': abuse_clear,
            'abuse_kind': abuse_kind,
            'recipient_cap': recipient_cap,
            'program_cap': program_cap,
        })

    def submit(self, reward_id_value, *, idempotency_key, approval_ref,
               signed_bytes_digest, spend_pool, budget_ceiling=None,
               execution_permit=None):
        return self._call('submit', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'approval_ref': approval_ref,
            'signed_bytes_digest': signed_bytes_digest,
            'spend_pool': spend_pool,
            'budget_ceiling': budget_ceiling,
            'execution_permit': execution_permit,
        })

    def observe_transfer_effects(self, reward_id_value, *, idempotency_key,
                                 effects_digest, outcome):
        return self._call('observe_transfer_effects', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'effects_digest': effects_digest,
            'outcome': outcome,
        })

    def reconcile_unknown(self, reward_id_value, *, idempotency_key,
                          same_digest, resolution):
        return self._call('reconcile_unknown', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'same_digest': same_digest,
            'resolution': resolution,
        })

    def observe_source_cancel(self, reward_id_value, *, idempotency_key,
                              source_view, reason):
        return self._call('observe_source_cancel', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'source_view': source_view,
            'reason': reason,
        })

    def observe_krw_refund(self, reward_id_value, *, idempotency_key,
                           source_view, reason):
        return self._call('observe_krw_refund', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'source_view': source_view,
            'reason': reason,
        })

    def supersede(self, reward_id_value, *, idempotency_key, approval_ref,
                  rule_version):
        return self._call('supersede', {
            'reward_id_value': reward_id_value,
            'idempotency_key': idempotency_key,
            'approval_ref': approval_ref,
            'rule_version': rule_version,
        })

    def reject_external(self, kind):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        self._inner.reject_external(kind)

    def view(self, reward_id_value):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        return self._inner.view(reward_id_value)

    def reward_ids(self):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        return self._inner.reward_ids()

    def pool_view(self):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        return self._inner.pool_view()

    def canonical_state(self):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        return self._inner.canonical_state()

    def state_digest(self):
        if self._inner is None:
            return _UNOPENED
        return self._inner.state_digest()

    def export_journal(self):
        try:
            return json.loads(canonical_json(self._journal))
        except CodecError as exc:
            raise WrapError('JOURNAL_RECORD') from exc

    @classmethod
    def restore(cls, journal):
        if not isinstance(journal, list):
            raise WrapError('RECOVERY_DIVERGENCE')
        machine = cls()
        for entry in journal:
            if not isinstance(entry, dict) or not isinstance(entry.get('op'), str):
                raise WrapError('RECOVERY_DIVERGENCE')
            fields = {key: value for key, value in entry.items() if key != 'op'}
            try:
                if entry['op'] == 'open':
                    machine.open(fields['opening_balances'])
                elif entry['op'] in _CALLS:
                    getattr(machine, entry['op'])(**fields)
                else:
                    raise WrapError('RECOVERY_DIVERGENCE')
            except (TokenRewardError, TypeError, KeyError, WrapError) as exc:
                raise WrapError('RECOVERY_DIVERGENCE') from exc
        if machine.export_journal() != journal:
            raise WrapError('RECOVERY_DIVERGENCE')
        return machine

    def _call(self, op, fields):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        encoded = _entry(op, fields)
        arguments = {key: value for key, value in encoded.items() if key != 'op'}
        before = self._inner.state_digest()
        result = getattr(self._inner, op)(**arguments)
        if self._inner.state_digest() != before:
            self._journal.append(encoded)
        return result
