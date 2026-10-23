# astra-decision-sheets-listvalues-v5-rs0

Node: `plan-astra-decision-sheets-listvalues-v5-rs0`. Document only. A
builder-authored decision sheet
(`docs/status/ASTRA_DECISION_SHEETS_KO.md`), in the style of
`docs/status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md`, collecting three
stopped decision groups: the `UNDETERMINED` list-query values of
`docs/contracts/READ_MODEL_QUERIES.md` §5/§6/§9, the `k-stage2-v5-impl`
residual stops, and the `rs-1` RS-0 acceptance-sentence options. The sheet
decides nothing, selects no option, sends nothing and is not a reply from
any owner.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1791773087 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results
below are not exact-head CI. There is no KTX kernel verification run ID
and no KIX protocol verification run ID for a head that contains these
files.

Observed `origin/main` and branch HEAD at session start, after
`git fetch origin main`: `77517f0c74cd892ca299cacf987cbab64a03337d`
(both equal).
Branch: `agent/kix-plan-astra-decision-sheets-listvalues-v5-rs0`.

## Locks

`git hash-object` before and after the documentation edits:

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Both required values, unchanged. `git diff --quiet origin/main --
reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/decisions
docs/aiops runtime` exits 0: no contract, decision record, program file or
protected path was edited.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/ASTRA_DECISION_SHEETS_KO.md` | New Korean decision sheet. Question/decision rows only; no value proposed. |
| `docs/README.md` | One pointer line on reading-order item 4, location only (`위치만. 결정·채택·회신이 아니다`). |
| `validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/README.md` | This record. |

## Cited-path check

Every repository-relative path cited in the new sheet was checked with
`test -f` at the delivery HEAD; all exist:

`docs/status/ASTRA_DECISION_SHEETS_KO.md`,
`docs/status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md`,
`docs/status/RS0_REVIEW_PACK.md`,
`docs/status/CURRENT_CAPABILITY_REGISTER.md`,
`docs/contracts/READ_MODEL_QUERIES.md`,
`docs/contracts/STATE_LIFECYCLE.md`,
`docs/contracts/FIRST_BATCH_OPEN_INPUTS.md`,
`docs/contracts/RIGHTS_SCALE_PROFILE.md`,
`docs/contracts/PG_TOSS_CARD_PROFILE.md`,
`docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md`,
`docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md`,
`docs/decisions/CUT_PROOF_I12_20261008.md`,
`docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md`,
`docs/DEVELOPMENT_PLAN.md`, `docs/README.md`, `.aiops/program.json`.

The `rs-1` stop record `/workspace/kix-run/state/rs-1.decision.md` is
outside the repository; the sheet cites it through
`docs/status/RS0_REVIEW_PACK.md` only and it is not part of the repo-path
check. Line numbers cited in the sheet were re-read at this HEAD and match
the text quoted (spot-checked: `READ_MODEL_QUERIES.md` :83-84, :175-176,
:183, :312-321, :329-345, :351, :386-391; `STAGE2…` :110-112, :135-139,
:181-182; `STATE_LIFECYCLE.md` :541-543, :552-560;
`FIRST_BATCH_OPEN_INPUTS.md` :35-37; `RETENTION…` :130;
`DEVELOPMENT_PLAN.md` :142; `CUT_PROOF…` :5;
`RIGHTS_SCALE_RS0_DECISION…` :3; `RIGHTS_SCALE_PROFILE.md` :3, :7).

`python3 scripts/check_status_register.py` is merged and was run (see
table). It checks that paths named inside the capability register exist;
the register was not edited, so it confirms the register is unaffected.

## Commands and results

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main && git rev-parse HEAD` | both `77517f0c74cd892ca299cacf987cbab64a03337d` |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| manual `test -f` loop over each repo path cited in the sheet | all cited paths exist (list above) |
| `git diff --check` | exit 0 |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/decisions docs/aiops runtime` | exit 0 — protected paths unchanged |
| `python3 scripts/check_status_register.py` | exit 0 |
| `python3 scripts/check_status_register.py --self-test` | exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 scripts/test_runtime_architecture.py` | exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0 |
| `git status --short` | untracked: `docs/status/ASTRA_DECISION_SHEETS_KO.md`, `validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/`; modified: `docs/README.md` |

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. Both workflows
classify this diff (docs under `docs/*` excluding
`docs/contracts`,`docs/adr`,`docs/PROTOCOL_MASTERPLAN_*`; `validation/*`
excluding `2026-09-11`; `docs/README.md` matches `docs/*`) as
documentation-only and skip the heavy steps on a hosted run; a skipped
heavy job is not a full-verification pass and this local run is not that
classification. Not run locally: cargo clippy, the reference
state-machine unittest suites, OpenAPI/integration checkers, SDK
conformance, storage probes, localnet, ZK — none required for a
document-only sheet; the kernel test and the two architecture scripts
above are the cheap local equivalents actually executed.

## Non-claims

Builder-authored; not an Astra or User decision and not a reply from any
owner. No node status changes. No numeric policy value, error-code name,
phase list or visibility cell value is proposed — quoted recommendations
and route templates keep their sources' not-a-decision status. No secret,
no real provider data, and no instruction to contact any external party:
"담당은 제공자이며 사용자를 거친다" quotes the contract's owner field, it
does not direct contact. No lock changed; `reference/v0.3-rc1/**`
byte-identical. No real funds, real PG/bank/KYC calls, public endpoints,
Sui testnet/mainnet, R2, storage engine, or production runtime. Local
checks are not exact-head CI.
