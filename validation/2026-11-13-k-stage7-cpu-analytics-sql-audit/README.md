# k-stage7-cpu-analytics-sql-audit

Builder-authored local evidence for Track K stage 7, roadmap R-11. No issue or
repository task document exists for this node: the supervisor's supplied node
specification, design and 2026-11-13 owner decision are the immutable task input.
This is not an ASTRA program-mode session. No git/GitHub mutation is performed.

Branch: `agent/kix-k-stage7-cpu-analytics-sql-audit`.
Base / initial task HEAD: `f52c58743b2919cbc66ab9c2760ecc76742faca7`.
Cached observed `origin/main`: `1e402787dd44300cf278adcd3eb70d7f5d2ae507`.
The latter includes four subsequent node merges (#447–#450); no rebase or merge
was performed. Remote freshness is unverified: the supervisor prohibits network,
so `git fetch origin main` (AGENTS §1) was not run.

Prerequisites: authenticated-export dependency PR #446, merge `f52c587…`, is this
base. Its implementation `976e1f7…` and stage-5 merge `2ec62ca…` are in local
history. `BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 explicitly adopts option A,
local non-production PostgreSQL 17.11, with single-writer/default-off/false flags.
The existing [export delivery](../2026-11-12-k-stage7-authenticated-export/README.md)
records the applied backend and tests. This audit exercises the actual pinned
backend; presence or merge of a decision alone is not treated as capability.
The owner separately approved the free offline engine dependency bundle.

See [coverage.md](coverage.md) for pre-existing coverage classifications and new
gaps, and [the harness README](../../analytics_audit/README.md) for reproduction,
catalog binding, adapter policies and limits. Historical maps remain unchanged.

Actual command results are retained in [commands.jsonl](commands.jsonl), including
failed attempts and subsequent fixes. Engine observations, host/protected-file
inventories and the final builder state are recorded alongside this report.
Records labeled `final-*` were executed by the earlier finishing builder session;
records labeled `finish-*` belong to the last builder session. Earlier records,
including `resumed-*`, were carried in with the prior draft and remain historical
attempts. [final-protected-before.json](final-protected-before.json) and
[final-protected-after.json](final-protected-after.json) capture the complete
protected-byte inventory before and after edits (123 files, zero differences);
[protected-before.json](protected-before.json) preserves the previous inventory.
[results.json](results.json) is the fail-closed aggregation over the three
complete engine runs (synthetic debug, synthetic release, local-PostgreSQL):
207 observations, 69 acceptance cases per run, every case PASS with identical
engine metadata and all production/runtime flags false. The [command
table](verification.md) lists the exact completed foreground
commands and exit codes; the JSONL retains output tails and log SHA-256 values.

A later supervisor-initiated merge of `origin/main` `1e40278…` (2026-11-14)
conflicted only in `docs/README.md`; the resolution and the merge-round local
check battery are recorded in [merge-resolution.md](merge-resolution.md). The
statements above about no merge having been performed describe the earlier
builder sessions and remain historical.

No implementation commit or exact final task head exists: the supervisor owns
committing. KTX exact-head CI run ID/status/conclusion: unavailable/not queried.
KIX protocol exact-head CI run ID/status/conclusion: unavailable/not queried.
No merge occurred; merge SHA and post-merge CI are not applicable. A2 non-author
review, final exact-head CI and any user merge remain outstanding supervisor gates.
Local acceptance is not merge readiness or production readiness.

Class B / UNDETERMINED: F64 tolerance/normalization, Fast64 adoption and
cancellation-sensitive intermediate SUM overflow ordering remain undecided by
User/Astra; this audit invents no policy. No production authentication,
multi-shard cut, incremental catch-up, performance, GPU, bank or chain behavior
is claimed. All production/runtime/economic execution flags stay false.

Implementation shape: an unpublished workspace audit crate with mandatory engines
behind the explicit `engines` feature. The complete conformance target requires
that feature; default CI emits an ignored-test reason and builds no engine
artifacts (verified in the separate CI-equivalent target directory). Both
adapters consume `ValidatedFeaturePlan`; catalog/fixture support is consolidated
in `tests/support/data.rs` and the named cases in `tests/conformance.rs`, rather
than the design's proposed separate catalog/fixtures files. No runtime entrypoint,
new protocol command, economic writer, workflow or authoritative contract changes.

Dependency resolution: the exact owner versions are used for Polars and
DuckDB; Polars also enables `round_series` for integer floor division, resolving
offline under the owner decision's extra-feature allowance. [dependency-resolution.json](dependency-resolution.json) records five
shared transitive patch changes from the provided bundle (`cfg-if`, `const-oid`,
`libc`, `syn`, `unicode-ident`). They all occur in the engine dependency graph;
this is not a general dependency sweep. The existing explicit crate dependency
pins remain unchanged. Workspace tests and Clippy were rerun for this graph.

Local deviations and limits:

- Fetch, commits, push, PRs, issues and comments are forbidden by this session's
  supervisor instruction. The owner decision's PR instruction is left to the
  supervisor under that explicit boundary. There was no root decision file to
  remove on entry.
- Python is 3.13.5; protocol CI uses 3.12. Rust 1.98.1 and Node 24 match CI.
- Engine opt-in and default-CI skip follow the owner decision. Default CI cannot
  stand in for the required local engine runs. No CI file was edited.
- Default workspace tests passed 339 with one explicit engine-feature skip.
  Historical Python passed 207 with one existing `CLI fixture runtime unavailable`
  skip; historical Node passed four. Engine acceptance must not skip engines.
- Full Move/Sui/localnet/ZK, bootstrap/downloads and unrelated storage probes were
  not run for these paths. The unchanged protocol offline-document checker block
  (65 commands, including self-tests), reference state machines, OpenAPI,
  integration gate, canonical/commerce, architecture, workspace and explicit
  kernel checks are the practical local CI equivalents. The exact extracted
  block is retained in [offline-checkers.sh](offline-checkers.sh).
- This delivery is local, source-informed audit evidence, not non-author A2 review,
  production qualification, program completion or a permission to merge.

Resumed-session diagnostic: the first reference-state-machine batch passed
settlement (224), booking/resale/admission (954), and credit (230), then failed
one of 169 AI tests when an existing console subprocess exceeded its unchanged
15-second timeout. The exact failing test passed separately in 2.686 seconds;
the full AI suite then passed 169, followed by token/reward 397, provider facts
86, payment effects 28, economics 99 and offline limits 9. Both OpenAPI checkers
and their self-tests also passed in that continuation. Root cause of the first
timeout is unproven; no timeout, reference source or CI rule was changed.

Additional Class B characterization: the audit labels nullable arithmetic
NULL propagation separately. Feature Semantics v1 does not explicitly define
that propagation rule, so this is not adopted as a new contract policy.

Release-acceptance note: the first 1-hour-bound release build attempt was
SIGTERM-killed mid `libduckdb-sys` compile; a second serial attempt from the
prior session was still running as an orphan at session entry (~286/305 cached
unity objects) and was terminated and recorded as exit -15. The resumable
object-cache wrapper preserved all completed objects; the rerun at
`CARGO_BUILD_JOBS=3` (cc honors `NUM_JOBS` for parallel C++ compilation)
finished the remaining objects and passed all 8 conformance tests in release.
`results/` mirrors the synthetic debug run's per-case files; `results.json`
is the cross-run aggregate.
