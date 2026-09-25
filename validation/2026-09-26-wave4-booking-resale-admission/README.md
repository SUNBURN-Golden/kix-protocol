# Wave 4 — booking, resale, and admission gates

Offline check for the protocol gates in
`docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`.
This note does not revise the Task 005 charter and does not promote
ORIGINAL_32 labels. B01–B05, R01–R05, and P03 stay **설계중**.

## Command

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -v
```

Local run on Python 3.13.5: 11 tests, OK (`Ran 11 tests in 0.002s`).
That count is this run only. It is not CI for the commit that records this
note, and it is not a payment-provider, chain-finality, or admission-routing result.

Implementation base at session start: `9e2dad654d7c6e46efade803018ef3e2cfea5e0a`
(`origin/main` after Wave 3 PR #60).
The Task 005 charter base remains `729a106add049ad1a75b90f99c00b6e0ccb8a67d`.
This wave does not rebase that charter.

## What the mock does

`reference/booking_resale_admission/mock_gates.py` keeps an in-memory fixture:

- B01–B05: register a show, hold one slot, bind an order at the registered primary price, record an injected 32-byte payment fact, then emit issuance evidence (`kind = 1`). The same binding posts once.
- R01–R04: the current holder lists once, an injected resale fact matches the listing amount, and accept moves the holder and version. The face split uses the integer division already in `rights::accept_sale`.
- R05, inside this process only: a second live listing, a live admission, a reused show-local payment ref, or a stale version is rejected.
- P03: a listed gate authorizes a 32-byte request, and consume moves the right to `CONSUMED` once.

Every response is `MOCK_GATE_ONLY`. Role labels are not authenticated principals.

## What it does not claim

- No organizer, seller, or gate authentication, and no chain grant or durable order.
- No quote approval, discount, or call into `reference/v0.3-rc1/commerce.py`.
- No live Toss/PG call, bank debit, refund, or failure compensation after a payment fact.
- No seller payout and no call into the Wave 3 settlement mock.
- No Sui object, no new Move module, and no `zk_gate` / `consume_private` proof.
- No production admission routing. `CONSUMED_ONCE` is not `core._admit`.
- No product frontend, kernel edit, or F04 credit.
- Passing these tests does not mean B01–B05, R01–R05, or P03 are implemented.
