//! Source-informed external consumer checks for Feature Semantics v1 §§6 and 10.
//! No cached rlibs,
//! implementation modules inside consumers, third-party harness or passing skips.

use std::env;
use std::ffi::OsString;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

struct Scratch(PathBuf);

impl Scratch {
    fn new() -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path =
            env::temp_dir().join(format!("kix-api-boundaries-{}-{nonce}", std::process::id()));
        fs::create_dir(&path).expect("create fresh compilation directory");
        Self(path)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        // Remove only the directory this invocation successfully created.
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn run(command: &mut Command) -> Output {
    command
        .output()
        .unwrap_or_else(|error| panic!("cannot run {command:?}: {error}"))
}

fn require_success(output: Output, context: &str) {
    assert!(
        output.status.success(),
        "{context}: {}\n{}\n{}",
        output.status,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr),
    );
}

fn compiler(rustc: &OsString, out: &Path) -> Command {
    let mut command = Command::new(rustc);
    // A rustup shim must fail if its toolchain is missing, never provision it.
    command.env("RUSTUP_AUTO_INSTALL", "0");
    command.args([
        "--edition=2024",
        "--error-format=short",
        "--color=never",
        "--out-dir",
    ]);
    command
        .arg(out)
        .arg("-L")
        .arg(format!("dependency={}", out.display()));
    command
}

fn dependency(command: &mut Command, out: &Path, name: &str) {
    command.arg("--extern").arg(format!(
        "{name}={}",
        out.join(format!("lib{name}.rlib")).display()
    ));
}

fn compile_consumer(rustc: &OsString, out: &Path, source: &Path) -> Output {
    let mut command = compiler(rustc, out);
    command.arg("--emit=metadata").arg(source);
    dependency(&mut command, out, "kix_types");
    dependency(&mut command, out, "kix_feature_ir");
    run(&mut command)
}

fn require_rejection(output: Output, source: &Path, code: &str, fragments: &[&str]) {
    let stderr = String::from_utf8(output.stderr).expect("compiler diagnostics must be UTF-8");
    assert_eq!(
        output.status.code(),
        Some(1),
        "{}: {stderr}",
        source.display()
    );
    // Short diagnostics put each error on one line. Accept exactly the intended
    // error at this fixture, plus rustc's abort summary; reject every other error.
    let errors: Vec<_> = stderr
        .lines()
        .filter(|line| line.contains("error"))
        .collect();
    let diagnostics: Vec<_> = errors
        .iter()
        .copied()
        .filter(|line| !line.starts_with("error: aborting due to "))
        .collect();
    assert_eq!(diagnostics.len(), 1, "unexpected compiler errors: {stderr}");
    let diagnostic = diagnostics[0];
    assert!(
        diagnostic.starts_with(&format!("{}:", source.display())),
        "{stderr}"
    );
    assert!(
        diagnostic.contains(&format!(": error[{code}]:")),
        "{stderr}"
    );
    for fragment in fragments {
        assert!(
            diagnostic.contains(fragment),
            "missing {fragment:?}: {stderr}"
        );
    }
}

fn build_libraries(rustc: &OsString, out: &Path) {
    let crates = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
    // Build fresh, unchanged local libraries in dependency order, separately
    // from the consumer crates. Any compiler/toolchain failure fails this test.
    for (directory, name) in [
        ("kix-types", "kix_types"),
        ("kix-feature-semantics", "kix_feature_semantics"),
        ("kix-feature-ir", "kix_feature_ir"),
    ] {
        let mut command = compiler(rustc, out);
        command.args(["--crate-type=rlib", "--crate-name", name]);
        command.arg(crates.join(directory).join("src/lib.rs"));
        if name == "kix_feature_ir" {
            dependency(&mut command, out, "kix_types");
            dependency(&mut command, out, "kix_feature_semantics");
        }
        require_success(run(&mut command), name);
    }
}

#[test]
fn fast64_external_consumer_api_boundaries() {
    let fixtures = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/api_boundaries");
    let scratch = Scratch::new();
    let out = &scratch.0;
    let rustc = env::var_os("RUSTC").unwrap_or_else(|| "rustc".into());
    build_libraries(&rustc, out);

    // Same compiler and dependency setup for the valid and invalid consumers.
    require_success(
        compile_consumer(&rustc, out, &fixtures.join("checked_export.rs")),
        "checked construction, public accessors and AssetAmount export control",
    );
    for (fixture, code, fragments) in [
        (
            "private_construction.rs",
            "E0451",
            &[
                "key",
                "registry_hash",
                "execution_max_atoms",
                "Fast64MoneyProfile",
                "private",
            ][..],
        ),
        (
            "read_key.rs",
            "E0616",
            &["`key`", "Fast64MoneyProfile", "private"],
        ),
        (
            "overwrite_key.rs",
            "E0616",
            &["`key`", "Fast64MoneyProfile", "private"],
        ),
        (
            "read_registry_hash.rs",
            "E0616",
            &["`registry_hash`", "Fast64MoneyProfile", "private"],
        ),
        (
            "overwrite_registry_hash.rs",
            "E0616",
            &["`registry_hash`", "Fast64MoneyProfile", "private"],
        ),
        (
            "raw_u128_export.rs",
            "E0308",
            &["expected `AssetAmount`", "found `u128`"],
        ),
    ] {
        let source = fixtures.join(fixture);
        require_rejection(
            compile_consumer(&rustc, out, &source),
            &source,
            code,
            fragments,
        );
    }
}

#[test]
fn validated_plan_external_consumer_api_boundaries() {
    let fixtures = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/api_boundaries");
    let scratch = Scratch::new();
    let out = &scratch.0;
    let rustc = env::var_os("RUSTC").unwrap_or_else(|| "rustc".into());
    build_libraries(&rustc, out);

    for fixture in [
        "validated_accessors.rs",
        "validated_mutation_after_last_use.rs",
    ] {
        require_success(
            compile_consumer(&rustc, out, &fixtures.join(fixture)),
            fixture,
        );
    }
    for (fixture, code, fragments) in [
        (
            "validated_private_construction.rs",
            "E0451",
            &[
                "plan",
                "catalog",
                "output",
                "ValidatedFeaturePlan",
                "private",
            ][..],
        ),
        (
            "validated_plan_borrow.rs",
            "E0502",
            &["`candidate.stages`", "mutable", "immutable"],
        ),
        (
            "validated_catalog_borrow.rs",
            "E0502",
            &["`schemas`", "mutable", "immutable"],
        ),
        (
            "validated_plan_accessor_mutation.rs",
            "E0596",
            &["borrow", "mutable", "`&` reference"],
        ),
        (
            "validated_catalog_accessor_mutation.rs",
            "E0596",
            &["borrow", "mutable", "`&` reference"],
        ),
        (
            "validated_output_mutation.rs",
            "E0594",
            &["assign", "`&` reference"],
        ),
    ] {
        let source = fixtures.join(fixture);
        require_rejection(
            compile_consumer(&rustc, out, &source),
            &source,
            code,
            fragments,
        );
    }
}
