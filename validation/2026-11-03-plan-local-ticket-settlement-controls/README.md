# Shared local ticket settlement controls

## Basis and boundaries

Node `plan-local-ticket-settlement-controls`; supervisor-supplied node specification
and design plan are the immutable task input. No task issue or docs/tasks document.
Not ASTRA program mode. Branch `agent/kix-plan-local-ticket-settlement-controls`.
Initial HEAD and cached origin/main: `6a784077d16bad54d5189b6b2a0af8dce8d0299a`.
No base delta locally. Supervisor prohibits network, overriding the §1 fetch;
remote freshness is unverified. No commits, publication or merge in this session.
Track P synthetic in-memory composition only. Product policy remains
UNDETERMINED — Astra/User; legal/accounting treatment remains UNDETERMINED —
User/designated external reviewers. Fixture numbers are examples, not policy.

## Existing coverage

Recorded before adding tests:

| Acceptance | Existing evidence | Classification / gap |
|---|---|---|
| Settlement phases, amounts, policy, replay | `reference/settlement_f01_f03/test_settlement_fsm.py`, `test_adopted_policy.py::AdoptedPolicyTests`, `test_settlement_rejection_atomicity.py` | Sufficient FSM coverage; selector composition uncovered |
| Uncommitted bound issuance, mismatch, refusal replay and fresh keys | `reference/booking_resale_admission/test_ticket_fulfillment.py::TicketFulfillmentTests.test_uncommitted_mismatched_and_expired_issuance` | Partial: direct later commit covered; interactive transitions missing |
| Recorded resale payments and bound transfer | `test_resale_payment_source.py`, `test_resale_payment_adapter.py`, `test_ticket_operations_session.py::TicketOperationsSessionTests.test_transcripts_session_and_cli_match_direct_graph_after_every_request` | Partial: interactive settlement pause missing |
| Shared instance and direct control | `test_ticket_operations_session.py::TicketOperationsSessionTests.test_one_shared_graph_per_construction_and_custom_inputs`, `direct_graph`, `direct_call`, `snapshot` | Partial: settlement wrapper/dispatch missing |
| Strict JSON, exits, fixtures and anchor | `test_ticket_operations_cli.py::TicketOperationsFixtureTests`, `TicketOperationsCliTests`; `test_ticket_fulfillment.py` | Partial: new selector schemas/journeys missing; validators sufficient unchanged |
| No automatic effects and false flags | Existing shared transcript snapshots and reservation/resale/admission flag helpers | Partial: new settlement actions missing |

Source-informed composition evidence, not clean-room independence. Canonical state
and journals omit retained refusals; explicit replay assertions must supplement them.

## Implementation and acceptance evidence

`TicketSettlementSession` publishes five methods after successful setup on the
same `SettlementMachine` consumed by reservation, resale and admission. The
shared CLI uses an explicit five-entry allowlist, existing `exact_fields` and
`decode_json`, and the unchanged domain-error envelope. Currency and every
statement component (including nullable adjustment reason) are required; policy
is forwarded unchanged. No FSM, contract, validator, SDK or CI definition changed.

`reference/booking_resale_admission/test_ticket_settlement_controls.py` adds eight
focused composition tests, each addressing the gaps above:

| Exact test ID (class `TicketSettlementControlsTests`) | Gap addressed |
|---|---|
| `test_transcripts_compare_every_step_and_preserve_refused_keys` | Independently constructs a public-FSM control graph; compares receipts/errors, canonical states, digests and all four journals after every booking/resale request. Explicit assertions distinguish retained refused keys, supplied fresh keys, historical initiate receipts and current views. Settlement actions leave all three ticket machines and all recording-fetch histories unchanged. Issuance does not adopt; transfer does not synchronize admission. Existing flag helpers and settlement false flags are checked. |
| `test_file_stdin_and_executable_exits_zero_one_two` | Both complete journeys run via file and stdin with every row compared to the direct control and exit 1. Success-only streams exit 0; structural streams stop at the offending line with exit 2, including after an accepted action. |
| `test_five_methods_forward_once_with_exact_objects_receipts_and_errors` | Checks the exact five selectors, method signatures and required keyword-only arguments, positional/keyword subject support, exact opaque objects, one FSM call and original receipt/exception identity through Python and dispatch. |
| `test_publication_calls_no_settlement_method` | Wrapper publication invokes no public settlement method; failed setup publishes no wrapper. |
| `test_illegal_phases_amount_mismatch_replay_and_historical_receipts` | Premature capture/commit; repeated authorization/capture/commit; inconsistent statement components; retained refusals after progress; historical authorization receipt; changed subject/body/operation conflicts; unknown view. |
| `test_committed_gross_mismatch_at_both_ticket_gates` | Initiated/committed gross differs from the paid reservation or recorded resale amount; old key retains its original uncommitted refusal and fresh key refuses amount mismatch. |
| `test_strict_json_and_policy_errors_stop_or_continue_without_side_effects` | Every selector's missing/extra fields, wrong containers, unsupported operations, nested duplicate keys, NaN/Infinity/exponent overflow; stopping structural errors; unchanged FSM policy errors and next-explicit-line continuation. |
| `test_fixture_retains_required_anchor` | New fixture still rejects missing anchor issuance, binding, either adoption or explicit clock. |

Existing `test_ticket_operations_session.py` helpers now handle settlement without
routing through the implementation; its shared-instance test also names the new
wrapper. The existing shared CLI schema matrix includes settlement. Standalone
finance tooling and standalone settlement CLIs were not added.

The new version-1 fixture retains the existing anchor and prepares a separate
paid, unissued reservation. It includes the merged recorded-payment source for
the anchor's resale. The 13-line booking and 16-line resale transcripts explicitly
initiate, bind, encounter an uncommitted refusal, authorize/capture/commit, replay
the refused key and separately request issuance/acceptance with a caller-supplied
fresh key. Settlement progress alone performs no ticket/payment follow-up.

## Commands/results

Commands ran from the worktree root. Python test/check commands used installed
`python3`, `PYTHONDONTWRITEBYTECODE=1` and:

```bash
export PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"
```

The focused command ran first. All later Python tests/checkers also prepended
`/tmp/kix-settlement-no-sockets` to PYTHONPATH using the guard below. Runners used
sequential foreground subprocesses; no long job was launched in the background.
The temporary runner JSON logs are `/tmp/kix-settlement-tests.json`,
`/tmp/kix-settlement-checks.json`, `/tmp/kix-settlement-rust.json` in this session;
the actual per-command results are recorded here for durable handoff.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; HEAD/cached main equal the base above; expected branch. Final refs/branch unchanged; 11 allowed changed paths |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before work; final verification below |
| `git ls-tree HEAD reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; final working blobs match HEAD |
| `python3 -m unittest test_ticket_settlement_controls` (first run) | Exit 1: 8 tests, 2 failures caused by incorrect new-test expected error names (`AMOUNT_MISMATCH` and `INVALID_SLOT`). Actual unchanged FSM codes are `SETTLEMENT_COMPONENT_MISMATCH` and `SLOT`. Corrected assertions only |
| `python3 -m unittest test_ticket_settlement_controls` (rerun) | PASS: 8 tests, 1.181 s |
| `python3 -m unittest test_ticket_fulfillment test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes test_booking_session test_booking_cli test_resale_session test_resale_cli test_resale_payment_source test_resale_payment_adapter test_admission_session test_admission_cli` | PASS: 137 tests, 12.375 s |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 1.864 s |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.254 s |
| `python3 /tmp/kix-settlement-offline.py` | PASS: 617 tests, 24.035 s; exactly one HTTP test excluded, partial socket-free coverage only |
| `python3 /tmp/kix-settlement-verify.py` | PASS: sequential foreground regression commands above, all exits 0 |
| `python3 /tmp/kix-settlement-verify.py checks` | PASS: eight checkers, each plain and self-test, plus two architecture commands below, all exits 0 |
| `python3 /tmp/kix-settlement-rust.py` | Exit 1: offline dependency prerequisites unavailable for test/Clippy commands; versions and formatting pass, individual results below |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/kix-settlement-preservation.py` | PASS: 178 protected blobs and all 31 existing booking fixtures match HEAD; exactly 11 allowed changed paths; AST/JSON/JSONL/whitespace valid; branch/HEAD/cached main unchanged |
| `git diff --check` | PASS |

Counts overlap and must not be summed. Inspected `.github/workflows/ktx-kernel.yml`
and `protocol.yml`; commands below are the closest relevant socket-free/offline
local equivalents, not full repository CI. The new test module is discovered by
the unchanged protocol workflow.

Each checker command actually ran as `python3 scripts/<name>.py`, then the same
command with `--self-test`:

| Checker | Plain result | Self-test result |
|---|---|---|
| `check_openapi_contract` | PASS: openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff | PASS: self-test: pass |
| `check_integration_gate_openapi` | PASS: integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false | PASS: self-test: pass |
| `check_settlement_evidence_map` | PASS: settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 | PASS: self-test: pass (33 negative controls) |
| `check_bra_evidence_map` | PASS: bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 | PASS: self-test: pass (50 negative controls) |
| `check_contract_error_codes` | PASS: contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 | PASS: self-test: pass |
| `check_docs_index` | PASS: docs index ok: scanned=338 indexed=303 allowlisted=35 | PASS: self-test: pass |
| `check_ci_test_discovery` | PASS: ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3; all 37 booking test modules reached | PASS: self-test: pass (18 negative controls) |
| `check_ci_checker_wiring` | PASS: ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 | PASS: self-test: pass (13 negative controls) |

| Command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.297 s |

The error-code map's CLASS_B=0 count concerns that map only; it does not erase
existing behavioral Class B limitations.

Rust commands used the installed CI-version toolchain and copied only existing
registry bytes (no installation or downloads) from `/home/box/.cargo/registry`
to `/tmp/kix-settlement-cargo/registry`. Environment:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-settlement-cargo
export CARGO_TARGET_DIR=/tmp/kix-settlement-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version` | PASS: cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `rustc --version` | PASS: rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: no matching cached `bcs`, required by workspace `kix-bcs1`; no tests/lint executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: no matching cached `bcs`, required by workspace `kix-bcs1`; no tests/lint executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: no matching cached `bcs`, required by workspace `kix-bcs1`; no tests/lint executed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

No offline prerequisite retry or network fallback was attempted. No Rust file changed.

### Reproduce the partial socket-free selection

`/tmp/kix-settlement-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

`/tmp/kix-settlement-offline.py`:

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
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(
    t for t in tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

Actual selection invocation (the foreground runner supplies this environment):

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="/tmp/kix-settlement-no-sockets:$PWD/reference/booking_resale_admission:$PWD" \
python3 /tmp/kix-settlement-offline.py
```

Every new CLI transcript subprocess inherits the guard. The discovery assertion
requires exactly one occurrence of the excluded full test ID; no other discovered
test is removed. Some existing importability probes construct their own child
environment; their unchanged source remains outside this guard's subprocess
claim. Full HTTP coverage is unchanged and remains a supervisor delivery gate.

## Changed paths and preservation

Complete changed-path list:

- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_settlement_controls.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_booking.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_resale.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-03-plan-local-ticket-settlement-controls/README.md`

Both locked blobs match before/after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Preservation checks compare Git blob hashes for all historical reference bytes,
locked files, `.aiops/`, `docs/tasks/`, contracts, workflows, settlement suite,
ticket FSMs and fixture validators against HEAD. All 31 preexisting booking
fixtures are byte-identical. The exact changed-path allowlist excludes every
other tracked path; AST/JSON/JSONL and whitespace checks also pass.

## Limitations and delivery gates

Class A: exercised transitions, gross/component gates, immutable first-result
semantics, historical/current views and domain errors match the unchanged
contracts. No explicit contract violation was found. No new contract-undefined
behavior was assigned semantics. Existing Class B clock-skew partial effects,
unsynchronized views, fault-injection non-rollback and process-local refusal
history remain unchanged. Canonical state/journals exclude retained refusals;
explicit refusal replay assertions cover those in this session. No cross-machine
rollback, receipt durability or synchronization is claimed.

Deviations: the supervisor's network prohibition overrides AGENTS.md §1 fetch;
no task issue/document exists or was created. Verification uses the required
partial socket-free selection; offline Rust tests/Clippy are unavailable due to
missing cached `bcs`. No design scope expansion or implementation STOP dependency
arose; no DECISION_REQUIRED file is needed. The initial two test expectation
errors and their corrections are recorded above.

No standalone finance workbench, statement-source integration, F04, refund or
distribution selector, reward coupling, primary-payment handoff, new protocol
command, network, persistence, credential, paid resource, chain execution or
production activation was added. Mock-only funds/finality/durability/production
flags remain false. This evidence is source-informed builder composition testing,
not clean-room independence, production safety, distributed fencing, bank
exactly-once, chain finality, legal/accounting compliance or production readiness.
Move/localnet/ZK, unrelated reference suites, full HTTP and Rust tests/lint were
not run successfully or claimed. No hardware/resources/policy decisions are
required to implement this node; product policy remains UNDETERMINED — Astra/User,
legal/accounting treatment UNDETERMINED — User/designated external reviewers.

The patch is uncommitted by instruction. Observed implementation HEAD remains
`6a784077d16bad54d5189b6b2a0af8dce8d0299a`, which does not contain these changes.
Exact final task head is supervisor-assigned and not yet available. No commit,
push, PR, issue, comment, ASTRA marker or merge was created.

| Delivery gate | Run ID / status / conclusion |
|---|---|
| Non-author A2 exact-head review | Pending supervisor delivery; builder checks are not review |
| Exact-final-head KTX kernel verification | Unavailable / pending / not claimed |
| Exact-final-head KIX protocol verification | Unavailable / pending / not claimed |
| Merge SHA, merge locked blobs and post-merge main CI | Not applicable: not merged |

Supervisor follow-up: establish the final committed head, obtain non-author A2
review, run unchanged full HTTP and Rust coverage with prerequisites, and require
both exact-final-head workflows completed/success. User merge authorization stays
separate. Builder READY means local implementation handoff, not merge readiness.
