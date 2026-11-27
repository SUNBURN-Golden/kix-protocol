# Local admission request inputs

Task: `plan-local-admission-request-inputs`. The supplied node specification and
read-only design plan are the immutable task input; no issue or task file under
`docs/tasks/` exists for this node. This is not ASTRA program mode. The historical
Task 005 charter was read as context, not as this node's execution input.

Observed local `origin/main`, task base and initial HEAD:
`bbf55e532a12cc0741554a1f8734ecd981c07031`.
Branch: `agent/kix-plan-local-admission-request-inputs`; initially clean.
The supervisor prohibits network actions, so `git fetch origin main` was not
run; remote freshness is unknown. No base change was made. Implementation and
final task commit SHAs are not assigned: all delivery changes are uncommitted
for the supervisor. No merge or GitHub action was performed.

## Existing coverage mapping (before new tests)

Paths below are relative to `reference/booking_resale_admission/`.

| Requirement | Existing coverage classification | New input-surface gap |
|---|---|---|
| Separate authorize/consume, first receipts, one version increment | Sufficient lifecycle coverage: `test_admission_fsm.py::test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`; partial session coverage: `test_admission_session.py::test_actual_session_explicit_effects_first_receipt_and_current_views` | Request-input forwarding and replay on the new selectors |
| Expiry, transferred presentations, resale locks | Sufficient lifecycle coverage: `test_admission_fsm.py::test_expired_authorization_is_replaced_once`, `test_transfer_then_entry_rejects_both_presentations`, `test_listing_and_cancel_order_against_entry` | Unrecorded inputs through standalone and shared desks |
| Source bypass, unchanged values, exception/receipt identity | Partial: session `test_direct_delegation_preserves_return_and_exception_identity` and adapter `test_exact_forwarding_receipt_and_exception_identity_for_both_methods` | Exactly one FSM call, opaque input identity and zero presentation calls on both new methods |
| Rejected keys, stale version/holder, settlement flags | Sufficient FSM/adapter coverage: `test_presentation_adapter.py::test_stale_version_holder_and_conflicting_keys`, `test_rejected_key_stays_rejected_after_listing_cancelled`, `test_settlement_flags_are_still_checked_for_each_operation` | Direct-input retained errors/conflicts and explicit state changes |
| Strict JSON/schema and exits | Partial: `test_admission_cli.py::test_every_session_argument_is_required_and_unknown_input_stops_before_dispatch`, `test_malformed_lines_setup_and_paths_exit_two`; shared strict-boundary tests | New fields/selectors; domain errors remain FSM errors rather than adapter record errors |
| Empty startup recordings, file/stdin, shared graph | Not covered for new inputs; partial composition coverage in `test_ticket_operations_session.py::test_transcripts_session_and_cli_match_direct_graph_after_every_request` | Empty-recording fixtures, both executables and explicit selector-to-FSM control mappings |
| Class-B cross-clock behavior | Sufficient characterization: `test_admission_rejection_atomicity.py::test_char_authorize_clock_skew_window` | No new semantics or duplicate lifecycle test |

## Implementation and new evidence

The two session methods each return exactly one public FSM call. They forward
complete caller inputs unchanged, with no adapter fetch, cache, inference,
clock adjustment, view lookup or follow-up. Authorization and consumption stay
separate. The strict dispatcher returns `receipt` and retains the local selector
in `operation`. The shared CLI's existing admission routing needs no change.

`AdmissionRequestInputsTests` in `test_admission_session.py` covers opaque
forwarding/return/exception identity, zero source access, real-FSM refusal and
retained-key parity, every changed subject/body binding under an accepted key,
and recorded/direct replay in both orders. Existing adapter tests remain intact.

`AdmissionInputsDeskChecks` in `test_admission_cli.py`, inherited by both desks,
compares every result/error and all four machines' canonical state, digest and
journal with a separately constructed public-FSM graph. It asserts no extra
effect on replay/refusal, unchanged economic/ownership state on direct admission
calls, no clock changes, zero presentation fetches and exactly one consumption
journal entry per admission/reservation machine. It runs complete file/stdin
transcripts plus a success stream through both executables. Strict schema cases
cover every omitted argument/envelope field, extras (`presentation_id` and
`external_dependency` included), invalid shapes, duplicate keys and nonfinite
JSON before dispatch. Semantic refusals continue only on supplied lines; a
later structural failure stops and overrides exit 1 with exit 2.

The existing shared session/CLI/direct-graph comparison also includes the new
shared transcript. Standalone setup reuses both existing bound tickets; shared
setup adds that same second bound ticket to the existing graph. Both fixtures
have empty presentation recordings; the shared fixture has empty offers too.
The 15-line standalone and 19-line shared streams explicitly exercise replay,
refusals, expiry, resale locks/cancellation and ownership transfer without
credential refresh. These are source-informed boundary tests, not an independent
FSM implementation or proof of general cross-machine atomicity.

## Commands and actual results

All commands ran from repository root, with `PYTHONDONTWRITEBYTECODE=1`
for Python checks. The focused command additionally used
`PYTHONPATH="$PWD/reference/booking_resale_admission"`. Installed tooling:
Python 3.12.15, rustc/Cargo 1.98.1. Long jobs ran in the foreground; no shell
background jobs were launched. No dependency download was attempted.

| Command | Actual result |
|---|---|
| `python3.12 -m unittest test_admission_session test_admission_cli test_presentation_source test_presentation_adapter test_ticket_operations_session test_ticket_operations_cli` | First run: 81 tests, 2 failures in new transcript assertions. Corrected the synthetic resale payment reference (it reused ticket 2's primary payment reference) and the expected existing bound-source refusal precedence. Re-run: 81 tests OK, exit 0. FSMs unchanged. |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 698 tests OK, exit 0, including existing clock-skew characterization and all admission/shared suites |
| `python3.12 scripts/verify_runtime_architecture.py` | Architecture v5 + KTX-R1 dependency gate OK, exit 0 |
| `python3.12 scripts/test_runtime_architecture.py` | 7 tests OK, exit 0 |
| `python3.12 scripts/check_openapi_contract.py` and the same command with `--self-test` | Both exit 0; 84 existing commands and unchanged pin |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0; 84 commands, productionEndpoint/publicHost false |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | Both exit 0; scanned 346, indexed 311, allowlisted 35 |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; 7 reference suites, 8 Node tests, 4 modules, 3 historical exclusions |
| `python3.12 scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0; 35 checker scripts |
| `python3.12 scripts/check_bra_evidence_map.py` and `--self-test` | Both exit 0; 39 rows, 50 negative controls |
| `python3.12 scripts/check_contract_error_codes.py` and `--self-test` | Both exit 0; 199 covered rows |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Unavailable, exit 101 before compilation: missing cached crates.io `bcs`, resolved through workspace package `kix-bcs1` |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Unavailable, exit 101 before compilation: same missing `bcs` cache |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Pass, exit 0 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (startup); `git hash-object --no-filters` on the same paths (final) | Both required blobs match before and after |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs .aiops docs/tasks .github sdk docs/contracts` | Exit 0; protected and out-of-scope paths unchanged |
| `git ls-files --others --exclude-standard -- reference/v0.3-rc1 .aiops docs/tasks` | Exit 0, empty output |
| Historical reference raw-blob verification (Python command below) | 108 tracked files checked byte-for-byte against HEAD, all match, exit 0 |
| `git diff --check` | Pass, exit 0 |
| `git rev-parse HEAD`; `git rev-parse origin/main` | Both remain `bbf55e532a12cc0741554a1f8734ecd981c07031` |

The checker commands and their self-tests ran sequentially via a standard-library
`subprocess.run` driver; each return code was inspected. Rust commands used a
separate sequential driver with `CARGO_NET_OFFLINE=true`. The read-only historical
byte check actually run was:

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 - <<'CHECK'
import subprocess
from pathlib import Path
entries = subprocess.check_output(['git', 'ls-tree', '-r', '-z', 'HEAD', 'reference/v0.3-rc1']).split(b'\0')
count = 0
for entry in entries:
    if not entry:
        continue
    metadata, name = entry.split(b'\t', 1)
    mode, kind, expected = metadata.split()
    assert kind == b'blob', entry
    actual = subprocess.check_output(['git', 'hash-object', '--no-filters', '--', name.decode()]).strip()
    assert actual == expected, name
    count += 1
print(f'{count} historical reference files: raw Git blobs match HEAD')
CHECK
```

The mixin tests actually invoke both executable CLIs with `--requests PATH`
and `--requests -`, compare full output with direct-FSM outcomes, and check
exit 1 for the complete refusal transcripts, exit 0 for the success stream and
exit 2 for malformed streams. These executable results are not inferred from
in-process tests.

The applicable local protocol subset was selected after inspecting
`.github/workflows/protocol.yml` and `.github/workflows/ktx-kernel.yml`.
Full protocol, Move/ZK, SDK and unrelated reference suites were not run.
The Rust cache failure is environmental and does not certify those checks;
the supervisor must supply dependencies and run the normal exact-head gates.

## Protected bytes, limits and pending gates

Before edits both locked Git blobs matched:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Initial `reference/v0.3-rc1` tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
Final raw-blob and working-byte checks above passed. FSMs, contracts,
catalogue, SDK, program plan, task documents, CI and protected paths are outside
the patch.

No explicit contract violation was found. The existing Class-B clock-skew
characterization is retained: a delegated reservation authorization may remain
after a local-window rejection. No rollback or clock synchronization is added.
Fresh post-consumption refusals in the fully bound graph depend on existing
ownership/reservation check order: version 2 consumption is `STALE_VERSION`,
while version 1 reauthorization is `RIGHT_NOT_ACTIVE`. These match direct FSM
calls; the wrapper does not replace them with a preferred lifecycle error.

Product policy remains **UNDETERMINED — Astra/User**; legal effects remain
**UNDETERMINED — User/legal**. P03 remains design-stage. No real funds, external
PG/bank/KYC, external network, Sui testnet/mainnet, hardware, credential issuance,
persistence, storage engine or production runtime is exercised or enabled.
The existing full-suite loopback gate test uses a disposable local listener;
no public endpoint or external service is contacted. In-memory replay is not durability, bank exactly-once, chain finality, offline
trust or production admission authority. Retained refusals are process-local;
canonical/journal comparisons do not imply durable rejection restoration.

Non-author A2 exact-HEAD review and KTX/KIX exact-head CI remain supervisor gates.
Their run IDs/status/conclusions are NOT_RUN/unavailable in this no-GitHub
builder session. No merge occurred; post-merge CI is not applicable. READY means
local builder handoff only, not merge-ready, independent review or activation.

## Changed paths

- `reference/booking_resale_admission/admission_session.py`
- `reference/booking_resale_admission/admission_cli.py`
- `reference/booking_resale_admission/test_admission_session.py`
- `reference/booking_resale_admission/test_admission_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/fixtures/admission_request_inputs_session.json`
- `reference/booking_resale_admission/fixtures/admission_request_inputs.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_admission_inputs_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_admission_inputs.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-04-plan-local-admission-request-inputs/README.md`

## Deviations

- Startup fetch omitted under the supervisor's explicit no-network instruction.
- No new task document or issue created; this node's execution input is supplied
  in the user message. No commit/push/PR/comment or independent review performed.
- Shared routing requires no production-code edit. No other scope change.
- Rust test/Clippy could not compile because the offline dependency cache lacks
  `bcs`. No network fetch, dependency/CI change or automatic retry was attempted.
