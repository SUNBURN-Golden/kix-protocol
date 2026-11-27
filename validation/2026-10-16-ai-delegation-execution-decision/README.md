# ai-delegation-execution-decision — decision proposal for enabling delegated execution

Node: `ai-delegation-execution-decision`. Document only. No code, no new tests,
no policy values, no new protocol command, no flag change.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `ai-delegation-contract-mock` (#130), `rs-3a` (#183), `rs-3b` (#184), all merged.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`47eed4b01b93dc4b00e102729bad1c74abdbae95`.
Branch: `agent/kix-ai-delegation-execution-decision`.
That commit is the merge of pull request #192.
This session did not commit, push, open a PR, create or close an issue, or comment.
There is no implementation commit SHA. Local results below are not exact-head CI.
There is no KTX kernel verification run ID and no KIX protocol verification
run ID for a head that contains these files.

Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged; the new files are untracked and `docs/README.md` is a worktree edit):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

The proposal recommends G2, L2, R2 and O1. It does not act on that
recommendation. Effect is only on User merge
([roadmap §1](../../docs/decisions/PROGRAM_ROADMAP_20260930.md)).
Merging the document adopts the shape only. It enables nothing:
`delegated_execution_enabled` stays `false` in `runtime/ARCHITECTURE.toml`.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md` | Decision proposal. Axes G (when), L (I11 limits), R (revocation). Prerequisites DX-1 to DX-16. Options for the User O1 to O4. |
| `docs/README.md` | One new table row and one validation bullet in the existing 2026-10-16 index section. |
| `validation/2026-10-16-ai-delegation-execution-decision/README.md` | This record. |

## Commands and results

Filled in below from the commands actually run.

Working directory: repository root.
Python 3.13.5. Node v20.19.2. `protocol.yml` pins Python 3.12 and Node 24.
Node 24 was not installed. SDK checks were not run. Rust toolchain per `rust-toolchain.toml`.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `47eed4b01b93dc4b00e102729bad1c74abdbae95`. |
| `git hash-object` on the two locked files, before the edit and after the edit | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, both times. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime scripts AGENTS.md` | Empty. |
| `git diff --check` | Exit 0. |
| `git status --short` | `M docs/README.md`, plus the two untracked paths in the table above. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Exit 0 both. `docs index ok: scanned=137 indexed=98 allowlisted=39`; `self-test: pass`. (Before the index edit the check failed with "not indexed" for the proposal, as designed.) |
| `python3 scripts/check_status_register.py` and `--self-test` | Exit 0 both. `capability register ok: paths=219 ev_ids=15 original32=32`; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` and `--self-test` | Exit 0 both. `blueprint=47 profile=47 expected=47`; `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` and `--self-test` | Exit 0 both. `queries=13 anchors=128 catalogues=2 citations=145`; `self-test: pass`. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | Exit 0 both. `commands=84 core=40 fsm=44`; `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | Exit 0 both. `commands=84 productionEndpoint=false publicHost=false`; `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/<suite> -t reference/<suite>` | `settlement_f01_f03` 22 tests OK; `booking_resale_admission` 47 OK; `credit_advance_f04` 26 OK; `ai_delegation` 22 OK; `token_reward` 61 OK. Author-side mocks only. Not independent verification. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 58 tests, OK. The same process printed `self-test: pass`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 78 passed, 0 failed (sum of `test result` lines). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 221 passed, 0 failed (sum of `test result` lines). |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Finished, no warnings. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Finished, no warnings. |
| Relative-link check, `python3 -I` from `/tmp`, on the proposal, `docs/README.md` and this record | 124 relative targets, 0 missing. |
| Whitespace scan of the proposal | 0 trailing-whitespace lines. |
| Secret-pattern scan of the proposal (`suiprivkey`, `BEGIN .*PRIVATE`, 64-hex strings, long `0x` strings) | 0 hits. |
| Positive-claim word scan of the proposal, skipping lines with `않`, `아니`, `없`, `not`, `no ` | 2 lines not skipped: the DX-13 row label ("Legal character of acts by an AI") and the §8 sentence naming `UNDETERMINED` legal answers. Both name an open question, not a conclusion. |
| Digit scan of the proposal, after removing backticked references and dates | Residual digits are section numbers, option and prerequisite ids, assumption ids, PR numbers, "1.0" in quoted lock wording, and "v5". No limit, window, period, quorum, service level, date, or cost was added. |

No `sui` command, faucet call, RPC call, or other network call was run. No key was created.

## What was not run

SDK checks (`scripts/check_sdk_client.py`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`) were not run. Node is v20.19.2. The workflow pins Node 24. `toolchains.json` and CI were not edited.

Not run: `scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`, `scripts/verify_canonical.py`, storage probes, `scripts/run_localnet*.py`, ZK. They need the `sui` CLI, snarkjs or the network. No claim that they were present.

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. For a diff limited to `docs/decisions/*` (other than `docs/contracts/*`, `docs/adr/*`, and `docs/PROTOCOL_MASTERPLAN_*`), `docs/README.md`, and `validation/*` other than `validation/2026-09-11/*`, both workflows classify the change as documentation-only and skip the heavy steps. A skipped heavy job is not a full-verification pass. This local run is not that classification and does not transfer to a later SHA. Final-head run IDs belong in the pull-request report after a head exists (AGENTS §11), not in a commit.

## Existing coverage (AGENTS §7)

No new tests. The proposal §9 cites the mock tests (`reference/ai_delegation/test_ai_delegation_mock.py`),
the architecture verifier and its test, and the RS-3a and RS-3b records as the existing evidence.
Limits on the chain, the mock-to-chain binding, authenticated principals and non-cooperating
revocation are not covered; they are listed as prerequisites, not closed.

## Contract classification (AGENTS §8)

No explicit contract violation. The proposal does not redefine a contract, open a lock, fill a
product value, or edit `docs/contracts/` or `docs/adr/`.

Contract-undefined items, left open in the proposal §8:

- Limits, period and allowed operations on the chain grant.
- The link between mock revocation and the chain cut.
- `cancel_show` against grants, and the private-path delegation gate.
- The I12 branch, the `H_g` policy, the time source, the non-cooperating executor design.
- Every I11 value (identity, limits, window, anti-splitting basis, post-check owner and deadline).

## Non-claims

No production readiness, durability, distributed fencing, bank exactly-once, chain finality, or a
legal conclusion. No approved limit, period, quorum, SLO or cost. No real funds, PG, bank, KYC,
public endpoint, Sui testnet or mainnet, replication, consensus, storage engine, or new coin/TIX
module. No key and no secret. No exact-head CI. A documentation-only green is not full
verification. The author's check is not independent review. The proposed shape is not tested and
not claimed sufficient. Nothing was enabled or connected.

## Deviations from the design plan

- Line references were re-read on this base. Corrected or added: the Move cut is at `rights_scale.move:909-921` (doc comment plus function); the plan's "signed bytes not recalled" text is `DEVELOPMENT_PLAN.md:296-301`; the §12 passage is `:530-536`; the node's "lines ~296-297" in the spec points into that same item 2.
- The plan listed the human designation under "U11-ID: Astra and User". The I11 row already records a designated issuer and alternate, so the proposal leaves only the service identity and further accountable humans open, and copies no names.
- The plan said to quote the roadmap §1 effect rule by line. The line was not re-verified, so the proposal cites §1 by section.
- The plan's reference to `CUT_PROOF_I12_20261008.md:138` was confirmed. That recommendation is quoted with its own undecided state.
- SDK checks were not run (Node v20.19.2, not 24).
- No root `DECISION_REQUIRED.md`. The open values stay inside the proposal. No STOP condition in the plan fired: no key or secret was handled, no spend was chosen, no value or name was filled, no new command was added, no flag or contract was edited.

## Remaining uncertainty

- Delegated execution stays off. Owners of the empty cells are in the proposal §8.
- The Astra-gate cell mismatch (dispatch `None`, roadmap `ARCHITECTURE`, no `astra_gate` key) is recorded and not resolved. This session follows `user_merge: true`.
- Hosted CI for the exact head does not exist until a head is published. A documentation-only skip on that head is not full verification.
