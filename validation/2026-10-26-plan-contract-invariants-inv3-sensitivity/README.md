# INV-3 corrupted-view sensitivity — local validation

Builder-authored evidence, not non-author A2 review, acceptance, a capability grade change or merge readiness. READY means local delivery to the supervisor.

Node/task ID: `plan-plan-contract-invariants-inv3-sensitivit`. The user-supplied node specification and read-only design plan are the immutable task input; no issue or current task document under `docs/tasks/` exists for this node. Task source: planner run 1793006593 (`/workspace/kix-run/logs/planner_1793006593`), dependency `plan-plan-contract-invariants-evidence-map`. Branch: `agent/kix-plan-plan-contract-invariants-inv3-sensitivit`. This is not an ASTRA program-mode session.

Locally observed `origin/main`, initial task HEAD and delivery-time Git HEAD: `ae6b905104d0cb2022001fb32ad98b1a6b3046ec`. There is no local base delta. Checks apply to the uncommitted working tree. No implementation commit or final task commit was created; publication belongs to the supervisor. Remote freshness is unverified: `git fetch origin main` was omitted because the final supervisor rule prohibits network actions. No commit, push, reset, GitHub action, issue, PR, comment, merge, tag or branch change was performed. No long job was launched in the shell background.

Changed paths (complete delivery list):

- `runtime/crates/kix-kernel/tests/contract_invariants.rs` — extract the observed replay predicate used by `Observer::run` into `check_replay`, add public before/after views, and add one source-informed INV-3 sensitivity test.
- `docs/README.md` — one required index link to this validation record (repository evidence corrects the design assumption).
- `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md` — cite the test, narrow F-B2, keep INV-3 PARTIAL and re-verify unchanged counts.
- `validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md` — this record.

Existing coverage mapping before adding the fixture (AGENTS.md §7):

| Requirement | Existing coverage | Classification before this node | New evidence / remaining boundary |
|---|---|---|---|
| Same typed first result and replay flag for a real retry | `runtime/crates/kix-kernel/tests/transitions.rs::response_loss_retry_returns_original_before_availability_check`; `contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories` | Sufficiently covered for those finite examples | Reuse the corpus replay predicate; no duplicate kernel-behavior test added. |
| First results remain immutable after later state changes | `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::rejection_replay_stays_immutable_after_the_blocking_hold_is_released`; `transitions.rs::expired_hold_retry_keeps_original_result_and_separate_current_state` | Sufficiently covered for those finite examples | New fixture alters saved observation copies after Send/Capture, for Held and Rejected outcomes. |
| Read-only replay, including stale context | Generated corpus and `contract_edge_cases.rs::replay_lookup_is_guarded_by_scope_and_semantics_only` | Partially covered at the observation boundary | Public views are compared explicitly; private admitted time remains witnessed only by whole-kernel Eq. |
| INV-3 checker rejects altered reply value/flag/error, changed public state/Eq sentinel and rewritten first results | `contract_invariants.rs::contract_predicates_reject_corrupted_observations_not_kernel_mutations` checks INV-1/2/4/5 only | Not covered (F-B2) | New `inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations` exercises all requested corrupted-copy cases through the same `check_replay` as the corpus. Unmodified probes pass; kernel equals its snapshot afterward. |
| Corpus shape and generated-history main test | Existing corpus assertions and map checker | Sufficiently covered for source/count agreement | Main function byte-identical to base; all seven corpus checks still MATCH. |

The new fixture observes both Held and Rejected first results without predicting the rejection variant. It confirms Capture changed state, validates unmodified replay probes, then changes observer copies only. Each alteration must return its specific INV-3 error prefix. It does not mutate the kernel or e4 model. The false `kernel_unchanged` boolean simulates the sentinel observation; it does not inject or independently inspect a private clock change. Source-informed authorship is explicit. INV-3 therefore remains PARTIAL; F-B2 is narrowed, not declared fully resolved. Counts remain **rows=27 COVERED=10 PARTIAL=12 NOT_COVERED=3 OPEN=2**. F-B1/F-B3/F-B4 and contract §4's four historical corruption examples remain unchanged.

Locked blobs, checked before edits and after verification:

| File | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Commands below were run from the repository root. Cargo uses `--offline` under the no-network instruction; dependencies were available. Tool versions actually observed: rustc 1.98.1 (48a229cea 2026-09-01), Cargo 1.98.1 (797e8a9bc 2026-08-05), Python 3.13.5. Workflow sources inspected: `.github/workflows/ktx-kernel.yml` and `.github/workflows/protocol.yml`. Local equivalents cover KTX kernel tests/Clippy/format/dependencies, protocol workspace Rust checks, architecture gates and the complete stdlib offline document-check block.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse origin/main HEAD` | Exit 0; initial worktree clean, expected branch, both SHAs equal base above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | Exit 0; both full locked pins above match. |
| `rustfmt --edition 2024 runtime/crates/kix-kernel/tests/contract_invariants.rs` | Exit 0; formatted only the allowed test file. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked --offline` (initial and restored) | Exit 0; 4 passed, 0 failed/ignored in each positive run. |
| `python3 scripts/check_contract_invariants_evidence_map.py` (initial) | Exit 1: new citation “is not a #[test] fn” because the doc comment was between the test attribute and fn. Moved comment above attribute; checker unchanged. |
| `python3 scripts/check_contract_invariants_evidence_map.py` (corrected) | Exit 0; 27 rows, corpus, anchors, test symbols, counts and locked blobs OK. |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; 2 positive controls and 66 negative fixtures OK (memory only). |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; 13 negative controls pass. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 86 passed, 0 failed/ignored; doc-tests succeed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; Clean with -D warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; Clean; check only, no mutation. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 265 passed, 0 failed/ignored; doc-tests succeed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; Clean with -D warnings. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; only normal dependency is local kix-types v0.0.0. |

Negative-control procedure (local only; no committed mutation):

1. A Python wrapper copied the finished allowed test file to `/tmp/ci_inv3_backup.rs` using `shutil.copyfile` and ran `git hash-object runtime/crates/kix-kernel/tests/contract_invariants.rs`: **f1cc5b565a6dfb239795f586ae5e6454f377830b**.
2. It inserted `return Ok(()); // Temporary negative control; restored immediately.` as the first statement of `check_replay`. Neither locked file was touched.
3. It ran `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked --offline` synchronously through `subprocess.run`: expected **exit 101**, **3 passed; 1 failed**. Only the new INV-3 fixture failed at `crates/kix-kernel/tests/contract_invariants.rs:645:22`, with ``called `Result::unwrap_err()` on an `Ok` value: ()``. Two compile warnings (unreachable statement and unused probe) are specific to this temporary disabled predicate. Raw output was saved locally to `/tmp/ci_inv3_negative.log`.
4. A `finally` block copied the backup back; the restored Git blob is **f1cc5b565a6dfb239795f586ae5e6454f377830b**, exactly matching the backup. The wrapper asserted exit 101 and the expected failing test/panic text. No `git restore` was used.
5. The restored narrow command passed all four tests; subsequent crate/workspace Clippy and formatting checks passed without those warnings.

This demonstrates that disabling the shared corrupted-view predicate is detected by the new test. It does not establish independent specification correctness or production fault-injection coverage.

Byte checks already run: inline Python compared the generated-history main function slice (from its fn signature to the next #[test]) with `git show origin/main:runtime/crates/kix-kernel/tests/contract_invariants.rs`: byte-identical, SHA256 `f8f18cbc84d59933d7d3a19336a347c8b1f8ee92f4ef2ddaf4236fcea8557eff`. A raw-byte comparison using `git ls-tree -r -z origin/main -- reference/v0.3-rc1` and `git cat-file blob <blob>` confirmed all **108** tracked reference files identical. `git diff --name-only origin/main -- docs/contracts docs/adr docs/tasks reference/v0.3-rc1 .aiops runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/tests/e4_state_model.rs scripts .github/workflows` returned exit 0, empty output.

The generated corpus artifact reports 256 sequences, 24,576 primary calls, 156,312 read-only replay probes, 434 retained capture facts and 0 failures. Replay probes are separate from the primary-call product. These are finite in-memory observations, not throughput or completeness claims.

No class C contract violation or new contract-undefined behavior was identified. The remaining class B INV-3 boundary is private admitted-time observability and source-informed authorship, with the kernel contract owner/non-author A2 reviewer unchanged. Other map uncertainties remain with their existing owners.

Deviations: fetch omitted under the supervisor's explicit no-network rule; Cargo commands add `--offline`. The full offline block initially stopped at `python3 scripts/check_docs_index.py` (exit 1: `not indexed: validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md`). The checker explicitly scans `validation/*/README.md`, contradicting the design assumption that no docs-index edit was needed. Added one pointer in `docs/README.md`, then re-ran the whole block. The design was otherwise followed. Added assertions on the observed Held outcome, number of saved first results and captured amount make the fixture setup explicit. The citation-format failure was fixed by moving the doc comment above #[test], without changing the checker. No product policy decision or scope expansion was needed; no decision request was created.

Exact-head KTX CI run ID/status/conclusion: **not queried/not run**. Exact-head KIX protocol CI run ID/status/conclusion: **not queried/not run**. Final committed task head and merge commit: **none**. Post-merge main CI: **not applicable**. Supervisor follow-up: commit/publication, non-author exact-HEAD A2 review, both final-head workflows and any later authorized merge/post-merge checks. Local READY is not merge-ready.

Non-claims: no grade change, clean-room authorship, independent proof/specification oracle, production fault injection, production durability, distributed fencing, bank exactly-once, chain finality, legal compliance or production readiness. No full hosted protocol pipeline, SDK/Move/ZK/localnet, provider/bank/KYC calls, funds, public endpoints, Sui testnet/mainnet, new command/policy value or storage/replication engine was run or introduced. The kernel/reference/task/contract/e4/.aiops/CI/script boundaries remain unchanged.

Full **Stdlib offline document checks** block: extracted from `.github/workflows/protocol.yml` and executed sequentially through Python `subprocess.run`, with each actual command/result below. After the required index pointer was added, **all 53 commands exited 0**. The earlier attempt stopped at the index failure recorded under deviations.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=272 indexed=237 allowlisted=35 |
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
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=22 PARTIAL=15 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=35 PARTIAL=18 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (83 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Final working-tree checks after recording the full offline block:

| Command | Actual result |
|---|---|
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=272 indexed=237 allowlisted=35. |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; 27 rows, corpus, anchors, test symbols, counts and locked blobs OK; all seven corpus rows MATCH. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/tests/contract_invariants.rs` | Exit 0; locked pins `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`; delivered allowed test file `f1cc5b565a6dfb239795f586ae5e6454f377830b` matches its restored backup. |
| `git diff --name-only origin/main -- docs/contracts docs/adr docs/tasks reference/v0.3-rc1 .aiops runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/tests/e4_state_model.rs scripts .github/workflows` | Exit 0; empty output. |
| `git diff --stat`; `git status --short` | Exit 0; three modified tracked paths plus the one new validation directory, exactly the four delivery files listed above. Untracked README is absent from diff --stat until the supervisor stages it. |

Local test artifacts include `.local/verification/ktx/contract-inv3-sensitivity.txt` and `contract-invariants-summary.json`; these generated diagnostics remain local. No repository commit was created to record validation evidence.
