"""Offline reference reconciliation for ticket refunds. Python 3.10+, stdlib.

Consumes exported provider files; makes no payment, refund or blockchain calls.
All matches mean 'consistent with imported records', not authenticated truth.
See README.md for supported profiles and intentional review boundaries.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import quote


class InvalidInput(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes)
                          else canonical(value).encode()).hexdigest()


def required(obj, key):
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip():
        raise InvalidInput(f"nonempty string required: {key}")
    return v  # Identifiers are never converted to floats or silently trimmed.


def integer(v):
    if type(v) is not int or v < 0:
        raise InvalidInput("nonnegative integer minor amount required")
    return v


def minor(text, currency):
    """Explicit limited currency profile; no implicit rounding or float maths."""
    exponents = {"EUR": 2, "USD": 2, "GBP": 2, "KRW": 0, "JPY": 0}
    if currency not in exponents:
        raise InvalidInput(f"unsupported currency profile: {currency}")
    try:
        n = Decimal(str(text)) * 10 ** exponents[currency]
    except InvalidOperation as e:
        raise InvalidInput("invalid decimal amount") from e
    if not n.is_finite() or n < 0 or n != n.to_integral_value():
        raise InvalidInput("invalid precision or negative amount")
    return int(n)


SCOPE_KEYS = ("provider", "environment", "merchant", "channel")


def scope_key(s):
    values = tuple(required(s, k) for k in SCOPE_KEYS)
    if s["environment"] not in {"test", "live", "sample"}:
        raise InvalidInput("environment must be test, live, or sample")
    return values


def refund_key(r):
    return (*scope_key(r["scope"]), r["payment_id"], r["refund_id"])


def payment_key(r):
    return (*scope_key(r["scope"]), r["payment_id"])


def suspicious_id(s):
    return not isinstance(s, str) or not s or s != s.strip() or bool(re.fullmatch(
        r"[+-]?\d+(?:\.\d+)?[eE][+-]?\d+", s))


def usable_reference(s):
    return bool(s and s.strip() and s not in {"<auto>", "<empty>"}
                and not s.startswith("YOUR_"))


def tagged_reference(reason):
    # This opt-in convention is OUR design, not a provider API guarantee.
    refs = re.findall(r"\[TIXREF:([A-Za-z0-9_-]{1,64})\]", reason or "")
    if len(refs) > 1:
        raise InvalidInput("multiple TIXREF tags in cancellation reason")
    return refs[0] if refs else None


def prepare_request(intent, reason="고객 요청", include_line_items=False):
    """Build an UNSENT request using existing provider APIs; contains no keys.

    A registered intent and original order/rights checks are prerequisites for
    a future execution service. This function grants no permission to execute.
    """
    s, provider = intent["scope"], intent["scope"]["provider"]
    scope_key(s)
    payment = quote(required(intent, "payment_id"), safe="")
    ref = required(intent, "reference")
    amount = integer(intent["amount_minor"])
    request = dict(method="POST", scope=s, intent_id=intent["id"], sent=False, headers={})
    if provider in {"toss", "portone"}:
        if intent["currency"] != "KRW" or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", ref):
            raise InvalidInput("KRW and tag-compatible reference required")
        tagged = f"{reason} [TIXREF:{ref}]"
        if len(tagged) > 200:
            raise InvalidInput("reason plus reference exceeds local 200-character profile")
        if provider == "toss":
            request.update(path=f"/v1/payments/{payment}/cancel",
                           body=dict(cancelAmount=amount, cancelReason=tagged))
            request["headers"]["Idempotency-Key"] = digest(intent)
        else:
            request.update(path=f"/payments/{payment}/cancel",
                           body=dict(storeId=s["merchant"], amount=amount, reason=tagged),
                           retry_profile="NOT_CONFIGURED")
    elif provider == "adyen":
        if len(ref) > 80:
            raise InvalidInput("Adyen reference exceeds 80 characters")
        request.update(path=f"/v72/payments/{payment}/refunds", body=dict(
            merchantAccount=s["merchant"], reference=ref,
            amount=dict(currency=intent["currency"], value=amount)))
        request["headers"]["Idempotency-Key"] = digest(intent)
        if include_line_items:
            request["body"]["lineItems"] = [dict(id=p["ticket_id"], quantity=1,
                amountIncludingTax=p["amount_minor"]) for p in intent["allocations"]]
    else:
        raise InvalidInput("request profile not implemented")
    return request


class Store:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("""CREATE TABLE IF NOT EXISTS records(
            kind TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(kind,id))""")

    def put(self, kind, key, payload):
        encoded = canonical(payload)
        old = self.db.execute("SELECT payload FROM records WHERE kind=? AND id=?",
                              (kind, key)).fetchone()
        if old:
            if old[0] != encoded:
                raise InvalidInput(f"immutable record conflict: {kind}/{key}")
            return False
        self.db.execute("INSERT INTO records VALUES(?,?,?)", (kind, key, encoded))
        return True

    def all(self, kind):
        return [json.loads(r[0]) for r in self.db.execute(
            "SELECT payload FROM records WHERE kind=? ORDER BY id", (kind,))]

    def add_intent(self, intent):
        required(intent, "id")
        required(intent, "reference")
        scope_key(intent["scope"])
        required(intent, "payment_id")
        required(intent, "currency")
        required(intent, "recorded_at")
        expected = integer(intent["amount_minor"])
        parts = intent.get("allocations")
        if not isinstance(parts, list) or not parts or expected == 0:
            raise InvalidInput("positive refund and ticket allocations required")
        seen = set()
        for part in parts:
            identity = (required(part, "ticket_id"), integer(part["rights_version"]))
            if identity in seen:
                raise InvalidInput("duplicate ticket allocation")
            seen.add(identity)
            integer(part["amount_minor"])
        if sum(p["amount_minor"] for p in parts) != expected:
            raise InvalidInput("allocation sum differs from intended refund")
        for old in self.all("intent"):
            if (old["id"] != intent["id"] and scope_key(old["scope"]) == scope_key(intent["scope"])
                    and old["reference"] == intent["reference"]):
                raise InvalidInput("reference reused within provider scope")
        self.put("intent", intent["id"], intent)

    def add_binding(self, binding):
        for key in ("id", "intent_id", "payment_id", "refund_id", "evidence_ref", "recorded_at"):
            required(binding, key)
        scope_key(binding["scope"])
        if binding.get("method") not in {"request_response_log", "operator_record"}:
            raise InvalidInput("unsupported binding method")
        if suspicious_id(binding["refund_id"]) or suspicious_id(binding["payment_id"]):
            raise InvalidInput("unsafe identifier in explicit binding")
        self.put("binding", binding["id"], binding)

    def ingest(self, adapter, data, scope, context=None, provenance="unverified_export"):
        scope_key(scope)
        context = context or {}
        if provenance not in {"official_sample", "synthetic", "unverified_export"}:
            raise InvalidInput("unsupported provenance class")
        raw = data.encode() if isinstance(data, str) else data
        batch = digest({"adapter": adapter, "scope": scope, "context": context,
                        "sha256": digest(raw), "provenance": provenance})
        if any(b["id"] == batch for b in self.all("batch")):
            return batch
        records = normalize(adapter, raw, scope, context)
        with self.db:
            self.put("batch", batch, {"id": batch, "adapter": adapter,
                "scope": scope, "sha256": digest(raw), "provenance": provenance,
                "rows": len(records), "source_authentication": "not_performed"})
            for i, r in enumerate(records):
                r.update({"batch": batch, "row_number": i + 1,
                          "provenance": provenance, "adapter": adapter})
                self.put("observation", f"{batch}:{i}", r)
        return batch


def fact(scope, payment, refund, currency, amount, kind, status,
         reference=None, issues=None, **extras):
    r = dict(scope=scope, payment_id=payment, refund_id=refund,
             currency=currency, amount_minor=amount, kind=kind, status=status,
             reference=reference if usable_reference(reference) else None,
             issues=list(issues or []), **extras)
    if kind in {"REFUND", "BOOKING", "EXCEPTION"}:
        if suspicious_id(payment) or suspicious_id(refund):
            r["issues"].append("IDENTIFIER_NOT_EXACT")
    return r


def verify_scope(scope, provider, merchant):
    if scope["provider"] != provider or scope["merchant"] != merchant:
        raise InvalidInput("provider/merchant differs from declared import scope")


def normalize(adapter, raw, scope, context):
    if adapter == "adyen_settlement_csv":
        return adyen_csv(raw, scope)
    obj = json.loads(raw.decode("utf-8-sig"))
    out = []
    if adapter == "toss_payment":
        verify_scope(scope, "toss", required(obj, "mId"))
        if obj["currency"] != "KRW":
            raise InvalidInput("Toss v0.1 profile supports KRW only")
        for c in obj.get("cancels") or []:
            status = "PG_CANCELLED" if c.get("cancelStatus") == "DONE" else "UNKNOWN"
            ref = tagged_reference(c.get("cancelReason")) if context.get("parse_reason_tag") else None
            out.append(fact(scope, required(obj, "paymentKey"), required(c, "transactionKey"),
                "KRW", integer(c["cancelAmount"]), "REFUND", status, ref,
                issues=["STATUS_UNRECOGNIZED"] if status == "UNKNOWN" else [],
                reference_method="reason_tag" if ref else None,
                event_time=c.get("canceledAt")))
        # lastTransactionKey and array position are intentionally never used.
    elif adapter == "toss_settlement":
        for row in obj if isinstance(obj, list) else [obj]:
            verify_scope(scope, "toss", required(row, "mId"))
            if row["currency"] != "KRW":
                raise InvalidInput("Toss v0.1 profile supports KRW only")
            out.append(fact(scope, required(row, "paymentKey"), required(row, "transactionKey"),
                "KRW", integer(row["amount"]), "BOOKING", "SETTLEMENT_RECORD",
                # A settlement row alone does not classify approval vs cancellation.
                booking_type="TOSS_UNCLASSIFIED", net_raw=row.get("payOutAmount"),
                event_time=row.get("approvedAt")))
    elif adapter == "portone_cancel":
        verify_scope(scope, "portone", required(context, "store_id"))
        if context.get("currency") != "KRW":
            raise InvalidInput("PortOne v0.1 profile supports KRW only")
        c = obj["cancellation"]
        status = {"SUCCEEDED": "PG_CANCELLED", "REQUESTED": "RECEIVED", "FAILED": "FAILED"}.get(c.get("status"), "UNKNOWN")
        ref = tagged_reference(c.get("reason")) if context.get("parse_reason_tag") else None
        issues = ["STATUS_UNRECOGNIZED"] if status == "UNKNOWN" else []
        out.append(fact(scope, required(context, "payment_id"), required(c, "id"),
            "KRW", integer(c["totalAmount"]), "REFUND", status, ref, issues,
            pg_cancellation_id=c.get("pgCancellationId"), trigger=c.get("trigger"),
            reference_method="reason_tag" if ref else None,
            event_time=c.get("cancelledAt") or c.get("requestedAt")))
    elif adapter == "adyen_refund_response":
        verify_scope(scope, "adyen", required(obj, "merchantAccount"))
        status = "RECEIVED" if obj.get("status") == "received" else "UNKNOWN"
        out.append(fact(scope, required(obj, "paymentPspReference"), required(obj, "pspReference"),
            required(obj["amount"], "currency"), integer(obj["amount"]["value"]),
            "REFUND", status, obj.get("reference"),
            issues=["STATUS_UNRECOGNIZED"] if status == "UNKNOWN" else [],
            reference_method="refund_reference",
            line_items=[{k: item.get(k) for k in ("id", "quantity", "amountIncludingTax")}
                        for item in obj.get("lineItems", [])],
            line_items_are_ticket_ids=context.get("line_items_are_ticket_ids", False)))
    elif adapter == "adyen_webhook":
        expected_live = "true" if scope["environment"] == "live" else "false"
        if obj.get("live") != expected_live:
            raise InvalidInput("webhook environment differs from declared scope")
        for wrapper in obj["notificationItems"]:
            w = wrapper["NotificationRequestItem"]
            verify_scope(scope, "adyen", required(w, "merchantAccountCode"))
            code, success = w.get("eventCode"), w.get("success")
            if success not in {"true", "false"}:
                raise InvalidInput("Adyen success must be the documented string value")
            if code == "REFUND":
                kind, status = "REFUND", "SUBMITTED" if success == "true" else "FAILED"
            elif code in {"REFUND_FAILED", "REFUNDED_REVERSED"}:
                # Keep payment-level exception scope; do not infer a different
                # refund's identity from amount, order reference or arrival order.
                kind, status = "EXCEPTION", code
            else:
                out.append(dict(scope=scope, kind="OTHER", status=code,
                                issues=["EVENT_NOT_HANDLED"]))
                continue
            out.append(fact(scope, w.get("originalReference", ""), required(w, "pspReference"),
                required(w["amount"], "currency"), integer(w["amount"]["value"]), kind, status,
                event_time=w.get("eventDate")))
            # merchantReference identifies the payment in the published schema;
            # it is NOT treated as our refund-intent reference.
    else:
        raise InvalidInput(f"unknown adapter: {adapter}")
    return out


def adyen_csv(raw, scope):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    needed = {"Merchant Account", "Psp Reference", "Type", "Modification Reference",
              "Gross Currency", "Gross Debit (GC)", "Gross Credit (GC)"}
    if not needed <= set(reader.fieldnames or []):
        raise InvalidInput("missing required Adyen CSV headers")
    out = []
    for row in reader:
        if None in row:
            out.append(dict(scope=scope, kind="OTHER", status="MALFORMED_CSV_ROW",
                            issues=["CSV_ROW_WIDTH"]))
            continue
        if all(v in {None, ""} for v in row.values() if not isinstance(v, list)):
            continue
        typ = row.get("Type", "")
        if not typ:
            out.append(dict(scope=scope, kind="OTHER", status="UNCLASSIFIED_ROW",
                            issues=["ROW_TYPE_MISSING"]))
            continue
        verify_scope(scope, "adyen", required(row, "Merchant Account"))
        if typ not in {"Refunded", "RefundedReversed", "Chargeback", "ChargebackReversed", "SecondChargeback"}:
            out.append(dict(scope=scope, kind="OTHER", status=typ, issues=[]))
            continue
        currency = row.get("Gross Currency", "")
        amount_field = "Gross Credit (GC)" if typ in {"RefundedReversed", "ChargebackReversed"} else "Gross Debit (GC)"
        issues = []
        try:
            amount = minor(row.get(amount_field), currency)
        except InvalidInput:
            amount = None
            issues.append("AMOUNT_PARSE_REVIEW")
        out.append(fact(scope, row.get("Psp Reference", ""), row.get("Modification Reference", ""),
            currency, amount, "BOOKING" if typ == "Refunded" else "EXCEPTION", typ,
            row.get("Modification Merchant Reference"), issues,
            booking_type=typ, batch_number=row.get("Batch Number"),
            net_currency=row.get("Net Currency"), net_debit_raw=row.get("Net Debit (NC)"),
            net_credit_raw=row.get("Net Credit (NC)"), event_time=row.get("Booking Date") or row.get("Creation Date"),
            placeholder_reference=row.get("Modification Merchant Reference") == "<auto>"))
    return out


def reconcile(store):
    intents = {i["id"]: i for i in store.all("intent")}
    bindings = store.all("binding")
    observations = store.all("observation")
    groups, quarantined, exceptions = defaultdict(list), [], []
    for r in observations:
        if r["kind"] == "OTHER":
            continue
        if r["kind"] == "EXCEPTION":
            exceptions.append(r)
        if r["issues"]:
            quarantined.append(r)
            continue
        if r["kind"] != "EXCEPTION":
            groups[refund_key(r)].append(r)
    results = []
    for key, rows in sorted(groups.items()):
        facts = [r for r in rows if r["kind"] == "REFUND"]
        books = [r for r in rows if r["kind"] == "BOOKING"]
        # Toss's settlement transaction may be an approval. Without a cancellation
        # observation we leave it unclassified rather than creating a fake refund.
        if not facts and all(r.get("booking_type") == "TOSS_UNCLASSIFIED" for r in books):
            continue
        issues, candidates, methods = set(), set(), set()
        refs = {r["reference"] for r in rows if r.get("reference")}
        if len(refs) > 1:
            issues.add("REFERENCE_CONFLICT")
        for i in intents.values():
            if (scope_key(i["scope"]) == key[:4] and i["payment_id"] == key[4]
                    and i["reference"] in refs):
                candidates.add(i["id"])
                methods.add("merchant_reference")
        for b in bindings:
            if (*scope_key(b["scope"]), b["payment_id"], b["refund_id"]) == key:
                if b["intent_id"] not in intents:
                    issues.add("BINDING_INTENT_MISSING")
                    continue
                i = intents[b["intent_id"]]
                if scope_key(i["scope"]) != key[:4] or i["payment_id"] != key[4]:
                    issues.add("BINDING_SCOPE_MISMATCH")
                else:
                    candidates.add(i["id"])
                    methods.add(b["method"])
        identity_rows = facts or books
        amounts = {r["amount_minor"] for r in identity_rows}
        currencies = {r["currency"] for r in rows}
        if len(amounts) != 1 or len(currencies) != 1:
            issues.add("SOURCE_VALUE_CONFLICT")
        candidate = intents[next(iter(candidates))] if len(candidates) == 1 else None
        if len(candidates) > 1:
            issues.add("ATTRIBUTION_CONFLICT")
        if candidate:
            if refs and refs != {candidate["reference"]}:
                issues.add("REFERENCE_CONFLICT")
            if currencies != {candidate["currency"]} or amounts != {candidate["amount_minor"]}:
                issues.add("AMOUNT_OR_CURRENCY_REVIEW")
            expected_items = sorted((p["ticket_id"], p["amount_minor"])
                                    for p in candidate["allocations"])
            for row in facts:
                if not row.get("line_items"):
                    continue
                if not row.get("line_items_are_ticket_ids"):
                    issues.add("LINE_ITEMS_NOT_MAPPED")
                    continue
                actual_items = []
                for item in row["line_items"]:
                    if (item.get("quantity") != 1 or not isinstance(item.get("id"), str)
                            or type(item.get("amountIncludingTax")) is not int):
                        issues.add("LINE_ITEM_PROFILE_REVIEW")
                        break
                    actual_items.append((item["id"], item["amountIncludingTax"]))
                else:
                    if sorted(actual_items) != expected_items:
                        issues.add("LINE_ITEM_ALLOCATION_CONFLICT")
        for r in quarantined:
            if refund_key(r) == key:
                issues.add("RELATED_QUARANTINED_RECORD")
        if any(payment_key(r) == key[:5] for r in exceptions):
            issues.add("PAYMENT_EXCEPTION_REVIEW")
        if len(books) > 1:
            issues.add("MULTIPLE_BOOKING_ROWS_REVIEW")
        if books and facts and any(r["amount_minor"] not in amounts for r in books):
            issues.add("BOOKING_AMOUNT_REVIEW")
        states = {r["status"] for r in facts}
        if "FAILED" in states and "PG_CANCELLED" in states:
            issues.add("STATUS_CONFLICT")
        if "FAILED" in states:
            process = "FAILED_AS_RECORDED"
        elif "PG_CANCELLED" in states:
            process = "PG_CANCELLED_AS_RECORDED"
        elif "SUBMITTED" in states:
            process = "SUBMITTED_NOT_FINAL"
        elif states:
            process = "REQUEST_RECEIVED"
        else:
            process = "NO_API_OUTCOME"
        if books and "FAILED" in states:
            issues.add("OUTCOME_BOOKING_REVIEW")
        # A booking exception must not erase a known ticket attribution.
        operational_issues = {"PAYMENT_EXCEPTION_REVIEW", "MULTIPLE_BOOKING_ROWS_REVIEW",
            "BOOKING_AMOUNT_REVIEW", "STATUS_CONFLICT", "OUTCOME_BOOKING_REVIEW",
            "LINE_ITEMS_NOT_MAPPED"}
        attribution_issues = issues - operational_issues
        state = "REVIEW" if attribution_issues else "MATCHED_AS_RECORDED" if candidate else "UNBOUND"
        if "PAYMENT_EXCEPTION_REVIEW" in issues:
            process = "PAYMENT_EXCEPTION_REVIEW"
        results.append(dict(key=list(key), intent_id=candidate["id"] if candidate else None,
            attribution=state, process=process,
            booking="REVIEW" if any("BOOKING" in x for x in issues) else "RECORD_LINKED" if books else "NOT_OBSERVED",
            matching_methods=sorted(methods), issues=sorted(issues),
            financial_review_required=bool(issues) or not candidate,
            observations=len(rows), booking_rows=len(books),
            allocations=candidate["allocations"] if state == "MATCHED_AS_RECORDED" else [],
            provider_bridge="NOT_CONFIGURED" if key[0] == "portone" else "SAME_PROVIDER"))
    # A reference reused for two provider refund IDs is not safe auto-attribution.
    per_intent = defaultdict(list)
    for r in results:
        if r["intent_id"]:
            per_intent[r["intent_id"]].append(r)
    for group in per_intent.values():
        if len(group) > 1:
            for r in group:
                r["issues"] = sorted(set(r["issues"]) | {"INTENT_USED_BY_MULTIPLE_REFUNDS"})
                r["attribution"], r["allocations"] = "REVIEW", []
                r["financial_review_required"] = True
    return dict(schema_version=1, source_authentication="not_performed",
        collection_completeness="not_established", financial_authorization=False,
        summary={"import_batches": len(store.all("batch")), "observations": len(observations),
            "intents": len(intents), "refund_groups": len(results),
            "attribution_states": dict(Counter(r["attribution"] for r in results)),
            "quarantined_records": len(quarantined), "payment_exceptions": len(exceptions),
            "other_rows": dict(Counter(r["status"] for r in observations if r["kind"] == "OTHER"))},
        refunds=results, quarantined=quarantined, payment_exceptions=exceptions,
        unmatched_intent_ids=sorted(set(intents) - set(per_intent)),
        sources=store.all("batch"))


def run_manifest(path, db_path=":memory:"):
    path = Path(path)
    spec = json.loads(path.read_text())
    store = Store(db_path)
    try:
        with store.db:
            for filename in spec.get("intents", []):
                for intent in json.loads((path.parent / filename).read_text()):
                    store.add_intent(intent)
            for filename in spec.get("bindings", []):
                for binding in json.loads((path.parent / filename).read_text()):
                    store.add_binding(binding)
        for source in spec.get("sources", []):
            store.ingest(source["adapter"], (path.parent / source["path"]).read_bytes(),
                source["scope"], source.get("context"), source.get("provenance", "unverified_export"))
        return reconcile(store)
    finally:
        store.db.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True)
    p.add_argument("--db", default=":memory:")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        report = run_manifest(args.manifest, args.db)
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report["summary"], ensure_ascii=False))
    except (InvalidInput, KeyError, json.JSONDecodeError, OSError) as e:
        p.exit(2, f"Input rejected; no successful report produced: {e}\n")


if __name__ == "__main__":
    main()
