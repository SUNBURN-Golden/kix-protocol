# ZK 설정·권리 현재성 보완 근거

기준 커밋은 `2658a43aefa792ff783457188814f8598a62f5b0`이다. 수정·검증 범위는 [프로토콜 보완 보고](../../docs/PROTOCOL_HARDENING.md)를 따른다.

- `build-verification.json`과 검사 로그: Python 88개, Node 4개, Move 3개, 회로 2개 및 SDK import.
- `zk-regression.json`: 기존 공개 자료의 취약성 재현 5개 결과와 새 키의 정상 2개·조작 거절 20개 결과.
- `mint/spend-key-verification.log`: 회로와 Powers of Tau에 대한 기여 키 검증 결과.
- `fixture-zk-artifact-manifest.json`, `mint/spend-verification-key.json`: 이번 실행의 공개 해시와 검증키. proving key·비밀 입력은 포함하지 않는다.
- `public-journey.json`, `private-journey.json`: 실제 로컬넷 정상·실패 여정의 선별 결과.
- `private-boundary-transactions.json`: 추가 경계 검사의 실제 실행 상태 16건(실패 6건 포함). 서명과 원 제출 바이트는 제외했다.
- `source-sha256.json`: 이번에 바꾼 실행 코드와 CI 설정의 파일 해시.

`build-verification.json`은 빌드만 기록하므로 `chainExecuted`와 `proofGenerated`가 false다. 체인 실행은 journey 파일, 증명 생성·검증은 ZK regression에서 확인한다. manifest의 `suiSerializationVerified: false`는 설정 시점 값이며 이후 체인 수락을 덮어쓰지 않는다.

단일 주체 시험 설정·단일 검증자 로컬넷이다. 운영 보안 감사·실제 PG/은행 연동·비공개 재발행 완료를 뜻하지 않는다. 이 자료의 로컬 체인 digest는 공개 익스플로러에서 조회할 수 없다.
