# RS journey evidence completeness — synthetic offline comparator evidence

Builder record for node `plan-rs-journey-evidence-completeness`, 2026-10-21.
Task input is the supervisor-provided node specification/design in the session;
there is no issue or task document for this node. This is not ASTRA program mode.

## Provenance and boundaries

Initial HEAD and locally observed `origin/main` both:
`4e5c30cc6779ea8b7d26fa40fdde6c84adfd44b7`.
Branch: `agent/kix-plan-rs-journey-evidence-completeness`; initially clean.
The supervisor prohibits all network/GitHub actions, so `git fetch origin main`
was not run; remote freshness is unverified. No rebase/base change occurred.
No commit, push, PR, issue, comment or merge is authorized. Implementation/final
commit SHAs, exact-head KTX/KIX CI run IDs/status/conclusion, A2 non-author review
and post-merge verification remain supervisor delivery gates, not local results.

## Existing coverage map (source inspection before adding tests)

| Requirement | Classification and existing evidence |
| --- | --- |
| Model/vector semantics | Sufficiently covered for reuse: `reference/rights_scale/test_model.py`, `Scripts.test_scripted_scenarios_end_in_a_consistent_state` and `Scripts.test_matrix_cases`; `test_private_model.py`, `Vectors.test_every_scenario_replays_with_its_scripted_outcomes_and_invariants`. |
| Comparator positives and divergence | Partially covered: historical `validation/2026-10-14-rs-1-public-path/README.md`, `2026-10-14-rs-2-private-path/README.md` (manual negative controls), `2026-10-14-rs-3a-delegation-primitives/README.md`. Existing test modules contain no automated comparator invocation. |
| Exact scenario/show/ticket membership; unique mint mapping | Not covered by dedicated comparator regressions. Count-only scenario checks do not establish uniqueness. Public comparison iterates reported ticket snapshots, allowing omissions. Private comparison iterates expected tickets but does not reject extra snapshots or aliased mint IDs. |

Synthetic fixtures use the existing replay/model helpers and fabricated object
IDs, labelled `SYNTHETIC_OFFLINE_COMPARATOR_ONLY`. Inputs and receipts live only
in temporary directories. The legacy success status remains unchanged for API
compatibility; it is never reported here as actual localnet evidence.

## Reproduction and correction

Before comparator edits, the complete public/delegated and private synthetic
controls passed (2 tests). Replacing the second record with a copy of the first
preserved report length and incorrectly passed both comparators. Removing a public
ticket snapshot while retaining its mint also incorrectly passed. The three
regression assertions failed with `SystemExit not raised`, demonstrating those
specific gaps rather than claiming any chain execution.

The comparators now count scenario-name multiplicities before lookup creation,
report sorted duplicate/missing/unexpected names and reject ambiguous expected
names. Private `controlIds` and `shows` must each exactly cover the expected shows;
per-show IDs must agree and cannot alias another show (even with different hex
padding). Missing show IDs are diagnosed before replay, avoiding default-ID
fallback. Mint count, unique ticket IDs and exact snapshot membership must pass
before constructing a mint-order mapping. Missing mint ticket identifiers produce
failures rather than a traceback. Public slot/generation checks and every mapped
ticket's field comparison remain in place. Private outcome-length diagnostics now
include both lengths. CLI and receipt fields/statuses remain compatible.

`test_compare_localnet.py` supplies shared synthetic fixtures/assertions and public
controls from every named vector plus matrix expansion, including
`rs3a_delegation_cut`. `test_compare_private.py` reuses them for every private
vector, including multiple shows. Mutations cover omitted/extra/unknown/duplicate
scenarios, duplicate expected names, missing/extra shows and control IDs,
mismatched/aliased IDs, missing/extra/substituted ticket snapshots, missing/extra
mints, duplicate mint IDs and missing mapping identifiers. CLI cases check
nonzero exit, `FAILED_MODEL_DIVERGENCE`, populated contextual diagnostics and no
traceback. Positive controls include reorderings and empty ticket collections.
Outcome, control/page, ticket, public grant/shard/payment/evidence and private
counter divergence checks are retained and exercised. Private-off state and
outcome length in both directions are covered.

Full public vectors finish without retained resale evidence. To exercise evidence
translation positively, one test truncates an existing vector just after its
successful payment attestation, then checks an amount mutation. This is an
in-memory synthetic input, not a new vector file or historical report modification.

## Actual verification

Python is `3.13.5` on this host (design anticipated 3.12); Cargo is `1.98.1`.
Python checks used `PYTHONDONTWRITEBYTECODE=1`; Cargo checks used
`CARGO_NET_OFFLINE=true`. All commands were foreground local processes; no
bootstrap, network fetch, chain journey, ceremony or artifact generation ran.

| Command actually run | Actual result |
| --- | --- |
| `git status --short`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git branch --show-current` | Initially clean; SHAs and branch above. |
| `python3 --version`; `cargo --version` | Python 3.13.5; Cargo 1.98.1. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale -p 'test_compare*.py' -k complete_positive -v` (before fixes) | Exit 0; 2 positive controls passed. |
| `PYTHONPATH=reference/rights_scale python3 -m unittest test_compare_localnet.PublicComparator.test_duplicate_scenario_hides_omission test_compare_private.PrivateComparator.test_duplicate_scenario_hides_omission test_compare_localnet.PublicComparator.test_missing_ticket_snapshot -v` (before fixes) | Exit 1; all 3 failed with `SystemExit not raised`: erroneous acceptance reproduced. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale -p 'test_compare*.py' -v` (first post-fix run) | Exit 1; 21 tests, one fixture error (`StopIteration` selecting retained evidence absent from full-vector endpoints). Corrected using the attestation prefix described above. |
| Same focused command, after fixture correction | Exit 0; 22 tests passed. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` (initial broader run) | Exit 0; 151 tests passed. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale -v` (captured by a stdlib subprocess wrapper) | Exit 0; 151 tests passed; all 22 then-current comparator tests from both modules explicitly listed. |
| Same focused command, after adding missing-identifier and private length diagnostics regressions | Exit 0; 24 tests passed. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` (final code) | Exit 0; 153 tests passed. |
| `python3 scripts/check_docs_index.py`; `python3 scripts/check_docs_index.py --self-test` (after record write) | Both exit 0; index scanned 193, indexed 158, allowlisted 35; self-test passed. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; v5/KTX-R1 dependency gate passed; no durability/performance certification. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 78 tests passed across test targets, no failures/ignored tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 257 tests passed across test targets, no failures/ignored tests. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |

The unchanged `protocol.yml` **Stdlib offline document checks** run block was
extracted read-only and executed via `subprocess.run` (26 commands). Each row below
represents two actual invocations: plain and with `--self-test`.

| Command (plain and `--self-test`) | Actual result for both |
| --- | --- |
| `python3 scripts/check_status_register.py` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py` | Exit 0 |
| `python3 scripts/check_docs_index.py` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0 |

CI discovery is unchanged: `.github/workflows/protocol.yml` invokes
`python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale`;
`scripts/verify_runtime.py` discovers this directory with `-p test*.py -v`.
The local default/verbose discovery runs confirm both new modules are collected.
This does not constitute a hosted CI run.

## Protected files and changed paths

Before edits, `git hash-object` (called via a Python subprocess) matched both locks:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

The before-work manifest covers all 108 files under `reference/v0.3-rc1/**`:
relative path to SHA-256 of bytes, serialized with `json.dumps(..., sort_keys=True)`.
Its SHA-256 is `dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
It is temporary (`/tmp/rs-protected-before.json`), not a repository artifact.

After implementation, direct
`git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
again returned the two exact hashes above. A Python inline check rebuilt the same
complete path/content manifest, asserted equality with the before-work manifest,
and confirmed the same 108-file count and manifest digest. It also asserted that
`git diff HEAD -- reference/v0.3-rc1 runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
is empty. All checks passed. `git diff --check` passed. Final observed HEAD remains
`4e5c30cc6779ea8b7d26fa40fdde6c84adfd44b7` with the six uncommitted paths below;
this is a base anchor, not an implementation commit. Final-merge blob and
main/push CI checks are not applicable (no merge).

Complete changed-path list:

- `reference/rights_scale/compare_localnet.py`
- `reference/rights_scale/compare_private.py`
- `reference/rights_scale/test_compare_localnet.py`
- `reference/rights_scale/test_compare_private.py`
- `validation/2026-10-21-plan-rs-journey-evidence-completeness/README.md`
- `docs/README.md`

## Deviations, non-claims and remaining gates

No scope/design change. Minor fixture adjustment: retained evidence uses an
existing vector prefix because complete vector endpoints retain none. Host Python
is 3.13.5 rather than the anticipated 3.12. Fetch is omitted under the supervisor's
explicit no-network instruction; origin freshness remains unverified. There is no
separate task file to edit/create. No commit/final delivery SHA exists yet.

No new protocol-contract violation or contract-undefined behavior was found.
The reproduced defects concern evidence comparator completeness and are corrected
within this node's authorization. General JSON-schema validation, cryptographic
root/nullifier values and driver correctness remain outside these comparisons.
Synthetic reports are source-informed model projections, not independent model
verification. Historical evidence is preserved; no localnet, cryptographic,
performance, operational, legal, durability or production-readiness claim is made.
No policy value or owner changes: unresolved P/S/K, retention, IssuerCap and GA
redistribution questions remain `UNDETERMINED`/`DECISION_REQUIRED` with their
existing owners. A2 non-author review and exact final-head KTX/KIX CI are still
required for supervisor delivery; local checks do not authorize merge.
