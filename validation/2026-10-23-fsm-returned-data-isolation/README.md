# Settlement and credit returned-data isolation

Node: `plan-fsm-returned-data-isolation`. Builder: Codex, 2026-10-23.
Builder-authored, source-informed, deterministic offline MOCK-only evidence;
not independent A2 review and no capability grade increase.

## Input and provenance

The task input is the supervisor-supplied node specification and read-only
Sonnet design plan in the builder prompt (planner run `1792719718`, supplied
source `/workspace/kix-run/logs/planner_1792719718`). No issue or current
`docs/tasks/` file exists for this node; none was created or edited. This is
not ASTRA program mode and the node is not in `.aiops/program.json`.
Dependencies: `plan-settlement-seeded-property-suite` and
`plan-credit-f04-seeded-property-suite`, whose test modules are present.

Branch: `agent/kix-plan-fsm-returned-data-isolation`.
Initial HEAD/base and locally recorded `origin/main` both equal
`fecb5e993c986080c63b4de41be5c5f476592610` (no local delta).
The supervisor forbids network actions, overriding the §1 fetch instruction:
`git fetch origin main` was NOT RUN. Remote freshness is unverified.
No commit, push, PR, issue, comment, or merge is authorized in this session.
Implementation/final task commit: not created; changes remain in this worktree
over the initial HEAD. Merge SHA and post-merge evidence: not applicable.
Exact-head KTX and KIX CI IDs/status/conclusions: NOT RUN / unavailable.
Local passes do not satisfy the hosted exact-head merge gate.

## Existing coverage mapping (inspected before adding tests)

Paths below are relative to `reference/`.

| Requirement | Existing coverage | Classification and gap |
|---|---|---|
| Exported outer-list clearing | `settlement_f01_f03/test_settlement_fsm.py::SettlementFsmTests.test_external_payment_attempts_leave_the_journal_unchanged` | Sufficiently covered for clearing the outer list; not duplicated as an outer-clear-only case. Nested bodies/entries partially covered. |
| First-result replay | Settlement `test_settlement_fsm.py::SettlementFsmTests.test_same_key_replays_and_a_different_body_is_rejected`; credit `test_credit_fsm.py::CreditFsmTests.test_same_draw_and_repay_notes_do_not_apply_twice` | Partially covered: no caller corruption of returned nested results. |
| Later transitions and restore | Settlement `test_settlement_properties.py::MachinePropertyTests.test_e_seeded_command_sequences` and `test_e_every_journal_prefix_restores_to_itself`; credit `test_credit_properties.py::MachinePropertyTests.test_seeded_machine_runs_hold_every_relation` and `test_restore_reproduces_the_digest_at_every_prefix` | Partially covered: seeded replay/prefix restore exists; mutation plus whole historical envelope comparisons are missing. |
| Nested policy/obligation/distribution, repayment/terms mutation | The replay/property tests above | Not covered as directed returned-object corruption. |
| `view`, credit `view_claim`, nested journal export isolation | Existing lifecycle/property view comparisons and settlement journal-clear test above | Partially covered: explicit nested mutations missing. |
| Previously returned snapshots survive advancement | Historical first-result comparisons in the replay/property tests above | Partially covered: explicit retained view/claim/export lifetime checks missing. |
| Complete-suite discovery and offline document checks | `.github/workflows/protocol.yml`, offline reference and stdlib document steps | Existing infrastructure sufficient; new modules use its default `test*.py` discovery with no workflow edits. Actual local results below. |

## Added evidence and classification

Each suite adds `test_returned_data_isolation.py`, with separate
`ReturnedResultReplayTests` and `CopyIsolationCharacterizationTests` classes.
Only existing fixture functions are imported from lifecycle tests, not their
TestCase classes. Subject/control machines and credit settlement sources are
constructed independently. Calls use deep-copied command arguments, and saved
expected responses use standard-library `deepcopy`, independently of the FSM's
JSON copy implementation. Every mutation is checked to change its target.

Class A (contract-defined and matching):
[settlement §§9.3–9.4](../../docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md#93-멱등키)
and [credit §§7.3–7.4](../../docs/contracts/CREDIT_ADVANCE_F04.md#73-멱등키)
require accepted-command replay to return the first snapshot, changing only
`duplicate=True` and `applied=None`. Tests compare the whole envelope, including
effect and historical phase, immediately, after later valid transitions, and
after restore from fresh unmutated exports. They corrupt first responses and
duplicate responses, and repeat the duplicate-corruption check after restore.
No `reconcile` receipts are included in economic-journal restore expectations.

Settlement cases corrupt nested policy dictionaries, obligation entries/lists,
distribution order and effect dictionaries, using replacement, deletion and
list edits. Commands advance through initiate/authorize/capture/commit/distribute
and a valid partial refund, using existing synthetic fixture amounts/policy.
Credit cases corrupt repayment entries/lists and nested
`open_terms.terms["interest-apr-schedule"]`, including `policy_number_status`
and `decided_value`. They advance through offer/approve/bind/draw, two repayments
and close. Corruption sentinels never enter commands or select product policy;
fresh source terms stay `UNDETERMINED` with null decided values.

Class B (contract undefined, source-informed characterization): public `view`,
credit `view_claim`, nested `export_journal` detachment, and previously returned
object lifetime are observed copying behavior beyond explicit replay predicates.
Journal edits cover settlement `body.policy`/`body.order`, credit
`body.face.obligations`, entry metadata and list removal. Existing journal shapes
are asserted (settlement uses `settlement_id`, credit uses `advance_id`). Corrupt
exports are discarded; only fresh exports are restored. Retained first/ordinary
command responses, views, claim views and exports remain equal to their saved
copies while fresh views track each transition.

After mutations, all fresh entity views, canonical state, digest and journal
exports equal untouched controls. Credit claim views are compared after draw
creates the claim. Both injected settlement sources' views/state/digests/exports
remain equal to the pre-command baseline and available unchanged to restore.
No ownership source is needed. No explicit contract violation was observed.

This extends only the MOCK evidence associated with
[EV-SET / EV-CREDIT](../../docs/status/CURRENT_CAPABILITY_REGISTER.md);
the register itself and its grades remain unchanged.

## Delivery paths

Exactly these four paths are changed:

- `reference/settlement_f01_f03/test_returned_data_isolation.py`
- `reference/credit_advance_f04/test_returned_data_isolation.py`
- `validation/2026-10-23-fsm-returned-data-isolation/README.md`
- `docs/README.md` (one relative index link)

## Actual local verification

Environment: Python 3.13.5; cargo 1.98.1 (`797e8a9bc`, 2026-08-05);
rustc 1.98.1 (`48a229cea`, 2026-09-01). CI pins Python 3.12 and Rust 1.98.1.
All Python test/check execution uses `PYTHONDONTWRITEBYTECODE=1` (version
inspection did not need it). Narrow discovery ran first in separate processes,
then complete suites, then workflow checks. The stdlib check commands below
were invoked sequentially by a Python `subprocess.run` driver which captured
each exit status; every command completed with status 0 unless specified.

| Actual command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03 -p test_returned_data_isolation.py -v` | PASS: 4 tests, 0.067s; all new method names collected. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p test_returned_data_isolation.py -v` | PASS: 4 tests, 0.167s; all new method names collected. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: 184 tests, 1.723s. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS: 146 tests, 6.546s. |
| `python3 scripts/check_status_register.py` and `--self-test` | Both PASS; register unchanged. |
| `python3 scripts/check_rs_profile_traceability.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_read_model_source_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Both PASS; 212 scanned, 177 indexed, 35 allowlisted. |
| `python3 scripts/check_i12_proof_ids.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_delegation_layer_matrix.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_rs_predicate_evidence_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_rs_im_evidence_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_adapter_identity_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_v5_transition_evidence_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_readiness_evidence_map.py` and `--self-test` | Both PASS. |
| `python3 scripts/check_stage5_host.py --self-test` | PASS; plain host acceptance deliberately NOT RUN. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Both PASS; 84 commands, pinned hash unchanged. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Both PASS; productionEndpoint/publicHost remain false. |
| `python3 scripts/verify_runtime_architecture.py` | PASS; v5 + KTX-R1 dependency gate, no durability/performance certification. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101 before compilation: cached `bcs v0.2.1` unavailable; offline HTTP refusal. No Rust test pass claimed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101: same missing cached `bcs v0.2.1`; no Clippy pass claimed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0). |
| `git diff --check` | PASS (exit 0). |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both before-work hashes match the required blobs below. |
| Inline stdlib preservation verifier (`python3 -` invoking `git hash-object`, `git ls-tree -r -z HEAD`, `git show HEAD:<path>` and comparing filesystem bytes/path sets) | PASS after work: both locks match; all 108 files under `reference/v0.3-rc1` byte-identical to HEAD; no extra files. |
| `git status --short`, `git diff --stat`, `git diff -- docs/README.md` | Only the four authorized delivery paths; index has one added link. |

No test or document-check failures occurred. The two broader Rust commands
could not run for an environment dependency reason; no network fallback was
attempted and no implementation/workflow fix was made.

## Preservation evidence

Before work both kernel blobs were checked with `git hash-object`; after work
the stdlib verifier repeated those comparisons against the literal required
values. Both match:

| Locked file | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / identical |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / identical |

The initial worktree was clean. `git ls-tree HEAD reference/v0.3-rc1` recorded
tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` before work. The after-work
verifier compared every one of its 108 tracked files byte-for-byte with HEAD
and checked for missing/extra files, then recorded the same tree ID. No locked
or historical reference file was edited, even transiently. No final-merge blob
check applies because no merge occurred.

## Limits and deviations

Tests are single-process, in-memory evidence. They do not test disk durability,
concurrency, distributed fencing, external exactly-once behavior, provider/bank
execution, chain finality, legal treatment, production readiness, or exhaustive
input/mutation coverage. No runtime, contracts, commands, queries, financial
policy, SDK artifacts, workflows or program configuration change.
No independent audit or exact-head hosted CI evidence is claimed. The supervisor
owns publication and subsequent review/CI gates.

Deviations: fetch omitted under the explicit no-network instruction; no task
document created under the explicit supplied-input boundary; local Python is
3.13.5 rather than CI's 3.12; offline Rust workspace tests and Clippy could not
start because `bcs v0.2.1` is absent from the local cache. Broader hosted jobs involving dependency bootstrap,
SDK/Move/ZK/localnet and provider/storage probes are outside touched paths and
were NOT RUN. No stop-condition resource or product decision was needed.
Future review can assess additional mutation surfaces in a separately authorized
task; this evidence does not define new copy-ownership contracts.
