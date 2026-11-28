# Commerce admission lost-reply vectors

The task input for `plan-commerce-admission-lost-reply` is the supervisor's
node specification and design plan from planner run `1795159796`. The task
has no issue or document under `docs/tasks/`. The starting HEAD on
`agent/kix-plan-commerce-admission-lost-reply` and cached `origin/main` both
resolved to `8341dd74002a056aa104d4acb2f54e4d9cffd954`, the supplied base.

## Coverage

| Requirement | Existing coverage | Paired replay evidence |
|---|---|---|
| Pinned setup and envelope, stable identities | Sufficient for the delivered sequence and tuple. `CommerceFixtureTupleTests.test_vectors` covers the source vector, duplicate replay, and fresh double-consume refusal. The SDK case “Commerce journey envelopes reach the transport once per step” covers verbatim forwarding. | Both tests verify the corpus digest, replay the same nine successful setup calls on fresh hosts, and compare the entire call trace to the single original envelope. |
| Identical missing receipt and terminal `UNKNOWN` | Partial. The SDK case “envelope, identifier, and transport rules stay local to one call” covers one transport invocation on a synchronous throw and a rejected promise. The two producer outcomes with one shared caller observation were uncovered. | Both tests compare the complete observation to the same `expected_caller` record, including identities, null receipt, `UNKNOWN`, one attempt, and zero follow-up calls. |
| Authorization persists before dispatch | Partial. `AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version` covers the authorized views. Loss before dispatch was uncovered. | `test_loss_before_dispatch` observes zero dispatches, version 1 on both views, and unchanged canonical state and accepted journals across all five machines. |
| Right consumed after dispatch and reply lost | Partial. The exact-tuple replay covers the returned success receipt and journal deltas. Loss of that receipt was uncovered. | `test_loss_after_dispatch` observes one dispatch and compares the discarded receipt to the existing golden at `#/steps/29/receipt`. Admission and reservation show `CONSUMED` at version 2. Each appends one `consume` entry with `key-consume-B`. All journal prefixes are intact and the other three machines are unchanged. |

[Exact-tuple replay](../../reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py) ·
[Admission FSM tests](../../reference/booking_resale_admission/test_admission_fsm.py) ·
[SDK conformance](../../sdk/conformance/conformance.test.mjs) ·
[New fixture](../../reference/booking_resale_admission/fixtures/commerce_admission_lost_reply_v1.json) ·
[New replay](../../reference/booking_resale_admission/test_commerce_admission_lost_reply.py)

## Local verification

Commands ran from the repository root with Python 3.12.15, Node 24.22.1,
and Cargo 1.98.1. `bra` is `reference/booking_resale_admission`. Python
validation used `PYTHONDONTWRITEBYTECODE=1` or `-B`. SDK runs used
`npm_config_offline=true`. Rust used `CARGO_NET_OFFLINE=true` and
`CARGO_TARGET_DIR=/tmp/kix-commerce-admission-lost-reply-target`.

| Command | Result |
|---|---|
| `git status --short --branch` and `git rev-parse HEAD refs/remotes/origin/main` | Exit 0. The clean starting branch and cached main both pointed to the supplied base. |
| `sha256sum sdk/conformance/vectors/commerce-fixture-tuple.vectors.json` | Exit 0. Matched the fixture pin `c9fbeee6a04da371dd054a325c9435a401b9694a1619ac9939de38f257495e22`. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce_admission_lost_reply.py' -v` | Exit 0 on the initial and final focused runs. Both cases passed on each run. |
| `python3.12 -m unittest discover -s "$bra" -p 'test_commerce_fixture_tuple_conformance.py' -v` | Exit 0. Four tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_admission_lost_reply.py` | Exit 0. Both tests passed using the documented replay command. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,073 tests passed using the protocol workflow's booking suite entry point. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The scoped Commerce manifest verified. |
| `npm --prefix sdk run conformance` | Exit 0. All 17 tests passed. |
| `npm --prefix sdk run verify-compat` | Exit 0. The `bootstrap-2` manifest verified. |
| `python3.12 -B -` running each Python invocation in the workflow's Stdlib offline document checks block, except the standalone loopback probe | All 68 invocations exited 0. The block includes `scripts/check_docs_index.py`, `scripts/check_ci_test_discovery.py`, the Commerce consumer binding and producer qualification checks, and their self-tests. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and `python3.12 -B scripts/check_sdk_client.py`, each also run with `--self-test` | All six invocations exited 0. The checks verified 84 catalogue commands and their pins. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0. Eleven tests passed. |
| `python3.12 scripts/verify_runtime_architecture.py` and `python3.12 scripts/test_runtime_architecture.py` | Both exit 0. Architecture gate and seven tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. All 139 kernel tests passed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0. The sole normal dependency is `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Emitted all three KTX source digests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 345 tests passed. The pre-existing analytics test requiring owner-provisioned engines was ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0. Both locked blob IDs below matched before and after. |
| `python3.12 -B -` comparing each file's raw-byte Git blob ID with `git ls-tree -r -z` for the frozen reference and checking the file set | Exit 0 before and after. All 108 frozen reference files matched the base byte-for-byte. |
| `git diff --exit-code "$base"` on protected paths and `git ls-files --others --exclude-standard` for those trees | Exit 0, with no changes or additions in the protected paths. |
| `git diff --check` and `git diff --no-index --check /dev/null "$path"` for each new file | No whitespace diagnostics on tracked or new files. |
| `git status --short --branch --untracked-files=all` | Exit 0. Exactly the five paths listed below. |

[Protocol workflow](../../.github/workflows/protocol.yml) ·
[Kernel workflow](../../.github/workflows/ktx-kernel.yml)

## Preservation and changed paths

| Locked file | Git blob before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_admission_lost_reply_v1.json`
- `reference/booking_resale_admission/test_commerce_admission_lost_reply.py`
- `validation/2026-11-20-plan-commerce-admission-lost-reply/README.md`

## Scope and delivery

The fixture evidence matches the admission contract §11 and the scope map's
handling of unresolved `UNKNOWN`. No contract violation or undefined
characterization surfaced. Test-harness views and receipt comparison describe
synthetic behavior in one process. Durability, production admission, chain
finality, actual providers, and legal effects are outside the demonstrated
scope. The recovery lookup is `NOT_BOUND`.
The pinned semantic grant applies to its listed outcomes. External acceptance
is `UNVERIFIED`. Product TTLs, fees, compensation, and provider or legal terms
are `UNDETERMINED` with their existing owners.
[Admission contract](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#11-검표-자격-수락-상태-기계) ·
[Qualification boundary](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification)

The supervisor's offline instruction superseded the routine fetch. Remote
freshness is unverified. The documentation index link is required by the
local equivalent of CI's document index check. The verification ran the
booking suite and selected offline CI equivalents. The standalone loopback
probe, separate HTTP gate job, unrelated reference suites, hosted bootstrap,
storage probes, and local-chain, Move, and ZK jobs are outside this run.

The worktree patch awaits the supervisor's commit, so implementation and
final task SHAs are pending. A2 non-author review and exact-head KTX kernel
and KIX protocol CI are pending, with run IDs, statuses, and conclusions
unavailable. Merge SHA and post-merge CI are inapplicable to this delivery.
