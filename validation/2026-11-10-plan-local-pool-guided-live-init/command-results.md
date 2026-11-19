# Actual command results

Run from the repository root. Each ledger command uses `PYTHONDONTWRITEBYTECODE=1`
and `PYTHONPATH=reference/token_reward`; these values are also stored in
[commands.jsonl](commands.jsonl). Check logs preserve stdout and stderr together.
Exit 101 for offline Cargo resolution is unavailable evidence, not a pass.
The full-suite exit 1 is retained and discussed in the README; the isolated
unchanged test and final full-suite invocation passed. No automatic retry loop ran.

Initial exploratory command (before saved-log capture):
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3 -m unittest test_pool_session test_pool_cli test_pool_client test_pool_console test_pool_console_subprocess`
→ 69 tests passed on default Python 3.13.5 (tool output observed).

| Command actually executed | Exit | Output |
|---|---|---|
| `python3.12 --version` | 0 | [check-01.log](check-01.log) |
| `cargo --version` | 0 | [check-02.log](check-02.log) |
| `rustc --version` | 0 | [check-03.log](check-03.log) |
| `python3.12 -m unittest test_pool_session test_pool_cli test_pool_client test_pool_console test_pool_console_subprocess` | 0 | [check-04.log](check-04.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | 0 | [check-05.log](check-05.log) |
| `python3.12 scripts/check_docs_index.py` | 0 | [check-06.log](check-06.log) |
| `python3.12 scripts/check_docs_index.py --self-test` | 0 | [check-07.log](check-07.log) |
| `python3.12 scripts/check_status_register.py` | 0 | [check-08.log](check-08.log) |
| `python3.12 scripts/check_status_register.py --self-test` | 0 | [check-09.log](check-09.log) |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` | 0 | [check-10.log](check-10.log) |
| `python3.12 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | [check-11.log](check-11.log) |
| `python3.12 scripts/check_class_b_index.py` | 0 | [check-12.log](check-12.log) |
| `python3.12 scripts/check_class_b_index.py --self-test` | 0 | [check-13.log](check-13.log) |
| `python3.12 scripts/check_ci_checker_wiring.py` | 0 | [check-14.log](check-14.log) |
| `python3.12 scripts/check_ci_checker_wiring.py --self-test` | 0 | [check-15.log](check-15.log) |
| `python3.12 scripts/check_ci_test_discovery.py` | 0 | [check-16.log](check-16.log) |
| `python3.12 scripts/check_ci_test_discovery.py --self-test` | 0 | [check-17.log](check-17.log) |
| `python3.12 scripts/check_openapi_contract.py` | 0 | [check-18.log](check-18.log) |
| `python3.12 scripts/check_openapi_contract.py --self-test` | 0 | [check-19.log](check-19.log) |
| `python3.12 scripts/check_integration_gate_openapi.py` | 0 | [check-20.log](check-20.log) |
| `python3.12 scripts/check_integration_gate_openapi.py --self-test` | 0 | [check-21.log](check-21.log) |
| `python3.12 -m unittest test_pool_session test_pool_cli test_pool_client test_pool_console test_pool_console_subprocess` | 0 | [check-22.log](check-22.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | 1 | [check-23.log](check-23.log) |
| `python3.12 scripts/verify_runtime_architecture.py` | 0 | [check-24.log](check-24.log) |
| `python3.12 scripts/test_runtime_architecture.py` | 0 | [check-25.log](check-25.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | [check-26.log](check-26.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 101 | [check-27.log](check-27.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 101 | [check-28.log](check-28.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | 101 | [check-29.log](check-29.log) |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | 101 | [check-30.log](check-30.log) |
| `python3.12 validation/2026-11-10-plan-local-pool-guided-live-init/verify_transcripts.py` | 0 | [check-31.log](check-31.log) |
| `python3.12 validation/2026-11-10-plan-local-pool-guided-live-init/verify_preservation.py` | 0 | [check-32.log](check-32.log) |
| `python3.12 -m unittest test_reward_console_subprocess.RewardConsoleSubprocessTests.test_source_incomplete_no_dispatch` | 0 | [check-33.log](check-33.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | 0 | [check-34.log](check-34.log) |
| `python3.12 scripts/check_docs_index.py` | 0 | [check-35.log](check-35.log) |
| `git diff --check` | 0 | [check-36.log](check-36.log) |
| `python3.12 validation/2026-11-10-plan-local-pool-guided-live-init/verify_preservation.py` | 0 | [check-37.log](check-37.log) |
