# Local resale request inputs

Task: `plan-local-resale-request-inputs`. The supplied node specification and
read-only design plan are the task input; no issue or `docs/tasks/` document exists.
This is not ASTRA program mode. Scope is the local Python desks, tests, synthetic
transcripts and documentation.

Observed local `origin/main`, task base and initial HEAD:
`1f4d28bb152eac61dd0b1d446eb8e788fa8dc098`.
Branch: `agent/kix-plan-local-resale-request-inputs`. Initial worktree was clean.
The supervisor prohibits all network actions, so `git fetch origin main` was not
run and remote freshness is unknown. No base change was made.

## Existing coverage (recorded before adding tests)

Paths in this table are under `reference/booking_resale_admission/`.

| Requirement | Existing coverage | Gap to cover |
|---|---|---|
| Adopted ticket, no startup offer, explicit continuation | Not covered for request inputs; recorded journeys in `test_resale_session.py::test_complete_explicit_flow_and_replay_after_close` | Empty-offer fixtures and executable file/stdin journeys |
| One delegation, result/error identity, zero fetches | Partial: `test_resale_session.py::test_direct_forwarding_preserves_receipt_and_exception_identity` for other methods | Opaque request inputs forwarded to `list_resale`, no source access or follow-up |
| Replay and changed-body conflict | Partial: `test_resale_offer_adapter.py::test_accepted_replay_key_conflict_competing_and_expired_replay_parity` | New boundary, retained refusals, replay after cancellation/expiry, recorded/direct cross-path replay |
| Version, holder, cap, expiry and locks | Sufficient FSM/adapter coverage: `test_rejected_offers_match_direct_errors_states_digests_and_journals`, `test_admission_lock_and_retained_refusal_after_lock_expiry_parity` in `test_resale_offer_adapter.py`; partial new-boundary coverage | Direct comparisons through new selector; null and explicit reservation binding |
| Economic/shared state | Partial: `test_ticket_operations_session.py::test_transcripts_session_and_cli_match_direct_graph_after_every_request` | Extend direct control and shared transcript with new selector |
| Strict fields and exits | Partial: structural/exit regressions in `test_resale_cli.py` and `test_ticket_operations_cli.py` | Each missing argument, extras and malformed shapes stop without dispatch |
| Suite/check discovery | Existing modules already discovered by CI | Run focused suites, full BRA/settlement discovery, architecture and applicable checkers |

## Implementation

`ResaleSession.list_resale_inputs` requires all nine caller fields, including an
explicit reservation binding or null. It returns exactly one existing FSM
`list_resale` invocation with unchanged values and exceptions. A strict local
JSONL selector returns the existing receipt envelope. The combined CLI already
routes resale requests through that dispatcher and required no production-code
change. Recorded-offer listing is preserved.

Two fresh fixtures retain the existing explicit issuance/adoption setup and
synthetic policy values but set `offers: []`. Shared presentation configuration
is preserved. Both eight-line transcripts list, replay, explicitly hold, release,
cancel, replay the first listing receipt, and read current listing/right state.
No operation is inferred or automatically followed up.

## Acceptance evidence

All paths below are under `reference/booking_resale_admission/`.

| Gap | New evidence |
|---|---|
| Exact unchanged forwarding, zero fetches, no follow-up | `test_resale_session.py::ResaleRequestInputsTests.test_exactly_one_call_opaque_inputs_receipt_and_exception_identity`: opaque fields, null/opaque binding, one `list_resale` call on success/domain/unexpected failure, receipt/exception identity, zero offer/payment calls; omitted Python binding fails before FSM access |
| Retained refusal keys, version/holder/cap/expiry/reservation errors | `ResaleRequestInputsTests.test_request_refusals_retained_keys_and_direct_fsm_parity`: null and explicit bindings, repeated refusals, corrected-body conflicts, fresh-key acceptance; canonical state, digest and journal match direct public FSM calls |
| Replay and competing sale lock | `ResaleRequestInputsTests.test_replay_after_cancel_and_expiry_and_competing_sale_lock`: every body/subject field changed under the accepted key conflicts; replay retains the first LISTED receipt after cancellation and expiry; competing refusal remains retained; ticket/settlement state unchanged |
| Admission lock | `ResaleRequestInputsTests.test_admission_lock_refusal_retained_after_lock_expiry`: direct-FSM parity before/after reservation clock advancement, retained refusal, fresh-key acceptance |
| Recorded-path compatibility | `ResaleRequestInputsTests.test_recorded_and_request_paths_share_existing_fsm_replay_identity`: both invocation orders replay one original FSM result and journal |
| File/stdin journeys and shared graph | `test_resale_cli.py::RequestInputsDeskChecks.test_request_inputs_empty_offers_file_stdin_and_direct_fsm_parity`, inherited by standalone/shared TestCases: full output equality, exit 0, separate explicit lifecycle steps, historical vs current state and per-request FSM graph snapshots. Existing `test_ticket_operations_session.py::test_transcripts_session_and_cli_match_direct_graph_after_every_request` also includes the new shared transcript |
| Strict fields and stop semantics | `RequestInputsDeskChecks.test_request_inputs_strict_fields_stop_before_any_dispatch`: remove every required argument/envelope field, add extra/offer_id fields and malformed shapes; exit 2, one error, no next-line execution/FSM listing/source fetch |
| Domain errors and exit 1 | `RequestInputsDeskChecks.test_request_inputs_domain_errors_continue_only_explicit_lines`: repeated stale-version/holder/cap/expiry refusals, corrected-body conflicts, fresh success/replay and competing lock; direct graph parity and executable stdin output for both desks |

Existing recorded transcripts, fixture parsing, duplicate JSON-key/nonfinite
input rejection, source failures and exit regressions run unchanged. These are
source-informed boundary comparisons, not independent implementations of the FSM.
Economic state comparisons exclude process-local retained receipt bookkeeping;
retained refusals are tested separately via replay/conflict behavior.

## Commands actually run and results

From repository root. Python verification used `PYTHONDONTWRITEBYTECODE=1`.
The focused command additionally used
`PYTHONPATH="$PWD/reference/booking_resale_admission"`.
Installed versions: Python 3.13.5; Rust toolchain 1.98.1 with Clippy/rustfmt.
No long job was launched in the shell background.

| Command | Actual result |
|---|---|
| `python3 -m unittest test_resale_session test_resale_cli test_resale_offer_source test_resale_offer_adapter test_ticket_operations_session test_ticket_operations_cli` | First run: 90 tests, 2 failing subtests in the new expiry expectation. Corrected the test to use the existing `OFFER_WINDOW_MS`, without changing FSM/implementation. Re-run: 90 tests, OK, exit 0 |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 688 tests, OK, exit 0 |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 224 tests, OK, exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | Dependency/architecture gate OK, exit 0 |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK, exit 0 |
| `python3 scripts/check_docs_index.py` and `--self-test` | Both exit 0; scanned 345, indexed 310, allowlisted 35 |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; 7 reference suites, 8 Node tests, 4 modules, 3 historical exclusions |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0; 35 checker scripts |
| `python3 scripts/check_bra_evidence_map.py` and `--self-test` | Both exit 0; 39 rows, 50 negative controls |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | Both exit 0; 199 covered rows |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Both exit 0; 84 existing commands, unchanged pin |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0; 84 existing commands, productionEndpoint/publicHost false |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Unavailable, exit 101 before compilation: cached crates.io package `bcs` missing (workspace resolution through `kix-bcs1`) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Unavailable, exit 101: same missing `bcs` cache |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Unavailable, exit 101: same missing `bcs` cache |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Pass, exit 0 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both required hashes match (below) |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs .aiops docs/tasks` | Exit 0; no protected-path changes |
| `git ls-tree -r HEAD reference/v0.3-rc1` before/after and `cmp /tmp/resale-protected-before.txt /tmp/resale-protected-after.txt` | Exit 0; same tracked tree manifest, with working bytes checked by diff above |
| `git ls-files --others --exclude-standard -- reference/v0.3-rc1 .aiops docs/tasks` | Exit 0, no added files in those paths |
| `git diff --check` | Pass, exit 0 |
| `git rev-parse HEAD` and `git rev-parse origin/main` | Both remain `1f4d28bb152eac61dd0b1d446eb8e788fa8dc098` |

The transcript tests actually execute both CLI programs with `--requests PATH`
and `--requests -` against the matching `*_request_inputs_session.json` fixture,
and compare full stdout and exit codes. They also run refusal streams through
each executable. No file/stdin outcome is inferred solely from in-process tests.

## Protected paths and complete changed-path list

| Locked file | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / same |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / same |

`reference/v0.3-rc1/**` remains byte-identical. No FSM, adapter, contract,
OpenAPI, SDK, CI, `.aiops/` or task document was changed.

Complete changed paths:

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/resale_session.py`
- `reference/booking_resale_admission/resale_cli.py`
- `reference/booking_resale_admission/test_resale_session.py`
- `reference/booking_resale_admission/test_resale_cli.py`
- `reference/booking_resale_admission/test_ticket_operations_session.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/fixtures/resale_request_inputs_session.json`
- `reference/booking_resale_admission/fixtures/resale_request_inputs.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_request_inputs_session.json`
- `reference/booking_resale_admission/fixtures/ticket_operations_request_inputs.jsonl`
- `validation/2026-11-04-plan-local-resale-request-inputs/README.md`

## Limitations, deviations and pending gates

Implementation follows the supplied design. The supervisor's explicit
no-network/no-publication instructions override session-start fetch: remote
freshness remains unknown. Local Python is 3.13.5 rather than CI's 3.12.
Rust test/Clippy execution is unavailable because the offline cache lacks `bcs`;
no dependencies were fetched, no CI/configuration was altered, and no unavailable
check is reported as passing. Untouched Move/ZK/localnet/provider/production paths
were not exercised; no broad repository CI success is claimed.

No new explicit contract violation or contract-undefined behavior was established.
The initial test error confused the fixture's selected expiry with the existing
FSM maximum window; the corrected test uses the existing gate constant.
No STOP dependency was needed and no product/legal value was decided.
Product policy remains **UNDETERMINED — Astra/User**; legal effects remain
**UNDETERMINED — User/legal**. No services, credentials, persistence, activation,
funds, external provider execution, chain finality, durability, legal compliance
or production-readiness evidence is supplied.

Delivery consists of uncommitted working-tree changes. Implementation/final task
commit: **not created**, per supervisor instruction; Git HEAD remains the base
SHA above. Merge commit and post-merge locked-blob/CI evidence: **not applicable**.
Exact-final-HEAD KTX kernel verification: **NOT_RUN**, run ID/status/conclusion
unavailable. Exact-final-HEAD KIX protocol verification: **NOT_RUN**, run
ID/status/conclusion unavailable. Non-author A2 exact-HEAD review and both
successful exact-HEAD workflows remain supervisor gates; local READY means
builder handoff only, with Rust checks explicitly unavailable. No commit, push,
PR, issue, comment, merge, branch or tag mutation was performed. User merge
authorization remains required.
