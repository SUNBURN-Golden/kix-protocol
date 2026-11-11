# Readiness checker PARTIAL fixture

Node: `plan-readiness-checker-partial-fixture`. Dependency:
`plan-plan-readiness-contract-evidence-map`. Issue: none. Audit floor: A2;
`astra_gate: None`; `user_merge: False`. Source: supplied node specification and
design plan, KIX planner run `1792572941`
(`/workspace/kix-run/logs/planner_1792572941`; log contents not independently
verified). This loop-proposed node is not in `.aiops/program.json`.
The supplied specification is the task input; no matching task document exists
under `docs/tasks/`, and none was created or revised. This is not ASTRA program mode.

Observed local `origin/main`, base and initial branch HEAD:
`26f1b9535db24a6b2e9c28753f561d4d6a271815` on
`agent/kix-plan-readiness-checker-partial-fixture`. No local ref delta.
`git fetch origin main` was omitted under the supervisor's explicit no-network
instruction; remote freshness is unverified. No commit, push, PR, issue action,
comment, history rewrite or merge was performed. Implementation/final task head
containing these edits: unavailable (uncommitted supervisor handoff). Exact-head
KTX/KIX run IDs, statuses and conclusions: unavailable, not requested or observed.
Merge SHA and post-merge CI: not applicable. Local verification does not establish
merge readiness or satisfy non-author exact-head review/A2 requirements.

## Existing coverage and reproduced gap

Coverage was mapped before editing `scripts/check_readiness_evidence_map.py`.
All paths/symbols below refer to that checker's original `self_test`, now
preserved in `_self_test_map` except for the corrected ownership control.

| Requirement | Existing coverage | Action |
|---|---|---|
| Valid supplied map; Python symbol positive/negative probe | sufficiently covered: baseline `find_problems` and `py_probe` | Retained per baseline. |
| Removed/duplicate/invented IDs; dangling path/symbol; wrong column; forbidden reference citation; free-text fixture; missing-cell citation | sufficiently covered: corresponding mutation cases | Retained without duplicating tests. |
| Unknown status; status/cell mismatch; EXERCISED without fixture; NOT_EXERCISED with fixture; EXERCISED naming a gap | sufficiently covered: corresponding mutation cases | Retained. |
| OPEN on wrong row; designated OPEN reclassified; OPEN without owner; unrecognized owner | sufficiently covered: corresponding mutation cases | Retained. |
| Counts, banner, locked blob, contract anchor | sufficiently covered: counts/banner cases, in-memory file injection, anchor removal | Retained, no negative-control counts repaired. |
| PARTIAL ownership rule | partially covered: owner removal from real `REC-CORE-COMMIT` assumed its current status | Replaced with validated synthetic fixture, exact diagnostic list. |
| Synthetic PARTIAL positive control independent of real status | not covered | Explicit citation, status, named gap, recognized owner and recomputed counts. |
| Complete self-test with zero PARTIAL rows | not covered | Validated in-memory transformation and complete second suite. |

Before editing, both plain checker and `--self-test` passed on the disk map.
An inline Python reproduction imported the original checker with
`PYTHONDONTWRITEBYTECODE=1`, changed every PARTIAL row in memory to EXERCISED,
set its missing/owner cells to `none`, and derived the counts from parsed rows.
`find_problems` returned `[]`, the nine OPEN lines were identical, and counts
were `EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`. The old `self_test`
returned 1 with `self-test: PARTIAL row without an owner was accepted`.
This is an embedded-regression defect, not a validator or runtime contract violation.

## Implementation and new evidence

`_with_recomputed_counts` is used only to construct valid in-memory fixtures.
`_without_partial_rows` retains citations, changes PARTIAL status/missing/owner
cells only, and derives counts. `self_test` runs the complete `_self_test_map`
suite against the supplied map and its zero-PARTIAL variant; it independently
requires the variant to have no PARTIAL rows, pass `find_problems`, and preserve
every OPEN row line. No recursive self-test calls or on-disk map writes occur.

Each suite explicitly builds `REC-CORE-COMMIT` with citation
`readiness/test_faults.py::test_core_record_in_an_fsm_journal_fails_closed`,
status `PARTIAL`, missing text
`Synthetic self-test gap: ownership requirement is under test.`, and owner
`k-readiness-conformance-suite` (already named in `readiness/CONFORMANCE.md`).
Other cells remain valid and counts are recomputed. The positive control must
return `[]`. Changing only the owner to `none` must return exactly:

```text
REC-CORE-COMMIT: PARTIAL row must have an owner
```

All original 21 mutation behaviors remain: 20 unchanged table cases plus the
separate, strengthened ownership case. The Python-symbol probe, injected
locked-blob mutation and removed-anchor control run for both baselines.
Validator semantics, owner recognition, citation rules, anchors, locked hashes,
and CLI options are unchanged. No retargeting to `OBS-AUDIT` was used.

## Changed paths

- `scripts/check_readiness_evidence_map.py`: embedded self-tests and fixture helpers.
- `validation/2026-10-21-readiness-checker-partial-fixture/README.md`: this record.
- `docs/README.md`: one link in the existing 2026-10-21 index.

## Commands and results

Commands ran from the repository root. Python: 3.13.5. Cargo/rustc: 1.98.1.
Rust commands used `--offline` to honor the no-network constraint; installed
dependencies sufficed. The narrow checks ran before broader verification.

| Command | Actual result |
|---|---|
| `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current`; `git status --short` | Exit 0; refs and branch above; initial worktree clean. |
| Inline Python SHA-256 snapshot (`hashlib`, `git ls-files -z`) and `git hash-object` for both locked paths | Exit 0; 898 tracked and 108 reference files captured; both blobs match. |
| `python3 scripts/check_readiness_evidence_map.py` (before and after edit) | Exit 0; 36 expected rows, 177 citations; EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` (before edit) | Exit 0 on current map; all original controls detected. |
| Inline Python pre-edit zero-PARTIAL reproduction, with `PYTHONDONTWRITEBYTECODE=1` | Harness exit 0; valid variant; old self-test returned the expected 1 and exact failure recorded above. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` (after edit) | Exit 0; both baselines pass, each with a valid synthetic PARTIAL positive control, 21 mutation detections, injected locked-blob detection and removed-anchor detection. |
| `python3 scripts/check_status_register.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_rs_profile_traceability.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_read_model_source_map.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_docs_index.py`; same command with `--self-test` | Both exit 0; scanned=188 indexed=153 allowlisted=35. |
| `python3 scripts/check_i12_proof_ids.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_delegation_layer_matrix.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_rs_predicate_evidence_map.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_rs_im_evidence_map.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_tl_predicate_evidence_map.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_contract_error_codes.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_adapter_identity_map.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/check_v5_transition_evidence_map.py`; same command with `--self-test` | Both exit 0. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests, OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; all test binaries and doc-tests passed, no failures. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; all workspace test binaries and doc-tests passed, no failures; output captured in `/tmp/readiness-workspace-test.log`. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings. |
| Inline Python post-edit zero-PARTIAL, validator-prefix and byte-snapshot assertions, with `PYTHONDONTWRITEBYTECODE=1` | Exit 0; direct `self_test(zero-PARTIAL input)` returns 0, both full suites pass (46 negative detections and two PARTIAL positive controls); all nine OPEN lines identical. Validator and preceding constants/helpers byte-identical to HEAD; preservation results below. |
| `git diff --check`; `git diff --stat`; `git diff -- scripts/check_readiness_evidence_map.py docs/README.md`; `git status --short` | Exit 0; no whitespace errors; tracked diff limited to checker and index, only untracked delivery path is this validation record. |

The 26 authoritative `Stdlib offline document checks` commands (the 13 checker
pairs above) were extracted from the unchanged workflow step and executed
sequentially by inline Python `subprocess.run`, stopping on nonzero exit.
They ran twice; the second run also persisted each actual exit code in
`/tmp/readiness-stdlib-results.json`, all 0, with individual stdout/stderr in
`/tmp/readiness-stdlib-00.log` through `-25.log`. These temporary logs are local
execution aids, not delivery paths. Final plain and self-test docs-index checks
were repeated after completing this record; both exited 0. Final `git diff
--check`, both locked-blob hashes, local HEAD/origin-main refs, untracked-file
allowlist and byte-manifest assertions also passed with the values above.

## Preservation, discrepancies and limits

Before editing, both Git blobs matched AGENTS §4:
`runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`.
A SHA-256 byte snapshot covered all 898 tracked files and separately all 108
files under `reference/v0.3-rc1/`, stored outside the repository in
`/tmp/readiness-partial-before.json` for before/after comparison.
Initial real-map SHA-256:
`b56d0ab1417e435f4b636d29a379a95df57fea44d37e67c236f4faf0f29ef6d5`.

After implementation and local verification, the same two Git blobs match and
the real-map SHA-256 is identical. All 896 tracked files outside the checker
and docs index match the initial byte snapshot. The complete 108-file reference
manifest (including its path set) also matches. Thus the real map and owners,
contracts, workflows, runtime, readiness/gate, task documents and `.aiops/` are
unchanged. The in-memory zero-PARTIAL map independently preserves the nine OPEN
row lines exactly; none of these fixture transformations is written to disk.

Design deviations: the strengthened ownership negative control runs separately
from the 20 retained table cases so it can require an exact diagnostic list.
An additional OPEN-line preservation guard is embedded in the orchestration.
No scope deviation. The fetch omission and offline Cargo flags follow the
explicit supervisor constraint. The closest installed local architecture and
Rust workflow equivalents passed, including workspace tests/Clippy. Full hosted
verification (triggered by a `scripts/` change), other Python runtime/gate,
Node/SDK, Move, circuit, storage probes and artifact-generation jobs were not
run; no protected reference artifacts were regenerated.

No new contract violation or contract-undefined runtime characterization was
found. The existing three recovery characterizations remain unresolved with
owner `Astra`; all six held rows retain their owners. All nine stay OPEN.
The synthetic EXERCISED rows are regression fixtures, not evidence of new
runtime coverage or closure of any real map gap. Operational count stays 0.

**`plan-readiness-receipt-audit-tests` still requires owner-approved input
revision outside its builder session. This prerequisite correction neither
implements nor resumes that blocked node.**

No runtime, readiness/gate, contract, workflow, task, `.aiops/`, reference or
policy change is authorized here. No real funds, provider calls, public
endpoints, Sui/localnet, secrets, storage engine or production runtime was used.
No production durability, power-loss, OS-crash, fsync correctness, distributed
fencing, chain finality, external exactly-once, independent acceptance or
production-readiness claim is made. Hosted CI and non-author review remain
supervisor follow-up; no existing historical CI success is inherited.
