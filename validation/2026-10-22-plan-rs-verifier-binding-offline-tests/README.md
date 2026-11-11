# Offline artifact and verifier pinning evidence

## Identity and scope

Node: `plan-rs-verifier-binding-offline-tests`; task input is the supervisor-supplied
node specification and design plan in this session. No issue or task document
under `docs/tasks/` exists for this node. This is not ASTRA program mode.
Branch: `agent/kix-plan-rs-verifier-binding-offline-tests`.
Starting HEAD and cached `origin/main`: `1c129f1a5fd73636c30c90a33ecfb9e4adf21217`.
The stated design base matches both. Remote freshness is unverified: the explicit
supervisor prohibition on network/GitHub actions supersedes the session-start
fetch. No commit, publication or merge is authorized for this builder.

Scope: one new offline test module, explicit package/CI discovery, the docs index
bullet and this record. The implementation (`private-scale.mjs`), contracts,
dependencies, `.aiops/program.json`, the locked kernel files and
`reference/v0.3-rc1/**` are unchanged.

## Prior coverage (recorded before adding cases)

Paths in this table are relative to `reference/rights_scale/client/`.

| Requirement | Classification | Existing evidence and gap |
|---|---|---|
| Manifest metadata matrix (format, profile numbers, K, phase 1, contributions, constraints, artifact and circuit digest fields) | Sufficiently covered | `zk-policy-v2.test.mjs` characterizes `requirePhase2ManifestV2` and `requirePhase2Key`. Not repeated; the new fixture is valid once and mutations target the bindings only. |
| Compressed verifier-key encoding | Sufficiently covered | `zk-helpers.test.mjs` pins `vkBytes` against literal bytes. The new fixture reuses its fabricated coordinate shapes and literal word expectations. |
| `artifacts(expectedHash)` pin against the loaded manifest bytes | Not covered offline | `admission-packet.test.mjs` and `mint-note.test.mjs` stub the policy guards and `vkBytes`; `zk-regression.mjs` and the localnet journeys need generated artifacts. |
| Artifact bytes against manifest digests, path containment | Not covered offline | Same reason; the sibling suites use a path allowlist and a sentinel manifest. |
| Encoded-verifier bytes against `vkey.json` | Not covered offline | The sibling suites replace `vkBytes` by a recording sentinel. |
| `checkVerifier` object pin (package, type, immutability) | Not covered | Only the localnet journey calls it with a real object (`private-localnet.mjs:66-69`). |
| `checkVerifier` manifest hash and independent mint/spend key bytes | Partially covered | The localnet journey and the RS-2 record show one `VERIFIER_KEY_PIN_MISMATCH` with an alternate Verifier on a disposable chain. No offline case separates the manifest hash, mint bytes and spend bytes, or checks ordering and absence of later reads. |
| Explicit discovery | Partially covered | `test:offline` and `protocol.yml` each list the same seven suites; the new suite is added to both without changing existing gates. |

## New case mapping

All cases drive the unchanged `artifacts` and `checkVerifier`. Every rejection
case uses `assert.rejects` (so no value is returned) and an exact event trace
(so nothing runs after the failing guard). Cases run sequentially and nested
cases are awaited. `getObject` arguments are asserted as
`{objectId: <requested ID>, include: {content: true}}` wherever the RPC is reached.

| Case in `verifier-binding.test.mjs` | Gap addressed |
|---|---|
| `fixture sanity` | Independent `node:crypto` digest agrees with shared `sha256`; ten manifest paths in literal order. |
| `artifacts_control` | Coherent synthetic control returns the exact four fields, with and without a pin; literal expected `vk.bin` bytes; full read trace. |
| `manifest_pin_mismatch` | Zero digest and digest of other bytes each reject with `CIRCUIT_MANIFEST_PIN_MISMATCH`; only `manifest.json` is read. |
| `artifact_byte_hash_mismatch` | A flipped artifact byte (trace stops at that file) and a changed manifest digest with a re-derived pin; both `CIRCUIT_ARTIFACT_HASH_MISMATCH:<file>`. |
| `artifact_path_escape` | Parent traversal, sibling-prefix directory, interior traversal and absolute entries each reject with `ARTIFACT_PATH` after the ten real files and without reading the escaped entry. |
| `encoded_verifier_byte_mismatch` | One flipped mint `vk.bin` byte, and a policy-valid spend `vkey.json` whose encoding differs from its `vk.bin` (digests re-derived, so only the encoding guard fires); `VERIFIER_ENCODING_MISMATCH` at the offending read. |
| `check_verifier_control` | Returns the artifacts result; requested object ID asserted; trace `getObject`, `parse`, then the full artifact trace. |
| `check_verifier_object_pin_rejections` | Other package ID, other type name, other module, address-owned, shared and object-owned all `VERIFIER_OBJECT_PIN_MISMATCH` with trace exactly `getObject` (no parse, no file read). Missing-owner characterization below. |
| `check_verifier_key_pin_rejections` | Differing manifest hash, one mint byte, one spend byte, truncated mint key, empty spend key and swapped mint/spend keys each `VERIFIER_KEY_PIN_MISMATCH` after the full artifact trace, each changed in isolation. |
| `check_verifier_supplied_hash_mismatch` | A supplied hash that differs from the loaded manifest bytes is refused by `artifacts` after `getObject` and `parse`. |
| `check_verifier_failure_propagation` | A throwing `parse` stub, an artifact guard failure with an also-wrong parsed key, and a failing `getObject` each propagate the original error with the exact earlier trace. |

Mutation sanity check (outside delivery paths, `/tmp/vb-mut/`, not part of the
suite): eleven single-guard mutations of a copy of `private-scale.mjs` (pin check
removed, path guard removed or weakened to no trailing separator, file hash check
removed, encoding comparison removed, package/type check removed, immutability
check removed, manifest-hash, mint-key and spend-key comparisons removed, wrong
object ID requested) each made the new suite fail (exit 1). The real
implementation was never edited.

## Mocked boundaries

| Boundary | Treatment | Consequence |
|---|---|---|
| `node:fs/promises` `readFile` | In-memory map rooted at the real `artifactRoot`; unexpected paths fail the test. Real `readJSON` reads through the same mock (imported after the mock, so no override of `readJSON` was needed). | No disk, real artifact or generated file is read. |
| `./types.mjs` `Verifier.parse` | Explicit stub returning a caller-supplied object; asserts it receives the fetched `content`. | **BCS layout and currentness of the Verifier decoder are not tested.** That remains with the queued extended-decoder node. |
| `rpc.getObject` | Fake object recording its arguments; returns a synthetic `{type, owner, content}`. | No RPC, endpoint or chain is contacted. |
| Not mocked | `sha256`, `vkBytes`, `readJSON`, `requirePhase2ManifestV2`, `requirePhase2Key`, `profile-constants.mjs`. | Hash, policy and encoding behavior is the repository's own code. The policy's metadata matrix is not repeated. |

Synthetic keys use the fabricated public coordinates of `zk-helpers.test.mjs`
(gamma differs from delta so the real key policy passes). They are encoder
fixtures, not curve points or usable verification keys. Expected `vk.bin` bytes
are literal hex words and never come from `vkBytes`. The manifest carries the
test-only `ROOT_HISTORY_K` fixture value; the operational K is not chosen.
`phase1.source` is `SYNTHETIC_METADATA_ONLY`.

## Commands and results

All final required local checks pass. Commands run from the repository root.
PATH for the checks prefers `/workspace/toolchain/node-v24.19.0-linux-x64/bin`
and `/workspace/venvs/film312/bin`. Versions: Node 24.19.0, npm 11.21.0,
Python 3.12.15, rustc 1.98.1 (`48a229cea`, 2026-09-01), Cargo 1.98.1
(`797e8a9bc`, 2026-08-05). Initial inspection found system Node 20.19.2; no
suite ran under it. Python checks inherit `PYTHONDONTWRITEBYTECODE=1`; Cargo
checks inherit `CARGO_NET_OFFLINE=true`. All subprocesses ran in the foreground;
no bootstrap, installation or download ran.

This worktree initially lacked `node_modules`. The ignored installation was
copied from `/workspace/kix-run/wt/plan-rs-mint-wrapper-offline-tests/reference/rights_scale/client/node_modules`
(its `package-lock.json` is byte-identical to this worktree's). On this toolchain
`node --test` reports named cases for these files, so counts below are cases.

| Command | Exit | Actual result |
|---|---|---|
| `git rev-parse HEAD origin/main` (no fetch) | 0 | Both `1c129f1a5fd73636c30c90a33ecfb9e4adf21217`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before edits) | 0 | `69564b16...` and `b607996c...`; both match the required blobs. |
| `node --experimental-test-module-mocks --test reference/rights_scale/client/verifier-binding.test.mjs` | 0 | 37 passed; 0 failed, cancelled, skipped, todo. |
| `node --experimental-test-module-mocks reference/rights_scale/client/verifier-binding.test.mjs` | 0 | 37 named cases (11 top-level, 26 nested); 0 failed; expected experimental/deprecation warnings left visible. |
| Eleven single-guard mutants of a `/tmp` copy of `private-scale.mjs` | 1 each | Each mutant fails the suite (fail counts 2 to 22); see mutation sanity check. |
| `npm --prefix reference/rights_scale/client run test:offline` | 0 | All eight suites; 569 passed; 0 failed, cancelled, skipped, todo. |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 267 passed; 0 failed/skipped/todo. |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs` | 0 | 166 passed; 0 failed/skipped/todo. |
| `node --test reference/rights_scale/client/ptau-header.test.mjs` | 0 | 34 passed; 0 failed/skipped/todo. |
| `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | 16 passed; 0 failed/skipped/todo. |
| `node --test reference/rights_scale/client/spend-witness.test.mjs` | 0 | 23 passed; 0 failed/skipped/todo. |
| `node --experimental-test-module-mocks --test reference/rights_scale/client/admission-packet.test.mjs` | 0 | 13 passed; 0 failed/skipped/todo. |
| `node --experimental-test-module-mocks --test reference/rights_scale/client/mint-note.test.mjs` | 0 | 13 passed; 0 failed/skipped/todo. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 129 tests; OK. |
| `node reference/rights_scale/client/gen-move-vectors.mjs --check` | 0 | Move known-answer constants match circomlibjs: 23 vectors |
| `python3 scripts/check_status_register.py` (+ `--self-test`) | 0 / 0 | capability register ok: paths=300 ev_ids=15 original32=32; self-test pass. |
| `python3 scripts/check_rs_profile_traceability.py` (+ `--self-test`) | 0 / 0 | blueprint=47 profile=47 expected=47; self-test pass. |
| `python3 scripts/check_read_model_source_map.py` (+ `--self-test`) | 0 / 0 | queries=13 anchors=128 catalogues=2 citations=145; self-test pass. |
| `python3 scripts/check_docs_index.py` (+ `--self-test`) | 1 then 0 / 0 | First run before this record existed: exit 1, broken index link to this record (expected). Final run with the record and index bullet: docs index ok: scanned=199 indexed=164 allowlisted=35; self-test pass. |
| `python3 scripts/check_i12_proof_ids.py` (+ `--self-test`) | 0 / 0 | proof_headings=4 proof_keys=10 pack_keys=14 expected=14; self-test pass. |
| `python3 scripts/check_delegation_layer_matrix.py` (+ `--self-test`) | 0 / 0 | rows=36 expected=36 citations=79; self-test pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` (+ `--self-test`) | 0 / 0 | rows=23 expected=23 citations=168; self-test pass. |
| `python3 scripts/check_rs_im_evidence_map.py` (+ `--self-test`) | 0 / 0 | rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 (unchanged); self-test pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` (+ `--self-test`) | 0 / 0 | rows=49 expected=49 citations=58; self-test pass. |
| `python3 scripts/check_contract_error_codes.py` (+ `--self-test`) | 0 / 0 | rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0; self-test pass. |
| `python3 scripts/check_adapter_identity_map.py` (+ `--self-test`) | 0 / 0 | rows=17 expected=17 citations=56; self-test pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` (+ `--self-test`) | 0 / 0 | rows=10 expected=10 citations=77; self-test pass. |
| `python3 scripts/check_readiness_evidence_map.py` (+ `--self-test`) | 0 / 0 | rows=36 expected=36 citations=177; self-test pass. |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0 | 7 tests; OK. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 78 passed across test binaries; 0 failed, 0 ignored. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 257 passed; 0 failed, 0 ignored. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Passed with `-D warnings`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Formatting check passed. |

The final locked-blob, protected-path diff and whitespace checks are recorded in the next section.

## Preservation

Both locked kernel blobs matched before edits and again after all checks:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`src/lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
`git diff HEAD -- reference/v0.3-rc1 .aiops docs/tasks runtime` is empty. The
package diff only appends `verifier-binding.test.mjs` to `test:offline`; removing
the two-line CI step reproduces the original workflow byte-for-byte, and its
position after `scripts/bootstrap.sh` is required because `private-scale.mjs`
imports `circomlibjs` and `snarkjs`. All existing workflow gates, checks, pins,
permissions, timeouts and conditions are preserved. The Git index is untouched.

Complete changed-path list:

- `reference/rights_scale/client/verifier-binding.test.mjs`
- `reference/rights_scale/client/package.json`
- `.github/workflows/protocol.yml`
- `docs/README.md`
- `validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md`

Implementation/final builder Git HEAD remains
`1c129f1a5fd73636c30c90a33ecfb9e4adf21217`; changes are uncommitted as requested.
There is no final committed delivery SHA or final-merge blob check yet.

## Discrepancies and non-claims

No explicit contract violation was found. Observed characterizations
(contract-undefined, class B; nothing redefined):

- `artifacts()` without a pin accepts any internally consistent manifest; the
  pin guard is conditional on a truthy `expectedHash`. The control case records
  that the unpinned call returns the same result on the coherent fixture.
- `checkVerifier` fetches and parses the object before `artifacts(manifestHash)`
  runs, so a supplied hash that differs from the loaded manifest bytes is refused
  by `artifacts` (`CIRCUIT_MANIFEST_PIN_MISMATCH`) before the object's own hash is
  compared. The case records that order only.
- An object without an `owner` rejects with a `TypeError` before the pin
  diagnostic (the case asserts only a `TypeError` and no parse or read).

Deviations from the design plan: the plan's `artifact_path_escape` listed two
entries; the suite also covers interior traversal and an absolute entry. It adds
swapped mint/spend keys, a failing `getObject` and an artifact-guard-before-key-pin
ordering case to the failure cases. Fetch was omitted under the explicit
no-network instruction; cached main freshness remains unverified. The
`readJSON`-only fallback described in the plan was not needed. Node 24 prints
deprecation warnings for `namedExports`/`defaultExport` mock options, the same
form the sibling suites use; they are not suppressed.

These are synthetic, source-informed integration tests within EV-RS for IM-17
and IM-27. They establish neither BCS layout or currentness of the Verifier
decoder (stubbed), nor curve validity or key usability, real artifact or ceremony
integrity, an operational Verifier ID pin, actual-chain verification, durability
or operational qualification. No evidence-map status, grade or owner changes:
IM-17 stays `PARTIAL` and IM-27 stays `COVERED_LOCALNET` as recorded. All
owner-controlled policy values remain UNDETERMINED with their existing owners,
in particular operational K, depth, shard counts and the Verifier ID pin
(`RS-2 ; DECISION_REQUIRED · Astra` as recorded in the evidence map and
profile). No funds, providers, secrets, keys, generated proving artifacts or
network are used. Bootstrap, Move/localnet journeys, `setup:zk`/`test:zk`, circuit
generation and storage probes were excluded from local verification.

## Delivery gates

Implementation/final committed head: not created by this builder; supervisor owns
Git publication. Exact-head KTX and KIX CI run IDs/status/conclusions: unobserved,
outstanding. A2 non-author exact-head review: outstanding. Merge SHA and post-merge
CI: not applicable (not merged). Local checks do not establish hosted CI success
or merge readiness.
