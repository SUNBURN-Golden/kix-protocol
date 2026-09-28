# KIX Protocol

KIX는 티켓 권리·거래 프로토콜을 중심으로 예매, 공식 리셀, 검표, 환불·정산, 금융 근거와 마케팅을 연결하는 연구·개발 프로젝트입니다. 승인된 권위 모델은 **모델 1 — 체인 권위 / 오프체인 위임 실행**이며, 기존 검증 자산을 계승해 Rust 운영 구현을 구축합니다. 현재 R1 v4는 메모리 내 거래 전이와 검증 장치의 기준선이지, 실제 체인 위임·회수, 내구성 있는 경제 엔진 또는 production 운영의 완성본이 아닙니다.

## 1. 현재 기준

**현행 개발계획 정본은 [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)입니다.** 승인·금지 범위와 다음 순서는 이 문서를 따릅니다. V24는 현행 정본이 아닙니다.

- 고정 R1 기준선: [`kix-r1-v4-verification-baseline-20260916`](https://github.com/BeautifulMind-JT/kix-protocol/tree/kix-r1-v4-verification-baseline-20260916).
- 이번 문서 작업 시작 시 확인한 **main HEAD**: `d5b9f2d67b5532fa35464c8557e88f70be300888`. 이 값은 기준 스냅샷이며, 이 문서 변경 뒤에도 영원히 최신 HEAD라는 뜻이 아닙니다.
- 실제 다음 작업은 [현재 main](https://github.com/BeautifulMind-JT/kix-protocol/tree/main)의 HEAD를 다시 확인하고 시작합니다. 태그·검토 SHA·실험 보존본의 용도는 [기준표](docs/status/BASELINES.md)에서 한 번에 확인합니다.

**이 루트 README의 역할:** 처음 온 독자가 프로젝트·현재 기준·금지 범위·읽는 순서를 확인하는 입구입니다.
**[docs/README.md](docs/README.md)의 역할:** 동일한 정본 아래 계약·검증·기록을 찾는 문서 색인입니다. 별도의 개발계획이 아닙니다.

## 2. 변경 금지 파일

| 파일 | 잠금 Git blob | 잠금 이유 |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | 검토한 R1 v4 동작을 고정해 모델·불변식·측정 결과의 기준이 움직이지 않게 함 |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | 만석에서도 bound 격리를 보존하는 검토 회귀를 고정 |

주석·명칭·포맷·자동 수정·임시 mutation도 잠금 예외가 아닙니다. 현재 CI는 테스트를 통해 두 blob을 대조합니다. [강제 경로와 한계](docs/status/LOCK_ENFORCEMENT.md)를 읽으세요. 테스트 검사는 브랜치 보호·필수 상태 검사 설정과 다릅니다.

## 3. 금지·보류 작업

| 작업 | 현재 판단 | 근거 |
|---|---|---|
| R2 및 자체 복제·저장·로그 신규 구현 | **금지 유지**. 단, 비운영 로컬 래퍼인 `readiness/`는 D-3 경계 안에서 허용 | [개발계획 §1·§5](docs/DEVELOPMENT_PLAN.md), [권위 모델 결정](docs/decisions/AUTHORITY_MODEL_1.md), [프로그램 결정 §4](docs/decisions/PROGRAM_DECISIONS_20260928.md) |
| (a) PR #11의 wire·저널을 v4 위로 통합 | **착수 승인 없음** | [권위 모델 결정](docs/decisions/AUTHORITY_MODEL_1.md), [#11 태그 보존·호환성](docs/status/PR11_PRESERVATION.md) |
| 명칭·죽은 코드·브랜치·태그·Cargo/CI/lint 등 위생 일괄 실행 | **목록만 유지, 실행 금지** | [코드 위생 목록](docs/CODE_HYGIENE_BACKLOG.md), [개발계획 §1](docs/DEVELOPMENT_PLAN.md) |
| 색인 변경·새 종결/회수/해제 전이 | **첫 묶음에서 제외** | [개발계획 §5·§6.3](docs/DEVELOPMENT_PLAN.md), [수명 계약 초안](docs/contracts/STATE_LIFECYCLE.md) |

KTX는 옛 코드명 표기이며 **정의된 약자가 아닙니다**. **3단계 schema·SDK에서 별도 승인 후 KIX Runtime으로 바꿀 예정**이며, 지금 일괄 치환하지 않습니다.

## 4. 승인된 다음 작업

현재 승인된 것은 **첫 묶음의 잔여 검토·보완**입니다. 잠금 v4의 비교 모델·계약 불변식 검사 검토, LC-FACT/LC-CUT/LC-TERM 수명 계약의 미정 입력 정리, 별도 성능 하네스·측정 계약의 검토를 진행합니다. 구체적인 열린 항목과 답할 주체는 [FIRST_BATCH_OPEN_INPUTS](docs/contracts/FIRST_BATCH_OPEN_INPUTS.md)를 따릅니다.

2026-09-17 사용자 결정으로 **토스페이먼츠를 잠정 선택하고, 결제수단 1단계는 토스를 통한 국내 KRW 일반 카드 결제로 한정**합니다. 리셀·금융 대금의 실제 가맹 범위와 일반 결제 웹훅 서명 규격은 미확인이므로 최종 가맹·운영 승인이 아닙니다. 간편결제·가상계좌는 토스 내 수단으로 나중에 검토하며, 간편결제 직접 가맹은 이번 범위가 아닙니다.

[토스 카드 제공자 프로파일](docs/contracts/PG_TOSS_CARD_PROFILE.md)에 공개 규격상 확인값·확인일·남은 질문과 어댑터 경계를 정리합니다. 공개값의 계약 초안 반영과 후보 잠정 선택은 실제 연동·종결/해제 구현·실자금 실행의 승인이 아닙니다. 모델 1 확정도 (a)·R2 착수로 확대하지 않습니다.

기존 E-4 비교 모델은 커널 소스를 참고해 작성했습니다. 두 구현의 일치와 계약 불변식 검증은 구분하며, [검증 범위·한계](docs/contracts/CONTRACT_INVARIANTS.md)를 유지합니다. 실제 은행 자금·체인 위임·분산 내구성을 검증했다는 뜻이 아닙니다.

**2026-09-28 현황:** 2026-09-25~27 main에는 다음이 병합됐습니다.

- Task 004 측정 장치
- [Task 005](docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md) Wave 2~5: Move 발행 확장, 정산·예매/리셀/검표·F04 여신의 mock과 상태기계
- 계약 전용 OpenAPI, loopback HTTP 관문, 로컬 readiness 저널

모두 mock·비운영 범위이며, 실 PG·은행·체인 연동이나 운영 승인이 아닙니다. 병합 목록과 CI 기록은 [main 상태 정합 기록](docs/status/MAIN_STATE_20260928.md)에 있습니다. 2026-09-26부터는 GitHub Actions 사용량이 소진돼 hosted CI가 실행되지 않았습니다.

**2026-09-28 결정:** 사용자가 PR #73을 병합(`cfeb0d6`)하면서 [프로그램 결정 D-1~D-3](docs/decisions/PROGRAM_DECISIONS_20260928.md)을 승인했습니다. 이제 승인 범위는 두 트랙입니다.

- **Track K (커널·영속):** 위 첫 묶음과 개발계획의 단계를 따릅니다. 4단계 backend 비교는 준비와 로컬 탐색 실측까지 열렸습니다.
- **Track P (제품 프로토콜):** Task 005 Wave 0~7과 그 후속입니다. 계약·mock·Move 확장·OpenAPI·비운영 0.x SDK·분리 저장소 앱·AI 위임 계약을 다루며, 게이트 기록만으로 착수합니다. Wave 2~5는 사후 승인됐고, Wave 6은 `kix-commerce-apps`에서 열렸습니다.

실자금·실 제공자 호출·공개 운영 엔드포인트·mainnet·커널 잠금·R2는 계속 잠겨 있습니다. 각 잠금의 해제 조건은 결정 문서 §5에 있습니다.

## 5. 읽는 순서

1. [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) — 현행 승인·금지·단계, **4단계 비교 정본은 §9 한 곳**.
2. [BASELINES.md](docs/status/BASELINES.md) — 지금 쓰는 main과 고정·역사 기준을 구분. [main 상태 정합 기록](docs/status/MAIN_STATE_20260928.md) — 2026-09-28 병합 범위·CI 공백·열린 결정.
3. [AUTHORITY_MODEL_1.md](docs/decisions/AUTHORITY_MODEL_1.md) — 승인된 모델과 현재 구현의 차이.
4. [STATE_LIFECYCLE.md](docs/contracts/STATE_LIFECYCLE.md) / [열린 입력](docs/contracts/FIRST_BATCH_OPEN_INPUTS.md) — 초안이며 미정 입력이 남음.
5. [CONTRACT_INVARIANTS.md](docs/contracts/CONTRACT_INVARIANTS.md) / [첫 묶음 증거](validation/2026-09-16-first-batch/README.md) — 무엇을 검사했고 검사하지 않았는지.
6. [PERFORMANCE_MEASUREMENT.md](docs/contracts/PERFORMANCE_MEASUREMENT.md) / [V4-SMOKE-001](docs/contracts/PERFORMANCE_BASELINE_V4.md) — 장치와 고정 조건; production 성능 실측 아님.
7. [Runtime 범위](runtime/README.md), [잠금 강제](docs/status/LOCK_ENFORCEMENT.md), [32개 상태표](docs/status/ORIGINAL_32_STATUS.md), [부분 앵커](docs/status/PARTIAL_ANCHOR_COUNTS.md).

## 6. 역사 문서 — 현행 계획 아님

아래 문서는 직접 열어도 첫 줄에서 역사 자료임을 표시합니다. 과거 본문은 보존하되 그 안의 ‘현재’, ‘다음’, ‘즉시 진행’을 오늘의 승인으로 읽지 않습니다.

| 문서 | 용도 |
|---|---|
| [PROTOCOL_MASTERPLAN_V24.md](docs/PROTOCOL_MASTERPLAN_V24.md) | **현행 아님** — 이전 2.4 실행·저장 로드맵 |
| [PROTOCOL_MASTERPLAN_V23.md](docs/PROTOCOL_MASTERPLAN_V23.md) | **현행 아님** — 이전 2.3 PostgreSQL 중심 계획 |
| [PROTOCOL_MASTERPLAN_V2.md](docs/PROTOCOL_MASTERPLAN_V2.md) | **현행 아님** — 이전 2.2 포괄 프로토콜 계획 |
| [BLUEPRINT_20260914.md](docs/BLUEPRINT_20260914.md) | **현행 아님** — 2026-09-14 단계·상품 블루프린트 |
| [ROADMAP.md](docs/ROADMAP.md) | **현행 아님** — 2026-09-13 로드맵 |
| [ROADMAP-v0.1.md](docs/ROADMAP-v0.1.md) | **현행 아님** — 2026-09-11 초기 로드맵 |
| [PROTOCOL_INTEGRATION_NEXT.md](docs/PROTOCOL_INTEGRATION_NEXT.md) | **현행 아님** — 이전 다음 통합 계획 |
| [RUNTIME_ARCHITECTURE_S062.md](docs/RUNTIME_ARCHITECTURE_S062.md) | **현행 아님** — S06.2 당시 실행 구조·후속 순서 |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | **현행 아님** — historical fixture의 2026-09-11 개발 환경 안내 |

[ADR-0001](docs/adr/0001-ktx-authority-commit-recovery.md)의 안전 관계, [보안 보완](docs/PROTOCOL_HARDENING.md), [저장 조사](docs/STORAGE_INVESTIGATION.md), [복구 제한](docs/PAID_RECOVERY.md)과 [archive 제한](docs/PAID_ARCHIVE.md)은 별도 근거입니다. 옛 계획의 효력 폐기가 그 안전 조건·실패 기록·미해결 사항을 지운다는 뜻은 아닙니다.

`reference/`, `validation/`, `reviews/`의 과거 코드·실험은 보존 자산입니다. Python/Node 시험 도구를 사용하는 것과 Python 운영 엔진을 채택하는 것은 다릅니다. 원본 증거를 현재 결과로 재라벨링하지 않습니다.

개인키·비공개 노트·proving key·로컬 체인 DB를 제출하지 않습니다. 공개 배포용 라이선스는 부여하지 않았습니다.
