# Local settlement statement adapter — builder evidence

Node/task ID: `plan-local-settlement-statement-adapter`, 2026-10-31.
Task input is the supervisor-provided node specification and read-only design
in this session; no task issue or node document under `docs/tasks/` exists.
`docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` was read as historical context;
PROGRAM_DECISIONS_20260928.md §2.1 authorizes this bounded in-memory addition.
This is builder-authored evidence, not non-author review, A2 acceptance or
merge readiness.

Cached `origin/main`, task base and branch HEAD before implementation:
`8f7eedaef3e2cc74dcc6e19363c0096908796145` on
`agent/kix-plan-local-settlement-statement-adapter`. They match locally; remote
freshness and remote dependency completion are unverified. The supervisor's
explicit no-network instruction supersedes the initial fetch in AGENTS.md §1.
No fetch, commit, push, GitHub action, issue or comment was performed. There is
no implementation commit or exact final task commit yet; HEAD stays at the
base and the supervisor owns publication. No merge occurred.

Protected bytes before work:

| Path | Git blob / tree |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1` | tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

Complete changed-path list:

- `reference/settlement_f01_f03/README.md`
- `reference/settlement_f01_f03/statement_source.py`
- `reference/settlement_f01_f03/fake_statement_source.py`
- `reference/settlement_f01_f03/statement_adapter.py`
- `reference/settlement_f01_f03/example_statement_adapter.py`
- `reference/settlement_f01_f03/test_statement_source.py`
- `reference/settlement_f01_f03/test_statement_adapter.py`
- `docs/README.md`
- `validation/2026-10-31-plan-local-settlement-statement-adapter/README.md`

The [settlement README](../../reference/settlement_f01_f03/README.md) records
the requirement-by-requirement existing coverage inventory, written before
new tests. Existing FSM/arithmetic coverage is sufficient as source material;
adapter integration was absent. New source tests cover copied immutable
recordings, fresh parsed documents, identity-pair lookups, call snapshots,
deterministic fault markers and malformed recording inputs. Adapter tests
cover one fetch, exact field/object forwarding, unchanged real FSM result and
error objects, absence/failure/identity/shape fencing, no FSM calls or key
binding on local failures, and no automatic operation/distribution.

Direct-versus-adapter comparisons cover valid component conservation,
malformed/bool/negative components and adjustment reasons, unchanged stored
rejection errors, corrected-body conflicts, fresh-key acceptance, replay after
later state changes, conflicting body/operation, duplicate movement and
unknown/illegal/terminal phases. Public state and journal equality are paired
with later key probes; canonical state alone omits the rejection key table.
The example test checks actual FSM replay, caller policy/order, intermediate
undistributed cash, final conservation and retained false flags.

Actual verification commands and results (all exit 0):

Settlement/example, checker and architecture Python commands below were run
with `PYTHONDONTWRITEBYTECODE=1`. Each checker
row represents two invocations, plain and `--self-test`. Cargo commands were
run with `CARGO_NET_OFFLINE=true`, using installed rustc/cargo 1.98.1 (matching
the workflows' Rust version); no dependency fetch or toolchain install ran.
Only foreground commands were launched. Raw checker/Rust logs were retained
under `/tmp/kix-*.log` for this session; they are not repository artifacts.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03 -p 'test_statement*.py'` | PASS, 15 new tests |
| `python3 reference/settlement_f01_f03/example_statement_adapter.py > /tmp/kix-settlement-statement-example.json` | PASS; JSON report has cash 93000, noncash 7000, explicit initiate/authorize/capture/commit/observe_statement/distribute journal; parsed with `python3 -c` to inspect those values |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS, 211 tests; all existing settlement tests unchanged |
| `python3 scripts/check_docs_index.py` / `--self-test` | PASS / PASS; scanned 322, indexed 287, allowlisted 35 |
| `python3 scripts/check_settlement_evidence_map.py` / `--self-test` | PASS / PASS; 27 headings/rows, 110 citations; 33 negative controls |
| `python3 scripts/check_contract_error_codes.py` / `--self-test` | PASS / PASS; all 199 rows COVERED; SET=34 unchanged |
| `python3 scripts/check_ci_checker_wiring.py` / `--self-test` | PASS / PASS; 35 scripts, 13 negative controls |
| `python3 scripts/check_ci_test_discovery.py` / `--self-test` | PASS / PASS; settlement directory files=13 reached by existing offline-reference workflow step; 18 negative controls |
| `python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 / KTX-R1 boundary; no durability/performance certification |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | PASS; sum of reported results: 139 passed, 0 failed/ignored |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | PASS |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS; check mode only |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | PASS; sum of reported results: 339 passed, 0 failed/ignored |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | PASS |
| `git diff --check` | PASS |
| `git rev-parse HEAD origin/main` | Both remain `8f7eedaef3e2cc74dcc6e19363c0096908796145` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after work: both match the required blobs above |
| `git rev-parse HEAD:reference/v0.3-rc1` | Preserved tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |
| Python byte comparison using `git ls-tree -rz HEAD -- ROOT`, then `git hash-object -- PATH` for every tracked file, and `git ls-files --others --exclude-standard -- ROOT` | PASS; all 108 historical-reference, 1 `.aiops` and 10 task-document file blobs match HEAD; no untracked files in those roots |
| `git status --short` | Exactly the nine changed paths listed above; no existing FSM/test/arithmetic, runtime, contract, catalogue, SDK, gate or workflow edits |

The architecture/kernel commands match the practical offline KTX checks;
the settlement/document/discovery and workspace checks are the relevant local
KIX equivalents for these touched paths. The Python test commands ran narrow
first, example second, complete settlement suite third, then the broader
checks. No failing test or checker needed a fix. Final source inspection found
no additional authorized implementation changes necessary.

After-work protection checks match all before-work locked blobs and the
historical-reference tree. Final-merge blob verification is not applicable
because nothing was merged.

No explicit contract violation found. New-key `observe_statement` of an
already-bound movement is economically inert but appends an accepted journal
entry; this is an existing source-informed characterization, not a newly
defined contract. Existing injected-late-fault/rollback characterizations are
unchanged; this adapter supplies no rollback guarantee.

Design deviations: network fetch omitted as explicitly required; Cargo checks
use offline mode to honor the same constraint. Scope and interfaces otherwise
follow the supplied design. Full hosted CI and unrelated Move/SDK/ZK/localnet
journeys are not claimed by this Python-only task's local checks.

KTX and KIX exact-final-head CI run ID/status/conclusion: **NOT_RUN / not
available** (no final commit or publication in this builder session).
Post-merge main CI: not applicable. Non-author exact-final-head review and
completed/success KTX and KIX workflows remain required before merge readiness;
the supervisor must establish those on the published final commit.

All amounts, policy and order in the runnable entry point are synthetic fixture
inputs. Product rates, waterfall, residual recipients, legal parties,
tax/accounting treatment and P04 closure remain **UNDETERMINED**, with Astra/User
and the existing I10 owners. No sockets, persistence, external services,
credentials, real funds, bank exactly-once, chain execution/finality, production
durability, runtime activation or production readiness was implemented or
verified. MOCK provenance and existing false flags remain unchanged.
