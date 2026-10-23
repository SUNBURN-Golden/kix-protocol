mod common;

use common::{closure, ctx, engine, human, id, observation, open_unknown, reserve, terminate_for};
use kix_kernel_v5::{
    ActorKind, AppliedTermination, Condition, Context, ExecutionFence, KernelError,
    ObservationOutcome, OrderState, ReserveOutcome,
};
use kix_types::Hash32;

fn unchanged(kernel: &kix_kernel_v5::Kernel, before: &kix_kernel_v5::Kernel) {
    assert_eq!(kernel, before);
}

#[test]
fn condition_indexes_are_c1_through_c5() {
    for (index, condition) in Condition::ALL.into_iter().enumerate() {
        assert_eq!(condition.index(), index);
    }
}

#[test]
fn termination_records_once_and_blocks_only_the_next_send() {
    let mut kernel = engine();
    let request = open_unknown(&mut kernel);
    let remaining = kernel.remaining();
    let reserved = kernel.reserved_observation_count();
    let decision = terminate_for(&kernel, 10, 3);
    let applied = kernel.terminate(ctx(3), decision).unwrap();
    assert!(!applied.replayed);
    assert_eq!(applied.original.applied_at_ms, 3);
    assert_eq!(applied.original.request, decision);
    assert_eq!(kernel.termination(id(3)), Some(&applied.original));
    let order = kernel.order(id(3)).unwrap();
    assert_eq!(order.state, OrderState::PaymentUnknown);
    assert_eq!(order.captured, None);
    assert!(!order.review_required);
    assert!(order.inventory_owned);
    assert_eq!(kernel.remaining(), remaining);
    assert_eq!(kernel.reserved_observation_count(), reserved);
    assert_eq!(kernel.observation_count(), 0);
    assert!(kernel.conflicts().is_empty());
    let before = kernel.clone();
    assert_eq!(
        kernel.mark_payment_unknown(ctx(4), id(3)),
        Err(KernelError::InvalidTransition)
    );
    unchanged(&kernel, &before);
    assert_eq!(
        kernel.reserve(ctx(4), request).unwrap().original,
        ReserveOutcome::Held(id(3))
    );
}

#[test]
fn replay_returns_the_original_record_and_does_not_change_state() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let decision = terminate_for(&kernel, 10, 3);
    let applied = kernel.terminate(ctx(3), decision).unwrap();
    let before = kernel.clone();
    let replay = kernel
        .terminate(
            Context {
                fence: ExecutionFence {
                    owner: id(8),
                    generation: 1,
                },
                now_ms: 1,
                semantics_version: kix_kernel_v5::SEMANTICS_VERSION,
            },
            decision,
        )
        .unwrap();
    assert!(replay.replayed);
    assert_eq!(replay.original, applied.original);
    unchanged(&kernel, &before);
}

#[test]
fn same_decision_with_a_different_payload_conflicts() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let decision = terminate_for(&kernel, 10, 3);
    kernel.terminate(ctx(3), decision).unwrap();
    let mut changed = decision;
    changed.rule_hash = Hash32::from_bytes([7; 32]);
    changed.authority.actor = ActorKind::Automatic;
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(4), changed),
        Err(KernelError::CommandConflict)
    );
    unchanged(&kernel, &before);
}

#[test]
fn a_second_decision_on_the_same_operation_is_already_terminated() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    let mut second = terminate_for(&kernel, 11, 3);
    second.evaluation = closure([false; 5]);
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(4), second),
        Err(KernelError::AlreadyTerminated)
    );
    unchanged(&kernel, &before);
}

#[test]
fn automatic_approval_is_rejected_before_order_checks() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let mut decision = terminate_for(&kernel, 10, 3);
    decision.authority.actor = ActorKind::Automatic;
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(3), decision),
        Err(KernelError::AutomaticApprovalDisabled)
    );
    unchanged(&kernel, &before);
    let mut unknown = decision;
    unknown.decision_id = id(12);
    unknown.order_id = id(99);
    assert_eq!(
        kernel.terminate(ctx(3), unknown),
        Err(KernelError::AutomaticApprovalDisabled)
    );
    unchanged(&kernel, &before);
    assert_eq!(decision.authority.actor, ActorKind::Automatic);
    assert_eq!(human(40).actor, ActorKind::Human);
}

#[test]
fn each_false_condition_is_rejected_and_stores_nothing() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    for index in 0..5 {
        let mut holds = [true; 5];
        holds[index] = false;
        let mut decision = terminate_for(&kernel, 10, 3);
        decision.evaluation = closure(holds);
        let before = kernel.clone();
        assert_eq!(
            kernel.terminate(ctx(3), decision),
            Err(KernelError::ConditionNotSatisfied)
        );
        unchanged(&kernel, &before);
    }
    let applied = kernel
        .terminate(ctx(3), terminate_for(&kernel, 10, 3))
        .unwrap();
    assert!(!applied.replayed);
}

#[test]
fn a_false_condition_wins_over_a_stale_snapshot() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let mut decision = terminate_for(&kernel, 10, 3);
    let other = reserve(4, 2, 1);
    kernel.reserve(ctx(3), other.clone()).unwrap();
    kernel
        .observe_capture(ctx(4), observation(&other, 1))
        .unwrap();
    decision.evaluation = closure([true, true, true, true, false]);
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(5), decision),
        Err(KernelError::ConditionNotSatisfied)
    );
    unchanged(&kernel, &before);
}

#[test]
fn stale_snapshot_after_a_new_observation_or_conflict_is_rejected() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let stale = terminate_for(&kernel, 10, 3);
    let other = reserve(4, 2, 1);
    kernel.reserve(ctx(3), other.clone()).unwrap();
    kernel
        .observe_capture(ctx(4), observation(&other, 1))
        .unwrap();
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(5), stale),
        Err(KernelError::StaleEvaluation)
    );
    unchanged(&kernel, &before);
    let applied = kernel
        .terminate(ctx(5), terminate_for(&kernel, 10, 3))
        .unwrap();
    assert!(!applied.replayed);
    assert_eq!(applied.original.request.evaluated.observations, 1);

    let mut kernel = engine();
    open_unknown(&mut kernel);
    let stale = terminate_for(&kernel, 10, 3);
    let bound = reserve(4, 2, 1);
    kernel.reserve(ctx(3), bound.clone()).unwrap();
    kernel
        .observe_capture(ctx(4), observation(&bound, 1))
        .unwrap();
    assert_eq!(
        kernel.observe_capture(ctx(5), observation(&reserve(5, 3, 1), 1)),
        Ok(ObservationOutcome::Conflict)
    );
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(6), stale),
        Err(KernelError::StaleEvaluation)
    );
    unchanged(&kernel, &before);
    assert!(!kernel.order(id(3)).unwrap().review_required);
    let applied = kernel
        .terminate(ctx(6), terminate_for(&kernel, 10, 3))
        .unwrap();
    assert_eq!(applied.original.request.evaluated.retained_conflicts, 1);
}

#[test]
fn known_capture_return_required_and_review_are_rejected() {
    let mut kernel = engine();
    let request = reserve(3, 1, 1);
    kernel.reserve(ctx(1), request.clone()).unwrap();
    kernel
        .observe_capture(ctx(2), observation(&request, 1))
        .unwrap();
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(3), terminate_for(&kernel, 10, 3)),
        Err(KernelError::InvalidTransition)
    );
    unchanged(&kernel, &before);
    assert_eq!(
        kernel.order(id(3)).unwrap().state,
        OrderState::PaymentConfirmed
    );

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
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(5), terminate_for(&kernel, 10, 3)),
        Err(KernelError::InvalidTransition)
    );
    unchanged(&kernel, &before);
    assert_eq!(
        kernel.order(id(3)).unwrap().state,
        OrderState::ReturnRequired
    );

    let mut kernel = engine();
    open_unknown(&mut kernel);
    let bound = reserve(4, 2, 1);
    kernel.reserve(ctx(3), bound.clone()).unwrap();
    kernel
        .observe_capture(ctx(4), observation(&bound, 1))
        .unwrap();
    assert_eq!(
        kernel.observe_capture(ctx(5), observation(&request, 1)),
        Ok(ObservationOutcome::Conflict)
    );
    assert!(kernel.order(id(3)).unwrap().review_required);
    assert_eq!(kernel.order(id(3)).unwrap().captured, None);
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(6), terminate_for(&kernel, 10, 3)),
        Err(KernelError::InvalidTransition)
    );
    unchanged(&kernel, &before);
}

#[test]
fn held_without_a_reserved_slot_is_not_an_absence_close() {
    let mut kernel = engine();
    kernel.reserve(ctx(1), reserve(3, 1, 1)).unwrap();
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(ctx(2), terminate_for(&kernel, 10, 3)),
        Err(KernelError::InvalidTransition)
    );
    unchanged(&kernel, &before);
    assert_eq!(kernel.reserved_observation_count(), 0);
}

#[test]
fn late_capture_keeps_the_termination_and_the_original_reserve_result() {
    let mut kernel = engine();
    let request = open_unknown(&mut kernel);
    let decision = terminate_for(&kernel, 10, 3);
    let applied = kernel.terminate(ctx(3), decision).unwrap();
    assert_eq!(kernel.remaining(), 79);
    assert_eq!(
        kernel
            .observe_capture(ctx(100), observation(&request, 1))
            .unwrap(),
        ObservationOutcome::ReturnRequired
    );
    assert_eq!(kernel.termination(id(3)), Some(&applied.original));
    assert_eq!(applied.original.request.evaluated.captured, None);
    assert_eq!(kernel.order(id(3)).unwrap().captured, Some(request.amount));
    assert_eq!(kernel.observation_count(), 1);
    assert_eq!(kernel.remaining(), 80);
    let replay = kernel.reserve(ctx(101), request).unwrap();
    assert!(replay.replayed);
    assert_eq!(replay.original, ReserveOutcome::Held(id(3)));
    assert_eq!(
        kernel.terminate(ctx(102), decision),
        Ok(AppliedTermination {
            original: applied.original,
            replayed: true,
        })
    );
}

#[test]
fn failed_termination_does_not_change_state() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    let before = kernel.clone();
    assert_eq!(
        kernel.terminate(
            Context {
                semantics_version: 4,
                ..ctx(3)
            },
            terminate_for(&kernel, 10, 3)
        ),
        Err(KernelError::UnsupportedSemantics)
    );
    assert_eq!(
        kernel.terminate(
            Context {
                fence: ExecutionFence {
                    owner: id(8),
                    generation: 2,
                },
                ..ctx(3)
            },
            terminate_for(&kernel, 10, 3)
        ),
        Err(KernelError::ExecutionFenced)
    );
    assert_eq!(
        kernel.terminate(ctx(1), terminate_for(&kernel, 10, 3)),
        Err(KernelError::ClockRegression)
    );
    let mut missing = terminate_for(&kernel, 10, 3);
    missing.order_id = id(99);
    assert_eq!(
        kernel.terminate(ctx(3), missing),
        Err(KernelError::UnknownOrder)
    );
    unchanged(&kernel, &before);
    assert!(kernel.termination(id(3)).is_none());
}
