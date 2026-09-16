#![allow(clippy::disallowed_methods)] // Observation clocks and output I/O are outside the kernel.
#[path = "support/perf_probe.rs"]
mod probe;
use std::fs;
use std::path::PathBuf;

#[test]
fn memory_probe_reports_saturation_without_recreating_kernel() {
    let output = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../../.local/verification/ktx");
    fs::create_dir_all(&output).unwrap();
    for workload in [probe::Workload::Uniform, probe::Workload::HotSeat, probe::Workload::Retry, probe::Workload::Conflict] {
        let report = probe::run(workload, 512, 128, 0);
        match workload {
            probe::Workload::Uniform => {
                assert_eq!(report.held, 128);
                assert_eq!(report.capacity, 384);
            }
            probe::Workload::HotSeat => {
                assert_eq!(report.held, 1);
                assert_eq!(report.rejected, 127);
                assert_eq!(report.capacity, 384);
            }
            probe::Workload::Retry => {
                assert_eq!(report.held, 1);
                assert_eq!(report.replay, 511);
                assert_eq!(report.capacity, 0);
            }
            probe::Workload::Conflict => {
                assert_eq!(report.other, 127);
                assert_eq!(report.capacity, 385);
            }
        }
        fs::write(output.join(format!("perf-smoke-{}.csv", report.workload)), &report.raw_csv).unwrap();
        fs::write(output.join(format!("perf-smoke-{}.json", report.workload)), report.json(0, 128)).unwrap();
    }
    let scheduled = probe::run(probe::Workload::HotSeat, 16, 128, 10_000);
    fs::write(output.join("perf-smoke-scheduled.csv"), scheduled.raw_csv.as_bytes()).unwrap();
    fs::write(output.join("perf-smoke-scheduled.json"), scheduled.json(10_000, 128)).unwrap();
}
