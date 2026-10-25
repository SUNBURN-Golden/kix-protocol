# Primary price/fee contract clause-to-test evidence map

**Builder-authored map, not a review or an acceptance; no grade change.**
Coverage applies only to scoped offline mock assertions. This map selects no
product value, command, enforcement location or operating policy.

## 0. Basis

Node `plan-primary-price-fee-contract-clause-eviden`; immutable input is the
supervisor-provided node specification/design, with no issue or matching task
file under `docs/tasks/`. Historical Task 005 is wave context only.
Observed cached `origin/main`, base and initial task HEAD are all
`92d08e755dfe362ed224112c8dada6c5fcea17d4`, on branch
`agent/kix-plan-primary-price-fee-contract-clause-eviden`.
The supervisor prohibits network actions, so fetch was not run and remote
freshness is unverified. No local base delta was observed.

Source: [MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md](../contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md),
revision **초안 0.1**. Its historical node boundaries are not this map node's scope.
All numbered headings (§0–§8), PF-C01..PF-C05 and nine §6 open items are mapped.
Test bodies were inspected before assigning coverage: the two primary boundary
modules, mock gate/settlement anchors, split properties, reservation rejection
atomicity and lifecycle anchors. The [#288 validation record](../../validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md)
names these tests. Its frozen-core differential is **NOT_MADE**, not cross-layer
equivalence. Historical results are not this run.

## 1. Vocabulary

| Status | Rule |
|---|---|
| COVERED | Cited tests exercise the row's scoped offline assertions; gap is `none`. |
| PARTIAL | At least one test citation with a specific remaining gap. |
| NOT_COVERED | Evidence is `none`; missing or unopened scope is named. |
| OPEN | Gap names `DECISION_REQUIRED · Astra` or `UNDETERMINED`, with the contract's owner verbatim. |

Owner `none` assigns nobody. Other clause owners are contract-verbatim parts,
separated by semicolons; open-item owners retain the entire contract cell.
These labels map existing evidence; they neither approve policy nor promote the
capability register. PF-C01/PF-C02 are PARTIAL across layers even though their
scoped offline arithmetic/binding has sufficient deterministic coverage.

## 2. Clause map

| Clause | Heading | Paraphrase | Evidence | Status | Open or missing | Owner |
|---|---|---|---|---|---|---|
| §0 | 범위와 상태 | Structural draft only; choice A is the contract node delivery boundary, not the final enforcement choice. | none | OPEN | DECISION_REQUIRED · Astra: final enforcement location remains UNDETERMINED. | Astra |
| §1 | 관측된 기준선 | Booking price checks and settlement floor split are offline baseline evidence. | `reference/booking_resale_admission/test_mock_gates.py::GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay`; `reference/settlement_f01_f03/test_mock_settlement.py::SettlementMockTests.test_f01_fee_floor_zero_fee_and_rejected_policies` | PARTIAL | Move Show/issuance, frozen lifecycle/core and extended ShowControl field observations are not tested by these citations; frozen reference citations are excluded. | none |
| §2 | 용어 | Existing KRW money bounds and integer bps limits are checked; direct issuance is outside paid-price binding. | `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_invalid_amount_rejected_with_contract_code`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_invalid_bps_rejected_with_contract_code`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_non_money_amounts_rejected_before_price` | PARTIAL | No on-chain price/fee field or per-show freezing evidence; booking mock has no primary fee field. Direct issuance and fee inclusion are not established. | Astra |
| §3 | 술어 | PF-C01/PF-C02 have offline evidence; predicate ids add no commands or on-chain enforcement. | `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_off_price_amounts_rejected_at_boundaries`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_non_money_amounts_rejected_before_price`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_seeded_prices`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_boundary_goldens`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_contract_section5_examples`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_seeded_grid` | PARTIAL | On-chain predicates and PF-C03..PF-C05 remain untested or open; see their rows. | Astra |
| PF-C01 | 가격 바인딩 | Paid mock binding rejects off-price and invalid money inputs; exact-price retry succeeds without rejection traces. | `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_off_price_amounts_rejected_at_boundaries`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_non_money_amounts_rejected_before_price`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_seeded_prices`; `reference/booking_resale_admission/test_mock_gates.py::GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay`; `reference/booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_unbound_issue_is_memory_evidence_without_economic_finality`; `reference/booking_resale_admission/test_reservation_rejection_atomicity.py::ReservationRejectionAtomicityTests.test_confirm_price_mismatch_leaves_no_trace` | PARTIAL | On-chain NOT_COVERED: no fixed primary price equality check or EPayment mismatch test; direct issuance excluded. Enforcement location is DECISION_REQUIRED · Astra. | Astra |
| PF-C02 | 분할 | Floor fee plus residual conserves gross; zero obligations are suppressed; goldens, seeded grids and Fraction oracle cover mock arithmetic. | `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_boundary_goldens`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_contract_section5_examples`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_seeded_grid`; `reference/settlement_f01_f03/test_settlement_properties.py::SplitPropertyTests.test_a_boundary_grid_of_gross_and_fee_bps`; `reference/settlement_f01_f03/test_settlement_properties.py::SplitPropertyTests.test_a_seeded_gross_and_fee_bps`; `reference/settlement_f01_f03/test_mock_settlement.py::SettlementMockTests.test_f01_fee_floor_zero_fee_and_rejected_policies` | PARTIAL | On-chain u128 primary split is NOT_COVERED. General residual priority is UNDETERMINED; enforcement location is DECISION_REQUIRED · Astra. | Astra |
| PF-C03 | 시점 (제안, Astra 대기) | Primary allocation timing is a proposal: mint only, never reservation/cancellation; no event schema is selected. | none | OPEN | DECISION_REQUIRED · Astra: primary allocation event/command schema and its timing tests remain absent. | Astra |
| PF-C04 | 환불 연결 | Refund linkage describes gross last_amount; it cannot establish bank receipt or fee-return policy. | none | OPEN | DECISION_REQUIRED · Astra: fee on refund remains UNDETERMINED; no allowed Python citation proves on-chain RefundDutyRequested.amount linkage. | Astra |
| PF-C05 | 격리 | Resale organizer/platform bps stay confined to accept_sale and separate from the primary fee. | none | NOT_COVERED | No Python test asserts primary/resale bps isolation; frozen Move accept_sale evidence is excluded. Any enforcement change is DECISION_REQUIRED · Astra. | Astra |
| §4 | 집행 선택지 | A/B/C are alternatives; this map chooses no enforcement location. | none | OPEN | DECISION_REQUIRED · Astra: final A/B/C choice is UNDETERMINED; B needs rs-1 contract work and C touches the preserved 16-slot reference. | Astra |
| §5 | 산술 예시 | All four synthetic examples check fee, residual, roles and zero-line suppression. | `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_contract_section5_examples` | COVERED | none | none |
| §6 | 열린 항목 | Nine product, protocol, legal/accounting and provider questions retain the contract status and owner below. | none | OPEN | DECISION_REQUIRED · Astra for product/protocol choices; legal/accounting and provider answers remain UNDETERMINED. | Astra; 사용자, 법률·회계 담당; 토스, 사용자 |
| §7 | 기존 커버리지 | Reuse contract mock anchors and #288 boundary/property evidence; admission and resale citations are lifecycle evidence only. | `reference/booking_resale_admission/test_mock_gates.py::GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay`; `reference/booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_unbound_issue_is_memory_evidence_without_economic_finality`; `reference/settlement_f01_f03/test_mock_settlement.py::SettlementMockTests.test_f01_fee_floor_zero_fee_and_rejected_policies`; `reference/booking_resale_admission/test_reservation_rejection_atomicity.py::ReservationRejectionAtomicityTests.test_confirm_price_mismatch_leaves_no_trace`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_off_price_amounts_rejected_at_boundaries`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_non_money_amounts_rejected_before_price`; `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests.test_seeded_prices`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_boundary_goldens`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_contract_section5_examples`; `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests.test_seeded_grid`; `reference/settlement_f01_f03/test_settlement_properties.py::SplitPropertyTests.test_a_boundary_grid_of_gross_and_fee_bps`; `reference/settlement_f01_f03/test_settlement_properties.py::SplitPropertyTests.test_a_seeded_gross_and_fee_bps`; `reference/booking_resale_admission/test_admission_fsm.py::AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`; `reference/booking_resale_admission/test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential` | PARTIAL | Frozen rights_tests.move citations are excluded and not Python. Lifecycle tests do not prove primary fee predicates, chain execution or economic finality. | none |
| §8 | 비청구 | Non-claims preserve policy, attestation/funds and authority boundaries; mocks establish no operating assurance. | none | NOT_COVERED | Bank/PG receipt, chain finality, durability, legal/tax treatment, production readiness, Move/localnet and the 16-slot profile are not verified here. | none |

Counts: COVERED=1 PARTIAL=6 NOT_COVERED=2 OPEN=5

## 3. On-chain layer

These additional layer rows do not duplicate the clause rows. No frozen path is
an executable citation, and no Move or Sui execution was performed.

| Layer | Evidence | Status | Open or missing | Owner |
|---|---|---|---|---|
| chain:PF-C01 | none | NOT_COVERED | Fixed primary price equality and EPayment mismatch enforcement absent; DECISION_REQUIRED · Astra on location. | Astra |
| chain:PF-C02 | none | NOT_COVERED | Primary fee/residual u128 split absent; DECISION_REQUIRED · Astra on location. | Astra |

On-chain: NOT_COVERED=2

## 4. Open items (contract §6)

Labels follow contract order. Item names are the contract cell's first sentence;
status and entire owner cells are copied verbatim. No value is filled.

| Item | Contract item | Contract status | Evidence | Status | Open | Owner |
|---|---|---|---|---|---|---|
| O1 | `primary_price`의 실제 값 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra |
| O2 | `primary_fee_bps`의 실제 값 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra |
| O3 | 수수료 수취인과 역할 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra |
| O4 | 환불 때 수수료를 돌려주는지 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra. 정산 쪽 후속은 `settlement-policy-deepening` |
| O5 | 수수료가 가격에 포함되는지, 가격 위에 더해지는지 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra |
| O6 | 집행 위치 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra. B는 `rs-1`의 `RIGHTS_SCALE_PROFILE` 개정. C는 16슬롯 참조를 건드리므로 그 결정 뒤에만 착수한다 |
| O7 | 1차 배분 사건 또는 명령 | `DECISION_REQUIRED · Astra` | none | OPEN | DECISION_REQUIRED · Astra: no decision or external answer supplied. | Astra |
| O8 | 수수료의 법률·세무·회계 처리 | `UNDETERMINED — 사용자와 법률·회계 담당` | none | OPEN | UNDETERMINED — 사용자와 법률·회계 담당: no decision or external answer supplied. | 사용자, 법률·회계 담당 |
| O9 | 토스 경로의 수수료 정산 동작 | `UNDETERMINED — 토스와 사용자` | none | OPEN | UNDETERMINED — 토스와 사용자: no decision or external answer supplied. | 토스, 사용자 |

Open items: OPEN=9

## 5. Limits and follow-up

Actual price and bps values, fee recipient, inclusion/on-top treatment, fee on
refund, enforcement location and primary allocation schema remain
**UNDETERMINED**, with the contract's DECISION_REQUIRED · Astra and named external
routes intact. Neither the 100000/500 adapter fixtures nor any synthetic test
number is product policy. General residual priority stays UNDETERMINED under the
settlement contract. No contract, test, mock, FSM, Move, register or grade changes.

This is builder-authored, source-informed evidence, not independent acceptance.
No production durability, distributed fencing, bank exactly-once, funds receipt,
chain finality, legal/tax compliance, performance or production readiness is
claimed. No new contract violation or undefined semantics is established here.

The stdlib checker validates structure, counts and direct TestCase symbol
existence without importing tests or reading frozen reference files. It cannot
assess semantic adequacy. Non-author review remains separate. Register checker
inventory synchronization belongs to a follow-up node; this node leaves it alone.
See the [actual validation record](../../validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md).
