# Evidence-map roll-up and consistency checker

Builder evidence for node `plan-plan-evidence-map-rollup-check`. No issue and no
node document under `docs/tasks/`; the supplied node prompt is the task input and
nothing under `docs/tasks/` was edited. Task base is the observed
`origin/main`, which `git fetch origin main` left equal to the branch HEAD:
`d2b748aef0c7b4af5bef23c771c6bce22b52905f`; no base delta.
Branch `agent/kix-plan-plan-evidence-map-rollup-check`.

**The roll-up is an index. It is not a review, an acceptance or a grade.** It is
index and evidence for `k-local-program-closeout` only. It changes no map status,
grade, owner or row, and adds no totals. The checker verifies textual consistency
of copied lines; it does not test whether any contract clause is satisfied.

Implementation, final and merge commit SHAs, and exact-head KTX and KIX protocol
CI run IDs/status/conclusion: not available in this session (the supervisor
commits and pushes; no network). Not merge-ready on that basis until exact-head
CI passes (AGENTS §10); merge is User-only (§12).

## Changed paths

- `docs/status/EVIDENCE_MAP_ROLLUP.md` (new)
- `scripts/check_evidence_map_rollup.py` (new)
- `.github/workflows/protocol.yml` (two lines in `Stdlib offline document checks`, before the `check_ci_checker_wiring.py` lines)
- `docs/README.md` (one index bullet)
- `validation/2026-10-26-plan-evidence-map-rollup-check/README.md` (this record)

## Existing coverage mapped before changes

| Requirement | Before | Evidence |
|---|---|---|
| Each map's Counts line agrees with its own table | Sufficiently covered per map | Each map's own `scripts/check_*_evidence_map.py`; all 55 stdlib-step commands pass unchanged. |
| Every contract has a map or a stated reason | Not covered | No cross-map index existed. `check_ci_checker_wiring.py` only checks that cited checkers are wired. |
| Copied Counts lines stay current | Not covered | New: `stale Counts copy:`. |

## What the checker enforces

`python3 scripts/check_evidence_map_rollup.py` (stdlib) over 25 contract files
(23 under `docs/contracts/**`, 2 matching `runtime/*_V1.md`):

- every contract file appears exactly once (`contract missing from roll-up:`, `contract listed more than once:`, `roll-up lists non-contract:`);
- every cited map and checker exists (`missing map:`, `missing checker:`);
- each map has exactly one `Counts:` line, and the copy equals it byte for byte (`map Counts line count:`, `stale Counts copy:`);
- each Counts line agrees with the statuses in the map's own table (`counts disagree with table:`);
- listed owners equal the map's distinct non-`none` owner cells (`owners mismatch:`);
- column arity and no-map reasons (`arity mismatch:`, `no-map row lacks reason:`).

`--self-test` has 16 negative controls, including the four required ones (missing
contract, stale copied Counts line, Counts line disagreeing with its table,
missing map path), plus positive controls and a temp-dir `collect()` fixture.

## Observed characterization (contract-undefined, no change made)

`docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` keeps ten BRA-RES9 rows in its
earlier key table, not in the table just above its Counts line. The final table
alone has 189 of the 199 rows. The checker therefore uses a documented row-scope
override mirroring `ROW_START` in `check_contract_error_codes.py`. The map was not
changed or relocated.

Owner cells are compared as whole cells exactly as each map writes them, so some
owner cells contain long free text (for example `TL_PREDICATE_EVIDENCE_MAP`).
Copying is faithful, not summarized. The two TOKEN contracts share one map and
repeat its line.

## Commands actually run (worktree, Python 3, cargo from `~/.cargo/bin`)

| Command | Result |
|---|---|
| `python3 scripts/check_evidence_map_rollup.py` | `evidence map roll-up ok: contracts=25; textual index only`, exit 0 |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | `self-test: pass (16 negative controls)`, exit 0 |
| In-memory mutation of the real snapshot (extra contract, stale copy, map Counts drift, missing map, owner drift) | each reported with its stable marker; unmutated snapshot gave 0 errors |
| All 55 `python3 scripts/check_*.py [--self-test]` lines of `Stdlib offline document checks` (includes `check_ci_checker_wiring.py`, `check_docs_index.py`, every map checker, plain and `--self-test`, and the two new lines) | 0 failures |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | OK |
| `reference/{settlement_f01_f03,booking_resale_admission,credit_advance_f04,ai_delegation,token_reward}` unittest discover | OK (196, 418, 148, 85, 168 tests respectively) |
| `check_openapi_contract.py` and `check_integration_gate_openapi.py`, plain and `--self-test` | pass |
| `python3 -m unittest integration_gate.test_offline_limits` | 4 tests OK |
| `python3 scripts/verify_runtime_architecture.py`, `python3 scripts/test_runtime_architecture.py` | OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | all `test result: ok`, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | finished, no warnings |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 .aiops docs/tasks docs/contracts runtime docs/status 'scripts/check_*.py' ':!scripts/check_evidence_map_rollup.py'` | empty, exit 0 (tracked files only; the new roll-up is untracked at that moment) |

Locked blobs before and after (`git rev-parse HEAD:<path>` and `git hash-object`):
`runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. Both unchanged.

Not run: `python3 scripts/check_sdk_client.py` (plain and `--self-test`) and
`npm --prefix sdk run ...` stop at the toolchain pin
(`node 20.19.2 does not match toolchains.json nodeMajor 24`); this is an
environment mismatch on a path this node does not touch. Also not run:
`scripts/bootstrap.sh` based steps, `verify_runtime.py`, `verify_commerce.py`,
`verify_canonical.py`, storage probes, the disposable-chain journey, the
workspace-wide cargo test and clippy (only `-p kix-kernel` was run), and any
GitHub Actions workflow.

## Non-claims and follow-ups

- Nothing here claims review, acceptance, a grade, production readiness or any contract satisfaction.
- Coupling: from now on, a new contract file, or a change to any map's Counts line or owner cells, must update the roll-up in the same PR or the stdlib step fails. Open PRs that touch maps will fail on the merge ref until they do.
- `COMPATIBILITY_MANIFEST_V1` stays without a map, blocked by `plan-plan-sdk-compat-manifest-clause-evidence` (User decision). `READ_MODEL_QUERIES` stays without one while it waits on `read-model-reference`. Their open values remain UNDETERMINED.
