# Offline provider-fact normalization harness — 2026-10-28

Builder-authored local evidence for node `plan-plan-provider-fact-normalization-offline`.
Task input: supplied node/design prompt; issue: none; no task document under `docs/tasks/`.
Depends on: `k1-adapter-event-identity`, `plan-plan-adapter-identity-evidence-map`,
`plan-plan-toss-card-profile-evidence-map`. This record is not independent A2
review, acceptance, merge readiness or a grade change.

Observed local `origin/main`, task base and unchanged branch HEAD:
`f13b2f8da720bb081195507bcc6936d39b94a640` on
`agent/kix-plan-plan-provider-fact-normalization-offline` (no local delta).
The supervisor forbids network/GitHub actions, overriding AGENTS §1 fetch;
remote freshness is unverified. Implementation is an uncommitted worktree patch;
final committed implementation/task head, KTX/KIX exact-head CI run IDs/status/conclusions,
non-author A2 review, merge SHA and post-merge CI are unavailable/not performed.
The supervisor owns Git/GitHub delivery. No commit, push, PR, issue or comment was made.

Scope: a dependency-free offline reference module `reference/provider_facts/`
plus a seeded `unittest` corpus that operates only on synthetic recorded
payment documents — never on live Toss responses and with no network —
implementing the contract-defined, decision-free parts of
[ADAPTER_EVENT_IDENTITY](../../docs/contracts/ADAPTER_EVENT_IDENTITY.md) draft 0.1
and [PG_TOSS_CARD_PROFILE](../../docs/contracts/PG_TOSS_CARD_PROFILE.md) §4/§6/§7:

- five-field `PaymentRef` tuple (provider, account/MID, environment,
  paymentKey, orderId) as payment identity, never an event ID;
- integer-KRW JSON parsing that never takes an f64 path (`parse_float`
  raises `FLOAT_TOKEN`) and rejects out-of-scale/sign/range amounts
  (`AMOUNT_SCALE`/`AMOUNT_SIGN`/`AMOUNT_RANGE`); the ceiling `KRW_U128_MAX`
  is the locked kernel's u128 bound, not a product policy value;
- raw timestamp text preservation; an offset-less `createdAt` is recorded
  `AMBIGUOUS_UNRESOLVED` and never assigned a zone; occurrence and receipt
  times stay separate and receipt stays out of the per-item fact;
- normalize-only-verified-facts: `timeout`/`not-found`/unsupported
  method/currency, an unverified-signal document and a binding-mismatched
  payment all stay terminal `Unresolved` without inferring absence; a
  cancel is a separate item and never erases the original payment item;
- `evidence_hash` = SHA-256 hexdigest of the canonical JSON of each item's
  normalized fact, independent per item;
- one Payment plus `cancels[]` is one `NormalizedPaymentHistory` of many
  items under one `PaymentRef`, never a batch of independent payments;
- at-most-one operation→payment binding: the same `OperationRef` with a
  different `paymentKey` becomes a `BindingConflict` on the store's review
  list — no new operation binding, no new order, no new capture.

Not implemented (stays with owners): `EventItemId` derivation or alias,
`ProviderFactKey` choice, domain/schema ids, transmission-identity
invariance (TM04), durable binding table (`k-stage5-durable-tx`), adapter,
inbox, lookup client, webhook signature, any policy value, any new kernel
command/enum, any Rust change. The module self-labels
`MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY`; all Python evidence in the maps is an
analog, NOT Toss.

Coverage before adding tests (AGENTS §7):

| Requirement | Existing evidence | Classification before / added assertion |
|---|---|---|
| PaymentRef five-field tuple | `reference/booking_resale_admission/mock_gates.py::observe_payment_fact` (untyped hex32) | Partial analog only. New `test_payment_ref.py::test_payment_ref_is_the_five_field_tuple` exercises the tuple, field validation and item-sharing. |
| S7-INTEGER-KRW | `runtime/crates/kix-kernel/tests/transitions.rs::u128_max_is_not_narrowed` | Partial (kernel bound only). New `test_integer_krw.py::test_integer_krw_rejects_float_scale_sign_and_range_paths` adds the offline JSON parse path. |
| S7-TIMEZONE | none | Not covered. New `test_timestamps.py::test_ambiguous_timezone_stays_unresolved_and_raw_text_is_preserved`. |
| S4-NORMALIZE | none | Not covered. New `test_normalize_verified_only.py::test_timeout_not_found_and_unsupported_stay_unresolved` and `::test_cancel_does_not_erase_the_original_payment_item`. |
| S4-EVIDENCE-HASH | `reference/booking_resale_admission/mock_gates.py::_canonical` (replay-compare string only) | Partial analog. New `test_evidence_hash.py::test_evidence_hash_is_sha256_of_canonical_normalized_fact`. |
| S6-ONE-PAYMENT | none | Not covered. New `test_one_payment_history.py::test_cancels_are_items_of_one_payment_not_a_batch`. |
| RULE-OP-BIND-CONFLICT | mock/fsm conflict error codes | Partial analogs. New `test_operation_binding.py::test_same_operation_different_payment_key_is_review_conflict_without_new_capture`. |

Map edits: `PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md` rows S4-NORMALIZE,
S6-ONE-PAYMENT, S7-TIMEZONE move NOT_COVERED→PARTIAL and S7-INTEGER-KRW
gains the offline citation (Counts now `rows=41 COVERED=5 PARTIAL=13
NOT_COVERED=12 OPEN=11`); clauses carry the required `Analog, NOT Toss`
label; `scripts/check_toss_card_profile_evidence_map.py` gains
`provider_facts` in the Python path alternation and drops `S4-NORMALIZE`
from `PROVIDER_ROWS` so the row may carry offline analog coverage — the
analog label rule, `MUST_BE_OPEN` and the remaining provider rows are
unchanged, and `S2-LOOKUP` remains the provider-row negative control.
`ADAPTER_IDENTITY_EVIDENCE_MAP.md` rows PaymentRef, 결제 → 이벤트 항목,
operation → 결제, RULE-OP-BIND-CONFLICT and S4-EVIDENCE-HASH gain mock
citations and rewritten missing cells; every status stays PARTIAL and the
counts line is unchanged; `scripts/check_adapter_identity_map.py` gains
`provider_facts` in the mock path alternation. `EVIDENCE_MAP_ROLLUP.md`
copies the new PG Counts verbatim. `protocol.yml` adds `provider_facts` to
the offline reference suite list — wiring the new suite the discovery
guard demands, not silencing a failure. Every UNDETERMINED cell and every
owner cell is byte-identical to the base.

Class A only: every exercised behavior is contract-defined; no class B
characterization is recorded and no class C contract violation was found.

Changed paths (complete):

- `reference/provider_facts/provider_facts.py`
- `reference/provider_facts/synthetic_documents.py`
- `reference/provider_facts/test_payment_ref.py`
- `reference/provider_facts/test_integer_krw.py`
- `reference/provider_facts/test_timestamps.py`
- `reference/provider_facts/test_normalize_verified_only.py`
- `reference/provider_facts/test_evidence_hash.py`
- `reference/provider_facts/test_one_payment_history.py`
- `reference/provider_facts/test_operation_binding.py`
- `docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md`
- `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md`
- `docs/status/EVIDENCE_MAP_ROLLUP.md`
- `scripts/check_toss_card_profile_evidence_map.py`
- `scripts/check_adapter_identity_map.py`
- `.github/workflows/protocol.yml`
- `docs/README.md`
- `validation/2026-10-28-plan-provider-fact-normalization-offline/README.md`

Actual verification (all Python test/checker invocations used
`PYTHONDONTWRITEBYTECODE=1`; commands ran in the repository root):

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts -v` | PASS: Ran 8 tests in 0.001s; OK — all seven mapped symbols plus the second S4-NORMALIZE case. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS: Ran 196 tests; OK. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS: Ran 418 tests; OK. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS: Ran 148 tests; OK. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS: Ran 85 tests; OK. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS: Ran 168 tests; OK. |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | PASS: Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK. |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS: 3 positive controls and 77 negative fixtures OK (memory only). |
| `python3 scripts/check_adapter_identity_map.py` | PASS: rows=17 expected=17 citations=66 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS: self-test: pass. |
| `python3 scripts/check_evidence_map_rollup.py` | PASS: evidence map roll-up ok: contracts=25; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | PASS: self-test: pass (16 negative controls). |
| `python3 scripts/check_ci_test_discovery.py` | PASS: ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3; `reference/provider_facts files=7` reached by the workflow step. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS: self-test: pass (18 negative controls). |
| `python3 scripts/check_docs_index.py` | PASS: docs index ok: scanned=302 indexed=267 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | PASS: self-test: pass. |
| `python3 scripts/check_ci_checker_wiring.py` | PASS: ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS: self-test: pass (13 negative controls). |
| `python3 scripts/check_class_b_index.py` | PASS: class B index ok: rows=216 sources=71 symbols=39; textual index only. |
| `python3 scripts/check_class_b_index.py --self-test` | PASS: self-test: pass (20 negative controls). |
| Full stdlib offline-checks block (`protocol.yml` lines 213–275, all 63 invocations verbatim) | PASS: all 63, exit 0 — every evidence-map checker, wiring, discovery, index, loopback/cargo/stage5 host self-tests. |
| `python3 scripts/check_openapi_contract.py` / `--self-test` | PASS: openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e; self-test: pass. |
| `python3 scripts/check_integration_gate_openapi.py` / `--self-test` | PASS: integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false; self-test: pass. |
| `python3 -m unittest integration_gate.test_offline_limits` | PASS: Ran 9 tests; OK (includes the socket guard). |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: `69564b166f0c27f9af5d8422f0a466b18d74c20f` / `b607996c83a119c349f1cc90469ac1ba82764e20`, both match. |
| `git rev-parse HEAD origin/main` | Both `f13b2f8da720bb081195507bcc6936d39b94a640`. |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` (protected tree untouched). |
| `git status --porcelain` | Only the changed paths listed above; no `runtime/`, `reference/v0.3-rc1/`, `.aiops/`, `docs/tasks/` or `docs/contracts/` path touched. |
| `git diff --check` | PASS, exit 0. |
| Map-row preservation diff (scripted row/cell compare vs HEAD) | PASS: PG map changes exactly the four named rows plus the vocabulary sentence and Counts line; adapter map changes exactly the five named rows; every owner cell and every other row byte-identical, all UNDETERMINED cells verbatim. |

`ktx-kernel.yml` equivalent for touched paths: none applicable — no Rust
change; the blob check above plus an unchanged `runtime/` status covers it.
Python 3.13.5 differs from the workflow's 3.12, so this is local evidence.
Checker success proves citation integrity and self-test sensitivity, not
that cited assertions establish provider semantics.

Remaining uncertainty / explicit non-claims:

- All fixtures are synthetic recorded documents; nothing about actual Toss
  behavior, field stability, signature scope, retention, exactly-once,
  durability, chain finality or production readiness is claimed.
- `source` labels are fixture preconditions, not a verification mechanism;
  no authenticated lookup exists.
- `AMBIGUOUS_UNRESOLVED` records non-assignment of a zone; it is not a
  timezone answer, and no apply-time/kernel clock is modeled.
- `BindingConflict`/`review`/`recorded_captures` are fixture evidence of
  the routing rule, not the durable §6.2 record (Track K stage5) and not a
  kernel command surface.
- `KRW_U128_MAX` is cited as the locked kernel's existing u128 bound, not
  chosen here as a product limit; zero-amount acceptance is a fixture
  characterization, not a policy.
- No EventItemId, alias, ProviderFactKey, domain/schema id, TransmissionId
  invariance, inbox, adapter, credential, endpoint, funds or real
  paymentKey/MID/orderId is created or selected.

Deviations: no fetch because the supervisor explicitly forbids network
actions; no Git/GitHub publication or exact-head CI in this builder
session. The supplied design's file set, test symbols and map edits were
followed; `BINDING_MISMATCH` was added as one extra terminal `Unresolved`
reason for a lookup document that names a different payment, and the
payment item's recorded status text is preserved verbatim (a DONE→CANCELED
snapshot produces a different normalized fact, matching the contract's
new-item rule). No scope expansion or decision-required resource was
needed.

Local builder delivery: READY. Supervisor commit/exact-head CI, non-author
A2 review and authorized merge remain separate. No merge-ready claim is
made.
