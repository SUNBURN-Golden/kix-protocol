# Exact validation commands

Commands ran in the repository root except the frozen commerce unittest,
whose working directory was `reference/v0.3-rc1`. Environment and complete output
are retained in `command-results.jsonl` and the named stdout/stderr files.

| Label | Command | Exit |
|---|---|---|
| focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_calculation_*.py' -v` | 0 |
| frozen-commerce | `python3.12 -B -m unittest test_commerce test_commerce_driver` | 0 |
| verify-commerce | `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce.json` | 0 |
| transcript-journey | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_picker_journey.txt` | 0 |
| transcript-precision | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_picker_precision.txt` | 0 |
| transcript-free | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_picker_free.txt` | 0 |
| transcript-decline | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_picker_decline.txt` | 0 |
| transcript-replacement | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_picker_replacement.txt` | 0 |
| transcript-boundaries | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2 < reference/booking_resale_admission/fixtures/commerce_console_picker_boundaries.txt` | 1 |
| check_docs_index | `python3.12 -B scripts/check_docs_index.py` | 0 |
| check_docs_index-self-test | `python3.12 -B scripts/check_docs_index.py --self-test` | 0 |
| check_status_register | `python3.12 -B scripts/check_status_register.py` | 0 |
| check_status_register-self-test | `python3.12 -B scripts/check_status_register.py --self-test` | 0 |
| check_bra_evidence_map | `python3.12 -B scripts/check_bra_evidence_map.py` | 0 |
| check_bra_evidence_map-self-test | `python3.12 -B scripts/check_bra_evidence_map.py --self-test` | 0 |
| check_openapi_contract | `python3.12 -B scripts/check_openapi_contract.py` | 0 |
| check_openapi_contract-self-test | `python3.12 -B scripts/check_openapi_contract.py --self-test` | 0 |
| check_integration_gate_openapi | `python3.12 -B scripts/check_integration_gate_openapi.py` | 0 |
| check_integration_gate_openapi-self-test | `python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | 0 |
| check_ci_checker_wiring | `python3.12 -B scripts/check_ci_checker_wiring.py` | 0 |
| check_ci_checker_wiring-self-test | `python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | 0 |
| check_ci_test_discovery | `python3.12 -B scripts/check_ci_test_discovery.py` | 0 |
| check_ci_test_discovery-self-test | `python3.12 -B scripts/check_ci_test_discovery.py --self-test` | 0 |
| runtime-architecture | `python3.12 -B scripts/verify_runtime_architecture.py` | 0 |
| runtime-architecture-tests | `python3.12 -B scripts/test_runtime_architecture.py` | 0 |
| kernel-test | `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 101 |
| workspace-test | `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 101 |
| kernel-clippy | `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | 101 |
| workspace-clippy | `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | 101 |
| rust-fmt | `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 |
| preservation | `python3.12 -B .local/refund-picker/preserve.py` | 0 |
| diff-check | `git diff --check` | 0 |
| booking-socket-free | `python3.12 -B .local/refund-picker/socket_free.py` | 0 |
| docs-index-final | `python3.12 -B scripts/check_docs_index.py` | 0 |
