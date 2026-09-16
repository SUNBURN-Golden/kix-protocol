# 상태 수명 계약 — 첫 묶음 초안 0.1

2026-09-16. 기준: 모델 1 승인 및 잠금 R1 v4
`69564b166f0c27f9af5d8422f0a466b18d74c20f`.
상태: **계약 초안 제출**. 일반 안전 규칙과 제공자별 미정 사항을 구분한다.
현재 커널에 종결/회수/해제 명령이나 색인을 추가하지 않는다. R2·(a) 보류 유지.

## 1. A-4와의 중복을 한 번만 정의

| 공통 계약 ID | 첫 묶음에서 정하는 것 | A-4 통합이 재사용할 부분 | 이번에 구현하지 않는 것 |
|---|---|---|---|
| LC-FACT | 늦은 실제 사실의 보존·동일성·새 권한 부여와 분리 | 회수 이후 capture/체인 결과와 미발행 약정 대사 | durable inbox·체인 verifier |
| LC-CUT | 역사 재생/현재 실행 구별, C_g와 H_g의 관계, 금지되는 새 소비 | 저널 재개·snapshot·회수 fence | 로그·분산 회수·상태이관 |
| LC-TERM | 종결 증거·미확정 외부 시도·한 번의 해제 자격 | lease 회수 때 미발행/미사용 판단에 쓸 근거 | final-failure/void·slot-release 전이 |

원계약은 승인 결정서 A-4(원문 blob
`f8a63bc83d2bc00f8e128d10d2b7bd83db84e510`)와 ADR-0001의 §§3–7 및
review addendum이다. 후자는 c8267d1 기준 blob
`07c36869e7b68fff10b02e6c59d7119df56d0785`다.
이 문서는 그 관계를 구체화한 초안이며 미정인 원천 증명을 이미 해결했다고 주장하지 않는다.

## 2. 서로 다른 수명

명령 최초 결과, 주문/operation의 경제 상태, 관측 원문, first-capture 슬롯,
quarantine/review, lease 권한, 메모리 캐시, 법정/사업 보존은 별도 대상이다.
현재 v4의 reserved→stored는 점유 형태 전환일 뿐 총 evidence 예산 회수가 아니다.
권한 만료와 실제 자금 결과의 미확정 여부도 별개다.

| 대상 | 현재 v4 | 향후 종결·회수의 조건 | 금지 |
|---|---|---|---|
| UNKNOWN operation | TTL 뒤에도 유지 | LC-TERM을 만족하는 증거와 모든 시도의 종결/전송 차단 | timeout·단일 not-found로 실패 선언 |
| 예약 슬롯 | 첫 bound capture 때 stored로 전환 | 지원되는 최종 실패/void를 한번만 적용한 뒤 한 번 해제 | 만료/owner 변경으로 해제 |
| 저장 event/conflict | 누적 보존 | active 참조·대사·법적 보존·독립 저장 확인을 모두 검토 | 만석 때문에 삭제 |
| bound quarantine/review | sticky | 권한 있는 결론·근거·영향 operation을 특정 | 같은 관측 재전달로 자동 해제 |
| unbound evidence | 보존된 conflict만 향후 binding 차단 | 종결·보존·재사용 금지 경계와 같이 관리 | evidence를 지워 identity를 새로 사용 |
| command 최초 결과 | 업무상 거절도 기록 | 지원 재시도 범위·원결과 위치·영구 재실행 금지 근거 | cache miss를 새 명령으로 실행 |
| 주문·operation identity | 재사용하지 않음 | 참조와 장기 식별/범위 폐쇄 계약 | owner generation 변경으로 identity 재발급 |

## 3. LC-FACT — 늦은 사실 보존

제공자 수신 원문, provider/account/endpoint/API-version/event-item/operation,
검증 결과와 원문 참조를 수신 ACK 전에 내구성 있게 확보해야 한다. 현재는
inbox 구현이 없으며 이 문장은 ACK할 수 있다는 허가가 아니다. 보존 실패 시
제공자 ACK를 하지 않고 해당 범위의 신규 의도를 제한한다.

같은 event-item의 다른 내용은 원본을 덮어쓰지 않는다. event identity와
경제 operation identity는 서로 다른 중복 경계다. batch delivery id를 서로
다른 capture의 단일 event id로 사용하지 않는다. 구체 제공자 정규화는 미정이다.

회수·만료 뒤 실제 capture 또는 체인 성공이 도착해도 원래 operation/grant/주문에
결합한 사실을 보존한다. 현재의 권위가 대사하되 옛 lease를 되살리거나 현재 다른
구매자의 재고를 해제하지 않는다. 미바인딩 사실은 UNMATCHED로 보존하고 임의 주문을
생성하지 않는다. 이 용어는 계약상 처리 상태이지 이번에 추가한 kernel enum이 아니다.

v4의 상충 Err(Capacity)는 bound 격리와 논리시간 변경이 이미 적용된 결과다.
상위 저장/처리 계층은 이를 전부 rollback/no-op으로 취급하지 않는다. 저장하지 못한
새 원문은 별도 custody 책임을 가진다. 종결 뒤 모순 사실도 과거 결과를 지우지 않고
추가 대사·의무 판단 대상으로 남긴다. 반환 필요 표식은 실제 환불 완료가 아니다.

## 4. LC-CUT — 회수 후 재생 경계

`lease_generation`, `ExecutionFence.generation`, business epoch, wire/semantics
version은 서로 바꾸어 쓸 수 없다. grant g의 신규 약정 중단 위치 C_g와 체인
회수 확정 증거 H_g를 연결하되 서로 다른 권위의 커밋 위치로 유지한다.
두 숫자를 하나의 전역 sequence처럼 비교하지 않는다. 관계 증명이 필요하다.

역사 재생은 당시의 승인 입력·정책·그때 유효했던 lease 근거로 기존 약정을 복원한다.
회수 후 옛 generation의 새로운 예약/발행 허가는 적용하지 않는다. 그러나 C_g 뒤의
늦은 실제 자금/체인 사실과 반환 의무는 버리지 않는다. 로그를 cut에서 절단해
후속 사실을 없애지 않는다. historical replay에서 외부 호출을 실행하지 않는다.
새 외부 실행은 복원 이후 현재 권위와 실제 전송 허용 조건을 다시 만족해야 한다.

source cut·이전 writer 차단·미발행 약정을 검증하지 못하면 해당 범위의 신규
소비/재위임을 보류한다. 침묵·복구 timeout·체인 미발행만으로 미사용 잔량을 만들지
않는다. chain freshness 시간원·기한, 독립 증거 가용성·비협조 cut 증명은 미정이다.
따라서 이 초안만으로 운영 회수나 오프라인 판매를 승인하지 않는다.

동일 물리 로그에 두 사실 종류를 보존할 수는 있으나 chain effects/확정 증거와
오프체인 커밋의 필드는 분리한다. 로컬 fsync가 chain finality를 대신하지 않는다.
#11의 현재 v1 로그에 이를 구현한 것으로 표시하지 않는다. v1을 v4로 조용히
재라벨링하거나 기존 golden을 덮어쓰지 않는다.

## 5. LC-TERM — 종결 근거와 해제 자격

종결은 provider contract가 최종 실패/void 또는 비실행을 보장하는 operation-scoped
인증 증거를 요구한다. 증거에는 해당 account/operation/API version, 원시 결과,
검증 주체·버전·관측 시점, 최종성의 의미와 재전송 차단의 근거가 연결돼야 한다.

네트워크 오류·한 번의 실패 시도·취소 요청 접수·단일 not-found·시간 경과는
충분하지 않다. 하나의 operation에 여러 전송 시도가 있다면 미종결 시도가 없어야 한다.
이미 보낸 요청은 내부 fencing만으로 취소되지 않는다. UNKNOWN을 다른 PG로 새 요청해
해결하지 않는다. 규칙을 만족하지 못하면 UNKNOWN과 슬롯이 남는다.

충분한 근거를 승인할 권한과 그 결론을 기록한 durable boundary가 먼저 또는
같은 권위 전이에서 성립한 뒤에만 slot release가 가능하다. 같은 종결 증거의
재전달은 재해제하지 않는다. lease 회수 그 자체가 operation의 비실행 증명은 아니다.
확정 capture가 있으면 실패 종결로 그 사실을 지울 수 없다. 모순되는 늦은 성공은
LC-FACT에 따라 보존하고 새로운 의무·검토 대상으로 처리한다.

제공자별 실제 종결 응답·멱등 보존기간·권한 주체·검증 함수는 미정이다.
범용 final이라는 문자열만 보고 해제할 수 있는 계약을 만들지 않는다.

## 6. 기록 회수와 의존 참조

메모리 결과 캐시의 축출은 권위 이력 폐기가 아니다. 캐시에 없으면 원결과를
검증할 수 있는 보존 위치를 조회한다. 조회 실패를 미실행으로 승격하지 않는다.
상세 이력을 줄이려면 지원 종료된 command 범위가 신규 실행될 수 없다는 별도
거절/압축 경계가 필요하다. 단순 tombstone 무한 증가로 문제를 옮기지 않는다.
현재 v4에는 이 회수 경로가 없으므로 시험에서도 가상 GC를 넣지 않는다.

회수 후보의 active order/operation, reserved slot, review, retained unbound fence,
반환 의무, replay window, dispute/법정 보존 참조를 확인해야 한다.
보관 성공은 해시뿐 아니라 실제 원문 접근·출처·완전성·복구 가능한 보존 위치의
근거가 필요하다. 아직 저장 backend가 없으므로 그 성공을 모의 boolean 하나로
운영 완료 처리하지 않는다. 정책 수치와 계약 당사자는 미정이다.

증거 추가/회수/binding/review 해제에 따른 색인 일관성은 이후 함께 검토한다.
이번에는 retained-conflict 선형 탐색을 변경하지 않는다.

## 7. 닫힌 원칙과 남은 입력

확정하여 공유하는 원칙은 LC-FACT/LC-CUT/LC-TERM의 안전 관계다.
첫 묶음 전체의 수명 계약을 완료 처리하려면 제공자별 종결 의미·보존/재시도 기간·
승인 권한·독립 회수 cut 증명과 원문 보존 확인 계약이 필요하며 아직 미정이다.
이 초안은 그 입력을 꾸며 넣지 않는다. (a)의 A-4 스키마/재생 구현은 이 문서의
계약 ID를 재사용하며, 같은 설계를 다시 만들어 비용을 이중 합산하지 않는다.

현재 E-4 통과는 위 미래 해제 규칙을 실행했다는 증거가 아니다. 현재 v4에서
슬롯이 남는 것을 올바르게 재현하는 것과 회수 기능 구현은 서로 다르다.
