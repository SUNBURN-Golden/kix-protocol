# KIX Protocol

티켓의 발행·구매·공식 리셀·입장·환불·배분·정산을 연결하는 프로토콜 연구·개발 저장소다.

현재 포함한 구현은 **SQLite 기반 합성 참조 모형 v0.1**이다. 실제 블록체인·PG·은행과 연결하지 않았으며, 검토에서 발견한 수정 사항은 아직 구현하지 않았다.

## 구성

| 경로 | 내용 |
|---|---|
| `reference/v0.1/` | 첨부된 통합 명세·코드·31개 검사·결과의 변경 없는 사본 |
| `reviews/v0.1-2026-09-11/` | 상세 검토보고서, 추가 재현 코드, 단일 변이 결과와 로그 |
| `docs/ROADMAP.md` | 검토에 따른 후속 개발 순서와 완료 기준 |

## 실행

검증 환경은 Python 3.12.14, SQLite 3.53.1, cryptography 46.0.0이다.

```bash
python -m pip install -r reference/v0.1/requirements.txt
python -m unittest discover -s reference/v0.1 -p test_core.py -v
```

검토 재현:

```bash
python reviews/v0.1-2026-09-11/review_probe.py --bundle reference/v0.1 --output .local/review
```

원본 `verify.py`는 결과 JSON과 manifest를 덮어쓴다. 기준 자료를 보존하면서 실행하려면 `.local/` 등의 별도 사본에서 실행한다.

## 확인된 범위

- 원본 31개 합성 검사가 통과했고 주요 JSON 2개가 재현됐다.
- 추가 경계 사례 10개는 현재 동작·제약의 재현이며 제품 요구사항 통과가 아니다.
- 단일 변이 10개 중 5개는 기존 검사가 탐지했고 5개는 탐지하지 못했다. 선택한 표본의 결과이며 전체 품질 점수가 아니다.
- 기존 권리 모형과의 검사는 일부 조건의 계약 검사다. 실제 체인·PG 사이의 분산 실행, ZK, 운영자 독립성은 아직 구현·검증하지 않았다.

## 문서

- [통합 명세 v0.1](reference/v0.1/KIX_프로토콜_통합명세_v0.1.md)
- [상세 검토](reviews/v0.1-2026-09-11/KIX_통합프로토콜_v0.1_상세검토.md)
- [후속 개발 계획](docs/ROADMAP.md)

초기 저장소 구성일: 2026-09-11. 이번 가져오기는 구현 변경이 아니다. 이 저장소에는 공개 배포용 라이선스를 부여하지 않았다.
