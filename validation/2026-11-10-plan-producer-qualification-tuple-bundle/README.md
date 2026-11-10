# plan-producer-qualification-tuple-bundle — builder validation

## Task and basis

Task ID: `plan-producer-qualification-tuple-bundle`. The task input is the
supervisor-supplied node specification and read-only design plan in the builder
prompt. No issue was created and no corresponding task document exists under
`docs/tasks/`; this is not ASTRA program mode. Audit floor A2; no Astra gate;
no merge authority.

Observed `origin/main` before work, base and starting branch HEAD:
`19cdc1c6393e88528d3918e0f4f1f37645a34042`.

Branch: `agent/kix-plan-producer-qualification-tuple-bundle`.

Implementation/final delivery head: unavailable; the supervisor owns commits.
Merge commit and post-merge checks: not applicable; no merge performed.

## What was added

A non-normative, machine-readable record of the current BOOTSTRAP producer
tuple and a stdlib-only identity checker:

- [record JSON](../../docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json) —
  pins every artefact sha256 (and Git blob where recorded), the 84 commands
  (40 core + 44 FSM), the 44 FSM actions, the five machines, the two OpenAPI
  documents, the SDK catalogue/generator/toolchain, the `bootstrap-2`
  profile/manifest/sidecar, both conformance vectors, the five read-model
  candidate fixtures and their manifest, the 13 read names as `NOT_BOUND`, the
  semantic `HOLD`, and SD1 as `OPEN` with owner `User`.
- [human companion](../../docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md) —
  status meanings and non-claims.
- [checker](../../scripts/check_producer_qualification_tuple.py) — recomputes
  every recorded digest, re-derives the command/action/read sets, cross-checks
  the OpenAPI, manifest, profile, sidecar and toolchain pins, and fails on
  drift. `--self-test` mutates in-memory copies and requires detection of a
  mutated blob digest, a missing command and a mismatched gate source pin.
- `.github/workflows/protocol.yml` — additive wiring of the new checker, plain
  and `--self-test`, in the always-run `Stdlib offline document checks` block.
  This is required by `scripts/check_ci_checker_wiring.py` for every
  `scripts/check_*.py`; it suppresses no failure.
- `docs/README.md` — index entry for the status record and this validation
  record.

The record is identity evidence only. It asserts no semantic, N/N-1,
production, audit or User approval. It does not resolve SD1, choose a verifier
order, publish a read query or regenerate any generated artefact.

## Complete changed-path list

- `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json` — new record.
- `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md` — new human companion.
- `scripts/check_producer_qualification_tuple.py` — new stdlib-only checker.
- `.github/workflows/protocol.yml` — two additive checker invocations.
- `docs/README.md` — one index section.
- `validation/2026-11-10-plan-producer-qualification-tuple-bundle/README.md` —
  this record.

No generated, runtime, reference, `.aiops`, `docs/tasks`, locked, contract,
SDK-output or CI-suppression change.

## Existing coverage mapped before editing

| Requirement | Coverage classification | Existing coverage / gap addressed |
|---|---|---|
| 84 commands = 40 core + 44 FSM | Sufficient behavioral coverage | `scripts/check_openapi_contract.py`, `scripts/check_integration_gate_openapi.py`, `scripts/check_sdk_client.py` and `integration_gate.catalogue.load_catalogue` derive the same set. The new record adds one independent identity pin; it does not replace these. |
| FSM actions and machine counts | Sufficient behavioral coverage | `integration_gate.fsm_contract.drift_problems` compares the FSM contract with live `REPLAYABLE` sets; the new checker re-derives the 44 actions and 10/11/10/4/9 machine counts. |
| Both OpenAPI blobs and source pins | Sufficient behavioral coverage | `check_openapi_contract.py` and `check_integration_gate_openapi.py` (plain and self-test). The new checker recomputes both blob digests and cross-checks their `x-kix-source` pins. |
| SDK output, generator and toolchain | Sufficient behavioral coverage | `check_sdk_client.py` regenerates in a temp directory; `npm --prefix sdk run verify-compat`. The new checker pins the committed bytes and the manifest cross-references. |
| Manifest and sidecar | Sufficient behavioral coverage | `check_sdk_client.py`, `verify_compat.mjs`, and the manifest's own `vectors`/`profile_sha256` fields. The new checker asserts sidecar = sha256(manifest) and every manifest internal digest. |
| 13 read names stay `NOT_BOUND` | Partially covered | `scripts/check_read_model_source_map.py` checks catalogue absence/source anchors and `reference/read_model/generate_fixtures.py --check` checks fixture determinism. No prior artefact listed the 13 names together with their candidate vector paths and `NOT_BOUND` status in one machine-readable record. The new record supplies that identity index only; it publishes no query. |
| Semantic `HOLD` and SD1 ownership | Partially covered | The profile grants and manifest non-claims, and the [existing SD1 record](../../docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md). The new record restates both without resolving either. |
| One recomputation gate for the whole tuple | Previously not covered | New checker and `--self-test`; no existing checker recomputed all tuple digests together. |

No new runtime test was necessary: the touched paths are documentation,
workflow wiring and a stdlib checker. Existing deterministic suites cover the
underlying command, FSM, OpenAPI and SDK behaviour.

## Commands actually run and actual results

All commands were run in this worktree, in the foreground. Python runs used
`PYTHONDONTWRITEBYTECODE=1` and `-B`; Rust ran with `CARGO_NET_OFFLINE=true`.
Observed tool versions: Python 3.12.15, Node v24.22.1, npm 11.21.1.

| Command | Actual result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD`; `git branch --show-current` | fetch succeeded; both SHAs `19cdc1c6393e88528d3918e0f4f1f37645a34042`; branch `agent/kix-plan-producer-qualification-tuple-bundle`. |
| `git status --short` (initial) | Clean. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both runs: `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`; match the required blobs. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` | exit 0: `producer qualification tuple identity ok: commands=84 core=40 fsm=44 reads=13` / `identity only; no semantic or operational qualification`. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py --self-test` | exit 0; printed `detected mutated blob digest`, `detected missing command`, `detected mismatched gate pin`, `self-test: pass`. |
| `python3.12 -B scripts/check_openapi_contract.py` | exit 0: `openapi contract pin ok: commands=84 core=40 fsm=44` with source sha256/blob. |
| `python3.12 -B scripts/check_openapi_contract.py --self-test` | exit 0: 24 negative controls then `self-test: pass`. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` | exit 0: `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false`. |
| `python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | exit 0: `self-test: pass`. |
| `python3.12 -B scripts/check_sdk_client.py` | exit 0: `sdk client pin ok: commands=84 node=24.22.1`. |
| `python3.12 -B scripts/check_sdk_client.py --self-test` | exit 0: `self-test: pass`. |
| `npm --prefix sdk run verify-compat` | exit 0: `{"ok":true,...}`. |
| `npm --prefix sdk run conformance` | exit 0: 6 tests passed, 0 failed. |
| `python3.12 -B scripts/check_docs_index.py` | First run exit 1 because this validation README did not yet exist (`broken index link`). After creation, exit 0: `docs index ok: scanned=398 indexed=363 allowlisted=35`. |
| `python3.12 -B scripts/check_docs_index.py --self-test` | First run exit 1 for the same missing target. After creation, exit 0: seven negative controls, `self-test: pass`. |
| `python3.12 -B scripts/check_ci_checker_wiring.py` | exit 0: `scripts=36 plain=35 self_test=36 self_test_only=1 docs=22 citations=99`. |
| `python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | exit 0: 13 negative controls, `self-test: pass`. |
| `python3.12 -B scripts/check_status_register.py` | exit 0: `paths=575 ev_ids=15 original32=32`. |
| `python3.12 -B scripts/check_status_register.py --self-test` | exit 0: `self-test: pass`. |
| All 65 invocations in the workflow's `Stdlib offline document checks` block, substituted as `python3.12 -B` (the added checker included) | exit 0 for all 65; `failures=0`. |
| `python3.12 -B scripts/check_read_model_source_map.py` | exit 0: `queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3.12 -B scripts/check_read_model_source_map.py --self-test` | exit 0: `self-test: pass`. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | exit 0: 9 tests, `OK`. |
| `python3.12 -B reference/read_model/generate_fixtures.py --check` | exit 0: `fixture vectors ok: files=6 seed=20261020`. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | exit 0: `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3.12 -B scripts/test_runtime_architecture.py` | exit 0: 7 tests, `OK`. |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0. |
| `git diff --check` | exit 0, no whitespace errors. |
| `git diff --exit-code -- .aiops docs/tasks runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1 docs/contracts/openapi sdk/generated sdk/compat sdk/conformance` | exit 0, no protected diff. |

Not run: `cargo test` and `cargo clippy`. No Rust source changed; the plan
noted the offline cache may lack `bcs`. No packages were fetched and no
dependency was bootstrapped. No GitHub/network action beyond the initial
`git fetch origin main`; no commit, push, PR, issue or comment was made.

## Preservation

| Path | Required | Observed before and after |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`git diff --exit-code` on `.aiops/`, `docs/tasks/`,
`reference/v0.3-rc1/`, `docs/contracts/openapi/`, `sdk/generated/`,
`sdk/compat/`, `sdk/conformance/` and the two locked kernel files is empty.
No generated artefact was rewritten: the SDK generator and fixture generator
were run only in check mode (or through the existing checker's temp
directory). No `.aiops/` or `docs/tasks/` file was read into the record as a
mutable input.

## Non-claims and remaining uncertainty

- This is builder-authored identity evidence, not non-author exact-head review,
  an Astra audit, a merge-ready claim or User approval.
- No semantic qualification, N/N-1 qualification, production qualification or
  integration-gate production qualification is made.
- No read query is published, bound or added to either catalogue. The candidate
  fixtures remain non-conformance evidence.
- SD1 is recorded as `OPEN` with owner `User`; no option, waiver or verifier
  order is selected. Its extension-profile interpretation stays UNDETERMINED.
- The record pins bytes at the observed base; it does not predict a future
  merge commit or certify that the tuple is unchanged after any later commit.
- The manifest `catalogue_input_commit`/`tree` are copied from the manifest
  producer block and name the generated SDK catalogue input, not this record
  commit.

Exact-head KTX CI run ID/status/conclusion: **NOT_RUN / unavailable**.
Exact-head KIX protocol CI run ID/status/conclusion: **NOT_RUN / unavailable**.
Post-merge main CI: **not applicable**. The supervisor owns commit, review and
CI; local checks do not replace those gates.

## Deviations

- The node has no `docs/tasks/` document; the supervisor-supplied node
  specification and design plan are the task input, as the plan anticipated.
- The design plan's optional fallback (a non-`check_` script name to avoid a CI
  edit) was not used. The new checker is additive and is wired into the
  always-run stdlib block, because `check_ci_checker_wiring.py` requires every
  `scripts/check_*.py` to run plain and with `--self-test`. No test or failure
  path is suppressed.
- `git fetch origin main` ran once at session start; no further network action
  was taken.
