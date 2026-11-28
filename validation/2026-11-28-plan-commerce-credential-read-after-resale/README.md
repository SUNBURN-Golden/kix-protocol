# Commerce credential read after resale validation

Task `plan-commerce-credential-read-after-resale` uses the supervisor-provided
node specification and design plan. Planner run `1795850668` records the
proposal. The node has no task issue or `docs/tasks/` document.

| Baseline | SHA or state |
|---|---|
| Cached `origin/main` and starting HEAD on `agent/kix-plan-commerce-credential-read-after-resale` | `3bea6925ccb0abe346668b9af180e20e323f9ac2` |
| Read model reference prerequisite | `b289f0c7ceb8226ab54b76704cc454c85efa023b` (merge of #178) |
| Admission replay after resale prerequisite | `d2807292b84f78aff16935aebba80d33443f4f3b` (merge of #518) |
| Implementation and final task head | Worktree delivery. The supervisor owns commits. |

The supervisor's no-network rule precluded `git fetch origin main`. The cached
ref matched the starting branch HEAD. Remote freshness is unverified.

## Coverage

| Acceptance | Existing coverage | New evidence |
|---|---|---|
| Presentations at the four write checkpoints | Partial. The predecessor goldens record direct credential views at steps 12–15. | One host replays source steps 0–15 and compares every complete write receipt. It calls `FsmHost.read` at each checkpoint and compares `result` with the live diagnostic view and the pinned predecessor view. Listing sets `LISTING_LOCKED`, payment preserves it, and transfer sets `STALE_VERSION`. |
| Same request, digest and admission watermark | Partial. `ReadQueryHostTests.test_each_query_matches_the_live_view_and_does_not_mutate` covers the general read envelope. | The shared request passes the published `get_credential` schema. All four responses carry the same complete envelope metadata. Live `accepted_through` is four admission entries at 1,120,000 ms. The admission journal digest remains fixed across the checkpoints. |
| All five journals unchanged and zero consumption per read | Partial. The host test covers general non-mutation and the predecessor covers zero consumption at transfer. | The replay compares canonical journal bytes immediately around each read for reservation, resale, admission, settlement and credit. Detached diagnostics retain the paired SHA-256 digests and zero counts of `op == "consume"` from reservation and admission. Both consume IDs are null. |
| Swapped read envelopes are detected | Uncovered. | The negative case exchanges only the first and fourth envelopes in a detached copy. The same complete-byte comparator rejects it. |
| Portable references and `HOLD_SEMANTIC` | Uncovered for this history. | The replay pins both predecessor files and checks canonical inputs and outcomes. The companion index resolves all four input, source and outcome associations with their existing `MOCK_EVIDENCE` write bindings. Both new fixtures carry `HOLD_SEMANTIC`. |

The observed sequence matches the credential contract and all 16 pinned write
receipts. No explicit contract violation or new contract-undefined behavior was
observed in the replay.
[Credential read contract §2.10](../../docs/contracts/READ_MODEL_QUERIES.md#210-get_credential) ·
[Predecessor replay](../../reference/booking_resale_admission/test_commerce_admission_replay_after_resale_vectors.py) ·
[General read host coverage](../../integration_gate/test_http_gate.py#L2554) ·
[Checkpoint table and replay command](../../reference/booking_resale_admission/README.md#commerce-credential-read-after-resale-vectors)

## Fixture pins

All four filenames are relative to `reference/booking_resale_admission/fixtures/`.

| File | SHA-256 | Git blob |
|---|---|---|
| `commerce_admission_replay_after_resale_inputs_v1.json` | `d37011eb1c62cec56b8be8fb3a68ab9e3e6b20dbdc64a4c8adcab9f0fb2585df` | `341079f211a033534c21614ee9ed1b4a2902243c` |
| `commerce_admission_replay_after_resale_receipts_v1.json` | `fd9a4c4cb3b3b493dec39c079d78b5b9ece1c298e7a5f755aac8170948c06439` | `0e21731f525a6bd53ebd9d1cd606bd9eca800ec9` |
| `commerce_credential_read_after_resale_inputs_v1.json` | `8d50fa084433f5ca10582b5a7e47d9aec32233683ce7d0a55c29768a1e0c9624` | `efa9fa16e15f3d49e251911782a273836df4b671` |
| `commerce_credential_read_after_resale_receipts_v1.json` | `904d5d13ed2a09827853e75439b9c187a6cc4fa96ca5e2bc269ebb3d24fe576d` | `0d51137cd352407c5867c63c46e9506d8eb73f21` |

## Changed paths

- `reference/booking_resale_admission/fixtures/commerce_credential_read_after_resale_inputs_v1.json`
- `reference/booking_resale_admission/fixtures/commerce_credential_read_after_resale_receipts_v1.json`
- `reference/booking_resale_admission/test_commerce_credential_read_after_resale_vectors.py`
- `reference/booking_resale_admission/test_commerce_companion_evidence_index.py`
- `reference/booking_resale_admission/README.md`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md`
- `docs/README.md`
- `validation/2026-11-28-plan-commerce-credential-read-after-resale/README.md`

## Local verification

Python 3.12.15 ran from the repository root with `PYTHONPATH=.` and
`PYTHONDONTWRITEBYTECODE=1`. Here `$bra` is `reference/booking_resale_admission`.
The three focused suites ran in the listed order before broad discovery.

| Command | Actual result |
|---|---|
| Inline `PYTHONPATH=.:reference/booking_resale_admission python3.12 -B -` vector capture | Exit 0. Replayed 16 matching receipts and wrote four complete host envelopes at the planned checkpoints. |
| Inline `PYTHONPATH=.:reference/booking_resale_admission python3.12 -B -` companion index append | Exit 0. Added four existing `MOCK_EVIDENCE` write bindings. Total is 19 packs and 438 steps. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p test_commerce_credential_read_after_resale_vectors.py -v` | Exit 0. Two tests passed, including swapped-envelope rejection. |
| Same focused command with `-p test_commerce_admission_replay_after_resale_vectors.py` | Exit 0. One test passed. |
| Same focused command with `-p test_commerce_companion_evidence_index.py` | Exit 0. All 18 tests passed, including the new checkpoint association test. |
| `python3.12 -B -m unittest integration_gate.test_http_gate.ReadQueryHostTests integration_gate.test_offline_limits` | Exit 0. All 20 tests passed. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra"` | Exit 0. All 1,112 tests passed, including the existing admission gate test on a disposable loopback endpoint. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for each other suite in the workflow block | Each exit 0. `settlement_f01_f03` 225, `credit_advance_f04` 342, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99 tests passed. |
| `python3.12 -B scripts/check_docs_index.py` and repeat with `--self-test` | Both exit 0. 490 scanned, 455 indexed, 35 allowlisted. Self-test passed. |
| `python3.12 -B scripts/check_read_model_source_map.py` and repeat with `--self-test` | Both exit 0. Verified 13 queries and 147 citations. Self-test passed. |
| `python3.12 -B scripts/check_bra_evidence_map.py` and repeat with `--self-test` | Both exit 0. Verified 39 rows and 219 citations. Self-test passed 50 negative controls. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and repeat with `--self-test` | Both exit 0. Reached nine reference suites, eight Node tests and four Python modules. Self-test passed 18 negative controls. |
| `python3.12 -B scripts/check_openapi_contract.py` and repeat with `--self-test` | Both exit 0. Verified 94 command and read schemas and the catalogue pin. Self-test passed. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and repeat with `--self-test` | Both exit 0. Verified 94 command and read schemas and local endpoint constraints. Self-test passed. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and repeat with `--self-test` | Both exit 0. Verified 84 command identities and 13 reads. Self-test passed. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and repeat with `--self-test` | Both exit 0. Verified 84 commands and 13 `NOT_BOUND` reads. Self-test passed 10 negative controls. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0. Architecture and declared dependency checks passed. |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0. Seven tests passed. |

### Offline Rust verification

Cargo used Rust 1.98.1 and `CARGO_NET_OFFLINE=true`. The full manifest stops at
resolution because the existing `kix-analytics-audit` dependency `duckdb` is
missing from the offline crates.io index. The fallback copied six local crates
and the pinned toolchain file into a temporary workspace under `.local/`.
`diff -qr` matched each source tree, and all six resolved package records
matched `runtime/Cargo.lock`. The fallback excludes `kix-analytics-audit` and
`kix-bcs1`. Full-workspace compilation remains unverified.

In the table, `$manifest` was `runtime/Cargo.toml` for the repository commands
and the generated manifest in the temporary workspace for the fallback.

| Command | Repository manifest | Six-crate manifest |
|---|---|---|
| `python3.12 -B scripts/check_cargo_offline_cache.py` piped to a Python JSON summary | Exit 0. 16 of 378 archives present. Both `duckdb` and `libduckdb-sys` absent. | — |
| Inline `python3.12 -B -` copying sources, running `diff -qr`, generating the manifest, and comparing lock records | — | Exit 0. Six byte-identical source trees and six matching package records. |
| `cargo generate-lockfile --manifest-path "$manifest" --offline` | — | Exit 0. |
| `cargo test --manifest-path "$manifest" -p kix-kernel --locked` | Exit 101 at offline resolution. | Exit 0 with `--quiet`. 139 tests passed. |
| `cargo clippy --manifest-path "$manifest" -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 at offline resolution. | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. | — |
| `cargo tree --manifest-path "$manifest" -p kix-kernel --edges normal --locked` | Exit 101 at offline resolution. | Exit 0. `kix-types` is the sole normal dependency. |
| `cargo test --manifest-path "$manifest" --workspace --locked` | Exit 101 at offline resolution. | Exit 0 with `--quiet`. 332 tests passed. |
| `cargo clippy --manifest-path "$manifest" --workspace --all-targets --locked -- -D warnings` | Exit 101 at offline resolution. | Exit 0. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Computed the workflow input digests. | — |

## Byte preservation

| Command | Actual result |
|---|---|
| `git rev-parse HEAD refs/remotes/origin/main` at start and after implementation | Both refs stayed at `3bea6925ccb0abe346668b9af180e20e323f9ac2`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` at start and after implementation | Both runs returned `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`, respectively. |
| `find reference/v0.3-rc1 -type f -print0 \| LC_ALL=C sort -z \| xargs -0 -r sha256sum \| sha256sum` at start and after implementation | Both inventories contain 108 files with digest `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b`. |
| `git diff --exit-code HEAD --` and `git ls-files --others --exclude-standard --` on protected paths | Exit 0. The frozen tree, runtime, `.aiops/`, task documents, workflows, OpenAPI, historical binding records, producer tuple and source fixtures match the base. |
| `git hash-object` and `sha256sum` on both predecessor and both new vector files | Exit 0. See the fixture pins above. |
| `git diff --check` and inline `python3.12 -B -` with `git diff`, `git ls-files` and `git show` | Exit 0. Ten expected paths changed. New-file whitespace passed. The companion JSON preserves all prior bytes before the appended pack, with 19 packs and 438 entries total. |

## Delivery scope

The evidence uses a source-informed in-memory mock with synthetic clocks.
The published local-call profile has grants `none`. The historical consumer
index retains 13 `NOT_BOUND` reads, SD1 remains `OPEN` and User-owned, and
external `kix-commerce-apps` acceptance remains `UNVERIFIED`. TTLs, fees and
compensation remain `UNDETERMINED` with Astra and JunTae. Legal and provider
effects remain `UNDETERMINED` with their existing owners.
[Published transport bindings](../../docs/status/COMMERCE_READ_BINDING_BY_TRANSPORT_V1.json)

The replay checks only the mock decisions and accepted journals. Admission
authority, provider calls, real funds, durable recovery, distributed fencing,
chain finality, legal compliance and production behavior are outside its
scope. Hosted bootstrap, full HTTP workflow setup, Move and ZK checks are
outside the local verification for these paths. A2 non-author review and
successful KTX and KIX workflows require the supervisor's exact delivery head.

| Hosted evidence | Run ID, status and conclusion |
|---|---|
| KTX kernel verification | Pending exact delivery head. |
| KIX protocol verification | Pending exact delivery head. |
| Merge and main push verification | Pending authorized merge. |
