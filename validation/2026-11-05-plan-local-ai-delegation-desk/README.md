# plan-local-ai-delegation-desk — builder validation

Task ID: `plan-local-ai-delegation-desk`. Task document: the supervisor-provided
node specification and read-only design plan in the executing session; no issue
or current `docs/tasks/` document exists for this loop-proposed node. Source
planner run: `1793857074`. This is not ASTRA program mode.

## Identity and gates

- Branch: `agent/kix-plan-local-ai-delegation-desk`.
- Observed local `origin/main`, starting branch HEAD and base:
  `b3d3a554c668457532fd6a044410dfab8ce2fb7d` (equal; no local base delta).
- Fetch: **NOT_RUN**, explicitly prohibited by the supervisor's no-network rule.
  Remote freshness is unverified. No rebase or base change was performed.
- Implementation/final committed head: **not created**; supervisor owns commits.
  This record describes uncommitted work on the starting HEAD, not CI for a future
  implementation SHA. Final task SHA must be recorded by the supervisor.
- Merge SHA / post-merge checks: **N/A**, no merge.
- Exact-head KTX CI run ID/status/conclusion: **NOT_RUN / unverified**.
- Exact-head KIX CI run ID/status/conclusion: **NOT_RUN / unverified**.
- A2 non-author exact-final-head review: **pending**, not self-certified here.
  No merge-ready claim or permission to publish/merge is supplied.

The shared control-plane pointer is a pending candidate, not runtime activation.
No GitHub, network, commit, push, issue, PR or comment action was performed.

## Existing coverage mapped before adding tests

Existing tests are under `reference/ai_delegation/` and remain unchanged.

| Requirement | Existing coverage / classification before desk | Added evidence for the gap |
|---|---|---|
| Seven explicit methods; isolated session | Domain sufficiently covered; session **not covered** | `test_delegation_session`: exact public surface/signatures, direct mock parity across all journeys, same-object forwarding/error propagation once, registry forwarding and session isolation |
| Receipts, inert proposals and false flags | **Partially covered**: `test_ai_delegation_mock.AiDelegationMockTests.test_query_does_not_change_state_and_propose_is_a_memo`, `test_flags_remain_false`, `test_grant_change_memo_does_not_widen_the_grant`; serialized desk absent | Complete CLI lifecycle receipt/view expectations; all eleven false flags, provenance, lifecycle and `effects_executed` |
| Contract refusals and disabled execution | Domain **sufficiently covered**: `test_denylist_and_unknown_tools`, `test_tool_level_follows_the_grant`, `test_execute_authority_and_attempt_are_disabled`; `test_rejection_atomicity.RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | Boundary transcript pins literal serialized codes, including `EXECUTE_AUTHORITY_DISABLED` and `DELEGATED_EXECUTION_DISABLED` |
| Replay and binding conflicts | Domain **sufficiently covered**: `test_grant_idempotency`, `test_proposal_idempotency`, property suite `IdempotencyTests`; `test_returned_data_isolation.ReturnedResultReplayTests` | Replay CLI transcript pins duplicate current records, both binding conflicts, first revocation reason and replay after decision/withdrawal/revocation |
| Single-fetch / no retries | Desk **not covered** | Session forwarding spies and CLI selected-call counts: one call per supplied line, zero implicit views/retries, zero calls on malformed envelopes |
| Strict JSON, schemas and stream behavior | Desk **not covered** | `test_delegation_serialization` and `test_delegation_cli`: duplicate keys, non-finite/overflow numbers, invalid Unicode/nesting/non-JSON Python values, all argument shapes, exact fixture schema, nested values left to mock, file/stdin/repeat equivalence, exits 0/1/2, malformed-stop and explicit continuation |
| Existing suite unchanged | **Sufficiently covered** by existing discovery command | Baseline before edits: 85 tests passed; final discovery adds the new desk tests |
| Index/checkers | Existing checker infrastructure **partially covered** desk discovery/index gap | Direct docs links, checker checks/self-tests and local architecture/KTX equivalents |

The domain coverage above is reused, not duplicated as a new independent model.
Builder-authored wrapper parity is source-informed evidence, not clean-room or
non-author review. No new Rust or kernel tests were needed for this Python desk.

## Actual commands and results

[commands.json](commands.json) records executed verification commands, return
codes and captured stdout/stderr (or links to captured transcripts). The initial
baseline and narrow failure/correction are explicitly labeled summaries of their
observed results. Read-only setup commands recorded HEAD/branch/local main and
read governance, contracts, existing tests and workflow definitions.

All Python verification ran with `PYTHONDONTWRITEBYTECODE=1`. The targeted
unittest command additionally used `PYTHONPATH=reference/ai_delegation`.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` (before edits) | exit 0; 85 existing tests passed |
| `PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_session test_delegation_serialization test_delegation_cli` (first run) | exit 1; 19 tests, 1 incorrect expected memo shape; corrected expectation for existing `subjects=None` normalization |
| Same targeted command (corrected run) | exit 0; 19 tests passed |
| Same targeted command (captured verification run) | exit 0; 19 tests passed |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` (with desk) | exit 0; 104 tests passed, comprising unchanged 85 existing tests plus 19 new tests |
| `python3 scripts/check_docs_index.py` and separate `--self-test` invocation | both exit 0 |
| `python3 scripts/check_status_register.py` and separate `--self-test` invocation | both exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py` and separate `--self-test` invocation | both exit 0; existing map statuses/owners unchanged |
| `python3 scripts/check_delegation_layer_matrix.py` and separate `--self-test` invocation | both exit 0 |
| `python3 scripts/check_contract_error_codes.py` and separate `--self-test` invocation | both exit 0; error-code coverage is not ordered-precedence conformance |
| `python3 scripts/check_class_b_index.py` and separate `--self-test` invocation | both exit 0; textual index only |
| `python3 scripts/check_ci_test_discovery.py` and separate `--self-test` invocation | both exit 0; existing discover wiring reaches the new test modules |
| `python3 scripts/check_ci_checker_wiring.py` and separate `--self-test` invocation | both exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; workspace resolution requires uncached `bcs` for `kix-bcs1`; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; same missing offline `bcs`; Clippy analysis not reached |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0; no formatting changes |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | exit 101; same missing offline `bcs`; no dependency tree certified |
| `python3 reference/ai_delegation/delegation_cli.py --fixture reference/ai_delegation/fixtures/delegation_session.json --requests reference/ai_delegation/fixtures/lifecycle.jsonl` | exit 0; 19 responses captured in [lifecycle.stdout.jsonl](lifecycle.stdout.jsonl) |
| Same CLI/fixture with `--requests reference/ai_delegation/fixtures/boundaries.jsonl` | expected exit 1 for domain refusals; 52 responses in [boundaries.stdout.jsonl](boundaries.stdout.jsonl) |
| Same CLI/fixture with `--requests reference/ai_delegation/fixtures/replay.jsonl` | expected exit 1 for binding conflicts; 28 responses in [replay.stdout.jsonl](replay.stdout.jsonl) |
| Byte-comparison Python program (exact `python3 -c` command in `commands.json`) | exit 0; both locks match and 108 frozen files match HEAD, with no added files |
| `git diff --check` | exit 0 |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks .github reference/ai_delegation/ai_delegation_mock.py reference/ai_delegation/ai_delegation_property_support.py` | exit 0; no changes in protected/governance/mock paths |
| `git rev-parse HEAD origin/main` | both remain `b3d3a554c668457532fd6a044410dfab8ce2fb7d` |

The CLI tests also verify file/stdin/repeated-process byte equality, every
complete lifecycle receipt and retained view, replay snapshots and first reason,
both execution refusal codes, malformed-stop and single-fetch/no-retry behavior.
Expected transcript exit 1 is a successful refusal demonstration, not a malformed
stream or failed verification test.

Workflow definitions inspected: `.github/workflows/protocol.yml` and
`.github/workflows/ktx-kernel.yml`. The selected stdlib checks and reference
discovery are the protocol equivalents applicable to the changed Python/docs
paths. The architecture/kernel/Clippy/format commands match the KTX steps, with
offline resolution to honor the no-network rule. Offline Cargo failed before
compilation because workspace resolution includes `kix-bcs1`, even with
`-p kix-kernel`. No runtime source or Cargo file changed. No cache installation,
network retry or CI alteration was attempted. Full protocol CI (including
untouched Rust/Move/SDK/ZK paths) and hosted exact-head checks remain unverified.

## Protected bytes and changed paths

Before edits, `git status --short` was empty. `git hash-object` matched both locks:

| Path | Before blob | After blob |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Frozen `reference/v0.3-rc1` starting Git tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. After work, all **108** files have
the same Git blob hashes as HEAD, and the worktree contains exactly that same
frozen path set. All existing mock/support/test files, kernel/runtime files,
contracts/status maps, `.github/`, `.aiops/` and task documents remain unchanged.
Final-merge blob verification is N/A because this builder does not merge.

Complete changed-path list (17 files):

```text
docs/README.md
reference/ai_delegation/README.md
reference/ai_delegation/delegation_cli.py
reference/ai_delegation/delegation_fixture.py
reference/ai_delegation/delegation_session.py
reference/ai_delegation/fixtures/boundaries.jsonl
reference/ai_delegation/fixtures/delegation_session.json
reference/ai_delegation/fixtures/lifecycle.jsonl
reference/ai_delegation/fixtures/replay.jsonl
reference/ai_delegation/test_delegation_cli.py
reference/ai_delegation/test_delegation_serialization.py
reference/ai_delegation/test_delegation_session.py
validation/2026-11-05-plan-local-ai-delegation-desk/README.md
validation/2026-11-05-plan-local-ai-delegation-desk/boundaries.stdout.jsonl
validation/2026-11-05-plan-local-ai-delegation-desk/commands.json
validation/2026-11-05-plan-local-ai-delegation-desk/lifecycle.stdout.jsonl
validation/2026-11-05-plan-local-ai-delegation-desk/replay.stdout.jsonl
```

## Contract findings, deviations and remaining uncertainty

No new contract violation or contract-undefined semantics are introduced by the
desk. **A5 remains an existing attributed class-C discrepancy**, as recorded in
[the October 26 addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure)
and [October 27 closure](../../docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md).
Contract §7 places grant-agent binding before tool lists; the mock checks actor
registration, tool lists, then grant-agent binding. New normative fixtures avoid
registered wrong agents paired with denied/unknown tools. That simultaneous case
is neither repaired nor claimed conforming here. The plan explicitly makes A5
independent of this delivery; its resolution belongs to Astra, with User
authorization of resulting scope/contract changes and User merge. Missing-grant
binding remains UNDETERMINED with that same owner; existing simultaneous-error
set-membership characterizations are not promoted to precedence evidence.

Deviations: fetch and publication/CI actions are omitted under the explicit
supervisor rule. No task document was created or changed. The first narrow run
found an incorrect test expectation for existing memo scope normalization
(`subjects=None`); only the test expectation was corrected. Any unavailable
local tool/dependency is recorded as such; no installation or network fallback.

Implementation follows the design plan without a surface or behavior deviation.
Local builder READY means the Python desk and its checks are complete for
supervisor handoff; it does not imply passing Rust checks, exact-head hosted CI,
independent review or merge readiness. The missing offline Cargo dependency is
an environment limitation, not a request to unlock any product capability.

Product limits and permitted surfaces remain UNDETERMINED (Astra); identity
policy remains with Astra/User; authoritative time and chain cuts with
`k1-cut-proof`/RS-3a; legal authority with legal review/User, per contract §9.
Synthetic fixtures establish no policy values. No changes to these owners,
contracts, status labels, readiness, protocol commands or runtime activation.

Non-claims: in-memory, sequential, synthetic only. No durability, distributed
fencing, bank exactly-once, chain finality, legal compliance, production readiness,
real funds, PG/bank/KYC/AI service calls, public endpoints, Sui testnet/mainnet,
storage/replication/consensus engine, coin/TIX module, credentials or signing.
`attempt_execution` remains disabled; approval remains an inert memo. No full
hosted workflow, independent A2 audit or exact-head CI result is inferred from
local checks. Follow-up gates belong to the supervisor: commit identity,
non-author review, exact-head KTX/KIX CI and any eventual human merge decision.
