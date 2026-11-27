# Offline producer manifest verdicts

Task `plan-offline-manifest-verdicts` uses the supervisor-supplied node specification and design as its task document. There is no issue or `docs/tasks/` document for this node. The local task branch `agent/kix-plan-offline-manifest-verdicts` started at `4472b0fb64d377d97fd2993673a4485459986606`, matching cached `origin/main` from the supervisor's worktree. The supervisor's no-network rule precluded `git fetch origin main` and remote verification.

## Coverage

| Requirement | Prior coverage | Builder evidence |
| --- | --- | --- |
| `C4-JSON-ONE-LINE` | Partial. `mixed-input vectors and the committed manifest` and `Commerce semantic manifest binds the exact fixture scope and vector bytes` in the SDK suite parse verdicts from stdout. | Compare complete success and refusal objects after requiring exactly one nonempty JSON line ending in LF, empty stderr and normal exit. |
| `C4-READ-ONLY-NO-ANCESTRY` | Partial. Verifier source states the boundary. `manifest-v1 verifier negative vectors reject exactly one fault each` snapshots selected checkout artifacts. | Run against two disposable writable file sets and compare the full directory and file inventory, entry types and file bytes before and after each of four invocations. |
| `C4-CHECK-ORDER` | Sufficient. `manifest verifier reports failures in contract order` covers the canonical parse gate and ordered §4 diagnostics. | Run the existing test and retain its map citation. |

The new regression, `vendored producer manifests return one verdict without changing files`, copies each manifest, adjacent sidecar, profile, all directly referenced files and the verifier's launch dependencies to a temporary root outside the checkout. It checks each pristine inventory against the source bytes. The child starts from the copied root with the absolute Node executable, an environment containing only `PATH` pointing to an empty directory, and Node permissions for read and write access inside the copy. It has no child-process permission. The copy contains no Git metadata and the child cannot read the original checkout or launch Git.

| Revision | Pristine verdict | Verdict after deleting one bound file |
| --- | --- | --- |
| `bootstrap-2` | Exit 0, `ok: true`, `BOOTSTRAP`, digest `eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0`. | Exit 1, `ok: false`, single diagnostic `mixed-input unreadable: <copy>/sdk/conformance/vectors/mixed-input.vectors.json`. |
| `commerce-fixture-8ba7f6c-1` | Exit 0, `ok: true`, `SEMANTIC_CONFORMANCE`, digest `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`. | Exit 1, `ok: false`, single diagnostic `commerce-fixture-request-to-receipt unreadable: <copy>/sdk/conformance/vectors/commerce-fixture-tuple.vectors.json`. |

The test compares each pristine digest with its checked-in sidecar. `<copy>` stands for the absolute temporary root asserted by the test. Each refusal baseline differs from its pristine inventory by just the deleted vector. The four invocations preserve the inventory and bytes from their respective baselines. The comparisons measure persistent file changes.

## Changed paths

| Path | Change |
| --- | --- |
| `sdk/conformance/conformance.test.mjs` | Add the vendored verifier regression and reuse the existing copy and launch helpers. |
| `docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md` | Cite the regression for the two §4 predicates and update the counts. |
| `docs/README.md` | Index the new validation record. |
| `validation/2026-11-20-plan-offline-manifest-verdicts/README.md` | Record builder evidence. |

## Local verification

Node 24.22.1, Python 3.12.15 and Rust 1.98.1. Cargo ran with `CARGO_NET_OFFLINE=true` and one disposable `CARGO_TARGET_DIR` under `/tmp`. The two focused Node tests ran before the broader checks. Both workflow classifiers route the SDK test path to full verification.

| Command | Result |
| --- | --- |
| `git status --short --branch`, `git rev-parse --verify HEAD`, `git rev-parse --verify refs/remotes/origin/main`, `git symbolic-ref --short HEAD` | Clean starting worktree on the expected branch. Both refs resolved to the recorded base. |
| `node --test --test-name-pattern='vendored producer manifests\|manifest verifier reports failures in contract order' sdk/conformance/conformance.test.mjs` | Exit 0. Both tests passed. |
| `npm --prefix sdk run conformance` | Exit 0. All 13 tests passed. |
| `npm --prefix sdk run verify-compat` | Exit 0. One `BOOTSTRAP` verdict with the `bootstrap-2` digest above. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py` and the same command with `--self-test` | Both exit 0. `rows=51 COVERED=20 PARTIAL=29 NOT_COVERED=2`. All 71 negative fixtures and the injected positive control passed. |
| `python3.12 -B scripts/check_<name>.py`, plain and with `--self-test`, for `sdk_client`, `docs_index`, `producer_qualification_tuple`, `ci_checker_wiring`, `ci_test_discovery`, `openapi_contract`, and `integration_gate_openapi` | All exit 0. The docs index found the new validation record. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exit 0. Architecture gate passed and 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 139 passed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 345 passed and 1 ignored by default. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0. `kix-types` was the sole normal dependency. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Printed all three KTX source digests. |
| `sha256sum sdk/compat/manifests/manifest.bootstrap-2.json sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json` | Exit 0. Both hashes matched the checked-in sidecars. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` and `git rev-parse HEAD:reference/v0.3-rc1` | Exit 0 before and after. See the IDs below. |
| `git diff --exit-code 4472b0fb64d377d97fd2993673a4485459986606 --` for the protected paths, with `':(exclude)sdk/conformance/conformance.test.mjs'`, and `git ls-files --others -- .aiops .github docs/tasks docs/contracts docs/decisions reference runtime sdk integration_gate` | Both exit 0 with no differences or extra files in the checked directories. The diff covered `.aiops/`, `.github/`, task and contract documents, producer and Commerce records and validation, `reference/`, `runtime/`, `sdk/`, `integration_gate/` and `toolchains.json`. |
| `git diff --check`, `git status --short --branch --untracked-files=all`, `git rev-parse --verify HEAD`, `git rev-parse --verify refs/remotes/origin/main` | All exit 0. The four paths above were the only worktree changes. Both refs still equal the starting base. |
| `git diff --no-index --check -- /dev/null validation/2026-11-20-plan-offline-manifest-verdicts/README.md` | Exit 1 for the new file, with no whitespace diagnostics. |

| Lock | Git ID before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` blob | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` blob | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1` base tree | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

## Scope and disposition

Bootstrap-2 grants catalogue-schema binding. The Commerce manifest carries the existing grant for the listed synthetic fixture steps across 28 actions. This evidence covers verifier behavior for these two fixed file sets. N/N−1 compatibility, external consumer acceptance, additional qualification and production behavior are outside scope.

The original SD1 check-order discrepancy is historical. JunTae retains formal ledger disposition and the §4 `extension_profile` interpretation remains `UNDETERMINED`. This run found no new contract violations or contract-undefined characterizations. See the [SD1 handoff](../2026-11-19-plan-producer-sd1-evidence-handoff/README.md).

The SDK, document and Rust checks are the local CI equivalents for the touched paths. Hosted dependency setup, full reference and integration suites, storage, Move, local-chain and ZK jobs were outside these checks. The supervisor owns publication and the A2 review and exact-head CI gates. This worktree delivery has no implementation commit, final task commit, merge commit, or hosted KTX and KIX CI run IDs, statuses or conclusions.
