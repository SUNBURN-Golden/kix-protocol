# Primary price/fee offline boundaries — builder validation

## Basis and delivery boundary

Node: `plan-primary-fee-split-offline-differential`. Date: 2026-10-25.
Task document: the supervisor-supplied node specification and read-only design
plan in the builder prompt; no corresponding issue or `docs/tasks/` file exists.
Source: KIX planner run 1792876090. Not ASTRA program mode; no signer or delivery
marker. Author is the builder: this record is not an independent PASS, an A2
audit, or a grade increase.

Branch: `agent/kix-plan-primary-fee-split-offline-differential`.
Starting HEAD/base and locally observed cached `origin/main` are both
`53c16b226346f2df824f93a5756a080acd489ec1`; no local base delta.
`git fetch origin main`: NOT_RUN because the supervisor explicitly prohibits
network actions, overriding AGENTS §1. Remote freshness is unverified.
Implementation/final task head: uncommitted working-tree patch over that base;
no new SHA exists. No commit, push, PR, issue or comment was made.

Exact-head KTX kernel verification and KIX protocol verification: run IDs
unavailable, status/conclusion NOT_RUN/not queried. Pending supervisor commit,
publication, exact-head CI and non-author review. Earlier-SHA CI does not
transfer. Merge SHA, final-merge blob verification and post-merge main CI are
not applicable. READY here means local builder delivery, not merge-ready.

## Changed paths

- `reference/settlement_f01_f03/test_primary_fee_split.py`
- `reference/booking_resale_admission/test_primary_price_binding.py`
- `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md`
- `docs/README.md`

No mock, FSM, contract, evidence map, error-code catalogue, capability register,
task, `.aiops/`, CI, Move or frozen reference file is changed.

## Coverage before and after (AGENTS §7)

Paths below are relative to the repository root. Requirements are from
`docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md` §3 and §7, with synthetic
examples from §5. This record does not rewrite that historical coverage section.

| Requirement | Before (citations) | After | Status |
|---|---|---|---|
| PF-C01 off-chain | PARTIAL: `reference/booking_resale_admission/test_mock_gates.py::GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay` tests 10_000 against 10_001 and bool rejection; `test_reservation_fsm.py::ReservationFsmTests.test_unbound_issue_is_memory_evidence_without_economic_finality` checks a price mismatch; `test_reservation_rejection_atomicity.py::ReservationRejectionAtomicityTests.test_confirm_price_mismatch_leaves_no_trace` covers rejection/control atomicity. | `test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests` adds five prices (1, 2, 7_777, MAX−1, MAX), valid off-price neighbors and extremes, seven invalid money values, and 20 seed-37 prices with neighboring amounts. Every rejection is followed by exact-price binding with the same order ID. | Boundary-covered for `MockGates.bind_order` only. Existing `reservation_fsm.py`, `admission_fsm.py` and `resale_fsm.py` paths cited, not extended. |
| PF-C02 off-chain | Sufficiently covered for the formula: `reference/settlement_f01_f03/test_settlement_properties.py::SplitPropertyTests` has the 12×6 boundary grid, Fraction oracle, eight seeds × 40 cases, roles, zero suppression and invalid inputs; `test_mock_settlement.py::SettlementMockTests.test_f01_fee_floor_zero_fee_and_rejected_policies` covers floor/zero/rejected policy cases. Missing explicit PF-C02 goldens, all four §5 examples, False and integer-valued float variants. | `test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests` adds eight hand-written boundary goldens, four §5 rows, seven bps and seven amount rejection cases, and four different seeds × 50 cases using the direct PF-C02 integer formula. Checks fee/residual roles, positive faces, zero-line suppression, floor inequalities and conservation. | Sufficiently covered off-chain in this mock; existing broad coverage reused. |
| PF-C01 and PF-C02 on-chain | NOT_COVERED: frozen `reference/v0.3-rc1/sui/sources/rights.move` has no primary price or primary fee field; `issue_paid` does not split. Contract §1/§7 records the gap. | No Move or contract changes or chain execution. | **NOT_COVERED**. Enforcement location remains **DECISION_REQUIRED · Astra** (§6). |
| Comparison with v0.3-rc1 | No standalone executable comparison in this suite. `core.py` imports six non-stdlib siblings by bare module name; primary split is inline in `Core._commit_trade`. | `V03CoreDifferentialStatusTests` reads AST only, verifies the import layout and inline primary fee key; `SiblingImportPathTests` checks local module origins and absence of the frozen directory from `sys.path`. | **NOT_MADE**; class B importability characterization, not equivalent implementation evidence. |
| PF-C03, PF-C04, PF-C05 | Existing proposed event timing, refund linkage and resale isolation are outside this node. | Unchanged; no new claim about these predicates. | Out of scope. |

`MAX` above is the existing money bound `10**12`, not a product price.
Additional existing lifecycle coverage is retained in
`reference/booking_resale_admission/test_admission_fsm.py::AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`
and `test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential`.
These are lifecycle evidence, not additional primary fee coverage.

## Differential: NOT_MADE

Frozen `reference/v0.3-rc1/core.py:14–19` uses bare imports of `common`,
`finance`, `lifecycle`, `observations`, `contracts` and `dispatch`.
They are sibling files, not standard-library modules. File-path loading alone
does not resolve them; making them available would require additional import
path/module setup. The #284 sibling-path guard and this node's design prohibit
injecting them into `sys.path` or `sys.modules`. No executable import was attempted,
no module was copied or shimmed, and the frozen reference was read only as text.
The AST check is a source-informed class B characterization of this layout,
not a runtime import experiment or an executable differential.

The arithmetic is inline in `Core._commit_trade` (`core.py:155–165`), rather than
a standalone split API. A complete comparison would also need the SQLite-backed
prepare/accept/capture/commit flow. That is not run here. Any future comparison
requiring different import allowances belongs in a separate node/decision.

## Findings, boundaries and remaining uncertainty

- A: tested PF-C01/PF-C02 predicates match the stated mock contracts.
- B: the frozen core's import layout is characterized above; no new contract
  semantics are invented. General residual priority remains **UNDETERMINED**
  under settlement contract §0.3.
- C: no explicit contract violation observed in the executed tests.

Actual price/bps values, fee recipient, fee inclusion/on-top treatment, fee on
refund and enforcement location all remain **DECISION_REQUIRED · Astra**.
No new protocol command or product policy is needed or selected here; no STOP
condition was encountered and no `DECISION_REQUIRED.md` is required.

Numbers are synthetic. The 100000/500 adapter fixtures are not used in the new
tests as values or policy. No production use, runtime activation, durability,
bank exactly-once, chain finality, legal/accounting compliance, performance or
production readiness is claimed. No real funds, PG/bank/KYC call, public endpoint,
Sui testnet/mainnet, storage engine, coin/TIX module or secret was used.

## Commands actually run and results

All verification ran from the worktree root in foreground subprocesses; no
background/detached job, network provisioning, git publication or CI query ran.
Python commands below used `PYTHONDONTWRITEBYTECODE=1`. A stdlib driver ran each
listed child command sequentially with `subprocess.run`, captured its exit code
and output, and stopped on failure. All validation commands passed on their
first run; no mock discrepancy or repair/retry was needed. Read-only inspection
used `cat`, `sed`, `rg`, `git status`, `git rev-parse` and workflow inspection.

Baseline, before adding tests or the validation record:

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 187 tests passed. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 402 tests passed. |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=237 indexed=202 allowlisted=35 |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |

Narrow checks, before broader verification:

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03 -p test_primary_fee_split.py -v` | Exit 0; 7 tests passed. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_primary_price_binding.py -v` | Exit 0; 3 tests passed. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |

Closest local equivalents of protocol.yml's reference/HTTP/OpenAPI steps:

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 194 tests passed. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 405 tests passed. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0; 147 tests passed. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Exit 0; 85 tests passed. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; 168 tests passed. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0; 100 tests passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test: pass |

Settlement increases from 187 to 194 tests (+7); booking from 402 to 405 (+3).
The five reference suites total 999 passing tests. HTTP/readiness adds 100.
No suite reported skips or failures. Counts are supporting evidence, not an
acceptance criterion by themselves.

The complete 27-command `Stdlib offline document checks` block was extracted
from the actual workflow (command count asserted as 27) and run sequentially:

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=364 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=238 indexed=203 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Index counts change from `scanned=237 indexed=202 allowlisted=35` to
`scanned=238 indexed=203 allowlisted=35`: exactly one new indexed validation
record. Error-code counts remain identical to baseline: 199 raised, asserted
and covered; CLASS_B=0 and CLASS_C=0 in that catalogue. This catalogue result
does not classify the separate core importability characterization.
Synthetic faults intentionally detected by checker self-tests are expected
negative controls, not failures in this repository.

Additional non-CI evidence-map checks:

| Command | Actual result |
|---|---|
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=106 COVERED=12 PARTIAL=5 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (31 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=212 COVERED=21 PARTIAL=15 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |

Closest local KTX architecture/kernel/lint/format/dependency checks:

| Command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `rustc --version` | Exit 0; rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo --version` | Exit 0; cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 78 tests passed; 0 failed; doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; Finished successfully with -D warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; No formatting diagnostics (check only). |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; kix-kernel v0.1.0 → local kix-types v0.0.0 only. |

These use the already installed Rust/Cargo 1.98.1 toolchain. Cargo commands use
`--offline` where applicable, with `CARGO_NET_OFFLINE=true` and
`RUSTUP_AUTO_INSTALL=0`; no dependencies or toolchain were downloaded. No Rust
file changed; whole-workspace formatting is check-only. Unrelated workspace
crate tests were not run.

Final scope and preservation checks:

| Command / one-time check | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` | Both `53c16b226346f2df824f93a5756a080acd489ec1`; cached ref only. |
| `git branch --show-current` | `agent/kix-plan-primary-fee-split-offline-differential`. |
| `git status --short` / `git status --porcelain --untracked-files=all` | Initially clean; after implementation, exactly the four changed paths listed above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before and after; both required blobs match (table below). |
| `git diff --exit-code HEAD -- reference/v0.3-rc1` | Exit 0; empty diff. |
| `git status --porcelain --untracked-files=all -- reference/v0.3-rc1` | Exit 0; empty. |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| Stdlib one-time frozen-tree check using `git ls-tree -rz HEAD -- reference/v0.3-rc1`, Git blob hashing of on-disk bytes, full `Path.rglob` path set and executable-mode comparisons | Exit 0; all 108 files, complete path set, bytes and executable modes match HEAD. |
| Stdlib AST scan of both new test modules for numeric literals 100000 and 500 | Exit 0; neither fixture value is used. |
| Stdlib expected changed-path-set assertion from `git status --porcelain --untracked-files=all` | Exit 0; exactly four planned paths. |
| `git diff --check` | Exit 0; no whitespace errors. |

## Locked and frozen evidence

Before edits and after verification, `git hash-object` matched both required blobs:

| File | Required / observed before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Frozen reference HEAD tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
All 108 on-disk reference files, their path set, bytes and executable modes match
HEAD. Both locked files and the frozen reference remained untouched throughout.
Final-merge verification is not applicable (no merge).

## Deviations and not-run checks

Fetch and all git/GitHub publication or queries were omitted under the explicit
supervisor instruction. No task document exists in `docs/tasks/`; the supplied
node specification is the immutable task input. Executable differential is
NOT_MADE for the planned, AST-checked reason above.

Move, localnet, ZK, Node/TypeScript, dependency provisioning and
`scripts/verify_runtime.py`: NOT_RUN (outside touched paths and the offline test
plan). Hosted workflows and artifact upload: NOT_RUN. Full Rust workspace tests
were not run for this Python-test-only patch; the offline KTX checks above
are additional local evidence, not production runtime execution. The design was
otherwise followed; no implementation-scope deviation was needed.
