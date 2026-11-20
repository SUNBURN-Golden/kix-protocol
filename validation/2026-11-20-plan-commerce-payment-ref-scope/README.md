# Commerce payment reference scope vectors

`plan-commerce-payment-ref-scope` uses the supervisor-supplied node specification
from planner run `1795159796` and the accompanying read-only design plan. The
node has no issue or task document under `docs/tasks/`. The starting HEAD and
cached `origin/main` both resolved to `d4cb2726d68764411ea16660da22188ef78eccc0`
on `agent/kix-plan-commerce-payment-ref-scope`. The supervisor's offline
instruction superseded the routine fetch in `AGENTS.md` §1. Remote freshness is
unverified.

## Coverage and evidence

| Requirement | Prior coverage | Fixture and replay coverage |
|---|---|---|
| Same-show payment identity and refusal atomicity | Sufficient at the resale FSM level. `ResaleRejectionAtomicityTests.test_observe_resale_payment_payment_binding_conflict_leaves_no_trace` checks the identical primary reference on a listed right. | Step 10 returns `PAYMENT_BINDING_CONFLICT`. The replay compares complete canonical state, state digests, accepted journals, and diagnostics across all five machines before and after the refusal. The listing remains `LISTED` with null payment and transfer references, held by `buyer-1` at version 1. |
| Distinct payment before transfer | Sufficient at the resale FSM level. `ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential` verifies separate payment and transfer behavior. | Step 11 records the distinct reference with a fresh key and retains the seller's version 1. Step 12 transfers the same `issue-1` to `buyer-2` at version 2. Each command appends one resale journal entry, and the listing's settlement gate is `UNBOUND`. |
| Reuse on a second show | Partial. `GateTests.test_payment_fact_is_not_funds_and_expiry_does_not_compensate` covers reuse through direct mock gate calls. | Step 16 is a first application for `order-2` on `show-2`, with `duplicate: false`, `applied: observe_payment`, and `PAYMENT_NOTED`. The same host still records the primary reference for `order-1` on `show-1`. |
| Portable indexed journey | The complete two-show history was absent. The existing companion index and resale-expiry replay cover the record format and setup separately. | All 16 bodies are validated against the published catalogue. The replay compares complete canonical UTF-8 output bytes, with 15 receipts and the exact refusal, detached views, ordered references and raw-byte pins. The index adds 16 input, outcome and binding associations. A detached control swaps the step 10 and 11 input or outcome pointers. |

[Resale rejection tests](../../reference/booking_resale_admission/test_resale_rejection_atomicity.py) ·
[Resale FSM tests](../../reference/booking_resale_admission/test_resale_fsm.py) ·
[Direct gate tests](../../reference/booking_resale_admission/test_mock_gates.py) ·
[Canonical inputs](../../reference/booking_resale_admission/fixtures/commerce_payment_ref_scope_inputs_v1.json) ·
[Complete outcomes](../../reference/booking_resale_admission/fixtures/commerce_payment_ref_scope_receipts_v1.json) ·
[Replay suite](../../reference/booking_resale_admission/test_commerce_payment_ref_scope_vectors.py) ·
[Companion index](../../docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md)

## Local verification

Python commands ran from the repository root with Python 3.12.15,
`PYTHONPATH=.`, and `PYTHONDONTWRITEBYTECODE=1`. `bra` is
`reference/booking_resale_admission`. Rust commands ran from `runtime/`
with Cargo 1.98.1 and a target directory in `/tmp`. SDK commands used
Node 24.22.1. The focused suites ran before the broader checks.

| Command | Result |
|---|---|
| `git status --short --branch` and `git rev-parse HEAD refs/remotes/origin/main` | Clean starting worktree on the assigned branch. Both refs matched the supplied base. |
| `PYTHONPATH=.:$bra python3.12 -B -` with an exploratory single-host replay | Exit 0. Same-show conflict, distinct payment, explicit transfer, and second-show reuse observed. |
| `PYTHONPATH=.:$bra python3.12 -B -` with the one-time fixture and index assembly scripts | Both exit 0. Wrote 16 canonical inputs and outcomes, then validated all 373 associations before writing the appended index. The replay test reads the checked-in data and compares bytes. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_payment_ref_scope_vectors.py` | Exit 0. 3 tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py` | Exit 0. 11 tests passed, covering 12 packs and 373 associations. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. 1,071 tests passed, including Commerce fixture tuple conformance. |
| `python3.12 -B <script> [--self-test]` for the workflow's [Stdlib offline document checks](../../.github/workflows/protocol.yml#L203), excluding the plain loopback host probe | All 68 invocations exited 0. This includes document index, BRA evidence map, CI discovery, producer tuple, and the Commerce consumer binding index, with their self-tests. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and `python3.12 -B scripts/check_sdk_client.py`, each also with `--self-test` | All 6 invocations exited 0. The catalogue has 84 commands, including 44 FSM commands. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | Exit 0. 11 tests passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exit 0. Architecture gate and 7 tests passed. |
| `npm --prefix sdk run conformance` and `npm --prefix sdk run verify-compat` | Both exit 0. 17 tests passed and the BOOTSTRAP manifest verified locally. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The existing scoped fixture manifest verified locally. |
| `cargo fmt --all -- --check` | Exit 0. |
| `cargo test -p kix-kernel --locked --offline` | Exit 0. 139 tests passed. |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `cargo tree -p kix-kernel --edges normal --locked --offline` | Exit 0. The sole normal dependency is `kix-types`. |
| `cargo test --workspace --locked --offline` | Exit 0. 345 tests passed. The existing analytics test for owner-provisioned offline engines was ignored. |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Exit 0. |
| `sha256sum Cargo.lock crates/kix-kernel/src/lib.rs crates/kix-kernel/tests/transitions.rs` | Exit 0. Produced the three KTX source digests. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0. Both §4 blob IDs matched before and after work. |
| `python3.12 -B /tmp/kix-commerce-payment-ref-scope-preservation.py` | Exit 0. Verified 4,398 base blobs outside the patch, including all 108 frozen reference files. The prior 11 packs and 357 associations match the base bytes. The unstaged patch has exactly the 10 paths below. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` for each new file | No whitespace diagnostics. The tracked check exits 0 and the new file comparisons exit 1 with empty diagnostics. |

## Preservation and changed paths

| Locked file | Git blob before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

- `docs/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_payment_ref_scope_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_payment_ref_scope_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/test_commerce_payment_ref_scope_vectors.py`
- `validation/2026-11-20-plan-commerce-payment-ref-scope/README.md`

The local check set includes the design plan's checks plus SDK and workspace
checks. The plain loopback host probe and the separate HTTP integration job
were omitted under the supervisor's offline instruction. The BRA suite ran
its existing local integration tests. Hosted bootstrap, local-chain, Move and
ZK jobs were outside local verification of these paths.

## Scope and delivery gates

The observed behavior matches the booking and resale contract §§3–4. This
replay surfaced zero contract violations and zero contract-undefined
characterizations. Diagnostic views describe the in-memory mock. Rejected-key
retention is process-local. Real payment, funds finality, durability, channel
exclusivity, provider identity, chain authority, legal effects, and production
readiness are outside the evidence. Product TTLs, fees, and compensation are
`UNDETERMINED` with Astra and JunTae. Provider and legal terms retain their
existing owners. [Booking and resale contract](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md)

The new history carries `HOLD_SEMANTIC`, all 13 reads `NOT_BOUND`, SD1 `OPEN`
and User-owned, and external consumer acceptance `UNVERIFIED`. Revision
`commerce-fixture-8ba7f6c-1` applies to the steps and outcomes listed in its
qualification table. [Scoped fixture qualification](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md)

The deliverable is a source-informed worktree patch. The implementation and
final task commit SHAs are pending the supervisor's commit. A2 non-author
review and exact-head KTX kernel and KIX protocol verification are pending
with run IDs, statuses, and conclusions unavailable. Merge SHA and post-merge
CI are inapplicable to this worktree delivery.
