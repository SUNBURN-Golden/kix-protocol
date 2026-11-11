# RS load-summary arithmetic and CSV regressions

Node: `plan-rs-summary-arithmetic-tests`, source: KIX planner run `1792715335`
(`/workspace/kix-run/logs/planner_1792715335`), loop-proposed, issue: none,
not in `.aiops/program.json`. Dependencies: `rs-4-l1`,
`plan-rs-model-gap-closure`; audit floor A2; Astra gate: none; user_merge: false.
This is not an ASTRA program-mode session. The task document is the supervisor's
node specification and read-only design plan supplied in the session; there is
no corresponding file under `docs/tasks/`.

Local starting `origin/main` and branch HEAD both resolve to
`3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af` on
`agent/kix-plan-rs-summary-arithmetic-tests`; the starting worktree was clean.
The task says latest main, but remote freshness is unverified: the supervisor's
explicit no-network rule overrides AGENTS.md §1's fetch instruction. No fetch,
rebase, commit, push, GitHub action, issue, PR or comment was performed.
Implementation/final task commit SHA: unavailable (uncommitted builder changes).
Merge commit and post-merge checks: not applicable.

## Existing coverage mapped before adding tests

The following map was recorded after reading existing test bodies and before
adding regressions. Test names are in
`reference/rights_scale/test_summarize_load.py::TestSummarizeRules` unless stated.

| Requirement | Existing evidence | Classification before this change |
|---|---|---|
| Measurement verdict rules | `test_matching_snapshot_passes`, `test_page_divergence_fails`, `test_unknown_branch_fails`, `test_main_records_shield_shortfall` | Sufficiently covered for these rules; retained unchanged |
| Distinct paths | `test_a_failed_path_is_reported_separately` checks summary/CLI receipt verdicts | Partially covered; numerical aggregate isolation unasserted |
| Empty, singleton, unsorted, repeated samples and percentile boundaries | Existing synthetic parents have `service_ms=1`, statistics unasserted | Not covered |
| Missing versus measured zero, metric-specific n, gas totals | Existing `_report()` has `gas=None`, arithmetic unasserted | Not covered |
| Parent/probe CSV fields and quoting | Existing CLI tests inspect `receipt.json` only | Not covered |
| Mixed-outcome service timing population | Failure outcomes tested, timing populations unasserted | Not covered |
| Discovery and documentation indexing | Existing discovery in `protocol.yml`, `scripts/check_docs_index.py` and its self-test | Sufficient machinery; verify additions without workflow edits |

`reference/rights_scale/test_load_plan.py` covers workload construction;
`reference/rights_scale/test_measurement_gap.py` covers evidence availability.
Neither supplies the missing arithmetic or CSV assertions.

## Scope and evidence status

Authorized changed paths only:

- `reference/rights_scale/test_summarize_load.py`
- `validation/2026-10-23-plan-rs-summary-arithmetic-tests/README.md`
- `docs/README.md`

The summarizer, measurement verdicts, generators/workloads, contracts, CI,
historical evidence, `.aiops/**` and `docs/tasks/**` are unchanged.

## New regressions and independent calculations

All new tests are in `reference/rights_scale/test_summarize_load.py`.
Expected numbers and CSV cells are fixed literals; no summarizer helper is
called to construct expected results. Calling `stats` and `summarize_path` is
the operation under test. `_report`, `_snapshot` and `_page` are reused only for
synthetic scaffolding, not numerical oracles. These tests are source-informed,
not clean-room or independent protocol verification.

| Test | Gap addressed and expected result |
|---|---|
| `TestSummaryArithmetic.test_stats_fixed_cases` | Complete dictionaries for empty, all-null, singleton, measured zero, unsorted/repeated samples and rounding. `[]` and `[None,None]` return null; `[7]` has n=1 and all values 7; `[None,0]` has n=1 and all values 0; `[9,1,9,3,3]` sorts to `[1,3,3,9,9]`, sum=25, mean=5 and p50/p95/p99=3/9/9; `[1,2,2]` has mean=5/3 rounded to 1.67 and percentiles 2/2/2. |
| `TestSummaryArithmetic.test_nearest_rank_boundaries` | Descending inputs n…1 around nearest-rank boundaries, with fixed n/min/max/mean/p50/p95/p99 dictionaries; table below. |
| `TestSummaryArithmetic.test_metric_specific_counts_and_mixed_outcomes` | Five public/issue parents: ok, abort, client_refused, ok, abort. Service `[10,30,0,null,omitted]` has n=3, min/max=0/30, mean=40/3→13.33, p50/p95/p99=10/30/30. Build `[0,omitted,4,null,omitted]` has n=2, mean=2, percentiles 0/4/4. Proof has only measured 6 (n=1); witness has only missing/null values (null statistics). Outcomes are exactly ok=2, abort=2, client_refused=1. The sole measured ok service is 10, while mixed-outcome service p99 is 30. |
| `TestSummaryArithmetic.test_gas_totals_preserve_large_integers` | Decimal-string gas components, independent counts and separate exact integer totals above 2^53 (table below), plus exact extrema/p95/p99. A gas-free consume has all three gas stats null and `gas_total={}`; a test-only `zero_gas` operation label with measured string zeros has n=1 and total=0 for each component. No protocol command is added. |
| `TestSummaryArithmetic.test_path_and_operation_aggregates_are_distinct` | Interleaved private/issue=101, delegated/issue=201 and public/consume=301 each remain singleton aggregates. Public/issue retains its original n=3 mixed service distribution. Exact operation membership is public={issue,consume}, private={issue}, delegated={issue}. |
| `TestSummaryCsv.test_parent_and_probe_csv_preserve_fields` | One unchanged CLI invocation with temporary report/scenario/output files. Three synthetic public parents and two branches; both CSVs parsed with `csv.DictReader` and `newline=''`, all cells compared to literal dictionaries. |

For the boundary cases the independently selected one-based ranks are the
reported p50/p95/p99 values because sorted inputs are 1…n. Arithmetic-series
means are (n+1)/2; expected values are stored in a fixed table in the test.

| n | min | max | mean | p50 | p95 | p99 |
|---:|---:|---:|---:|---:|---:|---:|
| 19 | 1 | 19 | 10 | 10 | 19 | 19 |
| 20 | 1 | 20 | 10.5 | 10 | 19 | 20 |
| 21 | 1 | 21 | 11 | 11 | 20 | 21 |
| 99 | 1 | 99 | 50 | 50 | 95 | 99 |
| 100 | 1 | 100 | 50.5 | 50 | 95 | 99 |
| 101 | 1 | 101 | 51 | 51 | 96 | 100 |

| Gas component | Measured decimal strings | n | Exact integer total |
|---|---|---:|---:|
| computation | `9007199254740993`, `2`, `0` | 3 | 9007199254740995 |
| storage | `9007199254740997`, `0` | 2 | 9007199254740997 |
| rebate | `9007199254741001`, `0` | 2 | 9007199254741001 |

The other two parents omit gas or have `gas=null`; storage is omitted on the
second gas-bearing parent and rebate is null on the third. Integer total types
are checked explicitly. Large floating-point gas means are not used as exact
oracles; no net gas value is calculated.

The CSV fixture reuses the generated public steps at seq 0, 1 and 5
(`create_show`, `claim_pages`, `parallel`) and the synthetic valid snapshot,
with no workload execution. Its in-memory scenario has those three steps and
no shield request. This is a serialization fixture, not journey evidence.
Literal parent rows cover path/phase/seq/op/signer/digest, all six timing fields,
outcome/abort/module/error/abort_or_error, expectation and mismatch flag,
recovered, parallel_k, congestion count, all gas fields and detail. Parent
abort 17 takes precedence over the simultaneously present error for
`abort_or_error`; the client-refused parent's multiline error is retained.

Branch rows inherit public/probe.concurrent/seq 5 and probe=parallel, with
zero-based branch identifiers 0/1, different issue/consume operations, slots
512/0, slots array `[512,513]` versus missing, different signers, digest present
versus missing, ok/abort outcomes, abort 23 and multiline error, service
9000/0, build 0/null, large decimal gas versus absent gas, and detail. Commas,
quotes and newlines occur in parent/probe/branch details; parsed JSON detail
objects and exact encoded CSV cells are both asserted. Errors also contain
literal newlines, exercising multiline CSV fields directly.
The branch operations do not appear in parent `by_op`, parent step count stays
3, and parallel statistics remain service=40 and gas totals=5/6/0 despite the
branch's service=9000 and large gas values.

## Contract classification and limitations

Class A, matching: blueprint §§7.3–7.4 requires distinct paths and timing
interpretations, and forbids calling mixed p99 successful-purchase latency.
The tests preserve those distinctions. The existing verdict regressions remain
unchanged. No explicit contract violation was found.

Class B, current behavior characterized where the contract does not prescribe
the arithmetic or encoding:

- `stats` sorts measured values, removes nulls, retains zeros and duplicates,
  returns null for an empty measured population, and rounds the arithmetic
  mean to two decimal places. Percentiles select the nearest rank
  `ceil(q*n)` (one-based), without interpolation.
- Summary counts are per metric, not per total parent count. Gas decimal
  strings are parsed as Python integers and summed independently per component;
  missing components have no samples and no total key, while measured zero has
  a sample and a zero total. No exactness claim is made for large float means.
- Each operation's timing statistics include all its measured parent outcomes;
  they are mixed-outcome service statistics. Probe branches are serialized
  separately and excluded from parent operation arithmetic. Parent probe
  timings and gas remain in the parent's parallel operation aggregate.
- CSV absent/null scalar cells are empty; measured zero is `0`, booleans are
  `True`/`False`. Expectations and present detail objects use compact JSON;
  missing expectations and branch slots are JSON `null`. Branch slot arrays
  use JSON's default spacing. The CSV writer quotes cells as needed; JSON
  detail strings escape quotes/newlines and round-trip to their original
  values. Parent abort is a scalar CSV cell, branch abort is JSON encoded
  (both fixtures use integers).

These are observations of the current reporter, not new protocol semantics or
schema guarantees. Acceptance does not imply benchmark reproduction, L2/L3
execution, journey-evidence completeness, workload adequacy, measurement
validity, successful purchase latency, production readiness, durability,
distributed fencing, chain finality, anonymity or legal compliance.
All inputs are synthetic. No network, sockets, chain, database, installation,
measurement campaign, secrets, paid service, production runtime or real funds
were needed or used for this task. SLOs and operational values remain
**UNDETERMINED**, retaining their existing User/Astra owners. Parked
journey-evidence completeness work remains excluded.

## Commands actually run and results

Commands ran from the repository root, narrow tests first. All listed checks
passed on their first run; there was no fix/retry cycle.

| Command | Actual result |
|---|---|
| `pwd`, `git status --short`, `git branch --show-current`, `git rev-parse HEAD`, `git rev-parse origin/main` | Correct worktree/branch, initially clean; both refs equal the starting SHA above |
| `python3 -B -m unittest discover -s reference/rights_scale -t reference/rights_scale -p test_summarize_load.py` | Exit 0; 11 tests, OK (0.158s) |
| `python3 -B -m unittest discover -s reference/rights_scale -t reference/rights_scale` | Exit 0; 172 tests, OK (3.728s) |
| `python3 -B scripts/check_docs_index.py` | Exit 0; `docs index ok: scanned=208 indexed=173 allowlisted=35` |
| `python3 -B scripts/check_docs_index.py --self-test` | Exit 0; all seven intentional invalid-index cases detected; `self-test: pass` |
| `git diff --check` | Exit 0; no whitespace errors |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` (via Python subprocess, before/after) | Required blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`, MATCH both times |
| `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (via Python subprocess, before/after) | Required blob `b607996c83a119c349f1cc90469ac1ba82764e20`, MATCH both times |
| `python3 -B -` protected-file manifest and allowlist audit (stdin scripts, procedure below) | Exit 0 before/after; all 108 frozen files identical and exactly the three authorized paths changed |
| `git diff --stat`, `git diff -- reference/rights_scale/test_summarize_load.py`, `rg`, `cat`, `sed`, and a `python3 -B -` scaffold inspection | Read-only review of changed tests, governance, plan, contracts, existing tests, index, and workflow commands; no external action |

Protection scripts used sorted `Path('reference/v0.3-rc1').rglob('*')` file
paths mapped to SHA-256 hashes of their full bytes, serialized with
`json.dumps(manifest, sort_keys=True, indent=2) + '\n'`. The complete manifests
were written to `/tmp/plan-rs-summary-arithmetic-protected-before.json` and
`/tmp/plan-rs-summary-arithmetic-protected-after.json` and compared for exact
equality (paths and bytes), both covering 108 files. Both manifest SHA-256s:
`3913e6dab3366bafca45af109258da5f0582068008733b5b3c63577af2092c20`.
The scripts also asserted both locked blobs against the required values.
The path audit combined `git diff --name-only HEAD` and
`git ls-files --others --exclude-standard` and asserted equality with the
three-path allowlist above. The manifests are temporary verification artifacts,
not repository changes.

Inspected `.github/workflows/protocol.yml`: Python discovery in the
`rights-scale` job and both docs-index commands in the protocol job are the
closest local equivalents for these touched paths. Inspected
`.github/workflows/ktx-kernel.yml`: it contains no summary Python check.
Kernel/workspace Rust tests, Clippy/formatting, Move, bootstrap, proving,
Node suites and localnet checks were not run; no corresponding code changed,
and this offline test-only task does not authorize chain execution or dependency
installation. The local checks are not a claim that the full workflows passed.

## Review, CI, deviations and remaining uncertainty

| Gate | Run ID | Status / conclusion |
|---|---|---|
| Non-author exact-head review / A2 audit | Unavailable | Not performed in this builder session |
| Exact-head KTX kernel verification | Unavailable | Not requested or observed; no final committed task head |
| Exact-head KIX protocol verification | Unavailable | Not requested or observed; no final committed task head |
| Post-merge main CI and locked-blob verification | Not applicable | No merge |

Local builder implementation is complete; this record does not claim
`merge-ready`. The supervisor owns subsequent git/GitHub work and exact-head
evidence. No older CI result is transferred to these changes.

Deviation from AGENTS.md §1: no `git fetch origin main`, per the explicit
supervisor no-network instruction. No node document was created or edited in
`docs/tasks/`; the supplied node/design plan is the immutable task input.
No substantive deviation from the design plan. The additional zero-only gas
case distinguishes measured zero totals from absent totals. The CSV fixture
uses only three scaffold parents to keep inputs small.

Remaining uncertainty: remote main freshness, non-author review and final-head
CI are unverified. Arithmetic/CSV choices characterized here remain subject to
future contract decisions. Actual workload completeness, L2/L3 measurements,
benchmark reproduction, and operational values require separate authorized
work and are not follow-up work performed in this session.
