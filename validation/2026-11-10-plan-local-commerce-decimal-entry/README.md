# Exact decimal commerce console — builder evidence

Node `plan-local-commerce-decimal-entry`; task input is the user-supplied node and
design plan (planner run 1794268560), with no issue or docs/tasks document. Not
ASTRA program mode. Branch `agent/kix-plan-local-commerce-decimal-entry`.
Initial HEAD, base and cached origin/main all equal
`e5b7927bca2ec78a0a6618d4ac3d1d5611a0b95d`; initial worktree clean.
Fetch omitted under the explicit supervisor no-network rule, so remote freshness
is unverified. No base/ref changes. Implementation remains uncommitted; an implementation/final task head for these
changes has not been assigned. The supervisor owns commits and publication. No merge or post-merge CI applies.

[Coverage map](coverage-map.md) was recorded before implementation and tests.
[Before preservation manifest](preservation-before.json) records both required
locked Git blobs and SHA-256 for all 108 protected reference files. The [after manifest](preservation-after.json) matches it exactly. Both locked blobs
match before and after; all 108 protected files and 2,698 non-task tracked files
remain byte-identical. [Implementation digests](implementation-sha256.json) identify
the tested console, interface tests, guide/index and six transcripts.

Implementation adds explicit compose_quote_decimal and compose_legs_decimal
controls through the unchanged isolated AssetSpec and Amount.from_decimal parser.
Complete caller metadata and literal decimal text yield canonical atom strings.
Only complete CE1 candidates publish conversion previews; existing confirmation,
discounts, invalidation, subprocess-only calculations and terminal fencing remain.

New console interface tests cover independent decimal/atom combinations with
identical full exchanges (including requests/results/hashes), precision 0/2/6/18/38,
zero, exact limits, >2^53, invalid metadata/text/precision/overflow, no partial
publication, mixed-asset and aggregate driver refusals, each EOF/decline, and
replacement across modes. Parser arithmetic coverage is reused, not duplicated as
an independent arithmetic model. All tests are source-informed builder evidence.

Six decimal fixtures demonstrate real local quote, split-plan and line-refund
subprocesses plus zero/precision/decline/replacement/refusal boundaries. Per-command
stdout/stderr and [exact commands/results table](commands.md) and [machine-readable exit codes](command-results.jsonl) are retained.

Product policy remains UNDETERMINED — Astra/User; legal/accounting treatment
UNDETERMINED — User/designated advisers. CALCULATION_ONLY; refund executionAuthorized=false.
No booking confirmation, FX, asset approval, new protocol commands, SDK/catalogue,
funds, PG/bank/KYC, Sui, public endpoints, production runtime, secrets, storage
engine or coin/TIX work. No claim of durability, distributed fencing, external
exactly-once, chain finality, legal compliance or production readiness.

Independent non-author A2 exact-head review and KTX/KIX completed/success workflows
remain required after supervisor commit/publication; run IDs/status/conclusions
are unavailable, not passed. No merge-ready claim. Contract violations found: none. No new contract-undefined behavior is introduced;
product policy and legal/accounting treatment remain unresolved as above.

## Actual results and deviations

Python 3.12.15, Node v24.22.1 and the provisioned Rust 1.98.1 toolchain were used.
Python validation used -B and PYTHONDONTWRITEBYTECODE=1 with inherited PYTHONPATH
removed before each command. Commands ran as foreground subprocesses; no background
shell jobs or network/GitHub actions. [Reproducible command recorder](reproduce-run-check.py.txt)
records exact argument arrays, working directories, stdin paths, exit codes and timings
in command-results.jsonl, with per-label stdout/stderr. Read-only inspection also
used git status/rev-parse/branch/hash-object/diff, rg, cat/sed, tool versions and local
cache inspection. Nothing was committed, pushed, rebased, fetched or published.

The initial six-test decimal run had five assertion failures: test expectations used
incorrect unchanged-driver error labels. Correct expectations are ASSET_METADATA_CONFLICT
for same-identity metadata changes, INVALID_ASSET_AMOUNT for aggregate overflow and
EMPTY_PAYMENT_LEG for a zero leg. The corrected six-test run passed, then the complete
44-test commerce client/console suite passed after stronger declared-limit and replacement
coverage. No calculator or product semantics were changed to resolve these failures.
The unchanged frozen asset/commerce/driver/canonical suites passed all 44 tests.

Six real CLI transcripts were executed with --cleanup-timeout 2, stdin from the
corresponding decimal fixture. Journey, free, precision, decline and replacement
exit 0. Boundaries exits 1 as intended for four explicit driver refusals and a local
exponent rejection; all six stderr files are empty. The fractional-asset journey
composes 100.00/200.00/300.00 gross, unchanged FIXED 6000 and BPS 1000 discounts,
300.00/186.00 payment legs, and a selected L2 refund of 16200 atoms via original routes
10000/6200. These are synthetic values, not policy decisions. The precision journey
sends exact 9007199254740993 atoms; free uses explicit zero legs and empty refund routes.

Offline Rust tests and Clippy are UNAVAILABLE (exit 101 before compilation) because
the provisioned registry lacks bcs. This is not a test pass or a source failure.
No network provisioning was attempted. Rust commands used the provisioned toolchain's
bin directory first on PATH, CARGO_NET_OFFLINE=true, CARGO_HOME=.local/decimal-entry/cargo
and CARGO_TARGET_DIR=.local/decimal-entry/target (absolute worktree paths at execution).
The existing registry was copied locally to keep all writes in the worktree.
Formatting passed. Runtime code was untouched; no runtime verification claim.

Broader booking discovery follows the predecessor's socket-free runner, excluding
exactly test_admission_fsm.AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit.
The runner asserts one exclusion and unique test IDs. It installs an audit hook rejecting
socket events in the parent and inherited child environments; existing tests which
replace child environments are outside that inherited-hook claim. The excluded HTTP
behavior is unchanged and not verified here. Reproduce by restoring
[the runner](reproduce-socket-free.py.txt) as .local/decimal-entry/socket_free.py and
[the guard](reproduce-sitecustomize.py.txt) as .local/decimal-entry/guard/sitecustomize.py,
then running python3.12 -B .local/decimal-entry/socket_free.py from the root.
This documented exclusion, unavailable Rust cache and no-fetch local baseline are
verification deviations from the supplied plan; no design or scope deviation.

[Complete changed-path list](changed-paths.txt) includes all evidence artifacts.
Preservation can be repeated with python3.12 -B
validation/2026-11-10-plan-local-commerce-decimal-entry/verify_preservation.py.
Review and both exact-head hosted CI gates remain pending supervisor delivery;
final implementation SHA is not yet assigned. Merge SHA, final-merge blob checks
and post-merge main CI are not applicable. No stale CI evidence is transferred.

The complete booking discovery passed **923 tests in 182.847 s**, with the single
HTTP exclusion described above. All applicable available checks passed. The local
handoff is READY for supervisor commit/review/CI, not merge-ready. Remaining work:
provision the missing offline Rust dependency in the authorized CI environment,
obtain independent A2 review of the exact final head, and require both exact-head
KTX and KIX workflows to complete successfully before any merge proposal. The
supervisor retains Git/GitHub publication and the User retains merge authorization.
