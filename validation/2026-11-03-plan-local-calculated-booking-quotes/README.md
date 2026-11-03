# Local calculated booking quotes — builder evidence

Task: `plan-local-calculated-booking-quotes`. The task input and design are the
supervisor-supplied node text; no task issue or node document under `docs/tasks/`
exists. This is not ASTRA program mode. This report is builder-authored,
source-informed evidence, not independent review or merge authorization.

Observed cached `origin/main`, base and initial task HEAD:
`8306d37b555b17228951393b8619592b800c0e1c` on
`agent/kix-plan-local-calculated-booking-quotes`. Remote freshness is unverified:
the explicit supervisor prohibition on network actions overrides AGENTS §1 fetch.

## Existing coverage map (recorded before adding tests)

| Requirement | Existing evidence | Classification / new gap |
|---|---|---|
| Calculation correctness | `reference/v0.3-rc1/test_commerce.py`, `test_commerce_driver.py` | Sufficient underneath; bridge parity uncovered |
| File/stdin and CLI exit semantics | `test_booking_quote_cli.py`, `test_ticket_operations_quotes.py` | Partial; calculated-source journeys uncovered |
| Replay, changed key input, primary price and expiry | `test_booking_quote_adapter.py::test_replay_alias_changed_quote_amount_order_and_binding_parity`, `test_retained_price_and_expiry_refusals_match_direct_session`; reservation regressions | Sufficient underneath; calculated integration uncovered |
| Single-line, no discounts, exact KRW, booking bounds | Commerce amount validation only | Restricted bridge profile uncovered |
| Malformed input, CE1 tokens, detached source | Commerce driver and `test_booking_quote_source.py` | Partial; new constructor and bridge uncovered |
| Source refusal atomicity, one fetch, no fallback | `test_booking_quote_adapter.py::test_missing_bad_json_and_faults_no_fsm_call_or_key_binding`, `test_source_failure_after_success_never_falls_back_to_retained_receipt`; shared desk suite | Partial; calculated source path uncovered |
| Existing recorded behavior, discovery, contracts | Existing quote/session/shared suites and CI checkers | Sufficient; rerun without duplicating |

Report index: [new evidence](#implementation-and-new-evidence),
[commands](#commands-actually-run-and-results),
[preservation](#complete-changed-paths-and-preservation),
[delivery limitations](#classification-deviations-and-remaining-delivery-gates).

## Implementation and new evidence

The optional source stores explicit reservation/request-text pairs immutably.
Every fetch calculates afresh through the unchanged CE1 decoder and
`commerce.build_quote`; only code modules are cached. Temporary legacy module
bindings are restored, with no added calculator path. Unsupported profiles and
booking money bounds become existing local source errors before confirmation.
The adapter, sessions, selectors, FSMs and contracts are unchanged. Both CLIs
compose the existing adapter; shared composition binds exactly `session.booking`.

| New test / evidence | Gap addressed |
|---|---|
| `test_calculated_booking_quote_source.py::test_complete_output_matches_direct_unchanged_calculator_and_boundaries` | Complete calculation equality with direct `commerce.build_quote` in a separate Python process; fetch amount/hash equality for amounts 1, 10001, 10**12, and maximum version/timestamp metadata |
| `test_all_source_rejections_do_not_delegate_mutate_or_bind_key` | Restricted assets (each metadata field), zero/two lines, zero-effect FIXED/BPS rules, exact out-of-bound atom strings (including 2**53+1 and u128), malformed schemas/tokens, CE1 size/depth, negative zero/fraction/exponent/nonfinite/duplicate/Unicode refusal; zero confirm calls, unchanged state/digest/journal, successful same-key reuse |
| `test_storage_results_and_calls_are_detached_and_fetch_recalculates`, `test_constructor_rejects_invalid_structure_but_calculation_is_lazy` | Caller mapping mutation, immutable stored entries, detached returned calculations/records/call tuples, empty/missing results, recalculation count, lazy malformed-text validation |
| `test_receipts_replay_price_expiry_and_historical_result_match_direct_session` | Direct BookingSession receipt/state/digest/journal parity; replay, changed hash/key conflict, price mismatch, exact reservation expiry and replay after cancellation |
| `test_invalid_callers_fetch_zero_and_failure_after_success_has_no_fallback` | Zero fetch on invalid callers, one fetch per explicit valid request, no delegation/mutation/fallback on later calculator refusal, retained successful replay afterward |
| `test_import_and_lazy_load_preserve_public_modules_and_paths` | Fresh-process lazy import, restoration of preexisting public module bindings, no sys.path pollution |
| `test_calculated_booking_quote_cli.py::test_each_transcript_matches_direct_session_and_keeps_other_surfaces_unchanged` | Every row compared to direct BookingSession calls with calculated amount/hash; source fetch count, separate shared booking graph, unchanged settlement/resale/admission snapshots and original issued inventory, null payment/settlement/issuance/right fields and unchanged mock flags |
| `test_both_desks_file_and_stdin_rows_exits_and_computed_hash` | Four transcripts through file and stdin, socket-denied subprocesses, complete output equality and row counts, success/replay and boundary refusal exits |
| `test_opt_in_mutual_exclusion_and_unchanged_recorded_and_unconfigured_behavior` | Exclusive source flags, unchanged recorded confirmation, unconfigured refusal, identical direct booking output with/without calculated source |
| `test_loading_has_no_calculation_fetch_or_clock_and_shared_binding_is_exact`, `test_strict_fixture_schema_encoding_lazy_failure_and_cli_exits` | Source-only construction, exact shared adapter binding, strict fixture fields/types/duplicates/empty collection, invalid UTF-8 file, malformed file/request, explicit session clock prerequisite and exits 0/1/2 |

Both confirm transcripts have 7 rows (exit 0); both boundary transcripts have 21
rows (exit 1). Boundary cases include source failure after success, primary-price
refusal and its retained changed-input conflict, cancellation/historical replay,
second hold and exact reservation expiry. The fixture's calculation expiry `1`
is deliberately distinct from the reservation clock `1000000` / expiry `1900000`;
this adapter does not invoke the commerce payment-planning gate. Calculation
metadata is hash-bound input, not authenticated order/show/expiry authority.
Shared fixture setup already includes unrelated synthetic issued inventory;
these journeys add a separate show and never progress payment/settlement/issuance.

## Commands actually run and results

All jobs ran in the foreground. No network, Git/GitHub publication, background
job or external service was used. Test counts overlap and must not be summed.
Supported Python was **3.12.15**. Except for the initial inspection/hash script,
Python verification used `PYTHONDONTWRITEBYTECODE=1`, including child processes.
The verification environment was:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="/tmp/kix-calculated-no-sockets:$PWD/reference/booking_resale_admission:$PWD"
```

`/tmp/kix-calculated-no-sockets/sitecustomize.py` installs this audit hook:

```python
import sys

def deny_sockets(event, args):
    if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('socket use forbidden in offline verification: ' + event)

sys.addaudithook(deny_sockets)
```

The new CLI child processes also install the same denial before importing the
CLI, independent of environment inheritance. Direct calculator subprocesses keep
the guard and prepend only the unchanged calculator directory to their own path.
Some unchanged import-only probes replace PYTHONPATH; guard inheritance is
claimed for the new children, not all historical import probes.

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; expected worktree/branch; HEAD and cached main equal the SHA above; no remote freshness claim |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required exact blobs match before and after |
| Initial Python SHA-256 snapshot using `git ls-files -z` | Recorded 298 protected paths and preexisting booking fixtures before implementation |
| `python3.12 --version` | Python 3.12.15 |
| `python3.12 -m unittest test_calculated_booking_quote_source test_calculated_booking_quote_cli` | First: 12 tests, one test-only incorrect expected exit for existing shared transcript. Corrected expectation, then **12 PASS**, 2.747 s, under socket denial |
| `PYTHONPATH=/tmp/kix-calculated-no-sockets:reference/v0.3-rc1:. python3.12 -m unittest test_commerce test_commerce_driver` | **27 PASS**, 0.411 s |
| Broad selected booking command below | **187 PASS**, 11.652 s |
| `python3.12 /tmp/kix-calculated-offline.py` (exact selection below) | **650 PASS**, 66.949 s; exactly one documented socket-dependent exclusion |
| `python3.12 scripts/verify_commerce.py --report .local/verification/commerce.json` | PASS; CALCULATION_ONLY, payable 48600, selected-line refund 16200, externalCalls 0 |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS; architecture v5 + KTX-R1 dependency gate, no durability/performance certification |
| `python3.12 scripts/test_runtime_architecture.py` | **7 PASS**, 0.273 s |
| `python3.12 -m unittest integration_gate.test_offline_limits` | **9 PASS**, 0.222 s |
| `python3.12 /tmp/kix-calculated-final.py` | PASS; exact 14-path allowlist, all 298 protected hashes equal initial bytes and HEAD Git blobs, new Python/JSON/JSONL syntax and whitespace, unchanged refs |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks docs/contracts .github sdk reference/v0.3-rc1` | PASS; no changes |
| `git diff --check` | PASS |

The test-only correction changed the expected exit for
`ticket_operations_booking.jsonl` from 0 to 1: that unchanged historical journey
intentionally includes domain refusals. Output equality with/without the source
was already passing. No implementation/contract correction was required by the
verification runs. The restricted profile check was moved ahead of calculation
before the successful rerun, in accordance with the supplied design.

The broad selected booking command actually run was:

```bash
python3.12 -m unittest \
  test_calculated_booking_quote_source test_calculated_booking_quote_cli \
  test_booking_quote_source test_booking_quote_adapter test_booking_quote_cli \
  test_booking_session test_booking_cli test_ticket_operations_quotes \
  test_ticket_operations_session test_ticket_operations_cli \
  test_primary_price_binding test_primary_resale_bps_isolation \
  test_reservation_fsm test_reservation_rejection_atomicity \
  test_returned_data_isolation test_open_items
```

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. Executed all
following checkers plainly and with `--self-test`, sequentially through
`python3.12 /tmp/kix-calculated-ci.py`. Every subprocess exit status was checked;
detailed outputs are local in `/tmp/kix-calculated-ci-results.json`.

| Command | Plain | `--self-test` |
|---|---|---|
| `python3.12 scripts/check_docs_index.py` | PASS | PASS |
| `python3.12 scripts/check_bra_evidence_map.py` | PASS | PASS |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py` | PASS | PASS |
| `python3.12 scripts/check_contract_error_codes.py` | PASS | PASS |
| `python3.12 scripts/check_ci_test_discovery.py` | PASS | PASS |
| `python3.12 scripts/check_ci_checker_wiring.py` | PASS | PASS |
| `python3.12 scripts/check_openapi_contract.py` | PASS | PASS |
| `python3.12 scripts/check_integration_gate_openapi.py` | PASS | PASS |

OpenAPI remains pinned at 84 commands, SHA-256
`ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`.
No CI/checker/contract file was changed. After completing this report, the eight
plain checkers and final preservation checks were rerun successfully.

### Exact socket-denied discovery selection

`/tmp/kix-calculated-offline.py` used the documented previous-node exclusion and
explicit booking path ordering:

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
assert sum(test.id() == excluded for test in tests) == 1
print('Explicit socket-dependent exclusion:', excluded, flush=True)
result = unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(
    test for test in tests if test.id() != excluded))
sys.exit(not result.wasSuccessful())
```

This is selected local evidence, not full discovery/full HTTP or a full-CI pass.
The excluded test and `integration_gate.test_http_gate` remain required on the
supervisor's authorized verification host. No sockets were opened here.

### Rust workflow equivalents and unavailable prerequisites

Used installed workflow-pinned Rust **1.98.1**, with a copy of the preexisting
`/home/box/.cargo/registry` at `/tmp/kix-calculated-cargo/registry`; no downloads.
`python3.12 /tmp/kix-calculated-rust.py` ran the commands sequentially with:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/home/box/.local/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-calculated-cargo
export CARGO_TARGET_DIR=/tmp/kix-calculated-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version`; `rustc --version` | Both 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101: cached `bcs` missing; no tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101: cached `bcs` missing; no lint result |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101: cached `bcs` missing; no tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101: cached `bcs` missing; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

These four dependency-resolution failures remain unverified, never passes. They
need an available offline dependency cache or the normal authorized CI host;
the no-network instruction precludes fetching dependencies in this session.

## Complete changed paths and preservation

- `reference/booking_resale_admission/calculated_booking_quote_source.py`
- `reference/booking_resale_admission/calculated_booking_quote_fixture.py`
- `reference/booking_resale_admission/booking_cli.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_calculated_booking_quote_source.py`
- `reference/booking_resale_admission/test_calculated_booking_quote_cli.py`
- `reference/booking_resale_admission/fixtures/calculated_booking_quotes.json`
- `reference/booking_resale_admission/fixtures/booking_calculated_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/booking_calculated_boundaries.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_calculated_confirm.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_calculated_boundaries.jsonl`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-03-plan-local-calculated-booking-quotes/README.md`

| Locked file | Required and observed before/after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The final script compares SHA-256 against the initial 298-file snapshot and
independently compares working bytes as Git blobs against HEAD throughout
`runtime`, `.aiops`, `docs/tasks`, `docs/contracts`, `.github`, `sdk`,
`reference/v0.3-rc1` and all preexisting booking fixtures. The preserved
`reference/v0.3-rc1` Git tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. No protected file was transiently edited.

## Classification, deviations and remaining delivery gates

Class A: exercised source/session/FSM behavior matches the stated local contract.
No explicit contract violation found. No newly discovered contract-undefined
behavior was assigned semantics. Pricing, discount and quote-authority policy
remain **UNDETERMINED — Astra/User**; tax and accounting treatment remain
**UNDETERMINED — User and designated advisers**. No policy values were chosen.

No functional design deviation. Lazy calculator imports use explicit file specs
and temporary module bindings rather than adding a calculator directory to
sys.path; bindings are restored even on load failure. AGENTS §1 fetch was omitted
under the explicit supervisor no-network instruction. Full HTTP discovery and
Rust test/Clippy validation remain unavailable locally, as detailed above. These
limitations do not weaken CI and require no new product policy or STOP-condition
scope expansion. No `DECISION_REQUIRED.md` was necessary.

This is complete local implementation for supervisor handoff, not merge-ready.
Initial and final worktree HEAD remain
`8306d37b555b17228951393b8619592b800c0e1c`; changes are uncommitted by explicit
instruction. No implementation/final delivery commit or merge commit exists in
this session. Exact-head **KTX** and **KIX** workflow run IDs/status/conclusions
are **unavailable / unverified**. No post-merge main CI or final-merge blob check
was performed. The supervisor retains publication, non-author A2 exact-head
review, full authorized-host HTTP coverage, successful exact-final-head KTX/KIX
workflows, user-only ready/merge authorization and post-merge checks.

No authenticated quote/pricing authority, clean-room independence, payment
handoff, settlement, issuance, real funds/providers, persistence, production
runtime/durability, distributed fencing, bank exactly-once, chain finality,
legal compliance or runtime activation is claimed. No protocol/catalogue/SDK,
coin/TIX or storage/replication engine change. Follow-up is the required delivery
verification on the authorized host, not additional product implementation.

## Fix round 1 (delivered-head review + exact-head CI)

Delivered implementation head reviewed by CI and non-author review:
`47e51671b5e3afca6aa6ff02ef15b25cb8ef2e3e`. The earlier report above describes
the pre-delivery worktree (`8306d37…`) and the builder's PYTHONPATH-assisted
environment; both are historical evidence, not the delivered-head result.

The exact-head KIX protocol run failed 4 tests. Root cause: the socket-denial
subprocess helpers in `test_calculated_booking_quote_cli.py:52` and
`test_calculated_booking_quote_source.py:211` spawned `python -B -c` without
`cwd=`, so the child's `sys.path[0]` was the repository root, not the suite
directory. The builder's recorded runs exported
`PYTHONPATH=…/reference/booking_resale_admission`, which masked the defect; CI
runs `python3 -m unittest discover -s reference/booking_resale_admission
-t reference/booking_resale_admission` from the repository root with no
PYTHONPATH. Fix: pass `cwd=HERE` in both helpers (the pre-existing
`test_booking_quote_cli.py:191-193` and `test_ticket_operations_cli.py:319-322`
pattern). No implementation, fixture or contract change; no CI change.

Re-run in the exact CI shape from the repository root, with `PYTHONPATH`
unset entirely (`env -u PYTHONPATH`) and `PYTHONDONTWRITEBYTECODE=1`:

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | **651 PASS**, 30.528 s |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` (CI Python 3.12) | **651 PASS**, 43.936 s |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_calculated_booking_quote_*.py' -v` | **12 PASS**, 1.869 s (includes all 4 previously failing tests) |
| `python3 -m unittest test_commerce test_commerce_driver` (in `reference/v0.3-rc1`) | **27 PASS**, 0.339 s |
| CI suite loop over `settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward provider_facts` | 224 / 651 / 148 / 85 / 186 / 73 PASS |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | PASS / PASS; 84 commands, sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e` |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | PASS / PASS |
| `python3 -m unittest integration_gate.test_offline_limits` | **9 PASS**, 0.114 s |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `69564b16…` and `b607996c…` match the required locked blobs |
| `git diff --stat HEAD` | only the two test helpers changed (2 insertions, 2 deletions) |

Locked blobs and `reference/v0.3-rc1/**` are unchanged by this fix; no
`runtime/`, `.github/`, `.aiops/`, `docs/tasks/` or contract path was touched.
Exact-final-head KTX/KIX run IDs remain **unavailable in this session**; the
supervisor publishes this round's head and the normal non-author exact-head
review and CI gates still apply. No new product policy, secret, network, real
funds/providers or runtime activation is involved.
