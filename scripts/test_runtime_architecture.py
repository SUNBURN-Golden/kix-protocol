#!/usr/bin/env python3
"""Real negative fixtures for the declaration/dependency checker, not Rust runtime code."""
from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_runtime_architecture as checker


class ArchitectureGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="kix-architecture-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("runtime", "docs"):
            shutil.copytree(
                checker.ROOT / name,
                self.root / name,
                ignore=shutil.ignore_patterns("target", "__pycache__"),
            )
        self.contract = self.root / "runtime/ARCHITECTURE.toml"
        self.original = self.contract.read_text()

    def run_checker(self) -> int:
        with patch.object(checker, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()):
            return checker.main()

    def test_valid_contract(self) -> None:
        self.assertEqual(self.run_checker(), 0)

    def test_invalid_contract_values(self) -> None:
        mutations = [
            ('quorum_ack = false', 'quorum_ack = true'),
            ('automatic_torn_tail_truncation = false', 'automatic_torn_tail_truncation = true'),
            ('complete_prefix_rollback_detected = false', 'complete_prefix_rollback_detected = true'),
            ('production_enabled = false', 'production_enabled = true'),
            ('production_enabled = false', 'production_enabled = 0'),
            ('consumer_truth = false', 'consumer_truth = 0'),
            ('fallback_to_python = false', 'fallback_to_python = 0'),
            ('same_resource_dual_write = false', 'same_resource_dual_write = true'),
            ('execution_fence_in_command_identity = false', 'execution_fence_in_command_identity = true'),
            ('old_bound_observations_preserved = true', 'old_bound_observations_preserved = false'),
            ('unknown_is_failure = false', 'unknown_is_failure = true'),
            ('in_memory_apply_is_durable_ack = false', 'in_memory_apply_is_durable_ack = true'),
            ('delegated_execution_enabled = false', 'delegated_execution_enabled = true'),
            ('projection_lsn_is_source_commit = false', 'projection_lsn_is_source_commit = true'),
            ('f64_sort_key = false', 'f64_sort_key = true'),
            ('python = false', 'python = true'),
            ('queue_position_preserved_on_reshard = true', 'queue_position_preserved_on_reshard = false'),
            ('model_output_is_authority = false', 'model_output_is_authority = true'),
            ('per_sale_terminal_fence_required = true', 'per_sale_terminal_fence_required = false'),
        ]
        for old, new in mutations:
            with self.subTest(mutation=new):
                self.assertIn(old, self.original)
                self.contract.write_text(self.original.replace(old, new, 1))
                with self.assertRaises(SystemExit):
                    self.run_checker()
        self.contract.write_text(self.original)

    def test_missing_lock_or_golden_vector(self) -> None:
        for relative in ("runtime/Cargo.lock", "runtime/crates/kix-bcs1/tests/golden_vectors.rs",
                         "runtime/crates/kix-ktx-wire/src/registry.rs",
                         "runtime/crates/kix-ktx-wire/tests/golden_vectors.rs",
                         "runtime/crates/kix-journal-local/tests/recovery.rs"):
            path = self.root / relative
            original = path.read_bytes()
            with self.subTest(missing=relative):
                path.unlink()
                try:
                    with self.assertRaises(SystemExit):
                        self.run_checker()
                finally:
                    path.write_bytes(original)

    def test_kernel_dependency_injection(self) -> None:
        manifest = self.root / "runtime/crates/kix-kernel/Cargo.toml"
        manifest.write_text(manifest.read_text() + '\ntokio = "1"\n')
        with self.assertRaisesRegex(SystemExit, "KERNEL_DEPENDENCY_DRIFT"):
            self.run_checker()

    def test_transitive_dependency_injection(self) -> None:
        manifest = self.root / "runtime/crates/kix-types/Cargo.toml"
        text = manifest.read_text()
        if "[dependencies]" in text:
            text = text.replace("[dependencies]", '[dependencies]\nserde = "1"', 1)
        else:
            text += '\n[dependencies]\nserde = "1"\n'
        manifest.write_text(text)
        with self.assertRaisesRegex(SystemExit, "KERNEL_TRANSITIVE_DEPENDENCY_DRIFT"):
            self.run_checker()

    def test_hidden_target_dependency(self) -> None:
        manifest = self.root / "runtime/crates/kix-kernel/Cargo.toml"
        manifest.write_text(manifest.read_text() + '\n[target.\'cfg(unix)\'.dependencies]\ntokio = "1"\n')
        with self.assertRaisesRegex(SystemExit, "KERNEL_HIDDEN_DEPENDENCY_DRIFT"):
            self.run_checker()

    def test_python_runtime_source_is_rejected(self) -> None:
        (self.root / "runtime/accidental_engine.py").write_text("pass\n")
        with self.assertRaisesRegex(SystemExit, "FORBIDDEN_RUNTIME_SOURCE"):
            self.run_checker()


if __name__ == "__main__":
    unittest.main(verbosity=2)
