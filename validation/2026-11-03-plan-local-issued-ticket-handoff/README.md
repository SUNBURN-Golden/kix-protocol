# Local issued ticket handoff evidence

Node `plan-local-issued-ticket-handoff`; immutable input is the supervisor-supplied
node specification and design plan in this session. No issue or docs/tasks file.
Not ASTRA program mode. Branch `agent/kix-plan-local-issued-ticket-handoff`.
Initial HEAD and cached origin/main: `e7cac26e2b7ff7a8566701b2517db5fc658bf2e6`.
Supervisor prohibits network/GitHub and Git publication, overriding §1 fetch;
remote freshness is unverified. No base changes or publication authorized.

## Coverage mapping before adding tests

| Requirement | Existing evidence | Classification / remaining gap |
|---|---|---|
| Separate issuance and adoption on shared graph | `test_ticket_fulfillment.py::test_prepared_second_ticket_matches_direct_graph` | Partial: manual inputs covered; source-backed connection missing |
| Exact forwarding, receipts/errors/state/journals | Fulfillment forwarding test; `test_ticket_operations_session.py` direct graph/snapshot helpers | Partial: extracted body and one selected target missing |
| Missing/malformed source and identity mismatch | Quote adapter tests cover analogous boundaries | Not covered for this connection; zero target calls and unbound keys needed |
| Unissued/consumed and atomic refusal | `test_adopt_issued_atomicity.py`, fulfillment adoption refusal tests, resale/admission FSM tests | Sufficient FSM coverage; adapter boundary and retained errors missing |
| Lifecycle replay and changed-body key conflicts | Fulfillment replay; `test_restore_fingerprint_equivalence.py` optional adoption binding fields | Partial: extraction after lifecycle changes missing |
| Detached data | `test_returned_data_isolation.py` views, input copies and first receipts | Sufficient FSM characterization; adapter copies missing |
| Explicit calls, clocks, mock flags, no defaults | Fulfillment graph snapshots/fetch histories and shared flag helpers | Partial: new connection needs guards and exact inputs |
| File/stdin, strict schema, regressions/checkers | Shared CLI suites and CI discovery | Partial: new selector/transcripts missing |
| Indexed evidence and delivery | Existing validation pattern | New record needed; non-author A2 review and exact-head CI remain supervisor gates |

Builder tests are source-informed, not independent or clean-room evidence.
Actual verification results and limitations will be recorded below.

## Implemented connection and new evidence

`IssuedTicketAdapter` validates explicit selectors/identities before source access,
reads the existing reservation and show views, and copies recorded booking/show
fields into one selected existing session `adopt_issued`. The shared session
constructs it with the same reservation machine and published target sessions.
The shared-only CLI selector requires exactly reservation/right/key; manual and
standalone adoption interfaces are unchanged. Local extraction exceptions are
separate from protocol errors and do not bind target keys. Target receipts and
exceptions propagate unchanged. No lifecycle precheck, cache, retry, fallback,
clock changes, ownership substitution or automatic follow-up is added.

New tests address the mapped gaps:

- `test_issued_ticket_adapter.py` checks constructor inactivity, exact original
  field forwarding to one selected target, explicit nullable quotes, ordered
  detached gates, unchanged receipt/exception identity, rereads on each request,
  malformed/missing containers/required fields/scalars, identity disagreement,
  source exceptions and validation before any target mutation. Spy inputs
  intentionally have consumed/current-owner/last-payment fields that must not
  replace the original booking values.
- `test_ticket_issued_handoff.py` compares receipts, errors, canonical states,
  digests and all four journals with equivalent direct FSM calls, using expected
  bodies from the preexisting manual fixture rather than the extraction code.
  It guards unselected adoption, checks unrelated graph state/fetch histories and
  reuses false-claim flag assertions. It covers separate explicit issuance and
  both adoptions, unissued/missing/mismatched source refusals and repaired same-key
  success, malformed-source repair on the actual graph, replay after listing,
  authorization, consumption and resale transfer, original buyer/payment, fresh
  consumed target refusals, retained refusal key conflicts, changed valid source
  body conflicts and returned-data isolation.
- `test_ticket_operations_cli.py::test_source_backed_adoption_shared_only_exact_arguments`
  extends schema coverage for every missing field, extra fields, wrong containers,
  unsupported target surfaces, exact operation string type, delegation/receipt identity and rejection by
  all standalone CLIs. Existing JSON decoding/schema matrices remain active.
- `ticket_operations_issued_handoff.jsonl` (18 rows) preserves the manual
  fulfillment journey with only explicit reservation/right/key handoff inputs;
  `ticket_operations_issued_handoff_boundaries.jsonl` (17 rows) covers extraction
  refusals, explicit recovery and existing target refusals/conflicts. Both reuse
  the unchanged fulfillment fixture with its issued anchor/prepared reservation.
  Tests execute each through file and stdin and compare every output row and
  intentional exit 1. The successful prefix exits 0; structural failures exit 2.

The consumed fresh-adoption test explicitly consumes on the shared reservation
source before either target adoption; both targets retain their existing
`ALREADY_CONSUMED` refusal. Later changed valid source input with that same key
matches direct `IDEMPOTENCY_CONFLICT`. Successful historical receipts replay after
consumption without requiring the source phase to remain `ISSUED`.

## Actual commands and results

All commands ran in this worktree, in the foreground. Python is 3.13.5.
Focused tests used the environment below; workflow-style discovery and the
checker runner omitted `PYTHONPATH` to keep the discovered suite first:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission:$PWD"
```

| Command actually executed | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD origin/main` | Initially clean; branch and both refs as recorded above; final refs/branch unchanged |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before and after work |
| `git ls-tree HEAD reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; all tracked working bytes match HEAD |
| `python3 -m unittest test_issued_ticket_adapter test_ticket_issued_handoff test_ticket_operations_cli` | PASS: 31 tests, 4.264 s; final strict-type rerun: 31 tests, 4.558 s |
| `python3 -m unittest test_ticket_fulfillment test_adopt_issued_atomicity test_returned_data_isolation test_restore_fingerprint_equivalence` | PASS: 27 tests, 1.783 s |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` with focused `PYTHONPATH` | Exit 1 before tests: sibling `test_contract_error_codes` import collision from existing sys.path setup |
| Same booking discovery command, with no `PYTHONPATH` (exact workflow form) | PASS: all 664 tests, 46.725 s; final strict-type rerun: 664 tests, 46.501 s; includes its HTTP test, no exclusions |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 224 tests, 1.845 s |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS: all 139 tests, 6.790 s; full HTTP coverage, no exclusions |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: 9 tests, 0.195 s |
| CLI `python3 reference/booking_resale_admission/ticket_operations_cli.py --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json --requests reference/booking_resale_admission/fixtures/ticket_operations_issued_handoff.jsonl` | Executed by transcript test with absolute paths: expected exit 1, empty stderr; every row equals direct-control expectation |
| Same CLI/fixture with `--requests -`, stdin from handoff transcript | Expected exit 1; identical 18 rows |
| Same CLI/fixture with `--requests reference/booking_resale_admission/fixtures/ticket_operations_issued_handoff_boundaries.jsonl` | Expected exit 1; all 17 rows match |
| Same CLI/fixture with `--requests -`, stdin from boundaries transcript | Expected exit 1; identical 17 rows |
| `python3 /tmp/kix-issued-handoff-checks.py` | PASS: sequential foreground subprocess runner; exact child commands, exit codes and output tails in [check-results.json](check-results.json) |
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate; durability/performance not certified |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests, 0.213 s |
| `python3 /tmp/kix-issued-handoff-rust.py` | Exit 1: runner records blocked offline Cargo checks and successful format/version checks in [rust-results.json](rust-results.json) |
| `python3 /tmp/kix-issued-handoff-preservation.py` | PASS: 313 protected tracked blobs; exactly 13 allowed changed paths; changed Python parses, JSON/JSONL parses, transcript counts 18/17; refs/branch unchanged |
| `git diff --check` | PASS |

Counts overlap; do not sum them. The discovery environment error was corrected
by matching the existing CI invocation, without modifying tests or workflows.

Inspected `.github/workflows/ktx-kernel.yml` and `protocol.yml`. Each checker below
ran as `python3 scripts/<name>.py` and again with `--self-test`:

| Checker | Plain | Self-test |
|---|---|---|
| `check_openapi_contract` | PASS: 84 commands, unchanged pin | PASS |
| `check_integration_gate_openapi` | PASS: 84 commands, publicHost/productionEndpoint false | PASS |
| `check_docs_index` | PASS: scanned 343, indexed 308, allowlisted 35 | PASS |
| `check_ci_test_discovery` | PASS: both new modules reached by unchanged discovery | PASS: 18 negative controls |
| `check_ci_checker_wiring` | PASS: 35 scripts | PASS: 13 negative controls |
| `check_bra_evidence_map` | PASS: 39 rows; capability grades unchanged | PASS: 50 negative controls |
| `check_contract_error_codes` | PASS: 199 covered rows; code map CLASS_B=0/CLASS_C=0 | PASS |

Code-map counts do not erase existing behavioral Class B characterizations.
The JSON artifacts retain exact child arguments and actual output tails; full
transient runner logs are under `/tmp/kix-issued-handoff-check-*.log` and
`/tmp/kix-issued-handoff-rust-*.log`, not repository deliverables.

Rust commands used the installed CI-version toolchain. The runner copied only
the existing public Cargo registry cache into `/tmp`; no downloads, installs,
credentials or host configuration changes:

```bash
export PATH="/home/box/.rustup/toolchains/1.98.1-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
export CARGO_HOME=/tmp/kix-issued-handoff-cargo
export CARGO_TARGET_DIR=/tmp/kix-issued-handoff-target
export CARGO_NET_OFFLINE=true
```

| Command | Actual result |
|---|---|
| `cargo --version`; `rustc --version` | Both 1.98.1 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | BLOCKED, exit 101: cached `bcs` missing, required by workspace `kix-bcs1`; no Rust tests executed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | BLOCKED, exit 101: same missing dependency; no Rust tests executed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | BLOCKED, exit 101: same prerequisite failure; no lint result |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |

No Rust file changed. Missing offline dependencies remain a supervisor verification
item; no automatic retry or network attempt was made. These local selections do
not establish full KTX/KIX CI. Untouched Move/localnet/ZK/SDK and other reference
suites were not run or claimed. Full HTTP coverage was run and passed.

## Complete changed-path list

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/issued_ticket_adapter.py`
- `reference/booking_resale_admission/ticket_operations_session.py`
- `reference/booking_resale_admission/ticket_operations_cli.py`
- `reference/booking_resale_admission/test_issued_ticket_adapter.py`
- `reference/booking_resale_admission/test_ticket_issued_handoff.py`
- `reference/booking_resale_admission/test_ticket_operations_cli.py`
- `reference/booking_resale_admission/fixtures/ticket_operations_issued_handoff.jsonl`
- `reference/booking_resale_admission/fixtures/ticket_operations_issued_handoff_boundaries.jsonl`
- `validation/2026-11-03-plan-local-issued-ticket-handoff/README.md`
- `validation/2026-11-03-plan-local-issued-ticket-handoff/check-results.json`
- `validation/2026-11-03-plan-local-issued-ticket-handoff/rust-results.json`

Preservation compared working Git blob hashes with `git ls-tree -rz HEAD` for
all tracked files under `runtime/`, `.aiops/`, `docs/tasks/`, `docs/contracts/`,
`.github/`, `sdk/`, `reference/v0.3-rc1/`, every preexisting booking fixture,
all fixture-validator modules and the four underlying booking gates/FSM files.
All 313 match. The initial clean worktree and required blob checks establish the
before baseline. There is no claim of transient mutation testing.

Both locked blobs match before and after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

## Classification, deviations, limits and pending delivery gates

Class A: exercised FSM behavior, first-result replay, retained target refusals,
key conflicts and atomic adoption match existing behavior/contracts. No explicit
contract violation was found. Returned-data copy ownership remains Class B
characterization, not a newly asserted protocol guarantee. Existing unsynchronized
reservation/resale ownership views and credential-reissuance limitations remain;
there is no synchronization, cross-machine rollback or policy interpretation.

Deviations: supervisor network prohibition overrides §1 fetch; no issue/task file
exists or was created. Selector coverage extends the existing CLI suite; direct
parity/transcripts use the planned new handoff suite. Full discovery uses the
workflow environment without focused-test PYTHONPATH after the observed import
collision. Rust tests/Clippy are blocked by missing cached `bcs`. No STOP-condition
dependency or consequential scope expansion arose; no decisions file is needed.

Product policy remains **UNDETERMINED — Astra/User**. Legal effects remain
**UNDETERMINED — User/legal**. No persistence, network integration, credentials,
funds, real PG/bank/KYC, public endpoints, chain execution, production runtime,
new protocol command, engine, coin/TIX module or credential reissuance was added.
This is builder-authored synthetic, source-informed evidence. It does not prove
clean-room independence, production durability, distributed fencing, bank/venue
exactly-once, chain finality, legal compliance or production readiness.

Implementation/observed HEAD remains `e7cac26e2b7ff7a8566701b2517db5fc658bf2e6`;
it does not contain the uncommitted patch. Final task head is **not assigned**;
the supervisor commits/publishes. Non-author A2 exact-head review is **pending**.
Exact-head KTX CI run ID/status/conclusion: **unavailable/pending**, not successful.
Exact-head KIX CI run ID/status/conclusion: **unavailable/pending**, not successful.
Both workflows must complete successfully at the supervisor's final head, with
normal Rust and HTTP coverage, before merge readiness can be proposed. Final-head
CI belongs in the supervisor closure report, not another evidence-only commit.
No commit, push, PR, issue, comment, marker or merge was created. Merge SHA,
final-merge locked-blob verification and post-merge main CI are not applicable.
Builder READY means the implementation is ready for supervisor handoff; blocked
Rust prerequisites, non-author review and exact-head CI remain separate gates.
