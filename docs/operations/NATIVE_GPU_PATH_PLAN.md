# Track K stage 8 — native GPU path plan

Node: `k-stage8-gpu-plan`. Date: 2026-11-14. Status: **PLAN_ONLY**.
This is a builder-authored preparatory document for A2 non-author review.
GPU implementation, equipment use/spend, runner provisioning and activation remain
**HOLD**. No GPU measurements have been run. Accepting this plan grants none of
those capabilities or permissions.

## 1. Scope, authority and prerequisites

The task input is the supervisor-supplied node specification and design; there
is no task issue or node document under `docs/tasks/`. This session is explicitly
outside ASTRA program mode. [Development plan](../DEVELOPMENT_PLAN.md) §§5/13
and [roadmap R-11](../decisions/PROGRAM_ROADMAP_20260930.md) authorize a document
after CPU/SQL audit, not stage-8 execution. The line-number hints in the task have
drifted; those sections, [AI GPU data plane](../../runtime/AI_GPU_DATA_PLANE.md)
§9, [native execution](../../runtime/NATIVE_GPU_EXECUTION.md), and
[performance profile](../../runtime/PERFORMANCE_PROFILE.md) §8 anchor this plan.

The [backend decision](../decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md) §6
specifies option A: local, non-production PostgreSQL **17.11 (Debian
17.11-0+deb13u1)**, single process/writer, default off, production flags false;
R2, replication, consensus and existing holds stay closed. Its section is
byte-identical to User-merge record #140, commit
`bb193efb5d238581096372c8a20bee1271dfe4df`, in local ancestry. This establishes
the recorded scope, not current backend availability or production adoption.

Dependency `k-stage7-cpu-analytics-sql-audit` is present in cached main via #451,
merge `f146930d0d8d29263b0e013c10b566050bf62b85`; its implementation is
`298e1e8cbe151a0aeefa7a63cbeb66ed22b24092`, delivered through merge head
`f45284c8f265c013c1e5f33239219d057e25e4ea`.
The [stage-7 report](../../validation/2026-11-13-k-stage7-cpu-analytics-sql-audit/README.md),
[coverage](../../validation/2026-11-13-k-stage7-cpu-analytics-sql-audit/coverage.md)
and [merge-round evidence](../../validation/2026-11-13-k-stage7-cpu-analytics-sql-audit/merge-resolution.md)
record actual local Rust/Polars/DuckDB runs, including the PostgreSQL source run
and its limits. They leave A2 non-author review and exact-head CI outstanding.
Local ancestry proves delivery presence; authoritative review/CI completion is
**UNVERIFIED — supervisor** under this session's no-network rule. Historical
status maps predate this harness and are not evidence that it is absent.
This plan neither declares that dependency DONE nor substitutes local tests for
its missing gate evidence. Independent, explicitly authorized document work
proceeds with that input unavailable; future GPU implementation stays HOLD.

Apply [completion design §5.1](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md):
`ADOPT` requires the specified actual capability, approved inputs and current
evidence; `DEFERRED` (including none yet), ambiguous/unknown outcomes and
`DECLINED` keep affected implementation/consumption WAITING/HOLD and retain all
descendants in the full catalogue. A declined branch requires a separately
reviewed, User-merged applicability/plan revision binding affected definitions
and digests before removal or a decision-bound nonimplementation deliverable.
Decision-document merge alone grants no qualification, release or completion.
This plan adds no decision interpreter or automatic completion predicate.

## 2. Semantic acceptance matrix

Authority is [Feature Semantics v1](../../runtime/FEATURE_SEMANTICS_V1.md), then
pure Rust reference semantics. Polars, DuckDB, native libcudf and supported
`cudf-polars` cases participate; agreement among engines cannot overrule the
contract. Stage 7 is source-informed, not clean-room or independent review.

In the table, `audit` means
`runtime/crates/kix-analytics-audit/tests/conformance.rs`; `IR tests` means
`runtime/crates/kix-feature-ir/tests/{schema_bound,validator_matrix}.rs`;
`scalar` means `runtime/crates/kix-feature-semantics/src/lib.rs`.
**Sufficient** is limited to the named audited CPU fixtures; **partial** means
broader behavior remains unproved; **not covered** means no GPU evidence.
Every future GPU column is a planned check, currently NOT_RUN.

| Requirement | Contract | Existing evidence | Coverage | Future GPU check | Unresolved owner |
|---|---|---|---|---|---|
| NULL filter/join/group | §2: NULL predicate drops; explicit EQUAL/UNEQUAL and INCLUDE/EXCLUDE; aggregate IGNORE | audit `null_semantics`, `join_semantics`, `export_binding`; scalar nullable helpers | Sufficient audited CPU subset; GPU not covered | Same datasets with null/non-null keys, all join kinds, both policies, duplicate multiplicities and left-join NULL outputs | Backend implementer; A2 reviewer |
| Sort and result multiplicity | §§3/8: direction, FIRST/LAST, stable relative order when required | audit `ordering_semantics`, `comparator_sensitivity`; `support/compare.rs` | Sufficient CPU ASC/DESC × FIRST/LAST stable fixtures; partial general plans | Exact required row order/ties; unspecified order canonical sort of complete logical rows preserving duplicates, never set equality; include order/duplicate mutation negatives | Backend implementer |
| Empty/all-null aggregates | §4: COUNT=0 on empty, COUNT(column) ignores NULL; SUM/MIN/MAX/MEAN=NULL on empty/all-null | audit `null_semantics`; scalar `aggregate_empty_semantics_are_fixed` | Sufficient audited CPU fixtures; GPU not covered | Empty global aggregation, all-null and grouped inputs, exact counts/nulls | Backend implementer |
| Integer arithmetic and overflow | §4: ERROR, never wrap/saturate | audit `overflow_semantics`: I64/U64 Add/Sub/Mul/SUM boundaries and `overflow-before-limit` | Sufficient monotone CPU boundary fixtures; partial general SUM semantics | Compare checked results/error class; earlier overflow must survive later `Limit(0)` or other result-discard optimization | Backend implementer; cancellation-sensitive intermediate SUM order UNDETERMINED — User/Astra |
| Exact IDs, integers and money atoms | §§6/8; fixed binary widths preserved | audit `export_binding`, `money_roundtrip_and_version_rejection`; export type checks | Sufficient CPU lossless fixtures; partial full device interchange | Bitwise fixed-ID/integer equality; u128 exact logical equality including >2^53 and max; no float/narrowing conversions | Backend implementer |
| Fast64 identity/range/version | §6: `(asset_id, registry_version)`, registry hash and `atoms <= executionMaxAtoms <= i64::MAX`, checked each export | IR tests `fast64_rejects_wrong_asset_version_or_hash_at_export`, `fast64_identity_mismatch_precedes_amount_range_for_each_identity_field`, `fast64_checked_range_is_inclusive_at_claim_and_capped_at_i64_max`, `fast64_checked_claim_is_not_inherited_across_registry_versions` | Sufficient scalar guards; authenticated execution/adoption partial | Reject mismatched asset/version/hash and out-of-range inputs before launch; changed version never inherits old admission | Fast64 adoption/authenticated registry execution policy UNDETERMINED — User/Astra |
| Wide128 | §6: lossless export only; SUM/MEAN/Arithmetic unsupported | audit `money_roundtrip_and_version_rejection`, IR tests | Sufficient CPU fixture roundtrip and rejection; GPU not covered | Preserve all 128 bits through documented Arrow representation; unsupported arithmetic fails before launch; no truncate/saturate/float | Backend implementer; representation reviewed before implementation |
| Categories/dictionaries | §7: vocabulary + semanticCode or equivalent stable identity | export mapping, audit `export_binding`; scalar `category_equality_is_semantic_not_dictionary_position` | Partial: decoded CPU values, no general device dictionary reencoding coverage | Compare decoded logical values with vocabulary identity; permute indices/dictionaries without altering answer; reject vocabulary mismatch | Backend implementer |
| F64 terminal-only | §§5/8/10: finite MEAN or root DIVIDE_TO_F64; only Limit afterwards; zero/null denominator => NULL | IR tests/scalar tests; audit exact-representable means (e.g. 2.5) | Partial; no general tolerance or GPU numerical evidence | Reject F64 keys/input/follow-on query/arithmetic, NaN/Inf; exercise divide null/zero; general approximate conformance HOLD pending policy | Versioned tolerance and normalization UNDETERMINED — User/Astra |
| Schema/plan admission and point in time | §10; data-plane §7; authenticated-export contract | IR tests; audit `export_binding`, `money_roundtrip_and_version_rejection`; `analytics_audit.test_admission` | Sufficient audited CPU version/admission negatives; partial production trust | Wrong catalog/version/digest/source bindings rejected before allocation; no future-observation joins; preserve snapshot bindings in §3 | Supervisor for source trust; backend implementer |
| Nullable arithmetic | v1 has no explicit propagation rule (Class B) | audit `overflow_semantics` `nullable-*`: NULL propagation in Rust and pinned engines | Characterization only; not adopted semantics | Retain as separately labeled characterization; do not promote an observed match into normative conformance | User/Astra |
| Comparator sensitivity | §8 | audit `comparator_sensitivity`: value/null/duplicate/order/error mutations | Sufficient named CPU comparator negatives; partial GPU adapter normalization | Deliberate GPU-result mutations must fail; engine errors must not be compared by arbitrary text or treated as successful empty rows | Backend implementer; semantic-error ABI mapping unresolved |
| Device ownership, pool/stream reuse, transfer/spill | data-plane §9 items 6–8 | Header and design only | Not covered | Ownership/fault tests in §3 and timings in §4 | Native implementer/runner owner |

Reuse stage 7's `tests/support/{data,reference,polar,duck,compare,mod}.rs`,
`analytics_audit/prepare_export.py` and `analytics_audit/report.py`, plus IR
validation and scalar helpers. These are test-only helpers, not production
compilers. A later implementation task must explicitly authorize any extraction
into reusable backend code. Extend the fixture matrix for GPU gaps rather than
duplicating the CPU regression suite. No new test or harness is added here.

## 3. Native integration boundary and implementation prerequisites

The existing [header](../../runtime/native_gpu/include/kix_gpu.h) is unchanged:

| ABI item | Existing names/fields | Planned responsibility |
|---|---|---|
| Context | `KixGpuContext` | Long-lived libcudf/RMM context per GPU/NUMA placement or measured equivalent |
| Options | `KixGpuOptions`: `device_id`, `stream_count`, `device_pool_bytes`, `pinned_host_pool_bytes` | Explicit reviewed configuration; no default sizing/budget invented |
| Input | `KixGpuInput`: `slot`, `schema`, `array` | Bind input slots to trusted source schemas and Arrow C Device arrays |
| Plan bytes | `KixByteSlice`: `data`, `len` | Borrowed registered KIX-BCS1 plan bytes; lifetime/validation bound before native admission |
| Lifecycle | `kix_gpu_context_create`, `kix_gpu_context_destroy` | Own device/stream/RMM resources; cleanup all initialization-failure paths |
| Execution | `kix_gpu_execute_feature_plan_v1` | Execute validated supported plans, returning ArrowSchema/ArrowDeviceArray under release-callback rules |
| Diagnostics | `kix_gpu_last_error` | Diagnostic text only; never business authority |

Future Rust safe wrapper confines unsafe code to a narrow FFI crate. A bounded
dedicated executor owns persistent contexts, device pools, pinned-host pools and
streams; it must run outside PostgreSQL transactions and Tokio core scheduler
threads. Reject unsupported plans before dispatch; explicitly permitted CPU
Polars fallback runs outside OLTP and is separately reported. Python is absent
from the target native runtime path. Pool exhaustion/backpressure must remain
distinct from unsupported plans and arithmetic failures; no automatic retry.
Queue limits, pool sizes and overload policy require approved inputs rather than
new product defaults.

`FeaturePlanV1` currently has `plan_id`, `source`, `stages`. Backend admission
requires `validate_with_schemas(catalog)` and its `ValidatedFeaturePlan` result;
structural `validate()` alone is insufficient. Catalog provenance is a separate
trusted export boundary, not a query-supplied schema. Registered KIX-BCS1 encoding,
schema registration, parser/allocation limits and golden vectors remain future
prerequisites: the header requires them but supplies no implementation. This plan
assigns no schema ID, wire bytes, new command or parser policy. Keep authenticated
source cuts distinct from projection watermarks; MVCC snapshot/LSN alone cannot
prove source completeness.

Preserve `FeatureSnapshot` bindings exactly (data-plane §7):

```text
featureSnapshotId
featureSchemaVersion
featurePlanVersion/planDigest
asOfObservationCursor
asOfCommitPosition
sourceDatasetVersions
policyVersionIds
assetRegistryVersionIds
featureHash
```

Before implementation, a separately reviewed ABI design must resolve:

- Whether execute returns synchronized data or pending device completion;
  synchronization-event ownership, stream ordering, cancellation and context
  destruction while work is outstanding. There is no asynchronous completion API
  in the header; do not infer one from a desired Rust completion handle.
- Borrowed schema/array/plan-buffer lifetime, callback ownership transfer and
  output state on partial failure; exactly-once release without double free,
  leaked references or use after release. A Rust wrapper cannot promise these
  before the native contract is settled.
- Context/thread safety, cross-stream sharing and diagnostic lifetime:
  `kix_gpu_last_error` says thread-local/context-local without selecting one.
- Mapping semantic overflow/schema errors onto the existing statuses
  `KIX_GPU_OK`, `KIX_GPU_INVALID_ARGUMENT`, `KIX_GPU_UNSUPPORTED_PLAN`,
  `KIX_GPU_OUT_OF_MEMORY`, `KIX_GPU_CUDA_ERROR`, `KIX_GPU_INTERNAL_ERROR`.
  The header has no distinct semantic-overflow status. Do not invent an enum,
  change a protocol error or depend on free-form error text as a semantic code.
- Concrete libcudf support for each Arrow type, Wide128 lossless representation,
  fixed binary widths, timestamp units/timezone and decoded vocabulary identity,
  checked against selected software pins. Zero-copy is conditional, not assumed.

Future tests must exercise producer callbacks retained until all consuming work
finishes, consumer output release exactly once, synchronization events across
streams, borrowed buffers alive through completion, cleanup after partial output,
context-create failure, OOM/device loss/CUDA errors, teardown and repeated reuse.
Compare creation/allocation counters across requests to detect per-request
context/allocator creation. GPU failure must not consume OLTP workers, leave
transactions open or alter economic authority; demonstrate isolation with
synthetic fault injection. These tests and the ABI design are future work.

## 4. Transfer-inclusive measurement protocol

Use the existing name `GPUCrossoverProfile` (performance profile §8). The fields
below are a **proposed documentation record**, not a registered wire schema.
All measurements/results are **NOT_RUN**. Select scales/repetitions and comparison
boundaries before a future authorized run; they are experimental inputs, not SLOs.

| Record group | Required observations |
|---|---|
| Identity/provenance | Workload family and plan/dataset hashes; source export trace, cut/watermarks; schema, feature/plan/semantics versions and digest; snapshot bindings from §3; run source commit and raw artifact hashes |
| Host/device | CPU model/count/affinity, RAM/NUMA, GPU model/count/VRAM, topology and actual PCIe/NVLink link, host/device placement, operating system, driver and power/clock settings observed |
| Software | Exact Rust/C++/build-tool pins, Arrow, CPU Polars, DuckDB comparison tooling, CUDA, RAPIDS/libcudf/RMM and cudf-polars; image/build digest and allocator configuration |
| Shape | Rows and actual bytes per input/output; types, null density, key cardinality/skew, joins, sorting, batch size; host-origin versus device-resident; compression/row groups where applicable |
| Run method | Cold/warm labels, initialization boundary, warmup/repetition count, CPU/GPU execution order, concurrency/queue load, cache state; all raw samples and failures, clock domains/units |
| Coverage/resources | Per-operator supported/executed backend, fallback count and reason, allocations/pool high-water/reserved/live bytes, pinned-host use, spill bytes/time/target, transfer bytes, OOM and failed-run evidence |
| Outcome | Semantic comparison evidence, CPU and native GPU end-to-end wall times, phase timings, summary method/spread, included/excluded costs, crossover outcome with exclusions; no success from failed/skipped/fallback cases |

Measure a monotonic host wall-clock span from admission of a complete request to
a host-visible result with required synchronization and cleanup. Record release
separately as well as including its cost in the selected full-cost boundary.
Record queue entry, service start and completion to expose small-job waiting.
The phase observations must include:

1. Schema/plan/export validation and conversion/materialization.
2. Executor queueing and scheduling.
3. Host-to-device transfer (bytes, pinned/pageable staging and actual completion).
4. Device compute (device events on the actual executing streams).
5. Synchronization and host waiting for visibility.
6. Device-to-host transfer where a host consumer needs the result.
7. Output/input release callbacks, resource return and cleanup.

Track cold context initialization separately from repeated execution with a
persistent context. Report two distinct scenarios: **host-origin with host
consumer** (full transfers and conversion) and **device-resident consumer**
(residency/ownership provenance, any required initial load amortization disclosed).
Never present device-resident compute time as host-origin end-to-end latency.
CPU and GPU must consume the same logical data and emit the same required result
under the same validation, materialization, cleanup and cache boundaries. List
one-time authenticated-export work as shared or charged identically; disk scans
and Parquet decoding cannot disappear from just one comparison.

For overlapping streams/transfers, retain event dependency spans and critical
path plus independent wall time. Phase sums need not equal wall time: do not add
overlapping host/device intervals or CPU wait already included in transfer
completion. Time CUDA events with their device clock and host intervals with a
host monotonic clock; record the method linking them, without subtracting
timestamps from different clock domains.

Start with stage-7 workload families: filters/projections, joins, group aggregates
and stable sorts, with CPU boundary fixtures plus scaled synthetic datasets.
Preserve null/skew/type distributions across scales. Include a small-job queued
case, a large-job memory/spill case and GPU failure isolation. Dataset sizes,
arrival rates, run counts, spill policy and caps are **UNDETERMINED — benchmark
owner/User**, not invented product values. Measure batch sizes/pool/stream options
only after equipment and experiment inputs are authorized.

Retain the existing crossover gate: **one workload family wins at three
consecutive scales with zero fallback**. Declare what “wins” compares (the same
full-cost end-to-end wall-time statistic and treatment of variation) before
running; retain raw samples and semantic PASS evidence for all three scales.
No new speedup percentage, global row threshold, latency SLO or automatic
production routing rule is added. A win justifies considering native work;
it does not authorize spend, backend adoption, activation or production use.

## 5. Dedicated NVIDIA CI runner options and costs

No inventory or quotes were verified: this session prohibits network and equipment
use. No model, provider, host, region, spending limit or operating budget is
selected. All numeric costs are **UNDETERMINED — User/procurement/provider**.

| Option | Compatibility/availability evidence needed | Cost entries to obtain | Constraint/tradeoff |
|---|---|---|---|
| Owner-provided compatible NVIDIA host | Owner consent/availability, GPU architecture/VRAM, driver/CUDA/RAPIDS compatibility, host topology and isolation capacity | Electricity/power and cooling, maintenance/warranty, administration and opportunity cost; existing hardware is not cost-free | Could avoid acquisition; compatibility and exclusive scheduling remain unverified |
| Dedicated purchased workstation/server | Vendor configuration and supported software matrix, RAM/VRAM/topology, power/cooling capacity, warranty and service availability | GPU and host acquisition, RAM, storage, delivery/tax, power/cooling, warranty, maintenance and administration | Dedicated control; upfront spend and ownership burden require User decision |
| Rented dedicated GPU capacity | Provider's dedicated isolation terms, exact GPU/VRAM, driver/image support, capacity/region and billing terms | Quoted hourly rate, minimum/increment/idle billed duration, persistent storage, transfer/egress, taxes and administration | Flexible experiment duration; provider billing and data/credential boundaries require User decision |

Each future quote must carry: option/configuration, **currency, quote date, source
or written quote reference, validity, region, taxes (included/excluded), billing
unit/minimum, assumptions and named owner**. These are currently UNDETERMINED
(User/procurement/provider); “no quote obtained” is not a zero-cost quote.
Maintain hardware/software compatibility evidence with the quote because an
incompatible low price is not a usable option.

```text
rental cost = quoted rate × billed hours + ancillary charges
ownership cost over a stated horizon = acquisition + operating + maintenance costs
```

For ownership, disclose power × hours × tariff, cooling assumptions, warranty,
storage replacement and administration; do not double-count bundled items. If
comparing amortized rates, the horizon, utilization and residual value must be
explicit owner-supplied assumptions. Report one-time and recurring costs
separately. Hours, rates, tariffs, horizon, currency, tax, utilization and total
budget stay UNDETERMINED. No procurement or rental is needed to complete this plan.

Future runner qualification must pin a mutually compatible **driver, CUDA,
RAPIDS/libcudf, RMM, Arrow, cudf-polars, Rust/C++ compiler/toolchain and OS/image**
tuple with hashes and compatibility sources; version numbers are not selected
here. Use isolated trusted jobs and synthetic authenticated fixtures. Do not run
untrusted PR code with GPU host/registration credentials. The runner owner must
define isolation, job teardown and resource accounting before activation; register
and activate through a separately authorized owner workflow. Missing GPU,
driver/library, engine or unsupported required fixture is a failing GPU lane,
never a skip disguised as conformance. CPU-only CI stays distinct.

Trace all eight required checks from data-plane §9 into the future lane:

| # | Required check | Future evidence |
|---|---|---|
| 1 | Feature IR → Polars Rust | Same validated fixture/cut/catalog; CPU reference comparison |
| 2 | Feature IR → native libcudf | Same fixtures, semantic results/errors and explicit native execution |
| 3 | Supported subset → cudf-polars | Named overlap matrix, raise-on-fail/no-fallback; unsupported cases labeled outside overlap |
| 4 | Integer/fixed-width exact match | Exact IDs/atoms and width/version/money negatives from §2 |
| 5 | Unsupported operators fail closed or explicit CPU outside OLTP | Pre-launch rejection; separately authorized fallback trace; fallback never counts toward GPU performance |
| 6 | ArrowDeviceArray lifetime/sync events | Callback/lifetime/stream/partial-failure cases in §3 |
| 7 | RMM pool/stream reuse | Creation/allocation counters, repeated-request tests and teardown/leak checks |
| 8 | Transfer and spill metrics | Raw phase events, bytes/resources and full-cost profiles from §4 |

## 6. Decision gates, delivery and remaining uncertainty

| Gate | Required action/evidence | Owner; current state |
|---|---|---|
| Document acceptance | A2 non-author exact-head review of semantics, ABI gaps, measurement boundaries and all eight checks; exact-head KTX and KIX workflows | Supervisor/reviewer; pending, no self-approval |
| Dependency gate | Authoritative stage-7 A2/CI evidence at delivered head; maintain actual local backend/cut evidence | Supervisor; UNVERIFIED here |
| Semantic policy | Versioned F64 tolerance/normalization, cancellation-sensitive SUM order, nullable arithmetic contract clarification and Fast64 adoption where needed | User/Astra; UNDETERMINED, affected execution HOLD |
| Native implementation | Separate authorized task for wire schema/golden vectors, ABI resolutions, safe wrapper/bridge/executor, tests and supported-operator matrix | User/design authority; HOLD |
| Equipment and operating cost | Compatible inventory/quotes, selected option, cost/budget/operating responsibility and explicit spend/use authorization | User/procurement/runner owner; DECISION_REQUIRED before use/spend |
| Runner activation | Approved credentials/registration/isolation, qualified pinned tuple and complete native GPU check evidence | User/runner owner; HOLD |
| Performance qualification | Authorized experiment, semantics PASS, full-cost three-consecutive-scale/no-fallback evidence | Benchmark owner/reviewer; NOT_RUN |

If implementation needs equipment, money/paid services, credentials, production
runtime, public endpoints, Sui testnet/mainnet, real funds/PG/bank/KYC, a storage
engine, new coin/TIX module, product policy, new protocol command or consequential
out-of-scope change, stop before that action. Write root `DECISION_REQUIRED.md`
with need/options/recommendation/decider. No such action is needed for this
document-only deliverable; unresolved future inputs stay explicitly open here.
All locks in [program decisions §5](../decisions/PROGRAM_DECISIONS_20260928.md)
remain. The two kernel blobs, `reference/v0.3-rc1/**`, task documents, `.aiops/`,
authoritative contracts and CI remain unchanged.

The [builder evidence](../../validation/2026-11-14-k-stage8-gpu-plan/README.md)
records current source anchors and actual local checks. This plan reports no
GPU speed, measurements, equipment qualification, independent audit, backend
completion, production readiness, durability, chain finality or legal compliance.
Local documentation checks cannot supply any of those missing inputs.
