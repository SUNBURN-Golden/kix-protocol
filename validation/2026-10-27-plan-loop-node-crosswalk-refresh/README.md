# Loop-node crosswalk refresh — 2026-10-27

Node: `plan-plan-loop-node-crosswalk-refresh-2026102`. Source: supplied KIX planner
run 1793083431; loop-proposed node, not in `.aiops/program.json`. Task document:
the immutable supervisor-provided node specification and read-only design in the
session; issue: none, no corresponding document under `docs/tasks/`.
Dependency: `plan-plan-plan-register-sync-20261027`, merged at #323
`4e3138c55b43d97ee6a8825ff6d1b743dd50ad14` by the exact branch-name observation.
Audit floor A2; astra_gate None; user_merge False. This is not ASTRA program mode.
Builder-authored documentary interpretation, not review, acceptance or a grade.

## Basis and boundary

Starting branch: `agent/kix-plan-plan-loop-node-crosswalk-refresh-2026102`.
Observed cached `origin/main`, task base and starting/current committed HEAD:
`4e3138c55b43d97ee6a8825ff6d1b743dd50ad14` (#323). Initial worktree clean;
local base delta zero. Fixed cutoff: that same SHA, inclusive. Lower bound:
#289 `22df2e96d1a7de4d0de371a1f64776e80af9d999`, exclusive, on its first-parent chain.
`git fetch origin main`: NOT_RUN under the supervisor's no-network instruction,
overriding AGENTS §1. Remote freshness is unverified. No base change.

`git rev-parse 4e3138c55b43d97ee6a8825ff6d1b743dd50ad14:.aiops/program.json`
returns `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`, equal to the historical program
blob. Working program bytes also hash to that blob; `.aiops/` is unchanged.

Implementation head and exact final task head: unassigned; uncommitted worktree
patch on the SHA above. The supervisor owns commits/publication and final-head
verification. No commit, push, reset, branch/tag mutation, GitHub/network action,
issue, PR, comment or merge was performed. No long job ran in the background.
KTX exact-head CI: run ID unavailable, NOT_RUN/not queried; KIX protocol
exact-head CI: likewise unavailable, NOT_RUN/not queried. Merge commit, merged
blob verification and post-merge main CI: N/A. READY means local builder handoff;
non-author exact-HEAD A2 review and both exact-head CI gates remain separate.

## Coverage mapped before adding evidence (AGENTS §7)

| Requirement | Existing coverage | Action / documented gap |
|---|---|---|
| Index/register consistency | Sufficiently covered by `check_docs_index.py` and `check_status_register.py`, plain/self-test | Reuse unchanged. |
| Roll-up/wiring consistency | Sufficiently covered structurally by `check_evidence_map_rollup.py` and `check_ci_checker_wiring.py`, plain/self-test | Reuse unchanged; full authoritative document block too. |
| Literal/equivalent selection, first-parent association, quoted specs/dependencies | Partially covered by historical crosswalk and October 25/27 sync records | New bounded inventory and manual artifact review; cutoff assertions below. |
| New range accounting, cumulative counts and original byte preservation | Not covered for #290–#323 | Nine rows, 25 accounting entries, empty absent-number complement; reproducible verifier below. |
| Scope/locks/reference/program preservation | Sufficiently covered by direct Git/blob/file-set comparisons | Verify bytes and modes, including untracked/ignored protected additions. |
| Remote freshness, independent review, hosted CI | Not covered here | Supervisor follow-up; no local substitution claim. |

No runtime test or persistent helper is added. The new evidence is the appended
crosswalk and the embedded one-time assertions. Prior sections remain the exact
cutoff byte prefix, including all historical rules, rows, accounting and decisions.

## Selection provenance and counts

Unchanged predicate on each cutoff `validation/*/README.md`:
``'not in `.aiops/program.json`' in ' '.join(text.split())``.
The full cutoff tree, excluding this new record, contains **61 literal matches**
and three equivalent-statement selections (#264, #274, #298): **64 rows**.
Previously 55 rows; **nine added = eight literal + one equivalent**.
The bounded range contains **34 merges, 25 nonmatches, zero absent PR numbers**.
Every nonmatch has its own path and full merge SHA in the appended accounting
table. Absence means absence only from this bounded history.

Exact text below is quoted after whitespace normalization; source paths are
associated with merges by their first-parent diff, not by directory date. Own
node IDs are copied from each record's identity, not embedded historical quotes.

| PR | Cutoff validation record | Selection quotation | Own node ID |
|---|---|---|---|
| #290 | `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md` | not in `.aiops/program.json` | `plan-plan-register-index-crosswalk-sync-20261` |
| #298 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md` | loop-proposed, absent from `.aiops/program.json` | `plan-plan-open-decisions-addendum-20261026-ai` |
| #301 | `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md` | not in `.aiops/program.json` | `plan-plan-ci-checker-wiring-guard` |
| #302 | `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md` | not in `.aiops/program.json` | `plan-plan-rs4-l2-option-impact-inventory` |
| #314 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md` | 1792916405; loop-proposed node, not in `.aiops/program.json`. | `plan-plan-open-decisions-closure-20261027` |
| #319 | `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md` | not in `.aiops/program.json` | `plan-plan-perf-harness-kernel-construction-co` |
| #320 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md` | not in `.aiops/program.json` | `plan-v5-kernel-only-contract-invariant-histor` |
| #321 | `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md` | not in `.aiops/program.json` | `plan-ci-test-suite-discovery-guard` |
| #323 | `validation/2026-10-27-plan-register-sync-20261027/README.md` | not in `.aiops/program.json` | `plan-plan-plan-register-sync-20261027` |

#314's quotation is historical #290 text embedded in its own README; this still
qualifies under the unchanged rule, like earlier #210/#272/#281.
#306 has no qualifying statement in its README; its SDK status addendum and the
README's recorded empty grep result do not select it. #313 names a canonical
closeout overlap but has no absence statement; it remains accounting-only.
Nonmatches were read for equivalent explicit absence statements; only #298
adds one. Earlier #264 and #274 equivalents retain their historical evidence.

## Manual overlap interpretation

- #290/#323: plan/register pointer artifacts fit `roadmap-sync` and
  `k-current-capability-map`; the full specs are not discharged.
- #298/#302/#314: A5, RS-4 measurement-gap and seven-stop inventories fit the
  gap-to-node portion of `k-local-program-closeout`'s “local delivery packet과
  gap-to-node 지도”. They are partial artifact overlaps, not full delivery packets.
- #302: the inventory's missing/open measurement cells fit
  `k-benchmark-reproduction`'s “안전성 중단 조건과 측정 누락 표”. No new safety-stop
  execution, measurement or option selection is implied.
- #319: counted construction/reset reporting and JSON assertions fit the
  report-template portion of “실측 재실행 packet과 보고서 template”. The suggested
  missing-measurement phrase was also inspected: unchanged PARTIAL/NOT_RUN
  procedures remain gaps, but the counter itself supplies no new safety-stop
  table. This narrower phrase avoids attributing that artifact to the counter.
- #314: SD1's unresolved check-order decision requirement fits
  `contract-compatibility-profile`'s “with explicit decisions for
  breaking/undetermined semantics”. No decision, semantic vector, compatibility
  implementation or qualification is supplied; #306 is accounting-only.
- #320: seed/replay histories fit `k-adversarial-corpus`'s “seed와
  shrinking/replay 입력을 저장한다”; no shrinking or independent oracle is claimed.
- #301/#321: no canonical artifact overlap identified by the builder; textual
  CI guards do not themselves fulfill corpus or protocol acceptance.

Canonical `depends_on` lists are copied from cutoff JSON, not the loop inputs.
Only `k-stage4-local-exploration` among these dependencies has an exact matching
first-parent branch merge: #122 `8dc60dfee3816864f4f45394ff31bb8070e76274`.
All other named dependencies are not determinable from this tree under the
existing branch-name rule. A missing branch match is not proof of non-merge;
a match is not acceptance. All effect cells say
“does not complete or start the canonical node”.

## Reproduction

Run from repository root. Git commands are local/read-only. Selection enumerates
cutoff objects using NUL-delimited paths and `git show`; it never counts the
new delivery README. The verifier also confirms the exact one-line index insertion,
all earlier crosswalk bytes, current JSON specs/dependencies, path scope, locked
hashes, and reference/program file sets/bytes/modes. It performs no mutation.

```sh
export PYTHONDONTWRITEBYTECODE=1
cutoff=4e3138c55b43d97ee6a8825ff6d1b743dd50ad14
git rev-parse origin/main HEAD
git rev-parse "$cutoff:.aiops/program.json"
git log --first-parent --merges --reverse --format='%H %s'   "22df2e96d1a7de4d0de371a1f64776e80af9d999..$cutoff"
git diff --unified=0 "$cutoff" -- docs/status/LOOP_NODE_CROSSWALK.md
```

Save the following block to `/tmp/kix-crosswalk-verify.py`, then run
`PYTHONDONTWRITEBYTECODE=1 python3 /tmp/kix-crosswalk-verify.py`:

```python
import json, os, re, stat, subprocess
from pathlib import Path

CUTOFF = '4e3138c55b43d97ee6a8825ff6d1b743dd50ad14'
LOWER = '22df2e96d1a7de4d0de371a1f64776e80af9d999'
PROGRAM = 'ff0f39a8129ca8b8d30818cce35c3d4e588872fc'
CROSSWALK = 'docs/status/LOOP_NODE_CROSSWALK.md'
RECORD = 'validation/2026-10-27-plan-loop-node-crosswalk-refresh/README.md'

def git(*args):
    return subprocess.check_output(['git', *args])

def norm(text):
    return ' '.join(text.split())

def rows(text):
    return [line.split('|')[1:-1] for line in text.splitlines()
            if re.match(r'^\| #\d+ \|', line)]

assert git('rev-parse', 'origin/main', 'HEAD').decode().split() == [CUTOFF]*2
assert LOWER in git('rev-list', '--first-parent', CUTOFF).decode().split()
paths = git('ls-tree', '-r', '--name-only', '-z', CUTOFF).decode().split('\0')
records = {p: git('show', f'{CUTOFF}:{p}').decode() for p in paths
           if re.fullmatch(r'validation/[^/]+/README.md', p)}
literal = {p for p, t in records.items() if 'not in `.aiops/program.json`' in norm(t)}
assert len(literal) == 61
equivalents = {
    'validation/2026-10-23-owner-stop-handoff-addendum/README.md':
        'Loop-proposed, absent from `.aiops/program.json`',
    'validation/2026-10-23-rs-map-gap-closure-batch-2/README.md':
        'loop-proposed and absent from `.aiops/program.json`',
    'validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md':
        'loop-proposed, absent from `.aiops/program.json`',
}
for path, quotation in equivalents.items():
    assert path not in literal and quotation in norm(records[path])
assert len(literal | equivalents.keys()) == 64
assert RECORD not in records
inventory = {}
for line in git('log', '--first-parent', '--merges', '--reverse', '--format=%H %s',
                f'{LOWER}..{CUTOFF}').decode().splitlines():
    sha, subject = line.split(' ', 1)
    pr = int(re.search(r'Merge pull request #(\d+) ', subject)[1])
    assert pr not in inventory
    changed = git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z',
                  sha+'^1', sha).decode().split('\0')
    found = [p for p in changed if p in records]
    assert len(found) == 1, (pr, found)
    inventory[pr] = (sha, found[0], subject)
assert len(inventory) == 34
absent = set(range(290, max(inventory)+1)) - inventory.keys()
assert absent == set()
selected = {pr for pr, (_, p, _) in inventory.items() if p in literal}
assert selected == {290, 301, 302, 314, 319, 320, 321, 323}
equivalent_path = inventory[298][1]
assert 'loop-proposed, absent from `.aiops/program.json`' in norm(records[equivalent_path])
selected.add(298)
old = git('show', f'{CUTOFF}:{CROSSWALK}')
new = Path(CROSSWALK).read_bytes()
assert new[:len(old)] == old
append = new[len(old):].decode()
assert append.startswith('\n## 5. Refresh recorded 2026-10-27')
selected_part, accounting_part = append.split('### Refresh accounting —', 1)
accounting_part = accounting_part.split('### Overlap limits', 1)[0]
selected_rows, account_rows = rows(selected_part), rows(accounting_part)
selected_prs = [int(c[0].strip()[1:]) for c in selected_rows]
account_prs = [int(c[0].strip()[1:]) for c in account_rows]
assert len(selected_prs) == len(set(selected_prs)) == 9
assert len(account_prs) == len(set(account_prs)) == 25
assert set(selected_prs) == selected
assert set(account_prs).isdisjoint(selected)
assert set(account_prs) | selected == inventory.keys()
# If absent numbers ever exist, their rows must be explicitly accounted for.
assert set(account_prs) - inventory.keys() == absent
program = json.loads(git('show', f'{CUTOFF}:.aiops/program.json'))
nodes = {n['id']: n for n in program['nodes']}
history = git('log', '--first-parent', '--merges', '--format=%H %s', CUTOFF).decode().splitlines()
for cells in selected_rows:
    pr = int(cells[0].strip()[1:])
    sha, record, subject = inventory[pr]
    assert cells[1].strip() == f'`{sha}`'
    own_id = cells[2].strip().strip('`')
    assert own_id in records[record][:600], (pr, own_id)
    assert subject.endswith('/agent/kix-'+own_id)
    assert cells[5].strip() == 'does not complete or start the canonical node'
    overlaps = re.findall(r'`([^`]+)`: "([^"]+)"', cells[3])
    if not overlaps:
        assert cells[3].strip() == 'none identified by the builder'
        assert cells[4].strip() == 'n/a'
    for node_id, phrase in overlaps:
        assert norm(phrase) in norm(nodes[node_id]['spec'])
        deps = nodes[node_id].get('depends_on', [])
        assert f'`{node_id}` depends_on ' in cells[4]
        segment = cells[4].split(f'`{node_id}` depends_on ', 1)[1]
        segment = re.split(r'; `[^`]+` depends_on ', segment)[0]
        actual_deps = re.findall(r'`([^`]+)` \(', segment)
        assert actual_deps == deps, (pr, node_id, actual_deps, deps)
        if not deps:
            assert segment.strip() == 'none'
        for dep in deps:
            hits = [l for l in history if l.endswith('/agent/kix-'+dep)]
            if hits:
                merge, sub = hits[0].split(' ', 1)
                number = re.search(r'#(\d+)', sub)[1]
                assert f'merged: branch `agent/kix-{dep}` at #{number} `{merge}`' in segment
            else:
                assert f'not determinable from this tree: no first-parent merge of branch `agent/kix-{dep}`' in segment
for cells in account_rows:
    pr = int(cells[0].strip()[1:])
    sha, record, _ = inventory[pr]
    assert f'`{sha}`' in cells[1] and f'`{record}`' in cells[1]
    assert record not in literal
# Count only effect-bearing rows, not accounting tables.
effect = ' | does not complete or start the canonical node |'
assert sum(l.endswith(effect) for l in old.decode().splitlines()) == 55
assert sum(l.endswith(effect) for l in new.decode().splitlines()) == 64
assert 'agent/kix-plan-plan-plan-register-sync-20261027' in inventory[323][2]
assert git('rev-parse', f'{CUTOFF}:.aiops/program.json').decode().strip() == PROGRAM
assert git('hash-object', '.aiops/program.json').decode().strip() == PROGRAM
assert git('diff', CUTOFF, '--', '.aiops/', 'reference/v0.3-rc1/') == b''
locks = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
for path, expected in locks.items():
    assert git('hash-object', path).decode().strip() == expected
# Include on-disk file sets (even ignored additions), bytes, and executable modes.
for root in ['reference/v0.3-rc1', '.aiops']:
    entries = {}
    for entry in git('ls-tree', '-r', '-z', CUTOFF, root).split(b'\0'):
        if not entry:
            continue
        meta, path = entry.split(b'\t', 1)
        mode, kind, blob = meta.decode().split()
        entries[path.decode()] = (mode, blob)
    disk = {str(p) for p in Path(root).rglob('*') if p.is_file() or p.is_symlink()}
    assert disk == set(entries)
    for path, (mode, blob) in entries.items():
        assert git('hash-object', path).decode().strip() == blob
        assert ('100755' if os.stat(path).st_mode & 0o111 else '100644') == mode
expected_paths = {CROSSWALK, 'docs/README.md', RECORD}
changed = set(filter(None, git('diff', '--name-only', CUTOFF).decode().splitlines()))
untracked = set(filter(None, git('ls-files', '--others', '--exclude-standard').decode().splitlines()))
assert changed | untracked == expected_paths, (changed, untracked)
for path in expected_paths:
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o644
old_index = git('show', f'{CUTOFF}:docs/README.md').decode()
index = Path('docs/README.md').read_text()
added = [l for l in index.splitlines(keepends=True) if f'../{RECORD}' in l]
assert len(added) == 1
assert index.replace(added[0]+'\n', '', 1) == old_index
subprocess.run(['git', 'diff', '--check'], check=True)
ws = subprocess.run(['git', 'diff', '--no-index', '--check', '/dev/null', RECORD], capture_output=True)
assert ws.returncode in (0, 1) and not ws.stdout and not ws.stderr
print('PASS: 34 merges = 9 selected + 25 accounted; absent=[]; literal=61; equivalent=3; cumulative=64')
print('PASS: original crosswalk bytes; one index line; canonical specs/dependencies; program; locks; reference/.aiops file sets, bytes, modes; exact three paths; whitespace')
```

## Complete changed paths

- `docs/status/LOOP_NODE_CROSSWALK.md` — append §5, preserving the original bytes.
- `docs/README.md` — one validation-index bullet.
- `validation/2026-10-27-plan-loop-node-crosswalk-refresh/README.md` — this record.

## Commands and actual results

Python actually used: 3.13.5. The workflow's document block uses available
`python3`; no interpreter qualification or complete hosted-workflow equivalence
is inferred. No earlier-SHA CI result is transferred. These paths fall within
the workflows' documentation classification when event/base conditions hold;
KTX's heavy checks are conditional on that classification. No Cargo, runtime,
Node, network, host provisioning or separate rights-scale job was run.

Narrow checks ran first, sequentially, stopping on failure:

| Command | Actual result |
|---|---|
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=290 indexed=255 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=452 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=32 plain=31 self_test=32 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |

The foreground runner `/tmp/kix-crosswalk-checks.py offline` extracted the exact
unguarded **Stdlib offline document checks** block from the checked-out
`.github/workflows/protocol.yml`. It asserted 57 commands, ran each in sequence
with stop-on-first-failure, and kept `check_stage5_host.py --self-test` only.
All 57 exited 0. This is the closest local CI equivalent for the touched paths;
it is not a complete workflow result.

Reproduce the same runner by saving the following to
`/tmp/kix-crosswalk-checks.py`; run `python3 /tmp/kix-crosswalk-checks.py narrow`
then `python3 /tmp/kix-crosswalk-checks.py offline` (logs stay under `/tmp`):

```python
import json,os,subprocess,sys
from pathlib import Path
phase=sys.argv[1];env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
if phase=='narrow':
 commands=[f'python3 scripts/{name}.py{arg}' for name in ['check_docs_index','check_status_register','check_evidence_map_rollup','check_ci_checker_wiring'] for arg in ['', ' --self-test']]
else:
 lines=Path('.github/workflows/protocol.yml').read_text().splitlines()
 start=next(i for i,l in enumerate(lines) if l.strip()=='- name: Stdlib offline document checks')
 end=next(i for i in range(start+1,len(lines)) if lines[i].startswith('      - '))
 step=lines[start:end];assert not any(l.lstrip().startswith('if:') for l in step)
 run=next(i for i,l in enumerate(step) if l.strip()=='run: |')
 commands=[l[10:] for l in step[run+1:] if l.strip()]
 assert len(commands)==57,len(commands)
 assert 'python3 scripts/check_stage5_host.py --self-test' in commands
 assert 'python3 scripts/check_stage5_host.py' not in commands
results=[]
for command in commands:
 r=subprocess.run(command,shell=True,executable='/bin/bash',env=env,text=True,capture_output=True)
 results.append({'command':command,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 print(command,'->',r.returncode,flush=True)
 Path(f'/tmp/kix-crosswalk-{phase}-results.json').write_text(json.dumps(results,indent=2))
 if r.returncode:
  print(r.stdout,r.stderr);sys.exit(r.returncode)
print(f'PASS: {len(results)} {phase} commands, all exit 0')
```

| Exact offline-block command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=452 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=290 indexed=255 allowlisted=35 |
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
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (85 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=32 plain=31 self_test=32 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test: pass (18 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Other executed commands and verification:

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse origin/main HEAD` | Exit 0; expected worktree/branch, initially clean, both refs equal cutoff. |
| `git log --first-parent --merges --reverse --format='%H %s' 22df2e96d1a7de4d0de371a1f64776e80af9d999..origin/main` | Exit 0; 34 merges #290–#323; none absent. |
| `git ls-tree -r --name-only -z <cutoff>`; `git show <cutoff>:<record>`; `git diff-tree --no-commit-id --name-only -r <merge>^1 <merge>` (initial inventory; NUL-delimited diffs in verifier) | Exit 0; cutoff record selection and one record associated with every bounded merge. |
| Inline Git/JSON dependency inspection | Initial diagnostic: exit 1, `KeyError: depends_on`; corrected inspection exit 0 with omitted dependency list treated as empty. Exact branch results as above. |
| `python3 /tmp/kix-crosswalk-edit.py`; `python3 /tmp/kix-crosswalk-record.py` | Exit 0; two document edits and validation record created; temporary scripts are outside delivery. Later inline Python updated this record and its embedded assertions/results. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/kix-crosswalk-verify.py` | Exit 0, initial and final runs; 34 = 9 selected + 25 accounted, absent=[], literal=61, equivalent=3, cumulative=64; all byte/spec/dependency/path/mode/whitespace assertions pass. Final run extracts the embedded verifier, avoiding a divergent temporary copy. |
| `git diff --unified=0 origin/main -- docs/status/LOOP_NODE_CROSSWALK.md` (saved to `/tmp/kix-crosswalk-append.diff`) | Exit 0; one EOF hunk, `@@ -192,0 +193,65 @@`; zero removed content lines. Original 192-line byte prefix preserved. |
| `git rev-parse origin/main:.aiops/program.json`; `git hash-object .aiops/program.json` (latter inside verifier) | Exit 0; both `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`, equal to historical blob. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after and final verifier) | Exit 0; before and after respectively `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`; both required values match. |
| `git rev-parse origin/main:reference/v0.3-rc1` | Exit 0; baseline tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git diff --quiet origin/main -- .aiops/ reference/v0.3-rc1/` | Exit 0; empty diff. Embedded verifier additionally checks every protected working byte, executable mode and complete file set including ignored additions. |
| `git diff --check` | Exit 0; clean. |
| `git diff --no-index --check /dev/null validation/2026-10-27-plan-loop-node-crosswalk-refresh/README.md` (inside verifier) | Exit 1 for the new-file comparison, no stdout/stderr: no whitespace diagnostics. |
| `git diff --name-only <cutoff>` and `git ls-files --others --exclude-standard` (inside verifier); `git status --short --untracked-files=all`; `git diff --stat` | Exit 0; exactly the three documented paths, all mode 100644. |
| `rg --files --hidden -g AGENTS.md -g '!.git'`; `cat`, `sed`, `rg` and inline read-only inspection | Exit 0 for final governance discovery; only root AGENTS.md found. Governance, task-named records, source/spec text and workflow definitions inspected; no network lookup. |
| `python3 --version` | Exit 0; Python 3.13.5. |

The two locked files and `reference/v0.3-rc1/**` were never edited or transiently
mutated. The reference and `.aiops/` comparisons are against the fixed cutoff,
with tracked bytes/modes and complete on-disk file sets verified.

## Deviations and limits

Fetch omitted under the explicit supervisor prohibition. No implementation
scope deviation. #323 is the verified cutoff and prerequisite merge; #314's
quoted selection and #306's nonselection follow the supplied design. For #319,
the narrower report-template phrase is used as explained above. An exploratory
dependency inspection initially raised `KeyError: depends_on` for `roadmap-sync`;
the corrected read uses an empty list for its omitted field, consistent with
the historical crosswalk. No repository change was needed for that diagnostic.

No new contract violation or undefined semantics was established by this
textual task. Historical A5/SD1 class C reports and #320 class B characterization
remain attributed to their source records; their reproductions were not run.
Canonical counting remains `DECISION_REQUIRED · Astra`. Original owners,
`UNDETERMINED` values, stops, node scopes and grades are unchanged. No canonical
node is completed or started. No runtime, benchmark, production, funds, provider,
chain, durability or clean-room independence result is claimed. The protocol's
separate rights-scale job and Rust/heavy steps are outside this document-only
local verification. Remote freshness, final-head CI and non-author review remain
unverified; no merge is proposed. Further canonical acceptance needs its owner's
separate decision and evidence; it is not follow-up work authorized by this node.
