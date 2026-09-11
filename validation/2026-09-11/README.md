# 실행 근거 읽는 순서

1. `runtime-versions.json`: 설치된 실제 버전과 Sui 아카이브·바이너리 SHA-256.
2. `build-verification.json` 및 5개 로그: Python, Node, SDK, Move, 회로 컴파일. 이 명령은 체인 거래와 증명 생성을 수행하지 않는다.
3. `public-journey.json`, `private-journey.json`: 각 별도 로컬 체인의 실행 결과와 보장 범위.
4. `public-transactions.json`, `private-transactions.json`: 실제 거래의 digest·상태·effects·events. 개인키, 비밀번호, 서명, 요청 바이트는 제외했다.
5. `mint-verification-key.json`, `spend-verification-key.json`, `private-public-inputs-and-proof.json`: 시험용 공개 검증키·공개 입력·증명. 비공개 witness는 포함하지 않는다.

`fixture-zk-artifact-manifest.json`은 시험용 파라미터 생성 시점의 기록이다. 그 안의 `suiSerializationVerified: false`는 생성 단계가 체인 검증을 수행하지 않았다는 뜻이다. 이후 실제 수락 여부는 `private-journey.json`에서 확인한다.

`imported-rc1-manifest.json`은 수정 전 rc1의 해시 목록이다. 현재 소스와 직접 비교하는 목록은 `reference/v0.3-rc1/results/manifest.sha256.json`이다. 이 디렉터리 자체의 해시는 `manifest.sha256`으로 확인한다.

로컬 체인 기록이므로 공개 익스플로러 링크는 없다. 같은 명령을 다시 실행하면 새 체인·키·거래 digest가 생성되며 바이트 일치를 요구하지 않는다. 성공·거절 조건과 실제 체인 실행 여부를 확인한다.

시험용 단일 주체 설정, 검증자 1개, RPC 신뢰, 16슬롯의 한계는 [실행 검증 보고](../../docs/RUNTIME_VALIDATION.md)에 있다.
