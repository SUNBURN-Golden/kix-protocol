# Resale expiry portable histories — builder evidence

Task ID: `plan-plan-commerce-resale-expiry-vectors`. Task document: the
supervisor-provided node specification/design in this session; no issue or
new `docs/tasks/` document. This is not ASTRA program mode.

Two complete source-informed input/outcome histories exercise only published
in-process `FsmHost` actions: unpaid listing expiry (12 steps), paid listing
expiry before transfer (15 steps). Expiry is a diagnostic condition, not a
phase. Original-key listing/payment replay preserves the historical first
receipt after clock advancement. Late payment/transfer reject
`LISTING_NOT_OPEN`; paid seller cancellation rejects `COMPENSATION_UNDEFINED`.
Payment facts, holder `buyer-1`, version `1`, and absence of transfer and
compensation are preserved. The seventh companion family adds exactly 27
entries while preserving the previous 240 entries and qualification metadata.

[Coverage mapping](coverage.md) was written before adding tests. New tests fill
the portable-history gap, compare complete canonical outcome bytes and source
pins, check all five machines for rejection/replay non-mutation, and use detached
negative controls for changed errors/facts/diagnostics, order, omissions,
duplicates and crossed references. Re-pinned malformed inputs reach semantic
checks. Injected effects verify non-mutation guards. Companion controls now
cover all seven families and re-pinned malformed outcomes in every grouped pack.

## Repository identity and preservation

- Branch: `agent/kix-plan-plan-commerce-resale-expiry-vectors`.
- Local observed `origin/main`, task base and initial HEAD:
  `3a119fcfa9b784f67082a667ee499a018fc4e7ce`; no local delta.
- Final branch HEAD remains that SHA: implementation is an uncommitted worktree
  patch for the supervisor. No final committed implementation SHA exists here.
- No merge commit; no commit, push, PR, issue, comment, fetch, other network
  operation or background job was performed.
- `git fetch origin main` was deliberately omitted under the supervisor's
  explicit no-network rule; freshness beyond the local ref is unverified.
- Before/after [preservation inventories](preservation-before.json) and
  [results](preservation-results.json) cover existing reference sources/fixtures,
  contracts, SDK, task inputs, `.aiops/`, CI, producer/binding metadata and locks.
  The initial full 4,155-file tracked inventory was compared before retaining
  the focused 859-file inventory: only the six authorized tracked paths differed.
- Locked blobs before and after:
  `runtime/crates/kix-kernel/src/lib.rs` =
  `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
  `b607996c83a119c349f1cc90469ac1ba82764e20`.
- All 108 tracked `reference/v0.3-rc1/**` files remain byte-identical, as do
  previous vectors/helpers, producer sources, contracts, SDK, binding index,
  producer tuple, CI, task documents and `.aiops/`.

## Actual local verification

Commands and full stdout/stderr are recorded in the adjacent logs and
`*-results.json`. `run_checks.py` runs sequential existing offline checks with
no automatic retry or golden update. The command/result table below records completed checks; full command arrays
and log paths are in the adjacent JSON. No hosted CI result is inferred from local checks.

## Deviations and limits

The design's payment-amount preservation assertion uses the existing
`listing.amount` plus the accepted payment journal's exact amount/reference;
there is no `payment_amount` view field. No producer or schema was changed.
The first temporary fixture-authoring helper invocation failed with
`ModuleNotFoundError: integration_gate` because `/tmp` was its import root;
setting `PYTHONPATH=.` corrected that invocation before outcome publication.
An initial workflow read used absent `ktx.yml`; the actual `ktx-kernel.yml` was
then inspected. Neither setup issue was a behavior/test failure.

The first broad offline run failed one unchanged provider-facts CLI test when a
child process exceeded its fixed 10-second timeout. A targeted diagnostic run
also timed out, at a different invalid input. Inspection found only simple
validation in these cases and a local harness mismatch: parent `-B` was not
inherited by child processes, whereas `protocol.yml` explicitly sets
`PYTHONDONTWRITEBYTECODE=1`. The validation runner was corrected to propagate
that CI setting. With it, the full provider-facts suite passed all 86 tests,
as did the remaining offline suites. The original failure and diagnostic logs
are retained; timeout causality is **not established**. No provider source,
test timeout or CI configuration was changed, and no blind retry loop was used.

No contract violation was found. Product TTL and compensation policy remain
**UNDETERMINED** with Astra/User and existing legal/accounting owners. There is
no new refund, compensation, relisting, transfer behavior, command or policy.
Synthetic times are fixture inputs, not approved product defaults.

All 13 reads remain **NOT_BOUND**, semantic consumption **HOLD_SEMANTIC**,
SD1 **OPEN/User-owned/unresolved**, and external consumer acceptance
**UNVERIFIED**. Diagnostic snapshots are local observations, not read APIs.
Rejected-key retention is process-local, outside the business snapshot/journal;
no durable recovery claim follows. There is no clean-room independence, real
funds/provider invocation, public endpoint, Sui execution, production runtime,
chain/funds finality, legal compliance or production-readiness claim.

Hosted exact-head KTX CI: **NOT_RUN**, run ID/status/conclusion unavailable.
Hosted exact-head KIX protocol CI: **NOT_RUN**, run ID/status/conclusion
unavailable. Post-merge CI: not applicable (no merge). A2 non-author exact-head
review remains for the supervisor; this builder does not claim independent
review, merge readiness or external acceptance. Unrelated hosted Move/ZK/chain
and production/storage workflow stages were not run for this fixture/doc patch.

## Command results and changed paths

The final corrected offline CI loop passed **2,321 tests** (eight suites plus
`integration_gate.test_offline_limits`). Kernel tests passed **139 tests**;
Clippy and formatting passed. The initial timeouts are retained below rather
than replaced by the later successes. No test count is a coverage claim.

Exact argument arrays, elapsed times and logs are in
[focused-results.json](focused-results.json), [offline-results.json](offline-results.json),
[diagnostic-results.json](diagnostic-results.json),
[offline-tail-results.json](offline-tail-results.json),
[offline-ci-results.json](offline-ci-results.json),
[checkers-results.json](checkers-results.json), and [ktx-results.json](ktx-results.json).
The first broad run used parent `-B` without the inherited bytecode environment;
`offline-tail` and `offline-ci` explicitly propagated the CI setting. The runner
was fixed between those runs; historical results describe the commands actually
run, not the runner's final source retroactively.

| Run | Command | Result | Actual output |
|---|---|---|---|
| focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_resale_expiry_vectors.py -v` | PASS (exit 0); 8 tests | [expiry-tests.log](expiry-tests.log) |
| focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_resale*.py' -v` | PASS (exit 0); 228 tests | [resale-tests.log](resale-tests.log) |
| focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_*.py' -v` | PASS (exit 0); 142 tests | [commerce-tests.log](commerce-tests.log) |
| focused | `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_companion_evidence_index.py -v` | PASS (exit 0); 6 tests | [companion-tests.log](companion-tests.log) |
| offline | `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0); 224 tests | [offline-01.log](offline-01.log) |
| offline | `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0); 1032 tests | [offline-02.log](offline-02.log) |
| offline | `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS (exit 0); 277 tests | [offline-03.log](offline-03.log) |
| offline | `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS (exit 0); 169 tests | [offline-04.log](offline-04.log) |
| offline | `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0); 397 tests | [offline-05.log](offline-05.log) |
| offline | `/home/box/.local/bin/python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | FAIL (exit 1); 86 tests; subprocess timeout | [offline-06.log](offline-06.log) |
| offline-tail | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS (exit 0); 86 tests | [offline-tail-01.log](offline-tail-01.log) |
| offline-tail | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/payment_effects -t reference/payment_effects` | PASS (exit 0); 28 tests | [offline-tail-02.log](offline-tail-02.log) |
| offline-tail | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/economics -t reference/economics` | PASS (exit 0); 99 tests | [offline-tail-03.log](offline-tail-03.log) |
| offline-tail | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest integration_gate.test_offline_limits` | PASS (exit 0); 9 tests | [offline-tail-04.log](offline-tail-04.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0); 224 tests | [offline-ci-01.log](offline-ci-01.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0); 1032 tests | [offline-ci-02.log](offline-ci-02.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS (exit 0); 277 tests | [offline-ci-03.log](offline-ci-03.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS (exit 0); 169 tests | [offline-ci-04.log](offline-ci-04.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0); 397 tests | [offline-ci-05.log](offline-ci-05.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS (exit 0); 86 tests | [offline-ci-06.log](offline-ci-06.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/payment_effects -t reference/payment_effects` | PASS (exit 0); 28 tests | [offline-ci-07.log](offline-ci-07.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest discover -s reference/economics -t reference/economics` | PASS (exit 0); 99 tests | [offline-ci-08.log](offline-ci-08.log) |
| offline-ci | `PYTHONDONTWRITEBYTECODE=1 /home/box/.local/bin/python3.12 -B -m unittest integration_gate.test_offline_limits` | PASS (exit 0); 9 tests | [offline-ci-09.log](offline-ci-09.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_openapi_contract.py` | PASS (exit 0) | [checkers-01.log](checkers-01.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_openapi_contract.py --self-test` | PASS (exit 0) | [checkers-02.log](checkers-02.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_integration_gate_openapi.py` | PASS (exit 0) | [checkers-03.log](checkers-03.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) | [checkers-04.log](checkers-04.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_docs_index.py` | PASS (exit 0) | [checkers-05.log](checkers-05.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_docs_index.py --self-test` | PASS (exit 0) | [checkers-06.log](checkers-06.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_ci_test_discovery.py` | PASS (exit 0) | [checkers-07.log](checkers-07.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) | [checkers-08.log](checkers-08.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_ci_checker_wiring.py` | PASS (exit 0) | [checkers-09.log](checkers-09.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) | [checkers-10.log](checkers-10.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_producer_qualification_tuple.py` | PASS (exit 0) | [checkers-11.log](checkers-11.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/check_producer_qualification_tuple.py --self-test` | PASS (exit 0) | [checkers-12.log](checkers-12.log) |
| checkers | `/home/box/.local/bin/python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | PASS (exit 0) | [checkers-13.log](checkers-13.log) |
| checkers | `/home/box/.local/bin/python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | PASS (exit 0) | [checkers-14.log](checkers-14.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/verify_runtime_architecture.py` | PASS (exit 0) | [checkers-15.log](checkers-15.log) |
| checkers | `/home/box/.local/bin/python3.12 -B scripts/test_runtime_architecture.py` | PASS (exit 0); 7 tests | [checkers-16.log](checkers-16.log) |
| ktx | `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS (exit 0) | [ktx-01.log](ktx-01.log) |
| ktx | `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS (exit 0) | [ktx-02.log](ktx-02.log) |
| ktx | `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) | [ktx-03.log](ktx-03.log) |
| diagnostic | `PYTHONPATH=reference/provider_facts python3.12 -B -m unittest test_payment_lookup_cli.PaymentLookupCliTests.test_invalid_entire_configuration_precedes_all_lookup_and_binding -v` | FAIL (exit 1); subprocess timeout | [provider-timeout-diagnostic.log](provider-timeout-diagnostic.log) |

The [complete changed-path list](changed-paths.txt) includes all evidence files.
[Artifact pins](artifacts.json) identify final output/document/test bytes and
validation evidence using raw-byte SHA-256 and Git blob IDs; the manifest has no
self-hash. [Final checks](final-results.json) record the final documentation,
preservation and whitespace checks. These results mean **READY for supervisor
delivery**, not merge-ready or independently reviewed.
