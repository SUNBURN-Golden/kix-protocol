"""Durability/boundary tests. Chain-query mocks here prove no Sui behavior;
scripts/run_localnet.py --paid separately exercises the actual Move package.
"""
import tempfile
import sqlite3
import subprocess
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from common import Rejected, digest
from mock_provider import MockProvider, SCOPE
from paid_integration import PaidCoordinator


class PaidDurabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.c = PaidCoordinator(self.temp.name)
        self.b = dict(format="kix-paid-localnet-v1", tradeId="resale", chain="fixture-chain", packageId="fixture-package",
                      showId="show", ticketId="chain-ticket", slot=0, generation=1, expectedVersion=1,
                      seller="seller", buyer="buyer", amount=120000, currency="KRW", expiresMs="1900000000000",
                      termsHash="00"*32, organizer="organizer", organizerBps=200, platformBps=300, resaleCap=150000)
        self.b["policyHash"] = digest(self.c.policy(self.b))
        with patch.object(self.c, "_query", return_value={"state": "ASSUMED_TEST_OFFER"}):
            self.c.prepare(self.b)

    def tearDown(self):
        self.c.close()
        self.temp.cleanup()

    def restart(self):
        self.c.close()
        self.c = PaidCoordinator(self.temp.name)

    def test_capture_commits_at_provider_before_lost_response_then_recovers_once(self):
        self.assertEqual(self.c.capture("resale", lose_response=True)["state"], "CAPTURE_OUTCOME_UNKNOWN")
        self.assertFalse(self.c.trade("resale")["captured"])
        self.restart()
        self.assertFalse(self.c.sync_capture("resale")["cashAvailable"])
        before = self.c.core.snapshot()
        self.c.sync_capture("resale")
        self.assertEqual(before, self.c.core.snapshot())
        self.c.capture("resale")
        self.assertEqual(self.c.provider.summary()[0]["economicExecutions"], 1)

    def test_projection_cannot_commit_without_verified_chain_success(self):
        self.c.capture("resale")
        before = self.c.core.snapshot()
        with self.assertRaisesRegex(Rejected, "VERIFIED_CHAIN_SUCCESS_REQUIRED"):
            self.c._run("bypass", "operator", "commit_trade", tradeId="resale")
        self.assertEqual(before, self.c.core.snapshot())

    def test_child_query_closes_databases_and_reopens_even_after_timeout(self):
        before = self.c.core.snapshot()
        connections = [self.c.core.db, self.c.provider.db]
        def timeout(*args, **kwargs):
            for db in connections:
                with self.assertRaises(sqlite3.ProgrammingError):
                    db.execute("SELECT 1")
            raise subprocess.TimeoutExpired("node", 45)
        with patch("paid_integration.subprocess.run", side_effect=timeout):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.c._query("inspect", self.b)
        self.assertEqual(before, self.c.core.snapshot())
        for db in (self.c.core.db, self.c.provider.db):
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])

    def test_same_trade_cannot_change_any_bound_fact_after_restart(self):
        self.restart()
        for key, value in (("buyer", "other"), ("seller", "other"), ("chain", "other"),
                           ("packageId", "other"), ("showId", "other"), ("ticketId", "other"),
                           ("amount", 120001), ("termsHash", "11"*32)):
            with self.subTest(key=key), self.assertRaisesRegex(Rejected, "TRADE_ID_CONFLICT"):
                self.c.prepare(dict(self.b, **{key: value}))

    def test_local_amount_currency_and_policy_are_strict(self):
        for change in (dict(amount=True), dict(currency="USD"), dict(policyHash="bad")):
            with self.assertRaises(Rejected):
                self.c.prepare(dict(self.b, **change))

    def test_second_trade_cannot_claim_same_show(self):
        with patch.object(self.c, "_query", return_value={"state": "ASSUMED_TEST_OFFER"}):
            with self.assertRaisesRegex(Rejected, "SHOW_ALREADY_BOUND"):
                self.c.prepare(dict(self.b, tradeId="resale-2"))
        self.assertNotIn("resale-2", self.c.core.snapshot()["trades"])

    def test_signed_request_cannot_be_replaced_after_unknown_result(self):
        payment = self.c.capture("resale")
        saved = dict(bindingHash=digest(self.b), chain=self.b["chain"], packageId=self.b["packageId"],
                     paymentRef=payment["paymentRef"], digest="first", bytes="test-only", signatures=["test-only"])
        self.c.record_submission("resale", saved)
        self.restart()
        with self.assertRaisesRegex(Rejected, "IMMUTABLE_REQUEST_CONFLICT"):
            self.c.record_submission("resale", dict(saved, digest="second"))
        with patch.object(self.c, "_query", return_value={"state": "OUTCOME_UNKNOWN"}):
            with self.assertRaisesRegex(Rejected, "CHAIN_UNRESOLVED_NO_COMPENSATION"):
                self.c.cancel("resale")
        self.assertEqual(self.c.trade("resale")["refundDue"], 0)


class ProviderRaceTests(unittest.TestCase):
    def test_two_process_connections_replay_one_provider_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "provider.sqlite")
            init = MockProvider(path)
            init.db.close()
            barrier, results, errors = threading.Barrier(2), [], []
            request = dict(kind="CAPTURE", scope=SCOPE, amount=120000, currency="KRW", bindingHash="test")
            def worker():
                p = MockProvider(path)
                try:
                    barrier.wait(timeout=5)
                    results.append(p.submit("one-key", request)["operationId"])
                except BaseException as error:
                    errors.append(str(error))
                finally:
                    p.db.close()
            threads = [threading.Thread(target=worker) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)
            self.assertFalse(errors)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], results[1])
            p = MockProvider(path)
            try:
                with self.assertRaisesRegex(Rejected, "PROVIDER_KEY_CONFLICT"):
                    p.submit("one-key", dict(request, amount=119999))
                self.assertEqual(p.summary()[0]["submitCalls"], 2)
                self.assertEqual(p.summary()[0]["economicExecutions"], 1)
            finally:
                p.db.close()


if __name__ == "__main__":
    unittest.main()
