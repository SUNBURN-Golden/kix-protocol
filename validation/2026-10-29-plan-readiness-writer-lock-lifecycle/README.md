# Readiness writer exclusion and failed-open cleanup

## Basis

Node: `plan-readiness-writer-lock-lifecycle`. Task input is the supervisor's
user-supplied node specification and design plan in this session; there is no
task issue or corresponding task document under `docs/tasks/`. This is not ASTRA
program mode. Authorization is offline regression evidence within
`docs/decisions/PROGRAM_DECISIONS_20260928.md` §4 and the existing single-writer
rule in `docs/contracts/READINESS_RUNTIME.md`.

Execution date: 2026-10-29. Observed **cached** `origin/main`, task base and branch
HEAD all equal `e5a8c0dad77c0b159beaa84dcd34fe1cebd9f7da` on
`agent/kix-plan-readiness-writer-lock-lifecycle`; the working tree was initially
clean. No local base delta. Remote freshness is unverified: the supervisor
expressly forbids all network/GitHub actions, so AGENTS §1's fetch was not run.
No rebase, merge or base change was performed.

Implementation/final committed task head: not created; supervisor owns commits
and publication. The SHA above identifies the unchanged starting HEAD, not a
commit containing these edits. No merge commit or post-merge checks exist.

## Existing coverage and precise gaps

| Requirement | Existing evidence | Classification before this node |
|---|---|---|
| Same-process exclusion and reopen after close | `readiness/test_faults.py::StoreTests.test_version_one_roundtrip_and_explicit_migration_only` | Sufficiently covered; retain the existing assertions. |
| Separate-process refusal, no mutation and reopen ordered after explicit close | The same StoreTests case uses two handles in one process only. | Not covered across processes; same-process evidence partially covers the overall lifecycle. |
| Complete-frame checksum failure | `readiness/test_faults.py::StoreTests.test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed` | Original failure sufficiently covered; cleanup while the failing process remains alive not covered. |
| Boundary initialization rejects a valid core record in an FSM journal | `readiness/test_faults.py::FaultTests.test_core_record_in_an_fsm_journal_fails_closed` | Original failure sufficiently covered; cleanup while the failing process remains alive not covered. |
| Detection of an injected handle leak | `readiness/test_conformance_sensitivity.py::ConformanceSensitivityTests.test_leaky_handle_is_caught` | Sufficient for its post-command leak control; it does not exercise failed initialization. |

## New assertions

Three methods in `readiness/test_faults.py::WriterLockLifecycleTests` close only
these gaps:

- `test_competing_process_refused_then_reopens_after_close`: parent owns a
  nonempty settlement journal; a fresh interpreter reports exactly
  `StoreError/JOURNAL_LOCKED`. Complete bytes, copied records and committed-byte
  accounting remain unchanged. The parent explicitly closes before signaling
  the child's single scheduled reopen; the child reads the original records and
  accounting, closes, and exits without changing bytes.
- `test_store_open_failure_releases_lock_while_process_alive`: reuse the
  reservation record and payload-byte-20 corruption from the checksum fixture.
  The child retains `StoreError/CHECKSUM_MISMATCH` and its traceback. While it
  waits, the parent's independent open also reaches `CHECKSUM_MISMATCH`, rather
  than `JOURNAL_LOCKED`. Locking precedes parsing in the inspected implementation;
  the damaged bytes remain identical and are never repaired. The child then
  acknowledges the retained original exception/traceback before exit.
- `test_boundary_init_failure_releases_lock_while_process_alive`: reuse the
  existing `core_commit` fixture unchanged. The child retains
  `ReadinessError/UNEXPECTED_RECORD` and its traceback. Before releasing that
  child, the parent successfully opens the store, checks exact records,
  accounting and bytes, and closes it. The child acknowledges the retained
  original failure; the journal remains invalid for FSM recovery.

The child code has no append path, including on unexpected open success.
Fresh `sys.executable -u -c` processes use repository-root cwd, `close_fds=True`
and anonymous stdin/stdout pipes. Blocking reader/waiter threads and queues
bound the handshakes at 30 seconds, solely as a harness deadlock guard. There
are no sleeps, polling or automatic retries; reopen is a signaled lifecycle
transition. Cleanup is registered immediately after acquisition, runs before
temporary-directory removal, closes stores and pipes, reaps children and joins
threads. A stuck child is terminated once, with kill as a final cleanup fallback.

## Actual commands and results

All test/check commands use `PYTHONDONTWRITEBYTECODE=1`. Results below describe
local execution only; they do not establish exact-head hosted CI.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; both SHAs and branch as recorded above. |
| `git hash-object` on both locked kernel paths | Before work: both match the required blobs listed below. |
| Python path/SHA-256 inventory of `reference/v0.3-rc1/**` | Before work: 108 files; aggregate hash below. |
| `python3 -m unittest readiness.test_faults.WriterLockLifecycleTests` | PASS: 3 tests. |
| `rustup toolchain list` | Installed active/default Rust 1.98.1; no installation. |
| `cat runtime/rust-toolchain.toml` | Exit 1: file absent; tooling discovery only. |
| `python3 -m unittest readiness.test_faults` | PASS: 67 tests, including all three new lifecycle tests. |
| `python3 scripts/check_readiness_evidence_map.py` | PASS: 36 rows, 186 citations; EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS: supplied and zero-PARTIAL baselines, synthetic PARTIAL controls and negative controls. |
| `python3 scripts/check_evidence_map_rollup.py` | PASS: 25 contracts; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | PASS: 16 negative controls. |
| `python3 scripts/check_docs_index.py` | PASS: scanned=312 indexed=277 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | PASS: all seven negative controls detected. |
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 and KTX-R1 dependency gate; no durability/performance certification. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS, exit 0: all workspace tests and doc-tests, including kix-kernel. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `git diff --check` | PASS: no whitespace errors. |
| Python before/after reference inventory equality and both `git hash-object` checks | PASS: both locked blobs match; all 108 reference paths and byte hashes identical. |
| Python comparison with `git show HEAD:docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md` | PASS: exactly one changed line, only the JRN-SINGLE-WRITER fixture cell; all other cells/text unchanged. |
| `git diff --name-only` and `git ls-files --others --exclude-standard` checked against the four-path allowlist | PASS: exactly the four authorized output paths. |

## Protected paths and complete change scope

Only these four paths are authorized outputs:

- `readiness/test_faults.py`
- `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`
- `validation/2026-10-29-plan-readiness-writer-lock-lifecycle/README.md`
- `docs/README.md`

Required locked blobs before and after work (both comparisons passed):

| Path | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Reference baseline: sorted path → SHA-256 inventory of all 108 files in
`reference/v0.3-rc1/`; SHA-256 of the sorted-key JSON inventory is
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
The before inventory is held outside the worktree; the after inventory matched
every path and byte hash, with the same aggregate hash. The complete changed-path
allowlist comparison also passed. All other tracked files, including the
protected inputs, implementation, workflows and manifests, remain unchanged.

Evidence-map edits append citations and explanatory qualifiers only to the
JRN-SINGLE-WRITER fixture cell. All statuses, counts, owners, nine OPEN rows,
historical text and other cells are preserved:
`Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`.

## Contract classification and non-claims

Writer refusal is contract-defined (AGENTS §8 A). Explicit-close reopening and
failed-initialization cleanup are source-informed implementation regressions
(§8 B), not new contract semantics or backend-neutral requirements. No contract
violation is asserted. Existing recovery uncertainties and `UNDETERMINED`
decisions remain open; this task selects no policy value.

No implementation, contract, checker, workflow, manifest, `.aiops/`, task
document, locked kernel file or protected reference file is changed.
`protocolTruth`, `productionConformance`, `productionReadiness`,
`productionEndpoint` and FSM `durable` stay false. No claim of production
readiness, power-loss or OS-crash durability, fsync correctness, distributed
fencing, multiwriter operation, external exactly-once, bank behavior, chain
finality or clean-room independence. No sockets, services, real funds, provider
calls, Sui network, dependencies, host changes, secrets or runtime activation.

## Deviations and review/CI gates

Fetch omitted under the explicit no-network instruction. The supplied node
specification substitutes for a nonexistent task document; no immutable task
input was created or changed. The combined HTTP/readiness CI command is narrowed
to `readiness.test_faults`, because its HTTP half opens sockets outside this
node's boundary. Rust commands use installed tooling and `--offline`; no
dependency installation or host change is authorized.

This is builder-authored local evidence, not independent review or merge-ready
status. Non-author exact-head review and both exact-head workflows, KTX kernel
verification and KIX protocol verification, must be completed/success before
any merge-ready report. Their run IDs/status/conclusions are NOT_RUN/unverified
in this session; the supervisor owns Git/GitHub and the final committed head.
No PR, comment, issue, commit, push or merge was made. Post-merge main CI and
merge-commit blob checks are not applicable. Remaining follow-up is supervisor
publication, exact-head review/CI and any user-authorized merge verification.
