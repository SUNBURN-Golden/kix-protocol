# AI delegation wrap conformance

Node: `plan-plan-ai-delegation-wrap-conformance`. Issue: none. Task document: the user-supplied node envelope and read-only design plan in this session; no file under `docs/tasks/` defines this loop-proposed node. Dependency: `plan-readiness-crash-point-sweep`. Audit floor A2. Not an ASTRA program-mode session.

Builder-authored local evidence, not independent review or a grade increase. Implementation is ready for supervisor handoff only, not merge-ready.

## Source and publication boundaries

Observed local `origin/main` and branch HEAD both equal `99c2655d38c283497b92dc24ba84a2ae6a5461fb`; branch `agent/kix-plan-plan-ai-delegation-wrap-conformance`. No base delta in local refs. Fetch was NOT_RUN because the supervisor explicitly prohibited network/GitHub actions; current remote freshness is unverified. Continued the three uncommitted partial-attempt files already present on arrival.

No commit, push, PR, issue or comment was made. Implementation/final task SHA: not yet assigned (uncommitted worktree). Exact-head KTX and KIX CI run IDs/status/conclusions: NOT_RUN/unverified, supervisor-owned after commit. Merge SHA and post-merge CI: not applicable. No old-head CI is transferred to this patch.

## Changed paths

- `readiness/conformance.py`: shared fixture and three adapter-neutral AI delegation scenarios.
- `readiness/test_faults.py`: sixth machine sweep row, six fault cells, two subsumption cells and replay/view dispatch; existing ExtensionTests retained.
- `readiness/CONFORMANCE.md`: 46 cases / 23 commands, nine subsumed cells, class-B replay characterization and fault-to-case table.
- `docs/README.md`: validation index pointer.
- `validation/2026-10-20-ai-delegation-wrap-conformance/README.md`: this evidence record.

No runtime, wrap, journal format, contract, workflow, `.aiops/`, task document or reference implementation change.

## Locks

Before and after work, `git hash-object` gives:

| Locked path | Required and observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`HEAD:reference/v0.3-rc1` tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Final diff and byte comparison against tracked HEAD verify that reference files remain byte-identical. No final merge exists to check.

## Existing coverage mapping (AGENTS §7)

| Requirement | Before this node | Gap addressed |
|---|---|---|
| Registry opens once across restart; same grant replay and unchanged journal/digest | Not covered by BackendConformance | `test_ai_delegation_registry_opens_once_and_issue_replays_across_restart` |
| Torn revoke recovery; replay; execution refusal | Partially covered: `ExtensionTests.test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off` uses FsmBoundary directly | `test_ai_delegation_torn_revoke_recovers_and_replays_once` exposes it through backend adapter |
| Crash-before-issue leaves no grant | Partially covered: `ExtensionTests.test_ai_delegation_crash_before_issue_does_not_create_the_grant` | `test_ai_delegation_crash_before_durable_issue_leaves_no_grant` adds adapter-neutral scenario and exact grant replay |
| Every AI command index × both fault kinds | Not covered | `CrashPointSweepTests.test_crash_point_sweep_ai_delegation`: open_registry, issue_grant, revoke_grant × partial/crash_before_durable |
| Existing fault cells remain subsumed | Sufficient for five prior machines; missing AI rows | Existing subsumption test now pins nine cells, including both dedicated AI fault cases |
| Observation fields | Sufficient in both existing ExtensionTests | Retained without editing those methods |

The sweep retains prefix recovery, fail-stop, first-resend result, no second journal entry, final digest/journal, record budget and false-label assertions. The five existing machines retain required `duplicate`/`applied` keys; only the AI wrap's observed shapes get special handling.

## Commands actually run

All jobs were foreground. Python tests used `PYTHONDONTWRITEBYTECODE=1`.

| Command | Result |
|---|---|
| `git status --short && git diff --stat && git rev-parse HEAD origin/main && git branch --show-current` | Three partial-attempt files on arrival; expected branch and identical local refs above |
| `python3 -m unittest -v readiness.test_faults` | PASS: 41 tests, including eight sweep tests and subsumption |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS: 78 tests; emitted ResourceWarning for an unclosed file in the HTTP suite, no failure |
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" || exit; done` | PASS: respectively 48 / 155 / 48 / 70 / 61 tests |
| `for check in check_docs_index check_status_register check_delegation_layer_matrix; do python3 "scripts/$check.py" && python3 "scripts/$check.py" --self-test || exit; done` | PASS: all six invocations; docs index 176 scanned / 141 indexed / 35 allowlisted; register and 36-row matrix valid; self-tests detected their intended negative fixtures |
| `git diff --check` | PASS: no whitespace errors |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | PASS: required blobs above |
| `git rev-parse HEAD:reference/v0.3-rc1` (before and after) | Unchanged tree above |
| `git diff --exit-code HEAD -- runtime reference .aiops docs/tasks .github` | PASS: no changes in protected/excluded tracked paths |
| `git status --short && git diff --stat` | Only the five changed paths listed above; no unexpected/untracked protected files |

Rust tests, Clippy and fmt: NOT_RUN, following the supplied design's touched-path selection; no Rust files change. Full protocol/kernel hosted checks remain required at the supervisor's exact final commit and are not claimed green here.

## Classification and non-claims

- Class A: observed behavior matches READINESS_RUNTIME lines 13, 21, 24, 26 and 40: prefix recovery, no grant before accepted append, replay without double grant, no record consumed by injected fault, execution disabled and durable false.
- Class B: open_registry has no idempotency key or duplicate flag; reopening an already-open registry raises `WrapError('ALREADY_OPEN')` without journal/digest change. AI duplicate responses omit `applied`. Exact first-resend result and cross-instance digest equality remain characterizations. All 23 swept commands emit one entry; multi-entry fault behavior is untested.
- Class C: none found on unmodified wrap/source.

No power-loss, OS-crash, fsync, lost-ack-after-append, concurrency, rejected-command sweep, production durability, chain finality, real funds, live provider, backend adoption or independent-conformance claim. Reward remains outside this mixin/sweep. The separate backend-adapter negative-control question remains untouched.

## Deviations and remaining gates

Preserved stricter replay shape assertions for existing machines rather than globally using dict.get as suggested by the design. Added explicit fault-to-case table. Actual booking/reference test count is 155, not the historical record's 75; only current observed counts are reported. No failing-before test run is claimed: this session resumed an already-written partial patch.

Network fetch and hosted exact-head verification are deferred under the supervisor instruction, not silently treated as passes. Supervisor must commit, obtain required exact-head KTX/KIX success and non-author review, and handle any authorized publication/merge and post-merge verification. No product decision or source change was required.
