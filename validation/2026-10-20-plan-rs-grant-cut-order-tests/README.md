# plan-rs-grant-cut-order-tests

Node: `plan-rs-grant-cut-order-tests`. Adds deterministic `test_scenario` Move unit tests that order the `revoke_grant` cut against delegated paid issuance (`attest_issuance_delegated` + `issue_paid_delegated`) and against delegated-page admission consumption (`authorize_admission` + `consume` on a ticket minted under the grant), in both serial orders, then updates only the RS-C06/RS-C07 rows of `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`.
Issue: none. Depends on: `rs-3a`, `rs-3b`, `plan-rs-predicate-evidence-map`, `plan-rs-model-gap-closure`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792381171 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA and no final task head SHA, and no KTX kernel verification or KIX protocol verification run exists for this work. The exact-head CI results belong in the pull request closure report (AGENTS.md section 11).

Observed `origin/main` = branch HEAD = `08119a41b7c8088a0e9d40bd35228af33d795643`, on the worktree `origin/main` ref. No `git fetch` was run: the supervisor forbids network/GitHub actions in builder sessions, so AGENTS.md section 1's read-only fetch was skipped and the recorded base is the ref the worktree was created from.

**This record and the map updates are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, the operational count stays 0, no Sui testnet/mainnet or localnet run was made, and each status remains a builder reading of the cited bodies.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match the required blobs before and after. The diff of `reference/v0.3-rc1`, `reference/rights_scale/sui/sources`, `reference/rights_scale/zk`, `reference/rights_scale/vectors`, `runtime/crates/kix-kernel`, `.aiops`, `docs/tasks`, `docs/contracts` and `docs/decisions` against `origin/main` is empty (commands below). No profile byte, Move source file, vector, circuit, manifest, K, P, S, W value, `MAX_BUNDLE_CHAIN`, `IssuerCap` custody choice, grant TTL/limit/allowed-operation set, or entry point changed.

## What this change does

- Six new tests in `reference/rights_scale/sui/tests/delegation_tests.move` close the executable part of the Move-side RS-C06(b)/RS-C07 gap named at the base:
  - `a_paid_issue_committed_before_the_cut_stands` (paid issue before cut): a completed delegated paid issue survives `revoke_grant` — ticket `holder == b`, `state == 0` (ACTIVE), `version == 1`, `last_amount == 50000`, `last_payment == ref` — the page totals keep `issued == 1`, the grant reads generation 2 / closed, and the page↔grant binding itself survives.
  - `the_cut_refuses_the_second_leg_of_a_paid_issue` (cut before paid issue): `reserve_delegated` then `revoke_grant` then `issue_paid_delegated` aborts with `EGrantClosed` (24) at `check_grant`.
  - `an_unissued_commitment_stays_observable_after_the_cut`: the stranded reservation stays `reserved == 1`, the delegate-owned `IssuancePayment` still reads slot 2 / the payment ref / expected generation 0 through the public views, and the page stays bound to the closed grant.
  - `a_consume_committed_before_the_cut_stands` (consume before cut): issue, authorize, consume, then cut — the ticket reads `state == 1` (CONSUMED), `version == 2`, grant generation 2 / closed.
  - `an_admission_committed_before_the_cut_completes_after_it` (cut before consume): issue, authorize, cut, then `consume` completes — `consume`/`authorize_admission` are ticket-path writes gated by `live()`, not by `check_grant`; the grant-checked set is exactly the five delegated paths of profile section 10.3, so the cut does not strand a live ticket's committed admission. This asserts the contract-defined outcome; it does not add a refusal that the contract does not have.
  - `a_consumed_ticket_cannot_use_the_cut_grant`: issue, authorize, consume, cut, then `refund_delegated` aborts `EGrantClosed` — `check_grant` precedes the liveness check there, so the closed-grant error wins even on a consumed ticket.
- `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`: RS-C06 row gains the six new Move citations in half (b) and the missing cell now reads that the Move tests exercise the cut against a delegated paid issue and a delegated-page admission consume in both serial orders (the localnet race probe still covers cancel-versus-issue, half (a), only). RS-C07 row gains the observability citations (`an_unissued_commitment_stays_observable_after_the_cut`, `an_admission_committed_before_the_cut_completes_after_it`, `a_consume_committed_before_the_cut_stands`) and its missing cell records that preservation of the unissued commitment and completion of a pre-cut-committed admission are now exercised on Move while the changed-authority late-fact reconciliation stays model/in-memory only (A-4, LC-CUT). Both statuses stay `PARTIAL`; the `Counts:` line is unchanged (`13/2/6/0/2`). The basis bullet names this node and its observed base; the non-claims bullet carves out that this update's Move tests were run with `sui move test`.
- No checker script changed: `check_rs_predicate_evidence_map.py` already accepts `reference/rights_scale/sui/tests/[a-z_]+\.move` paths and `#[test]`/`expected_failure` function symbols.
- Not done on purpose: no Move source, profile, contract, decision, task, register, workflow or checker change; no `reference/v0.3-rc1` byte changed; no IssuerCap custody, TTL, limit, policy or allowed-operation value chosen; no new entry point or command; no localnet measurement.

## Changed paths

| Path | Change |
|---|---|
| `reference/rights_scale/sui/tests/delegation_tests.move` | +6 tests in a "cut ordering" section; the `use` line gains `IssuancePayment`. |
| `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` | Rows RS-C06, RS-C07 (Move cells and missing cells); the basis bullet and one non-claim bullet now name this update. Statuses and `Counts:` unchanged. |
| `docs/README.md` | One bullet linking this record in a new 2026-10-20 index section. |
| `validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md` | This record. |

## AGENTS.md section 7: existing coverage per named gap

Each named gap was re-verified against the current test and source bodies before any test was written. "Still open" means no existing body asserts the missing sentence.

| Gap | Pre-existing coverage | Class before | New test |
|---|---|---|---|
| RS-C06(b) cut vs delegated paid issue, both orders | `the_cut_blocks_delegated_attest` and `the_cut_blocks_delegated_cancel` cover cut-then-attempt only; `delegated_paid_flow_mints_to_the_buyer` covers the happy path with no cut; no Move body committed a paid issue before the cut or presented one after. | partially covered | `a_paid_issue_committed_before_the_cut_stands`, `the_cut_refuses_the_second_leg_of_a_paid_issue` |
| RS-C06(b)/RS-C07 cut vs delegated-page admission consume, both orders | No existing body interleaves `authorize_admission`/`consume` with `revoke_grant`; the in-memory mirror `a_consume_committed_before_the_cut_still_reconciles_late_facts` and the model `test_the_cut_orders_a_delegated_consume_and_paid_issue_both_ways` cover the analogues off-chain only. | partially covered | `a_consume_committed_before_the_cut_stands`, `an_admission_committed_before_the_cut_completes_after_it` |
| RS-C07(b) preservation/observability of the unissued commitment at revocation | `a_page_with_a_stranded_reservation_cannot_be_reclaimed` asserts the reclaim block but never reads the stranded reservation or the delegate-held `IssuancePayment` after the cut. | partially covered | `an_unissued_commitment_stays_observable_after_the_cut` |
| Post-cut delegated use of the old grant on a consumed ticket | The `the_cut_blocks_delegated_*` tests refuse on live objects only; no body orders the closed-grant check against a terminal ticket state. | not covered | `a_consumed_ticket_cannot_use_the_cut_grant` |

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** Every exercised behaviour matched the profile sentences the map paraphrases: `EGrantClosed` on `issue_paid_delegated` and `refund_delegated` after `revoke_grant`; pre-cut ticket facts, totals, the page↔grant binding and the delegate-held `IssuancePayment` unchanged by the cut; a committed admission completing post-cut because `consume` is ticket-path (`live()`) and not in the section 10.3 grant-checked five-path set.

**B. Contract undefined (characterizations and remaining uncertainty; nothing amended).**

1. The grant has no TTL/expiry and no allowed-operation set (`create_grant`'s own comment: adding either is a profile decision). The tests assert nothing about either.
2. A stranded delegated reservation has no resolution path on chain — the delegate-owned `IssuancePayment` cannot be presented to any post-cut entry point, so the page stays unreclaimable. The tests record this as observability plus the existing `EDelegated` reclaim refusal; whether a release path should exist is a profile question, not answered here.
3. The model/in-memory late-fact reconciliation under a changed authority (RS-C07(b), A-4/LC-CUT) has no chain analogue — the Move tests exercise only what the current contract defines.

**C. Explicit contract violations.** None found; no locked file was touched and no reproduction was needed.

## Commands actually run and results

| Command | Result |
|---|---|
| `git status`; `git rev-parse HEAD origin/main` | clean tree at base; both `08119a41b7c8088a0e9d40bd35228af33d795643`; branch `agent/kix-plan-rs-grant-cut-order-tests` (`git fetch` skipped per the builder no-network rule) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — both match |
| `python3 scripts/configure_local.py` | created the checkout-local `client.yaml`/`sui.keystore` (empty keystore; ignored `.local/`) |
| `sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights_scale/sui` (pinned binary `sui 1.79.1-808640d9b49a`, the `toolchains.json` release, reused from a sibling worktree; git deps served from the local `~/.move` cache) | exit 0: `Test result: OK. Total tests: 258; passed: 258; failed: 0` (was 252 at base; +6 new) |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | exit 0: `Ran 121 tests ... OK` (unchanged; no Python model change) |
| `cd runtime && cargo test -p kix-delegated-exec --locked` | exit 0: all test binaries pass (delegation_fence.rs included; no Rust change) |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0: `rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` (was 159 citations at base; +9) |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0: all negative controls detected, ends `self-test: pass` |
| `python3 scripts/check_docs_index.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_status_register.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_rs_profile_traceability.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_read_model_source_map.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_rs_im_evidence_map.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_tl_predicate_evidence_map.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_i12_proof_ids.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_delegation_layer_matrix.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_contract_error_codes.py` + `--self-test` | exit 0 / `self-test: pass` |
| `cargo fmt --all -- --check` (in `runtime/`) | exit 0, no diff |
| `cargo clippy --workspace --all-targets --locked -- -D warnings` (in `runtime/`) | exit 0, no warnings |
| `cargo test --workspace --locked` (in `runtime/`) | exit 0: all workspace test binaries pass |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | exit 0 each |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0: `Ran 71 tests ... OK` (no path under `integration_gate`/`readiness` changed) |
| `python3 scripts/check_openapi_contract.py` + `--self-test` | exit 0 / `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` + `--self-test` | exit 0 / `self-test: pass` |
| `git diff --stat origin/main -- reference/v0.3-rc1 reference/rights_scale/sui/sources reference/rights_scale/zk reference/rights_scale/vectors runtime/crates/kix-kernel .aiops docs/tasks docs/contracts docs/decisions` | empty output |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after) | same two blobs — both match |

Not run: `scripts/run_localnet_rights_scale.py`, `scripts/run_localnet_rights_scale_private.py`, the ZK setup/test steps and `scripts/check_sdk_client.py` — they need the bootstrap venv (`PyYAML`), `npm ci` and Node 24, none of which exist in this environment and installing them is a network action the builder may not take; the `rights-scale` and `protocol` jobs of the exact-head KIX protocol workflow remain the evidence. Nothing under `client/`, `zk/`, `vectors/`, `sdk/`, `integration_gate` or `readiness` changed.

## Explicit non-claims / what was not tested

- Not an Astra review or acceptance; no register row changed; no grade is raised and the operational count stays 0.
- `test_scenario` only: no localnet, testnet, mainnet, ZK or Node run; no real payment, PG, bank, KYC or external endpoint of any kind.
- `PARTIAL` stays `PARTIAL`: RS-C06 still lacks a localnet probe of the cut against delegated operations (the one race probe is half (a) only), and the changed-authority reconciliation of RS-C07(b) has no chain analogue by design (A-4, LC-CUT).
- The tests characterize the existing `check_grant`/`live` split; they do not test IssuerCap custody choices, grant TTL, limits, allowed-operation sets or any policy value — all remain UNDETERMINED.
- No production durability, distributed fencing, bank exactly-once, chain finality or legal claim is made or inferred.

## Remaining uncertainty and follow-up candidates

- If a future task reads "cut-before-consume" as requiring a post-cut *refusal* of a committed admission, that is a contract/semantics change outside this node — the current contract completes it and the new test asserts exactly that.
- The stranded delegated `IssuancePayment` has no post-cut release path; if the profile ever wants one it is a new decision (profile section 10.5).
- Exact-head KTX and KIX protocol CI results are not known; they are for the pull request closure report.
