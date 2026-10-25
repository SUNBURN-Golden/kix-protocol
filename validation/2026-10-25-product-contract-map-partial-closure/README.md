# Product contract map partial-gap closure

Builder-authored local evidence, not a review or an acceptance; no grade change.

Node: `plan-product-contract-map-partial-closure`. Immutable input is the
supervisor-provided node specification and read-only design in this session.
Issue: none; no node task document exists under `docs/tasks/` and none was
created. `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` is historical wave
context, not a new instruction to execute its original Wave 1 work.
This is not an ASTRA program-mode session.

Observed cached `origin/main`, branch base and initial HEAD are all
`01f6c04c71dac27fab5d17017f4e837c076218c6`, on
`agent/kix-plan-product-contract-map-partial-closure`. Initial worktree: clean.
There is no observed base delta. Fetch is NOT_RUN because the supervisor forbids
network actions; remote freshness is unverified. Contract/map historical SHAs
remain historical and are not this task's base.

Implementation/final committed task HEAD: not created in this builder session.
HEAD remains the base above; deliverable is the uncommitted worktree patch.
No commit, push, PR, issue, comment, merge or external action was performed.
Exact-head KTX CI and KIX protocol CI: NOT_RUN; run IDs/status/conclusions are
unavailable, reserved to the supervisor. Merge SHA/post-merge CI/final merge
blob checks: not applicable. READY means locally complete for supervisor handoff,
not merge-ready or independently reviewed.

## Existing coverage and closed gaps

| Requirement | Before adding tests | Evidence/change | Resulting map row |
|---|---|---|---|
| (a) BRA limits | PARTIALLY covered by `test_mock_gates.py::GateTests.test_show_registration_bounds`, `test_contract_error_codes.py::GateErrorCodeGapTests.test_bad_clock_value_is_clock`, seeded gate/property and rejection tests. `test_primary_price_binding.py` also tests synthetic primary-price extremes, but not the whole §1 matrix. | Seven direct `ContractLimitBoundaryTests` in `test_contract_limit_boundaries.py`: gate ID and organizer label 100/101 and str subclass/bool; both show amount fields at 10**12/+1; clock 10**15/+1; corresponding reservation show fields, all three FSM idempotency keys and clocks; unchanged gate views/journals on rejection. | BRA §1 COVERED |
| (b) Settlement label | NOT covered by a direct assertion in the existing settlement happy-path test. | `test_settlement_catalogue.py::SettlementCatalogueTests.test_view_lifecycle_authority_is_in_memory_fsm` asserts IN_MEMORY_FSM in initiate/authorize/capture/commit/fail results and INITIATED/COMMITTED/FAILED views. | Settlement §9 COVERED together with (d) |
| (c) F04 face consumption | SUFFICIENTLY covered; map omitted cross-suite evidence. | Existing `test_mock_credit.py::CreditAdvanceMockTests.test_note_reserves_unpaid_face_without_funds_or_license` reads the Wave 3 `MockSettlement.view`, asserts snapshot_frozen and unchanged settlement. `test_claims_do_not_share_a_ceiling_and_the_snapshot_stays_frozen` rejects a later statement/distribution face and a changed caller mark with FACE_SNAPSHOT_FROZEN. Cited without duplicate tests. | Settlement §9.6 COVERED |
| (d) Offline catalogue names | PARTIALLY covered outside the suites by `scripts/check_openapi_contract.py`; no direct suite regression. F04's existing `CreditFsmTests.test_offer_approve_draw_repay_and_close_are_mock_ledger_only` already calls the direct lifecycle-label assertion in `assert_not_lending`. | `SettlementCatalogueTests.test_replayable_names_match_the_contract_only_catalogue` and `CreditCatalogueTests.test_replayable_names_match_the_contract_only_catalogue` compare every REPLAYABLE name to the OpenAPI action-body map/local operation IDs and FSM pin machine/command sets, exclude helper operations, retain the frozen protocol's 40 commands with no new prefixed names. Settlement also retains historical capture/settle_capture names. Reads only the three pinned JSON files; no network or generation. | Settlement §9 and F04 §7 COVERED |

No mock/FSM/contract semantics, limits, policy values or commands changed.
All newly exercised predicates match the existing contracts (AGENTS §8 class A).
No new class C violation or new contract-undefined behavior was found. Existing
class B observations remain characterized and are not promoted.

The settlement checker permits only the named F04 mock test file, only on §9.6,
with its existing AST symbol check and subtree symlink guard. Two added negative
controls reject that credit citation on another row and an unlisted credit file
on §9.6. The passing real map is also the positive cross-suite control.

| Map | Before (COVERED/PARTIAL/NOT_COVERED/OPEN) | After | Additional open items |
|---|---|---|---|
| Settlement (27 clauses) | 12/5/2/8 | 14/3/2/8 | none |
| BRA (39 clauses) | 21/15/1/2 | 22/14/1/2 | 9, unchanged |
| F04 (22 clauses) | 13/5/1/3 | 14/4/1/3 | 5, unchanged |

COVERED for Settlement §9 and F04 §7 establishes only local mock labels and
command-name agreement. Byte-level catalogue pins are checked separately by
`check_openapi_contract.py`; no new byte-history, authority or grade claim follows.

## Every gap left open

The following are copied from the resulting maps, including adopted open-item
rows. They retain their status and reason; no policy owner is replaced or value
filled. BRA §9/§10/§11 full catalogue/authority/grade gaps remain outside (d).
Settlement §9.2's pre-existing class B normative/descriptive interpretation needs
non-author semantic review; a conservation test cannot decide it.

### Settlement

| Clause/item | Status | Remaining gap/reason | Owner as recorded |
|---|---|---|---|
| §0.1 | NOT_COVERED | No settlement-suite test verifies the kernel scan, capture comparisons or reservation/lifecycle responsibilities; the contract records that historical scan. | none |
| §0.2 | PARTIAL | PRIMARY_FEE_BPS produces at most two payees per claim; arbitrary cardinality is untested. PG split-payment permission remains unconfirmed (PG_TOSS_CARD_PROFILE §8). | none |
| §0.3 | OPEN | UNDETERMINED residual-unit priority method and recipient nomination. Contract names no specific recipient owner; use its header/R-9 product-policy decision route, not a nominated payee. | DECISION_REQUIRED · Astra |
| §7.1 | OPEN | UNDETERMINED legal debtor/creditor identities and legal treatment; party/jurisdiction/material inputs precede legal advice. | 사용자(당사자·관할·자료), 그 다음 법무 |
| §7.2 | OPEN | UNDETERMINED costs, tiers, caps and payment timing; accounting cost definition also remains open. | 사용자와 회계 |
| §7.3 | OPEN | UNDETERMINED priority method and recipient nomination. No specific payee owner is named in this clause; header/R-9 gives the product-policy decision route. | DECISION_REQUIRED · Astra |
| §7.4 | OPEN | UNDETERMINED resale bps; S1–S3 are not adopted. | 사용자 |
| §7.5 | OPEN | UNDETERMINED tax nature/rates, reserve rates and accounting classification, retention and release timing; no release switch. | 사용자(관할·자료), 그 다음 세무·회계 |
| §7.6 | OPEN | UNDETERMINED legal refund debtor and partial-refund bearer; B1–B4 not adopted. | 사용자 → 법무, I10 경로 |
| §7.7 | OPEN | UNDETERMINED future P04 close evidence/implementation; storage and real PG/bank observation unlocks remain deferred under program §5. | 사용자(프로그램 결정 §5) |
| §7.8 | NOT_COVERED | UNDETERMINED / unopened items, not implementation requests. This clause names no owner; none is invented. No tests establish these external/product predicates. | none |
| §8 | PARTIAL | Non-implementation, legal/production non-claims, unchanged grades, historical-reference preservation and absence of signing/commitment cannot be established by these settlement tests. | none |
| §9.2 | PARTIAL | Existing class B zero-cash-commit characterization reaches distribute; §9.2 says zero-cash freeze is outside FSM acceptance. Prior record leaves descriptive versus normative interpretation for reviewer confirmation (see notes); conservation alone does not settle it. | none |

### BRA

| Clause/item | Status | Remaining gap/reason | Owner as recorded |
|---|---|---|---|
| §0 | PARTIAL | Flags and local evidence do not establish chain/bank authority, legal effects, performance or production non-claims. | none |
| §4 | PARTIAL | Local locks and false cross_channel_exclusive are tested; R05 currentness across executors/channels is NOT_COVERED (§7.3). | none |
| §7.1 | OPEN | UNDETERMINED policy/legal/provider inputs; the table below retains every named owner and the storage lock route. | 사용자 |
| §7.2 | OPEN | UNDETERMINED values remain with §7.1 owners; B/C are not adopted. | 사용자 |
| §7.3 | NOT_COVERED | Chain grant/finality, named seats/300-seat unification, live PG/bank/webhooks, actual buyer evidence availability, currentness across executors/channels, production admission routing, kernel lifecycle, general durability/exactly-once/compliance, TPS/p99/failure rates, apps/funds, reservation resale/F04 commands and settlement policy integration remain unopened. No owner is invented. | none |
| §7.4 | PARTIAL | Grade preservation and general non-claims cannot be proved by mock tests; full OpenAPI/catalogue pins belong to check_openapi_contract.py. | none |
| §8 | PARTIAL | Legal/production non-claims, historical-reference byte preservation and grades require separate guards; these are local reference tests. | none |
| §9 | PARTIAL | Full protocol_contract.json/OpenAPI pins and authority/grade assertions lie outside the reservation suite; no chain, legal or admission authority follows. | none |
| §9.3 | PARTIAL | Threads, other executors and other channels are not covered; cross_channel_exclusive remains false and §7.3 remains NOT_COVERED. | none |
| §9.7 | PARTIAL | Grades, production authority, durable/chain/bank exactly-once and full architectural non-claims are not established by local tests. | none |
| §10 | PARTIAL | Full catalogue/REPLAYABLE pins and legal/market/grade claims are outside these local tests; lifecycle_authority is not independently certified. | none |
| §10.4 | PARTIAL | No threads, cross-executor/channel currentness or production R05 exclusivity; cross_channel_exclusive stays false (§7.3). | none |
| §10.9 | PARTIAL | Grades, external legal/market/bank exactly-once, production routing and durable-journal non-claims remain outside these assertions. | none |
| §11 | PARTIAL | Core catalogue count and unprefixed loopback rejection are tested; full prefixed OpenAPI catalogue pins, authority and grades require separate checks. | none |
| §11.2 | PARTIAL | Clock-skew rejection can leave a delegated reservation authorization (recorded class B); no general atomicity across machines is established. Injected faults are separate characterizations (§4). | none |
| §11.4 | PARTIAL | Sequential single-process scenarios only; threads and other executors/channels, bypass paths and production routing remain NOT_COVERED in §7.3. | none |
| §11.7 | PARTIAL | Non-claims about grades, legal/chain/venue authority, durable/bank/venue exactly-once and all bypass paths cannot be established by this suite. | none |
| `actor-authentication-revocation` | OPEN | UNDETERMINED identity/KYC legal treatment; role flags stay false. | 사용자와 법률·개인정보 담당 |
| `durable-show-config` | OPEN | UNDETERMINED future durability; storage engine remains locked by §5 잠금; no legal value is attached to this row. | §5 잠금 |
| `approved-reservation-ttl` | OPEN | UNDETERMINED statutory hold limit and product TTL; 900_000/120_000ms remain fixtures. | 사용자와 법률 담당 |
| `discounts-and-coupons` | OPEN | UNDETERMINED discount/coupon tax and accounting treatment; quote_ref remains opaque. | 사용자와 세무·회계 담당 |
| `payment-attesters-authority` | OPEN | UNDETERMINED Toss attestation/webhook signature meaning; no attester authority is verified. | 사용자와 토스 기술 담당 (I02, I04) |
| `compensation-after-payment-fact` | OPEN | UNDETERMINED refund obligation, accounting treatment and settlement bearer; no compensation record is created. | 사용자와 법률 담당; 사용자와 회계 담당; settlement-policy-deepening |
| `resale-failure-compensation-seller-payout` | OPEN | UNDETERMINED seller-payment legal/tax/accounting treatment and resale acquiring scope; seller_due is only face allocation. | 사용자와 법률·세무·회계 담당; 사용자와 토스 영업 담당 (I03) |
| `refund-revoke-shield-gift-cancel-show` | OPEN | UNDETERMINED refund/revocation/show-cancellation legal effects; generation stays 1; no forbidden commands. | 사용자와 법률 담당 |
| `consume-private-delegated-sessions` | OPEN | UNDETERMINED delegated-session privacy; private circuit remains rs-2 scope, not invoked by this revision. | 사용자와 법률·개인정보 담당 |

### F04

| Clause/item | Status | Remaining gap/reason | Owner as recorded |
|---|---|---|---|
| §5 | OPEN | UNDETERMINED product policy numbers; remaining non-policy gaps are not opened by this map. | Astra |
| §5.1 | OPEN | UNDETERMINED legal parties, APR/schedule, rank, perfection and recalculation. | Astra; 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 당사자·관할·자료는 I10; 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 대항요건은 I10과 같은 법무 경로 |
| §5.2 | OPEN | UNDETERMINED; per-item owners and unresolved values are preserved below. | Astra; 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 당사자·관할·자료는 I10; 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 대항요건은 I10과 같은 법무 경로 |
| §5.3 | PARTIAL | Only adopted A behavior is exercised; unadopted B/C/D alternatives have no behavioral tests. | none |
| §5.4 | NOT_COVERED | UNDETERMINED unopened semantics, evidence, performance and new-command decisions; no owner named in this clause. | none |
| §5.5 | PARTIAL | Command count and forbidden names are asserted; complete OpenAPI/SDK/manifest byte preservation is outside this suite. | none |
| §6 | PARTIAL | The suite does not prove historical Wave 3 or reference/v0.3-rc1 byte preservation, licensing or external guarantees. | none |
| §7.9 | PARTIAL | Durability, legal treatment, licensing, bank exactly-once, chain finality, live HTTP and commerce-apps behavior are not tested. | none |
| `legal-parties` | OPEN | UNDETERMINED: Legal identities of lender, borrower, secured party and refund debtor | 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 당사자·관할·자료는 I10 |
| `interest-apr-schedule` | OPEN | UNDETERMINED: APR, fees, tenor and repayment schedule | Astra |
| `seniority` | OPEN | UNDETERMINED: Seniority and distribution rank | Astra |
| `perfection` | OPEN | UNDETERMINED: Perfection, registration, possession and external pledge | 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 대항요건은 I10과 같은 법무 경로 |
| `limit-recalculation` | OPEN | UNDETERMINED: Limit recalculation after the first frozen face | Astra |

## Commands and actual results

Before edits, the three complete suites passed: settlement 194, BRA 405,
F04 147 tests. Narrow new-module runs passed: BRA 7, settlement 2, F04 1.
The three map checkers then passed with their self-tests: settlement 33 negative
controls (including two new), BRA 50, F04 55.

All 45 broader commands below exited 0. The first 35 are extracted verbatim
from the `Stdlib offline document checks` run block in
`.github/workflows/protocol.yml` (no workflow edit). The remaining ten match its
reference-suite, non-production integration and OpenAPI steps. The runner used
foreground `subprocess.run` sequentially, with `PYTHONDONTWRITEBYTECODE=1` in its
environment; there were no background shell jobs, automatic retries or failures.
Invocation: `python3 /tmp/kix-product-partial-closure-verify.py`; temporary runner
and output logs are outside the deliverable. Commands and outcomes are retained
here so the evidence does not depend on those temporary files.

| Command actually run | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | exit 0; docs index ok: scanned=243 indexed=208 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | exit 0; self-test: pass; self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | exit 0; self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=2 items=9 citations=38 COVERED=1 PARTIAL=6 NOT_COVERED=2 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0; self-test: pass (72 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | exit 0; self-test: pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0; Ran 196 tests in 1.687s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | exit 0; Ran 412 tests in 9.530s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0; Ran 148 tests in 26.643s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0; Ran 85 tests in 4.699s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; Ran 168 tests in 2.870s; OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0; Ran 100 tests in 15.277s; OK; self-test: pass |
| `python3 scripts/check_openapi_contract.py` | exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0; self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0; self-test: pass |

The earlier focused verification also exited 0:

| Command actually run | Actual result |
|---|---|
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" \|\| exit; done` | Before edits: 194 / 405 / 147 tests, all OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_contract_limit_boundaries.py` | 7 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03 -p test_settlement_catalogue.py` | 2 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_credit_catalogue.py` | 1 test, OK |
| `for checker in settlement bra credit; do python3 "scripts/check_${checker}_evidence_map.py" \|\| exit; python3 "scripts/check_${checker}_evidence_map.py" --self-test \|\| exit; done` | All three maps pass; 33 / 50 / 55 negative controls pass |

The final documentation/preservation checks are recorded below; no further
business-code change followed the complete runs above.


## Preservation, deviations and limitations

Before edits, `git rev-parse HEAD:<path>` and `git hash-object <path>` matched:

| Locked file | Required and observed before/after blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Initial `HEAD:reference/v0.3-rc1` tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`, unchanged at final HEAD.
A read-only Python comparison against `git ls-tree -rz HEAD -- reference/v0.3-rc1`
computed each on-disk Git blob hash (including the blob header): all **108**
tracked files are byte-identical. No frozen file was edited or transiently mutated.

| Command/check actually run | Actual result |
|---|---|
| `git branch --show-current` | `agent/kix-plan-product-contract-map-partial-closure` |
| `git rev-parse origin/main HEAD` (before and after) | Both `01f6c04c71dac27fab5d17017f4e837c076218c6` |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs HEAD:reference/v0.3-rc1` (before and after) | Two required blobs and frozen tree shown above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both match required blobs above |
| Read-only Python `git ls-tree -rz HEAD -- reference/v0.3-rc1` plus Git-blob SHA-1 comparison | 108/108 tracked file bytes match HEAD |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 .aiops docs/tasks .github/workflows runtime` | exit 0, no diff |
| `git status --porcelain -- reference/v0.3-rc1 .aiops docs/tasks .github/workflows` | empty |
| `git diff --check` | exit 0, no whitespace errors |
| `python3 scripts/check_docs_index.py` (after final record update) | exit 0; scanned=243 indexed=208 allowlisted=35 |
| `git diff --name-only HEAD` and `git ls-files --others --exclude-standard` | Nine changed/new paths listed below |

Complete changed-path list (all uncommitted):

- `reference/booking_resale_admission/test_contract_limit_boundaries.py`
- `reference/settlement_f01_f03/test_settlement_catalogue.py`
- `reference/credit_advance_f04/test_credit_catalogue.py`
- `scripts/check_settlement_evidence_map.py`
- `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md`
- `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md`
- `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-25-product-contract-map-partial-closure/README.md`

Deviations: fetch omitted per the supervisor's explicit no-network instruction.
The FSM identifier regression additionally checks organizer_role and bool keys;
these are already defined input predicates, not new policy. The catalogue tests
also check exact prefixed FSM command keys, strengthening name agreement.
No other design deviation is intended.

Observed follow-up, deliberately not fixed: old map/checker prose describing the
checkers as local-only/not wired into protocol.yml is stale since PR #289. The
new local execution does not rewrite the original historical basis/results.
Other follow-up routes are the recorded policy owners, kernel scan evidence,
SDK/manifest/historical-byte evidence and non-author semantic review.

Rust cargo test/clippy/fmt: NOT_RUN, no Rust or Cargo paths changed. The closest
local equivalents for touched Python/document paths are the complete protocol
stdlib block, reference suites, integration tests and OpenAPI pin checks.
Full Rust/Move/Node/ZK CI, external systems, production durability, distributed
fencing, bank exactly-once, legal/compliance/licensing, chain finality, hardware
and performance were not tested or claimed. Real funds, PG/bank/KYC calls,
public endpoints, Sui, secrets, storage engines and production runtime remain
locked. The capability register and all grades stay unchanged.
