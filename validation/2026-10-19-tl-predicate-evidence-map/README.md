# TL predicate evidence map validation record

Builder-authored record for node `plan-tl-predicate-evidence-map`.
This file is not an independent review and not an acceptance.

## Task

Add `docs/status/TL_PREDICATE_EVIDENCE_MAP.md` and `scripts/check_tl_predicate_evidence_map.py` (with `--self-test`), wire the checker into `.github/workflows/protocol.yml`, and index the result from `docs/README.md`.

## Base

- `origin/main` and branch HEAD: `fe1f8666c4e50f7740bfe48641d3015fb66ef7fc` (observed after `git fetch origin main`).
- Locked blobs before and after work:
  - `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

## Commands and results

### Narrow tests and new checker

| Command | Result |
|---|---|
| `python3 scripts/check_tl_predicate_evidence_map.py` | `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7` (exit 0) |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | all 10 mutation cases detected, `self-test: pass` (exit 0) |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | `Ran 61 tests ... OK` (exit 0) |
| `python3 scripts/check_docs_index.py` | `docs index ok: scanned=167 indexed=132 allowlisted=35` (exit 0) |
| `python3 scripts/check_docs_index.py --self-test` | all 7 cases detected, `self-test: pass` (exit 0) |
| `python3 scripts/check_status_register.py` | `capability register ok: paths=249 ev_ids=15 original32=32` (exit 0) |
| `python3 scripts/check_status_register.py --self-test` | 4 cases detected, `self-test: pass` (exit 0) |

### Stdlib offline document checks (full set from `protocol.yml`)

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` | pass |
| `python3 scripts/check_status_register.py --self-test` | pass |
| `python3 scripts/check_rs_profile_traceability.py` | pass |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | pass |
| `python3 scripts/check_read_model_source_map.py` | pass |
| `python3 scripts/check_read_model_source_map.py --self-test` | pass |
| `python3 scripts/check_docs_index.py` | pass |
| `python3 scripts/check_docs_index.py --self-test` | pass |
| `python3 scripts/check_i12_proof_ids.py` | pass |
| `python3 scripts/check_i12_proof_ids.py --self-test` | pass |
| `python3 scripts/check_delegation_layer_matrix.py` | pass |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | pass |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | pass |
| `python3 scripts/check_rs_im_evidence_map.py` | pass |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | pass |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | pass |
| `python3 scripts/check_contract_error_codes.py` | pass |
| `python3 scripts/check_contract_error_codes.py --self-test` | pass |

### Closest local CI equivalents for the touched paths

| Command | Result |
|---|---|
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite"; done` | settlement 48 OK, booking 75 OK, credit 48 OK, ai_delegation 70 OK, token_reward 61 OK (exit 0) |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK` (exit 0) |
| `python3 scripts/test_runtime_architecture.py` | `Ran 7 tests ... OK` (exit 0) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | no output, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | all workspace tests passed (exit 0) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | no warnings, exit 0 |

## Changed paths

- `docs/status/TL_PREDICATE_EVIDENCE_MAP.md` — new 49-row evidence map, self-checked.
- `scripts/check_tl_predicate_evidence_map.py` — new stdlib-only checker with `--self-test`.
- `docs/README.md` — one added index line for the validation record and map.
- `.github/workflows/protocol.yml` — two added checker command lines in `Stdlib offline document checks`.
- `validation/2026-10-19-tl-predicate-evidence-map/README.md` — this record.

## Lock and protected-area checks

| Command | Result |
|---|---|
| `git hash-object runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `git hash-object runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --exit-code -- reference/v0.3-rc1` | unchanged (exit 0) |
| `git diff --exit-code -- reference/token_reward docs/contracts docs/decisions docs/tasks .aiops` | unchanged (exit 0) |

## Disagreements with TL-4 record listed, not corrected

- TL-4 §5 says only `reference/v0.3-rc1/sui/Move.toml` existed as the locked manifest. The current boundary test (`test_TL4_TK02_T1_only_the_authorized_move_manifests_exist`) expects both `reference/v0.3-rc1/sui/Move.toml` and `reference/rights_scale/sui/Move.toml`. The map treats the record's manifest count as stale; the record and capability register were not edited.
- TL-4 §5 labels TK-10 as `REVIEWED (gate records)` and TK-11 as `REVIEWED (wording)`. The map keeps `REVIEWED_RECORD` but notes these are builder-side reviews, not an independent PASS.
- TL-4 §5 labels TK-9 as a name scan. The map keeps it as `PARTIAL` because a name scan is not a proof that a gas-payment path is absent.

## Non-claims

- No independent verification of TK-1..TK-9; the blueprint TL-4 acceptance line remains open.
- No package, testnet, mainnet, real funds, real PG/bank/KYC call, storage engine, R2/replication/consensus, new coin/TIX module, product policy value, or new protocol command.
- No claim of operational readiness, legal compliance, investment return, liquidity, or price-keeping.
- Operational count stays 0.
