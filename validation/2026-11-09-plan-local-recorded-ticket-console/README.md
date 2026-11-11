# Recorded ticket console builder evidence

Node: `plan-local-recorded-ticket-console`. Immutable task input: user-supplied
node specification and design plan in this session (no task issue or file under
`docs/tasks/`). Source: planner run 1794195979. Non-ASTRA builder; single writer.

Local branch `agent/kix-plan-local-recorded-ticket-console`; initial HEAD and
cached `origin/main` both `85843ae5863f7ec982a7769ce5206932e7a7fbe4`.
The supervisor prohibits network/GitHub actions and commits, overriding startup
fetch: no fetch performed; current remote main is unverified. No base change.
Final implementation remains uncommitted for supervisor delivery; no final
implementation commit SHA or exact-head CI exists in this builder session.

## Pre-change coverage mapping

Inspected before adding tests; all test paths below are under
`reference/booking_resale_admission/`.

| Requirement | Existing evidence | Classification and gap |
|---|---|---|
| Exact adapter forwarding and receipt/error identity | `test_resale_offer_adapter.py::test_exact_forwarding_and_receipt_and_error_identity`; `test_presentation_adapter.py::test_exact_forwarding_receipt_and_exception_identity_for_both_methods` | Sufficient underlying behavior; new menu forwarding absent |
| Missing/fault recordings, replay, stale presentation | Adapter `test_absent_malformed_mismatched_and_fault_records_touch_no_fsm_or_keys`, `test_fetch_failure_after_acceptance_never_returns_cached_receipt`; presentation `test_missing_malformed_faults_precede_all_machine_access`, `test_stale_version_holder_and_conflicting_keys`, `test_transfer_refuses_old_and_transferred_presentations_without_reissue` | Sufficient adapter semantics; partial console composition |
| Shared graph and complete replies | `test_ticket_operations_session.py::test_transcripts_session_and_cli_match_direct_graph_after_every_request`, `test_replay_fetch_failure_and_key_conflicts_leave_shared_graph_unchanged` | Sufficient session semantics; new console selectors not covered |
| Real-child menu journeys, explicit replay/current views | Resale `test_live_transfer_transcript`; admission `test_live_admission_transcript`, `test_authorization_alone_never_consumes`, `test_declined_consumption_submits_nothing`; shared `test_live_shared_journey_one_child`, `test_navigation_sends_nothing` | Partial; manual-input journeys only |
| Caller proposal, exact confirmation, incomplete input | Console fulfillment/payment and admission literal/distinct approval tests | Partial; new actions absent |
| Terminal transport fencing, no retry/replacement | `test_ticket_operations_client.py`; shared `FAULT_ACTIONS` malformed/truncated/EOF, write, interruption and display-failure matrix | Sufficient client mechanics; partial new-action composition |
| Runnable recorded console transcripts and usage | Existing manual-input answer files | Not covered for these selectors |

No duplicated FSM matrix or client/session production change is indicated.

## Implementation and added evidence

The production patch adds one resale field-map entry and two admission entries
plus their existing literal confirmations. The existing mutation path adds the
key once, previews the complete caller request and calls the client once after
confirmation. The shared console already delegates these menus to the same
client. No client, session, adapter, dispatcher, FSM, fixture schema, receipt,
error, runtime setting, contract or CI change was needed.

New tests are source-informed composition evidence, not independent verification.
They use existing populated sources, real desk subprocesses and full-envelope
comparison with `dispatch_request(load_fixture(...), request)` on an equivalent
fresh graph; expected source/domain exceptions are normalized with `_error`.
Only helpers/constants are imported between suites, not TestCase classes.

| Gap | Added coverage (under `reference/booking_resale_admission/`) |
|---|---|
| Exact selectors, complete arguments/proposals and literal approvals | `test_resale_console.py::test_recorded_listing_inputs_and_confirmation_boundaries`; `test_admission_console.py::test_recorded_admission_inputs_and_confirmation_boundaries`, sharing `recorded_input_boundaries` |
| No submission on decline, blank/padded fields, malformed decimal expiry, EOF/interruption/input failure | Same boundary tests, every field and confirmation; shared `test_exception_declines_and_confirmation_interrupt_fence_queued_navigation` extended to recorded actions |
| Real-child recorded listing, cancellation, historical replay, changed binding conflict and current views | `test_recorded_listing_real_child_replay_and_changed_binding` |
| Independent authorization/consumption, declined consume, historical receipt replay, conflicts, unchanged current view | `test_recorded_admission_separate_actions_replay_and_conflicts`; `test_recorded_authorization_alone_and_consume_never_auto_authorizes` |
| Missing and both immediate synthetic source faults, exact error details and unchanged subsequent explicit observation | `test_recorded_offer_missing_and_source_faults_preserve_observations`; `test_recorded_presentation_missing_and_faults_preserve_observations` use temporary fixture copies |
| Navigation on one child with populated fixture and complete direct-dispatch parity | `test_shared_ticket_console.py::test_recorded_shared_journey_and_executable_transcript` |
| Stale presentations after separately selected resale payment/binding/transfer | Shared `test_recorded_stale_presentations_after_explicit_transfer`; both recorded admission selectors preserve `STALE_VERSION` and current observations |
| Terminal fencing, queued input untouched, no retry/child replacement | All three added to shared `FAULT_ACTIONS` (terminal envelopes, malformed/truncated/EOF replies, broken/short writes, interruption and display/diagnostic failures); already-fenced-client matrix extended; `test_received_recorded_action_display_failure_retains_receipt_and_fences` retains actual accepted receipts |
| Runnable answer files | Standalone `test_recorded_listing_documented_subprocess`, `test_recorded_admission_documented_subprocess` and shared executable-transcript test; also executed directly below |

Existing manual-input console journeys pass in the focused/regression commands.
The old unknown-action test used `consume`, which is now supported; it now uses
`unsupported` to retain the original unknown-action assertion.

## Changed paths

- `reference/booking_resale_admission/resale_console.py`
- `reference/booking_resale_admission/admission_console.py`
- `reference/booking_resale_admission/test_resale_console.py`
- `reference/booking_resale_admission/test_admission_console.py`
- `reference/booking_resale_admission/test_shared_ticket_console.py`
- `reference/booking_resale_admission/fixtures/resale_console_recorded.txt`
- `reference/booking_resale_admission/fixtures/admission_console_recorded.txt`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_recorded.txt`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-09-plan-local-recorded-ticket-console/README.md`
- `validation/2026-11-09-plan-local-recorded-ticket-console/run_offline_discovery.py`

## Commands actually run and results

Repository root unless stated otherwise. Python tests/checks used
`PYTHONDONTWRITEBYTECODE=1`; named-module tests used
`PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"`.
Repository workflows inspected: `.github/workflows/protocol.yml` (reference
suite discovery, offline documents/contracts, architecture and Rust workspace)
and `.github/workflows/ktx-kernel.yml` (architecture, kernel tests/Clippy/format).
No dependencies were downloaded, no jobs were backgrounded, and no unavailable
check is counted as passing.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; expected branch; both SHAs above. Remote freshness unverified, no fetch permitted |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both required blobs match (values below) |
| `python3 -m unittest test_resale_console test_admission_console test_shared_ticket_console` (first run) | Exit 1; 83 tests, seven failing subcases: fixture fault enum names instead of existing wire tokens (six), incorrect test phase `ISSUED` instead of existing `ELIGIBLE` (one). Corrected test inputs/expectations only |
| `python3 -m unittest test_resale_console test_admission_console test_shared_ticket_console` (after corrections and accepted-receipt display test) | Exit 0; 84 tests passed |
| `python3 -m unittest test_resale_offer_adapter test_presentation_adapter test_ticket_operations_client test_ticket_operations_session test_ticket_operations_cli test_resale_session test_admission_session test_resale_cli test_admission_cli test_booking_console test_settlement_console` | Exit 0; 195 tests passed |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0; nine tests passed |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; passed |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; seven regression tests passed |
| `python3 scripts/check_docs_index.py` | Exit 0; passed; repeated after evidence update: scanned=378 indexed=343 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; passed |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; passed |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; passed |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; passed |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; passed |
| `python3 scripts/check_openapi_contract.py` | Exit 0; passed |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; passed |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; passed |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; passed |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; passed |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; passed |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; passed |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; passed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; format check passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101; UNAVAILABLE: missing cached crates.io package `bcs` (required by workspace `kix-bcs1`); no Rust tests/lints executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101; UNAVAILABLE: missing cached crates.io package `bcs` (required by workspace `kix-bcs1`); no Rust tests/lints executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101; UNAVAILABLE: missing cached crates.io package `bcs` (required by workspace `kix-bcs1`); no Rust tests/lints executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101; UNAVAILABLE: missing cached crates.io package `bcs` (required by workspace `kix-bcs1`); no Rust tests/lints executed |
| `python3 -B reference/booking_resale_admission/resale_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/resale_console_recorded.txt` | Exit 0; 6 complete desk envelopes, empty stderr |
| `python3 -B reference/booking_resale_admission/admission_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/admission_console_recorded.txt` | Exit 0; 8 complete desk envelopes, empty stderr |
| `python3 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_recorded.txt` | Exit 0; 16 complete desk envelopes, empty stderr |
| `python3 validation/2026-11-09-plan-local-recorded-ticket-console/run_offline_discovery.py` | Exit 0; 904 tests passed in 119.447s; PARTIAL discovery, one loopback test explicitly excluded |
| `git diff --check` | Exit 0; no whitespace errors (also repeated after documentation/evidence updates) |
| Python SHA-256 comparison against pre-edit `/tmp/recorded-ticket-preservation.json`, with exact historical file-set comparison | PASS: all 108 historical files, both locked files and original populated fixture byte-identical |
| `git diff --name-only -- .aiops/ docs/tasks/ reference/v0.3-rc1/ runtime/ .github/` | Empty; no protected/scope changes |

The offline discovery helper runs the workflow's booking/resale/admission
`unittest` discovery suite, explicitly excluding exactly
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
That test creates a loopback HTTP server and is not run under the supervisor's
no-network rule. Discovery is **partial**, never a full workflow PASS. The
helper fails if the named exclusion does not exist exactly once. Repository CI
is unchanged and will still discover that test.

## Preservation, findings, limits and delivery gates

Required blobs verified before and after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

`reference/v0.3-rc1/**` (108 files) and the existing populated
`fixtures/ticket_operations_session.json` remain byte-identical. No edits to
`.aiops/`, `docs/tasks/`, runtime, workflows, settings or blocked nodes.

No explicit contract violation found; no new undefined contract semantics
introduced or resolved. Existing historical receipt/current observation and
stale credential behavior is preserved. Product policy remains **UNDETERMINED —
Astra/User**; legal effects remain **UNDETERMINED — User/legal**. Example keys,
roles, amounts and expiry values are synthetic fixture/caller choices, not policy
defaults. No new command, query, discovery, automatic source read, retry, child
replacement, production runtime or provider/chain call is added.

Deviations: startup fetch omitted per explicit supervisor no-network instruction;
local cached main used only as an unverified remote reference. Added a runnable
validation-only discovery helper to make the exact loopback exclusion explicit.
Rust test/Clippy equivalents are unavailable due to missing offline `bcs`; no
network fallback/retry. No implementation-design deviation.

This evidence covers source-informed, in-memory, synthetic local composition.
It does not establish production readiness, legal compliance, independent
identity/currentness, bank exactly-once, persistence/distributed fencing,
production durability, real funds/provider authentication or chain finality.
No public endpoints, Sui testnet/mainnet, hardware, paid services, credentials,
coin/TIX, replication/consensus/storage engine or runtime activation was used.

The work remains uncommitted as requested. Builder state READY means ready for
supervisor handoff, not merge-ready. Implementation/final task commit SHA,
non-author A2 exact-HEAD review, exact-head KTX and KIX CI run IDs/status/conclusions
remain **not available / pending supervisor delivery**. No merge occurred;
merge SHA, merge-blob and post-merge main CI checks are not applicable. Required
follow-up: provision offline Rust dependencies in an authorized environment,
execute the omitted checks, obtain non-author exact-HEAD review and both required
exact-head workflow successes. The supervisor owns git/GitHub publication; only
the User authorizes merge.
