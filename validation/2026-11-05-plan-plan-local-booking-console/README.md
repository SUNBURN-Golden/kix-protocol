# Guided local booking console — builder validation

Node: `plan-plan-local-booking-console`. Task input: supervisor-provided node
specification and read-only design in this session; no task issue or document
under `docs/tasks/` exists. Source: planner run 1793797513. This is not ASTRA
program mode. Publication, commit and GitHub operations belong to the supervisor.

Initial branch: `agent/kix-plan-plan-local-booking-console`.
Initial HEAD and cached `origin/main`:
`f37005f59a75d8b561d9463db423dd70b48ec9c1` (no local delta).
Remote freshness is unverified: the supervisor's explicit no-network instruction
overrides the fetch step. Initial worktree was clean. Implementation/final task
SHA will be established by the supervisor; no new commit is created here.

## Coverage mapping recorded before new console tests

Paths below are under `reference/booking_resale_admission/`.

| Requirement | Existing coverage classification and evidence | Console gap to exercise |
|---|---|---|
| Booking selectors, explicit session clock | Sufficient underlying coverage: `test_booking_session.BookingSessionTests.test_clock_requires_success_through_this_session_and_local_failure_binds_no_key`, `test_only_one_requested_call_with_exact_arguments_and_unchanged_receipt_or_error` | Guided explicit values and booking-only envelopes |
| Shared subprocess service and cleanup | Sufficient underlying coverage: `test_ticket_operations_client.TicketOperationsClientTests.test_buffered_child_reply_before_stdin_eof_and_response_derived_journey`, `test_cleanup_deadline_kills_and_reaps_owned_stubborn_child`, `test_cleanup_deadline_terminates_child_that_does_not_consume_eof` | One launch/close around console success and failure |
| Quote output, exact atoms/hash, no implicit mutation | Sufficient calculator coverage: `test_booking_quote_preview.BookingQuotePreviewTests.test_complete_quote_exact_atoms_hash_label_and_format_equivalence`, `test_exact_single_calculation_unchanged_return_without_machine_clock_or_confirmation`; calculation rejection matrix in `test_calculated_booking_quote_source.py` | Partial journey coverage: prompt interaction and displayed receipt/quote equality |
| Decline, text or identifier edits, failed replacement preview | Not covered at terminal level | No confirmation without fresh successful preview; identical text sent at preview/confirmation; external edits require explicit reload |
| Occupied seat, expiry, release/cancel | Sufficient FSM coverage: `test_reservation_fsm.ReservationFsmTests.test_overlapping_holds_and_replay_do_not_double_book`, `test_expiry_does_not_release_until_an_explicit_release`, `test_cancel_before_payment_frees_and_payment_blocks_compensation`; partial console coverage (none yet) | Real slot-0 refusal, explicit clock expiry, explicit cleanup and terminal views |
| Errors, uncertainty, terminal fencing | Sufficient transport coverage: client `test_structural_and_booking_input_errors_are_terminal`, `test_malformed_truncated_mismatched_and_exited_workers_never_resend`, `test_short_write_broken_pipe_and_interruption_fence_without_remainder_write` | Partial presentation coverage: unchanged envelopes/details, diagnostic bytes/causes, EOF/interruption/I/O stop further submissions |
| Import, docs, offline discovery | Partial: existing client import and predecessor offline recipe | Console import safety, usage transcript, indexed record, current checks |

New tests will be source-informed composition evidence, not independent review.
The existing fixture is reused unchanged: slot 0 has synthetic payment,
settlement binding, issuance and matching adoptions; slot 1 is available.
Console actions perform booking only. No policy value is chosen.

## Actual verification

Commands ran in the foreground, in order: narrow console tests, affected
client/booking/quote suites, broad selection, checks, offline Rust attempts,
then the CI-style console discovery and preservation checks. No long job was
launched in the background. The temporary runner
`python3 -B /tmp/kix-console-run.py PHASE` executed each command below
sequentially and retained stdout/stderr in `/tmp/kix-console-PHASE.json`.
These temporary files are not required to interpret this record.

Except where noted as initial/pre-guard, Python commands used:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-console-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The guard's `sitecustomize.py` contains:

```python
import sys

def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by local console verification guard: ' + event)

sys.addaudithook(deny_socket)
```

Parent and inheriting child environments use that guard. Existing import probes
that replace their subprocess environment are outside the child-guard claim.
The new CLI/import probes inherit the guard. No new dependencies were installed.
No GitHub, network, commit, push, issue, PR or comment action was performed.

Rust used the provisioned toolchain and existing predecessor cache:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-console-target
export CARGO_NET_OFFLINE=true
```

The cache lacks `bcs`. This is an environment limitation, not a green Rust
result. No Rust source, dependency, lockfile or CI was changed to bypass it.

| Command actually run | Actual result |
|---|---|
| `git status --short; git branch --show-current; git rev-parse HEAD origin/main` | Initial worktree clean; expected branch; both cached refs f37005f59a75d8b561d9463db423dd70b48ec9c1; no fetch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs; git rev-parse HEAD:reference/v0.3-rc1` | Required blobs match before edits; historical tree a6ecb124dc2b2267ca6be19e39fbe2aef143074b. |
| `python3 --version` | Python 3.13.5; hosted CI specifies 3.12. |
| `python3 -m unittest test_booking_console (initial, before guard)` | Exit 1: 14 tests in 1.715 s, 8 failures and 1 error. Transcript used unsupported clock subject console-clock; diagnostic test also failed to account for child exit-status line. |
| `python3 -B reference/booking_resale_admission/booking_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/booking_console_confirm.txt (initial)` | Exit 2: exact INVALID_ID on set_clock, then terminal BookingInputError on hold. Corrected transcript to explicit clock; no service change. |
| `python3 -m unittest test_booking_console (corrected, before guard)` | PASS: 14 tests in 1.650 s; exit 0. |
| `python3 -m unittest test_booking_console` | PASS: Ran 16 tests in 1.732s; exit 0. |
| `python3 -m unittest test_ticket_operations_client test_ticket_operations_session test_ticket_operations_cli test_booking_session test_booking_cli test_ticket_operations_quotes test_booking_quote_preview test_booking_quote_preview_cli test_booking_calculation_inputs test_booking_calculation_inputs_cli test_calculated_booking_quote_source test_calculated_booking_quote_cli` | PASS: Ran 110 tests in 20.723s; exit 0. |
| `python3 /tmp/kix-console-offline.py (initial runner)` | Exit 1 before discovery: suite root was not first on sys.path, causing test_contract_error_codes to resolve from settlement_f01_f03. Corrected temporary runner to match predecessor recipe; no repository fix. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: Ran 9 tests in 0.214s; exit 0. |
| `python3 /tmp/kix-console-offline.py` | PASS: Ran 758 tests in 70.801s; exit 0. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: Ran 9 tests in 0.194s; exit 0. |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=351 indexed=316 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | PASS (exit 0): bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (50 negative controls) |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0): architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS: Ran 7 tests in 0.293s; exit 0. |
| `cargo --version` | PASS (exit 0): cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `rustc --version` | PASS (exit 0): rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE (exit 101): cached bcs missing for workspace kix-bcs1; no test/lint body executed; no download or retry. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE (exit 101): cached bcs missing for workspace kix-bcs1; no test/lint body executed; no download or retry. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE (exit 101): cached bcs missing for workspace kix-bcs1; no test/lint body executed; no download or retry. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0): completed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/kix-console-no-sockets python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_booking_console.py` | PASS: 16 tests in 1.585 s; exit 0. Suite path is supplied by discovery, without a suite PYTHONPATH override. |
| `python3 -B /tmp/kix-console-preserve.py` | PASS (exit 0): 1,337 tracked files outside seven allowed paths unchanged; both locked blobs match; historical bytes, branch and cached refs preserved; new Python ASTs and git diff --check valid. |
| `git diff --check` | PASS (exit 0), also run by preservation helper. |

## Delivery gates and limits

Non-author A2 exact-final-head review: pending supervisor handoff.
Exact-head KTX kernel verification and KIX protocol verification run IDs,
statuses and conclusions: unverified, not launched. Full hosted CI remains
required. Builder readiness does not assert merge readiness. Merge SHA and
post-merge CI/locked-blob verification: not applicable (no merge authorized).
Product policy: **UNDETERMINED — Astra/User**. Legal effects:
**UNDETERMINED — User/legal**. No production durability, distributed fencing,
payment, issuance, bank exactly-once, chain finality, legal compliance or
production readiness is established by this local console evidence.

## New console coverage and reproduction

All new symbols below are methods of `test_booking_console.BookingConsoleTests`.
They compose the real subprocess desk except focused rendering/terminal envelope
fault cases. The controlled malformed-reply test also uses a real subprocess and
the ordinary transport client.

| New tests | Gap addressed |
|---|---|
| `test_live_guided_booking`, `test_documented_transcript_as_cli_subprocess` | Real view-show → explicit clock → hold → preview → literal confirmation → returned reservation view; one launch/close; exact booking envelopes and text; receipt amount/hash match displayed quote; original false flags and no payment/issuance |
| `test_decline_consumes_preview_without_confirmation_or_cleanup_mutation` | Decline has no confirmation write; consumes approval; reservation remains held |
| `test_reloading_even_whitespace_and_editing_identifiers_require_new_preview` | CRLF/whitespace preserved; reloading or editing target invalidates snapshot; new preview required; one-shot confirmation |
| `test_failed_replacement_preview_and_failed_load_cannot_use_prior_success` | Failed replacement calculation or file load cannot reuse earlier successful approval; exact source error details; future explicit action permitted |
| `test_external_file_edit_does_not_change_pending_confirmation` | External edits after preview do not change submitted text; confirmation never rereads |
| `test_occupied_seat_error_exact_and_expired_hold_requires_explicit_release` | Exact occupied/expired errors, spent confirmation approval, held state until explicit release |
| `test_explicit_cancel_confirmed_and_explicit_release_held` | Explicit cleanup actions and returned terminal states |
| `test_booking_input_terminal_error_fences_and_preserves_envelope`, `test_startup_and_fixture_terminal_envelopes_stop_before_next_action` | Terminal envelope stop; original details preserved; main closes real child after BookingInputError |
| `test_uncertain_real_transport_preserves_bytes_cause_and_closes_without_resubmit` | Partial non-UTF-8 reply, exact diagnostic bytes/request/cause, one submission, no retry/replacement and child reaped |
| `test_eof_interrupt_and_terminal_read_error_stop_and_close_without_compensation`, `test_interruption_at_confirmation_prompt_submits_no_confirmation`, `test_output_failure_after_reply_retains_result_and_stops` | EOF/interruption/terminal read or output failure fences submissions; no compensation; retained received result |
| `test_required_arguments_cleanup_budget_and_import_safety` | Required fixture/budget, invalid budget rejected before launch, import has no launch/output |
| `test_exact_decimal_renderer_without_floats` | Exact decimal rendering, including values above float exact-integer range |

The scripted success is the documented command in
[console usage](../../reference/booking_resale_admission/README.md#guided-local-booking-console).
The final CI-style discovery probe ensures new tests do not rely on a suite
`PYTHONPATH` override. Existing underlying transport/booking/quote matrices are
reused rather than copied.

The 758-test broad result is **partial socket-denied booking/resale/admission
selection**, not an unfiltered or full repository pass. It excludes exactly:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The predecessor recipe is
[the stdio client validation](../2026-11-04-plan-local-ticket-stdio-client/README.md).
The corrected `/tmp/kix-console-offline.py` is reproduced here:

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

Full unfiltered discovery, `integration_gate.test_http_gate`, provisioned Rust
checks and hosted KTX/KIX workflows remain required in the supervisor/CI path.
Move, localnet, TypeScript, circuit/proving-artifact, storage and other unrelated
full-workflow jobs were not run locally. Full hosted CI selection is intact.

## Preservation and complete changed-path list

Both locked blobs match before and after work:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Protected historical tree:
`reference/v0.3-rc1`: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
The preservation helper compares SHA-256 bytes for every initially tracked file
outside the seven allowed paths against its pre-edit snapshot (1,337 matches),
including every historical file, locked file, fixture, `.aiops/**`, `docs/tasks/**`,
contract and workflow. It also asserts the exact changed-path allowlist, unchanged
HEAD/cached main/branch, valid new Python ASTs and clean `git diff --check`.
Protected files were never edited or transiently mutated.

Complete changed paths:

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/booking_console.py`
- `reference/booking_resale_admission/test_booking_console.py`
- `reference/booking_resale_admission/fixtures/booking_console_quote.json`
- `reference/booking_resale_admission/fixtures/booking_console_confirm.txt`
- `validation/2026-11-05-plan-plan-local-booking-console/README.md`

## Deviations, characterizations and remaining uncertainty

- Fetch omitted under the explicit supervisor no-network rule. Cached refs match
  the design's base, but remote freshness and remote delta are unverified.
- The task is the supplied inline node/design; no issue or task file was created.
- Existing `set_clock` requires explicit subject `clock`. The prompt, fixture
  answers and tests use it; no selector, command or validation rule was changed.
- Initial clock-subject and error-output test assumptions, and the temporary
  broad-runner import order, were corrected with successful reruns above.
- Local Python is 3.13.5 rather than hosted CI's 3.12. Offline Rust tests/Clippy
  could not execute because cached `bcs` is missing; formatting did execute.
- Initial read-only inspection attempted `.github/workflows/verify.yml` and
  `test_bra_evidence_map.py`, which do not exist. Actual `protocol.yml`,
  `ktx-kernel.yml` and applicable checker/test paths were inspected and used.
- No change to client transport, dispatchers, validation, FSMs, contracts or CI
  was needed. No explicit contract violation found in exercised paths.
- Existing characterization: calculation scope/order/expiry fields do not bind
  booking identifiers or establish reservation currentness; explicit confirmation
  still uses existing service checks. This is documented, not redefined here.
- Product policy and legal effects remain UNDETERMINED as assigned above. No new
  business semantics are adopted. There is no claim of production runtime,
  persistence, actual providers/funds/KYC, public endpoints, chain execution,
  storage/replication/consensus engines, secrets or paid services.
- Requests have no response deadline. EOF/interruption or cleanup does not undo
  accepted work. Startup delivery can race process exit; transport failure stays
  uncertainty. No polling, replay, automatic compensation or recovery is added.
- Implementation and exact final task commit SHA: not created; supervisor owns
  commit/push. Current Git HEAD remains the recorded base with uncommitted work.
  Non-author A2 exact-final-head review and both exact-final-head KTX/KIX successes
  remain outstanding. No merge-ready verdict or merge authorization is asserted.
