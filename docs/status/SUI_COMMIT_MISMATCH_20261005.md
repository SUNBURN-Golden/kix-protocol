# Sui 릴리스 메타데이터와 framework pin 대조

확인일: 2026-10-05. 노드: `sui-commit-mismatch-note` (A1, 별도 아키텍처 결정 없음).
입력 정본: [.aiops/program.json](../../.aiops/program.json), plan/base
`0b8b6b484c1b5d49b7cb285e780481061c2b16c7`.
현재 문서의 설명만 보충한다. 역사 조사 원문·결정 기록·참조 구현·태그·pin은 보존한다.

## 두 값이 나타나는 이유

공식 GitHub 릴리스에는 **릴리스 메타데이터의 `target_commitish`**와 **실제 Git 태그가
가리키는 커밋**이라는 서로 다른 값이 있다. 이번 조회에서 다음을 확인했다.

| 근거 | 확인한 값 | 이 저장소에서의 역할 |
|---|---|---|
| `releases/tags/mainnet-v1.79.1`의 `target_commitish` | `58386edc269ef88ff0f40ab0a9d50e87cba80ca8` | 보존 조사와 개발계획 §9.1의 조사 소스 값과 일치 |
| `git/ref/tags/mainnet-v1.79.1`의 `object.sha` (`type=commit`), `git ls-remote` | `808640d9b49aecf29d8e6f46033c15eca236efa7` | 실제 태그 해석. `reference/v0.3-rc1/sui/Move.toml:6`의 framework pin과 일치 |

릴리스의 `published_at`은 `2026-09-09T17:18:01Z`다. `target_commitish` 필드를 태그의
대상 SHA로 대신 읽으면 조사 기준과 framework pin이 혼동된다. 태그의 실제 대상은
태그 ref로 확인해야 한다. 현재 메타데이터의 일치는 당시 조사자가 그 필드를 사용했다는
직접 증거는 아니며, 당시의 조회 절차나 태그 이동 이력을 이번 조회만으로 확정하지 않는다.

두 SHA는 별개 커밋이다. 커밋 API에서 `58386edc…`는 GraphQL 구독자 기본 한도를
줄인 변경 `#27896`이고, `808640d9…`는 1.79 릴리스 브랜치의 Docker 이미지 backport
`#27917`이다. compare API는 `status=diverged`, `ahead_by=50`, `behind_by=4`,
공통 조상 `a4158b3fb495aa12507ceb44bf128bfbe7dba2ac`를 반환했다.
따라서 두 SHA나 전체 소스를 동등하다고 부르지 않는다.

KIX의 Git 이력에서도 `2658a43aefa792ff783457188814f8598a62f5b0`이 참조 `Move.toml`에
`808640d9…` pin을 추가했다. 9월 29일 [범위 결정 §6.3](../decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md)과
[권리 청사진](../blueprints/rights-scale-v1/README.md)의 태그 관측과 이번 태그 조회는 일치한다.
9월 17일 [조사 게시 기록](../research/SUI_EQUIVOCATION_IMPORT.md) 및 보존 원문의
`58386edc…`는 당시 조사 기준으로 남긴다. 이 보충은 framework 교체나 과거 조사 재작성의 승인이 아니다.

## 확인한 파일의 범위

contents API를 두 SHA 각각에 대해 조회했다. 아래 두 파일은 같은 Git blob이다.

| Sui 경로 | 양쪽 SHA에서 확인한 blob |
|---|---|
| `crates/sui-core/src/execution_cache/object_locks.rs` | `8fff6c191c690e803a1bb901a0cf7b5765167985` |
| `crates/sui-protocol-config/src/snapshots/sui_protocol_config__test__Mainnet_version_136.snap` | `a45b246082453cb739e51bb0577bed646e4d1935` |

첫 blob은 조사 게시 기록의 값과도 일치한다. 이는 해당 잠금 소스와 스냅샷 바이트의
동일성을 확인한 것이다. 전체 framework·모든 조사 링크·빌드·실행 의미의 동등성,
현재 RPC binary/protocol/feature, 체인 장애·성능·운영 준비도는 확인하지 않았다.
Sui VM 시험·체인 호출·배포·wallet 작업은 이 문서 노드의 범위가 아니다.

## 증거 명령

아래는 이번 조사에서 실행한 조회 명령이다. 공개 GitHub 소스만 읽으며 체인 RPC를 호출하지 않는다.
API 응답은 전체 transcript 대신 위의 관련 필드와 blob을 기록했다.

```sh
git show 0b8b6b484c1b5d49b7cb285e780481061c2b16c7:reference/v0.3-rc1/sui/Move.toml
git log --all --oneline -- reference/v0.3-rc1/sui/Move.toml sui/Move.toml
git show 2658a43 -- reference/v0.3-rc1/sui/Move.toml
git ls-remote https://github.com/MystenLabs/sui.git refs/tags/mainnet-v1.79.1
curl -fsSL https://api.github.com/repos/MystenLabs/sui/releases/tags/mainnet-v1.79.1
curl -fsSL https://api.github.com/repos/MystenLabs/sui/git/ref/tags/mainnet-v1.79.1
curl -fsSL https://api.github.com/repos/MystenLabs/sui/commits/58386edc269ef88ff0f40ab0a9d50e87cba80ca8
curl -fsSL https://api.github.com/repos/MystenLabs/sui/commits/808640d9b49aecf29d8e6f46033c15eca236efa7
curl -fsSL https://api.github.com/repos/MystenLabs/sui/compare/808640d9b49aecf29d8e6f46033c15eca236efa7...58386edc269ef88ff0f40ab0a9d50e87cba80ca8
```

파일 blob 조회는 아래 명령을 두 `rev` 각각에 대해 실행한 것과 같다.

```sh
curl -fsSL 'https://api.github.com/repos/MystenLabs/sui/contents/crates/sui-core/src/execution_cache/object_locks.rs?ref=58386edc269ef88ff0f40ab0a9d50e87cba80ca8'
curl -fsSL 'https://api.github.com/repos/MystenLabs/sui/contents/crates/sui-core/src/execution_cache/object_locks.rs?ref=808640d9b49aecf29d8e6f46033c15eca236efa7'
curl -fsSL 'https://api.github.com/repos/MystenLabs/sui/contents/crates/sui-protocol-config/src/snapshots/sui_protocol_config__test__Mainnet_version_136.snap?ref=58386edc269ef88ff0f40ab0a9d50e87cba80ca8'
curl -fsSL 'https://api.github.com/repos/MystenLabs/sui/contents/crates/sui-protocol-config/src/snapshots/sui_protocol_config__test__Mainnet_version_136.snap?ref=808640d9b49aecf29d8e6f46033c15eca236efa7'
```

## 인계와 검증 경계

기존 coverage는 pin·조사 blob·태그 관측을 각각 충분히 기록했지만 두 값의 관계는
부분 coverage였다. 이번 메타데이터/태그/파일 대조가 그 설명 공백을 채운다.
제품 코드가 바뀌지 않아 새 kernel/Move 회귀시험은 추가하지 않는다.

로컬에서 `python3 scripts/check_openapi_contract.py` 및 `--self-test`,
`python3 scripts/check_integration_gate_openapi.py` 및 `--self-test`는 모두 exit 0이었다.
`git diff --check`도 exit 0이었다. 추가로 실행을 시도한
`python3 scripts/verify_runtime_architecture.py`와 `python3 scripts/test_runtime_architecture.py`는
Python 3.10에 `tomllib`가 없어 import 단계에서 exit 1이었다. PATH에서 Python 3.11~3.13과
Cargo를 찾지 못했다. 이를 architecture·Rust 시험 PASS로 세지 않는다. 해당 전체 검증은
필요할 때 CI의 고정 Python/Rust 환경에서 확인해야 하며, 검사기·CI·정책은 수정하지 않는다.

비작성자 검토, 실제 게시 head의 KTX kernel verification 및 KIX protocol verification,
필요한 감사와 최종 supervision은 후속 Mac pipeline의 별도 게이트다.
문서 전용 분류에 따른 무거운 검사 생략은 전체 protocol/kernel 시험 통과가 아니다.
이 구현 인계는 ready·병합·release·legacy DONE·프로그램 완료 증거가 아니다.
