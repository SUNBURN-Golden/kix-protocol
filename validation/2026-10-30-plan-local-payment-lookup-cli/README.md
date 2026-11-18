# Offline synthetic payment lookup CLI — 2026-10-30

Node/task: `plan-local-payment-lookup-cli`, predecessor
`plan-local-payment-scope-router`, planner run `1793356463`.
Immutable input is the supervisor-supplied node specification and read-only design
in this session. There is no task issue or document under `docs/tasks/`; this is
not ASTRA program mode. E01/B04 capability grades and all owner values are unchanged.

Branch: `agent/kix-plan-local-payment-lookup-cli`. Starting HEAD/base and locally
observed `origin/main`: `bad76d5837bf2746a36bf2183ae88c66bfc88f61`.
No local base delta. `git fetch origin main` was NOT_RUN under the supervisor's
explicit no-network rule; remote freshness is unverified. Implementation and final
committed heads belong to the supervisor; the builder leaves uncommitted work.

## Existing coverage mapped before adding tests

Paths below are relative to `reference/provider_facts/`.

| Acceptance | Existing classification and exact evidence | CLI gap addressed |
|---|---|---|
| Caller-provided local fixture; strict configuration before lookup | Not covered; examples hard-code setup | `test_payment_lookup_cli.py::test_new_fixture_complete_identities_route_in_each_dimension`, `::test_invalid_entire_configuration_precedes_all_lookup_and_binding`, `::test_duplicate_json_keys_and_invalid_json_are_configuration_errors`, `::test_usage_operation_and_file_errors` |
| Payment and partial/full cancellation | Sufficient helper coverage: `test_payment_lookup.py::test_full_cancellation_preserves_capture_and_has_independent_expected_history`, `test_normalize_verified_only.py::test_cancel_does_not_erase_the_original_payment_item` | Partially covered in wrapper; new subprocess golden and full-cancellation cases preserve payment-plus-cancel history |
| Complete references, integer amounts, timestamps, normalized facts and hashes | Sufficient normalization coverage: `test_normalization_golden_vectors.py::test_literal_facts_bytes_and_digests`, `::test_json_whitespace_and_key_order_invariance` | `::test_all_literal_golden_vectors_through_subprocess` reuses every unchanged literal fact/byte/digest vector, including u128 maximum and offset-less createdAt |
| Timeout, error, not-found, missing binding/route; original bound scope only | Sufficient router coverage: `test_payment_lookup_router.py::test_unresolved_scope_never_falls_back`, `::test_missing_binding_and_route_make_zero_calls`, `::test_two_scopes_dispatch_only_to_bound_fake` | Partially covered at new boundary; subprocess unresolved and missing-binding/route cases assert complete call references, zero/one selected calls and zero alternate calls |
| Exact recorded text; malformed response stays unresolved | Partial coverage: `test_fake_payment_lookup.py::test_recordings_are_copied_read_only_and_calls_are_snapshots`, `test_payment_lookup.py::test_unresolved_boundaries_preserve_state_and_make_one_call` | New loader/subprocess text cases preserve whitespace/Unicode and reject float/exponent only during lookup; unverified source label is unchanged |
| Bindings, captures and reviews unchanged | Sufficient router evidence: `test_payment_lookup_router.py::snapshot`, `::test_complete_identity_and_outputs_equal_single_scope_service` | Wrapper gap: `::test_lookup_once_preserves_nonempty_history_and_calls_router_once` snapshots populated captures/reviews, bindings/count and recordings; every subprocess checks fixture bytes unchanged |
| Existing examples and CI test discovery | Sufficient existing examples; new test file not previously present | New shipped-fixture subprocess plus suite/examples and textual discovery/wiring checks below |

New tests are builder-authored, source-informed boundary characterizations, not
clean-room independence or a provider conformance test. Existing helper tests and
golden expectations were inspected and preserved rather than duplicated.

## Implementation

`payment_lookup_cli.py` validates the entire internal fixture before populating a
fresh binding store or constructing fakes. It rejects duplicate keys/declarations,
invalid/unknown/missing fields and types, mismatched scopes and invalid fault
alternatives, including unused trailing routes. Opaque recorded text is unchanged.
One validated OperationRef goes to `PaymentLookupRouter.lookup` once. JSON uses the
existing normalized facts, receipt and item hashes, complete references, existing
unresolved reasons, fixed synthetic provenance and actual scope-sorted fake-call
snapshots. Usage/configuration/file errors exit 2 with empty stdout; histories and
unresolved results exit 0. Unexpected programming errors propagate.

## Commands actually run

All commands run from the repository root. Python verification uses
`PYTHONDONTWRITEBYTECODE=1`. No long job was launched in the background.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Clean start; expected branch; HEAD and local origin/main match base above. |
| `python3 --version`; `rustc --version`; `cargo --version` | Python 3.13.5; rustc/cargo 1.98.1. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p 'test_payment_lookup_cli.py' -v` | Exit 0, 11 tests passed on all three runs, including final unsorted-route/snapshot test strengthening. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | Exit 0, 73 tests passed on both initial and final full-suite runs. |
| `python3 reference/provider_facts/example_payment_lookup.py` | Exit 0; 7 valid JSON lines. |
| `python3 reference/provider_facts/example_payment_lookup_router.py` | Exit 0; 7 valid JSON lines. |
| `python3 reference/provider_facts/payment_lookup_cli.py --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json --operation-ref '{"provider":"toss-synthetic","account":"mid_synthetic_001","operation":"op_synthetic_0001"}'` | Exit 0; one valid JSON history with existing paid fact/hash and exactly one bound fake call. |
| `python3 scripts/check_adapter_identity_map.py` and `--self-test` | Both exit 0. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` and `--self-test` | Both exit 0; 41 map rows; self-test 3 positive/77 negative controls. |
| `python3 scripts/check_status_register.py` and `--self-test` | Both exit 0. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Both exit 0; 321 scanned, 286 indexed, 35 allowlisted. |
| `python3 scripts/check_evidence_map_rollup.py` and `--self-test` | Both exit 0. |
| `python3 scripts/check_class_b_index.py` and `--self-test` | Both exit 0; existing citations unchanged. |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | Both exit 0; no protocol error catalogue change. |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; new test module reached by existing provider_facts discovery. |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Both exit 0; unchanged pins. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0. |
| `python3 scripts/check_cargo_offline_cache.py` and `--self-test` | Both exit 0; all 18 expected cache entries present. |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0; 9 tests passed. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 139 passed across result groups, 0 failed/ignored. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 339 passed across result groups, 0 failed/ignored; includes kernel tests above, not additive independent evidence. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; dependency evidence equivalent to kernel workflow. |

The example/CLI/checker/offline-limit batch passed all 28 commands. The subsequent
architecture/Rust batch passed all 7 commands. No failing test/check required a
production-code fix. Initial inspection attempted a nonexistent
`test_provider_facts.py` (read-only `sed`, exit 2); actual coverage was then mapped
from the existing individual test modules using `rg`.

## Changed paths

- `reference/provider_facts/payment_lookup_cli.py` — loader, single lookup and JSON CLI.
- `reference/provider_facts/test_payment_lookup_cli.py` — loader/invocation/subprocess gaps.
- `reference/provider_facts/fixtures/payment_lookup.synthetic.json` — explicit runnable synthetic fixture.
- `reference/provider_facts/README.md` — usage, fixture/output structures, diagnostics and limits.
- `docs/README.md` — link to this validation record.
- `validation/2026-10-30-plan-local-payment-lookup-cli/README.md` — this evidence.

## Protection evidence

Before work, `git hash-object` returned the required locked blobs:

| Locked path | Required and observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Before editing, a Python SHA-256 path/byte manifest covered all 119 files under
`reference/v0.3-rc1/**`, `.aiops/**` and `docs/tasks/**`, including untracked files.
Its sorted JSON digest was
`0a4d7a0f6a37f7c40679121fd28cec68935fa428a5f0ede3f387c13d61afe3d6`.
After implementation and verification, all 119 path/byte entries and that digest
matched exactly. No protected file was
modified, including transiently. Existing normalizer, service, fake, router,
synthetic document module and normalization golden vectors are unchanged.

## Deviations, discrepancies and limits

Fetch omitted because the supervisor prohibits network actions. No task document
exists; supplied node/design is the immutable task input. No implementation scope
deviation. Added adjacent workflow OpenAPI/offline-limit/cache checks and kernel
dependency evidence to the planned verification. No issue, comment, marker,
commit, push, PR, branch/tag change or merge.

No class C contract violation found. Class B characterizations are the internal
fixture validation/diagnostic precedence, strict duplicate rejection, CLI exit and
JSON representation rules; these do not define protocol commands or product policy.
Existing unresolved semantics are retained, and no contract was amended.

Provider authentication and merchant scope remain **UNDETERMINED — Toss/User**;
event identity, aliases and operational domain/schema choices remain
**UNDETERMINED — Astra**. No credentials, SDK/OpenAPI change, economic application,
event-ID derivation, persistence, retries, polling, network access, real PG/bank/KYC,
Sui testnet/mainnet, funds, public endpoint, new coin/TIX, storage engine or runtime
activation. No UNKNOWN release, authentication, durable custody, distributed
fencing, finality, payment completion, exactly-once, legal compliance or production
readiness claim. Local CI equivalents do not substitute for hosted Move/ZK/full
protocol verification. No resource/policy STOP condition was encountered.

| Delivery evidence | State |
|---|---|
| Implementation/final committed task head | Pending supervisor; worktree patch over starting HEAD. |
| Non-author A2 exact-head review | PENDING on final supervisor head; builder evidence is not independent review. |
| KTX kernel verification exact-head run ID/status/conclusion | NOT_RUN / not observed; both required workflows must be completed/success on the final head before merge-ready. |
| KIX protocol verification exact-head run ID/status/conclusion | NOT_RUN / not observed; no GitHub/network action authorized. |
| Merge SHA / final merge blobs / post-merge main CI | N/A; no merge performed or authorized. |
| Builder handoff | READY for supervisor delivery; local implementation/validation complete, no merge-ready claim. |

Remaining follow-up: supervisor final commit/publication, non-author A2 review,
normal exact-head KTX/KIX workflows, and authorized merge/post-merge evidence.
Provider/owner inputs remain separate work.

## Final local checks

| Command | Actual result |
|---|---|
| Python path/SHA-256 manifest comparison against the pre-edit snapshot | Exit 0; all 119 protected files/path entries identical; digest above unchanged. |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 .aiops docs/tasks runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0; tracked protected content equals starting HEAD. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (invoked per path by Python) | Both required locked blobs match before and after, exactly as listed above. |
| Python newline/trailing-whitespace checks over the six delivered files; `ast.parse` over the two added Python modules | Exit 0; six files clean, both ASTs parse. |
| `git diff --check` | Exit 0. |
| `git rev-parse HEAD origin/main`; `git status --short` | HEAD/local origin/main unchanged at base; exactly the six delivered paths above. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Final evidence-document recheck: both exit 0. |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | Final discovery recheck: both exit 0. |
