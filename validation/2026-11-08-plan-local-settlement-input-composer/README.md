# Local settlement input composer — builder evidence

## Task and basis

Node `plan-local-settlement-input-composer`; immutable input is the supervisor's
node specification and design plan in the executing conversation. No issue or
current task document under `docs/tasks/` exists for this node; none was created
or edited. This is not ASTRA program mode. Dependencies: local settlement console
start, ticket statement distribution and shared ticket console. Audit floor A2;
normal non-author exact-head review and required KTX/KIX workflows remain gates.

Branch `agent/kix-plan-local-settlement-input-composer`; initial HEAD, task base and
cached `origin/main` all equal `b0fca792ba072ab880b2e1d7b23ce24242144328`.
Initial worktree was clean; no local base delta. The supervisor forbids network
and Git/GitHub publication, so `git fetch origin main` was omitted and remote
freshness remains unverified. Final implementation is an uncommitted patch on
that HEAD. No committed implementation/final task head or merge SHA exists for
this patch. No commit, push, reset, branch operation, issue, PR or comment occurred.

Read the repository README, DEVELOPMENT_PLAN, BASELINES, AUTHORITY_MODEL_1,
AGENTS, control-plane pointer/pin, PROGRAM_DECISIONS_20260928 section 5,
predecessor validation, console/adapter/service and relevant tests, and both
workflow definitions. The central policy pin remains a pending candidate with
runtime disabled. No policy or task document was changed.

## Change and boundaries

At the existing `policy` prompt, exact `guided` composes explicitly entered
`kind`, integer `fee_bps`, `residual_payee`, `fee_payee`. At `order`, exact `guided`
asks for an explicit nonnegative `payee_count` and that many numbered payees.
The count is terminal-only. Zero composes an empty list; duplicates and sequence
are preserved. There is no two-payee ceiling, default, recommended value,
policy selection, arithmetic, allocation, membership lookup or frozen-order
precheck. Raw JSON remains available, including strict policy-object decoding.
All completed mutations use the existing complete proposal, literal `SUBMIT`,
and one `TicketOperationsClient.request` call. No automatic reads, retries,
clock changes, source mutation or phase transitions were introduced. The adapter's
existing selected source read is unchanged.

Product policy remains **UNDETERMINED — Astra/User**; legal/accounting treatment
remains **UNDETERMINED — User/designated advisers**. P04/F01–F03 advances only
synthetic interaction. No capability grade or operational flag changes.

## Changed paths

- `reference/booking_resale_admission/settlement_console.py`
- `reference/booking_resale_admission/test_settlement_console.py`
- `reference/booking_resale_admission/test_shared_ticket_console.py`
- `reference/booking_resale_admission/fixtures/settlement_console_guided_booking.txt`
- `reference/booking_resale_admission/fixtures/settlement_console_guided_resale.txt`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-08-plan-local-settlement-input-composer/README.md`
- `validation/2026-11-08-plan-local-settlement-input-composer/guided_booking.stdout.txt`
- `validation/2026-11-08-plan-local-settlement-input-composer/guided_booking.stderr.txt`
- `validation/2026-11-08-plan-local-settlement-input-composer/guided_resale.stdout.txt`
- `validation/2026-11-08-plan-local-settlement-input-composer/guided_resale.stderr.txt`

## Coverage mapped before additions

Paths below are relative to `reference/booking_resale_admission/` unless stated.
Existing tests are reused rather than reproducing service arithmetic/model tests.

| Requirement | Existing coverage classification | Focused addition |
|---|---|---|
| Existing journeys and full proposals/replies | Sufficient for raw: `test_settlement_console.py::test_live_journey`, `test_booking_start_journey_one_child_source_owned_amount_and_no_ticket_effects`; `test_shared_ticket_console.py::test_resale_start_journey_creates_target_and_preserves_ticket_observations` | Guided booking and resale parity on fresh identical fixtures, exactly the same complete requests and replies, one child, unchanged ticket observations |
| Source-owned amounts, explicit caller arguments, no automatic effects | Sufficient: `test_ticket_settlement_inputs.py::test_required_signatures_constructor_no_reads_and_exact_forwarding`, `test_api_and_dispatch_journeys_match_receipts_errors_states_and_journals`, `test_manual_source_alias_replay_changed_extraction_and_caller_body_conflicts` | Reuse adapter/desk tests; console parity proves no additional request selectors or arguments |
| Explicit recorded statements and distribution | Sufficient service, partial composition: `test_ticket_statement_distribution.py::test_file_stdin_and_api_journeys_match_direct_fsm_after_every_step`, `test_retained_order_refusals_type_key_freedom_and_refund_block` | Guided transcripts retain explicit commit, observe, distribute and current views |
| Guided/raw equivalence | Not covered before this change | `test_guided_booking_journey_matches_raw_requests_results_and_ticket_observations`, `test_guided_resale_matches_raw_on_one_child_and_preserves_ticket_observations`; fee/order parity tests compare complete requests and reply streams |
| Zero/boundary fees, kind/payee refusals | Sufficient service: existing `test_policy_objects_are_forwarded_unchanged_and_retained_keys_conflict`; `reference/settlement_f01_f03/test_primary_fee_split.py::test_boundary_goldens`, `test_invalid_bps_rejected_with_contract_code` | `test_guided_policy_boundaries_and_service_refusals_match_raw`: 0, 1, 9999, 10000, -1, 10001, colliding payees, unsupported kind; unchanged integer and exact service errors; explicit sole nonzero payee at endpoints |
| Empty, duplicate, extra, changed and replayed order | Sufficient service: `test_ticket_statement_distribution.py::test_retained_order_refusals_type_key_freedom_and_refund_block`; partial console: `test_economic_validation_and_duplicate_order_are_left_to_service` | `test_guided_order_preserves_empty_duplicates_extra_payees_and_frozen_order`: 0/2/3 entries, exact forwarding, mismatch/duplicate/frozen/conflict errors, retained refusal key, historical replay and unchanged state on refusal |
| Malformed input and decline | Partial: `test_policy_syntax_errors_discard_selection_without_any_submission`, `test_invalid_syntax_never_submits_or_invents_defaults`, `test_every_mutation_requires_literal_single_use_submit` | `test_guided_malformed_fields_discard_without_submission_or_defaults`, `test_guided_declines_do_not_reuse_approval`: every guided field/count/key, noninteger/oversized integer/whitespace, zero unconfirmed requests |
| EOF, transport uncertainty and cleanup | Sufficient client and partial prompt coverage: `test_ticket_operations_client.py`, `test_eof_interruption_and_input_failure_fence_and_close`, `test_real_transport_uncertainty_does_not_resubmit_or_consume_queued_actions` | Guided EOF at every new field/key/confirmation, both initiations and order; malformed/truncated/EOF real child replies after confirmed mutations; one attempted request, queued actions unread, close exactly once |
| Documented CLI answers | Partial: existing raw subprocess transcripts | `test_guided_booking_transcript_as_cli_subprocess`, `test_guided_resale_transcript_as_cli_subprocess` and captured stdout/stderr below |

These tests are builder-authored and source-informed; direct dispatch parity is
not clean-room independence or a non-author A2 review. No new service semantics
or duplicated arithmetic implementation was added.

## Synthetic transcripts

Both use the unchanged `ticket_operations_settlement_inputs_session.json`.
[Booking stdout](guided_booking.stdout.txt) contains 18 full desk envelopes;
[booking stderr](guided_booking.stderr.txt) is empty. The guided booking path
initiates `claim-2` from `reserve-2`, explicitly authorizes/captures, commits
`statement-1`, observes `statement-2`, distributes, binds a refund and observes
synthetic cancellation acceptance, then replays initiation with its original key.
Each mutation is followed by an explicit current view. Source amount/currency is
10001/KRW; distributed cash is 9301, refund outstanding 3000 and PG adjustment
outstanding 1000. The replay remains a historical INITIATED snapshot.

[Resale stdout](guided_resale.stdout.txt) contains 21 full desk envelopes;
[resale stderr](guided_resale.stderr.txt) is empty. The shared console explicitly
creates `list-1`, initiates `resale-claim`, authorizes/captures, commits/observes
the two recorded resale statements, and distributes source-owned 8000/KRW on
one desk child. Explicit booking/listing/right views before and after settlement
match. The listing remains LISTED, unpaid and unbound; holder buyer-1/version 1.

## Commands and actual results

The two narrow runs used `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"`, without the later socket
guard. Baseline narrow command ran before editing: 83 tests passed. The same narrow
command after implementation: 93 tests passed. Subsequent checks use stdlib and
provisioned offline tools. No dependency downloads or services were used.

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-composer-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-composer-target
export CARGO_NET_OFFLINE=true
```

The `/tmp/kix-composer-no-sockets/sitecustomize.py` audit hook raises before
`socket.__new__`, `socket.connect`, `socket.bind` and `socket.getaddrinfo`.
Both manually captured transcript CLI paths inherit the guard. Some legacy test
children replace their environment; no inherited guard claim is made for those.
The repository's one deliberate HTTP test is excluded under the supervisor's
network prohibition, following the design plan and predecessor evidence.
No CI or production code was edited to accommodate the local environment.

The foreground `/tmp/kix-composer-verify.py PHASE` runner records command argv,
exit status, elapsed seconds and output to `/tmp/kix-composer-PHASE.json`.
`/tmp/kix-composer-discover.py` discovers the booking suite, flattens it and
asserts exactly one exclusion:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The first wrapper invocation failed before executing tests because the wrapper's
`/tmp` import path allowed a same-named settlement test module to shadow this
suite. The wrapper was corrected to put the booking suite first, matching normal
`python -m unittest` discovery. No repository code changed for this harness fix.
The settlement suite already passed and was not rerun for that wrapper correction.

<!-- RESULTS START -->
| Command actually run | Actual result |
|---|---|
| `python3 -B -m unittest test_settlement_console test_shared_ticket_console test_ticket_settlement_inputs test_ticket_statement_distribution test_ticket_operations_client (baseline, before edits)` | PASS, exit 0; 83 tests in 27.946s |
| `python3 -B -m unittest test_settlement_console test_shared_ticket_console test_ticket_settlement_inputs test_ticket_statement_distribution test_ticket_operations_client (after implementation)` | PASS, exit 0; 93 tests in 33.579s |
| `python3 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS, exit 0; 224 tests in 1.730s |
| `python3 -B /tmp/kix-composer-discover.py` | exit 1; Harness ImportError before any booking tests; fixed wrapper, rerun below |
| `python3 -B /tmp/kix-composer-discover.py` | PASS, exit 0; 885 tests in 130.395s; exactly one HTTP test excluded |
| `python3 -B scripts/check_docs_index.py` | PASS, exit 0; docs index ok: scanned=371 indexed=336 allowlisted=35 |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/check_status_register.py` | PASS, exit 0; capability register ok: paths=575 ev_ids=15 original32=32 |
| `python3 -B scripts/check_status_register.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/check_bra_evidence_map.py` | PASS, exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 -B scripts/check_bra_evidence_map.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/check_settlement_evidence_map.py` | PASS, exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 -B scripts/check_settlement_evidence_map.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/check_contract_error_codes.py` | PASS, exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 -B scripts/check_contract_error_codes.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/check_ci_checker_wiring.py` | PASS, exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/check_ci_test_discovery.py` | PASS, exit 0; ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0; self-test pass |
| `python3 -B scripts/verify_runtime_architecture.py` | PASS, exit 0 |
| `python3 -B scripts/test_runtime_architecture.py` | PASS, exit 0; 7 tests in 0.266s |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; UNAVAILABLE: offline cache lacks bcs; no compilation or tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; UNAVAILABLE: offline cache lacks bcs; no compilation or tests ran |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; UNAVAILABLE: offline cache lacks bcs; no compilation or tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; UNAVAILABLE: offline cache lacks bcs; no compilation or tests ran |
| `python3 -B reference/booking_resale_admission/settlement_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_guided_booking.txt > validation/2026-11-08-plan-local-settlement-input-composer/guided_booking.stdout.txt 2> validation/2026-11-08-plan-local-settlement-input-composer/guided_booking.stderr.txt` | PASS, exit 0; 18 full replies, no service errors, empty stderr |
| `python3 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_guided_resale.txt > validation/2026-11-08-plan-local-settlement-input-composer/guided_resale.stdout.txt 2> validation/2026-11-08-plan-local-settlement-input-composer/guided_resale.stderr.txt` | PASS, exit 0; 21 full replies, no service errors, empty stderr |
| `python3 -B /tmp/kix-composer-preserve.py` | PASS, exit 0; 12 allowed changed paths; 110 protected files and 1,559 other tracked files byte-identical; locked blobs, branch/base, AST and diff whitespace pass |
<!-- RESULTS END -->

## Preservation, discrepancies and limitations

Both locked Git blobs matched before edits. A pre-edit SHA-256 manifest at
`/tmp/kix-composer-preservation-before.json` covers 110 files (both locks plus all
108 existing `reference/v0.3-rc1/**` files); manifest SHA-256 is
`9c7c90516fd728796b19b905abb0513235dddd91ccf5eea02838d53f487efaed`.
Final check passed: exactly 12 allowed changed paths; 110 protected files and
1,559 other tracked files byte-identical; branch, HEAD and cached main unchanged;
changed Python syntax and `git diff --check` pass. Required blobs matched before
and after work:

| Locked path | Before and after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
FSMs, desk, adapters, client, SDK, contracts, catalogue, workflow definitions,
runtime flags, `.aiops/**`, `docs/tasks/**` and protected files remain unchanged.

No explicit contract violation or new contract-undefined behavior was found.
Existing class-B zero-cash distribution characterization remains unresolved and
unchanged: `reference/settlement_f01_f03/test_settlement_properties.py::test_e_characterization_zero_cash_commit_then_distribute_conserves`.
The console does not decide zero-cash order-freeze semantics.

No real funds, PG/bank/KYC, public endpoint, Sui chain, storage engine, new command,
new coin/TIX, secret, production runtime, financial/legal compliance, durable
closure, bank exactly-once, chain finality or distributed fencing was implemented
or tested. No equipment, paid service, policy value or scope expansion was needed.

## Deviations and delivery gates

- Fetch omitted under the supervisor's explicit network prohibition; cached main
  equals base but remote freshness is unverified.
- One loopback test excluded under that prohibition; remaining relevant local
  suites/checks are reported with their actual outcomes.
- Local test discovery wrapper corrected for duplicate sibling module names;
  the initial failed harness command is retained in the results.
- Cargo kernel/workspace tests and Clippy were attempted with `--locked --offline`;
  all four commands exit 101 before compilation because neither provisioned local
  registry cache contains `bcs` (needed by workspace member `kix-bcs1`). Architecture
  tests and formatting pass. No download, dependency rewrite, isolated substitute
  workspace or network retry was attempted. These four checks remain unavailable,
  not passed. Full protocol checks for unrelated Move/SDK/chain/ZK/storage paths
  were not run; the protected historical tree was not regenerated.
- No implementation deviation from the design plan. No task document was created;
  no user decision was needed. No policy default or recommendation was chosen.
- Implementation and final committed head: pending supervisor commit. KTX exact-head
  run ID/status/conclusion: not run, no run ID. KIX exact-head run ID/status/conclusion:
  not run, no run ID. Non-author exact-head A2 review: pending.
- Merge SHA/post-merge CI: not applicable; nothing merged. Local builder readiness
  is not merge readiness. The supervisor owns publication; required review and
  both exact-head workflows remain outstanding delivery gates.
