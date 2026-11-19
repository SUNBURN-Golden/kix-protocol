# Explicit local ticket fulfillment desk evidence

Node: `plan-local-ticket-fulfillment-desk`. Task input: supervisor-supplied node
specification and design plan in this session; no issue or docs/tasks document.
Not ASTRA program mode. Initial branch `agent/kix-plan-local-ticket-fulfillment-desk`.
Initial HEAD and cached origin/main: `d0a4697e2fbe88306d2a0227c56a741841e7ed43`.
Remote freshness is unverified: the supervisor prohibits network actions, overriding
AGENTS.md §1 fetch. No base change. No commits or GitHub actions authorized.

## Coverage mapping recorded before adding tests

| Requirement | Existing evidence | Classification and gap |
|---|---|---|
| Reservation/payment/expiry and bound/unbound issuance | `test_reservation_fsm.py`: `test_unbound_issue_is_memory_evidence_without_economic_finality`, `test_expiry_does_not_release_until_an_explicit_release`, `test_settlement_gate_refuses_uncommitted_finality`, `test_bound_issue_checks_gross_and_replays_only_with_the_commit_view` | Sufficient FSM coverage; missing desk forwarding/composition |
| Resale and admission sequencing | `test_resale_fsm.py`: `test_buy_hold_is_optional_and_cancel_order_decides_the_race`; `test_admission_fsm.py`: `test_listing_and_cancel_order_against_entry`, `test_issued_credential_is_consumed_once_and_replay_does_not_bump_version` | Sufficient FSM coverage; missing second-ticket fulfillment composition |
| Adoption atomicity | `test_adopt_issued_atomicity.py`: order/payment conflicts, failed materialization rollback and retry, for both machines; `test_resale_fsm.py::test_reservation_fsm_rejects_unissued_consumed_and_cancelled_tickets`; admission pre-issuance and source refusal tests | Sufficient unbound atomicity and FSM rejection coverage; missing bound session exposure |
| Explicit single calls and error/receipt identity | `test_booking_session.py`, `test_resale_session.py`, `test_admission_session.py` forwarding suites | Partial: four new selectors missing |
| Direct graph parity, journals/digests and no automatic actions | `test_ticket_operations_session.py::direct_graph`, `direct_call`, `snapshot`, existing transcript parity | Partial: fulfillment transcript missing |
| Strict arguments, exit 0/1/2, file/stdin, false claims | Existing standalone/shared CLI suites and flag helpers | Partial: new selectors and fulfillment history missing |
| Fixture anchor/clocks/adoption validation | Existing `test_ticket_operations_cli.py::test_setup_is_allowlisted_and_requires_explicit_clocks_binding_and_adoption` and standalone fixture regressions | Sufficient rules; preserve unchanged and test new fixture |

These are source-informed composition checks, not clean-room verification.
Results, changed paths, limitations and pending delivery gates are recorded below
when verification completes.

## Implementation and gap evidence

Booking exposes `bind_settlement` and `issue`, each requiring the existing
successful explicit session clock. Resale and admission each expose
`adopt_issued` with the full required explicit argument set, including nullable
reservation/quote arguments without defaults. Each wrapper forwards exactly
once and preserves receipt/exception identity. The existing shared router uses
the extended dispatch tables without changes. No FSM or fixture validator changed.

`test_ticket_fulfillment.py` provides ten focused tests:

- `test_prepared_second_ticket_matches_direct_graph`: an independently constructed
  public-FSM control graph after every request; compares receipts/errors,
  canonical states, digests and all four journals; unrelated-machine snapshots
  and recording fetch histories establish explicit action boundaries.
- `test_fulfillment_file_and_stdin`: both executable forms produce every expected
  row and exit 1; successful prefix exits 0; missing session clock stops with 2.
- `test_booking_clock_successful_replay_and_no_key_on_local_refusal`: fixture
  clocks do not initialize the booking session, failed clocks do not unlock it,
  and explicit successful clock replay does; prerequisite failure retains no key.
- `test_issuance_before_payment_and_retained_refusal`: explicit later payment
  does not repair a retained refusal; a supplied fresh key issues unbound memory
  evidence, preserving the existing UNBOUND behavior.
- `test_uncommitted_mismatched_and_expired_issuance`: committed amount mismatch,
  uncommitted settlement and expired reservation refuse without state/journal
  effects. Explicit later commit retains the original refusal; a fresh key works.
- `test_adoption_refusals_are_atomic_and_require_explicit_fresh_keys`: both
  surfaces refuse pre-issuance adoption; payment/quote mismatches leave no
  effects; retained errors, fresh keys, duplicate success and binding/key
  conflicts match the direct control.
- `test_same_key_changed_subject_body_or_operation`: binding and issuance replay
  and changed subject/body/cross-operation conflicts.
- `test_all_new_operations_forward_opaque_arguments_once_without_defaults`:
  explicit signature and dispatcher schemas, opaque caller objects and explicit
  nulls, one exact FSM call, original receipt and original exception identity.
- `test_new_selectors_strict_standalone_and_shared_arguments`: every missing
  field, extra fields, wrong argument containers, duplicate JSON keys, NaN and
  exponent overflow; stops at one output row with exit 2 and no machine effects.
- `test_new_fixture_retains_anchor_and_exact_setup_validation`: removal of the
  anchor issuance, binding, required adoption or clock is still rejected.

Existing booking and resale forwarding matrices and admission/shared CLI schema
matrices were extended rather than duplicating their tests. The 18-line fixture
journey explicitly replays a refused authorization after listing cancellation,
then supplies a fresh key, authorizes and separately consumes. Issuance replay
still contains version 1; current reservation/admission views contain version 2.
Resale remains version 1, preserving unsynchronized existing views. All successful
receipts/views run through the existing false-funds/chain/production flag helpers.

## Actual commands and results

All commands ran from the repository root in this worktree. Test runs used
`PYTHONDONTWRITEBYTECODE=1`. Focused session/desk commands used:

```bash
export PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"
```

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; both SHAs equal the base above; expected branch. Final refs/branch unchanged |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before work; verified again after work |
| `git ls-tree HEAD reference/v0.3-rc1` | Initial tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; final working bytes match HEAD |
| `python3 -m unittest test_ticket_fulfillment` | PASS: 10 tests, 3.171 s |
| `python3 -m unittest test_booking_session test_booking_cli test_resale_session test_resale_cli test_admission_session test_admission_cli test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes` | PASS: 111 tests, 19.081 s |
| `python3 -m unittest test_ticket_fulfillment test_booking_session test_booking_cli test_resale_session test_resale_cli test_admission_session test_admission_cli test_ticket_operations_session test_ticket_operations_cli test_ticket_operations_quotes` | PASS after extending existing matrices: 121 tests, 16.377 s |
| `python3 /tmp/kix-fulfillment-offline.py` with the guard/selection below | PASS: 609 tests, 26.354 s; exactly one HTTP test excluded. **Partial socket-free selection**, not full HTTP-suite success |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 2.649 s |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.318 s |
| `python3 /tmp/kix-fulfillment-checks.py` | PASS: sequential foreground checker subprocesses, each plain and self-test, plus architecture commands; individual results below |
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.308 s |
| `python3 /tmp/kix-fulfillment-rust.py` | Exit 1: offline prerequisite failures in tests/Clippy; versions/fmt pass, individual results below |
| `python3 /tmp/kix-fulfillment-preservation.py` | PASS: 254 protected working blobs and all 29 preexisting booking fixtures match HEAD; exactly 17 allowed changed paths; AST/JSON/18 JSONL rows/whitespace valid; branch/HEAD/cached origin/main unchanged |
| `git diff --check` | PASS |

Counts overlap and must not be summed. There were no Python test or checker
failures. The first focused run preceded the additional existing resale/admission
matrix entries; the combined 121-test run and 609-test selection include them.

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. The checker runner
executed `python3 scripts/<name>.py` and the same command with `--self-test`,
sequentially, recording every exit status:

| Checker | Plain | Self-test |
|---|---|---|
| `check_openapi_contract` | PASS: 84 commands, unchanged pin | PASS |
| `check_integration_gate_openapi` | PASS: 84 commands, publicHost/productionEndpoint false | PASS |
| `check_docs_index` | PASS: scanned 337, indexed 302, allowlisted 35 | PASS |
| `check_ci_test_discovery` | PASS: seven reference suites, all 36 booking test modules reached | PASS: 18 negative controls |
| `check_ci_checker_wiring` | PASS: 35 checker scripts | PASS: 13 negative controls |
| `check_bra_evidence_map` | PASS: 39 rows; capability grades unchanged | PASS: 50 negative controls |
| `check_contract_error_codes` | PASS: 199 covered rows, CLASS_B=0/CLASS_C=0 in that code map | PASS |

The code-map counts do not erase existing behavioral Class B characterizations.

Rust verification used the already-installed CI-version 1.98.1 toolchain.
Existing `/home/box/.cargo/registry` bytes were copied to
`/tmp/kix-fulfillment-cargo/registry`; nothing was downloaded or installed.
The runner passed this environment to every command:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-fulfillment-cargo
export CARGO_TARGET_DIR=/tmp/kix-fulfillment-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version`; `rustc --version` | Both 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101: no matching cached `bcs`, required by workspace `kix-bcs1`; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101: same missing cached `bcs`; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101: same prerequisite failure; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

No Rust file changed. No prerequisite installation, network retry or host change
was attempted. These commands are local selections, not full repository CI.
Move/localnet/ZK, other untouched reference suites and full HTTP coverage were
not run or claimed. Required hosted KTX/KIX checks remain pending.

## Reproduce the socket-denied selection

Create `/tmp/kix-fulfillment-no-sockets/sitecustomize.py`:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

Create `/tmp/kix-fulfillment-offline.py`:

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

Actual invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="/tmp/kix-fulfillment-no-sockets:$PWD/reference/booking_resale_admission:$PWD" \
python3 /tmp/kix-fulfillment-offline.py
```

Every new transcript subprocess inherits the socket guard. Some unchanged
import-only probes replace PYTHONPATH; their guard inheritance is not claimed.
The excluded HTTP test and `integration_gate.test_http_gate` remain unchanged
and required in normal CI. Neither ran locally.

The preservation script enumerates changed/untracked files against the complete
allowlist below, parses changed Python/JSON/JSONL, checks whitespace, and hashes
working bytes as Git blobs against HEAD throughout `runtime/`, `.aiops/`,
`docs/tasks/`, `docs/contracts/`, `.github/`, `sdk/`, `reference/v0.3-rc1/` and every
preexisting booking fixture. Initial clean status and the recorded locked blobs
provide the before baseline; the 254 protected blobs and 29 old fixtures all
match after work. Contracts, catalogue, SDK, FSMs, shared router, fixture
validators, kernel, task inputs, historical reference and program file are
unchanged. No claims of transient mutation testing are made.

## Complete changed-path list

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/booking_session.py`
- `reference/booking_resale_admission/booking_cli.py`
- `reference/booking_resale_admission/resale_session.py`
- `reference/booking_resale_admission/resale_cli.py`
- `reference/booking_resale_admission/admission_session.py`
- `reference/booking_resale_admission/admission_cli.py`
- `reference/booking_resale_admission/test_booking_session.py`
- `reference/booking_resale_admission/test_booking_cli.py`
- `reference/booking_resale_admission/test_resale_session.py`
- `reference/booking_resale_admission/test_admission_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/test_ticket_fulfillment.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_fulfillment.jsonl`
- `validation/2026-11-03-plan-local-ticket-fulfillment-desk/README.md`

## Contract classification, deviations and pending gates

Class A: exercised transitions, atomic adoption refusals, receipts, historical
snapshots/current views, retained errors and idempotency conflicts match the
unchanged contracts. No explicit contract violation was found. No new contract-
undefined behavior was introduced or assigned semantics. Existing Class B
clock-skew partial effects and unsynchronized source views remain unchanged;
no synchronization, cross-machine rollback or automatic follow-up is claimed.

Deviations: supervisor network prohibition overrides §1 fetch; no task issue or
docs/tasks document exists or was created. New fulfillment boundary/parity tests
are consolidated in `test_ticket_fulfillment.py`, reusing existing helpers and
extending existing matrices, so separate new admission-session and resale-CLI
test files were unnecessary. Verification is the stated partial socket-free
selection; Rust tests/Clippy remain unavailable offline due to missing `bcs`.
No STOP dependency, new protocol command, product policy choice or consequential
scope expansion arose. No decisions file is required.

Policy values remain **UNDETERMINED — Astra/User**. Legal, accounting, tax,
privacy and provider facts retain their existing named owners. Capability grades
are unchanged. This is source-informed builder evidence, not non-author review,
clean-room independence, production durability, distributed fencing, bank/venue
exactly-once, chain finality, legal compliance or production readiness. No real
funds, PG/bank/KYC calls, public endpoint, production runtime, Sui testnet/mainnet,
coin/TIX module, new engine, persistence, frontend, payment lookup/handoff,
automatic issuance or adoption, or new policy default was added.

Both locked blobs match before and after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The patch remains uncommitted by instruction. Observed implementation HEAD is
still `d0a4697e2fbe88306d2a0227c56a741841e7ed43`; it does not contain this patch.
The supervisor must assign the final task head. Non-author A2 exact-head review
is **pending**. Exact-head KTX run ID/status/conclusion and exact-head KIX run
ID/status/conclusion are **unavailable/pending**, not successful. Before delivery
require the review and both workflows completed/success for the supervisor's
exact final head, including normal HTTP and Rust verification. User publication/
merge authorization remains separate. No commit, push, PR, issue, comment,
ASTRA marker or merge was created. Merge SHA, final-merge blob checks and
post-merge main CI are not applicable. Builder READY denotes local handoff only,
not merge readiness. Offline Rust prerequisites, full HTTP coverage and hosted
exact-head gates remain supervisor verification items.
