# Shared local ticket operations desk

Task: `plan-local-ticket-operations-desk`. The authorized task document is the
supervisor's supplied node specification and design plan; no issue or repository
task document exists for this node. This is not ASTRA program mode.

Observed local `origin/main`, task base and starting HEAD:
`05ded3f73f29fdcd7734f27b0e07102b5888555a` on
`agent/kix-plan-local-ticket-operations-desk`. No local base delta. Remote freshness
is unverified: the supervisor explicitly prohibits network actions, overriding
the session-start fetch. No commits, pushes or GitHub actions are authorized.
Implementation/final committed head and exact-head CI are supervisor follow-ups.

## Existing coverage mapping (recorded before adding tests)

Paths below are relative to `reference/booking_resale_admission/`.

| Requirement | Existing coverage | Gap addressed here |
|---|---|---|
| Shared graph and explicit surface selection | Not covered jointly | Construction, source identities, isolation, combined dispatch |
| Listing blocks entry; cancellation permits fresh entry | FSM sufficient, composition partial: `test_admission_fsm.py::AdmissionFsmTests.test_listing_and_cancel_order_against_entry` | Runnable cancellation transcript, retained refusal |
| Authorization blocks listing; consumption blocks resale | FSM sufficient, composition partial: `test_admission_fsm.py::AdmissionFsmTests.test_entry_then_transfer_consumes_before_resale_can_move` | Runnable admission transcript |
| Old and unreissued recipient presentations refused after transfer | FSM/adapter sufficient: `test_admission_fsm.py::AdmissionFsmTests.test_transfer_then_entry_rejects_both_presentations`, `test_presentation_adapter.py` | Shared transfer transcript and current/historical views |
| Combined CLI/session/direct FSM parity | Not covered | Equivalent independently constructed graph, receipts/errors/state/digests/journals per request |
| First results, source faults, pure views, mock flags | Individual coverage sufficient: `test_resale_session.py`, `test_admission_session.py`, both adapter/source suites | Shared graph replay/fault effects and fetch counts |
| Independent clocks and no implicit follow-ups | Partial: both session suites; `test_admission_rejection_atomicity.py::AdmissionRejectionAtomicityTests.test_char_authorize_clock_skew_window` | Shared clocks, unchanged Class B skew characterization |
| Strict combined fixture/input, executable transcripts | Not covered jointly | Envelope/recording/setup rejection and stdin/file exit behavior |

This is source-informed builder evidence, not independent A2 review. Contracts,
product timing, authentication, independent currentness and reissuance policy
remain UNDETERMINED with Astra/User and existing contract owners. Existing
clock-skew partial effects and retained first refusals are preserved. No rollback,
production readiness, external finality or credential reissuance is claimed.

## Verification

All Python commands used `PYTHONDONTWRITEBYTECODE=1`. Named reference test
commands additionally used
`PYTHONPATH="$PWD/reference/booking_resale_admission"` from the repository root.
Commands below were actually executed; counts overlap and are not additive.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD origin/main` | Initially clean; correct branch; both SHAs equal the base above, unchanged at completion |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before and after work |
| `python3.12 -m unittest test_ticket_operations_session test_ticket_operations_cli` | First run: 13 tests, one failed test assertion about optional buyer on a held listing. Corrected the test to exercise the existing no-hold optional-buyer path. Rerun: PASS, 13 tests. No FSM/adapter/session semantics changed to satisfy the test |
| `python3.12 -m unittest test_resale_session test_resale_cli test_admission_session test_admission_cli test_resale_offer_source test_resale_offer_adapter test_presentation_source test_presentation_adapter test_admission_rejection_atomicity test_resale_rejection_atomicity` | PASS, 286 tests |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS, 522 tests, including existing HTTP-related tests |
| `python3.12 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS, 224 tests |
| `python3.12 -m unittest integration_gate.test_http_gate readiness.test_faults integration_gate.test_offline_limits` | PASS, 148 tests; an existing unclosed-file ResourceWarning was emitted; no public endpoint |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate; durability/performance not certified |
| `python3.12 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `/usr/bin/cargo --version`; `/usr/bin/rustc --version` | Existing system Cargo/rustc 1.85.1; no downloads or installation |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable, exit 101: offline cache lacks `serde`; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable, exit 101: offline cache lacks `serde`; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable, exit 101: system Cargo has no Clippy command |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Unavailable, exit 101: system Cargo has no fmt command |
| `git diff --check` | PASS |
| Final `python3.12 scripts/check_docs_index.py` | PASS after completing this record; scanned 329 / indexed 294 / allowlisted 35 |
| Inline Python `git ls-files --others --exclude-standard`, `ast.parse` on added Python files and trailing-whitespace checks | PASS, all 10 added files checked; all new Python files parse |
| Inline read-only Python Git-blob comparison, using `git ls-tree -r -z HEAD -- <protected paths>` and SHA-1 of each file with its Git blob header | PASS, 178 protected tracked blobs byte-identical to HEAD |
| `git diff --name-only HEAD` (inside the comparison) | Only existing tracked edits are the two authorized README files |
| `git ls-tree HEAD reference/v0.3-rc1` | Historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; working files byte-identical |

The four Cargo commands above ran sequentially with
`PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true CARGO_HOME=/tmp/kix-ticket-operations-cargo`.
This uses the available system tools without invoking rustup downloads. Missing
offline dependencies/components are unavailable checks, not passes. Rust source
is untouched; CI uses its pinned toolchain.

These applicable `protocol.yml` checkers each ran with `python3.12 scripts/<name>.py`
and separately with `--self-test`, through a sequential subprocess loop checking
each return code. All fourteen invocations passed:

| Script name | Plain result | Self-test result |
|---|---|---|
| `check_docs_index` | PASS, scanned 329 / indexed 294 / allowlisted 35 | PASS |
| `check_ci_test_discovery` | PASS, 7 reference suites / 8 Node tests / 4 modules; both new suites reached by existing discovery | PASS, 18 negative controls |
| `check_bra_evidence_map` | PASS, 39 rows; existing grades unchanged | PASS, 50 negative controls |
| `check_contract_error_codes` | PASS, 199 covered rows; no Class B/C additions | PASS |
| `check_openapi_contract` | PASS, 84 commands and existing pin unchanged | PASS |
| `check_integration_gate_openapi` | PASS, 84 commands; productionEndpoint/publicHost false | PASS |
| `check_ci_checker_wiring` | PASS, 35 scripts | PASS, 13 negative controls |

Each transcript also ran independently in a subprocess with this command:

```bash
python3.12 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
  --requests reference/booking_resale_admission/fixtures/ticket_operations_<scenario>.jsonl
```

| Scenario substituted | Actual result, asserted by the runner |
|---|---|
| `cancel` | Expected exit 1, empty stderr, 6 rows; errors `LISTING_LOCKED`, `LISTING_LOCKED` |
| `admission` | Expected exit 1, empty stderr, 7 rows; errors `ADMISSION_LOCKED`, `ALREADY_CONSUMED` |
| `transfer` | Expected exit 1, empty stderr, 16 rows; errors `STALE_VERSION`, `STALE_VERSION` |

The new CLI suite additionally executes each transcript through both files and
stdin, comparing every output row with the importable runner. The session suite
compares both session calls and CLI dispatch with independent direct public FSM
calls on an equivalent graph after every explicit request: receipts/errors,
canonical states, digests and journals match. Each adapted invocation fetches
once, including replays; pure views do not fetch. Source failure on replay never
uses a cached receipt or creates a follow-up.

## New evidence and changed paths

`test_ticket_operations_session.py` adds four composition tests: shared identities
and isolated constructions, independent clocks, per-request direct/CLI/session
parity for all transcripts, first-result replay/source failure/key conflict,
structural preconstruction rejection and publication only after setup succeeds.
`test_ticket_operations_cli.py` adds nine tests: exact fixture/setup/recording
fields, allowlisted setup prerequisites, caller values, fetch-time failures,
strict JSON, executable transcripts, all selectors' routing, structural stop and
exit/error/import behavior. Existing sufficient FSM and adapter tests are reused.

Complete changed-path list:

- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_fixture.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_cancel.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_admission.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_transfer.jsonl`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-02-plan-local-ticket-operations-desk/README.md`

## Deviations, protected paths and remaining gates

No functional deviation from the design. The supervisor-directed procedural
deviations are no fetch, commit, push, issue, PR, comments or hosted CI queries.
There is no new committed implementation/final task head; ending branch HEAD
remains `05ded3f73f29fdcd7734f27b0e07102b5888555a` with the changes above uncommitted.
Rust checks are unavailable as recorded; no installation/network workaround was
attempted. The full unchanged local HTTP regression ran successfully in addition
to the planned socket-free suites. No long job was launched in the background.

The final protected comparison covers the two kernel files, `reference/v0.3-rc1`,
`.aiops`, `docs/tasks`, `.github/workflows`, `docs/contracts`, `integration_gate`
and `sdk`. All 178 tracked blobs match HEAD. All other existing FSM, session,
fixture, adapter, source and test files remain unchanged; only the two README
files have tracked edits. Final locked blobs still match their required values.

No new contract violation or undefined behavior was found. Existing Class B
clock-skew partial effects remain characterized by the unchanged atomicity suite;
they are not repaired through synchronization or represented as rollback. After
transfer, reservation and resale versions differ and both admission presentations
remain refused, as the existing contract specifies. Timing, authentication,
currentness and reissuance decisions remain with Astra/User and contract owners.

| Remaining gate | Run ID / SHA | Actual state |
|---|---|---|
| Non-author A2 exact-final-head review | Unavailable | Pending supervisor; builder evidence is source-informed |
| Exact-final-head KTX kernel verification | Unavailable | Not run/queried; supervisor has not committed final head |
| Exact-final-head KIX protocol verification | Unavailable | Not run/queried; normal discovery and unchanged HTTP coverage remain required |
| Merge commit and post-merge main CI | Not applicable | No merge; User authorization still required |

Local implementation is ready for supervisor handoff, not a merge proposal.
No production runtime, durability, real funds, PG/bank/KYC, chain finality,
credential reissuance, authentication, distributed exclusivity, compensation,
seller payout or legal compliance is claimed. Follow-up candidates are the
existing undecided policies and external review/CI gates, not implicit work in
this node. No scope expansion or root DECISION_REQUIRED dependency was needed.

Before work, `git hash-object` matched both locked kernel blobs:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`quarantine_capacity.rs`).
