# Wave 3 — F01–F03 settlement mock

Offline check for the settlement contract in
`docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md`.
This note does not revise the Task 005 charter and does not promote
ORIGINAL_32 labels. F01, F02, F03, and P04 stay **설계중**.

## Command

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03 -v
```

Local run on Python 3.13.5: 10 tests, OK (`Ran 10 tests in 0.001s`).
That count is this run only. It is not CI for the commit that records this
note, and it is not a bank, payment-provider, or legal-finality result.

Implementation base at session start: `a2814923bc671889da49984a2c95964340a1506d`
(`origin/main` after Wave 2 PR #59).
The Task 005 charter base remains `729a106add049ad1a75b90f99c00b6e0ccb8a67d`.
This wave does not rebase that charter.

## What the mock does

`reference/settlement_f01_f03/mock_settlement.py` keeps an in-memory fixture:

- F01: one KRW claim, primary fee-bps split, payee face amounts, no spendable cash at recognition.
- F02: explicit settlement components. Confirmed cash is only the `amount` component. Distribution follows a caller-supplied payee order and leaves the shortfall as residual obligation.
- F03: a refund obligation ceiling. One full-gross binding reclassifies unpaid face versus already distributed amounts. A mock cancel acceptance reduces the refund balance and records a merchant adjustment outstanding.

Every view is `MOCK_SETTLEMENT_ONLY`. The same key with the same binding posts once.

## What it does not claim

- No legal debtor, creditor, or refund-debtor binding.
- No bank debit, live Toss/PG call, payout, or customer-credit confirmation.
- No right cancellation, collateral, admission, or external-return closure.
- No product revenue waterfall, resale split, partial-refund bearer, or cross-trade netting.
- No durable ledger, kernel change, Move change, or F04 credit.
- Passing these tests does not mean F01–F03 are implemented or that P04 settlement closure exists.
