# Builder evidence: plan-plan-capital-companion-evidence-index

Task input: supervisor-supplied node specification and read-only design plan in
this session; no task issue or node document under `docs/tasks/`. This is not
ASTRA program mode. Existing task documents are unchanged. Coverage inventory
was recorded in the companion usage documentation before adding tests.

Baseline: branch `agent/kix-plan-plan-capital-companion-evidence-index`, initial
HEAD and cached `origin/main` both
`763c41b66ee9a7ba805d2fb0d3096d81a247b79f`. No local base delta. Per the explicit
supervisor prohibition on network actions, `git fetch origin main` was not run;
current remote main is unverified. No commits, pushes, PRs, issues or comments
are authorized. Final committed head and hosted CI belong to the supervisor.

Pre-edit kernel Git blobs match `69564b166f0c27f9af5d8422f0a466b18d74c20f`
and `b607996c83a119c349f1cc90469ac1ba82764e20`. A SHA-256 manifest of all existing
tracked regular files was captured outside the deliverables before editing.
Verification results will be recorded after foreground checks complete.

## Implementation and preserved bytes

Changed paths (complete delivery list):

- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/README.md`
- `validation/2026-11-18-plan-plan-capital-companion-evidence-index/README.md`

The JSON pins 15 distinct existing artifacts with raw-byte SHA-256 and Git-blob
hashes. It covers seven families, 379 associations, 87 supplemental observations,
and 12 supporting scenarios. The documentation contains the pre-change coverage
inventory, shape descriptions, limitations and a read-only inline Python example.
The seven new tests cover only navigation, pins, identities, references and
claim guards; the original replay suites retain economic behavior coverage.

Detached negative controls remove/duplicate/reorder packs, scenarios, cases and
setup/history entries; cross valid same-operation references; substitute another
valid pack pin; alter source bytes or digests; remove replay symbols/headings;
and promote qualification claims or omit limitations. Rehashed detached output
controls fail scenario/step/operation/target/complete-envelope checks, independently
of digest matching. Rehashed self-contained refusal controls fail exact case
membership. Duplicate JSON keys, non-finite JSON and invalid pointers are rejected.
Omitted keywords, nulls, booleans and floats remain distinct.

Before/after SHA-256 comparison of all 4,222 pre-existing tracked regular files
found exactly one changed original path: `docs/README.md`. Thus every original
pack, producer, observer, replay module, contract, field guide, `.aiops/` file,
task document, workflow and all 108 `reference/v0.3-rc1/` files are byte-identical.
Both kernel Git blobs match before and after:

| Locked path | Git blob before/after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

No locked source was edited, formatted or transiently mutated. Injected checker
self-test bytes and temporary architecture-test trees do not alter repository
sources. Final merge checks are inapplicable.

## Actual local verification

Commands ran in the foreground; no shell background jobs or automatic retries.
Python versions: `python3` 3.13.5 and `python3.12` 3.12.15 (CI version family).
Rust and Cargo: 1.98.1. No dependencies were fetched. Rust invocations used
`RUSTUP_OFFLINE=1 CARGO_NET_OFFLINE=true`; test/Clippy/tree also used `--offline`.
One-time builder helpers in `/tmp/` assembled this new index and fixed inventory
only; they did not write or regenerate any existing vector. They are not a new
repository CLI or client. All completed verification invocations passed on their
first run; there were no test failures or corrective changes.

| Command actually run | Actual result |
| --- | --- |
| `python3 -B /tmp/build_capital_index_constants.py` | Wrote fixed family/path/identity inventory in the new test module only. |
| `python3 -B /tmp/build_capital_companion_index.py` | Wrote new JSON index; validated 379 associations, with family counts 98/54/51/53/63/27/33 and observation counts 0/0/0/31/37/8/11. |
| `python3 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_capital_companion_evidence_index.py` | 7 tests passed. |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_capital_companion_evidence_index.py` | 7 tests passed. |
| `python3 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 284 tests passed, including all seven replay suites and both supporting observer suites. |
| Documented read-only Python example extracted from the new Markdown, via `python3 -B -` | SHA-256 verified; printed `V01_tolerance_omitted`, `{}`, and `VarianceObservationError/TOLERANCE_REQUIRED`. |
| `python3 -B /tmp/run_capital_document_checks.py` | Ran all 67 actual commands in protocol.yml's Stdlib offline document checks block; every exit code 0. Expanded checker list below. |
| `python3 -B scripts/check_openapi_contract.py` and same with `--self-test` | Both passed. |
| `python3 -B scripts/check_integration_gate_openapi.py` and same with `--self-test` | Both passed. |
| `python3 -B scripts/check_sdk_client.py` and same with `--self-test` | Both passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 9 tests passed. |
| `python3 -B scripts/verify_runtime_architecture.py` | Architecture/dependency gate passed; no durability/performance certification. |
| `python3 -B scripts/test_runtime_architecture.py` | 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 139 passed, 0 failed; 9 targets including empty unit/doc-test targets. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed (check only). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 339 passed, 0 failed, 1 ignored across 48 targets. The existing ignored CPU/SQL engine acceptance test requires the owner-provisioned offline bundle and explicit engine features; no engine acceptance is claimed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Passed; only `kix-types` normal dependency. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before/after | Both locks match; hashes above. |
| Inline Python SHA-256 comparison against pre-edit manifest (`python3 -B -`) | 4,221 original files preserved; only existing `docs/README.md` changed; all 108 historical reference files preserved. |
| `git diff --check` | Passed. |

Every path below was invoked as `python3 -B <path>` and also with
`--self-test`, except `check_stage5_host.py` (self-test only, matching CI).
This expands the 67-command document-check run without claiming any unrun host
qualification. The loopback preflight probes local sockets only and selects no
host or public endpoint.

| Checker path | Actual result |
| --- | --- |
| `scripts/check_status_register.py` | Normal and self-test passed. |
| `scripts/check_producer_qualification_tuple.py` | Normal and self-test passed. |
| `validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | Normal and self-test passed. |
| `scripts/check_rs_profile_traceability.py` | Normal and self-test passed. |
| `scripts/check_read_model_source_map.py` | Normal and self-test passed. |
| `scripts/check_docs_index.py` | Normal and self-test passed. |
| `scripts/check_i12_proof_ids.py` | Normal and self-test passed. |
| `scripts/check_delegation_layer_matrix.py` | Normal and self-test passed. |
| `scripts/check_rs_predicate_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_rs_im_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_tl_predicate_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_contract_error_codes.py` | Normal and self-test passed. |
| `scripts/check_adapter_identity_map.py` | Normal and self-test passed. |
| `scripts/check_v5_transition_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_readiness_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_settlement_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_bra_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_credit_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_primary_price_fee_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_ai_delegation_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_lifecycle_adr_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_contract_invariants_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_toss_card_profile_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_bcs1_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_performance_measurement_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_feature_semantics_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_integration_gate_contract_evidence_map.py` | Normal and self-test passed. |
| `scripts/check_evidence_map_rollup.py` | Normal and self-test passed. |
| `scripts/check_class_b_index.py` | Normal and self-test passed. |
| `scripts/check_ci_checker_wiring.py` | Normal and self-test passed. |
| `scripts/check_ci_test_discovery.py` | Normal and self-test passed. |
| `scripts/check_loopback_host.py` | Normal and self-test passed. |
| `scripts/check_cargo_offline_cache.py` | Normal and self-test passed. |
| `scripts/check_stage5_host.py` | Self-test passed. |

The protocol workflow's eight-suite loop ran with `PYTHONDONTWRITEBYTECODE=1`
and Python 3.12, after the narrow tests. These are the actual expanded commands,
all exit 0 (2,319 tests total):

| Command | Actual result |
| --- | --- |
| `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 224 tests passed. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 1,032 tests passed. |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 284 tests passed, including the focused index tests, seven pack replays and both supporting observer suites. |
| `python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | 169 tests passed. |
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | 397 tests passed. |
| `python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | 86 tests passed. |
| `python3.12 -B -m unittest discover -s reference/payment_effects -t reference/payment_effects` | 28 tests passed. |
| `python3.12 -B -m unittest discover -s reference/economics -t reference/economics` | 99 tests passed. |

## Deviations, non-claims and remaining gates

No semantic design deviation. An explicit `observations` array stores the
planned supplemental snapshots/restore references; it adds no input commands.
The field guide resolves to `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`.
There is no node-specific task document; the supervisor's supplied node/design
is the immutable task input. No issue or `.aiops/` entry was created or edited.
The supervisor's no-network rule overrides AGENTS.md's initial fetch requirement;
only cached `origin/main` was observed. Offline Rust checks and CI-family Python
3.12 avoid downloads and confirm local interpreter compatibility.

No explicit contract violations or new contract-undefined behaviors were found.
Existing source-informed Class B characterizations, frozen-face semantics,
separate refund obligations, shared-exposure limits, `NOT_BOUND` and `repair=NONE`
are retained without promoting evidence. External Capital acceptance remains
**UNVERIFIED**; product limits **UNDETERMINED—Astra**; legal responsibility
**UNDETERMINED—User/legal**. No external consumer, real provider, funds, chain,
production runtime, storage engine, new coin/TIX, secret or policy value was used.
The existing default-workspace ignored CPU/SQL engine acceptance check was not
enabled. Sui/Move/ZK ceremonies, chain journeys, SDK npm conformance and production
or storage probes were not run: this node changes local JSON/Python discovery and
documentation only. The applicable offline reference, document, architecture and
Rust verification paths passed; this is not a claim of full hosted protocol CI.

| Delivery evidence | Status |
| --- | --- |
| Observed cached `origin/main` / initial branch HEAD | `763c41b66ee9a7ba805d2fb0d3096d81a247b79f` / same; no local delta; remote freshness unverified. |
| Implementation/final local HEAD | Same baseline SHA; implementation is an uncommitted worktree patch by supervisor instruction. No committed final task SHA exists in this session. |
| Exact-head KTX CI run ID/status/conclusion | Not obtained/not run; supervisor-owned after commit. No older result is transferred. |
| Exact-head KIX protocol CI run ID/status/conclusion | Not obtained/not run; supervisor-owned after commit. |
| A2 non-author exact-head review | Pending supervisor delivery; author validation is not independent review. |
| PR/merge SHA and post-merge CI | Not applicable; no publication or merge performed. |
| Final-merge locked blobs | Not applicable; no merge. |

Remaining work outside this builder session: supervisor commit/publication,
non-author A2 review, exact-head KTX/KIX CI, and any authorized post-merge checks.
The local patch is ready for that handoff; no merge-ready or production-ready
claim is made. User-only merge authorization remains unchanged.

After completing this record, `python3 -B scripts/check_docs_index.py` and its
`--self-test`, `python3 -B scripts/check_ci_checker_wiring.py`, and
`python3 -B scripts/check_ci_test_discovery.py` were deliberately rerun for the
final documentation/discovery state; all passed. No Python/index content changed
after the successful focused and full suite runs.
