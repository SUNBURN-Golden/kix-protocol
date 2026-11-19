# plan-local-credit-stdio-client — local builder evidence

Task input: the supervisor-supplied node specification and design plan in this
session; no task issue or document under docs/tasks exists. Not ASTRA program mode.
Branch: agent/kix-plan-local-credit-stdio-client. Initial HEAD and local origin/main:
`a02bd83c29f524de684ed0e97d3a750ac8c0de71`. No stated-base delta in local refs.
The user forbids network/GitHub and Git publication, overriding the initial fetch:
origin/main is locally observed, not freshly fetched. No commit/push/PR/comment.

## Coverage mapping (recorded before implementation)

| Requirement | Existing coverage | Classification and gap |
|---|---|---|
| Session/FSM parity | test_credit_session.CreditSessionTests.test_each_journey_matches_direct_machine_receipts_errors_and_reads | Sufficient for forwarding semantics; live transport not covered |
| Lifecycle, historical receipts/current views | test_credit_cli.CreditCliTests.test_lifecycle_historical_receipts_gate_views_and_reconcile | Sufficient semantics; partially covered overall: replies before stdin EOF missing |
| COMMITTED gate refusals | test_credit_cli.CreditCliTests.test_settlement_gate_refusals_retain_machine_error_codes and test_captured_gate_blocks_bound_draw_but_not_unbound; test_credit_properties.MachinePropertyTests gate cases | Sufficient business semantics; reuse journeys for client parity |
| Replay/idempotency conflicts | test_credit_cli.CreditCliTests.test_semantic_refusals_retain_machine_error_codes; test_credit_properties.py and test_credit_rejection_atomicity.py | Sufficient semantics; no duplicate business matrix needed |
| Strict JSON/fixtures/provenance/integer amounts | test_credit_cli.py decoder/shape/roundtrip/setup tests | Sufficient CLI coverage; reply validation not covered |
| One outstanding request; interrupted or malformed exchange; permanent fencing/no retry | No credit subprocess client exists; ticket_operations_client.py is lifecycle precedent | Not covered for credit |
| Import safety, child reaping, example | Session/CLI subprocess tests only | Not covered for credit client |

Builder-authored, source-informed evidence; A2 non-author review and exact-head
KTX/KIX CI remain supervisor gates, with no inherited success or merge claim.

## Delivered behavior and new gap coverage

`credit_client.py` explicitly owns one child and permits one synchronous exchange
at a time. Reply validation checks strict JSON/UTF-8, newline completion, exact
fields, provenance, operation correlation and success payload kind. Business
payloads and error codes are retained unchanged. Matching domain rejections allow
explicit continuation; typed fatal/startup errors stop the client. Transport
uncertainty permanently fences it, retaining request/wire/observed reply bytes.
Cleanup never resubmits, restarts, reconciles or compensates. Only the existing
CLI `_emit` changes, adding `flush=True`.

The new `test_credit_client.py::CreditClientTests` adds 15 tests:

| Gap | New tests |
|---|---|
| Live child replies before stdin EOF, direct-session equality, response-derived identities/sequence | `test_live_lifecycle_matches_direct_session` (ordinary buffering, inherited PYTHONUNBUFFERED removed), `test_existing_journeys_match_direct_session` (all five existing journeys) |
| JSON representation and integer preservation, rejection before write | `test_exact_integer_roundtrip_without_coercion`, `test_local_validation_before_write_and_valid_continuation` |
| Domain continuation, fatal/startup terminal state and broken-pipe race | `test_fatal_error_is_terminal_and_domain_error_allows_explicit_continuation`, `test_startup_errors_are_terminal_including_submission_race` |
| Malformed UTF-8/JSON, nested duplicate keys, nonfinite/overflow, wrong provenance/operation/payload/fields, truncated line/EOF, child exit; preserved bytes and exactly one submission/launch | `test_uncertain_replies_fence_without_resend`, `test_payload_kind_validation_for_reads_and_unknown_operations` |
| Short write, broken pipe, flush/read error, write/read interruption; no remainder write or recovery | `test_short_write_broken_pipe_and_interrupt_fence` |
| One outstanding request/cleanup, reentrancy and before-write rejection | `test_busy_and_reentrant_calls_do_not_write`, `test_concurrent_cleanup_rejected` |
| Owned-child reaping, idempotent close, caller exception, terminate/kill escalation | `test_close_reaps_owned_child_and_context_exception`, `test_cleanup_escalation` |
| Side-effect-free imports and runnable transcript example, including stop on error | `test_import_launches_nothing`, `test_example_matches_direct_session_and_stops_on_error` |

Existing deterministic coverage remains the authority for COMMITTED refusal,
historical receipts, current views, first-result replay and idempotency conflict
semantics. New parity tests exercise those existing journeys across the live
transport rather than creating a second business specification.

## Commands and actual results

Full stdout/stderr and exit codes are in [commands.json](commands.json). Validation
commands ran in the foreground, sequentially, with `PYTHONDONTWRITEBYTECODE=1`
and `CARGO_NET_OFFLINE=true`. No automatic retry or CI polling was performed.
The initial default interpreter was Python 3.13.5; CI-aligned runs used installed
Python 3.12.15. Rust was installed 1.98.1, matching the workflow pin. Only the
provisioned `/home/box/.cargo/registry` was copied into `/tmp/kix-credit-cargo/registry`
(`mkdir -p` and `cp -a`, exit 0); Cargo home/target stayed in `/tmp`, with no fetch,
installation or dependency modification.

Summary: focused client **15 passed**; combined client/CLI/session **35 passed**;
full credit discovery **183 passed**. Six CI reference suites passed
**224 / 858 / 183 / 117 / 200 / 73** tests, total **1,655**. All **68** offline
checker commands passed: the workflow's unguarded stdlib list except the plain
socket probe, both OpenAPI checkers in plain/self-test modes, and both architecture
scripts. Architecture self-tests passed 7 tests. Rust formatting passed. Four Rust
test/Clippy attempts were **unavailable (exit 101)** because workspace dependency
`bcs` is absent from the offline cache; no Rust tests or lint executed. These are
not green Rust gates. No cache change or retry followed those attempts.

The example ran under both Python versions and exited 0, each producing 34 JSONL
replies. Exact direct-session output comparison and error-stop behavior also pass
in the client tests.

| Actual command (common environment above) | Actual result |
|---|---|
| `env PYTHONPATH=reference/credit_advance_f04 python3 -m unittest test_credit_client test_credit_cli test_credit_session` | exit 0; 35 tests passed in 4.187s |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 183 tests passed in 10.725s |
| `python3 reference/credit_advance_f04/example_credit_client.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/lifecycle.jsonl --cleanup-timeout 1` | exit 0; 34 JSONL replies |
| `python3.12 --version` | exit 0 |
| `rustc --version` | exit 0 |
| `env PYTHONPATH=reference/credit_advance_f04 python3.12 -m unittest test_credit_client test_credit_cli test_credit_session` | exit 0; 35 tests passed in 4.375s |
| `python3.12 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0; 224 tests passed in 1.638s |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0; 858 tests passed in 98.053s |
| `python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 183 tests passed in 11.781s |
| `python3.12 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0; 117 tests passed in 3.679s |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 200 tests passed in 3.598s |
| `python3.12 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | exit 0; 73 tests passed in 10.443s |
| `python3.12 scripts/check_status_register.py` | exit 0 |
| `python3.12 scripts/check_status_register.py --self-test` | exit 0 |
| `python3.12 scripts/check_rs_profile_traceability.py` | exit 0 |
| `python3.12 scripts/check_rs_profile_traceability.py --self-test` | exit 0 |
| `python3.12 scripts/check_read_model_source_map.py` | exit 0 |
| `python3.12 scripts/check_read_model_source_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_docs_index.py` | exit 0 |
| `python3.12 scripts/check_docs_index.py --self-test` | exit 0 |
| `python3.12 scripts/check_i12_proof_ids.py` | exit 0 |
| `python3.12 scripts/check_i12_proof_ids.py --self-test` | exit 0 |
| `python3.12 scripts/check_delegation_layer_matrix.py` | exit 0 |
| `python3.12 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| `python3.12 scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_rs_im_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_contract_error_codes.py` | exit 0 |
| `python3.12 scripts/check_contract_error_codes.py --self-test` | exit 0 |
| `python3.12 scripts/check_adapter_identity_map.py` | exit 0 |
| `python3.12 scripts/check_adapter_identity_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_v5_transition_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_readiness_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_readiness_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_settlement_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_settlement_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_bra_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_bra_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_credit_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_credit_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_ai_delegation_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_lifecycle_adr_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_contract_invariants_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_toss_card_profile_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_bcs1_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_bcs1_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_performance_measurement_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_feature_semantics_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_feature_semantics_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_integration_gate_contract_evidence_map.py` | exit 0 |
| `python3.12 scripts/check_integration_gate_contract_evidence_map.py --self-test` | exit 0 |
| `python3.12 scripts/check_evidence_map_rollup.py` | exit 0 |
| `python3.12 scripts/check_evidence_map_rollup.py --self-test` | exit 0 |
| `python3.12 scripts/check_class_b_index.py` | exit 0 |
| `python3.12 scripts/check_class_b_index.py --self-test` | exit 0 |
| `python3.12 scripts/check_ci_checker_wiring.py` | exit 0 |
| `python3.12 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| `python3.12 scripts/check_ci_test_discovery.py` | exit 0 |
| `python3.12 scripts/check_ci_test_discovery.py --self-test` | exit 0 |
| `python3.12 scripts/check_loopback_host.py --self-test` | exit 0 |
| `python3.12 scripts/check_cargo_offline_cache.py` | exit 0 |
| `python3.12 scripts/check_cargo_offline_cache.py --self-test` | exit 0 |
| `python3.12 scripts/check_stage5_host.py --self-test` | exit 0 |
| `python3.12 scripts/check_openapi_contract.py` | exit 0 |
| `python3.12 scripts/check_openapi_contract.py --self-test` | exit 0 |
| `python3.12 scripts/check_integration_gate_openapi.py` | exit 0 |
| `python3.12 scripts/check_integration_gate_openapi.py --self-test` | exit 0 |
| `python3.12 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3.12 scripts/test_runtime_architecture.py` | exit 0 |
| `env CARGO_HOME=/tmp/kix-credit-cargo CARGO_TARGET_DIR=/tmp/kix-credit-target CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; UNAVAILABLE: cached bcs missing, no tests/lint executed |
| `env CARGO_HOME=/tmp/kix-credit-cargo CARGO_TARGET_DIR=/tmp/kix-credit-target CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; UNAVAILABLE: cached bcs missing, no tests/lint executed |
| `env CARGO_HOME=/tmp/kix-credit-cargo CARGO_TARGET_DIR=/tmp/kix-credit-target CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `env CARGO_HOME=/tmp/kix-credit-cargo CARGO_TARGET_DIR=/tmp/kix-credit-target CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; UNAVAILABLE: cached bcs missing, no tests/lint executed |
| `env CARGO_HOME=/tmp/kix-credit-cargo CARGO_TARGET_DIR=/tmp/kix-credit-target CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; UNAVAILABLE: cached bcs missing, no tests/lint executed |
| `env PYTHONPATH=reference/credit_advance_f04 python3.12 -m unittest test_credit_client` | exit 0; 15 tests passed in 2.426s |
| `python3.12 reference/credit_advance_f04/example_credit_client.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/lifecycle.jsonl --cleanup-timeout 1` | exit 0; 34 JSONL replies |
| `python3.12 /tmp/kix-credit-preserve.py` | exit 0; 121 protected files unchanged, both kernel blobs match |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime reference/credit_advance_f04/credit_session.py reference/credit_advance_f04/credit_fixture.py reference/credit_advance_f04/credit_fsm.py reference/credit_advance_f04/mock_credit.py reference/credit_advance_f04/open_terms.py` | exit 0 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| `git rev-parse HEAD origin/main HEAD:reference/v0.3-rc1 origin/main:reference/v0.3-rc1` | exit 0 |
| `git diff --check` | exit 0 |

Additional read-only session inspection: `git status --short` was initially clean;
`git branch --show-current`, `git rev-parse HEAD`, `git rev-parse origin/main` all
exited 0 with the values above. README, DEVELOPMENT_PLAN, BASELINES,
AUTHORITY_MODEL_1, AGENTS, PROGRAM_DECISIONS_20260928, the control-plane pointer/pin,
F04 contract, credit session/fixture/CLI/tests/fixtures, ticket client precedent
and both GitHub workflows were inspected. An initial pre-edit SHA-256 snapshot
attempt failed on Git-quoted non-ASCII filenames; switching the read to
`git ls-files -z` succeeded before editing. The optional `file` utility was absent;
Python 3.12 discovery succeeded through its existing interpreter symlink. Neither
inspection issue affected source files or validation results.

## Identity, preservation and outstanding gates

- Task ID: `plan-local-credit-stdio-client`; issue/task-document path: none. This
  supervisor input is the task document, and its design is read-only.
- Dependencies: `plan-local-credit-desk`, `plan-local-ticket-stdio-client`; audit
  floor A2, astra_gate None, user_merge False. No `.aiops/` adoption/activation.
- Observed local main/base, initial implementation HEAD and unchanged repository
  HEAD: `a02bd83c29f524de684ed0e97d3a750ac8c0de71`. Remote freshness is unverified;
  no local base delta, rebase, merge or history rewrite.
- Implementation/final task commit: **not created**, per supervisor instruction.
  The final task head will be the supervisor's eventual commit; these checks cover
  this uncommitted working-tree delivery. No SHA is invented for it.
- Kernel blobs before and after: `runtime/crates/kix-kernel/src/lib.rs` =
  `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
  `b607996c83a119c349f1cc90469ac1ba82764e20`. Neither was mutated, even transiently.
- SHA-256 snapshots before/after match for all 121 protected tracked paths,
  including 108 historical-reference files plus both locks, `.aiops/` and
  `docs/tasks/`. Read-only `git diff --exit-code origin/main -- ...` also confirms
  those paths, `.github/`, all `runtime/`, and the credit session/fixture/FSM/mock/
  open_terms modules unchanged. Historical `reference/v0.3-rc1` tree IDs at local
  HEAD and origin/main both equal `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
- Exact-final-head KTX workflow: **NOT_RUN**, run ID/status/conclusion unavailable.
- Exact-final-head KIX workflow: **NOT_RUN**, run ID/status/conclusion unavailable.
- Non-author exact-final-head A2 review: **pending supervisor**. Builder tests are
  source-informed and are not independent review or a clean-room witness.
- Merge commit, final-merge locked blobs, post-merge main CI IDs/status/conclusions:
  **not applicable**, no merge or GitHub action performed.

## Deviations, classifications and limits

1. AGENTS §1 fetch was not run because the explicit supervisor rule prohibits
   network actions. All Git refs above are locally observed. Git commits, pushes,
   PRs, issues and comments remain entirely with the supervisor.
2. Response-derived claim reads in the example wait for `snapshot_frozen=true`.
   The repository proves `view_claim` returns UNKNOWN_CLAIM before the first
   accepted draw/note. This preserves existing semantics and lets the supplied
   lifecycle example complete without inventing an empty claim.
3. The requested full booking discovery included its pre-existing
   `test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`:
   it made synthetic loopback HTTP exchanges. This should have been identified
   before running under the supervisor's no-network rule. No external/provider/
   GitHub calls or public endpoint were made. The later plain
   `scripts/check_loopback_host.py` socket probe was **NOT_RUN** for that reason;
   its fake-only `--self-test` passed. No additional socket probe was run.
4. Python 3.13.5 initial checks were supplemented with the available CI-pinned
   Python 3.12 line. Offline Rust test/Clippy resolution is blocked by absent bcs;
   no download, CI edit or runtime change was used to bypass it. Full hosted CI,
   SDK/Move/Sui/ZK/storage jobs unrelated to touched paths were not run.

Class A: existing defined credit behavior matches direct sessions and remains
unchanged. No explicit contract violation was found; no authoritative contract
was amended. No new Class B business semantics were invented. Existing Class B
characterizations remain: stored rejections are not journaled, reconcile shares
sources and proves in-memory determinism only, and a bound draw observes the
settlement view at call time. A transport failure leaves its business outcome
unknown; process exit or cleanup proves neither rejection nor rollback.

No real money, real PG/bank/KYC, public service, Sui testnet/mainnet, persistence,
storage/log engine, consensus/replication, new adapter/protocol command/coin/TIX,
SDK/catalogue change, product policy value, credit console or production runtime
was needed or implemented. Policy stays UNDETERMINED — Astra/User; legal terms
stay UNDETERMINED — User/legal. No durability, financial/legal compliance,
external exactly-once, chain finality or production readiness is claimed.

Remaining uncertainty: current remote main, missing offline Rust dependency,
non-author review and exact-final-head CI after the supervisor commits. No known
in-scope implementation fix remains. Local **READY** means ready for supervisor
handoff; it is not merge-ready, review acceptance or merge authorization.

## Complete changed-path list

- `reference/credit_advance_f04/credit_client.py`
- `reference/credit_advance_f04/credit_cli.py`
- `reference/credit_advance_f04/test_credit_client.py`
- `reference/credit_advance_f04/example_credit_client.py`
- `reference/credit_advance_f04/README.md`
- `docs/README.md`
- `validation/2026-11-06-plan-local-credit-stdio-client/README.md`
- `validation/2026-11-06-plan-local-credit-stdio-client/commands.json`
