# Caller-entered synthetic resale console payments — builder evidence

Node: `plan-plan-local-resale-payment-console-inputs`. Task input is the supplied
immutable supervisor conversation and design, sourced from planner run
`1793924907` (`/workspace/kix-run/logs/planner_1793924907`). No issue or node-specific
`docs/tasks/` document exists. Dependencies named by the input are
`plan-local-resale-payment-desk`, `plan-plan-local-resale-console` and
`plan-local-shared-ticket-console`. This is not ASTRA program mode. Audit floor
A2; no Astra gate or user merge authorization. This is source-informed console
composition evidence, not independent FSM verification.

## Base, scope and preservation

Branch: `agent/kix-plan-plan-local-resale-payment-console-inputs`.
Observed cached `origin/main`, task base and implementation HEAD:
`7362816e6ab7db4e2db0d4d02d6889c41a307df9`. Initial worktree was clean; local
base delta is zero. The supervisor prohibited network and GitHub actions, so
`git fetch origin main` was omitted. Remote freshness remains unverified.
No commit, push, reset, PR, issue, comment, tag, branch or network action was
performed. The final delivery is an uncommitted patch; there is no new final
committed task head or merge commit. The supervisor owns publication and must
record review and CI for the eventual exact head.

Only the existing `observe_resale_payment` desk selector is exposed. The console
asks for listing, reference, decimal integer amount, explicit JSON buyer/null and
key, displays the full proposal, and sends once after literal `SUBMIT`.
Nullable parsing is shared locally with listing reservation input; other buyer
prompts stay plain text. Service/FSM/client/dispatcher and fixture schemas remain
unchanged. Settlement actions, binding and transfer are separately selected.

A pre-edit SHA-256 snapshot of all 1,432 tracked files was saved as
`/tmp/kix-payment-before.json`. Both locked Git blobs matched before edits and
in the final check:

| Path | Required/observed before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Final preservation checks compare every initially tracked file against that
snapshot and enforce the eight-path output allowlist below. This covers
`reference/v0.3-rc1/**` (historical tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`), `.aiops/**`, `docs/tasks/**`,
contracts, SDK/OpenAPI/catalogue, workflows, runtime settings and unchanged
service/FSM/client/shared-console code. No protected bytes were transiently
mutated. Temporary harnesses and captured output are outside the repository.

## Coverage mapping made before adding tests

Paths below are relative to `reference/booking_resale_admission/`.

| Requirement | Existing coverage classification/evidence | Gap addressed here |
|---|---|---|
| Payment in LISTED/BUY_HELD, buyer/amount matching and replay | Sufficient at service layer: `test_resale_payment_adapter.py::ResalePaymentAdapterTests.test_payment_and_replay_parity_from_listed_and_held_then_explicit_transfer`, `test_semantic_rejections_and_retained_keys_match_direct_fsm`; `test_resale_session.py` | Console entry for a listing absent from recordings was not covered |
| Prompt fidelity, nullable reservation, literal confirmation and integer parsing | Partial: `test_resale_console.py::ResaleConsoleTests.test_every_mutation_requires_literal_single_use_submission`, `test_invalid_inputs_never_submit_or_generate_values`, `test_large_supported_integer_round_trip_and_current_ownership_rendering` | Explicit JSON payment buyer/null, full proposal and zero submissions on invalid/declined/interrupted input |
| Bound/unbound transfer and recorded-payment journey | Sufficient at console/service layer: `test_missing_payment_unknown_record_and_explicit_unbound_transfer`, `test_unknown_and_uncommitted_bound_settlement_preserve_errors`, `test_live_transfer_transcript`, `test_live_cancel_transcript` in `test_resale_console.py` | Compose caller-entered payment with separately selected settlement actions and transfer |
| One shared child and complete replies/flags | Partial: `test_shared_ticket_console.py::SharedTicketConsoleTests.test_live_shared_journey_one_child`, `test_resale_start_journey_creates_target_and_preserves_ticket_observations` | New listing/payment journey, all envelopes compared against equivalent direct dispatch |
| Fencing and no retry/replacement | Sufficient client layer: `test_ticket_operations_client.py::TicketOperationsClientTests.test_malformed_truncated_mismatched_and_exited_workers_never_resend`, `test_short_write_broken_pipe_and_interruption_fence_without_remainder_write`; partial shared-console fault matrices | Add the payment selection to existing matrices and retain successful payment receipt on display failure |

## New focused evidence

| Test in the edited test files | Gap/predicate |
|---|---|
| `ResaleConsoleTests.test_payment_inputs_exact_proposal_and_one_submission_per_confirmation` | Prompt order, full request/proposal/reply, JSON null/string including Unicode, large integer fidelity, decline then exactly one confirmed call, provider limitation wording |
| `test_invalid_payment_inputs_never_submit` | Blank/padded fields, malformed/non-string/empty/padded buyer JSON, fractional/scientific/negative/oversized integer text and blank key send nothing |
| `test_payment_input_failure_at_every_prompt_fences_without_submission` | EOF/interruption/input failure at every new field and confirmation; one cleanup, zero submissions |
| Extended `test_every_mutation_requires_literal_single_use_submission` | New action also declines lowercase confirmation |
| `SharedTicketConsoleTests.test_live_payment_inputs_listed_and_held_one_child_separate_settlement_and_transfer` | Recorded fixture excludes each new listing; one launch/close; exact request sequence, direct-dispatch full reply parity, complete proposals/display and unchanged flags; observation leaves ownership and existing settlement unchanged; separately selected settlement/bind/transfer; historical replay after transfer |
| `test_payment_inputs_buyer_amount_refusals_replay_conflicts_and_unchanged_views` | LISTED null/matching/wrong buyer; BUY_HELD matching/null/wrong buyer; wrong amounts in both phases; retained refusals, exact replay, conflicting key reuse and unchanged current views/ownership after refusal |
| `test_payment_inputs_bound_transfer_gates_and_retained_refusals` | Absent then uncommitted bound settlement refuses; keys retain original refusal after commit; separately entered fresh confirmed transfer succeeds |
| `test_payment_decline_and_confirmation_interrupt_fence_shared_navigation` | Decline sends nothing; EOF/interruption/input failure before approval fences queued surface navigation |
| `test_received_payment_display_failure_retains_accepted_result_and_fences_navigation` | Successful payment receipt retained after broken display; queued actions unread, one child, no retry/replacement |
| `test_payment_transcripts_as_cli_subprocess` | Real shared-console executable and desk child run both checked-in answer files, with 19/20 complete envelopes and historical replay/current view separation |
| Existing shared fault matrices extended through `FAULT_ACTIONS` | Terminal envelopes, malformed/truncated/EOF replies, short write/broken pipe/interrupted read, broken display/diagnostics stop after one payment submission and leave queued navigation unread |

The two new synthetic answer files use the existing
`fixtures/ticket_operations_settlement_inputs_session.json`. Listing IDs
`caller-listed` and `caller-held` are absent from its payment recordings. They
explicitly enter synthetic `ef` repeated 32 times as the payment reference,
`8000` integer KRW, null or matching buyer, and all keys and confirmations.
The settlement inputs reuse the predecessor example's caller-entered 500 bps
policy and two synthetic recorded statements. These are examples, not policy
values or authenticated provider facts. Both transcripts keep payment,
settlement, binding and transfer separate; recorded-payment fixtures stay intact.

## Actual local verification

Results below are actual executions, not proposed commands. Both
`.github/workflows/ktx-kernel.yml` and `.github/workflows/protocol.yml` were
inspected. The selected suites/checkers and offline Rust commands are the
closest practical local equivalents for the touched paths. No bootstrap,
download, hosted job, socket endpoint or detached/background shell job was used.

All Python commands inherited this environment (including child processes that
retain their environment):

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-payment-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary `sitecustomize.py` audit hook raises on `socket.__new__`,
`socket.connect`, `socket.bind` and `socket.getaddrinfo`. Legacy tests that
replace child environments are outside the child-guard claim. The foreground
runner `/tmp/kix-payment-run.py COMMANDS_JSON` executes listed commands once,
sequentially, storing exact commands, exit codes and combined output in
`COMMANDS_JSON.results.json`. It has no automatic retries. Command files are
`/tmp/kix-payment-{baseline,narrow,suites,checks,rust}.json`.

Development runs:

| Command | Actual result |
|---|---|
| `python3 -B -m unittest test_resale_console test_shared_ticket_console` before new tests | PASS: 38 tests |
| Same command with initial new tests | FAIL: 45 tests, 3 failures and 1 error; corrected new test indexing and compared ownership separately because `view_right` also reports listing phase; no service change |
| Same command after correcting assertions | PASS: 45 tests |

| Command actually run | Actual result |
|---|---|
| `python3 -B -m unittest test_resale_console test_shared_ticket_console test_ticket_operations_client test_ticket_operations_cli test_ticket_operations_session test_resale_session test_resale_cli test_resale_payment_source test_resale_payment_adapter` | PASS: 152 tests, exit 0 |
| `python3 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_payment_inputs_listed.txt > /tmp/kix-payment-listed.txt` | PASS: exit 0, 19 full desk envelopes (checked separately) |
| `python3 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_payment_inputs_held.txt > /tmp/kix-payment-held.txt` | PASS: exit 0, 20 full desk envelopes (checked separately) |
| `python3 -B /tmp/kix-payment-offline.py` | PASS: 846 tests, exit 0 |
| `python3 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, exit 0 |
| `python3 -B scripts/check_docs_index.py` | PASS: exit 0 |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_status_register.py` | PASS: exit 0 |
| `python3 -B scripts/check_status_register.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_bra_evidence_map.py` | PASS: exit 0 |
| `python3 -B scripts/check_bra_evidence_map.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_settlement_evidence_map.py` | PASS: exit 0 |
| `python3 -B scripts/check_settlement_evidence_map.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_contract_error_codes.py` | PASS: exit 0 |
| `python3 -B scripts/check_contract_error_codes.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py` | PASS: exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_ci_test_discovery.py` | PASS: exit 0 |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_openapi_contract.py` | PASS: exit 0 |
| `python3 -B scripts/check_openapi_contract.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/check_integration_gate_openapi.py` | PASS: exit 0 |
| `python3 -B scripts/check_integration_gate_openapi.py --self-test` | PASS: exit 0 |
| `python3 -B scripts/verify_runtime_architecture.py` | PASS: exit 0 |
| `python3 -B scripts/test_runtime_architecture.py` | PASS: 7 tests, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101, offline cache missing `bcs`; no compilation |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: exit 101, offline cache missing `bcs`; no compilation |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101, offline cache missing `bcs`; no compilation |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0 |

Rust used the provisioned `cargo 1.98.1` / `rustc 1.98.1` toolchain, existing
Cargo cache, `CARGO_NET_OFFLINE=true` and
`CARGO_TARGET_DIR=/tmp/kix-payment-target`. Kernel/workspace tests and Clippy
all stopped before compilation because the crates.io index cache lacks `bcs`,
required by workspace `kix-bcs1`. They are unavailable, not passed. No download,
dependency/lockfile edit or CI bypass was attempted; provisioned Rust execution
remains a supervisor/CI verification gate. Formatting passed.

| Additional command actually run | Actual result |
|---|---|
| `git status --short` (initial) | Clean worktree |
| `git rev-parse HEAD` / `git rev-parse origin/main` / `git branch --show-current` | Both cached refs equal the stated base; expected task branch |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both required blobs match |
| `git rev-parse HEAD origin/main HEAD:reference/v0.3-rc1` | Unchanged base refs and historical tree stated above |
| `python3 -B /tmp/kix-payment-transcript-check.py` | PASS: 19 LISTED and 20 HELD complete envelopes; no errors; historical payment replay/current transferred view |
| `python3 -B /tmp/kix-payment-preserve.py` | PASS: 1,427 initially tracked files byte-identical; exactly eight allowed changed paths; both locked blobs, historical/protected bytes, refs/branch, ASTs and whitespace checks match |
| `git diff --check` | PASS: exit 0 |

The preservation helper checks all initial tracked SHA-256 hashes outside the
allowed five tracked edits and requires exactly the listed eight outputs after
including untracked files. It checks both required Git blob values, cached
main/HEAD/branch, historical tree, parses the three edited Python files and runs
`git diff --check`. The final documentation record is rechecked after completion.


The broad BRA selection uses `/tmp/kix-payment-offline.py`, the explicit
filtered runner from [shared-console evidence](../2026-11-05-plan-local-shared-ticket-console/README.md).
It asserts unique discovery IDs and exactly one match for the excluded HTTP
socket test:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
Every other discovered test runs; this is not an unfiltered BRA pass.

## Complete changed-path list

- `reference/booking_resale_admission/resale_console.py`
- `reference/booking_resale_admission/test_resale_console.py`
- `reference/booking_resale_admission/test_shared_ticket_console.py`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_payment_inputs_listed.txt`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_payment_inputs_held.txt`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-06-plan-plan-local-resale-payment-console-inputs/README.md`

## Findings, deviations, non-claims and delivery gates

The supplied design was followed. No new protocol command, product policy value
or consequential scope expansion was required. No STOP condition was encountered;
no decision file was necessary. Contract-defined behavior matched the existing
services; no explicit violation or new contract-undefined behavior was found.
Existing class-B zero-cash settlement uncertainty remains untouched; these
examples select positive cash. Product policy remains **UNDETERMINED —
Astra/User**; provider authentication remains **UNDETERMINED — Toss/User**;
legal effects remain **UNDETERMINED — User/legal** and settlement accounting/
legal effects **UNDETERMINED — User/designated advisers**.

Fetch, publication, non-author review and hosted CI were omitted under the
explicit supervisor prohibition. Remote freshness remains unverified. The one
named socket-bearing test is excluded from broad BRA discovery. Rust tests and
Clippy are unavailable due to the missing cached `bcs` dependency. Local results
do not replace required exact-head review or CI.

| Delivery evidence | State |
|---|---|
| Final committed task head | Not created; uncommitted patch on `7362816e6ab7db4e2db0d4d02d6889c41a307df9` |
| Non-author A2 exact-head review | Pending supervisor publication/review |
| Exact-head KTX CI run ID/status/conclusion | Not run; none available |
| Exact-head KIX protocol CI run ID/status/conclusion | Not run; none available |
| Merge SHA / locked blobs at merge / post-merge main CI | Not applicable; no merge authorized or performed |

READY means builder handoff only, not merge-ready. These tests do not establish
real funds execution/safety, provider authentication, bank/KYC behavior,
production readiness, legal/accounting compliance, durability, distributed
fencing, external exactly-once, chain authority/finality or venue credential
reissue. No capability grade or runtime activation changes. Unrelated hosted
Move/localnet/TypeScript/ZK suites, full socket-bearing discovery and production
behavior are not claimed. The supervisor must obtain non-author A2 exact-head
review and both completed/success KTX/KIX workflows before merge readiness and
must preserve the human merge gate. Final CI belongs in external closure
evidence, without a self-referential evidence-only commit loop.
