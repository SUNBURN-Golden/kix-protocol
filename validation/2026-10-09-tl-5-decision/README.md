# tl-5-decision — operational activation decision proposal

Node: `tl-5-decision`. Document only. No code, no new tests, no
policy values, no new protocol command, no package, no key.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `tl-4`, `tl-legal-brief`.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`18b80a79614b3a5866f61728b0935294360cfa85`.
Branch: `agent/kix-tl-5-decision`.
That commit is the merge of pull request #165.
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

The proposal recommends option O1. It does not act on that recommendation.
Effect is only on User merge
([roadmap §1](../../docs/decisions/PROGRAM_ROADMAP_20260930.md)).
Merging the document adopts the criteria list only. It does not deploy to
testnet, does not deploy to mainnet, and does not issue a token.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md` | Decision proposal. Gates G-T, G-M, G-I. Options O1, O2, O3, O4. Recommendation O1. |
| `docs/README.md` | One row in the token-layer table. One validation bullet. |
| `validation/2026-10-09-tl-5-decision/README.md` | This record. |

`git diff --stat origin/main` lists only `docs/README.md`. The two new files
are untracked, so that command does not list them. `git status --short` shows
all three.

## Commands and results

Working directory: repository root.
Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1 (797e8a9bc 2026-08-05)`.
That matches `rust-toolchain.toml` channel `1.98.1`.
Python 3.13.5. Node v20.19.2. `protocol.yml` pins Python 3.12 and Node 24.
Node 24 was not installed. SDK checks were not run.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0 at session start. Both `18b80a79614b3a5866f61728b0935294360cfa85`. The same command again after the documents were written also exited 0, with the same two SHAs. |
| `git hash-object` on the two locked files, before the edit | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git hash-object` on the two locked files, after the edit | Same two values. |
| `git diff --stat origin/main` | `docs/README.md` only (`2 insertions`). Untracked files are not listed. |
| `git status --short` | `M docs/README.md`, plus the two untracked paths in the table above. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime AGENTS.md` | Empty. Exit 0. |
| `git diff --check` | Exit 0. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK (`Ran 7 tests in 0.190s`). |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. 58 tests, OK (`Ran 58 tests in 4.604s`). The same process printed `self-test: pass`. It also printed two `ResourceWarning` lines for unclosed files. The test file was not edited. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 22 tests, OK (`Ran 22 tests in 0.012s`). |
| same for `reference/booking_resale_admission` | Exit 0. 47 tests, OK (`Ran 47 tests in 0.239s`). |
| same for `reference/credit_advance_f04` | Exit 0. 26 tests, OK (`Ran 26 tests in 0.047s`). |
| same for `reference/ai_delegation` | Exit 0. 22 tests, OK (`Ran 22 tests in 0.029s`). |
| same for `reference/token_reward` | Exit 0. 61 tests, OK (`Ran 61 tests in 0.564s`). Author-side mock only. Not independent verification. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32. Doc-tests 0. 78 passed, 0 failed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. Counts: bcs1 3, golden_vectors 4, feature-ir 5, audit_regressions 8, schema_bound 18, feature-semantics 6, kernel lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32, kix-types 6. Sum 128 passed, 0 failed. Five doc-test binaries, 0 tests each. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| Relative-link check, `python3 -I` from `/tmp`, on the three changed files | 110 relative targets, 0 missing. A whitespace scan of the same three files found 0 trailing-whitespace lines. |
| Positive-claim word scan of the proposal (`legal`, `합법`, `인허가`, `투자수익`, `유동성`, `가격 유지`, `production-ready`), case-insensitive, skip a line that contains `않`, `아니`, `없`, `not`, or `no ` | 14 hits. 13 lines skipped because they negate or quote a lock. 1 line not skipped: the references path `TOKEN_LEGAL_REVIEW_BRIEF_KO.md`. Read by hand: it is a file name, not a claim that a review concluded anything. The skipped lines were read by hand. They are negations, the node id `tl-legal-brief`, or the quoted credit-lock unlock text. None states that a gate is open or that a review has concluded. |
| Digit scan of the proposal | Residual digits are the date, the SHAs, line references, section numbers, predicate and option ids, pull-request numbers already in the sources, the audit floor A3, the representation id F4, the path `v0.3-rc1`, and quoted lock wording such as "blob 2개", "Task 005", and "안정 1.0". No supply, cap, quorum, timelock length, service level, activation date, or cost was added. |

## What was not run

SDK checks (`scripts/check_sdk_client.py`, its `--self-test`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`) were not run. Node is v20.19.2. The workflow pins Node 24. `toolchains.json` and CI were not edited.

Not run: `scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`, `scripts/verify_canonical.py`, storage probes, `scripts/run_localnet.py`, ZK. No claim that `sui` or `snarkjs` were present.

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. For a diff limited to `docs/decisions/*` (other than `docs/contracts/*`, `docs/adr/*`, and `docs/PROTOCOL_MASTERPLAN_*`), `docs/README.md`, and `validation/*` other than `validation/2026-09-11/*`, both workflows classify the change as documentation-only and skip the heavy steps. A skipped heavy job is not a full-verification pass. This local run is not that classification and does not transfer to a later SHA. CI from an earlier SHA does not transfer. Final-head run IDs belong in the pull-request report after a head exists (AGENTS §11), not in a commit.

## Existing coverage (AGENTS §7)

No new tests. The proposal §9 cites `reference/token_reward/test_tl4_*.py` as an author-side mock and the capability register TL-5 row (`docs/status/CURRENT_CAPABILITY_REGISTER.md:160`) as not covered. This session does not close that row.

## Contract classification (AGENTS §8)

No explicit contract violation. The proposal does not redefine a contract, open a lock, fill a product number, or edit `docs/contracts/` or `docs/adr/`.

Contract-undefined items, left open in the proposal §8:

- Whether the shared key-management decision covers token keys. Owner: User.
- Whether the key-management operator and the mainnet operator are the same person. Owner: User.
- What "키 생성 없음(localnet)" requires. Owner: Astra.
- Legal, tax, accounting, AML/KYC, jurisdiction, chargeback, supply, cap, quorum, timelock, service level, date, and cost. Owners are named in the proposal. No value is filled.
- Wallet and exchange compatibility. The sources name no owner.

## Non-claims

No production readiness, durability, distributed fencing, bank exactly-once, chain finality, or a legal conclusion. No approved SLO, supply, cap, quorum, timelock, or cost. No real funds, PG, bank, KYC, public endpoint, Sui testnet or mainnet, replication, consensus, storage engine, or new coin/TIX module. No key and no secret. No exact-head CI. A documentation-only green is not full verification. The author's check is not independent review.

## Deviations from the design plan

- The plan grouped TK-1, TK-2, TK-3, TK-5, and TK-9 as `NOT VERIFIABLE · no package`. The TL-4 record on this base is finer. TK-2 part T1 is a repository-boundary check. TK-5 part V6 is an author-side harness. TK-2 parts T2 through T4, TK-5 parts V1 through V5, and TK-9's actual gas path are `NOT VERIFIABLE · no package`, with TK-1 and TK-3. The proposal uses that finer record.
- The roadmap D-E sentence is at `:46` on this base. The development-plan sentence "실자금·운영 발행은 미승인" is at `:602`. ADR-0003 cites `:599` from its own base. This file cites `:602`.
- Delegation-table line `:3` is the document status line. The proposal calls it that, rather than a table header.
- SDK checks were not run. This node's plan says to run them only when Node 24 is present. This host has Node v20.19.2.
- No root `DECISION_REQUIRED.md`. The open values stay inside the proposal. No STOP condition in the plan fired: no new number was required, no new protocol command was required, and no later merge contradicted the evidence section. `testnet-key-management-decision`, an Astra re-ruling, a TL-2 package, and `rs-5-decision` are still absent.

## Remaining uncertainty

- Testnet deployment, mainnet deployment, and issuance stay locked. Owners of the empty cells are in the proposal §8.
- The Astra-gate cell mismatch (dispatch `None`, roadmap §3.5 `ARCHITECTURE`, no `astra_gate` key) is recorded and not resolved. This session follows `user_merge: true`.
- Hosted CI for the exact head does not exist until a head is published. A documentation-only skip on that head is not full verification.
