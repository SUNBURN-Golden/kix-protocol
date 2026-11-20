# Canonical producer manifest byte boundaries

Task `plan-producer-canonical-byte-edges` uses the supervisor-supplied node specification and design as its task document. The planner input is run `1795159796`. The node has no issue or `docs/tasks/` document. Branch `agent/kix-plan-producer-canonical-byte-edges` started at `6e30f53d65443aadb85d02d4e30d0c48e17c7878`, matching the supervisor-provided cached `origin/main` and the design base. The supervisor prohibited network access, so the cached ref supplied the local observation in place of `git fetch origin main`.

## Coverage

The four new tests use independently specified byte literals in `sdk/conformance/conformance.test.mjs`. The [SDK evidence map](../../docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md) cites all four under [manifest-v1 §1](../../docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md#1-정규-인코딩).

| Evidence row | Prior coverage | Local evidence |
| --- | --- | --- |
| `C1-OBJECT-FORM` | Partial. `canonical encoding vectors` exercised ASCII key order, including nested objects. | `manifest-v1 bytes use code-point key order` checks the exact UTF-8 for U+E000 before U+10000, opposite their UTF-16 order, and asserts both decoded key/value pairs. Reversing the keys produces `unsorted-keys`. |
| `C1-STRING-ESCAPE` | Partial. The `unicode-string` vector exercised unescaped non-ASCII. | `manifest-v1 bytes escape controls quotes and backslashes` checks the complete JSON string bytes for U+0001, a quote and a backslash, then parses those bytes back to the original string. |
| `C1-INT-RANGE-BOUNDS` | Partial. The `integer-range` vector exercised positive overflow well beyond the limit. | `manifest-v1 bytes cover safe integer endpoints` parses and reserializes −9007199254740991 and 9007199254740991 exactly. Both adjacent out-of-range literals produce `integer-range`. |
| `C1-DEPTH-LIMIT` | Uncovered. The map had no boundary test. | `manifest-v1 bytes exercise the parser depth limit` parses 16 array/object pairs and follows them to the scalar. One extra array produces `depth`. |
| Manifest and profile digests | Sufficient. `vendored producer manifests return one verdict without changing files` checks both active manifests with the verifier and compares the manifest digests with their sidecars. `check_sdk_client.py::source_pin_errors` checks the historical `bootstrap-1` pins. | Reused the existing tests and verifier. Checked all three manifest and profile digest pairs directly. |

## Changed paths

| Path | Change |
| --- | --- |
| `sdk/conformance/conformance.test.mjs` | Add the four parser and serializer regressions. |
| `docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md` | Cite the tests, update the four rows and counts, and document the depth diagnostic. |
| `scripts/check_sdk_compat_manifest_evidence_map.py` | Move six self-test mutations to rows with the required coverage statuses. Preserve their expected diagnostics and the injected positive control. |
| `docs/README.md` | Index this validation record. |
| `validation/2026-11-20-plan-producer-canonical-byte-edges/README.md` | Record builder evidence. |

## Local verification

The focused Node tests ran before the broader checks. The SDK test path selects full verification in both workflow classifiers. Local equivalents used Node 24.22.1, npm 11.21.1, Python 3.12.15 and Rust 1.98.1. Cargo used `CARGO_NET_OFFLINE=true` and a disposable `CARGO_TARGET_DIR` under `/tmp`.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse HEAD refs/remotes/origin/main`, `git branch --show-current` | Exit 0. Clean starting worktree on the expected branch. Both refs matched the recorded base. |
| `node --test --test-name-pattern='^manifest-v1 bytes ' sdk/conformance/conformance.test.mjs` | Exit 0. All four focused tests passed. |
| `npm --prefix sdk run conformance` | Exit 0. All 17 tests passed. |
| `npm --prefix sdk run verify-compat` | Exit 0. `ok=true`, `BOOTSTRAP`, `bootstrap-2`, with the digest below. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. `ok=true`, `SEMANTIC_CONFORMANCE`, `commerce-fixture-8ba7f6c-1`, with the digest below. |
| `python3.12 -B -` (inline digest assertions) | Exit 0. For each checked-in manifest, SHA-256 matched the adjacent sidecar, including its LF terminator. The corresponding profile file's SHA-256 matched the manifest's `profile_sha256`. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py`, plain and with `--self-test` | Both exit 0. 51 rows, 24 covered, 26 partial, 1 uncovered. All 71 negative fixtures and the injected positive control passed. |
| `python3.12 -B scripts/check_<name>.py`, plain and with `--self-test`, for `sdk_client`, `producer_qualification_tuple`, `docs_index`, `ci_checker_wiring`, `ci_test_discovery`, `evidence_map_rollup`, and `class_b_index` | All exit 0. The SDK pins matched and the docs index accepted the new record. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exit 0. Architecture gate passed and all 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 139 passed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0. `kix-types` was the sole normal dependency. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Printed the three KTX source digests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 345 passed and 1 ignored by default. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` and `git rev-parse HEAD:reference/v0.3-rc1` | Exit 0 before and after. The IDs appear below. |
| `git diff --exit-code HEAD -- .aiops .github docs/tasks docs/contracts docs/decisions reference runtime sdk toolchains.json ':(exclude)sdk/conformance/conformance.test.mjs'` and `git ls-files --others -- .aiops .github docs/tasks docs/contracts docs/decisions reference runtime sdk` | Both exit 0 with empty output. |
| `git diff --check HEAD`, `git status --short --branch --untracked-files=all`, `git rev-parse HEAD refs/remotes/origin/main` | All exit 0. The five listed paths are the complete worktree changes. Both refs still match the recorded base. |
| `git diff --no-index --check -- /dev/null validation/2026-11-20-plan-producer-canonical-byte-edges/README.md` | Exit 1 for the new file, with no whitespace diagnostics. |

| Revision | Manifest SHA-256 | Profile SHA-256 |
| --- | --- | --- |
| `bootstrap-1` | `1cce4ee5a9aa64ef40825c0e6dedf920050e594cf20ea0aaf087ecbde46f0cca` | `4c92cf6d905f83fb3f5cd52e166dbadf057451ae46441fce1f91baaaa4367d34` |
| `bootstrap-2` | `eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0` | `c356b923997cefc132e63e73a179d5922dd7cb2124b9e9b399c662cd49803b73` |
| `commerce-fixture-8ba7f6c-1` | `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f` | `240bc0b2f200ca3256b8fdb6a3eab0c2fa1f4e1b6e51cc9a4e663e155750ef0d` |

| Lock | Git ID before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` blob | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` blob | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1` base tree | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

## Disposition

The tests found zero contract violations. Manifest-v1 specifies 32 nested containers as a verifier implementation limit and leaves the rejection reason unspecified. The `depth` reason observed at 33 is a class B characterization under AGENTS.md §8. The existing §4 `extension_profile` interpretation remains `UNDETERMINED` with the User.

The local evidence covers the listed SDK predicates, fixed producer artifacts, document checks and Rust gates. External consumer acceptance, N/N−1, production or semantic qualification, hosted dependency setup, and the unrelated reference, integration, storage, Move, local-chain and ZK suites were outside this verification. Bootstrap-2 catalogue-schema binding and the Commerce synthetic fixture grant retain their existing scope.

The supervisor owns publication. Implementation, final task and merge commit SHAs are unavailable for this worktree handoff. The KTX and KIX exact-head run IDs, statuses and conclusions, the A2 non-author review, and any post-merge evidence are pending supervisor delivery. The no-network baseline check was the only departure from AGENTS.md's startup procedure. The additional local checks covered CI wiring, CI test discovery, the evidence-map rollup and the class B index.
