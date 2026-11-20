# Commerce linked purchase and partial refund vectors

## Task and base

`plan-commerce-linked-refund-vectors` uses the supervisor-supplied node specification
and Claude design as its task document. The specification cites planner run
`1795084226`. The node has no issue or file under `docs/tasks/`.

The local `origin/main` tracking ref and starting task HEAD were both
`20156a20324941e440dd44e29fc5c9602749478c`. The branch is
`agent/kix-plan-commerce-linked-refund-vectors`. The supervisor prohibits network
and GitHub actions, so this session used the pre-fetched ref and remote freshness
is unverified. The work is delivered as a working-tree patch. Implementation and
final task commit SHAs are pending the supervisor's commit. No merge SHA applies.

## Existing coverage and new evidence

| Requirement | Existing coverage | Linked history evidence |
|---|---|---|
| Complete linked replay and exact pointers | Partial. `CommerceBoundIssuanceVectorTests.test_commit_is_separate_from_explicit_fresh_key_issuance` covers commitment and issuance. The original `CommerceJourneyReceiptTests.test_complete_output_bytes` has a separate refund settlement. | One 18-step history validates schemas, literal action order and shared identity. `test_complete_output_bytes_and_references` compares the full canonical output and resolves each pointer to its input. Detached controls change a receipt, cross a valid pointer, cross the settlement ID, and submit a malformed amount. |
| Post-issue reservation refusal | Covered for unbound issuance by `CommerceAdmissionCancellationVectorTests.test_issued_credential_survives_cancellation_and_explicit_entry_stages`. | The linked history exercises `CANCEL_AFTER_ISSUE` and compares the complete detached snapshots before and after, including all five machines' state, digests and accepted journals. |
| Partial cancellation acceptance with the right and admission journal intact | Partial. `CancelAcceptanceAdapterTests.test_partial_acceptance_and_replay_after_later_changes_match_direct` covers direct settlement parity and arithmetic. | `test_purchase_stages_and_partial_acceptance` compares the entire settlement view around acceptance and proves that only settlement appends a journal entry. Refund face stays `4000`, accepted goes `0 → 1500`, outstanding goes `4000 → 2500`, and PG adjustment goes `0 → 1500`. Cash stays `10001`, the complete issued right and populated admission journal are preserved, and `external_return_closed` and `right_cancelled` are false in the view and claim. |
| Separate authorization and consumption receipts | Covered for unbound issuance by the admission cancellation replay above. | `test_explicit_authorization_and_consumption_preserve_settlement` checks `AUTHORIZED` with an empty consumption ID, then `CONSUMED_ONCE` and right version `2`, with identical settlement state, digest, view and journal across those two commands. |
| Index and binding | Partial. The companion mapped nine packs with 323 associations and the binding index already covered the commands. | The tenth pack adds 18 associations. The companion checker rejects crossed input, outcome and binding references. The consumer binding checker verifies all 13 reads are `NOT_BOUND`. |

Paths for those regressions and the new portable artifacts are linked below.
[Bound issuance](../../reference/booking_resale_admission/test_commerce_bound_issuance_vectors.py) ·
[Original journey](../../reference/booking_resale_admission/test_commerce_journey_receipts.py) ·
[Admission cancellation](../../reference/booking_resale_admission/test_commerce_admission_cancellation_vectors.py) ·
[Cancellation acceptance adapter](../../reference/settlement_f01_f03/test_cancel_acceptance_adapter.py) ·
[Linked replay](../../reference/booking_resale_admission/test_commerce_linked_refund_vectors.py) ·
[Companion checker](../../reference/booking_resale_admission/test_commerce_companion_evidence_index.py)

## Local verification

Commands ran from the repository root with Python 3.12.15 and Rust 1.98.1.
In the table, `bra=reference/booking_resale_admission` and
`binding=validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`.
Each suite in the reference discovery loop ran with `PYTHONPATH=.`.

| Command | Result |
|---|---|
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_linked_refund_vectors.py` | Exit 0, 5 tests. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py` | First run exit 1 with two failures. The old case-reversal control was a no-op for the new singleton case, and one assertion still expected 323. Updated both and reran, exit 0 with 9 tests. |
| `python3.12 -B "$binding"` and `python3.12 -B "$binding" --self-test` | Both exit 0, `reads=13 not_bound=13`, 10 negative controls. |
| `PYTHONPATH=. python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` | All exit 0. `booking_resale_admission` 1,058, `settlement_f01_f03` 224, `credit_advance_f04` 298, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28, `economics` 99. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0, 11 tests. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0 with pipefail enabled, 139 tests. |
| Every Python invocation in the protocol workflow's [Stdlib offline document checks](../../.github/workflows/protocol.yml#L203), executed as `python3.12 -B` | 69 commands exit 0, including `scripts/check_docs_index.py` and its `--self-test`. |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both exit 0. Catalogue has 84 commands, 40 core and 44 FSM. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0, `productionEndpoint=false`, `publicHost=false`. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exit 0, 7 architecture tests. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0, 139 passed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0, 345 passed and 1 ignored. The existing analytics engine test requires an owner-provisioned offline bundle. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0. Only direct normal dependency is `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. KTX workflow source digests recorded locally. |
| `git rev-parse HEAD` and `git rev-parse --verify refs/remotes/origin/main` | Both resolve to `20156a20324941e440dd44e29fc5c9602749478c`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after, both match the required Git blobs listed below. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` for each new file | No whitespace diagnostics. The initial preservation wrapper expected exit 0 from `--no-index`. The corrected wrapper accepts its exit 1 for an added file with empty diagnostics. |
| Python raw-byte comparison against `git ls-tree -r -z` at the base, and index comparison against `git show` at the base | 4,372 tracked paths match, including all 108 frozen reference files. The serialized prefix and contents of all nine original companion packs and 323 associations match. |

The full reference discovery included existing local loopback tests. Its child
Python processes generated ignored bytecode caches that were removed from the
frozen reference tree. Subsequent check batches set `PYTHONDONTWRITEBYTECODE=1`
for child processes. Hosted bootstrap, Move, chain, ZK and external consumer
checks remain outside the local verification of these paths.

## Preservation and changed paths

The two locked blobs matched before and after, including the raw bytes in the
worktree.

| Path | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The base comparison covers the frozen reference, prior vectors, contracts,
OpenAPI, SDK, FSM and host sources, both workflows, the binding index, the
producer tuple, `.aiops/`, and `docs/tasks/`.

- `docs/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_linked_refund_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_linked_refund_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_linked_refund_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `validation/2026-11-20-plan-commerce-linked-refund-vectors/README.md`

## Scope and delivery gates

The evidence establishes source-informed in-process mock behavior and byte
identity. The vector exercises no external provider, bank, legal liability,
venue admission, production runtime, durability or chain finality. Compensation
policy stays **UNDETERMINED** with Astra and JunTae. Legal refund liability stays
**UNDETERMINED** with JunTae and legal counsel. No contract violation or new
contract-undefined characterization was found in the replay.

Semantic consumption stays `HOLD_SEMANTIC`, SD1 stays `OPEN` and User-owned, and
external consumer acceptance stays `UNVERIFIED`. The KTX kernel verification
and KIX protocol verification workflows have no run ID, status or conclusion
for this uncommitted patch. A2 non-author exact-HEAD review, hosted exact-HEAD
CI, and any post-merge checks are separate supervisor delivery gates.
