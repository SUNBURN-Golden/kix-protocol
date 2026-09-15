#!/usr/bin/env python3
"""Fail closed if KIX production architecture drifts from the greenfield contract."""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "runtime" / "ARCHITECTURE.toml"
RUNTIME = ROOT / "runtime"

FORBIDDEN_SUFFIXES = {".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
FORBIDDEN_NAMES = {"requirements.txt", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def exact(section: dict, expected: dict, label: str) -> None:
    require(section == expected, f"{label}_CHANGED:{section!r}")


def main() -> int:
    require(CONTRACT.is_file(), "RUNTIME_ARCHITECTURE_CONTRACT_MISSING")
    data = tomllib.loads(CONTRACT.read_text())

    top = {
        "version": "kix-runtime-architecture:4",
        "stage": "S06.2-greenfield-semantic-audit-gate",
        "legacy_reference_root": "reference/v0.3-rc1",
        "legacy_reference_role": "historical-regression-fixture-only",
        "production_runtime_root": "runtime",
        "production_language": "rust",
        "deployment_model": "modular-monolith",
        "async_runtime": "tokio",
        "internal_transport": "in-process-typed-calls",
        "oltp_database": "postgresql",
        "oltp_major": 18,
        "oltp_minor_policy": "latest-supported-minor",
        "database_driver_profile": "direct-prepared-binary-no-orm",
        "production_canonical_profile": "KIX-BCS1",
        "legacy_canonical_profile": "CE1",
        "legacy_commerce_schema": "kix:commerce:2",
    }
    for key, value in top.items():
        require(data.get(key) == value, f"RUNTIME_ARCHITECTURE_CONTRACT_CHANGED:{key}")

    hot = data["hot_path"]
    for key in (
        "python", "node", "sqlite", "dataframe_engine", "giant_json_state",
        "external_call_inside_db_transaction", "microservice_hop_required",
        "global_application_sequence", "global_balance_row",
        "dynamic_policy_parsing_per_request", "legacy_reference_is_design_authority",
    ):
        require(hot.get(key) is False, f"HOT_PATH_ARCHITECTURE_CHANGED:{key}")

    wire = data["wire"]
    require(wire.get("internal_canonical_encoding") == "bcs", "BCS_REMOVED")
    require(wire.get("framing") == "versioned-domain-separated-kix-bcs1", "BCS_FRAMING_CHANGED")
    require(wire.get("json_is_signing_identity") is False, "JSON_SIGNING_REINTRODUCED")
    require(wire.get("bcs_schema_registry_required") is True, "BCS_SCHEMA_REGISTRY_DISABLED")
    require(wire.get("cross_language_golden_vectors_required") is True, "BCS_GOLDEN_VECTORS_DISABLED")

    money = data["money"]
    require(money.get("protocol_atoms") == "u128", "PROTOCOL_MONEY_CHANGED")
    require(money.get("fast_lane_profile_key") == "asset-id-plus-registry-version", "FAST64_KEY_CHANGED")
    require(
        money.get("fast_lane_guard") == "atoms<=executionMaxAtoms(registryVersion)<=i64::MAX",
        "FAST64_GUARD_CHANGED",
    )
    require(money.get("wide128_feature_arithmetic") == "unsupported-fail-closed", "WIDE_MONEY_ARITHMETIC_ENABLED")

    chain = data["chain"]
    require(chain.get("production_transport") == "sui-grpc", "CHAIN_TRANSPORT_CHANGED")
    require(chain.get("production_topology") == "independent-object-sharded-v1", "CHAIN_TOPOLOGY_CHANGED")
    require(chain.get("show_wide_mutable_hot_object") is False, "SHARED_SHOW_REINTRODUCED")
    require(chain.get("show_wide_compensation_fence") is False, "SHOW_WIDE_FENCE_REINTRODUCED")
    require(chain.get("per_sale_terminal_fence_required") is True, "PER_SALE_FENCE_DISABLED")

    inventory = data["inventory"]
    require(inventory.get("reserved_seating") == "one-seat-one-contention-cell-no-general-shard", "RESERVED_SEATING_TOPOLOGY_CHANGED")
    require(inventory.get("general_admission") == "fixed-capacity-shards", "GA_TOPOLOGY_CHANGED")
    require(inventory.get("queue_position_preserved_on_reshard") is True, "QUEUE_POSITION_REISSUE_POLICY_CHANGED")
    require(inventory.get("reshard_changes_queue_rank") is False, "QUEUE_POSITION_CAN_BE_LOST")
    require(inventory.get("chain_capacity_is_authority") is True, "WAITING_ROOM_BECAME_CAPACITY_AUTHORITY")

    export = data["export"]
    require(export.get("economic_authority") == "postgresql", "EXPORT_AUTHORITY_CHANGED")
    require(export.get("consumer_truth") is False, "EXPORT_BECAME_TRUTH")
    require(export.get("full_export_consistency") == "repeatable-read-mvcc-snapshot", "FULL_EXPORT_SNAPSHOT_CHANGED")
    require(export.get("incremental_cursor") == "wal-lsn-or-equivalent-durable-cursor", "CDC_CURSOR_CHANGED")
    require(export.get("snapshot_and_lsn_are_distinct") is True, "SNAPSHOT_LSN_CONFLATED")
    for key in (
        "row_count_required", "per_file_hash_required", "manifest_hash_required",
        "source_schema_version_required", "export_schema_version_required", "partial_export_fail_closed",
    ):
        require(export.get(key) is True, f"EXPORT_INTEGRITY_CHANGED:{key}")

    analytics = data["analytics"]
    require(analytics.get("economic_authority") == "postgresql", "ANALYTICS_AUTHORITY_CHANGED")
    require(analytics.get("audit_engine") == "duckdb", "DUCKDB_AUDIT_ROLE_CHANGED")
    require(analytics.get("audit_source") == "authenticated-export-only", "DUCKDB_UNAUTHENTICATED_SOURCE_ALLOWED")
    require(analytics.get("feature_ir") == "kix-feature-ir-v1", "FEATURE_IR_CHANGED")
    require(analytics.get("feature_semantics") == "kix-feature-semantics-v1", "FEATURE_SEMANTICS_CHANGED")
    require(analytics.get("reference_semantics") == "pure-rust", "UPSTREAM_BECAME_SEMANTIC_AUTHORITY")
    require(analytics.get("cpu_dataframe_engine") == "polars-rust-lazy-streaming", "CPU_FEATURE_ENGINE_CHANGED")
    require(analytics.get("gpu_production_engine") == "libcudf-native", "NATIVE_GPU_ENGINE_CHANGED")
    require(
        analytics.get("cudf_polars_role") == "drafting-aid-conformance-benchmark-crossover-proxy",
        "CUDF_POLARS_PROMOTED_TO_PRODUCTION",
    )
    require(analytics.get("polars_conformance_required") is True, "POLARS_CONFORMANCE_DISABLED")
    for key in ("pandas_runtime_dependency", "duckdb_is_oltp_authority", "polars_is_oltp_authority", "cudf_is_oltp_authority"):
        require(analytics.get(key) is False, f"ANALYTICS_AUTHORITY_DRIFT:{key}")

    semantics = data["feature_semantics"]
    require(semantics.get("divide_by_zero") == "null", "DIVIDE_BY_ZERO_SEMANTICS_CHANGED")
    require(semantics.get("f64_mode") == "terminal-only-finite", "F64_MODE_CHANGED")
    require(semantics.get("f64_join_key") is False, "F64_JOIN_KEY_ENABLED")
    require(semantics.get("f64_group_key") is False, "F64_GROUP_KEY_ENABLED")
    require(semantics.get("f64_sort_key") is False, "F64_SORT_KEY_ENABLED")
    require(semantics.get("nan_or_inf") == "bug-fail-closed", "NONFINITE_F64_ALLOWED")
    require(
        semantics.get("category_conformance") == "decoded-logical-values-not-dictionary-index",
        "CATEGORY_PHYSICAL_INDEX_BECAME_SEMANTICS",
    )

    gpu = data["gpu_native"]
    exact(gpu, {
        "python_required": False,
        "bridge": "c-abi-arrow-c-device",
        "execution_model": "persistent-native-worker-per-gpu",
        "planner": "kix-feature-ir-v1",
        "semantics": "kix-feature-semantics-v1",
        "engine": "libcudf",
        "memory_resource": "rmm",
        "stream_aware": True,
        "same_process_zero_copy_preferred": True,
        "arrow_device_array_required": True,
        "fallback_to_python": False,
        "cudf_polars_conformance_required": True,
    }, "NATIVE_GPU_CONTRACT")

    crossover = data["gpu_crossover"]
    require(crossover.get("single_global_threshold") is False, "GLOBAL_GPU_THRESHOLD_INTRODUCED")
    require(crossover.get("measurement_proxy") == "cudf-polars-raise-on-fail", "GPU_CROSSOVER_PROXY_CHANGED")
    require(
        crossover.get("native_enable_gate") == "gpu-wins-three-consecutive-scales-with-zero-fallback",
        "GPU_ENABLE_GATE_CHANGED",
    )

    ai = data["ai_data_plane"]
    require(ai.get("primary_feature_ir") == "kix-feature-ir-v1", "AI_FEATURE_IR_CHANGED")
    require(ai.get("feature_semantics") == "kix-feature-semantics-v1", "AI_FEATURE_SEMANTICS_CHANGED")
    require(ai.get("cpu_feature_backend") == "polars-rust", "AI_CPU_BACKEND_CHANGED")
    require(ai.get("gpu_feature_backend") == "libcudf-native", "AI_GPU_BACKEND_CHANGED")
    require(ai.get("sql_audit_backend") == "duckdb", "AI_SQL_AUDIT_BACKEND_CHANGED")
    require(ai.get("model_output_is_authority") is False, "MODEL_BECAME_AUTHORITY")
    require(ai.get("model_output_requires_kernel_validation") is True, "MODEL_KERNEL_GATE_DISABLED")

    violations = []
    for path in RUNTIME.rglob("*"):
        if not path.is_file() or path == CONTRACT:
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name in FORBIDDEN_NAMES:
            violations.append(path.relative_to(ROOT).as_posix())
    require(not violations, "FORBIDDEN_RUNTIME_FILES:" + ",".join(sorted(violations)))

    required = [
        "runtime/CANONICAL_BINARY_BCS_V1.md",
        "runtime/MOVE_PRODUCTION_TOPOLOGY.md",
        "runtime/AI_GPU_DATA_PLANE.md",
        "runtime/NATIVE_GPU_EXECUTION.md",
        "runtime/FEATURE_SEMANTICS_V1.md",
        "runtime/AUTHENTICATED_EXPORT.md",
        "runtime/ONSALE_ADMISSION_CONTROL.md",
        "runtime/native_gpu/include/kix_gpu.h",
        "runtime/crates/kix-types/src/lib.rs",
        "runtime/crates/kix-feature-semantics/src/lib.rs",
        "runtime/crates/kix-feature-ir/src/lib.rs",
        "runtime/crates/kix-bcs1/src/lib.rs",
        "runtime/crates/kix-bcs1/tests/golden_vectors.rs",
        "docs/PROTOCOL_MASTERPLAN_V23.md",
    ]
    for rel in required:
        require((ROOT / rel).is_file(), f"REQUIRED_ARCHITECTURE_FILE_MISSING:{rel}")

    cargo = (ROOT / "runtime" / "Cargo.toml").read_text()
    require('"crates/kix-types"' in cargo, "KIX_TYPES_NOT_IN_WORKSPACE")
    require('"crates/kix-feature-semantics"' in cargo, "FEATURE_SEMANTICS_NOT_IN_WORKSPACE")
    require('"crates/kix-feature-ir"' in cargo, "FEATURE_IR_NOT_IN_WORKSPACE")
    require('"crates/kix-bcs1"' in cargo, "KIX_BCS1_NOT_IN_WORKSPACE")

    print("runtime architecture contract v4 + S07-A codec gate OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
