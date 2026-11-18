# Actual local commands and results

Commands ran from repository root. Every log captures stdout/stderr and exit status.

| Command | Actual result |
|---|---|
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_temporal_vectors.py -v` | [PASS; exit 0; 9 tests](temporal-focused.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_journey*.py' -v` | [PASS; exit 0; 13 tests](journey-unchanged.log) |
| `env PYTHONPATH=reference/booking_resale_admission python3.12 -B -m unittest test_reservation_fsm.ReservationFsmTests.test_cancel_before_payment_frees_and_payment_blocks_compensation test_admission_fsm.AdmissionFsmTests.test_transfer_then_entry_rejects_both_presentations test_admission_fsm.AdmissionFsmTests.test_expired_authorization_is_replaced_once test_admission_fsm.AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version -v` | [PASS; exit 0; 4 tests](cited-socket-free.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_status_register.py` | [PASS; exit 0](check_status_register.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | [PASS; exit 0; 224 tests](reference-settlement_f01_f03.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_status_register.py --self-test` | [PASS; exit 0](check_status_register-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_producer_qualification_tuple.py` | [PASS; exit 0](check_producer_qualification_tuple.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_producer_qualification_tuple.py --self-test` | [PASS; exit 0](check_producer_qualification_tuple-self-test.log) |
| `/home/box/.local/bin/python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | [PASS; exit 0](check_consumer_binding_index.log) |
| `/home/box/.local/bin/python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | [PASS; exit 0](check_consumer_binding_index-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_rs_profile_traceability.py` | [PASS; exit 0](check_rs_profile_traceability.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_rs_profile_traceability.py --self-test` | [PASS; exit 0](check_rs_profile_traceability-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_read_model_source_map.py` | [PASS; exit 0](check_read_model_source_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_read_model_source_map.py --self-test` | [PASS; exit 0](check_read_model_source_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_docs_index.py` | [FAIL; exit 1; missing index link, subsequently fixed](check_docs_index.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | [PASS; exit 0; 139 tests](http-readiness.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest integration_gate.test_offline_limits` | [PASS; exit 0; 9 tests](offline-limits.log) |
| `/home/box/.local/bin/python3.12 -B scripts/verify_runtime_architecture.py` | [PASS; exit 0](architecture.log) |
| `/home/box/.local/bin/python3.12 -B scripts/test_runtime_architecture.py` | [PASS; exit 0; 7 tests](architecture-negative.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | [PASS; exit 0](kernel-tests.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | [PASS; exit 0](workspace-tests.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_docs_index.py` | [PASS; exit 0](check_docs_index-fixed.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_docs_index.py --self-test` | [PASS; exit 0](check_docs_index-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_i12_proof_ids.py` | [PASS; exit 0](check_i12_proof_ids.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_i12_proof_ids.py --self-test` | [PASS; exit 0](check_i12_proof_ids-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_delegation_layer_matrix.py` | [PASS; exit 0](check_delegation_layer_matrix.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_delegation_layer_matrix.py --self-test` | [PASS; exit 0](check_delegation_layer_matrix-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_rs_predicate_evidence_map.py` | [PASS; exit 0](check_rs_predicate_evidence_map.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | [PASS; exit 0](workspace-clippy.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_rs_predicate_evidence_map.py --self-test` | [PASS; exit 0](check_rs_predicate_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_rs_im_evidence_map.py` | [PASS; exit 0](check_rs_im_evidence_map.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | [PASS; exit 0](rust-format.log) |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | [PASS; exit 0](kernel-dependencies.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_rs_im_evidence_map.py --self-test` | [PASS; exit 0](check_rs_im_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_tl_predicate_evidence_map.py` | [PASS; exit 0](check_tl_predicate_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_tl_predicate_evidence_map.py --self-test` | [PASS; exit 0](check_tl_predicate_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_contract_error_codes.py` | [PASS; exit 0](check_contract_error_codes.log) |
| `npm --prefix sdk run conformance` | [PASS; exit 0](sdk-conformance.log) |
| `npm --prefix sdk run verify-compat` | [PASS; exit 0](sdk-compat.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_contract_error_codes.py --self-test` | [PASS; exit 0](check_contract_error_codes-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_adapter_identity_map.py` | [PASS; exit 0](check_adapter_identity_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_adapter_identity_map.py --self-test` | [PASS; exit 0](check_adapter_identity_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_v5_transition_evidence_map.py` | [PASS; exit 0](check_v5_transition_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_v5_transition_evidence_map.py --self-test` | [PASS; exit 0](check_v5_transition_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_readiness_evidence_map.py` | [PASS; exit 0](check_readiness_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_readiness_evidence_map.py --self-test` | [PASS; exit 0](check_readiness_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_settlement_evidence_map.py` | [PASS; exit 0](check_settlement_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_settlement_evidence_map.py --self-test` | [PASS; exit 0](check_settlement_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_bra_evidence_map.py` | [PASS; exit 0](check_bra_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_bra_evidence_map.py --self-test` | [PASS; exit 0](check_bra_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_credit_evidence_map.py` | [PASS; exit 0](check_credit_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_credit_evidence_map.py --self-test` | [PASS; exit 0](check_credit_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_primary_price_fee_evidence_map.py` | [PASS; exit 0](check_primary_price_fee_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_primary_price_fee_evidence_map.py --self-test` | [PASS; exit 0](check_primary_price_fee_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_ai_delegation_evidence_map.py` | [PASS; exit 0](check_ai_delegation_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_ai_delegation_evidence_map.py --self-test` | [PASS; exit 0](check_ai_delegation_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_lifecycle_adr_evidence_map.py` | [PASS; exit 0](check_lifecycle_adr_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_lifecycle_adr_evidence_map.py --self-test` | [PASS; exit 0](check_lifecycle_adr_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_contract_invariants_evidence_map.py` | [PASS; exit 0](check_contract_invariants_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_contract_invariants_evidence_map.py --self-test` | [PASS; exit 0](check_contract_invariants_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_toss_card_profile_evidence_map.py` | [PASS; exit 0](check_toss_card_profile_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_toss_card_profile_evidence_map.py --self-test` | [PASS; exit 0](check_toss_card_profile_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_bcs1_evidence_map.py` | [PASS; exit 0](check_bcs1_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_bcs1_evidence_map.py --self-test` | [PASS; exit 0](check_bcs1_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_performance_measurement_evidence_map.py` | [PASS; exit 0](check_performance_measurement_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_performance_measurement_evidence_map.py --self-test` | [PASS; exit 0](check_performance_measurement_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_feature_semantics_evidence_map.py` | [PASS; exit 0](check_feature_semantics_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_feature_semantics_evidence_map.py --self-test` | [PASS; exit 0](check_feature_semantics_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_integration_gate_contract_evidence_map.py` | [PASS; exit 0](check_integration_gate_contract_evidence_map.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_integration_gate_contract_evidence_map.py --self-test` | [PASS; exit 0](check_integration_gate_contract_evidence_map-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_evidence_map_rollup.py` | [PASS; exit 0](check_evidence_map_rollup.log) |
| `python3.12 -B validation/2026-11-15-plan-commerce-temporal-vectors/check_preservation.py` | [PASS; exit 0](preservation-after.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_evidence_map_rollup.py --self-test` | [PASS; exit 0](check_evidence_map_rollup-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_class_b_index.py` | [PASS; exit 0](check_class_b_index.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_class_b_index.py --self-test` | [PASS; exit 0](check_class_b_index-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_ci_checker_wiring.py` | [PASS; exit 0](check_ci_checker_wiring.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | [PASS; exit 0](check_ci_checker_wiring-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_ci_test_discovery.py` | [PASS; exit 0](check_ci_test_discovery.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_ci_test_discovery.py --self-test` | [PASS; exit 0](check_ci_test_discovery-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_loopback_host.py` | [PASS; exit 0](check_loopback_host.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_loopback_host.py --self-test` | [PASS; exit 0](check_loopback_host-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_cargo_offline_cache.py` | [PASS; exit 0](check_cargo_offline_cache.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_cargo_offline_cache.py --self-test` | [PASS; exit 0](check_cargo_offline_cache-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_stage5_host.py --self-test` | [PASS; exit 0](check_stage5_host-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_openapi_contract.py` | [PASS; exit 0](check_openapi_contract.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_openapi_contract.py --self-test` | [PASS; exit 0](check_openapi_contract-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_integration_gate_openapi.py` | [PASS; exit 0](check_integration_gate_openapi.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | [PASS; exit 0](check_integration_gate_openapi-self-test.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_sdk_client.py` | [PASS; exit 0](check_sdk_client.log) |
| `/home/box/.local/bin/python3.12 -B scripts/check_sdk_client.py --self-test` | [PASS; exit 0](check_sdk_client-self-test.log) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | [PASS; exit 0](locked-blobs-after.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | [PASS; exit 0; 970 tests](reference-booking_resale_admission.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | [PASS; exit 0; 242 tests](reference-credit_advance_f04.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | [PASS; exit 0; 169 tests](reference-ai_delegation.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | [PASS; exit 0; 397 tests](reference-token_reward.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | [PASS; exit 0; 86 tests](reference-provider_facts.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/payment_effects -t reference/payment_effects` | [PASS; exit 0; 28 tests](reference-payment_effects.log) |
| `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/economics -t reference/economics` | [PASS; exit 0; 99 tests](reference-economics.log) |
| `python3.12 --version` | [PASS; exit 0](toolchain-python.log) |
| `node --version` | [PASS; exit 0](toolchain-node.log) |
| `cargo --version` | [PASS; exit 0](toolchain-cargo.log) |
| `python3.12 -B validation/2026-11-15-plan-commerce-temporal-vectors/check_preservation.py` | [PASS; exit 0](preservation-final.log) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | [PASS; exit 0](locked-blobs-final.log) |
| `python3.12 -B scripts/check_docs_index.py` | [PASS; exit 0](check_docs_index-final.log) |
