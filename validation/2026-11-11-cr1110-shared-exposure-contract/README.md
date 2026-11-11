# cr1110-shared-exposure-contract — builder evidence

Node: `cr1110-shared-exposure-contract`, SUNBURN-Golden/kix-protocol.
Integration step 3 (CR-CAPITAL-1110 #2). Issue: none. Task input: the
supervisor-supplied node specification in this session; there is no task
document under `docs/tasks/` for this node. This is not ASTRA program mode: no
signer, no delivery/blocked marker, no comment.

Branch: `agent/kix-cr1110-shared-exposure-contract`.

## Identity and gates

| Item | Observed value |
|---|---|
| Local `origin/main`, branch base and initial HEAD | `6df88c1654ce0fb15f783a11c1ba7fcfb1a95590` (merge #440); all three are equal |
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

- `docs/contracts/CREDIT_ADVANCE_F04.md` (§7.12 clause added)
- `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` (unnumbered §9.6 cross-reference)
- `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md` (§7.12 row, Counts, heading count)
- `docs/status/EVIDENCE_MAP_ROLLUP.md` (F04 Counts copy)
- `reference/credit_advance_f04/README.md` (shared-exposure section)
- `reference/credit_advance_f04/shared_exposure.py` (new)
- `reference/credit_advance_f04/fixtures/shared_exposure_v1.json` (new)
- `reference/credit_advance_f04/test_shared_exposure_contract.py` (new)
- `validation/2026-11-11-cr1110-shared-exposure-contract/README.md` (new)
- `docs/README.md` (one location-only index link added)

No machine, OpenAPI, CI, `.aiops`, `docs/tasks/`, locked-blob or
`reference/v0.3-rc1/` change. The boundary-vectors pack
(`settlement_credit_boundary_vectors.py`, its two fixtures and
`test_settlement_credit_boundary.py`) is unchanged; this node extends it.

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
| Several advances share one claim's exposure ledger; per-claim ceiling | partially covered: `test_mock_credit.py::CreditAdvanceMockTests.test_claims_do_not_share_a_ceiling_and_the_snapshot_stays_frozen`; boundary pack `S5_shared_exposure_two_advances` (ceiling refusal and exact residual) | E1 aggregates two advances on one claim; claim-level capacity is counted once per distinct `claim_id`; the group sum is reported, not enforced |
| Caller-supplied limit with no default | not covered for a cross-claim group | `LIMIT_REQUIRED` on omission; `LIMIT_INVALID` for `bool`, negative, float, string, `None`; inclusive `<=` boundary (E5) and over-limit fail-closed report (E2) |
| Frozen face unchanged after later settlement refund | sufficiently covered: `test_credit_properties.py::MachinePropertyTests.test_the_face_snapshot_stays_frozen_after_later_settlement_changes`; boundary pack `S3_face_snapshot_frozen_and_stable_view_claim` | E4 asserts the post-refund `CreditMachine.view` is byte-equal to the pre-refund view and pairs the gap with the §7.11 variance observer (`NOT_BOUND`, no repair) |
| Exposure moves only via existing transitions; repay keeps reservation, close releases it | sufficiently covered on the machine: `test_credit_fsm.py` lifecycle and default cases | E6 asserts the group-level intermediates: partial repay lowers outstanding but keeps the reservation; close releases it only at zero exposure |
| A defaulted advance retains reservation and outstanding | partially covered: `test_credit_fsm.py::CreditFsmTests.test_default_keeps_the_reservation_and_does_not_foreclose` | E3 aggregates three claims under one pool label including the `DEFAULTED` advance |
| Cross-claim debtor/pool grouping and legal debtor identity | not covered: the mock has no legal debtor identity (`legal_debtor_bound` false) | `group_id` is a caller label; mixed observation points fail `VIEW_BINDING_CONFLICT`; every observation maps to `NOT_BOUND` with repair `NONE` |

The new suite is source-informed, not clean-room verification.

## New tests and what each addresses

`test_shared_exposure_contract.py` adds 19 tests:

1. canonical fixture bytes, `FIXTURE_SHA256` pin, schema/provenance/contract/mapping;
2. every fixture view is a literal `CreditMachine.view` snapshot rebuilt by the machines;
3. all six scenarios replay to expected values;
4. aggregation formulas over exposed values only, claim dedupe and sorted claim entries;
5. cross-claim grouping is caller-supplied and not machine-enforced (E2; no debtor field in views);
6. a `DEFAULTED` advance still aggregates (E3);
7. limit is required with no default;
8. limit rejects `bool`, negative, float, string and `None`;
9. limit boundary is inclusive; one past it is over-limit and fail-closed;
10. frozen face unchanged after a full settlement refund, paired with the §7.11 variance (E4);
11. repay-then-close moves exposure only via transitions, with group-level intermediates (E6);
12. claim-field, `trade_id` and currency disagreements fail as `VIEW_BINDING_CONFLICT`;
13. an unfrozen view fails as `VIEW_NOT_FROZEN`, including a real pre-draw `APPROVED` view;
14. malformed or non-mock views, duplicate `advance_id`, empty/non-list groups and bad `group_id` fail as `VIEW_INVALID`;
15. observation is read-only and deterministic;
16. mapping is `NOT_BOUND` and all execution flags stay false on every fixture view;
17. loader rejects non-canonical bytes and a canonical but unpinned fixture;
18. the `--check` driver exits 0 with canonical JSON and exits 2 on usage error;
19. the §7.12 contract clause and the settlement §9.6 cross-reference exist.

The fixture was generated once through the module's `canonical()` and
`observe_shared_exposure()` from the test's machine captures (one-off script
outside the repository, not committed); expected values are machine-derived,
never hand-written.

## Commands and results

All Python commands ran in the foreground with `PYTHONDONTWRITEBYTECODE=1`.

| Command actually run | Actual result |
|---|---|
| `python3 -B reference/credit_advance_f04/test_shared_exposure_contract.py -v` | first run: 18 of 19 passed; the only failure was the contract-text test before §7.12 was written. After the contract edits: exit 0; 19 tests passed |
| `python3 -B reference/credit_advance_f04/shared_exposure.py --check` | exit 0; canonical JSON, 4365 bytes, fixture pin `cdb001701376c02cd3515bcdd939193922c960bdcaebf80ca8d3f0d7732c1c03` |
| CI reference-suite loop (`settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward`, `provider_facts`, `payment_effects`) | exit 0 for all seven: 224, 954, 230, 169, 397, 86 and 28 tests (credit suite 211 → 230 with the 19 new tests) |
| `check_openapi_contract.py` and `check_integration_gate_openapi.py` (plain plus `--self-test`) | 4 of 4 exit 0 |
| `python3 -m unittest integration_gate.test_offline_limits` | exit 0; 9 tests passed |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` (loopback only) | exit 0; 139 tests passed; self-test pass |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; all binaries ok, 139 passed / 0 failed (39 contract_edge_cases, 5 contract_invariants, 12 e4_state_model, 11 observation_slots, 32 performance_harness, 8 quarantine_capacity, 32 transitions) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0; no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `check_credit_evidence_map.py`, `check_evidence_map_rollup.py`, `check_settlement_evidence_map.py`, `check_contract_error_codes.py` (plain plus `--self-test`) | 8 of 8 exit 0; credit map rows=24 headings=24 citations=134 `COVERED=16 PARTIAL=4 NOT_COVERED=1 OPEN=3`; roll-up contracts=25; settlement map rows=27 headings=27 unchanged; error codes rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| Full `Stdlib offline document checks` block from `.github/workflows/protocol.yml` (all 65 invocations, plain and `--self-test`) | exit 0 for every invocation; 65 of 65, 0 failures. `check_docs_index.py`: `scanned=405 indexed=370 allowlisted=35` (the new validation record is linked once from `docs/README.md`); `check_ci_test_discovery.py`: `reference_suites=8 node_tests=8 modules=4 excluded=3` (the new test is reached by the existing credit-suite discovery); `check_ci_checker_wiring.py`: `scripts=36 plain=35 self_test=36 self_test_only=1` |

## Deviations from the design plan

- Heading count: the plan said the §0 Basis prose should go 22 → 23. The
  observed pre-work checker count was already 23 (the prose was stale at 22
  from before §7.11). With §7.12 the true count is 24; the prose now reads 24.
- Phase validation: the module additionally requires
  `phase ∈ {DRAWN, CLOSED, DEFAULTED}` (`VIEW_INVALID` otherwise). This is a
  strengthening consistent with the plan's "frozen/drawn advances only".
- E5 boundary split: the plan wanted exact and one-past in E5. E2 already
  pins the over-limit `false` case, so E5 pins the exact-boundary `within`
  case and the boundary test exercises `sum − 1` directly.
- Fetch: NOT_RUN under the supervisor's no-network rule (AGENTS §1 override).

## Contract classification

- Contract-defined and matching: §7.12 defines the aggregation formulas,
  claim-level dedupe, required caller-supplied limit with inclusive boundary,
  freeze stability through existing transitions, `NOT_BOUND` mapping and the
  `NOT_BOUND` refund component. All six fixture scenarios match.
- Contract-undefined characterizations: none newly asserted. Pre-draw grouping
  is explicitly undefined in this revision and fails closed as
  `VIEW_NOT_FROZEN`; the refund-driven per-claim gap remains the §7.11 /
  boundary-pack Class B characterization, unchanged.
- Contract violations: none found.
- New protocol commands, FSM phases, error-table entries or OpenAPI bytes: none.

## Non-claims and remaining uncertainty

The fixture is synthetic (`MOCK_CREDIT_F04_ONLY`, ledger `MOCK_EXPOSURE`) and
process-local. It does not establish durability, crash recovery, distributed
fencing, bank exactly-once, chain finality, live funds, accounting or legal
treatment, or production readiness. The limit is never given a default or a
product value; the product-limit owner is Astra and the legal-debtor owner is
the User (roadmap D-E, I10), both `UNDETERMINED`. `within_limit: true` is not an
acceptance or exposure authorization, and the group label is not a legal party.
A2 non-author exact-final-head review and completed/successful exact-head KTX
and KIX CI remain separate delivery gates, as does explicit human merge
authorization.
