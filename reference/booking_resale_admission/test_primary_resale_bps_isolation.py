"""Builder-authored PF-C05 mock isolation evidence, not an independent PASS.

Contracts: MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md section 3 PF-C05 and section 2;
SETTLEMENT_DISTRIBUTION_F01_F03.md section 2 (under docs/contracts/).
Synthetic values, no 100000/500 fixture, no policy value selected.
The booking mock has no primary fee field; the settlement mock has no resale
field. These source-informed checks exercise that structural separation and
the existing ResaleMachine settlement gate, not chain enforcement or funds.
"""

import random
import sys
import unittest
from pathlib import Path

import mock_gates
import resale_fsm
from mock_gates import OFFER_WINDOW_MS, GateError, MockGates
from resale_fsm import ResaleError, ResaleMachine

_SETTLEMENT_DIR = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT_DIR) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT_DIR))

import mock_settlement  # noqa: E402
import settlement_fsm  # noqa: E402
from mock_settlement import MockSettlement, SettlementError  # noqa: E402
from settlement_fsm import SettlementMachine  # noqa: E402

# Existing admission HTTP tests later load the frozen core and change sys.path.
# Capture our import environment so this guard tests this module's imports,
# independently of the order in which other test bodies execute.
_IMPORT_PATHS = frozenset(Path(entry).resolve() for entry in sys.path)

RESALE_BPS = (
    (0, 0), (0, 10000), (10000, 0), (1, 9999),
    (9999, 1), (5000, 5000), (1, 1), (3333, 3333),
)
FEE_BPS = (0, 1, 9999, 10000)
PRICES = (1, 7_777, 10**12)
PF_C05_SEEDS = (41, 43, 47)
T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS
PAY = "ab" * 32
SALE_PAY = "cd" * 32


def policy(fee_bps):
    return dict(kind="PRIMARY_FEE_BPS", fee_bps=fee_bps,
                residual_payee="organizer", fee_payee="platform")


def code_of(fn, error_type):
    try:
        fn()
    except error_type as error:
        return error.code
    raise AssertionError(f"expected {error_type.__name__}")


def show_kwargs(price, organizer_bps, platform_bps):
    return dict(
        organizer_role="organizer", capacity=1, gate_roles=["gate-a"],
        primary_price=price, resale_cap=price, resale_allowed=True,
        organizer_bps=organizer_bps, platform_bps=platform_bps,
    )


def primary_flow(price, organizer_bps, platform_bps):
    gate = MockGates()
    gate.set_clock(T0)
    gate.register_show("show", **show_kwargs(price, organizer_bps, platform_bps))
    gate.reserve_slot("reserve", show_id="show", slot=0, buyer_role="seller",
                      expires_ms=EXPIRES)
    # Keep the wrong price within the money bounds, including at price=1.
    mismatch = code_of(lambda: gate.bind_order(
        "order", reservation_id="reserve", amount=price - 1 if price > 1 else 2,
    ), GateError)
    bound = gate.bind_order("order", reservation_id="reserve", amount=price)
    paid = gate.observe_payment_fact(PAY, order_id="order", amount=price)
    issued = gate.issue("right", order_id="order")
    for envelope in (bound, paid, issued):
        # Exclude exactly the show view's two input echoes; compare everything
        # else, including binding, payment, issue evidence and the right.
        assert envelope["show"]["organizer_bps"] == organizer_bps
        assert envelope["show"]["platform_bps"] == platform_bps
        del envelope["show"]["organizer_bps"]
        del envelope["show"]["platform_bps"]
    return mismatch, bound, paid, issued


def primary_claim(gross, fee_bps):
    book = MockSettlement()
    book.recognize_claim("claim", trade_id="trade", gross=gross,
                         debtor_role="fixture-merchant", policy=policy(fee_bps))
    return book.view("claim")


def committed_settlement(gross, fee_bps):
    book = SettlementMachine()
    book.initiate("claim", idempotency_key="init", trade_id="trade", gross=gross,
                  debtor_role="fixture-merchant", policy=policy(fee_bps))
    book.authorize("claim", idempotency_key="auth")
    book.capture("claim", idempotency_key="capture")
    # Statement components are independent of PRIMARY_FEE_BPS obligations;
    # keep amount=gross, fee=0 like test_resale_fsm.settlement_at.
    book.commit("claim", idempotency_key="commit", movement_id="movement",
                gross=gross, amount=gross, fee=0, tax=0, held=0, adjustment=0)
    return book


def adopt(machine, price, organizer_bps, platform_bps):
    return machine.adopt_issued(
        "right", idempotency_key="adopt", show_id="show", slot=0,
        buyer_role="seller", expires_ms=EXPIRES, order_id="order",
        amount=price, payment_ref=PAY,
        **show_kwargs(price, organizer_bps, platform_bps),
    )


def resale_flow(price, organizer_bps, platform_bps, fee_bps):
    book = committed_settlement(price, fee_bps)
    machine = ResaleMachine(settlement_source=book)
    machine.set_clock("clock", idempotency_key="clock", now_ms=T0)
    adopt(machine, price, organizer_bps, platform_bps)
    listed = machine.list_resale(
        "listing", idempotency_key="list", right_id="right", version=1,
        seller_role="seller", recipient_role="buyer", amount=price,
        expires_ms=EXPIRES,
    )
    machine.observe_resale_payment(
        "listing", idempotency_key="pay", payment_ref=SALE_PAY,
        amount=price, buyer_role="buyer",
    )
    machine.bind_settlement("listing", idempotency_key="bind", settlement_id="claim")
    accepted = machine.accept_resale("transfer", idempotency_key="accept", listing_id="listing")
    return listed, accepted, machine.canonical_state(), book.view("claim")


class PrimaryResaleBpsIsolationPfC05Tests(unittest.TestCase):
    def check_binding(self, flow, price):
        mismatch, bound, paid, issued = flow
        self.assertEqual(mismatch, "PRIMARY_PRICE_MISMATCH")
        self.assertEqual(bound["order"]["amount"], price)
        self.assertEqual(paid["order"]["payment_ref"], PAY)
        self.assertEqual(issued["evidence"]["amount"], price)
        self.assertEqual(issued["right"]["last_amount"], price)
        self.assertEqual(issued["right"]["holder_role"], "seller")
        self.assertEqual(issued["right"]["version"], 1)
        for name in ("seller_due", "organizer_due", "platform_due"):
            self.assertNotIn(name, issued["evidence"])

    def check_split(self, claim, gross, fee_bps):
        fee = gross * fee_bps // 10000
        expected = {payee: face for payee, face in (
            ("organizer", gross - fee), ("platform", fee),
        ) if face}
        obligations = claim["obligations"]
        self.assertEqual({line["payee"]: line["face"] for line in obligations}, expected)
        self.assertEqual(len(obligations), len(expected))
        self.assertEqual(sum(line["face"] for line in obligations), gross)

    def check_resale(self, flow, price, organizer_bps, platform_bps, fee_bps):
        listed, accepted, _, claim = flow
        self.assertEqual(listed["listing"]["phase"], "LISTED")
        self.assertEqual(accepted["listing"]["phase"], "TRANSFERRED")
        self.assertIs(accepted["listing"]["mock_settlement_commit_observed"], True)
        self.assertEqual(accepted["right"]["holder_role"], "buyer")
        self.assertEqual(accepted["evidence"]["version_after"], 2)
        evidence = accepted["evidence"]
        organizer = price * organizer_bps // 10000
        platform = price * platform_bps // 10000
        self.assertEqual(
            (evidence["organizer_due"], evidence["platform_due"], evidence["seller_due"]),
            (organizer, platform, price - organizer - platform),
        )
        self.assertEqual(evidence["amount"], price)
        self.assertEqual(claim["phase"], "COMMITTED")
        self.assertEqual(claim["policy"], policy(fee_bps))

    def test_resale_bps_do_not_change_primary_binding(self):
        for price in PRICES:
            baseline = primary_flow(price, 0, 0)
            for o, p in RESALE_BPS:
                with self.subTest(price=price, organizer_bps=o, platform_bps=p):
                    flow = primary_flow(price, o, p)
                    self.check_binding(flow, price)
                    self.assertEqual(flow, baseline)

    def test_resale_bps_do_not_change_primary_fee_split(self):
        for price in PRICES:
            for fee_bps in FEE_BPS:
                baseline = primary_claim(price, fee_bps)
                for o, p in RESALE_BPS:
                    with self.subTest(price=price, fee_bps=fee_bps, organizer_bps=o, platform_bps=p):
                        issued = primary_flow(price, o, p)[3]
                        claim = primary_claim(issued["evidence"]["amount"], fee_bps)
                        self.check_split(claim, price, fee_bps)
                        self.assertEqual(claim["obligations"], baseline["obligations"])
        self.assertNotEqual(primary_claim(10**12, 0)["obligations"],
                            primary_claim(10**12, 10000)["obligations"])

    def test_primary_fee_bps_do_not_change_resale_list_and_accept(self):
        for price in PRICES:
            for o, p in RESALE_BPS:
                baseline = resale_flow(price, o, p, 0)
                for fee_bps in FEE_BPS:
                    with self.subTest(price=price, fee_bps=fee_bps, organizer_bps=o, platform_bps=p):
                        flow = resale_flow(price, o, p, fee_bps)
                        self.check_resale(flow, price, o, p, fee_bps)
                        # Entire listing/accept envelopes and canonical resale
                        # state match; the settlement source is checked separately.
                        self.assertEqual(flow[:3], baseline[:3])
        self.assertNotEqual(resale_flow(10**12, 0, 0, 0)[1]["evidence"],
                            resale_flow(10**12, 10000, 0, 0)[1]["evidence"])

    def test_resale_bps_sum_bound_independent_of_primary_fee(self):
        for price in PRICES:
            for fee_bps in FEE_BPS:
                # Includes fee=10000 and resale sum=10000: no combined cap.
                for o, p in ((0, 10000), (10000, 0), (1, 9999), (5000, 5000)):
                    with self.subTest(price=price, fee_bps=fee_bps, organizer_bps=o, platform_bps=p):
                        self.check_binding(primary_flow(price, o, p), price)
                        self.check_resale(resale_flow(price, o, p, fee_bps), price, o, p, fee_bps)
                for o, p, expected in ((10000, 1, "BPS_SUM"), (1, 10000, "BPS_SUM"),
                                       (5001, 5000, "BPS_SUM"), (10001, 0, "BPS")):
                    with self.subTest(price=price, fee_bps=fee_bps, organizer_bps=o, platform_bps=p):
                        gate = MockGates()
                        self.assertEqual(code_of(lambda: gate.register_show(
                            "show", **show_kwargs(price, o, p),
                        ), GateError), expected)
                        book = committed_settlement(price, fee_bps)
                        machine = ResaleMachine(settlement_source=book)
                        machine.set_clock("clock", idempotency_key="clock", now_ms=T0)
                        self.assertEqual(code_of(lambda: adopt(machine, price, o, p), ResaleError), expected)
            for o, p in RESALE_BPS:
                with self.subTest(price=price, organizer_bps=o, platform_bps=p, fee_bps=10001):
                    issued = primary_flow(price, o, p)[3]
                    gross = issued["evidence"]["amount"]
                    self.assertEqual(code_of(lambda: primary_claim(gross, 10001), SettlementError),
                                     "POLICY_FEE_BPS")
                    self.assertEqual(code_of(lambda: committed_settlement(gross, 10001), SettlementError),
                                     "POLICY_FEE_BPS")

    def test_seeded_isolation(self):
        for seed in PF_C05_SEEDS:
            r = random.Random(seed)
            for draw in range(20):
                price = r.randint(1, 10**12)
                fee_bps = r.randint(0, 10000)
                o = r.randint(0, 10000)
                p = r.randint(0, 10000 - o)
                with self.subTest(seed=seed, draw=draw, price=price, fee_bps=fee_bps,
                                  organizer_bps=o, platform_bps=p):
                    primary = primary_flow(price, o, p)
                    self.check_binding(primary, price)
                    self.assertEqual(primary, primary_flow(price, 0, 0))
                    claim = primary_claim(primary[3]["evidence"]["amount"], fee_bps)
                    self.check_split(claim, price, fee_bps)
                    baseline_gross = primary_flow(price, 0, 0)[3]["evidence"]["amount"]
                    self.assertEqual(claim["obligations"], primary_claim(baseline_gross, fee_bps)["obligations"])
                    resale = resale_flow(price, o, p, fee_bps)
                    self.check_resale(resale, price, o, p, fee_bps)
                    self.assertEqual(resale[:3], resale_flow(price, o, p, 0)[:3])


class PfC05SiblingImportPathTests(unittest.TestCase):
    def test_imports_resolve_from_suites(self):
        suite = Path(__file__).resolve().parent
        for module in (mock_gates, resale_fsm):
            self.assertEqual(Path(module.__file__).resolve().parent, suite)
        for module in (mock_settlement, settlement_fsm):
            self.assertEqual(Path(module.__file__).resolve().parent, _SETTLEMENT_DIR)
        self.assertNotIn(suite.parent / "v0.3-rc1", _IMPORT_PATHS)


if __name__ == "__main__":
    unittest.main()
