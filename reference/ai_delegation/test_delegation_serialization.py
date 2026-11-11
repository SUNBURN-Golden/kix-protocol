"""Transport validation gaps; nested domain predicates stay in the mock."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_delegation_mock import AiDelegationError, AiDelegationMock, _canonical
from delegation_cli import dispatch_request
from delegation_fixture import FixtureError, decode_json, load_fixture, session_from_fixture, validate_fixture
from delegation_session import DelegationSession
from test_delegation_session import FIXTURES, OPERATIONS, requests


class DelegationSerializationTests(unittest.TestCase):
    def test_registry_initialization_matches_constructor(self):
        valid = decode_json((FIXTURES / "delegation_session.json").read_text())
        registries = [[], ["a"], ["a", "b"], ["b", "a"], ["한글", "😀"], ["a" * 100],
                      ["a" * 101], [" a"], ["a "], [""], ["a", "a"], [1], [False],
                      [None], [{}], None, {}, "a", 1, True]
        for humans in registries:
            for agents in registries:
                fixture = {**valid, "human_principals": humans, "ai_agents": agents}
                with self.subTest(humans=humans, agents=agents):
                    # Transport validation deliberately does not preflight the domain.
                    validate_fixture(fixture)
                    try:
                        AiDelegationMock(humans, agents)
                    except AiDelegationError as expected:
                        with self.assertRaises(AiDelegationError) as caught:
                            session_from_fixture(fixture)
                        self.assertEqual(caught.exception.code, expected.code)
                    else:
                        session_from_fixture(fixture)

    def test_fixture_object_shape_and_forwarding(self):
        valid = decode_json((FIXTURES / "delegation_session.json").read_text())
        for value in ({}, [], {**valid, "fixture_version": True}, {**valid, "fixture_version": 1.0},
                      {**valid, "provenance": "REAL"}, {**valid, "extra": []},
                      {**valid, "ai_agents": ("agent-a",)}, {**valid, "ai_agents": ["\ud800"]}):
            with self.subTest(value=repr(value)), patch("delegation_fixture.DelegationSession") as constructor:
                with self.assertRaises(FixtureError):
                    session_from_fixture(value)
                constructor.assert_not_called()
        fixture = {**valid, "human_principals": ["z", "a"], "ai_agents": ["😀", "é"]}
        with patch("delegation_fixture.DelegationSession") as constructor:
            session_from_fixture(fixture)
            constructor.assert_called_once_with(fixture["human_principals"], fixture["ai_agents"])
            self.assertIs(constructor.call_args.args[0], fixture["human_principals"])

    def test_strict_json_decoder(self):
        for text in ('{"x":1,"x":2}', '{"x":{"a":1,"a":2}}', '[{"a":1,"a":2}]',
                     'NaN', 'Infinity', '-Infinity', '1e9999', '-1e9999', '', '[] trailing',
                     '{"x":}', '"\\ud800"', '[' * 2000):
            with self.subTest(text=text[:50]), self.assertRaises(FixtureError):
                decode_json(text)
        self.assertEqual(decode_json('"\\ud83d\\ude00"'), "😀")

    def assert_not_dispatched(self, request):
        session = DelegationSession(["human-a"], ["agent-a"])
        with patch.object(session, "_mock") as mock:
            with self.assertRaises(FixtureError):
                dispatch_request(session, request)
            self.assertEqual(mock.mock_calls, [])

    def test_missing_extra_arguments_for_all_seven_operations(self):
        examples = {r["operation"]: r for journey in ("lifecycle", "boundaries")
                    for r in requests(journey)}
        self.assertEqual(set(examples), set(OPERATIONS))
        for operation, request in examples.items():
            for field in request["arguments"]:
                bad = copy.deepcopy(request)
                del bad["arguments"][field]
                with self.subTest(operation=operation, missing=field):
                    self.assert_not_dispatched(bad)
            self.assert_not_dispatched({**request, "arguments": {**request["arguments"], "extra": 1}})
            for arguments in (None, [], "args", 1):
                self.assert_not_dispatched({**request, "arguments": arguments})

    def test_bad_envelopes_and_unsupported_selectors(self):
        for request in (None, [], {}, {"operation": "view_grant"},
                        {"arguments": {}}, {"operation": "view_grant", "arguments": {}, "x": 1}):
            self.assert_not_dispatched(request)
        for selector in (None, [], {}, 1, "restore", "canonical_state", "state_digest",
                         "_mock", "__init__", "transfer", "delegate", "close_delegation"):
            self.assert_not_dispatched({"operation": selector, "arguments": {}})

    def test_non_json_python_values_never_dispatch(self):
        for value in (float("nan"), float("inf"), float("-inf"), (1, 2),
                      {1: "value"}, b"x", "\ud800", object()):
            request = copy.deepcopy(requests("lifecycle")[0])
            request["arguments"]["scope"] = {"nested": value}
            self.assert_not_dispatched(request)
        cycle = []
        cycle.append(cycle)
        self.assert_not_dispatched({"operation": "view_grant", "arguments": {"grant_id": cycle}})

    def test_nested_values_and_tools_are_forwarded_without_transport_reinterpretation(self):
        session = DelegationSession(["human-a"], ["agent-a"])
        cases = [("scope", None, "SCOPE_VIOLATION"), ("scope", {"surfaces":[], "x":1}, "SCOPE_VIOLATION"),
                 ("limits", {}, "LIMIT_REQUIRED"), ("limits", [], "LIMIT_REQUIRED"),
                 ("period", None, "INVALID_PERIOD"), ("authority", ["EXECUTE"], "EXECUTE_AUTHORITY_DISABLED")]
        for field, value, code in cases:
            request = copy.deepcopy(requests("lifecycle")[0])
            request["arguments"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(AiDelegationError) as caught:
                dispatch_request(session, request)
            self.assertEqual(caught.exception.code, code)
        request = requests("lifecycle")[0]
        original = copy.deepcopy(request)
        with patch.object(session, "_mock") as mock:
            payload = {"opaque": [None, False, "한글"]}
            mock.issue_grant.return_value = payload
            result = dispatch_request(session, decode_json(_canonical(request)))
            self.assertIs(result["receipt"], payload)
            self.assertEqual(decode_json(_canonical(result)), result)
            self.assertEqual(request, original)
            self.assertEqual(mock.issue_grant.call_args.args[4], request["arguments"]["scope"])
            tool = {"operation":"call_tool", "arguments":{
                "actor":"agent-a", "grant_id":"g", "tool":"sign", "args":None, "now":False}}
            dispatch_request(session, tool)
            mock.call_tool.assert_called_once_with("agent-a", "g", "sign", None, False)

    def test_fixture_requires_exact_schema_version_provenance_and_both_registries(self):
        valid = json.loads((FIXTURES / "delegation_session.json").read_text(encoding="utf-8"))
        bad = [{}, {**valid, "fixture_version": True}, {**valid, "fixture_version":1.0},
               {**valid, "fixture_version":2}, {**valid, "provenance":"REAL"},
               {**valid, "grants":[]}, {**valid, "proposals":[]}]
        bad += [{k:v for k,v in valid.items() if k != field} for field in valid]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            for fixture in bad:
                path.write_text(json.dumps(fixture), encoding="utf-8")
                with patch("delegation_fixture.DelegationSession") as constructor:
                    with self.assertRaises(FixtureError):
                        load_fixture(path)
                    constructor.assert_not_called()
            for humans, agents, code in ((None, [], "INVALID_ID"), (["h", "h"], [], "INVALID_ID"),
                                         (["same"], ["same"], "MOCK_INVARIANT")):
                path.write_text(json.dumps({**valid, "human_principals":humans, "ai_agents":agents}), encoding="utf-8")
                with self.assertRaises(AiDelegationError) as caught:
                    load_fixture(path)
                self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()
