# Explicit readiness migration edge tests

Node: `plan-readiness-migration-edge-tests`. Issue: none. Dependencies:
`readiness-extensions`, `plan-plan-readiness-contract-evidence-map`, and
`plan-readiness-checker-partial-fixture`. Audit floor A2; `astra_gate: None`;
`user_merge: False`. Source: supplied node specification and read-only design
plan, KIX planner run `1792716839`
(`/workspace/kix-run/logs/planner_1792716839`; log contents not independently
verified). This loop-proposed node is not in `.aiops/program.json`.
The supplied specification is the task input; no node-specific task document
was supplied or found under `docs/tasks/`. None was created or revised.
This is not an ASTRA program-mode session.

Observed local `origin/main`, base and initial branch HEAD:
`471728e6488719be471eebb3ca8c30ab2948c444` on
`agent/kix-plan-readiness-migration-edge-tests`. The local refs match.
`git fetch origin main` was omitted under the supervisor's explicit no-network
instruction; remote freshness remains unverified. No commit, push, PR, issue
action, comment, history rewrite or merge was performed. Implementation/final
task head containing these edits: unavailable (uncommitted supervisor handoff).
Exact-head KTX and KIX run IDs/statuses/conclusions: unavailable, not requested
or observed. Merge SHA and post-merge CI: not applicable. Local verification
does not establish merge readiness or satisfy non-author exact-head review/A2.

## Existing coverage mapped before editing

Authority: [READINESS_RUNTIME.md / 버전 이전](../../docs/contracts/READINESS_RUNTIME.md#버전-이전),
within [program decision D-3, §4](../../docs/decisions/PROGRAM_DECISIONS_20260928.md#4-d-3-결정안--readiness-저널-허용-경계-안에서).
Existing test references below are in `readiness/test_faults.py`.

| Requirement | Existing coverage and classification | Missing predicate |
|---|---|---|
| Missing `kind` and `machine` | Partially covered: `ExtensionTests.test_explicit_v2_migration_does_not_run_on_open_or_guess_fields` removes both together. | Each field absent independently, both routes. |
| Required `protocolTruth=false` and `productionConformance=false` | Partially covered: the same ExtensionTests fixture provides both as false. | Each omitted independently; contradictory/non-boolean values; missing schema-2 production labels. |
| Production label contradictions | Partially covered: the same ExtensionTests fixture rejects `productionReadiness=True` on 1-to-2. | `productionEndpoint`, other non-false values, independent 2-to-2 fixtures, already-false schema-1 labels. |
| Malformed records after valid records | Not covered by existing migration fixtures. | Full input preservation after rejection at batch positions 1 and 2, both routes. |
| Unknown nested data and unchanged input | Partially covered: the same ExtensionTests fixture preserves `fixtureNote={'kept': True}`, compares schema-1 input, then feeds its upgrade into 2-to-2. | Deep mixed JSON values, whole-record equality, record count/order and independent schema-2 source equality. |
| Returned copy isolation | Not covered: equality assertions never mutate returned records. | Nested dictionary/list mutations beneath both known `entry` and unknown `fixtureNote`, both routes. |
| Schema-1 open and unsupported downgrade | Sufficiently covered: `StoreTests.test_version_one_roundtrip_and_explicit_migration_only`, `StoreTests.test_unknown_schema_is_refused_without_a_guess`, and the same ExtensionTests migration test. `integration_gate/test_http_gate.py::test_corrupt_journal_and_unknown_schema_do_not_listen` also rejects a schema-2 header. | Retain unchanged; no duplicate open/downgrade tests. The HTTP suite is not run here. |

The [evidence map](../../docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md)'s
`MIG-EXPLICIT = EXERCISED` establishes a fixture citation, not every migration
predicate's coverage. This finer mapping changes no map row or evidence grade.

## Added predicates and contract classification

All additions live in `MigrationEdgeTests`, adjacent to `ExtensionTests`.
Each test docstring names `READINESS_RUNTIME.md / 버전 이전`, the applicable
predicate and its prior coverage gap. Only public `migrate_explicit` is called;
no private migration helpers or file-format support are used. Fresh schema-2
fixtures are constructed directly, independently of the upgrade under test.

| Added test | Contract predicate and evidence |
|---|---|
| `test_missing_identity_fields_are_not_invented` | Omit `kind` or `machine` independently for 1-to-2 and 2-to-2; require `UNSUPPORTED_SCHEMA` and complete unchanged input. |
| `test_required_false_labels_are_not_invented_or_coerced` | Independently omit each original false label and reject `True`, `None`, `0`, and `"false"` on each route; schema-2 must already contain each production label. |
| `test_production_labels_reject_contradictions` | Each production label independently rejects those four values on both routes. Schema-1 accepts neither/either/both labels already false, fills absent constants, and leaves the source unchanged. Accepted labels use identity assertions against `False`. |
| `test_invalid_batch_suffix_preserves_all_inputs` | After one or two valid records, reject a non-record JSON null, wrong schema, missing machine, or contradictory endpoint label. Require exact error code and equality of the entire batch to a pre-call JSON snapshot. |
| `test_nested_unknown_fields_survive_explicit_migration` | Compare entire three-record lists and sources for both routes, preserving order/count, nested dictionaries/lists, unknown keys and mixed null/boolean/integer/string values. Only schema and absent production constants change on 1-to-2; 2-to-2 is value-identical. |
| `test_returned_nested_copies_are_isolated` | Returned list/records have distinct identities; mutate nested dictionaries/lists under `entry` and `fixtureNote` and append to the returned list, then compare the entire source to its pre-call snapshot. |

All added predicates are AGENTS §8 class A: contract-defined and matching in
local execution. No class-C violation or new class-B characterization was found.
The contract is unchanged. Existing recovery characterizations remain OPEN with
owner Astra, and all six held rows retain their existing owners. Receipt/audit
tests, their gaps, and negative-control wiring are untouched.

## Changed paths

- `readiness/test_faults.py`: six focused migration regression tests and test-local helpers.
- `validation/2026-10-23-plan-readiness-migration-edge-tests/README.md`: this distinct record.
- `docs/README.md`: one relative link in the existing 2026-10-23 validation index.

## Actual commands and results

Commands ran from the repository root. `python3 --version`, `cargo --version`
and `rustc --version` exited 0: Python 3.13.5, Cargo/rustc 1.98.1.
The relevant protocol workflow command
combines `integration_gate.test_http_gate` and `readiness.test_faults`. The
readiness component runs offline; the HTTP component opens loopback transport
and was excluded under the explicit no-network boundary. The authoritative
`Stdlib offline document checks` step and installed architecture/Rust checks
are the other closest local CI equivalents. No dependency downloads, backend
probes, provisioning, Sui or artifact generation are needed.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Exit 0; initially clean, both refs equal the base above; expected task branch. |
| Inline Python SHA-256 snapshots of all tracked files and the complete `reference/v0.3-rc1/` path set; Git-blob hashing of both locks | Exit 0; 931 tracked files, 108 reference files; both locks match (hashes below). Snapshots saved outside the repository under `/tmp/plan-readiness-migration-edge-tests-*-before.json`. |
| `python3 -B scripts/check_readiness_evidence_map.py` (before edits) | Exit 0; 36 rows, 177 citations, EXERCISED=25, PARTIAL=2, NOT_EXERCISED=0, OPEN=9. |
| `python3 -B -m unittest readiness.test_faults.MigrationEdgeTests` | Exit 0; 6 tests, OK. |
| `python3 -B -m unittest readiness.test_faults` | Exit 0; 51 tests, OK. |
| `python3 -B scripts/check_readiness_evidence_map.py` (after edits) | Exit 0; same 36 rows, 177 citations and status counts as before. |
| `python3 -B scripts/check_readiness_evidence_map.py --self-test` | Exit 0; supplied-map and zero-PARTIAL suites pass, including the synthetic PARTIAL ownership controls; final `self-test: pass`. |
| `python3 -B scripts/check_docs_index.py` | Exit 0; scanned=209, indexed=174, allowlisted=35. |
| `python3 -B scripts/check_docs_index.py --self-test` | Exit 0; final `self-test: pass`. |
| `python3 -B scripts/check_status_register.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_rs_profile_traceability.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_read_model_source_map.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_i12_proof_ids.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_delegation_layer_matrix.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_rs_predicate_evidence_map.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_rs_im_evidence_map.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_tl_predicate_evidence_map.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_contract_error_codes.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_adapter_identity_map.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_v5_transition_evidence_map.py`; same with `--self-test` | Both exit 0. |
| `python3 -B scripts/check_stage5_host.py --self-test` | Exit 0; synthetic self-tests pass, no host evaluation or provisioning. |
| `python3 -B scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 -B scripts/test_runtime_architecture.py` | Exit 0; 7 tests, OK. |
| `CARGO_TARGET_DIR=/tmp/kix-plan-readiness-migration-edge-tests-target cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101 before compilation/tests: uncached `bcs v0.2.1` requires download; `--offline` refused HTTP. No workspace-test pass is claimed. |
| `CARGO_TARGET_DIR=/tmp/kix-plan-readiness-migration-edge-tests-target cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 78 tests passed across 7 nonempty integration binaries, 0 failures; unit/doc-test binaries also pass with 0 tests. |
| `CARGO_TARGET_DIR=/tmp/kix-plan-readiness-migration-edge-tests-target cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101: same uncached `bcs v0.2.1` dependency; offline download refused. No workspace-Clippy pass is claimed. |
| `CARGO_TARGET_DIR=/tmp/kix-plan-readiness-migration-edge-tests-target cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `git diff --check`; `git diff --stat`; `git status --short`; `git diff -- readiness/test_faults.py docs/README.md` | Exit 0; no whitespace errors; two tracked paths changed and only this validation record is untracked. |
| Inline Python before/after SHA-256 manifest, locked-blob, unchanged-existing-tests and delivery-path assertions | Exit 0; 929 tracked files outside the two allowed paths unchanged, all 108 reference file paths/hashes identical, both locked blobs match. Removing only the added class restores the entire original test file byte-for-byte. |

An inline Python driver extracted all 27 commands in the unchanged workflow's
`Stdlib offline document checks` run block, added `-B`, and ran them sequentially
with `subprocess.run`, stopping on nonzero exit. All 27 exited 0. Individual
stdout/stderr logs are in `/tmp/plan-readiness-migration-edge-tests-stdlib-00.log`
through `-26.log`, with command/exit-code metadata in
`/tmp/plan-readiness-migration-edge-tests-stdlib-results.json`. Rust output was
captured in `/tmp/plan-readiness-migration-edge-tests-cargo-test.log`,
`-kernel-test.log`, `-workspace-clippy.log`, and `-kernel-clippy.log` (same prefix).
These logs and the Cargo target directory are temporary local execution aids,
not delivery paths. All commands ran in the foreground; nothing was backgrounded.

## Preservation, deviations and limits

Before editing, both Git blobs matched AGENTS §4:
`runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`.
The sorted JSON path/SHA-256 manifest for all 108 reference files has SHA-256
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
After the checks, both locked blobs still match and the reference path set and
all byte hashes match the pre-edit snapshot. All 929 tracked files outside the
test file and docs index are byte-identical to the initial snapshot, including
the migration implementation, contracts, map/checkers, workflows, `.aiops/`,
task documents and runtime. Existing test names and bodies are byte-identical.

Design deviations: no implementation-scope deviation. Fetch omission, offline
Cargo flags and exclusion of loopback HTTP follow the supervisor's no-network
instruction. Full workspace tests/Clippy could not execute without the missing
cached dependency; no download, bootstrap or dependency/configuration edit was
made. The dependency-free kernel checks, workspace formatting, architecture
checks and all task-required Python checks passed. Full hosted jobs, unrelated
runtime/gate, Node/SDK, Move/ZK, backend and artifact-generation jobs were not
run. Publication and exact-head CI belong to the supervisor; no old CI
success transfers to these edits. A2/non-author review remains outstanding.

These are source-informed, offline synthetic regressions of the existing D-3
local wrapper. No production runtime, real funds, PG/bank/KYC, public endpoint,
Sui testnet/mainnet, coin/TIX module, secrets, backend activation, storage engine,
policy value or new protocol command is introduced or exercised. No claim of
production durability, power-loss/OS-crash tolerance, fsync correctness,
distributed fencing, chain finality, external exactly-once, clean-room
independence, legal compliance or production readiness is made. Operational
count and evidence grades do not change. Existing OPEN/UNDETERMINED inputs and
their owners remain unchanged; receipt/audit and negative-control work require
their own task boundaries.
