# S06.1 직접 검증과 계보 보완 근거

2026-09-14, 계보 보완 S06 `974d8e4875c5128266aaefa830bdfcd33cf89534` 위의 S06.1 소스를 검사했다. 최종 Git 커밋 SHA를 이 파일 안에 자기 참조로 기록하지 않는다. 해당 PR의 head SHA와 Actions 실행 SHA를 대조하고, 아래 소스·자료의 SHA-256은 `manifest.json`으로 확인한다.

## 직접 실행

| 검사 | 결과 |
|---|---|
| Python 3.12.14 / SQLite 3.53.1 / Unicode 15.0.0 | 전체 207개 통과, `python-3.12.14.log` |
| Python 3.12.3 / SQLite 3.45.1 / Unicode 15.0.0 | 전체 207개 통과, `python-3.12.3.log` |
| 각 Python 환경 ↔ Node 24.19.0 TypeScript | 두 `canonical-python-*.json` 보고서 모두 PASS |
| 공유 고정 시험값 | 인코딩 13, 잘못된 wire 36, 잘못된 ID 10, 배정 6, 자산 3, 복합 계산 5, 잘못된 계산 요청 13 |
| TypeScript 추가 런타임 경계 | 36개 통과 |
| Commerce v2 대표 계산 | 결제액 48,600원, 선택 행 반환안 16,200원. 실제 PG·체인 호출 및 장부 변이 0 |

인코딩 시험에는 숫자처럼 보이는 객체 키, 2^53 초과 금액 문자열, u128 한도, 제어문자, Unicode 정규화 버전 차이, 서로 다른 hash domain, 전체 레지스트리 문맥을 묶는 `registryHash`가 포함된다. TypeScript는 Python의 결과를 그대로 해시하는 데 그치지 않고 견적·배정·행 반환안을 독립 계산한다. `execution_contracts`의 15개 시험은 자산 혼동, 레지스트리 집합 변경, 서로 다른 정수 의미, 기존 KRW 변환과 실제 reference Core 경계를 검사한다.

재실행 명령:

```bash
python -m unittest discover -s reference/v0.3-rc1 -p 'test*.py' -v
/usr/bin/python3 -m unittest discover -s reference/v0.3-rc1 -p 'test*.py' -v
python scripts/verify_canonical.py --report .local/verification/canonical.json
python scripts/verify_commerce.py --report .local/verification/commerce.json
```

## 새 SHA의 CI

- S05 `e7259a5`: [34830524529](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34830524529) 전체 성공.
- S06 `974d8e4`: [34830584614](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34830584614) 전체 성공. 원 S06 `032d974`와 tree 및 302개 blob이 같다.
- S06.1 기능 변경: 이 자료는 PR 게시 전 직접 검증 결과다. 최종 S06.1 SHA의 CI는 PR에서 별도로 확인한다. 위 두 CI를 S06.1의 성공 근거로 승계하지 않는다.

`stack.json`은 부모·tree·변경 범위·CI를 기록한다. CI에는 기존 공개 Sui, 실제 Sui와 모의 금융의 7개 여정, ZK 조작 거절과 비공개 Sui 여정을 유지하고 새 교차 언어 검사를 추가했다. 이번 로컬 직접 실행에서는 Sui/ZK 전체를 실행하지 않았다.

## 판정 범위

계산 규격과 실행 입력 검증의 근거다. 실제 금융 제공자 인증, 영속 Order/Observation/RefundReservation, 승인 레지스트리 서비스, 다중 자산 지급, CE1의 Move·회로 적용을 구현했다는 뜻이 아니다. 기존 rc1 해시·장부·복구 경로는 수정하지 않았다. 단일 주체 ZK 시험 설정, 과거 저장 유실 원인과 원격 내구성은 미완료 상태다. S05 복원은 조회·대사 전용이다.
