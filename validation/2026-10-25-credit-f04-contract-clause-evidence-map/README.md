# F04 contract clause evidence map — local validation

2026-10-25. Builder-authored execution record, not independent review or
acceptance; no grade change. F04 and E06 remain **설계중**, mock/sim only.

## Task and revision anchors

- Node: `plan-credit-f04-contract-clause-evidence-map`.
- Task document: the supervisor-provided node specification/design in this
  session. No issue exists and there is no node task file under `docs/tasks/`.
  This is not ASTRA program mode.
- Branch: `agent/kix-plan-credit-f04-contract-clause-evidence-map`.
- Observed cached `origin/main`, task base and initial HEAD:
  `a329ec07ac52ec15bff6c48079115d81ace5ab67` (all equal; no cached-base delta).
  Initial `git status --short` was empty.
- Implementation/final local HEAD remains that same SHA; this delivery is an
  **uncommitted worktree patch**. A final committed task head will be assigned by
  the supervisor, not claimed here. No merge commit exists for this delivery.
- Exact-head KTX CI: run ID/status/conclusion **not obtained**. Exact-head KIX
  protocol CI: run ID/status/conclusion **not obtained**. Post-merge main CI:
  **not applicable**. Network/GitHub and publication are supervisor-only.
  Local passes do not establish the AGENTS §10 merge gate.

Complete changed-path list:

- `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md` (new map).
- `scripts/check_credit_evidence_map.py` (new stdlib checker and self-test).
- `docs/README.md` (one index bullet).
- `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md`
  (this execution record).

## Coverage and checker scope

The [map](../../docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md) covers the actual
22 numbered headings, preserving exact titles. Existing deterministic coverage
is classified as 13 COVERED, 5 PARTIAL, 1 NOT_COVERED and 3 OPEN clauses, plus
five OPEN adopted items. Each policy number stays UNDETERMINED and each owner
is copied verbatim. The real-credit lock and the
[lift criteria as recorded](../../docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md)
are unchanged.

Existing coverage was inspected before adding checker self-tests. Mock, FSM,
open_terms, seeded-property, deterministic rejection, first-response isolation
and restore-fingerprint tests supply the citations. No domain regression tests,
contract, mock, FSM, register, grades or CI were changed. Unadopted alternatives,
complete catalog/SDK/manifest preservation and external guarantees retain named
gaps. §5.4 remains NOT_COVERED with owner none; §5/§5.1/§5.2 remain OPEN.

The checker fills a structural evidence gap: it verifies completeness, exact
headings, citation paths and direct TestCase test methods via AST, statuses,
counts and owner preservation. It does not execute cited modules or determine
semantic sufficiency. Its 55 in-memory negative controls detect missing §7.8,
new/removed/duplicate headings, dangling paths/symbols, helper/non-test methods,
unsafe paths, status and owner drift, missing UNDETERMINED, malformed rows,
missing citations/gaps/banners, stale/duplicate totals, and adopted-item drift.
A positive AST fixture checks direct TestCase selection and excludes ordinary
and inherited classes. The real unmodified map must pass before controls run.

## Commands and actual results

All commands ran from the repository root, in the foreground. The new checker
(plain and self-test) ran first, then the narrow F04 suite, then the sequential
workflow equivalents below. Every listed verification command exited 0.

| Command | Actual result |
|---|---|
| `git status --short` (start) | Exit 0; clean worktree. |
| `git rev-parse origin/main HEAD` | Exit 0; both a329ec07ac52ec15bff6c48079115d81ace5ab67. |
| `git branch --show-current` | Exit 0; agent/kix-plan-credit-f04-contract-clause-evidence-map. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Exit 0; required 69564b166f0c27f9af5d8422f0a466b18d74c20f and b607996c83a119c349f1cc90469ac1ba82764e20, respectively. |
| `python3 /tmp/build_credit_checker.py` | Exit 0; initial checker adaptation from the BRA sibling; final local edits followed before testing. |
| `python3 /tmp/build_credit_map.py` | Exit 0; regex confirmed 22 contract headings (0–7, 5.1–5.5, 7.1–7.9); wrote map, index bullet and initial record. |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; rows=22 headings=22 items=5 citations=127 COVERED=13 PARTIAL=5 NOT_COVERED=1 OPEN=3. |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; detected missing clause, dangling path and dangling symbol; direct TestCase selection pass; pass (55 negative controls). |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` (narrow) | Exit 0; 147 tests in 6.739s; OK. |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=364 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=237 indexed=202 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; Ran 187 tests in 1.705s; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; Ran 402 tests in 7.964s; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0; Ran 147 tests in 6.717s; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Exit 0; Ran 85 tests in 2.803s; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; Ran 168 tests in 1.824s; OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test: pass. |
| `rg -n '^(import\|from) ' scripts/check_credit_evidence_map.py` | Exit 0; imports only ast, re, sys and pathlib. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git diff --name-only origin/main -- runtime reference .github .aiops docs/tasks docs/contracts docs/decisions docs/status/CURRENT_CAPABILITY_REGISTER.md` | Exit 0; empty output, tracked out-of-scope paths unchanged. |
| `python3 -` (reference blob comparison below) | Exit 0; all 108 tracked reference/v0.3-rc1 files match index blobs byte for byte. |
| `git diff -- docs/README.md` | Exit 0; one added index bullet (and its separating blank line). |
| `git status --short` (after implementation) | Exit 0; exactly the four authorized paths above, including the new validation directory. |

`python3 /tmp/validate_credit_map.py` ran the 36 workflow-equivalent commands
above sequentially and returned exit 0. It extracted the authoritative **Stdlib
offline document checks** run block from `protocol.yml` (27 invocations), then
ran its five reference suites and four adjacent OpenAPI checks. Each return code
was captured; failures would stop the runner without a shell fallback. Outputs
were recorded locally in `/tmp/credit_map_validation_results.json`; neither
temporary runner nor results file is a repository artifact or runtime dependency.
`python3 /tmp/write_credit_validation.py` rendered those actual results into this
record and exited 0. Source inspection used `cat`, `sed`, `rg` and `wc` on the
session-start governance, current development plan, baselines, authority model,
F04 contract, decisions, cited test bodies/helpers, sibling maps/checkers and both
workflow definitions. Those were read-only inspection, not additional test claims.

After filling this record, the new map checker, docs-index checker and
status-register checker were each rerun plain and with `--self-test`; all six
commands exited 0 with the same successful counts/results. `git diff --check`,
`git rev-parse origin/main HEAD`, the two locked-file hashes, the protected-path
diff guard and `git status --short --untracked-files=all` were rerun too: exit 0,
unchanged HEAD/base and locked hashes, no protected-path diff, and exactly the
four listed paths. No checker or reference source changed after those runs.

Byte-preservation command actually run:

```python
# python3 - <<'PY'
import hashlib
from pathlib import Path
import subprocess
entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z',
                                   'reference/v0.3-rc1/']).split(b'\0')
checked = 0
for entry in entries:
    if not entry:
        continue
    metadata, name = entry.split(b'\t', 1)
    mode, expected, stage = metadata.split()
    path = Path(name.decode())
    assert mode == b'100644' and stage == b'0', (mode, path)
    data = path.read_bytes()
    actual = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert actual == expected.decode(), str(path)
    checked += 1
print('reference/v0.3-rc1 byte preservation: %d tracked files match index blobs' % checked)
# PY
```

## Preservation, deviations and limits

The locked blobs before and after work match exactly:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

- Session-start fetch was omitted because the explicit supervisor rule prohibits
  every GitHub/network action. Cached main is recorded; remote freshness is
  unverified. No base was changed.
- The plan's heading count of 22 is confirmed without correction. §4 is COVERED:
  existing tests exercise the caller codes and injected MOCK_INVARIANT. That
  injected assertion establishes only the internal error code; no rollback
  contract is inferred. This is the plan's allowed evidence-based choice.
- Item owners are checked for exact equality with the complete contract owner
  after `담당은 `, strengthening the planned substring test to reject truncation.
  OPEN clause owners also preserve the complete applicable owner set.
- The current workflow includes two integration-gate OpenAPI checks beside the
  planned OpenAPI pin checks; both were included. No workflow was edited.
- No Rust is touched, so Cargo tests/Clippy/fmt in `ktx-kernel.yml` are not the
  closest local equivalents for these paths. No full hosted-workflow pass is
  claimed; HTTP/SDK/Move/ZK/production-runtime jobs were not run for this map.

No newly established class C contract violation. Existing class B observations
remain class B: persistent frozen faces after release, same economic-identifier
replay under a new key after terminal, the gate's omission of later refund fields,
same-binding terminal re-offer reporting ILLEGAL_TRANSITION, injected internal
failures leaving unjournaled mutations or guard rejection after journaling, and
broader view/export copy isolation. The map records these limits without changing
contracts or promoting fault behavior into acceptance guarantees.

No real funds, PG/bank/KYC calls, public endpoint, Sui testnet/mainnet, storage
engine, product policy selection, new command, secret or production runtime was
needed or introduced. No legal/licensing, durable-storage, bank exactly-once,
chain-finality, distributed-fencing or production-readiness claim follows.
The remaining semantic judgment needs non-author review; policy/legal gaps stay
with their named owners. CI integration for the checker is a separate node.
No commit, push, reset, branch/tag mutation, PR, issue, comment, network action,
background job, polling or automatic retry was performed. READY means this local
builder delivery is ready for supervisor handling, not merge-ready under §10.
