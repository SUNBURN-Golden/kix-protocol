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


class Rejected(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Rejected(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def positive(n):
    require(type(n) is int and 0 < n <= 10**12, "INVALID_AMOUNT")
    return n


def ident(value):
    require(isinstance(value, str) and 0 < len(value) <= 100 and value.strip() == value,
            "INVALID_ID")
    return value


class Core:
    DOMAIN = "kix:fixture:lifecycle:0.1"
    SCOPE = {"provider": "toss", "environment": "test", "merchant": "kix-fixture", "channel": "card"}

    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS commands (operation_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, receipt TEXT NOT NULL)")
        initial = dict(domain=self.DOMAIN, events={}, tickets={}, trades={}, effects={},
                       evidence={}, payment_bindings={}, balances={}, journal=[], events_log=[], consents={})
        self.db.execute("INSERT OR IGNORE INTO state VALUES(1,?)", (canonical(initial),))
        require(self.snapshot()["domain"] == self.DOMAIN, "DOMAIN_MISMATCH")

    def snapshot(self):
        return json.loads(self.db.execute("SELECT body FROM state WHERE id=1").fetchone()[0])

    def execute(self, operation_id, actor, action, body, *, fail_before_commit=False, lose_response=False):
        ident(operation_id); ident(actor)
        require(action in ACTIONS, "UNKNOWN_ACTION")
        require(isinstance(body, dict) and body.get("domain") == self.DOMAIN, "DOMAIN_MISMATCH")
        fingerprint = digest(dict(actor=actor, action=action, body=body))
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute("SELECT fingerprint,receipt FROM commands WHERE operation_id=?", (operation_id,)).fetchone()
            if old:
                require(old[0] == fingerprint, "OPERATION_ID_CONFLICT")
                receipt = json.loads(old[1]); self.db.execute("COMMIT")
                return receipt
            self.s = self.snapshot()
            self.actor, self.op = actor, operation_id
            result = getattr(self, "_" + action)(copy.deepcopy(body))
            self.check(self.s)
            seq = len(self.s["events_log"]) + 1
            receipt = dict(domain=self.DOMAIN, operationId=operation_id, sequence=seq,
                           action=action, result=result)
            self.s["events_log"].append(receipt)
            self.db.execute("UPDATE state SET body=? WHERE id=1", (canonical(self.s),))
            self.db.execute("INSERT INTO commands VALUES(?,?,?)", (operation_id, fingerprint, canonical(receipt)))
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
        key = canonical([self.SCOPE, namespace, ident(source_id)])
        old = self.s["evidence"].get(key)
        if old is not None:
            require(old == binding, "SOURCE_EVIDENCE_CONFLICT")
            return False
        self.s["evidence"][key] = binding
        return True

    def source(self, b):
        self.role("pg-adapter")
        require(b.get("scope") == self.SCOPE and b.get("provenance") == "synthetic", "SOURCE_SCOPE_MISMATCH")

    def _create_event(self, b):
        self.role("operator")
        eid = ident(b["eventId"])
        require(eid not in self.s["events"], "EVENT_EXISTS")
        p = b["policy"]
        require(set(p) == {"primaryPrice", "resaleCap", "primaryFeeBps", "resaleFeeBps", "resaleOrganizerBps", "resaleAllowed", "refundProfile"}, "INVALID_POLICY")
        positive(p["primaryPrice"]); positive(p["resaleCap"])
        require(type(p["resaleAllowed"]) is bool and p["refundProfile"] == "FULL_CHAIN_UNWIND_FIXTURE", "UNSUPPORTED_POLICY")
        for k in ("primaryFeeBps", "resaleFeeBps", "resaleOrganizerBps"):
            require(type(p[k]) is int and 0 <= p[k] <= 10000, "INVALID_BPS")
        require(p["resaleFeeBps"] + p["resaleOrganizerBps"] <= 10000, "INVALID_SPLIT")
        require(isinstance(b["seats"], list) and 0 < len(b["seats"]) <= 300, "INVALID_SEATS")
        require(len(set(b["seats"])) == len(b["seats"]), "DUPLICATE_SEAT")
        self.s["events"][eid] = dict(status="OPEN", organizer=ident(b["organizer"]),
                                      policy=p, policyHash=digest(p), pool=digest([eid, self.SCOPE]))
        for seat in b["seats"]:
            ident(seat)
            tid = eid + "/" + seat
            require(tid not in self.s["tickets"], "TICKET_EXISTS")
            self.s["tickets"][tid] = dict(event=eid, seat=seat, state="AVAILABLE", owner=None,
                rightsVersion=0, admissionEpoch=0, lock=None, trades=[], session=None, used=False)
        return {"eventId": eid, "policyHash": digest(p)}

    def _prepare_trade(self, b):
        tid = ident(b["tradeId"]); require(tid not in self.s["trades"], "TRADE_EXISTS")
        t = self.ticket(b["ticketId"]); e = self.event(t["event"])
        require(e["status"] == "OPEN" and t["lock"] is None, "EVENT_CLOSED_OR_TICKET_LOCKED")
        require(type(b["expectedVersion"]) is int and t["rightsVersion"] == b["expectedVersion"], "STALE_RIGHTS_VERSION")
        require(t["state"] in ("AVAILABLE", "ACTIVE"), "RIGHT_NOT_TRANSFERABLE")
        buyer = ident(b["buyer"]); price = positive(b["amount"])
        primary = t["state"] == "AVAILABLE"
        if primary:
            self.role(buyer); require(price == e["policy"]["primaryPrice"], "PRIMARY_PRICE_MISMATCH")
        else:
            self.role(t["owner"])
            require(e["policy"]["resaleAllowed"] and buyer != t["owner"] and price <= e["policy"]["resaleCap"], "RESALE_POLICY_REJECTED")
        r = dict(id=tid, ticket=b["ticketId"], event=t["event"], kind="PRIMARY" if primary else "RESALE",
            seller=t["owner"], buyer=buyer, amount=price, currency="KRW", policyHash=e["policyHash"],
            expectedVersion=t["rightsVersion"], expectedAdmissionEpoch=t["admissionEpoch"], accepted=primary, status="PREPARED", captured=False,
            paymentId=None, settled=0, allocations=[], refundDue=0, refunded=0,
            reversalRequested=False, reversalPlanned=False, pool=digest([e["pool"],tid]))
        r["termsHash"]=digest(dict(domain=self.DOMAIN,scope=self.SCOPE,
            terms={k:r[k] for k in ("id","event","kind","ticket","buyer","seller","amount","currency","policyHash","expectedVersion","expectedAdmissionEpoch")}))
        self.s["trades"][tid] = r; t["lock"] = tid; t["trades"].append(tid)
        return {"tradeId": tid, "externalOrderId": tid, "status": "PREPARED", "termsHash":r["termsHash"]}

    def _accept_trade(self, b):
        r = self.trade(b["tradeId"]); self.role(r["buyer"])
        require(r["status"] == "PREPARED" and self.event(r["event"])["status"] == "OPEN", "TRADE_NOT_ACCEPTABLE")
        require(b["termsHash"] == r["termsHash"], "TERMS_MISMATCH")
        r["accepted"] = True
        return {"accepted": True}

    def _capture(self, b):
        self.source(b); tid=b["tradeId"]; r=self.trade(tid)
        positive(b["amount"])
        require(r["accepted"], "BUYER_HAS_NOT_ACCEPTED")
        require(b["orderId"] == tid and b["amount"] == r["amount"] and b["currency"] == r["currency"] and b["buyer"] == r["buyer"], "CAPTURE_BINDING_MISMATCH")
        pid=ident(b["paymentId"])
        binding=dict(trade=tid, buyer=r["buyer"], amount=r["amount"], currency=r["currency"])
        if not self.evidence("payment", pid, binding):
            return {"duplicate": True}
        require(not r["captured"], "SECOND_PAYMENT_REQUIRES_SEPARATE_REVIEW")
        r["captured"]=True; r["paymentId"]=pid
        self.s["payment_bindings"][pid]=tid
        self.post("pg:"+tid, "held:"+tid, r["amount"], "capture confirmed; not spendable cash")
        if r["status"] == "VOID" or self.event(r["event"])["status"] == "CANCELLED":
            self.reverse(tid)
        return {"captured": True, "cashAvailable": False}

    def _settle_capture(self, b):
        self.source(b); tid=b["tradeId"]; r=self.trade(tid); n=positive(b["amount"])
        require(r["captured"] and b["paymentId"] == r["paymentId"] and b["currency"] == r["currency"], "SETTLEMENT_BINDING_MISMATCH")
        if not self.evidence("funds", b["sourceId"], dict(kind="IN", trade=tid, amount=n, pool=r["pool"])):
            return {"duplicate": True}
        require(r["settled"]+n <= r["amount"], "EXCESS_SETTLEMENT")
        r["settled"]+=n
        self.post("funds:"+r["pool"], "pg:"+tid, n, "synthetic actual net receipt; zero PG fee fixture")
        return {"settled": r["settled"]}

    def _commit_trade(self, b):
        self.role("operator"); tid=b["tradeId"]; r=self.trade(tid); t=self.ticket(r["ticket"]); e=self.event(r["event"])
        require(e["status"] == "OPEN" and r["status"] == "PREPARED" and r["captured"] and r["accepted"], "TRADE_NOT_COMMITTABLE")
        require(t["lock"] == tid and t["rightsVersion"] == r["expectedVersion"] and t["state"] in ("AVAILABLE", "ACTIVE"), "RIGHTS_CONFLICT")
        p=e["policy"]; price=r["amount"]
        if r["kind"] == "PRIMARY":
            fee=price*p["primaryFeeBps"]//10000
            splits=[(e["organizer"], price-fee),("platform",fee)]
        else:
            fee=price*p["resaleFeeBps"]//10000; royalty=price*p["resaleOrganizerBps"]//10000
            splits=[(r["seller"],price-fee-royalty),(e["organizer"],royalty),("platform",fee)]
        for index,(payee,n) in enumerate(splits):
            if not n: continue
            aid=tid+"-"+str(index)
            r["allocations"].append(dict(id=aid,payee=payee,amount=n,paid=0,recovered=0))
            self.post("held:"+tid,"payable:"+aid,n,"allocate frozen policy")
        r["status"]="COMMITTED"; t["owner"]=r["buyer"]; t["state"]="ACTIVE"; t["lock"]=None
        t["rightsVersion"]+=1; t["admissionEpoch"]+=1
        return {"ticketId":r["ticket"],"owner":t["owner"],"rightsVersion":t["rightsVersion"],"admissionEpoch":t["admissionEpoch"]}

    def reverse(self, tid):
        r=self.trade(tid); r["reversalRequested"]=True
        if not r["captured"] or r["reversalPlanned"]: return
        if any(x["trade"]==tid and x["kind"]=="PAYOUT" and x["state"] not in ("DONE","ABORTED") for x in self.s["effects"].values()): return
        if r["allocations"]:
            for a in r["allocations"]:
                unpaid=a["amount"]-a["paid"]
                if unpaid: self.post("payable:"+a["id"],"refund:"+tid,unpaid,"cancel unpaid allocation")
                if a["paid"]: self.post("recoverable:"+a["id"],"refund:"+tid,a["paid"],"paid funds must be recovered")
        else:
            self.post("held:"+tid,"refund:"+tid,r["amount"],"captured but undelivered")
        r["refundDue"]=r["amount"]; r["reversalPlanned"]=True

    def _abort_trade(self,b):
        tid=b["tradeId"]; r=self.trade(tid)
        self.role("operator",r["buyer"],r["seller"])
        require(r["status"]=="PREPARED","TRADE_NOT_ABORTABLE")
        r["status"]="VOID"; t=self.ticket(r["ticket"])
        require(t["lock"]==tid,"LOCK_MISMATCH"); t["lock"]=None
        self.reverse(tid)
        return {"status":"VOID","refundDue":r["refundDue"]}

    def terminate_ticket(self,t):
        t["state"]="CANCEL_PENDING_CLOSE" if t["session"] else "VOID"
        t["rightsVersion"]+=1
        if not t["session"]: t["admissionEpoch"]+=1
        t["lock"]=None
        for tid in t["trades"]:
            r=self.trade(tid)
            if r["status"]=="PREPARED": r["status"]="VOID"
            self.reverse(tid)

    def _refund_ticket(self,b):
        t=self.ticket(b["ticketId"]); self.role(t["owner"])
        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_REFUNDABLE")
        require(b["expectedVersion"]==t["rightsVersion"],"STALE_RIGHTS_VERSION")
        self.terminate_ticket(t)
        return {"rightsState":t["state"],"refundComplete":False}

    def _cancel_event(self,b):
        e=self.event(b["eventId"]); self.role("operator",e["organizer"])
        e["status"]="CANCELLED"
        for t in self.s["tickets"].values():
            if t["event"]==b["eventId"] and t["state"] not in ("VOID","CANCEL_PENDING_CLOSE"):
                self.terminate_ticket(t)
        return {"eventStatus":"CANCELLED"}

    def _complete_event(self,b):
        e=self.event(b["eventId"]); self.role("operator",e["organizer"])
        require(e["status"]=="OPEN","EVENT_NOT_OPEN"); e["status"]="COMPLETED"
        # Void unfinished checkout so late payments cannot strand a held balance.
        for tid,r in self.s["trades"].items():
            if r["event"]==b["eventId"] and r["status"]=="PREPARED":
                r["status"]="VOID"; self.ticket(r["ticket"])["lock"]=None; self.reverse(tid)
        return {"eventStatus":"COMPLETED"}

    def _admit(self,b):
        self.role("venue"); t=self.ticket(b["ticketId"])
        require(self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")
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

    def _prepare_effect(self,b):
        self.role("operator"); eid=ident(b["effectId"]); require(eid not in self.s["effects"],"EFFECT_EXISTS")
        tid=b["tradeId"]; r=self.trade(tid); kind=b["kind"]; n=positive(b["amount"])
        require(kind in ("REFUND","PAYOUT"),"UNSUPPORTED_EFFECT")
        allocation=b.get("allocationId")
        if kind=="PAYOUT":
            require(self.event(r["event"])["status"]=="COMPLETED" and not r["reversalRequested"] and r["status"]=="COMMITTED","PAYOUT_NOT_RELEASED")
            a=next((x for x in r["allocations"] if x["id"]==allocation),None)
            require(a is not None,"ALLOCATION_NOT_FOUND")
            owed="payable:"+allocation; beneficiary=a["payee"]
        else:
            require(r["reversalPlanned"],"REFUND_PLAN_NOT_READY")
            owed="refund:"+tid; beneficiary=r["buyer"]
        pending=list(self.s["effects"].values())
        reserved_owed=sum(x["amount"] for x in pending if x["owed"]==owed and x["state"] not in ("DONE","ABORTED"))
        require(n<=-self.balance(owed)-reserved_owed,"OBLIGATION_ALREADY_RESERVED")
        reserved_cash=sum(x["amount"] for x in pending if x["pool"]==r["pool"] and not x["fundsObserved"] and x["state"]!="ABORTED")
        require(n<=self.balance("funds:"+r["pool"])-reserved_cash,"INSUFFICIENT_CONFIRMED_FUNDS")
        effect=dict(trade=tid,kind=kind,amount=n,currency="KRW",beneficiary=beneficiary,
            allocation=allocation,owed=owed,pool=r["pool"],paymentId=r["paymentId"],
            state="PREPARED",sent=False,confirmed=False,fundsObserved=False,conflict=False)
        # The stored body is immutable. Retrying uses the same body and key.
        effect["request"]=dict(effectId=eid,tradeId=tid,kind=kind,amount=n,currency="KRW",
                                beneficiary=beneficiary,paymentId=r["paymentId"],scope=self.SCOPE)
        effect["idempotencyKey"]=digest([self.DOMAIN,eid,effect["request"]])
        self.s["effects"][eid]=effect
        return {"effectId":eid,"idempotencyKey":effect["idempotencyKey"]}

    def _send_effect(self,b):
        self.role("operator"); x=self.s["effects"][b["effectId"]]
        require(x["state"] not in ("DONE","ABORTED"),"EFFECT_ALREADY_TERMINAL")
        x["sent"]=True; x["state"]="OUTCOME_UNKNOWN"
        return {"unsentFixtureRequest":x["request"],"idempotencyKey":x["idempotencyKey"]}

    def _abort_effect(self,b):
        self.role("operator"); x=self.s["effects"][b["effectId"]]
        require(not x["sent"] and not x["fundsObserved"] and not x["confirmed"],"SENT_EFFECT_CANNOT_RELEASE_BY_TIMEOUT")
        x["state"]="ABORTED"
        r=self.trade(x["trade"])
        if r["reversalRequested"]: self.reverse(x["trade"])
        return {"state":"ABORTED"}

    def finish_effect(self,eid):
        x=self.s["effects"][eid]
        if x["state"]=="DONE" or not (x["confirmed"] and x["fundsObserved"]): return
        self.post(x["owed"],"in_transit:"+eid,x["amount"],"confirmed result and actual funds matched")
        x["state"]="DONE"; r=self.trade(x["trade"])
        if x["kind"]=="REFUND": r["refunded"]+=x["amount"]
        else:
            a=next(a for a in r["allocations"] if a["id"]==x["allocation"]); a["paid"]+=x["amount"]
        if r["reversalRequested"]: self.reverse(x["trade"])

    def _observe_effect(self,b):
        self.source(b); eid=b["effectId"]; require(eid in self.s["effects"],"UNKNOWN_EFFECT")
        positive(b["amount"])
        x=self.s["effects"][eid]; require(x["sent"],"EFFECT_NOT_SENT")
        require(b["amount"]==x["amount"] and b["currency"]==x["currency"] and b["beneficiary"]==x["beneficiary"] and b["paymentId"]==x["paymentId"],"EFFECT_BINDING_MISMATCH")
        phase=b["phase"]; require(phase in ("STATUS","FUNDS"),"UNKNOWN_EVIDENCE_PHASE")
        status=b.get("status")
        require(phase!="STATUS" or status in ("SUCCESS","PENDING","FAILED"),"UNKNOWN_PROVIDER_STATUS")
        binding=dict(effect=eid,amount=x["amount"],beneficiary=x["beneficiary"],payment=x["paymentId"],phase=phase,status=status)
        if not self.evidence("funds" if phase=="FUNDS" else "effect-status",b["sourceId"],binding): return {"duplicate":True}
        if phase=="FUNDS":
            require(not x["fundsObserved"],"SECOND_FUNDS_MOVEMENT_REQUIRES_REVIEW")
            require(self.balance("funds:"+x["pool"])>=x["amount"],"FUNDS_BALANCE_CONFLICT")
            self.post("in_transit:"+eid,"funds:"+x["pool"],x["amount"],"actual debit observed, status may still be unknown")
            x["fundsObserved"]=True
        elif status=="SUCCESS":
            x["confirmed"]=True
        elif status=="FAILED":
            # No timeout/failure notification by itself proves all sends fenced.
            x["conflict"]=True
        self.finish_effect(eid)
        return {"state":x["state"],"confirmed":x["confirmed"],"fundsObserved":x["fundsObserved"],"review":x["conflict"]}

    def _observe_recovery(self,b):
        self.source(b); r=self.trade(b["tradeId"]); n=positive(b["amount"])
        a=next((a for a in r["allocations"] if a["id"]==b["allocationId"]),None)
        require(a is not None and b["payer"]==a["payee"] and b["currency"]=="KRW","RECOVERY_BINDING_MISMATCH")
        if not self.evidence("funds",b["sourceId"],dict(kind="RECOVERY",trade=b["tradeId"],allocation=a["id"],amount=n)): return {"duplicate":True}
        require(n<=self.balance("recoverable:"+a["id"]),"EXCESS_RECOVERY")
        self.post("funds:"+r["pool"],"recoverable:"+a["id"],n,"actual beneficiary recovery observed")
        a["recovered"]+=n
        return {"recovered":a["recovered"]}

    def _set_consent(self,b):
        self.event(b["eventId"])
        require(b["purpose"]=="next_event_marketing" and type(b["allowed"]) is bool,"INVALID_CONSENT")
        key=canonical([self.actor,b["eventId"],b["purpose"]])
        prior=self.s["consents"].get(key,{"version":0})
        self.s["consents"][key]=dict(subject=self.actor,event=b["eventId"],purpose=b["purpose"],
            allowed=b["allowed"],version=prior["version"]+1,operationId=self.op)
        return {"consentVersion":prior["version"]+1,"allowed":b["allowed"]}

    def view(self,actor,event_id,kind):
        """Fixture authorization only. No public state dump endpoint is provided."""
        s=self.snapshot(); require(event_id in s["events"],"EVENT_NOT_FOUND")
        e=s["events"][event_id]
        trades={k:r for k,r in s["trades"].items() if r["event"]==event_id}
        if kind=="mine":
            return dict(tickets={k:{f:t[f] for f in ("state","rightsVersion","admissionEpoch","used")} for k,t in s["tickets"].items() if t["event"]==event_id and t["owner"]==actor},
                trades={k:{f:r[f] for f in ("kind","amount","currency","status","refundDue","refunded")} for k,r in trades.items() if actor in (r["buyer"],r["seller"])})
        if kind=="finance":
            require(actor in ("finance-adapter",e["organizer"]),"UNAUTHORIZED_VIEW")
            allocations=[a for r in trades.values() for a in r["allocations"] if a["payee"]==e["organizer"]]
            return dict(primaryCaptured=sum(r["amount"] for r in trades.values() if r["captured"] and r["kind"]=="PRIMARY"),
                resaleCaptured=sum(r["amount"] for r in trades.values() if r["captured"] and r["kind"]=="RESALE"),
                organizerGrossAllocated=sum(a["amount"] for a in allocations),
                organizerPaid=sum(a["paid"] for a in allocations),
                organizerPayable=sum(-s["balances"].get("payable:"+a["id"],0) for a in allocations),
                organizerRecoveryOutstanding=sum(s["balances"].get("recoverable:"+a["id"],0) for a in allocations),
                refundOutstanding=sum(r["refundDue"]-r["refunded"] for r in trades.values()),
                refundPlansPending=sum(r["reversalRequested"] and r["captured"] and not r["reversalPlanned"] for r in trades.values()),
                evidenceClass="synthetic",currency="KRW",sequence=len(s["events_log"]))
        if kind=="marketing":
            require(actor=="marketing-adapter","UNAUTHORIZED_VIEW")
            # Opt-in is never inferred from purchase, ownership, resale, or admission.
            return [dict(subject=c["subject"],consentVersion=c["version"],purpose=c["purpose"],
                    attended=any(t["event"]==event_id and t["owner"]==c["subject"] and t["used"] for t in s["tickets"].values()))
                    for c in s["consents"].values() if c["event"]==event_id and c["allowed"]]
        raise Rejected("UNKNOWN_VIEW")

    @staticmethod
    def check(s):
        balances=s["balances"]
        require(sum(balances.values())==0,"UNBALANCED_LEDGER")
        rebuilt={}
        for entry in s["journal"]:
            positive(entry["amount"])
            for account,delta in ((entry["debit"],entry["amount"]),(entry["credit"],-entry["amount"])):
                rebuilt[account]=rebuilt.get(account,0)+delta
        require({k:v for k,v in balances.items() if v}=={k:v for k,v in rebuilt.items() if v},"JOURNAL_MISMATCH")
        for account,n in balances.items():
            require(type(n) is int,"NONINTEGER_BALANCE")
            require(n>=0 if account.startswith(("funds:","pg:","recoverable:","in_transit:")) else n<=0,"ACCOUNT_SIGN_VIOLATION")
        for tid,r in s["trades"].items():
            require(0<=r["refunded"]<=r["refundDue"]<=r["amount"],"REFUND_OVERPAY")
            if r["allocations"]:
                require(sum(a["amount"] for a in r["allocations"])==r["amount"],"ALLOCATION_MISMATCH")
            for a in r["allocations"]:
                require(0<=a["recovered"]<=a["paid"]<=a["amount"],"ALLOCATION_OVERPAY")
        for t in s["tickets"].values():
            if t["lock"]:
                r=s["trades"][t["lock"]]
                require(r["status"]=="PREPARED" and r["expectedVersion"]==t["rightsVersion"],"BROKEN_TICKET_LOCK")
        for pool in {x["pool"] for x in s["effects"].values()}:
            reserved=sum(x["amount"] for x in s["effects"].values() if x["pool"]==pool and not x["fundsObserved"] and x["state"]!="ABORTED")
            require(reserved<=balances.get("funds:"+pool,0),"OVERRESERVED_CASH")


ACTIONS = {"create_event","prepare_trade","accept_trade","capture","settle_capture","commit_trade",
           "abort_trade","refund_ticket","cancel_event","complete_event","admit","delegate","close_delegation",
           "prepare_effect","send_effect","abort_effect","observe_effect","observe_recovery","set_consent"}
