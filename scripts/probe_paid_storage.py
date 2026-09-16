#!/usr/bin/env python3
"""Local storage probe; chain replies and money are explicitly synthetic.

Each command runs Node -> fresh Python -> Node, using PaidCoordinator's actual
SQLite and child-query code. This is not an actual Sui acceptance journey.
The supervisor keeps acknowledged state separately and stops at first drift.
"""
import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference/v0.3-rc1"
sys.path.insert(0, str(SOURCE))
from common import canonical, digest, Rejected
from paid_integration import PaidCoordinator

NODE_PARENT = """
const {spawnSync}=require('node:child_process');
const fs=require('node:fs');
const r=spawnSync(process.argv[1],[process.argv[2],'--worker'],{
  input:fs.readFileSync(0),encoding:'utf8',timeout:30000});
process.stdout.write(r.stdout??'');process.stderr.write(r.stderr??'');
process.exit(r.status??2);
"""


def snapshot(coordinator):
    """SQL-only observation: never open/read/close a live DB file separately."""
    result = {}
    for name, db in (("projection", coordinator.core.db), ("provider", coordinator.provider.db)):
        tables = {}
        for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
            escaped = table.replace('"', '""')
            rows = db.execute('SELECT * FROM "' + escaped + '"').fetchall()
            tables[table] = sorted(canonical([{"blob": v.hex()} if isinstance(v, bytes) else v for v in row]) for row in rows)
        result[name] = dict(hash=digest(tables), tables={k: len(v) for k, v in tables.items()},
                            integrity=db.execute("PRAGMA integrity_check").fetchall())
    result["commands"] = dict(coordinator.core.db.execute("SELECT operation_id,fingerprint FROM commands").fetchall())
    result["items"] = dict(coordinator.core.db.execute("SELECT id,hash FROM integration_items").fetchall())
    result["effects"] = {k: {"sent": v["sent"], "state": v["state"], "attempts": v["dispatch"]["attempts"]}
                         for k, v in coordinator.core.snapshot()["effects"].items()}
    return result


def worker():
    q = json.load(sys.stdin)
    c = PaidCoordinator(q["directory"])
    report = dict(runtime=dict(python=sys.version.split()[0], sqlite=sqlite3.sqlite_version), before=snapshot(c))
    observation_path = Path(q["directory"]).parent / "worker-observation.json"
    observation_path.write_text(json.dumps(report, indent=2))
    original_run = subprocess.run

    def fixture_child(_command, **kwargs):
        query = json.loads(kwargs["input"])
        b = query["binding"]
        reply = dict(bindingHash=digest(b), source="SYNTHETIC_CHAIN_STORAGE_PROBE")
        if query["action"] == "observe":
            reply.update(state="EXECUTED_SUCCESS" if q.get("chain_success") else "OUTCOME_UNKNOWN",
                         digest="fixture-transfer", rawHash="fixture-receipt",
                         allocation=dict(seller_due=114000, organizer_due=2400, platform_due=3600))
        elif query["action"] == "closed":
            if not q.get("chain_closed"):
                raise Rejected("FIXTURE_SHOW_NOT_CLOSED")
            reply["state"] = "FIXTURE_CLOSED"
        elif query["action"] == "open":
            if q.get("chain_closed"):
                raise Rejected("FIXTURE_SHOW_CLOSED")
            reply["state"] = "FIXTURE_OPEN"
        else:
            reply["state"] = "FIXTURE_OFFER"
        kwargs["input"] = canonical(reply)
        return original_run(["node", "-e", "process.stdout.write(require('node:fs').readFileSync(0))"], **kwargs)

    try:
        with patch("paid_integration.subprocess.run", side_effect=fixture_child):
            if q["action"] == "advance":
                report["result"] = c.provider.advance(**q["params"])
            else:
                report["result"] = getattr(c, q["action"])(**q["params"])
                if q["action"] == "summary":
                    report["result"]["rightsAuthority"] = "SYNTHETIC_CHAIN_STORAGE_PROBE"
        report["ok"] = True
    except Rejected as error:
        report.update(ok=False, error=str(error))
    finally:
        try:
            report["after"] = snapshot(c)
        finally:
            c.close()
            observation_path.write_text(json.dumps(report, indent=2))
    print(canonical(report))


def run(args):
    directory = Path(args.directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    state_dir = directory / "state"
    trace = dict(format="kix-storage-probe-v1", money="MOCK", chain="SYNTHETIC",
                 naturalFailureReproduced=False, steps=[], result="RUNNING")
    prior = None
    chain_success = False
    chain_closed = False

    def invoke(action, params=None, expected_error=None):
        nonlocal prior
        n = len(trace["steps"])
        q = dict(directory=str(state_dir), action=action, params=params or {},
                 chain_success=chain_success, chain_closed=chain_closed)
        step = dict(sequence=n, action=action, request=q)
        trace["steps"].append(step)
        (directory / "trace.json").write_text(json.dumps(trace, indent=2))
        r = subprocess.run(["node", "-e", NODE_PARENT, args.python, str(Path(__file__).resolve())],
                           input=canonical(q), capture_output=True, text=True, timeout=40)
        step["exit"] = r.returncode
        step["stderr"] = r.stderr
        if r.returncode != 0:
            step["stdout"] = r.stdout
            raise RuntimeError("WORKER_FAILED:" + str(n))
        response = json.loads(r.stdout)
        step["response"] = response
        trace["runtime"] = response["runtime"]
        if prior is not None and prior != response["before"]:
            raise RuntimeError("ACKNOWLEDGED_STATE_CHANGED_BEFORE_COMMAND:" + str(n))
        if expected_error:
            assert not response["ok"] and expected_error in response["error"], response
        else:
            assert response["ok"], response
        for name in ("projection", "provider"):
            assert response["after"][name]["integrity"] == [["ok"]]
        if prior:
            for table in ("commands", "items"):
                if not all(response["after"][table].get(k) == v for k, v in prior[table].items()):
                    raise RuntimeError("ACKNOWLEDGED_RECORD_MISSING_AFTER_COMMAND:" + table + ":" + str(n))
        prior = response["after"]
        # Worker has exited: copying its complete DB/WAL/SHM set cannot cancel
        # that worker's locks or mix a running transaction with another version.
        latest = directory / "last-acknowledged"
        latest.mkdir(exist_ok=True)
        for old in latest.iterdir():
            old.unlink()
        for path in state_dir.glob("*.sqlite*"):
            shutil.copy2(path, latest / path.name)
        (directory / "trace.json").write_text(json.dumps(trace, indent=2))
        return response.get("result")

    try:
        for cycle in range(args.cycles):
            tid = "probe-" + str(cycle)
            chain_success, chain_closed = False, False
            binding = dict(format="kix-paid-localnet-v1", tradeId=tid, chain="fixture-chain", packageId="fixture-package",
                showId="show-"+str(cycle), ticketId="ticket-"+str(cycle), slot=0, generation=1, expectedVersion=1,
                seller="seller", buyer="buyer", amount=120000, currency="KRW", expiresMs="1900000000000",
                termsHash="00"*32, organizer="organizer", organizerBps=200, platformBps=300, resaleCap=150000)
            binding["policyHash"] = digest(PaidCoordinator.policy(binding))
            invoke("prepare", {"b": binding})
            invoke("capture", dict(tid=tid, lose_response=True))
            payment = invoke("sync_capture", dict(tid=tid))
            invoke("capture", dict(tid=tid))
            saved = dict(bindingHash=digest(binding), chain=binding["chain"], packageId=binding["packageId"],
                         paymentRef=payment["paymentRef"], digest="fixture-transfer", bytes="fixture", signatures=["fixture"])
            invoke("record_submission", dict(tid=tid, submission=saved))
            invoke("reconcile_chain", dict(tid=tid))
            invoke("cancel", dict(tid=tid), "CHAIN_UNRESOLVED_NO_COMPENSATION")
            chain_success = True
            invoke("reconcile_chain", dict(tid=tid))
            invoke("reconcile_chain", dict(tid=tid))
            s = invoke("summary", dict(tid=tid))
            key = next(p["key"] for p in s["provider"] if p["operationId"] == payment["paymentId"])
            invoke("advance", dict(key=key, settlement=True))
            invoke("sync_capture", dict(tid=tid))
            invoke("release_after_fixture_performance", dict(tid=tid))
            eid = tid + "-seller"
            invoke("prepare_effect", dict(tid=tid, eid=eid, kind="PAYOUT", amount=114000, allocation_id=tid+"-0"))
            invoke("send_effect", dict(eid=eid, lose_response=True))
            invoke("send_effect", dict(eid=eid))
            s = invoke("summary", dict(tid=tid))
            assert s["effects"][eid]["sent"] and s["effects"][eid]["dispatch"]["attempts"] == 1
            key = s["effects"][eid]["idempotencyKey"]
            chain_closed = True
            invoke("cancel", dict(tid=tid))
            s = invoke("summary", dict(tid=tid))
            assert s["trade"]["refundDue"] == 120000 and not s["trade"]["reversalPlanned"]
            invoke("advance", dict(key=key, status=True, funds=True))
            invoke("sync_effect", dict(eid=eid))
            s = invoke("summary", dict(tid=tid))
            assert s["balances"]["recoverable:"+tid+"-0"] == 114000 and s["trade"]["refunded"] == 0
        trace["result"] = "NO_FAILURE_REPRODUCED"
    except BaseException as error:
        continuity_failure = str(error).startswith(("ACKNOWLEDGED_STATE_CHANGED_BEFORE_COMMAND:", "ACKNOWLEDGED_RECORD_MISSING_AFTER_COMMAND:"))
        trace.update(result="FAILURE_CAPTURED", error=repr(error), naturalFailureReproduced=continuity_failure)
        failed = directory / "failure-files"
        failed.mkdir(exist_ok=True)
        for path in state_dir.glob("*.sqlite*"):
            shutil.copy2(path, failed / path.name)
    finally:
        trace["sourceSha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__), SOURCE / "paid_integration.py", SOURCE / "core.py", SOURCE / "mock_provider.py", SOURCE / "storage_receipt.py"]}
        trace["commands"] = len(trace["steps"])
        trace["historicalRootCauseEstablished"] = False
        (directory / "trace.json").write_text(json.dumps(trace, indent=2))
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps({k: v for k, v in trace.items() if k != "steps"}, indent=2) + "\n")
    print(json.dumps({k: v for k, v in trace.items() if k != "steps"}, indent=2))
    return 0 if trace["result"] == "NO_FAILURE_REPRODUCED" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--directory")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--report", help="Write a public summary, without DB files or full transaction bodies")
    args = parser.parse_args()
    if args.worker:
        worker()
    else:
        if not args.directory:
            parser.error("--directory must name a new disposable probe directory")
        if args.cycles < 1:
            parser.error("--cycles must be positive")
        raise SystemExit(run(args))
