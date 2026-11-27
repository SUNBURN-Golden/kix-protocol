# Offline RS manifest validation regressions

Node: `plan-rs-manifest-offline-regressions`, 2026-10-21. Input: the
supervisor-supplied node specification and read-only design plan in this session;
no issue or `docs/tasks/` document was supplied. Dependencies: `rs-2` and
`plan-rs-witness-ci-wiring`. This is not ASTRA program mode. Audit floor A2;
`astra_gate: None`; `user_merge: False` grants no merge authority.

## Baseline identity

Branch: `agent/kix-plan-rs-manifest-offline-regressions`. Starting HEAD and cached
`origin/main` both equal `8b92eb42353d5ca1058227671b3abda3142643c3`; the initial
worktree was clean, with no local base delta. The supervisor prohibits network
actions, so `git fetch origin main` was not run; remote freshness is unverified.
Implementation/final task head is not assigned: delivery is uncommitted changes
above this baseline, with commits/publication owned by the supervisor. No merge
commit or post-merge evidence exists.

## Coverage recorded before adding tests

Inspected `reference/rights_scale/client/zk-regression.mjs`, the complete
`zk-policy-v2.mjs` / `profile-constants.mjs` import graph, `setup-zk.mjs`, the
[RS-2 record](../2026-10-14-rs-2-private-path/README.md), the
[witness CI wiring record](../2026-10-21-plan-rs-witness-ci-wiring/README.md),
`docs/contracts/RIGHTS_SCALE_PROFILE.md` (IM-16, IM-17, IM-27), and the existing
workflow. The table was written before the new test file.

| Requirement | Prior coverage | Exact existing assertion / gap |
|---|---|---|
| Format, depth, slot bits, profile version mismatches | Sufficiently covered | `zk-regression.mjs` section 1: `v1 manifest refused`, `depth-4 manifest refused`, `slotBits mismatch refused`, `other profile version refused`. Reuse those cases; missing and wrong-type variants are absent. |
| K validity and explicit pin | Partially covered | Section 1: `missing K refused`, `K pin mismatch refused`; other invalid numeric/types and matching pins absent. |
| Phase-1 record | Partially covered | Section 1: `missing phase-1 record refused`; individual hash/source/power guards absent. |
| Both phase-2 contribution counts | Partially covered | Section 1: `missing phase-2 contribution refused` sets spend to zero; other fields/types/ranges absent. |
| Both constraint-count guards | Uncovered | No individual rejection assertions. |
| Capacity boundary | Partially covered | Section 1: `ptau too small for the circuit refused` uses real metadata and power 13; exact arithmetic boundary absent. |
| Three circuit-source hashes | Uncovered | No rejection assertions. |
| Ten artifact hashes | Partially covered | Section 1: `missing artifact hash refused` deletes only `spend_scale.zkey`; remaining paths and malformed values absent. |
| Individual verification-key format guards for both counts | Uncovered | No isolated `VK_FORMAT` assertions. |
| Missing/equal phase-2 points | Partially covered | Section 2: `uncontributed phase-2 key refused` on a real weak mint key; section 3 accepts contributed mint/spend keys. Missing points and numeric canonicalization absent. |
| Standalone execution and explicit CI invocation | Uncovered | Existing regression imports `snarkjs` and artifact-dependent helpers; no standalone manifest suite or CI step. |
| Indexed record | Uncovered for this node | Existing docs-index checker and self-test will be reused. |

## Changed paths and new evidence

- `reference/rights_scale/client/zk-policy-v2.test.mjs`: new Node built-in runner
  suite, using only `node:test`, `node:assert/strict`, `zk-policy-v2.mjs` and
  `profile-constants.mjs`. The validator imports only the constants, which have
  no imports. No package dependencies or artifacts are needed.
- `.github/workflows/protocol.yml`: one `Offline manifest validation regressions`
  step immediately after Node 24 setup and before bootstrap in `rights-scale`.
- `docs/README.md`: link to this record in the October 21 validation index.
- `validation/2026-10-21-plan-rs-manifest-offline-regressions/README.md`: this record.

Every new case is a **source-informed characterization**, not an independent
contract oracle. Fresh synthetic controls precede isolated mutations, and
rejections match the entire existing error message using `assert.throws`.
The fixture hashes are fabricated lowercase hexadecimal strings; counts of 1
and power 4 are arithmetic examples, not recounted circuit measurements or
policy choices. The imported K is explicitly test-only. Keys are guard-compatible
objects with distinct fabricated numeric-string points, not usable verification
keys. No proving artifact was generated or loaded.

| Gap | New named cases / existing rejection |
|---|---|
| Missing/type-invalid format/profile fields | `format`, `depth`, `slotBits`, `profileVersion`: deleted, null, wrong type; `CIRCUIT_MANIFEST_*`. Existing ordinary mismatch cases remain in `zk-regression.mjs`. |
| K ranges and positive controls | Null, string, fraction, zero, negative, NaN, infinities; `CIRCUIT_MANIFEST_ROOT_HISTORY_K`. Positive integer K and matching explicit pins pass. Existing missing-K/pin-mismatch cases remain cited above. |
| Phase-1 subfields | Hash absence/null/length/case/nonhex/number, falsy source, missing/null/string/fraction/nonfinite power; `PHASE1_RECORD_MISSING`. Integer power zero/negative reaches `PTAU_POWER_TOO_SMALL:mint_scale`. |
| Both contribution/count records | Each circuit independently: deleted/null/string/fraction/zero/negative/nonfinite values; `PHASE2_CONTRIBUTION_REQUIRED:<name>` or `CONSTRAINT_COUNT_MISSING:<name>`. |
| Exact capacity boundary | Each circuit independently accepts count 15 at power 4 and rejects 16 with `PTAU_POWER_TOO_SMALL:<name>`, keeping the other circuit valid. |
| All circuit-source hashes | Independently mutate all three source entries; `MISSING_CIRCUIT_HASH:<source>`. |
| All artifact hashes | Independently mutate all ten paths: deleted/null/empty/63-character/65-character/uppercase/nonhex/number; `MISSING_ARTIFACT_HASH:<exact path>`. |
| Missing/null record containers | Phase 1, contributions, constraints, files and circuits reject at the first existing applicable guard. |
| Key format for mint and spend counts | Missing/null/wrong protocol and curve, invalid/mismatched public counts, missing/null/wrong-size IC; `VK_FORMAT`. No array-type rule is invented beyond the existing length guard. |
| Key phase-2 point guards | Both counts: missing/null/false gamma or delta, identical points, numerically equal points in decimal/hex/zero-padded/signed representations; `UNCONTRIBUTED_PHASE2_KEY`. Distinct synthetic points pass. |

The capacity assertion characterizes only the validator predicate
`constraints + 1 <= 2 ** ptauPower`. `setup-zk.mjs` separately accounts for
public inputs. These are not equated, changed or claimed to prove setup validity.

## Preservation

| Locked file | Required Git blob | Before / after |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match / match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match / match |

`git ls-files -s` confirmed the initial index blobs, and `git hash-object`
confirmed working-tree blobs before and after. An inline Python/Git check
compared all 900 tracked files outside the allowed patch to their starting Git
blobs: all match, including 108 files under `reference/v0.3-rc1/` (tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`). The tracked diff plus nonignored
untracked list is exactly the four delivery paths. Implementation, constants,
contracts, package files, decoder files, `.aiops/`, task documents, historical
validation records and `ktx-kernel.yml` are unchanged.

Inline PyYAML `BaseLoader` checks parsed both workflows with literal `on`.
The added step has only `name` and `run`, directly invokes the standalone suite,
and has no suppression/conditional/timeout override. Removing only that step
reproduces the original raw bytes and parsed structure. Every existing check,
timeout, permission, condition, cache and action pin is preserved.

## Commands actually run and results

All commands ran from the repository root. Verification PATH places the existing
`/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin` first: Node **24.19.0**, Python **3.12.15**,
PyYAML **6.0.3**. Cargo/Rust **1.98.1** matches CI. No tool or dependency was
installed. The initial PATH probes found Node 20.19.2 and Python 3.13.5; those
were not used for acceptance checks. Cargo used only cached dependencies with
`CARGO_NET_OFFLINE=true`; no jobs were detached into the background.

The 26 commands from the existing `Stdlib offline document checks` block were
extracted unchanged from the parsed workflow and executed individually, with
stdout/stderr and exit codes captured. The table reports their actual outputs.
All checks below exited 0 unless explicitly described as a discovery probe.

| Command | Version | Exit | Result |
|---|---|---|---|
| `git rev-parse HEAD origin/main` | Git | 0 | Both `8b92eb42353d5ca1058227671b3abda3142643c3`; no local base delta. |
| `git ls-files -s` / `git hash-object` on both locked files | Git | 0 | Required blobs match, before and after. |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs` | Node 24.19.0 | 0 | One passing test-file summary; zero failed, cancelled, skipped or todo. |
| `node reference/rights_scale/client/zk-policy-v2.test.mjs` | Node 24.19.0 | 0 | 267 named cases pass; zero failed, cancelled, skipped or todo. |
| Inline complete import-graph check | Python 3.12.15 | 0 | Exactly the four allowed imports; no dynamic imports or external dependencies. `client/node_modules` is absent; the artifacts directory contains only its existing README. |
| Inline PyYAML parse and baseline workflow comparison | Python 3.12.15 / PyYAML 6.0.3 | 0 | Both workflows parse; step location/keys/command and exact preservation verified. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | Python 3.12.15 | 0 | 129 tests, OK. |
| `python3 scripts/verify_runtime_architecture.py` | Python 3.12.15 | 0 | Architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Python 3.12.15 | 0 | 7 tests, OK. |
| `python3 scripts/check_status_register.py` | Python 3.12.15 | 0 | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Python 3.12.15 | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Python 3.12.15 | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_docs_index.py` | Python 3.12.15 | 0 | docs index ok: scanned=191 indexed=156 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Python 3.12.15 | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Python 3.12.15 | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Python 3.12.15 | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Python 3.12.15 | 0 | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Python 3.12.15 | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Python 3.12.15 | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Python 3.12.15 | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Python 3.12.15 | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Python 3.12.15 | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Cargo/Rust 1.98.1 | 0 | 9 test targets; 78 passed, 0 failed/ignored. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Cargo/Rust 1.98.1 | 0 | 42 test targets; 257 passed, 0 failed/ignored. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Cargo/Rust 1.98.1 | 0 | Clean, no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Cargo/Rust 1.98.1 | 0 | Clean. |
| Inline `git ls-tree -r -z HEAD` / Git-blob comparison and changed-path allowlist | Python 3.12.15 / Git | 0 | 900 excluded tracked files byte-identical, including all 108 reference files; exactly four delivery paths. |
| `git diff --check` | Git | 0 | Clean. |

Discovery probes: an early `rg` search included two nonexistent guessed paths
(`reference/rights_scale/README.md` and `reference/rights_scale/scripts/setup-zk.mjs`)
and exited 2; the actual client setup path was subsequently read. The optional
`printenv NODE_OPTIONS` probe exited 1 because the variable was unset. A compound
absence probe exited 1 because the artifacts directory exists; inspection showed
only the tracked README, with no generated artifacts. These were environment/path
probes, not test failures. No test failure required an implementation fix or retry.

## Classifications, deviations and remaining uncertainty

- **A — matching:** The existing guards reject the documented missing/malformed
  profile and metadata examples and mismatched key formats with their existing
  codes. This evidence concerns guard behavior only; full cryptographic or
  contract completeness is not asserted.
- **B — characterization / undefined:** Numeric bounds and malformed-field
  semantics beyond the implemented guards are not specified here. Source
  inspection shows phase-1 source is checked for truthiness, IC only for length,
  and point strings are converted via `BigInt`; the suite creates no new source
  type, coordinate-shape, curve-membership or JSON-schema rules. Unknown JSON
  fields and malformed coordinate conversion are not assigned new expectations.
  IM-17's ambiguous “other keys” wording remains unresolved, as recorded in
  `docs/status/RS_IM_EVIDENCE_MAP.md`; no contract/evidence grade is changed.
- **C — explicit violation:** None found within this scoped inspection/testing.
- Execution deviation: fetch was omitted under the supervisor's no-network rule;
  local cached main is not claimed remotely fresh. Existing Node 24 / Python 3.12
  binaries were selected instead of default PATH tools. No design-scope deviation.
- Operational values remain **UNDETERMINED**, owned by **Astra**. No policy value,
  new protocol command, ceremony, artifact, secret or runtime change was needed.

## Delivery gates and non-claims

| Required workflow | Exact final head | Run ID | Status / conclusion |
|---|---|---|---|
| KTX kernel verification | Not assigned; supervisor owns commit | unavailable | Not run/observed in this session; no pass claimed. |
| KIX protocol verification | Not assigned; supervisor owns commit | unavailable | Not run/observed in this session; no pass claimed. |
| Post-merge main CI | No merge | unavailable | Not applicable. |

Local implementation and verification are complete for supervisor handoff.
This is **not merge-ready**: both exact-final-head workflows must be
`completed/success`, with A2 non-author exact-head review and human authorization
still required. No commit, push, issue, PR, comment, network action, Ready
transition or merge was performed. Earlier CI cannot transfer to a later head.

Bootstrap, Move, ceremony/proving-artifact generation, `test:zk`, localnet and
chain journeys were not run for this offline node; their existing CI checks
remain intact. The existing dependency-bound witness suite was not rerun.
No cryptographic verification, artifact-byte integrity, curve membership,
ceremony validity, independent contribution, operational readiness, production
durability, finality, real-money/provider behavior, performance or policy
approval is established. No real PG/bank/KYC calls, public endpoints, funds,
testnet/mainnet, storage engine, new coin/TIX module or production runtime was
used. The remaining delivery work belongs to the supervisor/reviewer; unresolved
IM-17 meaning and operational values remain with their existing owners.
