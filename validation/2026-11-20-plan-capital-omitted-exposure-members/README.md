# Capital omitted exposure members

Node `plan-capital-omitted-exposure-members` uses the supplied planner node
specification and design plan as its task input. It has no issue or task
document under `docs/tasks/`. Worktree branch
`agent/kix-plan-capital-omitted-exposure-members` and cached `origin/main`
both started at `e84339eaed71e921fca7ec4d82fa85ec1c7bc588`. The supervisor
prohibited network actions, so remote freshness was unverified.

## Coverage mapped before implementation

Paths in the coverage table are relative to `reference/credit_advance_f04/`.

| Requirement | Prior coverage | Evidence in this node |
| --- | --- | --- |
| Complete E1/E2 fixture groups | Sufficient in `test_shared_exposure_contract.py::SharedExposureContractTests.test_all_scenarios_replay_to_expected` and `test_aggregation_formulas_over_exposed_values_only`. | The existing suite owns contract coverage. The full groups are the controls for the new subsets. |
| One omitted advance at the same checkpoint, group label and limit | Uncovered. The shared-exposure suite covers caller grouping and the inclusive limit. | `CapitalOmittedExposureMembersTests.test_membership_pairs` compares four complete results and checks the exposure deltas, E1's unchanged claim reservation and E2's limit flip. |
| Raw source digest, exact ordered pointers and frozen views | Partial. `SharedExposureContractTests.test_fixture_is_canonical_and_pinned` and `test_fixture_views_are_literal_machine_snapshots` cover the source. `CapitalMixedCheckpointViewsTests.test_source_pins_and_pointer_identities` checks its own pack's pointers. | `CapitalOmittedExposureMembersTests.test_source_pins_and_pointer_identities` resolves E1/E2 and rejects detached byte drift and a byte-identical E5 view substituted for the E2 view. |
| Read-only inputs, whole result and authority flags | Partial. `SharedExposureContractTests.test_observation_is_read_only_and_deterministic` and `test_mapping_is_not_bound_and_execution_flags_stay_false` cover the observer. | Every new replay compares canonical input bytes before and after, compares the entire result with a literal expectation and checks the mapping and flags. |
| Companion discovery and exact case/result association | Uncovered for this family. The index already checks other self-contained comparisons. | `CapitalCompanionEvidenceIndexTests.test_complete_index` checks both pins, the four ordered associations, the replay symbol and guide heading. `test_omitted_exposure_members_crossed_references` rejects swaps of valid full/subset pointers in both pairs. |

## Results

The complete E1 fixture reports 70,000 KRW outstanding. Omitting
`adv-e1-2` reduces that figure to 40,000 KRW. The retained view still
carries the shared claim's 70,000 KRW reservation. E2 reports 110,000 KRW
against a 100,000 KRW fixture limit with both views and 60,000 KRW after
omitting `adv-e2-b`. The E2 subset flips `within_limit` to true. The complete
outputs also capture drawn, repaid, claim-level capacity and identities.
[Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-omitted-exposure-members)

The comparison matches F04 §7.12. Callers supply group membership and the
limit. The observer calculates over the supplied views and offers no way to
certify real pool completeness. All observations and refund components
remain `NOT_BOUND` with `repair=NONE`, fail-closed, read-only and without
exposure authority. The companion inventory contains 13 families, 459
entries, 128 supplemental observations and 12 supporting entries.

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_omitted_exposure_members_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_omitted_exposure_members.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-20-plan-capital-omitted-exposure-members/README.md`

## Verification

Commands ran from the repository root unless specified. `f04` is
`reference/credit_advance_f04`.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD refs/remotes/origin/main`, `git branch --show-current` | Clean starting worktree. Branch and cached base matched the supplied SHA. |
| `rg -n 'plan-capital-omitted-exposure-members' docs/tasks .aiops` and `ls -ld /workspace/kix-run/logs/planner_1795168746` | No in-repository task document or program entry. The named planner log path was absent. The supplied plan was available in the task message. |
| `sha256sum "$f04/fixtures/shared_exposure_v1.json"` and inline `python3.12 -B` source inspection | Source SHA-256 matched. E1/E2 scenario IDs, labels, limits and frozen advance identities matched. E5's first view equaled E2's first view. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_omitted_exposure_members.py` | 2 passed. The replay includes all four cases and the source identity test includes both detached controls. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_shared_exposure_contract.py` | 19 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 13 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04"` | 316 passed. |
| `python3 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 456 scanned, 421 indexed, 35 allowlisted. |
| `python3 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both passed. 24 clauses and 55 self-test negative controls. |
| `python3 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. F04 discovery reaches 27 files. All 18 self-test negative controls passed. |
| `python3 -B scripts/verify_runtime_architecture.py` | Architecture and declared dependency gate passed. |
| `python3 -B scripts/test_runtime_architecture.py` | 7 passed. |
| `cargo test -p kix-kernel --locked --offline` in `runtime/` | 139 passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` in `runtime/` | Passed. |
| `cargo fmt --all -- --check` in `runtime/` | Passed. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | Passed. The normal dependency tree contains `kix-types` only. |
| `git hash-object` and `sha256sum` on the new vector pack | Both companion pins matched the Git blob and raw SHA-256 below. |
| `git show HEAD:docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json` piped to inline `python3.12 -B -c` comparison | Removing the appended pack restores the exact prior index content at the JSON value level. |
| `git hash-object` on both locked kernel paths, `find reference/v0.3-rc1 -type f -print0 \| sort -z \| xargs -0 sha256sum` before and after, and `cmp` on the manifests | Both blobs matched their locks. The 108-file before/after manifests matched byte for byte. |
| `git diff --exit-code HEAD --` on the protected paths, source fixture, contracts and workflows | Passed. |
| `git diff --check`, inline `python3.12 -B` whitespace and changed-path check, `git status --short --untracked-files=all` and `git rev-parse HEAD` | Passed. Eight changed paths. HEAD remained at the supplied base. |

## Protected bytes and delivery gates

| Artifact | Verified value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `reference/v0.3-rc1/**` | 108-file sorted SHA-256 manifest with digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` before and after. |
| `shared_exposure_v1.json` | SHA-256 `cdb001701376c02cd3515bcdd939193922c960bdcaebf80ca8d3f0d7732c1c03`. |
| `capital_omitted_exposure_members_vectors_v1.json` | SHA-256 `946ed152019d3674049d6fd823f961dac47da19556b0d065ce5cacad3b8f9211` and Git blob `7eb99a026071327349163268bafad512ab1869f7`. |

No contract violations or new contract-undefined behavior surfaced.
This is source-informed Class B synthetic evidence. Product exposure limits
remain **UNDETERMINED — Astra**, legal responsibility **UNDETERMINED —
User/legal**, and external `kix-capital` acceptance **UNVERIFIED**. Provider
calls, funds execution, production runtime, durability, bank exactly-once,
chain finality, accounting and legal compliance were outside the checks.

The supervisor owns publication. The builder's changes are uncommitted, so
there is no implementation or final task commit SHA. A2 non-author
exact-head review and both hosted workflows are pending supervisor delivery.
KTX kernel verification and KIX protocol verification have no final-head run
ID, status or conclusion in this record. No merge occurred.

## Deviations

The supervisor's no-network instruction superseded the AGENTS.md startup
fetch. The cached main ref matched the supplied base. The builder used the
supplied node specification and plan because the referenced planner log path
was absent. Local verification covered the relevant document checks, F04
discovery and the KTX kernel workflow commands. Hosted execution and
unrelated protocol integration stages remain outside this local evidence.
