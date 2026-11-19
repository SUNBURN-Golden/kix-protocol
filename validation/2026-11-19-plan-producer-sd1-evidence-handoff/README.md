# Validation — producer SD1 evidence handoff

## Task and checkout

- Node `plan-producer-sd1-evidence-handoff`. The supervisor supplied the node specification and design plan from planner run `1795084226` (`/workspace/kix-run/logs/planner_1795084226`). This node has no issue or task file under `docs/tasks/`.
- Branch `agent/kix-plan-producer-sd1-evidence-handoff`. Starting HEAD and cached `origin/main` both resolved to `7002cf9e99f48af6ea5a12607aa69604b6573a6f`, the supplied planning basis. The supervisor's no-network instruction superseded the session-start fetch.
- The handoff is a worktree patch at that base. The supervisor owns commit and publication. Exact-head KTX and KIX run IDs, statuses and conclusions, and a merge SHA and post-merge checks, remain pending delivery. A2 non-author exact-head review, both required CI workflows and User merge authorization remain delivery gates.

## SD1 evidence chain

The October record captured an AGENTS.md §8 class C stop. The verifier at
that basis checked the OpenAPI references, generator and SDK output before
the profile byte hash, contrary to the specified sequence. [October SD1 stop](../../docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md)
and [manifest contract §4](../../docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md#4-최소-검증기).

JunTae authorized option 1 on November 18 via the supervisor (`[pt224u]`).
The checkout already includes the resulting relocation of the profile
read and hash ahead of both OpenAPI checks. [Owner decision record](../../docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md)
and [verifier profile hash block](../../sdk/compat/verify_compat.mjs#L146-L150).

The two-fault repro corrupts the profile and contract-only OpenAPI digests
in a temporary manifest with a matching sidecar. The wrapper requires
`ok: false`, verifier exit `1` and `profile bytes drift` first. The ordered
conformance test also covers canonical parse gating and the named §4
diagnostics. The evidence map records `C4-CHECK-ORDER` as `COVERED`.
[Two-fault repro](../2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py),
[`manifest verifier reports failures in contract order`](../../sdk/conformance/conformance.test.mjs#L364-L409)
and [SDK compatibility manifest evidence map](../../docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md#2-map).

## Byte identities

Raw file lengths, SHA-256 digests and Git blob IDs were computed before and
after the handoff. The bootstrap-2 manifest digest matches both the lowercase
hex in its sidecar and `manifest_sha256` in the passing verifier verdict.

| path | bytes | sha256 | gitBlob |
|---|---:|---|---|
| `sdk/compat/verify_compat.mjs` | 13120 | `8628518c41b4110f0adf9a5d841240ae06dc6c1fa5d5c4974f00d96a718c5de6` | `4d744a7e622f2678054b9f709a138252635309c6` |
| `sdk/compat/manifests/manifest.bootstrap-2.json` | 1892 | `eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0` | `06199b46de4c7d0c9dadd55f39d469936acb601a` |

The `kix-producer-qualification-tuple/1` record has 18 artifact entries.
The verifier identity is recorded here because the tuple omits the verifier.
The byte comparison covers the entire tuple, the consumer binding index, SDK
pins, manifests, profiles, sidecars, vectors, generated catalogue, both OpenAPI
documents, the FSM command contract, historical stop and ledger documents,
prior §4 validation, `reference/v0.3-rc1/`, `.aiops/`, `docs/tasks/`,
contracts and workflows. [Pinned producer tuple](../../docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json).

| Locked path | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

## Acceptance and existing coverage

| Acceptance | Existing coverage | Handoff evidence |
|---|---|---|
| Current docs reach the November evidence | Partial. The owner record and regression existed, and the SDK and producer handoff still described the October verifier. | Added and resolved relative links from the SDK, producer tuple, consumer boundary map and docs index. |
| Two-fault precedence and ordered §4 diagnostics | Sufficient. The existing two-fault repro and ordered conformance test cover precedence and fail-closed behavior. The companion single-fault suite compares unordered error sets. | Ran both ordered checks and full SDK conformance. |
| Starting artifact pins and binding statuses | Partial. SDK regeneration checks committed output, and the tuple checker and self-test cover the pins, all 13 reads and false promotion. Internally consistent pins can differ from a starting checkout. | Compared raw SHA-256 and Git blob identities against the starting checkout and verified the manifest verdict digest against the sidecar. |
| Docs index and checker entry points | Sufficient. The repository already provides both checker and self-test entry points. | Ran the relevant offline Protocol and KTX workflow checks below. |

The existing tests cover the requested behavior. This handoff adds a
documentation and byte-identity record.

## Changed paths

| Path | Handoff change |
|---|---|
| [`sdk/README.md`](../../sdk/README.md) | Current SD1 evidence and ordered regression link next to the companion single-fault suite. |
| [`docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md`](../../docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md) | October snapshot, November evidence and reason for recording verifier identity here. |
| [`docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md) | Current SDK verifier evidence and formal ledger ownership. |
| [`docs/README.md`](../../docs/README.md) | Validation link under BOOTSTRAP producer qualification. |
| `validation/2026-11-19-plan-producer-sd1-evidence-handoff/README.md` | This validation record. |

## Commands and results

Checks ran in the foreground with Python 3.12.15, Node 24.22.1, npm 11.21.1
and Rust 1.98.1. The ordered checks ran first, against the clean base and again
before the broader checks. Cargo used `CARGO_NET_OFFLINE=true` with a temporary
target directory.

| Command | Observed result |
|---|---|
| `git status --short --branch` and `git rev-parse HEAD refs/remotes/origin/main` | Clean starting worktree on the requested branch. Both refs matched the planning basis. |
| `git hash-object --no-filters runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before and after. Both working-file blobs matched the required values. |
| `python3.12 -B /tmp/kix-sd1-handoff.8Hrt9e/verify_bytes.py before` and the same helper with `after` | Exit 0 on both completed audits. All 182 protected files matched the base Git blobs and the recorded starting sizes and SHA-256 digests. The manifest sidecar agreed. The initial scratch run exited 1 on a schema-key typo, corrected to `record_schema_version` before the baseline snapshot. |
| `python3.12 -B validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py` | Wrapper exit 0, verifier exit 1 with `ok: false`. Profile at index 0, contract-only OpenAPI at index 1. |
| `node --test --test-name-pattern='^manifest verifier reports failures in contract order$' sdk/conformance/conformance.test.mjs` | Exit 0, 1 test passed. |
| `python3.12 -B scripts/check_sdk_client.py` and the same command with `--self-test` | Both exit 0. Temporary regeneration matched the committed SDK pins for 84 commands. Self-test passed. |
| `npm --prefix sdk run conformance` | Exit 0, 8 tests passed. |
| `npm --prefix sdk run verify-compat` | Exit 0. Verdict `ok: true`, `BOOTSTRAP`, `bootstrap-2`, and the `manifest_sha256` listed above. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py` and the same command with `--self-test` | Both exit 0. 51 rows checked, including `C4-CHECK-ORDER`. The self-test passed 71 negative fixtures and the injected positive control. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and the same command with `--self-test` | Both exit 0. 84 commands (40 core, 44 FSM) and 13 reads re-derived. Self-test passed, including the false-promotion controls. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and the same command with `--self-test` | Both exit 0. 13 of 13 reads `NOT_BOUND`. All 10 negative controls passed. |
| `python3.12 -B scripts/check_docs_index.py` and the same command with `--self-test` | Both exit 0. 441 scanned, 406 indexed and 35 allowlisted. Self-test passed. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and each with `--self-test` | All four exit 0. Both OpenAPI pins cover 84 commands. Both self-tests passed. |
| Remaining commands in the [Protocol stdlib document step](../../.github/workflows/protocol.yml#L203-L281), using `python3.12 -B` in place of `python3` and omitting the live loopback probe | All 68 offline invocations in that step exited 0, including the tuple, consumer, docs and SDK evidence-map checks listed above. The loopback self-test used fakes and passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exit 0. Architecture dependency gate and 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0, 139 tests passed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0. Sole normal dependency `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Printed all three KTX source digests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0, 345 tests passed. One opt-in analytics engine test was ignored by the default suite. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `python3.12 -B /tmp/kix-sd1-handoff.8Hrt9e/verify_handoff.py`, `git diff --check`, and `git status --short --branch --untracked-files=all` | All exit 0. The temporary audit compared links with the base and resolved 30 added relative links and 14 anchors, including the verifier and test source excerpts. Exactly the five planned paths differed. No whitespace errors. |

Both workflow classifiers send `sdk/README.md` through full verification.
Local evidence covers the relevant SDK, documentation, OpenAPI and Rust
steps. The active loopback host probe and the hosted bootstrap, local-chain,
ZK and storage jobs were outside this local run. The supervisor's
foreground-only and no-network constraints governed the checks.

## Disposition and limits

The original class C discrepancy is historical. The two-fault result on
this checkout matches §4. The pinned SD1 object retains `OPEN` and
`User`, and JunTae retains formal ledger disposition. The §4 interpretation
of `extension_profile` remains `UNDETERMINED` with the User. This handoff
found no additional contract discrepancy or contract-undefined behavior.

BOOTSTRAP grants `catalogue-schema-binding only`. Semantic consumption
remains `HOLD_SEMANTIC`, all 13 reads remain `NOT_BOUND`, and external
consumer acceptance remains `UNVERIFIED`. The local evidence is limited to
the checked-in verifier, pinned artifact identities and existing offline
checks. Semantic qualification, N/N−1 compatibility, public release,
production operation and independent acceptance are outside this handoff.
