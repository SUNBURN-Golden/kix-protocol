# testnet-key-management-decision — Sui testnet key management decision proposal

Node: `testnet-key-management-decision`. Document only. No code, no new tests,
no policy values, no new protocol command, no package, no key.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `rs-1` (merged).
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`751c51bdff661673eb2edb9de0dea8f6cbdac2e0`.
Branch: `agent/kix-testnet-key-management-decision`.
That commit is the merge of pull request #190.
This session did not commit, push, open a PR, create or close an issue, or comment.
There is no implementation commit SHA. Local results below are not exact-head CI.
There is no KTX kernel verification run ID and no KIX protocol verification
run ID for a head that contains these files.

Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged; the new files are untracked and `docs/README.md` is a worktree edit):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime AGENTS.md`
was empty. `git status --short` is the list of changed paths.

The proposal recommends C3, R2, I2, W2, and O1. It does not act on that
recommendation. Effect is only on User merge
([roadmap §1](../../docs/decisions/PROGRAM_ROADMAP_20260930.md)).
Merging the document adopts the shape only. It creates no key, deploys nothing,
and does not unlock Sui testnet deployment.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md` | Decision proposal. Axes C (custody), R (rotation), I (incident handling), W (who operates). Options for the User O1, O2, O3. |
| `docs/README.md` | One new index section: one table row and one validation bullet. |
| `validation/2026-10-16-testnet-key-management-decision/README.md` | This record. |

`git diff --stat origin/main` lists only `docs/README.md`. The two new paths are
untracked, so that command does not list them. `git status --short` shows all three.

## Commands and results

Working directory: repository root.
Python 3.13.5. Node v20.19.2. `protocol.yml` pins Python 3.12 and Node 24.
Node 24 was not installed. SDK checks were not run. Rust toolchain per `rust-toolchain.toml`.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `751c51bdff661673eb2edb9de0dea8f6cbdac2e0`. |
| `git hash-object` on the two locked files, before the edit | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git hash-object` on the two locked files, after the edit | Same two values. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime AGENTS.md` | Empty. Exit 0. |
| `git diff --check` | Exit 0. |
| `git status --short` | `M docs/README.md`, plus the two untracked paths in the table above. |
| `python3 scripts/check_status_register.py` and `--self-test` | Exit 0 both. `capability register ok: paths=219 ev_ids=15 original32=32`; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` and `--self-test` | Exit 0 both. `blueprint=47 profile=47 expected=47`; `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` and `--self-test` | Exit 0 both. `queries=13 anchors=128 catalogues=2 citations=145`; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Exit 0 both. `docs index ok: scanned=135 indexed=96 allowlisted=39`; `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. OK. The same process printed `self-test: pass`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 22 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. 47 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. 26 tests, OK. |
| same for `reference/ai_delegation` | Exit 0. 22 tests, OK. |
| same for `reference/token_reward` | Exit 0. 61 tests, OK. Author-side mock only. Not independent verification. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Exit 0 both. `commands=84 core=40 fsm=44`; `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Exit 0 both. `commands=84 productionEndpoint=false publicHost=false`; `self-test: pass`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 passed, 0 failed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 221 passed, 0 failed (sum of `test result` lines; the workspace has grown since the TL-5 record). |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| Relative-link check, `python3 -I` from `/tmp`, on the proposal and `docs/README.md` | 119 relative targets, 0 missing. |
| Whitespace scan of the proposal | 0 trailing-whitespace lines. |
| Secret-pattern scan of the proposal (`suiprivkey`, `BEGIN .*PRIVATE`, 64-hex strings, long `0x` strings, mnemonic words) | 0 hits. |
| Positive-claim word scan of the proposal (`legal`, `합법`, `인허가`, `투자수익`, `유동성`, `가격 유지`, `production-ready`), case-insensitive, skip a line that contains `않`, `아니`, `없`, `not`, or `no ` | 1 line not skipped: the topic label of prerequisite KM-11, "Legal character of custody". It names an open question, not a conclusion. |
| Digit scan of the proposal, after removing backticked references, dates, and ids | Residual digits are section and list numbers, the ADR number, dates in file names, "Groth16", and quoted lock wording ("blob 2개", "안정 1.0"). No signer count, quorum, timelock, rotation period, service level, date, or cost was added. |

No `sui` command, faucet call, RPC call, or other network call was run. No key was created.

## What was not run

SDK checks (`scripts/check_sdk_client.py`, its `--self-test`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`) were not run. Node is v20.19.2. The workflow pins Node 24. `toolchains.json` and CI were not edited.

Not run: `scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`, `scripts/verify_canonical.py`, storage probes, `scripts/run_localnet*.py`, ZK. They need the `sui` CLI or the network. No claim that `sui` or `snarkjs` were present.

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. For a diff limited to `docs/decisions/*` (other than `docs/contracts/*`, `docs/adr/*`, and `docs/PROTOCOL_MASTERPLAN_*`), `docs/README.md`, and `validation/*` other than `validation/2026-09-11/*`, both workflows classify the change as documentation-only and skip the heavy steps. A skipped heavy job is not a full-verification pass. This local run is not that classification and does not transfer to a later SHA. Final-head run IDs belong in the pull-request report after a head exists (AGENTS §11), not in a commit.

## Existing coverage (AGENTS §7)

No new tests. The proposal §10 cites the localnet runners (keys under ignored `.local/`) and the rs-1 record as the existing localnet evidence, and the capability register row "RS-5 / testnet keys" (`docs/status/CURRENT_CAPABILITY_REGISTER.md:159`) as not covered. This session does not close that row.

## Contract classification (AGENTS §8)

No explicit contract violation. The proposal does not redefine a contract, open a lock, fill a product number, or edit `docs/contracts/` or `docs/adr/`.

Contract-undefined items, left open in the proposal §9:

- The upgrade-authority holder for the rights-scale package. Not described in the repository.
- Whether the shared decision covers token keys (TL-5 K-2). Owner: User.
- Whether the testnet operator and the mainnet operator are the same person. Owner: User.
- Sui multi-signature, key-format, and upgrade facts not pinned by a repository source. `UNDETERMINED`.
- Signer count, quorum, timelock, rotation period, response and recovery times, and cost. Owners are named in the proposal. No value is filled.

## Non-claims

No production readiness, durability, distributed fencing, bank exactly-once, chain finality, or a legal conclusion. No approved SLO, signer count, quorum, timelock, or cost. No real funds, PG, bank, KYC, public endpoint, Sui testnet or mainnet, replication, consensus, storage engine, or new coin/TIX module. No key and no secret. No exact-head CI. A documentation-only green is not full verification. The author's check is not independent review. The proposed shape is not tested and not claimed sufficient.

## Deviations from the design plan

- Line references were re-read on this base and corrected where the plan's numbers differed: `.aiops/program.json:488-498` (plan: `:489-498`); the assumption A7 row is in `docs/status/I12_REVIEW_PACK.md:70` (plan: `CUT_PROOF_I12:115`, which is the proof section the row cites); common record fields at `TOKEN_AUTHORITY_AND_LIFECYCLE.md:158`.
- The plan listed a grep for the upgrade authority. It found the term only for the future token package, so the inventory says "not described in the repository" for rights-scale.
- The plan said to cite roadmap `:116` and `:64` for the gate mismatch. The proposal names those places by table instead of by line, because the line numbers were not re-verified.
- The ZK ceremony and the digit/positive-claim scans follow the TL-5 record's method. The workspace test sum is 221, not the 128 in the TL-5 record, because the workspace has more crates now.
- SDK checks were not run (Node v20.19.2, not 24).
- No root `DECISION_REQUIRED.md`. The open values stay inside the proposal. No STOP condition in the plan fired: no key or secret was handled, no spend or product was chosen, no number or name was filled, no new command was added.

## Remaining uncertainty

- Sui testnet deployment stays locked. Owners of the empty cells are in the proposal §9.
- The Astra-gate cell mismatch (dispatch `None`, roadmap `ARCHITECTURE`, no `astra_gate` key) is recorded and not resolved. This session follows `user_merge: true`.
- Hosted CI for the exact head does not exist until a head is published. A documentation-only skip on that head is not full verification.
