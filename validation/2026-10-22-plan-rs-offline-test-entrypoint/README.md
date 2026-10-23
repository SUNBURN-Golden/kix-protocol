# RS client offline-test entry point

Node `plan-rs-offline-test-entrypoint`, implemented 2026-10-22. Task input:
the supervisor-supplied specification and read-only design plan in this session,
from KIX planner run `1792592950` (`/workspace/kix-run/logs/planner_1792592950`).
This loop-proposed node is not in `.aiops/program.json`; no issue or
`docs/tasks/` document exists for it. This is not ASTRA program mode.
Audit floor A2; `astra_gate: None`; `user_merge: False` grants no merge authority.

Dependencies and predecessor evidence:

- [plan-rs-witness-ci-wiring](../2026-10-21-plan-rs-witness-ci-wiring/README.md)
- [plan-rs-manifest-offline-regressions](../2026-10-21-plan-rs-manifest-offline-regressions/README.md)
- [plan-rs-zk-encoding-regressions](../2026-10-21-plan-rs-zk-encoding-regressions/README.md)
- [plan-rs-spend-witness-offline-tests](../2026-10-21-plan-rs-spend-witness-offline-tests/README.md)
- [plan-rs-ptau-header-tests](../2026-10-21-plan-rs-ptau-header-tests/README.md)

The [original reconstruction record](../2026-10-21-plan-rs-witness-offline-regressions/README.md)
and the wiring/spend records correctly describe the broken package entry point
at their historical snapshots. They are preserved unchanged.

## Identity and delivery boundary

- Branch: `agent/kix-plan-rs-offline-test-entrypoint`; starting worktree clean.
- Starting HEAD, local base and cached `origin/main` all equal
  `a2a2e29ceefd50952454c6b378363b31be84c3b4`. No local base delta.
  `git fetch origin main` was not run because the supervisor explicitly
  prohibits all network actions. Remote freshness is unverified.
- Implementation head and exact final task head: unassigned. This delivery is
  an uncommitted working-tree patch above the starting HEAD; the supervisor
  owns commits and publication. HEAD is not a commit containing this patch.
- No merge commit, final-merge lock check or post-merge main CI is applicable.

Exactly three delivery paths:

1. `reference/rights_scale/client/package.json` — only `scripts["test:offline"]`.
2. `validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md` — this record.
3. `docs/README.md` — one relative link in a dated validation-index section.

The new script is exactly:

```text
node --test zk-policy-v2.test.mjs zk-helpers.test.mjs ptau-header.test.mjs witness-reconstruction.test.mjs spend-witness.test.mjs
```

It replaces `node --test offline.test.mjs`, whose target does not exist.
Explicit filenames run relative to the package directory. No glob, wrapper,
lifecycle hook, conditional skip, retry or failure suppression is introduced.

## Existing coverage mapping

| Acceptance requirement | Coverage before this patch | Change / verification |
|---|---|---|
| npm offline entry executes the five suites | **Not covered**: missing `offline.test.mjs` target | Replace only the script; run the exact offline acceptance command. |
| Fresh named-case execution separate from file totals | **Partially covered** by historical predecessor counts | Direct-file runs expose fresh case totals, including nested spend cases. |
| Each existing direct suite command remains green | **Sufficiently covered** by the five existing test files below | Reuse all suites unchanged; run each with `node --test` and directly with `node`. |
| Manifest/key policy guards | **Sufficiently covered**: `zk-policy-v2.test.mjs` | Existing synthetic metadata characterization, no new test. |
| Public-byte encodings | **Sufficiently covered**: `zk-helpers.test.mjs` | Existing fabricated-coordinate encoding characterization, no new test. |
| PTAU header reads | **Sufficiently covered**: `ptau-header.test.mjs` | Existing synthetic-buffer parser characterization, no new test. |
| Event reconstruction and read allowlist | **Sufficiently covered**: `witness-reconstruction.test.mjs` | Existing injected event/object-read fixtures, no decoder added. |
| Spend witness guards, indices, context and non-mutation | **Sufficiently covered**: `spend-witness.test.mjs` | Existing source-informed construction checks, no proof generation. |
| Dependency/lock preservation | **Partially covered**: existing pins; patch-specific preservation needed | Compare parsed manifest excluding only the script, lock bytes and textual diff. |
| Documentation indexing | **Sufficient existing checker machinery** | Add the exact-file link; run checker and self-test. |

Suite paths above are relative to `reference/rights_scale/client/`. New tests:
none. The new evidence fills the package-entry execution and fresh preservation
gaps without duplicating test coverage.

## Environment and offline prerequisites

All checks run from the repository root. PATH prefers the existing
`/workspace/toolchain/node-v24.19.0-linux-x64/bin` and
`/workspace/venvs/film312/bin`. Actual versions: Node **24.19.0**, npm **11.21.0**,
Python **3.12.15**, rustc **1.98.1** (`48a229cea`, 2026-09-01), Cargo **1.98.1**
(`797e8a9bc`, 2026-08-05). Python verification uses
`PYTHONDONTWRITEBYTECODE=1`; Cargo uses `CARGO_NET_OFFLINE=true`.

The worktree initially lacked `node_modules`. Before the script edit, `cmp`
confirmed that both package manifests and lockfiles matched the existing
installation source:
`/workspace/kix-run/wt/plan-rs-witness-offline-regressions/reference/rights_scale/client/`.
`cp -a` copied only that installation into this worktree's ignored client
`node_modules/`. An inline Python comparison verified all 147 installed package
versions and their `.package-lock.json` version/resolved/integrity fields
against the unchanged repository lockfile, with identical package sets.
No install, download, bootstrap, credentials or proving artifacts were needed.
Ignored logs and preservation snapshots are under
`.local/verification/offline-test-entrypoint/`; they are local scratch evidence,
not delivery paths. No background jobs were launched.

## Commands and actual results

All commands below ran in the root working directory, with the environment
above. Narrow npm/suite runs preceded broader verification. `node --test` on
this Node toolchain reports test files as tests; those totals are distinct from
the named cases exposed by direct `node` runs.

| Command | Exit | Actual result |
|---|---|---|
| `git status --short`; `git rev-parse HEAD origin/main`; `git branch --show-current` | 0 | Initially clean; baseline and branch as above. |
| `node --version`; `npm --version`; `python3 --version`; `rustc --version`; `cargo --version` | 0 | Versions above. |
| `cmp` of `package.json` and `package-lock.json` against the dependency source before edit | 0 | Both byte-identical. |
| `cp -a` cached `node_modules` into the ignored client directory; inline installed-package comparison | 0 | 147 installed packages match lock metadata and versions. |
| Inline Python/Git baseline byte audit (`git ls-tree -r -z HEAD`, Git blob calculation, SHA-256 snapshot); `git rev-parse HEAD:reference/v0.3-rc1` | 0 | All 911 tracked files match starting HEAD; both locked blobs match; 108 physical reference files snapshotted; reference tree below. |
| `npm --offline --prefix reference/rights_scale/client run test:offline` | 0 | All five named files pass; runner: 5 tests, 5 pass, 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 1 file passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/zk-policy-v2.test.mjs` | 0 | 267 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/zk-helpers.test.mjs` | 0 | 1 file passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/zk-helpers.test.mjs` | 0 | 166 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/ptau-header.test.mjs` | 0 | 1 file passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/ptau-header.test.mjs` | 0 | 34 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | 1 file passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/witness-reconstruction.test.mjs` | 0 | 16 named cases pass; 0 failures/cancellations/skips/TODOs. |
| `node --test reference/rights_scale/client/spend-witness.test.mjs` | 0 | 1 file passes; 0 failures/cancellations/skips/TODOs. |
| `node reference/rights_scale/client/spend-witness.test.mjs` | 0 | 23 named cases pass (7 top-level plus 16 nested); 0 failures/cancellations/skips/TODOs. |

The following are the closest applicable offline workflow equivalents from
the inspected `protocol.yml` and `ktx-kernel.yml`. All exited 0; no failed
acceptance check required an implementation fix or rerun.

| Command | Exit | Actual result |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=196 indexed=161 allowlisted=35. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | 0 | Self-test: pass; all seven expected corruption diagnostics detected. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 129 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | 0 | Architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_runtime_architecture.py` | 0 | 7 tests, OK. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 9 test targets, 78 passed, 0 failed/ignored/filtered. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 42 test targets, 257 passed, 0 failed/ignored/filtered. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Clean, includes kernel; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Clean. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | Only local `kix-types` is a normal kernel dependency. |
| Inline Python log audit of all ten direct-suite logs and Cargo summaries | 0 | Runner/case totals above confirmed separately; all failure/cancellation/skip/TODO fields zero; spend has 7 top-level and 23 total named results. |
| Inline Python/Git final byte and three-path audit; parsed-manifest and exact textual replacement comparison | 0 | 909 excluded tracked files preserved, all 108 physical reference files byte-identical, both locked blobs match, dependencies/lock unchanged; exact three delivery paths. |
| `git diff --check`; `git diff --stat`; `git diff -- reference/rights_scale/client/package.json docs/README.md` | 0 | No whitespace errors; single script-field edit and dated index addition inspected. New untracked record included separately in the three-path audit. |
| `git rev-parse HEAD origin/main` (final identity check) | 0 | Both remain the starting SHA; no commit performed. |

## Preservation

| Locked file | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

Starting `reference/v0.3-rc1` tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b` (108 files).
Before/after package-lock SHA-256 (unchanged):
`b9f24ad565960f4ded378965c1408e827b8f573b2237ca1a96bc137db16fac6c`.

The final audit compares calculated Git blobs against the initial clean
snapshot and HEAD. All 909 tracked files outside the three-path allowlist match;
the full physical reference-tree SHA-256 mapping matches, with no added or
deleted files. This preserves `.aiops/**`, `docs/tasks/**`, both workflows,
all existing suites/helpers, historical validation records and all other
tracked files. The tracked diff plus nonignored untracked file list is exactly
the three delivery paths above.

Excluding only `scripts["test:offline"]`, parsed package objects are identical.
An exact byte replacement comparison also confirms that every other manifest
byte is preserved. The Node engine remains `>=24 <25`; pins remain
`@mysten/sui` 2.30.0, `circomlib` 2.0.5, `circomlibjs` 0.1.7, `snarkjs` 0.7.5
and development dependency `circom2` 0.2.22. The lockfile is byte-identical.

## Discrepancies, deviations and limits

The predecessor's class-B broken-entry characterization is addressed only at
the developer package entry point. No explicit protocol contract violation or
new contract-undefined behavior was found. Existing source-informed parser,
encoder and manifest characterizations remain characterizations, not newly
defined contracts. Shared Poseidon provenance, real-object-decoder and
transport-completeness limits and the IM-19 gate-secret assertion gap remain.
Operational depth, root-history K, shard counts and retention stay
**UNDETERMINED** with their existing owners (Astra); no product policy is chosen.

The fetch omission is a deviation from AGENTS.md §1 required by the explicit
supervisor network ban. Reusing cached dependencies and the provisioned
toolchains follows the design. No implementation scope deviation or decision
stop was needed. A read-only discovery command tried nonexistent
`.github/workflows/ktx.yml` (exit 1); the actual `ktx-kernel.yml` was then read.
This was not a failed verification command or a CI change.

Workflow definitions were inspected. The five direct Node suite invocations,
rights-scale Python tests, architecture gate and offline Rust checks are local
equivalents of applicable portions of `protocol.yml` / `ktx-kernel.yml`.
Bootstrap, Sui/Move, localnet, setup/proving and storage probes are excluded by
this task and were not run. Local success establishes the repaired entry point
only, not localnet, cryptographic, operational or production qualification.
No independent cryptographic verification, complete PTAU validation, durability,
distributed fencing, bank exactly-once, chain finality, performance/SLO or legal
compliance claim is made. No tests, dependencies, decoder, workflows, contracts,
protocol command, storage engine or production runtime are added or changed.

## Delivery gates

| Gate | Exact final head / run ID | Status / conclusion |
|---|---|---|
| KTX kernel verification | Unassigned / unavailable | Not run or observed here; no pass claimed. |
| KIX protocol verification | Unassigned / unavailable | Not run or observed here; no pass claimed. |
| A2 non-author exact-head review | Supervisor's future committed head | Not performed by this builder. |
| Merge / post-merge main CI | No merge SHA / no run ID | Not applicable; no merge authorized or performed. |

The supervisor owns commit/publication and subsequent exact-head review/CI.
Both workflows must be completed/success for the actual final head before
merge readiness. Local delivery readiness does not establish merge readiness;
prior-head CI does not transfer. No commit, push, PR, issue, comment, tag or
branch mutation was performed. No ASTRA markers were posted.
