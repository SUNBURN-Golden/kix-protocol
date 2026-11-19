# Guided pool opening composer — builder evidence

Node: `plan-local-pool-opening-composer`; dependency:
`plan-plan-local-pool-accounting-workbench`. Task input is the supervisor-supplied
node specification and read-only design in the session; no issue or task document
was supplied. No file under `docs/tasks/` is an output.

Local verification results and coverage are being recorded here. This is
source-informed builder evidence, not independent review or merge readiness.
A2 non-author exact-final-head review and completed/success exact-head KTX and
KIX workflows remain supervisor delivery gates.

## Scope and identity

The patch adds required mutually exclusive `--fixture PATH` / `--guided-init`
startup options to the pool console. Guided entry collects five signed ASCII
integers in imported `POOLS` order, then uses the existing complete preview,
literal `SUBMIT`, `PoolSession`, initialization reply and action loop. The integer
parser is extracted from the existing mutation path without changing its grammar,
conversion or errors. Explicit invalid fixture values never select guided mode.

- Branch: `agent/kix-plan-local-pool-opening-composer`.
- Observed local `origin/main`, task base and starting HEAD:
  `c2aa970f7d95bd569f2a8eb40218cbc4c5d33b6b`; no local base delta.
- `git fetch origin main` was intentionally not run: the later explicit supervisor
  instruction forbids GitHub/network actions. Remote freshness is unverified.
- Implementation/final committed HEAD: not created; the builder leaves an
  uncommitted patch on that starting HEAD. The supervisor owns the final SHA.
- Merge commit and post-merge checks: not applicable; no merge occurred.
- Exact-head KTX run ID/status/conclusion: NOT_RUN / unavailable in this session.
- Exact-head KIX run ID/status/conclusion: NOT_RUN / unavailable in this session.
- A2 non-author exact-final-head review: pending supervisor delivery.

## Coverage map (before editing → reused evidence / gap closure)

All symbols below are in `reference/token_reward/`.

| Requirement | Existing coverage before this node | Reused coverage / new focused evidence |
|---|---|---|
| File-free opening journey | Not covered | `test_pool_console.PoolConsoleTests.test_guided_opening_journey_matches_fixture`; five explicit balances, initialization, credit/spend/view and repeated references; real `--guided-init` child |
| Fixture/guided envelope parity | Partial: existing console/CLI journeys | New journey test compares complete result envelopes with fixture mode; existing `test_real_guided_journey_and_boundaries` compares fixture console with CLI |
| Complete flushed preview, one constructor and one confirmation, pool order | Partial: fixture-only startup flush test | `test_guided_opening_preview_flushed_before_single_construction`; explicit plus signs/leading zeroes retain integer parsing; no implicit view/dispatch |
| Decline, incomplete input, EOF, interrupt/read failure before confirmation constructs no ledger | Partial: fixture-only initialization/operation tests | `test_guided_opening_abort_never_constructs` checks every opening prompt and confirmation, spies on ledger/dispatch, and checks no later read |
| Exact validation and no fallback/default | Partial: session constructor and fixture shape tests | `test_guided_opening_validation_matches_fixture` covers each pool at 0, MONEY_MAX, -1, MONEY_MAX+1 and 9007199254740993; original `INVALID_NONNEGATIVE`, exact int forwarding, operation null, explicit None/empty/invalid fixture values |
| Lexical invalid input without retry | Partial: mutation parser only | `test_guided_opening_lexical_failures_do_not_retry_or_consume_more` covers each pool, blank, fraction/exponent/boolean/null/whitespace/Unicode/sign-only/overlong values; no preview or ledger, unread later input retained |
| Obligation spend restrictions, insufficient funds and snapshot preservation | Sufficient | `test_reward_model.PoolConservationTests.test_TL0_TK04_T1_forbidden_pools_do_not_fund_token_spend`, `test_shortfall_pauses_without_cross_pool_top_up`; session rejection test; guided boundary journey reuses the same refusal vectors |
| Repeated references append again | Sufficient | `test_pool_session.PoolSessionTests.test_repeated_refs_match_direct_model_and_append_again`; real journey repeats both source and program references |
| Seven synthetic false flags and full existing envelopes | Partial at new prompts | Existing `check_metadata` reused for every guided result and diagnostics; result arrays compare whole envelopes |
| Terminal output failure fences construction/dispatch; no retry | Partial at new prompts | `test_guided_opening_terminal_output_failures_fence_construction_and_dispatch` injects write/flush failure at notice, all five prompts, preview, confirmation and initialized reply; after confirmation one ledger but zero dispatch; each failure attempted once |
| Post-mutation failure preserves completed mutation, fences further dispatch | Sufficient; same action loop | Existing `test_output_failure_after_mutation_does_not_rollback_retry_or_continue`, confirmation/EOF and interruption tests retained |
| Startup mode compatibility | Fixture mode covered, new selector absent | `test_startup_requires_exactly_one_mode`; neither/both options are argparse usage errors |

These are source-informed regression checks, not clean-room independence. The
model, session, CLI, fixture helpers and accounting semantics were not edited.
No explicit contract violation or newly contract-undefined behavior was found.
The existing repeated-reference characterization remains unchanged.

## Transcript evidence

- [File-free invocation](file-free-journey.sh) contains a here-document with all
  five explicitly entered balances and the entire process-local journey. It
  supplies neither `--fixture` nor an input file. [stdout](file-free-journey.stdout),
  [stderr](file-free-journey.stderr), [exit](file-free-journey.exit).
- Replayable guided inputs: `reference/token_reward/fixtures/pool_console_opening_journey.txt`
  and `pool_console_opening_boundaries.txt`. They prepend five synthetic example
  inputs to the unchanged existing action transcripts; these are not suggestions
  or defaults in the console.
- Guided [journey](guided-journey.stdout) and [boundaries](guided-boundaries.stdout),
  and fixture [journey](fixture-journey.stdout) and [boundaries](fixture-boundaries.stdout)
  are complete stdout captures with corresponding `.stderr` and `.exit` files.
  Successful journeys exit 0. Boundary journeys exit the expected 1 after three
  `POOL_FORBIDDEN_FOR_TOKEN_SPEND` refusals and `POOL_EXHAUSTED_PAUSED`; the earlier
  proposed credit is explicitly declined. All five transcript stderr files are empty.

## Preservation and non-claims

Both required kernel blobs matched before editing and after work:

| Path | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

[Preservation output](preservation-final.stdout) compares 121 protected tracked
files byte for byte with the base, including `.aiops/`, `docs/tasks/`, the two
locks and `reference/v0.3-rc1/**`. The latter's complete 108-file inventory also
matches the [pre-edit SHA256 inventory](reference-before-sha256.json), including
its file set. Manifest SHA256:
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
The [read-only checker](verify_preservation.py) can be rerun by the supervisor.
Final-merge blob verification is not applicable.

Funding amounts/policy remain **UNDETERMINED — Astra/User**. Accounting/legal
treatment remains **UNDETERMINED — User/designated advisers**. No real funds,
provider/bank/KYC calls, network endpoints, chain query or execution, coin/TIX,
production runtime, persistence, storage engine, protocol command, external
exactly-once, durability, legal compliance or production readiness was tested or
introduced. Full Move/ZK/localnet/bootstrap CI was not run: it is unrelated to
these Python/documentation changes and can mutate the protected reference tree.
No commit, push, PR, issue, comment, tag, branch change or ASTRA marker was made.

## Commands and deviations

Every captured verification invocation is listed independently in
[command → result](command-results.md) and [raw command ledger](commands.jsonl).
Each label has complete `.stdout`, `.stderr` and `.exit` captures. Commands ran
from the repository root with `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH=reference/token_reward`. Python 3.13.5 is the default; Python 3.12.15
is also installed and matches CI's major/minor. Cargo/rustc are 1.98.1.

No design/implementation scope deviation was necessary. Execution deviations:
fetch was omitted under the supervisor's explicit no-network rule; no remote
freshness is claimed. Rust formatting and both architecture checks passed, but
kernel/workspace tests and workspace Clippy exited 101 before compilation because
`bcs` is absent from the offline registry cache. These three checks are
**unavailable, not passes**; no online fetch or bootstrap was attempted.

The first Python 3.13 discovery run had 323 tests and one failure: the unchanged
`RewardConsoleSubprocessTests.test_source_incomplete_no_dispatch` case
`operation='observe', cut=11` exceeded its 10-second harness deadline. The same
failure was recorded by the dependency node. The isolated unchanged test then
passed. This is diagnostic evidence, not a proven root cause or justification to
change that unrelated harness. The original failing capture is retained.

The first preservation-check invocation failed because Git's default quoted
Unicode paths were treated as literal paths. The evidence checker was corrected
to consume NUL-delimited paths and passed; no protected file was changed.

Remaining supervisor work: provision offline Rust dependencies and rerun the
unavailable checks; obtain non-author A2 review and both workflows at the eventual
exact final head. Local builder completion supplies no merge authorization.

Final Python results: **35 focused pool tests passed on Python 3.13 and Python
3.12; all 323 token-reward tests passed on Python 3.12**. The 14 applicable
checker invocations (seven scripts, normal and self-test modes) passed. Both
architecture checks (including seven regression tests), Rust formatting, the
corrected preservation checker and final whitespace check passed. The docs index
was checked again after completing this report and passed. The complete changed
path inventory is [changed-paths.txt](changed-paths.txt), including every evidence
artifact; only console code, focused tests, two transcripts, documentation and
this validation directory changed.

Builder handoff: READY for supervisor handling, with the unavailable Rust checks
and normal review/CI gates above still outstanding. This is not merge-ready.
