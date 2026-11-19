# Admission cancellation portable vectors — builder evidence

Node/task: `plan-plan-commerce-admission-cancellation-vec`. Input: supervisor-supplied node specification and design in this session (no dedicated docs/tasks document, no issue). This is not ASTRA program mode. Historical [Task 005](../../docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md) provides program context only.

Observed local `origin/main`, task starting HEAD and current uncommitted implementation base: `d087cfa0bc77ee6e3969eb3354422f2c3ce5d1e8`. Branch: `agent/kix-plan-plan-commerce-admission-cancellation-vec`. No task/base delta locally. Remote freshness is unverified: the supervisor explicitly forbids network/GitHub actions, overriding the normal §1 fetch step. No fetch, commit, push, PR, issue, comment or merge occurred. Final committed task head, merge SHA and exact-head hosted KTX/KIX CI run IDs/status/conclusions are unavailable; the supervisor owns delivery. No merge-readiness or A2 review is claimed.

[Coverage map recorded before new tests](coverage.md) classifies behavioral coverage as sufficient and portable cancellation consumer coverage as missing. The new source-informed pack contains three histories/26 ordered steps, complete canonical receipts/refusal codes, exact input references and raw-byte source pins. Existing published actions execute through unchanged FsmHost. Tests check TICKET_CANCELLED, TICKET_NOT_ISSUED, CANCEL_AFTER_ISSUE, explicit admission stages, all five machines' refusal atomicity, separate process-local rejected-key bindings and detached negative controls. The companion appends 26 entries while preserving the previous seven packs/267 entries and qualification metadata.

## Local result

READY for supervisor handoff of the uncommitted patch. The three new histories have
7 + 7 + 12 steps with 33 source pins. All 10 focused replay tests pass. The eight
reference-suite runs passed (2,330 total executed tests, including 1,043 in booking,
which contains all Commerce vector/index suites). The cited cancellation regression,
89 admission atomicity tests, 16 document/catalogue/producer/binding checker invocations,
architecture checks, 139 kernel tests, Clippy and formatting also pass. No hosted
CI, independent review or merge-readiness is claimed. Python 3.12.15 and Cargo
1.98.1 were observed locally.

## Actual verification

The tables record commands actually run, including the failed discovery attempt.
The clean final booking-suite run covers every Commerce replay/index test, including
the added rejected-key check. Mixed `05.log` is retained only as diagnostic history;
its two terminal successes are not used as final verification evidence.
[Command ledger](commands.json) and [checker ledger](checker-commands.json) retain
exit codes and measured durations. Tests use `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=.:reference/booking_resale_admission` unless explicitly overridden,
and `CARGO_NET_OFFLINE=true`. The checker runner uses `PYTHONPATH=.`.
[Sequential test runner](run_checks.py) and [checker runner](run_checkers.py) are
retained for reproducibility; neither retries or updates goldens. The executed
checker list is drawn from `.github/workflows/protocol.yml` and `ktx-kernel.yml`.
Heavy Move/ZK/localnet/storage jobs and broader HTTP gate/fault suites were not
run because this patch touches offline fixtures/tests and evidence only. The
requested reference discovery itself includes existing loopback regressions.

| Command | Actual result | Log |
|---|---|---|
| `python3.12 -m unittest test_admission_fsm.AdmissionFsmTests.test_cancel_before_issue_blocks_entry_and_cancel_after_issue_does_not_void_it` | PASS (exit 0); 1 tests | [01.log](01.log) |
| `python3.12 -m unittest test_commerce_admission_cancellation_vectors` | PASS (exit 0); 9 tests | [02.log](02.log) |
| `python3.12 -m unittest test_admission_rejection_atomicity` | PASS (exit 0); 89 tests | [03.log](03.log) |
| `python3.12 -m unittest test_commerce_companion_evidence_index` | PASS (exit 0); 7 tests | [04.log](04.log) |
| `python3.12 -m unittest test_commerce_admission_cancellation_vectors` | PASS (exit 0); mixed log, superseded | [05.log](05.log) |
| `python3.12 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0); 224 tests | [06.log](06.log) |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | FAIL (exit 1) | [07.log](07.log) |
| `python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS (exit 0); 284 tests | [08.log](08.log) |
| `python3.12 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS (exit 0); 169 tests | [09.log](09.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0); 397 tests | [10.log](10.log) |
| `python3.12 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS (exit 0); 86 tests | [11.log](11.log) |
| `python3.12 -m unittest discover -s reference/payment_effects -t reference/payment_effects` | PASS (exit 0); 28 tests | [12.log](12.log) |
| `python3.12 -m unittest discover -s reference/economics -t reference/economics` | PASS (exit 0); 99 tests | [13.log](13.log) |
| `python3.12 -m unittest integration_gate.test_offline_limits` | PASS (exit 0); 9 tests | [14.log](14.log) |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p "test_commerce_*.py"` | PASS (exit 0); mixed log, superseded | [05.log](05.log) |
| `python3.12 -m unittest test_commerce_admission_cancellation_vectors` | PASS (exit 0); 10 tests | [16.log](16.log) |
| `PYTHONPATH=. python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0); 1043 tests | [17.log](17.log) |
| `git diff --check` | PASS (exit 0) | [18.log](18.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/verify_preservation.py` | PASS (exit 0) | [19.log](19.log) |
| `python3.12 scripts/check_docs_index.py` | PASS (exit 0) | [checker-01.log](checker-01.log) |
| `python3.12 scripts/check_docs_index.py --self-test` | PASS (exit 0) | [checker-02.log](checker-02.log) |
| `python3.12 scripts/check_ci_test_discovery.py` | PASS (exit 0) | [checker-03.log](checker-03.log) |
| `python3.12 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) | [checker-04.log](checker-04.log) |
| `python3.12 scripts/check_ci_checker_wiring.py` | PASS (exit 0) | [checker-05.log](checker-05.log) |
| `python3.12 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) | [checker-06.log](checker-06.log) |
| `python3.12 scripts/check_openapi_contract.py` | PASS (exit 0) | [checker-07.log](checker-07.log) |
| `python3.12 scripts/check_openapi_contract.py --self-test` | PASS (exit 0) | [checker-08.log](checker-08.log) |
| `python3.12 scripts/check_integration_gate_openapi.py` | PASS (exit 0) | [checker-09.log](checker-09.log) |
| `python3.12 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) | [checker-10.log](checker-10.log) |
| `python3.12 scripts/check_bra_evidence_map.py` | PASS (exit 0) | [checker-11.log](checker-11.log) |
| `python3.12 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0) | [checker-12.log](checker-12.log) |
| `python3.12 scripts/check_producer_qualification_tuple.py` | PASS (exit 0) | [checker-13.log](checker-13.log) |
| `python3.12 scripts/check_producer_qualification_tuple.py --self-test` | PASS (exit 0) | [checker-14.log](checker-14.log) |
| `python3.12 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | PASS (exit 0) | [checker-15.log](checker-15.log) |
| `python3.12 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | PASS (exit 0) | [checker-16.log](checker-16.log) |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS (exit 0) | [checker-17.log](checker-17.log) |
| `python3.12 scripts/test_runtime_architecture.py` | PASS (exit 0); 7 tests | [checker-18.log](checker-18.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS (exit 0); 139 tests | [checker-19.log](checker-19.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS (exit 0) | [checker-20.log](checker-20.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) | [checker-21.log](checker-21.log) |

## Preservation and limits

[Before inventory](preservation-before.json) records raw-byte SHA-256 and Git blob IDs for 341 protected/prior source paths. [After comparison](preservation-after.json) verifies 4,220 unchanged tracked paths, including all 108 frozen reference files, the 341-path before inventory and both locked blobs. [Read-only verifier](verify_preservation.py) also checks the serialized original seven-pack prefix and unchanged qualification metadata. Locked blobs after work match the before values; no merge occurred, so no merge-blob check applies. Locked blobs before work match `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`.

No contract violation or new contract-undefined behavior has been identified in these histories. Existing payment-compensation and admission clock-skew boundaries are not changed; no new precedence/policy is inferred. Synthetic inputs are examples only. Policy values remain UNDETERMINED—Astra/User; legal effects remain UNDETERMINED—User/legal. Semantic consumption HOLD_SEMANTIC, all 13 reads NOT_BOUND, SD1 OPEN/User-owned and external acceptance UNVERIFIED remain. No runtime, producer, catalogue, SDK, original binding index, prior vectors, contracts, locked kernel, reference/v0.3-rc1, .aiops or task-document change is authorized.

These tests establish local source-informed mock behavior/byte identity only: no clean-room independence, external consumer acceptance, venue admission, authenticity, legal compliance, distributed fencing, finality, durability, production readiness or real money/provider/chain execution. The new vector pack opens no sockets or external services. The explicitly requested existing broad booking regression includes its pre-existing loopback HTTP test; its local logs are retained. No public endpoint or external service was contacted. A2 non-author exact-head review and hosted exact-head CI remain supervisor follow-ups.

## Deviations

- The supervisor forbids network/GitHub actions, so the normal fetch was omitted; local origin/main freshness is unverified. No dedicated task document exists for this loop-proposed node; the supplied specification/design is the immutable task input, and historical Task 005 was read only as context.
- The design's global `PYTHONPATH=.:reference/booking_resale_admission` caused an existing duplicate-module discovery collision in the full booking suite (`test_contract_error_codes` resolved from settlement). The corrected full-suite invocation uses `PYTHONPATH=.` so unittest places the discovery root first, as CI does. No producer, old test, or CI source was changed.
- Two early validation invocations overlapped and accidentally shared `05.log`; their actual successful terminal results are recorded with explicit mixed-log notes. That log is retained and excluded from final evidence claims; clean final focused/full-suite verification supersedes it. Subsequent validation commands run sequentially within their ledger.
- Four transient authoring/validation helpers were initially created under `/tmp`, contrary to the worktree-only instruction. They were removed; reusable validation runners are now in this evidence directory. There are no retained helper changes outside the worktree.
- The new pack uses the existing entry/resale-order detached snapshot helper directly. It includes complete machine state/digest/journals in each output diagnostic, as proposed for this pack. Prior fixtures and helper files remain byte-identical.

Fixture construction was a one-time source-informed capture through `_observe`, checked against independent phase/refusal/order expectations and the cited existing regression. There is no golden update mode in the replay tests. No contract discrepancy was concealed by regeneration.

## Complete changed-path list

[Every changed/new path](changed-paths.txt) is listed below. No Git index or history
was changed. Current HEAD remains the starting SHA; there is no committed
implementation/final-task SHA yet. Hosted exact-head KTX and KIX run IDs,
status and conclusion, A2 non-author review, merge SHA and post-merge CI are
NOT RUN / unavailable in this supervisor-owned delivery. Local READY means
ready to hand off this working-tree patch, not merge-ready.

- `docs/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_admission_cancellation_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_admission_cancellation_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_admission_cancellation_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/01.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/02.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/03.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/04.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/05.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/06.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/07.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/08.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/09.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/10.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/11.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/12.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/13.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/14.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/16.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/17.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/18.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/19.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/README.md`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/changed-paths.txt`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-01.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-02.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-03.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-04.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-05.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-06.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-07.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-08.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-09.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-10.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-11.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-12.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-13.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-14.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-15.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-16.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-17.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-18.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-19.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-20.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-21.log`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/checker-commands.json`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/commands.json`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/coverage.md`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/finalize_report.py`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/preservation-after.json`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/preservation-before.json`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/run_checkers.py`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/run_checks.py`
- `validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/verify_preservation.py`
