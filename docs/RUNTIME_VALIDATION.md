# v0.3-rc1 실행 검증

> 과거 실행 기록이다. 이후 `2658a43`의 회로별 기여 누락과 조작 증명 수락을 재현했다. 이 문서의 정상 증명 수락 기록은 건전성 보장을 뜻하지 않는다. 수정 후 결과는 [프로토콜 보완 보고](PROTOCOL_HARDENING.md)를 따른다.

검증일: 2026-09-11. 이 보고는 원래 rc1의 미실행 Sui·ZK 부분을 실제로 실행한 결과다. 특허 신규성·진보성 또는 상용 보안 감사 결과를 뜻하지 않는다.

## 결과

| 대상 | 확인 결과 | 근거 |
|---|---|---|
| 설치 | Sui 1.79.1, SDK 2.30.0 및 잠긴 npm 의존성 설치 완료 | `runtime-versions.json` |
| Python | 88개 합성 검사 통과 | `python-tests.log` |
| Node | 4개 오프라인 검사 통과, 실제 SDK import 성공 | `node-offline.log`, `sdk-import.log` |
| Move | 3개 검사 통과, 로컬 게시 성공 | `move-tests.log`, 거래 자료 |
| 회로 | mint/spend 2개 컴파일 | `circuit-build.log` |
| 공개 여정 | 별도 프로세스 복구·소비, 이전 소유자·중복 소비 거절 | `public-journey.json` |
| 비공개 여정 | 노트 생성·소비 Groth16 증명을 Sui가 수락 | `private-journey.json` |
| 비공개 오류 | 변경 문맥 `zk_gate:2`, 다른 검증키 `rights:4`, 중복 `rights:8` 거절 | `private-transactions.json` |

모든 근거 파일은 [validation/2026-09-11](../validation/2026-09-11/)에 있다. 공개 여정 9건, 비공개 여정 13건의 거래 기록에서 개인키·비밀번호·서명·요청 원문은 제외했다. 실패한 거래의 digest와 실제 실행 상태를 보존했다. 로컬 체인의 digest이므로 공개 익스플로러에서 조회하는 기록은 아니다.

`build-verification.json`의 `chainExecuted`와 `proofGenerated`가 false인 이유는 기본 빌드 검사만 기록하기 때문이다. 체인 실행과 증명 수락은 별도의 journey JSON에서 확인한다. 시험용 ZK manifest의 `suiSerializationVerified: false`도 파라미터 생성 시점 기록이며, 그 뒤의 실제 Sui 수락 결과는 `private-journey.json`에 있다.

기존 선택 변이 14개는 원래 rc1 실행 자료를 보존했으며 이번에 다시 실행하지 않았다. 검사 개수는 오류 탐지 범위나 전체 안전성을 대신하지 않는다.

## 실행을 위해 수정한 부분

1. Move `create_show`의 사용하지 않는 추가 `payment_refs` 인자를 제거해 실제 호출 인자 수와 맞췄다. 해당 저장 필드는 빈 벡터로 생성된다.
2. 2024 Move에서 허용되지 않는 벡터 인덱스 대입 네 곳을 `borrow_mut`를 통한 대입으로 바꿨다.
3. Sui CLI·프레임워크 커밋·SDK 버전을 고정하고 `Move.lock`과 `package-lock.json`을 만들었다.
4. Circom WASM이 include 경로를 읽을 수 있도록 회로와 circomlib를 같은 임시 작업 영역에 배치한 뒤 컴파일한다. 회로의 제약식은 변경하지 않았다.
5. 기본 클라이언트는 SDK 사전 시뮬레이션을 유지한다. localhost 시험 전용 클라이언트는 명시적 gas와 이미 만든 transaction kind로 의도적 실패 거래를 실제 제출한다. 따라서 사전 시뮬레이션 오류를 체인 거절로 잘못 기록하지 않는다.
6. 실패 거래에도 영수증을 붙이고, 제출한 정확한 바이트의 digest를 기록한다. snarkjs worker가 남아 설정 프로세스 종료를 방해하던 부분은 모든 작업과 출력 완료 후 명시적으로 종료하도록 수정했다.
7. zkLogin을 쓰지 않는 새 로컬넷에서 OAuth JWK 백그라운드 조회를 비활성화했다. [설치 문서](DEVELOPMENT.md)에 원인·범위를 기록했다.

Python 금융·환불·송신 모형과 원래 회로 제약식을 이번 실행 보완에서 바꾸지 않았다. [원래 rc1 대비 소스 패치](runtime-changes-from-rc1.patch), [원본 가져오기 해시](source-imports-2026-09-11.json), `validation/2026-09-11/imported-rc1-manifest.json`으로 구분한다. 현재 소스의 패키지 해시는 `reference/v0.3-rc1/results/manifest.sha256.json`이다.

## 이번에 입증한 독립성의 범위

조정용 설정 프로세스가 종료된 뒤 다른 프로세스가 암호화 백업을 읽고 공개 체인 자료를 조회해, 자신의 gas와 다른 검표자 키로 실제 권리 소비를 완료했다. 실제 KIX 로그인·salt·대납 서비스를 구현하고 모두 종료한 실험은 아니다. RPC와 검증키·체인 식별의 초기 신뢰는 남아 있다.

## 남은 검증

- 검증자 1개의 로컬 체인이다. 다중 검증자 장애·네트워크 분할·RPC 악성 응답·검열을 시험하지 않았다.
- 실제 PG·은행 증거·정산 자금 이동을 붙이지 않았다. 허가된 attester의 진술을 은행 입금의 암호학적 증명으로 보지 않는다.
- Groth16 파라미터는 단일 주체 시험용이다. 신뢰 설정, 회로 감사, 운영 검증키 관리가 남아 있다.
- 비공개 모형은 16슬롯이며 전환 거래와 주소가 공개된다. 익명 집합 크기와 메타데이터 연계로 실서비스 익명성을 주장할 수 없다.
- 비공개 리셀·환불·unshield·키 교체는 미구현이다. 현재 세대 변경·폐기·재발행 후 오래된 비공개 증명이 거절되는 별도 실제 체인 음성 사례도 이번에는 실행하지 않았다.
- Codespaces 설정과 CI workflow는 준비했다. 별도 Codespace 인스턴스를 생성한 결과와 동일하지 않다.

다음 개발은 이 실행 가능한 기준에서 [통합 프로토콜 후속 작업](ROADMAP.md)으로 이어간다.
