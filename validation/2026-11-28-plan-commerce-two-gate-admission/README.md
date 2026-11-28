# Two-gate admission companion vectors

The task input is the supervisor's node brief and design plan for
`plan-commerce-two-gate-admission`, from planner run `1795823722`.
The node has no task issue or file under `docs/tasks/`. The local planner
output `planner_1795823722_codex0.out` matches the brief's objective,
acceptance criteria and dependencies.

Branch `agent/kix-plan-commerce-two-gate-admission` started at
`6f2d062d73fd89b8ab9053cfa4912fed85170eb8`. The cached `origin/main` and
the design base matched that SHA. The supervisor's offline instruction
superseded the session-start fetch. Remote freshness is unverified.
The implementation is an uncommitted worktree. Implementation, final delivery
and merge commit SHAs await supervisor publication.

## Acceptance and coverage

| Requirement | Existing coverage | Evidence added |
|---|---|---|
| Same paid, issued and unconsumed checkpoint | Sufficient for the source tuple. `CommerceFixtureTupleTests.test_vectors` replays the setup and `test_all_first_acceptances_resolve` compares full receipts. | Each fresh host replays all eight published envelopes through `adopt-B` and matches the eight indexed receipts. Payment, issuance and adoption have separate references. The hosts begin with identical detached snapshots. Slot 1 is `ISSUED` and `issue-B` is active at version 1 with an eligible credential and no authorization or consume ID. |
| First authorization wins in both orders | Partial. `AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version` exercises one gate order. | Each gate presents the same command pair in both cases, with distinct admission IDs, requests, operation IDs and body keys between gates. The first authorization receipt identifies its gate and request. The second returns `ADMISSION_LOCKED`. |
| Losing consume and refusal isolation | Partial. `AdmissionRejectionAtomicityTests.test_authorize_admission_admission_locked_leaves_no_trace` and `test_consume_gate_mismatch_leaves_no_trace` cover the codes individually. `CommerceReplacedAdmissionBindingVectorTests.test_complete_output_bytes_and_references` covers gate mismatch after replacement. | Before the winner consumes, the losing consume returns `GATE_MISMATCH`. Each refusal preserves the winning authorization and the canonical state and accepted journal of every machine. |
| The first gate consumes once at version 1 | Partial. The tuple replay covers gate-1 and the admission machine test checks duplicate consume behavior. | Each order returns `CONSUMED_ONCE` bound to the winner's gate, request and consume ID. The right advances to version 2, the authorization detaches and slot 1 stays `ISSUED`. The admission and reservation journals preserve their prefixes and each append exactly one winning consume. The other three journals and states match their prior values. |
| Complete indexed outcomes and swapped winners | Uncovered for this pair. | The focused test compares the entire replay record to canonical golden bytes and rejects exchanging just the two winning consume receipts. The companion-index test rejects exchanging just their outcome references. The eight associations resolve to the existing `MOCK_EVIDENCE` bindings at items 73 and 74. |

Both reservation and admission clocks stay at 1,000,000 throughout. Both gate
presentations expire at 1,100,000. The host follows the predicates in §§5 and 11
of the admission contract. The histories revealed no contract violation or
undefined behavior.
[Admission contract](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md) ·
[Inputs](../../reference/booking_resale_admission/fixtures/commerce_two_gate_admission_inputs_v1.json) ·
[Outcomes](../../reference/booking_resale_admission/fixtures/commerce_two_gate_admission_receipts_v1.json) ·
[Index](../../docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md#two-gate-admission)

## Changed paths

- `reference/booking_resale_admission/fixtures/commerce_two_gate_admission_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_two_gate_admission_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_two_gate_admission_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `validation/2026-11-28-plan-commerce-two-gate-admission/README.md`

## Local verification

The Python suites ran from the repository root with `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`. Here `bra` denotes
`reference/booking_resale_admission`. Both focused suites ran before
the broader tests.

| Command | Actual result |
|---|---|
| Inline Python 3.12 `FsmHost` probe | The first probe stopped on a diagnostic lookup for a nonexistent `slots` field in `view_show`. The corrected probe matched all eight indexed checkpoint receipts in both hosts and observed both exact refusal codes and winning consume receipts. |
| Inline Python 3.12 fixture and index generation | Wrote 5,223 input bytes, 114,669 outcome bytes and eight appended index entries. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_two_gate_admission_vectors.py` | Exit 0. Two tests passed. |
| `python3.12 -m unittest discover -s "$bra" -t "$bra" -p test_commerce_companion_evidence_index.py` | Exit 0. Seventeen tests passed across 18 packs and 434 associations. |
| `python3.12 -m unittest discover -s "reference/$suite" -t "reference/$suite"` for the eight reference suites in the protocol workflow | Seven suites exited 0. Booking/resale/admission passed 1,108 tests, settlement 224, credit 341, AI delegation 182, provider facts 86, payment effects 28 and economics 99. The first token-reward pass ran 397 tests and exited 1 after three console subcases missed the 10-second completion deadline and four supply CLI subcases timed out after 10 seconds. The last three suites ran in a separate loop after that early exit. |
| `PYTHONPATH=.:reference/token_reward python3.12 -m unittest -v test_reward_console_subprocess.RewardConsoleSubprocessTests.test_source_incomplete_no_dispatch test_supply_cli.SupplyCliTests.test_every_fixture_file_stdin_parity_and_direct_results` | Exit 0. Both previously affected tests passed with their original deadlines. |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | The full rerun ran 397 tests and exited 1. Three different console subcases in `test_source_domain_refusal_parity` missed the same 10-second completion deadline. The earlier subcases passed. |
| `git diff --exit-code HEAD -- reference/token_reward` and `PYTHONPATH=.:reference/token_reward python3.12 -m unittest -v test_reward_console_subprocess.RewardConsoleSubprocessTests.test_source_domain_refusal_parity` | The token-reward directory matched HEAD. The isolated test exited 1 with three other subcases missing a console completion or shutdown deadline. The full token-reward suite remains unverified on this host. |
| `python3.12 -m unittest integration_gate.test_offline_limits` | Exit 0. Nineteen socket-free tests passed. |
| `python3.12 scripts/check_{docs_index,ci_test_discovery,bra_evidence_map,openapi_contract,integration_gate_openapi,producer_qualification_tuple,contract_error_codes}.py`, each invoked separately and repeated with `--self-test` | All 14 invocations exited 0. |
| `python3.12 validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and repeat with `--self-test` | Both exited 0. All 13 reads are `NOT_BOUND`. |
| `python3.12 scripts/verify_runtime_architecture.py` and `python3.12 scripts/test_runtime_architecture.py` | Both exited 0. The architecture and dependency gate and all seven self-tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 with the installed Rust 1.98.1 toolchain. |
| `cargo --offline` against `runtime/Cargo.toml` with `test -p kix-kernel --locked`, `clippy -p kix-kernel --all-targets --locked -- -D warnings`, `tree -p kix-kernel --edges normal --locked`, `test --workspace --locked`, and `clippy --workspace --all-targets --locked -- -D warnings` | Each exited 101 before compilation. The local index lacks the optional `duckdb` dependency declared by the workspace's `kix-analytics-audit` crate. |
| Inline Python 3.12 workspace copy using `cmp`, `diff -qr`, `cargo --offline generate-lockfile --manifest-path "$manifest"` and `tomllib` | Exit 0. The six copied crate trees and toolchain file matched their originals. All six generated lock entries matched the repository lock. |
| `cargo --offline test --quiet --manifest-path "$manifest" -p kix-kernel --locked` and `cargo --offline test --quiet --manifest-path "$manifest" --workspace --locked` | Both exited 0 in the temporary workspace. 139 kernel tests and 332 tests across the six crates passed. |
| `cargo --offline clippy --quiet --manifest-path "$manifest" -p kix-kernel --all-targets --locked -- -D warnings` and the same command with `--workspace` in place of `-p kix-kernel` | Both exited 0 in the temporary workspace. |
| `cargo --offline tree --manifest-path "$manifest" -p kix-kernel --edges normal --locked` | Exit 0 in the temporary workspace. The kernel's sole normal dependency is `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Computed the three KTX workflow input digests. |
| `git rev-parse HEAD origin/main HEAD:reference/v0.3-rc1` and `git status --short --branch --untracked-files=all` | The two refs matched the design base. The historical subtree was `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The changed paths match the list above. |
| `git hash-object` on both locked files, before and after work | Kernel library matched `69564b166f0c27f9af5d8422f0a466b18d74c20f`. Quarantine capacity test matched `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| Sorted path and byte inventory with `find`, `sha256sum` and `cmp`, plus inline Python comparison with `git ls-tree -rz HEAD` | All 108 files in `reference/v0.3-rc1/` match their starting SHA-256 inventory and HEAD blobs. |
| `git diff --check`, protected-path `git diff --exit-code HEAD`, and inline Python with `git ls-files --others --exclude-standard -z` and `git show HEAD:docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json` | Exit 0. The four new files also passed whitespace checks. Protected paths have no tracked or untracked changes. Original index metadata, 17 packs and 426 associations match the base. |
| `sha256sum` and `git hash-object` on both new fixtures | Both SHA-256 and Git blob digests match the appended index pins. |

The temporary Rust workspace contained `kix-types`, `kix-feature-semantics`,
`kix-feature-ir`, `kix-kernel`, `kix-kernel-v5` and
`kix-delegated-exec`. It was removed after the run. Rust coverage is limited to
these six crates. Bootstrap, Move, chain and ZK workflow stages are outside
the local checks for the touched paths.

## Delivery and scope

KTX kernel verification and KIX protocol verification for the delivery head
each have run ID, status and conclusion unobserved. A2 non-author review and
publication remain pending. Post-merge verification applies after an authorized
merge.

The source-informed fixtures cover sequential mock admission at a synthetic
clock. Cross-host fencing, concurrency, venue admission, durable recovery,
real providers or funds, chain finality, legal compliance and production
readiness are outside the tested scope. The pack carries `HOLD_SEMANTIC`.
All 13 reads are `NOT_BOUND`, SD1 is `OPEN` and User-owned, and external
`kix-commerce-apps` acceptance is `UNVERIFIED`. Product TTLs, fees and
compensation are `UNDETERMINED` with Astra and the User.
