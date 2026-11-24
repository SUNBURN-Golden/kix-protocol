# Capital payee order recovery

Node `plan-capital-payee-order-recovery` uses the planner node specification
and design plan supplied in the task message. The node has no issue or task
document under `docs/tasks/`. The starting branch was
`agent/kix-plan-capital-payee-order-recovery`. Its HEAD and cached
`origin/main` both identified `409ed9fa506371fb065d871b52e3a99a55365456`,
matching the supplied design base. Remote freshness was unverified under the
supervisor's offline instruction. The referenced planner log path was absent
locally. The supplied task and design were available in the message.

## Coverage assessed before implementation

Test paths in the table are relative to `reference/credit_advance_f04/`
unless otherwise indicated.

| Requirement | Prior coverage | Evidence added |
| --- | --- | --- |
| R1 fee-first recovery and source identity | Sufficient in `test_capital_refund_composition_vectors.py::CapitalRefundCompositionVectorTests.test_full_refund_per_payee`, `test_artifact_and_source_pins` and `test_complete_history_vectors`. | Reuses the pinned scenario result and compares it with the new case at the same checkpoints. |
| Same R1 inputs with residual-first attribution | Uncovered. `reference/settlement_f01_f03/test_settlement_multi_payee_refund.py::RefundReservationPerPayeeTests.test_g_reservation_at_partial_distribution_is_per_payee` supplies the fee-first arithmetic precedent. | `CapitalPayeeOrderRecoveryTests.test_order_pair` changes only the order on a fresh replay, matches the setup receipts and initial snapshot, checks the distribution receipt by payee, and matches the literal rows at refund and acceptance. |
| Conservation, aggregate recovery and variance across orders | Partial. `test_full_refund_per_payee` and `verify_arithmetic` in the refund composition suite cover single-history arithmetic. | `test_order_pair` checks conservation throughout, the 10,000 KRW aggregate and identical complete post-refund variance observations. |
| Frozen credit and shared exposure across orders | Partial. `test_settlement_actions_preserve_credit` covers byte equality within each original history. | `test_order_pair` compares the complete canonical observations at initial, distribution, refund and acceptance against R1's initial observations. |
| Incorrect attribution with the same aggregate | Partial. The refund composition suite's `test_verifier_sensitivity` perturbs its fee-first split. | `test_swapped_payee_attribution` swaps just the residual-first recovery amounts and rejects the attribution while the total and face conservation still hold. The same test rejects omitted cancellation of the unpaid fee face at each refund checkpoint. |
| Exact navigation for the new comparison | Uncovered for these cases. `test_capital_companion_evidence_index.py::CapitalCompanionEvidenceIndexTests.test_complete_index` validates the existing families. | The extended validator verifies the fixture's byte pins, checks both associations and rejects swapped result pointers in `test_payee_order_crossed_result_references`. |

## Results

At both `refund-full` and `accept-full`, the fee-first order produces 5,000
KRW of recovery due for each payee. The residual-first order produces 0 for
`fee-r1` and 10,000 for `res-r1`. The unpaid 5,000 KRW fee face moves to
`cancelled_unpaid` and stays there through mock acceptance. For both cases,
the aggregate recovery due is 10,000 KRW, variance is −100,000 KRW, cash
delta is 0, and recovery delta is 10,000 KRW. The two histories have
byte-equal frozen credit and shared-exposure observations. The companion
index now has 14 families, 461 entries, 128 supplemental observations, and
12 supporting entries. [Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-payee-order-recovery) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#payee-order-recovery-comparison)

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_payee_order_recovery_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_payee_order_recovery.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-24-plan-capital-payee-order-recovery/README.md`

## Verification

Commands ran at the repository root unless specified. In the table, `f04`
is `reference/credit_advance_f04` and `settlement` is
`reference/settlement_f01_f03`. The three focused suites ran first.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD refs/remotes/origin/main`, `git branch --show-current` | Clean starting worktree on the supplied branch and cached base. |
| `rg -n 'plan-capital-payee-order-recovery' docs/tasks .aiops/program.json`, `ls -ld /workspace/kix-run/logs/planner_1795180531` | No task document or program entry matched. The named log path was absent. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_payee_order_recovery.py` | 2 passed, including both refund checkpoints and detached attribution and cancellation controls. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_refund_composition_vectors.py` | 7 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 14 passed, including the crossed-result control. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04"` | 319 passed. |
| `python3.12 -B -m unittest discover -s "$settlement" -t "$settlement"` | 224 passed. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 458 scanned, 423 indexed, 35 allowlisted. |
| `python3.12 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both passed. 24 clauses and 55 self-test controls. |
| `python3.12 -B scripts/check_settlement_evidence_map.py` and `--self-test` | Both passed. 27 clauses. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. The F04 workflow invocation covers the new file. All 18 self-test controls passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture and declared dependency gate passed. All 7 architecture tests passed. |
| `cargo fmt --all -- --check` in `runtime/` | Passed for the real workspace. |
| `cargo test -p kix-kernel --locked --offline`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | Workspace dependency resolution stopped each command before compilation because the local index lacks `duckdb`, required by `kix-analytics-audit`. |
| `cargo test --workspace --locked --offline`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in `runtime/` | Same resolution failure. Workspace test and lint results remain unavailable. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` and `--self-test` | `--require` exited 1. Only 14 of 378 locked archives were present, with `duckdb` and `libduckdb-sys` absent. Self-test passed. |
| Inline `python3.12 -B` temporary workspace setup, followed by `cargo test`, `cargo clippy --all-targets -- -D warnings`, and `cargo tree --edges normal` for `kix-kernel`, all with `--manifest-path`, `--locked` and `--offline` | The temporary workspace used unmodified copies of `kix-kernel` and `kix-types`, the same resolver, and their two original lockfile entries. Both copied locked blobs matched their pins. 139 kernel tests passed, Clippy passed, and the normal tree contained only `kix-types`. |
| `sha256sum` on both R1 source files and the new pack, and `git hash-object` on the new pack | Both R1 SHA-256 pins and both new pack digests matched the fixture and index. |
| `git hash-object` on both locked kernel paths before and after, sorted `find reference/v0.3-rc1 -type f -print0` SHA-256 manifests, and `cmp` | Both blobs matched their locks and the two 108-file manifests were byte-identical. |
| `git diff --exit-code HEAD --` on protected paths, contracts, workflows and both R1 sources, plus inline JSON comparison with `git show HEAD:docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json` | Protected paths had zero diff. Removing the appended family restored the prior index at the JSON value level. |
| `git diff --check`, inline `python3.12 -B` whitespace and changed-path check, `git status --short --untracked-files=all`, `git rev-parse HEAD` | Passed. Eight changed paths. The uncommitted worktree is based on the original branch HEAD. |

## Protected bytes and delivery gates

| Artifact | Verified value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `reference/v0.3-rc1/**` | 108-file sorted SHA-256 manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` before and after. |
| `capital_payee_order_recovery_vectors_v1.json` | SHA-256 `28218ee3d63faf2433cf064ef4176bb339eb0320abe95b20892836f0d8031eeb` and Git blob `5135ec5a944ebcd8314e2a0be9635c95e8617d66`. |

No contract violation or new contract-undefined behavior surfaced. Product
waterfall priority remains `UNDETERMINED` with Astra and external
`kix-capital` acceptance remains `UNVERIFIED`. This is source-informed
Class B synthetic builder evidence. Collection, credit repayment, real
funds, provider calls, live-chain behavior, durability and production
readiness were outside the verification.

The supervisor prohibited network and GitHub actions, including the
start-of-session fetch. The local workspace checks used the offline cache.
The missing Rust registry entries required the isolated kernel fallback.
Hosted Move, ZK and local-chain jobs were outside the local checks for
the touched paths. Publication is with the supervisor. The uncommitted
patch has no implementation or final task commit SHA, and there is no merge
SHA. Exact-head KTX kernel verification and KIX protocol verification
have no run ID, status or conclusion for this patch. A2 non-author review
and exact-head CI remain delivery gates.
