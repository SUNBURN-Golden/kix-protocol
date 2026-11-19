"""Real JSONL subprocess journeys for the synthetic local payment effect desk.

The journeys are run as separate processes against the published Core. Complete
receipts and selected views are compared with direct in-process Core execution.
``send_effect`` is only ever labelled a local intent; nothing is transmitted.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.payment_effects import payment_effect_cli as cli
from reference.payment_effects.payment_effect_fixture import (
    FixtureError,
    session_from_fixture,
)
from reference.payment_effects.payment_effect_session import (
    Core,
    PaymentEffectSessionClosed,
)

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
CLI_MODULE = "reference.payment_effects.payment_effect_cli"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
DOMAIN = "kix:fixture:lifecycle:0.3"
SCOPE = {
    "provider": "toss",
    "environment": "test",
    "merchant": "kix-fixture",
    "channel": "card",
}
POOL_ACCOUNT = (
    "funds:96fe3c4385b2d190258525c12e2b6315093b90733c62bcd19e19ce00db3aea6a"
)


def fixture_path(name):
    return FIXTURES / (name + ".json")


def journey_path(name):
    return FIXTURES / (name + ".jsonl")


def run_cli(fixture, requests, stdin_text=None):
    arguments = [
        sys.executable,
        "-B",
        "-m",
        CLI_MODULE,
        "--fixture",
        str(fixture),
    ]
    if stdin_text is None:
        arguments += ["--requests", str(requests)]
        return subprocess.run(
            arguments,
            cwd=ROOT,
            env=ENV,
            capture_output=True,
            text=True,
            timeout=120,
        )
    arguments += ["--requests", "-"]
    return subprocess.run(
        arguments,
        cwd=ROOT,
        env=ENV,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=120,
    )


def run_cli_bytes(fixture, requests):
    arguments = [
        sys.executable,
        "-B",
        "-m",
        CLI_MODULE,
        "--fixture",
        str(fixture),
        "--requests",
        str(requests),
    ]
    return subprocess.run(
        arguments,
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        timeout=120,
    )


def frames_of(proc):
    return [json.loads(line) for line in proc.stdout.splitlines()]


def read_journey(name):
    return [
        json.loads(line)
        for line in journey_path(name).read_text(encoding="utf-8").splitlines()
    ]


def read_fixture(name):
    return json.loads(fixture_path(name).read_text(encoding="utf-8"))


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


class JsonlJourneyTests(unittest.TestCase):
    def assert_envelope(self, frame):
        self.assertEqual(frame["evidenceClass"], "synthetic")
        self.assertIn("local intent", frame["notice"])
        self.assertIn("no provider", frame["notice"])
        self.assertIn("no provider, bank, chain or network transmission", frame["notice"])

    def test_cash_refund_journey(self):
        proc = run_cli(fixture_path("cash_refund"), journey_path("cash_refund"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        frames = frames_of(proc)
        self.assertEqual(len(frames), 6)
        for frame in frames:
            self.assert_envelope(frame)

        prepare = frames[0]["receipt"]
        self.assertEqual(prepare["action"], "prepare_effect")
        self.assertEqual(prepare["result"]["effectId"], "refund-primary")
        self.assertEqual(prepare["result"]["fundingBasis"], "CONFIRMED_POOL_CASH")
        self.assertEqual(frames[1]["receipt"]["result"]["dispatchDecision"], "FIRST_SEND_INTENT")

        after_send = frames[2]["view"]
        self.assertEqual(after_send["effects"]["refund-primary"]["state"], "OUTCOME_UNKNOWN")
        self.assertTrue(after_send["effects"]["refund-primary"]["sent"])
        self.assertEqual(after_send["balances"][POOL_ACCOUNT], 100000)
        self.assertEqual(after_send["balances"]["refund:primary"], -100000)

        status = frames[3]["receipt"]["result"]
        self.assertEqual(status["state"], "OUTCOME_UNKNOWN")
        self.assertTrue(status["confirmed"])
        self.assertFalse(status["fundsObserved"])
        self.assertEqual(frames[4]["receipt"]["result"]["state"], "DONE")

        final = frames[5]["view"]
        self.assertEqual(final["effects"]["refund-primary"]["state"], "DONE")
        self.assertEqual(final["effects"]["refund-primary"]["appliedAmount"], 100000)
        self.assertEqual(final["trades"]["primary"]["refunded"], 100000)
        self.assertEqual(
            final["balances"],
            {
                POOL_ACCOUNT: 0,
                "refund:primary": 0,
                "in_transit:refund-primary": 0,
                "pg:primary": 0,
            },
        )

    def test_payout_journey_funds_before_status(self):
        proc = run_cli(fixture_path("payout"), journey_path("payout"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        frames = frames_of(proc)
        self.assertEqual(len(frames), 5)
        for frame in frames:
            self.assert_envelope(frame)

        self.assertEqual(frames[0]["receipt"]["result"]["fundingBasis"], "CONFIRMED_POOL_CASH")
        self.assertEqual(frames[1]["receipt"]["result"]["dispatchDecision"], "FIRST_SEND_INTENT")
        funds = frames[2]["receipt"]["result"]
        self.assertEqual(
            funds,
            {
                "state": "OUTCOME_UNKNOWN",
                "confirmed": False,
                "fundsObserved": True,
                "review": False,
            },
        )
        self.assertEqual(frames[3]["receipt"]["result"]["state"], "DONE")

        view = frames[4]["view"]
        effect = view["effects"]["payout-primary-0"]
        self.assertEqual(effect["state"], "DONE")
        self.assertEqual(effect["appliedAmount"], 95000)
        allocations = {
            item["id"]: item["paid"] for item in view["trades"]["primary"]["allocations"]
        }
        self.assertEqual(allocations, {"primary-0": 95000, "primary-1": 0})
        self.assertEqual(
            view["balances"],
            {
                POOL_ACCOUNT: 5000,
                "payable:primary-0": 0,
                "payable:primary-1": -5000,
                "in_transit:payout-primary-0": 0,
                "pg:primary": 0,
            },
        )

    def test_original_cancel_journey_separates_acceptance_from_credit(self):
        proc = run_cli(fixture_path("original_cancel"), journey_path("original_cancel"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        frames = frames_of(proc)
        self.assertEqual(len(frames), 7)
        for frame in frames:
            self.assert_envelope(frame)

        before = frames[2]["view"]
        self.assertEqual(before["trades"]["primary"]["originalCancelled"], 0)
        self.assertEqual(before["effects"]["cancel-primary"]["customerCreditConfirmed"], 0)
        self.assertEqual(before["balances"]["pg:primary"], 100000)
        self.assertEqual(before["balances"]["pg_cancel_due:primary"], 0)

        accepted = frames[3]["receipt"]["result"]
        self.assertEqual(accepted["state"], "DONE")
        self.assertTrue(accepted["confirmed"])
        self.assertFalse(accepted["fundsObserved"])
        after_acceptance = frames[4]["view"]
        self.assertEqual(after_acceptance["trades"]["primary"]["originalCancelled"], 100000)
        self.assertEqual(
            after_acceptance["effects"]["cancel-primary"]["customerCreditConfirmed"], 0
        )
        self.assertEqual(after_acceptance["balances"]["pg_cancel_due:primary"], -100000)
        self.assertEqual(after_acceptance["balances"]["refund:primary"], 0)

        self.assertEqual(frames[5]["receipt"]["result"]["state"], "DONE")
        after_credit = frames[6]["view"]
        self.assertEqual(
            after_credit["effects"]["cancel-primary"]["customerCreditConfirmed"], 100000
        )
        self.assertEqual(after_credit["balances"], after_acceptance["balances"])
        self.assertEqual(
            after_credit["trades"]["primary"]["refunded"], 100000
        )

    def assert_journey_matches_core(self, name):
        fixture = read_fixture(name)
        core = Core(":memory:")
        try:
            for command in fixture["setup"]:
                core.execute(
                    command["operationId"],
                    command["actor"],
                    command["action"],
                    copy.deepcopy(command["body"]),
                )
            proc = run_cli(fixture_path(name), journey_path(name))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            frames = frames_of(proc)
            requests = read_journey(name)
            self.assertEqual(len(frames), len(requests))
            for request, frame in zip(requests, frames):
                if "view" in request:
                    selectors = request["view"]
                    self.assertEqual(
                        frame["view"],
                        selected_state(
                            core.snapshot(),
                            selectors["effectIds"],
                            selectors["tradeIds"],
                            selectors["accounts"],
                        ),
                    )
                else:
                    expected = core.execute(
                        request["operationId"],
                        request["actor"],
                        request["action"],
                        copy.deepcopy(request["body"]),
                    )
                    self.assertEqual(frame["receipt"], expected)
                    self.assertEqual(
                        set(frame), {"evidenceClass", "notice", "receipt"}
                    )
        finally:
            core.db.close()

    def test_all_journeys_match_direct_core_execution(self):
        for name in ("cash_refund", "payout", "original_cancel"):
            with self.subTest(journey=name):
                self.assert_journey_matches_core(name)

    def test_file_and_stdin_modes_emit_identical_frames(self):
        from_file = run_cli(fixture_path("cash_refund"), journey_path("cash_refund"))
        self.assertEqual(from_file.returncode, 0, from_file.stderr)
        stdin_text = journey_path("cash_refund").read_text(encoding="utf-8")
        from_stdin = run_cli(fixture_path("cash_refund"), None, stdin_text=stdin_text)
        self.assertEqual(from_stdin.returncode, 0, from_stdin.stderr)
        self.assertEqual(frames_of(from_stdin), frames_of(from_file))


class LocalFailureTests(unittest.TestCase):
    def test_malformed_fixtures_publish_no_usable_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            empty_requests = directory / "requests.jsonl"
            empty_requests.write_text("", encoding="utf-8")

            invalid_json = directory / "invalid.json"
            invalid_json.write_text("{", encoding="utf-8")
            bad_provenance = directory / "provenance.json"
            document = read_fixture("cash_refund")
            document["provenance"] = "imported"
            bad_provenance.write_text(json.dumps(document), encoding="utf-8")
            missing_trade = directory / "missing-trade.json"
            missing_trade.write_text(
                json.dumps(
                    {
                        "fixture_version": 1,
                        "provenance": "synthetic",
                        "setup": [
                            {
                                "operationId": "capture-missing",
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
                                    "buyer": "A",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            non_utf8 = directory / "non-utf8.json"
            non_utf8.write_bytes(b"\xff\xfe\x00")

            for name, expected_type in (
                (invalid_json, "FixtureError"),
                (bad_provenance, "FixtureError"),
                (missing_trade, "Rejected"),
                (non_utf8, "UnicodeDecodeError"),
            ):
                with self.subTest(fixture=name.name):
                    proc = run_cli(name, empty_requests)
                    self.assertEqual(proc.returncode, 2, proc.stderr)
                    frames = frames_of(proc)
                    self.assertEqual(len(frames), 1)
                    self.assertEqual(
                        set(frames[0]), {"localError"}
                    )
                    self.assertEqual(frames[0]["localError"]["type"], expected_type)
                    self.assertEqual(proc.stderr, "")

    def test_malformed_requests_stop_with_a_local_error(self):
        cases = {
            "unknown_field": (
                '{"operationId":"x","actor":"operator","action":"prepare_effect",'
                '"body":{},"extra":1}'
            ),
            "duplicate_key": (
                '{"operationId":"a","operationId":"b","actor":"operator",'
                '"action":"prepare_effect","body":{}}'
            ),
            "not_an_object": "[1,2]",
            "view_missing_selector": '{"view":{"effectIds":[],"tradeIds":[]}}',
            "view_unknown_selector": (
                '{"view":{"effectIds":[],"tradeIds":[],"accounts":[],"x":[]}}'
            ),
            "unsupported_action": (
                '{"operationId":"x","actor":"operator","action":"commit_trade",'
                '"body":{"domain":"%s","tradeId":"primary"}}' % DOMAIN
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            requests = Path(temporary) / "requests.jsonl"
            for name, line in cases.items():
                with self.subTest(case=name):
                    # A valid second line must never run after a framing error.
                    requests.write_text(
                        line + "\n"
                        '{"view":{"effectIds":[],"tradeIds":[],"accounts":[]}}\n',
                        encoding="utf-8",
                    )
                    proc = run_cli(fixture_path("cash_refund"), requests)
                    self.assertEqual(proc.returncode, 2, proc.stderr)
                    frames = frames_of(proc)
                    self.assertEqual(len(frames), 1)
                    self.assertEqual(set(frames[0]), {"localError"})
                    self.assertEqual(frames[0]["localError"]["type"], "FixtureError")
                    self.assertEqual(proc.stderr, "")

    def test_invalid_utf8_requests_are_local_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            requests = Path(temporary) / "requests.jsonl"
            requests.write_bytes(b"\xff\n")
            proc = run_cli_bytes(fixture_path("cash_refund"), requests)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            frames = [json.loads(line) for line in proc.stdout.decode().splitlines()]
            self.assertEqual(len(frames), 1)
            self.assertEqual(frames[0]["localError"]["type"], "UnicodeDecodeError")
            self.assertEqual(proc.stderr, b"")

    def test_main_closes_its_session_on_success_and_framing_error(self):
        created = []
        real_load = cli.load_fixture

        def tracking(path):
            session = real_load(path)
            created.append(session)
            return session

        with tempfile.TemporaryDirectory() as temporary:
            requests = Path(temporary) / "requests.jsonl"
            with mock.patch.object(cli, "load_fixture", tracking):
                requests.write_text(
                    '{"view":{"effectIds":[],"tradeIds":[],"accounts":[]}}\n',
                    encoding="utf-8",
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    result = cli.main(
                        ["--fixture", str(fixture_path("cash_refund")),
                         "--requests", str(requests)]
                    )
                self.assertEqual(result, 0)
                with self.assertRaises(PaymentEffectSessionClosed):
                    created[-1].execute(
                        "closed", "operator", "send_effect", {"effectId": "x"}
                    )

                requests.write_text("not json\n", encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    result = cli.main(
                        ["--fixture", str(fixture_path("cash_refund")),
                         "--requests", str(requests)]
                    )
                self.assertEqual(result, 2)
                with self.assertRaises(PaymentEffectSessionClosed):
                    created[-1].view(effect_ids=[], trade_ids=[], accounts=[])


class ReplayAndRejectionTests(unittest.TestCase):
    def test_core_rejections_continue_and_keep_original_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            requests = Path(temporary) / "requests.jsonl"
            requests.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "operationId": "unsettled-prepare",
                                "actor": "operator",
                                "action": "prepare_effect",
                                "body": {
                                    "domain": DOMAIN,
                                    "effectId": "refund-primary",
                                    "tradeId": "primary",
                                    "kind": "REFUND",
                                    "amount": 100000,
                                    "routeProfile": "CASH_REFUND_FIXTURE",
                                    "contractRef": "fixture:cash-refund:v1",
                                    "beneficiaryAccountRef": "fixture-account:A",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "view": {
                                    "effectIds": ["refund-primary"],
                                    "tradeIds": ["primary"],
                                    "accounts": [POOL_ACCOUNT, "refund:primary"],
                                }
                            }
                        ),
                        json.dumps(
                            {
                                "operationId": "cancel-prepare",
                                "actor": "operator",
                                "action": "prepare_effect",
                                "body": {
                                    "domain": DOMAIN,
                                    "effectId": "cancel-primary",
                                    "tradeId": "primary",
                                    "kind": "REFUND",
                                    "amount": 100000,
                                    "routeProfile": "PG_ORIGINAL_CANCEL_FIXTURE",
                                    "contractRef": "fixture:pg-cancel:v1",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "operationId": "cancel-send",
                                "actor": "operator",
                                "action": "send_effect",
                                "body": {
                                    "domain": DOMAIN,
                                    "effectId": "cancel-primary",
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            proc = run_cli(fixture_path("unsettled_refund"), requests)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            frames = frames_of(proc)
            self.assertEqual(len(frames), 4)
            self.assertEqual(
                frames[0],
                {"error": "INSUFFICIENT_CONFIRMED_FUNDS", "rejected": True},
            )
            self.assertIsNone(frames[1]["view"]["effects"]["refund-primary"])
            self.assertEqual(frames[1]["view"]["balances"][POOL_ACCOUNT], 0)
            self.assertEqual(
                frames[2]["receipt"]["result"]["fundingBasis"],
                "ORIGINAL_PAYMENT_AND_PG_LIABILITY",
            )
            self.assertEqual(
                frames[3]["receipt"]["result"]["dispatchDecision"],
                "FIRST_SEND_INTENT",
            )
            self.assertEqual(proc.stderr, "")

    def test_replay_and_conflicting_operation_bodies(self):
        prepare = {
            "domain": DOMAIN,
            "effectId": "refund-primary",
            "tradeId": "primary",
            "kind": "REFUND",
            "amount": 100000,
            "routeProfile": "CASH_REFUND_FIXTURE",
            "contractRef": "fixture:cash-refund:v1",
            "beneficiaryAccountRef": "fixture-account:A",
        }
        send = {"domain": DOMAIN, "effectId": "refund-primary"}
        status = {
            "domain": DOMAIN,
            "scope": dict(SCOPE),
            "provenance": "synthetic",
            "effectId": "refund-primary",
            "phase": "STATUS",
            "sourceId": "status-once",
            "providerOperationId": "provider-refund-primary",
            "amount": 100000,
            "currency": "KRW",
            "beneficiary": "A",
            "paymentId": "pay-primary",
            "status": "SUCCESS",
        }
        request_lines = [
            {"operationId": "dup", "actor": "operator", "action": "prepare_effect", "body": prepare},
            {"operationId": "dup", "actor": "operator", "action": "prepare_effect", "body": prepare},
            {
                "operationId": "dup",
                "actor": "operator",
                "action": "prepare_effect",
                "body": dict(prepare, amount=90000),
            },
            {"operationId": "send-once", "actor": "operator", "action": "send_effect", "body": send},
            {"operationId": "send-once", "actor": "operator", "action": "send_effect", "body": send},
            {"operationId": "send-again", "actor": "operator", "action": "send_effect", "body": send},
            {"operationId": "status-once", "actor": "pg-adapter", "action": "observe_effect", "body": status},
            {"operationId": "status-once", "actor": "pg-adapter", "action": "observe_effect", "body": status},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            requests = Path(temporary) / "requests.jsonl"
            requests.write_text(
                "\n".join(json.dumps(line) for line in request_lines) + "\n",
                encoding="utf-8",
            )
            proc = run_cli(fixture_path("cash_refund"), requests)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            frames = frames_of(proc)
            self.assertEqual(len(frames), 8)

            self.assertEqual(frames[0], frames[1])
            self.assertEqual(
                frames[0]["receipt"]["result"]["fundingBasis"],
                "CONFIRMED_POOL_CASH",
            )
            self.assertEqual(
                frames[2],
                {"error": "OPERATION_ID_CONFLICT", "rejected": True},
            )
            self.assertEqual(
                frames[3]["receipt"]["result"]["dispatchDecision"],
                "FIRST_SEND_INTENT",
            )
            self.assertEqual(
                frames[4]["receipt"]["result"],
                {
                    "effectId": "refund-primary",
                    "dispatchDecision": "QUERY_ONLY",
                    "state": "OUTCOME_UNKNOWN",
                    "replay": True,
                },
            )
            self.assertEqual(
                frames[5]["receipt"]["result"],
                {
                    "effectId": "refund-primary",
                    "dispatchDecision": "QUERY_ONLY",
                    "state": "OUTCOME_UNKNOWN",
                },
            )
            self.assertNotIn("replay", frames[5]["receipt"]["result"])
            self.assertEqual(frames[6], frames[7])
            self.assertEqual(frames[6]["receipt"]["action"], "observe_effect")
            self.assertEqual(proc.stderr, "")


class FramingTests(unittest.TestCase):
    def test_short_and_broken_writes_raise(self):
        class ShortWriter:
            def write(self, text):
                return 0

            def flush(self):
                raise AssertionError("flush must not run after a short write")

        class BrokenWriter:
            def write(self, text):
                raise BrokenPipeError("closed pipe")

            def flush(self):
                raise AssertionError("flush must not run after a broken write")

        with mock.patch("sys.stdout", ShortWriter()):
            with self.assertRaises(OSError):
                cli._emit({"value": 1})
        with mock.patch("sys.stdout", BrokenWriter()):
            with self.assertRaises(OSError):
                cli._emit({"value": 1})

    def test_valid_payloads_are_rejected_by_the_fixture_validator(self):
        # Sanity check that the CLI's imported strict decoder is the one used.
        with self.assertRaises(FixtureError):
            cli.decode_json("{} {}")


if __name__ == "__main__":
    unittest.main()
