# KIX Protocol

티켓의 발행·구매·공식 리셀·입장·환불·배분·정산을 연결하는 프로토콜 연구·개발 저장소다.

현재 개발 기준은 **v0.3-rc1 + 실행 환경 보완(2026-09-11)**이다. Sui와 npm 의존성을 설치했고, Move 및 회로 컴파일에 이어 공개·비공개 권리 사용을 실제 Sui 로컬넷에서 실행했다.

## 구성

| 경로 | 내용 |
|---|---|
| `reference/v0.3-rc1/` | 현재 참조 구현, Sui Move, 독립 클라이언트, ZK 회로 |
| `reference/v0.1/`, `reference/v0.2/` | 이전 기준 모형 보존 |
| `reviews/` | v0.1·v0.2 검토와 재현 자료 |
| `scripts/`, `.devcontainer/`, `.github/workflows/` | 설치·검증 자동화, Codespaces 구성, CI |
| `validation/2026-09-11/` | 실제 실행 로그, 체인 영수증, 공개 증명·검증키 |
| `docs/` | 실행 방법, 검증 범위, 변경 근거, 후속 개발 계획 |

## 실행

Linux x86_64, Python 3.12, Node 24 환경에서 저장소 루트 기준:

```bash
bash scripts/bootstrap.sh
source scripts/env.sh
python scripts/verify_runtime.py
python scripts/run_localnet.py
```

실제 Groth16 생성·검증을 포함하는 비공개 경로:

```bash
npm --prefix reference/v0.3-rc1/client run setup:zk
python scripts/run_localnet.py --private
```

GitHub에서 **Code → Codespaces → Create codespace on main**으로 같은 설치 구성을 사용할 수 있다. 설정 파일은 추가했으나 별도 Codespace 인스턴스를 생성한 것은 아니다. 상세 조건은 [개발 환경 안내](docs/DEVELOPMENT.md)를 따른다.

## 확인된 범위

| 확인 항목 | 이번 실제 결과 |
|---|---|
| Python 합성 검사 / Node 오프라인 검사 | 88개 / 4개 통과 |
| Sui Move / ZK 회로 | Move 검사 3개 통과, 회로 2개 컴파일 |
| 공개 경로 | 발행·이전 후 별도 프로세스 복구·소비, 이전 소유자·중복 사용 거절 |
| 비공개 경로 | 노트 생성·소비 증명 생성, Sui의 Groth16 검증 수락 |
| 비공개 오류 경로 | 다른 검표 문맥·다른 검증키 객체·중복 소비가 실제 체인에서 거절됨 |

이 로컬넷은 검증자 1개이며 RPC를 신뢰한다. 확인한 독립성은 설정 프로세스 종료 뒤 다른 프로세스가 백업과 체인 자료로 진행하는 범위다. 실제 PG·은행 연결, 다중 노드 장애 내성, 상용 KIX 서비스 전체 중단, 실서비스 익명성은 검증하지 않았다. ZK 설정은 단일 주체가 만든 시험용이며 비공개 모형은 16슬롯이다.

기존 선택 변이 14개 결과는 rc1 원자료를 보존했으며 이번 실행에서 재검사하지 않았다. 이전 `results/verification.json`은 각 버전 작성 당시 기록이다. 이번 실행 근거는 [실행 검증 보고](docs/RUNTIME_VALIDATION.md)와 `validation/2026-09-11/`이다.

## 문서

- [개발 환경과 재실행](docs/DEVELOPMENT.md)
- [실행 결과와 보장 범위](docs/RUNTIME_VALIDATION.md)
- [v0.3-rc1 원래 구현 보고](reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md)
- [가져온 자료의 원본 해시](docs/source-imports-2026-09-11.json)
- [rc1 이후 소스 수정](docs/runtime-changes-from-rc1.patch)
- [후속 개발 계획](docs/ROADMAP.md)

개인키·백업 비밀번호·비공개 노트·시험용 proving key·로컬 체인 DB는 추적하지 않는다. 공개 배포용 라이선스는 부여하지 않았다.
