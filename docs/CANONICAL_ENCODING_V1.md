# KIX Canonical Encoding v1

S06.1의 새 자산·계산·실행 계약은 `kix:canonical-encoding:1`(CE1)을 사용한다. 이 규격은 동일한 값을 동일한 바이트와 해시로 표현하기 위한 계약이다. 서명자의 권한, 외부 결제의 진실성, 지급 허가를 증명하지 않는다.

## 바이트 규칙

| 대상 | CE1 규칙 |
|---|---|
| 인코딩 | BOM 없는 UTF-8 JSON, 공백 없는 구분자 |
| 객체 키 | 길이 1–128의 표시 가능한 ASCII(U+0021–U+007E), ASCII 사전순 정렬 |
| 배열 | 원래 순서를 보존. 할인·결제 경로의 순서를 자동 정렬하지 않음 |
| 문자열 값 | Unicode 15.0에서 배정된 scalar만 허용, 이미 NFC여야 함. 묵시적 정규화·대체 문자 삽입 없음 |
| 문자열 이스케이프 | 따옴표·역슬래시와 JSON 제어문자만 이스케이프. 나머지 Unicode는 UTF-8로 기록 |
| JSON 숫자 | −(2^53−1)부터 2^53−1까지의 정수만 허용. `-0`, 소수·지수 표기·NaN·Infinity 거절 |
| 금액 | 부호·선행 0·지수가 없는 최소단위 십진 문자열. 자산별 한도는 별도 타입 검사 |
| boolean / null | JSON의 `true`/`false`/`null`. null 허용 필드는 각 객체 스키마가 추가 제한 |
| 입력 제한 | UTF-8 262,144바이트 이하, 중첩 깊이 64 이하 |
| 중복 키 | JSON 해석 시 거절. 마지막 값으로 덮어쓰지 않음 |

입력의 공백이나 동등한 JSON 이스케이프는 받아들일 수 있다. 해시에는 입력 원문이 아니라 검증 후 정규 직렬화한 바이트를 사용한다. 객체 키가 `"10"`, `"2"`이면 `"10"`이 먼저다. JavaScript 객체의 숫자형 키 열거 순서에 기대어 `JSON.stringify`를 호출하면 이 순서가 바뀔 수 있으므로 구현은 키를 정렬한 뒤 직접 재귀 직렬화한다.

NFC 검사만 선언하면 런타임의 Unicode 버전 차이를 없앨 수 없다. Python UCD 15.0과 Node의 더 새로운 Unicode 표에서 U+105D2 + U+0307 같은 문자열의 허용 결과가 실제로 달랐다. CE1은 `fixtures/unicode15_assigned_ranges.json`에 고정한 배정 문자 범위를 두 구현이 먼저 검사한다. 미배정 문자·noncharacter·surrogate·15.0 이후 문자는 거절하며, 15.0의 제어문자·사적 사용 문자는 범위에 포함한다. 정규화기는 Unicode 15.0 이상을 요구한다. 이미 배정된 문자 집합에 대한 정규화 결과의 안정성은 [Unicode 정규화 안정성 정책](https://www.unicode.org/policies/stability_policy.html#Normalization)에 따른다. 허용 범위를 넓히려면 새 규격·시험값을 명시적으로 도입해야 한다.

## 기계 식별자와 배정 순서

일반 ID는 `[A-Za-z0-9][A-Za-z0-9:_./-]*`, 길이 1–128로 제한한다. 자산의 완전한 참조는 같은 문법에 길이 1–256을 사용한다. 표시용 공연명·사람 이름을 기계 ID로 사용하지 않는다. 현재 Commerce 스키마가 별도의 표시 필드를 새로 제공한다는 뜻은 아니다.

주문·주문행·재고·정책·할인 규칙·할인 부담자·결제 경로·제공자·행사·회차 ID에 이 검사를 적용한다. `proportional()`을 직접 호출할 때도 배정 대상 키를 검사한다. largest-remainder 동률은 이 ASCII ID 오름차순으로 푼다.

Python 코드 포인트 순서와 JavaScript UTF-16 순서의 차이는 U+E000과 U+10000에서 재현할 수 있다. 두 문자는 모두 기계 ID로 거절하므로 어느 행이 나머지 1 atom을 받는지 언어별로 갈리지 않는다. Unicode 표시 문자열은 값으로 유지되며 배정 키로 사용되지 않는다.

## 해시 영역과 버전

해시 원문은 다음 바이트의 연결이다.

```text
ASCII("KIX-CE1") || 0x00 || ASCII(domain) || 0x00 || CE1(value)
```

SHA-256 결과는 소문자 16진수 64자로 표시한다. domain은 일반 기계 ID 문법·길이를 따르며 NUL과 빈 문자열을 허용하지 않는다. 프레임의 고정 prefix와 구분자를 제거하거나 JSON 배열로 대신하지 않는다.

새 Commerce 스키마는 `kix:commerce:2`다. 자산 ID는 `asset-v2-`와 `digest('kix:asset:2', AssetSpec)`를 연결한다. 견적·결제 배정·행 반환안은 각각 `kix:quote:2`, `kix:payment-plan:2`, `kix:line-refund-proposal:2` 영역을 사용한다. 계산 결과를 다른 종류의 근거로 해석하지 않는다.

Commerce v2의 `orderVersion`은 양수 u32다. `expiresAt`과 `checkedAt`은 Unix 밀리초이며 이 계산 JSON 프로파일에서는 2^53−1 이하 정수로 제한한다. 새 실행 계약의 TimestampMs는 더 큰 signed-64 범위를 십진 문자열로 운반할 수 있지만 이를 계산 JSON 숫자로 손실 변환하지 않는다.

## 기존 데이터와의 경계

- 기존 `common.canonical`/`common.digest`, rc1 명령·장부·저장 영수증·S03·S05·유상 Sui fixture의 바이트와 해시는 바꾸지 않는다.
- Commerce v1 견적을 v2 입력으로 자동 승격하지 않는다. 원 요청을 명시적으로 새 스키마에 맞춰 다시 계산해야 하며, 새 해시는 기존 승인이나 실행의 승계를 뜻하지 않는다.
- 기존 `asset-...` ID와 `asset-v2-...` ID를 같은 저장 키로 취급하지 않는다. 영속 주문 도입 시 스키마·레지스트리·정책 버전을 함께 고정한다.
- 과거 `validation/2026-09-14-commerce/`는 S06 v1의 역사적 근거다. 새 검증 근거는 S06.1 별도 경로에 둔다.

## 언어 간 확인 범위

Python 구현은 `canonical_encoding.py`, TypeScript 구현과 비교 실행기는 `reference/v0.3-rc1/client/`에 둔다. `scripts/verify_canonical.py`가 고정된 입력·예상 바이트·해시, 잘못된 입력의 거절, 자산 ID, largest-remainder 배정과 실제 견적·결제 배정·반환안 결과를 비교한다.

```bash
python scripts/verify_canonical.py --report .local/verification/canonical.json
```

이 검사는 새 계약의 Python/TypeScript 구현을 대상으로 한다. 기존 Move·Circom이 CE1을 이미 사용한다거나 새 다중 자산 주문을 체인에서 실행했다는 근거가 아니다. 해당 모듈을 연결할 때 동일 규격의 바이트와 숫자 범위를 별도로 검사해야 한다.
