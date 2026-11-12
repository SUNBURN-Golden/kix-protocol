# k-stage7-authenticated-export — authenticated, consistent export

Node: `k-stage7-authenticated-export` (Track K stage 7; program roadmap register
row R-11 in `docs/decisions/PROGRAM_ROADMAP_20260930.md`). Not an ASTRA
program-mode session. No issue. No commit, push, pull request, or comment in
this session (the supervisor does git/GitHub). Record opened 2026-11-12.
Branch: `agent/kix-k-stage7-authenticated-export`. Depends on
`k-stage5-durable-tx` (PR #443, merge `2ec62ca73ee41f397268944e8e0de98ef9d03305`,
ancestor of this branch HEAD — verified).

**State: acceptance covered locally — `merge-ready` candidate pending
supervisor commit/push, exact-head CI, non-author review and user merge.** The
offline suite (`authenticated_export.test_pure`, 54 tests) and the
PostgreSQL-bound suite (`authenticated_export.test_export`, 13 tests) run green
on the pinned local PostgreSQL 17.11, and the CI-equivalent battery below
passed. Nothing here is exact-head CI. No production readiness is claimed; the
export is a local fixture boundary and every execution flag is false.

## Decision applicability guard (CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md §5.1)

- `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 names the backend
  directly (option A: local, non-production PostgreSQL 17.11, single process,
  single writer, default off, production flags false). ADOPT with a named
  backend; the adoption file is unchanged on this base.
- No DEFERRED/DECLINED decision item is implemented. No decision-document merge
  is treated as a positive adoption beyond its specified scope.

## Base (AGENTS §1)

- Task branch HEAD and observed `origin/main`:
  `d34c316c1f354a6b1219796f80662bfc28972818` — **no delta**. Read from the local
  remote-tracking ref; `git fetch origin main` was not run because the
  supervisor rule for this session forbids network actions, so the true current
  main may be newer still.
- No implementation commit SHA and no final task head exist yet (the supervisor
  commits). Nothing here is exact-head CI.
- Tools: `rustc`/`cargo` 1.98.1 (workflow pin); `python3` 3.13.5 (`protocol.yml`
  pins 3.12 — deviation recorded below); node v24.22.1 (CI: 24); npm 11.21.1;
  PostgreSQL 17.11 at `/usr/lib/postgresql/17/bin/{postgres,initdb}`; psycopg
  3.2.6.

Locked blobs, before the edits and after the last verification run, identical:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`reference/v0.3-rc1/**`, `runtime/**`, `.aiops/**`, `docs/tasks/**`,
`.github/**`, `durable/**`, `readiness/**`, `exploration/**`, `onsale/**`,
`integration_gate/**` are untouched — `git status` shows only the paths below.

## Changed paths

- `authenticated_export/` (new top-level package; local fixture boundary —
  mirrors the `durable/`/`onsale/` layout, outside `check_ci_test_discovery.py`
  scope so **no workflow edit**): `__init__.py` (all flags false +
  `LOCAL_EXPORT_FIXTURE_ONLY`), `errors.py`, `mapping.py` (pinned
  `kix-local-export-types/1` type map + descriptor), `cut.py` (source cut /
  projection watermark documents + predicates), `files.py` (deterministic
  canonical-JSONL row files, per-file sha256), `manifest.py`
  (ExportManifestV1-shaped local document, contract field names, manifestHash
  binding, fail-closed validation), `auth.py` (fixture HMAC-SHA256,
  caller-supplied key, onsale/tokens.py pattern), `rollback.py` (consumer-side
  atomic anti-rollback registry), `exporter.py` (pure orchestration over an
  injected source adapter), `source.py` (PG-bound read-only adapter: one
  `SERIALIZABLE READ ONLY` snapshot, CRC re-verify, schema fingerprint),
  `verify.py` (fail-closed consumer verification + `audit_trace()`),
  `test_pure.py` (54 tests, database-free), `test_export.py` (13 tests,
  PG-bound, graceful skip, **not CI-wired**), `run.py` (acceptance runner),
  `README.md`.
- `scripts/stage7_local_check.py` — runner entrypoint (host.json + summary.json).
- `docs/README.md` — one index section (location pointer only), required by
  `scripts/check_docs_index.py` for this record.
- `validation/2026-11-12-k-stage7-authenticated-export/` — this record +
  `host.json`, `summary.json`.

## Design summary

Contract: `runtime/AUTHENTICATED_EXPORT.md` §§1–5 + ADR-0001 §9, over the
stage-5 local source via the unchanged `durable/` public layer.

- **Source cut (§§1–2).** One export = one shard = one `BEGIN ISOLATION LEVEL
  SERIALIZABLE READ ONLY` MVCC snapshot on its own read-only connection.
  `pg_current_snapshot()` (xmin:xmax:xip) is the cut identity;
  `pg_current_wal_lsn()` is captured at start/end as **provenance only** — a
  manifest whose `committedPosition` is an LSN alone is rejected. Per-table
  `{rowCount, contentSha256}` over mapped rows in PK order. Single shard only:
  no cross-shard coordinator protocol exists, so no multi-shard cut is
  certified and no global-atomicity claim is made; the decision boundary is
  recorded verbatim in `consistentCutProofOrDecisionBoundary`.
- **Projection watermarks.** Separate documents
  `{table, appliedSourcePosition, appliedAtSnapshot, lagRowCount}`: FULL_SNAPSHOT
  must equal the cut (lag 0); INCREMENTAL is the cumulative prefix up to
  `endCursor` and must not exceed the cut. Lag is reported, never hidden.
- **Modes (§3).** FULL_SNAPSHOT requires `fullSnapshot`
  (`isolationLevel/snapshotId/fingerprint/xmin/xmax`) and refuses cursors;
  INCREMENTAL requires `incremental`
  (`cursorKind='table-keyset/1'`, `startCursor`, `endCursor`,
  `boundarySemantics='startExclusive-endInclusive'`) and dedups by stable PK
  identity — redelivery is byte-identical (tested). Never merged into one
  ambiguous `commitPosition`.
- **Integrity + authentication (§4).** Every file (11 table files +
  `type-mapping.json`) is sha256-bound into `content.perFileHash` with row
  counts; `manifestHash` = sha256 of the canonical body without
  `manifestHash`/`signature`; `signature` = fixture HMAC-SHA256 over the
  canonical body incl. `manifestHash`+`keyVersion`, caller-supplied key, never
  stored. `RollbackRegistry` records last accepted `{exportSeq, exportId}` per
  `sourceClusterId` (seq ≤ last rejected; `exportSeq` travels beside the
  manifest as a transport ordinal — binding it into a signed production
  manifest is part of the undecided Astra policy). Missing, extra, truncated,
  re-hashed-without-key, wrong-key, corrupt-registry all fail closed (tested).
- **Type mapping (§5).** `type-mapping.json` pins `kix-local-export-types/1`:
  binary(32)/binary(16) as lowercase hex with exact widths; `amount_u128` as
  canonical u128 decimal text (Wide128-lossless, u128-max round-trips through
  PostgreSQL — tested); epoch-ms units explicit; inbox
  `occurredAtText`/`occurredOffset` verbatim; vocabularies pinned to the values
  the unchanged `durable/` layer writes; Fast64 not used; no Arrow/Parquet
  materialization (descriptor is the pin a later Arrow node must bind).
- **Audit trace (§5).** `verify.audit_trace()` resolves query → exportId →
  manifest → exact cut + watermarks → files/hashes → schema/semantics
  versions, recomputing every hash from disk; a trace is never returned for a
  tampered export (tested).
- **Read-only source.** The exporter takes no writer lock and no writes: an
  export succeeds while the single-writer unit holds its file lock (tested);
  a writer that commits mid-capture is invisible to the cut (tested);
  CRC corruption and `information_schema` drift fail closed (tested).

## Existing coverage mapping (AGENTS §7)

Sufficiently covered by existing suites, cited not duplicated (all rerun green
here): durable layer (`durable.test_pure` + `durable.test_durable` +
`durable.test_economics_binding`, 98 tests), readiness codec/canonical
(`verify_canonical.py`, `verify_commerce.py` PASS), onsale HMAC precedent
(`onsale/tokens.py` pattern reused, not duplicated).

New coverage (contract-predicate gaps only): 54 database-free tests covering
cut-vs-watermark separation, mode metadata, fail-closed
integrity/authentication, anti-rollback, type mapping and audit trace; plus
13 PG-bound tests covering snapshot isolation, restart re-export determinism,
incremental cursors/redelivery, CRC corruption, schema drift, writer-lock
independence and real provenance values.

## Commands actually run and results

### Local CI-equivalent battery (protocol.yml + ktx-kernel.yml)

All commands ran in the foreground on this worktree; logs under
`.local/verification/` (gitignored). `.venv/bin/python` steps ran with
`python3` because no bootstrap `.venv` exists locally (deviation recorded
below).

| Command | Result |
|---|---|
| `python3 -m unittest authenticated_export.test_pure` | 54 tests, OK |
| `python3 -m unittest authenticated_export.test_export` | 13 tests, OK (pinned local PostgreSQL 17.11, unix socket) |
| `python3 scripts/stage7_local_check.py validation/2026-11-12-k-stage7-authenticated-export` | 67 tests, `ok: true` |
| `python3 -m compileall -q authenticated_export scripts/stage7_local_check.py` | OK |
| Stdlib offline document checks — the full authoritative run block (32 checkers plain + `--self-test`, plus `check_stage5_host.py --self-test`) | all exit 0; `check_docs_index` earlier failed only on this missing record path, then passed after it was written |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 139 tests, OK |
| `python3 -m unittest integration_gate.test_offline_limits` | 9 tests, OK |
| Reference suite loop (protocol.yml): `settlement_f01_f03` 224, `booking_resale_admission` 954, `credit_advance_f04` 230, `ai_delegation` 169, `token_reward` 397, `provider_facts` 86, `payment_effects` 28, `economics` 99 | 2187 tests, all OK |
| `python3 -m unittest durable.test_pure` / `durable.test_durable` + `durable.test_economics_binding` | 30 / 68 tests, OK (composed layer regression) |
| `check_openapi_contract.py` (+`--self-test`), `check_integration_gate_openapi.py` (+`--self-test`) | pass; `commands=84 core=40 fsm=44`, `productionEndpoint=false publicHost=false` |
| `check_sdk_client.py` (+`--self-test`) | `sdk client pin ok: commands=84 node=24.22.1` |
| `npm --prefix sdk run conformance` | 7 tests, 7 pass, 0 fail |
| `npm --prefix sdk run verify-compat` | `ok: true`, BOOTSTRAP bootstrap-2 |
| `python3 scripts/verify_commerce.py --report .local/verification/commerce.json` | `result: PASS` (CALCULATION_ONLY, externalCalls 0) |
| `python3 scripts/verify_canonical.py --report .local/verification/canonical.json` | `result: PASS` |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 139 passed, 0 failed (log: `.local/verification/ktx/kernel-tests.log`) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 339 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| `python3 scripts/probe_paid_storage.py --python /usr/bin/python3 --directory .local/storage-probe --cycles 3 --report …` | `NO_FAILURE_REPRODUCED` |
| `python3 scripts/reproduce_storage_rollback.py --report …` | `INJECTED_ROLLBACK_REJECTED_BEFORE_CANCELLATION` |
| `python3 scripts/verify_paid_recovery.py --report …` | `PASSED`, 2 cases, SYNTHETIC chain, MOCK money |
| `/usr/bin/python3 scripts/verify_paid_archive.py --report …` | `PASSED`, 2 cases, SYNTHETIC chain, MOCK money |

**Merge-tree note:** this branch HEAD equals the observed `origin/main`
(`d34c316`), so there is no base delta to simulate; the working tree checked
here is the delivery content. If main moves before the supervisor pushes, the
battery must be re-checked on the actual merge tree.

### NOT_RUN locally (and why)

- `bash scripts/bootstrap.sh` — installs the pinned Sui CLI and locked
  dependencies over the network; the supervisor rule forbids network actions.
- `.venv/bin/python scripts/verify_runtime.py`, `scripts/run_localnet.py`
  (plain/`--paid`/`--private`) and ZK steps (`setup:zk`, `test:zk`, phase-1
  cache) — need the bootstrap `.venv`, snarkjs dependencies and a local chain;
  none present and no network provisioning is authorized. No Sui
  testnet/mainnet is touched.
- Exact-head KTX/KIX CI — the supervisor commits and pushes; both workflows
  must run on the final head. No CI run ID exists yet and none is claimed.

## Characterizations (contract-undefined, class B — recorded, not invented)

- `table-keyset/1` ranges are ordered by the primary key, not insertion time:
  a row inserted **below** `startCursor` after the prior export is outside the
  delta range (non-append-monotonic keys like `ledger.entry_id`, sha256-derived
  ids). The prefix watermark counts everything `<= endCursor` as covered by
  the cursor claim, so such an insert is not reported as lag — consumers
  needing gap-free catch-up use FULL_SNAPSHOT. Pinned by the PG suite and
  documented in the package README.
- A partial incremental prefix hash is an authenticated statement about the
  source: a consumer without source access checks count ordering, boundary
  equality and lag arithmetic locally, but re-deriving a partial prefix hash
  requires re-reading the source. Caught-up incremental exports (startCursor
  all null, count == cut) are re-hashed against the cut locally.
- `exportSeq` travels beside the manifest (transport ordinal), not inside the
  signed body — binding a sequence into a signed production manifest is part
  of the undecided anti-rollback policy.
- Local Python is 3.13.5 while `protocol.yml` pins 3.12; the stdlib-only
  checks and suites ran on 3.13.5. Recorded as a deviation, not a CI claim.

## Contract violations found

None. No locked file, frozen reference layer or authoritative contract was
changed to make a test pass; `durable/` and every composed layer are
byte-identical to their merged copies.

## Non-claims and open values

No real funds, real PG/bank/KYC calls, public endpoints, Sui testnet/mainnet,
R2 or own replication/consensus/storage engine, new coin/TIX module, secrets
or production runtime. No production durability, distributed fencing, bank
exactly-once, chain finality, legal compliance or production readiness is
inferred; all execution flags are false and `LOCAL_EXPORT_FIXTURE_ONLY` is
true. Open values stay `DECISION_REQUIRED · Astra`: production signing scheme
and trust root/registry, anti-rollback *policy* (the registry here is a local
consumer-side fixture), a registered production manifest wire schema,
multi-shard consistent-cut/coordinator protocol, and any SLO/retention/
frequency value. No Arrow/Parquet materialization happened in this node
(next node `k-stage7-cpu-analytics-sql-audit`).

## Remaining uncertainty and follow-up candidates

- Exact-head CI on the supervisor's final head (both workflows) is still
  required.
- The PG-bound suite requires the owner-provisioned pin; it skips gracefully
  elsewhere and is deliberately not CI-wired (owner decision: no CI may
  require PostgreSQL).
- Astra decisions on the open values above before any production-facing use.
