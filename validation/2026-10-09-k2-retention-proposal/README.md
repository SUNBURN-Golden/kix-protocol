# k2-retention-proposal — retention periods proposal

Node: `k2-retention-proposal`. Document only. No code, no new tests, no duration
numbers, no new protocol command.
Issue: [#106](https://github.com/SUNBURN-Golden/kix-protocol/issues/106). The
body is the pre-assignment placeholder. It is not a task envelope. `docs/tasks/`
has no file for this node.
Depends on: none.
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`a483ab1777ad0c3e15ff71798822cbf6b3666f83`.
Branch: `agent/kix-k2-retention-proposal`.
This session did not commit, push, open a PR, or comment. There is no
implementation commit SHA. Local results below are not exact-head CI.
There is no KTX kernel verification run ID and no KIX protocol verification
run ID for a head that contains these files.

Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged; the new files are untracked):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts`
was empty. `git diff --name-only origin/main` was empty because the new files
are untracked. `git status --short` is the list of changed paths.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md` | Decision proposal. Effect only on User merge. Recommendation is R1 (four separate periods, owners and anchors, no durations). |
| `validation/2026-10-09-k2-retention-proposal/README.md` | This record. |

## Commands and results

Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1`. That matches
`rust-toolchain.toml` and the workflow pin `1.98.1`.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | both `a483ab1777ad0c3e15ff71798822cbf6b3666f83` |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts` | empty |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests, OK |
| `python3 scripts/check_openapi_contract.py` | exit 0. `openapi contract pin ok: commands=40 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0. Suites: contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32. Lib unit tests 0. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. Kernel suites repeated as above. Also kix-bcs1 3 + golden_vectors 4, kix-feature-ir 5 + audit_regressions 8 + schema_bound 18, kix-feature-semantics 6, kix-types 6. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. For a diff limited to
`docs/decisions/*` and `validation/*` other than `validation/2026-09-11/*`, both
workflows classify the change as documentation-only and skip the heavy steps.
A skipped heavy job is not a full-verification pass. This local run is not that
classification and does not transfer to a later SHA.

Not run locally: OpenAPI self-test, integration gate, reference state-machine
suites, SDK conformance, `scripts/verify_runtime.py`, commerce and canonical
verifiers, storage probes, localnet, ZK. Those steps are the heavy path the
classifier skips for this diff.

## Non-claims

No legal, tax, accounting, or privacy conclusion. No row of
`FIRST_BATCH_OPEN_INPUTS.md` closed. `새로 실입력까지 완결된 행: 0` is unchanged.
No lock changed. No production durability. No effort estimate.
