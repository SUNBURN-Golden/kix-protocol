# Shared local ticket refund controls

Node `plan-plan-local-ticket-refund-controls`. Immutable task input: supervisor's
node specification and design in the session; no issue or docs/tasks document.
Not ASTRA program mode. Branch `agent/kix-plan-plan-local-ticket-refund-controls`.
Initial HEAD and cached origin/main: `a02b62c5314ad40f0c0afc3459cfe68ddc36ccbd`.
No local base delta. Supervisor prohibits network, overriding AGENTS.md §1 fetch;
remote freshness is unverified. No commits or GitHub actions are authorized.
Both required kernel blobs match before work. Historical reference and existing
fixtures will be compared byte-for-byte with HEAD after work.

## Existing coverage inventory (before new tests)

| Acceptance | Existing evidence | Classification / composition gap |
|---|---|---|
| Refund arithmetic, full reclassification, partial burden | `reference/settlement_f01_f03/test_mock_settlement.py::SettlementMockTests` refund tests; `test_settlement_multi_payee_refund.py` F–I tests; `test_settlement_fsm.py::SettlementFsmTests.test_refund_block_survives_replay_and_is_not_a_clawback` | Sufficient FSM coverage; shared desk absent |
| One fetch, identity checks, source failures and exact forwarding | `test_cancel_acceptance_adapter.py::CancelAcceptanceAdapterTests`; `test_cancel_acceptance_source.py` | Sufficient adapter/source coverage; injection and CLI transport absent |
| Shared machine, constructor isolation, original receipts/errors | `reference/booking_resale_admission/test_ticket_operations_session.py::TicketOperationsSessionTests`; `test_ticket_settlement_controls.py::TicketSettlementControlsTests` | Partial; refund methods absent |
| File/stdin partial/full/replay journeys and state parity per step | Existing ticket settlement booking/resale transcripts; `direct_graph`, `machines`, `snapshot` helpers | Not covered for refunds |
| Missing obligations, excess, invalid phases/amounts/identities, retained refusals | `CancelAcceptanceAdapterTests.test_economic_rejections_and_retained_keys_remain_in_fsm`, `test_phase_and_identifier_errors_match_direct`; multi-payee refund rejection/replay tests | Sufficient underneath; desk composition absent |
| Missing/malformed/mismatched recordings and immediate faults | `CancelAcceptanceAdapterTests.test_local_failures_never_call_fsm_mutate_state_or_consume_key` | Sufficient underneath; optional fixture and error envelope absent |
| Cash unchanged, adjustment open, no ticket side effects, partial distribution blocking | Adapter example tests, mock refund tests, ticket graph snapshots | Partial; new composition absent |
| Fixture compatibility, strict JSON and exit 0/1/2, discovery | `test_ticket_operations_cli.py::TicketOperationsFixtureTests`, `TicketOperationsCliTests`; discovery checker | Partial; optional cancellation fixtures and selectors absent |

Tests are source-informed composition evidence, not clean-room independence.
Canonical state and journals omit refusal bookkeeping; explicit replay/conflict
probes must supplement state comparisons. No new burden rule is authorized.

## Implementation and acceptance evidence

The two methods/selectors use the existing shared settlement machine. Refund
binding forwards once to `SettlementMachine.bind_refund`; observation calls one
unchanged `CancelAcceptanceAdapter.apply`, which performs one unchanged source
fetch and, on a valid recording, one existing `observe_mock_cancel_acceptance`.
Optional source injection performs no fetch. Fixture version 1 accepts optional
`cancel_acceptances` with exact identity pairs and one text/fault payload. Raw
payloads are validated only at explicit fetch. Missing source configuration is
an existing source-error-family diagnostic. No source, adapter, arithmetic, FSM,
contract, HTTP, SDK, catalogue, CI or runtime file changed.

New source-informed tests in `test_ticket_refund_controls.py`, class
`TicketRefundControlsTests`, close the composition gaps:

| Test | Evidence / gap addressed |
|---|---|
| `test_journeys_compare_api_cli_adapter_and_raw_fsm_after_every_step` | Partial/full/replay journeys through both importable methods and dispatch; separate direct adapter and raw-FSM graphs. Receipts, errors, canonical states, digests and journals compared after every step; each journey also executes through file and stdin and compares every output row. Shared object identities, source call histories and false flags checked. |
| `test_optional_injection_publication_forwarding_and_original_objects` | Configured constructor performs no fetch/economic effect beyond explicit setup; adapter receives shared machine/source. Required method signature, exact opaque arguments, one call, original receipt/error identity. Absent source preserves old fixtures, emits exit-1 diagnostic and continues only to explicit view. |
| `test_source_failures_match_adapter_fetch_once_and_leave_key_free` | Absent recordings, malformed text/non-object, missing/extra payload fields, mismatched/non-string identities and both immediate faults. Direct-adapter error parity, state isolation, exactly one fetch per explicit attempt, zero FSM calls on failure, no retained key, executable exit 1 and explicit-line continuation. |
| `test_economic_rejections_retained_keys_and_conflicts_at_both_phases` | CAPTURED and COMMITTED; missing obligation, excessive acceptance, invalid amount; retained refusal after later binding, body/key conflicts, unchanged confirmed cash, reduced refund outstanding and open adjustment. Existing repeated-source/new-key inert journal-entry characterization retained. |
| `test_partial_obligation_fully_accepted_and_summed_bindings_keep_burden_undefined` | Fully accepted partial obligation still has UNDEFINED burden; additional partial bindings totaling gross do not reclassify. Direct distribution probes on all four graphs preserve existing refusal and state, without exposing a distribution selector. |
| `test_invalid_bindings_and_phases_preserve_direct_fsm_errors` | Invalid binding amounts/beneficiary/reason/refund identity and premature bind/observation preserve direct FSM errors and state. |
| `test_strict_recording_fixture_schema_and_optional_compatibility` | Optional source absent in all old session fixtures; strict structural schema, missing/extra fields, duplicate pairs, text/fault exclusivity, unsupported fault values and invalid identities rejected before graph construction. Different identity pairs allowed; raw malformed payload not fetched during construction. |
| `test_cli_strict_json_exit_two_stops_after_prior_success` | Missing/extra selector arguments, wrong container, unsupported raw-FSM/distribution/cancel selectors, duplicate JSON keys and nonfinite numbers stop without effects/fetch. File/stdin executable exit 2 after prior success; structural fixture exit 2. |

The existing settlement forwarding test now checks seven selectors, tests the
six direct FSM methods (including binding) with exact opaque objects and original
receipts/exceptions, and delegates adapter-forwarding evidence to the focused
module. Its existing structural matrix includes both new selectors. Existing
`test_ticket_operations_cli.py` already derives its strict-selector matrix from
the dispatch table; no edit or duplicate matrix was needed there.

Refund steps leave reservation, resale and admission canonical states, digests,
journals and all other source fetch histories unchanged. They do not cancel a
booking, revoke a ticket, transfer ownership, consume admission or synchronize
adoptions. Partial binding 4000 plus acceptances 1000 and 500 produces refund
outstanding 2500 and PG adjustment outstanding 1500. One initial gross binding
10001 plus full acceptance produces refund outstanding 0 and adjustment 10001.
Confirmed cash stays 10001, `external_return_closed` stays false. Full acceptance
of a partial obligation and partial bindings totaling gross remain distinct from
one initial gross binding. Historical first receipts and retained refusal keys
are probed explicitly because snapshots omit refusal bookkeeping.

## Commands and actual results

Commands ran from the worktree root, in foreground, using `python3` and
`PYTHONDONTWRITEBYTECODE=1`. Initial focused and ticket-only discovery commands:

```bash
export PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"
```

Subsequent Python suite/checker commands also prepend
`/tmp/kix-refund-no-sockets` to that PYTHONPATH. Its `sitecustomize.py` installs this
audit hook, inherited by new journey subprocesses:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean, expected branch; HEAD/cached main both `a02b62c5314ad40f0c0afc3459cfe68ddc36ccbd`. Final refs unchanged. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before work; final byte comparison below. |
| `git ls-tree HEAD reference/v0.3-rc1` | Historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `python3 -m unittest test_ticket_refund_controls` — initial invocations | First invocation returned partial `.EE` output; terminal output was not collected. Next collected run: 8 tests, 1 failure and 2 errors. New-test helper incorrectly duplicated a settlement-ID keyword; distribution probe incorrectly included the absent zero-fee payee. Corrected tests only. |
| `python3 -m unittest test_ticket_refund_controls` — corrected run | PASS: 8 tests, 2.529 s. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_ticket*.py'` | PASS: 64 tests, 11.030 s. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 1.745 s. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.188 s. |
| `python3 /tmp/kix-refund-offline.py` | PASS: 625 tests, 25.384 s; partial socket-free booking/resale/admission discovery with exactly one HTTP exclusion below. |
| `python3 /tmp/kix-refund-checks.py` | PASS: all 16 checker invocations and both architecture commands below exit 0; sequential foreground runner. Actual captured outputs: `/tmp/kix-refund-checks.json`. |
| `python3 /tmp/kix-refund-rust.py` | Exit 1: four test/Clippy prerequisites unavailable (exit 101 each); toolchain versions and formatting pass. Individual results below; actual captured outputs `/tmp/kix-refund-rust.json`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/kix-refund-preservation.py` | PASS: 172 protected blobs and all 34 existing booking fixtures match HEAD; exactly 12 allowed changed paths, Python AST/JSON/JSONL/whitespace valid; branch/HEAD/cached main unchanged. |
| `git diff --check` | PASS. |

Counts overlap; do not sum them. The focused test executes the documented CLI
command once with each of `ticket_operations_refund_partial.jsonl`,
`ticket_operations_refund_full.jsonl`, `ticket_operations_refund_replay.jsonl`,
then with `--requests -` and the same text on stdin. All six executable journeys
exit 0 with every output row matching the direct controls. Other executable
cases in the focused tests establish exits 1 and 2.

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. Each checker below
actually ran as `python3 scripts/<name>.py` and then with `--self-test`:

| Checker | Normal result | Self-test result |
|---|---|---|
| `check_docs_index` | PASS: scanned=339 indexed=304 allowlisted=35 | PASS |
| `check_settlement_evidence_map` | PASS: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 | PASS: 33 negative controls |
| `check_bra_evidence_map` | PASS: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 | PASS: 50 negative controls |
| `check_contract_error_codes` | PASS: rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 | PASS |
| `check_openapi_contract` | PASS: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff | PASS |
| `check_integration_gate_openapi` | PASS: commands=84 productionEndpoint=false publicHost=false | PASS |
| `check_ci_test_discovery` | PASS: reference_suites=7 node_tests=8 modules=4 excluded=3; all 38 booking test modules reached | PASS: 18 negative controls |
| `check_ci_checker_wiring` | PASS: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 | PASS: 13 negative controls |

| Command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.179 s. |

The error-code map's CLASS_B=0 count concerns that map only; existing behavioral
undefined/characterization limits are preserved.

Rust commands used only the existing local toolchain and a copy of existing
`/home/box/.cargo/registry` bytes in `/tmp/kix-refund-cargo/registry`. No install,
download, network fallback or automatic retry:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-refund-cargo
export CARGO_TARGET_DIR=/tmp/kix-refund-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version` | PASS: cargo 1.98.1 (797e8a9bc 2026-08-05). |
| `rustc --version` | PASS: rustc 1.98.1 (48a229cea 2026-09-01). |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101: no matching cached `bcs`, required by workspace `kix-bcs1`; tests did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cached `bcs`; lint did not execute. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101: same missing cached `bcs`; tests did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101: same missing cached `bcs`; lint did not execute. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |

### Reproduce the partial socket-free discovery

`/tmp/kix-refund-offline.py` uses the predecessor's selection pattern:

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

Actual invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="/tmp/kix-refund-no-sockets:$PWD/reference/booking_resale_admission:$PWD" \
python3 /tmp/kix-refund-offline.py
```

Full HTTP coverage was not attempted because network actions are forbidden.
Exactly one discovered test is excluded; no other test is removed. Some unchanged
importability probes construct their own child environment and are outside the
guard's subprocess claim. Full unchanged HTTP coverage remains a delivery gate.

## Changed paths and preservation

Complete changed-path list (12):

- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_fixture.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_refund_controls.py`
- `reference/booking_resale_admission/test_ticket_settlement_controls.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_refund_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_refund_partial.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_refund_full.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_refund_replay.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-03-plan-plan-local-ticket-refund-controls/README.md`

Locked blobs match before and after work:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The preservation script hashes file bytes as Git blobs and compares against HEAD
for all historical reference files, both kernel locks, `.aiops/`, `docs/tasks/`,
contracts, workflows and the complete settlement suite: 172 protected blobs.
Historical `reference/v0.3-rc1` tree remains
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; all its working bytes match HEAD.
All 34 preexisting booking fixtures match HEAD. The exact 12-path change allowlist
excludes all other tracked/untracked outputs. No transient protected-file
mutation, CI edit, branch change or runtime activation was performed.

## Limitations, deviations and delivery gates

Class A: exercised operations match unchanged contracts and direct controls.
No explicit contract violation found. Class B: partial burden remains UNDEFINED;
full-gross fixture reclassification is not legal liability determination.
Repeated accepted source under a new key retains an economically inert accepted
journal entry. No new semantics assigned to these existing characterizations.
Process-local retained refusals are not journal durability. Existing unsynchronized
ticket views, clock-skew partial effects and lack of cross-machine rollback remain.

Product policy remains UNDETERMINED — Astra/User. Legal refund liability remains
UNDETERMINED — User/legal through I10. Synthetic fixture amounts are not defaults.
No hardware, money, paid service, secret, credential, public endpoint, real
PG/bank/KYC call, Sui testnet/mainnet, storage engine, coin/TIX module, production
runtime, new protocol command or consequential scope expansion was needed.
No implementation STOP dependency arose and no DECISION_REQUIRED file was needed.

Deviations: network prohibition overrides AGENTS.md §1 fetch; no task issue/doc
exists or was created. Existing dynamic CLI schema coverage required no edit to
`test_ticket_operations_cli.py`. Full discovery uses the explicit single-test
socket-free exclusion, and offline Rust test/Clippy prerequisites are unavailable.
The initial new-test defects and corrections are recorded above. No design scope
change was made.

Local results do not claim production safety/readiness, distributed fencing,
durability, bank exactly-once, chain finality, legal compliance, actual customer
credit or external refund closure. Move/localnet/ZK, unrelated reference suites,
full HTTP and Rust tests/Clippy were not successfully run or claimed. These are
source-informed builder checks, not non-author review or full repository CI.

The patch is uncommitted by instruction. Observed implementation HEAD remains
`a02b62c5314ad40f0c0afc3459cfe68ddc36ccbd`, which does not contain these changes.
The exact final task head will be assigned by the supervisor and is not available.
No commit, push, PR, issue, comment, ASTRA marker or merge was created.

| Delivery gate | Run ID / status / conclusion |
|---|---|
| A2 non-author exact-head review | Pending supervisor delivery; builder is author |
| Exact-final-head KTX kernel verification | Unavailable / pending / not claimed |
| Exact-final-head KIX protocol verification | Unavailable / pending / not claimed |
| Merge SHA / merge locked blobs / post-merge main CI | Not applicable: not merged |

Supervisor follow-up: commit the final patch, obtain A2 non-author exact-head
review, run unchanged full HTTP and Rust coverage with prerequisites, and require
both exact-final-head workflows completed/success. Ready transition and merge
remain separate human authorizations. Builder READY means local implementation
handoff; it does not propose merge.
