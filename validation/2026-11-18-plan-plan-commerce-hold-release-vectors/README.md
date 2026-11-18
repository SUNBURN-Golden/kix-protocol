# Expired hold release and slot reuse companion evidence

The supplied specification and design for `plan-plan-commerce-hold-release-vectors`
are the task input. The node has no issue or file under `docs/tasks/`. The base,
locally observed `origin/main` and `HEAD` of
`agent/kix-plan-plan-commerce-hold-release-vectors` all resolve to
`f315a499b9894ad6af8933461ad7267eb1b1c4ad`. The supervisor's no-network rule
precluded a fresh fetch. Remote freshness is unverified. The implementation is
in the worktree and the supervisor owns the delivery commit. Hosted KTX and
KIX exact-head run IDs, statuses and conclusions are unavailable for this patch.
A2 non-author review is pending. Merge SHA and post-merge CI are inapplicable.

## Coverage and results

The reservation and atomicity regressions already cover expired hold retention,
release, allocation and refusal behavior. The portable pack adds two 15-step
histories at and after expiry with complete receipts and refusals. Six first
acceptances per history advance the accepted reservation journal. Three replays
return the first receipts. Each replay and each of the six refusals preserves
all five machines' business state, digest and accepted journals. Current
diagnostics show B retaining the slot through every replay. Detached controls cover premature freeing, double
occupancy, changed outcomes, repinned clock drift, and crossed index references.
Test-local journal effects exercise the runtime non-mutation assertions.
[Coverage mapped before implementation](coverage.md)

The pack covers the existing reservation contract. Local verification surfaced
no explicit contract violation. The `expired` value for a released reservation
is an implementation diagnostic derived for pre-issue phases. Rejected keys are
retained within the process and excluded from the accepted journal. The pack is
source-informed and in-process. Durability, distributed exclusivity, actual
provider calls, real money, chain execution and production operation are outside
its scope. Semantic consumption is `HOLD_SEMANTIC`, all 13 reads are `NOT_BOUND`,
SD1 is `OPEN` and User-owned, and external acceptance is `UNVERIFIED`. TTL and
other product values remain **UNDETERMINED—Astra/User**. Legal effects remain
**UNDETERMINED—User/legal**.

## Local verification

The command ledger records exact invocations, environment, exit codes and log
paths. Logs 01–27 were present at resumption. Before the harness refinement,
the three focused Python 3.12 discovery commands below passed with 8, 8 and 85
tests respectively. They passed again after tying the synthetic clock declarations to the actual command bodies
and consolidating the before/after snapshots used by the mutation guard. The
canonical input and receipt bytes stayed identical through those refinements.
Python 3.12.15 matches the protocol workflow's Python series. Rust 1.98.1 matches
the kernel workflow. [Command ledger](commands.json)

| Command | Result |
|---|---|
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_hold_release_vectors.py` | 8 passed. [Log](28-python3.12.log) |
| Same discovery command with `-p test_commerce_companion_evidence_index.py` | 8 passed. [Log](29-python3.12.log) |
| Same discovery command with `-p 'test_reservation*.py'` | 85 passed. [Log](30-python3.12.log) |
| Same discovery command without `-p` | 1,052 passed. [Log](31-python3.12.log) |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Passed. [Check](32-python3.12.log) · [Controls](33-python3.12.log) |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Passed. [Check](34-python3.12.log) · [Controls](35-python3.12.log) |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | Passed. [Check](36-python3.12.log) · [Controls](37-python3.12.log) |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and `--self-test` | Passed with 13 reads `NOT_BOUND`. [Check](38-python3.12.log) · [Controls](39-python3.12.log) |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Passed again with the completed report. [Check](65-python3.12.log) · [Controls](66-python3.12.log) |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Passed. [Check](42-python3.12.log) · [Controls](43-python3.12.log) |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Passed. [Check](44-python3.12.log) · [Controls](45-python3.12.log) |
| `python3.12 -B scripts/check_bra_evidence_map.py` and `--self-test` | Passed. [Check](46-python3.12.log) · [Controls](47-python3.12.log) |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 9 passed. [Log](48-python3.12.log) |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed. 7 regression tests passed. [Gate](49-python3.12.log) · [Tests](50-python3.12.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | 139 passed. [Log](51-cargo.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | 339 passed. The existing optional CPU/SQL engine acceptance test was ignored. [Log](52-cargo.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Passed. [Log](53-cargo.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Passed. [Log](54-cargo.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. [Log](55-cargo.log) |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Passed. Normal dependency `kix-types`. [Log](56-cargo.log) |
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | Earlier run had one subprocess reply deadline failure in `test_source_incomplete_no_dispatch`. All 397 passed on a foreground rerun with the same command and environment. [Failure](27-python3.12.log) · [Rerun](57-python3.12.log) |
| `python3.12 -B -m unittest discover -s reference/<suite> -t reference/<suite>` for `settlement_f01_f03`, `credit_advance_f04`, `ai_delegation`, `provider_facts`, `payment_effects`, `economics` | 224, 284, 169, 86, 28 and 99 passed respectively. [Settlement](24-python3.12.log) · [Credit](25-python3.12.log) · [Delegation](26-python3.12.log) · [Provider](58-python3.12.log) · [Payment](59-python3.12.log) · [Economics](60-python3.12.log) |
| `python3.12 -B scripts/check_status_register.py` and `--self-test` | Passed. [Check](61-python3.12.log) · [Controls](62-python3.12.log) |
| `python3.12 -B scripts/check_read_model_source_map.py` and `--self-test` | Passed. [Check](63-python3.12.log) · [Controls](64-python3.12.log) |
| `git diff --check` | Passed. [Log](67-git.log) |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required hashes matched. [Log](68-git.log) |
| `python3.12 -B validation/2026-11-18-plan-plan-commerce-hold-release-vectors/verify_preservation.py` | 620 inventory paths, all 108 tracked frozen reference files, eight prior packs and qualification metadata verified. [Report](preservation.json) |

Verification used the workflows' offline reference and relevant document checks
and local equivalents of the Rust jobs. Hosted workflows, bootstrap and
chain/ZK jobs are outside this local verification.

## Changed paths and preservation

- `reference/booking_resale_admission/fixtures/commerce_hold_release_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_hold_release_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_hold_release_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- This validation directory contains the coverage, command and preservation
  evidence. The preservation report includes every changed path.

The byte comparison covers contracts, the producer tuple, binding index, SDK,
host and FSM sources, the frozen reference, CI, `.aiops/` and task documents.
The companion index preserves the eight original pack records, all 293 prior
entries and qualification metadata. It appends 30 entries for nine packs and
323 total entries. [Starting byte inventory](preserved-before.json) ·
[Final preservation report](preservation.json)

Both locked files matched before and after work.

| Locked file | Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
