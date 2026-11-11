# Open User decisions — October 26 SDK compatibility-manifest check-order stop addendum

## Basis and provenance

Builder-authored, dated 2026-10-26. Node:
`plan-plan-open-decisions-addendum-20261026-sd`; issue: none;
`depends_on: []`; audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. This loop-proposed node is absent from
`.aiops/program.json` and has no corresponding task document under `docs/tasks/`.
Task input is the supervisor-supplied node specification and read-only design plan.
Source: KIX planner run 1792990860 (`/workspace/kix-run/logs/planner_1792990860`,
as supplied; no planner execution is claimed).

Observed cached `origin/main`, base and starting branch HEAD:
`23391ab50e0467bc7b234c55e98614713d531f58` (#305), on
`agent/kix-plan-plan-open-decisions-addendum-20261026-sd`.
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness
remains unverified. No local base delta was observed. All main-branch line
citations below refer to this basis, not to a future delivery commit.

Source stop:
`/workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md`,
SHA-256 `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`.
This external, unmerged record is attributed task input, not a repository
Markdown link or a merged contract. Its diagnostic execution is not reproduced
here. Stop line citations identify those hashed bytes.

The [October 22 ledger](OPEN_USER_DECISIONS_20261022.md),
[October 23 supplement](OPEN_USER_DECISIONS_20261023_ADDENDUM.md),
[October 23 closure](OPEN_USER_DECISIONS_20261023_CLOSURE.md),
[October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md),
[October 26 AI delegation addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md) and
[October 26 BCS1 addendum](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md)
remain preserved. The [validation record](../../validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md)
contains exact gathering commands G0–G12, complete raw output, citation checks,
coverage mapping and local verification.

Filename deviation: `OPEN_USER_DECISIONS_20261026_ADDENDUM.md` already records
the AI delegation stop. The `_SDK_COMPAT` qualifier preserves that record and
the separate BCS1 addendum.

**This document selects no option and changes no node state.**

## New stop — plan-plan-sdk-compat-manifest-clause-evidence

- **Item:** SD1 · SDK manifest verifier check order. SD1 is this addendum's
  own label, not a reused ledger id.
- **Classification:** AGENTS.md §8 class C, explicit contract violation,
  as recorded in source stop line 5. The check-order discrepancy is still
  present in the main-branch source at the basis.
- **Contract clause:** [COMPATIBILITY_MANIFEST_V1.md §4](../contracts/sdk/COMPATIBILITY_MANIFEST_V1.md#4-최소-검증기),
  basis line 64, verbatim (G2, G11):

> 순서는 정규 파싱, 필수 필드와 kind, profile 바이트 해시, 두 OpenAPI 파일의 경로·blob·sha256, 생성기 해시와 `toolchains.json`의 Node 주버전, 생성 산출물 sha256, vector digest, sidecar digest다. 하나라도 어긋나면 0이 아닌 상태로 끝난다. 판정은 JSON 한 줄이다.

- **Verifier sites:** [sdk/compat/verify_compat.mjs](../../sdk/compat/verify_compat.mjs),
  selected by G1/G1b and confirmed against basis bytes by G10b.
  OpenAPI byte comparisons at 168 (`ref.sha256` and `ref.gitBlob`),
  generator comparison at 190 (`manifest.generator.sha256`) and output
  comparison at 201 (`manifest.sdk_output.sha256`) run before the profile
  comparison at 235 (`manifest.profile_sha256`). Their error sites are
  169 (`${label} bytes drift`), 191 (`generator bytes drift`) and
  202 (`sdk_output bytes drift`). Other selected checks before profile
  error site 236 are 180 (`toolchain drift`), 184 (`running node does not
  match toolchains.json`), 187 (`generator path drift`) and
  198 (`sdk_output path drift`). These seven selected error sites precede
  the profile site; G1 also returns vector error site 352, which follows it.
- **Unresolved interpretation:** `extension_profile` is compared at 221
  (`extension.sha256` and `extension.gitBlob`), with its byte error at 223,
  before the profile hash. Whether it is one of §4's “두 OpenAPI 파일” is
  UNDETERMINED — User. This addendum does not classify that additional check
  as a separate violation or supply contract semantics.
- **Observed vs required:** source stop line 5 says, verbatim:
  “Fail-closed error collection does not remove the ordering requirement.”
  Its line 7 names the diagnostic and expected error ordering. That is
  attributed evidence, not a new run or a conformance PASS here.
- **Decision needed (source line 5, verbatim opening clause):**

> the User must choose how to resolve the explicit contract §4 check-order violation.

- **Decision owner (source line 15, verbatim):**

> Who decides: the User.

- **Option 1:** See source stop (SHA-256
  `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`),
  “Options”, item 1, by reference only.
- **Option 2:** See source stop (SHA-256
  `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`),
  “Options”, item 2, by reference only.
- **Option 3:** See source stop (SHA-256
  `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`),
  “Options”, item 3, by reference only.
- **Source recommendation:** option 1 (stop line 15); this addendum does not
  endorse it.
- **Branch-only artifacts, not on main; excluded from the main inventory:**
  `docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md`,
  `scripts/check_sdk_compat_manifest_evidence_map.py`,
  `validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/README.md`,
  `validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py`
  and `DECISION_REQUIRED.md`. Paths are relative to the external source
  worktree. Its `.github/workflows/protocol.yml:259–260` checker invocations
  and `docs/README.md:342` map/record entry are also branch-only content;
  the workflow and index files themselves exist on main. G10 records
  expected missing-path exits at the basis; G10b distinguishes absent
  invocations/entry from existing main files. No branch-only artifact is
  represented as a main-branch Markdown link.

## Per-option artifact inventory

Mechanical selection; membership does not mean a required edit. All repository
artifacts in the main inventory exist at the basis. Each row names the
reproducing commands in the validation record. Counts describe inventory units,
not effort or permission. These are conditional candidates for owner review,
not a complete implementation specification.

| Set | Main-branch artifact and basis sites | Command |
|---|---|---|
| I-V · verifier | [sdk/compat/verify_compat.mjs](../../sdk/compat/verify_compat.mjs): comparisons 168, 190, 201, 221, 235 and selected error sites 169, 180, 184, 187, 191, 198, 202, 223, 236, 352 as described above | G1, G1b, G10b |
| I-P · manifest 1 and sidecar | [manifest.bootstrap-1.json](../../sdk/compat/manifests/manifest.bootstrap-1.json), [manifest.bootstrap-1.json.sha256](../../sdk/compat/manifests/manifest.bootstrap-1.json.sha256); `profile_sha256` is `4c92cf6d905f83fb3f5cd52e166dbadf057451ae46441fce1f91baaaa4367d34` | G4, G5a, G5b |
| I-P · profile 1 | [bootstrap-1.profile.json](../../sdk/compat/profiles/bootstrap-1.profile.json); byte hash matches the manifest's `profile_sha256` above | G4, G5a, G5b |
| I-P · manifest 2 and sidecar | [manifest.bootstrap-2.json](../../sdk/compat/manifests/manifest.bootstrap-2.json), [manifest.bootstrap-2.json.sha256](../../sdk/compat/manifests/manifest.bootstrap-2.json.sha256); `profile_sha256` is `c356b923997cefc132e63e73a179d5922dd7cb2124b9e9b399c662cd49803b73` | G4, G5b |
| I-P · profile 2 | [bootstrap-2.profile.json](../../sdk/compat/profiles/bootstrap-2.profile.json); byte hash matches the manifest's `profile_sha256` above | G4, G5b |
| I-P · pins and generation boundary | [scripts/check_sdk_client.py](../../scripts/check_sdk_client.py): `HISTORICAL_BOOTSTRAP_1` at 22–29 and `source_pin_errors` historical-pin guard at 78–82. [sdk/src/manifest.ts](../../sdk/src/manifest.ts): `BOOTSTRAP_REVISION` at 15. [sdk/generate/generate_manifest.mjs](../../sdk/generate/generate_manifest.mjs): `MANIFEST_PATH`/`SIDECAR_PATH` at 27–28, used at 191–192 | G5a, G5b, G5c |
| I-C · contract | [COMPATIBILITY_MANIFEST_V1.md](../contracts/sdk/COMPATIBILITY_MANIFEST_V1.md): §4 verifier command at 62 and check-order sentence at 64 | G2, G3, G11 |
| I-T · SDK tests | [sdk/conformance/conformance.test.mjs](../../sdk/conformance/conformance.test.mjs): `runVerifier` at 127, verifier path at 131; `test(` declarations at 143, 183, 237, 301, 324, 381; mixed-input/committed-manifest body at 324–375, using [mixed-input.vectors.json](../../sdk/conformance/vectors/mixed-input.vectors.json) at 337. This body checks rejection and nonempty errors, not simultaneous-fault precedence | G3, G6, G6b |
| I-T · SDK checker and entry points | [scripts/check_sdk_client.py](../../scripts/check_sdk_client.py): `git_blob_id`, `require_node`, `run_generator`, `regenerate`, `source_pin_errors`, `compare_outputs`, `expect_refusal`, `self_test`, `write_outputs`, `main` at 35, 40, 54, 63, 78, 93, 112, 123, 158, 173. [sdk/package.json](../../sdk/package.json): `conformance`/`verify-compat` at 12–13; [.github/workflows/protocol.yml](../../.github/workflows/protocol.yml): checker plain/self-test and npm entry points at 290–293 | G3, G6, G9 |
| I-R · register | [CURRENT_CAPABILITY_REGISTER.md](CURRENT_CAPABILITY_REGISTER.md): K3 schema·SDK row at 136; names the contract and bootstrap-2 manifest/profile paths; currently partial, semantic conformance consumer HOLD | G7 |
| I-X · index | [docs/README.md](../README.md): existing ledger navigation at 13, contract pointer at 27, AI and BCS1 record entries at 360 and 364 | G8-before, G8-after |

G4 lists seven tracked files under `sdk/compat`: six manifest/profile/sidecar
data artifacts plus the verifier already in I-V. G5a's three SHA-256 values
match the historical bootstrap-1 pins; these are a constraint, not candidates
for regeneration by default. G5b records both manifest profile hashes,
profile/manifest byte hashes and sidecar contents. The verifier reads these
artifacts; whether option 1 needs regenerated manifests is
UNDETERMINED — User. No regeneration is done or authorized here.

G3's non-validation matches identify current entry points; historical validation
mentions are recorded separately as per-file counts, not inventory rows.
There is no claim that this lexical selection finds every semantic dependency.

| Option (source items by reference above) | Main artifacts it could touch |
|---|---|
| 1 | I-V, I-T and I-R (K3 names the contract and manifest/profile paths). I-P regeneration remains UNDETERMINED; read access alone does not establish a regeneration requirement. I-C is preserved under this option's stated intent. I-X could point to a new node's record. The external map/checker would also need consideration as branch-only artifacts, not existing main files. |
| 2 | I-C §4 command/order sites at 62/64, I-R K3, I-X contract pointer at 27 and a new record pointer; I-T if tests/checker encode the revised requirement. This inventory does not establish that existing tests encode ordering. I-V and I-P remain unchanged under this option's stated intent. The external map/checker are branch-only candidates. |
| 3 | No main SDK, contract or test file change under this option's stated intent. Accepting the external diagnostic delivery could add its branch-only map, checker and validation artifacts, plus its checker invocations and index entry. Thus I-X and the existing CI workflow are conditional publication candidates; those branch additions are not on main today. |

## Still open — by reference

These items remain open at the linked records. Owner cells copy their sources
verbatim (G11); option lists and dispositions remain at those sources.

| Item | Original owner (as recorded) | Source |
|---|---|---|
| L1 · `k-stage5-durable-tx` host | User / supervisor (build host) | [October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md#closure-table), basis line 34 |
| L2 · `rs-4-l2` host | User (spend / environment); Astra (workload) | [October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md#closure-table), basis line 35 |
| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` host | Supervisor / repository owner controlling the execution host | [October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md#closure-table), basis line 40 |
| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | User / repository owner | [October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md#closure-table), basis line 42 |
| A5 · AI delegation check order | Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge. | [October 26 AI addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure), basis line 55 |
| BCS1 · checker-scope stop | the User/orchestrator owning this loop-proposed node. | [October 26 BCS1 addendum](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md#new-stop--plan-plan-bcs1-contract-bound-regressions), basis line 224, stop-owner quote |

## Non-claims

- No option is selected. This document selects no option and changes no node
  state, program status, evidence grade, policy value, owner, acceptance
  criterion or protocol command. No node is resumed, completed, retired or retried.
- No SDK, contract, checker, map, test or source is changed; the blocked
  manifest-evidence node and its diagnostic are not rerun. SD1 remains class C
  and blocked with the User. Its merge blocker is not waived by this ledger.
  The AI delegation and BCS1 stops remain at their linked sources and owners.
- Earlier ledgers and evidence are preserved. Both locked kernel blobs and
  `reference/v0.3-rc1/**` stay byte-identical. No change under `sdk/`,
  `docs/contracts/`, `reference/`, `runtime/`, `.aiops/`, `docs/tasks/`,
  `scripts/` or CI. The only outputs are this addendum, its validation record
  and one docs index entry.
- The RS-4 acceptable load level remains UNDETERMINED (User), and open
  contract/readiness rows retain their owners and unresolved values.
- No hosted CI result transfers from another SHA. This is builder evidence,
  not non-author exact-HEAD review, an Astra audit or a merge-ready claim.
  READY for this docs-only handoff does not resolve the underlying stop.
- No real funds, PG/bank/KYC call, public endpoint, Sui testnet/mainnet,
  R2, own replication/consensus/storage engine, coin/TIX module, secrets or
  production runtime is introduced. No production readiness, durability,
  distributed fencing, bank exactly-once, chain finality, legal compliance
  or protocol-completeness claim is made.
