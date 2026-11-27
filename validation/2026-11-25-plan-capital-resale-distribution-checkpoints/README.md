# Capital resale distribution checkpoints

The task input for `plan-capital-resale-distribution-checkpoints` is the
supervisor-supplied node specification and design. The node has no issue or
file under `docs/tasks/`. The local planner record is
`/workspace/kix-run/logs/planner_1795569040_codex0.last.md`.

The branch `agent/kix-plan-capital-resale-distribution-checkpoints` and cached
`origin/main` both started at `a19651d8b3e9c50617a9f5f755cad6a6f43e00ac`,
the supplied base. The supervisor's no-network instruction superseded the
startup fetch. Remote freshness is unverified.

## Coverage mapped before implementation

| Acceptance | Existing coverage | Added evidence |
| --- | --- | --- |
| Producer receipt bytes and SDK tuple replay | Sufficient for the producer in `reference/booking_resale_admission/test_commerce_journey_receipts.py::CommerceJourneyReceiptTests.test_complete_output_bytes` and `test_commerce_fixture_tuple_conformance.py::CommerceFixtureTupleTests.test_vectors`. | The Capital replay pins the three source digests and checks each SDK vector, journey input and exact receipt association. |
| Committed face and §7.11 observations | Partial. `test_capital_commerce_refund_checkpoints.py::CapitalCommerceRefundCheckpointTests.test_checkpoint_replay` freezes a different Commerce claim. `test_settlement_variance_contract.py::SettlementVarianceContractTests.test_all_scenarios_replay_to_expected` covers the observer. | A single frozen `settle-resale` claim serves both the commit and distribution observations. The replay compares the full expected envelopes. |
| Transfer and F04 preservation | Partial. Commerce replay covers transfer. `test_economics_credit_consumer_vectors.py::EconomicsCreditConsumerTests.test_frozen_credit_bytes_survive_all_economics_actions` covers other histories. | The middle case verifies `buyer-B` and right version 2 from the ownership receipt. All three cases check the same post-draw F04 views, claim, journal and state digest. |
| Crossed pointers and index membership | Uncovered for this family. The existing Capital index and refund replay cover other families. | The replay rejects crossed commit and distribution pointers before arithmetic. The index rejects crossed entry pointers and a detached fixture whose updated pins match its bytes. |

## Replay results

| Commerce checkpoint | Organizer / platform outstanding (fixture KRW) | §7.11 variance (fixture KRW) |
| --- | ---: | ---: |
| `settle-resale-commit` | 11,880 / 120 | 0 |
| `accept-A` | — | — |
| `distribute-resale` | 0 / 0 | −12,000 |

The commit claim freezes a 12,000 KRW face for `settle-resale` and
`trade-resale-A`. The intervening receipt records `listing-A`, transfer
`transfer-A-2`, and `issue-A` held by `buyer-B` at version 2. The distribution
receipt records 12,000 KRW distributed. Both observations use the same
frozen claim and synthetic zero tolerance. They retain `NOT_BOUND`,
`repair=NONE` and all fail-closed flags. The mock advance continues to show
10,000 KRW drawn and outstanding, zero repaid, and an empty repayment list.
The four journal entries remain `offer`, `approve`, `bind_settlement`, `draw`.
The index holds 18 families, 473 entries, 128 supplemental observations and
12 supporting entries.
[Field guide](../../docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md#capital-resale-distribution-checkpoints) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#resale-distribution-checkpoints)

## Local verification

Commands ran from the repository root unless noted. `f04` is
`reference/credit_advance_f04` and `bra` is `reference/booking_resale_admission`.
The targeted runs used Python 3.13.5 with `PYTHONPATH=.`. The workflow runs
used Python 3.12.15, matching the workflow's Python minor version, and ran
its command blocks under `bash -ex -o pipefail`. All Python test runs used
`PYTHONDONTWRITEBYTECODE=1`.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD`, `git rev-parse refs/remotes/origin/main`, `git symbolic-ref --short HEAD` | Clean worktree at the supplied branch and base. The cached main ref matched. |
| `sha256sum` over all three source files and inline Python inspecting vectors 19–21 and receipt and input steps 23–25 | All fixed digests, pointers, action names, bodies and source identities matched. |
| `python3 -m unittest discover -s "$f04" -t "$f04" -p test_capital_resale_distribution_checkpoints.py` | 2 passed. |
| `python3 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_journey_receipts.py` | 7 passed. |
| `python3 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_fixture_tuple_conformance.py` | 9 passed. |
| `python3 -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py` | 18 passed. |
| `python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the first four workflow suites | `settlement_f01_f03` 224, `booking_resale_admission` 1,086, `credit_advance_f04` 331 and `ai_delegation` 182 passed. |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | Initial exit 1 among 397 tests. `test_guided_decline_invalid_and_eof_no_dispatch` hit its 10-second subprocess deadline at `observe`, cut 7. Full rerun passed all 397. |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_console_subprocess.py -k test_guided_decline_invalid_and_eof_no_dispatch` | 1 passed on isolated rerun. `git diff --exit-code HEAD -- reference/token_reward` confirmed the suite was untouched. |
| `python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the remaining three suites | `provider_facts` 86, `payment_effects` 28 and `economics` 99 passed. |
| `python3.12 scripts/check_openapi_contract.py` and the same command with `--self-test` | Both exited 0. |
| `python3.12 scripts/check_integration_gate_openapi.py` and the same command with `--self-test` | Both exited 0. |
| `python3.12 -m unittest integration_gate.test_offline_limits` | 11 passed. |
| `bash -ex -o pipefail` on the extracted **Stdlib offline document checks** block using `python3.12` | All 69 commands exited 0. Docs index scanned 465 documents, with 430 indexed and 35 allowlisted. CI test discovery and its 18 negative controls passed. |
| `python3.12 scripts/verify_runtime_architecture.py` and `python3.12 scripts/test_runtime_architecture.py` | Architecture gate passed. All 7 architecture tests passed. |
| `cargo fmt --all -- --check` from `runtime/` | Exit 0. |
| `cargo test -p kix-kernel --locked --offline` | Runtime workspace exit 101 at DuckDB resolution. Temporary workspace exit 0, 139 tests passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Runtime workspace exit 101 at DuckDB resolution. Temporary workspace exit 0. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` | Runtime workspace exit 101 at DuckDB resolution. Temporary workspace exit 0 and shows `kix-types` as the sole normal dependency. |
| `cargo test --workspace --locked --offline` | Runtime workspace exit 101 at DuckDB resolution. Temporary workspace exit 0, 332 tests passed. |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Runtime workspace exit 101 at DuckDB resolution. Temporary workspace exit 0. |
| `python3.12 scripts/check_cargo_offline_cache.py --require` | Exit 1. The cache contained 14 of 378 locked registry archives. |
| Inline `python3.12` temporary workspace setup and `diff -qr` for each of its six crates | Copied byte-identical crate trees and selected their original lockfile entries. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0 for the three KTX dependency-evidence inputs. |
| `python3.12 scripts/check_docs_index.py` and `python3.12 scripts/check_ci_test_discovery.py`, each plain and with `--self-test` | All four passed on the final documentation. Workflow discovery reaches 32 F04 test files. |
| `git hash-object` on both locked files and the new pack, `sha256sum` on all three sources and the new pack, and `cmp` on the sorted `reference/v0.3-rc1` SHA-256 manifests | Both locked blobs and all source pins matched. The manifest matched byte for byte. The new pack's SHA-256 and Git blob matched the index pins. |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks docs/contracts .github/workflows reference/booking_resale_admission sdk` | Exit 0. |
| `git diff --check`, `git status --short --untracked-files=all`, `git rev-parse HEAD refs/remotes/origin/main` and inline `python3.12` using `git status --porcelain=v1` and `git show` | Exactly eight changed paths and no whitespace issues, including added files. HEAD and cached main matched the base. Removing the appended family restored the exact prior index bytes. |

The reference commands are from **Offline reference state machines and
OpenAPI pins**. [Protocol workflow](../../.github/workflows/protocol.yml#L289) · [Document checks](../../.github/workflows/protocol.yml#L203)

The offline fallback covers `kix-types`, `kix-feature-semantics`,
`kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and `kix-delegated-exec` with
the pinned Rust 1.98.1 toolchain. `kix-analytics-audit` and `kix-bcs1` remain
unverified locally. Hosted bootstrap, Move, chain, storage and ZK stages
are outside the local checks for the touched paths.

## Source pins

| Artifact | Raw SHA-256 |
| --- | --- |
| `sdk/conformance/vectors/commerce-fixture-tuple.vectors.json` | `c9fbeee6a04da371dd054a325c9435a401b9694a1619ac9939de38f257495e22` |
| `reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json` | `6819d46a7b86e1a16bae83be90666560bb45aa66d3d6f0d5e050e03e7a952998` |
| `reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json` | `f9555d84790b91eafe74c71453a2dbd301fae43566a5f0a3a47e19059151e9cc` |
| `reference/credit_advance_f04/fixtures/capital_resale_distribution_checkpoints_vectors_v1.json` | `ed4c3f4385283f1cf0fc63b51806afa27973a43d38ad87aa58c428f20cc12385` |

The new pack's Git blob is `3277a2bf77eb1f429a2b7d779dee8622fd773603`.
The index pins the same artifact for both input and output.

## Protected files

| Artifact | Verified identity before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | Identical sorted 108-file SHA-256 manifests, with manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` |

## Files changed

- `docs/README.md`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `reference/credit_advance_f04/fixtures/capital_resale_distribution_checkpoints_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `reference/credit_advance_f04/test_capital_resale_distribution_checkpoints.py`
- `validation/2026-11-25-plan-capital-resale-distribution-checkpoints/README.md`

## Scope and delivery gates

The observed behavior matches the applicable receipt and contract predicates.
No explicit contract violation or additional contract-undefined behavior was
found. The evidence covers synthetic, process-local execution and is
source-informed Class B. External `kix-capital` acceptance remains
`UNVERIFIED`. Product limits and tolerance policy remain `UNDETERMINED` with
Astra, and legal responsibility remains `UNDETERMINED` with User/legal.
Live funds, provider calls, production execution, durability, distributed
fencing, bank exactly-once, chain finality and legal compliance are outside
this verification scope.

The implementation and final task commits await the supervisor. A2 non-author
review and exact-head KTX kernel verification and KIX protocol verification
run IDs, statuses and conclusions are pending. Merge SHA and post-merge CI
are inapplicable to this worktree delivery.
