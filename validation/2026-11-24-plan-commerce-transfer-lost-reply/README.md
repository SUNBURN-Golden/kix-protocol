# Commerce resale transfer lost-reply vectors

The supervisor's node specification and planner run `1795180531` are the
task input for `plan-commerce-transfer-lost-reply`. The node has no issue
or file under `docs/tasks/`. The starting branch
`agent/kix-plan-commerce-transfer-lost-reply` and cached `origin/main` both
resolved to `708a5e24d2cfd9cbd33219a7a6ced7816b09e742`.

## Coverage

| Requirement | Existing coverage | Paired replay evidence |
| --- | --- | --- |
| Exact market request and paid setup | Sufficient. `CommerceFixtureTupleTests.test_inventory_and_edges` checks ordered setup and `test_market_full_receipts` checks the complete market receipts. | Both fresh hosts use the same pinned setup and envelope. Setup ends at `market-pay`, with each setup receipt compared to the market golden. |
| Shared caller observation | Partial. `CommerceAdmissionLostReplyTests` covers two losses for admission. The resale transfer fault pair was uncovered. | Both cases match one caller record with the original `operationId` and body key, a null receipt, `UNKNOWN`, a single attempt, and zero follow-up calls. |
| Request dropped before dispatch | Partial. `test_market_full_receipts` covers the paid listing with buyer-1 at version 1. A transport drop at that point was uncovered. | Zero producer dispatches and no hidden receipt. The paid listing, buyer-1's right at version 1, canonical machine state, and all five journals match their pre-attempt values. |
| Receipt dropped after dispatch | Partial. `test_market_full_receipts`, `test_market_receipt_mutations`, and `test_vectors` cover the delivered receipt, drift detection, and expected journal delta. A withheld receipt was uncovered. | The single hidden receipt matches the pinned full market golden in canonical bytes. The right is held by buyer-2 at version 2. All journal prefixes are intact, with one resale append for `transfer-1` and `key-market-accept`. |
| Recovery lookup stays `NOT_BOUND` | Sufficient. The SDK grant lookup has an existing proposed recovery case. | The portable fixture carries the same verdict and the replay checks it against the existing grant selection fixture. |

[Paired fixture](../../reference/booking_resale_admission/fixtures/commerce_transfer_lost_reply_v1.json) ·
[Replay](../../reference/booking_resale_admission/test_commerce_transfer_lost_reply.py) ·
[Market receipt tests](../../reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py) ·
[Admission lost-reply tests](../../reference/booking_resale_admission/test_commerce_admission_lost_reply.py) ·
[SDK conformance](../../sdk/conformance/conformance.test.mjs)

## Local verification

Commands ran from the repository root. `bra` below is
`reference/booking_resale_admission`. Python was 3.12.15 and Node was
24.22.1. The SDK commands ran with `npm_config_offline=true`.

| Command | Result |
| --- | --- |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce_transfer_lost_reply.py' -v` | Exit 0. One paired test passed, covering both fault points. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce_admission_lost_reply.py' -v` | Exit 0. Two tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p 'test_commerce_fixture_tuple_conformance.py' -v` | Exit 0. Nine tests passed, including the market full receipts, receipt mutations and all first-acceptance resolutions. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,083 tests passed, including the existing local loopback admission test. |
| `python3.12 -B -` running the Python commands from `Stdlib offline document checks` in `.github/workflows/protocol.yml`, excluding the standalone loopback host report | All 68 invocations exited 0, including the document index, test discovery, and Commerce qualification and consumer binding checks. |
| `npm --prefix sdk run conformance` | Exit 0. All 21 tests passed, including the proposed recovery lookup verdict. |
| `npm --prefix sdk run verify-compat` | Exit 0. The `bootstrap-2` manifest verified. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The scoped Commerce manifest verified. |
| `python3.12 -B scripts/check_openapi_contract.py`, `python3.12 -B scripts/check_integration_gate_openapi.py`, and `python3.12 -B scripts/check_sdk_client.py`, each also run with `--self-test` | All six invocations exited 0. Checked 84 existing commands and their pins. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest integration_gate.test_offline_limits` | Exit 0. Eleven tests passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Both exited 0. Architecture gate and seven tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/verify_commerce.py --report "$report_dir/commerce.json"` and `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/verify_canonical.py --report "$report_dir/canonical.json"` | Both reported `PASS` in a temporary report directory. |
| `sha256sum sdk/conformance/vectors/commerce-fixture-tuple.vectors.json "$bra/fixtures/commerce_market_full_receipts_v1.json"` | Exit 0. Both SHA-256 values match the paired fixture pins before and after. |
| `git hash-object` on both locked paths and a Python raw-byte comparison against `git ls-tree -rz HEAD -- reference/v0.3-rc1` | Both locked blobs and all 108 frozen reference paths match before and after. |
| `git diff --exit-code HEAD --` on the protected and pinned paths, and `git status --short --branch --untracked-files=all` | No diff on the protected and pinned paths. Status lists only the five paths below. |

## Delivery and preservation

The supervisor's offline instruction superseded the routine fetch. The
cached main ref is the local base, and remote freshness is unverified.
This delivery is an uncommitted worktree patch. Implementation and final
commit SHAs, A2 non-author review, and exact-head KTX kernel and KIX protocol
CI run IDs, statuses, and conclusions await supervisor delivery. Merge SHA
and post-merge CI are inapplicable.

Local verification covered the touched Python, fixture and documentation
paths plus their SDK and catalogue dependencies. The Cargo probe found
system Cargo 1.85.1 and the pinned 1.98.1 toolchain unavailable. Rust
verification for this patch was limited to the architecture checks and
protected-file comparison.

| Locked path | Git blob before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The frozen reference tree at HEAD is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Changed paths

- `docs/README.md`
- `reference/booking_resale_admission/README.md`
- `reference/booking_resale_admission/fixtures/commerce_transfer_lost_reply_v1.json`
- `reference/booking_resale_admission/test_commerce_transfer_lost_reply.py`
- `validation/2026-11-24-plan-commerce-transfer-lost-reply/README.md`

## Scope

The producer outcomes match the resale state machine's payment and transfer
rules. No explicit contract violation or undefined behavior surfaced. The
source-informed replay covers synthetic in-memory outcomes. Actual funds,
provider and chain facts, durability, and external Commerce acceptance are
outside the evidence. The recovery lookup remains `NOT_BOUND`.
[Resale state machine](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10-리셀-수락-상태-기계) ·
[Consumer boundary](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#unavailable-consumer-bindings)
