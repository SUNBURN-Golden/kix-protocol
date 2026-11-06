# Local ticket exception console evidence

Task: `plan-plan-local-ticket-exception-console`. The supplied supervisor node specification and read-only design are the task input; no node-specific file exists under `docs/tasks/`. No task document is changed. Non-ASTRA session; no issue or publication.

Initial branch: `agent/kix-plan-plan-local-ticket-exception-console`. Initial HEAD and cached `origin/main`: `cc77ef105a5d63186e20870e83750bae142c9e0f`. Fetch is prohibited by the supervisor, so remote freshness is unverified; no base change. Planner provenance: run 1793924907, supplied design step.

## Pre-change coverage inventory

Recorded before adding console coverage. Existing tests are source-informed.

| Requirement | Existing evidence | Coverage / console gap |
|---|---|---|
| Fail/cancel INITIATED/AUTHORIZED; CAPTURED/COMMITTED refusal; terminal immutability | `test_ticket_settlement_exceptions.py::test_pre_capture_and_terminal_parity` | Sufficient service coverage; no interactive selectors |
| Replay, changed reason/subject/operation conflicts, retained refusal | Same file `test_replay_and_retained_refusal_keys` | Sufficient service coverage; console composition missing |
| Reconciliation around statements/distribution/refunds; historical receipt | Same file `test_reconcile_history_and_restore` | Sufficient service coverage; console composition missing |
| No ticket mutation, source fetch or compensation from exceptions | Same file `test_settlement_exception_isolation` | Sufficient service coverage; display/selected-request gap |
| Ticket reconciliation, historical keys, ownership transfer STALE_VERSION | `test_ticket_operations_session.py::test_reconciliation_history_and_ownership_change_refusal_without_repair`, `check_reconcile_history`; `test_booking_cli.py::check_reconcile_cli` reused by booking/resale/admission/shared CLI suites; reconciliation tests in `test_booking_session.py`, `test_resale_session.py`, `test_admission_session.py` | Sufficient service coverage; all four console selectors missing |
| Explicit inputs, confirmation, EOF/interruption | Standalone console prompt tests and shared-console input/fault tests | Partial; extend to six new console actions |
| Complete errors, malformed/truncated replies, uncertain write, display failure, one child | `test_shared_ticket_console.py` fault matrix; `test_ticket_operations_client.py` | Partial; extend action matrix and verify already-fenced client never writes |

## Preservation before changes

Both required Git blobs match: kernel lib `69564b166f0c27f9af5d8422f0a466b18d74c20f`; quarantine test `b607996c83a119c349f1cc90469ac1ba82764e20`. Historical `HEAD:reference/v0.3-rc1` tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Initial tracked byte hashes are stored temporarily outside the worktree for final comparison.

## Implementation and new coverage

`booking_console.py`, `resale_console.py`, `admission_console.py` and
`settlement_console.py` expose only their already-dispatched operations.
Booking/admission reconciliation requires literal `RECONCILE`; resale and all
settlement exception actions require `SUBMIT`. Fail/cancel require an explicit
reason. Every selected request prints the full proposal, consumes one approval
and uses the existing client. No service graph/client/adapter/contract changes.
Receipts are explicitly historical, including fresh-key reconciliation; a
separately requested view remains the current observation. No automatic reads,
clock changes, recovery, retries, repair or compensation were introduced.

| New evidence | Gap addressed / concrete result |
|---|---|
| `test_ticket_exception_console.py` (three parameterized tests) | All six actions: ordered opaque subject/reason/key forwarding, full domain/local Unicode/control-character errors, wrong confirmation and approval consumption; blank/padded fields, missing input and EOF/KeyboardInterrupt/OSError at every prompt cause zero submissions |
| `test_shared_ticket_console.py::test_live_cross_surface_reconciliation_history_current_views_and_conflicts` | One real child; all four surfaces; historical replay, explicitly selected current views and fresh keys; subject/cross-operation conflicts; admission's historical success and repeated fresh-key STALE_VERSION after transfer; full-envelope parity with direct service controls and false-flag assertions |
| Same file `test_shared_pre_capture_exceptions_preserve_booking_and_navigation` | Shared-console delivery of the exception transcript, one worker, all four successful pre-capture fail/cancel combinations and unchanged explicit booking observations |
| Same file `test_already_fenced_client_rejects_exception_actions_before_writing_or_restarting` | Actual client is fenced by a short-write uncertainty; all six later actions fail before writing, preserve original uncertainty and unread navigation, and never launch a replacement worker |
| Same file extended `FAULT_ACTIONS` | All six actions participate in terminal envelopes, malformed/truncated/EOF replies, short/broken writes, interrupted exchange, display failures and unavailable diagnostic sink matrices; original replies/available request and reply bytes retained |
| Same file `test_exception_declines_and_confirmation_interrupt_fence_queued_navigation` | Declining sends nothing and permits explicit navigation; confirmation EOF/interruption/input failure terminates the whole shared session without reading queued navigation |
| `test_settlement_console.py::test_live_pre_capture_failure_cancellation_terminal_replays_and_post_capture_refusals` | Fail/cancel from INITIATED and AUTHORIZED, terminal FAILED/CANCELLED with claim=null, same-key replay, changed-reason/subject/operation conflicts, retained refusals, and fail/cancel ILLEGAL_TRANSITION from CAPTURED/COMMITTED; unchanged ticket observations |
| Same file `test_live_reconciliation_around_statements_distribution_refund_and_acceptance` | Explicit capture, statements, distributions, refund binding and synthetic acceptance; reconcile after each selected action, historical replay and current views; unchanged ticket observations; final distributed cash 9301, refund face 4000, outstanding 3000 in this fixture |
| Three answer files and CLI subprocess tests | Runnable shared and standalone interactions, expected statuses 1/1/0, 36/34/26 complete envelopes respectively; stdout/stderr captured beside this record |
| `test_admission_console.py` | Remove reconciliation from obsolete unsupported-action examples |

All controls are source-informed composition evidence, not independent FSM
verification. Existing service tests remain the evidence for transition
semantics and internal isolation; new console tests target the missing UI
composition. No new service semantics or fixture schemas were needed.

## Verification environment and selection

Both `.github/workflows/ktx-kernel.yml` and `.github/workflows/protocol.yml` were
inspected. The focused tests ran first, followed by affected offline reference
suites, documentation/catalogue checks, architecture checks and offline Rust
workflow equivalents. Commands are executed synchronously in a foreground
runner, with no detached/background shell jobs or automatic retries.

Python commands inherit:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-exception-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary `sitecustomize.py` installs a Python audit hook refusing
`socket.__new__`, `socket.connect`, `socket.bind` and `socket.getaddrinfo`.
Legacy subprocess tests that replace their environment are outside the child
hook claim. No network/GitHub action or endpoint was launched for this task.

`/tmp/kix-exception-run.py LABEL COMMANDS_JSON` uses `subprocess.run` once per
listed command, sequentially. The consolidated `command-results.json` retains each batch label, exact argument
array, exit code and complete combined output, including failed development
runs; individual temporary logs were consolidated without dropping output. Expected transcript refusals
exit 1 and are not failing tests. Three standalone CLI executions additionally
record their separate stdout/stderr and explicit input paths in
`transcript-results.json`.

The only BRA exclusion is the established socket-bearing test below. The runner
asserts unique test IDs and exactly one occurrence of that exclusion. This is an
explicit offline selection, not a full/unfiltered BRA or HTTP CI pass. Its exact
corrected body (`/tmp/kix-exception-offline.py`) is:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("reference/booking_resale_admission").resolve()))
suite = unittest.defaultTestLoader.discover(
    'reference/booking_resale_admission', top_level_dir='reference/booking_resale_admission')
def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test
all_tests = list(flatten(suite))
ids = [t.id() for t in all_tests]
assert len(ids) == len(set(ids)), 'duplicate discovery IDs'
excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
assert ids.count(excluded) == 1
print('EXCLUDED SOCKET TEST: ' + excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(
    unittest.TestSuite(t for t in all_tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

## Actual commands and results

Full combined stdout/stderr, argument arrays and exit codes are preserved in
[command-results.json](command-results.json). Test counts below come from those
actual executions. A broad-suite count is not additive with its focused subsets.

Development corrections were limited to transcript/test-runner inputs. The first
console run exposed the existing explicit booking session-clock prerequisite.
The targeted run then exposed an invalid synthetic admission request label; it
was replaced with the already-supported 32-byte request fixture value. No
service code or semantics changed. The first broad BRA discovery attempt failed
before tests because the temporary runner left the suite behind the settlement
import path; explicitly placing BRA at `sys.path[0]` fixed discovery. These
failed attempts remain recorded, not relabeled as passes.

| Batch / exact command | Actual result |
|---|---|
| baseline · `python3.12 -B -m unittest test_ticket_settlement_exceptions test_booking_session test_resale_session test_admission_session test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_client` | PASS: 88 tests, exit 0 |
| narrow-first · `python3.12 -B -m unittest test_booking_console test_resale_console test_admission_console test_settlement_console test_shared_ticket_console test_ticket_exception_console` | FAIL: exit 1; 114 tests; FAILED (failures=2) |
| targeted · `python3.12 -B -m unittest test_shared_ticket_console.SharedTicketConsoleTests.test_live_cross_surface_reconciliation_history_current_views_and_conflicts test_shared_ticket_console.SharedTicketConsoleTests.test_reconciliation_transcript_as_cli_subprocess test_shared_ticket_console.SharedTicketConsoleTests.test_shared_pre_capture_exceptions_preserve_booking_and_navigation` | FAIL: exit 1; 3 tests; FAILED (failures=1, errors=1) |
| targeted-corrected · `python3.12 -B -m unittest test_shared_ticket_console.SharedTicketConsoleTests.test_live_cross_surface_reconciliation_history_current_views_and_conflicts test_shared_ticket_console.SharedTicketConsoleTests.test_reconciliation_transcript_as_cli_subprocess test_shared_ticket_console.SharedTicketConsoleTests.test_shared_pre_capture_exceptions_preserve_booking_and_navigation` | PASS: 3 tests, exit 0 |
| narrow-final · `python3.12 -B -m unittest test_booking_console test_resale_console test_admission_console test_settlement_console test_shared_ticket_console test_ticket_exception_console` | PASS: 115 tests, exit 0 |
| suites · `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, exit 0 |
| suites · `python3.12 -B /tmp/kix-exception-offline.py` | FAIL: exit 1; no tests ran; import-path discovery collision |
| suites · `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS: 168 tests, exit 0 |
| suites · `python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS: 117 tests, exit 0 |
| suites · `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS: 200 tests, exit 0 |
| suites · `python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS: 73 tests, exit 0 |
| suites · `python3.12 -B -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, exit 0 |
| bra-corrected · `python3.12 -B /tmp/kix-exception-offline.py` | PASS: 857 tests, exit 0 |
| checks · `python3.12 -B scripts/verify_runtime_architecture.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/test_runtime_architecture.py` | PASS: 7 tests, exit 0 |
| checks · `python3.12 -B scripts/check_docs_index.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_docs_index.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_status_register.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_status_register.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_bra_evidence_map.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_bra_evidence_map.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_settlement_evidence_map.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_settlement_evidence_map.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_contract_error_codes.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_contract_error_codes.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_ci_checker_wiring.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_ci_test_discovery.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_openapi_contract.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_openapi_contract.py --self-test` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_integration_gate_openapi.py` | PASS, exit 0 |
| checks · `python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | PASS, exit 0 |
| rust · `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101; cached `bcs` absent, stopped before compilation |
| rust · `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: exit 101; cached `bcs` absent, stopped before compilation |
| rust · `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101; cached `bcs` absent, stopped before compilation |
| rust · `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

The corrected broad BRA run includes the final tightened uncertainty exception
assertion. Other affected offline suites all passed. Architecture gate output
certifies only the declared dependency boundary; it does not certify durability
or performance. Nine documentation/catalogue/wiring checkers passed both normal
and self-test modes; runtime architecture tests passed seven cases. No CI
workflow was changed.

Rust used provisioned `cargo 1.98.1` / `rustc 1.98.1`,
`CARGO_NET_OFFLINE=true` and `CARGO_TARGET_DIR=/tmp/kix-exception-target`.
Python was 3.12.15. Both Rust test commands and Clippy failed dependency
resolution before compilation because the offline crates.io cache lacks `bcs`,
required by `kix-bcs1`. Those checks are unavailable, never passes. No download,
cache bootstrap, lockfile edit or CI bypass was attempted. Formatting passed.

| Exact transcript command | Actual result | Captured output |
|---|---|---|
| `python3.12 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_reconcile.txt` | Expected exit 1; 36 complete envelopes | [stdout](shared_ticket_console_reconcile.stdout), [stderr](shared_ticket_console_reconcile.stderr) |
| `python3.12 -B reference/booking_resale_admission/settlement_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_exceptions_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_exceptions.txt` | Expected exit 1; 34 complete envelopes | [stdout](settlement_console_exceptions.stdout), [stderr](settlement_console_exceptions.stderr) |
| `python3.12 -B reference/booking_resale_admission/settlement_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_exceptions_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_reconcile.txt` | Expected exit 0; 26 complete envelopes | [stdout](settlement_console_reconcile.stdout), [stderr](settlement_console_reconcile.stderr) |

The helper `python3.12 -B /tmp/kix-exception-transcripts.py` passed checks of
all three expected exits, complete-envelope counts and historical labels. Full
parity with direct service controls is asserted by the real-child unit tests;
transcript capture is an additional CLI execution, not independent validation.

## Final preservation and complete changed paths

`python3.12 -B /tmp/kix-exception-preserve.py` compares initial tracked SHA-256
byte hashes, requires exactly nine allowed tracked edits and four new console
test/answer files, rejects new paths outside this evidence directory, verifies
refs/branch, checks both required Git blobs, parses every changed/new Python
file and runs `git diff --check`. It passes: **1,426 of 1,435 initially tracked
files remain byte-identical**, with exactly the nine allowed tracked changes.
That includes every file in `reference/v0.3-rc1/**`, both locked kernel files,
services, clients, contracts, SDK/OpenAPI, runtime flags, workflows, `.aiops/`,
program plan and `docs/tasks/`. See [preservation.json](preservation.json) for
machine-readable values and [changed-paths.txt](changed-paths.txt) for the
complete changed-path list, including evidence files.

Both blobs match before and after work:

| File | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Other inspection/preservation commands actually run:

| Command | Actual result |
|---|---|
| `git status --short` (initial) | Clean |
| `git rev-parse HEAD` / `git rev-parse origin/main` | Both cached refs `cc77ef105a5d63186e20870e83750bae142c9e0f` |
| `git branch --show-current` | `agent/kix-plan-plan-local-ticket-exception-console` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before work; repeated by final preservation helper |
| `git ls-tree HEAD reference/v0.3-rc1` | Historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |
| `git diff --check` | PASS; also run by preservation helper |
| `python3.12 -B /tmp/kix-exception-preserve.py` | PASS; permitted paths only, all other initial tracked bytes identical, refs/branch unchanged, locked blobs match, ASTs valid |
| `python3.12 --version` / `cargo --version` / `rustc --version` | Python 3.12.15; cargo/rustc 1.98.1 |

Complete changed paths:

```text
docs/README.md
reference/booking_resale_admission/README.md
reference/booking_resale_admission/admission_console.py
reference/booking_resale_admission/booking_console.py
reference/booking_resale_admission/fixtures/settlement_console_exceptions.txt
reference/booking_resale_admission/fixtures/settlement_console_reconcile.txt
reference/booking_resale_admission/fixtures/shared_ticket_console_reconcile.txt
reference/booking_resale_admission/resale_console.py
reference/booking_resale_admission/settlement_console.py
reference/booking_resale_admission/test_admission_console.py
reference/booking_resale_admission/test_settlement_console.py
reference/booking_resale_admission/test_shared_ticket_console.py
reference/booking_resale_admission/test_ticket_exception_console.py
validation/2026-11-06-plan-plan-local-ticket-exception-console/README.md
validation/2026-11-06-plan-plan-local-ticket-exception-console/changed-paths.txt
validation/2026-11-06-plan-plan-local-ticket-exception-console/command-results.json
validation/2026-11-06-plan-plan-local-ticket-exception-console/preservation.json
validation/2026-11-06-plan-plan-local-ticket-exception-console/settlement_console_exceptions.stderr
validation/2026-11-06-plan-plan-local-ticket-exception-console/settlement_console_exceptions.stdout
validation/2026-11-06-plan-plan-local-ticket-exception-console/settlement_console_reconcile.stderr
validation/2026-11-06-plan-plan-local-ticket-exception-console/settlement_console_reconcile.stdout
validation/2026-11-06-plan-plan-local-ticket-exception-console/shared_ticket_console_reconcile.stderr
validation/2026-11-06-plan-plan-local-ticket-exception-console/shared_ticket_console_reconcile.stdout
validation/2026-11-06-plan-plan-local-ticket-exception-console/transcript-results.json
```

## Findings, deviations, non-claims and remaining gates

Contract-defined behavior matches the unchanged services. No explicit contract
violation or new contract-undefined behavior was found. Existing class-B
zero-cash settlement uncertainty is unchanged; these new distribution examples
select positive cash. Product policy remains **UNDETERMINED — Astra/User**;
legal/accounting effects remain **UNDETERMINED — User/designated advisers**.
No policy value, new command, external resource or other STOP condition was
needed; no decision file was created.

Design deviation: common prompt/input/error cases are centralized in the new
`test_ticket_exception_console.py` instead of duplicating those cases in all
four standalone test modules. Existing standalone suites still run in full.
Real-child cases extend the existing shared/settlement helpers as planned.
The shared transcript additionally selects the booking clock and supplies the
existing admission request format. No service/contract changes were needed.

Supervisor constraints override fetch/publication steps: no fetch, GitHub/network
action, commit, push, issue/comment/PR, readiness change or merge was performed.
Remote main freshness is unverified. The established single socket test is
excluded from BRA discovery; HTTP tests remain a CI gate. Rust tests/Clippy are
unavailable due to cached dependencies. These are documented validation limits,
not evidence that those gates passed.

| Delivery evidence | State |
|---|---|
| Task input | Supplied node specification/design; no node-specific `docs/tasks/` document or issue |
| Observed local base / implementation HEAD | `cc77ef105a5d63186e20870e83750bae142c9e0f` (cached main and initial/final local HEAD) |
| Exact final committed task head | Not created: uncommitted patch; supervisor commits |
| Non-author exact-head A2 review | Pending supervisor delivery |
| Exact-head KTX CI run ID/status/conclusion | Not run; no run ID or conclusion available |
| Exact-head KIX protocol CI run ID/status/conclusion | Not run; no run ID or conclusion available |
| Merge SHA / locked blobs at merge / post-merge main CI | Not applicable; no merge authorized/performed |

READY means builder handoff only, not merge-ready or production-ready. The
supervisor must obtain non-author exact-head A2 review and completed/success
KTX/KIX workflows for the final committed head. Human-only merge authorization
remains required. Final-head CI belongs in external delivery evidence without a
self-referential evidence commit.

These local tests do not establish real funds execution or refund completion,
provider/operator authentication, PG/bank/KYC behavior, production readiness,
legal/accounting compliance, durability, distributed fencing, external
exactly-once, chain authority/finality or venue credential reissue. Authenticated
operator evidence and durable recovery remain outside this node. Unrelated
Move/localnet/ZK/TypeScript and full socket-bearing/hosted workflow executions
are not claimed. No capability grade or runtime activation changed. Remaining
follow-ups are the supervisor's dependency-provisioned Rust verification, HTTP
and exact-head hosted checks/review, and separately authorized operator-evidence
work; none were implemented here.
