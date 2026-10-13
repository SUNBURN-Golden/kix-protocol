# rs-1-issuercap-probe — does concurrent `IssuerCap` use by reference serialize?

Evidence for KIX program node `rs-1-issuercap-probe`: a named, rerunnable
localnet probe of the profile §13 decision criterion — two concurrent
issuer-signed transactions using the same `IssuerCap` by reference (`&`) —
plus the committed raw output and this note. The probe implementation is the
existing probe block in `reference/rights_scale/client/localnet.mjs` (lines
462–546), unchanged; the new runner `scripts/run_issuercap_probe.py` gives it
an independent entry point and a stable receipt. This session did not commit,
push, open a pull request, or edit `.aiops/` or `docs/tasks/`. The supervisor
owns git.

## Identity

| Item | Value |
|---|---|
| Task | `rs-1-issuercap-probe` — RS-1 probe: does concurrent IssuerCap use by reference serialize? No task issue; no `docs/tasks/` file for this node |
| Observed `origin/main` | `7b6a293e903845ff9c06a19f9a02c075d1790089` (local ref; `git fetch` not run — the supervisor forbids network/GitHub actions in this session) |
| Branch | `agent/kix-rs-1-issuercap-probe` |
| Task base (session-start HEAD) | `7b6a293e903845ff9c06a19f9a02c075d1790089` — identical to observed `origin/main`; no delta |
| Implementation commit | none. The supervisor owns git. The worktree is dirty on the task base |
| Deliverables | `scripts/run_issuercap_probe.py`; `validation/2026-10-14-rs-1-issuercap-probe/issuercap-probe.json` (raw output); this note |

## Measured result

Two issuer-signed `issue` transactions sharing one `&IssuerCap` were prepared
against different gas coins and submitted concurrently on a disposable
one-validator localnet (`{seated:16, ga:0, page_size:4, shards:2}` probe show,
fresh package publish). Raw output: `issuercap-probe.json` in this directory,
copied byte-for-byte from the run receipt.

`probes.issuerCap` verbatim:

- `a`: `"ok"`
- `b`: `{"abort": "SUBMISSION_REJECTED", "detail": "Transaction is rejected as
  invalid by more than 1/3 of validators by stake (non-retriable).
  Non-retriable errors: [Object (0xb0b349de…, SequenceNumber(631), …) already
  locked by a different transaction: TransactionDigest(91PciNtp…) … with 10000
  stake]."}`
- `note`: `"two concurrent issuer-signed issues sharing &IssuerCap; outcome
  recorded, not assumed"`

**Measured fact: the two transactions serialize.** The loser is rejected at
submission by the owned-object input lock — a validation-level rejection, not a
Move abort — and is non-retriable as submitted. A later submission can succeed
(`cancelVersusIssue.cancelRetry: "ok"` in the same receipt shows the
lost-response retry path working). The contrast case in the same block,
`duplicateSlotRace` (`attest_issuance`, no owned input), reaches execution for
both transactions; the loser aborts in Move (`abort: 9`), not at submission.

This result was reproduced twice in this worktree on independent localnets:
the dedicated probe run (`issuercap-probe.json`, chain `FqFRCoyk…`) and the
full rights-scale journey (`run_localnet_rights_scale.py`, chain
`6bQQrsPn…`, same `ok` + `SUBMISSION_REJECTED` shape). It matches the RS-1
session receipt (`validation/2026-10-14-rs-1-public-path/README.md`, per-wave
decisions table).

## Effect on the RS-0 `IssuerCap` decision (profile §13 / RS-0 record question 8)

- The blueprint's `[미확인]` — whether an owned object used only by
  reference (`&`) is still subject to the owned-input lock
  (`docs/blueprints/rights-scale-v1/README.md` §3.1, §3.6) — is resolved on
  this localnet: **yes, it locks; concurrent issuer transactions serialize.**
- This is the raw output profile §13 asked for. The choice among the three
  options — (1) split the cap per page/grant, (2) an authority check that
  uses no owned object, (3) accept the throughput ceiling of one cap — stays
  **OPEN with Astra**, exactly as §13 assigns. This node records the measured
  fact; it does not pick an option, and the cap-split RS-C01 test remains
  closed until that choice is made.
- Consistency with the owner decision
  (`docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md` §2): the
  decision specifies one owned `IssuerCap` per package, `issue` takes
  `&IssuerCap`, and says the probe result wins if it contradicts. The probe
  does not contradict it — the cap is a real owned object and behaves as an
  owned input — so no result-wins override is triggered.
- Throughput implication, recorded not asserted: every issuer-signed op
  (`issue`, `issue_paid`, `cancel_issuance`, `revoke`, `cancel_show`,
  `claim_pages`, `claim_shards`, `seal`, `create_show_control`) takes
  `&IssuerCap`, so issuer-side submissions serialize on that object on this
  profile. Whether that ceiling is acceptable is option 3's question —
  Astra's, with RS-4 load evidence later.

## Locks

`git hash-object` before and after work:

| File | Blob | Status |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | unchanged |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | unchanged |

`git status --short reference/v0.3-rc1` is empty; `git diff --stat origin/main
HEAD -- reference/v0.3-rc1` is 0 lines. `reference/rights_scale/client/localnet.mjs`
is unchanged — the probe is the RS-1 code path, not a second implementation.
Sui framework rev `808640d9b49aecf29d8e6f46033c15eca236efa7` unchanged in both
`Move.toml` files. `.aiops/` and `docs/tasks/` untouched.

## Coverage map (AGENTS.md §7)

| Requirement | Where | Status |
|---|---|---|
| Two concurrent issuer txs sharing `&IssuerCap` — do they serialize? | `localnet.mjs` probe block `probes.issuerCap` (existing, RS-1); this node's runner + committed raw output | covered — measured, twice |
| Rerunnable named probe entry point | `scripts/run_issuercap_probe.py` (new) | new script; exits non-zero if the driver fails or the probe block is absent |
| Raw output committed | `issuercap-probe.json` (verbatim receipt copy; addresses and digests only — ephemeral keypairs, no key material) | covered |
| Contrast: no-owned-input concurrency reaches execution | `probes.duplicateSlotRace` (both submitted; loser aborts in Move) | covered, same run |
| 16-slot profile / 19 Move tests / ZK regression unchanged | no edits under `reference/v0.3-rc1/**`; all suites rerun below | covered |

## Commands actually run and results

All run from this worktree. Toolchain: `sui 1.79.1-808640d9b49a` (verified
cache, sha256-checked), Node `v24.19.0` via `.local/shim`, `.venv` Python
3.12.15. Every command exit 0 unless noted.

| Command | Result |
|---|---|
| `git hash-object` on both locked files (before/after) | `69564b16…`, `b607996c…` — match, unchanged |
| `python3 scripts/check_status_register.py` (+ `--self-test`) | ok; self-test pass |
| `python3 scripts/check_rs_profile_traceability.py` (+ `--self-test`) | blueprint=47 profile=47; self-test pass |
| `python3 scripts/check_read_model_source_map.py` (+ `--self-test`) | queries=13 anchors=128; self-test pass |
| `python3 scripts/check_docs_index.py` (+ `--self-test`) | scanned=66 indexed=63 allowlisted=3; self-test pass |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 37 tests OK |
| `sui move --client.config $KIX_SUI_CONFIG --build-env mainnet test --path reference/rights_scale/sui` | 139 tests, all pass |
| `sui move --client.config $KIX_SUI_CONFIG --build-env mainnet test --path reference/v0.3-rc1/sui` | 19 tests, all pass (regression, unchanged) |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 58 tests OK |
| `python3 -m unittest discover` ×5 (`settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward`) | 22 / 47 / 26 / 22 / 61 tests OK |
| `python3 scripts/check_openapi_contract.py` (+ `--self-test`), `check_integration_gate_openapi.py` (+ `--self-test`), `check_sdk_client.py` (+ `--self-test`) | pass |
| `npm --prefix sdk run conformance`, `run verify-compat` | pass |
| `.venv/bin/python scripts/verify_runtime.py` | all 7 checks: python-tests, node-offline, sdk-import, move-tests, rs1-model-tests, rs1-move-tests, circuit-build |
| `.venv/bin/python scripts/verify_commerce.py` / `verify_canonical.py` | PASS / PASS |
| `.venv/bin/python scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | OK; 7 tests OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | all test binaries pass, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| Storage probes ×4 (`probe_paid_storage.py`, `reproduce_storage_rollback.py`, `verify_paid_recovery.py`, `verify_paid_archive.py`) | all PASSED |
| `.venv/bin/python scripts/run_localnet.py` (16-slot public) | `PASSED_ACTUAL_LOCALNET`, `zk: false`, `kixServicesCalled: 0` |
| `npm --prefix reference/v0.3-rc1/client run setup:zk` then `run test:zk` | fixture ceremony ok (`zkey verify`); regression `status: PASSED`, `ARCHIVED_AND_FRESH_KEYS` |
| `.venv/bin/python scripts/run_localnet.py --private` | `PASSED_ACTUAL_LOCALNET`, `zk: true`, all boundary rejections `ONCHAIN_REJECTED` as expected |
| `.venv/bin/python scripts/run_localnet_rights_scale.py` | `PASSED_ACTUAL_LOCALNET`, 14 scenarios, `failures: []`; inline `issuerCap` probe again `ok` + `SUBMISSION_REJECTED` |
| `.venv/bin/python scripts/run_issuercap_probe.py` (new) | `PASSED_ACTUAL_LOCALNET`; `probes.issuerCap` = `ok` + `SUBMISSION_REJECTED` → **serializes**; receipt at `.local/verification/issuercap-probe.json`, committed copy here |
| `.venv/bin/python scripts/run_localnet.py --paid` | **NOT RUN — environment limit.** Script requires Python 3.12 with SQLite 3.45.1; this machine has venv 3.12→SQLite 3.53.1 and system 3.13→3.46.1. Same pre-existing limitation the RS-1 session recorded; CI provides Ubuntu 24.04 Python 3.12 |

## Contract violations / contract-undefined characterizations (AGENTS.md §8)

- No class-C contract violation found. The locked files and `reference/v0.3-rc1/**`
  were not touched.
- Class B (already recorded by RS-0/RS-1, restated for this node's evidence):
  whether `IssuerCap` serialization is acceptable is the open §13 decision;
  this run adds the measured fact, not the choice.
- The submission rejection is non-retriable *as submitted* (locked input at a
  consumed version); it is not a liveness claim about resubmission, and the
  same receipt shows a later retry succeeding.

## Non-claims

- No performance, throughput, TPS, gas, latency, or contention-reduction
  claim. One-validator localnet, exploratory; the serialization fact is a
  correctness/ordering observation, not a benchmark.
- No claim about multi-validator behavior, testnet, mainnet, or production;
  localnet only.
- No claim that the cap question is decided — the three options stay OPEN
  with Astra.
- No real funds, real PG/bank/KYC calls, public endpoints, secrets, storage
  engine, replication, consensus, R2, or coin/TIX module. Ephemeral keypairs
  and faucet funds only; no key material is committed.

## Remaining uncertainty / follow-up candidates

- `IssuerCap` option choice: OPEN, owner Astra (raw output delivered).
- Whether serialization under a *shared* (consensus) cap or an owned-object-free
  authority check would change behavior is unmeasured — out of scope until
  Astra picks a direction.
- RS-4 load work will quantify the ceiling this serialization creates.

## Deviations from the design plan

- None of substance. The plan's `matrix_15` placeholder is the expanded
  scenario `matrix_15_0_p4_s2` (15 seated slots, 4-slot pages, 2 shards) —
  the smallest matrix case. The plan's optional `journey.log` excerpt was
  omitted; the JSON receipt is the committed raw output.
- `git fetch origin main` was not run (supervisor forbids network/GitHub
  actions); the observed `origin/main` is the local ref, equal to HEAD.
- `.local/shim` was added to PATH for Node 24 / Python 3.12 — the shared
  machine toolchain; `scripts/env.sh` itself is unchanged.

## Exact-head CI

None to report: this session made no commit, so there is no head SHA and no
workflow run. `scripts/` is a non-documentation path, so the change classifies
as full verification on both workflows when the supervisor opens the PR;
AGENTS.md §10 exact-head evidence is a gate dependency, not a gap in this
evidence.
