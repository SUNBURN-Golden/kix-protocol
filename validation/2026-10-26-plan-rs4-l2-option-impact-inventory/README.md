# RS-4 L2 option-impact inventory — validation

## Basis and scope

Date: 2026-10-26. Task/node: `plan-plan-rs4-l2-option-impact-inventory`.
Task document: supervisor-supplied node specification and read-only design plan;
there is no corresponding `docs/tasks/` file or issue. This is not ASTRA program
mode. The node is not in `.aiops/program.json`; metadata from the supplied input:
`depends_on: []`, audit floor A2, `astra_gate: None`, `user_merge: False`.
Planner source: run 1792980988 (`/workspace/kix-run/logs/planner_1792980988`, as
supplied, not executed or read as repository evidence).

Branch: `agent/kix-plan-plan-rs4-l2-option-impact-inventory`.
Observed cached `origin/main`, base and starting HEAD:
`fc11cdf0150e54ed38bb363f2ded7238c48c6e53`.
No cached base delta. `git fetch origin main`: **NOT_RUN**, because the
supervisor explicitly prohibits every GitHub/network action. Remote freshness
is unverified. No rebase, merge, branch operation, commit or publication occurs.

Delivery: [RS4_L2_DECISION_IMPACT_INVENTORY.md](../../docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md),
linked by [docs/README.md](../../docs/README.md). The source decision is quoted
only through [the October 22 ledger](../../docs/status/OPEN_USER_DECISIONS_20261022.md)
line 64. The external decision pointer is not opened or represented as a repository
link. Draft PR #191's FAILED_MEASUREMENT record is **node input only**; its content
and numbers were not fetched, inspected or copied.

The inventory follows the presentation of
[the October 26 addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md).
It selects no option, supplies no measurement and changes no node state.

## Existing coverage mapping (AGENTS.md §7)

These classifications describe coverage available before this documentation
change. No new tests were added; the new evidence is the inventory and this
reproducibility record.

| Acceptance requirement | Existing coverage classification | Reused evidence / gap addressed |
|---|---|---|
| 1: option sections, clauses, row IDs, path/denominator facts and downstream fences | Partially covered | Ledger row 2, both RS maps, `load_plan.py`, `measurement_gap.py` and program dependency fields supply the facts. Their per-option collation was not covered; the inventory supplies it. `test_load_plan.py::TestStructure`, `TestSlotAccounting`, `TestPrivatePath`, `TestDelegatedPath` already cover the L1 generator shape. |
| 2: no decision/value, original owners and UNDETERMINED | Partially covered | Ledger owner cell and `host_conditions.py:21–22` supply verbatim owner text; `test_host_conditions.py` covers the recorder's lack of verdicts. New documentary assertions are checked manually and by the limited source/quote sanity command V1 below. This is not a general proof of absence of recommendations or policy values. |
| 3: index and four checkers plain/self-test | Sufficiently covered by existing tooling | `check_docs_index.py`, `check_status_register.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`; reused without edits. |
| 4: derivation and command record | Not covered for this node | This README adds G1–G10 outputs and actual local command results. |
| 5: restricted paths unchanged and locks preserved | Sufficiently covered by existing Git/blob checks | Before/after locked hashes, protected-scope diff, actual-byte Git blob comparisons and complete tracked/untracked changed-path inventory; V2 below. |

`test_measurement_gap.py::TestMeasurementGap.test_end_state_check_names` already
asserts the end-state keys; `test_complete_record_is_fully_measured` and
`test_truncated_record_shows_l2_gap_structure` exercise full/truncated synthetic
coverage. `test_summarize_load.py::TestSummarizeRules.test_a_failed_path_is_reported_separately`
is reused as the predicate map's separation evidence (the symbol is validated by
the existing checker). These are source-informed offline fixtures, not independent
L2 measurement, clean-room evidence or acceptance closure.

## Fact derivation

Every line number in the inventory is relative to the unchanged source at the
cached base above, not a promise about later revisions.

| Inventory fact | How derived |
|---|---|
| §0 provenance | Supervisor input plus B1; external planner and PR metadata attributed only to the input. |
| §1A acceptance, title and metadata; all four repeated clause quotes | G1; V1 compares the objective and acceptance strings with the decoded program spec and requires one shared plus four per-option occurrences. |
| §1B and every option's owner; load UNDETERMINED | G8 ledger row 2 and G9 recorder docstring; exact original owner sentence is retained. |
| §1C predicate selection | G2, restricted to §2 data rows by V1: RS-C14, RR-2, RR-5, RR-6. Missing/open cells copied verbatim from the map, with basis lines 42/47/50/51. |
| §1C no IM match; IM-10 near-miss | G3 and V1 §2 selection: no row contains the RS-4/load selection terms and no row is MEASUREMENT_ONLY. Counts line 66 has MEASUREMENT_ONLY=0; IM-10's plain word “measurement” is not a match. |
| §1D version, seats, page, bundle and payment shards | G4 and G6; model line 48 and Move line 73 agree on the existing 1024-slot fixture. |
| §1D requested/default settings, planned/predicate/probe counts, phases and check keys | G6 expands defaults only in memory. G10 exposes the exact definitions and probe sites. Top-level planned steps are not successful transactions; probes count once and also belong to the predicate set. V1 recomputes the table. |
| §1C row-to-path relationships | G4 and source read of `load_plan.py:315–430`: RR-2(b) comment at 389, RR-6 at 364, `shield` append steps at 341–362; RS-C14's map cells name all three paths. |
| §1D′ undefined L2 denominators | G4, G5, G10 and full generator/CLI source read. Version/SEATS/builders define L1; the CLI has no show-size option. G5 is a pre-edit whole-tree lexical locator followed by source excerpts, not a claim that a lexical absence alone proves no workload. Header overrides do not replace builders' module constant. No L2 expansion or extrapolation is attempted. |
| §1D′ depth/phase-1 constraints and IM-11 | G5: blueprint lines 161/388, historical RS-2 record lines 127/274, IM-11 line 45. Cache availability is attributed to the historical record, not measured now. IM-11 is capacity context, not a member of the measurement-row selection. |
| §1E fences | G7 direct dependency arrays; direct/transitive relationships are derived from these edges. No external node state was queried. |
| §1F tooling limits | G9 and `measurement_gap.py` / `test_measurement_gap.py` module docstrings; narrow offline tests below. Their synthetic shapes do not import the external FAILED_MEASUREMENT record. |
| §§2–5 options / no-data consequences | G8 option text verbatim. O1/O2 exclude no path in their wording; O3a's “only” excludes other paths and public remainder; O3b's “first” sets an order without defining final public scope. Prefix cut and final scope stay UNDETERMINED — Astra (workload). No predicate/probe position is guessed for an unknown prefix. |
| §6 table and §7 limits | Collation of the preceding facts and explicit node boundaries. No new empirical assertion or policy number. |

G1–G10 below are actual commands run before the new documents were created,
with `PYTHONDONTWRITEBYTECODE=1` in their environment. Use the same environment
when reproducing. G5's whole-tree locator will also find these new documents if
rerun afterward; its recorded list is the pre-edit tree, and fact-bearing source
files remain unchanged. Raw output order from `rg` is not semantically relevant.

### G1

Command (exit 0):

```sh
rg -n -A8 '"id": "rs-4-l2"' .aiops/program.json
```

Raw output:

````text
469:      "id": "rs-4-l2",
470-      "title": "RS-4 L2: staged load validation at 16,384 slots",
471-      "depends_on": [
472-        "rs-4-l1"
473-      ],
474-      "spec": "Objective: load validation at 16,384 slots. Label results exploration data; no SLOs; localnet on the builder machine. A measurement environment beyond it, or any spend, is DECISION_REQUIRED. Report public, private and delegated paths separately (docs/blueprints/rights-scale-v1/README.md lines ~497-507, 374-420).\nAcceptance: scripts, raw results, report; checks green.\nCommon rules: follow AGENTS.md (program mode) and docs/decisions/PROGRAM_ROADMAP_20260930.md. Keep the two locked kernel blobs (AGENTS.md §4) and reference/v0.3-rc1/** unchanged unless this node says otherwise. The locks and unlock conditions in docs/decisions/PROGRAM_DECISIONS_20260928.md §5 still hold: no real funds, real PG/bank/KYC calls, public endpoints, Sui testnet or mainnet, R2 or own replication/consensus/storage engine, and no new coin/TIX module (the only exception is the localnet package of node tl-2, and only after the User merges tl-coin-lock-adr following the Astra re-ruling). Do not invent SLOs or product policy values: product policy values and new protocol commands go to DECISION_REQUIRED · Astra; values that need legal, tax, accounting or provider answers stay UNDETERMINED with the owner named. Do not edit CI to make the task pass. Evidence per AGENTS.md §14; protocol and kernel checks green at the exact head.",
475-      "audit_floor": "A2",
476-      "astra_auto_merge": true
477-    },
````

### G2

Command (exit 0):

```sh
rg -n 'RS-4|rs-4|load_plan|summarize_load|MEASUREMENT_ONLY' docs/status/RS_PREDICATE_EVIDENCE_MAP.md
```

Raw output:

````text
10:- Evidence read: `reference/rights_scale/sui/tests/*.move`, `reference/rights_scale/test_*.py`, `runtime/crates/kix-delegated-exec/tests/*.rs`, `reference/rights_scale/client/*.mjs`, `reference/rights_scale/vectors/*.json` and the RS-1, RS-2, RS-3a and RS-4 validation records. Test bodies were read before a status was kept; where the body did not establish the whole predicate sentence the row is `PARTIAL`.
21:| `MEASUREMENT_ONLY` | The profile hands the remaining obligation to RS-4 measurement; the structure half is cited and no figure is claimed. |
42:| RS-C14 | RS-C14-T1, RS-C14-T2, RS-C14-T3 | none | public: `reference/rights_scale/test_load_plan.py::test_public`; private: `reference/rights_scale/test_load_plan.py::test_private`; delegated: `reference/rights_scale/test_load_plan.py::test_delegated`, `reference/rights_scale/test_load_plan.py::test_three_paths_present`; separation: `reference/rights_scale/test_summarize_load.py::test_a_failed_path_is_reported_separately` | delegated: `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs::delegation_moves_the_execution_fence_to_the_delegate` | public: `reference/rights_scale/vectors/public_path.json::l1_1024_public_path`; private: `reference/rights_scale/vectors/private_path.json::l1_1024_private_path`; delegated: `reference/rights_scale/vectors/public_path.json::rs3a_delegation_cut`; load record: `validation/2026-10-15-rs-4-l1-load/README.md::delegated` | PARTIAL | The separation of per-path results is now asserted on a synthetic run report (a corrupted public snapshot fails only the public row); no real run report is checked, the delegated leg is in-memory only, and private resale, refund, reissue and key rotation are unimplemented and only stated as such. | RS-1, RS-2, RS-3a, RS-3b |
47:| RR-2 | RR-2-T1 | `reference/rights_scale/sui/tests/private_path_tests.move::issue_and_refund_do_not_change_the_revocation_root_but_revoke_does`, `reference/rights_scale/sui/tests/private_path_tests.move::a_revocation_cannot_lower_the_recorded_generation`, `reference/rights_scale/sui/tests/private_path_tests.move::a_revocation_built_on_a_stale_root_is_rejected`, `reference/rights_scale/sui/tests/root_math_tests.move::sparse_update_roots_match_circomlibjs` | `reference/rights_scale/test_private_model.py::test_issue_and_refund_do_not_move_the_revocation_root`, `reference/rights_scale/test_private_model.py::test_both_rules_give_the_same_verdict_for_every_note_after_every_operation` | none | `validation/2026-10-14-rs-2-private-path/README.md::RR-2 (+equivalence)` | PARTIAL | Concurrent revocations on one root are tested only as a sequential stale-witness case, and the collision rate is unmeasured. | RS-2; RS-4; Astra |
50:| RR-5 | RR-5-T1 | `reference/rights_scale/sui/tests/zk_staging_tests.move::claim_zk_fixes_the_domain_and_creates_one_tree_one_revocation_state_and_the_shard_families`, `reference/rights_scale/sui/tests/private_path_tests.move::shield_with_another_shows_tree_aborts` | none | none | `validation/2026-10-14-rs-2-private-path/README.md::1 note tree` | MEASUREMENT_ONLY | Contention of `shield` on the one note tree is unmeasured. | RS-2가 구조, RS-4가 측정 |
51:| RR-6 | RR-6-T1 | `reference/rights_scale/sui/tests/zk_staging_tests.move::claim_zk_fixes_the_domain_and_creates_one_tree_one_revocation_state_and_the_shard_families`, `reference/rights_scale/sui/tests/private_path_tests.move::another_shows_revocation_state_is_rejected` | none | none | `validation/2026-10-14-rs-2-private-path/README.md::1 revocation root per show` | MEASUREMENT_ONLY | The share of in-flight proofs one revoke invalidates and the re-proof delay are unmeasured. | RS-2가 구조, RS-4가 측정 |
53:Counts: COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2
````

### G3

Command (exit 0):

```sh
rg -n 'RS-4|rs-4|load_plan|summarize_load|MEASUREMENT_ONLY|measurement' docs/status/RS_IM_EVIDENCE_MAP.md
```

Raw output:

````text
22:| `MEASUREMENT_ONLY` | The profile hands the remaining obligation to RS-4 measurement. No row has this status at this base. |
29:Owner cell: required for `PARTIAL`, `NOT_COVERED` and `MEASUREMENT_ONLY` rows. The impact table has no owner column, so an owner is written in the profile's own words: a node the policy sentence names (IM-16 and IM-27 RS-2, IM-26 `RS-3b와 Track K v5`), the owner cell of the RR or section 4 row the sentence points to (IM-10 section 9, IM-29 section 6, IM-17 and IM-11 section 4 ceiling 5), or the reserved literal `none stated in profile`, which the record lists as a class B item.
44:| IM-10 | 변경 | The root is a stored incremental value; the full recomputation on every call is not brought into the extended profile; the acceptance rule is section 9. | `reference/rights_scale/sui/tests/root_math_tests.move::depth_ten_incremental_roots_match_circomlibjs`, `reference/rights_scale/sui/tests/root_math_tests.move::history_keeps_exactly_the_last_k_roots`, `reference/rights_scale/sui/tests/private_path_tests.move::shield_appends_in_insertion_order_and_the_page_is_not_written` | `reference/rights_scale/test_private_model.py::test_the_window_is_the_last_k_roots` | none | none | none | PARTIAL | The stored incremental root and the acceptance window are exercised; no test or measurement asserts that a call never recomputes the whole tree, which is an absence claim about the implementation. | RS-2 |
66:Counts: COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2
````

### G4

Command (exit 0):

```sh
rg -n '^(VERSION|SEATS|PAGE_SIZE|MAX_BUNDLE|PUBLIC_SHARDS|PRIVATE_SHARDS|DELEGATED_SHARDS)|RR-2|RR-6|DEFAULT_SETTINGS' reference/rights_scale/load_plan.py
rg -n LOCALNET_SHOW_SLOTS reference/rights_scale/model.py reference/rights_scale/sui/sources/rights_scale.move
```

Raw output:

````text
41:VERSION = 'kix-rs4-l1-load-v1'
43:SEATS = model.LOCALNET_SHOW_SLOTS        # 1024; L1 stage size (fixture, not policy)
44:PAGE_SIZE = model.LOCALNET_PAGE_SLOTS    # 64
45:MAX_BUNDLE = model.MAX_BUNDLE_CHAIN      # 8
47:PUBLIC_SHARDS = model.LOCALNET_PAYMENT_SHARDS   # 4
48:PRIVATE_SHARDS = 1
49:DELEGATED_SHARDS = model.LOCALNET_PAYMENT_SHARDS
364:    # RR-6: proofs generated before a revocation are invalid after it.
389:    # Two revocations built on the same root: exactly one lands (RR-2(b)).
523:DEFAULT_SETTINGS = {
546:    cfg = dict(DEFAULT_SETTINGS)
reference/rights_scale/model.py:48:LOCALNET_SHOW_SLOTS = 1024
reference/rights_scale/sui/sources/rights_scale.move:68:// `LOCALNET_SHOW_SLOTS` is the owner's "P" (slots per show) and `LOCALNET_PAGE_SLOTS`
reference/rights_scale/sui/sources/rights_scale.move:73:const LOCALNET_SHOW_SLOTS: u64 = 1024;
reference/rights_scale/sui/sources/rights_scale.move:1077:public fun localnet_show_slots(): u64 { LOCALNET_SHOW_SLOTS }
````

### G5

Command (exit 0):

```sh
rg -l --hidden -g '!.git' -g '!package-lock.json' '16,384|16384' .
rg -n '16,384|16384|power 15' reference/rights_scale/load_plan.py docs/blueprints/rights-scale-v1/README.md validation/2026-10-14-rs-2-private-path/README.md
rg -n '^\| IM-11 \|' docs/status/RS_IM_EVIDENCE_MAP.md
```

Raw output:

````text
./.aiops/program.json
./validation/2026-10-14-rs-2-private-path/README.md
./validation/2026-10-14-rs-2-private-path/constraints-by-depth.json
./docs/decisions/PROGRAM_ROADMAP_20260930.md
./docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md
./docs/status/OPEN_USER_DECISIONS_20261022.md
./docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md
./docs/status/CURRENT_CAPABILITY_REGISTER.md
./docs/blueprints/rights-scale-v1/README.md
./reference/rights_scale/test_host_conditions.py
./docs/contracts/RIGHTS_SCALE_PROFILE.md
./docs/aiops/KIX_PROGRAM_DRAFT.json
./docs/aiops/PROGRAM_EXPANSION_20261002_KO.md
validation/2026-10-14-rs-2-private-path/README.md:125:| 14 | 16,384 | 916 | 17,603 | **15** |
validation/2026-10-14-rs-2-private-path/README.md:127:**Decision for RS-2: depth 10, power 14.** The cached phase-1 file (power 14, produced by the protocol job) is reusable. A 16,384-slot show (depth 14) would need power 15 and a different phase-1 file; that is an input for RS-4/RS-5, not a decision here. Spend grows about 1,041 constraints per level.
validation/2026-10-14-rs-2-private-path/README.md:274:- A depth-14 profile (16,384 slots) needs ptau power 15, which the shared cache does not hold.
docs/blueprints/rights-scale-v1/README.md:51:5. 검증 규모는 16 → 1,024 → 16,384 → 65,536(+복수 공연 동시) 순이다. 이 숫자는 **시험 규모 제안**이며 달성 성능, 승인된 TPS·p99, 출시 수용량, 최종 상한이 아니다(§7).
docs/blueprints/rights-scale-v1/README.md:103:| IM-16 | `client/setup-zk.mjs:18`(관측 main). `13134e4`에서는 `:24`(캐시를 쓰지 않는 분기 안) | `powersoftau new bn128 14` — 2^14 = 16,384 제약까지의 fixture ceremony. `13134e4`에서는 `KIX_ZK_PHASE1_PTAU`로 이전 1단계 파일을 재사용할 수 있고(`:20`) 재사용 여부와 ptau SHA-256을 manifest의 `phase1`에 기록한다(`:28`). 기록된 제약 수(깊이 4): mint 비선형 393·선형 513, spend 비선형 3,629·선형 4,167 (`validation/2026-09-11/circuit-build.log`) | 필요. 깊이별 제약 수를 다시 재고 ceremony 파워를 재결정 | 회로별 phase-2 기여 검증. 단일 당사자 fixture는 운영 ceremony가 아님(`zk/artifacts/README.md`) |
docs/blueprints/rights-scale-v1/README.md:109:snarkjs v0.7.5 README(`snarkjs/README.md:93`)는 `powersoftau new`의 둘째 인자를 "ceremony가 받을 수 있는 최대 제약 수의 2의 거듭제곱 지수"로 설명한다(`14` → 16,384). 저장소 `client/package.json`이 같은 버전 `0.7.5`를 고정한다.
docs/blueprints/rights-scale-v1/README.md:158:- **객체 크기(IM-03).** 고정 스냅샷의 `max_move_object_size`는 256,000바이트다(§3.1). `Show`에 슬롯당 들어가는 바이트는 `generations` 8 + `occupied` 1 = 9이고, 유료 발급이면 결제 참조 33(길이 접두 1 + 32)이 더해지며, 비공개 경로를 끝까지 쓰면 노트·nullifier·challenge가 각 32바이트씩 더해진다. 그래서 **직접 발급만**이면 슬롯당 9바이트로 N ≤ 28,444이고(16,384는 147,456바이트로 들어가지만 65,536은 589,824바이트로 넘친다), **유료 발급이 있으면** 42바이트로 N ≤ 6,095이며(16,384는 688,128바이트라 넘친다), **비공개 경로까지 끝까지 쓰면** 138바이트로 **N ≤ 1,855**다. 65,536은 어느 경우에도 단일 객체에 들어가지 않는다. 고정 필드와 2차 결제 참조는 무시한 값이라 실제 한도는 더 낮다.
docs/blueprints/rights-scale-v1/README.md:159:- **루트 재계산(IM-10).** `consume_private` 한 번에 루트 재계산만으로 Poseidon 호출이 필요하다: 현행 46회(폐기 31 + 노트 15. context 해시 1회를 더하면 47회), 일반식 3N−2. N=1,024이면 3,070회, 16,384이면 49,150회, 65,536이면 196,606회. 매 검표마다 O(N)이다. 호출당 비용은 **[미확인]**이며 측정 항목이다.
docs/blueprints/rights-scale-v1/README.md:161:- **회로(IM-14~IM-17).** 깊이는 ⌈log2 N⌉: 1,024 → 10, 16,384 → 14, 65,536 → 16. 제약 수 증가와 ceremony 파워는 **[미확인]**이다.
docs/blueprints/rights-scale-v1/README.md:232:1. ①은 산술로 막힌다(§2.7). 직접 발급만이면 N ≤ 28,444이지만, 유료 발급이 있으면 N ≤ 6,095, 비공개 경로까지 끝까지 쓰면 N ≤ 1,855다. 65,536은 어느 경우에도 들어가지 않고 16,384는 유료 발급이 있으면 들어가지 않는다. 1,024는 최악에서도 141,312바이트라 들어가므로, ①은 **1,024 단계의 대조군**으로만 유용하다.
docs/blueprints/rights-scale-v1/README.md:283:- **생성 단계화.** `max_num_new_move_object_ids`가 2048이다. 지정석별(P=1) 65,536개는 이 한도만으로 최소 32번의 생성 트랜잭션이 필요하고(16,384개는 8번), P=256이면 페이지 256개다. 페이지마다 `derived_object`의 `Claimed` 동적 필드도 새 ID를 쓴다면 한 트랜잭션에 만들 수 있는 페이지는 이 수의 절반 근처로 줄어든다(계수는 **[미확인]**, 측정으로 정한다). 생성이 끝나 봉인되기 전에는 `open`이 거짓이어야 한다.
docs/blueprints/rights-scale-v1/README.md:388:| L2 | 16,384 | 중간 규모 | ①은 결제 참조가 슬롯마다 있으면(42바이트/슬롯, 688,128바이트) 산술상 불가다. 직접 발급만이면 147,456바이트로 들어가지만 그 경우는 유료 판매 경로가 없는 공연이다. 잠금 v4 커널의 `MAX_SEATS = 4,096` 때문에 지정석 단일 인벤토리 위임은 불가하다. 페이지 분할·GA·새 버전 crate 중 무엇을 쓸지는 RS-3b 결정 |
docs/blueprints/rights-scale-v1/README.md:395:- 1,023 / 1,024 / 1,025(깊이 10의 잎 한도). 확장 단계에서는 16,383/16,384/16,385, 65,535/65,536/65,537도 같은 방식으로 본다.
docs/blueprints/rights-scale-v1/README.md:589:for n in (1024, 16384, 65536):
docs/blueprints/rights-scale-v1/README.md:591:print(-(-65536 // 2048), -(-16384 // 2048))                          # min creation txs for per-slot objects: 32 8
docs/blueprints/rights-scale-v1/README.md:594:출력: `28444 6095 1855`, `1024 9216 43008 141312 3070`, `16384 147456 688128 2260992 49150`, `65536 589824 2752512 9043968 196606`, `32 8`.
45:| IM-11 | 변경 | Note capacity follows ceiling 5 of section 4; after SHIELDED, public transfer, refund and check-in are impossible. | `reference/rights_scale/sui/tests/private_path_tests.move::a_shielded_ticket_cannot_be_offered`, `reference/rights_scale/sui/tests/private_path_tests.move::a_shielded_ticket_cannot_authorize_a_public_admission`, `reference/rights_scale/sui/tests/private_path_tests.move::a_shielded_ticket_cannot_be_refunded`, `reference/rights_scale/sui/tests/root_math_tests.move::the_leaf_after_capacity_aborts`, `reference/rights_scale/sui/tests/zk_staging_tests.move::claim_zk_accepts_exactly_the_tree_capacity`, `reference/rights_scale/sui/tests/zk_staging_tests.move::claim_zk_rejects_a_show_larger_than_the_tree` | `reference/rights_scale/test_private_model.py::test_notes_never_exceed_the_slots`, `reference/rights_scale/test_private_model.py::test_a_show_larger_than_the_tree_cannot_enable_the_private_path` | none | `validation/2026-10-14-rs-2-private-path/README.md::shield_conserves_the_right_count` | none | COVERED_LOCALNET | none; K, the root-history length of the same ceiling, is a manifest field whose operational value the profile leaves UNDETERMINED, and this map chooses none. | K: DECISION_REQUIRED · Astra |
````

### G6

Command (exit 0):

```sh
python3 - <<'FACTS'
import sys, collections
sys.path.insert(0,'reference/rights_scale')
import load_plan as L, measurement_gap as M
d=L.assign_phases(L.expand())
print('version:', d['version'])
print('requested:', d['requested'])
print('settings:', d['settings'])
for n,s in d['paths'].items():
 print(n, 'steps:',len(s),'predicates:',sum(map(M._is_predicate,s)))
 print('probes:',[(x['name'],len(x['of'])) for x in s if x['op']=='parallel'])
 print('phases:',dict(collections.Counter(x['phase'] for x in s)))
 print('end_state_checks:',M._end_state_checks(d['expected'][n]))
FACTS
```

Raw output:

````text
version: kix-rs4-l1-load-v1
requested: {'seats_per_show': 1024, 'shield_count': 1024, 'consume_count': 32, 'invalidation_count': 8}
settings: {'seed': 20261014, 'show': {'seated': 1024, 'ga': 0, 'page_size': 64}, 'shards': {'public': 4, 'private': 1, 'delegated': 4}, 'zk': {'depth': 10, 'root_history_k': 4, 'nullifier_shards': 4, 'challenge_shards': 4}, 'closed_loop': True, 'arrival_rate': 0, 'shield_count': 1024, 'consume_count': 32, 'invalidation_count': 8, 'transfers': 8, 'admissions': 8, 'refunds': 16, 'revokes': 16, 'reissues': 2, 'reservations': 2, 'concurrency_probes': [{'path': 'public', 'name': 'same_page_issues', 'k': 2, 'expect': 'any'}, {'path': 'public', 'name': 'duplicate_slot_race', 'k': 2, 'expect': 'one_wins'}, {'path': 'public', 'name': 'same_shard_attests', 'k': 2, 'expect': 'any'}, {'path': 'public', 'name': 'cross_shard_attests', 'k': 2, 'expect': 'any'}, {'path': 'public', 'name': 'bundle_race', 'k': 2, 'expect': 'one_wins'}, {'path': 'private', 'name': 'concurrent_revokes', 'k': 2, 'expect': 'one_wins'}, {'path': 'delegated', 'name': 'shared_grant_reads', 'k': 2, 'expect': 'any'}]}
public steps: 482 predicates: 16
probes: [('same_page_issues', 2), ('duplicate_slot_race', 2), ('same_shard_attests', 2), ('cross_shard_attests', 2), ('bundle_race', 2)]
phases: {'stage.create': 5, 'probe.concurrent': 19, 'stage.fill': 367, 'probe.hot_slot': 8, 'stage.ops': 78, 'stage.cancel': 5}
end_state_checks: ['pages']
private steps: 1221 predicates: 14
probes: [('concurrent_revokes', 2)]
phases: {'stage.create': 6, 'stage.issue': 128, 'stage.shield_prefix': 8, 'probe.boundary': 8, 'stage.shield_rest': 1012, 'stage.revocation': 20, 'probe.concurrent_revokes': 3, 'stage.consume': 32, 'stage.negative': 2, 'stage.reconstruct': 2}
end_state_checks: ['pages', 'leaf_count', 'nullifiers', 'challenges', 'revocations']
delegated steps: 72 predicates: 11
probes: [('shared_grant_reads', 2)]
phases: {'stage.create': 5, 'stage.delegate': 4, 'stage.fill': 40, 'probe.delegated': 10, 'stage.cut': 7, 'stage.stranded': 6}
end_state_checks: ['pages', 'grants', 'page_delegated_to']
````

### G7

Command (exit 0):

```sh
python3 - <<'FACTS'
import json
p=json.load(open('.aiops/program.json'))
def walk(x):
 if isinstance(x,dict):
  if x.get('id') in ('rs-4-l2','rs-4-l3','rs-5-decision','k-benchmark-reproduction','k-local-program-closeout'):
   print(x['id'], 'depends_on:',x['depends_on'])
  for v in x.values(): walk(v)
 elif isinstance(x,list):
  for v in x: walk(v)
walk(p)
FACTS
```

Raw output:

````text
rs-4-l2 depends_on: ['rs-4-l1']
rs-4-l3 depends_on: ['rs-4-l2']
rs-5-decision depends_on: ['rs-4-l3', 'rs-1-issuercap-probe', 'testnet-key-management-decision']
k-benchmark-reproduction depends_on: ['k-stage4-local-exploration', 'rs-4-l3']
k-local-program-closeout depends_on: ['k-current-capability-map', 'k-adversarial-corpus', 'k-sdk-examples', 'k-benchmark-reproduction', 'k-operator-evidence']
````

### G8

Command (exit 0):

```sh
sed -n '64p' docs/status/OPEN_USER_DECISIONS_20261022.md
```

Raw output:

````text
| `rs-4-l2` 16,384슬롯 부하 측정 host · `/workspace/kix-run/wt/rs-4-l2/DECISION_REQUIRED.md` (2026-10-15) | 「User (spend / measurement environment), with Astra for any workload change.」 | 1. 「Run on a dedicated or quiet machine/VM (may involve cost): complete record, same scripts.」 2. 「Re-run on the builder machine in a quiet window with no other load: free, unreliable.」 3. 「Accept a reduced scope (e.g. public prefix only, or private and delegated first) as the L2 record: an Astra workload decision.」 | 「Option 1, or option 2 if the User can guarantee an idle builder host for several hours. The scripts need no change.」 | `reference/rights_scale/measurement_gap.py`가 존재한다 — 병합 #230 `6f75594…`; 병합된 기록 목록에서 경로별 분모를 다시 계산하는 오프라인 보고서로, 선택지 3의 범위 질문에 들어갈 자료다. `reference/rights_scale/host_conditions.py`와 `reference/rights_scale/test_host_conditions.py`가 존재한다 — 병합 #256 `f1734e0…`, 기록 `validation/2026-10-22-rs4-load-host-conditions-recorder/README.md`; 부하 평균·MemAvailable·uptime·벽시계 간극을 기록하는 표준라이브러리 기록기로 선택지 1/2의 공유 host 조건 근거다(러너에 배선 안 됨, 역치·판정 없음). 같은 기록이 허용 부하 수준은 `UNDETERMINED`(User)로 유지한다. `validation/2026-10-15-rs-4-l2-load/README.md`는 여전히 main 밖이다(부재 확인). |
````

### G9

Command (exit 0):

```sh
sed -n '18,29p' reference/rights_scale/host_conditions.py
```

Raw output:

````text
             gap-factor x interval.

Measured values and detected gaps only. There is no threshold, no verdict and no
default for the interval or the gap factor: the acceptable load level for an
RS-4 L2 attempt is UNDETERMINED (owner: User), so both numbers are required
arguments. A reported gap is not labelled: a VM suspend widens the wall clock
gap but not the monotonic gap, a scheduling stall widens both, and the summary
lists both numbers without interpreting them.

This module measures nothing by itself and is not wired into the L1 runner.
Exit status is non-zero only for unreadable or malformed input.

````

### G10

Command (exit 0):

```sh
nl -ba reference/rights_scale/load_plan.py | sed -n '523,585p'
nl -ba reference/rights_scale/load_plan.py | sed -n '655,680p'
nl -ba reference/rights_scale/measurement_gap.py | sed -n '46,62p'
nl -ba reference/rights_scale/test_measurement_gap.py | sed -n '77,85p'
rg -n 'same_page_issues|duplicate_slot_race|same_shard_attests|cross_shard_attests|bundle_race|concurrent_revokes|shared_grant_reads' reference/rights_scale/load_plan.py
```

Raw output:

````text
   523	DEFAULT_SETTINGS = {
   524	    'seed': DEFAULT_SEED,
   525	    'show': {'seated': SEATS, 'ga': 0, 'page_size': PAGE_SIZE},
   526	    'shards': {'public': PUBLIC_SHARDS, 'private': PRIVATE_SHARDS,
   527	               'delegated': DELEGATED_SHARDS},
   528	    'zk': {'depth': model.ZK_DEPTH, 'root_history_k': model.LOCALNET_ROOT_HISTORY_K,
   529	           'nullifier_shards': model.LOCALNET_NULLIFIER_SHARDS,
   530	           'challenge_shards': model.LOCALNET_CHALLENGE_SHARDS},
   531	    'closed_loop': True,
   532	    'arrival_rate': 0,
   533	    'shield_count': SEATS,          # the depth-10 leaf-capacity boundary
   534	    'consume_count': 32,
   535	    'invalidation_count': 8,
   536	    'transfers': 8,
   537	    'admissions': 8,
   538	    'refunds': 16,
   539	    'revokes': 16,
   540	    'reissues': 2,
   541	    'reservations': 2,
   542	}
   543	
   544	
   545	def expand(settings=None):
   546	    cfg = dict(DEFAULT_SETTINGS)
   547	    if settings:
   548	        cfg.update(settings)
   549	    rng = random.Random(cfg['seed'])
   550	    paths = {}
   551	    expected = {}
   552	    for name, build in (('public', public_path), ('private', private_path),
   553	                        ('delegated', delegated_path)):
   554	        steps, exp = build(cfg, random.Random(rng.randrange(2 ** 32)))
   555	        paths[name] = steps
   556	        expected[name] = exp
   557	    seq = 0
   558	    probes = []
   559	    for name, steps in paths.items():
   560	        for step in steps:
   561	            step.setdefault('expect', 'ok')
   562	            step['seq'] = seq
   563	            seq += 1
   564	            if step['op'] == 'parallel':
   565	                probes.append({'path': name, 'name': step.get('name'), 'k': len(step['of']),
   566	                               'expect': step['expect']})
   567	    cfg['concurrency_probes'] = probes
   568	    return {
   569	        'version': VERSION,
   570	        'settings': cfg,
   571	        'requested': {
   572	            'seats_per_show': cfg['show']['seated'],
   573	            'shield_count': cfg['shield_count'],
   574	            'consume_count': cfg['consume_count'],
   575	            'invalidation_count': cfg['invalidation_count'],
   576	        },
   577	        'phases': {
   578	            'public': ['stage.create', 'probe.concurrent', 'stage.fill', 'probe.hot_slot',
   579	                       'stage.ops', 'stage.cancel'],
   580	            'private': ['stage.create', 'stage.issue', 'stage.shield_prefix', 'probe.boundary',
   581	                        'stage.shield_rest', 'stage.revocation', 'probe.concurrent_revokes',
   582	                        'stage.consume', 'stage.negative', 'stage.reconstruct'],
   583	            'delegated': ['stage.create', 'stage.delegate', 'stage.fill', 'probe.delegated',
   584	                          'stage.cut', 'stage.stranded'],
   585	        },
   655	
   656	def main():
   657	    parser = argparse.ArgumentParser()
   658	    parser.add_argument('--expand', metavar='OUT')
   659	    parser.add_argument('--seed', type=int)
   660	    parser.add_argument('--shield-count', type=int)
   661	    parser.add_argument('--consume-count', type=int)
   662	    args = parser.parse_args()
   663	    settings = {}
   664	    if args.seed is not None:
   665	        settings['seed'] = args.seed
   666	    if args.shield_count is not None:
   667	        settings['shield_count'] = args.shield_count
   668	    if args.consume_count is not None:
   669	        settings['consume_count'] = args.consume_count
   670	    doc = assign_phases(expand(settings))
   671	    if args.expand:
   672	        Path(args.expand).write_text(json.dumps(doc, indent=1) + '\n')
   673	        counts = {k: len(v) for k, v in doc['paths'].items()}
   674	        print(f'expanded {VERSION} -> {args.expand} steps={counts}')
   675	        return
   676	    parser.error('--expand is required')
   677	
   678	
   679	if __name__ == '__main__':
   680	    main()
    46	# end-state checks.
    47	WORKLOAD_ECHOES = ('invalidation_count', 'consume_count')
    48	
    49	
    50	def _is_predicate(step):
    51	    """A predicate step asserts something: a named parallel probe, or an
    52	    expectation other than plain ok/any (expected abort or client refusal)."""
    53	    if step.get('op') == 'parallel':
    54	        return True
    55	    return step.get('expect') not in (None, 'ok', 'any')
    56	
    57	
    58	def _end_state_checks(expected):
    59	    """End-state check names a path's snapshot would be evaluated against."""
    60	    return [k for k in (expected or {}) if k not in WORKLOAD_ECHOES]
    61	
    62	
    77	
    78	    def test_end_state_check_names(self):
    79	        gap = measurement_gap.build_gap_report(self.doc, _report(self.doc), None)
    80	        checks = {n: p['end_state']['checks'] for n, p in gap['paths'].items()}
    81	        self.assertEqual(checks['public'], ['pages'])
    82	        self.assertEqual(checks['private'],
    83	                         ['pages', 'leaf_count', 'nullifiers', 'challenges', 'revocations'])
    84	        self.assertEqual(checks['delegated'], ['pages', 'grants', 'page_delegated_to'])
    85	
172:        {'op': 'parallel', 'name': 'same_page_issues',
176:        {'op': 'parallel', 'name': 'duplicate_slot_race',
180:        {'op': 'parallel', 'name': 'same_shard_attests',
186:        {'op': 'parallel', 'name': 'cross_shard_attests',
192:        {'op': 'parallel', 'name': 'bundle_race',
391:    steps.append({'op': 'parallel', 'name': 'concurrent_revokes', 'expect': 'one_wins',
456:    steps.append({'op': 'parallel', 'name': 'shared_grant_reads', 'expect': 'any',
581:                        'stage.shield_rest', 'stage.revocation', 'probe.concurrent_revokes',
634:        i_race = next(i for i, s in enumerate(steps) if s.get('name') == 'concurrent_revokes')
640:                ('probe.concurrent_revokes', i_cons - i_race),
````

### B1

Command (exit 0):

```sh
git status --porcelain=v1 --untracked-files=all
git branch --show-current
git rev-parse origin/main HEAD
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Raw output:

````text
agent/kix-plan-plan-rs4-l2-option-impact-inventory
fc11cdf0150e54ed38bb363f2ded7238c48c6e53
fc11cdf0150e54ed38bb363f2ded7238c48c6e53
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
````

## Local verification (AGENTS.md §9)

Order: the four narrow suites first, then all 49 commands extracted in order
from the actual `Stdlib offline document checks` run block in
[protocol.yml](../../.github/workflows/protocol.yml), then documentary and scope
checks. Every Python process ran with `PYTHONDONTWRITEBYTECODE=1`.
No job was started in the background, and no localnet/measurement command ran.

| Narrow command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_load_plan.py` | exit 0; Ran 21 tests in 0.024s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_measurement_gap.py` | exit 0; Ran 8 tests in 0.157s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_summarize_load.py` | exit 0; Ran 11 tests in 0.169s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_host_conditions.py` | exit 0; Ran 37 tests in 0.648s; OK |

77 existing offline tests passed in total. Their timing output is a test-run log, not a performance measurement.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_load_plan.py
```

```text
.....................
----------------------------------------------------------------------
Ran 21 tests in 0.024s

OK
```

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_measurement_gap.py
```

```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.157s

OK
```

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_summarize_load.py
```

```text
...........
----------------------------------------------------------------------
Ran 11 tests in 0.169s

OK
```

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/rights_scale -p test_host_conditions.py
```

```text
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.648s

OK
```

The closest local CI equivalent for the documentation scope is the complete
stdlib step, not just the four mandatory checker pairs. The extraction driver
read lines after `- name: Stdlib offline document checks` and `run: |`, collected
the indented commands until the next step, asserted every command began
`python3 scripts/check_`, then ran each sequentially with `subprocess.run`.
Below is the exact command list and actual status. No CI file was edited.

| Command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_read_model_source_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_read_model_source_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_i12_proof_ids.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_i12_proof_ids.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_delegation_layer_matrix.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_tl_predicate_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_error_codes.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_error_codes.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_adapter_identity_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_adapter_identity_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_v5_transition_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_readiness_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_readiness_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_settlement_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_settlement_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bra_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bra_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_credit_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_credit_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_primary_price_fee_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ai_delegation_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_lifecycle_adr_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_invariants_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_toss_card_profile_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bcs1_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bcs1_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_performance_measurement_evidence_map.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 (passed) |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_stage5_host.py --self-test` | exit 0 (passed) |

All 49 invocations exited 0. The checker self-tests deliberately print
expected rejected fixtures; these are passing negative controls, not repository
failures. The full G-command and narrow-suite outputs above are retained;
repetitive CI self-test fixture output is summarized by the actual exit statuses
in this table. In particular, `check_ci_checker_wiring.py --self-test` reported
`self-test: pass (13 negative controls)` and the plain invocation reported
`ci checker wiring ok: scripts=28 plain=27 self_test=28 self_test_only=1 docs=19 citations=25`.
These are existing wiring counts, not the number of invocations in the stdlib
step (49); other checkers may be wired in other steps.

## Documentary and byte-preservation checks

V1 and V2 are one-off verification snippets in `/tmp`, not new repository scripts
or regression tests. Their exact sources are included below so the checks can be
reproduced without the temporary files. V1's heading/link and lexical checks
have the limited purpose described in their output; they are not a semantic
policy approval or a replacement for non-author review.

### V1

Actual command: `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/check_rs4_inventory.py`; exit 0.

```text
Inventory Markdown links and fragments: 51 resolved
Acceptance clauses: 2 verbatim in shared facts and all four options; dependency edges match
Map selection: {'RS_PREDICATE_EVIDENCE_MAP.md': ['RS-C14', 'RR-2', 'RR-5', 'RR-6'], 'RS_IM_EVIDENCE_MAP.md': []}
L1 path, predicate, probe and end-state facts match in-memory expansion; no L2 expansion
Four option sections, original owner wording and no recommendation: OK
```

Source used (can also run inline with `PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'`):

```python
from pathlib import Path
import re,json,sys,unicodedata
sys.path.insert(0,'reference/rights_scale')
import load_plan as L,measurement_gap as M
p=Path('docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md'); text=p.read_text()
def slug(s):
 s=re.sub(r'[`*_]','',s).lower()
 return ''.join(c for c in s if c.isalnum() or c in '_- ').replace(' ','-')
def headings(p):
 return {slug(m[1]) for m in re.findall(r'^(#{1,6}) (.+)$',p.read_text(),re.M)}
count=0
for target in re.findall(r'\]\(([^)]+)\)',text):
 path,_,frag=target.partition('#')
 f=(p.parent/path).resolve() if path else p
 assert f.exists(),target
 if frag: assert frag in headings(f),(target,headings(f))
 count+=1
print('Inventory Markdown links and fragments:',count,'resolved')
program=json.loads(Path('.aiops/program.json').read_text())
nodes={}
def walk(x):
 if isinstance(x,dict):
  if 'id' in x and 'spec' in x: nodes[x['id']]=x
  for v in x.values(): walk(v)
 elif isinstance(x,list):
  for v in x: walk(v)
walk(program)
assert 'plan-plan-rs4-l2-option-impact-inventory' not in nodes
spec=nodes['rs-4-l2']['spec']
clauses=spec.splitlines()[:2]
for clause in clauses: assert text.count('> '+clause)==5,clause
assert 'rs-4-l2' in nodes['rs-4-l3']['depends_on']
assert 'rs-4-l3' in nodes['rs-5-decision']['depends_on']
assert 'rs-4-l3' in nodes['k-benchmark-reproduction']['depends_on']
assert 'k-benchmark-reproduction' in nodes['k-local-program-closeout']['depends_on']
print('Acceptance clauses:',len(clauses),'verbatim in shared facts and all four options; dependency edges match')
selected={}
for fname in ['RS_PREDICATE_EVIDENCE_MAP.md','RS_IM_EVIDENCE_MAP.md']:
 s=Path('docs/status',fname).read_text().split('## 2. Map')[1].split('## 3.')[0]
 rows=[line for line in s.splitlines() if re.match(r'^\| (?:RS-C\d+|RR-\d+|IM-\d+) \|',line)]
 selected[fname]=[line.split('|')[1].strip() for line in rows if re.search('RS-4|rs-4|load_plan|summarize_load|MEASUREMENT_ONLY',line)]
assert selected['RS_PREDICATE_EVIDENCE_MAP.md']==['RS-C14','RR-2','RR-5','RR-6']
assert selected['RS_IM_EVIDENCE_MAP.md']==[]
print('Map selection:',selected)
d=L.assign_phases(L.expand())
for n,s in d['paths'].items():
 row=f'| {n} | {len(s)} | {sum(map(M._is_predicate,s))} |'
 assert row in text,row
 assert all('`'+x['name']+'`' in text for x in s if x['op']=='parallel')
 assert all('`'+c+'`' in text for c in M._end_state_checks(d['expected'][n]))
print('L1 path, predicate, probe and end-state facts match in-memory expansion; no L2 expansion')
owner='User (spend / measurement environment), with Astra for any workload change.'
assert owner in Path('docs/status/OPEN_USER_DECISIONS_20261022.md').read_text()
assert text.count(owner)==9
assert 'UNDETERMINED (owner: User)' in Path('reference/rights_scale/host_conditions.py').read_text()
assert not re.search(r'recommend|we choose|should run',text,re.I)
print('Four option sections, original owner wording and no recommendation: OK')
```

### V2

Actual command: `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/check_rs4_scope.py`; exit 0.

```text
Changed paths (tracked diff plus untracked):
docs/README.md
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md
validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md
Protected tracked blobs byte-identical to cached origin/main: 440
Including reference/v0.3-rc1 blobs: 108
runtime/crates/kix-kernel/src/lib.rs 69564b166f0c27f9af5d8422f0a466b18d74c20f
runtime/crates/kix-kernel/tests/quarantine_capacity.rs b607996c83a119c349f1cc90469ac1ba82764e20
No __pycache__ directories
Cached origin/main = unchanged branch HEAD: fc11cdf0150e54ed38bb363f2ded7238c48c6e53
```

Source used (can also run inline with `PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'`):

```python
from pathlib import Path
import subprocess,hashlib,os
allowed={'docs/README.md','docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md','validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md'}
def git(*args): return subprocess.check_output(['git',*args])
changed=set(git('diff','--name-only','origin/main').decode().splitlines())|set(git('ls-files','--others','--exclude-standard').decode().splitlines())
assert changed==allowed,changed
print('Changed paths (tracked diff plus untracked):')
for p in sorted(changed): print(p)
protected=['reference/','scripts/','.github/','.aiops/','runtime/','docs/tasks/','docs/status/RS_PREDICATE_EVIDENCE_MAP.md','docs/status/RS_IM_EVIDENCE_MAP.md']
subprocess.run(['git','diff','--exit-code','origin/main','--',*protected],check=True)
entries=git('ls-tree','-rz','origin/main','--',*protected).split(b'\0')
count=0; refcount=0
for ent in entries:
 if not ent: continue
 meta,rawpath=ent.split(b'\t'); mode,kind,expected=meta.split(); path=Path(os.fsdecode(rawpath))
 assert kind==b'blob',(kind,path)
 data=os.fsencode(os.readlink(path)) if mode==b'120000' else path.read_bytes()
 actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest().encode()
 assert actual==expected,path
 count+=1
 if str(path).startswith('reference/v0.3-rc1/'): refcount+=1
print('Protected tracked blobs byte-identical to cached origin/main:',count)
print('Including reference/v0.3-rc1 blobs:',refcount)
for path,want in [('runtime/crates/kix-kernel/src/lib.rs','69564b166f0c27f9af5d8422f0a466b18d74c20f'),('runtime/crates/kix-kernel/tests/quarantine_capacity.rs','b607996c83a119c349f1cc90469ac1ba82764e20')]:
 got=git('hash-object',path).decode().strip(); assert got==want; print(path,got)
assert not list(Path('.').rglob('__pycache__')),'__pycache__ found'
print('No __pycache__ directories')
assert git('rev-parse','origin/main')==git('rev-parse','HEAD')
print('Cached origin/main = unchanged branch HEAD:',git('rev-parse','HEAD').decode().strip())
```

### V3

Actual command: `git diff --check`; exit 0.

```text
(no output)
```

### V4

Actual command: `git diff --exit-code origin/main -- reference/v0.3-rc1`; exit 0.

```text
(no output)
```

Before work, B1 gave the required blobs:

| Locked file | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | same required blob (V2) |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | same required blob (V2) |

V2 checks all 440 tracked blobs in the protected scopes directly against the
cached `origin/main` tree, including all 108 `reference/v0.3-rc1` blobs. It also
includes untracked paths in the exact three-path delivery check. This matters
because `git diff origin/main...HEAD` alone cannot see this uncommitted delivery.
V3 is the whitespace check; V4 is the explicitly requested reference-baseline diff.
No `__pycache__` directories exist after the checks.

## CI scope, deviations and limits

- Fetch intentionally NOT_RUN under the supervisor's no-network instruction;
  the cached ref is the observed base, not a verified fresh remote snapshot.
- The spec's phrase “paths and denominators ... at 16,384 slots” has no such
  definitions in this tree. Following the supplied design plan, the inventory
  records actual L1 definitions and missing L2 values as class B / UNDETERMINED —
  Astra (workload). It invents neither values nor an L2 workload. This does not
  resolve the existing rs-4-l2 environment decision or require a new decision
  to prepare the authorized inventory. Literal L2 denominator construction
  would require separate Astra workload input and authorized scope.
- As anticipated by the design plan, `k-local-program-closeout` is included
  as an additional, explicitly informational transitive dependency beyond
  the three named downstream nodes. No status is assigned to it.
- G-commands use `rg` instead of `grep`; G5 uses a whole-tree filename locator
  plus targeted source excerpts, and G7 decodes exact dependency arrays instead
  of relying on grep context windows. G10 adds definition/probe/CLI excerpts.
  These are read-only derivation refinements; no source facts change.
- The design plan's claim that both workflows skip all heavy jobs for these
  paths is too broad. The path cases at `ktx-kernel.yml:75–82` and
  `protocol.yml:156–163` classify the three changed files as documentation-only
  for their guarded kernel/protocol jobs. The independent `rights-scale` job
  (`protocol.yml:25–98`) has only the draft-PR guard, no docs-only guard, and
  includes Sui/localnet/ZK runs. Those runs are NOT_RUN locally under the node's
  explicit no-localnet/no-measurement scope. No blanket full-CI pass is claimed.
- The full stdlib block is run in addition to the design's five checker pairs;
  the optional narrow checks are extended with the already-cited summarizer
  and host-recorder synthetic suites. No new tests or dependencies are added.
- An exploratory lookup for `.github/workflows/ci.yml` reported no such file;
  `rg --files .github/workflows` located `ktx-kernel.yml` and `protocol.yml`,
  which were inspected instead. A speculative `docs/*RIGHT*` glob also reported
  no match; subsequent searches used existing exact source paths. Neither was
  a test failure or a repository change.

## AGENTS.md §14 delivery report

| Required item | Evidence / state |
|---|---|
| Task ID / document | Node above; supplied supervisor task/design input, no `docs/tasks/` document. |
| Observed cached main / base | `fc11cdf0150e54ed38bb363f2ded7238c48c6e53`; fetch NOT_RUN; freshness unknown. |
| Implementation head | Branch HEAD remains `fc11cdf0150e54ed38bb363f2ded7238c48c6e53`; implementation is the uncommitted three-path working-tree diff. |
| Exact final task head | No delivery commit created under supervisor rules. Existing HEAD is unchanged; it does not include the working-tree delivery. Supervisor assigns the committed head later. |
| Merge commit / post-merge blobs | N/A — no merge. |
| Complete changed paths | `docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md`; `docs/README.md`; `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md`. |
| Locked blobs | Both required hashes match before and after; final-merge check N/A. V2 also checks all protected source bytes. |
| Existing coverage / new evidence | Coverage table above; 77 existing offline tests pass; no new tests. Inventory collates the previously absent per-option evidence; README records derivation. |
| Commands / results | G1–G10 and B1 above exit 0; four narrow suites pass; 49 CI stdlib commands exit 0; V1–V4 exit 0. Final index/checker confirmation recorded below. |
| Exact-head KTX CI run ID / status / conclusion | Unavailable / NOT_RUN / not claimed; no final committed delivery head or GitHub action. |
| Exact-head KIX protocol CI run ID / status / conclusion | Unavailable / NOT_RUN / not claimed; local stdlib checks are the evidence, not a hosted result. |
| Post-merge main CI run ID / status / conclusion | N/A — no merge. |
| Contract violations found | None established by this documentation task; no behavioral change or measurement. |
| Contract-undefined characterizations | No in-tree 16,384-slot workload denominators; prefix cut and final O3b scope remain UNDETERMINED — Astra (workload). IM-10 is a lexical near-miss, not added measurement evidence. |
| Explicit non-claims / not tested | No measurement, localnet, host sampling, provisioning, spend, Cargo/Clippy/format, Move/ZK/Node execution, production system or external decision/PR verification. No option chosen, numeric policy value set, state/grade/contract changed, independent review or merge-ready claim. |
| Remaining uncertainty / owner | Allowed load stays `UNDETERMINED (owner: User)`; ledger owner stays “User (spend / measurement environment), with Astra for any workload change.” Host/spend, L2 workload, prefix cut, final scope, accepted measurement record and downstream release remain future owner decisions/evidence. Remote freshness and exact-head review/CI remain supervisor follow-up. |

Local builder delivery only. The rs-4-l2 decision remains open. Non-author
exact-HEAD review, applicable audit/CI and User-authorized Git/GitHub work are
outside this one-shot builder delivery; no merge readiness is asserted.

## Final local confirmation

After the final inventory citation and validation-record edits, the following
commands were run sequentially. All exited 0. No new source change required
a repeat of the 77 narrow tests or the other unchanged CI checkers.

| Actual command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py --self-test` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/check_rs4_inventory.py` | exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/check_rs4_scope.py` | exit 0 |
| `git diff --check` | exit 0 |
| `git diff --exit-code origin/main -- reference/ scripts/ .github/ .aiops/ runtime/ docs/tasks/ docs/status/RS_PREDICATE_EVIDENCE_MAP.md docs/status/RS_IM_EVIDENCE_MAP.md` | exit 0 |
| `git status --porcelain=v1 --untracked-files=all` | exit 0 |

Final inventory/scope output:

```text
Inventory Markdown links and fragments: 51 resolved
Acceptance clauses: 2 verbatim in shared facts and all four options; dependency edges match
Map selection: {'RS_PREDICATE_EVIDENCE_MAP.md': ['RS-C14', 'RR-2', 'RR-5', 'RR-6'], 'RS_IM_EVIDENCE_MAP.md': []}
L1 path, predicate, probe and end-state facts match in-memory expansion; no L2 expansion
Four option sections, original owner wording and no recommendation: OK
Changed paths (tracked diff plus untracked):
docs/README.md
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md
validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md
Protected tracked blobs byte-identical to cached origin/main: 440
Including reference/v0.3-rc1 blobs: 108
runtime/crates/kix-kernel/src/lib.rs 69564b166f0c27f9af5d8422f0a466b18d74c20f
runtime/crates/kix-kernel/tests/quarantine_capacity.rs b607996c83a119c349f1cc90469ac1ba82764e20
No __pycache__ directories
Cached origin/main = unchanged branch HEAD: fc11cdf0150e54ed38bb363f2ded7238c48c6e53
 M docs/README.md
?? docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md
?? validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md
```
