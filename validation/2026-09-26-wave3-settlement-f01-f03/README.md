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

## Settlement depth FSM — 2026-09-26

The sections above are the Wave 3 record and stay as written.
The same discover command now also loads `test_settlement_fsm.py`.

Local run on Python 3.13.5: 20 tests, OK (`Ran 20 tests in 0.011s`).
Ten are the original predicate tests. Ten are the lifecycle machine.
That count is this run only. It is not CI for the commit that records this
note, and it is not a bank, payment-provider, or legal-finality result.

`mock_settlement.py` remains the economic predicate.
`settlement_fsm.py` is the acceptance machine in front of it.
That is how this supersedes the Wave 3 pointer-only mock: the arithmetic
is unchanged, and a settlement case now has an explicit phase before those
predicates run. F01, F02, F03, and P04 stay **설계중**.
No `protocol_contract.json` command was added. The contract-only OpenAPI
catalogue is unchanged. There is no live HTTP server and no PG or bank call.

The contract table is `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` §9.
The accepted path is:

```text
INITIATED --authorize--> AUTHORIZED --capture--> CAPTURED --commit--> COMMITTED
     \                        \
      fail / cancel            fail / cancel
       \                        \
        FAILED                   FAILED
        CANCELLED                CANCELLED
```

`COMMITTED` is not terminal. Later statements, distribution, refund binding,
and mock cancel acceptance stay on `COMMITTED`. `FAILED` and `CANCELLED`
reject later mutations. `reconcile` replays the journal and does not change
the phase. `reject_external` always refuses a provider or bank attempt.

Same idempotency key and same canonical arguments replay the first success
or the first rejection. A different body for that key is `IDEMPOTENCY_CONFLICT`.
Accepted commands are the journal. `restore` rebuilds only those commands, so
a lost success response is a duplicate and a rejected command is absent.

### Non-claims

- `matched: true` is equality of this process's journal and views.
- `state_digest` is a sha256 of that in-memory state, not a signature or chain commitment.
- `FAILED` and `CANCELLED` are mock terminals, not P04 closure and not external-return closure.
- Mock authorization does not call a provider. `provider_authorization_executed` stays false.
- Direct `MockSettlement` calls remain the arithmetic fixture and the face snapshot the F04 mock reads. They do not pass this phase gate.
