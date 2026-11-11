# Local synthetic payment lookup adapter — 2026-10-30

Node/task: `plan-local-payment-lookup-adapter`. Task input is the supervisor's
node specification and read-only design in the session; no task issue or file
under `docs/tasks/` exists for this node. This is not ASTRA program mode.

Starting branch: `agent/kix-plan-local-payment-lookup-adapter`.
Starting HEAD/base and local `origin/main`: `6dfb03a23773b728ab3ec2e0d70059c9a220ab5b`.
No local base delta. `git fetch origin main` was **not run**: the supervisor
explicitly forbids all network/GitHub actions. Remote freshness is unverified.
Implementation and final committed heads are pending supervisor publication;
this builder does not commit, push, open PRs, post comments or merge.

## Coverage mapping recorded before adding tests

Inspected the existing provider_facts tests and both required workflow definitions.
All paths below are under `reference/provider_facts/` unless qualified.

| Requirement | Existing coverage classification | Gap / planned evidence |
|---|---|---|
| Paid and cancellation normalization with independent expectations | Partially covered: `test_normalization_golden_vectors.py::test_literal_facts_bytes_and_digests`, `test_normalize_verified_only.py::test_cancel_does_not_erase_the_original_payment_item` | No callable service; route unchanged golden literals through service and independently specify full-cancel history. |
| Missing binding / configured scope mismatch makes zero calls | Partially covered: `test_operation_binding.py::test_unknown_operation_lookup_preserves_state`, `::test_operation_scope_isolation` | New service dispatch guards across provider/account/environment and fake configuration. |
| One accepted call, no retry/fallback after timeout/error | Not covered | Observable fake calls and explicit deterministic faults through the service. |
| Timeout/not-found/unsupported/unverified unresolved | Sufficiently covered at helper: `test_normalize_verified_only.py::test_timeout_not_found_and_unsupported_stay_unresolved`, `::test_missing_or_unsupported_payment_and_cancel_statuses_stay_unresolved` | Add service-boundary assertions only, including malformed text and response mismatch. |
| Preserve bindings/captures/reviews | Partially covered: public snapshots in `test_operation_binding.py` | Populate captures/review then snapshot across all service outcomes; inspect code for absence of economic integration. |
| Exact integers/raw timestamps/golden vectors | Sufficiently covered: `test_integer_krw.py`, `test_timestamps.py`, `test_cancel_boundaries.py`, `test_normalization_golden_vectors.py` | Run unchanged suites and route every golden vector through service, including max u128 and offset-less timestamp. |
| Deterministic fake and returned-data isolation | Not covered for lookup | Immutable copied recordings, repeat calls, mutation isolation and full PaymentRef keys. |
| Synthetic labels, owners and evidence links | Partially covered: PROVENANCE and existing maps | Example output assertions; narrow supplemental map updates without owner/count changes. |
| CI discovery/wiring, index/checkers, OpenAPI pins | Existing scripts/workflows | Execute relevant checks and self-tests; protected manifest comparison. |

Before-work locked blobs match AGENTS §4:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.
A path/SHA-256 manifest was recorded before edits for 154 protected files,
including all 108 files under `reference/v0.3-rc1/`, `.aiops/`, `docs/tasks/`,
contracts, workflows, tracked OpenAPI paths, existing fixtures/golden vectors and
both locked files. Manifest SHA-256:
`b3fe7fb7a3bedb1792e042b2ef00ce1c8d4921cff624901c8a6fdd8c92ac8e3c`.

## Delivered implementation and new evidence

`payment_lookup.py::PaymentLookupService.lookup` reads the existing binding,
checks configured synthetic scope against the binding and fake, calls the fake
once, then uses unchanged `normalize_recorded_text` and existing result types.
`SyntheticLookupResult` fixes provenance to `MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY`.
No request can select a URL, credential, account, provider or alternate payment.
The deterministic fake copies a full-PaymentRef -> immutable-text/fault map and
exposes read-only recordings and an immutable call snapshot. Explicit timeout/
error markers require no time threshold, sleeps, real calls, queue or retries.
Missing recordings produce a synthetic not-found document.

New test/evidence gaps closed locally:

- `test_payment_lookup.py::test_missing_binding_makes_zero_calls` and
  `::test_scope_mismatch_makes_zero_calls`: missing-binding precedence plus each
  provider/account/environment dimension for bound/fake configuration guards.
- `::test_accepted_lookup_calls_fake_once_with_complete_bound_ref` and
  `::test_timeout_and_error_do_not_retry_or_fallback`: exact complete-reference
  call counts, alternate recording unused, no normalization after injected fault.
- `::test_unresolved_boundaries_preserve_state_and_make_one_call`: recorded
  timeout/not-found, unsupported method/currency/status, unverified source,
  mismatched response identity, float text, malformed JSON, non-object document,
  missing timestamp and absent recording remain unresolved.
- `::test_all_existing_golden_vectors_through_service`: unchanged literal facts,
  canonical UTF-8 bytes and SHA-256 digests, including u128 max and offset-less
  raw timestamp evidence. Expectations are never generated by normalization.
- `::test_full_cancellation_preserves_capture_and_has_independent_expected_history`:
  separately specified full-cancel facts alongside retained original capture.
  Existing vectors independently specify paid and partial-cancel results.
- Every outcome uses deep-copied public binding/count/capture/review snapshots
  and recording comparisons; fixture dictionaries/golden vectors are checked in
  teardown. `::test_repeat_explicit_lookup_is_fresh_and_cannot_relabel_provenance`
  mutates returned nested details and checks fresh later results.
- Invalid request arguments/selectors fail before fake calls; unrelated programming
  errors propagate. `test_fake_payment_lookup.py` covers copied/immutable
  recordings, full-reference keys, direct fake scope guards, repeatable fault
  markers and a runnable deterministic seven-scenario synthetic-labelled example.

This is source-informed synthetic characterization with independently specified
expected outputs, not clean-room independence or provider conformance.

## Executed commands and results

Python verification used `PYTHONDONTWRITEBYTECODE=1`; the broader CI-equivalent
batch also used `CARGO_NET_OFFLINE=true`. All jobs ran sequentially in the
foreground, with no shell background jobs. Rust/Cargo: 1.98.1, matching the
workflow toolchain. The two workflow files were inspected for relevant steps.
These commands reproduce relevant portions of `protocol.yml` and
`ktx-kernel.yml`, not the complete hosted workflows.

| Command | Actual result |
|---|---|
| `git rev-parse HEAD`; `git rev-parse origin/main` | Both `6dfb03a23773b728ab3ec2e0d70059c9a220ab5b`; local observations only. |
| `git branch --show-current` | `agent/kix-plan-local-payment-lookup-adapter`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both exact locked blobs match (above). |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p 'test_*payment_lookup.py' -v` — first run | 15 tests, 10 teardown failures: the test snapshot accidentally included Python `__builtins__`. Fixed the test to snapshot uppercase fixture constants only; no normalization/fixture change. |
| Same narrow command — rerun | Exit 0; 15 tests passed. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | Exit 0; 51 tests passed, including all existing golden-vector/boundary suites unchanged. |
| `python3 reference/provider_facts/example_payment_lookup.py` | Exit 0; seven deterministic JSON lines, all synthetic-labelled, three histories plus four unresolved scenarios, each one fake call. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; passed. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; passed. |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_status_register.py` | Exit 0; passed. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_docs_index.py` | Exit 0; passed. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; passed. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; passed. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; passed. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; passed. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test passed. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; passed. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test passed. |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0; 9 tests passed. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture/dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0; 18/18 dependencies present, none missing. |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; self-test passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 139 passed, 0 failed, 0 ignored (sum of test-result lines). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 339 passed, 0 failed, 0 ignored (sum of test-result lines). |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; passed with warnings denied. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; passed; check mode only. |
| Python path/SHA-256 manifest comparison and `git diff --exit-code HEAD --` the tracked protected-path list | Exit 0; all 154 paths/bytes unchanged, including all 108 reference/v0.3-rc1 files; manifest digest unchanged. |
| `git diff --check` | Exit 0; no whitespace errors. |

The check batch produced 27 exit-zero command results. Self-tests exercise
intentional negative controls; their diagnostic messages are expected passes,
not implementation failures. No checker, owner guard, OpenAPI pin, workflow,
contract, task document or program configuration was adapted.

## Complete changed-path list

- `reference/provider_facts/payment_lookup.py` — callable service and labelled result.
- `reference/provider_facts/fake_payment_lookup.py` — frozen scope, deterministic fake and faults.
- `reference/provider_facts/example_payment_lookup.py` — runnable seven-scenario example.
- `reference/provider_facts/test_payment_lookup.py` — service gaps listed above.
- `reference/provider_facts/test_fake_payment_lookup.py` — fake/example gaps listed above.
- `reference/provider_facts/README.md` — usage, internal interfaces, diagnostic precedence, owners and limits.
- `reference/provider_facts/provider_facts.py` — scope docstring only; normalization behavior unchanged.
- `docs/README.md` — link to this record.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md` — E01 synthetic callable evidence; retains `partial MOCK`.
- `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md` — dated supplemental fake evidence and retained gaps.
- `docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md` — supplemental fake evidence and PARTIAL normalization citations; provider rows remain untested/open as applicable.
- `validation/2026-10-30-plan-local-payment-lookup-adapter/README.md` — this record.

## Protected paths and delivery gates

The after-work path/byte manifest equals the before-work manifest exactly (same
154 files, same digest recorded above). The full reference/v0.3-rc1 tree, both
locked blobs, `.aiops/**`, `docs/tasks/**`, `docs/contracts/**`, workflows, tracked
OpenAPI paths, synthetic_documents.py and normalization_golden_vectors.py are
unchanged. Tracked protected paths also match starting HEAD. No locked file was
modified, including transiently. Normalizer diff is documentation only.

| Delivery evidence | State |
|---|---|
| Implementation/final committed task head | Not created by builder; uncommitted worktree over starting HEAD above, supervisor owns commit/publication. |
| Independent non-author A2 exact-HEAD review | PENDING; required on supervisor's final committed head. Builder self-check is not independent review. |
| KTX kernel verification exact-head run ID/status/conclusion | NOT_RUN / not observed; no GitHub/network action allowed. Must be completed/success on final head before merge-ready. |
| KIX protocol verification exact-head run ID/status/conclusion | NOT_RUN / not observed; no GitHub/network action allowed. Must be completed/success on final head before merge-ready. |
| Merge commit and post-merge main CI | N/A; no merge performed or authorized here. |
| Builder delivery | Locally complete for supervisor handoff; **not merge-ready**. |

## Deviations, discrepancies and non-claims

- Fetch omitted under the supervisor's explicit no-network instruction; local
  origin/main freshness is unverified. No rebase, branch change or base change.
- No issue/task file exists for this loop-proposed node; the supplied specification
  is the immutable task input. No task document or `.aiops/` file was created/edited.
- Scope is defined beside the fake and re-exported from payment_lookup, avoiding
  a circular import while keeping the planned public interface. The existing
  binding store in provider_facts.py is reused without behavior change.
- Added the workflow's offline-cache check/self-test as useful local CI evidence;
  Cargo ran offline with cached dependencies. No Rust code was changed.
- No class C contract violation found. Class B local synthetic characterizations:
  missing binding precedes scope checking; invalid operation errors propagate;
  bound/fake scope mismatches precede calls; explicit timeout/error and parser
  failures map to unresolved diagnostics; absent recordings are not-found fixtures.
  Direct fake scope refusal and configuration syntax validation are local guards,
  not authentication or new protocol errors/product policy. No provider semantics
  are invented. The initial snapshot test failure and correction are recorded above.

UNDETERMINED values retain their existing owners, including TM04, authentication
I04/TM05, scope I02/I03, status/termination I05, retention I08, independent cut I12
and Astra's event-source/alias/domain/schema/waiting-policy choices. S2-LOOKUP and
S4-LOOKUP-BINDING remain provider-evidence gaps; all map counts, OPEN rows and
owners are unchanged. Cancellation results cannot redefine retained capture
identity, clear UNKNOWN, release rights or establish refund completion.

Code inspection establishes there is no import/call to a kernel or economic
engine in the lookup/fake modules; state tests preserve populated public capture,
review and binding records. No actual economic engine was run by lookup tests.
No authentication, durable binding/custody, finality, payment completion,
exactly-once, legal compliance, provider conformance or production readiness is
claimed. No real provider, bank, KYC, Sui, public endpoint, SDK/HTTP, persistence,
polling, retry, new command, policy value, EventItemId, ProviderFactKey or alias
implementation was exercised/created. Hosted Move/ZK and complete protocol CI
were not run locally. Remaining follow-up is independent exact-head review and
both required exact-head workflows under the supervisor; real-provider scope
and every owner decision remain separate work.
