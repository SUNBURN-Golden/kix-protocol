"""Deliberate rollback/crash injections, NOT a natural SQLite-bug reproduction."""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from common import digest, canonical
from paid_integration import PaidCoordinator
from storage_receipt import StorageReceipt, StorageFault, directory_fingerprint

HERE = Path(__file__).resolve().parent


def seed(coordinator):
    b = dict(format="kix-paid-localnet-v1", tradeId="resale", chain="fixture-chain", packageId="fixture-package",
        showId="show", ticketId="ticket", slot=0, generation=1, expectedVersion=1, seller="seller", buyer="buyer",
        amount=120000, currency="KRW", expiresMs="1900000000000", termsHash="00"*32, organizer="organizer",
        organizerBps=200, platformBps=300, resaleCap=150000)
    b["policyHash"] = digest(coordinator.policy(b))
    with patch.object(coordinator, "_query", return_value={"state": "SYNTHETIC_CHAIN_FOR_STORAGE_TEST"}):
        coordinator.prepare(b)
        coordinator.capture("resale")
        key = coordinator.provider.summary()[0]["key"]
        coordinator.provider.advance(key, settlement=True)
        coordinator.sync_capture("resale")
        final = dict(state="EXECUTED_SUCCESS", allocation=dict(seller_due=114000, organizer_due=2400, platform_due=3600))
        coordinator.core.db.execute("INSERT INTO integration_final VALUES(?,?)", ("resale", canonical(final)))
        coordinator._run("commit", "operator", "commit_trade", tradeId="resale")
        coordinator._run("complete", "operator", "complete_event", eventId="show")
        coordinator.prepare_effect("resale", "payout", "PAYOUT", 114000, "resale-0")
    return b


class StorageContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / "state"
        with StorageReceipt(self.directory, {"action": "seed"}) as receipt:
            receipt.begin()
            c = PaidCoordinator(self.directory)
            self.binding = seed(c)
            receipt.finish(c)
        self.old = Path(self.tmp.name) / "before-send.sqlite"
        shutil.copy2(self.directory / "projection.sqlite", self.old)

    def send(self):
        with StorageReceipt(self.directory, {"action": "send"}) as receipt:
            receipt.begin()
            c = PaidCoordinator(self.directory)
            with patch.object(c, "_query", return_value={"state": "SYNTHETIC_OPEN"}):
                self.assertEqual(c.send_effect("payout", lose_response=True)["state"], "OUTCOME_UNKNOWN")
            receipt.finish(c)

    def test_baseline_without_receipt_accepts_healthy_rollback_and_misclassifies_cancel(self):
        self.send()
        shutil.copy2(self.old, self.directory / "projection.sqlite")
        c = PaidCoordinator(self.directory)
        try:
            self.assertEqual(c.core.db.execute("PRAGMA integrity_check").fetchall(), [("ok",)])
            self.assertFalse(c.core.snapshot()["effects"]["payout"]["sent"])
            self.assertEqual(len(c.provider.summary()), 2)
            c._run("cancel", "operator", "cancel_event", eventId="show")
            self.assertTrue(c.trade("resale")["reversalPlanned"])
            self.assertEqual(c.core.snapshot()["effects"]["payout"]["state"], "ABORTED")
        finally:
            c.close()

    def test_receipt_stops_healthy_rollback_before_any_cancel_or_provider_call(self):
        self.send()
        acknowledged = (self.directory / "storage-receipt.json").read_bytes()
        shutil.copy2(self.old, self.directory / "projection.sqlite")
        before = directory_fingerprint(self.directory)
        with self.assertRaisesRegex(StorageFault, "ACKNOWLEDGED_STATE_CHANGED"):
            with StorageReceipt(self.directory, {"action": "cancel"}) as receipt:
                receipt.begin()
                self.fail("No command may run after this rollback")
        self.assertEqual(directory_fingerprint(self.directory), before)
        self.assertEqual((self.directory / "storage-receipt.json").read_bytes(), acknowledged)

    def test_query_guard_stops_rollback_before_new_observation_or_payout_decision(self):
        self.send()
        c = PaidCoordinator(self.directory)
        def restore_during_child(*args, **kwargs):
            shutil.copy2(self.old, self.directory / "projection.sqlite")
            return subprocess.CompletedProcess(args, 0, canonical(dict(bindingHash=digest(self.binding), state="FIXTURE_OPEN")), "")
        try:
            with patch("paid_integration.subprocess.run", side_effect=restore_during_child):
                with self.assertRaisesRegex(StorageFault, "STATE_CHANGED_DURING_QUERY"):
                    c._query("open", self.binding)
        finally:
            c.close()

    def test_unchanged_restart_keeps_unknown_payout_reserved_through_cancel(self):
        self.send()
        with StorageReceipt(self.directory, {"action": "cancel"}) as receipt:
            receipt.begin()
            c = PaidCoordinator(self.directory)
            c._run("cancel", "operator", "cancel_event", eventId="show")
            self.assertFalse(c.trade("resale")["reversalPlanned"])
            self.assertTrue(c.core.snapshot()["effects"]["payout"]["sent"])
            key = c.core.snapshot()["effects"]["payout"]["idempotencyKey"]
            c.provider.advance(key, status=True, funds=True)
            c.sync_effect("payout")
            self.assertEqual(c.core.snapshot()["balances"]["recoverable:resale-0"], 114000)
            self.assertEqual(c.trade("resale")["refunded"], 0)
            receipt.finish(c)

    def test_command_process_dies_before_or_after_provider_commit_then_is_quarantined(self):
        for point in ("before", "after"):
            with self.subTest(point=point):
                target = Path(self.tmp.name) / ("crash-" + point)
                shutil.copytree(self.directory, target)
                code = """
import os,sys
from unittest.mock import patch
from paid_integration import PaidCoordinator
from storage_receipt import StorageReceipt
directory,point=sys.argv[1:]
with StorageReceipt(directory, {'action':'send'}) as receipt:
    receipt.begin()
    c=PaidCoordinator(directory)
    original=c.provider.submit
    def killed(*args,**kwargs):
        if point=='after': original(*args,**kwargs)
        os._exit(91)
    with patch.object(c,'_query',return_value={'state':'SYNTHETIC_OPEN'}), patch.object(c.provider,'submit',side_effect=killed):
        c.send_effect('payout')
"""
                r = subprocess.run([sys.executable, "-c", code, str(target), point], cwd=HERE, capture_output=True, timeout=15)
                self.assertEqual(r.returncode, 91, r.stderr)
                before = directory_fingerprint(target)
                with self.assertRaisesRegex(StorageFault, "UNFINISHED_COMMAND"):
                    with StorageReceipt(target, {"action": "send-again"}) as receipt:
                        receipt.begin()
                self.assertEqual(directory_fingerprint(target), before)
                c = PaidCoordinator(target)
                try:
                    effect = c.core.snapshot()["effects"]["payout"]
                    self.assertTrue(effect["sent"])
                    self.assertEqual(effect["dispatch"]["attempts"], 1)
                    self.assertEqual(len(c.provider.summary()), 2 if point == "after" else 1)
                finally:
                    c.close()

    def test_missing_receipt_does_not_silently_adopt_existing_database(self):
        (self.directory / "storage-receipt.json").unlink()
        with self.assertRaisesRegex(StorageFault, "UNTRACKED_DATABASE"):
            with StorageReceipt(self.directory, {"action": "summary"}) as receipt:
                receipt.begin()

    def test_second_process_cannot_enter_while_first_command_holds_lock(self):
        with StorageReceipt(self.directory, {"action": "one"}):
            code = """
import sys
from storage_receipt import StorageReceipt,StorageFault
try:
    with StorageReceipt(sys.argv[1], {'action':'two'}): pass
except StorageFault as error:
    print(error)
    sys.exit(2)
"""
            r = subprocess.run([sys.executable, "-c", code, str(self.directory)], cwd=HERE, capture_output=True, text=True, timeout=10)
            self.assertEqual(r.returncode, 2)
            self.assertIn("STORAGE_COMMAND_ALREADY_RUNNING", r.stdout)

    def test_cli_rejects_rollback_before_coordinator_initialization(self):
        supported = subprocess.run(["/usr/bin/python3", "-c", "import sqlite3;print(sqlite3.sqlite_version)"], capture_output=True, text=True)
        if supported.stdout.strip() != "3.45.1":
            self.skipTest("CLI fixture runtime unavailable")
        self.send()
        shutil.copy2(self.old, self.directory / "projection.sqlite")
        q = dict(directory=str(self.directory), endpoint="http://127.0.0.1:1", action="cancel", params=dict(tid="resale"))
        r = subprocess.run(["/usr/bin/python3", str(HERE / "paid_driver.py")], input=json.dumps(q), capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("ACKNOWLEDGED_STATE_CHANGED", json.loads(r.stdout)["error"])


if __name__ == "__main__":
    unittest.main()
