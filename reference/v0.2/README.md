# KIX protocol reference v0.2

v0.1 검토를 반영한 실행 가능한 기준 모형. 실제 결제·은행·체인·광고 발송은 수행하지 않는다.

1. `KIX_프로토콜_수정명세_v0.2.md`: 변경 동작, 환불·원장·생애주기, 정확한 구현 범위.
2. `KIX_Sui_ZK_후속구현계약_v0.2.md`: 아직 구현하지 않은 체인·운영자 독립·ZK의 후속 계약.
3. `results/verification.json`, `results/mutation_results.json`, `results/acceptance_trace.json`: 재현 결과.

```bash
python -m pip install -r requirements.txt
python verify.py
```

72개 검사: 기존 31개 흐름을 새 계약에 맞춰 이식하고 41개 경계·복구 검사를 추가했다. 14개 선택 변이는 각각 정상 입력 검사의 성공을 확인한 뒤 실행한다. 전수 변이 비율이나 보안 보증이 아니다.

주요 변경: 취소 후 미송신 지급 중단, 원결제 취소/현금 환불/배분 지급 경로, 환불 의무 선인식, 부분 이행, 명시적 PG 정산 구성, 원자료 보존, 재고와 발행 권리 분리, 게시와 예약, 무상 양도, 초대권, 동의 버전 및 발송 의도 확인.

v0.1 DB를 열어 자동 변환하지 않는다. 프로토콜 도메인이 다르면 거절한다. 새 DB에서 실행한다. 내부 좌석 ID를 권리 ID로 사용하지 않는다. 유상 최초 예약에는 `inventoryId`, 재고 버전, `expectedVersion=0`을 보내고 반환된 새 `ticketId`를 이후 명령에서 사용한다.

`test_core.Harness`의 기본값은 시험 드라이버 편의 기능이다. 공개 프로토콜의 묵시적 경로/동의 갱신 기능이 아니다. `Core.execute`는 명령 계약을 엄격히 검사한다. 실제 원천 어댑터의 설계 진입점은 원문을 먼저 보존하는 `Core.ingest`다. 아직 실제 인증은 없다.

두 환불 프로필 모두 명시적 합성 사례다. `LATEST_TRADE_UNWIND_FIXTURE`가 실상품 일반 환불의 권장 부담 구조라는 의미가 아니다. 현재 배분 비율과 전체 수취인의 행사 완료 후 지급도 시험 가정이다.

로컬 내보내기/재구축은 unsigned fixture 복구다. `vendor/rights_model.py`는 보존된 독립 모형이며, 코어의 실제 권리 정본으로 연결되지 않았다. Move 코드, 실제 ZK 회로, 독립 운영 검표자는 이 패키지에 구현돼 있지 않다.

해시는 `results/manifest.sha256.json`에 있다. 검증을 다시 실행하면 테스트 소요 시간과 일회용 변이 폴더가 포함된 텍스트 로그는 달라질 수 있다. 수용 사례 JSON과 환경이 같은 검증 요약 JSON은 결정적이다.
