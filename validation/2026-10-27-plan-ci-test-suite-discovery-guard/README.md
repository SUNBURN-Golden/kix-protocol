# plan-ci-test-suite-discovery-guard

## Identity and base

Node: `plan-ci-test-suite-discovery-guard`. Issue: none. Depends on: none.
Audit floor A2, `astra_gate: None`, `user_merge: False`.
Source: KIX planner run 1793078707, loop-proposed node, not in
`.aiops/program.json`. Task input is the supervisor's node specification and
read-only design supplied in this session; there is no corresponding task
document under `docs/tasks/`. This is not an ASTRA program-mode session.

- Branch: `agent/kix-plan-ci-test-suite-discovery-guard`.
- Starting HEAD and observed cached `origin/main`:
  `9ed15a7adc93359e99bb5c3512a3ca20c77cb264`; starting worktree clean,
  no local base delta. The supervisor prohibits network actions, so
  `git fetch origin main` was not run, overriding AGENTS.md §1 step 1.
  Remote freshness is unverified. No rebase or base change occurred.
- Implementation head and exact final task head: not assigned; delivery is
  uncommitted changes above the starting HEAD. Supervisor owns git/GitHub.
- Merge commit and post-merge main CI run ID/status/conclusion: not applicable.
- Exact-head KTX kernel verification and KIX protocol verification run
  ID/status/conclusion: unavailable, not queried or claimed. Both must be
  completed/success on the eventual published head before merge readiness.

No commit, push, reset, PR, issue, comment, tag/branch mutation, network action,
background job, polling or automatic retry was performed.
READY describes this local builder delivery, not merge readiness or A2 review.

## Locks

`git hash-object` before and after work matches both required blobs:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

All 108 files under `reference/v0.3-rc1` match their `origin/main` Git blobs
byte-for-byte, with no extra files on disk. Final-merge verification is not
applicable; no merge took place.

## What this change does

Adds `scripts/check_ci_test_discovery.py`, a stdlib-only checker with a plain
mode and `--self-test`. It reads `.github/workflows/protocol.yml` as text and
fails unless every offline test suite in scope is reached by a workflow step:

- every `test_*.py` under each `reference/<dir>/`, recursively;
- every `reference/rights_scale/client/**/*.test.mjs` (`node_modules` skipped);
- every `test_*.py` module at any depth under `readiness/` and
  `integration_gate/`, with or without `__init__.py`.

A step reaches a suite through `node --test PATH`, `python -m unittest MODULE`
or `python -m unittest discover` (including the `for suite in ...; do ... done`
list, expanded per value). Discover follows Python 3.11+ rules: `test*.py`
directly under the start directory, then only package subdirectories. A
readiness/integration_gate module is also reached when a module CI runs binds
every one of its TestCase classes at top level through `from X import Cls` or
`*`. `import X` and `from pkg import test_mod` bind no TestCase class and do
not count; binding only some classes is reported as a partial import.

`reference/v0.1`, `reference/v0.2` and `reference/v0.3-rc1` are excluded by
name, each with a written reason. The guard does not claim they run. An empty
reason, an exclusion naming no test suite, or a workflow step reaching an
excluded tree all fail. The workflow naming a missing module or node test,
an unresolved `$` discover path, an unsupported unittest option and an empty
set of test-running steps also fail. Usage errors exit 2.

The plain run on this tree lists each suite with the step that reaches it:

- six reference suites. Five are reached by
  `protocol/Offline reference state machines and OpenAPI pins`, and
  `rights_scale` by `rights-scale/Rights-scale Move and model tests`;
- eight node tests, each reached by its own `rights-scale` step;
- four modules. `readiness.test_conformance_sensitivity` is reached
  `via readiness.test_faults`, which imports `ConformanceSensitivityTests`.

`--self-test` uses temporary fixture trees and synthetic workflow text only. A
positive baseline mirrors the current shapes, including a nested
`readiness/subpackage/test_deep.py` named on a unittest line. It then rejects
18 negative controls, each by its own error prefix:

- an unwired suite directory;
- an unwired `.test.mjs`;
- unreached top-level, nested and non-package modules;
- an exclusion without a reason;
- a module reached only by `import` or as a package attribute;
- a partial from-import;
- a reference test in a non-package subdirectory;
- a commented-out wiring line;
- an unexpanded loop variable;
- an unsupported discover option;
- a missing named module or node test;
- an absent excluded tree;
- an excluded tree wired by discover;
- an empty workflow.

Exactly two lines wire the checker into the existing `Stdlib offline document
checks` step, after `check_ci_checker_wiring.py --self-test` and before
`check_stage5_host.py --self-test`. No other workflow line, suite or test changes.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_ci_test_discovery.py` | New test-discovery guard and synthetic self-test. |
| `.github/workflows/protocol.yml` | Two added commands in the existing stdlib step. |
| `docs/README.md` | One validation index bullet and separating blank line. |
| `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md` | This execution record. |

## Existing coverage mapping

| Requirement | Coverage before this node | Evidence / addressed gap |
|---|---|---|
| Every offline reference suite, node test and readiness/integration_gate test module is reached by a protocol.yml step | Not covered | No checker compared the test tree with workflow steps. A new suite directory, `.test.mjs` or test module could be added without running in CI. The new guard and its negative controls address this. |
| Import-chain reach (`readiness.test_faults` → `test_conformance_sensitivity`) | Not covered | Previously only implicit in the module source. The guard now credits it explicitly and rejects `import`-only, package-attribute and partial imports. |
| New checker wired plain and `--self-test` | Sufficiently covered | Existing `check_ci_checker_wiring.py` plain/self-test; it now counts 32 scripts. |
| Validation record indexed | Sufficiently covered | Existing `check_docs_index.py` plain/self-test. |
| Credited suites actually pass | Sufficiently covered by existing CI steps | Re-run locally below as the closest protocol.yml equivalents; no test was added or changed. |
| Exact-head KTX and KIX CI acceptance | Not covered in this session | Supervisor must publish, obtain non-author review and verify eventual exact-head CI. |

## Commands and results

Commands were run from the repository root with Python 3.13.5 unless noted.
The full stdlib step was run one subprocess per workflow command, in workflow
order: 57 commands, all exit 0. They were followed by the OpenAPI and
integration-gate checker pairs and a CLI usage control.

| Command | Result |
|---|---|
| `python3 scripts/check_ci_test_discovery.py` | Exit 0. 18 `reached:` lines and three `excluded:` lines, then `ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3` |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0. `self-test: pass (18 negative controls)` |
| `python3 scripts/check_ci_test_discovery.py --bogus` | Exit 2. `usage: check_ci_test_discovery.py [--self-test]` |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_ci_test_discovery.py` (Python 3.12.15) | Exit 0. Same summary line |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_ci_test_discovery.py --self-test` (Python 3.12.15) | Exit 0. `self-test: pass (18 negative controls)` |
| In-memory mutation probe: `check()` on the real tree with four edited copies of the workflow text | Removing the HTTP-gate line gave three `unreached test module` errors: `test_http_gate`, `test_faults` and `test_conformance_sensitivity`. Removing `token_reward` from the loop gave 8 `unreached test file` errors. Removing the `zk-helpers` node line gave 1 `unreached node test` error. Removing the rights_scale discover gave 6 `unreached test file` errors. The workflow file on disk was not modified. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=385 ev_ids=15 original32=32` |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47` |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145` |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_docs_index.py` | Exit 0. `docs index ok: scanned=286 indexed=251 allowlisted=35` |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14` |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0. `delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6` |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. `rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0. `rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0. `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7` |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_contract_error_codes.py` | Exit 0. `contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0` |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8` |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0` |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. `readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9` |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0. `settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8` |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0. `self-test: pass (33 negative controls)` |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0. `bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2` |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0. `self-test: pass (50 negative controls)` |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0. `credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3` |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0. `self-test: pass (55 negative controls)` |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0. `primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5` |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0. `self-test: pass (76 negative controls)` |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0. `ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1` |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0. `self-test: pass (86 negative controls)` |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0. `lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK` |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0. `self-test: positive injected citation and 49 negative fixtures passed (memory only)` |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0. `contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK` |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0. `contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only)` |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0. `Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK` |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0. `Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only)` |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0. `BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17` |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0. `self-test: pass (2 positive controls, 50 negative fixtures)` |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0. `performance evidence map ok: Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3` |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0. `self-test: pass (2 positive controls, 66 negative fixtures; memory only)` |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0. `feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17` |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0. `self-test: pass (77 negative controls, injected positive control)` |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0. `integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1` |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0. `self-test: pass (85 negative controls; injected positive and valid status controls)` |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0. `evidence map roll-up ok: contracts=25; textual index only` |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0. `self-test: pass (16 negative controls)` |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0. `ci checker wiring ok: scripts=32 plain=31 self_test=32 self_test_only=1 docs=22 citations=99` |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0. `self-test: pass (13 negative controls)` |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass` |

Credited suites, re-run as the closest protocol.yml equivalents:

| Command | Result |
|---|---|
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. `Ran 100 tests`, `OK`. The `-v` output names `ConformanceSensitivityTests` 8 times, confirming the import chain runs it. |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0. `Ran 4 tests`, `OK` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. `Ran 196 tests`, `OK` |
| same for `reference/booking_resale_admission` | Exit 0. `Ran 418 tests`, `OK` |
| same for `reference/credit_advance_f04` | Exit 0. `Ran 148 tests`, `OK` |
| same for `reference/ai_delegation` | Exit 0. `Ran 85 tests`, `OK` |
| same for `reference/token_reward` | Exit 0. `Ran 168 tests`, `OK` |
| same for `reference/rights_scale` | Exit 0. `Ran 173 tests`, `OK` |
| `node --test reference/rights_scale/client/{zk-policy-v2,zk-helpers,ptau-header}.test.mjs` (existing local Node 24.19.0 on PATH) | Exit 0 each; tests 267/166/34, fail 0 |

The other five node tests run after `scripts/bootstrap.sh` in CI, which needs
npm dependencies. They were not run, because no network is used here.

## Other verification

| Command | Actual result |
|---|---|
| `git rev-parse HEAD origin/main` | Exit 0; both `9ed15a7adc93359e99bb5c3512a3ca20c77cb264`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before/after | Exit 0; both match the required hashes in Locks. |
| `git diff -U0 -- .github/workflows/protocol.yml` | Sole hunk `@@ -264,0 +265,2 @@ jobs:` adds only the plain and `--self-test` commands. |
| `git diff --numstat` | `2 0` for the workflow and for `docs/README.md`. The two new files are untracked. |
| `git diff --quiet origin/main -- runtime .aiops reference docs/tasks docs/contracts docs/decisions readiness integration_gate` | Exit 0; protected paths unchanged. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git status --short --untracked-files=all` | Two modified and two new files, exactly as listed in Changed paths. |
| `reference/v0.3-rc1` byte comparison: each `git ls-tree -r -z origin/main` entry compared with `git cat-file blob`, plus a check for extra files on disk | 108 files, 0 mismatches, 0 extra files. |

The `readiness.test_faults` run, like the CI step, ran without
`PYTHONDONTWRITEBYTECODE` and wrote a git-ignored
`reference/v0.3-rc1/__pycache__/`. That cache was deleted before the byte
comparison above, so the tree on disk matches `origin/main` exactly.

## CI classification note

The workflow and script changes are not documentation-only under the repository
classifiers, so the eventual hosted delivery requires full verification. The
new commands sit in the unguarded stdlib step, which runs on every non-draft
event. Local results are not exact-head CI and do not transfer older CI results
to a new head. The supervisor must record the eventual exact-head KTX and KIX
run IDs, statuses and conclusions outside a follow-up evidence-only commit
(§§10–11).

Cargo tests, Clippy, rustfmt, Move, ZK/localnet, SDK and the five
bootstrap-dependent node suites were not run, because no Rust, Move,
reference, SDK or client source changed.

## Contract findings

No explicit contract violation and no contract-undefined characterization was
found. No runtime behavior was exercised beyond re-running existing suites.

## Non-claims, residuals and deviations

- No grade, review, acceptance, production readiness, durability, distributed
  fencing, bank exactly-once or chain finality claim. No real funds,
  PG/bank/KYC calls, public endpoint, Sui testnet/mainnet, new coin/TIX module,
  R2, storage engine, secrets or production runtime was needed.
- A pass establishes textual reach only. The workflow is parsed as text, not as
  YAML or shell. `if:` guards are ignored, so docs-only and same-tree runs that
  skip the reference and HTTP-gate steps still count as reaching. Scripts that
  run tests internally (`scripts/verify_runtime.py`), npm `test:zk` scripts,
  Move, Rust and SDK tests are out of scope.
- Imports are resolved statically from top-level statements. `load_tests`,
  `__all__`, runtime `sys.path` changes and dotted `MODULE.Class` unittest
  arguments are not modelled; a dotted class argument is reported as a
  missing module, not credited. Discover start directories that differ from
  `-t` are not checked for importability.
- The guard does not judge whether test assertions are adequate. Its
  self-tests are builder-authored synthetic controls, not independent
  verification.
- Deviations from the design:
  - The import-chain closure follows TestCase class bindings, not every
    module edge. A helper module importing a test module therefore does not
    count as reaching it, and neither does `from pkg import test_mod`. This
    matches what unittest loads from a module namespace.
  - Two controls and one error were added: a missing named node test, a
    package-attribute import, and `workflow discover path missing`. The
    self-test therefore reports 18 negative controls, not 16.
  - The stdlib step has 57 commands, not the 51 the design estimated.
- Execution deviations: fetch/GitHub actions were omitted under the
  supervisor's explicit prohibition; exact-head CI and remote freshness remain
  unverified. No User decision was needed.
