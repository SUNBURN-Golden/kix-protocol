# Local ticket settlement inputs

Node `plan-local-ticket-settlement-inputs`; task input is the supervisor-supplied
node specification and design in this session. No issue or `docs/tasks/` document
exists. Not ASTRA program mode. Branch
`agent/kix-plan-local-ticket-settlement-inputs`.

Initial HEAD and cached `origin/main` both:
`c641a7437f8dcf9094740bd0a4024ea1d2b89317`. No local base delta. The supervisor's
network prohibition overrides the initial fetch requirement; remote freshness is
unverified. No commits or GitHub actions are authorized.

Before edits, locked kernel blobs match `69564b166f0c27f9af5d8422f0a466b18d74c20f`
and `b607996c83a119c349f1cc90469ac1ba82764e20`. Protected historical tree
`reference/v0.3-rc1`: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Pre-change coverage inventory

Recorded before adding tests. Test paths below are relative to `reference/`.

| Requirement | Existing coverage | Classification / gap |
|---|---|---|
| Initiation, replay, changed-body conflicts, historical first receipts | `settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.test_same_key_replays_and_a_different_body_is_rejected`; `test_settlement_rejection_atomicity.py` initiation cases | Sufficient FSM semantics; partial adapter composition |
| Shared graph and explicit booking/resale binding, authorization, capture, commit | `booking_resale_admission/test_ticket_settlement_controls.py::TicketSettlementControlsTests.test_transcripts_compare_every_step_and_preserve_refused_keys`; `test_ticket_operations_session.py` | Partial: manual initiation only |
| Recorded commit/later observation and separate distribution | `booking_resale_admission/test_ticket_statement_distribution.py::TicketStatementDistributionTests.test_file_stdin_and_api_journeys_match_direct_fsm_after_every_step` | Sufficient existing controls; partial source-initiation journey |
| Source validation, single read, exception boundary, zero target calls and reusable key | `booking_resale_admission/test_issued_ticket_adapter.py` and statement adapter tests provide patterns | Not covered for settlement inputs |
| Missing/unconfirmed bookings, missing listings, mismatched IDs, malformed money/currency | Existing FSM view and input tests | Not covered for new extraction boundary |
| Manual/source equivalence, caller identity/policy passthrough and retained target refusals | Settlement rejection tests and shared direct-forward tests | Partial: new adapter path absent |
| API, file/stdin output and exit parity, strict request fields | `booking_resale_admission/test_ticket_operations_cli.py`, `test_ticket_settlement_controls.py` | Partial: new selectors absent |
| No automatic ticket/payment/settlement effects; mock provenance/false flags | Shared snapshot and flag helpers in existing desk/control tests | Partial: extraction path absent |
| Discovery, architecture, OpenAPI/document consistency | Existing CI scripts and workflows | Sufficient mechanisms; run against changed paths |

Snapshots omit retained refusal bookkeeping. Explicit same-key repair/replay
probes supplement state/digest/journal comparisons. New tests are source-informed
composition evidence, not clean-room or independent verification.

## Implementation and acceptance evidence

`SettlementInputAdapter` reads one selected public booking/resale view, checks
source identity and required fields, then invokes unchanged `initiate` once.
The shared wrapper injects its actual reservation/resale/settlement machines;
standalone `TicketSettlementSession` source arguments are optional. Construction
reads no inputs. The two selectors require all caller target identities, debtor
and complete policy. Source failures are local exceptions, outside target key
retention; target receipt/exception objects pass through unchanged. No policy,
fee, payee, identity or lifecycle eligibility is inferred.

| New test path (under `reference/booking_resale_admission/`) | Gap addressed |
|---|---|
| `test_settlement_input_adapter.py` | Exactly one selected view and one target call; unrelated source untouched; opaque caller inputs/result identity; no construction calls; valid amount boundaries; bad selectors/IDs/unavailable sources; wrong containers and missing fields; null, boolean, float, string and out-of-range amounts; malformed currency/order/source identities; immediate source exceptions/timeouts; explicit repair; target domain/local/programming exception identity outside source handling. |
| `test_ticket_settlement_inputs.py` | Both selectors through importable Python methods and strict dispatcher, compared after every transcript step with a separate raw-FSM graph: receipts/errors, canonical states, digests and journals; one selected read even on replay; real unconfirmed booking refusal followed by explicit confirmation and unpaid initiation with the same key; graph/key preservation on malformed/faulting sources; manual↔source equivalence, changed source amount/caller identities/policy conflicts; source alias/kind equality; required signatures and exact forwarding. |
| `test_ticket_settlement_inputs_cli.py` | Every transcript through executable file and stdin, matching the same raw controls and Python API; exits 0/1/2; missing/extra fields including gross/currency overrides, wrong containers/selectors, duplicate keys, nonfinite/overflow JSON; stopping after prior accepted input; local error continuation and absent sources without breaking manual initiation; actual unconfirmed setup file/stdin refusal. |

Existing `test_ticket_settlement_controls.py` now includes the two selectors in
its inventory and strict request matrix, distinguishing adapter methods from
direct forwards. All existing manual settlement tests remain in place. No test
selection, FSM, contract, OpenAPI, SDK or CI file changed.

All successful operations reuse existing settlement/booking/resale/admission flag
assertions. Initiation leaves the other three machines byte-equivalent in public
canonical state, digest and accepted journal, remains `INITIATED`, has no mock
authorization and no claim, and does not fetch offer/payment/presentation
recordings. Both successful journeys explicitly request binding, authorization,
capture, recorded commit, distribution, later statement observation and a second
distribution. Ticket issuance/transfer is separately requested. First initiation
receipts still report `INITIATED` after later progress.

The new fixture retains all existing anchor setup plus optional synthetic
statements. `booking` and `resale` transcripts each contain 15 requests and exit
0. Booking first cash is 5500, later cash 3801; explicitly distributed cash totals
9301, with 700 remaining non-cash accounting. Resale first/later cash is 4000 each,
and explicit distribution totals 8000. Caller policy has a synthetic 500 bps fee;
it is not derived from the listing's organizer/platform allocations. `boundaries`
contains 12 requests and exits 1: absent booking/listing, same-key repair, replay,
changed trade conflict, retained `POLICY_FIELDS` refusal and changed-body conflict.

Runnable transcripts and Python example are in the
[shared desk guide](../../reference/booking_resale_admission/README.md#initiating-settlement-from-local-ticket-records).
File/stdin outputs were also compared byte-for-byte in a separate foreground
runner. Every process starts with a fresh fixture graph. No operation is retried
automatically.

## Commands actually run and results

Commands ran from repository root in the foreground using installed/cached
prerequisites. No Git or GitHub mutation, network request or installation ran.
Python verification used:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-inputs-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-inputs-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

This guards the Python runner and inherited CLI environments. Existing
importability probes that replace their child environment are outside that
subprocess guard claim. No socket action was permitted by guarded runs. Counts
below overlap and must not be summed.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean, expected branch; both refs `c641a7437f8dcf9094740bd0a4024ea1d2b89317`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`; `git ls-tree HEAD reference/v0.3-rc1` | Both required lock blobs and historical tree match before edits. |
| `python3 -m unittest test_settlement_input_adapter test_ticket_settlement_inputs test_ticket_settlement_inputs_cli` (first run) | 4 adapter tests passed; 2 module import errors: new session test needed existing `admission_fixture` sibling-path setup. Corrected imports; also avoided exposing an imported TestCase to duplicate discovery. |
| Same command (second run) | 12 tests, 4 errors: test incorrectly asserted a nonexistent `mock_captured` public field. Removed that assertion; retained phase, authorization, claim and full-state assertions. |
| Same command (third run) | PASS: 12 tests, 2.649 s. |
| Same command (after explicit cross-source fingerprint/target-error evidence) | PASS: 13 tests, 1.877 s. |
| `python3 -m unittest test_ticket_settlement_controls test_ticket_statement_distribution test_ticket_operations_session test_ticket_operations_cli` | PASS: 43 tests, 7.414 s. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 1.882 s. |
| `python3 /tmp/kix-inputs-offline.py` (recipe below) | PASS: 676 tests, 119.531 s; exactly one unchanged HTTP test excluded; no duplicate test IDs. |
| `python3 /tmp/kix-inputs-checks.py` | PASS: sequential runner for the 19 commands detailed below; each exit 0, output captured in `/tmp/kix-inputs-checks.json`. |
| `python3 /tmp/kix-inputs-rust.py` | Exit 1: Rust tests/Clippy unavailable before execution; toolchain and format commands pass. Details below; output in `/tmp/kix-inputs-rust.json`. |
| `python3 /tmp/kix-inputs-transcripts.py` | PASS: invokes each new JSONL file and stdin separately, compares stdout/stderr bytes and expected exits; booking 15 rows/exit 0, resale 15 rows/exit 0, boundaries 12 rows/exit 1. |
| `python3 /tmp/kix-inputs-preservation.py` | PASS: 173 protected blobs, all 51 existing booking fixtures byte-identical to HEAD; exactly 14 allowed changed paths; lock hashes/refs/AST/JSON/whitespace valid. |
| `git diff --check` | PASS. |

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. The checker
runner executes each of these commands sequentially with captured actual output:

| Command | Actual result |
|---|---|
| `python3 -m unittest integration_gate.test_offline_limits` | PASS (exit 0): 9 tests, 0.569 s, OK |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0): architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0): 7 tests, 0.464 s, OK |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | PASS (exit 0): settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | PASS (exit 0): bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (50 negative controls) |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=344 indexed=309 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0): 47 booking/resale modules reached; ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0): self-test: pass (18 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0): ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0): self-test: pass (13 negative controls) |

The error-code map's CLASS_B=0 concerns that map, not all undefined product
behavior or owner decisions.

### Reproduce socket-free booking/resale discovery

Save the following as `/tmp/kix-inputs-offline.py` and run with the environment
above. The excluded test is preserved for normal full-suite CI; exclusion is
solely the supervisor's no-network constraint and supplied predecessor recipe.

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
assert len({t.id() for t in tests}) == len(tests), 'duplicate test discovery'
print('Explicit single HTTP exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(t for t in tests if t.id() != excluded))
sys.exit(not result.wasSuccessful())
```

### Offline Rust checks

The foreground Rust runner copied the existing `/home/box/.cargo/registry` into
`/tmp/kix-inputs-cargo/registry`, without installing/downloading dependencies.
It ran commands below with:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-inputs-cargo
export CARGO_TARGET_DIR=/tmp/kix-inputs-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version` | PASS (exit 0): cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `rustc --version` | PASS (exit 0): rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE (exit 101): missing cached `bcs` required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE (exit 101): missing cached `bcs` required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE (exit 101): missing cached `bcs` required by workspace `kix-bcs1`; tests/lint did not execute. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0). |

No Rust source changed. These prerequisite failures are not passing test or
Clippy results. The supervisor must run normal required CI with prerequisites.

## Changed paths and preservation

Complete changed-path list (14):

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_booking.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_boundaries.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_resale.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json`
- `reference/booking_resale_admission/settlement_input_adapter.py`
- `reference/booking_resale_admission/test_settlement_input_adapter.py`
- `reference/booking_resale_admission/test_ticket_settlement_controls.py`
- `reference/booking_resale_admission/test_ticket_settlement_inputs.py`
- `reference/booking_resale_admission/test_ticket_settlement_inputs_cli.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/ticket_operations_session.py`
- `validation/2026-11-04-plan-local-ticket-settlement-inputs/README.md`

The preservation helper uses NUL-delimited Git paths and compares actual file
bytes against `git show HEAD:<path>` for both kernel locks, all historical
`reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`, contracts, workflows and the
entire settlement suite: 173 blobs. It separately checks all 51 pre-existing
booking fixtures. It validates changed Python ASTs, JSON/JSONL syntax, whitespace,
exact changed-path allowlist and unchanged refs. Both locked blobs match before
and after work:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

Historical tree remains `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. No protected
file was edited, including transiently. `/tmp` helpers/output are local verification
aids, not independent evidence. No source-informed test is labeled clean-room.

## Deviations, classifications and delivery gates

The only implementation-plan adjustment is fixture composition: shared booking
payment observation is setup-only in the existing repository. The runnable
booking journey retains that explicit setup payment and requests issuance later;
a separate actual session test proves confirmed/unpaid initiation without adding
a payment selector or changing the fixture schema. No consequential scope
expansion, owner-policy decision or new protocol command was needed. No explicit
contract violation was found.

The adapter establishes extraction requirements, not source eligibility or an
authorization/source-to-trade contract. Existing target fingerprints omit source
identity; tests characterize alias/kind and manual/source equivalence without
changing that behavior. No new contract-undefined FSM semantics were invented.
Product policy remains **UNDETERMINED — Astra/User**; legal debtor/accounting
remain **UNDETERMINED — User/legal/accounting**. Existing open contract items,
map classifications and capability grades remain unchanged.

Network/fetch and the single HTTP test were not run, per supervisor instruction.
Rust tests/Clippy were attempted offline and could not reach execution due to the
missing cache prerequisite. Full protocol CI, Move/localnet/ZK/SDK suites and
live provider/chain/funds behavior were not run or certified. No concurrency,
authentication, currentness, rollback, durable storage, bank exactly-once, legal
compliance or production readiness claim is made.

Implementation/final committed head has not been assigned: all changes are an
uncommitted worktree diff against `c641a7437f8dcf9094740bd0a4024ea1d2b89317`.
The supervisor owns commit/publication. Non-author A2 review at the eventual exact
head and completed/success of both KTX kernel verification and KIX protocol
verification remain required. Neither workflow was queried or run here; run IDs,
statuses and conclusions are unavailable. No PR or merge exists for this node;
merge SHA, merged-lock checks and post-merge main CI are not applicable. Builder
completion is not merge readiness or authorization. Follow-up belongs to the
supervisor: publish the final head, obtain review and run full required CI with
its normal HTTP coverage and Rust prerequisites.
