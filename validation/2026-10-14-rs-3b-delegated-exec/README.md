# rs-3b — Rust delegated execution integration: page↔kernel inventory and GA counters (new crate)

Evidence for KIX program node `rs-3b`: the executor-side mapping of the extended
rights-scale profile (`docs/blueprints/rights-scale-v1/README.md` §6 rules 7–8, §8 row RS-3b;
`docs/contracts/RIGHTS_SCALE_PROFILE.md` §5, §10 items 7–8). A new in-memory crate,
`runtime/crates/kix-delegated-exec`, maps one `InventoryPage` or GA slot-range shard to one
`kix-kernel-v5` `Inventory`, so a show above the kernel's `MAX_SEATS = 4,096` runs as a set of
pages whose kernels operate concurrently, and maps the chain's anonymous GA slot ranges onto the
kernel's quantity counters with a deterministic lowest-free-slot choice.

**Everything here is an in-memory library fixture.** No delegated execution is enabled
(`runtime/ARCHITECTURE.toml` keeps `delegated_execution_enabled = false` and the architecture
verifier still passes). No chain client, grant expiry/TTL, allowed-operation set, page size P,
storage engine, consensus, or production runtime. The two locked kernel blobs and
`reference/v0.3-rc1/**` are byte-identical. Nothing below is a performance, durability or
production claim. This session did not commit, push, open a pull request, or edit `.aiops/`,
`docs/tasks/` or CI. The supervisor owns git.

## Identity

| Item | Value |
|---|---|
| Task | `rs-3b` — RS-3b: Rust delegated execution integration (new crate). No task issue; no `docs/tasks/` file for this node |
| Observed `origin/main` | `adcddc510a66ff70725084c0846830c29ef9ebbe` (`git fetch origin main` run at session end; earlier orientation showed the same ref) |
| Branch / task base | `agent/kix-rs-3b` at `adcddc5` — equal to the observed main; no delta to report |
| Implementation commit | none. The worktree is dirty on the task base |
| Depends on | `rs-3a` (merged at `45c08d5`), `k-stage2-v5-impl` (`kix-kernel-v5` crate) |
| Authorization | node definition; `docs/contracts/RIGHTS_SCALE_PROFILE.md` §5/§10/§13 updated with the draft mapping rules this node recorded (contract_change=YES per the node; the profile stays draft until Astra's ARCHITECTURE gate and the user merge) |

## What landed

- **`RangeTable`** — the off-chain mirror of the chain's sealed range table: non-empty, sorted,
  pairwise non-overlapping half-open `[start, end)` pages tagged `Seat` or `Ga`, distinct page
  indices, seat pages bounded by `kix_kernel_v5::MAX_SEATS`. Input order does not matter; gaps
  are permitted and mean "no owning page".
- **`DelegatedShow`** — one `Kernel` per page, built at construction. Seat page `[start, end)` →
  `Inventory::seats(&[end - start])`, show slot `i` → kernel seat `i - start`. GA page →
  `Inventory::general_admission(end - start)`. All pages start under the issuer authority at
  delegation epoch 1 with caller-supplied `business_epoch` and `Limits`; per-page scopes come
  from a caller-supplied function and must be distinct.
- **Routing with no partial multi-page effects.** `DelegatedReserve` carries a show-level
  `ShowSelection`. A seat bundle must lie inside one page (`CrossPageBundle`) and at most
  `MAX_BUNDLE` (`BundleTooLarge`); a GA request goes to the lowest-`start` GA page that can
  serve it whole, else `GaSpanningPages`. All three fail before any kernel call.
- **Command identity.** Show-level `CommandId { scope, principal, request }` is translated to
  the owning page's scope; identical bytes reach the same kernel where first-result replay and
  `CommandConflict` apply. `routed_commands` adds the cross-page half: the same
  `(principal, request)` routed to a different page is `MappingError::CommandConflict`. Kernel
  errors store no record and pin no route; recorded rejections do.
- **GA slot correspondence.** Per-page `BTreeSet<u32>` free sets; a successful `Held` allocates
  the `count` lowest free show slots and records `order_id -> SlotHold`; a successful `expire`
  returns the set. Tests assert `free + held == end - start` across sequences (the off-chain
  mirror of RS-C02).
- **Grant mirror and the cut.** `GrantState { delegate, generation, open }` mirrors
  `GrantControl`. `delegate_page` moves the page fence owner to the delegate at a bumped
  per-page epoch; `revoke_grant` closes the grant and re-fences every delegated page under the
  grant id itself (a tombstone no caller commands under); `undelegate_page` restores the issuer
  at a strictly greater epoch. Post-cut, new `reserve`/`mark_payment_unknown` calls get
  `GrantClosed` before any kernel call, commands under the old fence get `ExecutionFenced`,
  stored first results still replay (the kernel checks its command record before the fence),
  and `expire`/`observe_capture` continue under the tombstone fence. `delegate_page` and
  `undelegate_page` refuse pages with `Held`/`PaymentUnknown` orders — the `reserved == 0`
  mirror of RS-C07b's validated-unused-remainder rule.
- **Boundary.** `clippy.toml` is a byte-identical copy of `kix-kernel`'s (same I/O/clock/
  float/HashMap ban the v5 crate carries); normal dependencies are `kix-types` and
  `kix-kernel-v5` only. `#![forbid(unsafe_code)]`.

## Changed paths (complete)

Modified: `runtime/Cargo.toml` (workspace member), `runtime/Cargo.lock` (cargo-regenerated),
`runtime/README.md` (crate list lines for v5 and this crate),
`docs/contracts/RIGHTS_SCALE_PROFILE.md` (§5 two bullets, §10 item 7, §13 two rows — prose
only, no new `RS-C*`/`IM-*` ids), `docs/status/CURRENT_CAPABILITY_REGISTER.md` (RS-3b row).

Added: `runtime/crates/kix-delegated-exec/{Cargo.toml,clippy.toml,README.md,src/lib.rs}`,
`runtime/crates/kix-delegated-exec/tests/{common/mod.rs,range_table.rs,routing.rs,ga_slots.rs,delegation_fence.rs,boundary.rs}`,
this directory.

Not touched: `runtime/crates/kix-kernel/**`, `runtime/crates/kix-kernel-v5/**`,
`runtime/ARCHITECTURE.toml`, `reference/**`, `.aiops/`, `docs/tasks/`, all CI workflow files,
`docs/decisions/`, `docs/blueprints/`.

## Locked blobs

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

## Existing coverage first (AGENTS.md §7)

| Requirement | Existing coverage | Class |
|---|---|---|
| Page ↔ kernel `Inventory` correspondence, shows > 4,096 seats | none — RS-3a explicitly left page↔kernel mapping to this node | not covered |
| GA counter ↔ slot-range correspondence and deterministic empty-slot choice | none | not covered |
| Bundle bounds at the page map (64-seat kernel limit, cross-page bundles) | partially — v5 kernel tests cover `MAX_BUNDLE`/`InvalidRequest` inside one kernel; the page-boundary and pre-kernel failure modes are new | partially covered |
| Stable delegated command identity across pages (RS-C03b executor part) | partially — v5 covers single-kernel replay/conflict; cross-page identity collision is new | partially covered |
| Revocation cut semantics at the executor (RS-C07b, A-4/LC-CUT) | partially — RS-3a covers the on-chain cut in Move/model/localnet; the kernel-fence mirror is new | partially covered |
| Delegated execution stays disabled at runtime | covered — `scripts/verify_runtime_architecture.py` pins the flags; unchanged | sufficiently covered |

## New tests and evidence, and the gap each addresses

| Artifact | Tests | Gap addressed |
|---|---|---|
| `tests/range_table.rs` | 7 | table validation: empty/inverted/overlapping pages, duplicate indices, seat page `MAX_SEATS` bound, GA pages unbounded by it, half-open lookup, gaps |
| `tests/routing.rs` | 9 | a 7,000-seat show across two pages with kernel-local offset translation; `MAX_BUNDLE` 64 ok / 65 refused; cross-page bundle refused with zero state change; unknown/GA-owned slots; lowest-start GA page choice; wrong show scope; stored kernel rejections replay; kernel errors pin no route; capture observations route to the bound operation's page and unbound operations to `UnknownOperation`; a confirmed order does not block delegation |
| `tests/ga_slots.rs` | 4 | deterministic lowest-free-slot assignment, `order_id -> slots` bookkeeping, `expire` freeing and reassignment, spanning-request refusal, `free + held == range` conservation across mixed sequences |
| `tests/delegation_fence.rs` | 8 | first-result replay and both conflict halves; fence handoff to the delegate; grant/delegation preconditions; the cut — `GrantClosed` for new commitments, stored-result replay under any stale fence, continued releases under the tombstone; per-grant cuts; reclaim of the validated-unused remainder; grant/delegate/issuer identity collisions |
| `tests/boundary.rs` | 2 | dependency boundary (`kix-types` + `kix-kernel-v5` only, no v4, no dev/build deps) and the byte-identical clippy boundary |

30 tests total.

## Commands actually run and results

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main`; `git rev-parse HEAD` | `adcddc510a66ff70725084c0846830c29ef9ebbe`; same |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `69564b16…`, `b607996c…` — both match, before and after |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-delegated-exec` | 30/30 pass (also regenerated `runtime/Cargo.lock` for the new member) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-delegated-exec --all-targets --locked -- -D warnings` | clean |
| `cargo fmt --manifest-path runtime/Cargo.toml -p kix-delegated-exec -- --check` | reformatted once, then clean |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7/7 tests OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 78/78 pass, unchanged code |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 213/213 pass across all crates |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `python3 scripts/check_status_register.py` and `--self-test` | pass / pass (after the validation README existed) |
| `python3 scripts/check_rs_profile_traceability.py` and `--self-test` | pass / pass |
| `python3 scripts/check_docs_index.py` and `--self-test` | pass / pass |

Environment: pinned `rustc`/`cargo` 1.98.1 (`rust-toolchain.toml`), Python 3.13.5. These are
the closest local equivalents of `ktx-kernel.yml` and the `protocol.yml` Rust/doc jobs at this
worktree — **not** exact-head CI: nothing was committed or pushed, so no workflow ran on this
tree. CI IDs: none available.

Not run (this node touches none of those surfaces): Move tests, localnet journeys, SDK, storage
and commerce probes, canonical/bootstrap checks — the `protocol.yml` heavy paths. Recorded
honestly as not run locally, not inferred.

## Contract/implementation discrepancy classification (AGENTS.md §8)

**A. Contract-defined and matching:** page as the minimum delegation unit and per-page original
authority (§10.1–2, §5); one-write grant currentness check (`g.open`) before delegated
consumption (§10.3–4); pre-cut obligation preservation and validated-unused-remainder reclaim
(§10.5, A-4/LC-CUT, RS-C07b); no partial multi-page effects (§5 adjacency bullet, RS-C04);
kernel `MAX_SEATS`/`MAX_BUNDLE` unchanged (IM-26); locked files and `reference/` untouched
(§12).

**B. Contract undefined — recorded as draft rules or characterizations, none invented into a
binding value:**
1. Page→kernel correspondence (seat page ↔ one `Inventory::seats` segment; GA page ↔
   `Inventory::general_admission`) — assigned to this node in the contract, recorded as draft.
2. GA deterministic lowest-free-slot allocation inside a page and lowest-`start` page choice —
   assigned to this node, recorded as draft.
3. Command-identity translation `(show scope, principal, request) → (page scope, principal,
   request)` and the cross-page conflict rule — draft.
4. Tombstone fence owner = grant id between the cut and reclaim — an executor-side
   characterization; the grant/delegate/issuer distinctness requirement follows from it.
5. `mark_payment_unknown` refused post-cut (a new external send is a new commitment);
   `expire`/`observe_capture` continue (release and fact recording are not).
6. Grant `generation` in the mirror starts at 1 and bumps once at the cut, matching the
   `GrantControl` fields RS-3a shipped; delegation epochs are per-page counters, not the
   grant's generation.
7. `cancel_scope`, `terminate`, holds and reclamation reports exist in v5 but are not mapped
   here — the map exposes only what delegated reservation flow needs.
8. Page size P, grant TTL/expiry, allowed-operation sets, K, W stay UNDETERMINED (§4, §10.8);
   the range table is caller-supplied.

**C. Explicit contract violations:** none found.

## Explicit non-claims — what was not tested

- No testnet/mainnet/localnet, real funds, PG/bank/KYC, public endpoints, R2, replication/
  consensus/storage engine, coin/TIX module. In-memory only.
- Delegated execution is not enabled; nothing here is a runtime service, wire name, OpenAPI or
  catalogue entry.
- No durability, distributed fencing, executor handoff, journal or crash-restart story; the
  in-memory map is rebuilt from its inputs.
- No performance, throughput or contention claims.
- The grant mirror is not a chain read; principal/delegate/issuer identities are not
  authenticated.
- Cross-`DelegatedShow` behavior, `cancel_scope`/`terminate`/hold/reclaim-report mapping, and
  Move-side integration are not covered.

## Follow-up candidates

- Astra ARCHITECTURE audit of the draft mapping rules, then user merge.
- `ai-delegation-execution-decision`: whether and when `delegated_execution_enabled` ever flips.
- Page size P, grant TTL, allowed-operation sets (contract §4, §10.8) — DECISION_REQUIRED ·
  Astra if a product value is ever needed.
- Whether the executor needs a read-only command-record lookup in v5 for post-cut reconcile
  views beyond `order()`.

## Fix round 1 (independent review)

Two blocking findings and one latent defect they exposed were fixed in
`runtime/crates/kix-delegated-exec/src/lib.rs`; everything above remains the round-0 record.

1. **Stored GA commands lost first-result replay.** `reserve` recomputed the GA page choice
   from current `kernel.remaining()` before comparing against `routed_commands`, so an
   identical retry could re-route after a capacity shift and get `CommandConflict` instead of
   reaching the pinned page's kernel, which would return `replayed: true`. This also broke the
   post-cut replay path, since the `GrantClosed` gate is keyed to the stored route. Fix: a
   stored command is pinned to its recorded page and `pinned_selection` translates the
   selection there; a payload that cannot be expressed on the pinned page is the map's
   cross-page `CommandConflict`, and an expressible difference is the kernel's own.
2. **Cross-page `ProviderOperation` double-binding.** `operation_pages.insert` on `Held`
   silently overwrote, so a different command carrying an already-bound payment could hold a
   second order on another page, and `observe_capture` would then route only to the last-bound
   page, stranding the first order's reconciliation. Fix: a reserve-time check (after the
   `GrantClosed` gate, mirroring the kernel's record→fence→rejection order) answers the
   kernel's own `Rejected(OperationAlreadyBound)` when the operation is bound on another
   page. The rejection is synthesized — no kernel stores a record, no route is pinned — and
   stable because a kernel never unbinds an operation.
3. **Latent, exposed by fix 1:** the `Held` bookkeeping popped GA free slots even when
   `applied.replayed`, so once replays actually reached the kernel they would have consumed
   the free set a second time and broken `free + held == end - start`. Bookkeeping is now
   gated on `!applied.replayed`. `tests/ga_slots.rs` asserts the pinned-page replay leaves
   the free set, slot hold, and conservation untouched.

Also fixed the minor review note: `MappingError::CommandConflict`'s doc no longer mentions
the wrong-scope case (that is the separate `WrongScope` variant).

### New tests (fix round 1)

| Test | File | Covers |
|---|---|---|
| `a_replayed_ga_hold_consumes_no_free_slots` | `ga_slots.rs` | finding 1 + latent defect: replayed Held frees/consumes nothing |
| `a_stored_ga_command_replays_on_its_pinned_page_after_capacity_shifts` | `ga_slots.rs` | finding 1: pinned replay, kernel and map conflict halves |
| `the_cut_still_replays_a_stored_ga_result_on_its_pinned_page` | `delegation_fence.rs` | finding 1 post-cut: gate keyed to the pin, `GrantClosed` only for fresh commands |
| `a_payment_operation_binds_at_most_one_order_across_pages` | `routing.rs` | finding 2: cross-page rejection value, stability, kernel-stored same-page case, observation routing |

34 crate tests total (was 30).

### Commands actually run (fix round 1)

| Command | Result |
|---|---|
| `cargo test -p kix-delegated-exec` | 34/34 pass |
| `cargo clippy -p kix-delegated-exec --all-targets --locked -- -D warnings` | clean |
| `cargo fmt -p kix-delegated-exec -- --check` | reformatted once, then clean |
| `cargo test --workspace --locked` | 217/217 pass across all crates |
| `cargo clippy --workspace --all-targets --locked -- -D warnings` | clean |
| `cargo fmt --all -- --check` | clean |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7/7 tests OK |
| `python3 scripts/check_status_register.py` | pass |
| `python3 scripts/check_rs_profile_traceability.py` | pass |
| `python3 scripts/check_docs_index.py` | pass |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `69564b16…`, `b607996c…` — both match, before and after |

No commit, push, PR, comment, `.aiops/`, `docs/tasks/` or CI edit; the supervisor owns git.
Exact-head CI: none available — nothing committed.
