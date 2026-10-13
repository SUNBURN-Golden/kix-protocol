# k-stage2-v5-impl — in-memory v5 lifecycle slice

Node: `k-stage2-v5-impl`. Not an ASTRA program-mode session. No issue. No commit,
push, pull request, or comment in this session. Date: 2026-10-13.
Branch: `agent/kix-k-stage2-v5-impl`.

Authority: `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md` §5–§6 (option
O1, merged by PR #138), narrowed by the owner-delegate decision of 2026-10-13
("residual stops (final)"), which was the task input. That decision text is not a
file in this repository; this record quotes the values it fixed.

## Base (AGENTS §1)

- Task branch HEAD, after `git fetch origin main`: `a483ab1777ad0c3e15ff71798822cbf6b3666f83`
  (merge of PR #138). It is the merge-base with `origin/main`.
- Observed `origin/main`: `ab42cfef43a40c6b86fd3f22b69f00e134cc472e`, 79 commits ahead of
  the task base. **Delta reported, not applied:** this session did not rebase or merge main.
  The delta touches `docs/`, `scripts/`, `.github/workflows/protocol.yml`, `sdk/`,
  `reference/`, `integration_gate/`, `validation/` and the root `README.md`. It does not touch `runtime/`
  (`git diff HEAD origin/main -- runtime` is empty), so `Cargo.lock` here equals what the
  merge would carry plus this node's one entry. The new main-only steps are covered below
  by a throwaway merged-tree simulation.
- There is no implementation commit SHA and no final task head. Local results are not
  exact-head CI (AGENTS §10).
- `rustc 1.98.1 (48a229cea 2026-09-01)`, the workflow pin. `python3` here is 3.13.5
  (`protocol.yml` pins 3.12). `node` is v20.19.2 (`toolchains.json` asks for major 24).

Locked blobs before and after the edits, identical on `origin/main`:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat HEAD --` over `runtime/crates/kix-kernel runtime/crates/kix-types
reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts` is empty, and so is
`git diff --stat origin/main --` over `runtime/crates/kix-kernel runtime/crates/kix-types
reference/v0.3-rc1`.

## Changed paths

| Path | Change |
|---|---|
| `runtime/Cargo.toml` | Workspace member `crates/kix-kernel-v5` (one line). |
| `runtime/Cargo.lock` | One new package entry (8 lines). Lists `kix-kernel` and `kix-types`; the lock format does not separate the dev-dependency. `cargo tree --edges normal` prints only `kix-types`. |
| `runtime/crates/kix-kernel-v5/**` | New crate: `Cargo.toml`, byte copy of v4's `clippy.toml`, `src/lib.rs`, `README.md`, `tests/` (8 files plus `common/mod.rs`). |
| `validation/2026-10-13-k-stage2-v5-impl/README.md` | This record. |

No `DECISION_REQUIRED.md` is written: the owner decision answered the earlier stops by
deciding that the three state-changing transitions stay stopped (see "Stopped parts").
The earlier stopped-build draft named `2026-10-09-k-stage2-v5-impl` for this directory;
it was renamed to the session date.

## What landed

`runtime/crates/kix-kernel-v5` (`SEMANTICS_VERSION = 5`) forks the locked v4 transitions
and adds, all in memory and with no I/O:

- **Operational termination** (`Kernel::terminate`): one record per bound operation,
  replayed by `decision_id`, human actor only (automatic scope 0), five caller-supplied
  C1–C5 flags with hashes, stale-evaluation rejection. Its only effect is that
  `mark_payment_unknown` is refused.
- **Private conflict index** with v4's membership and rejections.
- **Hold references** (`place_hold`, `clear_hold`, `hold`): at most one
  `HoldRef { id, kind: Legal | Dispute | Erasure, placed_at_ms, placed_by }` per order.
  No expiry; only an explicit `clear_hold(id, by)` removes it.
- **Read-only reclamation report** (`reclaim_report`, `reclaim_reports`) with the owner's
  blocker order `ActiveOp, ReservedSlot, ReviewRequired, UnboundFence, ReturnObligation,
  ReplayWindow, Hold, I09, I10, I13`, batch order `(terminated_at, order_id)` ascending,
  and `ReclaimPolicy` defaults: retry-support 15 days, memory residency 72 hours, cap
  10,000 terminated records, retention floor 5 years (counted as 1,827 days).
  `ReturnRequired` and an open conflict are treated as held without a hold reference.

## Stopped parts (decided, not implemented)

The owner decision keeps these stopped and records the pre-authorized shapes as spec only.
Each names the open row in `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md` §1, all still
"미완결" there. This session did not edit that file or any contract.

| Transition | Open rows | State |
|---|---|---|
| One-time reserved-slot release | I12, I13 | No entry point. I12 handoff predicate (termination record, `late_fact_custody = Accepted{>= 64 KiB, 30 days}`, `transfer_blocked`, operation and record resident) is spec only until Astra reviews and JunTae approves the trust policy. I13 budget placeholder 0 bytes means blocked. |
| State-changing record/evidence reclamation | I09, I10, I13 | No entry point. `reclaim_report` is the only surface. Evidence hashes: nothing deletes them. |
| Review release | I11 (remaining automatic authority), conclusion contents | No entry point. Redelivery never clears `review_required`. The five-field conclusion is spec only (crate README). Automatic limit 0. |
| Conflict-index upkeep under the three above | — | Gate stays closed. The index preserves v4 membership only. |

## Existing coverage (AGENTS §7)

The v4 rows of the design decision §8 still stand and v4 tests were not edited. New tests
are only in `kix-kernel-v5`.

| Requirement | Class before | New test |
|---|---|---|
| Termination once, replay, payload conflict, second decision, automatic rejection, each false C1–C5, stale snapshot, capture / `ReturnRequired` / review rejection, send blocked, late capture keeps the first record, failed call changes nothing | not covered | `tests/termination.rs` (13) |
| Report: fixed blocker order, unconditional I09/I10/I13 tail, windows boundary-exact, saturating arithmetic, implicit hold, read-only, errors | not covered | `tests/reclaim_report.rs` (13) |
| Hold: kinds, no expiry, replay, conflicting reuse, one per order, explicit clear, rejections change nothing | not covered | `tests/holds.rs` (9) |
| Batch order and tie-break, terminated-only scope, cap flag, 10,000-record synchronous report | not covered | `tests/reclaim_batch.rs` (6) |
| Slot, inventory, review, evidence untouched by termination/hold/report/clear; reserved→stored is not budget reclaim; redelivery never clears review; `ReturnRequired` + mismatch keeps both | partial (v4 observation_slots, edge cases) | `tests/stopped_transitions.rs` (5) |
| Conflict index equals v4 membership, capacity, unbound identity | not covered | `tests/conflict_index.rs` (4), `tests/v4_differential.rs` |
| Version 5 rejects version 4 and the reverse; seeded v4/v5 equality on shared commands | partial (v4 rejects v3) | `tests/v4_differential.rs` (3) |
| Normal dependency is `kix-types` only; clippy boundary equals v4's | not covered | `tests/boundary.rs` (2) |

## B-class characterizations (AGENTS §8)

None is written into `docs/contracts/`.

- Termination is accepted only for `PaymentUnknown`, a reserved slot, no captured amount,
  and `review_required == false`. The only command it blocks is `mark_payment_unknown`.
- `OperationSnapshot::observations` and `retained_conflicts` are kernel-wide counts: a new
  retained observation or conflict on another order stales an earlier snapshot. A false
  condition is reported before staleness.
- `ActiveOp` is cleared only by an operational termination. An order that ended another
  way (for example `PaymentConfirmed`) is still listed active, since the kernel has no
  other terminal marker.
- `UnboundFence` is read as retained conflict evidence for the candidate's own operation
  identity (STATE_LIFECYCLE §6 "retained unbound fence").
- "Open conflict" for the implicit hold is a quarantined operation or retained conflict
  evidence.
- A cleared hold leaves no tombstone: a delayed duplicate placement after clearing
  re-places the hold (fails closed). `clear_hold` returns the clearing record; the ordered
  driver must log it. One hold per order follows the owner's `Option<HoldRef>`.
- "5 years" is counted as 1,827 days, the longest span of five calendar years, so the
  floor never elapses early. "Records" for the residency cap means terminated-order
  records. LRU is not implemented: no eviction exists.
- `memory_residency_ms` and `retention_floor_ms` run from the termination, the only
  terminal-state timestamp the kernel stores; the retry-support window runs from the
  reserve command's first result, now stored as `applied_at_ms` in the command record.
- The report takes a caller-supplied monotonic `now_ms` and rejects one below the kernel's
  ordered time with `ClockRegression`.
- The v4/v5 differential was written with the v4 source in view. Agreement is not an
  independence proof.
- `HoldRef.placed_at` is named `placed_at_ms` here.

**Flagged for the Astra architecture audit and the user merge.**

1. The 15-day retry-support default equals the provider's public idempotency-key period.
   `docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md` §3 and §5 (R3) and
   `FIRST_BATCH_OPEN_INPUTS.md` I07 say that period is not a KIX threshold, and its §7 says
   v5 may use only caller-supplied slots with no defaults. The owner decision of 2026-10-13
   is explicit that these are kernel defaults, so they are implemented as such, documented
   in the code as owner-delegate values unrelated to the provider period, and
   caller-overridable. The report cannot act on them: it never says eligible.
2. I09 stays `DECISION_REQUIRED · Astra` and I10 `UNDETERMINED · legal/privacy` in the
   contracts. The defaults here do not close them, and the report keeps I09, I10, I13 as
   unconditional blockers.
3. The delegation table's contract-change YES cell for this node needs Astra's
   architecture audit and the user merge (audit floor A3).

No explicit contract violation was found. The locked kernel's lack of these transitions is
the state STATE_LIFECYCLE §5.8 and §6 already record.

## Commands and results

All run from the node worktree in the foreground, after `git fetch origin main`.

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git rev-list --count HEAD..origin/main`; `git merge-base HEAD origin/main` | HEAD `a483ab1777ad0c3e15ff71798822cbf6b3666f83`; `origin/main` `ab42cfef43a40c6b86fd3f22b69f00e134cc472e`; 79 ahead; merge-base = HEAD |
| `rustc -V` | `rustc 1.98.1 (48a229cea 2026-09-01)` |
| `git hash-object` on the two locked paths (start, after edits) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --stat HEAD --` locked/forbidden paths; `git diff --stat origin/main --` v4, types, reference | both empty |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests, OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 (final run, after the last edit) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --locked` | exit 0. 55 tests: boundary 2, conflict_index 4, holds 9, reclaim_batch 6, reclaim_report 13, stopped_transitions 5, termination 13, v4_differential 3 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0. 78 tests: contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. kix-bcs1 7, kix-feature-ir 31, kix-feature-semantics 6, kix-kernel 78, kix-kernel-v5 55, kix-types 6. Doc-tests 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 after one fix: the first run failed on `clippy::redundant_locals` in `tests/reclaim_report.rs`; the line was removed and the whole command re-run |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --edges normal --locked` | `kix-kernel-v5` → `kix-types` only |
| `cargo test --release ... -p kix-kernel-v5 --test reclaim_batch ten_thousand -- --nocapture` (3 runs) | 10,000 records in 10.2 ms, 8.9 ms, 7.3 ms (SLO 50 ms; asserted in release builds only). Unoptimized build, one run: 49.5 ms, which is why the debug build does not assert it. Measurement on this machine, not a CI figure |
| Merged-tree simulation: `git archive origin/main` into a temp directory, this node's four paths copied over, then run there (temp directory removed afterwards) | `check_status_register.py` (+`--self-test`), `check_rs_profile_traceability.py` (+`--self-test`), `check_read_model_source_map.py` (+`--self-test`), `check_docs_index.py` (+`--self-test`), `verify_runtime_architecture.py`, `test_runtime_architecture.py`, `check_openapi_contract.py` (+`--self-test`; commands=84), `check_integration_gate_openapi.py` (+`--self-test`; commands=84): all exit 0 |
| Same tree: `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. 58 tests, OK |
| Same tree: reference `unittest discover` for settlement_f01_f03, booking_resale_admission, credit_advance_f04, ai_delegation, token_reward | exit 0. 22, 47, 26, 22, 61 tests, each OK |
| Same tree: `python3 scripts/check_sdk_client.py` | exit 1. `node 20.19.2 does not match toolchains.json nodeMajor 24`. `--self-test` did not run. Environment limit; the script does not read this crate |

Not run: `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`
(`sdk/node_modules` absent; Node major 20, not 24), `bash scripts/bootstrap.sh` and the
`.venv` steps (`verify_runtime.py`, commerce, canonical, paid storage, localnet), Move
tests, ZK setup, and `sui` (not on `PATH`). None of those read this crate. The
`ktx-kernel.yml` workflow (`-p kix-kernel` only) was not run as a workflow.

## CI (AGENTS §10, §14)

- Exact-head KTX kernel verification run: none. No commit exists.
- Exact-head KIX protocol verification run: none. No commit exists.
- Merge commit and post-merge main CI: not applicable.

The supervisor commits and opens the PR. This record claims `merge-ready` for nothing;
the node state is implementation complete locally, awaiting exact-head CI, non-author
review, Astra's architecture audit and the user merge.

## Non-claims

This record does not claim durability, distributed fencing, bank exactly-once behavior,
chain finality, legal compliance, production readiness, or that I09–I13 are closed. The
termination record is not a durable approval. The retention figures are kernel defaults
set by the owner delegate, not legal periods and not ratified Astra policy. Automatic
approval scope is 0. No provider fact was evaluated and no principal or approver was
authenticated. No wire, OpenAPI, or catalogue name was added; `v5.termination.*` and
`v5.reclaim.report` are reserved for a later node only. Local success is not exact-head CI
and is not merge authorization.
