# KIX 문서 색인

**현행 개발계획 정본은 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 하나입니다.** 현재 승인·금지·진행 순서는 §1·§5, 4단계 backend 비교는 §9를 따릅니다. 이 색인은 별도의 승인 문서가 아닙니다.

**[루트 README](../README.md)의 역할:** 프로젝트와 현재 기준·잠금·금지·읽는 순서를 안내하는 최초 입구.
**이 `docs/README.md`의 역할:** 같은 정본 아래 계약·검증·보존 자료의 위치를 안내하는 색인.

## 현재 문서 — 이 순서로 읽기

1. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) — 현재 계획·승인 범위.
2. [기준 commit·태그 표](status/BASELINES.md) — 현재 main, 고정 R1 태그, PR 검토 SHA, #11 실험을 구분.
3. [모델 1 결정](decisions/AUTHORITY_MODEL_1.md) — 체인 권위 / 오프체인 위임 실행. R2·(a) 착수 승인이 아님.
4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md).
5. [계약 불변식·비교 모델의 한계](contracts/CONTRACT_INVARIANTS.md), [첫 묶음 실행 근거](../validation/2026-09-16-first-batch/README.md).
6. [측정 계약](contracts/PERFORMANCE_MEASUREMENT.md), [고정 smoke 조건](contracts/PERFORMANCE_BASELINE_V4.md)(역사적 debug 논리 서명, 제품 p99 아님), [Task 004 장치 메모](../validation/2026-09-25-task-004-perf-measurement/README.md).
7. [잠금의 실제 CI 경로](status/LOCK_ENFORCEMENT.md), [위생 목록 — 실행 금지](CODE_HYGIENE_BACKLOG.md).
8. [원래 32개 항목](status/ORIGINAL_32_STATUS.md), [M 제외 부분 앵커](status/PARTIAL_ANCHOR_COUNTS.md), [#11 태그 보존](status/PR11_PRESERVATION.md).

## 역사 문서와 증거

[루트 역사 문서 목록](../README.md#6-역사-문서--현행-계획-아님)의 V24·V23·V2·BLUEPRINT·ROADMAP 등은 현행 계획이 아닙니다. 특히 V24의 자동 R2 진행은 현재 금지입니다. 역사 문서의 상단 경고 뒤 본문은 당시 기록으로 보존합니다.

[ADR-0001](adr/0001-ktx-authority-commit-recovery.md)의 안전 관계와 [보안 보완](PROTOCOL_HARDENING.md)·[저장 조사](STORAGE_INVESTIGATION.md)·[회귀 검증](RUNTIME_VALIDATION.md)은 근거별 범위로 읽습니다. 옛 계획의 승인 효력을 폐기했다고 안전 규칙이나 사건 기록을 삭제하지 않습니다.

모델 1·첫 묶음 승인은 backend 채택·커널 전환 완료·실금전 운영 승인과 다릅니다. 미정 항목, 두 잠금 blob, R2 금지, (a) 보류, 위생 일괄 금지는 유지합니다.
