# Toss card profile clause evidence map — local validation

Date: 2026-10-26 (Asia/Seoul). Node/task: **plan-plan-toss-card-profile-evidence-map**. Builder-authored evidence, not independent A2 review, acceptance, a capability grade change or merge readiness.

Task input is the supervisor’s node specification and read-only design plan in the session. No issue was created and no node document exists under docs/tasks/; none was added or edited. This is not ASTRA program mode. Branch: agent/kix-plan-plan-toss-card-profile-evidence-map.

Observed **local origin/main/base and initial task HEAD**: `1bb000bd125a1e8ecdd033cea01733d58588199e`, equal to the design’s base; no delta against that local ref. Fetch was omitted because the supervisor explicitly forbids network/GitHub actions; freshness of the remote is unverified. Implementation and final working-tree state are uncommitted on that same HEAD. No final delivery commit exists yet. No commit, push, PR, issue, comment, tag, branch mutation or merge was performed. Publication belongs to the supervisor.

Complete changed-path list:

- docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md — new clause map.
- scripts/check_toss_card_profile_evidence_map.py — new stdlib checker with in-memory self-tests.
- .github/workflows/protocol.yml — exactly two checker invocations added to the unguarded Stdlib offline document checks step.
- docs/README.md — one location-only bullet linking this record and the map.
- validation/2026-10-26-plan-toss-card-profile-evidence-map/README.md — this record.

[The map](../../docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md) is the existing-coverage mapping: **41 rows across §§1–9**, with **COVERED=5, PARTIAL=10, NOT_COVERED=15, OPEN=11**. COVERED is limited to stated offline kernel behavior. Partial rows name the missing adapter/provider/durable/time surfaces and their owners. No kernel, reference or adapter regression test was added. Existing v4/v5 tests were inspected and cited rather than duplicated. Python evidence is labelled analog, NOT Toss. The §8 table preserves the three item/status cells verbatim, including Markdown, and owner extracts exactly; all three remain UNDETERMINED/OPEN. No values were filled in.

The new evidence is the map plus checker self-tests for missing/duplicate/invented rows, new contract sections, missing anchors/symbols/files, helpers, malformed/empty/mixed citations, column/path restrictions, status/owner/gap rules, altered/dropped open items, missing links/related IDs, provider-result labelling, retry arithmetic and locked-blob changes. Final result: **3 positive controls and 77 negative fixtures passed**, memory only. The initial full stdlib-step run used 76 negative fixtures; the malformed-interval diagnostic was then added and the final checker pair was rerun successfully. Test-symbol existence is textual evidence, not proof of semantic coverage or independent provenance. The checker executes no cited test and uses no provider connection.

Before edits and after testing, raw Git blob hashes match:

| Path | Before | After |
|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | 69564b166f0c27f9af5d8422f0a466b18d74c20f |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | b607996c83a119c349f1cc90469ac1ba82764e20 |
| docs/contracts/PG_TOSS_CARD_PROFILE.md | 4338fc72698f2f15c3723f3d13e677d3e1aff29d | 4338fc72698f2f15c3723f3d13e677d3e1aff29d |
| docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md | e1fd5d1b24cdc5e08a29f1e8216a1c6b62c3f44d | e1fd5d1b24cdc5e08a29f1e8216a1c6b62c3f44d |
| docs/operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md | ee64ca29d99c5b955fb96d29a0ccfaa8cdae52b6 | ee64ca29d99c5b955fb96d29a0ccfaa8cdae52b6 |

All **108 tracked reference/v0.3-rc1 files** also match the local origin/main blob bytes. No transient locked-file mutation was used; negative controls substitute bytes in memory.

Commands actually run from the repository root are recorded below. Narrow checker checks ran before the broader CI equivalents. Both workflow definitions were inspected. Python subprocess runners under /tmp executed each listed command sequentially, in the foreground, with captured output; no long job was launched with a background shell operator. PYTHONDONTWRITEBYTECODE=1 was set for the stdlib, Rust and Python runner invocations. Cargo was offline and used already available dependencies. Observed tools: Python 3.13.5; rustc 1.98.1 (48a229cea 2026-09-01); cargo 1.98.1 (797e8a9bc 2026-08-05).

| Command | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` | Exit 0; both equal the full base SHA above; unchanged at final verification. |
| `git branch --show-current` | Exit 0; expected task branch above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs docs/contracts/PG_TOSS_CARD_PROFILE.md docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md docs/operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md` | Exit 0 before edits and at final verification; all five hashes match the table. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0 initially and after final changes; all 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK. |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; initially 3 positive/76 negative controls, final 3 positive/77 negative controls passed. |
| `python3 scripts/check_toss_card_profile_evidence_map.py --bogus` | Expected exit 2 with usage. A separate subprocess assertion confirmed returncode == 2. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 78 tests passed, no failures/ignored tests; doc-tests succeed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --locked --offline` | Exit 0; 56 tests passed, no failures/ignored tests; doc-tests succeed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 257 tests passed, no failures/ignored tests; doc-tests succeed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; all workspace targets passed with warnings denied; includes the KTX kernel CI scope. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; formatting check only, no source mutation. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance not certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 418 tests passed. |
| `python3 -m unittest integration_gate.test_http_gate` | Exit 0; 41 tests passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; normal dependency is kix-types v0.0.0 only. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0; a948a1b687de2727ad717db0f7a0aa4159ecf5258e52e18eccf05cc08329d83e; 84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f; d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae respectively. |
| `python3 /tmp/verify_toss_protected.py` | Exit 0; raw-byte SHA-1 recomputation, git show comparison of all five pinned files, unchanged HEAD check, 108 raw reference comparisons and protected-path diff all passed. Its Git commands are listed below. |
| `git ls-tree -r -z origin/main -- reference/v0.3-rc1` and `git cat-file blob <blob>` for each entry, invoked through the verification script | Exit 0; every tracked file’s read_bytes() equals its base Git blob. |
| `git show origin/main:<path>` for each of the five pinned files, invoked through the verification script | Exit 0; each file’s bytes equal the base Git blob. |
| `git diff --name-only origin/main -- docs/contracts docs/operations docs/tasks reference/v0.3-rc1 .aiops runtime docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md` | Exit 0; empty output. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git status --short` | Exit 0; exactly the five delivery paths above. |

The protocol.yml **Stdlib offline document checks** run block was extracted and every command executed in order: **43 commands, all exit 0**. The final new-checker pair was rerun after the one additional malformed-schedule fixture; other checkers’ inputs did not change. The exact commands and results (latest for the new checker) follow:

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=252 indexed=217 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

The authoritative stdlib block was extracted with this code (the /tmp runner used shlex.split and subprocess.run to capture each return code and output):

```python
workflow = Path('.github/workflows/protocol.yml').read_text()
block = workflow.split('      - name: Stdlib offline document checks\n', 1)[1].split('        run: |\n', 1)[1]
commands = []
for line in block.splitlines():
    if not line.startswith('          '):
        break
    if line.strip() and not line.lstrip().startswith('#'):
        commands.append(line.strip())
assert commands[-1] == 'python3 scripts/check_stage5_host.py --self-test'
```

Contract discrepancy classification: no explicit class C violation found in the cited offline evidence, and no new class B executable behavior characterized. Contract-undefined/external-input gaps remain named in the map: signature, merchant and split-payout scope, provider identity stability, real MID and scope binding, time interpretation, post-15-day exceptions, status/void evidence, retention, automatic delegation limit and independent cut. No contract semantics were invented or changed.

Deviations: fetch omitted under the supervisor’s no-network instruction. S6-ONE-PAYMENT uses the design’s allowed NOT_COVERED alternative because kernel dedupe does not verify a Toss Payment/cancels payload. Full workspace tests and workspace Clippy supplement the planned crate checks. The malformed-interval fixture adds a fail-closed diagnostic for unfamiliar input, without a contract or policy change. The §1–§9 task document is the supplied session specification; no immutable task file was invented. No STOP condition was encountered and no decision request was needed.

Exact-head **KTX CI** run ID/status/conclusion: **not queried/not run**. Exact-head **KIX protocol CI** run ID/status/conclusion: **not queried/not run**. Final delivery commit: **none** (supervisor will commit). Merge commit and post-merge main CI: **not applicable**. Both workflows will require exact-head evidence after publication; local results do not establish merge readiness. Non-author exact-HEAD A2 review and authorized merge/post-merge verification remain supervisor follow-up.

Non-claims and limits: **no provider facts, no live funds, no sandbox evidence**. No provider, bank or KYC calls, real card entry, credentials, public endpoints, Sui execution, storage engine or production runtime. The HTTP unit suite uses disposable loopback servers only. No full hosted protocol pipeline, Move/ZK/localnet, browser card authentication, actual long-delay provider execution, signature, finality, independent cut, legal compliance, production durability or exactly-once behavior was verified. v5 is an in-memory non-production model. Historical official-document statements were not refreshed. Open items remain UNDETERMINED/OPEN with the contract’s owners; the future provider-sandbox and adapter/custody nodes require separate inputs and authorization. Current capability register, contracts, both cross-linked documents, immutable reference tree, task documents and .aiops remain unchanged.
