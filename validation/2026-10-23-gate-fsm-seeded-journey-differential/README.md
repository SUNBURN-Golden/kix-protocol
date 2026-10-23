# Seeded gate/FSM journey differential

Node: `plan-plan-gate-fsm-seeded-journey-differentia`. Resumed session date:
2026-10-24 (Asia/Seoul); the directory retains the task's requested 2026-10-23 date.
Task input: supervisor-supplied node specification, read-only design plan and
owner Option 2 decision in the executing prompt. No issue or task document
under `docs/tasks/` exists for this node; those immutable inputs are untouched.
State: **READY for supervisor delivery**, based on local acceptance below.
This is not an exact-head CI or merge-ready verdict.

| Source anchor | Observed value |
|---|---|
| Local `origin/main` ref on resume | `f50047a902f9e4f2e6a25e904f6f89ad758eb8c0` |
| Task base / initial implementation HEAD / unchanged final task HEAD | `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af` |
| Branch | `agent/kix-plan-plan-gate-fsm-seeded-journey-differentia` |
| Base delta | Base is the merge base, 27 commits behind the local `origin/main` ref; no rebase or merge performed |
| Default / CI-version Python | 3.13.5 / 3.12.15 |
| Exact-head KTX / KIX CI | NOT_RUN; no run ID, status or conclusion available |
| Merge / post-merge CI | Not applicable; no merge performed |

Changes remain uncommitted for the supervisor. `git fetch origin main` was
NOT_RUN because the explicit supervisor rule forbids network actions; the
remote-tracking ref is a local observation, not a claim of remote freshness.
The existing draft was inspected and retained. The owner-authorized loopback
capability works on resume; `DECISION_REQUIRED.md` was already absent.

The prior stopped attempt recorded socket-denial failures: 6 new-class tests
with 11 errors / 1 failure and the 88-test acceptance command with 41 errors /
1 failure (both interpreters). Its booking reference suite also recorded one
socket error. Those were host-blocked results, not passes. The fresh, unchanged
HTTP/subprocess test runs below replace that outstanding acceptance gap. No
transport facade, patched assertion, skipped test or diagnostic substitute was
used for the resumed acceptance runs.

## Coverage before this change

| Requirement | Existing evidence | Classification before this node |
|---|---|---|
| 44 FSM bindings and unchanged 84-command catalogue | `TransportTests.test_fsm_commands_match_a_direct_machine_call`, `OpenApiAndSchemaTests`, OpenAPI checkers | Sufficient for catalogue/binding; partial for stateful differential |
| Admission journey | `TransportTests.test_admission_happy_path_over_http` | Partial: one fixed journey, no resale/credit interleave |
| Replays / operation identity | `TransportTests.test_fsm_idempotency_key_replays_without_using_operation_id`, `test_representative_commands_match_local_call`, `test_http_idempotency_key_header_is_not_consulted` | Partial: no all-machine journey replay conflicts |
| Restart | `TransportTests.test_restart_drops_in_memory_state`, readiness fault tests | Partial: core subprocess restart; readiness persistence is a different boundary |
| Resale/entry refusal after transfer | `AdmissionFsmTests.test_transfer_then_entry_rejects_both_presentations` | Sufficient reference semantics; missing gate differential |
| Settlement/credit rejection atomicity | `reference/{settlement_f01_f03,credit_advance_f04}/test_*_rejection_atomicity.py` | Sufficient reference characterization; missing gate/shadow prefix comparison |
| Seed corpus, shrinking/replay, gate journals across all machines | No equivalent in `integration_gate/test_http_gate.py` | Not covered |

## New fixtures and coverage gates

`SeededJourneyDifferentialTests` lives in `integration_gate/test_http_gate.py`,
so the unchanged CI command discovers it. Support is in
`integration_gate/journey_support.py`. Fixed seeds: **1, 2, 3, 5, 8, 13, 21, 34**;
**60 steps per seed**, including an explicit restart token. A private
`random.Random(seed)` chooses eligible lanes and replay order; no wall clock
or global random state supplies inputs. Bodies, dependent settlement claim and
resale holder/version are captured concretely by a separate generator host.

Each seed earns, from observed outcomes, all of these labels:

- `boundary:reservation->resale`, `boundary:reservation->settlement`,
  `boundary:settlement->credit`.
- `replay:identical:<machine>`, `replay:idempotency_conflict:<machine>`,
  `replay:opid_reuse:<machine>`, `out_of_order:<machine>` for all five machines.
- `replay:operation_id_conflict`, `restart`; stale work on all five machines
  rejects after restart and a reused clock key becomes a fresh success.

| Seeds | Additional boundary label | Expected branch |
|---|---|---|
| 1, 3, 5, 13, 21 | `boundary:resale->admission:stale` | Transfer succeeds; admission using observed holder/version rejects `STALE_VERSION` |
| 2, 8, 34 | `boundary:resale->admission:consume_first` | Admission succeeds and consumes; later listing rejects `ALREADY_CONSUMED` |

The driver compares complete status/payload/error results per step, all five
machines' digests, canonical views and exported journals after every prefix,
and both core snapshots. Rejections leave every machine snapshot unchanged;
core steps leave FSM state unchanged. Every restart checks a fresh empty host
and compares the departing segment before evidence can be discarded. One
subprocess test replays seed 1 before and after process replacement. Receipt
non-production labels stay false. Catalogue assertions pin 84 = 40 core + 44 FSM,
validate every body and run the unchanged OpenAPI validator.

Failure messages include seed, step, kind, action and concrete JSON after
deterministic remove-one-step shrinking. Format:
`{"seed": <integer>, "steps": [{"kind": ..., "lane": ..., "operation_id": ..., "actor": ..., "action": ..., "body": {...}}]}`.
`dump_failure` / `load_failure` preserve the full input, including restart tokens;
the support module documents replay. Shrinking recognizes the same mismatch
kind/action and lets infrastructure/schema errors propagate. A negative control
changes one shadow receipt, shrinks to a single replayable clock step, then
confirms that removing the injected divergence makes it pass.

## Commands and actual results

All commands ran from the repository root. The narrow class ran before the
broader checks. Every command in this table exited 0. The two default-Python
acceptance runs used the unchanged CI command; the 3.12 runs check CI's pinned
Python minor version too.

| Command actually run | Actual result |
|---|---|
| `git rev-parse origin/main HEAD`; `git branch --show-current`; `git merge-base HEAD origin/main`; `git rev-list --count HEAD..origin/main` | Anchors and 27-commit base delta above |
| `python3 --version`; `python3.12 --version` | Python 3.13.5; Python 3.12.15 |
| `python3 -m unittest integration_gate.test_http_gate.SeededJourneyDifferentialTests -v` | 6 tests, OK (5.280 s) |
| `python3.12 -m unittest integration_gate.test_http_gate.SeededJourneyDifferentialTests -v` | 6 tests, OK (5.205 s) |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` (run 1) | 88 tests, OK (14.150 s); self-test: pass |
| Same `python3` command (run 2) | 88 tests, OK (11.841 s); self-test: pass |
| `python3.12 -m unittest integration_gate.test_http_gate readiness.test_faults` (run 1) | 88 tests, OK (12.401 s); self-test: pass |
| Same `python3.12` command (run 2) | 88 tests, OK (10.022 s); self-test: pass |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 180 tests, OK |
| Same discover command for `booking_resale_admission` | 162 tests, OK (including the existing loopback test) |
| Same discover command for `credit_advance_f04` | 142 tests, OK |
| Same discover command for `ai_delegation` | 70 tests, OK |
| Same discover command for `token_reward` | 156 tests, OK |
| Stdlib/checker loop below (`python3`, plain and self-test) | All 31 invocations passed, including status register, docs index and both OpenAPI checkers |
| `python3 scripts/check_docs_index.py`; same with `--self-test` (after report/register updates) | Pass; scanned=208, indexed=173, allowlisted=35; self-test: pass |
| `python3 scripts/check_status_register.py`; same with `--self-test` (after report/register updates) | Pass; paths=334, ev_ids=15, original32=32; self-test: pass |
| `git diff --check` | Pass; no whitespace errors |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both locked blobs match the table below |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 runtime .github .aiops docs/tasks` | Pass; no tracked protected-path changes |
| `git ls-files --others --exclude-standard -- reference/v0.3-rc1 runtime .github .aiops docs/tasks` | Empty; no untracked nonignored protected-path files |

Exact reference-suite loop (each command's output was redirected to a local
scratch log and checked before continuing):

```bash
for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do
  PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"
done
```

Exact checker list executed from `protocol.yml` (plain and self-test):

```bash
for checker in check_status_register check_rs_profile_traceability check_read_model_source_map check_docs_index check_i12_proof_ids check_delegation_layer_matrix check_rs_predicate_evidence_map check_rs_im_evidence_map check_tl_predicate_evidence_map check_contract_error_codes check_adapter_identity_map check_v5_transition_evidence_map check_readiness_evidence_map check_openapi_contract check_integration_gate_openapi; do
  python3 "scripts/$checker.py" || exit "$?"
  python3 "scripts/$checker.py" --self-test || exit "$?"
done
python3 scripts/check_stage5_host.py --self-test
```

OpenAPI output: `commands=84 core=40 fsm=44`, contract SHA-256
`ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`,
Git blob `619ae21c82ca3df5661bd3831613f15fa65225ff`;
integration-gate `productionEndpoint=false publicHost=false`.

HTTP output was retained in local scratch logs:
`/tmp/kix-journey-resume-full-run-{1,2}.log`,
`/tmp/kix-journey-resume-full-py312-run-{1,2}.log`;
3.12 narrow output: `/tmp/kix-journey-resume-narrow-py312.log`.
The command/result table is the portable evidence; these scratch paths are not
committed artifacts.

## Protected paths and final verification

Before/after locked blobs (from `git hash-object`):

| File | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git rev-parse HEAD:reference/v0.3-rc1` gives tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Protected paths are compared against
the actual task base/HEAD, since unrelated upstream changes exist in the local
`origin/main` delta. No gate, catalogue, OpenAPI, FSM, readiness, runtime, CI,
`.aiops/`, `docs/tasks/` or reference implementation was edited.

## Deviations, characterizations and limits

- The no-network supervisor instruction overrides §1 fetch; no remote freshness
  or exact-head CI evidence is claimed. The 27-commit base delta is reported,
  not silently integrated. Supervisor integration/review remains outstanding.
- FSM `operationId` is ignored (`server._perform_fsm` and existing transport
  tests); the same-ID/different-body verdict follows the body key, never
  `OPERATION_ID_CONFLICT`. This is a class B characterization, not new semantics.
  The interleaved existing core `advance_clock` command exercises the real
  `OPERATION_ID_CONFLICT` path. No class C discrepancy was found.
- The design's post-transfer admission path is a refusal, as the existing
  transfer test requires. Even seeds also cover accepted authorization and
  consumption before a resale attempt. Clock mutations change the subject,
  preserving the fixture clock/window.
- Credit draws precede distribution so the captured committed face stays open.
  Fee 500 on gross 10001 is an existing synthetic fixture, not a policy decision.
- The prior draft's socket blocker is resolved by the owner Option 2 decision;
  no decision file remained to remove on resume. The test implementation needed
  no fix after loopback became available.
- No production durability, clean-room independence, readiness-journal FSM
  support, real funds, PG/bank/KYC, chain finality, public endpoint, deployment,
  concurrency/load or performance claim. Remaining uncertainty includes behavior
  outside these fixed seeds and differences shared by the source-informed host.
- Not run: Rust workspace/Clippy/fmt (no Rust change), SDK/Move/ZK/localnet and
  storage/runtime jobs (untouched paths), hosted KTX/KIX CI, non-author/Astra
  review, merge and post-merge verification. The applicable local equivalents are
  the HTTP/readiness command, five offline reference suites and stdlib checkers.
- EV-GATE changes only its fixture cell and baseline sentence; no grade or
  operational count changes. No commit, push, issue, PR or comment was made.

Complete changed-path list:

- `integration_gate/journey_support.py`
- `integration_gate/test_http_gate.py`
- `docs/README.md`
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`
- `validation/2026-10-23-gate-fsm-seeded-journey-differential/README.md`
