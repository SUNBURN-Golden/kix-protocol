# kix-delegated-exec

In-memory delegated-execution mapping layer. This crate maps the extended rights-scale profile's page model (`docs/contracts/RIGHTS_SCALE_PROFILE.md` §3, §5, §10) onto `kix-kernel-v5` `Kernel` instances: one `InventoryPage` or GA slot-range shard is one kernel `Inventory`, so a show larger than `MAX_SEATS = 4,096` runs as a set of pages operated concurrently under one map. It is not a service, not a chain client, not a storage engine, and not a production runtime.

Authority: the extended profile assigns the page↔kernel and GA counter↔slot-range correspondences to node rs-3b under the Astra architecture audit (contract §5, §10 items 7–8; blueprint `docs/blueprints/rights-scale-v1/README.md` §6 rules 7–8). The rules recorded here are draft rules, not contract amendments. Delegated execution stays disabled at runtime: `runtime/ARCHITECTURE.toml` keeps `delegated_execution_enabled = false` and nothing here is a wire, OpenAPI, or command-catalogue name.

## Implemented

- **Range table.** `RangeTable` mirrors the chain's sealed table: non-empty, ordered, pairwise non-overlapping half-open show-slot ranges, each tagged `Seat` or `Ga`. A show above 4,096 seats is valid because each seat page is at most `MAX_SEATS`; a GA page has no bitmap bound.
- **Page → kernel.** `DelegatedShow` builds one `Kernel` per page. A seat page `[start, end)` becomes `Inventory::seats(&[end - start])` and show slot `i` becomes kernel seat `i - start`; a GA page becomes `Inventory::general_admission(end - start)`. Seat requests are refused before any kernel call when they would cross a page boundary (`CrossPageBundle`) or exceed `MAX_BUNDLE` (`BundleTooLarge`); a GA request no single GA page can serve is `GaSpanningPages`. No partial multi-page effects exist.
- **GA slot correspondence.** The kernel keeps the quantity counter; the map keeps the per-page free-slot set and picks the `count` lowest free show slots on a successful `Held`, recording `order_id -> (page, slot set)`. A successful `expire` returns the set. `free + held == end - start` is asserted in tests as the off-chain mirror of RS-C02.
- **Command identity.** A show-level `CommandId { scope: show, principal, request }` is translated to `(page scope, principal, request)` on the owning page. The immutable table makes identical bytes reach the same kernel, where first-result replay and `CommandConflict` apply. A command the kernel already stored is pinned to its page — the GA page choice is not recomputed from current capacity — so an identical retry replays on the kernel holding the record even after capacity shifts or a grant cut. The map adds the cross-page half of the conflict rule: a stored identity whose new payload cannot be expressed on the pinned page is `MappingError::CommandConflict`.
- **Operation identity.** `operation_pages` binds each `ProviderOperation` to the single page that held it, mirroring the kernel's one-operation→one-order rule across pages. A fresh reserve routed to a different page than the bound one is answered with the kernel's own `Rejected(OperationAlreadyBound)` — synthesized by the map, stored nowhere — and `observe_capture` routes to the bound page only, so no order's reconciliation is stranded.
- **Grant mirror and the cut.** `GrantState` is an in-memory `GrantControl` mirror (`delegate`, `generation`, `open`). `delegate_page` moves the page kernel's fence owner to the delegate at a bumped per-page delegation epoch; `revoke_grant` closes the grant and re-fences every delegated page under the grant id itself (a held tombstone); `undelegate_page` restores the issuer at a strictly greater epoch. After the cut, new `reserve`/`mark_payment_unknown` calls are refused with `GrantClosed` and commands under the old fence get `ExecutionFenced`, while stored first results still replay — the kernel checks the command record before the fence — and `expire`/`observe_capture` continue under the tombstone fence. `delegate_page` and `undelegate_page` both refuse a page carrying `Held`/`PaymentUnknown` orders (the `reserved == 0` mirror of RS-C07b's validated-unused-remainder rule).

## Stopped

No entry point exists for these, and this node does not authorize them.

- **Runtime enablement.** `delegated_execution_enabled` stays `false`. Enabling delegated execution belongs to the user decision named in the program roadmap, not to a crate.
- **Grant expiry/TTL, allowed-operation sets, page size P, shard count, K, W.** Undefined in the contract (§4, §10.8); not invented here. The range table is caller-supplied.
- **Chain reads.** `GrantState` is a caller-maintained mirror. Nothing in this crate authenticates principals, delegates, issuers or grants.
- **`cancel_scope` surface.** Business-scope cancellation is not mapped; the map exposes no equivalent.
- **Durability.** No journal, checkpoint or replay of the map itself.

## Characterizations

- The tombstone fence owner post-cut is the grant id, an identity the driver does not issue commands under; `expire` and `observe_capture` remain possible under it because releases and fact recording are not new commitments.
- `mark_payment_unknown` is refused after the cut because authorizing a first external send is a new commitment, matching the chain's `EGrantClosed` on `issue_paid_delegated`.
- An observation whose operation was never bound on this show routes to `UnknownOperation` unless its event key was previously recorded, which routes it to that key's kernel for the retained-conflict path.
- A kernel error stores no command record, so it pins no route in the cross-page index; a recorded rejection does. The map's synthesized `Rejected(OperationAlreadyBound)` likewise stores no record and pins no route; it is stable because a kernel never unbinds an operation, so identical retries answer the same value (`replayed: false`, as no kernel record exists).
- A replayed `Held` consumes no map bookkeeping: the kernel changed nothing, so the GA free set, slot holds and the order/operation indices are untouched.
- `delegate_page`/`revoke_grant`/`undelegate_page` take caller-supplied `now_ms`; a non-monotonic supply can leave a mid-`revoke` page already re-fenced, which is the safe direction (the dead fence never becomes valid again).
- A GA page's free set is per-slot memory: `DelegatedShow` materializes `end - start` entries per GA page while the kernel keeps only the counter. The contract does not bound GA page size and this node does not choose one.

## Non-claims

This crate does not establish durability, distributed fencing, bank exactly-once behavior, chain finality, legal compliance, or production readiness. The mapping rules are draft rules for the Astra architecture audit, not amendments to `docs/contracts/RIGHTS_SCALE_PROFILE.md` and not an authorization of delegated execution. No wire, OpenAPI, or command-catalogue name is added here.
