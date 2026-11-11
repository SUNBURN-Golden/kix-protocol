"""One fresh, sequential, synthetic, in-memory AI delegation session."""

from __future__ import annotations

from ai_delegation_mock import AiDelegationMock


class DelegationSession:
    """Forward explicit caller inputs once; supply no authority or automation."""

    def __init__(self, human_principals: object, ai_agents: object) -> None:
        self._mock = AiDelegationMock(human_principals, ai_agents)

    def issue_grant(self, actor: object, grant_id: object, agent_id: object,
                    authority: object, scope: object, limits: object, period: object) -> dict:
        return self._mock.issue_grant(
            actor, grant_id, agent_id, authority, scope, limits, period)

    def revoke_grant(self, actor: object, grant_id: object, reason: object) -> dict:
        return self._mock.revoke_grant(actor, grant_id, reason)

    def decide_proposal(self, actor: object, proposal_id: object,
                        decision: object, now: object) -> dict:
        return self._mock.decide_proposal(actor, proposal_id, decision, now)

    def call_tool(self, actor: object, grant_id: object, tool: object,
                  args: object, now: object) -> dict:
        return self._mock.call_tool(actor, grant_id, tool, args, now)

    def attempt_execution(self, actor: object, proposal_id: object) -> None:
        return self._mock.attempt_execution(actor, proposal_id)

    def view_grant(self, grant_id: object) -> dict:
        return self._mock.view_grant(grant_id)

    def view_proposal(self, proposal_id: object) -> dict:
        return self._mock.view_proposal(proposal_id)
