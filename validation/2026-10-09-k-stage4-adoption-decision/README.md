# k-stage4-adoption-decision — backend adoption proposal

Node: `k-stage4-adoption-decision`. Document only. No code, no new tests, no
backend implementation, no second comparison table, no SLO or cost numbers.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `k-stage4-local-exploration`.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`6e54e723d582e88ae89df309eb144d4664c7e1f5`.
Branch: `agent/kix-k-stage4-adoption-decision`.
This session did not commit, push, open a PR, or comment. There is no
implementation commit SHA. Local results below are not exact-head CI.
There is no KTX kernel verification run ID and no KIX protocol verification
run ID for a head that contains these files. CI not run; no exact-head run ID.

Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged; the new files are untracked and `docs/README.md` is a worktree edit):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime`
was empty. `git status --short` is the list of changed paths.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` | Decision proposal. Effect only on User merge. Recommendation is A: PostgreSQL 17.11 for the stage-5 local, non-production scope. |
| `docs/README.md` | One index row. Status text: 결정 제안, 사용자 병합 때에만 효력, 구현 없음. |
| `validation/2026-10-09-k-stage4-adoption-decision/README.md` | This record. |

## Commands and results

Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1 (797e8a9bc 2026-08-05)`.
That matches `rust-toolchain.toml` channel `1.98.1`.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | both `6e54e723d582e88ae89df309eb144d4664c7e1f5` |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/adr runtime` | empty |
| Relative `](…)` targets in the new proposal, `test -e` each | 25 targets, 0 missing |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests, OK (`Ran 7 tests in 0.164s`) |
| `python3 scripts/check_openapi_contract.py` | exit 0. `openapi contract pin ok: commands=40 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. 53 tests, OK (`Ran 53 tests in 3.393s`). The same process printed `self-test: pass`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. kix-bcs1 3 + golden_vectors 4, kix-feature-ir 5 + audit_regressions 8 + schema_bound 18, kix-feature-semantics 6, kix-kernel lib 0 + contract_edge_cases 8 + contract_invariants 3 + e4_state_model 12 + observation_slots 11 + performance_harness 4 + quarantine_capacity 8 + transitions 32, kix-types 6. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. For a diff limited to
`docs/decisions/*`, `docs/README.md`, and `validation/*` other than
`validation/2026-09-11/*`, both workflows classify the change as
documentation-only and skip the heavy steps. A skipped heavy job is not a
full-verification pass. This local run is not that classification and does not
transfer to a later SHA.

Not run locally: OpenAPI `--self-test`, reference state-machine suites, SDK
conformance, `scripts/verify_runtime.py`, commerce and canonical verifiers,
storage probes, localnet, ZK. Those steps are the heavy path the classifier
skips for this diff.

Stage-4 measurements were not rerun. They need local PostgreSQL 17 and
FoundationDB 7.3.77, and a new host would be a different measurement.

## Deviations from the design plan

- Footprint is the §9 byte counts (PostgreSQL RSS sum `60018688`, disk
  `41535867`; FoundationDB RSS sum `146341888`, disk `210918811`). The plan's
  "59 MB" is not that sum (60.018688 decimal MB, 57.24 MiB). No megabyte
  rounding and no second comparison table. Goodput figures were not copied.
- ADR-0001 addendum B is the durable inbox. Outbox is named by development-plan
  line 112 and §10, not by that addendum.
- `.aiops/program.json` has no `astra_gate` key on this node. `astra_auto_merge`
  is false. The stage-5 spec's development-plan pointers (`~109`, `268–275`)
  do not land on the stage-5 row (112) or §10 (467–474). The proposal records
  that drift and does not edit `.aiops/`.

## Non-claims

No production readiness, durability equivalence, exactly-once, or finality.
No ranking. No approved SLO, TPS, p99, RTO, RPO, or cost. No lock opened.
No effort estimate. No exact-head CI.
