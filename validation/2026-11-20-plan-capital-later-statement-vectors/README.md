# Capital later settlement statement vectors — builder validation

Task `plan-capital-later-statement-vectors` uses the supervisor-supplied node
specification and design for planner run `1795149680`. This node has no issue or
task document under `docs/tasks/`. The checkout is
`agent/kix-plan-capital-later-statement-vectors`. At session start the worktree
was clean, and the cached `origin/main`, task base and task HEAD all resolved to
`14bb3eba50b6cc8acc07fe452323d5e68a834c56`. The supervisor prohibited network
actions, so the required startup fetch was skipped and remote freshness is
unverified. The planner log directory was absent from this environment. The
supplied specification and design carried the task input.

## Coverage before this addition

| Acceptance | Existing coverage | Added evidence |
| --- | --- | --- |
| Later statement preserves commit identity, and same-key replay has a single economic effect | Sufficient for the individual behaviors. `SettlementFsmTests.test_later_statement_stays_on_commit_and_cases_do_not_share_cash` and `StatementAdapterTests.test_replay_fetches_each_time_returns_first_snapshot_after_later_changes`. | `test_statement_identity_and_replay` checks the original commit movement, full replay envelope, identical live snapshot, and one journal entry for the later observation within the combined history. |
| Later cash distribution and requester refund | Sufficient for the individual behaviors. `SettlementMockTests.test_f02_later_cash_continues_on_the_frozen_order` and `SettlementFsmTests.test_partial_refund_distribution_survives_replay_and_is_not_a_clawback`. | `test_checkpoint_arithmetic` checks F01 cash and receivables, F02 obligations and both distribution effects, and the separate F03 obligation against literal inputs. |
| Frozen F04 face, shared exposure and variance | Partial composition coverage. `CapitalRefundCompositionVectorTests.test_settlement_actions_preserve_credit`, `SharedExposureContractTests.test_frozen_face_unchanged_after_settlement_refund` and `SettlementVarianceContractTests.test_mapping_is_not_bound_and_companions_are_diagnostic` cover frozen credit across refunds and the observer boundaries. | `test_frozen_credit_and_observers` checks unchanged F04 state and exposure through the second statement and distribution, and separately checks payee variance and cash delta. |
| Portable receipts, snapshots and index navigation for this history | No existing pack covers this sequence. The companion validator covers the shared navigation format. | `test_complete_history_vectors` checks exact replay bytes and source pins. `test_later_statement_crossed_references` rejects swapped statement and replay input, result and snapshot pointers. |

The fixture lists the contract clauses and the source-test paths and symbols
used in this mapping. [Literal input](../../reference/credit_advance_f04/fixtures/capital_later_statement_v1.json) · [Captured output](../../reference/credit_advance_f04/fixtures/capital_later_statement_vectors_v1.json) · [Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-later-settlement-statement-vectors)

## Changed paths

- `docs/README.md`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `reference/credit_advance_f04/fixtures/capital_later_statement_v1.json`
- `reference/credit_advance_f04/fixtures/capital_later_statement_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `reference/credit_advance_f04/test_capital_later_statement_vectors.py`
- `validation/2026-11-20-plan-capital-later-statement-vectors/README.md`

## Results

The protocol reference suites ran with Python 3.12.15. Rust checks used Cargo 1.98.1.

| Command | Actual result |
| --- | --- |
| `git status --short --branch` and `git rev-parse refs/remotes/origin/main HEAD` | Clean task branch at the cached base above. |
| `git ls-tree HEAD reference/v0.3-rc1 .aiops docs/tasks` | Captured the protected base trees before editing. |
| `PYTHONPATH=reference/credit_advance_f04 python3 -B -` (fixture capture) | Wrote both canonical fixtures after the replay passed the receipt, arithmetic and observer predicates. |
| `PYTHONPATH=reference/credit_advance_f04 python3 -B -` (index append) | Appended 13 result associations and six snapshots with SHA-256 and Git blob pins. |
| `python3 -B -m unittest discover -s "$credit" -t "$credit" -p test_capital_later_statement_vectors.py` | 4 passed. Here and below `credit=reference/credit_advance_f04`. |
| `python3 -B -m unittest discover -s "$credit" -t "$credit" -p test_capital_companion_evidence_index.py` | 11 passed. The 11 packs contain 451 receipt associations and 128 observations, with 12 separate supporting entries. |
| `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 224 passed. |
| `python3.12 -B -m unittest discover -s "$credit" -t "$credit"` | 310 passed. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the other six offline protocol suites | `booking_resale_admission` 1,067, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99 passed. The booking suite uses the local loopback mock. |
| `python3.12 -B scripts/check_openapi_contract.py` and `python3.12 -B scripts/check_integration_gate_openapi.py`, each also run with `--self-test` | All four passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 11 passed. |
| `python3 -B -` (run each command from `Stdlib offline document checks` in `.github/workflows/protocol.yml` with `-B`) | 69 of 69 passed on the complete rerun. The first pass produced 67 passes and two failures from the missing validation-record link. |
| `python3 -B scripts/check_docs_index.py` and the same command with `--self-test` | Both passed after adding the direct link from `docs/README.md` to this record. The first run flagged the missing link and the self-test requires a passing baseline. |
| `python3 -B scripts/verify_runtime_architecture.py` and `python3 -B scripts/test_runtime_architecture.py` | Architecture gate passed and 7 regression tests passed. |
| `cargo test -p kix-kernel --locked --offline` from `runtime/` | 139 passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` from `runtime/` | Passed. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` from `runtime/` | Passed. `kix-types` is the only normal dependency. |
| `cargo fmt --all -- --check` from `runtime/` | Passed. |
| `cargo test --workspace --locked --offline` from `runtime/` | 345 passed and one existing CPU/SQL acceptance test was ignored. That optional test requires an owner-provisioned offline bundle. |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` from `runtime/` | Passed. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before and after | Matched `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, respectively. |
| `git hash-object` on the two new fixtures | Both results match the Git blob pins in the companion index. |
| `git diff --exit-code HEAD -- .aiops .github/workflows docs/tasks docs/contracts reference/v0.3-rc1 runtime` | Exit 0. |
| `PYTHONPATH=reference/credit_advance_f04 python3 -B -` (byte comparison against `HEAD` and source citation check) | All 862 tracked files checked match their baseline bytes, including all 108 `reference/v0.3-rc1/` files. The ten existing pack records, two supporting records and qualification metadata retain their original bytes. The field guide preserves its prior content, and all seven source-test citations resolve. |
| `git diff --check HEAD`, `git status --short --untracked-files=all` and `git rev-parse refs/remotes/origin/main HEAD` | No tracked whitespace errors. The nine paths above match the worktree and both refs still point to the base. |
| `python3 -B -` (compare recorded paths with Git status and check file endings) | All nine changed files match the recorded paths and pass the whitespace and final-newline check. |

## Scope and delivery gates

This is process-local, source-informed Class B evidence. No contract violation
or new contract-undefined behavior was observed. External `kix-capital`
acceptance remains **UNVERIFIED**. Product tolerance, exposure limits, waterfall
and netting terms remain **UNDETERMINED — Astra**. Legal responsibility remains
**UNDETERMINED — JunTae and legal counsel**. The verification scope excludes
real money, external providers, public endpoints, Sui testnet/mainnet, and
production execution, durability, bank exactly-once, chain finality and legal
compliance. The additional offline checks cover the broader reference suites,
OpenAPI pins and offline limits. The unchanged Move, Sui localnet and ZK jobs
are outside the touched-path verification.

The delivery is an uncommitted worktree. Implementation and final delivery
SHAs, A2 non-author review, and exact-head KTX kernel and KIX protocol CI run
IDs, statuses and conclusions are pending supervisor handoff. Merge SHA and
post-merge checks are inapplicable at this stage.
