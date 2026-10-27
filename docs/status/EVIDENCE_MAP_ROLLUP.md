> **Builder-authored index, not a review, an acceptance or a grade.**

# Contract evidence-map roll-up

Node: `plan-plan-evidence-map-rollup-check`. Observed `origin/main`, `FETCH_HEAD`
after `git fetch origin main`, and starting branch HEAD:
`d2b748aef0c7b4af5bef23c771c6bce22b52905f`. This is index and evidence for
`k-local-program-closeout` only.
The consistency checker is `scripts/check_evidence_map_rollup.py` (stdlib;
plain and `--self-test`).

Scope: every regular file under `docs/contracts/**` and every
`runtime/*_V1.md`, including CANONICAL_BINARY_BCS_V1 and FEATURE_SEMANTICS_V1.
Counts lines are copied verbatim in each map's own status words, never summed
across maps or translated. A shared map is repeated for each applicable contract.
Multiple maps, checkers and Counts copies occupy corresponding `<br>` entries.

Open rows are rows whose owner cell, as the map itself assigns it, is not
`none`. The roll-up does not classify status words. Owners below are distinct
whole owner cells, copied verbatim in first-appearance order across the named
maps. `no owner column` describes a map without that column; it assigns nobody.
No map's status, owner or grade is changed. No-map reasons report existing
scope or stops; they close no open decision or UNDETERMINED value.

## 1. Contract roll-up

| Contract | Evidence map | Checker | Counts (verbatim) | Open-row owners | No-map reason |
|---|---|---|---|---|---|
| `docs/contracts/ADAPTER_EVENT_IDENTITY.md` | `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md` | `scripts/check_adapter_identity_map.py` | `Counts: CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8` | TM04<br>k1-adapter-event-identity<br>DECISION_REQUIRED · Astra; k-stage5-durable-tx<br>k-stage5-durable-tx<br>DECISION_REQUIRED · Astra<br>DECISION_REQUIRED · Astra; TM04 | none |
| `docs/contracts/AI_DELEGATION_AUTHORITY.md` | `docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_ai_delegation_evidence_map.py` | `Counts: COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1` | Astra (U11-L)<br>Astra (U11-L); Astra와 사용자 (U11-ID); Astra; `k1-cut-proof`, RS-3a; 법무 검토 (D-E, 사용자); 후속 노드; `ai-delegation-execution-decision` (사용자 병합) | none |
| `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` | `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_bra_evidence_map.py` | `Counts: COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2` | 사용자 | none |
| `docs/contracts/CONTRACT_INVARIANTS.md` | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md` | `scripts/check_contract_invariants_evidence_map.py` | `Counts: rows=27 COVERED=10 PARTIAL=12 NOT_COVERED=3 OPEN=2` | Kernel contract owner; non-author A2 reviewer<br>Contract owner<br>User: separate PG/bank authorization; I13 operations/security<br>Supervisor: exact-head KTX and KIX protocol CI; non-author A2 reviewer<br>I11 issuer/User; lifecycle contract owner<br>Contract owner; non-author A2 reviewer<br>User: separate R2 authorization; I12 proof reviewer/User trust-policy approval | none |
| `docs/contracts/CREDIT_ADVANCE_F04.md` | `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_credit_evidence_map.py` | `Counts: COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3` | Astra<br>Astra; 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 당사자·관할·자료는 I10; 사용자. 법률 검토의 주체와 시점은 로드맵 D-E. 대항요건은 I10과 같은 법무 경로 | none |
| `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md` | none | none | none | none | Input sheet: existing I01–I13 inputs and remaining owners, not a clause evidence map (source: FIRST_BATCH_OPEN_INPUTS.md §1). |
| `docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md` | `docs/status/PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_primary_price_fee_evidence_map.py` | `Counts: COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5` | Astra<br>Astra; 사용자, 법률·회계 담당; 토스, 사용자 | none |
| `docs/contracts/PERFORMANCE_BASELINE_V4.md` | none | none | none | none | Historical V4-SMOKE-001 record; cited as historical in PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:83. |
| `docs/contracts/PERFORMANCE_MEASUREMENT.md` | `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md` | `scripts/check_performance_measurement_evidence_map.py` | `Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3` | kix-kernel perf harness maintainer | none |
| `docs/contracts/PG_TOSS_CARD_PROFILE.md` | `docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md` | `scripts/check_toss_card_profile_evidence_map.py` | `Counts: rows=41 COVERED=5 PARTIAL=10 NOT_COVERED=15 OPEN=11` | k-provider-sandbox<br>k-stage5-durable-tx<br>k1-adapter-event-identity<br>토스<br>사용자; 토스 영업 담당자<br>기존 담당자 질문지 5번<br>not named in contract<br>박준태; 박명운 이사 | none |
| `docs/contracts/READINESS_RUNTIME.md` | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md` | `scripts/check_readiness_evidence_map.py` | `Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9` | Astra<br>사용자 승인<br>사용자 명시 승인<br>DECISION_REQUIRED · Astra | none |
| `docs/contracts/READ_MODEL_QUERIES.md` | none | none | none | none | Waits on `read-model-reference` for the reference module/catalogue work (READ_MODEL_QUERIES.md:25, :29); open values remain UNDETERMINED. |
| `docs/contracts/READ_MODEL_SOURCE_MAP.md` | none | `scripts/check_read_model_source_map.py` | none | none | Itself an input source map, not a Counts-line evidence map (READ_MODEL_SOURCE_MAP.md:7, §1). |
| `docs/contracts/RIGHTS_SCALE_PROFILE.md` | `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`<br>`docs/status/RS_IM_EVIDENCE_MAP.md` | `scripts/check_rs_predicate_evidence_map.py`<br>`scripts/check_rs_im_evidence_map.py` | `Counts: COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`<br>`Counts: COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` | RS-1<br>RS-1; DECISION_REQUIRED · Astra<br>RS-1, RS-3a, RS-3b<br>RS-1; RS-1 / Astra<br>RS-1, RS-3a<br>RS-2<br>RS-2; DECISION_REQUIRED · Astra<br>RS-1, RS-2, RS-3a, RS-3b<br>RS-2; RS-4; Astra<br>RS-2가 구조, RS-4가 측정<br>none stated in profile<br>K: DECISION_REQUIRED · Astra<br>RS-2 ; DECISION_REQUIRED · Astra<br>RS-3b와 Track K v5<br>RS-1 / Astra | none |
| `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` | `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_settlement_evidence_map.py` | `Counts: COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8` | DECISION_REQUIRED · Astra<br>사용자(당사자·관할·자료), 그 다음 법무<br>사용자와 회계<br>사용자<br>사용자(관할·자료), 그 다음 세무·회계<br>사용자 → 법무, I10 경로<br>사용자(프로그램 결정 §5) | none |
| `docs/contracts/STATE_LIFECYCLE.md` | `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md`<br>`docs/status/V5_TRANSITION_EVIDENCE_MAP.md` | `scripts/check_lifecycle_adr_evidence_map.py`<br>`scripts/check_v5_transition_evidence_map.py` | `Counts: rows=27 COVERED=6 PARTIAL=17 NOT_COVERED=1 OPEN=3`<br>`Counts: rows=10 TESTED=6 STOPPED=4 OPEN=0` | User: separate integration (a) authorization<br>I12 proof review/User trust policy; I13 operations/security custody<br>I09 User/developer; I10 User/legal/privacy; I13 operations/security<br>I11 issuer/User; review-resolution contract owner<br>I09 User/developer; I13 operations/security; lifecycle contract owner<br>User/lifecycle contract owner; I09 retry scope<br>I12 proof review/User trust policy; I13 operations/security; adapter owner<br>Adapter/integration owner; I13 operations/security<br>I13 operations/security custody; adapter owner<br>I12 proof review/User trust policy; integration (a) owner<br>I12 proof review/User trust policy; future adapter/replay owner<br>I12 non-author independent proof review and User trust-policy approval<br>Ingress/control adapter owner; I12 transfer proof/User trust policy<br>User: separate R2 authorization; future storage integration owner<br>User: separate replay/R2 scope; ingress/upgrade owner<br>Adapter contract owner; I13 custody<br>Adapter contract owner; User: separate R2 authorization<br>Future inventory/policy integration owner; User scope approval<br>Future admission/scheduling owner; I09 User/developer measurements<br>`docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md::I12와 I13이 닫히기 전까지 만들지 않는다`, `validation/2026-10-13-k-stage2-v5-impl/README.md::One-time reserved-slot release`<br>`docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md::그 결론의 내용이 정해지기 전까지 만들지 않는다`, `validation/2026-10-13-k-stage2-v5-impl/README.md::Review release`<br>`docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md::읽기 전용** 자격 보고만 만든다`<br>`docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md::상태를 바꾸는 회수는 **정지**다`, `validation/2026-10-13-k-stage2-v5-impl/README.md::State-changing record/evidence reclamation`<br>`docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md::전이가 열리기 전까지 게이트에 둔다`, `validation/2026-10-13-k-stage2-v5-impl/README.md::Conflict-index upkeep under the three above` | none |
| `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md` | `docs/status/TL_PREDICATE_EVIDENCE_MAP.md` | `scripts/check_tl_predicate_evidence_map.py` | `Counts: HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7` | TL-2<br>TL-3<br>TL-1<br>TL-5<br>TL-4<br>TL-2가 구현을 시험한다. TL-4가 독립적으로 본다<br>TL-1이 증거·브리지 인터페이스를 정한다. TL-2가 토큰 패키지가 없을 때의 기존 시험 통과를 본다<br>TL-3이 풀별 잔액 보존의 오프체인 모델을 맡는다<br>TL-2가 V1부터 V5까지. TL-3이 V6<br>TL-1이 목표와 기록된 예외를 나눈다. TL-2가 구현 시험을 맡는다. 예외가 남아 있는 동안 토큰 발행과 금고 지출은 시작하지 않는다<br>TL-4가 게이트 기록을 검토한다. TL-5가 게이트 기록을 확인하는 판단이다<br>TL-4가 산출물 문구를 본다<br>TL-3이 담보 산정 모델을 맡는다. 자산 선택 자체는 §2의 DECISION_REQUIRED · Astra다<br>TL-1이 정의한다. TL-2가 토큰 패키지가 없을 때의 기존 시험을 본다<br>TL-2. 패키지가 생기기 전에는 대상이 없다<br>TL-1이 B1을 권고한다. 구현은 잠금 해제 뒤다<br>TL-2가 끈 상태와 정지 상태를 시험한다. 켜진 상태의 패키지는 잠금 해제 뒤다<br>TL-3이 오프체인 모델에서 본다<br>TL-1이 정의한다. 위반 대응의 내용은 Astra다<br>TL-2가 경로를 시험한다. 이 파일은 정지를 실행하지 않는다<br>TL-1이 정의한다. TL-2가 구현을 시험한다<br>TL-1이 정의한다. 기존 AI 목은 EXECUTE를 거부한다<br>TL-4가 기록을 검토한다. TL-5가 확인하는 판단이다. 이 파일은 S1 게이트가 아니다<br>같다<br>TL-5. 이 계약이 그 판단을 하지 않는다<br>TL-2가 시험한다. 참·거짓은 **[미확인]**<br>표준 사실은 청사진 인용이다. TL-2가 핀에서 확인한다 | none |
| `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md` | `docs/status/TL_PREDICATE_EVIDENCE_MAP.md` | `scripts/check_tl_predicate_evidence_map.py` | `Counts: HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7` | TL-2<br>TL-3<br>TL-1<br>TL-5<br>TL-4<br>TL-2가 구현을 시험한다. TL-4가 독립적으로 본다<br>TL-1이 증거·브리지 인터페이스를 정한다. TL-2가 토큰 패키지가 없을 때의 기존 시험 통과를 본다<br>TL-3이 풀별 잔액 보존의 오프체인 모델을 맡는다<br>TL-2가 V1부터 V5까지. TL-3이 V6<br>TL-1이 목표와 기록된 예외를 나눈다. TL-2가 구현 시험을 맡는다. 예외가 남아 있는 동안 토큰 발행과 금고 지출은 시작하지 않는다<br>TL-4가 게이트 기록을 검토한다. TL-5가 게이트 기록을 확인하는 판단이다<br>TL-4가 산출물 문구를 본다<br>TL-3이 담보 산정 모델을 맡는다. 자산 선택 자체는 §2의 DECISION_REQUIRED · Astra다<br>TL-1이 정의한다. TL-2가 토큰 패키지가 없을 때의 기존 시험을 본다<br>TL-2. 패키지가 생기기 전에는 대상이 없다<br>TL-1이 B1을 권고한다. 구현은 잠금 해제 뒤다<br>TL-2가 끈 상태와 정지 상태를 시험한다. 켜진 상태의 패키지는 잠금 해제 뒤다<br>TL-3이 오프체인 모델에서 본다<br>TL-1이 정의한다. 위반 대응의 내용은 Astra다<br>TL-2가 경로를 시험한다. 이 파일은 정지를 실행하지 않는다<br>TL-1이 정의한다. TL-2가 구현을 시험한다<br>TL-1이 정의한다. 기존 AI 목은 EXECUTE를 거부한다<br>TL-4가 기록을 검토한다. TL-5가 확인하는 판단이다. 이 파일은 S1 게이트가 아니다<br>같다<br>TL-5. 이 계약이 그 판단을 하지 않는다<br>TL-2가 시험한다. 참·거짓은 **[미확인]**<br>표준 사실은 청사진 인용이다. TL-2가 핀에서 확인한다 | none |
| `docs/contracts/openapi/README.md` | `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_integration_gate_contract_evidence_map.py` | `Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1` | User<br>Supervisor / repository owner controlling the execution host<br>integration_gate maintainer<br>Astra | none |
| `docs/contracts/openapi/fsm-command-contract.json` | none | `scripts/check_openapi_contract.py`<br>`scripts/check_read_model_source_map.py` | none | none | Machine-readable command pin (docs/contracts/openapi/README.md §Files/파일; scripts/check_docs_index.py ALLOWLIST). |
| `docs/contracts/openapi/kix-protocol.contract-only.openapi.json` | none | `scripts/check_openapi_contract.py` | none | none | Machine-readable OpenAPI pin (docs/contracts/openapi/README.md §Files/파일; scripts/check_docs_index.py ALLOWLIST). |
| `docs/contracts/openapi/kix-protocol.integration-gate.openapi.json` | none | `scripts/check_integration_gate_openapi.py`<br>`scripts/check_openapi_contract.py` | none | none | Machine-readable OpenAPI pin (docs/contracts/openapi/README.md §Files/파일; scripts/check_docs_index.py ALLOWLIST). |
| `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md` | none | none | none | none | Clause map blocked by `plan-plan-sdk-compat-manifest-clause-evidence` (DECISION_REQUIRED, User): [SDK compatibility addendum](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md). |
| `runtime/CANONICAL_BINARY_BCS_V1.md` | `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md` | `scripts/check_bcs1_evidence_map.py` | `Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17` | KIX-BCS1 contract owner<br>kix-bcs1 maintainer<br>S08 Move/SDK schema owner | none |
| `runtime/FEATURE_SEMANTICS_V1.md` | `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md` | `scripts/check_feature_semantics_evidence_map.py` | `Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17` | k-stage7-cpu-analytics-sql-audit<br>k-stage7-authenticated-export<br>User | none |

## 2. Cross-contract maps

| Map | Checker | Counts (verbatim) | Open-row owners | Contracts read |
|---|---|---|---|---|
| `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` | `scripts/check_contract_error_codes.py` | `Counts: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0` | no owner column | `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md`<br>`docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`<br>`docs/contracts/CREDIT_ADVANCE_F04.md`<br>`docs/contracts/AI_DELEGATION_AUTHORITY.md` |

The error-code map's ten BRA-RES9 rows are in its earlier key table. The
checker uses the documented row-scope override matching that map's own checker;
this index does not relocate or reinterpret those rows.

## 3. Not rolled up

[AI_DELEGATION_LAYER_MATRIX](AI_DELEGATION_LAYER_MATRIX.md), checked by
`scripts/check_delegation_layer_matrix.py`, is a delegation-layer matrix rather
than a contract Counts-line map. [CURRENT_CAPABILITY_REGISTER](CURRENT_CAPABILITY_REGISTER.md),
checked by `scripts/check_status_register.py`, is a capability register rather
than a contract evidence map. Neither is added to cross-map totals.
