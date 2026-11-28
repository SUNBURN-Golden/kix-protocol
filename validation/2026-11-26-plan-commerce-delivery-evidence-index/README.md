# Commerce delivery evidence index

The task input for `plan-commerce-delivery-evidence-index` is the supplied
node specification and design from planner run `1795647575`. The node has no
GitHub issue or task document under `docs/tasks/`. The starting HEAD on
`agent/kix-plan-commerce-delivery-evidence-index` and cached `origin/main`
both resolved to `847aace358208af0235cfc9dd440b7c321ef2f48`. The supervisor
required offline work, so `git fetch origin main` was omitted and remote
freshness is unverified.

The non-normative index pins nine files by raw SHA-256 and Git blob ID. Its
13 rows link the fixture cases to their source vectors, caller observations
and producer diagnostics. The checker also verifies the existing vector and
receipt pins recorded inside the fixtures. All 12 losses retain the original
operation ID and body key, `UNKNOWN`, a null receipt, one attempt and zero
follow-up calls. Commerce sees `SETTLEMENT_NOT_COMMITTED` on delivery of the
pre-commit refusal. The proposed recovery and all 13 unpublished reads retain
`NOT_BOUND`.
[Delivery evidence index](../../docs/status/COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json) ·
[Consumer surface map](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification)

## Coverage

The replay modules below are in `reference/booking_resale_admission/`.

| Requirement | Prior coverage | Added evidence |
|---|---|---|
| Payment observation, issuance and transfer before and after dispatch | Sufficient for both outcomes. Each `test_both_losses_have_the_same_caller_observation` checks caller identity and producer deltas in `test_commerce_payment_observation_lost_reply.py`, `test_commerce_issuance_lost_reply.py` and `test_commerce_transfer_lost_reply.py`. | Exact cross-fixture associations to the shared tuple vectors and each producer record. |
| Admission consumption and refund acceptance before and after dispatch | Sufficient for both outcomes. `test_loss_before_dispatch` and `test_loss_after_dispatch` in `test_commerce_admission_lost_reply.py` and `test_both_losses_have_the_same_caller_observation` in `test_commerce_refund_acceptance_lost_reply.py` check the respective observations and producer deltas. | Exact associations, including rejection of the hidden refund receipt as a caller pointer. |
| Delivered, dropped and withheld pre-commit refusal | Sufficient for behavior. `test_delivery_controls_the_caller_observation` in `test_commerce_withheld_resale_refusal.py` checks all three caller and producer outcomes. | Exact pointer checks reject swaps even when the source values are equal, plus substitution of a withheld refusal code or a different fixture's caller pointer. |
| Recovery and unpublished reads | Sufficient for the existing binding policy. `sdk/conformance/conformance.test.mjs` exercises grant selection and cross-checks the binding index. | Resolve the recovery decision and match the 13 unique read names across both records. Detached controls cover missing and promoted bindings. |
| Each delivery case resolves exactly once | Previously uncovered across the six fixtures. | Enumerate the cases independently of the index. A detached duplicate replacing a valid case fails even when the case count is preserved. |

## Local verification

Commands ran in the foreground. Focused runs and protocol checks used Python
3.12.15 with bytecode disabled. Architecture checks used Python 3.13.5. SDK
checks used Node 24.22.1 and `npm_config_offline=true`.

The focused command ran first from the repository root.

```bash
bra=reference/booking_resale_admission
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$bra" python3.12 -B -m unittest -v \
  test_commerce_delivery_evidence_index \
  test_commerce_payment_observation_lost_reply test_commerce_issuance_lost_reply \
  test_commerce_transfer_lost_reply test_commerce_admission_lost_reply \
  test_commerce_refund_acceptance_lost_reply test_commerce_withheld_resale_refusal
```

| Command | Actual result |
|---|---|
| Focused command above | Exit 0. Six index tests and seven replay tests passed across the six fixture modules. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,093 booking, resale and admission tests passed. |
| `python3.12 -B -` executing the `Stdlib offline document checks` commands from `.github/workflows/protocol.yml` with `python3.12 -B` | All 69 invocations exited 0, including the documentation index, producer tuple, read-model source map and CI discovery checks and their self-tests. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`, with and without `--self-test` | Both exited 0 in the workflow block and direct rerun. All 13 reads stayed `NOT_BOUND`, and all ten negative controls passed. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and `python3.12 -B scripts/check_sdk_client.py`, each with and without `--self-test` | All six invocations exited 0. The 84-command catalogue and pins verified. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0. All 11 tests passed. |
| `npm --prefix sdk run conformance` | Exit 0. All 28 tests passed, including the unbound reads and proposed recovery verdict. |
| `npm --prefix sdk run verify-compat` | Exit 0. The `bootstrap-2` manifest verified. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The scoped Commerce manifest verified. |
| `python3 -B scripts/verify_runtime_architecture.py` and `python3 -B scripts/test_runtime_architecture.py` | Both exited 0. The architecture gate and seven regression tests passed. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` | Exit 1. The cache contains 14 of 378 locked registry packages. |
| `python3.12 -B -` comparing each index pin to `git rev-parse HEAD:<path>` and resolving both documentation links | Exit 0. The nine pins match the base and the links resolve. |
| `git diff HEAD --exit-code -- .aiops docs/tasks runtime reference/v0.3-rc1 reference/booking_resale_admission/fixtures sdk .github/workflows docs/contracts docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json` | Exit 0. The pinned sources, protected paths, workflows and runtime have zero tracked differences. |
| `git diff --check` | Exit 0. |
| `git status --short --branch --untracked-files=all` | Exit 0. The five paths below are the complete change set. |

### Offline Rust checks

The repository commands used `cargo +1.98.1` with `--manifest-path
runtime/Cargo.toml`. A temporary workspace used byte-for-byte copies of the six
crates with only workspace dependencies. It excluded `kix-analytics-audit` and
`kix-bcs1`, kept the pinned toolchain, and ran `cargo +1.98.1 generate-lockfile
--offline` with exit 0. All six resulting package records matched the repository
lockfile. The dependency cache gap leaves the full workspace checks pending.

| Cargo arguments | Repository workspace | Temporary six-crate workspace |
|---|---|---|
| `test -p kix-kernel --locked --offline` | Exit 101. Missing offline `duckdb` index entry during workspace resolution. | Exit 0. 139 tests passed. |
| `clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101. Same resolution failure. | Exit 0. |
| `tree -p kix-kernel --edges normal --locked --offline` | Exit 101. Same resolution failure. | Exit 0. `kix-types` is the kernel's sole normal dependency. |
| `test --workspace --locked --offline` | Exit 101. Same resolution failure. | Exit 0. 332 tests passed. |
| `clippy --workspace --all-targets --locked --offline -- -D warnings` | Exit 101. Same resolution failure. | Exit 0. |
| `fmt --all -- --check` | Exit 0. | — |

## Preservation

`git hash-object` matched both locked Git blob IDs before and after work.

| Path | Verified Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git rev-parse HEAD:reference/v0.3-rc1 origin/main:reference/v0.3-rc1`
returned tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` for both refs.
The Python byte comparison against `git ls-tree -rz HEAD` and `git cat-file
blob` verified all 108 paths and the complete path set before and after work.

## Delivery and scope

The supervisor receives the worktree patch. Implementation and final delivery
SHAs, A2 non-author review and exact-head KTX kernel and KIX protocol CI run
IDs, statuses and conclusions are pending. The merge SHA and post-merge CI are
inapplicable. The offline checks cover the affected paths and their immediate
dependencies. CI bootstrap, storage, disposable-chain and ZK jobs were outside
the verification scope.

The checker found zero contract violations or new undefined behaviors. The
existing scoped grant still governs semantic consumption. External Commerce
acceptance remains `UNVERIFIED`. Product TTLs, fees, compensation, visibility
and provider, legal and accounting terms remain `UNDETERMINED` with their
recorded owners. The checks cover pinned source-informed fixture evidence.
Live funds, provider calls, chain effects, persistence and production
qualification are outside the evidence scope.

## Changed paths

- `docs/status/COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `reference/booking_resale_admission/test_commerce_delivery_evidence_index.py`
- `validation/2026-11-26-plan-commerce-delivery-evidence-index/README.md`
