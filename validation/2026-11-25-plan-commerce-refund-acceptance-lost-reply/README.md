# Commerce refund acceptance lost-reply validation

`plan-commerce-refund-acceptance-lost-reply` uses the supplied node spec and
design plan from planner run `1795523250`. The spec was delivered in the
builder brief. The node has no issue or `docs/tasks/` document.

The cached `origin/main` and starting `HEAD` both resolved to
`1643f17b1b65eedafd9b15934a8b020dc1c0ab68` on
`agent/kix-plan-commerce-refund-acceptance-lost-reply`.
[Consumer handoff](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md#consumer-handoff)

## Coverage

| Requirement | Existing coverage | Evidence in this change |
| --- | --- | --- |
| Ordered setup, ordinary acceptance and receipt resolution | Sufficient. `CommerceFixtureTupleTests.test_inventory_and_edges`, `test_vectors` and `test_all_first_acceptances_resolve` cover these paths. | Both histories replay all 13 setup calls and compare their complete receipts. |
| Mock acceptance leaves external return open | Sufficient. `SettlementFsmTests.test_full_refund_acceptance_does_not_close_an_external_return` covers the settlement contract. | Both live settlement and claim views keep `funds_executed` and `external_return_closed` false. The settlement stays `CAPTURED`. |
| Missing-reply caller behavior | Partial. `CommerceIssuanceLostReplyTests.test_both_losses_have_the_same_caller_observation` covers the fault pattern for issuance. | `CommerceRefundAcceptanceLostReplyTests.test_both_losses_have_the_same_caller_observation` records the exact submitted envelope and the single shared `UNKNOWN` observation. |
| Refund balances behind the missing reply | Gap. The ordinary refund replay has a delivered receipt. | Before dispatch, all five snapshots are preserved and 12,000 KRW remains outstanding. After dispatch, 12,000 KRW is accepted, one journal entry is appended and all five journal prefixes are preserved. The full hidden receipt matches the step 38 golden. |
| Recovery lookup | Sufficient in the grant-selection corpus. `proposed-uncertain-operation-recovery` expects `NOT_BOUND` and a null vector ID. | The pair verifies that status and records zero follow-up calls in either history. |

[Commerce tuple suite](../../reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py) ·
[Settlement suite](../../reference/settlement_f01_f03/test_settlement_fsm.py) ·
[Issuance replay](../../reference/booking_resale_admission/test_commerce_issuance_lost_reply.py) ·
[Refund acceptance replay](../../reference/booking_resale_admission/test_commerce_refund_acceptance_lost_reply.py)

## Source pins

| Input | SHA-256 | Git blob |
| --- | --- | --- |
| [Commerce tuple vectors](../../sdk/conformance/vectors/commerce-fixture-tuple.vectors.json) | `c9fbeee6a04da371dd054a325c9435a401b9694a1619ac9939de38f257495e22` | `0095e53801921e87c5417dd86920a625c2fede78` |
| [Journey receipts](../../reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json) | `6819d46a7b86e1a16bae83be90666560bb45aa66d3d6f0d5e050e03e7a952998` | `e9f34b8f35ed7f6a0867f1d2036bda521ee15eab` |
| [Booking branch receipts](../../reference/booking_resale_admission/fixtures/commerce_booking_branch_receipts_v1.json) | `1268382cdce28c931e160e253a6cafdac0f74de4124a53df1c78bd625f4b82c4` | `ab98cce8492b21b29871c4c1ad4ccda1a722d9ed` |

## Local verification

Commands ran from the repository root with Python 3.12.15, Node 24.22.1 and
Rust 1.98.1. In the table, `$bra` is `reference/booking_resale_admission`
and `$checker` is
`validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`.

| Command | Result |
| --- | --- |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_refund_acceptance_lost_reply.py -v` | Exit 0. One test passed with both fault points. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_fixture_tuple_conformance.py -v` | Exit 0. All 9 tests passed. |
| `python3.12 -B "$checker"` and `python3.12 -B "$checker" --self-test` | Both exited 0. The 13 listed reads stayed `NOT_BOUND` and all 10 negative controls passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -` using unittest discovery over `$bra` and filtering out `AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit` | Exit 0. All 1,084 selected tests passed. The excluded case opens a loopback socket. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` | All seven invocations exited 0. `settlement_f01_f03` passed 224 tests, `credit_advance_f04` 322, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99. |
| `python3.12 -B -` invoking the `Stdlib offline document checks` Python commands from `.github/workflows/protocol.yml` with Python 3.12 and `-B` | All 68 invocations passed, including docs index, CI test discovery, consumer binding and their self-tests. The plain loopback socket probe was omitted. |
| `python3.12 -B` on `scripts/check_docs_index.py` and `scripts/check_ci_test_discovery.py`, plain and with `--self-test` | All four direct reruns exited 0. |
| `python3.12 -B` on `scripts/check_openapi_contract.py`, `scripts/check_integration_gate_openapi.py` and `scripts/check_sdk_client.py`, plain and with `--self-test` | All six invocations exited 0. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits readiness.test_faults` | Exit 0. All 109 tests passed. |
| `npm_config_offline=true npm --prefix sdk run conformance` | Exit 0. All 26 tests passed, including the unbound recovery lookup. |
| `npm_config_offline=true npm --prefix sdk run verify-compat` | Exit 0. Verified `bootstrap-2`. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. Verified the scoped Commerce manifest. |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce.json` and `python3.12 -B scripts/verify_canonical.py --report .local/verification/canonical.json` | Both exited 0. The synthetic calculations and Python/TypeScript canonical agreement passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exited 0. The architecture gate and all 7 self-tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Recorded the KTX workflow input hashes. |
| `cargo test --offline --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 before compilation. The offline index lacked `duckdb` for `kix-analytics-audit`. |
| `cargo clippy --offline --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 with the same missing cache entry. |
| `cargo tree --offline --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 with the same missing cache entry. |
| `cargo test --offline --manifest-path runtime/Cargo.toml --workspace --locked` and `cargo clippy --offline --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Both exited 101 with the same missing cache entry. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | Exit 0 in reporting mode. Found 14 of 378 locked registry packages cached. |
| `cp -R` and `diff -qr` for `kix-kernel` and `kix-types` in a temporary workspace under `.local/verification/` | Both copies matched their sources. |
| `cargo generate-lockfile --offline --manifest-path "$manifest"` in that two-crate workspace | Exit 0. |
| `cargo test --offline --manifest-path "$manifest" -p kix-kernel --locked` and a rerun with `--quiet` | Both exited 0. All 139 kernel tests passed. |
| `cargo clippy --offline --manifest-path "$manifest" -p kix-kernel --all-targets --locked -- -D warnings` and `cargo tree --offline --manifest-path "$manifest" -p kix-kernel --edges normal --locked` | Both exited 0. Clippy passed and the only normal dependency was `kix-types`. |
| `sha256sum` and `git hash-object` on the three pinned inputs | Both exited 0 and produced the hashes in the source pin table. |
| `python3.12 -B -` resolving the two new relative links under **Consumer handoff** | Exit 0. Both resolved to the intended files. |
| `git ls-tree HEAD`, `git hash-object` on the locked files, `git diff --exit-code HEAD` and `git ls-files --others` on protected paths | Both blobs and the frozen tree matched. The final protected-path check found zero differences or additions. |
| `git diff --check` and `python3.12 -B -` checking whitespace in all three new files | Both exited 0. |

## Preservation and delivery

| Protected input | Identity checked before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/` | Git tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

The supervisor's offline rule supersedes the routine fetch. Remote main
freshness remains unverified. The worktree changes are uncommitted, so
implementation and final task commit SHAs are pending. The A2 non-author
review and exact-head KTX and KIX run IDs, statuses and conclusions are
pending supervisor delivery. Merge SHA and post-merge CI are inapplicable.

The isolated Rust checks cover the kernel and its normal dependency.
Full-workspace Rust tests and Clippy remain unverified. Socket-based HTTP,
local-chain, Move, ZK and storage probes were outside the offline checks for
these paths.

## Changed paths

- `docs/README.md`
- `docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md`
- `reference/booking_resale_admission/fixtures/commerce_refund_acceptance_lost_reply_v1.json`
- `reference/booking_resale_admission/test_commerce_refund_acceptance_lost_reply.py`
- `validation/2026-11-25-plan-commerce-refund-acceptance-lost-reply/README.md`

## Scope

The replay is source-informed evidence for synthetic, in-memory producer
behavior. It surfaced zero contract discrepancies or undefined behaviors.
External Commerce acceptance remains `UNVERIFIED`. Real funds, PG, bank, KYC,
production execution, chain finality, durability and distributed fencing are
outside this evidence. Product fees and compensation and legal, accounting
and provider terms remain `UNDETERMINED` with their existing owners.
