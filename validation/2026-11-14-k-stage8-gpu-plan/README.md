# k-stage8-gpu-plan — builder evidence

Started 2026-11-14; local verification completed 2026-11-15 (Asia/Seoul).
Task: Track K stage 8 native GPU path plan, document only.
Input: supervisor-supplied node specification/design in this session; no issue
and no node task document under `docs/tasks/`. No task input was created or edited.
Branch: `agent/kix-k-stage8-gpu-plan`. Not ASTRA program mode.

Entry HEAD/base and cached observed `origin/main` both:
`f146930d0d8d29263b0e013c10b566050bf62b85`. No local base delta.
Remote freshness UNVERIFIED: supervisor forbids network, so the required
`git fetch origin main` was not run. No rebase, merge or branch changes occurred.
Implementation/final commit SHA: not assigned; supervisor owns committing the
uncommitted delivery. Entry HEAD is not a commit of these new documents.
Merge SHA/post-merge blob and main CI checks: not applicable; no merge performed.

KTX exact-head CI run ID/status/conclusion: unavailable/not queried.
KIX protocol exact-head CI run ID/status/conclusion: unavailable/not queried.
No GitHub actions, polling, comments, issues, PR, commit or push performed.
A2 non-author exact-head review and final-head CI remain supervisor gates;
local delivery readiness does not mean merge-ready.

## Deliverable and coverage

See [native GPU path plan](../../docs/operations/NATIVE_GPU_PATH_PLAN.md):
semantic acceptance matrix (§2), native ABI and prerequisites (§3), complete
transfer-cost protocol (§4), runner options/cost model and eight-check lane (§5),
and decision/implementation holds (§6). Costs are UNDETERMINED; measurements
NOT_RUN. No equipment, paid service, GPU, new policy value or secret is needed
to deliver this plan.

| Requirement | Existing coverage classification | New evidence/gap addressed |
|---|---|---|
| Semantic match criteria | Sufficient named CPU subset; partial general semantics; native GPU not covered | Contract-to-test matrix with exact fixture paths and future GPU obligations; no duplicate tests |
| Transfer-inclusive crossover | Design exists; execution not covered | Phase boundaries, provenance, comparable CPU/GPU cost, overlap handling, three consecutive scales/zero fallback; no performance results |
| Native ABI | Header/design partial; implementation/lifetime/resource coverage absent | Exact existing names, wire/ABI gaps and future fault tests; no header or code change |
| Runner/equipment/costs | Future requirements only; no inventory/quote/qualification | Three options, cost formulas, quote fields/owners and all eight CI checks; no numeric quote or selection |
| Dependency completion | Stage-7 local source-informed evidence and #451 ancestry present; authoritative A2/CI unavailable | Distinguishes delivery presence from completion; future GPU work HOLD |

No new tests added. No explicit contract violation found during document/source
inspection. Class B: stage-7 nullable arithmetic NULL propagation remains an
observed characterization; F64 tolerance/normalization, cancellation-sensitive
SUM order and Fast64 adoption remain UNDETERMINED. No normative contract changed.

## Protected paths and commands

Complete changed-path list (all document/evidence outputs):

- `docs/operations/NATIVE_GPU_PATH_PLAN.md` — main plan.
- `docs/README.md` — links to plan and evidence; no status/authority change.
- `validation/2026-11-14-k-stage8-gpu-plan/README.md` — this report.
- `validation/2026-11-14-k-stage8-gpu-plan/offline-checkers.sh` — unchanged
  67-command workflow run block, extracted for reproducibility with
  `set -euo pipefail`; evidence only, not a new test harness or CI change.
- `validation/2026-11-14-k-stage8-gpu-plan/commands.jsonl` — actual foreground
  check commands, UTC start timestamps, durations, exit codes and complete output.
- `validation/2026-11-14-k-stage8-gpu-plan/protected-files.json` — before/after
  SHA-256 inventory of all 125 tracked protected files and exact kernel blobs.

Both locked Git blobs match before and after:

| File | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

[Protected inventory](protected-files.json) covers both kernel files and all
tracked `reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**`, `.github/**`.
All 125 files match their entry bytes. Additional Git diff/untracked checks
confirm no runtime, reference, task, program or workflow changes. Final-merge
verification is not applicable. New-document links resolve locally; final
whitespace checks include the new untracked documents/evidence.

Commands below actually ran from the worktree root, narrow checks first. Rust
used the provisioned **1.98.1** toolchain, `--locked --offline` without downloads.
Full output and actual commands are in [commands.jsonl](commands.jsonl).
All checks completed in the foreground; no background long job or automatic
retry was used. No verification failure required a code/CI fix.

| Command | Actual result |
|---|---|
| `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Expected task branch; both SHAs `f146930d0d8d29263b0e013c10b566050bf62b85` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before/after |
| `git merge-base --is-ancestor bb193efb5d238581096372c8a20bee1271dfe4df HEAD`; Python comparison of decision §6 against that merge | Exit 0; exact approved section matches; scope only, not capability evidence |
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=418, indexed=383, allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; negative controls pass |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; 41 historical rows: 3 COVERED, 21 PARTIAL, 17 NOT_COVERED; unchanged map |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; 81 negative controls plus injected positive control |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture/dependency gate OK; durability/performance not certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed |
| `bash validation/2026-11-14-k-stage8-gpu-plan/offline-checkers.sh` | Exit 0; all 67 commands from current `protocol.yml` Stdlib offline document checks block pass, including self-tests |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 139 passed, no failures/ignores |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 339 passed, 1 explicit engine-feature ignore |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0 |
| Python SHA-256 before/after inventory and local Markdown link resolution | 125 protected files identical; new-document local links resolve |
| `git diff --check` and whitespace inspection of new untracked text files | Exit 0; no whitespace errors |

The unchanged `.github/workflows/ktx-kernel.yml` and `protocol.yml` were inspected.
These paths meet their documentation-only classification: KTX heavy checks are
normally skipped, while the full protocol stdlib document-check block still
runs. This delivery also ran explicit kernel and default workspace checks.
Default workspace tests do **not** run optional Polars/DuckDB acceptance: the
single ignore names the required `engines` feature. That is not CPU engine or
GPU conformance evidence. Unrelated heavy protocol checks (bootstrap/downloads,
Move/Sui/localnet/ZK and untouched reference suites) were not run for this
document-only change. No CI success is inferred from a local run or earlier SHA.

## Deviations and limitations

- Supervisor's no-network/no-publication rule overrides fetch and delivery steps;
  no authoritative external dependency/review/CI claims are made. No task issue
  exists and the explicit non-program-mode instruction controls the generic
  common-rule reference to program mode.
- Approximate task line numbers have drifted; development-plan §§5/13 and runtime
  GPU/performance sections supply the actual scope anchors.
- Local Python is 3.13.5 versus workflow Python 3.12. Rust 1.98.1 matches CI.
- No GPU bridge, harness, workflow, dependencies, registered wire schema or
  hardware was added. Future gates and missing inputs do not prevent the
  expressly authorized preparatory document.
- No GPU/transfer/spill measurement, engine conformance rerun, PostgreSQL source
  test, Move/Sui/localnet/ZK execution, production runtime or external integration
  is claimed. Existing stage-7 results retain their original scope and SHA.
- The builder cannot perform A2 non-author review of its own work. Supervisor
  must obtain that and exact-final-head KTX/KIX evidence after committing;
  no later commit is needed solely to record its own CI results.

Remaining work belongs to separately authorized follow-ups: obtain authoritative
dependency/A2/exact-head evidence; resolve semantic-policy and ABI inputs; obtain
compatible host inventory and written cost quotes for a User decision; only then
consider native implementation, GPU lane qualification and measurements. This
report changes no plan/catalogue definitions or completion predicates.

Local document delivery: **READY for supervisor review/commit**, with the external
gates above outstanding. GPU implementation, equipment use/spend and activation
remain HOLD. No root `DECISION_REQUIRED.md` was needed because completion of the
authorized plan did not require crossing a STOP boundary.
