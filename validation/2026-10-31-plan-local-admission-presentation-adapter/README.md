# Local admission presentation adapter — builder evidence

Node/task ID: `plan-local-admission-presentation-adapter`, 2026-10-31.
Task document: supervisor-provided node specification and read-only design in
this session; no node issue or current node document under `docs/tasks/` exists.
The node is not in `.aiops/program.json`. This is not ASTRA program mode.
The existing §11 admission implementation and contract establish the local
dependency on booking-resale-admission-deepening; remote completion is unverified.

Branch: `agent/kix-plan-local-admission-presentation-adapter`. Cached
`origin/main`, task base, initial HEAD and current HEAD are
`c302bc296282d2f89df58b490732533e7a9bc1e9`. No local base delta. Remote freshness
is unverified: the supervisor forbids network actions, superseding AGENTS.md §1's
fetch. No commit, push, GitHub action, issue, comment or background job was run.
Implementation/final task commit SHA: not yet created (uncommitted delivery).
Merge SHA and post-merge checks: not applicable. Supervisor owns publication.

Complete changed-path list:

- `reference/booking_resale_admission/presentation_source.py`
- `reference/booking_resale_admission/fake_presentation_source.py`
- `reference/booking_resale_admission/presentation_adapter.py`
- `reference/booking_resale_admission/example_presentation_adapter.py`
- `reference/booking_resale_admission/test_presentation_source.py`
- `reference/booking_resale_admission/test_presentation_adapter.py`
- `reference/booking_resale_admission/README.md`
- `docs/README.md`
- `validation/2026-10-31-plan-local-admission-presentation-adapter/README.md`

The [module README](../../reference/booking_resale_admission/README.md) records
the existing coverage mapping made before adding tests. FSM consumption/replay,
transfer/listing/expiry, settlement/external-source refusals and false flags
were sufficiently covered at the FSM layer and partially covered overall.
Presentation source isolation and pre-delegation behavior had no coverage.
New tests fill these source/adapter gaps with exact forwarding and receipt/error
identity, direct-FSM parity, accepted/rejected replay and key conflicts, one
fetch for each explicit invocation, no retry/fallback/cache, separate calls,
stale holder/version/transfer/listing/expiry refusals, configured-source checks,
recording isolation and malformed-input rejection. Zero-call spies and paired
same-key real-machine acceptance prove boundary rejections do not bind keys;
state digests alone would not prove that. The runnable example uses actual local
reservation, resale, settlement and admission instances with synthetic values.

Verification commands/results are recorded below. Python uses
`PYTHONDONTWRITEBYTECODE=1`; selected tests use
`PYTHONPATH="$PWD/reference/booking_resale_admission"`; Cargo runs offline.
Default Python is 3.13.5. After discovering that `protocol.yml` pins 3.12, the
new tests, selected regressions and example were also run with installed Python
3.12.15. Rust and Cargo are 1.98.1, matching both workflows. No installation or
network access occurred. Temporary raw checker/runtime logs are under
`/tmp/kix-presentation-*`; they are not committed evidence.

| Command actually run | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD origin/main` | Initially clean, expected branch; both SHAs as above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | Required blobs match, see below. |
| `git rev-parse HEAD:reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `python3 -m unittest test_presentation_source test_presentation_adapter` | Initial run: 18 tests, one test-fixture failure: reused rejected key returned the FSM's correct `IDEMPOTENCY_CONFLICT` before the intended `NOT_HOLDER` case. Separated case keys; second run: 19 tests PASS. No FSM change. |
| `python3 reference/booking_resale_admission/example_presentation_adapter.py > /tmp/kix-presentation-example.json` plus JSON inspection | PASS; ADMISSION_AUTHORIZED before explicit consume, CONSUMED_ONCE, replay version 2, three fetches. |
| Selected socket-free admission command below | PASS, 104 tests. |
| `python3 --version`; `python3.12 --version`; `rustc --version`; `cargo --version`; `rustup toolchain list` | Python 3.13.5 / 3.12.15; Rust/Cargo 1.98.1, active default toolchain. |
| `python3.12 -m unittest test_presentation_source test_presentation_adapter` | PASS, 19 tests on the CI Python minor version. |
| Selected socket-free admission command below, replacing `python3` with `python3.12` | PASS, 104 tests. |
| `python3.12 reference/booking_resale_admission/example_presentation_adapter.py > /tmp/kix-presentation-example-312.json` | PASS, exit 0. |
| `python3 scripts/check_docs_index.py` and `--self-test` | PASS; 324 scanned, 289 indexed, 35 allowlisted. |
| `python3 scripts/check_bra_evidence_map.py` and `--self-test` | PASS; 39 rows/headings, 219 citations; 50 negative controls. |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | PASS; all 199 rows covered. |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | PASS; 35 scripts, 13 negative controls. |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | PASS; booking/resale/admission reaches 19 test files through existing directory discovery, including both new modules; 18 negative controls. |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | PASS; 84 commands, pin unchanged. |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | PASS; 84 commands, productionEndpoint=false/publicHost=false. |
| `python3 scripts/verify_runtime_architecture.py` | PASS; declaration/dependency gate only. |
| `python3 scripts/test_runtime_architecture.py` | PASS, 7 tests. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | PASS, exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | PASS, exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | PASS, exit 0. |
| `git diff --exit-code HEAD --` protected and out-of-scope paths listed below | PASS, no tracked changes. |
| Python read-only probe: NUL-delimited `git ls-tree -rz HEAD -- reference/v0.3-rc1`, `git hash-object --` for each file and both locks, compare all historical working-tree paths, `git rev-parse HEAD` | PASS; both locked blobs and all 108 historical files byte-identical, no added historical files, HEAD unchanged. |
| `git diff --check` | PASS. |

The out-of-scope diff command checked the two locked kernel files,
`reference/v0.3-rc1`, `.aiops`, `docs/tasks`, `docs/contracts`,
`.github/workflows`, the four booking/resale/admission FSM/gate implementations,
`test_admission_fsm.py`, `sdk` and `integration_gate`.
A diagnostic `rg 'test_presentation'` against the discovery log returned no match
(exit 1): that checker prints suite counts rather than individual Python file
names. Inspection confirmed `reference/booking_resale_admission files=19` and
the checker derives both new modules from `test_*.py`; the checker itself passed.

Selected existing regressions actually run:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission"
A=test_admission_fsm.AdmissionFsmTests
python3 -m unittest \
  "$A.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version" \
  "$A.test_transfer_then_entry_rejects_both_presentations" \
  "$A.test_listing_and_cancel_order_against_entry" \
  "$A.test_expired_authorization_is_replaced_once" \
  "$A.test_external_sources_fail_closed_without_being_read" \
  "$A.test_settlement_commit_is_not_entry_and_a_granted_flag_rejects" \
  "$A.test_restart_replays_journal_and_retry_is_duplicate" \
  test_admission_rejection_atomicity test_returned_data_isolation test_open_items
```

Both protected Git blobs matched before and after implementation:

| Path | Required and actual Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

No explicit contract violation found. Existing class-B clock-skew and
post-mutation fault characterizations remain unchanged; boundary rejection is
not a general cross-machine atomicity claim. No new lifecycle semantics or
production policy was invented. Production timing, venue identity, revocation
and independent currentness remain **UNDETERMINED**, with Astra/User and existing
contract owners. Retained mock flags are not evidence of external properties.

Design deviations: reject non-JSON NaN/Infinity constants as malformed too.
Procedural deviations: supervisor-required omitted fetch and uncommitted local
delivery; local verification additionally included workspace Rust tests/Clippy
from `protocol.yml`, beyond the design's kernel-only commands. No full local
suite claim: the HTTP suite is unchanged and must run
through normal exact-final-head CI. No FSM, contract, catalogue, HTTP, SDK,
workflow, `.aiops/`, task input, runtime or historical-reference changes.

| Required evidence | Run ID | Status / conclusion |
|---|---|---|
| Non-author exact-head review / A2 | Not available | Pending supervisor orchestration; builder tests are not review. |
| Exact-final-head KTX kernel verification | Not available | Not run/queried; final implementation commit not yet created. |
| Exact-final-head KIX protocol verification | Not available | Not run/queried; final implementation commit not yet created. |
| Post-merge main CI | Not applicable | No merge. |

No real services/funds, secrets, public endpoints, Sui networks, persistence,
storage engines, production runtime or activation were used. No production
durability, distributed fencing, venue/bank exactly-once, legal compliance,
chain finality or overall production-readiness claim. Remaining work: supervisor
publication, non-author exact-final-head review/A2 and completed/success KTX/KIX
checks, including unchanged HTTP coverage. No merge readiness or authorization
is implied by this local builder handoff.
