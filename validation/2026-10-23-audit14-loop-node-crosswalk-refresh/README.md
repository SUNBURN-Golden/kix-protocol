# audit14 loop-node crosswalk refresh

Node: `audit14-audit14-loop-node-crosswalk-refresh`. Source: KIX audit #14
(`/workspace/kix-run/audits/audit_14_20261023.md`), finding 4, and the supervisor's
supplied node specification and read-only design plan. Issue: none. Depends on:
none. Audit floor A2; Astra gate: None; user_merge: False. Not ASTRA program mode.
No node-specific task file exists under `docs/tasks/`; none was created or edited.
The requested October 23 record path is retained; this builder session ran on
2026-10-24. Builder-authored documentary evidence, not non-author review.

## Identity and bases

- Historical crosswalk basis: `85acc3399a23e87ee4092693840c4e0a620867a0` (#209).
- Refresh cutoff: `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` (#269).
- Program Git blob at both bases: `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`.
  Parsed with `json.loads`; canonical definitions are `nodes[].id`, `spec`,
  and optional `depends_on` (omission means none; declared order retained).
- Starting branch: `agent/kix-audit14-audit14-loop-node-crosswalk-refresh`.
  Starting HEAD/base and locally observed `origin/main`:
  `08ced25441171b2423e6399f04dae14ca0a0a3f8` (#271); initial worktree clean.
  Delta from cutoff: two first-parent merges, #270
  `2d2e93eb14fe41bafaf2dbaa91f02d861c8be8b5` and #271
  `08ced25441171b2423e6399f04dae14ca0a0a3f8`.
  These are excluded from the refreshed evidence, with no rebase or base change.
- `git fetch origin main`: NOT_RUN under the supervisor's explicit no-network
  rule, which overrides AGENTS §1. Remote freshness remains unverified.
- Implementation/final task head: unassigned; uncommitted patch over the starting
  HEAD. No commit, push, PR, issue, comment, branch/tag change or merge performed.
  Merge SHA / final-merge lock checks / post-merge CI: not applicable.
- Exact-head KTX kernel verification and KIX protocol verification: run IDs,
  statuses and conclusions unavailable, NOT_RUN / not queried. Local READY is
  supervisor handoff only; exact-head CI and non-author review remain pending.

## Changed paths

- `docs/status/LOOP_NODE_CROSSWALK.md`
- `validation/2026-10-23-audit14-loop-node-crosswalk-refresh/README.md`
- `docs/README.md`

The original basis, 18 rows, historical range observations and entire §3 paragraph
remain byte-identical. Added: dated #269 basis; 30 rows; individual accounting
for 27 excluded merges and three absent PR numbers; #267 historical clarification;
one exact-file docs-index pointer. No canonical status or count was changed.

## Existing coverage and gaps (AGENTS §7)

| Requirement | Existing coverage | Evidence used here |
|---|---|---|
| Validation indexing and link targets | Sufficiently covered: `scripts/check_docs_index.py` plain and `--self-test` | Reused unchanged |
| Original crosswalk selection and citations | Partially covered: 18 historical rows and `validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md` | Preserve historical bytes, extend from pinned records |
| New selection, PR/SHA, normalized spec fragments, dependency order and exact branch observations | Not covered by an existing repository checker | Inline standard-library assertions below |
| Exhaustive range accounting / preservation | Not covered for this refresh | Bounded merge inventory, complete cutoff-record scan and before/after byte assertions |

No new persistent test, helper, checker or CI configuration was added. The inline
checks close documentary gaps only; they do not rerun or promote source tests
cited by historical records.

## Selection ledger at #269

Whitespace is normalized with `" ".join(text.split())`. The exact literal
selection quotation is given for each selected record. All 47 literal matches
in the complete cutoff tree comprise the 18 historical records and 29 new ones.
#264 adds the sole equivalent explicit statement, quoted in full below; there
are 48 rows total. The 57 actual range merges partition into 30 rows and 27
exclusions. No corresponding validation record exists for #219, #230, #237,
#238, #260 or #266. The absence of records was checked in the complete cutoff
tree, alongside each merge's changed paths and its node identity; source files
or later sibling records do not replace a missing record.

#210 is selected by its literal quotation even though the record is an audit
crosswalk. #260/#261 are individually excluded for missing record/statement,
without an audit exemption. #267 is selected from its resumed record at #269,
regardless of its October 17 directory date. No historical finding is relabelled
as a new current defect. PR order follows Git first-parent merge order (so #236
follows #238); absent numbers are not assumed merged.

| PR | Record at #269 | Disposition / exact selection quotation |
|---|---|---|
| #210 | `validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md` | ROW — “not in `.aiops/program.json`” |
| #211 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md` | ROW — “not in `.aiops/program.json`” |
| #212 | `validation/2026-10-17-delegated-exec-seeded-differential/README.md` | ROW — “not in `.aiops/program.json`” |
| #213 | `validation/2026-10-17-rs-im-evidence-map/README.md` | ROW — “not in `.aiops/program.json`” |
| #214 | `validation/2026-10-18-contract-error-code-coverage/README.md` | NO ROW — no explicit canonical-program absence statement |
| #215 | `validation/2026-10-18-readiness-crash-point-sweep/README.md` | NO ROW — no explicit canonical-program absence statement |
| #216 | `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md` | ROW — “not in `.aiops/program.json`” |
| #217 | `validation/2026-10-19-rs-model-gap-closure/README.md` | ROW — “not in `.aiops/program.json`” |
| #218 | `validation/2026-10-19-tl-predicate-evidence-map/README.md` | NO ROW — no explicit canonical-program absence statement |
| #219 | `none` | NO ROW — no corresponding validation record |
| #220 | `validation/2026-10-19-bra-fsm-error-code-coverage/README.md` | NO ROW — no explicit canonical-program absence statement |
| #221 | `validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md` | ROW — “not in `.aiops/program.json`” |
| #222 | `validation/2026-10-20-plan-register-index-sync-20261020/README.md` | NO ROW — no explicit canonical-program absence statement |
| #223 | `validation/2026-10-20-adapter-identity-evidence-map/README.md` | ROW — “not in `.aiops/program.json`” |
| #224 | `validation/2026-10-20-token-reward-readiness-wrap/README.md` | ROW — “not in `.aiops/program.json`” |
| #225 | `validation/2026-10-20-v5-transition-evidence-map/README.md` | ROW — “not in `.aiops/program.json`” |
| #226 | `validation/2026-10-20-ai-delegation-wrap-conformance/README.md` | NO ROW — no explicit canonical-program absence statement |
| #227 | `validation/2026-10-20-stage5-preflight/README.md` | ROW — “not in `.aiops/program.json`” |
| #228 | `validation/2026-10-20-token-reward-rejection-atomicity/README.md` | ROW — “not in `.aiops/program.json`” |
| #229 | `validation/2026-10-20-read-model-contract-fixture-prep/README.md` | ROW — “not in `.aiops/program.json`” |
| #230 | `none` | NO ROW — no corresponding validation record |
| #231 | `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md` | ROW — “not in `.aiops/program.json`” |
| #232 | `validation/2026-10-21-plan-register-index-sync-20261021/README.md` | NO ROW — no explicit canonical-program absence statement |
| #233 | `validation/2026-10-21-reward-wrap-conformance/README.md` | NO ROW — no explicit canonical-program absence statement |
| #234 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md` | ROW — “not in `.aiops/program.json`” |
| #235 | `validation/2026-10-21-kix-types-boundary-fixtures/README.md` | ROW — “not in `.aiops/program.json`” |
| #237 | `none` | NO ROW — no corresponding validation record |
| #238 | `none` | NO ROW — no corresponding validation record |
| #236 | `validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md` | ROW — “not in `.aiops/program.json`” |
| #239 | `validation/2026-10-21-readiness-checker-partial-fixture/README.md` | ROW — “not in `.aiops/program.json`” |
| #240 | `validation/2026-10-21-plan-rs-witness-offline-regressions/README.md` | NO ROW — no explicit canonical-program absence statement |
| #241 | `validation/2026-10-21-plan-rs-witness-ci-wiring/README.md` | NO ROW — no explicit canonical-program absence statement |
| #242 | `validation/2026-10-21-plan-rs-manifest-offline-regressions/README.md` | NO ROW — no explicit canonical-program absence statement |
| #243 | `validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md` | NO ROW — no explicit canonical-program absence statement |
| #245 | `validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md` | NO ROW — no explicit canonical-program absence statement |
| #246 | `validation/2026-10-21-plan-rs-ptau-header-tests/README.md` | NO ROW — no explicit canonical-program absence statement |
| #247 | `validation/2026-10-21-v5-evidence-citation-guard/README.md` | ROW — “not in `.aiops/program.json`” |
| #248 | `validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md` | ROW — “not in `.aiops/program.json`” |
| #251 | `validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md` | NO ROW — no explicit canonical-program absence statement |
| #252 | `validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md` | NO ROW — no explicit canonical-program absence statement |
| #253 | `validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md` | NO ROW — no explicit canonical-program absence statement |
| #254 | `validation/2026-10-22-plan-register-index-sync-20261022/README.md` | NO ROW — no explicit canonical-program absence statement |
| #255 | `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md` | ROW — “not in `.aiops/program.json`” |
| #256 | `validation/2026-10-22-rs4-load-host-conditions-recorder/README.md` | ROW — “not in `.aiops/program.json`” |
| #257 | `validation/2026-10-22-rs-offline-suite-evidence-sync/README.md` | ROW — “not in `.aiops/program.json`” |
| #258 | `validation/2026-10-22-open-user-decisions-ledger/README.md` | ROW — “not in `.aiops/program.json`” |
| #259 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md` | ROW — “not in `.aiops/program.json`” |
| #260 | `none` | NO ROW — no corresponding validation record |
| #261 | `validation/2026-10-23-plan-register-index-sync-20261023/README.md` | NO ROW — no explicit canonical-program absence statement |
| #262 | `validation/2026-10-23-plan-rs-summary-arithmetic-tests/README.md` | ROW — “not in `.aiops/program.json`” |
| #263 | `validation/2026-10-23-plan-readiness-migration-edge-tests/README.md` | ROW — “not in `.aiops/program.json`” |
| #264 | `validation/2026-10-23-owner-stop-handoff-addendum/README.md` | ROW — “Loop-proposed, absent from `.aiops/program.json`” |
| #265 | `validation/2026-10-23-fsm-returned-data-isolation/README.md` | ROW — “not in `.aiops/program.json`” |
| #266 | `none` | NO ROW — no corresponding validation record |
| #267 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md` | ROW — “not in `.aiops/program.json`” |
| #268 | `validation/2026-10-23-readiness-receipt-audit-tests/README.md` | NO ROW — no explicit canonical-program absence statement |
| #269 | `validation/2026-10-23-bra-section9-error-code-coverage/README.md` | NO ROW — no explicit canonical-program absence statement |
| #244 | n/a | ABSENT — no first-parent merge in bounded history |
| #249 | n/a | ABSENT — no first-parent merge in bounded history |
| #250 | n/a | ABSENT — no first-parent merge in bounded history |

## Overlap and dependency interpretation

The 34 new spec quotations (58 including historical rows) are normalized
substrings of the named `spec` at the pinned blob. Selection is independent
of overlap: ten selected rows use the existing fallback `none identified by
the builder` / `n/a` (#210, #227, #236, #239, #247, #248, #255, #256, #258,
#264). These are the crosswalk itself, preflight/host metadata, decision/owner
sheets, checker self-tests/citation guards or a test entry point; no honest
matching canonical deliverable phrase was identified. This is not a claim
that no broader relationship could ever be found.

For the mapped rows, seeded/rejection/first-result tests share the corresponding
`k-adversarial-corpus` predicate, while artifact-specific tests name their mock,
crate or reference domain. Evidence maps share `k-current-capability-map`'s
“요구별 source와 검증 gap 표” artifact. #224 maps the new FSM wrap to
`readiness-extensions`; #229's candidate fixtures share only the nonmutation
predicate with `read-model-reference`. In particular, they are not approved
query implementation or conformance. #262 maps minimal summary regression
cases to the adversarial gap predicate; synthetic arithmetic is not RS load
measurement. These are bounded builder readings, not exhaustive mappings or
canonical completion/acceptance claims.

Dependencies come from each named canonical node's JSON definition, in declared
order, not from its loop record. Missing lists are none. “Merged” requires the
full `agent/kix-<id>` branch in first-parent history **through #269**. In
particular, no inference from a `plan-*` branch is made. The inline check builds
the expected dependency cell from the JSON and Git and compares every character,
including PR and full SHA. Merge subjects without the standard branch suffix
(e.g. historical #81) supply no exact branch match. History observations do not
identify the GitHub merger or establish node acceptance.

## Preservation and locks

| Protected content | Before / after result |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, matches before and after |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20`, matches before and after |
| `HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; all 108 tracked files and the on-disk file set match starting HEAD |
| All tracked paths outside the three-path allowlist | Raw Git-blob comparison matches starting HEAD; index unchanged |
| Historical crosswalk | Removing only the additions restores the complete original bytes; all 18 rows and entire §3 preserved |

No protected content was modified, including transient edits. `.aiops/`,
`docs/tasks/`, contracts, runtime, reference sources and CI are unchanged.

## Commands and actual results

Read-only source discovery included `README.md`, `docs/DEVELOPMENT_PLAN.md`,
`docs/status/BASELINES.md`, `docs/decisions/AUTHORITY_MODEL_1.md`, `AGENTS.md`,
control-plane pointer/client, program decisions §5, the audit source, crosswalk,
pinned validation records and both workflow definitions. No current node task
file was found under `docs/tasks/`; the supplied task specification is the input.

Narrow checks ran before the broader batch, after the three delivery paths
existed. Every workflow command below was extracted from the actual unguarded
`Stdlib offline document checks` run block in `.github/workflows/protocol.yml`
and executed verbatim in order by `python3 -B /tmp/run-crosswalk-doc-ci.py`.
The wrapper asserts 27 invocations, runs each via `subprocess.run` in the
foreground, stops on nonzero exit and stores actual stdout/exit codes in
`/tmp/crosswalk-doc-ci-results.json`. Self-test summaries report successful
synthetic fault detection, not defects in this working tree.

| Command | Actual result |
|---|---|
| `python3 -B scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=219 indexed=184 allowlisted=35 |
| `python3 -B scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=347 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=219 indexed=184 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=173 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=197 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
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
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Other executed provenance and preservation commands:

| Command | Actual result |
|---|---|
| `pwd`, `git status --short`, `git branch --show-current` | Exit 0; supplied worktree/branch; initial worktree clean |
| `git rev-parse HEAD origin/main` | Exit 0; both starting SHA `08ced25441171b2423e6399f04dae14ca0a0a3f8` |
| `git rev-parse c7b470f^{commit} c7b470f:.aiops/program.json` | Exit 0; full cutoff and program blob as recorded above |
| `git log --first-parent --merges --reverse --format='%H %s' 85acc3399a23e87ee4092693840c4e0a620867a0..c7b470f` | Exit 0; 57 merges #210–#269, three absent numbers |
| `git log --first-parent --format='%H %s' c7b470f..HEAD` | Exit 0; only #270 and #271 beyond cutoff |
| Inline Python inventory using `git diff --name-only <merge>^1 <merge> -- validation` and `git show c7b470f:<record>` | Exit 0; 29 literal range records plus #264 equivalent; 27 excluded merges |
| Full cutoff scan using `git ls-tree -r --name-only c7b470f -- validation` and `git show` per README | Exit 0; 47 literal records, 18 historical + 29 new; #264 equivalent separately inspected |
| `git log --first-parent --merges --format='%H %s' c7b470f` | Exit 0; bounded dependency branch-name evidence read |
| `python3 -B /tmp/crosswalk-verify.py` | Initial exit 1: assertion assumed every historical merge used a branch-style subject; #81 does not. Corrected parser supplies no exact branch match for such subjects. Subsequent runs exit 0; final summary below |
| `python3 -B /tmp/run-crosswalk-doc-ci.py` | Exit 0; all 27 commands above passed |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before and after; both required hashes match |
| `git rev-parse HEAD:reference/v0.3-rc1` | Exit 0; reference tree ID above |
| `git diff --exit-code 08ced25441171b2423e6399f04dae14ca0a0a3f8 -- runtime/ reference/v0.3-rc1/ .aiops/ docs/tasks/ .github/` | Exit 0; no protected-path diff |
| `git diff --check` | Exit 0; no whitespace errors |
| Inline final-results JSON inspection (`len(results)==27` and all exits zero) | Initial exit 1: read the partial result file before the foreground batch finished. After waiting for terminal exit 0, rerun exited 0 with all 27 results |
| `git diff --name-status 08ced25441171b2423e6399f04dae14ca0a0a3f8`, `git ls-files --others --exclude-standard` | Exit 0; two modified docs and one untracked new record, exactly the three authorized paths |
| Read-only discovery `cat validation/2026-10-17-audit8-loop-node-canonical-crosswalk/README.md` | Exit 1; assumed date path absent. Read correct `validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md` from cutoff instead |
| Read-only discovery `rg` including `.github/workflows/ktx.yml` | Exit 2; assumed filename absent. Inspected actual `.github/workflows/ktx-kernel.yml` instead |

No repository checker failed. One temporary assertion-parser correction, one
premature result-file inspection and two missing-path discovery probes required
no repository code or CI change. The completed final 27-command batch passed;
the recorded inline acceptance block and narrow index checks were also rerun
after documentation assembly.

## Reproducible inline acceptance and preservation check

Run from the repository root before supervisor commit/publication. This is the
exact standard-library verification body executed as
`python3 -B /tmp/crosswalk-verify.py` (also executable inline as below), not a new
repository checker. It checks selection against the pinned complete cutoff
record set and merge inventory, ledger quotations/identities, all spec phrases,
new dependency cells, individual range accounting and protected bytes.
Human assessment of honestly overlapping artifacts and equivalent statements
remains a builder reading; substring membership alone proves neither.

```bash
python3 -B - <<'PY'
import hashlib,json,re,subprocess
from pathlib import Path
START='08ced25441171b2423e6399f04dae14ca0a0a3f8'
OLD='85acc3399a23e87ee4092693840c4e0a620867a0'
CUT='c7b470fc39ad6f6aa6ad59c18b5595cde41a7200'
BLOB='ff0f39a8129ca8b8d30818cce35c3d4e588872fc'
CROSS='docs/status/LOOP_NODE_CROSSWALK.md'
RECORD='validation/2026-10-23-audit14-loop-node-crosswalk-refresh/README.md'
allowed={CROSS,RECORD,'docs/README.md'}
def git(*args):
    return subprocess.check_output(['git',*args],text=True)
def norm(text):
    return ' '.join(text.split())
def table(text):
    return [[c.strip() for c in line.strip('|').split('|')]
            for line in text.splitlines() if re.match(r'^\| #\d+ \|',line)]
assert git('rev-parse','HEAD').strip()==START
assert git('rev-parse','origin/main').strip()==START
assert git('branch','--show-current').strip()=='agent/kix-audit14-audit14-loop-node-crosswalk-refresh'
assert git('rev-parse',CUT+':.aiops/program.json').strip()==BLOB
assert git('rev-parse',OLD+':.aiops/program.json').strip()==BLOB
nodes={n['id']:n for n in json.loads(git('show',BLOB))['nodes']}
history=[]
for line in git('log','--first-parent','--merges','--format=%H %s',CUT).splitlines():
    m=re.fullmatch(r'([0-9a-f]{40}) Merge pull request #(\d+) from [^/]+/(.+)',line)
    if not m:
        continue  # A non-branch merge subject proves no exact branch match.
    sha,pr,branch=m.groups()
    history.append((int(pr),sha,branch))
by_pr={pr:(sha,branch) for pr,sha,branch in history}
bounded=[]
for line in git('log','--first-parent','--merges','--reverse','--format=%H %s',OLD+'..'+CUT).splitlines():
    bounded.append(int(re.search(r'#(\d+)',line)[1]))
assert len(bounded)==len(set(bounded))==57
assert set(range(210,270))-set(bounded)=={244,249,250}
paths=[p for p in git('ls-tree','-r','--name-only',CUT,'--','validation').splitlines()
       if re.fullmatch(r'validation/[^/]+/README.md',p)]
records={p:norm(git('show',CUT+':'+p)) for p in paths}
literal={p for p,t in records.items() if 'not in `.aiops/program.json`' in t}
equivalent='validation/2026-10-23-owner-stop-handoff-addendum/README.md'
assert 'Loop-proposed, absent from `.aiops/program.json`' in records[equivalent]
assert equivalent not in literal
assert len(literal)==47
selected=literal|{equivalent}
text=Path(CROSS).read_text()
section1=text.split('## 1. Crosswalk\n',1)[1].split('## 2. Range accounting',1)[0]
rows=table(section1)
assert len(rows)==48
new={int(r[0][1:]):r for r in rows if int(r[0][1:])>=210}
assert len(new)==30
ledger_text=Path(RECORD).read_text().split('## Selection ledger at #269\n',1)[1].split('\n## ',1)[0]
ledger=table(ledger_text)
assert len(ledger)==60
assert len({r[0] for r in ledger})==60
assert {int(r[0][1:]) for r in ledger}==set(range(210,270))
record_for={}
for pr_cell,path_cell,disposition in ledger:
    pr=int(pr_cell[1:]);p=path_cell.strip('`')
    if pr not in by_pr:
        assert p=='n/a' and disposition.startswith('ABSENT')
        continue
    sha,branch=by_pr[pr]
    touched={p for p in git('diff','--name-only',sha+'^1',sha,'--','validation').splitlines()
             if re.fullmatch(r'validation/[^/]+/README.md',p)}
    if p=='none':
        assert not touched and disposition.startswith('NO ROW')
        assert pr not in new
        continue
    assert touched=={p} and p in records
    record_for[pr]=p
    if p in selected:
        assert disposition.startswith('ROW') and pr in new
        quote=re.search('“(.+)”',disposition)[1]
        assert quote in records[p]
        node=re.search(r'Node:?\s+`([^`]+)`',records[p])[1]
        assert new[pr][2]=='`'+node+'`'
    else:
        assert disposition.startswith('NO ROW') and pr not in new
assert set(new)=={pr for pr,p in record_for.items() if p in selected}
assert len({p for p in record_for.values() if p in literal})==29
assert len(selected-{p for pr,p in record_for.items() if pr in new})==18
# The exact source-derived dependency text enforces order and every citation.
def dependency_cell(node):
    deps=nodes[node].get('depends_on',[])
    observations=[]
    for dep in deps:
        branch='agent/kix-'+dep
        matches=[(pr,sha) for pr,sha,b in history if b==branch]
        if matches:
            assert len(matches)==1
            pr,sha=matches[0]
            observation=f'merged: branch `{branch}` at #{pr} `{sha}`'
        else:
            observation=f'not determinable from this tree: no first-parent merge of branch `{branch}`'
        observations.append(f'`{dep}` ({observation})')
    return f'`{node}` depends_on '+('; '.join(observations) if deps else 'none')
all_quote_count=0
for row in rows:
    for node,quote in re.findall(r'`([^`]+)`: "([^"]+)"',row[3]):
        assert norm(quote) in norm(nodes[node]['spec'])
        all_quote_count+=1
quote_count=0
for pr,row in new.items():
    assert len(row)==6 and row[1]=='`'+by_pr[pr][0]+'`'
    assert row[5]=='does not complete or start the canonical node'
    if row[3]=='none identified by the builder':
        assert row[4]=='n/a'
        continue
    pairs=re.findall(r'`([^`]+)`: "([^"]+)"',row[3])
    assert '; '.join(f'`{n}`: "{q}"' for n,q in pairs)==row[3]
    for node,quote in pairs:
        assert norm(quote) in norm(nodes[node]['spec']),(pr,node,quote)
        quote_count+=1
    assert row[4]=='; '.join(dependency_cell(n) for n,q in pairs)
# All actual excluded merges and all absent numbers have unique accounting rows.
account=text.split('### Refresh accounting —',1)[1].split('## 3. Open decision',1)[0]
account_rows=table(account)
assert len(account_rows)==30
assert {int(r[0][1:]) for r in account_rows}==set(range(210,270))-set(new)
for pr_cell,seen,reason in account_rows:
    pr=int(pr_cell[1:]);assert reason
    if pr in by_pr:assert by_pr[pr][0] in seen
    else:assert 'No first-parent merge' in seen
# Removing only the additions restores the exact original crosswalk.
restored=re.sub(r'### Refresh recorded .*?(?=## 1\. Crosswalk\n)','',text,flags=re.S)
restored=re.sub(r'### Refresh accounting .*?(?=## 3\. Open decision\n)','',restored,flags=re.S)
restored=''.join(line for line in restored.splitlines(keepends=True)
                 if not re.match(r'^\| #(2[1-6][0-9]) \|',line))
assert restored==git('show',START+':'+CROSS)
original=git('show',START+':'+CROSS)
assert text.split('## 3. Open decision\n')[1].split('## 4.')[0]==original.split('## 3. Open decision\n')[1].split('## 4.')[0]
idx=Path('docs/README.md').read_text()
assert idx.count('](../'+RECORD+')')==1
# All tracked paths outside the allowlist, including 108 protected reference
# files, are compared to raw HEAD blobs; no Git index mutation is performed.
entries=subprocess.check_output(['git','ls-tree','-rz','--full-tree',START]).split(b'\0')
ref_count=0
for entry in filter(None,entries):
    meta,path=entry.split(b'\t',1);mode,kind,oid=meta.split();p=path.decode()
    if p in allowed:continue
    assert kind==b'blob',p
    f=Path(p)
    data=(str(f.readlink()).encode() if mode==b'120000' else f.read_bytes())
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert actual==oid.decode(),p
    ref_count+=p.startswith('reference/v0.3-rc1/')
assert ref_count==108
tracked_ref=set(git('-c','core.quotePath=false','ls-files','reference/v0.3-rc1').splitlines())
assert tracked_ref=={str(p) for p in Path('reference/v0.3-rc1').rglob('*') if p.is_file()}
locks={'runtime/crates/kix-kernel/src/lib.rs':'69564b166f0c27f9af5d8422f0a466b18d74c20f',
       'runtime/crates/kix-kernel/tests/quarantine_capacity.rs':'b607996c83a119c349f1cc90469ac1ba82764e20'}
for path,expected in locks.items():assert git('hash-object',path).strip()==expected
changed=set(git('diff','--name-only',START).splitlines())
untracked=set(git('ls-files','--others','--exclude-standard').splitlines())
assert changed|untracked==allowed
assert not git('diff','--cached','--name-only')
assert not git('diff','--name-only',START,'--','runtime/','reference/v0.3-rc1/','.aiops/','docs/tasks/','.github/')
assert git('rev-parse','HEAD:reference/v0.3-rc1').strip()=='a6ecb124dc2b2267ca6be19e39fbe2aef143074b'
print(f'PASS: 57 merges; 30 new / 48 total rows; 27 excluded merges; 3 absent PRs; {quote_count} new / {all_quote_count} total spec quotations; dependency lists/citations; historical bytes and section 3; 108 reference files; locks; exactly 3 paths')
PY
```

Actual terminal result:

```text
PASS: 57 merges; 30 new / 48 total rows; 27 excluded merges; 3 absent PRs; 34 new / 58 total spec quotations; dependency lists/citations; historical bytes and section 3; 108 reference files; locks; exactly 3 paths
```

## Contract findings, non-claims and residuals

- A (defined and matching): documented selection, canonical substring,
  declared-dependency and branch-observation rules match the pinned sources.
- B (undefined): whether loop work counts toward/completes/replaces a canonical
  node remains the existing `DECISION_REQUIRED · Astra` question in §3, unchanged.
  No new runtime characterization; historical B/C findings keep their own scope.
- C (explicit violation): none found in this documentary task. The historical
  #267 old-base finding is not treated as a current defect or reopened here.

No canonical status, owner, completion/count, policy value, command, authority
or acceptance changed. These checks do not prove production readiness,
durability, distributed fencing, exactly-once payments, chain finality, legal
compliance or an independent A2 review. No cited historical fixture was rerun
or promoted to new runtime evidence.

All three paths satisfy the documentation-only path patterns in the KTX job
and protocol job. Rust tests, Cargo/Clippy/format, heavy protocol, Move/localnet,
ZK, npm/Node and reference/readiness/HTTP suites: NOT_RUN for this documentary
patch. The separate `rights-scale` job has no documentation-only classifier;
the 27 local document checks are the closest relevant local equivalent, not
full workflow verification. Plain `check_stage5_host.py` was never invoked;
only its synthetic self-test ran. No background long job was started.

Deviations: fetch omitted under the supervisor's no-network rule; the local
starting base is #271 rather than #269, while the evidence remains bounded to
#269 as designed. The task's October 23 path is retained and the actual October
24 execution date is disclosed. No substantive design or scope deviation.
No hardware, paid services, credentials, live funds/providers, public endpoint,
Sui testnet/mainnet, storage engine, coin/TIX module or production runtime was
needed or used. No new decision request was necessary.

Remaining uncertainty: remote freshness, future exact-head CI, non-author review
and Astra's canonical-counting decision. Supervisor owns publication and any
later merge. Later merges need a separate refresh; the inline assertions are
one-time documentary checks, not continuous CI coverage.
