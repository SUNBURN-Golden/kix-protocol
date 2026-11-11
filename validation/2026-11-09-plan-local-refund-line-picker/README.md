# Guided refund line picker — builder evidence

Node: `plan-local-refund-line-picker`. Task input is the immutable user-supplied
node specification and design plan; no issue or `docs/tasks/` document exists.
Source: KIX planner run 1794209474; supplied design step: Claude CLI Sonnet 5.5
xhigh. This is not ASTRA program mode. Supervisor owns git/GitHub delivery.

Branch: `agent/kix-plan-local-refund-line-picker`. Initial HEAD/base and cached
`origin/main`: `f5fe55278e71e0ff3158f639626a4f138321cc8c`; worktree initially clean.
Fetch omitted under the explicit supervisor no-network rule; freshness is
unverified. No base/ref change. Implementation/final task head remains
uncommitted for supervisor delivery. No merge, merge SHA or post-merge checks.

[Coverage](coverage.md) was mapped before implementation. Picker tests use real
calculator children and compare entire `CalculationExchange` sequences to the
explicit JSON path: request bytes, complete replies, integer strings and hashes.
These are source-informed builder tests, not independent financial verification.

The local `pick_lines` control displays only active successful quote results,
collects a bounded explicit count and literal IDs, then CE1-encodes a complete
selection. It clears selection/refund before prerequisites and collection.
No trimming, sorting, deduplication, default, calculation or request occurs in
selection. Existing `propose_line_refund` requires literal `SUBMIT_REFUND` and
passes the complete quote, payment plan, IDs and expected plan hash through the
unchanged client. JSON selection and upstream invalidation remain supported.
Known refusals retain driver semantics; transport failure fences without retry.

Refund policy remains **UNDETERMINED — Astra/User**; legal/accounting treatment
remains **UNDETERMINED — User/designated advisers**. CALCULATION_ONLY and refund
executionAuthorized=false remain intact. Capability grades unchanged. No
booking, settlement, payment/refund execution, real provider calls, funds,
production runtime, public endpoints, Sui, storage/replication/consensus, coin/TIX,
secrets or protocol commands added. No production readiness, durability,
distributed fencing, bank exactly-once, chain finality or legal compliance claim.

## Local results

Implementation and available local verification are complete. Exact commands,
exit codes and foreground command output are retained in [command-results.jsonl](command-results.jsonl) and per-command
stdout/stderr. No local result replaces non-author A2 exact-final-head review or
both required exact-head KTX and KIX workflows. Their run IDs/status/conclusions
remain pending supervisor delivery; no merge-ready claim.

## Acceptance coverage added

Cases in `CommerceCalculationConsoleTests`:

| Test | Gap addressed |
|---|---|
| `test_picker_journey_json_parity` | Guided bundle quote/legs/ID selection through real children equals the JSON path byte-for-byte; returned row labels/strings, multiple caller-ordered IDs, precision/free amounts, hashes and execution boundary; parent calculation entry points and clock prohibited |
| `test_picker_selection_and_confirmation_launch_counts` | No launch on selection/show/decline, one refund launch on literal confirmation; full MAX_LINES count permitted without deduplication |
| `test_picker_driver_refusals_preserve_input` | Empty array, duplicates, unknown/empty/malformed IDs; identical JSON-path requests/results/refusals; CRLF, quotes and spaces preserved |
| `test_picker_replacement_invalidates_selection_and_refund` | Identical/different replacements, bad CE1/count/encoding, JSON/picker transitions; quote/plan/history retained, prior selection/refund never restored |
| `test_picker_missing_inputs_and_upstream_invalidation` | Absent, refused and replaced quote; quote without plan; all quote/payment input controls still invalidate picker-created dependents |
| `test_picker_eof_and_decline` | EOF at every picker prompt initially and after a refund, partial candidate unpublished; EOF/decline at refund confirmation sends nothing further |
| `test_picker_refund_uncertainty_fences` | Malformed refund reply and launch failure after successful quote/plan, terminal exit 2, retained uncertain request, no later launch/retry/fallback, children reaped |

Six synthetic answer fixtures use no JSON line-selection input. The journey
selects `L3`, then `L1`; the request preserves that order, while the unchanged
driver returns sorted `lineIds`. Its customer refund is exactly `32400` atoms,
with original-card `20000` and original-bank `12400`. Precision retains
`"9007199254740993"`; free has empty original routes. Boundaries retain exact
`INVALID_ID_LIST`, `DUPLICATE_ID`, `UNKNOWN_REFUND_LINE`, `INVALID_CANONICAL_ID`
errors without repair. `show` renders history again and adds no dispatch.

## Reproduction and verification boundaries

All Python commands use Python 3.12.15, `-B`, `PYTHONDONTWRITEBYTECODE=1` and unset
initial `PYTHONPATH`. [command-results.jsonl](command-results.jsonl) records exact
argument arrays, working directories, transcript stdin paths, environment and exit
codes. Per-command stdout/stderr are retained. Every job was a foreground process;
no Git/network publication or background jobs. Restore [runner](reproduce-run.py.txt)
under `.local/refund-picker/run.py` to reproduce the logged commands.

The broader booking discovery uses the workflow's start/top-level directory and
excludes exactly the existing
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The runner asserts one matching exclusion and unique test IDs. Parent and inherited
child environments install an audit hook refusing all `socket.` events. Existing
tests that replace child environments are outside that inherited-hook claim.
Initial `PYTHONPATH` is unset; the runner explicitly sets it for inherited guard,
booking and repository-root imports, placing booking first in parent imports.
This filtered local equivalent does not claim the excluded HTTP test passed.
Sources: [discovery](reproduce-socket_free.py.txt) and
[guard](reproduce-sitecustomize.py.txt), restored under `.local/refund-picker/`
(guard at `guard/sitecustomize.py`). This reuses the predecessor's documented
no-network discovery procedure.

Rust uses the provisioned 1.98.1 bin directory first on PATH and
`CARGO_NET_OFFLINE=true`; the existing registry is copied into writable
`.local/refund-picker/cargo`, with target output under `.local/refund-picker/target`.
No downloads or provisioning. Kernel/workspace test and Clippy commands all stop
at dependency resolution with exit 101 because cached `bcs` is missing. They are
UNAVAILABLE, not passing, and no source edit can repair absent dependencies.
The supervisor must supply cache or obtain required workflow results later.

## Preservation, deviations and remaining gates

Before work, both locked blobs matched:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

[preservation-before.json](preservation-before.json) records both files and all
108 frozen reference files. Final [preservation-after.json](preservation-after.json) matches that manifest
exactly. [preservation.json](preservation.json) confirms 2,320 tracked non-task files
unchanged, both locked Git blobs matched, refs unchanged and changed Python ASTs
valid; [reproduction source](reproduce-preserve.py.txt). Client, arithmetic,
contracts, booking flows, `.aiops/`, `docs/tasks/`, CI and protected files are
outside this patch. No protected file was transiently edited.

Deviations: fetch omitted under supervisor no-network instructions; no
commit/push/PR/issue/comment, so final committed task head and remote freshness
are unavailable. One existing HTTP test is excluded for that same boundary.
Rust test/Clippy checks are unavailable due to the missing offline dependency.
No design-semantic deviation or STOP-condition input was needed.

No explicit contract violation found in exercised paths. No undefined contract
behavior was assigned new semantics. Policy and legal/accounting decisions remain
UNDETERMINED with their existing owners. No external resources or decisions were
needed to implement the picker. Supervisor delivery must preserve non-author A2
exact-final-head review and successful exact-head KTX and KIX workflows. Their
run IDs/status/conclusions are pending; no older CI result transfers here.
Merge and post-merge main CI are not applicable to this uncommitted builder session.
Builder READY means local handoff only, not merge-ready or merge authorization.


## Actual command evidence table

All commands and stdin paths are expanded in [commands.md](commands.md); the
machine-readable log retains working directories and elapsed times. No test
failed or required an implementation fix. Missing offline dependencies remain
unavailable checks. The closest applicable steps were selected after inspecting
`.github/workflows/protocol.yml` and `.github/workflows/ktx-kernel.yml`.

| Command actually run | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initial clean expected branch; both cached refs at the SHA above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs matched before work; matched again in preservation |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_calculation_*.py' -v` | Exit 0: 38 tests, 36.898 s |
| `(cd reference/v0.3-rc1 && python3.12 -B -m unittest test_commerce test_commerce_driver)` | Exit 0: 27 tests, 0.350 s |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce.json` | Exit 0: PASS, CALCULATION_ONLY, externalCalls=0 |
| `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2` with each picker fixture as stdin | Journey/precision/free/decline/replacement exit 0; boundaries expected exit 1; all stderr empty |
| `python3.12 -B .local/refund-picker/socket_free.py` | Exit 0: 917 tests, 145.127 s; exactly one HTTP exclusion |
| `python3.12 -B scripts/check_docs_index.py`, `check_status_register.py`, `check_bra_evidence_map.py`, `check_openapi_contract.py`, `check_integration_gate_openapi.py`, `check_ci_checker_wiring.py`, `check_ci_test_discovery.py`, each normally and with `--self-test` | All 14 exit 0 |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0: architecture/dependency gate OK |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0: 7 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: cached bcs absent, tests did not start |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: same dependency |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same dependency, lint did not start |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same dependency |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `python3.12 -B .local/refund-picker/preserve.py` | Exit 0: non-task tracked bytes, frozen reference, locks, refs and ASTs preserved |
| `git diff --check` | Exit 0 |

[Complete changed-path inventory](changed-paths.txt) includes the console, focused
tests, two guides, six new answer transcripts and this evidence directory. Final
documentation-index verification is also recorded in the command log.
