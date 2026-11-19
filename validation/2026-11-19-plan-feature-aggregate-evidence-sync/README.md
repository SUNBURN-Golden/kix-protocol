# FeatureIR aggregate empty-policy evidence

The `plan-feature-aggregate-evidence-sync` node connects two existing validator regressions to `S4-EMPTY-AGGREGATES`. Its input is the supervisor-supplied specification and owner decision of 2026-11-18 (`pt224u`). Planner run `1793143383` proposed this node outside `.aiops/program.json`, with no issue or matching task document under `docs/tasks/`. Its dependency, `plan-plan-feature-ir-validator-matrix-closure`, left the S4 citations for follow-up. [Matrix validation record](../2026-10-26-plan-feature-ir-validator-matrix-closure/README.md)

## Coverage

| Requirement | Classification and evidence |
|---|---|
| §4 empty-policy table | Sufficiently covered. The two existing scalar citations fix the policies for all five kinds. The existing FeatureIR MEAN citation checks a plan with a terminal F64 result. |
| §4 policy rejection and acceptance through both §10 validators | Sufficiently covered. Both tests iterate `aggregate_specs()`. COUNT uses Zero with U64 output. SUM, MIN and MAX use Null with I64 output, and MEAN uses Null with TerminalF64 output. The rejection test flips only `empty_policy` and expects `Err(FeatureIrError::AggregatePolicyMismatch)`. The control keeps the contract policy and expects `Ok(())`. For each case, `assert_both()` checks `validate()` and `validate_with_schemas(&catalog())` against that expectation. [Matrix source](../../runtime/crates/kix-feature-ir/tests/validator_matrix.rs) · [Contract §§4 and 10](../../runtime/FEATURE_SEMANTICS_V1.md) |
| S4 documentation | Previously partially covered. The row now cites both regressions and §3 records their scope. The following sentence, all other rows and the counts line retain their original wording. [Evidence map](../../docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md) |
| Aggregate evaluation | Not covered. Neither test runs an evaluator on empty or all-null datasets. Backend conformance remains open. S4 stays `PARTIAL` with owner `k-stage7-cpu-analytics-sql-audit`. |

The validator results match the cited contract (AGENTS §8 A). This inspection found no contract violation or new undefined behavior. The existing tolerance, precision, negative-zero and depth questions remain open. The change adds no tests or capability grades.

## Revision and changed paths

The assigned branch `agent/kix-plan-feature-aggregate-evidence-sync` started clean at `d3506262bf6227ab71ea72427e4d1ee996a0c5ef`. This is the comparison base and the end-of-session HEAD. The local `origin/main` ref was `5be902b5cd7d314e9e7d05ab919597385896e48f`, 290 commits ahead. The map and matrix source were identical at both revisions. The supervisor's offline rule precluded a fetch, so remote freshness is unverified. The uncommitted work uses the assigned base.

| Changed path | Change |
|---|---|
| `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md` | Append two citations, revise the S4 gap and replace the single owner-approved §3 sentence. |
| `docs/README.md` | Index the dated S4 follow-up alongside the matrix record. |
| `validation/2026-11-19-plan-feature-aggregate-evidence-sync/README.md` | Record the assertion review, local checks and integrity evidence. |

## Local verification

Commands ran from the repository root. The Python checkers used `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR="$PWD/runtime/target"`. The focused Cargo run preceded the document checks.

| Command | Exit | Observed result |
|---|---:|---|
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test validator_matrix --locked aggregate_` | 0 | Both newly cited tests ran. 2 passed, 0 failed, 5 filtered out. |
| `python3 scripts/check_feature_semantics_evidence_map.py` | 0 | 41 rows, 3 COVERED, 21 PARTIAL, 17 NOT_COVERED. |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | 0 | 81 negative controls and the injected positive control passed. |
| `python3 scripts/check_evidence_map_rollup.py` | 0 | 25 contracts in the roll-up. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | 0 | 16 negative controls passed. |
| `python3 scripts/check_docs_index.py` | 0 | 297 scanned, 262 indexed, 35 allowlisted. |
| `python3 scripts/check_docs_index.py --self-test` | 0 | Detected all seven index defects. |
| All commands in the `Stdlib offline document checks` run block of `.github/workflows/protocol.yml` at the comparison base | 0 each | A foreground Python runner executed all 63 command lines in workflow order, including the six above. |

The initial plain and self-test map checks each exited 1 with `S4-EMPTY-AGGREGATES: Gap must be nonempty text without backticks`. Removing the two pairs of backticks around the API names in the Gap cell fixed both checks.

For the full workflow block the runner denied the `socket` system call to itself and its children. The informational `python3 scripts/check_loopback_host.py` command exited 0 and reported `all_ok=false`, with socket creation denied in both processes. The synthetic self-test passed. Both workflows classify these three paths as documentation. The KTX kernel build, workspace tests, Clippy and formatting are outside the docs-only path. [Protocol workflow](../../.github/workflows/protocol.yml) · [KTX workflow](../../.github/workflows/ktx-kernel.yml)

## Integrity

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main` and `git rev-list --left-right --count HEAD...origin/main` | Revisions above. Branch-only commits 0, local main-only commits 290. |
| `git hash-object --no-filters runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after, respectively by path, `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git rev-parse HEAD:reference/v0.3-rc1` | Git tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. All 108 working-tree paths and file hashes matched before and after. |
| `git ls-tree -rz HEAD` and `git hash-object --no-filters --stdin-paths` | All 1,077 tracked files outside the three changed paths matched their HEAD blobs before and after. The comparison includes history under `validation/`, contracts, capability grades, source, checkers, CI, `.aiops/` and `docs/tasks/`. |
| `git diff --check HEAD` and `git status --short --untracked-files=all` | No whitespace errors. Only the three paths listed above were modified or added. The root `DECISION_REQUIRED.md` was already absent. |

The integrity check hashed each sorted repository-relative path, a NUL, its lowercase Git blob ID and a newline into a single SHA-256 digest. Before and after digests matched for the protected tracked files (`6d0198509ca9a34973c329da7fb7a1e150bc58aa696c84dc0c7049c0031c88ae`) and for the complete reference file inventory (`21d27d5d6cbcef76dc23a1977e4b0d23c816cf25faa98646ec0177e82c60d967`). A separate comparison against `git show HEAD:<path>` verified the exact two appended citations, unchanged S4 status and owner, the approved §3 sentence and its original continuation, and byte-identical content in every other map line.

This is builder-authored local evidence. Independent A2 review remains pending. The supervisor owns publication. There is no implementation commit, final task commit or merge commit for this worktree change. Exact-head KTX and KIX protocol CI have no run IDs, statuses or conclusions for this delivery. Post-merge CI is inapplicable. No historical CI result is carried forward.
