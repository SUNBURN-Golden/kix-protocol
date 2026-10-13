# i12-review-pack

Node: `plan-i12-review-pack`. Builder-authored, non-author review pack for the
I12 cut proof (`docs/status/I12_REVIEW_PACK.md`) plus a stdlib-only
id/section checker (`scripts/check_i12_proof_ids.py`), preparing the evidence
the non-author independent review of
`docs/decisions/CUT_PROOF_I12_20261008.md` and the User's trust-policy
approval need. The pack reviews, accepts and changes nothing; it records no
option 1/2/3 acceptance and does not close I12.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1791848082 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results
below are not exact-head CI. There is no KTX kernel verification run ID
and no KIX protocol verification run ID for a head that contains these
files.

Observed `origin/main` and branch HEAD at session start:
`5e8ee3f1882d97f1c442fe485407e51822ec22ce`.
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which
equals the task-branch HEAD (`git status -sb` shows the branch tracks
`origin/main` with no divergence).
Branch: `agent/kix-plan-i12-review-pack`.

Working directory: repository root of this worktree. Python 3.13.5
(workflow installs 3.12), rustc/cargo 1.98.1 (matches
`rust-toolchain.toml`), node 20.19.2 (toolchains.json pins nodeMajor 24 —
see Attempted but environment-blocked).

## Locks

`git hash-object` after all edits (the files were never opened for edit;
`git diff --quiet origin/main -- runtime/` exits 0):

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github
docs/tasks docs/contracts docs/blueprints docs/decisions runtime`
exited 0. The proof document, the contracts, the blueprint, the open-inputs
row and the kernel are byte-identical to the recorded base.

## What this record points at

`docs/status/I12_REVIEW_PACK.md` is new. Its first lines state it is not a
review, not an acceptance and not a change of status, and that it is
builder-authored. It contains: (1) a 14-row coverage table mapping every
proposition P1–P4 and assumption A1–A10 of the proof to the exact existing
evidence (kernel source/test paths and lines for generation fencing,
retained-conflict membership and commit-before-send ordering) and marking
each row machine-checked in-memory model only, prose-only, or depending on
unimplemented pieces; (2) the owner-only inputs — A9 reviewer identity and
same-version review evidence, per-assumption trust-policy approval, the §5
option 1/2/3 acceptance record (none recorded), and the
DECISION_REQUIRED · Astra / D-E items — none supplied; (3) findings quoted
with line numbers classified A/B/C under AGENTS.md §8 (four A items, four B
items including two line-drift records, no C found; no silent fix); (4) a
ten-question reviewer checklist; and a non-claims footer.

`scripts/check_i12_proof_ids.py` is new: stdlib only, verifies the proof
still defines P1–P4 as `### P` headings and A1–A10 as first-column keys of
its §4 table exactly once each, that the pack carries each id exactly once
as a first-column key, and that every `proof §N` reference in the pack
resolves to a `## N.` heading in the proof. `--self-test` mutates in-memory
copies and requires each check to catch its break, including removed-id
detection on both sides. It is not wired into CI — see follow-ups.

`docs/README.md` gained one pointer row after the I12 row of the
2026-10-08 merged-documents index table. Nothing else in the file changed.

`validation/2026-10-13-i12-review-pack/README.md` is this record.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/I12_REVIEW_PACK.md` | New review pack. |
| `scripts/check_i12_proof_ids.py` | New checker. |
| `docs/README.md` | One pointer row added (`+1` line in `git diff`). |
| `validation/2026-10-13-i12-review-pack/README.md` | This record. |

## Commands and results

| Command | Result |
|---|---|
| `git status -sb`, `git rev-parse HEAD`, `git rev-parse origin/main` | Exit 0. Branch tracks `origin/main`; both SHAs `5e8ee3f1882d97f1c442fe485407e51822ec22ce`. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. Prints detection of removed P1 heading (missing in proof), removed A5 row (missing in proof), removed A9 pack row (missing in pack), extra `A11` pack row, extra `P9` proof heading, unresolved `proof §9` citation; `self-test: pass`. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=170 ev_ids=12 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. Ran 58 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. Ran 22 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. Ran 47 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. Ran 26 tests, OK. |
| same for `reference/ai_delegation` | Exit 0. Ran 22 tests, OK. |
| same for `reference/token_reward` | Exit 0. Ran 61 tests, OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `commands=84 core=40 fsm=44`, sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`, gitBlob `619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, OK. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed across 8 test binaries, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --check` | Exit 0. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/blueprints docs/decisions runtime` | Exit 0. Protected paths unchanged. |
| `git status --short` / `git diff --stat origin/main` | `M docs/README.md` (+1 line); untracked: `docs/status/I12_REVIEW_PACK.md`, `scripts/check_i12_proof_ids.py`, `validation/2026-10-13-i12-review-pack/`. Nothing else. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change. |
| `npm --prefix sdk run conformance` | Fails under node 20: `ERR_UNKNOWN_FILE_EXTENSION` importing `sdk/src/client.ts` (the suite needs node 24 type stripping). |
| `npm --prefix sdk run verify-compat` | Fails under node 20: `ERR_UNKNOWN_FILE_EXTENSION`. Same class of failure. |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and
performs pip/npm/Sui installs — this session has Python 3.13.5, node
20.19.2 and no network. Move package tests, `reference/v0.3-rc1` client
vitest suites, and hosted KTX/KIX runs for a head containing these files:
not run here.

CI classification note: `scripts/check_i12_proof_ids.py` is a
non-documentation path under both classifiers
(`.github/workflows/protocol.yml:87`, `.github/workflows/ktx-kernel.yml`),
so a pull request containing this node is **not** docs-only; hosted
exact-head runs will execute the full suites.

## Non-claims

The pack reviews, accepts and changes nothing: it is builder-authored
evidence, not the non-author independent review that open-inputs row I12
requires, and not a status change for I12. No proof, contract, blueprint,
decision-record or kernel byte was edited; no policy value, time-source
number, H_g finality policy, path or command was chosen; every
UNDETERMINED/DECISION_REQUIRED item keeps its named owner. The new checker
is a convenience check, not a contract gate, and is not wired into CI. The
parked bounded-model node (`plan-i12-cut-proof-bounded-model`,
`reference/cut_proof_model/`) is cited, not built. Local suite passes are
not exact-head CI and are not independent verification. No Move, circuit or
localnet code was added. No real funds, real PG/bank/KYC calls, public
endpoints, Sui testnet/mainnet, R2, storage engine, secrets or production
runtime were touched or needed.

## Follow-up candidates

- Wire `scripts/check_i12_proof_ids.py` into a suitable CI step (follow-up
  candidate only; not done here — the RS-profile checker's wiring was a
  separate merged node, PR #170).
- Findings B-1/B-2 in the pack (the proof's stale dev-plan and blueprint
  line numbers, cited content verified verbatim at the drifted lines) are
  candidates for a later proof revision; correcting the proof is outside
  this node.
- If the User names the A9 reviewer, the review artefact will need a
  pointer row in the capability register and possibly the open-inputs row —
  separate task.
