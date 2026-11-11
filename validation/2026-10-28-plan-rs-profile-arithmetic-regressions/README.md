# RS creation bps and issuance event-budget regressions

Node: `plan-rs-profile-arithmetic-regressions`. Task input: the supervisor-provided
node specification and read-only design plan in this session; no task issue or
corresponding document under `docs/tasks/` exists for this node. Source: KIX planner
run 1793149067 (`/workspace/kix-run/logs/planner_1793149067`), loop-proposed and not
in `.aiops/program.json`. Dependencies: `plan-rs-model-gap-closure` and
`plan-plan-rs-im-evidence-map`. Audit floor A2; `astra_gate: None`;
`user_merge: False`. This is not an ASTRA program-mode session.

This is builder-authored evidence, not independent A2 review, Astra acceptance,
a capability-grade change or merge readiness. READY means local builder delivery.

## Base and publication boundary

Observed local `origin/main` and initial branch HEAD both equal
`03cf8e145e4dddf2a42e9a71dd9a8bd184b8fa20`, on
`agent/kix-plan-rs-profile-arithmetic-regressions`; the initial worktree was clean.
No local base delta was observed. `git fetch origin main` was NOT_RUN because the
supervisor explicitly prohibits every network action, overriding AGENTS.md §1's
fetch instruction. Remote freshness is unverified; historical document SHAs are
not current observations. No rebase or base change is authorized or performed.

Implementation head and final committed task head: unavailable; this delivery is
an uncommitted worktree patch. Exact-head KTX kernel verification and KIX protocol
verification run IDs/statuses/conclusions: unavailable, not run in this session.
No merge occurred; merge SHA, final-merge blob checks and post-merge main CI are
not applicable. Git/GitHub publication belongs to the supervisor.

## Existing coverage recorded before test edits (AGENTS.md §7)

The following bodies were inspected and this table was written before changing
`reference/rights_scale/test_model.py`. Python citations below are in that file.

| Requirement | Existing evidence | Before-change classification |
|---|---|---|
| Creation policy rejection | `RangeTable.test_create_policy_checks`: `(9000,1001)` and an oversized organizer component return `EPolicy`. | Partially covered |
| Acceptance at sums 9999/10000, zero-component cases and exact value preservation | No targeted assertions. | Not covered |
| Fixture bundle boundaries | `Predicates.test_c05_limit_minus_one_limit_limit_plus_one`: 7/8/9, dedicated limit error and incomplete/mismatched/zero bundles. | Sufficiently covered; retain |
| Two events per issuance through the fixture limit | `Predicates.test_each_issue_emits_two_events`: six events for three issuances, without event-type counts. | Partially covered |
| Issuance slot/generation and accompanying Change | `Predicates.test_the_issuance_event_carries_the_slot_and_the_generation`: refund/reissue, generations 1/2 and accompanying Change. | Sufficiently covered; retain |
| Recorded event-budget boundaries | No arithmetic regression for profile §6. | Not covered |

Existing Move evidence was also read: under `reference/rights_scale/sui/tests/`,
`creation_tests.move::bps_over_ten_thousand_is_rejected` rejects `(9000,1001)`;
`public_path_tests.move::each_issue_emits_two_events` counts three Issuance and
three Change events; and
`bundle_tests.move::c05_a_bundle_at_the_limit_issues_every_slot_across_three_pages`
issues eight slots across three pages. Reading these bodies is not a new Move
execution result. The contract input is the unchanged draft
`docs/contracts/RIGHTS_SCALE_PROFILE.md` §6, not a fresh network limit lookup.

## Protected-file baseline

Before editing, `git hash-object` returned the required blobs:

| Path | Required and observed before |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

A Python stdlib SHA-256 manifest was captured in session memory before edits.
It includes every regular file under `reference/v0.3-rc1`, `runtime`, `.aiops`,
`docs/tasks`, `docs/contracts`, `docs/decisions`, `.github/workflows`,
`reference/rights_scale/sui`, `reference/rights_scale/zk`,
`reference/rights_scale/vectors`, plus `reference/rights_scale/model.py`.
The complete sorted path-to-hash mapping contains 281 files. Its canonical JSON
(`sort_keys=True`, `separators=(',', ':')`) SHA-256 is
`0b36ae63ac11b671fe9cc63ae5405df1032ac0b107f56401e65a2e2bd1a768f3`.
The after-work manifest has the identical 281 paths and per-file hashes, including
all 108 files under `reference/v0.3-rc1`; the canonical manifest digest is unchanged.
Both locked Git blobs also match after work. No protected-file mismatch occurred.

The manifest command was run before edits and after test/checker execution; both
JSON results were held in session memory and their complete `files` mappings were
compared for equality (not just their aggregate hashes):

```python
import hashlib, json
from pathlib import Path
roots = [Path(p) for p in (
    'reference/v0.3-rc1', 'runtime', '.aiops', 'docs/tasks',
    'docs/contracts', 'docs/decisions', '.github/workflows',
    'reference/rights_scale/model.py', 'reference/rights_scale/sui',
    'reference/rights_scale/zk', 'reference/rights_scale/vectors')]
manifest = {}
for root in roots:
    for path in ([root] if root.is_file() else sorted(root.rglob('*'))):
        if path.is_file():
            manifest[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
print(json.dumps({'files': manifest, 'count': len(manifest),
                  'sha256': hashlib.sha256(encoded).hexdigest()}))
```

## Changed paths and acceptance evidence

| Path | Change and addressed gap |
|---|---|
| `reference/rights_scale/test_model.py` | Adds `RangeTable.test_create_bps_sum_boundaries_preserve_supplied_values` and `Predicates.test_recorded_profile_event_budget_arithmetic`; extends `Predicates.test_each_issue_emits_two_events`. No model implementation changed. |
| `docs/status/RS_IM_EVIDENCE_MAP.md` | Only IM-01/IM-29 Python citations and gap cells change. All statuses, owners, counts and other rows remain byte-identical. |
| `validation/2026-10-28-plan-rs-profile-arithmetic-regressions/README.md` | This coverage, execution and integrity record. |
| `docs/README.md` | Exact Markdown link to this validation README. |

Creation cases use `make(claim=False, seal=False, ...)`. For sum 9999, the
synthetic allocations are `(4999,5000)`, `(0,9999)`, `(9999,0)`; for sum 10000,
`(5000,5000)`, `(0,10000)`, `(10000,0)`. Each accepted show preserves both supplied
bps values exactly. Sum 10001 is rejected with existing `EPolicy` for
`(5000,5001)`, `(0,10001)`, `(10001,0)`. These inputs select no commercial policy.

The existing event regression now executes each bundle size 1 through unchanged
fixture `model.MAX_BUNDLE_CHAIN == 8` on a fresh sealed show with 16 seated slots,
no GA and page size 4. Starting at slot 2 crosses three pages in the maximum case.
Only the event slice after setup is inspected: exactly n tickets, 2*n events,
n Issuance and n Change events, plus existing model invariants. The existing
7/8/9 refusal and slot/generation regressions are retained without duplication.

The arithmetic test locates exactly one `max_num_event_emit` row within profile
§6 and pins its recorded value to 1024. It connects the event rate to the actual
model-event regression and asserts `1024 // 2 == 512`. It executes no bundles of
these sizes and overrides no fixture constant:

| Issuances | Required events | Remaining event budget | Fits event budget |
|---|---|---|---|
| 511 | 1022 | 2 | yes |
| 512 | 1024 | 0 | yes |
| 513 | 1026 | -2 | no |

IM-01 stays `COVERED_MODEL_OR_MEMORY`, owner `none`. IM-29 stays `PARTIAL`, owner
`RS-1 / Astra`. Counts remain exactly:

```text
COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2
```

## Commands actually run and results

The narrow test ran first, then full rights-scale discovery, then the requested
checkers. All listed verification commands exited 0 unless explicitly NOT_RUN.
No long-running job was launched in the background.

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Expected node worktree and branch; clean initial status; both SHAs `03cf8e145e4dddf2a42e9a71dd9a8bd184b8fa20`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both required blobs match, as listed above. |
| `python3 -` (manifest script above, before and after) | Identical complete path sets and SHA-256 hashes for 281 files; manifest digest above unchanged. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale -p test_model.py` | 53 tests passed, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 175 tests passed, OK. |
| `python3 scripts/check_rs_im_evidence_map.py` | OK: 30/30 rows, 202 citations; counts unchanged. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | `self-test: pass`; all 16 listed negative controls detected. |
| `python3 scripts/check_evidence_map_rollup.py` | OK: contracts=25; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | `self-test: pass (16 negative controls)`. |
| `python3 scripts/check_docs_index.py` | OK: scanned=298, indexed=263, allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | `self-test: pass`; all seven listed negative controls detected. |
| `python3 scripts/check_ci_test_discovery.py` | OK: reference_suites=6, node_tests=8, modules=4, excluded=3; all six rights-scale Python modules reached by the existing workflow discovery. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | `self-test: pass (18 negative controls)`. |
| `python3 -` (scope assertion using `git show HEAD:docs/status/RS_IM_EVIDENCE_MAP.md`, current map, `git diff --name-only HEAD` and `git ls-files --others --exclude-standard`) | PASS: 30 statuses/owners unchanged; only IM-01/IM-29 Python citations and gap cells changed; Counts and all non-row text unchanged; exactly the four authorized paths changed. |
| `git diff --check`; `git diff --stat`; `git diff -- reference/rights_scale/test_model.py docs/status/RS_IM_EVIDENCE_MAP.md docs/README.md` | Clean whitespace check; inspected tracked diff confirms scoped test and citation changes. The untracked validation README is included in the separate four-path scope assertion. |

Repository guidance, named contract/evidence bodies and both workflow definitions
were read with `cat`, `sed` and `rg`. The full Python discovery and the four checker
pairs are the touched-path local equivalents in `protocol.yml`. The Rust tests,
architecture checks, Clippy and formatting in `ktx-kernel.yml` were inspected but
not run: no Rust path changes, and the supplied design limits local checks to
this Python/documentary node. Move, Node, ZK setup and localnet steps were not run.
Local Python results do not replace exact-head KTX/KIX CI or non-author review.

## Discrepancies, deviations and remaining uncertainty

- A, contract-defined and matching: tested bps acceptance/rejection and fixture
  event deltas match the unchanged model and profile inputs. The recorded integer
  arithmetic gives the stated event-only ceiling. No explicit contract violation
  (C) was found; no new contract-undefined behavior characterization (B) was added.
- Operational `MAX_BUNDLE_CHAIN` remains UNDETERMINED, owned by RS-1 / Astra.
  Fixture 8 and arithmetic ceiling 512 are not operational selections. Actual PTB
  feasibility and command, input-object, argument, transaction-byte, written-object,
  effects-size and other limits remain unverified. Actual calls may emit additional
  events. No test of oversized model bundles or runtime event-budget API was added.
- The only design/procedure deviation is omitting AGENTS.md §1's fetch under the
  supervisor's explicit no-network rule; local refs are recorded without a claim
  of remote freshness. The prompt supplies the task input instead of a new
  `docs/tasks/` document, which this session is prohibited from creating or editing.
- No commit, push, PR, issue, comment, tag, branch mutation or merge was performed.
  Exact final-head CI and independent review remain supervisor follow-up gates;
  this record does not propose merge or transfer any older SHA's CI result.
- No network, chain execution, measurements, product policy selection, credentials,
  real funds, provider calls, public endpoints, production runtime, storage engine,
  new coin/TIX module or protocol command was needed or used. No production
  readiness, durability, bank exactly-once, distributed fencing, chain finality,
  legal compliance or cryptographic-independence claim is made.
