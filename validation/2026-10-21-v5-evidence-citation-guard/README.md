# v5 evidence citation guard

Node: `plan-v5-evidence-citation-guard`; dependency:
`plan-plan-v5-transition-evidence-map`. Date: 2026-10-21. Issue: none.
Audit floor: A2; `astra_gate: None`; `user_merge: false`.
Not an ASTRA program-mode session.

Task input: the supervisor-supplied node specification and read-only design plan
in the builder prompt, sourced from KIX planner run 1792588608
(`/workspace/kix-run/logs/planner_1792588608`). No task document exists under
`docs/tasks/` for this node; none was created or changed. This loop-proposed node
is not in `.aiops/program.json`.

## Base and delivery boundary

Observed local `origin/main` and branch HEAD both:
`e9caa181278048cdd0c403929d00a03d5ecd3ab4`.
Branch: `agent/kix-plan-v5-evidence-citation-guard`; initial working tree clean.
No local base delta. The supervisor forbids all network/GitHub actions, so
`git fetch origin main` was deliberately not run; remote freshness is unverified.

All changes are uncommitted. No implementation commit, final task head, merge
commit or post-merge check exists for this patch. KTX kernel verification and
KIX protocol verification exact-head run IDs/statuses/conclusions are unavailable;
no hosted CI was queried or started. Non-author exact-head A2 review remains
pending. No commit, push, PR, issue, comment or merge was performed. Local READY
means ready for supervisor delivery, not merge-ready or accepted.

## Existing coverage and the reproduced gap (AGENTS §7)

All checker references below are to
`scripts/check_v5_transition_evidence_map.py`.

| Requirement | Before | Existing evidence / added coverage |
|---|---|---|
| Bare existing/missing paths, empty/spaces/tabs-only symbols in each fixture column | Not covered | New `_fixture_citation_self_test` mutations of `TERM`, keeping status/counts valid |
| Missing files, missing functions, helpers | Partially covered | Existing `dangling path`, `dangling test symbol`, `helper fn cited as a test` and `symbol_ok` probe; new column-specific controls for both columns |
| Valid/invalid mixed lists and multiple invalid members | Not covered | Each new negative runs alone, valid-before-invalid and invalid-before-valid; a combined list requires all four expected diagnostics |
| `none`, valid single/multiple citations | Partially covered | Real map and symbol probe; new explicit positives on `TERM` and stopped `SLOT-RELEASE` with zero problems required |
| Real-map counts, other grammar/status/path/anchor/open-input/lock checks | Sufficiently covered | Retain existing `self_test` negatives, locked-blob injection and removed-anchor control; plain CLI checks counts |
| Validation index coverage | Sufficiently covered | Existing `check_docs_index.py` and its self-tests; new direct index link |

Before the implementation fix, an importlib-based in-memory reproduction called
`find_problems(_with_cell(map_text, 'TERM', col, citation), sources, files=...)`.
The missing path was forced to `None` through `files`, and no Rust file was
created. All four cases returned `[]` (incorrect acceptance):

| Column | Bare citation | Original result |
|---|---|---|
| v5 tests | `runtime/crates/kix-kernel-v5/tests/termination.rs` | `[]` |
| v5 tests | `runtime/crates/kix-kernel-v5/tests/citation_missing.rs` | `[]` |
| Stop guard | `runtime/crates/kix-kernel-v5/tests/termination.rs` | `[]` |
| Stop guard | `runtime/crates/kix-kernel-v5/tests/citation_missing.rs` | `[]` |

`parse_cell` retained these citations, `has_tests` counted them, but
`citations_of` omitted them because their symbol was `None`. The fixture loop
only checked the allowed path pattern. This also skipped file existence checks
for bare missing paths. Regression expectations were added first; running
`python3 scripts/check_v5_transition_evidence_map.py --self-test` then exited 1
with missing citation-specific diagnostics, before changing validation logic.

## Implementation and changed paths

| Path | Change |
|---|---|
| `scripts/check_v5_transition_evidence_map.py` | Validate every parsed fixture citation locally; add memory-only negative and positive controls |
| `docs/status/V5_TRANSITION_EVIDENCE_MAP.md` | Clarify fixture grammar in §1 only |
| `validation/2026-10-21-v5-evidence-citation-guard/README.md` | This evidence record |
| `docs/README.md` | One dated index link |

Both fixture columns now require an allowed v5 test path, a nonempty symbol,
existing file text and the existing `symbol_ok` / `TEST_FN` match. Diagnostics
include row, column, path, symbol when present, and the particular failure.
A bare missing file reports both the missing symbol and missing file. Invalid
paths are rejected before reading. Lists validate every member. Document-wide
`citations_of`, CLI, status derivation, path rules and symbol matcher are unchanged.

New fixtures inject `citation_probe.rs` text containing two attributed functions
and a helper; `citation_missing.rs` maps to `None`. All fixtures stay in memory.
No Rust fixtures or runtime sources were created or modified.

## Verification commands and results

Commands were run in the foreground from the worktree. Environment:
Python 3.13.5 (protocol CI pins 3.12), rustc/cargo 1.98.1 (workflow toolchain pin).
Initial plain/self-test runs of both narrow checkers exited 0. The deliberately
red regression run above exited 1. After the fix both narrow checkers and their
self-tests exited 0 before the documentation changes.

The authoritative `Stdlib offline document checks` run block in
`.github/workflows/protocol.yml` was read unchanged and its 26 commands
executed sequentially through a foreground Python subprocess runner; every
command exited 0. The individual commands/results and the other checks are:

| Command | Actual result |
|---|---|
| `git branch --show-current; git rev-parse HEAD; git rev-parse origin/main; git status --short` | Exit 0; expected task branch, matching base/HEAD above; initially clean |
| `Inline Python raw-byte manifest / Git-blob calculation before editing` | Exit 0; 110 protected files; both required blobs match |
| `Inline Python importlib reproduction, original find_problems, four bare-path mutations` | Exit 0; all four returned [] (bypass reproduced) |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test (regressions added, before fix)` | Exit 1 as intended; new row/column/citation-specific expectations fail |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=195 indexed=160 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 78 passed, 0 failed across test binaries/doc-tests |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 257 passed, 0 failed across test binaries/doc-tests |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `Inline Python final raw-byte manifest, blob and map-section comparison` | Exit 0; 110 protected paths/bytes identical, both blobs match; map section and all subsequent bytes identical |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/decisions` | Exit 0; no changes |
| `git diff --check` | Exit 0 |

The Rust pass totals are sums of the actual `test result: ok` lines, not
counts inferred from source. These checks cover the planned closest local
architecture/Rust equivalents of both workflows and all stdlib document
checks. Full hosted verification (including dependency bootstrap,
Python/TypeScript/Move/circuit/storage/localnet integration and artifact
upload) was not run or claimed. No dependencies were installed.


## Protected-file integrity

Before editing, raw-byte Git blob checks matched both required values:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

A sorted path-to-SHA256 manifest covers those two files plus every regular file
under `reference/v0.3-rc1/**`: 110 files. The pre-edit JSON manifest's SHA256 is
`9c7c90516fd728796b19b905abb0513235dddd91ccf5eea02838d53f487efaed`.
The final check compares both path sets and raw-byte digests with that snapshot,
plus the map from `## 2. Map` onward with its pre-edit bytes.
The final comparison passed: all 110 path/digest entries are identical
(108 reference files and the two locks), both required blobs still match,
and every byte from the map section onward is unchanged. No protected file
was mutated, including transiently. No final-merge blob check applies.


## Discrepancies, deviations and limits

The discovered issue is the checker gap reproduced above, not a runtime/lifecycle
contract violation. No runtime contract discrepancy or new contract-undefined
behavior was found; no authoritative contract or owner decision was amended.
There was no scope/design deviation. The no-network supervisor instruction
overrode the session-start fetch; offline Cargo is used without installing
dependencies or changing CI. Hosted-only verification is not inferred from
these local results.

This record claims citation validity only. `TEST_FN` remains a textual matcher,
not a Rust parser; no claim is made about what a cited test asserts, semantic
coverage, clean-room independence, independent review, lifecycle approval,
durability, distributed fencing, bank exactly-once, chain finality, legal
compliance or production readiness. The real map remains 10 rows, 6 TESTED,
4 STOPPED, 0 OPEN. I09–I13, all UNDETERMINED values, lifecycle stops and owner
decisions retain their status. Runtime, workflows, `.aiops/`, task documents,
contracts, decisions and historical evidence are outside the changed paths.

No hardware, paid service, credential, production runtime, provider/network call,
storage engine, policy value or protocol command was needed. Remaining work is
supervisor publication, exact-head hosted CI and non-author review; no merge is
authorized by this record.
