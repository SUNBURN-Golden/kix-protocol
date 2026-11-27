# Guided local settlement console — builder evidence

Node: `plan-plan-local-settlement-console`. Task input: the supervisor-provided
node specification and read-only design plan in the executing conversation.
No issue or `docs/tasks/` document exists for this node; none was created or edited.
This is not ASTRA program mode. Builder-only local evidence, not independent
review, merge readiness or runtime activation.

## Source and preservation

Initial branch: `agent/kix-plan-plan-local-settlement-console`.
Observed cached `origin/main`, task base and initial implementation HEAD:
`7c43b795241d4e7da047fc3a7634e08ab3471c40`. Initial worktree clean; no local
base delta. `git fetch origin main` was deliberately omitted because the
supervisor explicitly prohibits GitHub/network actions. Remote freshness is
unverified. No commit, push, reset, PR, issue, comment or network action occurred.
The supervisor owns publication. Final implementation is an uncommitted patch;
there is no distinct final committed task head or merge SHA in this session.

The locked blobs matched before editing:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Before editing, a SHA-256 snapshot of all tracked file bytes was saved outside
the repository. Final preservation confirms 1,352 initially tracked files outside
the six allowed paths are byte-identical, and both locked blobs match after work.
The historical `reference/v0.3-rc1` Git tree remains
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`, with its working bytes also unchanged.
Both kernel
locks, `reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**`, contracts, FSMs,
fixtures supplied by predecessors, SDK, catalogue, workflows and protected
configuration were never edited or transiently mutated.

## Existing coverage mapped before new tests

Paths in this table are relative to `reference/`.

| Requirement | Existing coverage classification and evidence | New composition gap |
|---|---|---|
| Statement arithmetic, shortfall and frozen caller order | Sufficient at arithmetic layer: `settlement_f01_f03/test_mock_settlement.py`, `test_f02_statement_does_not_infer_fee_or_shrink_faces`, `test_f02_caller_order_selects_shortfall_and_then_freezes`, `test_f02_later_cash_continues_on_the_frozen_order` | Display/forward exact order and residual obligation fields; no duplicate arithmetic implementation |
| Refund ceiling, acceptance bounds, policy uncertainty | Sufficient FSM/desk coverage: `booking_resale_admission/test_ticket_refund_controls.py`, `test_economic_rejections_retained_keys_and_conflicts_at_both_phases`, `test_partial_obligation_fully_accepted_and_summed_bindings_keep_burden_undefined`; `settlement_f01_f03/test_mock_settlement.py`, `test_f03_partial_refund_blocks_distribution_without_reclassifying` | Show exact errors and unchanged separately requested view; label synthetic acceptance |
| Statement/refund input journey and exact envelopes | Sufficient desk layer: `booking_resale_admission/test_ticket_settlement_fact_inputs.py`, `test_empty_and_omitted_sources_complete_explicit_journey`, `test_boundary_transcript_matches_direct_fsm` | Not covered for settlement console: prompts, one real child, rendered sections, documented answers |
| Recorded selectors and immutable receipt replay | Sufficient service layer: `booking_resale_admission/test_ticket_statement_distribution.py`, `test_file_stdin_and_api_journeys_match_direct_fsm_after_every_step`, `test_direct_recorded_key_equivalence_conflicts_and_movement_characterization` | Partial via predecessor consoles; settlement receipt/current-view distinction and recorded-source composition missing |
| Single client, diagnostics, fencing and cleanup | Sufficient transport layer: `booking_resale_admission/test_ticket_operations_client.py`, `test_malformed_truncated_mismatched_and_exited_workers_never_resend`, `test_short_write_broken_pipe_and_interruption_fence_without_remainder_write`, cleanup deadline tests | Partial through booking/resale consoles; settlement queued-action fencing and saved reply on display failure missing |
| Per-mutation decline and exact input parsing | Partial conventions in `booking_resale_admission/test_booking_console.py` and `test_resale_console.py`; no settlement terminal tests | Not covered: all eight settlement mutations require their own literal `SUBMIT`; no generated values |

## New evidence

All tests below are methods of
`reference/booking_resale_admission/test_settlement_console.py`'s
`SettlementConsoleTests`. These are source-informed composition tests; they do
not claim clean-room independence or reimplement settlement arithmetic.

| Test | Gap addressed |
|---|---|
| `test_live_journey` | One actual desk launch/close, all 12 explicit requests, full response parity with unchanged `dispatch_request`, exact rendered fields, partial statements, distribution/refund/acceptance, historical first receipt and current view |
| `test_insufficient_cash_keeps_service_obligations_and_explicit_order` | Residual obligations and unchanged faces displayed after caller-ordered distribution; shortfall is not mislabeled a refusal |
| `test_over_refund_acceptance_and_conflicting_keys_preserve_current_view` | Exact `REFUND_CEILING`, `REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION`, `IDEMPOTENCY_CONFLICT` and unchanged subsequent views |
| `test_recorded_statement_and_acceptance_selectors_and_source_refusal` | Recorded commit/observation/acceptance, exact known source error and explicit continuation using unchanged fixtures |
| `test_every_mutation_requires_literal_single_use_submit` | Decline all eight mutations, zero submissions, complete proposal, approval cannot authorize the next action |
| `test_invalid_syntax_never_submits_or_invents_defaults` | Integer/JSON/explicit text parsing; invalid selections submit nothing |
| `test_economic_validation_and_duplicate_order_are_left_to_service` | Signed integer and duplicate order forwarded without UI policy decisions |
| `test_null_claim_has_no_manufactured_cash` | Actual initiated fixture returns null claim; unavailable display has no manufactured cash |
| `test_large_integer_is_forwarded_without_float_conversion` | Exact supported integer forwarding/display with original service refusal |
| `test_eof_interruption_and_input_failure_fence_and_close` | Last complete reply retained; EOF during approval submits nothing; same child reaped |
| `test_terminal_envelopes_stop_before_queued_action` | Startup/structural errors retain envelopes and stop queued actions |
| `test_real_transport_uncertainty_does_not_resubmit_or_consume_queued_actions` | Actual malformed/truncated child replies, exact uncertainty bytes/causes, single request, queued actions unread, child reaped |
| `test_output_failure_retains_reply_even_if_diagnostics_fail` | Save reply before rendering; broken display/diagnostic streams cannot authorize another request |
| `test_request_interruption_is_terminal` | Interrupted submission never continues or resubmits |
| `test_required_arguments_import_and_lifecycle_failures` | Required fixture/finite positive cleanup budget, inert import, startup/cleanup failures and nonzero child status |
| `test_documented_transcript_as_cli_subprocess` | Actual terminal CLI composes with the real desk using the checked-in answer file |

The [usage and transcript](../../reference/booking_resale_admission/README.md#guided-local-settlement-console)
record all caller inputs and service integers. Each mutation explicitly selects a
view afterwards. Current cash 9301, refund outstanding 3000 and PG adjustment
outstanding 1000 are separate service facts. The final duplicate commit still
reports original cash 5500/open receivable 4001. Synthetic acceptance never
means real refund completion; execution/closure/durability flags remain false.

## Executed local verification

Python commands use the predecessor's socket-denial guard in both the parent
and inheriting children:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-settlement-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-settlement-no-sockets/sitecustomize.py`:

```python
import sys
def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by local console verification guard: ' + event)
sys.addaudithook(deny_socket)
```

Legacy import probes which replace their child environment are outside the
child-guard claim. New console tests/probes inherit the guard. No dependencies
were bootstrapped or downloaded. Jobs run in the foreground, never as background
shell jobs. The workflows inspected were `.github/workflows/protocol.yml` and
`.github/workflows/ktx-kernel.yml`. The checks below are targeted offline local
equivalents for the touched paths, not full hosted CI.

| Command actually run | Actual result |
|---|---|
| `git status --short`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git branch --show-current` | Clean initial worktree, expected branch; both cached refs `7c43b795241d4e7da047fc3a7634e08ab3471c40` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before work |
| `python3 -m unittest test_settlement_console` (initial) | Exit 1: 16 tests, one failure; test incorrectly assumed CAPTURED has a null claim. Corrected test fixture to INITIATED, without service changes |
| `python3 -m unittest test_settlement_console` (corrected) | PASS: 16 tests, exit 0 |
| `python3 -m unittest test_ticket_operations_client test_ticket_operations_session test_ticket_operations_cli test_ticket_statement_distribution test_ticket_refund_controls test_ticket_settlement_controls test_ticket_settlement_fact_inputs test_ticket_settlement_fact_inputs_cli test_booking_console` | PASS: 94 tests, exit 0 |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, exit 0 |
| `python3 -B reference/booking_resale_admission/settlement_console.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_fact_inputs_session.json --cleanup-timeout 1 < reference/booking_resale_admission/fixtures/settlement_console_journey.txt > /tmp/kix-settlement-transcript.txt` | PASS: exit 0; 12 complete desk envelopes; current 9301 cash / 3000 refund outstanding / 1000 PG adjustment outstanding |

| Command actually run | Actual result |
|---|---|
| `python3 scripts/check_docs_index.py` | PASS, exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_settlement_evidence_map.py` | PASS, exit 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | PASS, exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_contract_error_codes.py` | PASS, exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | PASS, exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_ci_test_discovery.py` | PASS, exit 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_openapi_contract.py` | PASS, exit 0 |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS, exit 0 |
| `python3 scripts/check_integration_gate_openapi.py` | PASS, exit 0 |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS, exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | PASS, exit 0 |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, exit 0 |

| Command actually run | Actual result |
|---|---|
| `python3 /tmp/kix-settlement-offline.py` | PASS: 805 tests, exit 0; exactly one HTTP socket test excluded as named below |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_settlement_console.py` | PASS: 16 tests, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101 before compilation; cached crates.io index lacks `bcs`, required by workspace `kix-bcs1` |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101 before compilation; same missing cached `bcs` dependency |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0 |
| `python3 -B /tmp/kix-settlement-preserve.py` | PASS: exit 0; exactly six allowed changed paths, 1,352 other tracked paths byte-identical, locked blobs match, historical bytes unchanged, branch/HEAD/cached main unchanged, new Python ASTs parse, `git diff --check` clean |

Rust used the provisioned toolchain and predecessor cache, without installation
or dependency downloads:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-console-target
export CARGO_NET_OFFLINE=true
```

Missing `bcs` is an environment limitation, not a green Rust result. No Rust
source, dependency, lockfile or CI change was made to bypass it. Provisioned
Rust test/Clippy execution remains a supervisor/CI gate. No Rust code is touched.

The broad offline selection uses the same single explicit exclusion as the
predecessor [booking console evidence](../2026-11-05-plan-plan-local-booking-console/README.md).
The excluded test starts an HTTP socket; this is not an unfiltered BRA pass.
`/tmp/kix-settlement-offline.py` contains:

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

The external foreground runner `/tmp/kix-settlement-verify.py PHASE` runs each
listed command sequentially with the above environment, retaining command,
actual return code and combined stdout/stderr in
`/tmp/kix-settlement-PHASE.json`. It does not retry commands. These temporary
files are not needed to interpret the results recorded here.

The preservation helper compares every initial tracked path's SHA-256 with its
pre-edit snapshot and rejects any mismatch outside the six-path allowlist below.
It unions those mismatches with `git ls-files --others --exclude-standard` and
requires exactly that allowlist. It also asserts unchanged HEAD, cached main,
branch, both required `git hash-object` values, parses both new Python ASTs and
runs `git diff --check`. This covers working bytes as well as Git tree identity.

## Complete changed-path list

- `reference/booking_resale_admission/settlement_console.py`
- `reference/booking_resale_admission/test_settlement_console.py`
- `reference/booking_resale_admission/fixtures/settlement_console_journey.txt`
- `reference/booking_resale_admission/README.md`
- `validation/2026-11-05-plan-plan-local-settlement-console/README.md`
- `docs/README.md`

## Deviations, gates and non-claims

The conversation is the immutable task input, as explicitly supplied by the
supervisor; no task document or issue was authored. Fetch/publication and
independent review/CI are deferred to the supervisor by explicit instruction.
The broader offline selection exceeds the design's named narrow regressions
while retaining the predecessor's single socket-test exclusion. Rust test and
Clippy are unavailable because the offline cache lacks `bcs`; no dependency
bootstrap was attempted. Formatting and both architecture checks passed.
The transcript adds explicit intermediate views and a caller-selected original
commit replay to demonstrate snapshots versus current observations. Economic
validation remains service-owned, including negative integer refusals and
duplicate distribution order. No new policy, protocol command or consequential
scope expansion was needed; no DECISION_REQUIRED condition was encountered.

Contract-defined behavior matched the existing dispatcher controls; no explicit
contract violation was found. Existing class-B zero-cash distribution
characterization remains unresolved; no UI policy was invented to resolve it.
Distribution/refund policy: **UNDETERMINED — Astra/User**. Accounting/legal
effects: **UNDETERMINED — User/designated advisers**.

Required non-author A2 exact-head review: pending supervisor publication.
Exact-head KTX kernel CI run ID/status/conclusion: unavailable, not run.
Exact-head KIX protocol CI run ID/status/conclusion: unavailable, not run.
Post-merge main CI: not applicable; no merge. Final committed task HEAD and
review/CI evidence must be recorded externally for the supervisor's eventual
exact head, without committing a self-referential CI evidence loop.

No claims of real refund completion, provider/bank exactly-once, distributed
fencing, durability, accounting/legal compliance, chain finality, production
readiness or completed P04 durable closure follow from these tests. F04, reward
coupling, persistence, new ledgers/read models, FSM/contract/catalogue/SDK and
protected configuration changes remain outside scope. Full socket-bearing BRA
discovery and unrelated Move, storage, localnet, TypeScript and ZK jobs are not
claimed locally. Policy, independent review and required full CI remain open
gates; this report cannot authorize merge or readiness promotion.
