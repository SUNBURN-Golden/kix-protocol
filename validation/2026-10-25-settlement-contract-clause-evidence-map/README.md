# Settlement contract clause evidence map — execution record

2026-10-25. Builder-authored map, not a review or an acceptance; no grade change.
Node: `plan-settlement-contract-clause-evidence-map`. Task input is the supervisor's
node specification and read-only design supplied in this session; no node issue
or `docs/tasks/` document exists. Task 005's charter was read as historical context,
not reused as current implementation authorization.

Local observed `origin/main`, task base and branch HEAD are all
`590e544b3d097ba3de2fc573deae43b15bc39773` on
`agent/kix-plan-settlement-contract-clause-evidence-map`; no local base delta.
No fetch was run: the supervisor explicitly prohibited network actions, overriding
AGENTS §1's fetch requirement. Remote freshness is unverified. The contract's
historical bases are retained as history, not task bases.

Implementation and final committed task head: not created in this session;
changes remain uncommitted for the supervisor. No merge commit exists for this
work. KTX and KIX exact-head CI run IDs/status/conclusions: not available, not
queried or run. Post-merge main CI: not applicable. READY here means local builder
handoff, not merge-ready, independent review, acceptance or production readiness.

## Changed paths

- `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md` — all 27 contract headings,
  scoped predicates, 106 existing test citations, coverage limits and owners.
- `scripts/check_settlement_evidence_map.py` — stdlib-only heading/status/owner
  and AST test-citation validation, with in-memory negative controls.
- `docs/README.md` — one location bullet linking both new documents.
- `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md` — this record.

## Existing coverage and added evidence

The [map](../../docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md) is the requirement
coverage inventory: 12 COVERED, 5 PARTIAL, 2 NOT_COVERED, 8 OPEN.
Existing deterministic mock, FSM, adopted-policy, seeded-property,
rejection-atomicity, returned-result replay, multi-payee refund and restore
fingerprint tests were inspected and cited; none was duplicated or modified.
COVERED describes sufficient existing evidence for the scoped mock predicate,
PARTIAL describes partial coverage, and NOT_COVERED describes absent coverage.
OPEN preserves an unresolved decision and its contract owner route.

The new evidence is structural: every contract heading exactly once, unchanged
titles, only allowed test paths, direct test methods on TestCase classes, status
and owner consistency, and counts. Mutation self-tests demonstrate missing clauses,
dangling paths/symbols, helper/non-test citations, policy closure, owner drift,
title drift, malformed rows and stale counts are rejected. These checks do not
verify the semantic adequacy of test assertions.

## Commands and actual results

| Command | Actual result |
|---|---|
| `git status --short; git branch --show-current; git rev-parse origin/main HEAD` | Initially clean; expected branch; both refs 590e544b3d097ba3de2fc573deae43b15bc39773. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both required blobs match (full values below). |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; rows=27 headings=27 citations=106 COVERED=12 PARTIAL=5 NOT_COVERED=2 OPEN=8. |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; 31 negative controls detected, including removed §9.3, added §9.7, dangling path/symbol and helper symbol; self-test: pass. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; Ran 187 tests in 2.084s; OK. |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=364 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=233 indexed=198 allowlisted=35 |
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
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test: pass |
| `rg -n '^(import\|from) ' scripts/check_settlement_evidence_map.py` | Exit 0; only ast, re, sys and pathlib imports. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git diff --name-only origin/main -- runtime reference .github .aiops docs/tasks docs/contracts docs/decisions docs/status/CURRENT_CAPABILITY_REGISTER.md` | Exit 0; empty output; protected/out-of-scope tracked paths unchanged. |
| `python3 - (reference blob comparison below)` | Exit 0; all 108 tracked reference/v0.3-rc1 files match their index blobs byte for byte. |
| `git status --short; git diff --stat` | Exactly the four authorized changed paths; tracked diff is the docs index bullet; other three files are new/untracked. |

The narrow checker and settlement suite ran before the broader checks. The 29
broader commands above were run sequentially by a foreground stdlib subprocess
runner: the complete protocol.yml **Stdlib offline document checks** run block
(27 invocations), then the two OpenAPI-pin commands adjacent to the settlement
suite. Each return code was recorded and all were zero. No shell `FAIL` fallback
masked an exit code. Source inspection used `cat`, `sed`, `rg` and `wc` on the
session-start guidance, contract, cited tests/helpers, existing maps/checkers and
the two workflow definitions. These are read-only inspection commands, not tests.
`python3 /tmp/build_settlement_map.py` generated the initial map from manually
assigned rows and exact contract titles; it exited 0 and is not a repository
artifact or a continuing dependency.

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

After the record was filled, the map checker, its self-test, docs-index checker
and status-register checker were checked again, with the same successful results;
locked blobs and the scope guard were checked again. No source/test edits were
made after the 187-test settlement run. The final record update changes only this
execution narrative, not the tested checker or cited evidence.


## Preservation, deviations and limits

Before work, `git hash-object` returned the required blobs:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The design's count of 26 headings is incorrect: regex extraction yields 27.
All 27 are mapped. §6 is COVERED because existing fault tests do exercise
MOCK_INVARIANT; the design allowed that judgment after reading the tests.
§9 and §9.2 are PARTIAL: lifecycle_authority/catalog scope is outside direct
suite assertions, and §9.2 retains the prior zero-cash interpretation question.

No newly established class C violation. The pre-existing
[seeded property record §7(iii)](../2026-10-16-settlement-seeded-property-suite/README.md)
labels the zero-cash commit/distribute observation **B, reviewer to confirm**:
conservation is tested, and the sentence describing zero-cash freeze as outside
FSM acceptance remains subject to descriptive/normative interpretation. This map
does not decide that interpretation. If review finds it normative, the prior
record says class C blocks merge. Existing minimal reproduction:
`MachinePropertyTests.test_e_characterization_zero_cash_commit_then_distribute_conserves`.

Other class B observations: internal invariant injection may leave live mutation
outside the journal (reconcile detects it); general returned-view/export isolation
and retained-object lifetime are characterizations beyond immutable first-result
replay; new command keys on already-bound economic identifiers and distribution
after full reclassification retain their previously recorded limits. No rollback
or independent-review claim follows.

§0.3/§7.3 use the contract header/R-9 `DECISION_REQUIRED · Astra` route, with no
specific payee owner invented. §7.8 remains UNDETERMINED/unopened, NOT_COVERED,
owner none because the contract names none. Other open policy values retain their
contract-verbatim owners; P04 remains deferred. No product policy value is chosen.
F01/F02/F03/P04 remain 설계중. The capability register and grades are unchanged.

The checker runs locally only; CI is unchanged by task constraint. A separate
User/orchestrator node could wire it into protocol.yml to prevent later citation
drift. This task does not test real PG/bank/KYC, funds, Sui, durable storage, legal
or accounting treatment, bank exactly-once, finality, production readiness,
performance, arbitrary payee cardinality or F04 snapshot integration. No Rust
code is touched, so cargo checks are outside the closest local equivalents for
these paths; this is not a claim that the hosted workflows ran or would skip.
No commits, pushes, issues, PRs, comments, external actions, polling, automatic
retry or background jobs were performed.
