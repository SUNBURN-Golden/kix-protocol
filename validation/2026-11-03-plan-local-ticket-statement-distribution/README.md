# Shared ticket recorded statements and explicit distribution

Node `plan-local-ticket-statement-distribution`. Task input is the supervisor's
node specification and design supplied in this session; no issue or task document
exists. Not ASTRA program mode. Branch
`agent/kix-plan-local-ticket-statement-distribution`.
Initial HEAD and cached origin/main: `ed0ce301bc7d5965bf1e9f0518ff2f5cd2de62ba`.
No local base delta. The supervisor prohibits network, overriding the initial
fetch; remote freshness is unverified. No commits or GitHub writes authorized.

## Pre-change coverage inventory

Recorded before adding tests. Paths below are relative to `reference/`.

| Requirement | Existing evidence | Classification / remaining gap |
|---|---|---|
| Recorded commit and later statement | `settlement_f01_f03/test_statement_adapter.py::StatementAdapterTests` | Partial: adapter parity exists; shared desk and file/stdin transport absent |
| Conservation and direct-FSM parity | `settlement_f01_f03/test_settlement_properties.py`; adapter parity tests | Partial: arithmetic sufficient; four-machine composition absent |
| Replay, conflicting request keys and movement bindings | Adapter replay/binding tests; `test_settlement_rejection_atomicity.py` | Partial: FSM sufficient; direct-versus-recorded desk keys absent |
| Invalid/frozen order and later cash | `test_mock_settlement.py::SettlementMockTests.test_f02_caller_order_selects_shortfall_and_then_freezes`, `test_f02_later_cash_continues_on_the_frozen_order`; rejection-atomicity tests | Sufficient FSM coverage; desk routing absent |
| Partial refund refusal | `test_settlement_fsm.py::SettlementFsmTests.test_refund_block_survives_replay_and_is_not_a_clawback`; `booking_resale_admission/test_ticket_refund_controls.py` | Partial: desk currently probes distribution directly, selector absent |
| Tax and held remain non-cash | `settlement_f01_f03/test_adopted_policy.py::AdoptedPolicyTests.test_t0_tax_and_held_stay_non_cash` | Sufficient arithmetic coverage; assert preservation in composed journey |
| Source failures make no FSM call or key binding; fetch once | `StatementAdapterTests.test_local_source_rejections_do_not_call_fsm_or_bind_key` | Partial: source/adapter sufficient; injection/fixture/CLI absent |
| No construction fetch, automatic distribution or retry | Adapter constructor/forwarding tests; shared desk construction tests | Partial: configured statement desk absent |
| Existing direct commit/refund controls and strict schema | `booking_resale_admission/test_ticket_settlement_controls.py`, `test_ticket_refund_controls.py`, `test_ticket_operations_cli.py` | Partial: retain and extend selector matrices |

No arithmetic, source or adapter tests will be duplicated as new economic rules.
Snapshots omit retained rejection bookkeeping; explicit key probes supplement them.

## Implementation and acceptance evidence

Only the shared session, fixture loader and CLI compose existing operations.
`statement_source` is optional in both constructors. The adapter holds the same
settlement instance as all three ticket consumers. No settlement implementation,
contract, catalogue, SDK, CI or authoritative task input changed.

New source-informed tests live in
`reference/booking_resale_admission/test_ticket_statement_distribution.py`:

| Test | Gap addressed |
|---|---|
| `test_file_stdin_and_api_journeys_match_direct_fsm_after_every_step` | Both transcripts through Python methods, CLI dispatcher, executable file and stdin; every receipt/error and all four machines' canonical states, digests and journals match a separately constructed raw-FSM graph after each request. Exactly one source fetch per recorded request, including replay; other sources untouched. In-memory journal restoration also matches. |
| `test_retained_order_refusals_type_key_freedom_and_refund_block` | Non-list order leaves its key free; duplicate/missing/unknown payees retain refusal keys; changed accepted order refuses. Later statement adds undistributed cash only. Partial refund blocks distribution without changing prior allocation; an older accepted distribution key still replays its first result. |
| `test_direct_recorded_key_equivalence_conflicts_and_movement_characterization` | Recorded and direct commit share existing operation/key/body identity. First receipt survives later distribution. Changed body/operation and movement conflicts retain FSM semantics. New-key repeated movement is economically inert but journaled, an existing characterization. |
| `test_injection_no_construction_fetch_and_exact_adapter_forwarding` | Constructor shared identity and state parity, no fetch; required keyword-only signatures; original arguments, receipt and exception forwarded once; missing source preserves old fixtures and emits exit 1 with explicit-line continuation. |
| `test_source_failures_fetch_once_no_fsm_call_or_key_binding` | Both selectors: absent record, malformed text/non-object, missing/extra fields, mismatched/non-string identity, immediate error/timeout. One fetch, zero FSM calls and unchanged graph; same live FSM accepts a valid record using that exact key afterward. |
| `test_economic_invalid_records_reach_fsm_and_retain_refusals` | Shaped but economically invalid records retain FSM refusal/key semantics in both commit and observation phases. Fixed body with old key conflicts, explicit fresh key succeeds. |
| `test_strict_optional_fixture_schema_defers_record_decoding` | Wrong containers, missing/extra fields, duplicates, payload exclusivity, invalid identifiers and unsupported fault values rejected before graph construction. Distinct identity pairs allowed; raw text decoded only on request; every old shared fixture loads without a statement source. |
| `test_cli_source_errors_continue_structural_errors_stop` | Source failures through executable file/stdin exit 1 and continue to explicit view; required/missing/extra fields and wrong containers stop with exit 2 without fetch/effects. File/stdin structural failure stops after a prior successful view. |

Existing settlement forwarding coverage now checks ten selectors, separating the
three adapter methods from seven direct methods. `distribute` forwards opaque
order objects without mutation or defaults; original receipt/error identity and
exact call count are checked. Existing strict-selector matrices include the new
selectors. The refund test drops only its obsolete unsupported-distribute case.

`ticket_operations_statement_distribution.jsonl` exits 0 using a preserved
issued anchor, both adoptions and clocks plus a separate ticket-bound claim.
First statement: gross 6000 = cash 5500 + fee 200 + tax 100 + held 100 + adjustment
100. Later statement: gross 4001 = cash 3801 + fee 200. Explicit distributions
using `["platform", "organizer"]` allocate 500/5000 then 0/3801. Final cash is
9301, non-cash accounting and outstanding obligations are 700, open receivable
is zero. Original tax/held inputs remain in the accepted journal. The unchanged
`check_claim_view` oracle checks conservation after successful settlement steps.
Statement calls leave distributed cash unchanged.

`ticket_operations_statement_boundaries.jsonl` exits 1, demonstrating historical
first-result replay, conflicting keys, invalid/frozen order and partial-refund
refusal. Both transcripts run as files and stdin in the focused suite, comparing
every output row with direct controls. Reproducible CLI commands are in the
[shared desk guide](../../reference/booking_resale_admission/README.md#recorded-statements-and-explicit-distribution-on-the-shared-ticket-desk).

## Commands actually run and results

All commands ran from the repository root in the foreground. No network,
installation, commit, push, PR, issue or comment action ran. Python suite/checker
commands used this environment:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-statements-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-statements-no-sockets/sitecustomize.py` contains:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

This hook applies to the runner and inherited CLI subprocess environments.
Unchanged importability probes that replace their child environment are outside
the subprocess guard claim. No socket action was observed or permitted by the
guarded runs. Counts overlap; do not sum them.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD origin/main`; `git branch --show-current` | Initially clean; expected branch, both refs `ed0ce301bc7d5965bf1e9f0518ff2f5cd2de62ba`; unchanged at preservation check. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before edits. |
| `python3 -m unittest test_ticket_statement_distribution` (first run) | 8 tests, 5 failures: test control compared the raw operation name with the local selector envelope. Corrected test helper only. |
| Same command (second run) | 8 tests, 2 errors: missing explicit booking-session clock in new transcript; test incorrectly expected statement details in public view rather than accepted journal. Added explicit clock line, corrected test. |
| Same command (corrected run) | PASS: 8 tests, 1.284 s. |
| `python3 -m unittest test_ticket_settlement_controls test_ticket_refund_controls test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes test_ticket_fulfillment` | PASS: 64 tests, 12.389 s. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 1.843 s. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.213 s. |
| `python3 /tmp/kix-statements-offline.py` | PASS: 633 tests, 28.537 s; exactly one HTTP test excluded below. |
| `python3 /tmp/kix-statements-checks.py` | PASS: all 16 checker invocations and both architecture commands exit 0; sequential subprocess runner, captured output `/tmp/kix-statements-checks.json`. |
| `python3 /tmp/kix-statements-rust.py` | Exit 1: four test/Clippy commands unavailable (each exit 101); toolchain version commands and formatting pass. Details below; captured output `/tmp/kix-statements-rust.json`. |
| `python3 /tmp/kix-statements-preservation.py` (initial run) | Failed to read a Unicode historical filename because Git quoted it. No file changes; fixed verification script to use NUL-delimited paths. |
| Same preservation command (corrected run) | PASS: 173 protected blobs, 38 existing booking fixtures byte-identical to HEAD; exactly 12 allowed changed paths; Python AST/JSON/JSONL/whitespace valid; refs unchanged. |
| `git diff --check` | PASS. |

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. Each checker ran
as `python3 scripts/check_<name>.py` and again with `--self-test`:

| Name | Normal result | Self-test result |
|---|---|---|
| `docs_index` | PASS: scanned=340 indexed=305 allowlisted=35 | PASS |
| `settlement_evidence_map` | PASS: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 | PASS: 33 negative controls |
| `bra_evidence_map` | PASS: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 | PASS: 50 negative controls |
| `contract_error_codes` | PASS: rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 | PASS |
| `openapi_contract` | PASS: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff | PASS |
| `integration_gate_openapi` | PASS: commands=84 productionEndpoint=false publicHost=false | PASS |
| `ci_test_discovery` | PASS: reference_suites=7 node_tests=8 modules=4 excluded=3; reaches all 39 booking test modules | PASS: 18 negative controls |
| `ci_checker_wiring` | PASS: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 | PASS: 13 negative controls |

The error-code map's CLASS_B=0 concerns that map; it does not close undefined
product policy or characterize all behavior.

| Command | Result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.206 s. |

### Reproduce socket-free discovery

Save as `/tmp/kix-statements-offline.py` and run with the environment above:

```python
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path('reference/booking_resale_admission').resolve()))
excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test
suite = unittest.defaultTestLoader.discover('reference/booking_resale_admission',
    top_level_dir='reference/booking_resale_admission')
tests = list(flatten(suite))
assert sum(t.id() == excluded for t in tests) == 1
print('Explicit single HTTP exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(t for t in tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

This is partial local coverage of the full CI suite. The single unchanged HTTP
loopback test was excluded according to the supplied design and predecessor
recipe because network actions are prohibited; full HTTP coverage remains a
delivery gate.

### Offline Rust prerequisites

Used the existing toolchain and a copy of `/home/box/.cargo/registry` under
`/tmp/kix-statements-cargo/registry`. No dependencies downloaded or installed.

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-statements-cargo
export CARGO_TARGET_DIR=/tmp/kix-statements-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version` | PASS: cargo 1.98.1 (797e8a9bc 2026-08-05). |
| `rustc --version` | PASS: rustc 1.98.1 (48a229cea 2026-09-01). |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: missing cached `bcs` required by workspace `kix-bcs1`; tests did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cached `bcs`; lint did not execute. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: same missing cached `bcs`; tests did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cached `bcs`; lint did not execute. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |

## Changed paths and preservation

Complete changed-path list (12):

- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_fixture.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_statement_distribution.py`
- `reference/booking_resale_admission/test_ticket_settlement_controls.py`
- `reference/booking_resale_admission/test_ticket_refund_controls.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_statement_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_statement_distribution.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_statement_boundaries.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-03-plan-local-ticket-statement-distribution/README.md`

Locked blobs match before and after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

The preservation check compares actual bytes against HEAD for both locks, all
`reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`, contracts, workflows and the
entire settlement suite: 173 blobs. All 38 pre-existing booking fixtures also
match HEAD. Historical reference tree remains
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. No protected file was intentionally
or transiently edited. Verification helper outputs in `/tmp` are local aids,
not committed artifacts or independent evidence.

## Deviations, uncertainty and delivery gates

No implementation scope deviation or contract violation found. Fixture setup
prepares the separate claim through explicit existing initiate/authorize/capture
and binding operations; its booking clock still requires an explicit transcript
line, preserving the existing session prerequisite. This changes no FSM policy.

The supervisor's no-network rule replaces AGENTS.md §1 fetch; cached origin/main
freshness is unknown. Rust tests/Clippy could not execute due to missing local
`bcs`; this is an environment limitation, not a passing test. One unchanged
HTTP test is excluded from local discovery as planned. No automatic retry or
network fallback was used. Required tests must run in a provisioned environment.

Waterfall values remain **UNDETERMINED — User/accounting**; recipient-priority
policy remains **UNDETERMINED — Astra**; refund liability remains
**UNDETERMINED — User/legal**. Existing new-key repeated-movement journal behavior
is characterization, not a newly defined contract. No real PG/bank/KYC, funds,
public endpoints, Sui, storage engine, persistence or production runtime was used.
No durability, exactly-once external execution, legal compliance, chain finality,
production readiness or cross-machine rollback is claimed. No broader item or
P04/F02 completion label is promoted.

Builder state: local implementation ready for supervisor handoff with the above
verification limitations; **not merge-ready**. Implementation and final task
commit SHA: not created by this builder; working tree remains based on
`ed0ce301bc7d5965bf1e9f0518ff2f5cd2de62ba`. Merge SHA and post-merge verification:
not applicable, no merge. Exact-head KTX CI run ID/status/conclusion: unqueried,
not available. Exact-head KIX protocol CI run ID/status/conclusion: unqueried,
not available. No earlier SHA's CI is claimed for this work. The supervisor must
commit and arrange independent A2 non-author exact-head review, successful
completed KTX/KIX workflows, and applicable HTTP/Rust coverage before any merge
proposal. Ready transition and merge require the User's explicit authorization.
