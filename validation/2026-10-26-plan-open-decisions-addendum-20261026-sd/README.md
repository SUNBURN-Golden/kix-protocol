# SDK compatibility-manifest stop addendum — validation record

Node: `plan-plan-open-decisions-addendum-20261026-sd` (2026-10-26).
Task document: supervisor-supplied node specification and read-only design plan;
no issue or node document under `docs/tasks/`. This is not ASTRA program mode.
Audit floor A2; `depends_on: []`; `astra_gate: None`; `user_merge: False`.
Source: supplied KIX planner run 1792990860, not executed by this builder.

Deliverable: [SDK compatibility-manifest stop addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md).
This is documentation of an existing stop and conditional artifact inventory.
No option is selected and no node disposition is changed.

## Basis and delivery boundaries

Observed cached `origin/main`, base, starting HEAD and unchanged Git HEAD:
`23391ab50e0467bc7b234c55e98614713d531f58` (#305).
Branch: `agent/kix-plan-plan-open-decisions-addendum-20261026-sd`.
`git fetch origin main`: NOT_RUN, explicitly prohibited by the supervisor's
no-network rule. Remote freshness remains unverified; local HEAD/base delta: none.
The task input overrides the normal AGENTS.md §1 fetch requirement.
No commit, push, reset, GitHub action, PR, issue or comment is performed.
Implementation/final delivery commit SHA: NOT_CREATED; this is an uncommitted
worktree handoff. Exact final task head is for the supervisor to establish.
Merge SHA and post-merge verification: NOT_APPLICABLE (not merged).
Exact-head KTX and KIX CI run IDs/status/conclusions: NOT_RUN / unavailable;
no hosted CI or merge-ready claim. Historical CI is not transferred.

Source stop (read-only external input):
`/workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md`.
SHA-256: `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`.
G0 records its actual bytes' digest and exact selected lines. The source agrees
with the supplied design excerpts. Its diagnostic is NOT_RUN here; the
reproduction and expected result remain attributed to that source.

The complete changed-path list is:

- `docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md` (new)
- `docs/README.md` (one new bullet linking both outputs)
- `validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md` (new)

These output files/entry are not claimed to exist at the basis. All pre-existing
repository paths cited by the addendum are checked at the basis in G10.
External branch-only paths are checked for absence at that SHA. Existing main
workflow/index files are distinguished from their absent branch-only contents
by G10b. G1/G1b source results are independently repeated against basis bytes
in G10b. G11 pins the contract quotation and owner-source lines to the basis.

## Existing coverage mapping (AGENTS.md §7)

| Requirement | Existing coverage before this node | Classification and this node's evidence |
|---|---|---|
| Addendum and both index pointers | `scripts/check_docs_index.py` checks index reachability; its `--self-test` exercises missing links | Sufficient checker coverage; new file/entry were not covered as content before this node. G8-after and local checks cover the additions |
| Status-register consistency | `scripts/check_status_register.py` and `--self-test` check register paths, evidence ids and original-row keys | Sufficient; reused without modifying the register or checker |
| Checker wiring | `scripts/check_ci_checker_wiring.py` and `--self-test` | Sufficient; reused without changing wiring |
| Check-order contract and current implementation | Contract §4 line 64 and verifier comparisons/errors (G1/G1b/G2); external stop attributes a diagnostic | Partially covered: main mixed-input test at 324–375 asserts failure/nonempty errors, not simultaneous-fault precedence. G6b inspects it; no new test or reproduction is authorized here |
| Per-option inventory and exact owners | Prior ledgers record owners and older stops, not SD1's current inventory | Not covered for this new ledger entry; G0–G11 fill the documentary gap with mechanical selection and verbatim owner copies |
| Basis-path/symbol presence and branch-only separation | No prior check specific to this addendum | Not covered for this new entry; G10/G10b/G11 and selected grep outputs provide the evidence |
| Locked blobs and immutable reference | AGENTS.md fixed blob ids; existing repository lock enforcement | Sufficient expected values; G12 before/after and working-file hashes recheck them. Reference/protected-path diff and byte comparisons verify preservation |

No tests, checkers or diagnostic scripts are added. This record fills a ledger
provenance/inventory gap; it does not close the verifier's contract gap.

## Gathering method and interpretation

All commands below actually ran from the node worktree root. G0 and the two
external-worktree greps in G10b are read-only external input reads. Other
unqualified grep/hash/list commands ran on untouched basis files; G8 is labeled
before/after the index change. Commands, stdout, stderr and exit codes are
recorded separately with no filtering or output truncation. Empty output is
shown as an empty fenced block. Transcript collection/rendering helpers were
kept under `/tmp`, not added to the repository.

G3 lists historical validation mentions as per-file counts, not main inventory
rows, and does not assert an exhaustive semantic dependency set.
G4 returns seven tracked paths: six data files plus I-V's verifier; it is not
seven manifest/profile/sidecar data files. G5a records three immutable historical
pins and their matching bytes. G5c/G6b supplement the supplied greps with context
for the pin guard and test-body claims. They do not execute SDK tests.

Exit 1 for the node-definition/branch-only-content greps means no match, as
expected. Exit 128 for each of the five branch-only `git cat-file -e` calls
means the path is absent at the basis, as expected; these are not failing
validation checks. All 46 pre-existing repository path checks in the original
G10 group succeed; G10-extra checks two paths named by the K3 row.

## Raw command transcript

### S0

```sh
git status --short
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git rev-parse HEAD origin/main
```

Exit: `0`.

stdout (raw):

```text
23391ab50e0467bc7b234c55e98614713d531f58
23391ab50e0467bc7b234c55e98614713d531f58
```

stderr: empty.

```sh
git branch --show-current
```

Exit: `0`.

stdout (raw):

```text
agent/kix-plan-plan-open-decisions-addendum-20261026-sd
```

stderr: empty.

```sh
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: `0`.

stdout (raw):

```text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
```

stderr: empty.

```sh
git log -1 --format='%H %s'
```

Exit: `0`.

stdout (raw):

```text
23391ab50e0467bc7b234c55e98614713d531f58 Merge pull request #305 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-contract-clause-ev
```

stderr: empty.

```sh
git grep -nF 'plan-plan-open-decisions-addendum-20261026-sd' 23391ab50e0467bc7b234c55e98614713d531f58 -- .aiops/program.json docs/tasks/
```

Exit: `1`.

stdout: empty.

stderr: empty.

### G0

```sh
sha256sum /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md
```

Exit: `0`.

stdout (raw):

```text
10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af  /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md
```

stderr: empty.

```sh
grep -n 'Who decides\|What is needed\|^[123]\. ' /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md
```

Exit: `0`.

stdout (raw):

```text
5:What is needed: the User must choose how to resolve the explicit contract §4 check-order violation. `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md` requires profile byte hash before OpenAPI, generator/toolchain and SDK output checks. `sdk/compat/verify_compat.mjs` performs those checks before the profile hash. This is AGENTS §8 class C. Fail-closed error collection does not remove the ordering requirement.
11:1. Open a new task, branch and session to move the profile-hash check ahead of OpenAPI/generator/output checks and add a regression. That task must also reclassify C4-CHECK-ORDER in the map and remove/replace the checker's live class-C anchor guard, which intentionally fails after an order fix.
12:2. Through an explicitly authorized contract-change workflow, amend §4 to specify collection of all errors with no normative order, then update the map/checker and evidence accordingly.
13:3. Accept this delivery solely as diagnostic evidence; retain the unresolved violation and merge blocker. This is not contract conformance acceptance.
15:Recommendation: option 1, preserving the existing contract. Who decides: the User. The builder has implemented only the authorized map, checker, CI invocations and diagnostic evidence. No SDK/contract fix, merge approval, policy choice, runtime activation or GitHub action was performed.
```

stderr: empty.

### G1

```sh
grep -nE 'errors\.push\(.*(bytes drift|toolchain drift|running node|generator path drift|sdk_output path drift)' sdk/compat/verify_compat.mjs
```

Exit: `0`.

stdout (raw):

```text
169:      errors.push(`${label} bytes drift`);
180:      errors.push("toolchain drift");
184:      errors.push("running node does not match toolchains.json");
187:      errors.push("generator path drift");
191:      errors.push("generator bytes drift");
198:    errors.push("sdk_output path drift");
202:      errors.push("sdk_output bytes drift");
223:          errors.push("extension_profile bytes drift");
236:    errors.push("profile bytes drift");
352:        errors.push(`vector bytes drift: ${vector.name}`);
```

stderr: empty.

### G1b

```sh
grep -nE '!== (ref\.sha256|manifest\.generator\.sha256|manifest\.sdk_output\.sha256|extension\.sha256|manifest\.profile_sha256)' sdk/compat/verify_compat.mjs
```

Exit: `0`.

stdout (raw):

```text
168:    if (sha256Hex(bytes) !== ref.sha256 || gitBlobId(bytes) !== ref.gitBlob) {
190:    if (generatorBytes && sha256Hex(generatorBytes) !== manifest.generator.sha256) {
201:    if (outputBytes && sha256Hex(outputBytes) !== manifest.sdk_output.sha256) {
221:          (sha256Hex(extensionBytes) !== extension.sha256 || gitBlobId(extensionBytes) !== extension.gitBlob)
235:  if (profileBytes && sha256Hex(profileBytes) !== manifest.profile_sha256) {
```

stderr: empty.

### G2

```sh
grep -n '^순서는 정규 파싱' docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md
```

Exit: `0`.

stdout (raw):

```text
64:순서는 정규 파싱, 필수 필드와 kind, profile 바이트 해시, 두 OpenAPI 파일의 경로·blob·sha256, 생성기 해시와 `toolchains.json`의 Node 주버전, 생성 산출물 sha256, vector digest, sidecar digest다. 하나라도 어긋나면 0이 아닌 상태로 끝난다. 판정은 JSON 한 줄이다.
```

stderr: empty.

### G3

```sh
git grep -nE 'verify_compat|verify-compat' -- . ':!validation/'
```

Exit: `0`.

stdout (raw):

```text
.github/workflows/protocol.yml:293:          npm --prefix sdk run verify-compat
docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md:62:`sdk/compat/verify_compat.mjs --manifest <path> [--expect-kind K] [--expect-revision R]`
sdk/README.md:46:npm --prefix sdk run verify-compat
sdk/conformance/conformance.test.mjs:131:      resolve(ROOT, "sdk/compat/verify_compat.mjs"),
sdk/package.json:13:    "verify-compat": "node compat/verify_compat.mjs --manifest compat/manifests/manifest.bootstrap-2.json --expect-kind BOOTSTRAP --expect-revision bootstrap-2"
```

stderr: empty.

```sh
git grep -c -E 'verify_compat|verify-compat' -- validation/
```

Exit: `0`.

stdout (raw):

```text
validation/2026-10-08-ai-delegation-contract-mock/README.md:1
validation/2026-10-09-audit2-gate-browser-access-test-determinism/README.md:1
validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md:1
validation/2026-10-09-audit3-tl-docs-plan-index-sync/README.md:1
validation/2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p/README.md:1
validation/2026-10-09-audit4-tl-plan-index-register-sync/README.md:1
validation/2026-10-09-k-a-integration-decision/README.md:1
validation/2026-10-09-k-a-reestimate/README.md:1
validation/2026-10-09-openapi-catalogue-promotion/README.md:1
validation/2026-10-09-tl-5-decision/README.md:1
validation/2026-10-12-register-nontl-rows-sync/README.md:1
validation/2026-10-12-rs0-review-pack/README.md:1
validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md:1
validation/2026-10-13-docs-index-coverage-check/README.md:1
validation/2026-10-13-i12-review-pack/README.md:1
validation/2026-10-13-k-stage2-v5-impl/README.md:1
validation/2026-10-14-rs-1-issuercap-probe/README.md:1
validation/2026-10-14-rs-1-public-path/README.md:1
validation/2026-10-14-rs-2-private-path/README.md:1
validation/2026-10-16-ai-delegation-execution-decision/README.md:1
validation/2026-10-16-testnet-key-management-decision/README.md:1
validation/2026-10-20-token-reward-readiness-wrap/README.md:1
validation/2026-10-20-token-reward-rejection-atomicity/README.md:1
```

stderr: empty.

### G4

```sh
git ls-files sdk/compat
```

Exit: `0`.

stdout (raw):

```text
sdk/compat/manifests/manifest.bootstrap-1.json
sdk/compat/manifests/manifest.bootstrap-1.json.sha256
sdk/compat/manifests/manifest.bootstrap-2.json
sdk/compat/manifests/manifest.bootstrap-2.json.sha256
sdk/compat/profiles/bootstrap-1.profile.json
sdk/compat/profiles/bootstrap-2.profile.json
sdk/compat/verify_compat.mjs
```

stderr: empty.

### G5a

```sh
grep -n -A7 '^HISTORICAL_BOOTSTRAP_1 = {' scripts/check_sdk_client.py
```

Exit: `0`.

stdout (raw):

```text
22:HISTORICAL_BOOTSTRAP_1 = {
23-    ROOT / 'sdk/compat/profiles/bootstrap-1.profile.json':
24-        '4c92cf6d905f83fb3f5cd52e166dbadf057451ae46441fce1f91baaaa4367d34',
25-    ROOT / 'sdk/compat/manifests/manifest.bootstrap-1.json':
26-        '1cce4ee5a9aa64ef40825c0e6dedf920050e594cf20ea0aaf087ecbde46f0cca',
27-    ROOT / 'sdk/compat/manifests/manifest.bootstrap-1.json.sha256':
28-        'fd568b8117a010d1e259323af6f788efe97d497ec8e15406d99d53cddc389d89',
29-}
```

stderr: empty.

```sh
grep -n 'historical bootstrap-1' scripts/check_sdk_client.py
```

Exit: `0`.

stdout (raw):

```text
82:            errors.append('historical bootstrap-1 pin changed: ' + str(path.relative_to(ROOT)))
```

stderr: empty.

```sh
sha256sum sdk/compat/profiles/bootstrap-1.profile.json sdk/compat/manifests/manifest.bootstrap-1.json sdk/compat/manifests/manifest.bootstrap-1.json.sha256
```

Exit: `0`.

stdout (raw):

```text
4c92cf6d905f83fb3f5cd52e166dbadf057451ae46441fce1f91baaaa4367d34  sdk/compat/profiles/bootstrap-1.profile.json
1cce4ee5a9aa64ef40825c0e6dedf920050e594cf20ea0aaf087ecbde46f0cca  sdk/compat/manifests/manifest.bootstrap-1.json
fd568b8117a010d1e259323af6f788efe97d497ec8e15406d99d53cddc389d89  sdk/compat/manifests/manifest.bootstrap-1.json.sha256
```

stderr: empty.

### G5b

```sh
grep -o '"profile_sha256":"[0-9a-f]\{64\}"' sdk/compat/manifests/manifest.bootstrap-1.json sdk/compat/manifests/manifest.bootstrap-2.json
```

Exit: `0`.

stdout (raw):

```text
sdk/compat/manifests/manifest.bootstrap-1.json:"profile_sha256":"4c92cf6d905f83fb3f5cd52e166dbadf057451ae46441fce1f91baaaa4367d34"
sdk/compat/manifests/manifest.bootstrap-2.json:"profile_sha256":"c356b923997cefc132e63e73a179d5922dd7cb2124b9e9b399c662cd49803b73"
```

stderr: empty.

```sh
sha256sum sdk/compat/profiles/*.json sdk/compat/manifests/*.json
```

Exit: `0`.

stdout (raw):

```text
4c92cf6d905f83fb3f5cd52e166dbadf057451ae46441fce1f91baaaa4367d34  sdk/compat/profiles/bootstrap-1.profile.json
c356b923997cefc132e63e73a179d5922dd7cb2124b9e9b399c662cd49803b73  sdk/compat/profiles/bootstrap-2.profile.json
1cce4ee5a9aa64ef40825c0e6dedf920050e594cf20ea0aaf087ecbde46f0cca  sdk/compat/manifests/manifest.bootstrap-1.json
eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0  sdk/compat/manifests/manifest.bootstrap-2.json
```

stderr: empty.

```sh
cat sdk/compat/manifests/*.sha256
```

Exit: `0`.

stdout (raw):

```text
1cce4ee5a9aa64ef40825c0e6dedf920050e594cf20ea0aaf087ecbde46f0cca
eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0
```

stderr: empty.

```sh
grep -n 'BOOTSTRAP_REVISION' sdk/src/manifest.ts
```

Exit: `0`.

stdout (raw):

```text
15:export const BOOTSTRAP_REVISION = "bootstrap-1";
```

stderr: empty.

```sh
grep -n 'MANIFEST_PATH\|SIDECAR_PATH' sdk/generate/generate_manifest.mjs
```

Exit: `0`.

stdout (raw):

```text
27:const MANIFEST_PATH = "sdk/compat/manifests/manifest.bootstrap-2.json";
28:const SIDECAR_PATH = "sdk/compat/manifests/manifest.bootstrap-2.json.sha256";
191:  const manifestOut = resolve(outRoot, MANIFEST_PATH);
192:  const sidecarOut = resolve(outRoot, SIDECAR_PATH);
```

stderr: empty.

### G6

```sh
grep -nE '^test\(|runVerifier\(|mixed-input' sdk/conformance/conformance.test.mjs
```

Exit: `0`.

stdout (raw):

```text
127:function runVerifier(manifestPath) {
143:test("catalogue pin matches the contract-only OpenAPI and the source contract", () => {
183:test("every catalogue command accepts a minimal body and rejects schema violations", () => {
237:test("envelope, identifier, and transport rules stay local to one call", async () => {
301:test("canonical encoding vectors", () => {
324:test("mixed-input vectors and the committed manifest", () => {
326:  const happy = runVerifier(manifestPath);
337:  const mixed = parseStrict(read(resolve(ROOT, "sdk/conformance/vectors/mixed-input.vectors.json")));
338:  assert.equal(mixed.profile, "kix-compat-mixed-input/1");
366:      const result = runVerifier(target);
381:test("client surface does not carry a URL, credential, or repeat-call API", () => {
```

stderr: empty.

```sh
grep -nE '"(conformance|verify-compat)":' sdk/package.json
```

Exit: `0`.

stdout (raw):

```text
12:    "conformance": "node --test conformance/conformance.test.mjs",
13:    "verify-compat": "node compat/verify_compat.mjs --manifest compat/manifests/manifest.bootstrap-2.json --expect-kind BOOTSTRAP --expect-revision bootstrap-2"
```

stderr: empty.

```sh
grep -nE '^def |^HISTORICAL_BOOTSTRAP_1' scripts/check_sdk_client.py
```

Exit: `0`.

stdout (raw):

```text
22:HISTORICAL_BOOTSTRAP_1 = {
35:def git_blob_id(data):
40:def require_node():
54:def run_generator(openapi, source, catalogue, pin):
63:def regenerate(directory):
78:def source_pin_errors():
93:def compare_outputs(directory):
112:def expect_refusal(document, label):
123:def self_test():
158:def write_outputs():
173:def main(argv):
```

stderr: empty.

### G7

```sh
grep -n '^| K3 ' docs/status/CURRENT_CAPABILITY_REGISTER.md
```

Exit: `0`.

stdout (raw):

```text
136:| K3 schema·SDK | EV-BCS, EV-GATE; `sdk/README.md`, `sdk/sdk-pin.json`, `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md`, `sdk/compat/manifests/manifest.bootstrap-2.json`, `sdk/compat/profiles/bootstrap-2.profile.json` | partial. bootstrap-2 exists; semantic conformance consumer HOLD. p-sdk-1·supported schema별 독립 tuple conformance; stable 1.0/publish/rename 별도 결정 |
```

stderr: empty.

### G8-before

```sh
grep -nE 'OPEN_USER_DECISIONS_20261026|COMPATIBILITY_MANIFEST_V1' docs/README.md docs/DEVELOPMENT_PLAN.md
```

Exit: `0`.

stdout (raw):

```text
docs/README.md:13:4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md), [담당자 질문서](status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md)(위치만. 회신·정책 결정이 아니다), [세 묶음 결정 시트](status/ASTRA_DECISION_SHEETS_KO.md)(위치만. 결정·채택·회신이 아니다), [두 번째 묶음 결정 시트](status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md)(위치만. 결정·채택·회신이 아니다), [열린 사용자 결정 원장(2026-10-22)](status/OPEN_USER_DECISIONS_20261022.md)(위치만. 결정·채택·회신이 아니다), [10월 23일 소유자 정지 보충 기록](status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md)(네 정지의 출처·질문·인계 근거만. 선택·처분·재개 결정이 아니다), [10월 23일 열린 결정 마감 보충 기록](status/OPEN_USER_DECISIONS_20261023_CLOSURE.md)(#269 기준 병합으로 해소된 네 정지와 남은 다섯 항목. 선택·노드 상태 변경이 아니다), [10월 25일 열린 결정 마감 후속 기록](status/OPEN_USER_DECISIONS_20261025_CLOSURE.md)(#282 기준. #274로 해소된 A3 포함 다섯 해소, 남은 네 항목. 선택·노드 상태 변경이 아니다), [10월 26일 AI 위임 검사 순서 정지 보충 기록](status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md)(출처·소유자·선택지별 영향 목록만. 선택·수정·노드 상태 변경이 아니다), [RS-4 L2 결정 선택지별 영향 목록](status/RS4_L2_DECISION_IMPACT_INVENTORY.md)(선택지별 사실만. 선택·값·노드 상태 변경이 아니다).
docs/README.md:27:비운영 TypeScript 0.x 클라이언트는 [sdk/README.md](../sdk/README.md)에 있고, 계약 전용 OpenAPI에서 다시 생성한다. manifest-v1과 BOOTSTRAP profile은 [contracts/sdk/COMPATIBILITY_MANIFEST_V1.md](contracts/sdk/COMPATIBILITY_MANIFEST_V1.md)가 정한다. 이 산출물은 안정 1.0·공개 배포·운영 적합이 아니다.
docs/README.md:360:- [plan-plan-open-decisions-addendum-20261026-ai](../validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md) — [AI 위임 검사 순서 정지 보충 기록](status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md): 출처·소유자·선택지별 기계 수집 영향 목록만. 선택·수정·노드 상태 변경이 아니다.
docs/README.md:364:- [plan-plan-open-decisions-addendum-bcs1-checke](../validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md) — [BCS1 checker-scope stop addendum](status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md): attributed conflict facts and A/B/C impact inventory; no option selected, checker/map/test/source or node-state change.
```

stderr: empty.

### G9

```sh
grep -nE 'check_sdk_client|npm --prefix sdk' .github/workflows/protocol.yml
```

Exit: `0`.

stdout (raw):

```text
290:          python3 scripts/check_sdk_client.py
291:          python3 scripts/check_sdk_client.py --self-test
292:          npm --prefix sdk run conformance
293:          npm --prefix sdk run verify-compat
```

stderr: empty.

### G10

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:AGENTS.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:README.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/README.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/DEVELOPMENT_PLAN.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/BASELINES.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/decisions/AUTHORITY_MODEL_1.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/decisions/PROGRAM_DECISIONS_20260928.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/CONTROL_PLANE_POINTER.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:.github/control-plane-client.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:.aiops/program.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/tasks
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:.github/workflows/protocol.yml
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:.github/workflows/ktx-kernel.yml
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:scripts/check_docs_index.py
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:scripts/check_status_register.py
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:scripts/check_ci_checker_wiring.py
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:scripts/check_sdk_client.py
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/conformance/conformance.test.mjs
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/conformance/vectors/mixed-input.vectors.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/package.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/src/manifest.ts
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/generate/generate_manifest.mjs
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/generate/generate_client.mjs
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/generated/catalogue.ts
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:toolchains.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/contracts/openapi/kix-protocol.contract-only.openapi.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/contracts/openapi/kix-protocol.integration-gate.openapi.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/contracts/openapi/fsm-command-contract.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/CURRENT_CAPABILITY_REGISTER.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:runtime/crates/kix-kernel/src/lib.rs
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:reference/v0.3-rc1
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261022.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261023_CLOSURE.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/manifests/manifest.bootstrap-1.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/manifests/manifest.bootstrap-1.json.sha256
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/manifests/manifest.bootstrap-2.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/manifests/manifest.bootstrap-2.json.sha256
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/profiles/bootstrap-1.profile.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/profiles/bootstrap-2.profile.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/verify_compat.mjs
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md
```

Exit: `128`.

stdout: empty.

stderr (raw):

```text
fatal: path 'docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md' does not exist in '23391ab50e0467bc7b234c55e98614713d531f58'
```

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:scripts/check_sdk_compat_manifest_evidence_map.py
```

Exit: `128`.

stdout: empty.

stderr (raw):

```text
fatal: path 'scripts/check_sdk_compat_manifest_evidence_map.py' does not exist in '23391ab50e0467bc7b234c55e98614713d531f58'
```

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/README.md
```

Exit: `128`.

stdout: empty.

stderr (raw):

```text
fatal: path 'validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/README.md' does not exist in '23391ab50e0467bc7b234c55e98614713d531f58'
```

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py
```

Exit: `128`.

stdout: empty.

stderr (raw):

```text
fatal: path 'validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py' does not exist in '23391ab50e0467bc7b234c55e98614713d531f58'
```

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:DECISION_REQUIRED.md
```

Exit: `128`.

stdout: empty.

stderr (raw):

```text
fatal: path 'DECISION_REQUIRED.md' does not exist in '23391ab50e0467bc7b234c55e98614713d531f58'
```

### G11

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md | grep -nE '^\| (L1 |L2 |A2 |A4 )'
```

Exit: `0`.

stdout (raw):

```text
34:| L1 · `k-stage5-durable-tx` host | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User / supervisor (build host) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 1. |
35:| L2 · `rs-4-l2` host | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User (spend / environment); Astra (workload) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 2. |
40:| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) | Supervisor / repository owner controlling the execution host | STILL OPEN | — | Owner and options unchanged; see the linked supplement heading. |
42:| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | — | Owner and options unchanged. #276 delivered `plan-plan-register-index-sync-20261024`; its record names no disposition of this node. See the [#276 record](../../validation/2026-10-24-plan-register-index-sync/README.md). |
```

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md | grep -nF 'Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.'
```

Exit: `0`.

stdout (raw):

```text
55:  Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.
```

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:docs/status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md | grep -nF 'the User/orchestrator owning this loop-proposed node.'
```

Exit: `0`.

stdout (raw):

```text
224:> **Who decides:** the User/orchestrator owning this loop-proposed node. The
```

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md | grep -n '^순서는 정규 파싱'
```

Exit: `0`.

stdout (raw):

```text
64:순서는 정규 파싱, 필수 필드와 kind, profile 바이트 해시, 두 OpenAPI 파일의 경로·blob·sha256, 생성기 해시와 `toolchains.json`의 Node 주버전, 생성 산출물 sha256, vector digest, sidecar digest다. 하나라도 어긋나면 0이 아닌 상태로 끝난다. 판정은 JSON 한 줄이다.
```

stderr: empty.

### G12-before

```sh
git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: `0`.

stdout (raw):

```text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
```

stderr: empty.

```sh
git diff --exit-code 23391ab50e0467bc7b234c55e98614713d531f58 HEAD -- reference/v0.3-rc1
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git diff --exit-code 23391ab50e0467bc7b234c55e98614713d531f58 -- reference/v0.3-rc1
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: `0`.

stdout (raw):

```text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
```

stderr: empty.

### G10b

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:.github/workflows/protocol.yml | grep -nF 'check_sdk_compat_manifest_evidence_map.py'
```

Exit: `1`.

stdout: empty.

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:docs/README.md | grep -nE 'SDK_COMPAT_MANIFEST_EVIDENCE_MAP|plan-sdk-compat-manifest-clause-evidence'
```

Exit: `1`.

stdout: empty.

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/verify_compat.mjs | grep -nE 'errors\.push\(.*(bytes drift|toolchain drift|running node|generator path drift|sdk_output path drift)'
```

Exit: `0`.

stdout (raw):

```text
169:      errors.push(`${label} bytes drift`);
180:      errors.push("toolchain drift");
184:      errors.push("running node does not match toolchains.json");
187:      errors.push("generator path drift");
191:      errors.push("generator bytes drift");
198:    errors.push("sdk_output path drift");
202:      errors.push("sdk_output bytes drift");
223:          errors.push("extension_profile bytes drift");
236:    errors.push("profile bytes drift");
352:        errors.push(`vector bytes drift: ${vector.name}`);
```

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:sdk/compat/verify_compat.mjs | grep -nE '!== (ref\.sha256|manifest\.generator\.sha256|manifest\.sdk_output\.sha256|extension\.sha256|manifest\.profile_sha256)'
```

Exit: `0`.

stdout (raw):

```text
168:    if (sha256Hex(bytes) !== ref.sha256 || gitBlobId(bytes) !== ref.gitBlob) {
190:    if (generatorBytes && sha256Hex(generatorBytes) !== manifest.generator.sha256) {
201:    if (outputBytes && sha256Hex(outputBytes) !== manifest.sdk_output.sha256) {
221:          (sha256Hex(extensionBytes) !== extension.sha256 || gitBlobId(extensionBytes) !== extension.gitBlob)
235:  if (profileBytes && sha256Hex(profileBytes) !== manifest.profile_sha256) {
```

stderr: empty.

```sh
grep -nE 'check_sdk_compat_manifest_evidence_map' /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/.github/workflows/protocol.yml
```

Exit: `0`.

stdout (raw):

```text
259:          python3 scripts/check_sdk_compat_manifest_evidence_map.py
260:          python3 scripts/check_sdk_compat_manifest_evidence_map.py --self-test
```

stderr: empty.

```sh
grep -nE 'SDK_COMPAT_MANIFEST_EVIDENCE_MAP|plan-sdk-compat-manifest-clause-evidence' /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/docs/README.md
```

Exit: `0`.

stdout (raw):

```text
342:- [plan-plan-sdk-compat-manifest-clause-evidence](../validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/README.md) — Bootstrap manifest §§1–5 [clause-to-test map](status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md) and stdlib checker; verifier order class C reproduced, blocked pending User decision, no SDK or contract change.
```

stderr: empty.

### G5c

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:scripts/check_sdk_client.py | grep -n -A5 '^def source_pin_errors'
```

Exit: `0`.

stdout (raw):

```text
78:def source_pin_errors():
79-    errors = []
80-    for path, digest in HISTORICAL_BOOTSTRAP_1.items():
81-        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
82-            errors.append('historical bootstrap-1 pin changed: ' + str(path.relative_to(ROOT)))
83-    source = SOURCE_PATH.read_bytes()
```

stderr: empty.

### G6b

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:sdk/conformance/conformance.test.mjs | grep -n -A51 '^test("mixed-input vectors and the committed manifest"'
```

Exit: `0`.

stdout (raw):

```text
324:test("mixed-input vectors and the committed manifest", () => {
325-  const manifestPath = resolve(ROOT, "sdk/compat/manifests/manifest.bootstrap-2.json");
326-  const happy = runVerifier(manifestPath);
327-  assert.equal(happy.status, 0, happy.stderr || happy.stdout);
328-  const verdict = JSON.parse(happy.stdout);
329-  assert.equal(verdict.ok, true);
330-  assert.equal(verdict.profile_kind, "BOOTSTRAP");
331-  assert.equal(verdict.profile_revision, "bootstrap-2");
332-  const sidecar = readFileSync(`${manifestPath}.sha256`, "utf8");
333-  assert.equal(sidecar, `${verdict.manifest_sha256}\n`);
334-  assert.equal(readFileSync(manifestPath, "utf8").includes(verdict.manifest_sha256), false);
335-
336-  const original = parseStrict(readFileSync(manifestPath));
337-  const mixed = parseStrict(read(resolve(ROOT, "sdk/conformance/vectors/mixed-input.vectors.json")));
338-  assert.equal(mixed.profile, "kix-compat-mixed-input/1");
339-  const directory = mkdtempSync(join(tmpdir(), "kix-sdk-"));
340-  try {
341-    for (const item of mixed.cases) {
342-      const target = join(directory, `${item.name}.json`);
343-      if (item.op === "truncate") {
344-        writeFileSync(target, readFileSync(manifestPath).subarray(0, -1));
345-      } else if (item.op === "duplicate-key") {
346-        const text = readFileSync(manifestPath, "utf8");
347-        const open = text.indexOf("{");
348-        if (open !== 0) {
349-          throw new Error("committed manifest does not start with an object");
350-        }
351-        writeFileSync(target, `{"contract":{},${text.slice(1)}`);
352-      } else {
353-        const copy = parseStrict(canonicalStringify(original));
354-        const parts = item.path.split(".");
355-        let cursor = copy;
356-        for (const part of parts.slice(0, -1)) {
357-          cursor = cursor[part];
358-        }
359-        const leaf = parts[parts.length - 1];
360-        const value = item.name === "wrong-revision" ? "bootstrap-9" : item.value;
361-        cursor[leaf] = item.op === "copy" ? getPath(copy, item.from) : value;
362-        const encoded = canonicalStringify(copy);
363-        writeFileSync(target, encoded);
364-        writeFileSync(`${target}.sha256`, `${sha256Hex(encoded)}\n`);
365-      }
366-      const result = runVerifier(target);
367-      assert.notEqual(result.status, 0, item.name);
368-      const body = JSON.parse(result.stdout);
369-      assert.equal(body.ok, false, item.name);
370-      assert.ok(body.errors.length > 0, item.name);
371-    }
372-  } finally {
373-    rmSync(directory, { recursive: true, force: true });
374-  }
375-});
```

stderr: empty.

```sh
git show 23391ab50e0467bc7b234c55e98614713d531f58:sdk/conformance/conformance.test.mjs | grep -n -A13 '^function runVerifier'
```

Exit: `0`.

stdout (raw):

```text
127:function runVerifier(manifestPath) {
128-  return spawnSync(
129-    process.execPath,
130-    [
131-      resolve(ROOT, "sdk/compat/verify_compat.mjs"),
132-      "--manifest",
133-      manifestPath,
134-      "--expect-kind",
135-      "BOOTSTRAP",
136-      "--expect-revision",
137-      "bootstrap-2",
138-    ],
139-    { cwd: ROOT, encoding: "utf8" },
140-  );
```

stderr: empty.

### G10-extra

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/README.md
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git cat-file -e 23391ab50e0467bc7b234c55e98614713d531f58:sdk/sdk-pin.json
```

Exit: `0`.

stdout: empty.

stderr: empty.

### G8-after

```sh
grep -nE 'OPEN_USER_DECISIONS_20261026|COMPATIBILITY_MANIFEST_V1' docs/README.md docs/DEVELOPMENT_PLAN.md
```

Exit: `0`.

stdout (raw):

```text
docs/README.md:13:4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md), [담당자 질문서](status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md)(위치만. 회신·정책 결정이 아니다), [세 묶음 결정 시트](status/ASTRA_DECISION_SHEETS_KO.md)(위치만. 결정·채택·회신이 아니다), [두 번째 묶음 결정 시트](status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md)(위치만. 결정·채택·회신이 아니다), [열린 사용자 결정 원장(2026-10-22)](status/OPEN_USER_DECISIONS_20261022.md)(위치만. 결정·채택·회신이 아니다), [10월 23일 소유자 정지 보충 기록](status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md)(네 정지의 출처·질문·인계 근거만. 선택·처분·재개 결정이 아니다), [10월 23일 열린 결정 마감 보충 기록](status/OPEN_USER_DECISIONS_20261023_CLOSURE.md)(#269 기준 병합으로 해소된 네 정지와 남은 다섯 항목. 선택·노드 상태 변경이 아니다), [10월 25일 열린 결정 마감 후속 기록](status/OPEN_USER_DECISIONS_20261025_CLOSURE.md)(#282 기준. #274로 해소된 A3 포함 다섯 해소, 남은 네 항목. 선택·노드 상태 변경이 아니다), [10월 26일 AI 위임 검사 순서 정지 보충 기록](status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md)(출처·소유자·선택지별 영향 목록만. 선택·수정·노드 상태 변경이 아니다), [RS-4 L2 결정 선택지별 영향 목록](status/RS4_L2_DECISION_IMPACT_INVENTORY.md)(선택지별 사실만. 선택·값·노드 상태 변경이 아니다).
docs/README.md:27:비운영 TypeScript 0.x 클라이언트는 [sdk/README.md](../sdk/README.md)에 있고, 계약 전용 OpenAPI에서 다시 생성한다. manifest-v1과 BOOTSTRAP profile은 [contracts/sdk/COMPATIBILITY_MANIFEST_V1.md](contracts/sdk/COMPATIBILITY_MANIFEST_V1.md)가 정한다. 이 산출물은 안정 1.0·공개 배포·운영 적합이 아니다.
docs/README.md:360:- [plan-plan-open-decisions-addendum-20261026-ai](../validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md) — [AI 위임 검사 순서 정지 보충 기록](status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md): 출처·소유자·선택지별 기계 수집 영향 목록만. 선택·수정·노드 상태 변경이 아니다.
docs/README.md:364:- [plan-plan-open-decisions-addendum-bcs1-checke](../validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md) — [BCS1 checker-scope stop addendum](status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md): attributed conflict facts and A/B/C impact inventory; no option selected, checker/map/test/source or node-state change.
docs/README.md:366:- [plan-plan-open-decisions-addendum-20261026-sd](../validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md) — [SDK compatibility-manifest check-order stop addendum](status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md): attributed class C finding, User owner and per-option artifact inventory; no option selected, SDK/contract/checker/test or node-state change.
```

stderr: empty.

## Verification results and limitations

Local acceptance checks and preservation commands follow in the verification
transcript below. Their results apply to this worktree content, not a future
supervisor commit. Narrow checks run before the broader wiring guard and final
scope/preservation checks. The inspected `protocol.yml` stdlib document step
runs the docs-index/status/wiring checks even for docs-only changes; these are
the closest relevant local equivalents for the three touched Markdown paths.
The KTX workflow's docs-only classifier skips its Rust steps for these paths.

SDK conformance, SDK checker execution, `npm --prefix sdk run verify-compat`,
Rust tests/Clippy/formatting, Move and the source diagnostic: NOT_RUN (no code
paths changed; SDK execution is outside this documentary inventory).
The SDK mixed-input and checker source inspections are not test executions.
No full hosted CI pass, independent A2 review or Astra audit is claimed.

## Findings, deviations and remaining uncertainty

- Class C: source stop's SDK §4 order violation remains present at the basis
  and unresolved. SD1 is this addendum's own new label. No fix or waiver is
  attempted; the underlying evidence node remains blocked, not merge-ready.
- Contract-undefined interpretation: whether `extension_profile` is within
  §4's two OpenAPI files is UNDETERMINED — User; no new semantics are inferred.
  Whether option 1 needs regenerated manifests is also UNDETERMINED — User.
- Still-open L1, L2, A2, A4, A5 and BCS1 are carried forward with exact owner
  text from G11, by reference only. No owner answer is supplied.
- Filename deviation: `_SDK_COMPAT` avoids overwriting the October 26 AI
  addendum or BCS1 addendum. No substantive design-plan deviation was needed.
- Fetch deviation: NOT_RUN under the supervisor's explicit no-network rule.
- Verification adaptation: `git diff <basis>..HEAD` is empty because commits
  are prohibited. Working-tree diffs, untracked-file listing and byte-level
  scope checks include the actual uncommitted outputs instead.
- Supplemental gathering commands G5c/G6b/G10-extra and final byte checks
  strengthen citation/preservation evidence; they do not broaden node scope.
- Validation-helper correction: the first `python3 /tmp/kix-sdk-ledger-final-checks.py`
  invocation exited 1 because Python interpreted an embedded NUL in the shell
  command string (`ValueError: embedded null byte`). Its byte-check command
  was NOT_LAUNCHED; the preceding scope/lock/hash commands had exited 0.
  The helper was corrected to preserve literal escapes using a raw string,
  and the complete invocation reran with exit 0. No repository file was
  modified by that failed attempt; successful raw command results follow.
- No root `DECISION_REQUIRED.md` is needed for this authorized ledger node.
  The external stop is recorded, not resolved. READY means the docs-only
  worktree is ready for supervisor review; it is not merge authorization.
- No real funds, real PG/bank/KYC calls, public endpoints, Sui testnet/mainnet,
  R2, own replication/consensus/storage engine, coin/TIX module, secrets or
  production runtime. No policy value, new command, node state, evidence grade,
  contract, SDK, checker, test, CI or immutable historical evidence is changed.
- No claims about production readiness, durability, distributed fencing,
  bank exactly-once, chain finality, legal compliance or protocol completeness.

## Local verification transcript

| Command | Result |
|---|---|
| `python3 scripts/check_docs_index.py` | PASS (exit 0) |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_status_register.py` | PASS (exit 0) |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0) |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) |
| `git rev-parse HEAD:<locked path>` and `git hash-object <locked paths>` | Both required blobs match before and after |
| Byte-level protected-path comparison (`V-bytes` below) | PASS: 482 protected blobs; 108 immutable reference blobs; exactly 3 authorized changed paths |
| `git diff --check` | PASS |

### V-local

```sh
python3 scripts/check_docs_index.py
```

Exit: `0`.

stdout (raw):

```text
docs index ok: scanned=269 indexed=234 allowlisted=35
```

stderr: empty.

```sh
python3 scripts/check_docs_index.py --self-test
```

Exit: `0`.

stdout (raw):

```text
self-test: detected removed index link to docs/adr/0001-ktx-authority-commit-recovery.md (not indexed: docs/adr/0001-ktx-authority-commit-recovery.md)
self-test: detected unindexed scanned file docs/status/SELFTEST_UNINDEXED.md (not indexed: docs/status/SELFTEST_UNINDEXED.md)
self-test: detected unindexed validation record validation/SELFTEST_UNINDEXED/README.md (not indexed: validation/SELFTEST_UNINDEXED/README.md)
self-test: detected dropped allowlist entry docs/contracts/openapi/fsm-command-contract.json (not indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected removed scanned file docs/contracts/openapi/fsm-command-contract.json (allowlist names a file outside the scanned set: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected allowlisted entry also index-linked docs/contracts/openapi/fsm-command-contract.json (allowlisted but indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected broken index link docs/status/SELFTEST_MISSING_TARGET.md (broken index link: docs/status/SELFTEST_MISSING_TARGET.md)
self-test: pass
```

stderr: empty.

```sh
python3 scripts/check_status_register.py
```

Exit: `0`.

stdout (raw):

```text
capability register ok: paths=385 ev_ids=15 original32=32
```

stderr: empty.

```sh
python3 scripts/check_status_register.py --self-test
```

Exit: `0`.

stdout (raw):

```text
self-test: detected missing path (path not found: docs/status/NO_SUCH_FILE_9f3a.md)
self-test: detected undefined EV id (undefined evidence id referenced: EV-XXX)
self-test: detected dropped original id (original id E01 appears 0 times as a row key (want 1))
self-test: detected duplicated original id (original id E01 appears 2 times as a row key (want 1))
self-test: pass
```

stderr: empty.

```sh
python3 scripts/check_ci_checker_wiring.py
```

Exit: `0`.

stdout (raw):

```text
ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=59
```

stderr: empty.

```sh
python3 scripts/check_ci_checker_wiring.py --self-test
```

Exit: `0`.

stdout (raw):

```text
self-test: detected unwired checker
self-test: detected plain-only wiring
self-test: detected unlisted self-test-only checker
self-test: detected missing cited checker
self-test: detected document cites unrun checker
self-test: detected allowlisted script wired plain
self-test: detected allowlisted script missing self-test
self-test: detected missing allowlisted script
self-test: detected workflow invokes missing file
self-test: detected commented-out invocation
self-test: detected no scripts
self-test: detected no invocations
self-test: detected no documents
self-test: pass (13 negative controls)
```

stderr: empty.

### V-preservation

```sh
git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: `0`.

stdout (raw):

```text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
```

stderr: empty.

```sh
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: `0`.

stdout (raw):

```text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
```

stderr: empty.

```sh
git diff --exit-code 23391ab50e0467bc7b234c55e98614713d531f58 HEAD -- reference/v0.3-rc1
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git diff --exit-code 23391ab50e0467bc7b234c55e98614713d531f58 -- sdk/ docs/contracts/ reference/ runtime/ .aiops/ docs/tasks/ .github/ scripts/
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
sha256sum /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md
```

Exit: `0`.

stdout (raw):

```text
10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af  /workspace/kix-run/wt/plan-plan-sdk-compat-manifest-clause-evidence/DECISION_REQUIRED.md
```

stderr: empty.

### V-content

```sh
grep -n 'selects no option' docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md
```

Exit: `0`.

stdout (raw):

```text
42:**This document selects no option and changes no node state.**
165:- No option is selected. This document selects no option and changes no node
```

stderr: empty.

```sh
grep -n SDK_COMPAT_ADDENDUM docs/README.md
```

Exit: `0`.

stdout (raw):

```text
366:- [plan-plan-open-decisions-addendum-20261026-sd](../validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md) — [SDK compatibility-manifest check-order stop addendum](status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md): attributed class C finding, User owner and per-option artifact inventory; no option selected, SDK/contract/checker/test or node-state change.
```

stderr: empty.

### V-scope

```sh
git diff --check
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git diff --name-only 23391ab50e0467bc7b234c55e98614713d531f58..HEAD
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git diff --name-only 23391ab50e0467bc7b234c55e98614713d531f58
```

Exit: `0`.

stdout (raw):

```text
docs/README.md
```

stderr: empty.

```sh
git ls-files --others --exclude-standard
```

Exit: `0`.

stdout (raw):

```text
docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md
validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md
```

stderr: empty.

### V-bytes

```sh
python3 - <<'CHECK'
import hashlib
import os
import subprocess
from pathlib import Path
basis = '23391ab50e0467bc7b234c55e98614713d531f58'
protected = ['sdk', 'docs/contracts', 'reference', 'runtime', '.aiops', 'docs/tasks', '.github', 'scripts']
raw = subprocess.check_output(['git', 'ls-tree', '-r', '-z', basis, '--', *protected])
count = 0
reference_count = 0
for record in raw.split(b'\0'):
    if not record:
        continue
    meta, name = record.split(b'\t', 1)
    mode, kind, expected = meta.split()
    assert kind == b'blob', (name, kind)
    path = Path(os.fsdecode(name))
    data = os.fsencode(os.readlink(path)) if mode == b'120000' else path.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert actual == expected.decode(), str(path)
    count += 1
    reference_count += name.startswith(b'reference/v0.3-rc1/')
tracked_changes = subprocess.check_output(['git', 'diff', '--name-only', basis], text=True).splitlines()
untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], text=True).splitlines()
allowed = {
    'docs/README.md',
    'docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md',
    'validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md',
}
assert set(tracked_changes + untracked) == allowed, (tracked_changes, untracked)
print(f'PASS: {count} protected tracked blobs byte-identical; reference/v0.3-rc1 blobs={reference_count}; changed paths exactly the 3 authorized Markdown outputs')
CHECK
```

Exit: `0`.

stdout (raw):

```text
PASS: 482 protected tracked blobs byte-identical; reference/v0.3-rc1 blobs=108; changed paths exactly the 3 authorized Markdown outputs
```

stderr: empty.

## Final citation and whitespace review

The link/quotation check passes for all 33 addendum links and the exact contract line. For `git diff --no-index --check /dev/null <new file>`, exit 1 with empty output is expected because the file differs from `/dev/null`. Exit 3 in the initial validation-record check combined that content difference with a whitespace error (an extra blank line at EOF). The renderer was corrected to end with one newline, and the checks were rerun below. The initial raw result is preserved here, not presented as a pass.

### V-final-review

```sh
git diff --check
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md
```

Exit: `1`.

stdout: empty.

stderr: empty.

```sh
git diff --no-index --check /dev/null validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md
```

Exit: `3`.

stdout (raw):

```text
validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md:1856: new blank line at EOF.
```

stderr: empty.

```sh
git rev-parse HEAD origin/main
```

Exit: `0`.

stdout (raw):

```text
23391ab50e0467bc7b234c55e98614713d531f58
23391ab50e0467bc7b234c55e98614713d531f58
```

stderr: empty.

```sh
python3 - <<'CHECK'
import re
import subprocess
from pathlib import Path
basis = '23391ab50e0467bc7b234c55e98614713d531f58'
root = Path.cwd()
addendum = root / 'docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md'
validation = 'validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md'
links = re.findall(r'\]\(([^)]+)\)', addendum.read_text())
for target in links:
    relative = (addendum.parent / target.split('#', 1)[0]).resolve().relative_to(root).as_posix()
    if relative == validation:
        assert (root / relative).is_file()
    else:
        subprocess.run(['git', 'cat-file', '-e', basis + ':' + relative], check=True)
contract_line = subprocess.check_output(['git', 'show', basis + ':docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md'], text=True).splitlines()[63]
assert '> ' + contract_line in addendum.read_text().splitlines()
print(f'PASS: all {len(links)} addendum links resolve at the basis (new validation output excepted); contract basis line 64 is quoted verbatim')
CHECK
```

Exit: `0`.

stdout (raw):

```text
PASS: all 33 addendum links resolve at the basis (new validation output excepted); contract basis line 64 is quoted verbatim
```

stderr: empty.

### V-final-corrected

```sh
git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md
```

Exit: `1`.

stdout: empty.

stderr: empty.

```sh
git diff --no-index --check /dev/null validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md
```

Exit: `1`.

stdout: empty.

stderr: empty.

```sh
git diff --check
```

Exit: `0`.

stdout: empty.

stderr: empty.

```sh
git status --short
```

Exit: `0`.

stdout (raw):

```text
 M docs/README.md
?? docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md
?? validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/
```

stderr: empty.
