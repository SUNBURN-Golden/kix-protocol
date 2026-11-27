# BCS1 clause evidence map — local builder record

Builder-authored evidence, not A2 review, acceptance, a capability grade change or merge readiness.

Task/node: `plan-plan-bcs1-contract-clause-evidence-map` (planner run `1792977654`). Task document: the immutable supervisor-provided node and design plan in the session; no issue or `docs/tasks/` file exists for this node. This is not an ASTRA program-mode session.

Observed local `origin/main`, starting branch HEAD, implementation-base HEAD and final local HEAD: `18aefc8f7c0dd13b7249e0d80304f3b97459fa3a`.
Branch: `agent/kix-plan-plan-bcs1-contract-clause-evidence-map`.
No commit was made; implementation is the five-file working-tree patch below. The supervisor will establish a committed final task head. The local base/HEAD delta was zero. Remote freshness and any delta from live main are unverified: the supervisor explicitly prohibited network actions, so `git fetch origin main` was not run.

Contract Git blob: `19a58ab1e232c54eb39b717a94c637322c493a4d` (`runtime/CANONICAL_BINARY_BCS_V1.md`).
Toolchain actually used: `rustc 1.98.1 (48a229cea 2026-09-01)`; `cargo 1.98.1 (797e8a9bc 2026-08-05)`. Cargo commands used `CARGO_NET_OFFLINE=true`; cached locked dependencies were sufficient. Commands were run sequentially in foreground subprocesses; no shell background jobs were used.

Complete changed-path list:

- `.github/workflows/protocol.yml`: two checker invocations, immediately after the Toss evidence checker pair and before stage-5 host self-test.
- `docs/README.md`: one bullet linking this record and the map under the 2026-10-26 index.
- `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md`: new 39-row map, follow-up candidates, characterizations and non-claims.
- `scripts/check_bcs1_evidence_map.py`: new standalone stdlib checker and in-memory self-tests.
- `validation/2026-10-26-plan-bcs1-contract-clause-evidence-map/README.md`: this record.

Existing coverage was inspected before adding the checker. The [map](../../docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md) classifies each requirement: 12 sufficiently covered fixture predicates (COVERED), 10 partially covered, 17 not covered. Every COVERED/PARTIAL row cites one or more of these seven unchanged tests:

| Existing file | Test functions |
|---|---|
| `runtime/crates/kix-bcs1/src/lib.rs` mod tests | `round_trip_and_hash_are_deterministic`, `wrong_magic_schema_version_and_trailing_bytes_are_rejected`, `bounded_utf8_rejects_oversize_values` |
| `runtime/crates/kix-bcs1/tests/golden_vectors.rs` | `fixed_bytes_and_hash_match_external_golden_values`, `u128_zero_and_max_are_lossless`, `domain_schema_and_version_are_bound`, `legacy_json_is_not_kix_bcs1_identity` |

No Rust tests or malformed-input corpus were added. The eight required follow-ups remain NOT_COVERED: zero-id InvalidSchemaIdentity; encode/decode BodyTooLarge separately; EnvelopeTooLarge; multi-byte UTF-8 byte-versus-character limits; truncated envelope; §5 Rust↔Move equality; §8 Move/SDK equality. Other uncovered schema/governance predicates retain gaps and candidate owners in the map. S08 work and the parked boundary-corpus node are not absorbed.

New evidence addresses document integrity only: clause IDs are checked for uniqueness/completeness, anchors within numbered contract sections, status/test/gap/owner consistency, exact test symbols in allowed files (including lib.rs mod tests membership), mandatory follow-ups and partial rows, counts, locked blobs, non-claims, and contract/Rust golden byte/hash equality. Self-tests include a positive injected test and 50 negative fixtures; deliberately missing `::absent` citations are rejected both alone and alongside a valid citation. All self-test mutations are in memory.

Actual local verification commands and results follow. Exit codes are zero unless explicitly stated. The full stdlib run block was extracted from the edited workflow and each command executed in its original order, using Python subprocesses with `PYTHONDONTWRITEBYTECODE=1`. No CI guards or external actions were emulated.

| Command | Actual result |
|---|---|
| `git status --short` (before) | Empty; worktree initially clean. |
| `git rev-parse origin/main HEAD` | Both `18aefc8f7c0dd13b7249e0d80304f3b97459fa3a`. |
| `git branch --show-current` | `agent/kix-plan-plan-bcs1-contract-clause-evidence-map`. |
| `git hash-object runtime/CANONICAL_BINARY_BCS_V1.md` | `19a58ab1e232c54eb39b717a94c637322c493a4d`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `b607996c83a119c349f1cc90469ac1ba82764e20`, both match. |
| `python3 -m py_compile scripts/check_bcs1_evidence_map.py` | Pass, no output (also rerun after checker constant formatting). |
| `python3 scripts/check_bcs1_evidence_map.py` | `BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17`. |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` (initial development run) | Exit 1: `anchor removed accepted or wrong diagnostic: []`. The fixture used a normalized string as an exact replacement against differently spaced source. Fixed the fixture to match normalized whitespace; contract was unchanged. |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` (corrected, repeated after final checker formatting) | `self-test: pass (2 positive controls, 50 negative fixtures)`; missing citation detected as `is not a test function`. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-bcs1 --locked` (narrow test, before broader checks) | 3 unit + 4 golden tests passed; 0 failures; 0 doctests. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-bcs1 --all-targets --locked -- -D warnings` | Exit 0;     Finished dev profile [unoptimized + debuginfo] target(s) in 1.59s |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; No output; formatting check passed. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 257 passed; 0 failed; 0 ignored across 42 result groups (including zero-test groups). |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 78 passed; 0 failed; 0 ignored across 9 result groups (including zero-test groups). |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0;     Finished dev profile [unoptimized + debuginfo] target(s) in 0.54s |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0;     Finished dev profile [unoptimized + debuginfo] target(s) in 0.45s |
| `rg -n 'check_bcs1' .github/workflows/protocol.yml` | Plain invocation at line 253; self-test at line 254 in the stdlib run block. |
| `git diff --quiet origin/main -- runtime reference/v0.3-rc1 .aiops docs/tasks` | Exit 0; no protected-tree changes. |
| `git diff --check` | Exit 0, no whitespace errors. |
| `git diff --name-only origin/main` plus `git ls-files --others --exclude-standard` | Exactly the five paths listed above (two tracked edits, three new files). |

All 45 commands from the protocol workflow's stdlib offline document-check step, in order (actual final output line shown):

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=256 indexed=221 allowlisted=35 |
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
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0; BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Locked blobs match before and after all tests, including checks inside the new checker. `runtime/**`, `reference/v0.3-rc1/**`, `.aiops/**` and `docs/tasks/**` remain byte-identical to the observed base. No contract or kernel mutation, even transient, was performed.

Contract discrepancy classification: no class-C explicit violation was found. Class-B source-informed characterizations remain uncertain: zero domain/schema rejection beyond the stated positive version; encode-side BodyTooLarge/EnvelopeTooLarge semantics; the unspecified 32-byte overhead bound and apparent encode-side EnvelopeTooLarge unreachability for realistic bounds; and oversize BoundedUtf8 body decode yielding BodyDecode rather than construction's BoundedUtf8Exceeded. These were recorded, not converted into new semantics or tests. The map preserves the ASCII-only/body-helper limitation and trailing-byte-only malformed-input evidence.

Deviations: no fetch, commit, publication or hosted checks because of the supervisor's explicit restrictions. The in-session node text is the task input, rather than a nonexistent docs/tasks document. Added workspace Clippy beyond the planned crate-only invocations because protocol.yml also runs it. Fixed the whitespace-sensitive self-test fixture described above. No scope changes or decisions were needed.

Exact-head KTX CI run ID/status/conclusion: not available, not requested or queried. Exact-head KIX protocol CI run ID/status/conclusion: not available, not requested or queried. No final committed delivery head, PR, merge commit or post-merge main CI exists for this builder delivery. Local results do not establish hosted CI success; final-head CI and non-author exact-head review remain supervisor responsibilities. No GitHub/network action, commit, push, issue, comment, branch/tag mutation or merge was performed.

Explicit non-claims: no production schema registry; no Move/SDK equality; no malformed-input corpus. No production runtime, real funds/provider calls, Sui testnet/mainnet, storage engine, policy value or protocol command was needed or introduced. No durability, finality, production readiness, legal compliance, clean-room independence or capability increase is inferred. Local verification covers the touched document/checker paths, the entire stdlib step and offline Rust CI equivalents; unrelated bootstrap, network, SDK, Move/localnet, storage and ZK workflow steps were not run.

Remaining uncertainty/follow-up candidates: the map's 17 uncovered and 10 partial requirements, S08 equality schema ownership, the parked boundary corpus, live-main freshness, and future committed-head CI/review. Candidate ownership in this map does not authorize those follow-ups.

Local builder delivery: READY; merge-ready is not claimed.
