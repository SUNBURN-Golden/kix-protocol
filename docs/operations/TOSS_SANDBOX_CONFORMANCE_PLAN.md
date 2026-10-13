# Toss sandbox conformance plan

Status: document-only plan. No Toss call, no credential, no tunnel, no account.
Node: `toss-sandbox-conformance-plan`.
Canonical dependencies, both already merged: `k1-adapter-event-identity`
([ADAPTER_EVENT_IDENTITY](../contracts/ADAPTER_EVENT_IDENTITY.md) draft 0.1, pull request #124)
and `toss-method-expansion-review`
([TOSS_METHOD_EXPANSION_REVIEW](../reviews/TOSS_METHOD_EXPANSION_REVIEW.md), merged 2026-10-05).
This file feeds the pending node `k-provider-sandbox`
([pending catalogue](../decisions/PROGRAM_ROADMAP_20260930_PENDING.json), id at line 626).
That node's promotion text asks for a confirmed provider scope and a sandbox-account-use
approval. This plan does not give that approval.

This file is a plan. It adds no code, test, contract, command, or policy value.
It does not amend [PG_TOSS_CARD_PROFILE](../contracts/PG_TOSS_CARD_PROFILE.md),
[STATE_LIFECYCLE](../contracts/STATE_LIFECYCLE.md), or
[FIRST_BATCH_OPEN_INPUTS](../contracts/FIRST_BATCH_OPEN_INPUTS.md).
The open-input line 「새로 실입력까지 완결된 행: 0」 stays as written there.

## 1. Status and boundary

[PROGRAM_DECISIONS_20260928 §5](../decisions/PROGRAM_DECISIONS_20260928.md)
keeps real funds and real PG, bank, and KYC calls locked until the Toss profile's
open items are confirmed, sandbox conformance evidence exists, and the User
approves. [PROGRAM_ROADMAP_20260930 §5](../decisions/PROGRAM_ROADMAP_20260930.md)
names this node as the plan for that sandbox evidence.
[F04 real-funds criteria O-4](../decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md)
points at this plan and leaves the PG lock on that same §5 row.
Sandbox evidence leaves that lock closed.

[PG_TOSS_CARD_PROFILE §5](../contracts/PG_TOSS_CARD_PROFILE.md) records that the
2026-09-17 public note S5 describes domestic card checks in test mode with real
card data, that the card-authentication segment is interactive, and that a
fixture or a mocked lookup is a different activity from a Toss check.
[PG_TOSS_CARD_PROFILE §1](../contracts/PG_TOSS_CARD_PROFILE.md) records the
public-document confirmation date 2026-09-17 and says a later document change
needs a fresh read. This plan carries that date forward. A re-read is step 1
of `k-provider-sandbox`, and it is not done here.

Out of scope for this plan and for the case catalogue below:

- Bank sandbox and KYC sandbox.
- Adapter, inbox, and harness code. The harness shape belongs to `k-provider-sandbox`.
- Durable ACK custody. [STATE_LIFECYCLE §3](../contracts/STATE_LIFECYCLE.md) already
  says there is no inbox, and that sentence is not permission to ACK.
  Case TS-I stays blocked on `k-stage5-durable-tx`.
- Easy-pay and virtual-account execution. Those stay written questions until TM01
  is answered. Case TS-G records the questions only.
- A new fetch of Toss documentation.

The two locked kernel blobs and `reference/v0.3-rc1/**` stay unchanged.
[AGENTS.md](../../AGENTS.md) §5 and the program-decision §5 locks stay in force:
real funds, real PG, bank, and KYC calls, public endpoints, Sui testnet and
mainnet, R2 or a new replication, consensus, or storage engine, and a new
coin or TIX module.

## 2. Evidence classes and result vocabulary

Every future run labels each case with one class and one result. The class is
part of the result. A fixture pass stays a fixture pass.

| Class | Meaning |
|---|---|
| `F` | Offline fixture or mock. The record says `NOT Toss`. |
| `S` | Non-interactive sandbox call, after the entry criteria in §6. |
| `M` | Manual card authentication. [Profile §5](../contracts/PG_TOSS_CARD_PROFILE.md) separates this segment from an unattended check. |
| `W` | Written Toss answer, held outside Git (§5). |
| `X` | Blocked. The reason is the result, and the case is not run. |

| Result | When it is used |
|---|---|
| `PASS_SANDBOX` | The named sandbox case met its wording, on an approved test account, with the raw artifact in custody. |
| `FAIL` | The case ran and the wording failed. |
| `INCONCLUSIVE` | The case ran and the observation does not decide the wording. The gap stays visible. |
| `BLOCKED(reason)` | A §9 row or a missing Toss answer stops the case. |
| `NOT_RUN` | No attempt. |
| `FIXTURE_PASS` | An `F` case met its local wording. The label `NOT Toss` stays on the row. |

An absent account is `NOT_RUN` or `BLOCKED(no sandbox-account-use approval)`.
It is never a pass. A mock pass, a webhook-only pass, or a local-harness refusal
is never labelled Toss verification. `PASS_SANDBOX` is available only for a case
whose class is `S` or `M` and whose Toss answers for that row are in custody.
`W` cases close as written answers, not as `PASS_SANDBOX`.
`F` cases close as `FIXTURE_PASS` or `FAIL`.
`X` cases close as `BLOCKED(reason)`.

## 3. Case catalogue

Scope is the ordinary KRW card path in the Toss profile. Each row cites an
existing document. No pass rate, latency, repeat count, or wait is set here.
Correctness rows are binary.

`S` and `M` rows still depend on §6. Until those entry criteria hold, the
result is `BLOCKED` or `NOT_RUN`, including when the class above is `S` or `M`.

### 3.1 Identity and redelivery

Anchors: [ADAPTER_EVENT_IDENTITY §3 and §5](../contracts/ADAPTER_EVENT_IDENTITY.md)
rows 1–7, and TM04 in the [method review §3](../reviews/TOSS_METHOD_EXPANSION_REVIEW.md).

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-A1 | `S` | Identity §5 rows 1–3 | A redelivery, a second transmission of the same fact, or an administrator retry adds a raw-evidence reference only. It does not add an event item, an order, or an operation. | TM04 | `PASS_SANDBOX` when a sandbox redelivery keeps one item and the KIX rule accepts the same observation once. `FIXTURE_PASS` when only an offline fixture shows that rule (`NOT Toss`). `FAIL` when a second item, order, or operation appears. `INCONCLUSIVE` when the account cannot redeliver. |
| TS-A2 | `S` | Identity §5 row 4 | A repeated authenticated GET whose normalized fact is unchanged keeps the same event item and the same evidence hash. Snapshot time and GET count do not mint an item. | TM04 | `PASS_SANDBOX` when repeated GETs of one unchanged payment stay one item. `FIXTURE_PASS` for an offline repeat only. `FAIL` when a repeat mints an item. `INCONCLUSIVE` when the body changes for an unexplained reason; that observation is recorded and handed to TS-A5. |
| TS-A3 | `M` | Identity §5 row 6 | `DONE` then `CANCELED` is a new event item. The original capture item stays. Cancellation does not rewrite the original item as "no capture". | TM04, T05 · I05 | `PASS_SANDBOX` when the sandbox shows a new item for the cancel and the original capture remains. `FAIL` when the cancel reuses the capture item or erases it. `BLOCKED(manual card segment)` until §9 allows the interactive segment. `INCONCLUSIVE` when the status vocabulary is still the open T05 question. |
| TS-A4 | `M` | Identity §5 row 7 | One `cancels[]` entry is its own return item. It is not an update of the capture item's evidence hash, and it is not a batch of independent payments. | TM04, T05 · I05 | `PASS_SANDBOX` when a partial cancel is a separate item beside the capture. `FAIL` when the cancel is absorbed into the capture hash. `BLOCKED(manual card segment)` until §9 allows the interactive segment. |
| TS-A5 | `W` | Identity §4.5 option A and §5 row 5 | The field that is `ProviderFactKey` is observed. This plan does not choose it. The same key with different normalized content is `Conflict` and keeps the original capture. | TM04 | The written answer names the field, or says Toss has not confirmed one. No field is assumed in the meantime. `FAIL` is not available, because the case does not pick a field. A later `S` observation may record which field stayed put across redelivery; that observation stays `INCONCLUSIVE` as a key choice until the written answer exists. |
| TS-A6 | `F` | Identity §3 | The same operation with a different `paymentKey` is a binding conflict. No new operation and no new order are created, and the fact is not submitted as a new capture. | None for the local rule. TM04 still governs which provider ids are stable. | `FIXTURE_PASS` when an offline fixture shows the conflict and stops there (`NOT Toss`). `FAIL` when the fixture opens a second order or submits a new capture. `PASS_SANDBOX` is not a result of this row. |

### 3.2 Webhook signal, lookup, and errors

Anchors: [profile §4](../contracts/PG_TOSS_CARD_PROFILE.md),
[lifecycle §5.2 C1](../contracts/STATE_LIFECYCLE.md), I04, I08, and TM05.

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-B1 | `W` | Profile §4 | Signature fields, covered bytes, algorithm, and key scope for ordinary `PAYMENT_STATUS_CHANGED` stay the open I04 question. The payout and seller signature text is not copied onto the card webhook. | T04 · I04, TM05 | The written answer states the fields, or states that they are unconfirmed. Unconfirmed stays unconfirmed. A webhook body alone is not a fact, so a webhook-only check is never `PASS_SANDBOX`. Receipt of a webhook is `BLOCKED(no non-public delivery path)` until §9. |
| TS-B2 | `S` | Profile §4 | A signal is stored as a signal. The fact comes from an authenticated lookup on the server-fixed host and the account key already bound to the operation. The lookup URL and key are not taken from the webhook body. | T04 · I04, TM05 | `PASS_SANDBOX` when a harness-initiated lookup on the bound account matches the bound payment and the signal is kept as a separate artifact. `FAIL` when the signal is promoted to a fact, or when the lookup uses a URL or key from the body. The receipt half of a webhook stays `BLOCKED(no non-public delivery path)`. |
| TS-B3 | `S` | Profile §4 and lifecycle §5.2 C1 | A wrong account, wrong key, or wrong environment returns no fact for this binding. That response is not evidence that the payment is absent. | I02, I04 | `PASS_SANDBOX` when the wrong scope yields no fact and the original UNKNOWN stays. `FAIL` when the wrong scope is stored as absence or as a fact for this operation. `INCONCLUSIVE` when the body is an error that TS-B4 already classifies. |
| TS-B4 | `S` | Lifecycle §5.2 C1; profile §2 and §8 for key rotation | Timeout, 401, 403, 429, 5xx, and a parse error are not absence. A key rotation is recorded. It does not clear UNKNOWN and it does not justify a new key or a new PG for the same operation. | I08, TM05, T08 · I08 | `PASS_SANDBOX` when each injected error leaves UNKNOWN in place and a rotation drill does the same. `FAIL` when any of those outcomes is recorded as absence or triggers a new operation. `INCONCLUSIVE` when TS-Q4 says the sandbox will not inject the fault. `BLOCKED(TS-Q4)` until Toss says whether fault injection is allowed. |

### 3.3 Idempotency and lost responses

Anchors: [profile §2](../contracts/PG_TOSS_CARD_PROFILE.md) (public note S1) and
[lifecycle §5.2 C3](../contracts/STATE_LIFECYCLE.md).

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-C1 | `S` | Profile §2 | The same idempotency key and the same request reuse the first response. That reuse is not a fresh read of the latest payment state. | T08 · I08 | `PASS_SANDBOX` when the sandbox returns the first response for the same key and the same body. `FAIL` when KIX treats that reuse as a new capture or as a current-state proof. `INCONCLUSIVE` when the account's key lifetime differs from the public text; the difference is recorded under I08. |
| TS-C2 | `S` | Profile §2 | Toss's reaction to the same key with a different body is recorded and left as an observation. KIX rejects its own mismatched resend and does not mint a new key for that operation. | T08 · I08 | `PASS_SANDBOX` when the observation is stored and KIX keeps the original key. `FAIL` when KIX sends a new key or a new PG request for the same UNKNOWN operation. The Toss status code, whatever it is, stays an observation. |
| TS-C3 | `S` | Profile §2; lifecycle §5.2 C3 | `409` with `IDEMPOTENT_REQUEST_PROCESSING` means the remote request is still in progress. The operation stays UNKNOWN. | TM05 | `PASS_SANDBOX` when that response leaves UNKNOWN in place and C3 stays unmet. `FAIL` when the response is treated as success, absence, or a reason to send a new key. `BLOCKED(TS-Q4)` when the sandbox cannot produce this response. |
| TS-C4 | `S` | Identity §5 row 3; profile §2; lifecycle §5.2 C3 | A response lost after the server has succeeded is reconciled by an authenticated lookup on the original key. No new idempotency key and no new PG request are created. | TM05, T05-L · I05 | `PASS_SANDBOX` when the lookup finds the original result and the operation is not resent. `FAIL` when a lost response starts a second payment. `INCONCLUSIVE` when the lookup itself is a TS-B4 error; UNKNOWN stays. |
| TS-C5 | `S` | Lifecycle §5.2 C1 and C3 | A timeout leaves the operation UNKNOWN. The local sender stopping is not proof that the provider did nothing. No new key and no new PG request are created. | T05-L · I05 | `PASS_SANDBOX` when a timeout stays UNKNOWN and the original key is unchanged. `FAIL` when the timeout clears UNKNOWN or starts another provider request. `BLOCKED(TS-Q4)` when the sandbox cannot produce a timeout. |

### 3.4 Order, late capture, and the retry schedule

Anchors: [identity §5](../contracts/ADAPTER_EVENT_IDENTITY.md) rows 8–9 and
[profile §3](../contracts/PG_TOSS_CARD_PROFILE.md).

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-D1 | `S` | Identity §5 row 8 | Out-of-order snapshots are both kept. An earlier snapshot does not overwrite a later fact. Turning the kernel clock backward is `ClockRegression` and changes nothing. The kernel tests in §7 already cover that clock rule. | TM04, TS-Q1 | `PASS_SANDBOX` when two sandbox snapshots in reverse arrival order both remain and the later fact is intact. `FIXTURE_PASS` for the existing kernel clock tests (`NOT Toss`). `FAIL` when an older snapshot replaces a newer fact or the clock moves backward. |
| TS-D2 | `F` | Identity §5 row 9; profile §3 | A late capture after expiry keeps the capture, and the kernel reports `ReturnRequired` when the applied time is past expiry. `ReturnRequired` is not a completed refund. The kernel tests in §7 already cover this. This plan adds no second copy of those tests. | None for the kernel rule | `FIXTURE_PASS` cites the existing kernel tests (`NOT Toss`). `FAIL` is a failing run of those tests. A future sandbox attachment may record that a late provider fact arrived; that attachment is `S` evidence about Toss and does not relabel the kernel result. |
| TS-D3 | `X` | Profile §3, public note S2 | The published retry schedule is an observation target only. Whether the sandbox follows it is open. No wait, TTL, or pass threshold is set here. | TS-Q1, TS-Q2 | `BLOCKED(webhook delivery and observation budget)`. See §9. The case is not run from this plan. |

### 3.5 Amount, time text, and method

Anchors: [identity §4.4](../contracts/ADAPTER_EVENT_IDENTITY.md) and
[profile §6 and §7](../contracts/PG_TOSS_CARD_PROFILE.md).

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-E1 | `S` | Identity §4.4; profile §7 | KRW amounts stay integer won. A JSON number is not parsed through binary floating point. Scale, sign, and range stay attached to the fact. | T05 · I05 | `PASS_SANDBOX` when the raw amount text is stored and the normalized fact is an integer won value of that text. `FAIL` when the path uses binary floating point or drops a won. `FIXTURE_PASS` for an offline integer fixture (`NOT Toss`). |
| TS-E2 | `S` | Identity §4.4 and §6.1; profile §7 | Timestamp text is kept raw, with the offset when the payload has one. `createdAt` without an offset does not receive an assumed zone. `approvedAt` and `createdAt` stay separate fields. Occurrence, receipt, and apply time stay three times. | TS-Q1 | `PASS_SANDBOX` when both fields are stored as text and an offset is recorded only where the payload has one. `FAIL` when a zone is invented or one field overwrites the other. |
| TS-E3 | `S` | Profile §6; identity §5 row 11 | A method or type that differs from the requested ordinary-card path keeps the fact for reconciliation and grants no new right and no new send. A `card` object by itself does not classify the payment as the ordinary-card path. | TM02 | `PASS_SANDBOX` when a mismatched method is retained and no right is granted. `FAIL` when the mismatch is dropped or a right is issued. `INCONCLUSIVE` for easy-pay composition until TM02 is answered; that part stays on TS-G. |

### 3.6 Environment fence and account scope

Anchor: [identity §4.3](../contracts/ADAPTER_EVENT_IDENTITY.md) and
[profile §5](../contracts/PG_TOSS_CARD_PROFILE.md).

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-F1 | `F` | Profile §5 | A test key aimed at the live host, and a live key aimed at the sandbox host, are refused before any network send. The marker that distinguishes the keys is TS-Q3. This plan does not name that marker. | TS-Q3 | `FIXTURE_PASS` when the harness refuses both crossings before a send (`NOT Toss`). `FAIL` when either crossing reaches the network. `PASS_SANDBOX` is not a result of this row. `BLOCKED(TS-Q3)` until the marker is a written Toss answer, because the harness otherwise has nothing to recognize. |
| TS-F2 | `F` | Identity §4.3 | `PaymentRef` includes provider, account (MID), and environment. The two environments do not share one account alias. The kernel key is provider, account, and event id; environment is applied before that alias is cut. | T02 · I02 | `FIXTURE_PASS` when an offline fixture keeps the two environments apart (`NOT Toss`). `FAIL` when two environments share an alias. The real test MID is `BLOCKED(I02)` until Toss and the User name it. `PASS_SANDBOX` waits for that MID and is out of this `F` row. |

### 3.7 Other methods, custody, and ACK

| ID | Class | Anchor | KIX invariant | Toss answer | Result wording |
|---|---|---|---|---|---|
| TS-G | `W` | [Method review §1–§3](../reviews/TOSS_METHOD_EXPANSION_REVIEW.md) | Easy-pay and virtual-account execution stay questions. The ordinary-card absence path is not copied onto those methods. A fact for an unsupported method is kept for reconciliation and grants no new right. | TM01 through TM09 | The row records the written answers when they exist. Until TM01 is answered there is no execution case, so there is no `PASS_SANDBOX`. `BLOCKED(TM01)` for any run that would send those methods. |
| TS-H | `X` | Profile §5; pending `k-provider-sandbox` item 3 | Test-credential custody, deletion, and the audit path are confirmed before a sandbox run stores a credential. Git holds no secret. | I13 | `BLOCKED(custody owner unnamed)`. The check becomes a written custody record plus an audit once §9 names an owner. This plan does not create a credential. |
| TS-I | `X` | Lifecycle §3 | Provider raw evidence is durable before a provider ACK. There is no inbox in the current tree, so this case has nowhere to record that custody. | None. The blocker is `k-stage5-durable-tx`. | `BLOCKED(no inbox until stage 5)`. The case is not run. An in-memory residue is not this case. |

## 4. Toss answers needed

The questions already exist. This plan does not send them and does not edit
[the question sheet](../status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md) or
[the open inputs](../contracts/FIRST_BATCH_OPEN_INPUTS.md).
Owner strings below are the ones those documents already use, marked
`UNDETERMINED` because no answer is on file.
[Open inputs §4](../contracts/FIRST_BATCH_OPEN_INPUTS.md) says TM04 and TM05
have no row on the question sheet. This plan lists them as its own
sandbox-specific questions and leaves the sheet gap as a follow-up. A later
User-reviewed edit can add the sheet rows. This node does not.

Sheet rows T02, T03, T03-P, T04, T05, T05-L, and T08 are the open inputs
I02, I03, I04, I05, and I08 under the sheet's own pairing. They are one
question each, not a second set.

| ID | Unblocks | Owner | Stays blocked while unanswered |
|---|---|---|---|
| T02 · I02 | TS-F2 account scope, and the §6 test MID | `UNDETERMINED · 사용자·토스 계약/기술` | A named test MID and environment. Operating binding stays closed. |
| T03 · I03 | No ordinary-card TS row. Recorded because the sheet asks it. | `UNDETERMINED · 사용자·토스 영업` | Resale and finance receipt. |
| T03-P · I03 | No ordinary-card TS row. Related to TM07. | `UNDETERMINED · 토스` (profile §8, 미확인) | Split payout to several payees. |
| T04 · I04 | TS-B1 | `UNDETERMINED · 토스 기술` (질문지 5) | Webhook-only authentication. Unconfirmed is not treated as "no signature". |
| T05 · I05 | TS-A3, TS-A4, TS-E1 | `UNDETERMINED · 토스 기술` | Closing or deleting from a status string alone. |
| T05-L · I05 | TS-C4, TS-C5, and any claim that a lookup gap means absence | `UNDETERMINED · 토스 기술` | Treating a missing remote result as proof of absence. |
| T08 · I08 | TS-B4 rotation, TS-C1, TS-C2 | `UNDETERMINED · 토스, PG 계정 운영` | Retention, and UNKNOWN handling after a key change. The public 15-day idempotency text is not a retention period. |
| TM01 | TS-G execution | `UNDETERMINED · 사용자·토스 영업/계약` | Easy-pay and virtual-account merchant acceptance. |
| TM02 | TS-G amount shape; the easy-pay part of TS-E3 | `UNDETERMINED · 토스 기술` | Per-source amount and capture normalization. |
| TM03 | TS-G virtual-account ordering | `UNDETERMINED · 토스 기술` | Deposit economic effect and terminal meaning. |
| TM04 | TS-A1 through TS-A5, and the key choice in identity §4.5 | `UNDETERMINED · 토스 기술·어댑터 계약 담당(I06)` | A stable event mapping, and any claim that I06 is complete. No question-sheet row (§4 of the open inputs). |
| TM05 | TS-B1, TS-B2, TS-B4, TS-C3, TS-C4 | `UNDETERMINED · 토스 기술/보안 (I04/I07/I08/I13)` | Authenticated-fact, resend-safety, and evidence-completeness claims. No question-sheet row. |
| TM06 | TS-G refund mapping | `UNDETERMINED · 토스 기술/계약` | Operational refund for those methods. |
| TM07 | TS-G settlement match | `UNDETERMINED · 토스 정산/계약·사용자` | Settlement reconciliation and split payout. |
| TM08 | No TS execution row. Policy values stay out of this plan. | `UNDETERMINED · 제품 정책 담당·Astra·사용자` | The method review already marks a new policy value or command as `DECISION_REQUIRED · Astra`. This plan sets neither. |
| TM09 | TS-G personal-data and tax questions | `UNDETERMINED · 사용자·법무/개인정보·세무·회계·토스 증빙` | Legal, tax, and accounting sufficiency for those methods. |
| TS-Q1 | Whether any `S` result may be read as evidence about live | `UNDETERMINED · Toss` | Sandbox and live response and webhook shapes are uncompared. Every `S` result stays sandbox-scoped. |
| TS-Q2 | TS-B1 receipt and TS-D3 | `UNDETERMINED · Toss` | Whether the sandbox can deliver a webhook without a public URL. Until answered, those cases stay `BLOCKED`. |
| TS-Q3 | TS-F1 | `UNDETERMINED · Toss` | The test-key marker. This plan does not invent the spelling. |
| TS-Q4 | TS-B4, TS-C3, TS-C5 | `UNDETERMINED · Toss` | Whether the sandbox account allows fault injection. |

Follow-up, not this node: add question-sheet rows for TM04 and TM05. Owner of
that sheet edit is the User, because the sheet is an existing contract-adjacent
document and this node's delegation row says no new contract definition.

## 5. Where evidence is recorded

| Artifact | Place |
|---|---|
| This plan | `docs/operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md` |
| This node's evidence record | `validation/2026-10-09-toss-sandbox-conformance-plan/README.md`, the naming form in [AGENTS.md](../../AGENTS.md) §2 |
| A future sandbox run | `validation/<date>-k-provider-sandbox-<run>/README.md` |

Each future run summary contains the case-result table, the exact source SHA,
the tool versions, the redacted structure of each response, and the sha256
plus an opaque reference for each raw artifact. The opaque reference names
the custody object. It does not embed the object.

Raw responses and written Toss replies go to access-controlled custody outside
Git. The location is `UNDETERMINED · operations/security (I13)`, the owner
already named for custody in the open inputs. Git holds no PAN, no CVC, no
OTP, no secret key, and no personal data.

Folding a Toss answer back into the Toss profile or into an open-input row is
a later contract change with User review. It is not done in this node.

## 6. Gate sequence for the future node

`k-provider-sandbox` is not started here. Its entry criteria are:

1. A sandbox-account-use approval from the User.
2. An I02 test MID, as a custody reference rather than a value in Git.
3. A named custody owner for raw evidence and test credentials (I13).
4. A fresh read of the Toss documents. The 2026-09-17 confirmation is the
   baseline this plan carries, and it is not that re-read.
5. A harness design that is not an adapter. The design includes a host
   allowlist and the live-key refusal in TS-F1. The harness location belongs
   to that node.

Exit statement for that future node: the case results leave the PG lock closed.
Real PG, bank, and KYC calls still need the §5 conditions and an explicit User
approval. A `PASS_SANDBOX` row does not supply that approval.

## 7. Existing coverage map

Classification follows [AGENTS.md](../../AGENTS.md) §7. Names below were
checked against the tree at the session base. This plan adds no test.

| Requirement | Existing coverage | Class |
|---|---|---|
| Event deduplication distinct from economic-effect deduplication | [`transitions.rs`](../../runtime/crates/kix-kernel/tests/transitions.rs) `event_deduplication_and_economic_effect_deduplication_are_separate` | Sufficient for the locked kernel. Identity §10.1. |
| Same event, different payload, original capture kept | `transitions.rs` `same_event_different_payload_preserves_conflicting_evidence` | Sufficient for the locked kernel. |
| Accepted duplicate observation advances time once | `transitions.rs` `accepted_duplicate_observation_advances_time_without_reapplying_capture` | Sufficient for the locked kernel. Also asserts `ClockRegression`. |
| One external operation cannot fund two orders | `transitions.rs` `duplicate_external_operation_cannot_fund_two_orders` | Sufficient for the locked kernel (`OperationAlreadyBound`). |
| Replay does not clear quarantine | [`quarantine_capacity.rs`](../../runtime/crates/kix-kernel/tests/quarantine_capacity.rs) `original_event_and_command_replays_never_clear_quarantine` | Sufficient for the locked kernel. |
| Clock does not move backward | `transitions.rs` `accepted_expiry_check_advances_time_but_reservation_result_lookup_does_not`, `unknown_semantics_and_regressed_time_are_not_applied`; `quarantine_capacity.rs` `rejected_evidence_that_quarantines_also_advances_logical_time` | Sufficient for the kernel half of TS-D1. |
| Late capture after expiry | `transitions.rs` `late_capture_after_expiry_and_resale_does_not_release_new_buyer`, `late_capture_after_cancellation_creates_return_marker_not_resurrection`, `reviewed_late_capture_keeps_return_marker_and_review_requirement`; [`contract_edge_cases.rs`](../../runtime/crates/kix-kernel/tests/contract_edge_cases.rs) `return_required_is_stable_under_further_late_evidence` | Sufficient for the kernel half of TS-D2. |
| Local backend admission and replay | [`readiness/conformance.py`](../../readiness/conformance.py) `BackendConformance` | Partial. Local readiness store. `NOT Toss`. |
| Loopback bind refusal | [`integration_gate/test_http_gate.py`](../../integration_gate/test_http_gate.py) `OpenApiAndSchemaTests.test_refuses_non_loopback_bind` | Sufficient for the current gate. Relevant to the webhook block in §9. |
| Independent mock PG on the localnet paid path | [`scripts/run_localnet.py`](../../scripts/run_localnet.py) `--paid` | Partial as a non-Toss stand-in. The flag's help text calls it an independent mock PG. `NOT Toss`. |
| Historical adapter sketch | [`reference/v0.3-rc1/adapters.py`](../../reference/v0.3-rc1/adapters.py) `check_legacy_toss` | Not Toss evidence. Immutable reference package. |
| Toss-shaped derivation, binding record, and `UNMATCHED` | No adapter in the tree. Identity §10.1 already marks this uncovered. | Not covered. |

## 8. Non-claims

This plan does not support a claim about any of the following:

- Toss behaviour, in sandbox or live.
- Webhook signature.
- Provider or chain finality.
- Exactly-once delivery or exactly-once payment.
- Durability of an inbox, a journal, or a custody store.
- Production readiness.
- Legal, tax, accounting, or privacy sufficiency.

A hosted CI run that classifies this diff as documentation-only and skips the
heavy jobs is not full verification. That classification is recorded in the
evidence README for this node, not asserted as a protocol pass.

## 9. Decisions and unknowns

These rows are for the future execution node. This plan does not choose them
and does not add a root decision file. The precedent is
[ADAPTER_EVENT_IDENTITY §9](../contracts/ADAPTER_EVENT_IDENTITY.md), which keeps
the decision inside the document.

| Topic | Status | Handling |
|---|---|---|
| Webhook receipt needs a reachable URL | `DECISION_REQUIRED · User`, plus `UNDETERMINED · Toss` (TS-Q2) | The loopback gate and the public-endpoint lock stay closed. A tunnel is a public endpoint. TS-B1 receipt and TS-D3 stay `BLOCKED`. |
| Test mode and real card data | `DECISION_REQUIRED · User`, plus `UNDETERMINED · 법무/개인정보` | Profile §5, citing S5. This is a PAN custody and privacy matter. `M` cases wait. This plan gives no card-entry steps. |
| Sandbox account, contract, or paid-service terms | `DECISION_REQUIRED · User` | Unknown whether Toss requires a contract or a fee, and the lock needs account-use approval. This plan does not create an account. |
| Test-credential custody owner and location | `UNDETERMINED · operations/security` (I13) | Secrets stay out of Git. TS-H stays `BLOCKED` until an owner is named. |
| Observation time budget | `DECISION_REQUIRED · User` for the budget; `UNDETERMINED · Toss` for whether sandbox follows the published schedule | Profile §3 records the S2 interval sum as 5,461 minutes (about 91 hours). This plan sets no budget and no wait. |
| Any pass rate, latency, repeat count, or wait | `DECISION_REQUIRED · Astra` | No number is invented. Correctness cases stay binary. |
| A new command or enum, including `UNMATCHED` or an inbox | `DECISION_REQUIRED · Astra` | Identity §9 already lists the related architecture items. This plan adds no command. |
| TS-I and ACK custody | Blocked on `k-stage5-durable-tx` | No inbox until stage 5. |
| Toss-shaped derivation | Blocked on an adapter that does not exist and is not authorized | Not covered, §7. |
| Harness location and shape | Belongs to `k-provider-sandbox` | Not designed here. |
| Labelling drift | Controlled by §2 | A fixture pass stays `FIXTURE_PASS` / `NOT Toss`. `reference/v0.3-rc1/adapters.py` and the localnet mock PG are non-Toss evidence. |
| Merge boundary | Delegation table: contract change NO, audit floor A2, delegated merge | An edit under `docs/contracts/` or a new normative term would be a different node. This plan does not do that. Hosted CI skips heavy steps for a documentation-only diff; that skip is not full verification. |
