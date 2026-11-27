# rs-model-gap-closure

Node: `plan-rs-model-gap-closure`. Closes the Python/Rust-closable PARTIAL-row gaps that `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` and `docs/status/RS_IM_EVIDENCE_MAP.md` named at the base, then edits only those rows, their statuses and the `Counts:` lines.
Issue: none. Depends on: `plan-rs-predicate-evidence-map`, `plan-plan-rs-im-evidence-map`, `rs-3b`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792307132 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA and no final task head SHA, and no KTX kernel verification or KIX protocol verification run exists for this work. The exact-head CI results belong in the pull request closure report (AGENTS.md section 11).

Observed `origin/main` = branch HEAD = `39146a44187af4b43ac57148661bc3af2fb3104f`, after `git fetch origin main` (a read-only fetch that AGENTS.md section 1 asks for).

**This record and the map updates are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, the operational count stays 0, no Sui, ZK, localnet or Node run was made, and each status remains a builder reading of the cited bodies.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match the required blobs before and after. The diff of `reference/v0.3-rc1`, `reference/rights_scale/sui`, `reference/rights_scale/zk`, `reference/rights_scale/vectors`, `runtime/crates/kix-kernel`, `.aiops`, `docs/tasks`, `docs/contracts` and `docs/decisions` against `origin/main` is empty (commands below). No profile byte, Move source, vector, circuit, manifest, K, P, S, W value, `MAX_BUNDLE_CHAIN` or `IssuerCap` option changed.

## What this change does

- Six new tests close the missing sentences an in-memory test can close:
  - `test_private_model.py::test_a_publicly_consumed_ticket_cannot_be_shielded` (RS-C09): a ticket consumed publicly cannot be shielded — `shield` aborts `EClosed`, no leaf and no nullifier is created, and the consumed slot stays occupied. A private spend needs a note, so none can be constructed for it.
  - `test_private_model.py::test_the_slot_bit_bound_is_the_log_ceiling_at_several_sizes` (IM-14): `claim_zk` accepts exactly the capacities whose log ceiling fits `ZK_DEPTH` (`capacity <= 2 ** ZK_DEPTH`), exercised at 11 sizes across the boundary. This is the model's only exposure of the slot-bit rule.
  - `test_model.py::test_the_cut_orders_a_delegated_consume_and_paid_issue_both_ways` (RS-C06(b), RS-C07): consume-then-cut leaves pre-cut tickets `ACTIVE`, preserves the stranded `IssuancePayment` (holder `dele`) and refuses every consume under the old grant with `EGrantClosed`; cut-then-consume refuses the same calls identically and leaves nothing; the strand blocks `undelegate_page` with `EDelegated`.
  - `test_model.py::test_the_issuance_event_carries_the_slot_and_the_generation` (IM-04, IM-29): the `Issuance` event carries the slot and the generation values, across a refund and a reissue (generation 1 then 2), each followed by its `Change`.
  - `test_model.py::test_offer_accept_gift_authorize_admission_and_consume_write_only_the_ticket` (IM-03): `snapshot()` keys `control`, `pages`, `shards` and `grants` are byte-identical before and after each of `offer`, `accept_gift`, `authorize_admission` and `consume`.
  - `test_summarize_load.py::test_a_failed_path_is_reported_separately` (RS-C14): on a synthetic report with a corrupted public snapshot, `summarize_load.py` reports the public path `FAILED_MEASUREMENT` and the private and delegated paths `PASSED_MEASUREMENT`, with `failed_paths == ['public']` — no per-path pooling.
- `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs::a_consume_committed_before_the_cut_still_reconciles_late_facts` (RS-C06(b)/RS-C07 in-memory mirror): a consume committed before the cut still reconciles its late fact under the tombstone fence (`PaymentConfirmed`); the dead delegate fence is refused (`ExecutionFenced`); a fresh `reserve` and the still-pending `mark_payment_unknown` of a pre-cut `Held` order are refused `GrantClosed`; the unresolved order keeps blocking `undelegate_page`.
- Row updates only where the missing sentence is now asserted: RS-C09 `PARTIAL` → `COVERED_LOCALNET` (the `shield-then-public refusals` record and the Move tests were already cited); IM-03 `PARTIAL` → `COVERED_MODEL_OR_MEMORY`; IM-04 `PARTIAL` → `COVERED_LOCALNET`. RS-C06, RS-C07, RS-C14, RS-C16, IM-14 and IM-29 stay `PARTIAL` with reduced missing text. New counts: predicate `COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`; IM `COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2`.
- Not done on purpose: no Move test added or run (the Move-side gaps stay named open in the cells), no profile, contract, decision, task, register, workflow or checker change, no `reference/rights_scale/sui|zk|vectors` or `reference/v0.3-rc1` byte changed.

## Changed paths

| Path | Change |
|---|---|
| `reference/rights_scale/test_private_model.py` | +2 tests: RS-C09 public-then-private refusal; IM-14 log-ceiling bound at 11 sizes. |
| `reference/rights_scale/test_model.py` | +3 tests: RS-C06(b)/RS-C07 cut ordering both ways plus preserved commitment; IM-04/IM-29 Issuance slot+generation values; IM-03 read-only object keys around the four public ops. |
| `reference/rights_scale/test_summarize_load.py` | +1 test: RS-C14 per-path separation on a synthetic report. |
| `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs` | +1 test: cut-versus-consume in both orders, late-fact reconciliation under the tombstone fence; new imports `amount`, `CaptureObservation`, `ObservationOutcome`, `Hash32`. |
| `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` | Rows RS-C06, RS-C07, RS-C09, RS-C14, RS-C16; the `Counts:` line; the basis and one non-claim bullet now name this update. |
| `docs/status/RS_IM_EVIDENCE_MAP.md` | Rows IM-03, IM-04, IM-14, IM-29; the `Counts:` line; the basis and one non-claim bullet now name this update. |
| `docs/README.md` | One bullet linking this record in the 2026-10-19 index. |
| `validation/2026-10-19-rs-model-gap-closure/README.md` | This record. |

## AGENTS.md section 7: existing coverage per named gap

Each named gap was re-verified against the current test bodies before any test was written. "Still open" means no existing body asserts the missing sentence.

| Gap | Pre-existing coverage | Class before | New test |
|---|---|---|---|
| RS-C09 public-then-private | `test_an_honest_proof_is_recorded_once` and `test_the_same_note_cannot_be_spent_with_a_new_challenge` cover nullifier replay only; nothing consumes publicly then shields. | partially covered | `test_a_publicly_consumed_ticket_cannot_be_shielded` |
| RS-C06(b)/RS-C07 orderings | `test_the_cut_blocks_every_delegated_path_and_delegation` and `the_cut_refuses_new_commitments_but_replays_stored_results` exercise the cut-then-attempt order only; no test commits a paid issue pre-cut then cuts, or reconciles a late fact post-cut; `show.payments` preservation at revocation was unasserted. | partially covered | `test_the_cut_orders_a_delegated_consume_and_paid_issue_both_ways`; `a_consume_committed_before_the_cut_still_reconciles_late_facts` |
| RS-C16 omitted control | `test_c16_wrong_page_is_rejected_everywhere` covers wrong page/shard only. Omission is not constructible in the model (ShowControl is the method receiver, not an argument) — no test added. | partially covered, reduced gap text only | none |
| IM-04/IM-29 event fields | `test_each_issue_emits_two_events` counts events; no body read slot/generation values. | partially covered | `test_the_issuance_event_carries_the_slot_and_the_generation` |
| IM-03 unwritten objects | `test_the_package_surface_is_exactly_the_section_3_operations_plus_read_only_views` covers the surface, not per-op writes. | partially covered | `test_offer_accept_gift_authorize_admission_and_consume_write_only_the_ticket` |
| IM-14 slot-bit rule | `test_a_show_larger_than_the_tree_cannot_enable_the_private_path` exercises only 1024/1025. | partially covered | `test_the_slot_bit_bound_is_the_log_ceiling_at_several_sizes` |
| RS-C14 per-path separation | `test_page_divergence_fails` checks only the corrupted path's verdict; `test_matching_snapshot_passes` checks the all-pass case; no body asserted one path's failure leaves the others' verdicts. | partially covered | `test_a_failed_path_is_reported_separately` |

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** Every exercised behaviour matched the profile sentences the maps paraphrase: `EClosed` on `shield` of a consumed ticket, `EGrantClosed` on every delegated path after `revoke_grant`, `EDelegated` on the stranded reclaim, `ERange` on `claim_zk` above `2 ** ZK_DEPTH`, per-path `FAILED`/`PASSED_MEASUREMENT` separation in `receipt.json`, tombstone-fence fact reconciliation and `GrantClosed` at the map gate in `kix-delegated-exec`.

**B. Contract undefined (characterizations and remaining uncertainty; nothing amended).**

1. RS-C09: the model has no leaf-membership check inside `consume_private` — a proof carries the note label and the verifier binding, so "spend privately" of a note-less ticket is not constructible as a call; the test asserts the shield refusal and the absence of any note and nullifier instead. The Move-side clause (a public consume followed by `shield` in one PTB) has no Move test; the row cell says so.
2. RS-C16: omitting the control is not constructible in the model (the ShowControl is `self`) and a `None` grant raises `AttributeError`, not `Abort`; no test was added, and the missing cell now records this rather than "not exercised".
3. IM-14: the slot-bit rule is exposed in the model only as the `claim_zk` capacity bound `capacity <= 2 ** ZK_DEPTH` (`SLOT_BITS == ZK_DEPTH` in the client constants); the commitment layout `H(secret, slot, generation, domain, 1)` remains untested, and the row stays `PARTIAL`.
4. IM-29: the section 6 arithmetic ceiling for two events per issue (`MAX_BUNDLE_CHAIN`) is untested and stays UNDETERMINED; the row stays `PARTIAL`.
5. RS-C14: the new evidence runs `summarize_load.py` on synthetic records, not a real run report; the row stays `PARTIAL` and says so.

**C. Explicit contract violations.** None found; no locked file was touched and no reproduction was needed.

## Commands actually run and results

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | both `39146a44187af4b43ac57148661bc3af2fb3104f`; clean tree, branch `agent/kix-plan-rs-model-gap-closure` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — both match |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | exit 0: `Ran 121 tests ... OK` (was 115 at base; +6 new) |
| `cd runtime && cargo test -p kix-delegated-exec --locked` | exit 0: all test binaries pass, including `a_consume_committed_before_the_cut_still_reconciles_late_facts` (delegation_fence.rs 12/12) |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0: `rows=23 expected=23 citations=159 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0: all negative controls detected, ends `self-test: pass` |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0: `rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0: all negative controls detected, ends `self-test: pass` |
| `python3 scripts/check_status_register.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_rs_profile_traceability.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_read_model_source_map.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_docs_index.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_i12_proof_ids.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_delegation_layer_matrix.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_contract_error_codes.py` + `--self-test` | exit 0 / `self-test: pass` |
| `cargo clippy --workspace --all-targets --locked -- -D warnings` (in `runtime/`) | exit 0, no warnings |
| `cargo fmt --all -- --check` (in `runtime/`) | exit 0, no diff |
| `cargo test --workspace --locked` (in `runtime/`) | exit 0: all workspace tests pass |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | exit 0 each |
| `git diff --stat origin/main -- reference/rights_scale/sui reference/rights_scale/zk reference/rights_scale/vectors reference/v0.3-rc1 runtime/crates/kix-kernel .aiops docs/tasks docs/contracts docs/decisions` | empty output |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after) | same two blobs — both match |

Not run: `sui move test`, the localnet runners, the ZK setup/test jobs, `scripts/run_localnet*.py`, Node, `check_openapi_contract.py`, `check_integration_gate_openapi.py`, `check_sdk_client.py` and the `integration_gate`/`readiness` unittest step — nothing under `client/`, `sui/`, `zk/`, `vectors/`, OpenAPI, SDK or readiness paths changed.

## Explicit non-claims / what was not tested

- Not an Astra review or acceptance; no register row changed; no grade is raised and the operational count stays 0.
- No Sui, ZK, Move, localnet or Node run. The Move-side gaps named in the cells stay open: no Move test cuts a grant against a paid issue, replays a publicly consumed ticket into `shield`, or omits a control.
- `COVERED_LOCALNET`/`COVERED_MODEL_OR_MEMORY` are builder readings of the cited bodies under each map's own vocabulary; they are not proofs that the predicates hold on chain, under concurrency, or in production. The new evidence is in-memory: the Python model and the `kix-delegated-exec` map, plus a synthetic report through `summarize_load.py`.
- No production durability, distributed fencing, bank exactly-once, chain finality or legal claim is made or inferred.

## Remaining uncertainty and follow-up candidates

- RS-C06(b) still lacks a Move test cutting a grant against a paid issue; RS-C14 still lacks a real-run report check; IM-14's commitment layout and IM-29's section 6 arithmetic stay open, each as its reduced missing cell states.
- Exact-head KTX and KIX protocol CI results are not known; they are for the pull request closure report.
