"""KIX lifecycle executable reference specification; synthetic inputs ONLY.

SQLite is the sole authority in this model. No PG, chain, authenticated API,
zero-knowledge proof, bank account, or physical gate is implemented here.
Actor/source strings are fixture assumptions, never production credentials.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sqlite3

from common import Rejected, require, canonical, digest, positive, ident, external_id
from finance import FinanceMixin
from lifecycle import LifecycleMixin
from observations import ObservationMixin
from contracts import validate_command, SOURCE_ACTIONS
from dispatch import DispatchMixin


class Core(DispatchMixin, FinanceMixin, LifecycleMixin, ObservationMixin):
    DOMAIN = "kix:fixture:lifecycle:0.3"
    SCOPE = {"provider": "toss", "environment": "test", "merchant": "kix-fixture", "channel": "card"}

    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS commands (operation_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, receipt TEXT NOT NULL)")
        initial = dict(domain=self.DOMAIN, events={}, tickets={}, trades={}, effects={},
                       evidence={}, payment_bindings={}, balances={}, journal=[], events_log=[], consents={}, inventory={}, listings={}, gifts={}, refund_cases={}, clock=0)
        self.db.execute("INSERT OR IGNORE INTO state VALUES(1,?)", (canonical(initial),))
        require(self.snapshot()["domain"] == self.DOMAIN, "DOMAIN_MISMATCH")
        self.init_inbox()
        self.db.execute("CREATE TABLE IF NOT EXISTS command_inputs (operation_id TEXT PRIMARY KEY, actor TEXT, action TEXT, body TEXT)")

    def snapshot(self):
        return json.loads(self.db.execute("SELECT body FROM state WHERE id=1").fetchone()[0])

    def execute(self, operation_id, actor, action, body, *, fail_before_commit=False, lose_response=False, _observation_id=None):
        ident(operation_id); ident(actor)
        validate_command(action, body)
        require(isinstance(body, dict) and body.get("domain") == self.DOMAIN, "DOMAIN_MISMATCH")
        fingerprint = digest(dict(actor=actor, action=action, body=body))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute("SELECT fingerprint,receipt FROM commands WHERE operation_id=?", (operation_id,)).fetchone()
            if old:
                require(old[0] == fingerprint, "OPERATION_ID_CONFLICT")
                receipt = json.loads(old[1])
                if _observation_id is not None: self.mark_observation_applied(_observation_id)
                self.db.execute("COMMIT")
                return self.replay_receipt(action, receipt, body)
            self.s = self.snapshot()
            self.actor, self.op = actor, operation_id
            result = getattr(self, "_" + action)(copy.deepcopy(body))
            self.invalidate_offers()
            self.check(self.s)
            seq = len(self.s["events_log"]) + 1
            receipt = dict(domain=self.DOMAIN, operationId=operation_id, sequence=seq,
                           action=action, result=result)
            self.s["events_log"].append(receipt)
            if action in SOURCE_ACTIONS:
                self.record_source_fact(_observation_id or operation_id, dict(action=action,body=body),
                                        applied=(operation_id, seq) if result.get("financialApplication",True) else None, state=self.s)
            if _observation_id is not None: self.mark_observation_applied(_observation_id)
            self.db.execute("UPDATE state SET body=? WHERE id=1", (canonical(self.s),))
            self.db.execute("INSERT INTO commands VALUES(?,?,?)", (operation_id, fingerprint, canonical(receipt)))
            self.db.execute("INSERT INTO command_inputs VALUES(?,?,?,?)", (operation_id, actor, action, canonical(body)))
            if fail_before_commit:
                raise RuntimeError("INJECTED_BEFORE_COMMIT")
            self.db.execute("COMMIT")
        except BaseException:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        if lose_response:
            raise ConnectionError("INJECTED_RESPONSE_LOSS_AFTER_COMMIT")
        return receipt

    def role(self, *actors):
        require(self.actor in actors, "UNAUTHORIZED_FIXTURE_ACTOR")

    def event(self, event_id):
        require(event_id in self.s["events"], "EVENT_NOT_FOUND")
        return self.s["events"][event_id]

    def ticket(self, ticket_id):
        require(ticket_id in self.s["tickets"], "TICKET_NOT_FOUND")
        return self.s["tickets"][ticket_id]

    def trade(self, trade_id):
        require(trade_id in self.s["trades"], "TRADE_NOT_FOUND")
        return self.s["trades"][trade_id]

    def balance(self, account):
        return self.s["balances"].get(account, 0)

    def post(self, debit, credit, amount, reason):
        positive(amount)
        for account, delta in ((debit, amount), (credit, -amount)):
            self.s["balances"][account] = self.balance(account) + delta
        self.s["journal"].append(dict(operation=self.op, debit=debit, credit=credit,
                                      amount=amount, currency="KRW", reason=reason))

    def evidence(self, namespace, source_id, binding):
        self.role("pg-adapter")
        key = canonical([self.SCOPE, namespace, external_id(source_id)])
        old = self.s["evidence"].get(key)
        if old is not None:
            require(old == binding, "SOURCE_EVIDENCE_CONFLICT")
            return False
        self.s["evidence"][key] = binding
        return True

    def source(self, b):
        self.role("pg-adapter")
        require(b.get("scope") == self.SCOPE and b.get("provenance") == "synthetic", "SOURCE_SCOPE_MISMATCH")



    def _accept_trade(self, b):
        r = self.trade(b["tradeId"]); self.role(r["buyer"])
        require(r["status"] == "PREPARED" and self.event(r["event"])["status"] == "OPEN" and self.s["clock"] < r["expiresAt"], "TRADE_NOT_ACCEPTABLE")
        require(b["termsHash"] == r["termsHash"], "TERMS_MISMATCH")
        r["accepted"] = True
        return {"accepted": True}

    def _capture(self, b):
        self.source(b); tid=b["tradeId"]; r=self.trade(tid)
        positive(b["amount"])
        require(r["accepted"], "BUYER_HAS_NOT_ACCEPTED")
        require(b["orderId"] == r["externalOrderId"] and b["amount"] == r["amount"] and b["currency"] == r["currency"] and b["buyer"] == r["buyer"], "CAPTURE_BINDING_MISMATCH")
        pid=external_id(b["paymentId"])
        binding=dict(trade=tid, buyer=r["buyer"], amount=r["amount"], currency=r["currency"])
        if not self.evidence("payment", pid, binding):
            return {"duplicate": True}
        require(not r["captured"], "SECOND_PAYMENT_REQUIRES_SEPARATE_REVIEW")
        r["captured"]=True; r["paymentId"]=pid
        self.s["payment_bindings"][pid]=tid
        self.post("pg:"+tid, "held:"+tid, r["amount"], "capture confirmed; not spendable cash")
        if r["status"] == "VOID" or self.event(r["event"])["status"] == "CANCELLED" or self.s["clock"] >= r["expiresAt"]:
            self.reverse(tid)
        return {"captured": True, "cashAvailable": False}


    def _commit_trade(self, b):
        self.role("operator"); tid=b["tradeId"]; r=self.trade(tid); t=self.ticket(r["ticket"]); e=self.event(r["event"])
        require(e["status"] == "OPEN" and r["status"] == "PREPARED" and r["captured"] and r["accepted"] and self.s["clock"] < r["expiresAt"], "TRADE_NOT_COMMITTABLE")
        require(t["lock"] == tid and t["rightsVersion"] == r["expectedVersion"] and t["state"] in ("AVAILABLE", "ACTIVE"), "RIGHTS_CONFLICT")
        p=e["policy"]; price=r["amount"]
        require(e["salesStatus"]=="OPEN", "SALES_CLOSED")
        if r["kind"] == "PRIMARY":
            fee=price*p["primaryFeeBps"]//10000
            splits=[(e["organizer"], price-fee),("platform",fee)]
        else:
            fee=price*p["resaleFeeBps"]//10000; royalty=price*p["resaleOrganizerBps"]//10000
            splits=[(r["seller"],price-fee-royalty),(e["organizer"],royalty),("platform",fee)]
        for index,(payee,n) in enumerate(splits):
            if not n: continue
            aid=tid+"-"+str(index)
            r["allocations"].append(dict(id=aid,payee=payee,amount=n,paid=0,recovered=0,returned=0))
            self.post("held:"+tid,"payable:"+aid,n,"allocate frozen policy")
        r["allocationVersion"]+=1; r["status"]="COMMITTED"; t["owner"]=r["buyer"]; t["state"]="ACTIVE"; t["lock"]=None
        t["rightsVersion"]+=1; t["admissionEpoch"]+=1
        return {"ticketId":r["ticket"],"owner":t["owner"],"rightsVersion":t["rightsVersion"],"admissionEpoch":t["admissionEpoch"]}


    def _abort_trade(self,b):
        tid=b["tradeId"]; r=self.trade(tid)
        self.role("operator",r["buyer"],r["seller"])
        require(r["status"]=="PREPARED","TRADE_NOT_ABORTABLE")
        r["status"]="VOID"; t=self.ticket(r["ticket"])
        require(t["lock"]==tid,"LOCK_MISMATCH"); t["lock"]=None
        self.reverse(tid)
        return {"status":"VOID","refundDue":r["refundDue"]}


    def _refund_ticket(self,b):
        t=self.ticket(b["ticketId"]); self.role(t["owner"])
        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_REFUNDABLE")
        require(b["expectedVersion"]==t["rightsVersion"],"STALE_RIGHTS_VERSION")
        self.terminate_ticket(t, "CURRENT_HOLDER_REFUND")
        return {"rightsState":t["state"],"refundComplete":False}

    def _cancel_event(self,b):
        e=self.event(b["eventId"]); self.role("operator",e["organizer"])
        e["status"]="CANCELLED"; e["salesStatus"]="CLOSED"; e["admissionStatus"]="CLOSED"
        for t in self.s["tickets"].values():
            if t["event"]==b["eventId"] and t["state"] not in ("VOID","CANCEL_PENDING_CLOSE"):
                self.terminate_ticket(t, "EVENT_CANCELLED")
        # Event-wide cancellation includes earlier refunded/closed issuances.
        for tid,r in self.s["trades"].items():
            if r["event"]==b["eventId"]: self.reverse(tid, "EVENT_CANCELLED")
        return {"eventStatus":"CANCELLED"}

    def _complete_event(self,b):
        e=self.event(b["eventId"]); self.role("operator",e["organizer"])
        require(e["status"]=="OPEN","EVENT_NOT_OPEN"); e["status"]="COMPLETED"; e["salesStatus"]="CLOSED"; e["admissionStatus"]="CLOSED"
        # Void unfinished checkout so late payments cannot strand a held balance.
        for tid,r in self.s["trades"].items():
            if r["event"]==b["eventId"] and r["status"]=="PREPARED":
                r["status"]="VOID"; self.ticket(r["ticket"])["lock"]=None; self.reverse(tid)
        return {"eventStatus":"COMPLETED"}

    def _admit(self,b):
        self.role("venue"); t=self.ticket(b["ticketId"])
        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")
        require(self.event(t["event"])["admissionStatus"]=="OPEN", "ADMISSION_CLOSED")
        require(b["holder"]==t["owner"] and b["expectedVersion"]==t["rightsVersion"] and b["admissionEpoch"]==t["admissionEpoch"],"STALE_OR_WRONG_PRESENTATION")
        t["state"]="CONSUMED"; t["used"]=True; t["rightsVersion"]+=1; t["admissionEpoch"]+=1
        return {"admissionId":self.op,"decision":"ADMITTED_ONCE"}

    def _delegate(self,b):
        t=self.ticket(b["ticketId"]); self.role(t["owner"])
        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_DELEGATABLE")
        require(b["expectedVersion"]==t["rightsVersion"],"STALE_RIGHTS_VERSION")
        t["state"]="DELEGATED"; t["rightsVersion"]+=1; t["admissionEpoch"]+=1
        t["session"]=digest([self.DOMAIN,b["ticketId"],self.op,t["admissionEpoch"],"venue"])
        return {"session":t["session"],"admissionEpoch":t["admissionEpoch"]}

    def _close_delegation(self,b):
        self.role("venue"); t=self.ticket(b["ticketId"])
        require(t["state"] in ("DELEGATED","CANCEL_PENDING_CLOSE") and t["session"]==b["session"] and t["admissionEpoch"]==b["admissionEpoch"],"DELEGATION_SCOPE_MISMATCH")
        require(type(b["used"]) is bool and b.get("provenance")=="synthetic_final_controller_log","FINAL_USE_RESULT_REQUIRED")
        t["used"]=b["used"]; t["session"]=None; t["rightsVersion"]+=1; t["admissionEpoch"]+=1
        t["state"]="VOID" if self.event(t["event"])["status"]=="CANCELLED" else "CONSUMED" if b["used"] else "ACTIVE"
        return {"rightsState":t["state"]}






    def _observe_recovery(self,b):
        self.source(b); r=self.trade(b["tradeId"]); n=positive(b["amount"])
        a=next((a for a in r["allocations"] if a["id"]==b["allocationId"]),None)
        require(a is not None and b["payer"]==a["payee"] and b["currency"]=="KRW","RECOVERY_BINDING_MISMATCH")
        if not self.evidence("funds",b["movementId"],dict(kind="RECOVERY",trade=b["tradeId"],allocation=a["id"],amount=n)): return {"duplicate":True}
        require(n<=self.balance("recoverable:"+a["id"]),"EXCESS_RECOVERY")
        self.post("funds:"+r["pool"],"recoverable:"+a["id"],n,"actual beneficiary recovery observed")
        a["recovered"]+=n
        return {"recovered":a["recovered"]}


