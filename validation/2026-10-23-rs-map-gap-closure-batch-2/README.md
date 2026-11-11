# RS map gap closure batch 2 — builder validation

Date: 2026-10-23; resumed 2026-10-24 after the owner provisioned the Rust toolchain/cache. State: **READY** for supervisor handoff: node-specific tests and all required local equivalents pass, including the previously blocked workspace tests and Clippy. No publication or merge is authorized. This is builder-authored evidence, not non-author review, Astra acceptance, merge readiness or a capability-grade change.

## Input and source anchors

- Node: `plan-plan-rs-map-gap-closure-batch-2`; source: KIX planner run 1792670909 (`/workspace/kix-run/logs/planner_1792670909`), loop-proposed and absent from `.aiops/program.json`. No issue exists. The task document is the supervisor-supplied node envelope and design plan in this session; there is no corresponding `docs/tasks/` file to edit.
- Dependencies: `plan-rs-model-gap-closure`, `plan-rs-grant-cut-order-tests`, `plan-plan-rs-offline-suite-evidence-sync`; audit floor A2, `astra_gate: None`, `user_merge: False`. This is not ASTRA program mode.
- Branch: `agent/kix-plan-plan-rs-map-gap-closure-batch-2`. The earlier attempt recorded initial clean HEAD and worktree `origin/main` both at `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`. At this resume, HEAD is still `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af` and the local `origin/main` ref is `f50047a902f9e4f2e6a25e904f6f89ad758eb8c0`; `git rev-list --left-right --count HEAD...refs/remotes/origin/main` reports `0 27`. No rebase, merge or base change was performed. Upstream changes include the docs index and capability register, so the supervisor must account for that delta when publishing. Remote freshness is unknown: `git fetch origin main` was skipped because the supervisor forbids all network actions.
- Implementation/final committed head: unavailable (changes deliberately uncommitted). HEAD remains the base above. No commit, push, PR, issue, comment, tag, branch operation or merge occurred.
- Exact-head KTX kernel verification and KIX protocol verification: run ID/status/conclusion unavailable; no GitHub action authorized. Merge SHA and post-merge main CI: not applicable. Historical CI is not inherited.
- Read inputs: root governance/README, development plan, baselines, authority model, control-plane pointer/client pin, program decisions §5, RS profile and both maps, existing Move/Python evidence, prior gap-closure/grant-cut/offline-suite records, and the repository workflows. Candidate control-plane adoption does not activate runtime.

## Complete changed paths

- `reference/rights_scale/sui/tests/private_path_tests.move`
- `reference/rights_scale/test_private_model.py`
- `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`
- `docs/status/RS_IM_EVIDENCE_MAP.md`
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`
- `docs/README.md`
- `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md`

Only the two test files and evidence/index files implement this node. The owner resolved the earlier Rust environment blocker outside this session and authorized removal of `DECISION_REQUIRED.md`; it was already absent on resume and remains absent. Ignored scratch/config/cache files are under this checkout's `.local/`; no wallet or secret was generated.

## Existing coverage before adding tests (AGENTS §7)

| Requirement | Existing evidence inspected | Before | Gap closed here |
|---|---|---|---|
| RS-C09 public-then-shield | `test_private_model.py::test_a_publicly_consumed_ticket_cannot_be_shielded`; Move shield-then-public and nullifier-replay cases | partially covered | New Move `a_publicly_consumed_ticket_cannot_be_shielded` exercises the real shield entry after public consume with the current version. |
| IM-18 pinned verifier across a later manifest claim | `zk_staging_tests.move::claim_zk_twice_aborts`, `two_shows_pinning_different_manifests_have_different_domains`; `private_path_tests.move::a_verifier_other_than_the_pinned_one_is_rejected` | partially covered | New passing temporal continuity test plus extension of the exact-authority rejection case to use later show B's pinned verifier. |
| IM-19 absence of a secret/path in the gate signature | `MoveParity.test_constants_match_the_move_source`; existing source-order assertions; `admission-packet.test.mjs::packet_contains_only_public_fields` asserts the packet only | partially covered; exact gate-signature assertion not covered | New explicitly source-informed `MoveParity.test_consume_private_signature_has_no_secret_or_witness_path`. |
| Map schemas, citation resolution and counts | Existing two map checkers and their self-tests | sufficiently covered | Reuse unchanged; no checker or duplicate checker test added. |

## Assertions and map effects

- RS-C09: issue to B, record inventory, authorize and publicly consume. Before the expected abort, assert CONSUMED (1), version 2, unchanged totals and a zero-leaf empty-root tree. Call real `shield` through `z::shield_proved` using version 2, the pinned verifier and nonzero commitment 100. Exact `EClosed` (1) at `kix_rights_scale::rights_scale` is required, before Groth16. No assertion after the abort and no rollback-state claim.
- IM-18: show A has two notes, consumes once under A, then show B claims/seals a distinct manifest B. A retains its original domain and consumes a second time under A with fresh nullifier/challenge, emits `PrivateAdmission`, and records both values. The separate rejection test consumes A first, creates/claims B and then passes B's verifier to A, expecting exact `EAuthority` (4) at the rights-scale module. Consumption helpers omit Groth16; these tests establish state/binding continuity, not a profile upgrade or proof acceptance.
- IM-19: strip source comments, find exactly one real `public fun consume_private(` declaration, normalize whitespace and compare the entire ordered 13-parameter interface, including names and types. The test excludes the `_unproven_for_testing` helper and fails on added or renamed secret/path parameters. It is source-informed characterization, not independent privacy validation; arbitrary proof-byte contents and transport are outside its assertion.
- RS-C09 remains `COVERED_LOCALNET` on its historical localnet provenance; the new result is a local Move unit test. IM-18 changes from `PARTIAL` to `COVERED_MODEL_OR_MEMORY` because its complete missing sentence is now exercised. IM-19 remains `PARTIAL`: real BCS decoding and transport completeness remain open.
- Predicate counts: `COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` (174 citations).
- Impact counts: `COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` (200 citations).
- EV-RS links this record; its grade and the operational count (0) remain unchanged. The docs index links this record. No profile/operational value selected: K, P, S, W, MAX_BUNDLE_CHAIN and the IssuerCap option remain UNDETERMINED/unselected.

## Earlier attempt: tools, local environment and actual results

Versions actually observed: `sui 1.79.1-808640d9b49a` (matches `toolchains.json`); `Python 3.13.5`; `rustc 1.98.1 (48a229cea 2026-09-01)`; `cargo 1.98.1 (797e8a9bc 2026-08-05)`. Python differs from CI's 3.12 pin; no interpreter install was attempted.

Sui was absent from PATH; the read-only cached executable `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui` was reused. Commands below spell out that binary. `python3 scripts/configure_local.py` produced an empty keystore configuration in `.local/sui-config/`. Initial Sui execution failed on the default read-only config location; setting `SUI_CONFIG_DIR` exposed a second read-only dependency-cache lock. Copying the existing cache using `cp -a /home/box/.move .local/move-cache` resolved that failure. All successful Sui commands ran with `SUI_CONFIG_DIR="$PWD/.local/sui-config"` and `MOVE_HOME="$PWD/.local/move-cache"`. No HOME override, dependency download, RPC or public endpoint was used. `--build-env mainnet` selects compilation environment only; these are unit tests, not mainnet execution. No build manifest/lockfile changed.

The following initial-attempt table and output are retained from the draft and its local logs; these are historical results, superseded by the resumed verification below where applicable. All Cargo commands ran with `CARGO_NET_OFFLINE=true` to enforce the no-network instruction. Long commands were sequential within foreground runners; none was launched as a shell background job. Local logs and result JSON are ignored scratch in `.local/rs-map-gap-closure-batch-2/`; durable output excerpts are below.

| Command actually run | Exit / actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse refs/remotes/origin/main`; `git branch --show-current` | 0; clean initial tree, both SHAs and branch as above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after implementation) | 0; both required blobs match, exact values below. |
| `sui --version` | 127: command not found on PATH. |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui --version` | 0: `sui 1.79.1-808640d9b49a`. |
| `python3 scripts/configure_local.py` | 0: `Checkout-local Sui configuration ready; no wallet was generated.` |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_publicly_consumed_ticket_cannot_be_shielded` (initial default config/cache) | 1: `Read-only file system (os error 30)`. |
| Same command with only local `SUI_CONFIG_DIR` | 1: lock acquisition in `/home/box/.move/git/` failed, read-only filesystem. |
| `cp -a /home/box/.move .local/move-cache` | 0; existing cached framework copied into writable checkout-local scratch. |
| Same public-shield command with local `SUI_CONFIG_DIR` and `MOVE_HOME` | 0: `Test result: OK. Total tests: 1; passed: 1; failed: 0`. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale -p test_private_model.py -k test_consume_private_signature_has_no_secret_or_witness_path` | 0: `Ran 1 test ... OK`. |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_verifier_other_than_the_pinned_one_is_rejected` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui` | 0: Test result: OK. Total tests: 260; passed: 260; failed: 0 |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0: Ran 167 tests in 4.417s; OK |
| `python3 scripts/check_status_register.py` | 0: `capability register ok: paths=332 ev_ids=15 original32=32` |
| `python3 scripts/check_status_register.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_rs_profile_traceability.py` | 0: `rs profile traceability ok: blueprint=47 profile=47 expected=47` |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_read_model_source_map.py` | 0: `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145` |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_docs_index.py` | 0: `docs index ok: scanned=208 indexed=173 allowlisted=35` |
| `python3 scripts/check_docs_index.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_i12_proof_ids.py` | 0: `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14` |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_delegation_layer_matrix.py` | 0: `delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6` |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0: `rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_rs_im_evidence_map.py` | 0: `rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0: `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7` |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_contract_error_codes.py` | 0: `contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0` |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_adapter_identity_map.py` | 0: `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8` |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0: `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0` |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_readiness_evidence_map.py` | 0: `readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9` |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/check_stage5_host.py --self-test` | 0: `self-test: pass` |
| `python3 scripts/verify_runtime_architecture.py` | 0: architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0: Ran 7 tests; OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0: All kix-kernel test binaries and doc-tests pass (78 tests across integration binaries). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 101: BLOCKED before compilation: missing cached `bcs v0.2.1`; attempted HTTP request refused by offline mode. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 101: BLOCKED before compilation: missing cached `bcs v0.2.1`; attempted HTTP request refused by offline mode. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0: Pass; no output and no files rewritten. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | 0: Pass; dev profile finished, no warnings. |

All 27 commands in the current `Stdlib offline document checks` run block of `.github/workflows/protocol.yml` were extracted and executed, in order, with their individual outputs and exit codes retained. This includes both map checkers, both self-tests, index/register checks and their self-tests. Kernel tests/Clippy and architecture/format checks were the closest available KTX equivalents at that point; full workspace tests and Clippy were blocked in that attempt. No CI was edited.

Actual new-case/full-suite output excerpts:

```text
[ PASS    ] kix_rights_scale::private_path_tests::a_publicly_consumed_ticket_cannot_be_shielded
Test result: OK. Total tests: 1; passed: 1; failed: 0
[ PASS    ] kix_rights_scale::private_path_tests::a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed
Test result: OK. Total tests: 1; passed: 1; failed: 0
[ PASS    ] kix_rights_scale::private_path_tests::a_verifier_other_than_the_pinned_one_is_rejected
Test result: OK. Total tests: 1; passed: 1; failed: 0
Test result: OK. Total tests: 260; passed: 260; failed: 0
Ran 167 tests in 4.417s
OK
```

Sui also emitted existing compiler/lint warnings in unchanged test helpers/root-math tests; they did not fail compilation or tests. No warning suppression or hygiene sweep was performed.

Historical output of both workspace Cargo blockers (before owner cache provisioning):

```text
error: failed to download `bcs v0.2.1`

Caused by:
  attempting to make an HTTP request, but --offline was specified
```

In the earlier attempt, read-only `find` searches under `/workspace`, `/tmp`, `/home/box` and `/opt` found neither `bcs-0.2.1.crate` nor an unpacked `bcs-0.2.1` source directory. We did not rerun the blocked commands without a changed environment or permit a network fallback.

## Protected bytes and AGENTS §8 classification

The before/after Git-format blob checks both produced:

```text
69564b166f0c27f9af5d8422f0a466b18d74c20f  runtime/crates/kix-kernel/src/lib.rs
b607996c83a119c349f1cc90469ac1ba82764e20  runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

`git diff --name-only -- reference/v0.3-rc1 reference/rights_scale/sui/sources reference/rights_scale/sui/Move.toml reference/rights_scale/sui/Move.lock reference/rights_scale/zk reference/rights_scale/client reference/rights_scale/vectors runtime .aiops docs/tasks docs/contracts docs/decisions .github` exited 0 with no output. These boundaries are unchanged. Final byte/hash and whitespace checks are recorded below after the completed report is written.

- **A, contract-defined and matching:** public-consumed ticket cannot shield; verifier/domain pinning survives another show's manifest claim; foreign verifier refusal. The temporal regressions pass without changing implementation semantics.
- **B, source-informed characterization:** the complete declared gate-call signature has no secret or witness-path parameter. This is deliberately a source-informed assertion of the current interface; it does not invent semantics for opaque proof bytes or transport privacy. Existing unresolved map/profile questions remain unchanged.
- **C, explicit contract violations:** none found. No locked-file edit or diagnostic contract-violation reproduction was needed.

## Deviations, limitations and handoff

1. Fetch skipped per the supervisor's no-network rule. Local `origin/main` freshness cannot be claimed.
2. Reused pinned Sui and copied cached public framework dependencies to checkout-local scratch because default locations were read-only. No tooling download, HOME override or secret needed.
3. Python 3.13.5 was available rather than CI's pinned 3.12; all 167 local Python tests pass under that interpreter.
4. The initial workspace test/Clippy dependency blocker was resolved by the owner: `rustup default 1.98.1-x86_64-unknown-linux-gnu` and `cargo fetch --locked` were performed by the supervisor, outside this builder session. The resumed verification uses the populated cache with network access disabled. No dependency, workspace or CI change was made to bypass the checks. The resolved `DECISION_REQUIRED.md` is absent.
5. No exact-head hosted CI or non-author review is available; this uncommitted builder handoff is not merge-ready. The supervisor owns publication and exact-head gates.

No localnet/ZK ceremony/proof generation, actual profile upgrade, circuit verification, Node suite rerun, load measurement, real BCS decoding, transport completeness, secrecy of arbitrary proof bytes, production runtime, real funds/providers, public endpoints, testnet/mainnet, durability, distributed fencing, bank exactly-once, chain finality, anonymity or legal compliance is claimed. Client/circuit/vector paths were not changed. Existing historical localnet evidence remains historical evidence at its own head. Operational values stay UNDETERMINED; the source-informed characterization is not clean-room or independent cryptographic evidence.

The remaining supervisor work is non-author exact-head review plus exact-head KTX/KIX CI after committing; those publication gates are not builder-local acceptance items. IM-19 real BCS/transport coverage and operational-value decisions remain separate follow-up tasks.

## Earlier attempt: final checks after writing its report

| Command | Exit / actual result |
|---|---|
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0: rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_im_evidence_map.py` | 0: rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_docs_index.py` | 0: docs index ok: scanned=208 indexed=173 allowlisted=35 |
| `python3 scripts/check_status_register.py` | 0: capability register ok: paths=332 ev_ids=15 original32=32 |
| `git diff --check` | 0: (no output) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | 0: 69564b166f0c27f9af5d8422f0a466b18d74c20f; b607996c83a119c349f1cc90469ac1ba82764e20 |
| `Per-file git hash-object vs git rev-parse HEAD:<path> for git ls-files reference/v0.3-rc1` | 0: 108 tracked files match HEAD; no untracked nonignored files |

## Resumed verification after the owner decision (2026-10-24)

The owner approved Option 1 and completed toolchain/cache provisioning outside this builder session. `DECISION_REQUIRED.md` was already absent at resume and remains absent. The seven-file implementation draft was inspected and retained; resumed edits correct source anchors and record the completed verification. No implementation semantics, profile, checker, CI, manifest or operational value changed.

Actual versions were rechecked: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1 (797e8a9bc 2026-08-05)`, `sui 1.79.1-808640d9b49a`, and `Python 3.13.5`. The initial bare `sui --version` check again returned 127 because Sui is not on PATH; the cached pinned binary below returned 0. No installer or network action was run.

The commands below ran sequentially in foreground subprocesses, narrow cases first. They used the same checkout-local `SUI_CONFIG_DIR`/`MOVE_HOME` and `CARGO_NET_OFFLINE=true` described above. Actual complete local outputs and exit codes were captured under `.local/rs-map-gap-closure-batch-2/resume-{narrow,full,runtime,docs}-results.json`; these ignored scratch logs are not publication artifacts. The durable table and excerpts below supersede earlier incomplete workspace results.

| Command actually rerun | Exit / actual result |
|---|---|
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_publicly_consumed_ticket_cannot_be_shielded` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_verifier_other_than_the_pinned_one_is_rejected` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale -p test_private_model.py -k test_consume_private_signature_has_no_secret_or_witness_path` | 0: Ran 1 test in 0.001s; OK. |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui` | 0: Test result: OK. Total tests: 260; passed: 260; failed: 0 |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0: Ran 167 tests in 3.683s; OK. |
| `python3 scripts/verify_runtime_architecture.py` | 0: architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0: Ran 7 tests in 0.163s; OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0: All test binaries/doc-tests pass: 78 passed, 0 failed, 0 ignored across 9 result summaries. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0: All test binaries/doc-tests pass: 257 passed, 0 failed, 0 ignored across 42 result summaries. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0: Pass; Finished `dev` profile [unoptimized + debuginfo] target(s) in 2.32s; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0: Pass; no output, no files rewritten. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | 0: Pass; Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.01s; no warnings. |
| `python3 scripts/check_status_register.py` | 0: capability register ok: paths=332 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | 0: rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | 0: read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_docs_index.py` | 0: docs index ok: scanned=208 indexed=173 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | 0: i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | 0: delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0: rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | 0: rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0: tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | 0: contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | 0: adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0: v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | 0: readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0: self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | 0: self-test: pass |

All 40 resumed verification commands above exited 0. The docs list was extracted unchanged from the complete `Stdlib offline document checks` run block in `.github/workflows/protocol.yml`; all 27 commands, including negative-control self-tests, passed. No workflow was edited. The Rust checks cover the requested closest local KTX/protocol equivalents; they do not replace hosted exact-head CI.

Actual resumed target/full-suite output:

```text
[ PASS    ] kix_rights_scale::private_path_tests::a_publicly_consumed_ticket_cannot_be_shielded
Test result: OK. Total tests: 1; passed: 1; failed: 0
[ PASS    ] kix_rights_scale::private_path_tests::a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed
Test result: OK. Total tests: 1; passed: 1; failed: 0
[ PASS    ] kix_rights_scale::private_path_tests::a_verifier_other_than_the_pinned_one_is_rejected
Test result: OK. Total tests: 1; passed: 1; failed: 0
Test result: OK. Total tests: 260; passed: 260; failed: 0
Ran 167 tests in 3.683s
OK
    Checking bcs v0.2.1
    Checking kix-bcs1 v0.1.0 (/workspace/kix-run/wt/plan-plan-rs-map-gap-closure-batch-2/runtime/crates/kix-bcs1)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 2.32s
```

Both map checks resolve the new citations: predicate `23 rows / 174 citations / 13,2,6,0,2`; impact `30 rows / 200 citations / 11,5,12,0,0,2`, in their declared status orders. EV-RS grade and operational count remain unchanged. IM-19 stays PARTIAL.

Final preservation checks and source anchors:

| Command / check | Exit / actual result |
|---|---|
| `git rev-parse HEAD`; `git rev-parse refs/remotes/origin/main`; `git rev-list --left-right --count HEAD...refs/remotes/origin/main` | 0: HEAD/base `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`; cached main `f50047a902f9e4f2e6a25e904f6f89ad758eb8c0`; delta `0 27`. Remote freshness unknown; no fetch/base change. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (resume before/after) | 0: `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `b607996c83a119c349f1cc90469ac1ba82764e20`; both match. |
| `python3 .local/rs-map-gap-closure-batch-2/resume_integrity.py` (first invocation) | 1: verification helper misread Git-quoted non-ASCII filenames from `git ls-files`; no source mutation or mismatch. Corrected the scratch helper to use NUL-delimited `git ls-files -z`. |
| `python3 .local/rs-map-gap-closure-batch-2/resume_integrity.py` (corrected invocation) | 0: both locks match; all 108 tracked `reference/v0.3-rc1` files hash-identical to HEAD; no untracked nonignored files there; protected boundaries have no diff; exactly seven authorized files changed; resolved decision file absent; whitespace clean. |
| `git diff --check` | 0: no output. |

The byte check compares each `git hash-object <path>` against `git rev-parse HEAD:<path>` using the NUL-delimited tracked path list. Protected boundaries additionally use `git diff HEAD --name-only --` for `reference/v0.3-rc1`, RS Move sources/Move.toml/Move.lock, zk, client, vectors, runtime, `.aiops`, `docs/tasks`, contracts, decisions and `.github`; the result is empty.

No new class C violation or contract-undefined behavior was found during resume; the class A and source-informed characterization classifications above remain. The latest local-main delta is recorded without adopting it. Non-author exact-head review, final committed implementation/task head, KTX/KIX run IDs/status/conclusions and any merge/post-merge fields remain unavailable or not applicable because the supervisor exclusively owns publication. Local READY means the authorized builder work and local checks are complete. The explicit non-claims and IM-19/operational-value follow-ups above remain.

### Checks after the resumed report was written

| Command | Exit / actual result |
|---|---|
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0: rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_im_evidence_map.py` | 0: rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_docs_index.py` | 0: docs index ok: scanned=208 indexed=173 allowlisted=35 |
| `python3 scripts/check_status_register.py` | 0: capability register ok: paths=332 ev_ids=15 original32=32 |
| `python3 .local/rs-map-gap-closure-batch-2/resume_integrity.py` | 0: Both locked blobs match; 108 preserved-reference files match HEAD; protected boundaries unchanged; exactly seven allowed changed paths; decision file absent; whitespace clean; source anchors/delta unchanged. |

## Merge conflict reconciliation (2026-10-24)

Node: `plan-plan-rs-map-gap-closure-batch-2`; task input is the supervisor's supplied node description, with no task issue/document created. Branch: `agent/kix-plan-plan-rs-map-gap-closure-batch-2`. Observed task/implementation HEAD: `b1fe707bfcc99ac43edcbd2622caad1a25e1ce22`. Cached `origin/main` and the existing `MERGE_HEAD`: `f50047a902f9e4f2e6a25e904f6f89ad758eb8c0`. Merge base: `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`; `git rev-list --left-right --count HEAD...origin/main` returned `1 27`. No fetch was run because the supervisor prohibits network actions; remote freshness is unknown. The merge was already in progress when this session began.

The only conflict was the appended validation list in `docs/README.md`. All of main's newer entries were retained verbatim and the node's batch-2 link was appended after them. `git diff MERGE_HEAD -- docs/README.md` shows only that node link and its separating blank line. Existing headings and anchors remain valid. The auto-merged register retains the batch-2 citation in EV-RS alongside main's newer register changes. This session edits only `docs/README.md` and this validation record; incoming auto-merged files were retained. Original node tests and both RS maps remain byte-identical to task HEAD; the existing coverage mapping and map status decisions above still apply. No new tests were added during reconciliation.

All commands below used existing local tools and caches. Sui used the same `SUI_CONFIG_DIR`, `MOVE_HOME` and `CARGO_NET_OFFLINE=true` environment documented above; `--build-env mainnet` is the unit-test compilation environment, with no chain execution. Full foreground outputs and exit codes are in ignored `.local/rs-map-gap-closure-batch-2/merge-verification/` scratch; the actual results are recorded here independently of those logs.

| Command actually run | Exit / actual result |
|---|---|
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_publicly_consumed_ticket_cannot_be_shielded` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui a_verifier_other_than_the_pinned_one_is_rejected` | 0: Test result: OK. Total tests: 1; passed: 1; failed: 0 |
| `/workspace/kix-run/wt/rs-4-l2/.local/bin/sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui` | 0: Test result: OK. Total tests: 260; passed: 260; failed: 0 |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0: Ran 173 tests in 4.859s; OK. Main adds six summary regressions to the earlier 167-test result. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 0: Ran 184 tests in 1.841s; OK. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 0: Ran 179 tests in 6.372s; OK. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 0: Ran 146 tests in 7.390s; OK. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults readiness.test_conformance_sensitivity` | 0: Ran 108 tests in 8.339s; OK; self-test: pass. In-process/loopback only. |
| `python3 scripts/check_docs_index.py` and `python3 scripts/check_docs_index.py --self-test` | Both 0: docs index ok: scanned=220 indexed=185 allowlisted=35; self-test: pass. |
| `python3 scripts/check_status_register.py` and `python3 scripts/check_status_register.py --self-test` | Both 0: capability register ok: paths=348 ev_ids=15 original32=32; self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` and `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Both 0: rows=23 citations=174; status counts 13/2/6/0/2 unchanged; self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` and `python3 scripts/check_rs_im_evidence_map.py --self-test` | Both 0: rows=30 citations=200; status counts 11/5/12/0/0/2 unchanged; self-test: pass. |
| `python3 .local/rs-map-gap-closure-batch-2/merge-verification/verify.py docs` | 0: all remaining 19 commands from the workflow's `Stdlib offline document checks` block passed, completing its 27 commands together with the eight above. |
| `git diff --check` and `git diff --cached --check` | Both 0: no whitespace errors. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` and per-file preservation checks | Both locked blobs match before/after: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`. All 108 tracked `reference/v0.3-rc1` files match HEAD; no untracked nonignored files there. |
| Tracked working-tree text scan for conflict markers; index/citation preservation assertions | 0: no markers; both sides' appended links occur exactly once; EV-RS cites this record; `.aiops/`, `docs/tasks/` and `.github/` have no diff from HEAD. |
| `git add -- docs/README.md` | Failed: Git's index is outside the writable worktree, so creation of `index.lock` failed with `Read-only file system`. No retry or permission change. The file content is resolved; the supervisor must stage it. |

The remaining 19 document commands are plain and `--self-test` calls to `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, `check_adapter_identity_map.py`, `check_v5_transition_evidence_map.py`, and `check_readiness_evidence_map.py`, plus `check_stage5_host.py --self-test`. Main's newer error-code table passes with 199 rows including BRA-RES9=10; its readiness map passes with 36 rows / 183 citations / EXERCISED=27 / PARTIAL=0 / OPEN=9. No CI workflow was edited, and Rust checks were not repeated for this documentation reconciliation.

No contract violation or new undefined behavior was found. All operational values, source-informed limitations and explicit non-claims above remain. No commit, abort, push, network action or external post was performed. The Git index still lists `docs/README.md` as unmerged solely because staging is unavailable in this sandbox. Final committed task/merge heads and exact-head KTX/KIX/post-merge CI run IDs/status/conclusions are unavailable; supervisor staging, commit and subsequent review/CI remain. Local READY denotes completed conflict resolution and passing local checks, not merge authorization or exact-head CI success.
