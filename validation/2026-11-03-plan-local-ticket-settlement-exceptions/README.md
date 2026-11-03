# Shared ticket settlement failure, cancellation and reconciliation

Node `plan-local-ticket-settlement-exceptions`. Task input is the supervisor's
supplied node specification and read-only design; no issue or `docs/tasks/`
document exists. This is not ASTRA program mode. Branch:
`agent/kix-plan-local-ticket-settlement-exceptions`.

Initial HEAD and cached origin/main both:
`468e479743c53834dfd25cb01def163180dcee81`. No observed local base delta.
The supervisor prohibits network, overriding AGENTS.md §1 fetch; remote
freshness is unverified. No git/GitHub publication is authorized.

## Pre-change coverage inventory

Recorded before adding tests. Paths are relative to `reference/`.

| Requirement | Existing evidence | Classification / gap |
|---|---|---|
| Pre-capture fail/cancel, late refusal, terminal immutability | `settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.test_terminal_fail_and_cancel_are_immutable`, `test_illegal_transitions_do_not_move_the_phase`; fail/cancel rejection matrices in `test_settlement_rejection_atomicity.py` | Sufficient FSM coverage; shared surface not covered |
| First-result replay and conflicts | `SettlementFsmTests.test_same_key_replays_and_a_different_body_is_rejected`; shared `test_ticket_settlement_controls.py` forwarding/replay coverage | Partial: shared exception selectors absent; retained key probes needed |
| Reconciliation after statement/distribution/refund | `SettlementFsmTests.test_reconcile_matches_restore_and_does_not_enter_the_economic_journal`; `test_settlement_multi_payee_refund.py::RefundReplayTests`; shared statement/refund journeys | Sufficient FSM arithmetic; shared reconciliation not covered |
| Required signatures, exact JSONL fields, exits | `booking_resale_admission/test_ticket_settlement_controls.py`, `test_ticket_refund_controls.py`, `test_ticket_operations_cli.py` | Partial: extend selector matrices and executable journeys |
| Unchanged ticket machines and no source fetch/retry/compensation | Shared graph/source tests in `test_ticket_operations_session.py` and `test_ticket_statement_distribution.py` | Partial: new selectors need composed state and call checks |

No underlying arithmetic or source tests need duplication. State/digest/journal
snapshots omit retained key bookkeeping; explicit replay/conflict probes are required.

## Implementation and acceptance evidence

The session forwards `fail`, `cancel` and `reconcile` once to its existing shared
settlement machine, requiring caller-provided identity, key and applicable
reason. Three exact-field CLI entries reuse the existing parser, errors and
receipt envelopes. No validation/default/cache is added to the wrapper.
FSM semantics, fixture loader/schema, contracts, catalogue, SDK, runtime flags
and CI are unchanged. This is builder-authored, source-informed composition
evidence, not independent verification or an A2 acceptance.

New tests in `reference/booking_resale_admission/test_ticket_settlement_exceptions.py`:

| Test | Gap addressed / observed result |
|---|---|
| `test_pre_capture_and_terminal_parity` | Both fail/cancel from INITIATED and AUTHORIZED; refusal after CAPTURED/COMMITTED. Every exposed mutator refuses terminal changes, including recorded operations supplied with matching recordings. View/reconcile remain available. Every complete receipt/error and graph snapshot matches raw FSM controls. |
| `test_replay_and_retained_refusal_keys` | Earlier initiate/authorize and terminal receipts replay original snapshots. Changed reason, identity, operation and reconcile key reuse conflict. A phase refusal remains bound after advancement; terminal refusal replays and changed body conflicts. Journal restoration forgets reconciliation and retained refusal keys while accepted operations retain replay. |
| `test_reconcile_history_and_restore` | Reconcile between recorded statements, distributions, refund binding and synthetic acceptance matches complete direct-FSM receipts; current state/digest/journal do not change during reconciliation. Old reconciliation keys retain their AUTHORIZED snapshot; fresh receipts reflect COMMITTED state with distribution/refund progress. In-memory restore permits a fresh receipt with the historical key. Full synthetic cancellation acceptance also preserves false external-return flags. Existing claim oracle checks conservation. |
| `test_settlement_exception_isolation` | Reservation `reserve-2` is explicitly bound to pre-capture `claim-2`. Every new selector preserves booking/resale/admission canonical states, digests and journals. Public ticket mutators, source fetches and settlement distribution/refund/external-attempt methods are instrumented to fail on invocation; all remain uncalled. No reservation cancellation, inventory release, ownership change or inferred compensation occurs. |
| `test_file_stdin_and_strict_errors` | Both fixture transcripts run through session, dispatcher and executable file/stdin paths, comparing every output to direct controls. Required/missing/extra/duplicate fields, wrong containers, nonfinite JSON and unknown selector stop with exit 2. Invalid identity/key/reason and unknown settlement preserve FSM errors and continue with exit 1; successful reconciliation journey exits 0. |

The extended generic test
`test_ticket_settlement_controls.py::TicketSettlementControlsTests.test_fsm_methods_forward_once_with_exact_objects_receipts_and_errors`
checks all 13 settlement selectors, including exact required keyword-only
signatures, opaque original argument objects, original receipt/error identity
and exactly one machine call for these three direct methods. Generic structural
error matrices now include the new selectors. Obsolete unsupported-selector
entries are removed/replaced without exposing raw restore or observation methods.

Fixture version 1 retains the existing issued anchor, both adoptions and explicit
clocks. Setup reuses predecessor recordings and prepares additional synthetic
pre-capture cases. `claim-2` is AUTHORIZED and bound to `reserve-2`; capture is
an explicit reconciliation transcript request. The exception transcript has
30 explicit lines (exit 1); the reconciliation transcript has 26 (exit 0).
No economic policy value is supplied by the session or inferred from the examples.

## Commands actually run and results

Commands ran from the repository root in the foreground. No network, package
installation, git commit/push/reset, GitHub action, background job or comment
ran. Test counts overlap and must not be summed. Python suites/checkers used:

```sh
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-exceptions-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-exceptions-no-sockets/sitecustomize.py` installs this audit hook:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

It applies to runner and inherited CLI subprocess environments. Unchanged
importability probes that replace their child environment are outside the
subprocess guard claim. No socket action was observed/permitted by guarded runs.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD origin/main` | Initially clean; expected branch; both refs `468e479743c53834dfd25cb01def163180dcee81`. Refs remain unchanged. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before edits: both required blobs match. |
| `python3 -m unittest test_ticket_settlement_exceptions` (first run) | FAILED: 1 loader error; new test imported settlement before the existing sibling-path bootstrap. Fixed test import order. |
| Same command (corrected run) | PASS: 5 tests, 16.913 s. |
| `python3 -m unittest test_ticket_settlement_controls test_ticket_refund_controls test_ticket_statement_distribution test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes test_ticket_fulfillment` (first run) | FAILED: 72 tests, 2 failures; old compatibility checks assumed only one fixture could configure each optional recording source. |
| Same command (corrected run) | PASS: 72 tests, 14.222 s; compatibility checks now follow declared source fields and verify no construction fetch. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 1.802 s. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.193 s. |
| `python3 /tmp/kix-exceptions-offline.py` | PASS: 638 tests, 44.370 s; exactly one unchanged HTTP test excluded as below. Includes the final new/changed tests. |
| `python3 /tmp/kix-exceptions-checks.py` | PASS: sequential runner; all 16 checker invocations and both architecture commands exit 0. Captured output: `/tmp/kix-exceptions-checks.json`. |
| `python3 /tmp/kix-exceptions-rust.py` | Exit 1: four test/Clippy commands unavailable, each exit 101; toolchain version commands and formatting pass. Captured output: `/tmp/kix-exceptions-rust.json`. |
| `python3 /tmp/kix-exceptions-preservation.py` | PASS: 173 protected blobs and 41 existing fixtures byte-identical to HEAD; exactly 12 allowed changed paths; AST/JSON/JSONL/whitespace valid; refs unchanged. |
| `git diff --check` | PASS. |

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. The checker runner
executes each command below normally and with `--self-test`:

| Command | Normal result | `--self-test` result |
|---|---|---|
| `python3 scripts/check_docs_index.py` | PASS: scanned=341 indexed=306 allowlisted=35 | PASS |
| `python3 scripts/check_settlement_evidence_map.py` | PASS: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 | PASS: 33 negative controls |
| `python3 scripts/check_bra_evidence_map.py` | PASS: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 | PASS: 50 negative controls |
| `python3 scripts/check_contract_error_codes.py` | PASS: rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 | PASS |
| `python3 scripts/check_openapi_contract.py` | PASS: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff | PASS |
| `python3 scripts/check_integration_gate_openapi.py` | PASS: commands=84 productionEndpoint=false publicHost=false | PASS |
| `python3 scripts/check_ci_test_discovery.py` | PASS: reference_suites=7 node_tests=8 modules=4 excluded=3; reaches all 40 BRA test modules | PASS: 18 negative controls |
| `python3 scripts/check_ci_checker_wiring.py` | PASS: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 | PASS: 13 negative controls |

CLASS_B=0 and CLASS_C=0 refer to the error-code map, not to undefined legal or
product-policy effects.

| Architecture command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS: v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.210 s. |

### Socket-free discovery reproduction

`/tmp/kix-exceptions-offline.py` uses the same discovery recipe as the predecessor
[validation record](../2026-11-03-plan-local-ticket-statement-distribution/README.md#reproduce-socket-free-discovery),
under the audit hook above. It discovers BRA tests, asserts exactly one match,
and removes only:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The remaining 638 tests run with the standard unittest runner. This is partial
local coverage; no full HTTP suite claim is made. The excluded test requires
loopback sockets, prohibited by the supervisor's no-network boundary.

### Offline Rust prerequisites and results

The existing `/home/box/.cargo/registry` was copied into
`/tmp/kix-exceptions-cargo/registry`. No dependency was downloaded or installed.
The Rust runner used:

```sh
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-exceptions-cargo
export CARGO_TARGET_DIR=/tmp/kix-exceptions-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version` | PASS: cargo 1.98.1 (797e8a9bc 2026-08-05). |
| `rustc --version` | PASS: rustc 1.98.1 (48a229cea 2026-09-01). |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: exit 101, cached `bcs` missing, required by workspace `kix-bcs1`; tests did not run. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101, same missing cached `bcs`; lint did not run. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: exit 101, same missing cached `bcs`; tests did not run. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: exit 101, same missing cached `bcs`; lint did not run. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0. |

## Changed paths and preservation

Complete list of 12 changed paths:

- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_settlement_exceptions.py`
- `reference/booking_resale_admission/test_ticket_settlement_controls.py`
- `reference/booking_resale_admission/test_ticket_refund_controls.py`
- `reference/booking_resale_admission/test_ticket_statement_distribution.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_exceptions_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_exceptions.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_reconciliation.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-03-plan-local-ticket-settlement-exceptions/README.md`

Locked blobs match before and after work:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

The preservation script compares actual bytes against HEAD for both locks,
all `reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`, contracts, workflows and
the entire settlement suite (173 blobs), plus all 41 pre-existing BRA fixtures.
All match. Historical tree remains `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
No protected path was intentionally or transiently edited. Local helper files
under `/tmp` are verification aids, not independent evidence or repository outputs.

## Deviations, uncertainty and handoff gates

One file beyond the supplied design list changed:
`test_ticket_statement_distribution.py`. The old statement/refund compatibility
checks assumed their fixtures were the sole source-configured fixtures; they
now check declared optional fields and verify construction never fetches.
No implementation scope expansion or explicit contract violation was found.
No new contract-undefined semantics are invented; existing process-local
reconciliation/refusal-key retention and restore behavior are characterized.

The supervisor's no-network instruction overrides startup fetch; cached
origin/main freshness is unknown. Missing cached `bcs` prevents local Rust
tests/Clippy, and one unchanged HTTP test is excluded as planned. These are
unavailable checks, not passing evidence; a provisioned environment must run
them. No automatic retry or network fallback was attempted.

Legal termination and refund effects remain **UNDETERMINED — User/legal**.
Existing waterfall/accounting and recipient-priority policy questions remain
with their existing User/accounting/Astra owners. No real funds, PG/bank/KYC,
public endpoints, Sui testnet/mainnet, secrets, storage/replication engine,
coin/TIX module or production runtime was needed. No bank reconciliation,
durable closure, external exactly-once, chain finality, legal compliance,
production readiness or cross-machine compensation/rollback is claimed.
No broader F01/F03 completion or capability grade is promoted.

Builder handoff: implementation complete with recorded verification limitations;
**not merge-ready**. Implementation/final task commit SHA: not created, as the
supervisor owns git publication; the uncommitted worktree remains based on
`468e479743c53834dfd25cb01def163180dcee81`. Merge commit/post-merge verification:
not applicable (no merge). Exact-head KTX CI run ID/status/conclusion:
not available/unqueried. Exact-head KIX protocol CI run ID/status/conclusion:
not available/unqueried. No earlier head's CI is claimed for this patch.
The supervisor must commit and arrange independent A2 non-author exact-head
review, both completed/success KTX/KIX checks and unavailable HTTP/Rust
verification before any merge proposal. User-only merge authorization remains.
