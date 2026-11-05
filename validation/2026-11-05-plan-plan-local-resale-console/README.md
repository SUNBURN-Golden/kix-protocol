# Guided local resale console — builder evidence

Node: `plan-plan-local-resale-console`. Immutable task input: inline supervisor
node specification and design, planner run 1793832890; no task issue or document
exists. Non-ASTRA session. Supervisor owns commits and GitHub publication.

Branch: `agent/kix-plan-plan-local-resale-console`. Initial HEAD and cached
`origin/main`: `ff913965c106a9ee806972d910d8498aa8edc37b`, no delta; clean worktree.
Fetch omitted under the explicit no-network supervisor instruction; remote
freshness is unverified. No implementation/final commit is created by this builder.

## Existing coverage mapped before adding tests

All paths in this table are under `reference/booking_resale_admission/`.

| Requirement | Classification and existing evidence | Console gap |
|---|---|---|
| Explicit listing arguments and one call | Sufficient service coverage: `test_resale_session.ResaleRequestInputsTests.test_exactly_one_call_opaque_inputs_receipt_and_exception_identity`; `test_resale_cli` request-input parity tests | Partial terminal coverage: prompts, literal confirmation and full envelopes |
| Transfer/cancellation on one child | Partial: `test_resale_session.ResaleSessionTests.test_complete_explicit_flow_and_replay_after_close`, `test_competing_listing_release_cancel_and_post_payment_error`; client `test_buffered_child_reply_before_stdin_eof_and_response_derived_journey` | Real console answer transcripts, single launch/close, output parity |
| Price and ownership refusal | Sufficient semantics: `test_resale_session.ResaleRequestInputsTests.test_request_refusals_retained_keys_and_direct_fsm_parity` | Exact console errors and no automatic correction |
| Missing payment/settlement; optional binding | Sufficient semantics: session `test_no_implicit_payment_binding_hold_or_close_and_unbound_transfer_works`; `test_resale_fsm.ResaleFsmTests.test_bound_transfer_waits_for_mock_commit_and_reconciles` | Console refusals, unknown/uncommitted settlement and explicit unbound success |
| Historical replay vs current state | Partial: request-input `test_replay_after_cancel_and_expiry_and_competing_sale_lock`; session complete flow above | Explicit repeat confirmation, receipt/view labels and separate outcomes |
| Decline; exact integer rendering | Not covered for resale console; booking renderer tested by `test_booking_console.BookingConsoleTests.test_exact_decimal_renderer_without_floats` | Decline all mutations, no floats or implicit values |
| Uncertainty, EOF, interruption, terminal I/O | Sufficient transport: client `test_malformed_truncated_mismatched_and_exited_workers_never_resend`, `test_short_write_broken_pipe_and_interruption_fence_without_remainder_write`; partial console composition in `test_booking_console` | Resale fencing before queued action, saved reply/diagnostics and cleanup |
| Offline docs/discovery | Partial: predecessor console validation and workflows | Current socket-denied regressions and indexed usage/evidence |

New tests are source-informed composition evidence, not independent review.
Underlying matrices above are reused rather than replicated.

## New evidence and coverage

All new tests are methods of `test_resale_console.ResaleConsoleTests`.

| New tests | Documented gap addressed |
|---|---|
| `test_live_transfer_transcript`, `test_live_cancel_transcript`, `test_documented_transcripts_as_cli_subprocesses` | One real child per journey, exact selector order/arguments, separate listing/payment/ownership, explicit replay/current observations, every success reply equals direct dispatch on an equivalent fixture graph |
| `test_price_and_ownership_refusals_are_exact_and_do_not_correct` | Original RESALE_CAP, NOT_HOLDER and STALE_VERSION envelopes, no automatic corrections |
| `test_missing_payment_unknown_record_and_explicit_unbound_transfer`, `test_unknown_and_uncommitted_bound_settlement_preserve_errors` | Premature transfer, exact missing-record error, unknown/uncommitted bound settlement refusals; explicit unbound success without implicit setup |
| `test_every_mutation_requires_literal_single_use_submission`, `test_invalid_inputs_never_submit_or_generate_values` | Zero submissions on decline for all nine mutations, no approval reuse, complete proposed request, decimal integers and explicit JSON reservation binding |
| `test_large_supported_integer_round_trip_and_current_ownership_rendering` | Supported 999999999999 KRW round trip and exact integer output; current version retained |
| `test_eof_interrupt_and_input_failure_stop_and_close`, `test_request_interruption_fences_before_queued_action` | EOF/read failure/interruption and interruption during approval/exchange fence submissions, no compensation and child cleanup |
| `test_terminal_envelopes_preserved_before_queued_action`, `test_real_transport_uncertainty_stops_queued_action_and_reaps_child` | Terminal replies/startup failure, real truncated invalid reply, request/reply bytes and cause retained, no retry/replacement/further queued action |
| `test_output_failure_retains_reply_and_fences_even_with_broken_diagnostics`, `test_required_arguments_cleanup_budgets_import_and_cleanup_failure` | Saved result before rendering, broken diagnostic sink, required fixture/budget, finite positive cleanup validation, import safety and cleanup failure |

The pre-existing payment-session fixture is reused unchanged; test-only fixture
variants are temporary caller-selected files, not new setup behavior. The initial
14-test run had one incorrect assertion expecting a generic payment-source error;
the actual source returns `ResalePaymentNotFound`. Corrected the assertion only.
All final console tests pass. No service semantics were changed.

## Actual local verification

All commands ran in the foreground. No shell background jobs, network actions,
GitHub actions, commits, pushes, issues, PRs or comments were performed. Temporary
runners invoke commands sequentially and do not retry. The independent broad
suite and check runners are separate foreground tool executions. Actual outputs
were retained in `/tmp/kix-resale-checks.json`, `/tmp/kix-resale-rust.json` and
the tool execution results; those files are not needed to interpret this record.

Python environment (including child CLI processes):

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-resale-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary `sitecustomize.py` guard is:

```python
import sys

def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by resale console verification guard: ' + event)

sys.addaudithook(deny_socket)
```

This guards the parent and inheriting children. Existing import probes that
replace their subprocess environments are outside the child-guard claim; new
console subprocess/import tests inherit it. No dependencies were installed.
Local Python is 3.13.5; hosted CI specifies 3.12.

For Rust commands the temporary runner explicitly used the provisioned toolchain
and predecessor cache, without downloads:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-resale-target
export CARGO_NET_OFFLINE=true
```

| Command actually run | Actual result |
|---|---|
| `git status --short` / `git rev-parse HEAD` / `git rev-parse refs/remotes/origin/main` / `git branch --show-current` | Clean initial worktree; expected branch; HEAD and cached main both ff913965c106a9ee806972d910d8498aa8edc37b; fetch prohibited |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before: required blobs match (listed below) |
| `git ls-tree -r HEAD reference/v0.3-rc1 > /tmp/resale-console-protected-before.txt` | Protected tracked tree captured before work; full tracked byte SHA-256 snapshot also saved before edits |
| `python3 --version` | 3.13.5 |
| `python3 -m unittest test_resale_console` (initial) | Exit 1: 14 tests in 2.747 s, one assertion failure on exact missing-record error type |
| `python3 -m unittest test_resale_console` (corrected, final) | PASS: 15 tests in 1.881 s; exit 0 |
| `python3 -m unittest test_booking_console test_ticket_operations_client test_resale_session test_resale_cli test_resale_fsm test_resale_offer_source test_resale_offer_adapter test_resale_payment_source test_resale_payment_adapter test_ticket_operations_session test_ticket_operations_cli` | PASS: 147 tests in 13.828 s; exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kix-resale-no-sockets python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_resale_console.py` | PASS: 15 tests in 1.902 s; exit 0; suite path provided by discovery |
| `python3 -B reference/booking_resale_admission/resale_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_payment_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/resale_console_transfer.txt > /tmp/kix-resale-transfer-output.txt` | PASS: exit 0; 13 unchanged desk envelopes, historical TRANSFERRED replay and current CLOSED view |
| `python3 -B reference/booking_resale_admission/resale_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_payment_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/resale_console_cancel.txt > /tmp/kix-resale-cancel-output.txt` | PASS: exit 0; 8 unchanged desk envelopes, historical LISTED replay and current CANCELLED view |
| `python3 scripts/check_docs_index.py` | PASS: docs index ok: scanned=352 indexed=317 allowlisted=35; exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | PASS: self-test: pass; exit 0 |
| `python3 scripts/check_ci_test_discovery.py` | PASS: ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3; exit 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS: self-test: pass (18 negative controls); exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | PASS: ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99; exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS: self-test: pass (13 negative controls); exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | PASS: bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2; exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS: self-test: pass (50 negative controls); exit 0 |
| `python3 scripts/check_contract_error_codes.py` | PASS: contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0; exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS: self-test: pass; exit 0 |
| `python3 scripts/check_openapi_contract.py` | PASS: openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff; exit 0 |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS: self-test: pass; exit 0 |
| `python3 scripts/check_integration_gate_openapi.py` | PASS: integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false; exit 0 |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS: self-test: pass; exit 0 |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: Ran 9 tests in 0.199s; OK; exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified; exit 0 |
| `python3 scripts/test_runtime_architecture.py` | PASS: Ran 7 tests in 0.182s; OK; exit 0 |
| `cargo --version` | PASS: cargo 1.98.1 (797e8a9bc 2026-08-05); exit 0 |
| `rustc --version` | PASS: rustc 1.98.1 (48a229cea 2026-09-01); exit 0 |
| `python3 scripts/check_cargo_offline_cache.py --require` | UNAVAILABLE: archives missing for 11 of 18 registry packages, including bcs 0.2.1; no download; exit 1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: no matching cached bcs for workspace kix-bcs1; test/lint body did not execute; exit 101 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: no matching cached bcs for workspace kix-bcs1; test/lint body did not execute; exit 101 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: no matching cached bcs for workspace kix-bcs1; test/lint body did not execute; exit 101 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: completed; exit 0 |
| `python3 -B /tmp/kix-resale-offline.py` | PASS: 773 tests in 70.906 s; exit 0; partial socket-denied discovery with the single exclusion below |
| `python3 -B /tmp/kix-resale-preserve.py` | PASS: 1,342 tracked files outside the seven allowed paths byte-identical; both locked blobs, historical bytes, branch and cached refs preserved; new Python ASTs parse and diff whitespace valid |
| `git diff --check` | PASS; exit 0 (also executed by preservation helper) |

The broad runner follows the [predecessor console recipe](../2026-11-05-plan-plan-local-booking-console/README.md)
with exactly this single exclusion:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
It is **partial offline booking/resale/admission discovery**, not full repository
or unfiltered discovery. Its exact executable content is reproduced here:

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

## Preservation and changed paths

Both locked blobs verified before and after work:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The preservation helper compares SHA-256 bytes against the initial snapshot of
all 1,344 tracked files. All 1,342 outside the two allowed existing documentation
files match; all new files are checked against the exact seven-path allowlist.
This includes every historical `reference/v0.3-rc1/**` file, both kernel locks,
`.aiops/**`, `docs/tasks/**`, FSMs, adapters, dispatchers, contracts, catalogue,
SDK, workflow and existing fixture bytes. It also asserts unchanged HEAD, cached
main and branch, valid new Python ASTs and `git diff --check`. Protected files
were never edited or transiently mutated.

Complete changed paths:

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/resale_console.py`
- `reference/booking_resale_admission/test_resale_console.py`
- `reference/booking_resale_admission/fixtures/resale_console_transfer.txt`
- `reference/booking_resale_admission/fixtures/resale_console_cancel.txt`
- `validation/2026-11-05-plan-plan-local-resale-console/README.md`

## Delivery gates, deviations and limits

Builder implementation is ready for supervisor handoff; this is not a merge-ready
verdict. Initial/ending Git HEAD remains
`ff913965c106a9ee806972d910d8498aa8edc37b`. Implementation commit SHA and exact
final task head SHA: not created here, to be established by the supervisor.
Non-author A2 exact-final-head review: pending. Exact-head KTX kernel verification
and KIX protocol verification: run IDs/statuses/conclusions unverified, not
launched. Both workflows and the independent review remain required. Merge SHA,
post-merge main CI and merge-commit locked-blob verification: not applicable;
no merge was authorized or performed.

- Fetch omitted under the later explicit no-network supervisor rule. Cached
  main/HEAD match, but remote freshness/delta remains unverified. Inline task
  specification/design is the task input; no issue/task document was created.
- The design was followed without expanding selectors or semantics. Clock
  subject remains `clock`; settlement setup is caller-selected fixture setup.
  Bind remains optional and transfer gating remains unchanged. Listing, payment
  observation and ownership are separate returned outcomes.
- Exact missing-record error is the existing `ResalePaymentNotFound` subclass;
  corrected the initial generic test expectation. Supported integer testing uses
  999999999999 within the unchanged 10**12 bound, rather than inventing support
  for values above it. No capability grades changed.
- Python is 3.13.5 rather than CI's 3.12. Rust tests and Clippy could not execute
  because the existing cache lacks bcs (and the archive checker reports 11
  missing packages). No dependencies were downloaded and no retry was attempted.
  Rust formatting passed. This limitation does not represent green Rust CI.
- Full hosted workflows, unfiltered/HTTP discovery, other reference suites,
  Move/localnet, SDK/TypeScript, circuit/proving-artifact, storage and production
  checks were not run. Provisioned Rust/hosted checks remain supervisor/CI work.
- No explicit contract violation found in exercised paths. No new
  contract-undefined behavior was assigned semantics. Product policy stays
  **UNDETERMINED — Astra/User**; legal effects stay
  **UNDETERMINED — User/legal**. Fixtures are examples, not adopted policy.
- Blocking transport has no response deadline. Cleanup/EOF/interruption cannot
  undo accepted requests. A startup reply can race child exit; either terminal
  envelope or transport uncertainty fences the console. Recording replay fetches
  again and may fail; there is no fallback, automatic retry/replay, restart,
  follow-up view, clock advance, business compensation or persistence.
- This is source-informed local composition evidence, not independent review.
  No production durability, distributed fencing, actual funds/providers/KYC,
  bank exactly-once, chain finality, legal compliance, venue reissuance or
  production-readiness claim is established. No STOP-condition resource or
  boundary expansion was needed. R01–R04 retain their existing grades.
