# audit29-consumer-surface-boundary-map — builder validation

## Task and basis

Task ID: `audit29-consumer-surface-boundary-map`; supervisor-supplied node
specification and read-only design plan in the builder prompt. No issue was
created and no corresponding task document exists under `docs/tasks/`.
Source: external `/workspace/kix-run/audits/audit_29_20261110.md`, finding 2.
This is not ASTRA program mode. Audit floor A2; no Astra gate; no merge authority.

Observed cached `origin/main`, base and starting/task HEAD:
`508c65e690a8eaf035bfc282f263f3198c103600`.
Branch: `agent/kix-audit29-consumer-surface-boundary-map`.
No local base delta. `git fetch origin main` was NOT_RUN because the supervisor
explicitly prohibits network/GitHub actions; remote freshness remains unverified.
Implementation/final delivery head: unavailable (supervisor owns commits).
Merge commit/post-merge checks: not applicable; no merge performed.

The [inventory](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md) is
builder-authored and non-normative. No independent review or qualification PASS.

## Complete changed-path list

- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md` — single consolidated inventory.
- `docs/README.md` — inventory and validation entry.
- `docs/contracts/openapi/README.md` — interface-boundary navigation.
- `sdk/README.md` — navigation beside BOOTSTRAP/semantic HOLD.
- `reference/booking_resale_admission/README.md` — ticket and calculator links.
- `reference/token_reward/README.md` — token-tool entry-point link.
- `validation/2026-11-10-audit29-consumer-surface-boundary-map/README.md` — this record.

## Existing coverage mapped before editing

| Requirement | Coverage classification | Reused evidence / gap addressed |
|---|---|---|
| Cited boundaries and prerequisites for every surface | Partially covered | Individual guides/contracts/dispatchers existed; consolidated navigation was missing. New inventory adds no behavior. Citation/fragment and field review checks the documentation gap. |
| HTTP/calculator/ticket namespaces remain separate | Sufficient behavioral coverage | `integration_gate/test_http_gate.py::test_fsm_idempotency_key_replays_without_using_operation_id` and `test_http_idempotency_key_header_is_not_consulted`; `reference/booking_resale_admission/test_commerce_calculation_client.py`; `test_ticket_operations_session.py`. |
| Pool references append again, without deduplication | Sufficiently covered | `reference/token_reward/test_pool_session.py::PoolSessionTests.test_repeated_refs_match_direct_model_and_append_again` checks direct-model parity and second effects. |
| Synthetic observations cannot be treated as authenticated facts | Partially covered | Existing reward/source/supply tests and authority contracts establish local predicates and false non-claim flags. They cannot establish authentication; the map explicitly preserves that limit. |
| Missing bindings remain NOT_BOUND/HOLD | Partially covered | Read-model source map/candidate vectors, SDK profile/checks and SD1 record preserve existing limits. Independent semantic consumer qualification remains unavailable. |
| Discoverable single inventory | Previously not covered | New index entry and guide backlinks, existing `check_docs_index.py`, manual citation/anchor review. |

No new tests, generators, schemas, helpers or runtime code. Existing deterministic
tests already cover the relevant behavior; the missing artifact was documentation.

## Commands and actual results

The commands below were executed in this worktree. Python tests use
`PYTHONDONTWRITEBYTECODE=1`; existing Python 3.12.15, Node v24.22.1 and Rust
1.98.1 are available. Cargo is kept offline to honor the no-network rule.
No dependencies are bootstrapped and no protected assets are regenerated.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initial worktree clean; matching SHA/branch above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before: both required blobs match (see preservation below). |
| Python SHA-256 snapshot of both locked files and every file under `reference/v0.3-rc1/` | Saved before edits to `/tmp/audit29-boundary-protected-before.json`. |
| In `reference/booking_resale_admission`: `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest test_ticket_operations_session test_commerce_calculation_client` | PASS: 15 tests. |
| In `reference/token_reward`: `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest test_reward_session test_pool_session test_supply_reconciliation test_collateral_assessment` | PASS: 23 tests. |

## Preservation, limitations and delivery gates

Required locked blobs before edits:

| Path | Required / observed before |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

After work: both blob hashes still match; all 110 protected files (the two
kernel files and 108 files under `reference/v0.3-rc1/`) match the pre-edit
SHA-256 snapshot, with no additions/deletions in that subtree. Its baseline Git
tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
`git diff --exit-code HEAD --` on protected paths also passed. No final
merge verification applies in this session. `.aiops/`, `docs/tasks/`, generated
SDK/catalogue files, CI and historical validation records are outside the patch.

Known explicit contract violation: SD1, verifier order, remains blocked with User
at [the existing record](../../docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md).
This task documents it and does not reopen its diagnostic or resolve/waive it.
Existing Class B ticket clock-skew/post-mutation faults and reward
restore/fingerprint/late-failure characterizations remain as cited in the map.
No new contract violation or undefined semantics is introduced by this patch.

Exact-head KTX CI run ID/status/conclusion: **NOT_RUN / unavailable**.
Exact-head KIX protocol CI run ID/status/conclusion: **NOT_RUN / unavailable**.
Post-merge main CI: **not applicable**. No non-author exact-final-head A2 review
has been obtained by this builder. Local checks do not replace these delivery gates.

Deviations: use supplied node input instead of a nonexistent task document; fetch
omitted under the no-network rule. Per-surface two-column tables keep the planned
inventory fields readable. The OpenAPI backlink is appended after its existing
content to preserve line-numbered evidence anchors; the initial insertion
shifted G20/G21 in the source-map checker and was corrected without editing
the evidence map or checker. Rust compilation/Clippy/dependency evidence is
unavailable because the offline cache lacks `bcs`; no packages were fetched. No design scope change, product policy choice,
finance architecture adoption or qualification promotion.

No real funds/provider calls, public endpoint, Sui testnet/mainnet, production
runtime, new coin/TIX, storage/replication/consensus engine or credentials.
No durability, distributed fencing, bank exactly-once, chain finality, legal
compliance, production readiness or protocol-completeness claim.
Consumer repositories and separate Capital ownership are unverified. Follow-up
requires owner decisions for existing blockers, publication/qualification of
missing bindings, and supervisor-owned commit/review/CI; none is completed here.

## Documentation checks and source review

The entire `Stdlib offline document checks` block of
`.github/workflows/protocol.yml` was executed, plus OpenAPI and SDK checks.
Each table row's command was run both as printed and with ` --self-test`
appended, except `check_stage5_host.py`, whose workflow invokes only self-test.
PASS means exit 0; host/cache reports have the narrower meaning stated below.

| Command | Plain result | With `--self-test` |
|---|---|---|
| `python3.12 -B scripts/check_docs_index.py` | PASS | PASS |
| `python3.12 -B scripts/check_status_register.py` | PASS | PASS |
| `python3.12 -B scripts/check_read_model_source_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_openapi_contract.py` | PASS | PASS |
| `python3.12 -B scripts/check_integration_gate_openapi.py` | PASS | PASS |
| `python3.12 -B scripts/check_sdk_client.py` | PASS | PASS |
| `python3.12 -B scripts/check_rs_profile_traceability.py` | PASS | PASS |
| `python3.12 -B scripts/check_i12_proof_ids.py` | PASS | PASS |
| `python3.12 -B scripts/check_delegation_layer_matrix.py` | PASS | PASS |
| `python3.12 -B scripts/check_rs_predicate_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_rs_im_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_tl_predicate_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_contract_error_codes.py` | PASS | PASS |
| `python3.12 -B scripts/check_adapter_identity_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_v5_transition_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_readiness_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_settlement_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_bra_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_credit_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_primary_price_fee_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_ai_delegation_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_lifecycle_adr_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_contract_invariants_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_toss_card_profile_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_bcs1_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_performance_measurement_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_feature_semantics_evidence_map.py` | PASS | PASS |
| `python3.12 -B scripts/check_evidence_map_rollup.py` | PASS | PASS |
| `python3.12 -B scripts/check_class_b_index.py` | PASS | PASS |
| `python3.12 -B scripts/check_ci_checker_wiring.py` | PASS | PASS |
| `python3.12 -B scripts/check_ci_test_discovery.py` | PASS | PASS |
| `python3.12 -B scripts/check_loopback_host.py` | PASS | PASS |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | PASS | PASS |
| `python3.12 -B scripts/check_stage5_host.py` | NOT_RUN (workflow self-test only) | PASS |

Initial `check_read_model_source_map.py` and its `--self-test` both exited 1:
`G20`/`G21` reported shifted `FIXTURE_ONLY` line anchors in the OpenAPI README
(tokens moved from 52/70 to 57/75). Moving the new backlink to the end restored
both anchors. Both commands were rerun explicitly and exited 0; normal output:
`queries=13 anchors=128 catalogues=2 citations=145`; self-test: `pass`.
No checker, contract pin or source-map anchor was altered.

`check_loopback_host.py` reported `all_ok=true` for in-process and child probes.
`check_cargo_offline_cache.py` exits 0 as an inspection tool; it reported 7/18
archives present and 11 missing (including `bcs` 0.2.1). That exit is **not**
a claim that offline Rust compilation is available. Stage-5 host self-test
checks the probe logic only and does not qualify a host.

| Review command | Actual result |
|---|---|
| `python3.12 -B /tmp/audit29-review-links.py` | PASS: 96 local links, 13 fragments and all five guide/index backlinks; checks both new Markdown files and added links in existing guides. |
| `python3.12 -B -` (inline JSON/AST citation inspection) | PASS: exactly 40 core + 44 FSM actions; both admission example actions exist; all 7 named test citations exist. |
| Source/contract/dispatcher reading and manual comparison | All seven surface groups reviewed for envelope, namespace, identity/replay, setup, authority, qualification and missing bindings. No new auth/qualification claim; existing SD1 retained. |

The temporary review script resolves local link targets, derives heading slugs,
checks every cited fragment in the new inventory and checks inventory backlinks
in each modified guide. It is validation scaffolding under `/tmp`, not a new
repository checker, generator or conformance test. Temporary runner/results/logs
are also under `/tmp/audit29-*`; durable command/results are recorded here.

## Broader local workflow equivalents

All following commands ran from repository root with
`PYTHONDONTWRITEBYTECODE=1` and `CARGO_NET_OFFLINE=true`. The six reference
suite commands use the protocol workflow's suite list. They follow the focused
38-test run above and preserve existing source-informed evidence limits.

| Command | Actual result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0) |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0); Ran 7 tests in 0.237s |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | UNAVAILABLE (exit 101 before test/lint/tree execution): offline resolver cannot find `bcs`, required by workspace member `kix-bcs1` |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | UNAVAILABLE (exit 101 before test/lint/tree execution): offline resolver cannot find `bcs`, required by workspace member `kix-bcs1` |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | UNAVAILABLE (exit 101 before test/lint/tree execution): offline resolver cannot find `bcs`, required by workspace member `kix-bcs1` |
| `python3.12 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS (exit 0); Ran 139 tests in 7.506s |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | PASS (exit 0); Ran 9 tests in 0.243s |
| `npm --prefix sdk run conformance` | PASS (exit 0); 6 tests passed |
| `npm --prefix sdk run verify-compat` | PASS (exit 0); `ok=true`, `profile_kind=BOOTSTRAP`, `profile_revision=bootstrap-2` |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0); Ran 924 tests in 170.158s |
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0); Ran 382 tests in 58.113s |
| `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0); Ran 224 tests in 1.880s |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS (exit 0); Ran 183 tests in 11.542s |
| `python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS (exit 0); Ran 149 tests in 10.219s |
| `python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS (exit 0); Ran 86 tests in 12.769s |

Reference suites: **1,948 tests passed** across the six suites; the focused
38 tests overlap those suites and are not additional unique coverage. HTTP/
readiness: 139; offline limits: 9; architecture regressions: 7; SDK: 6.
These are local test counts, not independent semantic conformance.

Full Rust workspace test/Clippy: **NOT_RUN** after the kernel commands failed
at shared workspace dependency resolution; no automatic retry or package
bootstrap. Full protocol Move/localnet/ZK/storage-provider stages: **NOT_RUN**;
this is the closest practical documentation/interface verification, not a full
protocol CI run. No protected fixture/proving assets were regenerated to obtain
a pass. Supervisor-owned exact-head CI remains required.

## Final worktree verification

| Command | Actual result |
|---|---|
| `python3.12 -B /tmp/audit29-verify-preservation.py` | PASS: before/after SHA-256 equality of all 110 protected files, unchanged file set, both required Git blobs, protected tracked-path diff clean, exactly seven authorized Markdown outputs. |
| `git diff --check` | PASS; no whitespace errors. |
| `git rev-parse HEAD origin/main` | Both remain `508c65e690a8eaf035bfc282f263f3198c103600`; no commit/push performed. |

The preservation script compares every pre-edit protected path and SHA-256,
checks the frozen-reference file set, computes both required blobs with
`git hash-object`, compares protected tracked paths against HEAD, and compares
changed/untracked paths with the seven-file allowlist above. Protected-path
comparison covers `.aiops/`, `docs/tasks/`, `.github/`, SDK generated/compatibility
assets and the frozen reference tree in addition to the two kernel files.

Builder handoff: **READY**, with Rust dependency checks unavailable and
non-author exact-final-head A2 review / exact-head KTX and KIX CI still pending.
This does not resolve SD1 or authorize merge.
