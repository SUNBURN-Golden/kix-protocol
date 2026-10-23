# v5-transition-evidence-map

Node: `plan-plan-v5-transition-evidence-map`. Adds `docs/status/V5_TRANSITION_EVIDENCE_MAP.md` — one row per transition/command that `docs/contracts/STATE_LIFECYCLE.md` §§5–6 names and that `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md` option O1, narrowed by the 2026-10-13 owner residual-stops decision recorded in `validation/2026-10-13-k-stage2-v5-impl/README.md`, leaves in scope — and `scripts/check_v5_transition_evidence_map.py` (stdlib only, `--self-test`), wired into the unguarded `Stdlib offline document checks` step of `.github/workflows/protocol.yml` after the `check_adapter_identity_map.py` lines.

Issue: none. Depends on: `plan-v5-lifecycle-seeded-model-test`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792427921 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `b8c8d1057e8124fef09dc2301fdc841015f22b4a` (merge of PR #224). `git fetch origin main` was not run (this session forbids network actions); the value is the local `origin/main` ref. Branch `agent/kix-plan-plan-v5-transition-evidence-map`. No task document exists under `docs/tasks/` for this node; the task input is the node spec quoted above.

**This record and the map are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, no stopped transition is opened, no open input is resolved, and no v5 `src`, contract or locked-blob byte changed.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker recomputes both blobs on every run. Nothing under `runtime/`, `reference/` (so `reference/v0.3-rc1/` too), `readiness/`, `integration_gate/`, `.aiops/`, `docs/tasks/`, `docs/contracts/` or `docs/decisions/` changed.

## What this change does

- The map has 10 rows: 6 `TESTED`, 4 `STOPPED`, 0 `OPEN`.
  - `TESTED` rows resolve to cited `#[test]` fns in the v5 test tree: TERM (13 `termination.rs` + the seeded `lifecycle_model.rs` test), TERM-LATE (4), RR-REVIEW (2), RECLAIM-READ (13 `reclaim_report.rs` + 6 `reclaim_batch.rs` + the seeded test), HOLD (9 `holds.rs`), CONFLICT-INDEX (4 `conflict_index.rs` + the seeded `v4_differential.rs` test).
  - `STOPPED` rows are marked, not tested: SLOT-RELEASE (I12, I13), REVIEW-RELEASE (I11 + conclusion contents), RECLAIM-APPLY (I09, I10, I13), INDEX-UPKEEP (gates on the same stops). Each names the design decision §6 gate and the implementation record's `Stopped parts` row, and each `Stop guard` cell names the `#[test]` fns that pin the stopped behavior.
- The row set is a builder reading of the §§5–6 scope: the five design-decision §6 transitions, the §5.6 late-success rule, the §5.7.1 orthogonality rule, the §6 hold reference, and the §6 index-upkeep gate. Contract §5.4 authority generations and §5.5 automation tiers are paper/automation scope — no kernel transition implements them, so no row; the §5.1/§5.4.7 durable approval axis is stage-5 scope (non-goal, stated in the map preamble).
- `boundary.rs` (2 fns) and the two `v4_differential.rs` version-rejection tests are O1 crate-boundary evidence — cited in the map's scope-boundary subsection, not given contract rows.
- The checker verifies the hardcoded row ids and their contract/decision anchor strings, the eight-cell row width, cell grammar (`v5 surface` = `no entry point` or `pub fn` citations into `src/lib.rs`; `v5 tests`/`stop guard` = `none` or citations into `tests/` requiring a `#[test]`-attributed `fn` — a helper like `termination.rs::unchanged` is rejected; `missing or open` carries no citations; `decision / owner` citations restricted to the contract, design decision, open-inputs file and implementation record), status-versus-cell consistency, every `path::symbol` citation in the whole document (repo-relative, existing path and symbol, never under `reference/v0.3-rc1/`), open-input ids (`I\d\d` tokens must be rows of `FIRST_BATCH_OPEN_INPUTS.md`), the two locked blobs, and the `Counts:` line. `--self-test` requires each deliberate break to be caught (19 mutation cases + locked-blob injection + removed anchor).

## Changed paths

| Path | Change |
|---|---|
| `docs/status/V5_TRANSITION_EVIDENCE_MAP.md` | New map, 10 rows. |
| `scripts/check_v5_transition_evidence_map.py` | New checker, stdlib only. |
| `.github/workflows/protocol.yml` | Two added lines at the end of the stdlib step. |
| `docs/README.md` | One bullet in the 2026-10-20 section linking the map and this record. |
| `validation/2026-10-20-v5-transition-evidence-map/README.md` | This record. |

## AGENTS.md section 7: existing coverage per row

| ID | Map status | Section 7 class | Missing |
|---|---|---|---|
| TERM | `TESTED` | covered at name level | In-memory record only; durable approval is stage-5 scope. |
| TERM-LATE | `TESTED` | covered at name level | none |
| RR-REVIEW | `TESTED` | covered at name level | none (v4 regression `contract_edge_cases.rs::return_required_is_stable_under_further_late_evidence` pre-exists on the locked kernel) |
| SLOT-RELEASE | `STOPPED` | not covered — stopped | No release transition; I12 handoff predicate, I13 custody budget. |
| REVIEW-RELEASE | `STOPPED` | not covered — stopped | No release transition; I11 remainder + conclusion contents. |
| RECLAIM-READ | `TESTED` | covered at name level | I09, I10, I13 stay unconditional blockers; no report is ever eligible. |
| RECLAIM-APPLY | `STOPPED` | not covered — stopped | No state-changing reclaim; I09, I10, I13. |
| HOLD | `TESTED` | covered at name level | Neither call authenticates anyone or releases anything else. |
| CONFLICT-INDEX | `TESTED` | covered at name level | Upkeep under stopped transitions is the INDEX-UPKEEP row. |
| INDEX-UPKEEP | `STOPPED` | not covered — stopped | Nothing to keep the index consistent under until reclaim/release open. |

"Name level": the checker proves the cited `#[test]` fn names exist in the cited files. What each test asserts is the map's reading, not a checker verdict.

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** Nothing new asserted — this node adds no test and classifies no behavior beyond the rows above.

**B. Contract undefined (characterizations; nothing amended).** The row scope is itself a characterization: the contract §§5–6 prose does not enumerate a row set, so the map states its scope rule in §0. The §5.4 authority-generation and §5.5 automation-tier texts have no kernel transition and are excluded on that ground.

**C. Explicit contract violation:** none found.

## Commands and results

All run from the node worktree in the foreground. `python3` here is 3.13.5 (`protocol.yml` pins 3.12); `rustc` 1.98.1 (the workflow pin).

| Command | Result |
|---|---|
| `git rev-parse HEAD`; `git branch --show-current`; `git status --short`; `git log --oneline -5` | HEAD `b8c8d1057e8124fef09dc2301fdc841015f22b4a` on `agent/kix-plan-plan-v5-transition-evidence-map`; clean tree before edits |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0` |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. Unmodified map passes; all 19 mutation cases, the injected locked-blob mutation and the removed anchor detected; `self-test: pass` |
| `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, `check_adapter_identity_map.py`, each plain and `--self-test` | All exit 0 |
| `python3 scripts/check_docs_index.py` and `--self-test` | Exit 0 after this record was added (before: one `not indexed` line for this record) |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | Exit 0 — `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`; 7 tests `OK` (nothing under `runtime/` changed) |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | `OK` |
| `python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | Each `OK` |
| `check_openapi_contract.py`, `check_integration_gate_openapi.py`, each plain and `--self-test` | All exit 0 |
| `cd runtime && cargo fmt --all -- --check`; `cargo test --workspace --locked --offline`; `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | fmt exit 0; all test-result lines `ok` (kix-kernel-v5: 56 tests incl. `lifecycle_model` 1); clippy no warnings. (`--offline`: no network in this session.) |
| `cd runtime && cargo test -p kix-kernel-v5 --locked --offline` | Exit 0 — the 56 `#[test]` fns the map cites all run and pass |
| `git diff --stat origin/main -- reference/v0.3-rc1 runtime readiness integration_gate docs/contracts docs/decisions docs/tasks .aiops` | Empty — none of those paths changed |
| `python3 scripts/check_sdk_client.py`; `npm --prefix sdk` steps; Move (`sui`), localnet, ZK jobs; exact-head KTX kernel verification and KIX protocol verification | **Not run.** Node major 20 ≠ 24 pre-existing limitation (`sdk/` untouched); no Sui binary or network; there is no pushed head |

## CI (AGENTS §10, §14)

- Exact-head KTX kernel verification run: none. No commit exists.
- Exact-head KIX protocol verification run: none. No commit exists.
- Merge commit and post-merge main CI: not applicable.
- The `scripts/` + `.github/` additions make the changed-path classifier run **full** verification on a non-draft PR, not docs-only — the conservative direction.

The supervisor commits and opens the PR. This record claims `merge-ready` for nothing; the node state is complete locally, awaiting exact-head CI, non-author review and the user merge decision.

## Non-claims

- Not an Astra review; the contract stays draft 0.6 and the capability register is unchanged (`CURRENT_CAPABILITY_REGISTER.md` is a dated snapshot — left for a register-sync node).
- The map decides nothing and raises no grade: a cited name exists in the test tree, nothing more. It does not claim what any cited test asserts, and it does not run them.
- Stopped transitions stay stopped: no slot release, no review release, no state-changing reclaim, no index upkeep under them. Open inputs I09–I13 stay open; the durable-approval axis (§5.1/§5.4.7) is stage-5 scope and untouched.
- No `src`, contract, decision, `.aiops/` or `docs/tasks/` change; no new protocol command, wire or catalogue name; no secrets, no policy values.
- No claim of durability, distributed fencing, bank exactly-once, chain finality, legal compliance or production readiness; local success is not exact-head CI and is not merge authorization.
