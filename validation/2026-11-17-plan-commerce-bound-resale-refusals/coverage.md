# Existing coverage and residual portable gaps

Node: `plan-commerce-bound-resale-refusals`. Coverage mapped before adding tests.
All paths in the following table are relative to `reference/booking_resale_admission/`.
Existing files remain byte-identical; their exact pins are in the new receipt pack.

| Requirement | Existing deterministic coverage | Classification before this node | New evidence |
|---|---|---|---|
| Bound resale refuses committed amount mismatch | `test_resale_fsm.py::ResaleFsmTests.test_bound_transfer_waits_for_mock_commit_and_reconciles` | sufficiently covered at FSM level; portable history not covered | `committed-resale-amount-mismatch`: committed gross 10001 versus listing 8000, exact `SETTLEMENT_AMOUNT_MISMATCH`, five-machine preservation |
| Failed settlement blocks transfer | Same source test, its FAILED branch | sufficiently covered at FSM level; portable history not covered | `failed-settlement-blocks-transfer`: explicit fail reason, bound transfer `SETTLEMENT_NOT_COMMITTED`, seller/version/journals preserved |
| Original rejected transfer key remains rejected after commit; explicit fresh key transfers once | Same source test, AUTHORIZED refusal and post-commit original-key replay | sufficiently covered at FSM level; portable history not covered | `rejected-transfer-after-commit`: explicit refused replay, explicit fresh-key command, explicit accepted replay; retained seller/version 1 until fresh command |
| Captured refusal followed by committed success | `fixtures/commerce_journey_conformance_v1.json` / `fixtures/commerce_journey_receipts_v1.json`: `accept-A-before-commit → settle-resale-commit → accept-A` | sufficiently covered | Cited and inventoried; no duplicate captured-to-committed success case |
| Canonical full receipt comparison, strict decoding and source pinning | `test_commerce_journey_receipts.py` | partially covered: reusable infrastructure, other histories | Reuse `_decode`, `_pin`, compare entire new output bytes; no writer mode |
| Detached diagnostics and historical first receipts | `test_commerce_historical_receipt_vectors.py`; `commerce_historical_*`: issuance after consumption, transfer after closure, distributions/refunds, settlement key conflicts | partially covered: transfer success/replay, not these bound refusals | Reuse `_snapshot`, `_views`, `_assert_views`; all five machine state/digest/journals around every new refusal |
| Expiry and stale ownership | `test_commerce_temporal_vectors.py`; `commerce_temporal_*`: paid expiry, stale transferred presentations, expired authorization replacement | sufficiently covered for those predicates; residual settlement-bound histories not covered | Reuse strict `_assert_paths`; no expiry duplicate |
| Resale/admission ordering | `test_commerce_entry_resale_order_vectors.py`; `commerce_entry_resale_order_*`: listing cancellation then entry, entry/consumption then listing refusal | sufficiently covered for those predicates; residual settlement-bound histories not covered | Inventory and pin only; no admission execution added |
| Settlement-bound issuance and retained rejected issuance key | `test_commerce_bound_issuance_vectors.py`; `commerce_bound_issuance_*`: issuance after commitment and amount mismatch | sufficiently covered for reservation issuance; residual resale histories not covered | Adapt validator pattern locally; no pinned helper refactor |
| Reads/catalogue and consumer boundaries | Journey conformance plus producer tuple / consumer binding checkers | partially covered: reusable boundaries | Check all 13 read names absent from host/catalogue; preserve index bytes; applicable checks run unchanged |

New suite: `test_commerce_bound_resale_vectors.py`. Complete output/reference,
coverage, commitment/key, separate-fact and refusal-preservation tests exercise
all three input histories. Mutation controls change error codes, receipt fields,
scalar types, snapshots, digests, journals, references, step/case order and source
pins. Recomputed input pins do not bypass independent ordering, error, replay,
key, schema and journal assertions. Public-command injections add an effect at
every refusal, transfer during commitment and a replay effect. The controls must
raise assertions; none transiently mutate production or protected files.

Contract classification: §§10.5–10.7 and settlement §9 define the observed
behavior and match it (A). No explicit contract violation found. No newly
undefined contract behavior is assigned semantics. Existing uncertainty remains:
rejected-key retention is process-local and is not restored from accepted
journals; diagnostic hashes are not durable or finality proofs. This is
source-informed verification, not clean-room independent qualification.
