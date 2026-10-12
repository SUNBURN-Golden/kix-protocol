# rs0-review-pack

Node: `plan-rs0-review-pack`. Builder-authored RS-0 acceptance review pack
(`docs/status/RS0_REVIEW_PACK.md`) plus a stdlib-only id-traceability
checker (`scripts/check_rs_profile_traceability.py`), preparing the
evidence the Astra review of `docs/contracts/RIGHTS_SCALE_PROFILE.md` 0.1
and `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md` needs. The pack
reviews, accepts and changes nothing; it does not unblock `rs-1`.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1791773087 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results
below are not exact-head CI. There is no KTX kernel verification run ID
and no KIX protocol verification run ID for a head that contains these
files.

Observed `origin/main` and branch HEAD at session start:
`ba352dfe9789af89983e9c1b1a303461ea240016` (merge of PR #167).
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which
equals the task-branch HEAD (`git status -sb` shows the branch tracks
`origin/main` with no divergence).
Branch: `agent/kix-plan-rs0-review-pack`.

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
exited 0. The profile, the RS-0 decision record, the blueprint and the
contracts are byte-identical to the recorded base.

## What this record points at

`docs/status/RS0_REVIEW_PACK.md` is new. Its first lines state it is not a
review, not an acceptance and not a change of status, and that it is
builder-authored. It contains: (1) a 47-row traceability table mapping
every blueprint RS-C01..RS-C17 and IM-01..IM-30 to the profile section
that defines it, the proposed test id and the owning node; (2) the
profile's own OPEN/UNDETERMINED/DECISION_REQUIRED items with named owners
and the RS node each gates — no value chosen; (3) findings quoted with
line numbers classified A/B/C under AGENTS.md §8 (four A items, six B
items, no C found; no silent fix); (4) the three `rs-1` unlock routes
with an exact User-sentence template each and what stays locked, none
chosen; (5) a ten-question Astra reviewer checklist; and a non-claims
footer.

`scripts/check_rs_profile_traceability.py` is new: stdlib only, counts
each `RS-C\d{2}`/`IM-\d{2}` id used as a first-column markdown table key
in the blueprint and the profile, and reports ids missing from,
duplicated in or extra to either document. `--self-test` mutates
in-memory copies and requires each check to catch its break, including
removed-id detection on both sides. It is not wired into CI — see
follow-ups.

`validation/2026-10-12-rs0-review-pack/README.md` is this record. Not
added to `docs/README.md`.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/RS0_REVIEW_PACK.md` | New review pack. |
| `scripts/check_rs_profile_traceability.py` | New checker. |
| `validation/2026-10-12-rs0-review-pack/README.md` | This record. |

## Commands and results

| Command | Result |
|---|---|
| `git status -sb`, `git rev-parse HEAD`, `git rev-parse origin/main` | Exit 0. Branch tracks `origin/main`; both SHAs `ba352dfe9789af89983e9c1b1a303461ea240016`. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. Prints detection of removed RS-C01/IM-01 (missing in profile), duplicated rows, removed/duplicated RS-C03 in blueprint, extra `RS-C99`/`IM-99`; `self-test: pass`. |
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
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=168 ev_ids=12 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, OK. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed across 9 test binaries, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --check` | Exit 0. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/blueprints docs/decisions runtime` | Exit 0. Protected paths unchanged. |
| `git status --short` / `git diff --name-only origin/main` | Untracked only: `docs/status/RS0_REVIEW_PACK.md`, `scripts/check_rs_profile_traceability.py`, `validation/2026-10-12-rs0-review-pack/`. Nothing else. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` (and `--self-test`) | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change. |
| `npm --prefix sdk run conformance` | Exit 1 under node 20: `ERR_UNKNOWN_FILE_EXTENSION` importing `sdk/src/client.ts` (the suite needs node 24 type stripping). |
| `npm --prefix sdk run verify-compat` | Exit 1 under node 20: `ERR_UNKNOWN_FILE_EXTENSION` importing `sdk/src/jsonschema.ts`. Same class of failure. |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and
performs pip/npm/Sui installs — this session has Python 3.13.5, node
20.19.2 and no network. Move package tests, `reference/v0.3-rc1` client
vitest suites, and hosted KTX/KIX runs for a head containing these files:
not run here.

CI classification note: `scripts/check_rs_profile_traceability.py` is a
non-documentation path under both classifiers
(`.github/workflows/protocol.yml:87`, `.github/workflows/ktx-kernel.yml:79`),
so a pull request containing this node is **not** docs-only; hosted
exact-head runs will execute the full suites.

## Non-claims

The pack reviews, accepts and changes nothing: it is builder-authored
evidence, not the non-author exact-HEAD review AGENTS.md requires, and
not a status change for RS-0 or RS-1. No profile, decision-record,
blueprint or contract byte was edited; no policy value, ceiling, ceremony
power, path or command was chosen; every UNDETERMINED/DECISION_REQUIRED/
OPEN item keeps its named owner. The new checker is a convenience check,
not a contract gate, and is not wired into CI. Local suite passes are not
exact-head CI and are not independent verification. No Move, circuit or
localnet code was added. No real funds, real PG/bank/KYC calls, public
endpoints, Sui testnet/mainnet, R2, storage engine, secrets or production
runtime were touched or needed.

## Follow-up candidates

- Wire `scripts/check_rs_profile_traceability.py` into a suitable CI step
  (follow-up candidate only; not done here — CI wiring is a User decision
  per the `rs-1` stop record).
- Finding B-4 in the pack (package path/module name deferred to
  RS-1/RS-2 although the blueprint assigns the choice to RS-0) is a
  review question for Astra; resolving it may require a profile revision,
  which is outside this node.
