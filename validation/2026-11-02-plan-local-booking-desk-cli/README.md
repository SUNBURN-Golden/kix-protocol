# Local booking desk validation

Node: `plan-local-booking-desk-cli`. Task input is the supervisor's supplied node
specification and design; no issue or task document exists. Builder-authored,
source-informed evidence; no independent A2 review claim.

## Baseline and preservation

Branch: `agent/kix-plan-local-booking-desk-cli`.
Initial HEAD and locally observed `origin/main`:
`41ace611f4a012d16accc86794087690b87e114e` (no local delta).
The supervisor prohibits network/GitHub actions, overriding the session-start
fetch; remote freshness is unverified. No commits, pushes or publication are made.
Implementation and final committed head remain supervisor-owned; current HEAD
identifies the baseline, not the uncommitted implementation. No merge occurred.
Exact-head KTX/KIX run IDs/status/conclusions and post-merge CI: not available.
Non-author A2 exact-head review and successful full workflows remain merge gates.

Before work, `git hash-object` returned the required locked blobs:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Historical `reference/v0.3-rc1` baseline tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Existing coverage map (inspected before new tests)

Paths below are under `reference/booking_resale_admission/`.

| Requirement | Existing evidence and classification | Boundary gap addressed |
| --- | --- | --- |
| Registration/hold/confirmation separate from payment/issue | Partially covered overall; FSM sufficient: `test_reservation_fsm.py::test_unbound_issue_is_memory_evidence_without_economic_finality` | Actual session and runnable confirm transcript stopping before payment |
| Overlap/release/reacquisition | Partially covered overall: `test_reservation_fsm.py::test_overlapping_holds_and_replay_do_not_double_book` | Session/CLI history including retained refusal and explicit fresh key |
| Pre-payment cancellation | Partially covered overall: `test_reservation_fsm.py::test_cancel_before_payment_frees_and_payment_blocks_compensation` | Cancel transcript and freed slot |
| Price mismatch | Partially covered overall: `test_primary_price_binding.py::test_off_price_amounts_rejected_at_boundaries` | Forward unchanged rejection/state/journal |
| Expiry without release | Partially covered overall: `test_reservation_fsm.py::test_expiry_does_not_release_until_an_explicit_release` | Boundary transcript with explicit time/release |
| Replay/conflict | Partially covered overall: overlap test and `test_reservation_fsm.py::test_same_key_conflict_does_not_move_phase` | Historical confirmation replay after cancellation |
| Rejection atomicity | Sufficient FSM regression: unchanged `test_reservation_rejection_atomicity.py` | Re-run; no duplicate atomicity implementation |
| Session parity | Not covered | Compare receipts/errors, canonical state, digest and journals after each explicit call |
| Non-mutating views | Sufficient FSM evidence, partial boundary: `test_returned_data_isolation.py::test_views_are_detached` | Session/CLI view snapshots |
| Strict input/no automatic actions | Not covered for booking | Exact schemas, duplicate keys/nonfinite/invalid JSON, prerequisites and one-call forwarding |
| Transcripts/discovery/docs | Not covered for booking | File/stdin subprocess runs and offline discovery/document guards |

## Results

Actual execution results and final preservation checks follow.

### Commands actually run

`PYTHONDONTWRITEBYTECODE=1` was used for Python verification. Narrow module runs
also used `PYTHONPATH="$PWD/reference/booking_resale_admission"`. Full discovery
uses the workflow's command without that extra path (see deviation below).
All commands ran in the foreground through the execution tool; no background jobs.

| Command | Actual result |
| --- | --- |
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean, expected branch; HEAD/local main both `41ace611f4a012d16accc86794087690b87e114e` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both required hashes match (listed above) |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |
| `python3 -m unittest test_booking_session test_booking_cli` (first run) | 13 tests; 1 error: test supplied expiry 1900000 with custom clock 8, exceeding existing window; corrected test input to explicit 900008 |
| `python3 -m unittest test_booking_session test_booking_cli` (after correction) | Exit 0; 13 tests passed |
| `python3 -m unittest test_reservation_fsm test_reservation_rejection_atomicity test_primary_price_binding test_returned_data_isolation test_open_items` | Exit 0; 96 tests passed, existing files unchanged |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` (with extra `PYTHONPATH`, initial run) | Exit 1 before execution: same-named settlement `test_contract_error_codes` imported from wrong directory |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` (workflow environment, no extra `PYTHONPATH`) | Exit 0; 509 tests passed, including existing loopback HTTP coverage |
| `python3 scripts/check_docs_index.py` and `--self-test` | Both exit 0 |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; new suites reached by unchanged workflow discovery |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0 |
| `python3 scripts/check_bra_evidence_map.py` and `--self-test` | Both exit 0 |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | Both exit 0 |
| `python3 scripts/check_read_model_source_map.py` and `--self-test` | Both exit 0 |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Both exit 0 |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; declared dependency gate OK; no durability/performance certification |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 1; pinned rustup unavailable: update-hash directory read-only |
| `/usr/bin/cargo --version`; `/usr/bin/rustc --version`; installed component inspection | System Cargo/rustc 1.85.1; pinned 1.98.1 absent, no system Clippy/rustfmt components |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` with system PATH/offline environment below | Exit 101; missing cached `const-oid` dependency; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` with system PATH/offline environment | Exit 1; component dispatch reaches unavailable rustup (read-only update-hash directory) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` with system PATH/offline environment | Exit 1; unavailable rustup/component, same read-only failure |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` with system PATH/offline environment | Exit 101; missing cached `const-oid`; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` with system PATH/offline environment | Exit 1; unavailable rustup/component, same read-only failure |
| `git diff --check` | Exit 0 |
| Python preservation check using `git ls-tree -rz HEAD reference/v0.3-rc1` and Git blob SHA-1 over file bytes, plus complete file-set comparison | Exit 0; all 108 historical files byte-identical, no additions/removals |
| Python changed-path allowlist check using `git diff --name-only` and `git ls-files --others --exclude-standard` | Exit 0; exactly the 10 authorized paths listed below |

System Rust attempts used `PATH=/usr/bin:/bin CARGO_NET_OFFLINE=true
CARGO_TARGET_DIR=/tmp/kix-booking-desk-target`. No packages/toolchains were installed
and no dependency/network fetch was authorized. These Rust results are unavailable
verification, not passes. Rust sources and workflows are untouched.

### New evidence and changed paths

- `reference/booking_resale_admission/booking_session.py` — thin explicit-input boundary; delegates all eight operations to the injected machine, one call at a time.
- `reference/booking_resale_admission/booking_cli.py` — strict local selector/argument validation, shared JSON decoder, receipt/error output and exit handling.
- `reference/booking_resale_admission/fixtures/booking_confirm.jsonl` — explicit registration, buyer hold, separate confirmation and views.
- `reference/booking_resale_admission/fixtures/booking_cancel.jsonl` — pre-payment cancellation and historical confirmation replay/current view.
- `reference/booking_resale_admission/fixtures/booking_boundaries.jsonl` — explicit competing/released holds, retained refusal, fresh keys, price mismatch, expiry and cancellation/replay.
- `reference/booking_resale_admission/test_booking_session.py` — 6 focused tests: actual-machine differential histories, one-call forwarding/error identity, clock and quote prerequisites without bound keys, FSM-owned limits and detached non-mutating views.
- `reference/booking_resale_admission/test_booking_cli.py` — 7 focused tests: file/stdin transcripts, direct-FSM parity after every line, exact schemas/all excluded FSM selectors, strict JSON and stop behavior, domain continuation, files/usage/imports.
- `reference/booking_resale_admission/README.md` — complete interface/schema/usage and transcript outcomes/limitations.
- `docs/README.md` — discovery link only.
- `validation/2026-11-02-plan-local-booking-desk-cli/README.md` — this coverage and execution record.

After work both locked blobs match their required hashes. The historical tree's
108 files are byte-identical to baseline. Existing FSMs, tests, contracts,
HTTP/SDK/catalogues, workflows, `.aiops/` and `docs/tasks/` have no edits.
Final-merge preservation checks: not applicable (no merge).

### Deviations, limits and outstanding gates

No implementation deviation from the supplied design. Session clock initialization
also accepts successful explicit clock replay, preserving unchanged FSM replay
semantics and current time. The fixture loader helpers are reused without loading
any admission/resale fixture or initializing excluded lifecycle operations.

Execution deviations: fetch omitted under the supervisor's explicit network ban;
full discovery drops the plan's exported `PYTHONPATH` to match CI and avoid its
existing module-name collision; Rust verification unavailable for the toolchain
and offline-cache reasons recorded above. No CI or environment configuration was
changed to hide these limitations.

No contract violation found, and no new contract-undefined behavior assigned a
meaning. The boundary's local clock/quote prerequisites are node-specific input
requirements, not changes to reservation semantics. Existing expiry, retained
rejection and historical-receipt behavior is characterized against the unchanged
FSM. Evidence is source-informed and synthetic, not clean-room independent.

Confirmation remains separate from payment and issuance: payment/issuance/
settlement/right are null in the confirmation transcript. No payment observation,
lookup, settlement binding, refund, issuance, admission or automatic follow-up is
exposed. The payment–reservation handoff remains blocked. No authentication,
external authority, money, PG/bank/KYC, Sui execution, persistence, durability,
distributed exclusivity, legal compliance, production readiness or activation was
tested or claimed. This is sequential in-memory local evidence only.

B01/B02/B04 labels and §7.1 unresolved policy inputs/owners remain unchanged.
Approved TTLs, discounts, provider authority, authentication and compensation
remain UNDETERMINED with Astra/User and external owners. Follow-up candidates are
those existing owner decisions and the separately blocked handoff, not work
implicitly opened by this node.

Builder state: implementation ready for supervisor handoff; **not merge-ready**.
Supervisor must establish the implementation/final SHA after committing and obtain
non-author A2 exact-head review and successful KTX/KIX workflows. No run IDs,
remote freshness, final committed SHA or post-merge success are asserted here.
