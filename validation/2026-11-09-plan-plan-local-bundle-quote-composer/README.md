# Guided synthetic bundle quote composition — builder evidence

Node: `plan-plan-local-bundle-quote-composer`. Task input is the user-supplied
immutable node specification and design plan; no issue or `docs/tasks/` document
exists for this node. This is not ASTRA program mode. Supervisor owns commits
and publication. Design provenance: KIX planner run 1794197723; supplied design
step identified Claude CLI Sonnet 5.5 xhigh. This builder used that supplied plan.

Initial branch: `agent/kix-plan-plan-local-bundle-quote-composer`. Initial HEAD,
base and cached local `origin/main`: `0afb7c199acb880ed7a1972d261f92ff9244d8d7`.
Initial worktree clean. Fetch omitted under the supervisor's explicit no-network
instruction; remote freshness is unverified. No base/ref changed. Implementation
and final task head remain uncommitted, pending supervisor delivery. No merge;
merge SHA, final-merge lock verification and post-merge main CI are not applicable.

[Coverage mapping](coverage.md) was written before implementation/tests. The
console/client's existing deterministic arithmetic and uncertainty coverage is
reused. New bundle tests address guided quote composition, full exchange parity,
exact strings/order/caps, refusal propagation, invalidation, EOF and launch counts.
These are source-informed builder tests, not independent arithmetic verification.

Implementation and available local checks are complete. Exact commands,
exit codes and timings are retained in [command-results.jsonl](command-results.jsonl),
with per-command stdout/stderr. Final results and limitations are recorded below. No local result substitutes for required non-author A2
exact-final-head review or exact-head KTX/KIX workflows; their run IDs, statuses
and conclusions are pending supervisor delivery and are not claimed as passed.

Product policy remains **UNDETERMINED — Astra/User**; tax/accounting treatment
remains **UNDETERMINED — User/designated advisers**. Synthetic calculation only,
`CALCULATION_ONLY`, refund `executionAuthorized=false`. B03/F03 grades unchanged.
No booking confirmation, coupon lifecycle, execution, funds, real provider/bank/KYC,
Sui, public endpoint, production runtime, storage engine, coin/TIX or new protocol
command is added. No durability, distributed fencing, external exactly-once,
chain finality, legal compliance or production readiness claim.

## Implementation and acceptance evidence

`_compose_quote` collects explicit order identity/version, scope, policy reference,
expiry, bounded line count, every line/asset field, bounded rule count and every
ordered rule field. Only CE1 integer/token parsing, JSON array/string/null typing,
existing count bounds and canonical encoding run locally. Business validation
stays with the unchanged calculator driver. The shared integer helper also serves
existing guided legs. No client implementation, calculator semantics, driver
action allowlist, booking bridge, policy value or execution path changed.

The candidate is local until complete encoding succeeds. Entering `compose_quote`
first clears quote input, active quote, plan, refund and selected lines. Stored
legs/history match file loading behavior. The preview submits nothing; existing
`simulate_quote`, `plan_payments`, `propose_line_refund` each require their separate
literal confirmation. Known refusals are visible without repair or automatic retry.

New `CommerceCalculationConsoleTests` cases:

| Test | Documented gap addressed |
|---|---|
| `test_bundle_journey_file_parity` | Three real-child exchanges for each bundle/precision/free journey equal file-input exchanges byte-for-byte, including hashes and original routes; parent arithmetic entry points prohibited; each confirmed calculation launches once |
| `test_bundle_driver_refusals_preserve_input_and_dispatch_once` | Seven exact driver errors, unchanged submitted request, one child each, no success promotion or retry |
| `test_bundle_literal_strings_caps_and_array_order` | Reversed lines/rules/eligibility, explicit string and null caps, file parity, literal whitespace/quotes/empty fields, CRLF removal only |
| `test_bundle_integer_json_and_encoding_failures_never_publish` | Invalid CE1 integers at every integer prompt, count bounds, typed eligibility/caps, Unicode and size encoding failure; no published candidate or process launch |
| `test_bundle_replacement_clears_input_quote_and_dependents` | Identical replacement, malformed integer/eligibility/cap, encoding failure, driver refusal, stored-leg reuse and explicit new line selection |
| `test_bundle_eof_decline_and_each_confirmation_launch_counts` | EOF at every composition prompt initially and after a refund; no extra launch on composition/decline; each confirmation separately counted |

Six fixtures `commerce_console_bundle_{journey,precision,free,decline,replacement,boundaries}.txt`
are runnable from the repository root using the guide's command. All use synthetic
caller inputs. Actual terminal stdout/stderr is retained as `transcript-*.{stdout,stderr}.txt`.
Journey composes three lines, FIXED then BPS, two payment legs, then `L2` refund:
synthetic payable `48600`, selected-line refund `16200`, original-card `10000`
and original-bank `6200`. Precision retains `"9007199254740993"`; free explicitly
has zero rules/legs and empty original routes. Boundaries show `DUPLICATE_LINE`,
`DUPLICATE_INVENTORY`, `DUPLICATE_DISCOUNT_RULE`, `DUPLICATE_ID`,
`UNKNOWN_DISCOUNT_LINE`, `MIXED_QUOTE_ASSETS`, `DISCOUNT_EXCEEDS_PAYABLE`.
`show` renders history again; printed reply count is not dispatch count.

## Actual commands and results

All Python validation used Python 3.12.15 with `-B`, `PYTHONDONTWRITEBYTECODE=1`
and unset `PYTHONPATH`, except the explicit inherited socket guard below. Jobs
ran as foreground subprocesses; no shell background jobs or network actions.
[command-results.jsonl](command-results.jsonl) records exact argument arrays,
working directories, exit codes and elapsed times; per-label output files retain
stdout/stderr. The table groups only identical command patterns.

| Command actually run | Result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; expected branch and cached refs at SHA above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before work; final preservation also verifies them |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_calculation_*.py' -v` (initial) | Exit 1: 31 tests, 49 subtest/assertion failures caused by fixture slicing at `show` inside `fixture-show`; retained in `focused.stderr.txt` |
| Same focused command after correcting test/transcript action boundary | Exit 0: 31 tests in 21.506 s (`focused-final`) |
| Same focused command after strengthening failed-replacement quote-input assertion | Exit 0: 31 tests in 22.543 s (`focused-verified`) |
| `(cd reference/v0.3-rc1 && python3.12 -B -m unittest test_commerce test_commerce_driver)` | Exit 0: 27 tests in 0.358 s |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce.json` | Exit 0: PASS, CALCULATION_ONLY, externalCalls=0 |
| `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_bundle_journey.txt` | Exit 0; also run once directly during diagnosis |
| Same console command with bundle precision, free, decline and replacement transcripts | All exit 0, stderr empty |
| Same console command with bundle boundaries transcript | Expected exit 1 for seven exact known refusals, stderr empty |
| `python3.12 -B .local/bundle-quote/socket_free.py` | Exit 0: 910 tests in 136.338 s; exactly one existing HTTP exclusion |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_status_register.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_bra_evidence_map.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both exit 0; command catalogue unchanged |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0: architecture/dependency gate OK |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0: 7 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: provisioned cache lacks `bcs`; tests did not start |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: same missing cache dependency |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cache dependency; lint did not start |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cache dependency |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `python3.12 -B .local/bundle-quote/preserve.py` | Exit 0: 2,087 non-task tracked files unchanged, all 108 frozen files byte-identical, both locked blobs match, refs unchanged and changed Python ASTs valid |
| `python3.12 -B scripts/check_docs_index.py` (final evidence links) | Exit 0 |
| `git diff --check` | Exit 0 |

Rust commands used the provisioned 1.98.1 toolchain directly, with its bin
directory first on PATH, `CARGO_NET_OFFLINE=true`, writable
`CARGO_HOME=.local/bundle-quote/cargo` and
`CARGO_TARGET_DIR=.local/bundle-quote/target` (absolute paths recorded in JSONL).
The provisioned registry was copied into that local cache; no dependencies were
downloaded. No source changes can resolve an absent offline dependency.

Broader booking discovery uses the workflow's start/top-level directories and
excludes exactly
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
It asserts exactly one matching exclusion and no duplicate test IDs. The parent
and inherited child environments install an audit hook rejecting every `socket.`
event. Existing tests replacing child environments are outside the inherited-hook
claim. Excluded HTTP coverage is unavailable, not passing. The initial parent
`PYTHONPATH` is unset; the runner explicitly sets it only for inherited guard,
booking-suite and repository-root imports, with the booking suite first on the
parent's import path to avoid sibling-module collisions. This is a filtered local
equivalent, not the full hosted workflow. Reproduction sources are retained in
[reproduce-socket_free.py.txt](reproduce-socket_free.py.txt),
[reproduce-sitecustomize.py.txt](reproduce-sitecustomize.py.txt) and
[reproduce-run.py.txt](reproduce-run.py.txt); restore them under the matching
`.local/bundle-quote/` paths (guard in `guard/sitecustomize.py`).

## Preservation, deviations and remaining gates

Both required kernel Git blobs matched before work:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

[preservation-before.json](preservation-before.json) records SHA-256 for the two
locks and all 108 frozen reference files. [preservation-after.json](preservation-after.json) matches the before manifest exactly.
[preservation.json](preservation.json) verifies all non-task tracked bytes, locked Git blobs
and unchanged cached refs. The complete [changed-paths.txt](changed-paths.txt) includes
the four modified source/guide paths, six new input fixtures and every evidence artifact. No protected file was edited, even
transiently. Preservation runner source is retained in
[reproduce-preserve.py.txt](reproduce-preserve.py.txt). Client/driver, `.aiops/`, `docs/tasks/`, CI and all frozen bytes remain
outside the patch.

Deviations: no fetch/commit/push/PR/issue/comment under supervisor instructions;
remote freshness and final commit remain unverified. Initial test/transcript
slicing was corrected to match whole menu actions instead of the suffix of a
scope value; no product semantics changed. One existing HTTP test is excluded
for the no-network boundary. Offline Rust test/Clippy evidence is unavailable
because of the missing provisioned dependency. No product-policy value, new
protocol command or other STOP-condition input was needed.

No explicit contract violation found in exercised paths. No contract-undefined
behavior was assigned semantics; product and tax/accounting decisions remain
UNDETERMINED. Follow-up delivery gates: supervisor supplies offline cache or runs
required Rust checks in CI; non-author A2 exact-final-head review; exact-head KTX
and KIX workflow IDs/statuses/conclusions. No run IDs are available or claimed.
Builder READY denotes local implementation handoff only, not merge-ready,
independent review, workflow completion or merge authorization.
