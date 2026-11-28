# Capital repayment attribution validation

Task `plan-capital-repayment-attribution` uses the node specification and design
supplied by the supervisor. It has no issue or separate task document in
`docs/tasks/`. Local `origin/main` and starting branch HEAD both
resolved to `70c106c705fd1dba9e6341639ba9f9f5c0e1d0de` on
`agent/kix-plan-capital-repayment-attribution`. The builder delivers worktree
changes for the supervisor to commit.

## Existing coverage and added evidence

| Requirement | Existing coverage | Added evidence |
| --- | --- | --- |
| Common H1 checkpoint and per-advance exposure | Partial. `CapitalCrossClaimHistoryVectorTests.test_complete_history_vectors` and `test_checkpoint_arithmetic` cover A1. | Each branch compares all 20 setup results and the full initial snapshot to H1. The tests compare outstanding exposure by advance ID and match the A1 receipt and snapshot to H1. |
| Accepted journal attribution | Partial. H1 captures the A1 entry and `CapitalOperationReplayVectorTests.test_complete_history_vectors` covers accepted repayment entries. | Each branch verifies its full receipt and the exact journal append, including the target, key and body. |
| Cross-target key conflict and atomicity | Partial. `CapitalOperationReplayVectorTests.test_refusals_preserve_public_state` covers refusal atomicity. | Each successful branch sends the same key to the other advance, expects `IDEMPOTENCY_CONFLICT` and compares the entire post-refusal snapshot to the accepted one. |
| Frozen faces, reservations and settlement journal | Partial. H1 arithmetic and replay cover the A1 branch. | Each setup checks its offer faces against the committed settlement claims. Both accepted branches preserve the complete credit claim records and settlement snapshot. |
| A wrong target at the same group total | Uncovered in H1 and operation replay. | `test_detached_attribution_swap` crosses the receipts and snapshots at 110,000 group outstanding and checks for semantic rejection. `test_repayment_attribution_swapped_journals` crosses valid pointers and separately repins crossed journal entries to test the resolved target. |

| Case | A1 outstanding | A2 outstanding | B1 outstanding | Group outstanding |
| --- | ---: | ---: | ---: | ---: |
| `repay_a1` | 30,000 | 30,000 | 50,000 | 110,000 |
| `repay_b1` | 40,000 | 30,000 | 40,000 | 110,000 |

The companion inventory validates 24 families with 486 case and step entries,
134 observations and 12 supporting entries. The new pack's raw SHA-256 is
`9c08127c4ed7147647dc98acff258853cc2fd777728f4c7db9772b5a98100b57`. Its Git blob
is `233980fcebd53caf91d96c68b1a09ce5c30f0d37`.
[Paired vectors](../../reference/credit_advance_f04/fixtures/capital_repayment_attribution_vectors_v1.json) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#repayment-attribution)

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_repayment_attribution_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_repayment_attribution.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-28-plan-capital-repayment-attribution/README.md`

## Commands and results

Python commands used Python 3.12.15 from the repository root with
`PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=.`. The four focused runs preceded
the reference suites and document checks. Both workflows classify reference
test and fixture paths as full verification.

| Command | Result |
| --- | --- |
| `python3.12 -B -m unittest discover -s "$F" -t "$F" -p "test_capital_${name}.py"` with `F=reference/credit_advance_f04` | `repayment_attribution` 2 passed, `operation_replay_vectors` 10 passed, `cross_claim_history_vectors` 8 passed, `companion_evidence_index` 24 passed. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` | `settlement_f01_f03` 225 passed, `booking_resale_admission` 1,109 passed, `credit_advance_f04` 345 passed, `ai_delegation` 182 passed, `token_reward` 397 passed, `provider_facts` 86 passed, `payment_effects` 28 passed, `economics` 99 passed. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 487 scanned, 452 indexed, 35 allowlisted. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. The workflow reaches 39 credit test files, including this node's test. |
| `python3.12 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both passed. 24 rows and 134 citations. |
| `python3.12 -B scripts/check_settlement_evidence_map.py` and `--self-test` | Both passed. 27 rows and 110 citations. |
| `python3.12 -B scripts/check_contract_error_codes.py` and `--self-test` | Both passed. 199 rows and 198 covered codes. |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both passed. The 94-command contract pin matched. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both passed. The 94-command gate pin matched. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 19 passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Architecture and declared dependency gate passed. |
| `python3.12 -B scripts/test_runtime_architecture.py` | 7 passed. |

Rust commands used the pinned 1.98.1 toolchain and `CARGO_NET_OFFLINE=true`.
In the original `runtime/` workspace, Cargo resolves the optional `duckdb`
dependency of `kix-analytics-audit` even for kernel-only commands. The local
offline index lacks that entry. To verify the local crates, a temporary
workspace under `.local/` copied all crate files, verified them with
`diff -qr` and generated a lockfile for six workspace members. Its membership
excluded `kix-analytics-audit` and `kix-bcs1`, which declare uncached registry
dependencies.

| Command | Repository workspace | Temporary six-crate workspace |
| --- | --- | --- |
| `cargo +1.98.1 fmt --all -- --check` | Passed | Covered by the repository run |
| `cargo +1.98.1 generate-lockfile --offline` | Existing repository lockfile | Passed |
| `cargo +1.98.1 test -p kix-kernel --locked --offline` | Exit 101, missing `duckdb` | 139 passed |
| `cargo +1.98.1 clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101, missing `duckdb` | Passed |
| `cargo +1.98.1 tree -p kix-kernel --edges normal --locked --offline` | Exit 101, missing `duckdb` | Passed, direct dependency `kix-types` |
| `cargo +1.98.1 test --workspace --locked --offline` | Exit 101, missing `duckdb` | 332 passed |
| `cargo +1.98.1 clippy --workspace --all-targets --locked --offline -- -D warnings` | Exit 101, missing `duckdb` | Passed |

## Protected bytes and delivery gates

| Command | Result |
| --- | --- |
| `git rev-parse --verify origin/main` and `git rev-parse HEAD` before and after | Both refs resolved to the starting SHA above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before and after | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `sha256sum` on the sorted tracked paths under `reference/v0.3-rc1/` before work and all files found under that path after work, then `cmp` | Identical 108-path manifests with SHA-256 `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`. |
| `sha256sum reference/credit_advance_f04/fixtures/capital_cross_claim_history{,_vectors}_v1.json` | The unchanged fixture and vectors matched the original H1 verifier pins. |
| `git diff --exit-code HEAD --` for `.aiops`, `.github`, `docs/tasks`, `docs/contracts`, `runtime`, `reference/v0.3-rc1`, `reference/settlement_f01_f03` and tracked F04 paths excluding the companion index test | Exit 0. |
| `git diff --check` and `git status --short --untracked-files=all` | Whitespace check passed. The worktree listed the eight paths above. |
| `ls -ld /workspace/kix-run/logs/planner_1795823722` | Planner log unavailable locally. The supplied node specification is the task input. |

The supervisor's no-network instruction superseded the startup fetch. The
observed base is the local remote-tracking ref. Remote freshness is
unverified. The builder handed off an uncommitted worktree, so implementation
and final task commit SHAs are pending. Exact-head KTX kernel verification
and KIX protocol verification run IDs, statuses and conclusions are pending
the supervisor's commit and publication. A2 non-author review is also
pending. Merge and post-merge verification do not apply to this handoff.

The replay matched F04 §§7.2–7.3 and 7.11–7.12 for the recorded cases. It
found zero contract violations and zero contract-undefined behaviors. This
is source-informed Class B mock evidence. External Capital acceptance is
`UNVERIFIED`. Product limits and tolerances are `UNDETERMINED` with Astra.
Legal responsibility is `UNDETERMINED` with the User and legal counsel.
Live funds, PG/bank/KYC, public endpoints, production runtime, chain
execution, durable idempotency and selection of the intended recipient of
a real payment are outside this verification.
