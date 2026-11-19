# Producer qualification boundary negative controls

## Task and basis

Task ID: `plan-producer-hold-negative-controls`; dependency:
`plan-producer-qualification-tuple-bundle`; audit floor A2; no Astra gate or
merge authority. The supervisor-supplied node specification and read-only design
plan are the task input. No issue or corresponding `docs/tasks/` document
exists; this is not ASTRA program mode. Source supplied by the supervisor:
KIX planner run 1794789397 (`/workspace/kix-run/logs/planner_1794789397`).

Cached `origin/main`, base and starting branch HEAD all equal
`89b5a9348f34c5269fbae17175b543520a6f5b14` on
`agent/kix-plan-producer-hold-negative-controls`. No local base delta was
observed. Fetch was NOT_RUN because the supervisor explicitly prohibited
GitHub/network actions; remote freshness is unverified.

Implementation and final delivery commit SHAs are unavailable: changes are
uncommitted and the supervisor owns git publication. No merge was performed.
The historical provenance SHAs in the unchanged tuple are not this task's base.

## Complete changed paths

- `scripts/check_producer_qualification_tuple.py`: module description and
  `self_test()` only; 27 new detached controls retain the original three.
- `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md`: checker coverage and limits.
- `docs/README.md`: direct navigation to this evidence.
- `validation/2026-11-16-plan-producer-hold-negative-controls/README.md`: this report.

The checker uses fresh `copy.deepcopy(record)` inputs, selects queries by
`name` and surfaces by `id`, and reuses unchanged artifact bytes and presence
information. Exact diagnostic membership is required for every new control;
diagnostic ordering is not asserted. Original validation and catalogue checks
run before and after the controls. No mutation is written to disk.

## Existing coverage mapped before editing

| Requirement | Existing coverage classification | Existing evidence and gap |
|---|---|---|
| Unchanged tuple and catalogue identity | Sufficient | `scripts/check_producer_qualification_tuple.py`: initial `validate()` and `_catalogue_cross_check()` in `self_test()`, plus plain CLI. Retained. |
| Blob drift, missing command, gate source-pin mismatch | Sufficient | The same `self_test()` had three deterministic controls. Retained without duplication. |
| HOLD semantic status/surface and NOT_BOUND read status/surface | Partial | `_check_semantic_and_sd1()`, `_check_surfaces()` and `_check_read_queries()` already reject promotion; no targeted self-test controls. |
| SD1 OPEN/User and forbidden resolution fields | Partial | `_check_semantic_and_sd1()` and the existing SD1 addendum state the boundary; no targeted self-test controls. |
| Non-normative declaration and required non-claims | Partial | Existing `validate()` predicates and `REQUIRED_NON_CLAIMS`; no targeted self-test controls. |
| Missing/duplicate read names and candidate-fixture bindings | Not covered by existing self-tests | Existing `_check_read_queries()` predicates supply the diagnostics; targeted controls added here. |
| SDK manifest negative vectors | Separate sufficient manifest coverage | `sdk/conformance/conformance.test.mjs` exercises the separate verifier, not these tuple boundaries. No duplicate SDK vectors added. |

Predecessor evidence remains at
[the tuple builder report](../2026-11-10-plan-producer-qualification-tuple-bundle/README.md).

## Mutation and diagnostic matrix

Each row starts with a fresh record. All use the existing validator, with
unchanged artifacts. All seven forbidden keys and eight non-claims run
individually, not as a combined failure.

| Mutation | Required existing diagnostic |
|---|---|
| `semantic_hold.status = BOOTSTRAP_SCHEMA_BOUND` | `semantic hold status is not HOLD_SEMANTIC` |
| `semantic_sdk_consumer.status = BOOTSTRAP_SCHEMA_BOUND` | `semantic_sdk_consumer is not HOLD_SEMANTIC` |
| `get_booking.status = BOOTSTRAP_SCHEMA_BOUND` | `read query is not NOT_BOUND: get_booking` |
| `read_query_surface.status = BOOTSTRAP_SCHEMA_BOUND` | `read_query_surface is not NOT_BOUND` |
| `sd1.status = CLOSED` | `SD1 status is not OPEN` |
| `sd1.owner = Builder` | `SD1 owner is not User` |
| Add each SD1 key: `selected_option`, `option`, `options`, `waiver`, `verifier_order`, `resolution`, `resolved` | `SD1 records a forbidden resolution field: <key>` for that exact key |
| `normative = True` | `record must declare normative false` |
| Remove `This record is non-normative identity evidence only.` | `missing non-claim: This record is non-normative identity evidence only.` |
| Remove `No semantic qualification is made.` | `missing non-claim: No semantic qualification is made.` |
| Remove `No N/N-1 qualification is made.` | `missing non-claim: No N/N-1 qualification is made.` |
| Remove `No production qualification is made.` | `missing non-claim: No production qualification is made.` |
| Remove `No audit approval or User approval is made.` | `missing non-claim: No audit approval or User approval is made.` |
| Remove `No read query is published or bound.` | `missing non-claim: No read query is published or bound.` |
| Remove `No SD1 resolution, waiver or verifier order is chosen.` | `missing non-claim: No SD1 resolution, waiver or verifier order is chosen.` |
| Remove `The integration gate is not qualified as production.` | `missing non-claim: The integration gate is not qualified as production.` |
| Remove `get_booking`, adjust recorded count | `read query name set drift` (count diagnostic cannot satisfy the control) |
| Append a detached duplicate of `get_booking`, adjust count | `duplicate read query name` (count diagnostic cannot satisfy the control) |
| Set `get_booking.candidateVector` outside `READ_FIXTURES` | `read query candidate vector drift: get_booking` |
| Change `get_booking.candidateVector` from reservation to allowed resale fixture, keep digest | `read query fixture digest drift: get_booking` |
| Set only `get_booking.fixtureSha256` to 64 zeros | `read query fixture digest drift: get_booking` |

Candidate-binding coverage is limited to allowed paths and digest consistency.
The validator does not enforce a unique query-to-fixture assignment; coordinated
path-and-digest rebinding is outside this coverage. No new rule is inferred.

## Commands and actual results

Commands ran in this worktree in the foreground. Python version:
`3.13.5`; Cargo `1.98.1 (797e8a9bc 2026-08-05)`; rustc
`1.98.1 (48a229cea 2026-09-01)`. Rust commands used
`CARGO_NET_OFFLINE=true`; no dependencies were fetched or installed.

Narrow checker commands ran first, followed by the four focused document
checkers (plain and self-test), then the remaining authoritative workflow
block. All 67 block invocations passed, preserving the stage-5 self-test-only
exception. The table below lists the exact Python commands, in execution order.
The tuple commands also passed separately before the document block.

| Command | Actual result |
|---|---|
| `python3 -B scripts/check_docs_index.py` | exit 0 |
| `python3 -B scripts/check_docs_index.py --self-test` | exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py` | exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| `python3 -B scripts/check_status_register.py` | exit 0 |
| `python3 -B scripts/check_status_register.py --self-test` | exit 0 |
| `python3 -B scripts/check_read_model_source_map.py` | exit 0 |
| `python3 -B scripts/check_read_model_source_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_producer_qualification_tuple.py` | exit 0 |
| `python3 -B scripts/check_producer_qualification_tuple.py --self-test` | exit 0 |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | exit 0 |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | exit 0 |
| `python3 -B scripts/check_rs_profile_traceability.py` | exit 0 |
| `python3 -B scripts/check_rs_profile_traceability.py --self-test` | exit 0 |
| `python3 -B scripts/check_i12_proof_ids.py` | exit 0 |
| `python3 -B scripts/check_i12_proof_ids.py --self-test` | exit 0 |
| `python3 -B scripts/check_delegation_layer_matrix.py` | exit 0 |
| `python3 -B scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| `python3 -B scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_rs_im_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_tl_predicate_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_contract_error_codes.py` | exit 0 |
| `python3 -B scripts/check_contract_error_codes.py --self-test` | exit 0 |
| `python3 -B scripts/check_adapter_identity_map.py` | exit 0 |
| `python3 -B scripts/check_adapter_identity_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_v5_transition_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_readiness_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_readiness_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_settlement_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_settlement_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_bra_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_bra_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_credit_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_credit_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_primary_price_fee_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_ai_delegation_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_lifecycle_adr_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_contract_invariants_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_toss_card_profile_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_bcs1_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_bcs1_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_performance_measurement_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_feature_semantics_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_feature_semantics_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_integration_gate_contract_evidence_map.py` | exit 0 |
| `python3 -B scripts/check_integration_gate_contract_evidence_map.py --self-test` | exit 0 |
| `python3 -B scripts/check_evidence_map_rollup.py` | exit 0 |
| `python3 -B scripts/check_evidence_map_rollup.py --self-test` | exit 0 |
| `python3 -B scripts/check_class_b_index.py` | exit 0 |
| `python3 -B scripts/check_class_b_index.py --self-test` | exit 0 |
| `python3 -B scripts/check_ci_test_discovery.py` | exit 0 |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | exit 0 |
| `python3 -B scripts/check_loopback_host.py` | exit 0 |
| `python3 -B scripts/check_loopback_host.py --self-test` | exit 0 |
| `python3 -B scripts/check_cargo_offline_cache.py` | exit 0 |
| `python3 -B scripts/check_cargo_offline_cache.py --self-test` | exit 0 |
| `python3 -B scripts/check_stage5_host.py --self-test` | exit 0 |

Closest additional local KTX/protocol equivalents and preservation checks:

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; both SHAs and branch as recorded above. |
| `python3 -B scripts/check_producer_qualification_tuple.py` (narrow run) | exit 0; `commands=84 core=40 fsm=44 reads=13`; identity only. |
| `python3 -B scripts/check_producer_qualification_tuple.py --self-test` (narrow run) | exit 0; all 30 controls detected; original inputs still pass after controls. |
| `python3 -B -` (in-memory diagnostic suppression experiment described below) | exit 0; suppressing each of 26 distinct new diagnostic strings independently makes self-test return 1 and print the missing and actual diagnostics. |
| `python3 -B scripts/verify_runtime_architecture.py` | exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 -B scripts/test_runtime_architecture.py` | exit 0; 7 tests, OK. |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; every suite passed. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0; every executed suite passed; one existing analytics engine acceptance test ignored because it requires an owner-provisioned offline bundle. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0. |
| `python3 -B -` (AST and tracked-byte comparison described below) | exit 0; all checker code outside module docstring and self-test unchanged; 3,819 of 3,822 tracked files byte-identical, only the three intended existing paths changed. |
| `git diff --check` | exit 0. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both runs match the exact required blobs in the preservation table. |
| `git diff --exit-code -- .aiops docs/tasks reference/v0.3-rc1 runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json sdk reference/read_model docs/contracts .github/workflows` | exit 0; no protected or out-of-scope diff. |

After filling the evidence tables, the same eight focused invocations for
`check_docs_index`, `check_ci_checker_wiring`, `check_status_register` and
`check_read_model_source_map` (plain and `--self-test`) all passed again.
Plain outputs: docs index `scanned=423 indexed=388 allowlisted=35`; checker
wiring `scripts=36 plain=35 self_test=36 self_test_only=1 docs=22 citations=99`;
status register `paths=577 ev_ids=15 original32=32`; read model source map
`queries=13 anchors=128 catalogues=2 citations=145`.

The suppression experiment loaded the checker with `runpy.run_path`, retained
its original `validate`, and replaced only that in-memory global with a wrapper
that filtered out one exact expected diagnostic. For each distinct new expected
string, it called `self_test()` with captured stdout/stderr and asserted return
1, `missing diagnostic: <string>` and `actual diagnostics:`. It restored the
original validator afterward. The 27 controls have 26 distinct strings because
the allowed-path change and digest-only change share a fixture-digest diagnostic.
No file or validator predicate was mutated by this experiment.

The preservation experiment compared AST dumps of `git show HEAD:<checker>`
and the working file, excluding only the module docstring and `self_test()`.
It compared each tracked file's SHA-256 with the pre-edit snapshot and required
that the changed set equal the three existing paths in the complete list above.
The only new file is this report.

Not run: full hosted protocol CI, bootstrap, localnet/chain execution, ZK
artifact generation, production runtime, optional analytics engine bundle or
external services. These checks do not replace full protocol CI. No broad
runtime behavior or performance claim is made from the local checks.


## Preservation and discrepancies

Before editing, `git hash-object` matched both required blobs:

| Locked file | Required and observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

A SHA-256 snapshot of all 3,822 tracked regular files was captured before edits
in `/tmp/kix-producer-hold-before.json` for comparison after verification.
The tracked-byte comparison passed after the local suites: every tracked file
outside the three intended existing changes is byte-identical, including all
of `reference/v0.3-rc1/**`, both locked kernel files, the producer JSON,
SDK/verifier/generator, manifests, catalogues, fixtures, contracts, CI,
`.aiops/`, task documents and historical evidence. Both locked blobs were
checked again at final handoff, with identical results recorded above.

No new contract violation or contract-undefined behavior was discovered.
The known SD1 verifier-order violation remains unresolved, OPEN, owned by User;
its `extension_profile` interpretation remains `UNDETERMINED — User`.
`BOOTSTRAP_SCHEMA_BOUND`, `HOLD_SEMANTIC` and `NOT_BOUND` retain their meanings
and recorded values. The producer JSON, validator predicates/constants, CLI,
SDK/verifier/generator, manifests, catalogues, fixtures, contracts, workflows,
`.aiops/`, task documents, historical evidence and protected reference are
outside this patch.

## Limits and remaining gates

Builder-authored, source-informed local evidence only. No semantic or N/N-1
qualification, production qualification, audit approval, User approval,
integration-gate production qualification, read publication/binding or
`contract-compatibility-profile` implementation/completion is claimed.
No production durability, distributed fencing, bank exactly-once, chain
finality, legal compliance or protocol-completeness claim follows.

Exact-head KTX CI run ID/status/conclusion: **unavailable / NOT_RUN**.
Exact-head KIX protocol CI run ID/status/conclusion: **unavailable / NOT_RUN**.
Merge commit and post-merge main CI: **not applicable**. A2 non-author exact-head
review and exact-head hosted CI remain supervisor delivery gates; this report
does not propose merge. No commit, push, PR, issue or comment was made.

## Deviations

- The supplied node specification is the task input; no task document was
  created or edited, as planned.
- The required session-start fetch was omitted under the supervisor's explicit
  no-network rule. The recorded main SHA is cached and has not been refreshed.
- Python checks used the available Python 3.13.5 instead of CI's Python 3.12.
  All local checks passed; interpreter parity remains a hosted CI concern.
- The design anticipated potentially missing offline Rust dependencies; they
  were available, so all planned offline Rust checks ran and passed.
- Added an in-memory diagnostic suppression experiment to verify that unrelated
  errors cannot satisfy the new exact-membership assertions. No extra source
  file or validation rule was added.
