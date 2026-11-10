# Source-backed booking quote console — builder evidence

Node: `plan-plan-local-source-quote-console`. Task input is the supplied node
specification and read-only design; no task issue or node document exists under
`docs/tasks/`. Non-ASTRA builder session, supervisor owns Git/GitHub publication.

Initial HEAD and cached `origin/main`: `2a50b8f1f7dab95b59de389e1f57db9eb88e2cc2`.
Branch: `agent/kix-plan-plan-local-source-quote-console`. Fetch omitted under
explicit supervisor no-network instruction; remote freshness is unverified.

## Existing coverage mapping (recorded before adding tests)

| Requirement | Classification before console changes | Existing evidence / gap |
|---|---|---|
| Source options and real children | Partially covered | `test_ticket_operations_client.test_quote_payload_and_both_existing_quote_fixture_options`; console wiring absent |
| Complete replies, identities, synthetic flags | Sufficient underneath; partial console composition | `test_ticket_operations_quotes.test_transcripts_match_direct_adapter_receipts_errors_and_graph_after_every_line`; console/direct parity needed |
| Current reads, historical replay, conflicting keys | Partially covered | Same service transcript test and adapter `test_replay_alias_changed_quote_amount_order_and_binding_parity`; console journey absent |
| Missing/malformed/faulting records, mismatch | Sufficient underneath; partial console composition | Quote service `test_source_rejections_do_not_delegate_mutate_or_bind_the_confirmation_key`; adapter `test_missing_bad_json_and_faults_no_fsm_call_or_key_binding`; calculated source `test_all_source_rejections_do_not_delegate_mutate_or_bind_key` |
| Pricing/expiry refusals | Sufficient underneath; partial console composition | Adapter `test_retained_price_and_expiry_refusals_match_direct_session`; calculated source `test_receipts_replay_price_expiry_and_historical_result_match_direct_session` |
| Decline, incomplete input, navigation | Partially covered | Existing booking confirmation and shared `test_navigation_sends_nothing`; new action untested |
| Preview invalidation on source action | Not covered | New invalidation boundary |
| Uncertainty fencing, no retry/replacement | Sufficient client; partial action coverage | Client malformed/write/interruption tests; shared `FAULT_ACTIONS` matrix needs new action |
| Both flags rejected / absent compatible | Not covered for flags; existing no-source journeys sufficient | Parser mutual exclusion and forwarding need tests |
| Documentation/preservation | Existing infrastructure | Docs index, BRA evidence, contract, architecture checks; add usage and indexed evidence |

No new service semantics are authorized. Product policy remains
**UNDETERMINED — Astra/User**; legal effects **UNDETERMINED — User/legal**.

## Added composition evidence

| Evidence | Gap addressed |
|---|---|
| `test_booking_console.test_source_journeys_complete_parity_history_and_refusals` | Both live source bindings, full direct-dispatch parity, explicit unchanged views after source refusals, same-key success, retained price refusal, cancellation/current views, historical replay, changed order/hash conflicts and explicit reservation expiry |
| `test_source_clean_success_and_absent_source_terminal_error` in the same module | Exit 0 with either source; no-source submission preserves terminal FixtureError, diagnostics and unread next action |
| Same module's source prompt/incomplete/selection/interruption/flags tests | Literal-token-only submission, complete escaped proposal and prompt order, blank/whitespace fields and interrupted collection submit nothing, pending calculated preview invalidates before decline/bad input while loaded text and target survive, conflicting flags rejected before launch |
| `test_shared_ticket_console.test_source_shared_journeys_reentry_history_and_parity` | Both sources forwarded once to one child with one close, explicit resale/admission observations, booking re-entry, full reply parity and each surface's original synthetic flags |
| Same module `test_source_transcripts_as_real_console_subprocesses` | All four supplied answer files run through real console entry points and their real children, comparing every complete reply to equivalent direct dispatch |
| Shared `test_source_decline_incomplete_input_and_navigation_submit_nothing` | Decline, invalid field and navigation on a live child perform zero requests |
| New booking source action in existing shared `FAULT_ACTIONS` | Null/terminal errors, malformed/truncated/EOF replies, short/broken writes, exchange interruption and display failures fence the shared session; one attempt, retained request/reply/exception diagnostics, unread queued navigation, no retry or replacement child |

Underlying adapter/source/FSM semantics reuse existing regression tests rather
than duplicating private implementation tests. These are source-informed console
composition controls, not clean-room or independent protocol verification.
The service, source loaders, adapter, client, FSM and populated fixture remain
unchanged. Calculated sources have no fixture fault selector; synthetic source
error/timeout entries are exercised through the unchanged recorded fixture.
No fault syntax or other semantics were invented for the calculated source.

## Verification environment and actual commands

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. Focused console
tests ran first, then relevant source/client/service regressions, then the broad
offline BRA suite and applicable documentation/contract/architecture checks.
Long-running test commands used foreground subprocesses; no detached jobs,
network actions, automatic retries or CI modifications were used.

Python 3.12.15; cargo/rustc 1.98.1. Commands run from the repository root with:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-source-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
export CARGO_NET_OFFLINE=true
export CARGO_TARGET_DIR=/tmp/kix-source-target
```

Temporary `sitecustomize.py` installs an audit hook rejecting `socket.__new__`,
`socket.connect`, `socket.bind`, and `socket.getaddrinfo`. Legacy tests that
replace child environments are outside the inherited-hook claim. No network
or endpoint was requested. `/tmp/kix-source-run.py` invokes each argument array
once with `subprocess.run`, preserving full combined output and exit code in
[command-results.json](command-results.json) and [check-results.json](check-results.json).
Expected boundary-transcript exits 1 are intentional, not failed tests.

The first focused run failed only in the newly added parity helper: it applied
booking-only flag assertions to resale/admission views. Restricting that check
to booking and using the existing surface-specific assertions fixed those four
subtest errors; the next full focused run passed. Both executions are retained.
No product implementation or service semantics changed for that correction.

The no-network broad selection is the design's established **single** exclusion:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
It is not an unfiltered/HTTP CI pass. Exact `/tmp/kix-source-offline.py` body:

```python
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path('reference/booking_resale_admission').resolve()))
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
assert len(ids) == len(set(ids))
excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
assert ids.count(excluded) == 1
print('EXCLUDED SOCKET TEST: ' + excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(
    unittest.TestSuite(t for t in all_tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

| Command actually run | Actual result |
|---|---|
| `python3.12 -B -m unittest test_booking_console test_shared_ticket_console` | FAIL: exit 1; 65 tests; four new parity-helper subtest errors (corrected below) |
| `python3.12 -B -m unittest test_booking_console test_shared_ticket_console` | PASS: exit 0; 65 tests |
| `python3.12 -B -m unittest test_booking_quote_source test_booking_quote_adapter test_booking_quote_cli test_calculated_booking_quote_source test_calculated_booking_quote_cli test_ticket_operations_quotes test_ticket_operations_client test_booking_quote_preview test_booking_quote_preview_cli test_ticket_operations_session test_ticket_operations_cli` | PASS: exit 0; 101 tests |
| `python3.12 -B /tmp/kix-source-transcripts.py` | PASS: exit 0; four expected-exit-1 transcripts; 35/31/37/33 full replies; direct parity |
| `python3.12 -B /tmp/kix-source-offline.py` | PASS: exit 0; 947 tests; exactly one socket-bearing test excluded |
| `python3.12 -B /tmp/kix-source-preserve.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_docs_index.py` (after completing evidence links) | PASS: exit 0 |
| `git diff --check` | PASS: exit 0 |
| `python3.12 -B scripts/check_docs_index.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_docs_index.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_status_register.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_status_register.py --self-test` | PASS: exit 0 |
| `python3.12 -B scripts/check_bra_evidence_map.py` | PASS: exit 0 |
| `python3.12 -B scripts/check_bra_evidence_map.py --self-test` | PASS: exit 0 |
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
| `python3.12 -B scripts/test_runtime_architecture.py` | PASS: exit 0; 7 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101; offline cache lacks `bcs`; no compilation |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101; offline cache lacks `bcs`; no compilation |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0 |

Rust tests and Clippy were attempted offline and stopped before compilation:
the provisioned crates.io cache lacks `bcs`, required by `kix-bcs1` during
workspace resolution. They are **unavailable**, not passes. No dependency
download, cache bootstrap, lockfile modification or CI bypass was attempted.
Formatting passed. Full hosted protocol CI (including socket, Move/localnet,
ZK and TypeScript steps) and unrelated suites are not claimed by these local
checks; no runtime or capability grade changed.

## Real subprocess transcripts

The commands and explicit input paths are recorded in
[transcript-results.json](transcript-results.json). Each uses
`python3.12 -B reference/booking_resale_admission/<console>.py`,
`--fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json`,
`--cleanup-timeout 1` and the corresponding source option documented in the
[usage guide](../../reference/booking_resale_admission/README.md#source-backed-booking-confirmation-in-the-live-consoles).
Every parsed `desk=` envelope matches an equivalent `dispatch_request` on a
separately loaded desk plus the unchanged `BookingQuoteAdapter` and selected
source loader. Errors use the existing `_error` representation. Receipt
identities, duplicates/applied fields and synthetic flags are compared in full.

| Console / source | Input answer file (under BRA fixtures/) | Exit / full replies | Captures |
|---|---|---|---|
| Booking / recorded | `booking_console_source_recorded.txt` | Expected 1 / 35 | [stdout](booking_console_source_recorded.stdout), [stderr](booking_console_source_recorded.stderr) |
| Booking / calculated | `booking_console_source_calculated.txt` | Expected 1 / 31 | [stdout](booking_console_source_calculated.stdout), [stderr](booking_console_source_calculated.stderr) |
| Shared / recorded | `shared_ticket_console_source_recorded.txt` | Expected 1 / 37 | [stdout](shared_ticket_console_source_recorded.stdout), [stderr](shared_ticket_console_source_recorded.stderr) |
| Shared / calculated | `shared_ticket_console_source_calculated.txt` | Expected 1 / 33 | [stdout](shared_ticket_console_source_calculated.stdout), [stderr](shared_ticket_console_source_calculated.stderr) |

The clean booking cases separately demonstrate exit 0 for both sources; terminal
no-source and controlled transport cases demonstrate exit 2. Known source
errors permit later explicit input. Synthetic timeout is a known source error,
not evidence of an uncertain transport or an inferred rollback. No implicit
view, clock advance, preview, retry, cancel or child replacement is performed.

## Preservation and complete changed paths

The initial clean tracked-file SHA-256 manifest was recorded before any edit.
`python3.12 -B /tmp/kix-source-preserve.py` compares all those bytes, requires
exactly the six authorized tracked changes, restricts untracked additions to
the four answer files and this evidence directory, verifies unchanged refs and
branch, parses changed Python ASTs and runs `git diff --check`.
The preservation run passed: **3,108 of 3,114 initially tracked files** remain
byte-identical, including all **108** historical files; only the six allowed
tracked paths differ. See [preservation.json](preservation.json) for actual counts and results and
[changed-paths.txt](changed-paths.txt) for the complete changed-path list,
including evidence artifacts.

Both locked blobs match before and after work:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The historical `reference/v0.3-rc1` tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; all its tracked working-tree bytes
remain identical to the initial manifest. All other unchanged tracked bytes
also include `.aiops/**`, `docs/tasks/**`, service contracts, loaders, adapter,
client, FSMs, fixtures, workflows, SDK and blocked-node work. No commit, push,
fetch, rebase, branch/tag operation or GitHub action was performed.

Inspection/preservation commands actually run include `git status --short`
(initial clean), `git rev-parse HEAD`, `git rev-parse origin/main`,
`git branch --show-current`, `git hash-object` on both locked paths,
`git ls-tree HEAD reference/v0.3-rc1`, `git diff --check`, Python/cargo/rustc
version queries and the manifest/preservation helpers. These are local
observations, not remote freshness or hosted verification claims.

## Classifications, deviations and delivery gates

Contract-defined behavior matches the unchanged service controls. No explicit
contract violation or new contract-undefined behavior was found. Calculation
`expiresAt` remains hash-bound metadata; reservation expiration remains
service-owned. Product policy **UNDETERMINED — Astra/User** and legal effects
**UNDETERMINED — User/legal** remain open; this node assigns no policy values.
No STOP-condition resource or scope expansion was needed, so no
`DECISION_REQUIRED.md` was created.

Implementation follows the supplied design. A small reuse choice folds the new
action into the existing full-proposal/literal-confirmation branch; source
selection still invalidates the preview before field collection. Shared tests
reuse the focused booking module's direct-dispatch parity helper and extend the
existing shared fault matrix. Boundary transcripts are supplemented by separate
clean-success tests rather than making every boundary transcript a success-only
example. Fetch/publication steps are explicitly omitted under the supervisor's
no-network/no-Git-write instructions. Rust tests/Clippy and the one socket-bearing
test remain unavailable here, as documented above.

| Required delivery evidence | State |
|---|---|
| Task ID / task document | `plan-plan-local-source-quote-console`; user-supplied node/design, no node task issue/document |
| Cached base / initial and final local implementation HEAD | `2a50b8f1f7dab95b59de389e1f57db9eb88e2cc2`; no observed delta, remote freshness unverified |
| Exact final committed task head | Not created; supervisor commits the uncommitted patch |
| Independent non-author exact-head A2 review | Pending supervisor delivery |
| Exact-head KTX CI run ID/status/conclusion | Not run; no run ID/status/conclusion available |
| Exact-head KIX protocol CI run ID/status/conclusion | Not run; no run ID/status/conclusion available |
| Merge SHA / locked blobs at merge / post-merge main CI | Not applicable; no merge performed or authorized |

Builder READY is a local handoff state; it does not assert merge readiness.
Required independent exact-head review, dependency-provisioned Rust checks,
socket-bearing verification and completed/success KTX/KIX exact-head CI remain
supervisor delivery gates. User-only merge authorization remains in force.
Final-head CI evidence belongs outside a self-referential repository commit.

No production runtime, real funds, PG/bank/KYC calls, public endpoint, chain
execution, source-preview API, persistence, new protocol command or SDK binding
was added or tested. Local tests do not establish durability, distributed
fencing, external exactly-once behavior, chain finality, payment completion,
legal compliance or production readiness. Follow-up candidates are limited to
supervisor verification/publication gates and separately authorized policy or
external evidence; no next node was started in this session.
