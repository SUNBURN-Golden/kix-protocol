# Offline public-tree witness reconstruction regressions

Node: `plan-rs-witness-offline-regressions`. Task input: the supervisor-supplied
node specification and read-only design plan in this session; no issue or
`docs/tasks/` document was supplied. This is not ASTRA program mode.

## Identity and base

- Branch: `agent/kix-plan-rs-witness-offline-regressions`.
- Session HEAD and cached `origin/main`: `9b462fd2cd6890cd0d8fbc2930f2cc54255e2915`.
  There is no local base delta. The supervisor prohibits all network actions, so
  `git fetch origin main` was not run; remote freshness is unverified
  (deviation from AGENTS.md §1 step 1, forced by the session rule).
- No commit, push, PR or publication is authorized; the supervisor owns
  git/GitHub. Implementation/task head will be assigned by the supervisor.

## Locked blobs (verified before and after the work)

| File | Required blob | `git ls-files -s` | `git hash-object` (worktree) |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

`reference/v0.3-rc1/**` and `.aiops/**` are unchanged (empty diff).

## Changed paths

- `reference/rights_scale/client/witness-reconstruction.test.mjs` — new
  `node:test` suite (16 cases) against the existing `rebuildTreeView`.
- `docs/status/RS_IM_EVIDENCE_MAP.md` — IM-19 missing-evidence cell and a
  reading note; status `PARTIAL`, counts, citations and gaps unchanged.
- `docs/status/RS_PREDICATE_EVIDENCE_MAP.md` — RR-4 missing-evidence cell and a
  reading note; status `COVERED_LOCALNET`, counts, citations unchanged.
- `docs/README.md` — index bullet linking this record.
- `validation/2026-10-21-plan-rs-witness-offline-regressions/README.md` — this record.

Client implementation, BCS layouts, page-currentness logic, contracts,
workflows, `package.json`/`package-lock.json`, `.aiops/program.json`, locked
kernel files and `reference/v0.3-rc1/**` are unchanged.

## Existing coverage mapping (recorded before adding tests)

| Existing evidence read | Classification for this node |
|---|---|
| `reference/rights_scale/client/private-localnet.mjs::eventsView`, `reconstruct`, event-backed `prove`; `reference/rights_scale/vectors/private_path.json` | Partially covered: successful RPC/checkpoint/cache comparison and event-backed witnesses; missing deterministic offline guard rejection and object-read allowlist checks. |
| `reference/rights_scale/client/zk-regression.mjs`, section 4 | Sufficiently covered at circuit level: wrong roots, note siblings and revocation paths; reconstruction event handling is not covered. No duplicate proof tests added. |
| `reference/rights_scale/sui/tests/root_math_tests.move::empty_tree_zero_hashes_match_circomlibjs`, `depth_ten_incremental_roots_match_circomlibjs`, `sparse_update_roots_match_circomlibjs` | Sufficiently covered arithmetic; offline reconstruction integration is not covered. Selected existing constants cross-check the fixture oracle. |

## What the new suite adds

`rebuildTreeView` (`reference/rights_scale/client/chain-witness.mjs`) is driven
with synthetic BCS-serialized `NoteAdded`/`RevocationLeaf` events from an
injected `source` and injected `getFields` object reads.

- Positive controls: `empty_tree`, `populated_tree`, `reordered_notes`,
  `unrelated_show_events` (a foreign-show note index 999 and a foreign-show
  slot-5 generation 99 are interleaved and must be filtered before rebuilding),
  `maximum_revoked_generation` (genuine increasing history reordered so a lower
  generation arrives last).
- Negative controls: `missing_note_index`, `duplicate_note_index`
  (`NOTE_EVENT_GAP:2`), `corrupt_intermediate_note_root`
  (`NOTE_EVENT_ROOT_MISMATCH:1` while commitments and the stored object
  root/count stay intact), `note_root_mismatch`, `note_count_mismatch`,
  `revocation_root_mismatch`, `revocation_count_mismatch`
  (`REBUILT_*_ROOT_MISMATCH:<source>`), `omitted_maximal_revocation`,
  `omitted_nonmaximal_revocation` and `duplicated_revocation` (the last two keep
  the rebuilt root equal so only the event-count check can catch them).
- Read allowlist: `getFields` permits exactly `(treeId, NoteTree)` and
  `(revocationId, RevocationState)`, each read exactly once in passing cases,
  and fails on any other id/schema. No `InventoryPage` or inventory-vector read
  is possible through the injection.
- `dense_fixture_matches_existing_move_known_answers` cross-checks the fixture
  oracle against constants copied from `root_math_tests.move`.

## Fixture provenance and non-claims

- The oracle is a deliberately dense bottom-up fold over all `2 ** DEPTH`
  leaves (unused positions zero), independent of `SparseTree`/`noteTreeOf`/
  `revocationTreeOf`. Both share the circomlibjs Poseidon primitive, and the
  Move constants the oracle is cross-checked against were originally generated
  with the same primitive — a structural cross-check, **not** an independent
  cryptographic proof.
- `getFields` returns explicitly labeled parsed-field projections; no object
  BCS decoding is claimed for objects. Event bytes are real BCS through
  `types.mjs` serializers (`NoteAdded.serialize`/`RevocationLeaf.serialize`
  round-trip through the same parsers the client uses).
- No RPC connection, localnet, secrets, proving keys, circuit generation or new
  dependency is used. Nothing is claimed about transport completeness,
  checkpoint scanning, page currentness, historical-root acceptance,
  gate-packet secrecy or production behavior.
- IM-19 stays `PARTIAL`: the gate-secret assertion gap and the historical
  evidence grades are preserved. Public-tree retention and operational
  parameters stay UNDETERMINED, owned by Astra.

## Commands actually run and actual results

All commands from the repository root unless noted. Node:
`/workspace/toolchain/node-v24.19.0-linux-x64/bin/node` (v24.19.0; the PATH
`node` is v20.19.2, below the package `engines` range `>=24 <25`). Python:
3.13.5 (workflow pins 3.12; difference noted, results recorded as run).

| Command | Result |
|---|---|
| `git rev-parse HEAD` / `git rev-parse origin/main` | `9b462fd2cd6890cd0d8fbc2930f2cc54255e2915` / same |
| `git ls-files -s` + `git hash-object` on the two locked files | both required blobs match, before and after |
| `node --test reference/rights_scale/client/witness-reconstruction.test.mjs` | 16 tests, 16 pass, 0 fail (~1.9 s) |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 129 tests, OK |
| `node reference/rights_scale/client/gen-move-vectors.mjs --check` | `Move known-answer constants match circomlibjs: 23 vectors` |
| `python3 scripts/check_rs_im_evidence_map.py` | ok: rows=30 expected=30 citations=179 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | ok: rows=23 expected=23 citations=168 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_docs_index.py` | ok: scanned=189 indexed=154 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | self-test: pass |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 42 test targets, 257 tests passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean, no warnings |

## Local execution vs CI discovery

The new file is invoked by **neither** workflow: `protocol.yml` runs the
rights-scale Python discovery suite, the localnet drivers and
`setup:zk`/`test:zk` (`zk-regression.mjs`), and `ktx-kernel.yml` runs the
runtime Cargo steps. The `node --test` result above is local execution only,
not CI discovery. Because the diff touches `reference/**`, the docs-only
classifier would run full verification on the exact head; that CI evidence is a
delivery gate this record does not produce. Localnet and ZK-generation steps
were not run locally (they require a disposable Sui localnet and the fixture
ceremony and are outside this node).

## Discrepancy classification (AGENTS.md §8)

- Contract violations found: none. `rebuildTreeView` behaved as
  `chain-witness.mjs` documents; every rejection asserted is an existing guard.
- Contract-undefined characterizations (class B, recorded only): the
  `test:offline` script in `reference/rights_scale/client/package.json` names
  `offline.test.mjs`, a file that does not exist at this base (pre-existing,
  added by commit `c6ca519`). Package files are outside this node's authorized
  paths, so it is left untouched and unresolved.

## Remaining gates

Exact-head KTX kernel verification and KIX protocol verification (both
completed/success), A2 non-author review and human merge authorization remain
delivery gates. `user_merge: False`; no merge is claimed or proposed here.
