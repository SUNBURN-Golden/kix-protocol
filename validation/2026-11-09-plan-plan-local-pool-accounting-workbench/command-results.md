# Commands actually executed

Environment: Python 3.13.5; rustc 1.98.1 (48a229cea 2026-09-01).

Raw output and exit statuses are retained, including the initial failed discovery.

| Command | Actual result | Evidence |
|---|---|---|
| `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3 -m unittest test_reward_model.PoolConservationTests test_tl4_model_properties.PoolPropertyTests test_tl4_fuzz_boundaries` | Exit 0; 16 tests passed | [model-baseline.log](model-baseline.log) |
| `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3 -m unittest test_pool_session test_pool_cli test_pool_console` | Exit 0; 26 tests passed | [pool-focused.log](pool-focused.log) |
| `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3 -m unittest test_pool_session test_pool_cli test_pool_console` | Exit 0; 28 tests passed | [pool-focused-final.log](pool-focused-final.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | Exit 0 | [check_docs_index.log](check_docs_index.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | Exit 0 | [check_docs_index-self-test.log](check_docs_index-self-test.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0 | [check_tl_predicate_evidence_map.log](check_tl_predicate_evidence_map.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0 | [check_tl_predicate_evidence_map-self-test.log](check_tl_predicate_evidence_map-self-test.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_class_b_index.py` | Exit 0 | [check_class_b_index.log](check_class_b_index.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_class_b_index.py --self-test` | Exit 0 | [check_class_b_index-self-test.log](check_class_b_index-self-test.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py` | Exit 0 | [check_ci_checker_wiring.log](check_ci_checker_wiring.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0 | [check_ci_checker_wiring-self-test.log](check_ci_checker_wiring-self-test.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py` | Exit 0 | [check_ci_test_discovery.log](check_ci_test_discovery.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0 | [check_ci_test_discovery-self-test.log](check_ci_test_discovery-self-test.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_openapi_contract.py` | Exit 0 | [check_openapi_contract.log](check_openapi_contract.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_openapi_contract.py --self-test` | Exit 0 | [check_openapi_contract-self-test.log](check_openapi_contract-self-test.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | Exit 0 | [runtime-architecture.log](runtime-architecture.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_integration_gate_openapi.py` | Exit 0 | [check_integration_gate_openapi.log](check_integration_gate_openapi.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0 | [check_integration_gate_openapi-self-test.log](check_integration_gate_openapi-self-test.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101, missing offline dependency; no compilation | [kernel-tests.log](kernel-tests.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed | [runtime-architecture-regressions.log](runtime-architecture-regressions.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | FAILED: exit 1 (retained; see later diagnosis/rerun); 316 tests | [token-reward-discovery.log](token-reward-discovery.log) |
| `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3 -m unittest test_reward_console_subprocess.RewardConsoleSubprocessTests.test_source_incomplete_no_dispatch` | Exit 0; 1 tests passed | [existing-reward-timeout-diagnostic.log](existing-reward-timeout-diagnostic.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: exit 101, missing offline dependency; no compilation | [workspace-tests.log](workspace-tests.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101, missing offline dependency; no compilation | [workspace-clippy.log](workspace-clippy.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 | [workspace-fmt.log](workspace-fmt.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_cargo_offline_cache.py` | Exit 0 | [cargo-cache-diagnostic.log](cargo-cache-diagnostic.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 reference/token_reward/pool_cli.py --fixture reference/token_reward/fixtures/pool_session.json --requests reference/token_reward/fixtures/pool_journey.jsonl` | Exit 0 | [pool-cli-journey.stdout](pool-cli-journey.stdout) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 reference/token_reward/pool_cli.py --fixture reference/token_reward/fixtures/pool_session.json --requests reference/token_reward/fixtures/pool_boundaries.jsonl` | Expected exit 1: domain refusals | [pool-cli-boundaries.stdout](pool-cli-boundaries.stdout) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 reference/token_reward/pool_console.py --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_journey.txt` | Exit 0 | [pool-console-journey.stdout](pool-console-journey.stdout) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 reference/token_reward/pool_console.py --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_boundaries.txt` | Expected exit 1: domain refusals | [pool-console-boundaries.stdout](pool-console-boundaries.stdout) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 validation/2026-11-09-plan-plan-local-pool-accounting-workbench/verify_preservation.py` | Exit 0 | [protected-preservation.log](protected-preservation.log) |
| `git diff --check` | Exit 0 | [patch-whitespace.log](patch-whitespace.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; 316 tests passed | [token-reward-discovery-final.log](token-reward-discovery-final.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 validation/2026-11-09-plan-plan-local-pool-accounting-workbench/verify_preservation.py` | Exit 0 | [protected-preservation-final.log](protected-preservation-final.log) |
| `env PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | Exit 0 | [docs-index-final.log](docs-index-final.log) |
| `git diff --check` | Exit 0 | [patch-whitespace-final.log](patch-whitespace-final.log) |
