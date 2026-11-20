# Commerce late payment after booking cancellation vectors

## Task and base

`plan-commerce-late-payment-after-cancel` uses the supervisor's node specification
and read-only design plan as its task input. The source is planner run
`1795149680`, with the node recorded in
`/workspace/kix-run/logs/planner_1795149680_codex0.last.md`. There is no node
issue or task document under `docs/tasks/`.

Starting HEAD and the cached `origin/main` ref both resolved to
`652b02cbcf8e9265e469c96c55f8e841315a884e` on branch
`agent/kix-plan-commerce-late-payment-after-cancel`. The supervisor's
network restriction takes precedence over the routine fetch, leaving remote
freshness unverified. The implementation is a worktree patch. Implementation
and final task commit SHAs are pending the supervisor's commit.

## Existing coverage and new evidence

| Requirement | Coverage before this task | Evidence in this patch |
|---|---|---|
| Portable input and complete outcome associations | Partial. The linked-refund replay and companion validator cover the format and pins. The new history was absent. | `test_complete_output_bytes_and_references` validates all 16 command bodies against the published schemas, checks their literal order and identities, resolves the pointers and compares the complete canonical outcomes. The index adds 16 associations. Detached controls cross input and outcome pointers among the three same-action payment entries. |
| Late refusal and original-key replay | Partial. `test_hold_terminal_immutable_leaves_no_trace` checks a hold after release. `test_observe_payment_after_issue_leaves_no_trace` checks payment refusal after issuance. | Both calls against `order-1` return `TERMINAL_IMMUTABLE`. Canonical state, digests, accepted journals, both reservation views and the show match across both calls. |
| Cancellation receipt after reuse | Partial. `test_cancel_before_payment_frees_and_payment_blocks_compensation` replays cancellation before reuse. `test_expired_slot_retention_release_reuse_and_historical_replay` covers release after reuse. | The original cancellation receipt matches on replay except for `duplicate: true` and `applied: null`. The historical receipt shows slot 0 as `FREE` while the current snapshot shows `reserve-2` holding it. |
| Replacement payment, issuance, authorization and consumption | Covered for one buyer by `test_issued_credential_survives_cancellation_and_explicit_entry_stages`. The second booking after a refused late payment was uncovered. | Separate receipts record `PAYMENT_NOTED` with buyer 2's reference, `ISSUED` with active version-1 `issue-2` and `UNBOUND` settlement, `AUTHORIZED` with no consumption ID, then `CONSUMED_ONCE` at version 2. Journal prefixes and per-command deltas cover all five machines. |
| Compensation and qualification | Covered as open policy in the booking contract and earlier companion evidence. | Compensation flags are false where emitted and the settlement journal stays empty. The pack records the existing decision owners and retains the companion qualification boundaries. |

[Reservation tests](../../reference/booking_resale_admission/test_reservation_fsm.py) ·
[Rejection tests](../../reference/booking_resale_admission/test_reservation_rejection_atomicity.py) ·
[Hold-release test](../../reference/booking_resale_admission/test_commerce_hold_release_vectors.py) ·
[Admission-cancellation test](../../reference/booking_resale_admission/test_commerce_admission_cancellation_vectors.py) ·
[Linked-refund test](../../reference/booking_resale_admission/test_commerce_linked_refund_vectors.py) ·
[Late-payment replay](../../reference/booking_resale_admission/test_commerce_late_payment_after_cancel_vectors.py) ·
[Companion validator](../../reference/booking_resale_admission/test_commerce_companion_evidence_index.py)

## Local verification

Commands ran from the repository root with Python 3.12.15 and Rust 1.98.1.
Python checks used `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=.`.
In the commands below, `bra=reference/booking_resale_admission` and
`binding=validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`.

| Command | Result |
|---|---|
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_late_payment_after_cancel_vectors.py` | Exit 0. Four tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py` | Exit 0. Ten tests passed, covering 11 packs and 357 steps. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,067 booking tests passed. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the other seven workflow suites | All exit 0. Settlement 224, credit 305, AI delegation 182, token reward 397, provider facts 86, payment effects 28, economics 99. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0. Eleven tests passed. |
| `python3.12 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. All 139 tests passed using local fixtures and loopback. |
| Every invocation in [Stdlib offline document checks](../../.github/workflows/protocol.yml#L203), executed with `python3.12 -B` | All 69 exit 0. This includes the CI test discovery and checker wiring self-tests. |
| `python3.12 -B scripts/check_docs_index.py` and its `--self-test` | Both exit 0. The checker scanned 448 paths. |
| `python3.12 -B scripts/check_bra_evidence_map.py` and its `--self-test` | Both exit 0. The checker verified 39 rows and 219 citations. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and its `--self-test` | Both exit 0. The tuple pins 84 commands and 13 reads. |
| `python3.12 -B "$binding"` and its `--self-test` | Both exit 0. All 13 reads are `NOT_BOUND`. |
| `python3.12 -B scripts/check_openapi_contract.py` and its `--self-test` | Both exit 0. The pin covers 84 commands, 40 core and 44 FSM. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and its `--self-test` | Both exit 0. `productionEndpoint=false` and `publicHost=false`. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exit 0. Seven architecture tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0 with 139 passed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0 with 345 passed and one ignored. The ignored analytics test requires the owner-provisioned offline engine bundle. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0. The sole normal dependency is `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Produced the KTX workflow's three source digests. |
| `git rev-parse --verify origin/main` and `git rev-parse --verify HEAD` | Both resolve to `652b02cbcf8e9265e469c96c55f8e841315a884e`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both blobs matched before and after. |
| `python3.12 -B /tmp/kix-late-payment-preservation.py` | Exit 0. Compared worktree bytes against base Git blobs and compared the index against its base bytes. All 4,389 tracked paths outside the patch and all 10 prior packs with 341 associations match. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` for each new file | No whitespace diagnostics. The tracked diff exits 0 and the added file comparisons exit 1 with empty diagnostics. |

## Preservation and changed paths

The base comparison covers all 108 frozen reference files, prior vectors,
contracts, SDK, host and FSM sources, CI workflows, binding and producer pins,
`.aiops/` and `docs/tasks/`.

| Locked file | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

- `docs/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_late_payment_after_cancel_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_late_payment_after_cancel_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_late_payment_after_cancel_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `validation/2026-11-20-plan-commerce-late-payment-after-cancel/README.md`

## Scope and delivery gates

The refusal applies to the synthetic reservation command. Actual provider
facts remain subject to the state lifecycle contract. Refund liability,
actual late-fact custody, durability, chain finality, production admission
and external consumer operation are outside this evidence. Compensation is
**UNDETERMINED** with Astra and JunTae.
[State lifecycle §3](../../docs/contracts/STATE_LIFECYCLE.md#3-lc-fact--늦은-사실-보존)

This is source-informed evidence. Semantic consumption stays `HOLD_SEMANTIC`,
all 13 reads stay `NOT_BOUND`, SD1 stays `OPEN` and User-owned, and external
acceptance is `UNVERIFIED`. A2 non-author exact-HEAD review, hosted KTX kernel
and KIX protocol verification, and any post-merge checks are supervisor gates.
Both hosted workflows lack run IDs, statuses and conclusions for this patch.
No merge SHA applies. The replay matched the defined contract behavior.
Compensation is the existing unresolved product question for this history.

Local equivalents covered the offline reference and document checks and the
applicable Rust checks. Hosted bootstrap, external consumer, Move, local-chain
and ZK jobs were outside the local verification of these paths.
