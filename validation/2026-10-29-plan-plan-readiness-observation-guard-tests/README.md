# Readiness observation payload and false-label guards

Node: `plan-plan-readiness-observation-guard-tests`. Execution date: 2026-10-29.
Task input: the supervisor-supplied node specification and read-only design
plan; no issue or node-specific `docs/tasks/` document exists. Source: KIX
planner run `1793200863` (`/workspace/kix-run/logs/planner_1793200863`).
Dependencies: `readiness-extensions`, `plan-readiness-receipt-audit-tests`.
Non-ASTRA session; audit floor A2; `astra_gate: None`; `user_merge: False`.
Builder-authored local evidence, not non-author review or merge readiness.

## Source and heads

Branch: `agent/kix-plan-plan-readiness-observation-guard-tests`.
Starting HEAD, base and locally observed `origin/main` all equal
`e5a8c0dad77c0b159beaa84dcd34fe1cebd9f7da`; local base delta is zero.
The worktree was initially clean. `git fetch origin main` was NOT_RUN because
the later supervisor instruction prohibits network actions; remote freshness
is unverified. No rebase, merge or base change was performed.

Implementation content is uncommitted. The unchanged branch HEAD is the
starting SHA above; an implementation commit and exact final task head have
not been established. Commit, publication and GitHub actions belong to the
supervisor. No merge commit exists for this delivery.

## Coverage mapped before adding tests

All class/method names below are in `readiness/test_faults.py`.

| Requirement | Prior coverage and classification | Added evidence |
|---|---|---|
| Normal boundary observation output | Sufficient examples: `ExtensionTests.test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off`, `ExtensionTests.test_ai_delegation_crash_before_issue_does_not_create_the_grant`, `RewardWrapTests.test_reward_torn_write_replays_once`; `BoundaryMutationGuardTests._assert_observation` checks all five false labels for unchanged/fault calls | Existing integration scenarios retained unchanged |
| Complete permitted metadata across appended, unchanged and fault | Partially covered by those integration assertions | `ObservationGuardTests.test_positive_observations_preserve_metadata`: component, machine, decision, schema, count/fault code, exact field shape, all seven prohibited keys absent and all five labels literally False |
| Direct prohibited top-level field rejection | Not covered: normal outputs omit some keys but never supply prohibited fields to the helper | `test_prohibited_top_level_fields_are_rejected`: independently enumerated body, entry, args, limits, scope, period, authority; each rejects None, empty dict, empty list and empty string with OBSERVATION_BODY (28 subtests) |
| Direct exact-False label validation | Not covered: normal-output/store checks do not reach the helper's rejection path | `test_non_false_labels_are_rejected`: each of protocolTruth, productionConformance, productionReadiness, productionEndpoint, fsmDurable rejects True, integer 0, None, empty string and 'false' with OBSERVATION_LABEL (25 subtests); `test_literal_false_labels_are_accepted` accepts each label individually and all together (6 subtests), checking every label by identity |
| Invalid helper machine inputs | Not covered directly | `test_invalid_machine_inputs_are_rejected`: empty string, None, False, 0, empty list, empty dict and bytes raise OBSERVATION (7 subtests) |

The distinct gap is direct helper rejection, not missing normal integration
examples. Tests use only `ObservationError` and public `boundary_observation`,
with independent test-local field lists rather than implementation constants.
Every negative call has a valid decision and exactly one invalid dimension.
Positive cases use only metadata already emitted by `FsmBoundary._observe`:
schema plus appendedEntries=1/0 or faultCode='PARTIAL_WRITE'.

## Commands and actual results

Commands ran from repository root. The new class ran first, then the combined
readiness modules. The combined command runs sensitivity tests through both
the existing import and the explicit module selection; 77 is the runner's
execution count, not a count of unique tests. No implementation fix was needed.
The installed pinned Rust toolchain is `1.98.1-x86_64-unknown-linux-gnu`;
Cargo used cached dependencies with `--locked --offline`.

| Command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest readiness.test_faults.ObservationGuardTests` | PASS, 5 tests, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest readiness.test_faults readiness.test_conformance_sensitivity` | PASS, 77 test executions, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | PASS, scanned=312 indexed=277 allowlisted=35, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | PASS, self-test passed, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py` | PASS, reference_suites=7 node_tests=8 modules=4 excluded=3; readiness.test_faults reached, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py --self-test` | PASS, 18 negative controls, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_readiness_evidence_map.py` | PASS, rows=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_readiness_evidence_map.py --self-test` | PASS, supplied map and zero-PARTIAL map controls, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_runtime_architecture.py` | PASS, 7 tests, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS, all kernel tests and doc-tests, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS, all workspace tests and doc-tests, exit 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS, exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -` (inline preservation verifier described below) | Initial line-delimited path check failed on Git filename quoting; corrected NUL-delimited before/after checks PASS, exit 0 |
| `git status --short` / `git diff --name-only` | Only the four authorized paths listed below; three tracked modifications and one new validation README |
| `git rev-parse HEAD` / `git rev-parse refs/remotes/origin/main` | Both e5a8c0dad77c0b159beaa84dcd34fe1cebd9f7da; local ref only |
| `git branch --show-current` | agent/kix-plan-plan-readiness-observation-guard-tests |
| `rustup toolchain list` | Installed 1.98.1-x86_64-unknown-linux-gnu, active/default |

The relevant workflow definitions were inspected:
`.github/workflows/protocol.yml` runs readiness.test_faults alongside the
socket-using HTTP suite, document/discovery/map checkers and workspace Rust
checks. `.github/workflows/ktx-kernel.yml` runs architecture, kernel tests,
Clippy and formatting. The commands above are the socket-free local
equivalents for the touched paths. Full hosted workflows are not claimed.

## Preservation and complete changed paths

Before and after edits, an inline `PYTHONDONTWRITEBYTECODE=1 python3 -` verifier compared
`git hash-object` on both locked files to their required blobs. It enumerated
every reference file using pathlib, compared the full path set to
`git ls-tree -rz --name-only HEAD -- reference/v0.3-rc1`, compared every file's
bytes to `git show HEAD:<path>` and computed a sorted path/SHA-256 manifest.
The manifest digest hashes `json.dumps(manifest, sort_keys=True).encode()`.

| Protected asset | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | PASS, 69564b166f0c27f9af5d8422f0a466b18d74c20f | PASS, same required blob |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS, b607996c83a119c349f1cc90469ac1ba82764e20 | PASS, same required blob |
| `reference/v0.3-rc1/**` | PASS, 108 paths, byte-identical to HEAD | PASS, same complete paths and bytes |

Before/after reference manifest SHA-256:
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
The first verifier attempt exited 1 because line-delimited `git ls-tree`
quoted a Korean filename; the diagnostic showed 108 filesystem/tracked files
with only that representation difference. Switching the verifier to `-z`
resolved it; no protected file was changed. Final-merge lock verification is
not applicable because no merge occurred.

Complete allowed changed-path list:

- `readiness/test_faults.py`: import and five direct guard/positive test methods.
- `readiness/CONFORMANCE.md`: existing coverage, negative-test gap and limits.
- `validation/2026-10-29-plan-plan-readiness-observation-guard-tests/README.md`: this record.
- `docs/README.md`: one relative validation link.

Implementation, contracts, evidence maps/grades, workflows, SDK artifacts,
`.aiops/**`, task documents and protected sources remain unchanged.

## Gates, deviations and limits

| Gate | Run ID | Status / conclusion |
|---|---|---|
| Exact-head KTX kernel verification | None | NOT_RUN / unverified; supervisor must establish final committed head |
| Exact-head KIX protocol verification | None | NOT_RUN / unverified; no earlier SHA success transferred |
| Non-author exact-HEAD review / A2 audit | None | Outstanding; builder evidence is not independent review |
| Merge / post-merge main CI | None | Not performed / not applicable |

The supplied design is implemented within its four allowed paths. Deviations:
session-start fetch is excluded by the supervisor's no-network rule; the full
`integration_gate.test_http_gate` suite is NOT_RUN because it opens sockets.
Architecture/Rust checks ran after the combined suite and before the document
checks so the validation link target could contain their actual results.
No background jobs, downloads, provider calls, credentials, runtime activation
or GitHub publication were used. No required exact-head review/CI gate is waived.
Final-head results belong in the supervisor's closure report rather than a
repository commit that would create a self-reference loop.

Contract classification: the false-label boundary matches
PROGRAM_DECISIONS_20260928 §4 and READINESS_RUNTIME.md (AGENTS §8 class A).
The exact helper codes, top-level key list, machine-input validation and
permitted metadata shape are source-informed implementation characterizations
(class B), not new authoritative semantics. No explicit contract violation
was found. No combined-invalid precedence, recursive sanitization, whitespace
normalization, machine registration, extra-field policy or new decision
vocabulary is defined or tested.

No production durability, power-loss/OS-crash/fsync correctness, distributed
fencing, bank exactly-once, chain finality, backend conformance/adoption, audit
evidence or production-readiness proof is claimed. All five observation labels
remain literally False. Existing recovery uncertainties, OPEN owners,
product-policy values and evidence-map grades remain unchanged. Follow-up is
the supervisor's final commit, A2 non-author exact-HEAD review and successful
exact-head KTX/KIX CI; these local results do not establish merge readiness.
