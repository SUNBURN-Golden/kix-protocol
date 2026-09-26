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

## Reservation and ticketing depth — 2026-09-26

The sections above are the Wave 4 record and stay as written.
The same discover command now also loads `test_reservation_fsm.py`.

Local run on Python 3.13.5: 22 tests, OK (`Ran 22 tests in 0.022s`).
Eleven are the original gate tests. Eleven are the lifecycle machine.
That count is this run only. It is not CI for the commit that records this
note, and it is not a venue, payment-provider, or admission-routing result.

Observed `origin/main` at session start: `85145eb33799a7c712890ff81708def8a7d61ee5`.
The Wave 4 gate file and its base SHA are unchanged. B01–B05, R01–R05, and P03 stay **설계중**.

`mock_gates.py` remains the slot, price, payment-fact, and admission predicate.
`reservation_fsm.py` is the acceptance machine in front of it.
The machine does not add resale or credit commands. Direct `MockGates` calls still do not pass this phase gate.
No `protocol_contract.json` command was added. The contract-only OpenAPI
catalogue is unchanged. There is no live HTTP server, no venue adapter, and no PG or bank call.

The contract table is `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` §9.
The accepted path is:

```text
hold --> HELD --> confirm --> CONFIRMED --> observe_payment --> PAYMENT_NOTED --> issue --> ISSUED
          |                    |
          release              cancel
          |                    |
          RELEASED             CANCELLED

ISSUED --> authorize_admission --> ADMISSION_AUTHORIZED --> consume --> CONSUMED
```

Expiry does not free a slot. `release` from `HELD` does, including after expiry.
`cancel` after a payment fact is `COMPENSATION_UNDEFINED`. `cancel` after issue is `CANCEL_AFTER_ISSUE`.
A second consume is `ALREADY_CONSUMED`. One slot has one occupying hold.

Same idempotency key and same canonical arguments replay the first success
or the first rejection. The replay body is the first response snapshot.
`view` is the current phase. A different body for that key is `IDEMPOTENCY_CONFLICT`.
Accepted commands are the journal. `restore` rebuilds only those commands.

### Settlement hook

`issue` never sets `economic_finality_claimed`.
Unbound issue is memory evidence only (`settlement_gate = UNBOUND`).
Bound issue reads `view` on an injected settlement machine and does not call settlement commands.
It is refused unless that view is `COMMITTED`, KRW, the same gross as the order, and every finality flag on that view is false.
The success flag is `mock_settlement_commit_observed`. That records a mock phase observation.
It does not move the settlement machine, grant admission, or execute funds.
`MOCK_COMMIT_OBSERVED` is not a deposit. Restore the settlement journal first when a bound issue is in the reservation journal. The reservation journal does not freeze a commit the settlement view no longer shows.

### Non-claims

- `matched: true` is equality of this process's journal and views.
- `state_digest` is a sha256 of that in-memory state, not a signature or chain commitment.
- `RELEASED`, `CANCELLED`, and `CONSUMED` are mock terminals, not production admission closure.
- `CANCEL_AFTER_ISSUE` does not refund and does not return inventory.
- A frozen issue snapshot is not the current right. After consume, `view` shows `CONSUMED` and version 2.
- No resale listing, transfer, credit advance, live HTTP server, or commerce-apps change.

## Resale depth — 2026-09-26

The sections above stay as written.
The same discover command now also loads `test_resale_fsm.py`.

Local run on Python 3.13.5: 29 tests, OK (`Ran 29 tests in 0.051s`).
Eleven are the original gate tests. Eleven are the reservation lifecycle machine.
Seven are the resale lifecycle machine.
That count is this run only. It is not CI for the commit that records this
note, and it is not a marketplace, payment-provider, venue-reissue, or chain-finality result.

Observed `origin/main` at session start: `a47828dd4517c5a7397e09eb6b563a64e4265c82`.
The Wave 4 gate file, the reservation machine, and their base SHAs are unchanged.
B01–B05, R01–R05, and P03 stay **설계중**.

`mock_gates.py` remains the listing, holder, price, and payment-fact predicate.
`resale_fsm.py` is the acceptance machine in front of the resale surface.
`reservation_fsm.py` does not gain list, hold, payment, or transfer commands.
Direct `MockGates` calls still do not pass this phase gate.
No `protocol_contract.json` command was added. The contract-only OpenAPI
catalogue is unchanged. There is no live HTTP server, no marketplace transport,
no KYC, no venue credential reissue, and no PG or bank call.

The contract table is `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` §10.
The accepted path is:

```text
eligible issued ticket
  --> list_resale --> LISTED --> observe_resale_payment --> PAYMENT_NOTED
                         |
                         hold_buy (optional)
                         |
                         BUY_HELD
  --> accept_resale --> TRANSFERRED --> close --> CLOSED

LISTED or BUY_HELD --> cancel_listing --> CANCELLED
```

`adopt_issued` copies an already issued in-memory right into this machine.
It does not run the reservation lifecycle. A bound reservation source must
already be `ISSUED` or `ADMISSION_AUTHORIZED` with an `ACTIVE` right.
`CANCELLED` is `TICKET_CANCELLED`. A consumed right is `ALREADY_CONSUMED`.
`HELD` before issue is `TICKET_NOT_ISSUED`.

One live listing per right. A second live listing is `RIGHT_SALE_LOCKED`.
The same listing id does not return to `LISTED` after accept or cancel.
The same transfer id does not bump `version` again.
A different transfer id on that listing is `ILLEGAL_TRANSITION`, or
`TERMINAL_IMMUTABLE` after `close`.
Seller label and version are checked at list and at transfer.
Expiry, holder drift, and version drift reject the transfer and leave the
holder and version unchanged.

`hold_buy` names only the listing's recipient. Another buyer is
`RECIPIENT_MISMATCH`, or `BUYER_HOLD_LOCKED` when a hold is already in force.
Seller cancel and buyer hold resolve in command order inside this process.
That order is not a thread schedule and not cross-channel exclusion.
`cross_channel_exclusive` stays false.
Cancel after a resale payment fact is `COMPENSATION_UNDEFINED`.

### Settlement hook

`accept_resale` never sets `economic_finality_claimed` or `venue_credential_reissued`.
Unbound accept is the in-memory holder and version change only (`settlement_gate = UNBOUND`).
Bound accept reads `view` on an injected settlement machine and does not call settlement commands.
It is refused unless that view is `COMMITTED`, KRW, the same gross as the listing, and every finality flag on that view is false.
The success flag is `mock_settlement_commit_observed`. That records a mock phase observation.
It does not move the settlement machine, pay the seller, or execute funds.
A rejected transfer key keeps that rejection after the settlement view later becomes `COMMITTED`.
`MOCK_COMMIT_OBSERVED` is not a deposit. Restore the settlement journal first when a bound transfer is in the resale journal. The resale journal does not freeze a commit the settlement view no longer shows.
If a reservation source is bound, restore that journal to the state the resale commands re-read. The resale journal does not freeze the reservation phase.

### Presentation

Accept changes the holder label and adds one to `version`. `generation` stays 1.
The right id does not change. The slot stays `ISSUED`.
`prior_presentation_valid` is false after transfer.
`view_presentation` reports `matches_current_right` false for the previous holder and version, and false while a live listing is attached.
That comparison is not venue entry and not credential reissue.

### Non-claims

- `matched: true` is equality of this process's journal and views.
- `state_digest` is a sha256 of that in-memory state, not a signature or chain commitment.
- `CLOSED` and `CANCELLED` are mock terminals for that listing id, not production marketplace closure.
- Face split integers are not a seller payout and are not posted into the settlement book.
- No live marketplace, KYC, venue credential reissue, credit advance, or commerce-apps change.
