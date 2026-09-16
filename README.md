# KIX Protocol

**현재 개발 기준: [개발계획 2.4 — KTX 실행 기반 재설계](docs/PROTOCOL_MASTERPLAN_V24.md).**
[권한·커밋·복구 ADR](docs/adr/0001-ktx-authority-commit-recovery.md)과 [runtime](runtime/README.md)을 먼저 확인하세요. S07-A `98d5f637…`의 Rust 타입·BCS·분석 의미론과 기존 보안/장애 회귀를 보존하면서 production 실행 기반을 새로 구축합니다. 기존 Python 기능도 필요한 업무 의미와 안전 보장을 Rust로 재구축하며, 아직 없던 영속 모델을 함께 구현합니다.

티켓의 발행·구매·공식 리셀·입장·환불·배분·정산을 연결하는 프로토콜 연구·개발 저장소입니다.

## 구현과 목표의 구분

현재 실제 Rust workspace는 `kix-types`, `kix-bcs1`, `kix-feature-ir`, `kix-feature-semantics`, 새 `kix-kernel`입니다. 커널은 단일 shard의 결정론적 메모리 내 전이와 회귀 테스트입니다. **복제 저장소·durable ACK·운영 결제 엔진·배포된 KTX·성능 우위는 아직 없습니다.**

목표는 edge/admission → 지역별 격리 cell → Rust KTX replicated shard → 외부 PG/체인 어댑터 → 검증된 관측입니다. PostgreSQL은 projection/control 후보이며, SQL 정본 비교는 별도 재고에서만 수행합니다. 같은 재고에 두 writer를 두지 않습니다. 배타적 위임 실행과 체인 직접 실행을 구분하고, 예약 완료·결제 사실·체인 발행 완료를 동일시하지 않습니다.

## 보존하는 자산

- S07-A: 실제 KIX-BCS1 encode/decode/SHA-256 및 고정 golden vector.
- S06.2: Rust 타입, FeatureIR 재귀/스키마 검증, Fast64 asset/version/hash 대조.
- S06/S06.1: 계산-only 가격·배정·반환안과 Python↔TypeScript CE1 회귀. production BCS와 namespace가 다릅니다.
- S03/S05: 제한된 지급 복구·별도 archive·조회 전용 복원. whole-host/remote durability와 과거 유실 원인 규명은 완료되지 않았습니다.
- Sui/Move/ZK: 기존 로컬넷과 보안 회귀. 16-slot shared Show는 production topology가 아닙니다.

기준 `2658a43`의 Groth16 설정 결함과 후속 기여·검증·조작 증명 거절 기록은 [보안 보완 문서](docs/PROTOCOL_HARDENING.md)에 보존합니다. 보안 PR #1은 main `eff0f44…`에 별도 반영됐습니다. 시험용 설정이 운영 ZK 신뢰 설정이나 키 이관을 완료했다는 뜻은 아닙니다.

## 구성

| 경로 | 역할 |
|---|---|
| `runtime/` | Rust 실행/코덱/의미론 및 v5 계약 |
| `docs/adr/` | 정본·원자성·복구 결정 |
| `reference/` | 역사적 Python/Node/SQLite·Move·ZK 회귀/장애 fixture |
| `scripts/`, `.github/workflows/`, `.devcontainer/` | 검증·CI·Codespaces 도구 |
| `validation/`, `reviews/` | 실제 실행 근거와 역사적 감사 자료 |

## 검증

```bash
python scripts/verify_runtime_architecture.py
cargo test --manifest-path runtime/Cargo.toml --workspace --locked
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
```

Rust toolchain은 `rust-toolchain.toml`의 1.98.1입니다. 전체 CI는 기존 `protocol.yml`과 새 `ktx-kernel.yml`을 구분해 검사합니다. 구 SHA의 성공을 새 SHA의 성공으로 계산하지 않습니다. R1의 메모리 내 재생은 실제 crash-recovery 증거가 아닙니다.

기존 fixture/localnet 회귀는 계속 실행합니다.

```bash
bash scripts/bootstrap.sh
source scripts/env.sh
python scripts/verify_runtime.py
python scripts/run_localnet.py
python scripts/run_localnet.py --paid
npm --prefix reference/v0.3-rc1/client run setup:zk
npm --prefix reference/v0.3-rc1/client run test:zk
python scripts/run_localnet.py --private
```

## 문서

[개발계획 2.4](docs/PROTOCOL_MASTERPLAN_V24.md) · [권한 ADR](docs/adr/0001-ktx-authority-commit-recovery.md) · [BCS](runtime/CANONICAL_BINARY_BCS_V1.md) · [Move topology](runtime/MOVE_PRODUCTION_TOPOLOGY.md) · [export](runtime/AUTHENTICATED_EXPORT.md) · [성능 계약](runtime/PERFORMANCE_PROFILE.md) · [AI/GPU](runtime/AI_GPU_DATA_PLANE.md).

이전 [개발계획 2.3](docs/PROTOCOL_MASTERPLAN_V23.md) 및 [S06.2](docs/RUNTIME_ARCHITECTURE_S062.md)는 역사적 설계/비교 기준입니다. 새 권위 모델은 ADR-0001을 따르며 하위 문서의 보안·타입·현재성 요구는 유지합니다. [저장 조사](docs/STORAGE_INVESTIGATION.md)와 [복구 제한](docs/PAID_RECOVERY.md)은 미해결 사항을 별도로 추적합니다.

개인키·비공개 노트·proving key·로컬 체인 DB는 추적하지 않습니다. 실제 PG/은행 계약, 독립 checkpoint 검증, 운영 ZK 설정, 원격 내구성 및 branch protection은 독립 완료조건입니다. 공개 배포용 라이선스는 부여하지 않았습니다.
