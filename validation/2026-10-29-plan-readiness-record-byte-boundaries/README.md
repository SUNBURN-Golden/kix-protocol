# Readiness record-size byte boundaries and rejection atomicity

## Basis

Node: `plan-readiness-record-byte-boundaries`. Task input: the supervisor's
user-supplied node specification and design plan in this session; no issue or
corresponding document under `docs/tasks/` exists. Not ASTRA program mode.
Scope is offline regression evidence under PROGRAM_DECISIONS_20260928 §4,
with `docs/contracts/READINESS_RUNTIME.md` and `readiness/CONFORMANCE.md` as
boundary references. The existing implementation-only `MAX_RECORD_BYTES` in
`readiness/store.py` remains 1048576; no product policy value is selected.

Execution date: 2026-10-29. Initially clean branch
`agent/kix-plan-readiness-record-byte-boundaries`; cached `origin/main`, task
base and starting HEAD all equal `9e0ea233b418d6ad536c581320a53b5e64a057fa`.
No local base delta. Remote freshness is unverified: the supervisor forbids
network actions, so AGENTS §1's fetch was omitted. No base change was made.
Implementation/final committed task head: not created; the supervisor owns
commits/publication. The starting SHA does not contain these uncommitted edits.
No merge commit, final-merge blob verification or post-merge CI exists.

## Existing coverage

Mapped before adding tests; existing tests are retained without duplication.

| Requirement | Existing evidence | Prior coverage |
|---|---|---|
| Small-record stamping, append and reopen | `readiness/test_faults.py::StoreTests.test_version_one_roundtrip_and_explicit_migration_only` | Sufficient for its small-record predicate; partially covers boundary round trips. |
| Tears, payload/CRC corruption and damaged length prefixes | `readiness/test_faults.py::JournalByteSweepTests`, especially `test_truncation_at_every_offset_keeps_the_longest_whole_frame_prefix` and `test_characterization_b_damaged_length_prefix_drops_later_acknowledged_frames` | Sufficient for existing corruption predicates; not coverage of valid near-limit appends. |
| Aggregate record/byte budgets and replay identity | `readiness/conformance.py::BackendConformance.test_budget_rejection_preserves_records_and_replay_identity` | Sufficient for admission-budget predicates; partially covers state preservation, not oversized append rejection. |
| Budget reason and overload queue behavior | `readiness/test_faults.py::ExtensionTests.test_budget_names_the_existing_limit_and_overload_does_not_queue` | Sufficient for its aggregate-budget/overload predicates, not the per-record ceiling. |
| Independent stamped byte sizing at limit-minus-one, exact limit and limit-plus-one | No valid boundary-sized append fixture in those tests. | Not covered. |
| Multibyte UTF-8 byte rather than character accounting | Existing small fixtures do not distinguish admission at the byte ceiling. | Not covered. |
| Oversized append preserves journal bytes, deep-copied records and accounting; valid append on the same handle then reopen | Existing fault/budget coverage uses other rejection paths. | Partially covered overall; this rejection/reuse path not covered. |

## New assertions

`readiness/test_faults.py::RecordSizeBoundaryTests` uses only public store methods
and temporary local files. The synthetic `entry.text` is not an FSM command;
these records never go through FSM replay. Large fixtures stay outside the
byte-by-byte mutation sweep.

- `test_ascii_and_utf8_record_size_boundaries_roundtrip`: tokens `a` and `가🙂`
  at 1048575 and 1048576 payload bytes; explicit expected stamp, returned record,
  full records list, length prefix, complete payload bytes, CRC and committed-byte
  accounting. Close/reopen preserves exact records, bytes and accounting.
- `test_oversized_record_rejection_is_atomic_and_store_reusable`: for both tokens,
  accept a small prefix, reject exactly 1048577 payload bytes with
  `RECORD_TOO_LARGE`, compare journal bytes, deep-copied records and
  `committed_bytes` immediately. Append an exact-limit record on the same handle,
  check the complete prefix plus independently framed valid payload, then close
  and reopen with precisely the two accepted records and unchanged bytes.

The test-local oracle explicitly constructs schema/non-production stamps and
uses stdlib `json.dumps(ensure_ascii=False, sort_keys=True, separators=(',', ':'),
allow_nan=False).encode('utf-8')`. It does not call `_stamp`, `_parse` or
`canonical_json`. Empty-envelope overhead is measured independently; `divmod`
fills the remaining budget with whole tokens and an ASCII remainder. Every
boundary payload length is asserted before invoking the store. The multibyte
token has two characters and seven UTF-8 bytes; its serialized character count
is less than its byte count, and even the oversized case has fewer characters
than the byte ceiling. Header and eight framing bytes do not consume that
ceiling. Each acquired handle closes in a `finally` block before cleanup.

## Actual commands/results

All test/check commands set `PYTHONDONTWRITEBYTECODE=1`. Local evidence only.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; cached main/HEAD and branch as above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before work: both required blobs match. |
| Python sorted path/SHA-256 inventory of `reference/v0.3-rc1/**` | Before work: 108 files; inventory hash below. |
| `python3 -m unittest readiness.test_faults.RecordSizeBoundaryTests` | PASS: 2 tests (four accepted round-trip subtests and two rejection/reuse subtests). |
| `python3 -m unittest readiness.test_faults` | PASS: 69 tests. |

The workflow's **Stdlib offline document checks** block was read and its
63 listed commands extracted and executed sequentially, with the explicit
plain-loopback exclusion below (no shell background jobs). The first pass
had 61 successes, one index formatting failure and one exclusion. After the
index correction and targeted rerun, all 62 permitted commands passed.
This is not a claim that the excluded real-socket probe passed.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | PASS (exit 0): capability register ok: paths=454 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | PASS (exit 0): rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | PASS (exit 0): read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=313 indexed=278 allowlisted=35 |
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
| `python3 scripts/check_class_b_index.py` | Initial FAIL (exit 1): blank line separated CB-218 from the table; removed that line. Rerun PASS (exit 0): rows=218 sources=73 symbols=47. |
| `python3 scripts/check_class_b_index.py --self-test` | PASS (exit 0): self-test: pass (20 negative controls) Also rerun after the table fix: PASS. |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 scripts/check_loopback_host.py` | NOT_RUN: plain mode opens real loopback sockets, excluded by this node. Fake-socket self-test below is permitted. |
| `python3 scripts/check_loopback_host.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_cargo_offline_cache.py` | PASS (exit 0): total=18 present=18 missing=0; host cache observation only. |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | PASS (exit 0): self-test: pass |

Other actual verification:

| Command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests. |
| `rustup toolchain list` | Installed active/default 1.98.1; no installation. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS, exit 0: all workspace tests and doc-tests, including kix-kernel; log summaries total 339 passed, 0 failed, 0 ignored across 46 test binaries/doc-test groups. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | PASS, exit 0: kix-kernel → kix-types only. |
| Python stdlib sizing calculation for the explicit schema-1 stamped envelope | PASS: empty payload overhead 127 bytes. ASCII serialized characters equal bytes at 1048575/1048576/1048577; multibyte serialized characters are 299685/299686/299687 respectively. |
| Python before/after reference path and byte-hash comparison, plus both `git hash-object` checks | PASS: all 108 paths/byte hashes identical; both locked blobs match. |
| Python comparison of index rows with `git show HEAD:docs/status/CLASS_B_CHARACTERIZATION_INDEX.md` | PASS: all 217 existing rows byte-identical; only CB-218 appended. Counts recomputed, with one additional validation row and test-cited row. |
| `git diff HEAD --name-only` and `git ls-files --others --exclude-standard`, checked against the four-path allowlist | PASS: exactly the four authorized output paths below. |
| `git diff --check` | PASS: no whitespace errors. |
| `git rev-parse HEAD` after work | Unchanged starting HEAD `9e0ea233b418d6ad536c581320a53b5e64a057fa`; no commit containing the edits. |

Discovery-only reads initially tried `.github/workflows/ktx.yml` and
`.github/workflows/kernel.yml` (absent, exit 1), then read the actual
`.github/workflows/ktx-kernel.yml`. An initial search used the absent
`docs/status/READINESS_CONTRACT_EVIDENCE_MAP.md` before locating and reading
`docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`. These were path discovery
misses, not failing regression results. No network command was run.


## Protected paths

Complete authorized output list:

- `readiness/test_faults.py`
- `validation/2026-10-29-plan-readiness-record-byte-boundaries/README.md`
- `docs/README.md`
- `docs/status/CLASS_B_CHARACTERIZATION_INDEX.md`

Before/after-work required blobs (both comparisons passed):

| Path | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Reference inventory: 108 sorted paths and SHA-256 byte hashes, with sorted-key
JSON inventory SHA-256
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
After-work comparison matched every path/byte hash and the same aggregate hash.
The complete output-path allowlist also passed: all other tracked content,
including implementation, contracts, `.aiops/`, task documents and workflows,
remains unchanged. The readiness map retains
`Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`.

## Contract classification/non-claims

Class B: the implementation-only per-record UTF-8 byte ceiling and oversized rejection atomicity/reuse are source-informed characterizations, not approved product policy or backend-neutral requirements.

No explicit contract violation found. No implementation, contract, conformance
mixin, evidence-map grade, owner or recovery decision is changed.
`OPEN-LENPREFIX-MIDFRAME`, `OPEN-ZERO-BYTE-REINIT` and
`OPEN-FRAME-BOUNDARY-CUT` remain open with existing owners, as do all nine OPEN
rows. Production durability and policy values remain UNDETERMINED.
No `.aiops/`, task input, workflow, locked kernel or protected reference edit.

No power-loss, OS-crash, physical-media/fsync proof, distributed fencing,
external exactly-once, chain finality, production readiness or clean-room
independence claim. No real funds, provider/bank/KYC calls, sockets, external
services, Sui network, new protocol command, production runtime, storage engine,
replication, consensus, secrets, paid tooling or hardware acquisition.
`protocolTruth`, `productionConformance`, `productionReadiness`,
`productionEndpoint` and FSM `durable` remain false.

## Review and CI gates; deviations

The supervisor's explicit no-network rule supersedes AGENTS §1 fetch.
The supplied node is the immutable task input; no task document is created.
The combined HTTP/readiness CI command is narrowed to `readiness.test_faults`
under the node's no-socket boundary. The design plan also listed the plain
`check_loopback_host.py` preflight among stdlib commands; source inspection
showed it opens real sockets, so only its fake-socket self-test was run.
This is the sole local-check exclusion within the design's listed command set.
Unrelated protocol workflow bootstrap, HTTP, SDK/Move/ZK, service and local-chain
jobs are not local equivalents for the changed tests; they were not run, and
full hosted CI remains required. Offline Rust commands use installed
cached tooling/dependencies; no installation or host modification.

Non-author A2 exact-head review remains outstanding. KTX kernel verification
and KIX protocol verification exact-head run IDs/status/conclusions are
NOT_RUN/unverified in this session; no final committed task head exists yet.
Local success cannot substitute for either required hosted workflow, including
required jobs. No commit, push, PR, issue, comment or merge is performed.
READY means local builder handoff only, not merge-ready or an independent PASS.
Remaining follow-up: supervisor publication, final-head review/CI and any
user-authorized merge/post-merge verification. Recovery decisions and policy
values stay with their existing owners.
