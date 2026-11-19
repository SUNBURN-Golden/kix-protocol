# Offline provider structural rejections — 2026-10-28

Builder-authored evidence for `plan-provider-structural-rejection-tests`.
Task input: the supplied node/design prompt, KIX planner run `1793194686`
(`/workspace/kix-run/logs/planner_1793194686`); issue: none; task document under
`docs/tasks/`: absent. This node is not in `.aiops/program.json`; this is not
an ASTRA program-mode session. Dependency records:
[provider normalization](../2026-10-28-plan-provider-fact-normalization-offline/README.md)
and [cancel boundaries](../2026-10-28-plan-provider-cancel-boundary-tests/README.md).
Their historical results are not inherited as this node's test results.

Evidence label: **MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY — Analog, NOT Toss**.
Scope: new offline stdlib tests, this record and one docs-index link only.

Local observed `origin/main`, supplied base and start HEAD all equal
`40c256be36186e02f6e80480d04af34448e67b35` on
`agent/kix-plan-provider-structural-rejection-tests`; no locally observed base
delta. The supervisor prohibits network actions, overriding AGENTS §1 fetch;
remote freshness is unverified. Implementation/final task SHA: no commit
created, supervisor-owned. Merge SHA/post-merge CI: not applicable.

## Coverage mapped before adding tests (AGENTS §7)

This table was written after inspecting implementation and all existing
provider tests, before creating `test_structural_rejections.py`. Paths below
are relative to `reference/provider_facts/`.

| Requirement | Prior classification | Existing coverage / gap |
|---|---|---|
| Malformed JSON (`DOCUMENT_JSON`) | Not covered | No assertion for syntax errors in existing provider tests. |
| Non-object documents / non-string parser arguments (`DOCUMENT_TYPE`) | Not covered | Existing parser controls use object JSON strings. |
| Literal NaN/Infinity/-Infinity (`UNEXPECTED_CONSTANT`) | Not covered | Float-token coverage does not exercise JSON constants. |
| Unknown/missing/non-string recorded outcomes (`RECORDED_OUTCOME_UNKNOWN`) | Not covered | `test_normalize_verified_only.py::NormalizeVerifiedOnlyTests.test_timeout_not_found_and_unsupported_stay_unresolved` covers supported non-document outcomes only. |
| Missing/non-object payment (`DOCUMENT_TYPE`) | Not covered | Existing binding/status checks use payment objects. |
| Missing/invalid timestamps (`TIMESTAMP_TYPE`, `TIMESTAMP_MISSING`) | Partially covered | `test_timestamps.py::TimestampTests.test_ambiguous_timezone_stays_unresolved_and_raw_text_is_preserved` covers valid raw text/offsets only; invalid receipt, occurrence and cancellation timestamp branches missing. |
| Non-list cancels (`CANCELS_TYPE`) | Not covered | Valid empty/nonempty lists only. Missing/null acceptance requires explicit characterization controls. |
| Non-object cancel entries (`CANCEL_ITEM_TYPE`) | Not covered | Existing mixed-history failures use object entries. |
| Malformed cancellation before/between/after valid entries, no partial history | Partially covered | `CancelBoundaryTests` covers amount/status failures at all three positions, not structural/timestamp exceptions. |
| Positive controls, unchanged inputs, retained valid histories/facts/hashes | Partially covered | Helpers in `test_cancel_boundaries.py` preserve state across amount/status rejection; structural rejection paths missing. `test_one_payment_history.py` and both `EvidenceHashTests` methods sufficiently cover existing one-payment and canonical hash rules. |
| Amount/status boundaries | Sufficiently covered for prior scope | Reuse `test_integer_krw.py::IntegerKrwTests.test_integer_krw_rejects_float_scale_sign_and_range_paths`; all four `test_cancel_boundaries.py::CancelBoundaryTests` methods (`test_cancel_amount_types_sign_and_range`, `test_cancel_json_decimal_and_exponent_tokens`, `test_cancel_integer_technical_boundaries`, `test_unsupported_cancel_status_positions`); `test_normalize_verified_only.py::NormalizeVerifiedOnlyTests.test_missing_or_unsupported_payment_and_cancel_statuses_stay_unresolved`. Do not duplicate these matrices. |
| Discovery/docs indexing | Sufficiently covered wiring | Existing provider suite discovery and plain/self-test checkers in `protocol.yml`; current-patch results pending. |

## Contract basis and characterization boundary

[PG_TOSS_CARD_PROFILE §§4–7](../../docs/contracts/PG_TOSS_CARD_PROFILE.md)
defines verified-fact normalization, fixture limitations, one-payment history
and provider conversion boundaries.
[ADAPTER_EVENT_IDENTITY §4.4](../../docs/contracts/ADAPTER_EVENT_IDENTITY.md#44-정규화된-사실)
requires integer amounts without f64 conversion, raw timestamps with no
invented timezone, and per-item facts/hashes. Retention assertions support
these boundaries within the in-memory fixture only.

Exact Python exception codes, selected timestamp fields and fallback order,
missing/null cancels acceptance, and all-or-exception returns are
source-informed fixture characterizations (AGENTS §8 B), not new contract
semantics or provider conformance evidence. Duplicate-key handling and
timestamp-calendar/offset-range semantics remain undecided and untested.

## New regression mapping

All new methods are in
[`test_structural_rejections.py`](../../reference/provider_facts/test_structural_rejections.py),
class `StructuralRejectionTests`. Mutable fixtures and entries are always
copied with `deepcopy`; no existing test class is imported or subclassed.

| Method | Gap covered / actual assertions |
|---|---|
| `test_malformed_json` | Empty text, truncated object, trailing comma and trailing garbage raise `DOCUMENT_JSON` through parser and text normalization. |
| `test_document_type` | JSON null/list/string/integer/bool roots raise `DOCUMENT_TYPE` through parser and both normalizers. Non-string parser/text arguments (including objects and bytes) separately raise the same code. |
| `test_nonfinite_constants` | Literal `NaN`, `Infinity`, `-Infinity` in an otherwise valid serialized document raise `UNEXPECTED_CONSTANT` through parser and text normalization. A uniquely occurring quoted placeholder is replaced; no Python non-finite float is constructed. |
| `test_recorded_outcome` | Missing/null/empty/unknown/integer/bool/list/object outcomes with the valid authenticated fixture source raise `RECORDED_OUTCOME_UNKNOWN` through both normalizers. |
| `test_payment_type` | Missing/null/list/string/integer/bool payment values raise `DOCUMENT_TYPE` through both normalizers. An empty object is not treated as a payment-type error. |
| `test_timestamp_type` | Direct `raw_timestamp` rejects null/non-string/empty/whitespace/padded text as `TIMESTAMP_TYPE`. Missing and invalid `recorded_at` do the same through both normalizers. Each occurrence field's nonempty whitespace fails when selected; invalid `requestedAt`/`createdAt` also fail when retained as detail behind valid `approvedAt`. |
| `test_timestamp_missing` | All occurrence fields absent, null, false, integer, list, object or empty string are skipped, ending in `TIMESTAMP_MISSING` through both normalizers. |
| `test_timestamp_fallback_controls` | Valid copied timestamps isolate `approvedAt`, then `requestedAt`, then `createdAt` selection; earlier absent/non-string/empty candidates are skipped. Raw selected text and all retained timestamp facts match. Offset-less `createdAt` retains existing unresolved handling. Priority is characterization only. |
| `test_cancels_type` | Object/string/integer/bool cancels raise `CANCELS_TYPE` through both normalizers. |
| `test_missing_null_and_empty_cancels_controls` | Missing, null and empty-list cancels all reproduce the valid PAID history/facts/hashes. This acceptance is fixture characterization only. |
| `test_cancel_item_type` | Null/list/string/integer/bool entries raise `CANCEL_ITEM_TYPE` at positions 0, 1 and 2 among two valid cancellations, through both normalizers. |
| `test_cancel_timestamp_rejections` | A supported-status, valid-amount cancellation with missing/null/non-string/empty/whitespace/padded `canceledAt` raises `TIMESTAMP_TYPE` at all three positions, through both normalizers. |
| Shared helpers (used by every rejection sequence) | First retain copied valid PAID, PARTIAL_CANCEL, MULTIPLE_CANCELS and OFFSET_LESS_CREATED_AT histories, deep snapshots, facts and hashes. Positive controls parse and normalize through both entry points with complete item counts/kinds and shared PaymentRef. Every rejected call checks the exact `ProviderFactsError.code`, unchanged caller inputs, unchanged retained histories/facts/hashes and equivalent fresh normalizations. A caller result sentinel remains unassigned after each exception, including malformed cancellation after valid entries: no partial history is returned. Valid object JSON is explicitly parsed successfully before normalization rejects its structure. Global fixtures are compared with deep snapshots after every method. |

No new amount/status rejection matrix was added. Canonical hash correctness,
original-payment retention, UNKNOWN handling and operation binding reuse prior
coverage; unchanged facts are compared across failed calls, without requiring
hash equality across different payment statuses.

## Commands actually run and results

All commands ran from the repository root. Python was `3.13.5` (hosted
protocol CI selects `3.12`); `rustc 1.98.1 (48a229cea 2026-09-01)` and
`cargo 1.98.1 (797e8a9bc 2026-08-05)` match the workflow toolchain version.
Cargo used the existing cache with `--locked --offline`. Jobs ran in the
foreground; no dependency installation, service, socket or network action
was used. Relevant CI definitions inspected: `protocol.yml` stdlib document
checks/provider discovery/Rust boundary and `ktx-kernel.yml` architecture,
kernel tests, Clippy and formatting. These are the closest applicable local
checks for this patch, not a claim that the whole hosted workflow ran.

In the checker rows below, **both modes** means the exact plain command shown
and that same command with ` --self-test` appended; each was actually run with
`PYTHONDONTWRITEBYTECODE=1` in its environment, in a sequential subprocess batch.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Exit 0; initially clean, expected branch, both SHAs `40c256be36186e02f6e80480d04af34448e67b35`. Final status has exactly the three authorized paths. |
| `python3 --version`; `rustc --version`; `cargo --version` | Exit 0; versions recorded above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` and `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (via read-only Python subprocesses) | Exit 0 before/after; both required blobs match the table below. |
| Read-only `python3 -B` SHA-256 path/byte manifest capture and comparison | PASS, exit 0; identical 110-file protected manifest and path set, including all 108 legacy files, before/after. |
| Read-only `python3 -B` Git-blob comparison of every `git ls-tree -rz HEAD` entry | PASS, exit 0; 1,101 tracked files checked; all 1,100 tracked paths outside `docs/README.md` byte-identical to HEAD. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p test_structural_rejections.py -v` | PASS, exit 0; 12 new test methods. Run first, before broader checks. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS, exit 0; 28 tests. |
| `python3 scripts/check_ci_test_discovery.py` — both modes | PASS, exit 0 each; 7 reference suites, provider discovery reaches all 9 test files, 8 Node tests, 4 modules; 18 negative controls. |
| `python3 scripts/check_docs_index.py` — both modes | PASS, exit 0 each; scanned 308, indexed 273, allowlisted 35; 7 negative controls. Rechecked after completing this record. |
| `python3 scripts/check_adapter_identity_map.py` — both modes | PASS, exit 0 each; 17 rows, 71 citations, unchanged counts; negative controls all detected. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` — both modes | PASS, exit 0 each; 41 rows; 3 positive controls and 77 negative fixtures. |
| `python3 scripts/check_evidence_map_rollup.py` — both modes | PASS, exit 0 each; 25 contracts; 16 negative controls. |
| `python3 scripts/check_class_b_index.py` — both modes | PASS, exit 0 each; existing textual index 217 rows/72 sources/45 symbols; 20 negative controls. No index or grade change. |
| `python3 scripts/check_ci_checker_wiring.py` — both modes | PASS, exit 0 each; 35 scripts, 34 plain, 35 self-test, 1 self-test-only, 22 docs, 99 citations; 13 negative controls. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | PASS, exit 0; architecture v5 + KTX-R1 dependency gate. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/test_runtime_architecture.py` | PASS, exit 0; 7 tests, temporary-copy negative fixtures only. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS, exit 0; 139 tests across 7 integration suites; unit/doc targets have 0 tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline > /tmp/kix-provider-structural-workspace-tests.log 2>&1` | PASS, exit 0; 46 successful target summaries, 339 passed, 0 failed/ignored/measured/filtered. Actual log summaries inspected with read-only Python; no error/warning diagnostics. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings > /tmp/kix-provider-structural-clippy.log 2>&1` | PASS, exit 0; log inspected, no warnings/errors. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `git diff --check`; `git diff --stat`; `git status --short` | PASS, exit 0; clean diff whitespace and expected paths only. New files also inspected directly (Git diff omits untracked file contents). |

## Complete changed paths and preservation

- `reference/provider_facts/test_structural_rejections.py` (new)
- `validation/2026-10-28-plan-provider-structural-rejection-tests/README.md` (new)
- `docs/README.md` (one adjacent validation link)

Before edits the worktree was clean and both required kernel blobs matched.
The before/after manifest maps each protected path to its SHA-256 byte digest.
Its own digest is SHA-256 of `json.dumps(manifest, sort_keys=True).encode()`:
`9c7c90516fd728796b19b905abb0513235dddd91ccf5eea02838d53f487efaed`
before and after. All 110 protected files match, with no legacy additions or
deletions; 108 are under `reference/v0.3-rc1/**`.

| Locked path | Before Git blob | After Git blob |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The all-tracked-file Git-blob comparison also confirms unchanged implementation,
fixtures, existing tests, contracts, evidence maps/grades, CI, `.aiops/**` and
`docs/tasks/**`. No transient mutation of protected files was performed;
checker negative fixtures run in memory or temporary copies only.

## Delivery gates, deviations and remaining uncertainty

Local implementation is complete and checks pass; **READY for supervisor
handoff only**, not merge-ready. Implementation/final committed task HEAD is
unavailable because the supervisor owns commits and publication; the branch
HEAD remains `40c256be36186e02f6e80480d04af34448e67b35` plus this patch.

| External gate | Run ID | Status / conclusion |
|---|---|---|
| Exact-final-head KTX kernel verification | Unavailable | Not queried or run here; unknown. |
| Exact-final-head KIX protocol verification | Unavailable | Not queried or run here; unknown. |
| Non-author exact-HEAD A2 review | Unavailable | Pending supervisor delivery; this builder report is not independent review. |
| Merge / post-merge main CI / final-merge blob check | Not applicable | No merge authorized or performed. |

Deviations: AGENTS §1 fetch omitted under the explicit supervisor no-network
rule; local main freshness cannot be established. The design command's
`PYTHONDONTWRITECODE` typo was corrected to `PYTHONDONTWRITEBYTECODE` and `-B`
retained for architecture tests. No scope deviation or required policy
decision arose. No commit, push, PR, issue or comment was made.

No explicit contract violation (AGENTS §8 C) was found. Contract-undefined
characterizations (AGENTS §8 B) are the exact error codes, timestamp field
selection/skipping/retention validation, absent/null cancels acceptance and
exception propagation without partial return. Duplicate-key handling,
timestamp-calendar and offset-range semantics remain undecided; no expectation
was added for them. A future authorized task may investigate these gaps.

Provider unknowns retain their existing owners: I02 User/Toss contract and
technical teams, I03 User/Toss sales, I04/I05/TM04 Toss technical, I08 Toss/PG
account operations, and TM05 Toss technical/security. Identity derivation,
alias/schema choices and policy values stay with Astra/User per the contracts;
durable custody remains outside this fixture and with the existing stage-5
work. No owner, unknown, open item or evidence grade was changed.

Non-claims: source-informed offline synthetic regression evidence only, not
clean-room independence, real Toss behavior, provider authentication or
finality, durable custody, bank exactly-once, chain finality, policy approval,
operational behavior or production readiness. No real funds/provider/bank/KYC
calls, public endpoints, Sui testnet/mainnet, storage engine, production runtime,
credentials, new coin/TIX module or new protocol command were used or added.
The full hosted workflow, network/HTTP services, Move/ZK checks and unrelated
SDK/application checks were not run; local checks do not satisfy exact-head CI
or non-author review gates.
