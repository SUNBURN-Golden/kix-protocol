# KIX v0.3-rc1

> **실행 보완(2026-09-11):** 이후 Sui·SDK 설치, Move 검사, 공개·비공개 로컬넷 여정과 Groth16 수락까지 실행했다. 아래는 원래 rc1 작성 당시의 상태 기록이다. 현재 기준은 [실행 검증 보고](../../../docs/RUNTIME_VALIDATION.md)와 [개발 환경 안내](../../../docs/DEVELOPMENT.md)를 따른다. `results/verification.json`은 원래 작성 시점 기록으로 보존했다.

**상태: Python 기준 모형의 수정은 검증됨. Sui·ZK 구현 소스는 포함했으나 빌드·실행은 미검증.**

이 패키지는 v0.2 독립 검토의 R01–R09에 대응한다. 원래 v0.2 파일 42개는 변경하지 않았다.
`results/verification.json`의 체인 실행/증명 생성 항목은 모두 `false`다. 정상 동작을 가정해 작성한 Move·SDK 소스를 실행 성공으로 취급하면 안 된다.

## 구성

| 경로 | 역할 | 확인 수준 |
|---|---|---|
| `core.py`, `finance.py`, `lifecycle.py`, `observations.py`, `dispatch.py` | 합성 입력으로 권리·돈·실행 의무 처리 | Python 검사 88개 통과 |
| `test_core.py`, `test_v02.py`, `test_v03.py` | 기존 72개 + 이번 반례 회귀 16개 | 실행함 |
| `mutation_check.py` | 기존 선택 방어 변이 14개 | 모두 탐지 |
| `sui/sources/rights.move` | 발행·양도·리셀·검표·폐기·비공개 전환 | 컴파일 전 소스 |
| `sui/sources/zk_gate.move` | 공연에 고정한 불변 검증키 객체 | 컴파일 전 소스 |
| `sui/tests/rights_tests.move` | 보유자·수신자·검표 권한 전이 검사 | 실행하지 못함 |
| `client/independent.mjs`, `localnet.mjs` | 직접 서명·제출·암호화 백업·독립 프로세스 복구 | JavaScript 구문 검사만 수행 |
| `client/backup.mjs`, `encoding.mjs` | 백업 암복호화·직렬화 | 오프라인 검사 4개 통과; Sui 직렬화 호환성은 미검증 |
| `zk/circuits/` | 노트 생성, 발행 포함·현재 세대·중복 소비·검표 문맥 검증 회로 | 컴파일·증명 생성 전 |
| `DESIGN_SUI_ZK.md` | 검증 명제·권한·공개 범위·제한 | 설계 문서 |
| `results/review_trace_v03.json` | 이번 반례의 수정 후 실제 합성 실행 결과 | 재실행 가능 |

## 지금 재실행 가능한 검사

```bash
python3 verify.py
python3 review_trace_v03.py
python3 check_reproducibility.py
node --test client/offline.test.mjs
python3 scripts/preflight.py
```

마지막 명령은 Sui/SDK/증명 도구가 없으면 `BLOCKED_MISSING_RUNTIME`과 종료 코드 3을 반환한다. 이것은 체인 시험 통과가 아니다. `verify.py`의 종료 코드 0은 Python 기준 모형 검사만 뜻한다.

Python 의존성은 `requirements.txt`를 따른다. 현재 검증 환경은 Python 3.12.14, SQLite 3.53.1, cryptography 46.0.0이다.

## 실제 체인 실행을 재개하는 순서

아래 단계는 작성 환경에서 실행하지 못했다. 공식 설치 파일 요청이 승인 단계에서 취소되었고 `sui`, `cargo`, `rustc`, SDK·SNARK 패키지가 없었다. 실제 SDK 응답 형식, Move 타입·빌림 검사, Poseidon/Arkworks 직렬화 호환성을 이 단계에서 확인하고 수정해야 한다.

1. 공식 Sui CLI와 Node 패키지를 설치할 수 있는 개발 환경에서 `client/`의 `npm install`을 실행한다. 생성된 `package-lock.json`, 실제 SDK 버전, Sui CLI 버전, `Move.lock`을 보존한다. 현재 SDK 범위 지정은 설치 전 후보이며 재현 가능한 잠금으로 확정되지 않았다.
2. 새 디렉터리에서 공식 로컬넷을 시작한다. 기존 체인 자료를 재생성 대상으로 삼지 않는다.
3. 패키지 루트에서 `sui move test --path sui`를 실행한다.
4. `client/`에서 `node localnet.mjs`를 실행한다. 이 스크립트는 localhost만 허용한다. 실제 바이트코드 빌드·로컬 게시·발행·A→B 양도 후 설정 프로세스를 종료한다. 새 프로세스가 B의 암호화 백업을 복구하고 다른 검표자의 키로 사용 처리한다. 체인에서 A의 권한과 재사용을 거절한 영수증이 있어야 성공 파일을 쓴다.
5. `client/`에서 `node setup-zk.mjs`를 실행해 **단일 주체 시험용** 파라미터를 만든다. 운영용 신뢰 설정 절차가 아니다.
6. 서로 다른 새 결과 디렉터리에서 `KIX_PRIVATE=1 KIX_JOURNEY_DIR=../results/private-localnet node localnet.mjs`를 실행한다. B에게 이전한 같은 Ticket을 `SHIELDED`로 잠근 뒤 노트를 만든다. 새 프로세스는 백업과 공개 체인 자료에서 증명을 만들고, 다른 검표자의 거래로 소비한다. 틀린 문맥·다른 검증키 객체·재사용도 실제 체인에서 거절되어야 한다.

`localnet.mjs`의 설정 프로세스는 실제 KIX 운영 서비스가 아니다. 이 실험은 별도 프로세스와 키로 개발용 조정 프로세스 의존을 없애는 시험이다. 아직 구현되지 않은 로그인·salt·대납 서비스를 켰다가 끈 실험이라고 주장하지 않는다. 코드 자체는 이 서비스들을 호출하지 않는다.

## 의도적인 제한

- 실제 PG, 은행, 생산용 어댑터 및 금융 계약은 연결하지 않았다. Python의 actor/source는 합성 문자열이다.
- Python 기준 모형과 Sui 원장을 자동으로 동기화하는 브리지는 아직 없다. 공개 리셀 Move 코드는 결제 증거 발급자의 서명된 체인 거래를 신뢰하는 인터페이스이며, 실제 PG 승인·정산을 검증한 결과가 아니다.
- Sui 후보 모형은 최대 16개 재고와 16개 비공개 노트다. 공개 권리의 주소·ID·이전·금액은 보인다.
- 비공개 전환은 되돌리지 않는다. 전환 후 허용 동작은 비공개 검표와 발행 권한자의 폐기/공연 취소다. 비공개 리셀·환불·재고 재개·키 교체는 지원하지 않는다. 공개 경로와 비공개 경로의 이중 사용은 `SHIELDED` 상태로 차단한다.
- 백업은 키와 노트를 복구한다. 백업까지 모두 잃은 사용자의 권리 복구는 구현하지 않았다.
- 클라이언트는 선택한 Sui RPC를 신뢰한다. 검증자 서명/체크포인트를 직접 검증하는 라이트 클라이언트는 아니다. 공유 상태의 최종 전이 조건은 Move가 확인하도록 작성했다.
- SQLite 도메인은 `kix:fixture:lifecycle:0.3`으로 바뀌었다. v0.2 DB를 제자리에서 업그레이드하지 않는다. 재고 식별자는 발권사·행사·회차·좌석의 NFC 정규화된 튜플 해시다.
- 공식 외부 티켓 전환, 다수 수취인 배분 정책, 운영용 개인키 회복 및 회로 보안 검토, 특허성 평가는 남아 있다.
