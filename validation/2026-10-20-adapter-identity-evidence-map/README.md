# adapter-identity-evidence-map

Node: `plan-plan-adapter-identity-evidence-map`. Adds `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md`, one row per identity term, relation and rule of `docs/contracts/ADAPTER_EVENT_IDENTITY.md` draft 0.1 sections 2–4 (6 terms, 4 relations, 2 rules, 5 section-4 items — 17 rows), and `scripts/check_adapter_identity_map.py` (stdlib only, `--self-test`), wired into the unguarded `Stdlib offline document checks` step of `.github/workflows/protocol.yml` after the `check_contract_error_codes.py` lines.

Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792427921 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `b3f1c6c1f943dc5faccaa9451aee55fa7305dc4c`. `git fetch origin main` was not run (this session forbids network actions); the value is the local `origin/main` ref. Branch `agent/kix-plan-plan-adapter-identity-evidence-map`.

**This record and the map are a builder-authored reading, not an Astra review and not an acceptance. No grade is raised, the operational count stays 0, no adapter code, schema id or domain id is written, no Sui, ZK, localnet, Move or Node run was made, and no open input is resolved.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. The checker recomputes both blobs on every run. Nothing under `runtime/`, `reference/` (so `reference/v0.3-rc1/` too), `readiness/`, `integration_gate/`, `.aiops/`, `docs/tasks/`, `docs/contracts/` or `docs/decisions/` changed.

## What this change does

- The map has 17 rows: 2 `CARRIED`, 7 `PARTIAL`, 0 `NO_SURFACE`, 8 `UNDETERMINED`. Statuses are builder readings of the cited surfaces; Astra may reclassify.
- Each surface cell is `none`, one or more `path::symbol` citations, and/or `UNDETERMINED (owner: X)`. Every owner is written verbatim in the contract except the reserved literal `k-stage5-durable-tx`, whose record is not on this base and is named as text only — never a checked citation.
- Every cell that depends on an open input stays `UNDETERMINED` with its owner: `TM04` (provider key/transmission stability), `DECISION_REQUIRED · Astra` (EventItemId source, alias rule, domain/schema ids), `k-stage5-durable-tx` (durable alias/binding table). `I04` is a contract open input that no section 2–4 row's surface content depends on at this base.
- The contract's section 3 table lists four relations while the task text names three; all four are mapped.
- The checker verifies the contract-derived ids (section 2 terms, section 3 relations) plus the hardcoded rule/section-4 ids and their contract anchor strings, ten-cell row width, status-versus-cell consistency, citation path existence, column path prefixes (never under `reference/v0.3-rc1/`), symbol definitions (`def`/`class`/constant for Python, `fn`/`struct`/`enum`/`const`/`type` for Rust, exact text for the Toss profile), owner naming, the two locked blobs and the counts line. `--self-test` requires each deliberate break to be caught.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md` | New map, 17 rows. |
| `scripts/check_adapter_identity_map.py` | New checker, stdlib only. |
| `.github/workflows/protocol.yml` | Two added lines at the end of the stdlib step. |
| `docs/README.md` | One row in the 2026-10-20 section linking the map and this record. |
| `validation/2026-10-20-adapter-identity-evidence-map/README.md` | This record. |

## AGENTS.md section 7: existing coverage per row

| ID | Map status | Section 7 class | Missing |
|---|---|---|---|
| TransmissionId | `UNDETERMINED` | not covered | No executable surface stores a provider transmission id; re-delivery invariance is the TM04 question. |
| RawEvidenceRef | `PARTIAL` | partially covered | Kernel `CaptureObservation` carries `evidence_hash` only; no raw-byte custody store exists. |
| PaymentRef | `PARTIAL` | partially covered | The mock `payment_ref` is a bare hex32 bound to one order/listing; no five-field tuple exists. |
| ProviderFactKey | `UNDETERMINED` | not covered | No surface carries a per-item stable provider key; which field is stable is TM04's question. |
| EventItemId | `UNDETERMINED` | partially covered | Kernel consumes `event_id`/`EventKey`; the alias source (§4.5) and durable table are unadopted/unbuilt. |
| OperationRef | `PARTIAL` | partially covered | Kernel `ProviderOperation`, gate `operationId`, journal `operationId` exist; the §6.2 four-way binding does not. |
| 전송 → 이벤트 항목 | `UNDETERMINED` | partially covered | The kernel dedupe boundary exists; no surface carries the "many transmissions" side. |
| 결제 → 이벤트 항목 | `PARTIAL` | partially covered | Kernel per-key observations and mock one-fact-per-payment_ref exist; no item list under a payment. |
| operation → 결제 | `PARTIAL` | partially covered | Kernel/mock enforce one binding per order/listing; no PaymentRef exists to state it against. |
| operation → 주문 | `CARRIED` | sufficiently covered | none |
| RULE-OBSERVE-KEY | `CARRIED` | sufficiently covered | none |
| RULE-OP-BIND-CONFLICT | `PARTIAL` | partially covered | Analog conflict codes exist (kernel Conflict, mock PAYMENT_BINDING_CONFLICT, gate OPERATION_ID_CONFLICT); the adapter-side rule does not exist. |
| S4-DERIVATION | `UNDETERMINED` | not covered | No derivation exists; its source is undecided per §4.5. |
| S4-EVIDENCE-HASH | `PARTIAL` | partially covered | Kernel stores/compares `evidence_hash`; no surface computes a normalized-fact SHA-256. |
| S4-SOURCE | `UNDETERMINED` | not covered | §4.5 choice A blocked on TM04; choice B needs a "same item" rule. |
| S4-ALIAS | `UNDETERMINED` | not covered | Neither alias table nor truncation rule adopted; durable table is stage5's. |
| S4-DOMAIN-SCHEMA | `UNDETERMINED` | not covered | No id assignment; registry change is a separate contract decision. |

Totals: 2 sufficiently covered, 4 partially covered, 3+8 = the rest not covered at contract level (see rows).

## AGENTS.md section 8: discrepancies found

**A. Contract-defined and matching.** RULE-OBSERVE-KEY and operation → 주문: the kernel implements them as the contract writes them (builder reading; the checker proves only that cited names exist).

**B. Contract undefined (characterizations; nothing amended).**

1. The task text names "three cardinality relations"; the contract section 3 table has four rows. All four are mapped; the map does not choose between the readings.
2. `reference/booking_resale_admission/mock_gates.py` `_replay_payment` and `admission_fsm.py` raise `PAYMENT_BINDING_CONFLICT`/`IDEMPOTENCY_CONFLICT` against their own binding model, not the contract's OperationRef↔paymentKey rule; the map labels them analogs.
3. `I04` is an open input in the contract but no section 2–4 row's surface content depends on it at this base; it is named in the gap summary only.
4. The stage5 durable-table owner `k-stage5-durable-tx` names an unmerged branch record; it is a text owner, not a resolvable path on this base.

**C. Explicit contract violation:** none found.

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main` | Both `b3f1c6c1f943dc5faccaa9451aee55fa7305dc4c`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8`. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. Unmodified map passes; all 17 mutation cases and the injected locked-blob mutation detected; `self-test: pass`. |
| `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, each plain and `--self-test` | All exit 0. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Exit 0 after this record was added (before: one broken index link for this record). |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | `OK`. |
| `python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation` | Each `OK`. |
| `check_openapi_contract.py`, `check_integration_gate_openapi.py`, each plain and `--self-test` | All exit 0. |
| `python3 scripts/check_sdk_client.py` | **Not runnable in this session:** exits 1 with `node 20.19.2 does not match toolchains.json nodeMajor 24` — a pre-existing toolchain limitation, unrelated to the touched paths (`sdk/` unchanged). |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | Exit 0, `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`; tests `OK` (nothing under `runtime/` changed). |
| `cd runtime && cargo test --workspace --locked --offline`; `cargo clippy --workspace --all-targets --locked --offline -- -D warnings`; `cargo fmt --all -- --check` | All 41 test-result lines `ok`, no failures; clippy finished with no warnings; fmt check exit 0. (`--offline` because the session has no network.) |
| `git diff --stat origin/main -- reference/v0.3-rc1 runtime readiness integration_gate docs/contracts docs/decisions docs/tasks .aiops` | Empty — none of those paths changed. |
| Move (`sui move test`), localnet, ZK, Node jobs; exact-head KTX kernel verification and KIX protocol verification | **Not run.** No Sui binary or network use in this session, and there is no pushed head. |

## Non-claims

- Not an Astra review; the contract stays draft 0.1 and the capability register is unchanged (`CURRENT_CAPABILITY_REGISTER.md`'s checker list is a dated snapshot, explicitly not auto-synced — left for a register-sync node).
- No adapter, inbox, outbox, lookup client, binding store, schema/domain id, wire format or Rust trait is built or chosen; no open input (TM04, I04, §4.5 choices, domain/schema ids) is resolved.
- The checker confirms a cited name exists in a cited file. It does not run any cited test and does not prove a surface implements the contract rule; that is the reading recorded in the map.
- No claim of Toss behavior, signature scope, durability, exactly-once, provider finality or production readiness; nothing under `reference/v0.3-rc1/` is cited and both locked blobs are unchanged.
