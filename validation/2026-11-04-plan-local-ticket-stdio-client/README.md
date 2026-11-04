# plan-local-ticket-stdio-client — builder evidence

Task input: the supplied immutable user node/design; no issue or docs/tasks task
exists. This is not ASTRA program mode. Branch:
`agent/kix-plan-local-ticket-stdio-client`.
Initial HEAD and cached origin/main: `4138625eb4504b98bc56745bb180299875528ce9`.
The supervisor's explicit no-network instruction overrides the normal fetch
step; remote freshness is unverified. No base/ref changes, commits or publication.

Implementation: explicit single-child blocking JSONL client; response flushing;
caller-configured example; no graph/contract/FSM/catalogue changes.

## Existing coverage inspected before adding tests

| Requirement | Initial classification and evidence | Gap addressed |
|---|---|---|
| Batch stdin/file parity, exits 0/1/2 | Sufficient: `test_ticket_operations_cli.TicketOperationsCliTests.test_three_transcripts_file_and_stdin_exact_session_results`, `test_booking_transcripts_file_and_stdin`, `test_bad_json_stops_and_structural_error_overrides_previous_refusal`; `test_ticket_settlement_fact_inputs_cli.TicketSettlementFactInputsCliTests.test_file_stdin_journeys_and_domain_continuation` | Rerun existing coverage; no duplicate batch suite |
| Live response before stdin EOF | Not covered: batch uses `subprocess.run(input=...)` | `test_buffered_child_reply_before_stdin_eof_and_response_derived_journey`, ordinary buffered child, deadline/event harness |
| Same graph, receipts/current views, explicit response-derived requests | Partially covered: `test_ticket_operations_session.py`, `test_ticket_settlement_fact_inputs.py` direct/FSM parity | Live listing/cancellation and settlement tests compare direct session calls; receipt IDs drive next requests, flags retained |
| Domain/source continuation and structural terminal replies | Partially covered: batch suites above and `test_booking_prerequisites_stop_without_binding_keys_or_undoing_prior_effects` | Live domain/source continuation, `FixtureError`, `BookingInputError`, null-selector startup error fencing |
| Quote envelope and startup quote options | Partially covered: `test_ticket_operations_quotes.py`, `test_booking_quote_preview.py` | Live quote payload plus recorded/calculated fixture journeys compared to direct session/adapter calls |
| Transport uncertainty, no resend/replacement | Not covered | Real controlled workers: malformed/truncated/UTF-8/JSON/envelope/correlation replies and exit after submission; one received line/one launch; injected short write, broken pipe, partial interrupted read |
| Single outstanding request and resource cleanup | Not covered | Concurrent/reentrant rejection before write, context exception, repeated close, terminate/kill deadlines and reaping |
| Import and runnable example | Partially covered: existing desk import probe | Client import has no launch/output; example matches direct receipts/views and stops on source error |

New tests are source-informed composition evidence, not clean-room independent
review. No product policy is adopted.

## Actual verification

Results are recorded below after executing the commands. Test harness deadlines
are safeguards, not product response-timeout policy. No background jobs, polling,
sockets, dependency downloads or network actions are authorized.

Python runs use:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-stdio-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

The temporary `sitecustomize.py` installs `sys.addaudithook` rejecting
`socket.__new__`, `socket.connect`, `socket.bind`, `socket.getaddrinfo`, following
the predecessor's guard. Parent and inherited child environments use the guard;
existing import probes that replace their child environment are outside that
child-guard claim. Socket-free discovery uses the predecessor's exact single
exclusion, recorded with results below. Normal CI selection is unchanged.

### Commands and actual results

The temporary foreground runner `/tmp/kix-stdio-run.py` ran phases `narrow`,
`affected`, `broad`, `checks`, `rust` in that order, then reran
`narrow`, `affected`, `broad`, `checks` after the final refinement below. It executed each underlying
command below sequentially with captured stdout/stderr, saved in temporary
`/tmp/kix-stdio-<phase>.json` files. All Python phases exited 0; the Rust runner
exited 1 because the four dependency-resolution attempts exited 101. These
unavailable prerequisites were not retried with downloads enabled.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initial clean worktree, expected branch; both cached refs `4138625eb4504b98bc56745bb180299875528ce9`; no fetch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`; `git ls-tree HEAD reference/v0.3-rc1` | Required lock hashes match before editing; historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `python3 --version` | Python 3.13.5 (local provisioned interpreter; hosted workflow specifies 3.12). |
| `python3 -m unittest test_ticket_operations_client` (initial) | Exit 1: 12 tests, 6 failures and 2 errors in 32.105 s. Corrected nonexistent `view_listing` selector, controlled-worker stdout descriptor closure, and successful transcript exit expectations. |
| `python3 -m unittest test_ticket_operations_client` (corrected) | PASS: 12 tests in 2.313 s; exit 0. Extended reentrant/termination coverage afterward. |
| `python3 -m unittest test_ticket_operations_client` (extended coverage before final refinement) | PASS: 13 tests in 2.582 s; exit 0. |
| `python3 -m unittest test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes test_booking_quote_preview test_ticket_settlement_fact_inputs test_ticket_settlement_fact_inputs_cli` | PASS: 59 tests in 14.001 s; exit 0. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests in 1.689 s; exit 0. |
| `python3 /tmp/kix-stdio-offline.py` | PASS: 742 tests in 66.734 s; exit 0. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests in 0.193 s; exit 0. |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0): architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests in 0.167 s; exit 0. |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=350 indexed=315 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0): ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | PASS (exit 0): bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (50 negative controls) |
| `python3 scripts/check_settlement_evidence_map.py` | PASS (exit 0): settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (33 negative controls) |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0): self-test: pass |
| `cargo --version` | PASS (exit 0): cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `rustc --version` | PASS (exit 0): rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE (exit 101): cached `bcs` missing for workspace `kix-bcs1`; test/lint did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE (exit 101): cached `bcs` missing for workspace `kix-bcs1`; test/lint did not execute. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE (exit 101): cached `bcs` missing for workspace `kix-bcs1`; test/lint did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE (exit 101): cached `bcs` missing for workspace `kix-bcs1`; test/lint did not execute. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0): completed |
| `python3 /tmp/kix-stdio-preserve.py` | PASS (exit 0): 1,332 unchanged tracked blobs outside seven allowed paths, required locks match, historical bytes preserved, refs unchanged, changed Python ASTs valid, `git diff --check` passed. |
| `git diff --check` (also invoked by preservation helper) | PASS (exit 0). |

### Final refinement verification

Final review made transport uncertainty independently terminal inside the client,
and made the startup test deterministic about delivery versus a real broken-pipe
race. A controlled real worker delivers the existing null-selector startup
error after reading one request; the real invalid-fixture desk must either return
the same error or raise uncertainty caused by a broken pipe. Neither permits
another write. These are task-defined transport semantics, not a new protocol.

The following final-code checks were rerun after those changes:

| Command | Actual result |
|---|---|
| `python3 -m unittest test_ticket_operations_client` | PASS: 13 tests in 2.349 s; exit 0. |
| `python3 -m unittest test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes test_booking_quote_preview test_ticket_settlement_fact_inputs test_ticket_settlement_fact_inputs_cli` | PASS: 59 tests in 13.676 s; exit 0. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests in 1.731 s; exit 0. |
| `python3 /tmp/kix-stdio-offline.py` | PASS: 742 tests in 65.905 s; exit 0. |
| All 19 commands in the checker phase listed above, including both normal and `--self-test` forms | PASS again: every command exit 0; 9 offline-limit tests and 7 architecture tests passed. |
| `python3 /tmp/kix-stdio-preserve.py`; `python3 scripts/check_docs_index.py` after completing this report | PASS: all 1,332 protected/non-task tracked blobs and both locks unchanged; exact seven changed paths; refs and Python ASTs valid; whitespace and index valid. |

Rust was not retried: no Rust source, toolchain or dependency-cache inputs changed.
Its four unavailable results above still require provisioned CI dependencies.

The 742-test booking/resale discovery is **partial socket-free selection**,
excluding exactly the predecessor's
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
Unfiltered discovery and `integration_gate.test_http_gate` remain for normal CI;
neither is claimed here. Discovery asserts that this exclusion occurs once and
that test IDs are unique. Its temporary runner is reproduced below:

```python
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path('reference/booking_resale_admission').resolve()))
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

The Rust environment copied only the provisioned
`/home/box/.cargo/registry` into `/tmp/kix-stdio-cargo/registry` and used:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-stdio-cargo
export CARGO_TARGET_DIR=/tmp/kix-stdio-target
export CARGO_NET_OFFLINE=true
```

No Rust source changed. Missing cached `bcs` is not a green Rust test or Clippy
result. The contract-error checker's CLASS_B=0/CLASS_C=0 concerns that evidence
map only and does not resolve open product policy.

The initial inspection also attempted to read `.github/workflows/verify.yml`,
which does not exist (read command exit 1); subsequently inspected the actual
`.github/workflows/protocol.yml` and `ktx-kernel.yml`. No CI changes were made.

## Preservation and changed paths

Both locked blobs matched before and after edits:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The byte-level preservation helper hashes every tracked blob outside the seven
allowed paths against HEAD (1,332 matches), including both locks, historical
reference files, `.aiops/**`, `docs/tasks/**`, contracts, workflows, fixtures and
all other existing tests/sources. Initial tracked worktree was clean. No protected
file was transiently mutated. The final changed-path allowlist and refs match.

Protected historical tree at HEAD:
`reference/v0.3-rc1`: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

Complete intended changed-path list:

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/ticket_operations_client.py`
- `reference/booking_resale_admission/test_ticket_operations_client.py`
- `reference/booking_resale_admission/example_ticket_operations_client.py`
- `validation/2026-11-04-plan-local-ticket-stdio-client/README.md`

## Deviations and outstanding gates

- Existing resale operation is `view`, not the design's proposed `view_listing`;
  the example and tests use the existing selector. No new command was added.
- Fetch omitted under the supervisor's no-network rule; no task issue/doc exists.
- Local Python is 3.13.5 rather than hosted CI's 3.12. Offline Rust tests/Clippy
  were unavailable due missing cached `bcs`; no dependency downloads attempted.
- Initial narrow-suite selector/worker/exit-expectation mistakes were corrected
  and rerun successfully, as recorded above.
- Implementation/final commit SHA: not created; supervisor owns git/GitHub.
- Non-author exact-head A2 review: pending after supervisor establishes head.
- KTX kernel verification run ID/status/conclusion: unverified, not launched.
- KIX protocol verification run ID/status/conclusion: unverified, not launched.
- Merge SHA, final-merge locked blobs and post-merge main CI: not applicable.

No explicit contract violation found in exercised paths. Product timing,
authentication, pricing, distribution and refund policy remain
**UNDETERMINED — Astra/User**. No business semantics were invented. Blocking
requests have no automatic timeout, and accepted work cannot be undone by
cleanup. Startup error delivery can race process exit; broken submission still
means local uncertainty. No production durability, distributed fencing, bank
exactly-once, chain finality, legal compliance or production readiness is claimed.
No actual providers/funds/KYC, public endpoint, Sui execution, storage/replication
engine, secret, paid service or production runtime was used.

Builder handoff is distinct from merge readiness. Supervisor must establish the
final head, obtain non-author review and both exact-head CI successes; merge
remains subject to explicit User authorization.
