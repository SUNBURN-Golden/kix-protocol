# kix-types-boundary-fixtures

Node: `plan-plan-kix-types-boundary-fixtures`. Boundary fixtures for the untested
constructors and edges of `runtime/crates/kix-types` (fixed-width ids, versioned
asset-bound money, typed counters), the approved boundary types used by `kix-bcs1`,
`kix-feature-ir`, `kix-kernel-v5` and `kix-delegated-exec`.
Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`,
`user_merge: false`. Loop-proposed node, not in `.aiops/program.json`. No ASTRA markers
were posted.

This session did not commit, push, open a pull request, create or close an issue, or
comment. There is no implementation commit SHA and no final task head SHA. Local results
below are not exact-head CI. Exact-head CI for the final head is not recorded in the
commit (AGENTS §11); it belongs in the PR closure report.

Observed `origin/main` and branch HEAD at session start:
`059410cd85bf944142175fbd70364f7cc54ea196` (merge of PR #234). `git fetch origin main`
was not run in this worktree (no network/GitHub actions in the builder session);
`origin/main` resolved to the same SHA locally.

## Locks

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

No change to `runtime/crates/kix-types/src/lib.rs`, `runtime/crates/kix-types/Cargo.toml`,
`runtime/Cargo.toml`, `runtime/Cargo.lock`, `runtime/ARCHITECTURE.toml`,
`reference/v0.3-rc1/**`, `.aiops/`, `.github/` or `docs/tasks/`.

## New tests (`runtime/crates/kix-types/tests/boundary_edges.rs`)

| Test | Gap closed |
|---|---|
| `full_range_counters_accept_zero_and_primitive_max` | `Sequence`/`Generation`/`AdmissionEpoch` (u64) and `Version`/`Quantity`/`DurationSeconds` (u32) at 0 and at the declared max; `get()` returns the input. The "max+1" cell is empty — see class B below |
| `hash32_display_round_trips_lowercase_hex` | `Display` output is 64 lowercase hex chars and `parse_lower_hex` inverts it for ascending, `0xff` and `0xa5` byte arrays |
| `hash32_parse_rejects_malformed_lengths_and_case` | `InvalidHash` for uppercase, non-hex (`g`/`z`/`-`) at first/mid/last positions, length 63, length 65 and empty input |
| `legacy_asset_id_rejects_malformed_inputs` | `InvalidLegacyAssetId` (not `InvalidHash`) for missing/wrong/uppercase prefix, uppercase/non-hex/truncated/overlong/empty digest, and a non-leading prefix; positive control round-trips to `from_bytes` |
| `asset_amount_checked_at_approved_boundaries` | `atoms == approved_max` accepted, `approved_max + 1` and `u128::MAX` over a lower max rejected, `u128::MAX`/`u128::MAX` and `0`/`0` accepted |
| `byte_array_ids_order_and_hash_consistently` | `Ord` follows lexicographic `as_bytes()` order for `KixId`/`Hash32`/`AssetId` on first-byte, last-byte and equal pairs; `cmp == Equal` iff `==`; equal values collapse in a `HashSet` and hash identically |
| `type_error_display_strings_are_pinned` | all six `TypeError` `Display` strings verbatim; `TypeError` coerces to `Box<dyn std::error::Error>` |

## API-to-test map (AGENTS §7)

Existing inline tests are in `runtime/crates/kix-types/src/lib.rs` (six `#[test]`s).

| Type/API | New tests | Existing tests | Coverage |
|---|---|---|---|
| `KixId` bytes | `byte_array_ids_order_and_hash_consistently` | `production_id_is_fixed_128_bits` | sufficiently for in-memory identity |
| `Hash32` parse/`Display` | `hash32_display_round_trips_lowercase_hex`, `hash32_parse_rejects_malformed_lengths_and_case`, `byte_array_ids_order_and_hash_consistently` | `hash_parser_is_compatibility_only_and_strict` (one valid, uppercase, length-2) | sufficiently at scalar level |
| `AssetId` legacy parse | `legacy_asset_id_rejects_malformed_inputs`, `byte_array_ids_order_and_hash_consistently` | `asset_identity_is_binary_first` (one valid, one whole-string uppercase) | sufficiently at scalar level |
| `RegistryVersion`, `DomainId`/`SchemaId`/`SchemaVersion`, `KixBcs1Header` | none (cited, not duplicated) | `bcs_header_types_cannot_be_zero` | sufficiently for the zero-rejection contract |
| `TimestampMs`, `BasisPoints` bounded counters | none (cited, not duplicated) | `semantic_integer_types_keep_distinct_ranges` (max accepted, max+1 rejected for both) | sufficiently for the reachable range guard |
| `Sequence`, `Version`, `Quantity`, `Generation`, `AdmissionEpoch`, `DurationSeconds` | `full_range_counters_accept_zero_and_primitive_max` | none | partially: endpoints pinned; no in-domain input can reach `CounterOutOfRange` (class B) |
| `AssetAmount::checked` | `asset_amount_checked_at_approved_boundaries` | `amount_cannot_lose_asset_or_registry_context` (one accept, one reject) | sufficiently at scalar level |
| `TypeError` | `type_error_display_strings_are_pinned` | variant equality asserted inline; `Display` strings not asserted before | sufficiently for the six variants |

## AGENTS §8 classification

- **Class A (contract-defined and matching):** strict lowercase-64-hex `Hash32`
  parsing; `asset-v2-` prefix requirement and `InvalidLegacyAssetId` mapping;
  `AssetAmount::checked` approved-max bound; `Ord`/`Hash`/`Eq` consistency on the
  byte-array ids; the six `TypeError` `Display` strings.
- **Class B (contract undefined), characterization only, no fix, no semantics chosen:**
  1. *Full-range counters.* `Sequence`, `Version`, `Quantity`, `Generation`,
     `AdmissionEpoch` and `DurationSeconds` are declared `counter!(Name, T, T::MAX)`:
     the bound equals the primitive max, so `new()` is total on the input type and
     `CounterOutOfRange` is unreachable for them. Whether the bound is intended or a
     narrower domain maximum exists is undefined — no contract names these maxima.
  2. *Zero acceptance.* The six counters accept 0 while `RegistryVersion` and the
     schema ids reject it; no contract says whether zero is a valid sequence,
     version, quantity, generation, epoch or duration.
  3. *Domain semantics.* No consumer of `kix-types` imports `DurationSeconds`,
     `Version`, `Quantity`, `Generation`, `AdmissionEpoch` or `Sequence` today; any
     wire/domain meaning stays undetermined.
- **Class C (explicit violation):** none found; all tests pass on unmodified `src/`.

The pinned rows intentionally break if `src/` later changes; that is intended and not
a contract assertion.

## Commands actually run

See the final session report for the evidence table; results recorded there are the
actual outputs.

## Non-claims

- In-memory constructor/parser tests through public APIs only. Not a wire, BCS1
  serialization, storage, exporter, durability or production result.
- This record does not claim completeness: only the listed cells are pinned, and the
  empty "max+1" cells for full-range counters are recorded, not filled.
- This record does not claim clean-room independence: the fixtures are
  source-informed characterizations of `src/lib.rs` as written.
- No domain maximum, zero-validity rule or wire meaning for the six counters is
  chosen; no consumer of those types exists to characterize against.
- Release-mode behaviour is untested; all runs are dev-profile.
- Test count is not a completion criterion.

## Remaining uncertainty and follow-ups

- Whether the unreachable `CounterOutOfRange` guard on the six full-range counters is
  intentional needs a separate explicit decision if a narrower domain maximum is ever
  defined.
- If a consumer starts importing `Sequence`/`Version`/`Quantity`/`Generation`/
  `AdmissionEpoch`/`DurationSeconds`, their domain semantics need a contract before
  stronger fixtures can be written.
