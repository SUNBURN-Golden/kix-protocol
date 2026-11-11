"""In-process tests for the synthetic local payment effect session.

Every test initializes through an explicit fixture and the published Core
commands. No test Harness defaults, state injection or value inference is used.
``send_effect`` is asserted only as a stored local intent, never as transmission.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.payment_effects.payment_effect_fixture import (
    FixtureError,
    decode_json,
    load_fixture,
    session_from_fixture,
    validate_fixture,
)
from reference.payment_effects.payment_effect_session import (
    Core,
    EFFECT_ACTIONS,
    PaymentEffectLocalError,
    PaymentEffectSession,
    PaymentEffectSessionClosed,
    Rejected,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DOMAIN = "kix:fixture:lifecycle:0.3"
SCOPE = {
    "provider": "toss",
    "environment": "test",
    "merchant": "kix-fixture",
    "channel": "card",
}
POOL = "96fe3c4385b2d190258525c12e2b6315093b90733c62bcd19e19ce00db3aea6a"
POOL_ACCOUNT = "funds:" + POOL
PAYMENT = "pay-primary"
BUYER = "A"
ORGANIZER = "organizer"


def read_fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_text(encoding="utf-8"))


def direct_core(fixture):
    core = Core(":memory:")
    for command in fixture["setup"]:
        core.execute(
            command["operationId"],
            command["actor"],
            command["action"],
            copy.deepcopy(command["body"]),
        )
    return core


def prepare_cash_refund(effect_id="refund-primary", amount=100000):
    return {
        "domain": DOMAIN,
        "effectId": effect_id,
        "tradeId": "primary",
        "kind": "REFUND",
        "amount": amount,
        "routeProfile": "CASH_REFUND_FIXTURE",
        "contractRef": "fixture:cash-refund:v1",
        "beneficiaryAccountRef": "fixture-account:" + BUYER,
    }


def prepare_payout(effect_id, allocation, amount, beneficiary=ORGANIZER):
    return {
        "domain": DOMAIN,
        "effectId": effect_id,
        "tradeId": "primary",
        "kind": "PAYOUT",
        "amount": amount,
        "allocationId": allocation,
        "routeProfile": "BANK_PAYOUT_FIXTURE",
        "contractRef": "fixture:payout:v1",
        "beneficiaryAccountRef": "fixture-account:" + beneficiary,
    }


def prepare_pg_cancel(effect_id="cancel-primary", amount=100000):
    return {
        "domain": DOMAIN,
        "effectId": effect_id,
        "tradeId": "primary",
        "kind": "REFUND",
        "amount": amount,
        "routeProfile": "PG_ORIGINAL_CANCEL_FIXTURE",
        "contractRef": "fixture:pg-cancel:v1",
    }


def send(effect_id):
    return {"domain": DOMAIN, "effectId": effect_id}


def observe(
    effect_id,
    phase,
    amount,
    *,
    beneficiary=BUYER,
    status=None,
    movement_id=None,
    source_id=None,
    provider_operation_id=None,
    payment_id=PAYMENT,
):
    body = {
        "domain": DOMAIN,
        "scope": dict(SCOPE),
        "provenance": "synthetic",
        "effectId": effect_id,
        "phase": phase,
        "sourceId": source_id or effect_id + "-" + phase.lower(),
        "providerOperationId": provider_operation_id or "provider-" + effect_id,
        "amount": amount,
        "currency": "KRW",
        "beneficiary": beneficiary,
        "paymentId": payment_id,
    }
    if status is not None:
        body["status"] = status
    if movement_id is not None:
        body["movementId"] = movement_id
    return body


def selected_state(snapshot, effect_ids, trade_ids, accounts):
    return {
        "effects": {
            effect_id: (
                copy.deepcopy(snapshot["effects"][effect_id])
                if effect_id in snapshot["effects"]
                else None
            )
            for effect_id in effect_ids
        },
        "trades": {
            trade_id: (
                copy.deepcopy(snapshot["trades"][trade_id])
                if trade_id in snapshot["trades"]
                else None
            )
            for trade_id in trade_ids
        },
        "balances": {
            account: snapshot["balances"].get(account, 0) for account in accounts
        },
    }


class FixtureValidationTests(unittest.TestCase):
    def test_valid_documents_are_accepted_without_creating_a_core(self):
        for name in (
            "cash_refund",
            "payout",
            "original_cancel",
            "unsettled_refund",
        ):
            with self.subTest(fixture=name):
                validate_fixture(read_fixture(name))

    def test_malformed_documents_are_refused_before_initialization(self):
        base = read_fixture("cash_refund")

        wrong_version = copy.deepcopy(base)
        wrong_version["fixture_version"] = 2
        duplicate = copy.deepcopy(base)
        duplicate["setup"].append(copy.deepcopy(duplicate["setup"][0]))
        empty = copy.deepcopy(base)
        empty["setup"] = []
        wrong_provenance = copy.deepcopy(base)
        wrong_provenance["provenance"] = "synthetic-but-not-really"
        extra_top = copy.deepcopy(base)
        extra_top["note"] = "not allowed"
        bad_action = copy.deepcopy(base)
        bad_action["setup"][0]["action"] = "delegate"
        bad_body = copy.deepcopy(base)
        bad_body["setup"][0]["body"] = []
        bad_actor = copy.deepcopy(base)
        bad_actor["setup"][0]["actor"] = 7

        for name, document in (
            ("wrong_version", wrong_version),
            ("duplicate_operation", duplicate),
            ("empty_setup", empty),
            ("wrong_provenance", wrong_provenance),
            ("extra_top_field", extra_top),
            ("unsupported_action", bad_action),
            ("non_object_body", bad_body),
            ("non_string_actor", bad_actor),
        ):
            with self.subTest(case=name):
                with self.assertRaises(FixtureError):
                    validate_fixture(document)

    def test_strict_json_rejects_duplicate_keys_and_non_finite_numbers(self):
        with self.assertRaises(FixtureError):
            decode_json('{"a":1,"a":2}')
        with self.assertRaises(FixtureError):
            decode_json('{"a":NaN}')
        with self.assertRaises(FixtureError):
            decode_json('[1e999]')

    def test_rejected_setup_publishes_no_session(self):
        fixture = {
            "fixture_version": 1,
            "provenance": "synthetic",
            "setup": [
                {
                    "operationId": "no-trade",
                    "actor": "pg-adapter",
                    "action": "capture",
                    "body": {
                        "domain": DOMAIN,
                        "scope": dict(SCOPE),
                        "provenance": "synthetic",
                        "tradeId": "missing",
                        "orderId": "order-missing",
                        "paymentId": "pay-missing",
                        "amount": 100000,
                        "currency": "KRW",
                        "buyer": BUYER,
                    },
                }
            ],
        }
        with self.assertRaisesRegex(Rejected, "TRADE_NOT_FOUND"):
            session_from_fixture(fixture)
        # A failed initialization leaves no global state: a fresh fixture works.
        session = session_from_fixture(read_fixture("cash_refund"))
        try:
            self.assertIsNotNone(session.view(
                effect_ids=[], trade_ids=["primary"], accounts=[]
            )["trades"]["primary"])
        finally:
            session.close()


class SessionExecutionTests(unittest.TestCase):
    def test_cash_refund_receipts_and_views_match_direct_core(self):
        fixture = read_fixture("cash_refund")
        session = session_from_fixture(copy.deepcopy(fixture))
        direct = direct_core(fixture)
        try:
            commands = (
                (
                    "cash-1-prepare",
                    "operator",
                    "prepare_effect",
                    prepare_cash_refund(),
                ),
                ("cash-2-send", "operator", "send_effect", send("refund-primary")),
                (
                    "cash-3-status",
                    "pg-adapter",
                    "observe_effect",
                    observe("refund-primary", "STATUS", 100000, status="SUCCESS"),
                ),
                (
                    "cash-4-funds",
                    "pg-adapter",
                    "observe_effect",
                    observe(
                        "refund-primary",
                        "FUNDS",
                        100000,
                        movement_id="movement-refund-primary",
                    ),
                ),
            )
            selectors = {
                "effect_ids": ["refund-primary"],
                "trade_ids": ["primary"],
                "accounts": [POOL_ACCOUNT, "refund:primary", "in_transit:refund-primary"],
            }
            for operation_id, actor, action, body in commands:
                expected = direct.execute(
                    operation_id, actor, action, copy.deepcopy(body)
                )
                self.assertEqual(
                    session.execute(operation_id, actor, action, body), expected
                )
                self.assertEqual(
                    session.view(**selectors),
                    selected_state(
                        direct.snapshot(),
                        selectors["effect_ids"],
                        selectors["trade_ids"],
                        selectors["accounts"],
                    ),
                )

            final = session.view(**selectors)
            self.assertEqual(final["effects"]["refund-primary"]["state"], "DONE")
            self.assertEqual(final["effects"]["refund-primary"]["appliedAmount"], 100000)
            self.assertEqual(final["trades"]["primary"]["refunded"], 100000)
            self.assertEqual(final["balances"], {account: 0 for account in selectors["accounts"]})
        finally:
            session.close()
            direct.db.close()

    def test_payout_funds_before_status(self):
        session = session_from_fixture(read_fixture("payout"))
        selectors = {
            "effect_ids": ["payout-primary-0"],
            "trade_ids": ["primary"],
            "accounts": [
                POOL_ACCOUNT,
                "payable:primary-0",
                "payable:primary-1",
                "in_transit:payout-primary-0",
            ],
        }
        try:
            session.execute(
                "payout-prepare",
                "operator",
                "prepare_effect",
                prepare_payout("payout-primary-0", "primary-0", 95000),
            )
            session.execute(
                "payout-send", "operator", "send_effect", send("payout-primary-0")
            )

            first = session.execute(
                "payout-funds",
                "pg-adapter",
                "observe_effect",
                observe(
                    "payout-primary-0",
                    "FUNDS",
                    95000,
                    beneficiary=ORGANIZER,
                    movement_id="movement-payout-primary-0",
                ),
            )
            self.assertEqual(
                first["result"],
                {
                    "state": "OUTCOME_UNKNOWN",
                    "confirmed": False,
                    "fundsObserved": True,
                    "review": False,
                },
            )
            partial = session.view(**selectors)["effects"]["payout-primary-0"]
            self.assertEqual(partial["fundsAmount"], 95000)
            self.assertEqual(partial["confirmedAmount"], 0)
            self.assertEqual(partial["appliedAmount"], 0)

            second = session.execute(
                "payout-status",
                "pg-adapter",
                "observe_effect",
                observe(
                    "payout-primary-0",
                    "STATUS",
                    95000,
                    beneficiary=ORGANIZER,
                    status="SUCCESS",
                ),
            )
            self.assertEqual(second["result"]["state"], "DONE")
            view = session.view(**selectors)
            effect = view["effects"]["payout-primary-0"]
            self.assertEqual(effect["confirmed"], True)
            self.assertEqual(effect["fundsObserved"], True)
            self.assertEqual(effect["appliedAmount"], 95000)
            allocations = {
                item["id"]: item["paid"]
                for item in view["trades"]["primary"]["allocations"]
            }
            self.assertEqual(allocations, {"primary-0": 95000, "primary-1": 0})
            self.assertEqual(
                view["balances"],
                {
                    POOL_ACCOUNT: 5000,
                    "payable:primary-0": 0,
                    "payable:primary-1": -5000,
                    "in_transit:payout-primary-0": 0,
                },
            )
        finally:
            session.close()

    def test_status_before_funds_and_duplicate_observations(self):
        session = session_from_fixture(read_fixture("cash_refund"))
        try:
            session.execute(
                "prepare-1",
                "operator",
                "prepare_effect",
                prepare_cash_refund(),
            )
            session.execute("send-1", "operator", "send_effect", send("refund-primary"))

            status = observe(
                "refund-primary", "STATUS", 100000, status="SUCCESS",
                source_id="status-once",
            )
            first = session.execute("status-1", "pg-adapter", "observe_effect", status)
            self.assertEqual(
                first["result"],
                {
                    "state": "OUTCOME_UNKNOWN",
                    "confirmed": True,
                    "fundsObserved": False,
                    "review": False,
                },
            )
            duplicate = session.execute(
                "status-dup", "pg-adapter", "observe_effect", status
            )
            self.assertEqual(duplicate["result"], {"duplicate": True})

            funds = observe(
                "refund-primary",
                "FUNDS",
                100000,
                movement_id="movement-once",
                source_id="funds-once",
            )
            done = session.execute("funds-1", "pg-adapter", "observe_effect", funds)
            self.assertEqual(done["result"]["state"], "DONE")
            duplicate_funds = session.execute(
                "funds-dup", "pg-adapter", "observe_effect", funds
            )
            self.assertEqual(duplicate_funds["result"], {"duplicate": True})

            # A fresh source identifier for an already-applied movement is still
            # a duplicate funds fact, not a second debit.
            remint = dict(funds, sourceId="funds-reminted")
            duplicate_movement = session.execute(
                "funds-remint", "pg-adapter", "observe_effect", remint
            )
            self.assertEqual(duplicate_movement["result"], {"duplicate": True})

            view = session.view(
                effect_ids=["refund-primary"],
                trade_ids=["primary"],
                accounts=[POOL_ACCOUNT, "refund:primary", "in_transit:refund-primary"],
            )
            self.assertEqual(view["effects"]["refund-primary"]["fundsAmount"], 100000)
            self.assertEqual(view["trades"]["primary"]["refunded"], 100000)
            self.assertEqual(view["balances"], {POOL_ACCOUNT: 0, "refund:primary": 0, "in_transit:refund-primary": 0})
        finally:
            session.close()

    def test_conflicting_observation_and_operation_bodies_are_refused(self):
        session = session_from_fixture(read_fixture("cash_refund"))
        selectors = {
            "effect_ids": ["refund-primary"],
            "trade_ids": ["primary"],
            "accounts": [POOL_ACCOUNT, "refund:primary"],
        }
        try:
            body = prepare_cash_refund()
            session.execute("prep", "operator", "prepare_effect", body)
            session.execute("send", "operator", "send_effect", send("refund-primary"))

            before = session.view(**selectors)
            with self.assertRaisesRegex(Rejected, "EFFECT_BINDING_MISMATCH"):
                session.execute(
                    "wrong-amount",
                    "pg-adapter",
                    "observe_effect",
                    observe("refund-primary", "STATUS", 110000, status="SUCCESS"),
                )
            self.assertEqual(session.view(**selectors), before)

            accepted = observe(
                "refund-primary",
                "STATUS",
                100000,
                status="SUCCESS",
                source_id="status-source",
            )
            session.execute("status-ok", "pg-adapter", "observe_effect", accepted)
            with self.assertRaisesRegex(Rejected, "SOURCE_EVIDENCE_CONFLICT"):
                session.execute(
                    "status-conflict",
                    "pg-adapter",
                    "observe_effect",
                    dict(accepted, status="FAILED"),
                )

            # Replaying an operation identifier with a different body is refused
            # before any state changes.
            with self.assertRaisesRegex(Rejected, "OPERATION_ID_CONFLICT"):
                session.execute(
                    "prep", "operator", "prepare_effect",
                    prepare_cash_refund(amount=90000),
                )
            with self.assertRaisesRegex(Rejected, "EFFECT_EXISTS"):
                session.execute(
                    "prep-second", "operator", "prepare_effect", body
                )
            self.assertEqual(
                session.view(**selectors)["effects"]["refund-primary"]["amount"],
                100000,
            )
        finally:
            session.close()

    def test_insufficient_confirmed_funds_changes_nothing_and_can_retry(self):
        session = session_from_fixture(read_fixture("unsettled_refund"))
        selectors = {
            "effect_ids": ["refund-primary", "cancel-primary"],
            "trade_ids": ["primary"],
            "accounts": [POOL_ACCOUNT, "refund:primary", "pg:primary", "pg_cancel_due:primary"],
        }
        try:
            before = session.view(**selectors)
            # Captured but unsettled cash is not confirmed pool funds.
            with self.assertRaisesRegex(Rejected, "INSUFFICIENT_CONFIRMED_FUNDS"):
                session.execute(
                    "unsettled-prepare",
                    "operator",
                    "prepare_effect",
                    prepare_cash_refund(),
                )
            self.assertEqual(session.view(**selectors), before)

            # The rejected operation left no command record; the same identifier
            # can describe a different, valid local intent.
            prepared = session.execute(
                "unsettled-prepare",
                "operator",
                "prepare_effect",
                prepare_pg_cancel(),
            )
            self.assertEqual(
                prepared["result"]["fundingBasis"],
                "ORIGINAL_PAYMENT_AND_PG_LIABILITY",
            )
            session.execute(
                "cancel-send", "operator", "send_effect", send("cancel-primary")
            )
            view = session.view(**selectors)
            self.assertIsNone(view["effects"]["refund-primary"])
            self.assertEqual(view["effects"]["cancel-primary"]["state"], "OUTCOME_UNKNOWN")
            self.assertEqual(view["balances"][POOL_ACCOUNT], 0)
            self.assertEqual(view["balances"]["pg:primary"], 100000)
        finally:
            session.close()

    def test_partial_observations_stay_unknown_until_bounded(self):
        session = session_from_fixture(read_fixture("cash_refund"))
        selectors = {
            "effect_ids": ["refund-primary"],
            "trade_ids": ["primary"],
            "accounts": [POOL_ACCOUNT, "refund:primary", "in_transit:refund-primary"],
        }
        try:
            session.execute(
                "partial-prepare", "operator", "prepare_effect", prepare_cash_refund()
            )
            session.execute(
                "partial-send", "operator", "send_effect", send("refund-primary")
            )

            session.execute(
                "partial-status-1",
                "pg-adapter",
                "observe_effect",
                observe(
                    "refund-primary",
                    "STATUS",
                    40000,
                    status="SUCCESS",
                    source_id="partial-status-source-1",
                ),
            )
            effect = session.view(**selectors)["effects"]["refund-primary"]
            self.assertEqual(effect["state"], "OUTCOME_UNKNOWN")
            self.assertEqual(effect["confirmedAmount"], 40000)
            self.assertEqual(effect["appliedAmount"], 0)

            session.execute(
                "partial-funds-1",
                "pg-adapter",
                "observe_effect",
                observe(
                    "refund-primary",
                    "FUNDS",
                    40000,
                    movement_id="movement-part-1",
                    source_id="partial-funds-source-1",
                ),
            )
            view = session.view(**selectors)
            effect = view["effects"]["refund-primary"]
            self.assertEqual(effect["state"], "OUTCOME_UNKNOWN")
            self.assertEqual(effect["fundsAmount"], 40000)
            self.assertEqual(effect["appliedAmount"], 40000)
            self.assertEqual(view["balances"][POOL_ACCOUNT], 60000)
            self.assertEqual(view["balances"]["refund:primary"], -60000)

            # STATUS is cumulative; the final success does not itself release
            # the remaining cash obligation without an observed movement.
            session.execute(
                "partial-status-2",
                "pg-adapter",
                "observe_effect",
                observe(
                    "refund-primary",
                    "STATUS",
                    100000,
                    status="SUCCESS",
                    source_id="partial-status-source-2",
                ),
            )
            effect = session.view(**selectors)["effects"]["refund-primary"]
            self.assertEqual(effect["state"], "OUTCOME_UNKNOWN")
            self.assertEqual(effect["appliedAmount"], 40000)

            session.execute(
                "partial-funds-2",
                "pg-adapter",
                "observe_effect",
                observe(
                    "refund-primary",
                    "FUNDS",
                    60000,
                    movement_id="movement-part-2",
                    source_id="partial-funds-source-2",
                ),
            )
            view = session.view(**selectors)
            self.assertEqual(view["effects"]["refund-primary"]["state"], "DONE")
            self.assertEqual(view["effects"]["refund-primary"]["appliedAmount"], 100000)
            self.assertEqual(view["trades"]["primary"]["refunded"], 100000)
            self.assertEqual(
                view["balances"],
                {POOL_ACCOUNT: 0, "refund:primary": 0, "in_transit:refund-primary": 0},
            )

            with self.assertRaisesRegex(
                Rejected, "SECOND_FUNDS_MOVEMENT_REQUIRES_REVIEW"
            ):
                session.execute(
                    "partial-funds-over",
                    "pg-adapter",
                    "observe_effect",
                    observe("refund-primary", "FUNDS", 1, movement_id="movement-over"),
                )
        finally:
            session.close()

    def test_abort_is_refused_for_a_sent_unknown_effect(self):
        session = session_from_fixture(read_fixture("payout"))
        selectors = {
            "effect_ids": ["payout-primary-0", "payout-primary-1"],
            "trade_ids": ["primary"],
            "accounts": [POOL_ACCOUNT, "payable:primary-0", "payable:primary-1"],
        }
        try:
            session.execute(
                "unsent-prepare",
                "operator",
                "prepare_effect",
                prepare_payout("payout-primary-0", "primary-0", 95000),
            )
            aborted = session.execute(
                "unsent-abort",
                "operator",
                "abort_effect",
                send("payout-primary-0"),
            )
            self.assertEqual(aborted["result"], {"state": "ABORTED"})

            session.execute(
                "sent-prepare",
                "operator",
                "prepare_effect",
                prepare_payout(
                    "payout-primary-1", "primary-1", 5000, beneficiary="platform"
                ),
            )
            session.execute(
                "sent-send", "operator", "send_effect", send("payout-primary-1")
            )
            before = session.view(**selectors)
            with self.assertRaisesRegex(
                Rejected, "SENT_EFFECT_CANNOT_RELEASE_BY_TIMEOUT"
            ):
                session.execute(
                    "sent-abort",
                    "operator",
                    "abort_effect",
                    send("payout-primary-1"),
                )
            self.assertEqual(session.view(**selectors), before)
            self.assertEqual(
                before["effects"]["payout-primary-1"]["state"], "OUTCOME_UNKNOWN"
            )
            self.assertEqual(
                before["effects"]["payout-primary-0"]["state"], "ABORTED"
            )
        finally:
            session.close()

    def test_views_are_detached_and_do_not_mutate_state(self):
        fixture = read_fixture("cash_refund")
        core = direct_core(fixture)
        session = PaymentEffectSession(core)
        try:
            session.execute(
                "read-prepare", "operator", "prepare_effect", prepare_cash_refund()
            )
            session.execute(
                "read-send", "operator", "send_effect", send("refund-primary")
            )
            before = core.snapshot()
            first = session.view(
                effect_ids=["refund-primary", "missing"],
                trade_ids=["primary"],
                accounts=[POOL_ACCOUNT, "refund:primary", "unknown:account"],
            )
            self.assertEqual(core.snapshot(), before)
            self.assertIsNone(first["effects"]["missing"])
            self.assertEqual(first["balances"]["unknown:account"], 0)

            first["effects"]["refund-primary"]["state"] = "TAMPERED"
            first["trades"]["primary"]["refunded"] = 1
            first["balances"][POOL_ACCOUNT] = -1
            second = session.view(
                effect_ids=["refund-primary"],
                trade_ids=["primary"],
                accounts=[POOL_ACCOUNT],
            )
            self.assertEqual(second["effects"]["refund-primary"]["state"], "OUTCOME_UNKNOWN")
            self.assertEqual(second["trades"]["primary"]["refunded"], 0)
            self.assertEqual(second["balances"][POOL_ACCOUNT], 100000)
        finally:
            session.close()

    def test_local_action_whitelist_does_not_reach_the_core(self):
        fixture = read_fixture("cash_refund")
        core = direct_core(fixture)
        session = PaymentEffectSession(core)
        try:
            with self.assertRaises(PaymentEffectLocalError):
                session.execute(
                    "not-an-effect", "operator", "commit_trade",
                    {"domain": DOMAIN, "tradeId": "primary"},
                )
            control = direct_core(fixture)
            try:
                expected = control.snapshot()
            finally:
                control.db.close()
            self.assertEqual(core.snapshot(), expected)
            # The refused local action recorded nothing; the identifier is free.
            session.execute(
                "not-an-effect", "operator", "prepare_effect", prepare_cash_refund()
            )
        finally:
            session.close()

    def test_close_is_idempotent_and_sessions_do_not_survive(self):
        session = load_fixture(FIXTURES / "cash_refund.json")
        session.close()
        session.close()
        with self.assertRaises(PaymentEffectSessionClosed):
            session.execute(
                "closed", "operator", "prepare_effect", prepare_cash_refund()
            )
        with self.assertRaises(PaymentEffectSessionClosed):
            session.view(effect_ids=[], trade_ids=[], accounts=[])

        with load_fixture(FIXTURES / "cash_refund.json") as managed:
            self.assertIsInstance(managed, PaymentEffectSession)
        with self.assertRaises(PaymentEffectSessionClosed):
            managed.view(effect_ids=[], trade_ids=[], accounts=[])

    def test_effect_action_set_is_exactly_the_published_commands(self):
        self.assertEqual(
            EFFECT_ACTIONS,
            {"prepare_effect", "send_effect", "abort_effect", "observe_effect"},
        )


if __name__ == "__main__":
    unittest.main()
