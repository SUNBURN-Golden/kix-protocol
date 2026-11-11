# Completed-append acknowledgement-loss local evidence

Node: `plan-readiness-post-append-ack-loss`; issue: none. Immutable task input:
user-supplied node specification and read-only design plan in this builder
session; no corresponding task file under `docs/tasks/`. Source: KIX planner
run `1793237680` (`/workspace/kix-run/logs/planner_1793237680`), loop-proposed,
outside `.aiops/program.json`. Dependencies:
`plan-readiness-crash-point-sweep`, `plan-plan-ai-delegation-wrap-conformance`,
`plan-plan-reward-wrap-conformance`, `plan-readiness-wrap-fault-sensitivity`.
Audit floor A2; Astra gate none; user_merge False; not ASTRA program mode.
Builder-authored source-informed local evidence only, not non-author review.

## Source identities and execution boundaries

Execution date: 2026-10-29. Branch:
`agent/kix-plan-readiness-post-append-ack-loss`. Initially clean. Observed local
`origin/main`, base and initial/unchanged HEAD:
`9593ad04cd727b7107485b4113dbd5c6066a4393`.
No local-ref delta. `git fetch origin main` NOT_RUN because the supervisor
explicitly forbids network/GitHub actions; remote freshness remains unverified.
No rebase, merge, commit, push, PR, issue, comment or other publication occurred.
Implementation/final task head: not assigned; uncommitted patch, supervisor owns
Git and GitHub. No merge commit or post-merge checks apply to this session.

Read-only inspections covered AGENTS.md, README, DEVELOPMENT_PLAN, BASELINES,
AUTHORITY_MODEL_1, task-directory index (no matching task document), control-plane
pointer/client, PROGRAM_DECISIONS_20260928 §4–5, READINESS_RUNTIME,
CONFORMANCE, fault/conformance/sensitivity tests, wrappers/observations and both
workflow definitions. The supplied node/design are the task document for this
non-program session. The pending shared-policy pin does not activate a runtime.

## Changed paths

- `readiness/test_faults.py`: test-only exception, scoped real-append wrapper and
  seven `PostAppendAckLossTests` methods; shared snapshots and explicit labels.
- `readiness/CONFORMANCE.md`: dated additive coverage; historical exclusions intact.
- `docs/README.md`: one link to this record.
- `validation/2026-10-29-plan-readiness-post-append-ack-loss/README.md`: this record.

## Existing coverage mapped before edits (AGENTS §7)

| Requirement | Existing test/path | Prior classification |
|---|---|---|
| Incomplete/absent command recovery at every sequence position | `readiness/test_faults.py::CrashPointSweepTests`, `readiness/conformance.py::BackendConformance` | Sufficient for partial/crash-before-durable; not the completed-append boundary. `partial` leaves an incomplete frame, `crash_before_durable` writes no target frame. |
| Fencing, reopening and replay identity/economics | `CrashPointSweepTests`, `BoundaryMutationGuardTests`, `BackendConformance` restart cases | Partially covered: failure fences and replay work elsewhere, but no positive completed-append lost-ack test. |
| Detection of wrongly retained absent attempts | `readiness/test_conformance_sensitivity.py::PersistFaultAttemptAdapter` AI/reward partial/crash mappings | Sufficient negative controls, reused unchanged. Their real-append-then-raise injection deliberately violates absence expectations, making mapped cases fail. It does not positively prove retained-result replay. |
| Caller exception despite completed append, retention before replay, zero append on replay for seven machines | No positive case; sweep explicitly excludes lost acknowledgements | Not covered; seven new cases. |
| Other journal/restore/size/codec/envelope/lock behavior | Existing `StoreTests`, `JournalByteSweepTests`, `WrapperRestoreRejectionTests`, `RecordSizeBoundaryTests`, `JsonCodecRegressionTests`, `RecordEnvelopeTests`, `WriterLockLifecycleTests` | Sufficient for their existing predicates; not duplicated. |

## Seven new outcomes

Every method below is `PostAppendAckLossTests.test_post_append_ack_loss_<machine>`.
Each passed: exactly one append invocation/completion, exact injected exception
object/code at caller, fault observation, refused subsequent calls and machine
access with an uninvoked sentinel, completed prefix recovered before replay,
full duplicate response equality, zero replay appends, unchanged canonical state,
digest, public view, journal, stamped records/count, committed bytes and file
bytes, and retention after a second reopen. Separate uninterrupted controls use
the same valid fixtures, without inheriting/rerunning sweep tests.

| Machine | Sequence index / target / identity | Business predicate and outcome |
|---|---|---|
| settlement | 4 / distribute / `dist-1` | PASS: cash 97,000, organizer/platform effect 92,000/5,000; unchanged full obligations, outstanding 3,000/0. |
| reservation | 2 / hold / `hold-1` | PASS: HELD reservation and RESERVED slot. |
| resale | 4 / accept_resale / `transfer-1` | PASS: buyer-2 holder, current version 2. |
| credit | 2 / draw / `draw-1` | PASS: outstanding exposure 80,000. |
| admission | 3 / consume / `consume-1` | PASS: CONSUMED, version 2 and unchanged evidence. |
| ai_delegation | 1 / issue_grant / grant `g1`, identical binding | PASS: ACTIVE/generation 1; replay has no `applied`. Replay occurs before revocation; no invented idempotency key or historical ACTIVE-after-revocation assertion. |
| reward | 5 / observe_transfer_effects / `fx-1` | PASS: one identical reward effect, entire pool unchanged, treasury fixture balance 46. |

Keyless `open_registry`/`open` are prefix steps only. The test wrapper saves one
instance's real `append(body, fault=None)`, lets it return successfully, then
raises a preconstructed `_PostAppendAckLost(StoreError)` carrying
`TEST_POST_APPEND_ACK_LOST`. It never fabricates a record or changes accounting,
recovery, production fault hooks, adapter requirements or protocol commands.
The patch scope ends before reopening. Explicit replay modifies expected response
only by `duplicate=True` and non-AI `applied=None`; every effect, evidence and
business snapshot is otherwise compared in full. The call has no automatic retry.

Record schema is exactly `schema=1`, `kind=fsm_commit`, `machine`, `entry`,
`protocolTruth=False`, `productionConformance=False`. Required view/result labels
are indexed (missing fields fail), including FSM durable, applicable sweep flags,
all AI FALSE_FLAGS and reward ALWAYS_FALSE_FLAGS; reward provenance is literally
MOCK_TOKEN_REWARD_ONLY. Both fault and replay observations require schemaVersion 1,
all four false truth/production flags and false fsmDurable.

## Commands actually run and results

Commands ran from repository root in the foreground. Inspection commands (`cat`,
`sed`, `rg`, `git ls-tree`) were read-only. Three ad-hoc `python3 -B -` fixture
inspections opened temporary local boundaries through each selected prefix and
printed results/views or their false flags; all exited 0. No external call.
The table below records executable acceptance checks and protection evidence.

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git rev-parse HEAD origin/main`; `git branch --show-current` | Exit 0; expected directory/branch, clean initial status, both refs equal base above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after) | Exit 0, both required blobs match (values below). |
| `python3 -B -` initial reference-byte verifier using `git ls-tree -r --name-only <base> reference/v0.3-rc1`, `Path.read_bytes()` and `git show <base>:<path>` | FAILED before edits and on the first final check: `FileNotFoundError` because default Git quoting escaped a Korean filename. The initial shell bundle continued to a successful fixture inspection, masking that script's failure in its overall exit status. No protected mismatch was established. Corrected below; the initial clean Git status is the pre-edit protection evidence. |
| `python3 -B -m unittest -v readiness.test_faults.PostAppendAckLossTests` | PASS twice, 7 tests each (initial implementation and after adding business anchors). |
| `python3 -B -m unittest readiness.test_faults` | PASS twice, 98 tests each (same two revisions). |
| `python3 -B scripts/check_docs_index.py` | PASS twice (including final record), exit 0: scanned=318, indexed=283, allowlisted=35. |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS, exit 0: all seven negative controls detected. |
| `python3 -B scripts/check_ci_test_discovery.py` | PASS, exit 0: 7 reference suites, 8 node tests, 4 modules, 3 historical exclusions; existing readiness module entry reaches new methods. |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0: 18 negative controls. |
| `python3 -B scripts/check_readiness_evidence_map.py` | PASS, exit 0: 36 rows, 186 citations; EXERCISED=27, PARTIAL=0, NOT_EXERCISED=0, OPEN=9. |
| `python3 -B scripts/check_readiness_evidence_map.py --self-test` | PASS, exit 0: supplied-map and zero-PARTIAL baselines and positive/negative controls. Locked-blob mutation occurs in the checker's temporary fixture, not the protected worktree. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS, exit 0: 139 tests. Existing integration tests emitted ResourceWarning for unclosed file handles; no test failure. Loopback only, no public endpoint. |
| `python3 -B scripts/verify_runtime_architecture.py` | PASS, exit 0: architecture v5 + KTX-R1 dependency gate; durability/performance NOT certified. |
| `python3 -B scripts/test_runtime_architecture.py` | PASS, exit 0: 7 tests. |
| `rustup toolchain list` | Exit 0: installed active/default 1.98.1; no download. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS, exit 0: 139 integration tests (39+5+12+11+32+8+32), no failures; unit/doc suites each have 0 tests. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `git rev-parse HEAD origin/main HEAD:reference/v0.3-rc1` | Exit 0: unchanged local refs above; protected reference tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| Corrected `python3 -B -` verifier: `git ls-tree -rz --name-only <base> reference/v0.3-rc1`, NUL splitting, byte comparison via `git show`, exact file-set comparison; changed/untracked allowlist and historical-prefix checks | PASS, exit 0: all 108 reference files byte-identical to base with exact file set; exactly four permitted changed/untracked paths; original CONFORMANCE and docs index bytes preserved as exact prefixes. |
| `git diff --check`; `git diff --stat`; `git diff -- readiness/test_faults.py`; `git diff -- docs/README.md`; `git status --short --untracked-files=all` | Exit 0; no whitespace errors, final source diff reviewed, exactly the four paths listed above. No staged changes or commit. |

Read-only inspection probes also encountered a guessed workflow filename
`.github/workflows/ktx.yml` (absent, `cat` exit 1) and absent `.cargo` search
directory (`rg` diagnostic); discovery located and read the actual
`.github/workflows/ktx-kernel.yml`. Neither affected checks or changed files.

## Protected paths, classifications and delivery gates

Before/after locked blobs (both verified; no edits):

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

The initial clean worktree and final exact four-path allowlist preserve all
runtime source, contracts, decisions, `.aiops/`, `docs/tasks/`, workflows and
reference implementations. The corrected final verifier byte-compares the
entire protected reference file set. Historical CONFORMANCE exclusions remain
verbatim, including the earlier sweep's lost-ack limitation. No protected path
was transiently edited. The initial byte-verifier error is recorded above rather
than reported as a pre-edit pass.

AGENTS §8 A: matching boundary refusal after store failure, idempotent replay,
retained business state and false non-production labels. §8 B: source-informed
cross-instance full result/state/digest/byte equality, selected fixtures' one-entry
transitions and duplicate response shapes. No authoritative contract defines
these exact representation comparisons as a backend requirement. §8 C: no
explicit contract violation found. No contract or product-policy value was set.
Existing malformed-recovery, mid-file length damage, zero-byte reinitialization,
frame-boundary cuts and AI tool-check-order uncertainties remain unchanged and
UNDETERMINED; this node does not resolve or regrade them.

Deviations: fetch omitted under explicit supervisor prohibition; task input is
in-session rather than a new immutable docs/tasks file. No design implementation
deviation; literal business anchors strengthen the control comparisons. No Rust
input changes. Full protocol pipeline (SDK, Move, circuit, localnet/storage jobs)
and Rust workspace-wide tests/Clippy are NOT_RUN and are not represented by
these touched-path local equivalents. The reference-byte verification script
needed NUL-delimited paths; both failed attempts and the passing correction are
recorded above. All task tests/checkers passed on their first implementation run;
the narrow/module tests also passed after adding literal business anchors.
Exact final head awaits supervisor commit. Exact-head KTX CI run ID/status/
conclusion: NOT_RUN/unavailable. Exact-head KIX protocol CI run ID/status/
conclusion: NOT_RUN/unavailable. Non-author exact-HEAD A2 review: outstanding.
Post-merge main CI/locked blobs: N/A (no merge). These remain delivery gates;
local builder READY is not merge-ready or merge authorization.

This is controlled in-process acknowledgement-loss evidence only, using a single
process/writer and local files. It is no OS-crash, power-loss, physical-media/fsync
durability, distributed fencing, external exactly-once, bank/PG/KYC execution,
chain finality, legal compliance, production-readiness or backend-adoption proof.
No hardware, expenditure, credentials, public endpoints, Sui testnet/mainnet,
new storage engine, coin/TIX module or production runtime was required or used.
Follow-up is the supervisor's commit/publication and required exact-head gates;
external durability scenarios require separate authorization/evidence.
