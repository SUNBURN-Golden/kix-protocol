# Producer read-query fixture associations

## Task and provenance

Task: `plan-producer-read-association-check`, Integration step 1. The supervisor's
node specification and design plan in the session are the immutable task input;
no issue or corresponding `docs/tasks/` document exists. Dependencies:
`plan-producer-hold-negative-controls`, `plan-read-model-contract-fixture-prep`.
Source: planner run 1794869012 (`/workspace/kix-run/logs/planner_1794869012`),
supplied provenance only, not independently inspected. Audit floor A2; no Astra
gate, merge authority or ASTRA program mode.

Starting branch: `agent/kix-plan-producer-read-association-check`. Cached
`origin/main`, base and starting HEAD: `def945f6a3afdb8ba0088a6e627dd7a0c6784cc2`.
No local base delta. Fetch omitted under the explicit supervisor no-network rule;
remote freshness unverified. Implementation/final delivery SHA unavailable:
changes remain uncommitted for the supervisor. No merge or GitHub action.

Before editing, both locked blobs matched their required IDs:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (kernel lib) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (quarantine capacity test).
A SHA-256 inventory of all 3,925 tracked regular files was captured in
`/tmp/kix-read-association-before.json` for final byte comparison.

## Existing coverage recorded before checker edits

| Acceptance | Coverage | Existing test/evidence and gap |
|---|---|---|
| Unchanged tuple passes | Sufficient | Plain CLI and initial/final `validate()` plus `_catalogue_cross_check()` in `scripts/check_producer_qualification_tuple.py:self_test()`. Both baseline commands passed: 84 commands, 40 core, 44 FSM, 13 reads; 30 existing controls. |
| Coordinated path/digest rebinding | Partial | Existing allowed-path mutation requires a digest-drift diagnostic; matching replacement digest bypasses it. |
| Missing fixture ownership | Not covered | Existing missing-name control removes a tuple row, not the fixture query. |
| Duplicate fixture ownership | Not covered | Existing duplicate-name control duplicates a tuple row, not query ownership. |
| Kind disagreement | Partial | Tuple versus manifest checked; fixture body kind ignored. |
| False promotion | Sufficient | All 30 existing self-test controls, documented in `validation/2026-11-16-plan-producer-hold-negative-controls/README.md`; retain unchanged. |
| Fixture behavior | Sufficient | `reference/booking_resale_admission/test_read_model_fixtures.py:ReadModelFixtureTests`: byte reproduction, manifest hashes, point/list replay, deterministic replay, non-mutation, non-claims and NOT_BOUND. Reuse suite plus generator `--check`. |
| Related identity/document checks | Sufficient existing checks | Read-model source-map, consumer-binding, docs index, status register and CI checker wiring; run normal/self-test plus full workflow stdlib block. |

## Complete changed paths

- `scripts/check_producer_qualification_tuple.py`: derive query owners/kinds
  solely from `READ_FIXTURES` bodies; cross-check fixture/manifest/tuple names,
  manifest file set/digests and tuple artifact pins; detached self-test controls.
- `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md`: strengthened checks and limits.
- `docs/README.md`: direct link to this evidence.
- `validation/2026-11-17-plan-producer-read-association-check/README.md`: this report.

`validate(record, artifacts, present) -> list[str]` remains free of file I/O;
CLI arguments and exit codes are unchanged. All owners are collected before
checking uniqueness. No hardcoded query-to-fixture table, query-prefix heuristic
or tuple-path ownership inference is used. Non-object fixture/manifest data and
invalid kinds fail with diagnostics rather than exceptions.

## Detached mutation matrix

All 30 existing controls are retained. The following extend focused coverage;
135 negative controls and one positive control passed in the narrow self-test.
Every new record is a deep copy; artifact mappings are detached with immutable
byte values. A self-test-only re-pin helper updates fixture SHA-256/Git blob,
manifest file SHA-256, every affected tuple query hash and manifest artifact
SHA-256/Git blob. It writes no fixture or producer artifact to disk.

| Mutation/control | Required diagnostic or result | Gap addressed |
|---|---|---|
| Append whitespace to a fixture and consistently re-pin | No problems | Positive check of the re-pin helper and acceptance of association-preserving bytes. |
| Each of 13 queries redirected to another valid fixture with its matching digest | `read query association path mismatch: <name>` | Coordinated path/digest rebinding. |
| Remove each query from its fixture, retain manifest/tuple entries, re-pin | `read query association missing: <name>` | Missing ownership, distinct from a missing tuple row. |
| Copy each query to another fixture, re-pin | `read query association duplicate: <name>` | Duplicate ownership, distinct from a duplicate tuple row. |
| Change each fixture kind to the other valid kind, re-pin | `read query association kind mismatch: <name> (manifest)` | Fixture-body kind now participates in association checks; tuple disagreement also reported. |
| Change each manifest kind alone, re-pin manifest | `read query association kind mismatch: <name> (manifest)` | Manifest versus fixture. |
| Change each tuple kind alone | `read query association kind mismatch: <name> (tuple)` | Tuple versus fixture. |
| Change each manifest and tuple kind together, keep fixture kind | `read query association kind mismatch: <name> (manifest)` | Coordinated metadata disagreement with the fixture. |
| Invalid UTF-8/JSON; non-object fixture, queries or query; invalid kind | Exact unreadable/shape diagnostic or `kind mismatch ... (fixture)` | Malformed fixture inputs reject without throwing. |
| Missing fixture bytes | `read fixture unreadable: <path> (KeyError)` | Unavailable fixture inputs reject without throwing. |
| Unexpected fixture query | `unexpected read fixture query: unexpected_query` | Unequal fixture/manifest/tuple name sets. |
| Non-object manifest, manifest files or manifest queries | Exact shape diagnostic | Malformed manifest inputs reject without throwing. |
| Extra/missing manifest file; malformed file entry | Exact file-set/entry diagnostic | Exact five-file manifest inventory. |

The 91 per-query controls and six malformed-fixture controls require the named
association/shape diagnostic **and absence of incidental digest, SHA-256,
Git-blob or byte-drift errors**. The positive control requires an empty problem
list. Missing bytes and malformed manifest file maps inherently produce further
missing-byte/digest diagnostics, so those separate controls assert their exact
structural diagnostic. The unchanged inputs are compared with snapshots and
revalidated, including the catalogue cross-check, after all controls.

## Commands and actual results

Commands run in the foreground; a local Python harness captures each command's
combined output, exit status and elapsed time in `/tmp` before continuing. No
long job is launched with shell backgrounding. Narrow tests ran before broader
checks. The authoritative `protocol.yml` **Stdlib offline document checks**
block was extracted and executed verbatim, with `PYTHONDONTWRITEBYTECODE=1`.
All 67 invocations passed; the stage-5 plain invocation remained omitted.

Available Python: `3.13.5` (CI pins `3.12`). Cargo:
`1.98.1 (797e8a9bc 2026-08-05)`; rustc:
`1.98.1 (48a229cea 2026-09-01)`. Rust commands use
`CARGO_NET_OFFLINE=true`; no dependency installation or fetch is performed.


### Narrow checks

| Command | Actual result |
|---|---|
| `python3 -B scripts/check_producer_qualification_tuple.py` | exit 0; commands=84 core=40 fsm=44 reads=13 |
| `python3 -B scripts/check_producer_qualification_tuple.py --self-test` | exit 0; 135 negative controls and 1 positive control; originals unchanged and valid |
| `python3 -B reference/read_model/generate_fixtures.py --check` | exit 0; six files byte-identical, seed=20261020 |
| `python3 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_read_model_fixtures.py` | exit 0; 7 tests, OK |
| `python3 -B scripts/check_read_model_source_map.py` | exit 0 |
| `python3 -B scripts/check_read_model_source_map.py --self-test` | exit 0 |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | exit 0 |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | exit 0 |
| `python3 -B scripts/check_docs_index.py` | exit 0 |
| `python3 -B scripts/check_docs_index.py --self-test` | exit 0 |
| `python3 -B scripts/check_status_register.py` | exit 0 |
| `python3 -B scripts/check_status_register.py --self-test` | exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py` | exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | exit 0 |

### Authoritative stdlib block (verbatim command list)

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | exit 0 |
| `python3 scripts/check_status_register.py --self-test` | exit 0 |
| `python3 scripts/check_producer_qualification_tuple.py` | exit 0; commands=84 core=40 fsm=44 reads=13 |
| `python3 scripts/check_producer_qualification_tuple.py --self-test` | exit 0; 135 negative controls and 1 positive control; originals unchanged and valid |
| `python3 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | exit 0 |
| `python3 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` | exit 0 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | exit 0 |
| `python3 scripts/check_read_model_source_map.py` | exit 0 |
| `python3 scripts/check_read_model_source_map.py --self-test` | exit 0 |
| `python3 scripts/check_docs_index.py` | exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| `python3 scripts/check_i12_proof_ids.py` | exit 0 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_contract_error_codes.py` | exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | exit 0 |
| `python3 scripts/check_adapter_identity_map.py` | exit 0 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` | exit 0 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_settlement_evidence_map.py` | exit 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_credit_evidence_map.py` | exit 0 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py` | exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py` | exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py` | exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py` | exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py` | exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_evidence_map_rollup.py` | exit 0 |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | exit 0 |
| `python3 scripts/check_class_b_index.py` | exit 0 |
| `python3 scripts/check_class_b_index.py --self-test` | exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| `python3 scripts/check_ci_test_discovery.py` | exit 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0 |
| `python3 scripts/check_loopback_host.py` | exit 0 |
| `python3 scripts/check_loopback_host.py --self-test` | exit 0 |
| `python3 scripts/check_cargo_offline_cache.py` | exit 0 |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | exit 0 |
| `python3 scripts/check_stage5_host.py --self-test` | exit 0 |

### Broader checks

| Command | Actual result |
|---|---|
| `python3 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0; 1006 tests, OK |
| `python3 -B scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 -B scripts/test_runtime_architecture.py` | exit 0; 7 tests, OK |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; all executed suites passed |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0 |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | exit 0; kix-kernel -> kix-types only |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0; all executed suites passed; one existing engine-bundle test ignored |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |

The two baseline tuple commands also passed before editing (plain identity
84/40/44 and 13 reads; original self-test 30 controls). The first post-edit
plain/self-test run passed before the malformed-manifest controls were added;
the final checker was then exercised by both the narrow and full stdlib runs.
No validation command failed. An exploratory `rg` lookup included nonexistent
`.github/workflows/ci.yml` and returned exit 2; the actual workflow is
`.github/workflows/ktx-kernel.yml`, which was inspected along with `protocol.yml`.

The workspace's existing ignored test is
`tests::local_engine_acceptance_requires_explicit_feature`: CPU/SQL engines
require an owner-provisioned offline bundle (`--features engines --test conformance`).
It was not enabled or provisioned for this identity-checking node.

## Preservation evidence

| Command / experiment | Actual result |
|---|---|
| `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Expected task branch; both SHAs `def945f6a3afdb8ba0088a6e627dd7a0c6784cc2` at session start. |
| `python3 -B -` (pre-edit inventory) | Captured SHA-256 of 3,925 tracked regular files before checker edits. |
| `python3 -B -` (post-test inventory comparison) | All 3,922 tracked files outside the three intended existing-file changes byte-identical. Only new file: this report. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both required blob IDs match, as listed above. |
| `git diff --exit-code -- .aiops docs/tasks reference/v0.3-rc1 runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json sdk reference/read_model docs/contracts .github/workflows` | exit 0; no protected or out-of-scope diff. |
| `git diff --check` | exit 0. |

The inventory experiment compares each current file's SHA-256 to the snapshot,
asserts that the changed set is exactly the three existing paths listed above,
and checks the untracked file inventory for exactly this report. It covers the
locked kernel files, the complete tracked `reference/v0.3-rc1/**` tree,
producer artifacts, all candidate fixtures and generator, SDK/verifier,
consumer-binding checker/JSON, contracts, `.aiops/`, task documents,
workflows and historical validation evidence.

## Discrepancies, limitations and delivery gates

No new contract violation or contract-undefined behavior was discovered. The
known SD1 SDK verifier check-order violation remains OPEN, owned by User;
`extension_profile` interpretation remains `UNDETERMINED — User`. No SDK
behavior is changed and no resolution is attempted. Visibility, pagination
limits, cursor lifetime, ordering, open-listing phases, retention and query-digest
policy remain UNDETERMINED. Semantic consumption remains HOLD_SEMANTIC and all
13 reads remain NOT_BOUND. No query is published, implemented or promoted.

Source-informed, builder-authored local identity evidence only. Consistency does
not establish semantic correctness or authenticity when all source artifacts
and pins are deliberately rewritten together. No semantic or N/N-1 acceptance,
production qualification, audit/User approval, production durability,
distributed fencing, bank exactly-once, chain finality, legal compliance,
performance or protocol-completeness claim follows. Consumer app expectations
remain UNVERIFIED. No protected file was regenerated or transiently mutated.

Not run: full hosted protocol workflow, bootstrap/dependency installation,
other reference suites, SDK conformance, Move/localnet/chain execution, ZK
artifact generation, optional analytics engine bundle, production runtime or
external services. The planned closest local checks passed; this does not
substitute for full hosted CI or A2 non-author exact-head review.

Implementation/final task commit SHA: unavailable (uncommitted supervisor handoff).
Exact-head KTX CI run ID/status/conclusion: unavailable / NOT_RUN.
Exact-head KIX protocol CI run ID/status/conclusion: unavailable / NOT_RUN.
A2 non-author exact-head review: not performed by this builder.
Merge commit SHA and post-merge main CI: not applicable (no merge).
These are supervisor delivery gates, not inherited from earlier SHAs. This
report does not propose merge. No commit, push, PR, issue or comment was made.

## Final documentation checks

After completing the evidence report, these six invocations passed again:

| Command | Actual result |
|---|---|
| `python3 -B scripts/check_docs_index.py` | exit 0 |
| `python3 -B scripts/check_docs_index.py --self-test` | exit 0 |
| `python3 -B scripts/check_status_register.py` | exit 0 |
| `python3 -B scripts/check_status_register.py --self-test` | exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py` | exit 0 |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | exit 0 |

All 96 recorded verification invocations exited 0. The final preservation
comparison, locked-blob check and `git diff --check` also passed. HEAD remains
`def945f6a3afdb8ba0088a6e627dd7a0c6784cc2`; implementation is uncommitted.

## Deviations

- The supplied node/design is the task input; no issue or `docs/tasks/` document
  was created or edited. This is explicitly outside ASTRA program mode.
- Session-start fetch omitted because the supervisor prohibits network actions;
  the recorded main is cached and remote freshness is unverified.
- Python 3.13.5 was available instead of CI's 3.12. Rust matches the pinned
  1.98.1 toolchain; offline dependencies were available.
- The seven association mutation types run for every one of the 13 queries,
  and malformed fixture/manifest controls exercise the new validation branches.
  Tests stay in the existing CI-wired self-test; no new runner/dependency.
- No consequential scope change, product decision, protected-file change or
  external resource was required. No DECISION_REQUIRED dependency was found.
