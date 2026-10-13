#[test]
fn manifest_normal_dependency_is_only_kix_types() {
    let manifest = include_str!("../Cargo.toml");
    let dependencies = section(manifest, "[dependencies]");
    assert_eq!(dependency_names(dependencies), vec!["kix-types"]);
    assert!(!dependencies.contains("kix-kernel"));
    let dev = section(manifest, "[dev-dependencies]");
    assert_eq!(dependency_names(dev), vec!["kix-kernel"]);
    assert!(manifest.contains("name = \"kix-kernel-v5\""));
    assert!(manifest.contains("edition = \"2024\""));
    assert!(manifest.contains("publish = false"));
    assert!(!manifest.contains("[build-dependencies]"));
    assert!(!manifest.contains("[target."));
}

#[test]
fn clippy_boundary_is_the_v4_byte_copy() {
    let v5 = include_str!("../clippy.toml");
    let v4 = include_str!("../../kix-kernel/clippy.toml");
    assert_eq!(v5, v4);
    assert!(v5.contains("std::fs::read"));
    assert!(v5.contains("std::time::SystemTime::now"));
    assert!(v5.contains("std::collections::HashMap"));
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
