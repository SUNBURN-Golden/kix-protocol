# Task 003-C1 — generated crosswalk evidence gates

Issued by the orchestrator on 2026-09-21 following explicit user authorization
to take over the approved Devin follow-up. Immutable input for a new execution
session. This task authorizes test/evidence changes and a draft PR, not merge.

## Source and scope

- Base/current main at issue: `6332bca0f54cc2114d986b24ab218ace33a5df12`.
- Selective carry-forward source: `7f99812f4558e4802a51d5468da35754db693c43`.
- New branch: `agent/task-003c1-evidence-gates-20260921`.
- Reuse only the two test implementation files from that source; do not import
  old validation claims as current results. Keep PR #26 and old task immutable.
- Read root AGENTS.md, README, DEVELOPMENT_PLAN, BASELINES, AUTHORITY_MODEL_1,
  original 003-C task, ADR §§3/5/6, contract invariants/lifecycle, frozen tests.
- Fetch/record main before work; report access limitations and any base drift.

## Frozen inputs

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`: `d37ea7df55423c83bedee16bf12bdc8dd61f7cae`.
- `runtime/crates/kix-kernel/tests/support/model_v4.rs`: `f020860b86933bf7511befccdb833b0c532b3629`.

No production/model edits, including temporary mutations or formatting. No R2,
replication/storage/log, lifecycle/release/GC/index, workflow/lint weakening,
renaming, real PG/bank/chain execution, settings changes, or main writes.

## Required corrections

F01: In the generated differential path gate actual Kernel pre/post Clone+Eq
for contract-defined read-only calls: reserve replay and reserve errors, unit
errors (including InvalidTransition send), expiry errors, and capture errors
only where the contract excludes mutation. Do not blanket-gate capture Capacity
for a known conflicting event or successful capture replay/expiry checks, which
can advance time and/or quarantine. Add a test-only negative sensitivity check
showing the new equality guard detects a clock-only perturbation made through
public APIs while old comparisons do not. Never alter frozen kernel/model source.
The prior Devin injection patch was not supplied; do not claim its 662 figure
as independently reproduced without the missing code.

F02: Require single-field altered payload witnesses for four fields (order_id,
payment.operation, expires_at_ms, selection) crossed with three disjoint contexts
(normal, stale fence only, regressed clock only). Preserve broad existing classes.
Other payload fields must be unchanged for a single-field cell. No new owner-only
versus generation-only submatrix is required. Export counts and first witnesses.

F03: Preserve exact/strict-after UNKNOWN retry distinctions and add a same-order,
same ProviderOperation retry-refusal -> subsequent matching first capture anchor.
Retry must retain exact reserved slot, ownership and state; capture must be at or
after expiry, not cancelled, consume that reservation, become ReturnRequired,
and release owned inventory once. Include source step identities in evidence.
Do not count cancellation-caused ReturnRequired as this deadline anchor.

F04: Add a per-order ordered anchor: first ReturnRequired -> distinct-event matching
DuplicateEffect -> later distinct-event mismatch/Review -> reviewed=true send
InvalidTransition. Require phase/capture retention, no second inventory release,
sticky review and actual Kernel Eq on the final refused send. Store stable
order/operation and relevant source step identities for auditable witnesses.

F05: Seed the Row 7 cumulative gate only from retained Ok(Conflict) naming two
distinct bound operations. Record origin evidence and both order/operation IDs;
advance the relevant same order only through successful owner replacement,
actual expiry release, successful cancellation, then refused send. Keep broad
Capacity-origin coverage as supporting inventory, excluded from this gate.
Do not hardcode historical hit counts (9 retained / 4 Capacity).

Row 8 is already semantically sufficient. Preserve its coverage and export the
P2/config0/seed1 steps 18/20/23 identity evidence without duplicating fixed tests.

## Change boundary

Allowed implementation paths: `tests/e4_state_model.rs`,
`tests/support/coverage_v4.rs` under kix-kernel; one narrow test-only helper if
necessary; new `validation/2026-09-21-task-003c1-evidence-gates/README.md`.
This Task document is bootstrap-only. Existing task/model/deterministic/regression
sources and historical validation reports must remain unchanged.

Preserve historical trace(), baseline_cases(), relation_cases(), required_classes(),
shrink helpers and sensitivity tests, and CASES=256/STEPS=128/RELATION_SEEDS=64/
RELATION_STEPS=48. Reuse 003-C P1/P3 steering; change no generator unless a required
semantic path is demonstrably absent, and explain any narrowly necessary change.
No fixed copies of the deterministic Task 001 traces as property fixtures.

## Verification and acceptance

Use the repository/CI toolchain and --locked. Do not silently substitute or change
toolchain policy. If local execution is unavailable, report that and use exact-head
CI; never invent local results. Separate relation and baseline counts: all new
crosswalk anchors must reach their gates in the relation corpus alone.

Add minimal negative observer/harness tests for the new material distinctions.
Run frozen deterministic tests, E-4 baseline/relation/crosswalk, sensitivity/shrink,
workspace tests, fmt, clippy -D warnings, architecture checks where available.
Verify frozen blobs before and after. Export a current eight-row crosswalk with
actual counts, same-trace identities and limitations. No unresolved row is sufficient.

Create a draft PR; record full base/bootstrap/implementation/final head, changed
paths, frozen blobs, actual commands/results and both exact-head CI run IDs,
head_sha/status/conclusion. KTX and full protocol must both be completed/success
before describing verification as complete. Record final CI in PR text, not an
endless sequence of CI-reference commits. No merge or draft removal.

Implementation review is author-side verification, not independent final approval.
No formal proof, clean-room model, durability/performance, chain/bank or production
readiness claims follow from this task.
