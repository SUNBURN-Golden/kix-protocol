# Request-time calculated booking confirmation — builder evidence

Node: `plan-local-booking-calculation-inputs`. Task input is the supplied supervisor
node specification/design, with no issue or task document under `docs/tasks/`.
Non-ASTRA session; local uncommitted delivery only.

Observed cached `origin/main`, task base and initial HEAD:
`ecefde2c78fafd6e373bda67561a81f20fb7cb87`.
Branch: `agent/kix-plan-local-booking-calculation-inputs`.
Fetch omitted under the supervisor's explicit no-network instruction; remote
freshness is unverified. No base delta locally. Implementation/final commit and
merge SHA: not created (supervisor owns Git/GitHub delivery).

## Coverage mapping inspected before new tests

| Requirement | Existing coverage | Gap addressed here |
|---|---|---|
| Runtime request text, method and JSONL without startup quote source | Not covered | New method, strict booking selector inherited by shared desk; no source construction/fetch |
| Exact arithmetic, complete single-line KRW, no discounts | Sufficient calculator coverage; partial integration: `test_calculated_booking_quote_source.CalculatedBookingQuoteSourceTests.test_complete_output_matches_direct_unchanged_calculator_and_boundaries` and `invalid_texts()` | Reuse boundary corpus through request-time method; price endpoints |
| Receipt/error/state/journal parity | Partial: `test_calculated_booking_quote_source`, `test_booking_quote_adapter`, `test_ticket_operations_quotes` | Compare calculated-source/adapter controls after every new journey step |
| Source failures do not delegate or bind keys | Partial: `test_all_source_rejections_do_not_delegate_mutate_or_bind_key` in calculated source tests | Spy on new path, snapshot, reuse key; failure after success; invalid identifiers |
| Primary-price/expiry refusals, changed inputs, immutable replay | Sufficient FSM/adapter coverage; partial new path: `test_booking_quote_adapter` retained refusal/replay tests | New path parity including format-equivalent text, changed hash/amount/order/reservation, explicit clock and cancel |
| Strict envelopes, file/stdin, exits and shared isolation | Partial: `test_calculated_booking_quote_cli`, `test_ticket_operations_quotes` | Both desks with no quote flags; exit 0/1/2, stop/continue, unchanged other machines |
| No automatic downstream effects; false flags | Partial integration: `test_booking_session`, shared session tests | Full snapshots, source call counts, no payment/settlement/issuance; `assert_not_final` |

These are source-informed tests, not independent clean-room evidence. B03/B05
remain partial mock capabilities. Pricing/quote authority: **UNDETERMINED —
Astra/User**. Tax/accounting: **UNDETERMINED — User/designated advisers**.

## Implementation and changed paths

`BookingSession.confirm_calculated_quote` validates caller identifiers, calculates
once and delegates once to ordinary confirmation. Source exception normalization
surrounds calculation only, matching the existing adapter's error behavior.
`booking_cli._DISPATCH` adds a strict selector that the shared desk inherits.
No shared-session implementation change was needed.

Complete changed-path list (all new or modified files):

- `reference/booking_resale_admission/booking_session.py`
- `reference/booking_resale_admission/booking_cli.py`
- `reference/booking_resale_admission/test_booking_calculation_inputs.py`
- `reference/booking_resale_admission/test_booking_calculation_inputs_cli.py`
- `reference/booking_resale_admission/fixtures/booking_calculation_inputs_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/booking_calculation_inputs_boundaries.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_calculation_inputs_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_calculation_inputs_boundaries.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-04-plan-local-booking-calculation-inputs/README.md`

The two new test modules contain 12 tests addressing the mapped integration gaps.
Method tests exercise the existing malformed/unsupported input corpus, both
amount endpoints, calculation/confirmation call counts, unchanged receipt and
exception identity, failure after success, key reuse, changed-input conflicts,
retained price/expiry refusals, explicit clocks, cancellation and opaque metadata.
CLI tests compare receipts/errors/canonical states/digests/journals against the
existing source/adapter after every step, with no request-time source use. They
exercise both file/stdin modes without quote flags, strict envelopes, exit 0/1/2,
stop/continue behavior, historical replay/current view, flags and shared graph
isolation. Existing synthetic request texts are reused in four new fixtures;
preexisting fixtures are unchanged.

## Commands actually run and actual results

Python: **3.12.15**. Commands below ran from the repository root. The initial
focused command used `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"`. The corrected focused
run, discovery and checker wrapper used:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-booking-inputs-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary `sitecustomize.py` installs an audit hook raising `AssertionError`
for `socket.__new__`, `socket.connect`, `socket.bind` and `socket.getaddrinfo`.
New CLI subprocesses reuse the existing calculated-quote CLI harness, which
installs the same denial before import independently of environment inheritance.
Historical import probes can replace PYTHONPATH; this is not a claim of guard
inheritance for every historical child process.

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Correct worktree/branch, initially clean; cached main/base/HEAD equal the SHA above; no remote freshness claim |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: required blobs `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` match |
| Python SHA-256 snapshot using `git ls-files -z` over frozen reference, locked kernel, `.aiops` and `docs/tasks` | 121 tracked protected paths recorded before editing; final verification checks original bytes and HEAD blobs |
| `python3.12 --version` | Python 3.12.15 |
| `python3.12 -m unittest test_booking_calculation_inputs test_booking_calculation_inputs_cli` | Initial: 12 tests, one test-control error in 2.088 s; corrected source reservation identity, rerun under socket denial: **12 PASS**, 2.256 s |
| `python3.12 /tmp/kix-booking-inputs-discovery.py` (selection below) | **709 PASS**, 54.819 s; exactly one documented no-network exclusion |
| `python3.12 /tmp/kix-booking-inputs-checks.py` | All 20 subprocesses exit 0; exact commands detailed below |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; no durability/performance certification |
| `python3.12 scripts/test_runtime_architecture.py` | **7 PASS**, 0.296 s |
| `python3.12 -m unittest integration_gate.test_offline_limits` | **9 PASS**, 0.215 s |
| `python3.12 scripts/verify_commerce.py --report /tmp/kix-booking-inputs-commerce.json` | PASS: CALCULATION_ONLY, payable 48600, selected-line refund 16200, externalCalls 0 |
| `python3.12 /tmp/kix-booking-inputs-rust.py` | Rust 1.98.1; formatting PASS; four offline dependency-resolution failures, detailed below |
| `git diff --check` | PASS |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github sdk reference/v0.3-rc1` | PASS: no changes to these paths |

The initial test error was in the control: a changed caller reservation was
compared against a source entry still bound to the original reservation. The
control now uses the same reservation as the request-time call. No implementation
change was required by testing; no contract was redefined.

The checker wrapper ran each command below, with no arguments and then
`--self-test`, and inspected every exit code. Detailed local outputs are in
`/tmp/kix-booking-inputs-checks.json`.

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

The same wrapper then ran architecture verification, its tests, offline limits
and commerce verification (commands/results above). OpenAPI remains 84 commands,
SHA-256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`.
Both `.github/workflows/ktx-kernel.yml` and `protocol.yml` were inspected; these
are the applicable offline document/API/discovery and KTX equivalents, not a
claim of full protocol CI (Move/localnet/ZK/SDK/storage jobs were not run).

### Offline discovery selection

The supervisor forbids network actions, so the dependency validation record's
single loopback-test exclusion was reused. No CI file/test was edited. This
exact temporary runner executes discovery, verifies exactly one excluded test
exists and runs all remaining tests:

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

This includes all new and existing calculated-quote, booking and shared-desk
regressions except that one preexisting HTTP test. The excluded test and full
HTTP gate require the supervisor's authorized verification host.

### Rust equivalents and missing offline prerequisite

`python3.12 /tmp/kix-booking-inputs-rust.py` copied the preexisting local registry
from `/home/box/.cargo/registry` into `/tmp/kix-booking-calculation-inputs-cargo/registry`
and ran commands sequentially with this environment, without downloads:

```bash
export CARGO_HOME=/tmp/kix-booking-calculation-inputs-cargo
export CARGO_TARGET_DIR=/tmp/kix-booking-calculation-inputs-target
export CARGO_NET_OFFLINE=true
export RUSTUP_TOOLCHAIN=1.98.1
```

| Command | Actual result |
|---|---|
| `cargo --version`; `rustc --version`; `rustup toolchain list` | Installed/active toolchain 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101: cached `bcs` package missing; no tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101: cached `bcs` missing; no lint result |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101: cached `bcs` missing; no tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101: cached `bcs` missing; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

These four commands remain **unverified**, not passes. Detailed local outputs
are in `/tmp/kix-booking-inputs-rust.json`. An offline cache containing the locked
workspace dependencies or authorized CI must supply this prerequisite; no
network installation, Cargo/workflow edit or automatic retry was attempted.

## Preservation, deviations and delivery gates

The final preservation check compares all 121 pre-snapshot SHA-256 values to
working bytes and HEAD Git blobs, verifies the exact 11-path change allowlist,
checks Python/JSONL syntax, unchanged existing fixtures, unchanged HEAD/base/branch and
whitespace. Its exact command/result is appended after execution below.

Design deviations: none in the implementation. Recording-only absence and
record-reservation mismatch rows are omitted from the new request-text fixtures
because no recording is selected. Invalid calculation requests and changed
booking identities remain covered. Shared graph implementation is reused.
Verification deviations are the explicit no-fetch/no-network restriction, one
loopback exclusion and unavailable offline Rust dependency, all disclosed above.

No contract violations were found. Existing undefined authority/policy values
remain undefined: calculation metadata is opaque hash-bound data, not booking
identity/currentness validation. No new policy, protocol command, pricing/quote
authority or tax/accounting treatment was chosen. No STOP condition required a
product decision; no `DECISION_REQUIRED.md` was created.

No commit/push/PR/issue/comment/merge, tag/ref change, hardware, paid service,
secret, production runtime, real funds, provider call, public endpoint or Sui
execution was performed. No automatic payment, issuance, retry or clock change
was added. This proves local composition and in-memory regressions only, not
production readiness, durability, distributed fencing, bank exactly-once,
chain finality or legal compliance. B03/B05 remain partial; CALCULATION_ONLY
calculations and MOCK_GATE_ONLY receipts retain their distinct flags.

Implementation/final task commit: **not created**; initial HEAD remains the SHA
above, with this uncommitted patch for the supervisor. Non-author **A2 exact-head
review** and required exact-head CI remain delivery gates:

| Gate | Run ID | Status/conclusion |
|---|---|---|
| KTX kernel verification, final supervisor commit | Not available | Not run/unverified |
| KIX protocol verification, final supervisor commit | Not available | Not run/unverified |
| Non-author A2 review | Not available | Pending |
| Merge commit and main/push post-merge CI | Not applicable | No merge authorized/performed |

Local implementation is ready for supervisor review; no merge-ready claim.
Remaining follow-up is dependency-complete Rust verification, the excluded
loopback test/full required CI and non-author review on the supervisor's final
commit. Authority/policy decisions stay with their named owners.

Final preservation command: `PYTHONDONTWRITEBYTECODE=1 python3.12 /tmp/kix-booking-inputs-final.py`
— **PASS**: all 121 protected paths match their initial SHA-256 and HEAD bytes;
exact 11-path allowlist; Python/JSONL syntax, preexisting fixtures, HEAD/base/branch
and whitespace checks pass. This includes byte-identical `reference/v0.3-rc1/**`
and both locked kernel blobs. `python3.12 scripts/check_docs_index.py` was also
rerun after completing this report: **PASS**, scanned 347, indexed 312,
allowlisted 35. Final merge blob verification is not applicable (no merge).
