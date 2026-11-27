# Offline mint-note wrapper evidence

## Identity and scope

Node: `plan-rs-mint-wrapper-offline-tests`; task input is the supervisor-supplied
node specification and design plan in this session. No issue or task document
under `docs/tasks/` exists for this node. This is not ASTRA program mode.
Branch: `agent/kix-plan-rs-mint-wrapper-offline-tests`.
Starting HEAD and cached `origin/main`: `9eb6b5f932cae5f4f1b431ef79c9f15874db1c36`.
The stated design base matches both. Remote freshness is unverified: the explicit
supervisor prohibition on network/GitHub actions supersedes the session-start
fetch. No commit, publication or merge is authorized for this builder.

## Prior coverage (recorded before adding cases)

Paths in this table are relative to `reference/rights_scale/client/`.

| Requirement | Classification | Existing evidence and gap |
|---|---|---|
| Public byte encoding | Sufficiently covered | `zk-helpers.test.mjs` tests literal proof/key encodings, field endpoints and metadata guards. Reuse the fabricated coordinates, without duplicating its matrix. |
| Manifest/key metadata guards | Sufficiently covered | `zk-policy-v2.test.mjs` covers manifest fields, artifact hashes, contribution records and mint/spend public counts. Leave that matrix unchanged. |
| Commitment order, inverse and decimal mint witness | Partially covered | `spend-witness.test.mjs::commitment_binding` checks spend commitment binding; `zk-regression.mjs` invokes mint using generated artifacts. Neither provides a focused deterministic offline mint-construction assertion. IM-14 records the commitment-layout gap. |
| Mint artifact paths and public order | Partially covered | `admission-packet.test.mjs::packet_contains_only_public_fields` checks the spend wrapper; `zk-regression.mjs` checks contributed mint public-input mutations cryptographically at its own run. Mint-specific offline path selection and witness-to-wrapper binding remain untested. |
| Pre-insertion holder-note fields, no roots/paths/index | Not covered | No focused offline mint shape assertion. `private-localnet.mjs` adds the insertion index only after `NoteAdded`, so mint must not invent one. |
| Mutated mint signals before verification | Partially covered | `admission-packet.test.mjs::public_signal_layout_rejections` covers the admission analogue; mint boundary missing (mint-specific IM-27 portion). |
| Verifier rejection and prover exceptions | Partially covered | `admission-packet.test.mjs::local_verification_failure` and `prover_failure_propagates` cover admission; mint boundary missing. |
| Explicit discovery | Partially covered | Package `test:offline` explicitly lists six existing suites; protocol CI explicitly invokes admission. Add mint to both without changing existing gates. |

## New case mapping

All cases exercise the actual `mintNote → prove → artifacts` implementation.

| Case in `mint-note.test.mjs` | Gap addressed |
|---|---|
| `mint_witness_binding` | Complete witness equality against independently assembled H(17,700,4,77,1), exact six keys, canonical decimal strings, extended-Euclid inverse and multiplicative inverse relation. |
| `mint_artifact_binding` | Literal mint WASM/zkey/vkey paths, ordered four public signals, mint verification key, both key-policy counts (mint 4, spend 6), artifact checks before proving and verification before encoding. |
| `holder_note_shape` | Exact holder-note/result fields, literal 128 proof bytes, no roots/paths/inverse/insertion index. |
| `mint_public_signal_layout_rejections` | Seven awaited mutations: distinct-position swap, missing/extra signal, each of four changed values; exact layout diagnostic and zero verifier/encoder calls. |
| `mint_local_verification_failure` | False verification rejects with the exact diagnostic; no encoding or returned note. |
| `mint_prover_failure_propagates` | Original error identity propagates; no verification/encoding or returned note. |

Every invocation snapshots the caller ticket and checks preservation on success
and rejection. Cases run sequentially, reset mock state, await nested cases and
restore module mocks afterward. Rejection assertions require rejected promises;
no note is returned on these failures.

## Fixtures and mocked boundaries

The public synthetic scalars are secret 17, slot 700, generation 4, domain 77.
Before wrapper invocation, `circomlibjs` directly supplies the expected Poseidon
commitment; test-local extended Euclid supplies the inverse. Expectations never
come from captured prover inputs, wrapper output or `MINT_PUBLIC`. This is
structural evidence sharing Poseidon, not a clean-room cryptographic oracle.

`randomBytes(32)` returns exactly the 32-byte big-endian representation of 17;
unexpected sizes and extra draws fail. Other crypto exports are preserved.
Node 24's CJS mock bridge requires a copied default crypto export because its
original `constants` property is non-configurable; the filesystem default is
copied as well. Dependency mocks are registered before dynamically importing the
unchanged wrapper. The wrapper itself is neither mocked nor copied.

Artifact reads use an in-memory path allowlist rooted at the test file's
`../zk/artifacts`; unexpected reads fail without fallback. Manifest file digests
use real `sha256`. JSON keys, `vkBytes` and policy guards are recording sentinels,
so existing real metadata/encoder coverage remains necessary. Prover responses
are fabricated; the verifier records the mint key, signal array and proof
identity. Real `FR`, `sha256` and `proofBytes` are retained.

Proof coordinates are the public fabricated encoder fixture from
`zk-helpers.test.mjs`: `pi_a=[513,2,1]`,
`pi_b=[[1027,1541],[3,4],[1,0]]`, `pi_c=[2055,5,1]`.
Expected encoding is four literal padded little-endian words starting `0102`,
`0304`, `0506`, `0708`, independently stated without calling `proofBytes`.
No circuit or proof validity is implied.

## Commands and results

All final required local checks pass. Commands run from the repository root.
PATH for final checks prefers `/workspace/toolchain/node-v24.19.0-linux-x64/bin`
and `/workspace/venvs/film312/bin`. Versions: Node 24.19.0, npm 11.21.0,
Python 3.12.15, rustc 1.98.1 (`48a229cea`, 2026-09-01), Cargo 1.98.1
(`797e8a9bc`, 2026-08-05). Initial inspection found system Node 20.19.2 and
Python 3.13.5; no suite ran under Node 20.
Python checks inherit `PYTHONDONTWRITEBYTECODE=1`; Cargo checks inherit
`CARGO_NET_OFFLINE=true`. All subprocesses were awaited; no shell background
job, bootstrap, installation or download ran.

This worktree initially lacked `node_modules`. The cached installation at
`/workspace/kix-run/wt/plan-rs-offline-test-entrypoint/reference/rights_scale/client/node_modules`
was copied into the ignored local directory. The cache's lockfile matched
byte-for-byte; its non-script manifest fields matched the HEAD manifest; all
147 installed package versions and version/resolved/integrity metadata matched
the unchanged lockfile, with identical package sets. Logs and runner/audit
scratch files are in `/tmp/mint-wrapper-verification/` and
`/tmp/mint-wrapper-preservation.py`, outside delivery paths.

Node's `--test` reports file-level summaries on this toolchain. The additional
direct invocation reports 13 named cases (six top-level, seven nested).
All final Node summaries have zero failures, cancellations, skips and TODOs.
Direct execution emits the expected experimental module-mocking and mock-option
deprecation warnings; these are not suppressed. Existing metadata/encoding,
PTAU, witness, spend and admission suites run through the complete package
command without duplicating their matrices.

| Command | Exit | Actual result |
|---|---|---|
| `git status --short; git branch --show-current; git rev-parse HEAD; git rev-parse origin/main` | 0 | Initially clean; expected branch; starting and cached main SHA above. |
| Inline locked-blob and historical-file snapshot audit | 0 | Both locked blobs match; 108 historical files snapshotted. Initial tracked-byte comparison failed on quoted Unicode path names (exit 1); corrected NUL-delimited comparison passed (exit 0). |
| Inline cached dependency audit and copy | 0 | 147 packages match the unchanged lockfile; ignored installation copied without downloads. |
| `node --experimental-test-module-mocks --test reference/rights_scale/client/mint-note.test.mjs` (first attempt, Node 24) | 1 | Missing `circomlibjs` before cached dependency copy; no assertions executed. |
| Same narrow command (second attempt) | 1 | Crypto mock bridge failed to redefine `constants`; corrected by copying the default export, without changing implementation. |
| Same narrow command (final) | 0 | 1 passing file-level summary; zero failures/cancellations/skips/TODOs. |
| `node --experimental-test-module-mocks reference/rights_scale/client/mint-note.test.mjs` | 0 | 13 named cases pass; zero failures/cancellations/skips/TODOs. |
| `npm --prefix reference/rights_scale/client run test:offline` | 0 | All 7 explicit suites pass; runner reports 7 files/tests; zero failures/cancellations/skips/TODOs. |
| `node --version` | 0 | v24.19.0 |
| `npm --version` | 0 | 11.21.0 |
| `python3 --version` | 0 | Python 3.12.15 |
| `rustc --version` | 0 | rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo --version` | 0 | cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 129 tests passed; OK. |
| `node reference/rights_scale/client/gen-move-vectors.mjs --check` | 0 | Move known-answer constants match circomlibjs: 23 vectors |
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=198 indexed=163 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected in temporary fixtures. |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0 | 7 tests passed; OK. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 78 passed across test binaries/doc tests; 0 failed, 0 ignored. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 257 passed across test binaries/doc tests; 0 failed, 0 ignored. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Passed with -D warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Formatting check passed. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | Only kix-types is a normal kernel dependency. |
| `python3 /tmp/mint-wrapper-preservation.py` | 0 | Exactly five allowed changed paths; index untouched; locked blobs and all 108 historical files match; package/workflow additions only; diff whitespace check passes. |
| `git diff --check` | 0 | No whitespace errors. |

## Preservation

Before editing, both locked kernel working-file blobs matched their required IDs:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`src/lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
A SHA-256 snapshot of 108 files under `reference/v0.3-rc1/` (excluding
`node_modules`) was saved outside the repository; every tracked historical file
was also compared byte-for-byte with HEAD using NUL-delimited Git paths.
The first tracked-file comparison failed on Git-quoted Unicode names; the
NUL-delimited correction passed. No protected bytes were changed.

After tests, `/tmp/mint-wrapper-preservation.py` again verified both locked
blobs and all 108 historical files, including byte comparisons with HEAD and the
pre-edit SHA-256 snapshot. Historical subtree at HEAD:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The Git index remains untouched.
The package diff only appends `mint-note.test.mjs`; removing the new two-line CI
step reproduces the original workflow byte-for-byte. All existing workflow
gates, checks, pins, permissions, timeouts and conditions are preserved.

Complete changed-path list:

- `reference/rights_scale/client/mint-note.test.mjs`
- `reference/rights_scale/client/package.json`
- `.github/workflows/protocol.yml`
- `docs/README.md`
- `validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md`

Implementation/final builder Git HEAD remains
`9eb6b5f932cae5f4f1b431ef79c9f15874db1c36`; changes are uncommitted as requested.
There is no final committed delivery SHA or final-merge blob check yet.

## Discrepancies and non-claims

No explicit contract violation was found. The pre-insertion note shape is a
source-informed characterization consistent with the later `NoteAdded` index
assignment; it does not redefine the post-insertion RR-4 backup contract. No new
contract-undefined behavior or policy value was adopted.

Deviations: fetch was omitted under the explicit no-network instruction; cached
main freshness remains unverified. Cached dependencies needed a local ignored
copy, and the crypto mock needed a copied default export for Node's bridge.
The two failed narrow attempts and corrected path audit are recorded above.
The design's five delivery paths and implementation boundaries are unchanged.

These are synthetic, source-informed wrapper tests within EV-RS, sharing
Poseidon. They establish neither circuit validity nor cryptographic independence,
real artifact/key integrity, operational verifier pinning, chain execution,
durability, privacy or production readiness. No evidence-map status or grade is
raised. All owner-controlled policy values remain UNDETERMINED with their
existing owners; in particular operational depth, K, shard counts and retention
are not chosen here. No funds, providers, secrets, keys, generated proving
artifacts or network are used. Bootstrap, circuit generation/ceremonies/proving,
Move/localnet journeys and storage probes were excluded from local verification.
No operational parameter or owner was changed. Remaining follow-up is supervisor
publication, A2 non-author exact-head review and exact-head hosted verification;
real circuit/artifact/chain properties remain with their existing evidence and
gates.

## Delivery gates

Implementation/final committed head: not created by this builder; supervisor owns
Git publication. Exact-head KTX and KIX CI run IDs/status/conclusions: unobserved,
outstanding. A2 non-author exact-head review: outstanding. Merge SHA and post-merge
CI: not applicable (not merged). Local checks do not establish hosted CI success
or merge readiness.
