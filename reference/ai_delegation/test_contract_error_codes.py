"""Negative tests for contract error codes (section 8) that no other test names.

Added by plan-contract-error-code-coverage. Fixtures are synthetic and follow
test_ai_delegation_mock.py; no limit, period or name here is a product value.
"""

import unittest

from ai_delegation_mock import AiDelegationError, AiDelegationMock

HUMAN = "human-issuer"
AGENT = "agent-1"


class AiDelegationErrorCodeGapTests(unittest.TestCase):
    def setUp(self):
        self.book = AiDelegationMock([HUMAN], [AGENT])
        self.book.issue_grant(
            actor=HUMAN,
            grant_id="g1",
            agent_id=AGENT,
            authority=["QUERY", "PROPOSE"],
            scope={"surfaces": ["surface-a"]},
            limits={"per_action_max": 100, "cumulative_max": 1_000, "count_max": 5, "currency": "KRW"},
            period={"not_before": 10, "not_after": 20},
        )

    def fails(self, fn):
        before = self.book.state_digest()
        try:
            fn()
        except AiDelegationError as error:
            self.assertEqual(self.book.state_digest(), before)
            return error.code
        self.fail("expected AiDelegationError")

    def test_unknown_proposal_id_is_unknown_proposal_on_every_path(self):
        self.assertEqual(self.fails(lambda: self.book.view_proposal("p-missing")), "UNKNOWN_PROPOSAL")
        self.assertEqual(
            self.fails(lambda: self.book.decide_proposal(HUMAN, "p-missing", "APPROVE", 10)),
            "UNKNOWN_PROPOSAL",
        )
        self.assertEqual(
            self.fails(lambda: self.book.call_tool(
                AGENT, "g1", "withdraw_proposal", {"proposal_id": "p-missing"}, 10
            )),
            "UNKNOWN_PROPOSAL",
        )


if __name__ == "__main__":
    unittest.main()
