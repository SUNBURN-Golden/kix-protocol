mod common;

use common::{ctx, engine, id, observation, open_unknown, reserve, terminate_for};
use kix_kernel_v5::{
    Blocker, DAY_MS, DEFAULT_MEMORY_RESIDENCY_CAP_RECORDS, DEFAULT_MEMORY_RESIDENCY_MS,
    DEFAULT_RETENTION_FLOOR_MS, DEFAULT_RETRY_SUPPORT_WINDOW_MS, HOUR_MS, ImplicitHold, Kernel,
    KernelError, ObservationOutcome, OrderState, REPORT_SLO_MS, REPORT_SLO_RECORDS, ReclaimPolicy,
};

const OPEN_INPUTS: [Blocker; 3] = [Blocker::I09, Blocker::I10, Blocker::I13];

fn policy() -> ReclaimPolicy {
    ReclaimPolicy::default()
}

fn blockers(kernel: &Kernel, now_ms: u64, order: u8) -> Vec<Blocker> {
    kernel
        .reclaim_report(now_ms, id(order), &policy())
        .unwrap()
        .blockers
}

/// A report never says eligible: it is ordered and ends with the open inputs.
fn assert_shape(list: &[Blocker]) {
    assert!(list.is_sorted(), "fixed report order: {list:?}");
    assert!(list.len() >= OPEN_INPUTS.len());
    assert_eq!(&list[list.len() - 3..], OPEN_INPUTS);
}

#[test]
fn defaults_are_the_owner_delegate_values() {
    let defaults = policy();
    assert_eq!(defaults.retry_support_window_ms, 15 * 24 * 3_600_000);
    assert_eq!(defaults.retry_support_window_ms, 1_296_000_000);
    assert_eq!(DEFAULT_RETRY_SUPPORT_WINDOW_MS, 15 * DAY_MS);
    assert_eq!(defaults.memory_residency_ms, 72 * HOUR_MS);
    assert_eq!(DEFAULT_MEMORY_RESIDENCY_MS, 259_200_000);
    assert_eq!(defaults.memory_residency_cap_records, 10_000);
    assert_eq!(DEFAULT_MEMORY_RESIDENCY_CAP_RECORDS, 10_000);
    // Five calendar years are at most 1,827 days; the floor never ends early.
    assert_eq!(defaults.retention_floor_ms, 1_827 * DAY_MS);
    assert_eq!(DEFAULT_RETENTION_FLOOR_MS, defaults.retention_floor_ms);
    assert!(defaults.retention_floor_ms >= 5 * 365 * DAY_MS);
    assert_eq!((REPORT_SLO_MS, REPORT_SLO_RECORDS), (50, 10_000));
}

#[test]
fn blocker_declaration_order_is_the_fixed_report_order() {
    assert!(
        [
            Blocker::ActiveOp,
            Blocker::ReservedSlot,
            Blocker::ReviewRequired,
            Blocker::UnboundFence,
            Blocker::ReturnObligation,
            Blocker::ReplayWindow,
            Blocker::Hold,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
        .is_sorted_by(|a, b| a < b)
    );
}

#[test]
fn unterminated_orders_list_active_op_and_the_reserved_slot() {
    let mut kernel = engine();
    kernel.reserve(ctx(1), reserve(3, 1, 1)).unwrap();
    assert_eq!(
        blockers(&kernel, 1, 3),
        vec![
            Blocker::ActiveOp,
            Blocker::ReplayWindow,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
    kernel.mark_payment_unknown(ctx(2), id(3)).unwrap();
    assert_eq!(
        blockers(&kernel, 2, 3),
        vec![
            Blocker::ActiveOp,
            Blocker::ReservedSlot,
            Blocker::ReplayWindow,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
}

#[test]
fn termination_clears_only_active_op() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    let report = kernel.reclaim_report(3, id(3), &policy()).unwrap();
    assert_eq!(
        report.blockers,
        vec![
            Blocker::ReservedSlot,
            Blocker::ReplayWindow,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
    assert_eq!(report.terminated_at_ms, Some(3));
    assert_eq!(report.hold, None);
    assert!(report.implicit_hold.is_empty());
    // Residency runs from the terminal state; the floor from the termination.
    assert_eq!(report.memory_residency_ends_at_ms, Some(3 + 72 * HOUR_MS));
    assert_eq!(report.retention_floor_ends_at_ms, Some(3 + 1_827 * DAY_MS));
    // The retry-support window runs from the reserve command's first result.
    assert_eq!(report.replay_window_ends_at_ms, 1 + 15 * DAY_MS);
    // Even far past every window the slot, and the open inputs, still block.
    let late = blockers(&kernel, 40 * DAY_MS, 3);
    assert_eq!(
        late,
        vec![
            Blocker::ReservedSlot,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13
        ]
    );
    assert_shape(&late);
}

#[test]
fn unterminated_report_has_no_termination_derived_times() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let report = kernel.reclaim_report(2, id(3), &policy()).unwrap();
    assert_eq!(report.terminated_at_ms, None);
    assert_eq!(report.memory_residency_ends_at_ms, None);
    assert_eq!(report.retention_floor_ends_at_ms, None);
}

#[test]
fn replay_window_ends_exactly_at_first_result_plus_window() {
    let mut kernel = engine();
    kernel.reserve(ctx(5), reserve(3, 1, 1)).unwrap();
    let window = 1_000;
    let short = ReclaimPolicy {
        retry_support_window_ms: window,
        ..policy()
    };
    let at = |now_ms: u64| {
        kernel
            .reclaim_report(now_ms, id(3), &short)
            .unwrap()
            .blockers
    };
    assert!(at(5 + window - 1).contains(&Blocker::ReplayWindow));
    assert!(!at(5 + window).contains(&Blocker::ReplayWindow));
    assert_eq!(
        kernel
            .reclaim_report(5, id(3), &short)
            .unwrap()
            .replay_window_ends_at_ms,
        5 + window
    );
    // A later reservation of another order does not move this order's window.
    kernel.reserve(ctx(50), reserve(4, 2, 1)).unwrap();
    assert_eq!(
        kernel
            .reclaim_report(50, id(3), &short)
            .unwrap()
            .replay_window_ends_at_ms,
        5 + window
    );
}

#[test]
fn saturating_arithmetic_never_wraps_the_windows() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    let huge = ReclaimPolicy {
        retry_support_window_ms: u64::MAX,
        memory_residency_ms: u64::MAX,
        memory_residency_cap_records: 0,
        retention_floor_ms: u64::MAX,
    };
    let report = kernel.reclaim_report(3, id(3), &huge).unwrap();
    assert_eq!(report.replay_window_ends_at_ms, u64::MAX);
    assert_eq!(report.memory_residency_ends_at_ms, Some(u64::MAX));
    assert_eq!(report.retention_floor_ends_at_ms, Some(u64::MAX));
    assert!(report.blockers.contains(&Blocker::ReplayWindow));
}

#[test]
fn review_unbound_fence_and_open_conflict_hold_are_listed() {
    let mut kernel = engine();
    kernel.reserve(ctx(1), reserve(3, 1, 1)).unwrap();
    kernel.mark_payment_unknown(ctx(2), id(3)).unwrap();
    let bound = reserve(4, 2, 1);
    kernel.reserve(ctx(3), bound.clone()).unwrap();
    kernel
        .observe_capture(ctx(4), observation(&bound, 1))
        .unwrap();
    assert_eq!(
        kernel.observe_capture(ctx(5), observation(&reserve(3, 1, 1), 1)),
        Ok(ObservationOutcome::Conflict)
    );
    let report = kernel.reclaim_report(5, id(3), &policy()).unwrap();
    assert_eq!(
        report.blockers,
        vec![
            Blocker::ActiveOp,
            Blocker::ReservedSlot,
            Blocker::ReviewRequired,
            Blocker::UnboundFence,
            Blocker::ReplayWindow,
            Blocker::Hold,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
    assert_eq!(report.hold, None);
    assert_eq!(report.implicit_hold, vec![ImplicitHold::OpenConflict]);
    assert!(kernel.order(id(3)).unwrap().review_required);
    assert_eq!(kernel.order(id(3)).unwrap().captured, None);
}

#[test]
fn return_required_is_listed_and_treated_as_held() {
    let mut kernel = engine();
    let request = reserve(3, 1, 1);
    kernel.reserve(ctx(1), request.clone()).unwrap();
    kernel.mark_payment_unknown(ctx(2), id(3)).unwrap();
    kernel.cancel_scope(ctx(3), 2).unwrap();
    assert_eq!(
        kernel
            .observe_capture(ctx(4), observation(&request, 1))
            .unwrap(),
        ObservationOutcome::ReturnRequired
    );
    let report = kernel.reclaim_report(4, id(3), &policy()).unwrap();
    assert_eq!(
        report.blockers,
        vec![
            Blocker::ActiveOp,
            Blocker::ReturnObligation,
            Blocker::ReplayWindow,
            Blocker::Hold,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
    assert_eq!(report.hold, None);
    assert_eq!(report.implicit_hold, vec![ImplicitHold::ReturnRequired]);
    assert_eq!(
        kernel.order(id(3)).unwrap().state,
        OrderState::ReturnRequired
    );
}

#[test]
fn late_capture_after_termination_adds_the_return_obligation() {
    let mut kernel = engine();
    let request = open_unknown(&mut kernel);
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    assert_eq!(
        kernel
            .observe_capture(ctx(100), observation(&request, 1))
            .unwrap(),
        ObservationOutcome::ReturnRequired
    );
    // Past the retry-support window: only the return obligation, the implicit
    // hold and the open inputs remain. The slot became stored evidence.
    let report = kernel
        .reclaim_report(30 * DAY_MS, id(3), &policy())
        .unwrap();
    assert_eq!(
        report.blockers,
        vec![
            Blocker::ReturnObligation,
            Blocker::Hold,
            Blocker::I09,
            Blocker::I10,
            Blocker::I13,
        ]
    );
    assert_eq!(report.implicit_hold, vec![ImplicitHold::ReturnRequired]);
    assert_eq!(report.terminated_at_ms, Some(3));
}

#[test]
fn no_report_is_ever_eligible() {
    let mut kernel = engine();
    kernel.reserve(ctx(1), reserve(3, 1, 1)).unwrap();
    open_unknown_second(&mut kernel);
    for order in [3, 4] {
        for now_ms in [3, DAY_MS, 100 * DAY_MS, u64::MAX / 2] {
            assert_shape(&blockers(&kernel, now_ms, order));
        }
    }
    kernel
        .terminate(ctx(5), terminate_for(&kernel, 10, 4))
        .unwrap();
    for now_ms in [5, DAY_MS, 5_000 * DAY_MS, u64::MAX] {
        assert_shape(&blockers(&kernel, now_ms, 4));
    }
}

fn open_unknown_second(kernel: &mut Kernel) {
    kernel.reserve(ctx(2), reserve(4, 2, 1)).unwrap();
    kernel.mark_payment_unknown(ctx(3), id(4)).unwrap();
}

#[test]
fn report_does_not_change_state_or_advance_time() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    let before = kernel.clone();
    let report = kernel.reclaim_report(3, id(3), &policy()).unwrap();
    kernel.reclaim_reports(3, &policy()).unwrap();
    assert_eq!(kernel, before);
    assert_eq!(report.order_id, id(3));
    assert!(report.blockers.contains(&Blocker::ReservedSlot));
    // A later report at the same ordered time is still accepted: no time moved.
    assert!(!kernel.expire(ctx(3), id(3)).unwrap());
}

#[test]
fn unknown_order_and_regressed_time_are_rejected_without_change() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let before = kernel.clone();
    assert_eq!(
        kernel.reclaim_report(2, id(99), &policy()),
        Err(KernelError::UnknownOrder)
    );
    assert_eq!(
        kernel.reclaim_report(1, id(3), &policy()),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(
        kernel.reclaim_reports(1, &policy()),
        Err(KernelError::ClockRegression)
    );
    assert_eq!(kernel, before);
}
