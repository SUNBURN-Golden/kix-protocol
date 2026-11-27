# rs-profile-revision-log-0-2 — profile header marked as draft revision 0.2

Node: `audit6-rs-profile-revision-log-0-2`. Version-metadata sync of
`docs/contracts/RIGHTS_SCALE_PROFILE.md`: the header now matches the bytes the
file already carries. RS-3a (PR #183) and RS-3b (PR #184) rewrote parts of
§3/§5/§10/§13 while the header still said `문서 버전 0.1 · 작성 2026-10-08`
(KIX audit #6, finding 4). This node bumps the header to **0.2 (초안)**, keeps
the status line **초안. 미검토. 미측정.**, and adds a `## 0. 개정 이력` section
that lists exactly which sections each PR changed, with the validation-record
paths, and records that 0.1 @ `9b12626b` is the version
`docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md` cites.

No semantic rule, RS-C/IM/RR id, status notation, or adoption sentence was
changed. No RS-0 decision record edit. No code, CI, blueprint, or reference
surface was touched.

Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`. `user_merge: False`.
Source: KIX audit #6 (`audit_6_20261014.md`, finding 4 / fix_nodes[2]).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results below
are not exact-head CI. There is no KTX kernel verification run ID and no KIX
protocol verification run ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`50af6096a84f72c8c1249f23279dab0b279e4c82` (merge of PR #186).
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which equals
the task-branch HEAD (`git status -sb` shows the branch tracks `origin/main`
with no divergence).
Branch: `agent/kix-audit6-rs-profile-revision-log-0-2`.

Working directory: repository root of this worktree. Python 3.13.5 (workflow
installs 3.12).

## Locks

`git hash-object` on both files before the first edit and after all edits:

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

`git diff --stat origin/main -- runtime/ reference/ .aiops/ docs/tasks/
docs/decisions/ .github/` produced no output. `reference/v0.3-rc1/**` is
byte-identical.

## Git derivation of the 0.1 → 0.2 delta (re-derived, not taken from the plan)

| Fact | Command | Result |
|---|---|---|
| commits touching the profile since 0.1 | `git log --format=… 9b12626b..HEAD -- docs/contracts/RIGHTS_SCALE_PROFILE.md` | exactly two: `45c08d519daa70adaf89ba5e8d2e89175422dc17` (rs-3a, in PR #183 via merge `adcddc510a66ff70725084c0846830c29ef9ebbe`, second parent verified) and `954e6e3a2b6abbe40af3a13d04e4263fa7fbe547` (rs-3b, in PR #184 via merge `ced0e2f42c0491753db91acf87bd61574eb37ce4` → branch head `3dee308f`; `954e6e3` verified an ancestor of `3dee308f`) |
| total delta | `git diff --stat 9b12626b..HEAD -- <profile>` | 20 insertions, 11 deletions — exactly the union of the two per-commit diffs (15+6 and 5+5); no other hunks |
| profile at the RS-1 anchor | `git show 9b12626b:<profile>` + `git log 68a58ae..9b12626b -- <profile>` | header already `계약 0.1`; no commit touched the profile between the 0.1 merge (`68a58ae`, PR #125, 2026-10-08) and `9b12626b`, so 「0.1 @ 9b12626b」 names the 0.1 bytes exactly |
| rs-3a hunks | `git show 45c08d5 -- <profile>` | §3 object table `GrantControl` row; §3 operation table +8 delegated-operation rows; §10 intro, items 2, 3, 4, 5 (each extended), item 8 added |
| rs-3b hunks | `git show 954e6e3 -- <profile>` | §5 two bullets (seat page↔kernel `Inventory` correspondence; GA lowest-free-slot deterministic assignment); §10 item 7 rewritten; §13 two rows |

The design plan's rs-3a note said "§10 서두·항목 2–4·8"; git shows item 5 also
gained a sentence (cut 뒤 미해소 예약 회수 거절). The revision log records the
git-accurate list: §10 서두·항목 2–5·항목 8(신규).

## What changed

`docs/contracts/RIGHTS_SCALE_PROFILE.md`, three hunks:

1. **Header** — line 1 `계약 0.2 (초안)`; line 3 `문서 버전 0.2 (초안) · 작성
   2026-10-08 · 개정 2026-10-14 · 상태: **초안. 미검토. 미측정.**` (status text
   unchanged, 개정 date added).
2. **New `## 0. 개정 이력`** — between the intro and `## 1.` so no existing
   §1–§13 anchor moves (§5/§10/§13 are cited by the register, the plan and
   three validation records). Three rows: 0.1 (PR #125 `68a58ae`, the version
   `RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md`'s 「초안 0.1 @
   `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`」 cites, record → RS-0 decision
   record), 0.2 RS-3a (PR #183 `adcddc5`, §3 `GrantControl` 행 + 위임 연산
   8행, §10 서두·항목 2–5·항목 8, record → rs-3a validation README), 0.2 RS-3b
   (PR #184 `ced0e2f`, §5 두 불릿, §10 항목 7, §13 두 행, record → rs-3b
   validation README). Followed by the inheritance sentence: 0.2 inherits the
   0.1 body verbatim outside the listed edits; the remaining 「0.1」 sentences
   (§4·§6·§7·§8·§9·§11·§13 — enumerated after re-grepping the file) are 0.1-era
   statements; RS-C/IM/RR ids, status notations and adoption sentences
   unchanged; still draft, confirmed only by Astra review and the user merge.
3. **§2 one clause** — `문서 버전 0.1과 온체인 profile_version은 다른 값이다` →
   `문서 버전과 온체인 profile_version은 다른 값이다`. §2 sits outside the
   protected §3–§13 range; the rule (doc version ≠ on-chain `profile_version`)
   is unchanged, only the now-stale number is dropped so the body cannot be
   read as still claiming version 0.1. This is the only body clause touched.

## Changed paths

| Path | Change |
|---|---|
| `docs/contracts/RIGHTS_SCALE_PROFILE.md` | Header bump; new `## 0. 개정 이력`; §2 stale-number clause. 13 insertions, 3 deletions. |
| `validation/2026-10-14-rs-profile-revision-log-0-2/README.md` | This record. Not added to `docs/README.md` (`validation/` is outside `check_docs_index.py` scan patterns). |

`docs/README.md` and `docs/DEVELOPMENT_PLAN.md` are unchanged: the profile is
already index-linked (DEVELOPMENT_PLAN §18), and no new scanned file was
created.

## Existing coverage mapping (AGENTS §7)

| Requirement | Classification | Evidence |
|---|---|---|
| RS profile ↔ blueprint id traceability (RS-C01..17, IM-01..30, once each, first-cell keys) | sufficiently covered | `scripts/check_rs_profile_traceability.py` + `--self-test`; the new §0 table's first cells (`0.1`, `0.2`, `개정`) cannot match `ID_KEY`, so the existing checker covers this node's risk — no new test added |
| docs index coverage | sufficiently covered | `scripts/check_docs_index.py` + `--self-test`; no scanned file added or renamed |
| register self-consistency | sufficiently covered | `scripts/check_status_register.py` + `--self-test`; register untouched |
| revision-log section lists = actual 0.1→0.2 delta | covered by this node's derivation | per-PR `git show` above, recorded in the table; no automated checker exists for this (a git-diff-vs-table checker would be new tooling outside this node's scope) |

No new tests: the two predicates this file can break (id traceability, index
coverage) already have CI-wired checkers, cited above.

## Commands and results

| Command | Result |
|---|---|
| `git status --short --branch`, `git rev-parse HEAD origin/main` | Exit 0. `agent/kix-audit6-rs-profile-revision-log-0-2` at `50af6096a84f72c8c1249f23279dab0b279e4c82` = local `origin/main`; clean at start. `git fetch` not run (network forbidden this session). |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after edits) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values, unchanged. |
| `git log 9b12626b..HEAD -- <profile>` (per-commit) | Exit 0. Exactly `45c08d5` (rs-3a) and `954e6e3` (rs-3b); see derivation table. |
| `git diff --stat 9b12626b..HEAD -- <profile>` | Exit 0. 20 insertions / 11 deletions — union of the two commits, no surprise hunks. |
| `git diff 9b12626b..HEAD -- <profile>` (full read) | Every hunk falls inside §3/§5/§10/§13 and attributes to #183 or #184 as the new §0 table lists. |
| `git show 68a58ae:<profile>` / `git log 68a58ae..9b12626b -- <profile>` | 0.1 header confirmed; empty log — 「0.1 @ 9b12626b」 is the 0.1 bytes. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. All seven mutation cases detected; `self-test: pass`. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=219 ev_ids=15 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. Four cases detected; `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. All 18 cases detected; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0. `docs index ok: scanned=66 indexed=63 allowlisted=3`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. Five cases detected; `self-test: pass`. |
| `git diff --check` | Exit 0. No whitespace errors. |
| `git diff --stat origin/main -- runtime/ reference/ .aiops/ docs/tasks/ docs/decisions/ .github/` | Exit 0, empty output. Protected paths unchanged. |
| `git status --short` (final) | `M docs/contracts/RIGHTS_SCALE_PROFILE.md`, untracked `validation/2026-10-14-rs-profile-revision-log-0-2/`. Nothing else. |

## Not run

Cargo/rustc suites under `runtime/` (`ktx-kernel.yml` equivalents): no Rust
source changed, so the closest local equivalent is the empty-diff check on
`runtime/` above — recorded as NOT_RUN-for-cargo rather than claimed. The
OpenAPI/SDK checker steps and the heavy (Sui/Move/localnet/ZK) verification
were not run here; `docs/contracts/*` is a verifier input in both workflow
classifiers, so the exact-head PR run of KIX + KTX protocol verification is
still required and is the supervisor's to trigger. `bootstrap.sh` (installs;
no network this session) not run.

## Non-claims

0.2 is a draft revision mark, not a review or an adoption: the status line
still says 초안·미검토·미측정, and confirmation remains Astra architecture
review plus the user merge (audit finding 5 stays visible — no Astra review
record exists in this tree). Nothing here marks the RS-3a/RS-3b edits
themselves reviewed; the log only names what changed and where the evidence
lives. The RS-1 authorization, `state/rs-1.decision_answer.md` and the
register's RS-1 row still cite 0.1 @ `9b12626b`; they remain accurate as
written and were not edited. No contract semantics, RS-C/IM/RR id, status
notation, task document, `.aiops/` file, decision record, or CI file was
changed. In-body 「0.1」 sentences in §4/§6/§7/§8/§9/§11/§13 are intentionally
left as 0.1-era statements, covered by the inheritance sentence — not an
oversight.

## Follow-up candidates

- Astra ARCHITECTURE review records for the five A3 merges (audit finding 5):
  if they happened, their location needs recording; until then 0.2's
  미검토 status stands and RS-4 builds on unreviewed text.
- `state/rs-1.decision_answer.md` archival to `docs/decisions/archive/` is a
  sibling node's scope (RS-1 gate closure), not this one's.
- A checker pairing the revision log's section lists against the actual
  per-PR diffs would prevent future header drift; new tooling is outside this
  node's scope.
