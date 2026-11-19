# Actual command → result evidence

Executed from repository root. Validation commands inherited `PYTHONDONTWRITEBYTECODE=1`.
Python is 3.13.5 unless `python3.12` (3.12.15) is named. All commands are local/offline.
Boundary transcript exit 1 is expected; Rust exit 101 is unavailable, not passing.
The first focused run was recorded after runner creation; its original combined log is retained.
Repeated final preservation/diff entries reflect the added transcript-comparison evidence.

| Command | Result | Captures |
|---|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_pool*.py'` | exit 0; 58 tests passed | [stdout](pool-focused-final.stdout), [stderr](pool-focused-final.stderr), [exit](pool-focused-final.exit) |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; passed | [stdout](architecture.stdout), [stderr](architecture.stderr), [exit](architecture.exit) |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed | [stdout](architecture-tests.stdout), [stderr](architecture-tests.stderr), [exit](architecture-tests.exit) |
| `python3 scripts/check_docs_index.py` | exit 0; passed | [stdout](check_docs_index.stdout), [stderr](check_docs_index.stderr), [exit](check_docs_index.exit) |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; passed | [stdout](check_docs_index-self-test.stdout), [stderr](check_docs_index-self-test.stderr), [exit](check_docs_index-self-test.exit) |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0; passed | [stdout](check_tl_predicate_evidence_map.stdout), [stderr](check_tl_predicate_evidence_map.stderr), [exit](check_tl_predicate_evidence_map.exit) |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0; passed | [stdout](check_tl_predicate_evidence_map-self-test.stdout), [stderr](check_tl_predicate_evidence_map-self-test.stderr), [exit](check_tl_predicate_evidence_map-self-test.exit) |
| `python3 scripts/check_class_b_index.py` | exit 0; passed | [stdout](check_class_b_index.stdout), [stderr](check_class_b_index.stderr), [exit](check_class_b_index.exit) |
| `python3 scripts/check_class_b_index.py --self-test` | exit 0; passed | [stdout](check_class_b_index-self-test.stdout), [stderr](check_class_b_index-self-test.stderr), [exit](check_class_b_index-self-test.exit) |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0; passed | [stdout](check_ci_checker_wiring.stdout), [stderr](check_ci_checker_wiring.stderr), [exit](check_ci_checker_wiring.exit) |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0; passed | [stdout](check_ci_checker_wiring-self-test.stdout), [stderr](check_ci_checker_wiring-self-test.stderr), [exit](check_ci_checker_wiring-self-test.exit) |
| `python3 scripts/check_ci_test_discovery.py` | exit 0; passed | [stdout](check_ci_test_discovery.stdout), [stderr](check_ci_test_discovery.stderr), [exit](check_ci_test_discovery.exit) |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0; passed | [stdout](check_ci_test_discovery-self-test.stdout), [stderr](check_ci_test_discovery-self-test.stderr), [exit](check_ci_test_discovery-self-test.exit) |
| `python3 scripts/check_openapi_contract.py` | exit 0; passed | [stdout](check_openapi_contract.stdout), [stderr](check_openapi_contract.stderr), [exit](check_openapi_contract.exit) |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0; passed | [stdout](check_openapi_contract-self-test.stdout), [stderr](check_openapi_contract-self-test.stderr), [exit](check_openapi_contract-self-test.exit) |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0; passed | [stdout](check_integration_gate_openapi.stdout), [stderr](check_integration_gate_openapi.stderr), [exit](check_integration_gate_openapi.exit) |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0; passed | [stdout](check_integration_gate_openapi-self-test.stdout), [stderr](check_integration_gate_openapi-self-test.stderr), [exit](check_integration_gate_openapi-self-test.exit) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0; passed | [stdout](rust-format.stdout), [stderr](rust-format.stderr), [exit](rust-format.exit) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; unavailable: offline bcs missing, no compilation | [stdout](kernel-offline.stdout), [stderr](kernel-offline.stderr), [exit](kernel-offline.exit) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; unavailable: offline bcs missing, no compilation | [stdout](workspace-offline.stdout), [stderr](workspace-offline.stderr), [exit](workspace-offline.exit) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; unavailable: offline bcs missing, no compilation | [stdout](clippy-offline.stdout), [stderr](clippy-offline.stderr), [exit](clippy-offline.exit) |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 346 tests passed | [stdout](token-reward-discovery.stdout), [stderr](token-reward-discovery.stderr), [exit](token-reward-discovery.exit) |
| `python3 reference/token_reward/pool_console.py --mode subprocess --fixture reference/token_reward/fixtures/pool_session.json --cleanup-timeout 1 < reference/token_reward/fixtures/pool_console_journey.txt` | exit 0; passed | [stdout](subprocess-journey.stdout), [stderr](subprocess-journey.stderr), [exit](subprocess-journey.exit) |
| `python3 reference/token_reward/pool_console.py --mode subprocess --fixture reference/token_reward/fixtures/pool_session.json --cleanup-timeout 1 < reference/token_reward/fixtures/pool_console_boundaries.txt` | exit 1; expected domain refusals | [stdout](subprocess-boundaries.stdout), [stderr](subprocess-boundaries.stderr), [exit](subprocess-boundaries.exit) |
| `python3 reference/token_reward/pool_console.py --mode in-process --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_journey.txt` | exit 0; passed | [stdout](in-process-journey.stdout), [stderr](in-process-journey.stderr), [exit](in-process-journey.exit) |
| `python3 reference/token_reward/pool_console.py --mode in-process --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_boundaries.txt` | exit 1; expected domain refusals | [stdout](in-process-boundaries.stdout), [stderr](in-process-boundaries.stderr), [exit](in-process-boundaries.exit) |
| `python3 reference/token_reward/pool_console.py --guided-init < reference/token_reward/fixtures/pool_console_opening_journey.txt` | exit 0; passed | [stdout](guided-journey.stdout), [stderr](guided-journey.stderr), [exit](guided-journey.exit) |
| `python3 reference/token_reward/pool_console.py --guided-init < reference/token_reward/fixtures/pool_console_opening_boundaries.txt` | exit 1; expected domain refusals | [stdout](guided-boundaries.stdout), [stderr](guided-boundaries.stderr), [exit](guided-boundaries.exit) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_pool*.py'` | exit 0; 56 tests passed | [combined](pool-focused-initial.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 346 tests passed | [stdout](token-reward-python312.stdout), [stderr](token-reward-python312.stderr), [exit](token-reward-python312.exit) |
| `python3 scripts/check_docs_index.py` | exit 0; passed | [stdout](docs-index-final.stdout), [stderr](docs-index-final.stderr), [exit](docs-index-final.exit) |
| `python3 validation/2026-11-09-plan-local-pool-live-console/verify_preservation.py` | exit 0; passed | [stdout](preservation.stdout), [stderr](preservation.stderr), [exit](preservation.exit) |
| `git diff --check` | exit 0; passed | [stdout](diff-check.stdout), [stderr](diff-check.stderr), [exit](diff-check.exit) |
| `python3 validation/2026-11-09-plan-local-pool-live-console/verify_transcripts.py` | exit 0; passed | [stdout](transcript-check.stdout), [stderr](transcript-check.stderr), [exit](transcript-check.exit) |
| `python3 validation/2026-11-09-plan-local-pool-live-console/verify_preservation.py` | exit 0; passed | [stdout](preservation.stdout), [stderr](preservation.stderr), [exit](preservation.exit) |
| `git diff --check` | exit 0; passed | [stdout](diff-check.stdout), [stderr](diff-check.stderr), [exit](diff-check.exit) |
