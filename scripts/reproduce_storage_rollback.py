#!/usr/bin/env python3
"""Deliberately restore an old ledger; compare unguarded and guarded outcomes.

All rights/provider inputs are synthetic. This reproduces the consequence of
lost dispatch records, NOT the cause of the historical storage incident.
"""
import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference/v0.3-rc1"
sys.path.insert(0, str(SOURCE))
from paid_integration import PaidCoordinator
from storage_receipt import StorageReceipt, StorageFault
from test_storage_receipt import seed


def main(report_path):
    report = dict(fault="DELIBERATE_PROJECTION_ROLLBACK", historicalRootCauseEstablished=False,
                  rights="SYNTHETIC", money="MOCK", steps=[])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        state = root / "state"
        with StorageReceipt(state, {"action": "seed"}) as receipt:
            receipt.begin()
            c = PaidCoordinator(state)
            seed(c)
            receipt.finish(c)
        old = root / "before-send.sqlite"
        shutil.copy2(state / "projection.sqlite", old)
        report["steps"].append(dict(action="prepare_payout", sent=False, amount=114000))
        with StorageReceipt(state, {"action": "send"}) as receipt:
            receipt.begin()
            c = PaidCoordinator(state)
            with patch.object(c, "_query", return_value={"state": "SYNTHETIC_OPEN"}):
                c.send_effect("payout", lose_response=True)
            report["steps"].append(dict(action="provider_committed_response_lost", sent=True,
                 providerOperations=len(c.provider.summary()), dispatchAttempts=c.core.snapshot()["effects"]["payout"]["dispatch"]["attempts"]))
            receipt.finish(c)
        for mode in ("unguarded", "guarded"):
            target = root / mode
            shutil.copytree(state, target)
            shutil.copy2(old, target / "projection.sqlite")
            c = PaidCoordinator(target)
            before = dict(integrity=c.core.db.execute("PRAGMA integrity_check").fetchall(),
                          sent=c.core.snapshot()["effects"]["payout"]["sent"], providerOperations=len(c.provider.summary()))
            c.close()
            if mode == "unguarded":
                c = PaidCoordinator(target)
                try:
                    c._run("cancel", "operator", "cancel_event", eventId="show")
                    report[mode] = dict(before=before, cancellationExecuted=True,
                        reversalPlanned=c.trade("resale")["reversalPlanned"], payoutState=c.core.snapshot()["effects"]["payout"]["state"])
                    assert report[mode]["reversalPlanned"] and report[mode]["payoutState"] == "ABORTED"
                finally:
                    c.close()
            else:
                try:
                    with StorageReceipt(target, {"action": "cancel"}) as receipt:
                        receipt.begin()
                    raise AssertionError("rollback was accepted")
                except StorageFault as error:
                    assert "ACKNOWLEDGED_STATE_CHANGED" in str(error)
                    c = PaidCoordinator(target)
                    try:
                        executed = c.core.db.execute("SELECT count(*) FROM commands WHERE operation_id='cancel'").fetchone()[0]
                        report[mode] = dict(before=before, error=str(error), cancellationExecuted=bool(executed), providerOperations=len(c.provider.summary()))
                        assert executed == 0 and len(c.provider.summary()) == 2
                    finally:
                        c.close()
    report["result"] = "INJECTED_ROLLBACK_REJECTED_BEFORE_CANCELLATION"
    report["sourceSha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path(__file__), SOURCE / "core.py", SOURCE / "paid_integration.py", SOURCE / "storage_receipt.py", SOURCE / "test_storage_receipt.py")}
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    main(parser.parse_args().report)
