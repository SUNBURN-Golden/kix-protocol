"""Run the bounded integration suite and write reproducible synthetic traces."""
import hashlib
import io
import json
from pathlib import Path
import platform
import sqlite3
import sys
import unittest
import cryptography
from test_core import Harness

ROOT=Path(__file__).resolve().parent


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs): super().__init__(*args,**kwargs); self.passed=[]
    def addSuccess(self,test): super().addSuccess(test); self.passed.append(test.id())


def main():
    out=ROOT/"results"; out.mkdir(exist_ok=True)
    buffer=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT),pattern="test_core.py")
    result=unittest.TextTestRunner(stream=buffer,verbosity=2,resultclass=RecordedResult).run(suite)
    (out/"tests.txt").write_text(buffer.getvalue())
    summary=dict(scope="synthetic SQLite reference model and two existing-model contract checks",
        testsRun=result.testsRun,passed=result.passed,failures=[(str(t),err) for t,err in result.failures],
        errors=[(str(t),err) for t,err in result.errors],successful=result.wasSuccessful(),
        environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,cryptography=cryptography.__version__),
        chainTransactions=0,providerRequestsSent=0,realFundsMoved=0)
    (out/"verification.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    require=result.wasSuccessful()
    if not require:
        print(buffer.getvalue()); return 1
    traces={}
    h=Harness(); h.chain()
    traces["after_resale"]=h.c.view("finance-adapter","show","finance")
    h.run("admit","venue",ticketId="show/A1",holder="B",expectedVersion=2,admissionEpoch=2)
    h.run("complete_event",eventId="show"); h.payout_all()
    traces["after_payout"]=h.c.snapshot()
    h.run("cancel_event",eventId="show")
    traces["cancellation_after_payout"]=h.c.snapshot()
    for tid,r in h.c.snapshot()["trades"].items():
        for a in r["allocations"]:
            h.source("observe_recovery",tradeId=tid,allocationId=a["id"],payer=a["payee"],
                     amount=a["paid"],currency="KRW",sourceId="recover-"+a["id"])
    h.refund_all(); traces["after_recovery_and_refund"]=h.c.snapshot(); h.c.db.close()
    (out/"synthetic_lifecycle_trace.json").write_text(json.dumps(traces,ensure_ascii=False,indent=2))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name!="manifest.sha256.json"}
    (out/"manifest.sha256.json").write_text(json.dumps(hashes,ensure_ascii=False,indent=2))
    print(json.dumps({"tests":result.testsRun,"passed":len(result.passed),"chain_transactions":0,"provider_requests_sent":0}))
    return 0


if __name__=="__main__": sys.exit(main())
