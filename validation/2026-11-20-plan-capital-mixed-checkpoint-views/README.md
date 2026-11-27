# Capital mixed-checkpoint views builder validation

## Task and base

- Node `plan-capital-mixed-checkpoint-views`, branch `agent/kix-plan-capital-mixed-checkpoint-views`.
- Task input is the supervisor-provided node envelope and design plan from planner run `1795159796`. This node has no task issue or `docs/tasks/` document.
- The local `origin/main` reference and starting branch HEAD both resolved to `2786dda4b790a355364baf52aa580a97a3c3e072`. The supervisor's offline rule precluded the §1 fetch, so remote freshness is unverified. The delivery is an uncommitted worktree patch. The supervisor owns the implementation and final commit IDs.
- [F04 §7.12](../../docs/contracts/CREDIT_ADVANCE_F04.md#712-공유-노출shared-exposure) · [Vector pack](../../reference/credit_advance_f04/fixtures/capital_mixed_checkpoint_views_vectors_v1.json) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#mixed-checkpoint-comparisons)

## Existing coverage and added evidence

Paths in this table are relative to `reference/credit_advance_f04/`.

| Requirement | Prior coverage | Evidence added |
| --- | --- | --- |
| Same-checkpoint arithmetic and counting face once per claim | Sufficient. `test_capital_terminal_capacity_vectors.py::CapitalTerminalCapacityVectorTests.test_repayment_close_capacity_arithmetic` and `test_frozen_faces_and_captured_observations` | The repayment and close controls use the exact pairs from the pinned source and compare complete results. |
| Refuse conflicting reservations | Sufficient. `E09_reserved_conflict` in `fixtures/capital_refusal_vectors_v1.json`, replayed by `test_capital_refusal_vectors.py::CapitalRefusalVectorTests.test_rejections_match_and_preserve_inputs` | `close_mixed` uses the historical pair with reservations 70,000 and 30,000 and checks the typed error. |
| Mixed repayment with agreeing claim bindings | Not covered for these checkpoints | `repay_mixed` records 70,000 outstanding at the synthetic limit against 55,000 at `repay-part`. |
| Input preservation and observation flags | Partial. `test_shared_exposure_contract.py::SharedExposureContractTests.test_observation_is_read_only_and_deterministic` and `test_mapping_is_not_bound_and_execution_flags_stay_false` cover the observer | Every new call checks its canonical arguments on exit. Successful results assert one claim, two advances, inclusive limit, `NOT_BOUND`, `repair=NONE` and `authorizes_exposure=false`. |
| Source pins, pointer identity and consumer discovery | Partial. `test_capital_terminal_capacity_vectors.py::CapitalTerminalCapacityVectorTests.test_artifact_and_source_pins` and the companion validator cover existing packs | The replay checks raw digests, source-to-output association, scenario and step IDs, exact pointer order and view IDs. Detached controls reject byte drift and an equal-valued `adv-2` from the wrong checkpoint. The index validator checks both artifact pins, replay and guide locations, four input/result associations and rehashed or crossed references. |

The literal expected results were authored from the supplied arithmetic and
the pinned view identities before replay. All amounts are synthetic KRW.

| Case | Drawn | Repaid | Outstanding or refusal | Open face | Reserved | Residual |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `repay_mixed` | 70,000 | 0 | 70,000 | 100,000 | 70,000 | 30,000 |
| `repay_same` | 70,000 | 15,000 | 55,000 | 100,000 | 70,000 | 30,000 |
| `close_mixed` | — | — | `SharedExposureError` / `VIEW_BINDING_CONFLICT` | — | 70,000 and 30,000 in the inputs | — |
| `close_same` | 70,000 | 40,000 | 30,000 | 100,000 | 30,000 | 70,000 |

The companion inventory is 12 families, 455 entries, 128 supplemental
observations and 12 supporting entries. The index wording now describes
binding agreement and caller checkpoint selection, consistent with §7.12.

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_mixed_checkpoint_views_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_mixed_checkpoint_views.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-20-plan-capital-mixed-checkpoint-views/README.md`

## Verification

Commands ran from the repository root unless a row specifies `runtime/`.
`f04` is `reference/credit_advance_f04`.

| Command | Result |
| --- | --- |
| `git status --short --branch` and `git rev-parse HEAD refs/remotes/origin/main` | Initial worktree clean, correct branch, both refs at the SHA above. |
| `sha256sum reference/credit_advance_f04/fixtures/capital_terminal_capacity{,_vectors}_v1.json` and inline `python3.12 -B` preflight using `_resolve` | Both supplied digests, the output's `fixture_sha256`, scenario identity, `repay-part` and `close-fresh` positions, group, integer limit and five view identities matched. An initial diagnostic assumed `trade-1`; inspection found `trade-claim-1` in every resolved view and the corrected preflight passed. |
| `git hash-object` and `sha256sum` on the new vector pack | Git blob `d6b486b5beabefb93ff1c5897aa8d3cd24d42f14` and raw SHA-256 `eb7daed7e620f9a2852ec51bf57a12651ad112ea8ef85529eae94f82c3692114` match both companion pins. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_mixed_checkpoint_views.py` | 2 passed, including four replay subtests, on both runs. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 12 passed on both runs. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04"` | 313 passed on both runs. |
| `python3 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 453 scanned, 418 indexed, 35 allowlisted. |
| `python3 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both passed. 24 clauses and 55 self-test negative controls. |
| `python3 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. F04 discovery covers 26 test files. All 18 self-test negative controls passed. |
| `python3 -B scripts/verify_runtime_architecture.py` | Architecture and KTX dependency gate passed. |
| `python3 -B scripts/test_runtime_architecture.py` | 7 passed. |
| `cargo test -p kix-kernel --locked --offline` in `runtime/` | 139 passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` in `runtime/` | Passed. |
| `cargo fmt --all -- --check` in `runtime/` | Passed. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | Passed. Normal dependency tree contains `kix-types` only. |
| `git hash-object` on both locked paths, `find reference/v0.3-rc1 -type f -print0 \| sort -z \| xargs -0 sha256sum` before and after, `cmp` on the manifests | Both locked blobs match their required IDs and the before/after manifests are byte-identical. |
| `git diff --exit-code HEAD --` on protected paths and both source fixtures | Protected paths, source fixtures and workflows match the base. |
| `git show HEAD:docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json` piped to inline `python3.12 -B -c` comparison | Prior packs, supporting entries and qualification match the base. |
| `git diff --check`, inline `python3.12 -B` whitespace check on the three added files, and `git status --short --untracked-files=all` | Whitespace checks passed and status listed the eight paths above. |

## Protected bytes and delivery gates

| Protected path | Required value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | 108-file sorted SHA-256 manifest with digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`. |

This is source-informed synthetic Class B evidence. No contract violation was
found in the four comparisons. Section 7.12 leaves the current checkpoint and
its authority to callers. The mixed repayment result characterizes the
observer when those views still agree on bindings.

Product exposure limits remain **UNDETERMINED — Astra**, legal responsibility
**UNDETERMINED — User/legal**, and external `kix-capital` acceptance
**UNVERIFIED**. The checks cover offline observations and discovery only.
Production readiness, durable execution, provider calls, real funds, chain
finality and legal compliance were outside this task.

A2 non-author exact-head review and both hosted workflows remain pending
supervisor delivery. KTX kernel verification and KIX protocol verification
have no builder-verified run ID, status or conclusion for a final head. No
merge or post-merge verification applies to this worktree.
