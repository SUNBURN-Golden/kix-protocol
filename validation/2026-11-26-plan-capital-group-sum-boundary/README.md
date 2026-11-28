# Capital group sum boundary

The supervisor supplied the specification and design plan for
`plan-capital-group-sum-boundary`. The node has no GitHub issue or
`docs/tasks/` document. Branch `agent/kix-plan-capital-group-sum-boundary`
and cached `origin/main` both started at
`e1161eeadb06d3386028a0c3cfa7d68fcaab2348`.

## Coverage before implementation

Test paths in this table are relative to `reference/credit_advance_f04/`.

| Requirement | Existing coverage | Added evidence |
| --- | --- | --- |
| Rebuild two frozen views with the existing mocks | Partial. `test_shared_exposure_contract.py::SharedExposureContractTests.test_fixture_views_are_literal_machine_snapshots` reconstructs the smaller E1–E6 fixtures. | Reconstruct both complete `DRAWN` views from distinct claims and trades at 1,000,000,000,000 and 1 fixture KRW. |
| Count claim capacity once and aggregate above the per-view ceiling | E1 sufficiently covers same-claim deduplication. E2 covers cross-claim aggregation at smaller amounts. The above-ceiling group was uncovered. | Compare both sorted claim records and the advance IDs, exact aggregate capacity, drawn and outstanding exposure, and zero repayment and residual capacity. |
| Compare the same group at the exact limit and one below | Partial. E2/E5 and `test_limit_boundary_is_inclusive_and_over_limit_is_fail_closed` cover an inclusive boundary and a smaller out-of-limit case. | Compare the full records for explicit limits at the group total and one unit below. |
| Reject a detached view at the same total | Partial. `test_capital_refusal_vectors.py::CapitalRefusalVectorTests.test_rejections_match_and_preserve_inputs` covers `E21_face_overflow`. | Apply only the specified amount overrides to a detached machine view and preserve exposure and capacity arithmetic. Require the exact `VIEW_INVALID` envelope. |
| Preserve inputs and authority flags | Partial for this pair. `test_observation_is_read_only_and_deterministic` and `test_mapping_is_not_bound_and_execution_flags_stay_false` cover the existing fixture. | Compare canonical argument bytes around all three calls, re-read both views and check authority, refund and mapping fields. |
| Discover both source views and three complete results | Uncovered for this family. `test_capital_companion_evidence_index.py::CapitalCompanionEvidenceIndexTests.test_complete_index` covers the prior inventory. | Validate exact pins, case/result and view references, replay symbol, guide heading and qualification. Reject crossed success and source-view pointers and a detached pack with reversed case view references and recomputed pins. |

## Results

Both success cases report 1,000,000,000,001 fixture KRW drawn and outstanding,
count each distinct claim's capacity once and preserve the input bytes. They
report `within_limit=true` at 1,000,000,000,001 and `false` at
1,000,000,000,000. The detached single view at 1,000,000,000,001 produces
`VIEW_INVALID`. Positive observations keep `refund_component=NOT_BOUND`
and `authorizes_exposure=false`. The index contains 19 packs, 476 entries,
130 supplemental observations and 12 supporting entries.
[F04 §7.12](../../docs/contracts/CREDIT_ADVANCE_F04.md#712-공유-노출shared-exposure) · [Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-group-sum-boundary) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#group-sum-boundary)

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_group_sum_boundary_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_group_sum_boundary.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-26-plan-capital-group-sum-boundary/README.md`

## Local verification

Commands ran from the repository root unless indicated. `$f04` is
`reference/credit_advance_f04`. Python and Cargo report versions
`3.12.15` and `1.98.1`.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD origin/main` | Clean starting worktree. HEAD and cached main both resolved to the supplied base. |
| `rg -n 'plan-capital-group-sum-boundary' docs/tasks .aiops/program.json` | No repository task document or program entry. The planner run's `planner_1795611291_codex0.last.md` contains the source node under `capital-group-sum-boundary` with the same goal and acceptance. |
| Inline `PYTHONPATH=reference/credit_advance_f04 python3.12 -B -` fixture and index construction | Captured the two machine views and three observer envelopes, wrote canonical fixture bytes, and appended the pack with matching raw-byte pins for input and output. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_group_sum_boundary.py` | 1 test passed, covering three cases. Passed immediately after fixture generation and again before the broader checks. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 19 tests passed, including the three crossed-reference controls in the new test. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04"` | 333 tests passed. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 468 scanned, 433 indexed and 35 allowlisted. |
| `python3.12 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both passed. 24 clauses and 55 negative controls. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. F04 discovery reaches 33 files. All 18 negative controls passed. |
| Inline `python3.12 -B -` runner for the `Stdlib offline document checks` commands in `.github/workflows/protocol.yml` | All 69 checker invocations passed with Python 3.12 and bytecode writes disabled. |
| `python3.12 -B scripts/verify_runtime_architecture.py`, `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate and all 7 tests passed. |
| `cargo fmt --all -- --check` in `runtime/` | Passed. |
| `cargo test -p kix-kernel --locked --offline`, `cargo test --workspace --locked --offline` in `runtime/` | Both exited 101 before compilation. The offline registry lacks the `duckdb` index entry needed to resolve `kix-analytics-audit`. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | All exited 101 at the same resolution step. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | The offline cache contains 14 of 378 locked archives. |
| Inline `python3.12 -B -` temporary Cargo workspace setup and `diff -qr` on each copied crate | Six local-only crate trees matched byte for byte. The temporary workspace uses the corresponding original lockfile entries. |
| `cargo test -p kix-kernel --locked --offline --quiet`, `cargo test --workspace --locked --offline --quiet` in the temporary workspace | 139 kernel tests and 332 six-crate workspace tests passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in the temporary workspace | Both passed. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` in the temporary workspace | Passed. The normal kernel dependency tree contains only `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | All three KTX workflow input digests were computed. |
| `git hash-object` on the locks and fixture, `sha256sum` on the fixture, and `cmp` on sorted `reference/v0.3-rc1` byte manifests | The two locked blobs and the 108-file manifest match before and after. The fixture pins match the index. |
| `git diff --exit-code HEAD -- .aiops docs/tasks .github reference/v0.3-rc1 runtime`, `git diff --check`, `git status --short --untracked-files=all`, and inline `python3.12 -B -` index and untracked-file checks | Protected paths have no changes, whitespace checks passed, exactly eight files changed, and the prior JSON index bytes match after removing the appended pack. |

## Protected bytes and delivery gates

| Artifact | Verified value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | Sorted 108-file SHA-256 manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` |
| `capital_group_sum_boundary_vectors_v1.json` | SHA-256 `2b94f8c629794d021b76c129d8aa364707557c353c0d46016474b7c3a6e85e57`, Git blob `6cb7bfabccb73c4dc133223be3d0f53d2200c90b` |

The three cases match F04 §7.12. No contract violation or new
contract-undefined behavior surfaced. This is source-informed Class B
synthetic evidence. Product exposure limits remain **UNDETERMINED — Astra**,
legal responsibility **UNDETERMINED — User/legal**, and external
`kix-capital` acceptance **UNVERIFIED**. Evidence covers local mock replay
and index association. Real funds, provider and public endpoint calls,
Sui execution, production runtime, durability, bank exactly-once,
chain finality, accounting and legal compliance are outside these checks.

The worktree is ready for supervisor handoff. The implementation and final
task commit SHAs, A2 non-author exact-head review, and exact-head KTX kernel
verification and KIX protocol verification run IDs, statuses and conclusions
are pending supervisor delivery. There is no merge commit or post-merge CI.

## Deviations

The supervisor's no-network rule superseded the startup fetch. The cached
main ref matched the supplied base. The offline Cargo fallback covered
`kix-types`, `kix-feature-semantics`, `kix-feature-ir`, `kix-kernel`,
`kix-kernel-v5` and `kix-delegated-exec`. The full workspace, including
`kix-analytics-audit` and `kix-bcs1`, remains unverified locally. The
network-dependent bootstrap, unrelated SDK/Move/ZK and chain integration
stages, and hosted runs were outside this local validation.
