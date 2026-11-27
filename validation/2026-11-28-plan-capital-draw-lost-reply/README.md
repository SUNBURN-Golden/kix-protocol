# Builder evidence for plan-capital-draw-lost-reply

The supervisor-supplied node envelope and design plan are the task input.
The node comes from planner run `1795791795` and has no issue or file under
`docs/tasks/`. The task branch
`agent/kix-plan-capital-draw-lost-reply` and cached `origin/main` both point to
`394a6cb0f64935bec3da183353bfffcff06a3d01`, matching the design base. Remote
freshness is unverified. Builder delivery is an uncommitted worktree.

## Coverage before this change

Test paths are relative to `reference/credit_advance_f04/`.

| Requirement | Existing coverage | New verification |
| --- | --- | --- |
| Same draw identity, one attempt, `UNKNOWN`, null receipt and zero follow-up calls | Partial. `test_credit_client.py::CreditClientTests.test_uncertain_replies_fence_without_resend` covers client fencing after an uncertain reply on `offer`. | The replay captures the complete submitted S2 draw step in both histories and compares the exact canonical caller observations. |
| Loss before dispatch | Uncovered for the matching S2 draw. | Zero dispatches preserve the entire `APPROVED` credit snapshot and its three prior journal entries. |
| Loss after dispatch | Sufficient for ordinary acceptance. `test_capital_equal_gross_claim_binding.py::CapitalEqualGrossClaimBindingTests.test_equal_gross_claim_binding` checks the accepted envelope and resulting credit snapshot. The delivery fault was uncovered. | One dispatch yields the same envelope, a frozen `DRAWN` view, 10,000 fixture KRW outstanding and the exact prior journal prefix plus one draw entry. The caller receives no receipt. |
| Preserve both settlement journals | Partial. The equal-gross replay checks the original histories through ordinary draw dispatch. | The new histories restore fresh S1 and S2 machines, preserve the literal S2 offer face, and compare both complete settlement journals before setup, after setup and after the caller returns. |
| Capital discovery | Uncovered for this pair. | The index validates 23 families, 484 entries, 132 supplemental observations and 12 supporting entries. It rejects resolving pointer swaps, including equivalent caller results, and a re-pinned caller record with a leaked phase. |

The harness verifies the private receipt against the complete pinned matching
envelope. The prior credit journal is `offer`, `approve`, `bind_settlement` in
both histories. The dropped request adds no entry. The withheld acceptance
adds exactly one `draw` entry. [Vector pack](../../reference/credit_advance_f04/fixtures/capital_draw_lost_reply_vectors_v1.json) · [Focused replay](../../reference/credit_advance_f04/test_capital_draw_lost_reply.py) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#draw-lost-reply)

## Commands and results

Python used 3.12.15. The focused checks preceded both full suites.
`$f04` denotes `reference/credit_advance_f04`. The focused and broader Python
runs set `PYTHONDONTWRITEBYTECODE=1`. Cargo and rustc used 1.98.1 with
`CARGO_NET_OFFLINE=true` for both the workspace and isolated checks.

| Command | Actual result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD origin/main`, `git branch --show-current` | Clean startup worktree on the requested branch. Both refs matched the pinned design base. |
| Inline `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/credit_advance_f04 python3.12 -B -` | Captured both replay histories, compared the caller records canonically and wrote the vector and one appended index row. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_draw_lost_reply.py -v` | 1 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_equal_gross_claim_binding.py -v` | 1 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py -v` | 23 passed, including the resolving pointer swaps and the detached caller-shape control. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for `credit_advance_f04` and `settlement_f01_f03` | 341 and 224 passed, respectively. |
| `python3.12 -B scripts/check_$check.py` and the same with `--self-test` for `docs_index`, `ci_test_discovery`, `ci_checker_wiring`, `credit_evidence_map`, `settlement_evidence_map`, `openapi_contract` and `integration_gate_openapi` | All 14 invocations passed. The docs index counted 481 scanned, 446 indexed and 35 allowlisted. CI discovery reached 37 F04 test files. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 17 passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py`, `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed. All 7 architecture tests passed. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` with an inline JSON summary, and `python3.12 -B scripts/check_cargo_offline_cache.py --self-test` | Both exited 0. The cache report found 16 of 378 archives present and `duckdb` missing. |
| `cargo test -p kix-kernel --locked --offline`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | Each exited 101 before compilation. Workspace member `kix-analytics-audit` requires the missing `duckdb` registry entry. |
| `cargo fmt --all -- --check` in `runtime/` | Passed. |
| `cargo test --workspace --locked --offline`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in `runtime/` | Both exited 101 on the same missing registry entry. |
| Inline `CARGO_NET_OFFLINE=true python3.12 -B -` with a temporary workspace under `runtime/target/` | `diff -qr` confirmed the copied `kix-kernel` and `kix-types` crates. `cargo generate-lockfile --offline` passed. |
| `cargo test -p kix-kernel --locked --offline --quiet`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline` in the temporary workspace | All passed. There were 139 kernel test passes, and `kix-types` was the sole normal dependency. |
| `git ls-tree HEAD`, `git hash-object`, `sha256sum` and sorted content manifests compared with `cmp` | Both locked kernel blobs matched before and after. The 108-file frozen manifest was byte-identical. The original fixture matched its source SHA-256 pin and the new fixture matched both index pin digests. |
| `git diff --check`, scoped `git diff --exit-code HEAD`, `git status --short --untracked-files=all` and an inline artifact comparison | Eight changed paths. Protected paths and all earlier index rows matched the base. |
| Final `python3.12 -B scripts/check_docs_index.py` and `python3.12 -B scripts/check_ci_checker_wiring.py` | Both passed again with the same counts. |

## Changed files

- `reference/credit_advance_f04/fixtures/capital_draw_lost_reply_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_draw_lost_reply.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-28-plan-capital-draw-lost-reply/README.md`

## Artifact identities

| Artifact | Identity |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | 108 files, sorted manifest SHA-256 `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` |
| Pinned equal-gross pack | SHA-256 `dcce54255062d391faaf2d0ccc2f1f284fae8b0abbafe620162f33e25c740b34` |
| New lost-reply pack | SHA-256 `44d5d22ce2a7d57c52e6985fb2c6bb7ff953ffc7173613c933db53b1fc6fa766`, Git blob `20b7be80c5ce9291a03de377925b378469effe63` |

## Deviations

The supervisor's no-network rule superseded the startup fetch. The offline
cache required a temporary two-crate workspace for the kernel commands. The
whole Rust workspace remains locally unverified. Hosted provisioning and the
SDK, Move, local chain, storage and ZK stages fall outside this local check of
the changed paths.

## Scope and delivery gates

The synthetic credit outcomes match F04 §§7.2 and 7.5. The replay found zero
contract violations. The missing-reply behavior is a harness characterization
with recovery lookup `NOT_BOUND`.
Evidence is source-informed Class B. External Capital acceptance is
`UNVERIFIED`. Product limits and financial terms are `UNDETERMINED` with
Astra. Legal responsibility is `UNDETERMINED` with User/legal. The replay
uses process-local mocks. External execution, distributed durability,
provider exactly-once behavior, chain finality and production readiness
remain unverified.

A2 non-author review and exact-head hosted KTX and KIX CI are pending
supervisor delivery gates. No implementation, final delivery or merge
commit exists yet. Hosted run IDs, conclusions and post-merge checks are
unavailable for this worktree.
