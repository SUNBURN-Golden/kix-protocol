# Offline integration-gate gap closure — 2026-10-28

Builder-authored local evidence for node `plan-plan-integration-gate-offline-gap-closur`.
Task input: supplied node/design prompt; issue: none; no task document under `docs/tasks/`.
This record is not independent A2 review, acceptance, merge readiness or a grade change.

Observed local `origin/main`, task base and unchanged branch HEAD:
`048b17dc3c586a17aaf3ef66f5f773513979041c` on
`agent/kix-plan-plan-integration-gate-offline-gap-closur` (no local delta).
The supervisor forbids network/GitHub actions, overriding AGENTS §1 fetch;
remote freshness is unverified. Implementation is an uncommitted worktree patch;
final committed implementation/task head, KTX/KIX exact-head CI run IDs/status/conclusions,
non-author A2 review, merge SHA and post-merge CI are unavailable/not performed.
The supervisor owns Git/GitHub delivery. No commit, push, PR, issue or comment was made.

Coverage before adding tests:

| Requirement | Existing evidence | Classification before / added gap assertion |
|---|---|---|
| G-OPENAPI-NO-CORS-CHANGE | `scripts/check_openapi_contract.py::validate`, `::self_test`; `integration_gate/openapi_doc.py::validate` | PARTIAL: transport/auth fields refused, current bytes unpinned. New `OfflineGapTests.test_gate_openapi_rendered_bytes_are_pinned` pins committed/rendered bytes including newline; `test_browser_origin_is_transport_only_statically` checks CLI/startup/Host/origin/preflight/header flow and document isolation. |
| G-SAME-PROCESS-REPLAY | `integration_gate/test_http_gate.py::TransportTests.test_representative_commands_match_local_call`, `::test_http_idempotency_key_header_is_not_consulted` | PARTIAL: body-change conflict/replay covered. New `test_core_actor_only_conflict_preserves_receipt` and `test_core_action_only_conflict_preserves_receipt` isolate each changed fingerprint field, require exact OPERATION_ID_CONFLICT, complete original receipt/snapshot equality before/after, and successful fresh-ID alternate controls. |
| K-WIRE-NAMES | `integration_gate/test_http_gate.py::TransportTests.test_admission_happy_path_over_http`, `::test_unsupported_paths_methods_and_actions` | PARTIAL: prefixed journey and consume_admission rejection exist. New `test_unprefixed_admission_names_are_not_dispatchable` excludes both unprefixed names across commands/names/fsm_commands/fsm_name_set, checks prefixed machine/op mappings and host lookup rejection. |
| No sockets / CI reachability | `OfflineLimitsTests.test_socket_guard_is_active`; protocol.yml offline reference step | Sufficient existing guard/discovery wiring retained; imports occur after module guard installation. No workflow change. |
| Citation integrity | Existing map checker qualified-symbol checks | New REQUIRED_OFFLINE_CITES plus per-citation deletion, fabrication and method-removal controls; no source files mutated by negative fixtures. |

The map stays `rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1`. Only the three
rows' Tests/Gap cells change. All statuses, owners, other rows and the seeded-journey
host stop remain unchanged. Gap text is copied verbatim from the supplied design.

OpenAPI SHA-256 (committed and rendered):
`d05beb48c234b924af086b886ce9bb524dc34407ad2e4a57f1e8af84255820f6`.
No OpenAPI artifact was regenerated. Static AST assertions characterize the current
source boundary; two in-memory negative fixtures inject a document configuration
dependency and a CORS-conditioned payload mutation. They are sensitivity evidence,
not a general information-flow proof. Browser opt-in also controls existing Host
checks and preflight. There is no OpenAPI-serving route to test.

Class A: observed bounded byte derivation, fingerprint conflict/replay and catalogue
exclusions match the cited contract. Class B: direct FsmHost.call of either excluded
name raises KeyError with `(name,)` before body access; the exception type is an
implementation characterization, not an HTTP error contract. Owner of remaining
HTTP assertion gaps: integration_gate maintainer. No class C contract violation found.

Verification commands/results and final preservation evidence are recorded below.

Changed paths (complete):

- `integration_gate/test_offline_limits.py`
- `scripts/check_integration_gate_contract_evidence_map.py`
- `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-28-plan-integration-gate-offline-gap-closur/README.md`

Actual verification (all Python test/checker invocations used
`PYTHONDONTWRITEBYTECODE=1`; commands ran in the repository root):

| Command | Actual result |
|---|---|
| `python3 -m unittest integration_gate.test_offline_limits.OfflineGapTests -v` (initial) | FAIL: 4 passed, 1 failed; the AST helper mistakenly forbade legitimate CLI sys.argv use in document main. Fixed the test helper to allow CLI entry while keeping build/render isolated; no application change. |
| `python3 -m unittest integration_gate.test_offline_limits.OfflineGapTests -v` (after fix and final AST tightening) | PASS: 5 tests; both in-memory negative fixtures rejected. |
| `python3 -m unittest integration_gate.test_offline_limits -v` | PASS: 9 tests including the socket guard; passed after helper correction and again after final AST tightening. |
| `python3 scripts/check_openapi_contract.py` | PASS: openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS: self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | PASS: integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS: self-test: pass |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | PASS: integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS: self-test: pass (100 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_ci_test_discovery.py` | PASS: ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS: self-test: pass (18 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS: ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS: self-test: pass (13 negative controls) |
| `python3 scripts/check_docs_index.py` | PASS: docs index ok: scanned=301 indexed=266 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS: self-test: pass |
| `python3 scripts/check_evidence_map_rollup.py` | PASS: evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | PASS: self-test: pass (16 negative controls) |
| `python3 scripts/check_class_b_index.py` | PASS: class B index ok: rows=216 sources=71 symbols=39; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | PASS: self-test: pass (20 negative controls) |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: Ran 196 tests in 1.934s; OK |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS: Ran 418 tests in 8.909s; OK |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS: Ran 148 tests in 6.567s; OK |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS: Ran 85 tests in 2.827s; OK |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS: Ran 168 tests in 1.819s; OK |
| `python3 scripts/verify_runtime_architecture.py` | PASS: architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS: 7 tests. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS: 127 tests (34 contract edges, 5 contract invariants, 12 E4, 11 observation slots, 25 performance harness, 8 quarantine, 32 transitions); 0 unit/doc tests. No performance benchmark run. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `sha256sum docs/contracts/openapi/kix-protocol.integration-gate.openapi.json` | PASS: d05beb48c234b924af086b886ce9bb524dc34407ad2e4a57f1e8af84255820f6, matching the supplied pin. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: 69564b166f0c27f9af5d8422f0a466b18d74c20f / b607996c83a119c349f1cc90469ac1ba82764e20, both match. |
| `git rev-parse HEAD origin/main` | Both 048b17dc3c586a17aaf3ef66f5f773513979041c. |
| `git rev-parse HEAD:reference/v0.3-rc1` | a6ecb124dc2b2267ca6be19e39fbe2aef143074b (initial protected tree). |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 .aiops docs/tasks .github/workflows integration_gate/server.py integration_gate/openapi_doc.py docs/contracts` | PASS: no differences, exit 0. |
| `python3 /tmp/kix-gap-verify-preservation.py` (source below) | PASS: all 148 protected tracked files match HEAD bytes; exactly three map rows change, only Tests/Gap cells, all statuses/owners preserved. |
| `git diff --check` | PASS, exit 0. |
| `python3 --version`; `rustc --version`; `cargo --version` | Python 3.13.5; rustc 1.98.1 (48a229cea 2026-09-01); cargo 1.98.1 (797e8a9bc 2026-08-05). |

The two map-checker invocations also passed immediately after citation edits;
its final self-test has 100 negative controls, including 15 new per-citation
controls (deletion, fabrication and removal of the cited method). Checker
success proves citation integrity, not that the cited assertions establish semantics.
Protocol CI already reaches the module via
`python3 -m unittest integration_gate.test_offline_limits`; the discovery and
wiring guards pass without workflow edits. The inspected KTX workflow commands
were run using installed Rust 1.98.1 and cached dependencies with `--offline`.
The protocol offline reference step's five suites and four OpenAPI invocations
were run. Python differs from the workflow's 3.12, so this is local evidence.
No Rust code changed; no full workspace, Move, ZK or Node run was needed for the
touched paths. No socket-opening HTTP/readiness suite or host preflight ran.

Preservation comparison source (temporary local script; not a repository output):

```python
from pathlib import Path
import hashlib
import subprocess

protected = ['runtime/crates/kix-kernel/src/lib.rs',
             'runtime/crates/kix-kernel/tests/quarantine_capacity.rs',
             'reference/v0.3-rc1', '.aiops', 'docs/tasks', '.github/workflows',
             'docs/contracts', 'integration_gate/server.py', 'integration_gate/openapi_doc.py']
paths = subprocess.check_output(['git', 'ls-files', '-z', '--', *protected]).decode().split('\0')
count = 0
for path in filter(None, paths):
    baseline = subprocess.check_output(['git', 'show', 'HEAD:' + path])
    assert Path(path).read_bytes() == baseline, path
    count += 1
print('Protected tracked files byte-identical to initial HEAD:', count)
for path in protected[:2]:
    data = Path(path).read_bytes()
    print(path, hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest())
map_path = 'docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md'
before = subprocess.check_output(['git', 'show', 'HEAD:' + map_path]).decode()
after = Path(map_path).read_text()
def rows(text):
    return {line.split('|')[1].strip(): [cell.strip() for cell in line.strip('|').split('|')]
            for line in text.splitlines() if line.startswith('|')}
a, b = rows(before), rows(after)
assert a.keys() == b.keys()
changed = {name for name in a if a[name] != b[name]}
assert changed == {'K-WIRE-NAMES', 'G-OPENAPI-NO-CORS-CHANGE', 'G-SAME-PROCESS-REPLAY'}
for name in a:
    if name in changed:
        assert [i for i in range(8) if a[name][i] != b[name][i]] == [3, 6], name
    else:
        assert a[name] == b[name], name
print('Map: exactly three target rows changed; Tests/Gap cells only; all statuses/owners preserved')
```

Preservation applies to locked files, `reference/v0.3-rc1/**`, `.aiops/`,
`docs/tasks/`, workflow files, contracts and gate implementation. No transient
mutation or regeneration of those files was performed. Final-merge lock checks
are not applicable: this session did not merge.

Remaining uncertainty / explicit non-claims:

- Historical pre-browser byte identity is not established by the current-artifact pin.
- Actor/action fingerprint variants are tested directly in Core, not across HTTP.
- HTTP rejection of unprefixed authorize_admission remains unasserted; lookup KeyError
  supplies no HTTP status/error semantics.
- Bound-listener default port/limit enforcement, publicHost response assertions,
  seeded FSM journeys and worker ordering remain with their existing map owners.
  The seeded-journey host stop remains open.
- Authentication, retry/transport guarantees and commerce binding remain unresolved;
  these synthetic tests assert no live adapter, funds, chain finality, distributed
  durability, external exactly-once, production conformance or production suitability.
- AST regression pins are source-informed and intentionally sensitive to structural
  changes. They are neither clean-room evidence nor an independent A2 audit.

Deviations: no fetch because the supervisor explicitly forbids network actions;
no Git/GitHub publication or exact-head CI in this builder session. The design's
five files, five new tests and verbatim gap text were followed. Added checker
negative controls for removal of the cited test method, plus class-B index plain
and self-test checks to validate the updated characterization text. No scope
expansion or decision-required resource was needed.

Local builder delivery: READY. Supervisor commit/exact-head CI, non-author A2
review and authorized merge remain separate. No merge-ready claim is made.
