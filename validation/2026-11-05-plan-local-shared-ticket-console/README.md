# Shared local ticket console — builder evidence

Node: `plan-local-shared-ticket-console`. Task input is the supervisor-provided
node specification and read-only design plan in the executing conversation.
There is no issue or current `docs/tasks/` document for this node; none was
created or edited. This is not ASTRA program mode. Local builder evidence only;
non-author A2 exact-head review and exact-head KTX/KIX CI remain delivery gates.

## Input and source

Objective: compose booking, resale, admission and settlement into one live local
terminal session, reusing their `run_console` functions and existing dispatcher
operations. Navigation must send no requests, re-entry must invalidate booking
previews, and terminal failures must stop requests across every surface.
Scope: console composition, focused tests, synthetic answers and indexed usage
and validation documentation. Dependencies: `plan-local-ticket-stdio-client`,
`plan-plan-local-booking-console`, `plan-plan-local-resale-console`,
`plan-plan-local-admission-console`, `plan-plan-local-settlement-console`.
Audit floor A2; no Astra gate or user merge authorization in this node input.
The conversation is the immutable task input, not a new repository task document.

Observed branch: `agent/kix-plan-local-shared-ticket-console`.
Initial cached `origin/main`, task base and implementation HEAD all equal
`f41b03ab669f633c233ce49a1c069834d358b924`. The worktree was clean and there was
no local base delta. The supervisor explicitly prohibited GitHub/network
operations, so `git fetch origin main` was omitted. Remote freshness remains
unverified. No rebase, commit, push, reset, PR, issue, comment or network action
was performed. The supervisor owns Git/GitHub publication.

Final task work is an uncommitted patch. HEAD and cached main remain the above
SHA; there is no distinct final committed task head or merge commit from this
session. The eventual exact head must receive fresh non-author review and CI.

## Preservation

A pre-edit SHA-256 snapshot of all 1,358 initially tracked files was saved to
`/tmp/kix-shared-before.json`. Both locked blobs matched before editing and in
the final preservation check:

| Path | Required and observed Git blob, before/after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

All 1,356 initially tracked files outside the two edited documentation files
remain byte-identical. Four new files complete the six-path output allowlist.
`reference/v0.3-rc1/**` working bytes are unchanged; the historical Git tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The snapshot also covers `.aiops/`,
`docs/tasks/`, contracts, FSMs, existing consoles/client/session/dispatcher,
SDK/catalogue, workflow and configuration bytes. No protected source was edited,
regenerated, reformatted or transiently mutated. No new protocol command or
product policy was needed. A final preservation helper enforces the exact
changed-path allowlist, hashes, branch/refs, Python AST parsing and clean
`git diff --check`.

## Existing coverage mapped before new tests

Paths below are relative to `reference/booking_resale_admission/` unless noted.
These new checks are source-informed composition evidence, not clean-room FSM
verification or a capability-grade promotion.

| Requirement | Existing classification and exact evidence | Composition gap |
|---|---|---|
| One shared graph | Partial: `test_ticket_operations_session.py::TicketOperationsSessionTests.test_one_shared_graph_per_construction_and_custom_inputs`; `test_ticket_operations_client.py::TicketOperationsClientTests.test_buffered_child_reply_before_stdin_eof_and_response_derived_journey` | Switching real console surfaces while retaining earlier mutations and one child lifecycle |
| Existing business semantics and envelopes | Sufficient service-layer evidence: `test_ticket_operations_session.py::TicketOperationsSessionTests.test_transcripts_session_and_cli_match_direct_graph_after_every_request`, `test_ticket_operations_client.py::TicketOperationsClientTests.test_domain_and_source_errors_allow_explicit_continuation` | Full envelopes and refusal status must survive shared-menu navigation |
| Booking invalidation | Partial: `test_booking_console.py::BookingConsoleTests.test_reloading_even_whitespace_and_editing_identifiers_require_new_preview` | Leaving and re-entering booking must discard quote, target and pending confirmation |
| Navigation | Not covered across surfaces; existing four console suites cover their own local actions | Menu choices/unknown choices/enter/leave must cause zero business requests |
| Transport and terminal fencing | Sufficient client-layer evidence: `test_ticket_operations_client.py::TicketOperationsClientTests.test_malformed_truncated_mismatched_and_exited_workers_never_resend`, `test_short_write_broken_pipe_and_interruption_fence_without_remainder_write`; partial per-surface console coverage | Terminal failure must prevent subsequent menu/surface actions and replacement launch |
| Receipts/current views and false flags | Sufficient local service/surface evidence in `test_resale_console.py::ResaleConsoleTests.test_live_transfer_transcript`, `test_admission_console.py`, `test_settlement_console.py::SettlementConsoleTests.test_live_journey`, `test_reservation_fsm.py::assert_not_final`, `test_admission_session.py::assert_flags`, `test_ticket_settlement_controls.py::settlement_flags` | Explicit views after switching must retain earlier local facts and synthetic boundaries |
| Settlement arithmetic/obligations | Sufficient: `reference/settlement_f01_f03/test_mock_settlement.py` and existing settlement controls/facts suites | No duplicate arithmetic or new economic semantics; only compose existing distribution/view |

## New composition evidence

All methods below belong to `SharedTicketConsoleTests` in
`test_shared_ticket_console.py`. Helpers are imported as functions, never as
`TestCase` classes, so discovery does not duplicate predecessor suites.

| Test | Gap addressed |
|---|---|
| `test_live_shared_journey_one_child` | One actual child launch and one close; exact sequence of 18 requests through real consoles on all four surfaces; direct-service parity for every full envelope, revisited booking/resale/settlement views and unchanged synthetic flags |
| `test_navigation_sends_nothing` | Unknown menu inputs and visits/exits on all four surfaces produce zero requests; every delegate receives identical client and stream objects; embedded caller owns close |
| `test_booking_reentry_discards_preview` | Prior successful preview cannot confirm after re-entry; missing reload/target blocks preview, fresh preview and literal confirmation required, decline consumes preview |
| `test_actual_business_refusals_allow_explicit_switching` | Real domain `{code}` refusals on all four surfaces, real payment/statement source `{type,message}` refusals, exact direct-service parity and explicit later successful view |
| `test_exact_refusal_envelope_matrix_and_sticky_status` | Both error-envelope forms on every surface preserve text/escaping and sticky exit 1 even after entering/exiting a clean surface |
| `test_terminal_envelopes_fence_every_surface` | Fixture/booking-input/null-selector terminal envelopes preserved; later selections for every surface remain unread |
| `test_real_malformed_truncated_and_eof_replies_fence_every_surface` | Actual controlled child replies, retained uncertainty bytes/request, one request/launch/close, no queued navigation consumed |
| `test_real_write_uncertainty_and_request_interruption_fence_every_surface` | Broken pipe, short write and interrupted read on real client transport; no remainder submission/retry/replacement/compensation |
| `test_input_failures_at_menu_and_every_surface_fence_queued_navigation` | EOF, interruption and failed input after an explicit view (or at menu) stop before queued requests; received reply retained in surface diagnostics |
| `test_display_failures_fence_all_surfaces_even_with_broken_diagnostics` | Broken output after received reply fences all surfaces, preserves last reply where sink works, broken diagnostic sink never authorizes another request; initial menu output failure sends nothing |
| `test_unexpected_surface_results_and_exceptions_stop_without_more_input` | Invalid delegate statuses and unexpected exceptions/interruption fence every surface before reading more input |
| `test_cli_arguments_import_launch_and_cleanup_failures` | Required fixture/positive finite budget, inert import, launch failure, exactly one close and cleanup status precedence for clean/refused/terminal sessions |
| `test_documented_transcript_as_cli_subprocess` | Real new terminal entry point and desk child using the checked-in synthetic answers, all four surfaces and 18 intact envelopes |

The [usage and checked-in answers](../../reference/booking_resale_admission/README.md#shared-local-ticket-console)
show explicit fixture clock selection, free-slot booking confirmation, an
independent existing ticket's resale/payment/transfer, stale admission
presentation and distribution of fixture cash. Revisited current views report
`CONFIRMED`, holder `buyer-2` / version `2`, and distributed cash `8000`.
The stored venue credential stays `buyer-1` / version `1`; `STALE_VERSION` is
preserved. The booking confirmation is not payment or issuance. These fixture
records are not automatically linked into a new commercial transaction.

## Executed local verification

All Python verification used the parent/child socket-denial guard from the
predecessor [settlement validation](../2026-11-05-plan-plan-local-settlement-console/README.md):

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-shared-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-shared-no-sockets/sitecustomize.py` contains:

```python
import sys

def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by local console verification guard: ' + event)

sys.addaudithook(deny_socket)
```

New subprocess tests/probes inherit this guard. Legacy probes replacing their
child environment are outside the child-guard claim. No sockets, downloads or
dependency bootstrap were used. Jobs ran in the foreground; no detached or
background shell job was started. Both `.github/workflows/ktx-kernel.yml` and
`.github/workflows/protocol.yml` were inspected; these are their closest
practical offline equivalents for the touched paths, not full hosted CI.

Initial development runs are retained as actual failures, not green evidence:

| Command | Actual result and correction |
|---|---|
| New shared CLI transcript command below, first run | Exit 2: `BookingInputError` required explicit successful session clock before hold; added caller-selected clock inputs, no service change |
| Same transcript, second run | Exit 1: exact `DISTRIBUTION_ORDER_MISMATCH`; corrected caller order to fixture's sole `organizer` obligation, no policy/service change |
| `python3 -B -m unittest test_shared_ticket_console` (initial) | Exit 1: 13 tests, 1 failure and 2 errors; corrected expected preview count, used existing resale-specific flag helper, and handled the direct helper's uncaught known source errors in parity expectations |
| Same focused command after corrections | PASS: 13 tests, exit 0 |

The foreground runner `/tmp/kix-shared-run.py COMMANDS_JSON` executes each
listed command sequentially under that environment and saves its exact command,
exit code and combined stdout/stderr to `COMMANDS_JSON.results.json`. It does
not retry commands. Command sets were `/tmp/kix-shared-narrow.json`,
`/tmp/kix-shared-suites.json`, `/tmp/kix-shared-checks.json` and
`/tmp/kix-shared-rust.json`. The following table records the final actual runs.

| Command actually run | Actual result |
|---|---|
| `python3 -B -m unittest test_shared_ticket_console` | PASS: 13 tests, exit 0 |
| `python3 -B -m unittest test_booking_console test_resale_console test_admission_console test_settlement_console test_ticket_operations_client test_ticket_operations_session test_ticket_operations_cli` | PASS: 109 tests, exit 0 |
| `python3 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_payment_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_journey.txt > /tmp/kix-shared-transcript.txt` | PASS: exit 0, 18 desk envelopes |
| `python3 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, exit 0 |
| `python3 -B /tmp/kix-shared-offline.py` | PASS: 818 tests, exit 0; exactly one named HTTP socket test excluded |
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
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101, offline cache missing `bcs` before compilation |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101, offline cache missing `bcs` before compilation |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0 |

Rust commands used only the provisioned toolchain and existing cache:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-console-target
export CARGO_NET_OFFLINE=true
```

The missing `bcs` dependency is required by workspace `kix-bcs1`. Neither Rust
tests nor Clippy reached compilation; they are **unavailable**, not passed.
No Rust code, dependency, lockfile or CI was changed to bypass the cache.
Formatting and both architecture checks passed. Provisioned Rust testing/Clippy
and full workspace verification remain supervisor/CI gates.

The 818-test broad BRA runner uses the predecessor's single explicit exclusion:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
That test starts an HTTP socket. This is not an unfiltered BRA pass. No other
test is excluded. `/tmp/kix-shared-offline.py` contains:

```python
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path('reference/booking_resale_admission').resolve()))
excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
suite = unittest.defaultTestLoader.discover('reference/booking_resale_admission', top_level_dir='reference/booking_resale_admission')
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item
tests = list(flatten(suite))
assert sum(t.id() == excluded for t in tests) == 1
assert len({t.id() for t in tests}) == len(tests), 'duplicate test discovery'
print('Explicit single HTTP exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(t for t in tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

## Final local evidence checks

| Command actually run | Actual result |
|---|---|
| `git status --short --branch` (initial) | Clean expected task branch |
| `git rev-parse origin/main HEAD` | Both cached refs `f41b03ab669f633c233ce49a1c069834d358b924`; no local base drift |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs matched before edits |
| `python3 -B /tmp/kix-shared-preserve.py` | PASS: 1,356 initially tracked files byte-identical, exactly six allowed changed paths, both locked blobs and historical bytes/tree unchanged, refs/branch unchanged, new ASTs parse, `git diff --check` clean |
| `python3 -B scripts/check_docs_index.py` (after completed evidence record) | PASS: exit 0, scanned=355 indexed=320 allowlisted=35 |

The preservation command compares every initial tracked file SHA-256, unions
changed paths with untracked paths and requires exactly the six paths below.
It verifies both required Git blob hashes and unchanged cached main/HEAD/branch,
the historical Git tree and protected working bytes. Temporary harnesses and
transcript output are outside the repository and are not delivery files.

## Complete changed-path list

- `reference/booking_resale_admission/shared_ticket_console.py`
- `reference/booking_resale_admission/test_shared_ticket_console.py`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_journey.txt`
- `reference/booking_resale_admission/README.md`
- `validation/2026-11-05-plan-local-shared-ticket-console/README.md`
- `docs/README.md`

## Deviations, uncertainty and delivery gates

The supplied design was followed. Caller inputs explicitly select the existing
booking clock and the fixture's single-payee distribution order. No automatic
clock, view, compensation or business request was added. Fetch and all
publication/review/hosted CI were omitted under the explicit supervisor rule.
Remote main freshness remains unverified. The broad runner excludes exactly the
named socket-bearing test. Offline Rust test/Clippy execution is unavailable
because the cache lacks `bcs`; no downloads were attempted. No STOP condition or
consequential scope expansion was encountered, so no decision file was needed.

Contract-defined behavior matched existing services; no explicit contract
violation was found. No new contract-undefined behavior was defined. Existing
class-B zero-cash distribution uncertainty remains as recorded by predecessor
settlement evidence; this composition selects positive fixture cash and does not
resolve it. Product/admission/distribution policy remains **UNDETERMINED —
Astra/User**; legal effects **UNDETERMINED — User/legal**; settlement accounting/
legal effects **UNDETERMINED — User/designated advisers**.

| Delivery evidence | State |
|---|---|
| Final committed task HEAD | Not created; uncommitted builder patch on `f41b03ab669f633c233ce49a1c069834d358b924` |
| Non-author A2 exact-head review | Pending supervisor publication |
| Exact-head KTX kernel CI run ID/status/conclusion | Not run; no run ID, status or conclusion available |
| Exact-head KIX protocol CI run ID/status/conclusion | Not run; no run ID, status or conclusion available |
| Merge commit / locked blobs on final merge / post-merge main CI | Not applicable; no merge authorized or performed |

These local results do not establish real funds safety, real provider/bank/KYC
behavior, production admission, external exactly-once, distributed fencing,
durability, chain authority/finality, legal/accounting compliance or durable P04
closure. No capability grade or runtime activation was changed. Full
socket-bearing discovery, Rust execution and unrelated hosted protocol suites
(Move, storage, localnet, TypeScript, ZK) are not claimed. The supervisor must
record the eventual exact-head review/CI externally without creating a CI
self-reference commit loop. This report does not authorize merge.
