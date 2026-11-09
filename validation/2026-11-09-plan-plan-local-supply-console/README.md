# Local supply console — builder evidence

Task ID: `plan-plan-local-supply-console`; dependency:
`plan-local-supply-reconciliation-tool`. Task document: the user-supplied inline
node specification and design plan; no issue or `docs/tasks/` document exists.
This is an ordinary builder session, not ASTRA program mode.

Observed local `origin/main`, task base and unchanged branch HEAD:
`f41547f49cde7a510f46753f5e0a3eb6ebb3811c` on
`agent/kix-plan-plan-local-supply-console`. No local base delta. The supervisor's
explicit prohibition on network/git publication overrides the normal fetch
step: remote freshness was not verified. No commit, push, PR, issue, comment,
branch change, tag operation or merge was performed. Final task head and merge
SHA do not exist for this uncommitted delivery; the supervisor owns them.

The separate `reference/token_reward/supply_console.py` composes explicit
hypothetical events, previews requests and dispatches only literal confirmations.
It forwards the exact complete returned report object and preserves complete
responses/errors. Edits invalidate results immediately; failed/declined
calculations cannot reuse old selections. All state is in memory.
`stop_payout` is displayed only. Supply policy and operational responses remain
**UNDETERMINED — Astra/User**. See [usage](../../reference/token_reward/README.md#local-supply-console).

The [coverage map](coverage.md) was recorded before adding tests. The new
`SupplyConsoleTests` and `SupplyConsoleSubprocessTests` cover interface gaps over
the real dispatcher and existing fixture requests; they introduce no arithmetic
oracle or clean-room claim. Existing dispatcher, CLI and model coverage is reused.

The [command ledger](commands.json) records exact validation commands, environment,
exit statuses and stdout/stderr captures, including unavailable checks. All
validation commands were run from the repository root, in the foreground with
`PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=reference/token_reward`. Python 3.13.5
passed the initial focused tests; Python 3.12.15 matches the CI minor version and
passed the final focused and full tests. After a final correction keeping event
counts independent of supply-amount bounds, both test commands were rerun and
passed. No product source or test changes followed those final passing runs.

| Actual command | Result |
|---|---|
| `python3 -m unittest test_supply_console test_supply_console_subprocess test_supply_reconciliation test_supply_cli test_reward_model.SupplyTests test_tl4_model_properties.SupplyPropertyTests` | exit 0; 35 tests passed, initial Python 3.13 run |
| `python3.12 -m unittest test_supply_console test_supply_console_subprocess test_supply_reconciliation test_supply_cli test_reward_model.SupplyTests test_tl4_model_properties.SupplyPropertyTests` | exit 0; 35 tests passed, final run in `25.stderr.txt` |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 278 tests passed, final run in `26.stderr.txt` |
| `python3 scripts/check_docs_index.py` and `python3 scripts/check_docs_index.py --self-test` | both exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` and `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | both exit 0 |
| `python3 scripts/check_class_b_index.py` and `python3 scripts/check_class_b_index.py --self-test` | both exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` and `python3 scripts/check_ci_checker_wiring.py --self-test` | both exit 0 |
| `python3 scripts/check_ci_test_discovery.py` and `python3 scripts/check_ci_test_discovery.py --self-test` | both exit 0; new console tests reached through unchanged token_reward discovery |
| `python3 scripts/check_openapi_contract.py` and `python3 scripts/check_openapi_contract.py --self-test` | both exit 0; 84 commands, unchanged pin |
| `python3 scripts/check_integration_gate_openapi.py` and `python3 scripts/check_integration_gate_openapi.py --self-test` | both exit 0; productionEndpoint=false, publicHost=false |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; architecture/dependency boundary passed |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | unavailable, exit 101; uncached `bcs`, no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | unavailable, exit 101; same dependency-resolution failure |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | unavailable, exit 101; uncached `bcs`, no lint executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | unavailable, exit 101; same dependency-resolution failure |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `python3 validation/2026-11-09-plan-plan-local-supply-console/verify_preservation.py` | exit 0; 110 protected files byte-identical, both locked blobs match, protected tracked paths unchanged against HEAD |
| `git diff --check` | exit 0 |
| `python3 -` (initial inventory/whitespace script, source in ledger) | exit 1; overbroad scan flagged a verbatim terminal prompt's trailing space; no product defect |
| `python3 validation/2026-11-09-plan-plan-local-supply-console/record_changed_paths.py` | exit 0; complete path inventory and source/document whitespace check; verbatim output captures excluded |

The closest applicable local workflow steps were selected from
`.github/workflows/ktx-kernel.yml` and `.github/workflows/protocol.yml`.
Offline dependency-resolution failures are environment limitations, not test
failures or passes. Each distinct Cargo command was attempted once. No download,
automatic retry, CI edit or dependency change was performed.
`run_validation.py` is a foreground capture helper for reproducing commands and
appending their actual stdout/stderr/status to the ledger.
The initial whitespace scan was corrected to exclude captured stdout/stderr;
terminal prompt spaces are intentional and the captures remain unedited.

## Runnable terminal transcripts

[Transcript ledger](transcripts.json) records the executable, input fixture,
exit status and complete stdout/stderr captures for nine real subprocess runs.
No JSON request file is prepared. Each fixture can be replayed from root:

```bash
python3.12 reference/token_reward/supply_console.py < reference/token_reward/fixtures/supply_console_match.txt
```

| Input fixture (`reference/token_reward/fixtures/`) | Exit / result | Full stdout / stderr |
|---|---|---|
| `supply_console_match.txt` | 0 / report then MATCH | [stdout](transcript-match.stdout.txt), [stderr](transcript-match.stderr.txt) |
| `supply_console_holder_burn.txt` | 0 / report then HOLDER_BURN_OUTSIDE_LAYER | [stdout](transcript-holder_burn.stdout.txt), [stderr](transcript-holder_burn.stderr.txt) |
| `supply_console_unexplained.txt` | 0 / report then UNEXPLAINED | [stdout](transcript-unexplained.stdout.txt), [stderr](transcript-unexplained.stderr.txt) |
| `supply_console_unapproved_mint.txt` | 0 / report then UNAPPROVED_MINT, stop_payout=true displayed | [stdout](transcript-unapproved_mint.stdout.txt), [stderr](transcript-unapproved_mint.stderr.txt) |
| `supply_console_unapproved_path.txt` | 0 / report then UNAPPROVED_PATH, stop_payout=true displayed | [stdout](transcript-unapproved_path.stdout.txt), [stderr](transcript-unapproved_path.stderr.txt) |
| `supply_console_both_causes.txt` | 0 / report then UNAPPROVED_PATH (characterization only) | [stdout](transcript-both_causes.stdout.txt), [stderr](transcript-both_causes.stderr.txt) |
| `supply_console_duplicate.txt` | 1 / SUPPLY_EVENT_DUPLICATE | [stdout](transcript-duplicate.stdout.txt), [stderr](transcript-duplicate.stderr.txt) |
| `supply_console_conservation.txt` | 1 / SUPPLY_CONSERVATION, event order retained | [stdout](transcript-conservation.stdout.txt), [stderr](transcript-conservation.stderr.txt) |
| `supply_console_boundaries.txt` | 0 / declines and cancellations, zero dispatches/results | [stdout](transcript-boundaries.stdout.txt), [stderr](transcript-boundaries.stderr.txt) |

Subprocess tests compare all six complete successful journeys with direct
dispatcher responses. In-process tests wrap the real dispatcher, verify exact
report object identity and single dispatch counts, inject malformed reports to
prove no repair, and cover edits, declines, failures, invalid fields, EOF,
interruption and I/O boundaries. New coverage is 12 stream tests and 5 subprocess
tests. These tests are source-informed interface evidence, not a new model oracle.

Before editing, both locked kernel Git blobs matched the prescribed values:

| Path | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

[Pre-edit SHA-256 inventory](preservation-before.json) covers the two locked
files and every file in `reference/v0.3-rc1/` (110 total). Final preservation
checks passed against this inventory and tracked protected paths against HEAD;
see [final preservation evidence](preservation-after.json). Both locked Git
blobs also match after implementation. Models, CLI, dispatcher, existing tests,
contracts, CI, `.aiops/` and task documents are unchanged.

Complete changed paths are recorded in [changed-paths.txt](changed-paths.txt):
the new console, two new test modules, nine input fixtures, token_reward README,
docs index and this validation directory (coverage, ledgers, logs, transcripts,
preservation inventories and capture/check helpers).

No explicit contract violation found. Simultaneous unapproved mint/path still
selects `UNAPPROVED_PATH`, retained only as class-B characterization under TL-4
§6.B. No semantics or policy value was defined.

Deviations: use available Python versions (recorded per command); skip fetch and
all GitHub actions per supervisor. Offline Cargo dependencies were unavailable
and were not downloaded or treated as passing. The validation capture helper was
temporarily staged in `/tmp`, then moved into this worktree's evidence directory;
no helper remains at that temporary path. No design/scope deviation was needed.

A2 non-author exact-final-head review is pending. KTX kernel verification and
KIX protocol verification: exact-head run IDs/status/conclusions are **not
available/not checked** in this offline, uncommitted session. No prior result
transfers to this patch. Post-merge CI and final-merge blob checks are not
applicable: no merge occurred. `READY` means local builder delivery only, not
merge-ready or merge authorization.

No production durability, bank exactly-once, chain finality, authenticated
approvals, operational payout response, legal compliance, performance or
production readiness was tested or claimed. No runtime, external resource,
dependency, chain access, funds, protocol command or policy change was needed.
Full Move/localnet/ZK/storage and unrelated suite jobs are not reproduced.
