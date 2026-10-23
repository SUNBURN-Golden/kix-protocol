# Open User decisions — October 23 owner-stop supplement

## Basis and provenance

Builder-authored supplement to the [October 22 ledger](OPEN_USER_DECISIONS_20261022.md).
This document records exactly four additional stops, their existing options and
the evidence an owner would need for a handoff. It is not an owner answer,
decision, adoption, independent review or authorization to resume a node.
The historical ledger and its validation record are preserved.

Node: `plan-owner-stop-handoff-addendum`; dependencies:
`plan-plan-open-user-decisions-ledger-20261022` and
`audit13-plan-register-sync-20261023`; audit floor A2, `astra_gate: None`,
`user_merge: False`. This loop-proposed node has no issue or corresponding
`docs/tasks/` document and is absent from `.aiops/program.json`.
Its task input is the supervisor-supplied node specification and design plan.
This is not ASTRA program mode.

Source of the four supplied stop excerpts: KIX planner run 1792716839,
`/workspace/kix-run/logs/planner_1792716839_codex1.prompt.md`, under the exact
node headings named below. The supplied source prefix
`/workspace/kix-run/logs/planner_1792716839` is not an existing literal path.
These excerpts are explicitly attributed task input, not merged contracts or
owner decisions. Additional external state/worktree reads are separately
attributed below; their reported outcomes were not reproduced by this node.

Repository-local facts below were checked in this worktree at starting HEAD
`1d8d228e6fa5cabacf341dd6add0890e8fe95421`, equal to cached `origin/main`,
on branch `agent/kix-plan-owner-stop-handoff-addendum`.
`git fetch origin main` was NOT_RUN under the supervisor's no-network rule;
remote freshness is unverified. Historical SHAs in source records retain their
original attribution and do not identify this supplement's delivery head.
The [distinct validation record](../../validation/2026-10-23-owner-stop-handoff-addendum/README.md)
lists citation checks, actual commands and preservation evidence.

## Owner stops

### plan-plan-bra-section9-inline-error-code-cove

- **Node:** `plan-plan-bra-section9-inline-error-code-cove`.
- **Source:** Supplied stop under this node's heading in
  `/workspace/kix-run/logs/planner_1792716839_codex1.prompt.md` (lines 283–319).
- **Source completeness:** Complete as supplied through `STATUS: DECISION_REQUIRED`.
  Its branch implementation and proposed BRA-RES9 rows were not independently
  inspected; its scope-conflict diagnosis remains attributed to the stop record.
- **Decision owner:** User or orchestrator owning the node specification;
  not the builder.
- **Unresolved question:** How should the requirement that every new BRA-RES9
  row be `COVERED` or `CLASS_B` be reconciled with the restriction to
  `reservation_fsm.py` as the raise source? The supplied record identifies six
  of sixteen §9 codes without literal raise sites there: `CLOCK_REGRESSION`,
  `SLOT_OCCUPIED`, `RESERVATION_EXPIRED`, `ADMISSION_LOCKED`, `RIGHT_NOT_ACTIVE`
  (lifted from `mock_gates.py`), and `UNKNOWN_SETTLEMENT` (re-raised from the
  injected settlement source). It reports that suite tests assert those codes,
  making `CLASS_B` and `CLASS_C` unavailable under the existing checker rules.
- **Existing options:** (a) Add a fenced `PASS_THROUGH` status for asserted codes
  without local raise sites, naming the origin; this changes checker taxonomy.
  (b) Widen BRA-RES9 sources to `mock_gates.py`, closing five rows but leaving
  `UNKNOWN_SETTLEMENT` unresolved outside the permitted suite citations.
  (c) Restrict BRA-RES9 to the ten locally raised codes, explicitly exclude all
  six pass-through codes and narrow the Non-claims sentence; the source says
  the six already have coverage under BRA (five) and SET (one).
- **Source recommendation:** The stop record recommends (c), citing unchanged
  checker rules and no contract/mock/FSM change. This supplement does not endorse it.
- **Repository-local evidence:** [BRA contract](../contracts/BOOKING_RESALE_ADMISSION_GATES.md)
  §9 documents reservation rejections inline. The [coverage map](CONTRACT_ERROR_CODE_COVERAGE.md)
  Non-claims explicitly excludes enumeration of §9. The current
  [checker](../../scripts/check_contract_error_codes.py) `TABLES` has no BRA-RES9
  key; validation rejects an asserted code without a derived raise site.
  [reservation_fsm.py](../../reference/booking_resale_admission/reservation_fsm.py)
  `::_lift` rethrows `GateError` as `ReservationError(error.code)`.
  These facts corroborate the boundary, without verifying proposed branch rows.
- **Branch evidence / verification limits:** No branch validation record or
  candidate identity was supplied or inspected for this entry. The proposed
  sixteen-row inventory and branch checker failure are unverified here;
  an absent BRA-RES9 key in main is not a failed verification of that branch.
- **Owner-authorized handoff evidence:** Explicit owner scope decision and
  revised acceptance issued outside the builder session, identifying allowed
  sources/statuses or exclusions. A future handoff must identify the candidate
  and provide its row inventory, citation derivation and unchanged or expressly
  authorized checker results against the revised acceptance. No taxonomy is
  changed and no option is implemented here.
- **Disposition:** No option or node disposition is selected by this supplement.

### plan-plan-gate-fsm-seeded-journey-differentia

- **Node:** `plan-plan-gate-fsm-seeded-journey-differentia`.
- **Source:** Supplied stop under this node's heading in
  `/workspace/kix-run/logs/planner_1792716839_codex1.prompt.md` (lines 320–346).
  Additional source read separately:
  `/workspace/kix-run/wt/plan-plan-gate-fsm-seeded-journey-differentia/validation/2026-10-23-gate-fsm-seeded-journey-differential/README.md`.
- **Source completeness:** The supplied host-stop excerpt includes options,
  recommendation, owner and a validation pointer. The separately read worktree
  record is branch evidence, not a merged contract or owner answer.
- **Decision owner:** Supervisor / repository owner controlling the execution host.
- **Unresolved question:** Which authorized loopback-capable host will verify
  the candidate after the reported `socket.socket(AF_INET, SOCK_STREAM)` denial
  (`PermissionError: [Errno 1] Operation not permitted`) and subprocess
  `REFUSING_BIND`? No public endpoint is required.
- **Existing options:** (1) Supervisor runs the unchanged tests in its
  loopback-enabled local environment, reviews the outputs and returns any
  implementation failures for correction. (2) A new builder session permits
  local loopback tests under the same scope and production/external-network locks.
- **Source recommendation:** The supplied stop recommends option 1 and says
  not to weaken tests or change gate/CI code to evade the restriction.
- **Repository-local evidence:**
  [test_http_gate.py](../../integration_gate/test_http_gate.py) `::start_process`
  starts the gate subprocess and requires its loopback listening announcement.
  [server.py](../../integration_gate/server.py) binds to loopback and reports
  `REFUSING_BIND` on startup `OSError`. The unchanged acceptance command in
  [protocol.yml](../../.github/workflows/protocol.yml), step
  `Non-production HTTP integration gate`, is
  `python3 -m unittest integration_gate.test_http_gate readiness.test_faults`.
- **Branch evidence / verification limits:**
  `validation/2026-10-23-gate-fsm-seeded-journey-differential/README.md` is absent
  from this checkout. Its separate-worktree record reports an uncommitted
  candidate above historical HEAD `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`.
  It reports exit 1 for the narrow `SeededJourneyDifferentialTests` class and
  two unchanged acceptance runs under each of Python 3.13.5 and 3.12.15,
  blocked by socket denial / `REFUSING_BIND`. These are attributed failed
  verification attempts, not reproduced failures here. Its reported passing
  direct-dispatch diagnostics do not establish HTTP/process acceptance.
  The branch implementation and current candidate identity remain unverified.
- **Owner-authorized handoff evidence:** Exact candidate commit/tree identity
  (including any uncommitted changes), host authorization and host/interpreter
  context, plus complete outputs and exits for
  `python3 -m unittest integration_gate.test_http_gate.SeededJourneyDifferentialTests -v`
  and the unchanged acceptance command. Return actual implementation failures
  for an authorized correction; retain the transport boundary and all locks.
  This supplement grants no host permission and runs none of those tests.
- **Disposition:** No option or node disposition is selected by this supplement.

### plan-plan-rs-map-gap-closure-batch-2

- **Node:** `plan-plan-rs-map-gap-closure-batch-2`.
- **Source:** Supplied stop under this node's heading in
  `/workspace/kix-run/logs/planner_1792716839_codex1.prompt.md` (lines 404–426).
  Additional source read separately:
  `/workspace/kix-run/wt/plan-plan-rs-map-gap-closure-batch-2/validation/2026-10-23-rs-map-gap-closure-batch-2/README.md`.
- **Source completeness:** The supplied excerpt includes the dependency blocker,
  options, recommendation, owners and validation pointer. The separately read
  worktree record supplies reported command outcomes, not independent verification.
- **Decision owner:** Supervisor for dependency provisioning and verification
  handoff; User alone for any change to network authorization.
- **Unresolved question:** How will full workspace verification be completed
  after the reported offline pre-compilation failure for uncached `bcs v0.2.1`?
  Other missing dependencies may surface after that first blocker is resolved.
- **Existing options:** (1) Supervisor prepares dependencies from unchanged
  `runtime/Cargo.lock` in an authorized environment and reruns workspace tests
  and Clippy. (2) User authorizes a separate dependency-download step followed
  by those checks. (3) Defer delivery until a fully cached builder environment
  is available. No option permits bypassing the lockfile, versions, membership or CI.
- **Source recommendation:** The supplied stop recommends option 1; it does
  not request a product-policy value or new protocol command.
- **Repository-local evidence:** [Cargo.lock](../../runtime/Cargo.lock) pins
  `bcs` at `0.2.1`. [RS predicate map](RS_PREDICATE_EVIDENCE_MAP.md) row RS-C09
  and [RS implementation map](RS_IM_EVIDENCE_MAP.md) rows IM-18/IM-19 retain
  their existing statuses and gaps. The branch's proposed coverage is not
  imported into those rows by this supplement.
- **Branch evidence / verification limits:**
  `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md` is absent from
  this checkout and readable only in the separate worktree inspected. It
  reports an uncommitted candidate above historical HEAD
  `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`, 260 Move tests, 167 Python tests,
  27 offline document checks, kernel-only tests/Clippy, architecture and format
  checks passing. It reports workspace tests and workspace Clippy exiting 101
  before compilation for missing cached `bcs v0.2.1` with Cargo explicitly
  offline. These are branch-record reports, not results obtained by this
  supplement; they establish neither workspace success nor a code-test failure.
  Cache completeness and current candidate identity remain unverified here.
- **Owner-authorized handoff evidence:** Owner authorization for the environment
  and any separate download, exact candidate and lockfile identities, dependency
  availability, and actual outputs/exits for
  `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` and
  `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings`
  in that authorized environment. Preserve the locked kernel and all scope
  boundaries. This supplement provisions nothing and runs no Cargo or Move command.
- **Disposition:** No option or node disposition is selected by this supplement.

### plan-plan-plan-register-index-sync-20261023

- **Node:** `plan-plan-plan-register-index-sync-20261023`.
- **Source:** Supplied stop under this node's heading in
  `/workspace/kix-run/logs/planner_1792716839_codex1.prompt.md` (lines 347–403).
  Additional longer state copy read separately:
  `/workspace/kix-run/state/plan-plan-plan-register-index-sync-20261023.decision.md`.
- **Source completeness:** **INCOMPLETE** supplied excerpt: its last line is
  “`git fetch origin main` was NOT_RU”. Do not infer the missing suffix or
  remaining sections from that excerpt. The longer state copy separately
  records fetch as NOT_RUN under its supervisor prohibition, checks and limits;
  it does not make the supplied excerpt complete or provide an owner answer.
- **Decision owner:** User / repository owner.
- **Unresolved question:** How should duplicate synchronization be disposed of,
  and how should acceptance requiring an already occupied validation path be
  revised? The supplied record says the substantive synchronization already
  existed at its starting HEAD and the prescribed record belongs to another node.
- **Existing options:** Retire as superseded by #261, with explicit owner
  acceptance of the existing delivery; revise to independent verification with
  a distinct evidence record and externally revised changed-file/basis acceptance;
  or supply genuinely missing synchronization requirements with revised scope,
  attribution and acceptance. The source's suggested alternative path is
  `validation/2026-10-23-plan-plan-plan-register-index-sync-20261023/README.md`;
  its availability must be checked by a future authorized session before use.
- **Source recommendation:** The supplied record recommends retirement as
  superseded by #261 because it found no missing substantive edit. This
  supplement does not retire the node or accept that recommendation.
- **Repository-local evidence:** [Plan](../DEVELOPMENT_PLAN.md) §5 already lists
  #254–#260. The [capability register](CURRENT_CAPABILITY_REGISTER.md) records
  RS-4/K5/EV-RS pointers and its historical October 23 basis at
  `2393988eeca984f12f0819ac56b6870be1a5832f`. The [docs index](../README.md)
  links the corresponding records. The occupied
  [sync validation record](../../validation/2026-10-23-plan-register-index-sync-20261023/README.md)
  explicitly identifies `audit13-plan-register-sync-20261023`; it is preserved
  under that attribution. These are checkout-visible facts, not new approval.
- **Branch evidence / verification limits:** The supplied stop's historical
  base/HEAD is `3a2ddab0cc56e8c2ccf60c129e8bcd309d48b5af`, attributed there to
  #261. That merge attribution is also visible in local first-parent history;
  no GitHub verification or remote freshness is claimed. The longer state
  copy's reported checks remain its own results, not this supplement's results.
  The truncated excerpt alone cannot establish its final checks or complete scope.
- **Owner-authorized handoff evidence:** Explicit owner disposition. If work
  continues, the owner must issue revised scope and acceptance outside the
  executing builder session, with genuinely missing work or independent
  verification identified, a distinct unused evidence path and exact candidate
  basis. Do not relabel the audit13 record or create artificial synchronization
  edits to satisfy an obsolete changed-file requirement.
- **Disposition:** No option or node disposition is selected by this supplement.

## Evidence availability

Repository-local citations above were checked for file existence and named
sections/symbols/rows; the validation record inventories them. This confirms
where the cited material is, not every semantic assertion or branch outcome.

| Evidence state | Meaning in this supplement |
|---|---|
| Present in the starting main checkout | Independently inspected local file content at the stated starting SHA; remote freshness remains unverified. |
| Absent from this checkout / unavailable branch evidence | Unverified here, not proof that a test or implementation failed. Gate/RS records were readable separately but remain external branch reports. |
| Reported nonzero verification command | An attributed failed or blocked verification attempt: gate host denial or RS dependency failure before compilation. Not a newly reproduced result or proof of an implementation defect. |
| Incomplete excerpt | Supplied duplicate-sync text ends mid-token; separately read material has separate provenance. No missing text is silently reconstructed. |
| NOT_RUN | This session did not execute the command; no pass/fail inference. |

## Non-claims

- No option, node disposition, status, evidence grade, policy value, owner,
  acceptance criterion or protocol command is selected or changed. Policy
  values remain `UNDETERMINED` with their existing owners. Recommendations
  above belong only to their source records; none is endorsed here.
- No blocked node is implemented, resumed, completed, retired or retried.
  Handoff requirements describe evidence for a future owner-authorized session;
  this document supplies no authorization and changes no program status.
- The October 22 ledger, historical validation records, development plan,
  register, contracts, task inputs, `.aiops/`, CI, runtime, locked kernel blobs,
  `reference/v0.3-rc1/**` and activation flags remain unchanged.
- No host/dependency provisioning, measurements, real host preflight, socket
  tests, Cargo/Move/chain execution, external calls, paid services, secrets,
  production runtime, public endpoint, Sui testnet/mainnet, storage engine,
  R2, new coin/TIX module or new protocol command is involved.
- Local document checks establish neither exact-head hosted CI nor non-author
  review, merge readiness, production readiness, durability, distributed fencing,
  bank exactly-once, chain finality or legal compliance. No historical CI result
  transfers to this supplement.
