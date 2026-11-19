# Actual verification commands and results

Every row records a foreground invocation; full output is in the linked log.
Intermediate failures remain visible. Durations in structured records are not performance measurements.

| Command actually run | Actual result | Full output |
|---|---|---|
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_historical_receipt_vectors.py -v` | PASS (exit 0) | [historical-focused.log](historical-focused.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_historical_receipt_vectors.py -v` | FAIL (exit 1) | [historical-final.log](historical-final.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_historical_receipt_vectors.py -v` | FAIL (exit 1) | [historical-final-fixed.log](historical-final-fixed.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_historical_receipt_vectors.py -v` | PASS (exit 0) | [historical-verified.log](historical-verified.log) |
| `python3.12 -B scripts/check_status_register.py` | PASS (exit 0) | [document-01-check_status_register.log](document-01-check_status_register.log) |
| `python3.12 -B scripts/check_status_register.py --self-test` | PASS (exit 0) | [document-02-check_status_register-self-test.log](document-02-check_status_register-self-test.log) |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` | PASS (exit 0) | [document-03-check_producer_qualification_tuple.log](document-03-check_producer_qualification_tuple.log) |
| `python3.12 -B scripts/check_producer_qualification_tuple.py --self-test` | PASS (exit 0) | [document-04-check_producer_qualification_tuple-self-test.log](document-04-check_producer_qualification_tuple-self-test.log) |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | PASS (exit 0) | [document-05-check_consumer_binding_index.log](document-05-check_consumer_binding_index.log) |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | PASS (exit 0) | [document-06-check_consumer_binding_index-self-test.log](document-06-check_consumer_binding_index-self-test.log) |
| `python3.12 -B scripts/check_rs_profile_traceability.py` | PASS (exit 0) | [document-07-check_rs_profile_traceability.log](document-07-check_rs_profile_traceability.log) |
| `python3.12 -B scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0) | [document-08-check_rs_profile_traceability-self-test.log](document-08-check_rs_profile_traceability-self-test.log) |
| `python3.12 -B scripts/check_read_model_source_map.py` | PASS (exit 0) | [document-09-check_read_model_source_map.log](document-09-check_read_model_source_map.log) |
| `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0) | [settlement-regressions.log](settlement-regressions.log) |
| `python3.12 -B scripts/check_read_model_source_map.py --self-test` | PASS (exit 0) | [document-10-check_read_model_source_map-self-test.log](document-10-check_read_model_source_map-self-test.log) |
| `python3.12 -B scripts/check_docs_index.py` | PASS (exit 0) | [document-11-check_docs_index.log](document-11-check_docs_index.log) |
| `python3.12 -B scripts/check_docs_index.py --self-test` | PASS (exit 0) | [document-12-check_docs_index-self-test.log](document-12-check_docs_index-self-test.log) |
| `python3.12 -B scripts/check_i12_proof_ids.py` | PASS (exit 0) | [document-13-check_i12_proof_ids.log](document-13-check_i12_proof_ids.log) |
| `python3.12 -B scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0) | [document-14-check_i12_proof_ids-self-test.log](document-14-check_i12_proof_ids-self-test.log) |
| `python3.12 -B scripts/check_delegation_layer_matrix.py` | PASS (exit 0) | [document-15-check_delegation_layer_matrix.log](document-15-check_delegation_layer_matrix.log) |
| `python3.12 -B scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0) | [document-16-check_delegation_layer_matrix-self-test.log](document-16-check_delegation_layer_matrix-self-test.log) |
| `python3.12 -B scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0) | [document-17-check_rs_predicate_evidence_map.log](document-17-check_rs_predicate_evidence_map.log) |
| `python3.12 -B scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0) | [document-18-check_rs_predicate_evidence_map-self-test.log](document-18-check_rs_predicate_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_rs_im_evidence_map.py` | PASS (exit 0) | [document-19-check_rs_im_evidence_map.log](document-19-check_rs_im_evidence_map.log) |
| `python3.12 -B scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0) | [document-20-check_rs_im_evidence_map-self-test.log](document-20-check_rs_im_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0) | [document-21-check_tl_predicate_evidence_map.log](document-21-check_tl_predicate_evidence_map.log) |
| `python3.12 -B scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0) | [document-22-check_tl_predicate_evidence_map-self-test.log](document-22-check_tl_predicate_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_contract_error_codes.py` | PASS (exit 0) | [document-23-check_contract_error_codes.log](document-23-check_contract_error_codes.log) |
| `python3.12 -B scripts/verify_runtime_architecture.py` | PASS (exit 0) | [architecture.log](architecture.log) |
| `python3.12 -B scripts/test_runtime_architecture.py` | PASS (exit 0) | [architecture-tests.log](architecture-tests.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS (exit 0) | [kernel-tests.log](kernel-tests.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS (exit 0) | [kernel-clippy.log](kernel-clippy.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) | [rustfmt.log](rustfmt.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_*.py' -v` | PASS (exit 0) | [commerce-suites.log](commerce-suites.log) |
| `python3.12 -B scripts/check_openapi_contract.py` | PASS (exit 0) | [check-openapi_contract.log](check-openapi_contract.log) |
| `python3.12 -B scripts/check_openapi_contract.py --self-test` | PASS (exit 0) | [check-openapi_contract-self-test.log](check-openapi_contract-self-test.log) |
| `python3.12 -B scripts/check_integration_gate_openapi.py` | PASS (exit 0) | [check-integration_gate_openapi.log](check-integration_gate_openapi.log) |
| `python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) | [check-integration_gate_openapi-self-test.log](check-integration_gate_openapi-self-test.log) |
| `python3.12 -B scripts/check_sdk_client.py` | PASS (exit 0) | [check-sdk_client.log](check-sdk_client.log) |
| `python3.12 -B scripts/check_sdk_client.py --self-test` | PASS (exit 0) | [check-sdk_client-self-test.log](check-sdk_client-self-test.log) |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | PASS (exit 0) | [offline-limits.log](offline-limits.log) |
| `python3.12 -B scripts/check_contract_error_codes.py --self-test` | PASS (exit 0) | [document-24-check_contract_error_codes-self-test.log](document-24-check_contract_error_codes-self-test.log) |
| `python3.12 -B scripts/check_adapter_identity_map.py` | PASS (exit 0) | [document-25-check_adapter_identity_map.log](document-25-check_adapter_identity_map.log) |
| `python3.12 -B scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0) | [document-26-check_adapter_identity_map-self-test.log](document-26-check_adapter_identity_map-self-test.log) |
| `python3.12 -B scripts/check_v5_transition_evidence_map.py` | PASS (exit 0) | [document-27-check_v5_transition_evidence_map.log](document-27-check_v5_transition_evidence_map.log) |
| `python3.12 -B scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0) | [document-28-check_v5_transition_evidence_map-self-test.log](document-28-check_v5_transition_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_readiness_evidence_map.py` | PASS (exit 0) | [document-29-check_readiness_evidence_map.log](document-29-check_readiness_evidence_map.log) |
| `python3.12 -B scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0) | [document-30-check_readiness_evidence_map-self-test.log](document-30-check_readiness_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_settlement_evidence_map.py` | PASS (exit 0) | [document-31-check_settlement_evidence_map.log](document-31-check_settlement_evidence_map.log) |
| `python3.12 -B scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0) | [document-32-check_settlement_evidence_map-self-test.log](document-32-check_settlement_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_bra_evidence_map.py` | PASS (exit 0) | [document-33-check_bra_evidence_map.log](document-33-check_bra_evidence_map.log) |
| `python3.12 -B scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0) | [document-34-check_bra_evidence_map-self-test.log](document-34-check_bra_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_credit_evidence_map.py` | PASS (exit 0) | [document-35-check_credit_evidence_map.log](document-35-check_credit_evidence_map.log) |
| `python3.12 -B scripts/check_credit_evidence_map.py --self-test` | PASS (exit 0) | [document-36-check_credit_evidence_map-self-test.log](document-36-check_credit_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_primary_price_fee_evidence_map.py` | PASS (exit 0) | [document-37-check_primary_price_fee_evidence_map.log](document-37-check_primary_price_fee_evidence_map.log) |
| `python3.12 -B scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS (exit 0) | [document-38-check_primary_price_fee_evidence_map-self-test.log](document-38-check_primary_price_fee_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_ai_delegation_evidence_map.py` | PASS (exit 0) | [document-39-check_ai_delegation_evidence_map.log](document-39-check_ai_delegation_evidence_map.log) |
| `python3.12 -B scripts/check_ai_delegation_evidence_map.py --self-test` | PASS (exit 0) | [document-40-check_ai_delegation_evidence_map-self-test.log](document-40-check_ai_delegation_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_lifecycle_adr_evidence_map.py` | PASS (exit 0) | [document-41-check_lifecycle_adr_evidence_map.log](document-41-check_lifecycle_adr_evidence_map.log) |
| `python3.12 -B scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS (exit 0) | [document-42-check_lifecycle_adr_evidence_map-self-test.log](document-42-check_lifecycle_adr_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_contract_invariants_evidence_map.py` | PASS (exit 0) | [document-43-check_contract_invariants_evidence_map.log](document-43-check_contract_invariants_evidence_map.log) |
| `python3.12 -B scripts/check_contract_invariants_evidence_map.py --self-test` | PASS (exit 0) | [document-44-check_contract_invariants_evidence_map-self-test.log](document-44-check_contract_invariants_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_toss_card_profile_evidence_map.py` | PASS (exit 0) | [document-45-check_toss_card_profile_evidence_map.log](document-45-check_toss_card_profile_evidence_map.log) |
| `python3.12 -B scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS (exit 0) | [document-46-check_toss_card_profile_evidence_map-self-test.log](document-46-check_toss_card_profile_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_bcs1_evidence_map.py` | PASS (exit 0) | [document-47-check_bcs1_evidence_map.log](document-47-check_bcs1_evidence_map.log) |
| `python3.12 -B scripts/check_bcs1_evidence_map.py --self-test` | PASS (exit 0) | [document-48-check_bcs1_evidence_map-self-test.log](document-48-check_bcs1_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_performance_measurement_evidence_map.py` | PASS (exit 0) | [document-49-check_performance_measurement_evidence_map.log](document-49-check_performance_measurement_evidence_map.log) |
| `python3.12 -B scripts/check_performance_measurement_evidence_map.py --self-test` | PASS (exit 0) | [document-50-check_performance_measurement_evidence_map-self-test.log](document-50-check_performance_measurement_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_feature_semantics_evidence_map.py` | PASS (exit 0) | [document-51-check_feature_semantics_evidence_map.log](document-51-check_feature_semantics_evidence_map.log) |
| `python3.12 -B scripts/check_feature_semantics_evidence_map.py --self-test` | PASS (exit 0) | [document-52-check_feature_semantics_evidence_map-self-test.log](document-52-check_feature_semantics_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py` | PASS (exit 0) | [document-53-check_integration_gate_contract_evidence_map.log](document-53-check_integration_gate_contract_evidence_map.log) |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS (exit 0) | [document-54-check_integration_gate_contract_evidence_map-self-test.log](document-54-check_integration_gate_contract_evidence_map-self-test.log) |
| `python3.12 -B scripts/check_evidence_map_rollup.py` | PASS (exit 0) | [document-55-check_evidence_map_rollup.log](document-55-check_evidence_map_rollup.log) |
| `python3.12 -B scripts/check_evidence_map_rollup.py --self-test` | PASS (exit 0) | [document-56-check_evidence_map_rollup-self-test.log](document-56-check_evidence_map_rollup-self-test.log) |
| `python3.12 -B scripts/check_class_b_index.py` | PASS (exit 0) | [document-57-check_class_b_index.log](document-57-check_class_b_index.log) |
| `python3.12 -B scripts/check_class_b_index.py --self-test` | PASS (exit 0) | [document-58-check_class_b_index-self-test.log](document-58-check_class_b_index-self-test.log) |
| `python3.12 -B scripts/check_ci_checker_wiring.py` | PASS (exit 0) | [document-59-check_ci_checker_wiring.log](document-59-check_ci_checker_wiring.log) |
| `python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) | [document-60-check_ci_checker_wiring-self-test.log](document-60-check_ci_checker_wiring-self-test.log) |
| `python3.12 -B scripts/check_ci_test_discovery.py` | PASS (exit 0) | [document-61-check_ci_test_discovery.log](document-61-check_ci_test_discovery.log) |
| `python3.12 -B scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) | [document-62-check_ci_test_discovery-self-test.log](document-62-check_ci_test_discovery-self-test.log) |
| `python3.12 -B scripts/check_loopback_host.py` | PASS (exit 0) | [document-63-check_loopback_host.log](document-63-check_loopback_host.log) |
| `python3.12 -B scripts/check_loopback_host.py --self-test` | PASS (exit 0) | [document-64-check_loopback_host-self-test.log](document-64-check_loopback_host-self-test.log) |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | PASS (exit 0) | [document-65-check_cargo_offline_cache.log](document-65-check_cargo_offline_cache.log) |
| `python3.12 -B scripts/check_cargo_offline_cache.py --self-test` | PASS (exit 0) | [document-66-check_cargo_offline_cache-self-test.log](document-66-check_cargo_offline_cache-self-test.log) |
| `python3.12 -B scripts/check_stage5_host.py --self-test` | PASS (exit 0) | [document-67-check_stage5_host-self-test.log](document-67-check_stage5_host-self-test.log) |
| `python3.12 -B validation/2026-11-15-plan-commerce-historical-receipt-vectors/check_preservation.py` | PASS (exit 0) | [preservation-after.log](preservation-after.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0) | [booking-regressions.log](booking-regressions.log) |
| `python3.12 -B scripts/check_docs_index.py` | PASS (exit 0) | [docs-index-final.log](docs-index-final.log) |
| `python3.12 -B validation/2026-11-15-plan-commerce-historical-receipt-vectors/check_preservation.py` | PASS (exit 0) | [preservation-final.log](preservation-final.log) |
