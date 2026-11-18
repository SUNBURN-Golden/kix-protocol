# BCS1 contract-bound regressions

Builder record for `plan-plan-bcs1-contract-bound-regressions`, from planner run `1792980988` and the supervisor's Option A decision on 2026-11-18. The task input is the supervisor-provided node and design plan. The node has no issue or `docs/tasks/` file.

The branch `agent/kix-plan-plan-bcs1-contract-bound-regressions` started and ended at `fc11cdf0150e54ed38bb363f2ded7238c48c6e53`. The implementation is the working-tree patch. The local `origin/main` reference was `693d6fe2fd04e4e1cb23175e7111b600bef4a25f`, 341 commits ahead. The BCS1 crate, contract, map and checker matched at both starting commits. The workspace manifest, lockfile and protocol workflow differed, so the Rust results below apply to the supplied checkout. The supervisor's offline restriction took precedence over the fetch step. Remote freshness is unverified.

Contract blob `19a58ab1e232c54eb39b717a94c637322c493a4d`. Rust and Cargo both reported version 1.98.1.

## Coverage and classification

The existing coverage below was inspected before adding the tests. Existing code and symbol citations are in the [BCS1 evidence map](../../docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md).

| Follow-up | Existing coverage | New evidence and AGENTS §8 classification |
|---|---|---|
| `FU-ZERO-ID` | **Not covered.** `golden_vectors.rs::domain_schema_and_version_are_bound` and `lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected` exercise mismatched identities. | `fu_zero_id_schema_version_zero_is_rejected` rejects a matching zero-version fixture on encode and decode and accepts version 1 (§1, A). The `InvalidSchemaIdentity` variant is B. |
| `FU-ENVELOPE-TOO-LARGE` | **Not covered.** `lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected` reaches the parser and checks trailing data. | `fu_envelope_too_large_is_rejected_before_bcs_decode` uses the same invalid framing at the bound and one byte above it to exercise guard order (§2, A). `EnvelopeDecode`, `EnvelopeTooLarge` and the public 32-byte overhead used to locate the bound are B. |
| `FU-BODY-TOO-LARGE-ENCODE` | **Not covered.** `golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` encodes an in-bound body. | `fu_body_too_large_encode_is_rejected` accepts 16 bytes and rejects 17 with `BodyTooLarge`. The encode-side guard and its variant are B. §2 names `MAX_BODY_BYTES` and specifies the decode check. |
| `FU-BODY-TOO-LARGE-DECODE` | **Not covered.** `lib.rs::round_trip_and_hash_are_deterministic` decodes an in-bound body. | `fu_body_too_large_decode_is_rejected` rejects a valid frame within the envelope bound containing a body one byte over the schema limit, with an at-limit round-trip control (§2, A). `BodyTooLarge` is B. |
| `FU-UTF8-MULTIBYTE` | **Not covered for multibyte.** `lib.rs::bounded_utf8_rejects_oversize_values` covers ASCII construction and body-helper decoding. | `fu_utf8_multibyte_limit_counts_bytes_not_chars` round-trips `한` at exactly three bytes and rejects `한a` during construction and full-envelope decode (§2 and §8 gate 5, A). `BoundedUtf8Exceeded` and `BodyDecode` are B. |
| `FU-TRUNCATED-ENVELOPE` | **Not covered for truncation.** `lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected` has a trailing-byte probe. | `fu_truncated_envelope_is_rejected` rejects cuts at zero bytes, within the header and one byte before the end (§8 gate 3, A). `EnvelopeDecode` is B. |

The fixture types share the contract's reserved `65535/65535` identity. Each test selects its local type through the public API. The raw-body fixtures isolate envelope and length behavior from schema-specific body validation. These are source-informed regressions. They found zero class C violations.

The envelope-bound row remains PARTIAL. Zero domain/schema semantics and encode-side `EnvelopeTooLarge` reachability remain contract-undefined and untested. `FU-S08-MOVE-EQUALITY` and `FU-S08-SDK-EQUALITY` remain open with the S08 Move/SDK schema owner. The three truncations are fixed samples. Fuzzing, a systematic malformed-input corpus, production registry enforcement, runtime durability, provider calls, chain finality and production readiness are outside this evidence.

## Changed paths

- `runtime/crates/kix-bcs1/tests/contract_bound_regressions.rs`
- `scripts/check_bcs1_evidence_map.py`
- `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-26-plan-bcs1-contract-bound-regressions/README.md`

## Commands and results

Cargo verification ran in `runtime/` against the locked dependency cache. The workspace and kernel test totals were summed from the Cargo result lines. The commands correspond to the Rust and relevant offline documentation steps of `protocol.yml` and `ktx-kernel.yml` on this branch.

| Command | Actual result |
|---|---|
| `git status --short --branch`, `git rev-parse origin/main HEAD`, `git rev-list --left-right --count HEAD...origin/main` | Initial worktree clean. Local refs as recorded above. Delta `0 341`. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs`, `git hash-object` for both files before work and `git hash-object --no-filters` after work | Both matched HEAD and the required blobs. Kernel lib `69564b166f0c27f9af5d8422f0a466b18d74c20f`. Quarantine test `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `cargo test -p kix-bcs1 --offline --locked` | 13 passed, including all six regressions, on the initial run and after formatting. |
| `cargo clippy -p kix-bcs1 --all-targets --offline --locked -- -D warnings` | Passed on the initial run and after formatting. |
| `CARGO_NET_OFFLINE=true cargo fmt --all -- --check` | Initially exited 1 over one new assertion's line wrap. Passed after the wrap was corrected. |
| `cargo test --workspace --offline --locked` | 263 passed, 0 failed, 0 ignored. |
| `cargo clippy --workspace --all-targets --offline --locked -- -D warnings` | Passed. |
| `cargo test -p kix-kernel --offline --locked` | 78 passed, 0 failed, 0 ignored. |
| `cargo clippy -p kix-kernel --all-targets --offline --locked -- -D warnings` | Passed. |
| `cargo tree -p kix-kernel --edges normal --offline --locked` | Kernel's only normal dependency was `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Printed all three KTX dependency evidence digests. |
| `python3 scripts/check_bcs1_evidence_map.py` | Passed with 39 rows, 17 COVERED, 11 PARTIAL and 11 NOT_COVERED. |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Passed with 2 positive controls and 52 negative fixtures, including the two new closure guards. |
| `python3 scripts/check_ci_checker_wiring.py` and `python3 scripts/check_ci_checker_wiring.py --self-test` | Passed. Self-test detected 13 negative controls. |
| `python3 scripts/verify_runtime_architecture.py` and `python3 scripts/test_runtime_architecture.py` | Architecture gate passed and all 7 gate tests passed. |
| `python3 scripts/check_docs_index.py` and `python3 scripts/check_docs_index.py --self-test` | The initial plain check exited 1 because this record did not yet exist. Both passed after the record was added (260 scanned, 225 indexed, 35 allowlisted). |
| Inline `python3` map comparison with `git show HEAD:docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md` | Verified both S08 entries in both tables and all map bytes outside the approved rows, counts and §§3–4. |
| `git diff --check`, `git diff --exit-code HEAD --` on protected paths and `git diff --exit-code origin/main -- runtime/crates/kix-bcs1/src runtime/CANONICAL_BINARY_BCS_V1.md reference/v0.3-rc1` | Passed. Codec source, contract, reference tree, locked kernel files, workspace manifest and lockfile, workflows, `.aiops/` and task files matched the supplied HEAD. The codec source, contract and reference tree also matched the local `origin/main`. |
| Inline `python3` checks using `git show origin/main:<path>` with the edited map substituted in memory | The local `origin/main` baselines passed. The first overlay detected four stale Class B quotations and a stale roll-up count. Preserving the quoted text within §4 made the Class B index pass. The roll-up passed with its BCS1 count refreshed in memory. |

## Delivery and integration

The evidence map's §0 basis remains historical. This record provides the new basis without editing §0. The §4 observations retain the verbatim passages cited by the newer local `origin/main` Class B index.

The supplied branch predates `docs/status/EVIDENCE_MAP_ROLLUP.md`. Applying the patch to the newer local `origin/main` requires refreshing the roll-up's BCS1 copy to `Counts: rows=39 COVERED=17 PARTIAL=11 NOT_COVERED=11`. That one-line refresh passed the newer checker in memory and is outside the approved worktree edit set.

The worktree is ready for supervisor handoff on the supplied base. There is no committed delivery head or merge commit. KTX kernel verification and KIX protocol verification have no exact-head run ID, status or conclusion for this patch. Post-merge CI and non-author A2 review are pending supervisor delivery.

## PR fix round 1 (2026-11-18)

Builder fix-round session under the supervisor's offline restriction. The first-session record above is preserved unchanged.

### Finding and root cause

Exact-head KIX protocol CI failed in `Stdlib offline document checks` with a single error:
`stale Counts copy: `runtime/CANONICAL_BINARY_BCS_V1.md`: docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md`
(exit 1). No independent review finding was supplied. The cause is the one the first session predicted in "Delivery and integration": the branch base `fc11cdf0150e54ed38bb363f2ded7238c48c6e53` predates `docs/status/EVIDENCE_MAP_ROLLUP.md` and `scripts/check_evidence_map_rollup.py` (added on main by `7dce9b5`, `plan-plan-evidence-map-rollup-check`). PR CI runs on the merge with main, where the roll-up still copied the pre-node Counts line `Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17` while this node legitimately changed the map to `Counts: rows=39 COVERED=17 PARTIAL=11 NOT_COVERED=11`. The roll-up checker requires the copy to match the map byte-for-byte.

The failure was reproduced locally read-only: `git merge-tree --write-tree origin/main HEAD` produced clean merge tree `a89393b4eb8065ef5917a9fb056a6781195774b0`; extracting it and running all 67 document-check commands from main's `protocol.yml` gave exactly one failure, the same stale-Counts error. No other document check failed on the merge tree.

### Fix applied (this round's changed paths)

- `docs/status/EVIDENCE_MAP_ROLLUP.md` — new in this worktree: main's roll-up verbatim (`git show origin/main:docs/status/EVIDENCE_MAP_ROLLUP.md`) with exactly one line changed, the BCS1 row's Counts (verbatim) cell refreshed to `Counts: rows=39 COVERED=17 PARTIAL=11 NOT_COVERED=11`. Verified by diff against main's version: line 52 only. No status, owner, grade or other row changed; the owners cell already matches the map's unchanged owner column.
- `docs/README.md` — the existing node bullet now also links the roll-up (`[roll-up](status/EVIDENCE_MAP_ROLLUP.md)`), so `check_docs_index.py` passes on the branch base with the roll-up document present. The merge-tree checker is set-based; main's own roll-up index entry is unaffected.
- `validation/2026-10-26-plan-bcs1-contract-bound-regressions/README.md` — this section.

No Rust, contract, map, checker-script, workflow, `.aiops/`, `docs/tasks/` or reference-tree change was made in this round. The six regressions, their classifications (zero class C) and the S08 rows are unchanged.

### Supervisor integration requirement (blocking for delivery)

The roll-up file does not exist at the branch base, so committing it creates exactly one add/add conflict when the branch merges with main. Verified with read-only plumbing (`git merge-tree --write-tree --merge-base=fc11cdf… origin/main <worktree-state tree>`): `CONFLICT (add/add): Merge conflict in docs/status/EVIDENCE_MAP_ROLLUP.md`; `docs/README.md` and everything else auto-merge. A plain commit-and-push therefore leaves the PR conflicted and no merge-ref CI can run.

Required integration: merge `origin/main` into the branch (or refresh the base) and resolve the single roll-up conflict to **main's current roll-up with the BCS1 Counts cell set to `Counts: rows=39 COVERED=17 PARTIAL=11 NOT_COVERED=11`**. If main has not moved past the locally observed `693d6fe2fd04e4e1cb23175e7111b600bef4a25f`, the worktree file is exactly that resolution (main blob `4ce46f5faaa70920cc2391b08265bc3f45d0d284` → fixed blob `bbe16e9db0b24beb933d903ecd5bbf020642649a`). If main moved, re-apply the one-cell refresh to main's newer roll-up instead of keeping this file wholesale. The builder did not merge, commit, push or fetch; base integration is the supervisor's git operation.

### Commands and actual results (fix round 1)

Branch worktree (base `fc11cdf`, HEAD `d77ca988b779207be4ade258b7f93e041584544e`, local `origin/main` `693d6fe2fd04e4e1cb23175e7111b600bef4a25f`, 341 commits ahead; fetch NOT_RUN under the offline restriction):

| Command | Actual result |
|---|---|
| `git hash-object` on both locked kernel files, before and after | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, both rounds. |
| `git diff --exit-code HEAD --` on `runtime/crates/kix-bcs1/src`, contract, `reference/v0.3-rc1`, `.aiops`, `docs/tasks`, `.github`, `runtime/Cargo.toml`, `runtime/Cargo.lock`, `runtime/crates/kix-kernel` | Unchanged. `git diff --exit-code origin/main -- reference/v0.3-rc1 runtime/crates/kix-bcs1/src runtime/CANONICAL_BINARY_BCS_V1.md` also unchanged. |
| S08 row comparison against `git show HEAD:` of the map | Identical; the map file itself is untouched this round. |
| `cargo test -p kix-bcs1 --offline --locked` (in `runtime/`) | 13 passed (3 lib + 6 regressions + 4 golden), 0 failed; all six `fu_*` tests named and ok. |
| `cargo clippy -p kix-bcs1 --all-targets --offline --locked -- -D warnings` | Passed. |
| `CARGO_NET_OFFLINE=true cargo fmt --all -- --check` | Passed. |
| `cargo test --workspace --offline --locked` | 263 passed, 0 failed, 0 ignored. |
| `cargo clippy --workspace --all-targets --offline --locked -- -D warnings` | Passed. |
| `cargo test -p kix-kernel --offline --locked`; `cargo clippy -p kix-kernel --all-targets --offline --locked -- -D warnings`; `cargo tree -p kix-kernel --edges normal --offline --locked` | 78 passed, 0 failed; clippy passed; kernel's only normal dependency is `kix-types`. |
| `python3 scripts/check_bcs1_evidence_map.py` and `--self-test` | Passed: `Counts: rows=39 COVERED=17 PARTIAL=11 NOT_COVERED=11`; self-test 2 positive controls, 52 negative fixtures. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Passed after the bullet edit: scanned=261 indexed=226 allowlisted=35. Before the edit both failed with `not indexed: docs/status/EVIDENCE_MAP_ROLLUP.md`. |
| All 49 document-check commands from this branch's `protocol.yml` | 48 pass. `check_ci_checker_wiring.py` fails with 6 errors: the roll-up document cites `check_evidence_map_rollup.py`, `check_feature_semantics_evidence_map.py`, `check_integration_gate_contract_evidence_map.py`, which exist and run only on main. See deviations. |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | Gate OK; 7 gate tests OK. |

Simulated resolved PR merge tree (read-only plumbing; no commit, no ref or worktree mutation): worktree state tree `777ce64ce8f3ff907592912b1ec19c9127aba8d1` built with a temporary index; `git merge-tree --write-tree --merge-base=fc11cdf… origin/main <tree>` gave the single add/add conflict above; merged tree `b6f3111468fcb14502724a8947a9244d813b8679` extracted to a temp directory with the roll-up resolved to the fixed file; resolved tree object `ea03934d6f1cb50d785f42df2c0684d581303901`. `git diff --stat origin/main <resolved tree>` shows exactly six changed paths: the five first-session paths plus the one-line roll-up refresh.

| Command (in the resolved merge tree) | Actual result |
|---|---|
| All 67 document-check commands from main's `protocol.yml`, including `check_evidence_map_rollup.py` plain and `--self-test` | 0 failures. Roll-up plain: `evidence map roll-up ok: contracts=25; textual index only`. |
| `CARGO_TARGET_DIR=<temp> CARGO_NET_OFFLINE=true cargo test --workspace --locked` (cold build) | 345 passed, 0 failed, 0 ignored; all six `fu_*` regressions ok. |
| `cargo test -p kix-bcs1 --locked`; `cargo test -p kix-kernel --locked` | 13 passed / 0 failed; 139 passed / 0 failed. |
| `cargo clippy --workspace --all-targets --locked -- -D warnings`; `-p kix-bcs1`; `-p kix-kernel` | All passed. |
| `cargo fmt --all -- --check` | Passed. |

### Deviations and non-claims

- Branch-local `check_ci_checker_wiring.py` cannot pass while the roll-up document is present on this base: the document cites three checkers that main added after the base, and wiring them into this branch's CI would be a prohibited CI edit and would drag in main-only maps. On the PR merge tree the same checker passes (verified above). This is a stale-base artifact, not a delivery defect; it disappears once the supervisor integrates main.
- Local Python is 3.13.5; `protocol.yml` pins 3.12. All stdlib checks ran on 3.13.5 locally.
- Remote freshness unverified (fetch NOT_RUN, offline restriction). The merge-tree evidence is against the locally observed `origin/main` `693d6fe…`; if main moves, the roll-up cell refresh must be re-applied to the newer roll-up and the merge-tree battery re-run by the supervisor.
- The merge-tree Rust results come from a local cold build of the simulated resolved merge tree, not from GitHub CI. No exact-head CI run ID exists for this round; the supervisor's delivery produces it. No class C violation was found; classifications and non-claims of the first session stand. No production, durability, bank, chain or readiness claim is made.
