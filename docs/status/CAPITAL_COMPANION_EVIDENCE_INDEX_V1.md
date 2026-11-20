# Capital companion evidence index v1

This [JSON index](CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json) is non-normative,
read-only discovery metadata for `kix-capital`. It associates ten
consumer pack families and two supporting observer fixtures. It defines no
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
| **Total** | | **438** | **122** |

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

The seven families with setup and history associate `setup_steps` with
`setup_results`, and `steps` with `history`. `observations` contain
`scenario_id`, `kind`, `ref`, and `step_id` for `step_snapshot` observations.
They reference existing initial/per-step snapshots and, where present,
`restore_checks`. They are supplemental observations, never input commands.

The refusal pack's input and output pins name the same self-contained file.
Its entries have `case_id`, `observer`, `input_ref` (whole case),
`arguments_ref`, `keywords_ref`, and `result_ref` (`expected_error`). Omitted
keywords remain `{}`; null, booleans and JSON floating values stay distinct.

The two supporting records pin `settlement_variance_v1.json` and
`shared_exposure_v1.json`. Each associates six scenario identities with whole
input scenarios and `/expected` results, existing contract-test symbols,
F04 §§7.11–7.12 headings and the guide's limitations section. They are supporting
evidence, outside the ten consumer families.

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
introduced. Shared exposure uses compatible same-point snapshots, counts
capacity once per distinct claim, and requires an explicit caller-supplied
synthetic limit. Caller labels do not bind legal debtors. Tolerance/limit
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
