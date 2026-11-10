# plan-plan-local-payment-effect-desk — synthetic local payment effect desk

Builder evidence for node `plan-plan-local-payment-effect-desk`. This is a
local, synthetic, in-memory usability surface over the unchanged
`reference/v0.3-rc1` Core. It is not a protocol change, a settlement/F04
connection, a pending Finance projection, a transmission path or a production
runtime.

## Observed state

- Observed branch: `agent/kix-plan-plan-local-payment-effect-desk`
- Observed `HEAD`: `58cd386b3e85abab01faad5218821a990d451e1d`
- Observed HEAD tree: `09d962c518911a3cbe1d95347cc91ca5ee01bb1c`
- Base: same as observed HEAD (the branch was created from the then-current
  local `main` by the supervisor).
- `git fetch origin main`: **NOT_RUN**. The builder instructions for this
  one-shot session forbid network/GitHub actions, so remote freshness of
  `origin/main` is unverified; no fetch result is claimed.
- Commits/pushes/PRs/issues/comments: **none created** by this session. The
  supervisor owns all git and GitHub operations.
- Merge commit: none.

## Changed paths

- `.github/workflows/protocol.yml` — appended `payment_effects` to the existing
  offline reference-suite discovery loop only.
- `docs/README.md` — appended a location-only index section linking the new
  reference README and this record.
- `reference/payment_effects/README.md`
- `reference/payment_effects/__init__.py`
- `reference/payment_effects/payment_effect_session.py`
- `reference/payment_effects/payment_effect_fixture.py`
- `reference/payment_effects/payment_effect_cli.py`
- `reference/payment_effects/test_payment_effect_session.py`
- `reference/payment_effects/test_payment_effect_cli.py`
- `reference/payment_effects/fixtures/cash_refund.json`
- `reference/payment_effects/fixtures/payout.json`
- `reference/payment_effects/fixtures/original_cancel.json`
- `reference/payment_effects/fixtures/unsettled_refund.json`
- `reference/payment_effects/fixtures/cash_refund.jsonl`
- `reference/payment_effects/fixtures/payout.jsonl`
- `reference/payment_effects/fixtures/original_cancel.jsonl`
- `validation/2026-11-10-plan-plan-local-payment-effect-desk/README.md` (this
  record)

## Protected-file preservation

Locked blobs verified with `git hash-object` after all edits:

| File | Required blob | Observed blob |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --stat -- reference/v0.3-rc1` and `git status --porcelain --
reference/v0.3-rc1` were both empty. `git status --porcelain -- .aiops` was
empty. `docs/tasks/` was not edited.

## Existing coverage first

| Requirement | Classification | Existing evidence |
|---|---|---|
| STATUS-before-FUNDS and FUNDS-before-STATUS | sufficiently covered at Core | `reference/v0.3-rc1/test_core.py::test_effect_observation_orders_and_duplicate_facts`, `test_funds_before_status_debits_cash_without_claiming_refund_done` |
| duplicate observations | sufficiently covered at Core | `test_effect_observation_orders_and_duplicate_facts` |
| conflicting operation body / replay | sufficiently covered at Core | `test_response_loss_and_conflicting_id_after_restart` |
| insufficient confirmed funds | sufficiently covered at Core | `test_capture_is_not_available_cash`, `test_unrelated_event_funds_cannot_fund_refund` |
| partial bounded effects | sufficiently covered at Core | `test_partial_refunds_are_separate_bounded_effects` |
| abort of sent unknown effect | sufficiently covered at Core | `test_unknown_outcome_never_releases_reservation` |
| cash refund / exact payout | sufficiently covered at Core | `test_full_chain_refund_before_payout`, `test_purchase_resale_admission_and_exact_payouts` |
| original cancellation versus customer credit | sufficiently covered at Core | `reference/v0.3-rc1/test_v02.py::test_pg_cancel_before_settlement_needs_no_cash_and_separate_credit` |
| fixture-only session initialization through `Core.execute` | not covered | new session/CLI tests |
| complete receipt and selected-view parity with direct Core | not covered | `test_cash_refund_receipts_and_views_match_direct_core`, `test_all_journeys_match_direct_core_execution` (cash refund, payout and original cancel) |
| real subprocess JSONL journeys | not covered | cash refund, payout and original-cancel journey tests |
| strict fixture/request framing and exit codes | not covered | CLI failure/replay tests |
| detached non-mutating reads and closure | not covered | session view/close tests and in-process `main` closure test |
| CI discovery wiring for the package | not covered | `.github/workflows/protocol.yml` line change plus `check_ci_test_discovery.py` |

The new tests assert wrapper preservation of Core semantics (receipt identity,
rejection text, replay shape, first-result and UNKNOWN handling). They do not
re-implement or replace the Core regressions above.

## New tests and addressed gaps

`reference/payment_effects/test_payment_effect_session.py` (15 tests):

- accepts the four explicit synthetic fixtures and refuses malformed documents
  before Core creation;
- refuses a Core-rejected setup and publishes no session;
- compares complete receipts and selected snapshots against a direct Core for
  the cash-refund command sequence;
- exercises FUNDS-before-STATUS payout completion, STATUS-before-FUNDS and
  duplicate observations through the session;
- refuses binding/evidence/operation-identifier conflicts and insufficient
  confirmed funds, with unchanged selected state and a usable retry;
- covers partial cumulative STATUS versus incremental FUNDS observations and
  bounded over-observation;
- refuses aborting a sent unknown effect and aborts an unsent one;
- proves views are detached and non-mutating, refuses non-effect actions, and
  closes idempotently with no use after close;
- asserts the action allow-list is exactly the four published effect commands.

`reference/payment_effects/test_payment_effect_cli.py` (13 tests):

- runs real subprocess JSONL journeys for cash refund, payout and
  original-payment cancellation;
- checks complete receipts and selected views against direct Core execution for
  all three journeys;
- proves file and stdin request modes emit identical frames;
- covers malformed fixtures (invalid JSON, wrong provenance, Core-rejected
  setup, non-UTF-8), malformed requests, framing stop semantics, Core-rejection
  continuation and exit codes 0/1/2;
- covers operation replay/conflict and QUERY_ONLY send decisions;
- proves the CLI closes its session on success and framing failure and detects
  short/broken output writes.

## Commands actually run and actual results

| Command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/payment_effects -t reference/payment_effects` | `Ran 28 tests` — `OK`; includes three-journey receipt/view parity against direct Core |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/v0.3-rc1 python3 -m unittest test_core test_v02 test_v03` | `Ran 88 tests in 0.428s` — `OK` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B -m reference.payment_effects.payment_effect_cli --fixture reference/payment_effects/fixtures/cash_refund.json --requests reference/payment_effects/fixtures/cash_refund.jsonl` | exit `0`; 6 frames; final effect `DONE`, refunded `100000`, selected balances `0` |
| same CLI for `payout.json` / `payout.jsonl` | exit `0`; 5 frames; FUNDS before STATUS; final effect `DONE`, allocation `primary-0` paid `95000`, pool `5000` |
| same CLI for `original_cancel.json` / `original_cancel.jsonl` | exit `0`; 7 frames; `originalCancelled=100000` and `customerCreditConfirmed=0` after `PG_CANCELLED`; credit `100000` after `CUSTOMER_CREDIT_CONFIRMED` with unchanged balances |
| `python3 scripts/check_ci_test_discovery.py` | exit `0`; `ci test discovery ok: reference_suites=8 node_tests=8 modules=4 excluded=3`; `reference/payment_effects files=2` reached by the protocol offline step |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit `0`; `pass (18 negative controls)` |
| `python3 scripts/check_ci_checker_wiring.py` | exit `0`; `ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99` |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit `0`; `pass (13 negative controls)` |
| `python3 scripts/check_openapi_contract.py` | exit `0`; `openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit `0`; `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | exit `0`; `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit `0`; `self-test: pass` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest integration_gate.test_offline_limits` | `Ran 9 tests in 0.159s` — `OK` |
| `python3 scripts/check_docs_index.py` | exit `0`; `docs index ok: scanned=396 indexed=361 allowlisted=35` |
| `python3 scripts/check_docs_index.py --self-test` | exit `0`; `self-test: pass` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --stat -- reference/v0.3-rc1` | empty |
| `git status --porcelain -- reference/v0.3-rc1` | empty |
| `git status --porcelain -- .aiops` | empty |

No exact-head KTX or KIX CI run exists for this work because no commit or pull
request was created, per the builder instruction that the supervisor owns git
and GitHub operations.

## Contract classification and observations

- Contract-defined and matching: the four effect commands, their required
  fields, operation replay, immutable first results, UNKNOWN retention,
  duplicate evidence and rejection codes are used unchanged.
- Contract violations found: **none**.
- Contract-undefined local tooling (not protocol semantics): JSONL framing,
  exit codes `0/1/2`, the `view` selector shape, detached snapshot copying and
  the `send_effect` local-intent notice. These are wrapper behaviours and are
  not proposed as protocol contract.
- Existing Core characterization retained by a wrapper test: re-presenting an
  already-applied FUNDS movement under a fresh source identifier still returns
  `{"duplicate": true}` because the funds evidence is keyed by `movementId`.
  This is existing Core behaviour, not a new rule.

## Explicit non-claims

- `send_effect` is a stored local intent only. No provider, bank, card network,
  Sui testnet/mainnet, chain, email, HTTP or other external transmission occurs.
- No file-backed database, persistence, restart recovery, durability,
  exactly-once execution, distributed fencing or chain finality is claimed.
- No settlement/F04 FSM is connected; no pending Finance projection is
  implemented; no catalogue or protocol command is added or changed.
- No product policy value, price, fee, provider fact or legal/accounting
  treatment is chosen.
- Product values remain UNDETERMINED — Astra/User. Provider facts remain
  UNDETERMINED — provider/User. Legal/accounting treatment remains
  UNDETERMINED — User/designated advisers.
- Passing local tests do not authorize merge. Non-author exact-head review and
  the required KTX/KIX exact-head CI remain separate gates.

## Remaining uncertainty and follow-up candidates

- Remote freshness of `origin/main` is unverified because `git fetch` was not
  allowed in this session.
- Exact-head CI and non-author review have not run; the supervisor must create
  the commit/PR and obtain both before any merge decision.
- The wrapper deliberately treats an invalid request as a stream-stopping local
  error and a Core rejection as a continuing line. That choice is local tooling
  policy only and may be revisited outside this node if a different desk
  behaviour is wanted.
- No resource-leak instrumentation exists beyond explicit close assertions and
  subprocess exit; durability and crash recovery are out of scope.
