# plan-commerce-journey-end-to-end-conformance — validation

Integration step 2: one end-to-end commerce journey through reservation,
payment, issuance, resale/admission, refund and adverse paths.

## Basis

- Task: `plan-commerce-journey-end-to-end-conformance` (integration node).
- Observed `origin/main` = base = implementation head at session start:
  `6320c7ed927fe4b6b8e615e705bbbbe28fa8779b`.
- Branch: `agent/kix-plan-commerce-journey-end-to-end-conformance`.
- Worktree: `/workspace/kix-run/wt/plan-commerce-journey-end-to-end-conformance`.

No commit, push, PR, issue or comment was made by this session. There is no
exact-head CI evidence yet; the supervisor commits and pushes.

## Changed paths

| Path | Kind |
| --- | --- |
| `reference/booking_resale_admission/test_commerce_journey_conformance.py` | new conformance test (6 tests) |
| `reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json` | new consumer-facing fixture transcript (44 steps) |
| `docs/README.md` | required index link for the new validation record (`scripts/check_docs_index.py`) |
| `validation/2026-11-10-plan-commerce-journey-end-to-end-conformance/README.md` | this evidence file |

No catalogue, OpenAPI, SDK, generated, `.aiops`, CI, locked-blob,
`reference/v0.3-rc1/**`, `docs/tasks/**` or dependency change. The
`docs/README.md` edit is one index bullet; it changes no status, grade,
owner, count or capability claim.

## What the fixture drives

One show (`show-journey`, capacity 4, gates `gate-1`/`gate-2`, primary price
12000, resale cap 15000, 100/100 bps). All bodies use only the published
`docs/contracts/openapi/fsm-command-contract.json` actions and fields; the
test fails if a body carries a field outside the action schema, misses a
required field, or omits the declared subject field.

44 ordered steps, all through `integration_gate.fsm_host.FsmHost`:

- **Reservation**: clock, register-show, holds A/B/C, confirms A/B/C,
  payment observation A/B, issuance A/B, cancellation of C.
- **Resale**: clock, adopt A's issued right, list, buyer hold, resale payment
  observation, settlement initiate/authorize/capture, bind settlement,
  refusal of accept before commit, commit, accept (transfer), distribute.
- **Admission**: clock, adopt B's issued right, authorize, consume B.
- **Refund**: cancellation settlement (initiate/cancel), failure settlement
  (initiate/fail), refund settlement (initiate/authorize/capture), full-gross
  `bind_refund`, `observe_mock_cancel_acceptance`.
- **Adverse**: hold over capacity (`SLOT`), hold on occupied slot
  (`SLOT_OCCUPIED`), issue on cancelled reservation (`TERMINAL_IMMUTABLE`),
  double consume (`ALREADY_CONSUMED`), accept before settlement commit
  (`SETTLEMENT_NOT_COMMITTED`), and same-key replay of consume B.

Expected values are recorded per step as receipt paths (`expect.paths`) and
journal deltas (`expect.journal`), not invented reads. Rejections are asserted
to append nothing to any journal.

## Existing coverage mapping (AGENTS.md §7)

| Requirement | Classification | Existing evidence |
| --- | --- | --- |
| Reservation hold/confirm/observe/issue/cancel transitions | partially covered | `reference/booking_resale_admission/test_reservation_fsm.py`, `test_reservation_rejection_atomicity.py`, `test_primary_price_binding.py` |
| Resale adopt/list/hold/pay/bind/accept | partially covered | `test_resale_fsm.py`, `test_resale_rejection_atomicity.py`, `test_adopt_issued_atomicity.py` |
| Admission adopt/authorize/consume | partially covered | `test_admission_fsm.py`, `test_admission_rejection_atomicity.py` |
| Settlement F01–F03 lifecycle and refund | partially covered | `reference/settlement_f01_f03/test_settlement_fsm.py` and peers |
| One show through all published machines in one transcript, with receipts as the only evidence | not covered | this test |
| Same-key replay returning the stored duplicate result in a multi-machine journey | partially covered | per-machine replay tests; cross-machine replay is new here |
| 13 read queries remain NOT_BOUND | covered | `docs/contracts/READ_MODEL_QUERIES.md`, `scripts/check_read_model_source_map.py`; this test additionally requires absence from both catalogue pins and `FsmHost._commands` |
| Published-schema conformance of every step body | partially covered | contract/OpenAPI checkers validate the contract, not a journey body set; this test checks each body against the action schema |

## Commands run and actual results

All commands were run in the foreground from the worktree root, in the order
shown.

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_journey_conformance.py' -v` | 6 tests, OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 139 tests, OK (self-test: pass) |
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward provider_facts payment_effects; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite"; done` | 224 / 954 / 183 / 169 / 397 / 86 / 28 tests, all OK |
| `python3 scripts/check_ci_test_discovery.py --self-test && python3 scripts/check_ci_test_discovery.py` | self-test pass (18 controls); `ci test discovery ok: reference_suites=8 node_tests=8 modules=4 excluded=3`; new module reported reached under `reference/booking_resale_admission files=63` |
| Full `stdlib offline document checks` list from `protocol.yml` (all 29 checkers plus `--self-test`) | all exit 0; `check_docs_index.py` reports `scanned=401 indexed=366 allowlisted=35` |
| `python3 scripts/check_openapi_contract.py --self-test && python3 scripts/check_openapi_contract.py` | self-test pass; `openapi contract pin ok: commands=84 core=40 fsm=44` |
| `python3 scripts/check_integration_gate_openapi.py --self-test && python3 scripts/check_integration_gate_openapi.py` | self-test pass; `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false` |
| `python3 -m unittest integration_gate.test_offline_limits` | 9 tests, OK |
| `python3 scripts/check_read_model_source_map.py --self-test && python3 scripts/check_read_model_source_map.py` | self-test pass; `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145` |
| `python3 scripts/check_bra_evidence_map.py --self-test && python3 scripts/check_bra_evidence_map.py` | self-test pass (50 controls); `bra evidence map ok: rows=39 ...` |
| `python3 scripts/check_settlement_evidence_map.py --self-test && python3 scripts/check_settlement_evidence_map.py` | self-test pass (33 controls); `settlement evidence map ok: rows=27 ...` |
| `python3 scripts/check_contract_error_codes.py --self-test && python3 scripts/check_contract_error_codes.py` | self-test pass; `contract error code coverage ok: rows=199 ...` |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; all binaries green (last reported binary: 32 passed, 0 failed) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` (CI command) | exit 0; every reported binary `ok`, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0, no warnings |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` (CI command) | exit 0, no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` (both required blobs) |

## Assertions the test makes

1. Every step action is in the 44-name FSM catalogue; bodies match the
   published schema; step ids are unique; the fixture count equals
   `FSM_COMMAND_COUNT`.
2. One show is used throughout; the non-adverse steps cover the full
   reservation, resale, admission, settlement and refund action set; the five
   refusals map to exactly the five existing FSM codes.
3. Payment observation, issuance, admission authorization and consumption are
   separate facts with distinct identifiers and distinct receipts; the payment
   receipt carries neither `issuance_id` nor `admission_id`.
4. Every occurrence of the 24 always-false flags in any receipt is `False`
   (including all 14 `NON_CLAIMS`), `funds_executed` is `False` and
   `external_payment` is `"UNSUPPORTED"` in every receipt; settlement views
   keep `legal_debtor_bound`, `bank_debit_observed`,
   `external_return_closed`, `right_cancelled`, `admission_granted`,
   `provider_authorization_executed` false.
5. The 13 read-query names match the canonical list, are not in the core or
   FSM catalogue, and are not dispatchable in `FsmHost`.
6. Replaying consume B with the same key returns the stored result with
   `duplicate=true`, `applied=null`, no journal growth, and an otherwise
   identical receipt.

## Non-claims

- Mock gate and mock settlement only, one process, caller-supplied fixture
  constants. No real funds, bank, PG, KYC, venue credential, chain ownership,
  economic finality, durability, production admission or legal compliance is
  claimed or exercised.
- Command receipts are the only evidence. No read API exists or is simulated;
  the 13 queries remain NOT_BOUND.
- The fixture's actors, clocks, prices and bps are test inputs, not product
  policy values or production defaults.
- CI was not run for this tree; the supervisor owns commit, push and CI.

## Remaining uncertainty

- The repository CI (`KTX kernel verification`, `KIX protocol verification`)
  has not run on this tree. The local commands above are the closest
  equivalents, not a substitute for exact-head CI.
- Discovery of this module relies on the existing
  `reference/booking_resale_admission` suite entry in `protocol.yml`; the new
  file was not wired separately and no CI file was edited.
