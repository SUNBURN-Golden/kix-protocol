# Offline RS event-source regressions

Node `plan-plan-rs-event-source-offline-tests`, 2026-10-22. Task input is the
supervisor-supplied specification and design plan in this session (planner run
`1792624655`); no issue or `docs/tasks/` file exists. Not ASTRA program mode.
Dependencies: [rs-2](../2026-10-14-rs-2-private-path/README.md),
[witness regressions](../2026-10-21-plan-rs-witness-offline-regressions/README.md),
and [offline entrypoint](../2026-10-22-plan-rs-offline-test-entrypoint/README.md).
Audit floor A2; no merge authority.

## Identity

Branch `agent/kix-plan-plan-rs-event-source-offline-tests` started clean.
Starting HEAD/base and cached `origin/main` are both
`93cec6aaf12f22bf8aefc0453fe545b6bd38b819`; no local delta. Fetch was omitted
because the supervisor prohibits network actions; remote freshness is unverified.
Implementation and final task commit SHAs are unassigned: the supervisor owns
commits/publication, and starting HEAD does not contain this working-tree patch.
No merge, final-merge blob check or post-merge CI applies.

## Coverage mapped before adding tests

Paths below are under `reference/rights_scale/client/` unless stated otherwise.

| Requirement | Prior coverage classification and exact evidence | Gap / planned test |
|---|---|---|
| Reconstruction guards and object-read allowlist | Sufficiently covered: `witness-reconstruction.test.mjs` (`empty_tree`, `populated_tree`, `missing_note_index`, root/count rejection cases) injects `source.events` | Reuse unchanged; readers are bypassed. |
| JSON-RPC type filters, ascending order, cursor forwarding, terminal pages, BCS/digest/sequence preservation | Not covered deterministically: reconstruction suite bypasses `jsonRpcEventSource` | `jsonrpc_pages_preserve_records`, `jsonrpc_empty_result`. |
| Checkpoints from zero through height, including empty checkpoints | Not covered deterministically; historical RS-2 reader use only | `checkpoint_traverses_advertised_height`. |
| Transaction-local event sequences and package/module/name filtering | Not covered offline | `checkpoint_filters_without_renumbering`. |
| Repeated reads, event-name switching, newly appended checkpoints once | Not covered deterministically; incremental implementation exists | `checkpoint_reuses_history_and_appends_once`. |
| Equivalent histories through both readers | Partially covered: `private-localnet.mjs::eventsView` and historical RS-2 record | `sources_project_equivalent_histories`, explicit expected ordered records. |
| Separate-instance isolation | Not covered offline | `source_instances_are_isolated`. |
| Fail-closed transport and zero retries | Not covered for these readers | Scoped SDK/ledger stubs, network/timer guards, exact request logs, zero retry counters. |
| Offline registration, additive CI, bounded evidence | Partially covered by existing five-suite entrypoint and workflow/checkers | Add sixth suite and one workflow invocation; run Node 24 and document checks. |

This table was written before the new test file. These are source-informed
synthetic reader tests supporting blueprint §5.6(4), RR-4 and IM-19, not new
reconstruction tests or independent cryptographic verification.

## Execution and preservation

Exactly seven delivery paths:

1. `reference/rights_scale/client/event-sources.test.mjs` — seven sequential
   named reader cases inside one containing test; scoped guards precede dynamic
   SDK/reader imports, and all mocks are restored on teardown, including failure.
2. `reference/rights_scale/client/package.json` — append the new suite to the
   explicit `test:offline` list, preserving the five existing suites.
3. `.github/workflows/protocol.yml` — one direct invocation after offline spend
   tests and existing dependency installation, before Move/localnet/proving.
4. `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` — supplemental RR-4 reading note.
5. `docs/status/RS_IM_EVIDENCE_MAP.md` — supplemental IM-19 reading note.
6. `validation/2026-10-22-plan-plan-rs-event-source-offline-tests/README.md` — this record.
7. `docs/README.md` — exact-file relative validation link.

### Environment and dependency provenance

All acceptance commands ran from the repository root with PATH preferring the
already provisioned `/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin`. Versions: Node **24.19.0**, npm **11.21.0**,
Python **3.12.15**, rustc **1.98.1** (`48a229cea`, 2026-09-01), Cargo **1.98.1**
(`797e8a9bc`, 2026-08-05). Initial default Node was 20.19.2; no acceptance test
used it. Python commands suppress bytecode writes; Cargo network access is
disabled. No bootstrap, install, downloads, listeners or background jobs ran.

The client initially had no `node_modules`. Before editing the manifest,
`cmp` confirmed its manifest and lockfile matched the existing installation in
`/workspace/kix-run/wt/plan-rs-offline-test-entrypoint/reference/rights_scale/client/`.
Only that installation's ignored `node_modules` was copied into this worktree.
An inline Python audit verified identical installed/locked package sets and
all **147** versions plus resolved/integrity metadata against the unchanged
lockfile. No proof artifacts were copied. Ignored scratch logs and the initial
byte snapshot live under `.local/verification/event-sources/`.

### Commands actually run

Narrow reader execution preceded the full offline entrypoint, then document,
Python/architecture and workspace verification. Every check below exited 0;
no acceptance failure required a fix or test rerun. `node --test` on the
provisioned toolchain reports files as tests. The direct-file invocation exposes
the named cases separately: seven reader cases plus their containing test.

| Command | Exit | Actual result |
|---|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | 0 | Initially clean; branch and equal local SHAs as above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | 0 | Both required blobs match before edits; final audit also matches. |
| `node --version`; `npm --version`; `python3 --version`; `rustc --version`; `cargo --version` | 0 | Versions above (initial default Node recorded separately). |
| Inline Python/Git baseline byte audit (`git ls-tree -r -z HEAD`, calculated Git blobs, physical SHA-256 reference snapshot); `git rev-parse HEAD:reference/v0.3-rc1` | 0 | 912 tracked files match starting HEAD; 108 physical reference files; tree below. |
| `cmp` manifest and lockfile against the cached dependency source; `cp -a` its `node_modules`; inline Python installed-package comparison | 0 | Both files identical before edit; 147 package versions and lock metadata match. |
| `node --test reference/rights_scale/client/event-sources.test.mjs` | 0 | 1 file passes, 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/event-sources.test.mjs` | 0 | All 7 named reader cases and containing test pass (8 reported tests); 0 failures/cancellations/skips/TODOs; all guarded attempts and source retry counts zero. |
| `npm --offline --prefix reference/rights_scale/client run test:offline` | 0 | All 6 explicit files pass; 6 reported tests, 0 failures/cancellations/skips/TODOs. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | 0 | scanned=197 indexed=162 allowlisted=35; also rerun after final record update. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | 0 | Pass; 7 expected corruption diagnostics. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py` | 0 | 23/23 rows, 168 citations; counts unchanged. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | Pass; all 13 expected corruptions detected. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py` | 0 | 30/30 rows, 179 citations; counts unchanged. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | Pass; all 15 expected corruptions detected. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py` | 0 | blueprint=47 profile=47 expected=47. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | Pass; all 7 expected corruptions detected. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py` | 0 | paths=300 ev_ids=15 original32=32. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py --self-test` | 0 | Pass; all 4 expected corruptions detected. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 129 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | 0 | Architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_runtime_architecture.py` | 0 | 7 tests, OK. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 42 test targets, 257 passed; 0 failed/ignored/measured/filtered, including the kernel. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Clean, no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Clean. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | Only local `kix-types` is a normal kernel dependency. |
| Inline Python/Git final byte/path audit; parsed-manifest comparison; exact additive workflow comparison; pre-reading-note map comparison; Cargo log summary audit | 0 | Exactly 7 delivery paths; 907 other tracked files and all 108 physical reference files unchanged; manifest only appends suite; CI only adds its invocation; map tables/counts identical; Cargo totals confirmed. |
| `git diff --check`; `git diff --stat`; `git diff -- .github/workflows/protocol.yml reference/rights_scale/client/package.json`; final `git status --short`; `git rev-parse HEAD origin/main` | 0 | No whitespace errors; additive wiring inspected; SHAs remain starting SHA, no commit. Untracked suite and validation record are included in the 7-path audit. |

The inspected workflows are `protocol.yml` (`rights-scale` and protocol
document/architecture/workspace steps) and `ktx-kernel.yml`. Workspace testing
includes the kernel; workspace Clippy includes its all-targets check. These are
the closest applicable offline equivalents, not a full hosted workflow run.
Bootstrap, Move/localnet journeys and proving/ceremony steps were not run:
this node authorizes synthetic offline reader coverage without chain or proof
artifacts. Existing CI steps, dependencies, timeout and conditions are preserved.

### Protected bytes

| Locked path | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

Before work all 912 tracked files matched HEAD. After work all 907 tracked files
outside the five edited tracked paths still match, including readers, retry
logic, decoders, journey comparators, existing tests, contracts, lockfiles,
`.aiops/**`, `docs/tasks/**` and the kernel locks. The two new files complete the
seven-path allowlist. The physical reference snapshot matches in full (108
files, no additions/deletions), with unchanged `reference/v0.3-rc1` Git tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Package-lock SHA-256 remains
`b9f24ad565960f4ded378965c1408e827b8f573b2237ca1a96bc137db16fac6c`.

## Discrepancies and deviations

The scoped valid fixtures match the specified reader behavior (class A); no
explicit contract violation was found. No new class-B undefined semantics are
asserted or relied on. Malformed responses/types, sequence values outside the
safe integer range, retry-on-error behavior and counter isolation after nonzero
retries remain untested. The serialized roots are synthetic values; no root
reconstruction/acceptance or event-decoder coverage is claimed by this suite.

No implementation/design scope deviation was needed. Execution deviations:
the explicit supervisor network ban overrides the initial fetch requirement;
cached dependencies were verified and copied locally instead of installing.
The specification supplied in this session is the task input; no task document
or issue was created. No commit, push, PR, issue, comment, CI dispatch, host
change or approval flow was performed.

## Limits and remaining gates

Evidence is synthetic reader coverage, not live transport completeness,
finality, public-tree retention, proof verification, operational acceptance or
production readiness. No network, chain, credentials, proof artifacts or host
changes are used. Policy values remain UNDETERMINED with their existing owners;
RR-4 stays COVERED_LOCALNET and IM-19 stays PARTIAL, including its gate-secret
assertion gap. A2 non-author exact-head review and both required exact-head
workflows remain supervisor delivery gates; no run IDs or conclusions are
observed here. Local results do not replace them.

| Required external evidence | Run ID | Status / conclusion |
|---|---|---|
| KTX kernel verification at final task head | unobserved | Pending supervisor commit/publication and exact-head verification. |
| KIX protocol verification at final task head | unobserved | Pending supervisor commit/publication and exact-head verification. |
| Post-merge main CI | not applicable | No merge performed or authorized in this session. |

Builder state: READY for supervisor review/commit, not a merge-ready verdict.
Remaining follow-up candidates are live transport/retention evidence and the
existing owner-policy and gate-secret gaps; none is resolved by these tests.
