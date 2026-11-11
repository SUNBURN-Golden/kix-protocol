# Receipt replay and gate audit test evidence

Node: `plan-readiness-receipt-audit-tests`. Execution date: 2026-10-23.
Task input: the supervisor's node specification, design plan and owner decision
in this session; no issue or task file under `docs/tasks/` exists for this node.
This is builder evidence, not independent review or merge authorization.

## Starting state and boundaries

- Branch: `agent/kix-plan-readiness-receipt-audit-tests`.
- Starting HEAD/base: `26f1b9535db24a6b2e9c28753f561d4d6a271815`; clean worktree.
- Locally cached `origin/main`: `f4df0d8ce0253e7b9755f7eb77e857b2d49057e0`.
  These differ. No fetch was performed: the supervisor explicitly prohibits all
  network/GitHub actions. The supplied base is preserved without merge or rebase.
  `git rev-list --left-right --count HEAD...origin/main` returned `0 55`;
  `git merge-base HEAD origin/main` is the starting HEAD above.
- Owner decision explicitly permits the checker `self_test` correction alongside
  the four originally authorized paths. No `DECISION_REQUIRED.md` was present.
- Before edits, `git hash-object` matched both locks:
  `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
  `b607996c83a119c349f1cc90469ac1ba82764e20`.

## Existing coverage mapped before adding tests

All unqualified test names below are in `integration_gate/test_http_gate.py`.

| Requirement | Existing coverage | Gap to address |
|---|---|---|
| Original receipt replay without another record | Partial: `test_killed_gate_replays_one_event_and_drops_a_torn_tail`; budget replay in `test_journal_budget_does_not_apply_the_next_command` | Complete receipt equality, byte/count preservation and actual replay audit |
| Checksum-valid wrong receipt digest refuses startup | Not covered: `test_corrupt_journal_and_unknown_schema_do_not_listen` stops at checksum/schema validation | Reach `RECEIPT_MISMATCH` with valid framing and preserve bytes |
| Append failure fences subsequent commands | Not covered at HTTP gate; `readiness/test_faults.py` covers other boundary fault surfaces | Instance-local append failure, divergence response and persistent refusal after restoring append |
| Actual replayed/inactive/diverged audit output | Partial: `test_request_id_is_echoed_and_audited`, `test_budget_rejection_names_the_record_limit_and_omits_the_body`, `test_overload_observation_does_not_queue` | Parse real stderr for all three decisions, four false labels, no body/entry or distinctive body content |
| Existing checksum/schema, budget, drain, loopback behavior | Sufficient: above tests plus `test_drain_keeps_liveness_and_refuses_commands`, `test_loopback_refusal_still_applies_with_a_readiness_directory` | Retain and run combined suite; no duplicate tests |
| Map and index validation | Normal checks exist; checker self-test assumes REC-CORE-COMMIT remains PARTIAL | Create a valid synthetic PARTIAL control before removing its owner; retain all negative checks |
| Recovery decisions and protected paths | Nine OPEN rows and owners; two locked blobs and reference/v0.3-rc1 | Preserve verbatim and compare after work |

## Added evidence

All four new methods are in `integration_gate.test_http_gate.TransportTests`:

| Method | Assertions closing the mapped gap |
|---|---|
| `test_core_receipt_replay_preserves_receipt_and_journal` | Real HTTP commit has the expected core record fields and receipt digest; close/reopen and identical operation return the complete original receipt, one unchanged record and byte-identical journal; actual `replayed` audit |
| `test_checksum_valid_receipt_mismatch_refuses_startup` | Derives a record from a successful HTTP control, changes only its digest, writes via the ordinary store, successfully reopens to prove valid framing/checksum; bounded CLI process exits 2 with RECEIPT_MISMATCH, no listening announcement and no byte change |
| `test_readiness_disabled_call_audits_inactive` | Normal HTTP success without a readiness directory; actual `inactive` audit |
| `test_append_failure_diverges_and_blocks_subsequent_commands` | Live instance's append raises StoreError before writing; HTTP 503 DURABILITY_DIVERGENCE without receipt fields; after patch removal both repeated and new operations receive NOT_READY, /ready fails, bytes/count stay unchanged; actual `diverged` audit |

`assert_journal_audit` parses actual captured stderr after server and request
threads finish. Each target has a unique request ID and exactly one audit line;
all four truth/production labels are explicitly false, body/entry keys are
absent, and distinctive request-body values occur nowhere in captured output.
Audit output is never mocked. The append failure is an injected pre-write
exception, not an OS/disk failure experiment.

The checker change is confined to `self_test`: construct an in-memory PARTIAL
row with a named synthetic gap, recognized owner Astra and recomputed counts;
require this control to validate, then remove its owner for the existing
negative check. Validator semantics and all 23 existing negative checks remain.
The corrected self-test passed against both the original two-PARTIAL map and
the updated zero-PARTIAL map. Only REC-CORE-COMMIT and OBS-AUDIT rows change;
updated totals are EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9.

## Commands actually run and results

Every command below exited 0 unless explicitly stated otherwise. The narrow
tests ran first (four selected methods together); the four individual method
commands also passed. The combined suite then used the unchanged CI entry point.

| Command | Actual result |
|---|---|
| `python3 -m unittest integration_gate.test_http_gate.TransportTests.test_core_receipt_replay_preserves_receipt_and_journal` | 1 test passed |
| `python3 -m unittest integration_gate.test_http_gate.TransportTests.test_checksum_valid_receipt_mismatch_refuses_startup` | 1 test passed |
| `python3 -m unittest integration_gate.test_http_gate.TransportTests.test_readiness_disabled_call_audits_inactive` | 1 test passed |
| `python3 -m unittest integration_gate.test_http_gate.TransportTests.test_append_failure_diverges_and_blocks_subsequent_commands` | 1 test passed |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 86 tests passed |
| `python3 scripts/check_readiness_evidence_map.py` | rows=36 expected=36 citations=183; 27 EXERCISED, 0 PARTIAL, 0 NOT_EXERCISED, 9 OPEN |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | pass; all 23 negative cases detected, including ownerless synthetic PARTIAL |
| `python3 scripts/check_docs_index.py` | scanned=188 indexed=153 allowlisted=35; pass |
| `python3 scripts/check_docs_index.py --self-test` | pass |
| `python3 scripts/check_status_register.py` | pass |
| `python3 scripts/check_status_register.py --self-test` | pass |
| `python3 scripts/check_rs_profile_traceability.py` | pass |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | pass |
| `python3 scripts/check_read_model_source_map.py` | pass |
| `python3 scripts/check_read_model_source_map.py --self-test` | pass |
| `python3 scripts/check_i12_proof_ids.py` | pass |
| `python3 scripts/check_i12_proof_ids.py --self-test` | pass |
| `python3 scripts/check_delegation_layer_matrix.py` | pass |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | pass |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | pass |
| `python3 scripts/check_rs_im_evidence_map.py` | pass |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | pass |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | pass |
| `python3 scripts/check_contract_error_codes.py` | pass |
| `python3 scripts/check_contract_error_codes.py --self-test` | pass |
| `python3 scripts/check_adapter_identity_map.py` | pass |
| `python3 scripts/check_adapter_identity_map.py --self-test` | pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | pass |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | pass |
| `python3 scripts/check_integration_gate_openapi.py` | commands=84; productionEndpoint=false publicHost=false; pass |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | pass |
| `python3 scripts/verify_runtime_architecture.py` | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 78 tests passed, zero failures; doc tests passed (0 tests) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | pass |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | pass |
| Inline Python: `find_problems` and `self_test` for `git show HEAD:docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md` and the working map | Both valid; both self-tests pass |
| Inline Python: compare all OPEN row lines and all map row cells against starting HEAD | Nine OPEN rows/owners byte-identical; changed row IDs exactly REC-CORE-COMMIT, OBS-AUDIT |
| Inline Python: compare protected tracked file bytes with `git show HEAD:<path>` using `git ls-files -z` | 146 files byte-identical: both locks, reference/v0.3-rc1, .aiops, docs/tasks, .github/workflows, docs/contracts |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both exact required blobs listed above |
| `git diff --check` | pass |

The 26 document checker invocations were extracted from the unchanged
`protocol.yml` “Stdlib offline document checks” step and executed sequentially,
without changing any command. KTX equivalents follow `ktx-kernel.yml`; Cargo
uses `--offline` to honor the supervisor's network prohibition. Logs in this
session: `/tmp/kix-receipt-audit-combined.log`,
`/tmp/kix-receipt-audit-doc-checks.log`, `/tmp/kix-receipt-audit-kernel.log`.
No long job was launched in the background.

One verification harness attempt failed before completing its comparison:
newline-delimited `git ls-files` quoted a Korean filename, producing a
FileNotFoundError. Re-running with NUL-delimited `git ls-files -z` passed for
all 146 files. This was a path-parsing error in the ad hoc check, not a product
or test failure. There were no failing product tests or checkers.

## Final paths, state and limitations

Complete changed-path list relative to starting HEAD:

- `integration_gate/test_http_gate.py`
- `scripts/check_readiness_evidence_map.py`
- `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-23-readiness-receipt-audit-tests/README.md`

Implementation/final checkout HEAD remains
`26f1b9535db24a6b2e9c28753f561d4d6a271815`, with the five-path uncommitted
patch above; no new final commit SHA exists. No commit, push, PR, issue, comment,
merge, branch/tag mutation, or GitHub action was performed. Exact-head hosted
KTX CI and KIX protocol CI: run IDs/status/conclusions unverified, not queried.
Merge SHA and post-merge CI are not applicable. READY means local builder
handoff only; it does not mean merge-ready.

Deviations from the conditional design: the owner-authorized checker path is
included, the record uses the actual execution date, and no fetch was performed
under the supervisor's prohibition. The cached main is 55 commits ahead of the
supplied base; no claim is made about tests on that later tree. No stale draft
or DECISION_REQUIRED.md existed to remove. No implementation, contract,
workflow, task input, .aiops file or protected reference file changed.

AGENTS §8: no new explicit contract violation or undefined behavior was found.
The three existing class-B recovery characterizations remain OPEN with owner
Astra; the six held rows and blocked conformance-negative-controls node are
untouched. Remaining follow-up is supervisor publication, exact-head hosted CI,
non-author review and any separately required audit/owner decision.

These source-informed tests use temporary local files and loopback fixtures.
They do not test power loss, OS crash, partial physical writes, hardware fsync
correctness, real provider calls, real funds, public endpoints, Sui, replication,
distributed fencing or production runtime. No production durability, external
exactly-once, chain finality or production readiness claim is made. Heavy Move,
ZK, SDK and backend CI work unrelated to the touched paths was not executed.

## Merge conflict resolution — 2026-10-23

This section records the supervisor-requested merge repair and supersedes the
checkout/handoff state above for this resumed session. Earlier results remain
historical evidence; they are not transferred to the merged worktree.
Task input is the current supervisor message for
`plan-readiness-receipt-audit-tests`; there is no issue or `docs/tasks/` task
file for this node. No new tests or implementation changes were needed.

- Branch: `agent/kix-plan-readiness-receipt-audit-tests`.
- Observed implementation/task HEAD before and after repair:
  `c4287ed94a0bd0295f0452fc4374a45dd661159d`.
- Cached `origin/main` and merge target (`MERGE_HEAD`):
  `f4df0d8ce0253e7b9755f7eb77e857b2d49057e0`.
- Merge base: `26f1b9535db24a6b2e9c28753f561d4d6a271815`.
  The supplied node base differs from the merge target; the existing,
  supervisor-authorized merge brings in main's newer work. No fetch was run
  because the supervisor prohibits network actions. No additional merge,
  rebase, commit, push, abort or external publication was performed.
- Final merge commit SHA does not exist yet; the supervisor commits the merge.
  Hosted KTX and KIX protocol run IDs/status/conclusions were not queried.
  No main merge or post-merge CI is claimed. READY means local handoff only.

Resolution decisions:

- `docs/README.md`: keep every main index link and both conflicting entries;
  place receipt/audit evidence under the existing October 23 heading. Date
  the earlier checker record's prerequisite statement to its own base rather
  than treating it as the current node's disposition.
- `scripts/check_readiness_evidence_map.py`: retain main's entire file
  byte-for-byte. Its synthetic PARTIAL fixture already preserves the node's
  intent, with a positive control, isolated ownerless diagnostic, complete
  runs on supplied/zero-PARTIAL maps, and an injected missing-file fixture.
  The duplicated node fixture is unnecessary; no validator rule is weakened.
- `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`: retain all node coverage
  rows and counts; add a dated merge basis explaining that main now contains
  the sensitivity module. Its column stays `none`, with no new sensitivity
  claim or change to the blocked negative-controls node or OPEN decisions.
- This validation record: append fresh commands/results and preservation
  evidence without rewriting the original execution history.

The four receipt/audit tests and the pre-addition coverage mapping above were
reviewed again and are sufficient for this repair. The tests are byte-identical
to node HEAD. Relative to main, exactly REC-CORE-COMMIT and OBS-AUDIT have
changed table rows. The 36 final rows match node HEAD; all nine OPEN rows and
owners match both parents byte-for-byte. Counts remain 27 EXERCISED, 0 PARTIAL,
0 NOT_EXERCISED, 9 OPEN; the operational count stays 0.

Fresh verification:

| Command | Actual result |
|---|---|
| `python3 -m unittest integration_gate.test_http_gate.TransportTests.test_core_receipt_replay_preserves_receipt_and_journal integration_gate.test_http_gate.TransportTests.test_checksum_valid_receipt_mismatch_refuses_startup integration_gate.test_http_gate.TransportTests.test_readiness_disabled_call_audits_inactive integration_gate.test_http_gate.TransportTests.test_append_failure_diverges_and_blocks_subsequent_commands` | Exit 0; 4 tests passed before combined suite |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0; 100 tests passed, 0 failures |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; 36 rows, 183 citations; 27 EXERCISED, 0 PARTIAL, 0 NOT_EXERCISED, 9 OPEN |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; supplied-map and zero-PARTIAL-map runs passed, including synthetic PARTIAL positive/ownerless controls |
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=214 indexed=179 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; all negative controls detected |
| `python3 scripts/check_status_register.py` | Exit 0 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; synthetic tests only, no host qualification |
| Inline Python preservation/coverage/index/marker checks using `git ls-tree -rz --full-tree MERGE_HEAD`, `git show`, blob hashes and direct byte comparisons | Exit 0; 146 protected files match main; all 56 incoming paths outside node paths match main; checker matches main; tests match node HEAD; map rows and OPEN owners preserved; every main index link retained; no conflict markers in 942 tracked paths |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before repair; both required blobs match; inline Git-blob verification after repair matches worktree and both parents |
| `git diff --check` | Exit 0 |
| `git diff --cached --check` | Exit 0 |
| Inline Python evidence-append harness | Exit 1 before any write: its log-block assertion incorrectly required a trailing newline removed by splitting; record appended directly afterward; no product/test/checker failure |
| `git add docs/README.md scripts/check_readiness_evidence_map.py docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md validation/2026-10-23-readiness-receipt-audit-tests/README.md` | Exit 128: Git metadata is outside the writable sandbox; index.lock creation failed with Read-only file system. No index changes made. Supervisor must stage resolved files before committing |

The 27 commands in the current protocol workflow's Stdlib offline document
checks step were extracted verbatim and all passed, including the four required
map/index invocations. No workflow was edited. Logs from this repair:
`/tmp/kix-receipt-audit-merge-narrow.log`,
`/tmp/kix-receipt-audit-merge-combined.log`, and
`/tmp/kix-receipt-audit-merge-doc-checks.log`.

The complete repair path list is `docs/README.md`,
`scripts/check_readiness_evidence_map.py`,
`docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`, and this validation record.
The supervisor's already-staged incoming main changes are retained; all 56
incoming paths outside the node's allowed paths match main exactly. The node's
original `integration_gate/test_http_gate.py` additions remain unchanged.
Both kernel locks match the required blobs before and after repair:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20` respectively.
`reference/v0.3-rc1/**`, `.aiops/**`, task inputs, contracts and workflows match
the merge target; the reference snapshot also has no diff against node HEAD.

No new contract violation or undefined characterization was found (AGENTS §8).
Existing recovery uncertainties, owners and blocked negative-controls
disposition remain untouched. These local checks do not establish production
durability, power-loss/fsync behavior, provider exactly-once, chain finality,
operational readiness, or an independent review. No Rust source changed;
Cargo, Move, ZK, SDK and backend verification were not rerun for this repair.
Exact-head CI and non-author review remain supervisor follow-up after the
supervisor commits/publishes; no merge-ready claim is made.
