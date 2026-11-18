# Provider normalization golden vectors — local builder evidence

Node: `plan-provider-normalization-golden-vectors`; execution date 2026-10-28.
Input: the supervisor-supplied node specification and read-only design plan in
this session; no issue or task document exists for this node. Dependencies are
`plan-plan-provider-fact-normalization-offline` and
`plan-provider-cancel-boundary-tests`. This is not an ASTRA program-mode session.

Observed local `origin/main` and initial/current task HEAD:
`0ce8b0567e172e627d69ab121d75cd87f00607fa` on
`agent/kix-plan-provider-normalization-golden-vectors`. They match; no local
base delta. Remote freshness is unverified: the supervisor's explicit
no-network rule overrides the AGENTS.md §1 fetch. No commit, push, GitHub
operation or merge is authorized or performed. Implementation/final committed
head, merge SHA and post-merge checks are not applicable to this uncommitted
builder handoff.

## Basis and coverage before changes

Read the repository guidance and
[ADAPTER_EVENT_IDENTITY §4.4](../../docs/contracts/ADAPTER_EVENT_IDENTITY.md#44-정규화된-사실),
fixture inputs, implementation and existing tests before adding coverage.
The following paths are relative to `reference/provider_facts/`.

| Requirement | Before-change coverage | Gap addressed |
|---|---|---|
| Complete independent fact, byte and digest expectations | Partially covered: `test_evidence_hash.py::EvidenceHashTests.test_evidence_hash_is_sha256_of_canonical_normalized_fact` derives expected bytes/hash from the actual fact | Five literal facts, separately transcribed bytes and pinned digest strings in `normalization_golden_vectors.py`; `NormalizationGoldenVectorTests.test_literal_facts_bytes_and_digests` compares both entry points to them |
| Payment/cancel, Korean, raw timestamps, existing u128 boundary | Partially covered: `test_timestamps.py::TimestampTests.test_ambiguous_timezone_stays_unresolved_and_raw_text_is_preserved`, `test_integer_krw.py::IntegerKrwTests.test_integer_krw_rejects_float_scale_sign_and_range_paths`, `test_cancel_boundaries.py::CancelBoundaryTests.test_cancel_integer_technical_boundaries` | Complete literal vectors rather than only component checks |
| JSON whitespace/key ordering | Not explicitly covered by existing hash tests | `test_json_whitespace_and_key_order_invariance`: compact, indented and recursively reversed dictionaries, preserving array order |
| Included-field sensitivity | Partially covered: both existing `EvidenceHashTests` methods change amounts; `test_payment_ref.py::PaymentRefTests.test_payment_ref_is_the_five_field_tuple` checks reference equality | `test_included_fields_change_fact_and_hash`: five reference fields, payment/cancel amounts and occurrence text; explicit edits to copies of literal facts, changed hashes and unchanged unaffected items, through both entry points |
| Receipt/index exclusion and cancellation ordering | Sufficiently covered: `EvidenceHashTests.test_cancel_hashes_ignore_snapshot_order_and_receipt_metadata` | Reused unchanged through full provider discovery; no duplicate tests |
| Discovery, docs index and checker self-tests | Existing workflow wiring sufficient | Run current discovery and stdlib workflow block; no workflow edits |

## Source-informed literal derivation

This is builder-authored, source-informed evidence, not clean-room authorship
or independent A2 review. The author inspected `synthetic_documents.py`,
`provider_facts.py`, existing tests and §4.4. The expectations are specified
independently of calls to `normalize_recorded_document`, `normalized_fact`,
and the implementation's `_canonical` helper. The vector module imports
nothing and contains complete literal dictionaries, bytes and digest strings.
There is no expectation generator in the delivered tests.

1. Manually specify all fact fields from the fixture values and inspected
   representation: provenance; five-field payment reference; item kind,
   integer amount, KRW, status, occurrence text/offset/status; and complete
   payment or cancellation detail. `PAID`, `PARTIAL_CANCEL` payment and cancel,
   `OFFSET_LESS_CREATED_AT`, and `MAX_KRW_AMOUNT` supply five selected items.
   `item_position` selects only this fixture's item, never an event identity.
2. Separately transcribe each canonical JSON byte literal: recursively sorted
   keys; compact comma/colon separators; unescaped Unicode encoded as UTF-8;
   exact decimal integers; JSON null for None; no BOM or trailing newline.
   Korean `카드` is explicitly `\xec\xb9\xb4\xeb\x93\x9c` in the byte literals.
   Preserve original `requestedAt`/`approvedAt` text. Offset-less `createdAt`
   keeps null offset and `AMBIGUOUS_UNRESOLVED`, while approvedAt remains
   the occurrence. The boundary is literal integer
   `340282366920938463463374607431768211455`, an existing representation limit.
3. Run standalone stdlib `runpy`, `json` and `hashlib` over only the literal
   module, with no implementation/fixture import: decode the manually prepared
   bytes to cross-check the separate fact dictionary, calculate
   `hashlib.sha256(literal).hexdigest()`, and replace digest placeholders with
   those strings. This was done before running normalization tests. The
   delivered literals are never computed from actual normalizer results.
4. Tests independently decode/hash the constants, serialize actual facts with
   stdlib JSON for byte comparison, and compare public `evidence_hash` results
   with the pinned digest strings. A shared implementation field omission
   therefore cannot silently rewrite the test oracle.

| Case | UTF-8 byte length | SHA-256 |
|---|---:|---|
| `paid_payment` | 685 | `623bb1ed3e35ec4c7ad5908a774089661b968eac38d29106d4afb3d99ca3cd23` |
| `partial_cancel_payment` | 697 | `4be77e0249d636616dbe884114b0e2e8cfd690a2b02a7fe41d2385b19de4b76f` |
| `partial_cancel_item` | 497 | `0113104c22549a824251cdcaeb1722ff24c451a87c31e2af2a2b8b8f3ba64edd` |
| `offsetless_created_at_payment` | 774 | `41b8a0483d7cf03913c97c4ddb8667d6b30a42e925532e547c70f0bebeda6d7c` |
| `u128_max_payment` | 719 | `52c826ba3ca35303a08a8ac2a5432666a87a06151b56754cecaa9e0cb6f993cd` |

Sensitivity changes the five reference fields individually, updating matching
paymentKey/orderId document fields when needed. Each changes both item facts
and hashes. Changing totalAmount or approvedAt affects the payment only;
changing cancelAmount or canceledAt affects the cancel only. Occurrence
changes add `.000` with the same offset and instant, demonstrating that raw
text is preserved. Expected facts are copies of literals with explicit edits,
never copies of actual results. Tests also check fixture/vector preservation.

## Actual verification

Commands run from the repository root, in the foreground. Python checks use
`PYTHONDONTWRITEBYTECODE=1`. Host Python is 3.13.5; hosted protocol CI selects
3.12. No dependency provisioning or network access is part of this evidence.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD`; `git rev-parse refs/remotes/origin/main`; `git branch --show-current` | Clean at start; expected branch; both refs `0ce8b0567e172e627d69ab121d75cd87f00607fa`. |
| `python3 --version`; `date -u +%F` | Python 3.13.5; 2026-10-28. |
| Standalone stdlib literal-only `runpy`/JSON decode/SHA-256 derivation (described above) | PASS; all 5 manually specified facts match decoded literal bytes; digest values/lengths shown above. No implementation/fixture imports. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p test_normalization_golden_vectors.py -v` | PASS (exit 0); 3 tests, run before broader checks. |
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -v` | PASS (exit 0); 31 tests. |
| `rustc --version` | PASS (exit 0) |
| `cargo --version` | PASS (exit 0) |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0) |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0); 7 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS (exit 0); 139 passed across 9 target summaries, no failures |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS (exit 0); 339 passed across 46 target summaries, no failures |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS (exit 0) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS (exit 0) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) |

The following 63 commands were extracted verbatim from the current
`protocol.yml` **Stdlib offline document checks** run block and executed
sequentially with `subprocess.run`, retaining each exit code and output.
`check_stage5_host.py` runs only with `--self-test`, as CI requires.
The plain loopback/cache checks report this host only, with no activation,
service provisioning or offline-build guarantee. Full output was inspected;
logs are temporary under `/tmp/provider-golden-document-checks.json` and
`/tmp/provider-golden-runtime-checks.json`, not deliverables.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | PASS (exit 0); capability register ok: paths=454 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | PASS (exit 0); rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | PASS (exit 0); read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_docs_index.py` | PASS (exit 0); docs index ok: scanned=309 indexed=274 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | PASS (exit 0); i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS (exit 0); delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0); rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | PASS (exit 0); rs im evidence map ok: rows=30 expected=30 citations=202 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0); tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0); contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | PASS (exit 0); adapter identity evidence map ok: rows=17 expected=17 citations=71 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | PASS (exit 0); v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | PASS (exit 0); readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | PASS (exit 0); settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | PASS (exit 0); bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | PASS (exit 0); credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | PASS (exit 0); primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | PASS (exit 0); ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | PASS (exit 0); lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS (exit 0); self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | PASS (exit 0); contract invariants map: 27 rows, corpus, anchors, test symbols, counts, locked blobs and F-B1 document pins OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | PASS (exit 0); contract invariants self-test: 2 positive controls and 97 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | PASS (exit 0); Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS (exit 0); Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | PASS (exit 0); BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | PASS (exit 0); performance evidence map ok: Counts: rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (2 positive controls, 81 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | PASS (exit 0); feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (81 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | PASS (exit 0); integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS (exit 0); self-test: pass (100 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_evidence_map_rollup.py` | PASS (exit 0); evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | PASS (exit 0); self-test: pass (16 negative controls) |
| `python3 scripts/check_class_b_index.py` | PASS (exit 0); class B index ok: rows=217 sources=72 symbols=45; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | PASS (exit 0); self-test: pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS (exit 0); ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0); self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | PASS (exit 0); ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0); self-test: pass (18 negative controls) |
| `python3 scripts/check_loopback_host.py` | PASS (exit 0); Host-context JSON report only |
| `python3 scripts/check_loopback_host.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_cargo_offline_cache.py` | PASS (exit 0); Host-context JSON report only |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | PASS (exit 0); self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | PASS (exit 0); self-test: pass |

## Changed paths and preservation

Complete changed-path list:

- `reference/provider_facts/normalization_golden_vectors.py` (new)
- `reference/provider_facts/test_normalization_golden_vectors.py` (new)
- `validation/2026-10-28-plan-provider-normalization-golden-vectors/README.md` (new)
- `docs/README.md` (one relative validation link)

Before edits, `git hash-object` confirmed both required worktree blobs:
`runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`.
A complete sorted path-to-SHA-256 byte manifest of all 108 files under
`reference/v0.3-rc1/**` was saved outside the repository at
`/tmp/provider-golden-protected-before.json` for after-work comparison.
After all implementation/check runs, both worktree blobs still match the same
required values above. The complete 108-file path-to-SHA-256 manifest compares
equal before/after; SHA-256 of its `json.dumps(manifest, sort_keys=True)` UTF-8
serialization is
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
A read-only `git ls-tree -rz HEAD` walk recomputed each Git blob as SHA-1 of
`blob <byte-length>\0<file-bytes>` (symlinks use target bytes): all 1,102 tracked
paths outside `docs/README.md` match HEAD. This covers the implementation,
fixtures, old tests, contracts/maps, SDK/manifests, .aiops, task inputs and CI.
`git status --short --untracked-files=all` shows exactly the four listed paths;
the docs diff contains only the new relative link. Cargo outputs are ignored
build artifacts, not source changes.

| Preservation command / check | Actual result |
|---|---|
| Read-only Python `git hash-object` calls for the two locked worktree files | PASS before and after; both exact required blobs match |
| Python sorted SHA-256 byte manifest, before/after `reference/v0.3-rc1/**` | PASS; all 108 files and paths equal, manifest digest above |
| Read-only Python Git-blob recomputation against `git ls-tree -rz HEAD` | PASS; 1,102 tracked paths outside the allowed docs edit unchanged |
| `git diff --check` | PASS (exit 0) |
| `git diff -- docs/README.md` | One new relative validation link only |
| `git status --short --untracked-files=all` | Exactly four paths listed above |

Final docs-index/self-test and scope checks run after completing this record
are recorded in the supervisor handoff; their results do not require any new
source or evidence-grade changes.

## Discrepancies, limitations and delivery gates

All evidence is `MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY`, **Analog, NOT Toss**.
These vectors pin only the current synthetic fixture representation; they
adopt no operational encoding, provider conformance contract, product policy,
hash-schema/domain/schema registry or SDK/manifests. No grade is promoted.
Raw snapshot status differences are characterized as fixture content; no
past event identity or historical capture hash is derived from these snapshots.

Contract classification: existing §4.4 integer/text/fact requirements match
these observations (A); no explicit contract violation was found. The exact
JSON representation is a synthetic characterization, not contract-defined
operational semantics (B). `EventItemId` derivation, `ProviderFactKey`, alias
rules and domain/schema assignments remain UNDETERMINED with existing owners:
TM04/Toss technical, Astra, and `k-stage5-durable-tx` for durable tables.
No uncertainty is resolved by these vectors. No STOP condition was encountered.

No live lookup, real funds, PG/bank/KYC call, public endpoint, Sui, secret,
production runtime, storage/replication/consensus implementation, new coin/TIX
module or protocol command was needed. No durability, exactly-once, chain
finality, legal compliance or production-readiness claim follows. Full protocol
CI (bootstrap, SDK, Move/localnet, circuits and unrelated integration jobs)
is not run locally by this node.

Non-author A2 exact-HEAD review is outstanding. KTX kernel verification and
KIX protocol verification exact-final-head run IDs/status/conclusions are
unavailable and unqueried; the supervisor owns final commit/publication and
those gates. No merge/post-merge result applies. Local READY means builder
handoff only, not merge-ready, independent review or hosted CI success.

Deviations: no implementation-scope deviation. Per the supervisor, no fetch,
commit or GitHub action; remote freshness/final committed SHA remain unverified.
Local Cargo uses offline mode and existing tools/cache only. Workspace test and
Clippy runs extend the planned kernel checks to match the protocol Rust step. Python version
differs from CI as recorded above. No task input, .aiops, authoritative contract,
evidence grade, implementation, existing fixture/test, CI or protected file is edited.
