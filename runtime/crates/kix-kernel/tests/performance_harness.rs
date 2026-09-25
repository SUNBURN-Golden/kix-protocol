#![allow(clippy::disallowed_methods)] // Observation clocks and output I/O are outside the kernel.
#[path = "support/perf_probe.rs"]
mod probe;
use std::fs;
use std::path::PathBuf;

#[test]
fn memory_probe_reports_saturation_without_recreating_kernel() {
    let output = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../.local/verification/ktx");
    fs::create_dir_all(&output).unwrap();
    for workload in [
        probe::Workload::Uniform,
        probe::Workload::HotSeat,
        probe::Workload::Retry,
        probe::Workload::Conflict,
    ] {
        let report = probe::run(workload, 512, 128, 0);
        match workload {
            probe::Workload::Uniform => {
                assert_eq!(report.held, 128);
                assert_eq!(report.capacity, 384);
                assert_eq!(report.first_capacity, Some(128));
                assert_eq!(report.samples_after_first_capacity, 383);
                assert!(report.saturation());
                assert!(!report.low_load());
            }
            probe::Workload::HotSeat => {
                assert_eq!(report.held, 1);
                assert_eq!(report.rejected, 127);
                assert_eq!(report.capacity, 384);
                assert_eq!(report.conflict_retained, 0);
                assert!(report.hot_seat());
                assert!(!report.low_load());
                assert_eq!(report.samples_after_first_capacity, 383);
            }
            probe::Workload::Retry => {
                assert_eq!(report.held, 1);
                assert_eq!(report.replay, 511);
                assert_eq!(report.capacity, 0);
                assert!(report.same_command_retry());
                assert!(!report.low_load());
                assert!(!report.saturation());
                assert_eq!(report.samples_after_first_capacity, 0);
            }
            probe::Workload::Conflict => {
                assert_eq!(report.conflict_retained, 127);
                assert_eq!(report.other, 0);
                assert_eq!(report.capacity, 385);
                assert_eq!(report.first_capacity, Some(127));
                assert_eq!(report.samples_after_first_capacity, 384);
                assert!(report.history_growth());
                assert!(report.saturation());
            }
        }
        assert_separated(&report, 0, 128);
        fs::write(
            output.join(format!("perf-smoke-{}.csv", report.workload)),
            &report.raw_csv,
        )
        .unwrap();
        fs::write(
            output.join(format!("perf-smoke-{}.json", report.workload)),
            report.json(0, 128),
        )
        .unwrap();
    }
    let scheduled = probe::run(probe::Workload::HotSeat, 16, 128, 10_000);
    assert_eq!(scheduled.held, 1);
    assert_eq!(scheduled.rejected, 15);
    assert_eq!(scheduled.capacity, 0);
    assert!(scheduled.hot_seat());
    assert!(!scheduled.low_load());
    assert!(!scheduled.saturation());
    assert_eq!(scheduled.budget_phase(), "under-budget");
    let scheduled_json = scheduled.json(10_000, 128);
    assert!(scheduled_json.contains("fixed-origin i/rate schedule"));
    assert!(scheduled_json.contains(probe::SCHEDULED_LATENCY_NS_MEANING));
    assert!(scheduled_json.contains(probe::SERVICE_NS_MEANING));
    fs::write(
        output.join("perf-smoke-scheduled.csv"),
        scheduled.raw_csv.as_bytes(),
    )
    .unwrap();
    fs::write(output.join("perf-smoke-scheduled.json"), scheduled_json).unwrap();
}

#[test]
fn low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation() {
    assert_eq!(probe::low_load_sample_count(128), 32);
    assert_eq!(probe::low_load_sample_count(2), 1);
    let low = probe::run(probe::Workload::Uniform, 32, 128, 0);
    assert!(low.low_load());
    assert!(!low.hot_seat());
    assert!(!low.same_command_retry());
    assert!(!low.history_growth());
    assert!(!low.saturation());
    assert_eq!(low.budget_phase(), "under-budget");
    assert_eq!(low.held, 32);
    assert_eq!(low.rejected, 0);
    assert_eq!(low.replay, 0);
    assert_eq!(low.capacity, 0);
    assert_eq!(low.conflict_retained, 0);
    assert_eq!(low.samples_after_first_capacity, 0);
    let low_json = low.json(0, 128);
    assert!(low_json.contains("\"low_load\":true"));
    assert!(low_json.contains("\"hot_seat\":false"));
    assert!(low_json.contains("\"same_command_retry\":false"));
    assert!(low_json.contains("\"history_growth\":false"));
    assert!(low_json.contains("\"saturation\":false"));
    assert!(low_json.contains("service-time microbenchmark; not open-loop"));

    let hot_under_budget = probe::run(probe::Workload::HotSeat, 16, 128, 0);
    assert!(hot_under_budget.hot_seat());
    assert!(!hot_under_budget.low_load());
    assert!(!hot_under_budget.saturation());
    assert_eq!(hot_under_budget.held, 1);
    assert_eq!(hot_under_budget.rejected, 15);
    assert_eq!(hot_under_budget.capacity, 0);

    let retry = probe::run(probe::Workload::Retry, 16, 128, 0);
    assert!(retry.same_command_retry());
    assert!(!retry.low_load());
    assert!(!retry.saturation());
    assert_eq!(retry.held, 1);
    assert_eq!(retry.replay, 15);
    assert_eq!(retry.capacity, 0);

    let growth = probe::run(probe::Workload::Conflict, 8, 128, 0);
    assert!(growth.history_growth());
    assert!(!growth.saturation());
    assert!(!growth.low_load());
    assert_eq!(growth.conflict_retained, 8);
    assert_eq!(growth.capacity, 0);
    assert_eq!(growth.samples_after_first_capacity, 0);
    assert_eq!(growth.budget_phase(), "under-budget");
    assert_eq!(growth.outcome("conflict_retained").unwrap().count, 8);
    assert!(growth.outcome("held").unwrap().service_p99_ns.is_none());
}

#[test]
fn outcome_summaries_do_not_label_mixed_p99_as_success() {
    let hot = probe::run(probe::Workload::HotSeat, 512, 128, 0);
    assert_eq!(hot.outcome("held").unwrap().role, "new-success");
    assert_eq!(hot.outcome("held").unwrap().count, 1);
    assert_eq!(hot.outcome("business_rejected").unwrap().count, 127);
    assert_eq!(
        hot.outcome("business_rejected").unwrap().role,
        "business-reject"
    );
    assert_eq!(hot.outcome("capacity").unwrap().count, 384);
    assert_eq!(hot.outcome("replayed").unwrap().count, 0);
    assert_eq!(hot.outcome("conflict_retained").unwrap().count, 0);
    assert!(hot.outcome("held").unwrap().service_p99_ns.is_some());
    assert!(hot.outcome("replayed").unwrap().service_p99_ns.is_none());
    assert_eq!(
        hot.outcomes.iter().map(|item| item.count).sum::<usize>(),
        512
    );
    let json = hot.json(0, 128);
    assert!(json.contains("\"mixed_result_p99_service_ns\":"));
    assert!(json.contains("\"mixed_result_p99_scheduled_latency_ns\":"));
    assert!(json.contains(probe::MIXED_P99_INTERPRETATION));
    assert!(!json.contains("\"p99_service_ns\""));
    assert!(!json.contains("\"p99_scheduled_latency_ns\""));
    assert!(!json.contains("success_p99"));
    assert!(!json.contains("purchase_p99"));
    assert!(!json.contains("new_success_p99"));
    assert!(json.contains("\"new_success_count\":1"));
    assert!(json.contains(probe::GOODPUT_INTERPRETATION));
    let goodput = hot.memory_only_new_held_per_elapsed_s();
    assert!(goodput.is_some());
    assert!(json.contains(&format!(
        "\"memory_only_new_held_per_elapsed_s\":{}",
        goodput.unwrap()
    )));

    let low = probe::run(probe::Workload::Uniform, 32, 128, 0);
    let held_p99 = low.outcome("held").unwrap().service_p99_ns.unwrap();
    assert_eq!(low.mixed_p99_service_ns, held_p99);
    let low_json = low.json(0, 128);
    assert!(low_json.contains(probe::MIXED_P99_INTERPRETATION));
    assert!(low_json.contains("\"new_success_count\":32"));
    assert!(!low_json.contains("\"p99_service_ns\""));
}

#[test]
fn evidence_binding_records_budgets_toolchain_and_non_claims() {
    let files = ["uniform.csv", "binding.json"];
    let json = probe::evidence_binding_json(&probe::EvidenceBinding {
        commit: Some("729a106add049ad1a75b90f99c00b6e0ccb8a67d"),
        tree: Some("abc"),
        kernel_blob: "69564b166f0c27f9af5d8422f0a466b18d74c20f",
        quarantine_blob: "b607996c83a119c349f1cc90469ac1ba82764e20",
        contract_edge_blob: "d37ea7df55423c83bedee16bf12bdc8dd61f7cae",
        model_v4_blob: "f020860b86933bf7511befccdb833b0c532b3629",
        probe_blob: Some("probe"),
        harness_blob: None,
        example_blob: Some("example \"quote\""),
        toolchain: "rustc test",
        host_uname: Some("Linux test"),
        os: "linux",
        arch: "x86_64",
        build_mode: "release",
        debug_assertions: false,
        samples: 8192,
        low_load_samples: 32,
        command_limit: 4096,
        rate: 0,
        output_files: &files,
    });
    assert!(json.contains("69564b166f0c27f9af5d8422f0a466b18d74c20f"));
    assert!(json.contains("b607996c83a119c349f1cc90469ac1ba82764e20"));
    assert!(json.contains("d37ea7df55423c83bedee16bf12bdc8dd61f7cae"));
    assert!(json.contains("f020860b86933bf7511befccdb833b0c532b3629"));
    assert!(json.contains("\"commit\":\"729a106add049ad1a75b90f99c00b6e0ccb8a67d\""));
    assert!(json.contains("\"harness_blob\":null"));
    assert!(json.contains("example \\\"quote\\\""));
    assert!(json.contains("\"build_mode\":\"release\""));
    assert!(json.contains("\"debug_assertions\":false"));
    assert!(json.contains("\"samples\":8192"));
    assert!(json.contains("\"low_load_samples\":32"));
    assert!(json.contains("\"command_limit\":4096"));
    assert!(json.contains("\"orders_limit\":4096"));
    assert!(json.contains("\"observations_limit\":128"));
    assert!(json.contains("\"rate\":0"));
    assert!(json.contains("service-time microbenchmark; not open-loop"));
    assert!(json.contains("\"product_slo\":null"));
    assert!(json.contains(probe::NON_CLAIMS));
    assert!(json.contains("not a product performance result"));
    assert!(json.contains("\"kernel_resets_during_workload\":0"));
}

fn assert_separated(report: &probe::Report, rate: u64, command_limit: usize) {
    assert_eq!(
        report.held
            + report.replay
            + report.rejected
            + report.capacity
            + report.conflict_retained
            + report.other,
        report.total
    );
    assert_eq!(report.other, report.other_error + report.other_observation);
    assert_eq!(
        report.outcomes.iter().map(|item| item.count).sum::<usize>(),
        report.total
    );
    assert_eq!(report.outcome("held").unwrap().count, report.held);
    assert_eq!(report.outcome("replayed").unwrap().count, report.replay);
    assert_eq!(
        report.outcome("business_rejected").unwrap().count,
        report.rejected
    );
    assert_eq!(report.outcome("capacity").unwrap().count, report.capacity);
    assert_eq!(
        report.outcome("conflict_retained").unwrap().count,
        report.conflict_retained
    );
    let rows: Vec<&str> = report.raw_csv.lines().skip(1).collect();
    assert_eq!(rows.len(), report.total);
    assert!(report.raw_csv.starts_with(
        "index,scheduled_ns,start_ns,end_ns,service_ns,scheduled_latency_ns,outcome\n"
    ));
    if let Some(index) = report.first_capacity {
        assert_eq!(
            report.samples_after_first_capacity,
            report.total - index - 1
        );
        assert!(rows[index].ends_with(",capacity"));
        assert!(
            rows.iter()
                .skip(index + 1)
                .all(|row| row.ends_with(",capacity"))
        );
        assert_eq!(
            report.budget_phase(),
            "includes-samples-after-first-capacity"
        );
    }
    let json = report.json(rate, command_limit);
    assert!(json.contains("\"mixed_result_p99_service_ns\":"));
    assert!(json.contains(probe::MIXED_P99_INTERPRETATION));
    assert!(json.contains(probe::NON_CLAIMS));
    assert!(json.contains("\"kernel_resets_during_workload\":0"));
    assert!(!json.contains("\"p99_service_ns\""));
    assert!(!json.contains("success_p99"));
    assert!(!json.contains("purchase_p99"));
    let mode = probe::build_mode();
    assert!(json.contains(&format!("\"build_mode\":\"{mode}\"")));
    assert!(json.contains(&format!("\"target_os\":\"{}\"", std::env::consts::OS)));
    assert!(json.contains(&format!("\"target_arch\":\"{}\"", std::env::consts::ARCH)));
}
