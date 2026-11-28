# Capital statement component identity builder evidence

Task `plan-capital-statement-component-identity` uses the supplied node envelope
and design from planner run `1795815309`. The node has no GitHub issue or
`docs/tasks/` task document. The worktree branch is
`agent/kix-plan-capital-statement-component-identity`. The initial HEAD and
cached `origin/main` both resolve to `4609a91def3923bc12d4518a646e9e4544b201a2`,
matching the supplied base. The supervisor's offline rule precludes the startup
fetch, so remote freshness is unverified.

## Coverage before the change

Test paths are relative to `reference/credit_advance_f04/` unless shown in full.

| Acceptance | Existing coverage | New evidence |
| --- | --- | --- |
| Equal totals, frozen face, exposure and variance | Partial. `test_capital_later_statement_vectors.py::CapitalLaterStatementVectorTests.test_checkpoint_arithmetic` and `test_frozen_credit_and_observers` cover the fee history. | `CapitalStatementComponentIdentityTests.test_statement_component_identity` compares independent branches from the entire pinned checkpoint, matches the fee branch to L1, and checks the arithmetic in both. |
| Distinct accepted entries | Partial. `test_capital_later_statement_vectors.py::CapitalLaterStatementVectorTests.test_statement_identity_and_replay` covers the fee entry. | The replay compares the six-entry prefix plus one complete normalized entry per branch and ties the branch snapshot to its journal pointer. |
| Fresh-key conflict and zero accepted appends | Partial. `reference/settlement_f01_f03/test_statement_adapter.py::StatementAdapterTests.test_duplicate_movement_and_conflicting_binding_match_direct_fsm` covers a changed cash/fee binding. | Each replay submits the opposite fee/held split with `stmt-2-other-split`, verifies the full refusal, and compares both journals and the snapshot across the call. |
| Swapped journal references | Uncovered. `test_capital_companion_evidence_index.py::CapitalCompanionEvidenceIndexTests.test_later_statement_crossed_references` covers L1 statement/replay references. | `test_statement_component_identity_swapped_journal_refs` exercises the crossed index pointers, crossed fixture pointers with recomputed pins, and exchanged journal bodies at the correct positions. |
| `NOT_BOUND` and `repair=NONE` | Partial. `test_capital_later_statement_vectors.py::CapitalLaterStatementVectorTests.test_frozen_credit_and_observers` covers the original fee observation. | The paired replay checks both complete observer mappings and the refund, fail-closed, mutation and authorization fields. |

## Observed results

Both branches append one statement for `part-2` with 40,000 fixture KRW gross
and 37,000 cash. The entries record `(fee, held)` as `(3,000, 0)` and `(0, 3,000)`.
Both branches report the same settlement claim, a frozen 100,000 KRW F04 face
with 60,000 cash on face, 15,000 drawn and outstanding with zero repaid, and
−60,000 variance with a separate +37,000 cash delta. Both crossed submissions
return `STATEMENT_BINDING_CONFLICT` with zero accepted appends. Both variance
and shared-exposure observations retain `NOT_BOUND` and `repair=NONE`.

The [companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#statement-component-identity)
contains 23 packs, 484 entries, 132 supplemental observations and 12 supporting
entries. The two new observation records each point to their branch's accepted
journal entry.

## Local verification

Python verification used Python 3.12.15 with `-B`, `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`. Cargo ran offline on toolchain 1.98.1.

| Command | Result |
| --- | --- |
| `git status --short --branch` and `git rev-parse HEAD refs/remotes/origin/main` | Clean branch at startup. Both refs matched the envelope base. |
| `python3.12 -B -` with `PYTHONPATH=.:reference/credit_advance_f04` to replay and serialize the pack and append its index entry | Generated canonical vector bytes and both artifact pins. The index edit preserved the prior content byte for byte. |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_capital_statement_component_identity.py` | 1 passed. |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_capital_later_statement_vectors.py` | 4 passed. |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_capital_companion_evidence_index.py` | 23 passed. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"`, for each of the eight reference suites in the protocol workflow | 2,462 passed. `settlement_f01_f03` 224, `booking_resale_admission` 1,105, `credit_advance_f04` 341, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99. |
| `python3.12 -B -` invoking the Python commands in `.github/workflows/protocol.yml` under **Stdlib offline document checks** | 69 of 69 invocations passed, including the docs index, CI discovery, and settlement and credit evidence maps and their self-tests. The host probe exercised local loopback only. |
| `python3.12 -B scripts/check_docs_index.py` and `python3.12 -B scripts/check_ci_test_discovery.py` after recording results | Both passed. The docs checker scanned 483 documents, and CI discovery reached all 37 F04 test files. |
| `python3.12 -B scripts/check_openapi_contract.py` and `python3.12 -B scripts/check_integration_gate_openapi.py`, each plain and with `--self-test` | All four invocations passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 18 passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed and 7 architecture tests passed. |
| `cargo fmt --all -- --check` in `runtime/` | Exit 0. |
| `cargo test -p kix-kernel --locked --offline`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline`, `cargo test --workspace --locked --offline` and `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in `runtime/` | Each exited 101 before compilation. Workspace dependency resolution could not find `duckdb`, required by `kix-analytics-audit`. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` | Exit 1. The cache had 16 of 378 locked registry archives. Missing archives included `duckdb`, `libduckdb-sys` and `bcs`. |
| `python3.12 -B - "$scratch"` and `diff -qr` for each copied crate | Created an ignored scratch workspace using byte-identical copies of six local-only crates and their existing lockfile blocks. All six comparisons passed. The scratch workspace was removed after verification. |
| `cargo test -p kix-kernel --locked --offline --quiet`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` and `cargo tree -p kix-kernel --edges normal --locked --offline` in the scratch workspace | 139 kernel tests passed. Clippy exited 0. Normal dependencies consisted of `kix-types`. |
| `cargo test --workspace --locked --offline --quiet` and `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in the scratch workspace | 332 tests passed. Clippy exited 0. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Captured the three KTX workflow source hashes. |
| `git hash-object`, `sha256sum`, and sorted `find ... -print0` with `sort -z`, `xargs -0 sha256sum` and `cmp` | Both kernel locks and both L1 pins matched before and after. All 108 preserved paths and hashes matched. The new vector's two pins matched. |
| `git diff --check`, scoped `git diff --exit-code HEAD`, `git status --short --untracked-files=all` and inline Python comparing the JSON index against `git show` | Whitespace and protected scope checks passed. Exactly eight paths changed. The original companion index bytes match after removing the new pack. |
| `python3.12 -B -` checking `git diff --name-only HEAD` and `git ls-files --others --exclude-standard` against the record | All eight paths, whitespace, the direct validation link and the index counts matched. |

## Protected bytes and fixture pins

| Artifact | Verified identity |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` before and after |
| `reference/v0.3-rc1/**` | 108 files, path-and-SHA-256 manifest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` before and after |
| `capital_later_statement_v1.json` | SHA-256 `1d0e7e806258b3bdaca08da0d4486fcdaf119fdb41470ac48f4df4602821ae4b` before and after |
| `capital_later_statement_vectors_v1.json` | SHA-256 `8d9949eec525ade2369437dde20f11f3aaa0a70b1d0a387af36bd64f33294317` before and after |
| `capital_statement_component_identity_vectors_v1.json` | SHA-256 `cae9854cc5da29bb1d45bb2c9adf620821c822fafac09e838a1b05bce403a79e`, Git blob `01e86fe9731f00e5b5ff145f425394437e65cd13` |

## Changed paths

- `docs/README.md`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `reference/credit_advance_f04/fixtures/capital_statement_component_identity_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `reference/credit_advance_f04/test_capital_statement_component_identity.py`
- `validation/2026-11-28-plan-capital-statement-component-identity/README.md`

## Deviations and remaining gates

The supervisor's offline rule superseded the startup fetch. The scratch Rust
workspace used `kix-types`, `kix-feature-semantics`, `kix-feature-ir`,
`kix-kernel`, `kix-kernel-v5` and `kix-delegated-exec`. Actual-workspace Rust
test and Clippy coverage remains unverified with `kix-analytics-audit` and
`kix-bcs1` in the workspace because registry dependencies are unavailable.
The opposed statement submissions use the fixture-local key
`stmt-2-other-split`, unused in either independent branch at submission.

The paired replay is source-informed Class B evidence. The builder observed
zero contract violations and zero new contract-undefined characterizations.
External `kix-capital` acceptance is `UNVERIFIED`. Product limits and
tolerances remain `UNDETERMINED` with Astra and legal responsibility remains
`UNDETERMINED` with the User and legal counsel. The evidence covers in-memory
mock journals and observations. Live funds, external providers, public
endpoints, durability, distributed execution, chain finality, legal
compliance and production readiness remain outside its verification scope.

Implementation and final task commit SHAs await the supervisor's commit.
A2 non-author review and exact-head KTX and KIX run IDs, statuses and
conclusions are pending delivery gates. Merge SHA and post-merge CI are
inapplicable to the working-tree patch.
