# S4-PROBES / F-B3 expected business replies

Task ID: `plan-plan-contract-invariants-f-b3-reply-asse`. Task document: the
supervisor-supplied node specification and read-only design plan in this session;
there is no issue or corresponding file under `docs/tasks/`. No task input edited.
Date: 2026-10-27. State: implemented and locally verified; publication, non-author
A2 review and exact-head hosted CI belong to the supervisor. This is not merge-ready.

## Basis and protected content

- Branch: `agent/kix-plan-plan-contract-invariants-f-b3-reply-asse`.
- Observed local `origin/main`, task base and initial/final branch HEAD:
  `035d5705c93b318a49941ce5f7410f843360c427` (identical; no local base delta).
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
  `reference/v0.3-rc1/**`, both locks, kernel source, contracts, task documents,
  `.aiops/`, `.github/` and scripts. No transient mutation of locked files.

Complete changed paths:

1. `runtime/crates/kix-kernel/tests/contract_invariants.rs`
2. `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md`
3. `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md`

Only S4-PROBES changes in the map. It stays PARTIAL with narrowed F-B3 and the
negative-control citation. The Counts line and its rollup copy remain verbatim:

`Counts: rows=27 COVERED=10 PARTIAL=12 NOT_COVERED=3 OPEN=2`

S5-SHARED-ERROR and S5-PERSISTENCE remain OPEN. All other rows are unchanged.

## Existing coverage mapping (inspected before adding tests)

Paths in this table are under `runtime/crates/kix-kernel/tests/`.

| Requirement | Prior classification and exact evidence | Gap addressed here |
|---|---|---|
| Generated non-reserve reply values | Partially covered: `contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories` checked post-state predicates but used only is_ok for these replies | Assert typed values for every issued Send, Expire, Capture, Owner and Cancel |
| Reserve first-result identity / probes | Sufficiently covered: same generated test and `inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations` | No new reserve oracle or probe behavior |
| Event vs economic dedupe | Sufficient for examples: `transitions.rs::event_deduplication_and_economic_effect_deduplication_are_separate` | Extend exact reply checks across existing histories, not duplicate examples |
| Expiry / UNKNOWN / historical facts | Sufficient for examples: `transitions.rs::expired_hold_retry_keeps_original_result_and_separate_current_state`, `unknown_payment_is_not_released_by_ttl`, `historical_capture_after_owner_change_is_not_discarded` | Generated expiry and owner/capture reply coverage |
| Observation capacity and promised slots | Sufficient for examples: `observation_slots.rs::full_observation_budget_blocks_first_unknown_without_state_change`, `unrelated_event_flood_cannot_starve_promised_capture`, `conflicting_event_cannot_spend_slot_reserved_for_capture`, `reserved_slot_survives_expiry_check_owner_change_and_cancellation` | Track promised operations from observed successful sends and public counter deltas |
| Exact expiry / retry boundaries | Sufficient for examples: `contract_edge_cases.rs::expiry_instant_is_treated_consistently_by_every_entry_point`, `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot`, `return_required_is_stable_under_further_late_evidence` | Reuse contract anchors, retain class B where exact replies are unspecified |
| Reply-checker sensitivity | Not covered for non-reserve expected replies | New `reply_oracle_rejects_deliberately_wrong_expected_replies` rejects incorrect values, Ok/Err shape, wrong errors/kinds and lost slot/event history copies; kernel Eq snapshot unchanged |

## Clause to reply branch mapping and remaining uncertainty

This oracle is **source-informed**, because the author knew the locked kernel
source; it is not clean-room. It reads only our emitted inputs, observed replies,
public order/counter/conflict getters and configured limits. Expected values are
computed before the call, then compared afterward. It imports neither E-4 nor
its model/generator/guard logic. Class B assertions are explicit characterizations
of undefined exact reply/precedence details, not newly defined contract semantics.

Contract anchors (current local base):

- R: `runtime/crates/kix-kernel/README.md`, Implemented meaning, Observation
  reservation and remaining gaps, and Verification.
- A: `docs/adr/0001-ktx-authority-commit-recovery.md`, §6, §7, §8 and review addendum A/B.
- L: `docs/contracts/STATE_LIFECYCLE.md`, §5.7 and §5.7.1.

Short verbatim anchors: R: “UNKNOWN retries reuse the reservation.”;
R: “The budget includes stored event records, stored conflicts and outstanding reserved slots.”;
A §6: “Mismatch means review”;
A §6: “a matching capture after expiry/cancellation means ReturnRequired”;
L §5.7: “expire는 Held만 해제하고 PaymentUnknown은 TTL만으로 해제하지 않는다.”

| Branch labels | Derivation from pre-call public state/history | Contract basis / classification |
|---|---|---|
| send.unknown-order | Public order lookup absent | B: exact UnknownOrder error not specified by the cited clauses |
| send.invalid-state | Review flag or phase other than Held/PaymentUnknown | A §6 quarantine prevents sending; R UNKNOWN retention. B: exact InvalidTransition and phase/error precedence |
| send.closed | Local cancelled flag or now >= requested expiry | R local fences; L §5.7 retention. B: refusal to retry UNKNOWN after TTL and exact InvalidTransition versus capacity precedence |
| send.capacity | No previously observed promised slot and public sum at limit | R explicit pre-send Capacity contract; prerequisite error precedence remains B |
| send.ok | Eligible public phase, open time/scope, own slot or free budget | R pre-send reservation and UNKNOWN reuse; successful unit reply encoding is a source-informed characterization |
| expire.unknown-order | Public order lookup absent | B: exact UnknownOrder encoding |
| expire.early / expire.released / expire.noop | Pre-expiry; expired Held owning inventory; all other known orders | L §5.7 Held-only release and R UNKNOWN past TTL. B: exact false/true/false bool encoding |
| capture.dup-event | Matching provider/account/event and identical saved payload | A §6 event dedupe / addendum A exact replay not conflict; saved original observed reply, no new effect |
| capture.conflict | Same event key, different payload; retained conflict replay or free budget | A §6 / addendum A retain contradictions and original fact; Conflict enum spelling/repeated-conflict reply is source-informed characterization |
| capture.conflict-capacity | New conflicting payload, public sum full | A review addendum A / R explicitly specify Capacity after bound quarantine |
| capture.capacity | Fresh event without its own promise, sum full | R bounded sum / promised-slot isolation, including explicit Capacity before UnknownOperation when full |
| capture.unknown-operation | Fresh event, budget available, no public order bound to full operation | R explicit UnknownOperation without storage; A review addendum B unmatched custody remains external |
| capture.duplicate-effect | Fresh event for already captured operation, full AssetAmount equal | A §6 economic dedupe; L §5.7.1 matching duplicate does not erase review/return; enum encoding is source-informed |
| capture.review-mismatch | Fresh event with requested/retained amount mismatch | A §6 mismatch means review; L §5.7.1 later mismatching fact may return Review without replacing ReturnRequired |
| capture.return-required | First matching capture, expired/cancelled or already Expired | A §6, R matching late capture; L §5.7 explicitly uses application time. L §5.7.1 review remains orthogonal |
| capture.review-sticky | First matching timely capture on reviewed order | A §6 / R matching facts never auto-clear review or authorize fulfillment; Review encoding is source-informed |
| capture.confirmed | First matching timely capture, no cancel/review, bound order | R first full capture/asset binding and A §6; exact PaymentConfirmed mapping is source-informed characterization |
| owner.ok / owner.invalid | Compare input generation to last successfully observed fence | A §7 local ordered transitions only. B: strict comparison and exact unit/error replies |
| cancel.ok / cancel.invalid | Compare epoch to initial 1 / last successful cancellation | A §7 local cancellation only. B: strict comparison and exact unit/error replies |

There was no class C contradiction with a cited contract clause. Exact admission
values and some outcome encodings/precedence remain class B; S4-PROBES therefore
stays PARTIAL. None of these observations defines a new protocol rule or policy.

Context validity is fenced to version 4, the last successful owner fence and a
time at least as large as any prior emitted time. The last is a conservative
upper bound on admitted time, not a prediction of failed-call clock changes.
Unsupported contexts panic with S4-REPLY undetermined context. All non-reserve
corpus inputs satisfy these conditions. Successful sends add an operation only
when the public reserved counter rises; new retained captures record the observed
reply and remove the corresponding promise. Counter deltas and history lengths
are checked after every call. Existing read-only reserve probes remain intact.

## Executed corpus and branch counts

The existing 4 × 64 × 96 corpus, six initialization inputs, 90 generated inputs,
seeds, fixture limits and replay probes are unchanged. There are 24,576 primary
calls, 156,312 read-only replay probes and 434 retained capture facts observed.
Issued family counts: `[10496, 2304, 1792, 7936, 1792, 256]` for
Reserve/Send/Expire/Capture/Owner/Cancel. Exact-reply check counts:
`[0, 2304, 1792, 7936, 1792, 256]`, totaling **14,080**. Main-test assertions
require checked == issued for each of the five non-reserve families and the sum
of branch hits == all reply checks. Existing summary JSON shape is unchanged.

| Branch | Hits |
|---|---:|
| cancel.ok | 256 |
| capture.capacity | 1792 |
| capture.confirmed | 277 |
| capture.conflict | 1077 |
| capture.conflict-capacity | 937 |
| capture.dup-event | 2101 |
| capture.duplicate-effect | 804 |
| capture.return-required | 116 |
| capture.review-mismatch | 15 |
| capture.review-sticky | 26 |
| capture.unknown-operation | 791 |
| expire.early | 89 |
| expire.noop | 61 |
| expire.released | 114 |
| expire.unknown-order | 1528 |
| owner.ok | 1792 |
| send.capacity | 3 |
| send.closed | 99 |
| send.invalid-state | 222 |
| send.ok | 273 |
| send.unknown-order | 1707 |

`owner.invalid` and `cancel.invalid` have zero hits in the fixed corpus. No inputs
were added to it to increase branch coverage. Counts do not establish exhaustive
precedence coverage; the conflict label combines fresh and already-retained cases.

Runtime artifacts (ignored local evidence, not extra tracked paths):
`.local/verification/ktx/contract-reply-oracle-summary.json`,
`contract-reply-oracle-sensitivity.txt`, and the unchanged existing summary.
Kernel/workspace test and Clippy logs: `.local/verification/fb3/`.

## Commands actually run and results

All commands run from the repository root unless a tool's absolute-path read is
shown. Rust toolchain observed: rustc 1.98.1 / cargo 1.98.1. All Cargo verification
uses the offline lockfile. Tests ran in the foreground; no background long job.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; both SHAs and branch as recorded above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before editing and after tests) | Exit 0; both required blobs match |
| `rustfmt --edition 2024 --config skip_children=true runtime/crates/kix-kernel/tests/contract_invariants.rs` | Exit 0; formats only allowed test file |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline --test contract_invariants` | Exit 0; 5 passed, including deliberate-wrong-reply sensitivity |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 87 passed, 0 failed (aggregate of log result groups) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 276 passed, 0 failed (aggregate, includes kernel suite) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; 27 rows, corpus, anchors, symbols, counts and locks OK; all 7 corpus facts MATCH |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; 2 positive controls and 66 negative fixtures |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; 25 contracts, Counts copy matches |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; 16 negative controls |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; kernel depends only on kix-types |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0; digests recorded below |
| `git diff --check` | Exit 0 |
| `git diff --stat origin/main -- reference/v0.3-rc1 runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs docs/contracts docs/tasks .aiops .github scripts` | Exit 0; empty diff |

SHA-256 outputs, in the command's path order:

```text
a948a1b687de2727ad717db0f7a0aa4159ecf5258e52e18eccf05cc08329d83e
84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f
d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae
```

Routine inspection used `rg`, `sed`, `cat`, `git diff` and a Python stdlib parser
for aggregate test counts. No failing verification run or repair retry occurred.
Closest CI equivalents inspected: `.github/workflows/ktx-kernel.yml` architecture,
kernel tests, Clippy, formatting and dependency evidence; `protocol.yml` workspace
Rust boundary and the two relevant evidence-map checkers/self-tests. Unrelated
Move, TypeScript, local-chain, ZK and storage jobs were not run for this test/map patch.

## Deviations and non-claims

- No fetch, publication, commits or hosted CI: explicit supervisor restrictions
  override the normal session-start fetch and final-head delivery workflow.
- `expected_reply` takes the fixture limits explicitly (no public kernel limits
  getter exists) and uses `&self`; it need not mutate state. `run` returns its
  observed reply so the negative control can inspect actual calls without
  changing the generated corpus. These are local interface details only.
- Counts did not change because the design's PARTIAL branch applies; therefore
  no rollup edit. Map edits are restricted to S4-PROBES as authorized.
- `CONTRACT_INVARIANTS.md` §4's historical “No next expected business reply is
  predicted by a model” and the map's §4 F-B3 finding remain unchanged outside
  allowed scope. The new clause-based, source-informed oracle narrows that
  historical observation boundary; it does not relabel E-4 or claim independence.
  If non-author A2 review interprets that sentence as prohibiting this test path,
  the contract owner/User must resolve it in a separate authorized contract task.
- No availability, complete guard precedence, clean-room independence, universal
  capture custody, production readiness, bank exactly-once, real-money, durable
  recovery, distributed fencing or chain-finality claims. No external provider,
  production runtime, public endpoint, secret or Sui network was used.
- Follow-up candidates are contract-owner clarification of exact class B replies
  and review of the historical F-B3 prose, not implementation work in this session.
