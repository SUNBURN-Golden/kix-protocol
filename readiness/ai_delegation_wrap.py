"""Local journal wrap around the in-memory AI delegation mock.

The mock stays the semantic source. This wrap records an explicit open of the
caller-supplied registry and later public calls whose state digest changed.
Restart replays those entries through the same public methods. It does not
enable execution, flip durable, or treat the file as a grant ledger.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from readiness.codec import CodecError, canonical_json

ROOT = Path(__file__).resolve().parents[1]
_DELEGATION = str(ROOT / 'reference' / 'ai_delegation')
if _DELEGATION not in sys.path:
    sys.path.insert(0, _DELEGATION)

from ai_delegation_mock import AiDelegationError, AiDelegationMock  # noqa: E402

_UNOPENED = hashlib.sha256(b'{"machine":"ai_delegation","opened":false}').hexdigest()
_CALLS = ('issue_grant', 'revoke_grant', 'decide_proposal', 'call_tool')


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


class AiDelegationWrap:
    """Public restore target for readiness journals. Not a protocol command."""

    def __init__(self):
        self._inner = None
        self._journal = []

    def open_registry(self, humans, agents):
        if self._inner is not None:
            raise WrapError('ALREADY_OPEN')
        inner = AiDelegationMock(humans, agents)
        entry = _entry('open_registry', {'humans': humans, 'agents': agents})
        self._inner = inner
        self._journal.append(entry)
        return {'opened': True, 'durable': False, 'execution_enabled': False}

    def issue_grant(self, actor, grant_id, agent_id, authority, scope, limits, period):
        return self._call('issue_grant', {
            'actor': actor,
            'grant_id': grant_id,
            'agent_id': agent_id,
            'authority': authority,
            'scope': scope,
            'limits': limits,
            'period': period,
        })

    def revoke_grant(self, actor, grant_id, reason):
        return self._call('revoke_grant', {
            'actor': actor,
            'grant_id': grant_id,
            'reason': reason,
        })

    def decide_proposal(self, actor, proposal_id, decision, now):
        return self._call('decide_proposal', {
            'actor': actor,
            'proposal_id': proposal_id,
            'decision': decision,
            'now': now,
        })

    def call_tool(self, actor, grant_id, tool, args, now):
        return self._call('call_tool', {
            'actor': actor,
            'grant_id': grant_id,
            'tool': tool,
            'args': args,
            'now': now,
        })

    def attempt_execution(self, actor, proposal_id):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        self._inner.attempt_execution(actor, proposal_id)

    def view_grant(self, grant_id):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        return self._inner.view_grant(grant_id)

    def view_proposal(self, proposal_id):
        if self._inner is None:
            raise WrapError('NOT_OPEN')
        return self._inner.view_proposal(proposal_id)

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
                if entry['op'] == 'open_registry':
                    machine.open_registry(fields['humans'], fields['agents'])
                elif entry['op'] in _CALLS:
                    getattr(machine, entry['op'])(**fields)
                else:
                    raise WrapError('RECOVERY_DIVERGENCE')
            except (AiDelegationError, TypeError, WrapError) as exc:
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
