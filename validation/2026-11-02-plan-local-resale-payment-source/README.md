# Synthetic local resale payment source — builder evidence

Task: `plan-local-resale-payment-source`. Immutable input is the supervisor's
node specification and design supplied in this session; no issue or task file
exists for this node. This is not ASTRA program mode.

Local cached `origin/main`, base and initial HEAD:
`c621e101e8a7efc47349ba23970dc6b578018218`, branch
`agent/kix-plan-local-resale-payment-source`. No local base delta. The supervisor
forbids network actions, so AGENTS §1 fetch was not run; remote freshness remains
unverified. No commit/push/PR/comment is authorized. Final committed implementation
and task heads, KTX/KIX exact-head run IDs/status/conclusions, non-author A2 review,
merge and post-merge evidence remain supervisor/reviewer gates. Builder READY is
not merge-ready.

Before edits both working-file Git blobs match their locks:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (kernel lib) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (quarantine test).
Historical `reference/v0.3-rc1` HEAD tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Existing coverage mapping (recorded before new tests)

Paths in this table are under `reference/booking_resale_admission/`.

| Requirement | Existing coverage classification and evidence | New gap |
|---|---|---|
| LISTED/BUY_HELD payment, separate transfer | Sufficient FSM coverage: `test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential`, `test_buy_hold_is_optional_and_cancel_order_decides_the_race`; session `test_complete_explicit_flow_and_replay_after_close` | Partial overall: source-backed observation and separate explicit session transfer |
| Receipts/errors/state/journal, replay/conflict | Sufficient FSM coverage: above tests, `test_resale_rejection_atomicity.py`, `test_returned_data_isolation.py` | Partial overall: payment-adapter/direct parity including retained semantic rejections |
| Wrong buyer, wrong amount, expiry, unknown listing | Sufficient scoped FSM coverage: hold/transfer tests and `test_stale_listing_policy_and_expiry_do_not_transfer` | Partial overall: valid-shaped source records reach the same FSM decisions |
| Missing/malformed/mismatched listing/faults bind no key | Not covered for payment source; offer adapter `test_absent_malformed_mismatched_and_fault_records_touch_no_fsm_or_keys` is precedent | Zero-access sentinel, real-machine snapshots and valid same-key reuse |
| One fetch per request, no retry/fallback/cache | Not covered for payment source | Replay, bad callers, faults and failure after acceptance |
| Immutable recordings/detached results | Not covered for payment source; offer source isolation is precedent | Constructor mapping mutation, fresh decoding, receipt mutation |
| False flags/no implicit external effects | Sufficient FSM coverage: `assert_not_final`, bound-transfer test and `test_open_items.py` | Partial overall: unchanged flags, reservation/settlement snapshots and exact adapter call boundary |
| Runnable example, regression/discovery/docs | Existing checkers and offer/session examples are precedent | New source modules, actual-session example and indexed evidence |

Tests are source-informed local regression evidence, not independent verification.
Verification results and final changed paths are recorded below after execution.

## Commands actually run and results

Commands ran in the foreground from repository root. Python is 3.13.5; all test
and checker commands set `PYTHONDONTWRITEBYTECODE=1`. Named booking-module
commands additionally set `PYTHONPATH="$PWD/reference/booking_resale_admission"`.
Counts overlap and must not be added together. No implementation/test assertion
failed. The temporary broader runner initially failed during discovery, then
passed after its import path was corrected, as recorded below.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean, expected branch, both SHAs equal the base above; unchanged at completion |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS, both required blobs before and after |
| `git rev-parse HEAD:reference/v0.3-rc1` | Historical tree equals the value above |
| `python3 -m unittest test_resale_payment_source test_resale_payment_adapter` | PASS, 16 tests |
| `python3 -m unittest test_resale_fsm test_resale_session test_resale_cli` | PASS, 35 tests, including three new session tests |
| `python3 -m unittest test_resale_offer_source test_resale_offer_adapter` | PASS, 17 tests |
| `python3 -m unittest test_resale_rejection_atomicity test_returned_data_isolation test_open_items` | PASS, 127 tests |
| `python3 reference/booking_resale_admission/example_resale_payment_adapter.py > /tmp/kix-resale-payment-example.json` | Exit 0, actual session produces PAYMENT_NOTED pause and separate TRANSFERRED receipt; both held/unheld variants are also exercised by new tests |
| Socket-guarded `python3 /tmp/kix-resale-payment-offline.py > /tmp/kix-resale-payment-offline.log 2>&1` (runner below) | First attempt: discovery ImportError, sibling settlement `test_contract_error_codes` imported first due to temporary script path ordering; no tests ran. Added booking path at index 0. Rerun: PASS, 540 tests; one exact HTTP test explicitly excluded |
| `python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo --version`; `rustc --version` with system environment below | Cargo/rustc 1.85.1 available; no installation/download |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable, exit 101: cached crates.io `serde` missing; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable, exit 101: cached `serde` missing; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable, exit 101: system Cargo has no `clippy` command |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Unavailable, exit 101: system Cargo has no `fmt` command |
| `git diff --check` | PASS |
| Read-only Python Git-blob comparison using `git ls-tree -r -z HEAD -- <two locked files> reference/v0.3-rc1` and SHA-1 over the Git blob header plus working bytes | PASS, all 110 protected tracked blobs byte-identical |
| Inline Python `git diff --name-only HEAD`; `git ls-files --others --exclude-standard`; new-file `ast.parse` and trailing-whitespace checks | PASS: exactly four allowed tracked edits, seven new files; all new Python files parse |
| `git diff --exit-code HEAD -- runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1 .aiops docs/tasks .github/workflows docs/contracts runtime sdk` | PASS, no protected-path changes |

The four ancillary Cargo checks each ran with
`PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true CARGO_HOME=/tmp/kix-resale-payment-cargo`.
This selects existing system tools without invoking rustup downloads or network
access. Their prerequisite failures are **not passes**. No Rust implementation
changed; full CI retains its pinned toolchain and dependencies.

The inspected workflows are `.github/workflows/protocol.yml` and
`.github/workflows/ktx-kernel.yml`. The applicable documentation/discovery/OpenAPI
commands each ran as `python3 scripts/<name>.py` and separately with `--self-test`
using a sequential subprocess loop that checked each exit code. All fourteen
commands passed with a socket-denying `sitecustomize` on `PYTHONPATH`:

| Script | Plain result | Self-test result |
|---|---|---|
| `check_docs_index` | PASS, scanned 331 / indexed 296 / allowlisted 35 | PASS |
| `check_bra_evidence_map` | PASS, 39 rows; grades unchanged | PASS, 50 negative controls |
| `check_contract_error_codes` | PASS, 199 covered rows; no Class B/C additions | PASS |
| `check_ci_checker_wiring` | PASS, 35 scripts | PASS, 13 negative controls |
| `check_ci_test_discovery` | PASS, both new suites reached by existing booking discovery, 31 booking files | PASS, 18 negative controls |
| `check_openapi_contract` | PASS, 84 commands, pin unchanged | PASS |
| `check_integration_gate_openapi` | PASS, 84 commands, productionEndpoint/publicHost false | PASS |

Architecture checks used the same socket guard. No workflow was modified.

## Socket-free broader selection and reproduction

Full booking discovery contains one existing live loopback test. It was not run:
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
This is a 540-test offline selection, **not a full-suite or full-CI pass**.
No HTTP/readiness, Move, ZK, SDK, production runtime or external provider suite
is claimed. The guard applies to the test runner and subprocesses that inherit
its environment; existing import-only subprocess probes supply their own
`PYTHONPATH`. New payment code/tests and the example use only standard-library,
in-memory synthetic inputs and no sockets or external dependencies.

The actual temporary guard `/tmp/kix-resale-payment-no-sockets/sitecustomize.py`:

```python
import sys


def deny_sockets(event, args):
    if event in {"socket.__new__", "socket.connect", "socket.bind", "socket.getaddrinfo"}:
        raise AssertionError("socket use forbidden in offline verification: " + event)


sys.addaudithook(deny_sockets)
```

The corrected temporary runner `/tmp/kix-resale-payment-offline.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("reference/booking_resale_admission").resolve()))
excluded = "test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit"


def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test


suite = unittest.defaultTestLoader.discover(
    "reference/booking_resale_admission", top_level_dir="reference/booking_resale_admission")
tests = list(flatten(suite))
assert sum(test.id() == excluded for test in tests) == 1
print("Explicit socket-dependent exclusion:", excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(
    test for test in tests if test.id() != excluded))
sys.exit(not result.wasSuccessful())
```

Actual invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="/tmp/kix-resale-payment-no-sockets:$PWD/reference/booking_resale_admission:$PWD" \
python3 /tmp/kix-resale-payment-offline.py > /tmp/kix-resale-payment-offline.log 2>&1
```

## New evidence, changed paths and limits

`test_resale_payment_source.py` covers copied/read-only recordings, detached
nested results and call snapshots, strict JSON, absence and immediate faults.
`test_resale_payment_adapter.py` covers exact argument/receipt/exception identity,
LISTED and BUY_HELD payment/direct-FSM parity, replay through another recording
selector and after transfer/close, conflicts, retained wrong-buyer/amount/binding
refusals, expiry and unknown listing. State/digest/journal comparisons and
same-key probes distinguish pre-delegation refusal from retained FSM rejection.
It also covers shape matrices, one-fetch outcomes, faults after acceptance
without cached receipts, and held/unheld actual-session examples.
The three session additions cover optional source compatibility, missing
configuration, explicit sequencing, unchanged reservation/settlement snapshots,
direct-call replay equivalence and faults without follow-up requests.

Complete changed-path list:

- `reference/booking_resale_admission/resale_payment_source.py`
- `reference/booking_resale_admission/fake_resale_payment_source.py`
- `reference/booking_resale_admission/resale_payment_adapter.py`
- `reference/booking_resale_admission/resale_session.py`
- `reference/booking_resale_admission/example_resale_payment_adapter.py`
- `reference/booking_resale_admission/test_resale_payment_source.py`
- `reference/booking_resale_admission/test_resale_payment_adapter.py`
- `reference/booking_resale_admission/test_resale_session.py`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-02-plan-local-resale-payment-source/README.md`

No contract violation or new contract-undefined FSM behavior was found. Existing
copy-isolation and clock/order characterizations remain source-informed, without
new protocol semantics or an independent verification claim. False authority,
provider/funds/durability/finality flags remain unchanged. No reference derivation,
cancellation-history interpretation, reservation handoff, settlement execution,
admission, payout, persistence, concurrency or production capability was added
or tested. Synthetic recordings do not prove provider authenticity or eligibility.

Product values remain **UNDETERMINED — Astra/User**. Provider authority remains
with User/Toss technical owners; resale merchant eligibility with User/Toss sales;
compensation/payout duties with existing legal/accounting/tax owners. No values
or owner decisions were filled in. Contract/evidence-map statuses are unchanged.

Deviations: session-start network fetch omitted under the explicit supervisor
rule; no repository task document created; socket-dependent HTTP coverage excluded
from broader discovery; temporary runner import order corrected before its pass;
ancillary Rust checks unavailable due to existing offline prerequisites. No design
or scope expansion was required and no STOP dependency was encountered.

Delivery is uncommitted. Full exact-final-head **KTX kernel verification** and
**KIX protocol verification** run IDs/status/conclusions are unavailable, not green;
non-author exact-head A2 review is pending. Merge/post-merge SHA and CI evidence
are not applicable (no merge). The supervisor retains all git/GitHub actions.
