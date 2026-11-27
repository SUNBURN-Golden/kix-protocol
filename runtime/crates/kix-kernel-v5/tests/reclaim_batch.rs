#![allow(clippy::disallowed_methods)] // The SLO probe reads a wall clock outside the kernel.

mod common;

use std::time::Instant;

use common::{
    amount, closure, ctx, engine, fence, human, id, observation, open_unknown, reserve,
    terminate_for,
};
use kix_kernel_v5::{
    Blocker, DAY_MS, Inventory, Kernel, KernelError, Limits, ObservationOutcome, ProviderOperation,
    REPORT_SLO_MS, REPORT_SLO_RECORDS, ReclaimPolicy, Reserve, Selection, Terminate,
};
use kix_types::{Hash32, KixId};

fn policy() -> ReclaimPolicy {
    ReclaimPolicy::default()
}

fn open_and_unknown(kernel: &mut Kernel, n: u8, now_ms: u64) {
    kernel
        .reserve(ctx(now_ms), reserve(n, u16::from(n), 1))
        .unwrap();
    kernel.mark_payment_unknown(ctx(now_ms), id(n)).unwrap();
}

#[test]
fn reports_cover_only_terminated_orders_sorted_by_time_then_order_id() {
    let mut kernel = engine();
    for (n, now_ms) in [(7, 1), (4, 2), (3, 3), (9, 4)] {
        open_and_unknown(&mut kernel, n, now_ms);
    }
    // Order 9 is never terminated. Orders 4 and 3 are terminated at the same
    // ordered time, 4 first, so the order_id tie-break is observable.
    kernel
        .terminate(ctx(7), terminate_for(&kernel, 10, 7))
        .unwrap();
    kernel
        .terminate(ctx(9), terminate_for(&kernel, 11, 4))
        .unwrap();
    kernel
        .terminate(ctx(9), terminate_for(&kernel, 12, 3))
        .unwrap();
    let before = kernel.clone();
    let batch = kernel.reclaim_reports(9, &policy()).unwrap();
    assert_eq!(kernel, before);
    assert_eq!(batch.now_ms, 9);
    assert_eq!(batch.terminated_records, 3);
    assert!(!batch.over_residency_cap);
    let seen: Vec<_> = batch
        .reports
        .iter()
        .map(|report| (report.terminated_at_ms.unwrap(), report.order_id))
        .collect();
    assert_eq!(seen, vec![(7, id(7)), (9, id(3)), (9, id(4))]);
    for report in &batch.reports {
        let single = kernel
            .reclaim_report(9, report.order_id, &policy())
            .unwrap();
        assert_eq!(report, &single);
        assert!(!report.blockers.contains(&Blocker::ActiveOp));
        assert_eq!(
            &report.blockers[report.blockers.len() - 3..],
            &[Blocker::I09, Blocker::I10, Blocker::I13]
        );
    }
    // A non-terminated order is still reportable one by one, with ActiveOp.
    assert!(
        kernel
            .reclaim_report(9, id(9), &policy())
            .unwrap()
            .blockers
            .contains(&Blocker::ActiveOp)
    );
}

#[test]
fn empty_kernel_gives_an_empty_batch() {
    let kernel = engine();
    let batch = kernel.reclaim_reports(0, &policy()).unwrap();
    assert!(batch.reports.is_empty());
    assert_eq!(batch.terminated_records, 0);
    assert!(!batch.over_residency_cap);
}

#[test]
fn residency_cap_is_a_count_of_terminated_records() {
    let mut kernel = engine();
    for (n, now_ms) in [(3, 1), (4, 2)] {
        open_and_unknown(&mut kernel, n, now_ms);
    }
    for (decision, n) in [(10, 3), (11, 4)] {
        kernel
            .terminate(ctx(5), terminate_for(&kernel, decision, n))
            .unwrap();
    }
    let at_cap = ReclaimPolicy {
        memory_residency_cap_records: 2,
        ..policy()
    };
    let below_cap = ReclaimPolicy {
        memory_residency_cap_records: 1,
        ..policy()
    };
    assert!(
        !kernel
            .reclaim_reports(5, &at_cap)
            .unwrap()
            .over_residency_cap
    );
    assert!(
        kernel
            .reclaim_reports(5, &below_cap)
            .unwrap()
            .over_residency_cap
    );
    // The cap flags the count only; every record stays and still blocks.
    assert_eq!(kernel.order_count(), 2);
    assert_eq!(
        kernel.reclaim_reports(5, &below_cap).unwrap().reports.len(),
        2
    );
}

#[test]
fn a_late_conflict_after_termination_is_reported_for_every_affected_order() {
    let mut kernel = engine();
    let request = open_unknown(&mut kernel);
    let bound = reserve(4, 2, 1);
    kernel.reserve(ctx(3), bound.clone()).unwrap();
    kernel.mark_payment_unknown(ctx(4), id(4)).unwrap();
    kernel
        .terminate(ctx(5), terminate_for(&kernel, 10, 3))
        .unwrap();
    kernel
        .observe_capture(ctx(6), observation(&bound, 1))
        .unwrap();
    // The same event id with another operation conflicts and quarantines both.
    assert_eq!(
        kernel.observe_capture(ctx(7), observation(&request, 1)),
        Ok(ObservationOutcome::Conflict)
    );
    let batch = kernel.reclaim_reports(7, &policy()).unwrap();
    assert_eq!(batch.reports.len(), 1);
    let report = &batch.reports[0];
    assert_eq!(report.order_id, id(3));
    assert!(report.blockers.contains(&Blocker::ReviewRequired));
    assert!(report.blockers.contains(&Blocker::UnboundFence));
    assert!(report.blockers.contains(&Blocker::Hold));
}

fn big_id(tag: u8, n: u32) -> KixId {
    let mut bytes = [tag; 16];
    bytes[..4].copy_from_slice(&n.to_be_bytes());
    KixId::from_bytes(bytes)
}

fn big_reserve(n: u32) -> Reserve {
    Reserve {
        id: kix_kernel_v5::CommandId {
            scope: id(9),
            principal: id(2),
            request: big_id(1, n),
        },
        order_id: big_id(2, n),
        expected_business_epoch: 1,
        selection: Selection::GeneralAdmission { count: 1 },
        amount: amount(10_000),
        quote_hash: Hash32::from_bytes([3; 32]),
        policy_hash: Hash32::from_bytes([4; 32]),
        expires_at_ms: DAY_MS,
        payment: ProviderOperation {
            provider: id(20),
            account: id(21),
            operation: big_id(3, n),
        },
    }
}

#[test]
fn ten_thousand_records_report_synchronously_in_order_within_the_slo() {
    let records = u32::try_from(REPORT_SLO_RECORDS).unwrap();
    let mut kernel = Kernel::new(
        id(9),
        fence(),
        1,
        Inventory::general_admission(records + 1).unwrap(),
        Limits {
            commands: REPORT_SLO_RECORDS + 1,
            orders: REPORT_SLO_RECORDS + 1,
            observations: REPORT_SLO_RECORDS + 1,
        },
    )
    .unwrap();
    for n in 0..records {
        kernel.reserve(ctx(1), big_reserve(n)).unwrap();
    }
    for n in 0..records {
        kernel.mark_payment_unknown(ctx(2), big_id(2, n)).unwrap();
    }
    // Terminate in descending order id at ascending times so the sort key is
    // visibly the time, and ties on time break by order id.
    for n in (0..records).rev() {
        let order_id = big_id(2, n);
        let request = Terminate {
            decision_id: big_id(4, n),
            order_id,
            evaluated: kernel.operation_snapshot(order_id).unwrap(),
            evaluation: closure([true; 5]),
            authority: human(40),
            rule_hash: Hash32::from_bytes([6; 32]),
        };
        let at = 10 + u64::from((records - 1 - n) / 100);
        kernel.terminate(ctx(at), request).unwrap();
    }
    let now_ms = 20 * DAY_MS;
    let started = Instant::now();
    let batch = kernel.reclaim_reports(now_ms, &policy()).unwrap();
    let elapsed = started.elapsed();
    eprintln!(
        "reclaim_reports: {} records in {elapsed:?} (SLO {REPORT_SLO_MS} ms, debug_assertions={})",
        batch.reports.len(),
        cfg!(debug_assertions)
    );
    assert_eq!(batch.reports.len(), REPORT_SLO_RECORDS);
    assert_eq!(batch.terminated_records, REPORT_SLO_RECORDS);
    assert!(!batch.over_residency_cap);
    assert!(
        batch
            .reports
            .windows(2)
            .all(|pair| (pair[0].terminated_at_ms, pair[0].order_id)
                < (pair[1].terminated_at_ms, pair[1].order_id))
    );
    assert!(batch.reports.iter().all(|report| {
        report.blockers
            == vec![
                Blocker::ReservedSlot,
                Blocker::I09,
                Blocker::I10,
                Blocker::I13,
            ]
    }));
    // The 50 ms target is an optimized-build figure. An unoptimized test build
    // does not assert it, so a loaded CI runner cannot turn it into a flake.
    if !cfg!(debug_assertions) {
        assert!(
            elapsed.as_millis() <= u128::from(REPORT_SLO_MS),
            "{elapsed:?} exceeds the {REPORT_SLO_MS} ms report SLO"
        );
    }
}

#[test]
fn a_regressed_batch_time_is_rejected() {
    let mut kernel = engine();
    open_unknown(&mut kernel);
    assert_eq!(
        kernel.reclaim_reports(1, &policy()),
        Err(KernelError::ClockRegression)
    );
}
