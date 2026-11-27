# Offline admission packet and proof-wrapper regressions

Node `plan-rs-admission-packet-offline-tests`, 2026-10-22. Task input: the
supervisor-supplied node specification and read-only design plan, from planner
run `1792626649`. No issue or task document under `docs/tasks/` exists for this
node; this is not ASTRA program mode. Dependencies: `rs-2`,
`plan-rs-spend-witness-offline-tests`, `plan-rs-offline-test-entrypoint`.
Audit floor A2; `astra_gate: None`; `user_merge: False` grants no merge authority.

## Identity and delivery

Branch: `agent/kix-plan-rs-admission-packet-offline-tests`. Starting HEAD and
cached `origin/main`: `93cec6aaf12f22bf8aefc0453fe545b6bd38b819`.
Initial worktree clean; no local base delta. Fetch was omitted under the
supervisor's explicit network prohibition, so remote freshness is unverified.
Implementation and exact final task heads are unassigned: the delivery is an
uncommitted patch, and the supervisor owns commits and publication. Starting
HEAD does not contain this patch. No merge SHA or post-merge check applies.

Exactly five delivery paths:

- `reference/rights_scale/client/admission-packet.test.mjs`
- `reference/rights_scale/client/package.json` (only `scripts["test:offline"]`)
- `.github/workflows/protocol.yml` (one additive test invocation)
- `validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md`
- `docs/README.md` (one exact-file relative link)

## Coverage inspected before adding cases

Paths in this table are relative to `reference/rights_scale/client/`.

| Requirement | Existing coverage classification and anchor | Added evidence |
|---|---|---|
| Spend guards, inclusion paths, slot/index distinction | **Sufficiently covered** by `spend-witness.test.mjs`: `domain_mismatch`, `commitment_binding`, `selected_prefix`, `distinct_indices` | Existing matrices reused unchanged. |
| Public witness order/context, caller preservation | **Sufficiently covered** at witness boundary by `gate_limbs_and_public_order`, `context_binding`, `repeat_calls_preserve_inputs` in that suite; **partially covered** at admission-wrapper boundary | All new cases snapshot caller values and retain leaf-array/Map identity in `finally`. |
| Proof byte encoding | **Sufficiently covered** by `zk-helpers.test.mjs`: `source-informed: proof A / B.x0 / B.x1 / C order and widths` and coordinate guards | Reuse fabricated coordinates with literal byte expectations for packet integration. |
| Manifest/key metadata guards | **Sufficiently covered** by `zk-policy-v2.test.mjs`: synthetic manifest control, field mutations, guard-compatible synthetic keys and equal gamma/delta cases | No duplicate policy matrix; policy checks explicitly stubbed here. |
| Event reconstruction/read boundary | **Sufficient existing offline coverage** in `witness-reconstruction.test.mjs`: empty/populated trees, ordering, filtering, roots/counts and injected object allowlist | No reconstruction/decoder change. |
| Cryptographic admission path | **Partially covered** by `zk-regression.mjs`: section 2 calls `admissionProof`; section 4 exercises circuit witness rejection using artifacts | Inspected only; no proving or ceremony run here. |
| Exact public packet and forbidden witness fields | **Not covered** by those suites | `packet_contains_only_public_fields`. |
| Prover public-signal order/count/value rejection | **Not covered** at wrapper boundary | `public_signal_layout_rejections`: swap distinct roots, remove/add a signal, alter each of six positions. |
| Local verifier rejection and prover-error propagation | **Not covered** by synthetic offline wrapper tests | `local_verification_failure`, `prover_failure_propagates`. |
| Dependency order and rejection stage cutoff | **Not covered** at wrapper boundary | Exact event traces in every new case; no verifier/encoding after layout rejection, no post-prove key read after prover error. |
| Offline package/CI discovery | Existing package invokes five suites; new suite **not covered** | Append sixth suite and mocking flag; one explicit CI command after spend-witness tests, before Move/localnet/proving. |

## Fixtures, oracle and mocked boundaries

Calls use the real unchanged `admissionProof` -> `spendWitness` -> lexical
`prove` and `artifacts` bodies. The client is dynamically imported only after
Node 24 `mock.module` registration; the client itself and its functions are
never mocked, transformed or copied. Cases run sequentially, reset mock state
for every invocation, and restore mocks after the suite.

The published spend-witness fixture supplies public synthetic scalars: secret
17, slot 700, generation 4, domain 77, insertion index 2, gate limbs 19/37,
challenge 23, expiry 1900000000123. Every call supplies a challenge. No random
fallback or `mintNote` is called. Tree leaves are 101, 102, the fixture
commitment, 104, 105; revocations are `(700,3)`, `(2,1)`, `(701,2)`.

A test-local dense bottom-up fold independently assembles roots without the
sparse-tree/path helpers. Before any invocation, expected public signals are
assembled literally in the order `[noteRoot, revocationRoot,
H(17,700,4,77,2), H(19,37,23,1900000000123,1), 77, 1]`, then converted to
decimal strings. Expectations do not come from captured prover input, packet
output or `SPEND_PUBLIC`. Poseidon and `DEPTH` are shared with the client;
this is source-informed structural evidence, not clean-room independence.

The synthetic response uses the fabricated coordinates from the encoder suite
(`pi_a` x 513, `pi_b` x limbs 1027/1541, `pi_c` x 2055). Literal expected
little-endian words start `0102`, `0304`, `0506`, `0708`, each padded to 32
bytes. These are encoder fixtures, not generated or valid cryptographic proofs.

| Dependency | Exact test replacement / limit |
|---|---|
| `snarkjs.groth16.fullProve` | Returns fabricated coordinates and independent expected signals, mutated signals, or throws the exact sentinel error. Checks actual spend-witness scalar/path presence and exact paths `spend_scale_js/spend_scale.wasm` / `spend_scale.zkey`. No proving. |
| `snarkjs.groth16.verify` | Recording configurable boolean stub, checking spend-key sentinel and proof/signal object identity. No cryptographic verification. |
| `node:fs/promises.readFile` | In-memory allowlist only: manifest JSON, spend wasm/zkey sentinel buffers, mint/spend VK sentinel bytes. Unexpected reads fail. Real `artifacts()` parses manifest bytes and hashes listed sentinel buffers using real SHA-256. No artifact reads from disk. |
| `zk-helpers.mjs.readJSON` | Only mint/spend `.vkey.json` paths allowed; returns tagged objects with no key material. |
| `zk-helpers.mjs.vkBytes` | Records exact sentinel identity and returns tagged byte buffers. Does not establish key validity or encoding integrity. |
| `zk-helpers.mjs.proofBytes` | Records call and proof identity, forwards to the unchanged real encoder. Real `FR` and `sha256` retained. |
| `zk-policy-v2.mjs` guards | Recording stubs for manifest/key checks, asserting the sentinel manifest and public counts 4/6. Actual policy validation is outside this suite's claims. |

The packet is compared in full with independently assembled expected values
and exactly seven own fields: `noteRoot`, `revocationRoot`, `nullifier`,
`challenge`, `expiresMs`, `proof`, `publicSignals`. The first five are decimal
strings, proof is a byte array, signals are the expected six decimal strings.
Recursive own-key inspection rejects note, secret, slot, generation, inverse,
input and witness-path fields. It does not search numeric substrings.

Successful order is manifest/artifact/key checks -> proving -> spend-key JSON
read -> local verification -> real encoding. Wrong signal order/count/value
throws `CIRCUIT_PUBLIC_INPUT_LAYOUT`; false verification throws
`LOCAL_GROTH16_VERIFICATION_FAILED`; prover failure propagates the identical
error. Rejected promises cannot return packets, and exact event traces exclude
subsequent stages.

## Commands and actual results

All commands run from the repository root. PATH prefers the provisioned
`/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin`. Python checks inherit
`PYTHONDONTWRITEBYTECODE=1`; Cargo checks inherit `CARGO_NET_OFFLINE=true`.
Actual versions: Node 24.19.0, npm 11.21.0, Python 3.12.15, rustc 1.98.1
(`48a229cea`, 2026-09-01), Cargo 1.98.1 (`797e8a9bc`, 2026-08-05).
The initial system Node was 20.19.2; no suite was run with that version.

Cached dependencies came from
`/workspace/kix-run/wt/plan-rs-offline-test-entrypoint/reference/rights_scale/client/`.
Before copying, both its package manifest and lockfile matched this worktree.
Only the ignored installation was copied; no bootstrap/install/download ran.
Ignored scratch logs, command/result JSON and preservation audit scripts live
under `.local/verification/admission-packet/`. All subprocesses were awaited;
no shell background job was launched.

`node --test` on this toolchain reports files as tests. Direct-file runs
provide the named-case counts separately. Narrow admission runs preceded the
package, existing-suite and broader checks. Direct admission execution emits
Node's expected experimental module-mocking warning and `namedExports`
deprecation warning; neither is suppressed.

| Command | Exit | Actual result |
|---|---|---|
| `git status --short; git branch --show-current; git rev-parse HEAD; git rev-parse origin/main` | 0 | Initially clean; branch/base/HEAD above. |
| `node --version; npm --version; python3 --version; rustc --version; cargo --version` | 0 | 24.19.0 / 11.21.0 / 3.12.15 / 1.98.1 / 1.98.1. |
| `cmp of cached package.json and package-lock.json before edit; cp -a cached node_modules into ignored client directory` | 0 | Both files identical; copied existing installation without downloads. |
| `Inline installed-package JSON audit` | 0 | All 147 package versions and version/resolved/integrity metadata match unchanged lock; identical package sets. |
| `Inline pre-edit Git blob / SHA-256 audit; git hash-object of both locks; git ls-tree HEAD reference/v0.3-rc1` | 0 | 912 tracked files match HEAD; 108 physical reference files snapshotted; both locks match; reference tree below. |
| `node --experimental-test-module-mocks --test reference/rights_scale/client/admission-packet.test.mjs` | 0 | 1 passing file-level summary; 0 failures/cancellations/skips/TODOs. |
| `node --experimental-test-module-mocks reference/rights_scale/client/admission-packet.test.mjs` | 0 | 13 named cases pass (four top-level plus nine nested); 0 failures/cancellations/skips/TODOs. |
| `npm --prefix reference/rights_scale/client run test:offline` | 0 | All six explicit suites pass; runner: 6 files/tests, 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 1 file-level summary passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 267 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs` | 0 | 1 file-level summary passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/zk-helpers.test.mjs` | 0 | 166 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/ptau-header.test.mjs` | 0 | 1 file-level summary passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/ptau-header.test.mjs` | 0 | 34 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | 1 file-level summary passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | 16 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/spend-witness.test.mjs` | 0 | 1 file-level summary passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/spend-witness.test.mjs` | 0 | 23 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | Ran 129 tests in 2.740s; OK. |
| `node reference/rights_scale/client/gen-move-vectors.mjs --check` | 0 | Move known-answer constants match circomlibjs: 23 vectors |
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=197 indexed=162 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | Self-test passed; expected diagnostic mutations detected. |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0 | Ran 7 tests in 0.155s; OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 9 test targets; 78 passed, 0 failed/ignored. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 42 test targets; 257 passed, 0 failed/ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Clean; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Clean. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | kix-kernel -> kix-types only (normal dependency tree). |
| `python3 .local/verification/admission-packet/check-preservation.py` | 0 | Both locks match; 108 physical reference files preserved; all other tracked bytes unchanged; exactly five delivery paths; exact package replacement and additive workflow confirmed. |
| `git diff --check` | 0 | Clean, including separate whitespace/newline checks for new delivery files. |


## Preservation, discrepancies and limits

Before edits, an inline Git blob audit confirmed all 912 tracked files matched
starting HEAD. SHA-256 snapshots cover all tracked files and all 108 physical
files under `reference/v0.3-rc1/`. Both locked kernel blobs matched:

| File | Before and after / required Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Reference tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
Post-work SHA-256 comparison verified every previously tracked path except
only the three authorized edits is byte-identical to its initial state;
`private-scale.mjs`, all existing tests, dependencies/lockfile, contracts,
circuits, decoders, `.aiops/`, task documents and kernel locks are preserved.
Both kernel hashes above matched before and after all test execution. All 108
physical reference files match the baseline, with no added/removed file.
Removing the new CI step restores the previous workflow byte-for-byte; its
existing job conditions and timeout are untouched. The package diff is exactly
the single script replacement specified by the design.

No explicit contract violation or new contract-undefined semantics identified.
The packet shape and wrapper failures match the unchanged implementation
(class A within this test boundary); synthetic coordinates and mocked policy
are characterization fixtures, not newly defined cryptographic semantics.
No contract, circuit, decoder, source, policy value, task document, `.aiops/`
file, dependency or lockfile is changed. Operational depth, K, shard counts,
retention and other operational parameters remain **UNDETERMINED**, owned by
Astra. Existing IM-19 status is unchanged.

This evidence addresses only IM-19's packet-construction portion. It does not
establish cryptographic privacy, proof validity, gate transport/call secrecy,
localnet execution, circuit correctness, transport completeness, actual
artifact integrity, operational readiness or closure of all IM-19 requirements.
No real funds, provider calls, public endpoints, keys, secrets, credentials,
ceremonies, chain journeys or production runtime are used. Bootstrap, Move,
Sui, proving and storage jobs are outside the local offline verification.

## Deviations and remaining work

The only governance deviation is omission of `git fetch origin main` under the
supervisor's explicit ban on every network/GitHub action. No implementation
scope deviation or decision stop was needed. Early read-only discovery tried
nonexistent `.github/workflows/ktx.yml` and historical dependency locations;
the actual `ktx-kernel.yml` and available cached installation were then used.
These were discovery misses, not failed verification commands. All acceptance
and applicable offline CI-equivalent commands above exited 0.

Full hosted CI was not run or observed. Bootstrap, Sui/Move, localnet,
ceremony/proving and storage jobs were intentionally excluded by the supplied
offline design. No older CI result is transferred to this patch. Follow-up
work for gate transport/secrecy, real-artifact behavior and cryptographic
privacy requires separately authorized evidence; complete IM-19 closure is
still open. Policy/architecture decisions remain with Astra and resources,
publication and merge authorization remain with the User/supervisor boundary.

## Delivery gates

| Gate | Exact final head / run ID | Status / conclusion |
|---|---|---|
| KTX kernel verification | Unassigned / unavailable | Not run or observed here; no pass claimed. |
| KIX protocol verification | Unassigned / unavailable | Not run or observed here; no pass claimed. |
| A2 non-author exact-head review | Supervisor's future committed head | Outstanding; builder evidence is not independent review. |
| Merge / post-merge main CI | No merge SHA / no run ID | Not applicable. |

Local delivery readiness does not establish merge readiness. The supervisor
owns publication and subsequent exact-head review/CI; both required workflows
must complete successfully on the actual final head before proposing merge.
No commit, push, PR, issue, comment, ASTRA marker, tag or branch mutation was
performed.
