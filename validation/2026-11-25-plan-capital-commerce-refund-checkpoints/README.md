# Capital Commerce refund checkpoints

## Task and base

The supervisor-supplied node specification and design for
`plan-capital-commerce-refund-checkpoints` are the task input. The node has no
issue or file under `docs/tasks/`. The corresponding local planner entry was
found in `/workspace/kix-run/logs/planner_1795523250_codex0.last.md`.

The branch is `agent/kix-plan-capital-commerce-refund-checkpoints`. The observed
local `origin/main` tracking ref and the starting task HEAD both resolve to
`1af97ed2bb5ba79ec2122832e60c0febbb0f37c5`, which agrees with the stated base.
Remote freshness is unverified under the supervisor's offline instruction, which
overrides the startup fetch. Implementation and final task commit SHAs await
the supervisor's commit. The exact-head KTX and KIX CI run IDs, statuses and
conclusions are unavailable for the working-tree patch. A2 non-author review
is pending. Merge SHA and post-merge CI do not apply.

## Existing coverage and added evidence

| Requirement | Coverage before this node | Added evidence |
| --- | --- | --- |
| Digest and exact receipt, settlement and claim identity | Partial. `CommerceLinkedRefundVectorTests.test_complete_output_bytes_and_references` covers producer replay and input pointers. | `test_checkpoint_replay` hashes raw source bytes before decoding and verifies schema, case, literal pointer and order, enclosing action, accepted receipt and the `claim-1` / `trade-claim-1` / `KRW` identity. |
| Verbatim committed face and three zero-variance observations | Partial. `SettlementCreditBoundaryTests.test_credit_journal_stores_the_literal_face` covers literal snapshots and `SettlementVarianceContractTests.test_all_scenarios_replay_to_expected` covers the observer. | One Commerce claim enters a test-only offer and draw verbatim. The complete observer envelopes match the fixture, and each compares 10,001 KRW of settlement outstanding to the same frozen 10,001 KRW face. |
| Requester refund and repayment separation | Partial. `CommerceLinkedRefundVectorTests.test_purchase_stages_and_partial_acceptance` covers the settlement progression. `SettlementCreditBoundaryTests.test_s4_refund_obligation_and_partial_acceptance_are_visible` covers the F04 boundary with a different synthetic claim. | The three receipts establish 0 → 4,000 → 2,500 KRW outstanding, with 1,500 mock-accepted and 1,500 PG adjustment outstanding at the last checkpoint. Drawn and outstanding exposure are both 10,000 KRW, and repayment is zero. The full F04 snapshot is compared after each observation. |
| Equal-variance pointer swap | Missing for these receipts. The existing companion index tests cover other families' crossed references. | `test_swapped_checkpoint` proves both crossed claims still produce zero variance before the replay rejects the swapped association. `test_commerce_refund_checkpoints_crossed_references` rejects crossed index pointers, a re-pinned detached pack swap, and raw source digest drift. |
| Refund component and observer authority | Sufficient for the standalone variance observer. Partial for the linked Commerce claim. | Every full observed envelope preserves `refund_component=NOT_BOUND`, `contract_status=NOT_BOUND`, `repair=NONE`, `fail_closed=true`, `mutates_state=false` and `authorizes_exposure=false`. |

[Producer replay](../../reference/booking_resale_admission/test_commerce_linked_refund_vectors.py) · [Boundary replay](../../reference/credit_advance_f04/test_settlement_credit_boundary.py) · [Variance replay](../../reference/credit_advance_f04/test_settlement_variance_contract.py) · [Capital checkpoint replay](../../reference/credit_advance_f04/test_capital_commerce_refund_checkpoints.py) · [Capital index tests](../../reference/credit_advance_f04/test_capital_companion_evidence_index.py)

## Local verification

Commands run from the repository root use Python 3.12.15 and Rust 1.98.1.
For discovery, `bra=reference/booking_resale_admission`,
`f04=reference/credit_advance_f04`, `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`.

| Command | Result |
| --- | --- |
| `git rev-parse origin/main HEAD` and `git symbolic-ref --short HEAD` | Both SHAs match the stated base, and the branch matches the task. |
| `sha256sum reference/booking_resale_admission/fixtures/commerce_linked_refund_receipts_v1.json` | `7181761ec5533cf1a9aab450f4a7f3d32ed6c467713c8d532ceff24a89908839` matches the plan and fixture. |
| `PYTHONPATH=.:reference/credit_advance_f04 PYTHONDONTWRITEBYTECODE=1 python3.12 -` (fixture and index generation) | First invocation stopped before writing with `KeyError: 'body'` while reading the S4 offer. Rerun read its `arguments` and wrote the canonical fixture and index entry. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_linked_refund_vectors.py` | 5 passed on both runs. |
| `python3.12 -m unittest discover -s "$f04" -t "$f04" -p test_capital_commerce_refund_checkpoints.py` | 2 passed on both runs. |
| `python3.12 -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 16 passed on both runs. |
| `python3.12 -m unittest discover -s "$f04" -t "$f04"` | Initial exit 1 during discovery when a Commerce module shadowed the Capital `test_restore_fingerprint_equivalence`. An inline Python discovery probe omitting the new replay found 323 tests and loaded the correct module. Deferring the Economics helper imports in the new replay fixed the collision. The full rerun passed all 325 tests. |
| `python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the seven other workflow reference suites | `settlement_f01_f03` 224, `booking_resale_admission` 1,085, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99 passed. |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | Both exit 0. The contract pins cover 84 commands, including 40 core and 44 FSM. |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0. `productionEndpoint=false` and `publicHost=false`. |
| `python3.12 -m unittest integration_gate.test_offline_limits` | 11 passed. |
| `python3.12 -m unittest integration_gate.test_http_gate readiness.test_faults` | 139 passed. The existing HTTP suite emitted a `ResourceWarning` for an unclosed stream. |
| `python3.12 -` invoking each Python command from the workflow's **Stdlib offline document checks** step | All 69 commands exited 0, including docs index, CI discovery, settlement, Commerce and credit evidence maps and their self-tests. |
| `python3.12 scripts/check_docs_index.py` and `python3.12 scripts/check_ci_test_discovery.py`, both plain and with `--self-test` | All four final documentation checks exited 0. The index covered 427 documents with 35 allowlisted, and CI discovery included 30 F04 test files. |
| `python3.12 scripts/verify_runtime_architecture.py` and `python3.12 scripts/test_runtime_architecture.py` | Architecture gate passed. All 7 tests passed. |
| `cargo fmt --all -- --check` from `runtime/` | Exit 0. |
| `cargo test -p kix-kernel --locked --offline` | Runtime workspace exit 101 before compilation. Temporary workspace exit 0, 139 passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Runtime workspace exit 101 before compilation. Temporary workspace exit 0. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` | Runtime workspace exit 101 during resolution. Temporary workspace exit 0, only normal dependency `kix-types`. |
| `cargo test --workspace --locked --offline` | Runtime workspace exit 101 before compilation. Six-crate temporary workspace exit 0, 332 passed. |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Runtime workspace exit 101 before compilation. Six-crate temporary workspace exit 0. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` | Exit 1, with 14 of 378 locked registry archives available. Missing entries included `duckdb`, `libduckdb-sys` and `bcs`. |
| `python3.12 -B -` for temporary Rust workspace, with `diff -qr` on each copied crate | All six crate trees matched. The temporary manifest selected those crates and reused their original lockfile blocks. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0, recorded the KTX workflow input hashes. |
| `git hash-object` on the two locked paths and the new fixture | Exit 0, matches the identities below. |
| `find reference/v0.3-rc1 -type f -print0 \| sort -z \| xargs -0 sha256sum`, then `cmp` of before and after manifests | Both manifests list 108 files and match byte for byte. |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks docs/contracts .github/workflows reference/booking_resale_admission` | Exit 0. |
| `git diff --check`, `git status --short --untracked-files=all`, and inline Python using `git show` and `git ls-files` | Whitespace checks passed, including added files. The prior index serialization matched after removing the appended pack. Exactly eight paths changed. |

The full Rust workspace could not resolve `duckdb` for `kix-analytics-audit`
from the offline index. The temporary workspace used `kix-types`,
`kix-feature-semantics`, `kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and
`kix-delegated-exec`. Full-workspace Rust test and Clippy results remain
unverified for `kix-analytics-audit` and `kix-bcs1`. Hosted bootstrap, Move,
chain, storage and ZK jobs are outside the local checks for the touched paths.

## Protected and fixture identities

| Artifact | Verified identity |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `reference/v0.3-rc1/**` | Sorted SHA-256 manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` before and after. |
| `capital_commerce_refund_checkpoints_vectors_v1.json` | SHA-256 `6d0ac8fb018d5bdb55a388eb8353ab538e533bdb3ad547de72d75de02714085a` and Git blob `49cf3276c0a9386b410cd5b0260af84421fe368f` match both index pins. |

## Files changed

- `docs/README.md`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `reference/credit_advance_f04/fixtures/capital_commerce_refund_checkpoints_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_commerce_refund_checkpoints.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `validation/2026-11-25-plan-capital-commerce-refund-checkpoints/README.md`

## Scope and remaining gates

The observed behavior matched the supplied contract and receipt predicates.
No explicit contract violation or additional contract-undefined behavior was
found. This is source-informed, synthetic Class B evidence. External
`kix-capital` acceptance is `UNVERIFIED`. The replay covers mock observations
and process-local state. It leaves live funds, PG/bank/KYC, public endpoints,
chain finality, durability, distributed execution, legal/accounting treatment
and production readiness outside its verification scope. Product limits and
tolerance policy remain `UNDETERMINED` with Astra, netting mechanics with
the User, and legal refund liability with the User and legal counsel.

The next delivery evidence is non-author A2 review and successful KTX and KIX
CI for the supervisor's exact final commit.
