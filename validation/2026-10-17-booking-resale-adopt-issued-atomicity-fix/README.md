# booking-resale-adopt-issued-atomicity-fix

Node: `plan-plan-booking-resale-adopt-issued-atomici`. Depends on: `booking-resale-admission-deepening`.
Audit floor A2. `astra_gate: None`, `user_merge: false`. Issue: none. Not program mode; no ASTRA markers
posted. Source: KIX planner run 1792193921 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no
implementation commit SHA, no final task head SHA and no exact-head CI run ID; local results below are not
exact-head CI. Exact-head CI belongs in the PR closure report (AGENTS section 11).

Observed `origin/main` and branch HEAD at session start: `7bdc99933c804b417b94d9dba40f13d370861cab`
(`git fetch origin main` left it unchanged; no delta).

## Locks

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

Changed paths: `reference/booking_resale_admission/resale_fsm.py`, `.../admission_fsm.py`, new
`.../test_adopt_issued_atomicity.py`, this record, one `docs/README.md` row. `mock_gates.py`,
`docs/contracts`, `reference/v0.3-rc1`, `.aiops`, `.github`, `runtime`, `docs/tasks` are unchanged.

## Defect

`adopt_issued` ran `_materialize` (register_show, reserve_slot, bind_order, observe_payment_fact, issue)
against the private `MockGates` with no rollback. A rejection from a later step
(`ORDER_BINDING_CONFLICT`, `PAYMENT_BINDING_CONFLICT`, any `_require`) left earlier gate mutations behind
while the journal stayed unchanged. Contract basis: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`
sections 10.7 and 11.5 (rejected commands are not journaled; restoring the same journal gives the same
`canonical_state` and `state_digest`).

Repro: `adopt_issued('tix-1', slot 0, 'ord-1')` accepted; `adopt_issued('tix-2', slot 1, 'ord-1', fresh pay)`
rejected `ORDER_BINDING_CONFLICT`; the Resale `state_digest` then changed and
`restore(export_journal()).canonical_state()` differed from `canonical_state()`; a following
`adopt_issued('tix-3', slot 1, 'ord-3')` was rejected `SLOT_OCCUPIED` although a machine restored from the
same journal accepts it. The Admission machine showed the same live-versus-restored divergence, but its
digest did not change because `canonical_state` does not render gate slots.

## Fix

Both machines gain a private `_commit_adopt(normalized, record)`. It swaps `self._gates` for a `deepcopy`,
runs `_materialize`, inserts the right/credential and calls `_invariant()`; on any exception it restores the
original gates object, removes the inserted record and re-raises. Scratch-copy was chosen over
validate-first because validate-first would duplicate five `MockGates` predicates (window, slot occupancy,
order binding, payment binding, issue) into two files. `MockGates` holds only dict/list/int/str/bool/None,
and nothing outside the three FSM files reads `._gates`. No command, error code, field, option or policy
value was added; no accepted path changed.

Unit boundary: `_accept` (journal append) stays outside the unit; with validated inputs its own `_require`
is unreachable, and widening it was not in scope.

Line pins: `docs/contracts/READ_MODEL_SOURCE_MAP.md` section 6 pins line numbers in both FSM files. The
in-place edit is line-neutral (15 lines replaced by 15 in `resale_fsm.py`, 19 by 19 in `admission_fsm.py`),
the helper is appended after the last pinned line, and `deepcopy` is imported function-locally so that no
top-level import shifts an anchor. `scripts/check_read_model_source_map.py` passes.

## No accepted-path change (digest probe)

Probe (kept outside the repo, `/tmp/kix-probe/probe.py`, run `python3 -I`): wraps `ResaleMachine.__init__`
and `AdmissionMachine.__init__` to register every instance (including those built by `restore`), runs
`unittest` discovery over the existing `test_*.py` files only, and after each test prints
`test_id, machine kind, index, state_digest, len(export_journal())`. Run before any edit and after the fix
(new test file excluded): 78 rows, byte-identical (`cmp` exit 0), sorted-output sha256
`5a725f356f52b74cf4536add2a7709cd01a3b203678d00d88d723996009b4fb6`. Two pre-change runs were also
byte-identical to each other.

## New tests fail before, pass after

`test_adopt_issued_atomicity.py`, run against the unmodified FSMs (created before any FSM edit):
`Ran 10 tests ... FAILED (failures=4, errors=6)`. Excerpts:

- Resale `test_order_binding_conflict_leaves_no_trace` / `test_payment_binding_conflict_leaves_no_trace`:
  `AssertionError: '610d3b4c...' != '89f5ee8b...'` (state_digest changed by the rejected call).
- Resale/Admission `test_invariant_failure_after_materialize_rolls_back`: digest (Resale) or state
  (Admission, leftover credential) differs from a fresh machine.
- Admission `test_order_binding_conflict_leaves_no_trace` / `test_payment_binding_conflict_leaves_no_trace`:
  `AdmissionError: SLOT_OCCUPIED` on the follow-up adopt (digest and restore equality held, as classified).
- Both `test_rejected_right_can_be_adopted_afterwards`: `MOCK_INVARIANT` on the retry.
- Both `test_rejection_after_show_registration_leaves_no_trace`: the follow-up failed. In that first run the
  follow-up reused the idempotency key with a different body (`IDEMPOTENCY_CONFLICT`, a test bug); the key
  was then made distinct, and the pre-fix leak (`SHOW_BINDING_CONFLICT`) was not re-run on unmodified code.
  That one case's failing-before evidence is therefore weaker than the others.

After the fix: the 10 new tests pass (also under `PYTHONHASHSEED=0` and `1`), and the full discover run is
57 tests OK.

## AGENTS section 8 classification

- Resale restore-equality after a rejected adopt (10.7): class C, explicit contract violation; fixed here.
- Admission live-versus-restored gate-slot divergence (11.5): class B in observable state (digest does not
  render gate slots); removed by the same change.

## AGENTS section 7 mapping

| Requirement | Coverage |
|---|---|
| Rejected adopt after gate mutation | not covered before; now `test_adopt_issued_atomicity.py` |
| Rejected commands not journaled (other commands) | sufficiently covered (e.g. `test_resale_fsm.py` lines 641-642, 696) |
| Restore equality on accepted sequences | sufficiently covered (`test_resale_fsm.py` 644-646, reconcile tests) |
| Restore equality after a rejected adopt | not covered before; now new file |
| Accepted paths | covered by the existing suite plus the digest probe |

## Commands actually run (local, not exact-head CI)

See the evidence table in the final session report: all listed commands exited 0 (existing suite 57 OK incl.
new tests; `integration_gate.test_http_gate readiness.test_faults` OK; settlement 43, credit 48,
ai_delegation 22, token_reward 61 OK; the seven doc/contract checkers and the two openapi checks, plain and
`--self-test`, exit 0). Rust, Sui, Node and ZK steps of `ktx-kernel.yml`/`protocol.yml` were not run (no
Rust touched); the locked-blob check stands in.

## Follow-ups and non-claims

- When `plan-booking-resale-admission-seeded-property` lands its `test_gate_properties.py`, the two
  `expectedFailure` markers in its `RejectedAdoptAtomicityTests` must be removed (they would report an
  unexpected success). This node neither creates nor depends on that file.
- `ReservationMachine` and other commands were not audited for the same pattern.
- In-memory reference mocks only: no durability, production, chain-finality or distributed-fencing claim.

This record raises no evidence grade, marks nothing reviewed or operational, and keeps the operational
count at 0.
