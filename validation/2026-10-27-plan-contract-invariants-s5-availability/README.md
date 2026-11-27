# S5-SAFE-REJECT / S5-FINITE contract-based availability examples

Task ID: `plan-plan-contract-invariants-s5-availability`. Task document: the
supervisor-supplied node specification and read-only design plan in this session;
there is no issue or corresponding file under `docs/tasks/`. No task input edited.
Date: 2026-10-27. State: implemented and locally verified; publication, non-author
A2 review and exact-head hosted CI belong to the supervisor. This is not merge-ready.

## Basis and protected content

- Branch: `agent/kix-plan-plan-contract-invariants-s5-availability`.
- Observed local `origin/main`, task base and initial branch HEAD:
  `876f41067bc7eb70bcd6ebd9c744c11b46f046b6` (identical; no local base delta).
- No fetch was performed: the supervisor explicitly prohibits all network actions.
  Remote freshness is unverified. No commit, push, PR, issue or comment was made.
- Implementation is the uncommitted working-tree patch, not the unchanged HEAD.
  A final committed implementation/task SHA does not exist in this builder session.
- Merge SHA, exact-head KTX/KIX run IDs/status/conclusions and post-merge main CI:
  not applicable / not run. No earlier CI is attributed to this patch.
- Both initial and post-test `git hash-object` checks returned:
  - `runtime/crates/kix-kernel/src/lib.rs`:
    `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`:
    `b607996c83a119c349f1cc90469ac1ba82764e20`.
- The protected-path diff against local `origin/main` is empty, including
  `reference/v0.3-rc1/**`, both locks, kernel source, contracts, the kernel README,
  task documents, `.aiops/`, `.github/`, scripts, `tests/support/model_v4.rs` and
  `e4_state_model.rs`. No transient mutation of locked files.

Complete changed paths:

1. `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
2. `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md`
3. `docs/README.md`
4. `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md`

In the test file the eight existing tests (the "frozen Task 001" set named by the
`e4_state_model.rs` crosswalk) and their helpers are byte-unchanged. Only the module
doc gains one paragraph, the `use` list gains the public `MAX_BUNDLE`, and new
helpers and seven tests are appended. The new tests use only the public kernel API
and observable state. They import neither `model_v4`, the e4 model nor any generator.

Map edits: S5-SAFE-REJECT and S5-FINITE cite the new tests and narrow their Gap text.
Both stay PARTIAL, because finite examples do not establish availability over all
valid inputs. New finding F-B5, one §0 follow-up bullet and the §5 non-claims sentence
are extended. No status changed, so the Counts line and its roll-up copy in
`docs/status/EVIDENCE_MAP_ROLLUP.md` are recomputed as unchanged and not edited:

`Counts: rows=27 COVERED=10 PARTIAL=12 NOT_COVERED=3 OPEN=2`

S5-SHARED-ERROR and S5-PERSISTENCE remain OPEN. All other rows are unchanged.

## Existing coverage mapping (inspected before adding tests)

Paths in this table are under `runtime/crates/kix-kernel/tests/`.

| Requirement | Prior classification and exact evidence | Gap addressed here |
|---|---|---|
| Free range inside one actual segment | Partially covered: `transitions.rs::reservation_has_inventory_order_and_stable_external_intent` (one example), `transitions.rs::actual_segment_boundary_is_an_aisle` (rejection side) | Ranges ending exactly at the aisle, the whole second segment, first and last seats, MAX_BUNDLE characterization |
| Word crossing without an aisle | Partially covered: `transitions.rs::sixty_four_bit_word_boundary_is_not_an_aisle` (one example) | Exact gap between two holds across seat 64; the 127/128 boundary; crossing that ends at the aisle |
| GA up to remaining capacity | Partially covered: `transitions.rs::general_admission_never_overdraws_and_expiry_is_single_release` (overdraw rejection side) | Exactly the full capacity in one request, and exactly the remainder after earlier holds; seat analogue filling two segments |
| Reuse after expiry | Partially covered: `transitions.rs::late_capture_after_expiry_and_resale_does_not_release_new_buyer`, `contract_edge_cases.rs::rejection_replay_stays_immutable_after_the_blocking_hold_is_released` (single seat, count 1, no GA) | Multi-seat superset of released and never-held seats; full GA capacity reuse; expired order stays Expired without inventory |
| Reuse after cancellation | Characterized: `transitions.rs::local_cancellation_blocks_new_reservations_but_not_original_results` (new reservations BusinessFenced) | None; no contract requires success (class B, F-B5 a) |
| Success after unrelated rejection or replay | Partially covered: `transitions.rs::overlapping_bundle_rejection_never_partially_allocates`, `contract_edge_cases.rs::retained_unbound_conflict_bans_the_identity_for_any_future_order` | Success on the exact selection every rejected request asked for, after Unavailable, OrderExists, OperationAlreadyBound, InvalidRequest, expired, replay and five guard errors, on seat and GA fixtures |
| Last record slots | Partially covered: `transitions.rs::bounded_records_backpressure_without_evicting_old_results` (backpressure side) | Minimal limits admit one reservation; the last command and last order slot admit a reservation after a recorded rejection |
| Smallest positive price, 1 ms TTL | Not covered | amount 1 with expires_at_ms = now + 1 is held and released exactly at expiry, on seat and GA fixtures |

## New tests, contract clauses and class B characterizations

All in `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`. Each `///` doc comment
before `#[test]` names its clause. Fixtures mirror CONTRACT_INVARIANTS §4: seat segments
[65, 5] and GA capacity 6, plus [200] and [5, 5] seat inventories where a test needs
them. Command times strictly increase, so admitting equal times is not relied on.

| Test | Contract clause | Class B characterization inside the test |
|---|---|---|
| `free_contiguous_range_inside_one_actual_segment_is_held` | ADR §8 all-or-none contiguous segment selection; README Implemented meaning | Two MAX_BUNDLE (64) ranges; the README names a maximum bundle length without a value |
| `word_crossing_range_inside_one_segment_is_held_between_neighbours` | README "crossing a 64-bit word when appropriate but never crossing an aisle"; ADR §8 machine-word boundaries | none |
| `seats_and_general_admission_are_held_up_to_exact_remaining_capacity` | README "GA capacity cannot overdraw"; ADR §8 R1 covers GA capacity | none |
| `inventory_released_by_expiry_is_reusable_by_a_new_command` | STATE_LIFECYCLE §5.7 expire releases only Held; ADR §6 released inventory can be owned by another order; README Implemented meaning | Cancellation reuse is recorded as class B and not asserted |
| `success_follows_unrelated_rejections_errors_and_replays` | ADR §3/§5 read-only replay; ADR §4 every fallible validation precedes all mutation; STATE_LIFECYCLE §2 rejections are recorded | Exact Rejection and KernelError variants; cross-kind selections rejected as InvalidRequest |
| `last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection` | README bounded records, no dedupe eviction; ADR §3 capacity backpressures instead of forgetting; STATE_LIFECYCLE §2 | Inclusive limits; exact Capacity variant |
| `smallest_positive_price_and_one_millisecond_ttl_are_held` | README Hard boundaries "accepts positive-price orders"; STATE_LIFECYCLE §5.7/§2 expiry instant | none |

The required part of every test is the final Held result, the Held order owning its
inventory and the exact reduction in remaining units. The rejected requests in the
success-after-noise test all ask for the target selection, so any partial allocation
would make the final reservation fail. Errors are checked against a whole-kernel `Eq`
clone. The same command identity that met only errors is still held afterwards.

Class B findings (recorded as F-B5 in the map, not new contract semantics):

- (a) Reuse after `cancel_scope`: ADR §7 makes cancellation a sticky local business
  fence and no contract defines reopening, so no success is required.
- (b) Reuse of inventory released when a late capture produces ReturnRequired is
  not asserted.
- (c) The bundle maximum value and whether record-count limits are inclusive.
  The README names maximum bundle lengths and configured record counts without
  values. The MAX_BUNDLE and last-slot cases are labelled characterizations.
- (d) The exact Rejection and KernelError variants and cross-kind selection
  handling on the unrelated-rejection steps.

No class C violation was found: every case the contracts require to succeed was held.

## Commands actually run and results

Commands run from the repository root unless noted; Cargo commands ran from `runtime/`.
Rust toolchain observed: rustc 1.98.1 / cargo 1.98.1. All Cargo verification uses the
offline lockfile. Every command ran in the foreground; no background long job.
Test totals are aggregated from the `test result` lines in the logs under
`.local/verification/s5/` (ignored local artifacts, not tracked paths).

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD origin/main` | Initially clean; both SHAs as recorded above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before editing and after all tests) | Exit 0; both required blobs match |
| `cargo fmt -p kix-kernel -- --check` | Exit 0 |
| `cargo test -p kix-kernel --locked --offline --test contract_edge_cases` | Exit 0; 15 passed (8 existing, 7 new), 0 failed, first run |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo test -p kix-kernel --locked --offline` | Exit 0; 100 passed, 0 failed (9 result groups) |
| `cargo test --workspace --locked --offline` | Exit 0; 289 passed, 0 failed (43 result groups) |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo fmt --all -- --check` | Exit 0 |
| `cargo tree -p kix-kernel --edges normal --locked --offline` | Exit 0; kernel depends only on kix-types |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; 2 positive controls and 66 negative fixtures |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; contracts=25; Counts copy matches |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; 16 negative controls |
| All 55 `python3` commands extracted in order from the `Stdlib offline document checks` run block in `.github/workflows/protocol.yml` | All exit 0 (55 commands, 0 failures); includes `check_docs_index.py` (scanned=282 indexed=247 allowlisted=35) and its `--self-test`, `check_lifecycle_adr_evidence_map.py` (27 rows OK) and `--self-test` (49 negative fixtures), and `check_toss_card_profile_evidence_map.py` and `--self-test`, which also cite this test file; log at `.local/verification/s5/stdlib-document-checks.log` |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests OK |
| `git diff --exit-code --stat origin/main -- reference/v0.3-rc1 runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/README.md runtime/crates/kix-kernel/tests/support runtime/crates/kix-kernel/tests/e4_state_model.rs docs/contracts docs/adr docs/tasks docs/status/EVIDENCE_MAP_ROLLUP.md .aiops .github scripts` | Exit 0; empty protected-path diff |
| `git ls-files --others --exclude-standard -- reference/v0.3-rc1` | Exit 0; empty output |
| `git diff -U0 origin/main -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | Three hunks only: module doc, `use` list, appended tail; existing tests unchanged |
| `git diff --check` | Exit 0 |

Closest CI equivalents inspected: `.github/workflows/ktx-kernel.yml` (architecture, kernel
tests, Clippy, formatting, dependency tree) and `protocol.yml` (workspace Rust boundary
and the stdlib document checks). Unrelated Move, TypeScript, local-chain, ZK and storage
jobs were not run for this test/map patch. No verification failure or repair retry occurred.

## Deviations and non-claims

- No fetch, publication, commits or hosted CI: explicit supervisor restrictions
  override the normal session-start fetch and final-head delivery workflow.
- The plan's `general_admission_is_held_up_to_exact_remaining_capacity` is named
  `seats_and_general_admission_are_held_up_to_exact_remaining_capacity`, because it
  also fills a [5, 5] seat inventory. The objective asks for both fixture kinds.
- The existing `kernel()` helper is not rewritten to delegate to the new
  `kernel_with`, so the frozen Task 001 tests and helpers stay byte-unchanged.
- The free-range test adds the single-seat cases (64, 1) and (69, 1). The
  success-after-noise test adds an already-expired request and reuses the target
  command identity for the guard errors. These are additions within the plan.
- `r1_perf_probe` and the e4 summary record the blob of `contract_edge_cases.rs` at
  run time; that recorded value changes with this file and is not pinned anywhere.
- No availability proof: seven finite examples do not establish availability over
  all valid inputs. Source-informed authorship: the author read the locked kernel
  source when choosing boundaries, so this is not clean-room evidence. No capability
  grade change, no kernel, contract, ADR, kernel README, checker or `model_v4` change.
- No production readiness, durability, distributed fencing, bank exactly-once,
  chain finality or real-money claims. No external provider, production runtime,
  public endpoint, secret or Sui network was used.
- Follow-up candidates: contract-owner clarification of the F-B5 items, chiefly
  whether a cancelled scope may reopen and the inclusive limit values.
