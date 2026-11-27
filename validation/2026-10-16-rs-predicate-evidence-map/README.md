# rs-predicate-evidence-map

Node: `plan-rs-predicate-evidence-map`. Adds `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`, one row per predicate RS-C01..RS-C17 and RR-1..RR-6 of `docs/contracts/RIGHTS_SCALE_PROFILE.md` (23 rows), and `scripts/check_rs_predicate_evidence_map.py` (stdlib only, `--self-test`), wired into the unguarded `Stdlib offline document checks` step of `.github/workflows/protocol.yml` next to the delegation-layer-matrix lines.
Issue: none. Depends on: `rs-3b`, `plan-rs0-review-pack`, `plan-delegation-layer-gap-matrix` (#200). Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792148545 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `543c1438ce044479fd9646bc5e1cde933a153a4c`. `git fetch origin main` was not run (this session forbids network actions); the value is the local `origin/main` ref. Branch `agent/kix-plan-rs-predicate-evidence-map`.

**This record and the map are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, the operational count stays 0, no Sui, ZK, localnet, Move, Cargo or Node run was made, and no gap is closed.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Nothing under `runtime/`, `reference/` (so `reference/v0.3-rc1/` too), `readiness/`, `.aiops/`, `docs/tasks/`, `docs/contracts/`, `docs/decisions/` or `docs/blueprints/` changed.

## What this change does

- The map has 23 rows with a closed status: 12 `COVERED_LOCALNET`, 2 `COVERED_MODEL_OR_MEMORY`, 7 `PARTIAL`, 0 `NOT_COVERED`, 2 `MEASUREMENT_ONLY`. Statuses are builder readings of the cited test bodies; Astra may reclassify.
- Column 2 is the proposed test id copied from the profile. The citations are `path::symbol` grouped by layer. RS-C03, RS-C06 and RS-C07 keep their (a)/(b) halves, RS-C14 keeps public/private/delegated; a row takes the weakest of its halves.
- Every `PARTIAL` and `MEASUREMENT_ONLY` row names what is missing in one sentence and an owner written as the profile writes it. No open value is chosen: page size P, shard count S, root history K, revocation window W, `MAX_BUNDLE_CHAIN`, the `IssuerCap` option and a GA redistribution command stay with their owners.
- The checker verifies ids against profile sections 8 and 9, the test id and owner cells against the profile, statuses against citations, path existence and column prefixes (nothing under `reference/v0.3-rc1/`), symbol definitions, the split labels and the counts line. `--self-test` first requires the unmodified map to pass and a Move same-line `#[test] fun` positive control, then requires each of these breaks to be caught: removed id, duplicated id, dangling path, dangling symbol, unknown status, `NOT_COVERED` row with a citation, uncited row that is not `NOT_COVERED`, altered test id, owner not in the profile, empty missing cell on a `PARTIAL` row, citation under `reference/v0.3-rc1`, dropped split label, wrong counts line.
- Not done on purpose: no test added or renamed, no profile or register edit, no gap closed. The capability register records no Astra architecture review for any of these rows and still does not.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` | New map. |
| `scripts/check_rs_predicate_evidence_map.py` | New checker. |
| `.github/workflows/protocol.yml` | Two added lines in the stdlib step. |
| `docs/README.md` | One table row linking the map and this record. |
| `validation/2026-10-16-rs-predicate-evidence-map/README.md` | This record. |

## AGENTS.md section 7: existing coverage per row

"Sufficiently" means every sentence of the predicate has at least one cited test whose body I read; it does not mean accepted. Localnet figures in the cited records are quoted at their own heads.

| ID | Map status | Section 7 class | Missing |
|---|---|---|---|
| RS-C01 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C02 | `PARTIAL` | partially covered | Sentence 2 (redistribution moves two pages in one PTB and keeps the total) has no operation and no test; the package defines no such entry, and a test asserts that absence. |
| RS-C03 | `COVERED_MODEL_OR_MEMORY` | sufficiently covered, model or in-memory only | Half (b) is an in-memory mirror only: there is no R2 fence and no durable stable-identity store behind it. |
| RS-C04 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C05 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C06 | `PARTIAL` | partially covered | Half (b): the order of a grant cut against a delegated consume is exercised only serially (the one localnet race probe covers cancel against issue, half (a)), and no Move test cuts a grant against a paid issue. |
| RS-C07 | `PARTIAL` | partially covered | Reconciliation of late facts under the current authority and preservation of unissued commitments at revocation (A-4, LC-CUT) have no executable evidence beyond the stranded-reservation refusal; the profile itself says RS-3 did not implement them. |
| RS-C08 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C09 | `PARTIAL` | partially covered | No test consumes a ticket publicly and then shields or spends it privately, so the public-then-private half of "once in total" is unexercised; shield-then-public and nullifier replay are covered. |
| RS-C10 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C11 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C12 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C13 | `COVERED_MODEL_OR_MEMORY` | sufficiently covered, model or in-memory only | none |
| RS-C14 | `PARTIAL` | partially covered | No test checks the separation of per-path results in a real run report; the delegated leg is in-memory only; private resale, refund, reissue and key rotation are unimplemented and are only stated as such. |
| RS-C15 | `COVERED_LOCALNET` | sufficiently covered | none |
| RS-C16 | `PARTIAL` | partially covered | A call with an old-generation control is not constructible (rs-1 record), so that clause has no test; omission of a control is not exercised either. |
| RS-C17 | `COVERED_LOCALNET` | sufficiently covered | none |
| RR-1 | `COVERED_LOCALNET` | sufficiently covered | none |
| RR-2 | `PARTIAL` | partially covered | Concurrent revocations on one root are tested only as a sequential stale-witness case, and the collision rate is unmeasured. |
| RR-3 | `COVERED_LOCALNET` | sufficiently covered | none |
| RR-4 | `COVERED_LOCALNET` | sufficiently covered | none |
| RR-5 | `MEASUREMENT_ONLY` | partially covered: structure covered, measurement left to RS-4 | Contention of `shield` on the one note tree is unmeasured. |
| RR-6 | `MEASUREMENT_ONLY` | partially covered: structure covered, measurement left to RS-4 | The share of in-flight proofs one revoke invalidates and the re-proof delay are unmeasured. |

Totals: 14 sufficiently covered (12 + 2), 9 partially covered (7 `PARTIAL` + 2 `MEASUREMENT_ONLY`), 0 not covered.

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** Every row in the map other than the items below: the cited tests assert what the profile sentence says, as far as the profile defines it.

**B. Contract undefined (characterizations and remaining uncertainty; nothing amended).**

1. No test name carries a proposed test id. The only occurrence of one in tests, vectors or drivers is the doc comment `RR-2-T1` at `reference/rights_scale/sui/tests/private_path_tests.move:470`, above the test that the map cites for RR-2. The profile marks ids as proposals and RS-0 added no tests, so this is not a violation.
2. The T1/T2/T3 splits of RS-C03, RS-C06, RS-C07, RS-C14 have no one-to-one test; the map cites the nearest tests by content and labels the halves.
3. The fixtures K = 4, `MAX_BUNDLE_CHAIN` = 8 and the shard counts in the tests are not profile values; the profile leaves them UNDETERMINED or `DECISION_REQUIRED · Astra`.
4. RS-C02 sentence 2 (redistribution of two pages in one PTB): the package has no such operation and `test_no_ga_redistribution_entry_exists_in_the_package` asserts its absence. The profile defines the sentence but §3 has no operation for it; the rs-1 record keeps it `DECISION_REQUIRED · Astra`.
5. RS-C16: a call with an old-generation control is not constructible (rs-1 record), so that clause has no test.
6. RS-C09: no test consumes a ticket publicly and then shields or spends it privately.
7. RR-2: concurrent revocations on one root are tested only as a sequential stale-witness case (rs-2 record limitation 8); the collision rate is RS-4's.
8. RS-C06(b)/RS-C07(b): the cut-versus-consume order is exercised serially; the reconciliation of late facts and the preservation of unissued commitments at revocation (A-4, LC-CUT) have no executable evidence, and the profile says RS-3 did not implement them.

**C. Explicit contract violation:** none found. No cited test contradicts a profile predicate, so no blocker is raised.

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main` | Both `543c1438ce044479fd9646bc5e1cde933a153a4c`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. `rs predicate evidence map ok: rows=23 expected=23 citations=153 COVERED_LOCALNET=12 COVERED_MODEL_OR_MEMORY=2 PARTIAL=7 NOT_COVERED=0 MEASUREMENT_ONLY=2`. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. Unmodified map passes, Move positive control passes, all 13 breaks listed above detected, `self-test: pass`. |
| `check_rs_profile_traceability.py`, `check_status_register.py`, `check_read_model_source_map.py`, `check_docs_index.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, each plain and with `--self-test` | All exit 0 (docs index: `scanned=146 indexed=111 allowlisted=35`; delegation matrix: `rows=36 expected=36`; `self-test: pass` for each). |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | `Ran 115 tests`, `OK`. |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | Exit 0, `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`; tests `OK`. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | `OK`. |
| `python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | Each `OK`. |
| `cd runtime && cargo test --workspace --locked --offline`; `cargo clippy --workspace --all-targets --locked --offline -- -D warnings`; `cargo fmt --all -- --check` | All test results `ok`, no failures; clippy finished with no warnings; fmt check exit 0. (`--offline` because the session has no network; nothing under `runtime/` changed.) |
| Move (`sui move test`), localnet, ZK, Node jobs; exact-head KTX kernel verification and KIX protocol verification | **Not run.** No Sui binary or network use in this session, and there is no pushed head. |

## Non-claims

- Not an Astra architecture review; the profile stays draft 0.2 and the capability register is unchanged.
- No Sui, ZK, localnet, Move, Cargo or Node job ran in this session; those CI jobs and the exact-head KTX and KIX workflows are not run here because there is no pushed head.
- No grade is raised and the operational count stays 0. Nothing here shows production durability, real concurrency behaviour, anonymity, or bank or chain finality.
- Counts and `PASSED_ACTUAL_LOCALNET` statements in the cited records are quoted at their own heads and were not re-run on this one.
- The checker confirms that a cited name exists in a cited file. It does not run the test and does not check that the test asserts the predicate; that is the reading recorded in the map.
