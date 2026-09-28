# KIX 기준 commit·태그 용도표

확인 기준: 2026-09-16, 문서 정합화 시작 시 main `d5b9f2d67b5532fa35464c8557e88f70be300888`.
**진행 순서·승인의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)이며, 이 표는 소스와 증거의 기준을 분리하는 색인입니다.**

## 다섯 기준의 용도

| 기준 | 정확한 식별자 | 무엇의 기준인가 | 지금 작업에서의 사용 |
|---|---|---|---|
| 현재 main 작업선 | 문서 작업 시작 시 `d5b9f2d67b5532fa35464c8557e88f70be300888`; tree `c3b02085650ad394283f3325cf5dd87664c66ddb` | #12/#13 병합과 #11 보존 문서까지 포함한 작업 시작 스냅샷 | **현재 문서 작업의 base.** 이후 실제 main HEAD는 작업 시작 때 다시 확인. 이 고정값을 영구 최신값이라고 쓰지 않음 |
| 고정 R1 기준선 | `kix-r1-v4-verification-baseline-20260916` → `d5b9f2d67b5532fa35464c8557e88f70be300888`; tag object `05d133c9dc4ef8e979391ced4099d2c9415e0124` | R1 v4 + 검증 장치의 재현 기준 | 비교·회귀 기준. **통합 완료·R2 완료·운영 승인 아님.** 문서 변경 때문에 태그를 옮기지 않음 |
| PR #12 검토 기준 | `c8267d1c2bdbcd732aa46401fe059b92d8ae72a6`; tree `fb8b67b6d9f1fcddea68153a9f4b9e9310cee776` | v4 슬롯·격리 구현과 문서 정합화 시점 | 과거 검토 근거. 새 작업을 이 브랜치에서 자동 시작하지 않음. 커널 원구현 `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631`과 잠금 blob 동일 |
| PR #13 검토 기준 | `0cb65749492bf78e6cea00d3c9c7eee4f891827d`; tree `59746105a8e1b82b0109bb958e6f9104abb70f39` | 첫 묶음 모델·불변식·측정 장치·계약 초안 인수 시점 | 당시 결과의 정확한 소스 앵커. main에 병합된 과거 head이지 별도 최신 정본 아님 |
| PR #11 실험 보존 | `kix-exp-r2a-local-journal-v1-20260916-r2` → `55a3df4968f5684bb4cb9e3c9781ab5f00165235`; tree `38901ede6a20dc67025014116ea92c0ea35f8bf5`; tag object `1311668253bbbbffdc90f1a9f446c42d43e5fa1f` | 의미론 **1**의 wire·로컬 저널 실험과 정정된 cold-build 호환성 증거 | 조회·비교용 보존. **현재 v4 코드에 포함되지 않음. (a) 미승인, R2 금지** |

실제 main 확인 예: `git fetch origin main` 후 `git rev-parse origin/main`.
로컬 작업 중인 HEAD도 별도로 `git rev-parse HEAD`로 기록합니다. 문서에 자기 자신의
미래 commit SHA를 쓰려 하지 않으며, 새 문서 제출 SHA와 main 병합 여부는 해당 PR/commit에서 확인합니다.
태그를 다시 발행하거나 main을 과거 head로 이동시키라는 명령이 아닙니다.

## 병합과 문서 차이

#12 merge `31e60b2269e90cba6da9a1a41dacf039f5662c30`의 tree는 #12 검토 head와 같습니다.
#13 merge `bf6c2be37e8c55778f4fe378634f7895fd69a327`의 tree도 #13 head와 같습니다.
그 뒤 `d5b9f2d67b5532fa35464c8557e88f70be300888`은 `docs/status/PR11_PRESERVATION.md`만 추가했습니다.
따라서 최종 main의 전체 tree와 #13 tree가 다르더라도 커널이 달라졌다는 뜻은 아닙니다.

## 보존하되 채택하지 않는 식별자

첫 #11 태그 `kix-exp-r2a-local-journal-v1-20260916`는 같은 v1 commit을 가리키지만,
공유 빌드 디렉터리의 all-pass 결과를 담아 **호환성 인수 근거에서 제외**됐습니다.
삭제·강제 이동하지 않고 `-r2` 정정 태그를 사용합니다. 이 `r2` 접미사는 태그 정정 차수이지 R2 개발 승인 표시가 아닙니다.
세부 실패·원본 CI·자료 위치는 [PR11_PRESERVATION.md](PR11_PRESERVATION.md)에 있습니다.

기존 제출안 `57adb8d579986a945b716f0f181c0be938ceb389`는 **문서 Git blob**이며,
commit SHA나 운영 기준 태그가 아닙니다. 새 원격 정본의 경로는 `docs/DEVELOPMENT_PLAN.md`입니다.
`98d5f6372b68f875bcb2b670c5998697ecfb76c1`은 S07-A의 역사적 구현/시험 소스이며 지금의 작업 시작점이 아닙니다.

## 증거를 승계하지 않는 원칙

R1 기준선 태그가 가리키는 main의 전체 protocol run은 `35079606640`이며 success였습니다.
exact-main 검증은 operation run `35079754929`에서 target main을 checkout했습니다.
PR #13 전체 run `35069017150`과 KTX run `35069017358`은 #13 head 대상입니다.
이전 SHA의 성공을 새 문서 변경 head의 성공으로 자동 표시하지 않습니다.
위 표의 기존 R1·#11 태그는 annotated/unsigned이며 문서상 고정과 서버 보호 규칙은 별개입니다.
2026-09-17 추가된 `kix-exp-r1-preservation-ops-v1-20260916`은 운영 이력 보존용
**lightweight tag + GitHub Pre-release 본문**입니다. 새 개발 기준선으로 세지 않습니다.
대상 commit·tree·본문 위치와 대조값은 [운영 이력 보존 기록](PR11_PRESERVATION.md)에 있습니다.

## 2026-09-28 추가 — hosted CI 공백 기간의 기준

| 기준 | 정확한 식별자 | 사용 |
|---|---|---|
| 마지막 hosted CI 녹색 main | `b61e48d965e7ed3f1c5f4fcd5ad863b961ce4e28`(#62 병합), KIX protocol verification run `36184686465` success | CI 공백 이전의 마지막 검증 지점. 이후 SHA로 승계하지 않음 |
| 2026-09-28 확인 main | `34a722d26fa894366c26bac9de4187c598fbf3eb`(#72 병합), run `36304355015` failure(사용량 소진, 테스트 본문 미실행) | hosted CI 미검증. 로컬 대체 결과만 있음 |

2026-09-26 이후 병합분과 원인 기록, 복구 뒤 확인할 항목은 [main 상태 정합 기록](MAIN_STATE_20260928.md)에 있다. 이 표도 태그를 새로 만들거나 옮기라는 뜻이 아니다.
