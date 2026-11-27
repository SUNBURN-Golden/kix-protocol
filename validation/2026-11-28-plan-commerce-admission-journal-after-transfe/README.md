# Commerce admission journal after transfer

## Task and base

- The supervisor's inline node specification and design plan are the task input for `plan-commerce-admission-journal-after-transfe`. The node has no issue or file under `docs/tasks/`.
- Branch `agent/kix-plan-commerce-admission-journal-after-transfe`, cached `origin/main` and the starting branch HEAD all resolve to the design base `8c0118844b59c388c17d3e4b414ebc5f7036ab6c`.
- The implementation is in the worktree. The supervisor owns the implementation and final commit SHAs and GitHub delivery. User merge authorization applies.
- The acceptance predicates come from [BOOKING_RESALE_ADMISSION_GATES §§11.4–11.5](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#114-순서).

## Results and coverage

The two cases pin the predecessor input and receipt bytes by SHA-256 and Git blob ID. The ordered step references follow the primary payment observation at step 4, issuance at step 5 and admission authorization at step 10. The issued ticket journal is pinned through the predecessor receipt at step 7.

| Case | Replay checkpoint | Observed ownership | Local restore | Fresh local reconcile | New consumptions |
|---|---|---|---|---|---|
| `matching-ownership` | Step 12, `resale_set_clock` | `buyer-1`, version 1 | Canonical state equals the pinned checkpoint state | `matched: true`, `duplicate: false`, four entries | 0 |
| `transferred-ownership` | Step 15, `resale_accept_resale` | `buyer-2`, version 2 | `STALE_VERSION` | `STALE_VERSION` | 0 |

The four-entry, 1,009-byte admission journal is identical at both checkpoints. Its SHA-256 is `e31a859f8624df93e3fad0fead647519fdef5831a36c7bf347f6c714683030de`. The matching admission state digest is `d782c9eca0fd94583e3a4e9e4c99838805bfcc1c511c5d93fa412ac8a54e44d0`. Step 14 records the resale payment while ownership remains `buyer-1` at version 1. Step 15 records the explicit `transfer-1`.

| Requirement | Existing coverage before this node | Added evidence |
|---|---|---|
| Pin the command sequence and shared journal | Partial. `CommerceAdmissionReplayAfterResaleVectorTests.test_complete_output_bytes_and_references` reproduces the predecessor history. | The new fixture pins both source files and the canonical journal. The replay resolves and checks the ordered source steps and complete receipts. |
| Restore and reconcile with matching ownership | Partial. `AdmissionFsmTests.test_restart_replays_journal_and_retry_is_duplicate` covers a journal restore and reconciliation in the FSM. | The focused replay verifies the expired authorization's restored canonical state and a fresh reconciliation at the matching checkpoint. |
| Reject journal replay after explicit transfer with zero consumptions | Partial. `AdmissionFsmTests.test_restore_fails_closed_when_ownership_moves` checks direct restore. The predecessor checks a fresh consume after transfer. | The focused replay checks direct restore and fresh reconciliation independently and verifies all live canonical states, zero journal consumes and null consume IDs. |
| Reject a stale case labeled matched | Uncovered in the portable pack. | `test_rejects_stale_case_labeled_matched` tests false matches in each diagnostic with a recomputed companion output pin. |
| Index both published checkpoints and preserve consumer qualification | Partial. `CommerceCompanionEvidenceIndexTests.test_complete_index` checks coverage and read qualification. | `test_admission_journal_checkpoint_associations` verifies exact case, receipt and binding pointers and rejects crossed outcomes. The index covers 16 packs and 424 entries. |

All 13 consumer reads are `NOT_BOUND`, semantic consumption is `HOLD_SEMANTIC`, SD1 is `OPEN` and User-owned, and external acceptance is `UNVERIFIED`. The contract predicates reproduced locally. There were no contract violations or undefined characterizations observed in these cases.

## Changed paths

- `reference/booking_resale_admission/fixtures/commerce_admission_journal_after_transfer_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_admission_journal_after_transfer_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_admission_journal_after_transfer_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `validation/2026-11-28-plan-commerce-admission-journal-after-transfe/README.md`

## Local verification

Python verification used `PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`. In the table, `$bra` expands to `reference/booking_resale_admission`.

| Command | Result |
|---|---|
| `git rev-parse origin/main HEAD` | Both local refs matched the design base. |
| `git hash-object` for the two locked files and `git diff --exit-code HEAD -- reference/v0.3-rc1/` before editing | Both blob IDs matched and the historical reference diff was empty. |
| Inline Python 3.12 predecessor checkpoint probe with `FsmHost`, `ReservationMachine.restore`, `AdmissionMachine.restore` and `AdmissionMachine.reconcile` | All 16 receipts matched. The 1,009-byte journal and matching digest agreed with the design. Both post-transfer diagnostics raised `STALE_VERSION`. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_admission_journal_after_transfer_vectors.py -v` | 2 passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_admission_fsm.py -v` | 18 passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_admission_replay_after_resale_vectors.py -v` | 1 passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py -v` | 15 passed. |
| First `python3.12 scripts/check_docs_index.py` | Exit 1. The docs linked to this report before it was created. |
| `python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"` | All eight CI reference suites passed. `booking_resale_admission` 1,103, `settlement_f01_f03` 224, `credit_advance_f04` 339, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28, and `economics` 99. |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | Both passed after adding this report. |
| `python3.12 scripts/check_bra_evidence_map.py` and `--self-test` | Both passed. |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. Discovery reaches the new replay file. |
| `python3.12 scripts/check_producer_qualification_tuple.py` and `--self-test` | Both passed. |
| `python3.12 scripts/check_read_model_source_map.py` and `--self-test` | Both passed. |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | Both passed. |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | Both passed. |
| `python3.12 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and `--self-test` | Both passed. All 13 reads were `NOT_BOUND`. |
| `python3.12 -m unittest integration_gate.test_offline_limits` | 17 passed. |
| `python3.12 scripts/verify_runtime_architecture.py` and `python3.12 scripts/test_runtime_architecture.py` | Architecture gate passed. All 7 tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 during offline workspace dependency resolution. The cache lacks `duckdb`, required by `kix-analytics-audit`. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` and `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Both exited 101 on the same missing package. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` and `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Both exited 101 on the same missing package. |
| `cargo generate-lockfile --offline`, `cargo test -p kix-kernel --locked`, `cargo clippy -p kix-kernel --all-targets --locked -- -D warnings`, and `cargo tree -p kix-kernel --edges normal --locked`, each with the temporary manifest under `runtime/target/` | All passed in the two-crate workspace containing copies of the unchanged `kix-kernel` and `kix-types`. 139 tests passed. The temporary workspace was removed. |
| `git diff --check`, `git diff --exit-code HEAD -- .aiops/ docs/tasks/ .github/workflows/ reference/v0.3-rc1/`, `git rev-parse origin/main HEAD` and `git status --short --untracked-files=all` | Passed. Protected paths had no diff, both refs still resolve to the base and the changed paths match the list above. |
| Inline Python Git blob checks using `git ls-tree -rz HEAD -- reference/v0.3-rc1` and comparison of the companion index against `git show HEAD:docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json` | All 108 historical paths matched the base byte-for-byte. Both locked blobs matched. The original 15 packs and all index qualification fields matched the base. |

The locked blobs matched before and after work. `runtime/crates/kix-kernel/src/lib.rs` was `69564b166f0c27f9af5d8422f0a466b18d74c20f`, and `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` was `b607996c83a119c349f1cc90469ac1ba82764e20`.

## Deviations

The supervisor prohibited network access, so the base is the cached `origin/main` and remote freshness is unverified. The cited planner path had no file under that exact name. The suffixed `planner_1795791795_codex0.last.md` confirmed the supplied goal, acceptance and dependencies.

Workspace Rust verification requires a fuller offline dependency cache. The temporary two-crate run provides local kernel evidence. The full-workspace Cargo results and hosted exact-head results remain open.

## Limits and outstanding evidence

These are in-process mock observations over synthetic time. A historical replay match grants no admission authority. They establish no production admission, chain finality, durability, external consumer acceptance or legal and provider outcomes. Product TTLs, fees and compensation remain `UNDETERMINED` with their existing owners.

The delivery gates are hosted exact-head KTX kernel verification, hosted exact-head KIX protocol verification and A2 non-author review. This worktree has no delivery commit, run IDs, hosted results or merge SHA. Post-merge verification applies after an authorized merge.
