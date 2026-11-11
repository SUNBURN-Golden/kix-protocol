# contract-error-code-coverage

Node: `plan-contract-error-code-coverage`. Adds `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` (139 rows over the four contract error-code tables), `scripts/check_contract_error_codes.py` (stdlib only, `--self-test`, `--emit`), three small negative-test files, and two lines in the stdlib step of `.github/workflows/protocol.yml`.
Issue: none. Depends on: `settlement-policy-deepening`, `booking-resale-admission-deepening`, `f04-mock-deepening`, `ai-delegation-contract-mock`. Audit floor A2. Not an ASTRA program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA or final task head SHA, and no exact-head CI run exists for this work; those belong in the pull request closure report (AGENTS.md section 11).

Observed `origin/main` = branch HEAD = `5587afb34cdf9df51b981bcea4a9507250e70528` (merge of #213), after `git fetch origin main`.

**This record and the map are a builder-authored reading, not an independent review and not an acceptance. No grade is raised, nothing is claimed for production, and the checker proves only that a code name appears on a raise path or in a test body.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `git diff --stat origin/main` over `reference/v0.3-rc1`, `runtime`, `.aiops`, `docs/tasks`, `docs/contracts`, `docs/decisions` is empty. Under `reference/` only three new `test_contract_error_codes.py` files exist; no existing file there changed.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` | New map. |
| `scripts/check_contract_error_codes.py` | New checker. |
| `reference/settlement_f01_f03/test_contract_error_codes.py` | New, 5 tests. |
| `reference/booking_resale_admission/test_contract_error_codes.py` | New, 18 tests. |
| `reference/ai_delegation/test_contract_error_codes.py` | New, 1 test. |
| `.github/workflows/protocol.yml` | Two added lines after the IM map checker lines. |
| `docs/README.md` | One index row. |
| `validation/2026-10-18-contract-error-code-coverage/README.md` | This record. |

## AGENTS.md section 7: existing coverage

Counts: SET=34 BRA=64 F04=16 AID=25, 139 rows (131 distinct strings; `INVALID_ID`, `INVALID_AMOUNT`, `CURRENCY_UNSUPPORTED`, `UNKNOWN_CLAIM` repeat across tables). The task text said about 110. Before this change 115 rows were RAISED and ASSERTED (sufficiently covered, test cited per row in the map) and 24 were raised but named by no test (not covered). F04 had no gap. After this change all 139 are RAISED and ASSERTED.

## Added tests (24 codes)

| File | Test | Code(s) closed |
|---|---|---|
| settlement | `test_negative_component_is_invalid_nonnegative` | `INVALID_NONNEGATIVE` |
| settlement | `test_policy_not_a_dict_is_policy_type` | `POLICY_TYPE` |
| settlement | `test_policy_key_set_must_match_is_policy_fields` | `POLICY_FIELDS` |
| settlement | `test_bad_payee_identifier_is_policy_payee` | `POLICY_PAYEE` |
| settlement | `test_reason_without_adjustment_is_adjustment_reason_unexpected` | `ADJUSTMENT_REASON_UNEXPECTED` |
| booking | `test_bad_version_is_version_type` | `VERSION_TYPE` |
| booking | `test_bad_clock_value_is_clock` | `CLOCK` |
| booking | `test_listing_expiry_outside_window_is_listing_window` | `LISTING_WINDOW` |
| booking | `test_unregistered_show_is_unknown_show` | `UNKNOWN_SHOW` |
| booking | `test_unregistered_order_is_unknown_order` | `UNKNOWN_ORDER` |
| booking | `test_same_reservation_id_other_slot_is_reservation_binding_conflict` | `RESERVATION_BINDING_CONFLICT` |
| booking | `test_order_on_cancelled_reservation_is_reservation_not_open` | `RESERVATION_NOT_OPEN` |
| booking | `test_payment_or_issue_on_aborted_order_is_order_not_open` | `ORDER_NOT_OPEN` |
| booking | `test_abort_of_issued_order_is_order_not_abortable` | `ORDER_NOT_ABORTABLE` |
| booking | `test_second_payment_ref_on_paid_order_is_order_payment_bound` | `ORDER_PAYMENT_BOUND` |
| booking | `test_wrong_primary_payment_amount_is_payment_amount_mismatch` | `PAYMENT_AMOUNT_MISMATCH` |
| booking | `test_same_issuance_id_other_order_is_issuance_binding_conflict` | `ISSUANCE_BINDING_CONFLICT` |
| booking | `test_same_transfer_id_other_listing_is_transfer_binding_conflict` | `TRANSFER_BINDING_CONFLICT` |
| booking | `test_same_admission_id_other_request_is_admission_binding_conflict` | `ADMISSION_BINDING_CONFLICT` |
| booking | `test_same_consume_id_other_request_is_consume_binding_conflict` | `CONSUME_BINDING_CONFLICT` |
| booking | `test_second_resale_payment_ref_is_listing_payment_bound` | `LISTING_PAYMENT_BOUND` |
| booking | `test_wrong_resale_payment_amount_is_resale_amount_mismatch` | `RESALE_AMOUNT_MISMATCH` |
| booking | `test_consume_with_other_request_is_admission_request_mismatch` | `ADMISSION_REQUEST_MISMATCH` |
| ai_delegation | `test_unknown_proposal_id_is_unknown_proposal_on_every_path` | `UNKNOWN_PROPOSAL` |

Fixtures are synthetic and copied in style from sibling tests; no new mock hook, policy value or product number. Where an accessor exists (`view`, `view_show`, `view_right`, `state_digest`) the test also checks the state is unchanged.

## Class B and class C findings

None. Every documented code (except the excluded `MOCK_INVARIANT`) was reached by an input. One characterization: `SETTLEMENT_FACE_FIELDS` (F04) is named in a test body only by the `assertIn` coverage guard at `test_credit_properties.py`; the seeded oracle in `credit_property_support.py` drives it. It counts as ASSERTED under the definition and carries the note `guard-only`; no test was added because the node says to add none for F04. Also, `POLICY_FEE_BPS`, `REFUND_BINDING_CONFLICT` (SET) and `INVALID_ID` (AID) are named only in property tests.

## Commands run

| Command | Result |
|---|---|
| `git fetch origin main; git rev-parse origin/main HEAD` | both `5587afb3...` |
| `git hash-object` of the two locked files, before and after | both blobs match |
| `python3 scripts/check_contract_error_codes.py` | exit 0: `SET=34 BRA=64 F04=16 AID=25 rows=139 RAISED=139 ASSERTED=139 COVERED=139 CLASS_B=0 CLASS_C=0` |
| `python3 scripts/check_contract_error_codes.py --self-test` | exit 0, `self-test: pass`; detects removed row, duplicated row, misspelled code (both sides), stale counts, wrong cell count, unknown status, MOCK_INVARIANT row, removed raise site, removed asserting test, Raised set to no, dangling path, dangling symbol, citation outside suite, under v0.3-rc1, not a derived site, added contract code, removed heading, COVERED without test, CLASS_B with none note, CLASS_C on asserted code; plus extractor positive controls |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t ...` | 48 tests OK |
| same for `booking_resale_admission` | 75 tests OK |
| same for `credit_advance_f04` | 48 tests OK |
| same for `ai_delegation` | 70 tests OK |
| `check_docs_index.py`, `check_status_register.py`, each plain and `--self-test` | exit 0 (docs index ok: scanned=162 indexed=127 allowlisted=35; capability register ok: paths=249 ev_ids=15 original32=32) |
| `check_rs_profile_traceability`, `check_read_model_source_map`, `check_i12_proof_ids`, `check_delegation_layer_matrix`, `check_rs_predicate_evidence_map`, `check_rs_im_evidence_map`, each plain and `--self-test` | exit 0 |
| `git diff -U0 .github` | exactly two added lines |

Not run: Cargo, Sui, ZK, Node jobs and `ktx-kernel.yml`; no `runtime/` byte changed.

## Non-claims

Not an independent review. No production, durability or grade claim. ASSERTED shows a name in a test body, not what the test asserts or that all callers can reach it. The FSM-added code tables (F04 section 7.8, booking sections 10.8 and 11.6) and any table outside the four named are not read. Exact-head CI is not yet known.
