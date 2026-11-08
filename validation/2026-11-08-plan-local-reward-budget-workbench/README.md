# Local reward-budget workbench — builder evidence

## Identity and base

Node/task: `plan-local-reward-budget-workbench`, dependencies `tl-3-offchain`
and `tl-4`, audit floor A2, Astra gate none. Task document is the supervisor's
node objective, acceptance criteria and read-only design plan supplied in this
session. No issue or task file under `docs/tasks/` exists for this loop-proposed
node; none was created or modified. This is not ASTRA program mode.

Observed **local** `origin/main`, task base, initial and current uncommitted HEAD:
`aab0627f380931804ce0b9f1beba9d6f3f3fb3c2`, on branch
`agent/kix-plan-local-reward-budget-workbench`. These match; no base delta was
observed. `git fetch origin main`: NOT_RUN, because the supervisor explicitly
forbids network/GitHub actions. Remote freshness remains unverified. The
supervisor owns commits/publication: implementation and final task commit SHAs
are unavailable; no merge commit or post-merge CI exists.

Implementation follows the supplied design: two allowlisted calculation selectors,
strict complete JSON file/stdin requests and guided entry, complete previews,
literal single-use confirmations and explicit residual handoff. The unchanged
functions own all arithmetic and domain refusals. No reward session is created.

## Changed paths

- `reference/token_reward/reward_budget_workbench.py`
- `reference/token_reward/test_reward_budget_workbench.py`
- `reference/token_reward/fixtures/reward_budget/residual.json`
- `reference/token_reward/fixtures/reward_budget/budget_floor.json`
- `reference/token_reward/fixtures/reward_budget/budget_cap.json`
- `reference/token_reward/fixtures/reward_budget/guided_floor.txt`
- `reference/token_reward/fixtures/reward_budget/guided_cap.txt`
- `reference/token_reward/fixtures/reward_budget/guided_decline.txt`
- `reference/token_reward/README.md`
- `docs/README.md`
- `validation/2026-11-08-plan-local-reward-budget-workbench/` (this record,
  evidence capture/check scripts, command records and stdout/stderr, preservation
  manifests and complete expanded `changed-paths.txt`).

## Preservation

`preservation-before.json` records Git blobs and SHA-256 bytes for both locked
kernel files and all 108 files under `reference/v0.3-rc1/**` before editing.
Kernel blobs match `69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`, respectively.
The after manifest and `check_preservation.py` verify all 110 entries, membership,
required blobs, and that all changed paths stay within the declared additive
scope. The model, FSM, session, existing CLI/console/client, contracts, catalogue,
runtime configuration, `.aiops/`, task inputs and CI are unchanged.

## Coverage mapping

Existing coverage was inspected and classified before adding tests. Paths in
this table are relative to `reference/token_reward/`. These are author-side,
source-informed checks, not clean-room or non-author exact-head acceptance.

| Requirement | Existing classification and reused evidence | New gap coverage |
|---|---|---|
| Residual deductions, window exclusion, budget floor/cap and descriptive periods | Sufficient arithmetic: `test_reward_model.py::BudgetTests.test_budget_inputs_have_no_defaults_and_exclude_in_window_revenue`; `test_tl4_model_properties.py::BudgetAndRewardIdTests.test_TL4_budget_matches_floor_formula_and_is_monotone` and `test_TL4_in_window_revenue_is_excluded_from_the_net_residual` | Adapter success envelopes and real CLI fixture transcripts; no duplicate arithmetic oracle |
| Strict envelope, missing inputs, selector allowlist | Not covered for this new dispatcher; existing reward CLI shape helper tests apply to a different surface | `DispatchTests.test_shape_missing_every_field_and_unsupported_selectors`: every missing field, unknown envelope/argument fields, non-object shapes and unsupported `submit`/attribute selectors |
| File/stdin/guided parity | Not covered | `CliTests.test_file_stdin_guided_identical_success_envelopes`, `test_real_guided_fixtures`, `GuidedTests.test_direct_entry_for_both_operations`: compare complete success envelopes |
| Explicit handoff and separate confirmations | Not covered | `GuidedTests.test_explicit_handoff_matches_complete_requests`, `test_complete_preview_flushed_before_each_confirmation`: requests/call counts, displayed residual copied only after selection, complete preview before each call |
| Exact integer transport | Partial: model arithmetic/TL-4 tests; no workbench transport | `CliTests.test_exact_integer_transport_and_descriptive_periods`: `999999999999 * 999999999999 // 1000000000000 = 999999999998` via stdin/guided and different periods; >2**53 rejected integer reaches dispatch unchanged; `GuidedTests.test_decoded_scalar_types_and_large_integer_reach_model_unchanged` |
| Original error propagation | Partial: BudgetTests and `test_tl4_fuzz_boundaries.py::JunkAndJournalTests.test_TL4_junk_values_on_the_fenced_surface_raise_token_reward_error` | `DispatchTests.test_model_errors_propagate_with_original_codes`: every field with invalid amount/type, ratios, periods, window overflow, excess deductions and scaled overflow despite small cap; same exception identity; real CLI errors in both modes |
| Malformed JSON and I/O | Partial: existing shared `reward_fixture`/reward CLI coverage, no new input surface | `CliTests.test_malformed_json_missing_fields_and_multiple_documents`, `test_io_failure_eof_and_mutually_exclusive_modes`: empty/truncated/duplicate/non-finite/Unicode/multi-document inputs, missing file, option exclusivity; importable non-JSON rejection |
| Decline, EOF, no retry | Not covered for workbench | `GuidedTests.test_declines_and_literal_confirmation`, `test_eof_at_every_prompt_never_dispatches_incomplete_request`, `test_bad_scalar_or_selection_stops_without_retry`: all prompt cuts, no partial/stale dispatch, no budget after handoff decline |
| No policy defaults, period multiplier, conversion or submission | Sufficient existing function signatures and arithmetic; transport selectors uncovered | Every omitted argument rejected; different periods yield identical CLI budget; `submit` and currency arguments rejected; additive tool uses no session/network/persistence |

New tests live in `test_reward_budget_workbench.py`. Existing BudgetTests and
complete TL-4 arithmetic/fuzz coverage run in the full reference suite.

## Actual commands and results

`commands.json` records each validation argv, working directory, supplied stdin,
bytecode environment, exit status, duration when retained, and captured stdout/stderr paths.
`run_checks.py` runs subprocesses in the foreground, sequentially, with
`PYTHONDONTWRITEBYTECODE=1`. Python is provisioned 3.12; installed Rust is 1.98.1.
Cargo commands use `--locked --offline`; no downloads or automatic retries.
The actual result table below summarizes the retained command records. Inspection commands included
`git status --short`, `git rev-parse HEAD`, `git rev-parse origin/main`,
`git branch --show-current`, `git hash-object` for both locks, `rustc --version`,
`cargo --version`, `rg`/`sed`/`cat` for repository guidance, contracts, existing
coverage and both workflows. All were read-only; the initial worktree was clean.

## Real CLI transcripts

The `transcripts` phase captures stdout, stderr and exit status for each of:

- `--request fixtures/reward_budget/residual.json` and identical stdin document:
  residual `40`.
- `--request fixtures/reward_budget/budget_floor.json` and identical stdin:
  budget ceiling `13`.
- `--request fixtures/reward_budget/budget_cap.json` and identical stdin:
  budget ceiling `10`.
- `--guided` with `guided_floor.txt` and `guided_cap.txt`: residual `40`, literal
  `USE_RESIDUAL`, complete new request, separate `CALCULATE`, budget `13`/`10`.
- `--guided` with `guided_decline.txt`: residual `40`, explicit decline, no budget.

All paths above are relative to `reference/token_reward/`; exact executed paths
and stdin files are in `commands.json`. File/stdin bytes are checked for equality;
guided success envelopes are compared by real subprocess tests. JSON result
lines carry synthetic provenance/unit; prompts/previews are separate lines.

## Contract findings and non-claims

No explicit contract violation or new contract-undefined behavior was found.
The existing calculation semantics match the requested wrapper: integer floor,
cap, descriptive periods and overflow rejection before cap. Product caps, ratios,
periods and financial components remain **UNDETERMINED — Astra/User**; accounting
treatment remains **UNDETERMINED — User/designated advisers**. Fixture values
are synthetic and establish no product values or accounting decisions.

This work establishes no legal/accounting compliance, real money safety,
production readiness, currency conversion, payouts, chain finality, durable
storage, token activation or independent acceptance. No external services,
settlement/credit connections, reward submission, secrets, public endpoints,
Sui execution, storage engine or hardware/paid-service dependency is involved.
Full hosted protocol/Move/ZK/runtime integration is not claimed by these focused
offline checks.

## Deviations and pending gates

- Fetch omitted under the supervisor's explicit network prohibition; only the
  local main reference was observed. The task input is this session's supplied
  node/design, not a fabricated `docs/tasks/` file.
- Errors are written to stderr; guided prompts/previews and successes to stdout.
  This makes file/stdin stdout one machine-readable success envelope. The design
  did not prescribe stream placement; codes and exit statuses match it.
- Builder delivery is uncommitted. A2 non-author review of the final exact head,
  KTX kernel verification (run ID/status/conclusion: PENDING, unobserved) and KIX
  protocol verification (run ID/status/conclusion: PENDING, unobserved) remain
  supervisor gates. No older CI is transferred. No merge is proposed; final head,
  merge and post-merge checks are not applicable until supervisor publication.

## Verification results

All commands below were actually run from the repository root with bytecode
writes disabled. `commands.json` and named stdout/stderr captures provide the
expanded command-level evidence. No failed test required an implementation fix.

| Command | Actual result |
|---|---|
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_budget_workbench.py` | exit 0; 17 tests passed |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 253 tests passed, including BudgetTests and TL-4 |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | exit 0 each; scanned=375, indexed=340, allowlisted=35; plain checker repeated once for a capture correction |
| `python3.12 scripts/check_status_register.py` and `--self-test` | exit 0 each |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | exit 0 each; 49 existing rows unchanged |
| `python3.12 scripts/check_class_b_index.py` and `--self-test` | exit 0 each; textual index only |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | exit 0 each; new workbench test module reached by token_reward workflow discovery |
| `python3.12 scripts/check_ci_checker_wiring.py` and `--self-test` | exit 0 each |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | exit 0 each; 84-command pin unchanged |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | exit 0 each; publicHost/productionEndpoint false |
| `python3.12 scripts/verify_runtime_architecture.py` | exit 0; architecture/dependency boundaries accepted |
| `python3.12 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `python3.12 reference/token_reward/reward_budget_workbench.py --request reference/token_reward/fixtures/reward_budget/residual.json` | exit 0; residual 40; empty stderr |
| Same CLI `--request reference/token_reward/fixtures/reward_budget/budget_floor.json` | exit 0; ceiling 13; empty stderr |
| Same CLI `--request reference/token_reward/fixtures/reward_budget/budget_cap.json` | exit 0; ceiling 10; empty stderr |
| Same CLI `--request -` with each of the three JSON fixtures as stdin | three exits 0; same envelopes and bytes as corresponding file mode; empty stderr |
| Same CLI `--guided` with `guided_floor.txt`, `guided_cap.txt`, `guided_decline.txt` from the same fixture directory | three exits 0; ceilings 13/10 after selected residual handoff, decline with residual only; empty stderr |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; missing cached `bcs`; tests unavailable, not a pass |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; same missing `bcs`; lint unavailable |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; same missing `bcs`; tests unavailable |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; same missing `bcs`; lint unavailable |
| `git diff --check` | exit 0 |
| `python3.12 validation/2026-11-08-plan-local-reward-budget-workbench/check_preservation.py` | exit 0; all 110 protected files and membership byte-identical, both locked blobs match, all changed paths within scope, file/stdin transcripts match |

The suite and documentation check phases initially overlapped as foreground tool
sessions. Their evidence collectors reused capture number 02. The complete suite
output was recovered as `suite.stdout.txt`/`suite.stderr.txt`; its initial collector
elapsed duration was lost (unittest itself reports 16.107s). Initial docs-index
output was observed in tool output but not retained as a file; that record marks
its capture unavailable, and one fresh plain docs-index run retained the output.
The collector was corrected to read its current record index after command
completion; remaining phases were sequential. No results were fabricated and
no test was repeated to hide a failure.

Rust dependency cache provisioning and the four unavailable Rust checks remain
follow-up verification for the supervisor or CI. There is no in-scope code fix
for a missing offline cache, and no network/download attempt or automatic retry
was made. Local Python acceptance and applicable offline document/architecture
checks are green; these results do not establish merge readiness.
