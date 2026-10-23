# bra-fsm-error-code-coverage

Node: `plan-bra-fsm-error-code-coverage`. Extends `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` and `scripts/check_contract_error_codes.py` from the four contract error-code tables (139 rows) to seven, adding `BOOKING_RESALE_ADMISSION_GATES.md` sections 10.8 and 11.6 and `CREDIT_ADVANCE_F04.md` section 7.8 (50 rows, keys BRA-RES, BRA-ADM, F04-FSM). Adds six tests for the seven codes that were raised but named by no test.
Issue: none. Depends on: `booking-resale-admission-deepening`, `f04-mock-deepening`, `plan-contract-error-code-coverage`. Audit floor A2. Not an ASTRA program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA or final task head SHA, and no exact-head CI run exists for this work; those belong in the pull request closure report (AGENTS.md section 11).

Observed `origin/main` = branch HEAD = `77da4bcc37e227c549929740a30e4ac544efe4db`. Per the supervisor's rule this session ran no network or GitHub action, so `git fetch origin main` was not run; the value is the local `origin/main` ref, not a re-fetched one.

**This record and the map are a builder-authored reading, not an independent review and not an acceptance. No grade is raised, nothing is claimed for production, and the checker proves only that a code name appears on a raise path or in a test body.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `git status --short` and `git diff --stat` over `reference/v0.3-rc1`, `runtime`, `.aiops`, `docs/tasks`, `docs/contracts`, `docs/decisions` are empty.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_contract_error_codes.py` | Three `TABLES` entries (BRA-RES → `resale_fsm.py`, BRA-ADM → `admission_fsm.py`, F04-FSM → `credit_fsm.py`); `ROW_START` is generated from the key set; docstring names the seven tables; `self_test` gains three new-key fixtures (added contract code, removed raise site, citation that is not a derived site). |
| `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` | Header names seven tables and both nodes; "Tables read" gains three rows; the RAISED definition lists raise files per key; Result and Non-claims updated; 50 rows added; `Counts:` regenerated. |
| `reference/booking_resale_admission/test_resale_fsm.py` | Two tests: `test_unknown_hold_and_conflicting_hold_id_are_rejected` (`UNKNOWN_HOLD`, `HOLD_BINDING_CONFLICT`), `test_reservation_bound_commands_need_a_ticket_source` (`TICKET_SOURCE_REQUIRED`, adopt and list paths). |
| `reference/booking_resale_admission/test_admission_fsm.py` | Four tests: `test_adopt_with_a_reservation_but_no_ticket_source_is_required` (`TICKET_SOURCE_REQUIRED`), `test_ticket_source_that_breaks_is_unavailable_not_silent` (`TICKET_SOURCE_UNAVAILABLE`, set_clock and view paths), `test_stale_presentation_answer_is_credential_stale` (`CREDENTIAL_STALE`), `test_settlement_source_that_breaks_fails_closed` (`SETTLEMENT_SOURCE_UNAVAILABLE`). |
| `docs/README.md` | Index row updated (four tables to seven, extension record linked); one bullet under the 2026-10-19 record index. |
| `validation/2026-10-19-bra-fsm-error-code-coverage/README.md` | This record. |

## AGENTS.md section 7: existing coverage

New rows: BRA-RES=20 (booking section 10.8), BRA-ADM=15 (section 11.6), F04-FSM=15 (F04 section 7.8). Of the 50, 43 were RAISED and ASSERTED by tests that already existed (sufficiently covered; the map cites a raise site and a test per row). Seven were raised but named by no test (not covered) and are closed by the six new tests above. F04-FSM had no gap. After this change all 189 rows are RAISED and ASSERTED.

## Class B and class C findings

None. Every code in the three FSM-added tables is raised in its mapped FSM file and reached by a caller input in the new or existing tests; no row needed a contract-undefined fence or a mock change. One characterization carried over from the first node stands: `SETTLEMENT_FACE_FIELDS` (F04) is named only by the `assertIn` coverage guard in `test_credit_properties.py`; the seeded oracle drives it.

## Commands run

| Command | Result |
|---|---|
| `git status`; `git rev-parse HEAD`; `git rev-parse origin/main` | clean tree; both `77da4bcc37e227c549929740a30e4ac544efe4db` (no fetch; local ref) |
| `git hash-object` of the two locked files, before and after | both blobs match section 4 |
| `python3 scripts/check_contract_error_codes.py --emit` | exit 0; used to draft rows; before the new tests it showed exactly the seven GAP rows listed above |
| `cd reference/booking_resale_admission && python3 -m unittest test_resale_fsm test_admission_fsm` | 27 tests OK (6 new included) |
| `python3 scripts/check_contract_error_codes.py` | exit 0: `SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0` |
| `python3 scripts/check_contract_error_codes.py --self-test` | exit 0, `self-test: pass`; the 21 prior breaks plus the three new BRA-RES fixtures (added contract code, removed raise site, non-derived citation) are all caught |
| `python3 -m unittest discover` over `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` (the protocol.yml suite loop) | 48, 155, 48, 70, 61 tests, all OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 71 tests OK |
| `check_status_register`, `check_rs_profile_traceability`, `check_read_model_source_map`, `check_i12_proof_ids`, `check_delegation_layer_matrix`, `check_rs_predicate_evidence_map`, `check_rs_im_evidence_map`, `check_tl_predicate_evidence_map`, `check_docs_index`, `check_openapi_contract`, `check_integration_gate_openapi`, each plain and `--self-test` | exit 0 |
| `python3 scripts/check_sdk_client.py` | not run to a verdict: local `node` is 20.19.2 and `toolchains.json` requires nodeMajor 24 |
| `git diff --stat` / `git status --short` over `reference/v0.3-rc1`, `runtime`, `.aiops`, `docs/tasks`, `docs/contracts`, `docs/decisions` | empty |

Not run: the `.venv`-dependent verification scripts (`verify_runtime.py`, `verify_commerce.py`, `verify_canonical.py`, `verify_runtime_architecture.py`, storage probes), `bootstrap.sh`, the localnet/Move legs, the ZK npm legs, the SDK npm legs, and all of `ktx-kernel.yml` (Cargo). None of the paths those steps read changed; the kernel-relevant check is the locked-blob match above.

## Non-claims

Not an independent review. No production, durability or grade claim. ASSERTED shows a name in a test body, not what the test asserts or that all callers can reach it. Tables outside the seven named ones are not read: the booking reservation machine's section 9 rejections (`CANCEL_AFTER_ISSUE`, `UNKNOWN_SETTLEMENT`, the section 9.5 settlement rows) are documented inline in transition and prose tables, not in a "codes this machine adds" table, so this node does not enumerate them. `MOCK_INVARIANT` stays excluded. Exact-head CI is not yet known.
