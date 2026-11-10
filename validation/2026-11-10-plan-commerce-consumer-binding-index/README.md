# plan-commerce-consumer-binding-index — builder validation

## Task and basis

Task ID: `plan-commerce-consumer-binding-index`. The task input is the
supervisor-supplied node specification and read-only design plan in the builder
prompt. No issue was created and no corresponding task document exists under
`docs/tasks/`; this is not ASTRA program mode. Audit floor A2; no Astra gate;
no merge authority.

Observed `origin/main` (cached local ref), base and starting branch HEAD:
`5efab699e9b0711aef471ab9af44bd37ea6094a4`.

Branch: `agent/kix-plan-commerce-consumer-binding-index`.

`git fetch origin main` was **NOT_RUN** under the supervisor's no-network
instruction; remote freshness is unverified. No local base delta was observed.

Implementation/final delivery head: unavailable; the supervisor owns commits.
Merge commit and post-merge checks: not applicable; no merge performed.

## What was added

A non-normative, machine-readable consumer binding index and a stdlib-only
checker that binds every published command and owner-decided read name to its
pinned source, body schema, gate envelope, offline journey evidence and exactly
one status:

- [index JSON](../../docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json) —
  84 commands (40 core + 44 FSM) and 13 read names with exactly one status
  each, 14 pinned artefacts, the BOOTSTRAP profile facts, the 44-step journey
  fixture binding, external consumer expectations as `UNVERIFIED`, SD1 as
  User-owned and `OPEN`, and explicit non-claims.
- [checker](check_consumer_binding_index.py) — derives the command set from
  `integration_gate.catalogue.load_catalogue`, recomputes every sha256 and Git
  blob, cross-checks the producer qualification tuple, re-derives the journey
  fixture, rejects drift, unknown/missing/reordered/duplicate commands, a read
  query upgraded from `NOT_BOUND`, broken journey references, malformed or
  multiple statuses, unresolved body-schema pointers and semantic claims.
  `--self-test` mutates in-memory copies only.
- [boundary map extension](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md) —
  one new section between “Unavailable consumer bindings” and “Evidence and
  non-claims”. Every existing row and statement is preserved; the map is not
  replaced.
- `docs/README.md` — one consumer-surface section edit linking the index and
  this record.
- this validation record.

The index is navigation. It publishes no read query, adds no catalogue entry,
changes no protocol behavior, chooses no policy value and does not replace the
existing boundary map. **BOOTSTRAP is not consumer acceptance.**

### Status allocation

| Surface | Count | Status |
|---|---:|---|
| Core commands | 40 | `BOOTSTRAP_SCHEMA_BOUND` |
| FSM commands exercised by the offline journey fixture | 27 | `MOCK_EVIDENCE` |
| FSM commands not exercised by that fixture | 17 | `BOOTSTRAP_SCHEMA_BOUND` |
| Owner-decided read names | 13 | `NOT_BOUND` |
| Semantic SDK consumer | 1 | `HOLD_SEMANTIC` |

`MOCK_EVIDENCE` means named steps of
`commerce_journey_conformance_v1.json` call that published action. It is
offline mock-fixture evidence only, not delivered consumer behavior, funds,
finality, venue admission or production evidence. The 44 step ids are bound
exactly once each; the union of references is all 44 steps.

## Complete changed-path list

- `docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json` — new index record.
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md` — one added section; no
  existing content removed.
- `docs/README.md` — one consumer-surface section edit.
- `validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`
  — new stdlib checker (deliberately outside `scripts/`, so no CI wiring edit
  is required; `check_ci_checker_wiring.py` scans only `scripts/check_*.py`).
- `validation/2026-11-10-plan-commerce-consumer-binding-index/README.md` —
  this record.

No runtime, reference, protocol-contract, generated, manifest-bound,
OpenAPI, SDK, `.aiops`, `docs/tasks`, CI or locked-blob change.

## Existing coverage mapped before editing

| Requirement | Coverage classification | Existing coverage / gap addressed |
|---|---|---|
| 84 published commands = 40 core + 44 FSM | Sufficient behavioral coverage | `scripts/check_openapi_contract.py`, `scripts/check_integration_gate_openapi.py` and `integration_gate.catalogue.load_catalogue` derive the set. The index adds one cross-record pin; the checker re-derives the set independently. |
| FSM actions, machines and subject fields | Sufficient behavioral coverage | `integration_gate.fsm_contract.drift_problems`; the FSM command contract pin. The index adds the per-command `bodySchemaRef` and `subjectField` bindings. |
| Contract/source/SDK/profile pin identity | Sufficient behavioral coverage | `scripts/check_producer_qualification_tuple.py` pins the same artefacts. The index cross-checks its shared pins against that tuple. |
| Journey behavior and read non-binding | Sufficient behavioral coverage | `reference/booking_resale_admission/test_commerce_journey_conformance.py` (6 tests) exercises all 44 steps and requires the 13 read names to be absent. The index adds the per-action-to-step map. |
| 13 read names stay `NOT_BOUND` | Partially covered | `scripts/check_read_model_source_map.py` and the journey test assert catalogue absence; no prior record bound every name to its candidate vector digest and status in one machine-readable index. The index supplies navigation only. |
| Semantic `HOLD`, SD1 ownership, external consumer status | Partially covered | The `bootstrap-2` profile/manifest non-claims and the SD1 record. The index restates `HOLD_SEMANTIC`, `UNVERIFIED` external expectations and User-owned `OPEN` SD1 without resolving them. |
| One check over all commands, reads and journey references | Previously not covered | New checker and `--self-test`; no existing checker validated a single consumer-binding record. |

No new runtime test was necessary: the touched paths are documentation and a
stdlib validation checker, and the underlying command, FSM and journey
behavior already has deterministic coverage.

## Commands actually run and actual results

All commands ran in this worktree, in the foreground, with
`PYTHONDONTWRITEBYTECODE=1` and `-B` for Python. Observed Python 3.12.

| Command | Actual result |
|---|---|
| `git rev-parse HEAD origin/main`; `git branch --show-current` | both `5efab699e9b0711aef471ab9af44bd37ea6094a4`; branch `agent/kix-plan-commerce-consumer-binding-index`. |
| `git status --short` (initial) | clean. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`; match the required blobs in every run. |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | exit 0; detected missing command, unknown command, drifted artifact digest, read query upgraded from `NOT_BOUND`, broken journey reference, journey action mismatch, multiple status fields, absent status field, unresolved body-schema pointer and injected semantic claim; `self-test: pass (10 negative controls)`. |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | exit 0: `consumer binding index ok: commands=84 core=40 fsm=44 mock=27 bootstrap=57 reads=13 not_bound=13 journey_steps=44 journey_actions=27` / `non-normative navigation only; BOOTSTRAP is not consumer acceptance`. |
| `python3 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_journey_conformance.py' -v` | exit 0: 6 tests, `OK`. |
| `python3 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | exit 0: `commands=84 core=40 fsm=44 reads=13`; `self-test: pass`. |
| `python3 -B scripts/check_read_model_source_map.py` and `--self-test` | exit 0: `queries=13 anchors=128 catalogues=2 citations=145`; `self-test: pass`. |
| `python3 -B scripts/check_openapi_contract.py` and `--self-test` | exit 0: `commands=84 core=40 fsm=44` with source sha256/blob; `self-test: pass`. |
| `python3 -B scripts/check_integration_gate_openapi.py` and `--self-test` | exit 0: `commands=84 productionEndpoint=false publicHost=false`; `self-test: pass`. |
| `python3 -B scripts/check_docs_index.py` (first run, before this README existed) | exit 1: `broken index link: validation/2026-11-10-plan-commerce-consumer-binding-index/README.md`. |
| `python3 -B scripts/check_docs_index.py` and `--self-test` (final run) | exit 0; index coverage and seven negative controls pass. |
| `python3 -B scripts/check_ci_checker_wiring.py` and `--self-test` | exit 0: `scripts=36 plain=35 self_test=36 self_test_only=1 docs=22 citations=99`; 13 negative controls pass. |
| `python3 -B scripts/check_ci_test_discovery.py` and `--self-test` | exit 0: `reference_suites=8 node_tests=8 modules=4 excluded=3`; 18 negative controls pass. |
| Every `python3` invocation in the workflow’s `Stdlib offline document checks` block (65 invocations), run verbatim from `.github/workflows/protocol.yml` | first run: 63 pass, 2 fail only on the missing validation README; final run after this README existed: `failures=0`. |
| `git diff --check` | exit 0; no whitespace errors. |
| `git diff --name-only` | exactly the five paths listed above. |
| `git diff --name-only origin/main...HEAD` | empty; the supervisor owns the commit, so no implementation head exists yet. |
| `git diff --exit-code -- .aiops docs/tasks runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1 docs/contracts docs/contracts/openapi sdk/generated sdk/compat sdk/conformance .github/workflows` | exit 0; no protected diff. |
| `git status --short` (final) | exactly the five changed paths, all untracked/modified as listed above; no other path. |

Not run: `cargo test`, `cargo clippy` and the full Rust workspace suite. No
Rust or other runtime source changed. Both workflows classify `docs/*` and
`validation/*` as docs-only, so the expected CI path is the always-on stdlib
block; exact-head CI is still the supervision gate.

## Preservation

| Path | Required | Observed before and after |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`reference/v0.3-rc1/**` was read only. No `.aiops/`, `docs/tasks/`, contract,
OpenAPI, SDK output, manifest, generated artefact, CI or runtime file changed.

## Non-claims and remaining uncertainty

- This is builder-authored navigation and identity evidence, not non-author
  exact-head review, an Astra audit, a merge-ready claim or User approval.
- `BOOTSTRAP_SCHEMA_BOUND` binds catalogue/schema identity only. `MOCK_EVIDENCE`
  is offline fixture evidence only.
- No semantic qualification, N/N-1 qualification, production qualification,
  durable/persistent read model or integration-gate production qualification is
  made.
- No read query is published, bound or added to either catalogue; candidate
  fixtures remain non-conformance evidence.
- External `kix-commerce-apps` consumer expectations are `UNVERIFIED`: the
  adapter is not present in this repository and no external invocation was
  performed.
- SD1 remains `OPEN`, owner `User`, unresolved; no option, waiver or verifier
  order is selected.
- Policy values (visibility, limits/defaults, cursor lifetime, sort keys, open
  phases, retention/history and legal treatment) remain `UNDETERMINED` with
  their recorded owners; this node selects none.
- The record pins bytes at the observed base. It does not predict a future
  merge commit or certify the tuple after later commits.

## Required evidence report (AGENTS.md §14)

- Task ID / document: `plan-commerce-consumer-binding-index`; supervisor-
  supplied node spec and design plan; no `docs/tasks/` document and no issue.
- Observed `origin/main` / base: `5efab699e9b0711aef471ab9af44bd37ea6094a4`.
- Implementation head: unavailable; supervisor owns commit/push.
- Exact final task head: unavailable.
- Merge commit: none; no merge performed.
- Changed paths: the five paths above.
- Locked blobs: both match before and after.
- Existing coverage mapping: table above.
- New tests/evidence: new index and checker; `--self-test` with 10 negative
  controls; no runtime test added. The checker covers a previously uncovered
  one-record command/read/journey binding.
- Commands and results: table above; all executed commands exit 0 in the final
  state.
- Exact-head KTX CI run ID/status/conclusion: **NOT_RUN / unavailable**.
- Exact-head KIX protocol CI run ID/status/conclusion: **NOT_RUN /
  unavailable**.
- Post-merge main CI: **not applicable**.
- Contract violations found: none.
- Contract-undefined characterizations: external consumer method signatures
  and expected behavior remain **UNVERIFIED**; SD1 remains **OPEN**; policy
  values remain **UNDETERMINED**.
- Explicit non-claims: above.
- Remaining uncertainty: exact-head review/CI, future merge state and the
  external consumer contract.

## Deviations

- `git fetch origin main` was not run (supervisor no-network instruction); the
  record names the cached local `origin/main` and marks remote freshness
  unverified.
- No commit/push/PR/issue/comment was made; the supervisor owns delivery, so
  implementation and final head SHAs are unavailable.
- The checker is under `validation/`, not `scripts/`, by design: this avoids a
  CI edit and keeps the change docs-only. It is not required to be wired into
  `protocol.yml` by `check_ci_checker_wiring.py`, which scans only
  `scripts/check_*.py`.
- The machine-readable index has no separate human-readable `docs/status/*.md`
  companion; the boundary-map section and this record are the navigation.
  `check_docs_index.py` scans `docs/status/*.md` and `validation/*/README.md`,
  so the JSON needs no index-link entry of its own.

STATUS: READY
