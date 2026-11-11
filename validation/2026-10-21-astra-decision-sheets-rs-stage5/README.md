# astra-decision-sheets-rs-stage5

Node: `plan-plan-astra-decision-sheets-rs-stage5`. Document only. A
builder-authored decision sheet
(`docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md`), a follow-up to
`docs/status/ASTRA_DECISION_SHEETS_KO.md` (bundle 1), collecting the
named-but-unsheeted open items that blocked nodes need: the `IssuerCap`
cap-split choice of `docs/contracts/RIGHTS_SCALE_PROFILE.md` §13, the
operational values behind the test-only numeric fixtures of
`reference/rights_scale/sui/sources/rights_scale.move` (root-window K,
nullifier/challenge/payment shard counts, tree depth, bundle limit, and
the unbounded GA counter), the RS-C02 sentence-2 redistribution operation,
and the three stage-5 items named in the `k-stage5-durable-tx` record
(`EventItemId` source, 16-byte alias rule, inbox policy for conflict
items). The sheet decides nothing, selects no option, sends nothing and
is not a reply from any owner.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `plan-astra-decision-sheets-listvalues-v5-rs0`,
`plan-stage5-host-preflight-checker`. Audit floor A2. `astra_gate: None`,
`user_merge: false`.
Source: KIX planner run 1792541948 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results
below are not exact-head CI. There is no KTX kernel verification run ID
and no KIX protocol verification run ID for a head that contains these
files.

Observed `origin/main` and branch HEAD at session start:
`e2313ab473ea1b5a7b5b9246a564749188c1c2c8` (both equal; local ref —
`git fetch` was not run because this session's rules forbid
network/GitHub actions; the worktree starts from latest main).
Branch: `agent/kix-plan-plan-astra-decision-sheets-rs-stage5`.

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
| `docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md` | New Korean decision sheet, same format as `ASTRA_DECISION_SHEETS_KO.md`. Question/decision rows only; no value proposed. |
| `docs/README.md` | One location-only pointer appended to reading-order item 4 (`위치만. 결정·채택·회신이 아니다`); one bullet in the `## 2026-10-21 검증 기록 색인` section. |
| `validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md` | This record. |

## Cited-path check

Every repository-relative path cited in the new sheet was checked with
`test -f` at the delivery HEAD; all exist:

`docs/contracts/RIGHTS_SCALE_PROFILE.md`,
`docs/contracts/ADAPTER_EVENT_IDENTITY.md`,
`docs/adr/0001-ktx-authority-commit-recovery.md`,
`docs/status/RS_PREDICATE_EVIDENCE_MAP.md`,
`docs/status/CURRENT_CAPABILITY_REGISTER.md`,
`docs/status/ASTRA_DECISION_SHEETS_KO.md`,
`docs/status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md`,
`docs/blueprints/rights-scale-v1/README.md`,
`docs/DEVELOPMENT_PLAN.md`,
`reference/rights_scale/sui/sources/rights_scale.move`,
`reference/rights_scale/test_model.py`,
`runtime/crates/kix-delegated-exec/README.md`,
`validation/2026-10-14-rs-1-issuercap-probe/README.md`,
`validation/2026-10-20-stage5-preflight/README.md`,
`scripts/check_stage5_host.py`, `.aiops/program.json`.

The `k-stage5-durable-tx` stop record
`/workspace/kix-run/state/k-stage5-durable-tx.decision.md` and its evidence
record `validation/2026-10-13-k-stage5-durable-tx/README.md` (unmerged
branch `agent/kix-k-stage5-durable-tx`) are outside the repository; the
sheet cites them by path only and they are not part of the repo-path
check. The record was read in this session: it names the `EventItemId`
source, the alias rule and the inbox policy for conflict items as the
Astra decisions that stay open, and states they do not block the
acceptance run.

Line numbers cited in the sheet were re-read at this HEAD and match the
text quoted (spot-checked: `RIGHTS_SCALE_PROFILE.md` :35, :48, :55, :67,
:69, :106-107, :135, :158, :161, :185, :231-233, :250-258,
:262-268; `rights_scale.move` :72, :75-84, :368-369, :738;
`RS_PREDICATE_EVIDENCE_MAP.md` :28-29, :32, :58;
`test_model.py` :125; `kix-delegated-exec/README.md` :22, :35;
`blueprints/rights-scale-v1/README.md` :132, :287;
`ADAPTER_EVENT_IDENTITY.md` :131, :135-136, :138, :142-143, :160, :220,
:234-235, :239; `ADR-0001` :80, :143, :147-151;
`ASTRA_DECISION_SHEETS_KO.md` :111).

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD && git rev-parse origin/main` | both `e2313ab473ea1b5a7b5b9246a564749188c1c2c8` (`git fetch` not run — session rules forbid network actions) |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| manual `test -f` loop over each repo path cited in the sheet | all cited paths exist (list above) |
| `git diff --check` | exit 0 |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/decisions docs/aiops runtime` | exit 0 — protected paths unchanged |
| `python3 scripts/check_status_register.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_read_model_source_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_docs_index.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_i12_proof_ids.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_contract_error_codes.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_adapter_identity_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 scripts/test_runtime_architecture.py` | exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0 |
| `git status --short` | untracked: `docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md`, `validation/2026-10-21-astra-decision-sheets-rs-stage5/`; modified: `docs/README.md` |

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. Both workflows
classify this diff (`docs/status/*.md`, `docs/README.md`,
`validation/*/README.md` — all `docs/*`/`validation/*` outside the
verifier-input allowlist) as documentation-only and skip the heavy steps
on a hosted run; a skipped heavy job is not a full-verification pass and
this local run is not that classification. On a hosted docs-only run the
only `protocol.yml` step that still executes is "Stdlib offline document
checks"; its exact command list was run above. Not run locally: cargo
clippy, the reference state-machine unittest suites, OpenAPI/integration
checkers, SDK conformance, storage probes, localnet, ZK,
`scripts/check_stage5_host.py` (a preflight report for a different node's
host prerequisite, expected to report missing prerequisites on this
host) — none required for a document-only sheet; the kernel test and the
two architecture scripts above are the cheap local equivalents actually
executed.

## Non-claims

Builder-authored; not an Astra or User decision and not a reply from any
owner. No node status changes. No numeric fixture value, option, command
name or policy is proposed — quoted recommendations and options keep
their sources' not-a-decision status. The stage-5 stop record and its
unmerged evidence record are cited by path as outside-the-repository
input only; their contents are not represented as merged contract. No
secret, no real provider data, and no instruction to contact any external
party: "제공자·사용자 경유" quotes the contract's owner field, it does
not direct contact. No lock changed; `reference/v0.3-rc1/**`
byte-identical. No real funds, real PG/bank/KYC calls, public endpoints,
Sui testnet/mainnet, R2, storage engine, or production runtime. Local
checks are not exact-head CI.
