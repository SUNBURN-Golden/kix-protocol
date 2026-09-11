# v0.2 목적 대조 검토

사용자가 제공한 검토보고서, 재현 코드, 결과 및 검증 요약을 보존했다. 보고서 안의 작성 당시 로컬 경로는 원문의 일부다. 원본 v0.2 패키지는 저장소의 `reference/v0.2/`에 있다.

저장소 루트에서 재현한다.

```bash
python3 reviews/v0.2-2026-09-11/review_v02_probe.py --bundle reference/v0.2 --output .local/review-v0.2
```

이 코드는 v0.2의 문제·제약을 재현하는 호출 코드다. v0.3의 수정 결과는 `reference/v0.3-rc1/results/review_trace_v03.json`을 참고한다. 실제 PG·체인 실행 검사는 아니다.
