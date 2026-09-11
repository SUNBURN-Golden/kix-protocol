"""Contract checks against preserved earlier KIX models; no external calls."""
import json
from core import digest, require
from vendor import tix_reconcile as legacy


def refund_intent(core, effect_id):
    s=core.snapshot(); x=s["effects"][effect_id]; r=s["trades"][x["trade"]]
    require(x["kind"]=="REFUND", "NOT_A_REFUND")
    return dict(id=effect_id, reference="rf_"+digest([core.DOMAIN,effect_id])[:40],
        scope=core.SCOPE, payment_id=x["paymentId"],currency="KRW",amount_minor=x["amount"],
        recorded_at="2026-09-11T00:00:00Z",  # Explicit fixture timestamp.
        allocations=[dict(ticket_id=r["ticket"], rights_version=r["expectedVersion"]+(1 if r["allocations"] else 0),
                          amount_minor=x["amount"])])


def check_legacy_toss(core,effect_id,raw_payment):
    intent=refund_intent(core,effect_id)
    store=legacy.Store()
    try:
        store.add_intent(intent)
        store.ingest("toss_payment",json.dumps(raw_payment),core.SCOPE,
                     context={"parse_reason_tag":True},provenance="synthetic")
        return legacy.reconcile(store)
    finally:
        store.db.close()


def unsent_refund_request(core,effect_id):
    request=legacy.prepare_request(refund_intent(core,effect_id),reason="합성 시나리오 환불")
    # Preserve the coordinator's durable key through the legacy request builder.
    request["headers"]["Idempotency-Key"]=core.snapshot()["effects"][effect_id]["idempotencyKey"]
    return request
