# plan-local-payment-lookup-console — builder evidence

Task input: supervisor-supplied node specification and design in the session;
no issue or task document exists. Non-ASTRA session; no task input edited.
Branch: `agent/kix-plan-local-payment-lookup-console`.
Cached `origin/main`, base and initial HEAD: `f502da0f81491a774c6df8cea055edea9f128fa4`.
Fetch NOT_RUN: the supervisor explicitly prohibits all network/GitHub actions.
Remote freshness is unverified; no cached base delta. No commit/publication is authorized.

## Existing coverage mapped before console tests

Paths below are in `reference/provider_facts/`. These are source-informed checks,
not independent provider verification.

| Requirement | Existing coverage classification and evidence | Console gap to address |
|---|---|---|
| Paid/cancellation/unresolved through real router | Partial: `test_payment_lookup_cli.py::test_full_cancellation_keeps_payment_and_cancel`, `test_unresolved_original_scope_only_and_recorded_text_opaque`; router `test_complete_identity_and_outputs_equal_single_scope_service` | Scripted terminal journeys and runnable stdin transcripts |
| Preview/decline/invalid input: zero lookups | Not covered at console boundary; CLI `test_invalid_entire_configuration_precedes_all_lookup_and_binding` sufficiently covers loader validation matrix | Terminal input, argument boundary, preview flush and literal confirmation |
| One router call per submission; zero-fake rejection | Partial: CLI `test_lookup_once_preserves_nonempty_history_and_calls_router_once`; router `test_missing_binding_and_route_make_zero_calls`, `test_unresolved_scope_never_falls_back` | Real forwarding spies at console boundary, trailing submissions ignored |
| Exact integers/raw timestamps/history/hashes | Sufficient normalization coverage: `test_normalization_golden_vectors.py::test_literal_facts_bytes_and_digests`; `test_payment_lookup.py::test_full_cancellation_preserves_capture_and_has_independent_expected_history` | Lossless terminal JSON rendering, literal goldens and multiple cancels |
| Unexpected/terminal failures: no retry | Partial: CLI `test_unexpected_programming_error_propagates`, router `test_unrelated_programming_error_propagates` | Read/write/flush/short write/interruption before and after submission |
| Fixed bindings/routes/recordings/evidence | Sufficient lower-layer coverage: CLI `test_lookup_once_preserves_nonempty_history_and_calls_router_once` | Console journey with populated captures/review and unchanged fixture bytes |
| Discovery/docs/OpenAPI/local gates | Partial: `.github/workflows/protocol.yml` discovers provider_facts and runs documentation/OpenAPI/discovery checks | Run applicable checks and transcripts after implementation |

## Results and delivery gates

Implementation is complete in the uncommitted worktree. READY is a builder handoff
state only; it is not merge-ready. No new decision or external resource is needed
for the standard-library console. Rust verification is unavailable for the
pre-existing offline-cache reason recorded below.
Non-author A2 exact-head review and hosted exact-head KTX/KIX success remain required.
No hosted CI, merge or post-merge verification is claimed by this builder session.


## Implementation and new evidence

`payment_lookup_console.py` uses the existing complete fixture validator and
`lookup_once` unchanged. It performs a binding-only preview, flushes it before
literal confirmation and makes at most one router invocation. Its `result=` JSON
retains all returned fields, exact integers, raw strings/timestamps, cancellation
items and original hashes; ASCII escaping prevents terminal control injection.
No completion interpretation, recording edits, economic application or retry is
added. Errors terminate even if the synthetic lookup already happened.

New `test_payment_lookup_console.py::PaymentLookupConsoleTests` fills only the
console boundary gaps mapped above:

| Tests | Evidence gap addressed |
|---|---|
| `test_scripted_transcripts_use_real_router` | Six actual console subprocesses using the unchanged shipped fixture: paid, partial/full cancellation, timeout/error and decline |
| `test_preview_is_flushed_before_submit_and_declines_never_lookup`, `test_invalid_identifiers_and_eof_end_without_lookup` | Preview is present and flushed before submission; literal confirmation; zero CLI/router/fake calls for declines, invalid identities and EOF |
| `test_submit_forwards_once_and_ignores_trailing_submissions`, `test_missing_binding_or_route_submits_once_with_zero_fake_calls` | Wrapping spies execute real CLI/router/fake, both merchant scopes, CRLF and trailing submissions; missing binding/route submits once with zero fake calls |
| `test_display_preserves_literal_golden_bytes_and_hashes`, `test_all_cancellations_and_terminal_controls_survive_rendering` | Reused literal goldens (including u128 maximum and offset-less timestamp), complete ordered multi-cancel history, raw receipt and unchanged hashes, escaped control text |
| `test_state_unchanged_with_populated_captures_and_review` | Original binding, nonempty capture/review evidence, routes and recordings retained; bind/capture calls forbidden; shipped fixture bytes checked after every test |
| `test_terminal_read_failures_stop_before_submission`, `test_terminal_write_and_flush_failures_never_retry`, `test_lookup_and_render_errors_are_terminal` | Read/interruption failures at every prompt; failed/short writes and flush failures at every output boundary, stderr failure, interruption/errors before and after the fake runs, serialization failure; no second call/fallback |
| `test_main_validates_configuration_before_input_or_lookup`, `test_main_loads_once_and_runs_one_journey` | Malformed/duplicate/abbreviated/credential arguments, invalid trailing fixture declaration and missing file stop before prompts; valid fixture loads once and forwards one journey |

## Actual commands and results

All Python verification used `PYTHONDONTWRITEBYTECODE=1`. Commands ran in the
foreground; no network, automatic retry, GitHub actions or publication occurred.
The first narrow run exposed test-setup errors, then explicit corrections and a
later post-call failure assertion were tested. No production module fix or
contract change was required.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p test_payment_lookup_console.py -v` | Initial run: 13 tests, 6 errors from test setup (invalid OperationRef constructed before entering console; provenance referenced from wrong module). Fixed test setup: 13 passed. After adding post-fake-call failure cases: 13 passed again. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | 86 passed before the extra post-call failure cases; final run: 86 passed. |
| `python3 reference/provider_facts/example_payment_lookup.py` | Exit 0; 7 JSON rows; empty stderr. |
| `python3 reference/provider_facts/example_payment_lookup_router.py` | Exit 0; 7 JSON rows; empty stderr. |
| `python3 reference/provider_facts/payment_lookup_console.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json < reference/provider_facts/fixtures/payment_lookup_console_paid.txt` | Exit 0; empty stderr; transcript output verified by console tests. |
| `python3 reference/provider_facts/payment_lookup_console.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json < reference/provider_facts/fixtures/payment_lookup_console_partial.txt` | Exit 0; empty stderr; transcript output verified by console tests. |
| `python3 reference/provider_facts/payment_lookup_console.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json < reference/provider_facts/fixtures/payment_lookup_console_full.txt` | Exit 0; empty stderr; transcript output verified by console tests. |
| `python3 reference/provider_facts/payment_lookup_console.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json < reference/provider_facts/fixtures/payment_lookup_console_timeout.txt` | Exit 0; empty stderr; transcript output verified by console tests. |
| `python3 reference/provider_facts/payment_lookup_console.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json < reference/provider_facts/fixtures/payment_lookup_console_error.txt` | Exit 0; empty stderr; transcript output verified by console tests. |
| `python3 reference/provider_facts/payment_lookup_console.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json < reference/provider_facts/fixtures/payment_lookup_console_decline.txt` | Exit 0; empty stderr; transcript output verified by console tests. |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=367 indexed=332 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=575 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=71 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK. |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_class_b_index.py` | Exit 0; class B index ok: rows=218 sources=73 symbols=47; textual index only. |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test passed. |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0; 9 tests passed. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101; BLOCKED before execution: locked dependency `bcs 0.2.1` absent from offline registry; no tests/lints/dependency tree produced. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101; BLOCKED before execution: locked dependency `bcs 0.2.1` absent from offline registry; no tests/lints/dependency tree produced. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101; BLOCKED before execution: locked dependency `bcs 0.2.1` absent from offline registry; no tests/lints/dependency tree produced. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; formatting passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 101; BLOCKED before execution: locked dependency `bcs 0.2.1` absent from offline registry; no tests/lints/dependency tree produced. |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0 (inspection only): 7/18 locked archives present; 11 missing, including bcs 0.2.1. This exit is not a successful Cargo build. |
| `cargo --version`; `rustc --version` | cargo 1.98.1, rustc 1.98.1 (matches workflow toolchain version). |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before/after: both required blobs match (values below). |
| Python SHA-256 manifest comparison of protected trees and fixture | Before/after: identical bytes and path sets, 122 files (details below). |

## Changed paths and protected bytes

Complete builder output paths:

- `reference/provider_facts/payment_lookup_console.py`
- `reference/provider_facts/test_payment_lookup_console.py`
- `reference/provider_facts/fixtures/payment_lookup_console_paid.txt`
- `reference/provider_facts/fixtures/payment_lookup_console_partial.txt`
- `reference/provider_facts/fixtures/payment_lookup_console_full.txt`
- `reference/provider_facts/fixtures/payment_lookup_console_timeout.txt`
- `reference/provider_facts/fixtures/payment_lookup_console_error.txt`
- `reference/provider_facts/fixtures/payment_lookup_console_decline.txt`
- `reference/provider_facts/README.md`
- `docs/README.md`
- `validation/2026-11-07-plan-local-payment-lookup-console/README.md`

Before and after work, locked Git blobs:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The local SHA-256 manifest covers all files in `reference/v0.3-rc1/**`,
`.aiops/**`, `docs/tasks/**`, the two locked files and shipped
`payment_lookup.synthetic.json`. All 122 bytes-hashes and protected tree path
sets matched before/after. SHA-256 of the sorted JSON manifest:
`f935fdcbd14a6bd1e1214bdb7af9b73ea6fcc2356326334b0bd2c6b481ef4658`.
No contracts, OpenAPI, normalizer, service/router/CLI/fake, runtime flags, policy
values or workflows changed. No transient edits to protected files were made.

## Discrepancies, deviations, non-claims and remaining gates

- No class C contract violation was found. No new underlying contract semantics
  were defined. Prompt order, literal confirmation, JSON line labels and exit
  codes are local tooling conventions, not protocol/policy decisions.
- No implementation design deviation was needed. Coverage mapping uses actual
  existing test names; new terminal tests are source-informed, not clean-room or
  non-author review.
- Fetch was not run under the explicit supervisor network prohibition. Initial
  and final local HEAD remain `f502da0f81491a774c6df8cea055edea9f128fa4`;
  cached `origin/main` equals that SHA. Remote freshness remains unverified.
- No implementation commit/final delivery commit SHA exists yet: work is
  uncommitted for the supervisor. No commits, pushes, issues, comments, PRs,
  branches/tags, readiness changes or merges were created by this session.
- Rust tests, Clippy and dependency evidence were attempted once each in offline
  mode and blocked by missing pre-existing locked registry dependencies. Existing
  local caches were inspected; the required archives are unavailable. Dependencies
  were not replaced or fetched. Formatting and architecture checks passed.
  The supervisor/qualified host must run these locked checks with a populated
  offline cache; this report does not call them green.
- Hosted exact-head **KTX kernel verification**: NOT_RUN, run ID/status/conclusion
  unavailable. Hosted exact-head **KIX protocol verification**: NOT_RUN, run
  ID/status/conclusion unavailable. No older CI result is transferred.
- A2 non-author exact-head review, both exact-head completed/success workflow
  gates and human-only readiness/merge authorization remain required. No
  independent audit, acceptance, grade change or merge readiness is claimed.
  Merge SHA, final-merge blob checks and post-merge main CI: not applicable,
  no merge performed.
- Full hosted KIX verification (Move/Sui/localnet/ZK, historical runtime and
  unrelated suites) was not executed locally. This task runs no public endpoint,
  provider/bank/KYC, production runtime, real money, chain or storage engine.
- Provider authentication and merchant scope remain **UNDETERMINED — Toss/User**.
  There is no payment/refund completion, issuance eligibility, UNKNOWN release,
  finality, durability, distributed fencing, legal compliance or production
  claim. Booking/resale/settlement and the blocked reservation handoff remain
  outside this console. No policy value or protocol command was introduced.
