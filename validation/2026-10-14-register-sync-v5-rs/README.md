# register-sync-v5-rs-20261014

Node: `audit6-register-sync-v5-rs-20261014`. Location index sync of
`docs/status/CURRENT_CAPABILITY_REGISTER.md` to the v5 and RS-1..RS-3b code
already merged on `origin/main`. No decision text, no grade raise, no
reviewed/operational claim, no code change to any shipped surface, no new
protocol command.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`. `user_merge: False`.
Source: KIX audit #6 (`audit_6_20261014.md`, finding 1 / fix_nodes[0]).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results below
are not exact-head CI. There is no KTX kernel verification run ID and no KIX
protocol verification run ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`ced0e2f42c0491753db91acf87bd61574eb37ce4` (merge of PR #184).
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which equals
the task-branch HEAD (`git status -sb` shows the branch tracks `origin/main`
with no divergence).
Branch: `agent/kix-audit6-register-sync-v5-rs-20261014`.

Working directory: repository root of this worktree. Python 3.13.5 (workflow
installs 3.12).

## Locks

`git rev-parse HEAD:<path>` before the first edit and `git hash-object` after
all edits (the files were never opened for edit;
`git diff --stat origin/main -- runtime/` is empty):

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --stat origin/main -- runtime/ reference/v0.3-rc1 .github/
docs/contracts/ docs/decisions/ docs/tasks/ .aiops/` produced no output.
`reference/v0.3-rc1/**` is byte-identical.

## What this record points at

Locations only. A sixth sync-base line in
[the register](../../docs/status/CURRENT_CAPABILITY_REGISTER.md) names
`ced0e2f42c0491753db91acf87bd61574eb37ce4` (2026-10-14) for: the K2 row, the
RS-1/RS-2/RS-3a/RS-3b rows, and three new shared-evidence rows. It also
records that the 2026-10-12 base line's `k-stage2-v5-impl`/`rs-1`
not-merged notations are superseded while `read-model-reference` stays
not merged.

New evidence ids (first-column keys of the shared evidence index):

| ID | Area | Grade | Merge(s) |
|---|---|---|---|
| EV-V5 | `runtime/crates/kix-kernel-v5` | MOCK(memory) | PR #179 (`4813388b5bcde72c298c7392ff5230316da44470`) |
| EV-DELEG | `runtime/crates/kix-delegated-exec` | MOCK(memory) | PR #184 (`ced0e2f42c0491753db91acf87bd61574eb37ce4`) |
| EV-RS | `reference/rights_scale` | LOCALNET | PR #180 (`7b6a293e903845ff9c06a19f9a02c075d1790089`), probe PR #181 (`dd92e1146ec8eb7024da6c0f62aa721bdc1be780`), PR #182 (`bd367efcc9127663b902b973850ffafc179469df`), PR #183 (`adcddc510a66ff70725084c0846830c29ef9ebbe`), PR #184 |

Merge SHAs above are from `git log --merges origin/main`; the register rows
themselves carry PR numbers and validation-record paths only, matching the
register's convention.

Rewritten rows:

- **K2** now reads `in-memory v5 slice merged (PR #179); MOCK(memory)` and
  keeps the locked-v4 boundary; it newly records that the shipped retention
  defaults rest on an owner decision of 2026-10-13 that is not a file in this
  repository — the flag the v5 record itself raises
  (`validation/2026-10-13-k-stage2-v5-impl/README.md`) — and that the
  relation to `RETENTION_PERIODS_PROPOSAL_20261009.md` §7 is unresolved.
  This sync cites the flag; it does not adjudicate it.
- **RS-1** reads `merged (PR #180, probe PR #181)` and adds the probe's
  measured fact (two concurrent issuer transactions sharing `&IssuerCap`
  serialize; the §13 option choice stays OPEN, owner Astra).
- **RS-2, RS-3a, RS-3b** read `merged (PR #182 / #183 / #184)`; every
  not-covered clause of the prior text is kept verbatim
  (익명성·ceremony·회로 감사·성능 미주장; 위임 실행·TTL·허용 연산 집합·
  durable 등). The one clause that moved — RS-3a's "RS-3b 페이지↔커널 대응은
  not covered" — now points at EV-DELEG, which is what PR #184 merged.
- Each of K2 and RS-1..RS-3b carries "Astra ARCHITECTURE 검토 기록은 이 트리에
  없음(프로파일 미검토)" — the merged state is recorded without marking the
  Astra gate as done (audit finding 5 stays visible).
- The RS section header's "새 프로파일 source/fixture는 **없음**" is replaced
  by a sentence indexing the merged profile source as EV-RS/EV-DELEG (v5:
  EV-V5). The EV-MOVE comparison-regression sentence is unchanged.

No evidence grade was raised; the operational count stays 0; every prior
"not covered" cell still says so or names the in-memory/localnet scope.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | New sync-base line; EV-index preamble date; EV-V5/EV-DELEG/EV-RS rows; K2 row; RS section header sentence; RS-1/RS-2/RS-3a/RS-3b rows. |
| `validation/2026-10-14-register-sync-v5-rs/README.md` | This record. Not added to `docs/README.md` (`validation/` is outside `check_docs_index.py` scan patterns). |

`docs/README.md` is unchanged: the register is already index-linked there.
Its snapshot sentences still describe the pre-2026-10-14 bases; refreshing
them is index wording left to the sibling `plan-index-sync` node (see
follow-ups).

## Existing coverage mapping (AGENTS §7)

| Requirement | Classification | Evidence |
|---|---|---|
| register self-consistency (paths, EV ids, original32 keys) | sufficiently covered | `scripts/check_status_register.py` + `--self-test`; no new test needed |
| docs index coverage | sufficiently covered | `scripts/check_docs_index.py` + `--self-test`; no scanned file was added |
| RS profile↔blueprint id traceability | sufficiently covered | `scripts/check_rs_profile_traceability.py` + `--self-test`; profile untouched |

No new tests were added: this node moves register pointers only, and the two
CI-wired checkers already cover the predicates this file can break. No Rust,
Move, Python, or client code changed, so no runtime suite is re-run as
evidence for this node (see Not run).

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse origin/main`, `git rev-parse HEAD`, `git status --short` | Exit 0. Both `ced0e2f42c0491753db91acf87bd61574eb37ce4`; clean tree at start. |
| `git status -sb` | Exit 0. `agent/kix-audit6-register-sync-v5-rs-20261014` tracks `origin/main`, no divergence. `git fetch` not run (network forbidden this session). |
| `git log --merges --oneline origin/main` | Exit 0. Confirmed mapping #179=v5, #180=rs-1, #181=probe, #182=rs-2, #183=rs-3a, #184=rs-3b (merge commit `ced0e2f`). |
| `git log --merges --oneline --grep='pull request #13' origin/main` | Exit 0. Confirmed #138 = `STAGE2_V5_CRATE_DESIGN_DECISION` merge, #139 = retention proposal merge. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=219 ev_ids=15 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. Detected missing path, undefined `EV-XXX`, dropped E01 row, duplicated E01 row; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0. `docs index ok: scanned=66 indexed=63 allowlisted=3`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. Detected removed index link, unindexed scanned file, dropped allowlist entry, removed scanned file, broken index link; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. Sanity check: the profile file was not touched. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. All seven mutation cases detected; `self-test: pass`. |
| `git diff --check` | Exit 0. No whitespace errors. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after edits) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values, unchanged. |
| `git hash-object` on the two locked files (after edits) | Same required values. |
| `git diff --stat origin/main -- runtime/ reference/v0.3-rc1 .github/ docs/contracts/ docs/decisions/ docs/tasks/ .aiops/` | Exit 0, empty output. Protected paths unchanged. |
| `git status --short` | `M docs/status/CURRENT_CAPABILITY_REGISTER.md`, untracked `validation/2026-10-14-register-sync-v5-rs/`. Nothing else. |

## Not run

Cargo/rustc suites under `runtime/` (`ktx-kernel.yml` equivalents): no Rust
source changed, so the closest local equivalent is the empty-diff check on
`runtime/` above — recorded as NOT_RUN-for-cargo rather than claimed.
Move package tests, localnet journeys, ZK fixtures, `bootstrap.sh`
(`.venv`/pip/npm/Sui installs; no network this session), the `sdk` suite, and
hosted KTX/KIX runs for a head containing these files: not run here.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or operational,
and keeps the operational count at 0. "merged" is a location statement about
`origin/main`, not a gate verdict: no register wording marks the Astra
ARCHITECTURE review as done, and the RS rows now say explicitly that no such
record exists in this tree. The retention-defaults contradiction (audit
finding 3) is cited as flagged, not resolved — resolving it needs a product
policy value and is `DECISION_REQUIRED` for the owner, not for this node.
Fixture index entries are not execution PASS claims; the EV-RS LOCALNET and
EV-V5/EV-DELEG MOCK scopes are stated inside their rows. No contract,
decision, task, `.aiops/`, or CI file was changed.

## Follow-up candidates

- `docs/README.md` register snapshot sentences still name only the
  2026-10-09/10-12 bases; index wording for the 2026-10-14 base belongs to
  the sibling `plan-index-sync-20261014` node (audit fix_nodes[1]).
- The v5 retention defaults vs `RETENTION_PERIODS_PROPOSAL_20261009.md` §7
  (audit finding 3): needs the owner decision recorded in-tree or the
  defaults reverted to caller-supplied slots — owner/Astra decision.
- Astra ARCHITECTURE review records for the five A3 merges (audit finding 5):
  if they happened, their location needs recording; if not, the profile's
  미검토 status stands and RS-4 builds on unreviewed text.
- RS-4 L2's open values (audit finding 9: ptau power 15, shard counts, GA
  redistribution) gate the next nodes; all are labelled OPEN.
