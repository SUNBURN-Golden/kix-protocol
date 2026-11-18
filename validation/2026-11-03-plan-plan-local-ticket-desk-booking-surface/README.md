# Shared local ticket desk booking surface — builder evidence

Task: `plan-plan-local-ticket-desk-booking-surface`. The immutable input is the
supervisor's node specification and design in this session; no issue or task
file under `docs/tasks/` exists. This is not ASTRA program mode.
Branch: `agent/kix-plan-plan-local-ticket-desk-booking-surface`.
Initial HEAD/base/cached `origin/main`: `77c93e06e4d71f02669fce2009022f2b7111302e`.
No local base delta. The supervisor prohibits network actions, overriding the
§1 fetch requirement; remote freshness is unverified. No history change occurs.

## Pre-change coverage mapping

Recorded before adding tests; paths are relative to
`reference/booking_resale_admission/`.

| Requirement | Existing evidence / classification | Gap to cover |
|---|---|---|
| Three shared surfaces, fresh graph and publish after setup | Partial: `test_ticket_operations_session.TicketOperationsSessionTests.test_one_shared_graph_per_construction_and_custom_inputs`, `test_constructor_rejects_structure_before_graph_and_domain_failure_before_publish` | Booking instance identity, constructor purity, failure publication |
| Issued-slot refusal, second-slot lifecycle | Sufficient FSM coverage: `test_reservation_fsm.ReservationFsmTests.test_overlapping_holds_and_replay_do_not_double_book`, `test_cancel_before_payment_frees_and_payment_blocks_compensation`; shared booking not covered | New shared transcript; session/CLI/direct graph parity after each line |
| Booking observes admission | Sufficient FSM evidence: `test_admission_fsm.AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`; shared booking not covered | Booking views ISSUED → ADMISSION_AUTHORIZED → CONSUMED, version and occupied slot |
| Historical receipts/current views, retained refusals and conflicts | Partial: `test_booking_session.BookingSessionTests.test_reconciliation_matches_direct_fsm_and_preserves_business_state`, shared reconciliation/history tests | Shared booking confirmation/reconcile replay, argument/subject/cross-operation/setup/delegated key conflicts |
| Explicit clock and quote prerequisites | Sufficient standalone: `test_booking_session.BookingSessionTests.test_clock_requires_success_through_this_session_and_local_failure_binds_no_key`, `test_quote_mandatory_valid_identifier_and_rejection_does_not_bind_key`; shared boundary partial | Fixture clocks insufficient, failed/replayed initialization and no bound key on local refusal |
| Strict schemas, exits and programming errors | Partial: selector/schema matrices in `test_ticket_operations_cli.py`; standalone `test_booking_cli.py` | All nine booking selectors, duplicate/nonfinite JSON, stopping BookingInputError precedence |
| Mock flags, source calls, existing resale/admission journeys | Sufficient old journeys: shared session per-line direct parity and three CLI transcripts; booking route partial | Reservation flag helper; zero booking recording fetches; preserve old transcript bytes |
| File/stdin transcripts, discovery and documentation | New journeys not covered | Two executable transcripts, unchanged discovery/HTTP coverage, indexed validation |

Both locked blobs matched before editing:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.
Protected tree listing saved to `/tmp/ticket-booking-protected-before.txt`.
Contract: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` §§1, 3, 5, 9–11.
Evidence is source-informed and builder-authored, not independent review.

## Implementation and acceptance evidence

`TicketOperationsSession.booking` wraps the reservation machine already used by
resale and admission. It is constructed only after successful setup, with no
FSM operation or source fetch. Graph identity tests cover all three surfaces,
the single settlement source, one construction per FSM, fresh graphs and
unchanged source identities. A publication-only guard rejects any public FSM
call during BookingSession construction; required fixture adoption queries are
outside that guard. Setup failures publish none of the three sessions.

`ticket_operations_cli.py` routes `surface: booking` through the unchanged
`booking_cli.dispatch_request`. The exact nine selectors, required arguments,
quote validation and explicit session clock prerequisite are reused unchanged.
`BookingInputError` joins stopping local-input errors (exit 2); domain refusals
retain `{code}` and continue only through supplied lines (exit 1). Existing
0/1/2 behavior, prior accepted effects and unexpected exception propagation are
preserved. Fixture structure and setup requirements are unchanged. The booking
surface adds no payment, issuance, settlement, organizer lifecycle operation, new query or
protocol command.

Two new transcripts run on the original two-slot issued-ticket fixture:

| File under `fixtures/` | Observable evidence |
|---|---|
| `ticket_operations_booking.jsonl` | 21 requests: no-clock views; explicit replayed fixture clock; occupied issued-slot refusal and its retained replay; changed-argument conflict; second-slot hold/confirm/cancel; historical confirmation/reconciliation versus current CANCELLED and FREE slot; changed-subject/cross-operation/setup-key conflicts; missing-reservation refusal retained across replay and conflicting subject |
| `ticket_operations_booking_admission.jsonl` | 13 requests: no-clock booking views and reconciliation; explicit admission authorize/consume on original ticket; ISSUED → ADMISSION_AUTHORIZED → CONSUMED, right version 1 → 2, slot remains ISSUED; historical reconciliation stays ISSUED while fresh receipts reflect each phase; delegated admission keys conflict in the shared reservation namespace |

The shared session parity test now covers both new transcripts, comparing raw
session calls, CLI routing and an independently constructed direct FSM graph
after every line. It compares receipts/errors, canonical state, digests and
accepted journals for all four machines. Existing flag helpers check unchanged
reservation/resale/admission mock flags. Source-call histories prove booking
adds no recording fetches. The existing reconciliation helper checks unchanged
business snapshots around success/refusal/replay/conflict; process-local
receipt/rejection bookkeeping still exists. Explicit journey assertions check
historical first results (`duplicate: true`, `applied: null`), current views,
slot states and null payment/issuance/settlement/right fields on the second
reservation. A renamed copy of the existing standalone boundary journey also
exercises registration/release through the shared graph and verifies that
booking leaves settlement, resale and admission unchanged.

The shared selector/schema matrices now include all nine booking operations.
They reject missing/extra arguments and excluded FSM operations before effects
or source access. Booking-specific duplicate JSON fields, nonfinite constants
and exponent overflow are rejected. Prerequisite tests guard each FSM mutation
to prove a missing clock never reaches the FSM or binds a key; a failed clock
cannot initialize the session, a successful replay can, and views/reconciliation
need none. Invalid quote errors override earlier domain refusals, stop the stream,
preserve prior holds and permit a later valid confirmation using the same key.
Unexpected dispatcher exceptions propagate. Both transcripts are tested through
file and stdin subprocesses, matching every output row and expected exit 1.
Existing resale/admission/payment/reconciliation journeys remain covered and
all preexisting fixture bytes remain unchanged.

## Commands actually run and results

All jobs ran in the foreground. No network, Git/GitHub mutation, publication,
commit, automatic retry, background job, external service or socket was used.
Diagnosed test corrections and toolchain/cache discovery justified reruns.
Python verification used the following environment, inherited by new transcript
children:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-booking-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean, expected branch; HEAD/base/cached origin/main all `77c93e06e4d71f02669fce2009022f2b7111302e`; no remote freshness claim |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before and after: exact required blobs listed above |
| `git ls-tree -r HEAD reference/v0.3-rc1 .aiops docs/tasks > /tmp/ticket-booking-protected-before.txt` | Initial tree listing retained and matched after work |
| `python3 -m unittest test_ticket_operations_session test_ticket_operations_cli` | First: 25 tests, four assertion/setup failures; corrected as below. Second: 25 PASS in 3.976 s. Added existing-selector shared journey: 26 PASS in 4.080 s. Final import/format cleanup: 26 PASS in 7.281 s |
| `python3 -m unittest test_booking_session test_booking_cli test_resale_session test_resale_cli test_admission_session test_admission_cli` | PASS: 73 tests, 4.610 s |
| `python3 /tmp/kix-booking-offline.py` | PASS: 568 tests, 18.332 s; exact single HTTP exclusion asserted once, detailed below; not a full-suite pass |
| `python3 /tmp/kix-booking-transcripts.py` | PASS: four foreground CLI invocations (two files × file/stdin), expected exit 1, 21/13 rows respectively; file/stdin outputs identical |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.217 s |
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.177 s |
| `python3 /tmp/kix-booking-final-check.py` | PASS: exactly nine allowed changed paths; AST/JSONL/whitespace checks; all 254 protected working blobs match HEAD; all preexisting fixtures unchanged; initial HEAD/cached origin/main and branch unchanged |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github sdk reference/v0.3-rc1` (also in final script) | PASS: no changes |
| `git diff --check` | PASS |
| Final `python3 scripts/check_docs_index.py`, `check_ci_test_discovery.py`, `check_ci_checker_wiring.py`, `check_bra_evidence_map.py`, `check_contract_error_codes.py`, `check_openapi_contract.py`, `check_integration_gate_openapi.py` (each under `scripts/`) | PASS after completing this evidence record |
| `git rev-parse HEAD:reference/v0.3-rc1` (also in final script) | Preserved tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

The first failures were test assumptions: show slots contain records, not bare
state strings, and fixture adoption legitimately reads reservation views. The
corrected test checks each slot's `state` and guards only BookingSession
publication. Per-line session/CLI/direct FSM parity passed throughout; no FSM or
contract fix was needed. Counts overlap and must not be summed.

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. Each checker
below ran plainly and with `--self-test` in a sequential foreground subprocess
loop (`python3 /tmp/kix-booking-checks.py`), checking every exit status:

| Command (`python3 scripts/<name>.py`) | Plain | `--self-test` |
|---|---|---|
| `check_docs_index` | PASS: scanned 334, indexed 299, allowlisted 35 | PASS |
| `check_ci_test_discovery` | PASS: seven reference suites, including all 31 booking test modules; unchanged workflow discovery | PASS: 18 negative controls |
| `check_ci_checker_wiring` | PASS: 35 checker scripts | PASS: 13 negative controls |
| `check_bra_evidence_map` | PASS: 39 rows, grades unchanged | PASS: 50 negative controls |
| `check_contract_error_codes` | PASS: 199 covered rows, CLASS_B=0/CLASS_C=0 in this code map | PASS |
| `check_openapi_contract` | PASS: 84 commands, unchanged pin | PASS |
| `check_integration_gate_openapi` | PASS: 84 commands, productionEndpoint/publicHost false | PASS |

The map's zero Class B/C count does not erase preexisting behavioral Class B
characterizations elsewhere.

Rust checks initially used installed system 1.85.1 tools with
`PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true CARGO_HOME=/tmp/kix-booking-cargo`.
`cargo --version` and `rustc --version` succeeded. Both test commands exited 101
because that isolated cache lacked `serde`; Clippy/fmt exited 101 because the
system components were absent. These were prerequisite failures, not passes.
Read-only cache/tool inspection found installed 1.98.1 and a 53 MB registry.
Copied existing registry bytes into the isolated `/tmp/kix-booking-cargo/registry`
without downloading anything, then executed the same commands with:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_NET_OFFLINE=true
export CARGO_HOME=/tmp/kix-booking-cargo
export CARGO_TARGET_DIR=/tmp/kix-booking-target
```

Actual CI-version results (`python3 /tmp/kix-booking-cached-rust-checks.py`):

| Command | Result |
|---|---|
| `cargo --version`; `rustc --version` | Both 1.98.1, matching workflow version |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable: exit 101, cached `bcs` missing; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable: exit 101, cached `bcs` missing; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable: exit 101, cached `bcs` missing; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

No Rust file changed. Offline prerequisites were not installed or fetched.

## Reproduce the exact socket-denied selection

The recipe reuses the prior reconciliation record's selection, changing only
the temporary path. Create `/tmp/kix-booking-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

Create `/tmp/kix-booking-offline.py`, then run it with the Python environment
above:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path('reference/booking_resale_admission').resolve()))
excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'

def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test

suite = unittest.defaultTestLoader.discover('reference/booking_resale_admission',
                                           top_level_dir='reference/booking_resale_admission')
tests = list(flatten(suite))
assert sum(test.id() == excluded for test in tests) == 1
print('Explicit socket-dependent exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(
    test for test in tests if test.id() != excluded))
sys.exit(not result.wasSuccessful())
```

All new transcript child processes inherit the socket guard. Some unchanged
import-only probes replace PYTHONPATH; their guard inheritance is not claimed.
The excluded HTTP test and `integration_gate.test_http_gate` are unchanged and
remain required for normal CI. Neither ran locally. This selection is not full
CI or a full-suite pass. Full HTTP coverage is preserved.

The four direct transcript commands were the documented commands with
`--requests fixtures/ticket_operations_booking.jsonl` and
`--requests fixtures/ticket_operations_booking_admission.jsonl` (full repository
paths), plus `--requests -` supplied each same file's text on stdin, always with
`--fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json`.
The foreground runner asserted expected exit 1 and identical file/stdin output.

The final preservation script enumerates changed and untracked paths against
the exact allowlist below, parses new Python/JSONL, checks whitespace, compares
initial protected tree listings, and independently hashes working bytes as Git
blobs throughout `runtime`, `.aiops`, `docs/tasks`, `docs/contracts`, `.github`,
`sdk` and `reference/v0.3-rc1` against HEAD. It separately hashes every preexisting
booking fixture and verifies both required lock hashes and initial refs.

## Complete changed-path list

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_booking.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_booking_admission.jsonl`
- `validation/2026-11-03-plan-plan-local-ticket-desk-booking-surface/README.md`

## Contract classification, deviations and delivery gates

Class A: exercised reservation/admission transitions, immutable first receipts,
current views, retained refusals and key conflicts match unchanged contracts.
No explicit contract violation was found. No new undefined behavior or policy
was introduced. Existing Class B clock-skew partial effects and post-restore
response distinctions remain unchanged; no cross-machine rollback is claimed.
Reconciliation's unchanged business state does not mean no process-local key
bookkeeping. Shared keys and clocks are intentionally neither namespaced nor
synchronized, and no retry, automatic transition or recovery is added.

Deviations: the supervisor's network prohibition prevented §1 fetch; no task
issue/document exists or was created; local verification excludes exactly the
HTTP test named above; Rust test/Clippy prerequisites remain unavailable offline.
The constructor purity guard was narrowed to publication because fixture setup
requires source queries. Existing boundary/reconciliation helpers and the
standalone selector journey were reused to cover gaps without duplicate FSM
tests. No STOP dependency, new command or consequential expansion arose.

B02/B05/P03 capability grades remain unchanged. Product timing and authority
remain **UNDETERMINED — Astra/User**; legal effects remain
**UNDETERMINED — User/legal**. Other contract owners remain unchanged. This is
source-informed builder evidence, not clean-room verification or non-author
review. No real funds, external authority, live PG/bank/KYC, production endpoint,
Sui execution, new storage engine, persistence, runtime activation, policy
default, production durability, bank/venue exactly-once, chain finality, legal
compliance or production readiness is claimed.

The patch is uncommitted by instruction. HEAD remains
`77c93e06e4d71f02669fce2009022f2b7111302e` and does not contain these changes.
Implementation/final task head is for the supervisor to assign. Exact-head KTX
and KIX run IDs/status/conclusions are **unavailable/pending**, not successful.
Non-author A2 exact-head review remains pending. Before merge require that
review, both workflows completed/success at the supervisor's exact final head
(including normal HTTP coverage), and separate User publication/merge authority.
No PR, issue, comment, ASTRA marker or merge was created. Merge SHA/final-merge
lock verification/post-merge main CI are not applicable. Builder READY denotes
local handoff only and is not merge-ready. Missing offline Rust prerequisites
and unrun HTTP coverage remain supervisor verification items.
