# plan-capital-operation-replay-vectors builder evidence

Task input: the supervisor-supplied node specification and read-only design in
this session; no issue or matching `docs/tasks/` file exists. Not ASTRA mode.
Observed local `origin/main`, base and starting branch HEAD:
`61c01403116fd161f86bd01a8c7888b8603b0781`.
Branch: `agent/kix-plan-capital-operation-replay-vectors`.
Network/fetch, commits, pushes, PRs and comments are prohibited by the supervisor.
Remote freshness is therefore unverified; local base delta is zero.

## Coverage assessment recorded before new tests

Existing deterministic semantics are sufficient; this task fills a portable
mutation-history evidence gap, without changing the producer.

| Requirement | Before change | Existing evidence / missing transport |
| --- | --- | --- |
| Draw/repay identity | Sufficient semantics; not covered as portable histories | `test_credit_fsm.py::CreditFsmTests.test_same_draw_and_repay_notes_do_not_apply_twice` |
| Repayment ordering and partial/completion amounts | Sufficient semantics; not covered as portable histories | `CreditFsmTests.test_repayment_order_partial_and_double_application` |
| Reconcile/restore without second draw | Sufficient semantics; not covered as portable history | `CreditFsmTests.test_reconcile_replays_the_journal_without_a_second_draw` |
| Exact complete receipts, errors and all public state at each observation | Partially covered | FSM suite and `test_settlement_credit_boundary.py`; full portable mutation histories missing |
| Duplicate notes do not append journal or double exposure | Sufficient semantics | Same-note FSM regression above; new pack exposes it to consumers |
| Conflicts/invalid sequences preserve state | Sufficient semantics | `test_credit_rejection_atomicity.py` methods `test_draw_duplicate_draw_leaves_no_trace`, `test_repay_binding_conflict_leaves_no_trace`, `test_repay_sequence_type_leaves_no_trace`, `test_repay_sequence_gap_leaves_no_trace`, `test_repay_exceeds_outstanding_leaves_no_trace` |
| Historical response versus later current state | Partially covered for transport | F04 §7.3 and same-note regression; complete late replay receipts missing |
| Frozen face and once-per-claim capacity | Sufficient semantics; composition partial | boundary S5, shared-exposure E1/E6, economics consumer vectors; mutation history composition missing |
| Source/artifact integrity and sensitivity | Not covered for new pack | Existing refusal/economics pack patterns only |
| Observer boundaries and owner limits | Sufficient contract; new pack documentation absent | F04 §§7.3–7.5, 7.9, 7.12; Capital refusal pack validates observer inputs, not mutation history |

Snapshots mean public views, claim, accepted journal, canonical state and digest.
Stored rejection identities are excluded from canonical state; no private-cache
immutability claim is made. Source-informed golden captures are not independent
semantic implementations. Contract-defined matching behavior is retained.

## Implementation and acceptance evidence

Added two canonical companion JSON artifacts and a test-only bounded replay
module. No producer source/test/fixture was edited. The golden output pack is
captured from the unchanged machines; it is explicitly source-informed.
Independent arithmetic literals constrain those captures rather than deriving
expected totals from the shared-exposure observer.

| Acceptance | Evidence |
| --- | --- |
| History inventory/citations and complete results | R1/R2/R3; `test_history_inventory_and_citations`, `test_complete_history_vectors` |
| Same key versus same note/new key | R1, full historical/current receipt comparisons; `test_duplicates_preserve_current_state`, `test_historical_receipts_after_later_repayment` |
| Conflicts and invalid ordering preserve public state | R1/R2 exact `CreditError` codes; `test_refusals_preserve_public_state` |
| Reconcile/restore without second draw | R3 plus restore checks for all three histories; `test_reconcile_restore_replay` |
| Frozen face and once-per-claim accounting | Literal committed claim equality at every offer, retained claim/journal face, same-point views; `test_frozen_face_and_shared_capacity` |
| Pins and effective verifier | Both artifact hashes, ordered source inventory, detached error/exposure/replay/source mutations; `test_artifact_and_source_pins`, `test_verifier_sensitivity` |
| Observer/non-authority boundary | Unchanged observer; `test_observation_boundaries`; consumer field guide |

R1 records 12 setup calls and 13 history calls; the final accepted credit
journal has 10 entries. Group outstanding moves 70,000 → 60,000 → 50,000,
while reservation remains 70,000 on one 100,000 face. R2 records 8 setup and
9 history calls; its final journal has 6 entries, outstanding 0 and reservation
50,000. R3 records 8 setup and 3 history calls; its final journal has 5 entries,
outstanding 10,000 and reservation 15,000. Duplicate/rejected calls append
nothing. Reconcile is not a journaled mutation.

Historical same-key replay retains original `credit` and `effect`, changing
only `duplicate=true`, `applied=null`; current snapshots retain later repayments.
New-key repeats of an existing note return current duplicate envelopes with
`effect=null`. All three bound histories restore with the same settlement source,
then replay the original draw without another exposure or journal entry.
Missing-source restore refuses with `SETTLEMENT_SOURCE_REQUIRED`.

## Actual verification commands and results

Commands ran in this worktree with no background shell jobs and no network
commands. Python subprocess runners invoked the listed commands sequentially,
set `PYTHONDONTWRITEBYTECODE=1`, captured output, and stopped on nonzero exit.
No failed check or implementation repair cycle occurred.

For the focused rows below, `C=reference/credit_advance_f04` is a display
abbreviation only. Each command actually used that full path for both `-s`
and `-t`.

| Command | Actual result |
| --- | --- |
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initial worktree clean; both SHAs `61c01403116fd161f86bd01a8c7888b8603b0781`; expected task branch |
| `git ls-files -z` and `python3 -B` pre-edit SHA-256 inventory; `git hash-object` for each locked kernel file | 243 protected tracked paths retained in manifest; both required blobs match before work |
| `python3 -B` one-time fixture/capture heredoc using unchanged setup replay and machines | Wrote canonical source-informed golden inputs/outputs; tests contain no generation path; arithmetic supplied separately |
| `python3 -B -m unittest discover -s C -t C -p test_capital_operation_replay_vectors.py` | 10 passed initially; 10 passed again in focused sequence after adding the boundary-input source pin and simplifying canonical loading |
| `python3 -B -m unittest discover -s C -t C -p test_credit_fsm.py` | 14 passed, including all three cited behavior sources |
| `python3 -B -m unittest discover -s C -t C -p test_credit_rejection_atomicity.py` | 94 passed |
| `python3 -B -m unittest discover -s C -t C -p test_settlement_credit_boundary.py` | 13 passed |
| `python3 -B -m unittest discover -s C -t C -p test_economics_credit_consumer_vectors.py` | 6 passed |
| `python3 -B -m unittest discover -s C -t C -p test_shared_exposure_contract.py` | 19 passed; expected usage-error output is an exercised negative control |
| `python3 -B -m unittest discover -s C -t C -p test_capital_refusal_vectors.py` | 6 passed |
| `python3 -B scripts/check_docs_index.py` and `--self-test` | Both exit 0; index 420 scanned / 385 indexed / 35 allowlisted; negative controls passed |
| `python3 -B scripts/check_credit_evidence_map.py` and `--self-test` | Both exit 0; unchanged 24-row map; 55 negative controls passed |
| `python3 -B scripts/check_settlement_evidence_map.py` and `--self-test` | Both exit 0; unchanged 27-row map; 33 negative controls passed |
| `python3 -B scripts/check_contract_error_codes.py` and `--self-test` | Both exit 0; 199 rows, CLASS_C=0; negative controls passed |
| `python3 -B scripts/check_class_b_index.py` and `--self-test` | Both exit 0; 218 rows; 20 negative controls passed |
| `python3 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; new test reached by existing credit-suite discovery; 18 negative controls passed |
| `python3 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0; 13 negative controls passed |
| `python3 -B scripts/check_openapi_contract.py` and `--self-test` | Both exit 0; 84 commands, existing bytes pinned; negative controls passed |
| `python3 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0; 84 commands, non-production flags retained |
| `python3 -B scripts/verify_runtime_architecture.py` | Exit 0; v5/KTX-R1 dependency boundary passes; durability/performance not certified |
| `python3 -B scripts/test_runtime_architecture.py` | 7 passed |
| `RUSTUP_AUTO_INSTALL=0 cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; workspace tests including locked kernel pass; existing analytics engine acceptance remains ignored without owner-provisioned engine feature/bundle |
| `RUSTUP_AUTO_INSTALL=0 cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0 |
| `RUSTUP_AUTO_INSTALL=0 cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest integration_gate.test_offline_limits` | 9 passed |
| `git diff --check` | Exit 0 |

The unchanged offline reference-suite loop completed successfully: **2,225
tests** across eight suites. Each command below used
`PYTHONDONTWRITEBYTECODE=1` and exited 0.

| Command | Actual result |
| --- | --- |
| `python3 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 224 passed |
| `python3 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 970 passed |
| `python3 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 252 passed |
| `python3 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | 169 passed |
| `python3 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | 397 passed |
| `python3 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | 86 passed |
| `python3 -B -m unittest discover -s reference/payment_effects -t reference/payment_effects` | 28 passed |
| `python3 -B -m unittest discover -s reference/economics -t reference/economics` | 99 passed |
| `python3 -B` final protected-byte/changed-path guard and `git hash-object` for both locked files | 243 protected paths match before/after; both locked blobs match; exactly eight authorized changed paths |
| `git diff --check`; `PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_docs_index.py` | Exit 0 on final documentation; changed files also pass trailing-newline/whitespace checks |

Existing reference tests exercise local subprocess/loopback mocks; they do not
contact external providers or publish endpoints. No external network action
was initiated by this session.

The unmodified `.github/workflows/protocol.yml` offline-reference loop and
`.github/workflows/ktx-kernel.yml` were inspected. The workspace Rust checks
are a superset of KTX's kernel-only commands. The document checker selection
matches the task design's applicable checks; hosted Move/ZK/Node and other
unrelated workflow jobs are not claimed as locally run.

## Changed paths and preserved bytes

Complete delivery path list:

- `reference/credit_advance_f04/fixtures/capital_operation_replay_v1.json`
- `reference/credit_advance_f04/fixtures/capital_operation_replay_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_operation_replay_vectors.py`
- `reference/credit_advance_f04/README.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-15-plan-capital-operation-replay-vectors/README.md`
- `validation/2026-11-15-plan-capital-operation-replay-vectors/protected_bytes.json`

`protected_bytes.json` contains the actual before/after SHA-256 inventories of
243 existing tracked paths: both locked kernel files, all existing producer
paths under credit, settlement and economics (except the explicitly edited
credit README), `reference/v0.3-rc1/**` (108 files), `.aiops/`, `docs/tasks/`,
contracts and CI workflows. All 243 match. All 43 inventoried existing credit
producer/test/fixture paths match. No transient mutation of locked files was
performed. Final Git diff is restricted to the eight paths above.

| Locked path | Before / after Git blob |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / same |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / same |

| Artifact | SHA-256 |
| --- | --- |
| `capital_operation_replay_v1.json` | `831125251e5e0b1767cda4dba444f2c6d391403ba975ef05f17b475eeb124599` |
| `capital_operation_replay_vectors_v1.json` | `a1562367abf9f4de1fcb180786423b9df4a7740da9563c7de2daeebc397005c7` |

## Identity, deviations and remaining delivery gates

Implementation/start HEAD and local observed base are
`61c01403116fd161f86bd01a8c7888b8603b0781`. All delivery changes are uncommitted
by instruction; no distinct final committed task head exists yet. The supervisor
must establish it. No merge commit exists; post-merge locked-blob and main/push
checks are not applicable in this builder session.

| Delivery gate | Run ID | Status / conclusion |
| --- | --- | --- |
| Exact-final-head KTX kernel verification | Not created/queried | UNVERIFIED; GitHub/network prohibited |
| Exact-final-head KIX protocol verification | Not created/queried | UNVERIFIED; GitHub/network prohibited |
| A2 non-author exact-head review | Not available | PENDING; builder verification is not independent review |
| Post-merge main CI | Not applicable | No merge |

Deviations from repository defaults are explicit supervisor instructions:
no `git fetch origin main` (no network), no task-file creation (task is the
supplied node specification), no commits/publication/PR/issue/comments. No
implementation scope deviation from the supplied design was needed. The
source pin inventory additionally includes the unchanged boundary input from
which the synthetic face was copied. Existing offline integration-limit tests
were also run to complete the corresponding protocol CI step. The pre-edit
inventory was initially all tracked files and then scoped to the 243 protected
paths above using the already-recorded before hashes.

Contract violations found: **none**. No new undefined behavior was assigned
semantics. Source-informed observer/history characterizations are not new
contract authority. Stored rejection identities are not included in canonical
state and are not asserted privately immutable.

No new adapter, repayment-source ingestion, protocol command, production
runtime, public endpoint, storage engine, real funds, PG/bank/KYC calls, Sui
execution or secrets are involved. Local tests do not establish hosted CI,
durability, distributed fencing, bank exactly-once, chain finality, legal
compliance or production readiness. Existing ignored engine tests are not
claimed to pass. External Capital consumer acceptance stays **UNVERIFIED**;
there is no published read or external acceptance test.

Observer mapping remains `NOT_BOUND`, repair `NONE`; execution/finality flags
remain false. Product limits, repayment terms and netting remain
**UNDETERMINED — Astra**; legal parties remain **UNDETERMINED — User/designated
legal advisers**. Synthetic group labels and limits confer no legal identity,
approval or exposure authority. Remaining follow-up candidates are external
Capital acceptance, future observer binding (User), product/legal decisions
under those owners, and supervisor review/CI/publication gates. None is added
to this node or `.aiops/program.json`.

Builder result: **READY for supervisor delivery**, subject to the separate review,
exact-final-head CI and human authorization gates above. This is not a merge-ready
claim. All requested local checks passed; no `DECISION_REQUIRED.md` was needed.
