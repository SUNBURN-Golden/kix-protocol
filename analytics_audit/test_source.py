"""Mandatory local PostgreSQL -> authenticated export -> three-engine acceptance.

Explicitly invoked; missing PostgreSQL, Rust or engines is a failure, never skip.
No service is contacted: the exporter provisions a disposable Unix-socket cluster.
"""
import os
from pathlib import Path
import subprocess
import unittest


class LocalSourceTests(unittest.TestCase):
    def test_three_engines_on_local_postgres_export(self):
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.update(RUSTUP_TOOLCHAIN='1.98.1', KIX_AUDIT_SOURCE='postgres', CARGO_BUILD_JOBS='1')
        command = ['cargo', 'test', '--manifest-path', 'runtime/Cargo.toml',
                   '-p', 'kix-analytics-audit', '--features', 'engines',
                   '--test', 'conformance', '--locked', '--offline', '--', '--test-threads=1']
        completed = subprocess.run(command, cwd=root, env=env, check=False)
        self.assertEqual(completed.returncode, 0, command)


if __name__ == '__main__':
    unittest.main()
