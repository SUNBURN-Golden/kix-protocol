# Synthetic payment lookup to reservation observation

The offline example takes a confirmed reservation to `PAYMENT_NOTED` by observing
one 15,000 KRW payment on its bound fake. It retains both the lookup evidence
and the reservation response. The slot stays reserved and issuance stays absent.

The task input is the supervisor’s inline `plan-local-payment-reservation-handoff`
node and design, with the 2026-11-18 owner decision on local and hosted
verification. There is no task issue or node-specific file in `docs/tasks/`.
The Track P charter is `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md`. Scope
comes from `docs/DEVELOPMENT_PLAN.md`, `PROGRAM_DECISIONS_20260928` §§2.1/5
and `BOOKING_RESALE_ADMISSION_GATES` §§3/9.

## Worktree and base

The builder resumed the 2026-10-31 draft and retained its validation path and
offline runner. This record reports the 2026-11-19 verification on the assigned
`agent/kix-plan-local-payment-reservation-handoff` worktree.

| Revision | Observed value |
|---|---|
| Task base and local HEAD before and after verification | `8f7eedaef3e2cc74dcc6e19363c0096908796145` |
| Local `origin/main` | `5a1735824305f902036c97b3b31f503abe76bae5` |
| Base delta | Task branch 0 ahead, 242 behind the cached ref. The supervisor prohibited fetching or changing the task base. Remote freshness is unverified. |
| Implementation head and final task head | Pending supervisor commit. The local HEAD identifies the base only. |
| Merge commit and post-merge CI | Inapplicable to this uncommitted builder handoff |

## Coverage mapping recorded before adding adapter tests

Existing tests are source-informed evidence, not independent verification.
Paths below are relative to `reference/`.

| Requirement | Existing evidence | Classification / gap |
|---|---|---|
| Dispatch to original fake | `provider_facts/test_payment_lookup_router.py::PaymentLookupRouterTests.test_two_scopes_dispatch_only_to_bound_fake` | Partial: composition with reservation absent |
| Confirm/payment/issuance separation, no finality | `booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_unbound_issue_is_memory_evidence_without_economic_finality` | Partial: no lookup handoff |
| Complete identity and amount validation | `provider_facts/test_payment_lookup_router.py::PaymentLookupRouterTests.test_complete_identity_and_outputs_equal_single_scope_service`, `booking_resale_admission/test_reservation_rejection_atomicity.py::ReservationRejectionAtomicityTests.test_observe_payment_amount_mismatch_leaves_no_trace` | Partial: need zero observation calls for handoff mismatches |
| Missing binding/route, timeout, not-found, unverified source and no fallback | `provider_facts/test_payment_lookup_router.py::PaymentLookupRouterTests.test_missing_binding_and_route_make_zero_calls`, `test_unresolved_scope_never_falls_back`; `provider_facts/test_payment_lookup.py::PaymentLookupTests.test_unresolved_boundaries_preserve_state_and_make_one_call` | Sufficient lookup coverage; missing composition state/evidence preservation |
| Cancellation history | `provider_facts/test_payment_lookup.py::PaymentLookupTests.test_full_cancellation_preserves_capture_and_has_independent_expected_history`; `provider_facts/test_one_payment_history.py::OnePaymentHistoryTests.test_cancels_are_items_of_one_payment_not_a_batch` | Sufficient normalization; missing non-application at handoff |
| Replay, first result and key conflict | `booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_restore_replays_a_lost_success_and_omits_rejections`, `test_same_key_conflict_does_not_move_phase` | Sufficient FSM coverage; missing composed explicit replay |
| Integer amounts and raw timestamps | `provider_facts/test_integer_krw.py`, `test_timestamps.py`, `test_normalization_golden_vectors.py` literal vectors | Sufficient normalization; need handoff pass-through and differing range boundary |
| Runnable offline composition | Existing lookup examples do not invoke reservation | Not covered |
| Discovery and OpenAPI pins | `scripts/check_ci_test_discovery.py`, `check_openapi_contract.py`, `check_integration_gate_openapi.py` | Existing checkers reused unchanged |

## Implemented behavior and new gap coverage

The adapter retains the actual lookup object and the actual FSM response or
`ReservationError` separately. It only invokes `observe_payment`, with the
configured local order, caller-supplied mock payment reference and key, and the
exact integer evidence amount. A complete fixture association is required;
provider/local order IDs deliberately differ in the example. No phase guard
interferes with first-result replay. There is no adapter cache or retry.

The 19 new tests are in
`reference/provider_facts/test_payment_reservation_handoff.py::PaymentReservationHandoffTests`:

| New test | Gap addressed |
|---|---|
| `test_primary_payment_handoff` | Confirmed reservation, original fake once, unchanged response identity, exactly one accepted observation, retained slot, absent issuance/right/settlement, all non-claim flags false |
| `test_association_validation_and_frozen_configuration` | Exact reference types, existing identifier/key/mock-ref formats, frozen configuration |
| `test_every_submitted_operation_dimension_requires_exact_match` | Provider/account/operation changes cause zero lookups and zero observations |
| `test_every_associated_payment_dimension_requires_exact_match` | Each of five payment identity fields checked against configured association |
| `test_lookup_envelope_history_and_item_identities_are_checked` | Complete operation envelope and five payment fields at envelope/history/item boundaries checked; zero observation calls |
| `test_inconsistent_association_scope_cannot_apply_even_consistent_lookup` | Provider/account must agree across operation and payment even if returned payment/history match each other |
| `test_local_order_and_reservation_are_explicit` | Wrong order, missing reservation and a different existing reservation/order cannot apply |
| `test_amount_mismatch_and_provider_reservation_range_boundary` | Mismatches, zero, `10**12+1`, `2**53+1`, u128 maximum retained without application; exact 1 and `10**12` accepted |
| `test_currency_and_noninteger_defense_before_observation` | Currency, bool, float and string evidence/view values rejected before observation |
| `test_unresolved_and_missing_configuration_preserve_state_without_fallback` | Missing binding/route, timeout, lookup error, not-found, unverified source, float lexeme; two explicit submissions each call original fake once; alternate successful fake never selected |
| `test_cancellation_histories_are_retained_intact` | Partial/full/multiple cancels, canceled statuses with no entries, DONE with cancel entries; original histories/hashes unchanged |
| `test_nonprimary_histories_are_not_applied` | Empty/multiple payment histories, cancel-only and unsupported status cannot apply |
| `test_raw_timestamp_receipt_details_and_hashes_survive` | Raw occurrence/receipt and offset-less createdAt, nested details and hashes preserved |
| `test_explicit_success_replay_and_replay_after_separate_issue` | Same adapter used for all three submissions. Duplicate success returns the original PAYMENT_NOTED snapshot after a separate issue. Three original-fake lookups and one accepted observation |
| `test_rejection_is_retained_after_separate_transition` | Expired rejection stays cached after explicit cancellation; separately caller-selected new key gets existing terminal rejection |
| `test_conflicting_key_is_not_replaced` | Existing key with different mock reference returns FSM conflict, no generated replacement key or retry |
| `test_returned_mutable_evidence_does_not_change_later_explicit_results` | Caller mutations do not alter recording or first-result snapshots |
| `test_only_reservation_errors_are_enveloped` | Actual observation exception object preserved; unrelated lookup/view/observation programming errors propagate |
| `test_offline_example_callable_and_subprocess_agree` | Callable/standalone deterministic output equivalent, one fake call, no issuance/right |

Tests retain populated binding capture/review evidence and recording snapshots;
blocked paths compare full public `canonical_state` (including accepted journal).
Lookup and observation spies prove call bounds and returned-object preservation.
These are source-informed composition tests. Existing normalization vectors and
FSM tests remain the evidence for their separate contracts.

## Builder verification on 2026-11-19

Commands ran from the repository root. Python tests and checkers used
`PYTHONDONTWRITEBYTECODE=1`. The checker rows with two invocations give the
plain command and its `--self-test` run. Each verification command below exited 0.

| Command | Observed result |
|---|---|
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p test_payment_reservation_handoff.py` | 19 passed |
| `python3 reference/provider_facts/example_payment_reservation_handoff.py` | One original-fake call, one accepted observation, 15,000 KRW, reserved slot, no issuance or right, execution and finality flags false |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | 92 passed, including the 19 adapter tests |
| `python3 validation/2026-10-31-plan-local-payment-reservation-handoff/run_booking_offline.py` | 417 passed. The unchanged runner barred sockets and reported exactly one exclusion. |
| `PYTHONPATH=reference/booking_resale_admission python3 -m unittest test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit` | 1 passed on the owner-authorized 127.0.0.1 loopback. Both FSM names yielded HTTP 400 and the published admit operation returned the expected rejection. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Full unchanged suite, 418 passed, including the same HTTP test |
| `python3 -m unittest integration_gate.test_offline_limits` | 9 passed |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Both passed. 84 commands (40 core, 44 FSM). SHA-256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`, Git blob `619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Both passed. 84 commands, public host and production endpoint flags false |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. Protocol workflow reaches all 15 provider test files, including the handoff, and all 17 booking test files. 18 negative controls passed. |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | Both passed. 35 scripts and 13 negative controls |
| `python3 scripts/check_bra_evidence_map.py` and `--self-test` | Both passed. 39 booking/resale/admission evidence rows |
| `python3 scripts/check_adapter_identity_map.py` and `--self-test` | Both passed, including the locked blob checks |
| `python3 scripts/check_toss_card_profile_evidence_map.py` and `--self-test` | Both passed. 41 rows, 3 positive and 77 negative controls |
| `python3 scripts/check_docs_index.py` and `--self-test` | Both passed |
| `rustc --version`, `cargo --version` | Both 1.98.1 |
| `python3 scripts/check_cargo_offline_cache.py` | 18 of 18 locked registry archives present |
| `cargo fetch --manifest-path runtime/Cargo.toml --offline --locked` | Resolved from local cache |
| `python3 scripts/verify_runtime_architecture.py`, `python3 scripts/test_runtime_architecture.py` | Architecture gate passed, 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 139 passed in 9 result groups |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 339 passed in 46 result groups, zero failed or ignored. Includes the kernel. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Passed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Passed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed |
| `git diff --check` | Passed |
| `git status --short --branch`, `git rev-parse origin/main HEAD`, `git rev-list --left-right --count HEAD...origin/main` | Resumed draft on the assigned branch, revisions and delta above |
| `git status --short --untracked-files=all` | Seven delivery paths listed below |

The two overlapping booking results are reported separately. The offline runner
still excludes exactly
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The owner assigned authoritative verification of that test in the full unchanged
suite to hosted exact-head CI. Loopback was available for the additional builder
run. Hosted results are pending.

## Changed files and protected paths

- `reference/provider_facts/payment_reservation_handoff.py`
- `reference/provider_facts/example_payment_reservation_handoff.py`
- `reference/provider_facts/test_payment_reservation_handoff.py`
- `reference/provider_facts/README.md`
- `docs/README.md`
- `validation/2026-10-31-plan-local-payment-reservation-handoff/README.md`
- `validation/2026-10-31-plan-local-payment-reservation-handoff/run_booking_offline.py`

| Byte check | Before and after |
|---|---|
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The exact working directory path set and all 108 file blobs match `git ls-tree -r HEAD -- reference/v0.3-rc1`. |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 reference/booking_resale_admission .aiops docs/tasks .github docs/contracts sdk integration_gate` | Empty |

## Delivery gates and limits

The owner resolved the earlier verification decision. `DECISION_REQUIRED.md`
was already absent on resumption. The offline runner remains as supplied.
The builder performed no GitHub action or external service call.

| Required before merge readiness | Evidence for a committed final head |
|---|---|
| Non-author review, A2 floor | Pending |
| KTX kernel verification | Pending. Run ID, status and conclusion unobserved. |
| KIX protocol verification, including the unchanged booking suite | Pending. Run ID, status and conclusion unobserved. |

The tests establish in-process synthetic composition. No explicit contract
violation was found. Adapter diagnostic reasons and their precedence describe
local behavior (class B). Provider authentication and merchant scope remain
**UNDETERMINED — Toss/User**. Event identity, aliases and production mapping
remain **UNDETERMINED — Astra**. Durability, bank execution, chain finality and
production behavior are outside this verification. The hosted Move/ZK and
service checks also lie outside the local runs above.
