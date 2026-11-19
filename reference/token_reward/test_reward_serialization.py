"""JSON boundary gaps: no FSM calls on malformed structure or non-JSON data."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reward_cli import dispatch_request
from reward_fixture import FixtureError, decode_json, load_fixture
from reward_session import RewardSession
from test_reward_session import FIXTURES, requests
from tl4_support import funded_opening, human_approval
from token_reward_model import PROVENANCE, TokenRewardError, _canonical


class RewardSerializationTests(unittest.TestCase):
    def test_strict_decoder_rejects_duplicates_nonfinite_overflow_and_bad_json(self):
        for text in ('{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}',
                     '[{"x":1,"x":2}]', 'NaN', 'Infinity', '-Infinity',
                     '{"x":1e9999}', '{"x":-1e9999}', '', '[] trailing',
                     '{"x":}', '"\\ud800"', '[' * 2000):
            with self.subTest(text=text[:50]), self.assertRaises(FixtureError):
                decode_json(text)

    def assert_not_dispatched(self, request):
        session = RewardSession(funded_opening())
        with patch.object(session, "_machine") as machine:
            with self.assertRaises(FixtureError):
                dispatch_request(session, request)
            self.assertEqual(machine.mock_calls, [])

    def test_all_operation_shapes_missing_extra_arguments_and_unsupported_selectors(self):
        examples = {r["operation"]: r for name in ("participation", "cancellation", "unknown_pending")
                    for r in requests(name)}
        examples["supersede"] = {"operation": "supersede", "arguments": {
            "reward_id_value": "r", "idempotency_key": "s", "approval_ref": human_approval(),
            "rule_version": "v2"}}
        optional = {"mark_eligible": {"abuse_kind", "recipient_cap", "program_cap"},
                    "submit": {"budget_ceiling", "execution_permit"}}
        for op, request in examples.items():
            for field in set(request["arguments"]) - optional.get(op, set()):
                bad = copy.deepcopy(request)
                del bad["arguments"][field]
                with self.subTest(operation=op, missing=field):
                    self.assert_not_dispatched(bad)
            bad = copy.deepcopy(request)
            bad["arguments"]["unexpected"] = None
            self.assert_not_dispatched(bad)
            self.assert_not_dispatched({**request, "arguments": []})
        for request in (None, [], {}, {"operation": "hold"},
                        {"operation": "hold", "arguments": {}, "extra": 1}):
            self.assert_not_dispatched(request)
        for operation in (None, [], {}, 1, "restore", "reject_external", "export_journal",
                          "transfer", "__init__", "_machine", "canonical_state"):
            self.assert_not_dispatched({"operation": operation, "arguments": {}})

    def test_nested_structures_and_nonjson_python_data_never_dispatch(self):
        observe = requests("participation")[0]
        submit = requests("participation")[3]
        changes = [(observe, "reward_key", None), (observe, "reward_key", {}),
                   (observe, "reward_key", {**observe["arguments"]["reward_key"], "extra": 1}),
                   (observe, "source_view", []), (submit, "approval_ref", None),
                   (submit, "approval_ref", {}),
                   (submit, "approval_ref", {**human_approval(), "extra": 1}),
                   (submit, "approval_ref", {**human_approval(), "evidence_refs": "ref"}),
                   (submit, "execution_permit", []), (submit, "execution_permit", {}),
                   (submit, "execution_permit", {"fence_ref": "f", "signed_bytes_digest": "1"*64, "x": 1})]
        for original, field, value in changes:
            bad = copy.deepcopy(original)
            bad["arguments"][field] = value
            with self.subTest(field=field, value=value):
                self.assert_not_dispatched(bad)
        for value in (float("nan"), float("inf"), float("-inf"), (1, 2), {1: "value"}, b"x", "\ud800"):
            bad = copy.deepcopy(observe)
            bad["arguments"]["source_view"]["opaque"] = value
            self.assert_not_dispatched(bad)

    def test_metadata_and_receipt_payload_survive_canonical_roundtrip(self):
        session = load_fixture(FIXTURES / "reward_session.json")
        request = requests("participation")[0]
        original = copy.deepcopy(request)
        result = dispatch_request(session, decode_json(_canonical(request)))
        self.assertEqual(result["provenance"], PROVENANCE)
        self.assertEqual(result["receipt"]["reward"]["source_view"],
                         original["arguments"]["source_view"])
        self.assertEqual(decode_json(_canonical(result)), result)
        self.assertEqual(request, original)

    def test_optional_fields_and_prior_record_are_not_inserted_by_dispatch(self):
        session = RewardSession(funded_opening())
        request = requests("participation")[3]
        del request["arguments"]["budget_ceiling"]
        with patch.object(session, "_machine") as machine:
            machine.submit.return_value = {"opaque": [None, False, "unchanged"]}
            result = dispatch_request(session, request)
            self.assertEqual(result["receipt"], machine.submit.return_value)
            self.assertNotIn("prior_record", machine.submit.call_args.kwargs["approval_ref"])
            self.assertNotIn("prior_record", request["arguments"]["approval_ref"])
            self.assertIsNone(machine.submit.call_args.kwargs["budget_ceiling"])

    def test_setup_requires_explicit_complete_balances_version_and_provenance(self):
        valid = json.loads((FIXTURES / "reward_session.json").read_text())
        malformed = [{}, {**valid, "fixture_version": True}, {**valid, "fixture_version": 2},
                     {**valid, "provenance": "REAL"}, {**valid, "extra": 1},
                     {**valid, "opening_balances": {}}, {**valid, "opening_balances": None}]
        for pool in valid["opening_balances"]:
            balances = dict(valid["opening_balances"])
            del balances[pool]
            malformed.append({**valid, "opening_balances": balances})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            for fixture in malformed:
                path.write_text(json.dumps(fixture))
                with patch("reward_fixture.RewardSession") as constructor:
                    with self.assertRaises(FixtureError):
                        load_fixture(path)
                    constructor.assert_not_called()
            path.write_text(json.dumps({**valid, "opening_balances": {
                **valid["opening_balances"], "PROTOCOL_REVENUE": True}}))
            with self.assertRaises(TokenRewardError) as caught:
                load_fixture(path)
            self.assertEqual(caught.exception.code, "INVALID_NONNEGATIVE")


if __name__ == "__main__":
    unittest.main()
