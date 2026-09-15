#!/usr/bin/env python3
"""KTX architecture v5 declaration/dependency gate, not a performance proof.

Behavior is exercised by cargo tests. Actual durability, fault histories and
performance are future gates, explicitly NOT certified by this script.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
FORBIDDEN_NAMES = {"requirements.txt", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def expected(actual: dict, values: dict, label: str) -> None:
    for key, value in values.items():
        require(actual.get(key) == value, f"{label}_CHANGED:{key}")


def main() -> int:
    data = tomllib.loads((ROOT / "runtime/ARCHITECTURE.toml").read_text())
    expected(data, {
        "version": "kix-runtime-architecture:5",
        "stage": "KTX-R0-R1-transition-kernel",
        "authority_adr": "docs/adr/0001-ktx-authority-commit-recovery.md",
        "masterplan": "docs/PROTOCOL_MASTERPLAN_V24.md",
        "legacy_reference_root": "reference/v0.3-rc1",
        "legacy_reference_role": "historical-regression-fixture-only",
        "production_runtime_root": "runtime", "production_language": "rust",
        "deployment_model": "regional-cells-modular-monolith", "async_runtime": "tokio",
        "internal_transport": "in-process-typed-calls", "oltp_database": "postgresql",
        "oltp_major": 18, "oltp_minor_policy": "latest-supported-minor",
        "database_role": "projection-control-or-isolated-comparison-authority",
        "database_driver_profile": "direct-prepared-binary-no-orm",
        "production_canonical_profile": "KIX-BCS1", "legacy_canonical_profile": "CE1",
        "legacy_commerce_schema": "kix:commerce:2",
    }, "RUNTIME")
    expected(data["execution"], {
        "primary_target": "replicated-ktx", "implemented": "io-free-single-shard-transition-kernel",
        "production_enabled": False, "durable_driver_implemented": False,
        "consensus_candidate": "raft-rs", "authority": "scope-assigned-single-writer",
        "profiles": ["DelegatedExecution", "NativeChainExecution"],
        "delegated_execution_enabled": False, "exclusive_grant_required": True,
        "same_resource_dual_write": False, "command_identity": "stable-scope-principal-command-id",
        "execution_fence_in_command_identity": False,
        "payload_comparison": "immutable-typed-payload-separate-from-key",
        "old_bound_observations_preserved": True, "unknown_is_failure": False,
        "cancellation_barrier_binds_placement": True, "replay_semantics_version_required": True,
    }, "EXECUTION")
    expected(data["durability"], {
        "ack_contract": "stable-quorum-commit-and-recoverable-result",
        "in_memory_apply_is_durable_ack": False, "result_and_intent_in_same_commit": True,
        "dedupe_moves_with_inventory": True, "snapshot_log_replay_required": True,
        "whole_region_rpo_zero_claimed": False, "actual_crash_history_required": True,
        "performance_claim_from_unit_tests": False,
    }, "DURABILITY")
    for key in (
        "python", "node", "sqlite", "dataframe_engine", "giant_json_state",
        "external_call_inside_db_transaction", "microservice_hop_required",
        "global_application_sequence", "global_balance_row", "dynamic_policy_parsing_per_request",
        "legacy_reference_is_design_authority",
    ):
        require(data["hot_path"].get(key) is False, f"HOT_PATH_CHANGED:{key}")
    expected(data["wire"], {
        "internal_canonical_encoding": "bcs", "framing": "versioned-domain-separated-kix-bcs1",
        "json_is_signing_identity": False, "bcs_schema_registry_required": True,
        "cross_language_golden_vectors_required": True,
    }, "WIRE")
    expected(data["money"], {
        "protocol_atoms": "u128", "fast_lane_profile_key": "asset-id-plus-registry-version",
        "fast_lane_guard": "atoms<=executionMaxAtoms(registryVersion)<=i64::MAX",
        "wide128_feature_arithmetic": "unsupported-fail-closed", "float": False,
        "out_of_profile_behavior": "reject-never-truncate",
    }, "MONEY")
    expected(data["chain"], {
        "production_transport": "sui-grpc", "production_topology": "independent-object-sharded-v1",
        "show_wide_mutable_hot_object": False, "show_wide_compensation_fence": False,
        "per_sale_terminal_fence_required": True, "reservation_is_chain_finality": False,
    }, "CHAIN")
    expected(data["inventory"], {
        "reserved_seating": "one-seat-one-contention-cell-no-general-shard",
        "general_admission": "fixed-capacity-shards",
        "offchain_owner": "logical-row-or-actual-contiguous-segment",
        "queue_position_preserved_on_reshard": True, "reshard_changes_queue_rank": False,
        "capacity_authority": "explicit-execution-profile", "row_equals_replication_group": False,
        "waiting_room_role": "admission-control-and-ga-shard-router-not-authority",
    }, "INVENTORY")
    expected(data["export"], {
        "economic_authority": "scope-assigned-single-writer", "consumer_truth": False,
        "full_export_consistency": "source-consistent-cut-plus-projection-watermarks",
        "projection_full_consistency": "repeatable-read-mvcc-snapshot",
        "incremental_cursor": "source-shard-commit-and-projection-cursor",
        "projection_lsn_is_source_commit": False, "snapshot_and_lsn_are_distinct": True,
        "cross_shard_consistent_cut_required": True,
    }, "EXPORT")
    for key in ("row_count_required", "per_file_hash_required", "manifest_hash_required",
                "source_schema_version_required", "export_schema_version_required", "partial_export_fail_closed"):
        require(data["export"].get(key) is True, f"EXPORT_INTEGRITY_CHANGED:{key}")
    expected(data["analytics"], {
        "economic_authority": "scope-assigned-single-writer", "online_transaction_dependency": False,
        "audit_engine": "duckdb", "audit_source": "authenticated-export-only",
        "feature_ir": "kix-feature-ir-v1", "feature_semantics": "kix-feature-semantics-v1",
        "reference_semantics": "pure-rust", "cpu_dataframe_engine": "polars-rust-lazy-streaming",
        "gpu_production_engine": "libcudf-native",
        "cudf_polars_role": "drafting-aid-conformance-benchmark-crossover-proxy",
        "polars_conformance_required": True,
        "pandas_runtime_dependency": False, "duckdb_is_oltp_authority": False,
        "polars_is_oltp_authority": False, "cudf_is_oltp_authority": False,
    }, "ANALYTICS")
    expected(data["feature_semantics"], {
        "divide_by_zero": "null", "f64_mode": "terminal-only-finite",
        "f64_join_key": False, "f64_group_key": False, "f64_sort_key": False,
        "nan_or_inf": "bug-fail-closed",
        "category_conformance": "decoded-logical-values-not-dictionary-index",
    }, "SEMANTICS")
    gpu = {
        "python_required": False, "bridge": "c-abi-arrow-c-device",
        "execution_model": "persistent-native-worker-per-gpu", "planner": "kix-feature-ir-v1",
        "semantics": "kix-feature-semantics-v1", "engine": "libcudf", "memory_resource": "rmm",
        "stream_aware": True, "same_process_zero_copy_preferred": True,
        "arrow_device_array_required": True, "fallback_to_python": False,
        "cudf_polars_conformance_required": True,
    }
    require(data["gpu_native"] == gpu, "NATIVE_GPU_CONTRACT_CHANGED")
    expected(data["gpu_crossover"], {
        "single_global_threshold": False, "measurement_proxy": "cudf-polars-raise-on-fail",
        "native_enable_gate": "gpu-wins-three-consecutive-scales-with-zero-fallback",
    }, "GPU_CROSSOVER")
    expected(data["ai_data_plane"], {
        "primary_feature_ir": "kix-feature-ir-v1", "feature_semantics": "kix-feature-semantics-v1",
        "cpu_feature_backend": "polars-rust", "gpu_feature_backend": "libcudf-native",
        "sql_audit_backend": "duckdb", "model_output_is_authority": False,
        "model_output_requires_kernel_validation": True, "core_availability_depends_on_gpu": False,
    }, "AI")

    for path in (ROOT / "runtime").rglob("*"):
        if "target" in path.relative_to(ROOT / "runtime").parts:
            continue  # build artifacts are not runtime source dependencies
        if path.is_file():
            require(path.suffix.lower() not in FORBIDDEN_SUFFIXES and path.name not in FORBIDDEN_NAMES,
                    f"FORBIDDEN_RUNTIME_SOURCE:{path.relative_to(ROOT)}")
    required = [
        data["authority_adr"], data["masterplan"], "runtime/Cargo.lock",
        "runtime/CANONICAL_BINARY_BCS_V1.md", "runtime/MOVE_PRODUCTION_TOPOLOGY.md",
        "runtime/AI_GPU_DATA_PLANE.md", "runtime/NATIVE_GPU_EXECUTION.md",
        "runtime/FEATURE_SEMANTICS_V1.md", "runtime/AUTHENTICATED_EXPORT.md",
        "runtime/ONSALE_ADMISSION_CONTROL.md", "runtime/native_gpu/include/kix_gpu.h",
        "runtime/crates/kix-bcs1/tests/golden_vectors.rs",
        "runtime/crates/kix-kernel/tests/transitions.rs", "docs/PROTOCOL_MASTERPLAN_V23.md",
    ]
    cargo = tomllib.loads((ROOT / "runtime/Cargo.toml").read_text())
    for crate in ("kix-types", "kix-bcs1", "kix-feature-ir", "kix-feature-semantics", "kix-kernel"):
        required.append(f"runtime/crates/{crate}/src/lib.rs")
        require(f"crates/{crate}" in cargo["workspace"]["members"], f"CRATE_NOT_IN_WORKSPACE:{crate}")
    for rel in required:
        require((ROOT / rel).is_file(), f"REQUIRED_ARCHITECTURE_FILE_MISSING:{rel}")

    # Actual declared dependency edge, not a prose statement. R1 must stay I/O-free.
    kernel = tomllib.loads((ROOT / "runtime/crates/kix-kernel/Cargo.toml").read_text())
    require(kernel.get("dependencies") == {"kix-types": {"path": "../kix-types"}}, "KERNEL_DEPENDENCY_DRIFT")
    types = tomllib.loads((ROOT / "runtime/crates/kix-types/Cargo.toml").read_text())
    require(not types.get("dependencies"), "KERNEL_TRANSITIVE_DEPENDENCY_DRIFT")
    print("architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
