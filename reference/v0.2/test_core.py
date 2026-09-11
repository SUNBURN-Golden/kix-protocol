import copy
import itertools
import json
from pathlib import Path
import tempfile
import threading
import unittest

from core import Core, Rejected, digest
from adapters import check_legacy_toss, refund_intent, unsent_refund_request


POLICY=dict(primaryPrice=100000,resaleCap=150000,primaryFeeBps=500,
            resaleFeeBps=300,resaleOrganizerBps=200,resaleAllowed=True,
            refundProfile="FULL_CHAIN_UNWIND_FIXTURE")


class Harness:
    def __init__(self,core=None):
        self.c=core or Core(); self.seq=0

    def run(self,action,actor="operator",op=None,**body):
        self.seq+=1
        # Fixture defaults are only a test-driver convenience; the API requires them.
        state=self.c.snapshot()
        if "ticketId" in body and body["ticketId"] in state["inventory"]:
            body["ticketId"]=state["inventory"][body["ticketId"]]["currentRight"]
        if action=="prepare_effect":
            from finance import ROUTES
            route=body.setdefault("routeProfile","BANK_PAYOUT_FIXTURE" if body["kind"]=="PAYOUT" else "CASH_REFUND_FIXTURE")
            body.setdefault("contractRef",ROUTES[route]["contract"])
            if ROUTES[route]["cash"]:
                r=state["trades"][body["tradeId"]]
                payee=next(a["payee"] for a in r["allocations"] if a["id"]==body["allocationId"]) if body["kind"]=="PAYOUT" else r["buyer"]
                body.setdefault("beneficiaryAccountRef","fixture-account:"+payee)
        if action=="set_consent":
            body.setdefault("business","KIX"); body.setdefault("channel","email")
            key=self.c.consent_key(actor,body)
            body.setdefault("expectedConsentVersion",state["consents"].get(key,{"version":0})["version"])
        if action=="capture" and body.get("orderId")==body.get("tradeId"):
            body["orderId"]=state["trades"][body["tradeId"]]["externalOrderId"]
        if action=="observe_recovery": body.setdefault("movementId",body.get("sourceId"))
        if action=="settle_capture":
            body.setdefault("grossAmount",body["amount"])
            for f in ("feeAmount","taxAmount","heldAmount","adjustmentAmount"): body.setdefault(f,0)
            body.setdefault("feeBearer","platform"); body.setdefault("contractRef","fixture:settlement:v1")
            body.setdefault("movementId",body.get("sourceId"))
        return self.c.execute(op or "op-"+str(self.seq),actor,action,dict(domain=Core.DOMAIN,**body))

    def source(self,action,**body):
        body.setdefault("scope",Core.SCOPE); body.setdefault("provenance","synthetic")
        return self.run(action,"pg-adapter",**body)

    def right(self,inventory="show/A1"):
        return self.c.snapshot()["inventory"][inventory]["currentRight"]

    def event(self,eid="show",seats=None,**changes):
        body=dict(eventId=eid,organizer="organizer",policy=POLICY,seats=seats or ["A1"]); body.update(changes)
        self.run("create_event",**body)

    def prepare(self,trade="primary",ticket="show/A1",buyer="A",amount=100000):
        state=self.c.snapshot(); unit=state["inventory"].get(ticket)
        if unit and unit["currentRight"] is None:
            self.run("prepare_trade",buyer,tradeId=trade,inventoryId=ticket,buyer=buyer,amount=amount,
                     expectedInventoryVersion=unit["version"],expectedVersion=0)
        else:
            rid=unit["currentRight"] if unit else ticket
            t=state["tickets"][rid]
            self.run("prepare_trade",t["owner"] or buyer,tradeId=trade,ticketId=rid,buyer=buyer,
                     amount=amount,expectedVersion=t["rightsVersion"])
        r=self.c.snapshot()["trades"][trade]
        if not r["accepted"]:
            terms=r["termsHash"]
            self.run("accept_trade",buyer,tradeId=trade,termsHash=terms)

    def capture(self,trade="primary",settle=True):
        r=self.c.snapshot()["trades"][trade]
        self.source("capture",tradeId=trade,orderId=trade,paymentId="pay-"+trade,
                    amount=r["amount"],currency="KRW",buyer=r["buyer"])
        if settle:
            self.source("settle_capture",tradeId=trade,paymentId="pay-"+trade,sourceId="deposit-"+trade,amount=r["amount"],currency="KRW")

    def purchase(self,trade="primary",ticket="show/A1",buyer="A",amount=100000,settle=True):
        self.prepare(trade,ticket,buyer,amount); self.capture(trade,settle)
        self.run("commit_trade",tradeId=trade)

    def chain(self):
        self.event(); self.purchase(); self.purchase("resale",buyer="B",amount=120000)

    def effect(self,eid,trade,kind,amount,allocation=None,**changes):
        self.run("prepare_effect",effectId=eid,tradeId=trade,kind=kind,amount=amount,allocationId=allocation,**changes)
        self.run("send_effect",effectId=eid)

    def observe(self,eid,phase,status=None,source_id=None,**changes):
        x=self.c.snapshot()["effects"][eid]
        b=dict(effectId=eid,phase=phase,sourceId=source_id or eid+"-"+phase+"-"+str(status),
               amount=x["amount"],currency=x["currency"],beneficiary=x["beneficiary"],paymentId=x["paymentId"],providerOperationId="provider-"+eid)
        if phase=="FUNDS": b["movementId"]=source_id or "movement-"+eid
        if status: b["status"]=status
        b.update(changes)
        return self.source("observe_effect",**b)

    def finish(self,eid):
        self.observe(eid,"STATUS","SUCCESS"); self.observe(eid,"FUNDS")

    def refund_all(self):
        for tid,r in self.c.snapshot()["trades"].items():
            if r["refundDue"]>r["refunded"]:
                eid="refund-"+tid
                self.effect(eid,tid,"REFUND",r["refundDue"]-r["refunded"]); self.finish(eid)

    def payout_all(self):
        for tid,r in self.c.snapshot()["trades"].items():
            for a in r["allocations"]:
                eid="payout-"+a["id"]
                self.effect(eid,tid,"PAYOUT",a["amount"],a["id"]); self.finish(eid)


class LifecycleTests(unittest.TestCase):
    def setUp(self): self.h=Harness()
    def tearDown(self): self.h.c.db.close()

    def test_purchase_resale_admission_and_exact_payouts(self):
        h=self.h; h.chain(); t=h.c.snapshot()["tickets"][h.right()]
        self.assertEqual(t["owner"],"B")
        h.run("admit","venue",ticketId="show/A1",holder="B",expectedVersion=2,admissionEpoch=2)
        h.run("complete_event",eventId="show"); h.payout_all()
        s=h.c.snapshot(); paid={}
        for r in s["trades"].values():
            for a in r["allocations"]: paid[a["payee"]]=paid.get(a["payee"],0)+a["paid"]
        self.assertEqual(paid,{"organizer":97400,"platform":8600,"A":114000})
        self.assertTrue(all(v==0 for v in s["balances"].values()))

    def test_full_chain_refund_before_payout(self):
        h=self.h; h.chain(); h.run("refund_ticket","B",ticketId="show/A1",expectedVersion=2)
        self.assertEqual(h.c.snapshot()["tickets"][h.right()]["state"],"VOID")
        h.refund_all(); s=h.c.snapshot()
        self.assertEqual([s["trades"][x]["refunded"] for x in ("primary","resale")],[100000,120000])
        self.assertTrue(all(v==0 for v in s["balances"].values()))

    def test_cancel_after_payout_keeps_recoverables_then_recovers(self):
        h=self.h; h.chain(); h.run("complete_event",eventId="show"); h.payout_all()
        h.run("cancel_event",eventId="show"); s=h.c.snapshot()
        self.assertEqual(sum(v for k,v in s["balances"].items() if k.startswith("recoverable:")),220000)
        self.assertEqual(sum(v for k,v in s["balances"].items() if k.startswith("refund:")),-220000)
        with self.assertRaisesRegex(Rejected,"INSUFFICIENT_CONFIRMED_FUNDS"):
            h.effect("unfunded","resale","REFUND",120000)
        for tid,r in s["trades"].items():
            for a in r["allocations"]:
                h.source("observe_recovery",tradeId=tid,allocationId=a["id"],payer=a["payee"],amount=a["paid"],currency="KRW",sourceId="recover-"+a["id"])
        h.refund_all()
        self.assertTrue(all(v==0 for v in h.c.snapshot()["balances"].values()))

    def test_late_payment_after_abort_never_mints_ticket(self):
        h=self.h; h.event(); h.prepare(); h.run("abort_trade",tradeId="primary"); h.capture()
        s=h.c.snapshot(); self.assertIsNone(s["tickets"][h.right()]["owner"])
        self.assertEqual(s["trades"]["primary"]["refundDue"],100000)
        h.refund_all()

    def test_event_completion_aborts_unfinished_checkout(self):
        h=self.h; h.event(); h.prepare(); h.run("complete_event",eventId="show"); h.capture()
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refundDue"],100000)
        with self.assertRaisesRegex(Rejected,"TRADE_NOT_COMMITTABLE"): h.run("commit_trade",tradeId="primary")

    def test_capture_is_not_available_cash(self):
        h=self.h; h.event(); h.purchase(settle=False); h.run("cancel_event",eventId="show")
        with self.assertRaisesRegex(Rejected,"INSUFFICIENT_CONFIRMED_FUNDS"): h.effect("r","primary","REFUND",100000)

    def test_original_qr_invalid_after_resale(self):
        h=self.h; h.chain()
        with self.assertRaisesRegex(Rejected,"STALE_OR_WRONG_PRESENTATION"):
            h.run("admit","venue",ticketId="show/A1",holder="A",expectedVersion=1,admissionEpoch=1)

    def test_resale_lock_blocks_admission_and_second_resale(self):
        h=self.h; h.event(); h.purchase(); h.prepare("resale",buyer="B",amount=120000)
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_ADMISSIBLE"):
            h.run("admit","venue",ticketId="show/A1",holder="A",expectedVersion=1,admissionEpoch=1)
        with self.assertRaisesRegex(Rejected,"TICKET_LOCKED"): h.prepare("second",buyer="C",amount=120000)

    def test_admission_first_blocks_resale(self):
        h=self.h; h.event(); h.purchase()
        h.run("admit","venue",ticketId="show/A1",holder="A",expectedVersion=1,admissionEpoch=1)
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_TRANSFERABLE"): h.prepare("resale",buyer="B",amount=120000)

    def test_delegation_requires_bound_final_log(self):
        h=self.h; h.event(); h.purchase()
        d=h.run("delegate","A",ticketId="show/A1",expectedVersion=1)["result"]
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_TRANSFERABLE"): h.prepare("resale",buyer="B",amount=120000)
        with self.assertRaisesRegex(Rejected,"DELEGATION_SCOPE_MISMATCH"):
            h.run("close_delegation","venue",ticketId="show/A1",session=d["session"],admissionEpoch=d["admissionEpoch"]-1,used=False,provenance="synthetic_final_controller_log")
        h.run("close_delegation","venue",ticketId="show/A1",session=d["session"],admissionEpoch=d["admissionEpoch"],used=False,provenance="synthetic_final_controller_log")
        h.prepare("resale",buyer="B",amount=120000)

    def test_cancel_delegation_does_not_invent_unused_closure(self):
        h=self.h; h.event(); h.purchase()
        d=h.run("delegate","A",ticketId="show/A1",expectedVersion=1)["result"]
        h.run("cancel_event",eventId="show")
        self.assertEqual(h.c.snapshot()["tickets"][h.right()]["state"],"CANCEL_PENDING_CLOSE")
        h.run("close_delegation","venue",ticketId="show/A1",session=d["session"],admissionEpoch=d["admissionEpoch"],used=True,provenance="synthetic_final_controller_log")
        t=h.c.snapshot()["tickets"][h.right()]; self.assertEqual(t["state"],"VOID"); self.assertTrue(t["used"])

    def test_response_loss_and_conflicting_id_after_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/"state.db"); c=Core(path)
            b=dict(domain=Core.DOMAIN,eventId="show",organizer="organizer",policy=POLICY,seats=["A1"])
            with self.assertRaises(ConnectionError): c.execute("fixed","operator","create_event",b,lose_response=True)
            c.db.close(); c=Core(path)
            self.assertEqual(c.execute("fixed","operator","create_event",b)["sequence"],1)
            with self.assertRaisesRegex(Rejected,"OPERATION_ID_CONFLICT"):
                c.execute("fixed","operator","create_event",dict(b,seats=["A2"]))
            with self.assertRaisesRegex(Rejected,"OPERATION_ID_CONFLICT"):
                c.execute("fixed","intruder","create_event",b)
            c.db.close()

    def test_failure_rolls_back_state_journal_and_outbox(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); before=h.c.snapshot()
        b=dict(domain=Core.DOMAIN,effectId="r",tradeId="primary",kind="REFUND",amount=100000,routeProfile="CASH_REFUND_FIXTURE",contractRef="fixture:cash-refund:v1",beneficiaryAccountRef="fixture-account:A")
        with self.assertRaises(RuntimeError): h.c.execute("crash","operator","prepare_effect",b,fail_before_commit=True)
        self.assertEqual(before,h.c.snapshot())
        self.assertEqual(h.c.db.execute("SELECT count(*) FROM commands WHERE operation_id='crash'").fetchone()[0],0)

    def test_duplicate_capture_under_new_operation_id(self):
        h=self.h; h.event(); h.purchase(); before=h.c.snapshot()["balances"]
        h.source("capture",tradeId="primary",orderId="primary",paymentId="pay-primary",amount=100000,currency="KRW",buyer="A")
        self.assertEqual(before,h.c.snapshot()["balances"])

    def test_wrong_capture_and_payment_reuse_rejected(self):
        h=self.h; h.event(seats=["A1","A2"]); h.purchase(); h.prepare("other","show/A2",buyer="B")
        with self.assertRaisesRegex(Rejected,"SOURCE_EVIDENCE_CONFLICT"):
            h.source("capture",tradeId="other",orderId="other",paymentId="pay-primary",amount=100000,currency="KRW",buyer="B")
        with self.assertRaisesRegex(Rejected,"CAPTURE_BINDING_MISMATCH"):
            h.source("capture",tradeId="other",orderId="other",paymentId="new",amount=99999,currency="KRW",buyer="B")

    def test_effect_observation_orders_and_duplicate_facts(self):
        for order in itertools.permutations(("STATUS","FUNDS")):
            with self.subTest(order=order):
                h=Harness(); h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
                for phase in order:
                    h.observe("r",phase,"SUCCESS" if phase=="STATUS" else None)
                    h.observe("r",phase,"SUCCESS" if phase=="STATUS" else None)
                    if phase=="FUNDS":
                        self.assertEqual(sum(v for k,v in h.c.snapshot()["balances"].items() if k.startswith("funds:")),0)
                s=h.c.snapshot(); self.assertEqual(s["trades"]["primary"]["refunded"],100000)
                self.assertTrue(all(v==0 for v in s["balances"].values())); h.c.db.close()

    def test_funds_before_status_debits_cash_without_claiming_refund_done(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        h.observe("r","FUNDS"); s=h.c.snapshot()
        self.assertEqual(s["trades"]["primary"]["refunded"],0)
        self.assertEqual(s["balances"]["in_transit:r"],100000)
        self.assertEqual(s["balances"]["refund:primary"],-100000)

    def test_unknown_outcome_never_releases_reservation(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        first=h.run("send_effect",effectId="r")["result"]
        h.observe("r","STATUS","FAILED")
        self.assertEqual(first,h.run("send_effect",effectId="r")["result"])
        with self.assertRaisesRegex(Rejected,"SENT_EFFECT_CANNOT_RELEASE"): h.run("abort_effect",effectId="r")
        with self.assertRaisesRegex(Rejected,"OBLIGATION_ALREADY_RESERVED"): h.effect("r2","primary","REFUND",100000)
        h.finish("r"); self.assertTrue(h.c.snapshot()["effects"]["r"]["conflict"])

    def test_partial_refunds_are_separate_bounded_effects(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show")
        h.effect("r1","primary","REFUND",40000); h.finish("r1")
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refunded"],40000)
        with self.assertRaisesRegex(Rejected,"OBLIGATION_ALREADY_RESERVED"): h.effect("over","primary","REFUND",60001)
        h.effect("r2","primary","REFUND",60000); h.finish("r2")

    def test_same_funds_evidence_cannot_pay_two_obligations(self):
        h=self.h; h.chain(); h.run("cancel_event",eventId="show")
        h.effect("r1","primary","REFUND",100000); h.effect("r2","resale","REFUND",120000)
        h.observe("r1","FUNDS",source_id="same-bank-id")
        with self.assertRaisesRegex(Rejected,"SOURCE_EVIDENCE_CONFLICT"): h.observe("r2","FUNDS",source_id="same-bank-id")

    def test_late_failure_does_not_erase_completed_money(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000); h.finish("r")
        balances=h.c.snapshot()["balances"]; h.observe("r","STATUS","FAILED")
        self.assertEqual(balances,h.c.snapshot()["balances"]); self.assertEqual(h.c.snapshot()["effects"]["r"]["state"],"DONE")

    def test_inflight_payout_delays_reversal_then_creates_recovery(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        h.effect("p","primary","PAYOUT",95000,"primary-0")
        h.run("cancel_event",eventId="show")
        self.assertFalse(h.c.snapshot()["trades"]["primary"]["reversalPlanned"])
        h.finish("p"); s=h.c.snapshot()
        self.assertEqual(s["balances"]["recoverable:primary-0"],95000)
        self.assertEqual(s["trades"]["primary"]["refundDue"],100000)

    def test_unsent_payout_can_be_aborted_after_cancellation(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        h.run("prepare_effect",effectId="p",tradeId="primary",kind="PAYOUT",amount=95000,allocationId="primary-0")
        h.run("cancel_event",eventId="show"); h.run("abort_effect",effectId="p")
        self.assertTrue(h.c.snapshot()["trades"]["primary"]["reversalPlanned"])
        h.refund_all()

    def test_unrelated_event_funds_cannot_fund_refund(self):
        h=self.h; h.event("first"); h.event("second")
        h.purchase("t1","first/A1",settle=False); h.purchase("t2","second/A1")
        h.run("cancel_event",eventId="first")
        with self.assertRaisesRegex(Rejected,"INSUFFICIENT_CONFIRMED_FUNDS"): h.effect("r","t1","REFUND",100000)

    def test_policy_consent_domain_and_permissions(self):
        h=self.h; h.event(); h.purchase()
        with self.assertRaisesRegex(Rejected,"UNAUTHORIZED"): h.run("cancel_event","B",eventId="show")
        with self.assertRaisesRegex(Rejected,"RESALE_POLICY_REJECTED"): h.prepare("high",buyer="B",amount=150001)
        t=h.c.snapshot()["tickets"][h.right()]
        h.run("prepare_trade","A",tradeId="resale",ticketId="show/A1",buyer="B",amount=120000,expectedVersion=t["rightsVersion"])
        with self.assertRaisesRegex(Rejected,"BUYER_HAS_NOT_ACCEPTED"): h.capture("resale")
        with self.assertRaisesRegex(Rejected,"DOMAIN_MISMATCH"): h.c.execute("bad-domain","operator","cancel_event",dict(domain="wrong",eventId="show"))

    def test_source_scope_and_recipient_binding(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        with self.assertRaisesRegex(Rejected,"EFFECT_BINDING_MISMATCH"): h.observe("r","STATUS","SUCCESS",beneficiary="B")
        with self.assertRaisesRegex(Rejected,"SOURCE_SCOPE_MISMATCH"):
            h.observe("r","STATUS","SUCCESS",scope=dict(Core.SCOPE,environment="live"))

    def test_existing_toss_reconciliation_contract(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000,routeProfile="PG_ORIGINAL_CANCEL_FIXTURE")
        intent=refund_intent(h.c,"r"); request=unsent_refund_request(h.c,"r")
        self.assertFalse(request["sent"])
        self.assertEqual(request["headers"]["Idempotency-Key"],h.c.snapshot()["effects"]["r"]["idempotencyKey"])
        raw=dict(mId=Core.SCOPE["merchant"],paymentKey="pay-primary",currency="KRW",cancels=[dict(transactionKey="pg-cancel-1",cancelAmount=100000,cancelStatus="DONE",cancelReason="fixture [TIXREF:"+intent["reference"]+"]")])
        result=check_legacy_toss(h.c,"r",raw)
        self.assertEqual(result["refunds"][0]["attribution"],"MATCHED_AS_RECORDED")
        self.assertEqual(result["refunds"][0]["process"],"PG_CANCELLED_AS_RECORDED")
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refunded"],0)

    def test_existing_private_rights_model_financial_terms_binding(self):
        from vendor import rights_model as rm
        ledger,a,b,n,controller=rm.fixture()
        h=self.h; h.chain(); terms=h.c.snapshot()["trades"]["resale"]["termsHash"]
        out=rm.new_note(n,b,"integration-transfer")
        cmd=ledger.prepare("TRANSFER","integration-transfer",n,a,out,b,finance=terms)
        cmd.finance="tampered"
        with self.assertRaisesRegex(rm.Rejected,"BAD_RECOVERY_ACK"): ledger.execute(cmd)
        cmd.finance=terms; ledger.execute(cmd)
        with self.assertRaisesRegex(rm.Rejected,"RIGHT_ALREADY_CONSUMED"):
            ledger.execute(ledger.prepare("ADMIT","stale-admit",n,a))

    def test_two_database_connections_compete_for_same_seat(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/"race.db"); init=Harness(Core(path)); init.event(); init.c.db.close()
            barrier=threading.Barrier(2); outcomes=[]
            def worker(user):
                c=Core(path)
                try:
                    barrier.wait(timeout=5)
                    c.execute("race-"+user,user,"prepare_trade",dict(domain=Core.DOMAIN,tradeId="trade-"+user,inventoryId="show/A1",expectedInventoryVersion=0,buyer=user,amount=100000,expectedVersion=0))
                    outcomes.append("reserved")
                except Rejected: outcomes.append("rejected")
                finally: c.db.close()
            threads=[threading.Thread(target=worker,args=(u,)) for u in ("A","B")]
            for t in threads:t.start()
            for t in threads:t.join(timeout=10)
            self.assertEqual(sorted(outcomes),["rejected","reserved"])

    def test_same_event_other_payment_cannot_fund_refund(self):
        h=self.h; h.event(seats=["A1","A2"])
        h.purchase("t1","show/A1",settle=False); h.purchase("t2","show/A2")
        h.run("cancel_event",eventId="show")
        with self.assertRaisesRegex(Rejected,"INSUFFICIENT_CONFIRMED_FUNDS"): h.effect("r","t1","REFUND",100000)

    def test_marketing_consent_and_revocation_and_finance_minimization(self):
        h=self.h; h.chain()
        self.assertEqual(h.c.view("marketing-adapter","show","marketing"),[])
        h.run("set_consent","B",eventId="show",purpose="next_event_marketing",allowed=True)
        self.assertEqual(h.c.view("marketing-adapter","show","marketing")[0]["subject"],"B")
        h.run("set_consent","B",eventId="show",purpose="next_event_marketing",allowed=False)
        self.assertEqual(h.c.view("marketing-adapter","show","marketing"),[])
        f=h.c.view("finance-adapter","show","finance")
        self.assertEqual((f["primaryCaptured"],f["resaleCaptured"],f["organizerGrossAllocated"]),(100000,120000,97400))
        self.assertNotIn("buyer",f); self.assertNotIn("seller",f)
        self.assertEqual(h.c.view("stranger","show","mine"),dict(tickets={},trades={}))


if __name__=="__main__": unittest.main(verbosity=2)
