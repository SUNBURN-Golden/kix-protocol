# plan-local-fulfillment-console — local builder evidence

Task input: the supervisor-supplied node and design in this conversation; no
issue or task document exists. Non-ASTRA session; supervisor owns Git/GitHub.
Branch `agent/kix-plan-local-fulfillment-console`; initial HEAD/base and cached
`origin/main`: `3bfba955888f8aac53bb7188ece8b34370b60db9`. Initially clean.
Fetch is prohibited by the supervisor's no-network rule; remote freshness is
unverified. No local base delta, rebase or history change.

## Existing coverage mapped before adding tests

Paths are relative to `reference/booking_resale_admission/`.

| Requirement | Existing classification and evidence | Console gap |
|---|---|---|
| Prepared paid issuance and separate target adoptions | Partial: `test_ticket_fulfillment.py::TicketFulfillmentTests.test_prepared_second_ticket_matches_direct_graph`; `test_ticket_issued_handoff.py::TicketIssuedHandoffTests.test_separate_adoptions_lifecycle_replay_exact_calls_and_unrelated_state` | Real-child interactive prompts, explicit views, one launch/close |
| Authorization then independent consumption | Partial: `test_admission_console.py::AdmissionConsoleTests.test_authorization_alone_never_consumes` and `test_declined_consumption_submits_nothing` | Start from explicit issuance, adopt then authorize and separately confirm consumption |
| Issuance without payment | Sufficient service coverage: `test_ticket_fulfillment.py::TicketFulfillmentTests.test_issuance_before_payment_and_retained_refusal` | Preserve original refusal and unchanged view at prompt boundary |
| Source refusal, reservation/right mismatch, recovery using same key | Sufficient service coverage: `test_ticket_issued_handoff.py::TicketIssuedHandoffTests.test_source_failures_bind_no_keys_then_recover_same_key_and_match_direct_refusals` | Original source error envelopes and explicit continuation across surfaces |
| Decline and exact outgoing request | Partial: existing booking/resale/admission prompt suites | New literal confirmations and exactly three caller fields; no UI payload assembly |
| Exact replay, conflicting keys, receipt/current distinction | Sufficient service coverage: fulfillment and handoff lifecycle/replay tests above, `test_same_key_changed_subject_body_or_operation` in fulfillment | Interactive replay after consumption must retain historical version 1; current booking/admission version 2; resale independently version 1 |
| Uncertainty and terminal fencing | Sufficient client coverage: `test_ticket_operations_client.py::TicketOperationsClientTests.test_malformed_truncated_mismatched_and_exited_workers_never_resend`, `test_short_write_broken_pipe_and_interruption_fence_without_remainder_write`; partial shared console fault matrix | Exercise all four new actions with queued surfaces; one send, one cleanup, no replacement |
| False flags, policy ownership, protected paths | Sufficient existing helpers: `test_reservation_fsm.py::assert_not_final`, `test_resale_fsm.py::assert_not_final`, `test_admission_session.py::assert_flags` | Apply helpers and full envelope parity to new journeys; hash preservation checks |

This is source-informed console composition evidence, not independent protocol
verification, a policy decision or a capability-grade promotion.

## Implementation and new evidence

Only the three console prompt loops, their tests, terminal answer fixtures and
usage/evidence documentation changed. New booking actions require literal
`BIND_SETTLEMENT` / `ISSUE`; admission adoption requires `ADOPT`; resale adoption
uses existing `SUBMIT`. Each proposal is printed before approval. Declines send
nothing. Booking labels received receipts as historical and explicit views as
current observations. No business eligibility logic or adoption payload is
assembled in the UI. Resale preserves nullable JSON reservation input for
listing; its adoption reservation input is required plain text, matching the
other new caller identifiers. No service/adapter/FSM/schema/catalogue changes.

| New or expanded test | Composition gap addressed |
|---|---|
| `test_fulfillment_prompt_exact_request_decline_and_original_errors` in each of the three console suites | Prompt order, complete proposed envelope, opaque explicit caller fields, literal decline, exactly one confirmed request, unchanged original source/domain error details |
| `test_fulfillment_confirmation_interruption_sends_nothing` in each console suite | EOF, interruption and failed input before approval send nothing and fence |
| `SharedTicketConsoleTests.test_live_fulfillment_separate_actions_one_child_and_explicit_views` | Actual child, one launch/cleanup, 11-request sequence, unchanged prepared paid fixture, explicit clock/binding/issuance/separate adoptions and explicit views, full direct-session parity and false flags |
| `test_live_fulfillment_authorize_decline_consume_then_historical_replays` | 22 actual requests: authorization alone and declined consumption preserve `AUTHORIZED` at version 1; separately confirmed consumption reaches version 2; exact issuance/adoption replay retains historical version 1 and duplicate/applied semantics; resale retains independently observed version 1 |
| `test_live_fulfillment_boundaries_preserve_source_domain_and_key_results` | 25 actual requests: pre-issuance source refusal, missing/crossed source pairs, decline, recovery using formerly source-refused keys, exact replay and all four target/domain key conflicts |
| `test_live_issue_without_payment_preserves_refusal_and_current_view` | Remove only second-order payment setup in a temporary fixture; repeat issuance preserves retained `ILLEGAL_TRANSITION`; current view stays `CONFIRMED` with no payment/right; explicit navigation continues |
| `test_fulfillment_requires_explicit_successful_booking_clock` | Fixture clocks do not authorize booking-session mutation; original terminal `BookingInputError` fences queued surfaces |
| Expanded existing shared `test_terminal_envelopes_fence_every_surface`, `test_real_malformed_truncated_and_eof_replies_fence_every_surface`, `test_real_write_uncertainty_and_request_interruption_fence_every_surface`, `test_display_failures_fence_all_surfaces_even_with_broken_diagnostics` | All four new actions join the predecessor matrix: terminal envelopes, actual malformed/truncated/EOF replies, short/broken/interrupted transport and failed output preserve last reply/uncertainty and leave later surfaces unread, with one launch/close and no retry/replacement |

The [usage and three answer transcripts](../../reference/booking_resale_admission/README.md#guided-local-fulfillment-in-the-shared-console)
identify synthetic `reserve-2`, `order-2`, `issue-2`, `claim-2`, `buyer-3`, clock
`1000000`, payment reference `cd` repeated 32 times and amount `10001` KRW.
These are caller examples, never policy defaults. Setup stops at PAYMENT_NOTED
for the second ticket; it neither binds nor issues nor adopts it. The blocked
payment-reservation handoff remains untouched. Consumption uses existing
caller-entered authorization/consumption identifiers, version, gate, request,
expiry, keys and separate approvals. Receipts and explicit current views are
compared with the existing direct service graph; this shares implementation
and is not independent verification. Tests import helper functions without
introducing TestCase classes into discovery namespaces.

## Verification environment

Python commands below actually used installed Python **3.12.15** (`python3.12`);
`python3` on this host is 3.13.5, so the explicit 3.12 executable was selected.
Both `.github/workflows/ktx-kernel.yml` and `.github/workflows/protocol.yml` were
inspected. No toolchain/dependency bootstrap, sockets, network or background
shell jobs were used. This is the closest practical offline verification for
the changed Python/document paths, not a complete hosted protocol run.

All test/check children inherited:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-shared-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The reused predecessor guard `/tmp/kix-shared-no-sockets/sitecustomize.py` is:

```python
import sys
def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by local console verification guard: ' + event)
sys.addaudithook(deny_socket)
```

New real-child tests and transcript probes inherit this environment. Legacy
probes replacing their child environment are outside the child-guard claim.
The broad BRA runner asserts unique discovered IDs and excludes exactly the
existing HTTP socket test, using the predecessor's documented pattern:

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

This runner was saved as `/tmp/kix-fulfillment-offline.py`. Its result is filtered
coverage; no unfiltered BRA suite pass is claimed.

Foreground runner `/tmp/kix-fulfillment-run.py` executes each argv in the narrow,
suites, checks and rust JSON command sets, sequentially within each set, captures
actual output/exit and writes `/tmp/kix-fulfillment-NAME.json.results.json`.
It does not retry. Separate independent verification sets may run concurrently.
Transcript runner `/tmp/kix-fulfillment-transcripts.py` supplies each checked-in
answer file as stdin and saves stdout and actual exit/error/envelope counts.
These temporary harnesses/logs are outside the repository.

The initial focused run of
`python3.12 -B -m unittest test_booking_console test_resale_console test_admission_console test_shared_ticket_console`
failed: **74 tests, 7 errors**. The test harness parsed JSON diagnostics together
with a following child-exit line (six errors), and direct adapter parity did not
catch target-domain key conflicts (one error). Parsing the diagnostic's first
line and catching the existing domain exception set corrected these test-only
gaps. The same command then **passed 74 tests**. No service error semantics were
changed to satisfy tests.

## Actual command results

| Command actually executed (argv) | Actual result |
|---|---|
| `python3.12 -B -m unittest test_booking_console test_resale_console test_admission_console test_shared_ticket_console test_settlement_console test_ticket_operations_client test_ticket_operations_session test_ticket_operations_cli test_ticket_fulfillment test_ticket_issued_handoff test_issued_ticket_adapter` | PASS: 163 tests, exit 0 |
| `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, exit 0 |
| `python3.12 -B /tmp/kix-fulfillment-offline.py` | PASS: 837 tests, exit 0; one named HTTP test excluded; unique IDs asserted |
| `python3.12 -B scripts/check_docs_index.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_docs_index.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_status_register.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_status_register.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_bra_evidence_map.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_bra_evidence_map.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_settlement_evidence_map.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_settlement_evidence_map.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_contract_error_codes.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_contract_error_codes.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_ci_checker_wiring.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_ci_test_discovery.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_ci_test_discovery.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_openapi_contract.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_openapi_contract.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_integration_gate_openapi.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/verify_runtime_architecture.py` | PASS: exit 0 |
| `python3.12 -B scripts/test_runtime_architecture.py` | PASS: 7 tests, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: exit 101; offline cache missing `bcs`, before compilation |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101; offline cache missing `bcs`, before compilation |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0 |

Rust commands used provisioned toolchain 1.98.1 and its existing offline cache:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:$PATH"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-fulfillment-target
export CARGO_NET_OFFLINE=true
```

Tests and Clippy both returned `no matching package named bcs found`, required
by workspace member `kix-bcs1`. Neither reached compilation. These are unavailable
verification, never passes. No download, dependency change, lockfile change or
CI edit was attempted. Formatting and architecture checks passed; offline Rust
execution remains a supervisor/CI gate.

Transcript commands below show the exact argv with the stdin file supplied by
the runner (equivalent shell redirection). Their stdout remains in `/tmp`.

| Command / stdin | Actual result |
|---|---|
| `python3.12 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_fulfillment.txt` | Expected exit 0; 11 desk envelopes; stderr empty; stdout `/tmp/kix-fulfillment-transcript.txt` |
| `python3.12 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_fulfillment_consume.txt` | Expected exit 0; 22 desk envelopes; stderr empty; stdout `/tmp/kix-fulfillment-transcript_consume.txt` |
| `python3.12 -B reference/booking_resale_admission/shared_ticket_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/shared_ticket_console_fulfillment_boundaries.txt` | Expected exit 1; 25 desk envelopes; `Child exit status=1`; stdout `/tmp/kix-fulfillment-transcript_boundaries.txt` |

## Preservation and final local checks

Pre-edit `/tmp/kix-fulfillment-before.json` contains SHA-256 snapshots of all
1,365 initially tracked paths. The final preservation helper compares every
tracked path, enforces the exact 13-path output allowlist (including untracked
new files), verifies unchanged refs/branch and both locked Git blobs, parses
changed Python ASTs and runs `git diff --check`.

| Locked path | Required and observed Git blob, before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

All 1,356 initially tracked paths outside the nine edited paths are
byte-identical. Four new files complete the allowlist. This includes all
`reference/v0.3-rc1/**` bytes (Git tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`), `.aiops/`, `docs/tasks/`, contracts,
FSMs, services, adapters, client, SDK/catalogue, CI and runtime configuration.
No protected file was edited, regenerated, reformatted or transiently mutated
by the builder. No product policy or new protocol command was needed.

| Additional command | Actual result |
|---|---|
| `git status --short` (initial) | Clean expected task branch |
| `git branch --show-current` | `agent/kix-plan-local-fulfillment-console` |
| `git rev-parse HEAD origin/main` | Both cached refs `3bfba955888f8aac53bb7188ece8b34370b60db9` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before edits) | Both required blobs matched |
| `python3.12 -B /tmp/kix-fulfillment-preserve.py` | PASS: 1,356 unchanged tracked paths, 13 allowed outputs, both required blobs and protected historical bytes unchanged; ASTs parse, refs unchanged, diff clean |
| `python3.12 -B scripts/check_docs_index.py` (after completed evidence record) | PASS: exit 0; scanned=357, indexed=322, allowlisted=35 |

## Complete changed-path list

- `reference/booking_resale_admission/booking_console.py`
- `reference/booking_resale_admission/resale_console.py`
- `reference/booking_resale_admission/admission_console.py`
- `reference/booking_resale_admission/test_booking_console.py`
- `reference/booking_resale_admission/test_resale_console.py`
- `reference/booking_resale_admission/test_admission_console.py`
- `reference/booking_resale_admission/test_shared_ticket_console.py`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_fulfillment.txt`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_fulfillment_consume.txt`
- `reference/booking_resale_admission/fixtures/shared_ticket_console_fulfillment_boundaries.txt`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-05-plan-local-fulfillment-console/README.md`

## Deviations, uncertainties and delivery gates

The design was followed. The explicit Python 3.12 executable replaces this
host's 3.13 `python3`; the underlying runtime is the planned Python version.
Resale's existing nullable listing reservation prompt is scoped to listing so
adoption takes the planned required plain identifier. No semantic change or new
dependency was needed. Fetch/publication/hosted CI were omitted under the
supervisor rule; no commit, push, PR, issue, comment, marker, merge, branch/tag
mutation or network action was performed. Remote main freshness is unverified.
The broad suite excludes only the named HTTP test. Rust tests/Clippy are
unavailable due to the existing offline cache. No STOP condition was encountered
and no DECISION_REQUIRED file was needed.

No explicit contract violation was found. No new contract-undefined behavior was
defined. Historical receipts and independently current views match existing
services; later target state never changes the first receipt. Existing open
payment-handoff, policy, legal, admission timing/identity, distribution and
credential-reissuance questions remain with their existing owners. Product
policy remains **UNDETERMINED — Astra/User** and legal effects
**UNDETERMINED — User/legal**; settlement accounting/legal effects remain
**UNDETERMINED — User/designated advisers**. No capability grade, runtime
activation, false finality/durability flag or policy owner was changed.

| Required delivery evidence | State |
|---|---|
| Task ID / task document | `plan-local-fulfillment-console`; immutable conversation input, no task file/issue exists |
| Observed cached main / base / implementation HEAD | `3bfba955888f8aac53bb7188ece8b34370b60db9` |
| Exact final committed task head | Not created: uncommitted patch on the above HEAD; supervisor owns commit/publication |
| Non-author A2 exact-head review | Pending supervisor publication; these builder tests do not satisfy it |
| Exact-head KTX CI run ID/status/conclusion | Not run; no run ID/status/conclusion available |
| Exact-head KIX protocol CI run ID/status/conclusion | Not run; no run ID/status/conclusion available |
| Merge SHA / locked blobs on merge / post-merge main CI | Not applicable: no merge authorized/performed |

`READY` means the authorized builder patch and available local checks are
complete. It is not `merge-ready` under AGENTS.md §10: fresh non-author A2 review,
exact committed-head KTX/KIX CI, unavailable Rust execution and any later
post-merge checks remain supervisor gates. Record eventual final-head CI outside
repository commits to avoid self-reference loops.

These local synthetic tests do not establish production readiness, real-money
or provider/bank/KYC behavior, legal compliance, chain authority/finality,
durability, distributed fencing or external exactly-once. No unfiltered HTTP
suite, Move, storage, localnet, TypeScript or ZK verification is claimed. The
fixture's recorded payment is not payment-provider execution, adoption is not
credential reissuance, and replay is not new authority to consume. Follow-up
candidates are the pending external review/CI/cache checks and separately
authorized owner decisions; no further implementation was begun in this session.
