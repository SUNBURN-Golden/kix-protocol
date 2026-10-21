# RS supplemental offline citation integrity

Node: `plan-rs-offline-evidence-citation-check`, implemented 2026-10-22.
Task input: supervisor-supplied node specification and read-only design plan in
this session; no issue or `docs/tasks/` document was supplied. Not ASTRA program
mode. Audit floor A2; no publication or merge authority.

## Identity and scope

Starting branch: `agent/kix-plan-rs-offline-evidence-citation-check`.
Starting HEAD and cached `origin/main` both equal
`93cec6aaf12f22bf8aefc0453fe545b6bd38b819`; initially clean, no local base delta.
The supervisor prohibits all network actions, so `git fetch origin main` was
not run (AGENTS.md §1 deviation). Remote freshness remains unverified.
Implementation/final task head is unassigned: the supervisor owns commits and
GitHub. No merge commit, exact-head CI or post-merge evidence exists here.

Changed paths:

- `scripts/check_rs_im_evidence_map.py`
- `docs/status/RS_IM_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-22-plan-rs-offline-evidence-citation-check/README.md`

## Existing coverage mapping and added evidence

| Requirement | Existing coverage before editing | Added evidence |
|---|---|---|
| Primary identifiers, treatments, statuses, owners, counts and original symbols | Sufficient: existing `self_test` mutations in `scripts/check_rs_im_evidence_map.py` | Reused unchanged; supplemental rows never enter primary counts or citation columns. |
| Docs index | Sufficient: `scripts/check_docs_index.py` and its self-test | Exact-file record link in the existing 2026-10-22 section. |
| Unsafe paths and missing files | Partial: primary checker already rejects traversal, protected references and missing files | Separate exact offline allowlists; reject URLs, backslashes, absolute/traversal and unsupported paths before reading; resolved-path fences, including simulated symlinks. |
| Supplemental grammar, Node literal test names and record headings | Not covered | In-memory positive fixtures and diagnostic-specific mutations in `supplemental_self_test`; both suites, quoted/escaped names, comments/strings/templates/regex, nesting, malformed cells and members, unknown IMs, duplicate/missing identifiers, missing files/names/headings. |
| Supplemental/localnet isolation | Not covered | Remove IM-15's primary localnet citations while retaining its valid supplemental evidence; require the existing COVERED_LOCALNET diagnostic. Compare all primary rows across supplemental mutations. |

The table has three supplemental identifiers, 23 full literal test-name citations
(16 reconstruction, 2 IM-14 spend, 5 IM-15 spend) and four record-heading citations
(27 citations total). The checker reads source text using the standard library;
it does not execute or import cited code. The bounded recognizer supports the
existing suites' direct top-level quoted `test(...)` statements; computed names,
nested tests and modifiers are outside this citation grammar.

## Preservation and non-claims

Both locked blobs matched before editing and after verification, in working-tree
bytes and the Git index:

| Locked file | Required Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The preservation check compared all 909 tracked files outside the four-path
allowlist to their starting Git blobs: byte-identical, including all 108 files
under `reference/v0.3-rc1/`. Its starting tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Both locked blobs match before/after.
The entire primary map section (including its Counts line) is byte-identical;
existing content changes only the designated reading-note sentence. The diff
and nonignored untracked paths equal the four delivery paths. HEAD, branch and
cached `origin/main` are unchanged.

Primary rows, counts, open gaps and decision owners are preserved. IM-19 remains
PARTIAL, including its missing gate-secret assertion. Public-tree retention and
operational parameters stay UNDETERMINED with Astra; IssuerCap stays OPEN.
Operational count remains 0. Ordinary Markdown links remain ordinary links;
the reading note retains its historical-snapshot explanation.

This work establishes citation integrity only, not test execution, assertion
adequacy, independent verification, circuit correctness, transport completeness,
localnet success, durability, legal compliance or production readiness. No Node,
Move, Sui, proving or ceremony step is needed or run. No runtime, contract,
workflow, program plan, task input, historical record or protected file is edited.

## Commands actually run and results

All final checks run from the repository root. Verification PATH begins with
`/workspace/venvs/film312/bin`: Python 3.12.15, matching the workflow's 3.12
series. Cargo/Rust are 1.98.1. Python uses `PYTHONDONTWRITEBYTECODE=1` and Cargo
uses `CARGO_NET_OFFLINE=true`; cached tools/dependencies only, no bootstrap,
installs, network or background jobs. The 26 commands in the workflow's
`Stdlib offline document checks` run block were extracted unchanged and run
sequentially, after the four narrow map/index checks passed. KTX architecture,
kernel and broader workspace checks followed. Local logs and command/result
JSON are under `/tmp/rs-offline-citation-check/` (not delivery artifacts).

Initial development under default Python 3.13.5: the map check passed; the
first self-test exited 1 on the escaped-backslash positive control, fixed by
validating/decoding whole escape pairs. The second exited 1 because the new
localnet-isolation fixture targeted IM-01, which is COVERED_MODEL_OR_MEMORY;
the fixture now removes IM-15's localnet citations while retaining IM-15's
supplement. The next self-test passed. These are checker/fixture development
failures, not failures of the cited Node suites (which were not executed).
No final verification command failed or needed a retry.

| Command | Exit | Actual result |
|---|---|---|
| `python3 scripts/check_rs_im_evidence_map.py` (initial default Python) | 0 | 30 primary rows, 179 primary citations; 3 supplemental rows, 27 citations. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` (development, default Python) | 1, 1, then 0 | Escaped-backslash control and IM-01 fixture corrected as described above; final development self-test passed. |
| Narrow `python3 scripts/check_rs_im_evidence_map.py` and `--self-test` | 0 each | Map and in-memory self-tests pass under Python 3.12.15. |
| Narrow `python3 scripts/check_docs_index.py` and `--self-test` | 0 each | scanned=197 indexed=162 allowlisted=35; self-test passes. |
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=300 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=197 indexed=162 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2; supplemental offline evidence ok: rows=3 citations=27 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | Self-test: pass; expected mutation diagnostics detected. |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | 0 | 7 tests; OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0 | 9 test targets; 78 passed, 0 failed, 0 ignored. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0 | 42 test targets; 257 passed, 0 failed, 0 ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0 | Clean; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Clean; no output. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | 0 | Normal dependency tree: kix-kernel -> kix-types only. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | 0 | All three hashes recorded in local log; starting-blob preservation checked separately. |
| `python3 --version`, `/workspace/venvs/film312/bin/python3 --version`, `cargo --version`, `rustc --version` | 0 | Default Python 3.13.5; verification Python 3.12.15; Cargo/Rust 1.98.1. |
| `git rev-parse HEAD`, `git rev-parse origin/main`, `git branch --show-current`, `git status --short` | 0 | Starting SHA and branch above; initially clean. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | 0 | Both required blobs match before work; final preservation command repeats and checks index too. |
| `git ls-tree HEAD reference/v0.3-rc1` | 0 | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `python3 /tmp/rs-offline-citation-check/verify_preservation.py` | 0 | 909 excluded tracked files byte-identical, including 108 protected reference files; both locks match worktree/index; primary map/counts unchanged; four-path allowlist exact; refs unchanged. |
| `git diff --check` | 0 | Clean. |

The inline lexer diagnostic used `ast` and imported only the checker to inspect
in-memory tokens; it identified that an escaped backslash pair was rejected.
No cited client module or dependency was imported. Read-only `cat`, `sed`, `rg`,
`git diff` and local Git inspection established the inputs and preservation
baseline; no remote freshness or historical CI result is inferred.
The docs-index check and self-test passed again after this record was completed.

## Deviations and remaining gates

No design-scope deviation, explicit contract violation or new contract-undefined
characterization was found. The bounded static recognizer adds regex opacity
and simulated symlink fences to keep text/path handling conservative; it is
not a general JavaScript parser and does not assess test assertions. Future
changes to suite syntax or allowed records require an explicit checker update.
No scope expansion or new resources/policy decisions are needed. The fetch/network
restriction above is imposed by the supervisor. Cached tools were used instead
of bootstrap; unrelated chain/localnet/proving/ceremony and other protocol
integration steps were not run, as required by the node's citation-only scope.
The full applicable stdlib document step and local runtime boundary equivalents
passed; they do not substitute for either exact-head workflow. No commit, push, PR, issue,
comment, branch/tag mutation or merge is performed. No GitHub action is taken.

| Delivery gate | Head / run ID | Status / conclusion |
|---|---|---|
| KTX kernel verification | Final head unassigned / unavailable | Not run or observed; no pass claimed. |
| KIX protocol verification | Final head unassigned / unavailable | Not run or observed; no pass claimed. |
| A2 non-author exact-head review | Unassigned | Outstanding; builder self-tests are not independent review. |
| Post-merge main CI | No merge / unavailable | Not applicable. |

Local completion is a supervisor handoff. Exact-head workflows and required
non-author review remain delivery gates; no merge readiness is claimed.
Final-head CI belongs in the authorized delivery report, outside another
repository commit solely to record the preceding head's CI.
