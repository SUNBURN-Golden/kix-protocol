# 2026-10-08 로컬 탐색 원시 자료

이 디렉터리는 Track K 4단계 로컬 탐색의 원시 표본이다. **탐색 자료**이며
제품 SLO, backend 채택, 내구성 우열이 아니다.

비교 답의 정본은 [개발계획 §9](../../docs/DEVELOPMENT_PLAN.md) 비교표 하나다.
이 파일은 그 표를 다시 만들지 않는다.

| 파일 | 내용 |
|---|---|
| `host.json` | 후보 프로세스를 시작하기 전에 기록한 기계·버전·잠금 blob·자원 cap |
| `manifest.json` | 두 후보가 같은 입력 fingerprint를 썼고 ranking이 비어 있다는 확인 |
| `postgresql/summary.json`, `postgresql/samples.csv` | PostgreSQL 17.11 로컬 실행 |
| `foundationdb/summary.json`, `foundationdb/samples.csv` | FoundationDB 7.3.77 단일 로컬 프로세스 |

재현은 저장소 루트에서 다음이다. 로컬 PostgreSQL 17과 FoundationDB 7.3.77이
필요하며, 측정 프로세스는 루프백 또는 유닉스 소켓만 연다.

```bash
python3 scripts/stage4_local_explore.py validation/2026-10-08-k-stage4-local-exploration
python3 -m unittest exploration.stage4.test_stage4
```

후보를 동시에 띄우지 않는다. 체인 재고 writer, 실 PG/은행 호출, 공개 운영
엔드포인트는 없다.
