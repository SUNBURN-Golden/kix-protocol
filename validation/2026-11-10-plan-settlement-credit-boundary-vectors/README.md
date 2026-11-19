# plan-settlement-credit-boundary-vectors — builder evidence

Node: `plan-settlement-credit-boundary-vectors`, SUNBURN-Golden/kix-protocol.
Issue: none. Task input: the supervisor-supplied node specification in this
session; there is no task document under `docs/tasks/` for this node. This is
not ASTRA program mode: no signer, no delivery/blocked marker, no comment.
Branch: `agent/kix-plan-settlement-credit-boundary-vectors`.

## Identity and gates

| Item | Observed value |
|---|---|
| Local `origin/main` and initial task HEAD | `652e41e7503c2a7300abf634abad9581f2fb0710` (merge #438); the two are equal |
| Base delta against local ref | none |
| Fetch | NOT_RUN: the supervisor explicitly prohibits network/GitHub actions, overriding AGENTS §1 fetch |
| Implementation head | no commit created; supervisor owns git. Working-tree delivery only |
| Exact final task head | pending supervisor commit/push |
| Merge commit / post-merge CI | not applicable; no merge |
| Exact-final-head KTX CI | NOT_RUN; no run ID/status/conclusion available |
| Exact-final-head KIX CI | NOT_RUN; no run ID/status/conclusion available |
| A2 non-author exact-final-head review | pending supervisor workflow; builder checks are not independent review |

No commit, push, PR, issue, comment, tag, branch mutation or merge was
performed. No prior CI result transfers to the supervisor's eventual final head.

## Changed paths

- `reference/credit_advance_f04/fixtures/settlement_credit_boundary_v1.json` (new)
- `reference/credit_advance_f04/fixtures/settlement_credit_boundary_vectors_v1.json` (new)
- `reference/credit_advance_f04/settlement_credit_boundary_vectors.py` (new)
- `reference/credit_advance_f04/test_settlement_credit_boundary.py` (new)
- `reference/credit_advance_f04/README.md` (section added)
- `validation/2026-11-10-plan-settlement-credit-boundary-vectors/README.md` (new)
- `docs/README.md` (one location-only index link added)

No machine, contract, OpenAPI, CI, `.aiops`, `docs/tasks/`, locked-blob or
`reference/v0.3-rc1/` change.

## Locked-blob verification

| Locked file | Required blob | Before work | After work |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

`git diff --name-only -- reference/v0.3-rc1 .aiops docs/tasks` is empty.

## Existing coverage map (before adding tests)

Paths are under `reference/credit_advance_f04/` unless fully qualified.

| Requirement | Existing evidence and classification | New gap coverage |
|---|---|---|
| Captured-versus-committed settlement gate; draw claims no finality | sufficiently covered: `fixtures/settlement_gates.jsonl` and `test_credit_fsm.py::CreditFsmTests.test_bound_draw_waits_for_mock_commit_and_does_not_claim_finality` | Consumer-replay vectors embed the literal captured and committed claim snapshots; the captured face keeps `confirmed_cash_on_face: 0` after the settlement later commits |
| First accepted face freezes; `view_claim` stable | partially covered: `test_credit_fsm.py` `FACE_SNAPSHOT_FROZEN` case and `test_credit_properties.py` stability checks on the machine | Vectors show a modified later face failing `FACE_SNAPSHOT_FROZEN`, and `view_claim` byte-equal before and after a settlement refund plus partial acceptance |
| Refund obligation and partial acceptance visibility; no funds | sufficiently covered on the settlement side: `reference/settlement_f01_f03/` `bind_refund` / `observe_mock_cancel_acceptance` tests | Cross-boundary observation: settlement claim shows `refund_face`, `refund_outstanding`, `pg_adjustment_outstanding`; the credit `view_claim` has no refund keys and `funds_executed` stays false |
| Shared exposure on one ledger; caller-supplied limits | partially covered: `test_credit_fsm.py` / `test_mock_credit.py` amount-ceiling cases | Two distinct advances on one claim with amounts `40000` and `30000`; `30001` fails `ADVANCE_EXCEEDS_OPEN_FACE` without changing the offer; `30000` reserves the exact residual |
| Reconciliation gap reported without repair | classified contract-undefined (Class B): `test_credit_properties.py::ClassBCharacterizationTests.test_b_the_gate_does_not_read_refund_fields_of_the_settlement_view` | Explicit report record `SETTLEMENT_REFUND_NOT_REFLECTED_IN_CREDIT_FACE` / `UNDEFINED` / repair `NONE`; both reconciles report `matched: true`, and the gap remains observable afterwards |

The new suite is source-informed, not clean-room verification.

## New tests and what each addresses

`test_settlement_credit_boundary.py` adds 13 tests:

1. canonical JSON files, `fixture_sha256` pin, provenance;
2. exact replay through `replay_pack` and driver exit 0;
3. driver exits 1 and names the scenario/step on a mutated vector;
4. every acceptance tag maps to a scenario;
5. only existing public machine methods are dispatched (no new command);
6. every offered face is the literal settlement claim snapshot (no derivation);
7. the credit journal stores the fixture literal verbatim;
8–13. S1 captured-face freeze across settlement commit, S2 committed-face
gate/no-finality, S3 freeze plus stable `view_claim`, S4 refund and partial
acceptance, S5 shared exposure and caller limits, S6 reconciliation gap without
repair.

## Commands and results

All Python commands ran in the foreground with `PYTHONDONTWRITEBYTECODE=1`.

| Command actually run | Actual result |
|---|---|
| `python3 -B reference/credit_advance_f04/test_settlement_credit_boundary.py -v` | exit 0; 13 tests passed |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0; 224 tests passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 196 tests passed |
| `python3 -B reference/credit_advance_f04/settlement_credit_boundary_vectors.py` | exit 0; canonical output 203617 bytes, byte-identical to the vector file |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; 32 passed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0; no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| CI reference-suite loop (`settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward`, `provider_facts`, `payment_effects`) | exit 0 for all seven: 224, 954, 196, 169, 397, 86 and 28 tests |
| `check_openapi_contract.py` and `check_integration_gate_openapi.py` (plain plus `--self-test`) | 4 of 4 exit 0 |
| `python3 -m unittest integration_gate.test_offline_limits` | exit 0; 9 tests passed |
| Document checker block from `.github/workflows/protocol.yml` (plain plus `--self-test`) | 65 of 65 invocations exit 0; no failure |

The document-checker block includes `check_docs_index.py` (the new validation
record is linked once from `docs/README.md`), `check_credit_evidence_map.py`,
`check_settlement_evidence_map.py`, `check_contract_error_codes.py`,
`check_class_b_index.py`, `check_ci_test_discovery.py` (the new test is reached
by the existing credit-suite discovery step) and `check_ci_checker_wiring.py`.

## Contract classification

- Contract-defined and matching: captured/committed gate, face freeze,
  `SETTLEMENT_NOT_COMMITTED`, `FACE_SNAPSHOT_FROZEN`,
  `ADVANCE_EXCEEDS_OPEN_FACE`, refund visibility and partial acceptance.
- Contract-undefined (Class B, not newly invented): a settlement refund is not
  reflected in the frozen credit face; the pack reports it with
  `contract_status: "UNDEFINED"` and repair `NONE`. No repair is implemented.
- Contract violations: none found.

## Non-claims and remaining uncertainty

The pack is synthetic (`MOCK_SETTLEMENT_ONLY` / `MOCK_CREDIT_F04_ONLY`) and
process-local. It does not establish durability, crash recovery, distributed
fencing, bank exactly-once, chain finality, live funds, legal or accounting
treatment, production readiness, or any product/Finance term. It adopts no
pending Finance design. A2 non-author exact-final-head review and completed,
successful exact-head KTX and KIX CI remain separate delivery gates, as does
explicit human merge authorization.
