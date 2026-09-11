"""Inventory, issuance, offers and consent. Time/actors remain injected fixtures."""
from common import canonical, digest, ident, positive, nonnegative, require

REFUND_PROFILES=("FULL_CHAIN_UNWIND_FIXTURE","LATEST_TRADE_UNWIND_FIXTURE")


class LifecycleMixin:
    def _create_event(self,b):
        self.role("operator"); eid=ident(b["eventId"])
        require(eid not in self.s["events"],"EVENT_EXISTS")
        p=b["policy"]
        require(set(p)=={"primaryPrice","resaleCap","primaryFeeBps","resaleFeeBps","resaleOrganizerBps","resaleAllowed","refundProfile"},"INVALID_POLICY")
        positive(p["primaryPrice"]); positive(p["resaleCap"])
        require(type(p["resaleAllowed"]) is bool and p["refundProfile"] in REFUND_PROFILES,"UNSUPPORTED_POLICY")
        for k in ("primaryFeeBps","resaleFeeBps","resaleOrganizerBps"):
            require(type(p[k]) is int and 0<=p[k]<=10000,"INVALID_BPS")
        require(p["resaleFeeBps"]+p["resaleOrganizerBps"]<=10000,"INVALID_SPLIT")
        seats=b["seats"]
        require(isinstance(seats,list) and 0<len(seats)<=300 and all(isinstance(x,str) for x in seats),"INVALID_SEATS")
        require(len(set(seats))==len(seats),"DUPLICATE_SEAT")
        quota=nonnegative(b.get("invitationQuota",0)); require(quota<=len(seats),"INVITATION_QUOTA_EXCEEDS_INVENTORY")
        admission=b.get("admissionStatus","OPEN"); require(admission in ("OPEN","CLOSED"),"INVALID_ADMISSION_STATUS")
        self.s["events"][eid]=dict(status="OPEN",salesStatus="OPEN",admissionStatus=admission,
            organizer=ident(b["organizer"]),policy=p,policyHash=digest(p),pool=digest([eid,self.SCOPE]),
            invitationQuota=quota,invitationsIssued=0)
        for seat in seats:
            ident(seat); iid=eid+"/"+seat; ident(iid)
            self.s["inventory"][iid]=dict(event=eid,seat=seat,generation=0,version=0,currentRight=None)
        return {"eventId":eid,"policyHash":digest(p),"inventoryIds":[eid+"/"+x for x in seats]}

    def new_right(self,iid,expected):
        require(iid in self.s["inventory"],"INVENTORY_NOT_FOUND")
        u=self.s["inventory"][iid]
        require(type(expected) is int and expected==u["version"],"STALE_INVENTORY_VERSION")
        require(u["currentRight"] is None,"INVENTORY_NOT_RELEASED")
        u["generation"]+=1; u["version"]+=1
        rid="right-"+digest([self.DOMAIN,iid,u["generation"]])
        require(rid not in self.s["tickets"],"RIGHT_ID_REUSE")
        self.s["tickets"][rid]=dict(event=u["event"],seat=u["seat"],inventoryId=iid,generation=u["generation"],
            state="AVAILABLE",owner=None,rightsVersion=0,admissionEpoch=0,lock=None,trades=[],session=None,used=False,
            issuanceKind="PURCHASE")
        u["currentRight"]=rid
        return rid

    def _prepare_trade(self,b):
        tid=ident(b["tradeId"]); require(tid not in self.s["trades"],"TRADE_EXISTS")
        if "inventoryId" in b:
            require("ticketId" not in b,"AMBIGUOUS_RIGHT_REFERENCE")
            rid=self.new_right(b["inventoryId"],b["expectedInventoryVersion"])
        else: rid=b["ticketId"]
        t=self.ticket(rid); e=self.event(t["event"])
        require(e["status"]=="OPEN" and t["lock"] is None,"EVENT_CLOSED_OR_TICKET_LOCKED")
        require(e["salesStatus"]=="OPEN","SALES_CLOSED")
        require(type(b["expectedVersion"]) is int and t["rightsVersion"]==b["expectedVersion"],"STALE_RIGHTS_VERSION")
        require(t["state"] in ("AVAILABLE","ACTIVE"),"RIGHT_NOT_TRANSFERABLE")
        buyer=ident(b["buyer"]); price=positive(b["amount"]); primary=t["state"]=="AVAILABLE"
        listing=None
        if primary:
            self.role(buyer); require(price==e["policy"]["primaryPrice"],"PRIMARY_PRICE_MISMATCH")
        else:
            if b.get("listingId"):
                listing=self.s["listings"].get(b["listingId"])
                require(listing and listing["state"]=="LISTED" and listing["ticketId"]==rid
                        and listing["seller"]==t["owner"] and listing["version"]==t["rightsVersion"]
                        and listing["amount"]==price and self.s["clock"]<listing["expiresAt"],"LISTING_NOT_AVAILABLE")
                require(b.get("listingHash")==listing["termsHash"],"LISTING_TERMS_MISMATCH")
                self.role(buyer)
            else: self.role(t["owner"])
            require(e["policy"]["resaleAllowed"] and buyer!=t["owner"] and price<=e["policy"]["resaleCap"],"RESALE_POLICY_REJECTED")
        expiry=b.get("expiresAt",self.s["clock"]+900)
        require(type(expiry) is int and self.s["clock"]<expiry<=self.s["clock"]+86400,"INVALID_RESERVATION_EXPIRY")
        if listing: require(expiry<=listing["expiresAt"],"RESERVATION_EXCEEDS_LISTING")
        r=dict(id=tid,ticket=rid,event=t["event"],kind="PRIMARY" if primary else "RESALE",seller=t["owner"],buyer=buyer,
            amount=price,currency="KRW",policyHash=e["policyHash"],expectedVersion=t["rightsVersion"],
            expectedAdmissionEpoch=t["admissionEpoch"],accepted=primary or listing is not None,status="PREPARED",captured=False,
            paymentId=None,settled=0,settlementGross=0,allocations=[],allocationVersion=0,refundDue=0,refunded=0,
            originalCancelled=0,reversalRequested=False,reversalPlanned=False,pool=digest([e["pool"],tid]),
            expiresAt=expiry,listingId=b.get("listingId"))
        r["termsHash"]=digest(dict(domain=self.DOMAIN,scope=self.SCOPE,terms={k:r[k] for k in (
            "id","event","kind","ticket","buyer","seller","amount","currency","policyHash","expectedVersion","expectedAdmissionEpoch","expiresAt")}))
        # Full digest encoded without truncation. Length is 47 ASCII characters.
        import base64
        r["externalOrderId"]="kix_"+base64.urlsafe_b64encode(bytes.fromhex(digest([self.DOMAIN,self.SCOPE,tid]))).decode().rstrip("=")
        require(all(v["externalOrderId"]!=r["externalOrderId"] for v in self.s["trades"].values()),"EXTERNAL_ORDER_COLLISION")
        self.s["trades"][tid]=r; t["lock"]=tid; t["trades"].append(tid)
        if listing: listing["state"]="RESERVED"; listing["tradeId"]=tid
        return {"tradeId":tid,"ticketId":rid,"externalOrderId":r["externalOrderId"],"status":"PREPARED","termsHash":r["termsHash"]}

    def terminate_ticket(self,t,reason):
        t["state"]="CANCEL_PENDING_CLOSE" if t["session"] else "VOID"
        t["rightsVersion"]+=1
        if not t["session"]: t["admissionEpoch"]+=1
        t["lock"]=None
        profile=self.event(t["event"])["policy"]["refundProfile"]
        committed=[tid for tid in t["trades"] if self.trade(tid)["status"]=="COMMITTED"]
        targets=set(committed if profile=="FULL_CHAIN_UNWIND_FIXTURE" or reason=="EVENT_CANCELLED" else committed[-1:])
        for tid in t["trades"]:
            r=self.trade(tid)
            if r["status"]=="PREPARED": r["status"]="VOID"; targets.add(tid)
            if tid in targets: self.reverse(tid,reason)

    def _release_inventory(self,b):
        self.role("operator")
        u=self.s["inventory"].get(b["inventoryId"]); require(u is not None,"INVENTORY_NOT_FOUND")
        require(type(b["expectedInventoryVersion"]) is int and b["expectedInventoryVersion"]==u["version"],"STALE_INVENTORY_VERSION")
        require(u["currentRight"]==b["closedRightId"],"CURRENT_ISSUANCE_MISMATCH")
        t=self.ticket(b["closedRightId"])
        # No provider timeout or unknown delegated gate use can satisfy closure.
        require(t["state"]=="VOID" and not t["session"] and not t["used"] and not t["lock"],"RIGHT_NOT_SAFELY_CLOSED")
        require(all(self.trade(tid)["status"]!="PREPARED" for tid in t["trades"]),"LATE_EXECUTION_NOT_FENCED")
        require(self.event(u["event"])["status"]=="OPEN" and self.event(u["event"])["salesStatus"]=="OPEN","INVENTORY_EVENT_CLOSED")
        u["currentRight"]=None; u["version"]+=1
        return {"inventoryId":b["inventoryId"],"inventoryVersion":u["version"],"closedRightId":b["closedRightId"]}

    def _void_unissued(self,b):
        t=self.ticket(b["ticketId"]); self.role("operator")
        require(t["state"]=="AVAILABLE" and not t["lock"] and t["owner"] is None,"RIGHT_ALREADY_ISSUED")
        require(all(self.trade(tid)["status"]=="VOID" for tid in t["trades"]),"LATE_EXECUTION_NOT_FENCED")
        t["state"]="VOID"; t["rightsVersion"]+=1; t["admissionEpoch"]+=1
        return {"rightsState":"VOID"}

    def _create_listing(self,b):
        lid=ident(b["listingId"]); require(lid not in self.s["listings"],"LISTING_EXISTS")
        t=self.ticket(b["ticketId"]); e=self.event(t["event"]); self.role(t["owner"])
        require(e["status"]=="OPEN" and e["salesStatus"]=="OPEN" and t["state"]=="ACTIVE" and not t["lock"],"RIGHT_NOT_LISTABLE")
        require(b["expectedVersion"]==t["rightsVersion"],"STALE_RIGHTS_VERSION")
        n=positive(b["amount"]); require(e["policy"]["resaleAllowed"] and n<=e["policy"]["resaleCap"],"RESALE_POLICY_REJECTED")
        expiry=b["expiresAt"]; require(type(expiry) is int and self.s["clock"]<expiry<=self.s["clock"]+86400,"INVALID_LISTING_EXPIRY")
        listing=dict(ticketId=b["ticketId"],seller=t["owner"],version=t["rightsVersion"],amount=n,
                     policyHash=e["policyHash"],expiresAt=expiry,state="LISTED")
        listing["termsHash"]=digest([self.DOMAIN,lid,listing]); self.s["listings"][lid]=listing
        return {"listingId":lid,"termsHash":listing["termsHash"],"rightLocked":False}

    def _reserve_listing(self,b):
        listing=self.s["listings"].get(b["listingId"]); require(listing is not None,"LISTING_NOT_FOUND")
        return self._prepare_trade(dict(tradeId=b["tradeId"],ticketId=listing["ticketId"],buyer=self.actor,
            amount=listing["amount"],expectedVersion=listing["version"],listingId=b["listingId"],
            listingHash=b["listingHash"],expiresAt=b["expiresAt"]))

    def _cancel_listing(self,b):
        listing=self.s["listings"].get(b["listingId"]); require(listing is not None,"LISTING_NOT_FOUND")
        self.role(listing["seller"]); require(listing["state"]=="LISTED","LISTING_NOT_CANCELLABLE")
        listing["state"]="CANCELLED"; return {"listingState":"CANCELLED"}

    def _advance_clock(self,b):
        self.role("operator"); now=b["now"]
        require(type(now) is int and self.s["clock"]<=now<=10**12,"INVALID_FIXTURE_CLOCK")
        self.s["clock"]=now; return {"logicalTime":now}

    def _expire_trade(self,b):
        self.role("operator"); r=self.trade(b["tradeId"])
        require(r["status"]=="PREPARED" and self.s["clock"]>=r["expiresAt"],"RESERVATION_NOT_EXPIRED")
        r["status"]="VOID"; t=self.ticket(r["ticket"])
        require(t["lock"]==b["tradeId"],"LOCK_MISMATCH"); t["lock"]=None
        self.reverse(b["tradeId"],"DELIVERY_FAILED")
        return {"status":"VOID","lateCommitFenced":True}

    def _offer_gift(self,b):
        gid=ident(b["giftId"]); require(gid not in self.s["gifts"],"GIFT_EXISTS")
        t=self.ticket(b["ticketId"]); self.role(t["owner"])
        require(t["state"]=="ACTIVE" and not t["lock"] and self.event(t["event"])["status"]=="OPEN","RIGHT_NOT_GIFTABLE")
        require(type(b["expectedVersion"]) is int and b["expectedVersion"]==t["rightsVersion"],"STALE_RIGHTS_VERSION")
        recipient=ident(b["recipient"]); require(recipient!=self.actor,"SAME_GIFT_RECIPIENT")
        expiry=b["expiresAt"]; require(type(expiry) is int and self.s["clock"]<expiry<=self.s["clock"]+86400,"INVALID_GIFT_EXPIRY")
        gift=dict(ticketId=b["ticketId"],donor=self.actor,recipient=recipient,version=t["rightsVersion"],expiresAt=expiry,state="OFFERED",
                  policyHash=self.event(t["event"])["policyHash"],refundBeneficiaryMode="ORIGINAL_PAYMENT_BUYER")
        gift["termsHash"]=digest([self.DOMAIN,gid,gift]); self.s["gifts"][gid]=gift
        return {"giftId":gid,"termsHash":gift["termsHash"]}

    def _accept_gift(self,b):
        gift=self.s["gifts"].get(b["giftId"]); require(gift is not None,"GIFT_NOT_FOUND")
        self.role(gift["recipient"]); t=self.ticket(gift["ticketId"])
        require(gift["state"]=="OFFERED" and self.s["clock"]<gift["expiresAt"] and b["termsHash"]==gift["termsHash"],"GIFT_NOT_ACCEPTABLE")
        require(t["state"]=="ACTIVE" and not t["lock"] and t["owner"]==gift["donor"] and t["rightsVersion"]==gift["version"]
                and self.event(t["event"])["status"]=="OPEN","GIFT_RIGHT_CONFLICT")
        t["owner"]=gift["recipient"]; t["rightsVersion"]+=1; t["admissionEpoch"]+=1; gift["state"]="ACCEPTED"
        return {"ticketId":gift["ticketId"],"owner":t["owner"],"rightsVersion":t["rightsVersion"],"financialEntries":0}

    def _cancel_gift(self,b):
        gift=self.s["gifts"].get(b["giftId"]); require(gift is not None,"GIFT_NOT_FOUND")
        self.role(gift["donor"]); require(gift["state"]=="OFFERED","GIFT_NOT_CANCELLABLE")
        gift["state"]="CANCELLED"; return {"giftState":"CANCELLED"}

    def _issue_invitation(self,b):
        u=self.s["inventory"].get(b["inventoryId"]); require(u is not None,"INVENTORY_NOT_FOUND")
        e=self.event(u["event"]); self.role(e["organizer"])
        require(e["status"]=="OPEN" and e["salesStatus"]=="OPEN","EVENT_NOT_OPEN")
        require(e["invitationsIssued"]<e["invitationQuota"],"INVITATION_QUOTA_EXCEEDED")
        rid=self.new_right(b["inventoryId"],b["expectedInventoryVersion"]); t=self.ticket(rid)
        t["owner"]=ident(b["recipient"]); t["state"]="ACTIVE"; t["rightsVersion"]=1; t["admissionEpoch"]=1; t["issuanceKind"]="INVITATION"
        e["invitationsIssued"]+=1
        return {"ticketId":rid,"financialEntries":0,"invitationsIssued":e["invitationsIssued"]}

    def _close_sales(self,b):
        e=self.event(b["eventId"]); self.role("operator",e["organizer"])
        require(e["status"]=="OPEN","EVENT_NOT_OPEN"); e["salesStatus"]="CLOSED"
        for tid,r in self.s["trades"].items():
            if r["event"]==b["eventId"] and r["status"]=="PREPARED":
                r["status"]="VOID"; self.ticket(r["ticket"])["lock"]=None; self.reverse(tid)
        return {"salesStatus":"CLOSED"}

    def _open_admission(self,b):
        e=self.event(b["eventId"]); self.role("operator",e["organizer"])
        require(e["status"]=="OPEN","EVENT_NOT_OPEN"); e["admissionStatus"]="OPEN"
        return {"admissionStatus":"OPEN"}

    def invalidate_offers(self):
        for listing in self.s["listings"].values():
            t=self.ticket(listing["ticketId"]); e=self.event(t["event"])
            if listing["state"]=="LISTED" and (t["state"]!="ACTIVE" or t["owner"]!=listing["seller"]
                or t["rightsVersion"]!=listing["version"] or self.s["clock"]>=listing["expiresAt"] or e["status"]!="OPEN" or e["salesStatus"]!="OPEN"):
                listing["state"]="INVALIDATED"
            if listing["state"]=="RESERVED" and self.trade(listing["tradeId"])["status"]!="PREPARED":
                listing["state"]="CLOSED"
        for gift in self.s["gifts"].values():
            t=self.ticket(gift["ticketId"])
            if gift["state"]=="OFFERED" and (t["state"]!="ACTIVE" or t["owner"]!=gift["donor"] or t["rightsVersion"]!=gift["version"]
                or self.s["clock"]>=gift["expiresAt"] or self.event(t["event"])["status"]!="OPEN"):
                gift["state"]="INVALIDATED"

    @staticmethod
    def consent_key(subject,b):
        return canonical([subject,b["eventId"],b["business"],b["channel"],b["purpose"]])

    def _set_consent(self,b):
        self.event(b["eventId"])
        require(b["purpose"]=="next_event_marketing" and type(b["allowed"]) is bool
                and b["business"]=="KIX" and b["channel"] in ("email","sms"),"INVALID_CONSENT")
        key=self.consent_key(self.actor,b); prior=self.s["consents"].get(key,{"version":0})
        require(type(b["expectedConsentVersion"]) is int and b["expectedConsentVersion"]==prior["version"],"STALE_CONSENT_VERSION")
        c=dict(subject=self.actor,event=b["eventId"],purpose=b["purpose"],business=b["business"],channel=b["channel"],
               allowed=b["allowed"],version=prior["version"]+1,operationId=self.op,recordedAt=self.s["clock"])
        self.s["consents"][key]=c
        return {"consentVersion":c["version"],"allowed":c["allowed"]}

    def _authorize_marketing(self,b):
        self.role("marketing-adapter"); self.event(b["eventId"])
        c=self.s["consents"].get(self.consent_key(b["subject"],b))
        require(c and c["allowed"] and type(b["expectedConsentVersion"]) is int and c["version"]==b["expectedConsentVersion"],"CONSENT_NOT_CURRENT")
        return {"dispatchDecision":"AUTHORIZED_FIXTURE_INTENT","consentVersion":c["version"],"authorizedAt":self.s["clock"],"networkSendPerformed":False}

    def marketing_view(self,actor,event_id,s):
        require(actor=="marketing-adapter","UNAUTHORIZED_VIEW")
        return [dict(subject=c["subject"],consentVersion=c["version"],purpose=c["purpose"],business=c["business"],channel=c["channel"],
                admissionRecorded=any(t["event"]==event_id and t["owner"]==c["subject"] and t["used"] for t in s["tickets"].values()))
                for c in s["consents"].values() if c["event"]==event_id and c["allowed"]]
