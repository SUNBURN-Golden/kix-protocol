"""Predicate checks for the token-reward reference model.

Fixture numbers in this file are not policy values. They exercise TK-4,
TK-12, and V6. They are not an independent verification of those predicates.

This suite runs in the protocol workflow's offline reference loop
(.github/workflows/protocol.yml). A passing run is not an independent
verification.
"""

import hashlib
import inspect
import json
import unittest

from token_reward_model import (
    ALARM_HOLDER_BURN,
    ALARM_MATCH,
    ALARM_UNAPPROVED_MINT,
    ALARM_UNAPPROVED_PATH,
    ALARM_UNEXPLAINED,
    MONEY_MAX,
    OBLIGATION_POOLS,
    POOLS,
    REWARD_ID_SCHEME,
    SPENDABLE_POOLS,
    PoolLedger,
    TokenRewardError,
    collateral_recognized,
    net_residual_revenue,
    reconcile_supply,
    reward_budget,
    reward_id,
    supply_report,
)


def codes(fn):
    try:
        fn()
    except TokenRewardError as error:
        return error.code
    raise AssertionError("expected TokenRewardError")


def opening(**overrides):
    """Synthetic opening balances. Not a policy value."""

    base = {pool: 0 for pool in POOLS}
    base.update(overrides)
    return base


def supply_event(event_id, op, amount, *, approved=True, path_approved=True, program="program-1"):
    return {
        "event_id": event_id,
        "op": op,
        "amount": amount,
        "approved": approved,
        "path_approved": path_approved,
        "program": program,
    }


class PoolConservationTests(unittest.TestCase):
    """TL0-TK04-T1. Exercises pool conservation. Not an independent verification."""

    def test_TL0_TK04_T1_forbidden_pools_do_not_fund_token_spend(self):
        for pool in ("CUSTOMER_DEPOSIT", "ORGANIZER_SETTLEMENT", "REFUND_RESERVE"):
            self.assertIn(pool, OBLIGATION_POOLS)
            ledger = PoolLedger(opening(**{name: 20 for name in POOLS}))
            before = ledger.view()
            self.assertEqual(codes(lambda pool=pool: ledger.spend(pool, 1, "program-1")), "POOL_FORBIDDEN_FOR_TOKEN_SPEND")
            self.assertEqual(ledger.view(), before)

    def test_shortfall_pauses_without_cross_pool_top_up(self):
        ledger = PoolLedger(
            opening(PROTOCOL_REVENUE=2, TOKEN_TREASURY_REWARD=9, CUSTOMER_DEPOSIT=8)
        )
        before = ledger.view()["balances"]
        self.assertEqual(codes(lambda: ledger.spend("PROTOCOL_REVENUE", 3, "program-1")), "POOL_EXHAUSTED_PAUSED")
        self.assertEqual(ledger.view()["balances"], before)
        self.assertFalse(hasattr(ledger, "transfer"))
        self.assertFalse(hasattr(ledger, "top_up"))

    def test_spendable_pools_conserve_across_explicit_orders(self):
        operations = [
            ("credit", "PROTOCOL_REVENUE", 5, "src-1"),
            ("spend", "PROTOCOL_REVENUE", 3, "program-1"),
            ("credit", "TOKEN_TREASURY_REWARD", 7, "src-2"),
            ("spend", "TOKEN_TREASURY_REWARD", 2, "program-1"),
            ("credit", "CUSTOMER_DEPOSIT", 4, "src-3"),
        ]
        orders = (
            operations,
            (operations[2], operations[3], operations[0], operations[1], operations[4]),
            (operations[4], operations[0], operations[2], operations[1], operations[3]),
        )
        balances = []
        for order in orders:
            ledger = PoolLedger(opening())
            for kind, pool, amount, ref in order:
                if kind == "credit":
                    ledger.credit(pool, amount, ref)
                else:
                    ledger.spend(pool, amount, ref)
                snapshot = ledger.view()
                for name in POOLS:
                    credits = sum(item["amount"] for item in snapshot["credits"] if item["pool"] == name)
                    spends = sum(item["amount"] for item in snapshot["spends"] if item["pool"] == name)
                    self.assertEqual(credits - spends, snapshot["balances"][name])
            balances.append(ledger.view()["balances"])
        self.assertEqual(balances[0], balances[1])
        self.assertEqual(balances[1], balances[2])
        self.assertEqual(balances[0]["PROTOCOL_REVENUE"], 2)
        self.assertEqual(balances[0]["TOKEN_TREASURY_REWARD"], 5)
        self.assertEqual(balances[0]["CUSTOMER_DEPOSIT"], 4)
        self.assertEqual(balances[0]["ORGANIZER_SETTLEMENT"], 0)
        self.assertEqual(balances[0]["REFUND_RESERVE"], 0)

    def test_spend_before_credit_pauses_and_later_credit_can_fund_same_pool(self):
        paused = PoolLedger(opening())
        self.assertEqual(codes(lambda: paused.spend("TOKEN_TREASURY_REWARD", 1, "program-1")), "POOL_EXHAUSTED_PAUSED")
        self.assertEqual(paused.view()["balances"]["TOKEN_TREASURY_REWARD"], 0)
        funded = PoolLedger(opening())
        funded.credit("TOKEN_TREASURY_REWARD", 1, "src-1")
        funded.spend("TOKEN_TREASURY_REWARD", 1, "program-1")
        self.assertEqual(funded.view()["balances"]["TOKEN_TREASURY_REWARD"], 0)
        self.assertEqual(funded.view()["balances"]["PROTOCOL_REVENUE"], 0)

    def test_opening_balances_are_required_and_not_defaulted(self):
        self.assertIs(
            inspect.signature(PoolLedger.__init__).parameters["opening_balances"].default,
            inspect.Parameter.empty,
        )
        self.assertEqual(codes(lambda: PoolLedger({})), "POOL_BALANCES_REQUIRED")
        missing = opening()
        del missing["REFUND_RESERVE"]
        self.assertEqual(codes(lambda: PoolLedger(missing)), "POOL_BALANCES_REQUIRED")
        extra = opening()
        extra["OTHER"] = 1
        self.assertEqual(codes(lambda: PoolLedger(extra)), "POOL_BALANCES_REQUIRED")
        self.assertEqual(codes(lambda: PoolLedger(opening()).spend("NO_SUCH_POOL", 1, "program-1")), "POOL_UNKNOWN")
        self.assertEqual(SPENDABLE_POOLS, frozenset({"PROTOCOL_REVENUE", "TOKEN_TREASURY_REWARD"}))

    def test_caller_opening_dict_is_not_aliased(self):
        balances = opening(PROTOCOL_REVENUE=4)
        ledger = PoolLedger(balances)
        balances["PROTOCOL_REVENUE"] = 0
        self.assertEqual(ledger.view()["balances"]["PROTOCOL_REVENUE"], 4)


class CollateralTests(unittest.TestCase):
    """TL0-TK12-T1. Exercises collateral recognition. Not an independent verification."""

    def test_TL0_TK12_T1_token_only_collateral_is_rejected(self):
        self.assertEqual(
            codes(lambda: collateral_recognized(100, [{"kind": "TOKEN", "amount": 50}])),
            "TOKEN_ONLY_COLLATERAL_REJECTED",
        )

    def test_token_valuation_is_refused(self):
        items = [{"kind": "TOKEN", "amount": 50, "valuation": 1}]
        self.assertEqual(codes(lambda: collateral_recognized(100, items)), "PRICE_SOURCE_UNDEFINED")
        mixed = [
            {"kind": "KRW_GUARANTEE", "amount": 40},
            {"kind": "TOKEN", "amount": 50, "valuation": 1},
        ]
        self.assertEqual(codes(lambda: collateral_recognized(100, mixed)), "PRICE_SOURCE_UNDEFINED")

    def test_krw_portion_only_when_token_is_also_present(self):
        recognized = collateral_recognized(
            100,
            [
                {"kind": "KRW_GUARANTEE", "amount": 30},
                {"kind": "ESCROW", "amount": 25},
                {"kind": "TOKEN", "amount": 999},
            ],
        )
        self.assertEqual(recognized["recognized_krw"], 55)
        self.assertEqual(recognized["token_recognized"], 0)
        self.assertEqual(recognized["liability_krw"], 100)
        self.assertEqual(recognized["currency"], "KRW")

    def test_empty_collateral_recognizes_zero_without_a_token_error(self):
        recognized = collateral_recognized(20, [])
        self.assertEqual(recognized["recognized_krw"], 0)
        self.assertEqual(recognized["token_recognized"], 0)

    def test_unknown_collateral_kind_is_rejected(self):
        self.assertEqual(
            codes(lambda: collateral_recognized(10, [{"kind": "KIX_TOKEN", "amount": 1}])),
            "COLLATERAL_KIND_UNSUPPORTED",
        )


class BudgetTests(unittest.TestCase):
    def test_budget_inputs_have_no_defaults_and_exclude_in_window_revenue(self):
        for function in (net_residual_revenue, reward_budget):
            for parameter in inspect.signature(function).parameters.values():
                self.assertIs(parameter.default, inspect.Parameter.empty)
        # Synthetic fixtures, not policy values.
        residual = net_residual_revenue(
            gross_revenue=100,
            refundable_window_revenue=40,
            customer_deposit_outlay=3,
            organizer_settlement_outlay=4,
            refund_reserve_outlay=3,
            operating_cost=5,
            loss_provision=5,
        )
        self.assertEqual(residual, 40)
        capped = reward_budget(
            cap=30,
            ratio_numerator=1,
            ratio_denominator=2,
            net_residual=residual,
            periods=4,
        )
        self.assertEqual(capped, 20)
        same_residual_other_n = reward_budget(
            cap=30,
            ratio_numerator=1,
            ratio_denominator=2,
            net_residual=residual,
            periods=9,
        )
        self.assertEqual(same_residual_other_n, capped)
        floored = reward_budget(
            cap=100,
            ratio_numerator=1,
            ratio_denominator=3,
            net_residual=40,
            periods=4,
        )
        self.assertEqual(floored, 13)
        self.assertEqual(
            codes(
                lambda: net_residual_revenue(
                    gross_revenue=10,
                    refundable_window_revenue=11,
                    customer_deposit_outlay=0,
                    organizer_settlement_outlay=0,
                    refund_reserve_outlay=0,
                    operating_cost=0,
                    loss_provision=0,
                )
            ),
            "WINDOW_REVENUE_EXCEEDS_GROSS",
        )
        self.assertEqual(codes(lambda: reward_budget(cap=1, ratio_numerator=1, ratio_denominator=0, net_residual=1, periods=1)), "INVALID_RATIO")
        self.assertEqual(codes(lambda: reward_budget(cap=1, ratio_numerator=1, ratio_denominator=1, net_residual=1, periods=0)), "INVALID_PERIODS")


class SupplyTests(unittest.TestCase):
    def test_v6_supply_recompute_and_alarm_classes(self):
        events = [
            supply_event("mint-1", "MINT", 10),
            supply_event("alloc-1", "ALLOCATE", 4),
            supply_event("burn-1", "BURN", 3),
        ]
        report = supply_report(events)
        self.assertEqual(report["minted_total"], 10)
        self.assertEqual(report["allocated_total"], 4)
        self.assertEqual(report["burned_total"], 3)
        self.assertEqual(report["layer_supply"], 7)
        self.assertEqual(report["unapproved_mint"], 0)
        matched = reconcile_supply(report, 7)
        self.assertEqual(matched["alarm"], ALARM_MATCH)
        self.assertFalse(matched["mismatch"])
        self.assertFalse(matched["stop_payout"])

        unapproved = supply_report(events + [supply_event("mint-x", "MINT", 3, approved=False)])
        self.assertEqual(unapproved["layer_supply"], 7)
        self.assertEqual(unapproved["unapproved_mint"], 3)
        minted = reconcile_supply(unapproved, 10)
        self.assertEqual(minted["alarm"], ALARM_UNAPPROVED_MINT)
        self.assertTrue(minted["mismatch"])
        self.assertTrue(minted["stop_payout"])

        bad_path = supply_report([supply_event("mint-p", "MINT", 10, path_approved=False)])
        path = reconcile_supply(bad_path, 10)
        self.assertEqual(path["alarm"], ALARM_UNAPPROVED_PATH)
        self.assertTrue(path["stop_payout"])
        self.assertTrue(path["mismatch"])

        holder_events = [
            supply_event("mint-h", "MINT", 10),
            supply_event("hold-1", "HOLDER_BURN", 2, approved=False, program=None),
        ]
        holder_report = supply_report(holder_events)
        self.assertEqual(holder_report["layer_supply"], 10)
        self.assertEqual(holder_report["holder_burn_outside_layer"], 2)
        holder = reconcile_supply(holder_report, 8)
        self.assertEqual(holder["alarm"], ALARM_HOLDER_BURN)
        self.assertFalse(holder["mismatch"])
        self.assertFalse(holder["stop_payout"])

        unexplained = reconcile_supply(report, 6)
        self.assertEqual(unexplained["alarm"], ALARM_UNEXPLAINED)
        self.assertTrue(unexplained["mismatch"])
        self.assertFalse(unexplained["stop_payout"])

    def test_tampered_report_is_recomputed_and_rejected(self):
        report = supply_report([supply_event("mint-1", "MINT", 10)])
        report["layer_supply"] = 0
        self.assertEqual(codes(lambda: reconcile_supply(report, 0)), "SUPPLY_REPORT_MISMATCH")

    def test_duplicate_supply_event_is_rejected(self):
        event = supply_event("mint-1", "MINT", 1)
        self.assertEqual(codes(lambda: supply_report([event, dict(event)])), "SUPPLY_EVENT_DUPLICATE")

    def test_chain_figure_is_only_the_supplied_integer(self):
        report = supply_report([supply_event("mint-1", "MINT", 1)])
        self.assertEqual(reconcile_supply(report, 1)["chain_supply"], 1)
        self.assertNotIn("endpoint", report)
        self.assertEqual(report["figure"], "SYNTHETIC_SUPPLY_FIGURE")


class RewardIdTests(unittest.TestCase):
    def test_reward_id_binds_the_tuple_and_not_a_rule_version(self):
        kwargs = {
            "program": "program-1",
            "source_op_id": "op-1",
            "recipient": "recipient-1",
            "kind": "participation",
        }
        left = reward_id(**kwargs)
        right = reward_id(**kwargs)
        self.assertEqual(left, right)
        self.assertNotEqual(left, reward_id(**{**kwargs, "source_op_id": "op-2"}))
        self.assertTrue(left.startswith(REWARD_ID_SCHEME + ":"))
        names = reward_id.__code__.co_varnames
        self.assertNotIn("rule_version", names)
        self.assertNotIn("fence", names)
        payload = {
            "kind": "participation",
            "program": "program-1",
            "recipient": "recipient-1",
            "source_op_id": "op-1",
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(left, REWARD_ID_SCHEME + ":" + digest)
        self.assertLessEqual(len(left), 100)
        self.assertEqual(MONEY_MAX, 10**12)


if __name__ == "__main__":
    unittest.main()
