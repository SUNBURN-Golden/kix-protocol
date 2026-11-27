# Offline RS-2 phase-1 header parsing regressions

## Task input and baseline

Node `plan-rs-ptau-header-tests`, 2026-10-21. Task input is the supplied node
specification and read-only design plan in this session; no issue or
`docs/tasks/` document exists for this node. Dependencies: `rs-2`,
`plan-rs-manifest-offline-regressions`, `plan-rs-zk-encoding-regressions`.
Audit floor A2; `astra_gate: None`; non-program-mode execution.
`user_merge: False` grants no publication or merge authority; the supervisor
owns commits and GitHub actions.

Branch `agent/kix-plan-rs-ptau-header-tests` started clean at
`20b692b0e7de91f70693d15b14ff5c5c52fc21cb`, equal to the locally observed
`origin/main`. No local base delta. The supervisor's explicit network ban
overrides the initial fetch: `git fetch origin main` was not run, and remote
freshness is unverified. Implementation/final task head is not assigned;
delivery remains an uncommitted worktree on that baseline. No merge occurred.

## Coverage before additions

This table was written before creating the new suite. Inspected the parser,
`setup-zk.mjs`, adjacent manifest/encoder suites, both workflows,
`docs/contracts/RIGHTS_SCALE_PROFILE.md` IM-16/IM-17 and the historical
[RS-2 record](../2026-10-14-rs-2-private-path/README.md),
[manifest record](../2026-10-21-plan-rs-manifest-offline-regressions/README.md)
and [encoder record](../2026-10-21-plan-rs-zk-encoding-regressions/README.md).

| Requirement | Existing coverage | Classification / gap |
|---|---|---|
| Cached/fresh phase-1 inspection in setup | `setup-zk.mjs` calls `ptauPower` before cache reuse and after phase-1 setup; the RS-2 record documents integration runs | Partially covered: historical artifact-backed integration, no isolated synthetic parser assertions |
| Manifest phase-1 metadata guards | `zk-policy-v2.test.mjs`, cases for `phase1.ptauPower`, `phase1.ptauSha256`, `phase1.source` and capacity boundary | Sufficiently covered for adjacent metadata behavior; preserve and rerun, no `ptauPower` import |
| Little-endian encoders and proof/key bytes | `zk-helpers.test.mjs`, `little` asymmetric/boundary cases and proof/VK serialization | Sufficiently covered for adjacent encoding behavior; preserve and rerun, no `ptauPower` import |
| First/later header traversal, skipped sizes and modulus offsets | No direct parser suite | Not covered |
| Unsigned asymmetric power extraction | No direct parser suite | Not covered |
| Wrong magic, absent header and numeric-read truncations | No direct parser suite | Not covered |
| Ignored version, header size, trailing data and unread later sections | No direct parser suite | Not covered; characterize without inventing validation requirements |
| Dependency-free pre-bootstrap parser invocation | Adjacent suites already run under Node 24 before bootstrap | Not covered for parser; reuse existing workflow environment |
| Documentation indexing | `scripts/check_docs_index.py` and self-test | Sufficiently covered machinery; add this record's link |

## New cases and acceptance mapping

The new `reference/rights_scale/client/ptau-header.test.mjs` imports only
`node:test`, `node:assert/strict` and `ptauPower` from `./zk-helpers.mjs`.
The helper itself imports only Node built-ins; none of its I/O functions are
called. `setup-zk.mjs` is not imported because its top level executes setup.
All fixtures use literal hex fields, opaque modulus markers, `Buffer.from`,
`Buffer.alloc` and `Buffer.concat`. No encoder or duplicated parser computes
expected results. Checked intact controls precede truncations and mutations.
All 34 cases pass, with no failures, cancellations, skips or TODOs.

| Gap / acceptance item | New cases and precise existing result |
|---|---|
| Header first; varying modulus spans | First-section header with n8 = 1, 3 and 32, opaque 0xa5 bytes, literal power `04 03 02 01` returns `0x01020304` in each case |
| Unsigned LE extraction | Zero, `03 02 01 80` returns `0x80010203`, and `ff ff ff ff` returns `0xffffffff`; these powers are never exponentiated |
| Header later / section traversal | Three distinct non-header sections before the header, with 3-byte, zero-byte and 5-byte payloads; additional 257-byte skip with literal LE size `01 01 00 00 00 00 00 00` |
| Skipped-section size controls traversal | A decoy header inside the skipped payload is ignored; changing only that size to zero returns the decoy's distinct `0x0a0b0c0d` |
| Wrong magic | `pTau`, `xxxx`, four zero bytes, empty buffer and 1-/2-/3-byte magic prefixes all throw exactly `PTAU_FORMAT` |
| Missing header | Zero declared sections, complete traversal of two non-header sections, or a readable header outside the declared count throw exactly `PTAU_HEADER_MISSING` |
| Truncated fields actually read | Cuts inside section count, ID, eight-byte size, header n8 and power; absent power after the modulus; cut before completing the declared modulus span. Each selected numeric read throws an actual `RangeError` with `code: ERR_OUT_OF_RANGE`, without asserting Node's offset-dependent prose |
| Unvalidated version / header size / trailing data | Versions zero and all-ones, header size zero/understated/overstated, and appended garbage leave the extracted power unchanged; named characterization cases |
| Early return versus completeness | First of two readable headers wins; truncating the second declared section to one ID byte is ignored because the first header already returned |
| CI integration | Exactly one unconditional `Offline PTAU header parsing regressions` step after the encoder suite and before bootstrap, inheriting existing Node 24; no failure suppression |
| Adjacent coverage / documentation | Existing manifest and encoder suites preserved and rerun; this record linked beside their records in `docs/README.md` |

Complete delivery path list (exactly four):

- `reference/rights_scale/client/ptau-header.test.mjs`
- `.github/workflows/protocol.yml`
- `docs/README.md`
- `validation/2026-10-21-plan-rs-ptau-header-tests/README.md`

## Preservation

| Locked file | Required Git blob | Before / after |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match / match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match / match |

`git hash-object` verified both working-tree files before and after work.
Baseline `reference/v0.3-rc1/` tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
An inline Python/Git audit compared all 906 tracked files outside the delivery
allowlist to their baseline Git blobs: all match, including all 108 files under
`reference/v0.3-rc1/`. The tracked diff plus nonignored untracked list is exactly
the four delivery paths; the Git index is unchanged. Parser/setup implementation,
existing suites, dependency files, contracts, policy values, `.aiops/`, task
documents, historical records and `ktx-kernel.yml` remain byte-identical. No
transient source mutations were used.

PyYAML `BaseLoader` inspection verified that the new workflow step contains only
`name` and `run`, follows the encoder suite, precedes bootstrap and inherits
Node 24. Removing only those two added lines reproduces both the baseline
workflow bytes and parsed structure exactly. Existing action pins, permissions,
timeouts, cache settings, conditions and checks are preserved.

## Commands and actual results

Verification used PATH preferring the already provisioned
`/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin`: Node **24.19.0**, Python **3.12.15**, PyYAML
**6.0.3**, Rust/Cargo **1.98.1**. Initial shell probes found Node 20.19.2 and
Python 3.13.5; those were not used for acceptance checks. No installation,
downloads or background jobs. Rust commands used `CARGO_NET_OFFLINE=true`;
Python verification used `PYTHONDONTWRITEBYTECODE=1`.

The new suite ran first, followed by the existing manifest/encoder suites, then
broader checks. Direct Node suite runs additionally exposed individual case
counts because `node --test` here summarizes files. Local Python/Rust logs are
ignored files in `.local/verification/ptau-header-tests/`, not delivery artifacts.
All verification commands below exited 0; no failed acceptance checks or
implementation fixes occurred.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; baseline and branch as recorded above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before and after |
| `git rev-parse HEAD:reference/v0.3-rc1` | Reference tree recorded above |
| `node --version`; `python3 --version`; `rustc --version`; `cargo --version`; `python3 -c 'import yaml; print(yaml.__version__)'` | Verification versions above; default PATH probes distinguished above |
| `node --test reference/rights_scale/client/ptau-header.test.mjs` | File passes; no failures/cancellations/skips/TODOs |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs reference/rights_scale/client/zk-helpers.test.mjs` | Both file summaries pass; no failures/cancellations/skips/TODOs |
| `node reference/rights_scale/client/ptau-header.test.mjs` | 34 named cases pass |
| `node reference/rights_scale/client/zk-policy-v2.test.mjs` | 267 named cases pass |
| `node reference/rights_scale/client/zk-helpers.test.mjs` | 166 named cases pass |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 129 tests, OK |
| `python3 scripts/verify_runtime_architecture.py` | Architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 78 passed, 0 failed/ignored |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 257 passed, 0 failed/ignored |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Clean, includes kernel |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Clean |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Only local `kix-types` is a normal kernel dependency |
| Inline Python import/fixture audit | Only the allowed three imports; helper imports built-ins; no dynamic import, skip, TODO or only; client `node_modules` absent; artifact directory contains only existing README |
| Inline PyYAML parse and baseline workflow comparison | Exact additive pre-bootstrap step verified; all other workflow bytes and parsed structure preserved |
| Inline Python/Git preservation and four-path allowlist audit | 906 tracked files unchanged outside allowlist, including 108 reference files; index unchanged |
| `git diff --check` | No whitespace errors |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | SHA-256 values below |

```text
a948a1b687de2727ad717db0f7a0aa4159ecf5258e52e18eccf05cc08329d83e  runtime/Cargo.lock
84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f  runtime/crates/kix-kernel/src/lib.rs
d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae  runtime/crates/kix-kernel/tests/transitions.rs
```

Every command in the authoritative `Stdlib offline document checks` workflow
block was extracted unchanged with PyYAML and executed individually. All 26
commands exited 0. Self-tests' corruption diagnostics are expected negative
controls, followed by terminal pass results.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | self-test: pass |
| `python3 scripts/check_docs_index.py` | docs index ok: scanned=194 indexed=159 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | self-test: pass (supplied map and zero-PARTIAL baseline) |

Read-only discovery directory/glob probes returned exit 2 for absent optional
paths while locating tools; these were not acceptance failures. The existing
encoder validation record supplied the provisioned tool paths. No missing
prerequisite, automatic retry or consequential scope expansion was needed.

## AGENTS §8 classification

No explicit contract violation (class C) was found in the inspected IM-16/IM-17
requirements. Parser behavior is source-informed characterization: ignored
version, header-section length, trailing data, opaque modulus bytes and early
return without validating later sections are **class B, contract undefined**.
Custom messages and the selected Node numeric-read errors describe the existing
implementation, not a complete PTAU validation contract. No new format semantics
were invented and no parser hardening was performed. IM-16/IM-17's separate
ceremony/manifest requirements and the prior IM-17 interpretation uncertainty
remain unchanged.

## Non-claims and remaining uncertainty

These small readable buffers are not valid PTAU files, cryptographic material,
ceremony parameters or complete-format validation. This supplements IM-16/IM-17
evidence without closing those predicates or changing evidence grades. No
constraint recount, circuit compilation, bootstrap, ceremony, proving files,
downloads, Move/localnet, testnet/mainnet, external-provider calls or real funds.
Operational depth, K, shard counts and retention remain **UNDETERMINED**, owned
by Astra. No independent cryptographic verification, anonymity, durability,
performance, finality, legal compliance or production-readiness claim.

Exact-final-head KTX CI and KIX protocol CI: run IDs unavailable, status/conclusion
not run. Non-author A2 exact-head review remains required after supervisor
commits. Merge SHA, final-merge lock verification and post-merge main CI are not
applicable. Local completion will not imply merge-ready status.

Local delivery is complete for supervisor review/publication. Remaining work
outside this builder's authorization is supervisor commit/publication,
non-author exact-head review and exact-head hosted CI (including preserved
artifact-backed/chain checks). No merge or GitHub action was performed.
Design deviation: the supervisor network ban overrides the session-start fetch;
cached main freshness remains unverified. Direct Node runs expose case counts;
the 257-byte skip and decoy-header vectors add small traversal probes within the
specified boundary. No other design deviation or decision stop.
