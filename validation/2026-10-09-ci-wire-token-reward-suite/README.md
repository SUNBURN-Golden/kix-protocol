# ci-wire-token-reward-suite

Wires the existing TL-3 off-chain suite `reference/token_reward/` into the protocol workflow's offline reference loop. This session did not commit, push, or open a pull request.

## Identity

| Item | Value |
|---|---|
| Task | `audit3-ci-wire-token-reward-suite` (no task issue, no `docs/tasks/` edit) |
| Observed `origin/main` | `d63768ddf276c60173aa2c933f4feef3449a9452` |
| Branch | `agent/kix-audit3-ci-wire-token-reward-suite` |
| Branch HEAD before edits | `d63768ddf276c60173aa2c933f4feef3449a9452` (same as `origin/main`; no unique commits) |
| Implementation commit | none. The supervisor owns git. The worktree is dirty on that base. |
| Source | KIX audit #3, `audit_3_20261009.md` finding F1 |

`git fetch origin main` on 2026-10-09 reported `origin/main` at that SHA. The branch was already there. No rebase and no merge of main.

## What landed

- `.github/workflows/protocol.yml` suite list, one line: `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do`. `git diff --numstat origin/main -- .github/workflows/protocol.yml` is `1 1`.
- Header notes in `reference/token_reward/test_reward_fsm.py` and `test_reward_model.py`. The fixture paragraphs stay as they were. The stale "does not name this directory" sentences now say the suite runs in `.github/workflows/protocol.yml` and that a passing run is not an independent verification. `git diff -U0` touches only those docstring lines.
- This README.

`committed_settlement_view` in `test_reward_fsm.py` imports `settlement_fsm` from `reference/settlement_f01_f03` by inserting that directory on `sys.path` for the import, then removing it. The loop starts one process per suite, so the module name does not collide with another suite. The settlement suite has to stay in the checkout for that test. The local `token_reward` run below includes it and passed.

## Locks

Checked before edits and again after the test commands.

| File | Blob (`git hash-object`) |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/protocol_contract.json` | `619ae21c82ca3df5661bd3831613f15fa65225ff` (`git rev-parse HEAD:reference/v0.3-rc1/protocol_contract.json`) |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github/workflows/ktx-kernel.yml` exited 0. `git diff --name-only origin/main` lists only the two test files and `protocol.yml`. This README is untracked until the supervisor adds it.

## Coverage

Existing deterministic tests already exercise the predicates. This node adds no assertion. The gap it closes is hosted execution of that suite.

| Requirement | Result |
|---|---|
| TK-4 pool conservation | sufficiently covered by `reference/token_reward/test_reward_model.py` (`test_TL0_TK04_T1_forbidden_pools_do_not_fund_token_spend` and the pool cases around it) |
| TK-7 one payout effect | sufficiently covered by `reference/token_reward/test_reward_fsm.py` (`test_TL0_TK07_T1_one_payout_effect_under_retry_delay_and_reencoding`) |
| TK-8 token and KRW effects stay apart | sufficiently covered by `test_reward_fsm.py` (`test_TL0_TK08_T1_token_and_krw_effects_stay_apart`) |
| TK-12 collateral recognition | sufficiently covered by `test_reward_model.py` (`test_TL0_TK12_T1_token_only_collateral_is_rejected` and the collateral cases around it) |
| V6 supply recompute | sufficiently covered by `test_reward_model.py` (`test_v6_supply_recompute_and_alarm_classes`) |
| CI runs `reference/token_reward` | was not covered. The suite list now names `token_reward` |

A passing local or hosted run is exercised coverage. It is not the independent verification TL-4 owns for TK-4/7/8/12 and V6.

## Commands and results

Python in this environment is 3.13.5. The workflow installs Python 3.12. The suite imports only the standard library plus its sibling modules. `python3.12` is not installed here, so that extra run was not done.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | `d63768ddf276c60173aa2c933f4feef3449a9452` and the same SHA for HEAD |
| `git hash-object` on the two locked kernel files | both match the table above, before and after |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0. Ran 20 tests. OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0. Ran 43 tests. OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0. Ran 20 tests. OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0. Ran 22 tests. OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0. Ran 37 tests in 0.051s. OK |
| `python3 scripts/check_openapi_contract.py` | exit 0. `commands=84 core=40 fsm=44` pin `ed827de1…` / `619ae21…` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0. `commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0. `self-test: pass` |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. Ran 58 tests in 4.932s. OK. Captured output also had one `ResourceWarning` for an unclosed file and a `self-test: pass` line |
| `python3 -c "import yaml; yaml.safe_load(...)"` | not run. `ModuleNotFoundError: No module named 'yaml'` |
| `git diff --check` | exit 0 |
| `git diff --numstat origin/main -- .github/workflows/protocol.yml` | `1 1` |
| `grep` for `not name this directory` under `reference/token_reward` | no hit |

## Not run

| Command | Why |
|---|---|
| Rust, Move, ZK, `scripts/bootstrap.sh`, `verify_runtime.py`, commerce and canonical verifiers, runtime-architecture, SDK | outside the edited paths. `ktx-kernel.yml` is unchanged. This machine's `python3` is 3.13.5; `bootstrap.sh` wants 3.12 |
| Exact-head KTX kernel verification and KIX protocol verification | No commit and no pull request in this session, so no run ID exists. Per AGENTS.md §11 those IDs belong in the PR closure report, not in a follow-up commit. A green check is not evidence that `token_reward` ran: the closure report should cite the `Offline reference state machines and OpenAPI pins` log line that names the suite |

## Non-claims

No new tests and no policy values. No independent verification of TK-4, TK-7, TK-8, TK-12, or V6. No production endpoint, public host, real payment, KYC, bank, or venue call. No Sui testnet or mainnet. No durability, chain finality, or production-readiness claim. CI success from an earlier SHA does not transfer to a later SHA. Exact-head CI was not run in this session.

## Contract notes

No contract violation found. No contract-undefined behavior was given a new meaning. The settlement import above is existing test code and was left unchanged.
