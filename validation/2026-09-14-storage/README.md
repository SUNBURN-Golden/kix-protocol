# 저장 조사 검증 자료

기준: `8e69bd7`. 이 디렉터리는 후속 저장 조사와 명시적 장애 주입 결과다.

- `probe-default.json`: Python 3.12.14 / SQLite 3.53.1, 합성 체인 + 실제 조정자 저장 코드, 66개 명령.
- `probe-system.json`: Python 3.12.3 / SQLite 3.45.1, 같은 합성 경로 66개 명령.
- `deliberate-rollback.json`: 모의 제공자 처리 뒤 projection만 과거로 되돌리는 의도적 장애. 기존 판단의 위험과 새 차단을 비교한다.
- `python-default.log`, `python-system.log`: 전체 Python 검사 결과. 새 8개는 저장 경계·실제 프로세스 종료·잠금·CLI 차단을 검증한다.
- `manifest.json`: 변경 소스와 결과 파일의 SHA-256.

`NO_FAILURE_REPRODUCED`는 과거 사고가 없었다거나 해결됐다는 뜻이 아니다. `DELIBERATE_PROJECTION_ROLLBACK`은 원인 미상의 자연 유실과 구분한다. 실제 체인·ZK 재검증은 이 PR의 GitHub Actions에서 별도 확인한다.

공개 결과에는 개인키·서명·DB·WAL·실제 결제 참조가 없다. 프로브의 전체 합성 명령 trace와 닫힌 DB 세트는 로컬 `.local/storage-probe-*/`에 보존하며 저장소에는 포함하지 않는다.
