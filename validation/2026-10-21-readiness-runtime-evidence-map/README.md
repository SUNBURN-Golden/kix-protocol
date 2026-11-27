# readiness-runtime-evidence-map

Node: `plan-plan-readiness-contract-evidence-map`. Adds `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`, one row per clause of `docs/contracts/READINESS_RUNTIME.md` (5 marker flags, 7 journal/record clauses, 2 migration clauses, 7 integration-gate clauses, 6 "이 경계가 보인 것" checks, 3 class-B open items, 6 `보류` items — 36 rows), and `scripts/check_readiness_evidence_map.py` (stdlib only, `--self-test`), wired into the unguarded `Stdlib offline document checks` step of `.github/workflows/protocol.yml` after the `check_v5_transition_evidence_map.py` lines.

Issue: none. Depends on: `k-readiness-conformance-suite`, `readiness-extensions`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session; no ASTRA markers posted.
Source: KIX planner run 1792541948 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files. Exact-head CI belongs in the PR closure report (AGENTS section 11).

Observed `origin/main` = branch HEAD = `91d2e507362a79834c09790d9f379ee15f2a1453`. `git fetch origin main` was not run (this session forbids network actions); the value is the local `origin/main` ref. Branch `agent/kix-plan-plan-readiness-contract-evidence-map`.

**This record and the map are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, the operational count stays 0, no readiness or gate source is changed, no open item is reclassified, and no Move, ZK, localnet, Sui or Node run was made.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker recomputes both blobs on every run. Nothing under `runtime/`, `reference/` (so `reference/v0.3-rc1/` too), `readiness/`, `integration_gate/`, `.aiops/`, `docs/tasks/`, `docs/contracts/` or `docs/decisions/` changed.

## What this change does

- The map has 36 rows: 25 `EXERCISED`, 2 `PARTIAL`, 0 `NOT_EXERCISED`, 9 `OPEN`. Statuses are builder readings of the cited fixtures; Astra may reclassify.
- Each fixture/impl cell is `none` or `path::symbol` citations; the missing-or-open cell is plain text; the owner cell is `none` or `;`-separated owners written verbatim in the contract, `readiness/CONFORMANCE.md` or `docs/decisions/PROGRAM_DECISIONS_20260928.md`, except the reserved literal `DECISION_REQUIRED · Astra`.
- The three class-B characterizations (mid-frame length-prefix corruption read as torn tail, 0-byte journal re-initialisation, clean frame-boundary cuts) stay `OPEN` with owner `Astra` — the pending Astra ruling on the contract's recovery clause. The six `보류` items stay `OPEN` with their lock owners (`사용자 승인`, `사용자 명시 승인`, `DECISION_REQUIRED · Astra`). The map reclassifies none of them, and the checker reserves `OPEN` to those nine ids and forces them to keep it.
- `readiness/test_conformance_sensitivity.py` does not exist at this base; its column is `none` in every row and a future citation into it is checked by the ordinary existence rule.
- The checker verifies the hardcoded ids and their contract anchor strings, ten-cell row width, cell grammar, status-versus-cell consistency, citation path existence, column path prefixes (never under `reference/v0.3-rc1/`), symbol definitions (`def`/`class`/constant for Python, exact text for Markdown), owner naming against the three owner sources, the banner phrases, the two locked blobs and the counts line. `--self-test` requires each deliberate break to be caught.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md` | New map, 36 rows. |
| `scripts/check_readiness_evidence_map.py` | New checker, stdlib only. |
| `.github/workflows/protocol.yml` | Two added lines at the end of the stdlib step. |
| `docs/README.md` | One row in the 2026-10-21 section linking the map and this record. |
| `validation/2026-10-21-readiness-runtime-evidence-map/README.md` | This record. |

## AGENTS.md section 7: existing coverage per row

| ID | Map status | Section 7 class | Missing |
|---|---|---|---|
| FLAG-PROTOCOL-TRUTH | `EXERCISED` | sufficiently covered | none |
| FLAG-PROD-CONFORMANCE | `EXERCISED` | sufficiently covered | none |
| FLAG-PROD-READINESS | `EXERCISED` | sufficiently covered | none |
| FLAG-PROD-ENDPOINT | `EXERCISED` | sufficiently covered | none |
| FLAG-FSM-DURABLE | `EXERCISED` | sufficiently covered | none |
| JRN-FRAME-FSYNC | `EXERCISED` | sufficiently covered | none |
| JRN-SINGLE-WRITER | `EXERCISED` | sufficiently covered | none |
| RCV-TORN-TAIL | `EXERCISED` | sufficiently covered | none |
| RCV-CHECKSUM-CLOSED | `EXERCISED` | sufficiently covered | none |
| REC-FSM-ENTRY | `EXERCISED` | sufficiently covered | none |
| REC-CORE-COMMIT | `PARTIAL` | partially covered | The core_commit shape and replay are exercised; no fixture flips a stored receipt digest, so RECEIPT_MISMATCH and the diverged observation are unexercised. |
| REPLAY-IDEMPOTENT | `EXERCISED` | sufficiently covered | none |
| MIG-READ-PATH | `EXERCISED` | sufficiently covered | none |
| MIG-EXPLICIT | `EXERCISED` | sufficiently covered | none |
| GATE-LOOPBACK | `EXERCISED` | sufficiently covered | none |
| GATE-CONCURRENCY | `EXERCISED` | sufficiently covered | none |
| GATE-DRAIN | `EXERCISED` | sufficiently covered | none |
| OBS-AUDIT | `PARTIAL` | partially covered | The replayed, inactive and diverged journalDecision values are not asserted by any fixture. |
| GATE-RESTART-LOSS | `EXERCISED` | sufficiently covered | none |
| BUDGET-LIMITS | `EXERCISED` | sufficiently covered | none |
| GATE-BROWSER-OPTIN | `EXERCISED` | sufficiently covered | none |
| SEEN-SETTLEMENT … SEEN-GATE-REKILL (6 rows) | `EXERCISED` | sufficiently covered | none |
| OPEN-LENPREFIX-MIDFRAME, OPEN-ZERO-BYTE-REINIT, OPEN-FRAME-BOUNDARY-CUT | `OPEN` | contract undefined | Class-B characterizations; classification waits on the pending Astra ruling on the recovery clause. |
| HOLD-PUBLIC-DEPLOY … HOLD-NEW-COMMANDS (6 rows) | `OPEN` | held by the §5 program locks | Unlock conditions (user approval; a documented backend comparison for R2; an authorized decision for a production claim) are unmet. |

Totals: 27 rows sufficiently or partially covered by existing fixtures, 9 contract-open/held rows the map leaves open.

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** The 25 `EXERCISED` rows: the cited fixtures exercise each clause as written (builder reading; the checker proves only that cited names exist).

**B. Contract undefined (characterizations; nothing amended).**

1. The three class-B items from the journal byte sweep stay `OPEN`: mid-frame length-prefix damage parsed as a torn tail dropping later acknowledged frames, 0-byte journal re-initialisation, and clean frame-boundary truncation being undetectable. The contract's recovery clause defines only a trailing incomplete frame and a complete frame with a bad checksum; the Astra ruling on it is pending.
2. `RECEIPT_MISMATCH` and the `diverged`/`replayed`/`inactive` `journalDecision` values exist in `integration_gate/server.py` and `recovery.py` but are unexercised — recorded as `PARTIAL` coverage gaps owned by `k-readiness-conformance-suite`, not as contract changes.
3. The boundary emits `unchanged`/`fault` `journalDecision` values outside the contract's six-value audit list; the map does not treat that as a violation — the list describes the gate's local-call audit line.

**C. Explicit contract violation:** none found.

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main` | Both `91d2e507362a79834c09790d9f379ee15f2a1453`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. `readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9`. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. Unmodified map passes; all 21 mutation cases plus the injected locked-blob mutation and the removed contract anchor detected; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Exit 0. |
| `python3 scripts/check_status_register.py` and `--self-test` | Exit 0. |
| All other stdlib document checks in the same workflow step (rs_profile_traceability, read_model_source_map, i12_proof_ids, delegation_layer_matrix, rs_predicate_evidence_map, rs_im_evidence_map, tl_predicate_evidence_map, contract_error_codes, adapter_identity_map, v5_transition_evidence_map), each plain and `--self-test` | All exit 0. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | `OK` — the CI entry point, unchanged. |
| `python3 -m unittest readiness.test_faults` alone | `OK`. |
| `git status --porcelain reference/v0.3-rc1 readiness integration_gate runtime` | Empty — none of those paths changed. |
| `cd runtime && cargo fmt --all -- --check`; `cargo test -p kix-kernel --locked --offline`; `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | fmt exit 0; all test binaries `ok` (last shown: 32 passed, 0 failed); clippy finished with no warnings. (`--offline` because the session has no network; nothing under `runtime/` changed.) |
| Move (`sui move test`), localnet, ZK, Node SDK jobs; exact-head KTX kernel verification and KIX protocol verification | **Not run.** No Sui binary or network use in this session and there is no pushed head; this PR's diff touches `scripts/` and `.github/workflows/`, which the path classifier forces into full verification hosted. |

## Non-claims

- Not an Astra review; the contract stays unchanged and the capability register is unchanged (`CURRENT_CAPABILITY_REGISTER.md`'s checker list is a dated snapshot, explicitly not auto-synced — left for a register-sync node).
- The map names which existing fixtures touch each clause. It runs none of them, proves no assertion, decides no classification, reclassifies no open item and raises no grade; the operational count stays 0.
- No claim of production durability, power loss, OS crash, `fsync` correctness, chain finality, external exactly-once, distributed fencing or production readiness; all fixtures are controlled single-process local files and loopback HTTP. Nothing under `reference/v0.3-rc1/` is cited and both locked blobs are unchanged.
