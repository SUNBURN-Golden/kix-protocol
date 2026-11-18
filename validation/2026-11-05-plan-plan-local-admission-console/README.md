# plan-plan-local-admission-console — builder evidence

Task input: the supervisor-supplied inline node and read-only design in the
executing conversation; no issue and no task document under `docs/tasks/` exists
for this node. No task document was created or changed. This is not ASTRA
program mode. Audit floor A2; no independent review is claimed.

Initial branch: `agent/kix-plan-plan-local-admission-console`.
Cached `origin/main`, task base and initial HEAD:
`7e75391341ef944faa9bea3e82909233292b2ce8`.
The explicit supervisor no-network rule overrides the startup fetch: remote
freshness/delta is unverified. Initial worktree was clean. Implementation/final
commit SHA is not created; supervisor owns git/GitHub publication. HEAD remains
that base while this delivery is uncommitted. No merge or post-merge CI applies.

## Existing coverage mapping (inspected before adding tests)

Paths below are under `reference/booking_resale_admission/`.

| Requirement | Existing coverage | New interaction gap |
|---|---|---|
| Authorization separate from consumption; replay/current state | Sufficient FSM coverage: `test_admission_fsm.AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`; partial terminal coverage | One child, exact prompted selectors, separate literal approvals, explicit current view, snapshot versus current labels |
| Expired authorization | Sufficient: `test_presentation_adapter.PresentationAdapterTests.test_expired_authorization_cannot_consume_or_change_state`; `test_admission_fsm.AdmissionFsmTests.test_expired_authorization_is_replaced_once` | Explicit terminal clock, unchanged error and unconsumed view |
| Stale holder/version, transferred tickets and changed bindings | Sufficient underlying `test_admission_session.AdmissionRequestInputsTests` and shared `test_admission_cli.AdmissionInputsDeskChecks` (also inherited by ticket desk CLI tests) | Complete terminal fields, original replies, same child's transfer preparation outside menu |
| Caller values, false flags and original replies | Sufficient session/direct-FSM parity in `test_admission_session.py`, `test_ticket_operations_session.py`; partial terminal coverage | Decoded displayed envelope equality; direct controls; presentation versus stored credential; accepted text and large integer preservation |
| Decline submits nothing | Not covered for admission terminal | Decline inspection and literal, distinct, single-use confirmations |
| Transport and child lifecycle | Sufficient client coverage in `test_ticket_operations_client.py`; partial console interaction coverage | One launch/close, uncertainty bytes, last reply, queued actions after EOF/interruption/read/output/terminal failure |
| Docs, executable/import safety | Partial predecessor console/discovery checks | Executable answer fixtures, silent import, required budget, indexed record and current offline checks |

New tests are source-informed composition evidence, not independent FSM
verification. Existing FSM invariants are reused rather than duplicated. The
console, tests and two answer fixtures add no service semantics or policy values.

## Verification

| Command actually run | Actual result |
|---|---|
| `git status --short; git rev-parse HEAD; git rev-parse origin/main; git branch --show-current` | Initial worktree clean; expected branch; both cached refs/base `7e75391341ef944faa9bea3e82909233292b2ce8`; no fetch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required locked blobs match before and after work (hashes below). |
| `git ls-tree -r HEAD reference/v0.3-rc1; git rev-parse HEAD:reference/v0.3-rc1` | Protected historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; bytes preserved. |
| `python3 --version; /usr/bin/python3 --version` | Python 3.13.5. |
| `python3 -m unittest test_admission_console` | PASS: 16 tests in 5.117s; exit 0. |
| `python3 -m unittest test_ticket_operations_client test_admission_session test_admission_cli test_ticket_operations_session test_ticket_operations_cli test_presentation_source test_presentation_adapter test_admission_rejection_atomicity test_booking_console test_resale_console` | PASS: 214 tests in 18.222s; exit 0. |
| `python3 /tmp/kix-admission-offline.py` | PASS: 789 tests in 83.108s; exit 0. Partial discovery: exactly one HTTP test excluded as reproduced below. |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=353 indexed=318 allowlisted=35 |
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
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests in 0.194s; exit 0. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests in 0.198s; exit 0. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_admission_console.py` | PASS: 16 tests in 4.627s; exit 0. |
| `cargo --version` | PASS (exit 0): cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `rustc --version` | PASS (exit 0): rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101; cached `bcs` missing for workspace `kix-bcs1`. No test/lint body executed; no network retry. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: exit 101; cached `bcs` missing for workspace `kix-bcs1`. No test/lint body executed; no network retry. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101; cached `bcs` missing for workspace `kix-bcs1`. No test/lint body executed; no network retry. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0): format check completed |
| `python3 -B /tmp/kix-admission-preserve.py` | PASS: 1,347 tracked files outside seven allowed paths unchanged; locked/historical bytes, refs/branch, exact path allowlist, ASTs and diff check pass. |
| `git diff --check` | PASS (exit 0); no whitespace errors. |

All commands ran synchronously in the foreground; no job was launched in the
background. Local Python is 3.13.5 (hosted CI specifies 3.12). Python tests and
checks use `PYTHONDONTWRITEBYTECODE=1`. Narrow, affected and broad tests use:

```bash
export PYTHONPATH="/tmp/kix-admission-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary guard is `sitecustomize.py` on that path, containing:

```python
import sys

def deny_socket(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise RuntimeError('socket denied by local admission console verification guard: ' + event)

sys.addaudithook(deny_socket)
```

The new console executable/import probes and all its desk children inherit this
environment. Existing regression import probes that replace their subprocess
environment are outside the inherited-child-guard claim. No dependency was
installed; no network, git publication, issue, PR or comment action was performed.

The temporary `/tmp/kix-admission-offline.py` reproduces the predecessor
[booking console exclusion recipe](../2026-11-05-plan-plan-local-booking-console/README.md):

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

This is **partial socket-denied reference discovery**, not an unfiltered suite
pass. Full discovery/HTTP checks remain in the supervisor/CI path. Checks in the
table below use `PYTHONPATH=/tmp/kix-admission-no-sockets` only, including the final
CI-style console discovery, which obtains its suite import path from discovery.
The temporary foreground runner `python3 -B /tmp/kix-admission-checks.py` runs
each listed command sequentially and saves its actual output to
`/tmp/kix-admission-checks.json`; those files are not required to interpret this
record. Rust uses the provisioned toolchain and existing cache:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-admission-target
export CARGO_NET_OFFLINE=true
```

## New interaction evidence

All new methods below belong to `test_admission_console.AdmissionConsoleTests`.

| Test | Gap addressed |
|---|---|
| `test_live_admission_transcript` | One real child and close; exact admission envelopes; explicit view, clock, authorize, inspect, consume, replay authorization and inspect; historical AUTHORIZED versus current CONSUMED/version 2; false flags; decoded displayed replies match direct-FSM controls |
| `test_authorization_alone_never_consumes` | Authorization plus explicit view and quit contains no consumption request; version 1 and no consume ID |
| `test_declined_consumption_submits_nothing` | Decline submits nothing, followed by explicit unchanged authorization inspection |
| `test_each_confirmation_is_literal_distinct_and_single_use` | AUTHORIZE/CONSUME/SET_CLOCK confirmations cannot substitute for one another or carry forward; consumption selection alone never invokes authorization |
| `test_expiry_stale_holder_version_and_request_refusals_match_fsm` | Explicit expiry clock and ADMISSION_EXPIRED; exact STALE_VERSION, NOT_HOLDER, ADMISSION_REQUEST envelopes; request case/text preserved, no correction or automatic clock |
| `test_transferred_ticket_refusals_with_same_real_child` | Harness explicitly transfers through existing resale selectors in the same real child before console; old/new holder/version errors unchanged; stored adopted credential and caller presentation remain distinct; no resale menu/setup added |
| `test_changed_binding_preserves_first_result_and_text` | Changed request binding yields original IDEMPOTENCY_CONFLICT, complete explicit replay retains first result; accepted Unicode identifiers, keys and lowercase hex preserved exactly |
| `test_malformed_terminal_fields_submit_nothing_and_do_not_infer` | Bad decimal syntax, Unicode digits, excessive integers, blank/padded text rejected without submission; unknown actions submit nothing; integer above float exact range forwarded unchanged |
| `test_consumption_confirmation_eof_interrupt_and_read_failure_send_nothing` | EOF/interruption/read failure during consume confirmation cannot submit consumption; prior authorization reply retained |
| `test_eof_interrupt_and_input_failure_stop_and_close` | EOF/interruption/read failure fences after last explicit action and closes child; interruption before authorization confirmation submits nothing |
| `test_terminal_envelopes_preserved_before_queued_action` | Original terminal fixture/input envelope retained; queued view not submitted; actual invalid-fixture child also fences |
| `test_real_transport_uncertainty_stops_queued_action_and_reaps_child` | Real truncated non-UTF-8 reply; exact request and reply bytes/cause retained; one request only; no retry/replacement; child reaped |
| `test_output_failure_retains_reply_and_fences_even_with_broken_diagnostics` | Received last reply survives display failure; broken diagnostics cannot permit a second action |
| `test_request_interruption_fences_before_queued_action` | Submitted exchange interruption prevents queued submission |
| `test_required_arguments_cleanup_budgets_import_and_cleanup_failure` | Required fixture/finite-positive cleanup budget before launch; silent import; close failure fences |
| `test_documented_transcripts_as_cli_subprocesses` | Both documented answer files run through the actual console executable and inherited socket guard |

Direct controls are independently constructed with the existing `direct_graph`,
`direct_call`, `outcome`, `snapshot` helpers and source-informed FSMs. They bypass
the console/client/session adapters but do not constitute clean-room or non-author
review. No test-count threshold is used as an acceptance criterion.

## Preservation, delivery gates and non-claims

Required kernel blobs match before and after edits:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Historical `reference/v0.3-rc1` tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
A pre-edit SHA-256 snapshot of all tracked files is compared with final bytes
outside the changed-path allowlist, including every historical/locked file,
`.aiops/**`, `docs/tasks/**`, session, FSM, fixture loader, contract and workflow.
Protected files were never edited or transiently mutated. Final preservation
also checks unchanged refs/branch, the exact path allowlist, Python AST parsing
and `git diff --check`.

Complete changed-path list:

- `reference/booking_resale_admission/admission_console.py`
- `reference/booking_resale_admission/test_admission_console.py`
- `reference/booking_resale_admission/fixtures/admission_console_consume.txt`
- `reference/booking_resale_admission/fixtures/admission_console_decline.txt`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-05-plan-plan-local-admission-console/README.md`

Non-author A2 exact-final-head review: **pending supervisor handoff**.
Exact-final-head KTX kernel verification and KIX protocol verification run IDs,
statuses and conclusions: **unverified, not launched**. No final delivery commit
was made. No merge-ready verdict, draft-ready action or merge authorization is
asserted. Merge SHA, post-merge main CI and merge-commit blob checks: not
applicable. Supervisor must retain those required gates after committing.

Admission timing and identity policy remain **UNDETERMINED — Astra/User**;
legal effects remain **UNDETERMINED — User/legal**. P03 remains design-stage.
This evidence establishes no authentication, independent currentness, real entry,
production runtime/readiness/durability, distributed fencing, bank exactly-once,
chain finality, legal compliance, actual funds/provider/KYC execution, secret
handling, storage/consensus/replication engine or capability-grade improvement.
No unrelated Move, localnet, TypeScript, circuit/proving-artifact or full-workflow
verification was run locally.

## Deviations and remaining uncertainty

- Startup fetch omitted under the explicit no-network supervisor rule; only the
  cached main/base/head were observed, all identical. Remote freshness is unknown.
- Task input is the supplied inline node/design, not an issue or task file; no
  task issue/document or `.aiops/` state was created or changed.
- Python 3.13.5 is provisioned instead of CI's 3.12. The existing socket-denied
  discovery recipe excludes exactly one HTTP test. This is not full CI evidence.
- Offline kernel/workspace tests and kernel Clippy were unavailable because the
  existing Cargo cache lacks `bcs`. No dependencies, lockfiles, CI or runtime code
  were changed to bypass this. Provisioned offline cache or hosted CI is needed
  for these outstanding checks; formatting did execute successfully.
- No implementation scope deviation or consequential policy choice was needed.
  Semantic malformed request text is passed to the existing desk unchanged;
  malformed terminal syntax is rejected locally, as with the predecessor console.
- No explicit contract violation was found in exercised paths. Existing Class-B
  `test_admission_rejection_atomicity.AdmissionRejectionAtomicityTests.test_char_authorize_clock_skew_window`
  remains unchanged: clock-skew/partial cross-machine advancement is an observed
  characterization, not a rollback guarantee or something repaired here.
- Requests have no response deadline. Cleanup/EOF does not undo accepted work;
  startup envelopes may race process exit. Uncertainty remains fenced, without
  polling, retry, replacement, compensation, automatic view or clock changes.
- Independent review, final commit SHAs and exact-head hosted CI remain for the
  supervisor. No production/currentness/legal decision is inferred from local
  test results. No STOP-condition dependency was needed for this implementation.
