# Local admission session and CLI evidence

Node: `plan-local-admission-session-cli`. Task document: user-supplied node and
read-only design specification (no issue or `docs/tasks/` file for this node).
Non-ASTRA builder session; supervisor owns publication.

Observed local `origin/main`, task base and unchanged HEAD:
`fd3333580c0c2ed9186bb3b6917f0077a75a94f3`.
Fetch omitted under the explicit supervisor prohibition on network actions;
remote freshness is unverified. Final implementation is an uncommitted working
tree; implementation/final commit SHA and both exact-head CI runs are pending
supervisor publication. No merge or post-merge evidence exists for this task.

## Coverage mapping recorded before new tests

| Requirement | Existing coverage and classification | New gap |
|---|---|---|
| Separate authorization/consume and duplicate without effect | Sufficient FSM/adapter coverage: `test_admission_fsm.AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`, `test_presentation_adapter.PresentationAdapterTests.test_receipts_replay_and_effects_match_direct_fsm` | Session and CLI path not covered |
| Expiry, stale presentation, conflicting key codes | Sufficient below CLI: adapter `test_expired_authorization_cannot_consume_or_change_state`, `test_stale_version_holder_and_conflicting_keys`, `test_successful_key_conflicts_and_consume_never_auto_authorizes` | CLI error serialization not covered |
| Source faults cause no follow-up | Partial: adapter `test_missing_malformed_faults_precede_all_machine_access`, `test_settlement_flags_are_still_checked_for_each_operation`, one-fetch tests | Session fault behavior with each configured authority source |
| Current views versus first receipts | Sufficient FSM/adapter: `test_returned_data_isolation` and adapter `test_receipts_replay_and_effects_match_direct_fsm` | Session view and receipt delegation |
| Mock/non-production flags | Sufficient below session: adapter equivalence and `test_open_items` | Session/CLI forwarding |
| Missing inputs without defaults | Not covered for new fixture/CLI | Strict schema, explicit setup graph, mandatory arguments, errors/exits |
| Docs/discovery and unchanged regressions | Existing repository checkers and admission regressions | New modules discovery and scoped local checks |

New evidence is builder-authored, source-informed, synthetic and socket-free;
not independent review. Preserve the unchanged HTTP suite for normal CI.

## Delivery and new evidence

The [session documentation](../../reference/booking_resale_admission/README.md)
describes the strict fixture schema, the five existing method selectors and
expected transcript. New `test_admission_session.py` covers explicit real-machine
effects, no implicit authorization/consumption, first receipts/current views,
all existing mock flags, exact receipt/exception identity, presentation faults,
read failures from each configured authority and clock delegation. New
`test_admission_cli.py` covers caller identifiers/roles, independent fixture loads,
all mandatory fixture/setup/presentation/request fields, omitted clocks and
bindings, strict JSON, rejected setup without partial session publication,
operation allowlists, source fault markers, subprocess/stdin transcript,
unchanged domain codes, replay journals, exit statuses and importability.
Source failure tests inject faults before mutation; they do not imply general
cross-machine rollback. Unexpected programming errors propagate.

Complete changed-path list:

- `reference/booking_resale_admission/admission_session.py`
- `reference/booking_resale_admission/admission_fixture.py`
- `reference/booking_resale_admission/admission_cli.py`
- `reference/booking_resale_admission/fixtures/admission_session.json`
- `reference/booking_resale_admission/fixtures/admission_requests.jsonl`
- `reference/booking_resale_admission/test_admission_session.py`
- `reference/booking_resale_admission/test_admission_cli.py`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-02-plan-local-admission-session-cli/README.md`

## Actual verification commands and results

Commands ran from repository root. Python test commands used
`PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH="$PWD/reference/booking_resale_admission"`.
Default `python3` is 3.13.5. Tests and final transcript used installed
`python3.12` 3.12.15, matching protocol CI's Python minor version. Rust/Cargo
1.98.1 match CI. Cargo ran offline without installation. No shell background
jobs, commits, pushes or GitHub/network actions were used.

| Command actually run | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; expected `agent/kix-plan-local-admission-session-cli`; both SHAs equal the base above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | Both required blobs match; see lock table below. |
| `git ls-tree -r HEAD reference/v0.3-rc1 > /tmp/kix-admission-reference-before.txt` | Historical manifest recorded before edits. |
| `python3 reference/booking_resale_admission/admission_cli.py --fixture reference/booking_resale_admission/fixtures/admission_session.json --requests reference/booking_resale_admission/fixtures/admission_requests.jsonl > /tmp/kix-admission-transcript.jsonl` | First smoke run exit 2: `PAYMENT_BINDING_CONFLICT` from accidentally reused payment reference on the second fixture ticket. Gave ticket 2 a distinct caller-supplied synthetic payment reference; next run expected exit 1, 14 rows and three intended request rejections. No FSM change. |
| `python3.12 -m unittest test_admission_session test_admission_cli` | First run: 19 tests, one test error (`KeyError` from looking for clock metadata in the reservation per-ticket view). Corrected the test to use public canonical state. Second run: 19 tests PASS. |
| `python3.12 -m unittest test_presentation_source test_presentation_adapter` | PASS, 19 tests, existing suites unchanged. |
| Selected socket-free regression command below | PASS, 104 tests. |
| `python3.12 reference/booking_resale_admission/admission_cli.py --fixture reference/booking_resale_admission/fixtures/admission_session.json --requests reference/booking_resale_admission/fixtures/admission_requests.jsonl > /tmp/kix-admission-transcript-312.jsonl` | Expected exit 1; transcript has explicit conflict, stale-version and expired-authorization rejections. Subprocess assertions verify all 14 rows. |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | PASS; scanned=325 indexed=290 allowlisted=35. |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | PASS; 21 booking suite test files reached by existing directory discovery; 18 negative controls. |
| `python3.12 scripts/check_bra_evidence_map.py` and `--self-test` | PASS; 39 rows/headings, 219 citations; 50 negative controls. |
| `python3.12 scripts/check_contract_error_codes.py` and `--self-test` | PASS; 199/199 covered error rows; self-tests pass. |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | PASS; 84 commands, pin unchanged; self-tests pass. |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | PASS; 84 commands, productionEndpoint=false/publicHost=false. |
| `python3.12 scripts/check_ci_checker_wiring.py` and `--self-test` | PASS; 35 scripts; 13 negative controls. |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS; declaration/dependency gate, not durability certification. |
| `python3.12 scripts/test_runtime_architecture.py` | PASS, 7 tests. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked > /tmp/kix-admission-kernel-tests.log 2>&1` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings > /tmp/kix-admission-kernel-clippy.log 2>&1` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked > /tmp/kix-admission-workspace-tests.log 2>&1` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings > /tmp/kix-admission-workspace-clippy.log 2>&1` | PASS, exit 0. |
| `git diff --exit-code HEAD --` protected/out-of-scope paths listed below | PASS, no tracked changes. |
| Read-only Python `git ls-tree -rz HEAD -- reference/v0.3-rc1`, per-file `git hash-object --`, complete working-tree path comparison and both locked blob comparisons | PASS: all 108 historical files byte-identical with no added historical files; both locks match. Historical tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; HEAD unchanged. |
| `git diff --check` | PASS. |

The protected/out-of-scope diff checked both locks, historical tree, `.aiops`,
`docs/tasks`, `docs/contracts`, `sdk`, `integration_gate`, `.github`, all three
booking FSMs, `mock_gates.py`, existing presentation adapter/source/example and
presentation tests, plus `test_admission_fsm.py`. No CI or HTTP test edits.
Raw temporary runtime logs under `/tmp/kix-admission-*` are diagnostic output,
not committed evidence. File reads and `rg` searches inspected the prescribed
entry documents, governance, control-plane pointer/client pin, existing
contracts/evidence, setup signatures, source/FSM behavior and both workflows.

Selected unchanged socket-free regressions actually run:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission"
A=test_admission_fsm.AdmissionFsmTests
python3.12 -m unittest \
  "$A.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version" \
  "$A.test_transfer_then_entry_rejects_both_presentations" \
  "$A.test_listing_and_cancel_order_against_entry" \
  "$A.test_expired_authorization_is_replaced_once" \
  "$A.test_external_sources_fail_closed_without_being_read" \
  "$A.test_settlement_commit_is_not_entry_and_a_granted_flag_rejects" \
  "$A.test_restart_replays_journal_and_retry_is_duplicate" \
  test_admission_rejection_atomicity test_returned_data_isolation test_open_items
```

Checker loop actually run (each plain check and self-test passed):

```bash
export PYTHONDONTWRITEBYTECODE=1
for check in check_docs_index check_ci_test_discovery \
  check_bra_evidence_map check_contract_error_codes \
  check_openapi_contract check_integration_gate_openapi; do
  python3.12 "scripts/$check.py"
  python3.12 "scripts/$check.py" --self-test
done
```

## Protected bytes and remaining gates

Both locked blobs matched before and after implementation:

| Path | Required and actual Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

No explicit contract violation discovered. Existing class-B clock-skew and
post-mutation fault characterizations are preserved by the unchanged regression
selection. No new lifecycle semantics or product policy is defined. Timing,
identity, revocation and independent currentness remain **UNDETERMINED** with
Astra/User and existing contract owners. P03 remains **설계중**.

Design notes/deviations: the plan says “six” selectors but lists five; the
implementation exposes exactly the five named existing methods. Strict decoding
also rejects JSON exponent overflow (`1e999`), which Python otherwise turns into
infinity. Explicit complete fixture bindings require non-null reservation/quote
identifiers; this narrows synthetic fixture setup only and does not change FSM
method defaults. The accidental duplicate payment fixture and incorrect clock
assertion were corrected in allowed files, with subsequent checks passing.
Procedural deviations: no fetch under supervisor instructions; no commit or
GitHub publication, so final implementation SHA/CI remain pending.

| Required external evidence | Run ID | Status / conclusion |
|---|---|---|
| Non-author exact-final-head review / A2 | Unavailable | Pending supervisor orchestration; these tests are not independent review. |
| Exact-final-head KTX kernel verification | Unavailable | Not run/queried; implementation commit not yet created. |
| Exact-final-head KIX protocol verification | Unavailable | Not run/queried; implementation commit not yet created. |
| Merge commit / post-merge main CI | Not applicable | No merge. |

No full booking-suite or full protocol success is claimed. Preserve the full
unchanged HTTP suite and run it in normal exact-final-head CI. No hardware,
paid services, secrets, real provider calls, real funds, public endpoints, Sui
networks, persistence, storage engine or production runtime were required.
No production durability, distributed fencing, venue/bank exactly-once, chain
finality, legal compliance or production-readiness claim is made.
Builder handoff is locally READY; merge readiness is not established. Remaining
work is supervisor publication, non-author exact-final-head review/A2 and
completed/success KTX/KIX workflows including unchanged HTTP coverage, followed
by user-only merge authorization and post-merge checks if merged.
