# Local settlement reward observation adapter

Node: `plan-local-settlement-reward-adapter`. Input: the supervisor-supplied node
specification and read-only Sonnet design plan, planner run `1793327754`.
There is no task issue or current file under `docs/tasks/` for this node. This is
not ASTRA program mode and the node is not added to `.aiops/program.json`.

Cached `origin/main`, base and initial branch HEAD:
`fae08dca658774568358c55d9db879626f6bcea4`.
Branch: `agent/kix-plan-local-settlement-reward-adapter`. Initial worktree clean.
No local base delta. Remote freshness is unverified: the supervisor's explicit
no-network instruction overrides AGENTS §1's fetch instruction.

Implementation/final committed task head: not established (supervisor owns
commits). Merge SHA and post-merge checks: not applicable; nothing merged.

## Existing coverage mapped before new tests (AGENTS §7)

Paths below are under `reference/token_reward/` unless specified otherwise.

| Requirement | Existing evidence | Classification and adapter gap |
|---|---|---|
| Live COMMITTED settlement produces OBSERVED | `test_reward_fsm.py::test_live_settlement_view_field_names_match_and_can_be_read`, `test_source_kinds_require_a_committed_krw_snapshot` | Partially covered: caller supplies the snapshot; no configured binding/dispatch |
| Missing binding, unknown settlement, no identity inference or request substitution | No adapter exists | Not covered at adapter boundary |
| Non-COMMITTED produces no reward | `test_reward_rejection_atomicity.py::test_observe_source_not_committed_leaves_no_trace` | Partially covered: no live settlement phase matrix through adapter |
| Settlement and full pool view unchanged; observation only | Settlement FSM tests; `test_reward_fsm.py::test_flags_and_points_stay_non_transferable_on_every_phase` | Partially covered: cross-machine isolation untested |
| Unchanged replay returns first result | `test_snapshot_isolation.py::test_retained_snapshots_survive_later_transitions`, `test_mutated_first_results_do_not_change_state_or_replay` | Sufficiently covered in machine; live adapter replay remains a gap |
| Changed snapshot conflicts; rejected first-result semantics | `test_reward_rejection_atomicity.py::test_idempotency_conflict_leaves_no_trace`, `test_restore_forgets_stored_rejections` | Partially covered: live source advancement untested at adapter boundary |
| Rule version cannot replace identity | `test_reward_fsm.py::test_observe_under_a_new_rule_before_payout_does_not_create_a_second_id`, `test_rule_version_change_pays_once_unless_superseded` | Sufficiently covered in machine; adapter propagation remains a gap |
| Input/view/journal detachment | `test_snapshot_isolation.py` mutation matrix | Sufficiently covered; do not duplicate full matrix |
| Identifier, amount and version validation | `test_reward_rejection_atomicity.py::test_observe_reward_key_fields_leaves_no_trace`, `test_observe_invalid_id_leaves_no_trace`, `test_observe_invalid_amount_leaves_no_trace`, `test_observe_invalid_rule_version_leaves_no_trace` | Sufficiently covered in machine; verify adapter forwards inputs and binding validation reuses helpers |
| Import origin and path cleanup | `test_reward_fsm.py::SiblingImportPathTests` | Partially covered: new entrypoints need equivalent guards |
| Runnable offline integration example and CI discovery | No adapter example/tests | Not covered |

## Scope and delivery boundary

Internal in-memory observation only, with immutable copied synthetic fixture
bindings from stable source operation ID to settlement ID. Identifiers are not
inferred from settlement, trade or command IDs. Full live views pass unchanged to
the existing reward machine, which owns identity, validation and first results.
No automatic hold, eligibility, issuance, refund interpretation or payout.

Policy values remain **UNDETERMINED — Astra**; approver designation belongs to
the **User**; chargeback periods remain **UNDETERMINED — payment provider**.
Fixture numbers and rules are explicit synthetic inputs, not policy decisions.

Required before merge-ready: A2/non-author review of the supervisor's exact final
head and both KTX kernel verification and KIX protocol verification completed with
success on that head. Run IDs/status/conclusions: **not queried / unavailable**
(no GitHub/network action authorized). Local readiness is not merge readiness.

## Verification

Python `3.13.5`; `rustc 1.98.1 (48a229cea 2026-09-01)`;
`cargo 1.98.1 (797e8a9bc 2026-08-05)`. Rust matches the inspected workflows'
`1.98.1` pin. Local Python differs from hosted `3.12`; no hosted equivalence is
claimed. All Python verification used `PYTHONDONTWRITEBYTECODE=1`. The temporary
foreground command recorder also set `CARGO_NET_OFFLINE=true`; Cargo commands
explicitly used `--offline`. No dependencies were fetched or installed.

The commands below are the actual child commands (the recorder only captures
stdout/stderr, exit code and elapsed time under
`/tmp/kix-settlement-reward-evidence/`). All were run in the node worktree, narrow
tests first, then the two suite discoveries and applicable workflow equivalents.
No shell background jobs were used.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_settlement_reward_adapter.py -v` (first run) | Exit 1: 12 tests, one failure and one error. New test reused a rejected key across changed requests; another incorrectly expected provenance in the pool view. |
| Same narrow command (second run) | Exit 1: 12 tests, one failure. Corrected key isolation; remaining test assumed scalar pool credits/spends instead of the existing view shape. |
| Same narrow command (third run) | Exit 0: 12 tests passed after fixing only new test expectations. |
| `python3 reference/token_reward/example_settlement_reward.py` | Exit 0: deterministic synthetic JSON, explicit binding, COMMITTED settlement, OBSERVED non-transferable POINT_F4 reward, unsupported external execution and false execution/finality flags. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0: 180 tests passed (includes all 12 adapter tests). |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0: 196 tests passed. |
| `python3 scripts/check_docs_index.py` | Exit 0: scanned=320, indexed=285, allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0: pass. |
| `python3 scripts/check_status_register.py` | Exit 0: paths=457, ev_ids=15, original32=32. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0: 49 rows, 58 citations; existing statuses unchanged. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0: pass. |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0: 27 rows/headings, 110 citations; existing statuses unchanged. |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0: 33 negative controls passed. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0: 25 contracts; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0: 16 negative controls passed. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0: scripts=35, plain=34, self_test=35, self_test_only=1. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0: 13 negative controls passed. |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0: seven reference suites reached, including nine token-reward test files; new module reached by unchanged protocol workflow discovery. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0: 18 negative controls passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0: 84 commands, pinned bytes unchanged. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0: pass. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0: v5 + KTX-R1 dependency gate OK; durability/performance not certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0: seven tests passed. |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0: 18/18 archives present, missing=[]; presence alone is not compilation proof. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0: 139 passed, zero failed/ignored across nine result groups (including doc tests). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0: 339 passed, zero failed/ignored across 46 result groups (includes kernel; do not add these counts). |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0: no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. Check only; no formatting mutation. |
| `git diff --check` | Exit 0. |

After completing this report, `PYTHONDONTWRITEBYTECODE=1 python3
scripts/check_docs_index.py` and `git diff --check` passed again. A read-only
`python3` stdin check asserted a final newline and no trailing whitespace in all
four new files; it passed. `git status --short` showed exactly the five paths
listed below, and `git rev-parse HEAD` still returned the initial base SHA.

## Added evidence and changed paths

All new test methods below belong to
`reference/token_reward/test_settlement_reward_adapter.py::SettlementRewardAdapterTests`.
They are builder-authored, source-informed integration evidence, not independent
verification or an A2 review.

| New test | Gap addressed |
|---|---|
| `test_committed_bound_source_is_observed` | Real FSMs; spies prove one live read and one dispatch, identical snapshot object forwarded and identical response returned; complete stored view, derived identity, observation-only journal and no payout/approval. |
| `test_missing_binding_and_unknown_settlement_create_no_reward` | Exact adapter/settlement diagnostics, zero reward dispatch, empty reward IDs/journal, unchanged public state and later reuse of the same explicit key after lookup succeeds. |
| `test_non_committed_sources_create_no_reward` | Live INITIATED/AUTHORIZED/CAPTURED/FAILED/CANCELLED rejection matrix; no reward IDs/journal or public-state changes. |
| `test_source_selection_is_configuration_only` | Two distinct settlements; copied bindings withstand caller mutation; matching settlement/trade/command IDs confer no binding; forbidden request arguments cannot substitute snapshot, kind, settlement or machines. |
| `test_binding_identifiers_and_reward_key_reuse_existing_validation` | Existing identifier/key helpers reject malformed configuration/keys before source lookup. |
| `test_reward_inputs_are_validated_by_reward_machine` | Invalid amount, rule and idempotency inputs preserve existing machine errors/public state. |
| `test_unchanged_source_replays_first_result` | Duplicate metadata, unchanged journal/public state; original OBSERVED result remains replayed after an explicitly separate hold transition. |
| `test_changed_live_snapshot_conflicts` | Explicit settlement distribution changes its complete view; adapter rereads it, producing conflict and preserving the original reward snapshot. |
| `test_rule_version_cannot_replace_reward` | Same-key conflict, explicit new-key rule-version rejection and same-rule duplicate rejection; only the original reward identity remains. |
| `test_rejected_first_result_survives_source_advancement` | Repeated CAPTURED rejection retains its first fingerprint; after explicit COMMITTED advancement the same key conflicts; adapter never retries or substitutes keys. |
| `test_offline_example_output_and_flags` | Real subprocess entrypoint, deterministic output, complete unchanged snapshot, provenance, no pool movement/payout, flags false and non-transferability true. |
| `test_sibling_import_origins_and_path_cleanup` | Both machines/models originate in their own suites; temporary sibling path removed. |

Successful and rejected observations compare full settlement canonical state,
settlement journal and full reward pool view. The existing snapshot-isolation
suite covers the broader mutation matrix. Public canonical state omits rejection
cache entries; unchanged canonical state does **not** mean no internal trace.

Complete changed-path list:

- `reference/token_reward/settlement_reward_adapter.py` — internal adapter.
- `reference/token_reward/test_settlement_reward_adapter.py` — integration tests.
- `reference/token_reward/example_settlement_reward.py` — runnable offline example.
- `validation/2026-10-30-plan-local-settlement-reward-adapter/README.md` — this report.
- `docs/README.md` — one validation-record link.

## Preservation evidence

Before editing, a temporary read-only helper enumerated `git ls-files -z` and
hashed every tracked file except the authorized `docs/README.md` change. This
covered 1,121 paths, including all 108 `reference/v0.3-rc1/` files, the existing
FSM/model files, contracts, catalogue/SDK, workflows, `.aiops/**` and
`docs/tasks/**`. The helper additionally recorded both locked Git blobs.

Actual commands:

| Command | Result |
|---|---|
| `git status --short` (initial) | Exit 0, empty (clean). |
| `git rev-parse HEAD`; `git rev-parse origin/main` | Exit 0 each; both `fae08dca658774568358c55d9db879626f6bcea4`. |
| `git branch --show-current` | Exit 0: `agent/kix-plan-local-settlement-reward-adapter`. |
| `python3 /tmp/kix-settlement-reward-evidence/preservation.py > /tmp/kix-settlement-reward-evidence/before.json` | Exit 0, initial manifest. |
| `python3 /tmp/kix-settlement-reward-evidence/preservation.py > /tmp/kix-settlement-reward-evidence/after.json` | Exit 0, final manifest. |
| `cmp /tmp/kix-settlement-reward-evidence/before.json /tmp/kix-settlement-reward-evidence/after.json` | Exit 0: all 1,121 protected tracked paths and both blobs unchanged. |
| `sha256sum /tmp/kix-settlement-reward-evidence/before.json /tmp/kix-settlement-reward-evidence/after.json` | Both `a3c0201dcea9f8ebd2bbb0131400f8949d4b4a1977ab6ff9d932d525696200e3`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`; same before/after. |

Final-merge blob verification and main/push workflow evidence are not applicable
in this uncommitted, unmerged builder session.

## Contract classification, deviations and limits

- **A, matching:** existing reward identity/validation, complete source snapshots,
  immutable first results, rule-version duplicate rejection, pool separation and
  observation-only behavior. No explicit contract violation found.
- **B, undefined:** trusted synthetic fixture bindings do not establish
  authenticated commerce provenance or cross-machine concurrency semantics.
  No such guarantee is invented. Rejection-cache behavior is characterized using
  existing machine semantics; the adapter adds no journal or persistence.
- **Deviations:** no fetch or remote-head/CI query, because the supervisor forbids
  network/GitHub actions; no current task document exists, so the supplied spec
  remains the input. Local Python is 3.13.5 versus hosted 3.12. The adapter uses a
  type-only settlement import because both actual machines are injected; the
  runnable example uses the planned temporary sibling-import pattern with exact
  path restoration. No substantive design/scope deviation.
- No real funds, PG/bank/KYC call, public endpoint, chain execution, coin/TIX,
  secrets, storage engine or production runtime. No policy value, approval or
  chargeback period is selected. No refund interpretation or automatic reward
  lifecycle advance. No durability, distributed fencing, bank exactly-once,
  chain finality, legal compliance, production readiness or evidence-grade claim.
- Full hosted workflows (including unrelated SDK/Move/ZK jobs) were not run;
  relevant local equivalents passed. The supervisor must establish the final
  committed head, obtain A2/non-author exact-head review and verify both named
  repository workflows on that head before any merge-ready claim. No commit,
  push, PR, issue, comment, tag/branch mutation or merge was performed.

Builder handoff: implementation complete and locally verified; **not merge-ready**.

## PR fix round 1 — local revalidation (2026-10-30)

The supervisor supplied no concrete blocking finding and no failed-job log.
The review input says “review passed or unavailable”; this is not evidence that
independent review passed. A possible billing/runner refusal is unverified.
No code defect or local check failure was reproduced, so no implementation or
test change was made. This appendix is the only changed path in this round.
The coverage mapping and source-informed integration evidence above still apply;
no duplicate tests were added. No contract violation was found. Trusted fixture
bindings and cross-machine concurrency remain the characterized limits above.

Observed cached `origin/main` and task base:
`fae08dca658774568358c55d9db879626f6bcea4`.
Implementation and fix-round initial/final HEAD:
`9c90324ce21cabbbb68dcd9aed095a62b5ac3091`.
`git merge-base origin/main HEAD` returns the base above; the branch contains
one implementation commit beyond it. No base movement was made. These local
refs do not verify remote freshness. The supervisor prohibits fetch, all other
network/GitHub actions, commits, pushes and posts. The report remains uncommitted;
the supervisor will establish the next final task head.

All Python commands below ran with `PYTHONDONTWRITEBYTECODE=1` on Python 3.13.5.
Hosted Python 3.12 and the complete repository workflows were not run in this
round. Rust files were unchanged; the earlier Rust results above are historical
evidence, not reruns in this round. The offline example's output and command
logs are local temporary artifacts under
`/tmp/kix-settlement-reward-fix-round-1/`; they are not committed evidence.

| Exact command | Actual fix-round result |
|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_settlement_reward_adapter.py -v` | Exit 0; 12 tests passed. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; 180 tests passed, including the live-settlement field-name regression and 12 adapter tests. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 196 tests passed. |
| `python3 reference/token_reward/example_settlement_reward.py` | Exit 0; synthetic bound settlement COMMITTED, reward OBSERVED, execution/finality flags false. The adapter test also verifies output and unchanged pools. |
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=320, indexed=285, allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; pass. |
| `python3 scripts/check_status_register.py` | Exit 0; paths=457, ev_ids=15, original32=32. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; 49 rows, 58 citations. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; pass. |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; 27 rows/headings, 110 citations. |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; 33 negative controls passed. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; 25 contracts, textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; 16 negative controls passed. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; scripts=35, plain=34, self_test=35, self_test_only=1. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; 13 negative controls passed. |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; reference_suites=7, node_tests=8, modules=4, excluded=3; adapter tests reached. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; 18 negative controls passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; 84 commands, pinned bytes unchanged. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; pass. |

Preservation: both locked files were hashed before and after this round with
`git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.
`git diff --exit-code origin/main HEAD -- reference/v0.3-rc1 runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs .aiops docs/tasks`
passed. A Python SHA-256 manifest comparison against the pre-edit tracked-file
snapshot also passed for every tracked path except this report, including all
108 historical reference files. Final `git diff --check` and
`PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` passed.

| External gate | Run ID / status / conclusion |
|---|---|
| Exact-head KTX kernel verification | Unavailable / not queried / unknown. |
| Exact-head KIX protocol verification | Unavailable / not queried / unknown. |
| Independent non-author exact-head review | Not established by supplied input. |
| Merge SHA / post-merge main CI / merged locked blobs | Not applicable; no merge performed. |

No stop-condition dependency or product-policy decision was needed; no
`DECISION_REQUIRED.md` is warranted. **STATUS: READY** means the local builder
handoff is ready for the supervisor. It is **not merge-ready**: both workflows
must succeed on the supervisor's exact final head and the required independent
review must be established. No commit, push, post, workflow change or network
action was performed. Production, durability, finality and legal non-claims above
remain in force.
