# rs-im-evidence-map

Node: `plan-plan-rs-im-evidence-map`. Adds `docs/status/RS_IM_EVIDENCE_MAP.md`, one row per impact-table id IM-01..IM-30 of `docs/contracts/RIGHTS_SCALE_PROFILE.md` section 12 (30 rows), and `scripts/check_rs_im_evidence_map.py` (stdlib only, with `--self-test`), wired into the stdlib step of `.github/workflows/protocol.yml`.
Issue: none. Depends on: `plan-rs-predicate-evidence-map`, `plan-rs0-review-pack`, `rs-3b`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792193921 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA and no final task head SHA, and no KTX kernel verification or KIX protocol verification run exists for this work. The exact-head CI results belong in the pull request closure report (AGENTS.md section 11).

Observed `origin/main` = branch HEAD = `9eb6b9ff24c6ca5825a3d999c81932a38ae79f02` (merge of #212), after `git fetch origin main` (a read-only fetch that AGENTS.md section 1 asks for).

**This record and the map are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, the operational count stays 0, no Sui, ZK, Move, localnet, Cargo or Node run was made, and the checker proves only that a cited name exists, not that the test asserts the predicate.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match the required blobs before and after. The diff of `reference/v0.3-rc1`, `runtime`, `.aiops`, `docs/tasks`, `docs/contracts` and `docs/decisions` against `origin/main` is empty (commands below).

## What this change does

- The map has 30 rows with a closed status: 10 `COVERED_LOCALNET`, 3 `COVERED_MODEL_OR_MEMORY`, 15 `PARTIAL`, 0 `NOT_COVERED`, 0 `MEASUREMENT_ONLY`, 2 `UNCHANGED_BY_DESIGN`. Statuses are builder readings of the cited test bodies; Astra may reclassify.
- Column 2 is the treatment word copied from the profile. The citations are `path::symbol` grouped by layer (Move, Python, Rust, localnet or record, unchanged-file evidence). A row takes the weakest status of its halves.
- Every `PARTIAL` row names what is missing in one sentence and an owner written as the profile writes it, or the reserved literal `none stated in profile`. No open value is chosen: page size P, shard count S, root history K, revocation window W, `MAX_BUNDLE_CHAIN` and the `IssuerCap` option stay with their owners.
- The checker verifies ids against section 12, the treatment word against the profile, statuses against citations, path existence and column patterns (nothing under `reference/v0.3-rc1/`), symbol definitions, owner parts and the counts line.
- Not done on purpose: no test added or renamed, no profile, register, decision or task edit, no gap closed.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/RS_IM_EVIDENCE_MAP.md` | New map. |
| `scripts/check_rs_im_evidence_map.py` | New checker. |
| `.github/workflows/protocol.yml` | Two added lines in the stdlib step. |
| `docs/README.md` | One table row linking the map and this record. |
| `validation/2026-10-17-rs-im-evidence-map/README.md` | This record. |

## AGENTS.md section 7: existing coverage per row

"Sufficiently" means every sentence of the policy text has at least one cited test whose body I read; it does not mean accepted. Localnet figures in the cited records are quoted at their own heads.

| ID | Map status | Section 7 class | Missing |
|---|---|---|---|
| IM-01 | 변경 | `COVERED_MODEL_OR_MEMORY` | sufficiently covered, model or in-memory only | none; the bps sum is tested at one pair that exceeds the ceiling (9000 and 1001) and the ceiling itself is not tested as accepted. |
| IM-02 | 변경 | `COVERED_MODEL_OR_MEMORY` | sufficiently covered, model or in-memory only | none; the initial generation 0 is shown by a first issue at expected generation 0 being accepted, and no test reads the generation right after creation. |
| IM-03 | 변경 | `PARTIAL` | partially covered | The split into objects has test evidence; no test asserts that offer, accept_gift, authorize_admission and consume leave ShowControl and InventoryPage unwritten (the read-only borrow is visible in the signatures of rights_scale.move, a builder reading and not a test), and the shield test asserts the page is not written only for shield. |
| IM-04 | 변경 | `PARTIAL` | partially covered | Per-page counters summed on read are exercised through the totals helper; no test reads the slot or generation value of an Issuance event, and the field layout is shown only by the BCS definition in client/types.mjs. |
| IM-05 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-06 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-07 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-08 | 유지 | `PARTIAL` | partially covered | The first three sentences are tested; the last sentence is a statement about what is not on chain and no test asserts it. refund_apply emits RefundDutyRequested, as the reference rights.move already does (builder reading of both sources), and the profile does not say whether such an event counts as a new refund obligation. |
| IM-09 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-10 | 변경 | `PARTIAL` | partially covered | The stored incremental root and the acceptance window are exercised; no test or measurement asserts that a call never recomputes the whole tree, which is an absence claim about the implementation. |
| IM-11 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none; K, the root-history length of the same ceiling, is a manifest field whose operational value the profile leaves UNDETERMINED, and this map chooses none. |
| IM-12 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-13 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-14 | 변경 | `PARTIAL` | partially covered | One slot bit count (the one of the 1,024-slot fixture tree) is exercised with its boundary; no test asserts the log-ceiling rule at other sizes, and no test pins the commitment layout beyond the public input layouts of the circuits. |
| IM-15 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none; circuits of other depths were compiled for constraint counts only, and a proof ran at one depth. |
| IM-16 | 새 프로파일 | `PARTIAL` | partially covered | No Move, Python or Rust test covers the recount; the evidence is a record and a fixture manifest. That the old depth 4 fixture still runs rests on a command row of the rs-1 record, which this map re-ran nowhere, and no operational ceremony is specified or tested. |
| IM-17 | 새 프로파일 | `PARTIAL` | partially covered | The v2 fields are produced and refused by the Node client policy, but no Move, Python or Rust test reads a manifest. The K value is UNDETERMINED (the example carries a test fixture), and the profile does not say whether other keys means other K values, other circuit keys or unknown JSON keys. |
| IM-18 | 유지 | `PARTIAL` | partially covered | The verifier and domain are fixed once per show and two shows may pin different manifests; no test runs one show across a profile or verifier change, so the pinned-until-the-end half is shown only by construction. |
| IM-19 | 변경 | `PARTIAL` | partially covered | The rebuild from events is shown at one slot of a localnet run; no test asserts that the full leaf vector is never read or that the secret is absent from the gate call (the consume_private signature has no secret parameter, a builder reading and not a test). |
| IM-20 | 새 프로파일 | `PARTIAL` | partially covered | The extended definitions are a separate file used by the localnet drivers to decode live objects; no unit test pins their field layout to the Move structs, and that the reference decoder is unchanged rests on the command rows of the rs-1 record, with nothing under reference/v0.3-rc1 cited here. |
| IM-21 | 변경 | `PARTIAL` | partially covered | The on-chain currency check reads the page. No client-side currency check of the extended profile exists in the cited layers: the localnet drivers only snapshot page generations for the model comparison, and the independent client of the reference profile lies under reference/v0.3-rc1, which this map does not cite. |
| IM-22 | 새 프로파일 | `PARTIAL` | partially covered | The extended tests, drivers and runners are separate files and the rs-1 record lists the reference suite passing as unchanged; no test asserts that the old localnet and ZK regression files are unmodified. |
| IM-23 | 새 프로파일 | `COVERED_MODEL_OR_MEMORY` | sufficiently covered, model or in-memory only | none; that the mock was not edited is shown only by the diff rows of this node record. |
| IM-24 | 새 프로파일 | `PARTIAL` | partially covered | That this document is the extension contract is a statement about documents with no executable content; only the still-present sentence and the mock test that enforces it are cited. |
| IM-25 | 손대지 않음 | `UNCHANGED_BY_DESIGN` | untouched by design; unchanged-file evidence only | none; the sentences are present at the base, and their not being edited by this node is shown only by the empty diff rows of the record. |
| IM-26 | 손대지 않음 | `PARTIAL` | partially covered | The constants and the locked blobs are shown unchanged and the new crates route above them; the separate approval named by the sentence is a decision matter outside executable evidence, and this map does not read or assess it. |
| IM-27 | 새 프로파일 | `COVERED_LOCALNET` | sufficiently covered | none; the manifest is a single-party local fixture and pins no operational Verifier ID. |
| IM-28 | 변경 | `COVERED_LOCALNET` | sufficiently covered | none |
| IM-29 | 유지 | `PARTIAL` | partially covered | Two events per issue are counted; no test reads the slot or generation values of an Issuance event, and the section 6 arithmetic that two events per issue fit the ceiling is not asserted by any test (MAX_BUNDLE_CHAIN stays UNDETERMINED). |
| IM-30 | 손대지 않음 | `UNCHANGED_BY_DESIGN` | untouched by design; unchanged-file evidence only | none; the wiring of the new-profile tests is recorded by the rs-1 and rs-2 records, and the two checker lines this node adds wire a document check, not a new-profile test. |

Totals: 13 sufficiently covered (10 + 3), 15 partially covered, 0 not covered, 2 untouched by design.

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** Every row not listed under B: the cited tests and files show what the policy sentence says, as far as the profile defines it.

**B. Contract undefined (characterizations and remaining uncertainty; nothing amended).**

1. IM-11 and IM-17 say "상한 5". Read as row 5 of the section 4 ceiling table, not the number 5. K stays UNDETERMINED; `manifest-v2.example.json` carries `rootHistoryK: 4` as a test fixture and is quoted as such. The profile does not say what "other keys are rejected" (IM-17) covers.
2. IM-08: `refund_apply` emits `RefundDutyRequested`; the reference `rights.move` already emitted it. The profile does not say whether such an event counts as a new refund obligation.
3. IM-30: `protocol.yml` already holds the `rights-scale` job added by the RS-1 and RS-2 nodes (the rs-2 record states it touched no `timeout-minutes`). This node adds two checker lines to the stdlib step; they are a document-check wiring, not the new-profile test wiring that IM-30 assigns to RS-1 and RS-2, and no `timeout-minutes` changed (both remain 30).
4. IM-26: the separate approval of RS-3b and Track K v5 is a decision matter; the map cites the constants, the locked blobs test and the new crates, and does not assess the approval.
5. The impact table has no owner column. Rows IM-03, IM-04, IM-08, IM-14, IM-18, IM-19, IM-20, IM-21, IM-22 and IM-24 name no owner in the profile, so their owner cell is the reserved literal `none stated in profile`. `docs/status/RS0_REVIEW_PACK.md` section 1 may hint at owners but is not binding and was not used.
6. IM-23 and IM-24 are evidenced from `reference/booking_resale_admission/test_mock_gates.py`, so the checker's Python column also allows `reference/booking_resale_admission/test_*.py`; its unchanged-file column also allows top-level `docs/*.md`, for the historical 16-slot sentences of IM-25.
7. "Untouched" rows rest on the unchanged file at the base and on this record's own diff rows; a citation into `reference/v0.3-rc1/**` is forbidden by the checker, so nothing there is cited.

**C. Explicit contract violations.** None found. No cited body contradicts a treatment word, so no row is marked as a violation and the profile was not edited.

## Commands actually run and results

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | both `9eb6b9ff24c6ca5825a3d999c81932a38ae79f02` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, both times |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0: `rs im evidence map ok: rows=30 expected=30 citations=175 COVERED_LOCALNET=10 COVERED_MODEL_OR_MEMORY=3 PARTIAL=15 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0: 15 negative controls detected (removed id, duplicated id, dangling path, dangling symbol, unknown status, altered treatment word, treatment word outside the profile words, NOT_COVERED with a citation, PARTIAL with an empty missing cell, owner not in the profile, citation under `reference/v0.3-rc1`, UNCHANGED_BY_DESIGN on a changed row, COVERED on an untouched row, wrong cell count, wrong counts line) plus the Move and Python symbol positive controls; ends `self-test: pass` |
| the seven existing stdlib checkers of the workflow step, each plain and with `--self-test`: `check_status_register`, `check_rs_profile_traceability`, `check_read_model_source_map`, `check_docs_index`, `check_i12_proof_ids`, `check_delegation_layer_matrix`, `check_rs_predicate_evidence_map` | all 14 invocations exit 0 (`rows=23 expected=23` for the predicate map; `docs index ok: scanned=160 indexed=125 allowlisted=35`) |
| `git diff --stat origin/main -- reference/v0.3-rc1 runtime .aiops docs/tasks docs/contracts docs/decisions` | empty output |
| `git diff -U0 .github` | exactly two added lines, `python3 scripts/check_rs_im_evidence_map.py` and the same with `--self-test`, at the same 10-space indent as the lines above them; no other workflow line changed (both `timeout-minutes: 30` untouched) |
| `git status --short` | `M .github/workflows/protocol.yml`, `M docs/README.md`, and the three new paths; nothing else |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | exit 0: `Ran 115 tests ... OK` (Python model tests; no Sui, ZK or Node involved) |

Not run: the Sui, ZK, localnet and Node jobs, `ktx-kernel.yml`, `cargo test`, `cargo clippy` and `cargo fmt` (no `runtime/` byte changed), and any YAML linter.


## Explicit non-claims / what was not tested

- Not an Astra review or acceptance; no register row changed; no grade is raised and the operational count stays 0.
- No Sui, ZK, Move, localnet, Cargo or Node run was made. The Move, ZK, localnet and Node jobs of `protocol.yml` and `ktx-kernel.yml` were not run locally.
- The checker proves only that a cited name exists in a file of an allowed path, not that the test asserts the predicate. Each status is a builder reading of the cited bodies.
- No YAML linter ran; the workflow edit was reviewed by `git diff` only.
- No production durability, distributed fencing, chain finality or production readiness is claimed or inferred.

## Remaining uncertainty and follow-up candidates

- The 15 `PARTIAL` rows each name their gap; the owners in the profile decide whether to close them. Candidates: a test of the read-only borrow of IM-03, an Issuance field assertion for IM-04 and IM-29, a client-side currency check for IM-21, a BCS layout pin for IM-20.
- Exact-head KTX and KIX protocol CI results are not known; they are for the pull request closure report.
