# Capital companion evidence index v1

This [JSON index](CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json) is non-normative,
read-only discovery metadata for `kix-capital`. It associates twenty-four
consumer pack families and 12 supporting entries across two observer fixtures. It defines no
protocol interface, client, command, endpoint or execution authority. The
[existing field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md) and unchanged
[F04 contract](../contracts/CREDIT_ADVANCE_F04.md) retain their original scope.

## Coverage inventory recorded before adding tests

Replay paths in this table are relative to `reference/credit_advance_f04/`.

| Acceptance requirement | Existing coverage | Before this index |
| --- | --- | --- |
| Settlement-credit boundary behavior | `test_settlement_credit_boundary.py::SettlementCreditBoundaryTests.test_vector_pack_replays_exactly` | Sufficient |
| Economics-credit composition | `test_economics_credit_consumer_vectors.py::EconomicsCreditConsumerTests.test_public_snapshot_bytes_and_pins` | Sufficient |
| Observer refusals | `test_capital_refusal_vectors.py::CapitalRefusalVectorTests.test_rejections_match_and_preserve_inputs` | Sufficient |
| Operation replay | `test_capital_operation_replay_vectors.py::CapitalOperationReplayVectorTests.test_complete_history_vectors` | Sufficient |
| Terminal capacity | `test_capital_terminal_capacity_vectors.py::CapitalTerminalCapacityVectorTests.test_complete_history_vectors` | Sufficient |
| Cross-claim history | `test_capital_cross_claim_history_vectors.py::CapitalCrossClaimHistoryVectorTests.test_complete_history_vectors` | Sufficient |
| Refund composition | `test_capital_refund_composition_vectors.py::CapitalRefundCompositionVectorTests.test_complete_history_vectors` | Sufficient |
| Supporting variance/shared-exposure arithmetic | `test_settlement_variance_contract.py::SettlementVarianceContractTests.test_all_scenarios_replay_to_expected`, `test_shared_exposure_contract.py::SharedExposureContractTests.test_all_scenarios_replay_to_expected` | Sufficient |
| Exact seven-family membership and artifact pins | Individual replay suites pin artifacts; consolidated inventory absent | Partial |
| Scenario/case and ordered-step associations | Individual replays preserve order; central navigation absent | Partial |
| Replay symbols and guide sections | No consolidated resolver | Not covered |
| Missing/duplicate/reordered entries; crossed same-operation references | No companion index controls | Not covered |
| Stale pins and false qualification claims | Existing per-pack pins; no index claim validator | Not covered centrally |
| Original bytes and document discovery | Existing source-pin tests and document/discovery checkers | Partial; before/after manifest required |

The new standard-library `test_capital_companion_evidence_index.py` validates
associations and detached negative controls. It does not duplicate economic
replays or import existing `TestCase` classes. Existing replay suites continue
to establish their own behavior predicates. Actual commands and preservation
checks are in the [builder record](../../validation/2026-11-18-plan-plan-capital-companion-evidence-index/README.md).

## Metadata and associations

The record has exactly `record_schema_version`, `record_kind`, `normative`,
`consumer`, `qualification`, `nonClaims`, `packs` and `supporting_evidence`.
Version is `kix-capital-companion-evidence-index/1`; kind is
`NON_NORMATIVE_COMPANION_EVIDENCE_INDEX`; `normative` is false.
Paths are repository-relative. Each artifact pin has `path`, raw-byte `sha256`
and `gitBlob` (SHA-1 over the Git blob header and raw bytes). No self-hash is
used. Digests identify bytes and do not authenticate them.

| Family | Shape | Entries | Supplemental observations |
| --- | --- | ---: | ---: |
| settlement_credit_boundary | ordered_steps | 98 | 0 |
| economics_credit_consumer | scenario_inputs | 54 | 0 |
| capital_refusal | self_contained_refusals | 51 | 0 |
| capital_operation_replay | setup_and_history | 53 | 31 |
| capital_terminal_capacity | setup_and_history | 63 | 37 |
| capital_cross_claim_history | setup_and_history | 27 | 8 |
| capital_refund_composition | setup_and_history | 33 | 11 |
| capital_refund_identity | setup_and_history | 24 | 13 |
| capital_reconcile_freshness | setup_and_history | 15 | 8 |
| capital_predraw_terminal | setup_and_history | 20 | 14 |
| capital_later_statement | setup_and_history | 13 | 6 |
| capital_mixed_checkpoint_views | self_contained_comparisons | 4 | 0 |
| capital_omitted_exposure_members | self_contained_comparisons | 4 | 0 |
| capital_payee_order_recovery | self_contained_comparisons | 2 | 0 |
| capital_offsetting_claim_gaps | self_contained_comparisons | 2 | 0 |
| capital_commerce_refund_checkpoints | self_contained_comparisons | 3 | 0 |
| capital_overlapping_exposure_groups | self_contained_comparisons | 4 | 0 |
| capital_resale_distribution_checkpoints | self_contained_comparisons | 3 | 0 |
| capital_group_sum_boundary | self_contained_comparisons | 3 | 2 |
| capital_draw_refusal_after_restore | self_contained_comparisons | 2 | 0 |
| capital_equal_gross_claim_binding | self_contained_comparisons | 2 | 0 |
| capital_refund_versus_repayment | self_contained_comparisons | 2 | 0 |
| capital_statement_component_identity | self_contained_comparisons | 2 | 2 |
| capital_repayment_attribution | self_contained_comparisons | 2 | 2 |
| **Total** | | **486** | **134** |

The eighth family pairs refund and cancellation-acceptance inputs with their
receipts, errors and current snapshots. For the coverage map and an example of
a historical receipt, see the [refund identity field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-refund-and-cancellation-acceptance-identity-histories).

The ninth family pairs eight setup calls and seven history calls with their
complete envelopes. Its eight snapshots let readers compare the historical
reconcile receipts with fresh local matches and the current variance after a
full-gross refund. [Reconcile freshness field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-reconcile-freshness-vectors)

Each pack has `id`, `shape`, `input`, `output`, `replay_test`, `guide_refs`,
`limitations`, ordered `entries` and `observations`. Replay references contain
`path` and `symbol` (`Class.method`, checked by Python AST without importing the
replay suite). Guide references contain `path` and an exact existing `heading`.
Membership, keys and JSON scalar types are checked against fixed expectations.

Paired entries contain `scenario_id`, `section`, `step_id`, `input_ref` and
`result_ref`, plus `operation`/`target` only where the source defines them.
References are `path#/JSON/pointer`; results point to the complete `result`
envelope, including refusals. Identity uses family, scenario, section and
position, so two valid same-operation pointers are not interchangeable.

Boundary entries pair `scenarios[i].steps[j]` with the corresponding output
step's `result`. Economics inputs have no steps array: every entry points to
`scenarios[i].inputs` and declares `input_granularity: scenario`. Its expected
ordering follows the existing replay recipe: create, capture confirmation,
settle, each advance's offer/approve/bind/draw, frozen checkpoint, then each
history action and its checkpoint. P/F/FD keep their distinct order.

The eight families with setup and history associate `setup_steps` with
`setup_results`, and `steps` with `history`. `observations` contain
`scenario_id`, `kind`, `ref`, and `step_id` for `step_snapshot` observations.
They reference existing initial/per-step snapshots and, where present,
`restore_checks`. They are supplemental observations, never input commands.

The refusal pack's input and output pins name the same self-contained file.
Its entries have `case_id`, `observer`, `input_ref` (whole case),
`arguments_ref`, `keywords_ref`, and `result_ref` (`expected_error`). Omitted
keywords remain `{}`; null, booleans and JSON floating values stay distinct.

Each comparison pack uses one file for both pins. Its entries have
`case_id`, `input_ref` (whole case) and `result_ref` (complete
`expected_result` envelope). The exposure comparison cases use ordered
`view_refs` to identify individual snapshots. The payee order comparison
uses shared `input_ref` and `baseline_ref` fields within its fixture to
identify the R1 input and fee-first result in the two pinned source files.

The two supporting records pin `settlement_variance_v1.json` and
`shared_exposure_v1.json`. Each associates six scenario identities with whole
input scenarios and `/expected` results, existing contract-test symbols,
F04 §§7.11–7.12 headings and the guide's limitations section. They are supporting
evidence, outside the consumer pack families.

### P1 pre-draw rejection and cancellation

`capital_predraw_terminal` indexes `P1_reject_cancel_before_draw`. This
synthetic, process-local history captures rejection and cancellation before the
first credit note, replays of the original outcomes, and a separate mock draw
that uses the full available capacity.

| Pin under `reference/credit_advance_f04/fixtures/` | SHA-256 | Git blob |
| --- | --- | --- |
| [Input `capital_predraw_terminal_v1.json`](../../reference/credit_advance_f04/fixtures/capital_predraw_terminal_v1.json) | `538f9cb0123b518c34f2a5ff3916433ac69acd093c961943d04f314178f1e58d` | `908c358e10a644769ca659de1dd1531741d47fd6` |
| [Output `capital_predraw_terminal_vectors_v1.json`](../../reference/credit_advance_f04/fixtures/capital_predraw_terminal_vectors_v1.json) | `2f08fc5d4d066c3a6dd5b774799fdcaddcd9b2e947d643b6d5eba7a4d6e7fb98` | `e86897b912054b2e7f7d392e1da0c8a9df116d0a` |

The setup entries come first, followed by the history entries. Each range
uses ascending `{j}` and each result selects the full success or error envelope.

| Entries | Input fragment | Result fragment |
| --- | --- | --- |
| Setup (`j = 0…6`) | `#/scenarios/0/setup_steps/{j}` | `#/scenarios/0/setup_results/{j}/result` |
| History (`j = 0…12`) | `#/scenarios/0/steps/{j}` | `#/scenarios/0/history/{j}/result` |

The output observations list `#/scenarios/0/history/{j}/snapshot` for
`j = 0…12` in history order, then `#/scenarios/0/initial_snapshot`.
Pre-draw shared-exposure grouping remains contract-undefined. A
`shared_exposure` value of `null` records that the observer was skipped.

Replay symbol `CapitalPredrawTerminalVectorTests.test_complete_history_vectors`
in [`test_capital_predraw_terminal_vectors.py`](../../reference/credit_advance_f04/test_capital_predraw_terminal_vectors.py).
[P1 field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-pre-draw-rejection-and-cancellation-companion-p1)

### L1 later settlement statement after a requester refund

`capital_later_statement` indexes `L1_later_statement_after_requester_refund`.
The history follows the later statement and its original-key replay through the
next distribution against the same frozen credit claim.

| Pin under `reference/credit_advance_f04/fixtures/` | SHA-256 | Git blob |
| --- | --- | --- |
| [Input `capital_later_statement_v1.json`](../../reference/credit_advance_f04/fixtures/capital_later_statement_v1.json) | `1d0e7e806258b3bdaca08da0d4486fcdaf119fdb41470ac48f4df4602821ae4b` | `5cd80de37aad4c4ed8aca10208606f79e7856e49` |
| [Output `capital_later_statement_vectors_v1.json`](../../reference/credit_advance_f04/fixtures/capital_later_statement_vectors_v1.json) | `8d9949eec525ade2369437dde20f11f3aaa0a70b1d0a387af36bd64f33294317` | `bbbd19e8ba7db7f7617a5fe0742e1663aa336cff` |

| Entries | Input fragment | Complete result fragment |
| --- | --- | --- |
| Setup (`j = 0…7`) | `#/scenarios/0/setup_steps/{j}` | `#/scenarios/0/setup_results/{j}/result` |
| History (`j = 0…4`) | `#/scenarios/0/steps/{j}` | `#/scenarios/0/history/{j}/result` |

The six observations point to `#/scenarios/0/history/{j}/snapshot` in history
order, followed by `#/scenarios/0/initial_snapshot`. The index validator checks
position even when the statement and replay arguments or snapshots are equal.
Replay symbol `CapitalLaterStatementVectorTests.test_complete_history_vectors`.
[Replay verifier](../../reference/credit_advance_f04/test_capital_later_statement_vectors.py) · [L1 field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-later-settlement-statement-vectors)

### Mixed-checkpoint comparisons

`capital_mixed_checkpoint_views` indexes `repay_mixed`, `repay_same`,
`close_mixed` and `close_same` in that order. The mixed repayment pair reports
70,000 KRW outstanding and its same-checkpoint control reports 55,000 KRW.
The mixed close pair returns `VIEW_BINDING_CONFLICT` and its control reports
30,000 KRW. Read `#/cases/{i}` for each case and
`#/cases/{i}/expected_result` for the complete outcome. The replay verifies
the underlying source digests and exact view pointers.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_mixed_checkpoint_views_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_mixed_checkpoint_views.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-mixed-checkpoint-views)

### Omitted exposure member comparisons

`capital_omitted_exposure_members` indexes `e1_full`, `e1_omit_second`,
`e2_full` and `e2_omit_second` in that order. The pairs hold the fixture
checkpoint, group label and limit fixed. The case and complete result are at
`#/cases/{i}` and `#/cases/{i}/expected_result`. Each case points to the
group label, limit and selected frozen views in the pinned shared-exposure
fixture. Callers supply group membership. Completeness applies to the fixture
scenario and cannot be certified for a real pool by the observer.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_omitted_exposure_members_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_omitted_exposure_members.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-omitted-exposure-members)

### Payee order recovery comparison

`capital_payee_order_recovery` indexes `r1_fee_first` and `r1_residual_first`
in that order. Each case at `#/cases/{i}` declares its distribution order.
Its result at `#/cases/{i}/expected_result` records both the full-refund and
mock-acceptance checkpoints. Each order produces 10,000 KRW of recovery due,
with different payee attribution. The validator rejects cross-wired result
pointers even though both resolve to complete envelopes.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_payee_order_recovery_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_payee_order_recovery.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-payee-order-recovery)

### Offsetting claim gap comparison

`capital_offsetting_claim_gaps` indexes two complete F04 §7.11 observations
from the pinned settlement-variance fixture. The input and result fragments
below are relative to the comparison pack.

| Case | Claim / trade | Source scenario | Input fragment | Complete result fragment |
| --- | --- | --- | --- | --- |
| `v4_claim_gap` | `claim-v4` / `trade-v4` | `V4_positive_observation_sign` | `#/cases/0` | `#/cases/0/expected_result` |
| `v6_claim_gap` | `claim-v2` / `trade-v2` | `V6_boundary_plus_one_out_of_tolerance` | `#/cases/1` | `#/cases/1/expected_result` |

The two cases report +40,000 and −40,000 KRW. Each is outside its own
synthetic tolerance. `#/diagnostic_sum_krw` records their arithmetic sum.
`CapitalOffsettingClaimGapsTests.test_claim_pair` verifies the pinned views,
original tolerances and complete attributed results. The index validator
rejects an exchange of the two resolvable result pointers.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_offsetting_claim_gaps_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_offsetting_claim_gaps.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-offsetting-claim-gaps)

### Commerce refund checkpoints

`capital_commerce_refund_checkpoints` links one frozen F04 claim to three
Commerce receipts. The input and result fragments are relative to the
comparison pack. Each `receipt_ref` points into the raw-byte-pinned Commerce
receipt file.

| Case | Input fragment | Complete result fragment | Commerce receipt fragment |
| --- | --- | --- | --- |
| `commit` | `#/cases/0` | `#/cases/0/expected_result` | `#/cases/0/steps/9/receipt` |
| `bind-refund` | `#/cases/1` | `#/cases/1/expected_result` | `#/cases/0/steps/14/receipt` |
| `observe-mock-acceptance` | `#/cases/2` | `#/cases/2/expected_result` | `#/cases/0/steps/15/receipt` |

The validator rejects swapped receipt pointers even though both resolve to
the same claim and produce zero variance. The refund component remains
`NOT_BOUND`.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_commerce_refund_checkpoints_vectors_v1.json) · [Commerce receipts](../../reference/booking_resale_admission/fixtures/commerce_linked_refund_receipts_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_commerce_refund_checkpoints.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-commerce-refund-checkpoints)

### Overlapping exposure group comparisons

`capital_overlapping_exposure_groups` indexes four complete outcomes at the
same E3 checkpoint. Both artifact pins identify the comparison pack. Each
case points to ordered views, the group label and the limit in the pinned E3
fixture. The fragments below are relative to the comparison pack.

| Case | Input fragment | Complete result fragment |
| --- | --- | --- |
| `e3_ab` | `#/cases/0` | `#/cases/0/expected_result` |
| `e3_bc` | `#/cases/1` | `#/cases/1/expected_result` |
| `e3_abc` | `#/cases/2` | `#/cases/2/expected_result` |
| `e3_duplicate_b` | `#/cases/3` | `#/cases/3/expected_result` |

The replay verifies the 30,000 KRW overlap and the `VIEW_INVALID` refusal.
The index validator rejects exchanges of valid case or result pointers.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_overlapping_exposure_groups_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_overlapping_exposure_groups.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-overlapping-exposure-groups)

### Resale distribution checkpoints

`capital_resale_distribution_checkpoints` pairs three ordered Commerce
receipts with complete results. The input and result fragments are relative
to the same pinned comparison pack. Receipt fragments point into the pinned
booking-resale journey receipts.

| Case | Input fragment | Complete result fragment | Commerce receipt fragment |
| --- | --- | --- | --- |
| `settle-resale-commit` | `#/cases/0` | `#/cases/0/expected_result` | `#/steps/23/receipt` |
| `accept-A` | `#/cases/1` | `#/cases/1/expected_result` | `#/steps/24/receipt` |
| `distribute-resale` | `#/cases/2` | `#/cases/2/expected_result` | `#/steps/25/receipt` |

The two settlement receipts supply outstanding obligations for the same
frozen F04 claim. The middle receipt records ownership. The index rejects
an exchange of the commit and distribution receipt pointers even when both
resolve and the detached pack has matching new digests.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_resale_distribution_checkpoints_vectors_v1.json) · [Commerce receipts](../../reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_resale_distribution_checkpoints.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-resale-distribution-checkpoints)

### Group sum boundary

`capital_group_sum_boundary` uses the same pinned file for input and output.
Its ordered `source_credit_view` observations point to the complete frozen
views at `#/credit_views/0` (1,000,000,000,000 fixture KRW drawn) and
`#/credit_views/1` (1 fixture KRW drawn).

| Case | Input fragment | Complete result fragment |
| --- | --- | --- |
| `at_total` | `#/cases/0` | `#/cases/0/expected_result` |
| `one_below` | `#/cases/1` | `#/cases/1/expected_result` |
| `single_view_overflow` | `#/cases/2` | `#/cases/2/expected_result` |

Both success cases reference the same views in the same order and record
1,000,000,000,001 fixture KRW drawn and outstanding. The refusal references
the first view and supplies the overrides for a detached copy. The validator
rejects exchanged success-result pointers and exchanged source-view pointers.
Replay symbol `CapitalGroupSumBoundaryTests.test_group_sum_boundary`.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_group_sum_boundary_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_group_sum_boundary.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-group-sum-boundary)

### Draw refusal after restore

`capital_draw_refusal_after_restore` uses the same pinned file for input and
output. Both cases start at `#/before`, with identical accepted journals and
zero exposure after S1's `s1-commit`.

| Case | Input fragment | Complete result fragment | Outcome |
| --- | --- | --- | --- |
| `original` | `#/cases/0` | `#/cases/0/expected_result` | `CreditError` with `SETTLEMENT_NOT_COMMITTED`, zero appends |
| `restored` | `#/cases/1` | `#/cases/1/expected_result` | New mock draw of 10,000 fixture KRW, one append |

Refused calls leave no accepted journal entry. Equal journals and state
digests cannot establish whether the original received a refused call.
The validator rejects exchanged result pointers even when both resolve.
Replay symbol `CapitalDrawRefusalAfterRestoreTests.test_draw_refusal_pair`.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_draw_refusal_after_restore_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_draw_refusal_after_restore.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-draw-refusal-after-restore)

### Equal-gross claim binding

`capital_equal_gross_claim_binding` pins the same comparison pack as input
and output. Both branches offer the full S2 claim and submit the same draw
request. F04 §7.5 checks claim identity even when the committed settlements
share currency and gross.

| Case | Settlement binding | Case fragment | Complete result fragment | Outcome |
| --- | --- | --- | --- | --- |
| `matching` | `stl-s2` | `#/cases/0` | `#/cases/0/expected_result` | One mock draw, 10,000 fixture KRW outstanding |
| `crossed` | `stl-s1` | `#/cases/1` | `#/cases/1/expected_result` | `SETTLEMENT_BINDING_CONFLICT`, zero outstanding and zero appends |

The replay compares the complete advance views, credit journals, original
offer faces and both settlement journals. The index validator rejects
exchanged result pointers even when both resolve.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_equal_gross_claim_binding_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_equal_gross_claim_binding.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-equal-gross-claim-binding)

### Refund versus repayment

`capital_refund_versus_repayment` pins the same comparison pack for input and
output. Both cases start at the pack's `before` snapshot, with a 4,000 KRW
requester refund bound to `claim-1` and a 10,000 KRW mock advance drawn.

| Case | Case fragment | Complete result fragment | Refund outstanding (fixture KRW) | Credit outstanding (fixture KRW) |
| --- | --- | --- | ---: | ---: |
| `mock_acceptance` | `#/cases/0` | `#/cases/0/expected_result` | 2,500 | 10,000 |
| `repayment_note` | `#/cases/1` | `#/cases/1/expected_result` | 4,000 | 8,500 |

Each result reference resolves to the complete accepted command envelope.
Each case also includes an `after` snapshot with that branch's shared-exposure
observation and both journals. The index rejects an exchange of the two result
references even when both resolve to valid envelopes.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_refund_versus_repayment_vectors_v1.json) · [Replay verifier](../../reference/credit_advance_f04/test_capital_refund_versus_repayment.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-refund-versus-repayment)

### Statement component identity

The `capital_statement_component_identity` input and output pins identify the same
[vector pack](../../reference/credit_advance_f04/fixtures/capital_statement_component_identity_vectors_v1.json).
Its SHA-256 is `cae9854cc5da29bb1d45bb2c9adf620821c822fafac09e838a1b05bce403a79e`
and its Git blob is `01e86fe9731f00e5b5ff145f425394437e65cd13`.

| Case | Input fragment | Complete result fragment | Observation fragment | Accepted journal fragment |
| --- | --- | --- | --- | --- |
| `fee` | `#/cases/0` | `#/cases/0/expected_result` | `#/cases/0/after` | `#/cases/0/after/settlement/journal/6` |
| `held` | `#/cases/1` | `#/cases/1/expected_result` | `#/cases/1/after` | `#/cases/1/after/settlement/journal/6` |

Each `statement_observation` binds its case to the accepted `part-2` journal
entry. The index rejects an exchange of the two `journal_ref` values even
though both entries resolve and both branches report equal claim totals.
Replay symbol `CapitalStatementComponentIdentityTests.test_statement_component_identity`.
[Replay verifier](../../reference/credit_advance_f04/test_capital_statement_component_identity.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-statement-component-identity)

## Repayment attribution

The self-contained pack pins the H1 input and output and identifies the starting
snapshot and original repayment instruction. Each case has an `input_ref` and
a `result_ref` to its complete accepted receipt. Each `repayment_observation`
links both H1 commit receipts, the target draw receipt and the original A1
repayment receipt. Its case-local links identify the target frozen claim,
accepted repayment journal entry, shared-exposure observation and conflict
result. [Vector pack](../../reference/credit_advance_f04/fixtures/capital_repayment_attribution_vectors_v1.json) · [H1 receipts](../../reference/credit_advance_f04/fixtures/capital_cross_claim_history_vectors_v1.json)

| Case | H1 draw receipt | Frozen claim | Accepted journal entry |
| --- | --- | --- | --- |
| `repay_a1` | `#/scenarios/0/setup_results/11/result` | `claim-h1-a` | `#/cases/0/after/credit/journal/12` |
| `repay_b1` | `#/scenarios/0/setup_results/19/result` | `claim-h1-b` | `#/cases/1/after/credit/journal/12` |

Both observations report 110,000 fixture KRW outstanding. The index checks the
journal target for each case and rejects crossed journal links even when both
links resolve. [Replay verifier](../../reference/credit_advance_f04/test_capital_repayment_attribution.py) · [Field guide](ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-repayment-attribution) · [Builder validation](../../validation/2026-11-28-plan-capital-repayment-attribution/README.md)

## Read-only consumption

Run this inline Python from the repository root; it reads existing files only.
There is no new CLI, subprocess client, endpoint or runtime:

```python
import hashlib, json
from pathlib import Path

root = Path('.')
index = json.loads((root / 'docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json').read_text())
pack = next(p for p in index['packs'] if p['id'] == 'capital_refusal')
raw = (root / pack['input']['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest() == pack['input']['sha256']
case = json.loads(raw)['cases'][0]
print(case['case_id'], case['keywords'], case['expected_error'])
```

This example identifies pinned evidence; it establishes no consumer acceptance
or execution authority. Run the focused standard-library validator with:

```sh
python3 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_capital_companion_evidence_index.py
```

## Limits and remaining gates

Original source-informed Class B limitations remain. Frozen faces are not
revalued by refunds, distribution or acceptance. Refund obligations, recovery,
PG adjustment and credit repayment are separate; no netting mechanics are
introduced. Shared exposure checks agreement on same-claim binding fields,
counts capacity once per distinct claim, and requires an explicit
caller-supplied synthetic limit. The caller supplies group membership, selects
the checkpoints and establishes their freshness. Caller labels do not bind legal debtors. Tolerance/limit
success grants no authority. Observations and refund components remain
`NOT_BOUND`, `repair=NONE`, fail-closed and non-mutating.

External `kix-capital` acceptance remains **UNVERIFIED**. Product limits remain
**UNDETERMINED—Astra** and legal responsibility **UNDETERMINED—User/legal**.
The refund identity entry extends the original seven-family inventory. The
producer implementations, previous packs and supporting fixtures retain their original bytes.
No new policy, protocol behavior, durable recovery, real
funds/PG/bank/KYC, public endpoints, Sui testnet/mainnet, storage engine,
coin/TIX, secrets or production runtime is introduced or tested.
A2 non-author exact-head review and exact-head KTX/KIX CI remain supervisor
delivery gates. Local validation is not merge authorization.
