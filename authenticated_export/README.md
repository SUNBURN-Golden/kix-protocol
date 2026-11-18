# authenticated_export — Track K stage 7 (R-11), local fixture boundary

Authenticated, consistent export over the stage-5 durable local PostgreSQL
source. Contract: `runtime/AUTHENTICATED_EXPORT.md` §§1–5 and ADR-0001 §9.
Backend: the adopted local, non-production PostgreSQL 17.11 (option A of
`docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6), composed through
`durable/` unchanged. This package is **not** protocol truth, not a production
endpoint, not a registered manifest wire schema, not a replication or storage
engine, and not a production-conformance claim. Every execution flag in
`__init__.py` is false; `LOCAL_EXPORT_FIXTURE_ONLY` is true.

## Layout

| Module | Role |
| --- | --- |
| `mapping.py` | Pinned PostgreSQL→export type mapping (psycopg-free). |
| `cut.py` | Source cut and projection watermark documents; consistency checks. |
| `files.py` | Deterministic canonical-JSONL row files, per-file sha256 binding. |
| `manifest.py` | ExportManifestV1-shaped local manifest, exact contract field names. |
| `auth.py` | Fixture HMAC-SHA256 signing/verification (onsale/tokens.py pattern). |
| `rollback.py` | Consumer-side local anti-rollback registry, atomic write. |
| `exporter.py` | Pure orchestration over an injected source adapter. |
| `source.py` | PG-bound read-only adapter: one SERIALIZABLE READ ONLY snapshot. |
| `verify.py` | Fail-closed consumer verification and the audit trace. |
| `test_pure.py` | Database-free suite (fixture source adapter). |
| `test_export.py` | PostgreSQL-bound suite; graceful skip without the backend. |
| `run.py` | Local acceptance runner (host.json + summary.json). |

Run: `python3 scripts/stage7_local_check.py [output-dir]` (default
`validation/2026-11-12-k-stage7-authenticated-export`). The runner checks the
two locked kernel blobs before running anything.

## Source cut vs projection watermark (§§1–2)

- One export = one shard = one MVCC snapshot: `BEGIN ISOLATION LEVEL
  SERIALIZABLE READ ONLY`, identity `pg_current_snapshot()` (xmin:xmax:xip).
  Every table is read inside that single snapshot; a writer that commits
  mid-capture is invisible to the cut (tested).
- `pg_current_wal_lsn()` at start/end is **provenance only**, never a cut.
  A manifest whose `committedPosition` is an LSN alone is rejected.
- Single shard only. No cross-shard coordinator protocol exists, so no
  multi-shard cut is certified and no global-atomicity claim is made; the
  decision boundary is recorded verbatim in
  `consistentCutProofOrDecisionBoundary`.
- The cut carries per-table `{rowCount, contentSha256}` over the mapped rows
  in primary-key order. The projection watermark is a separate document:
  `{table, appliedSourcePosition, appliedAtSnapshot, lagRowCount}`. For
  FULL_SNAPSHOT every watermark equals the cut and lag is 0. For INCREMENTAL
  the watermark is the cumulative prefix up to `endCursor`; lag (cut rows
  beyond the prefix) is reported, never hidden.

## Modes (§3)

- `FULL_SNAPSHOT`: every row of the cut; requires `fullSnapshot`
  (`isolationLevel`, `snapshotId`, `fingerprint`, `xmin`, `xmax`);
  `incremental` must be null; cursors are refused.
- `INCREMENTAL`: per-table keyset delta `(startCursor, endCursor]` with
  `cursorKind='table-keyset/1'` and
  `boundarySemantics='startExclusive-endInclusive'`; requires `incremental`
  metadata; `fullSnapshot` must be null. Dedup identity is the stable primary
  key: redelivery of the same cursor range is byte-identical (tested).
- The two metadata blocks are never merged into one ambiguous
  `commitPosition`.

### Keyset characterization (recorded, not hidden)

`table-keyset/1` ranges are ordered by the primary key, not by insertion
time. For tables whose keys are not append-monotonic (`ledger.entry_id`,
sha256-derived ids), a row inserted **below** `startCursor` after the prior
export is outside the delta range. The prefix watermark counts everything
`<= endCursor` as covered by the cursor claim, so such an insert is not
reported as lag. This is a characterization of the pinned cursor kind: the
contract fixes the boundary semantics and requires visible gaps/lag but does
not define an insert-below-cursor policy. A consumer that needs gap-free
catch-up uses FULL_SNAPSHOT (or chooses cursors with knowledge of the key
order). The PG suite asserts this behavior explicitly.

A partial incremental prefix hash is an authenticated statement about the
source: a consumer without source access can check count ordering, boundary
equality and lag arithmetic locally, but re-deriving a partial prefix hash
requires re-reading the source. When an incremental export has caught up from
the beginning (`startCursor` all null, watermark count == cut count), the
delta is the whole cut content and is re-hashed against the cut locally.

## Manifest, hashes and authentication (§§3–4)

- Field names are exactly the contract's (`manifest.py:MANIFEST_FIELDS`),
  plus the fixture `keyVersion`/`signature`. This is a local fixture document
  (`kix-export-manifest-local/1`); registering a production wire schema is
  DECISION_REQUIRED · Astra.
- `content.manifestHash` = sha256 of the canonical body **without**
  `content.manifestHash` and **without** `signature`.
- `signature` = fixture HMAC-SHA256 over the canonical body **without**
  `signature` (includes `manifestHash` and `keyVersion`), caller-supplied key,
  never stored or committed. A hash alone proves neither authorized
  authorship nor latest state; the production signing scheme, trust root and
  registry boundary are DECISION_REQUIRED · Astra.
- Every file (11 table files + `type-mapping.json`) is sha256-bound into
  `content.perFileHash` with its row count; `manifest.json` is written last.
  The consumer re-checks the exact file set: missing, extra, truncated or
  re-hashed-without-key files all fail closed (tested, including a full
  re-hash attack that keeps the old signature).
- Anti-rollback: `RollbackRegistry` records, per `sourceClusterId`, the last
  accepted `{exportSeq, exportId}`; `exportSeq <= last` is rejected and the
  file is written atomically. `exportSeq` is a caller-supplied transport
  ordinal that travels **beside** the manifest at verification time — it is
  not a manifest field, because binding it into a signed production manifest
  is part of the undecided Astra policy. The registry is consumer state,
  never exporter state, and fails closed on a corrupt file.

## Type mapping (§5)

`type-mapping.json` is the pinned descriptor (`kix-local-export-types/1`):

- binary(32) (sha256 columns, sha256-derived ids) and binary(16) (event
  alias) are lowercase hex with exact width checks — never widened or
  truncated.
- `amount_u128` is canonical u128 decimal text (Wide128-lossless): no leading
  zeros, `<= 2^128-1`, never a float, never narrowed to a signed integer.
  u128-max round-trips through PostgreSQL (tested).
- `created_ms`/`received_ms`/`at_ms` are epoch milliseconds, unit explicit in
  the descriptor. Inbox `occurredAtText`/`occurredOffset` inside `fact_json`
  are preserved verbatim; no time zone is assumed.
- `inbox_delivery.raw` is exported as lowercase hex bound by its sha256
  (`raw_sha256`); the durable per-row `crc` column is exported unchanged and
  bound by the content hash. `ledger.is_open` is exported (it is outside the
  durable CRC by design).
- Vocabularies are pinned to the values the unchanged `durable/` layer writes
  (outcome/relation/state/phase/budget_class/intent_kind); anything else
  fails closed. Fast64 is not used (no approved execution profile). No
  Arrow/Parquet materialization happens in this node; the descriptor is the
  pin a later Arrow node must bind.
- The pin is psycopg-free and independent of `durable/`; the PG suite
  cross-checks it column-for-column against `durable.schema` and pins the
  live `information_schema` fingerprint of the eleven tables. Schema drift
  fails closed (`EXPORT_SCHEMA`) without editing `durable/`.

## Audit trace

`verify.audit_trace(directory, key=None)` resolves query → exportId →
manifest → exact source cut and projection watermarks → exact files/hashes →
schema and semantics versions, recomputing every hash from disk. Any broken
link raises; a trace is never returned for a tampered export.

## Non-claims

No production durability, distributed fencing, bank exactly-once, chain
finality, legal compliance or production readiness is inferred. No SLO,
ranking, product policy value, new protocol command, public endpoint, funds
execution or chain writer. The export takes no writer lock (tested against
the single-writer file lock) and performs no writes against the source.
