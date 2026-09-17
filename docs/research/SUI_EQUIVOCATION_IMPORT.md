# Sui 조사 원문 게시와 적용 범위

작성·공식 소스 재확인: 2026-09-17 (Asia/Seoul). 문서만 변경한다.
원문은 [SUI_EQUIVOCATION_REPLICATION_RESEARCH_5440de0cf721.md](SUI_EQUIVOCATION_REPLICATION_RESEARCH_5440de0cf721.md)에 바이트 그대로 보존한다.

## 1. 원문 식별과 시점

| 구분 | 값 |
|---|---|
| 원문 전체 Git blob | `5440de0cf721932398af87344fe59d48b9858ad3` |
| 실제 크기 | 47,408바이트 |
| 원문 SHA-256 | `c49dd2e1444a860a684b6ac10250ff84ef2eba6fba1d064d8c230173388d4d75` |
| 원문 조사 시점 T0 | 2026-09-16~2026-09-17, Asia/Seoul |
| 원문 KIX 검토 commit | `94376835ea4fc818619fc79e2be4df7d4947496a` |
| 원문 Sui 기준 릴리스 | `mainnet-v1.79.1`, protocol 136 |
| Sui 고정 소스 commit | `58386edc269ef88ff0f40ab0a9d50e87cba80ca8` |

원문의 확인 시점·기준 commit·출처·제안·미확인 사항을 현재 시제로 다시 쓰지 않는다.
이번 게시 메타데이터나 경고를 원문 안에 추가하지 않았다. 원문 안의 기성 도구·gas·
shared/owned 비교는 당시 조사 내용으로 보존하며 이번 객체 배치나 제품 채택의 결정이 아니다.
연구 결과는 `docs/research/`, 진행 조건은 기존 정본 `docs/DEVELOPMENT_PLAN.md §9.1`로
분리한다. 같은 진행 조건을 두 문서에서 독립적으로 정의하지 않는다.

## 2. 요청 기준과 실제 원격 상태

요청 기준은 'PR #17 병합 후 최신 main'이다. 작업 시작 시 실제 main은
`3cbb8df3a466fe171d7261f9090c324a458af3f6`이고 #17은 open/draft/미병합이었다.
따라서 **#17 병합 후 main을 확보했다고 표시하지 않는다.**

이번 문서 초안은 #17의 head `c5d2792170e8e476370a064b8a7de626a5213412`, tree
`20b9538f9d48ad513c2f2ea28c478d01c758b01d` 위의 별도 후속 브랜치로 제출한다.
비교 base는 #17의 `codex/docs-lc-term-authority-v04-20260917` 브랜치다.
#17이나 main을 임의 병합·변경하지 않으며, 기존 계약 0.4도 수정하지 않는다.
#17이 실제 병합되면 새 main과 차이·충돌·CI를 다시 확인해야 하며, 이번 기록으로
그 확인이나 병합을 했다고 간주하지 않는다. CI는 제출 head의 실제 실행만 보고한다.

## 3. 제거된 메커니즘과 남은 조건

| 항목 | 기록할 구분 |
|---|---|
| 제거된 것 | 소유 객체의 **합의 전 잠금 분열 때문에 다음 epoch까지 동결되는 메커니즘**. 조사 기준 Mainnet 릴리스에서는 제거됨 |
| 남은 것 | 정확한 owned 입력 version/digest의 유효성과 동일 버전의 단일 소비. 서로 다른 업무 intent의 경쟁을 무제한 허용한다는 뜻이 아님 |
| 남은 것 | 구 리더가 이미 서명·외부 노출한 거래의 정체성·관측·결과 인계. 로컬 leader 교체나 fence는 이미 나온 거래를 취소하지 못함 |
| 사용하지 않을 전제 | 과거 epoch 동결을 현재 failover RTO·필수 epoch 대기·R2 비용 증액의 근거로 사용하는 것 |
| 이번에 확인하지 않은 것 | KIX 대상 RPC의 live binary/protocol/feature 상태, 실제 체인 호출·rescue·장애 재현·성능 |

원문 §§0·1-1·2-1·2-2가 근거다. 공식 변경 기록과 고정 릴리스 소스를 이번에도 읽어
원문의 중심 구분을 대조했다. 이는 대상 네트워크를 실측한 독립 검증 결과는 아니다.

- [Sui PR #24676](https://github.com/MystenLabs/sui/pull/24676): pre-consensus에서 post-consensus 잠금으로 이동하는 변경. 병합일을 Mainnet 활성화일로 간주하지 않는다.
- [Sui PR #26278](https://github.com/MystenLabs/sui/pull/26278): Mainnet protocol v105부터 해당 경로가 활성화됐다는 후속 기록.
- [고정 object_locks.rs](https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-core/src/execution_cache/object_locks.rs): 전체 Git blob `8fff6c191c690e803a1bb901a0cf7b5765167985`. version/digest 검사와 합의 후 잠금을 확인.
- [고정 릴리스](https://github.com/MystenLabs/sui/releases/tag/mainnet-v1.79.1): protocol 136. 이번 문서는 이 조사 기준을 보존하며 이후 모든 릴리스를 확인한 것으로 확대하지 않는다.

## 4. 저장소 전제 검색의 범위

색인 검색은 빈 결과와 `incomplete_results: true`를 반환했다. 그것으로 부재를
판정하지 않았다. 고정 main/#17 tree의 경로·blob과 확보한 전체 문서 바이트를
대조하고 `equivocat`, `pre-consensus`, `동결`, `freeze/frozen`, `epoch/에포크` 등으로
검색했으며, 추가로 #17의 전체 변경분과 관련 Sui/Move 설계 문서를 직접 읽었다.

**이 범위에서 '소유 객체 equivocation은 현행에서도 다음 epoch까지 동결된다'를
전제로 채택한 기존 문장은 발견하지 못했다.** 판매/취소 epoch나 ZK 증명 현재성은
소유 객체 합의 전 잠금 동결과 다른 용어다. 확인된 오류 문장이 있어 수정한 것으로
꾸미지 않았으며, §9.1에 향후 잘못된 전제를 사용하지 않도록 구분을 명시했다.

다만 전체 저장소 checkout과 모든 파일 바이트 검색은 완료하지 못했다. tree 목록은
본문 검사가 아니고, 일부 본문과 코드/로그 미확인 범위가 남는다. 따라서 '저장소
전체에 없다'는 전수 부재 판정은 하지 않는다. 상세 검색 경로·실제 일치·미확인 목록은
제출 검색 증거에서 구분한다. 이번에 새로 게시하는 원문의 과거 동결 설명은 역사적
동작을 설명하고 현행에서 배제하는 것이므로, 옛 전제를 현행 채택하는 문장이 아니다.

## 5. 이번 반영의 한계

향후 R2가 별도 승인되면 **객체당 논리적 서명 권한 단일화**와 **구 리더 미확정 거래
인계**를 반드시 다루는 조건을 개발계획 §9.1에 기록했다. 동일 bytes 재전달과 새
transaction 생성, 내부 fencing과 체인 종결, 회수 이후 재송신 권한을 구분한다.
**독립적인 R2 작업량 추정치는 없다. 숫자 없음.** (a) 또는 첫 묶음의 추정을 R2로
전용하지 않는다. 두 사항 기록만으로 R2의 모든 선행조건을 충족하거나 착수를 승인하지 않는다.

커널·wire·설정·어댑터·저널·실험 코드 변경 없음. R2·(a) 금지 유지.
객체 배치 설계·Kiosk·zkLogin·SDK/gas 모드 선택은 이번 작업 범위가 아니다.
실제 거래·서명·rescue·배포·보호 규칙·태그 변경도 하지 않는다.
