# read-model-contract-fixture-prep

Node: `plan-read-model-contract-fixture-prep`. Issue: none (loop-proposed node,
not in `.aiops/program.json`). Depends on `read-model-contract`,
`openapi-catalogue-promotion`. Audit floor A2. `astra_gate: None`,
`user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792464145.

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation head SHA and no final task
head SHA, and no KTX kernel verification or KIX protocol verification run
exists for this work. The exact-head CI results belong in the pull request
closure report (AGENTS.md section 11).

Observed `origin/main` = branch HEAD = `70000ed8a189b8b3b92a4a858d7cce1ed43e5d7b`,
on the worktree `origin/main` ref. No `git fetch` was run: the supervisor
forbids network/GitHub actions in builder sessions, so AGENTS.md section 1's
read-only fetch was skipped and the recorded base is the ref the worktree
was created from.

**The read-model implementation (`read-model-reference`) is not merged, and
these fixtures are candidate evidence only — not conformance evidence.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs`
`69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
`b607996c83a119c349f1cc90469ac1ba82764e20`. Both match the required blobs
before and after. `reference/v0.3-rc1/**`, `docs/tasks/`, `.aiops/`,
`docs/contracts/`, `.github/` are untouched.

## What this change does

- New `reference/read_model/generate_fixtures.py`: stdlib-only, seeded
  (`SEED = 20261020`, `random.Random`) scenario driver. Builds the five
  machines via their public `REPLAYABLE` commands only, then emits
  per-domain JSON vectors. List-page/cursor helpers are named `expected_*`;
  no `def list_shows(`, `def list_bookings(`, `def list_open_listings(`
  exists, so the source-map absence anchors A04/A05/A12/A21 stay true.
- New `reference/read_model/vectors/{manifest,reservation,resale,admission,settlement,credit}.json`:
  committed golden vectors covering all 13 approved query names — point
  `ok`/`error` answers, list `population`/`pages`/`cursor_cases`
  (`FIXTURE_CURSOR_V1`; `CURSOR_MISMATCH`, `SNAPSHOT_CHANGED`,
  `INVALID_LIMIT`, `INVALID_ID`), `accepted_through` watermarks, and
  `visibility` marked `NOT_BOUND` with `RECOMMENDATION_NOT_DECISION`
  subsets. `list_open_listings.open_phase_predicate` is `NOT_BOUND`.
- New `reference/read_model/README.md`: candidate-evidence doc (seeds,
  regeneration command, NOT_BOUND markers, non-claims).
- New `reference/booking_resale_admission/test_read_model_fixtures.py`:
  stdlib `unittest` self-check (byte-determinism, every expected answer
  replayed against the live generating model, reserved-key absence,
  always-false flags, non-mutation `canonical_state`/`export_journal`/
  `logical_time_ms` across view calls, two replays byte-identical).
- `docs/README.md`: one index bullet linking this record.
- The five `ReadObservationV1` keys plus `subject_scope`/`profile_revision`
  are absent from all emitted vectors (asserted by the self-check).

Not done on purpose: no query implementation, no wire binding, no
catalogue/OpenAPI/`protocol_contract.json` change, no capability-register
grade change, no `UNDETERMINED` value filled (limit cap/default, cursor
lifetime, sort key, visibility matrix, open-phase predicate, error code
names, `query_digest` algorithm all stay `NOT_BOUND`/`UNDETERMINED · Astra`).

## Changed paths

| Path | Change |
|---|---|
| `reference/read_model/generate_fixtures.py` | New seeded generator (~1160 lines). |
| `reference/read_model/vectors/*.json` | 6 new committed vector files. |
| `reference/read_model/README.md` | New candidate-evidence doc. |
| `reference/booking_resale_admission/test_read_model_fixtures.py` | New stdlib self-check (6 tests). |
| `validation/2026-10-20-read-model-contract-fixture-prep/README.md` | This record. |
| `docs/README.md` | One index bullet. |

## AGENTS.md section 7: existing coverage mapping

| Task requirement | Existing coverage | Class before | New artifact |
|---|---|---|---|
| Point-query expected answers | Each FSM test already calls the same `view*` on its own scenarios (`test_reservation_fsm.py`, `test_resale_fsm.py`, `test_admission_fsm.py`, `test_settlement_fsm.py`, `test_credit_fsm.py`) | partially covered | Cross-machine seeded scenario vectors + manifest watermarks |
| List populations/pages/cursors | None — lists are `SOURCE_MISSING`; no implementation exists (RMQ:403) | not covered | `FIXTURE_CURSOR_V1` model vectors incl. mismatch/snapshot-change cases |
| `*_SOURCE_UNAVAILABLE` decisions | `test_admission_fsm.py` covers VENUE/OWNERSHIP/SETTLEMENT paths on commands | partially covered | `view_credential` decision vectors incl. TICKET_SOURCE_UNAVAILABLE, SETTLEMENT_SOURCE_REQUIRED |
| Deterministic replay inputs for later nodes | None | not covered | Committed JSON + `--check` byte comparison + self-check |

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** All `view*` outputs matched the RMQ
section-2 key lists; `SettlementMachine`/`CreditMachine` have no clock and
`accepted_through` omits `logical_time_ms` exactly there.

**B. Contract-undefined characterizations.** Fixture cursor format
`FIXTURE_CURSOR_V1`, `fixture_limit`, `FIXTURE_ORDERING identifier-asc`, and
the modeled `CURSOR_MISMATCH`/`SNAPSHOT_CHANGED`/`INVALID_LIMIT` kinds are
fixture parameters, not decided contract values; error code names stay
`NOT_BOUND`.

**C. Explicit contract violations.** None found; no locked file touched.

## Commands actually run and results

| Command | Result |
|---|---|
| `git rev-parse HEAD`; `git rev-parse origin/main`; `git status` | both `70000ed8a189b8b3b92a4a858d7cce1ed43e5d7b`; clean tree; branch `agent/kix-plan-read-model-contract-fixture-prep` (`git fetch` skipped per builder no-network rule) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before+after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — both match |
| `python3 reference/read_model/generate_fixtures.py` | wrote 6 vector files, seed=20261020 |
| `python3 reference/read_model/generate_fixtures.py --check` | `fixture vectors ok: files=6 seed=20261020` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Ran 162 tests — OK (includes the 7 new self-check tests) |
| `python3 scripts/check_docs_index.py` + `--self-test` | ok / `self-test: pass` |
| `python3 scripts/check_read_model_source_map.py` + `--self-test` | ok (queries=13 anchors unchanged) / `self-test: pass` |
| `python3 scripts/check_openapi_contract.py` + `--self-test`; `python3 scripts/check_integration_gate_openapi.py` + `--self-test` | ok / `self-test: pass` (catalogue bytes untouched) |
| `for s in settlement_f01_f03 credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/$s -t reference/$s; done` | all OK |
| Other `protocol.yml` doc checkers (status_register, rs_profile_traceability, i12_proof_ids, delegation_layer_matrix, rs_predicate, rs_im, tl_predicate, contract_error_codes, adapter_identity, v5_transition) each + `--self-test` | all ok / `self-test: pass` — no corresponding files touched |
| Rust/Node/Sui/ZK/integration-gate CI steps | not run — no corresponding paths touched |

## Non-claims

- Vectors pin current in-memory `view*` outputs; a later legitimate source
  change will fail the self-check — regenerate under a new seed record
  rather than weakening it.
- No payment, issuance, admission, durability, chain-finality, or
  production claim. No real funds, PG/bank/KYC calls, public endpoints,
  Sui testnet/mainnet, storage engine, or new protocol command.
