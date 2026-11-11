# RS-4 L2 decision — per-option impact inventory

## 0. Basis and provenance

Builder-authored, dated 2026-10-26. Node:
`plan-plan-rs4-l2-option-impact-inventory`; issue: none; `depends_on: []`;
audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. The loop-proposed node is absent from
`.aiops/program.json` and has no task document under `docs/tasks/`.
Task input is the supervisor-supplied node specification and read-only design plan.
Source: KIX planner run 1792980988 (`/workspace/kix-run/logs/planner_1792980988`,
as supplied; no planner execution is claimed).

Observed cached `origin/main`, base and starting branch HEAD:
`fc11cdf0150e54ed38bb363f2ded7238c48c6e53` on
`agent/kix-plan-plan-rs4-l2-option-impact-inventory`.
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness
remains unverified. No local base delta was observed.

The source decision pointer is
`/workspace/kix-run/wt/rs-4-l2/DECISION_REQUIRED.md` (2026-10-15), quoted through
[October 22 ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행),
basis line 64. Only the in-tree ledger was read; the external pointer is not a
repository link. Draft PR #191's FAILED_MEASUREMENT record is **node input only**:
no PR content, measurements or numbers are imported or independently verified.
The [October 26 addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md) supplies the
presentation style. The [validation record](../../validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md)
contains derivation commands, raw outputs and local verification.

**This document selects no option, sets no value and changes no node state.**

## 1. Shared facts

### A. rs-4-l2 acceptance clauses

Source: [.aiops/program.json](../../.aiops/program.json), basis lines 469–476;
node title: “RS-4 L2: staged load validation at 16,384 slots”,
`audit_floor: A2`, `astra_auto_merge: true`.
These are source metadata, not an authorization for this builder to publish or merge.
The objective and acceptance are quoted verbatim:

> Objective: load validation at 16,384 slots. Label results exploration data; no SLOs; localnet on the builder machine. A measurement environment beyond it, or any spend, is DECISION_REQUIRED. Report public, private and delegated paths separately (docs/blueprints/rights-scale-v1/README.md lines ~497-507, 374-420).
>
> Acceptance: scripts, raw results, report; checks green.

The same spec also requires:

> Evidence per AGENTS.md §14; protocol and kernel checks green at the exact head.

This inventory supplies no measurement record or acceptance disposition.

### B. Decision ownership and open values

Ledger owner (verbatim): **User (spend / measurement environment), with Astra for any workload change.**

The acceptable load level remains **UNDETERMINED (owner: User)**, verbatim from
[host_conditions.py](../../reference/rights_scale/host_conditions.py), basis lines
21–22. No host, load, duration, interval, gap factor or threshold is set here.
Any workload change remains with Astra under the ledger owner sentence.
L2 workload denominators, scope and cut points below are
**UNDETERMINED — Astra (workload)**; this labels missing inputs and assigns no value.

### C. Map rows that cite RS-4 measurement

Selection rule: select §2 data rows whose cells contain `RS-4`, `rs-4`,
`load_plan` or `summarize_load`, or whose status is `MEASUREMENT_ONLY`.
This is a reproducible lexical inventory, not a claim that every measurement
obligation or dependent predicate has been found.

[RS_PREDICATE_EVIDENCE_MAP.md §2](RS_PREDICATE_EVIDENCE_MAP.md#2-map)
selects the following rows. “Missing or open” cells are copied verbatim;
statuses and owners are unchanged.

| Row ID | Basis line | Existing status | Citation / path relationship | Missing or open (verbatim) |
|---|---|---|---|---|
| RS-C14 | 42 | PARTIAL | `test_load_plan.py` public/private/delegated and separation via `test_summarize_load.py`; L1 load record; all three paths | The separation of per-path results is now asserted on a synthetic run report (a corrupted public snapshot fails only the public row); no real run report is checked, the delegated leg is in-memory only, and private resale, refund, reissue and key rotation are unimplemented and only stated as such. |
| RR-2 | 47 | PARTIAL | Owner cell cites RS-4; private `concurrent_revokes` at `load_plan.py:389–393` names RR-2(b) | Concurrent revocations on one root are tested only as a sequential stale-witness case, and the collision rate is unmeasured. |
| RR-5 | 50 | MEASUREMENT_ONLY | Private `shield` steps append to the one note tree; `load_plan.py:341–362` | Contention of `shield` on the one note tree is unmeasured. |
| RR-6 | 51 | MEASUREMENT_ONLY | Private invalidation and re-proof sequence; `load_plan.py:364–387` names RR-6 | The share of in-flight proofs one revoke invalidates and the re-proof delay are unmeasured. |

[RS_IM_EVIDENCE_MAP.md §2](RS_IM_EVIDENCE_MAP.md#2-map): **0 selected rows**.
Its basis line 66 says `MEASUREMENT_ONLY=0`; no §2 row contains the other
selection terms. IM-10 (line 44) mentions “measurement” but does not cite RS-4,
so is a lexical near-miss, not a selected row. IM-11 (line 45) is related capacity
context in §1D′ below, not an added member of this selection.

### D. Paths and denominators actually defined in the tree (L1 only)

Sources: [load_plan.py](../../reference/rights_scale/load_plan.py) lines 41–49,
523–585; [model.py](../../reference/rights_scale/model.py) line 48;
[rights_scale.move](../../reference/rights_scale/sui/sources/rights_scale.move)
line 73. Version is `kix-rs4-l1-load-v1`; `SEATS = model.LOCALNET_SHOW_SLOTS`
is **1,024**, page size 64, bundle bound 8, and public/private/delegated payment
shards are 4/1/4. These are existing test fixtures, not values for L2 or policy.

Default `requested` denominators are `seats_per_show=1024`, `shield_count=1024`,
`consume_count=32`, `invalidation_count=8`. `DEFAULT_SETTINGS` labels the shield
count the “depth-10 leaf-capacity boundary”. Its other fixture settings are
seed 20261014; seated 1024, GA 0; ZK depth 10, root history K 4, nullifier and
challenge shards 4 each; closed loop true, arrival rate 0; transfers 8,
admissions 8, refunds 16, revokes 16, reissues 2 and reservations 2.
No arrival-rate or capacity claim follows from these fixture settings.

G6 expands the defaults in memory and writes no scenario file. A planned step
is one top-level step, not a successful transaction or a right. Each parallel
probe has two child operations; they are not separately added to the top-level
step denominator. Predicate counts use `measurement_gap._is_predicate`:
a parallel probe, or an expectation other than `None`, `ok` or `any`.
Probe counts are subsets of predicate counts, not extra denominators to add.

| Path | Planned steps (L1) | Predicate steps (L1) | Named parallel probes (L1) | End-state check keys |
|---|---|---|---|---|
| public | 482 | 16 | 5: `same_page_issues`, `duplicate_slot_race`, `same_shard_attests`, `cross_shard_attests`, `bundle_race` | `pages` |
| private | 1221 | 14 | 1: `concurrent_revokes` | `pages`, `leaf_count`, `nullifiers`, `challenges`, `revocations` |
| delegated | 72 | 11 | 1: `shared_grant_reads` | `pages`, `grants`, `page_delegated_to` |

The check keys are also asserted by
[test_measurement_gap.py](../../reference/rights_scale/test_measurement_gap.py)::`test_end_state_check_names`
(lines 78–84). Workload echoes `invalidation_count` and `consume_count` are
excluded from end-state checks by `measurement_gap._end_state_checks`.
No measured-step numerator is supplied here.

Phase order and default top-level step counts, from `assign_phases(expand())`:

| Path | Phases in order (`phase=count`, L1 only) |
|---|---|
| public | `stage.create=5`, `probe.concurrent=19`, `stage.fill=367`, `probe.hot_slot=8`, `stage.ops=78`, `stage.cancel=5` |
| private | `stage.create=6`, `stage.issue=128`, `stage.shield_prefix=8`, `probe.boundary=8`, `stage.shield_rest=1012`, `stage.revocation=20`, `probe.concurrent_revokes=3`, `stage.consume=32`, `stage.negative=2`, `stage.reconstruct=2` |
| delegated | `stage.create=5`, `stage.delegate=4`, `stage.fill=40`, `probe.delegated=10`, `stage.cut=7`, `stage.stranded=6` |

The row-to-path relationships in §1C refer to this existing L1 structure;
they do not establish that any L2 script or record exists.

### D′. No defined 16,384-slot workload denominators

At this basis `load_plan.py` defines no 16,384-slot path or denominator.
Its CLI (lines 659–680) has `--expand` for output and only `--seed`,
`--shield-count` and `--consume-count` as settings overrides; the path builders
read the module constant `SEATS`. The in-process `expand(settings)` can merge
settings, but changing the requested header does not replace that constant.
No such override is used here.

| L2 path | Seats per show objective | Planned-step, phase, predicate, probe and private shield/consume/invalidation denominators |
|---|---|---|
| public | 16,384, per §1A | UNDETERMINED — Astra (workload) |
| private | 16,384, per §1A | UNDETERMINED — Astra (workload) |
| delegated | 16,384, per §1A | UNDETERMINED — Astra (workload) |

Related tree facts, not a new workload:

- [Blueprint](../blueprints/rights-scale-v1/README.md), basis line 161:
  “깊이는 ⌈log2 N⌉: 1,024 → 10, 16,384 → 14, 65,536 → 16.”
  Its L2 row (line 388) names 16,384 as the intermediate stage, not an achieved run.
- [RS-2 validation record](../../validation/2026-10-14-rs-2-private-path/README.md),
  line 127: “A 16,384-slot show (depth 14) would need power 15 and a different phase-1 file; that is an input for RS-4/RS-5, not a decision here.”
  Line 274 says: “A depth-14 profile (16,384 slots) needs ptau power 15, which the shared cache does not hold.”
  These are attributed historical record statements; cache contents are not inspected here.
- IM-11 in [the IM map](RS_IM_EVIDENCE_MAP.md) cites
  `claim_zk_rejects_a_show_larger_than_the_tree` in
  [zk_staging_tests.move](../../reference/rights_scale/sui/tests/zk_staging_tests.move).
  Capacity rejection evidence supplies no L2 measurement denominator.

This is an AGENTS.md §8 class B characterization of undefined L2 workload
inputs, as anticipated in the supplied design plan. No 16,384-slot counts are
extrapolated from L1, and no contract or script is changed.

### E. Downstream dependency fences

Source: [.aiops/program.json](../../.aiops/program.json), `depends_on` fields;
G7 extracts these exact edges. Under every option, while `rs-4-l2` remains
unresolved, these nodes remain dependency-blocked:

| Node | Relevant direct dependency | Relation to rs-4-l2 |
|---|---|---|
| `rs-4-l3` | `rs-4-l2` | direct |
| `rs-5-decision` | `rs-4-l3` | transitive |
| `k-benchmark-reproduction` | `rs-4-l3` | transitive |

Informational further edge: `k-local-program-closeout` depends on
`k-benchmark-reproduction`, so also has a transitive dependency on `rs-4-l2`.
The validation record notes this additional informational node.
Other prerequisites in the source remain intact. Selecting an option would
not itself produce an accepted L2 record; whether a future record satisfies
§1A is not determined here and remains with the §1B owners. This table describes
dependency edges, not a query of external node status or a resumption decision.

### F. Existing offline tools and their limits

[measurement_gap.py](../../reference/rights_scale/measurement_gap.py) computes
coverage on scenario/report pairs. Its
[test module](../../reference/rights_scale/test_measurement_gap.py) describes a
synthetic record shaped like a recorded L2 failure; this is in-tree synthetic
coverage, not verification or import of draft PR #191's external record.
[host_conditions.py](../../reference/rights_scale/host_conditions.py) records
host facts without a threshold or verdict and says it is not wired into the
L1 runner. Neither tool is invoked on a real measurement record or host here.

## 2. O1 — dedicated or quiet host

### Option text (verbatim)

[Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행):

> Run on a dedicated or quiet machine/VM (may involve cost): complete record, same scripts.

### Acceptance clauses

[rs-4-l2 source, §1A](#a-rs-4-l2-acceptance-clauses):

> Objective: load validation at 16,384 slots. Label results exploration data; no SLOs; localnet on the builder machine. A measurement environment beyond it, or any spend, is DECISION_REQUIRED. Report public, private and delegated paths separately (docs/blueprints/rights-scale-v1/README.md lines ~497-507, 374-420).
>
> Acceptance: scripts, raw results, report; checks green.

### Affected map rows

[Predicate map](RS_PREDICATE_EVIDENCE_MAP.md#2-map): **RS-C14, RR-2, RR-5, RR-6**;
exact open cells and row/path relationships are in [§1C](#c-map-rows-that-cite-rs-4-measurement).
[IM map](RS_IM_EVIDENCE_MAP.md#2-map): **none** under the same selection rule.
Naming an affected row does not change its status or imply the option resolves it.

### Path and denominator facts

[§1D](#d-paths-and-denominators-actually-defined-in-the-tree-l1-only) lists the only
defined fixture: public 482, private 1221 and delegated 72 planned L1 steps,
with their predicate/probe and shield denominators.
[§1D′](#d-no-defined-16384-slot-workload-denominators) records the missing L2
workload: every 16,384-slot path denominator remains
**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.

### Paths the option text leaves without data

None excluded by option text (“complete record, same scripts”). This describes intended scope, not acquired data or proven completeness. All three paths still lack new L2 data in this inventory.

### Blocked downstream nodes

As [§1E](#e-downstream-dependency-fences) shows, **`rs-4-l3`**, **`rs-5-decision`**
and **`k-benchmark-reproduction`** remain dependency-blocked while `rs-4-l2`
is unresolved. No option selection or acceptance is inferred. Informationally,
`k-local-program-closeout` retains its further transitive dependency.

### Owner and UNDETERMINED items

Verbatim owner: **User (spend / measurement environment), with Astra for any workload change.**

Environment or spend remains with User; any workload change remains with Astra. Host and spend are unresolved; allowed load remains **UNDETERMINED (owner: User)**.

## 3. O2 — idle builder window

### Option text (verbatim)

[Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행):

> Re-run on the builder machine in a quiet window with no other load: free, unreliable.

### Acceptance clauses

[rs-4-l2 source, §1A](#a-rs-4-l2-acceptance-clauses):

> Objective: load validation at 16,384 slots. Label results exploration data; no SLOs; localnet on the builder machine. A measurement environment beyond it, or any spend, is DECISION_REQUIRED. Report public, private and delegated paths separately (docs/blueprints/rights-scale-v1/README.md lines ~497-507, 374-420).
>
> Acceptance: scripts, raw results, report; checks green.

### Affected map rows

[Predicate map](RS_PREDICATE_EVIDENCE_MAP.md#2-map): **RS-C14, RR-2, RR-5, RR-6**;
exact open cells and row/path relationships are in [§1C](#c-map-rows-that-cite-rs-4-measurement).
[IM map](RS_IM_EVIDENCE_MAP.md#2-map): **none** under the same selection rule.
Naming an affected row does not change its status or imply the option resolves it.

### Path and denominator facts

[§1D](#d-paths-and-denominators-actually-defined-in-the-tree-l1-only) lists the only
defined fixture: public 482, private 1221 and delegated 72 planned L1 steps,
with their predicate/probe and shield denominators.
[§1D′](#d-no-defined-16384-slot-workload-denominators) records the missing L2
workload: every 16,384-slot path denominator remains
**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.

### Paths the option text leaves without data

None excluded by option text. No rerun occurs here and all three paths still lack new L2 data. The source calls this option “unreliable”; it defines no quantitative reliability criterion.

### Blocked downstream nodes

As [§1E](#e-downstream-dependency-fences) shows, **`rs-4-l3`**, **`rs-5-decision`**
and **`k-benchmark-reproduction`** remain dependency-blocked while `rs-4-l2`
is unresolved. No option selection or acceptance is inferred. Informationally,
`k-local-program-closeout` retains its further transitive dependency.

### Owner and UNDETERMINED items

Verbatim owner: **User (spend / measurement environment), with Astra for any workload change.**

The window and environment remain with User; any workload change remains with Astra. Allowed load remains **UNDETERMINED (owner: User)**. No reliability, idle-load or duration threshold is supplied.

## 4. O3a — reduced scope: public prefix only

### Option text (verbatim)

[Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행):

> Accept a reduced scope (e.g. public prefix only, or private and delegated first) as the L2 record: an Astra workload decision.

### Acceptance clauses

[rs-4-l2 source, §1A](#a-rs-4-l2-acceptance-clauses):

> Objective: load validation at 16,384 slots. Label results exploration data; no SLOs; localnet on the builder machine. A measurement environment beyond it, or any spend, is DECISION_REQUIRED. Report public, private and delegated paths separately (docs/blueprints/rights-scale-v1/README.md lines ~497-507, 374-420).
>
> Acceptance: scripts, raw results, report; checks green.

The acceptance clause “Report public, private and delegated paths separately”
and this option’s phrase “an Astra workload decision” are both retained;
this inventory does not adjudicate a reduced record against that acceptance.

### Affected map rows

[Predicate map](RS_PREDICATE_EVIDENCE_MAP.md#2-map): **RS-C14, RR-2, RR-5, RR-6**;
exact open cells and row/path relationships are in [§1C](#c-map-rows-that-cite-rs-4-measurement).
[IM map](RS_IM_EVIDENCE_MAP.md#2-map): **none** under the same selection rule.
Naming an affected row does not change its status or imply the option resolves it.

### Path and denominator facts

[§1D](#d-paths-and-denominators-actually-defined-in-the-tree-l1-only) lists the only
defined fixture: public 482, private 1221 and delegated 72 planned L1 steps,
with their predicate/probe and shield denominators.
[§1D′](#d-no-defined-16384-slot-workload-denominators) records the missing L2
workload: every 16,384-slot path denominator remains
**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.

### Paths the option text leaves without data

Under the named “public prefix only” sub-variant, private and delegated have no samples in that scope, and the public remainder after the prefix has no data. The cut point is **UNDETERMINED — Astra (workload)**. RR-2, RR-5 and RR-6 lose their cited private measurement path; RS-C14 lacks the private and delegated components plus the unrecorded public remainder. Which public predicates or probes fall after the cut is not determined.

### Blocked downstream nodes

As [§1E](#e-downstream-dependency-fences) shows, **`rs-4-l3`**, **`rs-5-decision`**
and **`k-benchmark-reproduction`** remain dependency-blocked while `rs-4-l2`
is unresolved. No option selection or acceptance is inferred. Informationally,
`k-local-program-closeout` retains its further transitive dependency.

### Owner and UNDETERMINED items

Verbatim owner: **User (spend / measurement environment), with Astra for any workload change.**

Scope and prefix cut point remain **UNDETERMINED — Astra (workload)**. Accepting reduced scope is the option’s own “an Astra workload decision”. Environment/spend remains with User; allowed load remains **UNDETERMINED (owner: User)**.

## 5. O3b — reduced scope: private and delegated first

### Option text (verbatim)

[Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행):

> Accept a reduced scope (e.g. public prefix only, or private and delegated first) as the L2 record: an Astra workload decision.

### Acceptance clauses

[rs-4-l2 source, §1A](#a-rs-4-l2-acceptance-clauses):

> Objective: load validation at 16,384 slots. Label results exploration data; no SLOs; localnet on the builder machine. A measurement environment beyond it, or any spend, is DECISION_REQUIRED. Report public, private and delegated paths separately (docs/blueprints/rights-scale-v1/README.md lines ~497-507, 374-420).
>
> Acceptance: scripts, raw results, report; checks green.

The acceptance clause “Report public, private and delegated paths separately”
and this option’s phrase “an Astra workload decision” are both retained;
this inventory does not adjudicate a reduced record against that acceptance.

### Affected map rows

[Predicate map](RS_PREDICATE_EVIDENCE_MAP.md#2-map): **RS-C14, RR-2, RR-5, RR-6**;
exact open cells and row/path relationships are in [§1C](#c-map-rows-that-cite-rs-4-measurement).
[IM map](RS_IM_EVIDENCE_MAP.md#2-map): **none** under the same selection rule.
Naming an affected row does not change its status or imply the option resolves it.

### Path and denominator facts

[§1D](#d-paths-and-denominators-actually-defined-in-the-tree-l1-only) lists the only
defined fixture: public 482, private 1221 and delegated 72 planned L1 steps,
with their predicate/probe and shield denominators.
[§1D′](#d-no-defined-16384-slot-workload-denominators) records the missing L2
workload: every 16,384-slot path denominator remains
**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.

### Paths the option text leaves without data

The named “private and delegated first” sub-variant includes those paths first; it supplies no actual samples. Whether public follows is **UNDETERMINED — Astra (workload)**: “first” states an order and does not settle final scope. No path is definitively excluded by that phrase alone. If public is omitted, RS-C14’s public component has no data; RR-2, RR-5 and RR-6 remain private-path obligations, not satisfied by naming their path.

### Blocked downstream nodes

As [§1E](#e-downstream-dependency-fences) shows, **`rs-4-l3`**, **`rs-5-decision`**
and **`k-benchmark-reproduction`** remain dependency-blocked while `rs-4-l2`
is unresolved. No option selection or acceptance is inferred. Informationally,
`k-local-program-closeout` retains its further transitive dependency.

### Owner and UNDETERMINED items

Verbatim owner: **User (spend / measurement environment), with Astra for any workload change.**

Final scope and ordering details remain **UNDETERMINED — Astra (workload)**. Accepting reduced scope is the option’s own “an Astra workload decision”. Environment/spend remains with User; allowed load remains **UNDETERMINED (owner: User)**.

## 6. Per-option comparison

All rows share the four §1C predicate-map rows and zero selected IM rows.
Counts are inventory units, not effort, coverage or completion measures.

| Option / sub-variant | Paths excluded or unresolved by option text | Rows lacking a cited path if scoped as stated | Downstream nodes still fenced while L2 is unresolved | Owner |
|---|---|---|---|---|
| O1 dedicated or quiet host | None excluded; no data acquired here | No path excluded; all four obligations remain open | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
| O2 idle builder window | None excluded; no data acquired here | No path excluded; all four obligations remain open | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
| O3a public prefix only | Private, delegated and public remainder; cut UNDETERMINED — Astra (workload) | RR-2, RR-5, RR-6; RS-C14 private/delegated components and public remainder | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
| O3b private and delegated first | Public inclusion UNDETERMINED — Astra (workload) | RS-C14 public component if public omitted; private obligations unchanged | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |

## 7. Non-claims

- No option is chosen or endorsed. No new numeric policy value, host, load,
  duration, threshold, cut point, L2 fixture or protocol command is set.
  Acceptable load stays **UNDETERMINED (owner: User)**; any workload change
  stays with **Astra**, under the verbatim §1B owner sentence.
- No measurement, localnet, host sampling, provisioning or spend occurs.
  No 16,384-slot denominator is derived. A synthetic offline test is not an
  L2 measurement. Draft PR #191 is node input only, not verified evidence here.
- No node is resumed, completed, retried or retired. No acceptance criterion,
  owner, map status, capability grade or program state changes.
- This is builder evidence, not non-author exact-HEAD review, an Astra audit,
  exact-head hosted CI evidence or a merge-ready claim.
- Both locked kernel blobs and `reference/v0.3-rc1/**` remain byte-identical;
  no `reference/**`, scripts, CI, `.aiops/`, task document or RS map changes.
- No real funds, PG/bank/KYC call, public endpoint, Sui testnet/mainnet,
  R2, own replication/consensus/storage engine, coin/TIX module, secrets or
  production runtime is introduced. No production readiness, durability,
  distributed fencing, bank exactly-once, chain finality, legal compliance
  or protocol-completeness claim follows.
