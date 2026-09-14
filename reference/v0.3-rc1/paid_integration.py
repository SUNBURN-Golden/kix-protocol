"""First integration slice: existing public Sui right -> paid resale -> settlement.

Local trusted-process coordinator, NOT an authenticated API. Sui is the rights
authority; Core is an accounting projection; MockProvider is an independent
synthetic money authority. No arbitrary actor/source envelopes are exposed.
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from common import canonical, digest, ident, require
from core import Core
from mock_provider import MockProvider, SCOPE
from storage_receipt import StorageFault, coordinator_fingerprint

HERE = Path(__file__).resolve().parent


class Projection(Core):
    DOMAIN = "kix:integration:localnet:1"
    SCOPE = SCOPE

    def _commit_trade(self, b):
        row = self.db.execute("SELECT body FROM integration_final WHERE trade_id=?", (b["tradeId"],)).fetchone()
        require(row and json.loads(row[0])["state"] == "EXECUTED_SUCCESS", "VERIFIED_CHAIN_SUCCESS_REQUIRED")
        result = super()._commit_trade(b)
        chain = json.loads(row[0])["allocation"]
        expected = [int(chain[k]) for k in ("seller_due", "organizer_due", "platform_due")]
        actual = self.trade(b["tradeId"])["allocations"]
        require([a["amount"] for a in actual] == [n for n in expected if n], "CHAIN_LEDGER_ALLOCATION_MISMATCH")
        return result


class PaidCoordinator:
    def __init__(self, directory, endpoint="http://127.0.0.1:9000"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.endpoint = endpoint
        self._connect()

    def _connect(self):
        self.core = Projection(str(self.directory / "projection.sqlite"))
        self.provider = MockProvider(str(self.directory / "mock-provider.sqlite"))
        self.core.db.execute("CREATE TABLE IF NOT EXISTS integration_items (id TEXT PRIMARY KEY, hash TEXT, body TEXT)")
        self.core.db.execute("CREATE TABLE IF NOT EXISTS integration_final (trade_id TEXT PRIMARY KEY, body TEXT)")
        self.core.db.execute("CREATE TABLE IF NOT EXISTS integration_evidence (hash TEXT PRIMARY KEY, body TEXT)")
        self.core.db.execute("CREATE TABLE IF NOT EXISTS integration_shows (show_key TEXT PRIMARY KEY, trade_id TEXT UNIQUE)")

    def close(self):
        self.core.db.close()
        self.provider.db.close()

    def _save(self, key, body):
        self.core.db.execute("INSERT OR IGNORE INTO integration_items VALUES(?,?,?)", (key, digest(body), canonical(body)))
        require(self.core.db.execute("SELECT hash FROM integration_items WHERE id=?", (key,)).fetchone()[0] == digest(body), "IMMUTABLE_REQUEST_CONFLICT")
        return body

    def _get(self, key):
        row = self.core.db.execute("SELECT body FROM integration_items WHERE id=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _evidence(self, body):
        self.core.db.execute("INSERT OR IGNORE INTO integration_evidence VALUES(?,?)", (digest(body), canonical(body)))

    def _run(self, op, actor, action, **body):
        return self.core.execute(op, actor, action, dict(domain=self.core.DOMAIN, **body))["result"]

    def _source(self, action, **body):
        envelope = dict(action=action, body=dict(domain=self.core.DOMAIN, scope=SCOPE, provenance="synthetic", **body))
        result = self.core.ingest(digest(envelope), canonical(envelope).encode(), fixture_authenticated=True)
        require(result["state"] == "APPLIED", "PROJECTION_REVIEW:"+str(result.get("error")))
        return result

    def _query(self, action, binding, **extra):
        q = dict(action=action, endpoint=self.endpoint, binding=binding, **extra)
        # Persist and close before crossing a child-process/runtime boundary.
        # Never retain SQLite handles through the independent RPC process.
        require(not self.core.db.in_transaction and not self.provider.db.in_transaction, "QUERY_REQUIRES_COMMITTED_STATE")
        expected_storage = coordinator_fingerprint(self)
        db_path = self.directory / "projection.sqlite"
        before = db_path.stat().st_ino
        self.close()
        try:
            r = subprocess.run(["node", str(HERE / "client/paid-chain.mjs")], input=canonical(q),
                               text=True, capture_output=True, timeout=45, cwd=HERE / "client")
        finally:
            self._connect()
            if coordinator_fingerprint(self) != expected_storage:
                raise StorageFault("STORAGE_RECOVERY_REQUIRED:STATE_CHANGED_DURING_QUERY")
        require(r.returncode == 0, "CHAIN_ADAPTER_REJECTED:"+r.stderr[-1000:])
        result = json.loads(r.stdout)
        require(result["bindingHash"] == digest(binding), "CHAIN_ADAPTER_BINDING_MISMATCH")
        result["storageBoundary"] = dict(reopenedAfterChild=True, fileIdentityChanged=before != db_path.stat().st_ino)
        self._evidence(result)
        return result

    @staticmethod
    def policy(b):
        return dict(primaryPrice=100000, resaleCap=b["resaleCap"], primaryFeeBps=500,
                    resaleFeeBps=b["platformBps"], resaleOrganizerBps=b["organizerBps"], resaleAllowed=True,
                    refundProfile="LATEST_TRADE_UNWIND_FIXTURE")

    def prepare(self, b):
        expected = set("format tradeId chain packageId showId ticketId slot generation expectedVersion seller buyer amount currency expiresMs termsHash organizer organizerBps platformBps resaleCap policyHash".split())
        require(set(b) == expected, "EXACT_TRADE_BINDING_REQUIRED")
        tid = ident(b["tradeId"])
        for k in ("slot", "generation", "expectedVersion", "amount", "organizerBps", "platformBps", "resaleCap"):
            require(type(b[k]) is int and 0 <= b[k] <= 10**12, "INVALID_BINDING_INTEGER")
        require(b["format"] == "kix-paid-localnet-v1" and b["currency"] == "KRW" and b["expectedVersion"] == 1
                and b["generation"] == 1 and 0 < b["amount"] <= b["resaleCap"], "FIRST_PUBLIC_RESALE_ONLY")
        require(b["policyHash"] == digest(self.policy(b)), "POLICY_HASH_MISMATCH")
        prior = self._get("binding-"+tid)
        if prior:
            require(prior == b, "TRADE_ID_CONFLICT")
        else:
            self._query("inspect", b)
        # Deliberately bounded first slice: one tracked resale per show. Sharing
        # inventory with another coordinator is not an implemented protocol yet.
        key = digest([b["chain"], b["packageId"], b["showId"]])
        self.core.db.execute("INSERT OR IGNORE INTO integration_shows VALUES(?,?)", (key, tid))
        require(self.core.db.execute("SELECT trade_id FROM integration_shows WHERE show_key=?", (key,)).fetchone()[0] == tid, "SHOW_ALREADY_BOUND")
        self._save("binding-"+tid, b)
        event = self._run("event-"+tid, "operator", "create_event", eventId=b["showId"], organizer=b["organizer"],
                          policy=self.policy(b), seats=[str(b["slot"])], invitationQuota=1)
        # Import an already-issued right without inventing a primary payment.
        issued = self._run("import-"+tid, b["organizer"], "issue_invitation", inventoryId=event["inventoryIds"][0],
                           expectedInventoryVersion=0, recipient=b["seller"])
        self._run("prepare-"+tid, b["seller"], "prepare_trade", tradeId=tid, ticketId=issued["ticketId"],
                  buyer=b["buyer"], amount=b["amount"], expectedVersion=1)
        trade = self.trade(tid)
        self._run("accept-"+tid, b["buyer"], "accept_trade", tradeId=tid, termsHash=trade["termsHash"])
        return dict(bindingHash=digest(b), modelRightId=issued["ticketId"], chainRightId=b["ticketId"], primaryPaymentImported=False)

    def trade(self, tid):
        return self.core.snapshot()["trades"][tid]

    def capture(self, tid, *, lose_response=False):
        b = self._get("binding-"+tid)
        require(b is not None, "UNKNOWN_TRADE")
        r = self.trade(tid)
        request = dict(kind="CAPTURE", scope=SCOPE, tradeId=tid, bindingHash=digest(b),
                       orderId=r["externalOrderId"], buyer=b["buyer"], amount=b["amount"], currency=b["currency"])
        intent = self._save("capture-"+tid, dict(key=digest(["capture", digest(b)]), request=request))
        # This committed intent survives a provider call with no response. Same
        # request may be replayed only under this mock's explicit retention rule.
        try:
            self.provider.submit(intent["key"], request, lose_response=lose_response)
        except ConnectionError:
            return {"state": "CAPTURE_OUTCOME_UNKNOWN"}
        return self.sync_capture(tid)

    def sync_capture(self, tid):
        intent = self._get("capture-"+tid)
        require(intent is not None, "CAPTURE_INTENT_REQUIRED")
        fact = self.provider.lookup(intent["key"], digest(intent["request"]))
        if fact is None:
            return {"state": "CAPTURE_OUTCOME_UNKNOWN"}
        self._evidence(fact)
        q = fact["request"]
        require(fact["provenance"] == "MOCK_PROVIDER_ONLY" and fact["status"] == "SUCCESS", "MOCK_CAPTURE_NOT_CONFIRMED")
        self._source("capture", tradeId=tid, orderId=q["orderId"], paymentId=fact["operationId"],
                     amount=q["amount"], currency=q["currency"], buyer=q["buyer"])
        if fact["settlement"]:
            self._source("settle_capture", tradeId=tid, paymentId=fact["operationId"], amount=q["amount"], currency=q["currency"],
                         grossAmount=q["amount"], feeAmount=0, taxAmount=0, heldAmount=0, adjustmentAmount=0,
                         feeBearer="platform", contractRef="fixture:settlement:v1", movementId=fact["operationId"]+"-deposit")
        return dict(state="CAPTURE_CONFIRMED", paymentRef=digest([SCOPE, fact["operationId"]]),
                    paymentId=fact["operationId"], cashAvailable=fact["settlement"], provenance="MOCK_PROVIDER_ONLY")

    def record_submission(self, tid, submission):
        b = self._get("binding-"+tid)
        payment = self.sync_capture(tid)
        require(payment["state"] == "CAPTURE_CONFIRMED", "CAPTURE_REQUIRED")
        require(submission["bindingHash"] == digest(b) and submission["paymentRef"] == payment["paymentRef"]
                and submission["chain"] == b["chain"] and submission["packageId"] == b["packageId"], "SUBMISSION_BINDING_MISMATCH")
        self._save("submission-"+tid, submission)
        return dict(state="SIGNED_OUTCOME_UNKNOWN", digest=submission["digest"])

    def reconcile_chain(self, tid):
        b, saved = self._get("binding-"+tid), self._get("submission-"+tid)
        require(saved is not None, "SIGNED_SUBMISSION_REQUIRED")
        result = self._query("observe", b, submission=saved)
        prior = self.core.db.execute("SELECT body FROM integration_final WHERE trade_id=?", (tid,)).fetchone()
        if result["state"] == "OUTCOME_UNKNOWN":
            return json.loads(prior[0]) if prior else result
        if prior:
            old = json.loads(prior[0])
            require((old["digest"], old["state"], old["rawHash"]) == (result["digest"], result["state"], result["rawHash"]), "CHAIN_FINALITY_CONFLICT")
        else:
            self.core.db.execute("INSERT INTO integration_final VALUES(?,?)", (tid, canonical(result)))
        if result["state"] == "EXECUTED_SUCCESS":
            # Crash after storing proof but before projection is safe: command
            # replay commits exactly once and verifies the Move allocation.
            self._run("chain-commit-"+tid, "operator", "commit_trade", tradeId=tid)
        return result

    def cancel(self, tid):
        result = self.reconcile_chain(tid)
        require(result["state"] == "EXECUTED_SUCCESS" or result.get("compensationFence") == "SHOW_CLOSED_UNTRANSFERRED", "CHAIN_UNRESOLVED_NO_COMPENSATION")
        b = self._get("binding-"+tid)
        self._query("closed", b)
        return self._run("cancel-"+tid, "operator", "cancel_event", eventId=b["showId"])

    def release_after_fixture_performance(self, tid):
        """Injected performance-completion assumption, not an on-chain event."""
        require(self.reconcile_chain(tid)["state"] == "EXECUTED_SUCCESS", "CHAIN_SUCCESS_REQUIRED")
        self._query("open", self._get("binding-"+tid))
        return self._run("complete-"+tid, "operator", "complete_event", eventId=self._get("binding-"+tid)["showId"])

    def prepare_effect(self, tid, eid, kind, amount, allocation_id=None):
        r = self.trade(tid)
        if kind == "PAYOUT":
            self._query("open", self._get("binding-"+tid))
            a = next((a for a in r["allocations"] if a["id"] == allocation_id), None)
            require(a is not None, "ALLOCATION_NOT_FOUND")
            beneficiary, route, contract = a["payee"], "BANK_PAYOUT_FIXTURE", "fixture:payout:v1"
        else:
            require(kind == "REFUND", "UNSUPPORTED_EFFECT")
            beneficiary, route, contract = r["buyer"], "CASH_REFUND_FIXTURE", "fixture:cash-refund:v1"
        return self._run("effect-"+eid, "operator", "prepare_effect", tradeId=tid, effectId=eid, kind=kind, amount=amount,
                         allocationId=allocation_id, routeProfile=route, contractRef=contract, beneficiaryAccountRef="fixture-account:"+beneficiary)

    def send_effect(self, eid, *, lose_response=False):
        # The durable first-send flag precedes the external call. Later calls
        # only query; an absent provider operation is left unresolved here.
        effect = self.core.snapshot()["effects"][eid]
        if not effect["sent"] and effect["kind"] == "PAYOUT":
            self._query("open", self._get("binding-"+effect["trade"]))
        decision = self._run("send-"+eid, "operator", "send_effect", effectId=eid)
        if decision.get("dispatchDecision") != "FIRST_SEND_INTENT":
            return self.sync_effect(eid)
        claim = self._run("claim-"+eid, "operator", "claim_effect", effectId=eid, workerId="local-adapter", leaseSeconds=60)
        permit = self._run("dispatch-"+eid, "operator", "dispatch_effect", effectId=eid, workerId="local-adapter", claimGeneration=claim["claimGeneration"])
        require(permit["dispatchDecision"] == "SUBMIT_SAME_REQUEST", "NO_DISPATCH_PERMIT")
        request = json.loads(permit["requestBytes"])
        require(digest(request) == permit["requestHash"], "REQUEST_BYTES_CHANGED")
        if getattr(self, 'before_effect_submit', None):
            self.before_effect_submit(self, eid, permit)
        try:
            self.provider.submit(permit["idempotencyKey"], request, lose_response=lose_response)
        except ConnectionError:
            return {"state": "OUTCOME_UNKNOWN"}
        return self.sync_effect(eid)

    def sync_effect(self, eid):
        x = self.core.snapshot()["effects"][eid]
        fact = self.provider.lookup(x["idempotencyKey"], x["requestHash"])
        if fact is None:
            return {"state": x["state"], "decision": "QUERY_ONLY", "providerOperation": "NOT_FOUND"}
        self._evidence(fact)
        common = dict(effectId=eid, providerOperationId=fact["operationId"], amount=x["amount"], currency=x["currency"],
                      beneficiary=x["beneficiary"], paymentId=x["paymentId"])
        self._source("observe_effect", **common, phase="STATUS", status=fact["status"], sourceId=fact["operationId"]+"-"+fact["status"])
        if fact["funds"]:
            self._source("observe_effect", **common, phase="FUNDS", sourceId=fact["operationId"]+"-debit", movementId=fact["operationId"]+"-debit")
        return {"state": self.core.snapshot()["effects"][eid]["state"], "providerOperationId": fact["operationId"]}

    def summary(self, tid):
        r = self.trade(tid)
        s = self.core.snapshot()
        final = self.core.db.execute("SELECT body FROM integration_final WHERE trade_id=?", (tid,)).fetchone()
        return dict(trade=r, right=s["tickets"][r["ticket"]], balances=s["balances"], effects=s["effects"],
                    binding=self._get("binding-"+tid), chain=json.loads(final[0]) if final else None,
                    provider=self.provider.summary(), journalEntries=len(s["journal"]),
                    retainedEvidence=self.core.db.execute("SELECT count(*) FROM integration_evidence").fetchone()[0],
                    runtime=dict(python=sys.version.split()[0], sqlite=sqlite3.sqlite_version,
                                 journalMode=self.core.db.execute("PRAGMA journal_mode").fetchone()[0],
                                 synchronous=self.core.db.execute("PRAGMA synchronous").fetchone()[0]),
                    moneyProvenance="MOCK_PROVIDER_ONLY", rightsAuthority="ACTUAL_SUI_LOCALNET_TRUSTED_RPC")
