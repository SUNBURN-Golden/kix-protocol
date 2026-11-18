# Readiness JSON rejection and canonical receipt digests

## Basis and identifiers

Node: `plan-plan-readiness-json-codec-regressions`. Task input is the
supervisor's user-supplied node specification and design plan in this session;
no issue or corresponding `docs/tasks/` document exists. Source: planner run
1793228362; this loop-proposed node is not in `.aiops/program.json` and this
is not ASTRA program mode. Dependencies named by the input:
`readiness-extensions`, `plan-plan-readiness-journal-byte-sweep`, and
`plan-readiness-record-byte-boundaries`. Existing dependency evidence is
preserved, not regraded. Scope follows PROGRAM_DECISIONS_20260928 §4 (D-3)
and `docs/contracts/READINESS_RUNTIME.md`.

Execution date: 2026-10-29. Initially clean branch
`agent/kix-plan-plan-readiness-json-codec-regressions`. Cached `origin/main`,
task base and starting HEAD: `eb14bc4ed7077d5a5ae06306ff5e3d68d5a29ae8`.
No local base delta. Remote freshness is unverified: the supervisor's explicit
no-network instruction supersedes AGENTS §1 fetch. No base change was made.
Implementation/final committed task head: unavailable; no commit is created
in this builder session. The starting SHA does not contain these edits.
Merge SHA, final-merge blob checks and post-merge CI: not applicable, no merge.

## Coverage before changes

All existing cases below remain unchanged. The map was made before adding tests.

| Requirement | Existing evidence in `readiness/test_faults.py` | Prior classification |
|---|---|---|
| Small schema-1 round trip/stamps | `StoreTests.test_version_one_roundtrip_and_explicit_migration_only` | Sufficient for small-record predicate; partially covers new valid controls. |
| Checksum mismatch and torn-tail recovery | `StoreTests.test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed`; `JournalByteSweepTests.test_truncation_at_every_offset_keeps_the_longest_whole_frame_prefix`; `test_every_payload_and_crc_byte_flip_fails_closed` | Sufficient; reused. |
| Invalid UTF-8 and top-level duplicate keys with correct CRC | `JournalByteSweepTests.test_crc_consistent_damage_is_rejected_not_repaired` | Sufficient; reused. |
| ASCII/multibyte UTF-8 ceilings | `RecordSizeBoundaryTests.test_ascii_and_utf8_record_size_boundaries_roundtrip` | Sufficient; reused, no new size matrix. |
| Oversized append atomicity and same-handle reuse | `RecordSizeBoundaryTests.test_oversized_record_rejection_is_atomic_and_store_reusable` | Sufficient for size errors; codec serialization errors not covered. |
| BOM, nested duplicate keys, bare NaN/Infinity/-Infinity, malformed JSON | No dedicated cases in the mapped classes | Not covered. |
| Valid Unicode, finite numbers, distinct nested keys, quoted constants | Existing store and size round trips | Partially covered. |
| Serialization failures in codec/digest/append | Other rejection paths only | Not covered. |
| Literal canonical Unicode bytes and independently calculated digest | Size tests use a stdlib serialization oracle; gate receipt checks call `receipt_digest` | Partially covered. |
| Digest order invariance and content sensitivity | No explicit nested insertion-order fixture | Not covered. |

## New case matrix

All four methods are in
`readiness/test_faults.py::JsonCodecRegressionTests`; the class does not
inherit existing tests. Test-local framing follows the existing byte sweep,
without changing its cases. Only public codec/store APIs are exercised.

| New method | Gap and checked result |
|---|---|
| `test_complete_frames_reject_invalid_json_without_rewriting` | Ten direct-byte payloads: UTF-8 BOM; duplicate keys in nested object and object within array; bare NaN, Infinity, -Infinity; missing value; trailing comma; unterminated string; trailing text. Direct helper raises `CodecError('JOURNAL_CORRUPT')`. Each payload is also tested in a complete length/payload/CRC frame both at EOF and before an accepted suffix (20 file cases), after an accepted prefix. `open` raises `StoreError('JOURNAL_CORRUPT')`; the entire file stays byte-identical. |
| `test_valid_json_controls_roundtrip` | Four controls: literal Unicode; finite integers/decimals/exponent; distinct nested keys including repeated key names in different array objects; quoted constant names. Parse literal payload, open its frame, append through the public API and reopen; check exact records, committed bytes and file bytes. |
| `test_serialization_failures_report_journal_record` | Five nested values: NaN, positive/negative infinity, set and circular list. `canonical_json` and `receipt_digest` raise `CodecError('JOURNAL_RECORD')`; `append` propagates the same type/code. Compare bytes, deep-copied records and accounting after failure, then valid append on the same handle and reopen. |
| `test_canonical_unicode_bytes_and_receipt_digests` | Literal UTF-8 with accent/Korean/emoji and nested dictionaries. Compare canonical bytes directly, parse back and compare SHA-256 calculated from literal bytes. Reverse both dictionary insertion orders and retain digest; change 7 to 8 and check separately expected bytes/digest and inequality. |

Frames assert `2 <= len(payload) <= MAX_RECORD_BYTES` and exact full frame
length, with correctly recomputed CRC32, so malformed JSON does not exercise
the torn-tail branch. Header/prefix/suffix come from a journal created and
closed through public store APIs. Each malformed file uses a fresh temporary
directory. An unexpectedly accepted open is closed before the assertion fails.
All other acquired handles close before temporary-directory cleanup. Entries
are synthetic dictionaries in six-field schema-1 FSM envelopes (`schema`,
`protocolTruth`, `productionConformance`, `kind`, `machine`, `entry`), with
both labels false and `machine='settlement'`; none goes through FSM replay.

The digest oracle hashes this literal expected byte string, not codec output:

```python
b'{"a":{"accent":"\xc3\xa9","text":"\xea\xb0\x80\xf0\x9f\x99\x82"},"z":[true,null,7]}'
```

The changed-content oracle supplies the full literal with `8` instead of `7`
and independently calculates its SHA-256. No normalization semantics are added.

## Actual commands and results

Local evidence only. Python checks set `PYTHONDONTWRITEBYTECODE=1`; no
background shell jobs or provisioning. Narrow tests preceded broader checks.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; cached main/HEAD and branch as recorded above. |
| Python sorted path/SHA-256 inventory and `git hash-object` for both locked paths | Before work: both required blobs match; 108 protected reference files inventoried. |
| `python3 -m unittest readiness.test_faults.JsonCodecRegressionTests` | PASS: 4 tests. |
| `python3 -m unittest readiness.test_faults.StoreTests readiness.test_faults.JournalByteSweepTests readiness.test_faults.RecordSizeBoundaryTests` | PASS: 12 tests. |
| `python3 -m unittest readiness.test_faults` | PASS: 73 tests. |

The workflow's **Stdlib offline document checks** block was read; its 63
`python3` commands were extracted and executed sequentially with one explicit
real-socket exclusion. All 62 permitted commands passed on the first run.
Every actual command/result follows; no excluded command is counted as passing.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | PASS (exit 0): capability register ok: paths=454 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | PASS (exit 0): rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | PASS (exit 0): read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=314 indexed=279 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | PASS (exit 0): i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS (exit 0): delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0): rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | PASS (exit 0): rs im evidence map ok: rows=30 expected=30 citations=202 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0): tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | PASS (exit 0): adapter identity evidence map ok: rows=17 expected=17 citations=71 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | PASS (exit 0): v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | PASS (exit 0): readiness runtime evidence map ok: rows=36 expected=36 citations=186 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | PASS (exit 0): settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | PASS (exit 0): bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | PASS (exit 0): credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | PASS (exit 0): primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | PASS (exit 0): ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | PASS (exit 0): lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS (exit 0): self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | PASS (exit 0): contract invariants map: 27 rows, corpus, anchors, test symbols, counts, locked blobs and F-B1 document pins OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | PASS (exit 0): contract invariants self-test: 2 positive controls and 97 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | PASS (exit 0): Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS (exit 0): Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | PASS (exit 0): BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | PASS (exit 0): performance evidence map ok: Counts: rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (2 positive controls, 81 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | PASS (exit 0): feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (81 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | PASS (exit 0): integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (100 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_evidence_map_rollup.py` | PASS (exit 0): evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | PASS (exit 0): self-test: pass (16 negative controls) |
| `python3 scripts/check_class_b_index.py` | PASS (exit 0): class B index ok: rows=218 sources=73 symbols=47; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | PASS (exit 0): self-test: pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 scripts/check_loopback_host.py` | NOT_RUN: real sockets excluded by node |
| `python3 scripts/check_loopback_host.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_cargo_offline_cache.py` | PASS (exit 0): archive cache: total=18 present=18 missing=0; host observation only |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | PASS (exit 0): self-test: pass |

Broader KTX/protocol local equivalents, using installed tooling and offline
dependencies:

| Command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0): architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0): 7 tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS (exit 0): 339 passed, 0 failed, 0 ignored across 46 test/doc-test groups, including kix-kernel. Counts summed from actual test summaries. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS (exit 0). |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0). |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | PASS (exit 0): kix-kernel → kix-types only. |
| Python before/after reference path/byte-hash comparison and both `git hash-object` checks | PASS: all 108 paths and byte hashes identical; both required blobs match before/after. |
| Python output allowlist check using `git diff HEAD --name-only` and `git ls-files --others --exclude-standard` | PASS: exactly the four authorized paths listed below. |
| `git diff --check` | PASS (exit 0): no whitespace errors. |
| `git rev-parse HEAD origin/main` after work | Both remain `eb14bc4ed7077d5a5ae06306ff5e3d68d5a29ae8`; no commit containing the edits. |

After filling the results table, both `check_docs_index.py` and
`check_ci_test_discovery.py` were repeated normally and with `--self-test`:
all four invocations passed (exit 0). `git diff --check` passed again.
A final Python AST comparison against `git show HEAD:readiness/test_faults.py`
confirmed `StoreTests`, `JournalByteSweepTests` and `RecordSizeBoundaryTests`
unchanged; the four-path allowlist and both locked Git blobs also passed again.

## Protected files and output paths

Both before/after-work checks matched the required Git blobs:

| Path | Required/before/after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

A sorted path/SHA-256 byte inventory captured all 108 regular files under
`reference/v0.3-rc1/**` before work. After work every path and byte hash
matched, with the same sorted-key JSON inventory SHA-256:
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
The four-path output allowlist passed, preserving all other tracked content.
Authorized complete changed-path list:

- `readiness/test_faults.py`
- `readiness/CONFORMANCE.md`
- `validation/2026-10-29-plan-plan-readiness-json-codec-regressions/README.md`
- `docs/README.md`

## Classification, limits and remaining gates

AGENTS §8 B: JSON rejection details, serializer exception propagation,
canonical Unicode bytes and receipt-digest invariance are source-informed
characterizations of contract-undefined local codec details. They are not
new protocol requirements, backend conformance or Unicode normalization policy.
No explicit contract violation was found. No codec/store behavior, contract,
policy value, observation guard, evidence grade or open decision is changed.
The readiness map retains all nine OPEN rows and existing owners, including
`OPEN-LENPREFIX-MIDFRAME`, `OPEN-ZERO-BYTE-REINIT` and
`OPEN-FRAME-BOUNDARY-CUT`. Existing recovery uncertainties remain unresolved.

No production durability, stage-5 acceptance, clean-room independence,
power-loss, OS-crash, physical-media/fsync proof, distributed fencing, external
exactly-once, chain finality or backend-adoption claim. All truth, production
and FSM durable labels remain false. No services, sockets, credentials, real
funds, provider/bank/KYC calls, Sui networks, secrets, hardware, spending,
production runtime, new protocol command, storage engine, replication or
consensus is used or implemented. Contracts, `.aiops/`, task inputs, CI,
locked kernel files and protected references remain untouched.

Deviations: AGENTS §1 fetch is omitted under the explicit no-network rule;
there is no issue/task document to read or create. The workflow's combined
`python3 -m unittest integration_gate.test_http_gate readiness.test_faults`
is NOT_RUN because it opens sockets; readiness-only is the permitted local
equivalent. The real-socket `check_loopback_host.py` invocation is likewise
excluded; its fake-socket self-test is permitted. Full hosted protocol jobs,
SDK/Move/ZK/service/bootstrap checks and production/storage probes are outside
this test/doc node's local equivalents. Offline Rust commands use installed
tooling/cache only; no provisioning is authorized.

Non-author A2 exact-head review is outstanding. Exact-head KTX kernel
verification and KIX protocol verification run IDs/status/conclusions:
unavailable/NOT_RUN, since no final task commit or GitHub action is permitted
here. Post-merge CI is not applicable. No commit, push, PR, issue, comment or
merge is performed. READY denotes local builder handoff only, not merge-ready
or an independent PASS. Supervisor publication, final-head review/CI and any
user-authorized merge/post-merge verification remain follow-up work. Policy
and recovery decisions retain their existing owners.
