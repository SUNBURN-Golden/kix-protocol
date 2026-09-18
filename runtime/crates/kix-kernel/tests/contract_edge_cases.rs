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

use kix_kernel::{
    CaptureObservation, CommandId, Context, ExecutionFence, Inventory, Kernel, KernelError, Limits,
    ObservationOutcome, OrderState, ProviderOperation, Rejection, Reserve, ReserveOutcome,
    SEMANTICS_VERSION, Selection,
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
