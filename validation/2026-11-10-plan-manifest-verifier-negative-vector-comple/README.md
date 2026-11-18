# plan-manifest-verifier-negative-vector-comple — builder validation

## Task and basis

Node: `plan-manifest-verifier-negative-vector-comple`. The task input is the
supervisor-supplied node specification and read-only design plan in the builder
prompt. No issue was created and no corresponding task document exists under
`docs/tasks/`; this is not ASTRA program mode. Audit floor A2; no Astra gate;
no merge authority.

Observed `origin/main` before work, base and starting branch HEAD:
`034cd7659d0de116ab23c874ef05f5bcfecc2689` (merge #434). No base delta: the
branch HEAD, merge base and `origin/main` were the same SHA.

Branch: `agent/kix-plan-manifest-verifier-negative-vector-comple`.

Implementation/final delivery head: unavailable; the supervisor owns commits.
Merge commit and post-merge checks: not applicable; no merge performed.

Locked kernel blobs before and after work:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` for
`runtime/crates/kix-kernel/src/lib.rs` and
`b607996c83a119c349f1cc90469ac1ba82764e20` for
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs`. Both match the
required blobs. `reference/v0.3-rc1/**` was not touched.

## Why a companion vector document

`manifest.bootstrap-2.json` binds `mixed-input.vectors.json` by
`vectors[].sha256`, and `scripts/check_sdk_client.py` regenerates and
byte-compares the manifest, profile and sidecar. Editing the bound mixed-input
file in place would change the positive manifest bytes, contradicting the node
acceptance that the positive manifest, profile and vector bytes stay unchanged.
The extension is therefore
`sdk/conformance/vectors/manifest-verifier-negative.vectors.json`, a companion
matrix that the manifest does not list. The bound `mixed-input.vectors.json`
bytes are unchanged.

## What was added

- `sdk/conformance/vectors/manifest-verifier-negative.vectors.json` — canonical
  (`kix-canonical-json/1`) case matrix: 56 cases, 40 on the manifest surface,
  12 on the `bootstrap-2` profile surface and 4 on the sidecar surface. Each
  case records the surface, one mutation operation, one fault description and
  the exact expected error set.
- `sdk/conformance/conformance.test.mjs` — one new test that copies the
  verifier and its fixtures byte-identically into a temporary root, applies one
  mutation per case, runs the unmodified verifier logic, and requires a
  non-zero exit with the exact expected error set. Profile cases re-seal
  `manifest.profile_sha256` to the mutated profile bytes and rewrite the
  sidecar, so the intended profile predicate is the only fault. The test also
  re-runs the committed manifest and asserts `ok=true`,
  `profile_kind=BOOTSTRAP`, `profile_revision=bootstrap-2`, and snapshots
  sha256 for the positive artifacts before and after.
- `sdk/README.md` — documents the companion suite, the single-fault rule, the
  unordered assertion and the non-claims.
- `docs/README.md` — one index link to this record.
- `validation/2026-11-10-plan-manifest-verifier-negative-vector-comple/README.md`
  — this record.

No change to `sdk/compat/verify_compat.mjs`, `sdk/generate/*`, the generated
catalogue, the positive manifest/profile/sidecar, either bound vector, the
SD1 record, `.aiops/`, `docs/tasks/`, CI definitions, contracts or the locked
kernel blobs. No dependency was added.

## Existing coverage mapped before editing

| Requirement | Classification | Existing coverage / new gap addressed |
|---|---|---|
| Canonical strict-JSON rules | Sufficient | `sdk/conformance/vectors/canonical-encoding.vectors.json` plus the existing canonical-encoding test. Not duplicated; the new matrix adds manifest-level `manifest is not canonical`, `manifest truncated` and `manifest duplicate-key` branches. |
| Ten mixed manifest mutations | Partially covered | `sdk/conformance/vectors/mixed-input.vectors.json` asserts only non-zero exit and a non-empty error list. The new matrix keeps those bytes unchanged and adds exact expected sets plus the remaining verifier branches. |
| Manifest/top-level field set, schema version, self-reference | Not covered | New cases `manifest-field-set-drift`, `manifest-schema-version-drift`, `manifest-self-reference-final-commit`. |
| Producer repository, source commit/tree, field set, contract binding | Not covered | New producer cases plus `producer-protocol-domain-drift` and `producer-contract-schema-version-drift`. |
| Contract path/bytes and field sets | Partially covered | Mixed-input has contract-only and gate sha cases without exact sets. New path-unsafe, field-set and exact bytes cases. |
| Generator path/bytes/toolchain | Not covered | New `generator-path-drift`, `generator-bytes-drift`, `generator-toolchain-drift`, `generator-field-set-drift`. |
| `sdk_output` path/bytes | Partially covered | Mixed-input has one output sha case. New path and field-set cases. |
| `source_references` / extension profile | Not covered | New fixture and extension field-set/path/bytes cases. |
| Vectors shape/path/digest | Not covered | New shape, field-set, path and digest cases. |
| Profile identity/field-set/grants/bytes | Partially covered | Mixed-input has one profile digest case. New identity, field-set, self-reference, grants and vector-parity cases; digest drift is also reported by `manifest-profile-digest-format-drift`. |
| Catalogue and schema digests | Not covered | New catalogue field-set, OpenAPI binding, command-set, digest-map and digest-value cases. |
| Sidecar form/digest | Not covered | New form, digest, repeated-field and missing-sidecar cases. |
| Positive artifact byte freeze | Sufficient | `scripts/check_sdk_client.py` (plain and `--self-test`) regenerates and compares; the new test adds an in-process before/after sha256 snapshot. |

## Case-to-branch mapping

| Node branch group | New case names |
|---|---|
| Manifest schema / field-set / self-reference | `manifest-non-canonical-escape`, `manifest-truncated`, `manifest-duplicate-key`, `manifest-field-set-drift`, `manifest-self-reference-final-commit`, `manifest-schema-version-drift`, `manifest-profile-kind-unknown`, `manifest-profile-kind-mismatch`, `manifest-profile-revision-format-drift`, `manifest-profile-revision-mismatch`, `manifest-profile-digest-format-drift` |
| Producer repository / source commit / source tree | `producer-field-set-drift`, `producer-repository-drift`, `producer-source-commit-drift`, `producer-source-tree-drift`, `producer-protocol-domain-drift`, `producer-contract-schema-version-drift` |
| Contract path / bytes | `contract-field-set-drift`, `contract-only-field-set-drift`, `integration-gate-field-set-drift`, `contract-only-path-unsafe`, `integration-gate-path-unsafe`, `contract-only-bytes-drift`, `integration-gate-bytes-drift` |
| Generator path / bytes / toolchain | `generator-field-set-drift`, `generator-path-drift`, `generator-bytes-drift`, `generator-toolchain-drift` |
| `sdk_output` path / bytes | `sdk-output-field-set-drift`, `sdk-output-path-drift`, `sdk-output-bytes-drift` |
| `source_references` / extension profile | `source-references-field-set-drift`, `source-references-fixture-drift`, `extension-profile-field-set-drift`, `extension-profile-path-drift`, `extension-profile-bytes-drift` |
| Vectors shape / path / digest | `vectors-shape-not-array`, `vector-field-set-drift`, `vector-path-unsafe`, `vector-digest-drift` |
| Profile identity / field-set / grants / bytes | `profile-field-set-drift`, `profile-self-reference-commit`, `profile-identity-kind`, `profile-identity-revision`, `profile-schema-version-drift`, `profile-grants-drift`, `profile-vectors-differ`; bytes drift in `manifest-profile-digest-format-drift` |
| Catalogue / schema digest | `catalogue-field-set-drift`, `catalogue-openapi-binding-drift`, `command-set-digest-drift`, `schema-digest-map-drift`, `schema-digest-value-drift` |
| Sidecar form / digest | `sidecar-form-drift`, `sidecar-digest-drift`, `sidecar-repeats-manifest-field`, `sidecar-missing` |

Every case applies exactly one mutation. Several checks may fail from that one
fault; the test sorts the actual and expected error lists before comparing, so
it asserts membership and multiplicity, never order or precedence.

## Commands actually run and actual results

All commands were run in this worktree, in the foreground. Node v24.22.1,
Python 3.13.5.

| Command | Actual result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD`; `git merge-base origin/main HEAD` | fetch succeeded; all three SHAs `034cd7659d0de116ab23c874ef05f5bcfecc2689`. |
| `git status --porcelain` (initial) | Clean. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both runs: `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`; match the required blobs. |
| `npm --prefix sdk run conformance` (baseline, before edits) | exit 0; 6 tests passed, 0 failed. |
| `npm --prefix sdk run conformance` (with the new matrix) | exit 0; 7 tests passed, 0 failed, including `manifest-v1 verifier negative vectors reject exactly one fault each` (56 cases). |
| `npm --prefix sdk run verify-compat` | exit 0; `{"ok":true,"manifest_sha256":"eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0","profile_kind":"BOOTSTRAP","profile_revision":"bootstrap-2"}`. |
| `python3 scripts/check_sdk_client.py` | exit 0; `sdk client pin ok: commands=84 node=24.22.1 sourceSha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`. |
| `python3 scripts/check_sdk_client.py --self-test` | exit 0; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | exit 0; `docs index ok: scanned=399 indexed=364 allowlisted=35`. |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; seven negative controls then `self-test: pass`. |
| `python3 scripts/check_class_b_index.py` and `--self-test` | exit 0; `class B index ok: rows=218 sources=73 symbols=47`; `self-test: pass (20 negative controls)`. |
| `python3 scripts/check_readiness_evidence_map.py` | exit 0; `rows=36 expected=36 citations=186 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`. |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0; `rows=30 expected=30 citations=202`. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0; `rows=23 expected=23 citations=174`. |
| `python3 scripts/check_v5_transition_evidence_map.py` | exit 0; `rows=10 expected=10 citations=77`. |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | exit 0; `ci test discovery ok: reference_suites=8 node_tests=8 modules=4 excluded=3`; `self-test: pass (18 negative controls)`. |
| `python3 scripts/check_status_register.py` and `--self-test` | exit 0; `capability register ok: paths=575 ev_ids=15 original32=32`; `self-test: pass`. |
| `git diff --check` | exit 0; no whitespace errors. |
| `git diff --name-only` and protected-path check | Only the SDK harness, the new companion vector, the two READMEs and this record changed; `.aiops`, `docs/tasks`, the locked blobs, `reference/v0.3-rc1`, OpenAPI pins, generated catalogue, positive manifest/profile/sidecar and bound vectors have no diff. |

Not run: Rust `cargo test`/`clippy`/`fmt` and the Python runtime checks. No
Rust, runtime, OpenAPI or generated path changed; the touched paths are the SDK
conformance harness, one new vector document and documentation, so the SDK and
document checks above are the closest CI equivalents. No packages were fetched
and no network action beyond the initial `git fetch origin main` was made; no
commit, push, PR, issue or comment was made.

## Contract-undefined characterizations observed (not asserted or changed)

- `manifest.source_references.extension_profile` set to `false` is accepted by
  the verifier for `bootstrap-2` because all extension checks are skipped. This
  case is deliberately not a negative vector.
- Contract and vector `path` predicates reject only absolute paths and `..`;
  they do not compare against an expected path. The matrix targets the
  predicates that exist.
- Producer `source_commit` and `source_tree` are checked only for 40-hex
  format; no git ancestry or byte-at-commit check exists (contract §4 states
  this explicitly).
- The `running node does not match toolchains.json` branch is an environment
  check, not expressible as a manifest/profile/sidecar content fault, and is
  not part of this matrix.
- Contract-only live-flag/servers, contract-only JSON parse and profile parse
  error branches require mutating OpenAPI or profile bytes outside the node's
  enumerated mutation surfaces; they are not covered here. Strict-JSON parse
  reasons remain covered by `canonical-encoding.vectors.json`.

## Non-claims

- SD1 (verifier check order) is untouched and unresolved: no case asserts
  which error wins. `sdk/compat/verify_compat.mjs` is unchanged.
- No semantic conformance, N/N-1, production, audit, approval or merge claim.
  Scope remains BOOTSTRAP catalogue-schema binding only; semantic consumption
  stays HOLD.
- The exact-set assertions describe verifier behavior on this basis, not a
  contract amendment. No new protocol command, policy value, funds, secrets,
  production runtime or network path is introduced.
