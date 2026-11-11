# cr1110-settlement-variance-contract — builder evidence

Node: `cr1110-settlement-variance-contract`, SUNBURN-Golden/kix-protocol.
Integration step 3 (CR-CAPITAL-1110 #1). Issue: none. Task input: the
supervisor-supplied node specification in this session; there is no task
document under `docs/tasks/` for this node. This is not ASTRA program mode: no
signer, no delivery/blocked marker, no comment.

Branch: `agent/kix-cr1110-settlement-variance-contract`.

## Identity and gates

| Item | Observed value |
|---|---|
| Local `origin/main`, branch base and initial HEAD | `a1e44a64f0ebf25a9e983bf7dff3f62aaeade490` (merge #439); all three are equal |
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

- `docs/contracts/CREDIT_ADVANCE_F04.md` (§7.11 clause added)
- `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` (unnumbered §9.6 cross-reference)
- `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md` (§7.11 row and Counts)
- `docs/status/EVIDENCE_MAP_ROLLUP.md` (F04 Counts copy)
- `reference/credit_advance_f04/README.md` (settlement-variance section)
- `reference/credit_advance_f04/settlement_variance.py` (new)
- `reference/credit_advance_f04/fixtures/settlement_variance_v1.json` (new)
- `reference/credit_advance_f04/test_settlement_variance_contract.py` (new)
- `validation/2026-11-10-cr1110-settlement-variance-contract/README.md` (new)
- `docs/README.md` (one location-only index link added)

No machine, OpenAPI, CI, `.aiops`, `docs/tasks/`, locked-blob or
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
| Settlement view exposes `obligations[].outstanding`; credit `view_claim` exposes frozen `open_face` | sufficiently covered: `test_credit_fsm.py` bound-draw and freeze cases; `reference/settlement_f01_f03/test_mock_settlement.py` distribution cases | The new observer reads those exact fields; no machine arithmetic is re-derived |
| Frozen credit face after later settlement change | sufficiently covered: `test_credit_properties.py::MachinePropertyTests.test_the_face_snapshot_stays_frozen_after_later_settlement_changes` | V2/V3/V4 fixtures pair a later settlement view with a pre-change frozen face |
| Refund reclassification makes settlement outstanding zero | sufficiently covered: `reference/settlement_f01_f03/test_settlement_multi_payee_refund.py` and `test_mock_settlement.py` | V3 fixture observes the post-refund view against the frozen credit face |
| No default tolerance / caller-supplied policy value | not covered for a cross-contract variance | The module rejects omission (`TOLERANCE_REQUIRED`), `bool`, float, string, `None` and negative values (`TOLERANCE_INVALID`); no default is set |
| Non-zero observation disposition | partially covered as a Class B reconciliation-gap report in `test_settlement_credit_boundary.py` (different code path) | §7.11 defines a cross-contract observation and maps it to `NOT_BOUND` with repair `NONE`, fail-closed, no exposure authority |

The new suite is source-informed, not clean-room verification.

## New tests and what each addresses

`test_settlement_variance_contract.py` adds 15 tests:

1. canonical fixture bytes, `FIXTURE_SHA256` pin, schema/provenance/contract;
2. every fixture view is a literal `MockSettlement.view` / `MockCredit.view_claim` snapshot;
3. all six scenarios replay to expected values;
4. formula and `POSITIVE`/`ZERO`/`NEGATIVE` sign convention;
5. tolerance is required with no default;
6. tolerance rejects `bool`, negative, float, string and `None`;
7. tolerance boundary is inclusive; one past it is out-of-tolerance and fail-closed;
8. `claim_id`/`trade_id`/currency mismatches fail as `VIEW_BINDING_CONFLICT`;
9. an unfrozen credit view fails as `VIEW_NOT_FROZEN`;
10. malformed or non-mock views fail as `VIEW_INVALID`;
11. observation is read-only and deterministic;
12. mapping is `NOT_BOUND`; companions are diagnostic and excluded from the formula;
13. loader rejects non-canonical bytes and a canonical but unpinned fixture;
14. the `--check` driver exits 0 with canonical JSON and exits 2 on usage error;
15. the contract clause and the settlement §9.6 cross-reference exist.

## Commands and results

All Python commands ran in the foreground with `PYTHONDONTWRITEBYTECODE=1`.

| Command actually run | Actual result |
|---|---|
| `python3 -B reference/credit_advance_f04/test_settlement_variance_contract.py -v` | exit 0; 15 tests passed |
| `python3 -B reference/credit_advance_f04/settlement_variance.py --check` | exit 0; canonical JSON with fixture pin `f2db31f337bc44d5931e97f0e5c57d529e8f1f444339366b50178c304df38b76` |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0; 224 tests passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 211 tests passed |
| CI reference-suite loop (`settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward`, `provider_facts`, `payment_effects`) | exit 0 for all seven: 224, 954, 211, 169, 397, 86 and 28 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; 32 passed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0; no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `check_openapi_contract.py` and `check_integration_gate_openapi.py` (plain plus `--self-test`) | 4 of 4 exit 0 |
| `python3 -m unittest integration_gate.test_offline_limits` | exit 0; 9 tests passed |
| `check_credit_evidence_map.py`, `check_settlement_evidence_map.py`, `check_evidence_map_rollup.py`, `check_contract_error_codes.py`, `check_class_b_index.py`, `check_ci_test_discovery.py`, `check_ci_checker_wiring.py` (plain plus `--self-test`) | 14 of 14 exit 0; credit map rows=23 headings=23 `COVERED=15 PARTIAL=4 NOT_COVERED=1 OPEN=3`; roll-up contracts=25 |
| Full `Stdlib offline document checks` block from `.github/workflows/protocol.yml` (all 65 invocations, plain and `--self-test`) | exit 0 for every invocation; `check_docs_index.py`: `scanned=404 indexed=369 allowlisted=35` (the new validation record is linked once from `docs/README.md`); `check_contract_error_codes.py`: `rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0` |

## Contract classification

- Contract-defined and matching: §7.11 defines the formula, sign convention,
  required caller-supplied tolerance, `NOT_BOUND` mapping, diagnostic
  companions and the `NOT_BOUND` refund component. All six fixture scenarios
  match.
- Contract-undefined characterizations: none newly asserted. A positive
  observation (V4) is produced by pairing snapshots captured at different
  observation points; §7.11 states the observer reports the arithmetic and does
  not decide which view is current or authoritative.
- Contract violations: none found.
- New protocol commands, FSM phases, error-table entries or OpenAPI bytes: none.

## Non-claims and remaining uncertainty

The fixture is synthetic (`MOCK_SETTLEMENT_ONLY` /
`MOCK_CREDIT_F04_ONLY`) and process-local. It does not establish durability,
crash recovery, distributed fencing, bank exactly-once, chain finality, live
funds, accounting or legal treatment, or production readiness. Tolerance is
never given a default or a product value; the future binding owner is the User.
`within_tolerance: true` is not an acceptance or exposure authorization. A later
binding of the refund component and any scheduled observation point remain open
and owner-named in §7.11. A2 non-author exact-final-head review and
completed/successful exact-head KTX and KIX CI remain separate delivery gates,
as does explicit human merge authorization.
