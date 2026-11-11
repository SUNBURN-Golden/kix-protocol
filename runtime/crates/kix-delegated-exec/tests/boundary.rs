#[test]
fn manifest_normal_dependencies_are_kix_types_and_kix_kernel_v5() {
    let manifest = include_str!("../Cargo.toml");
    let dependencies = section(manifest, "[dependencies]");
    assert_eq!(
        dependency_names(dependencies),
        vec!["kix-types", "kix-kernel-v5"]
    );
    // In particular the locked v4 kernel is not a dependency of this crate.
    assert!(!dependency_names(dependencies).contains(&"kix-kernel"));
    assert!(manifest.contains("name = \"kix-delegated-exec\""));
    assert!(manifest.contains("edition = \"2024\""));
    assert!(manifest.contains("publish = false"));
    assert!(!manifest.contains("[dev-dependencies]"));
    assert!(!manifest.contains("[build-dependencies]"));
    assert!(!manifest.contains("[target."));
}

#[test]
fn clippy_boundary_is_the_v4_byte_copy() {
    let this = include_str!("../clippy.toml");
    let v4 = include_str!("../../kix-kernel/clippy.toml");
    assert_eq!(this, v4);
    assert!(this.contains("std::fs::read"));
    assert!(this.contains("std::time::SystemTime::now"));
    assert!(this.contains("std::collections::HashMap"));
}

fn section<'a>(manifest: &'a str, header: &str) -> &'a str {
    let rest = manifest
        .split_once(header)
        .unwrap_or_else(|| panic!("missing {header}"))
        .1;
    let end = rest.find("\n[").unwrap_or(rest.len());
    &rest[..end]
}

fn dependency_names(section: &str) -> Vec<&str> {
    section
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .map(|line| line.split('=').next().unwrap().trim())
        .collect()
}
