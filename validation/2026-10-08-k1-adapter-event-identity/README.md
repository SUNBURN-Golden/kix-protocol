# k1-adapter-event-identity — I06 draft evidence

Node: `k1-adapter-event-identity`. Document only. No adapter code.
Issue context: SUNBURN-Golden/kix-protocol #102 (read-only; this session posted nothing).
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`7481b0e16ce9b903abbffa62249bb91cd9e63cfe`.
Branch: `agent/kix-k1-adapter-event-identity`.
This session did not commit, push, open a PR, or comment. There is no implementation
commit SHA and no hosted CI run. Local results are not exact-head CI.

## What changed

| Path | Change |
|---|---|
| `docs/contracts/ADAPTER_EVENT_IDENTITY.md` | New draft 0.1. |
| `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md` | I06 row only. Status stays 미완결. Points at the draft. |
| `docs/contracts/PG_TOSS_CARD_PROFILE.md` | One sentence in §6. Identity relations live in the new draft. No provider value changed. |
| `validation/2026-10-08-k1-adapter-event-identity/README.md` | This record. |

`새로 실입력까지 완결된 행: 0` is unchanged. Locked kernel blobs and
`reference/v0.3-rc1/**` are unchanged.

## Coverage (AGENTS §7)

No new tests. The draft cites existing kernel tests; the names were checked in
`runtime/crates/kix-kernel/tests/` before citation.

| Requirement | Coverage |
|---|---|
| Kernel event dedupe, same-id conflict, duplicate observation, operation uniqueness, quarantine replay | Sufficient: `transitions.rs::event_deduplication_and_economic_effect_deduplication_are_separate`, `::same_event_different_payload_preserves_conflicting_evidence`, `::accepted_duplicate_observation_advances_time_without_reapplying_capture`, `::duplicate_external_operation_cannot_fund_two_orders`, `quarantine_capacity.rs::original_event_and_command_replays_never_clear_quarantine` |
| Adapter derivation of `event_id` / `evidence_hash`, binding record, UNMATCHED | Not covered. No adapter exists. |
| Toss ID stability and webhook signature | Not covered. I02–I05, I08, TM04, TM05 stay open. |

A local count of draft §5 found 11 data rows, each with four cells and a non-empty
마지막 칸 (절대 금지).

## Commands actually run

Working directory: repository root. Python 3.13.5 (`tomllib` present).
Cargo 1.98.1. Node v20.19.2 is present; `sui` and `snarkjs` are absent; `.venv` is absent.
`scripts/bootstrap.sh`, Sui localnet, ZK setup, and storage-probe steps were not run.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` before, after, and at this uncommitted tree's HEAD (HEAD is still the base). |
| `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `git diff --stat origin/main -- reference/v0.3-rc1` | Empty. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. Per-suite `ok` lines sum to 128 passed, 0 failed: bcs1 3, golden_vectors 4, feature-ir 5, audit_regressions 8, schema_bound 18, feature-semantics 6, kernel lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32, kix-types 6. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. 34 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 20 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. 43 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. 20 tests, OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. commands=40, pin OK. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. commands=40, productionEndpoint=false, publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. pass. |

## Not run locally

Pinned CLI install (`scripts/bootstrap.sh`), `scripts/verify_runtime.py`, commerce/canonical
verifiers, storage probes, `run_localnet.py`, and ZK `setup:zk` / `test:zk`.
The environment has no Sui CLI, no snarkjs, and no `.venv`. Node is v20.19.2, not the
workflow's Node 24. Those steps were not installed for this document draft.
`docs/contracts/*` is a verifier input, so hosted CI runs full verification.
That hosted result does not exist yet: this session did not publish a head.

## Deviations from the design plan

- The plan numbered both the case matrix and the times section as 5. The draft uses
  §5 case matrix, §6 times and binding (§6.1, §6.2), §7 PG boundary, §8 UNDETERMINED.
  That keeps the plan's acceptance map: relations through the PG boundary in §3–§7,
  and the open-input register in §8.
- Roadmap §3.3 still says merge 「자동(M1·Fable)」. Delegation row 35 says
  `contract_change=YES`, 대표님, and the node input says `user_merge=true`.
  The draft follows the delegation table and the node input. The roadmap file was not edited.

## Non-claims

No Toss behavior, signature, durability, exactly-once, provider finality, or production
readiness. I06 is not complete. No contract violation was found. Open provider facts
stay UNDETERMINED with the owners named in the draft. Option A versus B, the alias
method, schema id allocation, and any out-of-order wait number stay
DECISION_REQUIRED · Astra inside the draft. No root `DECISION_REQUIRED.md`.
No new kernel command.
