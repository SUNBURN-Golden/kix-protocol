# k1-evidence-close — first-batch integration review and evidence close-out

Node: `k1-evidence-close`. Document only. No code, no new tests, no policy values,
no new protocol command.
Issue: none.
Depends on `k1-e4-residual-review` and `k1-adapter-event-identity`. The I12 cut
proof is cited because this close-out points at it; it is not a third dependency
in the node input.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`ae869f38438d8174103171ec741a41376aee60df`.
Branch: `agent/kix-k1-evidence-close`.
This session did not commit, push, open a PR, or comment. There is no
implementation commit SHA. Local results below are not exact-head CI.
Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

What this record closes is `FIRST_BATCH_OPEN_INPUTS.md` §2 item 「잔여 통합 검토·증거 마감」,
and only when this record is merged. Lifecycle input reflection and the
fixed-environment performance repeat stay open. The first batch is not complete.
`새로 실입력까지 완결된 행: 0` is unchanged.

## Changed paths

| Path | Change |
|---|---|
| `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md` | New §4 ledger. I06 and I12 cells gain pointers. Status text stays 미완결. §1 counts, the §2 estimate table, and §3 are unchanged. |
| `docs/README.md` | Index only. One validation bullet for this record. One location pointer to the owner question sheet on reading-order item 4. |
| `validation/2026-10-08-k1-evidence-close/README.md` | This record. |

## Dependency evidence

Merge commits are from `git log --merges --full-history -- <path>`. Plain
`git log --merges -- <path>` was empty under default history simplification, so
it is not used as a negative result.

| Artifact | Merge on `origin/main` | PR |
|---|---|---|
| `validation/2026-10-05-k1-e4-residual-review/` | `5155ed307c71917ba3442fc5e1fc4cb950efefdc` | #114 |
| `docs/contracts/ADAPTER_EVENT_IDENTITY.md` and `validation/2026-10-08-k1-adapter-event-identity/` | `5561fc965803935be1894457ebc762a3d36489f5` | #124 |
| `docs/decisions/CUT_PROOF_I12_20261008.md` | `ae869f38438d8174103171ec741a41376aee60df` | #136 |

Hosted runs were read from the merge SHAs only. KTX kernel verification has no
run on any of these three SHAs (that workflow is `pull_request` and
`workflow_dispatch`). Each SHA has a KIX protocol verification push run with
`status=completed`, `conclusion=success`, and the heavy steps `skipped`:

| Merge | Protocol push run | What the job steps show |
|---|---|---|
| #114 `5155ed307c71917ba3442fc5e1fc4cb950efefdc` | `37292171263` (a later schedule run `37296845388` is also success with the same shape) | Heavy steps skipped. The diff is only the residual-review README, which the classifier treats as documentation-only. |
| #124 `5561fc965803935be1894457ebc762a3d36489f5` | `37729089565` | Heavy steps skipped. The diff includes `docs/contracts/*`, which the workflow file at that SHA classifies as full verification. This session did not retrieve the classify-step summary, so the skip reason is not established. |
| #136 `ae869f38438d8174103171ec741a41376aee60df` | `37793345460` | Heavy steps skipped. The diff is `docs/README.md` and `docs/decisions/CUT_PROOF_I12_20261008.md`, which the classifier allows as documentation-only. |

A skipped heavy job is not a full-verification pass. These run IDs are not
evidence that kernel or protocol tests executed. The adapter README's 128-test
count is historical and is not reused here.

## Integration cross-checks

1. **Row counts.** `FIRST_BATCH_OPEN_INPUTS.md` §1 has 13 rows, I01 through I13.
   The two rows whose status is an existing confirmation are I01 and I07.
   `새로 실입력까지 완결된 행: 0` is present. I02–I06 and I08–I13 stay 미완결.
2. **Sheet versus rows.** `docs/status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md`
   has rows for I02–I05, I08, I09–I13, and the residual-risk items (U-R1, U-R2).
   I06 is absent on purpose (sheet lines 100–101). The sheet says it was not sent.
3. **TM04 and TM05.** They have no question-sheet row. They appear in
   `ADAPTER_EVENT_IDENTITY.md`, `docs/reviews/TOSS_METHOD_EXPANSION_REVIEW.md`,
   and the open-input ledger. The I06 unlock condition therefore cannot be sent
   to Toss from the sheet. This node does not edit the sheet. Follow-up below.
4. **Cut proof versus sheet versus I12.** Sheet lines 94–96 are P12-C, P12-W,
   and P12-V. The cut proof cites P12-W and P12-V at its line 156 as sheet lines
   95 and 96, and A9 cites P12-V at sheet line 96. The I12 status cell remains
   미완결. The three texts agree that PG operational close does not replace the
   proof, and that independent review plus the user's trust-policy approval are
   still required. Cut-proof assumptions A4, A5, and A10 stay
   DECISION_REQUIRED · Astra. A9 and the trust-policy approval stay with the User.
5. **No document claims I06 or I12 closed.** Search hits are denials: the adapter
   draft, the cut proof's non-claims, and the open-input rows.
6. **Cited tests exist.** All 22 `file.rs::fn` names in the e4 README coverage
   table and all 5 names in `ADAPTER_EVENT_IDENTITY.md` §10.1 occur as `fn`
   under `runtime/crates/kix-kernel/tests/`. This check is a name lookup, not a
   test run.
7. **Option accepted by #136.** The merge commit message and the implementation
   commit message do not name option 1, 2, or 3. Not inferred.
8. **Stale statements, left as written.**
   - Root `README.md` line 40 still says the first-batch residual review is in
     progress. `roadmap-sync` owns that file.
   - `docs/status/CURRENT_CAPABILITY_REGISTER.md` is the 2026-10-06 snapshot at
     `2554173ebdda0922aaf7a0bc7ea773075187a3d9`.
   - Cut proof §0 says moving the I12 row off 미완결 is this node's job. This
     node adds a pointer and leaves the status 미완결, because A9 and the
     trust-policy approval are still absent and the merge does not record an option.

## Existing coverage (AGENTS §7)

No new tests. No new behavior.

| Requirement | Where it is already mapped |
|---|---|
| E-4 residual predicates | `validation/2026-10-05-k1-e4-residual-review/README.md` coverage table. That session did not execute the tests (`cargo` exit 127). |
| Adapter identity kernel regressions | `docs/contracts/ADAPTER_EVENT_IDENTITY.md` §10.1. Adapter derivation, Toss ID stability, and webhook signature stay not covered there. |
| I12 cut sentences | `docs/decisions/CUT_PROOF_I12_20261008.md` §6. That file adds no tests. |

## Commands actually run

Working directory: repository root. Python 3.13.5 (`tomllib` present).
Cargo 1.98.1. Node v20.19.2 is present. `sui` and `snarkjs` are absent. `.venv`
is absent. Hosted CI uses Python 3.12 and Node 24; those were not installed.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `ae869f38438d8174103171ec741a41376aee60df`. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `git diff --stat origin/main` | Two tracked paths: `docs/README.md`, `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md`. The new validation README is untracked, so this command does not list it. `git status --short` shows that directory as well. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks runtime` | Empty. |
| `git diff --check` | Exit 0. |
| Relative-link check, `python3 -I` outside the repo, on the three changed files | 0 missing links, 0 trailing-whitespace lines. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | First run exit 1. 53 tests, 1 failure: `BrowserAccessTests.test_real_responses_add_cors_only_for_the_allowed_origin`, `AssertionError: 415 != 503`. Same command rerun exit 0, 53 tests, OK. The test file was not edited. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 20 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. 43 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. 20 tests, OK. |
| same for `reference/ai_delegation` | Exit 0. 22 tests, OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. commands=40, pin OK. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. commands=40, productionEndpoint=false, publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. pass. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32. Doc-tests 0. 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. This run: bcs1 3, golden_vectors 4, feature-ir 5, audit_regressions 8, schema_bound 18, feature-semantics 6, kernel lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32, kix-types 6. Sum 128 passed, 0 failed. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |

## Not run locally

`scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`,
`scripts/verify_canonical.py`, the storage probes, `scripts/run_localnet.py`,
SDK conformance, and the ZK steps. No Sui CLI, no snarkjs, and no `.venv`.
Those steps are covered only by hosted CI, which does not exist for this
uncommitted tree.

## Deviations from the design plan

- Ledger row keys use the §2 cell text (`잔여 모델/검사 검토·범위 보강`,
  `잔여 수명 계약 입력 반영/검토`), not the plan's shortened labels.
- The question-sheet pointer is on `docs/README.md` reading-order item 4.
  The sheet's adding commit is 2026-10-06, so it is not listed under the
  2026-10-08 validation records.
- The residual-review row does not treat hosted full verification as the
  evidence. The #114 protocol run skipped its heavy steps.
- `git log --merges -- <path>` was empty until `--full-history` was added.
  The merge SHAs above are from that full history.

## Exact-head CI

Not recorded here. Per AGENTS §11 the final-head KTX and KIX protocol run IDs
belong in the pull-request report after a head exists. This tree is
uncommitted. A draft or skipped run is not a pass. Because the diff touches
`docs/contracts/*`, both workflow classifiers force full verification; the
documentation-only skip does not apply to this change. CI from an earlier SHA
does not transfer.

## Contract classification (AGENTS §8)

No explicit contract violation. The close-out does not redefine a contract,
choose a cut-proof option, or fill a product number.

Contract-undefined items already recorded elsewhere, left open:

- Which of cut-proof options 1, 2, and 3 the #136 merge accepted.
- TM04/TM05 have no sheet row, so the sheet cannot carry the I06 Toss question.
- H_g finality policy (A4), the time source and its numbers (A5), and an
  uncooperative executor (A10) remain DECISION_REQUIRED · Astra inside the cut proof.

## Non-claims

No production readiness, durability, distributed fencing, bank exactly-once,
chain finality, or legal compliance. No approved TPS, p99, or failure rate.
The stage-4 local exploration does not substitute for the fixed-environment
repeat. I06 and I12 are not complete. The 13-row input table gained no newly
complete row. This record does not re-estimate effort (`k-a-reestimate` is a
later node). No real funds, PG, bank, KYC, public endpoint, Sui testnet or
mainnet, R2, replication, consensus, or storage engine.

## Remaining uncertainty and follow-ups

- Toss facts for I02–I05, I08, TM04, and TM05: UNDETERMINED · Toss technical/contract.
- I10: UNDETERMINED · legal/privacy.
- I09 numbers and the performance targets: DECISION_REQUIRED · Astra. Equipment
  spend: User.
- I11 automatic-service limits and residual-risk policy: DECISION_REQUIRED · Astra.
- I12 independent reviewer (A9) and trust-policy approval: User.
- Add TM04/TM05 to a question sheet only in a later node that is allowed to edit it.
- Root `README.md` line 40 is stale relative to the residual-review handoff.
  Leave it for `roadmap-sync`.
- Hosted full verification of this exact head is still required after publication.
- The #124 protocol skip, despite a `docs/contracts/*` diff, is unexplained here.
  CI was not edited.
