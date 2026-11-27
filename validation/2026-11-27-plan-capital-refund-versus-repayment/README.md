# Capital refund versus repayment

## Task and base

The task input is the supervisor-supplied specification and design for
`plan-capital-refund-versus-repayment`. The matching entry is in local planner
run `1795774962`, file `planner_1795774962_codex0.last.md`. The node has no
issue or file under `docs/tasks/`.

The starting HEAD of `agent/kix-plan-capital-refund-versus-repayment` and the
cached `origin/main` both resolved to
`a5d042d2c9b9bfbcc74d6537dc109a78bcbe26bb`, the stated base. The supervisor's
offline instruction superseded the startup fetch. Remote freshness is
unverified. The base includes the Capital Commerce checkpoints (merge #508),
Capital operation replay (merge #454), and shared-exposure contract (merge #441).

## Coverage and added evidence

| Acceptance requirement | Previous coverage | Added evidence |
| --- | --- | --- |
| Linked purchase, receipt associations and verbatim offer face | Partial. `CommerceLinkedRefundVectorTests.test_complete_output_bytes_and_references` covers the source receipts, and `CapitalCommerceRefundCheckpointTests.test_checkpoint_replay` compares the three checkpoints to a frozen face. | The new replay verifies all three raw source pins and ordered checkpoint refs, resolves the source command bodies, and checks the complete live settlement setup receipts. Both fresh branches reproduce the same pre-command bytes. |
| Equal-sized commands, distinct balances and isolated journal appends | Partial. `CommerceLinkedRefundVectorTests.test_purchase_stages_and_partial_acceptance` covers mock acceptance. `CapitalOperationReplayVectorTests.test_complete_history_vectors` and `CreditFsmTests.test_repayment_order_partial_and_double_application` cover repayment. | `CapitalRefundVersusRepaymentTests.test_refund_versus_repayment` compares both complete receipts and snapshots, verifies the arithmetic independently, checks the one exact appended entry per branch and compares the other machine's full snapshot with the common checkpoint. |
| Frozen face and shared exposure from each resulting credit view | Partial. `SharedExposureContractTests.test_frozen_face_unchanged_after_settlement_refund` and `test_repay_then_close_moves_exposure_only_via_transitions` cover separate scenarios. | Both branches preserve the original offer-face bytes. The replay checks the complete shared-exposure observations, totals, capacity and fail-closed flags from each branch's own credit view. |
| Indexed case/result associations and their rejection controls | Missing for this pair. Existing index tests cover swaps in other families and independently enforce the qualification owners. | The index adds both complete results with the same input and output artifact pins. The detached result-pointer swap resolves both valid receipts, then fails the family-specific association check. |

[Commerce replay](../../reference/booking_resale_admission/test_commerce_linked_refund_vectors.py) · [Capital checkpoints](../../reference/credit_advance_f04/test_capital_commerce_refund_checkpoints.py) · [Operation replay](../../reference/credit_advance_f04/test_capital_operation_replay_vectors.py) · [Credit FSM](../../reference/credit_advance_f04/test_credit_fsm.py) · [Shared-exposure tests](../../reference/credit_advance_f04/test_shared_exposure_contract.py) · [Comparison replay](../../reference/credit_advance_f04/test_capital_refund_versus_repayment.py) · [Index tests](../../reference/credit_advance_f04/test_capital_companion_evidence_index.py)

## Local verification

Python commands ran from the repository root with Python 3.12.15,
`PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`. In the commands below,
`bra=reference/booking_resale_admission` and
`f04=reference/credit_advance_f04`.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD refs/remotes/origin/main` | Started with a clean task branch at the cached main SHA above. |
| `PYTHONPATH=.:reference/credit_advance_f04 PYTHONDONTWRITEBYTECODE=1 python3.12 -B -` (two inline scripts) | Captured both complete mock outcomes into the canonical fixture. Appended a single family with two result pointers to the existing Capital JSON index. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_linked_refund_vectors.py` | 5 passed on each of two runs. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p "$test.py"` for `test_capital_commerce_refund_checkpoints`, `test_capital_operation_replay_vectors`, and `test_shared_exposure_contract` | 2, 10 and 19 passed, respectively. |
| Same focused discovery for `test_capital_refund_versus_repayment` and `test_capital_companion_evidence_index` | 1 replay test passed on both runs. All 22 index tests passed, including the valid-pointer swap control. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the eight workflow suites | Passed. `settlement_f01_f03` 224, `credit_advance_f04` 339, `booking_resale_admission` 1,099, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28, `economics` 99. |
| `python3.12 -B scripts/check_openapi_contract.py` and `python3.12 -B scripts/check_integration_gate_openapi.py`, each plain and with `--self-test` | Four invocations passed. Both contracts cover 84 commands. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 16 passed. |
| `python3.12 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | 139 passed. The HTTP suite emitted a `ResourceWarning` for an unclosed stream. |
| `python3.12 -B -` invoking each Python command in `.github/workflows/protocol.yml` under **Stdlib offline document checks** | 69 of 69 invocations passed. This includes the docs index, CI discovery, and settlement, credit and Commerce evidence maps and their self-tests. |
| `python3.12 -B scripts/check_docs_index.py` and `python3.12 -B scripts/check_ci_test_discovery.py`, each plain and with `--self-test` | All four final checks passed. The docs checker scanned 478 documents. CI discovery found 36 F04 test files. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed and all 7 architecture tests passed. |
| `cargo fmt --all -- --check` in `runtime/` | Exit 0 on Rust 1.98.1. |
| `cargo test -p kix-kernel --locked --offline`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, and `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | Each exited 101 at dependency resolution because `kix-analytics-audit` requires the missing `duckdb` registry entry. |
| `cargo test --workspace --locked --offline` and `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in `runtime/` | Both exited 101 at the same dependency resolution step. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` | Exit 1. The cache held 16 of 378 locked registry archives. Missing entries included `duckdb`, `libduckdb-sys` and `bcs`. |
| `CARGO_NET_OFFLINE=true python3.12 -B -` for the temporary workspace | Copied the six local-only crates and reused their original Cargo lockfile blocks. `diff -qr` passed for every crate copy. |
| `cargo test -p kix-kernel --locked --offline --quiet` and the same kernel Clippy and dependency-tree commands in the temporary workspace | All passed. Kernel tests counted 139 passes. The normal dependency tree listed only `kix-types`. |
| `cargo test --workspace --locked --offline --quiet` and `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in the temporary workspace | 332 tests passed and Clippy exited 0. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Recorded all three KTX workflow input hashes locally. |
| `git hash-object` on the locked files and the new fixture, and `sha256sum` on the three pinned sources and the new fixture | Both locks, all source hashes and the new fixture pins matched. |
| Sorted path-and-SHA-256 manifest via `python3 -B -` before edits and `python3.12 -B -` after verification | All 108 paths and hashes matched byte for byte. |
| `git diff --check`, `git status --short --untracked-files=all`, scoped `git diff --exit-code HEAD`, and inline Python with `git ls-files` and `git show` | Whitespace and protected scope checks passed. Exactly eight intended paths changed. Both new artifact pins and all preceding index bytes matched. |

## Protected bytes and fixture identities

| Artifact | Verified identity |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` before and after |
| `reference/v0.3-rc1/**` | 108 files, manifest SHA-256 `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` before and after |
| `commerce_linked_refund_inputs_v1.json` | SHA-256 `55e319f9ae179d09a69b1665c203dedbee0690ed32b827ee987cd80490db67a6` |
| `commerce_linked_refund_receipts_v1.json` | SHA-256 `7181761ec5533cf1a9aab450f4a7f3d32ed6c467713c8d532ceff24a89908839` |
| `capital_commerce_refund_checkpoints_vectors_v1.json` | SHA-256 `6d0ac8fb018d5bdb55a388eb8353ab538e533bdb3ad547de72d75de02714085a` |
| `capital_refund_versus_repayment_vectors_v1.json` | SHA-256 `72b637b7e7209e36303fe4faa890c2339263ef3ae02e256d7e7c6410aef2a5e4`, Git blob `75183634816a2c93f2e598bb3e5ccac7bcf83728` |

## Files changed

- `docs/README.md`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `reference/credit_advance_f04/fixtures/capital_refund_versus_repayment_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `reference/credit_advance_f04/test_capital_refund_versus_repayment.py`
- `validation/2026-11-27-plan-capital-refund-versus-repayment/README.md`

## Deviations

The supervisor's offline rule superseded the startup fetch. Local Python
verification used the workflow's Python 3.12 version. The test compares all
five live settlement setup receipts with their Commerce goldens, including
the required commit and refund-binding receipts.

The temporary Rust workspace covered `kix-types`, `kix-feature-semantics`,
`kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and `kix-delegated-exec`.
Full-workspace Rust test and Clippy results remain unverified for
`kix-analytics-audit` and `kix-bcs1`. Hosted provisioning, SDK, Move, storage,
chain and ZK stages are outside the touched-path local check.

The repayment note uses the fixture identifiers `repayment-note-1` and
`repay-refund-comparison-1` for the note and idempotency key. The observation
uses the caller label `fixture-refund-versus-repayment`.

## Scope and remaining gates

The replay supplies source-informed Class B evidence from two process-local
mocks. No contract violation or additional contract-undefined behavior was
observed. External `kix-capital` acceptance is `UNVERIFIED`. Product limits
remain `UNDETERMINED` with Astra, and legal liability remains
`UNDETERMINED` with the User and legal counsel. Evidence covers fixture receipts,
in-memory journals and caller-supplied observations. Live funds, external
providers, public endpoints, legal compliance, durability, distributed
execution, chain finality and production readiness are outside that evidence.

Implementation and final task commit SHAs await the supervisor's commit.
A2 non-author review and exact-head KTX and KIX run IDs, statuses and
conclusions are pending delivery gates. Merge SHA and post-merge CI are
inapplicable to the working-tree patch.
