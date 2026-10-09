# openapi-catalogue-promotion

Evidence for the contract-only catalogue promotion of the 44 FSM `REPLAYABLE` commands. This session did not commit, push, or open a pull request.

## Identity

| Item | Value |
|---|---|
| Task | `openapi-catalogue-promotion` (no task issue, no `docs/tasks/` edit) |
| Observed `origin/main` | `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f` |
| Branch | `agent/kix-openapi-catalogue-promotion` |
| Implementation commit | none. The supervisor owns git. The worktree is dirty on that base. |
| Owner decision | JunTae, 2026-10-09: proceed with the recommended options in the program state decision (DR-1 B, DR-2 A, DR-3 `bootstrap-2`, DR-4) |

The worktree started at `2ead88aec7f5fc36ed802c32c98f3053367c7ede`, 46 commits behind `origin/main`, with no task commits. It was fast-forwarded to `origin/main` before edits.

## What landed

- Second pin `docs/contracts/openapi/fsm-command-contract.json` (44 commands, wire names `<machine>_<op>`).
- Contract-only and integration-gate OpenAPI catalogues are 84 commands. The 40 core schemas stay equal to `protocol_contract.json`.
- Loopback gate dispatches FSM actions on the existing core worker. Schema failures stay HTTP 400. FSM handler codes are HTTP 422. `--readiness-dir` refuses FSM actions with `READINESS_FSM_REFUSED` and does not append them.
- TypeScript 0.x client regenerated. New manifest revision `bootstrap-2`. `bootstrap-1` files are unchanged historical pins.
- Stop markers in the booking, settlement, and credit contract documents now cite the 2026-10-09 owner decision.

## Locks

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/protocol_contract.json` | `619ae21c82ca3df5661bd3831613f15fa65225ff` |

`git diff --name-only` against those paths, `.aiops/`, and `docs/tasks/` was empty.

## Coverage

| Requirement | Result |
|---|---|
| Pin check | `scripts/check_openapi_contract.py` and `--self-test`; `scripts/check_integration_gate_openapi.py` and `--self-test` |
| Loopback UNKNOWN_ACTION | `authorize_admission` removed from the unknown list. `consume_admission` still rejected |
| FSM parity, admission path, idempotency replay, readiness refusal | `integration_gate.test_http_gate` |
| Client conformance | regenerated catalogue; every command has a positive body and negative schema cases, including the 44 FSM commands |
| Producer manifest | `bootstrap-2` binds both OpenAPI blobs, the FSM source, generator, toolchain, output, domain, schemas, profile, and vectors. The manifest text does not contain its sidecar digest |
| Kernel | no kernel edit. `cargo test -p kix-kernel` and workspace tests, clippy, fmt |

## Commands and results

Python in this environment is 3.13.5. Node checks used Node 24.19.0 from `/home/box/.local/opt/node-v24.19.0-linux-x64` (`PATH` prefix). Default `/usr/bin/node` is v20.19.2 and was not used for the SDK.

| Command | Result |
|---|---|
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. 58 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0. 20 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0. 43 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0. 20 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0. 22 tests OK. Current `protocol.yml` includes this suite |
| `python3 scripts/check_openapi_contract.py` | exit 0. `commands=84 core=40 fsm=44` pin `ed827de1…` / `619ae21…` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0. `commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_sdk_client.py` | exit 0. `commands=84 node=24.19.0` |
| `python3 scripts/check_sdk_client.py --self-test` | exit 0. `self-test: pass` |
| `npm --prefix sdk run conformance` | exit 0. 6 tests pass |
| `npm --prefix sdk run verify-compat` | exit 0. `{"ok":true,"profile_kind":"BOOTSTRAP","profile_revision":"bootstrap-2","manifest_sha256":"eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0"}` |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. architecture gate OK; durability/performance not certified |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |

## Not run

| Command | Why |
|---|---|
| `bash scripts/bootstrap.sh`, `verify_runtime.py`, commerce/canonical verifiers, storage probes, `run_localnet.py`, ZK | `bootstrap.sh` requires Python 3.12. This machine has Python 3.13.5 only. Those steps are outside the edited paths |
| Exact-head GitHub Actions | No commit and no pull request in this session. CI run IDs are not available |

## Deviations

- The empty task branch was fast-forwarded from `2ead88a` to `origin/main` `c2cde86` before implementation. The design note's base was stale and the branch had no unique commits.
- DR-4 left the readiness refusal token for Astra to name and said not to invent one. The loopback label used here is `READINESS_FSM_REFUSED` (HTTP 422, `rejected: true`). It names the approved fail-closed behavior. A different spelling is Astra's. It is not a product-policy number.
- `bootstrap-2` `producer.source_commit` / `source_tree` are the base `c2cde86` / `394084b15e01bbe4a5612aeb3431f3278c43dd85`. This session must not create the catalogue commit, so there is no C1/C2 split. The verifier does not resolve that commit. Byte identity is the OpenAPI hashes and the FSM source hash. The manifest does not contain its own digest or a delivery head.
- The historical mixed-input vector still names `bootstrap-2` as a negative revision. The conformance run retargets that one case to `bootstrap-9` because `bootstrap-2` is now a legal revision. The vector file bytes are unchanged so the `bootstrap-1` pin of that file stays intact.
- Schema field limits that already live in the FSM handlers (windows, ident length, enums) were not copied into JSON Schema. Nested objects and arrays use only the keywords `integration_gate/schema.py` already allows.

## Non-claims

No production endpoint, public host, server entry, or security scheme. No real payment, KYC, bank, or venue call. No Sui testnet or mainnet. No new protocol command outside the existing `REPLAYABLE` sets. `durable`, protocol truth, and production conformance stay false. Stable 1.0 is not published. `bootstrap-2` is catalogue-schema binding only. Semantic conformance stays on HOLD. Exact-head CI was not run.
