# Recorded resale payments in local ticket desks — builder evidence

Task: `plan-local-resale-payment-desk`; task input is the supervisor's node
specification/design in this session, no issue or node-specific docs/tasks file.
Not ASTRA program mode. Cached origin/main, base and initial HEAD all equal
`5f8e85cb4c7e8f1090f75ba5dae249bc36814187`. Fetch is prohibited by the supervisor;
remote freshness is unverified. No commit or publication is authorized.

## Coverage mapping before new tests

Paths below are in `reference/booking_resale_admission/`.

| Requirement | Classification / existing evidence | Gap to address |
|---|---|---|
| Strict synthetic payment recordings | Sufficient source coverage: `test_resale_payment_source.py`; fixture wiring not covered | Optional payment field, envelope validation before construction, opaque text |
| LISTED / BUY_HELD observation, explicit transfer | Sufficient adapter: `test_resale_payment_adapter.py::test_payment_and_replay_parity_from_listed_and_held_then_explicit_transfer`; session: `test_resale_session.py::test_recorded_payment_uses_actual_session_and_requires_separate_transfer` | CLI composition partially covered; add both desk transcripts |
| Shared graph / admission STALE_VERSION | Partial: `test_ticket_operations_session.py::test_transcripts_session_and_cli_match_direct_graph_after_every_request`, existing transfer transcript | Payment adapter graph identity and recorded-payment transcript parity |
| One fetch, replay, first-result/conflicts | Sufficient adapter/session coverage; CLI partial | Dispatch replay/alias, post-close historical results, changed record conflicts |
| Missing/malformed/mismatched/fault input | Sufficient adapter no-access and source tests; desk not covered | Structured local errors, no mutation, same-key reuse, no retry/cache |
| Direct-payment compatibility, clocks, false flags | Sufficient existing CLI/session tests and `assert_not_final` / `assert_flags` | Regression plus recorded path flags and independent-machine snapshots |
| Discovery, docs, local verification | Existing checkers | Index this evidence; socket-denied selection and subprocesses |

Source-informed regression evidence, not independent verification. Results,
changed paths and limitations are recorded below after execution.

## Implementation and new evidence

Both strict loaders accept optional `payments`; absent means no source, empty
means an empty fake source. Envelope/identity/fault validation runs before graph
construction; recorded JSON remains opaque until fetch. The shared constructor
forwards its optional source into the existing resale session on the same machine
admission reads. Both request loops handle payment-source errors, preserving
exit statuses and output envelopes. The direct-payment selector is unchanged.

`test_resale_cli.py::RecordedPaymentDeskChecks` supplies six focused checks,
executed for both CLIs by `ResaleRecordedPaymentCliTests` and
`test_ticket_operations_cli.py::TicketRecordedPaymentCliTests`. They cover strict
fixture envelopes before construction, fresh/optional sources, both payment
phases, graph identity, exact journal operation, unchanged other machines,
false flags, file/stdin transcripts, boundary errors and same-key reuse, replay
fetch faults without cache, alias replay and changed-payload conflicts,
semantic-refusal/direct-FSM parity and zero-fetch structural failures. Existing
import probes in the two touched CLI test modules now retain the inherited guard.

The independent control construction in `test_ticket_operations_session.py`
continues to bypass the combined constructor and adapters. Its `direct_call`
translates recorded observation to the existing FSM `observe_resale_payment`.
The extended shared-session test and both CLI checks compare receipts/errors,
canonical states, digests and journals after every request. Standalone controls
compare the three applicable machines; shared controls compare all four.
Wrong amount/buyer refusals, replay, same-key conflicts and fresh-key acceptance
are also compared to direct FSM calls. Existing source/adapter shape matrices
are reused rather than duplicated.

The four new JSONL transcripts demonstrate LISTED and BUY_HELD observation,
PAYMENT_NOTED with unchanged holder/version, alias replay, separate binding and
transfer, close and historical payment replay. Both shared transcripts preserve
old-holder/version-1 and unreissued-recipient/version-2 STALE_VERSION refusals.
No request implicitly transfers or admits; venue credential reissuance stays false.
Existing fixtures and transcripts are byte-unchanged and their tests pass.

## Actual commands and results

All commands ran in the foreground from repository root, using installed tools
only. Python version: 3.13.5. Counts overlap and are not additive. No test or
implementation assertion failed. All Python verification commands used
`PYTHONDONTWRITEBYTECODE=1`. Named booking tests and the broader runner used:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-payment-desk-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; expected `agent/kix-plan-local-resale-payment-desk`; both SHAs equal the base above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before and after: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git ls-tree -r HEAD reference/v0.3-rc1 > /tmp/payment-desk-protected-before.txt`; `git rev-parse HEAD:reference/v0.3-rc1` | Historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; pre-work listing retained for comparison |
| `python3 -m unittest test_resale_payment_source test_resale_payment_adapter test_resale_session test_resale_cli test_ticket_operations_session test_ticket_operations_cli` | PASS, 65 tests (initial focused pass before the additional direct-FSM CLI parity check) |
| `python3 -m unittest test_resale_payment_source test_resale_payment_adapter test_resale_offer_source test_resale_offer_adapter test_resale_session test_resale_cli test_ticket_operations_session test_ticket_operations_cli test_presentation_source test_presentation_adapter test_admission_session test_admission_cli` | PASS, 122 tests; includes socket-denied file/stdin subprocess transcripts and boundary-error streams |
| `python3 /tmp/kix-payment-desk-offline.py` | PASS, 552 tests; exactly one explicit socket-dependent HTTP exclusion, asserted to match once |
| `python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo --version`; `rustc --version` (system environment below) | Both 1.85.1; no download/install |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable, exit 101: cached crates.io `serde` missing; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable, exit 101: cached `serde` missing; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable, exit 101: no system Cargo `clippy` command |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Unavailable, exit 101: no system Cargo `fmt` command |
| `git diff --check` | PASS |
| Final read-only inline Python path whitelist, `ast.parse`, JSON/JSONL parsing, trailing-whitespace and protected-blob checks | PASS: exactly 10 tracked edits + 7 new files; 17 allowed paths, all 110 protected blobs unchanged; HEAD and cached origin/main still equal the base |
| `python3 scripts/check_docs_index.py`; `python3 scripts/check_ci_checker_wiring.py` after completing this evidence record | PASS, unchanged counts |
| Read-only Python working-file Git-blob comparison against `git ls-tree -r -z HEAD -- <two locked files> reference/v0.3-rc1` | PASS, all 110 protected blobs byte-identical; historical tree listing also matches pre-work listing |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github reference/v0.3-rc1 sdk` | PASS, no changes |

Cargo commands each used
`PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true CARGO_HOME=/tmp/kix-payment-desk-cargo`.
This chooses installed system tools without invoking rustup downloads or network
access. Prerequisite failures are not passes. No Rust implementation changed.

Inspected CI: `.github/workflows/protocol.yml` and `ktx-kernel.yml`. The selected
checker commands each ran normally and with `--self-test`, through a sequential
subprocess loop checking every exit status, under the same socket guard:

| Command (`python3 scripts/<name>.py`) | Plain | `--self-test` |
|---|---|---|
| `check_docs_index` | PASS: scanned 332, indexed 297, allowlisted 35 | PASS |
| `check_ci_test_discovery` | PASS: 31 booking test files reached by existing workflow discovery | PASS, 18 negative controls |
| `check_ci_checker_wiring` | PASS: 35 scripts | PASS, 13 negative controls |
| `check_bra_evidence_map` | PASS: 39 rows; grades unchanged | PASS, 50 negative controls |
| `check_contract_error_codes` | PASS: 199 covered rows; no Class B/C additions | PASS |
| `check_openapi_contract` | PASS: 84 commands, pin unchanged | PASS |
| `check_integration_gate_openapi` | PASS: 84 commands, productionEndpoint/publicHost false | PASS |

## Reproduce the socket-denied selection

Create `/tmp/kix-payment-desk-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {"socket.__new__", "socket.connect", "socket.bind", "socket.getaddrinfo"}:
        raise AssertionError("socket use forbidden in offline verification: " + event)

sys.addaudithook(deny_sockets)
```

The guard is inherited by all CLI transcript subprocesses. Some unchanged
import-only probes elsewhere in the existing suite set their own PYTHONPATH;
this record does not claim their child interpreters load the guard. No transcript
child overrides it. The only excluded test is unchanged:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
It requires an actual loopback socket and is outside these local checks. The
552-test selection is not a full-suite or full-CI success claim.

Create `/tmp/kix-payment-desk-offline.py`:

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

Use the exported environment above and run `python3 /tmp/kix-payment-desk-offline.py`.
The focused unittest command in the evidence table uses that same environment.
No test is weakened or skipped in repository code and no workflow is edited.

## Complete changed-path list

- `reference/booking_resale_admission/resale_fixture.py`
- `reference/booking_resale_admission/ticket_operations_fixture.py`
- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/resale_cli.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_resale_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/fixtures/resale_payment_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_payment_session.json`
- `reference/booking_resale_admission/fixtures/resale_payment_listed.jsonl`
- `reference/booking_resale_admission/fixtures/resale_payment_held.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_payment_listed.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_payment_held.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-02-plan-local-resale-payment-desk/README.md`

## Limits, deviations and pending gates

No contract violation or new contract-undefined behavior was found. Existing
clock-skew and sequential-order characterizations remain unchanged; this work
adds no synchronization or rollback semantics. All authority, funds, durability
and finality flags remain false. No provider authenticity, merchant eligibility,
payout, credential reissuance, compensation, settlement execution, reservation
handoff, HTTP binding, persistence, concurrency or production capability is
implemented or claimed. No HTTP/readiness, Move, ZK, SDK or external-provider
suite is claimed. Product values remain **UNDETERMINED — Astra/User**; provider
authority remains with User/Toss technical owners; merchant eligibility with
User/Toss sales; payout duties with existing legal/accounting/tax owners.

Deviations: no fetch under the supervisor's explicit network prohibition; no
repository task document exists or was created; broader selection excludes the
one existing socket-dependent test; ancillary Rust checks lack installed offline
prerequisites. The implementation follows the design. Shared acceptance checks
are reused between the two existing CLI test modules to avoid duplication.
No STOP dependency or consequential scope expansion was needed.

Delivery is uncommitted. Current implementation/final committed HEAD remains the
initial SHA (it does not contain this working patch); the supervisor will create
the implementation/final task head. Exact-final-head KTX kernel verification and
KIX protocol verification run IDs/status/conclusions are unavailable, not green.
Non-author exact-head A2 review remains pending. No merge occurred; merge SHA and
post-merge CI are not applicable. Builder READY means local delivery only, not
merge-ready. All git/GitHub publication remains with the supervisor.
