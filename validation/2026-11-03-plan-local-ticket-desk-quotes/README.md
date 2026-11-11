# Recorded quotes on the shared ticket desk — builder evidence

Task: `plan-local-ticket-desk-quotes`. Immutable task input: the supervisor's
node specification and design supplied in this session; no issue or task file
exists. This is not ASTRA program mode. Branch:
`agent/kix-plan-local-ticket-desk-quotes`.

Initial HEAD/base/cached `origin/main`:
`15ea27bdf82bce3a32ce7627ceb6e52fd8965eed`. No local base delta. The supervisor's
explicit no-network instruction overrides the AGENTS §1 fetch requirement;
remote freshness remains unverified. No commit, publication or history change
is authorized. Implementation and final delivery commit SHAs belong to the
supervisor's later publication, not this uncommitted worktree.

## Coverage mapping recorded before adding tests

Paths below are relative to `reference/booking_resale_admission/`.

| Acceptance | Existing evidence / classification | Shared composition gap |
|---|---|---|
| One graph, explicit clock/register/hold/recorded confirmation/view | Partial: `test_ticket_operations_session.py::test_one_shared_graph_per_construction_and_custom_inputs`; standalone quote transcripts | Adapter identity, constructor purity, shared recorded journey |
| Unchanged receipts/errors | Partial: `test_booking_quote_adapter.py::test_histories_match_receipts_errors_state_digest_journal_after_every_step` | Shared routing versus direct adapter on independently constructed equivalent graph after each step |
| Alias/conflicting replay, bindings, historical/current views | Partial: `test_booking_quote_adapter.py::test_replay_alias_changed_quote_amount_order_and_binding_parity` | Shared and setup/delegated key collisions, replay after cancellation |
| Missing, malformed, mismatched, fault recordings | Sufficient adapter evidence: `test_missing_bad_json_and_faults_no_fsm_call_or_key_binding`, `test_invalid_record_shapes_scalars_and_binding_never_delegate_or_bind_key` in `test_booking_quote_adapter.py` | Shared error envelopes and continuation |
| Source failure after success; one fetch; no retry/fallback | Partial: `test_booking_quote_adapter.py::test_source_failure_after_success_never_falls_back_to_retained_receipt`; invalid caller coverage | Shared runner fetch accounting and scripted failure recovery |
| Pre-delegation rejection preserves FSM and keys | Partial: adapter rejection tests above | All-four-machine snapshots, confirmation spy and successful same-key reuse |
| No payment, settlement or issuance effects | Partial: `test_booking_quote_cli.py::test_file_and_stdin_transcripts_reach_confirmed_without_downstream_effects` | New booking has null downstream fields, zero payment count; unrelated shared state and source calls unchanged |
| Existing fixtures, unconfigured behavior and resale/admission compatibility | Sufficient baseline: existing booking/shared session/CLI tests and transcripts | Run unchanged transcripts with/without configured quote adapter |
| File/stdin output and exits 0/1/2 | Partial: standalone quote CLI tests; existing shared CLI tests | Shared quote transcripts and malformed/fixture/clock failure precedence |
| Documentation, OpenAPI and discovery | Existing repository checker scripts and workflows | Run applicable local checks, preserve normal HTTP and final-head CI gates |

The initial locked working blobs match the required values:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.
Protected paths and preexisting fixtures have a separate before-work byte hash
snapshot in `/tmp/kix-desk-quotes-protected-before.json`.

## Implementation and focused evidence

The only implementation change is shared CLI composition: keyword-only
`quote_adapter=None` on `dispatch_request` and `run_requests`, booking-only
forwarding, optional `--quotes` using the existing source fixture loader and an
adapter bound to `session.booking`, and continuing `BookingQuoteSourceError`
handling. Existing schema/selector validation, source, adapter, session and FSM
code are reused unchanged. No additional reservation machine is constructed.

`test_ticket_operations_quotes.py` fills the mapped integration gaps:

- Constructor spy proves exactly one reservation machine, adapter identity with
  the existing booking session, zero construction fetches and no implicit booking
  clock initialization. Fixture setup clocks alone do not initialize the session.
- Both transcripts compare shared dispatch to direct adapter/session execution
  on a separately constructed equivalent four-machine graph after every line.
  Receipts, errors, canonical state, digests, journals and fetch histories agree.
- Alias/changed quote/changed amount/changed order replays, order binding,
  cross-operation/setup/delegated-admission key collisions and retained FSM price
  refusals preserve existing errors. Boundary replay after cancellation returns
  the historical CONFIRMED receipt while the current view is CANCELLED.
- Missing, malformed-schema, invalid-JSON, duplicate-key, nonfinite, mismatched
  and both immediate fault recordings never call `BookingSession.confirm` and
  leave all four snapshots unchanged. A subsequent valid confirmation with the
  identical caller key succeeds, proving more than business-state snapshots alone.
- Invalid caller identifiers never fetch. Structurally invalid requests stop
  without fetching. A scripted success/missing/timeout/source-failure/success
  sequence fetches exactly once per invocation, delegates only on valid records,
  preserves exception identity/cause and never falls back to a retained success.
  Session, domain and unexpected programming exception identities are preserved.
- New booking fields `payment_ref`, `settlement_id`, `issuance_id`, `right` stay
  null; its separate show has zero payment references. Exactly one new accepted
  confirm journal entry appears. Settlement/resale/admission snapshots, original
  issued reservation view and unrelated source call histories remain unchanged.
- Every new file/stdin output row and exits 0/1/2 are asserted, including stopping
  malformed/clock errors after source refusals. File, encoding and fixture failures
  exit 2; embedded quote validation stays lazy. All eight existing shared journeys
  behave identically with/without the optional source, and unconfigured recorded
  confirmation remains unsupported. No existing fixture bytes were changed.

The new confirm transcript has 7 rows, exit 0. The boundary transcript has 20
rows, exit 1, including source failure after success, retained price refusal,
conflicting replay and second-hold expiry. Their IDs are separate from the shared
fixture's existing synthetic issued inventory. Existing flags stay unchanged.

## Commands actually run and results

All commands ran in the foreground. No network, Git/GitHub mutation, publication,
background job or external service was used. Tests are source-informed local
evidence; counts overlap and must not be summed.

Python is **3.12.15**, matching the workflow's 3.12 series (the default `python3`
is 3.13.5 and was used only for initial inspection/hash-helper setup). The
verification environment, inherited by transcript subprocesses, was:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-desk-quotes-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-desk-quotes-no-sockets/sitecustomize.py` contains:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean, expected branch, HEAD/base/cached main equal the SHA above; unchanged after work |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before and after: both exact required blobs |
| Initial Python hash snapshot of tracked protected paths and preexisting fixtures | PASS after correcting quoted Unicode filenames to use `git ls-files -z`; 280 paths recorded before implementation |
| `python3.12 -m unittest test_ticket_operations_quotes` | First: 12 tests, one test-only line-ending assertion failure; after correction: **12 PASS**, 2.633 s |
| `python3.12 -m unittest test_booking_quote_source test_booking_quote_adapter test_booking_quote_cli test_booking_session test_booking_cli test_ticket_operations_session test_ticket_operations_cli test_resale_session test_resale_cli test_admission_session test_admission_cli` | **118 PASS**, 9.954 s |
| `python3.12 /tmp/kix-desk-quotes-offline.py` (selection below) | First invocation stopped on duplicate test-module name due to path order; corrected documented ordering: **599 PASS**, 21.053 s; exactly one HTTP exclusion asserted |
| `python3.12 -m unittest integration_gate.test_offline_limits` | **9 PASS**, 0.251 s |
| `python3.12 /tmp/kix-desk-quotes-transcripts.py` | PASS: four foreground CLI invocations, 7/20 asserted rows, expected exits 0/1, file/stdin outputs identical; documented Python dispatch/runner composition also passed |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3.12 scripts/test_runtime_architecture.py` | **7 PASS**, 0.205 s |
| `python3.12 /tmp/kix-desk-quotes-final.py` | PASS: exactly nine expected changed paths, Python/JSON/JSONL/whitespace checks, initial refs unchanged, all 280 protected and preexisting fixture byte hashes match baseline and HEAD |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github sdk reference/v0.3-rc1` | PASS: no changes |
| `git diff --check` | PASS |

The malformed-JSON test initially compared a line without a trailing newline
to a file line with one, causing different JSON decoder locations in the otherwise
identical error. The expected input now includes actual line endings. The initial
hash helper also needed NUL-separated Git filenames rather than quoted display
names. Neither failure required an implementation or contract change.

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. The following
commands each ran plainly and with `--self-test`, sequentially through
`python3.12 /tmp/kix-desk-quotes-checks.py`; all actual subprocess statuses were
checked. That runner also ran both architecture commands above. Detailed output
is retained locally in `/tmp/kix-desk-quotes-check-results.json`.

| Command | Plain | `--self-test` |
|---|---|---|
| `python3.12 scripts/check_docs_index.py` | PASS | PASS |
| `python3.12 scripts/check_bra_evidence_map.py` | PASS | PASS |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py` | PASS | PASS |
| `python3.12 scripts/check_contract_error_codes.py` | PASS | PASS |
| `python3.12 scripts/check_ci_test_discovery.py` | PASS | PASS |
| `python3.12 scripts/check_ci_checker_wiring.py` | PASS | PASS |
| `python3.12 scripts/check_openapi_contract.py` | PASS | PASS |
| `python3.12 scripts/check_integration_gate_openapi.py` | PASS | PASS |

OpenAPI pin remains
`ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`
(84 commands). All eight plain checks and the final preservation script were
also rerun after completing this record; their results are reported by the
supervisor handoff. No checker/workflow was edited.

### Exact socket-denied discovery selection

The initial discovery wrapper omitted the documented explicit `sys.path` insert;
an imported settlement test module with the same name took precedence. Using the
previous booking-surface record's ordering fixed this invocation issue, without
editing any test module. `/tmp/kix-desk-quotes-offline.py` contains:

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

This is partial local coverage, not a full-suite/full-CI pass. The excluded HTTP
test and `integration_gate.test_http_gate` remain unchanged and required in normal
CI. Some unchanged import-only probes replace `PYTHONPATH`; socket-guard inheritance
is claimed for the new transcript children, not for those old probes.

### Rust checks and unavailable prerequisites

Used installed workflow-pinned **cargo/rustc 1.98.1** with no downloads. Copied the
existing `/home/box/.cargo/registry` into `/tmp/kix-desk-quotes-cargo/registry`, then
ran `python3.12 /tmp/kix-desk-quotes-rust.py` sequentially with:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/home/box/.local/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-desk-quotes-cargo
export CARGO_TARGET_DIR=/tmp/kix-desk-quotes-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version`; `rustc --version` | Both 1.98.1, workflow version |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable: exit 101, cached `bcs` missing; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Unavailable: exit 101, cached `bcs` missing; no lint result |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable: exit 101, cached `bcs` missing; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable: exit 101, cached `bcs` missing; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

The four dependency-resolution failures are limitations, never passes. No Rust
file was modified and no network retry or prerequisite installation was attempted.

## Complete changed-path list and preservation

- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_quotes.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_booking_quotes.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_recorded_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_recorded_boundaries.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-03-plan-local-ticket-desk-quotes/README.md`

Both locked working blobs match before and after:

| File | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The final preservation script independently hashes working bytes as Git blobs
against HEAD and compares SHA-256 against the initial snapshot throughout
`runtime`, `.aiops`, `docs/tasks`, `docs/contracts`, `.github`, `sdk`,
`reference/v0.3-rc1` and every preexisting booking fixture (280 files).
The preserved `reference/v0.3-rc1` tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
Session/fixture constructors, all FSMs, authoritative contracts and existing
fixtures are unchanged. No protected file was transiently edited.

## Classification, deviations, limits and remaining delivery gates

Class A: exercised confirmation, binding, replay, refusal and error behavior match
the unchanged adapter/session/FSM contract. No explicit contract violation found;
no newly discovered contract-undefined characterization. Pricing, discounts and
quote authority remain **UNDETERMINED — Astra/User**. No policy was chosen.

No implementation deviation from the supplied design was needed. Three extra
synthetic recordings (invalid JSON, duplicate fields and nonfinite JSON) cover
shared pre-delegation refusal gaps. Invocation corrections are recorded above.
AGENTS §1 fetch was omitted under the explicit supervisor no-network rule.
Rust tests/Clippy require an offline dependency cache including `bcs`, or the
normal authorized CI environment. These prerequisites are not repaired by
editing the repository or fetching packages here.

This is complete local implementation for supervisor handoff, not merge-ready.
Initial and final worktree HEAD remain `15ea27bdf82bce3a32ce7627ceb6e52fd8965eed`;
the implementation is uncommitted. No implementation/final delivery commit,
merge commit, PR or external CI run was created or queried. Exact-head KTX and
KIX status/conclusion/run IDs are **unverified / unavailable**, not inferred
from older evidence. Non-author A2 exact-head review, unchanged full HTTP
coverage, both exact-final-head workflows completed/success, user merge
authorization and post-merge verification remain supervisor delivery gates.
There is no post-merge CI result or final-merge locked-blob check in this session.

No claims of authenticated pricing, clean-room independence, payment handoff,
automatic settlement/issuance, production durability, real funds/provider calls,
network/HTTP coverage, chain execution/finality, legal compliance or runtime
activation are made. No persistence, SDK/catalogue, protocol command, production
runtime or new storage/replication engine is introduced. No out-of-node follow-up
was implemented. The remaining follow-up is the supervisor's publication and
required independent/final-head verification, not a new product-policy decision.
