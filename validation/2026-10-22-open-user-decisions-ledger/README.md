# Open User decisions ledger

Node: `plan-plan-open-user-decisions-ledger-20261022`. Document only. A
builder-authored in-repo ledger
(`docs/status/OPEN_USER_DECISIONS_20261022.md`) of the five open User/owner
decision items whose `DECISION_REQUIRED` records live outside main: the
`k-stage5-durable-tx` acceptance-run host, the `rs-4-l2` load-measurement
host, the `plan-readiness-conformance-negative-controls` CI-wiring option
A/B, the `plan-readiness-receipt-audit-tests` checker prerequisite, and the
`plan-booking-resale-admission-seeded-property` class C stop. One ledger row
per item carries who decides, the options and the recommendation as the
record states them, plus a repo-facts column verified against main only.
The ledger chooses no option, assigns no value, marks nothing reviewed and
changes no node state; the owner must re-trigger a node outside the builder
session.
Issue: none. `docs/tasks/` has no file for this node. Depends on:
`plan-plan-astra-decision-sheets-rs-stage5`,
`plan-readiness-checker-partial-fixture`,
`plan-plan-booking-resale-adopt-issued-atomici`. Audit floor A2.
`astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1792645030 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results
below are not exact-head CI. There is no KTX kernel verification run ID
and no KIX protocol verification run ID for a head that contains these
files.

Observed `origin/main` and branch HEAD at session start (after
`git fetch origin main`): `56d5f59468969825e0e2cd22f6803ebb5e6fb662`
(both equal; no base delta). Branch:
`agent/kix-plan-plan-open-user-decisions-ledger-20261022`.

## Locks

`git hash-object` before and after the documentation edits:

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Both required values, unchanged.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/OPEN_USER_DECISIONS_20261022.md` | New ledger. One row per open item (owner / options / recommendation as the record states them / repo facts since the record, HEAD-verified); no cell adopts, decides or marks anything reviewed. |
| `docs/README.md` | One location-only pointer appended to reading-order item 4 (`위치만. 결정·채택·회신이 아니다`); one bullet in the `## 2026-10-22 검증 기록 색인` section. |
| `docs/DEVELOPMENT_PLAN.md` | One row appended to the `병합된 문서 위치(2026-10-21~22)` §5 table with `—` PR/merge/merged_by placeholders (OpenAPI-promotion unmerged-row precedent); the adoption-sentence cell quotes the ledger's own decides-nothing sentence; `위치 포인터. 새 승인 아님.` A later sync node fills the merge fields. |
| `validation/2026-10-22-open-user-decisions-ledger/README.md` | This record. |

## Record sources and per-row source notes

All five records are outside main and were read in this session as node
input; the ledger quotes them from that input, not as merged contract:

| Row | Record source (outside main) | Read as |
|---|---|---|
| `k-stage5-durable-tx` host | `/workspace/kix-run/state/k-stage5-durable-tx.decision.md` (2026-10-13) | identical body also present as `DECISION_REQUIRED.md` in the unmerged worktree `agent/kix-k-stage5-durable-tx` |
| `rs-4-l2` host | `/workspace/kix-run/wt/rs-4-l2/DECISION_REQUIRED.md` (2026-10-15) | unmerged worktree |
| readiness negative-controls A/B | `/workspace/kix-run/wt/plan-readiness-conformance-negative-controls/DECISION_REQUIRED.md` | unmerged worktree |
| readiness receipt/audit prerequisite | `/workspace/kix-run/wt/plan-readiness-receipt-audit-tests/DECISION_REQUIRED.md` (2026-10-21) | unmerged worktree |
| BRA class C stop | `/workspace/kix-run/wt/plan-booking-resale-admission-seeded-property/DECISION_REQUIRED.md` | unmerged worktree |

Every who-decides/options/recommendation cell reproduced the record text in
full, so no cell needed the authorized fallback marker "text not in repo;
summarised from the node input". Two records (`k-stage5-durable-tx`,
`plan-readiness-receipt-audit-tests`) carry their recommendation inside the
option text itself (`(recommended)`, `Recommended:`); the ledger states that
explicitly instead of inventing a separate recommendation paragraph.

## Cited-path check (check_status_register-style)

Every repository-relative path the ledger cites as existing was checked with
`test -f` at the delivery HEAD; all exist:

`scripts/check_stage5_host.py`,
`validation/2026-10-20-stage5-preflight/README.md`,
`.github/workflows/protocol.yml`,
`validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md`,
`docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md`,
`reference/rights_scale/measurement_gap.py`,
`reference/rights_scale/host_conditions.py`,
`reference/rights_scale/test_host_conditions.py`,
`validation/2026-10-22-rs4-load-host-conditions-recorder/README.md`,
`validation/2026-10-21-readiness-checker-partial-fixture/README.md`,
`scripts/check_readiness_evidence_map.py`,
`docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`,
`reference/booking_resale_admission/test_adopt_issued_atomicity.py`,
`reference/booking_resale_admission/resale_fsm.py`,
`reference/booking_resale_admission/admission_fsm.py`,
`validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md`,
`docs/README.md`, `docs/DEVELOPMENT_PLAN.md`,
`validation/2026-10-22-open-user-decisions-ledger/README.md`.

Paths the ledger names as outside main were checked absent at the same HEAD
(none is linked as existing): `validation/2026-10-13-k-stage5-durable-tx/`,
`durable/`, `scripts/stage5_local_check.py`,
`validation/2026-10-15-rs-4-l2-load/README.md`,
`readiness/test_conformance_sensitivity.py`,
`reference/booking_resale_admission/test_gate_properties.py`.

Line- and content-level facts re-read at this HEAD and matching the ledger
cells: `.github/workflows/protocol.yml:237`
(`python3 scripts/check_stage5_host.py --self-test`) and `:244`
(`python3 -m unittest integration_gate.test_http_gate readiness.test_faults`);
`docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:64`
(`Counts: EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9`) with
`REC-CORE-COMMIT` and `OBS-AUDIT` still `PARTIAL` (rows 37 and 44);
`scripts/check_readiness_evidence_map.py` self-test containing the synthetic
`PARTIAL` positive control and the zero-`PARTIAL` second suite; the
scratch-copy `_commit_adopt` in `resale_fsm.py:1193` and
`admission_fsm.py:1105`; `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md:115-117`
(the two `expectedFailure` markers "must be removed (they would report an
unexpected success)" when `test_gate_properties.py` lands);
`validation/2026-10-21-readiness-checker-partial-fixture/README.md:166-168`
("`plan-readiness-receipt-audit-tests` still requires owner-approved input
revision outside its builder session. This prerequisite correction neither
implements nor resumes that blocked node.").

Merge-commit identities verified with `git log -1` on this tree:
#206 `244595db1524cbb1a01148baa07d6d28cd1b8dc6`,
#227 `154e9aae3da1bf0044dad606fcfd7e2fb6b3f8df`,
#230 `6f7559470bf2d555bbd80d0ae5d5f8a008e798f7`,
#236 `26f1b9535db24a6b2e9c28753f561d4d6a271815`,
#239 `9b462fd2cd6890cd0d8fbc2930f2cc54255e2915`,
#255 `1a69364eca0e2a219854c443f8183a9b0e733a2d`,
#256 `f1734e0…` (merge of
`agent/kix-plan-plan-rs4-load-host-conditions-recorder`).

Deviation from the supplied design plan, corrected against the tree: the
design attributed the CI wiring of `check_stage5_host.py --self-test` to
#238. `git log -S` on `.github/workflows/protocol.yml` shows the wiring
commit is `83c7847` on branch
`agent/kix-plan-plan-ci-wire-stage5-host-preflight-selft`, merged as #255
`1a69364eca0e2a219854c443f8183a9b0e733a2d` (#238 `e9f6fc0d…` was the
separate stdlib step comment-accuracy change). The ledger cites #255. The
design's `#묶음-4` anchor for the RS-stage5 sheet is not a resolvable GitHub
slug, so the ledger cites that sheet's §4 in prose without a link fragment.

## Commands and results

| Command | Result |
|---|---|
| `git fetch origin main` then `git rev-parse origin/main HEAD` | both `56d5f59468969825e0e2cd22f6803ebb5e6fb662`; clean tree at start |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| manual `test -f` loop over each repo path the ledger cites as existing | all exist (list above) |
| manual absence check over each path the ledger names outside main | all absent (list above) |
| `git log -1` on each cited merge SHA | all resolve to the named merges (list above) |
| `python3 scripts/check_status_register.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_read_model_source_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_docs_index.py` + `--self-test` | exit 0 / exit 0 (scanned=205 indexed=170 allowlisted=35) |
| `python3 scripts/check_i12_proof_ids.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_contract_error_codes.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_adapter_identity_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` + `--self-test` | exit 0 / exit 0 |
| `python3 scripts/check_stage5_host.py --self-test` | exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 scripts/test_runtime_architecture.py` | exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0 |
| `git diff --check` | exit 0 |
| `git diff --quiet HEAD -- reference/v0.3-rc1 runtime .aiops .github docs/tasks docs/contracts docs/decisions` | exit 0 — protected paths unchanged |
| `git status --short` | untracked: `docs/status/OPEN_USER_DECISIONS_20261022.md`, `validation/2026-10-22-open-user-decisions-ledger/`; modified: `docs/README.md`, `docs/DEVELOPMENT_PLAN.md` |

The command table records the final runs. One intermediate state is
reported honestly: after the `docs/README.md` edit but before this record
file existed, `check_docs_index.py` correctly failed with
`broken index link: validation/2026-10-22-open-user-decisions-ledger/README.md`;
creating the record resolved it and the final run passes.

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not queried or run; exact-head
KTX/KIX run IDs, statuses and conclusions are unavailable in this session,
and a docs-only skip on a hosted run is not a full-verification pass. Not
run locally: cargo clippy, the reference state-machine unittest suites,
OpenAPI/integration checkers, SDK conformance, storage probes, localnet, ZK,
and the plain invocation of `scripts/check_stage5_host.py` (a preflight
report for a different node's host prerequisite, expected to report missing
prerequisites on this host) — none required for a document-only ledger; the
kernel test and the two architecture scripts above are the cheap local
equivalents actually executed.

## Non-claims

Builder-authored; not an Astra or User decision and not a reply from any
owner. The ledger chooses no option, assigns no value, marks nothing
reviewed and changes no node state; the owner must re-trigger a node
outside the builder session. Quoted recommendations and options keep their
sources' not-a-decision status. The five stop records and their unmerged
evidence records are cited by path as outside-the-repository input only;
their contents are not represented as merged contract, and the repo-facts
column proves only that cited main paths exist, not what the cited tests
assert. The BRA and receipt/audit rows name the exact merged PR/record that
changed their precondition (#206 `244595db…`; #239 `9b462fd2…`) as
repository facts, not as owner decisions. No secret, no real provider data,
no real funds, real PG/bank/KYC calls, public endpoints, Sui
testnet/mainnet, R2, own replication/consensus/storage engine, new coin/TIX
module, product policy value, new protocol command or production runtime.
No lock changed; `reference/v0.3-rc1/**` byte-identical. Local checks are
not exact-head CI.
