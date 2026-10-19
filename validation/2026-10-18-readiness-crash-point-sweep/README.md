# readiness-crash-point-sweep

Node: `plan-readiness-crash-point-sweep`. Adds `CrashPointSweepTests` inside `readiness/test_faults.py`, a short section in `readiness/CONFORMANCE.md`, this record and one `docs/README.md` pointer. Issue: none. Depends on: `readiness-extensions`, `k-readiness-conformance-suite`. Audit floor A2. Not an ASTRA program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head or final task head SHA and no exact-head CI run for this work; those belong in the pull request closure report (AGENTS.md §11).

Observed `origin/main` = branch HEAD = `306dfa1261eb02881d1914b34d6510fc698a9979` (merge of #214), after `git fetch origin main`.

**This record is a builder-authored reading, not an independent review. No grade is raised and nothing is claimed for production.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `git rev-parse HEAD:reference/v0.3-rc1` = `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` before and after.

## Changed paths

| Path | Change |
|---|---|
| `readiness/test_faults.py` | New class `CrashPointSweepTests` (7 tests); `committed_face` added to an existing import. |
| `readiness/CONFORMANCE.md` | New section "Command-level crash-point sweep". |
| `validation/2026-10-18-readiness-crash-point-sweep/README.md` | This record. |
| `docs/README.md` | One index bullet. |

No `readiness/*.py` other than `test_faults.py`, no journal format, contract, workflow or `.github` change.

## AGENTS.md §7: existing coverage

| Requirement | Existing | Status |
|---|---|---|
| Fault at one command per machine | `test_settlement_cash_survives_restart_and_a_torn_commit`, `test_reservation_hold_survives_restart_and_a_torn_write`, `test_resale_transfer_does_not_bump_version_twice_after_restart`, `test_credit_exposure_is_not_drawn_twice_across_restart`, `test_admission_consume_survives_restart_once` | partial: `partial` only, one index each |
| `crash_before_durable` | `test_settlement_crash_before_durable_authorize_applies_once`, `test_reservation_crash_before_durable_hold_is_absent_until_retried` | partial: two machines |
| Record slot not consumed | `test_partial_attempt_does_not_consume_a_record_slot`, `test_crash_before_durable_leaves_the_attempt_out_of_the_record_budget` | partial: `core_commit` records only |
| Every index, full-result resend, finish-to-final digest, fail-stop | none | not covered |

The sweep subsumes seven cells (settlement `commit`/partial, reservation `hold`/partial, resale `accept_resale`/partial, credit `draw`/partial, admission `consume`/partial, settlement `authorize`/crash, reservation `hold`/crash). All existing tests are kept; they also assert `SLOT_OCCUPIED`, `ILLEGAL_TRANSITION`, `DUPLICATE_DRAW`, `ALREADY_CONSUMED`, concurrency and budget behaviour that the sweep does not.

## What the sweep does

The sequence per machine is built by a test-local recorder that collects the steps the existing `BackendConformance` helpers issue, then appends the scenario's final command, so each sequence equals the existing scenario by construction. Per case (`subTest` machine/fault/command/op): run commands 0..i-1, fault command i via `boundary.call(..., fault=...)`, check the fault code, check the same boundary then raises `READINESS_CLOSED` (contract-defined, `READINESS_RUNTIME.md` line 26; an addition beyond (a)-(d)), close, read the store (`len(records) == i`, entries equal the reference journal prefix, `protocolTruth`/`productionConformance` false), reopen and check (a) digest and journal equal the prefix state, (b) first resend returns the uninterrupted result with `duplicate` False and appends one entry, second resend is `duplicate` True with `applied` None and no change, (c) remaining commands return the reference results and the final digest/journal equal the reference, (d) record count equals the sequence length, a third reopen gives the same digest, and every `durable`, `funds_executed`, `economic_finality_claimed`, `chain_owner_current`, `admission_routing_production`, `bank_debit_observed` found in results and the final view is `False`. Only the adapter surface is used; no filenames, offsets or CRCs.

## Cases executed

Collected by the exact CI command (`python3 -m unittest -v integration_gate.test_http_gate readiness.test_faults`, 71 tests, OK):

- `CrashPointSweepTests.test_crash_point_sweep_settlement`, `_reservation`, `_resale`, `_credit`, `_admission`
- `CrashPointSweepTests.test_reference_runs_are_deterministic_and_one_entry_per_command`
- `CrashPointSweepTests.test_sweep_cells_subsume_the_existing_fault_cases`

Counts from the `executed` counter (each test asserts the count equals the sequence length): settlement 5+5, reservation 3+3, resale 5+5, credit 3+3, admission 4+4 for `partial` + `crash_before_durable`; 40 cases over 20 commands.

## Broken-replay control (acceptance 3, shown once, reverted)

Temporary edit of the single resend choke point `_resend`: `step(boundary.machine(name))` before `boundary.call`, i.e. the resent command is applied out of band, so the boundary returns `duplicate` and appends nothing. Result: 40 of 40 sweep sub-cases failed (45 failures in the class: 40 sub-cases plus the 5 per-machine count assertions). The edit was reverted by an inverse edit; `git hash-object readiness/test_faults.py` matched the pre-mutation hash `56d4a3d193cfe5575285f4b59a8e1faa7ce9a079` and the class is green again.

## Runtime (Python 3.13.5, ext4 on `/dev/vdb`; CI uses 3.12)

- `python3 -m unittest readiness.test_faults`, before (27 tests): 0.722 s, 0.679 s, 0.870 s, median 0.722 s.
- After (34 tests, +7): 0.833 s, 0.747 s, 0.753 s, median 0.753 s.
- The sweep class alone: about 0.2 s (0.197 s, 0.217 s over separate runs).
- Added module runtime: about 0.03 s by the medians, about 0.2 s by the class timing; the runs are noisy. No threshold set; coverage was not trimmed.

## Commands run and results

| Command | Result |
|---|---|
| `git fetch origin main; git rev-parse origin/main HEAD` | both `306dfa1…` |
| `git hash-object` on the two locked files (before and after) | match the required blobs |
| `python3 -m unittest readiness.test_faults` x3 before edit | 27 tests OK |
| `python3 -m unittest -v readiness.test_faults.CrashPointSweepTests` | 7 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v integration_gate.test_http_gate readiness.test_faults` | 71 tests OK (re-run on the final file) |
| `PYTHONHASHSEED=0` / `random` `python3 -m unittest readiness.test_faults` | OK / OK |
| `unittest discover` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | 48 / 75 / 48 / 70 / 61 tests OK |
| `check_docs_index.py`, `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_contract_error_codes.py`, each plain and `--self-test` | exit 0 for all 18 runs |
| cargo, clippy, fmt | NOT_RUN: nothing under `runtime/` changed; they run hosted |

## Class A / B / C

- Class A (contract-defined, matched): torn tail dropped, faults consume no record slot, same key returns the stored result once, fail-stop after a failed append (`READINESS_RUNTIME.md` lines 13, 21, 26, 40).
- Class B (contract does not define; observed characterizations): the first resend equals the uninterrupted result exactly (the contract says "once", not byte equality); digest equality across independent in-process instances; every one of the 20 commands emits exactly one journal entry, so `FsmBoundary.call`'s "fault on the first entry only" rule is untested for multi-entry commands.
- Class C: none found. Every case passed on unmodified code.

## Non-claims

No power-loss, OS-crash or `fsync` result. No lost-acknowledgement-after-durable-append case (`fault=` cannot inject it). Single process, single writer, local files. Not a `BackendConformance` control and no backend adoption. No production durability, no grade change. Unswept: `ai_delegation`, `core_commit` records, rejected commands, concurrency, the HTTP gate. The idempotency error cache is memory-only and not exercised. Reliance on private `BackendConformance` helpers: a rename fails loudly in the same CI command.

## Follow-ups owed to a later sync

`docs/status/CURRENT_CAPABILITY_REGISTER.md`, `DEVELOPMENT_PLAN.md` §5 and `.aiops` were not edited.
