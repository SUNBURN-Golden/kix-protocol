"""Wrapper gaps: explicit signatures, unchanged forwarding and isolated memory."""

import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import call, patch

from ai_delegation_mock import AiDelegationError, AiDelegationMock
from ai_delegation_property_support import mk_limits, mk_period, mk_scope
from delegation_session import DelegationSession


FIXTURES = Path(__file__).with_name("fixtures")
OPERATIONS = ("issue_grant", "revoke_grant", "decide_proposal", "call_tool",
              "attempt_execution", "view_grant", "view_proposal")


def requests(name):
    return [json.loads(line) for line in (FIXTURES / (name + ".jsonl")).read_text(
        encoding="utf-8").splitlines()]


class DelegationSessionTests(unittest.TestCase):
    def test_exactly_seven_public_methods_and_signatures_match_mock(self):
        self.assertEqual({name for name in dir(DelegationSession) if not name.startswith("_")},
                         set(OPERATIONS))
        for operation in ("__init__",) + OPERATIONS:
            with self.subTest(operation=operation):
                self.assertEqual(inspect.signature(getattr(DelegationSession, operation)),
                                 inspect.signature(getattr(AiDelegationMock, operation)))

    def test_all_journeys_match_direct_mock_results_and_errors(self):
        for journey in ("lifecycle", "boundaries", "replay"):
            session = DelegationSession(["human-a"], ["agent-a", "agent-b"])
            direct = AiDelegationMock(["human-a"], ["agent-a", "agent-b"])
            for request in requests(journey):
                operation, arguments = request["operation"], request["arguments"]
                with self.subTest(journey=journey, request=request):
                    try:
                        expected = getattr(direct, operation)(**arguments)
                    except AiDelegationError as error:
                        with self.assertRaises(AiDelegationError) as caught:
                            getattr(session, operation)(**arguments)
                        self.assertEqual(caught.exception.code, error.code)
                    else:
                        self.assertEqual(getattr(session, operation)(**arguments), expected)

    def test_each_method_forwards_original_objects_once_and_returns_same_object(self):
        examples = {r["operation"]: r["arguments"] for journey in ("lifecycle", "boundaries")
                    for r in requests(journey)}
        session = DelegationSession(["human-a"], ["agent-a"])
        for operation in OPERATIONS:
            arguments = examples[operation]
            values = [arguments[name] for name in inspect.signature(
                getattr(DelegationSession, operation)).parameters if name != "self"]
            with self.subTest(operation=operation), patch.object(session, "_mock") as mock:
                target = getattr(mock, operation)
                result = {"opaque": [None, False, "unchanged"]}
                target.return_value = result
                self.assertIs(getattr(session, operation)(**arguments), result)
                self.assertEqual(mock.mock_calls, [getattr(call, operation)(*values)])
                for actual, original in zip(target.call_args.args, values):
                    self.assertIs(actual, original)
                mock.reset_mock()
                refusal = AiDelegationError("DELEGATED_EXECUTION_DISABLED")
                target.side_effect = refusal
                with self.assertRaises(AiDelegationError) as caught:
                    getattr(session, operation)(**arguments)
                self.assertIs(caught.exception, refusal)
                self.assertEqual(len(mock.mock_calls), 1)

    def test_constructor_forwards_registries_without_defaults_or_restoration(self):
        humans, agents = ["human-a"], ["agent-a"]
        with patch("delegation_session.AiDelegationMock") as constructor:
            session = DelegationSession(humans, agents)
            constructor.assert_called_once_with(humans, agents)
            self.assertIs(constructor.call_args.args[0], humans)
            self.assertIs(constructor.call_args.args[1], agents)
            self.assertIs(session._mock, constructor.return_value)
        with self.assertRaises(TypeError):
            DelegationSession()
        with self.assertRaises(AiDelegationError) as caught:
            DelegationSession(["same"], ["same"])
        self.assertEqual(caught.exception.code, "MOCK_INVARIANT")

    def test_sessions_are_isolated_and_views_remain_detached(self):
        first, second = (DelegationSession(["human-a"], ["agent-a"]) for _ in range(2))
        first.issue_grant("human-a", "g", "agent-a", ["QUERY"],
                          mk_scope(), mk_limits(), mk_period())
        with self.assertRaises(AiDelegationError) as caught:
            second.view_grant("g")
        self.assertEqual(caught.exception.code, "UNKNOWN_GRANT")
        view = first.view_grant("g")
        view["scope"]["surfaces"].clear()
        self.assertEqual(first.view_grant("g")["scope"]["surfaces"], ["surf-a", "surf-b"])


if __name__ == "__main__":
    unittest.main()
