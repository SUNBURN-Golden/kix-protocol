# plan-consumer-binding-ci-guard — builder validation

## Task and basis

Task ID: `plan-consumer-binding-ci-guard`. Task input is the supervisor-supplied
node specification and read-only design plan in the builder prompt. No issue
or `docs/tasks/` task document exists for this node. This is a non-ASTRA
session, audit floor A2, no Astra gate, no merge authority. Dependencies:
`plan-commerce-consumer-binding-index` and
`plan-producer-qualification-tuple-bundle`.

Branch: `agent/kix-plan-consumer-binding-ci-guard`. Observed cached
`origin/main`, base and starting HEAD all equal
`f52c58743b2919cbc66ab9c2760ecc76742faca7`; initial worktree clean, no local
base delta. `git fetch origin main` was NOT_RUN under the supervisor's explicit
no-network rule; remote freshness is unverified. No base change was made.
Implementation/final delivery commit SHAs are unavailable: the supervisor owns
commits and publication. No merge commit or post-merge verification applies.

## Changed paths

- `.github/workflows/protocol.yml`: exactly two standalone invocations after
  the producer-tuple checker pair in `Stdlib offline document checks`.
- `docs/README.md`: link to this record under Consumer surface boundaries.
- `validation/2026-11-13-plan-consumer-binding-ci-guard/README.md`: this evidence.

The existing consumer checker and historical validation records are reused
unchanged. No wrapper or generic checker extension was added.

## Existing coverage mapping

| Requirement | Before edit | Existing evidence / change |
|---|---|---|
| Run consumer checker plain and self-test in CI | Not covered | Two invocations added to the unguarded stdlib step. |
| Reject artifact drift, missing commands, broken journey references | Sufficient | Existing consumer `self_test()` controls: drifted artifact digest, missing command, broken journey reference, journey action mismatch. |
| Reject read/semantic status upgrades | Sufficient | Existing `read_upgraded` and `semantic_claim` controls exercise read/profile validation. |
| Other malformed bindings | Sufficient | Existing unknown command, multiple/absent status and unresolved body-schema controls. |
| Producer identity preserved | Sufficient | `scripts/check_producer_qualification_tuple.py`, plain and self-test. |
| Generic CI wiring and docs index | Partially covered | Existing checker suites; generic wiring scans only `scripts/check_*.py`, so direct workflow placement inspection is also required. New README is indexed. |

No duplicate test suite added. The new evidence closes only the CI invocation
gap, not a semantic qualification gap.

## Wiring verification

The stdlib step has no `if`, `continue-on-error`, alternate working directory
or failure-swallowing expression. Both new commands are standalone at the
existing indentation. Its position follows the tree lookup and precedes guarded
heavy verification. Neither `steps.scope.outputs.docs_only` nor
`steps.verified.outputs.hit` controls this step. The existing non-draft job
eligibility and normal failure/prior-step-success behavior remain unchanged.
The stage-5 host checker retains its self-test-only exception.

Only the two invocation lines change in the workflow. Both workflows classify
the workflow-file change as non-documentation, so runtime architecture and
offline Rust equivalents are included in local verification. A local replay
does not simulate GitHub's scheduler or prove a hosted run occurred.

## Commands and actual results

Commands run in the
foreground at `/workspace/kix-run/wt/plan-consumer-binding-ci-guard`, with
`PYTHONDONTWRITEBYTECODE=1` for Python and `CARGO_NET_OFFLINE=true` for Cargo.
Python is 3.13.5; Cargo and rustc are 1.98.1 (the workflows pin Rust 1.98.1).
Python `-B` is used for the narrow checks; the stdlib block is replayed verbatim
with bytecode disabled through the environment.

| Command / inspection | Exit | Actual result |
|---|---:|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse origin/main HEAD` | 0 | Requested directory/branch; initial status clean; both refs at the basis SHA above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before edit) | 0 | Both required hashes match (Preservation below). |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | 0 | `consumer binding index ok: commands=84 core=40 fsm=44 mock=27 bootstrap=57 reads=13 not_bound=13 journey_steps=44 journey_actions=27`; `non-normative navigation only; BOOTSTRAP is not consumer acceptance`. |
| Same consumer command with `--self-test` | 0 | All ten controls detected; `self-test: pass (10 negative controls)`. |
| `python3 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | 0 each | `producer qualification tuple identity ok: commands=84 core=40 fsm=44 reads=13`; three controls detected; `self-test: pass`. |
| `python3 -B scripts/check_ci_checker_wiring.py` and `--self-test` | 0 each | `scripts=36 plain=35 self_test=36 self_test_only=1 docs=22 citations=99`; `self-test: pass (13 negative controls)`. |
| `python3 -B scripts/check_docs_index.py` and `--self-test` (narrow and final evidence checks) | 0 each | `docs index ok: scanned=411 indexed=376 allowlisted=35`; seven controls detected; `self-test: pass`. |
| Python placement assertions over the stdlib step header/body | 0 | Unguarded step; exact pair immediately after producer pair; stage-5 self-test only; 67 invocations extracted. |
| Python comparison of working workflow with `git show HEAD:.github/workflows/protocol.yml`, removing the added pair | 0 | `workflow delta: exactly the two required standalone invocations; all conditions and failure behavior unchanged`. |
| `python3 -B scripts/verify_runtime_architecture.py` | 0 | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 -B scripts/test_runtime_architecture.py` | 0 | Seven tests; `OK`. |
| `python3 --version`; `cargo --version`; `rustc --version` | 0 | Python 3.13.5; Cargo 1.98.1; rustc 1.98.1. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 139 passed, 0 failed, 0 ignored across test binaries. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | 0 | Finished dev profile; no warnings. |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | No formatting diff/output. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 339 passed, 0 failed, 0 ignored across test binaries (includes the 139 kernel tests). |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Finished dev profile; no warnings. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after checks) | 0 | Both required hashes match again. |
| Python SHA-256 comparison against the before-edit snapshot | 0 | `protected snapshot matches: 110 files byte-identical`. Includes the full frozen reference directory and both locked files. |
| `git diff --name-only HEAD` plus `git ls-files --others --exclude-standard`, compared to the three-path allowlist | 0 | Exactly the three Changed paths above, including the untracked README. |
| `git diff --check` | 0 | No whitespace errors. |
| `git diff --exit-code HEAD -- .aiops docs/tasks runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1 docs/contracts docs/status sdk validation/2026-11-10-plan-commerce-consumer-binding-index validation/2026-11-10-plan-producer-qualification-tuple-bundle .github/workflows/ktx-kernel.yml` | 0 | No protected, pinned, contract, SDK, dependency-evidence or KTX workflow diff. |

Narrow checks ran first, under `set -euo pipefail`. For the full stdlib replay,
Python extracted every ten-space-indented invocation between this step's
`run: |` and the following `- uses:` into
`/tmp/consumer-binding-stdlib.sh`, then invoked
`bash -euo pipefail -x /tmp/consumer-binding-stdlib.sh`. The commands were not
rewritten. The local temporary harness/logs are not repository artifacts.


### Full stdlib replay results

`bash -euo pipefail -x /tmp/consumer-binding-stdlib.sh` exited **0**: all
67 standalone invocations succeeded. The table records each command and an
actual output excerpt. The consumer and producer plain outputs have additional
identity details in the narrow-check table above. Host reports describe this
runner only, not a host selection or grant of permission.

| Command (repository root; bytecode disabled) | Exit | Actual output excerpt |
|---|---:|---|
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=577 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_producer_qualification_tuple.py` | 0 | identity only; no semantic or operational qualification |
| `python3 scripts/check_producer_qualification_tuple.py --self-test` | 0 | self-test: pass |
| `python3 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | 0 | non-normative navigation only; BOOTSTRAP is not consumer acceptance |
| `python3 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | 0 | self-test: pass (10 negative controls) |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=411 indexed=376 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=202 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=198 ASSERTED=198 COVERED=198 CLASS_B=1 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=71 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=186 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | 0 | settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | 0 | self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | 0 | bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | 0 | self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | 0 | credit evidence map ok: rows=24 headings=24 items=5 citations=134 COVERED=16 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | 0 | self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | 0 | primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | 0 | self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | 0 | ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | 0 | self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | 0 | lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | 0 | self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | 0 | contract invariants map: 27 rows, corpus, anchors, test symbols, counts, locked blobs and F-B1 document pins OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | 0 | contract invariants self-test: 2 positive controls and 97 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | 0 | Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | 0 | Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | 0 | BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | 0 | self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | 0 | performance evidence map ok: Counts: rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | 0 | self-test: pass (2 positive controls, 81 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | 0 | feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | 0 | self-test: pass (81 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | 0 | integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | 0 | self-test: pass (100 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_evidence_map_rollup.py` | 0 | evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | 0 | self-test: pass (16 negative controls) |
| `python3 scripts/check_class_b_index.py` | 0 | class B index ok: rows=218 sources=73 symbols=47; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | 0 | self-test: pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | 0 | ci checker wiring ok: scripts=36 plain=35 self_test=36 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | 0 | self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | 0 | ci test discovery ok: reference_suites=9 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | 0 | self-test: pass (18 negative controls) |
| `python3 scripts/check_loopback_host.py` | 0 | all_ok=true; host_selected=false; gate_suite_run=false; permission_granted=false (runner loopback context only) |
| `python3 scripts/check_loopback_host.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_cargo_offline_cache.py` | 0 | present=18 total=18 missing=[] |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | 0 | self-test: pass |

## Preservation

Before editing, `git hash-object` returned the required kernel blobs:

| Path | Required / observed before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

A SHA-256 snapshot of the two locked files and every file under
`reference/v0.3-rc1/` was recorded before editing (110 files).
The after-check comparison matched every path and digest. The full changed-path
allowlist also confirms the consumer index JSON, producer tuple and all their
pins, statuses, journey bindings and historical evidence are unchanged.

## Non-claims and remaining gates

BOOTSTRAP remains catalogue-schema-binding only (`bootstrap-2`), not consumer
acceptance. Semantic SDK consumption stays `HOLD_SEMANTIC`; all 13 read names
stay `NOT_BOUND`. SD1 remains the existing class-C verifier-order blocker,
User-owned, `OPEN` and unresolved; this node neither fixes nor waives it.
External consumer expectations remain `UNVERIFIED`; product policy remains
`UNDETERMINED` with its existing owners.

No new contract violation or contract-undefined behavior was found in this
wiring-only scope. No contracts, status records, SDK artifacts, protocol
commands or runtime behavior change. No semantic acceptance, N/N−1
qualification, durability, production readiness, real funds/provider calls,
chain finality, independent review or capability-grade promotion is claimed.
The full hosted workflow, SDK behavioral suites, Move/localnet and ZK suites
were not run; no tooling was bootstrapped into the frozen reference tree.
These results cover the requested stdlib block and the design plan's local
architecture/Rust equivalents, not every job of the protocol workflow.

Exact-final-head KTX CI run ID/status/conclusion: NOT_RUN / unavailable.
Exact-final-head KIX protocol CI run ID/status/conclusion: NOT_RUN / unavailable.
Post-merge main CI: not applicable. No commit, push, PR, issue, comment or merge
was performed. Local builder handoff still requires supervisor publication,
non-author exact-HEAD A2 review, exact-head CI and any later User merge approval.

Deviations: startup fetch omitted under the supervisor no-network rule;
implementation/final delivery SHAs await supervisor commits. Python checks used
the available Python 3.13.5 rather than CI's 3.12 environment; Rust matched the
workflow pin. No implementation deviation. No publication or readiness
transition is authorized by this local result. READY means local builder handoff
only, not merge-ready.
