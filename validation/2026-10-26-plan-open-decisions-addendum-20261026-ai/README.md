# Validation — October 26 AI delegation stop ledger addendum

## Basis, task and scope

Task `plan-plan-open-decisions-addendum-20261026-ai`; task document:
supervisor-supplied node specification/design in the session, no issue and no
matching `docs/tasks/` file. Not ASTRA program mode; loop-proposed, absent from
`.aiops/program.json`; depends_on []; audit floor A2; astra_gate None; user_merge False.

Observed cached origin/main / base / starting HEAD: `957f75d75ea4854eba117d66d07663133f0b7b2c`.
Branch: `agent/kix-plan-plan-open-decisions-addendum-20261026-ai`.
`git fetch origin main`: NOT_RUN, supervisor forbids all network/GitHub actions.
Remote freshness is unverified; starting origin/main and HEAD match.
Implementation/final committed task head: not created by this builder; HEAD
remains the starting SHA with the three documentary changes uncommitted.
Merge SHA: N/A, no merge performed.

Changed paths (complete intended delivery):
- `docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md`
- `docs/README.md`
- `validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md`

[Addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md) records provenance, owner, open stops and the inventory.
No new regression test: this task adds documentary evidence only.

## Source and pre-edit inspection

Read README, DEVELOPMENT_PLAN, BASELINES, AUTHORITY_MODEL_1, the supplied task
and named contract/evidence; inspected AGENTS, control-plane pointers and both
workflow definitions. The external worktree was read only. The source stop's
reproduction, branch test and blocked-node workflow were not executed.

```sh
git status --short --untracked-files=all
git rev-parse origin/main HEAD
git branch --show-current
sha256sum /workspace/kix-run/wt/plan-plan-aid-contract-map-partial-closure/DECISION_REQUIRED.md
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
git diff --quiet origin/main -- reference docs
```

Actual pre-edit results: status empty; both refs `957f75d75ea4854eba117d66d07663133f0b7b2c`;
branch as above; source SHA-256
`24338c0753381529f3a9c00936dd8792130d8021cdef4ce0b60b9e8c6dae8e12`;
locked blobs `69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`; diff quiet exit 0.
The pre-edit quiet check allows the working-tree grep/sed commands below to
represent the pinned SHA; the unchanged-source check is repeated after edits.

## Existing coverage mapping (AGENTS §7)

| Requirement | Existing coverage | Classification / action |
|---|---|---|
| Ledger provenance/owners/open items | October 22/23 ledgers and October 25 closure | Partially covered: A5 absent; add attributed stop and preserve owners. |
| Current actor/tool rejection behavior | Seven G2 functions and CASES below | Sufficient for inventory; not proof of contested check order. |
| Simultaneous actor-binding vs deny/unknown-tool precedence | Source stop's external characterization; main §7 map already PARTIAL | Partially covered: source report remains class C; no reproduction rerun or fix authorized here. |
| Other simultaneous failures | `reference/ai_delegation/test_ai_delegation_properties.py::ClassBCharacterizationTests.test_b_precedence_among_several_violations_is_set_membership` | Characterization only; not selected by G2 because it calls the propose helper and uses codes outside K. |
| Path/symbol presence, inventory counts | No existing addendum inventory | Not covered before task: G1–G7 and pinned-object presence verification below fill documentary gap. |
| Index/register consistency | `scripts/check_docs_index.py`, `scripts/check_status_register.py`, both with self-tests | Sufficient: use unchanged checkers; no duplicate test. |

## Mechanical gathering commands and raw outputs

All commands ran from the repository root before documentary edits, exit 0.
G1 is pinned to the full SHA. G2 starts from G1's file universe, strips only
the SHA prefix, then tracks classes and function bodies with awk. Each
function flushes at the next top-level/class-level definition, class boundary
or EOF. G5 compares function names from G2 with DLG rows; all selected matches
are in mock-test cells. No branch-only artifact is counted.

Each count below is the actual output of `( COMMAND ) | wc -l`, where COMMAND
is the exact corresponding block. This also specifies the count reproduction;
the raw output is preserved without shortening rows.

### G1

```sh
git grep -lE 'call_tool' 957f75d75ea4854eba117d66d07663133f0b7b2c -- 'reference/ai_delegation/test_*.py' 'readiness/test_*.py' readiness/conformance.py 'integration_gate/test_*.py'
```

Exit 0; `wc -l`: 7.

```text
957f75d75ea4854eba117d66d07663133f0b7b2c:readiness/test_faults.py
957f75d75ea4854eba117d66d07663133f0b7b2c:reference/ai_delegation/test_ai_delegation_mock.py
957f75d75ea4854eba117d66d07663133f0b7b2c:reference/ai_delegation/test_ai_delegation_properties.py
957f75d75ea4854eba117d66d07663133f0b7b2c:reference/ai_delegation/test_contract_error_codes.py
957f75d75ea4854eba117d66d07663133f0b7b2c:reference/ai_delegation/test_rejection_atomicity.py
957f75d75ea4854eba117d66d07663133f0b7b2c:reference/ai_delegation/test_restore_fingerprint_equivalence.py
957f75d75ea4854eba117d66d07663133f0b7b2c:reference/ai_delegation/test_returned_data_isolation.py
```

### G2

```sh
mapfile -t inventory_files < <(git grep -lE 'call_tool' 957f75d75ea4854eba117d66d07663133f0b7b2c -- 'reference/ai_delegation/test_*.py' 'readiness/test_*.py' readiness/conformance.py 'integration_gate/test_*.py' | sed 's/^[^:]*://')
for inventory_file in "${inventory_files[@]}"; do
  awk 'function flush() {
  if (test != "" && calls && codes)
    print FILENAME "::" (cls == "" ? "" : cls ".") test ":" start
  test = ""; calls = 0; codes = 0
}
FNR == 1 { cls = ""; test = ""; calls = 0; codes = 0 }
/^class / {
  flush(); cls = $2; sub(/[( :].*/, "", cls); next
}
/^(    def |def )/ {
  flush()
  name = $0; sub(/^[ ]*def /, "", name); sub(/\(.*/, "", name)
  if (name ~ /^test_/) { test = name; start = FNR }
}
test != "" && /call_tool/ { calls = 1 }
test != "" && /(UNKNOWN_ACTOR|UNKNOWN_GRANT|TOOL_NOT_ALLOWED|TRANSFER_FORBIDDEN|REFUND_EXECUTION_FORBIDDEN|SIGNING_FORBIDDEN|MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY|DENY_CODES)/ { codes = 1 }
END { flush() }' "$inventory_file"
done | sort -u
```

Exit 0; `wc -l`: 7.

```text
reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_ai_cannot_decide_and_strangers_are_rejected:162
reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_allowlist_is_disjoint_from_protocol_commands:240
reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools:222
reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_tool_level_follows_the_grant:483
reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_ai_actors_never_issue_revoke_or_decide:433
reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_deny_and_unknown_tools:400
reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_tool_level_follows_the_grant:449
```

### G2-CASES

```sh
grep -nE '^[[:space:]]*\("(UNKNOWN_ACTOR|UNKNOWN_GRANT|TOOL_NOT_ALLOWED|TRANSFER_FORBIDDEN|REFUND_EXECUTION_FORBIDDEN|SIGNING_FORBIDDEN|MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY)", "call_tool"' reference/ai_delegation/test_rejection_atomicity.py
```

Exit 0; `wc -l`: 6.

```text
57:    ("UNKNOWN_ACTOR", "call_tool", tool_args(actor="stranger"), None),
62:    ("TOOL_NOT_ALLOWED", "call_tool",
64:    ("TRANSFER_FORBIDDEN", "call_tool", tool_args("transfer"), None),
65:    ("REFUND_EXECUTION_FORBIDDEN", "call_tool", tool_args("refund_execution"), None),
66:    ("SIGNING_FORBIDDEN", "call_tool", tool_args("sign"), None),
67:    ("MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY", "call_tool", tool_args("pay"), None),
```

### G3-clauses

```sh
grep -nE '^\| §[57] \|' docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md
```

Exit 0; `wc -l`: 2.

```text
49:| §5 | 도구 허용 목록과 거부 목록 | Closed allow/deny lists refuse transfer, refund, signing, self-expansion and unknown tools; grant-change requests are memos. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_allowlist_is_disjoint_from_protocol_commands`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_grant_change_memo_does_not_widen_the_grant`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_deny_and_unknown_tools` | AI_DELEGATION_LAYER_MATRIX.md: DLG-05, DLG-06, DLG-08, DLG-09, DLG-10, DLG-36 | COVERED | none | none |
51:| §7 | 부여와 제안의 단계 | Caps, periods, revocation/history, idempotency and canonical digest have offline and local restart evidence. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_caps_count_open_proposals_and_release_on_reject_or_withdraw`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_period_boundaries`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_revocation_is_immediate_and_keeps_history`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_proposal_idempotency`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_digest_is_sha256_of_canonical_json`; `reference/ai_delegation/test_ai_delegation_properties.py::PeriodTests.test_decide_rechecks_the_period`; `reference/ai_delegation/test_ai_delegation_properties.py::IdempotencyTests.test_replay_after_revocation_is_still_a_duplicate`; `reference/ai_delegation/test_ai_delegation_properties.py::ReplayDeterminismTests.test_command_log_replay_reproduces_every_digest`; `reference/ai_delegation/test_ai_delegation_properties.py::ClassBCharacterizationTests.test_b_precedence_among_several_violations_is_set_membership`; `reference/ai_delegation/test_returned_data_isolation.py::ReturnedResultReplayTests.test_corrupted_first_and_duplicate_results_do_not_change_duplicates`; `reference/ai_delegation/test_restore_fingerprint_equivalence.py::AiDelegationRestoreFingerprintClassATests.test_same_grant_binding_replays`; `readiness/conformance.py::BackendConformance.test_ai_delegation_registry_opens_once_and_issue_replays_across_restart`; `readiness/test_faults.py::ExtensionTests.test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off` | AI_DELEGATION_LAYER_MATRIX.md: DLG-15..DLG-28, DLG-35 | PARTIAL | Check order 1–8 is characterized only as set membership for simultaneous violations. Local readiness journal tests do not establish production durability. | none |
```

### G3-codes

```sh
grep -nE '^\| `(UNKNOWN_ACTOR|UNKNOWN_GRANT|TOOL_NOT_ALLOWED|TRANSFER_FORBIDDEN|REFUND_EXECUTION_FORBIDDEN|SIGNING_FORBIDDEN|MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY)` \|' docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md
```

Exit 0; `wc -l`: 7.

```text
68:| `UNKNOWN_ACTOR` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
69:| `UNKNOWN_GRANT` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
71:| `TOOL_NOT_ALLOWED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
72:| `TRANSFER_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
73:| `REFUND_EXECUTION_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
74:| `SIGNING_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
75:| `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
```

### G4

```sh
grep -nE '^\| AID \| `(UNKNOWN_ACTOR|UNKNOWN_GRANT|TOOL_NOT_ALLOWED|TRANSFER_FORBIDDEN|REFUND_EXECUTION_FORBIDDEN|SIGNING_FORBIDDEN|MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY)` \|' docs/status/CONTRACT_ERROR_CODE_COVERAGE.md
```

Exit 0; `wc -l`: 7.

```text
222:| AID | `UNKNOWN_ACTOR` | `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock._human`; `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock.call_tool` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_ai_cannot_decide_and_strangers_are_rejected`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_ai_actors_never_issue_revoke_or_decide` | COVERED | none |
223:| AID | `UNKNOWN_GRANT` | `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock.call_tool`; `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock.revoke_grant` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_grant_idempotency`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_next_generation_requires_revoke` | COVERED | none |
225:| AID | `TOOL_NOT_ALLOWED` | `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock._open_for_write`; `reference/ai_delegation/ai_delegation_mock.py::AiDelegationMock._withdraw` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_allowlist_is_disjoint_from_protocol_commands`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools` | COVERED | none |
226:| AID | `TRANSFER_FORBIDDEN` | `reference/ai_delegation/ai_delegation_mock.py::DENYLIST` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools` | COVERED | none |
227:| AID | `REFUND_EXECUTION_FORBIDDEN` | `reference/ai_delegation/ai_delegation_mock.py::DENYLIST` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools` | COVERED | none |
228:| AID | `SIGNING_FORBIDDEN` | `reference/ai_delegation/ai_delegation_mock.py::DENYLIST` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools` | COVERED | none |
229:| AID | `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | `reference/ai_delegation/ai_delegation_mock.py::DENYLIST` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools` | COVERED | none |
```

### G5

```sh
grep -nE '^\| DLG-[0-9]+ \|' docs/status/AI_DELEGATION_LAYER_MATRIX.md | grep -F -f <(
mapfile -t inventory_files < <(git grep -lE 'call_tool' 957f75d75ea4854eba117d66d07663133f0b7b2c -- 'reference/ai_delegation/test_*.py' 'readiness/test_*.py' readiness/conformance.py 'integration_gate/test_*.py' | sed 's/^[^:]*://')
for inventory_file in "${inventory_files[@]}"; do
  awk 'function flush() {
  if (test != "" && calls && codes)
    print FILENAME "::" (cls == "" ? "" : cls ".") test ":" start
  test = ""; calls = 0; codes = 0
}
FNR == 1 { cls = ""; test = ""; calls = 0; codes = 0 }
/^class / {
  flush(); cls = $2; sub(/[( :].*/, "", cls); next
}
/^(    def |def )/ {
  flush()
  name = $0; sub(/^[ ]*def /, "", name); sub(/\(.*/, "", name)
  if (name ~ /^test_/) { test = name; start = FNR }
}
test != "" && /call_tool/ { calls = 1 }
test != "" && /(UNKNOWN_ACTOR|UNKNOWN_GRANT|TOOL_NOT_ALLOWED|TRANSFER_FORBIDDEN|REFUND_EXECUTION_FORBIDDEN|SIGNING_FORBIDDEN|MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY|DENY_CODES)/ { codes = 1 }
END { flush() }' "$inventory_file"
done | sort -u | sed -E 's/.*::[^.]*\.([^:]*):[0-9]+$/\1/'
)
```

Exit 0; `wc -l`: 8.

```text
36:| DLG-05 | issue and pay tools are refused MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY; issue and pay flags stay false. | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` `reference/ai_delegation/test_ai_delegation_mock.py::test_flags_remain_false` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
38:| DLG-07 | An AI decide_proposal is refused AI_CANNOT_DECIDE with state unchanged. | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_decide_and_strangers_are_rejected` | none | none | none | MOCK_ONLY |
40:| DLG-09 | Allow and deny lists are disjoint; transfer, refund execution and signing are deny codes. | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
41:| DLG-10 | The allow list is disjoint from the protocol_contract.json command keys. | `reference/ai_delegation/test_ai_delegation_mock.py::test_allowlist_is_disjoint_from_protocol_commands` | none | none | none | NOT_APPLICABLE_BY_DESIGN: contract §2 keeps the mock off the command catalogue |
43:| DLG-12 | delegate and close_delegation are not called, reused or renamed. | `reference/ai_delegation/test_ai_delegation_mock.py::test_allowlist_is_disjoint_from_protocol_commands` `reference/ai_delegation/test_ai_delegation_mock.py::test_mock_has_no_v03_import` | none | none | none | NOT_APPLICABLE_BY_DESIGN: contract §2 separates the two delegation axes |
63:| DLG-32 | issue_grant, revoke_grant and decide_proposal are callable only by human principals. | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_issue_widen_reissue_or_revive` `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_decide_and_strangers_are_rejected` | `reference/rights_scale/sui/tests/delegation_tests.move::only_the_issuer_creates_grants` `reference/rights_scale/sui/tests/delegation_tests.move::only_the_grant_issuer_cuts_it` issuer address check | absent: `runtime/crates/kix-delegated-exec/README.md` | none | ANALOGUE_NOT_BOUND |
64:| DLG-33 | Query tools need QUERY and propose tools need PROPOSE on the grant. | `reference/ai_delegation/test_ai_delegation_mock.py::test_tool_level_follows_the_grant` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
67:| DLG-36 | A tool in neither list is TOOL_NOT_ALLOWED. | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
```

### G6

```sh
grep -nE '^    def (call_tool|predict_call_tool|do_deny|do_unknown_tool|do_stranger)\(' reference/ai_delegation/ai_delegation_mock.py reference/ai_delegation/ai_delegation_property_support.py
```

Exit 0; `wc -l`: 5.

```text
reference/ai_delegation/ai_delegation_mock.py:280:    def call_tool(self, actor: object, grant_id: object, tool: object, args: object, now: object) -> dict:
reference/ai_delegation/ai_delegation_property_support.py:518:    def predict_call_tool(self, p):
reference/ai_delegation/ai_delegation_property_support.py:1220:    def do_deny(self):
reference/ai_delegation/ai_delegation_property_support.py:1230:    def do_unknown_tool(self):
reference/ai_delegation/ai_delegation_property_support.py:1272:    def do_stranger(self):
```

### G7-header

```sh
grep -n '^## 7\.' docs/contracts/AI_DELEGATION_AUTHORITY.md
```

Exit 0; `wc -l`: 1.

```text
193:## 7. 부여와 제안의 단계
```

### G7

```sh
sed -n '210,212p' docs/contracts/AI_DELEGATION_AUTHORITY.md
```

Exit 0; `wc -l`: 3.

```text
1. `actor`가 그 부여의 `agent_id`인지.
2. 도구 이름이 거부 목록인지, 허용 목록인지.
3. 부여가 있는지, 철회됐는지, 그 쌍의 `ACTIVE` 세대인지.
```

I-T = G2's 7 functions + one CASES artifact = 8; G2-CASES has 6
matching entries, not 6 functions. I-M = G3-clauses 2 + G3-codes 7 = 9.
I-C = G4 7; I-D = G5 8. I-S1 = G6 5 symbols; I-S2 = one §7
clause containing G7's 3 numbered lines. Both options use the identical
I-T/I-M/I-C/I-D sets; no editing obligation follows from selection.

## Local verification and preservation

### Narrow checks (run first)

| Command | Exit | Actual result |
|---|---|---|
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=254 indexed=219 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | self-test: pass |

### Closest protocol.yml document-check equivalent

The following foreground runner extracts every checker command from the
`Stdlib offline document checks` block, preserves order, and stops on the first
nonzero exit. All 43 commands completed with exit 0. Table results quote each
command's final output line; self-test diagnostics were captured and passed.
`PYTHONDONTWRITEBYTECODE=1` suppresses incidental Python cache writes.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import json
import subprocess
text = Path('.github/workflows/protocol.yml').read_text()
block = text.split('      - name: Stdlib offline document checks\n', 1)[1].split('      - uses:', 1)[0]
commands = [line.strip() for line in block.splitlines() if line.strip().startswith('python3 scripts/check_')]
results = []
for command in commands:
    p = subprocess.run(command.split(), text=True, capture_output=True)
    results.append(dict(command=command, exit=p.returncode, output=p.stdout + p.stderr))
    if p.returncode:
        break
print(json.dumps(results))
raise SystemExit(any(r['exit'] for r in results))
PY
```

| Command | Exit | Actual result (last output line) |
|---|---|---|
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=254 indexed=219 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | 0 | settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | 0 | self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | 0 | bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | 0 | self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | 0 | credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | 0 | self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | 0 | primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | 0 | self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | 0 | ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | 0 | self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | 0 | lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | 0 | self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | 0 | contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | 0 | contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | 0 | Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | 0 | Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_stage5_host.py --self-test` | 0 | self-test: pass |

The error-code checker's unchanged `CLASS_C=0` is its lexical map accounting,
not a semantic check-order verdict. It does not dispose of source stop A5.

### Unchanged delegation source sanity

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -p 'test_*.py'
```

Exit 0: `Ran 85 tests in 2.798s`, `OK`. This is the main suite only;
the branch-only check-order test and the source stop's reproduction were
not run. Passing the existing suite does not establish contract-order compliance.

### Pinned path and symbol verification

The read-only script below consumes the raw gathering blocks above, checks
every local addendum link except this new validation output, and also validates
supporting Python citations in the selected map rows. It runs
`git cat-file -e <sha>:<path>` and `git grep -nE` for definitions against the
full recorded SHA; AST checks additionally verify qualified class membership.
Constants CASES and DENYLIST are checked as assignments.

```sh
python3 - <<'PY'
from pathlib import Path
import ast
import json
import re
import subprocess

sha = '957f75d75ea4854eba117d66d07663133f0b7b2c'
doc = Path('docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md')
record = Path('validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md').read_text()
gathering = record.split('## Mechanical gathering commands and raw outputs', 1)[1].split('## Local verification and preservation', 1)[0]
raw = '\n'.join(re.findall(r'```text\n(.*?)\n```', gathering, flags=re.S))
# Validate selected rows' citations too, including supporting tests not in I-T.
symbols = set(re.findall(r'((?:reference|readiness)/[\w/.-]+\.py)::([\w.]+)', raw))
symbols.update({
    ('reference/ai_delegation/test_rejection_atomicity.py', 'CASES'),
    ('reference/ai_delegation/ai_delegation_mock.py', 'AiDelegationMock.call_tool'),
    ('reference/ai_delegation/ai_delegation_property_support.py', 'Model.predict_call_tool'),
    ('reference/ai_delegation/ai_delegation_property_support.py', 'Driver.do_deny'),
    ('reference/ai_delegation/ai_delegation_property_support.py', 'Driver.do_unknown_tool'),
    ('reference/ai_delegation/ai_delegation_property_support.py', 'Driver.do_stranger'),
})
paths = {p for p, _ in symbols}
# All local Markdown links in the addendum except this node's new validation output.
for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
    path = (doc.parent / target.split('#')[0]).resolve().relative_to(Path.cwd()).as_posix()
    if path != 'validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md':
        paths.add(path)
for path in sorted(paths):
    subprocess.run(['git', 'cat-file', '-e', f'{sha}:{path}'], check=True)
    print('PATH OK', path)
for path, symbol in sorted(symbols):
    source = subprocess.check_output(['git', 'show', f'{sha}:{path}'], text=True)
    tree = ast.parse(source)
    parts = symbol.split('.')
    if len(parts) == 2:
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == parts[0])
        assert any(isinstance(n, ast.FunctionDef) and n.name == parts[1] for n in cls.body), (path, symbol)
    elif symbol in {'CASES', 'DENYLIST'}:
        assert any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == symbol for t in n.targets) for n in tree.body)
    else:
        assert any(isinstance(n, ast.FunctionDef) and n.name == symbol for n in ast.walk(tree)), (path, symbol)
    for part in parts:
        pattern = rf'^{part} =' if part in {'CASES', 'DENYLIST'} else rf'^(class |    def |def ){part}\b'
        output = subprocess.check_output(['git', 'grep', '-nE', pattern, sha, '--', path], text=True)
        print(output, end='')
    print('SYMBOL OK', path + '::' + symbol)
for path in [
    'reference/ai_delegation/test_check_order_precedence.py',
    'validation/2026-10-26-plan-aid-contract-map-partial-closure/README.md',
    'DECISION_REQUIRED.md',
]:
    p = subprocess.run(['git', 'cat-file', '-e', f'{sha}:{path}'], capture_output=True)
    assert p.returncode != 0, path
    print('BRANCH-ONLY ABSENT', path)
assert 'plan-plan-open-decisions-addendum-20261026-ai' not in Path('.aiops/program.json').read_text()
print(f'PRESENCE: {len(paths)} paths, {len(symbols)} symbols; 0 missing; 3 branch-only paths absent')

PY
```

Exit 0; final output:

```text
BRANCH-ONLY ABSENT reference/ai_delegation/test_check_order_precedence.py
BRANCH-ONLY ABSENT validation/2026-10-26-plan-aid-contract-map-partial-closure/README.md
BRANCH-ONLY ABSENT DECISION_REQUIRED.md
PRESENCE: 17 paths, 42 symbols; 0 missing; 3 branch-only paths absent
```

The first scratch version assumed every unqualified symbol was a function and
failed an assertion on the existing DENYLIST constant. Correction: check
DENYLIST as an assignment like CASES. Corrected pinned checks passed; the
record-consuming form above also passed with the same 17 paths / 42 symbols.
This was a validation-helper correction, not a missing artifact or source change.

### Owners copied verbatim

```sh
grep -nF 'Astra as contract/design authority, with User authorization of' /workspace/kix-run/wt/plan-plan-aid-contract-map-partial-closure/DECISION_REQUIRED.md
grep -nF 'any resulting scope/contract change and User merge.' /workspace/kix-run/wt/plan-plan-aid-contract-map-partial-closure/DECISION_REQUIRED.md
grep -nF 'Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.' docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md
for inventory_owner in 'User / supervisor (build host)' 'User (spend / environment); Astra (workload)' 'Supervisor / repository owner controlling the execution host' 'User / repository owner'; do
  grep -nF "$inventory_owner" docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md || exit
done
python3 - <<'PY'
from pathlib import Path
source = Path('/workspace/kix-run/wt/plan-plan-aid-contract-map-partial-closure/DECISION_REQUIRED.md').read_text()
owner = source.split('Who decides: ', 1)[1].split(' This is not', 1)[0]
owner = ' '.join(owner.split())
assert owner in Path('docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md').read_text()
print('SOURCE OWNER EXACT after joining source line wrapping:', owner)
PY
```

Exit 0. Actual matches:

```text
45:Who decides: Astra as contract/design authority, with User authorization of
46:any resulting scope/contract change and User merge. This is not an ASTRA
55:  Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.
docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:34:| L1 · `k-stage5-durable-tx` host | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User / supervisor (build host) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 1. |
docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:78:- `k-stage5-durable-tx` host — User / supervisor (build host): [ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행).
docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md:78:| L1 · `k-stage5-durable-tx` host | User / supervisor (build host) | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) |
docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:35:| L2 · `rs-4-l2` host | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User (spend / environment); Astra (workload) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 2. |
docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md:79:| L2 · `rs-4-l2` host | User (spend / environment); Astra (workload) | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) |
docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:40:| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) | Supervisor / repository owner controlling the execution host | STILL OPEN | — | Owner and options unchanged; see the linked supplement heading. |
docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md:80:| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` loopback host | Supervisor / repository owner controlling the execution host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) |
docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:42:| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | — | Owner and options unchanged. #276 delivered `plan-plan-register-index-sync-20261024`; its record names no disposition of this node. See the [#276 record](../../validation/2026-10-24-plan-register-index-sync/README.md). |
docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:81:- `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition — User / repository owner: [supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023).
docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md:81:| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | User / repository owner | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) |
SOURCE OWNER EXACT after joining source line wrapping: Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.
```

Source owner words and punctuation match exactly after joining the source's
physical line wrap. Carry-forward owners are the closure table cells, rather
than its shorter prose summaries.

### Locked blobs, reference snapshot and scope

```sh
set -e
python3 - <<'PY'
from pathlib import Path
import hashlib
import subprocess
def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()
expected = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
for path, blob in expected.items():
    actual = git('hash-object', path)
    assert actual == blob, (path, actual)
    print('LOCK OK', actual, path)
tree = git('rev-parse', 'HEAD:reference/v0.3-rc1')
assert tree == git('rev-parse', 'origin/main:reference/v0.3-rc1')
print('REFERENCE TREE', tree)
entries = [entry for entry in git('ls-tree', '-rz', 'HEAD', '--', 'reference/v0.3-rc1').split('\0') if entry]
for entry in entries:
    meta, path = entry.split('\t')
    assert git('hash-object', path) == meta.split()[2], path
print('REFERENCE BLOBS:', len(entries), 'compared; 0 changed')
protected = ['reference', 'docs/contracts', 'runtime', '.aiops', 'docs/tasks', '.github', 'scripts']
changed = git('diff', '--name-only', 'origin/main', '--', *protected)
assert not changed, changed
print('PROTECTED DIFF: empty')
source = Path('/workspace/kix-run/wt/plan-plan-aid-contract-map-partial-closure/DECISION_REQUIRED.md')
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == '24338c0753381529f3a9c00936dd8792130d8021cdef4ce0b60b9e8c6dae8e12'
print('SOURCE SHA256:', digest)
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], text=True)
expected_paths = {
    'docs/README.md',
    'docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md',
    'validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md',
}
actual_paths = {line[3:] for line in status.splitlines()}
assert actual_paths == expected_paths, actual_paths
print(status)
print('HEAD:', git('rev-parse', 'HEAD'))
PY
git diff --check
```

Exit 0. Actual output:

```text
LOCK OK 69564b166f0c27f9af5d8422f0a466b18d74c20f runtime/crates/kix-kernel/src/lib.rs
LOCK OK b607996c83a119c349f1cc90469ac1ba82764e20 runtime/crates/kix-kernel/tests/quarantine_capacity.rs
REFERENCE TREE a6ecb124dc2b2267ca6be19e39fbe2aef143074b
REFERENCE BLOBS: 108 compared; 0 changed
PROTECTED DIFF: empty
SOURCE SHA256: 24338c0753381529f3a9c00936dd8792130d8021cdef4ce0b60b9e8c6dae8e12
 M docs/README.md
?? docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md
?? validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md

HEAD: 957f75d75ea4854eba117d66d07663133f0b7b2c
```

The first scratch preservation helper read quoted `git ls-tree` paths as
literal names and failed on the Korean snapshot filename. Its Python traceback
was a failed verification attempt; the enclosing shell returned 0 because it
then ran `git diff --check`, so that shell exit was not counted as a pass.
The corrected command above uses `ls-tree -rz` and NUL separation, and
`set -e`; all 108 blobs passed. Nothing in the snapshot was edited.

### Deviations, limits and delivery state (AGENTS §14)

- A4 is included as a fourth still-open pointer because the October 25 closure
  lists it STILL OPEN; the supplied node objective named only three old stops.
  This explicit design-plan handling preserves the existing ledger.
- Fetch was NOT_RUN under the supervisor's explicit no-network rule, overriding
  AGENTS §1's fetch step. No remote freshness claim.
- G5 found eight cells by the prescribed rule, including the four named
  examples; the addendum lists all eight without narrowing the rule.
- No new tests; the new evidence is the attributed A5 ledger entry, owner
  preservation, mechanically selected per-option inventory and reproducible
  counts. Source findings retain their original attribution.
- Contract violation: existing source-reported class C actor-binding precedence
  remains open. No fix, option selection, new violation or new interpretation
  was introduced. Missing-grant binding remains UNDETERMINED with the source's
  Astra/User owner; this task does not expand the source semantics.
- Closest KTX equivalent for these documentation-only paths: workflow scope
  inspected, locked blobs verified before and after, and immutable reference
  tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` / 108 blobs compared to HEAD.
  Rust sources and dependencies are unchanged; no Cargo execution.
- Cargo, Move, ZK, Node/SDK, HTTP/loopback, host provisioning, stage5 acceptance,
  Sui localnet/testnet/mainnet and full production/runtime checks: NOT_RUN,
  outside touched paths and unnecessary for this documentary change.
- Exact-head KTX CI run ID/status/conclusion: NOT_RUN / unavailable;
  exact-head KIX protocol CI run ID/status/conclusion: NOT_RUN / unavailable.
  No hosted success transfers. No commit, push, PR, issue, comment, tag, branch
  mutation or merge performed; supervisor owns Git/GitHub.
- Implementation/final committed head: none created; unchanged HEAD
  `957f75d75ea4854eba117d66d07663133f0b7b2c` plus these uncommitted files.
  Merge commit / final-merge locks / post-merge main CI: N/A, not merged.
- Remaining uncertainty: remote freshness, owner choice and actual per-option
  edits, missing-grant interpretation, and the four earlier open decisions.
  Any implementation/contract revision needs a separate owner-authorized node;
  no next node is started here.
- READY means local documentary builder delivery only. No non-author review,
  Astra audit, merge readiness, production readiness, durability, distributed
  fencing, bank exactly-once, chain finality, legal compliance or complete
  protocol verification is claimed.

### Final file checks

After recording results, the docs-index and status-register checks were rerun:
exit 0 with the same counts above; protected-path diff stayed empty.
The initial `git diff --no-index --check /dev/null <new-file>` checks both
reported `new blank line at EOF` (exit 3). Both new files were normalized to
one final newline, then the commands below were rerun.

| Command | Exit | Result |
|---|---|---|
| `git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md` | 1 | No whitespace diagnostics; exit 1 denotes the expected new-file diff. |
| `git diff --no-index --check /dev/null validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md` | 1 | No whitespace diagnostics; exit 1 denotes the expected new-file diff. |
| `git diff --check` | 0 | No diagnostics. |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=254 indexed=219 allowlisted=35 |
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=385 ev_ids=15 original32=32 |
