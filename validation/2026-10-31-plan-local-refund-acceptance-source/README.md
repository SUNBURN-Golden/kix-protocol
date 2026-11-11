# Local refund acceptance source — builder evidence

Node/task ID: `plan-local-refund-acceptance-source`, 2026-10-31.
Task input: supervisor-provided node specification and read-only design in this
session; no node issue or current node document under `docs/tasks/` exists.
`docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` was read as historical context.
PROGRAM_DECISIONS_20260928.md §2.1 and the node scope authorize this bounded
in-memory addition. This is a non-program-mode builder session, not non-author
review, A2 acceptance, architecture approval or merge readiness.

Cached `origin/main`, task base and pre-implementation branch HEAD all equal
`2d323b90f305d07d2ababdb5bbb0ffe47fda7b03` on
`agent/kix-plan-local-refund-acceptance-source`. There is no local base delta;
remote freshness is unverified. The supervisor's no-network instruction
supersedes the initial fetch in AGENTS.md §1. No fetch, commit, push, GitHub
operation, issue or comment was performed. Implementation and final task
commit SHAs do not exist yet: this work is uncommitted and HEAD remains the
base. The supervisor owns publication. No merge or post-merge checks apply.

Basis and dependencies: `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md`
§§5, 7.6 and 9; the existing statement-source modules and
[statement adapter evidence](../2026-10-31-plan-local-settlement-statement-adapter/README.md).
The local base contains settlement-policy-deepening's adopted
`SET-POLICY-DRAFT-0.3` posture and the statement adapter. Remote dependency
completion is unverified; historical passes are not evidence for this patch.

Complete changed-path list:

- `reference/settlement_f01_f03/cancel_acceptance_source.py`
- `reference/settlement_f01_f03/fake_cancel_acceptance_source.py`
- `reference/settlement_f01_f03/cancel_acceptance_adapter.py`
- `reference/settlement_f01_f03/example_cancel_acceptance_adapter.py`
- `reference/settlement_f01_f03/test_cancel_acceptance_source.py`
- `reference/settlement_f01_f03/test_cancel_acceptance_adapter.py`
- `reference/settlement_f01_f03/README.md`
- `docs/README.md`
- `validation/2026-10-31-plan-local-refund-acceptance-source/README.md`

The [settlement README](../../reference/settlement_f01_f03/README.md) contains
the existing coverage mapping written before adding tests. Existing refund,
property, replay and rejection-atomicity tests partially cover acceptance;
FSM partial-refund distribution blocking and workflow suite discovery are
sufficiently covered. Source/adapter behavior and this journey were uncovered.
The new source tests cover copied read-only recordings, nested fetched-document
isolation, stable call snapshots, pair lookup, repeatability, deterministic
fault markers and malformed inputs. New adapter tests cover one fetch per
explicit call, exact forwarding, unchanged result/error objects, direct-FSM
parity in CAPTURED and COMMITTED, duplicates after later changes, conflicting
source binding, missing/excessive obligations, malformed economics and retained
rejection-key probes. Pre-FSM shape/identity/absence/fault failures prove zero
FSM calls, no state/digest/journal mutation and later valid use of the same key.
Canonical state omits rejected keys, hence the explicit later-key probes.
The example test verifies the explicit operation sequence, preserved cash,
open adjustment, false flags, unmodified fixture inputs, blocked distribution
and journal restoration.

All Python verification below used `PYTHONDONTWRITEBYTECODE=1`. Cargo dependency resolution used
`CARGO_NET_OFFLINE=true`; installed rustc and cargo are both 1.98.1, matching
`.github/workflows/ktx-kernel.yml` and `protocol.yml`. No installation or network
access ran. Only foreground commands were launched. Temporary raw output is
under `/tmp/kix-refund-*`; it is not committed evidence.

| Command actually run | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; both SHAs equal the base above; expected branch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | Both match the required blobs below. |
| `git ls-tree HEAD reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `rustc --version`; `cargo --version`; `rustup toolchain list` | Installed and active 1.98.1. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03 -p 'test_cancel_acceptance*.py'` | First run: 13 tests, 1 failure from a test expecting `UNDEFINED` before obligation creation; actual existing flag was `NONE`. Corrected only the test expectation. Second run: 13 tests PASS. |
| `python3 reference/settlement_f01_f03/example_cancel_acceptance_adapter.py > /tmp/kix-refund-example.json` | PASS (exit 0); cash 97,000 throughout, adjustment 0/10,000/15,000, refund outstanding 40,000/30,000/25,000. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS, 224 tests. |
| `python3 scripts/check_docs_index.py` and `--self-test` | PASS; 323 scanned, 288 indexed, 35 allowlisted. |
| `python3 scripts/check_settlement_evidence_map.py` and `--self-test` | PASS; 27 rows, 110 citations; 33 negative controls. |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | PASS; 199 rows, all covered. |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | PASS; 35 scripts; 13 negative controls. |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | PASS; existing directory discovery includes the new tests; 18 negative controls. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | PASS; 84 commands, pin unchanged. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | PASS; 84 commands, productionEndpoint=false/publicHost=false. |
| `python3 scripts/verify_runtime_architecture.py` | PASS; architecture/dependency gate only. |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0; explicit standalone confirmation after the combined Rust run. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | PASS, exit 0. |
| `git diff --exit-code HEAD -- runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs reference/v0.3-rc1 .aiops docs/tasks docs/contracts .github/workflows reference/settlement_f01_f03/settlement_fsm.py reference/settlement_f01_f03/mock_settlement.py sdk integration_gate` | PASS, no protected/out-of-scope tracked changes. |
| `git diff --check` | PASS. |
| Python read-only per-file protection probe (`git ls-tree -rz HEAD -- reference/v0.3-rc1` plus `git hash-object` for each entry and both locks) | PASS; all 108 historical files byte-identical, both locks match, HEAD unchanged. Initial probe using line-oriented `git ls-tree -r` failed on Git-quoted Korean filenames; corrected the probe to NUL-delimited paths and reran successfully. No file mutation. |

Protected blobs before and after:

| Path | Required and actual Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The historical `reference/v0.3-rc1/**` working-tree bytes remain unchanged.
Contracts, arithmetic, FSM, catalogue, SDK, gate, workflows, task inputs and
`.aiops/` remain unchanged. No locked file was edited, even transiently.

Contract-defined observed behavior matches the existing contract; no explicit
contract violation was found. Existing characterization only: a new key for an
already accepted source/amount can append an economically inert journal entry.
This adds no repeated-source contract semantics. Before any refund the existing
bearer flag is `NONE`; binding the example's partial refund makes it `UNDEFINED`.
No implementation/design deviation was needed. Procedural deviations are the
supervisor-required omitted fetch, uncommitted delivery and absent remote CI.

| Required remote evidence | Run ID | Status / conclusion |
|---|---|---|
| Exact-final-head KTX kernel verification | Not available | Not run/queried; final implementation commit not yet created. |
| Exact-final-head KIX protocol verification | Not available | Not run/queried; final implementation commit not yet created. |
| Non-author exact-head review / audit floor A2 | Not available | Pending supervisor orchestration. |
| Post-merge main CI | Not applicable | No merge. |

Local readiness is limited to the checks above. Full hosted CI (including
untouched historical Move/circuit/local-chain checks), external provider
behavior/authentication, customer credit, bank execution, legal compliance,
production durability and distributed fencing were not tested or inferred.
No real services, funds, secrets, public endpoint, chain network or production
runtime was used. UNKNOWN is never translated into absence or completion.
Refund liability remains **UNDETERMINED — User/legal through I10**; provider
authentication remains **UNDETERMINED — Toss/User**; event-identity policy
remains with **Astra**. No provider-history conversion, identity derivation,
cancellation initiation, burden selection, external-return closure or new
protocol command is implemented. Remaining work is supervisor publication,
non-author exact-final-head review/A2 evidence and both required completed/
success KTX/KIX gates. Nothing here authorizes a ready transition or merge.
