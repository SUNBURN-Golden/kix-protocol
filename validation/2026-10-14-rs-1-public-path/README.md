# rs-1 — public path on the extended profile at 1,024 slots (localnet)

Evidence for KIX program node `rs-1`: the new `kix_rights_scale` Move package,
the pure-Python reference model, shared vectors, the actual-localnet driver, and
the workflow job, all on the extended public profile. The 16-slot reference
profile (`reference/v0.3-rc1/**`) is byte-identical; the two locked kernel blobs
are unchanged. This session did not commit, push, open a pull request, or edit
`.aiops/` or `docs/tasks/`. The supervisor owns git.

## Identity

| Item | Value |
|---|---|
| Task | `rs-1` — RS-1 public path on the new profile at 1,024 slots (localnet). No task issue; no `docs/tasks/` file for this node |
| Observed `origin/main` | `4813388b5bcde72c298c7392ff5230316da44470` |
| Branch | `agent/kix-rs-1` |
| Task base (session-start HEAD) | `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1` — the commit the owner decision names. The branch is behind `origin/main` by 43 commits; no rebase or merge was performed |
| Implementation commit | none. The supervisor owns git. The worktree is dirty on the task base |
| Authorization | owner delegate Option 2, 2026-10-13 — implement against draft profile 0.1 @ `9b12626b…` as it sits; recorded in `docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md` and `docs/decisions/archive/rs-1.decision_answer.md` |
| Profile status | `docs/contracts/RIGHTS_SCALE_PROFILE.md` stays draft (`초안`) until Astra review at the RS-1 ARCHITECTURE gate. Not edited |

## What landed

- New Move package `kix_rights_scale` at `reference/rights_scale/sui/` — one
  module `rights_scale.move` (~1,300 lines), five test files, `Move.toml`/`Move.lock`
  pinned to the same Sui rev `808640d9b49aecf29d8e6f46033c15eca236efa7`.
- Shared-object architecture per profile 0.1 §3: `ShowControl` (shared, one per
  show), `InventoryPage` (shared, `derived_object::claim` under
  `PageKey{index}`, seated or GA mode), `PaymentRefShard` (shared, derived under
  `ShardKey{index}`, keyed by payment ref hash mod S), `IssuerCap` (owned,
  minted at `init`, no transfer or burn function).
- Full public-path op set: `create_show_control`, `claim_pages`, `claim_shards`,
  `seal`, `issue`, `attest_issuance`, `issue_paid`, `cancel_issuance`,
  `attest_payment`, `offer`, `accept_gift`, `accept_sale`,
  `authorize_admission`, `consume`, `refund`, `revoke`, `cancel_show`, plus the
  hot-potato `Bundle` (`begin_bundle`/`bundle_issue`/`finish_bundle`,
  `MAX_BUNDLE_CHAIN = 8`).
- Localnet fixture constants in one module, commented `localnet default; Astra-owned`:
  `PROFILE_VERSION = 1`, `MAX_BUNDLE_CHAIN = 8`, `LOCALNET_SHOW_SLOTS = 1024`,
  `LOCALNET_PAGE_SLOTS = 64`, `LOCALNET_PAYMENT_SHARDS = 4`, shard routing
  `blake2b256(show_id || payment_ref || profile_version) mod S`.
- `reference/rights_scale/model.py` — in-memory model mirroring Move semantics
  and abort codes, with an `@atomic` snapshot/restore decorator and
  `check_invariants` (page conservation `free+reserved+issued+retired ==
  capacity`, generation monotonicity, slot range, shard range).
- `reference/rights_scale/replay.py` + `vectors/public_path.json` — one vector
  set replayed by both `test_model.py` and `compare_localnet.py` so the model
  and the chain are exercised by identical operations.
- `reference/rights_scale/client/` — Node 24 / `@mysten/sui` 2.30.0 localnet
  driver (`localnet.mjs`, `types.mjs`, own `package.json`/`package-lock.json`).
  Uses ephemeral keypairs and faucet funds only.
- `scripts/run_localnet_rights_scale.py` — retargeted copy of the existing
  `run_localnet.py` harness: builds a disposable one-validator localnet on
  loopback (ports 9000/9123), refuses to kill an existing process on a port
  collision, runs `compare_localnet.py`, writes a JSON receipt.
- `scripts/verify_runtime.py` — two additive checks (`rs1-model-tests`,
  `rs1-move-tests`); all pre-existing checks untouched.
- `scripts/bootstrap.sh` — one additive `npm ci` line for the new client.
- `.github/workflows/protocol.yml` — additive `rights-scale` job (PRs to
  `main`, `ubuntu-24.04`, Python 3.12 + Node 24): bootstrap, model tests, Move
  tests, and the localnet driver. Required-check shape consistent with the
  protocol job (`!draft` guard included). No existing job was edited.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md` — RS-1 row updated to
  `in progress; authorized against draft 0.1 @ 9b12626b`. RS-0 row unchanged.
- `docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md` and
  `docs/decisions/archive/rs-1.decision_answer.md` — owner-decision records,
  per the decision.

## Locks

`git hash-object` before and after work:

| File | Blob | Status |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | unchanged |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | unchanged |

`git status --short reference/v0.3-rc1` is empty; `git diff --stat origin/main
HEAD -- reference/v0.3-rc1` is 0 lines. The 16-slot `Move.toml` Sui rev is
unchanged; the new package pins the same rev. `.aiops/` and `docs/tasks/`
untouched.

## Per-wave decisions recorded here

| Decision | Value | Basis |
|---|---|---|
| Package path / name | `reference/rights_scale/sui`, package `kix_rights_scale`, module `rights_scale` | outside `reference/v0.3-rc1/**` per contract §2; distinct on-chain package id |
| `PROFILE_VERSION` | `1` | owner decision fixture, localnet default; Astra-owned |
| `MAX_BUNDLE_CHAIN` | `8` | owner decision fixture; not the protocol-limit arithmetic (512-event ceiling). PTB at exactly 8 succeeds; 9 aborts `EBundleTooLarge` — confirmed on localnet |
| `LOCALNET_SHOW_SLOTS` / `LOCALNET_PAGE_SLOTS` / `LOCALNET_PAYMENT_SHARDS` | `1024` / `64` / `4` | owner decision / fixture values, not operational policy |
| Shard routing | `blake2b256(show_id ‖ payment_ref ‖ profile_version) mod shard_count` | contract §3: "payment ref bytes determine the shard". The owner text reads `…‖ page_index ‖…`; hashing the page index would be constant per show and could not route refs, so the payment ref is hashed. Same construction in Move and `model.py`; cross-checked by `routing_tests.move` |
| Claim ordering | `(page_index asc, claim_sequence asc)` | owner decision; `claim_pages` takes `from`,`count` contiguous ranges and pages sort by index |
| `Claimed` derived-object ID coefficient | measured **2 new objects per page claim tx** on localnet (object ID + the `Claimed` sentinel object) | localnet `pageClaimMeasurements` in the journey receipt — measured, not assumed |
| `IssuerCap` concurrency | measured on localnet: two concurrent issuer-signed txs sharing `&IssuerCap` → one `ok`, one `SUBMISSION_REJECTED` (owned-object lock, non-retriable) | `probes.issuerCap` in the receipt. This is the `rs-1-issuercap-probe` result; it does not contradict the owner decision (single owned cap, `issue` takes `&IssuerCap`) and means issuer ops serialize on the cap object |
| Page claim batching in the driver | 8 pages per `claim_pages` PTB | driver-side chunking constant to stay under localnet gas budgets; a driver choice, not a protocol limit |

## Coverage map (contract §8.1 RS-1 assignment)

| Predicate | Where | Status |
|---|---|---|
| RS-C01 one-slot-one-right | `duplicate_issue`, `attest_issuance` duplicate-ref abort, `duplicateSlotRace` probe on localnet | covered |
| RS-C02 conservation | `check_invariants` + `conservation_invariant_*` Move tests (incl. full 1,024-slot loop) | conservation covered; GA redistribution (sentence 2) **not implemented** — no such §3 operation; stays `DECISION_REQUIRED · Astra` per owner decision |
| RS-C03(a) stale-generation resend | `expected_generation` arg on `issue`/`issue_paid`/`refund`/`revoke`; `stale_generation` aborts | covered |
| RS-C04 atomic cross-page bundle | `bundle_cross_page`, bundle tests, localnet bundle probes | covered |
| RS-C05 bounded bundle | limit−1/limit/limit+1 in Move tests + localnet (8 ok, 9 `EBundleTooLarge`) | covered |
| RS-C06(a) closed-show rejection | `assert_open` on all consumption paths; `consume_when_open`, `closed_*` tests | covered |
| RS-C07(a) cancel-show semantics | `cancel_show` bumps `cancel_generation`, closes show; issue/offer/consume/refund abort; `cancel_issuance` still works; localnet `cancelRace` probe | covered |
| RS-C08 reissue staleness | generation bump on refund/revoke makes old ticket unusable; `stale_ticket_after_reissue` | covered |
| RS-C15 staged creation | `create → claim_pages → claim_shards → seal`; `seal` requires all pages and shards; double-claim aborts in `derived_object` | covered |
| RS-C16 cross-object rejection | wrong-page/wrong-shard/foreign-show aborts; `ENotSealed` before seal | covered (see contract-undefined notes) |
| RS-C14 public share | public journey only; private/delegated paths not implemented (RS-2/RS-3) | public share covered |

## Contract-undefined characterizations (§8 class B)

- **"Old-generation `ShowControl`"** (C16) is not constructible: the control is
  a unique shared object with mutable `open`/`cancel_generation`, not a
  versioned object chain. The stale-generation case reduces to `open=false`
  / stale `expected_generation` rejections, which are tested.
- **`IssuerCap` serialization** is a measured fact, not a design bug: sharing a
  single owned `IssuerCap` by reference serializes issuer transactions at the
  object lock. Recorded above; throughput implications are out of scope (RS-4).
- **Routing-hash input wording** — see the per-wave decisions table.
- **`revoke` after `cancel_show`** is allowed (model and Move agree): `revoke`
  asserts no `open` because retiring an issued ticket is not consumption. The
  contract lists only consumption ops under `open`-gating. Observed
  characterization, matches the model.

## Commands actually run and results

All run from the worktree with the repo toolchain: `sui 1.79.1-808640d9b49a`,
Node `v24.19.0` via `.local/shim`, `.venv` Python 3.12.15. Every command exit 0
unless noted.

| Command | Result |
|---|---|
| `sui move --client.config $KIX_SUI_CONFIG --build-env mainnet test --path reference/rights_scale/sui` | 139 tests, all pass |
| `sui move test --path reference/v0.3-rc1/sui` | 19 tests, all pass (regression, unchanged) |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 37 tests OK |
| `.venv/bin/python scripts/verify_runtime.py` | all 7 checks pass: python-tests (207), node-offline, sdk-import, move-tests, rs1-model-tests, rs1-move-tests, circuit-build |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 58 tests OK |
| `python3 -m unittest discover -s reference/{settlement_f01_f03,booking_resale_admission,credit_advance_f04,ai_delegation,primitive_commerce}` | 20 / 47 / 26 / 22 / 37 tests OK |
| `python3 scripts/check_openapi_contract.py`, `check_integration_gate_openapi.py` | pass |
| `npm --prefix sdk run conformance`, `run verify-compat` | pass |
| `.venv/bin/python scripts/verify_commerce.py`, `verify_canonical.py` | PASSED |
| `.venv/bin/python scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | PASS |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | all pass |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| Storage probes ×4 | PASSED |
| `.venv/bin/python scripts/run_localnet.py` (16-slot public journey) | `PASSED_ACTUAL_LOCALNET`, authority SUI_MOVE, `kixServicesCalled: 0`, `zk: false` |
| `npm --prefix reference/v0.3-rc1/client run setup:zk` then `run test:zk` | fixture ceremony (fresh local phase-1 + contributed mint/spend keys, `zkey verify` ok); regression `status: PASSED` |
| `.venv/bin/python scripts/run_localnet.py --private` | `PASSED_ACTUAL_LOCALNET`, `zk: true`, revocation/cancellation nullifier boundaries all `ONCHAIN_REJECTED` as expected |
| `.venv/bin/python scripts/run_localnet_rights_scale.py` | `PASSED_ACTUAL_LOCALNET` — see receipt below |
| `.venv/bin/python scripts/run_localnet.py --paid` | **NOT RUN — environment limit.** The script guards `sys.version_info[:2] == (3,12)` and `sqlite3.sqlite_version == "3.45.1"`. Available interpreters: venv 3.12.15 → SQLite 3.53.1; system 3.13.5 → SQLite 3.46.1. No 3.45.1 build exists on this machine. Pre-existing limitation, unrelated to this task |

## RS-1 localnet receipt (this run)

`status: PASSED_ACTUAL_LOCALNET`, `authority: SUI_MOVE`, `kixServicesCalled: 0`,
`zk: false`, `ownGas: true`, one-validator committee,
`networkFaultToleranceTested: false`, `failures: []`,
`modelDivergence: null`. Scenarios (all passed):
`l1_1024_public_path` (issue→gift→resale→admission→consume→refund→revoke→
cancel→reissue at full 1,024-slot conservation), `ga_small_conservation`,
`matrix_15_16_17`, `matrix_15`, `matrix_16`, `matrix_17`, `matrix_1023`,
`matrix_1024`, `matrix_1025`, `page_size_1`, `page_size_4`, `page_size_256`,
`seated_page_edge_63_64_65`, `ga_page_edge_63_64_65`, `double_page_edge_127_128_129`,
`page_size_1024`, `shard_count_1`, `shard_count_2`, `shard_count_8`.

Probes: `issuerCap` (one ok / one `SUBMISSION_REJECTED` — serialized, see
above), `duplicateSlotRace` (exactly one success, loser no state),
`bundleAtomicity` (cross-page all-or-nothing), `concurrentBundles` (exactly one
success), `cancelRace` (cancel rejected on the shared-cap lock, retry ok —
serial-consistent), `foreignControl`/`foreignPage`/`wrongShard` rejections,
`staleGeneration` rejections, `pageClaimMeasurements` (2 objects/page claim).

Receipt file: `.local/localnet/rights-scale-<run>/journey/` (JSON; the `.local`
tree is gitignored — receipts are regenerated by the driver).

## Exact-head CI

None to report: this session made no commit, so there is no head SHA and no
workflow run. The new `rights-scale` job and the `protocol` job will run when
the supervisor opens the PR. AGENTS.md §10 exact-head evidence is therefore
**not yet established**; it is a gate dependency, not a gap in this evidence.

## Non-claims

- No performance, contention-reduction, gas, TPS, latency, or anonymity claim.
  The page-claim counts and probe timings in the receipt are exploratory lower
  bounds on a one-validator localnet, not measurements.
- No claim that the 1,024-slot profile improves anything over the 16-slot
  reference; results are never summed across profiles.
- No production, testnet, or mainnet deployment; no real funds, real
  PG/bank/KYC calls, public endpoints, secrets, storage engine, replication,
  consensus, R2, or coin/TIX module.
- The localnet disables zkLogin background JWK fetching in the disposable
  validator config (loopback-only run); this is a harness choice, not a
  network property.
- Model↔chain agreement is over the shared vectors only; it is not a proof of
  equivalence for arbitrary operation sequences.

## Deviations from the design plan

- `MAX_BUNDLE_CHAIN = 8` (owner decision) instead of the plan's 512-event
  arithmetic ceiling. The owner value is deliberately conservative; both 8-ok
  and 9-rejected are verified on localnet.
- Workflow job added per owner decision (the plan flagged workflow edits as
  needing authorization — it was granted). The job is additive only.
- Paid journey (`run_localnet.py --paid`) could not run in this environment
  (SQLite pin). Not bypassed; recorded as a gap for the CI environment, which
  provides Ubuntu 24.04 system Python 3.12.
- `LOCALNET_PAYMENT_SHARDS = 4` — the owner text did not pin a shard-count
  fixture; 4 chosen and labeled `localnet default; Astra-owned` alongside the
  other constants.

## Remaining uncertainty / follow-up candidates

- `rs-1-issuercap-probe` showed cap-object serialization. Whether one cap per
  show (vs per issuer) or a different authority object shape is wanted is an
  Astra question at the ARCHITECTURE gate; the probe receipt is the evidence.
- GA redistribution operation: `DECISION_REQUIRED · Astra` (unchanged).
- Astra architecture review of profile 0.1 + RS-0 decision record happens at
  the RS-1 gate; the profile stays draft until then.
- `state/rs-1.decision_answer.md` was archived to
  `docs/decisions/archive/rs-1.decision_answer.md` by node
  `audit6-rs1-state-answer-archive` after RS-1 merged as #180, content bytes
  unchanged, per the owner decision's retention rule.
- Whether `revoke` should also require `open` is contract-undefined (class B);
  both the model and the Move package allow revoke after cancel and this is
  tested. Flag for Astra if the contract intended otherwise.
