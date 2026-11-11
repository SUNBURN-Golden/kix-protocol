# Actual verification commands and results

Commands below ran as foreground subprocesses using the retained recorder.
Inherited PYTHONPATH was removed; PYTHONDONTWRITEBYTECODE=1 and
CARGO_NET_OFFLINE=true were set. Rust environment overrides are in README.md.
All times and exit codes are actual observations. Exit 1 for the boundary
transcript is an expected known-refusal result, not a failed verification.

| Label | Command | Working directory / stdin | Actual result |
| --- | --- | --- | --- |
| editor-focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_calculation_console.py -k test_edit_ -v` | `.` | 6 tests passed |
| verify-commerce | `python3.12 -B scripts/verify_commerce.py --report validation/2026-11-10-plan-local-commerce-draft-editor/commerce.json` | `.` | PASS (exit 0) |
| transcript-journey | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2` | `.; stdin=reference/booking_resale_admission/fixtures/commerce_console_edit_journey.txt` | PASS (exit 0) |
| frozen-commerce | `python3.12 -B -m unittest test_assets test_commerce test_commerce_driver test_canonical_encoding` | `/reference/v0.3-rc1` | 44 tests passed |
| transcript-precision | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2` | `.; stdin=reference/booking_resale_admission/fixtures/commerce_console_edit_precision.txt` | PASS (exit 0) |
| transcript-replacement | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2` | `.; stdin=reference/booking_resale_admission/fixtures/commerce_console_edit_replacement.txt` | PASS (exit 0) |
| transcript-boundaries | `python3.12 -B reference/booking_resale_admission/commerce_calculation_console.py --cleanup-timeout 2` | `.; stdin=reference/booking_resale_admission/fixtures/commerce_console_edit_boundaries.txt` | Expected refusal exit 1; four driver refusals |
| verify_runtime_architecture | `python3.12 -B scripts/verify_runtime_architecture.py` | `.` | PASS (exit 0) |
| check_docs_index | `python3.12 -B scripts/check_docs_index.py` | `.` | PASS (exit 0) |
| check_docs_index-self-test | `python3.12 -B scripts/check_docs_index.py --self-test` | `.` | PASS (exit 0) |
| test_runtime_architecture | `python3.12 -B scripts/test_runtime_architecture.py` | `.` | 7 tests passed |
| check_status_register | `python3.12 -B scripts/check_status_register.py` | `.` | PASS (exit 0) |
| check_status_register-self-test | `python3.12 -B scripts/check_status_register.py --self-test` | `.` | PASS (exit 0) |
| check_bra_evidence_map | `python3.12 -B scripts/check_bra_evidence_map.py` | `.` | PASS (exit 0) |
| check_bra_evidence_map-self-test | `python3.12 -B scripts/check_bra_evidence_map.py --self-test` | `.` | PASS (exit 0) |
| check_openapi_contract | `python3.12 -B scripts/check_openapi_contract.py` | `.` | PASS (exit 0) |
| check_openapi_contract-self-test | `python3.12 -B scripts/check_openapi_contract.py --self-test` | `.` | PASS (exit 0) |
| check_integration_gate_openapi | `python3.12 -B scripts/check_integration_gate_openapi.py` | `.` | PASS (exit 0) |
| check_integration_gate_openapi-self-test | `python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | `.` | PASS (exit 0) |
| check_ci_checker_wiring | `python3.12 -B scripts/check_ci_checker_wiring.py` | `.` | PASS (exit 0) |
| check_ci_checker_wiring-self-test | `python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | `.` | PASS (exit 0) |
| check_ci_test_discovery | `python3.12 -B scripts/check_ci_test_discovery.py` | `.` | PASS (exit 0) |
| check_ci_test_discovery-self-test | `python3.12 -B scripts/check_ci_test_discovery.py --self-test` | `.` | PASS (exit 0) |
| kernel-tests | `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | `.` | UNAVAILABLE: offline registry lacks bcs (exit 101 before compilation) |
| workspace-tests | `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | `.` | UNAVAILABLE: offline registry lacks bcs (exit 101 before compilation) |
| kernel-clippy | `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | `.` | UNAVAILABLE: offline registry lacks bcs (exit 101 before compilation) |
| workspace-clippy | `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | `.` | UNAVAILABLE: offline registry lacks bcs (exit 101 before compilation) |
| cargo-fmt | `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | `.` | PASS (exit 0) |
| commerce-focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_calculation_*.py' -v` | `.` | 50 tests passed |
| preservation | `python3.12 -B validation/2026-11-10-plan-local-commerce-draft-editor/verify_preservation.py` | `.` | PASS (exit 0) |
| booking-offline | `python3.12 -B .local/draft-editor/socket_free.py` | `.` | 929 tests passed; exactly one HTTP exclusion |
| preservation-final | `python3.12 -B validation/2026-11-10-plan-local-commerce-draft-editor/verify_preservation.py` | `.` | PASS (exit 0) |
