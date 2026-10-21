# Offline witness reconstruction CI wiring

Node: `plan-rs-witness-ci-wiring`, implemented 2026-10-21. Task input: the
supervisor-supplied node specification and read-only design plan in this session;
no issue or `docs/tasks/` document was supplied. Dependency:
`plan-rs-witness-offline-regressions` (the unchanged suite and its
[original execution record](../2026-10-21-plan-rs-witness-offline-regressions/README.md)).
This is not ASTRA program mode. Audit floor: A2; `astra_gate: None`;
`user_merge: False` grants no merge authority.

## Identity and base

- Branch: `agent/kix-plan-rs-witness-ci-wiring`.
- Starting HEAD and cached `origin/main`:
  `45ec626e2ffcd1cd47aa982622877873b5297139`; the starting worktree was clean.
  There is no local base delta. The supervisor prohibits all network actions,
  so `git fetch origin main` was not run. Remote freshness is unverified
  (the session instruction overrides AGENTS.md §1 step 1).
- Implementation/final task head: not assigned in this session; these are
  uncommitted working-tree changes above that starting HEAD. The supervisor
  owns commits, pushes and GitHub publication. No merge commit or post-merge
  result exists for this delivery.

## Changed paths

- `.github/workflows/protocol.yml` — one unconditional step in `rights-scale`,
  immediately after locked dependency installation, before Move/model tests,
  localnet and proving artifacts.
- `docs/README.md` — link to this subsequent CI-wiring record; preserve the
  predecessor entry as its historical snapshot.
- `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` — only the supplemental RR-4
  CI-discovery reading note.
- `docs/status/RS_IM_EVIDENCE_MAP.md` — only the supplemental IM-19
  CI-discovery reading note.
- `validation/2026-10-21-plan-rs-witness-ci-wiring/README.md` — this record.

## Preservation checks

The two locked blobs were verified in the index and working tree before and
after work:

| File | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

The initial diff against HEAD was empty for `runtime/`, `reference/`, `.aiops/`,
`docs/tasks/` and `ktx-kernel.yml`. After implementation and tests, an inline
Git-blob comparison verified all 897 tracked files outside the allowed patch
against starting HEAD, including all 108 files in `reference/v0.3-rc1/` (tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`). The combined tracked diff and
nonignored untracked list contains exactly the five delivery paths above.
Each map has exactly one changed line: its designated supplemental reading note.
Historical validation records, all structured map rows/counts/gaps/owners,
contracts, client code, package scripts/manifests/lockfiles and checker sources
are excluded from the patch. RR-4 remains `COVERED_LOCALNET`, IM-19 remains
`PARTIAL`, and public-tree retention and operational parameters remain
`UNDETERMINED`, owned by Astra.

## Existing coverage mapping

| Requirement / existing evidence | Coverage before wiring | Change / remaining gap |
|---|---|---|
| `reference/rights_scale/client/witness-reconstruction.test.mjs`: empty/populated trees, ordering/show filtering, maximum revoked generation, index/root/count rejection, named NoteTree/RevocationState read allowlist | Sufficiently covered by existing offline regressions | Reuse unchanged; no new tests, scripts or dependencies. |
| Explicit workflow invocation of that suite | Not covered | Dedicated `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` step under existing Node 24 setup, after bootstrap. |
| Broader IM-19 obligations | Partially covered | Gate-secret assertion, real object BCS decoding and transport completeness remain untested by this suite. |
| Documentation consistency | Sufficient existing verification machinery | Reuse all workflow document checkers and their self-tests unchanged. |

## Commands actually run and actual results

All working directories are the repository root. Node 24 is
`/workspace/toolchain/node-v24.19.0-linux-x64/bin/node` (v24.19.0); the default
PATH node is v20.19.2 and was not used for the regressions. Python checks use
`/workspace/venvs/film312/bin/python3` (3.12.15), with PyYAML 6.0.3 for parsing.
The default Python is 3.13.5 and has no PyYAML; that discovery probe failed
with `ModuleNotFoundError`, then the existing Python 3.12 environment was used.
Rust/Cargo are 1.98.1, matching CI. Cargo runs with `CARGO_NET_OFFLINE=true`.

The existing `node_modules` from the dependency node's worktree was copied
locally (ignored build input); `cmp` confirmed its package manifest and lockfile
are byte-identical to this worktree's. No download or bootstrap was run.
For the table below, the reused dependency worktree is
`/workspace/kix-run/wt/plan-rs-witness-offline-regressions`. Python commands ran
with `/workspace/venvs/film312/bin` first on PATH and
`PYTHONDONTWRITEBYTECODE=1`.
Commands in the `Stdlib offline document checks` block were extracted unchanged
from the parsed workflow and run individually with their exit codes checked;
the six narrow checker commands ran first, followed by the remaining twenty.

| Command | Tool version | Exit | Actual result |
|---|---|---|---|
| `git rev-parse HEAD` / `git rev-parse refs/remotes/origin/main` | Git | 0 | Both `45ec626e2ffcd1cd47aa982622877873b5297139`. |
| `node --version` / `python3 --version` (initial default PATH probes) | Node 20.19.2 / Python 3.13.5 | 0 | Located defaults; switched to existing Node 24 and Python 3.12 for verification. |
| `python3 -c 'import yaml; print(yaml.__version__)'` (initial default PATH probe) | Python 3.13.5 | 1 | PyYAML unavailable in default Python; used existing Python 3.12/PyYAML environment. |
| `git ls-files -s` and `git hash-object` on both locked files | Git | 0 | Required blobs match before and after work. |
| `cmp reference/rights_scale/client/package-lock.json /workspace/kix-run/wt/plan-rs-witness-offline-regressions/reference/rights_scale/client/package-lock.json` | system `cmp` | 0 | Lockfile identical. |
| `cmp reference/rights_scale/client/package.json /workspace/kix-run/wt/plan-rs-witness-offline-regressions/reference/rights_scale/client/package.json` | system `cmp` | 0 | Manifest identical; existing dependencies reused. |
| `node --version` (Node 24 PATH) | Node 24.19.0 | 0 | `v24.19.0`. |
| `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` | Node 24.19.0 | 0 | One test-file pass, zero failures, zero skipped in the runner summary. |
| `node --test --test-reporter=tap reference/rights_scale/client/witness-reconstruction.test.mjs` | Node 24.19.0 | 0 | TAP confirms one passing file-level subtest, zero failures/skips. |
| `node reference/rights_scale/client/witness-reconstruction.test.mjs` | Node 24.19.0 | 0 | All 16 named cases pass; zero failures/skips. |
| Inline PyYAML `BaseLoader` parse of `protocol.yml` and `ktx-kernel.yml`, plus baseline comparison | Python 3.12.15 / PyYAML 6.0.3 | 0 | Both parse with literal `on`; exact step/Node 24/order/root cwd/no suppression asserted. Removing only the addition reproduces the baseline parsed structure and raw bytes. |
| `python3 scripts/check_docs_index.py` | Python 3.12.15 | 0 | scanned=190 indexed=155 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Python 3.12.15 | 0 | rows=23 citations=168; COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` | Python 3.12.15 | 0 | rows=30 citations=179; COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | Python 3.12.15 | 0 | 129 tests, OK. |
| `python3 scripts/verify_runtime_architecture.py` | Python 3.12.15 | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Python 3.12.15 | 0 | 7 tests, OK. |
| `python3 scripts/check_status_register.py` | Python 3.12.15 | 0 | paths=300 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_rs_profile_traceability.py` | Python 3.12.15 | 0 | blueprint=47 profile=47 expected=47. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_read_model_source_map.py` | Python 3.12.15 | 0 | queries=13 anchors=128 catalogues=2 citations=145. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_i12_proof_ids.py` | Python 3.12.15 | 0 | proof_headings=4 proof_keys=10 pack_keys=14 expected=14. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_delegation_layer_matrix.py` | Python 3.12.15 | 0 | rows=36 citations=79; MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Python 3.12.15 | 0 | rows=49 citations=58; HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_contract_error_codes.py` | Python 3.12.15 | 0 | rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_adapter_identity_map.py` | Python 3.12.15 | 0 | rows=17 citations=56; CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Python 3.12.15 | 0 | rows=10 citations=77; TESTED=6 STOPPED=4 OPEN=0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `python3 scripts/check_readiness_evidence_map.py` | Python 3.12.15 | 0 | rows=36 citations=177; EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Python 3.12.15 | 0 | self-test: pass. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Cargo/Rust 1.98.1 | 0 | 9 test targets, 78 tests passed, 0 failed/ignored. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Cargo/Rust 1.98.1 | 0 | 42 test targets, 257 tests passed, 0 failed/ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Cargo/Rust 1.98.1 | 0 | Clean; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Cargo/Rust 1.98.1 | 0 | Clean. |
| Inline `git ls-tree -r -z HEAD` / Git-blob byte comparison and map-line comparison | Python 3.12.15 / Git | 0 | 897 excluded tracked files byte-identical; exactly five delivery paths; only designated map notes changed. |
| `git diff --check` | Git | 0 | Clean. |

No test failure required an implementation fix or retry. The default Node
24.19.0 `--test` report aggregates this run as one passing file; the direct-file
diagnostic separately showed all sixteen named cases passing. These are the
actual local summaries, not an inferred CI test count.

## Local execution versus exact-head CI

The protocol workflow now explicitly discovers the suite. The new step has only
`name` and `run`: no `if`, `continue-on-error`, pipeline, error wrapper or retry.
Its direct command propagates a nonzero exit through normal Actions behavior.
Existing job conditions, timeout, permissions, action pins, caches and all
existing checks remain intact. YAML parsing and local execution are not Actions
execution evidence. Preserved table cells and earlier records saying neither
workflow invokes the file describe the preceding snapshot.

| Required workflow | Exact final head | Run ID | Status / conclusion |
|---|---|---|---|
| KTX kernel verification | Supervisor has not committed final head | unavailable | Not run/observed here; no pass claimed. |
| KIX protocol verification | Supervisor has not committed final head | unavailable | Not run/observed here; no pass claimed. |

This workflow change is not documentation-only. Both exact-head workflows must
be `completed/success` before merge readiness; earlier-head success cannot
transfer. A2 non-author exact-head review and human merge authorization remain
delivery gates. Final-head CI evidence belongs in the authorized handoff report,
not another repository revision solely to record the previous head's CI.

## Discrepancies, deviations and non-claims

- No contract violation or newly undefined contract behavior was found. The
  predecessor's class-B characterization of the broken `test:offline` package
  script remains unresolved and unchanged; it was not invoked.
- The fetch restriction, reused installed dependencies and external existing
  Python 3.12 environment are execution-environment deviations, not scope
  changes. The design's five-path patch and all exclusions are preserved.
- The suite uses synthetic events and injected parsed-field projections, with
  shared circomlibjs Poseidon provenance. This is no independent cryptographic
  verification, real object decoder or transport-completeness result. The
  IM-19 gate-secret assertion gap remains.
- No RPC, chain, credentials or proving artifacts are required by the command.
  No Sui, Move, localnet or ZK ceremony was run here. Full bootstrap and the
  localnet/proving workflow steps were not run: they are unchanged and outside
  this offline wiring check, and bootstrap performs prohibited downloads and
  installs into the preserved reference tree.
- No production, production durability, chain finality, legal compliance,
  load-measurement, SLO or operational activation claim is added. No policy
  value, protocol command, storage engine, permission or production runtime
  change is needed or made.
- Local completion is a handoff to the supervisor, not merge readiness. No
  commit, push, issue, PR, comment, tag, branch mutation or merge was performed.
