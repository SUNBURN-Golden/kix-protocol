# Calculation-only booking quote preview — builder evidence

Node: `plan-local-booking-quote-preview`. Task input is the supplied supervisor
node specification and read-only design; no issue or `docs/tasks/` document exists
for this node. Non-ASTRA, single-writer local delivery; supervisor owns Git/GitHub.

Observed cached `origin/main`, task base and initial HEAD:
`633e4361b9768ec21a999404b63303e92651c017`.
Branch: `agent/kix-plan-local-booking-quote-preview`. Initial worktree clean.
Fetch omitted under the supervisor's explicit no-network instruction. Remote
freshness is unverified; no local base delta. Implementation/final commit and
merge SHA are not created in this session; HEAD remains the initial SHA, with
an uncommitted patch for the supervisor.

## Coverage mapped before adding tests

| Requirement | Existing classification and exact controls | New gap coverage |
|---|---|---|
| Complete unchanged calculator result, exact atoms, hash and CALCULATION_ONLY | Sufficient calculator coverage; preview integration absent: `test_calculated_booking_quote_source.CalculatedBookingQuoteSourceTests.test_complete_output_matches_direct_unchanged_calculator_and_boundaries`, `invalid_texts()` | Full result equality, formatting equivalence, amount endpoints and shared/standalone dispatch rejection corpus |
| No reservation access, state mutation, clock requirement, key binding or automatic confirmation | Partial: `test_booking_session.BookingSessionTests.test_views_without_session_clock_are_nonmutating_and_detached`; shared `test_ticket_operations_session.snapshot`/`machines`; no preview path | No-access machine sentinel; guarded clock/confirmation/source methods; all four shared machine canonical states/digests/journals; explicit clock flag and all configured source histories |
| Repeated results detached; errors never return cached success | Partial: `test_calculated_booking_quote_source.CalculatedBookingQuoteSourceTests.test_storage_results_and_calls_are_detached_and_fetch_recalculates` | Nested request/asset/line/totals mutations, one calculation per call, source exception identity and unexpected-exception normalization |
| Subsequent explicit confirmation retains amount/hash, price, expiry and replay | Sufficient existing confirmation checks, preview sequence absent: `test_booking_calculation_inputs.BookingCalculationInputsTests.test_price_expiry_and_amount_endpoints_match_adapter_with_retained_refusals`, `test_adapter_parity_for_replay_changed_inputs_binding_clock_and_cancel` | Control sessions with no previews; receipt/state/journal equality after each step, fresh key after rejected previews, missing clock, retained refusals, changed-input conflict, historical confirmation replay after cancellation/expiry |
| Strict envelopes, file/stdin and exits on both desks | Partial: `test_booking_calculation_inputs_cli.BookingCalculationInputsCliTests` and existing socket-denial subprocess harness in `test_calculated_booking_quote_cli.CalculatedBookingQuoteCliTests.cli` | Four new runnable transcripts; both file/stdin modes; duplicate keys/malformed JSON stop with 2; invalid inner calculation continues with 1; success exits 0 |

Snapshots omit some receipt bookkeeping. The no-access sentinel and no-preview
control-session confirmation/replay comparisons supplement them. Shared setup
precedes each isolation baseline; existing setup mutations are not preview effects.
Tests are source-informed, not independent clean-room evidence.

## Implementation and complete changed-path list

`BookingSession.preview_calculated_quote` calls `calculate_booking_quote` exactly
once and returns its complete result unchanged. Source exceptions pass through;
unexpected calculation exceptions use existing confirmation normalization.
`booking_cli._DISPATCH` adds the strict `request_text`-only selector returning
`quote`. Shared CLI reuses its existing booking delegation. Confirmation,
calculator and FSM implementations are unchanged.

- `reference/booking_resale_admission/booking_session.py`
- `reference/booking_resale_admission/booking_cli.py`
- `reference/booking_resale_admission/test_booking_quote_preview.py`
- `reference/booking_resale_admission/test_booking_quote_preview_cli.py`
- `reference/booking_resale_admission/fixtures/booking_quote_preview_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/booking_quote_preview_boundaries.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_quote_preview_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_quote_preview_boundaries.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-04-plan-local-booking-quote-preview/README.md`

## Commands actually run

Results are recorded below after execution. No previous node's test/CI result is
transferred to this patch.

Python **3.12.15**, Rust/Cargo **1.98.1**. Commands ran from the repository root.
The initial focused command used:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"
python3.12 -m unittest test_booking_quote_preview test_booking_quote_preview_cli test_calculated_booking_quote_source test_booking_calculation_inputs test_booking_calculation_inputs_cli
```

Focused result: **31 tests PASS**, 6.421 s (12 new preview tests). CLI children
install the existing socket-denial audit hook before importing the CLI.
Subsequent Python suite/checker/transcript commands used:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-preview-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary `sitecustomize.py` raises `AssertionError` for `socket.__new__`,
`socket.connect`, `socket.bind` and `socket.getaddrinfo`. Some historical child
import probes replace PYTHONPATH; this is not a claim of guard inheritance in
every historical subprocess. The new CLI tests reuse the independent child
socket-denial harness. No listener or external service was used.

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Correct worktree/branch, initially clean, local base/HEAD equal the SHA above; no fetch or remote freshness claim |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before editing; final check below repeats verification |
| Inline `python3.12` SHA-256 snapshot over `git ls-files -z` | Recorded 324 protected tracked files before edits in `/tmp/kix-preview-preservation.json`: runtime, frozen reference, `.aiops`, task documents, contracts, SDK, `.github`, existing booking fixtures |
| `python3.12 --version`; `cargo --version`; `rustc --version` | Python 3.12.15; Cargo and rustc 1.98.1 |
| Focused unittest command above | **31 PASS**, 6.421 s |
| `python3.12 /tmp/kix-preview-discovery.py` (exact selection below) | **729 PASS**, 66.492 s; one explicit preexisting HTTP loopback exclusion |
| `python3.12 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | **224 PASS**, 1.770 s |
| `python3.12 /tmp/kix-preview-checks.py` | All 20 child commands exit 0; detailed below |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance not certified |
| `python3.12 scripts/test_runtime_architecture.py` | **7 PASS**, 0.208 s |
| `python3.12 -m unittest integration_gate.test_offline_limits` | **9 PASS**, 0.280 s |
| `python3.12 scripts/verify_commerce.py --report /tmp/kix-preview-commerce.json` | PASS: CALCULATION_ONLY, payable 48600, selected-line refund 16200, externalCalls 0 |
| `python3.12 /tmp/kix-preview-rust.py` | Wrapper exit 1: four offline dependency-resolution failures; formatting passes; details below |
| `python3.12 /tmp/kix-preview-transcripts.py` | Eight documented CLI invocations have expected exits and identical file/stdin output; detailed below |
| `git diff --check` | PASS |
| `git diff --stat`; scoped `git diff`; `git status --short` | Inspected the two implementation additions, docs and complete untracked-path list; no unrelated changes |

The checker wrapper invoked every command below normally and with `--self-test`,
then architecture verification/tests, offline limits and commerce verification.
It recorded each child's exit/stdout/stderr in `/tmp/kix-preview-checks.json`.

| Command | Normal | `--self-test` |
|---|---|---|
| `python3.12 scripts/check_docs_index.py` | PASS (349 scanned, 314 indexed, 35 allowlisted) | PASS |
| `python3.12 scripts/check_bra_evidence_map.py` | PASS | PASS |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py` | PASS | PASS |
| `python3.12 scripts/check_contract_error_codes.py` | PASS | PASS |
| `python3.12 scripts/check_ci_test_discovery.py` | PASS | PASS |
| `python3.12 scripts/check_ci_checker_wiring.py` | PASS | PASS |
| `python3.12 scripts/check_openapi_contract.py` | PASS | PASS |
| `python3.12 scripts/check_integration_gate_openapi.py` | PASS | PASS |

OpenAPI remains 84 commands, SHA-256
`ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`.
Both `.github/workflows/ktx-kernel.yml` and `protocol.yml` were inspected. These
checks are the applicable offline Python, document/API/discovery and KTX local
equivalents; they do not replace full required exact-head CI.

### Offline discovery selection

The no-network instruction requires the dependency validation record's single
loopback-test exclusion. No repository test or workflow is modified. The exact
runner used is reproducible from this code:

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
print('Explicit no-network exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(
    test for test in tests if test.id() != excluded))
sys.exit(not result.wasSuccessful())
```

All new tests and affected existing offline suites pass. The single excluded
HTTP test is **unverified**, not a pass. Full HTTP gate, Move/localnet/ZK/SDK and
storage jobs were not run for this Python-only patch.

### File/stdin transcripts

`python3.12 /tmp/kix-preview-transcripts.py` executed the commands below under
socket denial, parsed every output row, checked expected exits and empty stderr,
and compared complete file/stdin output for each pair. Detailed invocation
records are in `/tmp/kix-preview-transcripts.json`. In the table:

- `D=reference/booking_resale_admission`
- `F=$D/fixtures/ticket_operations_session.json`
- `P=$D/fixtures/<fixture name>`

| Commands actually executed, with each indicated path expanded | Fixture name | Result, each mode |
|---|---|---|
| `python3.12 -B $D/booking_cli.py --requests $P`; `python3.12 -B $D/booking_cli.py --requests - < $P` | `booking_quote_preview_confirm.jsonl` | Exit 0; 10 rows; identical |
| Same two standalone commands | `booking_quote_preview_boundaries.jsonl` | Expected exit 1; 31 rows; identical |
| `python3.12 -B $D/ticket_operations_cli.py --fixture $F --requests $P`; `python3.12 -B $D/ticket_operations_cli.py --fixture $F --requests - < $P` | `ticket_operations_quote_preview_confirm.jsonl` | Exit 0; 10 rows; identical |
| Same two shared commands | `ticket_operations_quote_preview_boundaries.jsonl` | Expected exit 1; 31 rows; identical |

The focused CLI tests also run malformed outer JSON/duplicate-key transcripts
from both temporary files and stdin: exit 2, exactly one error row, later valid
preview not executed. Invalid inner calculation values continue to a valid
preview with exit 1 and require no clock. In-process structural variants include
extra/missing fields, non-object arguments, wrong/missing shared surfaces and
forbidden clock/reservation/key/amount arguments; calculation is never called.

### Offline Rust prerequisite failure

The Rust wrapper copied the existing local registry from
`/home/box/.cargo/registry` into `/tmp/kix-preview-cargo/registry` without downloads.
It used the installed toolchain directly with:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-preview-cargo
export CARGO_TARGET_DIR=/tmp/kix-preview-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101: no matching cached package `bcs`, required by workspace `kix-bcs1`; no tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101: same missing `bcs`; no lint result |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101: same missing `bcs`; no tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101: same missing `bcs`; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

Detailed child results are in `/tmp/kix-preview-rust.json`. The four failed
commands are verification blockers, **not passes**. Supplying a complete offline
cache or running on the supervisor's authorized CI host is required. No network
fetch, dependency substitution, manifest/workflow edit or automatic retry was
attempted. No Rust source was touched.

## Preservation, deviations, uncertainty and delivery gates

Implementation follows the design without deviation. The four fixtures extend
existing synthetic calculation-input journeys with preview before session setup
and before each explicit confirmation; source-recording-only boundaries stay in
existing tests. Strict malformed outer envelopes are executable temporary
file/stdin transcripts in the CLI tests, so the four checked-in journeys can
continue through domain refusals to historical replay.

Verification deviations: fetch omitted by explicit supervisor instruction; one
preexisting loopback test excluded; four Rust commands blocked by the missing
offline `bcs` dependency. These are not successful or waived CI checks.

The final preservation command below verifies all 324 initial SHA-256 snapshots
against both working bytes and their HEAD blobs, the exact 11-path change list,
new Python/JSONL syntax, branch/HEAD/base identity and whitespace. Both kernel
blob IDs must still be:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Initial frozen-reference tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
All `reference/v0.3-rc1/**` bytes are included in preservation verification.
Contracts, SDK, `.aiops/`, task documents, CI, calculator, FSMs, existing fixtures
and confirmation implementation remain unchanged.

No explicit contract violations were found. No new undefined semantics were
invented. Existing calculation metadata (`orderId`, scope, `expiresAt`) remains
opaque and hash-bound, independent of reservation identity/expiry. Pricing/quote
authority remains **UNDETERMINED — Astra/User**; tax/accounting remains
**UNDETERMINED — User/designated advisers**. B03/B05 remain partial mock
capabilities. No product decision or STOP-condition resource was needed, so no
root `DECISION_REQUIRED.md` is created. Missing offline dependencies are an
external verification prerequisite, not a product-policy choice.

No commit, push, issue, PR, comment, merge, tag/ref modification, public endpoint,
provider call, secrets, paid service, real funds, production runtime or Sui
execution was performed. No background job, automatic retry or polling routine
was created. This evidence is local and in-memory only. It establishes no
production readiness, authenticated quote authority, durability, distributed
fencing, bank exactly-once, chain finality, legal compliance or tax treatment.

Implementation/final task commit: **not created**, initial HEAD unchanged.
Merge SHA/final-merge blob verification/post-merge CI: **not applicable**.
The supervisor must preserve normal delivery gates on its eventual final commit:

| Gate | Run ID | Status/conclusion |
|---|---|---|
| KTX kernel verification, exact final supervisor head | Not available | Not run/unverified |
| KIX protocol verification, exact final supervisor head | Not available | Not run/unverified |
| Non-author A2 exact-head review | Not available | Pending |
| Main/push post-merge CI | Not applicable | No merge performed/authorized |

Local implementation is ready for supervisor handoff, with the disclosed
verification blockers; **no merge-ready claim**. Follow-up is dependency-complete
Rust verification, the excluded HTTP test, exact-head KTX/KIX CI and non-author
review after the supervisor commits. No prior SHA's CI is transferred.

Final preservation command: `PYTHONDONTWRITEBYTECODE=1 python3.12 /tmp/kix-preview-final.py`
— **PASS**: all 324 protected tracked files match initial SHA-256 and HEAD bytes;
both required locked blobs match; exactly the 11 listed paths changed; Python/JSONL
syntax, whitespace, unchanged branch/HEAD/base and frozen-reference tree checks
pass. `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github sdk reference/v0.3-rc1`
also passes. Final merge verification is not applicable (no merge).

After completing the evidence text, `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_docs_index.py`
was rerun — **PASS**, 349 scanned, 314 indexed, 35 allowlisted.
