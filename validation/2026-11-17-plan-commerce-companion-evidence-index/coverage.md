# Coverage mapping before adding tests

Task: `plan-commerce-companion-evidence-index`; input is the supervisor's node
specification and read-only design plan in the session (no issue or node-specific
`docs/tasks/` file). Task 005 is historical program context, not this node's base.

Inspected before creating the companion test:

| Requirement | Existing coverage | Assessment / new gap |
|---|---|---|
| Original 44-step journey behavior and complete outcomes | `reference/booking_resale_admission/test_commerce_journey_receipts.py`: `CommerceJourneyReceiptTests.test_complete_output_bytes`, `test_step_mapping`, `test_source_pins`, output/step/pin mutation controls | Sufficiently covered; reuse decoder/pin helpers, do not duplicate FSM tests. |
| Temporal (39 steps / 3 cases) | `test_commerce_temporal_vectors.py`: `CommerceTemporalVectorTests.test_complete_output_bytes_and_references`, `test_published_schemas_and_unbound_reads`, `test_order_and_mapping_mutations_fail`, `test_pins_fail_before_execution` | Sufficiently covered within pack. |
| Historical receipts (54 steps / 5 cases) | `test_commerce_historical_receipt_vectors.py`: `CommerceHistoricalReceiptVectorTests.test_complete_output_bytes_and_references`, `test_published_schemas_and_unbound_reads`, `test_order_and_mapping_mutations_fail`, `test_non_mutation_guard_detects_extra_effects` | Sufficiently covered within pack; first receipt differs from later diagnostics. |
| Resale/admission ordering (29 steps / 2 cases) | `test_commerce_entry_resale_order_vectors.py`: `CommerceEntryResaleOrderVectorTests.test_complete_output_bytes_and_references`, `test_published_schemas_sources_and_unbound_reads`, `test_output_order_identity_and_reference_mutations_fail`, `test_all_refusals_preserve_detached_snapshots` | Sufficiently covered within pack. |
| Bound issuance (25 steps / 2 cases) | `test_commerce_bound_issuance_vectors.py`: `CommerceBoundIssuanceVectorTests.test_complete_output_bytes_and_references`, `test_existing_coverage_and_portable_gap`, `test_commit_is_separate_from_explicit_fresh_key_issuance`, `test_source_and_fixture_pins_fail_before_execution` | Sufficiently covered within pack. |
| Bound resale (49 steps / 3 cases) | `test_commerce_bound_resale_vectors.py`: `CommerceBoundResaleVectorTests.test_complete_output_bytes_and_references`, `test_existing_coverage_and_portable_gaps`, `test_commit_retains_rejection_until_explicit_fresh_key`, `test_source_and_fixture_pins_fail_before_execution` | Sufficiently covered within pack; rejected-key retention is process-local. |
| Six-family navigation, ordered case/step/action to unchanged binding index, exact input/output pins and outcome references, replay symbols | No companion exists | Not covered. Add `test_complete_index` and detached digest/reference, coverage and association controls. |
| Qualification/non-claims | `scripts/check_producer_qualification_tuple.py` and `validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`, normal and self-test modes; per-pack read checks | Partially covered. Add strict companion metadata/type/non-claim controls; preserve source records. |
| Byte preservation | Locked blob tests and per-pack source pins | Partially covered. Capture before/after byte inventory of all pre-existing tracked files except the two authorized navigation documents. |

All test filenames without a directory above are under
`reference/booking_resale_admission/`. New controls validate detached copies or
injected readers; they never mutate existing artifacts or write goldens.
