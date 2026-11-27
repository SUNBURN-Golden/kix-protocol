# Guided synthetic split-payment entry — builder evidence

Node: `plan-local-split-payment-entry`. Task input is the immutable user-supplied
node specification and design plan in this session; no issue or task document
exists. This is not ASTRA program mode. The supervisor owns commits/publication.

Initial branch: `agent/kix-plan-local-split-payment-entry`. Observed local
`origin/main`, base and task HEAD: `9cf77508d42ddf4891279e8fdb49d3a0bcd15eec`.
The worktree was clean. Fetch was omitted under the explicit supervisor rule
forbidding network; remote freshness is unverified. No base/ref was changed.
Implementation/final task head is uncommitted, pending supervisor delivery.

## Coverage mapped before adding tests

| Requirement | Existing coverage / classification | Guided gap addressed |
|---|---|---|
| Existing client and file console behavior | Sufficient: `test_commerce_calculation_client.py` and existing `CommerceCalculationConsoleTests` | Retained unchanged file journeys alongside new tests |
| Split plan and selected-line refund | Arithmetic sufficient: `CommerceTests.test_bundle_discount_payment_split_and_failed_line_refund_calculation`, `test_every_refund_subset_conserves_original_route_and_discount_shares` in frozen `test_commerce.py`; guided input absent | `test_guided_split_refund_journey_and_file_parity`: exact requests/replies for journey, free and precision |
| Free array / large atom strings | Partial: console `test_free_and_large_atom_journeys_preserve_wire_strings_and_empty_routes`, frozen `test_free_quote_needs_no_money_and_refund_has_no_payment_route`, `test_exact_zero_two_six_and_eighteen_decimal_asset_profiles` | Guided zero count, exact `9007199254740993` strings, empty original routes |
| Driver refusals | Arithmetic sufficient: frozen `test_expiry_and_amount_mismatch_reject_without_payment_plan`, `test_mixed_assets_and_aggregate_overflow_are_rejected`; guided visibility absent | `test_guided_driver_refusals_are_visible_without_correction_or_retry`: four exact errors, one request per submission; paid quote with explicit empty legs refused |
| Replacement invalidation | Partial: existing console quote/legs/plan replacement tests | `test_guided_replacement_invalidates_plan_refund_and_selection`: identical, malformed count/decimals, failed CE1 encoding; quote/history preserved, old selections unusable |
| Consent, EOF, uncertainty | Partial: existing submission decline, EOF, transport and client fencing tests | `test_guided_eof_at_every_prompt_and_decline_submit_nothing_further`, `test_guided_plan_uncertainty_fences_after_successful_quote` |
| Exact caller fields, order and CE1 | File decoding sufficient; new composition absent | `test_guided_literal_strings_order_and_driver_owned_validation`, `test_guided_integer_and_encoding_failures_never_publish_candidate`: terminators only, no normalization/defaults, integer token/type checks, Unicode/size encoding failures |

Tests are source-informed composition evidence, not independent arithmetic
verification or non-author A2 review. No allocation algorithm was copied.

## Implementation and transcripts

`compose_legs` invalidates legs/plan/refund/selection before reading input. It
collects an explicit count bounded by the loaded driver's `MAX_LEGS`, then all
fields in entered order. Only count/decimals use lossless CE1 integer parsing;
other fields stay literal strings. Candidate bytes become active only after
complete successful CE1 encoding. The console displays the full composed array
and returns to the menu. The existing separately consented `plan_payments`
request owns the explicit clock and passes the array to the unchanged client
and driver. Totals, asset validity, expiry, allocations and refunds remain there.

Six runnable input transcripts are under the existing fixtures directory:
`commerce_console_guided_{journey,free,precision,boundaries,replacement,decline}.txt`.
Their actual stdout/stderr are in this evidence directory. `show` deliberately
renders historical successes again; printed `driver=` lines are not request
counts. Tests inspect recorded exchanges for request counts and exact parity.

- Journey: explicit card/bank plan at `999`, then selected `L2` refund.
- Free: count `0`, empty plan legs and refund original routes.
- Precision: exact `"9007199254740993"` in entered/request/refund atom strings.
- Boundaries: explicit duplicate legs, asset mismatch, wrong total and expired
  quote; exact errors visible, expected console exit `1`.
- Replacement: identical composition clears active plan/refund/selection;
  recalculating the plan still requires a new explicit line selection.
- Decline: quote only; no plan request after declining `SUBMIT_PLAN`.

## Actual commands and results

[command-results.json](command-results.json) contains exact argument arrays,
exit codes and elapsed times. Each label has corresponding stdout/stderr files.
Python commands use Python 3.12.15, `-B`, `PYTHONDONTWRITEBYTECODE=1`, and unset
`PYTHONPATH`, except the documented socket-free broader discovery environment.
The local runner captures foreground subprocess output without background jobs.

| Command actually run | Result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Clean initial worktree; expected branch; both refs at the SHA above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before and after |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_calculation_*.py' -v` | Exit 0: 25 tests in 10.381 s |
| `(cd reference/v0.3-rc1 && python3.12 -B -m unittest test_commerce test_commerce_driver)` | Exit 0: 27 tests in 0.350 s |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce.json` | Exit 0: PASS, synthetic payable 48600 / selected refund 16200, externalCalls=0 |
| `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_guided_journey.txt` | Exit 0 |
| Same console command with guided free, precision, replacement and decline transcripts | All exit 0 |
| Same console command with guided boundaries transcript | Expected exit 1: DUPLICATE_PAYMENT_LEG, PAYMENT_ASSET_MISMATCH, PAYMENT_TOTAL_MISMATCH, QUOTE_EXPIRED |
| `python3.12 -B .local/split-payment/socket_free.py` (initial runner) | Exit 1 before tests: import-order collision; corrected runner order |
| `python3.12 -B .local/split-payment/socket_free.py` (corrected) | Exit 0: 892 tests in 112.054 s; exactly one documented HTTP exclusion |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_status_register.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_bra_evidence_map.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both exit 0; 84-command pin unchanged |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0: architecture gate OK |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0: 7 tests |
| `cargo --version`; `rustc --version` | Both exit 0: 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: missing cached `bcs`; tests did not run |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: missing cached `bcs`; tests did not run |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: missing cached `bcs`; lint did not run |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: missing cached `bcs`; lint did not run |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `python3.12 -B .local/split-payment/preserve.py` | Exit 0: 1,567 non-task tracked files unchanged, 108 frozen files byte-identical, both locks match, refs unchanged, changed Python ASTs valid |
| `git diff --check` | Exit 0 |

Rust commands used the provisioned 1.98.1 toolchain, with its bin directory first
on PATH, `CARGO_NET_OFFLINE=true`, writable `CARGO_HOME=.local/split-payment/cargo`
and `CARGO_TARGET_DIR=.local/split-payment/target` (absolute paths). The existing
53 MB registry was copied locally; no network was attempted. Missing prerequisites
are unavailable verification, not passing tests. No Rust source changed.

Broader discovery uses the workflow's exact start/top-level directories and
filters only
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The runner asserts exactly one such ID and no duplicate IDs, then runs every
other test. The parent imports a guard after placing the booking suite first on
`sys.path`; its audit hook raises on every event starting with `socket.`.
Children inherit `PYTHONPATH` containing the guard directory, booking suite and
repository root. The guard is installed by `sitecustomize.py` in inherited
children; existing tests that replace child environments are outside this
inherited-child guard claim. No excluded HTTP coverage or socket use is claimed.


Reproduce the filtered runner at `.local/split-payment/socket_free.py`:

```python
import os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path('reference/booking_resale_admission').resolve()))
os.environ['PYTHONPATH']=os.pathsep.join(str(Path(p).resolve()) for p in ('.local/split-payment/guard','reference/booking_resale_admission','.'))
sys.path.append(str(Path('.').resolve()))
sys.path.append(str(Path('.local/split-payment/guard').resolve()))
import sitecustomize
excluded='test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
suite=unittest.defaultTestLoader.discover('reference/booking_resale_admission',top_level_dir='reference/booking_resale_admission')
def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite): yield from flatten(item)
        else: yield item
tests=list(flatten(suite))
assert sum(test.id()==excluded for test in tests)==1
assert len({test.id() for test in tests})==len(tests)
print('Excluded exactly one HTTP test:',excluded,flush=True)
result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(test for test in tests if test.id()!=excluded))
sys.exit(not result.wasSuccessful())
```

Its `.local/split-payment/guard/sitecustomize.py` is:

```python
import sys
def deny_sockets(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('socket event prohibited in local validation: ' + event)
sys.addaudithook(deny_sockets)
```

## Preservation, gates and non-claims

Before work both locked Git blobs matched:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

[frozen-reference-before.json](frozen-reference-before.json) records SHA-256 for
all 108 tracked frozen reference files. Final [preservation.json](preservation.json) and
[frozen-reference-after.json](frozen-reference-after.json) record byte comparisons.
The complete [changed-paths.txt](changed-paths.txt) lists the two READMEs, console,
console tests, six guided input fixtures and this node’s evidence artifacts. No protected file was transiently edited.
Contracts, catalogue, SDK, runtime flags, workflows, `.aiops/`, `docs/tasks/`,
client and driver are preserved. B03/B04 and F03 calculation usability increases
without a capability grade change.

Non-author A2 exact-head review and required KTX/KIX exact-head CI run IDs,
statuses and conclusions remain pending supervisor delivery. Local checks are
not exact-head CI. No merge occurred; merge SHA, final-merge locks and post-merge
main CI are not applicable. Builder READY is not merge-ready or merge approval.

No explicit contract violation was found in exercised paths. No contract-undefined
behavior was assigned new semantics. Product values remain **UNDETERMINED —
Astra/User**; legal/accounting treatment remains **UNDETERMINED — User/designated
advisers**. Booking quote entry, execution, booking/payment handoff, external
funds/providers/KYC, production runtime, public endpoints, Sui, persistence,
coin/TIX and new protocol commands remain outside scope. No durability,
distributed fencing, external exactly-once, chain finality, authenticated
provenance, legal compliance or production readiness claim.

## Deviations and remaining uncertainty

- Supervisor forbids network and publication: no fetch, commits, pushes, issues,
  PRs or comments. Current remote main and final task SHA remain unverified.
- Initial socket-free runner put the guard ahead of the booking suite on
  `sys.path`, allowing existing sibling test imports to collide. The local
  runner's path order was corrected; product files were unaffected.
- Broader discovery excludes exactly the predecessor's one loopback HTTP test;
  sockets remain prohibited by an audit hook in parent and inherited children.
  This is filtered local coverage, not the complete hosted workflow.
- No product value, protocol command or other STOP-condition input was needed.

- Offline Rust tests/Clippy remain unavailable because the provisioned cache lacks
  `bcs`; supplying the dependency cache and running exact-head CI remain delivery
  work for the supervisor. Architecture and formatting passed.
