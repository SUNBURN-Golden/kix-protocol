"""Independent command driver for a bounded review of the supplied KIX v0.2.

Uses the original Core, not an independent protocol implementation. Does not
import its Harness or change its sources. Counterexamples are synthetic and
describe current behavior, not acceptable production behavior or real PG facts.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile


POLICY = {
    "primaryPrice": 100000, "resaleCap": 150000, "primaryFeeBps": 500,
    "resaleFeeBps": 300, "resaleOrganizerBps": 200, "resaleAllowed": True,
    "refundProfile": "FULL_CHAIN_UNWIND_FIXTURE",
}


class Driver:
    def __init__(self, core_type, path=":memory:"):
        self.core_type = core_type
        self.c = core_type(path)
        self.n = 0

    def cmd(self, action, actor="operator", op=None, fault=None, **body):
        self.n += 1
        return self.c.execute(op or f"review-{self.n}", actor, action,
                              dict(domain=self.c.DOMAIN, **body), **(fault or {}))["result"]

    def source(self, action, **body):
        return self.cmd(action, "pg-adapter", scope=self.c.SCOPE,
                        provenance="synthetic", **body)

    def raw(self, action, **body):
        return json.dumps({"action": action, "body": dict(domain=self.c.DOMAIN,
            scope=self.c.SCOPE, provenance="synthetic", **body)},
            sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()

    def event(self, seats=None, **changes):
        self.cmd("create_event", eventId="show", organizer="organizer",
                 policy=dict(POLICY), seats=seats or ["A1"], **changes)

    def prepare(self, tid="primary", buyer="A", inventory="show/A1", amount=100000):
        u = self.c.snapshot()["inventory"][inventory]
        return self.cmd("prepare_trade", buyer, tradeId=tid, buyer=buyer,
            inventoryId=inventory, expectedInventoryVersion=u["version"],
            expectedVersion=0, amount=amount, expiresAt=900)

    def capture_body(self, tid="primary", payment=None):
        r = self.c.snapshot()["trades"][tid]
        return dict(tradeId=tid, orderId=r["externalOrderId"],
                    paymentId=payment or "pay-"+tid, amount=r["amount"],
                    currency="KRW", buyer=r["buyer"])

    def capture(self, tid="primary"):
        return self.source("capture", **self.capture_body(tid))

    def settlement_body(self, tid="primary", movement=None):
        r = self.c.snapshot()["trades"][tid]
        return dict(tradeId=tid, paymentId="pay-"+tid, amount=r["amount"],
                    grossAmount=r["amount"], feeAmount=0, taxAmount=0,
                    heldAmount=0, adjustmentAmount=0, feeBearer="platform",
                    contractRef="fixture:settlement:v1", currency="KRW",
                    movementId=movement or "settle-"+tid)

    def purchase(self, tid="primary", buyer="A", settle=True, inventory="show/A1"):
        out = self.prepare(tid, buyer, inventory)
        self.capture(tid)
        if settle:
            self.source("settle_capture", **self.settlement_body(tid))
        self.cmd("commit_trade", tradeId=tid)
        return out["ticketId"]

    def effect(self, eid, kind="REFUND", amount=100000, route=None,
               trade="primary", allocation=None, send=True, **extra):
        route = route or ("BANK_PAYOUT_FIXTURE" if kind=="PAYOUT" else "CASH_REFUND_FIXTURE")
        contracts = {"BANK_PAYOUT_FIXTURE": "fixture:payout:v1",
                     "CASH_REFUND_FIXTURE": "fixture:cash-refund:v1",
                     "PG_ORIGINAL_CANCEL_FIXTURE": "fixture:pg-cancel:v1"}
        r = self.c.snapshot()["trades"][trade]
        body = dict(effectId=eid, tradeId=trade, kind=kind, amount=amount,
                    routeProfile=route, contractRef=contracts[route], **extra)
        if kind=="PAYOUT":
            body["allocationId"] = allocation
            payee = next(a["payee"] for a in r["allocations"] if a["id"]==allocation)
        else:
            payee = r["buyer"]
        if route != "PG_ORIGINAL_CANCEL_FIXTURE":
            body["beneficiaryAccountRef"] = "fixture-account:"+payee
        result = self.cmd("prepare_effect", **body)
        if send:
            result = self.cmd("send_effect", effectId=eid)
        return result

    def observation_body(self, eid, phase, amount=None, source=None, **extra):
        x = self.c.snapshot()["effects"][eid]
        body = dict(effectId=eid, phase=phase, sourceId=source or eid+"-"+phase,
                    providerOperationId="provider-"+eid, amount=amount or x["amount"],
                    currency="KRW", beneficiary=x["beneficiary"], paymentId=x["paymentId"], **extra)
        if phase=="FUNDS" and "movementId" not in body:
            body["movementId"] = "move-"+eid
        return body

    def observe(self, eid, phase, **extra):
        return self.source("observe_effect", **self.observation_body(eid, phase, **extra))

    def finance(self):
        return self.c.view("finance-adapter", "show", "finance")

    def close(self):
        self.c.db.close()


def error_of(fn):
    try:
        return {"accepted": True, "result": fn()}
    except Exception as exc:
        return {"accepted": False, "error": str(exc), "exception": type(exc).__name__}


def run(core_type):
    rows = []
    def add(id, classification, title, observed):
        rows.append(dict(id=id, classification=classification, title=title, observed=observed))

    # An out-of-order statement first enters REVIEW, then is successfully applied.
    d=Driver(core_type)
    try:
        d.event(); d.prepare()
        packet=d.raw("settle_capture", **d.settlement_body())
        first=d.c.ingest("early-settlement", packet, fixture_authenticated=True)
        d.capture()
        second=d.c.apply_observation("early-settlement", fixture_authenticated=True)
        f=d.finance(); r=d.c.snapshot()["trades"]["primary"]
        assert first["state"]=="REVIEW" and second["state"]=="APPLIED"
        assert r["settled"]==100000
        assert f["sourceReview"]["observedMovementAmountUnderReview"]==100000
        assert f["sourceReview"]["inboxPendingOrReview"]==0
        add("R01", "DEFECT", "Resolved observation remains in unposted-review amount",
            {"first":first, "second_state":second["state"], "settled":r["settled"],
             "sourceReview":f["sourceReview"]})
    finally: d.close()

    # Positive customer-credit evidence conflicts with a later no-execution fence.
    d=Driver(core_type)
    try:
        d.event(); d.purchase(); d.cmd("cancel_event", eventId="show")
        d.effect("pg", route="PG_ORIGINAL_CANCEL_FIXTURE")
        credit=d.c.ingest("credit", d.raw("observe_effect", **d.observation_body("pg", "CUSTOMER_CREDIT_CONFIRMED")), fixture_authenticated=True)
        fence=d.c.ingest("fence", d.raw("observe_effect", **d.observation_body("pg", "FENCED_FAILURE",
            fenceRef="contradictory-final-record", fenceProvenance="synthetic_final_provider_fence")), fixture_authenticated=True)
        cash=d.effect("cash")
        d.observe("cash", "STATUS", status="SUCCESS")
        d.observe("cash", "FUNDS")
        f=d.finance(); s=d.c.snapshot()
        assert credit["state"]==fence["state"]=="APPLIED"
        assert s["effects"]["pg"]["state"]=="FAILED_FENCED"
        assert s["effects"]["cash"]["appliedAmount"]==100000
        assert f["customerCreditConfirmed"]==100000 and f["refundFulfilled"]==100000
        core_type.check(s)
        add("R02", "DEFECT_ON_CONFLICTING_SOURCE_INPUTS", "Customer credit does not block contradictory failure fence and second route",
            {"credit_ingest":credit["state"], "fence_ingest":fence["state"], "new_cash_dispatch":cash["dispatchDecision"],
             "pg_state":s["effects"]["pg"]["state"], "pg_customer_credit":100000,
             "separate_cash_fulfilled":100000, "original_duty":f["refundObligation"],
             "local_invariants_accept":True, "real_pg_behavior_asserted":False})
    finally: d.close()

    # Partial execution cannot be terminally closed, even with a remainder fence.
    d=Driver(core_type)
    try:
        d.event(); d.purchase(); d.cmd("complete_event", eventId="show")
        d.effect("p", kind="PAYOUT", amount=95000, allocation="primary-0")
        d.observe("p", "STATUS", amount=40000, status="SUCCESS")
        d.observe("p", "FUNDS", amount=40000)
        d.cmd("cancel_event", eventId="show")
        fence=error_of(lambda:d.observe("p", "FENCED_FAILURE", fenceRef="remainder-closed",
            fenceProvenance="synthetic_final_provider_fence"))
        d.observe("p", "STATUS", status="FAILED", source="partial-terminal-failure")
        f=d.finance(); s=d.c.snapshot()
        assert not fence["accepted"] and fence["error"]=="FINAL_FAILURE_FENCE_REQUIRED"
        assert s["effects"]["p"]["state"]=="OUTCOME_UNKNOWN"
        assert f["payoutOutcomeUnknown"]==55000 and f["refundUnclassified"]==100000
        add("R03", "MISSING_TERMINAL_STATE", "Partially successful payout has no final-partial closure",
            {"attempted_fence":fence, "paid":40000, "remaining_reserved":55000,
             "refundUnclassified":f["refundUnclassified"], "effect_state":s["effects"]["p"]["state"]})
        returned=error_of(lambda:d.source("observe_return", effectId="p", paymentId="pay-primary", payer="organizer",
            amount=40000, currency="KRW", movementId="partial-payout-return"))
        assert not returned["accepted"] and returned["error"]=="RETURN_REQUIRES_COMPLETED_CASH_EFFECT"
        add("R04", "MISSING_EVENT_CASE", "Return of an already applied partial payout cannot be posted", returned)
    finally: d.close()

    # The first-send response is lost before any real sender can receive it.
    with tempfile.TemporaryDirectory(prefix="kix-v02-send-loss-") as temp:
        path=str(Path(temp)/"core.db")
        d=Driver(core_type, path)
        d.event(); d.purchase(); d.cmd("complete_event", eventId="show")
        d.effect("p", kind="PAYOUT", amount=95000, allocation="primary-0", send=False)
        loss=error_of(lambda:d.cmd("send_effect", op="first-send", fault={"lose_response":True}, effectId="p"))
        d.close(); c=core_type(path)
        try:
            b={"domain":c.DOMAIN,"effectId":"p"}
            same=c.execute("first-send", "operator", "send_effect", b)["result"]
            fresh=c.execute("new-send", "operator", "send_effect", b)["result"]
            x=c.snapshot()["effects"]["p"]
            assert loss["exception"]=="ConnectionError"
            assert same["dispatchDecision"]==fresh["dispatchDecision"]=="QUERY_ONLY"
            assert x["providerOperationId"] is None
            add("R05", "RECOVERY_LIVENESS_CONTRACT_GAP", "Lost first-send handoff leaves query-only work without provider operation ID",
                {"loss":loss, "same_operation":same, "new_operation":fresh,
                 "providerOperationId":x["providerOperationId"], "local_request_retained":bool(x["request"]),
                 "external_sends_in_probe":0})
        finally:c.db.close()

    # A globally scoped digest is unchanged by a newly preserved raw collision.
    d=Driver(core_type)
    try:
        d.event(); d.purchase()
        base=d.capture_body(payment="second-payment")
        d.c.ingest("same-raw-id", d.raw("capture", **base), fixture_authenticated=True)
        before=d.finance()["sourceReview"]
        conflict=error_of(lambda:d.c.ingest("same-raw-id", d.raw("capture", **dict(base, amount=99999)), fixture_authenticated=True))
        after=d.finance()["sourceReview"]
        n=d.c.db.execute("SELECT count(*) FROM raw_conflicts").fetchone()[0]
        assert not conflict["accepted"] and n==1
        assert before==after
        add("R06", "EVIDENCE_SUMMARY_GAP", "Raw collision is preserved but absent from finance digest and conflict count",
            {"conflict":conflict, "raw_conflict_count":n, "finance_summary_unchanged":True,
             "reported_conflictingReviewFacts":after["conflictingReviewFacts"]})
    finally:d.close()

    # Every move is cumulative by status and incremental by cash facts, but full
    # applied fragments can also be returned before the total amount finishes.
    # Check every ordering of two positive facts against both credit/fence orders.
    credit_orders=[]
    for order in itertools.permutations(("CUSTOMER_CREDIT_CONFIRMED", "FENCED_FAILURE")):
        d=Driver(core_type)
        try:
            d.event(); d.purchase(); d.cmd("cancel_event", eventId="show")
            d.effect("pg", route="PG_ORIGINAL_CANCEL_FIXTURE")
            answers=[]
            for phase in order:
                extra = dict(fenceRef="same-final", fenceProvenance="synthetic_final_provider_fence") if phase=="FENCED_FAILURE" else {}
                answers.append(d.c.ingest("raw-"+phase, d.raw("observe_effect", **d.observation_body("pg",phase,**extra)),fixture_authenticated=True)["state"])
            credit_orders.append({"order":order,"states":answers,"effect":d.c.snapshot()["effects"]["pg"]["state"]})
        finally:d.close()
    add("R07", "ORDERING_CROSSCHECK", "Credit/fence order asymmetry", credit_orders)

    # The listing contract does not cap buyer-requested checkout duration below
    # the listing expiration. This is a policy gap, not an extra unauthorized sale.
    d=Driver(core_type)
    try:
        d.event(); rid=d.purchase()
        listing=d.cmd("create_listing", "A", listingId="L", ticketId=rid,
            expectedVersion=1, amount=120000, expiresAt=86400)
        d.cmd("reserve_listing", "B", listingId="L", listingHash=listing["termsHash"],
            tradeId="hold", expiresAt=86400)
        t=d.c.snapshot()["trades"]["hold"]
        assert t["expiresAt"]==86400 and t["status"]=="PREPARED"
        owner_abort=error_of(lambda:d.cmd("abort_trade", "A", tradeId="hold"))
        assert owner_abort["accepted"]
        add("R08", "PRODUCT_POLICY_GAP", "Buyer can reserve a listing for 24h without payment",
            {"hold_seconds":86400,"captured":t["captured"],"owner_can_abort":owner_abort["accepted"]})
    finally:d.close()

    # Disjoint event+seat pairs alias with slash concatenation before issuance.
    d=Driver(core_type)
    try:
        d.cmd("create_event",eventId="a",organizer="organizer",policy=dict(POLICY),seats=["b/c"])
        d.cmd("create_event",eventId="a/b",organizer="organizer",policy=dict(POLICY),seats=["c"])
        s=d.c.snapshot()
        assert len(s["events"])==2 and len(s["inventory"])==1
        assert s["inventory"]["a/b/c"]["event"]=="a/b"
        add("R09", "IDENTIFIER_COLLISION", "Valid event/seat tuples can overwrite unissued inventory",
            {"event_count":2,"inventory_count":1,"colliding_id":"a/b/c","surviving_event":"a/b"})
    finally:d.close()

    return rows


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); sys.path.insert(0,str(a.bundle.resolve()))
    from core import Core
    a.output.mkdir(parents=True,exist_ok=True)
    results=run(Core)
    report={"scope":"bounded synthetic review using original Core and a separate command driver",
            "independent_protocol_implementation":False, "real_external_calls":0,
            "source_hashes":{f:hashlib.sha256((a.bundle/f).read_bytes()).hexdigest() for f in
                ("core.py","finance.py","lifecycle.py","observations.py","contracts.py")},
            "results":results}
    (a.output/"review_results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"observations":len(results),"results":results},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
