# AI delegation authority contract and in-memory mock

Offline check for `docs/contracts/AI_DELEGATION_AUTHORITY.md` draft 0.1
and `reference/ai_delegation/`.
This note does not revise a task document under `docs/tasks/` and does not
promote ORIGINAL_32 labels. F04 and E06 stay **설계중**.

Issue #97. Not an ASTRA program-mode session. No delivery marker was posted.

## Session base

`git fetch origin main` then `git rev-parse origin/main HEAD`.

- `origin/main`: `d71b4117741f596e2b618ed1c32a42597bc0980b`
- branch `agent/kix-ai-delegation-contract-mock` HEAD: the same SHA
- The new files are uncommitted. This session does not commit or push.
- There is no new Git head, so there is no exact-head GitHub Actions run.

Locked blobs before and after, `git hash-object`:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 runtime .github .aiops docs/tasks docs/contracts/openapi sdk`
printed nothing and exited 0.

## Commands and results

Working directory: repository root. Python 3.13.5. Rust 1.98.1.
Node v20.19.2 is present. `sui` and `snarkjs` are absent. `.venv` is absent.

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -v` | 22 tests, OK (`Ran 22 tests in 0.031s`) |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 34 tests, OK (`Ran 34 tests in 2.380s`) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 20 tests, OK (`Ran 20 tests in 0.012s`) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 43 tests, OK (`Ran 43 tests in 0.188s`) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 20 tests, OK (`Ran 20 tests in 0.032s`) |
| `python3 scripts/check_openapi_contract.py` | exit 0 |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0 |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0 |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK (`Ran 7 tests in 0.187s`) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. Each package printed `test result: ok`, including `kix-kernel` tests `contract_edge_cases`, `contract_invariants`, `e4_state_model`, `observation_slots`, `performance_harness`, `quarantine_capacity`, `transitions` |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |

The 22-test count is this run only. It is not CI for a commit, and it is not an
implementation of AI delegation.

## Not run

`scripts/bootstrap.sh` was not executed. Its first two guards were executed on
their own and failed: Python is 3.13.5 (`assert sys.version_info[:2] == (3, 12)`
exit 1) and Node is 20.19.2 (the Node 24 guard exit 1).

Not run, because they need that bootstrap, Node 24, a Sui CLI, snarkjs, or a
local chain:

- `scripts/check_sdk_client.py`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`
- `scripts/verify_runtime.py`, `scripts/verify_commerce.py`, `scripts/verify_canonical.py`
- storage probes (`probe_paid_storage.py`, `reproduce_storage_rollback.py`, `verify_paid_recovery.py`, `verify_paid_archive.py`)
- `scripts/run_localnet.py` and the paid/private journeys
- ZK `setup:zk` / `test:zk`

Hosted KTX kernel verification and KIX protocol verification were not run.
No commit was created, so there is no exact head for those workflows.
A green local cargo run is not that GitHub Actions result.

`.github/workflows/protocol.yml` discovers only
`settlement_f01_f03`, `booking_resale_admission`, and `credit_advance_f04`.
It does not discover `reference/ai_delegation`. The workflow was not edited.
The 22 mock tests are local evidence only.

## Coverage

| Requirement | Before this tree | What covers it now |
|---|---|---|
| Query, propose, execute, scope, amount, period, revocation | Not covered | Contract §3–§7. Tests cite every `DLG-` id in a docstring |
| Model output does not issue or pay | Not covered | Inert proposal, `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY`, flags stay false |
| No AI self-expansion (I11) | Stated in `FIRST_BATCH_OPEN_INPUTS` only. That file was not edited | Human-only issue, revoke, and decide. Widen, reissue, and revive tools fail with the digest unchanged |
| Execution stays disabled (development plan §12) | Prose only | No constructor switch. `EXECUTE` is rejected. `attempt_execution` always raises |
| Allowlist excludes transfer, refund execution, and signing | Not covered | Closed allowlist and denylist, disjoint from each other |
| `delegate` and `close_delegation` unchanged | Existing ticket commands in `reference/v0.3-rc1` | Empty diff on that tree. AST test: the mock does not import it. Allowlist is disjoint from `protocol_contract.json` commands |
| Kernel locked behavior | Existing `kix-kernel` tests | Re-run above. Sources were not edited |

`FIRST_BATCH_OPEN_INPUTS` I11 and `CURRENT_CAPABILITY_REGISTER.md` were left
as they are. A register row is a later sync, not this node.

## What the mock does

`AiDelegationMock` keeps grants and proposal memos in one process.

- `QUERY` tools and `view_*` do not change `state_digest`.
- `PROPOSE` writes a memo. `effects_executed` stays false. Approving the memo does not issue or pay.
- `EXECUTE` cannot be stored. `attempt_execution` raises `DELEGATED_EXECUTION_DISABLED` and does not change the digest.
- Caps count `PROPOSED` and `HUMAN_APPROVED`. Rejected and withdrawn proposals release that share.
- Revocation takes effect when recorded, voids still-pending proposals, and keeps them.
- A revoked `grant_id` is not revived. The next generation is a new id after revoke.
- `state_digest` is sha256 of canonical JSON. It is not a signature.

Fixture amounts and periods are not product limits.

## What it does not claim

- No durable grant, chain grant, revocation cut, or identity system.
- No signing, transfer, refund execution, ticket issuance, or payment.
- No wire command and no OpenAPI or SDK entry.
- `HUMAN_APPROVED` is not a legal or payment approval.
- Passing these tests does not mean AI delegation is implemented.
- Passing the local cargo and Python checks does not mean hosted exact-head CI is green.

## Deviations from the design plan

- Missing ids are `UNKNOWN_GRANT` and `UNKNOWN_PROPOSAL`, not binding conflicts.
- The denylist also names `widen_grant`, `reissue_grant`, and `revive_grant` so those attempts have `AI_SELF_EXPANSION_FORBIDDEN`.
- `limits.currency` is required and must be `KRW`. There is no silent currency default.
- The mock keeps at most one `ACTIVE` grant per `(issuer, agent_id)`. Whether several grants may be live at once is still UNDETERMINED in contract §9. The one-active rule is a mock invariant so the cap predicates can be tested.
- A second revoke does not overwrite the first reason.
- A repeated proposal whose binding matches returns `duplicate: true` even if the grant was later revoked or is outside its period. A new proposal still re-checks.
