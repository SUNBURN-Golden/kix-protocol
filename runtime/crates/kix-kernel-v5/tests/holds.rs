mod common;

use common::{ctx, engine, id, open_unknown, reserve};
use kix_kernel_v5::{
    Blocker, Context, DAY_MS, ExecutionFence, HoldKind, HoldRef, Kernel, KernelError, ReclaimPolicy,
};

fn blockers(kernel: &Kernel, now_ms: u64, order: u8) -> Vec<Blocker> {
    kernel
        .reclaim_report(now_ms, id(order), &ReclaimPolicy::default())
        .unwrap()
        .blockers
}

fn placed(kernel: &mut Kernel, now_ms: u64, hold: u8, kind: HoldKind) -> HoldRef {
    kernel
        .place_hold(ctx(now_ms), id(3), id(hold), kind, id(50))
        .unwrap()
        .original
}

#[test]
fn every_hold_kind_blocks_and_is_recorded() {
    for (n, kind) in [HoldKind::Legal, HoldKind::Dispute, HoldKind::Erasure]
        .into_iter()
        .enumerate()
    {
        let mut kernel = engine();
        open_unknown(&mut kernel);
        let hold_id = 60 + n as u8;
        let applied = kernel
            .place_hold(ctx(3), id(3), id(hold_id), kind, id(50))
            .unwrap();
        assert!(!applied.replayed);
        assert_eq!(
            applied.original,
            HoldRef {
                id: id(hold_id),
                kind,
                placed_at_ms: 3,
                placed_by: id(50),
            }
        );
        assert_eq!(kernel.hold(id(3)), Some(&applied.original));
        let report = kernel
            .reclaim_report(3, id(3), &ReclaimPolicy::default())
            .unwrap();
        assert_eq!(report.hold, Some(applied.original));
        assert!(report.blockers.contains(&Blocker::Hold));
        assert!(report.implicit_hold.is_empty());
        // Placing a hold changes no order, inventory, slot or evidence.
        let order = kernel.order(id(3)).unwrap();
        assert!(order.inventory_owned && !order.review_required);
        assert_eq!(kernel.reserved_observation_count(), 1);
        assert_eq!(kernel.observation_count(), 0);
    }
}

#[test]
fn a_hold_never_expires_by_time() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let hold = placed(&mut kernel, 3, 60, HoldKind::Legal);
    for now_ms in [3, DAY_MS, 1_827 * DAY_MS, 10_000 * DAY_MS, u64::MAX] {
        let report = kernel
            .reclaim_report(now_ms, id(3), &ReclaimPolicy::default())
            .unwrap();
        assert!(report.blockers.contains(&Blocker::Hold), "now {now_ms}");
        assert_eq!(report.hold, Some(hold));
    }
    // Ordinary commands, including expiry, do not clear it either.
    assert!(!kernel.expire(ctx(50), id(3)).unwrap());
    assert!(kernel.expire(ctx(100), id(3)).is_ok());
    assert_eq!(kernel.hold(id(3)), Some(&hold));
}

#[test]
fn replaying_the_same_placement_returns_the_original_and_changes_nothing() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let hold = placed(&mut kernel, 3, 60, HoldKind::Dispute);
    let before = kernel.clone();
    let replay = kernel
        .place_hold(ctx(9), id(3), id(60), HoldKind::Dispute, id(50))
        .unwrap();
    assert!(replay.replayed);
    assert_eq!(replay.original, hold);
    assert_eq!(replay.original.placed_at_ms, 3);
    assert_eq!(kernel, before);
    // A replay is a read: it neither checks the fence nor advances time.
    let other_owner = Context {
        fence: ExecutionFence {
            owner: id(8),
            generation: 1,
        },
        now_ms: 1,
        semantics_version: kix_kernel_v5::SEMANTICS_VERSION,
    };
    assert!(
        kernel
            .place_hold(other_owner, id(3), id(60), HoldKind::Dispute, id(50))
            .unwrap()
            .replayed
    );
    assert_eq!(kernel, before);
}

#[test]
fn same_hold_id_with_a_different_payload_conflicts() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel.reserve(ctx(3), reserve(4, 2, 1)).unwrap();
    placed(&mut kernel, 3, 60, HoldKind::Legal);
    let before = kernel.clone();
    for (order, kind, by) in [
        (3, HoldKind::Erasure, 50),
        (3, HoldKind::Legal, 51),
        (4, HoldKind::Legal, 50),
    ] {
        assert_eq!(
            kernel.place_hold(ctx(4), id(order), id(60), kind, id(by)),
            Err(KernelError::CommandConflict)
        );
        assert_eq!(kernel, before);
    }
}

#[test]
fn an_order_carries_one_hold_and_a_second_one_is_rejected() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let first = placed(&mut kernel, 3, 60, HoldKind::Legal);
    let before = kernel.clone();
    assert_eq!(
        kernel.place_hold(ctx(4), id(3), id(61), HoldKind::Dispute, id(50)),
        Err(KernelError::HoldExists)
    );
    assert_eq!(kernel, before);
    assert_eq!(kernel.hold(id(3)), Some(&first));
}

#[test]
fn placement_rejections_change_no_state() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let before = kernel.clone();
    assert_eq!(
        kernel.place_hold(
            Context {
                semantics_version: 4,
                ..ctx(3)
            },
            id(3),
            id(60),
            HoldKind::Legal,
            id(50)
        ),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(
        kernel.place_hold(
            Context {
                fence: ExecutionFence {
                    owner: id(8),
                    generation: 2,
                },
                ..ctx(3)
            },
            id(3),
            id(60),
            HoldKind::Legal,
            id(50)
        ),
        Err(KernelError::ExecutionFenced)
    );
    assert_eq!(
        kernel.place_hold(ctx(1), id(3), id(60), HoldKind::Legal, id(50)),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(
        kernel.place_hold(ctx(3), id(99), id(60), HoldKind::Legal, id(50)),
        Err(KernelError::UnknownOrder)
    );
    assert_eq!(kernel, before);
    assert!(kernel.hold(id(3)).is_none());
}

#[test]
fn clear_hold_is_explicit_and_releases_nothing_else() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let hold = placed(&mut kernel, 3, 60, HoldKind::Erasure);
    let cleared = kernel.clear_hold(ctx(5), id(60), id(51)).unwrap();
    assert_eq!(cleared.hold, hold);
    assert_eq!(cleared.order_id, id(3));
    assert_eq!(cleared.cleared_by, id(51));
    assert_eq!(cleared.cleared_at_ms, 5);
    assert!(kernel.hold(id(3)).is_none());
    // Slot, evidence and the open inputs are unchanged by clearing.
    assert_eq!(kernel.reserved_observation_count(), 1);
    assert_eq!(
        blockers(&kernel, 5, 3),
        vec![
            Blocker::ActiveOp,
            Blocker::ReservedSlot,
            Blocker::ReplayWindow,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
    // The identifier is not placed any more; a second clear is rejected.
    let before = kernel.clone();
    assert_eq!(
        kernel.clear_hold(ctx(6), id(60), id(51)),
        Err(KernelError::UnknownHold)
    );
    assert_eq!(kernel, before);
    // A new hold with a new identifier can be placed after clearing.
    let second = placed(&mut kernel, 7, 61, HoldKind::Legal);
    assert_eq!(kernel.hold(id(3)), Some(&second));
}

#[test]
fn clear_hold_rejections_change_no_state() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    placed(&mut kernel, 3, 60, HoldKind::Legal);
    let before = kernel.clone();
    assert_eq!(
        kernel.clear_hold(ctx(4), id(99), id(51)),
        Err(KernelError::UnknownHold)
    );
    assert_eq!(
        kernel.clear_hold(ctx(1), id(60), id(51)),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(
        kernel.clear_hold(
            Context {
                semantics_version: 4,
                ..ctx(4)
            },
            id(60),
            id(51)
        ),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(
        kernel.clear_hold(
            Context {
                fence: ExecutionFence {
                    owner: id(8),
                    generation: 2,
                },
                ..ctx(4)
            },
            id(60),
            id(51)
        ),
        Err(KernelError::ExecutionFenced)
    );
    assert_eq!(kernel, before);
}

#[test]
fn clearing_an_explicit_hold_keeps_an_implicit_hold() {
    // ReturnRequired is treated as held with no hold reference at all.
    let mut kernel = engine();
    let request = open_unknown(&mut kernel);
    kernel.cancel_scope(ctx(3), 2).unwrap();
    kernel
        .observe_capture(ctx(4), common::observation(&request, 1))
        .unwrap();
    placed(&mut kernel, 5, 60, HoldKind::Dispute);
    kernel.clear_hold(ctx(6), id(60), id(51)).unwrap();
    let report = kernel
        .reclaim_report(6, id(3), &ReclaimPolicy::default())
        .unwrap();
    assert_eq!(report.hold, None);
    assert!(report.blockers.contains(&Blocker::Hold));
    assert!(report.blockers.contains(&Blocker::ReturnObligation));
}
