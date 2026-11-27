# Offline RS-2 spend witness regressions

Node `plan-rs-spend-witness-offline-tests`, 2026-10-21. The task input is the
supervisor-supplied node specification and read-only design plan; no issue or
`docs/tasks/` document exists for this node. This is not ASTRA program mode.
Dependencies: `rs-2`, `plan-rs-witness-offline-regressions`,
`plan-rs-witness-ci-wiring`. Audit floor A2; `astra_gate: None`;
`user_merge: False` grants no merge authority.

## Identity and scope

Starting branch: `agent/kix-plan-rs-spend-witness-offline-tests`. Starting HEAD
and cached `origin/main` both equal
`4e5c30cc6779ea8b7d26fa40fdde6c84adfd44b7`; initial worktree clean, no local
base delta. `git fetch origin main` is not run because the supervisor explicitly
prohibits all network actions. Remote freshness is unverified.

Implementation/final task head: unassigned; the supervisor owns commits and
publication. This delivery consists of uncommitted changes above the starting
HEAD. No merge commit or post-merge evidence exists.

Only these delivery paths are allowed:

- `reference/rights_scale/client/spend-witness.test.mjs`
- `.github/workflows/protocol.yml`
- `docs/README.md`
- `validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md`

## Existing coverage mapping (recorded before adding tests)

| Requirement | Existing coverage and classification | Gap addressed here |
|---|---|---|
| Direct domain and commitment guards | **Not covered** directly: `client/zk-regression.mjs` section 4 changes domain in a circuit witness/mint input, rather than asserting the client guard diagnostics. | Positive controls, isolated tree-domain and note-field mutations; coherent alternate-domain control and stale commitment. |
| Membership in a selected prefix | **Partially covered**: `zk-regression.mjs` sections 2/4 construct current views and reject wrong root/path circuit witnesses; the private localnet journey exercises historical views. | Direct inclusion/exclusion at insertion index 2, default/full/short prefixes, removed commitment and ignored suffix. |
| Insertion versus revocation slot index | **Partially covered** by the slot-3 witnesses and wrong-slot revocation path in `zk-regression.mjs` section 4. `witness-reconstruction.test.mjs` `populated_tree` and `maximum_revoked_generation` sufficiently cover reconstructing leaves and maxima, but do not call `spendWitness`. | Dense oracle for note index 2 versus revocation slot 700, including distinct leaves at both indices. |
| Gate limbs, context, action, nullifier and public order | **Partially covered** directly. `zk-regression.mjs` section 3 sufficiently covers proof-level single-public-input tampering; section 4 sufficiently covers wrong context, action, nullifier, root/path and revoked-note circuit refusal. | Literal six-signal order, dense roots/paths, separately computed hashes and limb/context mutations without proofs. |
| Determinism and caller non-mutation | **Not covered** by the existing witness suites. | Repeat complete outputs and snapshot tree/leaves/Map/note/options for successful and rejected calls. |
| Tree event reconstruction and root/count/index guards | **Sufficiently covered** by all 16 named reconstruction cases, including `missing_note_index`, `duplicate_note_index`, root/count mismatch and omitted/duplicated revocation cases. | Reuse unchanged; no duplicate event/decoder tests. |
| Manifest policy and byte encoding | **Sufficiently covered** at their separate offline boundaries by `zk-policy-v2.test.mjs` and `zk-helpers.test.mjs`. | Reuse unchanged. |
| CI invocation | **Not covered** for the new suite. Existing reconstruction runs after bootstrap. | Add one step immediately after reconstruction, before Move/localnet/proving. |

Paths abbreviated `client/` above are under `reference/rights_scale/`.

## New evidence and fixture provenance

`reference/rights_scale/client/spend-witness.test.mjs` uses only published
synthetic scalars: secret 17, slot 700, generation 4, domain 77 (alternate 78),
and commitment `H([17,700,4,domain,1])`. The commitment is inserted at index 2
in `[101,102,commitment,104,105]`. Revocation leaves are `700 -> 3`, `2 -> 1`,
`701 -> 2`. Expiry is fixed at `1900000000123`; challenges are explicitly 23
or 0. Every call supplies a challenge, including rejection paths. Gate addresses
are assembled by `high * 2**128 + low` from public limb pairs, never sampled.
No note minting, random fallback, proof generation, artifact loading, RPC or
chain execution is invoked.

The expectation helper fills all `2**DEPTH` leaves, folds adjacent pairs
bottom-up and collects siblings. It does not call client sparse-tree helpers.
Expected public signals are independently assembled in the literal order
`[noteRoot, revocationRoot, H(secret,slot,generation,domain,2),
H(gateLow,gateHigh,challenge,expiresMs,1), domain, 1]`. Expected order is not
derived from returned fields or `SPEND_PUBLIC`. The returned inverse is checked
algebraically with `secret * inverse % FR == 1`, including decimal-string shape.
All scalar fields, array lengths, complete output shape and BigInt return
values are checked. Every invocation snapshots tree, leaves, Map, note and
options, and checks retained leaf-array and Map identities in `finally`.

This oracle is **source-informed**, shares the client's circomlibjs Poseidon
primitive, `DEPTH` and `FR`, and is not clean-room or independent cryptography.
The names `secret`/`note` describe public fixtures here, not usable private notes.

| New named test | Acceptance evidence |
|---|---|
| `domain_mismatch` | Passing original and alternate-domain controls; changing only tree domain gives exact `NOTE_DOMAIN_MISMATCH`. |
| `commitment_binding` | Separate secret, slot, generation and commitment mutations give exact `NOTE_COMMITMENT_MISMATCH`; matching alternate tree/note domains with a stale commitment isolates domain commitment binding. |
| `selected_prefix` | Default equals explicit full count; count 3 includes insertion 2; counts 2 and 0 exclude it; removed commitment gives exact `NOTE_NOT_ON_CHAIN`; suffix changes cannot alter selected-prefix output. Accepted roots/paths match dense expectations. |
| `distinct_indices` | Note bits/path use insertion 2, revocation maximum/path use slot 700; fold both paths to expected roots, and distinguish slot-2 versus slot-700 leaf mutations. |
| `gate_limbs_and_public_order` | Zero gate, low-limb maximum, the `2**128` boundary and unequal nonzero limbs; explicit challenge 0; exact six-signal order, nullifier, context and admission action 1. |
| `context_binding` | Change low limb, high limb, challenge or expiry separately; recomputed context changes while roots/nullifier/domain/action remain stable. |
| `repeat_calls_preserve_inputs` | Complete repeat output equality with challenge 0, plus caller snapshots on success and all three requested guard failures. |

These seven top-level cases contain 23 named cases including nested cases.
The evidence supplements draft `RIGHTS_SCALE_PROFILE.md` IM-14 commitment
binding and IM-15 insertion/slot indices, nullifier, action and context
construction. It stays within `CURRENT_CAPABILITY_REGISTER.md` EV-RS's
reference-fixture boundary. No map/status/grade changes are made.

## Preservation and workflow checks

| Locked file | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

`reference/v0.3-rc1` starts at tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b` and is excluded from all edits.
The final inline Git-blob preservation check confirms all 904 tracked files
outside the allowlist are byte-identical to starting HEAD, including all 108
files under `reference/v0.3-rc1/`. Both locked blobs match in the index and
working tree. The tracked diff plus nonignored untracked files contains exactly
the four delivery paths listed above; branch and HEAD remain unchanged. This
also preserves `.aiops/`, task documents, implementation, contracts, package
manifests/lockfiles, policy values and the kernel workflow.

The new `rights-scale` step is exactly `name` plus the requested `node --test`
command, immediately after reconstruction and dependency setup, before
Move/model/localnet/proving. A PyYAML BaseLoader check parsed both workflows,
verified Node 24 and step order, and confirmed that removing only the addition
restores both the baseline parsed structure and raw bytes. No condition,
suppression, retry, timeout, permissions or existing check changed.

## Execution environment

All verification runs from the repository root. PATH places existing
`/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin` first: Node 24.19.0, Python 3.12.15,
PyYAML 6.0.3. Cargo/Rust are 1.98.1. Python uses
`PYTHONDONTWRITEBYTECODE=1`; Cargo uses `CARGO_NET_OFFLINE=true`.
Initial default tool probes reported Node 20.19.2 and Python 3.13.5; neither
default was used for verification.

Existing ignored `node_modules` was copied from
`/workspace/kix-run/wt/plan-rs-witness-offline-regressions/reference/rights_scale/client/`.
`cmp` confirmed that source and destination package manifests and lockfiles
match. An inline Python comparison checked all 147 installed package versions
and their `.package-lock.json` version/resolved/integrity metadata against the
unchanged repository lockfile, with identical package sets. No install,
download or bootstrap was needed.

The workflow's complete `Stdlib offline document checks` command list was
extracted with BaseLoader and executed sequentially, including all self-tests.
The exact commands/results are recorded below. Logs are local under
`/tmp/rs-spend-witness-evidence/`; they are not committed evidence artifacts.

## Commands actually run and results

| Command | Exit | Actual result |
|---|---|---|
| `node --test reference/rights_scale/client/spend-witness.test.mjs` | 0 | One passing file-level runner summary, zero failures/skips. |
| `node reference/rights_scale/client/spend-witness.test.mjs` | 0 | 23 named cases passed (seven top-level, nested cases included), zero failures/skips. |
| `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | One passing file-level runner summary, zero failures/skips. |
| `node reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | 16 named cases passed, zero failures/skips. |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | One passing file-level runner summary, zero failures/skips. |
| `node reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 267 named cases passed, zero failures/skips. |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs` | 0 | One passing file-level runner summary, zero failures/skips. |
| `node reference/rights_scale/client/zk-helpers.test.mjs` | 0 | 166 named cases passed, zero failures/skips. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 129 tests, OK. |
| `node reference/rights_scale/client/gen-move-vectors.mjs --check` | 0 | Move known-answer constants match circomlibjs: 23 vectors |
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=193 indexed=158 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | Self-test: pass (expected diagnostic mutations detected in temporary fixtures). |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0 | 7 tests, OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 9 test targets; 78 passed, 0 failed, 0 ignored. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 42 test targets; 257 passed, 0 failed, 0 ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Clean; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Clean. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | kix-kernel -> kix-types only (normal dependency tree). |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | 0 | All three hashes recorded in local log; preservation independently checked by Git blobs. |
| `node --version`, `python3 --version`, `cargo --version`, `rustc --version` with verification PATH | 0 | Node 24.19.0, Python 3.12.15, Cargo/Rust 1.98.1 (version probes used absolute paths for Node/Python). |
| `git rev-parse origin/main HEAD`, `git branch --show-current`, `git status --short` | 0 | Both SHAs match the recorded base; expected branch; initially clean. |
| `git hash-object` / `git ls-files -s` on locked files | 0 | Both required blobs match working-tree bytes and index before work. |
| `git ls-tree HEAD reference/v0.3-rc1` | 0 | Preserved reference tree ID recorded above. |
| `cmp` of reused package.json and package-lock.json; `cp -a` of existing node_modules | 0 | Matching inputs reused locally; no network or install. |
| Inline Python installed-package/lock metadata comparison | 0 | All 147 package versions, resolved/integrity records and package sets match. |
| Inline PyYAML BaseLoader workflow validation and baseline comparison | 0 | Both workflows parse; exact additive invocation/order; removal restores baseline parsed structure and bytes. |
| `git diff --check` | 0 | Clean after implementation; final repeat recorded below. |
| Inline Python `git ls-tree -r -z HEAD` / blob-byte comparison, lock/index checks and diff/untracked allowlist | 0 | 904 excluded tracked files byte-identical, including 108 reference files; both locked blobs match; exactly four paths; unchanged branch/HEAD. |
| Final `git diff --check` | 0 | Clean. |

Node 24's `--test` invocation reports a single passing file here; direct-file
execution additionally confirms named-case execution (23 new, 16 reconstruction,
267 manifest and 166 encoding cases). File-level counts are not substituted for
named-case coverage. All verification commands passed; no test-driven implementation fix or
retry was needed. Initial read-only workflow discovery tried the nonexistent
`.github/workflows/ktx.yml`; the actual `ktx-kernel.yml` was then inspected.

## Discrepancy classification, deviations and limitations

- No explicit contract violation or newly undefined contract behavior was found
  in the tested inputs. The construction checks match the cited IM-14/IM-15
  predicates (category A within the stated boundary).
- Malformed prefix/range semantics, duplicate commitment selection and
  noncanonical scalar inputs are not assigned new contract semantics or tested
  here. The pre-existing `test:offline` package script names a missing file; it
  remains unchanged and was not used. Explicit suite commands avoid that known
  package-script characterization.
- The only execution deviations are the supervisor's fetch/network prohibition
  and reuse of cached toolchains/dependencies instead of bootstrap. The four-path
  design and implementation scope are unchanged. No secrets, resources, new
  commands or policy decisions are needed; no `DECISION_REQUIRED.md` is needed.
- This is offline client construction evidence, not circuit verification,
  independent cryptographic proof, expiry enforcement, challenge replay
  protection, historical-root acceptance, real object/event completeness,
  Move/Sui execution, new localnet results or RS-4 measurement.
- Full bootstrap, Move/localnet, ceremony, proving and other unrelated protocol
  integration jobs were not run: this node forbids proof artifacts/chain
  execution, and bootstrap performs network installs and writes into the
  preserved reference tree. Closest applicable offline checks are listed above.
- No production readiness, durability, finality, anonymity, legal compliance,
  performance, real-funds or operational activation claim is made. Operational
  depth, K, shard counts and retention remain **UNDETERMINED**, owned by Astra.
  Existing test-only `DEPTH=10` and all constants/contracts remain unchanged.
- No commit, push, PR, issue, comment, tag, branch mutation or merge was performed.
  No GitHub/network action was taken. The supervisor owns publication.

## Remaining delivery gates

| Required workflow | Exact final task head | Run ID | Status / conclusion |
|---|---|---|---|
| KTX kernel verification | Not assigned; uncommitted delivery | unavailable | Not run/observed here; no pass claimed. |
| KIX protocol verification | Not assigned; uncommitted delivery | unavailable | Not run/observed here; no pass claimed. |
| Post-merge main CI | No merge | unavailable | Not applicable. |

Local completion is a supervisor handoff, not merge readiness. After the
supervisor commits, both exact-head workflows must complete successfully,
and A2 non-author exact-head review and any required human authorization
remain outstanding. No old-head CI is transferred to this patch. Record
final-head CI outside the repository to avoid an evidence self-reference loop.
