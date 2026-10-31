# Local finance workbench — builder evidence

Node `plan-local-finance-workbench`. Task input is the supervisor's node and
read-only design supplied in this session; there is no node task document or
issue. `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` is historical context.
This is not an ASTRA program-mode session.

Observed local `origin/main`, base and initial branch HEAD:
`2d323b90f305d07d2ababdb5bbb0ffe47fda7b03` on
`agent/kix-plan-local-finance-workbench`. Fetch/network actions are prohibited
by the supervisor, overriding AGENTS §1's fetch step; remote freshness is
unverified. No base drift is visible locally. No commits/publication authorized;
implementation/final committed head, hosted CI and merge evidence are pending
supervisor work. No merge-ready claim.

## Coverage inventory (recorded before adding interface tests)

Existing maps: [settlement](../../docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md)
and [credit](../../docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md).
Paths below are relative to `reference/`.

| Requirement | Existing coverage | Interface gap to address |
|---|---|---|
| Configurable actual-machine API and JSON CLI | Not covered | New session/CLI and subprocess fixture tests |
| Statement commit/observation | Partially covered: `settlement_f01_f03/test_statement_adapter.py`, tests `test_one_fetch_exact_forwarding_and_same_response_or_error_object`, `test_replay_fetches_each_time_returns_first_snapshot_after_later_changes` | Composed-machine parity and source-call counts |
| Rejected bound draw key stays rejected, explicit new key succeeds | Partially covered: `credit_advance_f04/test_credit_properties.py`, `MachinePropertyTests.test_a_gate_rejected_key_stays_rejected_after_commit_and_a_new_key_succeeds` | Actual settlement source instead of stub |
| Partial repayment and close | Sufficiently covered: `credit_advance_f04/test_credit_fsm.py`, `test_offer_approve_draw_repay_and_close_are_mock_ledger_only`, `test_repayment_order_partial_and_double_application`, `test_close_rejects_remaining_exposure_before_release` | Journey forwarding parity only |
| Credit inertness / separate settlement cash | Partially covered: credit gate tests and `settlement_f01_f03/test_settlement_fsm.py::test_later_statement_stays_on_commit_and_cases_do_not_share_cash` | Per-credit-step settlement state/journal equality; two real settlements |
| First results/errors/false flags | Sufficiently covered at FSM: both `test_returned_data_isolation.py`, `test_*_rejection_atomicity.py`, existing FSM/property suites | Interface parity, changed-body conflicts, saved face after later changes |
| No retries or replacement keys | Adapter covers source failures, session not covered | Dispatch spies and original-key probes |
| Whole-fixture validation / exact integer JSON | Not covered | Reject invalid late steps before constructing a session; subprocess status checks |
| CI discovery | Existing `scripts/check_ci_test_discovery.py` and credit discovery workflow | Verify new top-level tests are reached without workflow changes |

## Boundaries

Synthetic, one-process tooling only. Product policy remains UNDETERMINED under
SET-POLICY-DRAFT-0.3 / F04-MOCK-TERMS-DRAFT-0.2 with Astra/User and existing
legal, tax and accounting owners. No new economic calculation, automatic
transition, retry, replacement key, rollback, cross-machine atomicity, persistence,
read model, SDK, protocol command, funds, external provider, or chain execution.

Locked blobs before work match `69564b166f0c27f9af5d8422f0a466b18d74c20f`
and `b607996c83a119c349f1cc90469ac1ba82764e20`; protected reference tree at base
is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. All protected file bytes were
snapshotted before editing for final comparison.

## Implementation and new evidence

Added the session facade, strict fixture CLI, two runnable synthetic fixtures,
and two top-level test modules to the existing credit discovery directory.
The 13 new interface tests exercise direct-FSM receipt/error/state parity at
every fixture step; credit inertness around every credit command; independent
cash/exposure; explicit source fetch counts; unmodified result/exception objects;
original rejection keys; snapshots reused after later statements; early validation;
subprocess exit statuses; exact integer encoding and no retries/replacement keys.
The existing economic tests were reused, not duplicated as new policy evidence.
Discovery reports `reference/credit_advance_f04 files=10`, reached by the existing
`Offline reference state machines and OpenAPI pins` workflow step.

Complete changed paths:

- `docs/README.md`
- `reference/credit_advance_f04/README.md`
- `reference/credit_advance_f04/local_finance_session.py`
- `reference/credit_advance_f04/local_finance_cli.py`
- `reference/credit_advance_f04/fixtures/finance_journey.synthetic.json`
- `reference/credit_advance_f04/fixtures/finance_isolation.synthetic.json`
- `reference/credit_advance_f04/test_local_finance_session.py`
- `reference/credit_advance_f04/test_local_finance_cli.py`
- `validation/2026-10-31-plan-local-finance-workbench/README.md`

## Commands actually executed and results

All Python verification ran with `PYTHONDONTWRITEBYTECODE=1`. Python is 3.13.5;
Rust/Cargo are 1.98.1 (the workflows request Python 3.12 and Rust 1.98.1).
Tests ran in foreground subprocesses, without shell background jobs. No network,
commit, push, issue, PR or comment operation was performed. No check was weakened.

Before the final recorded pass, the same narrow unittest command below first ran
12 tests with 2 test-harness errors: a flag assertion used a nonexistent top-level
settlement receipt field and an inspect-based dispatch spy lacked its original
signature. Both were fixed in the test code; the next run passed 12 tests. A
saved-snapshot/offer-replay boundary test was then added; subsequent narrow runs
passed all 13 tests. Both fixtures also passed initial standalone smoke runs
(21 and 26 steps) before the recorded runs below. There were no implementation,
full-suite, checker or Rust-check failures.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p 'test_local_finance*.py'` | PASS — 13 tests |
| `python3 reference/credit_advance_f04/local_finance_cli.py --fixture reference/credit_advance_f04/fixtures/finance_journey.synthetic.json` | PASS — 21 steps; 3 source calls; ok=true |
| `python3 reference/credit_advance_f04/local_finance_cli.py --fixture reference/credit_advance_f04/fixtures/finance_isolation.synthetic.json` | PASS — 26 steps; 2 source calls; ok=true |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS — 211 tests |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS — 161 tests |
| `python3 scripts/check_docs_index.py` | PASS (exit 0) |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_settlement_evidence_map.py` | PASS (exit 0) |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_credit_evidence_map.py` | PASS (exit 0) |
| `python3 scripts/check_credit_evidence_map.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0) |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0) |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0) |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0) |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0) |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0) |
| `python3 scripts/test_runtime_architecture.py` | PASS — 7 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS (exit 0) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS (exit 0) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS (exit 0) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS (exit 0) |
| `git diff --check` | PASS; no whitespace errors |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before/after: prescribed blobs match |
| Python SHA-256 snapshot comparison of both locked files and every file under `reference/v0.3-rc1/**` | PASS: identical path set and all 110 file bytes before/after |
| `git rev-parse origin/main HEAD` / `git branch --show-current` | Both SHAs equal the recorded base; expected task branch |

The command table expands the exact commands run by a temporary stdlib runner.
Full transient output was retained under `/tmp/local-finance-{python,checks,rust}-*.log`
in this builder environment; it is not a durable or hosted-CI artifact. The
fixtures and tests are the committed-source candidates for reproducible evidence.

## Final state, deviations and remaining gates

- Final local HEAD remains `2d323b90f305d07d2ababdb5bbb0ffe47fda7b03`;
  implementation is **uncommitted** by instruction. There is no implementation
  commit or exact final task commit yet. No merge commit exists for this node.
- Both locked blobs after work still match the required values above. All 108
  protected reference files plus the two locked files are byte-identical.
  `.aiops/`, task documents, FSM implementations, contracts, catalogue, SDK,
  gate and workflows were not edited.
- Exact-head KTX CI: run ID/status/conclusion **not available/not queried**.
  Exact-head KIX CI: run ID/status/conclusion **not available/not queried**.
  Post-merge main CI: **not applicable; no merge performed**. Local checks do not
  substitute for either hosted workflow. A2 non-author exact-head review and
  completed/success required KTX/KIX gates remain supervisor responsibilities
  after commit/publication; no review, independent PASS or merge readiness claimed.
- Deviations: the supervisor prohibition on network overrides `git fetch origin
  main`; local remote-ref freshness is unverified. There is no node file under
  `docs/tasks/` and none was invented or edited. The current task is the supplied
  node/design. Python 3.13.5 was used locally instead of CI's 3.12. All requested
  applicable local checks were available and passed; no implementation scope
  deviation was needed.
- Contract violations found: **none**. No new economic/contract-undefined
  semantics were assigned. Existing source errors, rejection retention, first
  receipt snapshots after later transitions, adapter fetch-on-explicit-replay,
  and internal-fault boundaries remain existing behavior, not new guarantees.
- Not tested/claimed: hosted CI, independent review, Move/ZK/localnet workflows,
  external services, real payments/loans, legal/tax/accounting treatment,
  production runtime, durability, concurrent/distributed fencing, bank
  exactly-once, chain finality or production readiness. The touched Python
  tooling does not require those external/resource-dependent checks.
- Follow-up: supervisor commits the final tree, obtains required non-author
  exact-head review and required hosted gates. Product policy and its existing
  owner routes remain UNDETERMINED. No STOP condition was encountered and no
  DECISION_REQUIRED.md was needed.

Local builder delivery state: READY for supervisor handling, not merge-ready.
