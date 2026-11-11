# delegated-exec-seeded-differential

Node: `plan-plan-delegated-exec-seeded-differential`. Adds one std-only integration test, `runtime/crates/kix-delegated-exec/tests/seeded_differential.rs`: a seeded differential and invariant test for the in-memory `DelegatedShow` map, in the style of `runtime/crates/kix-kernel-v5/tests/v4_differential.rs`.
Issue: none. Depends on: `rs-3b`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792193921 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `ed1d48d52d943f000511573b78ebcfbf3cf5c114` (no delta).

**This test is builder-authored and source-informed (the source of `kix-delegated-exec` and `kix-kernel-v5` was in view). Agreement of the map with a bare kernel is not an independence proof. It is not an independent PASS.** In-memory only: no chain client, no durability, no replication. `delegated_execution_enabled` stays `false`. RS-C03(b) and RS-C14 stay in-memory evidence and are not upgraded. No grade is raised.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Unchanged: every `src/`, `Cargo.toml`, `Cargo.lock`, `clippy.toml`, `tests/common/mod.rs`, other crates, `runtime/ARCHITECTURE.toml`, `reference/`, `.github/`, `.aiops/`, `docs/tasks/`.

## What the test does

- `SEEDS` = the eight values of `v4_differential.rs`; `STEPS` = 160 generated steps per seed (the delegating profiles prepend a 15-step fixed prologue). The LCG recurrence is the one of `v4_differential.rs`; `below` reads `state >> 33` because the low bits of that LCG are periodic (one deliberate deviation).
- Five profiles: `one-page-seat`, `one-page-ga` (strict: one page, no context defects, a skipped step when the map would refuse before the kernel), `multi-page` (seat 0..8, seat 8..16, gap, GA 20..26, GA 26..40, seat 40..70, limits small enough to reach `Capacity`), `multi-page-delegated`, `multi-page-delegated-settling` (fewer reserves, so pages settle and can be undelegated).
- Subject: `DelegatedShow`, public API only, wrapped in `catch_unwind` (a map panic becomes a reported divergence with the seed). Reference: one independent `kix_kernel_v5::Kernel` per page with the same scope, inventory, limits and fence, driven with the same commands. The model of pre-kernel refusals, cross-page bindings, GA lowest-free allocation and grant transitions is typed in from the module documentation of `kix-delegated-exec` and contract sections 5 and 10; it does not call the subject.
- Per step: `norm(map answer) == reference answer` for page-local commands; predicted pre-kernel refusals (`BundleTooLarge`, `CrossPageBundle`, `UnknownSlot`, `GaSpanningPages`, `WrongScope`, pinned-page `CommandConflict`, `GrantClosed`, `UnknownOrder`, `UnknownOperation`, synthesized `OrderExists` and `OperationAlreadyBound`) must be exactly the documented one. Grant transitions use a set oracle (the error must be one of the violated preconditions) and the reference kernel decides kernel-level refusals.
- After every step: `page_kernel(p) == reference` (`Kernel: PartialEq`), `page_fence`, `grant`, `grant_of_page`, `remaining`; an order id and a provider operation bind to at most one page; seat bundles stay inside their page and within `MAX_BUNDLE`, owned seats are disjoint and `owned + remaining == page length`; GA `free + held == page size`, holds disjoint, in range, sized as requested, equal to the lowest-free allocation, and `free.len() == remaining`; every stored command replays on its pinned page (`replayed: true`, same original) under a stale or garbage fence and clock 0, after capacity shifts.
- Cut invariants (delegating profiles): a fresh reserve or `mark_payment_unknown` on a cut page is `GrantClosed` (never accepted); `expire` and `observe_capture` under the current (tombstone) fence never answer `GrantClosed` or `ExecutionFenced`; stored first results still replay; `delegate_page` and `undelegate_page` refuse `Held` or `PaymentUnknown` pages; a failed transition (kernel `ClockRegression`) leaves the fence and epoch mirror equal to the model and is retried (prologue plus random steps).
- Failure message: `delegated-exec differential mismatch profile=<p> seed=<n>`, the step and detail, then `shrunk N steps: [..]` (remove-one-step shrink, as in `v4_differential.rs`).
- Coverage guard (`coverage_guard_every_family_rejection_and_grant_transition_occurs`): asserts at least 8 seeds and 100 steps, runs the full matrix and requires 62 labels: the 11 command families, 17 `MappingError` kinds, 6 reachable `KernelError` kinds, 6 `Rejection` kinds, 5 `ObservationOutcome` kinds, and the grant transitions (created, delegated, revoked, undelegated, partial revoke, revoke retry completed, failed and retried delegate and undelegate). Labels come from exhaustive `match` functions, so a new enum variant breaks the build. Exempt kernel errors: `InvalidConfiguration` (constructor only), `WrongScope`, `UnknownOrder`, `UnknownOperation` (the map answers before the kernel), and the commands outside the map API. Observed in this run: 62 of 62 hit.

## AGENTS.md section 7: existing coverage first

| Area | Class | Existing tests | What is new |
|---|---|---|---|
| range table | sufficiently covered | `range_table.rs` (7 tests) | nothing; this file only builds valid tables |
| routing, replay, binding | partially covered (fixed scenarios) | `routing.rs` (11 tests) | random interleavings; order and operation binding checked in every prefix; equality with the page kernel; replay of every stored command after every step |
| GA slots | partially covered (`ga_conservation_holds_across_mixed_sequences` is the only mixed sequence) | `ga_slots.rs` (7 tests) | conservation and the lowest-free rule in every prefix of long histories, across expire, capture and conflict |
| delegation fence | partially covered (fixed scenarios) | `delegation_fence.rs` (11 tests) | random interleaving of delegate, revoke, undelegate with all commands; retry from arbitrary states |
| boundary | sufficiently covered | `boundary.rs` (2 tests) | untouched and green: no dependency was added |

## Negative controls (test side, no source edit)

A wrapper (`Subject` with a `Fault`) perturbs one answer; each control requires `Err`, the message to contain `seed=<n>`, a non-empty shrunk history no longer than the original that still fails under the fault and passes without it. Observed first failures:

| Control | Profile | First failure | Shrunk |
|---|---|---|---|
| reserve replay reports `replayed: false` | `multi-page` | seed=1, stored command did not replay | 1 of 160 |
| `expire` `Ok(true)` becomes `Ok(false)` | `one-page-seat` | seed=1, step 12, kernel `Ok(true)` vs map `Ok(false)` | 2 of 160 |
| `GrantClosed` reserve becomes `Held` | `multi-page-delegated` | seed=1, contract says `GrantClosed` | 4 of 175 |

## AGENTS.md section 8: classification

- **B, contract undefined, reachable panic (open, not fixed here).** A matching capture at or after expiry on a still-held GA order makes the kernel release the inventory (`ReturnRequired`), but the map neither returns the slots to its free set nor drops the hold. Afterwards the map's free set is smaller than the kernel's `remaining()`; the next fresh GA reserve that the kernel accepts reaches `free.pop_first().expect("remaining >= count")` (`runtime/crates/kix-delegated-exec/src/lib.rs`, the `reserve` hold loop) and panics, with the order already held in the kernel. Contract section 5 states the free-plus-held mirror only for `expire`; it is silent on a late capture. Minimal reproduction, pinned by `open_defect_late_ga_capture_leaves_map_free_set_behind_the_kernel`: GA page `[0,4)`; `ga_reserve(1, 4)` (expiry 100) at ctx 1; `observe_capture` with the matching amount at ctx 150 (`ReturnRequired`, kernel `remaining() == 4`, map free set empty); `ga_reserve(2, 1)` with expiry 1,000 at ctx 151 panics. The differential also finds it when not excluded (`open_defect_is_found_by_the_differential_when_not_excluded`: `GA page 0: free 0 but kernel remaining 1`, seed 1, shrunk to 38 steps). The generator excludes exactly this trigger (`Profile::exclude_late_ga_capture`; label `excluded:late-ga-capture` is hit). **Follow-up candidate for Astra: a fix node (return the hold on `ReturnRequired`, or define the contract rule).** When fixed, the two characterization tests fail by design; delete them and the switch.
- **B, characterized by the model, not failed:** the map refuses before the kernel, so (1) a refused request stores no command record (a bare kernel stores `Rejected(Unavailable)` or `Rejected(InvalidRequest)`), (2) `UnknownOrder` and `UnknownOperation` precede the kernel's fence, clock, semantics and `Capacity` checks, and (3) the synthesized cross-page `Rejected(OrderExists)` and `Rejected(OperationAlreadyBound)` precede the kernel's `BusinessFenced`, `InvalidRequest` and `OperationQuarantined`. The model encodes the documented map order, so these are asserted as the map's rule, not as agreement with a bare kernel; the strict one-page profiles avoid them.
- **B, source-informed assumption:** `revoke_grant` walks pages in ascending index and stops at the first kernel refusal.
- **Not asserted:** cross-page event-key and retained-conflict quarantine behaviour. Capture event ids carry a page namespace so one event key is only recorded on one page.
- **A, matching:** every other asserted rule. No contract violation (class C) was found.

## Commands actually run

The runtime workspace could not be resolved offline in this environment: `cargo ... --locked --offline` fails with `no matching package named bcs found` (`kix-bcs1`'s dependency is not in the local registry cache). Local equivalent: a scratch workspace in `/tmp/kixws` outside the repository, with symlinks to `kix-types`, `kix-kernel`, `kix-kernel-v5`, `kix-delegated-exec` and a copy of `Cargo.lock`. `kix-bcs1`, `kix-feature-ir`, `kix-feature-semantics` were therefore not built or tested here; they are untouched by this change.

| Command | Result |
|---|---|
| `git hash-object` on the two locked files (before and after) | `69564b16...`, `b607996c...` both times |
| `cargo test -p kix-delegated-exec --offline --test seeded_differential -- --nocapture` (scratch workspace) | 10 passed; coverage 62 of 62 labels; 3 negative controls detected; open defect found |
| `cargo test --workspace --offline` (scratch workspace, 4 crates) | all green: `kix-delegated-exec` boundary 2, delegation_fence 11, ga_slots 7, range_table 7, routing 11, seeded_differential 10; `kix-kernel`, `kix-kernel-v5`, `kix-types` all passed |
| `cargo clippy --workspace --all-targets --offline -- -D warnings` (scratch workspace) | clean |
| `cargo fmt --all -- --check` (scratch workspace) | clean |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK`; 7 tests OK |
| `python3 scripts/check_docs_index.py` and `--self-test` | exit 0 both (`docs index ok: scanned=158 indexed=123 allowlisted=35`) |
| the other stdlib checks of the `protocol.yml` "Stdlib offline document checks" step (status register, RS profile traceability, read-model source map, I12 proof ids, delegation layer matrix, RS predicate evidence map; plain and `--self-test`) | exit 0 each |

## Non-claims

In-memory only: no chain client, no durability, no distributed fencing, no replication, no storage engine. `delegated_execution_enabled` stays `false`; nothing is enabled. RS-C03(b) and RS-C14 stay in-memory evidence and are not upgraded; no grade is raised; the RS predicate evidence map and the delegation layer matrix are not edited (adding this test to them is a follow-up candidate). The test is source-informed and not a clean-room independence claim. It does not test grant TTL, page size P, allowed-operation sets, cross-page event keys or quarantine, real clocks, or any chain behaviour. The map-versus-bare-kernel equality is asserted only for the shared commands on the paths described above.

## Remaining uncertainty and follow-up candidates

- The late GA capture defect above (fix node or contract rule).
- Cross-page event-key and quarantine semantics (undefined; not asserted).
- Adding this test to the RS predicate evidence map and the delegation layer matrix.
- The full runtime workspace (`kix-bcs1`, `kix-feature-*`) was not built offline here; the exact-head CI is the authority for it.
