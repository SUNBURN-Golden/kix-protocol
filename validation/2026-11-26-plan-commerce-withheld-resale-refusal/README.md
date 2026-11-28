# Commerce pre-commit resale refusal delivery

The task input for `plan-commerce-withheld-resale-refusal` is the supervisor's
node specification and supplied design from planner run `1795611291`. This
node has no issue or task file under `docs/tasks/`. The starting HEAD on
`agent/kix-plan-commerce-withheld-resale-refusal` and the cached
`origin/main` both resolved to `4c5ea5a036741571fde18d71cfc6f464b76236f2`.
The supervisor required offline work, so fetch was skipped and remote
freshness is unverified.

## Coverage

| Requirement | Existing coverage | New fixture and replay evidence |
|---|---|---|
| Exact request, setup and refusal | Sufficient for producer behavior. `CommerceFixtureTupleTests.test_vectors` covers the refusal, and `test_booking_branch_full_receipts` covers the three branch receipts. | Each of three fresh hosts runs the same 15 ordered setup calls, with canonical comparisons against 12 journey receipts and three booking branch receipts. The target and both receipt sources are byte-pinned. Journey step 22 supplies the refusal oracle. |
| Caller observes only the outcome delivered | Partial. `CommerceTransferLostReplyTests.test_both_losses_have_the_same_caller_observation` covers a successful producer transfer with a withheld reply. | Only delivery exposes `SETTLEMENT_NOT_COMMITTED`. The two loss records match canonically, including the original operation ID and body key, one attempt, `UNKNOWN`, a null receipt and zero follow-up calls. The replay checks the exact caller field set for each loss. |
| Drop before dispatch versus refusal withheld | Uncovered for this vector. | The harness counts dispatches after setup and captures actual producer refusal codes. Counts are 1, 0 and 1, with the exact refusal recorded on both dispatches. |
| Preserve recorded payment, ownership, right version and accepted journals | Partial. `CommerceBoundResaleVectorTests.test_refusals_preserve_all_machines` covers state and journal preservation for existing bound refusal histories. | All three cases compare complete canonical state and accepted journals before and after the attempt for reservation, resale, settlement, admission and credit. The listing stays `PAYMENT_NOTED` at amount 12,000, the settlement stays `CAPTURED`, and seller `buyer-A` retains right `issue-A` at version 1. |
| Recovery stays fenced and both fixtures are discoverable | The grant selection vector already covers `NOT_BOUND`. The paired transfer fixture already covers transferred ownership at version 2 when a success reply is withheld. | The replay checks the specific proposed recovery selection and its null vector ID. The surface map links both fixture replays and the existing recovery boundary. |

[Portable fixture](../../reference/booking_resale_admission/fixtures/commerce_withheld_resale_refusal_v1.json) ·
[Focused replay](../../reference/booking_resale_admission/test_commerce_withheld_resale_refusal.py) ·
[Consumer surface map](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification)

## Local verification

Commands ran from the repository root unless otherwise stated. `$bra` is
`reference/booking_resale_admission`. Python was 3.12.15 for the replays
and 3.13.5 for the architecture checks. Node was 24.22.1. The SDK commands
ran with `npm_config_offline=true`.

| Command | Result |
|---|---|
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_withheld_resale_refusal.py -v` | Exit 0. One test covering three delivery cases passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_fixture_tuple_conformance.py -v` | Exit 0. Nine tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_transfer_lost_reply.py -v` | Exit 0. One test covering both loss cases passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,087 tests passed, including the suite's existing loopback admission test. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,087 tests passed again with bytecode writing disabled in subprocesses. |
| `python3.12 -B -` running the `Stdlib offline document checks` commands from `.github/workflows/protocol.yml`, excluding the standalone loopback host report | All 68 invocations exited 0, including `check_docs_index.py` and `check_ci_test_discovery.py` with and without `--self-test`. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and `python3.12 -B scripts/check_sdk_client.py`, each also run with `--self-test` | All six invocations exited 0. The 84-command catalogue and pins verified. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0. Eleven tests passed. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for `settlement_f01_f03` and `credit_advance_f04` | Both exited 0. Settlement passed 224 tests and credit passed 331. |
| `npm --prefix sdk run conformance` | Exit 0. All 27 tests passed, including the proposed recovery lookup verdict. |
| `npm --prefix sdk run verify-compat` | Exit 0. The `bootstrap-2` manifest verified. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The scoped Commerce manifest verified. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/verify_commerce.py --report "$report_dir/commerce.json"` and `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/verify_canonical.py --report "$report_dir/canonical.json"` | Both exited 0 and reported `PASS`, with reports in a temporary directory. |
| `python3 -B scripts/verify_runtime_architecture.py` and `python3 -B scripts/test_runtime_architecture.py` | Both exited 0. The architecture check and all seven regression tests passed. |
| `python3.12 -B -` resolving the two fixture links, two test links, the recovery anchor and the documentation index | Exit 0 on both runs. Links resolved. The prior successful transfer still records a hidden receipt and buyer-2 ownership at version 2. |
| `git diff --check` | Exit 0. |

### Rust workspace and offline fallback

Cargo used pinned toolchain 1.98.1 with `CARGO_NET_OFFLINE=true`. The
repository workspace commands ran in `runtime/`. The fallback copied the
six crates without registry dependencies into a temporary workspace, kept
the toolchain pin, used `cargo generate-lockfile --offline`, and compared
each of its six resolved package records to the checked-in lock. The cache
gap leaves the full workspace tests and Clippy pending.

| Command | Repository workspace | Temporary six-crate workspace |
|---|---|---|
| `cargo fmt --all -- --check` | Exit 0. | — |
| `cargo test -p kix-kernel --locked` | Exit 101. Missing offline `duckdb` index entry during workspace resolution. | Exit 0. 139 tests passed. |
| `cargo clippy -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101. Same resolution failure. | Exit 0. |
| `cargo test --workspace --locked` | Exit 101. Same resolution failure. | Exit 0. 332 tests passed. |
| `cargo clippy --workspace --all-targets --locked -- -D warnings` | Exit 101. Same resolution failure. | Exit 0. |
| `cargo tree -p kix-kernel --edges normal --locked` | Exit 101. Same resolution failure. | Exit 0. Reports `kix-types` as the sole kernel dependency. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` | Exit 1. 14 of 378 locked registry packages present. | — |

### Preservation

`git hash-object` matched both §4 blobs before and after work.

| Locked path | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git rev-parse` reports frozen tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`
on both HEAD and cached `origin/main`. A local Python comparison against
`git ls-tree -rz HEAD -- reference/v0.3-rc1` and `git cat-file blob` compared
all 108 paths. The first post-test comparison exited 1 because Python test
subprocesses created five ignored bytecode files under `__pycache__/`. A
local Python cleanup verified the files were untracked and removed only
those files and the empty cache directory. The comparison matched all 108
paths before work and again after the bytecode-disabled rerun.
`git diff --exit-code HEAD --` on the
protected and pinned paths exited 0. `git status --short --branch --untracked-files=all`
showed the five paths listed below.

## Delivery and scope

The supervisor receives a worktree patch. An implementation commit, a final
delivery SHA and A2 non-author review remain pending. Exact-head KTX kernel
and KIX protocol CI run IDs, statuses and conclusions are unavailable in this
session. Merge SHA and post-merge CI are inapplicable. Local verification
covered the affected paths and their immediate dependencies. The offline
session omitted the CI bootstrap, storage, disposable-chain and ZK jobs.

The replay matches the existing resale contract. It surfaced no contract
violation or undefined behavior. Rejected-key retention is process-local,
outside the accepted state and journals compared here. Recovery stays
`NOT_BOUND`. External Commerce acceptance stays `UNVERIFIED`. Product TTLs,
fees, compensation and provider terms stay `UNDETERMINED`.
Evidence is source-informed and limited to synthetic in-process behavior.
Live funds, provider or chain effects, persistence and runtime qualification
are outside its scope.
[Resale contract](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#105-정산-게이트)

## Changed paths

- `docs/README.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/fixtures/commerce_withheld_resale_refusal_v1.json`
- `reference/booking_resale_admission/test_commerce_withheld_resale_refusal.py`
- `validation/2026-11-26-plan-commerce-withheld-resale-refusal/README.md`
