# plan-stage5-host-preflight-checker — stage-5 pinned-host preflight

Node: `plan-stage5-host-preflight-checker`. Issue: none. `docs/tasks/` has
no file for this node; it is a loop-proposed node, not in
`.aiops/program.json`. Depends on: `k-stage4-adoption-decision`.
Branch: `agent/kix-plan-stage5-host-preflight-checker`.
Observed `origin/main` and branch HEAD at session start, after
`git fetch origin main`: `2c7bc7dd7d4831b0ab3c0ce5e394999a7f72de12`.

**Evidence preparation only; not a k-stage5-durable-tx acceptance run; no
option selected and no provisioning performed.**

This session did not commit, push, open a PR, or comment. There is no
implementation commit SHA. Local results below are not exact-head CI;
there is no KTX kernel verification run ID and no KIX protocol
verification run ID for a head that contains these files.

## Scope and non-claims

`scripts/check_stage5_host.py` is a standard-library-only, read-only
preflight checker. It reports whether the host it runs on meets the
`k-stage5-durable-tx` acceptance prerequisites named in that node's
DECISION_REQUIRED record. It installs nothing, changes nothing, starts
no service, connects to no database, and sets no CPU affinity. A PASS is
evidence that the named prerequisites were observed on the host; it is
not stage-5 acceptance, host qualification, provisioning approval,
durability evidence or production readiness. This node prepares
option-1 evidence for the blocked node; no provisioning and no decision.

## Source/basis

The prerequisite list is taken from the DECISION_REQUIRED record written
by the blocked `k-stage5-durable-tx` builder at
`/workspace/kix-run/state/k-stage5-durable-tx.decision.md` (dated
2026-10-13, evidence record
`validation/2026-10-13-k-stage5-durable-tx/README.md` on branch
`agent/kix-k-stage5-durable-tx`; that record is not in this worktree):

- PostgreSQL binaries at `/usr/lib/postgresql/17/bin/{postgres,initdb}`,
  version 17.11-0+deb13u1 — the adopted local, non-production pin of
  `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 (option A,
  merged via PR #140 per the record);
- importable `psycopg` 3.x;
- `taskset` and `ss` on PATH;
- cores 0–1 available.

The checker requires each binary's `--version` to equal the exact banner
`<name> (PostgreSQL) 17.11 (Debian 17.11-0+deb13u1)` after trimming
whitespace — a `17.11` substring, package metadata, a different binary
on PATH, or one binary's result is not accepted for the other.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_stage5_host.py` | New read-only stdlib preflight checker with `--self-test`. |
| `docs/README.md` | One index bullet pointing at this record (required by `scripts/check_docs_index.py`; see Deviations). |
| `validation/2026-10-20-stage5-preflight/README.md` | This record. |

## Existing coverage

- Host-fact collection: partially covered by `exploration/stage4/host.py`,
  which records host facts but does not validate both executable pins
  against exact banners; `exploration/stage4/clusters.py` launches
  services and imports psycopg, unsuitable for a read-only checker.
- Kernel-lock regression: covered by the existing locked-source checks
  (`locked_sources_and_new_harness_sources_are_identified`).
- A fail-closed, machine-readable preflight CLI for these exact
  prerequisites, including synthetic pin-rejection cases: not covered —
  that is the gap this node fills.

## Synthetic verification

`python3 -B scripts/check_stage5_host.py --self-test` injects synthetic
observations through the evaluator and requires each break to produce a
per-item FAIL line plus a FAIL summary: missing/non-executable binaries,
non-zero exit, timeout, banners `17.10` / `17.110` /
`17.11-0+deb13u2` / missing Debian revision / trailing suffix, an
independent `initdb` mismatch, psycopg import failure and major versions
2 and 4 and unparseable output, missing `taskset`/`ss`, affinity masks
excluding core 1, and an unavailable affinity API. It also asserts the
summary carries `schema_version: 1`, `evidence_prep: true` and
`acceptance_run: false`. The self-test never probes the actual host.

## Builder-host run

Run on this builder host at 2026-10-20 UTC with
`python3` (`platform.python_version()` = `3.13.5`):

```
python3 -B scripts/check_stage5_host.py
exit=1
{"expected": "postgres (PostgreSQL) 17.11 (Debian 17.11-0+deb13u1)", "id": "postgres", "observed": {"executable": false, "path": "/usr/lib/postgresql/17/bin/postgres", "present": false}, "reason": "file not present", "status": "FAIL", "type": "check"}
{"expected": "initdb (PostgreSQL) 17.11 (Debian 17.11-0+deb13u1)", "id": "initdb", "observed": {"executable": false, "path": "/usr/lib/postgresql/17/bin/initdb", "present": false}, "reason": "file not present", "status": "FAIL", "type": "check"}
{"expected": "importable psycopg, major version 3", "id": "psycopg", "observed": {"ok": false, "returncode": 1, "stderr": "...ModuleNotFoundError: No module named 'psycopg'", "stdout": ""}, "reason": "import failed: ...ModuleNotFoundError: No module named 'psycopg'", "status": "FAIL", "type": "check"}
{"expected": "executable on PATH", "id": "taskset", "observed": {"resolved": "/usr/bin/taskset"}, "reason": "/usr/bin/taskset", "status": "PASS", "type": "check"}
{"expected": "executable on PATH", "id": "ss", "observed": {"resolved": "/usr/bin/ss"}, "reason": "/usr/bin/ss", "status": "PASS", "type": "check"}
{"expected": "cores 0 and 1 in sched_getaffinity(0)", "id": "cpu_affinity", "observed": {"available": true, "cpus": [0, 1, 2, 3, 4, 5, 6, 7]}, "reason": "cores [0, 1, 2, 3, 4, 5, 6, 7] available", "status": "PASS", "type": "check"}
{"acceptance_run": false, "checks_failed": 3, "checks_passed": 3, "evidence_prep": true, "mode": "host", "schema_version": 1, "status": "FAIL", "type": "summary"}
```

The builder host FAILs on `postgres`, `initdb` and `psycopg`, as the
blocked node's record reported; `taskset`, `ss` and cores 0–1 happen to
be present here. This is the expected non-zero exit with per-item FAIL
lines, not a manufactured failure.

## Preservation checks

Locked blobs at session start and after the change (untracked new files
and worktree edits do not move HEAD):

- `runtime/crates/kix-kernel/src/lib.rs` → `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` → `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime` was empty.

## Commands and results

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | both `2c7bc7dd7d4831b0ab3c0ce5e394999a7f72de12` |
| `git hash-object` on the two locked files, before and after | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` both times |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime` | empty |
| `python3 -B scripts/check_stage5_host.py --self-test` | exit 0; 19 synthetic cases each caught; `self-test: pass` |
| `python3 -B scripts/check_stage5_host.py` | exit 1; FAIL summary, per-item lines above |
| `python3 -B scripts/check_stage5_host.py --bogus` | exit 2; usage on stderr |
| `python3 -B scripts/check_docs_index.py` | exit 0 after adding the index bullet |
| `python3 -B scripts/check_docs_index.py --self-test` | exit 0; `self-test: pass` |
| `python3 -B scripts/verify_runtime_architecture.py` | exit 0; `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 -B scripts/test_runtime_architecture.py` | exit 0; `Ran 7 tests`, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; all kix-kernel tests passed (transitions 32, contract_edge_cases 8, quarantine_capacity 8, others 0-failed) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0; all workspace crates green, doc-tests 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |

## Remaining blockers

- `k-stage5-durable-tx` stays blocked: this host lacks the pinned
  PostgreSQL binaries and psycopg, and this node performs no
  provisioning. Option selection and provisioning remain with the User.
- The design plan for this node declared DECISION_REQUIRED on (1) the
  docs-index link requirement and (2) locating the source record. Both
  resolved: repository precedent is that every `validation/*/README.md`
  is index-linked from `docs/README.md` (the checker runs in CI on every
  non-draft execution and would fail otherwise), and the source record
  was found at `/workspace/kix-run/state/k-stage5-durable-tx.decision.md`.
- No CI run exists for a head containing these files; exact-head CI is
  the §10 gate after the supervisor's commit.

## Non-claims

No production readiness, durability, exactly-once, or finality. No
acceptance suite was run. No option was selected. No provisioning,
install, or host mutation was performed. No lock opened, no evidence
grade raised, no exact-head CI.
