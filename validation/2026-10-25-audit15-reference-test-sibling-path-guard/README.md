# Audit 15 reference-test sibling path guard — builder validation

## Basis and delivery boundary

Node: `audit15-reference-test-sibling-path-guard`. Date: 2026-10-25.
The supervisor-supplied node specification and read-only design plan are the
current task document; no task file under `docs/tasks/` or issue exists for this
node. Source: KIX audit #15 finding 4. Not ASTRA program mode.

Branch: `agent/kix-audit15-reference-test-sibling-path-guard`.
Starting HEAD/base and observed cached `origin/main` all equal
`fe08e4134b2f2e58f48b636bdae7440d8cdb70dc`; no local base delta.
`git fetch origin main`: NOT_RUN under the supervisor's explicit no-network
rule, overriding AGENTS §1. Remote freshness is unverified.
Implementation/final task head: uncommitted working-tree patch above this base;
no new SHA. Exact-head KTX/KIX run IDs, status and conclusions are unavailable,
NOT_RUN/not queried. Merge SHA, final-merge locks and post-merge main CI are
not applicable. Git/GitHub publication belongs to the supervisor.

## Changed paths

- `reference/ai_delegation/test_rejection_atomicity.py`
- `reference/ai_delegation/test_restore_fingerprint_equivalence.py`
- `reference/token_reward/test_reward_fsm.py`
- `docs/README.md`
- `validation/2026-10-25-audit15-reference-test-sibling-path-guard/README.md`

## Locks and preserved evidence

Before edits and after implementation, kernel blobs match the required values:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`src/lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
The HEAD tree for `reference/v0.3-rc1` is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
One-time assertions compare all 108 tracked reference files, their complete on-disk
path set, bytes and executable modes against HEAD. All pass. Neither locked file
nor the preserved reference was edited, even transiently.

## Existing coverage mapping (AGENTS §7)

| Requirement | Before edits | Evidence used here |
|---|---|---|
| Preserve suite import priority | Partially covered: #277's `reference/booking_resale_admission/test_read_model_fixtures.py` uses index 1; five per-suite discoveries pass, but the three scoped insertions still use index 0 | Change only these three insertions to index 1 |
| AI mock and readiness wrap import origins | Not covered by `RejectionAtomicityTests` or the restore fingerprint classes; they exercise behavior without checking `__file__` | One `SiblingImportPathTests.test_imports_resolve_from_intended_directories` in each AI test module |
| Settlement and reward FSM import origins; temporary path cleanup | Partially covered: `RewardFsmTests.test_live_settlement_view_field_names_match_and_can_be_read` exercises the settlement helper, but does not assert origins | `SiblingImportPathTests.test_settlement_view_imports_from_settlement_suite` checks both origins and path cleanup |
| Preserve existing behavior and counts | Sufficient existing coverage in five reference suites and HTTP/readiness suite | Reuse unchanged, compare baseline/final counts |
| Indexed validation, document/map/code counts | Sufficient checker coverage in protocol.yml's 27-command document step | Reuse plain and self-test forms; compare outputs to baseline |

## Commands actually run and results

All commands ran from the worktree root in foreground tool sessions, without
background/detached jobs. Python validation used `PYTHONDONTWRITEBYTECODE=1`.
The first baseline discovery loop's terminal output was not fully captured;
the complete loop was repeated before edits with per-suite scratch logs. The
recorded baseline below is from that complete repeat. No baseline failure was
observed. The document comparison run began before edits and finished after the
implementation edit; the baseline docs-index count was captured before editing.

Narrow checks ran before broader final verification:

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -k SiblingImportPath -v` | Exit 0; 2 new guards passed, one in each AI module. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -k SiblingImportPath -v` | Exit 0; 1 new guard passed. |

Baseline and final per-suite commands and counts:

| Command (prefix `PYTHONDONTWRITEBYTECODE=1`) | Before edits | After edits |
|---|---|---|
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 187 passed | Exit 0; 187 passed |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 402 passed | Exit 0; 402 passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0; 147 passed | Exit 0; 147 passed |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Exit 0; 83 passed | Exit 0; 85 passed |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; 167 passed | Exit 0; 168 passed |

Only the required guard additions increase counts: AI delegation +2 and token
reward +1. The remaining suites retain exactly their baseline counts.

Closest local equivalents for protocol.yml's HTTP/reference/OpenAPI steps and
ktx-kernel.yml's architecture/kernel/lint/format/dependency steps:

| Command | Actual result |
|---|---|
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0; 100 tests passed; self-test: pass. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 78 tests passed, 0 failed; doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; Finished successfully with -D warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; No formatting diagnostics; check only, no files rewritten. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; kix-kernel v0.1.0 → local kix-types v0.0.0 only. |

Rust checks used the existing Rust/Cargo 1.98.1 toolchain and installed Clippy /
rustfmt. `--offline` prevents network access; no toolchain or dependency
provisioning occurred. No Rust file changes, so unrelated workspace crate tests
were not rerun. Kernel coverage and whole-workspace formatting match KTX's local
steps. Dependency tree evidence is reported above; artifact upload is not run.

The 27 commands were extracted from the actual unguarded `Stdlib offline document
checks` run block in `.github/workflows/protocol.yml`, asserting its command count,
and run sequentially with `subprocess.run`, stopping on any nonzero result.
Both comparison and final runs exited 0 for every command. Outputs below are
from the final run. All non-index outputs (including self-test diagnostics)
byte-match the comparison run. The index alone changes from
`scanned=230 indexed=195 allowlisted=35` to
`scanned=231 indexed=196 allowlisted=35`, exactly the new validation record.
Intentionally detected synthetic faults are self-test success, not repository
failures; checker self-tests use scratch copies and do not mutate locked files.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; `capability register ok: paths=364 ev_ids=15 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0; `docs index ok: scanned=231 indexed=196 allowlisted=35`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; `delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6`. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; `rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; `rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2`. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7`. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; `contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0`. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8`. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0`. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; `readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; `self-test: pass`. |

Additional commands actually run, with read-only inspections grouped:

| Command / check | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse HEAD origin/main` | Exit 0; expected worktree/branch; clean initially; HEAD/cached main equal the basis SHA above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before and after implementation; both required blobs match. Final acceptance repeats these checks. |
| `git rev-parse HEAD:reference/v0.3-rc1` | Exit 0; `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git diff --exit-code HEAD -- reference/v0.3-rc1` | Exit 0; unchanged. |
| `git diff --name-only HEAD -- .github .aiops docs/tasks docs/contracts docs/decisions scripts runtime readiness` | Exit 0; empty. |
| `rg -n 'sys\.path\.insert\(0' reference/ai_delegation reference/token_reward` | Exit 1; no matches, expected absence. |
| `command -v cargo`; `rustup toolchain list`; `rustup component list --installed`; `cargo --version`; `rustc --version` | Exit 0; existing toolchain 1.98.1, Clippy/rustfmt installed; local dependency cache inspected with `rg --files`. |
| `python3 /tmp/audit15-sibling-acceptance.py` | Exit 0; exact five paths, test/index edit reversals byte-match HEAD, both locks, all 108 reference paths/bytes/modes, expected suite count deltas and all 27 checker comparisons pass. Repeated after record transcription. |
| `git ls-tree -rz HEAD reference/v0.3-rc1`; `git cat-file blob <blob>`; on-disk byte/mode comparisons (via acceptance script) | Exit 0; all 108 reference files and complete on-disk file set match HEAD. |
| `git diff --check` | Exit 0; no whitespace diagnostics. Untracked record also passes trailing-whitespace assertions. |
| `git diff --stat`; `git diff -- <three test modules> docs/README.md`; `git status --short --untracked-files=all` | Exit 0; reviewed minimal three edits/guards and one index bullet; exactly the five specified paths. |
| `cat`, `sed`, `rg` over AGENTS, README, development plan, baselines, authority model, task paths, program decisions, candidate policy pointer/pin, audit #15, #277 precedent, existing tests/wrap, docs index and both workflows | Read-only inspection. The initial attempt to read `.github/workflows/ci.yml` found no such file; the correct `ktx-kernel.yml` and `protocol.yml` were then read. Optional `.cargo` / target / alternate-cache search paths that do not exist were ignored; the installed toolchain/cache were verified separately. |

Scratch outputs: `/tmp/audit15-sibling-baseline-<suite>.log`,
`/tmp/audit15-sibling-final-<suite>.log`,
`/tmp/audit15-sibling-baseline-docs.json`,
`/tmp/audit15-sibling-final-docs.json`, and
`/tmp/audit15-sibling-local-ci.json`. These are local evidence only and are not
repository deliverables. No repository checker or test failed; no CI change or
out-of-scope fix was needed.

## Contract findings (A/B/C) and non-claims

A: the node's import-path requirements are implemented without contract changes.
B: `readiness/ai_delegation_wrap.py:21` still inserts its own AI suite at index 0
when imported outside discovery; unchanged, a follow-up candidate. The guards
cover the three scoped modules. Combined discovery of multiple suites in one
process is untested; CI discovers each separately.
C: no explicit contract violation found.

No FSM, mock, contract, policy, command, grade, runtime, CI, `.aiops/`, task input,
rights-scale or historical evidence change. No production readiness, durability,
distributed fencing, bank exactly-once, chain finality, legal compliance,
clean-room independence or full-verification claim. Exact-head CI and non-author
review remain pending; no older CI evidence transfers. Heavy ZK, Move, localnet,
Node/SDK and paid-storage workflow steps, plain stage-5 host evaluation and
optional scratch shadow-module sensitivity probes are NOT_RUN; they are outside
this node's local verification scope. Local READY means builder
handoff only, with no merge proposal.

## Deviations

Fetch omitted under the supervisor's explicit no-network rule. No substantive
design deviation. Rust checks use provisioned tools and cache in offline mode.
No commit, push, PR, issue, comment, merge, tag or branch operation is performed.
