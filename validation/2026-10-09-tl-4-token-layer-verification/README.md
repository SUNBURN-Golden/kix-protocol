# tl-4 token-layer verification

Author-side threat model and property harness for the off-chain token layer.
This session did not commit, push, or open a pull request. A passing run is not an independent verification.

The command table below is filled after the local run in this session. Exact-head CI run IDs are not in this file.

## Identity

| Item | Value |
|---|---|
| Task | `tl-4` (no task issue, no `docs/tasks/` edit) |
| Task document | none. Node spec is `.aiops/program.json` `tl-4`. This session does not edit that file |
| Observed `origin/main` | `6bdd571fcb88496c98e25b32213c60017e209198` |
| Branch | `agent/kix-tl-4` |
| Branch HEAD before edits | `6bdd571fcb88496c98e25b32213c60017e209198` (same as `origin/main`) |
| Implementation commit | none. The supervisor owns git |
| Threat model | `docs/decisions/TL4_THREAT_MODEL_20261009.md` |

`git fetch origin main` on 2026-10-09 reported `origin/main` at that SHA. The branch was already there. No rebase and no merge of main.

## What this session adds

- `docs/decisions/TL4_THREAT_MODEL_20261009.md`
- `reference/token_reward/tl4_support.py` (not collected by discover)
- `reference/token_reward/test_tl4_model_properties.py`
- `reference/token_reward/test_tl4_fsm_properties.py`
- `reference/token_reward/test_tl4_fuzz_boundaries.py`
- This README

Product modules `token_reward_model.py` and `reward_fsm.py` are unchanged. So are the two existing test modules.

## Scope

TL-2 and TL-3 on-chain merged as does-not-open records. There is no token package. This delivery is the limited reading: off-chain harness plus an explicit not-verifiable list. It does not close the blueprint TL-4 acceptance line that asks for independent verification of TK-1 through TK-9 with no open blockers.

## Locks

Checked before edits. Checked again after the test commands and recorded in the evidence table.

| File | Required blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

## Coverage

Existing TL-3 tests exercise the same predicates. This harness adds author-side property and fuzz checks. It does not replace a non-author review.

| Requirement | Existing | This node |
|---|---|---|
| TK-4 pool conservation | partial. `reference/token_reward/test_reward_model.py` | author-side property scripts. Not an independent PASS |
| TK-7 one payout effect | partial. `test_reward_fsm.py` | author-side sequences, replay, idempotency |
| TK-8 token and KRW effects stay apart | partial. `test_reward_fsm.py` | author-side KRW-note check |
| TK-12 collateral | partial. `test_reward_model.py` | author-side oracle and permutations |
| V6 supply recompute | partial. `test_reward_model.py` | author-side oracle, tamper, stop_payout |
| TK-6 T6 AI slice | partial. FSM approval tests in `test_reward_fsm.py` | author-side slice. T1–T5 not verifiable, no package |
| TK-10 gate records | not covered by an executable test | reviewed in the threat model. Not a TL-5 judgment |
| TK-11 wording | not covered by an executable test | author read plus an aid scan of the new artifacts only |
| TK-1, TK-3, TK-5 V1–V5, TK-9 gas path, TK-2 T2–T4 | not covered | `NOT VERIFIABLE · no package` |
| `TL1-TK02-T1` no second Move manifest | not covered as a named check | repo-state check. Not a package proof |

Stale follow-up, left unchanged on purpose: `docs/status/CURRENT_CAPABILITY_REGISTER.md` still says TL-4 is not covered. `docs/DEVELOPMENT_PLAN.md` §18 is not retargeted by this node.

## Commands and results

Working directory: repository root. `python3` is 3.13.5. `python3.12` is 3.12.15. `cargo` and `rustc` are 1.98.1. Node is v20.19.2. The workflow installs Python 3.12 and Node 24.

Locked blobs, before the edits and again after these commands: `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | `6bdd571fcb88496c98e25b32213c60017e209198` for both |
| `git hash-object` on the two locked kernel files | both match the lock table, before and after |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime` | exit 0 |
| `git diff --check` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward -v` | exit 0. Ran 61 tests in 0.510s. OK |
| same discover, `PYTHONHASHSEED` 0, 1, 2, and `random` | exit 0 each. Ran 61 tests. OK |
| same discover twice in a row | exit 0 both. Ran 61 tests. OK. The two logs differ only in the elapsed-time line (0.506s and 0.492s) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0. Ran 61 tests in 0.503s. OK |
| discover `reference/settlement_f01_f03` | exit 0. Ran 22 tests in 0.014s. OK |
| discover `reference/booking_resale_admission` | exit 0. Ran 47 tests in 0.431s. OK |
| discover `reference/credit_advance_f04` | exit 0. Ran 26 tests in 0.047s. OK |
| discover `reference/ai_delegation` | exit 0. Ran 22 tests in 0.035s. OK |
| discover `reference/token_reward` inside the five-suite loop | exit 0. Ran 61 tests in 0.512s. OK |
| `python3 scripts/check_openapi_contract.py` | exit 0. `commands=84 core=40 fsm=44` pin `ed827de1…` / `619ae21…` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0. `commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0. `self-test: pass` |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. Ran 58 tests in 4.495s. OK. The process also printed one `ResourceWarning` for an unclosed file and `self-test: pass` |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. Ran 7 tests in 0.275s. OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. Every crate summary was `test result: ok`. Passed tests counted from those summaries: 128 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |
| `bash scripts/bootstrap.sh` | exit 1. `AssertionError: Python 3.12 is required` (`python3` is 3.13.5). The script did not reach the Node 24 check |

## Not run

| Command | Why |
|---|---|
| `.venv/bin/python scripts/verify_runtime.py` | `bash scripts/bootstrap.sh` exited 1 before creating `.venv`. `python3` is 3.13.5 and Node is v20.19.2. The script requires Python 3.12 as `python3` and Node 24 |
| `scripts/verify_commerce.py`, `scripts/verify_canonical.py`, SDK conformance, storage probes | same missing `.venv` and Node 24 pin. Not run. Not a pass |
| Move, ZK, `scripts/run_localnet.py` | not run. No Sui testnet or mainnet call was made |
| Exact-head KTX kernel verification and KIX protocol verification | No commit and no pull request in this session, so no run ID exists. Per AGENTS.md §11 those IDs belong in the PR closure report, not in a follow-up commit. Because `reference/` changes, both workflows leave docs-only mode. A green check on an earlier SHA does not transfer |

## Non-claims

No independent verification. No production endpoint, public host, real payment, KYC, bank, or venue call. No Sui testnet or mainnet. No durability, chain finality, or production-readiness claim. The wording on this line is a refusal: it does not claim production-ready status. CI success from an earlier SHA does not transfer. Exact-head CI was not run in this session.

## Contract notes

Threat model §6. Classification A: the author-side oracles matched the model on the final local run. Classification B: `effect_id` raises `TypeError` for a non-canonical argument; the contract does not name that function's error class. Product code was not patched. Classification C: none. This does not close the blueprint TL-4 acceptance line.
