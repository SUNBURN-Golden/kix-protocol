# k-a-integration-decision — integration (a) decision proposal

Node: `k-a-integration-decision`. Document only. No code, no new tests, no
journal or wire crate, no policy values, no new protocol command.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `k-a-reestimate`.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`57a3e3049c84a2ac0112371594e9bb4b85a8296f`.
Branch: `agent/kix-k-a-integration-decision`.
That commit is the merge of PR #141, which brought the re-estimate onto this tree.
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

The proposal recommends option B (`DEFERRED`). It does not act on that
recommendation. Effect is only on User merge
([roadmap §1](../../docs/decisions/PROGRAM_ROADMAP_20260930.md)).
Merging the document is not `ADOPT` of integration (a).

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md` | Decision proposal. Options A1, A2, A3, B, C. Recommendation B. |
| `docs/README.md` | One index row in the 2026-10-08 table. One validation bullet. |
| `validation/2026-10-09-k-a-integration-decision/README.md` | This record. |

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
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0 at session start. Both `57a3e3049c84a2ac0112371594e9bb4b85a8296f`. The same command again after the documents were written also exited 0, with the same two SHAs. |
| `git hash-object` on the two locked files, before the edit | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git hash-object` on the two locked files, after the edit | Same two values. |
| `git diff --stat origin/main` | `docs/README.md` only. Untracked files are not listed. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime AGENTS.md` | Empty. Exit 0. |
| `git diff --check` | Exit 0. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK (`Ran 7 tests in 0.171s`). |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. 53 tests, OK (`Ran 53 tests in 3.400s`). The same process printed `self-test: pass`. It also printed a `ResourceWarning` for an unclosed file. The test file was not edited. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 20 tests, OK (`Ran 20 tests in 0.017s`). |
| same for `reference/booking_resale_admission` | Exit 0. 43 tests, OK (`Ran 43 tests in 0.224s`). |
| same for `reference/credit_advance_f04` | Exit 0. 20 tests, OK (`Ran 20 tests in 0.030s`). |
| same for `reference/ai_delegation` | Exit 0. 22 tests, OK (`Ran 22 tests in 0.034s`). |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `openapi contract pin ok: commands=40 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `integration-gate openapi ok: commands=40 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32. Doc-tests 0. 78 passed, 0 failed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked -- --quiet` | Exit 0. Second run, used to read per-crate lines after the first log was truncated in the session display. Counts: bcs1 3, golden_vectors 4, feature-ir 5, audit_regressions 8, schema_bound 18, feature-semantics 6, kernel lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32, kix-types 6. Sum 128 passed, 0 failed. Five doc-test binaries, 0 tests each. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| Relative-link check, `python3 -I` from `/tmp`, on the three changed files | 104 relative targets, 0 missing. A whitespace scan of the same three files found 0 trailing-whitespace lines. |

## What was not run

SDK checks (`scripts/check_sdk_client.py`, its `--self-test`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`) were not run. Node is v20.19.2. The workflow pins Node 24. `toolchains.json` and CI were not edited.

Not run: `scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`, `scripts/verify_canonical.py`, storage probes, `scripts/run_localnet.py`, ZK. No claim that `sui` or `snarkjs` were present.

The PR #11 cold-build was not re-executed. The proposal cites [PR11_PRESERVATION.md](../../docs/status/PR11_PRESERVATION.md): wire 4 pass / 5 fail, journal library/recovery 1+13 pass, helper ignore 2, on the locked v4 kernel bytes.

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. For a diff limited to `docs/decisions/*` (other than `docs/contracts/*`, `docs/adr/*`, and `docs/PROTOCOL_MASTERPLAN_*`), `docs/README.md`, and `validation/*` other than `validation/2026-09-11/*`, both workflows classify the change as documentation-only and skip the heavy steps. A skipped heavy job is not a full-verification pass. This local run is not that classification and does not transfer to a later SHA. CI from an earlier SHA does not transfer. Final-head run IDs belong in the pull-request report after a head exists (AGENTS §11), not in a commit.

## Existing coverage (AGENTS §7)

No new tests. The proposal §8 maps the re-estimate §3 test names and the preservation record. Integration (a) itself is partial or not covered. The decision text is this document, and it has no effect before User merge.

## Contract classification (AGENTS §8)

No explicit contract violation. The proposal does not redefine a contract, choose a cut-proof option, fill a product number, or edit `docs/contracts/`.

Contract-undefined items, left open:

- Whether the framed fsync journal is inside the log-engine lock. Owner: User. The recommended restart shape does not draw that boundary.
- The 6~10 wire/journal split, as already allocated in the re-estimate. This proposal does not split it again.
- v5 construction, T0-to-v5 migration, the blocked fraction of WP3/WP4, stage-5 binding, and actual elapsed effort. Each remains `숫자 없음`.

## Non-claims

No production readiness, durability, distributed fencing, bank exactly-once, chain finality, or legal compliance. No approved SLO, TPS, p99, or cost. No R2 number. The first batch is not complete. The #136 merge's I12 option was not inferred. The 17~28 and 14~24 figures are the re-estimate's planning brackets, not a quote or a start authorization. No real funds, PG, bank, KYC, public endpoint, Sui testnet or mainnet, replication, consensus, storage engine, or new coin/TIX module. No exact-head CI.

## Deviations from the design plan

- The plan's "framed-fsync journal" is the PR #11 local journal as the re-estimate measured it: length-prefix frame, sequence, previous hash, SHA-256 via `canonical_hash_bytes`, append and fsync before apply. No CRC constant. The §6 sentence keeps the plan's words 「별도 프레임 저널」. The body says what that phrase points at.
- SDK checks were not run. This node's plan says to run them only when Node 24 is present. This host has Node v20.19.2.
- The 2026-10-09 validation bullet is in the 2026-10-08 index list, because that is the list the plan named. The bullet text carries 2026-10-09.
- The PR #11 cold-build was not rerun. The preservation record is the citation.
- A second `cargo test --workspace --locked -- --quiet` recovered per-crate counts after the first workspace log was truncated in the session display. Both runs exited 0.

## Remaining uncertainty

- Journal-versus-log-engine remains undecided. Owner: User.
- New wire or catalogue exposure of v5 transitions, H_g (A4), the time source (A5), an uncooperative executor (A10), I09 numbers, and I11 limits stay DECISION_REQUIRED · Astra.
- Toss facts (I02–I05, I08, TM04, TM05) stay UNDETERMINED · Toss contract/technical. I10 stays UNDETERMINED · legal/privacy. I13 and cost rates stay UNDETERMINED · user / operations owner.
- I12 independent review (A9) and trust policy stay with the User.
- `protocol-integration-evidence-closeout` lists this node in its predecessor list (`docs/decisions/PROGRAM_ROADMAP_20260930_PENDING.json` line 130). Under DEFERRED, integration (a) stays WAITING/HOLD in the catalogue. This session did not edit `.aiops/` or the catalogue.
- Hosted CI for the exact head does not exist until a head is published. A documentation-only skip on that head is not full verification.
