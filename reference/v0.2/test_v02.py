"""Behavioral regressions derived from the independent v0.1 review."""
import copy
import itertools
import json
import tempfile
import threading
import unittest
from pathlib import Path

from common import canonical, digest
from core import Core, Rejected
from test_core import Harness, POLICY


def raw(action,**body):
    return canonical(dict(action=action,body=dict(domain=Core.DOMAIN,scope=Core.SCOPE,provenance="synthetic",**body))).encode()


class ReviewRegressions(unittest.TestCase):
    def setUp(self): self.h=Harness()
    def tearDown(self): self.h.c.db.close()

    def test_completed_event_refuses_admission(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_ADMISSIBLE"):
            h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)

    def test_completed_event_guard_survives_stale_gate_configuration(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        # Fault injection: the independent gate configuration lags event completion.
        state=h.c.snapshot(); state["events"]["show"]["admissionStatus"]="OPEN"
        Core.check(state); h.c.db.execute("UPDATE state SET body=?",(canonical(state),))
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_ADMISSIBLE"):
            h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)

    def test_stale_resale_version_rejected_at_prepare(self):
        h=self.h; h.event(); h.purchase()
        with self.assertRaisesRegex(Rejected,"STALE_RIGHTS_VERSION"):
            h.run("prepare_trade","A",tradeId="stale",ticketId=h.right(),buyer="B",amount=120000,expectedVersion=0)

    def test_non_operator_cannot_commit_paid_trade(self):
        h=self.h; h.event(); h.prepare(); h.capture()
        with self.assertRaisesRegex(Rejected,"UNAUTHORIZED"):
            h.run("commit_trade","A",tradeId="primary")
        self.assertIsNone(h.c.snapshot()["tickets"][h.right()]["owner"])

    def test_stranger_cannot_refund_current_right(self):
        h=self.h; h.event(); h.purchase()
        with self.assertRaisesRegex(Rejected,"UNAUTHORIZED"):
            h.run("refund_ticket","B",ticketId=h.right(),expectedVersion=1)

    def test_delegation_requires_actual_final_fixture_marker(self):
        h=self.h; h.event(); h.purchase()
        d=h.run("delegate","A",ticketId=h.right(),expectedVersion=1)["result"]
        with self.assertRaisesRegex(Rejected,"FINAL_USE_RESULT_REQUIRED"):
            h.run("close_delegation","venue",ticketId=h.right(),session=d["session"],admissionEpoch=d["admissionEpoch"],used=False,provenance="nonfinal_log")

    def test_cancel_prepared_payout_blocks_first_and_duplicate_send(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        h.run("prepare_effect",effectId="p",tradeId="primary",kind="PAYOUT",amount=95000,allocationId="primary-0")
        h.run("cancel_event",eventId="show")
        x=h.c.snapshot()["effects"]["p"]
        self.assertEqual(x["state"],"ABORTED"); self.assertFalse(x["sent"])
        for op in ("same-dispatch","same-dispatch","new-dispatch"):
            reply=h.run("send_effect",op=op,effectId="p")["result"]
            self.assertNotIn("unsentFixtureRequest",reply)
        f=h.c.view("finance-adapter","show","finance")
        self.assertEqual((f["refundObligation"],f["refundOutstanding"],f["organizerPayable"]),(100000,100000,0))
        h.refund_all()

    def test_send_boundary_checks_allocation_version_even_without_cancel(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        h.run("prepare_effect",effectId="p",tradeId="primary",kind="PAYOUT",amount=95000,allocationId="primary-0")
        # Boundary fixture: simulate an allocation revision after preparation.
        s=h.c.snapshot(); s["trades"]["primary"]["allocationVersion"]+=1
        h.c.db.execute("UPDATE state SET body=?",(canonical(s),))
        result=h.run("send_effect",effectId="p")["result"]
        self.assertEqual(result["dispatchDecision"],"BLOCKED")
        self.assertFalse(h.c.snapshot()["effects"]["p"]["sent"])

    def test_unknown_payout_keeps_full_refund_exposure_and_query_only(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        h.run("prepare_effect",effectId="p",tradeId="primary",kind="PAYOUT",amount=95000,allocationId="primary-0")
        first=h.run("send_effect",op="send-once",effectId="p")["result"]
        self.assertEqual(first["dispatchDecision"],"FIRST_SEND_INTENT")
        h.run("cancel_event",eventId="show")
        for op in ("send-once","fresh-send-id"):
            result=h.run("send_effect",op=op,effectId="p")["result"]
            self.assertEqual(result["dispatchDecision"],"QUERY_ONLY"); self.assertNotIn("unsentFixtureRequest",result)
        f=h.c.view("finance-adapter","show","finance")
        self.assertEqual((f["refundObligation"],f["refundUnclassified"],f["payoutOutcomeUnknown"]),(100000,100000,95000))
        self.assertEqual((f["confirmedRefundCash"],f["cashRouteShortfall"]),(5000,95000))
        h.finish("p")
        f=h.c.view("finance-adapter","show","finance")
        self.assertEqual((f["refundUnclassified"],f["organizerRecoveryOutstanding"]),(0,95000))

    def test_pg_cancel_before_settlement_needs_no_cash_and_separate_credit(self):
        h=self.h; h.event(); h.purchase(settle=False); h.run("cancel_event",eventId="show")
        h.effect("r","primary","REFUND",100000,routeProfile="PG_ORIGINAL_CANCEL_FIXTURE")
        h.observe("r","PG_CANCELLED")
        s=h.c.snapshot(); self.assertEqual(s["trades"]["primary"]["refunded"],100000)
        self.assertFalse(s["effects"]["r"]["fundsObserved"])
        self.assertEqual(s["balances"]["pg_cancel_due:primary"],-100000)
        self.assertEqual(h.c.view("finance-adapter","show","finance")["customerCreditConfirmed"],0)
        h.source("adjust_pg_cancel",tradeId="primary",paymentId="pay-primary",amount=100000,currency="KRW",
                 contractRef="fixture:pg-cancel:v1",basis="RECEIVABLE_NETTING",movementId="pg-net-1")
        h.observe("r","CUSTOMER_CREDIT_CONFIRMED")
        self.assertTrue(all(v==0 for v in h.c.snapshot()["balances"].values()))
        self.assertEqual(h.c.view("finance-adapter","show","finance")["customerCreditConfirmed"],100000)

    def test_post_settlement_pg_cancel_does_not_fabricate_bank_debit(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show")
        h.effect("r","primary","REFUND",100000,routeProfile="PG_ORIGINAL_CANCEL_FIXTURE"); h.observe("r","PG_CANCELLED")
        s=h.c.snapshot(); pool=s["trades"]["primary"]["pool"]
        self.assertEqual(s["balances"]["funds:"+pool],100000)
        self.assertEqual(s["balances"]["pg_cancel_due:primary"],-100000)
        with self.assertRaisesRegex(Rejected,"PG_CANCEL_IS_NOT_BANK_DEBIT"): h.observe("r","FUNDS")
        h.source("adjust_pg_cancel",tradeId="primary",paymentId="pay-primary",amount=100000,currency="KRW",
                 contractRef="fixture:pg-cancel:v1",basis="BANK_DEBIT_OBSERVED",movementId="cancel-debit")
        self.assertTrue(all(v==0 for v in h.c.snapshot()["balances"].values()))

    def test_pg_cancel_can_complete_while_payout_classification_is_unknown(self):
        h=self.h; h.event(); h.purchase(); h.run("complete_event",eventId="show")
        h.effect("p","primary","PAYOUT",95000,"primary-0"); h.run("cancel_event",eventId="show")
        h.effect("r","primary","REFUND",100000,routeProfile="PG_ORIGINAL_CANCEL_FIXTURE"); h.observe("r","PG_CANCELLED")
        f=h.c.view("finance-adapter","show","finance")
        self.assertEqual((f["refundFulfilled"],f["refundUnclassified"],f["pgMerchantAdjustmentOutstanding"]),(100000,100000,100000))
        h.finish("p")
        self.assertEqual(h.c.snapshot()["balances"]["recoverable:primary-0"],95000)

    def test_pg_and_cash_routes_share_same_refund_limit(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show")
        h.effect("pg","primary","REFUND",100000,routeProfile="PG_ORIGINAL_CANCEL_FIXTURE")
        with self.assertRaisesRegex(Rejected,"OBLIGATION_ALREADY_RESERVED"): h.effect("cash","primary","REFUND",1)
        h.observe("pg","PG_CANCELLED")
        with self.assertRaisesRegex(Rejected,"OBLIGATION_ALREADY_RESERVED"): h.effect("cash2","primary","REFUND",1)

    def test_settlement_explicit_fee_bearer_and_cash_shortfall(self):
        h=self.h; h.event(); h.purchase(settle=False)
        h.source("settle_capture",tradeId="primary",paymentId="pay-primary",amount=97000,grossAmount=100000,
                 feeAmount=3000,currency="KRW",sourceId="net-statement")
        s=h.c.snapshot(); self.assertEqual(s["balances"]["pg:primary"],0)
        self.assertEqual(s["balances"]["expense:platform:primary"],3000)
        h.run("complete_event",eventId="show")
        h.effect("p","primary","PAYOUT",95000,"primary-0"); h.finish("p")
        with self.assertRaisesRegex(Rejected,"INSUFFICIENT_CONFIRMED_FUNDS"):
            h.effect("fee","primary","PAYOUT",5000,"primary-1")
        h.source("observe_funding",tradeId="primary",payer="platform",amount=3000,currency="KRW",contractRef="fixture:platform-funding:v1",movementId="platform-in")
        h.effect("fee","primary","PAYOUT",5000,"primary-1"); h.finish("fee")
        s=h.c.snapshot(); self.assertEqual(sum(v for a,v in s["balances"].items() if a.startswith("funds:")),0)
        self.assertEqual(sum(s["balances"].values()),0)

    def test_net_only_statement_does_not_invent_fee(self):
        h=self.h; h.event(); h.purchase(settle=False)
        h.source("settle_capture",tradeId="primary",paymentId="pay-primary",amount=97000,currency="KRW",sourceId="partial")
        s=h.c.snapshot(); self.assertEqual(s["balances"]["pg:primary"],3000)
        self.assertNotIn("expense:platform:primary",s["balances"])

    def test_single_execution_partial_funds_and_duplicate_movements(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        h.observe("r","STATUS","SUCCESS",amount=40000)
        h.observe("r","FUNDS",amount=40000,source_id="observation-a",movementId="bank-part-a")
        h.observe("r","FUNDS",amount=40000,source_id="observation-b",movementId="bank-part-a")
        self.assertEqual(h.c.snapshot()["effects"]["r"]["fundsAmount"],40000)
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refunded"],40000)
        h.observe("r","STATUS","SUCCESS",amount=100000,source_id="status-final")
        h.observe("r","FUNDS",amount=60000,source_id="observation-c",movementId="bank-part-b")
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refunded"],100000)

    def test_final_failure_fence_allows_new_attempt_but_late_fact_is_reviewed(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        h.observe("r","STATUS","FAILED")
        with self.assertRaisesRegex(Rejected,"OBLIGATION_ALREADY_RESERVED"):
            h.effect("r2","primary","REFUND",100000,retryOf="r")
        h.observe("r","FENCED_FAILURE",fenceRef="provider-final-record",fenceProvenance="synthetic_final_provider_fence")
        h.effect("r2","primary","REFUND",100000,retryOf="r")
        result=h.c.ingest("late-debit",raw("observe_effect",effectId="r",phase="FUNDS",sourceId="late-status",providerOperationId="provider-r",movementId="late-move",amount=100000,currency="KRW",beneficiary="A",paymentId="pay-primary"),fixture_authenticated=True)
        self.assertEqual(result["state"],"REVIEW")
        self.assertEqual(h.c.inbox_summary("show")["observedMovementAmountUnderReview"],100000)
        self.assertEqual(h.c.snapshot()["effects"]["r"]["fundsAmount"],0)

    def test_returned_refund_restores_money_duty_but_never_right(self):
        h=self.h; h.event(); h.purchase(); old=h.right(); h.run("refund_ticket","A",ticketId=old,expectedVersion=1)
        h.effect("r","primary","REFUND",100000); h.finish("r")
        h.source("observe_return",effectId="r",paymentId="pay-primary",payer="A",amount=100000,currency="KRW",movementId="returned")
        s=h.c.snapshot(); self.assertEqual(s["trades"]["primary"]["refunded"],0)
        self.assertEqual(s["tickets"][old]["state"],"VOID")
        h.effect("r-again","primary","REFUND",100000); h.finish("r-again")

    def test_refund_reissue_has_new_id_old_right_and_trade_stay_closed(self):
        h=self.h; h.event(); h.purchase(); old=h.right()
        h.run("refund_ticket","A",ticketId=old,expectedVersion=1); h.refund_all()
        version=h.c.snapshot()["inventory"]["show/A1"]["version"]
        h.run("release_inventory",inventoryId="show/A1",closedRightId=old,expectedInventoryVersion=version)
        h.purchase("second",buyer="B"); new=h.right(); self.assertNotEqual(old,new)
        self.assertEqual(h.c.snapshot()["tickets"][old]["state"],"VOID")
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_ADMISSIBLE"):
            h.run("admit","venue",ticketId=old,holder="A",expectedVersion=1,admissionEpoch=1)
        with self.assertRaisesRegex(Rejected,"TRADE_NOT_COMMITTABLE"): h.run("commit_trade",tradeId="primary")
        h.run("admit","venue",ticketId=new,holder="B",expectedVersion=1,admissionEpoch=1)
        Core.check(h.c.snapshot())

    def test_unknown_gate_use_and_consumed_right_block_inventory_release(self):
        h=self.h; h.event(); h.purchase(); rid=h.right()
        d=h.run("delegate","A",ticketId=rid,expectedVersion=1)["result"]
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_SAFELY_CLOSED"):
            h.run("release_inventory",inventoryId="show/A1",closedRightId=rid,expectedInventoryVersion=1)
        h.run("close_delegation","venue",ticketId=rid,session=d["session"],admissionEpoch=d["admissionEpoch"],used=True,provenance="synthetic_final_controller_log")
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_SAFELY_CLOSED"):
            h.run("release_inventory",inventoryId="show/A1",closedRightId=rid,expectedInventoryVersion=1)

    def test_late_payment_after_expiry_and_reissue_cannot_issue_old_right(self):
        h=self.h; h.event(); h.prepare(); old=h.right()
        h.run("advance_clock",now=900); h.run("expire_trade",tradeId="primary")
        h.run("void_unissued",ticketId=old)
        h.run("release_inventory",inventoryId="show/A1",closedRightId=old,expectedInventoryVersion=1)
        h.purchase("second",buyer="B"); h.capture("primary")
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refundDue"],100000)
        with self.assertRaisesRegex(Rejected,"TRADE_NOT_COMMITTABLE"): h.run("commit_trade",tradeId="primary")
        self.assertEqual(h.c.snapshot()["tickets"][h.right()]["owner"],"B")

    def test_latest_trade_profile_does_not_refund_prior_buyers(self):
        h=self.h; h.event(policy=dict(POLICY,refundProfile="LATEST_TRADE_UNWIND_FIXTURE"))
        h.purchase(); h.purchase("resale",buyer="B",amount=120000)
        h.run("refund_ticket","B",ticketId=h.right(),expectedVersion=2)
        s=h.c.snapshot(); self.assertEqual(s["trades"]["primary"]["refundDue"],0)
        self.assertEqual(s["trades"]["resale"]["refundDue"],120000)
        self.assertEqual(s["refund_cases"]["resale"]["reason"],"CURRENT_HOLDER_REFUND")

    def test_event_cancel_also_reverses_prior_closed_issuance_trades(self):
        h=self.h; h.event(policy=dict(POLICY,refundProfile="LATEST_TRADE_UNWIND_FIXTURE"))
        h.purchase(); h.purchase("resale",buyer="B",amount=120000)
        h.run("refund_ticket","B",ticketId=h.right(),expectedVersion=2)
        h.refund_all(); h.run("cancel_event",eventId="show")
        self.assertEqual(h.c.snapshot()["trades"]["primary"]["refundDue"],100000)
        self.assertEqual(h.c.snapshot()["trades"]["resale"]["refundDue"],120000)

    def test_cash_refund_formatter_cannot_be_used_for_pg_cancellation(self):
        from adapters import unsent_refund_request
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        with self.assertRaisesRegex(Rejected,"NOT_AN_ORIGINAL_PAYMENT_CANCEL"): unsent_refund_request(h.c,"r")

    def test_in_transit_refund_is_not_reported_as_new_cash_shortage(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show"); h.effect("r","primary","REFUND",100000)
        h.observe("r","FUNDS")
        f=h.c.view("finance-adapter","show","finance")
        self.assertEqual((f["refundFulfilled"],f["refundFundsInTransit"],f["cashRouteShortfall"]),(0,100000,0))

    def test_cancel_status_and_settlement_order_keep_explicit_pg_duty(self):
        for order in itertools.permutations(("CANCEL_RESULT","SETTLEMENT")):
            with self.subTest(order=order):
                h=Harness(); h.event(); h.purchase(settle=False); h.run("cancel_event",eventId="show")
                try:
                    h.effect("r","primary","REFUND",100000,routeProfile="PG_ORIGINAL_CANCEL_FIXTURE")
                    for fact in order:
                        if fact=="CANCEL_RESULT": h.observe("r","PG_CANCELLED")
                        else: h.source("settle_capture",tradeId="primary",paymentId="pay-primary",amount=100000,currency="KRW",sourceId="settlement")
                    h.source("adjust_pg_cancel",tradeId="primary",paymentId="pay-primary",amount=100000,currency="KRW",contractRef="fixture:pg-cancel:v1",basis="BANK_DEBIT_OBSERVED",movementId="debit")
                    self.assertTrue(all(n==0 for n in h.c.snapshot()["balances"].values()))
                finally: h.c.db.close()

    def test_listing_allows_admission_and_is_invalidated_on_use(self):
        h=self.h; h.event(); h.purchase()
        reply=h.run("create_listing","A",listingId="L",ticketId=h.right(),expectedVersion=1,amount=120000,expiresAt=600)["result"]
        self.assertFalse(reply["rightLocked"])
        h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)
        self.assertEqual(h.c.snapshot()["listings"]["L"]["state"],"INVALIDATED")
        with self.assertRaises(Rejected): h.run("reserve_listing","B",listingId="L",listingHash=reply["termsHash"],tradeId="r",expiresAt=500)

    def test_listing_reservation_is_exclusive_and_expiry_fences_commit(self):
        h=self.h; h.event(); h.purchase()
        listing=h.run("create_listing","A",listingId="L",ticketId=h.right(),expectedVersion=1,amount=120000,expiresAt=600)["result"]
        h.run("reserve_listing","B",listingId="L",listingHash=listing["termsHash"],tradeId="r",expiresAt=500)
        with self.assertRaises(Rejected): h.run("reserve_listing","C",listingId="L",listingHash=listing["termsHash"],tradeId="r2",expiresAt=500)
        with self.assertRaisesRegex(Rejected,"RIGHT_NOT_ADMISSIBLE"): h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)
        h.run("advance_clock",now=500)
        h.capture("r")
        with self.assertRaisesRegex(Rejected,"TRADE_NOT_COMMITTABLE"): h.run("commit_trade",tradeId="r")
        h.run("expire_trade",tradeId="r")
        self.assertEqual(h.c.snapshot()["listings"]["L"]["state"],"CLOSED")
        h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)

    def test_gift_needs_recipient_acceptance_and_invalidates_old_presentation(self):
        h=self.h; h.event(); h.purchase(); before=h.c.snapshot()["journal"]
        g=h.run("offer_gift","A",giftId="gift",ticketId=h.right(),expectedVersion=1,recipient="B",expiresAt=600)["result"]
        self.assertEqual(h.c.snapshot()["tickets"][h.right()]["owner"],"A")
        with self.assertRaisesRegex(Rejected,"UNAUTHORIZED"): h.run("accept_gift","C",giftId="gift",termsHash=g["termsHash"])
        h.run("accept_gift","B",giftId="gift",termsHash=g["termsHash"])
        self.assertEqual(h.c.snapshot()["journal"],before)
        with self.assertRaisesRegex(Rejected,"STALE_OR_WRONG_PRESENTATION"): h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)
        with self.assertRaisesRegex(Rejected,"INVALID_AMOUNT"): h.prepare("zero-sale",buyer="C",amount=0)

    def test_invitation_requires_issuer_quota_and_no_zero_money_entries(self):
        h=self.h; h.event(seats=["A1","A2"],invitationQuota=1)
        with self.assertRaisesRegex(Rejected,"UNAUTHORIZED"): h.run("issue_invitation","A",inventoryId="show/A1",expectedInventoryVersion=0,recipient="B")
        h.run("issue_invitation","organizer",inventoryId="show/A1",expectedInventoryVersion=0,recipient="B")
        with self.assertRaisesRegex(Rejected,"INVITATION_QUOTA_EXCEEDED"): h.run("issue_invitation","organizer",inventoryId="show/A2",expectedInventoryVersion=0,recipient="C")
        self.assertEqual(h.c.snapshot()["journal"],[])
        h.run("refund_ticket","B",ticketId=h.right(),expectedVersion=1)
        self.assertEqual(h.c.snapshot()["refund_cases"],{})

    def test_sales_close_preserves_admission_until_performance_complete(self):
        h=self.h; h.event(admissionStatus="CLOSED"); h.purchase()
        with self.assertRaisesRegex(Rejected,"ADMISSION_CLOSED"): h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)
        h.run("close_sales",eventId="show"); h.run("open_admission",eventId="show")
        with self.assertRaisesRegex(Rejected,"SALES_CLOSED"): h.prepare("r",buyer="B",amount=120000)
        h.run("admit","venue",ticketId=h.right(),holder="A",expectedVersion=1,admissionEpoch=1)

    def test_old_consent_new_id_is_rejected_and_new_intent_is_accepted(self):
        h=self.h; h.event()
        h.run("set_consent","A",eventId="show",purpose="next_event_marketing",allowed=True,expectedConsentVersion=0)
        h.run("set_consent","A",eventId="show",purpose="next_event_marketing",allowed=False,expectedConsentVersion=1)
        with self.assertRaisesRegex(Rejected,"STALE_CONSENT_VERSION"):
            h.run("set_consent","A",eventId="show",purpose="next_event_marketing",allowed=True,expectedConsentVersion=0)
        self.assertEqual(h.c.view("marketing-adapter","show","marketing"),[])
        h.run("set_consent","A",eventId="show",purpose="next_event_marketing",allowed=True,expectedConsentVersion=2)
        self.assertEqual(h.c.view("marketing-adapter","show","marketing")[0]["consentVersion"],3)

    def test_marketing_dispatch_rechecks_channel_and_revocation(self):
        h=self.h; h.event(); h.run("set_consent","A",eventId="show",purpose="next_event_marketing",allowed=True)
        body=dict(eventId="show",subject="A",business="KIX",channel="email",purpose="next_event_marketing",expectedConsentVersion=1)
        h.run("authorize_marketing","marketing-adapter",op="send-marketing",**body)
        h.run("set_consent","A",eventId="show",purpose="next_event_marketing",allowed=False)
        with self.assertRaisesRegex(Rejected,"CONSENT_NOT_CURRENT"): h.run("authorize_marketing","marketing-adapter",**body)
        self.assertEqual(h.run("authorize_marketing","marketing-adapter",op="send-marketing",**body)["result"]["dispatchDecision"],"RECHECK_WITH_NEW_OPERATION")

    def test_provider_ids_have_stable_mapping_and_full_payment_key(self):
        h=self.h; h.event(); h.prepare("주문 1")
        r=h.c.snapshot()["trades"]["주문 1"]
        self.assertRegex(r["externalOrderId"],r"^[A-Za-z0-9_-]{6,64}$")
        h.source("capture",tradeId="주문 1",orderId=r["externalOrderId"],paymentId="p"*200,amount=100000,currency="KRW",buyer="A")
        self.assertEqual(h.c.snapshot()["trades"]["주문 1"]["paymentId"],"p"*200)

    def test_strict_envelope_rejects_unknown_fields_and_missing_route(self):
        h=self.h; h.event(); h.purchase(); h.run("cancel_event",eventId="show")
        with self.assertRaisesRegex(Rejected,"UNKNOWN_FIELDS"):
            h.run("send_effect",effectId="no",bypass=True)
        with self.assertRaisesRegex(Rejected,"MISSING_FIELDS"):
            h.c.execute("no-route","operator","prepare_effect",dict(domain=Core.DOMAIN,effectId="r",tradeId="primary",kind="REFUND",amount=100000))


class InboxAndRecoveryTests(unittest.TestCase):
    def test_second_capture_is_preserved_and_deduplicated_under_review(self):
        h=Harness(); self.addCleanup(h.c.db.close); h.event(); h.purchase()
        before=h.c.snapshot(); r=before["trades"]["primary"]
        blob=raw("capture",tradeId="primary",orderId=r["externalOrderId"],paymentId="second-payment",amount=100000,currency="KRW",buyer="A")
        for oid in ("raw-a","raw-b","raw-a"):
            result=h.c.ingest(oid,blob,fixture_authenticated=True); self.assertEqual(result["state"],"REVIEW")
        self.assertEqual(h.c.snapshot(),before)
        self.assertEqual(h.c.inbox_summary("show")["observedCaptureAmountUnderReview"],100000)
        row=h.c.db.execute("SELECT raw FROM raw_inbox WHERE id='raw-a'").fetchone()
        self.assertIsNotNone(row); self.assertEqual(row[0],blob)

    def test_raw_crash_and_domain_commit_crash_are_recoverable(self):
        for point in ("fail_after_store","fail_before_apply_commit"):
            with self.subTest(point=point),tempfile.TemporaryDirectory() as temp:
                path=str(Path(temp)/"state.db"); h=Harness(Core(path)); h.event(); h.prepare()
                r=h.c.snapshot()["trades"]["primary"]
                blob=raw("capture",tradeId="primary",orderId=r["externalOrderId"],paymentId="pay-primary",amount=100000,currency="KRW",buyer="A")
                with self.assertRaises(RuntimeError): h.c.ingest("obs",blob,fixture_authenticated=True,**{point:True})
                h.c.db.close(); c=Core(path)
                try:
                    self.assertFalse(c.snapshot()["trades"]["primary"]["captured"])
                    self.assertEqual(c.apply_observation("obs",fixture_authenticated=True)["state"],"APPLIED")
                    before=c.snapshot()["balances"]
                    c.apply_observation("obs",fixture_authenticated=True)
                    self.assertEqual(c.snapshot()["balances"],before)
                finally: c.db.close()

    def test_invalid_and_conflicting_raw_are_not_erased_or_authenticated(self):
        c=Core(); self.addCleanup(c.db.close)
        result=c.ingest("invalid",b"not-json",fixture_authenticated=False)
        self.assertEqual(result["error"],"SOURCE_AUTHENTICATION_REQUIRED")
        with self.assertRaisesRegex(Rejected,"CONFLICT_PRESERVED"): c.ingest("invalid",b"different-raw")
        self.assertEqual(c.db.execute("SELECT count(*) FROM raw_conflicts").fetchone()[0],1)
        self.assertEqual(c.snapshot()["journal"],[])

    def test_local_replay_rebuilds_rights_obligations_and_pending_intent(self):
        h=Harness(); self.addCleanup(h.c.db.close); h.chain(); h.run("complete_event",eventId="show")
        h.effect("p","resale","PAYOUT",114000,"resale-0"); h.run("cancel_event",eventId="show")
        exported=h.c.export_replay(); c=Core.rebuild_fixture(exported); self.addCleanup(c.db.close)
        self.assertEqual(c.snapshot(),h.c.snapshot())
        self.assertEqual(c.view("finance-adapter","show","finance"),h.c.view("finance-adapter","show","finance"))
        reply=c.execute("after-recovery","operator","send_effect",dict(domain=Core.DOMAIN,effectId="p"))["result"]
        self.assertEqual(reply["dispatchDecision"],"QUERY_ONLY")
        self.assertFalse(exported["chainFinalityVerified"])

    def test_rebuild_preserves_rejected_raw_without_upgrading_authentication(self):
        h=Harness(); self.addCleanup(h.c.db.close); h.event(); h.purchase()
        r=h.c.snapshot()["trades"]["primary"]
        blob=raw("capture",tradeId="primary",orderId=r["externalOrderId"],paymentId="second",amount=100000,currency="KRW",buyer="A")
        h.c.ingest("second",blob,fixture_authenticated=True)
        h.c.ingest("unauthenticated",b"not-json",fixture_authenticated=False)
        with self.assertRaises(Rejected): h.c.ingest("unauthenticated",b"changed")
        export=h.c.export_replay(); c=Core.rebuild_fixture(export); self.addCleanup(c.db.close)
        self.assertEqual(c.export_replay(),export)
        self.assertEqual(c.inbox_summary("show"),h.c.inbox_summary("show"))
        tampered=copy.deepcopy(export); tampered["rawInbox"][0]["fixtureVerified"]=123
        with self.assertRaisesRegex(Rejected,"REPLAY_EVIDENCE_MISMATCH"): Core.rebuild_fixture(tampered)

    def test_cancel_and_first_send_are_serialized_and_unknown_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/"race.db"); h=Harness(Core(path)); h.event(); h.purchase(); h.run("complete_event",eventId="show")
            h.run("prepare_effect",effectId="p",tradeId="primary",kind="PAYOUT",amount=95000,allocationId="primary-0"); h.c.db.close()
            barrier=threading.Barrier(2); results=[]; errors=[]
            def worker(action,body):
                c=Core(path)
                try:
                    barrier.wait(timeout=5)
                    results.append(c.execute("race-"+action,"operator",action,dict(domain=Core.DOMAIN,**body)))
                except BaseException as exc: errors.append(str(exc))
                finally: c.db.close()
            threads=[threading.Thread(target=worker,args=("send_effect",{"effectId":"p"})),threading.Thread(target=worker,args=("cancel_event",{"eventId":"show"}))]
            for t in threads: t.start()
            for t in threads: t.join(timeout=10)
            self.assertEqual(errors,[]); self.assertEqual(len(results),2)
            c=Core(path)
            try:
                s=c.snapshot(); x=s["effects"]["p"]
                self.assertEqual(s["trades"]["primary"]["refundDue"],100000)
                order={r["action"]:r["sequence"] for r in results}
                if order["cancel_event"]<order["send_effect"]:
                    self.assertFalse(x["sent"]); self.assertEqual(x["state"],"ABORTED")
                else:
                    self.assertTrue(x["sent"]); self.assertEqual(x["state"],"OUTCOME_UNKNOWN")
                Core.check(s)
            finally: c.db.close()


if __name__=="__main__": unittest.main(verbosity=2)
