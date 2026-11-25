# Capital overlapping exposure groups

Node `plan-capital-overlapping-exposure-groups` uses the supervisor-supplied
planner specification and design plan as the task input. The node has no issue
or `docs/tasks/` document. Branch `agent/kix-plan-capital-overlapping-exposure-groups`
and cached `origin/main` both started at `2b968e72722cfd3f877ede557da90fa1a37510fa`.

## Coverage mapped before implementation

The test paths in this table are relative to `reference/credit_advance_f04/`.

| Requirement | Prior coverage | New evidence |
| --- | --- | --- |
| Pinned source and frozen views | Partial. `test_shared_exposure_contract.py::SharedExposureContractTests.test_fixture_is_canonical_and_pinned` and `test_fixture_views_are_literal_machine_snapshots` cover the canonical source and snapshot provenance. | `CapitalOverlappingExposureGroupsTests.test_source_pins_and_pointer_identities` checks the raw digest, E3 ID, label, limit and ordered source pointers. Detached controls reject source byte drift and a substituted valid view pointer. |
| Union and defaulted exposure | Sufficient for the E3 union in `SharedExposureContractTests.test_defaulted_advance_still_aggregates`. | The E3 union serves as the same-checkpoint control for the overlapping groups. |
| Overlap and attribution | Uncovered. `test_capital_omitted_exposure_members.py::CapitalOmittedExposureMembersTests.test_membership_pairs` compares E1/E2 subsets with their complete groups. | `CapitalOverlappingExposureGroupsTests.test_overlapping_groups` replays A+B, B+C and A+B+C, checks the exact three totals and traces the excess to B's frozen `DEFAULTED` view. |
| Duplicate refusal, preservation and authority | Partial. `SharedExposureContractTests.test_malformed_and_non_mock_views_are_rejected`, `test_observation_is_read_only_and_deterministic` and `test_mapping_is_not_bound_and_execution_flags_stay_false` cover the observer. | The replay passes A+B+B+C intact, checks the exact refusal and compares argument bytes before and after all four calls. It compares complete canonical results and checks the limit, mapping and authority flags. |
| Discovery and complete result association | Uncovered for this family. `test_capital_companion_evidence_index.py::CapitalCompanionEvidenceIndexTests.test_complete_index` covers the existing inventory. | The index test verifies the new artifact pins, all four associations, the replay symbol and guide heading. `test_overlapping_exposure_groups_crossed_references` rejects swapped case and result pointers. |

## Results

All calls use the E3 checkpoint, `pool-e3` label and 90,000 KRW fixture
limit. A+B reports 70,000 KRW outstanding and B+C reports 50,000. Their
120,000 KRW sum includes the same 30,000 KRW `DEFAULTED` advance `adv-e3-b`
twice. The distinct-member union counts that advance once and reports
90,000 KRW with `within_limit=true`. A+B+B+C returns `VIEW_INVALID`.
Argument bytes match before and after every call. Successful results
retain `NOT_BOUND`, `repair=NONE` and `authorizes_exposure=false`.
The index holds 17 families, 470 entries, 128 supplemental observations
and 12 supporting entries. [Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-overlapping-exposure-groups) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#overlapping-exposure-group-comparisons)

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_overlapping_exposure_groups_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_overlapping_exposure_groups.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-25-plan-capital-overlapping-exposure-groups/README.md`

## Local verification

Commands ran from the repository root unless specified. `f04` denotes
`reference/credit_advance_f04`.

| Command | Result |
| --- | --- |
| `git status --short --branch` and `git rev-parse HEAD refs/remotes/origin/main` | Clean starting worktree. HEAD and the cached main ref matched the supplied base. |
| `rg -n 'plan-capital-overlapping-exposure-groups' docs/tasks .aiops`, `ls -ld /workspace/kix-run/logs/planner_1795523250` and `rg --files /workspace/kix-run/logs /workspace/kix-run/plans` | No in-repository task or program entry. The exact log path was absent. The suffixed `planner_1795523250_codex0.last.md` corroborates the supplied scope, acceptance and dependencies. |
| `sha256sum "$f04/fixtures/shared_exposure_v1.json"` and inline `python3.12 -B` source inspection | Digest, E3 ID, label, limit and literal view identities matched. B is `DEFAULTED` with 30,000 KRW outstanding. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_overlapping_exposure_groups.py` | 2 passed. Covers four replay cases and two detached source controls. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_shared_exposure_contract.py` | 19 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 17 passed. Includes both crossed-pointer controls for the new comparison. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04"` | 328 passed. |
| `python3.12 -B scripts/check_docs_index.py` and the same command with `--self-test` | Both passed. 463 scanned, 428 indexed, 35 allowlisted. |
| `python3.12 -B scripts/check_credit_evidence_map.py` and the same command with `--self-test` | Both passed. 24 clauses and 55 negative controls. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and the same command with `--self-test` | Both passed. F04 discovery reaches 31 files. All 18 negative controls passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed. All 7 tests passed. |
| `cargo fmt --all -- --check` in `runtime/` | Passed. |
| `cargo test -p kix-kernel --locked --offline` and `cargo test --workspace --locked --offline` in `runtime/` | Both exited 101 before compilation. The registry index lacks `duckdb`, needed to resolve the unmodified `kix-analytics-audit` crate. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` and `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | All exited 101 at the same DuckDB resolution step. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` | Exit 1. The local cache holds 14 of 378 locked archives. |
| Inline `python3.12 -B` temporary workspace setup and `diff -qr` for each copied crate | Six local-only crate trees matched byte for byte. The temporary workspace used the original lockfile entries for those crates. |
| `cargo test -p kix-kernel --locked --offline --quiet` and `cargo test --workspace --locked --offline --quiet` in the temporary workspace | 139 kernel tests and 332 six-crate workspace tests passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` and `cargo tree -p kix-kernel --edges normal --locked --offline` in the temporary workspace | Both Clippy runs passed. The kernel's normal dependency tree contains only `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Recorded hashes for the three KTX workflow inputs. |
| `git hash-object` on the kernel locks and the new pack, `sha256sum` on both fixtures, and `cmp` on the sorted `reference/v0.3-rc1` SHA-256 manifests | Checked the identities below. Both locked blobs match before and after. The 108-file manifests match byte for byte. |
| `git diff --exit-code HEAD --` over the protected paths, `git diff --check`, `git status --short --untracked-files=all`, `git rev-parse HEAD` and inline `python3.12 -B` checks | Protected paths and HEAD match the base. Exactly eight files changed. The prior index matches byte for byte after removing the appended pack. Whitespace checks passed, including new files. |

## Protected bytes and delivery gates

| Artifact | Verified value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`. |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `reference/v0.3-rc1/**` | 108-file sorted SHA-256 manifest with digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`. |
| `shared_exposure_v1.json` | SHA-256 `cdb001701376c02cd3515bcdd939193922c960bdcaebf80ca8d3f0d7732c1c03`. |
| `capital_overlapping_exposure_groups_vectors_v1.json` | SHA-256 `9912b49d7474fab34870e512850f1aa40a49e6dbfed1c83b74c12e8ddc50810e`, Git blob `86cb4246daff384ee97c5667dc4be193eef3b723`. |

The comparison matches F04 §7.12. No contract violation or new
contract-undefined behavior surfaced. This is source-informed Class B
synthetic evidence. Product exposure limits remain **UNDETERMINED — Astra**,
legal responsibility **UNDETERMINED — User/legal**, and external `kix-capital`
acceptance **UNVERIFIED**. Provider calls, funds execution, production runtime,
durability, bank exactly-once, chain finality, accounting and legal compliance
were outside these checks.

The supervisor owns publication. The worktree changes are uncommitted. The
implementation and final task commit SHAs, A2 non-author exact-head review,
and KTX kernel verification and KIX protocol verification run IDs, statuses
and conclusions are pending supervisor delivery. No merge occurred.

## Deviations

The supervisor's no-network rule superseded the startup fetch. The cached
main ref matched the supplied base. The offline Cargo fallback covered
`kix-types`, `kix-feature-semantics`, `kix-feature-ir`, `kix-kernel`,
`kix-kernel-v5` and `kix-delegated-exec`. Results for the full runtime
workspace remain unverified, including `kix-analytics-audit` and `kix-bcs1`.
Hosted execution and unrelated protocol integration stages remain outside
this evidence.
