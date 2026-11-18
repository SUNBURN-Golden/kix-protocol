# plan-commerce-temporal-vectors — builder evidence

Task input: supervisor/user node specification and read-only design plan in this
session. No issue or node task document exists; no `docs/tasks/` input was
created or edited. Not ASTRA program mode. Branch:
`agent/kix-plan-commerce-temporal-vectors`.

Starting HEAD/base and cached `origin/main` are equal:
`fc0da57f84471ef41fe56592bd28dd1abb6f345c`. Remote freshness is UNVERIFIED:
`git fetch origin main` was NOT_RUN because the supervisor explicitly prohibited
network/GitHub actions. No observed local base delta. Implementation/final
committed task head is pending supervisor commit; changes remain uncommitted
on the starting HEAD. No commits, pushes, PRs, issues, comments, branch/tag
changes or merges were performed. Merge SHA and post-merge verification: N/A.

## Coverage mapped before implementation

Contract references mean `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`.
The existing behaviors are contract-defined and matching (classification A).
Paid compensation is expressly undefined; its refusal is preserved without
inventing a compensation or refund policy (classification B boundary).

| Requirement | Existing coverage/classification | Portable gap addressed |
|---|---|---|
| Paid expiry refuses issuance and preserves paid reservation; cancellation compensation undefined | Sufficient behavior: `test_reservation_fsm.ReservationFsmTests.test_cancel_before_payment_frees_and_payment_blocks_compensation`; §§3, 9.1, 9.2, 9.6 | Complete nine-step case, full accepted receipts, both cancellation refusals, issuance refusal and final paid/slot/right checks. |
| Both post-transfer presentations refuse admission | Sufficient behavior: `test_admission_fsm.AdmissionFsmTests.test_transfer_then_entry_rejects_both_presentations`; §§10.6, 11.3–11.4 | Complete 15-step case; buyer-2/version 2 resale and buyer-1/version 1 reservation remain separate; both `STALE_VERSION` codes and no credential reissuance. |
| Expiry alone does not consume; explicit replacement then one consumption | Sufficient behavior: `test_admission_fsm.AdmissionFsmTests.test_expired_authorization_is_replaced_once`; §§11.1–11.2, 11.4 | Complete 15-step case; clock and refused-consume observations preserve phases/version, explicit new admission/key/gate/request/expiry, then consumption. |
| Replay is immutable and another consume cannot consume again | Sufficient: same module's `test_issued_credential_is_consumed_once_and_replay_does_not_bump_version`; §§11.4–11.5 | Replay and distinct consumption included in expiry case; complete first-result comparison, state/digest/journal/view non-mutation and `ALREADY_CONSUMED`. |
| Refusal non-mutation | Partial cross-machine portable coverage; existing cited tests assert relevant state/digests/journals | Every refusal compares detached canonical state, state digest and entire journal on all five host machines, plus available existing views. No general rollback claim. |
| Ordered complete inputs, entire receipts, source/artifact identity | Not covered for these cases; existing journey/receipt suite covers only its unchanged journey | Two companion JSON packs, schema checks, fixed case/step order, one outcome per input, pointers, exact bytes, input plus 26 source pins. |
| Mutation sensitivity | Not covered for companion | Altered nested values, added/removed fields, false→0, nulls, codes, omitted/duplicated/reordered input/output steps and cases, reference changes, pins, malformed/duplicate-key JSON and every pinned file's byte drift. |
| Separate facts, false authority flags, all 13 reads NOT_BOUND | Sufficient existing journey invariants; new case evidence absent | Reuse helpers; explicit independent fact paths, all existing false flags checked, catalogue/host absence checks. |
| Producer tuple, consumer binding, document and CI discovery guards | Existing checkers | Run unchanged normally and with negative self-tests; preserve binding statuses, producer artifacts and CI. |

## Boundaries and pending gates

Source-informed in-process mock evidence preparation only. No client, console,
adapter, query, command, SDK example or adversarial corpus is implemented.
All 13 reads remain NOT_BOUND; semantic consumption remains HOLD_SEMANTIC;
SD1 remains OPEN/User-owned. Product time limits remain UNDETERMINED with Astra;
fixture times are synthetic. Legal/provider dependencies retain their contract
owners. Payment observation, issuance, authorization and consumption remain
separate facts. No new explicit contract violation was found. The existing SD1
issue and undefined compensation are unchanged. No new semantic policy chosen.

No external-consumer acceptance, HTTP result, independent/clean-room review,
real payment, chain ownership/finality, durability, venue admission, legal effect
or production readiness is claimed. Broader loopback regressions do not change
those limits. Non-mutation applies to these ordered fixtures, not general
cross-machine rollback or injected-fault cases.

A2 non-author exact-head review: PENDING, supervisor-owned. KTX kernel
verification exact-head CI and KIX protocol verification exact-head CI:
NOT_RUN, run IDs/status/conclusions unavailable; no committed delivery head or
network authorization. Local results do not constitute merge readiness.
Post-merge main CI: N/A, no merge.

## Evidence files

- [Actual commands/results](commands.jsonl) and adjacent full command logs.
- [Artifact/test hashes](artifacts.json), separate from the artifacts to avoid circular hashes.
- [Before-work protected byte inventory](preserved-inputs.json): 443 tracked files covering both locked blobs, frozen reference tree, existing BRA code/fixtures, `.aiops/**`, `docs/tasks/**`, `integration_gate/**`, `sdk/**`, `.github/**`, contracts and both binding/producer status files.
- `run_check.py` records foreground command output, exit status and elapsed time; elapsed times are not performance evidence. It uses `PYTHONDONTWRITEBYTECODE=1` and `CARGO_NET_OFFLINE=true` and installs nothing.

## Deviations and execution scope

The supervisor's no-network instruction overrides session-start fetch; cached
origin/main freshness is not asserted. Task input is this session's supplied
node specification; there is no corresponding node task document to read.
Git/GitHub publication and exact-head CI are reserved for the supervisor.

The proposed JSON format adds optional `observe` for existing-view assertions
at intermediate clock/refusal steps, with final view and separate-fact paths
under `final_expect`. This makes expiry-without-consumption independently
inspectable in the portable inputs; it adds no command or read binding.
The runner uses these observations locally and complete receipts remain the
portable output evidence. No production or contract interface changed.

The initial new receipt artifact was captured once during implementation from
`_observe` and `_canonical`, after confirming the ordered predicates through
FsmHost. Tests have no writer or refresh mode. This is source-informed builder
evidence, not independent acceptance. Both merged journey artifacts and their
tests remain byte-identical.

Toolchain/dependency installation, full frozen-reference aggregate scripts,
Sui/Move/localnet journeys, ZK setup/proving and storage probes are outside the
closest local equivalents for this test/document change and are NOT_RUN.
Some generate protected files or require network. No hosted CI result is
claimed. All recorded results below come from actual command execution.

The document-index check initially failed because this new validation README
was not indexed. A single navigation link was added to `docs/README.md`, beyond
the plan's proposed changed-file list, to satisfy the existing document
contract. The initial failure remains in `check_docs_index.log`; the corrected
run is `check_docs_index-fixed.log`. Both the normal check and self-test then
passed. CI and checker code were not changed.

## Protected blobs and artifact identity

Before work, the inventory matched both required Git blobs; direct
`git hash-object` and `check_preservation.py` confirm them after implementation.
The final verification is recorded separately after all suites complete.

| Locked path | Before/after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`preserved-inputs.json` records raw SHA-256 and Git blob IDs before edits.
`check_preservation.py` checks all 443 entries, absence of new untracked files
in the frozen/task/program trees, and artifact size/SHA-256/Git blob pins.
The source and artifact identities are comparison evidence for this worktree;
no old CI result is transferred to the uncommitted changes. Final merged
blobs and main/push CI are N/A.

| New artifact | SHA-256 |
|---|---|
| `commerce_temporal_inputs_v1.json` | `e4908638e90776c4dec9e95ed934faf74b6a81d354e54ce49bfc60706d0114e2` |
| `commerce_temporal_receipts_v1.json` | `95151db08cf216973c879c4603bb300d9207119570c41aa62e325d12472c004d` |
| `test_commerce_temporal_vectors.py` | `0cdd9393c89cbde9add8d1a44254bfc60817fa67596b7deface06634d88f3dd9` |

## Completed local verification

The nine focused tests, 13 unchanged journey/receipt tests and four named
socket-free regressions passed. The complete 67-invocation stdlib document
block from `protocol.yml` passed (with the documented index fix), as did the
OpenAPI/gate/SDK checks and their self-tests. Architecture and architecture
negative tests, kernel and workspace tests, workspace Clippy, formatting,
SDK conformance and BOOTSTRAP compatibility passed. Broader existing
HTTP/readiness (139 tests) and offline-limit (nine tests) suites passed.
All eight reference-suite discovery commands passed: settlement 224,
booking/resale/admission 970, credit 242, AI delegation 169, token reward 397,
provider facts 86, payment effects 28 and economics 99 (2,215 tests total).
There was one verification failure, the missing documentation index entry;
it was diagnosed, fixed with the one-line index link, and its check rerun
successfully. No other verification command failed.


The new focused coverage is `CommerceTemporalVectorTests` in
`reference/booking_resale_admission/test_commerce_temporal_vectors.py`:

| New test | Gap addressed |
|---|---|
| `test_paid_reservation_expiry` | Portable paid-expiry/refusal and retained payment/slot/right predicates. |
| `test_transfer_stale_presentations` | Portable transfer then both stale admission presentations. |
| `test_expired_authorization_replacement` | Portable expiry, explicit replacement, immutable replay and single consumption. |
| `test_complete_output_bytes_and_references` | Every receipt field, exact refusal and ordered body reference. |
| `test_published_schemas_and_unbound_reads` | Existing published bodies only, source mappings, no read binding. |
| `test_output_mutations_fail_comparison` | Nested changes, added/removed fields, boolean/null and refusal-code drift. |
| `test_order_and_mapping_mutations_fail` | Missing, duplicate or reordered input/output steps/cases and corrupted references/actions/IDs. |
| `test_pins_fail_before_execution` | Missing/duplicate/reordered pins, corrupted SHA/blob and byte drift for all 27 pinned inputs before replay. |
| `test_strict_serialization` | Malformed JSON, duplicate keys, non-finite numbers, noncanonical encoding and trailing bytes. |

The tests add consumer evidence for the documented gaps; they do not replace
existing behavioral coverage with duplicate feature implementations.
The existing workflow discovery guard reaches all 65 BRA test modules,
including this new module, through the unchanged reference-suite command.

See [the per-command evidence table](COMMANDS.md) and [machine-readable
command records](commands.jsonl) for exact commands, actual outcomes and full
logs, including the initial index failure. [Changed paths](changed-paths.txt)
is the complete file list, including every validation artifact.

Final preservation is recorded in `preservation-final.log`: all 443 protected
tracked inputs and all three new pinned artifacts match, both kernel blobs
match, HEAD and cached origin/main still equal the starting SHA, and no
untracked protected-tree additions exist. `locked-blobs-final.log` is an
independent direct Git-blob check. There is no merge commit or post-merge CI.

Implementation is ready for supervisor handoff with local acceptance checks
passed. A2 non-author exact-head review, supervisor commit/publication and both
exact-head CI workflows remain pending. Follow-up candidates are the already
queued SDK-example and adversarial-corpus nodes; neither was executed here.
There are no new unresolved implementation decisions within this node.
