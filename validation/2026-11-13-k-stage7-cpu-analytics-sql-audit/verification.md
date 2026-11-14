# Foreground command evidence

Carried-in draft attempts remain in `commands.jsonl`. This table contains only
the resumed builder session commands whose foreground process has completed.
Exit 0 is a command result; documented skipped coverage is not a conformance pass.
The finishing session additionally ran: `finish-admission` (0),
`finish-scalar` (0), `finish-engines-release-attempt1` (143, SIGTERM at the
1-hour bound), an orphaned serial restart `finish-engines-release` (-15,
killed on entry to the next session), `finish-engines-release-parallel` (0,
release acceptance, CARGO_BUILD_JOBS=3 after cache preserved ~286 objects) and
`finish-report-aggregation` (0, 207 PASS observations, 69 cases x 3 runs).

| Label | Command actually run | Exit |
|---|---|---|
| resumed-admission | `python3 -m unittest authenticated_export.test_pure analytics_audit.test_admission` | 0 |
| resumed-scalar | `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir -p kix-feature-semantics --locked --offline` | 0 |
| resumed-commerce | `python3 scripts/verify_commerce.py --report .local/analytics-audit/resumed-commerce.json` | 0 |
| resumed-architecture-selftest | `python3 scripts/test_runtime_architecture.py` | 0 |
| resumed-canonical | `python3 scripts/verify_canonical.py --report .local/analytics-audit/resumed-canonical.json` | 0 |
| resumed-architecture | `python3 scripts/verify_runtime_architecture.py` | 0 |
| resumed-workspace-tests | `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 0 |
| resumed-local-source-preparation | `python3 -c 'from analytics_audit.prepare_export import prepare; b=prepare("postgres"); print(b["source"]); print("Authenticated tables:", len(b["tables"]), "rows:", sum(map(len,b["tables"].values())))'` | 0 |
| resumed-sdk | `bash -c 'set -eu ⏎ python3 scripts/check_sdk_client.py ⏎ python3 scripts/check_sdk_client.py --self-test ⏎ npm --prefix sdk run conformance ⏎ npm --prefix sdk run verify-compat'` | 0 |
| resumed-workspace-clippy | `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | 0 |
| resumed-formatting | `env RUSTUP_TOOLCHAIN=1.98.1 cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 |
| resumed-kernel-tests | `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 0 |
| resumed-kernel-clippy | `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | 0 |
| resumed-kernel-dependency-tree | `env RUSTUP_TOOLCHAIN=1.98.1 cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | 0 |
| resumed-historical-node | `node --test reference/v0.3-rc1/client/offline.test.mjs` | 0 |
| resumed-integration-gate | `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 0 |
| resumed-historical-python | `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/v0.3-rc1 -p 'test*.py'` | 0 |
| resumed-protocol-offline-checkers | `bash validation/2026-11-13-k-stage7-cpu-analytics-sql-audit/offline-checkers.sh` | 0 |
| resumed-reference-state-machines | `bash -c 'set -eu ⏎ for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward provider_facts payment_effects economics; do ⏎   PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" ⏎ done ⏎ python3 scripts/check_openapi_contract.py ⏎ python3 scripts/check_openapi_contract.py --self-test ⏎ python3 scripts/check_integration_gate_openapi.py ⏎ python3 scripts/check_integration_gate_openapi.py --self-test ⏎ python3 -m unittest integration_gate.test_offline_limits'` | 1 |
| resumed-ai-console-timeout-reproduction | `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_console_subprocess.DelegationConsoleSubprocessTests.test_default_explicit_and_subprocess_cli_transcripts_are_identical` | 0 |
| resumed-formatting-after-harness-fixes | `env RUSTUP_TOOLCHAIN=1.98.1 cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 |
| resumed-reference-after-timeout-diagnosis | `bash -c 'set -eu ⏎ for suite in ai_delegation token_reward provider_facts payment_effects economics; do ⏎   PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" ⏎ done ⏎ python3 scripts/check_openapi_contract.py ⏎ python3 scripts/check_openapi_contract.py --self-test ⏎ python3 scripts/check_integration_gate_openapi.py ⏎ python3 scripts/check_integration_gate_openapi.py --self-test ⏎ python3 -m unittest integration_gate.test_offline_limits'` | 0 |
