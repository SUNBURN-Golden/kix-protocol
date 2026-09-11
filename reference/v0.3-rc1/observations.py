"""Durable raw inbox precedes parsing/authentication/domain attribution.

The fixtureAuthenticated flag is an injected test assumption, not verification.
Rejected raw facts remain review items, never silent successful domain postings.
"""
import base64
import hashlib
import json
from common import canonical, digest, ident, require, Rejected

SOURCE_ACTIONS={"capture","settle_capture","observe_effect","observe_recovery","adjust_pg_cancel","observe_return","observe_funding","finalize_effect","observe_dispatch_lookup"}


class ObservationMixin:
    def init_inbox(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS raw_inbox (id TEXT PRIMARY KEY, raw BLOB NOT NULL, sha256 TEXT NOT NULL, state TEXT NOT NULL, normalized TEXT, error TEXT, fixture_verified INTEGER NOT NULL DEFAULT 0)")
        self.db.execute("CREATE TABLE IF NOT EXISTS raw_conflicts (id TEXT, sha256 TEXT, raw BLOB NOT NULL, PRIMARY KEY(id,sha256))")
        self.db.execute("CREATE TABLE IF NOT EXISTS review_facts (fact_key TEXT PRIMARY KEY, event_id TEXT, action TEXT, amount INTEGER, currency TEXT, first_observation TEXT, conflict INTEGER NOT NULL DEFAULT 0, resolution TEXT NOT NULL DEFAULT 'OPEN')")

        self.db.execute("CREATE TABLE IF NOT EXISTS fact_variants (fact_key TEXT, binding_hash TEXT, normalized TEXT, first_observation TEXT, applied_operation TEXT, applied_sequence INTEGER, PRIMARY KEY(fact_key,binding_hash))")

    def mark_observation_applied(self,observation_id):
        self.db.execute("UPDATE raw_inbox SET state='APPLIED',error=NULL WHERE id=?",(observation_id,))

    def ingest(self,observation_id,raw,*,fixture_authenticated=False,fail_after_store=False,fail_before_apply_commit=False):
        ident(observation_id)
        require(isinstance(raw,bytes) and len(raw)<=1024*1024,"RAW_BYTES_REQUIRED")
        sha=hashlib.sha256(raw).hexdigest()
        self.db.execute("BEGIN IMMEDIATE")
        old=self.db.execute("SELECT sha256 FROM raw_inbox WHERE id=?",(observation_id,)).fetchone()
        if old and old[0]!=sha:
            self.db.execute("INSERT OR IGNORE INTO raw_conflicts VALUES(?,?,?)",(observation_id,sha,raw))
            self.db.execute("COMMIT")
            raise Rejected("RAW_OBSERVATION_ID_CONFLICT_PRESERVED")
        self.db.execute("INSERT OR IGNORE INTO raw_inbox VALUES(?,?,?,'STORED',NULL,NULL,0)",(observation_id,raw,sha))
        self.db.execute("COMMIT")
        if fail_after_store: raise RuntimeError("INJECTED_AFTER_RAW_STORE")
        return self.apply_observation(observation_id,fixture_authenticated=fixture_authenticated,fail_before_apply_commit=fail_before_apply_commit)

    def apply_observation(self,observation_id,*,fixture_authenticated=False,fail_before_apply_commit=False):
        row=self.db.execute("SELECT raw,state,normalized FROM raw_inbox WHERE id=?",(observation_id,)).fetchone()
        require(row is not None,"RAW_OBSERVATION_NOT_FOUND")
        if row[1]=="APPLIED":
            return {"observationId":observation_id,"state":"APPLIED","duplicate":True}
        normalized=None
        try:
            require(fixture_authenticated is True,"SOURCE_AUTHENTICATION_REQUIRED")
            self.db.execute("UPDATE raw_inbox SET fixture_verified=1 WHERE id=?",(observation_id,))
            normalized=json.loads(row[0])
            require(isinstance(normalized,dict) and set(normalized)=={"action","body"},"INVALID_SOURCE_ENVELOPE")
            action=normalized["action"]; body=normalized["body"]
            require(action in SOURCE_ACTIONS and isinstance(body,dict),"INVALID_SOURCE_ACTION")
            self.db.execute("UPDATE raw_inbox SET state='NORMALIZED',normalized=?,error=NULL WHERE id=?",(canonical(normalized),observation_id))
            result=self.execute("observation-"+digest(observation_id),"pg-adapter",action,body,fail_before_commit=fail_before_apply_commit,_observation_id=observation_id)
            # Raw resolution and economic-fact resolution committed WITH the ledger.
            return {"observationId":observation_id,"state":"APPLIED","receipt":result}
        except (Rejected,ValueError,TypeError,KeyError) as exc:
            self.db.execute("UPDATE raw_inbox SET state='REVIEW',error=? WHERE id=?",(str(exc),observation_id))
            if fixture_authenticated and isinstance(normalized,dict): self.record_source_fact(observation_id,normalized)
            return {"observationId":observation_id,"state":"REVIEW","error":str(exc)}

    def record_source_fact(self,observation_id,normalized,applied=None,state=None):
        b=normalized.get("body"); action=normalized.get("action")
        if action not in SOURCE_ACTIONS or not isinstance(b,dict) or b.get("scope")!=self.SCOPE or b.get("provenance")!="synthetic": return
        amount=b.get("amount"); currency=b.get("currency")
        if type(amount) is not int or not 0<=amount<=10**12 or currency!="KRW": return
        reference=b.get("paymentId") if action=="capture" else b.get("movementId")
        if not isinstance(reference,str): return
        state=state or self.snapshot()
        namespace="capture" if action=="capture" else "movement"
        key=digest([self.SCOPE,namespace,reference])
        r=state["trades"].get(b.get("tradeId"))
        if r is None and b.get("effectId") in state["effects"]:
            x=state["effects"][b["effectId"]]; r=state["trades"][x["trade"]]
        event=r["event"] if r else None
        # Delivery identifiers do not change an economic fact. The full binding does.
        binding=dict(action=action,body={k:v for k,v in b.items() if k!="sourceId"})
        bh=digest(binding)
        own_transaction=not self.db.in_transaction
        if own_transaction: self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT OR IGNORE INTO review_facts VALUES(?,?,?,?,?,?,0,'OPEN')",(key,event,action,amount,currency,observation_id))
            self.db.execute("INSERT OR IGNORE INTO fact_variants VALUES(?,?,?,?,NULL,NULL)",(key,bh,canonical(binding),observation_id))
            if applied:
                self.db.execute("UPDATE fact_variants SET applied_operation=COALESCE(applied_operation,?),applied_sequence=COALESCE(applied_sequence,?) WHERE fact_key=? AND binding_hash=?",(*applied,key,bh))
            variants=self.db.execute("SELECT binding_hash,applied_operation FROM fact_variants WHERE fact_key=?",(key,)).fetchall()
            conflict=len(variants)>1
            resolved=not conflict and all(op is not None for _,op in variants)
            self.db.execute("UPDATE review_facts SET conflict=?,resolution=?,event_id=COALESCE(event_id,?) WHERE fact_key=?",(int(conflict),'CONFLICT' if conflict else 'RESOLVED' if resolved else 'OPEN',event,key))
            if own_transaction: self.db.execute("COMMIT")
        except BaseException:
            if own_transaction: self.db.execute("ROLLBACK")
            raise

    def inbox_summary(self,event_id):
        rows=self.db.execute("SELECT action,amount,conflict,resolution FROM review_facts WHERE event_id=?",(event_id,)).fetchall()
        evidence={
            "scope":"GLOBAL_INBOX_AND_LEDGER_V1",
            "raw":[list(r) for r in self.db.execute("SELECT id,sha256,state,normalized,error,fixture_verified FROM raw_inbox ORDER BY id")],
            "rawConflicts":[list(r) for r in self.db.execute("SELECT id,sha256 FROM raw_conflicts ORDER BY id,sha256")],
            "facts":[list(r) for r in self.db.execute("SELECT * FROM review_facts ORDER BY fact_key")],
            "variants":[list(r) for r in self.db.execute("SELECT * FROM fact_variants ORDER BY fact_key,binding_hash")],
            "ledgerStateHash":digest(self.snapshot()),
        }
        return dict(evidenceDigest=digest(evidence),evidenceDigestScope=evidence["scope"],
                    eventReviewFacts=sum(status!='RESOLVED' for _,_,_,status in rows),
                    eventResolvedFacts=sum(status=='RESOLVED' for _,_,_,status in rows),
                    observedCaptureAmountUnderReview=sum(n for a,n,c,status in rows if a=="capture" and status=='OPEN'),
                    observedMovementAmountUnderReview=sum(n for a,n,c,status in rows if a!="capture" and status=='OPEN'),
                    conflictingReviewFacts=sum(c for a,n,c,status in rows),
                    conflictingFactAmountReference=sum(n for a,n,c,status in rows if c),
                    globalRawConflictCount=len(evidence['rawConflicts']),
                    unattributedFacts=self.db.execute("SELECT count(*) FROM review_facts WHERE event_id IS NULL").fetchone()[0],
                    inboxPendingOrReview=self.db.execute("SELECT count(*) FROM raw_inbox WHERE state!='APPLIED'").fetchone()[0],
                    pendingCountScope='GLOBAL',amountsAreUnpostedObservations=True,
                    completenessAttested=False)

    def export_replay(self):
        self.db.execute("BEGIN")
        try:
            value=self._consistent_export()
            self.db.execute("COMMIT")
            return value
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _consistent_export(self):
        rows=self.db.execute("SELECT i.operation_id,i.actor,i.action,i.body FROM command_inputs i JOIN commands c ON c.operation_id=i.operation_id ORDER BY json_extract(c.receipt,'$.sequence')").fetchall()
        commands=[dict(operationId=op,actor=actor,action=action,body=json.loads(body)) for op,actor,action,body in rows]
        raw=[dict(observationId=i,rawBase64=base64.b64encode(b).decode(),sha256=sha,state=state,normalized=normalized,error=error,fixtureVerified=verified)
             for i,b,sha,state,normalized,error,verified in self.db.execute("SELECT id,raw,sha256,state,normalized,error,fixture_verified FROM raw_inbox ORDER BY id")]
        review=[list(row) for row in self.db.execute("SELECT * FROM review_facts ORDER BY fact_key")]
        conflicts=[dict(observationId=i,sha256=sha,rawBase64=base64.b64encode(b).decode())
                   for i,sha,b in self.db.execute("SELECT id,sha256,raw FROM raw_conflicts ORDER BY id,sha256")]
        variants=[list(row) for row in self.db.execute("SELECT * FROM fact_variants ORDER BY fact_key,binding_hash")]
        evidence=dict(rawInbox=raw,reviewFacts=review,rawConflicts=conflicts,factVariants=variants)
        return dict(domain=self.DOMAIN,commands=commands,expectedStateHash=digest(self.snapshot()),**evidence,
                    expectedEvidenceHash=digest(evidence),authenticity="UNSIGNED_LOCAL_FIXTURE_EXPORT",chainFinalityVerified=False)

    @classmethod
    def rebuild_fixture(cls,export,path=":memory:"):
        require(export["domain"]==cls.DOMAIN,"DOMAIN_MISMATCH")
        c=cls(path)
        require(not c.snapshot()["events_log"],"REBUILD_REQUIRES_EMPTY_DATABASE")
        for cmd in export["commands"]: c.execute(cmd["operationId"],cmd["actor"],cmd["action"],cmd["body"])
        require(digest(c.snapshot())==export["expectedStateHash"],"REPLAY_STATE_MISMATCH")
        evidence={key:export[key] for key in ("rawInbox","reviewFacts","rawConflicts","factVariants")}
        require(digest(evidence)==export["expectedEvidenceHash"],"REPLAY_EVIDENCE_MISMATCH")
        for row in export["rawInbox"]:
            raw=base64.b64decode(row["rawBase64"],validate=True)
            require(hashlib.sha256(raw).hexdigest()==row["sha256"],"RAW_EXPORT_HASH_MISMATCH")
            # Restore evidence without upgrading authentication or retrying rejected facts.
            c.db.execute("INSERT INTO raw_inbox VALUES(?,?,?,?,?,?,?)",(row["observationId"],raw,row["sha256"],row["state"],row["normalized"],row["error"],row["fixtureVerified"]))
        c.db.execute("DELETE FROM fact_variants")
        c.db.execute("DELETE FROM review_facts")
        for row in export["reviewFacts"]: c.db.execute("INSERT INTO review_facts VALUES(?,?,?,?,?,?,?,?)",row)
        for row in export["factVariants"]: c.db.execute("INSERT INTO fact_variants VALUES(?,?,?,?,?,?)",row)
        for row in export["rawConflicts"]:
            raw=base64.b64decode(row["rawBase64"],validate=True)
            require(hashlib.sha256(raw).hexdigest()==row["sha256"],"RAW_EXPORT_HASH_MISMATCH")
            c.db.execute("INSERT INTO raw_conflicts VALUES(?,?,?)",(row["observationId"],row["sha256"],raw))
        return c
