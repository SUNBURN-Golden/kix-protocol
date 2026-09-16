#![allow(clippy::disallowed_methods)] // Separate measurement harness; no kernel source change.
#[path = "../tests/support/perf_probe.rs"]
mod probe;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 5 {
        return Err("usage: r1_perf_probe <output-dir> <samples:1..100000> <command-limit> <rate:0=service-only>".into());
    }
    let directory = std::path::Path::new(&args[1]);
    let count: usize = args[2].parse()?;
    let limit: usize = args[3].parse()?;
    let rate: u64 = args[4].parse()?;
    if count == 0 || count > 100_000 || limit < 2 {
        return Err("invalid sample count or command limit".into());
    }
    std::fs::create_dir_all(directory)?;
    for workload in [probe::Workload::Uniform, probe::Workload::HotSeat, probe::Workload::Retry, probe::Workload::Conflict] {
        let report = probe::run(workload, count, limit, rate);
        std::fs::write(directory.join(format!("{}.csv", report.workload)), &report.raw_csv)?;
        std::fs::write(directory.join(format!("{}.json", report.workload)), report.json(rate, limit))?;
        println!("{}", report.json(rate, limit));
    }
    Ok(())
}
