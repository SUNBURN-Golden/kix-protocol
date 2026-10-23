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

## Journal byte sweep: observed limits

`readiness.test_faults.JournalByteSweepTests` sweeps the current wrapper's
`journal.v1` byte by byte. It is a current-wrapper test of that file format. It
is not part of `BackendConformance`, and it is not a requirement for a
different file format. The record is
`validation/2026-10-17-readiness-journal-byte-sweep/README.md` (#205).

A 4-frame, 839-byte journal is written through `ReadinessStore.append`. Each
mutated copy is opened with `ReadinessStore.open`. The property checked is that
`open()` raises `StoreError`, or the recovered records are an exact prefix of
the originals. No altered, reordered or fabricated record was seen. Five
families:

- T: truncation at every offset 16..839 (824 cases).
- H: header truncation to 0..15 bytes and header byte flips (32 cases).
- F: payload and CRC byte flips (807 cases).
- L: length-prefix byte flips (16 cases).
- R: four CRC-consistent re-framed payload edits (4 cases).

Observed characterizations (AGENTS §8 class B, builder reading; the contract
does not define them):

- A damaged length prefix on a non-final frame (above `MAX_RECORD_BYTES`, or
  pointing past EOF) is parsed as a torn tail. `open()` truncates the file
  there and silently drops the later complete, acknowledged frames; restoring
  the byte does not bring them back. In the L family, 9 of 16 cases drop later
  frames, 3 final-frame cases look exactly like a torn tail, and the 4 cases at
  length byte 3 give `CHECKSUM_MISMATCH`.
- A 0-byte `journal.v1` is reinitialised: the header is written and the store
  is empty. 1..15 bytes give `JOURNAL_HEADER`.
- A clean truncation at a frame boundary is undetectable: `open()` returns the
  shorter prefix with no error.

The Astra ruling on `docs/contracts/READINESS_RUNTIME.md` line 21 is pending.
That line defines only a trailing incomplete frame and a complete frame with a
bad checksum. The suite is therefore not evidence of fail-closed behaviour for
mid-file length damage.

This section changes no `readiness/*.py`, no journal format and no contract,
and decides no classification. It makes no power-loss, OS-crash, `fsync` or
production durability claim.

## Command-level crash-point sweep

`readiness/test_faults.py` `CrashPointSweepTests` takes the command sequence of
each `BackendConformance` scenario (settlement 5, reservation 3, resale 5,
credit 3, admission 4, ai_delegation 3, reward 6 commands) and, for every
command index and both fault kinds (`partial`, `crash_before_durable`), injects
the fault through `FsmBoundary.call(..., fault=...)`, closes, reopens and
checks: the recovered digest and journal equal the prefix only; the resend
applies once and returns the uninterrupted result; finishing the sequence
reaches the uninterrupted final digest; the record count equals the accepted
commands and the false truth labels stay false. After the fault the same
boundary also refuses further calls with `READINESS_CLOSED`. That is 58 cases
over 29 commands.

It uses the public adapter surface only. The existing fault cases are kept; the
sweep reaches the same cells (the module test
`test_sweep_cells_subsume_the_existing_fault_cases` pins eleven of them).

Class B characterizations (the contract does not define them): byte-equal
result on the first resend; digest equality across independent in-process
instances; every command emits exactly one journal entry, so the "fault on the
first entry only" rule is not exercised for multi-entry commands. The
`ai_delegation` `open_registry` and the `reward` `open` carry no idempotency
key and return no `duplicate` flag: their resends raise each wrap's own
`WrapError('ALREADY_OPEN')` instead of a duplicate result (the two wraps
define distinct `WrapError` classes; the sweep's `REPLAY_ERRORS` cells pin
both; the journal and digest assertions afterwards are unchanged). The reward
wrap journals a command only when the state digest changed; all six commands
in the sweep sequence change it. The AI delegation mock's duplicate results
carry no `applied` key.

Not claimed: power loss, OS crash, `fsync`, a lost acknowledgement after a
durable append, concurrency, rejected commands, any backend adoption, any
production durability. Single process, single
writer, local files. Records:
`validation/2026-10-18-readiness-crash-point-sweep/README.md`,
`validation/2026-10-20-ai-delegation-wrap-conformance/README.md`,
`validation/2026-10-21-reward-wrap-conformance/README.md`.

`BackendConformance` also covers the `ai_delegation` wrap with three
scenarios through the same adapter surface: the registry opens once across a
restart and a journaled `issue_grant` resend returns `duplicate` with the
identical grant view while a resent `open_registry` raises `ALREADY_OPEN`; a
torn `revoke_grant` recovers as still `ACTIVE`, applies once on resend and
replays `duplicate`, with `attempt_execution` still refused as
`DELEGATED_EXECUTION_DISABLED`; and a `crash_before_durable` `issue_grant`
leaves no grant (`UNKNOWN_GRANT` on view) until the resend applies it once.
`durable` and `execution_enabled` stay false throughout. The two dedicated
`ExtensionTests` cases are kept: they additionally pin `last_observation`
fields the mixin does not.

| AI delegation fault / behavior | BackendConformance case | Sweep cells |
|---|---|---|
| Registry opens once; issue replay across restart | `test_ai_delegation_registry_opens_once_and_issue_replays_across_restart` | `open_registry` with both faults; repeat open raises `ALREADY_OPEN` without changing journal/digest |
| Torn revoke recovers ACTIVE; resend revokes once | `test_ai_delegation_torn_revoke_recovers_and_replays_once` | `revoke_grant` with `partial` and `crash_before_durable` |
| Crash before issue leaves no grant; resend issues once | `test_ai_delegation_crash_before_durable_issue_leaves_no_grant` | `issue_grant` with `partial` and `crash_before_durable` |

`BackendConformance` also covers the `reward` wrap with three scenarios
through the same adapter surface: the wrap opens once across a restart and a
journaled `hold` resend returns `duplicate` with the identical reward view
while a resent `open` raises `ALREADY_OPEN`; a torn `mark_eligible` recovers
as still `HELD`, applies once on resend and replays `duplicate`, with
`reject_external` still refused as `EXTERNAL_EXECUTION_UNSUPPORTED`; and a
`crash_before_durable` `observe` leaves no reward (`UNKNOWN_REWARD` on view)
until the resend applies it once. `durable` stays false throughout. The three
dedicated `RewardWrapTests` cases are kept: they additionally pin the
`restore(export_journal())` canonical-state round-trip and the
`last_observation` fields the mixin does not.

| Reward fault / behavior | BackendConformance case | Sweep cells |
|---|---|---|
| Wrap opens once; hold replay across restart | `test_reward_open_observe_and_hold_replay_across_restart` | `open` with both faults; repeat open raises `ALREADY_OPEN` without changing journal/digest |
| Torn mark_eligible recovers HELD; resend applies once | `test_reward_torn_mark_eligible_recovers_and_replays_once` | `mark_eligible` with `partial` and `crash_before_durable` |
| Crash before observe leaves no reward; resend observes once | `test_reward_crash_before_durable_observe_leaves_no_reward` | `observe` with `partial` and `crash_before_durable` |

## Token reward wrap

`readiness/reward_wrap.py` wraps `reference/token_reward/reward_fsm.py`'s
`RewardMachine` as the `reward` machine (`store.py` `FSM_MACHINES`,
`machines.py`). It follows the AI delegation wrap: an explicit `open` records
the caller-supplied `opening_balances` so restore is deterministic, then each
public command whose state digest changed is journaled and replayed through
the same public methods. `RewardWrapTests` in `readiness/test_faults.py`
covers a torn write replayed once, a crash-before-durable observe that leaves
no reward, and a `restore(export_journal())` round-trip of
`canonical_state` and `state_digest`.

Same bounds: single process, single writer, one local file, off unless
`--readiness-dir`. `durable`, `protocolTruth` and the production labels stay
false and `reject_external` still refuses. `MOCK_TOKEN_REWARD_ONLY`
provenance passes through unchanged: a matched replay is not a payout, a
bank debit or chain finality. The reward machine now shares
`BackendConformance` and the crash-point sweep through the same adapter
surface (see the sweep section above), and this section is not an independent
verification of TK-4, TK-7, TK-8, TK-12 or V6. Records:
`validation/2026-10-20-token-reward-readiness-wrap/README.md`,
`validation/2026-10-21-reward-wrap-conformance/README.md`.

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
- The `ai_delegation` and `reward` wrap cases of `BackendConformance` (six
  cases, sections above) are run by the unmodified-adapter control only. No
  faulty adapter here is mapped to them, so their sensitivity to a wrong
  backend is not shown.
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
