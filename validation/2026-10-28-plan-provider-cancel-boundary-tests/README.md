# Offline provider cancellation boundaries — 2026-10-28

Builder-authored evidence for node `plan-provider-cancel-boundary-tests`.
Task input: the supplied node/design prompt from KIX planner run `1793192361`
(`/workspace/kix-run/logs/planner_1793192361`); issue: none; task document under
`docs/tasks/`: absent. Dependency: `plan-plan-provider-fact-normalization-offline`,
whose [validation record](../2026-10-28-plan-provider-fact-normalization-offline/README.md)
is historical evidence, not a current test pass. This node is not in
`.aiops/program.json` and this is not an ASTRA program-mode session.

Local observed `origin/main`, base and start HEAD all equal
`5eb0da1103c3d552813e32f387145b4829bc5010` on
`agent/kix-plan-provider-cancel-boundary-tests`; no local base delta.
The supervisor prohibits network actions, overriding AGENTS §1 fetch;
remote freshness is unverified. Implementation: uncommitted worktree patch.
Final committed implementation/task SHA: unavailable (supervisor-owned).
Merge SHA and post-merge verification: not applicable, no merge performed.

Scope: one test module, this validation record and its docs index entry.
The implementation, fixtures, existing tests, contracts, evidence grades,
owner decisions, CI, `.aiops/**`, `docs/tasks/**`, locked kernel files and
`reference/v0.3-rc1/**` must remain byte-identical.

## Coverage mapped before adding tests (AGENTS §7)

The following table was written after inspecting the existing tests and source,
before creating `test_cancel_boundaries.py`. Test paths are relative to
`reference/provider_facts/`.

| Requirement | Existing coverage | Pre-change classification / gap |
|---|---|---|
| Cancellation type, sign and u128 range through document and text entry points | `test_integer_krw.py::IntegerKrwTests.test_integer_krw_rejects_float_scale_sign_and_range_paths` exercises `totalAmount`; ordinary cancellation amounts appear in `test_one_payment_history.py::OnePaymentHistoryTests.test_cancels_are_items_of_one_payment_not_a_batch` | Partially covered; `cancelAmount` rejection matrix and both entry points missing. |
| Decimal/exponent JSON cancellation tokens without float coercion | The same `IntegerKrwTests` method exercises payment tokens | Not covered for cancellations. |
| Integer cancellation technical boundaries | Payment zero/max in `IntegerKrwTests`; ordinary valid cancellations in `OnePaymentHistoryTests` | Partially covered; cancellation zero, one, above binary64 precision and u128 edges missing. |
| Invalid cancellation before, between and after valid entries | `OnePaymentHistoryTests` covers only valid multi-entry history | Not covered. |
| Unsupported cancellation statuses in mixed history | `test_normalize_verified_only.py::NormalizeVerifiedOnlyTests.test_missing_or_unsupported_payment_and_cancel_statuses_stay_unresolved` covers single-entry missing/null/string/type cases and repetition | Partially covered; mixed-history positions and text entry missing. Reuse broader status-type coverage. |
| No partial return, repeatability and unchanged inputs after rejection | Repetition in the preceding status test and `::test_timeout_not_found_and_unsupported_stay_unresolved` | Partially covered; mixed-history rejection and input preservation missing. |
| Retained valid history/facts/hashes after failures | `NormalizeVerifiedOnlyTests.test_cancel_does_not_erase_the_original_payment_item`; both methods in `test_evidence_hash.py::EvidenceHashTests` | Partially covered; preserve retained objects and re-normalized histories across invalid calls. Existing canonical SHA-256 and ordering rules are sufficiently covered and reused. |
| Suite discovery and docs indexing | `.github/workflows/protocol.yml` runs provider discovery and both checker modes | Existing wiring sufficient; current patch results pending execution. |

Contract basis: [ADAPTER_EVENT_IDENTITY §4.4](../../docs/contracts/ADAPTER_EVENT_IDENTITY.md#44-정규화된-사실)
and [PG_TOSS_CARD_PROFILE §§4–7](../../docs/contracts/PG_TOSS_CARD_PROFILE.md).
Tests are source-informed regressions over public APIs, not independent
provider conformance evidence or a clean-room model.

## Execution and delivery evidence

Before edits: all 1,099 tracked files matched HEAD by Git blob recomputation.
The 108-file `reference/v0.3-rc1/**` manifest (sorted Git tree order, each line
`<git-blob> <path>\n`) SHA-256 was
`ccacd46498373c1c82cf41dfbc5f7537e84ed3867a581775b16e6bb26a6c6466`.
Both kernel worktree blobs matched their required values:

| Path | Before blob | After blob |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

## New regression mapping

All new methods are in
[`reference/provider_facts/test_cancel_boundaries.py`](../../reference/provider_facts/test_cancel_boundaries.py),
class `CancelBoundaryTests`. Fixtures and nested entries are copied with
`deepcopy`; only the intended amount/status field is invalid in each case.

| Method | Gap exercised / assertions |
|---|---|
| `test_cancel_amount_types_sign_and_range` | `True`, `False`, `"5000"`, null and missing `cancelAmount` yield `AMOUNT_SCALE`; `-1` and `-5000` yield `AMOUNT_SIGN`; `KRW_U128_MAX + 1` yields `AMOUNT_RANGE`. Each runs through both document/text entry points at positions 0, 1 and 2 among the two valid `MULTIPLE_CANCELS` entries. A materialized Python `5000.0` separately characterizes document rejection as `AMOUNT_SCALE` at all positions. |
| `test_cancel_json_decimal_and_exponent_tokens` | Literal `5000.0`, `5000.5`, `5e3`, `5E+3` at all three positions. A unique quoted placeholder is serialized once and replaced by numeric text, without Python float construction or default JSON pre-parsing. Repeated parser calls raise `ProviderFactsError` with code `FLOAT_TOKEN`; repeated text normalization returns `Unresolved(FLOAT_TOKEN)`. |
| `test_cancel_integer_technical_boundaries` | `0`, `1`, `2**53 + 1`, `KRW_U128_MAX - 1`, `KRW_U128_MAX` with compatible valid `totalAmount`. Parser and both normalizers preserve exact integer cancellation amounts. Complete histories, per-item normalized facts and hashes agree between entry points. These are technical representation controls only. |
| `test_unsupported_cancel_status_positions` | `"READY"`, missing and null `cancelStatus` at all three positions, through both entry points, remain `Unresolved(STATUS_UNSUPPORTED)`. Existing broader single-entry enum/type coverage is reused. |
| Shared rejection helpers | Before each rejection sequence, retain normalized copies of `PAID`, `PARTIAL_CANCEL` and `MULTIPLE_CANCELS`, complete history snapshots, facts and hashes. Every rejected call returns the exact expected `Unresolved`, exposes no partial `items`, repeats deterministically, and leaves the input document unchanged. Retained histories/facts/hashes and fresh normalization through both entry points still match their snapshots after each rejection. JSON text is preserved; fixture globals are compared to deep copies after every test. Hash equality is required only for unchanged facts, never across changed payment statuses. |

## Commands actually run and results

All commands ran from the repository root. Python checks used
`PYTHONDONTWRITEBYTECODE=1`; Python was `3.13.5` (hosted protocol CI selects
`3.12`). `rustc` and `cargo` were `1.98.1`, matching the workflow toolchain.
Cargo was run offline against the existing dependency cache, in the foreground;
no dependencies were installed and no background jobs were started.

| Command | Actual result |
|---|---|
| `git status --short --branch` | Initially clean; expected branch `agent/kix-plan-provider-cancel-boundary-tests`, tracking `origin/main`. |
| `git rev-parse HEAD origin/main` | Both `5eb0da1103c3d552813e32f387145b4829bc5010`. HEAD remains unchanged; implementation/final committed head not created. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before/after; both required blobs shown above. |
| Read-only Python Git-blob comparison of all `git ls-tree -rz HEAD` entries | Before: 1,099 tracked files match HEAD. After: 1,098 tracked paths outside the allowed docs index change remain byte-identical; legacy 108-file manifest unchanged, as detailed below. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p test_cancel_boundaries.py -v` | PASS, exit 0; all 4 new methods pass. Run first, before broader checks. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -v` | PASS, exit 0; 16 tests, no failures. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py` | PASS, exit 0; 7 reference suites, 8 Node tests, 4 modules; provider suite reaches all 8 test files. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0; 18 negative controls detected. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | PASS, exit 0; scanned 307, indexed 272, allowlisted 35. Rechecked after completing this record. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | PASS, exit 0; all 7 negative controls detected. Rechecked after completing this record. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | PASS, exit 0; architecture v5 and KTX-R1 dependency gate. No runtime activation or durability/performance certification. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_runtime_architecture.py` | PASS, exit 0; 7 tests. Negative fixtures mutate temporary copies only. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS, exit 0; 139 tests across 7 integration suites; unit/doc-test targets contain 0 tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline > /tmp/kix-cancel-boundary-workspace-tests.log 2>&1` | PASS, exit 0; 46 successful target summaries, 339 passed, 0 failed/ignored/measured/filtered. Log inspected with `tail -n 12` and a read-only Python summary of the actual `test result:` lines; no errors/warnings. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS, exit 0. Includes the kernel target checked in KTX CI. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `git diff --exit-code HEAD -- . ':(exclude)docs/README.md'` | PASS, exit 0; no tracked changes outside the allowed index entry. New untracked deliverables are checked separately. |
| `git diff --check` | PASS, exit 0. |
| `git status --short --untracked-files=all` | Exactly the 3 changed paths listed below. |

Workflow inspection: `.github/workflows/protocol.yml` includes the provider suite
in its offline reference discovery loop and runs both checker modes. The Python
test path triggers full verification rather than the documentation-only skip.
The architecture, kernel, Clippy and formatting checks above also correspond to
`.github/workflows/ktx-kernel.yml`; workspace checks correspond to protocol CI.
These local checks are not a full hosted workflow execution. Bootstrap, SDK,
Move/localnet, circuit, storage probes and unrelated protocol jobs were not run;
no network action, installation, real provider or production runtime was needed.

## Changed paths and preservation

Complete changed-path list:

- `reference/provider_facts/test_cancel_boundaries.py` (new)
- `validation/2026-10-28-plan-provider-cancel-boundary-tests/README.md` (new)
- `docs/README.md` (index entry only)

Before edits, a read-only Python script enumerated `git ls-tree -rz HEAD`,
recomputed each Git blob as SHA-1 of `blob <byte-length>\0<file-bytes>` (symlinks
use their target bytes), and asserted equality with HEAD. It saved the manifest
under `/tmp/kix-cancel-boundary-start-manifest.txt`. The final check recomputed
all entries again, excluding only `docs/README.md`, and asserted equality with
the start manifest. All 1,098 excluded-from-edit tracked paths are unchanged.
The 108 legacy paths still produce the same manifest SHA-256
`ccacd46498373c1c82cf41dfbc5f7537e84ed3867a581775b16e6bb26a6c6466`.
This includes the implementation, fixtures, old tests, contracts/status maps,
owner decisions, `.aiops/**`, task documents, CI and both locked kernel blobs.
Status inspection checks that the only new paths are the two allowed files;
Cargo build output is ignored under `runtime/target/` and is not source evidence.

## Delivery gates and deviations

Non-author exact-HEAD A2 review: not performed by this builder. Exact-head
KTX kernel verification and KIX protocol verification run IDs/status/conclusions:
unavailable, not queried or executed. Both workflows and the non-author review
must pass for the supervisor's final committed head before proposing merge.
READY in this handoff means local builder completion only. No merge readiness,
independent review, hosted CI success or production readiness is claimed.

Deviations from the design: none in test scope or behavior. The supervisor's
explicit no-network/no-Git-publication instruction overrides fetch, commit and
GitHub delivery steps. Base freshness, final committed SHA, exact-head A2 review,
both hosted workflows and any authorized merge/post-merge checks belong to the
supervisor. Local test equivalents use offline Cargo and host Python 3.13.5;
they do not substitute for these gates. No PR, issue, comment, ASTRA marker,
commit, push, rebase, branch change, policy edit or protected-file edit occurred.

## Limitations and discrepancy classification

All evidence remains `MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY`, **Analog, NOT Toss**.
Zero, large integers and u128 limits are representation checks of the existing
harness, not product-policy limits, refund eligibility or cumulative-refund
approval. Status rejection characterizes the existing support boundary, not
provider enum completeness or cancellation finality. No provider authentication,
real funds, PG/bank/KYC calls, public endpoints, secrets, Sui, production runtime,
storage engine, identity derivation, new commands or policy values are involved.
No durability, exactly-once, legal compliance or chain-finality claim follows.
Existing external unknowns, owners and grades remain unchanged.

Discrepancy classification: A, existing integer/fact-preservation requirements
match the tested behavior; no explicit contract violation found. The exact
supported-status set, all-or-unresolved return shape and zero/u128 acceptance
are characterized only as existing synthetic harness behavior. Product-policy
and provider-finality semantics remain undefined/UNDETERMINED; none are invented
or promoted by these tests. No newly discovered contract-undefined behavior
requires a decision. Remaining work is independent review, exact-head hosted CI
and the already-recorded external/provider and policy evidence gaps. No node
STOP condition was encountered and no `DECISION_REQUIRED.md` was needed.
