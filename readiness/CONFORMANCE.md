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

Local acceptance is passing existing tests plus the reusable scenarios through
the existing CI command. The application still owns non-author exact-head
review, required Fable audits, draft publication, and successful exact-head KTX
and KIX hosted checks before delivery readiness. User-only merge and post-merge
verification remain required. Local Python checks do not supply those gates or
prove production durability, chain finality, or external exactly-once behavior.
