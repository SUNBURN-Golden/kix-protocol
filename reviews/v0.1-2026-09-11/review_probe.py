"""Bounded review of an UNMODIFIED KIX v0.1 bundle. No external calls.

Assertions reproduce current behavior; a reproduced gap is not a passing
product requirement. Mutations run in disposable copies, one at a time.
This is not a second implementation of the full protocol or a security proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile


POLICY = dict(primaryPrice=100000, resaleCap=150000, primaryFeeBps=500,
              resaleFeeBps=300, resaleOrganizerBps=200, resaleAllowed=True,
              refundProfile="FULL_CHAIN_UNWIND_FIXTURE")


def probes(root):
    sys.path.insert(0, str(root))
    from core import Core, Rejected

    class Driver:
        # Independently written driver; it does not import the supplied Harness.
        def __init__(self):
            self.core = Core()
            self.seq = 0

        def call(self, action, actor="operator", **body):
            self.seq += 1
            return self.core.execute(f"review-{self.seq}", actor, action,
                                     dict(domain=Core.DOMAIN, **body))

        def source(self, action, **body):
            return self.call(action, "pg-adapter", scope=Core.SCOPE,
                             provenance="synthetic", **body)

        def event(self):
            self.call("create_event", eventId="show", organizer="organizer",
                      policy=POLICY, seats=["A1"])

        def buy(self, trade="primary", buyer="A", amount=100000, settle=100000):
            t = self.core.snapshot()["tickets"]["show/A1"]
            self.call("prepare_trade", t["owner"] or buyer, tradeId=trade,
                      ticketId="show/A1", buyer=buyer, amount=amount,
                      expectedVersion=t["rightsVersion"])
            r = self.core.snapshot()["trades"][trade]
            if not r["accepted"]:
                self.call("accept_trade", buyer, tradeId=trade, termsHash=r["termsHash"])
            self.source("capture", tradeId=trade, orderId=trade,
                        paymentId=f"payment-{trade}", buyer=buyer,
                        amount=amount, currency="KRW")
            if settle:
                self.source("settle_capture", tradeId=trade, paymentId=f"payment-{trade}",
                            sourceId=f"deposit-{trade}", amount=settle, currency="KRW")
            self.call("commit_trade", tradeId=trade)

        def finish(self, effect):
            self.call("send_effect", effectId=effect)
            x = self.core.snapshot()["effects"][effect]
            for phase in ("STATUS", "FUNDS"):
                self.source("observe_effect", effectId=effect, phase=phase,
                            sourceId=f"{effect}-{phase}", status="SUCCESS" if phase == "STATUS" else None,
                            amount=x["amount"], currency="KRW",
                            paymentId=x["paymentId"], beneficiary=x["beneficiary"])

    results = []

    def record(case_id, category, observations):
        results.append(dict(id=case_id, category=category, observations=observations,
                            meaning="current behavior reproduced; not an acceptance-test pass"))

    d = Driver(); d.event(); d.buy()
    d.call("complete_event", eventId="show")
    d.call("prepare_effect", effectId="p", tradeId="primary", kind="PAYOUT",
           amount=95000, allocationId="primary-0")
    d.call("cancel_event", eventId="show")
    f = d.core.view("finance-adapter", "show", "finance")
    result = d.call("send_effect", effectId="p")
    assert d.core.snapshot()["effects"]["p"]["sent"] is True
    assert f["refundOutstanding"] == 0 and f["refundPlansPending"] == 1
    record("C01", "missing dispatch revalidation and monetary exposure field", dict(
        eventStatus="CANCELLED", unsentPayoutCanBecomeSent=True,
        returnedRequestAmount=result["result"]["unsentFixtureRequest"]["amount"], finance=f))
    d.core.db.close()

    d = Driver(); d.event(); d.buy(settle=0)
    d.call("cancel_event", eventId="show")
    try:
        d.call("prepare_effect", effectId="r", tradeId="primary", kind="REFUND", amount=100000)
        raise AssertionError("expected fixture cash gate")
    except Rejected as exc:
        assert str(exc) == "INSUFFICIENT_CONFIRMED_FUNDS"
        record("C02", "cash-only refund profile limitation", dict(
            error=str(exc), refundDue=100000, captured=True, settled=0))
    d.core.db.close()

    d = Driver(); d.event(); d.buy(settle=97000)
    d.call("complete_event", eventId="show")
    d.call("prepare_effect", effectId="p1", tradeId="primary", kind="PAYOUT",
           amount=95000, allocationId="primary-0")
    d.finish("p1")
    try:
        d.call("prepare_effect", effectId="p2", tradeId="primary", kind="PAYOUT",
               amount=5000, allocationId="primary-1")
        raise AssertionError("expected shortage with fee-shaped input")
    except Rejected as exc:
        assert str(exc) == "INSUFFICIENT_CONFIRMED_FUNDS"
        s = d.core.snapshot()
        assert s["balances"]["pg:primary"] == 3000
        record("C03", "net-settlement fee unsupported", dict(
            gross=100000, netReceipt=97000, unclassifiedPGReceivable=3000,
            remainingCash=sum(v for k, v in s["balances"].items() if k.startswith("funds:")),
            platformPayable=5000, error=str(exc)))
    d.core.db.close()

    d = Driver(); d.event(); d.buy()
    d.call("refund_ticket", "A", ticketId="show/A1", expectedVersion=1)
    d.call("prepare_effect", effectId="r", tradeId="primary", kind="REFUND", amount=100000)
    d.finish("r")
    t = d.core.snapshot()["tickets"]["show/A1"]
    try:
        d.call("prepare_trade", "B", tradeId="new-sale", ticketId="show/A1",
               buyer="B", amount=100000, expectedVersion=t["rightsVersion"])
        raise AssertionError("expected missing reissue path")
    except Rejected as exc:
        assert str(exc) == "RIGHT_NOT_TRANSFERABLE"
        record("C04", "inventory-reissue lifecycle missing", dict(
            eventStatus="OPEN", ticketState=t["state"], fullyRefunded=True, error=str(exc)))
    d.core.db.close()

    d = Driver(); d.event(); d.buy()
    d.buy("resale", "B", 120000, 120000)
    d.call("refund_ticket", "B", ticketId="show/A1", expectedVersion=2)
    obligations = {k: {"buyer": r["buyer"], "refundDue": r["refundDue"]}
                   for k, r in d.core.snapshot()["trades"].items()}
    assert obligations == {"primary": {"buyer": "A", "refundDue": 100000},
                           "resale": {"buyer": "B", "refundDue": 120000}}
    record("C05", "explicit full-chain-unwind product choice", obligations)
    d.core.db.close()

    d = Driver(); d.event(); d.buy()
    try:
        d.call("prepare_trade", "A", tradeId="gift", ticketId="show/A1",
               buyer="B", amount=0, expectedVersion=1)
        raise AssertionError("expected missing free transfer route")
    except Rejected as exc:
        assert str(exc) == "INVALID_AMOUNT"
        record("C06", "gift command missing", {"error": str(exc)})
    d.core.db.close()

    d = Driver(); d.event(); d.buy()
    before = d.core.snapshot()
    try:
        d.source("capture", tradeId="primary", orderId="primary",
                 paymentId="second-real-payment", buyer="A", amount=100000, currency="KRW")
        raise AssertionError("expected second-payment review rejection")
    except Rejected as exc:
        assert str(exc) == "SECOND_PAYMENT_REQUIRES_SEPARATE_REVIEW"
        assert d.core.snapshot() == before
        record("C07", "raw inbox missing, already disclosed", dict(
            error=str(exc), rejectedObservationPersisted=False, stateUnchanged=True))
    d.core.db.close()

    d = Driver(); d.event()
    d.call("set_consent", "A", eventId="show", purpose="next_event_marketing", allowed=True)
    d.call("set_consent", "A", eventId="show", purpose="next_event_marketing", allowed=False)
    # Simulates an earlier positive intent arriving with a DISTINCT command id.
    # Same-operation-id replay is correctly idempotent in the original model.
    d.call("set_consent", "A", eventId="show", purpose="next_event_marketing", allowed=True)
    marketing = d.core.view("marketing-adapter", "show", "marketing")
    assert len(marketing) == 1 and marketing[0]["consentVersion"] == 3
    record("C08", "no causal consent-version precondition", dict(
        semantics="distinct-id positive intent after revocation accepted; freshness not distinguishable",
        marketing=marketing))
    d.core.db.close()

    d = Driver(); d.event()
    r = d.call("prepare_trade", "A", tradeId="주문 1", ticketId="show/A1",
               buyer="A", amount=100000, expectedVersion=0)
    assert r["result"]["externalOrderId"] == "주문 1"
    record("C09", "provider identifier mapping missing", dict(
        returnedExternalOrderId=r["result"]["externalOrderId"],
        note="Toss orderId requires 6-64 characters from its documented ASCII alphabet"))
    try:
        d.source("capture", tradeId="주문 1", orderId="주문 1", paymentId="p" * 150,
                 buyer="A", amount=100000, currency="KRW")
        raise AssertionError("expected local 100-character id limit")
    except Rejected as exc:
        assert str(exc) == "INVALID_ID"
        record("C10", "provider payment id truncated contract", dict(
            paymentKeyLength=150, error=str(exc), note="Toss documents maximum 200 characters"))
    d.core.db.close()
    return results


MUTATIONS = [
    ("M01", "remove old-holder/version presentation guard",
     '        require(b["holder"]==t["owner"] and b["expectedVersion"]==t["rightsVersion"] and b["admissionEpoch"]==t["admissionEpoch"],"STALE_OR_WRONG_PRESENTATION")',
     '        pass # mutation: omit holder/version presentation guard'),
    ("M02", "allow admission while trade locked",
     '        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")',
     '        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE","RIGHT_NOT_ADMISSIBLE")'),
    ("M03", "FUNDS also confirms result",
     '            x["fundsObserved"]=True',
     '            x["fundsObserved"]=True; x["confirmed"]=True'),
    ("M04", "ignore effect beneficiary",
     ' and b["beneficiary"]==x["beneficiary"] and b["paymentId"]==x["paymentId"]',
     ' and b["paymentId"]==x["paymentId"]'),
    ("M05", "revocation remains allowed",
     '            allowed=b["allowed"],version=prior["version"]+1,operationId=self.op)',
     '            allowed=True,version=prior["version"]+1,operationId=self.op)'),
    ("M06", "ignore OPEN at admission",
     '        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")',
     '        require(t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")'),
    ("M07", "ignore caller expectedVersion when preparing trade",
     '        require(type(b["expectedVersion"]) is int and t["rightsVersion"] == b["expectedVersion"], "STALE_RIGHTS_VERSION")',
     '        require(type(b["expectedVersion"]) is int, "STALE_RIGHTS_VERSION")'),
    ("M08", "remove commit actor guard",
     '        self.role("operator"); tid=b["tradeId"]; r=self.trade(tid); t=self.ticket(r["ticket"]); e=self.event(r["event"])',
     '        tid=b["tradeId"]; r=self.trade(tid); t=self.ticket(r["ticket"]); e=self.event(r["event"])'),
    ("M09", "remove refund owner guard",
     '        t=self.ticket(b["ticketId"]); self.role(t["owner"])\n        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_REFUNDABLE")',
     '        t=self.ticket(b["ticketId"])\n        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_REFUNDABLE")'),
    ("M10", "omit final-controller-log provenance requirement",
     '        require(type(b["used"]) is bool and b.get("provenance")=="synthetic_final_controller_log","FINAL_USE_RESULT_REQUIRED")',
     '        require(type(b["used"]) is bool,"FINAL_USE_RESULT_REQUIRED")'),
]


WITNESS_PROGRAM = r'''
import json, sys
from core import Core, Rejected
c=Core(); seq=0
def call(action,actor="operator",**body):
 global seq
 seq+=1
 return c.execute("witness-"+str(seq),actor,action,dict(domain=Core.DOMAIN,**body))
policy=dict(primaryPrice=100000,resaleCap=150000,primaryFeeBps=500,
 resaleFeeBps=300,resaleOrganizerBps=200,resaleAllowed=True,refundProfile="FULL_CHAIN_UNWIND_FIXTURE")
call("create_event",eventId="show",organizer="organizer",policy=policy,seats=["A1"])
call("prepare_trade","A",tradeId="primary",ticketId="show/A1",buyer="A",amount=100000,expectedVersion=0)
call("capture","pg-adapter",scope=Core.SCOPE,provenance="synthetic",tradeId="primary",orderId="primary",
 paymentId="payment-primary",buyer="A",amount=100000,currency="KRW")
mid=sys.argv[1]
if mid!="M08": call("commit_trade",tradeId="primary")
if mid=="M06": call("complete_event",eventId="show")
if mid=="M10": d=call("delegate","A",ticketId="show/A1",expectedVersion=1)["result"]
try:
 if mid=="M06": call("admit","venue",ticketId="show/A1",holder="A",expectedVersion=1,admissionEpoch=1)
 elif mid=="M07": call("prepare_trade","A",tradeId="resale",ticketId="show/A1",buyer="B",amount=120000,expectedVersion=0)
 elif mid=="M08": call("commit_trade","intruder",tradeId="primary")
 elif mid=="M09": call("refund_ticket","intruder",ticketId="show/A1",expectedVersion=1)
 elif mid=="M10": call("close_delegation","venue",ticketId="show/A1",session=d["session"],admissionEpoch=d["admissionEpoch"],used=False)
 else: raise ValueError(mid)
 print(json.dumps({"result":"ACCEPTED"}))
except Rejected as exc:
 print(json.dumps({"result":"REJECTED","reason":str(exc)}))
finally: c.db.close()
'''


def mutations(root, out):
    results = []
    text = (root / "core.py").read_text()
    log_dir = out / "mutation_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    for mid, description, old, new in MUTATIONS:
        assert text.count(old) == 1, (mid, text.count(old))
        with tempfile.TemporaryDirectory(prefix="kix-review-mutation-") as temp:
            work = Path(temp) / "bundle"
            shutil.copytree(root, work, ignore=shutil.ignore_patterns("__pycache__", "results"))
            (work / "core.py").write_text(text.replace(old, new))
            p = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_core"],
                               cwd=work, capture_output=True, text=True, timeout=30)
            log = p.stdout + p.stderr
            (log_dir / f"{mid}.txt").write_text(log)
            # Only assertion failures count as killed; crashes are separate.
            if p.returncode == 0:
                verdict = "SURVIVED"
            elif "FAIL:" in log and "ERROR:" not in log:
                verdict = "KILLED_BY_ASSERTION"
            else:
                verdict = "ERROR_OR_INVALID_RUN"
            witness = None
            if mid in {"M06", "M07", "M08", "M09", "M10"}:
                base = subprocess.run([sys.executable, "-c", WITNESS_PROGRAM, mid],
                                      cwd=root, capture_output=True, text=True, timeout=10, check=True)
                mutant = subprocess.run([sys.executable, "-c", WITNESS_PROGRAM, mid],
                                        cwd=work, capture_output=True, text=True, timeout=10, check=True)
                witness = dict(original=json.loads(base.stdout), mutant=json.loads(mutant.stdout))
                assert witness["original"]["result"] == "REJECTED", witness
                assert witness["mutant"]["result"] == "ACCEPTED", witness
            results.append(dict(id=mid, description=description, result=verdict,
                                returncode=p.returncode,
                                failingTests=[line for line in log.splitlines() if line.startswith(("FAIL:", "ERROR:"))],
                                patch=dict(old=old, new=new), nonEquivalentWitness=witness))
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root = args.bundle.resolve(); out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    expected = json.loads((root / "results/manifest.sha256.json").read_text())
    hashes = {n: hashlib.sha256((root / n).read_bytes()).hexdigest() == sha for n, sha in expected.items()}
    if not all(hashes.values()):
        raise RuntimeError("input differs from supplied bundle manifest")
    results = dict(scope="bounded review, original Core and disposable one-line mutants; synthetic only",
                   inputCoreSHA256=hashlib.sha256((root / "core.py").read_bytes()).hexdigest(),
                   environment=dict(python=platform.python_version(), sqlite=sqlite3.sqlite_version),
                   hashes=hashes, probes=probes(root), mutations=mutations(root, out))
    (out / "review_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"probes_reproduced": len(results["probes"]),
                      "mutations": [{"id": r["id"], "result": r["result"]} for r in results["mutations"]]}, indent=2))


if __name__ == "__main__":
    main()
