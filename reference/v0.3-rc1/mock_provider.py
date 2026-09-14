"""Independent, durable TEST provider. No PG or bank network/account is used.

The administrator's advance() controls observations in fault tests. Same-key
retention is unlimited in this fixture, not a promise about a real provider.
"""
import json
import sqlite3
from common import canonical, digest, require

SCOPE = dict(provider="kix-mock", environment="local-fixture", merchant="kix-fixture", channel="simulated")


class MockProvider:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS operations (key TEXT PRIMARY KEY, request_hash TEXT, request TEXT, result TEXT, calls INTEGER)")

    def submit(self, key, request, *, lose_response=False):
        require(request["scope"] == SCOPE, "MOCK_SCOPE_REQUIRED")
        require(request["kind"] in ("CAPTURE", "PAYOUT", "REFUND"), "MOCK_KIND")
        require(type(request["amount"]) is int and request["amount"] > 0 and request["currency"] == "KRW", "MOCK_MONEY")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute("SELECT request_hash FROM operations WHERE key=?", (key,)).fetchone()
            if old:
                require(old[0] == digest(request), "PROVIDER_KEY_CONFLICT")
                self.db.execute("UPDATE operations SET calls=calls+1 WHERE key=?", (key,))
            else:
                result = dict(provenance="MOCK_PROVIDER_ONLY", operationId="mock-"+digest([SCOPE, key]),
                              idempotencyKey=key, requestHash=digest(request), request=request,
                              status="SUCCESS" if request["kind"] == "CAPTURE" else "PENDING",
                              settlement=False, funds=False, economicExecutions=1)
                self.db.execute("INSERT INTO operations VALUES(?,?,?,?,1)", (key, digest(request), canonical(request), canonical(result)))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        if lose_response:
            raise ConnectionError("MOCK_RESPONSE_LOST_AFTER_COMMIT")
        return self.lookup(key, digest(request))

    def lookup(self, key, request_hash):
        row = self.db.execute("SELECT request_hash,result FROM operations WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        require(row[0] == request_hash, "PROVIDER_LOOKUP_BINDING_MISMATCH")
        return json.loads(row[1])

    def advance(self, key, *, status=False, funds=False, settlement=False):
        """Fixture administrator only; never exposed as an economic command."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT result FROM operations WHERE key=?", (key,)).fetchone()
            require(row is not None, "MOCK_OPERATION_NOT_FOUND")
            r = json.loads(row[0])
            capture = r["request"]["kind"] == "CAPTURE"
            require(not settlement or capture, "ONLY_CAPTURE_SETTLES")
            require(not funds or not capture, "CAPTURE_IS_NOT_BANK_DEBIT")
            if status:
                r["status"] = "SUCCESS"
            if funds:
                r["funds"] = True
            if settlement:
                r["settlement"] = True
            self.db.execute("UPDATE operations SET result=? WHERE key=?", (canonical(r), key))
            self.db.execute("COMMIT")
            return r
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def summary(self):
        rows = self.db.execute("SELECT key,result,calls FROM operations ORDER BY key").fetchall()
        return [dict(key=key, operationId=json.loads(r)["operationId"], kind=json.loads(r)["request"]["kind"],
                     status=json.loads(r)["status"], economicExecutions=json.loads(r)["economicExecutions"], submitCalls=calls,
                     funds=json.loads(r)["funds"], settlement=json.loads(r)["settlement"]) for key, r, calls in rows]
