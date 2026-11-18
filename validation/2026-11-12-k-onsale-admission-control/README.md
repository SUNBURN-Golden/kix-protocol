# k-onsale-admission-control — waiting room and GA routing on the adopted local backend

Node: `k-onsale-admission-control`. Not an ASTRA program-mode session. No issue.
No commit, push, pull request, or comment in this session (the supervisor does
git/GitHub). Record opened 2026-11-12. Branch: `agent/kix-k-onsale-admission-control`.

**State: acceptance passed locally — `merge-ready` candidate pending supervisor
commit/push and exact-head CI.** The acceptance runner
`python3 scripts/onsale_local_check.py` ran green (113 tests, OK, exit 0,
`summary.json` `ok: true`, observed backend version exactly the pin). The
composed stage-5 layer was re-verified unchanged (`durable.test_pure` +
`durable.test_durable`, 94 tests OK; `scripts/stage5_local_check.py` exit 0).
Nothing here is exact-head CI; both workflows must still run on the final head
after the supervisor pushes. No production readiness is claimed.

## Decision applicability guard (CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md §5.1)

- `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 names the backend
  directly (option A: local, non-production PostgreSQL 17.11
  (Debian 17.11-0+deb13u1), single process, single writer, default off,
  production flags false). This is ADOPT with a named backend, not a name-only
  reference. The adoption sentence is present unedited in the merged file.
- Merge commit `bb193efb5d238581096372c8a20bee1271dfe4df` (PR #140) is an
  ancestor of this branch HEAD; the adoption file is byte-identical to the
  merged copy (sha256 `79991809e70412f742e3dae90037779a6b102f227fc338df4579fd858e4342e4`
  on both).
- Dependency `k-stage5-durable-tx` is merged at HEAD: PR #443, merge
  `2ec62ca73ee41f397268944e8e0de98ef9d03305`; `durable/` exists on HEAD and is
  composed unchanged by this node.

## Base (AGENTS §1)

- Task branch HEAD and observed `origin/main`:
  `2ec62ca73ee41f397268944e8e0de98ef9d03305` — **no delta**. Read from the local
  remote-tracking ref; `git fetch origin main` was not run because the
  supervisor rule for this session forbids network actions, so the true current
  main may be newer still.
- No implementation commit SHA and no final task head exist yet (the supervisor
  commits). Nothing here is exact-head CI.
- Tools: `rustc`/`cargo` 1.98.1 (workflow pin); `python3` 3.13.5 (`protocol.yml`
  pins 3.12 — deviation recorded below); node v24.22.1 (CI: 24); npm 11.21.1;
  PostgreSQL 17.11 (Debian 17.11-0+deb13u1) at
  `/usr/lib/postgresql/17/bin/{postgres,initdb}`; psycopg 3.2.6. Host
  preflight passed before implementation; no provisioning was needed.

Locked blobs, before the edits and after the last edit/verification run, identical:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`reference/v0.3-rc1/**`, `durable/**`, `exploration/**`, `readiness/**`,
`runtime/crates/**`, `.aiops/**`, `docs/tasks/**`, `.github/**`,
`ARCHITECTURE.toml`, the plan and the register are untouched.

## Changed paths

- `runtime/ONSALE_ADMISSION_CONTROL.md` — revision `ONSALE-STAGE5-LOCAL-0.1`.
  §§1–8 are kept verbatim; the revision adds a header (id, date, observed base,
  adoption/ancestry evidence, implementation location, unchanged authority
  model), §9 (clause-by-clause local realization map), §10 (open values,
  DECISION_REQUIRED · Astra / UNDETERMINED with owners) and §11 (non-claims).
- `onsale/` (new package, local Python API, no public endpoint):
  `__init__.py`, `tokens.py`, `model.py`, `schema.py`, `unit.py`, `router.py`,
  `room.py`, `test_pure.py`, `test_onsale.py`, `run.py`.
- `scripts/onsale_local_check.py` (new runner entry point).
- `validation/2026-11-12-k-onsale-admission-control/` — this record plus
  `host.json` and `summary.json` written by the runner.
- `docs/README.md` — one index row (location pointer only), required by
  `scripts/check_docs_index.py` for the new validation record.

## Design summary

- `OnsaleSession` **composes `durable.schema.DurableSession` unchanged**: one
  unix-socket connection, one schema per store directory, single-writer
  `FileLock`, SERIALIZABLE transactions, `CommitUnknown` on a failed COMMIT,
  the five-class budget ledger and its pin. It adds nine `onsale_*` tables with
  per-row CRC-32 over the immutable columns (reusing `durable.schema.row_crc`)
  and fails closed at open on any checksum mismatch.
- `onsale_ga_shard.remaining` is the only mutable capacity bookkeeping and is
  outside the row CRC (like `ledger.is_open`); at open it is checked against
  the derived invariant `remaining == initial_capacity − COUNT(committed
  successful admit evidence)` and `remaining ≥ 0`. There is no global mutable
  capacity row.
- `AdmissionUnit` commits identity + payload sha256 + first result + ticket +
  token + token-state transition + shard decrement + append-only evidence +
  negative hint + ledger entry in one transaction. Outcome vocabulary is the
  stage-5 one: `replayed / conflict_retained / capacity / business_rejected /
  new_success`, plus `unknown` on `CommitUnknown`. Capacity writes nothing;
  replay returns the stored first result; a conflicting payload is retained
  once as observation evidence.
- CommandIdentity = stable scope (show + epoch + mode) + principal +
  client_command_id; routing fields are never key components; the payload
  fingerprint is stored separately. Result reads and session views check the
  stored principal (`FORBIDDEN` otherwise).
- Tokens carry exactly the contract §4 fields; the signature is a fixture
  HMAC-SHA256 with a caller-supplied key (generated per test run, never
  committed or stored); the `keyVersion` label is pinned at open. The
  production signature scheme is DECISION_REQUIRED · Astra.
- Reissue closes the old token as terminal `REPLACED` and issues a new token
  with the same `queueTicketId` + `queuePositionIdentity`, new shard/nonce/
  expiry, in one commit; it decrements no shard. Old+new consumption races
  consume capacity once (the old token is terminal before the new exists).
- The expire sweep is a service operation (no command row), bounded by a
  required `max_count` and the `completion` budget; it closes the token's
  inflow ledger entry and appends `expire` evidence.
- `HintRouter` (capacity_aware / power_of_two, caller-supplied seeded RNG) and
  `WaitingRoom` are read-only routing/facade layers: hints never write, and
  the commit-time shard check re-decides. `effectiveRemaining` clamps at zero.
- Every limit is a required constructor argument with no default
  (`OnsaleLimits`, 8 fields; `BudgetSpec`, 5 classes). Fixture numbers live
  only in test code and are labeled not-product.

## Existing coverage mapping (AGENTS §7)

Sufficiently covered by the existing stage-5 suites, reused unchanged (rerun
green here): single-writer locking, SERIALIZABLE transaction mechanics,
`CommitUnknown`/lost-ack semantics, budget arithmetic and pin, ledger open/
close, per-row CRC fail-closed mechanics, replay/conflict vocabulary —
`durable/test_durable.py`, `durable/test_pure.py` (94 tests).

New coverage (documented gaps, contract predicates):

- `onsale/test_pure.py` (61 tests, database-free): GA sum invariant and
  invalid configs; effectiveRemaining arithmetic; versioned negative-hint
  validity (epoch/expiry, never permanent); identity stability under routing
  changes and fingerprint separation; §4 token field names, sign/verify,
  tamper and binding refusals; group-commit first-of count/bytes/max-wait
  boundaries; enqueue/admit/reissue decision paths (replay, conflict-once,
  capacity-no-write, every business refusal, recovery-class refusals,
  rank preservation, single-consumption structure); router strategies,
  hint exclusion, no-mutation; outcome vocabulary and false flags.
- `onsale/test_onsale.py` (52 tests, pinned local PostgreSQL): pin/socket/
  settings; GA creation pin and idempotent/different reconfigure; limits,
  key-version and budget pins at open; atomic multi-row commit; §8 evidence
  fields; monotone ticket seq; coarse versioned artifact without seat/user
  labels; bounded authorized session view; authorized durable result read;
  replay after reopen and after process kill; conflict retained once;
  lost-ack → unknown → read-back replay (enqueue and admit); injected
  mid-write failure leaves no partial rows; second writer refused; sequential
  and threaded admissions never exceed shard capacity; independent shard
  enforcement; sold-out commit returns a versioned hint; optimistic routing
  re-checked at commit; expired hint is not a permanent verdict; session and
  outstanding caps; queue-wait and TTL bounds; epoch isolation; reissue rank
  preservation, chain, old/new race single consumption, refusals, expiry;
  expire sweep (only issued past expiry, max_count resume, completion budget,
  no starvation under inflow saturation); inflow count/bytes/age caps, age
  freed by the completion sweep, replay under saturation, class independence,
  recovery under inflow saturation; per-table CRC tamper fail-closed for all
  nine tables plus the composed durable observation table; shard-remaining
  tamper fail-closed; false flags on every result.

## Commands actually run and results

| Command | Result |
|---|---|
| `python3 -m unittest onsale.test_pure -v` | 61 tests, OK |
| `python3 -m unittest onsale.test_onsale` | 52 tests, OK (pinned PostgreSQL 17.11, unix socket) |
| `python3 scripts/onsale_local_check.py` | 113 tests, OK, exit 0; `summary.json` `ok: true`; observed version `PostgreSQL 17.11 (Debian 17.11-0+deb13u1)` |
| `python3 -m unittest durable.test_pure durable.test_durable` | 94 tests, OK (stage-5 regression, composed unchanged) |
| `python3 scripts/stage5_local_check.py /tmp/onsale-s5-recheck` | 94 tests, OK, exit 0, `ok: true` |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 139 tests passed, 0 failed (log: `.local/verification/ktx/kernel-tests.log`) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | clean |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo tree … -p kix-kernel --edges normal --locked` + `sha256sum` + `git rev-parse HEAD` | evidence written to `.local/verification/ktx/` |

Three test-fixture mistakes were found and fixed during the first PG-bound run
(wrong `client_command_id`/`principal` on replay calls, and a sweep time bound
that did not cover all seeded expiries); the implementation behaved correctly
in each case (identity separation, ownership and expiry checks). No
implementation defect was found by the suites after the pre-run self-review
fixes.

### Local CI-equivalent battery (protocol.yml)

All commands below ran in the foreground on this worktree; logs are under
`.local/verification/onsale/` (gitignored). Python is 3.13.5 locally where CI
pins 3.12 (deviation recorded above); `.venv/bin/python` steps ran with
`python3` because no bootstrap `.venv` exists locally.

| Command (protocol.yml step) | Result |
|---|---|
| Stdlib offline document checks — the full authoritative run block, verbatim (65 invocations incl. every `--self-test`, `check_docs_index.py`, `check_ci_test_discovery.py`, `check_loopback_host.py`, `check_cargo_offline_cache.py`, `check_stage5_host.py --self-test`) | all exit 0; `docs index ok: scanned=408 indexed=373 allowlisted=35` |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 139 tests, OK |
| 7 reference suites (`settlement_f01_f03` 224, `booking_resale_admission` 954, `credit_advance_f04` 230, `ai_delegation` 169, `token_reward` 397, `provider_facts` 86, `payment_effects` 28) | 2088 tests, all OK |
| `check_openapi_contract.py` (+`--self-test`), `check_integration_gate_openapi.py` (+`--self-test`) | pass |
| `python3 -m unittest integration_gate.test_offline_limits` | 9 tests, OK |
| `check_sdk_client.py` (+`--self-test`) | `sdk client pin ok: commands=84 node=24.22.1` |
| `npm --prefix sdk run conformance` | 7 tests, 7 pass, 0 fail |
| `npm --prefix sdk run verify-compat` | `ok: true`, BOOTSTRAP bootstrap-2 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 339 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| `python3 scripts/verify_commerce.py --report .local/verification/commerce.json` | `result: PASS` (CALCULATION_ONLY, externalCalls 0) |
| `python3 scripts/verify_canonical.py --report .local/verification/canonical.json` | `result: PASS` |
| `python3 scripts/probe_paid_storage.py --python /usr/bin/python3 --directory .local/storage-probe --cycles 3 --report …` | `NO_FAILURE_REPRODUCED` |
| `python3 scripts/reproduce_storage_rollback.py --report …` | `INJECTED_ROLLBACK_REJECTED_BEFORE_CANCELLATION` |
| `python3 scripts/verify_paid_recovery.py --report …` | `PASSED`, 2 cases, SYNTHETIC chain, MOCK money |
| `/usr/bin/python3 scripts/verify_paid_archive.py --report …` | `PASSED`, 2 cases, SYNTHETIC chain, MOCK money |
| rights-scale offline node regressions (`zk-policy-v2`, `zk-helpers`, `ptau-header`) | 267 + 166 + 34 = 467 pass, 0 fail |

KTX kernel verification equivalents (ktx-kernel.yml) are in the table above
(architecture verifier + 7 tests, `cargo test -p kix-kernel` 139 passed,
clippy/fmt clean, dependency evidence in `.local/verification/ktx/`).

**Merge-tree note:** this branch HEAD equals the observed `origin/main`
(`2ec62ca`), so there is no base delta to simulate; the working tree checked
here is the delivery content. If main moves before the supervisor pushes, the
docs-index and the rest of the battery must be re-checked on the actual merge
tree (the stage-5 fix-round-1 precedent).

### NOT_RUN locally (and why)

- `bash scripts/bootstrap.sh` — installs the pinned Sui CLI and locked
  dependencies over the network; the supervisor rule forbids network actions.
- `.venv/bin/python scripts/verify_runtime.py`, `scripts/run_localnet.py`
  (plain/`--paid`/`--private`), `scripts/run_localnet_rights_scale*.py` — need
  the bootstrap `.venv` and a Sui binary/local chain; none is present and no
  network provisioning is authorized. No Sui testnet/mainnet is touched.
- ZK steps (`setup:zk`, `test:zk`, phase-1 cache) and the `rights-scale` job's
  bootstrap/chain/ZK steps — need snarkjs dependencies, the ceremony and a
  local chain; not run. The three dependency-free offline rights-scale node
  regressions did run (battery table above).
- Exact-head KTX/KIX CI — the supervisor commits and pushes; both workflows
  must run on the final head. No CI run ID exists yet and none is claimed.

## Characterizations (contract-undefined, class B — recorded, not invented)

- `runtime/ARCHITECTURE.toml` declares `oltp_major = 18` while the adopted pin
  is PostgreSQL 17.11. Recorded as a characterization only; the toml is not
  edited by this node.
- `source_commit_position` in hints/artifacts is a local monotone commit
  counter (tickets + token-state + evidence rows), never a chain source cut
  (ADR-0001 §9).
- The `cancel` budget class exists as a required slot with no writer: this
  revision creates no cancel command (contract §10).
- Group commit is realized as the pure proposal function `propose_group`
  (first of count/bytes/max wait); there is no batched network writer locally,
  and no latency/throughput number is claimed.
- Local Python is 3.13.5 while `protocol.yml` pins 3.12; the stdlib-only
  checks and suites ran on 3.13.5. Recorded as a deviation, not a CI claim.
- Key rotation with a changed key but the same `keyVersion` label makes
  previously issued tokens fail signature verification (business rejection);
  rotation policy is part of the open production signature decision.

## Contract violations found

None. §§1–8 predicates are realized as mapped in contract §9; no locked file
or authoritative contract was changed to make a test pass.

## Non-claims and open values

Contract §11 applies in full: no production readiness, durability equivalence,
power/OS crash behavior, hardware flush, independent failure domains, bank
exactly-once, chain finality, distributed fencing, legal compliance,
SLO/TPS/p99/RTO/RPO numbers, or independent acceptance. All evidence is
builder-authored local fixture evidence, before non-author review, Astra
audit, exact-head CI and User merge. All execution flags are false;
`LOCAL_ONSALE_FIXTURE_ONLY` is the only local label. No cross-store atomicity
between the token layer and reserved-seat `DurableUnit` is claimed. Open
values (fairness numbers, capacities/TTL/caps, routing strategy, signature
scheme, group-commit bounds, retention, refund/reopen invalidation, expired-
ticket rank revival) stay DECISION_REQUIRED · Astra / UNDETERMINED with the
owners named in contract §10; this node invents none of them.

## Remaining uncertainty and follow-up candidates

- Exact-head CI on the supervisor's final head (both workflows) is still
  required. HEAD equals the observed `origin/main`, so no merge delta was
  simulated; see the merge-tree note in the battery section.
- Astra decisions on the §10 open values before any production-facing use.
- A future node may bind the reserved-seat authority and the token layer in
  one journey; cross-store atomicity is explicitly not claimed here.
- The ARCHITECTURE.toml `oltp_major` characterization needs an owner decision
  if the pin and the declaration are to be reconciled.
