# Cargo offline archive cache preflight

Node: `plan-plan-cargo-offline-cache-preflight`. Builder execution: 2026-10-28;
the directory date follows the supplied design plan. Source: supervisor-supplied
node envelope and design plan, KIX planner run 1793088666
(`/workspace/kix-run/logs/planner_1793088666`). This is an issue-less,
non-program-mode, loop-proposed node, absent from `.aiops/program.json`.
There is no corresponding `docs/tasks/` document. This record is builder-authored
evidence, not non-author review or merge authorization.

## Identity and scope

Branch: `agent/kix-plan-plan-cargo-offline-cache-preflight`. Initial HEAD and
observed cached `origin/main` are both
`307f913fece040f3c735304555c3279dfb424f6b`, matching the design snapshot.
Remote freshness is unverified: the supervisor's explicit ban on network actions
overrides AGENTS.md §1's fetch instruction. No fetch, rebase or base change ran.
Implementation/final committed task head remains that SHA plus the uncommitted
four-path patch; the supervisor owns commit/publication. No merge occurred.

Complete changed paths:

- `scripts/check_cargo_offline_cache.py`
- `.github/workflows/protocol.yml` (exactly two invocation lines added)
- `docs/README.md`
- `validation/2026-10-27-plan-cargo-offline-cache-preflight/README.md`

## Motivation and boundaries

The [October 23 addendum, RS batch-2 stop](../../docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-rs-map-gap-closure-batch-2)
records workspace tests and Clippy stopping before compilation with uncached
`bcs v0.2.1` in explicit offline mode. This is historical evidence, not a current
blocker assertion. The [October 25 closure](../../docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md)
and [resumed RS batch-2 validation](../2026-10-23-rs-map-gap-closure-batch-2/README.md)
subsequently record owner-managed toolchain/cache provisioning and passing
workspace verification. This node provisions, downloads and changes nothing in
the Cargo cache; missing archives are report data, not authorization to fetch.

The [checker](../../scripts/check_cargo_offline_cache.py) reads the lockfile bytes
once, hashes those exact bytes, and counts every `registry+` package entry without
deduplication. It checks regular archive files at exactly one directory level
under the effective Cargo home's `registry/cache/`. Git/path entries are ignored.
Nonempty `CARGO_HOME` takes precedence over `~/.cargo`; the reported path is
absolute and normalized. Names/versions are validated before path construction.
Missing directories/archives are expected; permission and other inspection errors
produce stderr and exit 2 without a success report. Plain mode exits 0 on valid
inspection, `--require` returns 1 on missing archives, and CI invokes only plain
and `--self-test`. Invalid or combined modes exit 2.

`tomllib` is preferred; only its absence selects the legacy parser, never a TOML
syntax error. The fallback is deliberately limited to Cargo-generated root
integer version, package tables, quoted basic strings, dependency string arrays,
comments and whitespace. Unsupported constructs, duplicate keys, incomplete
tables/arrays and malformed values are refused. It is not a general TOML parser.
The fallback is forced during self-test on this modern interpreter; execution
under an actual Python < 3.11 interpreter remains untested.

## Coverage mapping before implementation

| Requirement | Existing coverage classification | Gap addressed or reused evidence |
|---|---|---|
| Lock parsing, counts, archive presence and CLI exit behavior | Not covered | New embedded `self_test()` uses temporary synthetic locks/cache, both parsers, all-present, one-missing, git/path ignored, malformed exit 2, complete require=0 and missing require=1. |
| Wrong version, multiple registry directories, `.crate` directories and depth | Not covered | New controls require regular files with exact name/version at one level; a nested hit does not count. |
| Malformed fallback syntax and inspection errors | Not covered | Duplicate/unsafe/missing fields, broken arrays, unsupported syntax, injected permission failures and absent-cache controls. |
| Entry multiplicity | Not covered | Duplicate name/version across sources counts as separate entries. |
| CI wiring | Sufficiently covered | Existing `scripts/check_ci_checker_wiring.py`, plain and self-test, unchanged. |
| Documentation index | Sufficiently covered | Existing `scripts/check_docs_index.py`, plain and self-test, unchanged. |
| CI test discovery | Sufficiently covered | Existing `scripts/check_ci_test_discovery.py`, plain and self-test, unchanged; new embedded tests reached by wiring. |
| Protected inputs | Partially covered | Existing kernel lock enforcement plus task-specific before/after byte snapshot and restricted-diff checks. |
| Actual builder cache | Not covered | Real plain report below, independently compared with `tomllib` registry entries and forced legacy parsing. |

## Actual builder report

Python: `3.13.5`; effective Cargo home: `/home/box/.cargo`.
Plain mode and host `--require` both exited 0:

```json
{
  "cargo_home": "/home/box/.cargo",
  "lock_sha256": "a948a1b687de2727ad717db0f7a0aa4159ecf5258e52e18eccf05cc08329d83e",
  "missing": [],
  "present": 18,
  "total": 18
}
```

This reports archive presence on this builder only. Archive integrity, registry
indexes, source replacement and toolchain availability are separate predicates;
the report does not establish offline compilation success.

## Verification evidence

All commands below were actually run in this worktree. Python check commands
used `PYTHONDONTWRITEBYTECODE=1`; Cargo commands used `CARGO_NET_OFFLINE=true`.
Foreground command collectors executed each list sequentially and captured
actual stdout/stderr and exit codes in `/tmp/kix-offline-*-results.json`.
Those scratch logs are not repository artifacts. No shell background jobs,
dependency downloads or provisioning ran.

Narrow checks ran first via `python3 /tmp/kix-offline-run-checks.py narrow`:
the Cargo checker and the three existing wiring/index/discovery guards each
ran with `--self-test` then plain, followed by host `--require`: nine commands,
all exit 0. The final checker self-test was also run directly after adding
environment/default-home, Unicode escape, missing-lock and invalid-cache controls;
it exited 0. Its final implementation was then reached by the full block below.

`python3 /tmp/kix-offline-run-checks.py docs` extracted the unchanged
`Stdlib offline document checks` run block plus the two new lines directly
from `protocol.yml` and executed all 63 invocations in workflow order:

| Actual command | Exit / result |
|---|---|
| `python3 scripts/check_status_register.py` | 0 |
| `python3 scripts/check_status_register.py --self-test` | 0 |
| `python3 scripts/check_rs_profile_traceability.py` | 0 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 |
| `python3 scripts/check_read_model_source_map.py` | 0 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 |
| `python3 scripts/check_docs_index.py` | 0 |
| `python3 scripts/check_docs_index.py --self-test` | 0 |
| `python3 scripts/check_i12_proof_ids.py` | 0 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_contract_error_codes.py` | 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 |
| `python3 scripts/check_adapter_identity_map.py` | 0 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_readiness_evidence_map.py` | 0 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_settlement_evidence_map.py` | 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_bra_evidence_map.py` | 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_credit_evidence_map.py` | 0 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py` | 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py` | 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_bcs1_evidence_map.py` | 0 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py` | 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py` | 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | 0 |
| `python3 scripts/check_evidence_map_rollup.py` | 0 |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | 0 |
| `python3 scripts/check_class_b_index.py` | 0 |
| `python3 scripts/check_class_b_index.py --self-test` | 0 |
| `python3 scripts/check_ci_checker_wiring.py` | 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | 0 |
| `python3 scripts/check_ci_test_discovery.py` | 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | 0 |
| `python3 scripts/check_loopback_host.py` | 0; all_ok=true, child exit 0; host context only, no gate suite |
| `python3 scripts/check_loopback_host.py --self-test` | 0 |
| `python3 scripts/check_cargo_offline_cache.py` | 0; 18 total, 18 present, missing=[] (full JSON above) |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | 0; both parsers, required cases and extra controls pass |
| `python3 scripts/check_stage5_host.py --self-test` | 0 |

Closest KTX/shared architecture checks ran via
`python3 /tmp/kix-offline-run-checks.py architecture`; offline Rust checks
ran via `python3 /tmp/kix-offline-run-checks.py rust`. Each collector exited 0.
These are local equivalents of applicable KTX/KIX architecture and Rust steps,
using the already-installed pinned Rust 1.98.1 toolchain and existing cache.

| Actual command | Exit / result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | 0; passed |
| `python3 scripts/test_runtime_architecture.py` | 0; 7 tests, OK |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 0; passed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | 0; passed |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 0; passed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | 0; passed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0; passed |
| `python3 scripts/check_cargo_offline_cache.py --require` | 0; actual host has all 18 archives. Synthetic missing case asserts exit 1. |
| `PYTHONDONTWRITEBYTECODE=1 python3` inline independent-count/cwd check | 0; independent `tomllib` entries equal forced legacy entries, count=18; absolute script invocation from `/tmp` exits 0; Unicode escape controls pass. |
| `PYTHONDONTWRITEBYTECODE=1 python3` inline `ast.parse(..., feature_version=(3, 8))` | 0; Python 3.8 grammar accepted; not execution under Python 3.8. |
| `python3 /tmp/kix-offline-integrity.py` | 0; 119 protected files byte-identical, exact four allowed changed paths including untracked files, workflow exactly two additions. |
| `git diff --check` | 0; no whitespace errors. |
| `git status --short` | 0; only the four allowed paths (new validation directory contains its README). |
| `git branch --show-current` | 0; `agent/kix-plan-plan-cargo-offline-cache-preflight`. |
| `git rev-parse HEAD` and `git rev-parse origin/main` | Each 0; both `307f913fece040f3c735304555c3279dfb424f6b`. |
| `python3 --version` | 0; Python 3.13.5 (`/usr/bin/python3`, from the independent check). |

The independent inline check compared the exact list of name/version dictionaries
filtered from a separate `tomllib.loads(runtime/Cargo.lock)` with both checker
parser paths, then parsed the JSON from an absolute-path subprocess invocation
with `cwd=/tmp`. No parser result or expected registry count is hardcoded into
the checker. Real `CARGO_HOME` was unset on this builder.

Before editing, a SHA-256 snapshot covered 119 protected regular files: every
`reference/v0.3-rc1/**` file, every existing Cargo.toml, runtime/Cargo.lock and
the two locked kernel files. The after-work integrity helper compares each
byte digest, checks protected paths against HEAD, inspects tracked and untracked
changes, and asserts the workflow diff has exactly the two specified additions.
Both before and after, `git hash-object` returned:

| Locked file | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / identical |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / identical |

The archive preflight itself does not invoke Cargo; the separately listed Cargo
commands are builder validation evidence. Full hosted bootstrap, Move/localnet,
ZK setup/proving, HTTP gate and reference runtime suites were not run for this
bounded checker change. No Rust source or manifest changed. Existing stdlib
loopback host preflight ran as part of the required full block and succeeded;
that is capability evidence only and is not HTTP gate execution or host selection.

## Findings, deviations and remaining verification

No contract violation or newly discovered contract-undefined runtime behavior was
found. This tooling changes no runtime semantics, product-policy value, protocol
command, evidence-map status, grade or activation flag. Existing open values stay
UNDETERMINED with their owners. Only synthetic self-test fixtures write temporary
files. The checker imports no repository runtime and invokes no Cargo/process or
network command.

Deviations: no network fetch per supervisor; execution date is October 28 while
the design-specified validation directory/index remain October 27. Actual host
`--require` exits 0 (all archives present); its failure path is verified with
synthetic missing archives. No scope expansion was needed.

Exact-head KTX and KIX hosted CI run IDs/status/conclusions: not obtained, because
GitHub/network actions and publication are prohibited. Final committed-head
verification and non-author exact-head review remain supervisor follow-up; local
results do not transfer old CI evidence or establish merge readiness. Merge SHA,
post-merge CI and final-merge lock checks: not applicable, no merge authorized.
No production runtime, funds, provider/bank/KYC calls, public endpoint, chain
execution, paid service, secret, storage engine, new coin/TIX module or R2 work
was exercised. No performance, durability or production-readiness claim is made.
