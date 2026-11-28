# Validation — read-model-reference

## PR #178 fix round 4 / exact-head CI at 42f219e

This section records the exact-head CI and independent producer-source audit for
the reviewed round 3 delivery head `42f219e337a4757f32f951a0bdf36c17f4d0dcd7`,
followed by the local fixes and checks for review round 4
(`read-model-reference.review_r4.md`). Prior history in `## PR #178 fix round 3`
and `## Original builder record (2026-10-13)` is preserved below.

### Exact-head CI and producer-input audit at `42f219e`

The workflow runs and byte-comparison results in this subsection apply **only**
to `42f219e337a4757f32f951a0bdf36c17f4d0dcd7` (not to the uncommitted round 4
edits below; per AGENTS §6 and §10, CI from an earlier SHA does not transfer to
a later SHA).

| Evidence | Value at `42f219e` |
|---|---|
| Reviewed / delivered head | `42f219e337a4757f32f951a0bdf36c17f4d0dcd7` |
| Delivered tree (`git rev-parse 42f219e^{tree}`) | `574e1cb6175e8a507c2f30a6d9922fb3f4075d85` |
| Merge parents of `42f219e` | `9e5ebe7d0167782b20e3ee83b010a0396470f5ee` (round 3 fix commit) and `4609a91def3923bc12d4518a646e9e4544b201a2` (post-merge `origin/main` base, PR #533) |
| Current branch HEAD before round 4 edits | `34edf38aad3064a63159be33e1863f224eea6f9a`, merging `origin/main` `6f2d062d73fd89b8ab9053cfa4912fed85170eb8` (PR #534 `4a01955` and PR #535 `6f2d062`) onto `42f219e` |
| KTX kernel verification (at `42f219e`) | Run ID `46082725817`, `status=completed`, `conclusion=success`, https://github.com/SUNBURN-Golden/kix-protocol/actions/runs/46082725817 |
| KIX protocol verification (at `42f219e`) | Run ID `46082725833`, `status=completed`, `conclusion=success`, https://github.com/SUNBURN-Golden/kix-protocol/actions/runs/46082725833 |
| Manifest at `42f219e` | `sdk/compat/manifests/manifest.bootstrap-3.json` SHA-256 `c2cde918f061678bd45ddcbfc647633f536524cdc9738a91f1eac0356e442a92` (matches sidecar `.sha256`) |
| Manifest-pinned producer source at `42f219e` | `producer.source_commit` = `33e20f30bba3587d52c49e323de236467746e298`, `producer.source_tree` = `09d4d0f7a5ccd1c20324df7170ad64f8ca29053d` (`git rev-parse 33e20f30bba3587d52c49e323de236467746e298^{tree}` matched) |

Independent verification of delivered producer inputs at `42f219e` outside the
manifest (`git show 42f219e:<path>` vs `git show 33e20f3:<path>`, plus
independent SHA-256 and Git-blob recomputation against every matching manifest
field):

| Path | `42f219e` == `33e20f3` | Manifest match | SHA-256 at `42f219e` | Git blob at `42f219e` |
|---|---|---|---|---|
| `docs/contracts/openapi/kix-protocol.contract-only.openapi.json` | exact match | sha256 + gitBlob match | `768aabd8e756d789a20d7b2fb65c20076017eadc8e8dfafe0b9d13ef7ae7f77d` | `f096739d515a9e13e26f4fa1f89cdff421e03763` |
| `docs/contracts/openapi/kix-protocol.integration-gate.openapi.json` | exact match | sha256 + gitBlob match | `670a540a0d66efe3b62bb845a3ce5f7ead4c42dee9e35da88b967e399f108f06` | `47692773cb4857a69a7cf2286369ae2d6d317e2d` |
| `docs/contracts/openapi/fsm-command-contract.json` | exact match | sha256 + gitBlob match | `2732173bd7a4fe71cfea4201f53261aaae59b0fe5416f64fe0a4e216ecd73f5f` | `d3eaf469e4b3c1ffda7d7ecd5b52a84524525356` |
| `reference/v0.3-rc1/protocol_contract.json` | exact match | fixture path + core pin match | `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e` | `619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `sdk/generate/generate_client.mjs` | exact match | sha256 match | `227fe42fd039db31a730d975abdfeb509211083464a2e91c92eca50c1e601690` | `7fd433b6e40a949e98ffa4a3afd9c9b4ecc6fdef` |
| `sdk/generated/catalogue.ts` | exact match | sha256 match | `65cef827fa82b137e46b66f4302f2673f512ec26484910cf5de9d9f65f387b9a` | `09adec22936f2bdc95fcceff96195190a7e330c2` |
| `sdk/compat/profiles/bootstrap-3.profile.json` | exact match | `profile_sha256` match | `7adf7ccea9af9659a864140cee110880420fb5a26c306bc3597a3eed3c20326d` | `b594b96830dd8da81f3b66a0ec9c58529eb1eecd` |
| `sdk/conformance/vectors/canonical-encoding.vectors.json` | exact match | vector sha256 match | `3446c13847bb153df06c1d5d3b7f09cd3b1648ac10bb0cc76d7b65c7014e99c2` | `947773687ea9e2226925168129bf0370e20a5a04` |
| `sdk/conformance/vectors/mixed-input.vectors.json` | exact match | vector sha256 match | `9e2441ddefc22a2f8c7be230436620908b735b128b9445b7a5a916e4d86a2e19` | `74bf25478d57a98c5ee102c362c4870fc8d16456` |
| `toolchains.json` | exact match | `nodeMajor=24` (`node-24`) match | `f4a37d32d50340db6caf8a1f914b1cceb344d410d6c7a5a6299552bd9764e3b5` | `a8c06bcf91eb385875100a5fecf6a6c46664e4c0` |
| `sdk/sdk-pin.json` | exact match | OpenAPI/source/FSM pin match | `c82b38e2c3f783272de60eba8401eefd8687bffd57394deaf3639a5ba7511a6a` | `b90feb09ec26691f678c25f761d90eb1fd93465d` |

Additionally, `git diff --stat 33e20f3 42f219e -- 'integration_gate/*.py' ':!integration_gate/test_offline_limits.py' 'reference/*/*fsm*.py' 'reference/*/mock_*.py'`
was empty; the files differing between `33e20f3` and `42f219e` on the scoped
gate/SDK/reference trees were only `docs/contracts/openapi/README.md`,
`integration_gate/test_offline_limits.py`, `sdk/generate/generate_manifest.mjs`,
and merged `main` test/fixture files under `reference/booking_resale_admission/`
and `reference/credit_advance_f04/`.

### Round 4 fixes (uncommitted on top of `34edf38`)

1. **Gate OpenAPI HTTP 200 description and manifest regeneration (finding 1).**
   Updated `integration_gate/openapi_doc.py` (`responses['200']['description']`,
   `validate()`, and `self_test()`) so HTTP 200 covers both core/FSM command
   receipts/results and the point-query read envelope
   (`read_schema_version`, `query`, `query_digest`, `fixture_mode`,
   `accepted_through`, `result`, current view, ignoring envelope `operationId`
   and `actor`, no receipt sequencing or command replay). Regenerated
   `docs/contracts/openapi/kix-protocol.integration-gate.openapi.json` via
   `python3 -m integration_gate.openapi_doc --write` (new SHA-256
   `773abae8a27666e9c16467826a9bc4de3e42f8c9256ae4edc908dcfa774ffaa5`, new Git
   blob `69b2b027b605c71438ee26d5d6c483de600fc959`), updated
   `EXPECTED_GATE_OPENAPI_SHA256` in `integration_gate/test_offline_limits.py`
   to the same digest, and regenerated the `bootstrap-3` manifest via
   `npm --prefix sdk run generate` (working interim manifest SHA-256
   `f1e9a32fecffe48bbaf12bb260f337aad9e8817d77c14dbd03bda3556d8fb5de`, matching
   sidecar `.sha256`; `bootstrap-3.profile.json`, `catalogue.ts`, `sdk-pin.json`,
   `bootstrap-1`, `bootstrap-2`, and `commerce-fixture-8ba7f6c-1` bytes
   unchanged). `SOURCE_COMMIT` and `SOURCE_TREE` in
   `sdk/generate/generate_manifest.mjs` keep the prior committed values with a
   supervisor `TODO`; the supervisor will update them to the commit containing
   these corrected producer bytes, re-run `npm --prefix sdk run generate`, and
   fill the next delivery head, final manifest digest, and exact-head CI run IDs
   after commit.
2. **Malformed Unicode rejection at the HTTP request boundary (finding 2).**
   Added `_reject_malformed_unicode` in `integration_gate/server.py` right after
   `json.loads` in `_local_call` so escaped unpaired Unicode surrogates (in any
   string key or value) fail closed with HTTP 400 `INVALID_JSON` before
   dispatch. Added regression coverage in
   `integration_gate/test_http_gate.py::ReadQueryLoopbackTests.test_get_presentation_rejects_lone_unicode_surrogate`
   (existing right + raw HTTP JSON `get_presentation` with `\uD800`, `\uDC00`,
   `\uDC00\uD800`, surrogate object key, and surrogate `operationId` -> 400
   `INVALID_JSON`, not 500 `INTERNAL_ERROR`; valid surrogate pair `\uD83D\uDE00`
   still succeeds with HTTP 200 and `matches_current_right: false`).
3. **Historical labeling of the 84-action producer tuple doc (finding 4).**
   Updated `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md` to label the
   84-action `bootstrap-2` tuple as a historical archived snapshot distinct from
   the live 94-action `bootstrap-3` catalogue, keeping the record non-normative
   and leaving `PRODUCER_QUALIFICATION_TUPLE_V1.json` untouched.

### Round 4 local checks actually run (Python 3.13.5, Node v24.22.1)

| Local check | Result |
|---|---|
| `python3 -m integration_gate.openapi_doc --write` | Wrote `docs/contracts/openapi/kix-protocol.integration-gate.openapi.json`; ok (`commands=94 productionEndpoint=false publicHost=false`). |
| `npm --prefix sdk run generate` | Regenerated `manifest.bootstrap-3.json` and `.sha256` (`f1e9a32f...`); historical `bootstrap-1`, `bootstrap-2`, `commerce-fixture-8ba7f6c-1` untouched. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Exit 0 (`commands=94 core=40 fsm=44 read=10`); `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Exit 0 (`commands=94 productionEndpoint=false publicHost=false`); `self-test: pass` (including new receipt-only 200 negative control). |
| `python3 scripts/check_sdk_client.py` and `--self-test` | Exit 0 (`commands=94 node=24.22.1`); `self-test: pass`. |
| `npm --prefix sdk run conformance` | Exit 0; 32 tests passed, 0 failed. |
| `npm --prefix sdk run verify-compat` | Exit 0 (`ok: true`, `profile_kind: BOOTSTRAP`, `profile_revision: bootstrap-3`, `manifest_sha256: f1e9a32fecffe48bbaf12bb260f337aad9e8817d77c14dbd03bda3556d8fb5de`). |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults integration_gate.test_offline_limits` | Exit 0; 163 tests passed (includes new lone-surrogate regression test and merged PR #535 `test_distribution_order`). |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for all 8 protocol suites | All passed: `settlement_f01_f03` 225, `booking_resale_admission` 1,106, `credit_advance_f04` 342, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28, `economics` 99. |
| Stdlib offline document, evidence-map, wiring, and discovery checkers (`check_status_register.py`, `check_producer_qualification_tuple.py`, `check_consumer_binding_index.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_docs_index.py`, `check_integration_gate_contract_evidence_map.py`, `check_sdk_compat_manifest_evidence_map.py`, `check_evidence_map_rollup.py`, `check_ci_checker_wiring.py`, `check_ci_test_discovery.py`), each plain and `--self-test` | All passed. |
| Locked kernel & frozen contract blobs (`git hash-object`) | `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`, `reference/v0.3-rc1/protocol_contract.json` = `619ae21c82ca3df5661bd3831613f15fa65225ff` (all match). |
| Delivery head, final `bootstrap-3` manifest digest, and exact-head CI for round 4 | Pending supervisor commit, `SOURCE_COMMIT`/`SOURCE_TREE` update + manifest regeneration, and GitHub Actions run on the resulting final head. |

Round 4 worktree paths

- `docs/contracts/openapi/kix-protocol.integration-gate.openapi.json`
- `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md`
- `integration_gate/openapi_doc.py`
- `integration_gate/server.py`
- `integration_gate/test_http_gate.py`
- `integration_gate/test_offline_limits.py`
- `sdk/compat/manifests/manifest.bootstrap-3.json`
- `sdk/compat/manifests/manifest.bootstrap-3.json.sha256`
- `sdk/generate/generate_manifest.mjs`
- `validation/2026-10-09-read-model-reference/README.md`

## PR #178 fix round 3

The node brief in the session input governs this round. The approved scope is
the ten point queries. The three list queries remain deferred under the owner
decision recorded below.

| Evidence | Round 3 result |
|---|---|
| Cached `origin/main` | `7b84c6912f4db44aeb94e62f4f52575e076c035a`. The branch and cached main diverge by three commits each from `dcbfef2826908985fc223ed0e2e07653105e9aa3`. The offline supervisor instruction precluded fetching. |
| Reviewed head and committed producer source | `33e20f30bba3587d52c49e323de236467746e298`, tree `09d4d0f7a5ccd1c20324df7170ad64f8ca29053d` |
| Round 3 delivery head | Pending supervisor commit |
| Reviewed manifest SHA-256 | `94b63b8b938769e08c2469f1a67ed8ac82cbb3408c8890473d879a0853b613c8`, from `git show HEAD:sdk/compat/manifests/manifest.bootstrap-3.json` |
| Regenerated manifest SHA-256 | `c2cde918f061678bd45ddcbfc647633f536524cdc9738a91f1eac0356e442a92`. The sidecar contains this digest. |
| Profile and SDK output | The regenerated files matched the reviewed bytes. Profile SHA-256 `7adf7ccea9af9659a864140cee110880420fb5a26c306bc3597a3eed3c20326d`. SDK catalogue SHA-256 `65cef827fa82b137e46b66f4302f2673f512ec26484910cf5de9d9f65f387b9a`. |
| Source binding | `git rev-parse <source>^{tree}` matched the manifest. `git show <source>:<path>` matched the working bytes for both OpenAPIs, both source contracts, the client generator, generated catalogue, both vectors, `toolchains.json`, and `sdk/sdk-pin.json`. SHA-256 and Git blob matched every corresponding manifest field. A scoped `git diff --exit-code <source>` also matched the gate, reference and SDK implementation paths. |
| KTX kernel verification | Run ID, status and conclusion unavailable for the reviewed head. Delivery-head evidence pending. |
| KIX protocol verification | Run ID, status and conclusion unavailable for the reviewed head. Delivery-head evidence pending. |

The supervisor's local state records an aggregate `PASS` at the reviewed head.
The exact workflow records belong in the PR evidence for their respective
heads. The manifest binds producer inputs, and the supervisor binds the
delivery head outside the manifest. Qualification and User approval require
their own evidence.

A merge preview against cached main reproduced three failures in the new
`CommerceGateDispatchTests`. That class read the current FSM catalogue while
checking the historical Commerce tuple. Using
`read_bootstrap_2_input(path, root=ROOT)` for the historical table's non-vector
paths passed all 16 offline-gate tests and all nine direct Commerce tuple
tests in the preview. The preview retained the original SHA-256 and blob
assertions, and the dispatch ran against the live in-memory catalogue. The
supervisor owns integration of the newer base and the test adjustment in
`CommerceGateDispatchTests._verified_evidence`.

| Local check | Result |
|---|---|
| `npm --prefix sdk run generate`, `verify-compat`, and `conformance` | Generated successfully, verified the new digest, 30 conformance tests passed. |
| `python3.12 scripts/check_sdk_client.py`, `check_openapi_contract.py`, `check_integration_gate_openapi.py`, each with and without `--self-test` | Passed. Both OpenAPIs had 94 actions, including ten point queries. |
| Protocol workflow's Python check scripts, including source, evidence map, and documentation checks | Passed. The gate evidence map and self-test passed on rerun after restoring the replay anchor text. |
| `python3.12 -m unittest integration_gate.test_http_gate readiness.test_faults integration_gate.test_offline_limits` | 156 tests passed on the branch and 159 in the merge preview with the test fix. |
| `python3.12 -m unittest discover -s reference/<suite> -t reference/<suite>` for the eight protocol workflow suites | All passed. Settlement 225, booking/resale/admission 1,098, credit 338, delegation 182, token reward 397, provider facts 86, payment effects 28, and economics 99. |
| Three FSM `test_accepted_through.py` discovery runs | One test per module passed. Existing tests cover the source views, read envelopes, and non-mutation. The Git source byte audit fills the manifest binding gap. |
| Rust workspace format, architecture verifier, and architecture tests | Passed. |
| Offline Rust workspace and package test, Clippy, and dependency tree commands | Cargo exited 101 during dependency resolution because the local registry lacked `duckdb`. |
| Offline two-crate KTX reproduction using the checked-in `kix-kernel` and `kix-types` sources and matching lock entries | 139 kernel tests passed. Kernel Clippy and the normal dependency tree check passed. |
| Locked and frozen inputs | Both required kernel blobs and the frozen contract blob matched before and after. All 108 frozen worktree files matched tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The OpenAPI check found no server or security keys. |

The [OpenAPI companion README](../../docs/contracts/openapi/README.md#비운영-통합-관문)
describes HTTP 200 command and point-query responses. Updating the generated
gate OpenAPI description requires a committed source containing those new
bytes and a new producer manifest.

Round 3 worktree paths

- `docs/contracts/openapi/README.md`
- `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md`
- `sdk/compat/manifests/manifest.bootstrap-3.json`
- `sdk/compat/manifests/manifest.bootstrap-3.json.sha256`
- `sdk/generate/generate_manifest.mjs`
- `validation/2026-10-09-read-model-reference/README.md`

## Original builder record (2026-10-13)

The round 3 table above supplies the current source and artifact identities.

Slice A only: the ten approved point queries. The three list queries are not in the catalogue. The owner decision for this node chose option (a): ship the ten point queries in the existing second pin, and bind the list values for the change that gives the lists their catalogue entry. There is no `DECISION_REQUIRED.md`.

This directory records local evidence from the builder session. It is not exact-head CI, not qualification, and not a merge authorization. No commit, push, PR, issue or comment was made in this session. The directory keeps the name of the earlier stopped build (`2026-10-09-…`); the evidence below is from 2026-10-13.

## Identity

| Item | Value |
|---|---|
| Task | `read-model-reference` (program node, no issue). Task input is the node brief and the owner decision in the session input. No file under `docs/tasks/` was edited |
| Branch | `agent/kix-read-model-reference` |
| Observed `origin/main` (`git fetch origin main`, at start and again at the end) | `ab42cfef43a40c6b86fd3f22b69f00e134cc472e` |
| Worktree HEAD at session start | `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`, which was 40 commits behind `origin/main` |
| Worktree HEAD now | `ab42cfef43a40c6b86fd3f22b69f00e134cc472e`. Moved by `git merge --ff-only origin/main`. See Deviations 1 |
| Base tree of the base commit | `4e10dfda71896d385a4ff37cd8588e1ae13e8fb4` |
| Ahead / behind `origin/main` | 0 ahead, 0 behind. All changes below are uncommitted |
| Implementation head / final task head / merge commit | none. The supervisor commits |
| Python | 3.13.5 (CI pins 3.12; `scripts/bootstrap.sh` was not run) |
| Node | 24.19.0 at `/home/box/.local/opt/node-v24.19.0-linux-x64/bin` |
| rustc | 1.98.1 |

## Locked blobs and forbidden paths

| Path | Required | Observed before work | Observed after the local checks |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |
| `reference/v0.3-rc1/protocol_contract.json` | `619ae21c82ca3df5661bd3831613f15fa65225ff` | match | match |

`git diff --stat origin/main -- reference/v0.3-rc1 runtime .aiops docs/tasks .github docs/contracts/READ_MODEL_QUERIES.md` is empty, and `git status --short` on the same paths is empty. Merge-commit blobs are for the post-merge step.

## What changed

94 commands = 40 core + 44 FSM `REPLAYABLE` + 10 point queries.

Queries: `get_show`, `get_booking`, `get_right`, `get_presentation`, `get_listing`, `get_admission`, `get_credential`, `get_settlement`, `get_credit_advance`, `get_credit_claim`. Each calls an existing `view*` method. `QUERY_TABLE` in `integration_gate/fsm_contract.py` maps the name to machine, method and subject field. `drift_problems` requires the method to start with `view` and to be in no `REPLAYABLE` set, so a write method is not reachable from a read.

Wire shape: reads use the existing `POST /x-kix-contract-only/local-call` envelope. The envelope `operationId` and `actor` are ignored for reads (no `OPERATION_ID_CONFLICT`, no Core row, no journal write). Success is HTTP 200 with `read_schema_version`, `query`, `query_digest`, `fixture_mode`, `accepted_through`, `result`. `result` is the unchanged view dict. Handler errors are HTTP 422 with existing codes (`UNKNOWN_SHOW`, `UNKNOWN_RESERVATION`, `UNKNOWN_RIGHT`, `UNKNOWN_LISTING`, `UNKNOWN_SETTLEMENT`, `UNKNOWN_ADVANCE`, `UNKNOWN_CLAIM`, `INVALID_ID`). No new code. With `--readiness-dir`, a read returns 422 `READINESS_FSM_REFUSED` before any machine is touched.

`accepted_through()` is a new read-only accessor on the five machines: `journal_entries`, plus `logical_time_ms` on the three clocked machines.

Pins after the change:

| Artifact | git blob | sha256 |
|---|---|---|
| `docs/contracts/openapi/fsm-command-contract.json` (second pin, `queries` added) | `d3eaf469e4b3c1ffda7d7ecd5b52a84524525356` | `2732173bd7a4fe71cfea4201f53261aaae59b0fe5416f64fe0a4e216ecd73f5f` |
| `docs/contracts/openapi/kix-protocol.contract-only.openapi.json` | `f096739d515a9e13e26f4fa1f89cdff421e03763` | `768aabd8e756d789a20d7b2fb65c20076017eadc8e8dfafe0b9d13ef7ae7f77d` |
| `docs/contracts/openapi/kix-protocol.integration-gate.openapi.json` | `47692773cb4857a69a7cf2286369ae2d6d317e2d` | `670a540a0d66efe3b62bb845a3ce5f7ead4c42dee9e35da88b967e399f108f06` |
| `sdk/generated/catalogue.ts` | not recorded | `65cef827fa82b137e46b66f4302f2673f512ec26484910cf5de9d9f65f387b9a` |
| `sdk/compat/profiles/bootstrap-3.profile.json` | not recorded | `7adf7ccea9af9659a864140cee110880420fb5a26c306bc3597a3eed3c20326d` |
| `sdk/compat/manifests/manifest.bootstrap-3.json` | not recorded | `8fcbdf66f5c13c1e4f46101003d1a256efa23c530f1e5c3ede8964154caf9d11` |

`machines` and `commands` in `fsm-command-contract.json` compare equal to `origin/main`; only `queries` was added. The previous second-pin values (blob `3771a873…`, sha256 `342e97cb…`) are historical. `protocol_contract.json` sha256 `ed827de1…` and blob `619ae21c…` are unchanged.

Compatibility revision `bootstrap-3` is a new profile and manifest. It binds `source_commit` `ab42cfef43a40c6b86fd3f22b69f00e134cc472e` and `source_tree` `4e10dfda71896d385a4ff37cd8588e1ae13e8fb4`, which are the base, not a delivery head. The two OpenAPI blobs and sha256 above, the generator sha256, the catalogue output sha256 and both vector files are bound. Kind `BOOTSTRAP`, grants catalogue-schema binding only. The `bootstrap-1` and `bootstrap-2` files were not regenerated; `scripts/check_sdk_client.py` carries a sha256 guard for both. Artifact identity is not qualification, audit or User approval.

## Existing coverage and new tests (AGENTS §7)

| Requirement | Existing coverage | Classification | New test and the gap it fills |
|---|---|---|---|
| FSM view behaviour of the ten surfaces | the `view*` assertions in `reference/*/test_*_fsm.py`, for example `test_reservation_fsm.py:283,307` for lazy expiry | sufficiently covered. Not duplicated | none |
| Catalogue binding and wire envelope per query | none | not covered | `ReadQueryHostTests.test_each_query_matches_the_live_view_and_does_not_mutate` (one `subTest` per query), `ReadQueryLoopbackTests.test_admission_path_then_all_point_queries` |
| Non-mutation (READ_MODEL_QUERIES §8): `canonical_state`, `export_journal`, clock unchanged for all five machines on valid, unknown and invalid reads | the credit machine's own `_guard` only | partially covered | the same two tests, through `_machine_snapshot` |
| `UNKNOWN_*` and `INVALID_ID` rejections leave state unchanged | none through the gate | not covered | `ReadQueryHostTests._assert_rejections_leave_state` |
| HTTP behaviour: unknown fields and write-shaped bodies rejected, repeated `operationId` allowed, core sequence unaffected | none | not covered | `ReadQueryLoopbackTests.test_admission_path_then_all_point_queries` |
| Readiness refusal without touching the journal | FSM-write refusal only | partially covered | `ReadQueryLoopbackTests.test_readiness_directory_refuses_reads_without_touching_the_journal` |
| CORS rule unchanged for reads | existing browser-origin tests | partially covered | `ReadQueryLoopbackTests.test_read_cors_matches_the_existing_loopback_rule` |
| `accepted_through()` on the five machines | none | not covered | `AcceptedThroughTests` in `reference/{booking_resale_admission,settlement_f01_f03,credit_advance_f04}/test_accepted_through.py` |
| Pin check updated | `check_openapi_contract.py`, `check_integration_gate_openapi.py`, `check_sdk_client.py` and their self-tests | partially covered | negative self-tests added in `check_openapi_contract.py`: a query mapped to a write method, a missing read-only marker, a read-count drift. `openapi_doc.validate` and the drift check carry the same predicates |
| Source-map anchors (main's `check_read_model_source_map.py`) | the map's §6 table | partially covered | anchors re-aimed to the new tree, 11 anchors added (G22–G32) and 5 more (P34–P38). The checker script is unchanged |

## Contract-undefined characterizations (AGENTS §8 B)

- `CreditMachine.view`, `CreditMachine.view_claim`, and `MockCredit._view_claim` include `open_terms`. `READ_MODEL_QUERIES.md` §2.12 and §2.13 do not list that key. Tests assert the live key set. The contract file was not amended.
- Point queries return the unfiltered view for any envelope `actor`. The OpenAPI text says the actor is a fixture actor with no access control. Visibility matrix values are not applied: they are the owner decision's list-time concern and stay `UNDETERMINED` in the contract.
- `ReadObservationV1` fields (`source_cut`, `projection_watermark`, `snapshot_digest`, `observed_receipt_refs`, `producer_manifest_digest`) stay reserved. `fresh: false`, `matches_current_right: false` and source-unavailable decision codes stay inside `result` with HTTP 200.
- Builder-chosen labels, for Astra to confirm: wire keys `result`, `query`, `journal_entries`; `query_digest` as sha256 over canonical JSON of `{action, body}` (the contract leaves the algorithm unnamed); `read_schema_version` `0.1`; reuse of `READINESS_FSM_REFUSED` for reads under `--readiness-dir`.

No explicit contract violation was found.

## Owner-bound list values (received in the session input; not implemented here)

The owner decision (standing approval 2026-10-09 12:34 KST) binds these values for the list change. No code in this change reads them, and `READ_MODEL_QUERIES.md` and `READ_MODEL_SOURCE_MAP.md` do not repeat them. They are recorded here only so the list change has a durable pointer.

| Item | Value |
|---|---|
| `limit` | default 20, cap 100. Values above 100 are clamped, not rejected |
| Cursor | opaque base64url `(sort_key, id)` tuple, 24 hours from issue, forward only. An expired cursor returns the generic invalid-cursor list error |
| `list_shows` | sort `starts_at` ascending, tie-break `show_id` ascending. Keys: `show_id`, `title`, `venue_id`, `starts_at`, `phase`, `seat_count_available` |
| `list_bookings` | sort `created_at` descending, tie-break `booking_id` descending. Keys: `booking_id`, `show_id`, `seat_label`, `phase`, `created_at`, `amount_minor` |
| `list_open_listings` | sort `created_at` descending, tie-break `listing_id` descending. Keys: `listing_id`, `show_id`, `seat_label`, `ask_minor`, `phase`, `created_at`. Open means phase `LISTED` or `OFFER_PENDING`; the predicate is now `BOUND` |
| Retention | shows listed 90 days after `ends_at`; bookings 2 years after terminal phase; open listings dropped on phase exit, history kept 2 years; last 50 phase transitions exposed; a legal-hold flag suspends exclusion and archival |
| Visibility | `list_shows` open to all. `list_bookings`: anonymous no, buyer own bookings, seller own shows' bookings with buyer identity masked, operator all. `list_open_listings`: seller identity masked except for the seller's own, operator all. Masked means a stable per-viewer pseudonym |
| Error names | `LIST_INVALID_CURSOR`, `LIST_CURSOR_EXPIRED`, `LIST_INVALID_SORT`, `LIST_FORBIDDEN` |

Still with the owners: privacy and legal questions (User, `tl-legal-brief`); Toss MID, webhook and account-key facts (`UNDETERMINED`).

## Commands actually run

All were run from the worktree root, in the foreground, after the last source edit.

| Command | Result |
|---|---|
| `git fetch origin main` (start) | `origin/main` = `ab42cfef43a40c6b86fd3f22b69f00e134cc472e`; HEAD `9b12626…` is an ancestor |
| `git merge --ff-only origin/main` (after restoring `docs/README.md` from HEAD and re-applying my two edits) | fast-forward to `ab42cfef…`. No commit created |
| `git fetch origin main` (end) | unchanged: `ab42cfef43a40c6b86fd3f22b69f00e134cc472e` |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. Ran 62 tests. OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for `settlement_f01_f03` | exit 0. 23 tests. OK |
| same, `booking_resale_admission` | exit 0. 48 tests. OK |
| same, `credit_advance_f04` | exit 0. 27 tests. OK |
| same, `ai_delegation` | exit 0. 22 tests. OK |
| same, `token_reward` | exit 0. 61 tests. OK |
| `python3 scripts/check_openapi_contract.py` | exit 0. `commands=94 core=40 fsm=44 read=10`, sha256 `ed827de1…`, gitBlob `619ae21c…` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0. `commands=94 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_sdk_client.py --write`, then `python3 scripts/check_sdk_client.py` (Node 24.19.0 on `PATH`) | exit 0. Regeneration changed only `producer.source_commit` and `source_tree` against the earlier draft. `catalogue.ts` byte-identical. `commands=94` |
| `python3 scripts/check_sdk_client.py --self-test` | exit 0. `self-test: pass` |
| `npm --prefix sdk run conformance` | exit 0. 6 tests, 6 pass, 0 fail |
| `npm --prefix sdk run verify-compat` | exit 0. `ok: true`, `profile_kind` `BOOTSTRAP`, revision `bootstrap-3`, manifest sha256 `8fcbdf66…` |
| `python3 scripts/check_status_register.py` and `--self-test` | exit 0 / pass. `paths=171` |
| `python3 scripts/check_rs_profile_traceability.py` and `--self-test` | exit 0 / pass |
| `python3 scripts/check_read_model_source_map.py` and `--self-test` | exit 0 / pass. `queries=13 anchors=144 catalogues=2 citations=156`. Before the anchor update the same check failed with stale anchors |
| `python3 scripts/check_docs_index.py` and `--self-test` | exit 0 / pass. `scanned=65 indexed=62 allowlisted=3` |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests. OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. Every crate result ok; 128 tests passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` (KTX workflow step) | exit 0. All results ok |
| `git hash-object` on the two kernel files and `protocol_contract.json` | the three required blobs match |
| `git diff --stat origin/main -- reference/v0.3-rc1 runtime .aiops docs/tasks .github docs/contracts/READ_MODEL_QUERIES.md` | empty |
| walk of both OpenAPI JSON files for `servers`, `security`, `securitySchemes` | none found |

Not run, and not treated as passed:

- `scripts/bootstrap.sh` and the `.venv` steps (`verify_runtime.py`, `verify_commerce.py`, `verify_canonical.py`). This machine's Python is 3.13; the script expects 3.12. A grep found no reference to `integration_gate`, the FSM contract, the SDK or the three reference modules in those scripts.
- The storage-probe, disposable-localnet, paid, private and ZK steps in `.github/workflows/protocol.yml`. This node does not change those paths.
- `cargo tree` and the artifact upload of the KTX "Dependency evidence" step, which only write under `.local/`.
- Exact-head GitHub Actions for either workflow (KTX kernel verification, KIX protocol verification). There is no commit and no pull request. The supervisor owns git and GitHub. Run IDs, status and conclusion: not available.
- Post-merge `main` CI and the post-merge locked-blob check.

## Deviations

1. **Branch moved.** The worktree started at `9b12626`, 40 commits behind `origin/main`. `origin/main` now carries `docs/contracts/READ_MODEL_SOURCE_MAP.md` and `scripts/check_read_model_source_map.py`, wired into the protocol workflow. The map's own text says a successor node updates its anchors in the same PR, and the FSM, gate and generator files this node edits are anchored. Run on the stale base, the PR would fail that check or conflict on `docs/README.md`. I ran `git merge --ff-only origin/main`. It created no commit and rewrote no history; the branch had no commits of its own. AGENTS §1 says not to change the task base silently, so this is reported here. The supervisor can undo it by pointing the branch back at `9b12626`; the source-map edits would then have no file to apply to.
2. **Second pin bytes changed.** The queries live in a `queries` key of the existing second pin, as the owner decision says. Its blob and sha256 changed (values above). `sdk/compat/verify_compat.mjs` still expects exactly `fixture_profile` and `extension_profile`, so no third pin file was added. This is a pin-semantics change inside the approved second pin. It is for the ARCHITECTURE gate to see.
3. **Manifest binds the base.** The builder cannot commit, so the manifest binds the base commit and tree as `bootstrap-2` did. It carries no delivery head and no self-referential field. The exact delivery head is bound by protected evidence outside the manifest. If the supervisor rebases or merges `main` again before delivery, `SOURCE_COMMIT` and `SOURCE_TREE` in `sdk/generate/generate_manifest.mjs` and the manifest must be regenerated.
4. **`READ_MODEL_SOURCE_MAP.md` edited.** Anchors, the §2 catalogue-status sentence, §3.2, §4, §5 and §7 were updated, and rows G22–G32 and P34–P38 added. No `UNDETERMINED` value was decided. The checker reads only the `commands` key, so it does not assert that the ten names are in `queries`. That is asserted by `check_openapi_contract.py`, `check_integration_gate_openapi.py`, `check_sdk_client.py` and the gate tests.
5. **`READ_MODEL_QUERIES.md` not edited.** The owner decision says §2.4 and §5 "are amended to match" for the `LIST_*` error names. Those names appear only in the list queries, which this change does not ship, and an edit would shift 36 anchors in the source map and change the blob it cites. The amendment goes with the list change.
6. **Decision records not edited.** `docs/decisions/OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md` line 35 still cites the old second-pin blob `3771a873…` as "the same as `openapi/README.md` line 34". That README line now holds `d3eaf469…`. The record is a pointer record, so it was left for a pointer sync.
7. **Capability register and plan not edited.** `docs/status/CURRENT_CAPABILITY_REGISTER.md` rows EV-GATE, "P catalogue/gate/readiness", the read-projection row and `fin-catalogue-read-model` still say 84 commands and "read-model-reference not merged". They stay true until this merges. A register sync after the merge is the repository's pattern.

## Non-claims and remaining uncertainty

This evidence does not say the kernel is safe, that durability is solved, that the protocol is fully verified, or that `bootstrap-3` qualifies the enlarged catalogue. Consumers stay on HOLD pending a semantic-conformance tuple. The per-query SDK conformance extension belongs to `p-sdk-1`; this node changed only counts, revision and pins in the conformance test. A point query returning 200 is not payment, issuance, admission, chain currency or durability evidence. No production endpoint, no public host, no real funds, no PG/bank/KYC, no Sui testnet or mainnet, no new coin or TIX module, no R2 or own storage engine.

Follow-up candidates: the three list queries with the bound values above; amend `READ_MODEL_QUERIES.md` §2.4 and §5 with the list change; extend `check_read_model_source_map.py` to read `queries` (a CI-script change, so it is not part of this node); register and pointer sync after merge; Astra confirmation of the builder-chosen wire labels.
