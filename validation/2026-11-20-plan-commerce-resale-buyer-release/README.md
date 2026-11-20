# Commerce resale buyer-hold release evidence

The task input for `plan-commerce-resale-buyer-release` is the supervisor-supplied
node specification from planner run `1795168746` and its read-only design plan.
The node has no issue or task file under `docs/tasks/`. Its declared dependencies
are `plan-commerce-companion-evidence-index` and `booking-resale-admission-deepening`,
with an A2 audit floor. The task adds one indexed `resale_release_hold` history
from an issued right through a refused release, a successful release, a fresh
hold for the same recipient, historical release replay, explicit payment
observation and explicit transfer.

The task branch `agent/kix-plan-commerce-resale-buyer-release` and cached
`origin/main` both resolved to `b11e38ef93b39e11b0e557479a2711217a35938d`.
The supervisor's offline instruction superseded the fetch in `AGENTS.md` §1.
The remote's current SHA is unverified.

## Coverage

| Requirement | Prior coverage | New evidence |
|---|---|---|
| Wrong-buyer release | Sufficient at FSM level. `ResaleRejectionAtomicityTests.test_release_hold_buyer_mismatch_leaves_no_trace` checks the held listing's rejection. | Steps 10–11 preserve the canonical state, digests, accepted journals and available public views across all five machines. The outcome is `BUYER_MISMATCH`, and `list-1` stays `BUY_HELD` by `buyer-2` under `hold-1`. |
| Valid release and fresh hold | Partial. `ResaleFsmTests.test_buy_hold_is_optional_and_cancel_order_decides_the_race` releases a hold and acquires a different hold before seller cancellation. | Steps 12–13 record `LISTED` with cleared hold and buyer fields, null resale payment and transfer references, and `buyer-1` still owning `issue-1` at version 1. `buyer-2` acquires `hold-2` on the same listing. Each call appends one resale journal entry. |
| Historical release replay after a fresh hold | Partial for the general replay rule. `ReturnedResultReplayTests.test_resale_first_results_survive_corruption_transitions_and_restore` covers immutable resale first results. The release-specific indexed history was absent. | Step 14 repeats step 12's exact body and key. The complete receipt matches the first `LISTED` result with only `duplicate: true` and `applied: null` changed. State, digests, accepted journals and views match the pre-replay snapshot, which shows `BUY_HELD` under `hold-2`. |
| Explicit payment and transfer | Sufficient at FSM level. `ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential` covers separate payment and transfer. | Step 15 records distinct synthetic resale payment with `PAYMENT_NOTED`, while `buyer-1` retains version 1. Step 16 transfers the same `issue-1` to `buyer-2` at version 2 with `transfer-1`. The settlement gate is `UNBOUND` and `funds_executed` is false. |
| Portable indexed replay | No prior companion family covered this history. The existing index validates one-to-one step and outcome associations. | The 16 bodies use the published schema. The replay checks complete canonical UTF-8 bytes for 15 receipts and one refusal, including detached views and raw-byte pins. The thirteenth family adds 16 associations for 389 total. A detached control swaps the original release and replay outcome pointers and the validator rejects the swap despite identical input bodies. |

[Resale transitions §10.2](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#102-전이) ·
[Idempotency and replay §10.7](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#107-멱등키와-재생) ·
[Resale FSM tests](../../reference/booking_resale_admission/test_resale_fsm.py) ·
[Resale rejection tests](../../reference/booking_resale_admission/test_resale_rejection_atomicity.py) ·
[First-result tests](../../reference/booking_resale_admission/test_returned_data_isolation.py) ·
[Replay guide](../../reference/booking_resale_admission/README.md#commerce-resale-buyer-hold-release-vectors)

## Local verification

Python discovery ran from the repository root with Python 3.12.15,
`PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`. `bra` is
`reference/booking_resale_admission`. Rust checks used Rust and Cargo 1.98.1.
SDK checks used Node 24.22.1. The focused suites ran before the broader checks.
The fixture and index assembly used one-time Python commands. The replay tests
only read the checked-in vectors.

| Command | Result |
|---|---|
| `git status --short --branch` and `git rev-parse HEAD` and `git rev-parse --verify origin/main` | Clean starting worktree on the assigned branch with both refs at the same SHA. |
| `PYTHONPATH=.:$bra PYTHONDONTWRITEBYTECODE=1 python3.12 -B -` for fixture and index assembly | Both exit 0. Assembled 16 canonical inputs and outcomes, then appended the corresponding entries and validated all 389 associations. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_resale_buyer_release_vectors.py` | Exit 0. 3 tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_resale_fsm.py` | Exit 0. 9 tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_resale_rejection_atomicity.py` | Exit 0. 119 tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py` | Exit 0. 12 tests passed. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite" -q` for the eight offline reference suites in protocol CI | Exit 0 for each. Booking/resale/admission 1,079, settlement 224, credit 313, AI delegation 182, token reward 397, provider facts 86, payment effects 28, economics 99. Total 2,408 passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits -q` | Exit 0. 11 tests passed. |
| `python3.12 -B <checker> [--self-test]` for the [workflow's stdlib checks](../../.github/workflows/protocol.yml#L203), excluding the plain loopback probe | All 68 invocations exited 0. These include docs index, BRA evidence map, CI test discovery, producer qualification tuple and Commerce consumer binding index, each with its self-test. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and `python3.12 -B scripts/check_sdk_client.py`, each also with `--self-test` | All six invocations exited 0. |
| `npm --prefix sdk run conformance` and `npm --prefix sdk run verify-compat` | Both exit 0. 20 tests passed and the `bootstrap-2` manifest verified. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The existing scoped grant verified. |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/resale-buyer-release-commerce.json` | Exit 0. Calculation contracts passed, with zero external calls. |
| `python3.12 -B scripts/verify_canonical.py --report .local/verification/resale-buyer-release-canonical.json` | Exit 0. Python and TypeScript canonical comparison passed. |
| `python3 scripts/verify_runtime_architecture.py` and `python3 scripts/test_runtime_architecture.py` | Both exit 0. Architecture boundary and 7 tests passed. |
| `cargo test --offline --manifest-path runtime/Cargo.toml -p kix-kernel --locked --quiet` | Exit 0. 139 tests passed. |
| `cargo clippy --offline --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo tree --offline --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0. The only normal dependency was `kix-types`. |
| `cargo test --offline --manifest-path runtime/Cargo.toml --workspace --locked --quiet` | Exit 0. 345 tests passed. The existing analytics test for owner-provisioned engines was ignored. |
| `cargo clippy --offline --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Produced the three KTX source digests. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0. Both §4 blob IDs matched before and after work. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -` to compare worktree blob hashes against `git ls-tree -rz HEAD` and index bytes against `git show HEAD:<index>` | Exit 0. 4,411 original blobs matched, including all 108 frozen reference files. The prior 12 packs and 373 entries were preserved. Exactly 10 paths were in the patch. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` for each new file | No whitespace diagnostics. |

The local check set includes the design plan's checks, plus offline Python,
SDK, canonical and Rust workspace checks. Hosted setup, separate HTTP and
storage probes, local-chain, Move and ZK jobs were outside local verification
of these paths. The BRA suite exercised its existing local integration tests.

## Preservation

| Locked file | Git blob before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The tracked contents of `reference/v0.3-rc1/` match their starting Git tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`, with no untracked or ignored files
in that directory. The binding index, producer tuple, scoped qualification,
workflow files, `.aiops/` and `docs/tasks/` match their original blobs.

## Changed paths

- `docs/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_resale_buyer_release_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_resale_buyer_release_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/test_commerce_resale_buyer_release_vectors.py`
- `validation/2026-11-20-plan-commerce-resale-buyer-release/README.md`

## Scope and delivery gates

There were no contract violations or new contract-undefined characterizations
within the observed history. This is source-informed, non-normative mock evidence.
The selected amounts and times are synthetic. Product TTLs, fees and compensation
remain `UNDETERMINED` with Astra and JunTae. Provider and legal terms retain their
existing owners. Live funds, real provider calls, durability, cross-channel
exclusivity, chain finality, legal effects and production readiness are outside
this evidence.

The new pack carries `HOLD_SEMANTIC`. The `resale_release_hold` binding remains
`BOOTSTRAP_SCHEMA_BOUND`, all 13 reads are `NOT_BOUND`, SD1 is `OPEN` and User-owned,
and external Commerce acceptance is `UNVERIFIED`. The existing semantic grant
applies to its listed steps and outcomes. [Scoped fixture qualification](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md)

The implementation and final task commit SHAs are pending the supervisor's commit.
The A2 non-author review and both hosted exact-head workflows, KTX kernel
verification and KIX protocol verification, are pending delivery. Run IDs,
statuses and conclusions are unavailable for this worktree patch. Merge SHA and
post-merge CI are inapplicable to this delivery.
