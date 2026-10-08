# k-a-reestimate — re-estimate of integration (a)

Node: `k-a-reestimate`. Document only. No code, no new tests, no policy values,
no new protocol command.
Issue: none.
Depends on `k1-evidence-close`.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`bb193efb5d238581096372c8a20bee1271dfe4df`.
Branch: `agent/kix-k-a-reestimate`.
This session did not commit, push, open a PR, or comment. There is no
implementation commit SHA. Local results below are not exact-head CI.
Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

The estimate is planning-only. It does not authorize integration (a), R2, a
journal, a storage engine, the v5 crate, or stage 5. The user decision is
`k-a-integration-decision`. The first batch is not complete. `새로 실입력까지
완결된 행: 0` is unchanged.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/INTEGRATION_A_REESTIMATE_20261009.md` | New estimate. T0 17~28, T1 17~28, T2 14~24, each a planning bracket against the historical 18~30. |
| `docs/README.md` | Index only. One row in the 2026-10-08 document table. One validation bullet that names this 2026-10-09 record. |
| `validation/2026-10-09-k-a-reestimate/README.md` | This record. |

`git diff --stat origin/main` lists only `docs/README.md` (2 insertions). The two
new files are untracked, so that command does not list them. `git status --short`
shows all three.

## Dependency evidence

`git log --merges -- validation/2026-10-08-k1-evidence-close` was empty.
`git log --merges --full-history -- validation/2026-10-08-k1-evidence-close`
printed `a059bd69eae321ccfeb5940f3d675b962103d361` (PR #137). That commit is an
ancestor of HEAD.

Merged sentences left intact on this HEAD:

- #138 `a483ab1777ad0c3e15ff71798822cbf6b3666f83`, v5 design §5, option O1.
- #140 `bb193efb5d238581096372c8a20bee1271dfe4df`, backend adoption §6, option A
  for stage-5 local non-production PostgreSQL 17.11 (Debian 17.11-0+deb13u1).

`CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md` §5.1 separates a merged user
decision from adoption of the recommended feature. This estimate quotes those
sentences and does not treat the merges as started implementation.

## Existing coverage (AGENTS §7)

No new tests. The overlap table in the estimate cites the existing tests by
path and function name. None of them subtracts a measured person-day from
18~30. The first-batch 10~16 is not added.

## Commands actually run

Working directory: repository root. Python 3.13.5 (`tomllib` present; the
architecture script imported). Cargo 1.98.1. rustc 1.98.1. Node v20.19.2 and
npm 9.2.0 are present. `sui` and `snarkjs` are absent (`command -v` printed
nothing). `.venv` is absent. `protocol.yml` pins Python 3.12 and Node 24.
Those were not installed.

A later verification command `git fetch origin main` moved `FETCH_HEAD` back
to `origin/main`. The PR #11 measurement below used an earlier
`git fetch --no-tags` of `55a3df4968f5684bb4cb9e3c9781ab5f00165235`. No ref
and no tag were created for that SHA.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0 at session start. Both `bb193efb5d238581096372c8a20bee1271dfe4df`. The same pair again during verification, exit 0. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| `git diff --stat origin/main` | `docs/README.md`, 2 insertions. Untracked files are not listed. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime` | Empty. Exit 0. |
| `git diff --check` | Exit 0, including after this README was added. |
| `wc -l` on `runtime/crates/kix-kernel/src/lib.rs` and the kernel test files | `lib.rs` 663; `contract_edge_cases.rs` 440; `contract_invariants.rs` 589; `e4_state_model.rs` 2202; `observation_slots.rs` 373; `performance_harness.rs` 292; `quarantine_capacity.rs` 335; `transitions.rs` 685; support `coverage_v4.rs` 1168, `evidence_gates.rs` 370, `model_v4.rs` 703, `perf_probe.rs` 623. `git cat-file -s` gave 24159 bytes for `lib.rs` and 11293 bytes for `quarantine_capacity.rs`. |
| `git fetch --no-tags origin 55a3df4968f5684bb4cb9e3c9781ab5f00165235` then `git rev-parse FETCH_HEAD` | Exit 0. `FETCH_HEAD` was that SHA. `git ls-tree -r --long` bytes and `git show FETCH_HEAD:<path> \| wc -l` lines are in the estimate §6. Wire Rust body 44593 bytes / 1220 lines, journal Rust body 33603 bytes / 980 lines. |
| `python3` allocation check of those bytes | `6 * 44593 / 78196 = 3.42`, `6 * 33603 / 78196 = 2.58`, `10 *` the same ratios `= 5.70` and `4.30`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0 on the first run. 53 tests, OK. The recorded `415 != 503` flake did not occur. The test file was not edited. A `ResourceWarning` for an unclosed file was printed; the result line is OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 20 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. 43 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. 20 tests, OK. |
| same for `reference/ai_delegation` | Exit 0. 22 tests, OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. commands=40, pin OK. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. commands=40, productionEndpoint=false, publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. pass. |
| `python3 scripts/check_sdk_client.py` | Exit 1. `node 20.19.2 does not match toolchains.json nodeMajor 24`. |
| `python3 scripts/check_sdk_client.py --self-test` | Exit 1. Same node-major message. |
| `npm --prefix sdk run conformance` | Exit 1. Node v20.19.2, `ERR_UNKNOWN_FILE_EXTENSION` for `sdk/src/manifest.ts`. |
| `npm --prefix sdk run verify-compat` | Exit 1. Same Node, `ERR_UNKNOWN_FILE_EXTENSION` for `sdk/src/jsonschema.ts`. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32. Doc-tests 0. 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. A second run of the same command, used to read the result lines, also exited 0. In binary order those lines are bcs1 3, golden_vectors 4, feature-ir 5, audit_regressions 8, schema_bound 18, feature-semantics 6, kernel lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32, kix-types 6. Sum 128 passed, 0 failed. Five doc-test binaries, 0 tests each. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked -- --list` | Exit 0. Used only to name the binaries in the row above. Tests were not executed by `--list`. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| Relative-link check, `python3 -I` from `/tmp`, on the three changed files | 0 missing links, 0 trailing-whitespace lines. |

## Not run locally

`scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`,
`scripts/verify_canonical.py`, the storage probes, `scripts/run_localnet.py`,
and the ZK steps. No Sui CLI, no snarkjs, and no `.venv`. `bootstrap.sh`
requires Node 24. Node 24 was not installed. The SDK commands above were run
on Node 20 and failed for that reason. They were not repaired by editing the
SDK, `toolchains.json`, or CI.

The PR #11 cold-build (wire 4 pass / 5 fail, journal 1+13 pass) was not
re-executed. The estimate cites `docs/status/PR11_PRESERVATION.md` for those
outcomes. This session only measured the tree at
`55a3df4968f5684bb4cb9e3c9781ab5f00165235`.

## Deviations from the design plan

- The plan's "CRC-framed" description does not match the fetched journal.
  `kix-journal-local` frames with a length prefix and `canonical_hash_bytes`
  (SHA-256 via `Sha256::digest` in that commit's `kix-bcs1`), then fsync.
  No CRC constant. The estimate says so.
- `git log --merges -- <path>` was empty until `--full-history` was added.
- The 2026-10-09 validation bullet is in the 2026-10-08 index list, because
  that is the list the plan named. The bullet text carries 2026-10-09.
- T0 and T1 share one planning sum (17~28). v5-crate construction and a later
  v4-to-v5 migration stay `숫자 없음` rather than a guessed delta. T2 sets the
  journal package to 0, meaning "do not rebuild", with the 3~4 add-back listed
  as what would change it. A partial shrink had no measured size.
- SDK checks were run, failed on Node 20, and were left failed. The plan said
  to run them when Node is present.

## Exact-head CI

Not recorded here. Per AGENTS §11 the final-head KTX and KIX protocol run IDs
belong in the pull-request report after a head exists. This tree is
uncommitted. A draft or skipped run is not a pass.

Both workflow classifiers treat `docs/*` (other than `docs/contracts/*`,
`docs/adr/*`, and `docs/PROTOCOL_MASTERPLAN_*`), `docs/README.md` included, and
`validation/*` other than `validation/2026-09-11/*` as documentation-only.
These three paths match that arm. Root `README.md` does not, and it was not
edited. A hosted run that skips heavy steps is not full verification. The
protocol workflow's own summary text says the green mark in that case is not
a full-verification pass. CI from an earlier SHA does not transfer. CI files
were not edited.

## Contract classification (AGENTS §8)

No explicit contract violation. The estimate does not redefine a contract,
choose a cut-proof option, fill a product number, or edit `docs/contracts/`.

Contract-undefined items recorded in the estimate §7.B, left open:

- The historical 6~10 had no wire/journal split. The 3~6 and 3~4 figures are
  a planning allocation of that bracket by measured bytes.
- Whether the framed fsync journal is inside the log-engine lock.
- v5 construction effort, migration effort, and the blocked fraction of the
  authority and recall packages. Each is `숫자 없음`.

## Non-claims

No production readiness, durability, distributed fencing, bank exactly-once,
chain finality, or legal compliance. No approved TPS, p99, or failure rate.
The 17~28 and 14~24 figures are not a quote, a deadline, or authorization to
start. The first batch is not complete. No I-row moved off 미완결. The #136
merge's option was not inferred. Stage-4 timings were not copied and are not
rankings or SLOs. R2 has no number. The v5 crate has no approved construction
number, and it is not in `runtime/crates` today. No real funds, PG, bank, KYC,
public endpoint, Sui testnet or mainnet, R2, replication, consensus, or
storage engine.

## Remaining uncertainty and follow-ups

- Journal admissibility is `k-a-integration-decision` (User).
- New wire or catalogue exposure of v5 transitions, H_g (A4), the time source
  (A5), an uncooperative executor (A10), I09 numbers, and I11 automatic limits
  stay DECISION_REQUIRED · Astra.
- Toss facts for I02–I05, I08, TM04, and TM05 stay UNDETERMINED · Toss
  technical/contract. I10 stays UNDETERMINED · legal/privacy. I13 and the cost
  inputs stay UNDETERMINED · user / operations owner.
- I12 independent reviewer (A9) and trust-policy approval stay with the User.
- Hosted CI for the exact head does not exist until a head is published.
  A documentation-only skip on that head is not full verification.
- Local SDK conformance needs Node 24, which this host does not have.
