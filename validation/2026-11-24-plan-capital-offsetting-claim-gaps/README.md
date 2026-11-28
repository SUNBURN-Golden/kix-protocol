# Capital offsetting claim gaps

Node `plan-capital-offsetting-claim-gaps` uses the node specification and
design supplied in the task message. The node has no GitHub issue or task
document under `docs/tasks/`. The named planner log for run `1795489732` was
absent locally. The starting branch was `agent/kix-plan-capital-offsetting-claim-gaps`.
Its HEAD and cached `origin/main` matched the design base
`50238d018090f60fd7bd58abccd56c38dcda334c`. The supervisor's offline rule
prevented the §1 fetch, so remote freshness is unverified.

## Coverage assessed before implementation

Test paths are relative to `reference/credit_advance_f04/`.

| Requirement | Prior coverage | Evidence added |
| --- | --- | --- |
| Individual variances, signs, tolerance and fail-closed mapping | Sufficient in `test_settlement_variance_contract.py::SettlementVarianceContractTests.test_all_scenarios_replay_to_expected`, `test_formula_and_sign_convention`, and `test_tolerance_boundary_is_inclusive_and_out_of_tolerance_is_fail_closed`. | `CapitalOffsettingClaimGapsTests.test_claim_pair` replays the pinned inputs and checks the full envelopes and independently specified claim rows. |
| Source pins, view identity and chronology | Sufficient for the original fixture in `test_settlement_variance_contract.py::SettlementVarianceContractTests.test_fixture_is_canonical_and_pinned` and `test_fixture_views_are_literal_machine_snapshots`. The new portable associations were uncovered. | `test_claim_pair` verifies both source digests, scenario identities, exact view and tolerance pointers, claim/trade, currency, frozen flag and complete view digests. The existing snapshot test reconstructs V4's earlier settlement observation and later frozen credit. |
| Zero diagnostic total with correct claim attribution | Uncovered for these two claims together. | `test_claim_pair` sums the two replayed variances. `test_swapped_claim_attributions` exchanges their attributed signs and variances and checks that each claim fails while the total holds. |
| Companion discovery and policy qualification | Partial. `test_capital_companion_evidence_index.py::CapitalCompanionEvidenceIndexTests.test_complete_index` already checks pins, result associations, discovery and qualification. | The inventory adds two cases and `test_offsetting_claim_gaps_crossed_result_references` rejects two individually valid result pointers exchanged between those cases. |

## Results

| Claim / trade | Settlement outstanding (KRW) | Frozen credit face (KRW) | Source tolerance (KRW) | Signed variance (KRW) |
| --- | ---: | ---: | ---: | ---: |
| `claim-v4` / `trade-v4` | 100,000 | 60,000 | 0 | +40,000 |
| `claim-v2` / `trade-v2` | 60,000 | 100,000 | 39,999 | −40,000 |

Both report `within_tolerance=false`, `NOT_BOUND`, `repair=NONE`,
`refund_component=NOT_BOUND`, `fail_closed=true`, `mutates_state=false` and
`authorizes_exposure=false`. The diagnostic sum is 0 KRW. The companion
index has 15 families, 463 entries, 128 supplemental observations and 12
supporting entries. The original settlement-variance supporting record
still has all six scenarios.
[Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-offsetting-claim-gaps) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#offsetting-claim-gap-comparison)

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_offsetting_claim_gaps_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_offsetting_claim_gaps.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-24-plan-capital-offsetting-claim-gaps/README.md`

## Verification

Commands ran from the repository root unless stated otherwise. `f04` is
`reference/credit_advance_f04` and `settlement` is
`reference/settlement_f01_f03`. The focused suites ran before broad checks.
Python 3.12.15 matched the workflow's reference-suite Python minor version.
Cargo and rustc were both 1.98.1.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse --verify refs/remotes/origin/main`, `git rev-parse --verify HEAD`, `git branch --show-current` | Clean starting worktree. Branch and cached base matched the supplied plan. |
| `rg -n 'plan-capital-offsetting-claim-gaps' docs/tasks .aiops/program.json` and `ls -ld /workspace/kix-run/logs/planner_1795489732` | No matching task or program entry. The planner log path was absent. |
| Inline `PYTHONPATH=reference/credit_advance_f04 python3 -B` | Loaded the digest-pinned source with the existing loader, used the observer to write the canonical pack, and appended the pack to the existing index encoding. |
| `python3.12 -B -m unittest test_capital_offsetting_claim_gaps` in `f04` | 2 passed on both runs, including the swap control. The second run included an explicit result claim/trade assertion. |
| `python3.12 -B -m unittest test_settlement_variance_contract` in `f04` | 15 passed, including literal snapshot reconstruction. |
| `python3.12 -B -m unittest test_capital_companion_evidence_index` in `f04` | 15 passed, including the crossed-result-pointer control. |
| `python3.12 -B "$f04/settlement_variance.py" --check` | Exit 0 on rerun and six scenarios passed. The first run's reporting pipe exited 1 because its inline JSON printer looked for a `match` field absent from CLI output. The rerun captured the CLI output and counted scenarios separately. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04"` | 322 passed. |
| `python3.12 -B -m unittest discover -s "$settlement" -t "$settlement"` | 224 passed. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 460 scanned, 425 indexed and 35 allowlisted. |
| `python3.12 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both passed. 24 clauses and 55 negative controls. |
| `python3.12 -B scripts/check_settlement_evidence_map.py` and `--self-test` | Both passed. 27 clauses and 33 negative controls. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. The CI F04 discovery invocation reaches the new test. All 18 negative controls passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture and declared dependencies passed. All 7 architecture tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed on the real workspace. |
| `cargo test -p kix-kernel`, `cargo clippy -p kix-kernel --all-targets -- -D warnings`, and `cargo tree -p kix-kernel --edges normal`, each with `--manifest-path runtime/Cargo.toml --locked --offline` before any Clippy `--` | Each exited 101 before compilation. The workspace requires `duckdb` for `kix-analytics-audit`, and the local registry index lacks it. |
| `cargo test --workspace` and `cargo clippy --workspace --all-targets -- -D warnings`, each with `--manifest-path runtime/Cargo.toml --locked --offline` before any Clippy `--` | Each exited 101 with the same offline resolution failure. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` and `--self-test` | `--require` exited 1 with 14 of 378 locked archives present. `duckdb` and `libduckdb-sys` were missing. The self-test passed. |
| Inline `python3.12 -B` temporary Rust workspace setup, followed by the five Cargo test, Clippy and tree commands above against its manifest with `--locked --offline` | All passed. 139 kernel tests and 332 tests across the six copied local-only crates, including the kernel. Kernel and subset Clippy passed, and the kernel's normal dependency tree contained only `kix-types`. The temporary workspace used byte-identical crate copies and their original lock entries. It excluded `kix-analytics-audit` and `kix-bcs1`. |
| `git hash-object` on both locked kernel paths and sorted `find reference/v0.3-rc1 -type f -print0` with `sha256sum`, before and after, followed by `cmp` | Both locked blobs matched and the two 108-file manifests were byte-identical. |
| `sha256sum` for both source files and the new artifact, and `git hash-object` for the source fixture and new artifact | Both source SHA-256 pins and the source fixture Git blob matched. The new artifact pins matched the index. |
| `git diff --exit-code HEAD --` on the protected paths, workflows, contracts and both source files, plus inline Python JSON comparison with `git show HEAD:docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json` | Zero protected or source diffs. Removing the new appended family restored the complete prior index at the JSON value level. |
| `git diff --check`, `git status --short --untracked-files=all`, and inline `python3.12 -B` path and whitespace check | Passed. Exactly the eight listed paths changed. |

## Protected bytes and delivery gates

| Artifact | Verified value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `reference/v0.3-rc1/**` | 108-file sorted SHA-256 manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` before and after. |
| `settlement_variance_v1.json` | SHA-256 `f2db31f337bc44d5931e97f0e5c57d529e8f1f444339366b50178c304df38b76` and Git blob `a97b99171649273e4e552596356e8da347bc9826`. |
| `settlement_variance.py` | SHA-256 `af5db942825f8268bde42142d343454bca3e0bb43ca417fdfb86d590e347005d`. |
| `capital_offsetting_claim_gaps_vectors_v1.json` | SHA-256 `a62a473bb69dde93769e9f1c04eb91a408a3d9014c253f4cbab211f9eeebeabe` and Git blob `37b5c3632407af78275cff6b143cf3b338358039`. |

No contract violation or new contract-undefined behavior surfaced. The
comparison provides source-informed Class B synthetic evidence. Product
thresholds remain `UNDETERMINED` with Astra, legal responsibility remains
`UNDETERMINED` with User/legal, and external `kix-capital` acceptance remains
`UNVERIFIED`. Netting, real funds, real provider calls, public endpoints,
live-chain execution, durability, legal compliance and production readiness
were outside the verification.

The supervisor owns publication. The worktree remains uncommitted with
HEAD `50238d018090f60fd7bd58abccd56c38dcda334c`. Implementation, final task
and merge commit SHAs are pending. There is no exact-head KTX or KIX CI
run ID, status or conclusion for the patch. Hosted Move, ZK and local-chain
jobs were outside the local checks for the touched paths. A2 non-author
review and exact-head KTX/KIX CI remain delivery gates.
