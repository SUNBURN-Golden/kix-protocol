# R1 observation-slot fix — 2026-09-15

Baseline PR #10 head: `bf460b1f7724c5ad7d561b19a64959383fcec6a8`.
Scope: R1 business logic only. This supplies no justification for KTX adoption or R2 continuation.

## Exact baseline execution

The baseline workspace sources/manifests/lockfile were compared to the Git blob identities of the SHA above. A Rust stdin harness executed the unchanged compiled kernel:

```text
head=bf460b1f7724c5ad7d561b19a64959383fcec6a8
old_quarantine_repro/conflict=Ok(Conflict)
old_quarantine_repro/review_a=true,review_b=true
old_quarantine_repro/send_b=Err(InvalidTransition)
old_time_repro/expire_500=Ok(false)
old_time_repro/new_reserve_300=Err(ClockRegression)
old_time_repro/after_duplicate_at_500/new_reserve_300=Err(ClockRegression)
A/full_budget_new_conflict=Err(Capacity)
A/unchanged=true,review_a=false,review_b=false,observations=1,conflicts=0
A/send_b_with_full_budget=Ok(())
B/fresh_unbound_capture=Err(UnknownOperation)
B/unchanged=true,orders=0,observations=0,conflicts=0
exit_code=0
```

The earlier cross-operation quarantine and no-op/duplicate time defects are already fixed at this baseline. A new conflict at full evidence capacity is not stored or quarantined. A fresh unbound success is not stored anywhere in the kernel. The README's external inbox is a requirement, not implemented storage.

## Change

One slot is reserved by complete provider/account/operation identity before the first successful `mark_payment_unknown`. Retries reuse the slot. Stored events + conflicts + reservations stay within the observation limit. Other events and new conflicts cannot spend it. The first bound new-event capture atomically converts its reservation to retained evidence; amount mismatch, cancellation, UNKNOWN expiry, owner changes and prior quarantine do not drop the promised slot.

```text
semantics_version=2
mark_A=Ok(()); reserved=1
retry_mark_A=Ok(()); reserved=1
mark_B=Err(Capacity)
unrelated_capture_B=Err(Capacity); reserved=1
first_capture_A=Ok(PaymentConfirmed); reserved=0; stored=1
exit_code=0
```

## Verification

Rust 1.98.1, workspace `cargo test --workspace --locked --offline`: 93 tests passed, including 32 existing kernel transitions and 11 new observation-slot tests. fmt and workspace all-target clippy with warnings denied passed. The previously authorized HashMap/HashSet/RandomState, clock/environment/I/O method restrictions and float-arithmetic deny are included in the kernel.

Tests explicitly retain A/B as remaining limitations and do not disguise them as fixed behavior. No state-model oracle, real provider adapter or fault-tolerant storage has been implemented in this patch.

## Compatibility and limits

The admission result changes, so SEMANTICS_VERSION is now 2; version-1 Context inputs are explicitly rejected. A previous test's hard-coded unknown version 2 is now expressed as SEMANTICS_VERSION + 1. Version-1 replay/migration and the separate R2-A branch are not automatically upgraded.

Only first bound capture capacity is protected. New conflicts at exhausted capacity still return Capacity without quarantine. Fresh unbound captures still return UnknownOperation without storage (Capacity can precede it when full). An upstream delivery must not be acknowledged as durably retained from these results. Retention/GC and unlimited operation are not implemented. No main merge, deployment or external DB change.

