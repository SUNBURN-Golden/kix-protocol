# Local readiness conformance

Source node: `.aiops/program.json`, `k-readiness-conformance-suite`, at
`b6373c2448ac947d245851abf7c4d9a00e70f5c9`. Canonical dependencies: none.
Scope follows PROGRAM_DECISIONS_20260928 §4 and READINESS_RUNTIME.md.
This is test infrastructure, not backend implementation or adoption.

`conformance.BackendConformance` contains the existing public-FSM fault cases.
Combine it with `unittest.TestCase` and set `backend` to a test adapter:

```python
class CandidateTests(BackendConformance, unittest.TestCase):
    backend = ApprovedCandidateAdapter()
```

No candidate is supplied or authorized here. The adapter supplies:

- `open_boundary(directory)`: fresh or recovered handle with `machine(name)`,
  `call(name, fn, fault=None)`, and `close()`.
- `fault_error`: exception type with the existing fault `code` values.
- `open_store(directory)`: handle with `append(body)`, `records`,
  `committed_bytes`, `can_accept(extra, max_records, max_bytes)`,
  `has_operation(operation_id)`, and `close()`.

Fault injection belongs to the adapter/boundary. `partial` leaves an incomplete
attempt and recovery retains only the preceding accepted records;
`crash_before_durable` leaves that attempt absent after recovery. These are
controlled in-process injections, not a power-loss or physical-media proof.
The common cases never inspect filenames, frame offsets, CRCs, or private FSM
layout. Adapter handles retain the same public FSM semantics and normalized
readiness errors. Every open handle is closed, including after an injection.

`assert_budget_rejection(test, ready_call, command_call, domain)` reuses the
existing command-level budget scenario. Supply callbacks returning
`(status, ready_view)` and `(status, receipt)` respectively, with an initially
empty one-record budget. It checks rejection of the next new command while the
accepted operation still replays unchanged. The current HTTP test supplies
these callbacks; the scenario itself does not open a socket. Budget numbers
are test fixtures, not new product policy.

Coverage before extraction:

| Requirement | Existing coverage | Change |
|---|---|---|
| Torn writes and restart | Sufficient: reservation, settlement, resale, credit, admission fault tests | Reuse in the mixin |
| Crash before durable | Sufficient: settlement authorize fault test | Reuse in the mixin |
| Replay idempotence | Sufficient: five FSM restart scenarios | Reuse in the mixin |
| Concurrent hold | Sufficient: reservation competing holds | Reuse; join both workers before returning |
| Budget command rejection and replay | Sufficient: HTTP `test_journal_budget_does_not_apply_the_next_command` | Extract transport-neutral assertion function |
| Backend-neutral entry points | Not covered | Mixin and current-wrapper adapter |
| Record and byte budget predicate boundaries | Partially covered by HTTP record budget | Add store predicate case, including recovery and false labels |

Journal format, schema migration, checksum corruption, writer lock, and refusal
of core records in an FSM journal remain current-wrapper tests in
`readiness.test_faults`; they are not requirements for a different file format.

Run the unchanged CI entry point:

```text
python3 -m unittest integration_gate.test_http_gate readiness.test_faults
```

`FaultTests` binds the mixin to `LocalReadinessAdapter`, so protocol CI already
executes the common suite against the current wrapper. No workflow changes are
needed. The local wrapper stays single-process, single-writer, local-file and
opt-in through `--readiness-dir`. All production/truth and FSM durable labels
remain false. No runtime source or protocol contract changes are made.

Later local scenarios added beside that table, still through the same public
adapter surface: a reservation hold that crashes before durable is absent
until retried once; a crash-before-durable store append does not take a record
slot; a partial append does not either. Schema 2 migration, the AI delegation
wrap, named budget limits, and audit-line fields are local-wrapper coverage in
`readiness.test_faults` and the loopback gate tests. They do not add a product
limit or make schema 2 a readable file version.

Local acceptance is passing existing tests plus the reusable scenarios through
the existing CI command. The application still owns non-author exact-head
review, required Fable audits, draft publication, and successful exact-head KTX
and KIX hosted checks before delivery readiness. User-only merge and post-merge
verification remain required. Local Python checks do not supply those gates or
prove production durability, chain finality, or external exactly-once behavior.

## Negative controls (fault sensitivity)

`readiness/test_conformance_sensitivity.py` binds `BackendConformance` to
deliberately faulty `LocalReadinessAdapter` subclasses. Each adapter breaks
one property, is run through its mapped case programmatically, and must fail;
the same case on the unmodified adapter must pass. Before this addition,
positive coverage for these properties was sufficient in the cases below,
but sensitivity to deliberately wrong adapters was not covered. The new tests
fill that gap without duplicating or changing the conformance scenarios.
Semantic mutants must produce one assertion failure, with no runner errors;
the handle leak must produce precisely `JOURNAL_LOCKED`. A separate control
runs every existing common-suite case on the unmodified adapter.

| Injected fault | Adapter | Catching case | What the case detects |
|---|---|---|---|
| Reopen drops the last acknowledged record | `DropOnReopenAdapter` | `test_budget_rejection_preserves_records_and_replay_identity` | recovered `records` no longer equals the accepted set |
| Replayed distribution is dispatched again under a fresh identity and appends a second application | `ReplayTwiceAdapter` | `test_settlement_cash_survives_restart_and_a_torn_commit` | replay incorrectly reports `duplicate=False` |
| A torn/`partial` attempt consumes a record slot | `PartialSlotAdapter` | `test_partial_attempt_does_not_consume_a_record_slot` | live record count includes the torn attempt; actual torn-file recovery is unchanged |
| A `crash_before_durable` attempt survives recovery | `CrashDurableAdapter` | `test_crash_before_durable_leaves_the_attempt_out_of_the_record_budget` | live accounting excludes the attempt, but recovery finds `op-crashed` |
| Ignore record budget or byte budget (separate subtests) | `BudgetBlindAdapter` | `test_budget_rejection_preserves_records_and_replay_identity` | `can_accept` returns True at the ignored cap; the other cap still works |
| Two concurrent holds on one slot both report success | `DoubleHoldAdapter` | `test_concurrent_reservation_holds_occupy_the_slot_once` | losing hold returns a false success, so no worker reports `SLOT_OCCUPIED` |
| Handle left open after an injected fault | `LeakyHandleAdapter` | `test_settlement_cash_survives_restart_and_a_torn_commit` | next `open_boundary` raises `JOURNAL_LOCKED`; outer test cleanup then releases the handle |

Run it directly:

```text
python3 -m unittest readiness.test_conformance_sensitivity
```

The owner-approved single import of `ConformanceSensitivityTests` in
`readiness.test_faults` makes the unchanged CI command above run the negative
controls too. The concurrency case uses its existing barrier and joins;
the new tests use no sleeps or scheduling-dependent winner assertions.

Documented gaps — properties this document describes with no
`BackendConformance` case that would catch a faulty adapter:

- Journal file format, schema version/migration, checksum mismatch,
  exclusion of a second simultaneous writer, refusal of `core_commit` in an FSM journal, and the
  `protocolTruth`/`productionConformance` label refusal are checked only by
  the current-wrapper tests in `readiness.test_faults`. The common suite is
  backend-neutral and contains no case for them.
- The `ai_delegation` machine is wrapped by `FsmBoundary` but no
  `BackendConformance` case exercises it; a delegation-specific fault is not
  covered.
- `boundary.last_observation` fields are asserted only in
  `readiness.test_faults`, not in the common suite.
- Named budget-limit diagnostics and overload admission are wrapper/gate
  coverage only; the common suite tests the store's boolean budget predicate.
- `assert_budget_rejection` runs through the loopback HTTP gate, not inside
  `BackendConformance`; the store-level predicate is covered, but command-level
  rejection over a non-HTTP adapter has no common-suite case.

The faulty adapters are test doubles, not candidate backends. Their failures
show the suite notices the injected faults; this is not a power-loss proof,
not a PostgreSQL or other candidate-backend test, and not a backend adoption.
