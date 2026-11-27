# PF-C05 offline primary/resale bps isolation

2026-10-26. Builder-authored, source-informed evidence, not independent review,
acceptance or a grade change. Node: `plan-plan-primary-fee-pf-c05-isolation-tests`.
Immutable task input: supervisor-provided specification and Sonnet design in the
session; no issue or matching task document under `docs/tasks/`. Historical Task
005 supplies wave context only. No task input was edited.

Branch: `agent/kix-plan-plan-primary-fee-pf-c05-isolation-tests`.
Observed cached `origin/main`, base, initial and final Git HEAD:
`a38e1679449e74186c5a4e3d19b6cb79f6b791d5`.
Implementation is the uncommitted working-tree patch; no implementation/final
commit was created. No local base delta. Remote freshness is unverified: the
supervisor's explicit no-network instruction overrides AGENTS.md §1 fetch.
No git/GitHub publication, issue, comment, merge or history mutation was done.
Exact-head KTX/protocol CI run IDs/status/conclusions: not obtained (network and
publication prohibited). Merge SHA and post-merge CI: not applicable.
Local completion is a supervisor handoff, not a merge-ready assertion.

## Existing coverage before additions (AGENTS.md §7)

| Requirement | Prior coverage | Inspected evidence and gap |
|---|---|---|
| Primary paid-price binding | Sufficient for PF-C01 alone; not covered for PF-C05 variation | `reference/booking_resale_admission/test_primary_price_binding.py::PrimaryPriceBindingPfC01Tests` (boundary/invalid/seeded); `test_mock_gates.py::GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay`. Neither varies resale bps. |
| Primary fee arithmetic | Sufficient for PF-C02 alone; not covered for PF-C05 variation | `reference/settlement_f01_f03/test_primary_fee_split.py::PrimaryFeeSplitPfC02Tests`; `test_settlement_properties.py::SplitPropertyTests`; `test_mock_settlement.py::SettlementMockTests.test_f01_fee_floor_zero_fee_and_rejected_policies`. Neither checks issued gross across resale bps. |
| Resale list/accept and settlement gate | Partial | `reference/booking_resale_admission/test_resale_fsm.py::ResaleFsmTests.test_transfer_is_idempotent_and_does_not_reissue_a_credential` and `ResaleFsmTests.test_bound_transfer_waits_for_mock_commit_and_reconciles` with its `settlement_at` helper exercise lifecycle with fee_bps=0; no fee-variation comparison. |
| Resale BPS_SUM versus primary fee | Not covered for isolation | `reference/booking_resale_admission/test_mock_gates.py::GateTests.test_show_registration_bounds` rejects invalid resale sums alone, without primary-fee variation. |
| Sibling import origin | Existing pattern sufficient | `test_resale_fsm.py` uses guarded index-1 insertion; settlement `test_primary_fee_split.py::SiblingImportPathTests` checks its own origin. New module adds a guard for its four imports. |

## New evidence and interpretation

All new tests are in
`reference/booking_resale_admission/test_primary_resale_bps_isolation.py`.
Direct methods of `PrimaryResaleBpsIsolationPfC05Tests` cover:

- `test_resale_bps_do_not_change_primary_binding`: exact-price binding, payment
  and issuance envelopes, wrong-price rejection and absence of resale dues.
  Only the show view's two verified bps input echoes are removed for comparison.
- `test_resale_bps_do_not_change_primary_fee_split`: issued gross feeds a fresh
  `MockSettlement`; full obligations match the baseline and a floor/residual
  oracle with zero-line suppression. Changing primary bps is a positive control.
- `test_primary_fee_bps_do_not_change_resale_list_and_accept`: real in-memory
  `SettlementMachine` source, stable settlement ID, whole listing/accept envelopes
  and canonical resale state equal across primary fees; dues match a resale
  oracle. Transfer/version and observed settlement commit prove progress, and
  varying resale bps supplies a positive control.
- `test_resale_bps_sum_bound_independent_of_primary_fee`: each price and primary
  fee accepts resale sum=10000 end to end, including primary fee=10000. Excessive
  resale sums reject as BPS_SUM on registration and adoption, individual bps=10001
  as BPS; invalid primary fee=10001 rejects as POLICY_FEE_BPS on both settlement
  entry points after each valid resale pair.
- `test_seeded_isolation`: 20 draws per seed 41/43/47 check both directions and
  the split oracle against corresponding baselines.

Boundary prices: 1, 7777, 10**12. Primary bps: 0, 1, 9999, 10000.
Eight resale boundary pairs, plus generated pairs constrained to sum<=10000.
All numbers and roles are synthetic fixtures, not product policy; no 100000/500
adapter fixture is adopted. `PfC05SiblingImportPathTests` checks both suite
origins and excludes the frozen reference from the module import-time sys.path.
It snapshots that environment because existing admission HTTP tests later call
`integration_gate.catalogue.reference_types()` and add the frozen path.

Class A: the exercised PF-C05 Python predicates match; no coupling/class C
violation was found. Class B characterization: booking has no primary fee field;
settlement has no resale field; the existing resale settlement gate inspects
phase, gross, currency and finality flags, not policy. Statement component fee
is distinct from primary obligation fee: the existing `amount=gross, fee=0`
commit fixture succeeds at every tested fee_bps, so no fallback was necessary.
No shared-field or on-chain enforcement semantics are inferred.

The evidence map now has PF-C05 PARTIAL for Python only and a separate
`chain:PF-C05` NOT_COVERED row. Counts recomputed from clause rows:
COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5; on-chain NOT_COVERED=3.
PF-C03/PF-C04 and all nine open items retain their decisions/owners. The checker
permits PF-C05 PARTIAL/NOT_COVERED only, preserves Astra/decision markers, and
requires the third chain row. Negative controls check invalid promotions, owner
and marker drift, the missing chain row, and stale counts.

## Changed paths

- `reference/booking_resale_admission/test_primary_resale_bps_isolation.py`
- `docs/status/PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md`
- `scripts/check_primary_price_fee_evidence_map.py`
- `docs/README.md`
- `validation/2026-10-26-plan-primary-fee-pf-c05-isolation-tests/README.md`

## Actual commands and results

Run from repository root with Python 3.13.5 (CI requests Python 3.12).
All final verification commands below exited 0. Read-only inspection used
`cat`, `sed`, `rg`, `git diff`, `git status` and Git object/ref queries.
No external network action or background job was launched.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; both refs equal the SHA above; expected task branch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before edits) | Both required blobs match: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -k PfC05 -v` | PASS: 6 tests, on both initial and post-fix runs. |


| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" \|\| exit; done` (first run) | Settlement PASS 196; booking FAIL 1/418 (new import guard observed a path added by an existing earlier HTTP test). Loop exited 1 before the other suites. No isolation assertion failed. |
| Same five-suite loop (after import-time guard fix) | PASS: settlement 196, booking 418, credit 148, delegation 85, reward 168; total 1015 tests. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS: 100 tests; embedded self-test pass. Existing unclosed-file ResourceWarning observed, no failure. These tests use loopback only. |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | PASS: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5. |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS: 76 negative controls and direct TestCase selection. |
| `python3 scripts/check_docs_index.py`; same with `--self-test` | PASS: scanned=246 indexed=211 allowlisted=35; self-test pass. |
| `python3 scripts/check_status_register.py`; same with `--self-test` | PASS: paths=385 ev_ids=15 original32=32; self-test pass. |
| Workflow-derived foreground Python harness: each invocation in protocol.yml's `Stdlib offline document checks`, then the four OpenAPI invocations below | PASS: 41 checker invocations, each exit 0. Exact checker inventory below. |
| `python3 scripts/check_openapi_contract.py`; same with `--self-test` | PASS: commands=84 core=40 fsm=44; self-test pass. |
| `python3 scripts/check_integration_gate_openapi.py`; same with `--self-test` | PASS: commands=84 productionEndpoint=false publicHost=false; self-test pass. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after tests) | Both required blobs match the before values. |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 '*.move' docs/contracts runtime .github .aiops docs/tasks` | PASS: empty protected-path diff; no protected untracked paths in status. |
| `git diff --check`; `git status --short`; `git rev-parse origin/main HEAD` | PASS: no whitespace errors; only the five changed paths listed above; refs unchanged at the recorded SHA. |

The workflow harness extracted every `python3 scripts/` line from the stdlib
step, ran it with `subprocess.run(shlex.split(command), capture_output=True)`,
printed exit status and final output line, and stopped on any nonzero result.
It did not execute unrelated workflow code. Each of the following was run both
plain and with `--self-test` (all PASS):

```text
python3 scripts/check_status_register.py
python3 scripts/check_rs_profile_traceability.py
python3 scripts/check_read_model_source_map.py
python3 scripts/check_docs_index.py
python3 scripts/check_i12_proof_ids.py
python3 scripts/check_delegation_layer_matrix.py
python3 scripts/check_rs_predicate_evidence_map.py
python3 scripts/check_rs_im_evidence_map.py
python3 scripts/check_tl_predicate_evidence_map.py
python3 scripts/check_contract_error_codes.py
python3 scripts/check_adapter_identity_map.py
python3 scripts/check_v5_transition_evidence_map.py
python3 scripts/check_readiness_evidence_map.py
python3 scripts/check_settlement_evidence_map.py
python3 scripts/check_bra_evidence_map.py
python3 scripts/check_credit_evidence_map.py
python3 scripts/check_primary_price_fee_evidence_map.py
python3 scripts/check_ai_delegation_evidence_map.py
```

`python3 scripts/check_stage5_host.py --self-test` also passed (plain host check
is excluded by CI). BRA reports 39 headings, 9 open items and 219 citations;
contract error-code check reports 199 rows, all raised/asserted/covered, no class
B/C discrepancy. This is checker output, not on-chain or production acceptance.

## Limits, deviations and follow-up

No mock, FSM, fee value, contract, Move, frozen reference, locked kernel, CI,
`.aiops/` or task-document change. No real funds/provider/KYC, public endpoint,
Sui network, secrets, paid service, equipment, storage engine or production
runtime was required. No DECISION_REQUIRED stop condition was encountered.

Deviations from design: the binding helper also checks an in-range wrong price
at price=1 (2); boundary resale tests run at all three prices; invalid primary
fee is checked on both settlement entry points; checker adds a decision-marker
negative control. The import guard checks a module-load snapshot, rather than
the global sys.path after other test bodies have run: the first full booking
run exposed pre-existing admission HTTP path mutation. Only this new guard was
changed; module-origin checks remain live. Fetch omitted and all Git/GitHub
publication deferred by explicit supervisor instruction. No settlement-suite file or arithmetic helper
change was needed.

On-chain PF-C01/PF-C02/PF-C05 remain NOT_COVERED. Enforcement location, policy
values, fee inclusion/recipient/refund treatment and the allocation schema remain
DECISION_REQUIRED · Astra or UNDETERMINED with named owners. No chain finality,
funds receipt, durability, distributed fencing, exactly-once, legal/tax compliance,
performance or production readiness claim. No Rust/Move/localnet/SDK build was
run because those implementations are untouched. Non-author exact-head review,
remote CI and any publication/merge remain supervisor/User work.

Final local state: READY for supervisor handoff; no merge-readiness claim.
