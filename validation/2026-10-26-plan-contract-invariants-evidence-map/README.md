# Contract invariants evidence map — local validation

Builder-authored record, not non-author A2 review, acceptance, a grade change or merge readiness. READY means local delivery to the supervisor.

Node/task ID: `plan-plan-contract-invariants-evidence-map`. The user-supplied node specification and read-only design plan are the immutable task input. There is no issue or current task document under `docs/tasks/` for this node. Source supplied by the task: planner run 1792972994. Branch: `agent/kix-plan-plan-contract-invariants-evidence-map`.

Locally observed `origin/main`, initial task HEAD and delivery-time Git HEAD: `54a785b864d629d623afc36ed807d9daebaf9285`. There is no local base delta. Checks apply to the uncommitted working tree below. No implementation commit or final task commit was created; publication belongs to the supervisor. Remote freshness is unverified: `git fetch origin main` was not run because the final supervisor instruction prohibits network actions. No commit, push, reset, branch change, merge, GitHub action, issue, PR or comment was performed. No long job was launched in the shell background.

The [map](../../docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md) is the AGENTS.md §7 existing-coverage mapping: **27 rows; 10 COVERED, 12 PARTIAL, 3 NOT_COVERED, 2 OPEN**. It covers contract §§1–5, INV-1..INV-5, corpus/initialization/probes, four corrupted-observer sensitivity cases and every §5 limitation. Every cited test body was read. Contract-path and source-informed evidence remain separate. INV-2 is PARTIAL because physical private command-map allocation is unmeasured. No Rust test was added or changed.

New evidence: the map and stdlib checker close a traceability/structural-validation gap. The checker verifies row/header/section/INV sets, counts, status/gap/owner rules, existing open-input ids, repo-relative citations to #[test] fns in permitted columns, raw locked blobs, corpus facts and forbidden oracle imports. Its self-test uses **2 positive controls and 66 negative fixtures**, entirely in memory. Missing/duplicate/miscounted rows, helper/missing/bare/mixed citations, path/column errors, blob/anchor drift, each corpus dimension, recorded/unrecorded B findings and oracle imports are exercised. The positive source-drift fixture updates both derived product and source-fact cells, preventing stale numbers from passing as a recorded mismatch.

Changed paths (complete delivery list):

- `.github/workflows/protocol.yml` — exactly two invocations in the existing stdlib document-check step.
- `docs/README.md` — one index bullet linking map and validation record.
- `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md` — new map.
- `scripts/check_contract_invariants_evidence_map.py` — new read-only stdlib checker with --self-test.
- `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md` — this record.

Locked blobs were checked before edits and after implementation/testing. The checker also hashes raw bytes; self-test substitutes in-memory bytes and never mutates either file.

| File | Before | After |
|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | 69564b166f0c27f9af5d8422f0a466b18d74c20f |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | b607996c83a119c349f1cc90469ac1ba82764e20 |

Commands actually run from the repository root. Narrow checker checks preceded broader verification. Cargo used --offline because network actions are forbidden; dependencies were available. Observed tools: Python 3.13.5; rustc 1.98.1 (48a229cea 2026-09-01); Cargo 1.98.1 (797e8a9bc 2026-08-05).

| Command | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` | Exit 0; both equal the full base SHA above. |
| `git branch --show-current` | Exit 0; expected task branch above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs docs/contracts/CONTRACT_INVARIANTS.md runtime/crates/kix-kernel/README.md docs/contracts/STATE_LIFECYCLE.md docs/adr/0001-ktx-authority-commit-recovery.md` | Exit 0; locked pins match. Contract blob 9c59e0a81f1675fa919ba9327642269bef9e70af; kernel README 788896ed3e00bae3d06d26b7e2ce999a00ff1029; lifecycle 8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d; ADR 054bc714b3c475fb8536df8d2d788b42e8c74b6c. |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; 27 rows, corpus, anchors, test symbols, counts and locked blobs OK. |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0 on initial and later runs; initial 57 negative fixtures passed, final expanded suite has 2 positive controls and 66 negative fixtures, all pass. |
| `python3 scripts/check_contract_invariants_evidence_map.py --invalid` | Expected exit 2 with usage; an inline subprocess assertion of exit 2 passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 78 passed, 0 failed/ignored; doc-tests succeed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --locked --offline` | Exit 0; 56 passed, 0 failed/ignored; doc-tests succeed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 257 passed, 0 failed/ignored; doc-tests succeed. Includes both kernel crates. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; no source mutation. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; all workspace targets pass, including KTX kernel Clippy scope. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance not certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `git diff --check` | Exit 0. |
| `git diff --name-only origin/main -- docs/contracts docs/adr docs/tasks reference/v0.3-rc1 .aiops runtime` | Exit 0, empty output; no protected/source path changes. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 after implementation/testing; both full pins match above. |
| Inline Python raw-byte comparison using `git ls-tree -r -z origin/main -- reference/v0.3-rc1` and `git cat-file blob <blob>` | Exit 0; all 108 tracked reference files raw-byte identical to locally observed origin/main. |
| `git status --short` | Exit 0; exactly the five delivery paths above. |

The authoritative **Stdlib offline document checks** run block in protocol.yml was extracted with Python and every command executed sequentially through subprocess: **41 commands, all exit 0**. These are the exact invocations, including docs-index and status-register self-tests. Repeated final checks cover the completed record too.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0: capability register ok: paths=385 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0: rs profile traceability ok: blueprint=47 profile=47 expected=47. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0: read model source map ok: queries=13 anchors=128 catalogues=2 citations=145. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_docs_index.py` | Exit 0: docs index ok: scanned=250 indexed=215 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0: i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0: delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0: rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0: rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0: tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0: contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0: adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0: v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0: readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0: self-test: pass. |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0: settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8. |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0: self-test: pass (33 negative controls). |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0: bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2. |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0: self-test: pass (50 negative controls). |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0: credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3. |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0: self-test: pass (55 negative controls). |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0: primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5. |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0: self-test: pass (76 negative controls). |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0: ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1. |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0: self-test: pass (86 negative controls). |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0: lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK. |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0: self-test: positive injected citation and 49 negative fixtures passed (memory only). |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0: contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK. |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0: contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only). |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0: self-test: pass. |

Corpus findings: **all seven rows MATCH**. The source has 4 fixtures (2 seat, 2 GA), 64 seeds, six initialization plus 90 generated calls, and an asserted 4 × 64 × 96 = 24,576 primary calls. Seat segments are [65,5], GA capacity is 6. E4 has four baseline cases × 256 seeds × 128 steps = 131,072 comparisons. Replay probes are separate. Checker consistency is textual/count evidence; it does not certify the generator or semantic completeness.

Contract discrepancies: **no explicit class C kernel contract violation identified**. Four class B characterizations remain in the map with owners: F-B1 historical source-anchor drift; F-B2 no INV-3 corrupted-view sensitivity fixture; F-B3 non-reserve reply values only read via is_ok() while predicates run after replies; F-B4 historical model naming does not change source-informed provenance. Current contract and historical pins were not edited.

Deviations from the read-only design plan: fetch omitted under the supervisor's later no-network rule; corpus fact cells are checked against extracted values as well as checking Result (the recorded-drift positive fixture therefore updates those cells); INV-2 uses the plan's permitted PARTIAL alternative; workspace tests/architecture-gate tests supplement the planned crate tests. No scope expansion or product policy decision was needed. No new decision request was created.

Exact-head KTX CI run ID/status/conclusion: **not queried/not run**. Exact-head KIX protocol CI run ID/status/conclusion: **not queried/not run**. Final committed task head and merge commit: **none**. Post-merge main CI: **not applicable**. Supervisor follow-up: commit/publication, non-author exact-HEAD A2 review, both final-head workflows and any later authorized merge/post-merge checks. Local results do not establish merge readiness or transfer CI evidence between SHAs.

Remaining uncertainty and non-claims: the map's named gaps/owners retain the private-allocation, corpus finiteness, shared-error, exact guard/phase/review, general availability and external custody boundaries. I11/I12/I13 and R2 remain open/locked as stated. No full hosted protocol pipeline, SDK/Move/ZK/localnet, external providers, live funds, public endpoints or chain execution was run. This task changes no Rust/kernel/contract/ADR/task/.aiops/reference bytes and makes no clean-room, specification-independence, production durability, distributed fencing, bank exactly-once, chain-finality, legal-compliance or production-readiness claim. Future semantic coverage or unlocks require separate authorization; this delivery only maps and checks existing evidence.
