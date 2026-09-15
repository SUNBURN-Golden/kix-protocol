# KIX Protocol

**최신 개발 기준:** S06.1 `d5cf004` 위의 **S06.2 greenfield production architecture reset**. [개발계획 2.3](docs/PROTOCOL_MASTERPLAN_V23.md), [S06.2 실행 구조](docs/RUNTIME_ARCHITECTURE_S062.md), [KIX-BCS1](runtime/CANONICAL_BINARY_BCS_V1.md), [production Sui topology](runtime/MOVE_PRODUCTION_TOPOLOGY.md), [AI/GPU data plane](runtime/AI_GPU_DATA_PLANE.md)을 먼저 확인하세요. 기존 Python/Node/SQLite rc1과 CE1/shared-Show는 역사적 regression/fault fixture이며 새 production 설계권한이 아닙니다. S07 production은 `runtime/`의 Rust modular monolith + Tokio + PostgreSQL 18에서 시작합니다.

티켓의 발행·구매·공식 리셀·입장·환불·배분·정산을 연결하는 프로토콜 연구·개발 저장소다.

현재 개발 기준은 **v0.3-rc1 역사적 fixture + S05 조회 전용 복원 + S06 계산·보류 기록 + S06.1 결정론 계약 + S06.2 greenfield production runtime/data-plane 경계(2026-09-15)**다. 저장 유실의 근본 원인과 독립 저장 내구성은 미해결이다. [저장 조사](docs/STORAGE_INVESTIGATION.md)와 [복구 범위·실행·제한](docs/PAID_RECOVERY.md)을 따른다.

기준 커밋 `2658a43`의 Groth16 설정에는 회로별 기여가 빠져 있었다. 당시 공개 증명·검증키만으로 공개 입력과 증명을 함께 조정해 검증을 통과하는 결함을 재현했다. 이후 회로별 기여·검증, 기존 키 거절, 조작 증명과 폐기·취소 경계 회귀를 추가했다. 과거 검증 수락 기록을 보안 보장으로 해석하지 않는다. [보완 결과](docs/PROTOCOL_HARDENING.md)를 먼저 읽는다.

## production architecture

```text
Client
  |
Rust KIX modular monolith + Tokio
  |
  +--> Rust kernel
  +--> PostgreSQL 18 narrow OLTP
  +--> Executor --> Sui gRPC / PG / Bank / FX
                         |
                  observation stream
                         |
                    Rust reducer

committed facts --> Arrow --> Parquet
                         |
               +---------+---------+
               |                   |
          Polars Lazy           DuckDB
        CPU Rust streaming       SQL
               |
         cudf-polars GPU
               |
              AI/ML
```

- production canonical identity: **KIX-BCS1**, not JSON CE1.
- production Move: immutable `ShowConfig` + independent inventory/right/sale/payment objects + sharded admission/nullifier state.
- Polars/DuckDB/cuDF: columnar analytics/AI plane이며 OLTP authority가 아님.
- Python/Node/SQLite reference: historical regression/fault fixture.

## 구성

| 경로 | 내용 |
|---|---|
| `runtime/` | S07+ Rust production runtime, KIX-BCS1, performance/AI data-plane contracts |
| `reference/v0.3-rc1/` | 역사적 Python/Node/SQLite, legacy Sui Move, 독립 클라이언트, ZK regression fixture |
| `reference/v0.1/`, `reference/v0.2/` | 이전 기준 모형 보존 |
| `reviews/` | v0.1·v0.2 검토와 재현 자료 |
| `scripts/`, `.devcontainer/`, `.github/workflows/` | 설치·검증 자동화, Codespaces 구성, CI |
| `validation/` | 역사적 실제 실행 로그·영수증·검증 자료 |
| `docs/` | 실행 방법, 검증 범위, 변경 근거, 개발 계획 |

## 실행

기존 fixture/localnet 회귀:

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

production architecture/Rust boundary:

```bash
python scripts/verify_runtime_architecture.py
cargo test --manifest-path runtime/Cargo.toml --workspace
```

Rust toolchain은 `rust-toolchain.toml`의 1.98.1로 고정한다. S07 business persistence와 actual KIX-BCS1 codec/production Move objects는 아직 구현 전이다.

## 확인된 범위

| 확인 항목 | 확인 범위·근거 |
|---|---|
| Python 모형·저장 경계·복구 검사 | S06.1 Python 207개를 복수 Python/SQLite 환경에서 통과한 역사적 regression 근거 |
| CE1 계산 계약 | Python/TypeScript에서 Commerce v2 고정 바이트·해시·배정·견적·반환안 일치. **production KIX-BCS1 보장은 아님** |
| S06.2 runtime 경계 | Rust 1.98.1 workspace와 architecture checker. 최종 S06.2 SHA에서 전체 CI로 판정 |
| Sui Move / ZK 회귀 | 기존 Move/회로/public/paid/private localnet regression 유지 |
| storage/recovery | S03/S05/S06의 제한된 지급 복구·archive 회귀 유지 |

현재 legacy chain fixture는 16-slot shared Show이고 RPC를 신뢰한다. 이것을 production throughput/topology로 해석하지 않는다. production ZK setup, independent checkpoint verification, 실제 PG·은행, remote durability는 미완료다.

## 주요 문서

- [개발계획 2.3 — Greenfield production protocol](docs/PROTOCOL_MASTERPLAN_V23.md)
- [S06.2 greenfield production architecture](docs/RUNTIME_ARCHITECTURE_S062.md)
- [KIX Binary Canonical Encoding v1](runtime/CANONICAL_BINARY_BCS_V1.md)
- [Production Sui object topology](runtime/MOVE_PRODUCTION_TOPOLOGY.md)
- [Runtime performance profile](runtime/PERFORMANCE_PROFILE.md)
- [AI / GPU data plane](runtime/AI_GPU_DATA_PLANE.md)
- [개발계획 2.2 — historical](docs/PROTOCOL_MASTERPLAN_V2.md)
- [S06.1 historical foundation](docs/FOUNDATION_S061.md)
- [CE1 historical/compatibility encoding](docs/CANONICAL_ENCODING_V1.md)
- [저장 기록 유실 조사](docs/STORAGE_INVESTIGATION.md)
- [프로토콜 보안 보완](docs/PROTOCOL_HARDENING.md)

## S05

Separate-filesystem archive와 reconciliation-only restore를 구현했다. restored workspace는 money execution을 재개하지 않는다. whole-host loss, remote durability, historical storage incident root cause는 미검증이다.

## S06

Asset/Amount, ordered discounts, multi-leg allocation, selected-line refund proposal을 계산-only 계약으로 구현했다. 외부 결제나 지급 권한을 만들지 않는다.

## S06.1

PR 계보, CE1, ASCII machine ID, Python↔TypeScript 결정론, registry-bound AssetAmount와 의미별 integer를 고정했다. 이 결과는 역사적 회귀/compatibility 자산으로 유지한다.

## S06.2 — greenfield reset

성능을 위해 production architecture를 기존 fixture에서 분리하는 수준을 넘어 **새 production design authority를 Rust 쪽으로 이동**한다.

- Rust-first production state machine
- PostgreSQL 18 typed OLTP
- KIX-BCS1 production canonical bytes/hash
- CE1/Python은 compatibility/regression only
- show-wide shared mutable Move topology 금지
- immutable ShowConfig, independent Right/SaleIntent/PaymentEvidence, sharded admission/nullifier
- Rust direct Sui gRPC streaming observation
- Arrow/Parquet columnar contract
- Polars Lazy를 feature/ETL의 기본 plan으로 사용
- DuckDB를 Parquet/Arrow SQL·대사에 사용
- cudf-polars/libcudf를 GPU feature acceleration에 사용
- AI/model output은 non-authoritative proposal이며 Rust kernel gate를 다시 통과

S07 Durable Commerce Execution은 이 아키텍처 위에서 처음부터 구현한다.

개인키·백업 비밀번호·비공개 노트·시험용 proving key·로컬 체인 DB는 추적하지 않는다. 공개 배포용 라이선스는 부여하지 않았다.
