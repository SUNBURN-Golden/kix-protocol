# KIX Protocol

티켓의 발행·구매·공식 리셀·입장·환불·배분·정산을 연결하는 프로토콜 연구·개발 저장소다.

현재 개발 기준은 **[v0.3-rc1](reference/v0.3-rc1/README.md)**이다. Python 기준 모형의 금융·생애주기 수정은 검사했으며, Sui Move·독립 클라이언트·ZK 회로는 소스를 포함했다. **실제 Sui 빌드·체인 실행·ZK 증명 생성은 아직 검증하지 않았다.**

## 구성

| 경로 | 내용 |
|---|---|
| `reference/v0.3-rc1/` | 현재 후보: Python 수정, Sui·클라이언트·회로 소스, 명세·검사·검증자료 |
| `reference/v0.2/` | v0.3의 기준이 된 v0.2 배포본과 원본 해시 |
| `reference/v0.1/` | 기존 v0.1 통합 명세·코드·검사·결과 |
| `reviews/v0.2-2026-09-11/` | v0.2 목적 대조 검토와 경계 사례 재현 코드·결과 |
| `reviews/v0.1-2026-09-11/` | 기존 v0.1 검토와 재현자료 |
| `docs/ROADMAP.md` | 현재 완료 범위와 다음 실행 기준 |

각 버전의 배포 파일은 기존 manifest와 일치하는 사본이다. v0.2의 42개, v0.3-rc1의 71개 파일 해시를 확인했다. manifest 자체는 이 수에 포함하지 않는다.

## 빠른 확인

저장소 루트에서 다음 명령을 실행한다. 검증 환경은 Python 3.12.14, SQLite 3.53.1, cryptography 46.0.0이었다.

```bash
python3 -m pip install -r reference/v0.3-rc1/requirements.txt
python3 reference/v0.3-rc1/scripts/verify_package.py
python3 -m unittest discover -s reference/v0.3-rc1 -p 'test_*.py' -v
node --test reference/v0.3-rc1/client/offline.test.mjs
```

기록된 검증 결과는 Python 88개 검사 통과, 선택한 방어 변이 14개 탐지, Node 오프라인 검사 4개 통과다. Node 검사는 백업·직렬화에 대한 검사이며 Sui SDK나 실제 체인의 실행 결과가 아니다.

`verify.py`, 변이 검사 및 결과 재생성 스크립트는 결과 파일을 덮어쓸 수 있다. 배포본의 해시를 유지하려면 별도 사본에서 실행한다. 상세 명령은 [후보 패키지 README](reference/v0.3-rc1/README.md)를 따른다.

## 실제 체인 검증

Sui CLI와 npm 의존성을 설치할 수 있는 환경에서 버전을 고정한 뒤 Move 테스트, 로컬넷 A→B 이전·백업 복구·대체 검표, ZK 증명 생성과 체인 검증을 실행해야 한다. 필요한 도구가 없으면 `scripts/preflight.py`는 종료 코드 3을 반환한다. 현재 체인 실행과 증명 생성 결과는 `false`로 기록되어 있다.

- [v0.3-rc1 구현 결과와 실행 조건](reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md)
- [Sui·ZK 설계와 제한](reference/v0.3-rc1/DESIGN_SUI_ZK.md)
- [v0.3-rc1 검증 결과](reference/v0.3-rc1/results/verification.json)
- [v0.2 기술 검토](reviews/v0.2-2026-09-11/KIX_v0.2_목적대조_기술검토.md)
- [다음 개발 순서](docs/ROADMAP.md)

실제 PG·은행·운영용 체인과 연결하거나 실제 돈을 이동한 결과가 아니다. 이 저장소에는 공개 배포용 라이선스를 부여하지 않았다.
