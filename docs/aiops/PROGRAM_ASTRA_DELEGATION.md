# kix-protocol — 프로그램 위임 초안

상태: NON_EXECUTABLE_DRAFT / PENDING_APPROVAL_DO_NOT_DISPATCH. 범위·시작 승인과 설치/qualification은 아직 완료되지 않았다. 전체 정의 정본은 `docs/aiops/KIX_PROGRAM_DRAFT.json`와 등록 manifest의 pending catalogue다. ID·spec·선행을 보존하고 계약 변경의 병합 flag/등급을 아래 판정대로 바꿨다.

## 정책 C — 대표님 결정 2026-10-01

원문: [중앙 #47 결정 기록](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/47#issuecomment-5927605393). Fable PASS가 나온 위임 노드는 보호된 중앙 executor가 자동 병합한다. `contract_change=YES`, `RELEASE`, `user_merge=true`는 대표님이 병합한다. 계약 변경 노드는 `user_merge=true`, `audit_floor=A3`, `astra_auto_merge=false`로 기록한다. 기존 대표님 전용 노드도 유지한다. 동적 감사에서 계약 변경 YES가 나오면 정적 NO 판정에도 자동 병합하지 않는다.

공개 계약·schema·protocol·operation·capability·BUILD_ID·ruleVersion·solverVersion·SDK/manifest 형식 변경을 계약 변경으로 판정했다. 선행 설계가 있다고 해서 실제 공개 형식 변경의 대표님 병합을 면제하지 않는다. 구현·소비 노드의 NO는 채택된 의미/형식을 그대로 지키는 범위이며, 변경이 필요해지면 YES/A3/User 경계로 다시 분류한다. 비작성자 exact-HEAD 리뷰·CI·제품 gate·호스트에 결합된 보호된 PASS·정확한 병합 HEAD를 모두 요구한다. GitHub 댓글만으로 protected receipt를 만들지 않는다.

이전 위임에서 계약 변경도 자동 병합하도록 둔 flag를 아래 표의 대표님 경계로 바꿨다. DAG나 과거 전달/승인 증거를 새 승인으로 전이하지 않는다. 개발 DONE·실환경 qualification·화면/작품 acceptance·release는 각각 독립 증거가 필요하다. UNKNOWN fencing·단일 writer·금융/chain/외부 전송/과금/공개 운영 잠금은 유지한다.

## 노드별 spec 판정 (82개)

| Node | contract_change | 병합 | audit_floor | spec 근거 |
|---|---|---|---|---|
| `roadmap-sync` | NO | 정책 C 위임 | A1 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `agents-scope-sync` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `sui-commit-mismatch-note` | NO | 정책 C 위임 | A1 | 선행에서 채택한 계약의 구현·소비; 새로운 공개 의미/형식 변경은 제외 |
| `p-sdk-0` | YES | 대표님 | A3 | TypeScript SDK 생성물·BOOTSTRAP manifest 공개 형식 |
| `openapi-catalogue-promotion` | YES | 대표님 | A3 | 새 FSM command/receipt·OpenAPI catalogue 계약 |
| `move-primary-price-fee` | YES | 대표님 | A3 | Move primary issuance 가격·수수료 계약 |
| `ai-delegation-contract-mock` | YES | 대표님 | A3 | AI query/propose/execute 위임 권한 계약 |
| `readiness-extensions` | YES | 대표님 | A3 | 명시 schema migration·budget/overload·wrapper operation 의미 |
| `settlement-policy-deepening` | YES | 대표님 | A3 | F01–F03 분배·환불 정책 계약 개정 |
| `booking-resale-admission-deepening` | YES | 대표님 | A3 | 예약·재판매·입장·보상 명령 및 권한 계약 |
| `f04-mock-deepening` | YES | 대표님 | A3 | F04 mock 조건·한도·상환 계약 개정 |
| `toss-method-expansion-review` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `gate-browser-access-decision` | YES | 대표님 | A3 | loopback CORS/relay 접근 capability 결정 |
| `gate-browser-access` | YES | 대표님 | A3 | 승인된 browser gate 동작·OPTIONS operation 계약 |
| `read-model-contract` | YES | 대표님 | A3 | 새 read/list query·visibility/cursor 계약 |
| `read-model-reference` | YES | 대표님 | A3 | 새 조회 command/receipt·OpenAPI 형식 추가 |
| `p-sdk-1` | YES | 대표님 | A3 | 확장 command/query catalogue의 SDK 형식 갱신 |
| `k1-e4-residual-review` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k1-adapter-event-identity` | YES | 대표님 | A3 | 전송/event/payment/operation identity 계약 |
| `k1-cut-proof` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `k1-open-inputs-brief` | NO | 정책 C 위임 | A1 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k1-evidence-close` | NO | 정책 C 위임 | A1 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `k-stage2-v5-design-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `k-stage2-v5-impl` | YES | 대표님 | A3 | 새 v5 lifecycle/release/index 공개 동작 |
| `k2-retention-proposal` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `k-stage3-schema-sdk-conformance` | NO | 정책 C 위임 | A3 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `k-stage4-comparison-plan` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k-readiness-conformance-suite` | NO | 정책 C 위임 | A2 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `k-stage4-local-exploration` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k-stage4-adoption-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `k-stage5-durable-tx` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k-onsale-admission-control` | YES | 대표님 | A3 | R4 waiting-room·GA routing 계약 개정 |
| `k-stage6-economics-reference` | YES | 대표님 | A3 | OrderLine·quote·capture/allocation/refund/payout 참조 계약 |
| `k-stage7-authenticated-export` | YES | 대표님 | A3 | authenticated source-cut export/manifest 형식 |
| `k-stage7-cpu-analytics-sql-audit` | NO | 정책 C 위임 | A2 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `k-stage8-gpu-plan` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k-a-reestimate` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `k-a-integration-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `rs-0` | YES | 대표님 | A3 | RIGHTS_SCALE_PROFILE·RR 규칙/권리 계약 |
| `rs-1` | YES | 대표님 | A3 | 새 Move package·rights scale schema/operation |
| `rs-1-issuercap-probe` | NO | 정책 C 위임 | A2 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `rs-2` | YES | 대표님 | A3 | 새 circuit/Verifier·manifest v2 형식 |
| `rs-3a` | YES | 대표님 | A3 | GrantControl·page grant/revocation operation 계약 |
| `rs-3b` | YES | 대표님 | A3 | page→inventory/GA counters 공개 매핑 계약 |
| `rs-4-l1` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `rs-4-l2` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `rs-4-l3` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `testnet-key-management-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `rs-5-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `tl-a` | YES | 대표님 | A3 | 토큰 역할·범위·기존 권리와의 분리 계약 ADR |
| `tl-0` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `tl-price-source-contract` | YES | 대표님 | A3 | 토큰 price source/staleness/error 계약 |
| `tl-1` | YES | 대표님 | A3 | 토큰 authority/lifecycle·bridge interface 계약 |
| `tl-coin-lock-adr` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `tl-2` | YES | 대표님 | A3 | 새 localnet token package·Move 공개 schema/operation |
| `tl-3-offchain` | YES | 대표님 | A3 | reward-transaction coupling 참조 계약 |
| `tl-3-onchain` | YES | 대표님 | A3 | localnet reward record schema/operation |
| `tl-4` | NO | 정책 C 위임 | A3 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `tl-legal-brief` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `tl-5-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `ai-delegation-execution-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `f04-real-funds-lift-criteria` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `toss-sandbox-conformance-plan` | NO | 정책 C 위임 | A2 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `public-endpoint-readiness-plan` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `sdk-1-0-decision` | NO | 대표님 | A3 | 기존 대표님 결정/실환경 수용의 user_merge 경계 보존 |
| `ktx-kix-rename-plan` | NO | 정책 C 위임 | A2 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `contract-compatibility-profile` | YES | 대표님 | A3 | immutable producer manifest·SDK profile/verifier 형식 |
| `wave7-marketing-contracts` | YES | 대표님 | A3 | M01–M04·M05 consent 공개 계약 |
| `protocol-runtime-boundary-register` | NO | 정책 C 위임 | A3 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `protocol-featureir-conformance` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `protocol-canonical-identity-conformance` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `protocol-read-projection-evidence` | YES | 대표님 | A3 | ReadObservationV1·query/source-cut/cursor schema |
| `protocol-local-recovery-conformance` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `protocol-integration-evidence-closeout` | NO | 정책 C 위임 | A3 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `fin-ledger-contract` | YES | 대표님 | A3 | versioned Finance projection/authority·numeric schema ADR |
| `fin-double-entry-projection` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `fin-observation-reconciliation` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `fin-multi-payee-refund-proof` | NO | 정책 C 위임 | A3 | spec의 승인된 동작 구현 또는 문서/계획 정리; 새 공개 계약 정의 없음 |
| `fin-credit-exposure-reconciliation` | NO | 정책 C 위임 | A3 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |
| `fin-consistent-accounting-export` | YES | 대표님 | A3 | Finance accounting export schema/manifest 형식 특화 |
| `fin-catalogue-read-model` | YES | 대표님 | A3 | 새 Finance read query/schema·SDK/producer manifest |
| `fin-finance-closeout` | NO | 정책 C 위임 | A3 | 기존 승인 계약의 시험·측정·증거/수용 인계; 새 계약 정의 없음 |

## 중앙 및 시작 경계

채택 검토 source는 [중앙 #47](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/47) `09e161caa652d75e9617caf632b3b9899be35740` 하나다. source 후보로 구현됐으며 설치·독립 A3·User 채택·실제 host qualification·activation은 PENDING이다. runtime/client pin이나 host record는 이 변경으로 바꾸지 않는다. 과거 checkpoint 목록과 별도 시작 PR 절차는 [REGISTRATION_SCOPE_APPROVAL_KO.md](REGISTRATION_SCOPE_APPROVAL_KO.md)를 따른다.

외부 선행은 pending catalogue에 둔다. 실제 저장소/program/node·plan/definition·delivery HEAD·merge SHA·필요한 post-merge 검증의 보호된 완료를 확인한 뒤, 별도 대표님 병합 plan revision에서 변환 전/후 digest와 근거를 기록해 승격한다. 현 schema v1은 빈 `depends_on_external`도 거부한다. 미완료·UNKNOWN·wrong-revision을 삭제해서 실행하지 않는다. bootstrap/범위/시작 PR은 자동 병합할 program delivery가 아니다.
