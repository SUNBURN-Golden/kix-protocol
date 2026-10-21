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

## PR fix round 1 — regex opacity

Task input: supervisor-supplied blocking review of PR #249 at
`0ce672ec6a5c608676f90a1c5cbdd37fa4d6095f`. The branch remains
`agent/kix-plan-rs-offline-evidence-citation-check`; cached `origin/main` is
`93cec6aaf12f22bf8aefc0453fe545b6bd38b819`, equal to the recorded base.
The supervisor again prohibits network actions, commits, pushes and comments.
No fetch was attempted; remote freshness is unverified. The fix is uncommitted,
so there is no new final task head or exact-head CI result.

The blocking finding is confirmed, not rebutted. Before editing, importing only
the Python checker and passing the reviewer's JavaScript as an in-memory string
made `literal_test_names` return `{'ghost'}` for
`const pattern = false || /;test('ghost', x);/;`. No JavaScript was executed.

Coverage before this fix was **partial**: the existing regex control followed
`=` and lacked an apparent statement boundary inside the regex. It did not cover
the two-pipe token context. Other task requirements retain their existing
coverage mapping above.

The bounded lexer now fails closed for the whole source when a slash outside
its supported regex-opener contexts has another slash before a physical line
terminator. This prevents an unsupported regex's body from becoming declaration
tokens. A lone slash before the line terminator cannot open a valid JavaScript
regex, so existing single-division expressions remain supported. This is
deliberately conservative: chained division or a division followed by a slash
in a comment on the same line can also cause all citations from that file to
be rejected. It remains a bounded recognizer, not a JavaScript parser.

New in-memory controls cover the reported `||` expression and related `&&`,
bitwise OR, AND and XOR contexts. They require whole-source rejection even
with a genuine test appended, and require the specific supplemental diagnostic
`::ghost: test name not declared`. Positive fixtures retain real declarations
alongside division and opaque assignment/nullish-context regexes containing
fake statement-boundary test calls; those fake names are separately rejected.

Only these paths change in this fix round:

- `scripts/check_rs_im_evidence_map.py`
- `validation/2026-10-22-plan-rs-offline-evidence-citation-check/README.md`

The map, docs index, contracts, workflows, `.aiops/`, `docs/tasks/`, runtime and
historical records remain byte-identical to the reviewed head. A raw Git-blob
comparison checks all 911 tracked files outside this two-file allowlist,
including all 108 protected reference files. Both locked blobs match the
required hashes in the table above before and after the code change.
Primary statuses/counts, supplemental/localnet separation, IM-19's gate-secret
gap, policy values and decision owners are unchanged.

| Check actually run | Result |
|---|---|
| Pre-fix in-memory reviewer reproduction, default Python 3.13.5 | Confirmed false declaration `ghost`. |
| Development `python3 scripts/check_rs_im_evidence_map.py --self-test` | First attempt rejected existing spend-suite divisions; second revealed a fixture incorrectly classifying the already opaque `??` context. Both corrected; third attempt passed. |
| `python3 scripts/check_rs_im_evidence_map.py` under Python 3.12.15 | Exit 0; 30 primary rows, 179 primary citations; 3 supplemental rows, 27 citations. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` under Python 3.12.15 | Exit 0; original mutations and new regex controls passed. |
| `python3 scripts/check_docs_index.py` under Python 3.12.15 | Exit 0; scanned=197 indexed=162 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` under Python 3.12.15 | Exit 0; self-test passed. |
| All 26 commands extracted unchanged from the workflow's `Stdlib offline document checks` block | Exit 0 each under Python 3.12.15. Per-command results/logs: `/tmp/rs-offline-citation-fix-round-1/`. |
| Raw blob comparison against `git ls-tree -rz HEAD`; `git hash-object` on both locked files | 911 files unchanged outside the fix allowlist; 108 protected reference files identical; both required lock hashes match. |
| `git diff --check` | Exit 0. |

All Python checks set `PYTHONDONTWRITEBYTECODE=1`. No CI failure log was supplied;
neither workflow was queried or triggered. KTX and KIX exact-head run IDs,
statuses and conclusions for the uncommitted fix are unavailable. Updated
independent review and exact-head CI remain supervisor delivery gates. No merge
or post-merge verification occurred. Rust and cited Node/Move suites were not
rerun for this Python-only fix. This round claims citation integrity only;
it supplies no test-execution, independent-verification or production claim.
No new protocol-contract violation, undefined protocol behavior or product
decision was introduced. Local readiness is a handoff to the supervisor.

## PR fix round 2 — template interpolation

Task input: supervisor-supplied blocking review of PR #249 at
`e228e57c0f55b1e8d6514b1ef5257da2387858ff`, on
`agent/kix-plan-rs-offline-evidence-citation-check`. Cached `origin/main` remains
`93cec6aaf12f22bf8aefc0453fe545b6bd38b819`, equal to the recorded base; remote
freshness is unverified because the supervisor prohibits network actions.
No fetch, commit, push, GitHub action or comment was performed. This fix remains
uncommitted above the reviewed implementation head; its final task head is
unassigned and belongs to the supervisor's delivery process.

The blocking finding is confirmed. Before editing, importing only the Python
checker and passing the reviewer's source as an in-memory string returned
`{'ghost'}` for this JavaScript, which contains no test call:

```javascript
const text = `${`;test('ghost', x);`}`;
```

Existing template coverage was **partial**: a plain opaque template was covered,
but nested/interpolated templates were not. The added regression failed on the
reviewed parser before the fix. All other requirements retain the coverage
mapping above, including the prior regex-opacity controls.

The template token now accepts only non-interpolated templates: escape pairs,
ordinary characters and dollar signs not followed by an opening brace. An
unescaped `${` prevents the token from matching; the existing unsupported-literal
guard then rejects the whole source at its opening backtick. An inner backtick
cannot expose template contents as code. This deliberately fails closed for
all template interpolation, even when genuine test declarations occur elsewhere
in the file. Supporting interpolation later would require an explicit bounded
grammar update; this fix does not introduce a JavaScript parser or execute JS.
Neither cited suite currently contains template interpolation, so all existing
citations still pass.

New in-memory controls cover the exact reviewer example, an interpolated call,
deeper nested templates and an escaped backslash immediately before real
interpolation. Each is checked both alone and with a genuine test appended,
requiring whole-source rejection and the specific supplemental diagnostic
`::ghost: test name not declared`. Positive fixtures retain real test names
beside opaque templates with escaped interpolation, escaped backticks and plain
dollar signs; fake names inside those templates are separately rejected.

Only these paths change in round 2:

- `scripts/check_rs_im_evidence_map.py`
- `validation/2026-10-22-plan-rs-offline-evidence-citation-check/README.md`

The map and docs index remain byte-identical to the reviewed head. All 911
tracked files outside this two-path allowlist match their starting bytes and
HEAD blobs, including all 108 files under `reference/v0.3-rc1/`. Both locked
kernel blobs match the required hashes above before and after this fix, also
matching the unchanged index. Runtime, contracts, workflows, `.aiops/`, task
inputs and historical records are unchanged. Primary statuses/counts and
supplemental/localnet separation, IM-19's gate-secret gap, all policy values and
named decision owners are preserved.

| Check actually run | Result |
|---|---|
| Pre-fix in-memory reviewer reproduction, default Python 3.13.5 | Confirmed false declaration `ghost`; no cited code executed. |
| Regression-first `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 1 as intended: `unsupported template interpolation accepted: reviewer nested template`. |
| Post-fix development `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; new template controls, previous regex controls and existing mutations pass. |
| `python3 scripts/check_rs_im_evidence_map.py` under Python 3.12.15 | Exit 0; 30 primary rows, 179 primary citations; 3 supplemental rows, 27 citations. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` under Python 3.12.15 | Exit 0; all positive controls and diagnostic-specific mutations pass. |
| `python3 scripts/check_docs_index.py` under Python 3.12.15 | Exit 0; scanned=197 indexed=162 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` under Python 3.12.15 | Exit 0; self-test passes. |
| All 26 commands extracted unchanged from the workflow's `Stdlib offline document checks` block | Exit 0 each under Python 3.12.15; per-command logs and results in `/tmp/rs-offline-round2/`, outside delivery. |
| Inline snapshot/HEAD-blob comparison; `git hash-object` on locked files | 911 excluded tracked files unchanged; 108 protected reference files match; both required lock hashes match worktree/index; branch, HEAD, cached main and index unchanged. |
| `git diff --check` | Exit 0. |

All Python checks set `PYTHONDONTWRITEBYTECODE=1`; no tools or dependencies were
installed. The docs-index check and self-test are repeated after this append.
No CI failure log was supplied. KTX and KIX exact-head workflow run IDs, statuses
and conclusions for the uncommitted fix remain unavailable; neither workflow
was queried or triggered. Updated non-author review and exact-head CI remain
supervisor delivery gates. No merge or post-merge verification occurred.

No protocol-contract violation, undefined protocol behavior, product decision or
scope expansion was introduced. Rust and cited Node/Move/localnet/proving suites
were not rerun for this Python-only correction. This record claims citation
integrity only, without test-execution, independence or production assurances.
Local readiness means handoff to the supervisor, with no merge-readiness claim.

## PR fix round 3 — hashbang comment opacity

Task input: the supervisor-supplied node specification and blocking review of
PR #249 at `5100fdc4639cff1ff062f5c222076daa85fcc3dd`, on
`agent/kix-plan-rs-offline-evidence-citation-check`. No issue or current task
document under `docs/tasks/` exists for this node. Cached `origin/main` is
`93cec6aaf12f22bf8aefc0453fe545b6bd38b819`, equal to the recorded base.
The supervisor prohibits network actions, so the AGENTS.md §1 fetch was omitted;
remote freshness remains unverified. The implementation head remains the SHA
above. This correction is uncommitted; the final task head is unassigned.

The blocking finding is confirmed and fixed. The regression added before the
lexer change failed because `#!node;test('ghost', x);` incorrectly satisfied a
`::ghost` citation: the required `::ghost: test name not declared` diagnostic
was absent. No JavaScript or cited dependency was imported or executed.

Existing coverage was **partial**: `supplemental_self_test` already exercised
line/block comments, strings, templates and regexes, but had no hashbang control.
The remaining requirements retain the coverage mapping above. The comment token
now recognizes `#!` only at source offset zero (`\A`) and consumes its contents
through EOF or the first JavaScript line terminator. Its body never becomes
executable tokens. Six in-memory controls require the exact missing-test
diagnostic for EOF, LF, CR, CRLF, U+2028 and U+2029 endings. For every nonempty
ending a positive map fixture also requires a genuine test immediately after
the comment to remain citeable. Prior regex/template regressions still pass.

The complete changed-path list for round 3 is:

- `scripts/check_rs_im_evidence_map.py`
- `validation/2026-10-22-plan-rs-offline-evidence-citation-check/README.md`

All 911 tracked files outside this two-path allowlist match their HEAD blobs,
including all 108 files under `reference/v0.3-rc1/` (tree
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`). Both locked kernel blobs match
their required hashes in the preservation table above before and after work;
the unchanged index matches too. The map and docs index, runtime, contracts,
workflows, `.aiops/`, task documents and historical records are unchanged.
Primary statuses/counts, supplemental/localnet separation, IM-19's gate-secret
gap, policy values and named owners are preserved.

| Command actually run | Actual result |
|---|---|
| Regression-first `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 1 as intended: hashbang EOF fixture missed `::ghost: test name not declared` (found no problems). |
| Post-fix `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; six new diagnostic controls, positive controls and prior regressions pass. |
| `python3 scripts/check_rs_im_evidence_map.py` under Python 3.12.15 | Exit 0; 30 primary rows, 179 primary citations; 3 supplemental rows, 27 citations. Primary statuses remain 11 localnet, 4 model/memory, 13 partial, 2 unchanged. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` under Python 3.12.15 | Exit 0; self-test passes. |
| `python3 scripts/check_docs_index.py` under Python 3.12.15 | Exit 0; scanned=197 indexed=162 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` under Python 3.12.15 | Exit 0; self-test passes. |
| All 26 commands extracted unchanged from the workflow's `Stdlib offline document checks` block | Exit 0 each under Python 3.12.15. |
| Inline Git-blob hash comparison; `git hash-object` for both locked files | 911 excluded tracked files and 108 protected references match HEAD; both required locks match worktree/index; branch, HEAD, cached main and index unchanged; no nonignored untracked paths. |
| `git diff --check` | Exit 0. |

Python checks used `PYTHONDONTWRITEBYTECODE=1`; no dependencies were installed.
The docs-index check/self-test and preservation checks are repeated after this
append. No CI failure log was supplied. KTX and KIX exact-head CI run IDs,
statuses and conclusions for this uncommitted correction are unavailable;
neither workflow was queried or triggered. Updated non-author review and
exact-head CI remain supervisor delivery gates. No commit, push, comment,
GitHub action, branch/tag mutation or merge occurred; post-merge CI is inapplicable.

No protocol-contract violation, undefined protocol behavior, new policy value
or scope expansion was found. The recognizer remains bounded rather than a
JavaScript parser. Rust and cited Node/Move/localnet/proving suites were not
rerun for this Python-only fix. This is citation-integrity evidence only,
without test-execution, independence or production claims. Local readiness
means handoff to the supervisor; no merge readiness is claimed.
