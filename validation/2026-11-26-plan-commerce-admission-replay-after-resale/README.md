# Commerce admission replay after resale validation

Task `plan-commerce-admission-replay-after-resale` uses the supervisor-provided
node specification and design plan. The node has no task issue or
`docs/tasks/` document. Planner run `1795647575` was cited in the specification.
Its local log directory was unavailable.

| Baseline | SHA or state |
|---|---|
| Cached `origin/main` at start | `474ebc4bcaf3e8ce36f764bbda3ce95010ed1095` |
| Starting HEAD on `agent/kix-plan-commerce-admission-replay-after-resale` | `474ebc4bcaf3e8ce36f764bbda3ce95010ed1095` |
| Implementation and final task head | Worktree delivery. The supervisor owns commits. |
| Merge commit | Pending user authorization and delivery gates. |

The offline supervisor rule precluded `git fetch origin main`. The cached
base matched the design and branch HEAD. Remote freshness is unverified.

## Existing coverage and additions

| Acceptance | Existing coverage | New evidence |
|---|---|---|
| An original authorization key returns its first receipt after expiry and transfer | Partial. `ReturnedResultReplayTests.test_admission_first_results_survive_corruption_transitions_and_restore` covers detached admission results. `CommerceHistoricalReceiptVectorTests.test_transfer_after_closure` covers original-key replay after a later resale transition. | The one-host history compares the full first and replay receipts after omitting only the top-level `duplicate` and `applied` fields. The replay preserves `admit-1`, `buyer-1`, version 1 and the original expiry. |
| Fresh stale consume is refused | Sufficient at individual FSM level. `ReservationRejectionAtomicityTests.test_consume_stale_version_leaves_no_trace` covers a stale consume without a journal append. `AdmissionFsmTests.test_transfer_then_entry_rejects_both_presentations` covers stale admission after a transfer. `CommerceTemporalVectorTests.test_expired_authorization_replacement` covers expiry without a resale transfer. [Reservation atomicity](../../reference/booking_resale_admission/test_reservation_rejection_atomicity.py) · [Admission FSM](../../reference/booking_resale_admission/test_admission_fsm.py) · [Temporal vectors](../../reference/booking_resale_admission/test_commerce_temporal_vectors.py) | The new history requires `FsmRejected.code == "STALE_VERSION"` for a fresh consume ID and key that present the original version, gate and request after transfer. |
| Neither call appends. Buyer keeps the right and no admission is consumed. | Partial. `CommerceTemporalVectorTests.test_transfer_stale_presentations` covers a transfer and stale presentations. `CommerceEntryResaleOrderVectorTests.test_consumption_and_ownership_versions_stay_distinct` distinguishes reservation consumption from resale ownership. | The test compares detached snapshots 15→16 and 16→17 separately, including full accepted journals, state, digests and available views. Each checkpoint requires `buyer-2` at version 2 with null consumption IDs in the reservation and credential views. Settlement and credit have no case views in this history. Their states, digests and empty journals are included. |
| Portable exact references and `HOLD_SEMANTIC` | The combined history was uncovered. | `CommerceAdmissionReplayAfterResaleVectorTests.test_complete_output_bytes_and_references` validates published command schemas, source pins, canonical output bytes and all six request/receipt/refusal pointers. The index test rejects crossing the first and replay outcome references even though their input bodies are identical. |

The history uses the existing command identities and the linked and independent
clock behavior in the Commerce contract. The reservation and credential
retain their historical authorization phases after expiry, with no live
admission ID. The resale machine observes current ownership. No explicit
contract violation or contract-undefined behavior was found.
[Booking, resale and admission contract](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md)

## Changed paths

- `reference/booking_resale_admission/fixtures/commerce_admission_replay_after_resale_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_admission_replay_after_resale_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_admission_replay_after_resale_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `validation/2026-11-26-plan-commerce-admission-replay-after-resale/README.md`

## Local verification

Python checks ran from the repository root with `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`. In the commands below, `$bra` is
`reference/booking_resale_admission`. The focused suites ran before the full
discovery command. The focused admission replay also ran after moving pin
validation ahead of host execution.

| Command | Actual result |
|---|---|
| Inline `python3.12 -B -` one-host smoke run before edits | Exit 0. Both clocks reached 1,120,000. Replay returned the first receipt with the two replay fields changed. Fresh consume returned `STALE_VERSION`. Both comparisons of adjacent snapshots matched. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_admission_replay_after_resale_vectors.py -v` | Exit 0 on both runs. One test passed, covering 18 ordered commands and all six exact pointers. |
| Same focused command with `-p test_commerce_temporal_vectors.py` | Exit 0. Nine tests passed. |
| Same focused command with `-p test_commerce_historical_receipt_vectors.py` | Exit 0. Thirteen tests passed. |
| Same focused command with `-p test_commerce_entry_resale_order_vectors.py` | Exit 0. Eleven tests passed. |
| Same focused command with `-p test_commerce_companion_evidence_index.py` | Exit 0. Thirteen tests passed, including the crossed-outcome control. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,095 tests passed. |
| `python3.12 -B scripts/check_docs_index.py` and repeat with `--self-test` | Both exit 0. 470 scanned, 435 indexed, 35 allowlisted. Self-test passed. |
| `python3.12 -B scripts/check_bra_evidence_map.py` and repeat with `--self-test` | Both exit 0. 39 rows and 219 citations validated. Self-test passed 50 negative controls. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and repeat with `--self-test` | Both exit 0. Nine reference suites, eight Node tests and four Python modules reached. Self-test passed 18 negative controls. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and repeat with `--self-test` | Both exit 0. Verified 84 command identities and 13 reads. Self-test passed. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and repeat with `--self-test` | Both exit 0. 84 commands and 13 `NOT_BOUND` reads. Self-test passed 10 negative controls. |
| `python3.12 -B scripts/check_read_model_source_map.py` and repeat with `--self-test` | Both exit 0. 13 queries and 145 citations validated. Self-test passed. |
| `python3.12 -B scripts/check_openapi_contract.py` and repeat with `--self-test` | Both exit 0. 84 commands and the catalogue pin matched. Self-test passed. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and repeat with `--self-test` | Both exit 0. 84 commands and local endpoint constraints validated. Self-test passed. |
| `python3.12 -B scripts/verify_commerce.py --report "$report_dir/commerce.json"` | Exit 0, `PASS`. Calculation-only report written to a temporary directory. |
| `python3.12 -B scripts/verify_canonical.py --report "$report_dir/canonical.json"` | Exit 0, `PASS` with Node 24.22.1. Report written to the same temporary directory. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0. Architecture and declared dependency gate passed. |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0. Seven tests passed. |

### Offline Rust checks

Cargo used Rust 1.98.1, `CARGO_NET_OFFLINE=true` and temporary output directories.
The full runtime manifest failed to resolve the existing `duckdb` dependency
of `kix-analytics-audit` in the offline crates.io index. The cache inventory
found 14 of 378 locked registry archives and confirmed the absence of
`duckdb` and `libduckdb-sys`.

The fallback used inline `python3.12 -B -` to copy the six local-only crate
trees to a temporary workspace, keeping the toolchain pin. `diff -qr` matched
each copy to its repository tree. `cargo generate-lockfile --manifest-path
"$manifest" --offline` succeeded, and a second inline Python check found all
six resolved package records identical to the corresponding checked-in
records. The temporary workspace included `kix-types`, `kix-feature-semantics`,
`kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and `kix-delegated-exec`.

| Command, with the manifest path selected for each workspace | Repository manifest | Temporary six-crate manifest |
|---|---|---|
| `cargo test --manifest-path "$manifest" -p kix-kernel --locked --offline` | Exit 101 during resolution, before compilation. | Exit 0. 139 tests passed. |
| `cargo clippy --manifest-path "$manifest" -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101 during resolution. | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. | Covered by the repository manifest check. |
| `cargo tree --manifest-path "$manifest" -p kix-kernel --edges normal --locked --offline` | Exit 101 during resolution. | Exit 0. The sole normal dependency is `kix-types`. |
| `cargo test --manifest-path "$manifest" --workspace --locked --offline` | Exit 101 during resolution, before compilation. | Exit 0. 332 tests passed. |
| `cargo clippy --manifest-path "$manifest" --workspace --all-targets --locked --offline -- -D warnings` | Exit 101 during resolution. | Exit 0. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` with an inline JSON summary | Exit 0 for the read-only inventory. 14 of 378 archives present. | — |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. KTX workflow input digests computed. | — |

`kix-analytics-audit` and `kix-bcs1` are outside the fallback. Full-workspace
Rust tests and Clippy remain unverified. Hosted bootstrap, Move and ZK were
outside the local checks for the touched paths.

## Byte preservation

| Command | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` at start and after implementation | Both refs stayed at `474ebc4bcaf3e8ce36f764bbda3ce95010ed1095`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` at start and after implementation | Matched `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, respectively. |
| `find reference/v0.3-rc1 -type f -print0 \| sort -z \| xargs -0 -r sha256sum`, then `cmp` | Both inventories contain 108 paths. The manifests match with SHA-256 `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`. |
| `git diff --exit-code HEAD --` and `git ls-files --others --exclude-standard --` on protected paths | Exit 0. No changes in runtime, the frozen reference tree, `.aiops/`, task documents, workflows, the OpenAPI catalogue, or SDK and Commerce qualification and binding inputs. |
| `git diff --check`, `git status --short --branch --untracked-files=all`, and inline `python3.12 -B -` with `git show` and `git ls-files` | Exit 0. Exactly ten paths changed. Added-file whitespace passed. The original companion index bytes are preserved before the appended pack. The index contains 14 families and 407 steps. |
| `git hash-object` and `sha256sum` on both new fixtures | Exit 0. Input blob `341079f211a033534c21614ee9ed1b4a2902243c`, SHA-256 `d37011eb1c62cec56b8be8fb3a68ab9e3e6b20dbdc64a4c8adcab9f0fb2585df`. Receipt blob `0e21731f525a6bd53ebd9d1cd606bd9eca800ec9`, SHA-256 `fd9a4c4cb3b3b493dec39c079d78b5b9ece1c298e7a5f755aac8170948c06439`. |

## Delivery boundaries

These observations use one synthetic in-process host. The output labels
current-state snapshots as `TEST_HARNESS_EVIDENCE`. The new history carries
`HOLD_SEMANTIC`. All 13 reads remain `NOT_BOUND`, SD1 remains `OPEN` and
User-owned, and external `kix-commerce-apps` acceptance remains `UNVERIFIED`.
Product TTLs, fees and compensation are `UNDETERMINED` with Astra and JunTae.
Provider and legal terms retain their existing owners.

The local evidence covers mock decisions and accepted journals. Real funds,
provider calls, venue acceptance, durable recovery, chain finality,
distributed fencing, production readiness and clean-room independence are
outside its scope. A2 non-author exact-head review and successful exact-head
KTX kernel and KIX protocol workflows remain delivery gates. Run IDs,
statuses and conclusions are unavailable in this worktree session.
