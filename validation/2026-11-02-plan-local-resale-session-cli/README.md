# Local resale session and CLI execution record

Task: `plan-local-resale-session-cli`; immutable task input is the supervisor's
node specification and design in this session, not a file under `docs/tasks/`.
No issue exists. Builder evidence is source-informed, not non-author A2 review.

## Baseline and boundaries

Local `origin/main`, base and initial task HEAD:
`590d68df770dc4af7ab8d0bd0788ae454eccd379`.
The supervisor forbids network/GitHub actions and commits; `git fetch origin main`
was therefore not run. Remote freshness is unverified. No base change occurred.
Implementation is delivered as an uncommitted worktree; final committed head,
KTX/KIX exact-head run IDs/status/conclusions and merge/post-merge evidence are
unavailable and remain supervisor/reviewer gates. READY means builder delivery,
not merge-ready. No independent review or hosted CI is claimed.

Before edits, working-file Git hashes matched both locks:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`kix-kernel/src/lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
Historical `reference/v0.3-rc1` HEAD tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Existing coverage mapping (recorded before new tests)

Paths below are under `reference/booking_resale_admission/`.

| Requirement | Existing coverage classification and exact evidence | New boundary gap |
|---|---|---|
| Complete list/hold/payment/bind/transfer/close journey | Partial: `test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential` covers machine lifecycle | Actual-machine fixture/session journey and executable JSONL transcript |
| Duplicate transfer and historical versus current views | Sufficient FSM coverage: above test; `test_returned_data_isolation.py::CopyIsolationCharacterizationTests.test_retained_snapshots_survive_later_transitions` | Session replay after close, no second version increment or journal entry |
| Holds, cancellation, competing listings | Partial at new boundary: `test_resale_fsm.py::ResaleFsmTests.test_buy_hold_is_optional_and_cancel_order_decides_the_race`; `test_resale_offer_adapter.py::ResaleOfferAdapterTests.test_accepted_replay_key_conflict_competing_and_expired_replay_parity` | Exact forwarding, unchanged refusal codes and explicit sequencing |
| Stale owner/version, expiry | Sufficient FSM coverage: `test_resale_fsm.py::ResaleFsmTests.test_stale_listing_policy_and_expiry_do_not_transfer` | Session/CLI propagation of existing errors |
| Bound uncommitted settlement, UNBOUND transfer | Sufficient FSM coverage: `test_resale_fsm.py::ResaleFsmTests.test_bound_transfer_waits_for_mock_commit_and_reconciles` and transfer test | No implicit commit/binding, unchanged settlement and reservation state |
| Source failure does nothing further | Sufficient adapter coverage: `test_resale_offer_adapter.py::ResaleOfferAdapterTests.test_fetch_failure_after_acceptance_never_returns_cached_receipt` and `test_absent_malformed_mismatched_and_fault_records_touch_no_fsm_or_keys` | Session one-fetch/no-follow-up and CLI explicit next-line behavior |
| Strict parsing, fixtures, pure views, importability | Not covered for resale session/CLI; admission equivalents exist in `test_admission_cli.py` | New resale boundary suites, malformed-input matrix and fresh graphs |
| Mock flags and regression/discovery | Partial: existing `test_resale_fsm`, `test_resale_offer_source`, `test_resale_offer_adapter`, `test_open_items` | Preserve all flags and run existing suites/checkers unchanged |

## Commands and results

All commands ran from the repository root, in the foreground. Python validation
used `PYTHONDONTWRITEBYTECODE=1`. Named booking-module commands additionally used
`PYTHONPATH="$PWD/reference/booking_resale_admission"`. No test failed; only
unavailable Rust tooling/dependencies prevented the ancillary Cargo checks.

| Command actually run | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main`; `git rev-parse HEAD` | Initial worktree clean; both SHAs equal the base above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before and after |
| `git ls-tree HEAD reference/v0.3-rc1` | Historical tree matches the value above |
| `python3 -m unittest test_resale_fsm test_resale_offer_source test_resale_offer_adapter` | PASS, 26 tests; existing files unchanged |
| `python3 -m unittest test_resale_session test_resale_cli` | PASS, 23 tests initially and on final rerun after tightening setup exception type assertion |
| `python3 -m unittest test_resale_rejection_atomicity test_returned_data_isolation test_open_items` | PASS, 127 tests |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS, 496 tests, including existing HTTP-related coverage |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS, 224 tests |
| `python3 reference/booking_resale_admission/resale_cli.py --fixture reference/booking_resale_admission/fixtures/resale_session.json --requests reference/booking_resale_admission/fixtures/resale_requests.jsonl` | Exit 0; twelve JSON output rows; same transcript verified through stdin in the new tests |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults integration_gate.test_offline_limits > /tmp/kix-resale-session-gate-tests.log 2>&1` | PASS, 148 tests; existing loopback HTTP tests unchanged; no public endpoint |
| `python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate; durability/performance not certified |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo --version` (default rustup shim) | Unavailable: read-only `/home/box/.rustup/update-hashes`; no toolchain installed by this task |
| `/usr/bin/cargo --version`; `/usr/bin/rustc --version` | System Cargo/rustc 1.85.1 available |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` with offline environment below | Exit 101: missing cached crates.io `serde`; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` with offline environment below | Exit 101: no `clippy` command installed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` with offline environment below | Exit 101: no `fmt` command installed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` with offline environment below | Exit 101: missing cached `serde`; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` with offline environment below | Exit 101: no `clippy` command installed |
| `git diff --check` | PASS |
| `python3` inline read-only Git-blob comparison using `git ls-tree -r -z HEAD -- <protected paths>` and SHA-1 of each working file with Git blob header | PASS, 178 protected tracked blobs byte-identical; all other tracked edits limited to the two authorized README files |
| `git diff --exit-code HEAD -- runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1 .aiops docs/tasks .github/workflows docs/contracts` | PASS, protected paths unchanged |

The five Cargo validation commands were each actually invoked with
`PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true CARGO_HOME=/tmp/kix-resale-session-cargo`.
This selects the existing system compiler without the read-only rustup shim and
prevents dependency network access. No dependency/tool download was attempted.
These are unavailable checks, not passes. Python code and documentation are the
only touched implementation paths; no Rust source changed.

The following exact checker loop ran; all nine plain checks and all nine
self-tests passed (18 successful commands):

```bash
export PYTHONDONTWRITEBYTECODE=1
for check in check_docs_index check_ci_test_discovery check_ci_checker_wiring check_bra_evidence_map check_settlement_evidence_map check_contract_error_codes check_read_model_source_map check_openapi_contract check_integration_gate_openapi; do
  python3 "scripts/$check.py" || exit "$?"
  python3 "scripts/$check.py" --self-test || exit "$?"
done
```

Final plain `check_docs_index.py` and `check_ci_test_discovery.py` reruns also passed.
Discovery found both new suites through the existing CI suite loop. No workflow
was edited. Evidence-map grades/counts, OpenAPI pins and source anchors remain
unchanged; these checks do not promote R01–R04 status.

## New evidence and changed paths

`test_resale_session.py` supplies seven focused tests for exact receipt/exception
forwarding, a complete actual-machine journey, replay after close, explicit
UNBOUND flow, competing/released/cancelled listings, stale/expired refusals,
independent clocks, detached pure views and source failure without follow-up.
`test_resale_cli.py` supplies sixteen tests for actual fresh fixture graphs,
strict preconstruction validation, no partially published setup, uncommitted
settlement refusal, deferred recording validation, exact dispatch/input parsing,
file/stdin transcript execution, error continuation and importability. Existing
FSM, source, adapter and HTTP test files remain byte-identical.

Complete changed-path list:

- `reference/booking_resale_admission/resale_session.py`
- `reference/booking_resale_admission/resale_fixture.py`
- `reference/booking_resale_admission/resale_cli.py`
- `reference/booking_resale_admission/fixtures/resale_session.json`
- `reference/booking_resale_admission/fixtures/resale_requests.jsonl`
- `reference/booking_resale_admission/test_resale_session.py`
- `reference/booking_resale_admission/test_resale_cli.py`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-11-02-plan-local-resale-session-cli/README.md`

## Deviations and final gates

No functional design deviation. The loader reuses the existing admission setup
field schema for the three allowed machines, excluding admission requirements;
it does not require settlement binding. The happy fixture deliberately exercises
UNBOUND primary issuance and a separately configured resale mock settlement.
Recorded offer text remains fetch-validated by the unchanged source/adapter.

Procedural deviations are supervisor-directed: no fetch, commit, push, issue,
PR, GitHub comment or CI query. The final committed implementation head does not
exist yet. Initial and ending branch HEAD remain the base SHA above. Ancillary
Rust checks could not execute due to missing offline dependencies/components;
network installation is prohibited. All Python acceptance/regression and
applicable documentation/discovery checks passed, including unchanged HTTP tests.

| External gate | Run ID | Status / conclusion |
|---|---|---|
| Non-author A2 exact-final-head review | Unavailable | Pending supervisor orchestration; builder tests are not independent review |
| Exact-final-head KTX kernel verification | Unavailable | Not run/queried; no implementation commit yet |
| Exact-final-head KIX protocol verification | Unavailable | Not run/queried; no implementation commit yet |
| Merge commit and post-merge main CI | Not applicable | No merge |

The final read-only comparison covered the two kernel locks, `reference/v0.3-rc1`,
`.aiops`, `docs/tasks`, `.github/workflows`, `docs/contracts`, `integration_gate`
and `sdk`: 178 tracked blobs matched HEAD. `git diff --name-only HEAD` additionally
confirmed that only the two authorized existing README files changed.
Both locked working-file blobs still match their required values. Historical
reference files, FSMs, contracts, HTTP, SDK, catalogue, `.aiops/`, task documents
and CI are unchanged. No new contract violation or contract-undefined semantics
were found. Existing Class B characterizations remain unchanged. Remaining work
is supervisor publication, non-author A2 review and successful exact-final-head
KTX/KIX workflows (normal HTTP coverage included), followed by user authorization
and post-merge checks if merged. This delivery does not propose merge.

## Limitations and remaining gates

No FSM/contract changes are authorized. All product values remain UNDETERMINED
with Astra/User and contract §7.1 owners. Fixture values are synthetic inputs.
No production durability, real funds, PG/bank/KYC, chain finality, credential
reissue, authentication, cross-channel exclusivity, compensation, seller payout,
legal compliance or production readiness is claimed. R01–R04 status is unchanged.
Existing Class B internal-fault/clock-skew characterizations remain; fixture
construction is not cross-machine rollback. No new contract violation is claimed.
