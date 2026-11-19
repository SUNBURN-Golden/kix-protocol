# Audit #29 capability pointer refresh — builder evidence

Node/task ID: `audit29-refresh-current-capability-pointers`. Task document:
the supervisor's inline node specification and read-only design plan in this
session; no issue or corresponding file under `docs/tasks/` exists.
Source: KIX audit #29, supplied external task input
/workspace/kix-run/audits/audit_29_20261110.md. Design provenance: supplied
Claude CLI Sonnet 5.5 xhigh read-only plan. Not ASTRA program mode.
Audit floor A2; Astra gate none; single writer, no delegated agents.

The patch adds ten navigation entries to each of three documents, covering exactly
PRs #416–#425. It does not inventory #399–#415, implement the separate consumer
boundary-map node, adopt integration recommendations or completion estimates,
or promote qualification, grades, coverage or canonical completion.
Operational capability count remains **0**, semantic consumers **HOLD**,
unsupported bindings **NOT_BOUND**. Policy/legal/accounting owners are unchanged.

## Basis and delivery evidence

Audit cutoff identity supplied by the audit: `8a8a0fc` only. Subsequently
observed local starting HEAD/base and cached origin/main:
`8a8a0fca7057b617235cf20cb28c8698be1a1f73`, branch
`agent/kix-audit29-refresh-current-capability-pointers`.
The worktree was initially clean; no local base delta or base change.
Fetch NOT_RUN under the later explicit supervisor no-network instruction;
current remote main is unverified. The full SHA is a builder observation, not
a claim that the audit itself established it.

Implementation/final committed task head: unavailable; changes remain uncommitted
on the starting HEAD. No merge occurred: merge SHA, final-merge blob verification
and post-merge main CI are not applicable.

| Delivery gate | Run ID / status / conclusion |
|---|---|
| Exact-final-head KTX kernel verification | unavailable / NOT_RUN / unavailable |
| Exact-final-head KIX protocol verification | unavailable / NOT_RUN / unavailable |
| A2 non-author exact-final-head review | pending supervisor delivery; no reviewer identity or approval claimed |
| Post-merge main CI | not applicable; no merge |

The supervisor owns commits and GitHub publication. No commit, push, reset,
branch/tag mutation, PR, issue, comment, ASTRA marker or GitHub/network action was
performed. READY denotes local handoff, not merge readiness or merge authority.
No historical CI success transfers to the eventual final head.

## Complete changed-path list

- [Development plan](../../docs/DEVELOPMENT_PLAN.md): one dated insertion at the
  end of §5's location records, before §6.
- [Capability register](../../docs/status/CURRENT_CAPABILITY_REGISTER.md): appended
  supplement connecting existing EV-BRA/P Wave4, EV-REF/B03/F03 and TL rows.
- [Loop-node crosswalk](../../docs/status/LOOP_NODE_CROSSWALK.md): appended §7 using
  this task's explicit selection; earlier literal-selection rules/totals preserved.
- This validation README: provenance, reconciliation, commands and limitations.

The existing [docs index](../../docs/README.md) already links all ten historical
records. The new record is indexed from DEVELOPMENT_PLAN, supported by the
existing checker. No index edit, runtime helper or behavioral test is needed.

## Existing coverage mapping

Inspected before adding evidence; no behavioral tests added or duplicated.

| Requirement | Existing coverage | Assessment / bounded task evidence |
|---|---|---|
| Register paths, EV references, original32 uniqueness | check_status_register.py and self-test | Sufficient for supported path forms; original grades and first-column IDs preserved |
| Index/validation reachability | check_docs_index.py and self-test | Sufficient; ten historical records already indexed, new record reached from plan |
| Exact ten-PR inventory and node/source/test/record identity | Existing index and builder records | Partially covered; assertions check three exact ten-row sets, record identity, merge branch IDs and indexed links |
| Cited symbols, canonical overlap/dependencies | Existing source/test files and read-only program spec | Partially covered; AST checks symbols, normalized spec substrings and exact depends_on; acceptance not assessed |
| Historical snapshots, locks, grades/HOLD/owners | Fixed base and pre-edit SHA-256 snapshot | Not covered by checkers alone; compare every original document byte and every other tracked input |
| Touched-path CI | Protocol stdlib block and KTX path classifier | Four narrow checks followed by 63 workflow commands; four paths qualify as documentation-only |

The register uses Markdown reference links because the existing checker interprets
inline targets from repository root. Bounded assertions resolve every added link
relative to its document, including anchors. The checker itself is unchanged.

## Ten-PR reconciliation

Merge SHAs below were read from local first-parent history with
`git log --first-parent --merges -12 --format='%H %s'` and its latest ten
checked by the bounded assertion. They were not inferred from directory dates or
preceding builders' base SHAs. No GitHub merger identity, reviewed head or CI
result was queried. Merge observations do not establish canonical acceptance.

| PR | Local first-parent merge SHA | Exact node ID |
|---|---|---|
| #416 | `0afb7c199acb880ed7a1972d261f92ff9244d8d7` | `plan-local-recorded-ticket-console` |
| #417 | `f0eab3e083f9ca317482ea10576c4605364fd51b` | `plan-plan-local-bundle-quote-composer` |
| #418 | `9ad388b2cf04a8eadc820e28e6098371e2accf5b` | `plan-local-reward-source-composer` |
| #419 | `f5fe55278e71e0ff3158f639626a4f138321cc8c` | `plan-plan-local-pool-accounting-workbench` |
| #420 | `c2aa970f7d95bd569f2a8eb40218cbc4c5d33b6b` | `plan-local-refund-line-picker` |
| #421 | `992bb392a890508ce8736fc5c63159de789c53ea` | `plan-local-pool-opening-composer` |
| #422 | `25e7f2ebaa08e3688a92b36ad3025325b5011d84` | `plan-local-pool-live-console` |
| #423 | `e5b7927bca2ec78a0a6618d4ac3d1d5611a0b95d` | `plan-local-supply-live-console` |
| #424 | `61e581acb3c702dafa145ab0e9e96996cc2e0be2` | `plan-local-commerce-decimal-entry` |
| #425 | `8a8a0fca7057b617235cf20cb28c8698be1a1f73` | `plan-local-pool-guided-live-init` |


Each supplement row links source, existing tests and historical validation.
Doubled plan-plan- prefixes are preserved. Overlap is a builder interpretation:

| PRs | Canonical artifact comparison | Declared depends_on (acceptance not assessed) |
|---|---|---|
| #416 | booking-resale-admission-deepening: reference/interface artifacts only | p-sdk-0 |
| #417, #420, #424 | k-stage6-economics-reference: existing quote/bundle/refund calculation artifacts only | k-stage5-durable-tx; settlement-policy-deepening; booking-resale-admission-deepening |
| #418, #419, #421, #422, #423, #425 | tl-3-offchain: existing reward/pool/V6 model tooling only | tl-1 |

Every supplement row states “does not complete or start the canonical node.”
Reused TL-4 tests are builder coverage, not independent verification.
Calculations stay CALCULATION_ONLY with refund executionAuthorized=false.
Reward source snapshots are unauthenticated assertions. Pool references are not
deduplication keys: accepted repetitions append again. Supply alarms and
stop_payout execute nothing; live means local subprocess.

Historical records retain unavailable Rust checks, reward-harness deadline
failures/reruns and [#423's fix-round-1 evidence](../2026-11-10-plan-local-supply-live-console/README.md#pr-fix-round-1--reconciliation-response-correlation).
That later evidence checks response offchain_supply against submitted layer_supply;
the original run is not relabeled as covering the correction. None of those
historical behavioral tests was rerun in this documentation task.

## Commands actually run and results

Repository root, foreground only; no downloads or background jobs. Read-only
inspection used cat, sed, rg, Git object/history reads and Python JSON/AST reads.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; expected branch; HEAD and cached ref match basis |
| `git log --first-parent --merges -12 --format='%H %s'` | All ten requested merges present; preceding #414/#415 excluded |
| `git rev-parse HEAD:.aiops/program.json` | ff0f39a8129ca8b8d30818cce35c3d4e588872fc |
| Pre-edit `python3.12 -B -` SHA-256 capture of `git ls-files -z` | Captured 2,850 tracked inputs, including 108 frozen reference files, to /tmp before edits |
| Python git hash-object calls before edits; `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` after edits | Both required blobs match before/after; values below |
| First `python3.12 -B scripts/check_status_register.py` (before link correction) | Exit 1: origin/main treated as nonexistent path; document-relative inline targets ambiguous; remaining chained narrow checks did not run |
| First `python3.12 -B /tmp/audit29-check.py` | Exit 1: diagnostic assumed #423 had a Node line; corrected to accept its exact-ID heading |
| Corrected `python3.12 -B /tmp/audit29-check.py` | Exit 0: three sets of ten unique rows; 46 link targets, 8 cited symbols; identity/spec/dependency/anchor and preservation assertions pass |
| `python3.12 -B /tmp/audit29-run-checks.py` | Exit 0: four narrow + 63 workflow invocations below; runner and guard reproduced below |
| `git diff --check` | Exit 0; whitespace clean |

### Narrow checks — Python 3.12.15

| Command | Actual result |
|---|---|
| `python3.12 -B scripts/check_status_register.py` | Exit 0; paths=575, ev_ids=15, original32=32 |
| `python3.12 -B scripts/check_status_register.py --self-test` | Exit 0; PASS |
| `python3.12 -B scripts/check_docs_index.py` | Exit 0; scanned=388, indexed=353, allowlisted=35 |
| `python3.12 -B scripts/check_docs_index.py --self-test` | Exit 0; PASS |

### Protocol stdlib block — workflow python3 resolves to 3.13.5

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; paths=575, ev_ids=15, original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; PASS |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; PASS |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=388, indexed=353, allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; PASS |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; PASS |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; PASS |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; PASS |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; PASS |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; PASS |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_class_b_index.py` | Exit 0; PASS |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; PASS |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; PASS |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_loopback_host.py` | Exit 0 reporting mode; all_ok=false: guard blocked socket creation and isolated child launch; no host qualification |
| `python3 scripts/check_loopback_host.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0 reporting mode; 7/18 archives present, 11 missing including bcs 0.2.1; no compilation claim |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; PASS |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; PASS |


The exact workflow command list was extracted, not approximated. Stage-5 ran only
its self-test; plain host evaluation was NOT_RUN. A network guard prevented real
socket creation and blocked the isolated loopback child before launch. The report
has host_selected=false, permission_granted=false, gate_suite_run=false.
It describes restricted execution, not unrestricted host availability.
Cache presence is a local observation; missing archives do not fail its plain
report invocation. No Rust compilation/test success is claimed.

The four changed paths meet the KTX documentation-only classifier. Rust
compilation, Clippy, formatting sweeps, Move/ZK/runtime suites and artifact
generation are unnecessary for this patch and NOT_RUN. Protocol's separate
rights-scale job and exact-head workflows remain hosted requirements; these
documentation checks do not substitute for them.

## Preservation, findings and non-claims

Final checks after writing this report repeated the bounded assertions, both
narrow checkers and their self-tests, followed by whitespace validation:

| Command | Actual result |
|---|---|
| `python3.12 -B /tmp/audit29-check.py` | Exit 0; 30 rows, 46 link targets, 8 symbols; protected bytes, file modes, authorized paths and original refs match |
| `python3.12 -B scripts/check_status_register.py` and `--self-test` | Both exit 0; 575 paths, 15 EV IDs, original32=32 |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both exit 0; scanned=388, indexed=353, allowlisted=35 |
| `git diff --check` | Exit 0 |

| Protected input | Before and after |
|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 |
| reference/v0.3-rc1/** | All 108 tracked files byte-identical |
| Other tracked inputs outside the three supplemented documents | All 2,847 byte-identical to base and pre-edit snapshot |
| Historical text in the three documents | Byte-identical after removing only additions; grades, owners, HOLD states, counts and selection rules retained |
| .aiops/, docs/tasks/, contracts, CI, historical validation records | Unchanged; no transient mutation |

No new explicit contract violation or contract-undefined semantics were found or
assigned. Existing [SD1 verifier check-order violation](../../docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md),
[A5 stop](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md),
[RS L2 FAILED_MEASUREMENT/HOLD](../../docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md)
and [Stage-5 gates](../../docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md)
remain with their recorded owners. Existing pool repetition and supply
unapproved-cause precedence characterizations are unchanged. No SDK semantic
qualification or clean handoff through those stops is supplied here.

No hardware/equipment, paid service, credentials, production runtime, public
endpoint, real funds/PG/bank/KYC, Sui testnet/mainnet, coin/TIX, storage engine,
replication, consensus, policy value or new protocol command was needed.
No durability, distributed fencing, bank exactly-once, chain finality, legal
compliance, production readiness or clean-room independence is tested or claimed.
No STOP condition was triggered; DECISION_REQUIRED.md was not needed.

## Deviations and remaining uncertainty

- Startup fetch omitted under the supervisor's explicit no-network instruction;
  remote freshness unverified. No rebase or base change.
- Reference-link formatting accommodates existing checker behavior; bounded
  assertions validate these links directly. No checker/CI change or substantive
  design deviation.
- Workflow commands retain exact python3 invocations (3.13.5 here); narrow checks
  use requested Python 3.12.15. Network guard restricts the loopback report;
  unrestricted host probes and hosted CI are unavailable.
- Initial diagnostic assertion rejected #423's heading format and was corrected;
  it did not reveal a repository defect.

Remaining supervisor work: assign final committed head, obtain A2 non-author
exact-HEAD review and required exact-head KTX/KIX workflow results. Publication
and User-only merge rules remain unchanged; no additional feature/policy work
is added to this node.

## Reproduction

Save the bounded assertion below as /tmp/audit29-check.py, then run
`python3.12 -B /tmp/audit29-check.py` from this uncommitted worktree.
It checks the immutable original base and exactly four authorized changed paths.
If the actual pre-edit /tmp snapshot is available it also checks that snapshot;
otherwise immutable-base comparison still runs. After supervisor commit, only
the handoff-state assertions need adaptation outside this builder session.

```python
"""Bounded documentary assertions; no behavioral or qualification claim."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

BASE = '8a8a0fca7057b617235cf20cb28c8698be1a1f73'
PLAN = 'docs/DEVELOPMENT_PLAN.md'
REGISTER = 'docs/status/CURRENT_CAPABILITY_REGISTER.md'
CROSSWALK = 'docs/status/LOOP_NODE_CROSSWALK.md'
RECORD = 'validation/2026-11-10-audit29-refresh-current-capability-pointers/README.md'
HEADINGS = {
    PLAN: '### 2026-11-10 audit #29 — bounded current-tree location supplement',
    REGISTER: '## Audit29 current-tree supplement',
    CROSSWALK: '## 7. Audit29 current-tree supplement',
}


def git(*args):
    return subprocess.check_output(['git', *args])


def normalized(s):
    return ' '.join(s.split())


def nodes(x):
    if isinstance(x, dict):
        if 'id' in x and 'spec' in x:
            yield x['id'], x
        for v in x.values():
            yield from nodes(v)
    elif isinstance(x, list):
        for v in x:
            yield from nodes(v)


program = dict(nodes(json.loads(Path('.aiops/program.json').read_text())))
merges = dict((int(n), sha) for sha, n in re.findall(
    r'^([0-9a-f]{40}) Merge pull request #(\d+) ',
    git('log', '--first-parent', '--merges', '-10', '--format=%H %s').decode(), re.M))
assert set(merges) == set(range(416, 426))
assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert git('rev-parse', 'origin/main').decode().strip() == BASE
all_links = set()
all_symbols = set()
for doc, heading in HEADINGS.items():
    old = git('show', BASE + ':' + doc)
    current = Path(doc).read_bytes()
    start = current.index(heading.encode())
    if doc == PLAN:
        end = current.index('## 6. E-4와 상태 수명'.encode(), start)
        # The insertion begins with an extra newline before its heading.
        assert current[:start - 1] + current[end:] == old, doc
        supplement = current[start:end].decode()
    else:
        assert current[:len(old)] == old, doc
        supplement = current[len(old):].decode()
    rows = re.findall(r'^\| #(\d+) \| (.*)$', supplement, re.M)
    assert len(rows) == 10 and {int(pr) for pr, _ in rows} == set(range(416, 426)), doc
    definitions = dict(re.findall(r'^\[([^]]+)\]: (\S+)$', supplement, re.M))
    # Resolve inline and reference Markdown links relative to each document.
    links = re.findall(r'\[([^]]+)\]\(([^)]+)\)', supplement)
    for label, ref in re.findall(r'\[([^]]+)\]\[([^]]+)\]', supplement):
        assert ref in definitions, (doc, ref)
        links.append((label, definitions[ref]))
    for label, target in links:
        raw, _, anchor = target.partition('#')
        path = (Path(doc).parent / raw).resolve()
        assert path.is_relative_to(Path.cwd()), (doc, target)
        assert path.exists(), (doc, target)
        if anchor and path.suffix == '.md':
            anchors = []
            for title in re.findall(r'^#+ (.+)$', path.read_text(), re.M):
                title = re.sub(r'[^\w\- ]', '', title.lower())
                anchors.append(title.replace(' ', '-'))
            assert anchor in anchors, (doc, target, anchors)
        all_links.add(str(path.relative_to(Path.cwd())))
        if '::' in label:
            filename, symbol = label.split('::')
            assert filename == path.name
            parsed = ast.parse(path.read_text())
            assert any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                       and n.name == symbol for n in ast.walk(parsed)), label
            all_symbols.add((str(path.relative_to(Path.cwd())), symbol))
    for pr, row in rows:
        fields = [c.strip() for c in row.split('|')]
        node = fields[0].strip('\x60')
        assert node not in program, node
        record_link = next(target for label, target in links if label.endswith(
            node if not node.startswith('plan-plan-') else node))
        record_path = (Path(doc).parent / record_link.split('#')[0]).resolve()
        record_text = record_path.read_text()
        assert (re.search(r'Node(?:/task ID)?:? \x60' + re.escape(node) + r'\x60', record_text)
                or record_text.startswith('# ' + node + ' —')), node
        assert ('/agent/kix-' + node) in git('show', '-s', '--format=%s', merges[int(pr)]).decode(), node
        assert record_path.relative_to(Path.cwd()).as_posix() in Path('docs/README.md').read_text(), node
        # Canonical field: exact spec substring, exact declared dependencies.
        can_field = fields[6]
        match = re.fullmatch(r'\x60([^\x60]+)\x60: "([^"]+)"; depends_on: (.*); '
                             r'does not complete or start the canonical node', can_field)
        assert match, (doc, pr, can_field)
        can, quote, deps = match.groups()
        assert normalized(quote) in normalized(program[can]['spec']), (doc, pr)
        assert re.findall(r'\x60([^\x60]+)\x60', deps) == program[can]['depends_on'], (doc, pr)
        assert fields[7].startswith('D1; '), (doc, pr)

# Byte comparison of every tracked input; supplements are the only exceptions.
tracked = git('ls-files', '-z').decode().split('\0')[:-1]
base_paths = git('ls-tree', '-r', '-z', '--name-only', BASE).decode().split('\0')[:-1]
assert set(tracked) == set(base_paths)
for p in tracked:
    if p not in HEADINGS:
        assert Path(p).read_bytes() == git('show', BASE + ':' + p), p
# The actual pre-edit SHA-256 snapshot, when available, is independently checked.
snapshot = Path('/tmp/audit29-before.json')
if snapshot.exists():
    before = json.loads(snapshot.read_text())
    assert before['base'] == BASE and set(before['files']) == set(tracked)
    for p, digest in before['files'].items():
        assert hashlib.sha256(git('show', BASE + ':' + p)).hexdigest() == digest, p
locks = {
    'runtime/crates/kix-kernel/src/lib.rs': '69564b166f0c27f9af5d8422f0a466b18d74c20f',
    'runtime/crates/kix-kernel/tests/quarantine_capacity.rs': 'b607996c83a119c349f1cc90469ac1ba82764e20',
}
for p, expected in locks.items():
    assert git('hash-object', p).decode().strip() == expected
new = git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')[:-1]
assert new == [RECORD], new
changed = git('diff', '--name-only', '-z').decode().split('\0')[:-1]
assert set(changed) == set(HEADINGS), changed
for line in git('diff', '--raw', '--no-renames', '--no-ext-diff').decode().splitlines():
    assert re.match(r'^:100644 100644 [0-9a-f]+ 0+ M\t', line), line
assert Path(RECORD).stat().st_mode & 0o777 == 0o644
assert all(p.startswith(('docs/', 'validation/')) and not p.startswith(
    ('docs/contracts/', 'docs/adr/', 'validation/2026-09-11/'))
           for p in changed + new)
print('PASS: 3 supplements x 10 unique PR rows; all node IDs, indexed records, source/test links,')
print('Markdown anchors, cited Python symbols, normalized canonical quotes and depends_on match.')
print(f'PASS: {len(all_links)} distinct link targets; {len(all_symbols)} cited Python symbols.')
print(f'PASS: {len(tracked) - 3} other tracked files byte-identical; '
      'all historical document bytes preserved; 108 frozen reference files and both locks match.')
print('PASS: exactly 4 authorized changed paths; documentation-only classification; refs unchanged.')
print('Local first-parent merge observations (not CI/review/acceptance):')
for pr, sha in sorted(merges.items()):
    print(f'#{pr} {sha}')
```

Save this guard as /tmp/audit29-guard/sitecustomize.py:

```python
"""Enforce the supervisor's no-network boundary during documentation checks."""
import sys


def no_network(event, args):
    if event.startswith('socket.'):
        raise PermissionError('audit29 supervisor no-network restriction')
    if event == 'subprocess.Popen':
        argv = args[1]
        if isinstance(argv, (list, tuple)) and '-I' in argv and any(
                isinstance(arg, str) and 'import json, socket' in arg for arg in argv):
            raise PermissionError('audit29 supervisor no-network restriction: isolated loopback probe not launched')


sys.addaudithook(no_network)
```


Save the foreground runner below as /tmp/audit29-run-checks.py, then run
`python3.12 -B /tmp/audit29-run-checks.py`. It retains per-command
stdout/stderr and exit codes in /tmp/audit29-check-results. Those temporary
captures are not additional repository outputs; actual results are recorded above.

```python
"""Run the narrow checks first, then the unchanged workflow block, foreground."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

capture = Path('/tmp/audit29-check-results')
capture.mkdir(exist_ok=True)
workflow = Path('.github/workflows/protocol.yml').read_text()
step = workflow.split('      - name: Stdlib offline document checks\n', 1)[1]
block = step.split('        run: |\n', 1)[1].split('\n      - ', 1)[0]
commands = [line.strip() for line in block.splitlines() if line.strip()]
assert all(re.fullmatch(r'python3 scripts/check_[a-z0-9_]+\.py(?: --self-test)?', c) for c in commands)
assert 'python3 scripts/check_stage5_host.py --self-test' in commands
assert 'python3 scripts/check_stage5_host.py' not in commands
narrow = [
    'python3.12 -B scripts/check_status_register.py',
    'python3.12 -B scripts/check_status_register.py --self-test',
    'python3.12 -B scripts/check_docs_index.py',
    'python3.12 -B scripts/check_docs_index.py --self-test',
]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='/tmp/audit29-guard')
results = []
for phase, cmd in [('narrow', c) for c in narrow] + [('workflow', c) for c in commands]:
    start = time.monotonic()
    completed = subprocess.run(shlex.split(cmd), env=env, capture_output=True, text=True)
    seconds = round(time.monotonic() - start, 3)
    number = len(results) + 1
    (capture / f'{number:02}.stdout').write_text(completed.stdout)
    (capture / f'{number:02}.stderr').write_text(completed.stderr)
    entry = dict(phase=phase, command=cmd, exit=completed.returncode, seconds=seconds,
                 stdout=completed.stdout, stderr=completed.stderr)
    results.append(entry)
    (capture / 'results.json').write_text(json.dumps(results, indent=2))
    print(f'{phase}: {cmd} -> exit {completed.returncode} ({seconds}s)', flush=True)
    if completed.returncode:
        print(completed.stdout[-4000:], completed.stderr[-4000:], flush=True)
        raise SystemExit(completed.returncode)
print(f'PASS: {len(narrow)} narrow + {len(commands)} workflow invocations.', flush=True)
```
