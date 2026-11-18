# Guided settlement initiation — local builder evidence

## Task and basis

Node: `plan-local-settlement-console-start`. Immutable task input: the supervisor's
node specification and design plan in the executing conversation. No issue or
current `docs/tasks/` document exists for this node; none was created or edited.
This is not ASTRA program mode. Dependencies are the merged local settlement
console, settlement-input adapter, settlement controls and statement distribution.
This report is source-informed builder composition evidence, not independent A2
review, merge readiness, capability promotion or runtime activation.

Branch: `agent/kix-plan-local-settlement-console-start`. Initial HEAD, task base
and cached `origin/main` all equal
`4451a934063cb4923eba852d53bed35a74fe4aef`; initial worktree clean, no local base
delta. The supervisor explicitly prohibited Git/GitHub/network publication and
network actions, so `git fetch origin main` was omitted; remote freshness remains
unverified. No commit, push, reset, GitHub action, issue, comment or PR occurred.
Final implementation is an uncommitted patch on that HEAD. Final committed task
head, merge SHA and exact-head CI identifiers do not exist in this session.

Read root README, DEVELOPMENT_PLAN, BASELINES, AUTHORITY_MODEL_1, governance and
control-plane pointer/pin, PROGRAM_DECISIONS_20260928, predecessor evidence and
relevant console/adapter/dispatcher/FSM tests. The candidate central pin remains
pending adoption and runtime disabled. The conversation's narrower scope controls
this task; no task input or policy document was rewritten.

## Preservation

Both locked blobs matched before editing and are checked again at completion:

| Path | Required Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Before editing, `/tmp/kix-console-start-before.json` recorded SHA-256 hashes of
all 1,362 initially tracked files. The final preservation check compares every
tracked file outside the eight allowed changed paths, including working bytes of
`reference/v0.3-rc1/**`. It also checks the locked blobs, unchanged branch/HEAD/
cached main, changed-path allowlist, AST syntax and `git diff --check`.
Final check passed: exactly eight changed paths; 1,357 other tracked files
byte-identical; both required kernel blobs still match. Historical Git tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b` and its working bytes are unchanged.
Dispatcher, sessions, adapters, arithmetic, FSMs, existing fixture schemas/data,
contracts, catalogue, SDK, workflows, production flags, `.aiops/**`, task documents
and protected historical/kernel files were never modified or transiently mutated.

## Existing coverage inventory (mapped before adding tests)

Paths below are relative to `reference/booking_resale_admission/` unless stated.

| Requirement | Existing classification and exact coverage | New gap |
|---|---|---|
| Source extraction and explicit caller arguments | Sufficient adapter coverage: `test_settlement_input_adapter.py::test_one_selected_read_and_one_target_call_with_opaque_arguments_and_result`, `test_malformed_records_never_delegate_and_explicit_repair_reads_again` | Guided JSON policy and source-ID composition absent |
| Source failures, no cross-machine effects, retained keys | Sufficient service coverage: `test_ticket_settlement_inputs.py::test_api_and_dispatch_journeys_match_receipts_errors_states_and_journals`, `test_missing_unconfirmed_malformed_and_faulting_sources_leave_graph_and_key_free`, `test_manual_source_alias_replay_changed_extraction_and_caller_body_conflicts` | Previously absent targets through actual console child not covered |
| Authorization/capture phase transitions | Sufficient FSM/desk coverage: `test_ticket_settlement_controls.py::test_illegal_phases_amount_mismatch_replay_and_historical_receipts`, `test_fsm_methods_forward_once_with_exact_objects_receipts_and_errors` | Confirmation and explicit sequence through prompts missing |
| Statement/distribution behavior | Sufficient: `test_ticket_statement_distribution.py::test_file_stdin_and_api_journeys_match_direct_fsm_after_every_step`, `test_direct_recorded_key_equivalence_conflicts_and_movement_characterization`; `reference/settlement_f01_f03/test_mock_settlement.py` | Partial console coverage starts with preconstructed target |
| Refund controls and policy uncertainty | Sufficient: `test_ticket_refund_controls.py::test_economic_rejections_retained_keys_and_conflicts_at_both_phases`, `test_partial_obligation_fully_accepted_and_summed_bindings_keep_burden_undefined` | Continue from caller-created target |
| Transport fencing, cleanup, prompt confirmation and shared navigation | Sufficient transport and partial console coverage: `test_ticket_operations_client.py`, existing `test_settlement_console.py`, `test_shared_ticket_console.py` | Four new selectors and two documented start transcripts missing |

No duplicate arithmetic/model/adapter tests were added. New tests compare full
unchanged dispatcher envelopes on a separately loaded service graph. This is
source-informed parity, not clean-room independence.

## New acceptance evidence

| New/extended test | Gap addressed |
|---|---|
| `test_settlement_console.py::test_booking_start_journey_one_child_source_owned_amount_and_no_ticket_effects` | Both targets absent in input graph; one actual child; exact 18-request sequence; INITIATED → AUTHORIZED → CAPTURED → COMMITTED; null claims then zero cash; source 10001/KRW; statement/distribution/refund outcomes; historical initiation replay; unchanged live booking/right/admission probes outside console request stream |
| `test_shared_ticket_console.py::test_resale_start_journey_creates_target_and_preserves_ticket_observations` | One actual child, explicit listing first, absent target; exact 21-request sequence and complete proposals/replies; source 8000/KRW; two recorded statements and distribution; historical initiation replay; explicit unchanged booking/listing/right observations |
| `test_settlement_console.py::test_missing_sources_and_invalid_transition_continue_only_when_selected` | Both missing source selectors retain exact source error; fresh explicit selection under same key succeeds; capture-before-authorize refusal leaves current phase unchanged; explicit continuation only |
| `test_settlement_console.py::test_policy_syntax_errors_discard_selection_without_any_submission` | Both selectors: malformed, absent, non-object, nested duplicate keys, NaN/infinities and exponent overflow discarded locally; zero submissions or proposals |
| `test_settlement_console.py::test_policy_objects_are_forwarded_unchanged_and_retained_keys_conflict` | Missing/extra fields, kind, invalid basis points and payee collision forwarded unchanged; exact service refusals retained; corrected body under same key conflicts; fresh key succeeds; duplicate after capture is historical and changed trade conflicts without state change |
| `test_settlement_console.py::test_every_mutation_requires_literal_single_use_submit` (extended) | Declining all 12 mutation selectors sends nothing; each new selector cannot inherit prior approval |
| `test_shared_ticket_console.py::test_resale_initiation_conflict_preserves_current_view` | Changed trade under resale initiation key after distribution returns exact conflict and leaves current settlement/listing unchanged |
| `test_settlement_console.py::test_booking_start_transcript_as_cli_subprocess`, `test_shared_ticket_console.py::test_resale_start_transcript_as_cli_subprocess` | Checked-in answer files run as actual CLI subprocesses with inherited socket denial, full existing fixture and explicit cleanup timeout |

Booking current cash/distributed cash is 9301, refund outstanding 3000 and PG
adjustment outstanding 1000, while the replayed initiation still has a null claim.
Resale distribution is 8000; listing remains LISTED, settlement/payment unbound,
right holder buyer-1 and version 1. No console action observes payment, binds a
ticket, issues/transfers a right, grants admission or sequences another phase.
All returned settlement production/execution flags remain false.

## Commands and actual results

Verification uses Python stdlib and provisioned tools only, without dependency
downloads. Commands run sequentially in the foreground. The runner
`/tmp/kix-console-start-verify.py PHASE` records each command, return code and
combined output in `/tmp/kix-console-start-PHASE.json`. Environment:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-settlement-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/local/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-console-start-target
export CARGO_NET_OFFLINE=true
```

The predecessor `/tmp/kix-settlement-no-sockets/sitecustomize.py`, inspected
before use, installs this audit guard in parent and inheriting children:

```python
import sys
def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by local console verification guard: ' + event)
sys.addaudithook(deny_socket)
```

Legacy probes that deliberately replace their child environment are outside the
inherited-child guard claim. Both new transcript CLI paths inherit the guard.
Inspected `.github/workflows/protocol.yml` and `ktx-kernel.yml`; the following
are the closest offline equivalents for touched Python/documentation paths and
kernel boundaries, not a claim that hosted CI or unrelated workflows ran.

<!-- RESULTS START -->
| Command actually run | Actual result |
|---|---|
| `git status --short; git rev-parse HEAD; git rev-parse origin/main; git branch --show-current (read-only)` | Initial clean tree; expected branch; both refs 4451a934063cb4923eba852d53bed35a74fe4aef |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before edits: both required blobs match |
| `python3 -m unittest test_settlement_console test_shared_ticket_console (first run)` | FAIL: 34 tests, two assertion failures; corrected expected UNKNOWN_SETTLEMENT, no service change |
| `python3 -m unittest test_settlement_console test_shared_ticket_console (corrected run)` | PASS: 34 tests, exit 0 |
| `python3 -m unittest test_settlement_console test_shared_ticket_console` | PASS: 37 tests, exit 0 |
| `python3 -m unittest test_settlement_input_adapter test_ticket_settlement_inputs test_ticket_settlement_inputs_cli test_ticket_settlement_controls test_ticket_statement_distribution test_ticket_refund_controls test_ticket_settlement_fact_inputs test_ticket_settlement_fact_inputs_cli test_ticket_operations_client` | PASS: 58 tests, exit 0 |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, exit 0 |
| `python3 scripts/check_docs_index.py` | PASS: exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_settlement_evidence_map.py` | PASS: exit 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | PASS: exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_contract_error_codes.py` | PASS: exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | PASS: exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_ci_test_discovery.py` | PASS: exit 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_openapi_contract.py` | PASS: exit 0 |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS: exit 0 |
| `python3 scripts/check_integration_gate_openapi.py` | PASS: exit 0 |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS: exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | PASS: exit 0 |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, exit 0 |
| `python3 /tmp/kix-console-start-offline.py` | PASS: 826 tests, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101 before compilation; offline crates.io index lacks bcs, required by workspace kix-bcs1 |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101 before compilation; offline crates.io index lacks bcs, required by workspace kix-bcs1 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0 |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_settlement_console.py` | PASS: 21 tests, exit 0 |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_shared_ticket_console.py` | PASS: 16 tests, exit 0 |
| `python3 -B reference/booking_resale_admission/settlement_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_start_booking.txt > /tmp/kix-console-start-booking.txt` | PASS: exit 0, 18 complete desk envelopes under socket denial |
| `python3 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_start_resale.txt > /tmp/kix-console-start-resale.txt` | PASS: exit 0, 21 complete desk envelopes under socket denial |
| `python3 - (inline saved-transcript envelope assertions)` | PASS: booking 18 / resale 21 envelopes; historical replay and current 9301 / 8000 distributions verified |
| `rg --files --hidden --no-ignore reference/v0.3-rc1 (filtered for __pycache__ or .pyc)` | No matches; filter exit 1, no generated bytecode found |
| `python3 -B /tmp/kix-console-start-preserve.py` | PASS: exactly eight changed paths; both locked blobs match before/after; protected historical tree and working bytes unchanged; PASS: 1357 other tracked files byte-identical; unchanged branch, HEAD and cached main; Python AST syntax and git diff --check pass |
| `python3 scripts/check_docs_index.py (final report)` | docs index ok: scanned=356 indexed=321 allowlisted=35 |
<!-- RESULTS END -->

## Complete changed paths

- `reference/booking_resale_admission/settlement_console.py`
- `reference/booking_resale_admission/test_settlement_console.py`
- `reference/booking_resale_admission/test_shared_ticket_console.py`
- `reference/booking_resale_admission/fixtures/settlement_console_start_booking.txt`
- `reference/booking_resale_admission/fixtures/settlement_console_start_resale.txt`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-05-plan-local-settlement-console-start/README.md`

## Discrepancies, deviations, non-claims and gates

The first focused run had 34 tests and two failures because new tests expected
`SETTLEMENT_NOT_FOUND`; existing service code returns `UNKNOWN_SETTLEMENT`.
Corrected only the assertions; the next 34-test run passed. After the additional
CLI and resale conflict coverage, the final focused selection has 37 tests.
No service/contract change was needed. No explicit contract violation was found.
The pre-existing class-B zero-cash distribution uncertainty remains unchanged.

The conversation is the current task input. Fetch and all Git/GitHub publication
are deferred to the supervisor by explicit instruction. No new issue/task file
or decision record was needed. No STOP condition or consequential scope expansion
was encountered. Test-only source probes bracket the booking console; resale
source observations are explicit shared-console selections. The broader BRA
selection retains exactly the predecessor's socket-test exclusion:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
It asserts that exactly one such test exists and discovered IDs are unique.
This is an offline selection, not a full socket-bearing BRA pass.
`/tmp/kix-console-start-offline.py` uses the same flattened discovery/filter code
as the [predecessor evidence](../2026-11-05-plan-plan-local-settlement-console/README.md#executed-local-verification),
copied unchanged into this session's driver. It ran 826 selected tests successfully.

Rust test and Clippy are unavailable before compilation because the provisioned
offline Cargo index lacks `bcs` for workspace member `kix-bcs1`. Neither is a
pass. No Rust source was touched, and no dependency bootstrap, download or CI
workaround was attempted. Formatting passed; Rust execution remains a supervisor/
CI gate with provisioned dependencies. Standalone discovery also passed both
touched modules (21 settlement-console tests and 16 shared-console tests).

Policy remains **UNDETERMINED — Astra/User**; legal/accounting treatment remains
**UNDETERMINED — User/designated advisers**. Synthetic policy inputs do not
establish resale economics or product defaults. No P04 durable closure,
persistence, payment truth, real refund completion, bank exactly-once, distributed
fencing, chain finality, legal compliance or production readiness was tested or
claimed. Real funds, PG/bank/KYC, public endpoints, Sui testnet/mainnet, own
storage/replication/consensus, new coin/TIX and production runtime remain locked.

Non-author A2 exact-final-head review: pending supervisor publication.
Exact-head KTX CI run ID/status/conclusion: not run/unavailable.
Exact-head KIX protocol CI run ID/status/conclusion: not run/unavailable.
Post-merge main CI and final-merge blob verification: not applicable; no merge.
No final committed head exists for this patch. The supervisor must record its
actual final head and obtain review and both required exact-head workflow
successes externally. Local builder completion does not authorize merge.
