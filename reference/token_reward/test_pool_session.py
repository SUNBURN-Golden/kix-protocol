"""Source-informed interface parity; existing model conservation tests are reused."""

import ast
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from pool_session import PoolSession, dispatch_request, read_opening_balances
from reward_fixture import FixtureError, decode_json
from token_reward_model import (ALWAYS_FALSE_FLAGS, MONEY_MAX, POOLS, PROVENANCE,
                                PoolLedger, TokenRewardError, _canonical)


FIXTURE = Path(__file__).parent / "fixtures/pool_session.json"


def opening():
    return read_opening_balances(FIXTURE)


def request(operation, pool="PROTOCOL_REVENUE", amount=1, ref="ref"):
    arguments = {} if operation == "view" else {
        "pool": pool, "amount": amount,
        "source_ref" if operation == "credit" else "program_ref": ref}
    return {"operation": operation, "arguments": arguments}


def check_metadata(test, reply):
    test.assertEqual(reply["unit"], "POINT_F4")
    test.assertEqual(reply["provenance"], PROVENANCE)
    test.assertIn("Synthetic POINT_F4 simulation", reply["notice"])
    for name in ALWAYS_FALSE_FLAGS:
        test.assertIs(reply[name], False)
    test.assertEqual(len(set(reply) & {"initialized", "view", "error"}), 1)


class PoolSessionTests(unittest.TestCase):
    def test_constructor_and_methods_forward_once_with_no_reward_machine(self):
        with patch("pool_session.PoolLedger", wraps=PoolLedger) as constructor, \
                patch("token_reward_model.PoolLedger.credit", autospec=True,
                      side_effect=PoolLedger.credit) as credit, \
                patch("token_reward_model.PoolLedger.spend", autospec=True,
                      side_effect=PoolLedger.spend) as spend, \
                patch("token_reward_model.PoolLedger.view", autospec=True,
                      side_effect=PoolLedger.view) as view, \
                patch("reward_fsm.RewardMachine", side_effect=AssertionError("reward coupling")), \
                patch("reward_fixture.RewardSession", side_effect=AssertionError("reward session")):
            balances = opening()
            session = PoolSession(balances)
            constructor.assert_called_once_with(balances)
            view.assert_not_called()
            dispatch_request(session, request("credit", amount=2, ref="source"))
            dispatch_request(session, request("spend", amount=1, ref="program"))
            dispatch_request(session, request("view"))
            credit.assert_called_once_with(session._ledger, "PROTOCOL_REVENUE", 2, "source")
            spend.assert_called_once_with(session._ledger, "PROTOCOL_REVENUE", 1, "program")
            # Each model mutation itself calls view once, plus the explicitly selected read.
            self.assertEqual(view.call_count, 3)

    def test_repeated_refs_match_direct_model_and_append_again(self):
        balances = opening()
        session, direct = PoolSession(balances), PoolLedger(balances)
        for operation in ("credit", "credit", "spend", "spend", "view"):
            args = request(operation, amount=2)["arguments"]
            expected = getattr(direct, operation)(**args)
            reply = dispatch_request(session, {"operation": operation, "arguments": args})
            self.assertEqual(reply["view"], expected)
            check_metadata(self, reply)
        self.assertEqual(len(session.view()["credits"]), 7)
        self.assertEqual(len(session.view()["spends"]), 2)
        self.assertEqual(session.view()["balances"], balances)

    def test_all_ordinary_rejections_preserve_full_snapshot_and_precedence(self):
        session, direct = PoolSession(opening()), PoolLedger(opening())
        cases = [request("spend", pool=pool) for pool in POOLS[:3]]
        cases += [request("spend", amount=3), request("credit", amount=MONEY_MAX),
                  request("spend", ref=" bad "), request("credit", ref=""),
                  request("credit", pool="UNKNOWN"),
                  request("spend", pool="CUSTOMER_DEPOSIT", amount=False, ref=None)]
        for op in ("credit", "spend"):
            for field, values in {"amount": [True, False, None, 1.0, "1", 0, -1, 2**100, [], {}],
                                  "pool": [None, 1, [], {}],
                                  "source_ref" if op == "credit" else "program_ref":
                                  [None, True, [], {}, "x" * 101]}.items():
                for value in values:
                    item = request(op)
                    item["arguments"][field] = value
                    cases.append(item)
        for item in cases:
            with self.subTest(item=item):
                before = session.view()
                with self.assertRaises(TokenRewardError) as expected:
                    getattr(direct, item["operation"])(**item["arguments"])
                with self.assertRaises(TokenRewardError) as actual:
                    dispatch_request(session, item)
                self.assertEqual(actual.exception.code, expected.exception.code)
                self.assertEqual(session.view(), before)
                self.assertEqual(session.view(), direct.view())

    def test_snapshots_from_all_methods_are_detached_in_both_directions(self):
        balances = opening()
        session = PoolSession(balances)
        first = session.view()
        first_copy = copy.deepcopy(first)
        balances["PROTOCOL_REVENUE"] = 999
        for operation in ("credit", "spend", "view"):
            result = dispatch_request(session, request(operation))["view"]
            expected = session.view()
            result["balances"]["PROTOCOL_REVENUE"] = 999
            result["credits"][0]["amount"] = 999
            if result["spends"]:
                result["spends"][0]["amount"] = 999
            result["credits"].clear()
            result["spends"].append({"corrupt": True})
            self.assertEqual(session.view(), expected)
            self.assertEqual(first, first_copy)

    def test_invalid_request_shapes_never_dispatch(self):
        cases = [None, [], {}, {"operation": "view"},
                 {"operation": "view", "arguments": {}, "extra": 0}]
        cases += [{"operation": op, "arguments": {}} for op in
                  (None, [], {}, True, "__init__", "transfer", "canonical_state")]
        for operation in ("credit", "spend", "view"):
            base = request(operation)
            for field in base["arguments"]:
                item = copy.deepcopy(base)
                del item["arguments"][field]
                cases.append(item)
            for args in ([], None, "", {**base["arguments"], "extra": 1}):
                cases.append({"operation": operation, "arguments": args})
        for value in (float("nan"), float("inf"), "\ud800", (1,), {1}):
            cases.append(request("credit", amount=value))
        with patch.object(PoolLedger, "credit") as credit, \
                patch.object(PoolLedger, "spend") as spend, \
                patch.object(PoolLedger, "view") as view:
            session = PoolSession(opening())
            for item in cases:
                with self.subTest(item=repr(item)), self.assertRaises(FixtureError):
                    dispatch_request(session, item)
            credit.assert_not_called()
            spend.assert_not_called()
            view.assert_not_called()

    def test_exact_integer_not_rounded_before_domain_validation(self):
        number = 9007199254740993
        item = decode_json('{"operation":"credit","arguments":{"pool":"PROTOCOL_REVENUE",'
                           '"amount":9007199254740993,"source_ref":"ref"}}')
        with patch.object(PoolLedger, "credit", autospec=True,
                          side_effect=PoolLedger.credit) as credit:
            session = PoolSession(opening())
            with self.assertRaisesRegex(TokenRewardError, "INVALID_AMOUNT"):
                dispatch_request(session, item)
            self.assertIs(type(credit.call_args.args[2]), int)
            self.assertEqual(credit.call_args.args[2], number)
        balances = {pool: MONEY_MAX for pool in POOLS}
        self.assertEqual(PoolSession(balances).view()["balances"], balances)

    def test_fixture_shape_and_constructor_errors_stay_separate(self):
        good = {"fixture_version": 1, "provenance": PROVENANCE, "opening_balances": opening()}
        invalid = [{key: value for key, value in good.items() if key != missing} for missing in good]
        invalid += [{**good, "extra": 1}, {**good, "fixture_version": True},
                    {**good, "fixture_version": 1.0}, {**good, "provenance": "REAL"}, []]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            for item in invalid:
                path.write_text(_canonical(item), encoding="utf-8")
                with self.assertRaises(FixtureError):
                    read_opening_balances(path)
            for balances in ({}, [], None, {**opening(), "OTHER": 1},
                             {key: value for key, value in opening().items() if key != POOLS[0]},
                             {**opening(), "PROTOCOL_REVENUE": True},
                             {**opening(), "PROTOCOL_REVENUE": MONEY_MAX + 1}):
                path.write_text(_canonical({**good, "opening_balances": balances}), encoding="utf-8")
                forwarded = read_opening_balances(path)
                with self.assertRaises(TokenRewardError) as expected:
                    PoolLedger(balances)
                with self.assertRaises(TokenRewardError) as actual:
                    PoolSession(forwarded)
                self.assertEqual(actual.exception.code, expected.exception.code)

    def test_new_modules_import_only_stdlib_and_selected_local_helpers(self):
        allowed = {"pool_session", "pool_cli", "reward_fixture", "token_reward_model"}
        for name in ("pool_session.py", "pool_cli.py", "pool_console.py"):
            tree = ast.parse((Path(__file__).parent / name).read_text())
            for node in ast.walk(tree):
                modules = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                           else [node.module] if isinstance(node, ast.ImportFrom) else [])
                for module in modules:
                    self.assertIn(module.split(".")[0], sys.stdlib_module_names | allowed)


if __name__ == "__main__":
    unittest.main()
