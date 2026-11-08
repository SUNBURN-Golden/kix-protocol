# Local collateral assessment tool — builder evidence

## Identity and basis

- Node: `plan-local-collateral-assessment-tool`; dependencies `tl-3-offchain`, `tl-4`.
- Task input: user-supplied node specification and read-only design plan in this
  session. No issue or task document exists; `docs/tasks/` was not changed.
- Branch: `agent/kix-plan-local-collateral-assessment-tool`.
- Locally observed `origin/main`, base and initial task HEAD:
  `aab0627f380931804ce0b9f1beba9d6f3f3fb3c2`. They match; remote freshness is
  unverified. The supervisor's explicit no-network rule overrides the initial
  fetch requirement. No fetch, GitHub action, commit, push or history change ran.
- Implementation and final task commit: not created; supervisor owns Git.
  Working-tree evidence only. No merge commit or post-merge run exists.
- Authority: `docs/DEVELOPMENT_PLAN.md`, `docs/decisions/AUTHORITY_MODEL_1.md`,
  `docs/decisions/PROGRAM_DECISIONS_20260928.md` §5,
  `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md` U2/TK-12 and the unchanged model.

## Scope

[Usage and schema](../../reference/token_reward/README.md#local-collateral-assessment).
The stdlib dispatcher calls the existing `collateral_recognized` once after
validating the envelope. The CLI reads one file/stdin JSON document or composes
all explicit guided inputs, previews them, and waits for literal `CALCULATE`.
Every response identifies synthetic calculation and unresolved decisions.
No model/FSM/session, contract, catalogue, runtime, workflow, token package,
`.aiops/`, task input or historical evidence is edited.

Asset selection and collateral ratios remain **UNDETERMINED — Astra/User**;
legal enforceability remains **UNDETERMINED — User/legal**. No custody, loan,
eligibility/adequacy classification, valuation or F04 connection is implemented.

## Existing coverage mapping (inspected before adding tests)

All paths below are under `reference/token_reward/` unless otherwise noted.

| Requirement | Existing coverage and classification | Added interface gap coverage |
|---|---|---|
| KRW guarantee/escrow sum and mixed token recognition zero | Sufficient arithmetic: `test_reward_model.CollateralTests.test_krw_portion_only_when_token_is_also_present`; `test_tl4_model_properties.CollateralPropertyTests.test_TL4_TK12_recognition_is_krw_sum_and_permutation_invariant` and `test_TL4_TK12_token_item_does_not_change_recognition` | Complete dispatcher/direct-result parity, real file/stdin/guided mixed journeys |
| Empty items | Sufficient arithmetic: `CollateralTests.test_empty_collateral_recognizes_zero_without_a_token_error` | Explicit `[]` and guided zero; missing list/count fails |
| Token-only, valuation, kind rejection | Sufficient domain coverage: `CollateralTests.test_TL0_TK12_T1_token_only_collateral_is_rejected`, `test_token_valuation_is_refused`, `test_unknown_collateral_kind_is_rejected`; `CollateralPropertyTests.test_TL4_TK12_any_valuation_key_is_refused` | Original error codes and multi-invalid precedence, including valuation on KRW items; real rejection transcripts |
| Exact integers and unchanged domain errors | Partial: `test_tl4_fuzz_boundaries.JunkAndJournalTests.test_TL4_junk_values_on_the_fenced_surface_raise_token_reward_error` | Dispatcher forwarding without coercion: 1, MONEY_MAX, sum at/over bound, >2**53, zero/negative/bool/string/fraction/exponent; caller input unchanged; one call on domain input |
| Strict decoding | Shared decoder sufficient: `test_reward_serialization.RewardSerializationTests`; calculator integration uncovered | Duplicate keys at multiple depths, non-finite/overflow, trailing JSON, Unicode/UTF-8, exact envelope, non-JSON Python values; zero calls on local shape/decode errors |
| Guided decline/incomplete input | Not covered for this calculator | EOF/interrupt at every prompt, malformed input and literal confirmation; zero calls unless confirmed complete; confirmed success/rejection one call |
| Synthetic output and no approval | Not covered for this calculator | Exact metadata/notice on calculation and rejection; below/equal/above-liability amounts return only the unchanged result |

[TL-4 historical evidence](../2026-10-09-tl-4-token-layer-verification/README.md)
is author-side and source-informed. This node neither upgrades it to independent
verification nor replaces its open decisions or no-package limitations.

## Added interface evidence

- `test_collateral_assessment.py`: result/error parity, exact integers, domain
  precedence, unchanged inputs and strict pre-dispatch validation.
- `test_collateral_cli.py`: actual subprocess file/stdin/guided journeys,
  deterministic output and instrumented no-call cancellation/incomplete checks.
- Six JSON and four guided fixtures contain synthetic example values only.
- Actual commands/results and transcripts are recorded below.

## Preservation

Before editing, `git hash-object` matched both required locked blobs:

| Path | Required/observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

[Protected before manifest](protected-before.json) records SHA-256 for both
locked files and all 108 files under `reference/v0.3-rc1/`. The final [preservation report](preservation.json) and [after manifest](protected-after.json)
confirm identical file sets and bytes (110 files total), both locked blobs match,
and all other tracked files remain unchanged. The manifest SHA-256 is
`5b6193dee8c4a75427c3dbfa42cb3c83873efcab5769c28bf5e16059c02e2642`.
The [protected-path Git diff](protected-diff.log) is empty (exit 0).

## Contract classification, non-claims and pending gates

- A: existing recognition and rejection semantics match TK-12 and are forwarded
  unchanged. No explicit contract violation found.
- B: the existing implementation's numeric bound, item/check ordering and other
  local input details are characterized implementation behavior, not new product
  policy or contract decisions. No authoritative contract is amended.
- No production qualification, real collateral/valuation, bank/KYC/PG, legal
  opinion, Sui execution, custody, finance approval, durability, distributed
  fencing, consensus, performance or independent verification was tested.
- A2 non-author exact-head review is pending. Exact-head KTX and KIX CI run
  ID/status/conclusion are unavailable: no delivery commit/PR was created and
  the builder is prohibited from network/GitHub actions. No merge-ready claim.
  Post-merge CI is not applicable. Supervisor must bind review and CI to the
  eventual committed head; local success cannot transfer from another SHA.
- All §5 locks remain. Product/architecture decisions belong to Astra/User;
  enforceability belongs to User/legal.

## Deviations

No fresh fetch under the supervisor's no-network restriction. Task input is the
supplied node spec, not a `docs/tasks/` file. No implementation/design scope
expansion. UTF-8-safe error-message escaping additionally handles duplicate
malformed Unicode keys before the shared decoder's Unicode validation.
EOF/interruption discards an incomplete proposal with exit 2; explicit decline
returns exit 0 with `cancelled: true`. Argument usage errors follow argparse.

## Actual commands and results

Commands ran from the repository root with `PYTHONDONTWRITEBYTECODE=1`.
`python3` is 3.13.5; provisioned `python3.12` is 3.12.15 (CI uses Python
3.12). Cargo/rustc are 1.98.1, matching the workflows. Rust commands used
`CARGO_NET_OFFLINE=true` and `RUSTUP_OFFLINE=1`; no downloads or external
services ran. Checks were foreground processes, without automatic retry.

| Command | Actual result | Log |
|---|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_collateral_*.py' -v` (initial) | exit 0; 13 tests, OK | [initial focused](focused-tests.log) |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -v` (initial) | exit 0; 249 tests, OK | [initial full suite](token-reward-tests.log) |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_collateral_*.py' -v` | exit 0; 14 tests, OK | [log](check-00.log) |
| `python3 scripts/check_docs_index.py` | exit 0; pass | [log](check-01.log) |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; pass | [log](check-02.log) |
| `python3 scripts/check_status_register.py` | exit 0; pass | [log](check-03.log) |
| `python3 scripts/check_status_register.py --self-test` | exit 0; pass | [log](check-04.log) |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0; pass | [log](check-05.log) |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0; pass | [log](check-06.log) |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0; pass | [log](check-07.log) |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0; pass | [log](check-08.log) |
| `python3 scripts/check_ci_test_discovery.py` | exit 0; pass | [log](check-09.log) |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0; pass | [log](check-10.log) |
| `python3 scripts/check_openapi_contract.py` | exit 0; pass | [log](check-11.log) |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0; pass | [log](check-12.log) |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0; pass | [log](check-13.log) |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0; pass | [log](check-14.log) |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; pass | [log](check-15.log) |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests, OK | [log](check-16.log) |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -v` | exit 0; 250 tests, OK | [log](token-reward-tests-final.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_collateral_*.py' -v` | exit 0; 14 tests, OK | [log](collateral-tests-python312.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -v` | exit 0; 250 tests, OK | [log](token-reward-tests-python312.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | **UNAVAILABLE**, exit 101; missing cached `bcs`, no tests/lint executed | [log](rust-tests.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | **UNAVAILABLE**, exit 101; missing cached `bcs`, no tests/lint executed | [log](rust-clippy.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0; no findings | [log](rust-fmt.log) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` and `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | both match required blobs, before/after | [report](preservation.json) |
| SHA-256 manifest comparison of both locks and `reference/v0.3-rc1/**` | 110 files identical, including all 108 reference files | [before](protected-before.json), [after](protected-after.json) |
| `git diff --exit-code HEAD -- runtime .aiops docs/tasks .github reference/v0.3-rc1 reference/token_reward/token_reward_model.py reference/token_reward/reward_fsm.py reference/token_reward/reward_session.py docs/contracts` | exit 0, empty diff | [log](protected-diff.log) |

The final suite includes the additional duplicate-surrogate-key interface
regression and UTF-8-safe diagnostic. Initial results are retained as
earlier working-tree evidence only. The full suite passes **250 tests**
on both Python versions; focused coverage passes **14 tests** on both.
The 7 applicable documentation/OpenAPI checks and their self-tests are
green, architecture checks are green (7 architecture tests), and Rust
formatting is green. Offline Rust test/Clippy prerequisites remain
unavailable; these are not passing checks. No dependency download, CI
modification or out-of-scope fix was attempted. Other workflow steps
(SDK, Move/localnet, ZK, storage probes and unrelated suites) were not
run for this Python calculator/documentation change.

Final documentation/index and whitespace checks: `python3 scripts/check_docs_index.py`,
`python3 scripts/check_docs_index.py --self-test` and `git diff --check` all
exited 0; [actual final results](final-document-checks.json). The changed-path
inventory also verifies every changed/new path is inside the authorized scope;
all four new Python modules parse successfully.

## Actual CLI transcripts

Each command used `PYTHONDONTWRITEBYTECODE=1`. [Machine-readable command
and exit manifest](transcripts.json). JSON inputs live in
`reference/token_reward/fixtures/`; redirected files contain the actual
supplied stdin. Stdout and stderr are captured separately without
editing. Empty stderr links are intentional. All 16 exits match their
expected outcomes; domain rejection and incomplete-input exits are
acceptance evidence.

| Actual command | Exit/outcome | Stdout | Stderr |
|---|---|---|---|
| `python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_guarantee.json` | 0; recognized_krw=30, token_recognized=0 | [JSON](guarantee-file.stdout.json) | [text](guarantee-file.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_guarantee.json` | 0; recognized_krw=30, token_recognized=0 | [JSON](guarantee-stdin.stdout.json) | [text](guarantee-stdin.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_escrow.json` | 0; recognized_krw=25, token_recognized=0 | [JSON](escrow-file.stdout.json) | [text](escrow-file.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_escrow.json` | 0; recognized_krw=25, token_recognized=0 | [JSON](escrow-stdin.stdout.json) | [text](escrow-stdin.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_mixed.json` | 0; recognized_krw=55, token_recognized=0 | [JSON](mixed-file.stdout.json) | [text](mixed-file.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_mixed.json` | 0; recognized_krw=55, token_recognized=0 | [JSON](mixed-stdin.stdout.json) | [text](mixed-stdin.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_empty.json` | 0; recognized_krw=0, token_recognized=0 | [JSON](empty-file.stdout.json) | [text](empty-file.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_empty.json` | 0; recognized_krw=0, token_recognized=0 | [JSON](empty-stdin.stdout.json) | [text](empty-stdin.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_token_only.json` | 1; TOKEN_ONLY_COLLATERAL_REJECTED | [JSON](token_only-file.stdout.json) | [text](token_only-file.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_token_only.json` | 1; TOKEN_ONLY_COLLATERAL_REJECTED | [JSON](token_only-stdin.stdout.json) | [text](token_only-stdin.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_valuation.json` | 1; PRICE_SOURCE_UNDEFINED | [JSON](valuation-file.stdout.json) | [text](valuation-file.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_valuation.json` | 1; PRICE_SOURCE_UNDEFINED | [JSON](valuation-stdin.stdout.json) | [text](valuation-stdin.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --guided < reference/token_reward/fixtures/collateral_guided_mixed.txt` | 0; recognized_krw=55, token_recognized=0 | [JSON](guided-mixed.stdout.json) | [text](guided-mixed.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --guided < reference/token_reward/fixtures/collateral_guided_empty.txt` | 0; recognized_krw=0, token_recognized=0 | [JSON](guided-empty.stdout.json) | [text](guided-empty.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --guided < reference/token_reward/fixtures/collateral_guided_decline.txt` | 0; cancelled; no calculation | [JSON](guided-decline.stdout.json) | [text](guided-decline.stderr.txt) |
| `python3 reference/token_reward/collateral_cli.py --guided < reference/token_reward/fixtures/collateral_guided_incomplete.txt` | 2; FixtureError | [JSON](guided-incomplete.stdout.json) | [text](guided-incomplete.stderr.txt) |

## Complete changed-path list

[Exact changed and new paths](changed-paths.txt), including this evidence bundle.
