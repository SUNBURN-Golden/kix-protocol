# Local settlement fact inputs — builder evidence

Node: `plan-local-settlement-fact-inputs`. Task input: supplied user node/design;
no issue or task document exists. Non-ASTRA builder session; no publication.

Cached origin/main and initial branch HEAD: `e44957789b04732c4efe222355c8d080817f2505`.
Branch: `agent/kix-plan-local-settlement-fact-inputs`. Clean starting worktree.
Fetch omitted under the supervisor no-network instruction; remote freshness is
unverified. No rebase or base change. Implementation/final committed head and
KTX/KIX run IDs: unavailable until supervisor publication. No merge performed.

## Coverage inventory (recorded before adding tests)

| Requirement | Existing evidence | Classification / gap |
|---|---|---|
| Statement components, phases, binding, replay and retained errors | `reference/settlement_f01_f03/test_statement_adapter.py`: `test_malformed_components_preserve_direct_errors_and_rejection_keys`, `test_duplicate_movement_and_conflicting_binding_match_direct_fsm`, `test_illegal_unknown_and_terminal_phase_errors_are_unchanged`, `test_replay_fetches_each_time_returns_first_snapshot_after_later_changes` | Sufficient adapter/FSM coverage; partial desk coverage |
| Cancellation identity, amounts, phases, retained errors | `reference/settlement_f01_f03/test_cancel_acceptance_adapter.py`: `test_source_binding_repeat_and_conflict_match_direct`, `test_economic_rejections_and_retained_keys_remain_in_fsm`, `test_phase_and_identifier_errors_match_direct` | Sufficient adapter/FSM coverage; partial desk coverage |
| Recorded statements/distribution | `reference/booking_resale_admission/test_ticket_statement_distribution.py`: per-step graph, file/stdin, source isolation and first-receipt replay tests | Sufficient existing recorded path; direct observation absent |
| Refund binding/recorded cancellation | `reference/booking_resale_admission/test_ticket_refund_controls.py`: direct adapter/FSM controls, partial/full/replay transcripts, strict inputs | Sufficient existing recorded path; direct acceptance absent |
| Session signatures/one-call forwarding and terminal controls | `test_ticket_settlement_controls.py`, `test_ticket_settlement_exceptions.py` | Partial: extend matrices for new selectors |
| Request-time facts with empty/omitted recordings; cross-path replay/conflicts; structural rejection before delegation; no automatic effects | No existing request-time methods or transcript | Not covered: focused session and CLI evidence required |

## Preservation before editing

Locked blobs match required values: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
and `b607996c83a119c349f1cc90469ac1ba82764e20`.
`reference/v0.3-rc1` HEAD tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
A SHA-256 byte manifest of both locks and all files under that tree was captured
in `/tmp/kix-facts-protected.json` before implementation.

## Delivered acceptance evidence

All comparisons are source-informed composition evidence against unchanged public
FSMs, not clean-room verification. Counts below overlap and must not be summed.

| Requirement / documented gap | Evidence added or extended |
|---|---|
| Complete request-time fields without startup sources | `test_ticket_settlement_fact_inputs.py::TicketSettlementFactInputsTests.test_empty_and_omitted_sources_complete_explicit_journey`: version-1 anchor setup, empty arrays and omitted optional sources; explicit commit/later statement/distribution/refund/acceptance; public claim arithmetic and in-memory journal restore equality |
| Every receipt/error and graph state/journal matches direct FSM | `FactInputEvidence.step` separately calls session API, JSONL dispatcher and independently constructed public FSM controls; compares complete results and all four machines' canonical state, state digest and exported journal after each request |
| Cross-path replay, changed body/settlement/operation and movement/source identity | `test_recorded_direct_replay_both_directions_and_identity_conflicts`: both first-path directions, replay after later distribution/acceptance, first snapshot unchanged, changed recorded/direct bodies, fresh-key binding conflicts and same identity on a separate settlement; recorded requests fetch once each, direct requests never fetch |
| Invalid components / refusals / phase advancement | `test_invalid_components_retain_original_refusals`, `test_unknown_and_pre_capture_phases_match_and_retain_keys`, boundary transcript: booleans, negative/out-of-range amounts, component mismatch, invalid movement ID/reasons, unknown claims, pre-commit statement, absent/excess refund and receivable overflow; refusal remains after later legal progress; corrected requests need fresh keys |
| Structural rejection before delegation, key remains free | `test_structural_rejections_do_not_delegate_or_bind_keys`: missing every required field (including explicit null adjustment reason), extras, wrong containers, duplicate fields, malformed/nonfinite JSON; delegation spy untouched, state/journal unchanged, corrected request accepted with original key |
| No implicit effects, false flags | `FactInputEvidence.step` checks exact one-call forwarding on success/error, source-call histories unchanged for direct requests, ticket graphs unchanged; forbids unsolicited distribution/refund binding/commit/reconcile/ticket mutations/clocks on observation. Journey checks no auto distribution or refund completion and false production flags even after full synthetic acceptance. No retry/fallback/cache added |
| Exact signatures, object/exception identity and terminal phases | Extended existing `test_ticket_settlement_controls.py::test_fsm_methods_forward_once_with_exact_objects_receipts_and_errors` and `test_ticket_settlement_exceptions.py::test_pre_capture_and_terminal_parity` matrices for both methods; obsolete unsupported selectors replaced/removed |
| File/stdin output and exits 0/1/2 | `test_ticket_settlement_fact_inputs_cli.py`: both fixture transcripts in file and stdin modes, with empty and omitted optional sources; in-process stream final graph parity; complete per-line outputs equal direct controls; structural errors stop after prior success, domain errors allow subsequent explicit lines |

Journey arithmetic is synthetic: gross 10001; commit
`6000 = 5500 + 200 + 100 + 100 + 100`; later statement
`4001 = 3801 + 200`. Distribution requires caller order `platform, organizer`.
A bound refund of 4000 and synthetic acceptance of 1000 leave cash 9301,
refund outstanding 3000 and PG adjustment outstanding 1000. Full synthetic
acceptance still leaves external-return/right-cancellation/bank/funds/durability
flags false. These values are examples, not adopted policy.

## Actual commands and results

Read `README.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/status/BASELINES.md`,
`docs/decisions/AUTHORITY_MODEL_1.md`, `AGENTS.md`, control-plane pointer/pin,
`docs/decisions/PROGRAM_DECISIONS_20260928.md`, the settlement contract, existing
coverage and both `.github/workflows/ktx-kernel.yml` / `protocol.yml` locally.
The supplied user node/design is the task input; no task document was created.

Python verification used this environment:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-facts-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-facts-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

This guards the test process and inherited CLI child environments. Unchanged
import-only probes that replace their child environment are outside that child
guard claim. No network action was permitted by guarded runs. No long job was
launched as a background shell job or service.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; expected branch; both refs equal `e44957789b04732c4efe222355c8d080817f2505`. Cached ref only, no fetch under no-network instruction. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`; `git ls-tree HEAD reference/v0.3-rc1` | Required lock hashes and historical tree match before edits. |
| `python3 -m unittest test_ticket_settlement_fact_inputs test_ticket_settlement_fact_inputs_cli` (first run) | Exit 1: two import errors before execution because the new test did not import the existing sibling-path bootstrap first. Fixed test import order. |
| Same command (second run) | PASS: 8 tests, 10.583 s. |
| Same command (after extended cross-path identity/source conflict evidence) | PASS: 8 tests, 8.416 s. |
| `python3 -m unittest test_ticket_settlement_controls test_ticket_statement_distribution test_ticket_refund_controls test_ticket_settlement_exceptions` | PASS: 29 tests, 29.690 s. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 2.577 s. |
| `python3 /tmp/kix-facts-offline.py` (first attempt) | Exit 1 during collection: duplicate-name module path collision (`test_contract_error_codes` from sibling settlement suite). Corrected temporary runner to prepend booking/resale directory exactly as the predecessor recipe does; no repository change needed. |
| Same command (corrected predecessor selection below) | PASS: 717 tests, 73.978 s; exactly one unchanged loopback HTTP test excluded, no duplicate test IDs. Partial socket-free discovery only. |
| `python3 /tmp/kix-facts-checks.py` | PASS: all 19 commands below executed sequentially, exit 0; actual stdout/stderr captured in `/tmp/kix-facts-checks.json`. |
| `python3 /tmp/kix-facts-rust.py` | Exit 1: toolchain versions/format pass; four offline test/Clippy commands unavailable due missing cached `bcs`, each exit 101 before execution; `/tmp/kix-facts-rust.json`. No download or retry fallback. |
| `python3 /tmp/kix-facts-preservation.py` | PASS: 110 initial byte-manifest files; 240 protected/existing-fixture Git blobs unchanged; exactly 13 allowed changed paths; required locks/refs/Python AST/JSON/JSONL/whitespace valid. |
| `git diff --check` | PASS (exit 0). |

The checker runner executes each command below, without shell/network calls:

| Command | Actual result |
|---|---|
| `python3 -m unittest integration_gate.test_offline_limits` | PASS (exit 0): Ran 9 tests in 0.244s; OK |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0): architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0): Ran 7 tests in 0.337s; OK |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=348 indexed=313 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | PASS (exit 0): settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | PASS (exit 0): bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (50 negative controls) |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3; all 51 booking/resale test modules reached |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |

The contract-error map's CLASS_B=0/CLASS_C=0 concerns that map; it does not
resolve unknown product policy or characterize every possible behavior.

### Reproduce the socket-free selection

Save as `/tmp/kix-facts-offline.py`, then run with the Python environment above:

```python
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path("reference/booking_resale_admission").resolve()))

excluded = 'test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit'
suite = unittest.defaultTestLoader.discover('reference/booking_resale_admission', top_level_dir='reference/booking_resale_admission')
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item

tests = list(flatten(suite))
assert sum(t.id() == excluded for t in tests) == 1
assert len({t.id() for t in tests}) == len(tests), 'duplicate test discovery'
print('Explicit single HTTP exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(t for t in tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

This is the predecessor validation recipe's single exclusion:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
Full unfiltered BRA discovery and `integration_gate.test_http_gate` are not
claimed. They remain unchanged for normal CI; the exclusion honors the
supervisor's no-network boundary.

### Offline Rust environment

The foreground runner copied only provisioned `/home/box/.cargo/registry` into
`/tmp/kix-facts-cargo/registry` and used:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-facts-cargo
export CARGO_TARGET_DIR=/tmp/kix-facts-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version` | PASS (exit 0): cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `rustc --version` | PASS (exit 0): rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE (exit 101): no matching cached package `bcs`, required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE (exit 101): no matching cached package `bcs`, required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE (exit 101): no matching cached package `bcs`, required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE (exit 101): no matching cached package `bcs`, required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0). |

No Rust source changed. These unavailable prerequisites are not green Rust test
or Clippy results. Required CI needs provisioned dependencies.

## Changed paths and preservation

Complete changed-path list (13):

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_fact_inputs_boundaries.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_fact_inputs_journey.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_fact_inputs_session.json`
- `reference/booking_resale_admission/test_ticket_refund_controls.py`
- `reference/booking_resale_admission/test_ticket_settlement_controls.py`
- `reference/booking_resale_admission/test_ticket_settlement_exceptions.py`
- `reference/booking_resale_admission/test_ticket_settlement_fact_inputs.py`
- `reference/booking_resale_admission/test_ticket_settlement_fact_inputs_cli.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/ticket_operations_session.py`
- `validation/2026-11-04-plan-local-settlement-fact-inputs/README.md`

The preservation helper compares actual bytes with the initial manifest and with
`git show HEAD:<path>`, using NUL-delimited tracked paths. Its 240-blob scope
includes both kernel locks, `reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**`,
contracts, workflows, the entire settlement reference suite and all pre-existing
booking/resale fixtures. It checks the exact changed-path allowlist, current refs,
Python ASTs, fixture JSON/JSONL and whitespace, without modifying protected files.
Both locked blobs match before/after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

No commit, push, PR, issue, comment, tag/ref change, settings change or merge was
performed. No `.aiops/`, task document, contract, adapter, FSM/arithmetic,
protocol/catalogue/SDK, production runtime or CI changes were made. The
historical tree remains `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Deviations, limitations and outstanding gates

- Added one `docs/README.md` index link beyond the planned file list because
  `scripts/check_docs_index.py` requires every new validation README to be indexed.
  This is a usage/evidence pointer, with no scope or policy change.
- Fetch omitted under the explicit supervisor no-network instruction; cached
  origin/main equals the starting task head, but remote freshness is unverified.
- No task issue/document exists; used the supplied immutable user node/design.
- Local verification used the planned single HTTP exclusion. Offline Rust
  tests/Clippy lack cached `bcs`; no dependency installation or network fallback.
- Corrected two verification setup mistakes (test bootstrap import and temporary
  discovery runner path), then reran the affected commands successfully.

No explicit contract violation was found in the exercised paths. No new domain
semantics were adopted. Existing fresh-key repeated-fact journaling remains an
observed FSM characterization, not a new contract. Rejection keys live in the
current process and are absent from canonical state/exported accepted journals;
retention evidence therefore uses behavioral probes after later state changes,
not only snapshot equality. In-memory restore equality does not imply durable
persistence or external replay authorization.

Distribution priorities/refund burden remain **UNDETERMINED — Astra/User**;
legal/accounting effects remain **UNDETERMINED — User/designated advisers**.
No actual bank/PG/KYC, funds, public endpoint, Sui execution, production runtime,
replication/consensus/storage engine, secret or paid service was used. No bank
exactly-once, distributed fencing, chain finality, legal/accounting compliance,
production durability or production readiness claim follows from these tests.

| Delivery gate | Actual state |
|---|---|
| Initial / cached origin/main / unchanged branch HEAD | `e44957789b04732c4efe222355c8d080817f2505` |
| Implementation / final task commit SHA | Not created: worktree-only builder; supervisor owns commit/publication |
| Non-author exact-head A2 review | Pending after supervisor establishes final head; builder self-check is not that review |
| Exact-head KTX kernel verification run ID/status/conclusion | Unverified; not inspected or launched in this no-network/no-publication session |
| Exact-head KIX protocol verification run ID/status/conclusion | Unverified; not inspected or launched in this no-network/no-publication session |
| Merge SHA / post-merge locked blobs / main push CI | Not applicable: no merge authorized or performed |

Builder implementation is ready for supervisor handoff with the stated local
verification limits. It is not merge-ready. Supervisor follow-up: commit the
reviewable patch, obtain non-author exact-head review and both required exact-head
CI successes; any merge remains User-only authorization.
