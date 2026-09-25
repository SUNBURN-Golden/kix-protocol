#![allow(clippy::disallowed_methods)] // Separate measurement harness; no kernel source change.
#[path = "../tests/support/perf_probe.rs"]
mod probe;

use std::path::{Path, PathBuf};
use std::process::Command;

const LOCKED_KERNEL: &str = "69564b166f0c27f9af5d8422f0a466b18d74c20f";
const LOCKED_QUARANTINE: &str = "b607996c83a119c349f1cc90469ac1ba82764e20";
const LOCKED_EDGE: &str = "d37ea7df55423c83bedee16bf12bdc8dd61f7cae";
const LOCKED_MODEL: &str = "f020860b86933bf7511befccdb833b0c532b3629";

const OUTPUT_FILES: &[&str] = &[
    "uniform.csv",
    "uniform.json",
    "hot-seat.csv",
    "hot-seat.json",
    "same-command-retry.csv",
    "same-command-retry.json",
    "retained-conflict-growth.csv",
    "retained-conflict-growth.json",
    "low-load-uniform.csv",
    "low-load-uniform.json",
    "binding.json",
];

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 5 {
        return Err(
            "usage: r1_perf_probe <output-dir> <samples:1..100000> <command-limit> <rate:0=service-only>"
                .into(),
        );
    }
    let directory = PathBuf::from(&args[1]);
    let count: usize = args[2].parse()?;
    let limit: usize = args[3].parse()?;
    let rate: u64 = args[4].parse()?;
    if count == 0 || count > 100_000 || limit < 2 {
        return Err("invalid sample count or command limit".into());
    }
    let repo = repo_root()?;
    let kernel_blob = git_line(
        &repo,
        &["hash-object", "--", "runtime/crates/kix-kernel/src/lib.rs"],
    )?;
    let quarantine_blob = git_line(
        &repo,
        &[
            "hash-object",
            "--",
            "runtime/crates/kix-kernel/tests/quarantine_capacity.rs",
        ],
    )?;
    let edge_blob = git_line(
        &repo,
        &[
            "hash-object",
            "--",
            "runtime/crates/kix-kernel/tests/contract_edge_cases.rs",
        ],
    )?;
    let model_blob = git_line(
        &repo,
        &[
            "hash-object",
            "--",
            "runtime/crates/kix-kernel/tests/support/model_v4.rs",
        ],
    )?;
    if kernel_blob != LOCKED_KERNEL
        || quarantine_blob != LOCKED_QUARANTINE
        || edge_blob != LOCKED_EDGE
        || model_blob != LOCKED_MODEL
    {
        return Err("frozen blob mismatch; refusing to write unbound performance evidence".into());
    }
    let mut reports = Vec::with_capacity(4);
    for workload in [
        probe::Workload::Uniform,
        probe::Workload::HotSeat,
        probe::Workload::Retry,
        probe::Workload::Conflict,
    ] {
        reports.push(probe::run(workload, count, limit, rate));
    }
    let low_count = probe::low_load_sample_count(limit);
    let low = probe::run(probe::Workload::Uniform, low_count, limit, rate);
    if !low.low_load() {
        return Err(
            "low-load uniform control saturated or rejected; no evidence directory was written"
                .into(),
        );
    }
    std::fs::create_dir_all(&directory)?;
    for report in reports {
        write_workload(&directory, report, rate, limit)?;
    }
    std::fs::write(directory.join("low-load-uniform.csv"), &low.raw_csv)?;
    let low_json = low.json(rate, limit);
    std::fs::write(directory.join("low-load-uniform.json"), &low_json)?;
    println!("{low_json}");
    write_binding(
        &directory,
        &repo,
        &FrozenBlobs {
            kernel: &kernel_blob,
            quarantine: &quarantine_blob,
            edge: &edge_blob,
            model: &model_blob,
        },
        ProbeArgs {
            samples: count,
            low_load_samples: low_count,
            command_limit: limit,
            rate,
        },
    )?;
    Ok(())
}

struct FrozenBlobs<'a> {
    kernel: &'a str,
    quarantine: &'a str,
    edge: &'a str,
    model: &'a str,
}

struct ProbeArgs {
    samples: usize,
    low_load_samples: usize,
    command_limit: usize,
    rate: u64,
}

fn write_binding(
    directory: &Path,
    repo: &Path,
    blobs: &FrozenBlobs<'_>,
    args: ProbeArgs,
) -> Result<(), Box<dyn std::error::Error>> {
    let commit = git_line(repo, &["rev-parse", "HEAD"])?;
    let tree = git_line(repo, &["rev-parse", "HEAD^{tree}"])?;
    let probe_blob = git_line(
        repo,
        &[
            "hash-object",
            "--",
            "runtime/crates/kix-kernel/tests/support/perf_probe.rs",
        ],
    )?;
    let harness_blob = git_line(
        repo,
        &[
            "hash-object",
            "--",
            "runtime/crates/kix-kernel/tests/performance_harness.rs",
        ],
    )?;
    let example_blob = git_line(
        repo,
        &[
            "hash-object",
            "--",
            "runtime/crates/kix-kernel/examples/r1_perf_probe.rs",
        ],
    )?;
    let toolchain = command_stdout("rustc", &["--version"])?;
    let host_uname = command_stdout("uname", &["-srvm"]).ok();
    let binding = probe::evidence_binding_json(&probe::EvidenceBinding {
        commit: Some(&commit),
        tree: Some(&tree),
        kernel_blob: blobs.kernel,
        quarantine_blob: blobs.quarantine,
        contract_edge_blob: blobs.edge,
        model_v4_blob: blobs.model,
        probe_blob: Some(&probe_blob),
        harness_blob: Some(&harness_blob),
        example_blob: Some(&example_blob),
        toolchain: &toolchain,
        host_uname: host_uname.as_deref(),
        os: std::env::consts::OS,
        arch: std::env::consts::ARCH,
        build_mode: probe::build_mode(),
        debug_assertions: cfg!(debug_assertions),
        samples: args.samples,
        low_load_samples: args.low_load_samples,
        command_limit: args.command_limit,
        rate: args.rate,
        output_files: OUTPUT_FILES,
    });
    std::fs::write(directory.join("binding.json"), &binding)?;
    println!("{binding}");
    Ok(())
}

fn write_workload(
    directory: &Path,
    report: probe::Report,
    rate: u64,
    limit: usize,
) -> Result<(), Box<dyn std::error::Error>> {
    std::fs::write(
        directory.join(format!("{}.csv", report.workload)),
        &report.raw_csv,
    )?;
    let json = report.json(rate, limit);
    std::fs::write(directory.join(format!("{}.json", report.workload)), &json)?;
    println!("{json}");
    Ok(())
}

fn repo_root() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    let root = root.canonicalize()?;
    Ok(root)
}

fn git_line(repo: &Path, args: &[&str]) -> Result<String, Box<dyn std::error::Error>> {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo)
        .args(args)
        .output()?;
    if !output.status.success() {
        return Err(format!(
            "git {args:?} failed: {}",
            String::from_utf8_lossy(&output.stderr)
        )
        .into());
    }
    Ok(String::from_utf8(output.stdout)?.trim().to_string())
}

fn command_stdout(program: &str, args: &[&str]) -> Result<String, Box<dyn std::error::Error>> {
    let output = Command::new(program).args(args).output()?;
    if !output.status.success() {
        return Err(format!("{program} {args:?} failed").into());
    }
    Ok(String::from_utf8(output.stdout)?.trim().to_string())
}
