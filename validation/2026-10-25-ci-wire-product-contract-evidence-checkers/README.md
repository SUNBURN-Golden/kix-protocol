# ci-wire-product-contract-evidence-checkers

Node: `plan-ci-wire-product-contract-evidence-checke`. Run the settlement,
BRA and credit F04 evidence-map checkers, plain and with `--self-test`, in
the unguarded `Stdlib offline document checks` step of
`.github/workflows/protocol.yml`. Issue: none. Depends on:
`plan-settlement-contract-clause-evidence-map` (#285),
`plan-bra-contract-clause-evidence-map` (#286), and
`plan-credit-f04-contract-clause-evidence-map` (#287), confirmed in the local
merge log. Audit floor A2. `astra_gate: None`, `user_merge: False`.
Not an ASTRA program-mode session. Source: KIX planner run 1792876090,
loop-proposed node, not in `.aiops/program.json`.

Task input is the supervisor's node specification and read-only design supplied
in the session; there is no node task document under `docs/tasks/`. No task
document was created or edited. The stage-5 wiring precedent is
`validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md`.

This is a local builder delivery, not merge-ready or independent A2 review.
The supervisor owns commits and GitHub publication. No commit, push, reset,
PR, issue, comment, tag/branch mutation, network action, background job,
polling or automatic retry was performed.

## Identity and base

- Branch: `agent/kix-plan-ci-wire-product-contract-evidence-checke`.
- Starting HEAD and observed cached `origin/main`:
  `c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f`. The starting worktree was clean;
  no local base delta. The supervisor explicitly prohibits network actions,
  so `git fetch origin main` was not run, overriding AGENTS.md §1 step 1.
  Remote freshness is unverified. No rebase or base change occurred.
- Implementation head and exact final task head: not assigned in this session;
  delivery consists of uncommitted changes above that starting HEAD.
- Merge commit and post-merge main CI: not applicable; no merge performed.
- Exact-head KTX kernel verification and KIX protocol verification:
  run ID/status/conclusion unavailable; not queried or claimed. Both must be
  completed/success on the supervisor's eventual PR head before merge readiness.

## Locks

Both `git hash-object` observations, before and after work, match:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`reference/v0.3-rc1/**` is byte-identical to the base (verified against Git
blobs, not just a timestamp-based diff). No `runtime/`, `.aiops/`,
`docs/tasks/`, checker, map, contract or historical validation file changed.
Final-merge blob verification is not applicable.

## What this change does

Adds exactly six commands after `check_readiness_evidence_map.py --self-test`
and before `check_stage5_host.py --self-test` in the existing stdlib step.
No comment, guard, job or other workflow step changes. The step has no `if:`
and therefore inherits only its job's draft skip; by construction these checks
also run on docs-only and same-tree-skip executions. No hosted execution was
observed. The stage-5 evaluator stays self-test-only.

The capability register's 검증·handoff sentence adds the three checker names
and their plain/`--self-test` invocations. Its `c7b470fc…` observation,
thirteen-checker list, stage-5 exception, authoritative-workflow/manual-drift
caveat and error-code note are preserved. No 위치 동기화 line was added.
The docs index gains one bullet for this record, without an allowlist change.
No grade, value, owner or UNDETERMINED/OPEN term changes.

## Changed paths

| Path | Change |
|---|---|
| `.github/workflows/protocol.yml` | Six added run lines, solely within the stdlib step. |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | Extend the handoff checker sentence. |
| `docs/README.md` | One validation index bullet and separating blank line. |
| `validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md` | This validation record. |

## Existing coverage mapping

| Requirement | Before this node | Evidence / gap addressed |
|---|---|---|
| Settlement map structure/citations and negative controls | Sufficiently covered locally; not covered in CI | `scripts/check_settlement_evidence_map.py` plain and `--self-test`, recorded in `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md`; six-line wiring fills the CI-execution gap. |
| BRA map structure/citations and negative controls | Sufficiently covered locally; not covered in CI | `scripts/check_bra_evidence_map.py` plain and `--self-test`, recorded in `validation/2026-10-25-bra-contract-clause-evidence-map/README.md`; wiring fills the CI-execution gap. |
| Credit F04 map structure/citations and negative controls | Sufficiently covered locally; not covered in CI | `scripts/check_credit_evidence_map.py` plain and `--self-test`, recorded in `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md`; wiring fills the CI-execution gap. |
| Register paths and validation index | Sufficiently covered by existing checkers | `scripts/check_status_register.py` and `scripts/check_docs_index.py`, each plain and `--self-test`; rerun against this delivery. |
| Docs-only and same-tree-skip execution | Partially covered: structural only | Parsed step has no `if:`; no hosted run observed. |
| Exact-head KIX and KTX acceptance | Not covered in this builder session | Supervisor must publish and verify both workflows on the final PR head. |

No tests were added: the existing deterministic self-tests cover the wiring
inputs; this node adds execution wiring, not checker semantics or duplicate
assertions. The checkers establish document structure and named-test existence,
not semantic adequacy or independent review.

## Commands and results

Repository root; `python3` is Python 3.13.5. The initial narrow run executed the
six product checker invocations separately, before edits: all exit 0, with
settlement/BRA/credit self-tests ending in `self-test: pass (31 negative controls)`,
`self-test: pass (50 negative controls)` and `self-test: pass (55 negative controls)`.
The full step was then run in workflow order, one subprocess per command.
The following table records actual exit codes and verbatim final summary lines.

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=367 ev_ids=15 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0. `docs index ok: scanned=239 indexed=204 allowlisted=35`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0. `delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6`. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. `rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0. `rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2`. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0. `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7`. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0. `contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0`. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8`. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0`. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. `readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0. `settlement evidence map ok: rows=27 headings=27 citations=106 COVERED=12 PARTIAL=5 NOT_COVERED=2 OPEN=8`. |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0. `self-test: pass (31 negative controls)`. |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0. `bra evidence map ok: rows=39 headings=39 items=9 citations=212 COVERED=21 PARTIAL=15 NOT_COVERED=1 OPEN=2`. |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0. `self-test: pass (50 negative controls)`. |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0. `credit evidence map ok: rows=22 headings=22 items=5 citations=127 COVERED=13 PARTIAL=5 NOT_COVERED=1 OPEN=3`. |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0. `self-test: pass (55 negative controls)`. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0. `self-test: pass`. |

## Other verification

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main` | Exit 0; both `c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f`. |
| `python3 --version` | Exit 0; `Python 3.13.5`. |
| `python3 scripts/check_docs_index.py (before edits)` | Exit 0; `docs index ok: scanned=238 indexed=203 allowlisted=35`. |
| `/workspace/venvs/film312/bin/python3 /tmp/validate_kix_product_wiring.py --verify-only (PyYAML BaseLoader)` | Exit 0; Python 3.12.15, PyYAML 6.0.3; both workflows parse; 33 commands; no step `if:`; only the specified run-block change; stage-5 self-test stays last. |
| `git diff -U0 -- .github/workflows/protocol.yml` | Exit 0; one hunk `@@ -236,0 +237,6 @@ jobs:`, exactly six additions and no removals/comments. |
| `git diff --numstat -- .github/workflows/protocol.yml` | Exit 0; `6 0 .github/workflows/protocol.yml`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs (before/after)` | Exit 0; both required blobs match before and after (see Locks). |
| `git diff --quiet origin/main -- runtime .aiops reference/v0.3-rc1 docs/tasks scripts docs/contracts docs/decisions docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md docs/status/BRA_CONTRACT_EVIDENCE_MAP.md docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md` | Exit 0; no protected-path diff. |
| `/workspace/venvs/film312/bin/python3 /tmp/validate_kix_product_wiring.py --verify-only (reference byte comparison)` | Exit 0; all 108 tracked reference/v0.3-rc1 files match origin/main Git blobs byte for byte. |
| `git diff --check` | Exit 0; clean. |
| `git status --short --untracked-files=all` | Exit 0; exactly three modified files and one new validation record, matching Changed paths. |
| `/workspace/venvs/film312/bin/python3 /tmp/validate_kix_product_wiring.py (initial full run)` | Exit 1 only at the temporary runner status assertion: its strip() removed the first status line’s leading space. All 33 checker subprocesses exited 0 before that assertion. Fixed only the /tmp runner; --verify-only rechecked structure/preservation using the captured checker results without rerunning them. |

After rendering the full record, `python3 scripts/check_status_register.py`
and `python3 scripts/check_docs_index.py` were each rerun plain and with
`--self-test`: all four exited 0 with the same summary lines above.
`python3 /tmp/write_kix_product_record.py` rendered the captured results
and exited 0. The final whitespace/status and preservation checks also
passed after the evidence record was filled.

The temporary validation runner and JSON results live under `/tmp/` only; they
are not delivery files or runtime dependencies. Source inspection used `cat`,
`sed`, `rg`, `wc`, `ls` and local Git reads on governance, development plan,
baselines, authority model, task index, the named evidence maps and records,
checker sources and both workflow definitions. These reads are not extra test
claims. No source or test logic changed, so Rust/Cargo/Clippy/format checks and
reference runtime suites were not run; the full stdlib step is the closest local
CI equivalent for the touched paths. Move/ZK/SDK/HTTP/backend execution was not run.

## CI classification note

`.github/workflows/protocol.yml` is a non-documentation path under both workflow
classifiers, so this delivery is not docs-only and calls for full hosted
verification after publication. The classifiers were inspected, not executed.
The stdlib step remains unguarded. Local passes are not exact-head CI. Per
AGENTS.md §§10–11, the supervisor must record the eventual exact-head KIX and KTX
run IDs/statuses/conclusions in the PR report rather than another commit solely
to record CI for a preceding head.

## Contract findings

No new explicit contract violation or contract-undefined characterization was
found in this wiring change. Existing map gaps and OPEN/UNDETERMINED items retain
their recorded labels and owners; no runtime behavior was exercised or reclassified.

## Non-claims, residuals and deviations

- No evidence grade, acceptance, legal/accounting treatment, production readiness,
  durability, distributed fencing, bank exactly-once or chain finality claim.
  No real funds, PG/bank/KYC calls, public endpoint, Sui testnet/mainnet, new coin/TIX
  module, R2, storage engine, secrets or production runtime was needed or introduced.
- The three checker docstrings retain their local-only/no-workflow-change wording.
  The settlement map's line 106, BRA map's line 131 and credit map's line 122
  still describe local-only/not-wired status at their preceding snapshots.
  This is known stale wording after this node; the explicit no-checker/no-map-change
  boundary leaves it for a later sync node. Historical validation records are intact.
- The register's checker list remains manual and may drift. Older validation
  records' workflow line numbers also drift; this step now occupies lines 203–243.
- Later citation or structural drift in these three maps now fails the stdlib CI
  step by design. This does not prove adequacy of the cited test assertions.
- The only execution deviations are the explicitly prohibited fetch/GitHub actions
  and consequent absence of exact-head CI evidence; no implementation-plan deviation.
  READY means ready for supervisor handling of this local delivery, not merge-ready.
