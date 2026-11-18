# Local commerce calculation console — builder evidence

Node: `plan-plan-local-commerce-calculation-console`. Task input is the immutable
user-supplied node/design in this session; no issue or task document exists.
This is not ASTRA program mode. Builder handoff, not merge approval.

Initial task HEAD and cached origin/main: `171ad3ebdc108870d62171506713e41a6c2086ac`.
Branch: `agent/kix-plan-plan-local-commerce-calculation-console`.
Supervisor forbids network/GitHub, commits, pushes and publication; fetch omitted,
remote freshness unverified. No base/ref change. Session began November 7 KST;
validation record dated November 8 KST.

## Coverage mapped before new tests

| Requirement | Existing coverage / initial classification | New composition gap |
|---|---|---|
| Bundle, ordered discounts, split and selected-line reversal | Sufficient arithmetic: `CommerceTests.test_bundle_discount_payment_split_and_failed_line_refund_calculation`, `test_discount_order_eligibility_and_cap_are_bound_and_observable`, `test_every_refund_subset_conserves_original_route_and_discount_shares` in `reference/v0.3-rc1/test_commerce.py` | Real subprocess chain and exact response retention in `test_real_driver_journey_exact_bytes_and_detached_snapshots` and console `test_real_driver_journey_retains_exact_quote_and_plan_for_next_request` |
| Stale hashes, expiry, totals, unsupported line selection | Sufficient arithmetic: `test_plan_allocation_and_original_route_changes_do_not_reuse_expected_hash`, `test_expiry_and_amount_mismatch_reject_without_payment_plan`, `test_input_mutation_and_unsupported_refund_selection` | Client `test_real_driver_rejections_do_not_promote_or_retry`; console explicit correction journey |
| Free orders and atoms above JS safe integer | Sufficient arithmetic: `test_free_quote_needs_no_money_and_refund_has_no_payment_route`, `test_exact_zero_two_six_and_eighteen_decimal_asset_profiles` | Console `test_free_and_large_atom_journeys_preserve_wire_strings_and_empty_routes` |
| Lossless bounded CE1 decoding | Sufficient codec/driver: `test_commerce_driver.py` duplicate-key, number-token, input-bound and malformed-input tests | New client/console file loading and wire-bound cases |
| Consent, EOF, input replacement, historical isolation | Not covered for this tool; ticket console patterns only | Every submission prompt declined/EOF; identical and failed quote/legs reload, failed/declined/new plans and changed/invalid selection tests |
| One child per submission, terminal fencing, no retry | Partially covered by predecessor ticket client; commerce EOF transport differs | Fixed target/import/no-launch, reentrancy, controlled real workers, interrupted reads/short writes/launch failure and cleanup escalation |
| Response schema/hash/snapshot bindings and output failure | Not covered for this client | Malformed and rehashed replies, detached immutable exchanges, output failure retains prior received success |

Tests are source-informed composition, not independent arithmetic verification or
non-author A2 review. The client uses CE1/asset/hash validation only; it never calls
build_quote, plan_payments, propose_line_refund or the restricted booking bridge.

## Actual commands and results

Detailed stdout, stderr, exit codes and elapsed times are in
[command-results.json](command-results.json). Commands ran as foreground children
of the local validation runner, sequentially within each phase. No background
jobs or automatic retries. Python is provisioned **3.12.15**. Ordinary Python
commands remove `PYTHONPATH` and set `PYTHONDONTWRITEBYTECODE=1`; the additional
socket-free run uses the explicit guard below. Narrow tests ran first, followed
by existing commerce suites, transcript and broader/document checks.

| Command actually run | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initial clean worktree; expected task branch; task HEAD and cached main both `171ad3ebdc108870d62171506713e41a6c2086ac`; remote freshness unverified |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`; `git ls-tree HEAD reference/v0.3-rc1` | Both required blobs match before work; frozen reference tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_calculation_*.py' -v` (initial) | Exit 1: 18 tests, one failed oversized-worker test; OS per-argument size prevented worker launch, so expected oversized response bytes were absent |
| Same focused command after worker correction | Exit 0: 18 tests in 5.124 s |
| `(cd reference/v0.3-rc1 && python3.12 -m unittest test_commerce test_commerce_driver)` | Exit 0: 27 tests in 0.372 s |
| Same focused command after response binding refinement | Exit 0: 18 tests in 5.105 s (5.255 s command wall time); logged |
| `python3.12 scripts/verify_commerce.py --report .local/verification/commerce.json` | Exit 0: PASS; CALCULATION_ONLY, payable 48600, selected refund 16200, externalCalls=0 in synthetic report |
| `python3.12 reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_journey.txt` | Exit 0; three explicit submissions; exact driver replies retained; [stdout](journey.stdout), [stderr](journey.stderr) |
| Same console command with `commerce_console_decline.txt` | Exit 0; no submissions; [stdout](decline.stdout), [stderr](decline.stderr) |
| Same console command with `commerce_console_replacement.txt` | Exit 0; historical outputs retained, identical reload clears active dependents; [stdout](replacement.stdout), [stderr](replacement.stderr) |
| Same console command with `commerce_console_free.txt` | Exit 0; empty legs and original routes; [stdout](free.stdout), [stderr](free.stderr) |
| Same console command with `commerce_console_precision.txt` | Exit 0; exact `"9007199254740993"` strings retained; [stdout](precision.stdout), [stderr](precision.stderr) |
| Same console command with `commerce_console_boundaries.txt` | Expected exit 1: QUOTE_EXPIRED, PAYMENT_TOTAL_MISMATCH, UNKNOWN_REFUND_LINE; [stdout](boundaries.stdout), [stderr](boundaries.stderr) |
| `python3.12 .local/commerce-console/socket_free.py` | Exit 0: 875 tests in 106.523 s; filtered coverage with exactly one documented HTTP exclusion |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | Both exit 0; index valid, self-test pass |
| `python3.12 scripts/check_status_register.py` and `--self-test` | Both exit 0; status register valid, self-test pass |
| `python3.12 scripts/check_bra_evidence_map.py` and `--self-test` | Both exit 0; evidence map valid, self-test pass |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | Both exit 0; existing 84-command pin unchanged, self-test pass |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0; productionEndpoint=false/publicHost=false, self-test pass |
| `python3.12 scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0; wiring valid, self-test pass |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; new tests reached by existing discovery, self-test pass |
| `python3.12 scripts/verify_runtime_architecture.py` | Exit 0: architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3.12 scripts/test_runtime_architecture.py` | Exit 0: 7 tests in 0.220 s |
| `cargo --version`; `rustc --version` | Both exit 0: provisioned 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: cached `bcs` missing for workspace kix-bcs1; no test execution |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: same missing cached `bcs`; no test execution |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cached `bcs`; no lint execution |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cached `bcs`; no lint execution |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| Focused command after final explicit result type/ID checks | Exit 0: 18 tests; final result and timing in command-results.json |
| Commerce verification script and all six transcripts after final type/ID checks | Expected exits again (0 for five, 1 for boundary refusals); final stdout/stderr checked in |
| `python3.12 .local/commerce-console/preserve.py`; `git diff --check` | PASS: 1,529 non-task tracked blobs unchanged, both locks match, all 108 historical reference files unchanged, no generated extra historical files, task/main refs unchanged, changed Python ASTs valid |

The final code refinement enforces explicit result identifier types/uniqueness,
nonnegative checkedAt, existing cardinality bounds and selected-line membership.
It performs schema/binding checks, with no pricing/allocation arithmetic.
Final focused tests and all transcripts were rerun successfully. Broader discovery
was rerun for that final code too: **875 tests passed in 104.211 s**,
exit 0 (104.601 s command wall time). This remains the same filtered
single-exclusion selection, with no duplicate test IDs. Final document-index
and CI-discovery checks also passed after completing the report.

### Reproducing socket-free coverage

The local runner is the predecessor's single-exclusion discovery with duplicate-ID
and exactly-one-exclusion assertions. Its effective code is:

```python
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path('reference/booking_resale_admission').resolve()))
excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
suite = unittest.defaultTestLoader.discover(
    'reference/booking_resale_admission', top_level_dir='reference/booking_resale_admission')
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item
tests = list(flatten(suite))
assert sum(test.id() == excluded for test in tests) == 1
assert len({test.id() for test in tests}) == len(tests)
result = unittest.TextTestRunner(verbosity=1).run(
    unittest.TestSuite(test for test in tests if test.id() != excluded))
sys.exit(not result.wasSuccessful())
```

The socket-free runner also installs an audit hook, and its environment sets
`PYTHONPATH` to the absolute local guard directory, booking reference directory
and repository root. The guard's `sitecustomize.py` is:

```python
import sys
def deny_sockets(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('socket event prohibited in local validation: ' + event)
sys.addaudithook(deny_sockets)
```

This guards the parent and children inheriting that environment, including the
new real commerce driver and console journeys. Existing probes that replace
the child environment are outside the inherited-child guard claim. Ordinary
focused and CLI checks also passed with PYTHONPATH removed to match CI imports.
This is **filtered** discovery, not full CI or the excluded HTTP test. No sockets
were opened to perform the excluded test. Existing booking/settlement adapter
regressions in this selection are unchanged.

Rust used only the provisioned registry, copied into the writable ignored
`.local/commerce-console/cargo/registry`, with this environment:

```text
PATH=/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:<existing PATH>
CARGO_HOME=<worktree>/.local/commerce-console/cargo
CARGO_TARGET_DIR=<worktree>/.local/commerce-console/target
CARGO_NET_OFFLINE=true
```

No dependency downloads or network actions were attempted. Missing prerequisites
are not passing Rust/Clippy results. No Rust source changed.

## Preservation and gates

Both locked kernel blobs matched before editing. Historical reference tree at
initial HEAD: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
[preservation.json](preservation.json) records the final byte-level comparison
against the initial clean index: all 1,529 tracked blobs outside the two permitted
README edits match, including both kernel locks, historical reference, contracts,
booking adapters/FSMs, catalogue, workflows, .aiops and docs/tasks. No protected
path was transiently mutated. Both refs remain at the initial SHA. Both locks:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Complete changed-path list: [changed-paths.txt](changed-paths.txt). It contains
only the two READMEs, new client/console, two focused test modules, synthetic
commerce_console fixtures/transcripts and this node's validation artifacts.

Implementation/final task head: uncommitted; supervisor owns commit/push.
Non-author exact-head A2 review and both exact-head KTX/KIX workflow run IDs,
statuses and conclusions are pending supervisor delivery. No merge occurred;
merge SHA, merge locks and post-merge CI are not applicable.

No contract violation found in exercised paths. No new product semantics.
Product policy remains **UNDETERMINED — Astra/User**. Legal/accounting treatment
remains **UNDETERMINED — User/designated advisers**. Quotes and plans have no
executionAuthorized field; refund proposals preserve executionAuthorized=false.
No external execution, funds/providers/KYC, sockets, new protocol commands,
booking confirmation, settlement execution, persistence, coin/TIX, Sui,
production runtime or policy defaults are introduced. No authentication,
durability, distributed fencing, chain finality, legal compliance or production
readiness claim. Hashes bind calculations, not external facts or authority.


## Deviations and remaining uncertainty

- Fetch omitted under the supervisor's explicit no-network rule; cached origin/main
  freshness is unverified. No task issue or docs/tasks document exists; task input
  is the supplied immutable node/design, as directed.
- The initial oversized-reply test exceeded the OS argument limit before launching
  its worker. The test worker now emits a repeated byte expression, allowing the
  response-bound predicate to be exercised. Corrected narrow suite passed.
- Explicit local result type/ID checks were tightened during builder review;
  arithmetic and frozen driver remained unchanged. No design-boundary deviation.
- Offline Rust tests/Clippy require provisioned cached bcs. They are unavailable,
  not green. Formatting and architecture checks passed. No network retry.
- `.local` runners, generated commerce report and Cargo cache/target are ignored
  execution artifacts, not deliverable product files. Runnable input transcripts,
  stdout/stderr, actual command evidence and preservation records are deliverables.
- No product value or new protocol command was needed; no DECISION_REQUIRED input
  was encountered. No explicit contract violation found. No contract-undefined
  behavior was assigned new semantics. Required external execution evidence on
  refund proposals remains unproved; proposals remain calculation-only.
- Final task SHA, A2 non-author exact-head review, exact-head KTX/KIX run IDs/status/
  conclusions and post-merge verification remain supervisor/User delivery gates.
  Local builder READY does not mean merge-ready or authorization to merge.
