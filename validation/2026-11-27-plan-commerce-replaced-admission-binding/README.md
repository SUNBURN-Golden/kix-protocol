# Replacement admission binding builder evidence

## Task and base

The task is `plan-commerce-replaced-admission-binding` on
`agent/kix-plan-commerce-replaced-admission-binding`. The user-supplied node
brief and design plan are the task input. The node also matches the local
planner record `/workspace/kix-run/logs/planner_1795774962_codex0.last.md`.
There is no issue or `docs/tasks/` document for this node. The starting branch
HEAD and cached `refs/remotes/origin/main` matched at
`7b84c6912f4db44aeb94e62f4f52575e076c035a`. The supervisor's network
restriction ruled out a remote fetch. Dependencies are the temporal vectors
and Commerce companion evidence index already present at that base.

## Coverage

| Requirement | Existing coverage | Evidence added |
|---|---|---|
| Expire and replace an admission on the same paid, issued right | Sufficient. `test_commerce_temporal_vectors.py::CommerceTemporalVectorTests.test_expired_authorization_replacement` covers expiry, replacement, consume and accepted replay. | The pack reuses all 12 source steps through `replace` and checks canonical equality with the temporal inputs before execution. |
| Use the old gate with the replacement request, then the replacement gate with the old request | Partial. The refusal matrix in `test_admission_rejection_atomicity.py` checks both codes individually on an authorized credential. The two crossed presentations against one replacement authorization were uncovered. | `CommerceReplacedAdmissionBindingVectorTests.test_complete_output_bytes_and_references` validates each published input, uses fresh operation identities and compares adjacent detached snapshots across both refusals. |
| The matching pair consumes once and both bound journals record the exact binding | Partial. The temporal case proves consumption and replay stability. It does not run the two crossed presentations immediately before the match or assert a sole consume with the matching binding in each journal. | The replay requires `CONSUMED_ONCE`, right version 2, detached authorization and an `ISSUED` slot. Each bound journal preserves its prior entries and appends one matching consume. |
| Separately resolve payment and issuance | Partial. The temporal pack has both receipts. This replacement-binding pack and its traceable references were uncovered. | The replay resolves both original receipt pointers and compares complete receipt bytes. The payment has no right and issuance carries version 1 and the same payment reference. |
| Navigate and verify the new pack through the companion index | Partial. `CommerceCompanionEvidenceIndexTests.test_complete_index` validates the existing packs. | Fifteen associations link exact bodies, outcomes, the replay symbol and bindings. The index test verifies all three presentations resolve to command 74 with `MOCK_EVIDENCE` and rejects swapping the two refusal references. |

The two refusals and subsequent acceptance match the existing predicates.
The node surfaced no contract violation or contract-undefined behavior.
[Admission contract §§5 and 11](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md)

## Changed paths

- `reference/booking_resale_admission/fixtures/commerce_replaced_admission_binding_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_replaced_admission_binding_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_replaced_admission_binding_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `validation/2026-11-27-plan-commerce-replaced-admission-binding/README.md`

## Local verification

Commands ran from the repository root with Python 3.12.15,
`PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`. In the commands below,
`$bra` is `reference/booking_resale_admission`. The focused checks ran
before the broader suites.

| Command | Actual result |
|---|---|
| Inline `python3.12 -` using the replay and the pinned temporal source | Exit 0. Authored canonical input and outcome fixtures after asserting the ordered presentations, snapshots, journal effects and both historical receipts. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce_replaced_admission_binding_vectors.py'` | Exit 0. One test passed over all 15 steps. |
| Inline `python3.12 -` using `validate_index` | Exit 0. Appended 15 entries and resolved all 422 entries before writing the companion index. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce_companion_evidence_index.py'` | Exit 0. Fourteen tests passed, including the swapped refusal reference control. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce*.py'` | Exit 0. All 209 tests passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,099 tests passed, including the existing disposable loopback smoke test. |
| `python3.12 scripts/verify_commerce.py --report .local/verification/commerce.json` | Exit 0, `PASS`. Calculation-only evidence reports zero external calls. |
| `python3.12 scripts/check_docs_index.py` and repeat with `--self-test` | Both exit 0. 477 scanned, 442 indexed and 35 allowlisted. |
| `python3.12 scripts/check_bra_evidence_map.py` and repeat with `--self-test` | Both exit 0. Validated 39 rows and 219 citations. All 50 negative controls passed. |
| `python3.12 scripts/check_ci_test_discovery.py` and repeat with `--self-test` | Both exit 0. Nine reference suites, eight Node tests and four Python modules reached. All 18 negative controls passed. |
| `python3.12 scripts/check_openapi_contract.py` and repeat with `--self-test` | Both exit 0. The catalogue pin and all 84 commands matched. |
| `python3.12 scripts/check_integration_gate_openapi.py` and repeat with `--self-test` | Both exit 0. Validated 84 commands and local endpoint constraints. |
| `python3.12 -m unittest integration_gate.test_offline_limits` | Exit 0. All 16 tests passed under the socket guard. |
| `python3.12 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and repeat with `--self-test` | Both exit 0. Validated 84 commands and 13 `NOT_BOUND` reads. All 10 negative controls passed. |
| `python3.12 scripts/check_producer_qualification_tuple.py` and repeat with `--self-test` | Both exit 0. Verified 84 command identities and 13 reads. |
| `python3.12 scripts/check_read_model_source_map.py` and repeat with `--self-test` | Both exit 0. Verified 13 queries and 145 citations. |
| `python3.12 scripts/verify_runtime_architecture.py` | Exit 0. Architecture and declared dependency gate passed. |
| `python3.12 scripts/test_runtime_architecture.py` | Exit 0. All seven tests passed. |

### Rust workflow checks

Cargo used the pinned 1.98.1 toolchain and `CARGO_NET_OFFLINE=true`. The
repository manifest requires `duckdb` for `kix-analytics-audit`, so offline
resolution stopped before compilation. The cache checker reported 16 of 378
locked registry archives present. Missing archives include `duckdb`,
`libduckdb-sys` and `bcs`.

The fallback used an inline `python3.12 -` command to copy six local-only
crates under `.local/verification/replaced-admission-rust-mirror/` with the
same toolchain pin. `diff -qr` matched the six source trees and `cmp` matched
the toolchain file. `cargo generate-lockfile --manifest-path "$manifest"
--offline` and an inline `tomllib` comparison confirmed that all six
resolved package records match `runtime/Cargo.lock`. The mirror includes
`kix-types`, `kix-feature-semantics`, `kix-feature-ir`, `kix-kernel`,
`kix-kernel-v5` and `kix-delegated-exec`.

| Command, with `$manifest` set to the workspace being checked | Repository manifest | Six-crate mirror with `--offline` |
|---|---|---|
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. | Repository formatting check covers the copied paths. |
| `cargo test --manifest-path "$manifest" -p kix-kernel --locked` | Exit 101, offline resolution. | Exit 0. |
| `cargo clippy --manifest-path "$manifest" -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101, offline resolution. | Exit 0. |
| `cargo tree --manifest-path "$manifest" -p kix-kernel --edges normal --locked` | Exit 101, offline resolution. | Exit 0. The sole normal dependency is `kix-types`. |
| `cargo test --manifest-path "$manifest" --workspace --locked` | Exit 101, offline resolution. | Exit 0. |
| `cargo clippy --manifest-path "$manifest" --workspace --all-targets --locked -- -D warnings` | Exit 101, offline resolution. | Exit 0. |
| `python3.12 scripts/check_cargo_offline_cache.py` with an inline JSON summary | Exit 0 for the cache inventory. 16 of 378 archives present. | — |

### Preservation

| Command | Actual result |
|---|---|
| `git rev-parse HEAD refs/remotes/origin/main` before and after | Both refs were `7b84c6912f4db44aeb94e62f4f52575e076c035a`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before and after | Matched the locked blobs `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, respectively. |
| `find reference/v0.3-rc1 -type f -print0 \| sort -z \| xargs -0 sha256sum`, then `cmp` | Both 108-path byte inventories matched, with manifest SHA-256 `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`. |
| `git diff --exit-code HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks .github docs/contracts sdk integration_gate` and `git ls-files --others --exclude-standard --` over the same paths | Exit 0 and no listed paths. |
| `git diff --check`, `git status --short --branch --untracked-files=all`, and inline `python3.12 -` using `git show` and `git ls-files` | Exit 0. Ten changed paths. New files passed whitespace checks. Prior index bytes were retained before the appended pack, yielding 15 packs and 422 entries. |
| `git hash-object` and `sha256sum` on the two new fixtures | Exit 0. Input Git blob `f98dc38e7aef07683e3f1a3a88f4d4303e5199dc`, SHA-256 `f101e5864f5be643a2c6cc32cf58acc605b49ccac752b16465d8d030101a9468`. Output Git blob `04d54cb94bec6516f964329545d53080ceef6a99`, SHA-256 `82447798f29bcb7d6a299707b82a0123e3abada62bc4f9a962dddee0228703a4`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Computed the three KTX workflow input digests. |

## Delivery and limits

Implementation and final task head are an uncommitted worktree patch on the
recorded base. Publication belongs to the supervisor. Exact-head KTX and KIX
CI have no run ID, status or conclusion for this patch. A2 non-author review
and both hosted workflow results remain delivery gates. There is no merge SHA
or post-merge verification.

The six-crate Rust mirror excludes `kix-bcs1` and `kix-analytics-audit`.
Full-workspace Rust tests and Clippy remain unverified. Hosted bootstrap and
the Move, chain and ZK workflow stages were outside local verification of the
touched paths.

This source-informed in-process evidence carries `HOLD_SEMANTIC`. All 13
reads remain `NOT_BOUND`, SD1 remains `OPEN` and User-owned, and external
consumer acceptance remains `UNVERIFIED`. Rejected-key bookkeeping is
process-local. The checks cover synthetic inputs and accepted journals in
one host. External Commerce execution, real funds or provider calls, venue
equipment, chain execution, durable recovery, distributed fencing, legal
compliance and production readiness are outside this evidence. Product TTLs,
fees and compensation remain `UNDETERMINED` with Astra and the User. Provider
and legal terms retain their existing owners.
