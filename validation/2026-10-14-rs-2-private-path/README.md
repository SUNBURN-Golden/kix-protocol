# rs-2 — private path on the extended profile: root rules, depth-10 circuits, Verifier, manifest v2 (localnet)

Evidence for KIX program node `rs-2`: the root rules RR-1..RR-6, the new depth-10 circuits, the
new frozen `Verifier`, manifest schema v2, witness reconstruction from chain data, the fixture
ceremony, the private-path model/vectors, an actual-localnet private journey, and the
additive workflow steps. The 16-slot reference profile (`reference/v0.3-rc1/**`, its 19 Move
tests and its ZK regression) is byte-identical and passes. The two locked kernel blobs are
unchanged. This session did not commit, push, open a pull request, or edit `.aiops/`,
`docs/tasks/`, `docs/contracts/` or any existing circom file. The supervisor owns git.

**Everything here is a localnet fixture.** The ceremony is single-party and is not an
operational ceremony; K, the shard counts and the tree depth are test-only fixture values.
Nothing below is an anonymity, performance, durability, audit or production claim.

## Identity

| Item | Value |
|---|---|
| Task | `rs-2` — RS-2 private path (root rules, new circuit, verifier, manifest v2). No task issue; no `docs/tasks/` file for this node |
| Observed `origin/main` | `dd92e1146ec8eb7024da6c0f62aa721bdc1be780` — the **local** `origin/main` ref. `git fetch origin main` was **not run**: the supervisor rule for this session forbids network actions |
| Branch / task base | `agent/kix-rs-2` at `dd92e1146ec8eb7024da6c0f62aa721bdc1be780` (equal to the observed main; no delta to report) |
| Implementation commit | none. The worktree is dirty on the task base |
| Depends on | `rs-1` (merged: `dd92e11` is its probe merge) |
| Authorization | RS-1 owner record (`docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md`) covers the package; the node definition and `docs/contracts/RIGHTS_SCALE_PROFILE.md` §9 cover RR-1..RR-6. Profile 0.1 stays draft until Astra's ARCHITECTURE gate |

## What landed

- **Root rules** (profile §9) in `reference/rights_scale/sui/sources/rights_scale.move`:
  - RR-1/RR-5: one append-only incremental `NoteTree` per show (frontier + K-root ring); `shield` is its only writer.
  - RR-2/RR-3/RR-6: one `RevocationState` per show storing only the sparse revocation root; the leaf of a slot is the highest revoked generation (default 0); only `revoke_with_root` writes it; the proof's public input is that one aggregated root, and the chain supplies its current value (window W = 0).
  - RR-4: no path is stored or accepted from anyone; the witness is rebuilt from public `NoteAdded` / `RevocationLeaf` events (`client/chain-witness.mjs`) and checked against the roots stored on chain.
  - `NullifierShard` and `ChallengeShard` families routed by the hash of the value alone (RS-C09, RS-C11, RS-C17).
  - `claim_zk` (creation stage, like page/shard claims) fixes the show's domain `Poseidon(show id mod FR, profile_version, manifest hash mod FR)` (RS-C11) and creates all private objects with derived addresses.
- **New Verifier** `reference/rights_scale/sui/sources/zk_gate.move`: frozen object, no caller-supplied key, `public(package)` verification entry points, malformed keys refused at creation, pinned by the show at `create_show_control`.
- **New circuits** `reference/rights_scale/zk/circuits/{common,mint_scale,spend_scale}.circom`, depth 10, same public layouts as the reference circuits (mint 4, spend 6). The spend circuit proves `generation > revokedMaxGeneration` against the slot-indexed sparse tree (RR-2). Existing circom files untouched.
- **Manifest v2** (`kix-zk-artifacts-v2`) from `client/setup-zk.mjs`: depth, slotBits, profileVersion, rootHistoryK, phase-1 record (source, SHA-256, power), phase-2 contribution counts, measured constraint counts, public-input layouts, circuit and artifact hashes. `zk-policy-v2.mjs` refuses v1 manifests, other depths/profiles, missing records, a power that is too small, and uncontributed keys.
- **Client**: `private-scale.mjs` (trees, note/admission proofs, verifier pin, revocation witness), `chain-witness.mjs` + `chain-kit.mjs` (localnet plumbing, two independent event sources), `private-localnet.mjs` (the journey), `zk-regression.mjs` (`test:zk`), `gen-move-vectors.mjs`, `measure-constraints.mjs`. Own `package.json`/`package-lock.json` (same pins as the reference client).
- **Model/vectors**: `model.py` (private path, abstract roots), `replay_private.py`, `compare_private.py`, `vectors/private_path.json`, `test_private_model.py`.
- **Runner and CI**: `scripts/run_localnet_rights_scale_private.py`; five additive steps in the existing `rights-scale` job of `.github/workflows/protocol.yml` (no existing step, no `timeout-minutes` touched); `scripts/verify_runtime.py` gains one additive `rs2-circuit-build` check; `.gitignore` ignores the generated artifacts.

## Changed paths (complete)

Modified: `.github/workflows/protocol.yml`, `.gitignore`, `docs/status/CURRENT_CAPABILITY_REGISTER.md` (RS-2 row only),
`reference/rights_scale/client/{package.json,package-lock.json,types.mjs}`, `reference/rights_scale/model.py`,
`reference/rights_scale/sui/sources/rights_scale.move`, `reference/rights_scale/test_model.py`, `scripts/verify_runtime.py`.

Added: `reference/rights_scale/client/{chain-kit,chain-witness,compile-circuits,gen-move-vectors,measure-constraints,private-localnet,private-scale,profile-constants,setup-zk,zk-helpers,zk-policy-v2,zk-regression,zk-test-utils}.mjs`,
`reference/rights_scale/{compare_private,replay_private,test_private_model}.py`,
`reference/rights_scale/sui/sources/zk_gate.move`,
`reference/rights_scale/sui/tests/{private_path_tests,root_math_tests,zk_staging_tests,zk_support}.move`,
`reference/rights_scale/vectors/private_path.json`,
`reference/rights_scale/zk/circuits/{common,mint_scale,spend_scale}.circom`, `reference/rights_scale/zk/artifacts/README.md`,
`scripts/run_localnet_rights_scale_private.py`, and this directory.

Not touched: `reference/v0.3-rc1/**`, `runtime/**`, `.aiops/`, `docs/tasks/`, `docs/contracts/`, `docs/decisions/`, `docs/blueprints/`, the other workflow, `scripts/bootstrap.sh` (it already runs `npm ci` for this client).

## Locked blobs

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

(`git hash-object`, at session start and again after all work. The merge-commit check of AGENTS.md §13 belongs to the supervisor.)

## Existing coverage first (AGENTS.md §7)

| Requirement | Existing coverage | Class |
|---|---|---|
| RR-1 K-root history | none for the extended profile. Reference profile accepts the current root only (`localnet-boundaries.mjs` `staleRoot`) | not covered |
| RR-2 revocation leaf = revoked max generation; issuance/refund leave the root | none. Reference revocation leaf is `H(slot, generation, domain, 3)` of the *current* generation and moves on every issuance | not covered |
| RR-3 W = 0 | partially: reference `oldRevoked` rejects a pre-revoke proof, depth 4, different root rule | partially covered (different profile, not counted) |
| RR-4 witness rebuilt from public data | none; reference reads the whole `Show` vector | not covered |
| RR-5/RR-6 one tree, one aggregated root | none (RS-1 has no trees) | not covered |
| New circuit, manifest v2, ptau power, constraint counts | reference depth-4 only (`validation/2026-09-11/circuit-build.log`) | not covered for depth 10 |
| Verifier pin (IM-27), wrong verifier/context rejection | reference: wrong verifier object, changed context (`localnet.mjs`) at depth 4 | partially covered (different package) |
| Compensated-forgery rejection | reference `zk-regression.mjs` (archived keys + fresh depth-4 keys) | partially covered; the new circuit's keys needed their own run |
| RS-C09, C10, C11, C12, C13, C17 | none (RS-1 left them to RS-2) | not covered |
| RS-C14 private share | none | not covered |

The 16-slot suite stays as the regression for the reference profile and is **not** counted as evidence for any row above.

## New tests and evidence, and the gap each addresses

| Artifact | Count | Gap addressed |
|---|---|---|
| `sui/tests/root_math_tests.move` | 15 | RR-1/RR-2 arithmetic: on-chain `poseidon_bn254` tree math equals circomlibjs (empty-tree zeros, depth-3 and depth-10 incremental roots, sparse-update roots, domain known answers); ring keeps exactly the last K; leaf capacity; malformed witnesses. Constants regenerated by `gen-move-vectors.mjs --check` |
| `sui/tests/zk_staging_tests.move` | 14 | `claim_zk`: domain, ten claim numbers, derived identities distinct from pages/payment shards, once only, creation stage only, pinned verifier, 1,024-slot cap, opt-in (RS-1 path unchanged without it), plain `revoke` refused on a rooted show, routing is a function of the value |
| `sui/tests/private_path_tests.move` | 49 | RS-C10 (shield keeps occupancy, SHIELDED refuses offer/authorize/refund/reissue/reservation), RS-C09/C17 (replay, challenge reuse), RS-C11 (wrong shard/tree/revocation object/verifier, other show), RR-1 boundary (age K-1 accepted, age K refused), RR-2/RR-3 (issuance and refund leave the root; revoke moves it; chain feeds the current root; stale/tampered/non-monotone witnesses refused), expiry bounds, fail-closed real `shield`/`consume_private` |
| `test_private_model.py` | 42 | model/Move parity (constants, codes, check order, surface), all predicate rules above on the model, vector replay, mutation check, **RR-2 equivalence lemma on 60 random operation sequences**, RS-C13 candidate sets, routing holds no slot |
| `zk-regression.mjs` (`test:zk`) | 54 checks | manifest v2 policy; the uncontributed-key forgery reproduced on `mint_scale` then refused by policy; every single-input and compensated forgery rejected with the contributed keys (mint and spend); the spend circuit refuses revoked, wrong-path, wrong-root, wrong-action, wrong-nullifier, wrong-context, other-domain, out-of-range witnesses |
| `private-localnet.mjs` + `compare_private.py` | 3 scenarios, 120 steps | the same scripts run against the published package with **real Groth16 proofs verified by the chain**, compared with the model step by step and by state |

Move totals: `kix_rights_scale` 217 tests (139 RS-1 + 78 new), reference `kix` 19.

## RR and predicate acceptance map

| Item | Where it is enforced | Where it is checked |
|---|---|---|
| RR-1 | `NoteTree.roots` ring, `ERoot` | `root_math_tests::history_keeps_exactly_the_last_k_roots`; Move age K-1/K tests; localnet `p_edge` (age 3 accepted) / `p_old` (age 4 refused with 19) |
| RR-2 (+equivalence) | `revoke_with_root`, spend circuit `LessThan(64)` | Move RR-2 tests; localnet `p5` valid after issue/refund traffic, revoke moves root; model equivalence test; `test:zk` witness refusals |
| RR-3 | `private_inputs` feeds `rev.root` | localnet `p6`/`p8` pre-revoke proofs refused by Groth16 (`zk_gate:2`), re-proof accepted |
| RR-4 | `chain-witness.mjs` | localnet `p_w`: witness of slot 1023 rebuilt from events only by two independent sources that agree with each other, the driver cache and the stored roots; accepted on chain |
| RR-5/RR-6 | one `TreeKey{0}` and one `TreeKey{1}` object | `structure` in the receipt: 1 note tree, 1 revocation root per show; circuit has one `revocationRoot` input |
| New circuit/Verifier/manifest v2 | `circuits/`, `zk_gate.move`, `setup-zk.mjs` | `npm run setup:zk`, `test:zk`, Verifier key pin (the alternate verifier is refused with `VERIFIER_KEY_PIN_MISMATCH`) |
| RS-C09 | `SHIELDED` + nullifier set | Move + localnet replay (`8`), shield-then-public refusals |
| RS-C10 | `shield_apply` / `live` | Move + localnet scenario `shield_conserves_the_right_count` (4 slots, 4 notes, re-shield `1`, reissue `9`, conservation) |
| RS-C11 | domain + shard routing + pinned Verifier | localnet: wrong shard `16`, wrong verifier `4`, proof of another show and of another manifest hash refused by Groth16, `shield` with a foreign domain refused; three distinct domains recorded |
| RS-C12 | RR-1..RR-4 | above |
| RS-C13 | no slot in routing; global tree | privacy section below |
| RS-C14 (private share) | reported separately | the receipt lists private results only; unimplemented items below |
| RS-C17 | `ChallengeShard` | Move + localnet (`p_c4` reuses challenge 424242 with another nullifier: `8`) |

## Measurements (exploratory, raw; not targets, not adoption evidence)

Constraint counts by tree depth (`constraints-by-depth.json`, produced by `measure-constraints.mjs`, circom2 0.2.22), ptau power = ceil(log2(constraints + public inputs + 1)):

| Depth | Leaves | mint_scale | spend_scale | Power needed |
|---|---|---|---|---|
| 4 | 16 | 906 | 7,193 | 13 |
| 6 | 64 | 908 | 9,275 | 14 |
| 8 | 256 | 910 | 11,357 | 14 |
| **10** | **1,024** | **912** | **13,439** | **14** |
| 12 | 4,096 | 914 | 15,521 | 14 |
| 14 | 16,384 | 916 | 17,603 | **15** |

**Decision for RS-2: depth 10, power 14.** The cached phase-1 file (power 14, produced by the protocol job) is reusable. A 16,384-slot show (depth 14) would need power 15 and a different phase-1 file; that is an input for RS-4/RS-5, not a decision here. Spend grows about 1,041 constraints per level.

Raw timings from the journey (`private-journey-receipt.json` `timings`, Node 20.19, one shared 8-core host, not a benchmark): mint proof 144–425 ms, spend proof 584–722 ms in the first run. Gas per operation as reported in effects (`gas` in the receipt): `consume_private` computation 1,000,000 units, storage cost 8.18M with rebate 4.94M (MIST); `shield` storage ≈ 11.0–11.5M; `revoke_with_root` ≈ 13.2M; `claim_zk` in the receipt. These are localnet effects values, not a gas model.

## Commands actually run and results

| Command | Result |
|---|---|
| `sui move … test --path reference/rights_scale/sui` | 217/217 pass (`move-tests-rights-scale.log`) |
| `sui move … test --path reference/v0.3-rc1/sui` | 19/19 pass (`move-tests-reference-16-slot.log`) — the 16-slot regression |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 79/79 pass (37 RS-1 + 42 new; `model-tests.log`) |
| `node reference/rights_scale/client/gen-move-vectors.mjs --check` | 23 vectors match circomlibjs |
| `npm --prefix reference/rights_scale/client run setup:zk` (fresh phase 1) | OK, 3 m 33 s; phase-1 source `FRESH_SINGLE_PARTY_LOCAL_FIXTURE`, power 14 |
| same, `KIX_ZK_PHASE1_PTAU` = earlier file | OK, 26–31 s; source `REUSED_CACHED_LOCAL_FIXTURE` |
| `npm --prefix reference/rights_scale/client run test:zk` | PASSED, 54 checks, ~7 s (`zk-regression-scale.json`) |
| `.venv/bin/python scripts/run_localnet_rights_scale_private.py` | `PASSED_ACTUAL_LOCALNET`, 3 scenarios / 120 steps, failures `[]`; 2 m 22 s – 2 m 40 s on an idle host (8 m 25 s once under host load, before the scan fix below). Receipt: `private-journey-receipt.json` |
| `.venv/bin/python scripts/run_localnet_rights_scale.py` (RS-1 public path, unchanged) | `PASSED_ACTUAL_LOCALNET`, failures `[]`, 10 m 53 s |
| `npm --prefix reference/v0.3-rc1/client run setup:zk` + `test:zk` | `PASSED`, scope `ARCHIVED_AND_FRESH_KEYS` — reference ZK regression unchanged |
| `.venv/bin/python scripts/run_localnet.py --private` (reference private journey) | `PASSED_ACTUAL_LOCALNET`, 40 s |
| `.venv/bin/python scripts/verify_runtime.py` | all 8 checks pass: python-tests, node-offline, sdk-import, move-tests, rs1-model-tests, rs1-move-tests, circuit-build, rs2-circuit-build |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 183 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | clean |
| `python3 scripts/check_status_register.py` (+ `--self-test`), `check_rs_profile_traceability.py` (+ `--self-test`), `check_docs_index.py` (+ `--self-test`), `check_read_model_source_map.py` (+ `--self-test`) | pass (see the supervisor evidence; run in this session after this file was added) |
| comparator negative controls (tampered outcome / revoked generation / revocation counter / nullifier count) | each rejected with `MODEL_DIVERGENCE`; an untouched report accepted |

Environment actually used: **Node v20.19.2** (the project pins Node 24; CI uses 24) and Python 3.12.15 (project venv); `sui` 1.79.1-808640d9b49a reused from a sibling worktree; `node_modules` copied from the sibling worktrees (the RS-1 tree plus the missing ZK packages, matching the new lockfile version for version). `npm ci` itself could not run offline (the local npm cache has no `circom2`), so the lockfile was assembled by merging the RS-1 lock with the reference lock's entries and checked with `npm ls --package-lock-only` (clean) and a version comparison against the installed tree (0 mismatches). CI's `npm ci --ignore-scripts` is the first run of the real command.

## CI budget (the 30-minute job)

Added to the existing `rights-scale` job, after the RS-1 steps: cache-key step, phase-1 cache **restore** (same key series as the protocol job, so main's file is found; the weekly schedule regenerates), `setup:zk`, `test:zk`, the private journey. No save step, no timeout/job edit.

| Segment (local, shared 8-core host, Node 20) | Time |
|---|---|
| Move tests (217) + model tests (79) | ≈ 10 s + 4 s |
| RS-1 public journey (existing step) | 10 m 53 s |
| `setup:zk`, cache hit / miss | 0.5 min / 3.6 min |
| `test:zk` | 0.1 min |
| private journey | 2.4 min idle (8.4 min once under load) |

Added work ≈ 3 min with a cache hit, ≈ 6.5 min with a miss, on this host. **The CI duration of the job was not measured** (no network); bootstrap and the CI runner's speed are unknown. The circuit build itself is far inside the budget, so no `DECISION_REQUIRED` was written. If the first CI run of this head is over 30 minutes, the owner must decide between a longer `timeout-minutes` and a separate job; this node did not edit either.

## Contract/implementation discrepancy classification (AGENTS.md §8)

**A. Contract-defined and matching:** RR-1..RR-6 as written; RS-C09..C12, C17; IM-09..IM-19, IM-22, IM-27; `Verifier` fixed once and no caller key (IM-13); context bound to the gate address (IM-12); cancel refuses private consumption (IM-12/IM-28); manifest v2 fields (IM-17); fixture ceremony power recount (IM-16).

**B. Contract undefined — recorded as characterizations, none invented into a contract:**
1. Whether the private objects are required at `seal`. Implemented **opt-in** (`claim_zk` before `seal`); a show without it has no private operation and keeps the RS-1 public path byte-for-byte.
2. Where `domain` lives. In `ShowControl.domain` (profile §3 lists it there); `0` means the private path is off.
3. Revocation leaf encoding: the raw highest revoked generation as a field element, default 0. The revoked generation is the revoked ticket's own generation.
4. Domain derivation: Poseidon over (show id mod FR, profile_version, manifest hash mod FR), both 32-byte inputs read big-endian.
5. Root-history shape: the K most recent roots including the current and the initial empty root; accepted iff age < K.
6. A show enabling the private path must have capacity ≤ 1,024 (the circuit's 10-bit slot range); larger shows get `ERange` at `claim_zk`.
7. `revoke_with_root` is a second entry point and plain `revoke` aborts `ERootRequired` on a rooted show, because a revoke that left the root alone would leave the note valid. Profile §3 names one `revoke` operation; the split is an implementation choice.
8. Concurrent revocations built on one root conflict as RR-2 says; only the sequential stale-witness case is tested (Move + localnet). A truly concurrent submission would also meet the temporary `&IssuerCap` serialization of the open probe and was not run.
9. `ChallengeShard` family count and `NullifierShard` count are fixture constants (4 each), like the RS-1 payment shards.

**C. Explicit contract violations:** none found.

## Privacy note (RS-C13) — documentation, not an anonymity claim

- **What is public at `shield`:** the holder, the ticket, the slot and the commitment appear together in one transaction (`NoteAdded` + `Change`). The state becomes `SHIELDED`. Privacy begins after that step; it hides only *which* shielded note a later admission spends.
- **Anonymity set** of one admission = notes inserted up to the root the proof used, minus spent nullifiers, minus revoked slots (both public). Measured on the main scenario by `replay_private.observer_candidates` (also asserted in `test_private_model.py`):

| Admission (script step) | Root age | Notes in tree | Candidates |
|---|---|---|---|
| 34 `p_edge` | 3 | 5 | **2** |
| 36 `p_cur` | 0 | 5 | 4 |
| 41 `p_c3` | 0 | 5 | 3 |
| 55 `p_w` | 0 | 5 | 2 |
| 65 `p5` | 0 | 8 | 4 |
| 73 `p6b` | 0 | 8 | 2 |

  Sets this small give no meaningful anonymity. Claiming any would be wrong; the profile's own rule (§1 non-claim) is kept.
- **Root choice is public.** The proof's note root and its age are visible; a larger K lets an observer place a proof in time and exclude newer notes. K is a fixture constant (4); the operational K stays UNDETERMINED (DECISION_REQUIRED · Astra).
- **Revocation root is public and global** (RR-6): one revoke invalidates every in-flight proof. The ratio and re-proof delay are RS-4 measurements, not made here.
- **Routing:** shards are chosen by the hash of the nullifier or challenge only; the Move routing function takes no slot, page or section (tested in `test_private_model.py::Privacy`).
- **Gate sees:** its own address, the challenge, the expiry and the nullifier; never the note, slot or secret (the packet carries none).
- **One global tree** (RR-5) keeps the anonymity set as large as the show allows; its contention is unmeasured.

## RR-4 scope recorded (what rebuilds without an indexer)

The note tree stores a frontier, not leaves; leaves and revoked generations are in `NoteAdded` / `RevocationLeaf` events. Both are rebuilt with **no indexer service**: (1) the node's `suix_queryEvents`, (2) a scan of every checkpoint over gRPC. The two agree with each other, with the driver's cache, and with the roots stored on chain (the driver fails otherwise). Limits: it needs the node to retain the checkpoints/events (pruning policy and the public-tree retention period stay UNDETERMINED, DECISION_REQUIRED · Astra if a policy value), and a full checkpoint scan is linear in chain height. Events from before a node's lowest available checkpoint cannot be recovered from that node.

## Deviations from the design plan

1. `seal` does **not** require `claim_zk` (plan: required). Opt-in keeps RS-1's tests, vectors, runner and CI step unchanged.
2. `ShowControl` gained `domain: u256` instead of a `zk_claimed` flag; no other ShowControl change.
3. `consume_private` takes `note_root` (the plan's signature omitted the root being looked up in the history).
4. `revoke_with_root` added beside `revoke` (plan: change `revoke`'s signature, which would break RS-1 callers).
5. Shard routing reuses RS-1's `route` over `bcs(value)`; no tag/salt.
6. CI uses the protocol job's own phase-1 key series (restore only) instead of a separate `kix-zk-phase1-rs-*` series.
7. Two RS-1 scope assertions in `test_model.py` ("no proof path" in the source; the exact public-function list) were updated to include the RS-2 surface; they described RS-1's scope, not a contract. The coin/TIX exclusion assertions remain.
8. `scripts/verify_runtime.py` gained one `rs2-circuit-build` check (not in the plan).
9. Move test hooks `*_unproven_for_testing` (`#[test_only]`) share the production check functions but skip the Groth16 call, because a unit test cannot hold a valid proof for object IDs unknown at compile time; real `shield`/`consume_private` are tested to fail closed, and acceptance/rejection of real proofs is tested on the localnet.
10. The lockfile was merged offline rather than produced by `npm install`; the checkpoint scan was made incremental after a slow run under host load.

## Explicit non-claims — what was not tested

- No testnet, mainnet, real funds, PG/bank/KYC, public endpoint, R2, replication/consensus/storage engine, coin/TIX module, delegation (RS-3a/b), private resale, refund, reissue, unshield or key rotation.
- The ceremony is single-party; no multi-party ceremony, no circuit or Move audit (RS-5).
- No throughput, latency, p99, contention, `shield` hot-object or revocation-invalidation ratio (RS-4). Timings above are raw samples on a shared host.
- No anonymity, no distributed fencing, no chain finality, no durability from these in-memory/localnet runs. RPC is trusted on the localnet.
- Not run: `npm ci`, `bootstrap.sh`, the paid localnet journey (host Python/SQLite precondition), the CI job duration, a concurrent-revocation race, mutation runs of the Move package.
- `suiSerializationVerified` stays `false` in the generated manifest as in the reference profile; acceptance of these proofs by the chain is shown by the journey, not by that flag.

## Re-verification pass (second session, same worktree state)

The worktree was re-verified end to end after the section above was written; nothing was edited
except this addendum. Node **v24.19.0** (`/home/box/.local/opt/node-v24.19.0-linux-x64/bin`) was on
`PATH` for the Node steps this time, matching the pinned toolchain; the earlier pass had only Node 20.

| Command | Result |
|---|---|
| `sui move … test --path reference/rights_scale/sui` | 217/217 pass |
| `sui move … test --path reference/v0.3-rc1/sui` | 19/19 pass |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 79/79 pass |
| `node …/rights_scale/client/gen-move-vectors.mjs --check` | 23 vectors match circomlibjs |
| `npm --prefix reference/rights_scale/client run setup:zk` with `KIX_ZK_PHASE1_PTAU` = prior `pot-final.ptau` | OK, ~35 s; `phase1: REUSED_CACHED_LOCAL_FIXTURE`, constraints 912/13,439, power 14 (regenerated the gitignored artifacts) |
| `npm --prefix reference/rights_scale/client run test:zk` | PASSED, 54 checks (run before and after the regeneration) |
| `npm --prefix reference/v0.3-rc1/client run test:zk` | PASSED, `ARCHIVED_AND_FRESH_KEYS` |
| `.venv/bin/python scripts/run_localnet_rights_scale_private.py` | `PASSED_ACTUAL_LOCALNET`, 3 scenarios, failures `[]`, ~2.3 min |
| `.venv/bin/python scripts/run_localnet_rights_scale.py` | `PASSED_ACTUAL_LOCALNET`, 14 scenarios, failures `[]` |
| `.venv/bin/python scripts/run_localnet.py` | `PASSED_ACTUAL_LOCALNET` |
| `.venv/bin/python scripts/run_localnet.py --private` | `PASSED_ACTUAL_LOCALNET` |
| `.venv/bin/python scripts/run_localnet.py --paid` | **not run to completion — environment precondition**: the script asserts Python 3.12 + SQLite 3.45.1 (Ubuntu 24.04 system Python, the CI runner image); this host has `/usr/bin/python3` 3.13.5/3.46.1 and uv 3.12.15/3.53.1. The paid path is untouched; the synthetic `verify_paid_recovery`/`verify_paid_archive` checks below did run and passed |
| `.venv/bin/python scripts/verify_runtime.py` | all 8 checks pass, including `rs2-circuit-build` |
| `.venv/bin/python scripts/verify_commerce.py`, `verify_canonical.py`, `verify_runtime_architecture.py` | PASS / PASS / OK |
| `python3 scripts/test_runtime_architecture.py` | 7/7 pass |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 58 tests OK |
| `python3 -m unittest discover` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | 22/47/26/22/61 pass |
| `check_status_register`, `check_rs_profile_traceability`, `check_read_model_source_map`, `check_docs_index`, `check_openapi_contract`, `check_integration_gate_openapi` (+ `--self-test` each) | all pass |
| `check_sdk_client` (+ `--self-test`), `npm --prefix sdk run conformance`, `verify-compat` | pass under Node 24 |
| `probe_paid_storage.py` (3 cycles), `reproduce_storage_rollback.py`, `verify_paid_recovery.py`, `verify_paid_archive.py` | PASSED (synthetic chain / mock money) |
| `cargo fmt --all -- --check` / `cargo test --workspace --locked --offline` / `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | clean / all pass / clean |
| `git hash-object` on both locked files | `69564b1…` and `b607996…` — match, before and after |

`bash scripts/bootstrap.sh` was not run: it needs network (pip install, `npm ci`, `install_sui.py`)
and asserts the system `python3` is 3.12 (this host's is 3.13.5); the environment was already
provisioned. `npm ci` still could not run offline. The locked blobs matched again at the end of this
pass.

## Remaining uncertainty and follow-up candidates

- First CI run of this head decides the job-duration question (see CI budget).
- Equivalence lemma (RR-2) is argued from the profile's operations and checked on random model sequences; a mechanized proof was not made. It must be re-proved if any operation can raise a slot generation after a note exists (e.g. a future private reissue).
- IssuerCap decision (probe) is still open; `claim_zk` and `revoke_with_root` take the temporary `&IssuerCap` like the other issuer-signed operations.
- A depth-14 profile (16,384 slots) needs ptau power 15, which the shared cache does not hold.
- K, W, shard counts, public-tree retention and the choice between event-based and stored leaves are Astra decisions; none was made here.
