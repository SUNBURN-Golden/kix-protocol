# plan-local-credit-desk — local builder evidence

Node: `plan-local-credit-desk`, SUNBURN-Golden/kix-protocol. Issue: none.
Task input: the supervisor-supplied node specification and read-only design in
this session; there is no task document under `docs/tasks/` for this node.
Dependencies: `f04-mock-deepening`, `settlement-policy-deepening`,
`plan-local-reward-desk`. Audit floor A2; not ASTRA program mode.

## Identity and gates

| Item | Observed value |
|---|---|
| Branch | `agent/kix-plan-local-credit-desk` |
| Local `origin/main` and initial task HEAD | `121e0bde37c23c458b6cb4c54e4e650ba1315d92` |
| Base delta against local ref | none |
| Fetch | NOT_RUN: supervisor explicitly prohibits network/GitHub actions, overriding AGENTS §1 fetch |
| Implementation/final task commit | none created; supervisor owns git. Working-tree delivery only |
| Merge commit / post-merge CI | not applicable; no merge |
| Exact-final-head KTX CI | NOT_RUN; no run ID/status/conclusion available |
| Exact-final-head KIX CI | NOT_RUN; no run ID/status/conclusion available |
| A2 non-author exact-final-head review | pending supervisor workflow; builder checks are not independent review |

No commit, push, PR, issue, comment, tag, branch mutation or merge was performed.
No prior CI result transfers to the supervisor's eventual final head. Completed,
successful KTX and KIX exact-head CI and non-author review remain required before
any merge proposal, together with explicit human merge authorization.

## Coverage map (before adding tests)

Existing paths below are under `reference/credit_advance_f04/` unless fully
qualified. The FSM, mock and open-terms modules are unchanged. New tests address
desk boundaries only.

| Requirement | Existing evidence and classification | New gap coverage |
|---|---|---|
| Offer/approve/draw/repay/close lifecycle and mock-exposure flags | sufficiently covered: `test_credit_fsm.py::CreditFsmTests.test_offer_approve_draw_repay_and_close_are_mock_ledger_only` and the flag/ledger assertions throughout that module | lifecycle transcript asserts phases, effects, `assert_not_lending` on every emitted receipt/view, historical `duplicate`/`applied` replay envelopes |
| Bound draw COMMITTED gate and settlement view predicates | sufficiently covered: `test_credit_fsm.py` COMMITTED/CAPTURED/FAILED book cases (gate, mismatch, binding, unknown source paths) | `settlement_gates`/`gate` transcripts exercise `SETTLEMENT_AMOUNT_MISMATCH`, `UNKNOWN_SETTLEMENT`, `SETTLEMENT_BINDING_CONFLICT`, `SETTLEMENT_NOT_COMMITTED`, `SETTLEMENT_SOURCE_REQUIRED` and the `UNBOUND`/`BOUND`/`MOCK_COMMIT_OBSERVED` view ladder through a fixture-built real `SettlementMachine` |
| Idempotency, first-result replay, stored rejections | sufficiently covered: `test_credit_fsm.py` duplicate/conflict cases; `test_credit_rejection_atomicity.py` | transcripts assert `duplicate:true`/`applied:null` replays, stored-rejection replay (`SETTLEMENT_NOT_COMMITTED` repeated), and `IDEMPOTENCY_CONFLICT` leaving the stored request intact |
| Terminal immutability and decline paths | sufficiently covered: `test_credit_fsm.py` reject/cancel/default/close terminal checks | `decline` transcript asserts REJECTED/CANCELLED/DEFAULTED views, retained `NOTED` note status and `TERMINAL_IMMUTABLE` fencing |
| Repayment order/binding and face predicates | sufficiently covered: `test_credit_fsm.py`, `test_mock_credit.py`, `test_credit_properties.py` (order, exceed, binding, face parse matrices) | `boundaries` transcript is a 29-code matrix including `REPAYMENT_ORDER`, `REPAYMENT_EXCEEDS_OUTSTANDING`, `REPAYMENT_BINDING_CONFLICT`, `FACE_SNAPSHOT_FROZEN`, `REFUND_OBLIGATION_OPEN`, `ADVANCE_EXCEEDS_OPEN_FACE`, `CREDIT_PRODUCT_UNDEFINED`, `INVALID_AMOUNT`, `INVALID_ID` |
| Journal reconcile determinism | sufficiently covered: `test_credit_fsm.py` and `test_restore_fingerprint_equivalence.py` | reconcile transcript asserts `matched:true`, `entry_count`, 64-hex `state_digest` and duplicate replay |
| Forwarding/optional omission, no implicit sources | not covered for the new session | `test_credit_session.py`: signature parity for all 12 operations, `product=None`/explicit forwarding, source constructor forwarding, `SETTLEMENT_SOURCE_REQUIRED` proving no implicit source, session isolation, transcript face vs fixture claim equality |
| Strict JSON/shape/serialization and no malformed dispatch | not covered for the new desk | `test_credit_cli.py`: nested duplicates, non-finite/overflow, invalid JSON/Unicode, all missing/extra arguments and unsupported selectors (incl. `restore`, `export_journal`, `canonical_state`, `attempt_execution`, `reject_unsupported`), non-dict `face`, non-JSON Python values, fixture schema/setup whitelist; dispatch spies |
| CLI exit behavior, stop boundary, file/stdin parity and determinism | not covered | `test_credit_cli.py`: real subprocess journeys, repeated byte-identical output, file/stdin parity, domain continuation, malformed stop without consuming idempotency, setup/I/O failures, settlement setup rejection codes at exit 2 |

The new suites contain 6 session and 13 CLI tests. These are builder-authored,
source-informed checks, not clean-room verification.

## Runnable transcripts

The fixture directory is `reference/credit_advance_f04/fixtures/`. Each row's
`--fixture` selects the session source; the `--requests` argument supplies the
only operations performed.

| Fixture | Request input | Expected exit | Evidence output |
|---|---|---|---|
| `committed.json` | `--requests reference/credit_advance_f04/fixtures/lifecycle.jsonl` | 0 | [lifecycle.stdout.jsonl](lifecycle.stdout.jsonl) |
| `committed.json` | `--requests reference/credit_advance_f04/fixtures/settlement_gates.jsonl` | 1 (explicit semantic refusals) | [settlement_gates.stdout.jsonl](settlement_gates.stdout.jsonl) |
| `captured.json` | `--requests reference/credit_advance_f04/fixtures/gate.jsonl` | 1 (explicit semantic refusals) | [gate.stdout.jsonl](gate.stdout.jsonl) |
| `unbound.json` | `--requests reference/credit_advance_f04/fixtures/decline.jsonl` | 1 (terminal fencing refusal) | [decline.stdout.jsonl](decline.stdout.jsonl) |
| `unbound.json` | `--requests reference/credit_advance_f04/fixtures/boundaries.jsonl` | 1 (explicit semantic refusals) | [boundaries.stdout.jsonl](boundaries.stdout.jsonl) |

Every transcript is executed twice and compared byte-for-byte during capture;
CLI tests also compare file/stdin interfaces, expected payloads and exit codes.
Recorded JSONL is synthetic output evidence, not a persistence/restoration format.

## Commands and results

Results below come from actual foreground executions. No hosted workflow
or background long job is started. CI definitions inspected:
`.github/workflows/protocol.yml` and `.github/workflows/ktx-kernel.yml`.
Python 3.13.5 is the local default; Python 3.12.15 is also available for the CI pin.

All Python commands below ran with `PYTHONDONTWRITEBYTECODE=1`. Actual stdout/stderr, exit codes, transcript notes and the complete path list are in [commands.json](commands.json).

| Command actually run | Actual result |
|---|---|
| `PYTHONPATH=reference/credit_advance_f04 python3 -m unittest test_credit_session test_credit_cli` | exit 0; 19 tests passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_credit_session.py` | exit 0; 6 tests passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_credit_cli.py` | exit 0; 13 tests passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 167 tests passed |
| `python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 167 tests passed |
| `python3 -m unittest discover` per CI loop for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward`, `provider_facts` | exit 0 each; 224/838/167/85/186/73 tests passed |
| `python3 scripts/check_docs_index.py` | exit 0; docs index ok: scanned=358 indexed=323 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_ci_test_discovery.py` | exit 0; reference/credit_advance_f04 files=10 reached by existing workflow loop; reference_suites=7 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0; pass (18 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | exit 0; rows=22 headings=22 items=5 citations=128 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | exit 0; pass (55 negative controls) |
| `python3 scripts/check_evidence_map_rollup.py` | exit 0; contracts=25 |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | exit 0; pass (16 negative controls) |
| `python3 scripts/check_status_register.py` | exit 0; paths=457 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_class_b_index.py` | exit 0; rows=218 sources=73 symbols=47 |
| `python3 scripts/check_class_b_index.py --self-test` | exit 0; pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0; scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0; pass (13 negative controls) |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0; rows=49 expected=49 citations=58 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_openapi_contract.py` | exit 0; commands=84 core=40 fsm=44 |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0; commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0; self-test pass |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; unavailable offline dependency `bcs`; no Rust tests executed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; unavailable offline dependency `bcs` |
| `git diff --check` | exit 0 |
| `python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/lifecycle.jsonl` | exit 0; 15 JSONL lines; two runs and one stdin run byte-identical |
| `python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/settlement_gates.jsonl` | exit 1; 17 JSONL lines; byte-identical across file/repeat/stdin |
| `python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/captured.json --requests reference/credit_advance_f04/fixtures/gate.jsonl` | exit 1; 13 JSONL lines; byte-identical across file/repeat/stdin |
| `python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/unbound.json --requests reference/credit_advance_f04/fixtures/decline.jsonl` | exit 1; 14 JSONL lines; byte-identical across file/repeat/stdin |
| `python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/unbound.json --requests reference/credit_advance_f04/fixtures/boundaries.jsonl` | exit 1; 51 JSONL lines; byte-identical across file/repeat/stdin |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0; both required blobs match before and after |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime reference/credit_advance_f04/credit_fsm.py reference/credit_advance_f04/mock_credit.py reference/credit_advance_f04/open_terms.py` | exit 0; protected/model paths unchanged against local origin/main |

| Required check not run | Reason |
|---|---|
| `git fetch origin main` | Supervisor explicitly prohibits network actions. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` (CI form) | Offline crate resolution fails on `bcs`; no network fetch authorized. No `runtime/` paths change. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` (CI form) | Same offline `bcs` resolution failure; `-p kix-kernel` variant recorded. |
| `Hosted exact-final-head KTX and KIX workflows` | No commit/publication authorized; supervisor owns git and GitHub. |

Rust environment discovery: `rustup toolchain list` reports
`1.98.1-x86_64-unknown-linux-gnu` active with `cargo`, `clippy`, `rustfmt`,
`rustc` components; `cargo --version` reports 1.98.1 matching the repository
pin. `/usr/bin/cargo` and `/usr/bin/rustc` report 1.85.1. The offline test and
clippy attempts used the rustup toolchain with `--locked --offline`; both stop
at dependency resolution because `bcs` (required by workspace member
`kix-bcs1`) is not vendored. `cargo fmt --check` needs no dependencies and
passed. These environment limitations are not counted as failing Rust checks;
no `runtime/` path changed.

Final historical-reference check: all 108 tracked `reference/v0.3-rc1/` files
are byte-identical to `origin/main` (`git diff --exit-code` row above);
`sha256sum` manifest digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`.
Both locked blobs match.

## Preservation

Before edits both kernel Git blobs matched their required values:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`quarantine_capacity.rs`).
Final preservation checks are recorded in the actual-results table.

## Classification, limitations and deviations

Class A: desk outputs preserve the existing FSM's open-face reservation, gate
and idempotency semantics within this synthetic process. No explicit contract
violation was found. No authoritative contract was amended.

Class B behavior remains unchanged: stored rejections are not journaled;
`MOCK_INVARIANT`, `IDEMPOTENCY_CONFLICT` and `INVALID_JOURNAL` rejections are
never stored; `reconcile` shares the injected sources and is a determinism
witness, not durable recovery. See the existing
[rejection-atomicity coverage](../../reference/credit_advance_f04/test_credit_rejection_atomicity.py)
and the [F04 contract evidence map](../../docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md).
The desk changes none of these and offers no restoration or rollback guarantee.

Design deviations: the plan's four transcripts became five — `lifecycle.jsonl`
stays a clean exit-0 happy path mirroring `participation.jsonl`, and the
committed-fixture binding/gate refusal cases moved into
`settlement_gates.jsonl`. Strict-JSON boundary coverage is folded into
`test_credit_cli.py` per the plan rather than a third module. `initiate`'s
`currency` and `commit`'s `adjustment_reason` are optional fixture fields
matching the machine signatures; all other setup body fields are required.
`ownership_source` stays a Python-level constructor argument only: no local
ownership fixture exists without pulling the booking graph, and embedders pass
it directly. The `face` embedded in each transcript is captured verbatim from
`book.view("claim-1")["claim"]` of the fixture-built book (`gate` uses the
captured claim; the unbound transcripts use the committed claim); the
mismatch/refund/variant faces are documented caller-supplied modifications, not
desk derivations.

No policy value was chosen. Synthetic identifiers, amounts, faces, reasons and
the fee policy are explicit fixtures only. `open_terms` stays UNDETERMINED
under adopted option A; policy numbers, lender/borrower identity, APR, rank,
perfection and limit recalculation remain UNDETERMINED with their named owners.
No STOP condition requiring any of those decisions is needed by this in-memory
desk.

No real money, provider/KYC/bank calls, public endpoint, secrets, production
runtime, Sui testnet/mainnet, coin/TIX module, protocol command, storage
engine, repayment-note synthesis, claim-snapshot adapter or statement-coupled
workbench. All false production flags are retained on every emitted receipt,
view and claim. No durability, chain finality, bank exactly-once,
legal-compliance, runtime activation or production readiness claim. Unrelated
Move/SDK/ZK/localnet/storage paths and full hosted workflows are NOT_RUN.
Remaining work belongs to the supervisor: commit the final content, obtain A2
non-author exact-head review and exact-head KTX/KIX CI. Possible future changes
to Class B behavior need a separately authorized task.

## Changed paths

- `docs/README.md`
- `reference/credit_advance_f04/README.md`
- `reference/credit_advance_f04/credit_cli.py`
- `reference/credit_advance_f04/credit_fixture.py`
- `reference/credit_advance_f04/credit_session.py`
- `reference/credit_advance_f04/fixtures/boundaries.jsonl`
- `reference/credit_advance_f04/fixtures/captured.json`
- `reference/credit_advance_f04/fixtures/committed.json`
- `reference/credit_advance_f04/fixtures/decline.jsonl`
- `reference/credit_advance_f04/fixtures/gate.jsonl`
- `reference/credit_advance_f04/fixtures/lifecycle.jsonl`
- `reference/credit_advance_f04/fixtures/settlement_gates.jsonl`
- `reference/credit_advance_f04/fixtures/unbound.json`
- `reference/credit_advance_f04/test_credit_cli.py`
- `reference/credit_advance_f04/test_credit_session.py`
- `validation/2026-11-05-plan-local-credit-desk/README.md`
- `validation/2026-11-05-plan-local-credit-desk/boundaries.stdout.jsonl`
- `validation/2026-11-05-plan-local-credit-desk/commands.json`
- `validation/2026-11-05-plan-local-credit-desk/decline.stdout.jsonl`
- `validation/2026-11-05-plan-local-credit-desk/gate.stdout.jsonl`
- `validation/2026-11-05-plan-local-credit-desk/lifecycle.stdout.jsonl`
- `validation/2026-11-05-plan-local-credit-desk/settlement_gates.stdout.jsonl`

## PR fix round 1 — duplicate surrogate keys

This is a separate follow-up record; the implementation-run results above remain
historical. Task input is the supervisor's `plan-local-credit-desk` fix-round-1
instruction and blocking review finding; no node task document or issue exists.
Branch: `agent/kix-plan-local-credit-desk`. Observed local `origin/main` remains
`121e0bde37c23c458b6cb4c54e4e650ba1315d92`; implementation and initial round HEAD
is `ff26605884d6eec6d6a3239744dd25c3b8eadc60`. The implementation record's base
matches that local main ref. Fetch is NOT_RUN because the supervisor forbids
network actions; current remote main is unverified. No rebase/base change,
commit, push or publication was performed. Final task head is pending the
supervisor's commit; no merge commit or post-merge check applies.

Finding accepted and reproduced: `_object` detects duplicates before
`validate_json` validates Unicode. Interpolating the raw duplicate key into the
diagnostic allowed `\udc80` to reach UTF-8/surrogateescape stdout as byte `0x80`.
The fix formats the key with `json.dumps(key, ensure_ascii=True)`, so even
unvalidated keys produce an escaped, printable diagnostic. CLI serialization,
FSM methods, domain error codes and policy values are unchanged.

Coverage mapping before this fix: strict decoder tests sufficiently cover ordinary
duplicate keys, and separately cover lone surrogates; their combination at the
subprocess byte boundary was not covered. The new
`test_credit_cli.py::CreditCliTests.test_duplicate_surrogate_keys_emit_utf8_json_errors_in_subprocess`
fills that gap with 12 cases: low/high surrogate keys, top-level/nested request
and fixture inputs, and UTF-8 stdout with surrogateescape/strict errors. It
strictly decodes stdout bytes, checks the complete `FixtureError` envelope,
exit 2, empty stderr, and exactly one output despite a following valid request.
This is builder-authored, source-informed regression evidence.

| Command actually run | Result |
|---|---|
| `PYTHONPATH=reference/credit_advance_f04 python3 -m unittest test_credit_cli.CreditCliTests.test_duplicate_surrogate_keys_emit_utf8_json_errors_in_subprocess` before fix | exit 1; 1 test, 12 subcases: 9 failures, 3 errors; the three errors reproduce invalid UTF-8 byte `0x80` |
| Same targeted command after fix | exit 0; 1 test, all 12 subcases pass |
| `PYTHONPATH=reference/credit_advance_f04 python3 -m unittest test_credit_session test_credit_cli` | exit 0; 20 tests pass |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 168 tests pass |
| `python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; 168 tests pass |
| `python3 scripts/check_docs_index.py` and `--self-test` | both exit 0; scanned=358, indexed=323, allowlisted=35; self-test pass |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | both exit 0; F04 files=10 reached by existing workflow loop; 18 negative controls pass |
| `python3 scripts/check_credit_evidence_map.py` and `--self-test` | both exit 0; rows=22, citations=128; 55 negative controls pass |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before/after | both required blobs match: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime` | exit 0; protected paths unchanged |
| `git rev-parse HEAD:reference/v0.3-rc1 origin/main:reference/v0.3-rc1` | both tree IDs `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; working-tree diff also empty |
| `git diff --check` | exit 0 |

Python checks ran with `PYTHONDONTWRITEBYTECODE=1`. Raw check outputs and the
reproduction result are in [fix-round-1.commands.json](fix-round-1.commands.json).
The existing protocol workflow's F04 discover loop and both CI definitions were
inspected; no CI changes were made. No CI failure was supplied. Hosted exact-head
KTX and KIX run IDs/status/conclusions are unavailable and were not inspected
(network prohibited). The supervisor must obtain non-author exact-head review
and both completed/success workflows for the eventual final commit. Local READY
means ready for supervisor delivery, not merge-ready or merge authorization.

Complete changed paths for this fix round:

- `reference/credit_advance_f04/credit_fixture.py`
- `reference/credit_advance_f04/test_credit_cli.py`
- `validation/2026-11-05-plan-local-credit-desk/README.md`
- `validation/2026-11-05-plan-local-credit-desk/fix-round-1.commands.json`

No domain contract violation or new contract-undefined characterization was
found; this fixes the documented strict-JSON boundary. Existing Class B
characterizations above remain unchanged. No STOP dependency, product policy,
protocol command or external execution is needed. Rust/runtime, unrelated suites,
Move, Sui and production behavior were not tested in this round; scope is the
local Python decoder and CLI. No durability, financial, legal or production
readiness claim follows. Remaining uncertainty is remote main freshness and the
supervisor's eventual exact-head review/CI; no further in-scope code fix is known.
