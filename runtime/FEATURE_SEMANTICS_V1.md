# KIX Feature Semantics v1

`KIX Feature IR v1`은 연산 이름만 공유하는 AST가 아니라, CPU Polars와 후속 native libcudf가 **같은 논리 결과**를 내도록 하는 의미론 계약과 함께 사용한다. upstream 엔진의 기본값은 KIX 의미론이 아니다.

## 1. Authority와 conformance

권위 순서는 다음과 같다.

```text
KIX Feature Semantics v1
        |
pure-Rust scalar/reference semantics
        |
   +----+------------------+
   |                       |
Polars Rust backend   native libcudf backend
   |
cudf-polars = drafting aid / benchmark / conformance participant only
```

Polars, libcudf, cudf-polars 어느 것도 의미론의 authority가 아니다. backend adapter는 upstream default를 사용하지 않고 KIX policy를 명시적으로 전달한다.

## 2. Null semantics

- Filter predicate가 `NULL`이면 행은 탈락한다.
- Join은 `nullEquality`를 IR에 명시한다. `EQUAL`과 `UNEQUAL`을 암묵 기본값으로 두지 않는다.
- GroupBy는 null key 포함 여부를 IR에 명시한다.
- Aggregate null value는 v1에서 `IGNORE`를 기본 계약으로 사용한다.
- Sort는 null 위치를 `FIRST` 또는 `LAST`로 명시한다.

## 3. Sort semantics

Sort는 다음을 모두 명시한다.

```text
columns
direction
nullOrder
stable
```

동일 키의 상대 순서를 보장해야 하는 계획은 `stable=true`여야 한다. upstream의 sort/stable_sort 선택은 backend adapter가 결정한다.

## 4. Aggregate semantics

v1 기본 규칙:

- `COUNT(empty) = 0`
- `SUM(empty/all-null) = NULL`
- `MIN(empty/all-null) = NULL`
- `MAX(empty/all-null) = NULL`
- `MEAN(empty/all-null) = NULL`
- 정수 overflow는 wrap/saturate하지 않고 `ERROR`
- 경제적 금액은 float aggregate로 계산하지 않는다.

## 5. F64 terminal-only

v1에서 F64는 **terminal model feature**로만 허용한다.

금지:

- F64 join key
- F64 group key
- F64 sort key
- F64 identity/equality key
- F64를 입력으로 하는 후속 arithmetic/query stage

F64 생성 경로는 두 개만 허용한다.

```text
MEAN(integer-like input)
  -> empty/all-null = NULL

DIVIDE_TO_F64(numerator, denominator)
  -> numerator NULL = NULL
  -> denominator NULL = NULL
  -> denominator 0 = NULL
```

그 외 F64 생성 경로는 v1에서 금지한다. 생성된 F64는 finite여야 하며 NaN 또는 +/-Inf가 발견되면 conformance/export failure다.

## 6. Money profiles

Protocol money는 계속 `u128 atoms`다. Feature fast lane은 **자산이 아니라 `(asset_id, registry_version)` 쌍**에 묶인다.

```text
MoneyProfileKey = (asset_id, registry_version)

Fast64 허용 조건:
  atoms <= executionMaxAtoms(registry_version) <= i64::MAX
```

두 조건을 export마다 모두 assert한다. registry version이 바뀌어 `executionMaxAtoms`가 커지면 과거 Fast64 판정을 새 버전에 자동 승계하지 않는다.

Rust 변환 경계는 `export_amount(AssetAmount)`이며 raw `u128` 변환 API를 제공하지 않는다. 프로파일의 key/hash는 private이고, amount의 asset id·registry version·registry hash가 모두 일치해야 범위 검사를 진행한다. `Fast64MoneyProfile::checked`는 전달된 주장값의 범위만 검사한다. 레지스트리의 서명/권한/내용 인증은 구현하지 않았으며 S07-D authenticated snapshot 경계에서 완료해야 한다.

`MoneyWide128`은 lossless export만 허용한다. v1 feature IR에서 `SUM/MEAN/Arithmetic(MoneyWide128)`은 unsupported이며 fail closed 한다. 묵시적 truncate/saturate/float 변환은 금지한다.

## 7. Category / Dictionary semantics

Arrow dictionary index는 물리 표현일 뿐 KIX semantic value가 아니다.

- KIX category는 `vocabularyId + semanticCode` 또는 동등한 안정 식별자를 사용한다.
- conformance는 dictionary buffer/index의 bit-exact equality가 아니라 **decoded logical value**를 비교한다.
- dictionary ordering 또는 index 재배치는 결과 불일치로 보지 않는다.

## 8. Conformance comparison

- integer, fixed ID, money atoms: exact equality
- category/dictionary: decoded logical equality
- terminal F64: finite-only + versioned tolerance policy
- row ordering: IR에서 stable/order가 요구된 경우에만 exact order 비교; order가 unspecified이면 canonical key sort 후 비교

최소 CI는 pure-Rust reference semantics와 Polars Rust backend를 항상 비교한다. native libcudf가 구현되면 동일 fixture를 추가하고, cudf-polars는 지원 가능한 연산에 한해 세 번째 비교 대상이 된다.

## 9. Upgrade gate

Polars/RAPIDS/libcudf 버전 업그레이드는 다음을 통과해야 한다.

1. Semantics v1 fixture 전체 통과
2. upstream default를 참조하는 adapter 코드가 없음
3. null/join/group/sort/aggregate edge fixture 통과
4. Fast64 registry-version fixture 통과
5. F64 NaN/Inf 생성 거절 fixture 통과
6. category dictionary 재인코딩 fixture 통과

Feature semantics를 바꾸려면 engine upgrade가 아니라 `KIX Feature Semantics v2`를 만든다.

## 10. Validator boundary — 2026-09-15 audit remediation

- `validate()`는 구조 및 추론 가능한 타입의 사전 검사다. source schema가 없으면 외부 컬럼의 존재/타입을 확정할 수 없으므로 실행 승인으로 사용하지 않는다.
- backend는 `validate_with_schemas(catalog)`가 반환한 `ValidatedFeaturePlan`을 받아야 한다. catalog는 plan 요청과 별도로 신뢰할 수 있는 export/catalog 경계에서 공급한다. 이 검증기는 catalog 인증 자체를 구현하지 않는다.
- source 및 join-right dataset id/schema version, 컬럼 존재, 표현식 입력/결과 타입, 출력 id 중복, aggregate 입력과 결과, join/group/sort key를 검사한다. F64가 있는 입력 schema는 거절한다.
- 모든 표현식은 같은 재귀 검사를 거친다. `DIVIDE_TO_F64`는 Project 루트에만 허용하며 두 피연산자는 같은 정수 타입이어야 한다. 내부 나눗셈과 필터의 F64 사용은 거절한다. 암묵적 I64/U64 coercion도 허용하지 않는다.
- Project 항목은 모두 stage 입력을 참조한다. 같은 Project의 앞선 alias는 입력이 아니며, 출력에 없는 원래 컬럼은 다음 stage에서 사라진다.
- GroupBy 출력은 key + aggregate다. COUNT는 U64이고 입력 생략은 COUNT(*)에만 허용한다. SUM은 같은 정수 타입을 보존하며 MEAN은 정수 입력에서 terminal F64를 만든다.
- Inner/Left join은 양쪽 컬럼을 출력하며 충돌하는 ColumnId는 거절한다. Semi/Anti join은 왼쪽 컬럼만 출력한다. 데이터셋 간 컬럼 id 할당/사전 projection으로 모호성을 제거해야 한다.
- F64 생성 후에는 Limit만 허용한다. plan은 최대 1,024 stages, 표현식은 깊이 64 및 총 100,000 nodes를 허용한다. wire 크기/파서 할당 제한은 별도의 구현 gate다.

이 변경은 검증기 구현이며 Polars compiler, 데이터 인증, 실제 CPU/GPU 실행 또는 conformance 완료를 의미하지 않는다.
