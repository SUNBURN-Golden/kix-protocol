# v5-residual-stops-owner-decision-record

Node: `plan-v5-residual-stops-owner-decision-record`. Archive the 2026-10-13 owner-delegate answer
for `k-stage2-v5-impl` and record the conflicts it leaves open.
Location record and byte-identical archive only: no new approval, no value adopted, no grade raise.
Issue: none. `docs/tasks/` has no file for this node. Depends on: none. Audit floor A2.
`astra_gate: None`, `user_merge: false` in the envelope; the record states a User merge is required
(acceptance 7), which is the stricter rule.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI; exact-head CI belongs in the PR closure report (AGENTS §11).

Observed `origin/main` and branch HEAD at session start: `a013cb0c471be0422a4a70d6b98e86c03f7131fa`.
`git fetch origin main` was not run (supervisor rule: no network); the local `origin/main` ref was used.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `reference/v0.3-rc1` and `.aiops` unchanged.

## Changed paths

- `docs/decisions/archive/k-stage2-v5-impl.decision_answer.md` (new, `cp` of the source)
- `docs/decisions/K_STAGE2_V5_RESIDUAL_STOPS_OWNER_DECISION_20261013.md` (new)
- `validation/2026-10-16-v5-residual-stops-owner-decision-record/README.md` (this file)
- `docs/status/CURRENT_CAPABILITY_REGISTER.md` (K2 and EV-V5 pointer clauses only)
- `docs/README.md` (two index rows, one bullet)

## Existing coverage mapping (AGENTS §7)

| Requirement | Coverage | Evidence |
|---|---|---|
| Byte identity of the archive | not covered by a checker | `cmp` below |
| Register paths valid | sufficiently covered | `scripts/check_status_register.py` |
| New files linked from docs index | sufficiently covered | `scripts/check_docs_index.py` |
| Conflict table citations | not covered; read by hand at the base SHA | grep of each cited line |

No test was added.

## Judgment calls

- Register scope: the node says the K2 pointer; the EV-V5 row carried the same stale clause, so both were
  changed to avoid a self-contradicting register. The 위치 동기화 기준 lines were not touched.
- Envelope `user_merge: false` versus acceptance 7: followed acceptance 7.
- The sha/blob hashes in the record contain digit runs; no retention value is copied anywhere.
- Historical records (`validation/2026-10-13-k-stage2-v5-impl`, `validation/2026-10-14-register-sync-v5-rs`)
  keep their old "not a file" wording (AGENTS §6).
- The proposal-versus-answer conflict is not classified as A/B/C (AGENTS §8): depends on which text governs.

## Commands and results

| Command | Result |
|---|---|
| `cmp <source> <archive>` | empty, exit 0 |
| `sha256sum` source and archive | both `7ec8a961550b3f71c014c93da8b18b0fc1ea5250de717809af8d8cf37a3c0399` |
| `git hash-object` on both locked files (before and after) | `69564b16…`, `b607996c…`, match |
| `python3 scripts/check_status_register.py` / `--self-test` | exit 0 `paths=233 ev_ids=15 original32=32` / pass |
| `python3 scripts/check_docs_index.py` / `--self-test` | exit 0 `scanned=141 indexed=106 allowlisted=39` / pass |
| `python3 scripts/check_rs_profile_traceability.py` / `--self-test` | exit 0 / pass |
| `python3 scripts/check_read_model_source_map.py` / `--self-test` | exit 0 / pass |
| `git diff --check` | exit 0 |
| `git diff --stat origin/main -- runtime docs/contracts docs/adr docs/DEVELOPMENT_PLAN.md scripts .github .aiops docs/tasks AGENTS.md reference` | empty |
| name grep over the record and this file | no hits (names appear only in `FIRST_BATCH_OPEN_INPUTS.md` lines 11, 35, 50 and the archive) |
| number grep over the record and the added README/register lines | only the git blob hash matches; no retention value |

## Not run

- `cargo`, Move, localnet, SDK steps: NOT_RUN, no code changed.
- Exact-head KTX and KIX protocol verification: unavailable before commit.

## Non-claims

- Provenance only. Nothing is adopted, reviewed or enabled; every lock stays.
- The author is the builder: not an independent review. A User merge is required.
- `DECISION_REQUIRED · Astra`, `UNDETERMINED · 법무/개인정보` (I10) and `UNDETERMINED · 운영/보안` (I13)
  stay open.

## Follow-ups

- `DEVELOPMENT_PLAN.md` §5 merge-table row and the K2 위치 동기화 기준 date: a later index-sync node.
- Resolving which text governs: Astra, with the User merging.
