#!/usr/bin/env bash
# Extracted verbatim from the post-merge .github/workflows/protocol.yml
# "Stdlib offline document checks" step (merge round, 2026-11-14).
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/check_status_register.py
python3 scripts/check_status_register.py --self-test
python3 scripts/check_producer_qualification_tuple.py
python3 scripts/check_producer_qualification_tuple.py --self-test
python3 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py
python3 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test
python3 scripts/check_rs_profile_traceability.py
python3 scripts/check_rs_profile_traceability.py --self-test
python3 scripts/check_read_model_source_map.py
python3 scripts/check_read_model_source_map.py --self-test
python3 scripts/check_docs_index.py
python3 scripts/check_docs_index.py --self-test
python3 scripts/check_i12_proof_ids.py
python3 scripts/check_i12_proof_ids.py --self-test
python3 scripts/check_delegation_layer_matrix.py
python3 scripts/check_delegation_layer_matrix.py --self-test
python3 scripts/check_rs_predicate_evidence_map.py
python3 scripts/check_rs_predicate_evidence_map.py --self-test
python3 scripts/check_rs_im_evidence_map.py
python3 scripts/check_rs_im_evidence_map.py --self-test
python3 scripts/check_tl_predicate_evidence_map.py
python3 scripts/check_tl_predicate_evidence_map.py --self-test
python3 scripts/check_contract_error_codes.py
python3 scripts/check_contract_error_codes.py --self-test
python3 scripts/check_adapter_identity_map.py
python3 scripts/check_adapter_identity_map.py --self-test
python3 scripts/check_v5_transition_evidence_map.py
python3 scripts/check_v5_transition_evidence_map.py --self-test
python3 scripts/check_readiness_evidence_map.py
python3 scripts/check_readiness_evidence_map.py --self-test
python3 scripts/check_settlement_evidence_map.py
python3 scripts/check_settlement_evidence_map.py --self-test
python3 scripts/check_bra_evidence_map.py
python3 scripts/check_bra_evidence_map.py --self-test
python3 scripts/check_credit_evidence_map.py
python3 scripts/check_credit_evidence_map.py --self-test
python3 scripts/check_primary_price_fee_evidence_map.py
python3 scripts/check_primary_price_fee_evidence_map.py --self-test
python3 scripts/check_ai_delegation_evidence_map.py
python3 scripts/check_ai_delegation_evidence_map.py --self-test
python3 scripts/check_lifecycle_adr_evidence_map.py
python3 scripts/check_lifecycle_adr_evidence_map.py --self-test
python3 scripts/check_contract_invariants_evidence_map.py
python3 scripts/check_contract_invariants_evidence_map.py --self-test
python3 scripts/check_toss_card_profile_evidence_map.py
python3 scripts/check_toss_card_profile_evidence_map.py --self-test
python3 scripts/check_bcs1_evidence_map.py
python3 scripts/check_bcs1_evidence_map.py --self-test
python3 scripts/check_performance_measurement_evidence_map.py
python3 scripts/check_performance_measurement_evidence_map.py --self-test
python3 scripts/check_feature_semantics_evidence_map.py
python3 scripts/check_feature_semantics_evidence_map.py --self-test
python3 scripts/check_integration_gate_contract_evidence_map.py
python3 scripts/check_integration_gate_contract_evidence_map.py --self-test
python3 scripts/check_evidence_map_rollup.py
python3 scripts/check_evidence_map_rollup.py --self-test
python3 scripts/check_class_b_index.py
python3 scripts/check_class_b_index.py --self-test
python3 scripts/check_ci_checker_wiring.py
python3 scripts/check_ci_checker_wiring.py --self-test
python3 scripts/check_ci_test_discovery.py
python3 scripts/check_ci_test_discovery.py --self-test
python3 scripts/check_loopback_host.py
python3 scripts/check_loopback_host.py --self-test
python3 scripts/check_cargo_offline_cache.py
python3 scripts/check_cargo_offline_cache.py --self-test
python3 scripts/check_stage5_host.py --self-test
