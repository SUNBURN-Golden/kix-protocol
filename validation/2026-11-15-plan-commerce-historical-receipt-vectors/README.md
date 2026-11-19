# plan-commerce-historical-receipt-vectors — builder evidence

Task input: user/supervisor node specification and supplied read-only design plan in this session; no issue or node document exists under `docs/tasks/`. Not ASTRA program mode.
Branch: `agent/kix-plan-commerce-historical-receipt-vectors`.
Starting HEAD/base and cached `origin/main`: `1aa8635829b675b424807cb0e7d008992d984e72` (equal; no local delta).
Remote freshness UNVERIFIED: fetch NOT_RUN under the explicit supervisor network ban.
Implementation/final committed head: pending supervisor commit; changes remain on starting HEAD. No merge; merge SHA/post-merge CI N/A.

## Coverage mapped before tests were added

| Requirement | Existing coverage classification | Portable-history gap / planned evidence |
|---|---|---|
| Issuance after consumption | Sufficient behavior: `reference/booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_cancel_after_issue_and_duplicate_consume` | Not covered as portable inputs/full outputs; issuance-after-consumption case. |
| Transfer after closure | Sufficient behavior/restore: `reference/booking_resale_admission/test_resale_fsm.py::ResaleFsmTests.test_restore_replays_one_transfer_and_omits_rejections` | Not covered as portable host history; transfer-after-closure case. Restore stays in existing regression. |
| Distribution/partial refund | Partial: `reference/settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.test_partial_refund_distribution_survives_replay_and_is_not_a_clawback` | First distribution after refund plus second zero-effect distribution and its replay in one portable history. |
| Full refund/mock acceptance | Partial: same file, `SettlementFsmTests.test_full_refund_acceptance_does_not_close_an_external_return` | Full snapshots for distribution/refund/acceptance replays while current refund outstanding is zero and PG adjustment remains open. |
| Same-key body conflicts/refusals | Sufficient behavior: same file, `test_same_key_replays_and_a_different_body_is_rejected`, `test_commit_fault_is_outside_the_journal_and_replay_stays_captured` | Schema-valid host history with exact conflict/refusal codes. |
| Complete outputs, references, source pins | Sufficient infrastructure in journey receipt and temporal packs; new histories not covered | Canonical full receipts/errors, ordered identities, complete input references and explicit source allowlist. |
| No extra effects or journal append | Partial across portable histories | Deep copies of all five machines' canonical state/digests/journals and relevant public views around every replay/refusal. |
| Mutation controls | New pack not covered | Nested additions/removals/changes, bool/zero and null, errors, missing/duplicate/reordered steps/cases, wrong references and every source byte drift before execution. |
| False flags / separate facts / binding and producer statuses | Sufficient existing helpers/checkers | Reuse unchanged helpers and checkers; payment/issuance/admission/refund/mock acceptance asserted separately. |

## Scope and gates

Source-informed in-process mock evidence only. Public machine views are test observations, not published reads. All 13 missing reads remain NOT_BOUND; semantic SDK consumption stays HOLD_SEMANTIC; SD1 stays OPEN/User-owned. Product policy values stay UNDETERMINED with their existing owners. Execution/finality flags remain false. No transport, automatic retry, read API, command, persistence or external execution is added.
Non-mutation assertions cover observable business state and journals; documented process-local rejected idempotency entries may be retained. No general rollback guarantee, independent clean-room evidence, production durability, legal compliance, real payment, external refund completion or chain finality is claimed.
A2 non-author exact-head review PENDING. Exact-head KTX and KIX CI NOT_RUN: no delivery commit or network authorization; run IDs/status/conclusions unavailable. No merge readiness or promotion claimed. Supervisor owns publication and review/CI gates.

## Deviations

Fetch omitted under the supervisor network ban. Task input is the supplied session specification, not a new repository task document. Golden bytes were captured during implementation; tests expose no update mode. CI, FSMs, contracts, catalogue, SDK, producer/binding statuses, old packs and 534 relevant tracked paths are inventoried for preservation. The preservation checker also rejects any tracked modification outside the two authorized consumer/navigation documentation edits.

## Evidence

Commands and results are recorded in `commands.jsonl` and adjacent foreground logs. Before-work protected bytes are in `preserved-inputs.json`; new fixture/test hashes are recorded separately in `artifacts.json` to avoid circular pins.

## Implemented evidence and preservation

The input pack contains five cases and 54 explicit steps, with 50 full accepted
receipts and four exact refusals in the output pack. There are 31 sorted source
pins plus the input pin. The five dedicated history tests close the portable gap
mapped above. The complete comparison validates canonical input/output bytes,
published body schemas, unique fixed step/case order and full body references.
Mutation controls cover receipt shape/value drift (including false versus zero
and null), errors, order/identity/reference corruption, every pinned file and
input/source pin sets before execution. An extra-effect control deliberately
executes the existing resale clock action on an unrelated machine and verifies
that both replay and refusal guards detect it. No new command was added.

Both locked blobs matched before work and in `preservation-after.log`:

| Path | Required / observed before and after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The checker verifies all 534 inventoried paths, including frozen
`reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**`, existing packs/helpers/FSMs,
contracts, catalogue, SDK, workflows and producer/binding status inputs. It also
checks artifact hashes, no additions in the frozen/program/task trees and no
other tracked modifications. Final-merge blob checks are N/A (no merge).
`artifacts.json` records raw SHA-256, Git blob and size for the two new JSON
artifacts and the new test without circular output/test self-pins.

## Implementation corrections and design deviations

The one-off artifact capture initially failed because a listing view uses
`holder_role`, not `current_holder_role`; the fixture observation was corrected
to the existing public field. It then captured all 54 outcomes successfully.
The first expanded guard-control run failed with `KeyError: credit_set_clock`;
that control incorrectly named an unpublished action. It was corrected to the
existing `resale_set_clock`. The next guard-control run failed because the
injected clock command also ran on the original issuance, making its later
injection a duplicate. The control now injects only at the targeted replay or
refusal. The final 13-test suite passed; both failed verification logs and all
actual command results remain in `commands.jsonl`.

The input schema adds explicit `refusal_of` / `conflict_of` references alongside
`replay_of` to make rejected-key histories independently inspectable. These are
fixture-only annotations, not command fields. The transfer case explicitly sets
up the reservation ticket source required by FsmHost, then uses the regression's
synthetic committed-settlement prerequisite, hold/payment/binding/transfer/close
history. Restore semantics remain covered by the source regression; the new
portable pack executes the explicit same-process calls requested by this node.

Temporary implementation helper scripts were briefly created under `/tmp`
(outside the requested worktree); they were removed. All delivered files are in
the node worktree. No Git publication, external-service access or hosted CI ran.
The full 67-command stdlib document block was executed as defined in the unchanged
protocol workflow; this includes its local loopback host preflight and offline
cache probes. It performs no public endpoint or external execution.

No explicit contract violation or new contract-undefined behavior was found.
Existing SD1/compensation uncertainties remain unchanged. Rejected-key retention
is the documented process-local behavior; external refund completion remains
open after mock acceptance. No product policy was chosen.

## Local verification scope

The new focused suite ran first, then the existing Commerce group and relevant
full reference suites. The unchanged protocol document block, OpenAPI/gate/SDK
pin checks and negative self-tests, offline-limit suite and practical KTX checks
ran locally. No toolchain or dependency installation was needed. These commands
run in the foreground with bytecode generation disabled and Cargo offline.

Sui/Move/localnet, proving-key generation/ZK verification, storage probes,
full frozen-reference aggregate scripts, unrelated reference suites, TypeScript
build/conformance and full Rust workspace checks were NOT_RUN: this node changes
only fixture/test evidence and related documentation. No hosted/full protocol CI
or exact-head acceptance is claimed from these targeted local equivalents.

See [every actual verification command and result](command-results.md),
[structured command records](commands.jsonl), and the adjacent full logs.
[Complete changed paths](changed-paths.txt) includes every delivered evidence
file. HEAD remains the starting SHA because the supervisor owns commits.

## Completed local results

All final required local checks passed. The full booking/resale/admission suite
passed 983 tests, including the relevant reservation/resale source regressions;
the settlement suite passed 224, including the distribution/refund/conflict
source regressions. The Commerce-only group passed 93 and the final focused new
suite passed 13. These are overlapping executions, not additive coverage counts.
The 67 workflow document commands all passed, including producer/binding,
read-model, documentation, evidence-map, CI discovery and checker-wiring checks
and their self-tests. OpenAPI/integration-gate/SDK pin checks and self-tests
passed. Offline limits passed nine tests; architecture negative tests passed
seven. Kernel tests, kernel Clippy with warnings denied and workspace formatting
passed with the existing offline dependencies. No required final check remains
failed; the two intermediate guard-test failures remain visible in the evidence.

| Local acceptance command group | Actual final result |
|---|---|
| Focused `test_commerce_historical_receipt_vectors.py` discovery | PASS, 13 tests |
| `test_commerce_*.py` discovery | PASS, 93 tests |
| Full `reference/booking_resale_admission` discovery | PASS, 983 tests |
| Full `reference/settlement_f01_f03` discovery | PASS, 224 tests |
| `run_document_checks.py` (unchanged protocol workflow stdlib block) | PASS, 67 commands |
| OpenAPI, integration-gate, SDK pin checks, each normal and `--self-test` | PASS, six commands |
| `integration_gate.test_offline_limits` | PASS, nine tests |
| Runtime architecture verification / negative tests | PASS / PASS, seven tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS |
| `check_preservation.py` | PASS, 534 original paths and three new artifact identities |

A2 non-author exact-head review, exact-head KTX and KIX hosted CI remain pending
supervisor delivery gates. No run IDs, success conclusions, final committed head
or merge SHA exist for these uncommitted changes. Task state: locally complete
for supervisor handoff, not merge-ready.

| Artifact | SHA-256 |
|---|---|
| `commerce_historical_inputs_v1.json` | `5904ef797dc02dfb7d3b080eef9edcd761b93590da3ae27c16fee85c5cfd4b8e` |
| `commerce_historical_receipts_v1.json` | `0c4f1e33c292f952c5949459fe80550dfdc8b3942be7513b7ee4dd1fda404c94` |
| `test_commerce_historical_receipt_vectors.py` | `9d85011fbd3a2cbff973aea216519268ce048a8dd9badef3c4e6a726c00ab73b` |
