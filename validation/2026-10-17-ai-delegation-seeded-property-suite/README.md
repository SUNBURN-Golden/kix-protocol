# ai-delegation-seeded-property-suite

Node: `plan-plan-ai-delegation-seeded-property-suite`. Adds a seeded, stdlib-only property suite for `AiDelegationMock`: `reference/ai_delegation/test_ai_delegation_properties.py` and its non-test support module `reference/ai_delegation/ai_delegation_property_support.py`.
Issue: none. Depends on: `ai-delegation-contract-mock`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792193921 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `e291a88211c45ee7285fd8abebcc6ef92bc39f23` (`git fetch origin main` succeeded; no delta).

**This suite is builder-authored. It is not an independent PASS. MOCK only: no AI service, no grant on chain, no execution, no grade change.** Fixture numbers are synthetic, not policy values. Contract section 9 values (product limits, period length, aggregation, suspend/resume) stay UNDETERMINED. Delegated execution stays disabled.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. `ai_delegation_mock.py`, `test_ai_delegation_mock.py`, `readiness/`, `docs/contracts/`, `reference/v0.3-rc1/`, `.aiops/`, `.github/`, `docs/tasks/` and `runtime/` are unchanged.

## What the suite does

- Fixed `SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)`, `random.Random(seed)` only, every choice over lists in a fixed order. No wall clock, no OS entropy, no network, no files. Final digests of all seeds are identical under `PYTHONHASHSEED` 0, 1, 2.
- The oracle (`Model`, in the support module) is typed in from `AI_DELEGATION_AUTHORITY.md` sections 3-8 and never calls the mock. Constants (money ceiling, 11 false flags, allow levels, deny table, phases, 26 codes) are re-typed; `ContractConstantTests` compares them with the module.
- `Driver(seed).run()` interleaves every public operation (issue, revoke, decide, the five tools, deny and unknown tools, `attempt_execution`, views, AI and stranger actors, invalid amounts, ids and `now`) with at most one deliberate defect per step. Per call: a raise must be `AiDelegationError` with a code in the oracle's set of violated predicates and in the reachable section 8 codes; `state_digest` and `canonical_state` must be unchanged after a rejection; after a success `canonical_state` equals the model and `state_digest` is sha256 of the canonical JSON; running sums are recomputed independently from `canonical_state`; ids only grow; generations are gap-free with one ACTIVE per pair; every view passes the envelope check; mutating a returned view does not change the digest. After each revoke the revoked grant is probed at three in-period `now` values.
- Coverage guard (`test_coverage_guard_op_families_and_codes`): every op family and outcome kind occurs, the union of observed codes equals the 25 reachable codes (`MOCK_INVARIANT` is constructor-only and has a directed test), and all five proposal phases are seen.

| Property | Where |
|---|---|
| (a) caps, boundary +/-1, split, share return | `CapTests` (seeded run + directed cumulative/per-action/count/reject/withdraw/approve) |
| (b) inclusive period | `PeriodTests` (60 random windows, both ends and +/-1, decide re-check) |
| (c) revocation | `RevocationTests`, probes in `Driver.probe_revoked`, no-delete and no-revive audit in `Driver.audit` |
| (d) rejected calls | every `Driver.step`; `AtomicityAndCodesTests` |
| (e) idempotency | `IdempotencyTests` (every binding field, permuted lists, replay after revocation) |
| (f) tools, EXECUTE, AI actors, flags | `AuthorityAndInertnessTests` |
| (g) command-log replay | `ReplayDeterminismTests` (fresh mock, every digest and result, reversed registries, perturbed-log control) |

## AGENTS.md section 7: existing coverage first

I read the bodies of `test_caps_count_open_proposals_and_release_on_reject_or_withdraw`, `test_period_boundaries`, `test_revocation_is_immediate_and_keeps_history`, `test_next_generation_requires_revoke` and the idempotency tests; the others by name and assertions.

| Property | Class | Existing tests (exact names, `test_ai_delegation_mock.py`) | What this suite adds |
|---|---|---|---|
| (a) caps | partially covered | `test_caps_count_open_proposals_and_release_on_reject_or_withdraw`, `test_per_action_boundary` | independent running sum after every seeded step; +/-1 over {1, 2, 7, 100, 10**12}; random splits; change proposals consume count |
| (b) period | partially covered | `test_period_boundaries`, `test_decide_rechecks_grant_and_approval_does_not_execute` | 60 random windows, random far `now`, seeded `now` near both ends |
| (c) revocation | partially covered | `test_revocation_is_immediate_and_keeps_history`, `test_next_generation_requires_revoke`, `test_ai_cannot_issue_widen_reissue_or_revive` | probes after every seeded revoke; no-delete, no-revive and monotone-phase audit after every step |
| (d) rejection atomicity and codes | partially covered | per-test `fails()` helper (digest only) | digest and `canonical_state` compared around every rejection, code checked against the oracle's set |
| (e) idempotency | partially covered | `test_grant_idempotency`, `test_proposal_idempotency` | every binding field, permuted lists, `subjects` omitted vs `[]`, replay after revocation, cross-grant reuse |
| (f) tools, flags, AI actors | partially covered | `test_denylist_and_unknown_tools`, `test_execute_authority_and_attempt_are_disabled`, `test_ai_cannot_decide_and_strangers_are_rejected`, `test_flags_remain_false`, `test_tool_level_follows_the_grant` | every deny tool, EXECUTE in any position, attempt with arbitrary actors and ids, envelope on every seeded result |
| (g) determinism | not covered | none (the mock has no journal or restore) | command-log replay on a fresh mock, every intermediate digest and result |
| DLG-10, 11, 12, 31 | sufficiently covered | `test_allowlist_is_disjoint_from_protocol_commands`, `test_mock_has_no_v03_import`, `test_execute_authority_and_attempt_are_disabled` | cited as covered elsewhere in `TraceabilityTests` |

## Negative controls

In `NegativeControlTests`, each control patches an attribute in memory with `unittest.mock.patch.object` (no source edited), runs the seeded drivers and requires `AssertionError`, not `AiDelegationError`; afterwards `assertIs` shows the original restored. Observed first failure messages (seed 1 first):

| Control | First oracle failure |
|---|---|
| `_require` no-op for `CUMULATIVE_EXCEEDED`, `_invariant` silenced | `call_tool accepted but the contract says CUMULATIVE_EXCEEDED` |
| `_require` no-op for `COUNT_EXCEEDED`, `_invariant` silenced | `call_tool accepted but the contract says COUNT_EXCEEDED` |
| `_require` no-op for `GRANT_REVOKED` | `call_tool raised GRANT_NOT_CURRENT, expected one of ['GRANT_REVOKED']` |
| `revoke_grant` restores PROPOSED after voiding | `canonical_state after revoke_grant differs from the contract model` |
| rejected `call_tool` bumps `_seq` before re-raising | `rejected call_tool (INVALID_ID) changed state_digest or canonical_state` |

## AGENTS.md section 8: discrepancy classes

No class C (explicit contract violation) found. No blocker. Reproduced in this session:

| # | Behaviour | Class | Handling |
|---|---|---|---|
| i | Decide-time `PER_ACTION_EXCEEDED`, `CUMULATIVE_EXCEEDED`, `COUNT_EXCEEDED`, `LIMIT_REQUIRED` never occur through the public API (grants are immutable, proposals are admitted under the same limits). Contract DLG-27 lists the re-check. | B | `test_b_decide_time_cap_codes_are_unreachable_from_the_public_api`; the oracle applies the re-check |
| ii | An authority list of four or more entries containing `EXECUTE` gives `INVALID_ID`; contract DLG-03 says `EXECUTE_AUTHORITY_DISABLED`. Both reject and record nothing. | B | oracle accepts either code for 4+ entries |
| iii | Non-list or duplicate scope lists give `INVALID_ID` or `SCOPE_VIOLATION`; section 8 names no exact code. | B | set membership |
| iv | The share returned by a void is not observable once the grant is revoked. | B | `test_b_the_share_of_a_void_is_not_observable_after_revocation` |
| v | Precedence among several violated predicates is set membership only, except the section 7 order. | B | oracle set |

## Changed paths

| Path | Change |
|---|---|
| `reference/ai_delegation/test_ai_delegation_properties.py` | New. 12 test classes, 47 tests (22 existing + 47 = 69 in the package). |
| `reference/ai_delegation/ai_delegation_property_support.py` | New non-test support: seeds, typed tables, `Model`, `Driver`. ASCII, stdlib plus the mock. |
| `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md` | This record. |
| `docs/README.md` | One index bullet. |

No workflow edit: the `ai_delegation` entry in the `protocol.yml` discover loop picks up the new file. The support module name is unique because `readiness/ai_delegation_wrap.py` puts this directory on `sys.path`.

## Commands actually run

All run from the repository root with `PYTHONDONTWRITEBYTECODE=1` after the last edit to the suite (fix round 1 removed one vacuous assertion).

| Command | Result |
|---|---|
| `PYTHONHASHSEED=0 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Ran 69 tests, OK (3.3 s) |
| same with `PYTHONHASHSEED=1` | Ran 69 tests, OK (2.6 s) |
| same with `PYTHONHASHSEED=2` | Ran 69 tests, OK (2.6 s) |
| same with `PYTHONHASHSEED=random` | Ran 69 tests, OK (2.7 s) |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Ran 64 tests, OK |
| `python3 scripts/check_delegation_layer_matrix.py` | exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| `python3 scripts/check_docs_index.py` | exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` (matches lock) |
| `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` (matches lock) |
| `git status --short` | only the four allowed paths changed (two new reference files, this record, `docs/README.md`) |

Not run: Cargo steps (no Rust touched; the locked-blob check is the substitute), Sui, Node and ZK steps. Exact-head CI run IDs are recorded in the PR closure comment (AGENTS.md section 11), not in this file.

Note on the negative controls for cumulative and count caps: they also silence the mock's own `_invariant`, otherwise `MOCK_INVARIANT` fires before the oracle is reached. They show the oracle catches a silenced cap check once the mock's own invariant is also off; the revocation and atomicity controls need no such patch.

## Non-claims

Builder-authored, not an independent PASS. MOCK only; no AI service, no grant on chain, no execution, no grade change, no durability. A command-log replay equals this process's own recomputation, not a journal or restore. Random coverage is a fixed corpus of 8 seeds, not exhaustive.
