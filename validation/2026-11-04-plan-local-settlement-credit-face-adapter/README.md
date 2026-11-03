# Local settlement claim → synthetic credit offer: builder evidence

Node `plan-local-settlement-credit-face-adapter`; task document is the supplied
supervisor node specification/design in this session. No issue or file under
`docs/tasks/` exists for this node; none was created or edited. This is outside
ASTRA program mode. Source-informed builder evidence, not independent review.

## Basis and scope

Cached `origin/main`, base and initial/current branch HEAD:
`c641a7437f8dcf9094740bd0a4024ea1d2b89317`.
Branch: `agent/kix-plan-local-settlement-credit-face-adapter`.
Initial working tree was clean. No locally observed base delta.
Remote freshness is unverified: the supervisor's explicit network ban overrides
the session-start fetch. No commit, push, GitHub action or background job was
performed. Implementation/final committed head, merge SHA and post-merge CI are
not applicable to this uncommitted builder handoff; the supervisor owns Git/GitHub.

The adapter reads one caller-selected settlement view and forwards a detached
claim to the existing offer exactly once at most. Binding, approval and draw
remain explicit. No FSM, contract, catalogue or workflow was changed.
Usage and the **pre-addition coverage inventory** are in the
[adapter README](../../reference/credit_advance_f04/README.md).

## Changed paths

- `reference/credit_advance_f04/settlement_claim_source.py`
- `reference/credit_advance_f04/fake_settlement_claim_source.py`
- `reference/credit_advance_f04/settlement_claim_adapter.py`
- `reference/credit_advance_f04/example_settlement_claim_adapter.py`
- `reference/credit_advance_f04/test_settlement_claim_source.py`
- `reference/credit_advance_f04/test_settlement_claim_adapter.py`
- `reference/credit_advance_f04/README.md`
- `docs/README.md`
- `validation/2026-11-04-plan-local-settlement-credit-face-adapter/README.md`

## New evidence and gap coverage

| Test (under `reference/credit_advance_f04/`) | Gap addressed |
|---|---|
| `test_settlement_claim_source.py::SettlementClaimSourceTests` (5 tests) | Local view read/detachment and actual-machine evolution, immutable fake recordings/call snapshots, repeatable immediate faults, malformed JSON and constructor types |
| `test_settlement_claim_adapter.py::SettlementClaimAdapterTests.test_one_read_one_offer_detached_forwarding_and_exact_result_or_exception` | Full uncoerced claim forwarding, nested detachment, extra fields retained, exactly one source/offer call, identical return/error object |
| `test_missing_identity_envelope_and_fault_failures_never_offer_or_bind_key` | Missing/malformed views and claims, identity mismatch, all required fields/false flags, source faults; no offer and caller key remains free |
| `test_local_unknown_and_preclaim_phases_never_offer` | Actual UNKNOWN_SETTLEMENT exception and absent INITIATED/FAILED claims |
| `test_credit_validation_and_rejection_replay_match_direct_offer` | Existing validation order/codes, retained rejection keys, refund-obligation rejection; receipts/errors/state/digest/journals compared on separate machines |
| `test_replay_after_transitions_and_changed_snapshot_conflicts_do_not_refresh` | Every invocation reads, unchanged first-result replay after draw, changed snapshot same/new-key conflicts, original face unchanged |
| `test_explicit_bound_draw_retains_committed_gate_and_original_face` | CAPTURED offer has zero exposure; explicit binding/approval; rejected key remains rejected after commit; fresh draw key succeeds without refreshing face |
| `test_shared_capacity_and_changed_face_are_still_draw_time_checks` | Offers reserve zero; draw shared capacity rejection; changed claim/extra fields still freeze out at draw; direct/adapted state equality |
| `test_settlement_claim_adapter.py::SettlementClaimExampleTests.test_statement_backed_offer_and_separate_explicit_draw` | Existing statement adapter → actual settlement claim → OFFERED, then explicit binding/approval/draw; false flags/open terms, no distribution, explicit fixture inputs |

## Actual commands and results

All Python verification used `PYTHONDONTWRITEBYTECODE=1`. Commands below ran
from the worktree root. Closest scoped equivalents were selected by reading
`.github/workflows/protocol.yml` and `ktx-kernel.yml`; full hosted CI is separate.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD origin/main`; `git branch --show-current` | Clean initial tree; SHAs and branch recorded above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before edits) | Both required blobs matched (below) |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p 'test_settlement_claim*.py'` (initial) | 13 tests, 1 error: new test fixture attempted zero-gross statement, existing INVALID_AMOUNT rejection |
| Same narrow command after fixture correction; final repeat after documentation/review | 13 tests passed on both runs |
| `python3 reference/credit_advance_f04/example_settlement_claim_adapter.py > /tmp/kix-credit-face-example.json` | Exit 0, actual-machine JSON output |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 224 tests passed |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 161 tests passed |
| `python3 scripts/check_docs_index.py`; same with `--self-test` | PASS / PASS; scanned=344, indexed=309, allowlisted=35 |
| `python3 scripts/check_settlement_evidence_map.py`; same with `--self-test` | PASS / PASS; 27 headings/rows; 33 negative controls |
| `python3 scripts/check_credit_evidence_map.py`; same with `--self-test` | PASS / PASS; 22 headings/rows, 5 open items; 55 negative controls |
| `python3 scripts/check_contract_error_codes.py`; same with `--self-test` | PASS / PASS; 199 rows COVERED, CLASS_B=0, CLASS_C=0 in that code-level map |
| `python3 scripts/check_ci_test_discovery.py`; same with `--self-test` | PASS / PASS; new credit tests reached, 18 negative controls |
| `python3 scripts/check_ci_checker_wiring.py`; same with `--self-test` | PASS / PASS; 35 scripts, 13 negative controls |
| `python3 scripts/check_openapi_contract.py`; same with `--self-test` | PASS / PASS; 84 commands, unchanged pin |
| `python3 scripts/verify_runtime_architecture.py` | PASS; architecture v5/dependency gate |
| `python3 scripts/test_runtime_architecture.py` | PASS; 7 tests |
| `cargo --version`; `rustup toolchain list` | Cargo 1.98.1; installed active/default toolchain 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101 before tests: missing cached `bcs`, required by workspace `kix-bcs1` |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101 before lint: same missing cached `bcs` prerequisite |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |
| Read-only protected-blob verification (`git ls-tree -rz HEAD -- <protected paths>` plus Python Git-blob hashing of working files; command below) | PASS; all 123 protected tracked files byte-identical; no untracked protected files |
| `git diff --check` | PASS, exit 0 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after work) | PASS; both required blobs still match |

The checker commands were executed sequentially in one shell loop, each plain
then `--self-test`, exiting on any failure. No checks were weakened. Rust tests
and lint were **not executed**: cached workspace dependencies are unavailable.
No Rust source changed; no dependency/network fallback or automatic retry was
attempted. This limitation is not a successful KTX run.

Exact protected-byte verification command (run from the repository root):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import hashlib
import subprocess

root = Path('.')
protected = subprocess.check_output(['git', 'ls-tree', '-rz', 'HEAD', '--', 'reference/v0.3-rc1/', '.aiops/', 'docs/tasks/', '.github/workflows/', 'runtime/crates/kix-kernel/src/lib.rs', 'runtime/crates/kix-kernel/tests/quarantine_capacity.rs'])
count = 0
for entry in protected.split(b'\0'):
    if not entry:
        continue
    meta, name = entry.split(b'\t', 1)
    mode, kind, expected = meta.split()
    assert kind == b'blob', name
    path = root / name.decode()
    data = path.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest().encode()
    assert actual == expected, name
    count += 1
assert not subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', 'reference/v0.3-rc1/', '.aiops/', 'docs/tasks/', '.github/workflows/'])
print(f'PASS: {count} protected tracked files byte-identical to HEAD; no added protected files')
PY
```

## Preservation and remaining gates

Before edits, required locked Git blobs matched:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

Baseline historical tree `HEAD:reference/v0.3-rc1`:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
Post-work verification matched all 123 protected tracked files to HEAD bytes,
including every historical-reference file and both locks. No files were added
under the protected paths. `.aiops/`, `docs/tasks/` and workflows also match.

| Gate | Run ID / status / conclusion |
|---|---|
| Non-author exact-head A2 review | Not performed; separate supervisor/reviewer gate |
| Exact-head KTX kernel verification | No run observed; no final committed task head; pending supervisor |
| Exact-head KIX protocol verification | No run observed; no final committed task head; pending supervisor |
| Merge and main/push CI | Not merged; not applicable |

No new contract violation or contract-undefined semantics were found. Existing
class B observations remain as recorded in the credit/settlement clause maps:
later-refund draw behavior, retained rejected keys versus accepted-only restore,
and injected-internal-fault rollback are not redefined or fixed here.
Detached data tests establish process-memory isolation only.

Product terms remain **UNDETERMINED — Astra/User**; legal parties, accounting and
collateral effects remain **UNDETERMINED — designated external owners**. No real
funds, real PG/bank/KYC, public endpoints, Sui execution, secrets, production
runtime, storage engine, finance session/CLI, repayment source or protocol command.
No claims of bank exactly-once, durability, finality, legal compliance, lending
approval, independent review or merge-readiness. Remaining work is non-author
review, supervisor publication and exact-head CI; product/external decisions stay
with their existing owners.

## Deviations

- Fetch omitted due to the supervisor's explicit network ban; cached main only.
- No issue/task file exists: the supplied node spec is the immutable task input.
- Initial new test used an invalid zero-gross statement. Replaced with explicit
  distribution to change a claim within the existing FSM; no checks were weakened.
- KTX tests/Clippy could not start because the offline Cargo cache lacks `bcs`.
  Formatting and architecture pass; hosted KTX/KIX CI remains a separate gate.

## Fix round 1 (delivered-head review + exact-head CI)

Delivered implementation head observed in this worktree:
`124df639b9f70f6c3f60b199d4cf5aec3f37eea0`, based on observed
`origin/main` `c641a7437f8dcf9094740bd0a4024ea1d2b89317`. The sections above
describe the pre-delivery builder worktree and remain historical evidence; the
delivered head above is the current review target.

No review findings were supplied to this round (the handoff reported "review
passed or unavailable"), and no failed-job or failing-step log was available
(the handoff noted a possible Actions billing/runner refusal). No code-level CI
failure could be reproduced from the repository: the offline CI equivalents,
including the full checker block and all reference suites, pass at this head.
Consequently this round makes **no implementation, test, contract, workflow or
lock change**; it only records re-verification. If hosted CI still cannot start a
runner, that is an infrastructure matter outside this node and outside this
session's network/GitHub ban.

Re-run shape: from the repository root, `PYTHONPATH` unset, Python 3.12 (the CI
interpreter), `PYTHONDONTWRITEBYTECODE=1`.

| Command | Actual result |
|---|---|
| `env -u PYTHONPATH python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p 'test_settlement_claim*.py'` | **13 PASS**, 0.068 s |
| `env -u PYTHONPATH python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | **161 PASS**, 6.455 s |
| CI suite loop (`settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward provider_facts`) under Python 3.12 | 224 / 664 / 161 / 85 / 186 / 73 PASS |
| `python3.12 reference/credit_advance_f04/example_settlement_claim_adapter.py` | exit 0, actual-machine JSON |
| CI stdlib checker block (`check_status_register` … `check_cargo_offline_cache`, each plain and `--self-test`, plus `check_stage5_host.py --self-test`) | PASS |
| `check_openapi_contract.py` (+ `--self-test`), `check_integration_gate_openapi.py` (+ `--self-test`), `unittest integration_gate.test_offline_limits` | PASS / PASS; PASS / PASS; **9 PASS** |
| `python3.12 scripts/verify_runtime_architecture.py`; `python3.12 scripts/test_runtime_architecture.py` | PASS; **7 PASS** |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |
| `cargo test -p kix-kernel --locked --offline` | UNAVAILABLE, resolution error before tests: offline cache lacks `bcs` (unchanged; no Rust source touched) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `69564b16…` and `b607996c…` match the required locked blobs |
| `git status --porcelain`; `git diff --check` | clean implementation tree; exit 0 |

Individually scoped runs of `test_settlement_claim_adapter.py` (8 PASS) and
`test_settlement_claim_source.py` (5 PASS) also pass without `PYTHONPATH`,
matching how CI discovery imports the suite.

No new contract violation or contract-undefined semantics were found in this
round. Locked blobs, `reference/v0.3-rc1/**`, `.aiops/`, `docs/tasks/`, contracts
and workflows are unchanged. Exact-head KTX/KIX run IDs remain unavailable in
this session; the supervisor publishes this round's head, and non-author
exact-head review plus required KTX/KIX CI remain separate merge gates. No
product, legal, accounting or collateral decision is made or implied here.
