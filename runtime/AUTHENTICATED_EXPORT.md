# KIX authenticated export contract

PostgreSQL은 economic authority다. DuckDB/Polars/libcudf는 PostgreSQL에서 만들어진 **검증 가능한 export**를 소비하는 계산 엔진이며 경제적 정본이 아니다.

## 1. Full snapshot과 incremental CDC를 분리

SQL snapshot과 WAL LSN은 같은 개념이 아니다.

### Full snapshot export

- `REPEATABLE READ` 이상에서 하나의 일관된 MVCC snapshot을 고정한다.
- 여러 export worker가 같은 read point를 공유해야 하면 PostgreSQL exported snapshot/imported snapshot을 사용한다.
- export transaction이 끝나기 전에 모든 participating reader가 snapshot을 사용한다.
- WAL 위치는 provenance로 기록할 수 있지만 snapshot identity를 대체하지 않는다.

### Incremental export

- logical/WAL cursor를 기준으로 증분 범위를 정의한다.
- `start_lsn`/`end_lsn` 또는 동등한 durable cursor의 inclusive/exclusive 규칙을 schema에 고정한다.
- 중복/재시작 시 stable event identity로 deduplicate한다.

## 2. ExportManifestV1

각 dataset export는 최소 다음을 가진다.

```text
exportId
exportMode = FULL_SNAPSHOT | INCREMENTAL
sourceClusterId
sourceDatabaseId
sourceSchemaVersion
exportSchemaVersion

fullSnapshot:
  isolationLevel
  snapshotTextOrEquivalent
  snapshotFingerprint
  snapshotXmin
  snapshotXmax

incremental:
  cursorKind
  startCursor
  endCursor
  boundarySemantics

provenance:
  walLsnObservedAtStart
  walLsnObservedAtEnd
  createdAt

content:
  rowCount
  fileCount
  perFileHash[]
  manifestHash
  partitionManifest
```

FULL_SNAPSHOT은 snapshot 필드를 필수로 하고, INCREMENTAL은 cursor 필드를 필수로 한다. 둘을 하나의 `commitPosition` 필드로 뭉개지 않는다.

## 3. Integrity

- 모든 Parquet 파일은 content hash를 가진다.
- manifest hash는 schema/version, file list/hash, row count, snapshot/cursor provenance를 포함한다.
- consumer는 manifest 검증 실패 시 dataset을 사용하지 않는다.
- partial upload나 missing file을 정상 export로 승격하지 않는다.

## 4. Type mapping

경제적 필드는 JSON blob을 경유하지 않는다.

- KIX ID: fixed binary(16)
- Asset/hash: fixed binary(32)
- Fast64 money: signed i64 atoms + asset id + registry version
- Wide money: lossless 128-bit representation; 묵시적 narrowing 금지
- timestamp: unit/timezone 명시
- category: semantic vocabulary/version 명시

BIGINT/NUMERIC/timestamptz 등 PostgreSQL type에서 Arrow type으로 변환할 때 mapping version을 export schema에 고정한다.

## 5. DuckDB의 역할

DuckDB는 authenticated export에 대한 audit/forensic/reconciliation executor다.

```text
PostgreSQL = truth
ExportManifestV1 + Parquet = signed/hashed evidence snapshot
DuckDB = query engine over that evidence
```

DuckDB 결과가 PostgreSQL과 다르면 DuckDB를 새 truth로 보지 않는다. 먼저 snapshot/cursor boundary, export completeness, type mapping, query semantics를 조사한다.

## 6. Audit answerability

모든 audit 결과는 최소 다음을 역추적할 수 있어야 한다.

```text
query/reconciliation run
 -> exportId
 -> ExportManifestV1
 -> source snapshot or cursor range
 -> exact files/hashes
 -> source schema + export schema
```

따라서 '이 숫자가 원장의 어느 상태를 계산한 것인가'에 답할 수 있어야 한다.
