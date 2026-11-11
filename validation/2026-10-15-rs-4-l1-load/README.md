# rs-4-l1 — staged load validation at 1,024 slots (localnet, exploration data)

Evidence for KIX program node `rs-4-l1`: a closed-loop staged-load measurement of the extended
rights-scale profile at the L1 stage size — 1,024 seated slots (the depth-10 leaf-capacity
boundary), page 64, payment shards 4, root history K=4 — run once on a disposable
one-validator localnet on this builder machine. Public, private and delegated paths are
generated, executed and reported **separately**
(`docs/blueprints/rights-scale-v1/README.md` §7 reporting separation; RS-4 node scope).

**Everything here is exploration data.** One-validator localnet samples on a shared virtual
builder host; closed loop (`arrival_rate 0`) plus fixed-k concurrency probes. No SLO, no
throughput claim, no latency claim, no gas-model claim, no durability or fault-tolerance
claim, no production readiness. Fixture values (1,024/64/4/depth-10/K=4) are Astra-owned
test values, not protocol values. The two locked kernel blobs are unchanged.
`reference/v0.3-rc1/**` is byte-identical. This session did not commit, push, open or edit
a pull request, post any comment, or edit `.aiops/`, `docs/tasks/` or CI. The supervisor
owns git.

## Identity

| Item | Value |
|---|---|
| Task | `rs-4-l1` — RS-4 L1: staged load validation at 1,024 slots. No task issue; no `docs/tasks/` file for this node |
| Observed `origin/main` | `10e44d40abd878736b900d768f925725c95a8cd0` (local `origin/main` ref; the supervisor rule for this session forbids network actions, so `git fetch origin main` was not run) |
| Branch / task base | `agent/kix-rs-4-l1`; parent of `82f0a5d` is the observed main — no delta to report |
| Implementation head at measurement time | `82f0a5d2ecb6797a15087d13a1b7d67482de3b09` (recorded in `host.json` as `git_head`) plus the uncommitted transient-retry patch listed under "What landed in this fix round"; the committed delivery head includes both |
| Depends on | `rs-1`, `rs-2`, `rs-3a` (merged localnet journeys reused as regression) |
| Record | `manifest.json` `kix-rs4-l1-load-v1`, `status: PASSED_MEASUREMENT` |

## Result

`receipt.json` / `manifest.json`: **PASSED_MEASUREMENT** — 1,775 steps sampled across the
three paths, 0 expectation mismatches, 0 `unknown`, 0 `driver_error`, every page-conservation
and end-state invariant in the generator's `expected` matched the chain snapshot, and every
requested workload count was processed (no shortfalls). Package
`0x8583ddbb3bc6c2e9bda938f3da9064dfeaf12e48a6580e12d575e3e345627965` on chain
`CUJRbSWxatpHjaHxGQuLr5xbZYsn7KhibbqTmvnY7NUt`, scenario fingerprint
`556ac60b01fcfcaa5a7b46bcc1623b3eaa70ec8c577ffa1558a6ae41bed83785`
(sha256 of `load-scenarios.json`).

| Path | Steps | ok | abort | client_refused | probes | Snapshot vs expected |
|---|---|---|---|---|---|---|
| public | 482 | 458 | 19 | 0 | 5/5 met | free 16 / issued 991 / retired 17 — matched per page |
| private | 1,221 | 1,206 | 12 | 2 | 1/1 met | issued 1,021 / retired 3; `leaf_count` 1,024, nullifiers 34, challenges 34, revocations 3 — all matched |
| delegated | 72 | 59 | 12 | 0 | 1/1 met | grant g1/g2 `open=false, generation=2`; page 14 reclaimed (`delegated_to=null`), page 15 still bound to g2 — matched |

Path timings (submit→finality window per step, sequential driver): public 521,032 ms,
private 1,505,972 ms, delegated 70,719 ms, total 2,138,693 ms
(`2026-10-15T03:36:55Z` → `04:12:34Z`).

## What each path exercised

- **public** (`public/`): 16-page claim in `claim_pages` runs of 8 (the 16-page claim exceeds
  the local gas budget — recorded as a driver bound, MAX_CLAIM=8), five fixed-k=2 concurrency
  probes on slots 512–521, a uniform bundle fill of the remaining 1,014 free slots, paid
  issuance on the last 8 slots of every page, hot-slot rejections (`EStale`, `EInventory`),
  reservation/refund/reissue/transfer/admission/revoke subsets, `cancel_show` of the full
  show and post-cancel refusals (`EClosed`; post-cancel `revoke` still succeeds — it has no
  open check).
- **private** (`private/`): all 1,024 slots issued then shielded — `shield_count: 1024`
  requested and `shields_ok: 1024` actual, the depth-10 leaf-capacity boundary. Includes the
  K=4 root-history probe (a proof bound to a root 4 writes old aborts `ERoot` 19 while one
  3 writes old is admitted), 8 pre-proved proofs invalidated by one revocation
  (`zk_gate:2` aborts) plus re-proof and client-side revocation refusals
  (2 `client_refused`, expected), two concurrent `revoke_with_root` on the same root
  (`one_wins` met; the loser was definitively rejected at submission, then landed on the
  rebuilt-witness retry while the already-revoked sibling aborted `EStale`), 32 fresh
  consumptions, and witness reconstruction from **both** independent event sources:
  `jsonrpc-queryEvents` (45,240 ms) and `grpc-checkpoint-scan` (61,452 ms), 1,024
  `NoteAdded` + 3 `RevocationLeaf` events each, rebuilt roots matching the on-chain roots.
- **delegated** (`delegated/`): two grants on pages 14–15, delegated bundle/single/paid
  issuance, a shared-`GrantControl` read probe (`any` met — both branches landed),
  `EDelegated` refusals of direct calls on delegated pages, holder-signed
  `refund_delegated`, the one-write `revoke_grant` cut and post-cut `EGrantClosed`
  refusals, grant independence, `undelegate_page` reclaim of page 14, and the stranded
  pre-cut reservation on page 15 leaving that page un-reclaimable
  (`undelegate_page`/`issue`/`cancel_issuance_delegated` all refused).

## Probe outcomes (raw: `*/probes.csv`)

| Probe | k | expect | Observed |
|---|---|---|---|
| same_page_issues | 2 | any | both ok |
| duplicate_slot_race | 2 | one_wins | one ok, loser `submission_rejected` (non-retriable invalid: owned-object version conflict) |
| same_shard_attests | 2 | any | both ok |
| cross_shard_attests | 2 | any | both ok |
| bundle_race | 2 | one_wins | one ok, loser `submission_rejected` |
| concurrent_revokes | 2 | one_wins | one ok, loser `submission_rejected` |
| shared_grant_reads | 2 | any | both ok |

Losing branches were rejected by the validator at submission with a definitive non-retriable
verdict (`submission_rejected`, never `unknown`, never resubmitted); `congestion_reject_count`
is 0 for every probe. This matches the RS-1 probe finding that the loser of an owned-object
race may fail at submission rather than aborting on-chain — a characterization, not a
contract change.

## What landed in this fix round (review round 1)

Round 0 (`82f0a5d`) delivered the measurement harness: `scripts/run_rights_scale_l1_load.py`,
`reference/rights_scale/load_plan.py`, `client/load-l1.mjs`, `summarize_load.py`,
`test_load_plan.py`, `test_summarize_load.py`. The review found the measurement itself was
never delivered (the orchestrating session had crashed; `host.json` recorded the pre-commit
`origin/main` head).

This round:

- **Executed the measurement** end-to-end on this worktree: fresh genesis → publish →
  verifier install → all three paths → snapshots → summarize → receipt/manifest. The full
  artifact set is this directory: `host.json`, `load-scenarios.json`, `load-report.json`
  (raw samples), `public|private|delegated/{samples.csv,probes.csv,summary.json}`,
  `receipt.json`, `manifest.json`, this README.
- **`transient()` retry** (`client/chain-kit.mjs`): one bounded retry helper (5 attempts,
  ~400 ms backoff) wrapping the driver's *read* calls — `getObject`, `listOwnedObjects`,
  `listCoins`, `getReferenceGasPrice`, `simulateTransaction` view calls (in `load-l1.mjs`),
  `tx.build` kind resolution, faucet-settle `getBalance`, `getChainIdentifier`, and the
  setup-path `executeTransaction`+`waitForTransaction` pair — plus both event sources in
  `client/chain-witness.mjs`. Motivation: a rehearsal run of this exact workload (1775
  samples, started before the round-0 commit existed) otherwise passed end-to-end but
  recorded one `driver_error` when a single gRPC-web fetch in the ~600-call checkpoint scan
  failed transiently — a transport flake, not data, failing a 35-minute measurement. This is
  the same treatment the driver already gives lost submission responses
  (`reconcileByDigest` ×10). Semantics are unchanged: the scan still reads every checkpoint,
  rebuilt roots are still checked against on-chain roots, a persistent failure still throws
  and is recorded. Retry counts are reported per source
  (`transport_retries` in the `reconstruct` sample detail; both 0 in this run — the recorded
  run needed no retries).
- **Docs index row** in `docs/README.md` (`Stdlib offline document checks` now requires
  `validation/*/README.md` links; `scripts/check_docs_index.py`).

Not touched: `reference/v0.3-rc1/**`, `runtime/**`, `.aiops/`, `docs/tasks/`, all CI
workflow files, Move sources and zk circuits/artifacts, `docs/decisions/`,
`docs/blueprints/`, `DEVELOPMENT_PLAN.md` merge-record table (post-merge index-sync
convention), product or protocol code. No new test needed for the retry itself: it is
transport plumbing under the existing harness, exercised end-to-end by the run recorded
here.

## Locked blobs

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

Also recorded in `host.json` under `locked_blob:*`.

## Existing coverage first (AGENTS.md §7)

| Requirement | Existing coverage | Class |
|---|---|---|
| Load measurement at 1,024 slots, separate per path | none — RS-1/RS-2/RS-3a journeys are correctness replays (16-slot and 1,024-slot state checks), not load records | not covered |
| Real Groth16 proofs at depth-10 capacity | partially — zk regression proves/refuses with fixture keys, 16-show private journey covers semantics | partially covered |
| Fixed-k concurrency evidence on the extended profile | partially — RS-1 probe exists on the 16-slot show | partially covered |
| Witness rebuild from two independent event sources at L1 size | partially — private journey does it at journey scale | partially covered |

## Commands actually run and results

| Command | Result |
|---|---|
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 115/115 pass (includes `test_load_plan`, `test_summarize_load`) |
| `PATH=<node24>:$PATH .venv/bin/python scripts/run_rights_scale_l1_load.py validation/2026-10-15-rs-4-l1-load` | `PASSED_MEASUREMENT`; all three paths PASSED; `shields_ok` 1024/1024; receipt `.local/verification/rights-scale-l1-load.json` |
| `node --check` on `load-l1.mjs`, `chain-witness.mjs`, `chain-kit.mjs` | clean |
| `python3 scripts/check_docs_index.py` (+ `--self-test`) | pass after the index row was added |
| `.venv/bin/python scripts/run_localnet_rights_scale_private.py` | `PASSED_ACTUAL_LOCALNET` — RS-2 regression on the edited shared files (see below) |

Environment: `sui` 1.79.1-808640d9b49a (`.local/bin`), Node v24.19.0
(`/home/box/.local/opt/node-v24.19.0-linux-x64/bin`, the `toolchains.json` major), Python
3.12.15 (`.venv`). The measurement ran on a disposable single-validator localnet
(committee size 1, epoch 6h so rotation could not cut the run, JWK background fetch
disabled) created and stopped by the runner script; nothing external was contacted.
A prior in-flight run from the crashed orchestrating session — disposable run dir
`rights-scale-l1-load-0571ib9k`, `git_head 10e44d40` — was left to finish as a rehearsal:
it reached all 1,775 steps, failed only on the transient gRPC fetch described above, and
motivated the retry. Its outputs were discarded; this directory is the authoritative record.

## Contract/implementation discrepancy classification (AGENTS.md §8)

**A. Contract-defined and matching:** uniform fill at 1,024 slots; paid subset routing to 4
shards; `EStale`/`EInventory`/`EClosed`/`EInventory` hot-slot and post-cancel refusals;
depth-10 leaf capacity = 1,024 accepted notes; K=4 root-history eviction (`ERoot` 19);
revocation invalidates pre-cut proofs (`zk_gate:2`) while re-proofed witnesses admit;
one-write grant cut with `EGrantClosed` post-cut refusals; stranded-reservation page not
reclaimable (`EDelegated`); `reserved==0` required for `undelegate_page`; page-conservation
invariants hold on every path.

**B. Contract-undefined — recorded as characterizations, none invented into a contract:**
1. Race losers fail at submission (`submission_rejected`, non-retriable invalid) rather
   than aborting on-chain — observed identically on the RS-1 probe; both are consistent
   with "exactly one lands" and neither side resubmits.
2. `reconstruct` is a `noTx` measurement: its 45–61 s reflects a full sequential scan of
   every checkpoint/event page on a cold single validator, not an optimized read path.
3. `service_ms` p50 ~750–820 / p95 ~1,700 across ops on this builder host is a
   localnet-plus-virtualization artifact; reported, not interpreted.
4. The `ERROR ... template SpendScale` line in the driver log is snarkjs/circom stderr from
   the *expected* circuit rejection (`circuit_rejects_revoked_note`,
   `client_refused` outcome) — noise, not a chain result.

**C. Explicit contract violations:** none found.

## Explicit non-claims — what was not tested

- No testnet/mainnet, real funds, PG/bank/KYC, public endpoints, R2, replication/consensus/
  storage engine, coin/TIX module, secrets. Localnet only; RPC trusted; faucet coins are
  localnet test values.
- No SLO, throughput, latency, contention-scaling or gas-model claims; `arrival_rate 0`;
  fixed-k=2 probes are contention evidence only, not load injection.
- No durability, fault-tolerance or committee-failure claims — committee size 1 by design;
  `networkFaultToleranceTested: false` in the receipt.
- No kernel/v5, delegated-execution runtime (RS-3b crate), lifecycle/GC or indexer claims.
- Not run: `npm ci` (locked `node_modules` reused), Move test suite (no Move change this
  round — the published package is exercised end-to-end instead), `run_localnet_rights_scale.py`
  public journey (RS-1 driver does not import the edited files), `verify_runtime.py`, cargo
  (no `runtime/**` change), workflow_dispatch/CI (no network actions permitted this session;
  exact-head CI is the supervisor/CI lane's job).

## Follow-up candidates

- Optional: fold the transport-retry counter into a per-run `host.json` field (currently it
  lives only in the `reconstruct` sample detail).
- Re-measure with a larger `--shield-count`/`consume_count` sweep only if a later node
  authorizes a measurement environment beyond the builder machine (DECISION_REQUIRED per the
  node scope).
- If the submission-rejection race-loser behavior ever needs an on-chain verdict instead,
  that is a protocol question, not a driver question.
