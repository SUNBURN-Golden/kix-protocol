# Commerce request envelope conformance

## Task and base

- Task ID `plan-bootstrap-commerce-envelope-conformance`. The supervisor-supplied
  node specification and design plan are the task input. The node came from
  planner run `1795084226` and has no issue or document under `docs/tasks/`.
- Branch `agent/kix-plan-bootstrap-commerce-envelope-conformance`. The clean
  starting HEAD, local `origin/main` and design base were all
  `f5f89be525ea3e03a80212e26871934abe9536b5`.
- The supervisor's network restriction took precedence over the fetch in
  AGENTS.md §1. Remote freshness is unverified. The builder delivered an
  uncommitted worktree on the same HEAD. The implementation commit, final
  delivery head, A2 non-author review, and exact-head KTX and KIX run IDs and
  results are pending supervisor delivery. Post-merge verification is not
  applicable to this worktree.

## Coverage

The merged Commerce journey supplies all 44 requests in order across 27
published FSM actions. Both suites compare `operationId`, `actor`, `action`
and `body` to a pre-call snapshot, including JSON value types. All five steps
with expected business refusals
go through the same schema checks as the other requests. `replay-consume-B`
carries its original reused FSM idempotency key. The SDK records exactly one
transport call per step. The gate evidence comes from `parse_envelope` under
the offline socket guard. [Journey fixture](../../reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json).

The shared companion defines the synthetic actor, operation ID prefix and four
single faults. Both tests apply each fault to a fresh copy of `payment-A`.
The SDK recorder stays empty and the gate parser raises before returning a
validated tuple.
[Companion fixture](../../reference/booking_resale_admission/fixtures/commerce_journey_envelope_cases_v1.json).

| Fault | SDK code | Gate code | Gate detail |
|---|---|---|---|
| Remove `body.idempotency_key` | `MISSING_REQUIRED` | `SCHEMA_REJECTED` | `body: missing idempotency_key` |
| Change `body.amount` to the string `"12000"` | `WRONG_TYPE` | `SCHEMA_REJECTED` | `body.amount: expected integer` |
| Add `body.unexpected` | `UNKNOWN_FIELD` | `SCHEMA_REJECTED` | `body: unknown fields unexpected` |
| Change the action to the `NOT_BOUND` read `get_booking` | `UNKNOWN_ACTION` | `UNKNOWN_ACTION` | `None` |

| Requirement | Prior coverage | Gap addressed |
|---|---|---|
| Both validators accept and preserve the journey envelopes | Partial. `test_every_step_binds_a_published_action_and_body` checked published actions and body keys. The SDK's `every catalogue command accepts a minimal body and rejects schema violations` test used generated minimal inputs. | The new SDK and gate tests validate the actual fixture bodies and check all four returned or forwarded fields. |
| Exactly one SDK transport call per accepted request | Partial. The SDK's minimal-body test counted calls for generated inputs. | A single recorder checks the delta for each of the 44 requests, including refusal and replay steps. |
| Both validators reject the four shared single faults | Partial. The SDK's minimal-body and envelope rule tests covered general schema errors. The existing Commerce journey test checked read names against the catalogue. | Both layers use the same four Commerce mutations and assert the existing errors, including the gate's detail. |
| Mock business outcomes and pinned identities | Sufficient. Commerce journey conformance and receipt-golden tests cover outcomes and replay. The producer tuple and consumer binding checkers cover pinned identities and status. | Reuse the existing suites and checkers. |

## Changed files

| Path | Change |
|---|---|
| `reference/booking_resale_admission/fixtures/commerce_journey_envelope_cases_v1.json` | Shared request metadata and four negative cases, outside the manifest's bound vectors. |
| `sdk/conformance/conformance.test.mjs` | Positive and negative tests through `createLocalCallClient` and a recording transport. |
| `integration_gate/test_offline_limits.py` | Positive and negative tests through `parse_envelope` with the pinned command map. |
| `docs/README.md` | One link under Consumer surface boundaries. |
| `validation/2026-11-20-plan-bootstrap-commerce-envelope-conformance/README.md` | Coverage, local results and evidence limits. |

## Local evidence

The verification commands ran in the foreground from the worktree root with
Node 24.22.1, npm 11.21.1, Python 3.12.15 via `python3.12`, and Rust 1.98.1.
Cargo commands used `CARGO_NET_OFFLINE=true`.

| Command | Actual result |
|---|---|
| `node --test --test-name-pattern='Commerce journey' sdk/conformance/conformance.test.mjs` | Initial run 1 passed, 1 failed because the SDK test did not remove the key. After the test fix, 2 passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits.CommerceJourneyEnvelopeTests` | 2 passed, including the final run with structural and JSON value comparison. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_journey*.py' -v` | 13 passed. |
| `npm --prefix sdk run conformance` | 10 passed. |
| `npm --prefix sdk run verify-compat` | `ok=true`, `BOOTSTRAP` revision `bootstrap-2`, manifest SHA-256 `eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0`. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 11 passed, including the final run. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 1,052 passed. Child Python processes generated ignored bytecode in the frozen reference tree. The five generated files were removed. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 1,052 passed on the rerun with the workflow's child-process environment setting. |
| `python3.12 -B scripts/check_sdk_client.py` and `--self-test` | 84-command SDK pin and self-test passed. |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | 84-command pin (40 core, 44 FSM) and self-test passed. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | 84-command pin, non-production and non-public flags, and self-test passed. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | Identity passed for 84 commands and 13 reads. Self-test passed. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and `--self-test` | Binding index passed for 84 commands, 13 unbound reads, 44 journey steps and 27 journey actions. All 10 negative controls passed. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Passed with 442 scanned, 407 indexed and 35 allowlisted. Self-test passed. |
| All invocations in the `Stdlib offline document checks` block of `.github/workflows/protocol.yml`, extracted and run with `python3.12 -B` | 69 invocations, 0 failures. Includes the two binding checkers, docs index, CI wiring and test discovery checks. |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce-envelope-calculation.json` | `PASS`, calculation only, zero external calls. |
| `python3.12 -B scripts/verify_canonical.py --report .local/verification/commerce-envelope-canonical.json` | `PASS`, CE1 and Commerce schema 2. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture and dependency gate passed. All 7 architecture tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Passed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Passed with the default exclusions, including the opt-in analytics engine test. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` and `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Dependency tree and source digests generated. The only normal dependency listed for `kix-kernel` is `kix-types`. |
| `git status --short --branch --untracked-files=all` and `git rev-parse HEAD origin/main` | The five changed paths above. HEAD and cached origin/main both match the base. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` for both additions | No whitespace diagnostics. The no-index comparisons returned 1 for added content. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs matched before and after work. |
| `python3.12 -B` byte check using `git ls-tree -rz HEAD` and `git ls-files --others --exclude-standard` | Before and after work, 147 protected files matched their HEAD blob IDs with no untracked additions in the checked paths. |
| `git ls-files --others --ignored --exclude-standard -- reference/v0.3-rc1` | Empty after cache cleanup and the suite rerun. |

| Locked file | Git blob before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The protected byte check covered both locks, `reference/v0.3-rc1/**`, the
journey and its receipt goldens, the producer tuple and consumer binding
index, both OpenAPI pins and the FSM contract, the SDK client, catalogue,
generator, compatibility artifacts and bound vectors, the workflows,
`.aiops/` and `docs/tasks/`.

## Evidence limits

This evidence covers request schemas for `BOOTSTRAP` revision `bootstrap-2`
and its `catalogue-schema-binding only` grant. The new tests end at the SDK
recorder and the Python parser. The existing offline Commerce suite supplies
separate FSM receipt and refusal evidence. Semantic SDK consumption stays
`HOLD_SEMANTIC`, external consumer acceptance stays `UNVERIFIED`, and all 13
reads stay `NOT_BOUND`. SD1 remains `OPEN` and User-owned, and the
`extension_profile` interpretation remains `UNDETERMINED`.

The fixture values are synthetic. Product policy remains `UNDETERMINED`
with Astra and the User. Refund liability, legal and accounting treatment, and
provider facts remain with the User, designated advisers and Toss as applicable.
The evidence gives no authentication, N/N-1 compatibility, funds, provider,
admission, finality, durability, legal or production assurance.

Contract violations and contract-undefined characterizations in the observed
request checks were both zero. The foreground verification covered the
planned local equivalents for the changed paths. Hosted workflow execution,
disposable chain and ZK jobs, and related infrastructure setup are outside
this builder evidence.
