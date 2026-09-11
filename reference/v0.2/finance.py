"""Explicit execution routes and double-entry reference accounting; no network I/O."""
from common import canonical, digest, ident, external_id, positive, nonnegative, require

TERMINAL = ("DONE", "ABORTED", "FAILED_FENCED")
ROUTES = {
    "CASH_REFUND_FIXTURE": {"kind": "REFUND", "contract": "fixture:cash-refund:v1", "cash": True,
                            "requiredEvidence": ["PROVIDER_SUCCESS", "BANK_DEBIT_OBSERVED"]},
    "PG_ORIGINAL_CANCEL_FIXTURE": {"kind": "REFUND", "contract": "fixture:pg-cancel:v1", "cash": False,
                                  "requiredEvidence": ["PG_CANCELLED"]},
    "BANK_PAYOUT_FIXTURE": {"kind": "PAYOUT", "contract": "fixture:payout:v1", "cash": True,
                           "requiredEvidence": ["PROVIDER_SUCCESS", "BANK_DEBIT_OBSERVED"]},
}


def cash_reservation(x):
    return max(0, x["amount"]-x["fundsAmount"]) if x["cashRoute"] and x["state"] not in TERMINAL else 0


class FinanceMixin:
    def reverse(self, tid, reason="DELIVERY_FAILED"):
        r = self.trade(tid)
        if not r["reversalRequested"]:
            r["reversalRequested"] = True
            r["allocationVersion"] += 1
        # Unsent work is closed durably, even if a stale worker later retrieves it.
        for x in self.s["effects"].values():
            if x["trade"] == tid and x["kind"] == "PAYOUT" and x["state"] == "PREPARED":
                require(not x["sent"], "PREPARED_EFFECT_ALREADY_SENT")
                x["state"] = "ABORTED"
                x["abortReason"] = "OBLIGATION_REVERSED"
        if not r["captured"]:
            return
        if not r["refundDue"]:
            r["refundDue"] = r["amount"]
            self.post("refund_classification:"+tid, "refund:"+tid, r["amount"], "recognize full refund duty before classifying funding")
            self.s["refund_cases"][tid] = dict(id=tid, reason=reason, sourceTrade=tid,
                rightId=r["ticket"], policyHash=r["policyHash"], beneficiary=r["buyer"],
                debtor="fixture-merchant", amount=r["amount"], currency="KRW", routes=[])
        if r["reversalPlanned"]:
            return
        if any(x["trade"] == tid and x["kind"] == "PAYOUT" and x["state"] not in TERMINAL
               for x in self.s["effects"].values()):
            return
        if r["allocations"]:
            for a in r["allocations"]:
                unpaid = a["amount"]-a["paid"]
                if unpaid:
                    self.post("payable:"+a["id"], "refund_classification:"+tid, unpaid, "cancel unpaid allocation")
                if a["paid"]:
                    self.post("recoverable:"+a["id"], "refund_classification:"+tid, a["paid"], "classify paid allocation recovery")
        else:
            self.post("held:"+tid, "refund_classification:"+tid, r["amount"], "undelivered payment classified")
        r["reversalPlanned"] = True

    def _settle_capture(self, b):
        self.source(b)
        tid=b["tradeId"]; r=self.trade(tid)
        require(r["captured"] and b["paymentId"]==r["paymentId"] and b["currency"]=="KRW", "SETTLEMENT_BINDING_MISMATCH")
        fields=("amount", "feeAmount", "taxAmount", "heldAmount", "adjustmentAmount")
        for f in fields: nonnegative(b[f])
        gross=positive(b["grossAmount"])
        require(sum(b[f] for f in fields)==gross, "SETTLEMENT_COMPONENT_MISMATCH")
        require(b["feeBearer"]=="platform" and b["contractRef"]=="fixture:settlement:v1", "SETTLEMENT_CONTRACT_MISMATCH")
        require(not b["adjustmentAmount"] or isinstance(b.get("adjustmentReason"),str) and b["adjustmentReason"].strip(), "ADJUSTMENT_REASON_REQUIRED")
        binding={k:b[k] for k in ("tradeId","paymentId","currency","grossAmount",*fields,"feeBearer","contractRef")}
        binding["adjustmentReason"]=b.get("adjustmentReason")
        if not self.evidence("funds", b["movementId"], binding): return {"duplicate":True}
        require(gross<=self.balance("pg:"+tid), "SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE")
        for f,account in (("amount","funds:"+r["pool"]),("feeAmount","expense:platform:"+tid),
                          ("taxAmount","tax_withheld:"+tid),("heldAmount","pg_held:"+tid),
                          ("adjustmentAmount","settlement_review:"+tid)):
            if b[f]: self.post(account,"pg:"+tid,b[f],"explicit settlement statement: "+f)
        r["settled"]+=b["amount"]
        r["settlementGross"]+=gross
        return {"settled":r["settled"],"grossAccounted":r["settlementGross"],"feeBearer":"platform"}

    def _prepare_effect(self,b):
        self.role("operator")
        eid=ident(b["effectId"]); require(eid not in self.s["effects"],"EFFECT_EXISTS")
        tid=b["tradeId"]; r=self.trade(tid); kind=b["kind"]; n=positive(b["amount"])
        profile=b["routeProfile"]; require(profile in ROUTES,"UNSUPPORTED_ROUTE")
        route=ROUTES[profile]
        require(kind==route["kind"] and b["contractRef"]==route["contract"],"EXECUTION_CONTRACT_MISMATCH")
        allocation=b.get("allocationId")
        if kind=="PAYOUT":
            require(self.event(r["event"])["status"]=="COMPLETED" and not r["reversalRequested"] and r["status"]=="COMMITTED","PAYOUT_NOT_RELEASED")
            a=next((a for a in r["allocations"] if a["id"]==allocation),None)
            require(a is not None,"ALLOCATION_NOT_FOUND")
            owed="payable:"+allocation; beneficiary=a["payee"]
        else:
            require(r["refundDue"]>0,"REFUND_PLAN_NOT_READY")
            owed="refund:"+tid; beneficiary=r["buyer"]
        pending=list(self.s["effects"].values())
        reserved=sum(x["amount"]-x["appliedAmount"] for x in pending if x["owed"]==owed and x["state"] not in TERMINAL)
        require(n<=-self.balance(owed)-reserved,"OBLIGATION_ALREADY_RESERVED")
        if route["cash"]:
            available=self.balance("funds:"+r["pool"])-sum(cash_reservation(x) for x in pending if x["pool"]==r["pool"])
            require(n<=available,"INSUFFICIENT_CONFIRMED_FUNDS")
            # The real adapter must resolve and authenticate the opaque account reference.
            require(b.get("beneficiaryAccountRef")=="fixture-account:"+beneficiary,"BENEFICIARY_ACCOUNT_REQUIRED")
        else:
            require(r["paymentId"] and n<=r["amount"]-r["originalCancelled"],"ORIGINAL_PAYMENT_BALANCE_EXCEEDED")
        if b.get("retryOf"):
            old=self.s["effects"].get(b["retryOf"])
            require(old and old["state"]=="FAILED_FENCED" and old["owed"]==owed and old["amount"]==n
                    and old["routeProfile"]==profile,"RETRY_REQUIRES_FINAL_FENCE")
        x=dict(trade=tid,kind=kind,amount=n,currency="KRW",beneficiary=beneficiary,allocation=allocation,
               owed=owed,pool=r["pool"],paymentId=r["paymentId"],routeProfile=profile,contractRef=route["contract"],
               cashRoute=route["cash"],requiredEvidence=route["requiredEvidence"],
               fundingBasis="CONFIRMED_POOL_CASH" if route["cash"] else "ORIGINAL_PAYMENT_AND_PG_LIABILITY",
               allocationVersion=r["allocationVersion"],state="PREPARED",sent=False,confirmed=False,
               confirmedAmount=0,fundsAmount=0,appliedAmount=0,fundsObserved=False,conflict=False,returned=0,
               customerCreditConfirmed=0,providerOperationId=None,attemptId=eid+":attempt:1",retryOf=b.get("retryOf"))
        x["request"]=dict(effectId=eid,attemptId=x["attemptId"],tradeId=tid,kind=kind,amount=n,currency="KRW",
                          beneficiary=beneficiary,beneficiaryAccountRef=b.get("beneficiaryAccountRef"),
                          paymentId=r["paymentId"],routeProfile=profile,contractRef=route["contract"],scope=self.SCOPE)
        x["idempotencyKey"]=digest([self.DOMAIN,eid,x["request"]])
        self.s["effects"][eid]=x
        if kind=="REFUND": self.s["refund_cases"][tid]["routes"].append(dict(effectId=eid,profile=profile,amount=n))
        return {"effectId":eid,"idempotencyKey":x["idempotencyKey"],"fundingBasis":x["fundingBasis"]}

    def _send_effect(self,b):
        self.role("operator"); eid=b["effectId"]; x=self.s["effects"][eid]; r=self.trade(x["trade"])
        # Idempotency is not permission to transmit again. One stored intent only.
        if x["sent"] or x["state"]=="DONE":
            return {"effectId":eid,"dispatchDecision":"QUERY_ONLY","state":x["state"]}
        if x["state"] in ("ABORTED","FAILED_FENCED"):
            return {"effectId":eid,"dispatchDecision":"BLOCKED","state":x["state"]}
        valid = x["kind"]!="PAYOUT" or (self.event(r["event"])["status"]=="COMPLETED"
                and not r["reversalRequested"] and x["allocationVersion"]==r["allocationVersion"])
        if not valid:
            x["state"]="ABORTED"; x["abortReason"]="SEND_REVALIDATION_FAILED"
            if r["reversalRequested"]: self.reverse(x["trade"])
            return {"effectId":eid,"dispatchDecision":"BLOCKED","state":"ABORTED"}
        require(x["amount"]<=-self.balance(x["owed"]),"OBLIGATION_CHANGED")
        x["sent"]=True; x["state"]="OUTCOME_UNKNOWN"
        return {"effectId":eid,"dispatchDecision":"FIRST_SEND_INTENT", "unsentFixtureRequest":x["request"],"idempotencyKey":x["idempotencyKey"]}

    def replay_receipt(self,action,receipt,body):
        if action=="send_effect":
            x=self.snapshot()["effects"][body["effectId"]]
            return dict(receipt,result={"effectId":body["effectId"],"dispatchDecision":"QUERY_ONLY","state":x["state"],"replay":True})
        if action=="authorize_marketing":
            # Historical authorization is evidence, not a new dispatch grant.
            return dict(receipt,result={"dispatchDecision":"RECHECK_WITH_NEW_OPERATION","replay":True})
        return receipt

    def _abort_effect(self,b):
        self.role("operator"); x=self.s["effects"][b["effectId"]]
        require(not x["sent"] and not x["fundsAmount"] and not x["confirmedAmount"],"SENT_EFFECT_CANNOT_RELEASE_BY_TIMEOUT")
        x["state"]="ABORTED"
        if self.trade(x["trade"])["reversalRequested"]: self.reverse(x["trade"])
        return {"state":"ABORTED"}

    def finish_effect(self,eid):
        x=self.s["effects"][eid]
        if x["state"]=="DONE": return
        x["confirmed"]=x["confirmedAmount"]==x["amount"]
        x["fundsObserved"]=x["fundsAmount"]==x["amount"]
        matched=min(x["confirmedAmount"],x["fundsAmount"]) if x["cashRoute"] else x["confirmedAmount"]
        delta=matched-x["appliedAmount"]
        if not delta: return
        r=self.trade(x["trade"])
        if x["cashRoute"]:
            self.post(x["owed"],"in_transit:"+eid,delta,"confirmed cumulative partial result and funds matched")
        else:
            self.post(x["owed"],"pg_cancel_due:"+x["trade"],delta,"PG cancellation accepted; merchant settlement remains separate")
            r["originalCancelled"]+=delta
        x["appliedAmount"]=matched
        if matched==x["amount"]: x["state"]="DONE"
        if x["kind"]=="REFUND": r["refunded"]+=delta
        else:
            a=next(a for a in r["allocations"] if a["id"]==x["allocation"]); a["paid"]+=delta
        if r["reversalRequested"]: self.reverse(x["trade"])

    def bind_provider_operation(self,eid,x,provider_id):
        external_id(provider_id)
        binding={"effectId":eid,"paymentId":x["paymentId"],"amount":x["amount"],"routeProfile":x["routeProfile"]}
        # Reusing one external operation for another effect is always forbidden.
        self.evidence("provider-operation",provider_id,binding)
        require(x["providerOperationId"] in (None,provider_id),"SECOND_PROVIDER_OPERATION_REQUIRES_REVIEW")
        x["providerOperationId"]=provider_id

    def _observe_effect(self,b):
        self.source(b); eid=b["effectId"]; require(eid in self.s["effects"],"UNKNOWN_EFFECT")
        x=self.s["effects"][eid]; n=positive(b["amount"])
        require(x["sent"],"EFFECT_NOT_SENT")
        require(x["state"] not in ("ABORTED","FAILED_FENCED"),"LATE_TERMINAL_EFFECT_FACT_REQUIRES_REVIEW")
        require(n<=x["amount"] and b["currency"]==x["currency"] and b["beneficiary"]==x["beneficiary"] and b["paymentId"]==x["paymentId"],"EFFECT_BINDING_MISMATCH")
        self.bind_provider_operation(eid,x,b["providerOperationId"])
        phase=b["phase"]; status=b.get("status")
        require(phase in ("STATUS","FUNDS","PG_CANCELLED","CUSTOMER_CREDIT_CONFIRMED","FENCED_FAILURE"),"UNKNOWN_EVIDENCE_PHASE")
        require(phase!="STATUS" or status in ("SUCCESS","PENDING","FAILED"),"UNKNOWN_PROVIDER_STATUS")
        binding=dict(effect=eid,amount=n,payment=x["paymentId"],beneficiary=x["beneficiary"],phase=phase,status=status,
                     providerOperationId=b["providerOperationId"],movementId=b.get("movementId"),fenceRef=b.get("fenceRef"))
        if not self.evidence("effect-observation",b["sourceId"],binding): return {"duplicate":True}
        if phase=="FUNDS":
            require(x["cashRoute"],"PG_CANCEL_IS_NOT_BANK_DEBIT")
            require(b.get("movementId"),"MOVEMENT_ID_REQUIRED")
            if not self.evidence("funds",b["movementId"],dict(effect=eid,amount=n,direction="OUT",payment=x["paymentId"])): return {"duplicate":True}
            require(x["fundsAmount"]+n<=x["amount"],"SECOND_FUNDS_MOVEMENT_REQUIRES_REVIEW")
            require(self.balance("funds:"+x["pool"])>=n,"FUNDS_BALANCE_CONFLICT")
            self.post("in_transit:"+eid,"funds:"+x["pool"],n,"actual debit observed separately from result")
            x["fundsAmount"]+=n
        elif phase=="PG_CANCELLED":
            require(not x["cashRoute"] and n==x["amount"],"PG_CANCEL_BINDING_MISMATCH")
            x["confirmedAmount"]=n
        elif phase=="CUSTOMER_CREDIT_CONFIRMED":
            require(not x["cashRoute"] and n==x["amount"],"CUSTOMER_CREDIT_BINDING_MISMATCH")
            x["customerCreditConfirmed"]=n
        elif phase=="FENCED_FAILURE":
            require(b.get("fenceRef") and b.get("fenceProvenance")=="synthetic_final_provider_fence"
                    and not x["confirmedAmount"] and not x["fundsAmount"] and n==x["amount"],"FINAL_FAILURE_FENCE_REQUIRED")
            x["state"]="FAILED_FENCED"; x["fenceRef"]=b["fenceRef"]
            if self.trade(x["trade"])["reversalRequested"]: self.reverse(x["trade"])
            return {"state":x["state"]}
        elif status=="SUCCESS":
            require(x["cashRoute"],"USE_PG_CANCEL_EVIDENCE")
            # Status amount is cumulative, movements are incremental.
            x["confirmedAmount"]=max(x["confirmedAmount"],n)
        elif status=="FAILED": x["conflict"]=True
        self.finish_effect(eid)
        return {"state":x["state"],"confirmed":x["confirmed"],"fundsObserved":x["fundsObserved"],"review":x["conflict"]}

    def _adjust_pg_cancel(self,b):
        self.source(b); tid=b["tradeId"]; r=self.trade(tid); n=positive(b["amount"])
        require(b["paymentId"]==r["paymentId"] and b["currency"]=="KRW" and b["contractRef"]=="fixture:pg-cancel:v1","PG_ADJUSTMENT_BINDING_MISMATCH")
        basis=b["basis"]
        require(basis in ("RECEIVABLE_NETTING","BANK_DEBIT_OBSERVED"),"UNSUPPORTED_PG_ADJUSTMENT")
        binding=dict(trade=tid,payment=r["paymentId"],amount=n,basis=basis)
        if not self.evidence("funds" if basis=="BANK_DEBIT_OBSERVED" else "pg-adjustment",b["movementId"],binding): return {"duplicate":True}
        require(n<=-self.balance("pg_cancel_due:"+tid),"PG_ADJUSTMENT_EXCEEDS_DUTY")
        credit="pg:"+tid if basis=="RECEIVABLE_NETTING" else "funds:"+r["pool"]
        available=self.balance(credit)
        if basis=="BANK_DEBIT_OBSERVED":
            available-=sum(cash_reservation(x) for x in self.s["effects"].values() if x["pool"]==r["pool"])
        require(n<=available,"PG_ADJUSTMENT_REQUIRES_RECONCILIATION")
        self.post("pg_cancel_due:"+tid,credit,n,"explicit merchant settlement adjustment")
        return {"merchantSettlementOutstanding":-self.balance("pg_cancel_due:"+tid)}

    def _observe_return(self,b):
        self.source(b); eid=b["effectId"]; x=self.s["effects"][eid]; n=positive(b["amount"])
        require(x["state"]=="DONE" and x["cashRoute"],"RETURN_REQUIRES_COMPLETED_CASH_EFFECT")
        require(b["currency"]=="KRW" and b["paymentId"]==x["paymentId"] and b["payer"]==x["beneficiary"],"RETURN_BINDING_MISMATCH")
        if not self.evidence("funds",b["movementId"],dict(effect=eid,amount=n,direction="RETURN")): return {"duplicate":True}
        require(x["returned"]+n<=x["amount"],"EXCESS_RETURN")
        r=self.trade(x["trade"])
        if x["kind"]=="REFUND":
            credit=x["owed"]; r["refunded"]-=n
        else:
            a=next(a for a in r["allocations"] if a["id"]==x["allocation"])
            if r["reversalRequested"]:
                require(r["reversalPlanned"] and n<=self.balance("recoverable:"+a["id"]),"RETURN_CLASSIFICATION_PENDING")
                credit="recoverable:"+a["id"]; a["recovered"]+=n
            else:
                credit=x["owed"]; a["paid"]-=n
            a["returned"]+=n
        self.post("funds:"+x["pool"],credit,n,"opposite funds fact; never resurrect ticket")
        x["returned"]+=n
        return {"returned":x["returned"],"rightsRestored":False}

    def _observe_funding(self,b):
        self.source(b); r=self.trade(b["tradeId"]); n=positive(b["amount"])
        require(b["payer"]=="platform" and b["contractRef"]=="fixture:platform-funding:v1" and b["currency"]=="KRW","FUNDING_CONTRACT_MISMATCH")
        if not self.evidence("funds",b["movementId"],dict(trade=b["tradeId"],payer="platform",amount=n,direction="FUNDING")): return {"duplicate":True}
        self.post("funds:"+r["pool"],"funding_due:platform:"+r["pool"],n,"explicit platform funding, not audience revenue")
        return {"funding":n}

    def view(self,actor,event_id,kind):
        self.db.execute("BEGIN")
        try:
            value=self._consistent_view(actor,event_id,kind)
            self.db.execute("COMMIT")
            return value
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _consistent_view(self,actor,event_id,kind):
        s=self.snapshot(); require(event_id in s["events"],"EVENT_NOT_FOUND")
        e=s["events"][event_id]; trades={k:r for k,r in s["trades"].items() if r["event"]==event_id}
        if kind=="mine":
            return dict(tickets={k:{f:t[f] for f in ("state","rightsVersion","admissionEpoch","used","inventoryId")} for k,t in s["tickets"].items() if t["event"]==event_id and t["owner"]==actor},
                trades={k:dict({f:r[f] for f in ("kind","amount","currency","status","refundDue","refunded")},
                    partyRole="BUYER" if actor==r["buyer"] else "SELLER",refundBeneficiaryIsYou=actor==r["buyer"])
                    for k,r in trades.items() if actor in (r["buyer"],r["seller"])})
        if kind=="marketing": return self.marketing_view(actor,event_id,s)
        require(kind=="finance" and actor in ("finance-adapter",e["organizer"]),"UNAUTHORIZED_VIEW")
        allocations=[a for r in trades.values() for a in r["allocations"] if a["payee"]==e["organizer"]]
        effects=[x for x in s["effects"].values() if x["trade"] in trades]
        outstanding=sum(r["refundDue"]-r["refunded"] for r in trades.values())
        funding=0; shortage=0; transit_total=0
        for r in trades.values():
            available=max(0,s["balances"].get("funds:"+r["pool"],0)-sum(cash_reservation(x) for x in effects if x["pool"]==r["pool"] and x["kind"]=="PAYOUT"))
            duty=r["refundDue"]-r["refunded"]
            transit=sum(x["fundsAmount"]-x["appliedAmount"] for x in effects if x["pool"]==r["pool"] and x["kind"]=="REFUND" and x["cashRoute"] and x["state"] not in TERMINAL)
            funding+=min(duty,available); shortage+=max(0,duty-available-transit); transit_total+=transit
        inbox=self.inbox_summary(event_id)
        return dict(primaryCaptured=sum(r["amount"] for r in trades.values() if r["captured"] and r["kind"]=="PRIMARY"),
            resaleCaptured=sum(r["amount"] for r in trades.values() if r["captured"] and r["kind"]=="RESALE"),
            primaryRefundObligation=sum(r["refundDue"] for r in trades.values() if r["kind"]=="PRIMARY"),
            resaleRefundObligation=sum(r["refundDue"] for r in trades.values() if r["kind"]=="RESALE"),
            primaryNetAfterRecognizedRefunds=sum(r["amount"]-r["refundDue"] for r in trades.values() if r["kind"]=="PRIMARY" and r["captured"]),
            resaleNetAfterRecognizedRefunds=sum(r["amount"]-r["refundDue"] for r in trades.values() if r["kind"]=="RESALE" and r["captured"]),
            capturedAwaitingRightsOrRefund=sum(r["amount"]-r["refunded"] for r in trades.values() if r["captured"] and r["status"]!="COMMITTED"),
            rightsCommittedAmount=sum(r["amount"] for r in trades.values() if r["status"]=="COMMITTED"),
            organizerGrossAllocated=sum(a["amount"] for a in allocations),organizerPaid=sum(a["paid"] for a in allocations),
            organizerPayable=sum(-s["balances"].get("payable:"+a["id"],0) for a in allocations),
            organizerRecoveryOutstanding=sum(s["balances"].get("recoverable:"+a["id"],0) for a in allocations),
            refundObligation=sum(r["refundDue"] for r in trades.values()),refundOutstanding=outstanding,
            refundFulfilled=sum(r["refunded"] for r in trades.values()),
            refundUnclassified=sum(s["balances"].get("refund_classification:"+tid,0) for tid in trades),
            refundPlansPending=sum(r["reversalRequested"] and r["captured"] and not r["reversalPlanned"] for r in trades.values()),
            payoutOutcomeUnknown=sum(x["amount"]-x["appliedAmount"] for x in effects if x["kind"]=="PAYOUT" and x["sent"] and x["state"] not in TERMINAL),
            confirmedRefundCash=funding,refundFundsInTransit=transit_total,cashRouteShortfall=shortage,
            pgMerchantAdjustmentOutstanding=sum(-s["balances"].get("pg_cancel_due:"+tid,0) for tid in trades),
            customerCreditConfirmed=sum(x["customerCreditConfirmed"] for x in effects),
            pgFees=sum(s["balances"].get("expense:platform:"+tid,0) for tid in trades),
            sourceReview=inbox,evidenceClass="synthetic",currency="KRW",sequence=len(s["events_log"]),
            asOf={"logicalTime":s["clock"],"sequence":len(s["events_log"])},policyHash=e["policyHash"],
            sourceScope=self.SCOPE,sourceCompleteness="NOT_ATTESTED",chainCheckpoint=None,
            calculatorVersion=self.DOMAIN)

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
        positive_prefix=("funds:","pg:","recoverable:","in_transit:","refund_classification:","expense:","tax_withheld:","pg_held:","settlement_review:")
        for account,n in balances.items():
            require(type(n) is int and (n>=0 if account.startswith(positive_prefix) else n<=0),"ACCOUNT_SIGN_VIOLATION")
        for tid,r in s["trades"].items():
            require(0<=r["refunded"]<=r["refundDue"]<=r["amount"],"REFUND_OVERPAY")
            require(-balances.get("refund:"+tid,0)==r["refundDue"]-r["refunded"],"REFUND_LEDGER_MISMATCH")
            if r["allocations"]: require(sum(a["amount"] for a in r["allocations"])==r["amount"],"ALLOCATION_MISMATCH")
            for a in r["allocations"]: require(0<=a["recovered"]<=a["paid"]<=a["amount"],"ALLOCATION_OVERPAY")
        for x in s["effects"].values():
            require(0<=x["appliedAmount"]<=x["confirmedAmount"]<=x["amount"] and 0<=x["fundsAmount"]<=x["amount"],"EFFECT_AMOUNT_MISMATCH")
            require(not x["cashRoute"] or x["appliedAmount"]<=x["fundsAmount"],"UNFUNDED_EFFECT_APPLICATION")
        for tid,t in s["tickets"].items():
            if t["lock"]:
                r=s["trades"][t["lock"]]
                require(r["status"]=="PREPARED" and r["expectedVersion"]==t["rightsVersion"] and r["ticket"]==tid,"BROKEN_TICKET_LOCK")
        for iid,unit in s["inventory"].items():
            live=[tid for tid,t in s["tickets"].items() if t["inventoryId"]==iid and t["state"]!="VOID"]
            require(len(live)<=1,"DUPLICATE_LIVE_INVENTORY_RIGHT")
            require(not live or live==[unit["currentRight"]],"INVENTORY_RIGHT_MISMATCH")
        for pool in {x["pool"] for x in s["effects"].values()}:
            reserved=sum(cash_reservation(x) for x in s["effects"].values() if x["pool"]==pool)
            require(reserved<=balances.get("funds:"+pool,0),"OVERRESERVED_CASH")
