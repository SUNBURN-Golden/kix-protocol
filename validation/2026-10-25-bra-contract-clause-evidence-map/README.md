# BRA contract clause evidence map — local validation

**Builder-authored record, not a review or an acceptance; no grade change.**

## Task and baseline

Node `plan-bra-contract-clause-evidence-map`, executed 2026-10-25 (Asia/Seoul).
No issue or task file exists for this node. The supervisor-provided task and
read-only design are the immutable input; no `docs/tasks/` file was created or
changed. This is not an ASTRA program-mode session.

Branch: `agent/kix-plan-bra-contract-clause-evidence-map`.
Local observed `origin/main`, task base and initial HEAD:
`c0fc5b4aed4da32284d9879ad21ef6b584db01d2` (all equal; no base delta).
The worktree was initially clean. The supervisor explicitly prohibits all
network/GitHub actions, so `git fetch origin main` was not run and remote
freshness is unverified. No commit or push is authorized. Implementation/final
commit SHA is therefore not yet assigned; HEAD remains the initial SHA with the
four-file working-tree patch. The supervisor will establish the delivery head.

Exact-head KTX CI: not requested/observed; run ID/status/conclusion unavailable.
Exact-head KIX protocol CI: not requested/observed; run ID/status/conclusion
unavailable. No previous SHA's CI is inherited. Merge SHA/post-merge CI are not
applicable: no merge was performed. READY means the local node acceptance checks
pass for supervisor handoff, not merge-ready or independent audit acceptance.

## Complete changed paths

- `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md` — 39 headings and nine open items.
- `scripts/check_bra_evidence_map.py` — stdlib-only structural checker/self-test.
- `docs/README.md` — one bullet indexing the map and this record.
- `validation/2026-10-25-bra-contract-clause-evidence-map/README.md` — this record.

## Existing coverage and new evidence

The [map](../../docs/status/BRA_CONTRACT_EVIDENCE_MAP.md) is the existing coverage
inventory: **21 COVERED, 15 PARTIAL, 1 NOT_COVERED, 2 OPEN** heading rows,
plus **9 OPEN** item rows and **212 citations**. COVERED is sufficient existing
local mock/FSM evidence; PARTIAL is partial evidence with the missing predicate
named; NOT_COVERED has no evidence for the external/unopened behavior; OPEN
retains an unresolved value and its contract owner. No business tests were added
or modified. Existing gates, negative controls, sequential races, open-item,
FSM, seeded-property, rejection-atomicity, returned-result and restore-fingerprint
bodies/helpers were inspected before assigning statuses.

The new checker closes a structural gap: exactly one row per numbered heading
and §7.1 item, exact headings, safe AST-visible test citations, pinned open/gap
statuses, owner preservation and counts. Its 50 in-memory negative controls catch
missing clauses, new/removed/duplicate headings, duplicate/invented rows, dangling
paths/symbols, helper/dynamic-method citations, unsafe paths, status/owner drift,
malformed rows/evidence and stale counts. A positive control verifies same-module
transitive TestCase/mixin inheritance. No source/import is executed by the
checker. The checker does not judge semantic test adequacy.

## Commands and actual results

Read-only source inspection used `pwd`, `cat`, `sed`, `rg` and Git identity/blob
queries on the start guidance, control-plane pointer, contract, maps/checkers,
cited tests/helpers, prior validation records and both workflow definitions.
Python heredocs generated the map from manually assigned rows and exact contract
titles, adapted the self-test's COVERED target after §1 became PARTIAL, and wrote
the index/record; all exited 0. These are construction/inspection, not test passes.
The narrow checks below ran before the broader workflow block. Initial plain
checker and self-test passed; the BRA suite then passed 402 tests in 8.054s.

| Command | Actual result |
|---|---|
| `pwd && git status --short && git rev-parse origin/main HEAD && git branch --show-current && git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0; correct worktree/branch, initially clean, refs equal c0fc5b4aed4da32284d9879ad21ef6b584db01d2; both required blobs match. |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; rows=39 headings=39 items=9 citations=212 COVERED=21 PARTIAL=15 NOT_COVERED=1 OPEN=2. |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; 50 negative controls detected, including missing clause, dangling path and dangling symbol; transitive inheritance positive control passes. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; Ran 402 tests in 8.054s; OK. |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=364 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=235 indexed=200 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; Ran 187 tests in 1.713s / OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; Ran 402 tests in 8.193s / OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0; Ran 147 tests in 7.678s / OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Exit 0; Ran 85 tests in 3.336s / OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; Ran 168 tests in 2.087s / OK |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test: pass |
| `git diff --check` | Exit 0; no whitespace errors. |
| `rg -n '^(import\|from) ' scripts/check_bra_evidence_map.py` | Exit 0; only ast, re, sys and pathlib (lines 10–13). |
| `git diff --name-only origin/main -- runtime reference .github .aiops docs/tasks docs/contracts docs/decisions docs/status/CURRENT_CAPABILITY_REGISTER.md` | Exit 0; empty output; protected/out-of-scope tracked paths unchanged. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0; after work both required blobs match (full values below). |
| `python3 -` (byte-preservation heredoc below) | Exit 0; all 108 tracked reference/v0.3-rc1 files match index blobs byte for byte. |
| `git status --short` | Exit 0; exactly the four authorized paths, with the new validation directory containing only README.md. |

The 27 commands from `protocol.yml`'s **Stdlib offline document checks** block
were extracted in workflow order and run sequentially in the foreground by a
stdlib subprocess runner, stopping on any nonzero exit. The adjacent offline
block was then run in order: all five reference discovery suites, then both
OpenAPI checkers plain and self-test. Every exit code was zero. The five-suite
block passed **989 tests** (187 + 402 + 147 + 85 + 168); this total excludes the
separate earlier 402-test narrow run. Each actual command/result is listed above.
No test failure or environment repair occurred. Child output was captured by the
foreground runner; no shell fallback masked failures and no background job ran.

The checker was finally tightened so the ownerless storage-lock fallback is used
only when the same contract item actually names that route. This does not change
the current map or its results. The final verification table below records the
checks after this change and after filling this execution narrative.

## Preservation

| Locked path | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

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
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert actual == expected.decode(), str(path)
    checked += 1
print('reference/v0.3-rc1 byte preservation: %d tracked files match index blobs' % checked)
# PY
```

## Deviations, classifications and limits

- Fetch was omitted under the supervisor's express network prohibition; remote
  freshness is unverified. The locally observed main/base/HEAD are equal.
- §1 is PARTIAL rather than the design's suggested COVERED: no direct assertions
  were found for identifier length boundaries/str subclasses, amount upper limit
  or clock upper limit. No test or contract was changed to fill those gaps.
- §4 is PARTIAL for real cross-channel currentness (as allowed by the design).
  §11.2 is PARTIAL for the recorded clock-skew class B limit. Other preambles,
  non-claims and sequential-order gaps retain explicit partial coverage.
- The checker additionally pins each item's complete owner list to its own
  §7.1 row, rather than accepting an arbitrary owner elsewhere in that section.
  This catches swapping two valid owners as well as inventing an owner. The
  ownerless durable-show-config uses only its explicit §5 잠금 route.
- The checker has 50 negative controls plus a transitive-inheritance positive
  control, extending the minimum requested cases. Row-generated setattr methods
  remain unresolvable by design and run through unittest discovery only.

No new explicit contract violation (class C) was found. The earlier adopt-issued
class C restore-equality defect was fixed on main and is pinned by inherited
atomicity regression tests. The existing class B clock-skew delegated-authorization,
post-mutation injected faults, general returned-data copy ownership/lifetime and
post-restore retry-response equivalence are described in the map and linked prior
records. This node does not redefine their contracts or make a general rollback
claim. Source-informed tests do not constitute independent review.

All nine items remain OPEN with UNDETERMINED inputs and contract-verbatim owners.
§7.3 remains NOT_COVERED for real executor/channel currentness, production routing,
chain grant/finality, actual buyer evidence availability, kernel lifecycle and
the other unopened gaps. No product policy value, command, storage engine or
external service is needed or chosen. B01–B05, R01–R05 and P03 remain 설계중;
no register or grade change. The map records evidence gaps without filling them.

No Rust is touched, so the cargo steps in `ktx-kernel.yml` are not the closest
local equivalents for these paths and were not run. No full hosted-workflow,
merge-ready, production, performance, durability, bank exactly-once, finality,
legal/tax/accounting compliance or real-money claim is made. No real funds,
PG/bank/KYC calls, public endpoints, Sui testnet/mainnet, new coin/TIX module,
secrets, equipment, paid service or production runtime was used. Tests include
only the suite's existing ephemeral loopback gate fixtures, not external calls.
No commit, push, issue, PR, GitHub comment, fetch, remote action, polling or
automatic retry was performed. No STOP condition was encountered.

Remaining follow-up candidates are the named evidence gaps, owner decisions,
class B semantics and possible CI wiring of the local checker, each in a
separate authorized node. This record is not authorization for those changes.

## Final verification

| Command | Actual result |
|---|---|
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=212 COVERED=21 PARTIAL=15 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_bra_evidence_map.py --invalid` | Exit 2; usage: check_bra_evidence_map.py [--self-test] |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=235 indexed=200 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=364 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `git diff --check` | Exit 0; (empty output) |
| `git diff --name-only origin/main -- runtime reference .github .aiops docs/tasks docs/contracts docs/decisions docs/status/CURRENT_CAPABILITY_REGISTER.md` | Exit 0; (empty output) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0; 69564b166f0c27f9af5d8422f0a466b18d74c20f / b607996c83a119c349f1cc90469ac1ba82764e20 |
| `git rev-parse origin/main HEAD` | Exit 0; c0fc5b4aed4da32284d9879ad21ef6b584db01d2 / c0fc5b4aed4da32284d9879ad21ef6b584db01d2 |
| `python3 -` (final verification runner, first invocation) | Exit 1 in the status-path assertion only: its stdout.strip() removed the leading status space from the first git-status row. All preceding checker and guard commands passed. This was a runner parsing error, not a repository test failure; corrected below by preserving raw line prefixes. |
| `git status --short --untracked-files=all` (corrected raw-line scope assertion) | Exit 0; exact four-file set verified. |
| `git diff --check` | Exit 0; empty output. |
| `git ls-files --others --exclude-standard -- runtime reference .github .aiops docs/tasks docs/contracts docs/decisions` | Exit 0; empty output. |

The final record-only append reports the corrected status helper; no checker, map, index, source or test changed after the successful final checks. All node acceptance checks pass for local supervisor handoff.
