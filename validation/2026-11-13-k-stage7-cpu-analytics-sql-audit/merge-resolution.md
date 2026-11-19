# Merge-round conflict resolution and local checks (2026-11-14)

Supervisor-initiated `git merge origin/main` into
`agent/kix-k-stage7-cpu-analytics-sql-audit`. This record covers only the merge
round; the earlier builder sessions' evidence in this directory is unchanged
and remains historical.

- Merge base: `f52c58743b2919cbc66ab9c2760ecc76742faca7` (PR #446 merge).
- Node HEAD (first parent): `298e1e8cbe151a0aeefa7a63cbeb66ed22b24092`.
- `origin/main` / MERGE_HEAD (second parent): `1e402787dd44300cf278adcd3eb70d7f5d2ae507`
  (includes node merges #447–#450). Cached ref; no fetch (supervisor prohibits
  network), remote freshness unverified.
- The merge commit itself is made by the supervisor; no commit, push, PR or
  comment was performed by this session.

## Conflict and resolution

Exactly one conflicted path: `docs/README.md` (both-modified, end-of-file
append clash after the `2026-11-12 authenticated export` section). All other
paths auto-merged.

Resolution kept both sides' intent:

- main's two new sections (`2026-11-13 economics-to-credit consumer vectors`,
  `2026-11-13 Capital companion rejection vectors`) stay verbatim in main's
  order, as do main's two non-conflicting additions (the consumer-binding CI
  wiring paragraph near the top and the receipt-goldens bullet in the
  `2026-11-10 commerce journey end-to-end conformance` section);
- this node's `## Stage 7 CPU analytics / SQL audit (local evidence)` section
  is re-applied verbatim at the end of the file (newest work, built on top of
  authenticated-export). No heading renumbering was needed: the index is
  append-ordered by date and the two sides' headings do not collide. No
  cross-reference updates were needed: no file links to either side's new
  section anchors, and `scripts/check_docs_index.py` resolves file targets,
  not anchors.

Verification of the resolved file:

- `git diff origin/main -- docs/README.md` shows only the node's 5 added lines;
- `git diff HEAD -- docs/README.md` shows only main's additions;
- no `<<<<<<<`/`=======`/`>>>>>>>` markers remain anywhere in the worktree;
- the full merge-tree delta vs `origin/main` is exactly this node's paths
  (`analytics_audit/`, `runtime/`, this validation directory, `docs/README.md`;
  102 files), so no main work was dropped. The only deletions vs main are in
  `runtime/Cargo.lock` (the node's own owner-approved engine dependency graph).

## Protected bytes

- Locked blobs (AGENTS §4), verified before and after the round:
  - `runtime/crates/kix-kernel/src/lib.rs` =
    `69564b166f0c27f9af5d8422f0a466b18d74c20f` ✓
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
    `b607996c83a119c349f1cc90469ac1ba82764e20` ✓
- `reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`: zero diff between both
  merge parents and between the worktree and the index.
- `runtime/` is byte-identical to the node HEAD (the merge changed no Rust
  code); `.github/workflows/` is byte-identical to `origin/main` (no CI edit).

## Local checks actually run (merge round)

All commands ran in the foreground from the worktree root. Logs are retained
beside this file with the `merge-` prefix. The stdlib document-check block was
re-extracted verbatim from the **post-merge** `protocol.yml`
([merge-offline-checkers.sh](merge-offline-checkers.sh), 67 commands): it now
includes main's two new `check_consumer_binding_index.py` invocations, which
the pre-merge `offline-checkers.sh` (65 commands) predates.

| Command | Result |
|---|---|
| `bash validation/2026-11-13-k-stage7-cpu-analytics-sql-audit/merge-offline-checkers.sh` (67 stdlib document checks incl. 34 self-tests, `set -euo pipefail`) | exit 0; `docs index ok: scanned=416 indexed=381 allowlisted=35`; `consumer binding index ok: commands=84 … reads=13 not_bound=13` ([log](merge-offline-checkers.log)) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0; 961 tests OK (954 prior + main's 7 new receipt-vector tests) ([log](merge-reference-booking.log)) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 242 tests OK (230 prior + main's 12 new capital-refusal/consumer-vector tests) ([log](merge-reference-credit.log)) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest analytics_audit.test_admission analytics_audit.test_report` | exit 0; 6 tests OK ([log](merge-analytics-python.log)) |
| `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo test --manifest-path runtime/Cargo.toml -p kix-analytics-audit --locked --offline` | exit 0; 1 ignored with the designed engine-feature reason (default-CI behavior) ([log](merge-cargo-crate.log)) |
| `env RUSTUP_TOOLCHAIN=1.98.1 cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 ([log](merge-cargo-fmt.log)) |
| `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CXXFLAGS='-g0 --param ggc-min-expand=10 --param ggc-min-heapsize=32768' CXX=<worktree>/.local/analytics-audit/cxx-cache.sh POLARS_MAX_THREADS=2 KIX_AUDIT_RESULTS=.local/analytics-audit/merge-debug cargo test --manifest-path runtime/Cargo.toml -p kix-analytics-audit --features engines --test conformance --locked --offline -- --test-threads=1` | exit 0; 8 conformance tests passed in 10.76s (cached debug engines, synthetic source; fresh results dir, prior `final-debug` evidence untouched) ([log](merge-engines-debug.log)) |
| `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 0; 339 passed, 1 designed engine-feature ignore, 48 test binaries ([log](merge-cargo-workspace.log)) |
| `env RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CARGO_TARGET_DIR=.local/analytics-audit/ci-target cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 0 ([log](merge-cargo-clippy.log)) |

Failed attempt, recorded for completeness: an initial
`python3 -m unittest analytics_audit.test_admission analytics_audit.test_report analytics_audit.test_source`
was killed at the 5-minute foreground bound (exit 143). `test_source` is the
mandatory three-engine local-PostgreSQL acceptance; without the prior
session's `CXX`/`CXXFLAGS` cache-wrapper environment its cargo build script
fingerprints differ and it began recompiling `libduckdb-sys` from scratch in
`runtime/target`. No orphan process remained. It was replaced by the quick
battery above plus the cached synthetic engine conformance re-run; nothing in
the harness, timeouts or CI was changed.

## Not re-run in this round, and why

- `analytics_audit.test_source` (local-PG three-engine acceptance) and the
  release-profile engine run: the merge changed no Rust, harness or fixture
  code (`runtime/` and `analytics_audit/` are byte-identical to the node HEAD),
  and the prior sessions' three complete runs (207 PASS observations, 69 cases
  each) remain the engine acceptance evidence. Re-running would rebuild the
  engine graph outside the cache-wrapper environment for no merge-related
  signal.
- Full Move/Sui/localnet/ZK, bootstrap/downloads, SDK npm suites, historical
  v0.3-rc1 suites and the remaining reference suites: unchanged by the merge
  (byte-identical to parents) and covered by the prior sessions' records.
- Exact-head KTX/KIX CI: not queried (no network); remains a supervisor gate.

## Deviations and non-claims

- Python 3.13.5 locally vs 3.12 pinned in `protocol.yml` (same deviation as the
  prior sessions). Rust 1.98.1 and Node 24 match CI.
- This round proves the merge resolution and post-merge local checks only. It
  is not A2 non-author review, not exact-head CI evidence, not merge readiness
  or production readiness, and grants no merge authority. All production/
  runtime/economic execution flags remain false; no policy value was invented.
