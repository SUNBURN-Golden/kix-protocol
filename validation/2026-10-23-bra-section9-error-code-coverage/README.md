# bra-section9-error-code-coverage

Node: `plan-plan-bra-section9-inline-error-code-cove`. Task input: the supervisor's
node specification and owner decision in this session; no issue or corresponding
file under `docs/tasks/` exists. Dependencies: `plan-bra-fsm-error-code-coverage`,
`plan-contract-error-code-coverage`. Audit floor A2; not an ASTRA program-mode
session. Builder-authored evidence, not independent review or acceptance.

## Scope and decision

The owner approved Option (c): enumerate the ten codes from the booking contract's
§9.2 effect column and §9.5 code column that have literal raise sites in
`reservation_fsm.py`. A fixed exclusion list removes six pass-through codes:
`CLOCK_REGRESSION`, `SLOT_OCCUPIED`, `RESERVATION_EXPIRED`, `ADMISSION_LOCKED`,
`RIGHT_NOT_ACTIVE` (already COVERED under BRA) and `UNKNOWN_SETTLEMENT` (already
COVERED under SET). State/slot labels, `CONSUMED_ONCE` and `MOCK_INVARIANT` are
excluded. The parser preserves first appearance order and de-duplicates repeats;
it does not intersect contract codes with current raise sites. Future codes in
these columns therefore require documentation even if no source site exists.

No checker status/taxonomy, contract, mock or FSM changed. No root
`DECISION_REQUIRED.md` was present at session start, so none needed removal.

## Source anchors and publication boundary

- Branch: `agent/kix-plan-plan-bra-section9-inline-error-code-cove`.
- Observed local `origin/main`: `a3f0fea3160fdea2f59fa8658573be173e242074`.
- Starting and unchanged branch HEAD/base: `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`.
- The base is an ancestor of the local `origin/main`, which includes later merges
  #262 through #268 (18 commits including merge-side commits). No rebase or merge
  was performed. Thus the supplied "from latest main" description differs from
  the local refs observed at session start.
- The supervisor prohibits network/GitHub actions and commits. Consequently
  `git fetch origin main` was not run; the observed ref is not freshly fetched.
  There is no new implementation or final task commit SHA. The supervisor owns
  commit/publication and exact-head review/CI.
- Exact-head KTX and KIX CI: not run or queried; run ID/status/conclusion unknown.
  No merge occurred, so no merge SHA or post-merge CI applies. Local READY is a
  builder handoff, not a merge proposal.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_contract_error_codes.py` | BRA-RES9 key, reservation-only raise sources, two-column inline parser, fixed exclusions, positive parser control and six negative §9 self-tests. |
| `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` | Tables read, RAISED scope, ten cited COVERED rows, 199-row counts, result and narrowed Non-claims. |
| `docs/README.md` | Coverage row and dated validation-record index link. |
| `validation/2026-10-23-bra-section9-error-code-coverage/README.md` | This record. |

## Existing coverage mapping (AGENTS.md §7)

Before adding tests, inspected existing reservation tests and derived the full
suite-wide ASSERTED sites with `--emit`. All ten new rows were already RAISED and
ASSERTED (sufficiently covered); no reference test addition was needed. The map
cites reservation tests specifically rather than incidental assertions in other
machines. Paths below are relative to `reference/booking_resale_admission/`.

| Codes | Existing asserting test |
|---|---|
| `ALREADY_CONSUMED`, `CANCEL_AFTER_ISSUE` | `test_reservation_fsm.py::ReservationFsmTests.test_cancel_after_issue_and_duplicate_consume` |
| `COMPENSATION_UNDEFINED`, `TERMINAL_IMMUTABLE` | `test_reservation_fsm.py::ReservationFsmTests.test_cancel_before_payment_frees_and_payment_blocks_compensation` |
| `EXTERNAL_UNSUPPORTED` | `test_reservation_fsm.py::ReservationFsmTests.test_external_attempts_do_not_journal_and_resale_is_absent` |
| `SETTLEMENT_NOT_COMMITTED` | `test_reservation_fsm.py::ReservationFsmTests.test_settlement_gate_refuses_uncommitted_finality` |
| `SETTLEMENT_SOURCE_REQUIRED`, `SETTLEMENT_AMOUNT_MISMATCH`, `SETTLEMENT_VIEW_REJECTED` | `test_reservation_fsm.py::ReservationFsmTests.test_bound_issue_checks_gross_and_replays_only_with_the_commit_view` |
| `SETTLEMENT_BINDING_CONFLICT` | `test_reservation_rejection_atomicity.py::ReservationRejectionAtomicityTests.test_bind_settlement_conflict_leaves_no_trace` |

The parser and missing-§9-citation regression requirements were not covered.
New checker controls close those gaps: an inline fixture checks column selection,
order, de-duplication and exclusions; negative mutations remove a raise citation,
remove an assertion citation, add a code to each target column, remove the §9.5
heading and malform a §9.5 row. Mutations are in memory only.

## Commands and actual results

Commands ran from the repository root unless stated otherwise. Read-only source
inspection used `rg`, `sed`, `cat`, `git log`, `git diff` and `git merge-base`.

| Command | Result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse origin/main HEAD` | Initially clean; branch and SHA values above. |
| `git log --oneline HEAD..origin/main`; `git merge-base HEAD origin/main` | Later merges #262–#268; merge base equals task HEAD above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before work: both required blobs match (values below). Final check recorded below. |
| `python3 scripts/check_contract_error_codes.py --emit > /tmp/bra-section9-emitted.md` | Exit 0; ten BRA-RES9 rows, all COVERED, no GAP. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; `SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0`. |
| `python3 scripts/check_contract_error_codes.py --self-test` (first run) | Exit 1: the §9.2 added-code mutation hit an earlier prose occurrence of CLOCK_REGRESSION. Fixed the fixture to match the entire transition-table row; parser behavior did not change. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_reservation*.py'` | 85 tests, OK (narrow verification). |
| `python3 scripts/check_contract_error_codes.py --self-test` (after fixture fix, standalone and again in the workflow block) | Exit 0; 30 negative mutations detected, including all six new §9 mutations; positive extractor controls also pass. |
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" || exit "$?"; done` | Exit 0; respectively 180, 162, 142, 70, 156 tests, all OK. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0; 82 tests, OK. Python emitted an unclosed-file ResourceWarning; it did not fail the run. |
| `python3 scripts/check_openapi_contract.py`; same with `--self-test` | Both exit 0; pin OK, 84 commands (40 core, 44 FSM); self-test pass. |
| `python3 scripts/check_integration_gate_openapi.py`; same with `--self-test` | Both exit 0; 84 commands, productionEndpoint=false, publicHost=false; self-test pass. |
| `git diff --check` | Exit 0. |
| `git rev-list --count HEAD..origin/main` | 18. |
| `git diff --quiet HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks docs/contracts docs/decisions .github/workflows`; `git status --short --` the same paths | Exit 0; empty status. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after work) | Both match the required blobs below. |
| Python comparison of `git ls-files reference/v0.3-rc1`, `git ls-tree -r HEAD reference/v0.3-rc1` and `git hash-object --stdin-paths` | All 108 tracked historical-reference file blobs match HEAD. |
| `python3 --version` | Python 3.13.5 locally; protocol CI requests 3.12. |

Executed every command from the `Stdlib offline document checks` run block in
`.github/workflows/protocol.yml` with a foreground Python subprocess runner;
all 27 invocations exited 0. The table lists each check, and "both" means the
plain command and the same command with `--self-test`:

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` (both) | Exit 0. |
| `python3 scripts/check_rs_profile_traceability.py` (both) | Exit 0. |
| `python3 scripts/check_read_model_source_map.py` (both) | Exit 0. |
| `python3 scripts/check_docs_index.py` (both) | Exit 0; new validation record is indexed. |
| `python3 scripts/check_i12_proof_ids.py` (both) | Exit 0. |
| `python3 scripts/check_delegation_layer_matrix.py` (both) | Exit 0. |
| `python3 scripts/check_rs_predicate_evidence_map.py` (both) | Exit 0. |
| `python3 scripts/check_rs_im_evidence_map.py` (both) | Exit 0. |
| `python3 scripts/check_tl_predicate_evidence_map.py` (both) | Exit 0. |
| `python3 scripts/check_contract_error_codes.py` (both) | Exit 0; 199 COVERED rows and self-test pass. |
| `python3 scripts/check_adapter_identity_map.py` (both) | Exit 0. |
| `python3 scripts/check_v5_transition_evidence_map.py` (both) | Exit 0. |
| `python3 scripts/check_readiness_evidence_map.py` (both) | Exit 0. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; no plain host acceptance evaluation. |

These are the closest local CI checks for the changed checker/status/index paths,
plus the protocol workflow's offline reference, integration and OpenAPI steps.
Not run: Rust/Cargo/Clippy, architecture verifiers, bootstrap, `.venv` runtime/
commerce/canonical/storage verification, Move/localnet, ZK and SDK/npm jobs.
Their inputs were not changed; no full-workflow or hosted-CI pass is claimed.

## Locks and protected scope

Required kernel blobs:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

Neither locked file was edited or transiently mutated. `reference/v0.3-rc1/**`,
`.aiops/`, `docs/tasks/`, contracts, decisions, mocks, FSMs and CI definitions were
not edited. No credentials, external calls or production runtime were required.

## Findings, limits and deviations

No contract violation, new contract-undefined characterization, CLASS_B row or
CLASS_C stop was found in the approved scope. All 199 map rows are COVERED.
Existing coverage was sufficient, so no duplicate reference tests were added.
Owner-approved re-scoping is the deliberate deviation from the initial sixteen-code
proposal; the six pass-throughs remain explicit Non-claims for BRA-RES9.

ASSERTED means a literal code name occurs in a test body, not that every caller
path is reached or independently verified. Only the named table columns are
enumerated; surrounding §9 prose is not a separate code source. The checker is a
source-informed convenience check, not a protocol or production-readiness proof.
No grade, durability, real-money, chain-finality or operational claim is made.
Independent review and exact-head hosted CI remain supervisor follow-ups.
