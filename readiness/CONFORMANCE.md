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
credit 3, admission 4 commands) and, for every command index and both fault
kinds (`partial`, `crash_before_durable`), injects the fault through
`FsmBoundary.call(..., fault=...)`, closes, reopens and checks: the recovered
digest and journal equal the prefix only; the resend applies once and returns
the uninterrupted result; finishing the sequence reaches the uninterrupted
final digest; the record count equals the accepted commands and the false
truth labels stay false. After the fault the same boundary also refuses
further calls with `READINESS_CLOSED`. That is 40 cases over 20 commands.

It uses the public adapter surface only. The existing fault cases are kept; the
sweep reaches the same cells (the module test
`test_sweep_cells_subsume_the_existing_fault_cases` pins seven of them).

Class B characterizations (the contract does not define them): byte-equal
result on the first resend; digest equality across independent in-process
instances; every command emits exactly one journal entry, so the "fault on the
first entry only" rule is not exercised for multi-entry commands.

Not claimed: power loss, OS crash, `fsync`, a lost acknowledgement after a
durable append, concurrency, rejected commands, the `ai_delegation` machine,
any backend adoption, any production durability. Single process, single
writer, local files. Record:
`validation/2026-10-18-readiness-crash-point-sweep/README.md`.

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
bank debit or chain finality. The reward machine is not part of
`BackendConformance` or the crash-point sweep, and this section is not an
independent verification of TK-4, TK-7, TK-8, TK-12 or V6. Record:
`validation/2026-10-20-token-reward-readiness-wrap/README.md`.
