# Local synthetic payment scope router — 2026-10-30

Node/task: `plan-local-payment-scope-router`. Immutable task input is the
supervisor's node specification and read-only design supplied in the session;
no task issue or node document under `docs/tasks/` exists. Not ASTRA program mode.
Planner provenance: run `1793327754`; predecessor `plan-local-payment-lookup-adapter`.

Starting branch: `agent/kix-plan-local-payment-scope-router`.
Starting HEAD/base and locally observed `origin/main`:
`fae08dca658774568358c55d9db879626f6bcea4`. No local base delta.
`git fetch origin main` was not run because the supervisor forbids network
and GitHub actions. Remote freshness is unverified. Implementation/final committed
heads are pending the supervisor; this builder does not commit or publish.

## Coverage mapping recorded before adding router tests

Inspected the single-scope service/fake/binding tests and the required workflow
steps. Paths below are relative to `reference/provider_facts/`.

| Acceptance | Existing coverage classification | Router gap / planned evidence |
|---|---|---|
| Missing binding and scope mismatch; accepted call exactly once | Sufficiently covered at single scope: `test_payment_lookup.py::test_missing_binding_makes_zero_calls`, `::test_scope_mismatch_makes_zero_calls`, `::test_accepted_lookup_calls_fake_once_with_complete_bound_ref` | Partially covered in composition: verify missing route, empty registry, zero unselected calls and two registered scopes. |
| Unresolved A cannot reach successful B | Partially covered: `test_payment_lookup.py::test_timeout_and_error_do_not_retry_or_fallback`, `::test_unresolved_boundaries_preserve_state_and_make_one_call` | Cross-scope timeout/error/not-found isolation absent; successful B positive control with reused payment/order strings. |
| Reused operation strings across provider/account | Partially covered: `test_operation_binding.py::test_operation_scope_isolation` | Dispatch with independent provider/account differences; complete operation/reference outputs. |
| Environment comes only from bound payment | Not covered by router | Two environments selected through separate existing operations; no operation identity expansion. |
| Immutable registration and inconsistent-registration rejection | Not covered | Validate types and all scope dimensions before calls; mutate caller map and prove fixed dispatch. |
| No retries, rebinding, capture/review mutation | Partially covered: service tests' populated public snapshots; binding tests | Snapshot populated bindings/count/captures/reviews and every fake's recordings across router outcomes and guards. |
| Complete five-field identities and unchanged normalized outputs | Sufficient normalization coverage: `test_normalization_golden_vectors.py::test_literal_facts_bytes_and_digests`, `test_payment_lookup.py::test_all_existing_golden_vectors_through_service`; full-key fake test `test_fake_payment_lookup.py::test_complete_reference_keys_and_direct_scope_guard` | Partial composition coverage: compare whole results to fresh equivalent services, including same payment key/different order; reuse existing golden tests unchanged. |
| Invalid arguments/selectors rejected before calls | Partially covered: `test_payment_lookup.py::test_invalid_operation_and_request_selection_are_rejected_without_calls` | Verify router preserves error and rejects account/provider/environment/payment selectors. |
| Deterministic offline example | Not covered for router | Two successful scopes and unresolved/missing scenarios, exact call deltas and synthetic labels. |
| Document/index and CI discovery checks | Existing scripts and protocol workflow suite discovery | Run applicable checkers and self-tests without wiring/allowlist changes. |

Before edits, both locked Git blobs match:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.
A before-work path/SHA-256 manifest covers 121 files: both locks,
`reference/v0.3-rc1/**`, `.aiops/**` and `docs/tasks/**`.
Canonical sorted manifest SHA-256:
`52fc4fe4a06f133cebd843cc163cda730aef827969954fbca5a1a7f5ee492d78`.

## Delivered implementation and evidence

`PaymentLookupRouter(bindings, *, routes)` copies and validates the entire
registration before building a read-only `MappingProxyType` registry of
single-scope services sharing the existing store. It has no registration or
replacement method. `lookup(operation_ref)` reads the original binding, derives
provider/account/environment from its complete PaymentRef, and returns the
selected service's result unchanged. An empty registry has no default route.
No service, fake, normalizer, binding store, fixture or golden vector changed.

New evidence in `reference/provider_facts/test_payment_lookup_router.py`:

- `test_two_scopes_dispatch_only_to_bound_fake`: two registered scopes differing
  independently by provider, account or environment; exact complete-reference
  calls and no unselected calls. Provider/account variants reuse operation and
  payment/order strings. Environment variants use separate operations without
  changing OperationRef identity.
- `test_unresolved_scope_never_falls_back`: timeout, error and absent-recording
  not-found on A while B holds a successful recording with identical payment
  and order strings. A makes one call per explicit invocation, never to B;
  B's positive control succeeds. Repeated explicit calls do not retry internally.
- `test_missing_binding_and_route_make_zero_calls`: all scope dimensions and
  empty registry, binding-required precedence and complete missing-route refs.
- `test_inconsistent_registration_rejected_without_calls` and
  `test_invalid_registration_types_make_zero_calls`: constructor guards across
  every dimension and wrong key/value types, with zero fake calls.
- `test_route_configuration_is_copied_and_immutable`: caller replacement,
  insertion and clearing cannot replace/remove an existing route or add a route.
- `test_complete_identity_and_outputs_equal_single_scope_service`: whole result
  equivalence to fresh single-scope services for paid/cancel/unverified/not-found/
  float-text outcomes; same payment key with distinct order IDs stays distinct.
  This is composition equivalence, not an independent normalization oracle;
  unchanged literal golden-vector tests supply independent expected bytes/hashes.
- `test_selected_service_result_is_returned_unchanged`: exact returned-object
  identity and one service invocation. Invalid request selectors/operation
  arguments fail without calls; unrelated programming errors propagate.
- Public deep snapshots preserve bindings, count, nonempty historical captures,
  nonempty reviews and every fake's recordings across all actual router outcomes.
  Complete operation/payment references and fixed synthetic provenance are checked.
- `test_offline_example_is_deterministic_and_synthetic`: callable and subprocess
  output match; seven rows, two scoped successes, five unresolved diagnostics,
  exact per-scope call deltas and synthetic limitations. No sockets or services.

## Commands actually executed and results

Python validation used `PYTHONDONTWRITEBYTECODE=1`. Rust/Cargo are 1.98.1,
matching both workflow pins. Cargo ran with `CARGO_NET_OFFLINE=true` and
`--offline`; no dependency download. Commands ran sequentially as foreground
processes, with no shell background jobs. Logs were captured in `/tmp/` for
inspection; results below describe this worktree, not predecessor CI.

| Command | Actual result |
|---|---|
| `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Both SHAs and branch as recorded above; local refs only. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before/after: both exact locked blobs match. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p 'test_payment_lookup_router.py' -v` | Exit 0; 11 tests passed on first run. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | Exit 0; 62 tests passed, including unchanged golden vectors and single-scope coverage. |
| `python3 reference/provider_facts/example_payment_lookup_router.py` | Exit 0; seven deterministic synthetic JSON lines: two histories and five unresolved results; exactly the selected calls. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; passed. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; passed. |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_status_register.py` | Exit 0; passed. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_docs_index.py` | Exit 0; passed. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; passed. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; passed; router tests reached by existing suite discovery. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; passed. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; passed. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; passed. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; passed. |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0; 18/18 cached dependencies present, none missing. |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; passed. |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0; 9 tests passed. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture/dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `rustc --version`; `cargo --version`; `rustup toolchain list` | Rust/Cargo 1.98.1; installed active/default toolchain 1.98.1-x86_64-unknown-linux-gnu. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 139 passed, 0 failed, 0 ignored (sum of 9 result lines). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 339 passed, 0 failed, 0 ignored (sum of 46 result lines). |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; passed with warnings denied. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; passed; check mode only. |

The checker/architecture batch passed 23/23 commands. Checker self-tests emit
intentional negative-control diagnostics, with exit 0. No test or checker failed;
no implementation fix or re-run was needed. Final documentation/protection
checks are recorded below after the last evidence edit.

## Complete changed-path list

- `reference/provider_facts/payment_lookup_router.py` — synchronous fixed router.
- `reference/provider_facts/test_payment_lookup_router.py` — composition gaps above.
- `reference/provider_facts/example_payment_lookup_router.py` — offline example.
- `reference/provider_facts/README.md` — usage, diagnostics, configuration and limits.
- `docs/README.md` — validation record index link.
- `validation/2026-10-30-plan-local-payment-scope-router/README.md` — this evidence.

## Discrepancies, deviations and delivery gates

No class C contract violation found. Class B local synthetic characterizations:
registration rejects wrong types and inconsistent scope before any fake call;
missing binding precedes route resolution; missing exact route returns
`LOOKUP_ROUTE_MISSING` while retaining the bound complete PaymentRef. These are
local diagnostics, not protocol errors or product policy. Existing service
unresolved semantics and output types remain unchanged. Synthetic scope strings
confer no authentication or merchant authorization.

Provider authentication and merchant scope remain **UNDETERMINED — Toss/User**.
Event identity, aliases, domain/schema assignments and policy decisions remain
with Astra. No authority contract, status, evidence grade or owner value changed.

Deviations: fetch omitted under the supervisor's no-network instruction; remote
main freshness remains unverified. No node task document exists, so the supplied
specification/design is the immutable input. Added adjacent workflow OpenAPI,
offline-limit and offline-cache checks to the planned checks. No design or scope
deviation in implementation. No issue, comment, marker, commit, push, PR, branch
change, merge, history rewrite or tag action was performed.

The router only imports the existing synthetic lookup modules and binding/result
types. There is no economic/kernel call. State snapshots prove preservation of
populated local capture/review records, not an economic-engine integration test.
No HTTP endpoint, new protocol command, SDK change, credential, real funds,
PG/bank/KYC/Sui call, public endpoint, persistence, storage engine, polling,
retry, event mapping or runtime activation was introduced or exercised.
No authentication, provider conformance, durable custody, distributed fencing,
finality, payment completion, UNKNOWN release, exactly-once, legal compliance
or production-readiness claim. Complete hosted Move/ZK/protocol execution was
not run locally and is not implied by these CI equivalents.

| Delivery evidence | State |
|---|---|
| Implementation/final committed task head | Not created by builder; uncommitted worktree over starting HEAD above. Supervisor owns final commit/publication. |
| Non-author A2 exact-head review | PENDING on supervisor's final head; builder checks are not independent review. |
| KTX kernel verification exact-head run ID/status/conclusion | NOT_RUN / not observed; no GitHub/network actions. Must be completed/success on final head before merge-ready. |
| KIX protocol verification exact-head run ID/status/conclusion | NOT_RUN / not observed; same final-head gate applies. |
| Merge commit / post-merge main CI | N/A; no merge performed or authorized. |
| Builder delivery | Locally complete for supervisor handoff; not merge-ready. |

Remaining follow-up: supervisor's final-head publication, independent A2 review,
both required workflows, and any separately authorized merge/post-merge evidence.
Provider/owner open inputs remain separate work. No resource/policy STOP condition
was encountered; no `DECISION_REQUIRED.md` was needed.

## Final local verification

| Command | Actual result |
|---|---|
| `python3 scripts/check_docs_index.py` and the same command with `--self-test` | Final evidence-document check: both exit 0. |
| `python3 scripts/check_ci_test_discovery.py` and the same command with `--self-test` | Final discovery check: both exit 0. |
| `python3 scripts/check_class_b_index.py` and the same command with `--self-test` | Both exit 0; existing index citations unchanged. |
| `python3 scripts/check_contract_error_codes.py` and the same command with `--self-test` | Both exit 0; no protocol error catalogue change. |
| Python path/SHA-256 manifest comparison | Exit 0; all 121 protected paths and bytes unchanged, including all 108 reference/v0.3-rc1 files; digest equals before-work digest above. |
| `git diff --exit-code HEAD --` followed by the manifest's protected path list | Exit 0; tracked protected paths also equal starting HEAD. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Final local check: both required locked blobs match exactly, as before work. |
| `git diff --check` | Exit 0; no whitespace errors. |
| Python final-newline/trailing-whitespace checks over all six delivered files and `ast.parse` over the three added Python files | Exit 0; all six files clean and three ASTs parse. |
| `git status --short`; `git rev-parse HEAD origin/main` | Exactly the six delivered paths listed above; HEAD and local origin/main remain the starting SHA. |

The final document/discovery batch passed 8/8 commands. No protected file was
modified, even transiently. `.aiops/**`, `docs/tasks/**`, `reference/v0.3-rc1/**`,
contracts, workflows, status/evidence maps, existing service/fake/normalizer,
fixtures and golden vectors were preserved. No final-merge blob check applies.
