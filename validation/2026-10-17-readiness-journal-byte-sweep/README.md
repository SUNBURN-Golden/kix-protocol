# readiness-journal-byte-sweep

Node: `plan-plan-readiness-journal-byte-sweep`. Exhaustive byte-level tear and flip sweep of the
non-production readiness journal `journal.v1` (`readiness/store.py`), a fault-scenario addition
allowed by D-3 (`docs/decisions/PROGRAM_DECISIONS_20260928.md` section 4).
Issue: none. Depends on: `readiness-extensions`. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Not program mode; no ASTRA markers posted. Source: KIX planner run 1792193921 (loop-proposed node, not
in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA, no final task head SHA and no exact-head CI run ID; local results
below are not exact-head CI. Exact-head CI belongs in the PR closure report (AGENTS section 11).

Observed `origin/main` and branch HEAD at session start: `492a85d36fc79aa31d3938bd44024b73dd70dfad`
(`git fetch origin main` left it unchanged; no delta).

## Locks

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

Changed paths: `readiness/test_faults.py` (new class `JournalByteSweepTests`; the only existing-line
change is the `readiness.store` import, extended with `HEADER_LEN`, `MAX_RECORD_BYTES`; plus `import zlib`
and `Counter`), this record, one `docs/README.md` row. `store.py`, `codec.py`, `migrate.py`, `policy.py`,
`machines.py`, `readiness/CONFORMANCE.md`, `docs/contracts`, `reference/v0.3-rc1`, `.aiops`, `.github`,
`runtime`, `docs/tasks` are unchanged.

## What the sweep does

A 4-frame journal (settlement, reservation `fsm_commit`; `integration_core` `core_commit`; credit
`fsm_commit`) is written through the public `ReadinessStore.append`: 839 bytes, frame bounds
`16, 185, 351, 678, 839` read from `committed_bytes`. Each mutation is written to a fresh directory and
opened with `ReadinessStore.open`. Global safety property: `open()` raises `StoreError`, or the recovered
records are an exact prefix of the originals. Families:

- **T**: truncate at every offset 16..839 (824 cases). Open returns exactly the longest whole-frame prefix,
  the file is truncated to that boundary, a following `append` works, and a further reopen sees prefix + new record.
- **H**: truncate to 0..15 bytes and XOR 0xFF every header byte (16 cases).
- **F**: XOR 0xFF every payload and CRC byte of every frame (807 cases).
- **L**: XOR 0xFF every byte of every 4-byte length prefix (16 cases).
- **R**: four CRC-consistent re-framed payload edits (invalid UTF-8, duplicate key, `schema` 2,
  `protocolTruth` true), so the `JOURNAL_CORRUPT` column is not vacuous.

Stdlib only, no randomness, no network, no wall-clock branching.

## AGENTS section 7 coverage mapping

Existing store tests (`readiness/test_faults.py`): `test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed`
and `test_unknown_schema_is_refused_without_a_guess`.

| Requirement | Before | Sweep adds |
|---|---|---|
| Tear of trailing frame | partial: one half-frame via `fault='partial'` | every offset 16..EOF, plus append and reopen after recovery |
| Checksum fail-closed | partial: one flip at offset 20 | every payload and CRC byte of all 4 frames |
| Header | partial: version 99 only | truncation 0..15, every header byte flip, reserved and magic bytes |
| Length prefix | not covered | all 16 length bytes, outcome classes pinned |
| CRC-consistent bad payload | not covered | 4 re-framed cases |

## Outcome table (mutations by result)

| Family | Cases | Prefix kept | CHECKSUM_MISMATCH | JOURNAL_CORRUPT | JOURNAL_HEADER | UNSUPPORTED_SCHEMA | Silent drop of later complete frames |
|---|---|---|---|---|---|---|---|
| T | 824 | 824 | 0 | 0 | 0 | 0 | 0 (the cut itself removes them) |
| H | 32 | 0 (1 empty-file reinit, class B) | 0 | 0 | 27 (15 truncations, 12 flips) | 4 (bytes 8-11) | 0 |
| F | 807 | 0 | 807 | 0 | 0 | 0 | 0 |
| L | 16 | 12 | 4 | 0 | 0 | 0 | 9 (included in the 12 prefix-kept) |
| R | 4 | 0 | 0 | 4 | 0 | 0 | 0 |

L detail: bytes 0-1 of any frame exceed `MAX_RECORD_BYTES`; byte 2 points past EOF; both are parsed as a
torn tail, giving prefix `originals[:i]` and the file truncated to `bounds[i]`. For frames 0-2 (each followed by
at least one complete frame) that drops later complete frames: 9 cases. Frame 3 (final) gives 3 cases that look exactly like a torn tail. Byte 3 gives
CHECKSUM_MISMATCH in all 4 cases. No altered, reordered or fabricated record was observed anywhere.

## AGENTS section 8 classification

| Finding | Class | Minimal reproduction (public API) |
|---|---|---|
| Damaged length prefix of a non-final frame (past EOF or above `MAX_RECORD_BYTES`) is parsed as a torn tail; `open()` truncates the file and silently drops later complete, acknowledged frames; restoring the byte does not bring them back | B | write 4 records; flip byte `bounds[1]` of `journal.v1`; `ReadinessStore.open(dir)`; observe `records` has 1 element and file size is `bounds[1]` with no error. Pinned by `test_characterization_b_damaged_length_prefix_drops_later_acknowledged_frames` |
| Final-frame length damage is indistinguishable from a torn tail | B | as above with the last frame; prefix of 3 records, no error |
| 0-byte `journal.v1` is silently reinitialised (header rewritten, empty store) | B | create empty file; `open()` returns empty store, file size 16 |
| Clean truncation at a frame boundary is undetectable | B | truncate to `bounds[2]`; `open()` returns 2 records, no error |
| `_validate` failures after a good CRC collapse to `JOURNAL_CORRUPT` (never `UNSUPPORTED_SCHEMA`/`PROTOCOL_TRUTH_REFUSED`) | B | re-frame a payload with `"schema":2` and a correct CRC; `open()` raises `JOURNAL_CORRUPT` |
| Class C (explicit contract violation) | none found | |

`docs/contracts/READINESS_RUNTIME.md` line 21 says "끝의 불완전한 프레임은 찢긴 쓰기다. 그 꼬리만 버리고, 체크섬이 맞는 앞선
레코드는 재생한다." and defines only a trailing incomplete frame and a complete frame with a bad checksum. A stricter reading
("only that tail") could make the first finding class C; this record classifies it B because the contract does not define a
damaged length prefix of a non-final frame, and does not decide the question. It is a follow-up candidate for Astra.

## Commands actually run

See the evidence table in the session report; summary: locked blobs match before and after;
`python3 -m unittest -v readiness.test_faults.JournalByteSweepTests` 6 tests OK in about 0.6 s;
`python3 -m unittest integration_gate.test_http_gate readiness.test_faults` 64 tests OK in about 5.1 s
(Python 3.13.5; CI uses 3.12); `readiness.test_faults` OK under `PYTHONHASHSEED=0` and `random`;
docs and register checks plain and `--self-test` exit 0. Not run locally: Cargo, clippy, fmt, Sui, Node, ZK,
localnet, reference-suite loop (those paths are untouched). Exact-head hosted CI is not claimed.

## Non-claims

No power-loss, OS-crash or disk-flush claim: files are rewritten in-process and `fsync` behaviour is not tested.
No production durability. `protocolTruth` and `productionConformance` stay `false`. Not a `BackendConformance`
negative control. No grade change, no contract change, no format change. Multi-byte or adversarial
CRC-matching damage beyond the four R cases is not swept.

## Follow-up candidates

- Astra ruling on the damaged-length-prefix reading of `READINESS_RUNTIME.md` line 21.
- Format-hardening ADR (length checksum, sync marker, or refusing to truncate when later bytes look like frames);
  any fix is a format/schema change, out of scope here.
- `CONFORMANCE.md` note that the sweep exists; EV-READY register row and the stale "14 tests OK" line.
