"""Author-side property checks for the token-reward reference model.

Oracles in this file are re-derived from TOKEN_ROLE_AND_SUPPLY.md §5.1, §5.2,
and §6. They are not a copy of the model's control flow used as the answer.
Fixture numbers are not policy values. Labels are harness-local, not protocol
commands. The builder wrote this file. A pass is not an independent PASS.
"""

from __future__ import annotations

import itertools
import unittest

from tl4_support import (
    CONTRACT_POOLS,
    OBLIGATION_POOLS,
    POOL_SCRIPT_STEPS,
    SEEDS,
    SPENDABLE_POOLS,
    SUPPLY_STREAM_LENGTH,
    codes,
    opening,
    rng,
)
from token_reward_model import (
    MONEY_MAX,
    OBLIGATION_POOLS as MODEL_OBLIGATION_POOLS,
    POOLS,
    SPENDABLE_POOLS as MODEL_SPENDABLE_POOLS,
    SUPPLY_REPORT_FIELDS,
    PoolLedger,
    TokenRewardError,
    collateral_recognized,
    net_residual_revenue,
    reconcile_supply,
    reward_budget,
    reward_id,
    supply_report,
)


class OracleReject(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def oracle_budget(cap: int, numerator: int, denominator: int, residual: int) -> int:
    """TOKEN_ROLE_AND_SUPPLY.md §6. min(cap, floor(residual * ratio)).

    The period count is not a multiplier. The residual is already the
    aggregate the caller says covers those periods.
    """

    scaled = residual * numerator // denominator
    if cap < scaled:
        return cap
    return scaled


def oracle_residual(gross: int, in_window: int, deductions: int) -> int:
    """§6. Revenue still inside the refundable window is excluded."""

    return (gross - in_window) - deductions


def oracle_supply(events: list) -> dict:
    """§5.1 and §5.2 V6, re-derived.

    Approved mint increases layer supply. allocate does not.
    Approved burn decreases layer supply and cannot exceed it.
    An unapproved burn does not decrease layer supply.
    Holder burn is outside the layer and is not subtracted.
    """

    minted = 0
    unapproved_mint = 0
    allocated = 0
    burned = 0
    holder_burn = 0
    seen = set()
    for event in events:
        if type(event) is not dict:
            raise OracleReject("SUPPLY_EVENT_FIELDS")
        event_id = event.get("event_id")
        if type(event_id) is not str or event_id in seen:
            if type(event_id) is str and event_id in seen:
                raise OracleReject("SUPPLY_EVENT_DUPLICATE")
            raise OracleReject("SUPPLY_EVENT_FIELDS")
        seen.add(event_id)
        op = event.get("op")
        amount = event.get("amount")
        approved = event.get("approved")
        if type(amount) is not int or not (0 < amount <= MONEY_MAX):
            raise OracleReject("INVALID_AMOUNT")
        if op == "MINT":
            if approved is True:
                minted += amount
            elif approved is False:
                unapproved_mint += amount
            else:
                raise OracleReject("SUPPLY_APPROVAL_TYPE")
        elif op == "ALLOCATE":
            allocated += amount
        elif op == "BURN":
            if approved is True:
                if amount > minted - burned:
                    raise OracleReject("SUPPLY_CONSERVATION")
                burned += amount
            elif approved is not False:
                raise OracleReject("SUPPLY_APPROVAL_TYPE")
        elif op == "HOLDER_BURN":
            if approved is not False or event.get("program") is not None:
                raise OracleReject("HOLDER_BURN_NOT_LAYER")
            holder_burn += amount
        else:
            raise OracleReject("SUPPLY_OP_UNSUPPORTED")
        if minted > MONEY_MAX or unapproved_mint > MONEY_MAX or allocated > MONEY_MAX or holder_burn > MONEY_MAX:
            raise OracleReject("INVALID_AMOUNT")
    layer = minted - burned
    if layer < 0:
        raise OracleReject("SUPPLY_CONSERVATION")
    return {
        "minted_total": minted,
        "unapproved_mint": unapproved_mint,
        "allocated_total": allocated,
        "burned_total": burned,
        "holder_burn_outside_layer": holder_burn,
        "layer_supply": layer,
    }


def _model_supply(events):
    try:
        return supply_report(events), None
    except TokenRewardError as error:
        return None, error.code


def _compare_supply(test, events):
    report, model_code = _model_supply(events)
    try:
        expected = oracle_supply(events)
        oracle_code = None
    except OracleReject as error:
        expected = None
        oracle_code = error.code
    test.assertEqual(model_code, oracle_code)
    if model_code is None:
        for field in (
            "minted_total",
            "unapproved_mint",
            "allocated_total",
            "burned_total",
            "holder_burn_outside_layer",
            "layer_supply",
        ):
            test.assertEqual(report[field], expected[field])
        test.assertEqual(report["layer_supply"], report["minted_total"] - report["burned_total"])
    return report


def _event(event_id, op, amount, *, approved=True, path_approved=True, program="program-1"):
    return {
        "event_id": event_id,
        "op": op,
        "amount": amount,
        "approved": approved,
        "path_approved": path_approved,
        "program": program,
    }


class PoolPropertyTests(unittest.TestCase):
    """TL0-TK04-T1. Author-side. Not an independent verification."""

    def test_TL4_TK04_pool_names_match_the_contract_list(self):
        self.assertEqual(POOLS, CONTRACT_POOLS)
        self.assertEqual(MODEL_OBLIGATION_POOLS, OBLIGATION_POOLS)
        self.assertEqual(MODEL_SPENDABLE_POOLS, SPENDABLE_POOLS)
        self.assertFalse(hasattr(PoolLedger, "transfer"))
        self.assertFalse(hasattr(PoolLedger, "top_up"))

    def test_TL4_TK04_obligation_spend_and_shortfall_leave_digest(self):
        ledger = PoolLedger(opening(PROTOCOL_REVENUE=2, TOKEN_TREASURY_REWARD=4, CUSTOMER_DEPOSIT=9))
        for pool in OBLIGATION_POOLS:
            before = ledger.state_digest()
            other = {name: ledger.view()["balances"][name] for name in CONTRACT_POOLS if name != pool}
            self.assertEqual(
                codes(lambda pool=pool: ledger.spend(pool, 1, "program-1")),
                "POOL_FORBIDDEN_FOR_TOKEN_SPEND",
            )
            self.assertEqual(ledger.state_digest(), before)
            for name, amount in other.items():
                self.assertEqual(ledger.view()["balances"][name], amount)
        before = ledger.state_digest()
        others = {name: ledger.view()["balances"][name] for name in CONTRACT_POOLS if name != "PROTOCOL_REVENUE"}
        self.assertEqual(
            codes(lambda: ledger.spend("PROTOCOL_REVENUE", 3, "program-1")),
            "POOL_EXHAUSTED_PAUSED",
        )
        self.assertEqual(ledger.state_digest(), before)
        self.assertEqual(ledger.view()["balances"]["PROTOCOL_REVENUE"], 2)
        for name, amount in others.items():
            self.assertEqual(ledger.view()["balances"][name], amount)

    def test_TL4_TK04_random_scripts_match_opening_plus_credits_minus_spends(self):
        for seed in SEEDS:
            mirror = {pool: seed % 5 for pool in CONTRACT_POOLS}
            ledger = PoolLedger(opening(**mirror))
            random = rng(seed)
            for step in range(POOL_SCRIPT_STEPS):
                pool = CONTRACT_POOLS[random.randrange(len(CONTRACT_POOLS))]
                amount = 1 + random.randrange(12)
                credit = random.randrange(2) == 0
                before = ledger.state_digest()
                snapshot = dict(ledger.view()["balances"])
                try:
                    if credit:
                        ledger.credit(pool, amount, "src-%s" % step)
                    else:
                        ledger.spend(pool, amount, "program-1")
                except TokenRewardError as error:
                    self.assertEqual(ledger.state_digest(), before)
                    self.assertEqual(ledger.view()["balances"], snapshot)
                    if not credit and pool in OBLIGATION_POOLS:
                        self.assertEqual(error.code, "POOL_FORBIDDEN_FOR_TOKEN_SPEND")
                    elif not credit and amount > snapshot[pool]:
                        self.assertEqual(error.code, "POOL_EXHAUSTED_PAUSED")
                    continue
                if credit:
                    mirror[pool] += amount
                else:
                    mirror[pool] -= amount
                self.assertEqual(ledger.view()["balances"], mirror)
            view = ledger.view()
            for pool in CONTRACT_POOLS:
                credits = sum(item["amount"] for item in view["credits"] if item["pool"] == pool)
                spends = sum(item["amount"] for item in view["spends"] if item["pool"] == pool)
                self.assertEqual(view["balances"][pool], credits - spends)
                self.assertEqual(view["balances"][pool], mirror[pool])


class CollateralPropertyTests(unittest.TestCase):
    """TL0-TK12-T1. Author-side. Not an independent verification."""

    def _recognized(self, items):
        total = 0
        for item in items:
            if item["kind"] in {"KRW_GUARANTEE", "ESCROW"}:
                total += item["amount"]
        return total

    def test_TL4_TK12_recognition_is_krw_sum_and_permutation_invariant(self):
        for seed in SEEDS:
            random = rng(seed)
            items = []
            for index in range(1 + random.randrange(4)):
                kind = ("KRW_GUARANTEE", "ESCROW", "TOKEN")[random.randrange(3)]
                items.append({"kind": kind, "amount": 1 + random.randrange(40)})
            krw_items = [item for item in items if item["kind"] != "TOKEN"]
            if not krw_items and any(item["kind"] == "TOKEN" for item in items):
                self.assertEqual(
                    codes(lambda items=items: collateral_recognized(50, items)),
                    "TOKEN_ONLY_COLLATERAL_REJECTED",
                )
                continue
            expected = self._recognized(items)
            results = []
            for order in itertools.permutations(items):
                recognized = collateral_recognized(50, list(order))
                results.append(recognized["recognized_krw"])
                self.assertEqual(recognized["recognized_krw"], expected)
                self.assertEqual(recognized["token_recognized"], 0)
                self.assertEqual(recognized["currency"], "KRW")
            self.assertEqual(len(set(results)), 1)

    def test_TL4_TK12_token_item_does_not_change_recognition(self):
        base = [
            {"kind": "KRW_GUARANTEE", "amount": 30},
            {"kind": "ESCROW", "amount": 12},
        ]
        without = collateral_recognized(80, base)
        with_token = collateral_recognized(80, base + [{"kind": "TOKEN", "amount": 999}])
        self.assertEqual(without["recognized_krw"], 42)
        self.assertEqual(with_token["recognized_krw"], without["recognized_krw"])
        self.assertEqual(with_token["token_recognized"], 0)
        self.assertEqual(
            codes(lambda: collateral_recognized(80, [{"kind": "TOKEN", "amount": 999}])),
            "TOKEN_ONLY_COLLATERAL_REJECTED",
        )

    def test_TL4_TK12_any_valuation_key_is_refused(self):
        for seed in SEEDS:
            random = rng(seed + 20)
            kind = ("KRW_GUARANTEE", "ESCROW", "TOKEN")[random.randrange(3)]
            items = [{"kind": kind, "amount": 5, "valuation": random.randrange(1, 9)}]
            self.assertEqual(
                codes(lambda items=items: collateral_recognized(10, items)),
                "PRICE_SOURCE_UNDEFINED",
            )


class BudgetAndRewardIdTests(unittest.TestCase):
    def test_TL4_budget_matches_floor_formula_and_is_monotone(self):
        for seed in SEEDS:
            random = rng(seed)
            for _ in range(12):
                cap = random.randrange(0, 400)
                numerator = random.randrange(0, 8)
                denominator = 1 + random.randrange(9)
                residual = random.randrange(0, 400)
                periods = 1 + random.randrange(6)
                other_periods = 1 + random.randrange(6)
                got = reward_budget(
                    cap=cap,
                    ratio_numerator=numerator,
                    ratio_denominator=denominator,
                    net_residual=residual,
                    periods=periods,
                )
                self.assertEqual(got, oracle_budget(cap, numerator, denominator, residual))
                again = reward_budget(
                    cap=cap,
                    ratio_numerator=numerator,
                    ratio_denominator=denominator,
                    net_residual=residual,
                    periods=other_periods,
                )
                self.assertEqual(again, got)
                if residual < 400 and cap < 400:
                    higher_residual = reward_budget(
                        cap=cap,
                        ratio_numerator=numerator,
                        ratio_denominator=denominator,
                        net_residual=residual + 1,
                        periods=periods,
                    )
                    higher_cap = reward_budget(
                        cap=cap + 1,
                        ratio_numerator=numerator,
                        ratio_denominator=denominator,
                        net_residual=residual,
                        periods=periods,
                    )
                    self.assertGreaterEqual(higher_residual, got)
                    self.assertGreaterEqual(higher_cap, got)

    def test_TL4_in_window_revenue_is_excluded_from_the_net_residual(self):
        for seed in SEEDS:
            random = rng(seed + 3)
            gross = 20 + random.randrange(80)
            in_window = random.randrange(gross + 1)
            deposit = random.randrange(5)
            settlement = random.randrange(5)
            reserve = random.randrange(5)
            operating = random.randrange(5)
            loss = random.randrange(5)
            deductions = deposit + settlement + reserve + operating + loss
            if deductions > gross - in_window:
                continue
            residual = net_residual_revenue(
                gross_revenue=gross,
                refundable_window_revenue=in_window,
                customer_deposit_outlay=deposit,
                organizer_settlement_outlay=settlement,
                refund_reserve_outlay=reserve,
                operating_cost=operating,
                loss_provision=loss,
            )
            self.assertEqual(residual, oracle_residual(gross, in_window, deductions))
            self.assertLessEqual(residual, gross - in_window)
            if in_window < gross and deductions <= gross - (in_window + 1):
                smaller = net_residual_revenue(
                    gross_revenue=gross,
                    refundable_window_revenue=in_window + 1,
                    customer_deposit_outlay=deposit,
                    organizer_settlement_outlay=settlement,
                    refund_reserve_outlay=reserve,
                    operating_cost=operating,
                    loss_provision=loss,
                )
                self.assertEqual(smaller, residual - 1)

    def test_TL4_reward_id_ignores_rule_version_and_does_not_collide(self):
        self.assertNotIn("rule_version", reward_id.__code__.co_varnames)
        base = {
            "program": "program-1",
            "source_op_id": "op-1",
            "recipient": "recipient-1",
            "kind": "participation",
        }
        original = reward_id(**base)
        self.assertEqual(original, reward_id(**base))
        for field in ("program", "source_op_id", "recipient", "kind"):
            changed = dict(base)
            changed[field] = base[field] + "-x"
            self.assertNotEqual(original, reward_id(**changed))
        self.assertNotEqual(
            reward_id(program="a,b", source_op_id="c", recipient="d", kind="e"),
            reward_id(program="a", source_op_id="b,c", recipient="d", kind="e"),
        )
        alphabet = ("a", "b", '"', ",", "가", "a" * 100, "a,b", "b,a")
        seen = {}
        for program, source, recipient, kind in itertools.product(alphabet, repeat=4):
            key = (program, source, recipient, kind)
            derived = reward_id(program=program, source_op_id=source, recipient=recipient, kind=kind)
            previous = seen.get(derived)
            self.assertIsNone(previous)
            seen[derived] = key
        self.assertEqual(len(seen), len(alphabet) ** 4)


class SupplyPropertyTests(unittest.TestCase):
    """V6. Author-side. TL0-TK05-T1's V1–V5 are not verifiable without a package."""

    def test_TL4_V6_random_streams_match_the_rederived_oracle(self):
        ops = ("MINT", "ALLOCATE", "BURN", "HOLDER_BURN")
        for seed in SEEDS:
            random = rng(seed)
            events = []
            for index in range(SUPPLY_STREAM_LENGTH):
                op = ops[random.randrange(len(ops))]
                approved = random.randrange(2) == 0
                path_approved = random.randrange(2) == 0
                if op == "HOLDER_BURN":
                    events.append(
                        _event(
                            "e-%s-%s" % (seed, index),
                            op,
                            1 + random.randrange(6),
                            approved=False,
                            path_approved=path_approved,
                            program=None,
                        )
                    )
                else:
                    events.append(
                        _event(
                            "e-%s-%s" % (seed, index),
                            op,
                            1 + random.randrange(6),
                            approved=approved,
                            path_approved=path_approved,
                        )
                    )
            if random.randrange(3) == 0 and events:
                events.append(dict(events[0]))
            _compare_supply(self, events)

    def test_TL4_V6_allocate_does_not_change_layer_supply(self):
        first = _event("mint-1", "MINT", 9)
        report = _compare_supply(self, [first])
        self.assertEqual(report["layer_supply"], 9)
        after = _compare_supply(self, [first, _event("alloc-1", "ALLOCATE", 4)])
        self.assertEqual(after["layer_supply"], report["layer_supply"])
        self.assertEqual(after["allocated_total"], 4)

    def test_TL4_V6_tamper_duplicate_holder_and_stop_payout(self):
        events = [
            _event("mint-1", "MINT", 10),
            _event("alloc-1", "ALLOCATE", 3),
            _event("burn-1", "BURN", 2),
        ]
        report = _compare_supply(self, events)
        self.assertEqual(report["layer_supply"], 8)
        orders = list(itertools.permutations(events[:2]))
        totals = []
        for order in orders:
            permuted = _compare_supply(self, list(order))
            totals.append((permuted["minted_total"], permuted["allocated_total"], permuted["layer_supply"]))
        self.assertEqual(len(set(totals)), 1)
        for field in SUPPLY_REPORT_FIELDS:
            tampered = dict(report)
            tampered["events"] = list(report["events"])
            if field == "layer_supply":
                tampered[field] = report[field] + 1
            elif isinstance(report[field], int):
                tampered[field] = report[field] + 1
            else:
                continue
            self.assertEqual(codes(lambda tampered=tampered: reconcile_supply(tampered, tampered["layer_supply"])), "SUPPLY_REPORT_MISMATCH")
        self.assertEqual(codes(lambda: supply_report([events[0], dict(events[0])])), "SUPPLY_EVENT_DUPLICATE")

        unapproved = _compare_supply(self, events + [_event("mint-x", "MINT", 3, approved=False)])
        minted = reconcile_supply(unapproved, unapproved["layer_supply"])
        self.assertEqual(minted["alarm"], "UNAPPROVED_MINT")
        self.assertTrue(minted["stop_payout"])
        self.assertTrue(minted["mismatch"])

        bad_path = _compare_supply(self, [_event("mint-p", "MINT", 10, path_approved=False)])
        path = reconcile_supply(bad_path, bad_path["layer_supply"])
        self.assertEqual(path["alarm"], "UNAPPROVED_PATH")
        self.assertTrue(path["stop_payout"])

        both = _compare_supply(
            self,
            [
                _event("mint-b", "MINT", 4, approved=False, path_approved=False),
            ],
        )
        both_alarm = reconcile_supply(both, both["layer_supply"])
        self.assertIn(both_alarm["alarm"], {"UNAPPROVED_MINT", "UNAPPROVED_PATH"})
        self.assertTrue(both_alarm["stop_payout"])

        holder = _compare_supply(
            self,
            [
                _event("mint-h", "MINT", 10),
                _event("hold-1", "HOLDER_BURN", 2, approved=False, program=None),
            ],
        )
        self.assertEqual(holder["layer_supply"], 10)
        chain = holder["layer_supply"] - holder["holder_burn_outside_layer"]
        noted = reconcile_supply(holder, chain)
        self.assertEqual(noted["alarm"], "HOLDER_BURN_OUTSIDE_LAYER")
        self.assertFalse(noted["mismatch"])
        self.assertFalse(noted["stop_payout"])

        matched = reconcile_supply(report, report["layer_supply"])
        self.assertEqual(matched["alarm"], "MATCH")
        self.assertFalse(matched["stop_payout"])
        unexplained = reconcile_supply(report, report["layer_supply"] - 1)
        self.assertEqual(unexplained["alarm"], "UNEXPLAINED")
        self.assertFalse(unexplained["stop_payout"])
        self.assertTrue(unexplained["mismatch"])
        self.assertEqual(matched["stop_payout"], matched["alarm"] in {"UNAPPROVED_MINT", "UNAPPROVED_PATH"})
        self.assertEqual(minted["stop_payout"], minted["alarm"] in {"UNAPPROVED_MINT", "UNAPPROVED_PATH"})
        self.assertEqual(path["stop_payout"], path["alarm"] in {"UNAPPROVED_MINT", "UNAPPROVED_PATH"})
        self.assertEqual(noted["stop_payout"], noted["alarm"] in {"UNAPPROVED_MINT", "UNAPPROVED_PATH"})
        self.assertEqual(unexplained["stop_payout"], unexplained["alarm"] in {"UNAPPROVED_MINT", "UNAPPROVED_PATH"})


if __name__ == "__main__":
    unittest.main()
