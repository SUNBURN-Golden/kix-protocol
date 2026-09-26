# Wave 5 — F04 credit-advance mock

Offline check for the credit-advance contract in
`docs/contracts/CREDIT_ADVANCE_F04.md`.
This note does not revise the Task 005 charter and does not promote
ORIGINAL_32 labels. F04 and E06 stay **설계중**.

## Command

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -v
```

Local run on Python 3.13.5: 7 tests, OK (`Ran 7 tests in 0.002s`).
That count is this run only. It is not CI for the commit that records this
note, and it is not a lending, bank, or license result.

Implementation base at session start: `4ec0f93255b9be1715784f1d2a5edde411cc96c6`
(`origin/main` after Wave 4 PR #61).
The Task 005 charter base remains `729a106add049ad1a75b90f99c00b6e0ccb8a67d`.
This wave does not rebase that charter.

## What the mock does

`reference/credit_advance_f04/mock_credit.py` keeps an in-memory fixture.
It does not import the Wave 3 settlement module and does not post into that book.
Tests pass `MockSettlement.view` dicts in-process.

- A note copies one claim view and reserves an amount up to the sum of unpaid obligation faces (`outstanding`). The same binding posts once.
- `confirmed_cash` and `recovery_due` are copied onto the view and are not added to that ceiling.
- An open refund whose bearer is still `UNDEFINED` is rejected. A full-gross reclass leaves unpaid face at 0, so a new note does not fit.
- The first accepted note freezes that claim's view. A later different view is rejected.
- Releasing a note only drops the in-memory reservation. The same id does not become `NOTED` again.
- `attempt_execution` always raises and does not change the note. Disburse, repay, and debit are refused as real funds. Accrual, license, foreclosure, priority, and perfection are refused as an undefined product.

Every view is `MOCK_CREDIT_F04_ONLY`. Role labels are not lenders or licensees.

## What it does not claim

- No real credit, regulated lending product, license, or registration.
- No interest, fee, APR, tenor, repayment schedule, delinquency, or loss allocation.
- No priority, collateral perfection, disposal, or revenue assignment.
- No bank debit, live Toss/PG call, payout, or observed repayment.
- No admission right and no legal debtor.
- No durable ledger, kernel change, or Move change.
- Passing these tests does not mean F04 or E06 are implemented.

## Credit depth FSM — 2026-09-26

The sections above are the Wave 5 record and stay as written.
The same discover command now also loads `test_credit_fsm.py`.

Local run on Python 3.13.5: 20 tests, OK (`Ran 20 tests in 0.026s`).
Seven are the original predicate tests. Thirteen are the lifecycle machine.
That count is this run only. It is not CI for the commit that records this
note, and it is not a lending, bank, or license result.

`mock_credit.py` remains the open-face reservation predicate.
`credit_fsm.py` is the acceptance machine in front of it.
A draw notes the Wave 5 reservation. A repay reduces mock outstanding
exposure only. Close calls `release_note` after that exposure is zero, which
returns reserved face and still leaves `repayment_observed` false.
F04 and E06 stay **설계중**.
No `protocol_contract.json` command was added. The contract-only OpenAPI
catalogue is unchanged. There is no live HTTP server and no PG or bank call.
Commerce-apps are not in this change.

The contract table is `docs/contracts/CREDIT_ADVANCE_F04.md` §7.
The accepted path is:

```text
OFFERED --approve--> APPROVED --draw--> DRAWN --close--> CLOSED
   \                    \                  \ \
    reject               cancel             repay (phase stays DRAWN)
     \                    \                  default, while exposure remains
      REJECTED            CANCELLED          DEFAULTED
```

`reject_unsupported("REPAY")` and `attempt_execution(kind="REPAY")` stay
`REAL_FUNDS_FORBIDDEN`. They are not the ledger `repay` command.
Interest, KYC, AML, risk-score, underwriting, accrual, license, foreclosure,
priority, and perfection stay `CREDIT_PRODUCT_UNDEFINED`.

Same idempotency key and same canonical arguments replay the first success
or the first rejection. A different body for that key is `IDEMPOTENCY_CONFLICT`.
The same `draw_id` does not increase exposure again. A different `draw_id`
after a draw is `DUPLICATE_DRAW`. Repayment notes apply once, in sequence order.
Accepted commands are the journal. `restore` rebuilds only those commands.
`reconcile` compares that replay and does not change the phase.

A bound draw reads an injected settlement view and requires `COMMITTED`
before `note_advance`. It does not call settlement commands.
`economic_finality_claimed`, `funds_executed`, and `bank_debit_observed` stay
false. A view that sets any of those true is rejected and creates no exposure.
Unbound draw is a mock ledger transition with `settlement_gate = UNBOUND`.

Ordered draw commands share the Wave 5 open-face ceiling.
`confirmed_cash` is not capacity. Partial repayment does not release the
reservation. Default keeps it. Close releases it only after outstanding
exposure is zero. Neither default nor close changes a resale holder, version,
or listing.

### Non-claims

- `matched: true` is equality of this process's journal and views.
- `state_digest` is a sha256 of that in-memory state, not a signature or chain commitment.
- `MOCK_COMMIT_OBSERVED` means the mock settlement phase was `COMMITTED`. It is not a disbursement.
- `outstanding_exposure` and `repaid_exposure` are mock ledger integers, not a repayment schedule, delinquency, or loss allocation.
- `approve` and `reject` do not underwrite, score risk, or decide KYC-AML.
- `default` does not foreclose, perfect collateral, or transfer ticket ownership.
- Direct `MockCredit` calls remain the Wave 5 fixture. They do not pass this phase gate.
- Passing these tests does not mean F04 or E06 are implemented.
