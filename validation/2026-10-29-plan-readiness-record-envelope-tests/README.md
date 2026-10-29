# Readiness record-envelope rejection and preservation

## Basis and identifiers

Node: `plan-readiness-record-envelope-tests`, supplied in the supervisor prompt;
no issue or corresponding `docs/tasks/` document exists. This is not ASTRA
program mode. Source: planner run 1793237680; dependencies are
`readiness-extensions`, `plan-plan-readiness-json-codec-regressions`, and
`plan-readiness-wrap-restore-rejections`.

Execution date: 2026-10-29. Branch:
`agent/kix-plan-readiness-record-envelope-tests`. Cached `origin/main`, task
base and initial HEAD: `e29bafc6d658cc6875dab571c2f4a72e2df49709`;
initial worktree clean. Remote freshness is unverified: the supervisor's
explicit no-network rule overrides the AGENTS §1 fetch. No base delta is
visible locally. Implementation/final committed head: unavailable, because
the supervisor owns commits and publication. No merge performed.

Read in governance order: root README, DEVELOPMENT_PLAN, BASELINES,
AUTHORITY_MODEL_1, then supplied node/design; PROGRAM_DECISIONS_20260928,
READINESS_RUNTIME, local conformance/evidence, store/codec and test sources,
and both workflow definitions. The central policy pointer is a pending
candidate, not runtime activation; no remote policy was fetched.

## Existing coverage (mapped before adding tests)

All test symbols below are in `readiness/test_faults.py`.

| Requirement | Existing evidence | Prior classification / gap |
|---|---|---|
| Accepted FSM/core store envelopes | `StoreTests.test_version_one_roundtrip_and_explicit_migration_only`, `JournalByteSweepTests.setUp` | Partially covered: no focused all-seven-machine plus core control. |
| Missing/extra fields, kind/machine mismatch, entry/body type, empty/non-string identifiers, digest length/alphabet | Selected schema/truth mutations in `JournalByteSweepTests.test_crc_consistent_damage_is_rejected_not_repaired`; explicit truth rejection in `StoreTests.test_protocol_truth_label_cannot_be_written` | Not systematically covered: add envelope matrix, preserving existing tests. |
| Rejection preserves bytes, records, accounting and same-handle reuse | `RecordSizeBoundaryTests.test_oversized_record_rejection_is_atomic_and_store_reusable`, `JsonCodecRegressionTests.test_serialization_failures_report_journal_record` | Partially covered: size/serialization paths only, not envelope validation. |
| Complete checksum-valid envelope rejection without byte rewrite | `JournalByteSweepTests.test_crc_consistent_damage_is_rejected_not_repaired` | Partially covered: selected mutations; no full envelope matrix with explicit whole-file preservation. |
| JSON syntax and serialization | `JsonCodecRegressionTests` | Sufficient for separation; unchanged, no duplicate codec matrix. |
| Wrapper restore entry semantics | `WrapperRestoreRejectionTests` | Sufficient for separation; unchanged, no FSM replay in envelope tests. |

## Case matrix

All three new methods are in `readiness/test_faults.py::RecordEnvelopeTests`.
They use public store APIs; framing uses stdlib JSON, big-endian lengths and
CRC32, without production `_stamp`, `_validate`, `_parse`, or codec helpers as
oracles. The seven FSM machine names and expected schema-1 stamps are explicit
test fixtures. Existing classes/helpers remain unchanged.

| Method | Gap addressed / assertions |
|---|---|
| `test_valid_fsm_and_core_envelopes_roundtrip` | All seven FSM machines and core `integration_core`/synthetic `advance_clock` control; exact expected stamped records, identity-false labels, incremental frame accounting, reopen and persisted byte preservation. Entries are envelope controls, not executed commands. |
| `test_invalid_append_preserves_journal_and_allows_next_append` | 70 named cases: each caller field missing; extra field; every inappropriate cross-kind field; unknown kind/machine; mismatched kind/machine; null/list/string/integer/boolean entry or body; each core textual field empty or null/list/integer/boolean/object; digest lengths 63/65 and length-64 uppercase/nonhex/space/non-ASCII alphabet; each reserved stamp explicitly supplied with its otherwise correct value. Exact `StoreError` type and `JOURNAL_RECORD`; bytes, deep-copied records and committed-byte snapshot unchanged; valid core append on the same handle has exact expected frame increment and records; close/reopen preserves accounting and bytes. |
| `test_invalid_complete_frames_fail_without_rewriting` | 70 persisted-envelope cases, each at EOF and before an accepted suffix (140 file fixtures). Persisted variants independently omit every field including each stamp; supplied correct stamps are normal here. Exact `StoreError` type and `JOURNAL_CORRUPT`, with whole-file byte preservation. |

Every frame fixture first verifies JSON round-trip, in-range payload size,
complete length and CRC32. Header, accepted prefix and suffix are obtained
through public append. Every rejection uses a fresh directory; an unexpectedly
accepted open is closed before failing. Every acquired handle closes before
temporary-directory cleanup. Core digests are synthetic shape controls; no
receipt authenticity or replay semantics are tested.

## Actual commands and results

All commands ran from the repository root. No shell background job, network,
provisioning or publication command was used. Narrow tests preceded broader
checks. Python commands used `-B`.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; branch and cached main/HEAD as recorded above. |
| `git hash-object` for each locked file; Python sorted reference path/SHA-256 inventory | Before: both required blobs match; 108 reference files inventoried. |
| `python3 -B -m unittest readiness.test_faults.RecordEnvelopeTests` | PASS: 3 test methods (70 append rejections, 140 invalid file fixtures, eight valid envelopes). |
| `python3 -B -m unittest readiness.test_faults` | PASS: 91 tests, 0 failures. |
| Python case-name enumeration | PASS: 70 unique append cases and 70 unique persisted cases. |
| Python AST comparison with `git show HEAD:readiness/test_faults.py` | PASS: every existing class/function unchanged; only `RecordEnvelopeTests` added. |

Read `.github/workflows/protocol.yml` and `ktx-kernel.yml`. Extracted the
protocol workflow's 63-command **Stdlib offline document checks** block and
ran each permitted command sequentially through `subprocess.run`; all 62
permitted commands passed on their first run. The real-socket host check was
explicitly excluded, not counted as a pass. Each actual invocation follows.

| Command | Actual result |
|---|---|

| `python3 -B scripts/check_status_register.py` | PASS (exit 0): capability register ok: paths=454 ev_ids=15 original32=32 |
| `python3 -B scripts/check_status_register.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_rs_profile_traceability.py` | PASS (exit 0): rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 -B scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_read_model_source_map.py` | PASS (exit 0): read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 -B scripts/check_read_model_source_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=317 indexed=282 allowlisted=35 |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_i12_proof_ids.py` | PASS (exit 0): i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 -B scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_delegation_layer_matrix.py` | PASS (exit 0): delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 -B scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0): rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 -B scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_rs_im_evidence_map.py` | PASS (exit 0): rs im evidence map ok: rows=30 expected=30 citations=202 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 -B scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0): tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 -B scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 -B scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_adapter_identity_map.py` | PASS (exit 0): adapter identity evidence map ok: rows=17 expected=17 citations=71 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 -B scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_v5_transition_evidence_map.py` | PASS (exit 0): v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 -B scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_readiness_evidence_map.py` | PASS (exit 0): readiness runtime evidence map ok: rows=36 expected=36 citations=186 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 -B scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_settlement_evidence_map.py` | PASS (exit 0): settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 -B scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (33 negative controls) |
| `python3 -B scripts/check_bra_evidence_map.py` | PASS (exit 0): bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 -B scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (50 negative controls) |
| `python3 -B scripts/check_credit_evidence_map.py` | PASS (exit 0): credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 -B scripts/check_credit_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (55 negative controls) |
| `python3 -B scripts/check_primary_price_fee_evidence_map.py` | PASS (exit 0): primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 -B scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (76 negative controls) |
| `python3 -B scripts/check_ai_delegation_evidence_map.py` | PASS (exit 0): ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 -B scripts/check_ai_delegation_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (86 negative controls) |
| `python3 -B scripts/check_lifecycle_adr_evidence_map.py` | PASS (exit 0): lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 -B scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS (exit 0): self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 -B scripts/check_contract_invariants_evidence_map.py` | PASS (exit 0): contract invariants map: 27 rows, corpus, anchors, test symbols, counts, locked blobs and F-B1 document pins OK |
| `python3 -B scripts/check_contract_invariants_evidence_map.py --self-test` | PASS (exit 0): contract invariants self-test: 2 positive controls and 97 negative fixtures OK (memory only) |
| `python3 -B scripts/check_toss_card_profile_evidence_map.py` | PASS (exit 0): Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 -B scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS (exit 0): Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 -B scripts/check_bcs1_evidence_map.py` | PASS (exit 0): BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 -B scripts/check_bcs1_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 -B scripts/check_performance_measurement_evidence_map.py` | PASS (exit 0): performance evidence map ok: Counts: rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3 |
| `python3 -B scripts/check_performance_measurement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (2 positive controls, 81 negative fixtures; memory only) |
| `python3 -B scripts/check_feature_semantics_evidence_map.py` | PASS (exit 0): feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 -B scripts/check_feature_semantics_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (81 negative controls, injected positive control) |
| `python3 -B scripts/check_integration_gate_contract_evidence_map.py` | PASS (exit 0): integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 -B scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (100 negative controls; injected positive and valid status controls) |
| `python3 -B scripts/check_evidence_map_rollup.py` | PASS (exit 0): evidence map roll-up ok: contracts=25; textual index only |
| `python3 -B scripts/check_evidence_map_rollup.py --self-test` | PASS (exit 0): self-test: pass (16 negative controls) |
| `python3 -B scripts/check_class_b_index.py` | PASS (exit 0): class B index ok: rows=218 sources=73 symbols=47; textual index only |
| `python3 -B scripts/check_class_b_index.py --self-test` | PASS (exit 0): self-test: pass (20 negative controls) |
| `python3 -B scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |
| `python3 -B scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 -B scripts/check_loopback_host.py` | NOT_RUN: real sockets excluded by offline node scope |
| `python3 -B scripts/check_loopback_host.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_cargo_offline_cache.py` | PASS (exit 0): archive cache: 18/18 present, 0 missing; host observation only |
| `python3 -B scripts/check_cargo_offline_cache.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_stage5_host.py --self-test` | PASS (exit 0): self-test: pass |


Broader KTX/protocol local equivalents used the installed Rust 1.98.1
(`rustup toolchain list`) and cached dependencies, with no provisioning.
Workspace tests include `kix-kernel`; no redundant kernel-only run was needed.

| Command | Actual result |
|---|---|
| `python3 -B scripts/verify_runtime_architecture.py` | PASS (exit 0): architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 -B scripts/test_runtime_architecture.py` | PASS (exit 0): 7 tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS (exit 0): 339 passed, 0 failed, 0 ignored across 46 test/doc-test groups (summed from actual summaries). |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS (exit 0) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | PASS (exit 0): kix-kernel depends on kix-types only. |
| Python initial post-work protected-path verifier | Verifier setup failure: saved `/tmp` inventory unavailable (`FileNotFoundError`); locked blobs had matched before this failure. |
| Python replacement reference verifier using line-delimited `git ls-tree` output | Verifier setup failure: Git quoted a non-ASCII filename, causing a path-set assertion failure. The actual before/after inventory digest already matched. |
| Python corrected reference verifier using `git ls-tree -rz --name-only HEAD -- reference/v0.3-rc1` and `git show HEAD:<path>` | PASS: all 108 path/content hashes match both the recorded pre-work inventory digest and HEAD bytes. |
| Python four-path allowlist from `git diff HEAD --name-only` plus `git ls-files --others --exclude-standard` | PASS: exactly the four authorized output paths. |
| Python whole-module AST comparison against `git show HEAD:readiness/test_faults.py` | PASS: the original module is unchanged apart from the new class, including existing imports and all prior tests/helpers. |
| `git diff --check` | PASS: no whitespace errors. |
| `git rev-parse HEAD origin/main` after work | Both remain `e29bafc6d658cc6875dab571c2f4a72e2df49709`; edits are uncommitted. |

The two ad hoc protected-path verifier errors above were corrected without
changing any protected file or product test. No product test/checker failure
was observed. Final document/discovery checks and protected-path verification
are repeated after completing this record; their results follow below.

## Protected paths and complete changed-path list

Both before and after work, the two locked files have the required Git blobs:

| Path | Required / before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

All 108 regular files under `reference/v0.3-rc1/**` have identical sorted
paths and SHA-256 content hashes before/after. Sorted-key JSON inventory
SHA-256: `dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
The after inventory also matches every protected file's HEAD bytes using
NUL-delimited Git paths. The four-path allowlist preserves runtime sources,
contracts, evidence maps/grades, open decisions, `.aiops/`, task documents,
workflows and all other tracked content. Complete changed-path list:

- `readiness/test_faults.py`
- `readiness/CONFORMANCE.md`
- `docs/README.md`
- `validation/2026-10-29-plan-readiness-record-envelope-tests/README.md`

## Contract classification and non-claims

Source-defined envelope field sets, stamp ownership, kind/machine matching,
container types, identifier/digest shape, exact rejection codes and
rejected-append preservation are AGENTS §8 class B characterizations, not
new contract semantics. No explicit contract violation was found. The
existing JSON syntax tests and wrapper restore tests retain their separate
roles. Valid envelopes do not establish valid FSM commands or authentic
receipts. No runtime implementation, product policy value, protocol command,
backend format requirement, grade or open decision is introduced.

The nine readiness-map OPEN rows and owners remain unchanged, especially
`OPEN-LENPREFIX-MIDFRAME`, `OPEN-ZERO-BYTE-REINIT` and
`OPEN-FRAME-BOUNDARY-CUT`. Recovery policy uncertainties remain unresolved.
These tests demonstrate the listed in-process local behavior only. No
production readiness/durability, power-loss, OS-crash, physical-media/fsync
proof, stage-5 acceptance, clean-room independence, distributed fencing,
external exactly-once, chain finality or backend adoption is claimed. No
hardware, paid service, secret, real funds, provider/PG/bank/KYC call, public
endpoint, Sui network, production runtime, storage engine, replication or
consensus is needed or used. False truth/production/durable labels stay false.

## Deviations, review/CI gates and remaining uncertainty

The supervisor's no-network rule overrides the session-start fetch; cached
main freshness is unverified. There is no task issue/document to read or
create; the supplied node/design is the task input. The design's final
read-only-session paragraph applies to its earlier planning session; this
builder is explicitly authorized to edit the four listed paths. No other
design deviation was needed.

The workflow's combined HTTP/readiness unittest command and plain real-socket
`check_loopback_host.py` are NOT_RUN; the readiness-only suite and fake-socket
host self-test are the scoped offline equivalents. Hosted SDK/Move/ZK, chain,
HTTP, service/bootstrap and storage probes are not covered by this local
verification. No broader runtime or network qualification follows from it.

Exact final task head: not established (no commit authorized). Exact-head
KTX kernel verification and KIX protocol verification: run ID unavailable,
status NOT_RUN, conclusion unavailable. Non-author exact-head A2 review:
outstanding. Merge commit, merged locked blobs and post-merge main CI: not
applicable. Local READY is a builder handoff state only; required exact-head
CI, non-author review, any publication and user-authorized merge/post-merge
verification remain supervisor delivery gates. No Git/GitHub mutation or
comment was performed. Existing recovery decisions retain their owners.


## Final verification repeat

After completing the substantive record, these checks passed again:

| Command | Actual result |
|---|---|
| `python3 -B scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=317 indexed=282 allowlisted=35 |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 -B scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 -B scripts/check_readiness_evidence_map.py` | PASS (exit 0): readiness runtime evidence map ok: rows=36 expected=36 citations=186 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 -B scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| Python final `git hash-object` assertions and sorted reference path/SHA-256 digest comparison | PASS: both required locked blobs match; all 108 protected reference paths/bytes retain the pre-work digest. |

The final whitespace and four-path allowlist checks also passed. No new test
code changed after the successful narrow/full suite and Rust runs.
