"""Interface gaps only; CollateralTests/TL-4 remain the arithmetic evidence."""

from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from collateral_assessment import NOTICE, OPERATION, dispatch_request
from reward_fixture import FixtureError, decode_json
from token_reward_model import MONEY_MAX, PROVENANCE, TokenRewardError, collateral_recognized


def request(liability=100, items=None):
    return {"operation": OPERATION, "arguments": {
        "liability_krw": liability, "collateral_items": [] if items is None else items}}


def item(amount=30, kind="KRW_GUARANTEE", **extra):
    return {"kind": kind, "amount": amount, **extra}


class CollateralDispatchTests(unittest.TestCase):
    def test_complete_results_parity_and_input_preservation(self):
        # Below/equal/above liability are all calculations, with no classification.
        for items in ([], [item(30)], [item(100, "ESCROW")], [item(101)],
                      [item(30), item(25, "ESCROW"), item(999, "TOKEN")]):
            with self.subTest(items=items):
                value = request(items=items)
                before = deepcopy(value)
                expected = collateral_recognized(**value["arguments"])
                with patch("collateral_assessment.collateral_recognized",
                           wraps=collateral_recognized) as calculate:
                    output = dispatch_request(value)
                calculate.assert_called_once_with(**value["arguments"])
                self.assertIs(calculate.call_args.kwargs["collateral_items"], items)
                self.assertEqual(value, before)
                self.assertEqual(output, {"operation": OPERATION, "provenance": PROVENANCE,
                                         "evidence_class": "CALCULATION_ONLY",
                                         "notice": NOTICE, "result": expected})

    def test_domain_code_and_error_precedence_parity(self):
        cases = [
            (request(0, [item(valuation=1)]), "INVALID_AMOUNT"),
            (request(items="bad"), "COLLATERAL_TYPE"),
            (request(items=[None]), "COLLATERAL_TYPE"),
            (request(items=[item(kind="bad", valuation=None)]), "PRICE_SOURCE_UNDEFINED"),
            (request(items=[item(kind="bad", extra=1)]), "COLLATERAL_KIND_UNSUPPORTED"),
            (request(items=[{"kind": "TOKEN"}]), "COLLATERAL_FIELDS"),
            (request(items=[item(extra=1)]), "COLLATERAL_FIELDS"),
            (request(items=[item(0, "TOKEN")]), "INVALID_AMOUNT"),
            (request(items=[item(kind="TOKEN")]), "TOKEN_ONLY_COLLATERAL_REJECTED"),
            (request(items=[item(kind="TOKEN"), item(valuation=1)]), "PRICE_SOURCE_UNDEFINED"),
        ]
        for value, code in cases:
            with self.subTest(value=value):
                before = deepcopy(value)
                with self.assertRaises(TokenRewardError) as direct:
                    collateral_recognized(**value["arguments"])
                with patch("collateral_assessment.collateral_recognized",
                           wraps=collateral_recognized) as calculate:
                    with self.assertRaises(TokenRewardError) as wrapped:
                        dispatch_request(value)
                calculate.assert_called_once_with(**value["arguments"])
                self.assertEqual(wrapped.exception.code, direct.exception.code)
                self.assertEqual(wrapped.exception.code, code)
                self.assertEqual(value, before)

    def test_exact_integer_boundaries_forward_without_coercion(self):
        for amount in (1, MONEY_MAX):
            value = request(amount, [item(amount)])
            output = dispatch_request(decode_json(json.dumps(value)))
            self.assertIs(type(output["result"]["recognized_krw"]), int)
            self.assertEqual(output["result"]["recognized_krw"], amount)
        at_bound = dispatch_request(request(items=[item(MONEY_MAX - 1), item(1, "ESCROW")]))
        self.assertEqual(at_bound["result"]["recognized_krw"], MONEY_MAX)
        with self.assertRaises(TokenRewardError) as caught:
            dispatch_request(request(items=[item(MONEY_MAX), item(1, "ESCROW")]))
        self.assertEqual(caught.exception.code, "INVALID_AMOUNT")
        for amount in (0, -1, True, False, "1", 1.0, 1.5, None, MONEY_MAX + 1, 2**53 + 1):
            for value in (request(amount), request(items=[item(amount)])):
                with self.subTest(value=value):
                    with patch("collateral_assessment.collateral_recognized",
                               wraps=collateral_recognized) as calculate:
                        with self.assertRaises(TokenRewardError) as caught:
                            dispatch_request(value)
                    self.assertEqual(caught.exception.code, "INVALID_AMOUNT")
                    calculate.assert_called_once_with(**value["arguments"])
        for spelling in ("1.0", "1e0", "9007199254740993"):
            value = decode_json('{"operation":"collateral_recognized","arguments":'
                                '{"liability_krw":' + spelling + ',"collateral_items":[]}}')
            self.assertEqual(value["arguments"]["liability_krw"],
                             9007199254740993 if spelling.isdigit() else 1.0)
            with self.assertRaises(TokenRewardError) as caught:
                dispatch_request(value)
            self.assertEqual(caught.exception.code, "INVALID_AMOUNT")

    def test_invalid_envelopes_and_python_values_never_calculate(self):
        values = [None, [], {}, {"operation": OPERATION},
                  {"operation": "other", "arguments": {}},
                  {"operation": [], "arguments": {}},
                  {"operation": OPERATION, "arguments": []},
                  {"operation": OPERATION, "arguments": {"liability_krw": 100}},
                  {"operation": OPERATION, "arguments": {"collateral_items": []}},
                  {**request(), "extra": 1},
                  request(float("inf")), request(float("nan")), request({1}),
                  request(items=(item(),)), request(items=[{1: 2}]),
                  request(items=[item(extra=b"bytes")]), request(items=[item(kind="\ud800")])]
        extra_argument = request()
        extra_argument["arguments"]["valuation"] = 1
        values.append(extra_argument)
        for value in values:
            with self.subTest(value=repr(value)):
                with patch("collateral_assessment.collateral_recognized") as calculate:
                    with self.assertRaises(FixtureError):
                        dispatch_request(value)
                    calculate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
