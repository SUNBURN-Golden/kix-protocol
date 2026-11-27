# Cross-order issuance companion vectors

The task is `plan-commerce-cross-order-issuance`. The supervisor supplied the
node specification and design plan in the builder prompt. This loop-proposed
node has no issue or task file. The task branch is
`agent/kix-plan-commerce-cross-order-issuance`. Its starting HEAD and cached
`origin/main` both resolved to `6d1dec5edd033635fd057f3caefd5ec36d7b8ba6`.
That agrees with the design base. The supervisor's offline rule superseded the
session-start fetch, so remote freshness is unverified. The builder handoff is
an uncommitted worktree on that SHA. Implementation, final delivery and merge
commit SHAs are pending supervisor publication.

Planner run `1795815309` was available locally as `planner_1795815309_codex0.out`.
Its node objective, dependencies and acceptance criteria matched the prompt.

## Acceptance and coverage

| Requirement | Existing coverage | Evidence added |
|---|---|---|
| Pinned `payment-2` checkpoint | Sufficient for predecessor behavior. `CommercePaymentRefScopeVectorTests.test_complete_output_bytes_and_references` verifies the original 16 outcomes. | The new replay verifies both raw-byte pins, resolves the two checkpoint references and replays the complete history in each fresh host, including the step-9 `PAYMENT_BINDING_CONFLICT`. Both hosts have identical detached checkpoint snapshots. |
| Collision with an already transferred issuance | Partial. `ReservationRejectionAtomicityTests.test_issue_binding_conflict_leaves_no_trace` uses `order-9`. | A paid `order-2` on `show-2` reuses `issue-1` and receives `ISSUANCE_BINDING_CONFLICT`. All five accepted journals, canonical states, digests and views equal the branch baseline. The reservation stays `PAYMENT_NOTED` with the payment and `RESERVED` slot retained and no right. |
| Distinct issuance | Partial. `ReservationFsmTests.test_unbound_issue_is_memory_evidence_without_economic_finality` exercises ordinary mock issuance. | A fresh `issue-2` adds one reservation journal entry with an intact prefix, preserves the other journals and issues exactly one version-1 right on `show-2` for `buyer-3`. |
| Resale and admission isolation across the new branches | Uncovered for this branch pair. The original replay verifies the transfer before `payment-2`. | Both branches compare the `show-1` views to the baseline, preserve `transfer-1` and `buyer-2` at version 2, and assert zero `consume` entries and null `consume_id` on both reservations. |
| Complete outcome associations | Partial. `CommerceCompanionEvidenceIndexTests.test_association_controls` covers other packs. | Both complete outcomes use the existing item 58 `MOCK_EVIDENCE` binding. Detached controls swap the input and outcome references independently and require the corresponding association error each time. The original index validates. |

The observed accepted journal lengths are 0 settlement, 10 reservation,
5 resale, 0 admission and 0 credit at the checkpoint. Only the distinct
issuance changes any length, raising reservation to 11.
[Canonical inputs and checkpoint pins](../../reference/booking_resale_admission/fixtures/commerce_cross_order_issuance_inputs_v1.json) ·
[Complete outcomes](../../reference/booking_resale_admission/fixtures/commerce_cross_order_issuance_receipts_v1.json) ·
[Replay](../../reference/booking_resale_admission/test_commerce_cross_order_issuance_vectors.py) ·
[Index](../../docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json)

## Changed paths

- `reference/booking_resale_admission/fixtures/commerce_cross_order_issuance_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_cross_order_issuance_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_cross_order_issuance_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `validation/2026-11-28-plan-commerce-cross-order-issuance/README.md`

## Local verification

The Python suites ran from the repository root with `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`. Below, `bra` is
`reference/booking_resale_admission`. The focused tests ran before the
broader workflow checks.

| Command | Actual result |
|---|---|
| Inline Python 3.12 `FsmHost` probe through both branches | Observed the checkpoint `PAYMENT_BINDING_CONFLICT`, one accepted `issue-2`, and `ISSUANCE_BINDING_CONFLICT` for `issue-1`. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_cross_order_issuance_vectors.py` | Exit 0. 1 test passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_payment_ref_scope_vectors.py` | Exit 0. 3 tests passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py` | Exit 0. 16 tests passed, covering 17 packs and 426 associations. |
| First `python3.12 -m unittest discover -s "$bra" -t "$bra"` | Exit 1. One existing admission-console subprocess reached its 10-second timeout. The other 1,104 tests passed. |
| `PYTHONPATH=.:reference/booking_resale_admission PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest -v test_admission_console.AdmissionConsoleTests.test_documented_transcripts_as_cli_subprocesses` | Exit 0. The previously timed-out test passed in 0.792 seconds. |
| `python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the eight workflow suites | Exit 0 in all eight suites. `booking_resale_admission` 1,105 on the full rerun, `settlement_f01_f03` 224, `credit_advance_f04` 339, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99. The rerun used the original timeout and test code. |
| `python3.12 scripts/check_{docs_index,bra_evidence_map,ci_test_discovery,producer_qualification_tuple,contract_error_codes,openapi_contract,integration_gate_openapi}.py`, each invoked separately and repeated with `--self-test` | All 14 invocations exited 0. |
| `python3.12 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and repeat with `--self-test` | Both exited 0. The checker found all 13 reads `NOT_BOUND`. |
| `python3.12 -m unittest integration_gate.test_offline_limits` | Exit 0. 18 tests passed. |
| `python3.12 scripts/verify_runtime_architecture.py` and `python3.12 scripts/test_runtime_architecture.py` | Both exited 0. Architecture and dependency gate passed, and 7 tests passed. |
| `cargo fmt --all -- --check` in `runtime/` | Exit 0. |
| `cargo test -p kix-kernel --locked --offline`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, and `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | Each exited 101 before compilation. Offline resolution could not find `duckdb` for `kix-analytics-audit`. |
| `cargo test --workspace --locked --offline` and `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in `runtime/` | Both exited 101 on the same missing offline dependency. |
| Inline Python 3.12 temporary mirror using `diff -qr`, `cmp`, `cargo generate-lockfile --manifest-path "$manifest" --offline` and `tomllib` | Exit 0. Six byte-matched local crate trees, pinned toolchain and six matching lock records. |
| `cargo test --quiet --manifest-path "$manifest" -p kix-kernel --locked --offline` and `cargo test --quiet --manifest-path "$manifest" --workspace --locked --offline` | Both passed in the temporary mirror. 139 kernel tests and 332 tests across the six crates. |
| `cargo clippy --quiet --manifest-path "$manifest" -p kix-kernel --all-targets --locked --offline -- -D warnings` and `cargo clippy --quiet --manifest-path "$manifest" --workspace --all-targets --locked --offline -- -D warnings` | Both passed in the mirror. |
| `cargo tree --manifest-path "$manifest" -p kix-kernel --edges normal --locked --offline` | Exit 0 in the mirror. The sole normal dependency is `kix-types`. The mirror was removed after the checks. |
| `git rev-parse origin/main HEAD HEAD:reference/v0.3-rc1` | Both refs matched the base. The historical subtree ID was `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git hash-object --` for the two locked kernel paths and both predecessor fixtures, before and after | All four blobs matched. The two checkpoint pins are recorded in the new input fixture. |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks .github docs/contracts integration_gate sdk`, `git ls-files --others --exclude-standard --` on those paths, and a direct `git ls-tree -rz HEAD` blob comparison | No changed or untracked paths in these areas. All 108 historical files matched the base byte-for-byte. |
| `git diff --check`, `git status --short --branch --untracked-files=all`, and inline Python using `git show HEAD:docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json` and `git ls-files --others --exclude-standard -z` | Exit 0. The changed paths match the list above and all four new files passed the whitespace check. The original index metadata, 16 packs and 424 associations matched the base. |
| `git hash-object --` and `sha256sum` for both new fixtures | Input blob `c360312479717032ac695d4d9bee74c1d6d7407e`, SHA-256 `7e60aa2daab71d4477c514c4656a3333483a8fcebaf4ee8a13d6f956568bd6cb`. Outcome blob `77337b1ee16b09bf2d7c7b1817b85b00f89d9e27`, SHA-256 `b32a8274c7aaebd95befc0380ca634562651ad5f321efbc754bb9a2994545262`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Computed the three KTX workflow input digests. |

The two locked blobs matched before and after work. `runtime/crates/kix-kernel/src/lib.rs`
matched `69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs` matched
`b607996c83a119c349f1cc90469ac1ba82764e20`.

The Rust fallback ran with `CARGO_NET_OFFLINE=true` using a temporary manifest
under `runtime/target/`. It contained `kix-types`, `kix-feature-semantics`,
`kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and `kix-delegated-exec`.
The temporary mirror and its generated artifacts were removed. Full workspace
test, Clippy and dependency resolution remain unverified. The local checks
covered the touched paths without the workflow's bootstrap, Move, chain and ZK
stages.

## Remaining gates and evidence scope

KTX kernel verification and KIX protocol verification for the eventual
delivery head both have run ID, status and conclusion unobserved. The A2
non-author exact-head review and the supervisor's delivery and subsequent
user-controlled merge remain pending. Post-merge evidence is inapplicable
to this uncommitted worktree.

The replay follows the existing mock issuance transition and conflict rule.
No contract discrepancy or newly required policy was identified. The observed
collision is bounded to the two-show in-process history and its accepted
business journals. Durable recovery, real provider or funds behavior, chain
finality, legal compliance and production readiness remain outside this evidence.
The pack remains `HOLD_SEMANTIC`, the 13 reads remain `NOT_BOUND`, SD1 remains
`OPEN` and User-owned, and external `kix-commerce-apps` acceptance remains
`UNVERIFIED`. TTLs, fees and compensation remain `UNDETERMINED` with Astra and
the User. Provider and legal terms retain their existing owners.
