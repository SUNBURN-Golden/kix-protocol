# cr1110-refund-bearer-requester — builder evidence

Node: `cr1110-refund-bearer-requester`, SUNBURN-Golden/kix-protocol.
Integration step 3 (CR-CAPITAL-1110 #3). Issue: none. Task input: the
supervisor-supplied node specification in this session; there is no task
document under `docs/tasks/` for this node. This is not ASTRA program mode: no
signer, no delivery/blocked marker, no comment.

Branch: `agent/kix-cr1110-refund-bearer-requester`.

Owner decision 2026-11-10 17:43 KST (준태님, the User): for partial refunds,
the party who requested the partial refund bears it. The node adds option B5
`REQUESTER` to `SETTLEMENT_DISTRIBUTION_F01_F03.md` §7.6/§5 as the adopted mock
posture for partial refunds, replacing B0, and mirrors it in
`CREDIT_ADVANCE_F04.md`. All execution flags stay false; mock funds only; no
new protocol commands, view keys or error codes.

## Identity and gates

| Item | Observed value |
|---|---|
| Branch base and initial HEAD | `298bd52446f3bc5d949049daea7960be843fa0e5` |
| Base delta against local `origin/main` | none observed at session start (local ref) |
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

- `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` — revision
  `SET-POLICY-DRAFT-0.4`; §5 bullets, §6 row retained as unreachable, §7
  preamble/adopted-test row, §7.6 B5 row adopted (B0 historical), §9.2 block
  sentence; decision source recorded in the revision header.
- `docs/contracts/CREDIT_ADVANCE_F04.md` — §2 bearer bullet `REQUESTER` for a
  non-reclassified open refund; §3 step 5 and §4 `REFUND_OBLIGATION_OPEN`
  rationale rewritten (the gate is kept; the reason is now the unbound
  refund/note netting order of §5, not an undefined bearer); revision header
  cites the same owner decision.
- `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` — the
  `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` row becomes `CLASS_B` with a
  reasoned note (retained in SET §6, unreachable under B5, no raise/assert
  site); two `REFUND_*` citations follow the renamed test; Counts recomputed.
- `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md` — §4/§5 citations follow
  renamed tests; §7 heading title and paraphrase moved to `0.4`/B5; §7.6 row
  records B5 adopted for the mock while the legal route stays OPEN.
- `docs/status/EVIDENCE_MAP_ROLLUP.md` — the verbatim Counts copy for the
  error-code map updated to the new values.
- `docs/contracts/READ_MODEL_SOURCE_MAP.md` — A29/A30 line anchors moved
  289→287 and 298→296 to match `mock_settlement.py` after the removed raise.
- `reference/settlement_f01_f03/mock_settlement.py` — the
  `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` raise removed; `_view`
  reports `REQUESTER` for an open non-reclassified refund and
  `distribution_blocked` is always `false`.
- `reference/settlement_f01_f03/settlement_property_support.py` —
  `BEARER_RANK` `REQUESTER`; refund-view oracle derives bearer/blocked under
  B5; the block code drops out of the raised-set while remaining in the
  contract code table.
- `reference/settlement_f01_f03/example_cancel_acceptance_adapter.py` — the
  example now performs the unblocked post-refund distribution instead of
  asserting the removed refusal.
- `reference/settlement_f01_f03/test_adopted_policy.py` — posture test pins
  B5/`REQUESTER`; `ABSENT` key tuple unchanged (no new keys).
- `reference/settlement_f01_f03/test_mock_settlement.py` — partial-refund
  tests renamed/updated to B5 (`REQUESTER`, distribution proceeds); full-gross
  reclass tests unchanged.
- `reference/settlement_f01_f03/test_settlement_fsm.py` — replay test renamed
  `test_partial_refund_distribution_survives_replay_and_is_not_a_clawback`;
  distribute after a partial refund succeeds (zero remaining cash on replay).
- `reference/settlement_f01_f03/test_settlement_multi_payee_refund.py` —
  partial-refund expectations and error-matrix rows updated (the removed code
  replaced by still-raised refusals such as `DISTRIBUTION_ORDER_MISMATCH`).
- `reference/settlement_f01_f03/test_settlement_properties.py` — seeded probe
  adjusted so `REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION` stays reachable.
- `reference/settlement_f01_f03/test_settlement_rejection_atomicity.py` — the
  old blocked-distribute atomicity test repurposed as
  `test_distribute_order_mismatch_with_open_refund_leaves_no_trace`: order
  checks still fire with an open partial refund and the follow-up valid
  distribute succeeds.
- `reference/settlement_f01_f03/test_cancel_acceptance_adapter.py` — journal
  gains `distribute`; restore/replay asserts the unblocked distribution.
- `reference/settlement_f01_f03/README.md` — example prose updated to B5.
- `reference/credit_advance_f04/mock_credit.py` — `_parse_face` accepts
  `REQUESTER` for an open non-reclassified refund face.
- `reference/credit_advance_f04/credit_property_support.py` — open-refund face
  builder emits `REQUESTER`/`distribution_blocked:false`; `expect_note` keeps
  `REFUND_OBLIGATION_OPEN`.
- `reference/credit_advance_f04/test_mock_credit.py` — bearer expectation
  `REQUESTER`; `REFUND_OBLIGATION_OPEN` still asserted.
- `reference/credit_advance_f04/test_settlement_credit_boundary.py` — S4
  refund claim expects `REQUESTER`/`distribution_blocked:false`.
- `reference/credit_advance_f04/fixtures/boundaries.jsonl` — face literals
  `REQUESTER`/`false` (the row still exercises the retained
  `REFUND_OBLIGATION_OPEN` refusal).
- `reference/credit_advance_f04/fixtures/settlement_credit_boundary_vectors_v1.json`
  — regenerated through the driver's own `actual_vectors`/`canonical`;
  `fixture_sha256` unchanged (`16088b7f…`); the delta is only
  `UNDEFINED`→`REQUESTER`, `distribution_blocked` `true`→`false` and one
  dependent `state_digest`.
- `reference/booking_resale_admission/test_ticket_refund_controls.py` —
  partial/replay bearer `REQUESTER`; summed-partial-bindings test asserts the
  now-succeeding distribution on every graph.
- `reference/booking_resale_admission/test_ticket_statement_distribution.py` —
  boundary journey drops the removed code; post-refund distribute applies the
  remaining cash; bearer `REQUESTER`.
- `reference/booking_resale_admission/test_settlement_console.py` — console
  display expects `REQUESTER`/`distribution_blocked:false`.
- `reference/booking_resale_admission/test_ticket_settlement_fact_inputs.py` —
  final bearer `REQUESTER`.
- `reference/booking_resale_admission/README.md` — active prose updated to
  B5; dated/historical records left intact.
- `docs/README.md` — one location-only index link added.
- `validation/2026-11-11-cr1110-refund-bearer-requester/README.md` (new) —
  this record.

No machine change outside the two touched mocks; no OpenAPI, catalogue, CI,
`.aiops`, `docs/tasks/`, `docs/decisions/`, locked-blob or
`reference/v0.3-rc1/` change. The `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED`
error-table row is retained (unreachable), so no catalogue/error-table churn.

## Locked-blob verification

| Locked file | Required blob | Before work | After work |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

`git diff --name-only -- reference/v0.3-rc1 .aiops docs/tasks .github` is
empty (0 paths).

## Existing coverage map (before the posture flip)

| Requirement | Existing evidence and classification | This node |
|---|---|---|
| Partial refund does not reclassify or claw back | sufficiently covered: `test_f03_partial_after_distribution_does_not_claw_back`, multi-payee reservation corpus | kept; expectations flipped to `REQUESTER`/unblocked |
| Full-gross `FIXTURE_FULL_GROSS_RECLASS` | sufficiently covered: `test_f03_full_refund_reclassifies_and_mock_acceptance_is_not_closure`, `test_g_*` reservation tests | unchanged |
| Distribution-block posture | previously asserted via the removed code path | repurposed atomicity test asserts order checks still fire and the valid distribute succeeds |
| F04 open-refund gate | sufficiently covered: `test_open_refund_blocks_and_release_is_not_repayment`, `boundaries.jsonl` row | kept `REFUND_OBLIGATION_OPEN`; face literal flipped to `REQUESTER` |

No new tests were added; existing deterministic coverage was re-pinned under
B5. The suite is source-informed, not clean-room verification.

## Commands and results

All Python commands ran in the foreground from the repository root.

| Command actually run | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0; 224 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 230 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0; 954 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0; 169 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | first discovery run reported `FAILED (failures=1)`; the rerun passed all 397 tests OK; treated as a flake and flagged — the failing test name was not captured |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | exit 0; 86 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/payment_effects -t reference/payment_effects` | exit 0; 28 tests OK |
| `python3 -B reference/credit_advance_f04/settlement_credit_boundary_vectors.py` | exit 0; prints canonical vectors (203,627 bytes); `fixture_sha256` unchanged |
| `python3 reference/read_model/generate_fixtures.py --check` | exit 0; `fixture vectors ok: files=6 seed=20261020` |
| `python3 scripts/check_openapi_contract.py` (+ `--self-test`) | both exit 0; `commands=84 core=40 fsm=44`, pin sha256 `ed827de1…`, gitBlob `619ae21c…` |
| `python3 scripts/check_integration_gate_openapi.py` (+ `--self-test`) | both exit 0; `commands=84 productionEndpoint=false publicHost=false` |
| `python3 -m unittest integration_gate.test_offline_limits` | exit 0; 9 tests OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0; 139 tests OK; loopback only; self-test pass |
| `python3 scripts/check_contract_error_codes.py` (+ `--self-test`) | both exit 0; `rows=199 RAISED=198 ASSERTED=198 COVERED=198 CLASS_B=1 CLASS_C=0` |
| `python3 scripts/check_settlement_evidence_map.py` (+ `--self-test`) | both exit 0; `rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8` |
| `python3 scripts/check_credit_evidence_map.py` (+ `--self-test`) | both exit 0; `rows=24 headings=24 items=5 citations=134 COVERED=16 PARTIAL=4 NOT_COVERED=1 OPEN=3` |
| `python3 scripts/check_bra_evidence_map.py` (+ `--self-test`) | both exit 0; `rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2` |
| `python3 scripts/check_class_b_index.py` (+ `--self-test`) | both exit 0 |
| `python3 scripts/check_ci_test_discovery.py` (+ `--self-test`) | both exit 0 |
| `python3 scripts/check_docs_index.py` (+ `--self-test`) | both exit 0; this record is linked once from `docs/README.md` |
| Full `Stdlib offline document checks` block from `.github/workflows/protocol.yml` (65 invocations; `check_stage5_host.py` self-test only per the workflow comment) | first full run: 62 of 65 exit 0 — `check_read_model_source_map.py` (plain and `--self-test`) reported stale A29/A30 anchors and `check_evidence_map_rollup.py` reported the stale Counts copy; after fixing those two docs, the rerun is 65 of 65 exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; `architecture v5 + KTX-R1 dependency gate OK` |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests OK |
| `python3 scripts/verify_commerce.py --report .local/verification/commerce.json` | exit 0; `"result":"PASS"` |
| `python3 scripts/verify_canonical.py --report .local/verification/canonical.json` | exit 0; `"result":"PASS"` (node v24.22.1) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; 139 passed / 0 failed across all binaries (rustc 1.98.1) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0; no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0; clean |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` and `.../tests/quarantine_capacity.rs` (before and after) | both match the required blobs |
| `git diff --name-only -- reference/v0.3-rc1 .aiops docs/tasks .github` | empty |

### Stdlib block

| Checkers run plain and `--self-test` | Actual result |
|---|---|
| `check_status_register.py`, `check_producer_qualification_tuple.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_docs_index.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, `check_adapter_identity_map.py`, `check_v5_transition_evidence_map.py`, `check_readiness_evidence_map.py`, `check_settlement_evidence_map.py`, `check_bra_evidence_map.py`, `check_credit_evidence_map.py`, `check_primary_price_fee_evidence_map.py`, `check_ai_delegation_evidence_map.py`, `check_lifecycle_adr_evidence_map.py`, `check_contract_invariants_evidence_map.py`, `check_toss_card_profile_evidence_map.py`, `check_bcs1_evidence_map.py`, `check_performance_measurement_evidence_map.py`, `check_feature_semantics_evidence_map.py`, `check_integration_gate_contract_evidence_map.py`, `check_evidence_map_rollup.py`, `check_class_b_index.py`, `check_ci_checker_wiring.py`, `check_ci_test_discovery.py`, `check_loopback_host.py`, `check_cargo_offline_cache.py` | 64 of 64 invocations exit 0 on the final run (32 scripts × plain+self-test) |
| `check_stage5_host.py --self-test` | exit 0 (self-test only, per the workflow comment) |

`check_docs_index.py` final output: `scanned=406 indexed=371 allowlisted=35`
(this record is linked once from `docs/README.md`).
`check_ci_test_discovery.py` final output:
`reference_suites=8 node_tests=8 modules=4 excluded=3` (all touched test files
are reached by the existing suite discovery).

## Deviations from the design plan

- Fetch: NOT_RUN under the supervisor's no-network rule (AGENTS §1 override);
  the observed base `298bd52446f3bc5d949049daea7960be843fa0e5` is the local
  branch base recorded at session start.
- Toolchain-limited CI equivalents: `bash scripts/bootstrap.sh` requires
  network (pip/npm/sui install) and asserts Python 3.12 while the session
  default `python3` is 3.13.5 (python3.12 exists but the pinned `.venv`,
  `sui` and `node_modules` are absent). Therefore `verify_runtime.py`, the
  `reference/v0.3-rc1` unittest discovery, the node circuit/SDK steps,
  `run_localnet*.py` and the rights_scale suites were NOT run locally.
  `verify_commerce.py` and `verify_canonical.py` are stdlib/node-only and were
  run and pass. Exact-head CI remains the gate for the rest.
- `token_reward` flakiness: the first discovery run reported one failure; the
  rerun passed all 397 tests. The failing test name was not captured. Flagged
  for reviewer attention; no token_reward file was touched by this node.
- The old `test_distribute_blocked_refund_bearer_undefined_leaves_no_trace`
  could not assert a removed code path; it was repurposed to assert the
  still-raised `DISTRIBUTION_ORDER_MISMATCH` with an open partial refund plus
  the succeeding follow-up distribute, per the plan's error-matrix guidance.
- `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` stays in the SET §6 table and
  the `CONTRACT_CODES` oracle set; the coverage row is `CLASS_B` with a
  reasoned note rather than COVERED, since no raise/assert site may remain.

## Contract classification

- Contract-defined and matching: §5/§7.6 B5 `REQUESTER` semantics — open
  partial refunds report `REQUESTER`, `distribution_blocked` is `false`,
  distribution proceeds in the frozen caller order, payee faces and unpaid
  amounts are never reduced or turned into `recovery_due`, and prior
  distributions are not clawed back. Full-gross `FIXTURE_FULL_GROSS_RECLASS`
  and the partial-sums-never-reclassify rule are unchanged. F04 mirrors the
  bearer value and keeps `REFUND_OBLIGATION_OPEN` while the refund/note
  netting order stays unbound.
- Contract-undefined characterizations: none newly asserted. Netting mechanics
  and numeric fee/percentage values remain `UNDETERMINED`; the legal refund
  debtor remains `UNDETERMINED` (사용자 → 법무, I10 경로).
- Contract violations: none found.
- New protocol commands, FSM phases, view keys, error-table entries or OpenAPI
  bytes: none.

## Non-claims and remaining uncertainty

The implementation is mock-only (`MOCK_SETTLEMENT_ONLY`,
`MOCK_CREDIT_F04_ONLY`) and process-local. It does not establish the legal
refund debtor, any netting arithmetic, fee or percentage value, durability,
crash recovery, distributed fencing, bank exactly-once, chain finality, live
funds, accounting treatment or production readiness. `REQUESTER` is a mock
bearer label recording the adopted B5 posture, not a legal-liability
determination. `REFUND_OBLIGATION_OPEN` intentionally remains enforced in F04;
lifting it would be a separate owner decision. A2 non-author exact-final-head
review and completed/successful exact-head KTX and KIX CI remain separate
delivery gates, as does explicit human merge authorization.
