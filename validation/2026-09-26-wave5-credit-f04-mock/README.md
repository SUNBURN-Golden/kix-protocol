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
