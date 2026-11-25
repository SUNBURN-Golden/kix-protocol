# FSM extension digest diagnostic order

On both manifest revisions, the copied verifier reported `profile bytes drift`
before `extension_profile bytes drift` in the profile pair, and
`sdk_output bytes drift` before `extension_profile bytes drift` in the SDK output
pair. Both pristine copies verified against their checked-in pins. Each altered
copy returned exactly the two intended diagnostics.

Task `plan-producer-extension-order-evidence` uses the supervisor-supplied node
specification and design from planner run `1795611291` as its task document.
The branch `agent/kix-plan-producer-extension-order-evidence` started at
`405791bb0cdd21d08cc372fc123d382482bde29d`. Cached `origin/main` matched that HEAD
and the planning basis. The supervisor's no-network rule precluded a fetch.

## Reproduce

From the repository root with Node 24:

```bash
node validation/2026-11-25-plan-producer-extension-order-evidence/repro_extension_order.mjs
```

Each invocation uses a fresh temporary root outside the checkout. The reproduction
copies the verifier, its launch dependencies, the toolchain record, the manifest
and its sidecar, the profile and every artifact and vector referenced by the
manifest. It runs the copied verifier with the absolute Node executable from the
copied root, passing `--manifest`, `--expect-kind` and `--expect-revision`. Node
restricts filesystem access to that root. The child has an empty executable
search path and no permission to launch another process.

Each altered case starts with the pristine manifest and sidecar. It replaces
`source_references.extension_profile.sha256` and one of `profile_sha256` or
`sdk_output.sha256` with 64 ASCII zeroes. The fields had different values
before mutation. Restoring those two fields in memory reproduces the pristine
bytes, including the FSM path and Git blob pin. The altered manifest uses
canonical encoding without a final LF. Its sidecar contains the lowercase SHA-256
of those bytes followed by one LF.

The reproduction checks the SHA-256 and Git blob of the verifier in each copy.
All six invocations exited normally with empty stderr and one JSON line ending
in LF. The reproduction compares the entire copied inventory and file bytes
immediately before and after each invocation, then removes the temporary root.
It checks diagnostic membership and multiplicity and preserves the emitted order.

## Transcript

The first line identifies the copied verifier. Each case has a metadata line
followed by the verifier's verbatim stdout. The `\n` in the metadata represents
the final LF in the sidecar.

```jsonl
{"verifier":"sdk/compat/verify_compat.mjs","sha256":"8628518c41b4110f0adf9a5d841240ae06dc6c1fa5d5c4974f00d96a718c5de6","git_blob":"4d744a7e622f2678054b9f709a138252635309c6"}
{"revision":"bootstrap-2","case":"pristine","changed_fields":[],"manifest_sha256":"eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0","sidecar":"eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0\n","exit_status":0}
{"ok":true,"manifest_sha256":"eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0","profile_kind":"BOOTSTRAP","profile_revision":"bootstrap-2"}
{"revision":"bootstrap-2","case":"extension-plus-profile","changed_fields":["source_references.extension_profile.sha256","profile_sha256"],"manifest_sha256":"e1be84b1dc24d05493301f1a4f488d4da2c518e170c9aee33cb23f9e7a0c371f","sidecar":"e1be84b1dc24d05493301f1a4f488d4da2c518e170c9aee33cb23f9e7a0c371f\n","exit_status":1}
{"ok":false,"errors":["profile bytes drift","extension_profile bytes drift"]}
{"revision":"bootstrap-2","case":"extension-plus-sdk-output","changed_fields":["source_references.extension_profile.sha256","sdk_output.sha256"],"manifest_sha256":"a9dc7c0718bf863ceba5f4b763b5c6ff151bb55531bcb326422920c98842d820","sidecar":"a9dc7c0718bf863ceba5f4b763b5c6ff151bb55531bcb326422920c98842d820\n","exit_status":1}
{"ok":false,"errors":["sdk_output bytes drift","extension_profile bytes drift"]}
{"revision":"commerce-fixture-8ba7f6c-1","case":"pristine","changed_fields":[],"manifest_sha256":"76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f","sidecar":"76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f\n","exit_status":0}
{"ok":true,"manifest_sha256":"76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f","profile_kind":"SEMANTIC_CONFORMANCE","profile_revision":"commerce-fixture-8ba7f6c-1"}
{"revision":"commerce-fixture-8ba7f6c-1","case":"extension-plus-profile","changed_fields":["source_references.extension_profile.sha256","profile_sha256"],"manifest_sha256":"22b4ae130a8f36a94bc338e81aa5c2c65df565373d9893a358ed122ae48b41be","sidecar":"22b4ae130a8f36a94bc338e81aa5c2c65df565373d9893a358ed122ae48b41be\n","exit_status":1}
{"ok":false,"errors":["profile bytes drift","extension_profile bytes drift"]}
{"revision":"commerce-fixture-8ba7f6c-1","case":"extension-plus-sdk-output","changed_fields":["source_references.extension_profile.sha256","sdk_output.sha256"],"manifest_sha256":"3a4d2dc84f598aec29dd706bad4b8db495bbbd4b0bfca5aaab78a6ce3db145dc","sidecar":"3a4d2dc84f598aec29dd706bad4b8db495bbbd4b0bfca5aaab78a6ce3db145dc\n","exit_status":1}
{"ok":false,"errors":["sdk_output bytes drift","extension_profile bytes drift"]}
```

## Coverage

| Requirement | Existing coverage and evidence |
| --- | --- |
| Pristine pins and detached inputs | Sufficient. `vendored producer manifests return one verdict without changing files` covers both pins, one-line verdicts and persistent file preservation. The pristine cases provide controls alongside the four paired faults. [SDK conformance tests](../../sdk/conformance/conformance.test.mjs) |
| Paired fault order | Uncovered. `extension-profile-bytes-drift` covers the single extension digest fault, and `manifest verifier reports failures in contract order` exercises the stages listed in §4 without the extension fault. The four altered copies record both pairings on both revisions. [Negative vectors](../../sdk/conformance/vectors/manifest-verifier-negative.vectors.json) · [Order regression](../../sdk/conformance/conformance.test.mjs#L611) |
| Traceability and owner handoff | Partial. The earlier SD1 handoff identifies the verifier and bootstrap pin. This transcript ties the two revisions and their altered copies to the same verifier bytes. [Earlier handoff](../2026-11-19-plan-producer-sd1-evidence-handoff/README.md) · [Producer tuple handoff](../../docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md#sd1-verifier-evidence-and-ledger-status) |
| Qualification boundaries | Sufficient. SDK conformance checks exact Commerce scope and the tuple checker verifies identity and exercises false promotions. [SDK conformance tests](../../sdk/conformance/conformance.test.mjs) · [Tuple checker](../../scripts/check_producer_qualification_tuple.py) |

## Decision boundary

Manifest-v1 §2 identifies `extension_profile` as the FSM contract reference.
Whether it belongs to §4's “two OpenAPI files” remains `UNDETERMINED` with
JunTae. Under AGENTS.md §8 this is a class B characterization of the tested
bytes. The observed order establishes no normative order. No explicit
contract violation surfaced in this run. The tuple retains
`sd1.status = OPEN` and `sd1.owner = User`.
[Manifest contract](../../docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md) · [Producer tuple handoff](../../docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md#sd1-verifier-evidence-and-ledger-status)

Bootstrap-2 grants `catalogue-schema-binding only`. The existing Commerce
grant covers only the listed fixture steps and outcomes across 28 actions.
The other 56 actions, unlisted steps and mismatched tuples stay
`HOLD_SEMANTIC`. The 13 read names stay `NOT_BOUND` and external acceptance
stays `UNVERIFIED`. This offline evidence makes no claims about N/N−1
compatibility, durability, distributed fencing, bank exactly-once, chain
finality, legal compliance or production readiness.
[Commerce fixture qualification table](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json) · [Consumer binding index](../../docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json)

## Local verification

The reproduction ran before SDK conformance and the offline document checks.
The worktree classifiers received the raw tracked diff against HEAD plus raw
additions against `/dev/null` for the two new files. Both workflow classifiers
returned `docs_only=true`. The first local attempt retained the final LF
that Bash command substitution strips, so the classifier treated it as an
extra diff line. The corrected replay passed with the workflow code intact.

| Command | Actual result |
| --- | --- |
| `node --version`, `npm --version`, `python3.12 --version` | Exit 0. Node 24.22.1, npm 11.21.1, Python 3.12.15. |
| `node validation/2026-11-25-plan-producer-extension-order-evidence/repro_extension_order.mjs` | Exit 0. Two pinned pristine successes, four paired refusals, and six unchanged fixture inventories. A second run matched the complete transcript byte for byte. |
| `npm_config_offline=true npm_config_update_notifier=false npm --prefix sdk run conformance` | Exit 0. All 27 tests passed. |
| `npm_config_offline=true npm_config_update_notifier=false npm --prefix sdk run verify-compat` | Exit 0. One successful verdict with the pinned `bootstrap-2` digest. |
| `python3.12 -B scripts/check_sdk_client.py`, plain and `--self-test` | Both exit 0. The catalogue pin check reported 84 commands. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py`, plain and `--self-test` | Both exit 0. Identity check reported 84 commands (40 core, 44 FSM) and 13 reads. Self-test passed its drift, false-promotion and association controls. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py`, plain and `--self-test` | Both exit 0. 51 rows (24 covered, 26 partial, one not covered). Self-test passed 71 negative fixtures and its injected positive control. |
| `python3.12 -B scripts/check_docs_index.py`, plain and `--self-test` | Both exit 0. 466 scanned, 431 indexed and 35 allowlisted. Both new inbound links resolved to this record. |
| [Protocol workflow's stdlib offline document checks](../../.github/workflows/protocol.yml#L203), streamed from the workflow and run with `python3.12 -B` | 68 invocations, all exit 0. The live `scripts/check_loopback_host.py` invocation was omitted under the supervisor's no-network rule. Its `--self-test` passed. |
| [KTX classifier](../../.github/workflows/ktx-kernel.yml#L27) and [KIX classifier](../../.github/workflows/protocol.yml#L109), replayed with the worktree's raw diff | Both exit 0 with `docs_only=true` on four regular-file paths. Rust and the protocol job's full verification steps are outside the classified scope. The separate Rights Scale job was outside the touched paths. |
| `sha256sum sdk/compat/verify_compat.mjs`, `git hash-object --no-filters sdk/compat/verify_compat.mjs` | Both exit 0. The IDs match the verifier identity in the transcript. |
| `git hash-object --no-filters` on both kernel locks | Exit 0 before and after. Both expected Git blobs matched. |
| Python inventory and byte check against `git ls-tree -rz HEAD -- reference/v0.3-rc1` | Exit 0 before and after. All 108 files matched their committed blobs. Both snapshots of the 108 files and 13 directories had SHA-256 `5c851da7f81762bdd6f28e6d48e34fff55a24c7ad3d6b1ccb896ea0539706efd`. |
| `git diff --exit-code HEAD` and `git ls-files --others` on protected paths | Both exit 0 with no tracked changes or new files in the checked paths. |
| `git diff --check`, `git status --short --branch --untracked-files=all`, `git rev-parse origin/main HEAD HEAD:reference/v0.3-rc1` | Exit 0. Only the four listed paths changed, and both refs still match the starting HEAD. |

| Protected path | Git ID before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` blob | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` blob | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1` tree | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

## Changed paths and delivery

- `validation/2026-11-25-plan-producer-extension-order-evidence/repro_extension_order.mjs`
- `validation/2026-11-25-plan-producer-extension-order-evidence/README.md`
- `docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.md`
- `docs/README.md`

The supervisor owns commit and publication. The worktree patch has no
implementation, final task or merge commit SHA. A2 non-author review and
exact-head KTX and KIX CI remain delivery gates. Neither workflow has a run ID,
status or conclusion for this uncommitted patch.
