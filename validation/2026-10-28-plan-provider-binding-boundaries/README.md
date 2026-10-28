# Offline provider binding boundaries — 2026-10-28

Builder-authored evidence for `plan-provider-binding-boundaries`.
**MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY — source-informed synthetic characterization;
Analog, NOT Toss.** This record changes no contract, evidence grade or owner.

Task input: supplied node/design prompt, KIX planner run `1793197931`
(`/workspace/kix-run/logs/planner_1793197931`); issue: none; no task document
under `docs/tasks/`. This loop-proposed node is not in `.aiops/program.json`
and this is not an ASTRA program-mode session. Dependency records:
[normalization](../2026-10-28-plan-provider-fact-normalization-offline/README.md)
and [structural rejections](../2026-10-28-plan-provider-structural-rejection-tests/README.md).
Their test/CI results are not inherited here.

Supplied base: latest main (no numeric SHA supplied). Locally observed
`origin/main` and initial branch HEAD both equal
`9c17e027141a099c55f27fe1808326bd82d0fdf7` on
`agent/kix-plan-provider-binding-boundaries`; initial worktree clean, no local
base delta. AGENTS §1 fetch was omitted under the explicit supervisor
no-network rule; remote freshness is unverified. No commits or GitHub actions
are authorized; implementation/final committed task SHA belongs to supervisor
delivery and is unavailable in this session.

## Existing coverage mapped before test edits (AGENTS §7)

Paths below are relative to `reference/provider_facts/`. This table was written
after reading the implementation and relevant tests, before editing tests.

| Requirement | Prior coverage | Classification / gap |
|---|---|---|
| Changed-PaymentRef conflict | `test_operation_binding.py::OperationBindingTests.test_same_operation_different_payment_key_is_review_conflict_without_new_capture` and `test_reacceptance_requires_the_entire_payment_ref` | Sufficiently covered conflict matrix; reuse all five fields. Partial preservation assertions: strengthen to complete public-state snapshots. |
| Initial provider/account scope mismatch | `test_initial_binding_rejects_operation_payment_scope_mismatch` | Partially covered; empty store only, no retained review/capture contents. |
| Provider/account/operation isolation | No multi-operation store test | Not covered; equal operation strings across scopes and independent operations need controls. |
| Unknown-operation lookup | No explicit unknown lookup test | Not covered. |
| Invalid store reference arguments | `test_payment_ref.py::PaymentRefTests.test_payment_ref_is_the_five_field_tuple` covers constructor fields only | Not covered at store entry points; reuse constructor checks without duplication. |
| Capture without binding | Existing conflicting-binding capture cases above | Partially covered; unbound valid operation missing. |
| Invalid/mismatched capture item | No explicit item guard tests | Not covered; wrong types and five-field reference mismatch need valid bindings. |
| Rejection preserves all fixture evidence | Existing conflict tests check selected fields/list lengths | Partially covered; compare every fixture lookup/count and complete deep-copied reviews/captures immediately around each rejection, with populated evidence. |
| Positive controls | Existing BOUND, REACCEPTED, lookup and capture checks | Partially covered; assert full appended capture dictionaries/digests and retain previous state. |
| Discovery/docs indexing | Existing `protocol.yml` provider discovery and checkers | Sufficiently covered wiring; current patch verification required. |

## Contract and characterization boundary

[ADAPTER_EVENT_IDENTITY §§2–3](../../docs/contracts/ADAPTER_EVENT_IDENTITY.md)
defines scoped OperationRef and at-most-one PaymentRef per operation. This
supports the E01/K1 identity gaps in the
[capability register](../../docs/status/CURRENT_CAPABILITY_REGISTER.md) without
changing their coverage or grades. The in-memory fixture's exact error codes,
guard order, and public review/capture structures are AGENTS §8 B source-informed
characterizations. In particular, capture with an invalid payment-reference
type on a bound operation raises `BINDING_REQUIRED`, whereas bind rejects it
as `INVALID_PAYMENT_REF`. No new validation of other NormalizedItem fields is
defined. No explicit contract violation has been observed.

## New regression mapping

All methods are in
[`test_operation_binding.py`](../../reference/provider_facts/test_operation_binding.py),
class `OperationBindingTests`. Five methods were added; three existing methods
were strengthened without duplicating the changed-PaymentRef conflict matrix.

| Test / helper | Evidence added |
|---|---|
| `test_operation_scope_isolation` | Four bindings: baseline, provider-only difference, account-only difference, operation-only difference. Equal operation strings in distinct provider/account scopes retain separate bindings. Complete snapshots after every insertion, reacceptance and targeted conflict show other bindings remain intact. Conflict appends only the exact expected `BindingConflict`. Successful captures retain preceding evidence. |
| `test_unknown_operation_lookup_preserves_state` | Unknown valid operation returns `None`; known operations return their original PaymentRefs. Complete state remains unchanged, including an unbound candidate, four bindings/captures and a populated review list. |
| `test_invalid_reference_arguments_preserve_state` | None/string/dict/wrong-reference-class operation arguments to bind, lookup and capture raise `INVALID_OPERATION_REF`; invalid payment-reference types to bind raise `INVALID_PAYMENT_REF`. The same invalid payment types on a bound capture raise the characterized `BINDING_REQUIRED`. Other arguments remain valid. Successful lookup, REACCEPTED and capture are positive controls. |
| `test_capture_without_binding_preserves_state` | A valid unbound operation plus valid PaymentRef and matching normalized item raises `BINDING_REQUIRED` without changing any evidence. Binding that same operation then succeeds and permits capture, retaining all preceding state. |
| `test_capture_item_mismatch_preserves_state` | With a valid matching binding, None/string/dict/PaymentRef/OperationRef items raise `CAPTURE_ITEM_MISMATCH`. A real NormalizedItem with each of the five PaymentRef fields changed independently raises the same error. A valid item captures successfully afterward. No amount/kind/time validation is invented. |
| Existing `test_same_operation_different_payment_key_is_review_conflict_without_new_capture` and `test_reacceptance_requires_the_entire_payment_ref` | Existing changed-key and full five-field conflict matrices retained. Expected complete review entries and snapshots replace count-only preservation checks; every rejected conflicting capture compares full state, then reacceptance retains it. |
| Existing `test_initial_binding_rejects_operation_payment_scope_mismatch` | Provider/account mismatch now runs against an unbound candidate with four unrelated bindings/captures and a review entry already populated. `BINDING_MISMATCH` preserves all state; matching bind/capture succeed afterward. |
| `_snapshot`, `_assert_rejected_unchanged` | Deep copies all fixture `(OperationRef, lookup result)` pairs, public binding count, complete review entries and complete capture dictionaries. Includes unbound candidates; never reads `_bindings`. Every rejected call compares the immediate before/after snapshot and exact error code. |
| `_assert_capture` and fixture controls | Normalize copied synthetic PAID/DIFFERENT_PAYMENT documents. Capture returns `evidence_hash(item)` and appends the complete expected operation/payment_key/item_index/evidence_hash dictionary, preserving all preceding captures/reviews/bindings. BOUND/REACCEPTED and successful lookup are asserted. |

## Commands actually run and results

All commands ran from the repository root. Python `3.13.5` differs from hosted
protocol CI's `3.12`; Cargo `1.98.1 (797e8a9bc 2026-08-05)` and rustc
`1.98.1 (48a229cea 2026-09-01)` use the repository workflow toolchain version.
Cargo used the existing cache with `--locked --offline`. Commands were run in
the foreground, without background jobs, dependency installation, sockets,
credentials or network actions.

Inspected `.github/workflows/protocol.yml` (stdlib document checks, provider
unittest discovery, architecture/Rust checks) and
`.github/workflows/ktx-kernel.yml` (architecture, kernel tests, Clippy, format).
The commands below are their closest applicable local equivalents for these
test/document changes, not a reproduction of the entire hosted workflow.

For checker rows, **both modes** means the displayed command and the same
command with ` --self-test` appended, each actually executed in a sequential
Python subprocess batch with `PYTHONDONTWRITEBYTECODE=1` in its environment.
Architecture commands used that environment too. The focused tests ran first,
then complete provider discovery, then checker/architecture/Rust verification.

| Actual command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD origin/main`; `git branch --show-current` | Exit 0; initially clean; expected branch; both SHAs equal the observed base above. Final status contains only the three allowed paths; HEAD unchanged. |
| `python3 --version`; `cargo --version`; `rustc --version` | Exit 0; versions recorded above. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -p test_operation_binding.py -v` | PASS, exit 0; 8 tests. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts` | PASS, exit 0; 36 tests. |
| `python3 scripts/check_docs_index.py` — both modes | PASS, exit 0 each; scanned=310, indexed=275, allowlisted=35; all 7 negative controls detected. Rechecked after completing this record. |
| `python3 scripts/check_ci_test_discovery.py` — both modes | PASS, exit 0 each; 7 reference suites, 8 Node tests, 4 modules, 3 historical exclusions; provider discovery reaches 10 files; 18 negative controls detected. |
| `python3 scripts/verify_runtime_architecture.py` | PASS, exit 0; architecture v5 + KTX-R1 dependency gate. Durability/performance not certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS, exit 0; 7 tests. Negative fixtures use temporary copies. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline > /tmp/kix-provider-binding-kernel-tests.log 2>&1` | PASS, exit 0; 139 tests across 7 integration suites, 9 target summaries including zero-test unit/doc targets. No failed/ignored/measured/filtered tests or warning/error diagnostics. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline > /tmp/kix-provider-binding-workspace-tests.log 2>&1` | PASS, exit 0; 339 passed across 46 successful target summaries; 0 failed/ignored/measured/filtered. No warning/error diagnostics. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings > /tmp/kix-provider-binding-clippy.log 2>&1` | PASS, exit 0; no warning/error diagnostics. Workspace includes kernel checks. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| Read-only `python3 -B` log-summary inspection | PASS, exit 0; kernel/workspace target summaries and diagnostic lines inspected, Clippy log inspected. |
| Read-only `python3` / `python3 -B` kernel Git-blob hashing and legacy SHA-256 manifest capture/comparison | PASS, exit 0 before/after; both locked blobs match; all 108 legacy paths/bytes identical. Details below. |
| Read-only `python3 -B` full tracked-file comparison using `git ls-tree -rz HEAD` plus `git ls-files --others --exclude-standard -z` | PASS, exit 0; 1,106 tracked files checked, 1,104 byte-identical to HEAD. Only the two authorized tracked files differ; exactly the validation README is untracked. |
| `git diff --check`; `git diff --stat`; `git status --short` | PASS, exit 0; no whitespace errors, expected changed paths only. Untracked validation record inspected directly. |

## Complete changed paths and preserved-file integrity

- `reference/provider_facts/test_operation_binding.py` (five new test methods,
  helpers, stronger assertions in three existing methods and provenance label)
- `validation/2026-10-28-plan-provider-binding-boundaries/README.md` (new)
- `docs/README.md` (one adjacent provider validation link)

Read-only hashing uses SHA-1 of `b"blob " + str(len(data)).encode() + b"\0" + data`,
the Git blob encoding, without writing Git objects.

| Locked file | Before Git blob | After Git blob |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The complete `reference/v0.3-rc1/**` manifest maps each sorted file path to its
SHA-256 byte digest. Before editing, it was saved to
`/tmp/plan-provider-binding-boundaries-before.json`; after work both the path set
and every byte digest compare equal: **108 files, unchanged**. SHA-256 of
`json.dumps(manifest, sort_keys=True).encode()` before and after:
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.

The full tracked-file comparison additionally confirms implementation,
fixtures, contracts, capability grades, evidence maps, CI, `.aiops/**` and
`docs/tasks/**` byte-identical to HEAD. No protected file was transiently
mutated. No task document was created or edited.

## Delivery gates, deviations and limitations

Local tests/checks pass. **READY for supervisor handoff only**, not merge-ready.
Implementation/final committed task head: unavailable, no commit authorized.
Current branch HEAD remains `9c17e027141a099c55f27fe1808326bd82d0fdf7` plus this
uncommitted patch. Supervisor owns commits, pushes and GitHub delivery.

| External evidence | Run ID | Status / conclusion |
|---|---|---|
| Exact-final-head KTX kernel verification | Unavailable | Not run or queried; unknown. |
| Exact-final-head KIX protocol verification | Unavailable | Not run or queried; unknown. |
| Non-author exact-HEAD A2 review | Unavailable | Pending supervisor delivery; builder evidence is not independent review. |
| Merge SHA / post-merge main CI / final-merge blob check | Not applicable | No merge authorized or performed. |

Deviations: AGENTS §1 fetch omitted under the user's explicit supervisor
no-network instruction; remote freshness is not verified. No task document
exists under `docs/tasks/`; the supplied node/design prompt is the authorized
input. No implementation/design scope deviation, failure requiring a fix, or
new policy decision arose. No commit, push, PR, issue, comment or marker was made.

No explicit contract violation (AGENTS §8 C) found. Exact Python error codes,
reference-type guard order and public fixture evidence formats remain §8 B
source-informed synthetic characterization, rather than new contractual or
provider semantics. Invalid payment-reference capture behavior is characterized
only for an already bound operation. NormalizedItem checks exercise existing
type/reference checks only; this does not validate arbitrary item contents.

`EventItemId` source, aliases and domain/schema values remain UNDETERMINED with
Astra/TM04 as currently assigned; TM04 remains with Toss technical. Durable
binding remains with `k-stage5-durable-tx`; memory retention does not satisfy
ADAPTER_EVENT_IDENTITY §6.2 durable custody. Future work on those open inputs
requires its existing owners and a separate authorized task. No grade, owner,
contract, policy value, protocol command or product behavior changed.

Non-claims: no provider conformance, clean-room independence, real Toss
behavior, authentication, provider/bank exactly-once, chain finality,
distributed fencing, durability, production performance or production readiness.
No sockets, credentials, provider/bank/KYC calls, real funds, public endpoints,
Sui testnet/mainnet, storage/replication/consensus engine, coin/TIX module,
production runtime or new dependencies were used or added. The full hosted
workflow, network/HTTP services, Move/ZK and unrelated SDK/application checks
were not run. Local green results do not satisfy exact-head CI, non-author
review or user-only merge authorization.
