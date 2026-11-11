# k-stage5-durable-tx — durable layer on the adopted local PostgreSQL

Node: `k-stage5-durable-tx`. Not an ASTRA program-mode session. No issue. No commit,
push, pull request, or comment in this session (the supervisor does git/GitHub).
Record opened 2026-10-13; acceptance rerun and this update 2026-11-12.
Branch: `agent/kix-k-stage5-durable-tx`.

**State: acceptance passed locally — `merge-ready` candidate pending supervisor
commit/push and exact-head CI.** Both acceptance commands ran green on the adopted
backend: `python3 -m unittest durable.test_durable` (58 tests, OK) and
`python3 scripts/stage5_local_check.py validation/2026-10-13-k-stage5-durable-tx`
(88 tests, OK, exit 0, `summary.json` `ok: true`, observed version exactly the pin).
The readiness `BackendConformance` suite (12 cases) is bound to
`DurablePostgresBackend` and passes on PostgreSQL 17.11. Nothing here is exact-head
CI; the two workflows must still run on the final head after the supervisor pushes.
No production readiness is claimed.

## Owner decision and provisioning (this session)

- Owner decision, 2026-11-10 17:25 KST (준태님, "설치해"): **Option 1 — provision the
  pinned backend and rerun.** The decision records PostgreSQL 17.11
  (Debian 17.11-0+deb13u1) at `/usr/lib/postgresql/17/bin/{postgres,initdb}`,
  python3-psycopg 3.2.6, no default system cluster, service disabled.
- The earlier blocked attempt (see "Historical" below) found this host had only
  `postgresql-client-17`: no server binaries, no `psycopg`. Under the owner's
  authorization the exact pinned packages were (re-)provisioned:
  - `sudo apt-get update` failed (HTTP 500 through the egress proxy), and apt over
    HTTPS also failed (SSL unexpected EOF) while curl over HTTPS worked. The URIs in
    `/etc/apt/sources.list.d/debian.sources` were switched http→https, then the
    package index and 11 `.deb` files were downloaded with curl from
    `https://deb.debian.org/debian` into `/tmp/s5-debs` and installed with
    `sudo DEBIAN_FRONTEND=noninteractive dpkg -i /tmp/s5-debs/*.deb`.
  - Installed: `postgresql-17` 17.11-0+deb13u1, `postgresql-client-17`
    17.11-0+deb13u1, `python3-psycopg` 3.2.6-1, `postgresql-common` 278,
    `postgresql-common-dev` 278, `ssl-cert` 1.1.3, `libjson-perl` 4.10000-1,
    `locales` 2.41-12+deb13u4, `libc-l10n` 2.41-12+deb13u4, `libipc-run-perl`
    20231003.0-2, `libio-pty-perl` 1.20-1+b3, `python3-typing-extensions` 4.13.2-1.
  - dpkg auto-created a default cluster `17/main`; it was dropped
    (`sudo pg_dropcluster 17 main`) and the service disabled
    (`sudo systemctl disable postgresql`), matching the owner-recorded host state:
    no default cluster, no TCP listener. Test clusters are started per-run by
    `exploration/stage4/clusters.py` with `listen_addresses=''` (unix socket only).
- These are host changes outside the repository, authorized by the owner decision.
  No repository file, workflow or CI definition was changed for provisioning.
- `DECISION_REQUIRED.md` (root) was removed after the decision; it is absent at the
  final worktree state and was never committed.

## Decision applicability guard (CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md §5.1)

- `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 (Korean original in the file;
  English rendering, not a quotation): if merged without edits, only option A is adopted; the
  adopted backend is the local, non-production PostgreSQL 17.11 (Debian 17.11-0+deb13u1) of
  stage 5; single process, single writer, default off, production flags false, R2 /
  replication / consensus not opened, stopped items stay stopped. This is ADOPT with a named
  backend. The sentence is present unedited in the merged file.
- Merge commit `bb193efb5d238581096372c8a20bee1271dfe4df` (PR #140, parent
  `6e54e723…`) is an ancestor of this branch HEAD. `git diff bb193efb HEAD --
  docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` is empty: the file is unchanged
  since the merge. `docs/DEVELOPMENT_PLAN.md` records the same sentence and the merge
  in its 2026-10-09 table.
- Other dependency `k-stage2-v5-impl`: `runtime/crates/kix-kernel-v5` exists on HEAD
  (merge `4813388`, PR #179). This node does not read or edit it.
- The node spec's old line numbers (`DEVELOPMENT_PLAN` ~109, 268–275) do not match the
  current plan; the adoption proposal §7 names the current ones (§5 row 112, §10).
  This node followed §10 and ADR-0001 Appendix B (lines 147–151).

## Base (AGENTS §1)

- Task branch HEAD: `4813388b5bcde72c298c7392ff5230316da44470` (merge of PR #179).
- Observed `origin/main`: `c0464f54bee6253e376b635103e698ef02b8f417`, **read from the
  local remote-tracking ref**. `git fetch origin main` was not run: the supervisor
  rule for this session forbids network actions, so the true current main may be
  newer still.
- **Delta (AGENTS §1):** HEAD is an ancestor of the observed `origin/main`;
  `git rev-list --count HEAD..origin/main` = **527 commits**. Per §1 the delta is
  reported, not silently rebased or merged. The three new paths (`durable/`,
  `scripts/stage5_local_check.py`, `validation/2026-10-13-k-stage5-durable-tx/`) do
  not exist on the observed `origin/main` (`git ls-tree` empty), so no path conflict
  is expected; the supervisor decides how to deliver against current main.
- No implementation commit SHA and no final task head exist yet (the supervisor
  commits). Nothing here is exact-head CI.
- Tools: `rustc`/`cargo` 1.98.1 (workflow pin); `python3` 3.13.5 (`protocol.yml` pins
  3.12 — deviation recorded below); node v24.22.1 (CI: 24); PostgreSQL 17.11
  (Debian 17.11-0+deb13u1); psycopg 3.2.6.

Locked blobs, before the edits and after the last edit/verification run, identical:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat HEAD --` over `runtime reference/v0.3-rc1 .aiops .github docs exploration
readiness integration_gate` is empty. `git status --porcelain` lists only the three new
paths below (`__pycache__` and `.local/` are gitignored).

## Changed paths (all new; nothing existing is edited)

| Path | Role |
|---|---|
| `durable/__init__.py` | Flags (all false) and the backend pin string. |
| `durable/errors.py` | `CommitUnknown`, `Backpressure`, `UnknownOperation`, `AliasConflict`, `NormalizationError`. |
| `durable/budgets.py` | `ClassLimit`, `BudgetSpec`: count/bytes/age for `inflow`, `completion`, `observation`, `cancel`, `recovery`. Every number is required from the caller. |
| `durable/model.py` | Pure admission decision (replay, conflict evidence, capacity, business rejection, new success). |
| `durable/normalize.py` | Per-item normalization, `evidence_hash`, alias resolution with a conflict check. |
| `durable/schema.py` | Tables, per-row CRC, single-writer file lock, serializable transactions, budget ledger. |
| `durable/unit.py` | `DurableUnit.apply`: one transaction for command, payload sha256, first result, slot, minimal order, outbox intent. |
| `durable/inbox.py` | Durable inbox: raw first, then items and aliases, then the apply hook, then the ACK. |
| `durable/outbox.py` | Attempt recorded before dispatch, outcome after; default dispatcher is a fixture that calls nothing. |
| `durable/cluster.py` | `PinnedPostgresCluster`: the stage-4 local cluster plus a fail-closed pin check. |
| `durable/backend.py` | Conformance adapter: stage-4 `PostgresAdapter` reused, plus `open_unit`. |
| `durable/test_pure.py` | 30 database-free tests. |
| `durable/test_durable.py` | 58 PostgreSQL-bound tests, including the `BackendConformance` binding. |
| `durable/run.py`, `scripts/stage5_local_check.py` | Local acceptance runner: `host.json` + `summary.json`. |
| `validation/2026-10-13-k-stage5-durable-tx/README.md` | This record. |
| `validation/2026-10-13-k-stage5-durable-tx/host.json` | Host evidence: git SHAs, package versions, locked-blob match, flags. |
| `validation/2026-10-13-k-stage5-durable-tx/summary.json` | Acceptance summary: `ok: true`, 88/0/0/0, observed pin and settings, all production flags false. |

`runtime/**`, `readiness/**`, `exploration/**`, `reference/**`, `.github/**`, `.aiops/**`,
`docs/**`, `integration_gate/**` are untouched. No workflow change; the new suites are not
wired into CI (like `exploration.stage4.test_stage4`, they need local PostgreSQL — per the
owner decision, no CI that needs PostgreSQL was added). `docs/README.md` and the plan are
not edited, so the doc index check is unaffected.

## What the layer does

- **Durable transaction.** One SERIALIZABLE transaction commits `command_result` (id,
  payload sha256, first result, outcome, u128 amount as decimal text), `slot_hold`,
  `minimal_order`, `outbox_intent` and the budget `ledger` row. Replay returns the stored
  first result and adds no row. A conflicting payload for a known command id is a separate
  `observation` row and the first result is returned unchanged. Capacity writes nothing.
  A taken slot stores the command with no order and no intent.
- **Commit uncertainty.** A `COMMIT` that fails after it was sent is `outcome: "unknown"`
  and closes the session. It is never reported as not applied; the next apply of the same
  command id reads the truth.
- **Inbox** (ADR-0001 Appendix B). Raw bytes, raw sha256, scope (provider, account,
  environment, profile version), headers, receive time and the caller's verification
  result are committed first; then the authenticated-lookup hook runs and the per-item
  rows are committed; then the apply hook; then the ACK. Persist failure, unknown commit
  or a full budget raises `Backpressure`: no ACK, no apply. `UnknownOperation` (or a fact
  with no operation reference) leaves the item `UNMATCHED`, never deleted, never marked
  applied; `reconcile` replays the stored raw once a binding exists. A known event key
  with a different fact is stored as a `CONFLICT` item with its own raw; the first item is
  never overwritten. A different raw with the same fact is `SAME_FACT`, kept as raw
  evidence, not a conflict. State is an append-only log.
- **Outbox.** Intents are committed with the business result and survive a process kill.
  `record_attempt` commits an `ATTEMPTING` row before calling the injected dispatcher and an
  `OUTCOME` row after. A dispatcher exception or a malformed result is `UNKNOWN`. A retry
  reuses the same intent id (the stable operation identity) and is charged to `recovery`.
  A `DISPATCHED` intent is never sent twice.
- **Per-item normalization.** One fact and one `evidence_hash` per item; amounts are KRW
  integers (bool, float, numeric string, negative and over-u128 are refused); the occurred
  time keeps its original text and offset or `None`; no zone is assumed; delivery id,
  receive time and retry count are not inputs; the alias table (`event_alias`) is durable,
  scoped, and refuses a collision.
- **Budgets.** Five classes, each with count, bytes and age, all supplied by the caller;
  the constructor fails without them. New command and inbox arrival are `inflow`; conflict
  and extra raw evidence are `observation`; the first dispatch attempt is `completion`;
  later attempts are `recovery`. A full `inflow` budget does not stop replay, conflict
  evidence or the outbox. The budget is pinned in `meta`; reopening with a different one is
  refused. Age is measured against the caller-supplied `now_ms`; no clock is read.
- **Fail closed.** Every table row carries a CRC-32 over its immutable columns (the raw
  blob is bound by its sha256). Opening a store verifies all rows; a mismatch is
  `CHECKSUM_MISMATCH`.

## Existing coverage first (AGENTS §7)

| Requirement | Existing coverage | Class | Action |
|---|---|---|---|
| Torn write, crash before durable, restart, replay idempotence, concurrent hold, budget predicate | `readiness/conformance.py` `BackendConformance` (12 cases) | sufficient as the contract | Bound to `DurablePostgresBackend` in `durable/test_durable.py::DurableConformance`; **run and passing on the pinned PostgreSQL 17.11** (12 cases + pin/settings test). |
| Local PostgreSQL record store, FSM boundary, checksum on `rec` | `exploration/stage4/test_stage4.py` (2026-10-08 record, PostgreSQL 17.11) | partial (exploration data, not re-run) | Reused unchanged through `PostgresAdapter`. |
| Business mapping on one local transaction, replay after capacity, process-kill replay, u128 text | `exploration/stage4` `PostgresUnit` + `test_stage4.py` | partial (synthetic unit, no outbox rows, no inbox) | Re-implemented with the outbox row and budget classes. |
| Kernel dedup / `Conflict` / `UnknownOperation` semantics | `runtime/crates/kix-kernel/tests/*` (locked v4) | sufficient for the kernel; says nothing about the adapter | Cited in `docs/contracts/ADAPTER_EVENT_IDENTITY.md` §10.1. Not duplicated. |
| Inbox custody, `UNMATCHED`, ACK ordering, per-item identity, alias table, outbox before dispatch, class-separated budgets | none (`ADAPTER_EVENT_IDENTITY.md` §10.1: "미커버") | **not covered** | New tests below. |

## New tests and the gap each addresses

`durable/test_pure.py` (30, no database): budget slots are required and typed; check order
count→bytes→age; class independence in `decide`; replay is free when full; u128 text; flags
false; per-item facts; amount, time and scope rules; alias collision; no provider JSON field
name in `normalize.py`.

`durable/test_durable.py` (58, needs PostgreSQL): the 12 conformance cases plus the pin
check; atomic unit and injected-failure rollback; restart and process-kill replay; commit
with a lost response (unknown, effect read back) and a commit that never arrived; u128
round trip; business rejection; conflict retained once; a corrupt row in each of the 11
checksummed tables fails closed; second writer refused; budget pin mismatch refused; flags;
class-separated budgets including age and recovery; inbox ordering (raw committed before the
apply hook, seen through a second connection), batch identities and alias durability,
`UNMATCHED` and reconcile, persist failure and unknown commit and full budget → no ACK, same
key different fact kept as conflict, same fact different bytes not a conflict, identical
redelivery, lookup failure, failed apply and redelivery, process kill; outbox survival across
kill, attempt committed before dispatch, default dispatcher, terminal `DISPATCHED`, `UNKNOWN`
retry keeps identity, attempt without outcome after kill, unrecorded outcome, unknown intent,
completion budget stops before dispatch.

## Commands actually run (AGENTS §9, §14)

Local results only, on this host, after provisioning. None is exact-head CI. The
acceptance runs and the full local CI-equivalent battery below were all run in the
foreground in this session and all passed; no test failed at any point after
provisioning, so no fix-and-rerun cycle was needed.

### Acceptance (node criterion)

| Command | Result |
|---|---|
| `python3 -m unittest durable.test_pure` | Ran 30 tests, OK |
| `python3 -m unittest durable.test_durable` | Ran 58 tests in 7.338s, OK (includes the 12 `BackendConformance` cases on PostgreSQL 17.11) |
| `python3 scripts/stage5_local_check.py validation/2026-10-13-k-stage5-durable-tx` | Ran 88 tests in 5.233s, OK; exit 0; `summary.json` `ok: true`, `tests: 88 ran / 0 failures / 0 errors / 0 skipped`, `observed_version` = "PostgreSQL 17.11 (Debian 17.11-0+deb13u1) on x86_64-pc-linux-gnu …"; fsync / full_page_writes / synchronous_commit / data_checksums on, autovacuum off, `listen_addresses` empty; all production flags false |
| `git hash-object` of the two locked files, before and after all work | `69564b16…`, `b607996c…`; match both times |

### Local equivalents of `ktx-kernel.yml`

| Command | Result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | "architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified" |
| `python3 scripts/test_runtime_architecture.py` | Ran 7 tests, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; 78 passed, 0 failed over 9 result lines (8+3+12+11+4+8+32) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0, no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo tree … -p kix-kernel --edges normal --locked` + `sha256sum` (dependency evidence) | exit 0; written to gitignored `.local/verification/ktx/` |

### Local equivalents of `protocol.yml`

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` (+ `--self-test`) | ok (paths=171 ev_ids=12 original32=32) / pass |
| `python3 scripts/check_rs_profile_traceability.py` (+ `--self-test`) | ok (47/47/47) / pass |
| `python3 scripts/check_read_model_source_map.py` (+ `--self-test`) | ok (queries=13 anchors=128 citations=145) / pass |
| `python3 scripts/check_docs_index.py` (+ `--self-test`) | ok (scanned=65 indexed=62 allowlisted=3) / pass |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Ran 58 tests in 4.012s, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for settlement_f01_f03, booking_resale_admission, credit_advance_f04, ai_delegation, token_reward | OK: 22, 47, 26, 22, 61 tests |
| `python3 scripts/check_openapi_contract.py` (+ `--self-test`) | ok (commands=84 core=40 fsm=44, sha256 `ed827de1…`) / pass |
| `python3 scripts/check_integration_gate_openapi.py` (+ `--self-test`) | ok (commands=84 productionEndpoint=false publicHost=false) / pass |
| `python3 scripts/check_sdk_client.py` (+ `--self-test`) | ok (commands=84 node=24.22.1) / pass |
| `npm --prefix sdk run conformance` | 6 tests, 6 pass, 0 fail; exit 0 (no dependencies; plain node) |
| `npm --prefix sdk run verify-compat` | `{"ok":true,…,"profile_kind":"BOOTSTRAP","profile_revision":"bootstrap-2"}`; exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0; 183 passed, 0 failed over 30 result lines |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0, no warnings |
| `python3 scripts/verify_commerce.py --report .local/verification/commerce.json` | PASS, `CALCULATION_ONLY`, externalCalls=0; exit 0 |
| `python3 scripts/verify_canonical.py --report .local/verification/canonical.json` | PASS; exit 0 |
| `python3 scripts/probe_paid_storage.py --python /usr/bin/python3 --directory .local/storage-probe --cycles 3 --report .local/verification/storage-probe.json` | exit 0; `NO_FAILURE_REPRODUCED`, money=MOCK, chain=SYNTHETIC, 66 commands |
| `python3 scripts/reproduce_storage_rollback.py --report .local/verification/storage-rollback.json` | exit 0; `INJECTED_ROLLBACK_REJECTED_BEFORE_CANCELLATION`, money=MOCK |
| `python3 -m compileall -q durable scripts/stage5_local_check.py` | exit 0 |

The last four contract scripts run in CI under `.venv/bin/python` (3.12); here they ran
under the system `python3` 3.13.5 with `PYTHONDONTWRITEBYTECODE=1`. They import only
stdlib and repo-local modules; the reference tree stayed byte-identical (verified by
`git diff`/`git status` afterwards). Reports went to gitignored `.local/`, not into the
repository.

### NOT_RUN, with reasons

| CI step | Why not run locally |
|---|---|
| `bash scripts/bootstrap.sh` | Asserts Python 3.12 exactly (host: 3.13.5); creates `.venv` and installs pip/npm/Sui tooling over the network, which this session may not do. |
| `.venv/bin/python scripts/verify_runtime.py` | Needs the `sui` binary (Move tests) and `.venv`; neither exists here. |
| `.venv/bin/python scripts/run_localnet.py` (default, `--paid`, `--private`) | Needs `sui`, PyYAML and `.venv`; a disposable local chain is out of this node's scope. |
| `npm --prefix reference/v0.3-rc1/client run setup:zk` / `test:zk` | Need a network `npm install` and snarkjs inside `reference/v0.3-rc1`, which must stay byte-identical. |
| Exact-head KTX kernel / KIX protocol CI | The supervisor commits and pushes; the workflows must run on the final head (AGENTS §10). A draft/skipped run is not a pass. |

### Historical: the earlier blocked attempt (superseded, kept per AGENTS §6)

Before the owner decision, this host had no PostgreSQL server binaries and no
`psycopg`. The actual results then were: `python3 -m unittest durable.test_durable`
FAILED with `ModuleNotFoundError: No module named 'psycopg'` at
`durable/test_durable.py:16`; `python3 scripts/stage5_local_check.py /tmp/s5out`
exited 1 with `summary.json` `ok: false`, `tests.ran: 31`, `errors: 1`,
`backend.observed_version: null` (output went to `/tmp`, not the repository). A root
`DECISION_REQUIRED.md` recorded the blocker and options. The owner chose Option 1
("설치해", 2026-11-10); the backend was provisioned as recorded above, both acceptance
commands were rerun green, and `DECISION_REQUIRED.md` was removed. The failed runs
above are history, not current evidence; the current evidence is the acceptance table.

### Developer smoke run on a stand-in (NOT evidence)

To shake out SQL and logic bugs before handoff, `durable/test_durable.py` was run in `/tmp`
against a throwaway `psycopg` stand-in written over **sqlite3** (outside the repository, not
committed): 57 of the 58 tests ran (the pin test needs the real process) and all passed; four
deliberate mutations of a scratch copy (drop the intent insert, treat `UnknownOperation` as
applied, remove the alias collision check, class a conflict as the same fact) were each
caught. sqlite is not PostgreSQL: it has no serializable isolation, no real process kill and
a different SQL dialect. This run says nothing about the adopted backend and is not offered
as acceptance evidence.

## Contract violations found

None. No discovered behavior required a locked-file change.

## Contract-undefined characterizations (AGENTS §8 B) — nothing invented, only recorded

- **`EventItemId` source and the 16-byte alias rule** stay `DECISION_REQUIRED · Astra`
  (`ADAPTER_EVENT_IDENTITY.md` §9) and TM04 stays unanswered. This node implements the
  recommended *alias table with a conflict-checked insert*; the candidate value is the first
  16 bytes of SHA-256 of `[scope, fact_key]` and is labeled a local fixture rule. The provider
  fact key is an opaque string the adapter supplies; no provider field is named in code.
- **Receipt ACK is conditioned on inbox custody, not on business application.** Appendix B ties
  the ACK to preservation. A failed apply hook (an exception other than `UnknownOperation`) also
  withholds the ACK so the provider redelivers; this is a choice for safety, not a contract text.
- **Raw arrival is charged to `inflow`**, even when it later turns out to carry only conflict
  evidence, because the raw must be committed before the lookup that reveals the item keys.
  Extra evidence items are charged to `observation`.
- **Age** means the dwell of the oldest still-open ledger entry of a class against the caller's
  `now_ms`. An inflow entry closes when its intent is `DISPATCHED` (or the inbox delivery has no
  `RECEIVED`/`UNMATCHED` item). With the fixture dispatcher no intent is ever dispatched, so such
  entries stay open. `observation` entries never close (no review release exists).
- **`cancel` class** is a required slot with no writer: no cancel command exists and a new
  protocol command is `DECISION_REQUIRED · Astra`.
- **Conflict items are offered to the apply hook** like first items; whether the adapter withholds
  them from the kernel is the integrator's policy.
- **`runtime/ARCHITECTURE.toml` says `oltp_major = 18`** while the adopted local pin is 17.11
  (the stage-4 record shows 17.11). The file is a verifier input and is not edited here.

## Non-claims

No production readiness, durability equivalence, power or OS crash behavior, hardware flush,
independent failure domain, bank exactly-once, chain finality or legal compliance. Process kill is
the disk-retained SIGKILL of the stage-4 exploration. `protocolTruth`, `productionConformance`,
`productionReadiness`, `productionEndpoint`, `chainWriter`, `fundsExecuted` and FSM `durable`
stay false; `localDurableData: true` is a local label only. No SLO, TPS, p99, RTO, RPO, retention
period, cost or budget number is set; the fixtures in test code are labeled not-product. No R2,
replication, consensus or own storage engine; no real PG, bank, KYC or provider call; no endpoint
other than a unix socket; no Sui testnet or mainnet; no new coin or TIX module; no new protocol
command or wire name; I09, I10, I12, I13 stay open and slot release and state-changing reclamation
stay stopped. The inbox does not authenticate anything (I04).

## Remaining uncertainty and follow-ups

1. Exact-head CI on the final head after the supervisor commits/pushes (both workflows,
   terminal state) — not yet available; this record is local evidence only.
2. The observed `origin/main` is 527 commits ahead of the task base; the supervisor
   decides delivery against current main (no rebase was performed, per AGENTS §1).
3. Plan sync (`DEVELOPMENT_PLAN.md` §10 still says "전부 미착수") belongs to the sync node.
4. Astra decisions on the `EventItemId` source, the alias rule, and the inbox policy for
   conflict items.