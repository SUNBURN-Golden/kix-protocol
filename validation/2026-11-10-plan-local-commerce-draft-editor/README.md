# Local commerce draft editor — builder evidence

Node `plan-local-commerce-draft-editor`. Task input is the supplied user node and
design plan (planner run 1794283920); no issue or docs/tasks document exists.
Not ASTRA program mode. Branch `agent/kix-plan-local-commerce-draft-editor`.
Initial HEAD/base and cached origin/main:
`347ce4429987164caac879591ed36251a7a9fcaa`. Initial working tree was clean.
Fetch omitted under the explicit supervisor no-network rule; remote freshness is
unverified. No base/ref changes. Implementation and final task head remain
unassigned because the supervisor owns commits/publication. No merge occurred.

The editor adds ordered draft display, positional line/discount replacement,
exact decimal line replacement and explicit version/expiry entry. Every edit
attempt invalidates draft and active quote/plan/refund/selection before display
and input. Detached candidates publish only on complete canonical encoding.
Stored legs and historical exchange bytes are retained. Editing submits nothing;
all calculations use the existing client and unchanged frozen driver with
explicit confirmation. No auto-repair, clock, defaults or retry is introduced.

[Coverage map](coverage-map.md) records existing coverage and gaps before changes.
Six new source-informed interface tests exercise full subprocess parity with
complete caller-authored inputs; zero-based positions and duplicate IDs; complete
metadata and ordered display; exact amounts above 2^53; preserved literal invalid
inputs; every incomplete edit prompt; failed edits; identical replacements;
retained legs/history; invalidated line selections; launch counts and decline;
driver rejection parity and terminal malformed-reply fencing.

[Command table](commands.md) and [command records](command-results.jsonl) contain exact argument arrays, working
directories, stdin fixture paths, exit codes and durations. Per-command stdout
and stderr are retained alongside the [reproducible recorder](reproduce-run-check.py.txt).
The four edit transcripts cover journey, precision, replacement/abandonment and
intentional refusal boundaries. They contain synthetic caller values only.

The [before](preservation-before.json) and [after](preservation-after.json) preservation manifests record
both locked Git blobs and all protected reference file SHA-256 values.
The preservation script also checks every non-task tracked file against its
index blob, unchanged refs, Python syntax and git diff whitespace.

Product policy remains UNDETERMINED — Astra/User; legal/accounting treatment
UNDETERMINED — User/designated advisers. CALCULATION_ONLY;
refund executionAuthorized=false. No immutable quote, calculation semantics,
booking confirmation, protocol command or stage-6 change. No money, PG/bank/KYC,
public endpoint, Sui, storage engine, coin/TIX, secrets or production runtime work.
No claims of financial independence, production readiness, distributed fencing,
durability, external exactly-once, finality or legal compliance.

Contract violations found: none. No new contract-undefined semantics introduced;
the policy uncertainties above remain. Independent non-author A2 exact-head
review and exact-head KTX/KIX completed/success CI remain separate pending gates.
CI run IDs/status/conclusions unavailable, not passed. Post-merge main CI and
final-merge blob verification are not applicable. Local READY is a supervisor
handoff state, not merge-ready.

## Verification and deviations

All available applicable checks passed. The initial focused editor run passed
6 tests in 15.074 s. The complete commerce client/console suite then passed
50 tests in 59.470 s, including an additional case discarding a buffered decimal
conversion when final encoding fails. Frozen assets/commerce/driver/canonical
tests passed 44 tests in 0.406 s. No failing test runs or source fixes were needed.
Commerce verification passed with externalCalls=0. The journey, precision and
replacement transcripts exited 0; boundaries exited 1 as expected with
DUPLICATE_LINE, UNKNOWN_DISCOUNT_LINE, MIXED_QUOTE_ASSETS and
DISCOUNT_EXCEEDS_PAYABLE. All four transcript stderr files are empty.

Seven document/OpenAPI/CI checker scripts passed in both normal and self-test
modes (14 checks). Runtime architecture verification passed; its 7 regression
tests passed. Cargo formatting passed. Offline kernel/workspace tests and both
Clippy commands exited 101 before compilation because the provisioned registry
lacks `bcs`. These four checks are UNAVAILABLE, not passes or source failures.
No network provisioning or retry was attempted. Rust 1.98.1 used its provisioned
toolchain bin directory first on PATH, CARGO_NET_OFFLINE=true,
CARGO_HOME=<worktree>/.local/draft-editor/cargo and
CARGO_TARGET_DIR=<worktree>/.local/draft-editor/target. The existing registry was
copied locally to keep writes within the worktree. Runtime code was untouched;
no runtime compilation/test claim is made.

Broader socket-free booking discovery passed **929 tests in 183.312 s**, with the
single HTTP exclusion below. Both required locked blobs match before and after;
all 108 protected reference files and 2,849 non-task tracked files remain
byte-identical. The script also verified unchanged HEAD/cached origin/main/branch,
valid changed Python syntax and clean diff whitespace. The
[complete changed-path inventory](changed-paths.txt) includes all evidence files;
[implementation digests](implementation-sha256.json) identify the tested source,
tests, guides and four transcripts.

Verification deviations are the explicitly prohibited fetch, unavailable offline
Rust dependency and the documented HTTP exclusion. No implementation/design or
scope deviation. Remaining work belongs to supervisor delivery: assign the final
commit, obtain non-author A2 review and exact-head KTX/KIX CI; provision the
missing dependency in an authorized environment. Local handoff is READY, not
merge-ready. No merge SHA or post-merge CI applies.

No Git mutations, GitHub/network actions or shell background jobs were run. Read-only
inspection used pwd, git status/rev-parse/branch/hash-object/diff/ls-files, rg,
cat/sed, tool and local-cache inspection. Git fetch was explicitly prohibited.
Applicable checks use provisioned Python 3.12, -B and PYTHONDONTWRITEBYTECODE=1
with inherited PYTHONPATH removed. Runtime code is untouched; offline Rust
checks are attempted without downloading missing dependencies.

Broader booking discovery reuses the predecessor socket-blocking runner and
excludes exactly
`test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`.
The runner asserts that single exclusion and unique test IDs. Its audit hook
rejects socket events in the parent and inherited child environments. Tests that
replace child environments are outside that inherited-hook claim. The HTTP
behavior is unchanged and not verified here. Reproduce with the retained
socket-free runner and sitecustomize guard under `.local/draft-editor/`.
