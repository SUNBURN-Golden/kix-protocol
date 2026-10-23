# Offline RS-2 public-byte encoding regressions

Node: `plan-rs-zk-encoding-regressions`, 2026-10-21. Task input is the
supervisor-supplied node specification and read-only design plan in this session;
no issue or `docs/tasks/` document was supplied. Dependencies: `rs-2` and
`plan-rs-manifest-offline-regressions`. Not ASTRA program mode. Audit floor A2;
`astra_gate: None`; `user_merge: False` grants no merge authority.

## Baseline identity

Branch: `agent/kix-plan-rs-zk-encoding-regressions`. Starting HEAD and cached
`origin/main` both equal `b761bd60f45f224b4c5db5e3af6963eb6e7dc4d5`;
initial worktree clean, no local base delta. The supervisor prohibits network
actions, so `git fetch origin main` was not run; remote freshness is unverified.
Implementation/final task head is not assigned: the supervisor owns commits and
publication. No merge commit or post-merge evidence exists.

## Coverage recorded before adding tests

Inspected `reference/rights_scale/client/zk-helpers.mjs`, `zk-test-utils.mjs`,
`zk-regression.mjs`, `setup-zk.mjs`, `private-scale.mjs`,
`zk-policy-v2.test.mjs`, both workflows, the
[RS-2 record](../2026-10-14-rs-2-private-path/README.md), the
[manifest regression record](../2026-10-21-plan-rs-manifest-offline-regressions/README.md),
and `docs/contracts/RIGHTS_SCALE_PROFILE.md` IM-16/IM-17.
This table was written before creating the new test file.

| Requirement | Prior coverage | Existing assertion / gap |
|---|---|---|
| Little-endian order and 8-/32-byte integer boundaries | Not covered | `little` is used by point/count encoding; no direct boundary or asymmetric byte-vector assertions. |
| Proof component order and widths | Partially covered | `zk-test-utils.mjs::unpackProof` checks length 128 and `Arkworks fixture round trip`; `zk-regression.mjs` section 3 uses it on artifact-backed mint/spend proofs. No independently assembled full-byte vector. |
| G1/G2 sign branches and G2 tie | Partially covered | Same artifact-backed round trips exercise available points, without explicit sign thresholds or G2 tie assertions. |
| Noncanonical field and non-affine coordinates | Not covered | No isolated `NONCANONICAL_FQ` / `AFFINE_POINT_REQUIRED` assertions. |
| VK order, widths and IC count bytes | Partially covered | `setup-zk.mjs` writes `vkBytes(key)`; `private-scale.mjs::artifacts` compares that same encoding to the saved file (`VERIFIER_ENCODING_MISMATCH`). No independent layout/count vector. |
| Explicit `vkBytes` protocol/curve/count rejection guards | Not covered | `zk-policy-v2.test.mjs` sufficiently covers its separate `requirePhase2Key` guards; those assertions do not call `vkBytes`. |
| Standalone suite before bootstrap | Not covered for encoder | Existing manifest suite is dependency-free and invoked before bootstrap; encoder-specific suite absent. |
| Indexed record / documentation check machinery | Sufficiently covered | Reuse `scripts/check_docs_index.py` and its self-test; add only this node's index entry. |

## Changed paths and new case mapping

- `reference/rights_scale/client/zk-helpers.test.mjs`: synchronous, table-driven
  tests importing only `node:test`, `node:assert/strict`, and the three encoders.
- `.github/workflows/protocol.yml`: one additive `Offline public-byte encoding
  regressions` invocation immediately after the offline manifest suite and
  before bootstrap in `rights-scale`, under its existing Node 24 pin.
- `docs/README.md`: relative link in the October 21 validation index.
- `validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md`: this record.

The suite is **source-informed encoding characterization**, using fabricated
decimal-string public coordinate records. Fresh proof/key factories and checked
positive controls precede isolated guard mutations. Expected buffers use literal
hex bytes, zero padding and concatenation; no function under test constructs
expected bytes, and no shifting or sign-selection algorithm is copied as an
oracle. The pinned FQ-minus-one byte vector was independently calculated using
Python `int.to_bytes(32, 'little')`. FQ is the coordinate modulus, not scalar FR.

| Gap | New cases / exact assertion |
|---|---|
| Integer order and boundaries | `little`: at 8 and 32 bytes, zero/one/255/256/unsigned maximum, negative one and first overflow (`INTEGER_ENCODING_RANGE`); asymmetric full-width vectors and omitted-width 32-byte vector. |
| Proof order and widths | Full 128-byte equality and slices for A at 0, B.x0 at 32, B.x1 at 64, C at 96, with distinct two-byte markers. |
| G1 signs | Both A and C: y=0, h, h+1, where h=(FQ-1)/2; literal expected 0x00/0x80 flag bytes. |
| G2 signs | y1=h with high y0; y1=h+1 with low y0; tie y1=0 with y0=0/h/h+1. Literal expected flags and full-buffer equality. Additional high-x case proves flags preserve existing high coordinate bytes in both G1 and G2. |
| Canonical field range | Every x/y limb in proof A/B/C and key alpha/beta/gamma/delta/IC[0]/IC[1]: accept 0 and FQ-1 with whole-buffer expectations; reject -1 and FQ with exact `NONCANONICAL_FQ`. |
| Affine coordinates | Every proof/key component accepts explicit 1 / [1,0] and omitted affine entries. Each G1 separately rejects z=0 and z=2; each G2 separately rejects z0=0 and z1=1, with exact `AFFINE_POINT_REQUIRED`. |
| VK layout/counts | Full equality and lengths `232 + 32 * IC.length` for counts 1/2/256; explicit eight-byte count vectors, including `00 01 00 00 00 00 00 00`. Distinct alpha/beta/gamma/delta and alternating IC markers; a mixed-sign key checks flags in their own point offsets. Counts are serialization examples, not profile policy. |
| VK format guards | Missing/wrong protocol, missing/wrong curve, short/long IC, mismatched/missing nPublic, each from a fresh valid control and each exactly `VK_FORMAT`. This does not impose stronger `requirePhase2Key` policy on `vkBytes`. |

## Preservation

| Locked file | Required Git blob | Before / after |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match / match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match / match |

`git hash-object` checked both working-tree files before and after work.
An inline Python/Git audit compared all 902 tracked files outside the four-path
allowlist to their starting Git blobs: all match. That includes all 108 files
under `reference/v0.3-rc1/`, whose baseline tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The tracked diff plus nonignored
untracked list is exactly the four delivery paths; the Git index is unchanged.
Encoders, contracts, BCS decoders, constants, dependency files, `.aiops/`, task
documents and historical evidence remain unchanged. No transient source
mutations were used.

Inline PyYAML `BaseLoader` checks parsed both workflows (including literal `on`).
The new step contains only `name` and `run`, with no conditional bypass or failure
suppression. Removing that step reproduces the original workflow's exact bytes
and parsed structure: all existing checks, action pins, timeouts, permissions,
cache settings and conditions are preserved.

## Commands actually run and results

All verification ran from the repository root with PATH preferring the existing
`/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin`. Node **24.19.0**, Python **3.12.15**, PyYAML
**6.0.3**, Cargo/Rust **1.98.1**. Initial PATH probes found Node 20.19.2 and
Python 3.13.5; those were not used for acceptance checks. No installation,
artifact generation or background job was performed. Rust commands used cached
dependencies with `CARGO_NET_OFFLINE=true`; Python verification used
`PYTHONDONTWRITEBYTECODE=1`.

All verification commands below exited 0. The combined Node command was run
before broader checks and again after adding the high-x sign-preservation case;
both runs passed. Direct suite execution additionally exposes individual case
counts because `node --test` here reports file summaries. The initial encoder
suite passed 165 cases; the final suite passes 166. No failed, cancelled, skipped
or TODO Node cases occurred. No implementation changes were needed.

| Command | Exit | Result |
|---|---|---|
| `git rev-parse HEAD` / `git rev-parse origin/main` / `git branch --show-current` | 0 | Baseline SHA and task branch as recorded above; no local base delta. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | 0 | Both required blobs match before and after. |
| `git ls-tree HEAD reference/v0.3-rc1` | 0 | Preserved reference tree as recorded above. |
| `node --version` / `python3 --version` / `rustc --version` / `cargo --version` | 0 | Pinned verification versions above; initial default PATH versions distinguished above. |
| `python3 -c 'import yaml; print(yaml.__version__)'` | 0 | 6.0.3, already installed. |
| Inline Python `int.to_bytes` fixture calculation | 0 | Pinned FQ-1 little-endian hex; asymmetric input values cross-checked. |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | Both file summaries pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs` | 0 | Final CI invocation passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/zk-helpers.test.mjs` | 0 | Final 166 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 267 named cases pass; 0 failures/cancellations/skips/TODOs. |
| Inline import-graph / offline fixture audit | 0 | Only the three allowed suite imports and Node built-ins in helper; no dynamic import, skip or TODO. `client/node_modules` absent; artifacts directory contains only existing README. |
| Inline PyYAML parse and baseline workflow comparison | 0 | Additive pre-bootstrap step only; exact preservation verified. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 129 tests, OK. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 78 tests pass, 0 failed/ignored. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 257 tests pass, 0 failed/ignored. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Clean; includes kernel. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Clean. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | Kernel normal dependency is local kix-types only. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | 0 | Hashes recorded below. |
| Inline Python/Git baseline and four-path allowlist audit | 0 | 902 tracked files preserved, including all 108 reference files; index unchanged. |
| `git diff --check` | 0 | No whitespace errors. |

Dependency-evidence SHA-256 values, in command order:

```text
a948a1b687de2727ad717db0f7a0aa4159ecf5258e52e18eccf05cc08329d83e  runtime/Cargo.lock
84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f  runtime/crates/kix-kernel/src/lib.rs
d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae  runtime/crates/kix-kernel/tests/transitions.rs
```

The existing `Stdlib offline document checks` block's 26 commands were extracted
unchanged from the parsed workflow and executed individually, followed by both
architecture commands. Their actual results are recorded here. Self-tests
exercise synthetic/in-memory negative controls; diagnostics for detected
corruption are expected and their terminal result is pass.

| Command | Exit | Actual result |
|---|---|---|
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=192 indexed=157 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | self-test: pass (supplied map and zero-PARTIAL baseline) |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0 | 7 tests, OK |

Read-only discovery probes initially tried nonexistent `.github/workflows/ktx.yml`
and `.github/workflows/kernel.yml` (exit 1); inspection then used the actual
`ktx-kernel.yml`. An optional directory-glob listing returned exit 2 for absent
paths. These were discovery errors, not verification results.

## Contract classifications, limits and delivery

No explicit contract violation was found. **B: contract-undefined/source-informed
characterization** applies to the fabricated-coordinate byte layouts and explicit
encoder guards above; these are observations of the existing serializer, not new
cryptographic semantics or a strengthened contract. Malformed shapes and broader
JavaScript coercions outside the explicit guards were not specified or tested.
The existing IM-17 interpretation of “other keys” remains unresolved; operational
policy values, including root-history K, remain **UNDETERMINED**. Nothing here
selects a policy value or alters an authoritative contract.

No curve membership, proof validity, usable verification key, clean-room
independence, independent cryptographic verification, anonymity, durability,
performance, chain finality, legal compliance or production readiness is claimed.
No bootstrap, proving artifacts, setup ceremony, Move tests, localnet journey,
testnet/mainnet, full protocol execution, external provider or real funds were
used. Existing artifact-backed/chain checks remain intact for supervisor CI.

| Gate / identity | Status |
|---|---|
| Implementation head / final task head | Not assigned; uncommitted worktree on starting HEAD. Supervisor owns Git. |
| Exact-head KTX workflow run ID / status / conclusion | Unavailable / not run / not run. |
| Exact-head KIX protocol workflow run ID / status / conclusion | Unavailable / not run / not run. |
| Non-author A2 exact-head review | Not performed; required after supervisor commits. |
| Merge SHA / final-merge locks / post-merge main CI | Not applicable; no merge performed. |

Local delivery is complete and ready for supervisor review/publication, with no
merge-ready claim. Remaining uncertainty is exact-final-head hosted CI, including
artifact-backed and chain checks, and non-author review. No consequential scope
expansion or decision stop was needed. Design deviations: the supervisor's network
ban overrides the session-start fetch; cached main freshness is unverified. An
extra high-x sign-preservation case and direct Node suite runs strengthen the
specified local evidence. No other design deviation.
