# k-stage6-economics-reference — economics as a reference model with synthetic money

Node: `k-stage6-economics-reference` (Track K stage 6; program roadmap register
row in `docs/decisions/PROGRAM_ROADMAP_20260930.md`, R-10 approves the reference
model only). Not an ASTRA program-mode session. No issue. No commit, push, pull
request, or comment in this session (the supervisor does git/GitHub). Record
opened 2026-11-12. Branch: `agent/kix-k-stage6-economics-reference`.

**State: acceptance covered locally — `merge-ready` candidate pending
supervisor commit/push and exact-head CI.** The new offline suite
`reference/economics` runs green (98 tests, OK) and the full local CI-equivalent
battery below passed, including the durable binding against the pinned local
PostgreSQL 17.11. Nothing here is exact-head CI; both workflows must still run
on the final head after the supervisor pushes. No production readiness is
claimed; all money is synthetic and every execution flag is false.

## Decision applicability guard (CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md §5.1)

- `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 names the backend
  directly (option A: local, non-production PostgreSQL 17.11, single process,
  single writer, default off, production flags false). ADOPT with a named
  backend; the adoption file is unchanged on this base.
- Dependencies verified merged and ancestors of this branch HEAD:
  `k-stage5-durable-tx` (PR #443, merge `2ec62ca73ee41f397268944e8e0de98ef9d03305`),
  `settlement-policy-deepening` (PR #156, merge `02b1bf2`),
  `booking-resale-admission-deepening` (PR #157, merge `28f263b`). The adopted
  settlement posture is `SET-POLICY-DRAFT-0.4` (B5 REQUESTER, owner decision
  2026-11-10); the BRA mock boundary is option A.
- No DEFERRED/DECLINED decision item is implemented. No decision-document merge
  is treated as a positive adoption beyond its specified scope.

## Base (AGENTS §1)

- Task branch HEAD and observed `origin/main`:
  `b63fca82fd9489429aaa19de6fc3f81427f0f84b` — **no delta**. Read from the local
  remote-tracking ref; `git fetch origin main` was not run because the
  supervisor rule for this session forbids network actions, so the true current
  main may be newer still.
- No implementation commit SHA and no final task head exist yet (the supervisor
  commits). Nothing here is exact-head CI.
- Tools: `rustc`/`cargo` 1.98.1 (workflow pin); `python3` 3.13.5 (`protocol.yml`
  pins 3.12 — deviation recorded below); node v24.22.1 (CI: 24); npm 11.21.1;
  PostgreSQL 17.11 at `/usr/lib/postgresql/17/bin/{postgres,initdb}`; psycopg
  3.2.6.

Locked blobs, before the edits and after the last verification run, identical:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`reference/v0.3-rc1/**`, `runtime/crates/**`, `.aiops/**`, `docs/tasks/**`,
`integration_gate/**`, `readiness/**`, `exploration/**`, `ARCHITECTURE.toml`,
the plan and the register are untouched. `durable/` is changed only by the one
added test file listed below; the stage-5 modules are byte-identical.

## Changed paths

- `reference/economics/` (new package, internal Python API — no wire names, no
  catalogue entries, no new protocol error codes):
  `__init__.py`, `authentication.py`, `quotes.py`, `captures.py`, `refunds.py`,
  `payouts.py`, `session.py`, `support.py` (test harness), `README.md`,
  `fixtures/*.json` (six synthetic journeys), `test_*.py` (12 modules, 98
  tests).
- `durable/test_economics_binding.py` — optional local-PG binding test;
  NOT CI-wired (stage-5 owner decision: no CI may require PostgreSQL). It skips
  gracefully when the pinned backend or psycopg is absent.
- `.github/workflows/protocol.yml` — one-word discovery wiring: `economics`
  added to the offline-suite `for` list so `scripts/check_ci_test_discovery.py`
  sees the suite. No step, guard or semantics change (payment_effects
  precedent).
- `docs/README.md` — one index row (location pointer only), required by
  `scripts/check_docs_index.py` for this record.
- `validation/2026-11-12-k-stage6-economics-reference/README.md` — this record.

## Design summary

`EconomicsSession` composes the unchanged published layers in one explicit,
sequential, in-memory session: `kix:commerce:2` calculation (`build_quote`,
`validate_quote`, `plan_payments`, `propose_line_refund`, largest-remainder
`proportional`), the frozen lifecycle/finance Core, the stage-5 pure admission
decision (`durable.model.decide` + caller `BudgetSpec`), the SET-POLICY-DRAFT-0.4
settlement FSM, the four published payment-effect commands, and the BRA resale
`seller_due` face. The kernel README "required follow-on commerce work" items
are covered as reference-model composition: asset/policy authentication
(fail-closed registries; hash binding is calculation integrity, not
authentication), OrderLine, immutable quotes (rebuild + `quoteHash`, stored
first quote), free orders (payable 0, no intent/capture), discounts
(FIXED/BPS/caps/bearers), bundles (all-or-none group acceptance), multiple
intents and captures (per-leg ledger, partial/multiple captures, atomic
over-capture refusal, retained `UNKNOWN`, immutable completion records),
allocation (exact conservation), refunds (proposal → caller authorization →
per-leg reservation → settlement `bind_refund`; full refunds additionally
reverse the Core event and send one published REFUND intent), payouts
(W0 caller-supplied order → distribution → allocation-bound PAYOUT effects),
resale seller payout (`seller_due` face → Core RESALE allocations → published
PAYOUT effects, caller-supplied synthetic split), multiple assets (per-asset
quote groups; no FX).

Every rate, cap, TTL, budget and expiry is caller-supplied synthetic fixture
input; nothing defaults a product policy value. u128 quotes above the KRW-only
`10**12` fixture-money bound are refused, never narrowed; non-KRW groups
compose calculation/admission but their settlement binding is refused
(`FIXTURE_MONEY_KRW_ONLY`).

## Existing coverage mapping (AGENTS §7)

Sufficiently covered by existing suites, cited not duplicated (all rerun green
here): commerce calculation and canonical pins (`scripts/verify_commerce.py`,
`reference/v0.3-rc1` tests run under `verify_commerce`), settlement FSM
(`reference/settlement_f01_f03`, 224 tests), BRA
(`reference/booking_resale_admission`, 954 tests), stage-5 admission
(`durable.test_pure` + `durable.test_durable`, 94 tests), payment effects
(`reference/payment_effects`, 28 tests).

New coverage (composition gaps only): 98 tests in `reference/economics/`
across authentication, quotes/immutability, free orders, discounts, bundles,
captures (partial/multiple/over-capture/replay/conflict/UNKNOWN/capacity),
allocation properties, refunds, payouts, resale seller payout, multi-asset,
and seeded conservation + rejection atomicity — plus 3 tests in
`durable/test_economics_binding.py` (differential admission vs in-memory,
replay-after-reopen from the database, over-durable session settle) on the
pinned local PostgreSQL. Seeded properties are builder-authored,
source-informed, not independent conformance.

## Commands actually run and results

### Local CI-equivalent battery (protocol.yml + ktx-kernel.yml)

All commands ran in the foreground on this worktree; logs under
`.local/verification/` (gitignored). `.venv/bin/python` steps ran with
`python3` because no bootstrap `.venv` exists locally (deviation recorded
below).

| Command | Result |
|---|---|
| `python3 -m unittest discover -s reference/economics -t reference/economics` | 98 tests, OK |
| Reference suite loop (protocol.yml): `settlement_f01_f03` 224, `booking_resale_admission` 954, `credit_advance_f04` 230, `ai_delegation` 169, `token_reward` 397, `provider_facts` 86, `payment_effects` 28, `economics` 98 | 2186 tests, all OK |
| `python3 -m unittest durable.test_pure durable.test_durable` | 94 tests, OK (composed layer regression) |
| `python3 -m unittest durable.test_economics_binding` | 3 tests, OK (pinned local PostgreSQL 17.11, unix socket) |
| Stdlib offline document checks — the full authoritative run block (32 checkers plain + `--self-test`, plus `check_stage5_host.py --self-test`) | all exit 0 after this record was written; `check_docs_index` earlier failed only on the missing record path, then passed |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 139 tests, OK |
| `python3 -m unittest integration_gate.test_offline_limits` | 9 tests, OK |
| `check_openapi_contract.py` (+`--self-test`), `check_integration_gate_openapi.py` (+`--self-test`) | pass; `commands=84 core=40 fsm=44`, `productionEndpoint=false publicHost=false` |
| `check_sdk_client.py` (+`--self-test`) | `sdk client pin ok: commands=84 node=24.22.1` |
| `npm --prefix sdk run conformance` | 7 tests, 7 pass, 0 fail |
| `npm --prefix sdk run verify-compat` | `ok: true`, BOOTSTRAP bootstrap-2 |
| `python3 scripts/verify_commerce.py --report .local/verification/commerce.json` | `result: PASS` (CALCULATION_ONLY, externalCalls 0) |
| `python3 scripts/verify_canonical.py --report .local/verification/canonical.json` | `result: PASS` |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 139 passed, 0 failed (log: `.local/verification/ktx/kernel-tests.log`) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 339 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo tree -p kix-kernel --edges normal --locked` + `sha256sum` + `git rev-parse HEAD` | evidence written to `.local/verification/ktx/` |
| `python3 scripts/probe_paid_storage.py --python /usr/bin/python3 --directory .local/storage-probe --cycles 3 --report …` | `NO_FAILURE_REPRODUCED` |
| `python3 scripts/reproduce_storage_rollback.py --report …` | `INJECTED_ROLLBACK_REJECTED_BEFORE_CANCELLATION` |
| `python3 scripts/verify_paid_recovery.py --report …` | `PASSED`, 2 cases, SYNTHETIC chain, MOCK money |
| `/usr/bin/python3 scripts/verify_paid_archive.py --report …` | `PASSED`, 2 cases, SYNTHETIC chain, MOCK money |
| Rights-scale offline node regressions (`zk-policy-v2`, `zk-helpers`, `ptau-header`) | 267 + 166 + 34 = 467 pass, 0 fail |

**Merge-tree note:** this branch HEAD equals the observed `origin/main`
(`b63fca8`), so there is no base delta to simulate; the working tree checked
here is the delivery content. If main moves before the supervisor pushes, the
battery must be re-checked on the actual merge tree.

### NOT_RUN locally (and why)

- `bash scripts/bootstrap.sh` — installs the pinned Sui CLI and locked
  dependencies over the network; the supervisor rule forbids network actions.
- `.venv/bin/python scripts/verify_runtime.py`, `scripts/run_localnet.py`
  (plain/`--paid`/`--private`), `scripts/run_localnet_rights_scale*.py` — need
  the bootstrap `.venv` and a Sui binary/local chain; none is present and no
  network provisioning is authorized. No Sui testnet/mainnet is touched.
- ZK steps (`setup:zk`, `test:zk`, phase-1 cache) and the `rights-scale` job's
  bootstrap/chain/ZK steps — need snarkjs dependencies, the ceremony and a
  local chain; not run. The three dependency-free offline rights-scale node
  regressions did run (table above).
- Exact-head KTX/KIX CI — the supervisor commits and pushes; both workflows
  must run on the final head. No CI run ID exists yet and none is claimed.

## Characterizations (contract-undefined, class B — recorded, not invented)

- The fixture money layers (Core, settlement FSM, effects) are KRW-only and
  cap at `10**12`; u128 quotes above the bound are refused, never narrowed.
  Non-KRW groups compose calculation + capture admission; their settlement
  binding is refused. No FX.
- The Core journey binds per order group (one synthetic event/trade carrying
  the group payable), not per line; per-line rights issuance is booking-layer
  scope. The settlement policy's residual payee must equal the event organizer
  and its fee payee `platform` so FSM obligation faces and Core PRIMARY
  allocations coincide; enforced fail-closed at settle.
- Partial refunds compose at the settlement FSM (B5 REQUESTER bearer, faces
  untouched, distribution continues). The published Core REFUND route is
  funded by a full-trade reversal liability, which would cancel the event and
  block the continuing distribution B5 requires — hence partial refunds do
  not use it; full refunds do (event reversal + one REFUND intent).
- Capture admission uses `slot = capture_id`, so several captures may share
  one leg but never one slot; the stage-5 `business_rejected` slot-collision
  outcome is not reachable through this API. Leg accounting and completion
  records are process-local fixture bookkeeping in this revision; the
  `cancel`/`recovery` budget classes are required slots with no writer.
- The resale journey's `primary.slot` is a 0-based integer (BRA gate seat
  index); the Core seat string is `str(slot)`. Caller expiries must fall
  inside the unchanged BRA offer window (`now < expires <= now + 900000` ms).
- Cross-machine atomicity is not claimed: every readable precondition is
  checked before the first write; a failure after a write is a blocker for
  manual review, never an automatic retry. The Core clock stays 0.
- Local Python is 3.13.5 while `protocol.yml` pins 3.12; the stdlib-only
  checks and suites ran on 3.13.5. Recorded as a deviation, not a CI claim.

## Contract violations found

None. No locked file, frozen reference layer or authoritative contract was
changed to make a test pass; every composed layer is byte-identical to its
merged copy.

## Non-claims and open values

No real funds, real PG/bank/KYC calls, public endpoints, Sui testnet/mainnet,
R2 or own replication/consensus/storage engine, new coin/TIX module, secrets
or production runtime. No production readiness, durability equivalence, bank
exactly-once, chain finality, legal/accounting treatment, provider
authentication, or independent conformance is claimed; `evidenceClass` is
`SYNTHETIC_REFERENCE` and all execution flags are false. Product policy
values (resale split bps S0, waterfall/cost numbers W0, canonical payee order
R0, tax/held treatment T0, legal refund debtor I10, provider attestation
I02/I04) stay `DECISION_REQUIRED · Astra` or `UNDETERMINED` with their owners;
the model accepts caller fixtures only and invents none of them.

## Remaining uncertainty and follow-up candidates

- Exact-head CI on the supervisor's final head (both workflows) is still
  required.
- The register's Rust integration step (a Rust economics crate or kernel
  binding) is out of this node's reference-model scope and needs its own
  decision.
- `DurableCaptureLedger` persists admission through the unchanged
  `DurableUnit`; leg accounting and completion records stay process-local —
  a durable binding for them is a possible later revision.
- Astra decisions on the open values (S0/W0/R0/T0/I02/I04/I10) before any
  production-facing use.
