# Local ticket desk reconciliation — builder evidence

Task: `plan-local-ticket-desk-reconciliation`. Immutable task input is the
supervisor's node specification and design in this session; no issue or
node-specific `docs/tasks/` document exists. This is not ASTRA program mode.
Branch: `agent/kix-plan-local-ticket-desk-reconciliation`. Initial HEAD, base and
cached `origin/main`: `07d0d44bb803b52defede21c311a1298d351a68a`.
The supervisor prohibits network actions, so §1 fetch was not run and remote
freshness is unverified. No local base delta; no base/history changes authorized.

## Coverage mapping before new tests

Paths below are relative to `reference/booking_resale_admission/`.

| Requirement | Existing coverage / classification | Boundary gap |
|---|---|---|
| FSM reconciliation and restore | Sufficient: `test_reservation_fsm.ReservationFsmTests.test_external_attempts_do_not_journal_and_resale_is_absent`, `test_resale_fsm.ResaleFsmTests.test_external_attempts_do_not_journal`, `test_admission_fsm.AdmissionFsmTests.test_restart_replays_journal_and_retry_is_duplicate`; restore/rejection cases in all three FSM suites | Reuse; no FSM changes |
| Restore fingerprints | Sufficient characterization: `test_restore_fingerprint_equivalence.py` | Preserve existing undefined post-restore response distinctions |
| Forward original identity/key exactly once, unchanged receipt/error | Partial: forwarding matrices in all three session suites and selector checks in CLI suites cover existing operations | Add reconcile rows; zero source fetch, opaque inputs and exception identity |
| Successful desk reconciliation, historical replay/current view, conflicts | Not covered at desk boundary; FSM first-result coverage sufficient | Independent direct controls, explicit later transitions, retained refusals, changed-subject and cross-operation keys |
| Ownership-change refusal | Partial: `test_admission_fsm.AdmissionFsmTests.test_restore_fails_closed_when_ownership_moves`, shared transfer transcript/session parity | Successful reconcile before transfer, historical replay then fresh-key `STALE_VERSION` and refusal replay |
| Journals, ticket/payment state, non-claim flags | Partial: existing desk snapshots and flag helpers | Snapshot all participating FSMs around each reconciliation success/refusal/replay/conflict; demonstrate process-local key bookkeeping |
| Strict schemas, compatible file/stdin journeys | Partial: existing desk schema matrices and old transcripts | Extend reconcile selectors, add four new transcripts without changing existing fixtures |
| Documents/discovery/CI | Existing checkers and workflow discovery | Index this record; socket-denied local evidence, preserve normal HTTP CI and pending non-author exact-head review |

Contracts: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` §§9.4, 10.7,
11.5. Preserve `docs/decisions/PROGRAM_DECISIONS_20260928.md` §5 locks.
Both locked file blobs match before edits:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.

This record is source-informed builder evidence, not independent review.
Execution results and delivery limits are recorded below after verification.

## Implementation and acceptance evidence

`booking_session.py`, `resale_session.py` and `admission_session.py` each add one
method returning exactly `self._machine.reconcile(subject, idempotency_key=key)`.
The corresponding strict dispatch tables add only that existing operation,
with the subject identity and caller key required, returning `receipt`.
Shared session/CLI implementation needs no edit: existing composition exposes
both nested methods and routes through the extended dispatch tables.
No FSM, fixture schema, protocol command, catalogue or HTTP surface changed.

The session forwarding matrices now include reconciliation. Dedicated opaque
identity/key cases prove no normalization, exactly one invocation, original
return-object and exception identity (including unexpected exceptions), and
zero presentation/offer/payment source access. Booking also tests reconciliation
on a caller-supplied machine without session clock initialization, while its
existing business clock prerequisite still holds.

Each session suite adds real-FSM parity over a new transcript. The shared
session suite additionally compares session calls and CLI routing with an
independently constructed graph after every line. `check_reconcile_history`
compares receipts/errors, canonical states, digests and accepted journals;
all participating machines are snapshotted immediately before/after every
reconcile success, replay, refusal and conflict. Fresh receipt digest/entry count
match the current machine; historical receipts preserve their original fields.
The tests deliberately observe process-local bookkeeping through replay and
changed-subject/cross-operation/rejected-key conflicts; unchanged business
snapshots do not imply a read-only operation.

`check_reconcile_cli` is reused by the four CLI suites. It checks direct-FSM
parity after each request, exact desk-to-FSM argument forwarding and one call,
zero recording fetches during reconciliation, unchanged graph snapshots, and
file/stdin subprocess output and exit status. Existing strict schema matrices
now include reconcile and reject missing/extra fields before dispatch. Existing
transcripts remain byte-unchanged; existing source/fixture/desk tests are reused.

New journeys:

| Transcript | Evidence |
|---|---|
| `booking_reconcile.jsonl` | Confirmed reconciliation, explicit cancellation, historical replay versus current CANCELLED, fresh reconciliation, cross-operation/subject conflicts, missing-subject refusal replay, retained failed-key conflict and malformed identity/key |
| `resale_reconcile.jsonl` | LISTED reconciliation, explicit hold/payment/binding/transfer/close, historical replay versus current CLOSED, fresh reconciliation and the same conflict/refusal/shape boundaries |
| `admission_reconcile.jsonl` | AUTHORIZED reconciliation, separate explicit consume, historical replay versus current CONSUMED, fresh reconciliation and the same conflict/refusal/shape boundaries |
| `ticket_operations_reconcile.jsonl` | Explicit authorization and successful reconciliation, explicit expiry clock advance, resale list/reconcile/payment/bind/transfer/close; old admission reconciliation key still succeeds historically, fresh key and failed-key replay both preserve STALE_VERSION, resale historical/current differences and unreissued credential refusal |

All four transcripts intentionally exit 1 because they include explicit domain
refusals. File and stdin outputs match direct controls. False flags and MOCK
provenance remain checked using each FSM's existing flag helper.

## Actual commands and results

All work and tests ran in the foreground with installed tools. No network,
publication, commit, background job or automatic retry was used. After a failed
test, changes addressed the diagnosed test setup and the narrow suite was rerun.
All verification Python commands use `PYTHONDONTWRITEBYTECODE=1`; narrow and
broader tests and document/architecture checks use:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-reconcile-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD refs/remotes/origin/main` | Initially clean, expected task branch, both SHAs equal `07d0d44bb803b52defede21c311a1298d351a68a`; no refreshed remote observation |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before/after: required `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git ls-tree -r HEAD reference/v0.3-rc1 .aiops docs/tasks > /tmp/ticket-reconcile-protected-before.txt` | Pre-work tree listing retained and matched at final verification |
| `python3 -m unittest test_booking_session test_booking_cli test_resale_session test_resale_cli test_admission_session test_admission_cli test_ticket_operations_session test_ticket_operations_cli` | First run: 94 tests, 8 subtest errors and 2 failures from test setup; corrected as described below. Second run: PASS, 94 tests, 9.722 s |
| `python3 /tmp/kix-reconcile-offline.py` | PASS, 563 tests, 30.614 s; exactly one asserted socket-dependent HTTP exclusion |
| `python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo --version`; `rustc --version` under system environment below | Both 1.85.1; no installation/download |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable, exit 101: cached crates.io `serde` missing; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable, exit 101: cached `serde` missing; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable, exit 101: no system Cargo `clippy` command |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Unavailable, exit 101: no system Cargo `fmt` command |
| `git diff --check` | Initial formatting check found one extra EOF blank line in `test_admission_cli.py`; removed. Final check PASS |
| `python3 /tmp/kix-reconcile-final-check.py` | PASS: exactly 21 allowed changed paths; Python AST/JSONL/trailing whitespace checks; all 110 protected working-file Git blobs byte-identical; pre-work tree listing and initial HEAD/cached origin/main unchanged |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github reference/v0.3-rc1 sdk` (also in final script) | PASS, no changes |
| `git rev-parse HEAD:reference/v0.3-rc1` | Preserved tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

Rust commands used
`PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true CARGO_HOME=/tmp/kix-reconcile-cargo`
to avoid rustup or dependency downloads. These installed system tools differ
from CI's 1.98.1 toolchain. Prerequisite failures are not passes; no Rust files
changed. Counts overlap and must not be added together.

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. The following
commands each ran normally and with `--self-test` in a sequential foreground
subprocess loop that checked every exit status:

| Command (`python3 scripts/<name>.py`) | Plain | `--self-test` |
|---|---|---|
| `check_docs_index` | PASS: scanned 333, indexed 298, allowlisted 35 | PASS |
| `check_ci_test_discovery` | PASS: all 31 booking test files reached by unchanged workflow discovery | PASS, 18 negative controls |
| `check_ci_checker_wiring` | PASS: 35 checker scripts | PASS, 13 negative controls |
| `check_bra_evidence_map` | PASS: 39 rows; grades unchanged | PASS, 50 negative controls |
| `check_contract_error_codes` | PASS: 199 covered rows, no Class B/C additions | PASS |
| `check_openapi_contract` | PASS: 84 commands, unchanged pin | PASS |
| `check_integration_gate_openapi` | PASS: 84 commands, productionEndpoint/publicHost false | PASS |

The first narrow run used the resale flag helper on booking receipts (which
lack resale-only `venue_credential_reissued`), and attempted the ownership-refusal
journey with only adoption in admission's history. The corrected test uses the
booking flag helper and an explicit prior authorization plus expiry, matching
`test_restore_fails_closed_when_ownership_moves`. Direct-FSM parity itself was
preserved. No implementation/FSM fix or policy choice was needed.

## Reproduce the socket-denied selection

Create `/tmp/kix-reconcile-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {"socket.__new__", "socket.connect", "socket.bind", "socket.getaddrinfo"}:
        raise AssertionError("socket use forbidden in offline verification: " + event)

sys.addaudithook(deny_sockets)
```

Create `/tmp/kix-reconcile-offline.py` and run it using the exported environment
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

Every new transcript subprocess inherits the guard via PYTHONPATH. Some unchanged
import-only child probes set their own PYTHONPATH; their guard inheritance is not
claimed. The excluded HTTP test and `integration_gate.test_http_gate` are
unchanged and remain required in normal CI. They were not run locally; this
socket-free selection is not full CI or a full-suite pass.

The final read-only path check enumerated changed/untracked paths, required the
21-path set below, parsed changed Python and JSONL, checked whitespace and hashed
working bytes as Git blobs against `git ls-tree -rz HEAD` for both locked files
and `reference/v0.3-rc1`. It also compared the initial protected tree listing,
checked forbidden trees with `git diff --exit-code` and verified initial refs.

## Complete changed-path list

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/admission_cli.py`
- `reference/booking_resale_admission/admission_session.py`
- `reference/booking_resale_admission/booking_cli.py`
- `reference/booking_resale_admission/booking_session.py`
- `reference/booking_resale_admission/fixtures/admission_reconcile.jsonl`
- `reference/booking_resale_admission/fixtures/booking_reconcile.jsonl`
- `reference/booking_resale_admission/fixtures/resale_reconcile.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_reconcile.jsonl`
- `reference/booking_resale_admission/resale_cli.py`
- `reference/booking_resale_admission/resale_session.py`
- `reference/booking_resale_admission/test_admission_cli.py`
- `reference/booking_resale_admission/test_admission_session.py`
- `reference/booking_resale_admission/test_booking_cli.py`
- `reference/booking_resale_admission/test_booking_session.py`
- `reference/booking_resale_admission/test_resale_cli.py`
- `reference/booking_resale_admission/test_resale_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `validation/2026-11-03-plan-local-ticket-desk-reconciliation/README.md`

## Contract classification, deviations and delivery limits

Class A: unchanged FSM reconciliation/idempotency behavior and the exercised
source-check refusal path match the contracts. No explicit contract violation
was found. `matched` compares local replayed state; the ownership-refusal test
requires a journaled authorization that rechecks ownership during replay. An
adoption-only history did not produce that refusal, so the journey includes the
existing authorization/expiry prerequisites rather than inventing new checks.
This is a test-fixture clarification to the design, not a new currentness rule.
Existing Class B post-restore response distinctions and clock-skew partial-effect
characterizations remain unchanged; no new contract semantics are adopted.

Deviations: no fetch under the supervisor's explicit network prohibition; no
repository task document exists or was created; one socket-dependent test is
excluded only from local execution; Rust prerequisites are unavailable offline.
Shared test assertions are reused in existing test modules to avoid duplication.
The shared refusal journey explicitly supplies authorization/expiry as above.
No STOP dependency, new protocol command or consequential scope expansion arose.

P03, R01–R05 and P06 retain their status. Currentness, operational policy and
retention values remain UNDETERMINED with their existing Astra/User and contract
owners; provider/funds/merchant/legal/accounting owners are unchanged. No repair,
reissuance, automatic transition, payment lookup, retry, durable recovery,
authenticated audit, external authority, funds execution, production durability,
bank exactly-once, chain finality, legal compliance or production readiness is
claimed. Evidence is source-informed and builder-authored, not independent.

Delivery is uncommitted. HEAD remains `07d0d44bb803b52defede21c311a1298d351a68a`;
it does not contain this patch. Implementation/final task head will be assigned
by the supervisor. Exact-final-head KTX and KIX run IDs/status/conclusions are
unavailable, not green. Non-author exact-head A2 review remains pending. No merge
occurred: merge SHA, final-merge lock checks and post-merge main CI are not
applicable. Before merge, require the non-author review and both exact-head
workflows completed/success, including normal HTTP coverage. Builder READY means
local delivery only, not merge-ready. All Git/GitHub publication stays with the
supervisor; nothing was posted and no ASTRA marker was emitted.
