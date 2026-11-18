# S5 residual characterizations and F-B1 provenance pin

Task ID: `plan-plan-contract-invariants-s5-residual-cha`. Date: 2026-10-28.
Task document: the supervisor-supplied node specification and read-only design
plan in the executing session; no issue, corresponding `docs/tasks/` document
or `.aiops/program.json` entry exists for this loop-proposed node. No task input
was created or changed. This is not ASTRA program mode. Builder-authored evidence,
not non-author A2 review, final-head hosted CI or merge readiness.

Branch: `agent/kix-plan-plan-contract-invariants-s5-residual-cha`.
Observed cached `origin/main`, task base and initial/unchanged HEAD:
`7438bf7c74d4398a19061a701baeec6899e94e86`. No local base delta.
Fetch is NOT_RUN because the supervisor prohibits network actions; remote
freshness is unverified. Dependencies are present in this base: the seven S5
availability examples and nineteen S5 precedence examples in `contract_edge_cases.rs`.
Implementation is the uncommitted working-tree patch. There is no final committed
implementation/task head, merge SHA, KTX/KIX exact-head run ID/status/conclusion,
or post-merge main CI. Publication, non-author A2 review and exact-head hosted CI
belong to the supervisor. No old CI is attributed to this patch.

Complete changed paths:

- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
- `scripts/check_contract_invariants_evidence_map.py`
- `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md`
- `docs/status/CLASS_B_CHARACTERIZATION_INDEX.md`
- `docs/README.md`
- `validation/2026-10-28-plan-contract-invariants-s5-residual-cha/README.md`

## Existing coverage first and residual matrix

Classification was made before adding tests. Rust paths below are relative to
`runtime/crates/kix-kernel/tests/`. All five new test functions are in
`contract_edge_cases.rs`; they use public APIs, supplied deterministic times and
identities, observable orders/counters and whole-kernel Eq for read-only replay
and ordinary errors. No model/generator is imported and no kernel is mutated
outside its public API. The author read the locked source: no clean-room claim.

AGENTS §8 class B: observed locked-v4 behavior, not required semantics or availability guarantees.
The named contract boundary is CONTRACT_INVARIANTS §5. Behavior remains undefined
as required semantics; owner: kernel contract owner/non-author A2 reviewer.

| Finding/item | Existing coverage | Test citation | Observed result | Remaining uncertainty | Owner |
|---|---|---|---|---|---|
| F-B5(a), cancelled identity reuse | Partially covered: `contract_edge_cases.rs::altered_payload_conflicts_after_local_cancellation` pins conflict/replay, not fresh old-order/operation attempts at epoch 2 on seats/GA | `contract_edge_cases.rs::class_b_cancelled_identity_reuse_remains_fenced` | Identical command replays Held read-only; changed epoch on the same identity conflicts; fresh command reusing old order or operation at epoch 2 records BusinessFenced, allocates no new inventory and replays immutably | No cancellation reopening semantics or general availability decided | Kernel contract owner/non-author A2 reviewer |
| F-B5(b), late capture release then reuse | Not covered for this sequence. `expiry_instant_is_treated_consistently_by_every_entry_point`, `return_required_is_stable_under_further_late_evidence` and `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot` pin late capture/release, but no fresh owner taking the released inventory | `contract_edge_cases.rs::class_b_return_required_inventory_is_reusable` | Seats and GA, starting Held and PaymentUnknown, without expire: matching late capture gives ReturnRequired, retains captured amount, releases units and converts a reserved slot to stored evidence when present. Old-order reuse gives OrderExists; old-operation reuse gives OperationAlreadyBound. Fresh identities take the units; a new duplicate event preserves the old capture and new owner; original Held result still replays | Finite synthetic histories; no lifecycle-release API or external fact verification | Kernel contract owner/non-author A2 reviewer |
| F-B5(c), bundle value and scope | Partially covered: `contract_edge_cases.rs::free_contiguous_range_inside_one_actual_segment_is_held` accepts MAX_BUNDLE; `transitions.rs::overflow_empty_and_oversize_selections_fail_without_inventory_change` rejects MAX_BUNDLE+1 as InvalidRequest | `contract_edge_cases.rs::class_b_bundle_limit_value_and_ga_scope` | MAX_BUNDLE == 64, GA with 65 available admits 65 | Not a required product limit or arbitrary bundle/selection semantics | Kernel contract owner/non-author A2 reviewer |
| F-B5(c), inclusive command/order counts | Partially covered: `contract_edge_cases.rs::last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection`, `transitions.rs::bounded_records_backpressure_without_evicting_old_results` combine record limits | `contract_edge_cases.rs::class_b_command_and_order_limits_are_independent` | Independently vary command or order limit to 1 and 2 on seats/GA, leaving other budgets available; exactly that count is Held; next free/unavailable request gives unchanged-state Capacity and old results replay, also after cancellation | Other limit values/histories and private command-map allocation unmeasured | Kernel contract owner/non-author A2 reviewer |
| F-B5(c), observation count and reserved conversion | Sufficiently covered; no duplicate limit test | `observation_slots.rs::repeated_unknown_reserves_once_and_other_operation_cannot_take_slot`; `observation_slots.rs::unrelated_event_flood_cannot_starve_promised_capture` | Exact observation capacity and reserved-to-stored conversion already asserted; new ReturnRequired sequence also checks conversion | General budget combinations untested | Kernel contract owner/non-author A2 reviewer |
| F-B5(d), unrelated rejection variants and cross-kind selections | Sufficiently covered; no duplicate variant suite | `contract_edge_cases.rs::success_follows_unrelated_rejections_errors_and_replays` through `success_after_noise` | OrderExists, OperationAlreadyBound, InvalidRequest (including GA-on-seats and seats-on-GA), CommandConflict, ClockRegression, ExecutionFenced, UnsupportedSemantics and WrongScope already pinned; success still follows | Exact variants remain characterizations, not a complete taxonomy | Kernel contract owner/non-author A2 reviewer |
| F-B6, full-order-only versus unavailable/cancellation | Partially covered: previous precedence matrix rows 15/23 documented observations but had no dedicated assertion | `contract_edge_cases.rs::class_b_command_and_order_limits_are_independent` | Full orders alone gives unchanged-state Capacity over Unavailable and over cancellation even at current epoch 2; twins show available admission and Unavailable with spare record capacity | Other record/budget combinations and triples untested | Kernel contract owner/non-author A2 reviewer |
| F-B6, unavailable versus quarantine/UNKNOWN-bound operation | Not covered by a dedicated pair test; previous matrix rows 26/27 documented observations | `contract_edge_cases.rs::class_b_unavailable_selection_preserves_observed_rejection_precedence` | OperationQuarantined and OperationAlreadyBound win respectively, on seats/GA; twins establish unavailable alone and operation guard with free selection; old orders, capture and UNKNOWN slot preserved | Other guard sub-pairs and full precedence remain undefined | Kernel contract owner/non-author A2 reviewer |
| F-B1, three document blob pairs | Partially covered by prose/manual hashes, not automated current pin | `scripts/check_contract_invariants_evidence_map.py::self_test` | Recompute raw-byte Git blob SHA-1; require exact L/A/R IDs and paths, compare historical rows against Contract §2, compare current rows against bytes and require historical/current inequality. Missing inputs, changed bytes for each file, wrong hashes, wrong paths, malformed hashes and duplicate/missing rows are memory-only negative fixtures | Provenance only, no Rust semantic assertion or historical CI transfer | Contract owner |

F-B6 items remaining unexercised **by this node** (earlier observations and tests
remain historical evidence; this list does not erase existing coverage):

- Payload conflict with another version or foreign scope; version versus stale
  fence, regressed time, full records/budget or unbound operation; foreign scope
  versus cancellation, stale fence, regressed time, full command records,
  unavailable inventory or quarantine.
- Stale execution fence versus regressed time, full records/budget or unbound
  operation; regressed time versus cancelled send, full command records/full
  observation budget, reviewed send, UNKNOWN retry after deadline or unbound capture.
- Cancellation versus unavailable inventory or quarantine on reserve; cancelled
  Held send at full budget, cancelled UNKNOWN retry, cancelled reviewed send,
  cancelled unreserved capture at full budget; reviewed send at full budget;
  unbound capture at full budget.
- Other entry-point combinations, send-budget combinations, compound selections,
  three-or-more simultaneous guards, general availability and independent oracle
  interpretation. Required semantics for every class B observation remain open.

F-B5 has finite observed examples for all four listed groups now; reopening after
cancellation, broader ReturnRequired histories (mismatch/review/cancellation and
all evidence-capacity combinations), arbitrary bundle shapes/limits and complete
variant/precedence semantics remain unexercised or undecided.

## Provenance, maps and protected bytes

The invariants map retains its seven-column schema and all statuses/owners.
S2-ANCHORS stays NOT_COVERED under its Rust-test vocabulary while its gap explains
the stdlib provenance check. S5 rows stay PARTIAL. The recomputed count and unchanged
rollup copy are `rows=27 COVERED=10 PARTIAL=12 NOT_COVERED=3 OPEN=2`.
CB-005/CB-009/CB-010 have synchronized verbatim quotes and checker/test citations;
CB-217 indexes this record. Recomputed index counts:
`rows=217 validation=203 evidence_map=14 test_cited=33 owner_named=14 superseded=0`.
Historical validation records are unchanged.

Before work, raw-byte Git blob SHA-1 checks gave:

| Path | Required/current blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `docs/contracts/STATE_LIFECYCLE.md` | `8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d` |
| `docs/adr/0001-ktx-authority-commit-recovery.md` | `054bc714b3c475fb8536df8d2d788b42e8c74b6c` |
| `runtime/crates/kix-kernel/README.md` | `788896ed3e00bae3d06d26b7e2ce999a00ff1029` |

The two locks, three documents and all 108 files under `reference/v0.3-rc1/`
were inventoried in `/tmp/kix-residual-protected-before.json` using
`sha1(b"blob " + decimal_length + b"\0" + raw_bytes)` before editing.
Final comparison is recorded in the evidence table below. No locked file was
formatted or temporarily modified; rustfmt was applied only to the changed test.

## Actual local verification

Rust commands run in `runtime/`, Rust 1.98.1, with existing offline dependencies.
Root stdlib commands run in the repository root. Closest touched-path equivalents
were selected after inspecting `.github/workflows/ktx-kernel.yml` and the Rust
and stdlib steps in `.github/workflows/protocol.yml`. The full hosted protocol
workflow (ZK/Move, paid-storage/history probes and external setup) was not run.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; both SHAs and branch as recorded above |
| Raw-byte Python protected inventory (two locks, three documents, 108 reference files) | Initial locks/current document blobs match the table; snapshot saved outside repository |
| `cargo fmt --all -- --check` (repository root, initial invocation) | Exit 1: no Cargo.toml at root; corrected to runtime workspace below |
| `rustc --version`; `rustfmt --edition 2024 crates/kix-kernel/tests/contract_edge_cases.rs` | Rust 1.98.1; targeted formatting exit 0 |
| `cargo test -p kix-kernel --test contract_edge_cases --locked --offline` | Exit 0; 39 passed including all five new tests |
| `cargo test -p kix-kernel --locked --offline` | Exit 0; 132 passed, 0 failed/ignored across 9 result groups; includes existing Git-based identity diagnostics |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; 27 rows, corpus, anchors, symbols, counts, locked blobs and F-B1 pins OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; 2 positive controls and 97 negative fixtures OK, memory only |

Additional actual results (workspace run before the final module-documentation
wording adjustment; kernel crate rerun afterwards; behavioral code unchanged):

| Command | Actual result |
|---|---|
| `cargo test --workspace --locked --offline` | Exit 0; 332 passed, 0 failed/ignored across 46 result groups |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo fmt --all -- --check` (runtime workspace) | Exit 0 |
| `cargo tree -p kix-kernel --edges normal --locked --offline` | Exit 0; only normal dependency is kix-types |
| `cargo test -p kix-kernel --locked --offline` (final module-doc wording) | Exit 0; 132 passed, 0 failed/ignored across 9 result groups |
| `python3 scripts/check_class_b_index.py` (initial synchronization) | Exit 1: stale ADR §7 citation absent from revised source prose; restored the boundary reference, then rerun exit 0 |
| Final raw-byte Python comparison with `/tmp/kix-residual-protected-before.json`, including reference path-set equality | Exit 0; both locked blobs, all three F-B1 documents and all 108 reference files unchanged; no added/deleted reference files |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/README.md runtime/crates/kix-kernel/tests/support runtime/crates/kix-kernel/tests/e4_state_model.rs docs/contracts docs/adr docs/tasks docs/status/EVIDENCE_MAP_ROLLUP.md .aiops .github` | Exit 0; empty protected-path diff |
| `git ls-files --others --exclude-standard -- reference/v0.3-rc1` | Exit 0; empty output |
| `git diff --check` | Exit 0 |

All 63 Python commands from the workflow's authoritative `Stdlib offline document
checks` run block ran sequentially, followed by the two runtime architecture
commands. All 65 exited 0. Loopback preflight reported all_ok=true on 127.0.0.1;
this is local runner context, not a host selection or public endpoint. Plain
stage-5 host evaluation is intentionally not in the workflow list; its memory-only
self-test ran. The actual expanded commands and exits follow.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0 |
| `python3 scripts/check_docs_index.py` | Exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0 |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0 |
| `python3 scripts/check_class_b_index.py` | Exit 0 |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0 |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0 |
| `python3 scripts/check_loopback_host.py` | Exit 0 |
| `python3 scripts/check_loopback_host.py --self-test` | Exit 0 |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0 |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0 |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0 |
| `python3 scripts/test_runtime_architecture.py` | Exit 0 |

Detailed local logs are outside the repository: `/tmp/kix-residual-kernel.log`,
`/tmp/kix-residual-kernel-final.log`, `/tmp/kix-residual-workspace.log`,
`/tmp/kix-residual-clippy.log`, `/tmp/kix-residual-stdlib-results.json`.
Counts above were summed from actual successful Cargo result lines, including
doc-test groups (zero-test groups contribute zero). All jobs ran as foreground
commands; no long job was launched in the background.


## Deviations and non-claims

The no-network supervisor instruction overrides AGENTS §1 fetch; no fetch was
attempted. Read-only local Git diagnostics are permitted by the actual builder
instruction, so the existing Git-based source identity tests run normally. No
commit, push, PR/issue/comment, ready transition, tag/branch mutation or merge was
performed. The task document is the supplied specification; none was invented
under `docs/tasks/`. One root formatting invocation used the wrong directory and
was corrected; no formatting mutation occurred on that failure. The initial class-B
index check caught an ADR §7 citation missing from the revised map prose; restoring
the existing cancellation boundary reference fixed it. The GA guard-pair fixture
uses capacity 7 so a free-selection control is live while another selection is
unavailable after the captured/held orders. The design did not require the default
capacity 6 for that characterization. No behavioral-scope deviation.

No class C contract violation found. All five behavioral additions are class B,
not new contract semantics. No availability proof, complete precedence order,
private allocation inspection, clean-room authorship, production durability,
external execution, bank exactly-once, chain authority/finality, legal compliance
or production-readiness claim. No hardware, paid service, credentials, real funds,
real PG/bank/KYC call, public endpoint, Sui testnet/mainnet, new protocol command,
product-policy value, storage engine or production runtime was needed.

[LOCKED_EDGE pin drift](../../docs/status/OPEN_USER_DECISIONS_20261027_PERF_PROBE_ADDENDUM.md)
is the already-open User/repository-owner decision. No option is selected, pin
repinned or release probe run. It does not block these synthetic characterizations.
Remaining uncertainty and follow-up owners are the matrix owners above; final-head
KTX/KIX CI and non-author A2 review remain supervisor gates. Local READY is only a
builder delivery state.
