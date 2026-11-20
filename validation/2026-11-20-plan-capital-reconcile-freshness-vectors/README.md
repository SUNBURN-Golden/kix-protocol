# Builder evidence for Capital reconcile freshness vectors

Task `plan-capital-reconcile-freshness-vectors` uses the supervisor-supplied
node specification and design plan. The planner source is run `1795084226`.
The node has no issue or `docs/tasks/` document and runs outside ASTRA program mode.
The starting HEAD of `agent/kix-plan-capital-reconcile-freshness-vectors` and the
local `origin/main` ref were both `e535d0124d6e514e1f0654dd279ac8f2144dd22e`.
The supervisor's network restriction superseded the fetch step. Remote main
freshness is unverified.

## Coverage assessed before adding tests

| Requirement | Existing coverage | Gap for this history |
| --- | --- | --- |
| Original-key reconcile returns the first receipt | Partial. `test_settlement_fsm.py::test_reconcile_matches_restore_and_does_not_enter_the_economic_journal` and `test_credit_fsm.py::test_reconcile_replays_the_journal_without_a_second_draw` cover individual machine duplicates. | Compare both complete first receipts with replays after the full-gross refund. |
| Fresh-key reconcile returns current digests and both machines match | Partial. `test_settlement_credit_boundary.py::test_s6_reconciliation_gap_is_reported_without_repair` checks both current digests after a partial refund. | Compare the first and fresh digests across full reclassification and verify fresh flags even when the credit digest stays equal. |
| Current variance and authority boundaries | Partial. `test_settlement_variance_contract.py::test_formula_and_sign_convention` and `test_mapping_is_not_bound_and_companions_are_diagnostic` cover arithmetic and disposition separately. | Show the change from 0 to −100,000 KRW on live views alongside the two matches. |
| Frozen face and exposure, with reconcile appending no economic entry | Partial. The FSM reconcile tests and `test_capital_refund_composition_vectors.py::test_settlement_actions_preserve_credit` check these separately. | Compare the complete credit/exposure snapshots and both journals at all checkpoints, with only the refund appending a row. |
| Portable replay and companion navigation | Uncovered for this history. `test_capital_operation_replay_vectors.py::test_complete_history_vectors` supplies R3 setup lineage, and `test_capital_companion_evidence_index.py::test_complete_index` verifies the eight existing families. | Pin the complete capture and sources. Reject detached stale receipts, variance and authority changes, and crossed same-operation pointers. |

## Result and artifact pins

The eight literal setup calls and seven history calls give eight observation
checkpoints. The original keys each return their complete first receipt with
`duplicate=true` and `applied=null`. Fresh keys return `duplicate=false`,
`applied=reconcile`, `matched=true`, `effect=null` and each machine's current
view and digest. After the refund, settlement has five economic entries and a
new digest. Credit retains four entries and the same digest. The only new
economic entry is `bind_refund`.

Current settlement outstanding drops from 100,000 to 0 KRW. The frozen
credit open face stays 100,000 KRW and outstanding exposure stays 15,000 KRW.
Variance moves from 0 to −100,000 KRW and falls outside the explicit synthetic
zero tolerance. Mapping and refund component stay `NOT_BOUND` and repair stays
`NONE`, with `fail_closed=true`, `mutates_state=false` and
`authorizes_exposure=false`. Detached semantic controls reject a stale fresh
receipt and altered variance, tolerance result, repair or exposure authority.
Detached index controls reject crossed input, result and snapshot pointers
for both machines. The index resolves 418 associations, 108 supplemental
snapshots or restore observations, and 12 supporting entries.

| Artifact | Raw SHA-256 | Git blob |
| --- | --- | --- |
| [Input](../../reference/credit_advance_f04/fixtures/capital_reconcile_freshness_v1.json) | `f5a59872cb5c5a72028df4803666b990e86eb615f853db37c4a2267530b1d035` | `7a3f79f19d2a2364f43c5a03b43d25ad61e8f47c` |
| [Output](../../reference/credit_advance_f04/fixtures/capital_reconcile_freshness_vectors_v1.json) | `528b40f910a21c049a6d58e7cd71c51d8f34e98b1a88f296609857a45a7bf4dd` | `dea5c4946b76d27dd1f18352686f0660372aedb9` |

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_reconcile_freshness_v1.json`
- `reference/credit_advance_f04/fixtures/capital_reconcile_freshness_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_reconcile_freshness_vectors.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `reference/credit_advance_f04/README.md`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-20-plan-capital-reconcile-freshness-vectors/README.md`

## Actual verification

Commands ran in the foreground from the repository root. Python was 3.13.5
and Cargo and rustc were 1.98.1. Cargo used `CARGO_NET_OFFLINE=true` and
`RUSTUP_OFFLINE=1`. In the table, `d` is `reference/credit_advance_f04`.

| Command | Actual result |
| --- | --- |
| `git status --short --branch`, `git rev-parse --verify origin/main`, `git rev-parse --verify HEAD`, `git symbolic-ref --short HEAD` | Clean starting worktree on the task branch. HEAD and local `origin/main` matched the base above. |
| `PYTHONPATH=reference/credit_advance_f04 python3 -B -` (one-time fixture capture) | Assembled literal inputs, replayed public calls, verified receipt rules and independent arithmetic, then wrote both canonical fixtures. |
| `PYTHONPATH=reference/credit_advance_f04 python3 -B -` (one-time index append) | Added 15 associations and eight supplemental snapshots, with SHA-256 and Git blob pins. |
| `python3 -B -m unittest discover -s "$d" -t "$d" -p test_capital_reconcile_freshness_vectors.py` | 5 passed. |
| `python3 -B -m unittest discover -s "$d" -t "$d" -p test_capital_companion_evidence_index.py` | 9 passed. |
| `python3 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the eight protocol workflow suites | `settlement_f01_f03` 224, `booking_resale_admission` 1,058, `credit_advance_f04` 304, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99 passed. |
| `python3 -B -` (invoke each command in the protocol workflow's `Stdlib offline document checks` step with `-B`) | All 69 exited 0, including the docs, CI discovery and wiring, settlement and credit evidence maps, and Class B checks and self-tests. [Workflow](../../.github/workflows/protocol.yml) |
| `python3 -B scripts/check_openapi_contract.py` and `python3 -B scripts/check_integration_gate_openapi.py`, each also with `--self-test` | All four passed. |
| `python3 -B -m unittest integration_gate.test_offline_limits` | 11 passed. |
| `python3 -B scripts/verify_runtime_architecture.py` and `python3 -B scripts/test_runtime_architecture.py` | Architecture gate passed. All seven regressions passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 139 passed, zero failed or ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Passed. `kix-types` is the only normal dependency. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 345 passed, zero failed, one ignored. The existing optional CPU/SQL acceptance test requires an owner-provisioned offline bundle. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Passed. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before and after | Both locks match, respectively `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git hash-object` on the two new fixtures | Both Git blob pins match the table above. |
| `git diff --check HEAD`, scoped `git diff --exit-code HEAD`, `git diff --stat HEAD`, `git status --short --branch`, `git rev-parse HEAD origin/main` | Whitespace checks passed for tracked changes. Protected scopes had zero diff. The six modified and four added paths match the delivery list. Both refs still resolve to the starting SHA. |
| `python3 -B -` (direct worktree byte, index and source citation checks against `HEAD`) | All 333 checked tracked files in protected and reference scopes match their base blobs, including all 108 `reference/v0.3-rc1/` files. The previous eight pack records, both supporting records and index qualifications match the base. All five source-test citations resolve. The field guide has its original prefix and the new files pass whitespace checks. |

## Scope and delivery gates

The local results cover source-informed, process-local Class B evidence.
No contract violation or new contract-undefined behavior was observed in
this history. Product tolerance and netting remain **UNDETERMINED — Astra**.
Legal liability remains **UNDETERMINED — JunTae and legal counsel**. External
`kix-capital` acceptance remains **UNVERIFIED**. Durability, chain finality,
bank exactly-once, legal compliance and production readiness are outside this
verification. The unchanged Move, Sui localnet and ZK jobs were outside the
touched-path equivalence. No paid services, public endpoints, real funds,
real PG/bank/KYC, Sui testnet/mainnet or production runtime were exercised.

The deliverable is the uncommitted worktree. The implementation commit and
final delivery head are pending supervisor publication. Exact-head KTX kernel
verification and KIX protocol verification have no observed run IDs, statuses
or conclusions. The A2 non-author review is pending. Merge SHA, merge-time blob
checks and post-merge CI are inapplicable at this stage.

The design was followed. Local verification additionally ran the workflow's
complete offline document-check step, offline limits and workspace-wide Rust
checks. Remote main freshness remains unverified under the network restriction.
