# Readiness wrapper recovery fault sensitivity

Node: `plan-readiness-wrap-fault-sensitivity`; issue: none. Task inputs are the
user-supplied node specification and read-only design plan, not a file under
`docs/tasks/`. Source: planner run `1793230233`; loop-proposed node outside
`.aiops/program.json`. Dependencies: `plan-readiness-conformance-negative-controls`,
`plan-plan-ai-delegation-wrap-conformance`, `plan-plan-reward-wrap-conformance`.
Audit floor A2; no Astra gate; not ASTRA program mode.

Builder-authored local evidence only; no independent review or grade increase.

## Existing coverage mapped before implementation (AGENTS §7)

This table was recorded before adding adapters or tests.

| Requirement | Existing evidence | Classification |
|---|---|---|
| Correct recovery/replay for all six wrapper cases | `readiness/conformance.py::BackendConformance.test_ai_delegation_registry_opens_once_and_issue_replays_across_restart`, `test_ai_delegation_torn_revoke_recovers_and_replays_once`, `test_ai_delegation_crash_before_durable_issue_leaves_no_grant`, `test_reward_open_observe_and_hold_replay_across_restart`, `test_reward_torn_mark_eligible_recovers_and_replays_once`, `test_reward_crash_before_durable_observe_leaves_no_reward`; existing all-cases unmodified-adapter control | Sufficient; reuse unchanged |
| Wrapper observations and reward restore round-trip | `readiness/test_faults.py::ExtensionTests`, `RewardWrapTests` | Sufficient; retain unchanged |
| Every command position with both faults | `CrashPointSweepTests.test_crash_point_sweep_ai_delegation`, `test_crash_point_sweep_reward` in `readiness/test_faults.py` | Sufficient; retain unchanged |
| Persistent recovery-mutant mapping for the six wrapper cases | Explicit gap in `readiness/CONFORMANCE.md`; prior reward validation contains temporary probes only | Not covered; this node's six negative controls |
| Sensitivity runner and CI discovery | Existing `_run_case`, `_CaseResult`, `_assert_fault_is_caught`; `ConformanceSensitivityTests` already imported by `readiness.test_faults` | Partially covered; reuse and require no skips/expected failures/unexpected successes |

## Observed source state

Branch: `agent/kix-plan-readiness-wrap-fault-sensitivity`. Initial HEAD and local
`origin/main`: `2141f72316ba8187d2f5d9de5c5fd0a909ee5993`; clean initial worktree,
no delta between local refs. `git fetch origin main` NOT_RUN: supervisor explicitly
prohibits all network actions. Remote freshness is unverified; no rebase or merge.
Implementation/final task head is unassigned (uncommitted patch); supervisor owns
commit/publication. No task document, historical evidence or #266 evidence rewritten.

## Changed paths

- `readiness/test_conformance_sensitivity.py`: two machine-scoped adapter mechanisms,
  six map entries/tests, intended-recovery traceback checks and stricter runner checks.
- `readiness/CONFORMANCE.md`: six negative-control rows and precise limits; removes
  only the six-case sensitivity-gap bullet, preserving all other documented gaps.
- `docs/README.md`: exact link to this record; historical #266 entry unchanged.
- `validation/2026-10-29-plan-readiness-wrap-fault-sensitivity/README.md`: this record.

Production code, `BackendConformance` assertions/fixtures, `readiness/test_faults.py`,
contracts, workflows, maps/grades, decisions, `.aiops/`, `docs/tasks/`, runtime and
reference implementations are unchanged.

## Six fault/control outcomes

Each map key has a `test_<key>_is_caught` outer method on the already CI-imported
`ConformanceSensitivityTests`. Every mutant runs exactly one unchanged mapped
case and yields exactly one intentional assertion failure in that case. Every
paired `LocalReadinessAdapter` control runs once and passes. Both runs require
zero errors, skips, expected failures and unexpected successes. The all-cases
control has the same no-skip checks. The existing leaky-handle control still
requires its separate `JOURNAL_LOCKED` error.

| Map key | Unchanged BackendConformance case | Captured recovery failure | Paired control |
|---|---|---|---|
| `ai_drop_acknowledged` | `test_ai_delegation_registry_opens_once_and_issue_replays_across_restart` | `conformance.py:697`: `self.assertEqual(machine.state_digest(), digest)` differs after losing `issue_grant` | PASS |
| `ai_partial_retained` | `test_ai_delegation_torn_revoke_recovers_and_replays_once` | `conformance.py:735`: `'REVOKED' != 'ACTIVE'` | PASS |
| `ai_crash_attempt_durable` | `test_ai_delegation_crash_before_durable_issue_leaves_no_grant` | `conformance.py:776` → `code` at line 136: `AssertionError: expected AiDelegationError`; existing grant prevents `UNKNOWN_GRANT` | PASS |
| `reward_drop_acknowledged` | `test_reward_open_observe_and_hold_replay_across_restart` | `conformance.py:815`: `self.assertEqual(machine.state_digest(), digest)` differs after losing `hold` | PASS |
| `reward_partial_retained` | `test_reward_torn_mark_eligible_recovers_and_replays_once` | `conformance.py:857`: `'ELIGIBLE' != 'HELD'` | PASS |
| `reward_crash_attempt_durable` | `test_reward_crash_before_durable_observe_leaves_no_reward` | `conformance.py:893` → `code` at line 136: `AssertionError: expected TokenRewardError`; existing reward prevents `UNKNOWN_REWARD` | PASS |

The drop adapter removes the selected machine's last recovered `fsm_commit`
from that handle's recovery records before normal `_recover()`. Empty opens
are unaffected. The persist adapter wraps only the opened instance's append,
calls ordinary append without injection for the selected machine/fault, then
raises the ordinary fault. Normal boundary fencing, close and real-file replay
remain in use. `partial` incorrectly commits the whole attempt requested as
torn; it does not simulate physical media tearing. Separate `partial` and
`crash_before_durable` configurations forward all other appends unchanged.
No global monkeypatch, new storage format, fabricated views/digests or failure
result stubs are used. Record fields and false labels are preserved.

## Commands actually run and results

Commands ran from repository root, in the foreground. Test and checker invocations
used `PYTHONDONTWRITEBYTECODE=1` (shown once here to shorten the command column).
Read-only `cat`, `sed` and `rg` inspections covered the required governance
inputs, D-3 contract, existing scenarios/wrappers, runner and workflow commands.

| Command | Actual result |
|---|---|
| `pwd && git status --short && git rev-parse HEAD && git rev-parse origin/main && git branch --show-current` | Expected worktree/branch; initially clean; both local refs equal the observed SHA above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after) | PASS: both required blobs match, values below |
| `git rev-parse HEAD:reference/v0.3-rc1` (before/after) | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |
| `python3 -` reference-byte comparison using `git ls-files -z reference/v0.3-rc1`, `Path.read_bytes()` and `git show HEAD:<path>` (before/after) | PASS: all 108 tracked reference files byte-identical to HEAD |
| `python3 -m unittest -v readiness.test_conformance_sensitivity` (baseline) | PASS: 8 outer tests |
| `python3 -m unittest readiness.test_faults` (baseline) | PASS: 73 tests |
| `python3 -m unittest -v readiness.test_conformance_sensitivity` (first implementation run) | FAIL: 14 outer tests, 2 failures in my traceback expectations for the crash cases; actual inner failures were the intended missing-domain-error assertions from `code(...)` |
| `python3 -m unittest -v readiness.test_conformance_sensitivity` (after correction) | PASS: 14 outer tests; six new intentional inner failures detected and paired controls pass |
| `python3 -m unittest readiness.test_faults` (after implementation) | PASS: 79 tests, including imported sensitivity class |
| `python3 scripts/check_ci_test_discovery.py` | PASS: 7 reference suites, 8 node tests, 4 modules, 3 historical exclusions; sensitivity module reached via `readiness.test_faults` |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS: all 18 negative controls detected |
| `python3 scripts/check_docs_index.py` (also repeated after completing this record) | PASS: scanned=315, indexed=280, allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` (also repeated after completing this record) | PASS: all intended negative fixtures detected |
| `python3 -` six-row diagnostic using `_run_case` for each mutant and paired control, asserting run/failure/error/skip counts and printing captured tracebacks | PASS: six intentional inner assertion failures at the locations above; six controls pass; zero runner errors or skips |
| `git diff --check` | PASS: no whitespace errors |
| `git diff --stat` and `git diff -- readiness/test_conformance_sensitivity.py readiness/CONFORMANCE.md docs/README.md` | Reviewed scoped implementation/documentation diff; no conformance assertions changed |
| `git diff --exit-code HEAD -- runtime reference .aiops docs/tasks .github` | PASS: no changes in protected/excluded tracked paths |
| `git status --short` | Only the four changed paths listed above, including this new validation directory |

The permitted local equivalent of `protocol.yml`'s combined HTTP/readiness step
is `readiness.test_faults` here. `integration_gate.test_http_gate` NOT_RUN because
it opens sockets, outside this node's explicit boundary. Discovery and docs-index
checks were run in both modes as their workflow requires. No Rust inputs change;
Cargo tests, Clippy and formatting NOT_RUN. Kernel blob and reference checks are
the applicable local preservation checks, not full workflow success.

## Protected bytes and remaining gates

Before and after implementation:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The reference tree and all 108 file-byte comparisons match HEAD. No protected
file was edited, even transiently. No final merge exists for merge-blob checks.
No commit, push, PR, issue or comment was made. Exact-head KTX kernel and KIX
protocol CI run IDs/status/conclusions: NOT_RUN/unverified, supervisor-owned
after commit. Merge SHA and post-merge CI: not applicable. Non-author exact-head
review and required audits remain separate gates. Local READY means builder
handoff only, not merge-ready, backend acceptance or independent verification.

## Classification, non-claims and deviations

Class A: the unmodified adapter controls match existing recovery/replay
expectations. Class C: no violation found in the unmodified implementation;
intentional faulty test adapters are not product discrepancies. Class B: no new
contract semantics or policy values were defined. Existing byte-sweep length
corruption/truncation uncertainties, command-sweep characterizations and
multi-entry/rejected-command/lost-ack limitations remain. All remaining
CONFORMANCE gaps (format/schema/checksum/writer/label refusal, observations,
named budget diagnostics/overload and non-HTTP command budget) are preserved.

No power-loss, OS-crash, physical-media/fsync, production durability, distributed
fencing, external exactly-once, payout, bank debit, chain finality, backend
adoption/acceptance or clean-room/independent verification is claimed. Inputs
are synthetic and files temporary/local within D-3. No sockets, external
services, new dependencies or execution activation. `durable`, execution and
production/truth false labels and `MOCK_TOKEN_REWARD_ONLY` provenance remain
unchanged. Product-policy values and recovery uncertainties stay UNDETERMINED;
no evidence-map grades, owner decisions or operational count change.

Deviations: fetch omitted under the supervisor's explicit no-network instruction;
remote freshness remains unverified. Crash-case traceback checks use the actual
`code(...)` helper assertions rather than an imagined returned error-code
mismatch; the initial expectations were corrected and tests rerun. No other
design or scope deviation and no product/resource decision required.
