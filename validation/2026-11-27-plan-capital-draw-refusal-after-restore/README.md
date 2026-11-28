# Capital draw refusal after restore

The supervisor-supplied node specification and design plan define
`plan-capital-draw-refusal-after-restore`. The node has no issue or file under
`docs/tasks/`. Branch `agent/kix-plan-capital-draw-refusal-after-restore` and
cached `origin/main` both started at `aa1b11b7678a382ad631b221302ddd5fe9f38dc5`.
The worktree was clean at startup.

## Coverage before implementation

Test paths in this table are relative to `reference/credit_advance_f04/`.

| Requirement | Before this node | Added evidence |
| --- | --- | --- |
| Same accepted history and zero exposure at S1's commit | Partial. `test_settlement_credit_boundary.py::SettlementCreditBoundaryTests.test_s1_captured_face_is_frozen_when_settlement_commits` checks the approved view. `test_capital_operation_replay_vectors.py::CapitalOperationReplayVectorTests.test_reconcile_restore_replay` restores accepted history. | Compare every delivered S1 result through `s1-commit`, then compare both complete views and journals, canonical states and digests before the two diagnostics. |
| Original returns its stored refusal without an append | Sufficient for the rule. `test_credit_properties.py::MachinePropertyTests.test_a_gate_rejected_key_stays_rejected_after_commit_and_a_new_key_succeeds` checks the stored refusal after a mock commit. | Match the original's complete result to the delivered S1 refusal and verify its complete view, journal, canonical state and digest after both calls. |
| Restored machine accepts the identical early draw | Partial. `test_credit_rejection_atomicity.py::CreditRejectionAtomicityTests.test_restore_forgets_stored_rejections` covers a refused offer. The operation replay suite restores a previously accepted draw. | Dispatch S1's original draw ID and key once per machine. Require the restored receipt to be a new acceptance and the journal to contain exactly one more entry with those IDs. |
| Preserve the captured face and isolate settlement | Partial. S1 covers the frozen face, and `test_settlement_credit_boundary.py::SettlementCreditBoundaryTests.test_credit_journal_stores_the_literal_face` checks the offer's literal face. | Match the shared offer entry to the full captured claim. Check the frozen face in the restored draw and compare the committed settlement view, journal, canonical state and digest after restoration and each call. |
| Discover both results and understand the journal limit | Uncovered for this comparison. `test_capital_companion_evidence_index.py::CapitalCompanionEvidenceIndexTests.test_complete_index` covers the preceding inventory. | Pin one new pack with two complete result associations. Add a negative control that swaps the two valid result pointers. |

## Observations

Both credit machines begin `APPROVED` with zero exposure and the same three
accepted entries. The original returns its stored `SETTLEMENT_NOT_COMMITTED`
refusal without appending. The restored machine accepts one 10,000 fixture-KRW
draw and appends a single entry. Its frozen face retains the captured claim's
zero confirmed cash and 100,000 fixture-KRW open receivable. The committed
settlement already shows 97,000 fixture KRW in confirmed cash and keeps the
same view, journal, canonical state and digest throughout the comparison.
The index contains 20 packs, 478 entries, 130 supplemental observations and
12 supporting entries. [Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-draw-refusal-after-restore) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#draw-refusal-after-restore)

F04 §§7.3–7.5 define the observed behavior. Refusals leave no accepted entry,
so equal journals and state digests cannot establish whether the original
received a refused call. This source-informed Class B comparison supplies no
retry authority. No contract violation or contract-undefined behavior surfaced.
External `kix-capital` acceptance remains **UNVERIFIED**, product limits
**UNDETERMINED — Astra**, and legal responsibility **UNDETERMINED — User/legal**.
Live funds and providers, public endpoints, Sui execution, durable recovery,
bank exactly-once, legal compliance and production readiness are outside the
evidence. [F04 §7.3](../../docs/contracts/CREDIT_ADVANCE_F04.md#73-멱등키)

## Changed paths

- `reference/credit_advance_f04/fixtures/capital_draw_refusal_after_restore_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_draw_refusal_after_restore.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-27-plan-capital-draw-refusal-after-restore/README.md`

## Local verification

Commands ran from the repository root unless specified. `$f04` is
`reference/credit_advance_f04`. The runs used Python 3.12.15 and Cargo 1.98.1.

| Command | Actual result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD refs/remotes/origin/main`, `git symbolic-ref --short HEAD` | Clean worktree on the requested branch. Both refs matched the supplied base. |
| `rg -n 'plan-capital-draw-refusal-after-restore' docs/tasks .aiops/program.json`, `ls -ld /workspace/kix-run/logs/planner_1795662280` | No matching repository task document or program entry. The planner log path was absent. The supervisor supplied the node specification in the session. |
| Inline `PYTHONPATH=reference/credit_advance_f04 python3.12 -B -` | Replayed the ten-step S1 prefix, compared it to the delivered results and wrote the canonical two-case pack outside the test run. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p "$test.py" -v` | `test_capital_draw_refusal_after_restore` passed 1 test, `test_settlement_credit_boundary` passed 13, `test_capital_operation_replay_vectors` passed 10, and `test_capital_companion_evidence_index` passed 20. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` | `settlement_f01_f03` 224 passed, `booking_resale_admission` 1,096, `credit_advance_f04` 335, `ai_delegation` 182, `provider_facts` 86, `payment_effects` 28 and `economics` 99. The initial `token_reward` run had 396 passes and one timeout. |
| `PYTHONPATH=reference/token_reward python3.12 -B -m unittest -v test_reward_console_subprocess.RewardConsoleSubprocessTests.test_quit_eof_interrupt_and_render_failure_reap` | Passed in isolation after a 10-second harness timeout on the first suite run. |
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | Full rerun passed all 397 tests without a code change. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and both with `--self-test` | All four passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | All 11 tests passed with sockets disabled by the test harness. |
| Inline `python3.12 -B -` running the workflow's `Stdlib offline document checks` commands with `-B`, excluding the plain socket probe | All 68 selected invocations passed. This includes the docs index and both evidence maps, test discovery and checker wiring, with their self-tests. The docs index counted 472 scanned, 437 indexed and 35 allowlisted. Discovery reaches 34 F04 test files. |
| `python3.12 -B scripts/verify_runtime_architecture.py`, `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed, as did all 7 tests. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml $scope --locked --offline`, `cargo clippy --manifest-path runtime/Cargo.toml $scope --all-targets --locked --offline -- -D warnings` for each of `-p kix-kernel` and `--workspace` | All four exited 101 before compilation. The offline index lacks `duckdb`, required by workspace member `kix-analytics-audit`. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exited 101 with the same missing `duckdb` entry. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | Found 14 of 378 locked archives. |
| Inline `python3.12 -B -` with a temporary Cargo workspace and `diff -qr` on each copied crate | Verified six local-only crate trees byte for byte, retaining their original lockfile entries. |
| In that temporary workspace, `cargo test -p kix-kernel --locked --offline --quiet`, `cargo test --workspace --locked --offline --quiet` | Passed 139 kernel tests and 332 six-crate workspace tests. |
| In that temporary workspace, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline` | Both Clippy scopes passed. The normal kernel dependency tree lists only `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Computed all three KTX workflow input hashes. |
| `git hash-object` on the locked files and pack, `sha256sum` on the pack and its S1 sources, and `(find reference/v0.3-rc1 -type f -print0 \| LC_ALL=C sort -z \| xargs -0 sha256sum) \| sha256sum` | The locked blobs and tracked frozen reference files match the base. The first final manifest included five ignored cache files. After their removal the entire frozen tree matches the starting digest. The pack and its two S1 source pins match the recorded values. |
| `git status --short --ignored --untracked-files=all -- reference/v0.3-rc1`, inline `python3.12 -B -` cache cleanup, and `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_calculation_client.py -v` with `$bra=reference/booking_resale_admission` | Removed 74 generated bytecode files, including the five in the frozen tree. All 7 commerce-client tests passed on rerun. The whole-tree digest matched the starting value both before and after that rerun, and ignored status of the frozen tree was clean. |
| `git diff --check`, `git diff --exit-code HEAD -- .aiops docs/tasks .github reference/v0.3-rc1 runtime`, `git status --short --untracked-files=all`, and inline `python3.12 -B -` artifact and path checks | Clean whitespace, eight changed paths, protected paths unchanged, and the previous JSON index recovered byte for byte by removing the new pack. |

## Protected bytes and delivery gates

| Artifact | Verified value |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | Sorted file SHA-256 manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` |
| `capital_draw_refusal_after_restore_vectors_v1.json` | SHA-256 `06aef555f6c8fb81aef4043d7553493ead55ca5a2035843a170ca2bd732f675b`, Git blob `eb7f4717801a86ce67bcbb4b3606acdf3398149b` |
| `settlement_credit_boundary_v1.json` | SHA-256 `16088b7f1170d322c0a0441e159c44151e68a31a24c46cad6c5fd0ded70b0803` |
| `settlement_credit_boundary_vectors_v1.json` | SHA-256 `f4e44f4a2f54c53de63f9fc7f94933c35453f9826992aadcd912a45fef0f26ce` |

The tested patch is uncommitted. Implementation and final task commit SHAs,
A2 non-author exact-head review, and exact-head KTX kernel and KIX protocol
CI run IDs, statuses and conclusions are pending supervisor delivery. A merge
commit and post-merge CI are inapplicable to this handoff.

## Deviations

The supervisor's network restriction superseded the startup fetch. Remote
freshness remains unverified. The prescribed booking discovery includes an
existing mock HTTP test that used loopback. The standalone loopback probes,
hosted runs, network bootstrap, and unrelated SDK, Move, ZK and chain stages
were omitted. The original `-B` flag did not carry over to test subprocesses.
Generated bytecode was removed and the commerce-client rerun inherited
`PYTHONDONTWRITEBYTECODE=1`. The Cargo fallback covered `kix-types`,
`kix-feature-semantics`, `kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and
`kix-delegated-exec`. The full workspace, including `kix-analytics-audit`
and `kix-bcs1`, remains unverified locally.
