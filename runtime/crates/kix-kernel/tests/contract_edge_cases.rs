//! Contract-driven edge cases not already covered by the existing v4 suite.
//!
//! Uses only the public `kix-kernel` API and observable state. It imports
//! neither `model_v4` nor any generator: each case is a deterministic example
//! of a documented predicate, checked against a whole-kernel `Eq` clone where
//! the contract says a call must leave state unchanged.
//!
//! Derivations: `docs/adr/0001-ktx-authority-commit-recovery.md` §3/§5/§6,
//! `docs/contracts/STATE_LIFECYCLE.md` §2/§3/§5,
//! `runtime/crates/kix-kernel/README.md` "Implemented meaning" and
//! "Observation reservation and remaining gaps".
//!
//! The availability examples at the end answer `docs/contracts/CONTRACT_INVARIANTS.md`
//! §5 ("incorrect but safe rejections"; "No finite test proves all inputs"). Each
//! builds a state in which ADR §3/§4/§6/§8, STATE_LIFECYCLE §2/§5.7 and the README
//! require a reservation to be held, and asserts that it is. They are finite,
//! source-informed examples (the author knew the locked kernel source), not an
//! availability proof. Values the contracts leave open (the bundle maximum,
//! inclusive record limits, exact rejection/error variants, cross-kind
//! selections) are labelled AGENTS §8 class B characterizations.
//!
//! The error-precedence pairs after them answer the §5 "wrong error precedence"
//! question (S5-PRECEDENCE). Each arms two public rejection guards on one call,
//! but only where ADR §3/§5/§6 or STATE_LIFECYCLE §2–§4 decide which one wins,
//! asserts that outcome with a whole-kernel `Eq` check and shows the losing
//! guard is live on a clone, a twin or a later valid call. Pairs no contract
//! orders are class B characterizations in the S5-PRECEDENCE validation
//! record and are deliberately not asserted here.

use kix_kernel::{
    CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, KernelError, Limits,
    MAX_BUNDLE, ObservationOutcome, OrderState, ProviderOperation, Rejection, Reserve,
    ReserveOutcome, SEMANTICS_VERSION, Selection,
};
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

const EXPIRY: u64 = 100;

fn id(n: u8) -> KixId {
    KixId::from_bytes([n; 16])
}

fn fence() -> ExecutionFence {
    ExecutionFence {
        owner: id(1),
        generation: 1,
    }
}

fn ctx(now_ms: u64) -> Context {
    Context {
        fence: fence(),
        now_ms,
        semantics_version: SEMANTICS_VERSION,
    }
}

fn amount(atoms: u128) -> AssetAmount {
    AssetAmount::checked(
        AssetId::from_bytes([7; 32]),
        atoms,
        u128::MAX,
        RegistryVersion::new(1).unwrap(),
        Hash32::from_bytes([8; 32]),
    )
    .unwrap()
}

fn kernel() -> Kernel {
    Kernel::new(
        id(9),
        fence(),
        1,
        Inventory::seats(&[10]).unwrap(),
        Limits {
            commands: 32,
            orders: 32,
            observations: 32,
        },
    )
    .unwrap()
}

fn request(n: u8, first: u16) -> Reserve {
    Reserve {
        id: CommandId {
            scope: id(9),
            principal: id(2),
            request: id(n),
        },
        order_id: id(n),
        expected_business_epoch: 1,
        selection: Selection::Seats { first, count: 1 },
        amount: amount(10_000),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: EXPIRY,
        payment: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: id(n),
        },
    }
}

fn capture(request: &Reserve, event: u8) -> CaptureObservation {
    CaptureObservation {
        event_id: id(event),
        operation: request.payment,
        amount: request.amount,
        evidence_hash: Hash32::from_bytes([event; 32]),
    }
}

/// ADR §3/§5: the first result of a completed command is immutable and its
/// replay is read-only, including for a rejection whose cause has disappeared.
#[test]
fn rejection_replay_stays_immutable_after_the_blocking_hold_is_released() {
    let mut k = kernel();
    let holder = request(3, 0);
    let loser = request(4, 0);
    k.reserve(ctx(1), holder.clone()).unwrap();
    let rejected = k.reserve(ctx(2), loser.clone()).unwrap();
    assert_eq!(
        rejected.original,
        ReserveOutcome::Rejected(Rejection::Unavailable)
    );
    assert!(!rejected.replayed);

    assert!(k.expire(ctx(EXPIRY), holder.order_id).unwrap());
    assert_eq!(k.remaining(), 10);

    let before = k.clone();
    let replay = k.reserve(ctx(EXPIRY + 1), loser.clone()).unwrap();
    assert!(replay.replayed);
    assert_eq!(replay.original, rejected.original);
    assert_eq!(k, before);
    assert!(k.order(loser.order_id).is_none());

    // Only a new command identity can take the released seat.
    let mut retry = request(5, 0);
    retry.expires_at_ms = 500;
    retry.payment = loser.payment;
    assert_eq!(
        k.reserve(ctx(EXPIRY + 2), retry).unwrap().original,
        ReserveOutcome::Held(id(5))
    );
}

/// ADR §3: command identity is `(scope, principal, request)`, so an altered
/// payload is a conflict rather than a new command. The documented reservation
/// lookup runs before the time/fence guards, so the conflict is reported even
/// under a stale fence or a regressed clock, and nothing is applied.
#[test]
fn altered_payload_conflicts_before_fence_and_clock_guards() {
    let original = request(3, 0);
    let stale_fence = Context {
        fence: ExecutionFence {
            owner: id(8),
            generation: 2,
        },
        ..ctx(50)
    };
    let regressed = ctx(0);

    for altered in [
        Reserve {
            order_id: id(4),
            ..original.clone()
        },
        Reserve {
            payment: ProviderOperation {
                operation: id(40),
                ..original.payment
            },
            ..original.clone()
        },
        Reserve {
            expires_at_ms: EXPIRY + 1,
            ..original.clone()
        },
        Reserve {
            selection: Selection::Seats { first: 1, count: 1 },
            ..original.clone()
        },
    ] {
        let mut k = kernel();
        k.reserve(ctx(10), original.clone()).unwrap();
        let before = k.clone();
        for context in [ctx(11), stale_fence, regressed] {
            assert_eq!(
                k.reserve(context, altered.clone()),
                Err(KernelError::CommandConflict)
            );
            assert_eq!(k, before);
        }
        // The unchanged payload still replays its original result.
        assert!(k.reserve(ctx(11), original.clone()).unwrap().replayed);
        assert_eq!(k, before);
    }
}

/// The reservation lookup checks scope and semantics but neither time nor
/// fence, so those two guards still outrank an existing command's replay.
#[test]
fn replay_lookup_is_guarded_by_scope_and_semantics_only() {
    let mut k = kernel();
    let original = request(3, 0);
    let first = k.reserve(ctx(10), original.clone()).unwrap();
    let before = k.clone();

    let foreign_scope = Reserve {
        id: CommandId {
            scope: id(77),
            ..original.id
        },
        ..original.clone()
    };
    assert_eq!(
        k.reserve(ctx(11), foreign_scope),
        Err(KernelError::WrongScope)
    );
    assert_eq!(
        k.reserve(
            Context {
                semantics_version: SEMANTICS_VERSION - 1,
                ..ctx(11)
            },
            original.clone()
        ),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(k, before);

    for context in [
        ctx(0),
        Context {
            fence: ExecutionFence {
                owner: id(8),
                generation: 9,
            },
            ..ctx(11)
        },
    ] {
        let replay = k.reserve(context, original.clone()).unwrap();
        assert!(replay.replayed);
        assert_eq!(replay.original, first.original);
        assert_eq!(k, before);
    }
}

/// STATE_LIFECYCLE §2: the expiry instant itself is the boundary for every
/// entry point. `now_ms == expires_at_ms` is already expired for a new
/// reservation and for a send authorization, releases a held reservation, and
/// classifies a matching capture as a return obligation.
#[test]
fn expiry_instant_is_treated_consistently_by_every_entry_point() {
    let held = request(3, 0);

    let mut k = kernel();
    k.reserve(ctx(1), held.clone()).unwrap();
    assert!(k.expire(ctx(EXPIRY), held.order_id).unwrap());
    assert_eq!(k.order(held.order_id).unwrap().state, OrderState::Expired);
    assert_eq!(k.remaining(), 10);

    let mut k = kernel();
    let late = Reserve {
        expires_at_ms: EXPIRY,
        ..request(4, 1)
    };
    assert_eq!(
        k.reserve(ctx(EXPIRY), late).unwrap().original,
        ReserveOutcome::Rejected(Rejection::InvalidRequest)
    );
    assert_eq!(k.order_count(), 0);

    let mut k = kernel();
    k.reserve(ctx(1), held.clone()).unwrap();
    let before = k.clone();
    assert_eq!(
        k.mark_payment_unknown(ctx(EXPIRY), held.order_id),
        Err(KernelError::InvalidTransition)
    );
    assert_eq!(k, before);

    let mut k = kernel();
    k.reserve(ctx(1), held.clone()).unwrap();
    assert_eq!(
        k.observe_capture(ctx(EXPIRY), capture(&held, 1)).unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(
        k.order(held.order_id).unwrap().state,
        OrderState::ReturnRequired
    );
}

/// README "Observation reservation": expiry never releases a reserved slot,
/// but it does end new send authorization. A retry at or after the deadline is
/// refused without releasing the reservation, the seat or the promised slot.
#[test]
fn unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot() {
    let mut k = kernel();
    let order = request(3, 0);
    k.reserve(ctx(1), order.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), order.order_id).unwrap();
    assert_eq!(k.reserved_observation_count(), 1);

    let before = k.clone();
    for now in [EXPIRY, EXPIRY + 50] {
        assert_eq!(
            k.mark_payment_unknown(ctx(now), order.order_id),
            Err(KernelError::InvalidTransition)
        );
        assert_eq!(k, before);
    }
    assert_eq!(
        k.order(order.order_id).unwrap().state,
        OrderState::PaymentUnknown
    );
    assert!(k.order(order.order_id).unwrap().inventory_owned);
    assert_eq!(k.remaining(), 9);

    assert_eq!(
        k.observe_capture(ctx(EXPIRY + 51), capture(&order, 1))
            .unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(k.reserved_observation_count(), 0);
    assert_eq!(k.remaining(), 10);
}

/// STATE_LIFECYCLE §3/§5 with ADR §6: a retained return obligation is not
/// re-applied by further evidence. A second matching event is a duplicate
/// economic effect and must not release inventory twice, and a later
/// mismatching event marks review without erasing the captured fact.
#[test]
fn return_required_is_stable_under_further_late_evidence() {
    let mut k = kernel();
    let order = request(3, 0);
    k.reserve(ctx(1), order.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), order.order_id).unwrap();
    assert_eq!(
        k.observe_capture(ctx(EXPIRY), capture(&order, 1)).unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(k.remaining(), 10);

    assert_eq!(
        k.observe_capture(ctx(EXPIRY + 1), capture(&order, 2))
            .unwrap(),
        ObservationOutcome::DuplicateEffect
    );
    let after_duplicate = k.order(order.order_id).unwrap().clone();
    assert_eq!(after_duplicate.state, OrderState::ReturnRequired);
    assert_eq!(after_duplicate.captured, Some(order.amount));
    assert!(!after_duplicate.inventory_owned);
    assert_eq!(k.remaining(), 10);

    let mut mismatched = capture(&order, 3);
    mismatched.amount = amount(1);
    assert_eq!(
        k.observe_capture(ctx(EXPIRY + 2), mismatched).unwrap(),
        ObservationOutcome::Review
    );
    let reviewed = k.order(order.order_id).unwrap();
    assert_eq!(reviewed.state, OrderState::ReturnRequired);
    assert_eq!(reviewed.captured, Some(order.amount));
    assert!(reviewed.review_required);
    assert_eq!(k.remaining(), 10);

    let before = k.clone();
    assert_eq!(
        k.mark_payment_unknown(ctx(EXPIRY + 3), order.order_id),
        Err(KernelError::InvalidTransition)
    );
    assert_eq!(k, before);
}

/// README: quarantine is sticky. Owner replacement, an expiry release and
/// scope cancellation are ordered transitions, not review resolution.
#[test]
fn bound_quarantine_survives_owner_change_expiry_and_cancellation() {
    let mut k = kernel();
    let first = request(3, 0);
    let second = request(4, 1);
    k.reserve(ctx(1), first.clone()).unwrap();
    k.reserve(ctx(2), second.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&first, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(4), capture(&second, 1)).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(k.quarantined_operation_count(), 2);

    let next = ExecutionFence {
        owner: id(8),
        generation: 2,
    };
    k.replace_owner(ctx(5), next).unwrap();
    let next_ctx = |now_ms| Context {
        fence: next,
        ..ctx(now_ms)
    };
    assert!(k.expire(next_ctx(EXPIRY), second.order_id).unwrap());
    k.cancel_scope(next_ctx(EXPIRY + 1), 2).unwrap();

    assert_eq!(k.quarantined_operation_count(), 2);
    assert!(k.order(first.order_id).unwrap().review_required);
    assert!(k.order(second.order_id).unwrap().review_required);
    assert_eq!(k.conflicts().len(), 1);
    assert_eq!(
        k.mark_payment_unknown(next_ctx(EXPIRY + 2), second.order_id),
        Err(KernelError::InvalidTransition)
    );
}

/// README: retained conflict evidence bans the provider/account/operation
/// identity, not one order row, so a different order cannot reuse it.
#[test]
fn retained_unbound_conflict_bans_the_identity_for_any_future_order() {
    let mut k = kernel();
    let bound = request(3, 0);
    let unbound = request(4, 1);
    k.reserve(ctx(1), bound.clone()).unwrap();
    k.observe_capture(ctx(2), capture(&bound, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(3), capture(&unbound, 1)).unwrap(),
        ObservationOutcome::Conflict
    );

    let reused = Reserve {
        payment: unbound.payment,
        ..request(5, 2)
    };
    assert_eq!(
        k.reserve(ctx(4), reused).unwrap().original,
        ReserveOutcome::Rejected(Rejection::OperationQuarantined)
    );
    assert_eq!(k.order(id(5)), None);
    assert_eq!(k.order_count(), 1);
    assert_eq!(k.quarantined_operation_count(), 1);
    assert_eq!(k.conflicts().len(), 1);

    // A different operation under the same provider/account is unaffected.
    let neighbour = Reserve {
        payment: ProviderOperation {
            operation: id(60),
            ..unbound.payment
        },
        ..request(6, 2)
    };
    assert_eq!(
        k.reserve(ctx(5), neighbour).unwrap().original,
        ReserveOutcome::Held(id(6))
    );
}

// ---------------------------------------------------------------------------
// CONTRACT_INVARIANTS §5 availability examples (S5-SAFE-REJECT / S5-FINITE).
// ---------------------------------------------------------------------------

/// Mirrors the CONTRACT_INVARIANTS §4 seat fixture: actual segments [65, 5].
const SEGMENTS: [u16; 2] = [65, 5];
/// Mirrors the CONTRACT_INVARIANTS §4 GA fixture capacity.
const GA_CAPACITY: u32 = 6;
const ROOMY: Limits = Limits {
    commands: 32,
    orders: 32,
    observations: 32,
};

fn kernel_with(inventory: Inventory, limits: Limits) -> Kernel {
    Kernel::new(id(9), fence(), 1, inventory, limits).unwrap()
}

fn seat_kernel() -> Kernel {
    kernel_with(Inventory::seats(&SEGMENTS).unwrap(), ROOMY)
}

fn ga_kernel() -> Kernel {
    kernel_with(Inventory::general_admission(GA_CAPACITY).unwrap(), ROOMY)
}

fn seats(n: u8, first: u16, count: u16) -> Reserve {
    Reserve {
        selection: Selection::Seats { first, count },
        ..request(n, first)
    }
}

fn ga(n: u8, count: u32) -> Reserve {
    Reserve {
        selection: Selection::GeneralAdmission { count },
        ..request(n, 0)
    }
}

fn units(selection: Selection) -> u32 {
    match selection {
        Selection::Seats { count, .. } => u32::from(count),
        Selection::GeneralAdmission { count } => count,
    }
}

/// A new command is held: original result, new order in Held owning its
/// inventory with the exact request, and remaining reduced by exactly its units.
fn assert_held(k: &mut Kernel, now_ms: u64, r: &Reserve) {
    let remaining = k.remaining();
    let reply = k.reserve(ctx(now_ms), r.clone()).unwrap();
    assert_eq!(reply.original, ReserveOutcome::Held(r.order_id), "{r:?}");
    assert!(!reply.replayed);
    let order = k.order(r.order_id).expect("held order is recorded");
    assert_eq!(order.request, *r);
    assert_eq!(order.state, OrderState::Held);
    assert!(order.inventory_owned);
    assert_eq!(k.remaining(), remaining - units(r.selection));
}

/// A new command is recorded as a business rejection without creating an
/// order or allocating any inventory (STATE_LIFECYCLE §2; ADR §4).
fn assert_rejected(k: &mut Kernel, now_ms: u64, r: &Reserve, reason: Rejection) {
    let (remaining, orders) = (k.remaining(), k.order_count());
    let reply = k.reserve(ctx(now_ms), r.clone()).unwrap();
    assert_eq!(reply.original, ReserveOutcome::Rejected(reason), "{r:?}");
    assert!(!reply.replayed);
    assert_eq!((k.remaining(), k.order_count()), (remaining, orders));
}

fn assert_error_leaves_state(k: &mut Kernel, context: Context, r: Reserve, want: KernelError) {
    let before = k.clone();
    assert_eq!(k.reserve(context, r), Err(want));
    assert_eq!(*k, before);
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. ADR §8 "All-or-none selection must
/// handle real aisles ... R1 covers contiguous segment selection" and README
/// "Implemented meaning": "All-or-none contiguous selection inside real
/// segments". A free range inside one actual segment must be held, including
/// one ending exactly at the aisle and the whole second segment. The two
/// MAX_BUNDLE cases are class B characterizations: the README names a maximum
/// bundle length but no value; the second also crosses the 64-bit word.
#[test]
fn free_contiguous_range_inside_one_actual_segment_is_held() {
    for (first, count) in [(0, 1), (20, 5), (60, 5), (64, 1), (65, 5), (69, 1)] {
        let mut k = seat_kernel();
        assert_held(&mut k, 1, &seats(30, first, count));
        assert_eq!(k.remaining(), 70 - u32::from(count));
    }
    // Class B characterization: the public MAX_BUNDLE is the observed maximum.
    for first in [0, 1] {
        let mut k = seat_kernel();
        assert_held(&mut k, 1, &seats(31, first, MAX_BUNDLE));
        assert_eq!(k.remaining(), 70 - u32::from(MAX_BUNDLE));
    }
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. README "Implemented meaning":
/// "crossing a 64-bit word when appropriate but never crossing an aisle"; ADR
/// §8 "machine-word boundaries". A free range across seats 63/64 or 127/128
/// inside one segment is held, including one that fits exactly between two
/// existing holds and one that ends exactly at the aisle.
#[test]
fn word_crossing_range_inside_one_segment_is_held_between_neighbours() {
    let mut k = seat_kernel();
    assert_held(&mut k, 1, &seats(30, 63, 2));
    assert_eq!(k.remaining(), 68);

    let mut k = kernel_with(Inventory::seats(&[200]).unwrap(), ROOMY);
    assert_held(&mut k, 1, &seats(31, 60, 3));
    assert_held(&mut k, 2, &seats(32, 66, 2));
    // Seats 63..66 are exactly the free gap and cross the word at 64.
    assert_held(&mut k, 3, &seats(33, 63, 3));
    assert_held(&mut k, 4, &seats(34, 127, 2));
    assert_eq!(k.remaining(), 200 - 10);
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. README "Implemented meaning": "GA
/// capacity cannot overdraw"; ADR §8 "R1 covers ... GA capacity". Capacity is
/// the limit, so a request for exactly the remaining units is held, in one
/// request or after earlier holds. The seat analogue takes every seat of two
/// actual segments with bundles inside each segment.
#[test]
fn seats_and_general_admission_are_held_up_to_exact_remaining_capacity() {
    let mut k = ga_kernel();
    assert_held(&mut k, 1, &ga(30, GA_CAPACITY));
    assert_eq!(k.remaining(), 0);

    let mut k = ga_kernel();
    assert_held(&mut k, 1, &ga(31, 1));
    assert_held(&mut k, 2, &ga(32, 2));
    assert_eq!(k.remaining(), 3);
    assert_held(&mut k, 3, &ga(33, 3));
    assert_eq!(k.remaining(), 0);

    let mut k = kernel_with(Inventory::seats(&[5, 5]).unwrap(), ROOMY);
    assert_held(&mut k, 1, &seats(34, 0, 5));
    assert_held(&mut k, 2, &seats(35, 5, 5));
    assert_eq!(k.remaining(), 0);
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. STATE_LIFECYCLE §5.7 "expire releases
/// only Held"; ADR §6 a late capture never resurrects an expired order "or
/// releas[es] inventory now owned by another order", so released inventory
/// can be owned by another order; README "Implemented meaning". After expiry
/// releases a hold, a new command, order and operation can take those units,
/// including a superset of released and never-held seats, while the expired
/// order stays Expired without inventory. Reuse after cancel_scope is class B:
/// ADR §7 cancellation is a sticky local fence, and no contract defines reopening.
#[test]
fn inventory_released_by_expiry_is_reusable_by_a_new_command() {
    let mut k = seat_kernel();
    let old = seats(30, 2, 4);
    assert_held(&mut k, 1, &old);
    assert!(k.expire(ctx(EXPIRY), old.order_id).unwrap());
    assert_eq!(k.remaining(), 70);
    let new = Reserve {
        expires_at_ms: 500,
        ..seats(31, 0, 8)
    };
    assert_held(&mut k, EXPIRY + 1, &new);
    let expired = k.order(old.order_id).unwrap();
    assert_eq!(expired.state, OrderState::Expired);
    assert!(!expired.inventory_owned);
    assert_eq!(k.remaining(), 62);

    let mut k = ga_kernel();
    let old = ga(32, GA_CAPACITY);
    assert_held(&mut k, 1, &old);
    assert!(k.expire(ctx(EXPIRY), old.order_id).unwrap());
    assert_eq!(k.remaining(), GA_CAPACITY);
    let new = Reserve {
        expires_at_ms: 500,
        ..ga(33, GA_CAPACITY)
    };
    assert_held(&mut k, EXPIRY + 1, &new);
    let expired = k.order(old.order_id).unwrap();
    assert_eq!(expired.state, OrderState::Expired);
    assert!(!expired.inventory_owned);
    assert_eq!(k.remaining(), 0);
}

/// Unrelated rejections, errors and replays, then the final success. Every
/// rejected request asks for the target selection, so any partial allocation
/// would make the final reservation fail.
fn success_after_noise(
    mut k: Kernel,
    holder: Reserve,
    blocked: Reserve,
    target: Selection,
    invalid: [Selection; 2],
) -> Kernel {
    let at = |n: u8| Reserve {
        selection: target,
        ..request(n, 0)
    };
    assert_held(&mut k, 1, &holder);
    assert_rejected(&mut k, 2, &blocked, Rejection::Unavailable);

    // ADR §3/§5: replay returns the original result and is read-only.
    let before = k.clone();
    for (r, original) in [
        (&holder, ReserveOutcome::Held(holder.order_id)),
        (&blocked, ReserveOutcome::Rejected(Rejection::Unavailable)),
    ] {
        let replay = k.reserve(ctx(3), r.clone()).unwrap();
        assert!(replay.replayed);
        assert_eq!(replay.original, original);
    }
    assert_eq!(k, before);

    // Recorded business rejections (STATE_LIFECYCLE §2). The exact variants are
    // class B characterizations; that nothing is allocated is ADR §4.
    let reused_order = Reserve {
        order_id: holder.order_id,
        ..at(40)
    };
    assert_rejected(&mut k, 4, &reused_order, Rejection::OrderExists);
    let reused_payment = Reserve {
        payment: holder.payment,
        ..at(41)
    };
    assert_rejected(&mut k, 5, &reused_payment, Rejection::OperationAlreadyBound);
    for (n, selection) in [(42, invalid[0]), (43, invalid[1])] {
        let r = Reserve {
            selection,
            ..request(n, 0)
        };
        assert_rejected(&mut k, 6, &r, Rejection::InvalidRequest);
    }
    let already_expired = Reserve {
        expires_at_ms: 7,
        ..at(44)
    };
    assert_rejected(&mut k, 7, &already_expired, Rejection::InvalidRequest);

    // Errors change no state (whole-kernel Eq); variants are class B.
    let target_request = at(45);
    let altered = Reserve {
        expires_at_ms: EXPIRY + 1,
        ..holder.clone()
    };
    assert_error_leaves_state(&mut k, ctx(8), altered, KernelError::CommandConflict);
    assert_error_leaves_state(
        &mut k,
        ctx(0),
        target_request.clone(),
        KernelError::ClockRegression,
    );
    let stale = Context {
        fence: ExecutionFence {
            owner: id(8),
            generation: 2,
        },
        ..ctx(8)
    };
    assert_error_leaves_state(
        &mut k,
        stale,
        target_request.clone(),
        KernelError::ExecutionFenced,
    );
    let old_semantics = Context {
        semantics_version: SEMANTICS_VERSION - 1,
        ..ctx(8)
    };
    assert_error_leaves_state(
        &mut k,
        old_semantics,
        target_request.clone(),
        KernelError::UnsupportedSemantics,
    );
    let foreign = Reserve {
        id: CommandId {
            scope: id(77),
            ..target_request.id
        },
        ..target_request.clone()
    };
    assert_error_leaves_state(&mut k, ctx(8), foreign, KernelError::WrongScope);

    // The same command identity that only met errors is still a new command.
    assert_held(&mut k, 9, &target_request);
    assert_eq!(k.order(blocked.order_id), None);
    k
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT and S5-FINITE. ADR §3/§5: replay
/// returns the original result and is read-only; ADR §4 "Every fallible
/// validation precedes all mutation" (no partial allocation); STATE_LIFECYCLE
/// §2: business rejections are recorded command results. After a blocked
/// overlap, replays, order/operation reuse, invalid and expired requests and
/// guard errors, the still-free target selection must be held, on a seat and
/// a GA fixture. Cross-kind selections are class B characterizations.
#[test]
fn success_follows_unrelated_rejections_errors_and_replays() {
    let k = success_after_noise(
        seat_kernel(),
        seats(30, 10, 3),
        seats(31, 12, 4),
        Selection::Seats {
            first: 13,
            count: 3,
        },
        [
            Selection::Seats {
                first: 63,
                count: 4,
            },
            Selection::GeneralAdmission { count: 1 },
        ],
    );
    assert_eq!(k.remaining(), 70 - 6);

    let k = success_after_noise(
        ga_kernel(),
        ga(30, 4),
        ga(31, 3),
        Selection::GeneralAdmission { count: 2 },
        [
            Selection::GeneralAdmission { count: 0 },
            Selection::Seats { first: 0, count: 1 },
        ],
    );
    assert_eq!(k.remaining(), 0);
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT and S5-FINITE. README "Implemented
/// meaning": bounded commands/orders/observations with no dedupe eviction; ADR
/// §3 "capacity exhaustion backpressures instead of forgetting"; STATE_LIFECYCLE
/// §2 rejections are recorded. With the smallest legal limits a reservation is
/// held, and with three command and two order slots the last of each still
/// admits a reservation after a recorded rejection. Old results still replay;
/// only the next new command backpressures. Inclusive limits and the exact
/// Capacity variant are class B characterizations.
#[test]
fn last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection() {
    let minimal = Limits {
        commands: 1,
        orders: 1,
        observations: 1,
    };
    let tight = Limits {
        commands: 3,
        orders: 2,
        observations: 1,
    };
    let fixtures = [
        (
            Inventory::seats(&SEGMENTS).unwrap(),
            [seats(30, 0, 2), seats(31, 1, 2), seats(32, 2, 3)],
            seats(33, 10, 1),
        ),
        (
            Inventory::general_admission(GA_CAPACITY).unwrap(),
            [ga(30, 3), ga(31, 4), ga(32, 3)],
            ga(33, 1),
        ),
    ];
    for (inventory, [first, blocked, last], next) in fixtures {
        let mut k = kernel_with(inventory.clone(), minimal);
        assert_held(&mut k, 1, &first);

        let mut k = kernel_with(inventory, tight);
        assert_held(&mut k, 1, &first);
        assert_rejected(&mut k, 2, &blocked, Rejection::Unavailable);
        assert_eq!(k.order_count(), 1);
        assert_held(&mut k, 3, &last);
        assert_eq!(k.order_count(), 2);

        let before = k.clone();
        assert!(k.reserve(ctx(4), first.clone()).unwrap().replayed);
        assert!(k.reserve(ctx(4), blocked.clone()).unwrap().replayed);
        assert_eq!(k, before);
        assert_error_leaves_state(&mut k, ctx(4), next, KernelError::Capacity);
    }
}

/// CONTRACT_INVARIANTS §5 / S5-SAFE-REJECT. README "Hard boundaries": "The
/// initial fixture accepts positive-price orders"; STATE_LIFECYCLE §5.7 and §2
/// (as asserted by expiry_instant_is_treated_consistently_by_every_entry_point):
/// now_ms >= expires_at_ms is expired, so expires_at_ms = now_ms + 1 is live.
/// The smallest positive price with a 1 ms TTL is held on both fixtures and is
/// released exactly at its expiry instant.
#[test]
fn smallest_positive_price_and_one_millisecond_ttl_are_held() {
    let now = 40;
    for (mut k, selection) in [
        (
            seat_kernel(),
            Selection::Seats {
                first: 69,
                count: 1,
            },
        ),
        (ga_kernel(), Selection::GeneralAdmission { count: 1 }),
    ] {
        let total = k.remaining();
        let r = Reserve {
            selection,
            amount: amount(1),
            expires_at_ms: now + 1,
            ..request(30, 0)
        };
        assert_held(&mut k, now, &r);
        assert!(k.expire(ctx(now + 1), r.order_id).unwrap());
        assert_eq!(k.order(r.order_id).unwrap().state, OrderState::Expired);
        assert_eq!(k.remaining(), total);
    }
}

// ---------------------------------------------------------------------------
// CONTRACT_INVARIANTS §5 error-precedence pairs (S5-PRECEDENCE).
// ---------------------------------------------------------------------------

/// A context under a semantics version other than v4.
fn old_semantics(now_ms: u64) -> Context {
    Context {
        semantics_version: SEMANTICS_VERSION - 1,
        ..ctx(now_ms)
    }
}

/// The owner installed by `replace_owner` in these examples.
fn next_fence() -> ExecutionFence {
    ExecutionFence {
        owner: id(8),
        generation: 2,
    }
}

fn ctx_under(fence: ExecutionFence, now_ms: u64) -> Context {
    Context {
        fence,
        ..ctx(now_ms)
    }
}

fn seat_limits(limits: Limits) -> Kernel {
    kernel_with(Inventory::seats(&[10]).unwrap(), limits)
}

/// The call fails with `want` and leaves the whole kernel unchanged.
fn refused<T: PartialEq + std::fmt::Debug>(
    k: &mut Kernel,
    want: KernelError,
    call: impl FnOnce(&mut Kernel) -> Result<T, KernelError>,
) {
    let before = k.clone();
    assert_eq!(call(&mut *k), Err(want));
    assert_eq!(*k, before);
}

/// A new command is recorded with `want` as its first result.
fn recorded(k: &mut Kernel, context: Context, r: Reserve, want: ReserveOutcome) {
    let reply = k.reserve(context, r).unwrap();
    assert_eq!(reply.original, want);
    assert!(!reply.replayed);
}

/// ADR §6 / addendum A: event 1 first names `a`, then `b`, quarantining both.
fn quarantine_pair(k: &mut Kernel, a: &Reserve, b: &Reserve, now_ms: u64) {
    k.observe_capture(ctx(now_ms), capture(a, 1)).unwrap();
    assert_eq!(
        k.observe_capture(ctx(now_ms + 1), capture(b, 1)).unwrap(),
        ObservationOutcome::Conflict
    );
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × local cancellation.
/// ADR §3: the same identity with a different payload is a conflict, not a new
/// command, so ADR §7's fence on new work does not record a BusinessFenced
/// result for it. A fresh identity is fenced; the original still replays.
#[test]
fn altered_payload_conflicts_after_local_cancellation() {
    let mut k = kernel();
    let original = request(3, 0);
    k.reserve(ctx(1), original.clone()).unwrap();
    k.cancel_scope(ctx(2), 2).unwrap();
    let altered = Reserve {
        expected_business_epoch: 2,
        ..original.clone()
    };
    refused(&mut k, KernelError::CommandConflict, |k| {
        k.reserve(ctx(3), altered)
    });

    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
    recorded(&mut k.clone(), ctx(3), request(4, 1), fenced);
    let before = k.clone();
    let replay = k.reserve(ctx(3), original).unwrap();
    assert!(replay.replayed);
    assert_eq!(replay.original, ReserveOutcome::Held(id(3)));
    assert_eq!(k, before);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × full command
/// records. ADR §3: an altered payload is a conflict on an existing identity,
/// which needs no new record; capacity backpressure applies to new commands.
#[test]
fn altered_payload_conflicts_at_full_command_capacity() {
    let mut k = seat_limits(Limits {
        commands: 1,
        ..ROOMY
    });
    let original = request(3, 0);
    k.reserve(ctx(1), original.clone()).unwrap();
    let altered = Reserve {
        selection: Selection::Seats { first: 1, count: 1 },
        ..original.clone()
    };
    refused(&mut k, KernelError::CommandConflict, |k| {
        k.reserve(ctx(2), altered)
    });

    refused(&mut k.clone(), KernelError::Capacity, |k| {
        k.reserve(ctx(2), request(4, 1))
    });
    assert!(k.reserve(ctx(2), original).unwrap().replayed);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × unavailable
/// inventory. ADR §3 conflict, and README "Immutable original outcome replay
/// before new-attempt availability checks": moving a held command onto taken
/// seats is a conflict, not a recorded Unavailable result.
#[test]
fn altered_payload_conflicts_when_its_selection_is_unavailable() {
    let mut k = kernel();
    let holder = request(3, 0);
    let mover = request(4, 1);
    k.reserve(ctx(1), holder).unwrap();
    k.reserve(ctx(2), mover.clone()).unwrap();
    let onto_holder = Reserve {
        selection: Selection::Seats { first: 0, count: 1 },
        ..mover.clone()
    };
    refused(&mut k, KernelError::CommandConflict, |k| {
        k.reserve(ctx(3), onto_holder)
    });

    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
    recorded(&mut k.clone(), ctx(3), request(5, 0), unavailable);
    assert!(k.reserve(ctx(3), mover).unwrap().replayed);
    assert!(k.order(id(4)).unwrap().inventory_owned);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × quarantine. ADR §3
/// conflict; ADR §6 a quarantined operation "cannot later gain a fresh
/// reservation binding". Re-pointing an existing command at a quarantined
/// operation is a conflict, records no OperationQuarantined result and leaves
/// the existing order unreviewed.
#[test]
fn altered_payload_conflicts_when_its_operation_is_quarantined() {
    let mut k = kernel();
    let (a, b, x) = (request(3, 0), request(4, 1), request(5, 2));
    for (t, r) in [(1, &a), (2, &b), (3, &x)] {
        k.reserve(ctx(t), r.clone()).unwrap();
    }
    quarantine_pair(&mut k, &a, &b, 4);
    let onto_quarantined = Reserve {
        payment: b.payment,
        ..x.clone()
    };
    refused(&mut k, KernelError::CommandConflict, |k| {
        k.reserve(ctx(6), onto_quarantined)
    });

    let fresh = Reserve {
        payment: b.payment,
        ..request(6, 3)
    };
    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
    recorded(&mut k.clone(), ctx(6), fresh, quarantined);
    assert!(k.reserve(ctx(6), x.clone()).unwrap().replayed);
    assert!(!k.order(x.order_id).unwrap().review_required);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, payload conflict × UNKNOWN. ADR §3
/// conflict; ADR §6 and STATE_LIFECYCLE §2 an UNKNOWN operation and its slot
/// survive the TTL. An altered retry after the deadline is a conflict and does
/// not record an OperationAlreadyBound result or touch the UNKNOWN order.
#[test]
fn altered_payload_conflicts_without_touching_an_unknown_payment() {
    let mut k = kernel();
    let unknown = request(3, 0);
    k.reserve(ctx(1), unknown.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), unknown.order_id).unwrap();
    let altered = Reserve {
        order_id: id(4),
        selection: Selection::Seats { first: 1, count: 1 },
        expires_at_ms: 500,
        ..unknown.clone()
    };
    refused(&mut k, KernelError::CommandConflict, |k| {
        k.reserve(ctx(EXPIRY + 1), altered.clone())
    });
    let order = k.order(unknown.order_id).unwrap();
    assert_eq!(order.state, OrderState::PaymentUnknown);
    assert!(order.inventory_owned);
    assert_eq!(k.reserved_observation_count(), 1);

    let fresh = Reserve {
        id: request(5, 1).id,
        ..altered
    };
    let bound = ReserveOutcome::Rejected(Rejection::OperationAlreadyBound);
    recorded(&mut k.clone(), ctx(EXPIRY + 1), fresh, bound);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × local
/// cancellation. ADR §5: v4 "rejects other versions", so neither a
/// BusinessFenced command result nor a ReturnRequired capture is applied under
/// another version. The same inputs under v4 then meet the cancellation.
#[test]
fn unsupported_semantics_records_nothing_after_local_cancellation() {
    let mut k = kernel();
    let unknown = request(3, 0);
    k.reserve(ctx(1), unknown.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), unknown.order_id).unwrap();
    k.cancel_scope(ctx(3), 2).unwrap();
    let fresh = request(4, 1);
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.reserve(old_semantics(4), fresh.clone())
    });
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.observe_capture(old_semantics(4), capture(&unknown, 1))
    });

    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
    recorded(&mut k, ctx(4), fresh, fenced);
    assert_eq!(
        k.observe_capture(ctx(5), capture(&unknown, 1)).unwrap(),
        ObservationOutcome::ReturnRequired
    );
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × unavailable
/// inventory. ADR §5: another version is rejected, so no Unavailable result is
/// recorded; the same identity under v4 is still a new command.
#[test]
fn unsupported_semantics_records_no_unavailable_rejection() {
    let mut k = kernel();
    k.reserve(ctx(1), request(3, 0)).unwrap();
    let blocked = request(4, 0);
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.reserve(old_semantics(2), blocked.clone())
    });

    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
    recorded(&mut k, ctx(2), blocked, unavailable);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × quarantine.
/// ADR §5 rejects other versions; ADR §6 and addendum A define the v4
/// quarantine. A conflicting event under another version quarantines nothing,
/// and a reservation naming a quarantined operation records nothing.
#[test]
fn unsupported_semantics_applies_no_quarantine() {
    let mut k = kernel();
    let (a, b) = (request(3, 0), request(4, 1));
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.observe_capture(old_semantics(4), capture(&b, 1))
    });
    assert_eq!(k.quarantined_operation_count(), 0);

    assert_eq!(
        k.observe_capture(ctx(4), capture(&b, 1)).unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(k.quarantined_operation_count(), 2);
    let reused = Reserve {
        payment: b.payment,
        ..request(5, 2)
    };
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.reserve(old_semantics(5), reused.clone())
    });
    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
    recorded(&mut k, ctx(5), reused, quarantined);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, semantics version × UNKNOWN. ADR §5
/// rejects other versions, so another version neither commits the UNKNOWN
/// send transition and its slot nor applies the first capture that would
/// spend that slot.
#[test]
fn unsupported_semantics_neither_sends_nor_captures_an_unknown_payment() {
    let mut k = kernel();
    let order = request(3, 0);
    k.reserve(ctx(1), order.clone()).unwrap();
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.mark_payment_unknown(old_semantics(2), order.order_id)
    });
    assert_eq!(k.order(order.order_id).unwrap().state, OrderState::Held);
    assert_eq!(k.reserved_observation_count(), 0);

    k.mark_payment_unknown(ctx(2), order.order_id).unwrap();
    assert_eq!(k.reserved_observation_count(), 1);
    refused(&mut k, KernelError::UnsupportedSemantics, |k| {
        k.observe_capture(old_semantics(3), capture(&order, 1))
    });
    assert_eq!(k.order(order.order_id).unwrap().captured, None);

    assert_eq!(
        k.observe_capture(ctx(3), capture(&order, 1)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.reserved_observation_count(), 0);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × local cancellation.
/// ADR §5: supplied time and monotonicity are validated at the ordered
/// boundary, so a regressed input is not admitted: no BusinessFenced result is
/// recorded and no ReturnRequired capture is applied. Valid times then meet the
/// cancellation.
#[test]
fn regressed_time_records_nothing_after_local_cancellation() {
    let mut k = kernel();
    let unknown = request(3, 0);
    k.reserve(ctx(1), unknown.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), unknown.order_id).unwrap();
    k.cancel_scope(ctx(10), 2).unwrap();
    let fresh = request(4, 1);
    refused(&mut k, KernelError::ClockRegression, |k| {
        k.reserve(ctx(5), fresh.clone())
    });
    refused(&mut k, KernelError::ClockRegression, |k| {
        k.observe_capture(ctx(5), capture(&unknown, 1))
    });

    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
    recorded(&mut k, ctx(11), fresh, fenced);
    assert_eq!(
        k.observe_capture(ctx(12), capture(&unknown, 1)).unwrap(),
        ObservationOutcome::ReturnRequired
    );
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, full command records × local
/// cancellation. STATE_LIFECYCLE §2: business rejections are recorded first
/// results; ADR §3: bounded records backpressure instead of forgetting. With no
/// command slot, no BusinessFenced result can be recorded, so the call is
/// refused unchanged; a twin with free slots records BusinessFenced.
#[test]
fn full_command_capacity_backpressures_after_local_cancellation() {
    let history = |limits| {
        let mut k = seat_limits(limits);
        k.reserve(ctx(1), request(3, 0)).unwrap();
        k.cancel_scope(ctx(2), 2).unwrap();
        k
    };
    let mut full = history(Limits {
        commands: 1,
        ..ROOMY
    });
    refused(&mut full, KernelError::Capacity, |k| {
        k.reserve(ctx(3), request(4, 1))
    });

    let fenced = ReserveOutcome::Rejected(Rejection::BusinessFenced);
    recorded(&mut history(ROOMY), ctx(3), request(4, 1), fenced);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, stale execution fence × unavailable
/// inventory. ADR §3/§6: internal fencing stops new internal writes by an old
/// owner, so the old owner records no Unavailable result; the current owner
/// does.
#[test]
fn stale_execution_fence_records_no_unavailable_rejection() {
    let mut k = kernel();
    k.reserve(ctx(1), request(3, 0)).unwrap();
    k.replace_owner(ctx(2), next_fence()).unwrap();
    let blocked = request(4, 0);
    refused(&mut k, KernelError::ExecutionFenced, |k| {
        k.reserve(ctx(3), blocked.clone())
    });

    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
    recorded(&mut k, ctx_under(next_fence(), 3), blocked, unavailable);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, stale execution fence × quarantine.
/// ADR §3/§6: the old owner's writes are stopped and "the current owner applies
/// those facts under its current execution fence". An old-fence conflicting
/// event quarantines nothing, and an old-fence reservation naming the
/// quarantined operation records nothing; the current owner applies both.
#[test]
fn stale_execution_fence_applies_no_quarantine() {
    let mut k = kernel();
    let (a, b) = (request(3, 0), request(4, 1));
    k.reserve(ctx(1), a.clone()).unwrap();
    k.reserve(ctx(2), b.clone()).unwrap();
    k.observe_capture(ctx(3), capture(&a, 1)).unwrap();
    k.replace_owner(ctx(4), next_fence()).unwrap();
    refused(&mut k, KernelError::ExecutionFenced, |k| {
        k.observe_capture(ctx(5), capture(&b, 1))
    });
    assert_eq!(k.quarantined_operation_count(), 0);

    assert_eq!(
        k.observe_capture(ctx_under(next_fence(), 5), capture(&b, 1))
            .unwrap(),
        ObservationOutcome::Conflict
    );
    assert_eq!(k.quarantined_operation_count(), 2);
    let reused = Reserve {
        payment: b.payment,
        ..request(5, 2)
    };
    refused(&mut k, KernelError::ExecutionFenced, |k| {
        k.reserve(ctx(6), reused.clone())
    });
    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
    recorded(&mut k, ctx_under(next_fence(), 6), reused, quarantined);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, stale execution fence × UNKNOWN.
/// ADR §3/§6: the old owner can neither authorize a send retry nor apply the
/// late fact; STATE_LIFECYCLE §2: owner change never releases the UNKNOWN
/// operation or its slot. The current owner may retry and applies the capture.
#[test]
fn stale_execution_fence_neither_sends_nor_captures_an_unknown_payment() {
    let mut k = kernel();
    let order = request(3, 0);
    k.reserve(ctx(1), order.clone()).unwrap();
    k.mark_payment_unknown(ctx(2), order.order_id).unwrap();
    k.replace_owner(ctx(3), next_fence()).unwrap();
    refused(&mut k, KernelError::ExecutionFenced, |k| {
        k.mark_payment_unknown(ctx(4), order.order_id)
    });
    refused(&mut k, KernelError::ExecutionFenced, |k| {
        k.observe_capture(ctx(4), capture(&order, 1))
    });
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(
        k.order(order.order_id).unwrap().state,
        OrderState::PaymentUnknown
    );

    k.mark_payment_unknown(ctx_under(next_fence(), 4), order.order_id)
        .unwrap();
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(
        k.observe_capture(ctx_under(next_fence(), 5), capture(&order, 1))
            .unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.reserved_observation_count(), 0);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × unavailable
/// inventory. ADR §5: a regressed input is not admitted, so no Unavailable
/// result is recorded; the same identity at a valid time is a new command.
#[test]
fn regressed_time_records_no_unavailable_rejection() {
    let mut k = kernel();
    k.reserve(ctx(10), request(3, 0)).unwrap();
    let blocked = request(4, 0);
    refused(&mut k, KernelError::ClockRegression, |k| {
        k.reserve(ctx(5), blocked.clone())
    });

    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
    recorded(&mut k, ctx(11), blocked, unavailable);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × quarantine. ADR §5:
/// a regressed input is not admitted; ADR addendum A: an admitted conflict
/// quarantines bound operations even when it returns Capacity. A regressed
/// conflicting event therefore quarantines nothing, with or without evidence
/// budget, and a regressed reservation naming the quarantined operation
/// records nothing.
#[test]
fn regressed_time_applies_no_quarantine() {
    for observations in [ROOMY.observations, 1] {
        let mut k = seat_limits(Limits {
            observations,
            ..ROOMY
        });
        let (a, b) = (request(3, 0), request(4, 1));
        k.reserve(ctx(1), a.clone()).unwrap();
        k.reserve(ctx(2), b.clone()).unwrap();
        k.observe_capture(ctx(10), capture(&a, 1)).unwrap();
        refused(&mut k, KernelError::ClockRegression, |k| {
            k.observe_capture(ctx(5), capture(&b, 1))
        });
        assert_eq!(k.quarantined_operation_count(), 0);

        let admitted = k.observe_capture(ctx(11), capture(&b, 1));
        if observations == 1 {
            assert_eq!(admitted, Err(KernelError::Capacity));
        } else {
            assert_eq!(admitted, Ok(ObservationOutcome::Conflict));
        }
        assert_eq!(k.quarantined_operation_count(), 2);
        let reused = Reserve {
            payment: b.payment,
            ..request(5, 2)
        };
        refused(&mut k, KernelError::ClockRegression, |k| {
            k.reserve(ctx(5), reused.clone())
        });
        let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
        recorded(&mut k, ctx(12), reused, quarantined);
    }
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, regressed time × UNKNOWN. ADR §5: a
/// regressed capture is not admitted, so it neither records the capture nor
/// spends the reserved slot; STATE_LIFECYCLE §2 keeps the slot for the later
/// valid capture.
#[test]
fn regressed_time_applies_no_capture_to_an_unknown_payment() {
    let mut k = kernel();
    let order = request(3, 0);
    k.reserve(ctx(1), order.clone()).unwrap();
    k.mark_payment_unknown(ctx(10), order.order_id).unwrap();
    refused(&mut k, KernelError::ClockRegression, |k| {
        k.observe_capture(ctx(5), capture(&order, 1))
    });
    assert_eq!(k.reserved_observation_count(), 1);
    assert_eq!(k.order(order.order_id).unwrap().captured, None);

    assert_eq!(
        k.observe_capture(ctx(11), capture(&order, 1)).unwrap(),
        ObservationOutcome::PaymentConfirmed
    );
    assert_eq!(k.reserved_observation_count(), 0);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, full command records × unavailable
/// inventory. STATE_LIFECYCLE §2 records business rejections; ADR §3 bounded
/// records backpressure instead of forgetting. With no command slot, no
/// Unavailable result is recorded; a twin with free slots records it.
#[test]
fn full_command_capacity_backpressures_before_an_unavailable_rejection() {
    let history = |limits| {
        let mut k = seat_limits(limits);
        k.reserve(ctx(1), request(3, 0)).unwrap();
        k
    };
    let mut full = history(Limits {
        commands: 1,
        ..ROOMY
    });
    refused(&mut full, KernelError::Capacity, |k| {
        k.reserve(ctx(2), request(4, 0))
    });

    let unavailable = ReserveOutcome::Rejected(Rejection::Unavailable);
    recorded(&mut history(ROOMY), ctx(2), request(4, 0), unavailable);
}

/// CONTRACT_INVARIANTS §5 / S5-PRECEDENCE, full command records × quarantine on
/// reserve. STATE_LIFECYCLE §2 and ADR §3 as above; ADR §6 bars the quarantined
/// operation from a fresh binding. With no command slot, no
/// OperationQuarantined result is recorded; a twin with free slots records it.
#[test]
fn full_command_capacity_backpressures_before_a_quarantine_rejection() {
    let (a, b) = (request(3, 0), request(4, 1));
    let history = |limits| {
        let mut k = seat_limits(limits);
        k.reserve(ctx(1), a.clone()).unwrap();
        k.reserve(ctx(2), b.clone()).unwrap();
        quarantine_pair(&mut k, &a, &b, 3);
        k
    };
    let reused = Reserve {
        payment: b.payment,
        ..request(5, 2)
    };
    let mut full = history(Limits {
        commands: 2,
        ..ROOMY
    });
    refused(&mut full, KernelError::Capacity, |k| {
        k.reserve(ctx(5), reused.clone())
    });

    let quarantined = ReserveOutcome::Rejected(Rejection::OperationQuarantined);
    recorded(&mut history(ROOMY), ctx(5), reused, quarantined);
}
