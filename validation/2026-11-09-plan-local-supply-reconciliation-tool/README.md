# Local synthetic supply reconciliation builder evidence

Node: `plan-local-supply-reconciliation-tool`. Task input: the supervisor's
inline node specification and read-only design plan; no issue or document under
`docs/tasks/` exists for this node. This is not an ASTRA program-mode session.
The task began on 2026-11-08; the environment advanced to 2026-11-09 before
verification, which is the evidence directory date.

Observed local `origin/main`, base and unchanged task HEAD:
`c530b26ddd2487d686cf0a1d3f52e6b404d2741f` on
`agent/kix-plan-local-supply-reconciliation-tool`. Initial `git status --short`
was empty. No fetch was run: the supervisor explicitly prohibited every network
action, overriding AGENTS.md §1's fetch step. Current remote freshness is
unverified. There is no delta between cached origin/main and task HEAD.
Implementation and final commit SHA: not assigned; the supervisor owns commits.
No commit, push, PR, issue, comment, merge, tag or branch mutation was performed.

## Delivered behavior and boundary

The additive dispatcher and one-request stdlib CLI call the existing
`supply_report(events)` or `reconcile_supply(offchain, chain_supply)` once.
Arguments have no defaults and supplied reports reach reconciliation unchanged.
The CLI preserves model results, rejection codes, synthetic figure and reported
`stop_payout` flag. Error responses retain scope metadata and a supported
operation when one was identified. Fixtures provide complete synthetic inputs.
See the [usage and schema](../../reference/token_reward/README.md#local-supply-reconciliation).

No new protocol command, policy value, socket, chain client, dependency,
persistence, runtime flag or economic action is introduced. Events describe
hypothetical inputs. A reported `stop_payout=true` executes no stop.
Supply policy and operational responses remain **UNDETERMINED — Astra/User**.

## Coverage mapped before adding interface tests

All paths in this table are under `reference/token_reward/`.

| Requirement | Existing coverage classification | Added interface evidence and gap |
|---|---|---|
| Report arithmetic and five reconciliation classes | Sufficient: `test_reward_model.SupplyTests.test_v6_supply_recompute_and_alarm_classes` | `SupplyDispatchTests.test_complete_result_parity_forwarding_and_input_preservation` and CLI fixture journeys compare complete direct results, preserve event order and verify only the selected wrapper call |
| Duplicate events | Sufficient: `SupplyTests.test_duplicate_supply_event_is_rejected` | Dispatcher and subprocess parity for duplicate event arrays and duplicates inside supplied reports preserve `SUPPLY_EVENT_DUPLICATE` |
| Tampered report totals | Sufficient: `SupplyTests.test_tampered_report_is_recomputed_and_rejected`; `test_tl4_model_properties.SupplyPropertyTests.test_TL4_V6_tamper_duplicate_holder_and_stop_payout` | Forward original report identity, retain missing/altered totals and `SUPPLY_REPORT_MISMATCH`, call no wrapper-side report repair |
| Caller-entered chain integer | Sufficient: `SupplyTests.test_chain_figure_is_only_the_supplied_integer` and TL-4 properties | Serialization rejects coercion from booleans, strings, floats, exponent notation and out-of-range integers; Unicode survives unchanged |
| Both causes precedence | Partial: TL-4 allows either alarm while requiring stop flag | Wrapper/direct parity and real CLI characterize current `UNAPPROVED_PATH` precedence, class B only |
| Synthetic labels, result fields, errors and input preservation | Not covered for new interface | Exact envelope/result equality, notice and `SYNTHETIC_SUPPLY_FIGURE`, original domain exception identity, metadata forwarding and no input mutation |
| File/stdin, decoding and diagnostic integration | Shared decoding sufficient; new CLI integration not covered | Real subprocess byte parity, exact canonical JSON, strict keys/finite numbers/UTF-8/Unicode, trailing JSON, missing files, usage stderr, null/supported operation diagnostics |
| No calculation on malformed input; import starts nothing | Not covered for new interface | Instrument both wrapper functions and assert neither runs; subprocess import has no output/action |

New tests are `test_supply_reconciliation.py` (5 interface tests) and
`test_supply_cli.py` (6 integration tests). They reuse model tests and TL-4
properties rather than reimplementing arithmetic or an independent oracle.

## Actual local verification

All test invocations set `PYTHONDONTWRITEBYTECODE=1`. The focused invocation also
sets `PYTHONPATH=reference/token_reward`. The machine-readable
[command ledger](commands.json) contains exact commands, exit statuses, and
separate stdout/stderr logs for every validation invocation, including any
unsuccessful attempt. See the final results table below.

| Command (from repository root) | Actual result |
|---|---|
| `PYTHONPATH=reference/token_reward python3 -m unittest test_reward_model.SupplyTests test_tl4_model_properties.SupplyPropertyTests test_supply_reconciliation test_supply_cli` | exit 0; 18 tests passed (Python 3.13.5) |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 261 tests passed |
| `PYTHONPATH=reference/token_reward python3.12 -m unittest test_reward_model.SupplyTests test_tl4_model_properties.SupplyPropertyTests test_supply_reconciliation test_supply_cli` | exit 0; 18 tests passed (Python 3.12.15, matching CI's minor version) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 261 tests passed |
| `python3 scripts/check_docs_index.py` and `--self-test` | both exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | both exit 0 |
| `python3 scripts/check_class_b_index.py` and `--self-test` | both exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | both exit 0 |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | both exit 0; token_reward suite reached by protocol discovery |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | both exit 0; 84 commands, unchanged pin |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | both exit 0; productionEndpoint=false, publicHost=false |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; architecture/dependency gate passed |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | **UNAVAILABLE**, exit 101; cached `bcs` absent, no tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | **UNAVAILABLE**, exit 101; same dependency-resolution failure, no lint executed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0; no findings |
| `git diff --check` | exit 0; no findings |

The checked workflow definitions were `.github/workflows/protocol.yml` and
`.github/workflows/ktx-kernel.yml`. Python 3.12 matching protocol CI is provisioned
and was also used for focused then full-suite verification; see the additional
rows above and ledger. No implementation or tests changed after the passing runs.
The offline Cargo cache failure is an environment limitation, not a passing
Rust result. It is also recorded by preceding local-tool nodes. No dependency
download, retry, CI edit or scope expansion was used to bypass it. Unrelated
SDK, Move, localnet, ZK, storage and other suite jobs were not run.

## Actual CLI transcripts

[Transcript ledger](transcripts.json) records all 18 real subprocess commands,
exit statuses and adjacent stdout/stderr captures: each of nine fixtures in
file and stdin modes. Each pair produced byte-identical canonical stdout and
empty stderr. Seven fixtures exited 0, including all alarming results;
duplicate and tampered fixtures exited 1 in both modes.

| Fixture | Result (both input modes) |
|---|---|
| `supply_report.json` | Complete unchanged synthetic report |
| `supply_match.json` | MATCH, mismatch=false, stop_payout=false |
| `supply_holder_burn.json` | HOLDER_BURN_OUTSIDE_LAYER, mismatch=false, stop_payout=false |
| `supply_unexplained.json` | UNEXPLAINED, mismatch=true, stop_payout=false |
| `supply_unapproved_mint.json` | UNAPPROVED_MINT, mismatch=true, stop_payout=true |
| `supply_unapproved_path.json` | UNAPPROVED_PATH, mismatch=true, stop_payout=true |
| `supply_both_causes.json` | UNAPPROVED_PATH, mismatch=true, stop_payout=true (class-B characterization) |
| `supply_duplicate.json` | SUPPLY_EVENT_DUPLICATE |
| `supply_tampered.json` | SUPPLY_REPORT_MISMATCH; supplied layer_supply=0 is not repaired |

Reproduce any row from the repository root with
`python3 reference/token_reward/supply_cli.py --request reference/token_reward/fixtures/<fixture>`
or `python3 reference/token_reward/supply_cli.py --request - < reference/token_reward/fixtures/<fixture>`.

## Preservation, discrepancies and delivery gates

Before work, `git hash-object` returned the required blobs:

| Locked file | Before blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Before work, `git ls-tree HEAD reference/v0.3-rc1` recorded tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Final byte comparisons and complete
changed paths are recorded in [preservation.json](preservation.json) and
[changed_paths.txt](changed_paths.txt). Both locked blobs still match the table
above. All 108 legacy reference files match their HEAD blobs. Every one of the
1,875 tracked files outside the two authorized README edits matches its HEAD
blob byte-for-byte, including models, FSMs, sessions, contracts, catalogue,
runtime flags, CI, `.aiops/` and task documents. The JSON records the comparison
method, count, path-list digest and actual Git command output. A final merge
blob check is not applicable because no merge occurred.

Changed paths comprise the dispatcher and CLI, two interface test files, nine
`reference/token_reward/fixtures/supply_*.json` fixtures, the two usage/index
README edits, and this validation directory's report, ledgers and captured logs.
The linked text manifest enumerates every changed file, including artifacts.

Explicit contract violations found: none. Contract-undefined observations:
the existing class-B priority of UNAPPROVED_PATH over UNAPPROVED_MINT is
preserved, per [TL-4 §6.B](../../docs/decisions/TL4_THREAT_MODEL_20261009.md).
Reconciliation checks six numeric totals against events; report metadata is not
fully validated or authenticated. The wrapper deliberately adds no nested
semantics or metadata normalization.

Exact-head KTX and KIX workflow run IDs/status/conclusions: unavailable, not
requested or checked under the no-network instruction. A2 non-author
exact-final-head review and both completed/success workflows remain supervisor
delivery gates. No merge occurred; merge SHA and post-merge checks are not
applicable. Local success is no merge authorization or independent review.

Not tested/claimed: independent chain verification, V1–V5, authenticated
approvals/reports, mint/allocate/burn/payout execution, real funds, providers,
Sui networks, storage durability, distributed behavior, production readiness,
legal conclusions or policy selection. Full protocol CI is not reproduced by
these focused offline equivalents. Future work needs separate task authority.

Deviations: fetch omitted under explicit supervisor prohibition; inline task
input used as explicitly supplied, with no task document created. Publication,
commits, external review and hosted CI remain with the supervisor. No design
semantics deviation.

Builder state: implementation and applicable Python/document/architecture
verification complete locally; offline Rust test/Clippy unavailable. Ready for
supervisor handling, subject to the pending review and exact-head CI gates above.
