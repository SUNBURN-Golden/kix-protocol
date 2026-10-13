# audit5-read-model-source-map-checker-decouple

Node: `audit5-read-model-source-map-checker-decouple`. Rewrite
`scripts/check_read_model_source_map.py` so the expected
`SOURCE_FOUND`/`SOURCE_MISSING` status per query, the must-not-exist
anchors, and the catalogue-absence expectation are read from the tables
in `docs/contracts/READ_MODEL_SOURCE_MAP.md` instead of a hardcoded
dict; keep hard failures for stale line anchors, unresolved files,
out-of-range citations and blob drift; keep `--self-test` covering every
retained check; add the §6 sentence that a successor node updates the
table rows in the same PR as its source change. Removes the PR #172 gate
contradiction that the approved `read-model-reference` node must break.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2.
Source: KIX audit #5 finding 1 (`/workspace/kix-run/audits/audit_5_20261013.md`;
loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close
an issue, or comment. There is no implementation commit SHA and no final
task head SHA yet. Local results below are not exact-head CI. There is
no KTX kernel verification run ID and no KIX protocol verification run
ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`db9152ab1c5ef113b8727749d4309ec70505480f`.
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which
equals the task-branch HEAD.
Branch: `agent/kix-audit5-read-model-source-map-checker-decouple`.

Working directory: repository root of this worktree. Python 3.13.5
(workflow installs 3.12), cargo via `runtime/` toolchain, node 20.19.2
(toolchains.json pins nodeMajor 24 — see Attempted but
environment-blocked).

## Locks

`git hash-object` on the working tree after all edits (both files were
never opened for edit; `git diff --quiet origin/main -- runtime/`
exits 0):

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks runtime .github`
exited 0.

## What this change does

The checker no longer carries the `QUERY_STATUS` dict. What it now does:

- `QUERY_NAMES` keeps the 13 owner-decided names only (the set is closed
  by user decision, `READ_MODEL_QUERIES.md:15`, and pinned by the blob
  check). Expected statuses are **not** in code.
- The §2 query table row's status cell is the expectation. It must be
  `SOURCE_FOUND` or `SOURCE_MISSING` and agree with the §6 anchor table:
  `SOURCE_FOUND` needs a `` `name` 원천 `` label row and no `-` anchor
  whose token holds `def name(`; `SOURCE_MISSING` needs at least one
  such `-` anchor and no `원천` row. Mismatch → `status drift for
  <name>: …`. A `list`/`point` kind cell on a name outside the 13 is an
  `unknown query row` failure, so a fourteenth query cannot slip in.
- A new §5 catalogue table `| id | 대상 | 카탈로그 파일 | 기대 |` (C01,
  C02) carries the expectation: `ABSENT` forbids all 13 names in
  `commands`; `PRESENT: a, b` requires exactly the listed names there
  and the rest absent. Each file in `CATALOGUES` must appear exactly
  once; a successor node adds a row for a new catalogue file.
- Retained verbatim: anchor file/line/token checks and `-` semantics,
  anchor-id dedupe, `path:line` citation range check, `git blob` drift
  check, `files=` injection for self-test.
- Doc §6 rule line documents the `` `name` 원천 `` label convention and
  gains the sanctioned sentence: a successor node updates the table
  rows (status, anchors, catalogue expectation, blob citation) in the
  same PR as its source change.

`--self-test` covers all retained checks plus the new ones: unknown
query row, `원천` label on a `SOURCE_MISSING` query, dropped absence
anchors, flipped catalogue expectation, dropped catalogue row.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_read_model_source_map.py` | Data-driven rewrite: expected status derived from §6 anchor labels, catalogue expectations parsed from §5 C-table; `QUERY_STATUS` dict removed; self-test extended to 16 cases. |
| `docs/contracts/READ_MODEL_SOURCE_MAP.md` | §5 gains the machine-readable catalogue-expectation table (C01, C02, both `ABSENT`); §6 rule line documents the `원천` label convention and gains the successor-update sentence. |
| `validation/2026-10-13-audit5-source-map-checker-decouple/README.md` | This record. Not added to `docs/README.md`. |

## Coverage mapping

- Query status ↔ source agreement: previously hardcoded (the dict);
  now covered by the `원천`-label / `def name(` absence-anchor
  consistency rule, verified by `status flipped`, `source label on
  missing query` and `absence anchors dropped` self-test cases.
- Catalogue absence: previously hardcoded over two fixed paths; now
  covered by the §5 C-table (`ABSENT`/`PRESENT:` grammar), verified by
  `catalogue expectation flipped`, `catalogue row dropped` and the
  retained `query in core catalogue` case.
- Stale anchors, unresolved files, out-of-range citations, blob drift,
  missing/duplicated query rows, duplicated anchor ids: retained,
  verified by the unchanged self-test cases.

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD`, `git rev-parse origin/main`, `git status --porcelain`, `git branch --show-current` | Exit 0. HEAD = origin/main = `db9152ab1c5ef113b8727749d4309ec70505480f` on `agent/kix-audit5-read-model-source-map-checker-decouple`; clean tree at start. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_read_model_source_map.py` (before edits) | Exit 0. `queries=13 anchors=128 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` (before edits) | Exit 0. `self-test: pass` (11 cases). |
| `python3 scripts/check_read_model_source_map.py` (after edits) | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` (after edits) | Exit 0. Detects all 16 mutations (anchor line moved/out-of-range/token changed, query row dropped/duplicated, unknown query row `get_zilch`, status flipped, `원천` label on missing query, absence anchors dropped, catalogue expectation flipped, catalogue row dropped, rmq cite out of range, blob id mismatch, cited surface renamed, absent surface added, query in core catalogue); `self-test: pass`. |
| Flip dry-run: `sed` `list_shows` row `SOURCE_MISSING`→`SOURCE_FOUND`, run checker, restore | Exit 1 as required: `` status drift for list_shows: declared SOURCE_FOUND but absence anchors remain: A04,A05 `` and `` declared SOURCE_FOUND but no `list_shows 원천` anchor ``. Restored file re-verified: exit 0. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=170 ev_ids=12 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0. `docs index ok: scanned=65 indexed=62 allowlisted=3`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. Ran 58 tests, `OK`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 22 tests, `OK`. |
| same for `reference/booking_resale_admission` | Exit 0. 47 tests, `OK`. |
| same for `reference/credit_advance_f04` | Exit 0. 26 tests, `OK`. |
| same for `reference/ai_delegation` | Exit 0. 22 tests, `OK`. |
| same for `reference/token_reward` | Exit 0. 61 tests, `OK`. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `commands=84 core=40 fsm=44`, sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`, gitBlob `619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. Architecture gate `OK`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, `OK`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed, 0 failed across 9 test binaries. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks runtime .github` | Exit 0. Protected paths unchanged. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change (`sdk/` untouched). |
| `npm --prefix sdk run conformance` | Exit 1 under node 20 (`ERR_UNKNOWN_FILE_EXTENSION` for `.ts`); the suite needs node 24 type stripping. |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and
performs pip/npm/Sui installs — this session has Python 3.13.5, node
20.19.2 and no network. Hosted KTX/KIX runs for a head containing these
files: not run here.

CI classification note: `scripts/check_read_model_source_map.py` and
`docs/contracts/READ_MODEL_SOURCE_MAP.md` are non-documentation paths
under both classifiers (`docs/contracts/*` is a verifier input), so this
change is **not** docs-only; hosted exact-head runs will execute the
full suites.

## Contract findings

- Contract violations found: none.
- Contract-undefined characterizations found: none. The `원천` label
  convention and the §5 expectation grammar are new doc-parse contracts
  this node introduces inside its own scope, documented in §5/§6 and
  the checker docstring.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or
operational, and keeps the operational count at 0. The rewrite changes
where expectations live (document, not code); it does not weaken the
gate — a `SOURCE_FOUND` claim still needs a verified `원천` anchor, a
`SOURCE_MISSING` claim still needs a verified `def name(` absence
anchor, and catalogue expectations still fail closed on missing or
malformed rows. Local passes are not exact-head CI and are not
independent verification.

## Remaining uncertainty and follow-ups

- A successor that names the `원천` label differently gets a
  `status drift` failure — fails closed by design; the convention is
  documented in §6.
- Exact-head KTX kernel verification and KIX protocol verification runs
  happen in hosted CI after the supervisor commits and the PR opens;
  not observed here.
