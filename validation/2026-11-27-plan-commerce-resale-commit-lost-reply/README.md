# Commerce resale settlement commit lost-reply validation

The task input for `plan-commerce-resale-commit-lost-reply` is the node spec
and design plan supplied by the supervisor from planner run `1795732059`.
There is no task issue or dedicated `docs/tasks/` file. The task branch is
`agent/kix-plan-commerce-resale-commit-lost-reply`. The starting HEAD and the
cached `origin/main` both resolve to `4815986627ac8702e0b2a588d5fc92210f2f3374`,
the base in the plan.

## Coverage

| Requirement | Existing coverage | Evidence in this change |
| --- | --- | --- |
| Replay all 16 ordered setup calls on fresh hosts | Partial. `test_vectors` in `test_commerce_fixture_tuple_conformance.py` covers the pinned setup order. `test_delivery_controls_the_caller_observation` in `test_commerce_withheld_resale_refusal.py` checks the pre-commit refusal on its own. | The new replay compares the 15 accepted setup receipts on both hosts with the two pinned receipt files. The last setup call must return `SETTLEMENT_NOT_COMMITTED` and preserve all five accepted states and journals before the commit attempt. |
| Same caller record for both losses | Partial. `test_both_losses_have_the_same_caller_observation` in `test_commerce_cancel_lost_reply.py` covers cancellation transport. | The recorded commit envelope yields the same original operation ID and body key, one attempt, `UNKNOWN`, a null receipt and zero follow-up calls in both histories. |
| Zero dispatches leave `CAPTURED` and one leaves `COMMITTED` | Partial. `test_vectors` covers a successful commit and its journal delta. The paired fault was uncovered. | The pre-dispatch drop preserves all five snapshots. The withheld reply adds one complete settlement `commit` entry for `settle-resale` and `mv-resale`, preserving every journal prefix. |
| Complete commit golden | Sufficient for a delivered receipt. `test_vectors` compares the success against journey step 23. | The withheld receipt matches the complete canonical UTF-8 bytes of the same pinned golden. |
| Preserve payment and seller at version 1 without transferring or distributing | Partial. The pre-commit refusal replay covers ownership before commit. | Both histories retain the payment reference and amount, the `BOUND` listing and `buyer-A` as holder of `issue-A` at version 1. The dispatch log allows only the commit, and `claim.distributed_cash` stays zero. |
| Delivery index and selector | The previous index and SDK loop covered earlier pairs. The two commit cases were uncovered. | The index records eight fixtures and 17 cases. Both new cases share a caller pointer and have distinct producer pointers. The Python mutation check rejects substituting the hidden receipt for the caller record, and SDK conformance checks `HOLD_SEMANTIC` with null vector ID for both losses. |

[Paired fixture](../../reference/booking_resale_admission/fixtures/commerce_resale_commit_lost_reply_v1.json) ·
[Focused replay](../../reference/booking_resale_admission/test_commerce_resale_commit_lost_reply.py) ·
[Delivery evidence index](../../docs/status/COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json)

## Local verification

Python 3.12.15, Node 24.22.1 and Rust 1.98.1 were available. Python
commands ran with `PYTHONDONTWRITEBYTECODE=1` exported. Commands ran from the
repository root except where indicated.

| Command | Result |
| --- | --- |
| `PYTHONPATH=reference/booking_resale_admission python3.12 -B -m unittest -v test_commerce_resale_commit_lost_reply test_commerce_delivery_evidence_index` | Exit 0 on both runs. Seven tests passed per run, including the two fault histories. |
| `npm --prefix sdk run conformance` | Exit 0. 30 tests passed, including the selector checks for all 17 indexed cases and the recovery verdict. |
| `npm --prefix sdk run verify-compat` | Exit 0. The `bootstrap-2` manifest verified. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The Commerce fixture manifest verified. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for `booking_resale_admission`, `settlement_f01_f03`, `credit_advance_f04`, `ai_delegation`, `token_reward`, `provider_facts`, `payment_effects` and `economics` | All exit 0. Suite counts in order were 1,097, 224, 335, 182, 397, 86, 28 and 99. The booking suite includes existing loopback checks. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0. 13 tests passed. |
| `python3.12 -B scripts/$check.py` and `python3.12 -B scripts/$check.py --self-test` for `check_docs_index`, `check_ci_test_discovery`, `check_openapi_contract`, `check_integration_gate_openapi` and `check_sdk_client` | All exit 0. The SDK and OpenAPI pins cover 84 commands and CI discovery reaches the replay. |
| `awk` selection of the `Stdlib offline document checks` run block in `.github/workflows/protocol.yml` piped to `bash -ex` with `python3.12 -B` | Exit 0 for the 68 selected commands. The standalone loopback host probe was omitted and its fake-socket self-test ran. The cache preflight reported 14 of 378 packages available. |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce-resale-commit-calculation.json` | Exit 0. Calculation checks reported PASS and zero external calls. |
| `python3.12 -B scripts/verify_canonical.py --report .local/verification/commerce-resale-commit-canonical.json` | Exit 0. Python and TypeScript canonical contract checks reported PASS. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0. Architecture and dependency boundary passed. |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0. Seven tests passed. |
| `cargo fmt --all -- --check` | Exit 0 in `runtime/`. |
| `cargo test -p kix-kernel --locked` | Exit 101 in `runtime/` during offline resolution of `duckdb`. Exit 0 in the isolated kernel workspace. |
| `cargo clippy -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 in `runtime/` during offline resolution of `duckdb`. Exit 0 in the isolated kernel workspace. |
| `cargo tree -p kix-kernel --edges normal --locked` | Exit 101 in `runtime/` during offline resolution of `duckdb`. Exit 0 in the isolated kernel workspace, showing only `kix-types` as a dependency. |
| `cargo test --workspace --locked` and `cargo clippy --workspace --all-targets --locked -- -D warnings` | Each exited 101 in `runtime/` during offline resolution of `duckdb` before the checks started. |
| `cargo generate-lockfile` | Exit 0 in the isolated kernel workspace. |
| `git diff --check` | Exit 0. |

Cargo ran with `CARGO_NET_OFFLINE=true`. The isolated checks used byte copies
of `kix-kernel` and `kix-types` and a generated two-crate lockfile in a
temporary directory under `.local/verification/`. The full workspace still
requires its dependency cache. CI provisioning, standalone HTTP integration
and readiness, Move, local chain and ZK jobs were outside the local checks for
these paths.

## Preservation

| Command or check | Before and after |
| --- | --- |
| `git rev-parse origin/main HEAD` | Both refs resolved to `4815986627ac8702e0b2a588d5fc92210f2f3374` on each check. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | The required blobs matched, respectively `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git rev-parse HEAD:reference/v0.3-rc1` and byte verification using `git ls-tree -rz HEAD -- reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The worktree had exactly the same 108 paths and every blob matched. |
| `git diff --exit-code HEAD -- .aiops docs/tasks .github/workflows runtime reference/v0.3-rc1` and `git status --porcelain --untracked-files=all` on those paths | No diffs or untracked files in those paths. |
| `sha256sum` and `git hash-object` on `commerce_resale_commit_lost_reply_v1.json` | SHA-256 `e7d0b544cb9e2ab715b8facac60bb2aab403b0807da3df9a58e49cfe97d9fa07` and blob `100942709a1763eb8e58a0773916e81d4599b787`. The index matches both digests. |

## Delivery state

The supervisor holds Git and GitHub publication. This session used the cached
`origin/main` because the supervisor prohibited network access. Remote
freshness is unverified. The planner run directory was unavailable locally;
the supplied task and design contain the execution input.

| Gate | State |
| --- | --- |
| Implementation head and final task head | Worktree delivery. HEAD stays at the recorded base until the supervisor commits. |
| KTX kernel verification | Exact-head run ID, status and conclusion unavailable. |
| KIX protocol verification | Exact-head run ID, status and conclusion unavailable. |
| A2 non-author review | Pending on the supervisor's committed head. |
| Merge and main CI | No merge commit or post-merge run for this delivery. |

The observed transitions match the settlement commit and the bound resale
requirements in the mock contracts. The replay found no contract violations or
undefined transition behavior. All 13 unpublished reads and operation recovery
remain `NOT_BOUND`. External Commerce acceptance remains `UNVERIFIED`. The
evidence covers source-informed synthetic in-process replay. Its scope excludes
production runtime, real provider execution, durability and chain finality.
Product TTLs, fees, compensation and provider, legal and accounting terms
remain `UNDETERMINED`.
[Settlement contract §9.2](../../docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md#92-전이) ·
[Booking, Resale and Admission Gates](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md)

## Changed paths

- `docs/README.md`
- `docs/status/COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/fixtures/commerce_resale_commit_lost_reply_v1.json`
- `reference/booking_resale_admission/test_commerce_resale_commit_lost_reply.py`
- `reference/booking_resale_admission/test_commerce_delivery_evidence_index.py`
- `sdk/conformance/conformance.test.mjs`
- `validation/2026-11-27-plan-commerce-resale-commit-lost-reply/README.md`
