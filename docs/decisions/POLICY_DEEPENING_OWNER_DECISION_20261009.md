# 정산·예매/리셀/검표·F04 정책 심화 — 소유자 결정 위치 기록 (2026-10-09)

노드 `audit4-audit4-policy-deepening-owner-decision-r`. 이슈 없음. 문서일: 2026-10-09.

상태: 위치 기록. 결정을 새로 만들지 않는다. 검토됨으로 표시하지 않는다.

이 파일은 이미 병합된 글이 인용하는 2026-10-09 소유자 결정을 [AGENTS.md](../../AGENTS.md) §5가 적는 `docs/decisions/` 아래에 가리킨다. 결정 문장을 새로 만들지 않는다.

행 번호는 이 기록을 쓸 때 `git fetch origin main` 뒤의 `origin/main`이자 HEAD인 `4e2122a3f61a0feea2c43035c1ae834e7097e429`에서 `grep -nF`로 읽었다. 작업 브랜치 HEAD는 그 SHA와 같았다.

## 1. 결정과 인용

결정자는 JunTae다. 날짜는 2026-10-09다. 시각 「12:34 KST」는 [정산 계약](../contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md) 24행에만 있다. [예매·리셀·검표 계약](../contracts/BOOKING_RESALE_ADMISSION_GATES.md)과 [F04 계약](../contracts/CREDIT_ADVANCE_F04.md)의 인용에는 시각이 없다. 이 기록은 세 파일의 문장을 하나의 행위로 묶지 않는다.

[TL-3 기록](TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md) 17행도 「2026-10-09 12:34 KST」를 적는다. 그 문장은 O1이다. 이 기록은 그 결정을 인용하지 않는다.

소유자 결정의 원문 본문은 이 저장소에 없다. 아래는 병합된 계약이 그 결정을 인용하는 문장이다. 이 줄은 인용문이 아니다. `rg -n -F '12:34 KST'`는 정산 계약 24행과 TL-3 기록 17행만 돌려주었다. `rg -n -F 'L0, W0, R0'`에서 정산 계약 밖은 `reference/settlement_f01_f03/test_adopted_policy.py:3` 한 줄이었다. `rg -n -F '선택지 A를 목 경계'`에서 두 계약 밖은 `reference/credit_advance_f04/test_open_terms.py:72`와 `reference/booking_resale_admission/test_open_items.py:80`이었다. 그 참조 줄은 계약 문장을 가리키거나 같은 날짜를 되풀이한다. 결정 원문이 아니다. 이 기록은 그 참조 파일을 고치지 않는다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:24`

> 소유자 JunTae가 2026-10-09 12:34 KST에 0.2의 권고 L0, W0, R0, S0, T0, B0, P0를 이 목의 자세로 채택했다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:33`

> 이 채택은 Astra의 아키텍처 서명이 아니다. 새 프로토콜 명령을 만들지 않는다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:282`

> 채택된 행은 L0, W0, R0, S0, T0, B0, P0이다. 다른 행은 채택하지 않는다.

출처: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:24`

> 2026-10-09 소유자 결정(JunTae)이 선택지 A를 목 경계로 채택했다. 정책 숫자는 채우지 않고 `UNDETERMINED`로 둔다. 담당은 §7.1에 있다.

출처: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:264`

> 2026-10-09 소유자 결정(JunTae)이 권고된 선택지 A를 목 경계로 채택했다.

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:165`

> 아래 다섯 항목의 목 경계는 §5.1이다. 2026-10-09 소유자 결정(JunTae)이 선택지 A를 목 경계로 채택했다. 정책 숫자는 비어 있다.

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:187`

> 2026-10-09 소유자 결정(JunTae)이 선택지 A를 목 경계로 채택했다.

개정 ID는 각 파일이 스스로 적는다. 정산은 `SET-POLICY-DRAFT-0.3`(`docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:23`). 예매·리셀·검표는 `BRA-OPEN-ITEMS-DRAFT-0.2`(`docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:23`). F04는 `F04-MOCK-TERMS-DRAFT-0.2`(`docs/contracts/CREDIT_ADVANCE_F04.md:184`).

## 2. 병합 PR

커밋 작성자는 `git show -s --format='%H %P %an'`로 읽었다. `mergedBy.login`과 `mergedAt`은 `gh pr view <n> --repo SUNBURN-Golden/kix-protocol --json title,headRefName,mergedBy,mergeCommit,mergedAt`로 읽었다. 둘은 다른 칸이다. `mergeCommit.oid`는 아래 병합 커밋과 같았다.

| PR | 노드 | 계약 개정 | 병합 커밋 | 부모 | 커밋 작성자 | merged_by | mergedAt |
|---|---|---|---|---|---|---|---|
| #156 | `settlement-policy-deepening` | `SET-POLICY-DRAFT-0.3` | `02b1bf202b926c3b99cb39b360a50b2a75d3f744` | `31eac0637a324244aeca00e849fdb0f7c685232e` `e26f1bac5f5170fbfd8b51aad71ba49d0665e609` | `soulbound_jt` | `BeautifulMind-JT` | `2026-10-09T12:48:09Z` |
| #157 | `booking-resale-admission-deepening` | `BRA-OPEN-ITEMS-DRAFT-0.2` | `28f263b5839921b729c2729c8ff5041f57d306ec` | `17c8a7dc66e49b090067b94ff7bc68cb6d79c5ee` `0dee7319c2598083d9e6c02e917940f8648b1a40` | `soulbound_jt` | `BeautifulMind-JT` | `2026-10-09T05:42:40Z` |
| #158 | `f04-mock-deepening` | `F04-MOCK-TERMS-DRAFT-0.2` | `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1` | `28f263b5839921b729c2729c8ff5041f57d306ec` `293cc81198d45faf8111637af6fe4d28fa3470cb` | `soulbound_jt` | `BeautifulMind-JT` | `2026-10-09T06:20:00Z` |

`gh`가 돌려준 `headRefName`은 #156 `agent/kix-settlement-policy-deepening`, #157 `agent/kix-booking-resale-admission-deepening`, #158 `agent/kix-f04-mock-deepening`이다. #157의 제목은 `Booking/resale/admission contract §7: decide the open items as a draft revision`이다. 그 읽기로 #157을 예매·리셀·검표 PR로 적는다.

같은 문장이 그 병합 트리에 이미 있었다. `git show <merge>:<contract>` 뒤 `grep -nF`로 읽은 행은 위 인용과 같다. #156 트리의 정산 문장은 24행, 33행, 282행이다. #157 트리의 예매·리셀·검표 문장은 24행, 264행이다. #158 트리의 F04 문장은 165행, 187행이다. 이 HEAD에서도 그 행이다.

## 3. 채택된 행

이 절의 블록인용은 계약 원문이다. 표의 ID 목록과 「채택 칸」 설명은 인용문이 아니다. 그 칸은 해당 행을 읽어 확인했다.

### 3.1 정산 — L0, W0, R0, S0, T0, B0, P0

절은 §7.1–§7.7이다. 각 행의 채택 문장은 다음이다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:320`

> | L0 | 역할 라벨을 법률 당사자에 묶지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:336`

> | W0 | 호출자 순서를 픽스처로만 둔다. 상품 waterfall을 만들지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:354`

> | R0 | 방법을 비운 채로 둔다. §2의 바닥 나눗셈을 일반 정책으로 올리지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:372`

> | S0 | 리셀 분할을 이 F01 정책 밖에 둔다. | 지금 효력. 0.3이 이 행을 채택한다. |

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:389`

> | T0 | `tax`와 `held`를 현금이 아닌 명세서 사실로만 둔다. 해제·적립·납부를 목에 만들지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:406`

> | B0 | `UNDEFINED`를 유지한다. 추가 배정을 멈추고 액면을 그대로 둔다. 자동 상계를 만들지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:425`

> | P0 | P04 종결을 성공으로 정의하지 않는다. 목 종결을 P04로 읽지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |

다른 행을 채택하지 않는다는 문장은 §1의 282행과 아래다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:342`

> 채택은 W0이다. W1–W4는 채택하지 않는다. W2와 W4는 원가·구간·상한·지급 시점이 문서로 정해진 뒤에만 다시 연다. 그 값은 이 문서에 없고 `UNDETERMINED`다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:360`

> 채택은 R0이다. 방법과 수취인 지명은 `UNDETERMINED`로 남는다. R1과 R3는 채택하지 않는다. 이 절은 알고리즘을 구현하지 않는다. §0.3이 픽스처와 코드를 바꾸지 말라고 한 문장은 그대로다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:377`

> 채택은 S0이다. S1–S3는 채택하지 않는다. S3를 이 목의 규칙으로 추가하지 않는다. 리셀 bps는 `UNDETERMINED`이고 담당은 사용자다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:394`

> 채택은 T0이다. T1–T3는 채택하지 않는다. 세율과 준비율은 `UNDETERMINED`다. 담당은 사용자, 그 다음 세무·회계다. 회계 담당이 분류를 답하기 전에 해제 스위치를 열지 않는다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:413`

> 채택은 B0이다. 법률상 환불채무자는 `UNDETERMINED`다. B1–B4는 채택하지 않는다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:430`

> 채택은 P0이다. P1–P3는 채택하지 않는다. 새 종결 명령을 만들지 않는다. `durable`은 거짓으로 남는다. §9가 새 프로토콜 명령은 `DECISION_REQUIRED · Astra`라고 한 문장은 그대로다.

360행이 이름 짓는 비채택은 R1과 R3다. R2·R4의 요약 문장은 그 줄에 없다.

### 3.2 예매·리셀·검표 — 선택지 A

§7.1의 아홉 ID는 284–292행이다. 채택 칸은 아홉 행 모두 A다.

- `actor-authentication-revocation` (284)
- `durable-show-config` (285)
- `approved-reservation-ttl` (286)
- `discounts-and-coupons` (287)
- `payment-attesters-authority` (288)
- `compensation-after-payment-fact` (289)
- `resale-failure-compensation-seller-payout` (290)
- `refund-revoke-shield-gift-cancel-show` (291)
- `consume-private-delegated-sessions` (292)

출처: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:265`

> 선택지 B와 C는 기록만 있고 채택하지 않는다.

출처: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:296`

> 각 항목의 채택은 A다. B와 C는 기록만 있고 채택하지 않는다.

### 3.3 F04 — 선택지 A

다섯 ID는 209–213행이다. 채택 칸은 다섯 행 모두 A다.

- `legal-parties` (209)
- `interest-apr-schedule` (210)
- `seniority` (211)
- `perfection` (212)
- `limit-recalculation` (213)

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:188`

> 선택지 B, C, D는 기록만 있고 채택하지 않는다.

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:223`

> 각 항목의 채택은 A다. 나머지 선택지는 기록만 있고 채택하지 않는다.

## 4. Astra 상태

아래는 [프로그램 로드맵](PROGRAM_ROADMAP_20260930.md) 42행의 연속된 부분 문자열이다. 그 행 전체가 아니다.

출처: `docs/decisions/PROGRAM_ROADMAP_20260930.md:42`

> 정책 값은 Astra 결정 경로로 정하고, 법률 의존 값은 `UNDETERMINED`로 둔다

이 저장소에서 #156, #157, #158의 Astra 판정 기록이나 그 PR에 대한 ARCHITECTURE 게이트 기록을 찾지 못했다. 이 문장은 기록의 부재다. 검토가 없었다는 말이 아니다.

돌린 검색은 다음이다.

- `rg -n -i -e 'Astra.*(승인|ruling|판정)' docs/decisions docs/status`는 50행이었다. 그 출력에서 `#156`, `#157`, `#158`, `settlement-policy-deepening`, `booking-resale-admission-deepening`, `f04-mock-deepening`을 거르면 행이 없었다.
- `rg -n -e '#156|#157|#158' docs`가 찾은 행은 [TL-3 기록](TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md) 5행과 [F04 실자금 해제 조건](F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md) 22행, 37행이다. 그 행은 병합 커밋을 가리킨다. Astra 판정 문장이 아니다.
- `#156|#157|#158`과 `Astra`, `ARCHITECTURE`, `판정`, `ruling`이 같은 줄에 있는 기록은 `reference/`와 `runtime/`을 빼고 찾지 못했다.
- `rg -n -F '아키텍처 서명'`은 정산 계약 33행만 돌려주었다. 그 문장이 이 채택이 Astra의 아키텍처 서명이 아니라고 적는 계약 문장이다. 예매·리셀·검표 계약과 F04 계약에는 같은 문장이 없다.

이 줄은 인용문이 아니다. [프로그램 로드맵](PROGRAM_ROADMAP_20260930.md) 67–69행은 세 노드의 계획 표에 Astra 게이트 칸으로 `ARCHITECTURE`를 적는다. 그 행은 PR 번호를 적지 않는다. 그 칸을 이 세 PR의 판정 기록으로 읽지 않는다. [판정 표](../aiops/PROGRAM_ASTRA_DELEGATION.md) 25–27행은 세 노드에 계약 변경 YES, 병합 대표님, A3를 적는다. 그 파일은 머리에서 `NON_EXECUTABLE_DRAFT`라고 적는다. 그 행은 이 세 PR의 Astra 판정 문장이 아니다.

## 5. 미정·이 기록이 열지 않는 것

숫자는 계약이 적은 대로 `UNDETERMINED`다. `DECISION_REQUIRED · Astra`인 제품 정책 숫자는 그 계약의 문장 그대로다. 이 기록은 숫자를 채우지 않는다.

출처: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:30`

> 세율, 준비율, 리셀 bps, waterfall의 상한·원가·구간·지급 시점, 잔여 단위의 수취인 지명은 권고가 비운 그대로 `UNDETERMINED`다.

> 법률상 채무자·채권자, 세금의 성격, 예수·준비금의 회계 분류도 `UNDETERMINED`다. 담당 경로는 I10이다.

> P04를 저장 엔진이나 실 PG·은행 관찰로 구현하는 일은 프로그램 결정 §5의 잠금 안에 있어 미룬다. 실자금, Sui mainnet, 운영 런타임, 비밀은 범위 밖이다.

출처: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:269`

> 정책 숫자와 법률·세무·회계·제공자 답변은 `UNDETERMINED`이고 담당을 이름 붙인다.

> 새 프로토콜 명령, 재시도, 인증 의미, 권한은 넣지 않는다.

> 실자금, 실 PG·은행·KYC, 공개 엔드포인트, Sui testnet·mainnet, 저장 엔진은 [PROGRAM_DECISIONS_20260928.md](../decisions/PROGRAM_DECISIONS_20260928.md) §5 잠금 그대로다.

> 하드웨어, 유료 서비스, 비밀, 운영 런타임도 이 개정 밖에 둔다.

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:190`

> 정책 숫자는 `UNDETERMINED`이고 담당을 이름 붙인다.

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:197`

> 결정 규칙은 법률 당사자와 담보 완전성을 숫자로 정하지 않는다. 그 둘은 `UNDETERMINED`다.

출처: `docs/contracts/CREDIT_ADVANCE_F04.md:198`

> 이자·순위·한도의 숫자도 이 개정에 없다. 담당은 Astra다.

잠금 포인터는 [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5다. 이 기록은 그 잠금을 열지 않는다.

## 6. 비주장

1. 이 기록은 새 결정을 더하지 않는다.
2. 작성자는 빌더다. 비작성자 검토가 아니다.
3. 이 글을 쓸 때 이 파일을 담은 exact-head CI는 없다.
4. 행 번호는 §1이 적은 HEAD의 자리다.
5. 소유자 결정의 원문 본문은 이 저장소에 없다. 저장소 안의 해당 문자열은 §1이 적은 계약 인용과 참조 모듈의 되풀이뿐이다.
6. 이 기록은 전체 검증이 아니다. F01–F04, B, R, P03 라벨을 올리지 않는다.
