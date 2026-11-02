# Local synthetic resale offer source — builder evidence

Task: `plan-local-resale-offer-source`; immutable task input is the user-supplied
node specification/design in this session. No node issue or node-specific
`docs/tasks/` document exists. Broader scope: `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md`,
`docs/DEVELOPMENT_PLAN.md`, `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`.
Dependency `booking-resale-admission-deepening` is represented by the existing
resale FSM and rejection audit at the observed base, not a new dependency claim.

## Preflight

- Branch: `agent/kix-plan-local-resale-offer-source`; resumed partial worktree: four untracked implementation/example files and this evidence directory; no tracked changes.
- Initial task HEAD and local `origin/main`: `1bed1bb5a48608b820efce40ede2ce0b9a1d663b`.
- `git fetch origin main` deliberately omitted: the supervisor prohibits all
  network actions. Remote freshness is unverified; no base adjustment was made.
- Kernel blobs before work match `69564b166f0c27f9af5d8422f0a466b18d74c20f`
  and `b607996c83a119c349f1cc90469ac1ba82764e20` respectively.
- Base `git ls-tree -r HEAD reference/v0.3-rc1/ | sha256sum`:
  `0c2dfd8991b7c8e9475344db10c7d8f8bd15dbfea7f5801ac91a136897777282`.

## Existing coverage mapping (recorded before new tests)

| Requirement | Classification and existing evidence | Gap to exercise |
|---|---|---|
| FSM ownership/version/price/expiry and listing race | Sufficient scoped behavior: `test_resale_fsm.py::ResaleFsmTests.test_stale_listing_policy_and_expiry_do_not_transfer`, `test_buy_hold_is_optional_and_cancel_order_decides_the_race` | Partial overall: direct/adapter parity absent |
| Replay and mock-only flags | Sufficient scoped behavior: `test_restore_replays_one_transfer_and_omits_rejections`, `test_external_attempts_do_not_journal` and `assert_not_final` in the same module | Receipt/error identity and adapter replay, including after expiry |
| Rejection atomicity and admission lock | Sufficient scoped FSM evidence: generated `test_resale_rejection_atomicity.py::ResaleRejectionAtomicityTests.test_list_resale_*_leaves_no_trace` | Boundary failures must never invoke the FSM or retain keys |
| One fetch per explicit invocation | Not covered for resale | Success, replay, key conflict, malformed callers/records, absence, faults; no cached fallback |
| Immutable recordings/detached results | Not covered for resale | Constructor mutation, read-only mapping, detached nested outputs/history, strict JSON decoding |
| Runnable actual-machine example | Not covered for this boundary | Explicit listing then competing-listing refusal; no hold, resale payment or transfer |
| Discovery/docs wiring | Existing repository checkers | New modules and evidence links discovered |

Baseline: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/reference/booking_resale_admission" python3.12 -m unittest test_resale_fsm test_resale_rejection_atomicity`:
**PASS**, 128 tests.


## Delivered boundary and gap evidence

- `resale_offer_source.py`: protocol, exact typed record and local input errors.
- `fake_resale_offer_source.py`: copied read-only JSON recordings, fresh decoding,
  duplicate/constant/root rejection, immediate ERROR/TIMEOUT faults, tuple history.
- `resale_offer_adapter.py`: exactly one fetch, shape/scalar/selector checks before
  any FSM access, then only `list_resale`; unchanged receipt/error propagation.
- `example_resale_offer_adapter.py`: real reservation and resale instances, explicit
  synthetic register/hold/confirm/payment-fact/issue/adopt setup, then one listing
  and a separate competing-listing refusal. No payment initiation or transfer.
- `test_resale_offer_source.py`: five tests addressing immutable mappings, deeply
  detached fetches/history, absence, strict decoding, constructor bounds and faults.
- `test_resale_offer_adapter.py`: twelve tests addressing exact forwarding and
  receipt/exception identity; direct/adapter receipts, errors, canonical states,
  digests and journals; replay, expiry, key conflicts, stale holder/version, cap,
  competing listing, admission lock and retained rejection after lock expiry;
  optional reservation binding; source failures after acceptance; shape/identity
  guards without FSM attribute access; real-machine zero-call/state/journal checks
  and valid same-key first acceptance after boundary failures; runnable example.

Existing tests were cited/reused rather than importing existing TestCase classes.
`assert_not_final` is reused from `test_resale_fsm.py`. The 473-test discovery run
includes the 17 new tests once and the existing 128-test resale baseline.

## Commands and actual results

All commands below ran from the repository root with Python 3.12.15.
Python test/example/check commands used `PYTHONDONTWRITEBYTECODE=1`; named-module
resale commands additionally used
`PYTHONPATH="$PWD/reference/booking_resale_admission"`.
No jobs were started with shell background execution. All invocations completed.

| Command | Actual result |
|---|---|
| `python3.12 -m unittest test_resale_fsm test_resale_rejection_atomicity` | PASS, 128 tests |
| `python3.12 -m unittest test_resale_offer_source test_resale_offer_adapter` | PASS, 17 tests |
| `python3.12 reference/booking_resale_admission/example_resale_offer_adapter.py` | PASS; LISTED then explicit RIGHT_SALE_LOCKED; two fetches; mock flags retained |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS, 473 tests, including existing loopback tests |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS; architecture/dependency declaration gate only |
| `python3.12 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo --version` | Exit 1: rustup attempted to create `/home/box/.rustup` on a read-only filesystem |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 1 before tests: pinned toolchain 1.98.1 not installed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 1 before Clippy: pinned toolchain not installed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 1 before formatting: pinned toolchain not installed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 1 before tests: pinned toolchain not installed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 1 before Clippy: pinned toolchain not installed |

All five Cargo verification attempts explicitly set `RUSTUP_AUTO_INSTALL=0`
and `CARGO_NET_OFFLINE=true`; no installation/download was attempted. The
read-only rustup startup error was diagnosed by disabling auto-install, revealing
the absent pinned toolchain. No Rust source was changed. The cache report also
lists 0/18 registry dependencies present; exit 0 is informational, not cache readiness.

The complete `protocol.yml` **Stdlib offline document checks** run block was
extracted with a local regex and each listed command invoked sequentially via
`subprocess.run`, replacing `python3` with `python3.12`. The two OpenAPI checkers
and their self-tests were then invoked the same way. Aggregate: **67 invocations,
0 failures**. Each table row below is an actually run command, not an inferred CI
result. Self-tests' intentionally detected negative controls are passing results.

| Command | Actual result |
|---|---|
| `python3.12 scripts/check_status_register.py` | PASS, exit 0 |
| `python3.12 scripts/check_status_register.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_rs_profile_traceability.py` | PASS, exit 0 |
| `python3.12 scripts/check_rs_profile_traceability.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_read_model_source_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_read_model_source_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_docs_index.py` | PASS, exit 0 |
| `python3.12 scripts/check_docs_index.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_i12_proof_ids.py` | PASS, exit 0 |
| `python3.12 scripts/check_i12_proof_ids.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_delegation_layer_matrix.py` | PASS, exit 0 |
| `python3.12 scripts/check_delegation_layer_matrix.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_rs_predicate_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_rs_im_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_rs_im_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_contract_error_codes.py` | PASS, exit 0 |
| `python3.12 scripts/check_contract_error_codes.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_adapter_identity_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_adapter_identity_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_v5_transition_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_v5_transition_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_readiness_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_readiness_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_settlement_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_settlement_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_bra_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_bra_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_credit_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_credit_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_ai_delegation_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_ai_delegation_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_lifecycle_adr_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_contract_invariants_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_contract_invariants_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_toss_card_profile_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_bcs1_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_bcs1_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_performance_measurement_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_performance_measurement_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_feature_semantics_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_feature_semantics_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_integration_gate_contract_evidence_map.py` | PASS, exit 0 |
| `python3.12 scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_evidence_map_rollup.py` | PASS, exit 0 |
| `python3.12 scripts/check_evidence_map_rollup.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_class_b_index.py` | PASS, exit 0 |
| `python3.12 scripts/check_class_b_index.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_ci_checker_wiring.py` | PASS, exit 0 |
| `python3.12 scripts/check_ci_checker_wiring.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_ci_test_discovery.py` | PASS, exit 0 |
| `python3.12 scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_loopback_host.py` | PASS, exit 0; loopback probes succeeded, no host qualification/permission claim |
| `python3.12 scripts/check_loopback_host.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_cargo_offline_cache.py` | PASS, exit 0; informational: 0/18 dependencies cached |
| `python3.12 scripts/check_cargo_offline_cache.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_stage5_host.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_openapi_contract.py` | PASS, exit 0 |
| `python3.12 scripts/check_openapi_contract.py --self-test` | PASS, exit 0 |
| `python3.12 scripts/check_integration_gate_openapi.py` | PASS, exit 0 |
| `python3.12 scripts/check_integration_gate_openapi.py --self-test` | PASS, exit 0 |

## Final scope and protected-byte verification

Complete changed paths (six new Python files, two documentation edits, one new record):

1. `reference/booking_resale_admission/resale_offer_source.py`
2. `reference/booking_resale_admission/fake_resale_offer_source.py`
3. `reference/booking_resale_admission/resale_offer_adapter.py`
4. `reference/booking_resale_admission/example_resale_offer_adapter.py`
5. `reference/booking_resale_admission/test_resale_offer_source.py`
6. `reference/booking_resale_admission/test_resale_offer_adapter.py`
7. `reference/booking_resale_admission/README.md`
8. `docs/README.md`
9. `validation/2026-11-02-plan-local-resale-offer-source/README.md`

| Verification command | Actual result |
|---|---|
| `git rev-parse HEAD origin/main` | Both `1bed1bb5a48608b820efce40ede2ce0b9a1d663b`; local refs only |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git ls-tree -r HEAD reference/v0.3-rc1/ \| sha256sum` | Base listing digest `0c2dfd8991b7c8e9475344db10c7d8f8bd15dbfea7f5801ac91a136897777282` |
| `git diff --exit-code -- reference/v0.3-rc1 reference/booking_resale_admission/resale_fsm.py reference/booking_resale_admission/reservation_fsm.py reference/booking_resale_admission/admission_fsm.py reference/booking_resale_admission/mock_gates.py docs/contracts sdk integration_gate .aiops docs/tasks .github` | PASS; no tracked changes in these preserved paths |
| `git diff --check` | PASS |
| `python3.12 -` (inline SHA-1 Git blob comparison of every protected reference file, plus actual file-set comparison) | PASS; all 108 `reference/v0.3-rc1/` files byte-identical to HEAD; no extra files |
| `python3.12 -` (inline AST parse and whitespace check over six new Python files) | PASS |
| `python3.12 scripts/check_docs_index.py` (after evidence completion) | PASS; scanned=326, indexed=291, allowlisted=35 |

## Handoff, deviations and retained uncertainty

- Implementation/final local Git HEAD remains
  `1bed1bb5a48608b820efce40ede2ce0b9a1d663b`; implementation is uncommitted.
  Exact final committed task head is **pending supervisor commit**, not this base.
  Merge SHA and post-merge CI: **not applicable; no merge performed**.
- No task issue exists and no node-specific file exists under `docs/tasks/`.
  The user-supplied node/design is the immutable task input; it is not an ASTRA
  program-mode session. No task documents, `.aiops/` files or workflow were edited.
- The partial implementation/example and initial coverage note were resumed.
  No implementation-design deviation was required. No policy value, new command,
  external service, storage engine or consequential out-of-node action was needed.
- Supervisor no-network/no-GitHub instruction overrides the preflight fetch:
  local `origin/main` matches task HEAD, but remote freshness remains unverified.
  No Git commit, push, branch/history mutation, issue/PR action or comment occurred.
- Python/tool selection matches the design. Full booking discovery and the entire
  offline document-check block ran successfully here, including local loopback.
  KTX architecture checks passed; Cargo checks were attempted but could not run
  without the unavailable pinned toolchain. No network/toolchain installation was
  authorized or performed. No broad Rust success is claimed.
- Full hosted protocol verification (Move, SDK, circuits/ZK and chain journeys),
  unrelated reference suites and Rust workspace execution are not established by
  this evidence. They were not needed to exercise changed Python/docs paths.
- KTX exact-final-head CI: run ID **not observed**, status/conclusion **unverified**.
  KIX exact-final-head CI: run ID **not observed**, status/conclusion **unverified**.
  A2 non-author exact-final-head review is **pending**. The supervisor must obtain
  that review and completed/success KTX/KIX on the final committed head before
  proposing merge; builder readiness is a local handoff only.
- Class A: observed adapter/FSM behavior matches the scoped listing contract.
  Class C explicit contract violations found: **none**. New Class B discrepancy:
  **none**; existing Class B clock-skew/post-mutation internal-fault audit cases
  remain characterizations, not rollback guarantees. No FSM was modified to hide them.
- Source-informed, deterministic, single-process synthetic evidence only.
  Record identity does not authenticate a seller or establish provider, chain or
  marketplace authority/currentness. No persistence, general cross-machine
  atomicity, legal compliance, funds movement or production readiness is proved.
  No payment lookup handoff, automatic hold/payment/transfer, payout, authentication,
  new protocol command or external call was added.
- R01/R05 remain partial with **설계중** labels. Product policy is **UNDETERMINED**
  with Astra/User. Legal/privacy, tax/accounting and Toss technical/sales inputs
  keep the named owners in contract §7.1. Future external sources require separate
  scope/authority decisions; this node does not open them.
