"""Executable strict command envelope contract. Domain-specific guards are in handlers."""
from common import require

# Required / optional fields. Unknown fields are rejected at the boundary.
COMMANDS={
 "create_event":("eventId organizer policy seats","invitationQuota admissionStatus issuerId sessionId reservationSeconds"),
 "prepare_trade":("tradeId buyer amount expectedVersion","ticketId inventoryId expectedInventoryVersion expiresAt listingId listingHash"),
 "accept_trade":("tradeId termsHash",""),
 "capture":("tradeId orderId paymentId amount currency buyer",""),
 "settle_capture":("tradeId paymentId amount currency grossAmount feeAmount taxAmount heldAmount adjustmentAmount feeBearer contractRef movementId","adjustmentReason sourceId"),
 "commit_trade":("tradeId",""),"abort_trade":("tradeId",""),
 "refund_ticket":("ticketId expectedVersion",""),"cancel_event":("eventId",""),"complete_event":("eventId",""),
 "admit":("ticketId holder expectedVersion admissionEpoch",""),
 "delegate":("ticketId expectedVersion",""),
 "close_delegation":("ticketId session admissionEpoch used provenance",""),
 "prepare_effect":("effectId tradeId kind amount routeProfile contractRef","allocationId beneficiaryAccountRef retryOf"),
 "claim_effect":("effectId workerId leaseSeconds",""),
 "dispatch_effect":("effectId workerId claimGeneration",""),
 "observe_dispatch_lookup":("effectId idempotencyKey requestHash result lookupRef observedAt","providerOperationId"),
 "finalize_effect":("effectId providerOperationId paymentId beneficiary amount unexecutedAmount currency sourceId fenceRef sourceCursor observedAt contractRef",""),
 "send_effect":("effectId",""),"abort_effect":("effectId",""),
 "observe_effect":("effectId phase sourceId providerOperationId amount currency beneficiary paymentId","movementId status fenceRef fenceProvenance"),
 "observe_recovery":("tradeId allocationId payer amount currency movementId","sourceId"),
 "adjust_pg_cancel":("tradeId paymentId amount currency contractRef basis movementId",""),
 "observe_return":("effectId paymentId payer amount currency movementId",""),
 "observe_funding":("tradeId payer amount currency contractRef movementId",""),
 "release_inventory":("inventoryId closedRightId expectedInventoryVersion",""),
 "void_unissued":("ticketId",""),
 "create_listing":("listingId ticketId expectedVersion amount expiresAt",""),
 "reserve_listing":("listingId listingHash tradeId expiresAt",""),
 "cancel_listing":("listingId",""),"expire_trade":("tradeId",""),"advance_clock":("now",""),
 "offer_gift":("giftId ticketId expectedVersion recipient expiresAt",""),
 "accept_gift":("giftId termsHash",""),"cancel_gift":("giftId",""),
 "issue_invitation":("inventoryId expectedInventoryVersion recipient",""),
 "close_sales":("eventId",""),"open_admission":("eventId",""),
 "set_consent":("eventId business channel purpose allowed expectedConsentVersion",""),
 "authorize_marketing":("eventId subject business channel purpose expectedConsentVersion",""),
}
SOURCE_ACTIONS={"capture","settle_capture","observe_effect","observe_recovery","adjust_pg_cancel","observe_return","observe_funding","finalize_effect","observe_dispatch_lookup"}
INTEGER_FIELDS=set("amount expectedVersion admissionEpoch grossAmount feeAmount taxAmount heldAmount adjustmentAmount expectedInventoryVersion expiresAt now invitationQuota expectedConsentVersion reservationSeconds leaseSeconds claimGeneration observedAt unexecutedAmount".split())
BOOLEAN_FIELDS={"used","allowed"}
NULLABLE_FIELDS={"allocationId","beneficiaryAccountRef","retryOf","status"}


def command_fields(action):
    req,opt=COMMANDS[action]; required=set(req.split())|{"domain"}
    if action in SOURCE_ACTIONS: required|={"scope","provenance"}
    return required,set(opt.split())


def validate_command(action,b):
    require(action in COMMANDS,"UNKNOWN_ACTION")
    require(isinstance(b,dict),"OBJECT_BODY_REQUIRED")
    req,opt=command_fields(action)
    require(req<=set(b),"MISSING_FIELDS:"+",".join(sorted(req-set(b))))
    require(set(b)<=req|opt,"UNKNOWN_FIELDS:"+",".join(sorted(set(b)-(req|opt))))
    for f,v in b.items():
        if f in NULLABLE_FIELDS and v is None: continue
        if f in INTEGER_FIELDS: require(type(v) is int and 0<=v<=10**12,"INVALID_INTEGER:"+f)
        elif f in BOOLEAN_FIELDS: require(type(v) is bool,"INVALID_BOOLEAN:"+f)
        elif f in ("scope","policy"): require(isinstance(v,dict),"INVALID_OBJECT:"+f)
        elif f=="seats": require(isinstance(v,list),"INVALID_ARRAY:seats")
        else: require(isinstance(v,str) and 0<len(v)<=300 and v.strip()==v,"INVALID_STRING:"+f)
    if action=="prepare_trade":
        require(("inventoryId" in b)!=("ticketId" in b),"EXACTLY_ONE_RIGHT_REFERENCE_REQUIRED")
        require("inventoryId" not in b or "expectedInventoryVersion" in b,"INVENTORY_VERSION_REQUIRED")
    if action=="observe_effect":
        require(b["phase"]!="FUNDS" or "movementId" in b,"MOVEMENT_ID_REQUIRED")
        require(b["phase"]!="FENCED_FAILURE" or {"fenceRef","fenceProvenance"}<=set(b),"FINAL_FAILURE_FENCE_REQUIRED")


def schema():
    result={"domain":"kix:fixture:lifecycle:0.3","unknownFields":"REJECT","sourceAuthentication":"FIXTURE_ONLY","commands":{}}
    for action in COMMANDS:
        req,opt=command_fields(action); props={}
        for field in sorted(req|opt):
            typ="integer" if field in INTEGER_FIELDS else "boolean" if field in BOOLEAN_FIELDS else "object" if field in ("scope","policy") else "array" if field=="seats" else "string"
            props[field]={"type":[typ,"null"] if field in NULLABLE_FIELDS else typ}
            if typ=="integer": props[field].update(minimum=0,maximum=10**12)
            if typ=="string": props[field].update(minLength=1,maxLength=300)
        result["commands"][action]={"type":"object","required":sorted(req),"properties":props,"additionalProperties":False}
    result["handlerConstraints"]="Positive monetary postings, enums, actor scopes, policy checks, current versions, balances and conditional bindings are additionally enforced in handlers. This exported catalog alone is not a full business validator."
    return result
