# KIX 개발 환경

확인일: 2026-09-11. 이번 작업 환경에서 설치부터 공개·비공개 로컬넷 실행까지 완료했다.

## 설치

대상은 Linux x86_64(Ubuntu 24.04 계열), Python 3.12, Node 24다. 저장소 루트에서 실행한다.

```bash
bash scripts/bootstrap.sh
source scripts/env.sh
```

설치 스크립트는 저장소 안에 Python 가상환경, npm 의존성, Sui CLI와 빈 로컬 클라이언트 설정을 만든다. Sui는 공식 릴리스 아카이브의 SHA-256을 확인한 후 CLI만 추출한다. `npm ci`는 커밋한 잠금 파일을 사용한다. 기존 지갑이나 네트워크 설정을 덮어쓰지 않는다.

실제로 확인한 버전은 Sui `1.79.1-808640d9b49a`, Node `24.19.0`, npm `11.9.0`, Python `3.12.14`, Sui SDK `2.30.0`, circom2 `0.2.22`, snarkjs `0.7.5`다. [전체 버전·해시](../validation/2026-09-11/runtime-versions.json)를 보존했다. `Move.toml`의 프레임워크도 같은 Sui 커밋에 고정했다. 컨테이너 이미지와 Python/Node 패치 버전까지 비트 단위로 고정한 구성은 아니다.

Sui 아카이브 다운로드는 약 1.1 GB다. 최초 설치에는 GitHub 릴리스, npm, PyPI 및 Sui 프레임워크 저장소에 접근할 수 있어야 한다. Rust와 네이티브 Circom 설치는 필요하지 않다. 회로는 npm의 WASM 컴파일러로 빌드한다.

## Codespaces

GitHub 저장소에서 **Code → Codespaces → Create codespace on main**을 선택하면 `.devcontainer/devcontainer.json`이 적용된다. Python 3.12와 Node 24 구성 후 `scripts/bootstrap.sh`가 실행된다. 이번에 별도 Codespace를 생성하거나 해당 인스턴스에서 다시 실행한 것은 아니다.

채팅 작업 환경과 Codespace가 같은 실행 세션으로 자동 연결되는 것은 아니다. GitHub에 커밋한 소스와 설정으로 개발 상태를 이어간다. 지금 채팅 작업 환경에도 실행 도구 설치가 완료돼 있다.

## 기본 검증

```bash
source scripts/env.sh
python scripts/verify_runtime.py
```

Python 88개, Node 오프라인 4개, SDK import, Move 검사 3개, 회로 2개 컴파일을 실행한다. 로그는 `.local/verification/`에 쓴다. 이 명령 자체는 체인 거래나 증명 생성을 수행하지 않으며, 결과 JSON도 이를 구분한다.

Move 명령의 `--build-env mainnet`은 고정한 프레임워크의 주소 해석을 위한 빌드 환경 이름이다. 로컬 여정의 실제 거래 대상은 `127.0.0.1`뿐이다. 메인넷·테스트넷 거래나 실제 돈을 사용하는 명령은 포함하지 않았다.

## 공개 권리 여정

```bash
python scripts/run_localnet.py
```

새 디렉터리에 genesis와 검증자 1개짜리 체인을 만들고 실행한 뒤 종료한다. 9000/9123 포트를 이미 쓰고 있으면 다른 프로세스를 종료하지 않고 실패한다. 생성된 계정과 체인 자료는 `.local/localnet/`에만 남는다.

발행·이전 후 설정 프로세스가 종료되고, 새 프로세스가 보유자 백업을 복구해 별도 검표자 키로 권리를 사용한다. 이전 소유자와 중복 사용의 거절은 SDK의 사전 시뮬레이션 오류가 아니라 **실제 실패 거래 영수증·Move 모듈·abort code**로 확인한다.

## 비공개 권리 여정

```bash
npm --prefix reference/v0.3-rc1/client run setup:zk
npm --prefix reference/v0.3-rc1/client run test:zk
python scripts/run_localnet.py --private
```

`setup:zk`는 컴파일, 단일 주체 시험용 Powers of Tau, mint/spend 각각의 Groth16 기여와 `zkey verify`를 수행한다. 시작할 때 기존 manifest를 무효화하고 모든 단계가 성공해야 새 manifest를 쓴다. 초기 키 또는 기여 기록이 없는 기존 manifest는 클라이언트가 거절한다. 이 검사는 운영용 신뢰 설정이나 다자 참여를 보장하지 않는다.

`test:zk`는 과거 공개 자료의 결함을 먼저 재현한 뒤 새 키에서 정상 증명 수락과 공개 입력·증명 동시 조작 거절을 검사한다. `--private`는 별도 시험 공연에서 실제 체인 조작 거절, 폐기 후 옛 증명 거절, 변경된 루트에 대한 유효 노트의 증명 재생성과 사용, 취소 후 거절을 추가로 검사한다. 폐기된 비공개 슬롯의 재발행은 여전히 금지한다.

개인키·백업 비밀번호·비공개 노트는 `.local/` 및 무시되는 실행 디렉터리에 있으므로 공유하지 않는다. `zk/artifacts/`의 시험용 파라미터도 Git에서 제외했다. 업로드한 검증 자료에는 공개 증명·공개 검증키·선별한 거래 결과만 들어 있다.

## 로컬넷의 불필요한 외부 키 조회 중지

기본 Sui 검증자는 zkLogin OAuth 공급자의 공개 JWK를 주기적으로 가져온다. 최초 실행에서 Slack 공급자에 대한 이 백그라운드 조회가 자동 승인 검토에 의해 거절됐다. 공식 Sui 소스의 `NodeConfig.zklogin_oauth_providers`와 `start_jwk_updater`에서 원인을 확인했다.

이 여정은 Ed25519 서명과 자체 Groth16 회로를 사용하고 zkLogin을 사용하지 않는다. 따라서 **새로 생성한 로컬 genesis의 검증자 설정**에서 `zklogin-oauth-providers`를 빈 맵으로 지정한 뒤 체인을 시작한다. `scripts/run_localnet.py`는 이를 파일에서 다시 검사한다. 외부 연결 허용 규칙이나 승인 정책은 변경하지 않았다. 이 설정의 사용 범위는 해당 로컬 시험이다.

근거: [고정 버전 NodeConfig](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/crates/sui-config/src/node.rs), [노드의 JWK updater](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/crates/sui-node/src/lib.rs).

## GitHub Actions

`protocol.yml`은 main push·PR·수동 실행에서 설치·기본 검사·공개 여정·시험용 키 생성·ZK 회귀 검사·비공개 여정을 모두 수행한다. 비공개 검사를 기본적으로 건너뛰던 `run_private` 옵션은 제거했다. 설정 파일을 추가한 것과 GitHub runner에서 통과한 것은 별개다. 각 실행 상태는 저장소 Actions에서 확인한다.

공식 안내: [Sui 설치](https://docs.sui.io/getting-started/onboarding/sui-install), [로컬 네트워크](https://docs.sui.io/getting-started/onboarding/local-network).
