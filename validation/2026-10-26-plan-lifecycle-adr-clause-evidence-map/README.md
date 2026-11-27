# Lifecycle/ADR clause evidence map — local validation

Builder-authored record, not independent A2 review, acceptance, a grade change or merge readiness. READY means local delivery to the supervisor.

Node/task ID: `plan-plan-lifecycle-adr-clause-evidence-map`. Task input is the user-supplied node specification and read-only design plan; no issue and no current `docs/tasks/` document for this node. Branch: `agent/kix-plan-plan-lifecycle-adr-clause-evidence-map`.

Locally observed `origin/main`, initial task HEAD and delivery-time Git HEAD: `944cb16f3ade5a395c0febe84fd47d5c16dc0fa3`. There is no local base delta. These checks apply to the uncommitted working tree described below. No implementation commit or final delivery commit has been created: the supervisor owns git/GitHub publication. Remote freshness was not checked; `git fetch origin main` was not run because the final supervisor instruction prohibits every network action. No rebase, merge, branch operation, commit, push, issue, PR or comment was performed.

The [map](../../docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md) contains 27 rows: **6 COVERED, 17 PARTIAL, 1 NOT_COVERED, 3 OPEN**. This is the existing-coverage mapping required by AGENTS.md §7, with INV-1 through INV-5 tied to the kernel-only generated-history test. Every cited body was read. Existing examples/invariant checks and source-informed E4/v5 differential evidence use separate columns. E4's two citations are evidence-gate classification/sensitivity tests and are explicitly labelled as such. No Rust test was added or changed. The new evidence is the map plus a stdlib structural checker; its positive control and 49 negative fixtures address malformed/missing citations, non-test helpers, anchors, paths/provenance columns, statuses, INV/open-input ids, row set/counts, the I12 handoff stop, and raw-byte locked hashes.

Changed paths (complete submitted list):

- `.github/workflows/protocol.yml` — only two checker invocations in the existing stdlib document-check step.
- `docs/README.md` — one location bullet linking map and record.
- `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md` — new builder map.
- `scripts/check_lifecycle_adr_evidence_map.py` — new read-only stdlib checker.
- `validation/2026-10-26-plan-lifecycle-adr-clause-evidence-map/README.md` — this record.

Locked files were checked with `git hash-object` before editing and after implementation/testing; both matched each time. Self-test injects mutated bytes into an in-memory file dictionary and never mutates either actual file.

| File | Before | After |
|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | 69564b166f0c27f9af5d8422f0a466b18d74c20f |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | b607996c83a119c349f1cc90469ac1ba82764e20 |

Commands actually run, from repository root. Narrow checker tests preceded broader document and Rust verification. Cargo used `--offline` to honor the no-network instruction; dependencies were already available. Rust source is unchanged. Host versions observed: Python 3.13.5, rustc 1.98.1 (48a229cea), Cargo 1.98.1, Node v20.19.2.

| Command | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` | Both SHAs equal the base above; exit 0. |
| `git branch --show-current` | Expected task branch; exit 0. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs docs/contracts/STATE_LIFECYCLE.md docs/adr/0001-ktx-authority-commit-recovery.md` | Exit 0; locked pins match; current lifecycle blob 8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d and ADR blob 054bc714b3c475fb8536df8d2d788b42e8c74b6c. |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK. |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | First development run exit 1: the wrong-width fixture accidentally appended owner text without an extra cell. Fixed the fixture to insert a ninth cell; subsequent run exit 0: positive injected citation and 49 negative fixtures passed, memory only. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0: 78 tests passed, 0 failed/ignored. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --locked --offline` | Exit 0: 56 tests passed, 0 failed/ignored. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; no source mutation. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0: architecture v5 + KTX-R1 dependency gate OK; durability/performance not certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0: 7 tests passed. |
| `python3 scripts/check_openapi_contract.py` | Exit 0: 84 commands, core=40, FSM=44; source pins match. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0: pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0: 84 commands; productionEndpoint=false, publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0: pass. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0: 257 tests passed, 0 failed/ignored; doc-test targets also succeeded. Includes the two kernel crates above. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; all workspace crates/targets pass. Includes the planned kix-kernel Clippy scope. |
| `git diff --check` | Exit 0. |
| `git diff --name-only origin/main -- docs/contracts docs/adr docs/tasks reference/v0.3-rc1 .aiops runtime` | Exit 0, empty output; protected/source paths unchanged. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 after implementation/testing; both full pins match the table above. |
| `git status --short` and `git diff --stat` | Only the five submitted paths above; no other tracked change. |
| `python3 scripts/check_sdk_client.py` | Additional non-stdlib-only SDK check: exit 1 before generation, Node 20.19.2 does not match toolchains.json nodeMajor 24. |
| `python3 scripts/check_sdk_client.py --self-test` | Same Node toolchain guard, exit 1; no SDK/reference edits or installations made. |

The complete authoritative **Stdlib offline document checks** run block in protocol.yml was parsed and each command executed sequentially with Python subprocess (no shell background jobs): **39 commands, all exit 0**. The table below records every pair, without claiming the SDK/Node checker is stdlib-only.

| Commands | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. |
| `python3 scripts/check_docs_index.py` | Exit 0. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0. |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0. |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0. |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0. |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0. |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0. |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0. |

CI/publication evidence: exact-head KTX run ID/status/conclusion = **not queried / unavailable**; exact-head KIX protocol run ID/status/conclusion = **not queried / unavailable**. No final committed task head, PR, merge commit or post-merge main CI exists from this builder session. No earlier SHA's CI is transferred. Non-author exact-HEAD review and both required exact-head workflows remain supervisor follow-up before any merge proposal.

Deviations and limits:

- Fetch omitted under the explicit supervisor no-network rule; cached local origin/main is the observed base, not proof of current remote main.
- Conservative body-based status assignment: L2-UNBOUND, L3-PRESERVE, L3-CAPACITY and A6-EVENT-ECON are PARTIAL because the broader retention/chain/custody/provenance obligations have no contract-path assertions in the cited tests. The design left these statuses for the builder to assess. No row was promoted from an existing capability grade. PARTIAL and NOT_COVERED require named owners as an additional checker constraint consistent with the objective.
- Added `--offline` to Cargo. Broadened the planned per-kernel Clippy check to the CI workspace scope and ran the optional full workspace tests. No dependency/configuration change was needed.
- The additional SDK checks exposed a pre-existing host Node major mismatch, outside this node's touched paths and outside the authoritative stdlib step. Node 24 was not installed because network/toolchain provisioning is outside the task. Full protocol CI (SDK/Move/localnet/ZK/storage probes and hosted orchestration) was not reproduced. The required stdlib checks, both requested kernel suites and closest applicable Rust/architecture/OpenAPI equivalents passed.

Contract discrepancies: no explicit kernel contract violation identified. Characterizations: current STATE_LIFECYCLE/ADR blobs differ from the historical CONTRACT_INVARIANTS pins; the map records both versions without rewriting history. Fresh unbound observations remain unstored in the pure kernel, retained versus unretained conflicts differ, and future long-term identity/scope-closure semantics are undefined. These are labelled limits, not invented semantics.

I09–I13 remain open with their existing owners. In particular LC-CUT handoff is OPEN under I12; slot/review/reclaim/index stops remain unchanged. Future custody, independent cut proof/trust approval, and durable ACK require separately authorized work. No durability, distributed fencing, bank exactly-once, chain finality, legal compliance or production-readiness claim; no live provider/funds/Sui execution. No contracts, ADR, task inputs, reference/v0.3-rc1, .aiops, locked bytes, Rust tests or runtime sources changed.
