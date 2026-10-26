# Open User decisions — October 26 BCS1 checker-scope stop addendum

## Basis and provenance

Builder-authored, dated 2026-10-26. Node:
`plan-plan-open-decisions-addendum-bcs1-checke`; issue: none;
`depends_on: []`; audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. This loop-proposed node is absent from
`.aiops/program.json` and has no corresponding task document under `docs/tasks/`.
Task input is the supervisor-supplied node specification and read-only design plan.
Source: KIX planner run 1792986805 (`/workspace/kix-run/logs/planner_1792986805`,
as supplied; no planner execution is claimed).

Observed cached `origin/main`, base and starting branch HEAD:
`9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58` (#303), on
`agent/kix-plan-plan-open-decisions-addendum-bcs1-checke`.
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness
remains unverified. No local base delta was observed.

Source stop:
`/workspace/kix-run/wt/plan-plan-bcs1-contract-bound-regressions/DECISION_REQUIRED.md`,
SHA-256 `964c74f959a0e8b89b3e8354ae9629b76c4c83b830cf727676e5f8f3939537dd`.
This is an external, unmerged record, attributed task input rather than a
repository link or merged contract. Its reported execution is not reproduced here.
Line citations to the stop below refer to those hashed bytes.

The [October 22 ledger](OPEN_USER_DECISIONS_20261022.md),
[October 23 supplement](OPEN_USER_DECISIONS_20261023_ADDENDUM.md),
[October 23 closure](OPEN_USER_DECISIONS_20261023_CLOSURE.md),
[October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md) and
[October 26 AI delegation addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md)
remain preserved. The [validation record](../../validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md)
records gathering commands, citation checks and local results.

Filename deviation: `OPEN_USER_DECISIONS_20261026_ADDENDUM.md` already records
the AI delegation stop. The `_BCS1` qualifier preserves that dated record.

**This document selects no option and changes no node state.**

## New stop — plan-plan-bcs1-contract-bound-regressions

The source classifies this as a scope/acceptance conflict, not an observed codec
contract violation (stop line 29). Decision needed (stop lines 10–14, verbatim):

> Authorize the narrowly scoped checker change in design plan §3.3, or revise the
> node's acceptance criteria outside this executing session. The supplied plan
> explicitly makes that change conditional on Option A authorization; it does not
> grant that authorization. AGENTS.md §3 requires stopping on incompatible task
> scope rather than broadening or rewriting the task.

The stop requires six follow-up rows to cite a new public-API test file while
the checker and its self-test pass (stop lines 16–18). The following facts are
quoted from the observed local main, not inferred from the stop's older base.

### Conflict facts at the basis

Checker source: [check_bcs1_evidence_map.py](../../scripts/check_bcs1_evidence_map.py).
Only the following test paths are accepted:

`scripts/check_bcs1_evidence_map.py:14`, verbatim:

```python
TEST_FILES = ('runtime/crates/kix-bcs1/src/lib.rs', 'runtime/crates/kix-bcs1/tests/golden_vectors.rs')
```
`scripts/check_bcs1_evidence_map.py:218–220`, verbatim:

```python
            if path not in TEST_FILES:
                problems.append(where + ' is outside test paths')
                continue
```
`scripts/check_bcs1_evidence_map.py:287–288`, verbatim:

```python
        if cells[2] not in TEST_FILES:
            problems.append('follow-up path outside test paths: ' + cells[0])
```

The follow-up heading and all eight status locks are pinned:

`scripts/check_bcs1_evidence_map.py:26`, verbatim:

```python
FU_HEAD = '## 3. Follow-up candidates (NOT_COVERED, no tests added)'
```
`scripts/check_bcs1_evidence_map.py:78–88`, verbatim:

```python
FOLLOW_UP = {
    'S1-VERSION-POSITIVE': 'FU-ZERO-ID',
    'S2-ENVELOPE-BOUND': 'FU-ENVELOPE-TOO-LARGE',
    'S2-BODY-BOUND-ENCODE': 'FU-BODY-TOO-LARGE-ENCODE',
    'S2-BODY-BOUND-DECODE': 'FU-BODY-TOO-LARGE-DECODE',
    'S2-UTF8-MULTIBYTE': 'FU-UTF8-MULTIBYTE',
    'S5-RUST-MOVE-EQUALITY': 'FU-S08-MOVE-EQUALITY',
    'S8-G3-TRUNCATED': 'FU-TRUNCATED-ENVELOPE',
    'S8-MOVE-SDK-EQUALITY': 'FU-S08-SDK-EQUALITY',
}
MUST_BE_NOT_COVERED = set(FOLLOW_UP)
```
`scripts/check_bcs1_evidence_map.py:270–274`, verbatim:

```python
        if ident in MUST_BE_NOT_COVERED:
            if status != 'NOT_COVERED':
                problems.append(ident + ': must stay NOT_COVERED')
            if FOLLOW_UP[ident] not in gap:
                problems.append(ident + ': missing follow-up tag: ' + FOLLOW_UP[ident])
```
`scripts/check_bcs1_evidence_map.py:280–283`, verbatim:

```python
    expected_fu = {(tag, ident) for ident, tag in FOLLOW_UP.items()}
    actual_fu = [(r[0], r[1]) for r in fu_rows if len(r) == 4]
    if len(fu_rows) != len(expected_fu) or len(actual_fu) != len(expected_fu) or set(actual_fu) != expected_fu:
        problems.append('follow-up table mismatch')
```

Current-state-dependent self-tests: the first FOLLOW_UP value is FU-ZERO-ID;
`FU row removed` therefore removes that row. The three S1-VERSION-POSITIVE
fixtures depend on its NOT_COVERED state and FU tag:

`scripts/check_bcs1_evidence_map.py:364`, verbatim:

```python
        ('FU row removed', map_text.replace(_row_line(map_text, next(iter(FOLLOW_UP.values()))) + '\n', ''), 'follow-up table mismatch'),
```
`scripts/check_bcs1_evidence_map.py:377–379`, verbatim:

```python
        ('not covered with tests', 'S1-VERSION-POSITIVE', TESTS, good, 'NOT_COVERED needs'),
        ('FU flipped', 'S1-VERSION-POSITIVE', STATUS, 'PARTIAL', 'must stay NOT_COVERED'),
        ('FU tag dropped', 'S1-VERSION-POSITIVE', GAP, 'zero ids', 'missing follow-up tag'),
```

The `anchor removed` fixture uses the same ID but is status-independent:

`scripts/check_bcs1_evidence_map.py:387`, verbatim:

```python
        ('anchor removed', re.sub(r'\s+'.join(map(re.escape, EXPECTED['S1-VERSION-POSITIVE'].split())), 'gone', sources['contract']), 'contract anchor is gone'),
```

Map source: [BCS1_CONTRACT_EVIDENCE_MAP.md](BCS1_CONTRACT_EVIDENCE_MAP.md).
Counts and heading, at `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:66–68`, verbatim:

```text
Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17

## 3. Follow-up candidates (NOT_COVERED, no tests added)
```

The eight §3 FU rows, `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:70–79`,
verbatim (the rows themselves are lines 72–79):

| FU | Row | Path | Candidate owner |
|---|---|---|---|
| FU-ZERO-ID | S1-VERSION-POSITIVE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-ENVELOPE-TOO-LARGE | S2-ENVELOPE-BOUND | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-BODY-TOO-LARGE-ENCODE | S2-BODY-BOUND-ENCODE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-BODY-TOO-LARGE-DECODE | S2-BODY-BOUND-DECODE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-UTF8-MULTIBYTE | S2-UTF8-MULTIBYTE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-S08-MOVE-EQUALITY | S5-RUST-MOVE-EQUALITY | runtime/crates/kix-bcs1/tests/golden_vectors.rs | S08 Move/SDK schema owner |
| FU-TRUNCATED-ENVELOPE | S8-G3-TRUNCATED | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-S08-SDK-EQUALITY | S8-MOVE-SDK-EQUALITY | runtime/crates/kix-bcs1/tests/golden_vectors.rs | S08 Move/SDK schema owner |

`docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:81`, verbatim:

```text
Paths identify candidate evidence locations only; no new tests are added or authorized. S08 equality will also need Move/SDK fixtures outside these two Rust files after a schema is approved. Other NOT_COVERED rows remain follow-up candidates with the gap and owner in §2.
```

Their §2 source rows at the basis (all NOT_COVERED; test cell `none`):

| FU | §2 ID | Map line | Conditional A/C treatment |
|---|---|---|---|
| FU-ZERO-ID | S1-VERSION-POSITIVE | 30 | New evidence; COVERED versus PARTIAL UNDETERMINED |
| FU-ENVELOPE-TOO-LARGE | S2-ENVELOPE-BOUND | 33 | New evidence; COVERED versus PARTIAL UNDETERMINED |
| FU-BODY-TOO-LARGE-ENCODE | S2-BODY-BOUND-ENCODE | 34 | New evidence; COVERED versus PARTIAL UNDETERMINED |
| FU-BODY-TOO-LARGE-DECODE | S2-BODY-BOUND-DECODE | 35 | New evidence; COVERED versus PARTIAL UNDETERMINED |
| FU-UTF8-MULTIBYTE | S2-UTF8-MULTIBYTE | 39 | New evidence; COVERED versus PARTIAL UNDETERMINED |
| FU-S08-MOVE-EQUALITY | S5-RUST-MOVE-EQUALITY | 47 | Remains NOT_COVERED |
| FU-TRUNCATED-ENVELOPE | S8-G3-TRUNCATED | 60 | New evidence; COVERED versus PARTIAL UNDETERMINED |
| FU-S08-SDK-EQUALITY | S8-MOVE-SDK-EQUALITY | 64 | Remains NOT_COVERED |

CI source: [protocol.yml](../../.github/workflows/protocol.yml).
The checker invocations are unchanged:

`.github/workflows/protocol.yml:253–254`, verbatim:

```text
          python3 scripts/check_bcs1_evidence_map.py
          python3 scripts/check_bcs1_evidence_map.py --self-test
```
`.github/workflows/protocol.yml:316`, verbatim:

```text
          cargo test --manifest-path runtime/Cargo.toml --workspace --locked
```

The stop's checker/map line citations, recorded at
`fc11cdf0150e54ed38bb363f2ded7238c48c6e53`, still hold at this basis:
`git diff --exit-code fc11cdf0150e54ed38bb363f2ded7238c48c6e53 HEAD -- scripts/check_bcs1_evidence_map.py docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md`
returned exit 0 with no output.

### Options (source text)

Stop lines 34–43, verbatim:

> 1. **A — recommended:** authorize only design plan §3.3's checker adaptation:
>    append the new test path; pin the six closed follow-up citations; retain the
>    two S08 NOT_COVERED locks; require FU tags only for remaining gaps; update the
>    follow-up heading; retarget the affected self-test fixtures to the unchanged
>    S08 row; add negative fixtures for lost closure citations and reverted status.
>    Then implement and verify the six tests and evidence-map updates as planned.
> 2. **B:** revise acceptance so the six rows remain NOT_COVERED and new evidence
>    appears only as prose. This does not meet current acceptance and was rejected
>    by the supplied design review.
> 3. **C:** authorize a separate checker node before this regression node.

Source recommendation: A. This addendum does not endorse it.
Decision owner and review boundary (stop lines 45–47, verbatim):

> **Who decides:** the User/orchestrator owning this loop-proposed node. The
> resulting checker change requires the planned non-author A2 review. This builder
> has not treated the recommendation as permission.

## Per-option impact inventory

These are conditional change inventories for the User/orchestrator, not permission
or an implementation specification. Future artifacts are explicitly distinguished
from paths that exist at the basis. The source's design plan §3.3 is not on main.
The future integration-test filename and each of the six rows' COVERED/PARTIAL
targets remain **UNDETERMINED — User/orchestrator**, subject to the required A2
review; this document supplies neither.

### Option A — scoped checker adaptation inside the regression node

**Files.** Would change `scripts/check_bcs1_evidence_map.py` and
`docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md`; add one public-API integration test
under the existing `runtime/crates/kix-bcs1/tests/` directory and a validation
README for the regression node. The test basename and validation path are
future artifacts, UNDETERMINED — User/orchestrator. No codec or contract edit
is implied by the stop.

**Checker assertions.** Would append the authorized test path to TEST_FILES
(line 14), adjust FU_HEAD (26), narrow MUST_BE_NOT_COVERED (88) to
S5-RUST-MOVE-EQUALITY and S8-MOVE-SDK-EQUALITY, and require FU tags only for
remaining gaps (270–274). The §3 table membership/path assertions (279–290)
would need to match the resulting follow-up representation. Pinning the six
closure citations needs a new constant/assertion analogous to PRESERVED_PARTIAL
(89–94, enforced at 275–277). Existing generic citation and status checks
(218–220, 264–269), plus Counts validation (291–293), still apply.

**Self-test fixtures.** Would retarget `FU row removed` (364) and
`not covered with tests`, `FU flipped`, `FU tag dropped` (377–379) to an unchanged
S08 row/tag; add negative fixtures for a lost closure citation and reverted
status. The fixture total printed at 403 would change; no future count is set.
The status-independent `anchor removed` fixture (387) need not change.

**Map rows.** Would add evidence to S1-VERSION-POSITIVE (30), S2-ENVELOPE-BOUND
(33), S2-BODY-BOUND-ENCODE (34), S2-BODY-BOUND-DECODE (35), S2-UTF8-MULTIBYTE
(39) and S8-G3-TRUNCATED (60). Each target status remains UNDETERMINED.
Would update Counts (66) and §3 heading/table/prose (68–81) to distinguish the
six closure citations from the two remaining S08 gaps (47, 64).
The three preserved PARTIAL rows remain constrained by lines 89–94, 275–277.
No total, unrelated row promotion or semantic contract amendment follows.

**CI steps.** No workflow edit: protocol.yml:253–254 would validate the adapted
map and self-tests; protocol.yml:316 would discover the new Rust integration
test through `cargo test --workspace --locked`. Rust fmt and Clippy at
protocol.yml:315,317 would apply to that future change. The existing
[ktx-kernel.yml](../../.github/workflows/ktx-kernel.yml):103 test step targets
`-p kix-kernel`; this option does not change that workflow.

**Acceptance satisfied / unmet.** The current regression acceptance could be
satisfied only after authorization, implementation of the six tests and map
updates, passing local checks and the planned non-author A2 review. It is not
satisfied by this inventory. The two S08 rows remain NOT_COVERED; production
schema/Move/SDK equality and the parked boundary corpus remain unmet/outside scope.

### Option B — revise acceptance, prose-only evidence

**Files.** The checker, map tables/rows and their Counts/heading would remain
unchanged. Any map edit would be prose outside those tables, consistent with
the pinned follow-up heading/prose. Whether any tests or a regression validation
README would be added is UNDETERMINED — User/orchestrator; the revised task input
must settle that outside the executing session.

**Checker assertions.** No changes to TEST_FILES (14), FU_HEAD (26), FOLLOW_UP
and MUST_BE_NOT_COVERED (78–88), status/FU checks (270–274), follow-up table
assertions (279–290) or Counts validation (291–293).

**Self-test fixtures.** Unchanged, including 364, 377–379 and status-independent
387; the existing fixture count at 403 is unchanged.

**Map rows.** All eight §2 rows at lines 30, 33–35, 39, 47, 60, 64 retain
NOT_COVERED and `none` citations; Counts (66) and §3 (68–81) remain as quoted.
Prose evidence cannot count as a closed table row under the current checker.

**CI steps.** No workflow edit: protocol.yml:253–254 retain the current checker
and self-tests; 316 retains workspace testing. No new Rust test is assumed.
The ktx-kernel.yml:103 test step is unchanged.

**Acceptance satisfied / unmet.** Would preserve current structural checker
acceptance, but does not meet the regression node's current six-row acceptance.
The source says B “was rejected by the supplied design review” (stop lines 40–42).
Any revised acceptance requires User/orchestrator input outside this session;
this addendum does not enact that revision. All eight FU gaps remain open.

### Option C — separate checker node first

**Files.** Would require the User/orchestrator to create and authorize a separate
node/task outside this session. Its checker change involves the same
`scripts/check_bcs1_evidence_map.py` units as A and its own validation record;
then the regression node would supply the new Rust integration test, map evidence
and its validation record. Future test/validation paths remain UNDETERMINED.

**Checker assertions.** Same conditional units as A: 14, 26, 88, 270–274,
279–290 and a closure-citation assertion analogous to 89–94 / 275–277.
The two S08 NOT_COVERED locks and three preserved PARTIAL citations stay fenced.
The node split must preserve valid intermediate states: changing FU_HEAD (26)
requires the matching map heading (68) in that same node, or table_rows at
134–138 reports `expected one section`. Allocation of the other map edits,
closure-citation activation and table changes between nodes is
**UNDETERMINED — User/orchestrator**; a checker-only intermediate state cannot
be assumed to pass. The regression objective/acceptance would remain unchanged.

**Self-test fixtures.** Same affected fixtures as A (364, 377–379), the two new
negative cases and resulting count at 403; 387 is status-independent. The
separate node must keep its own self-tests passing before the regression node
runs. Both nodes require their planned non-author A2 reviews; neither is supplied
by this builder inventory.

**Map rows.** Final conditional six-row evidence/status changes, Counts and §3
changes are the same as A, with two S08 rows still NOT_COVERED. The heading
synchronization above is required if FU_HEAD changes; the rest of the allocation
and the six COVERED/PARTIAL targets remain UNDETERMINED.

**CI steps.** Adapting the existing checker needs no workflow edit;
protocol.yml:253–254 verify each node's valid intermediate/final map and
self-tests, while 316 runs the later integration test. ktx-kernel.yml:103 stays
unchanged. If the owner instead chooses a new `scripts/check_*.py`, the existing
[check_ci_checker_wiring.py](../../scripts/check_ci_checker_wiring.py):4–5,19–32
requires protocol.yml wiring plain and `--self-test` (the fixed stage-5
self-test-only exception does not extend to a new checker).

**Acceptance satisfied / unmet.** Could meet current regression acceptance only
after both authorized nodes, their passing checks and two A2 reviews. A
preparatory checker node alone leaves the six regression gaps unmet. Nothing
changes or resumes now; ordering and intermediate-state design belong to the
User/orchestrator and A2 review.

### Per-option comparison

These are inventory units, not effort, coverage or completion measures.

| Option | Checker lines touched | Self-test fixtures | Map rows | CI edit | Regression acceptance | Owner |
|---|---|---|---|---|---|---|
| A | 14, 26, 88, 270–274, 279–290; new closure pins analogous to 89–94 / 275–277 | 364, 377–379; two new negatives; 403 count; 387 unchanged | Six §2 rows; Counts 66; §3 68–81; two S08 rows stay NOT_COVERED | None | Conditional on authorization, six tests/map updates, checks and A2 | User/orchestrator; non-author A2 review |
| B | None | None | All eight stay NOT_COVERED; possible prose only | None | Current acceptance unmet; revised input required | User/orchestrator; source design review rejected B |
| C | Same units as A in separate node; valid intermediate-state design required | Same affected units as A in separate node | Same final six-row impact as A; cross-node allocation UNDETERMINED; heading synchronized | None for existing checker; plain/self-test wiring if a new checker is chosen | Only after both nodes and two A2 reviews | User/orchestrator; two non-author A2 reviews |

## Still open — by reference

Owners for L1/L2/A2/A4 copy the October 25 closure table verbatim; A5 copies the
October 26 AI delegation addendum. Options remain only at the linked sources.

| Item | Original owner (as recorded) | Source |
|---|---|---|
| L1 · `k-stage5-durable-tx` host | User / supervisor (build host) | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) |
| L2 · `rs-4-l2` host | User (spend / environment); Astra (workload) | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행); [impact inventory](RS4_L2_DECISION_IMPACT_INVENTORY.md) |
| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` loopback host | Supervisor / repository owner controlling the execution host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) |
| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | User / repository owner | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) |
| A5 · AI delegation check order | Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge. | [October 26 addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md) |

A4 is listed STILL OPEN by the October 25 closure; it is not named in this
node's four-item carry-forward list. Including it by reference is an explicit
design-plan deviation preserving the ledger; no disposition is inferred.

## Non-claims

- No option, node disposition, program status, evidence grade, policy value,
  owner, acceptance criterion or protocol command is selected or changed.
  No node is resumed, completed, retired or retried by this document.
- No checker, map, contract, test or source is changed; the blocked regression
  node is not redone. Its scope/acceptance stop remains open with the
  User/orchestrator and required non-author A2 review. The AI delegation class C
  stop remains at its linked source and owner.
- Earlier ledgers and evidence are preserved. Both locked kernel blobs and
  `reference/v0.3-rc1/**` stay byte-identical. No change under `reference/`,
  `docs/contracts/`, `runtime/`, `.aiops/`, `docs/tasks/` or CI.
  `scripts/check_bcs1_evidence_map.py`, `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md`
  and kix-bcs1 sources/tests remain byte-unchanged.
- The RS-4 acceptable load level remains UNDETERMINED (User), and all open
  contract/readiness rows retain their owners and unresolved values.
- No hosted CI result transfers from another SHA. This is builder evidence,
  not non-author exact-HEAD review, an Astra audit or a merge-ready claim.
- No real funds, PG/bank/KYC call, public endpoint, Sui testnet/mainnet,
  R2, own replication/consensus/storage engine, coin/TIX module, secrets or
  production runtime is introduced. No production readiness, durability,
  distributed fencing, bank exactly-once, chain finality, legal compliance
  or protocol-completeness claim is made.
