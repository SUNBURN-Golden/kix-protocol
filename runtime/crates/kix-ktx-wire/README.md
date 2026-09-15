# KTX registered replay wire schemas

This R2-A crate serializes immutable genesis, ordered kernel commands and typed
application decisions through KIX-BCS1. It does not authenticate an input,
implement a snapshot, persist anything, or provide a quorum acknowledgement.
`kix-kernel` continues to depend only on `kix-types`.

## Registration and compatibility

`registry.rs` is the registration source of truth. The same registration
constants supply the codec trait implementations and the enumerable registry.
`encode_registered` / `decode_registered` accept only the sealed
`RegisteredSchema` implementations in this crate. Adding an arbitrary
`KixBcsSchema` implementation elsewhere does not register a KTX entry point.
Tests reject duplicate or zero identities and production registration of the
historical test-only identity `65535/65535`.

| Schema | Domain/schema/version | Maximum body bytes |
| --- | --- | ---: |
| `GenesisV1` | `1/1/1` | 8,320 |
| `CommandV1` | `1/2/1` | 512 |
| `CommandResult` | `1/3/1` | 128 |

The existing `kix-bcs1` test vector and bytes are unchanged. These registrations
are distinct from the historical test namespace. A command schema is not a
public authorization endpoint or an authenticated AssetRegistry.

All fixed integers use BCS little endian. IDs are fixed 16 bytes; asset and hash
identities are fixed 32 bytes. Sequences and enum tags use canonical ULEB128.
Tuple/struct fields are concatenated in the order specified below. Enum tags,
field order, error codes, semantics and bindings may not change under these
schema identities. New behavior needs a versioned replay/migration contract.
Currently only kernel semantics version 1 is accepted; unknown versions fail
before replay. No rolling upgrade or version activation is implemented.

## Exact field and tag definitions

Shared layouts:

- `Fence = (owner:id16, generation:u64)`.
- `Context = (fence:Fence, now_ms:u64, semantics_version:u16)`.
- `CommandId = (scope:id16, principal:id16, request:id16)`.
- `Operation = (provider:id16, account:id16, operation:id16)`.
- `Amount = (asset_id:bytes32, atoms:u128, registry_version:u32, registry_hash:bytes32)`.

`GenesisV1 = (scope:id16, fence:Fence, business_epoch:u64, inventory:Inventory,
limits:(commands:u32, orders:u32, observations:u32), semantics_version:u16)`.
Inventory tag 0 is `Seats(vec<u16>)`; each value is the length of a real
contiguous segment. Tag 1 is `GeneralAdmission(capacity:u32)`. Seats have at most
4,096 segments and at most 4,096 total seats, all lengths positive. The decoder
rejects excessive declared segment counts before allocating element storage.
GA capacity, owner generation, business epoch and limits must be positive.
Limits are converted to `usize` with checked conversion when creating the
kernel. No occupied bitmap or mutable pre-existing state is accepted as genesis.

`CommandV1 = (ctx:Context, action:Action)` with these action tags and fields:

| Tag | Action and payload |
| ---: | --- |
| 0 | `Reserve(id:CommandId, order_id:id16, expected_business_epoch:u64, selection:Selection, amount:Amount, quote_hash:bytes32, policy_hash:bytes32, expires_at_ms:u64, payment:Operation)` |
| 1 | `MarkPaymentUnknown(order_id:id16)` |
| 2 | `Expire(order_id:id16)` |
| 3 | `CancelScope(next_business_epoch:u64)` |
| 4 | `ReplaceOwner(next:Fence)` |
| 5 | `ObserveCapture(event_id:id16, operation:Operation, amount:Amount, evidence_hash:bytes32)` |

Selection tag 0 is `Seats(first:u16, count:u16)`; tag 1 is
`GeneralAdmission(count:u32)`. Semantically rejected but structurally valid
requests, including zero price or unavailable seats, remain encodable so their
deterministic application decisions can be reproduced. Zero registry version
is structurally invalid. Decoding preserves `u128` without narrowing, but it
does not authenticate the claimed registry or an asset-specific approved limit.

`CommandResult` has the same six action tags, each followed by BCS
`Result`: tag 0 for success payload, tag 1 for a stable `KernelError:u8`.
Success payloads are:

- Reserve: `(ReserveOutcome, replayed:bool)`. Outcome tag 0 is `Held(order_id:id16)`;
  tag 1 is `Rejected(reason:u8)`.
- MarkPaymentUnknown, CancelScope, ReplaceOwner: unit, no payload bytes.
- Expire: `bool` (`0` or `1`).
- ObserveCapture: `outcome:u8`.

| Code | KernelError | Reserve rejection | Observation outcome |
| ---: | --- | --- | --- |
| 0 | InvalidConfiguration | InvalidRequest | PaymentConfirmed |
| 1 | UnsupportedSemantics | BusinessFenced | ReturnRequired |
| 2 | ExecutionFenced | Unavailable | Review |
| 3 | ClockRegression | OrderExists | DuplicateEffect |
| 4 | WrongScope | OperationAlreadyBound | Conflict |
| 5 | CommandConflict | OperationQuarantined | — |
| 6 | Capacity | — | — |
| 7 | UnknownOrder | — | — |
| 8 | InvalidTransition | — | — |
| 9 | UnknownOperation | — | — |

Unknown tags and codes, invalid booleans, noncanonical ULEB128, truncated input,
trailing bytes and mismatched envelope identities fail decoding.

## Replay and decision recovery

An immutable genesis plus the complete ordered command log reconstructs all
private kernel state, including original requests/results, payment intents,
owner and cancellation state, accepted observations, contradictory evidence and
quarantined operations. `CommandV1::apply` dispatches directly to the pure
kernel and returns the typed decision. It performs no external execution.

A storage driver may persist commands before application and reconstruct
results/intents through version-fixed replay. It must not mutate command
context while replaying, reinterpret old semantics, discard rejected-command
history, or mistake the original reservation outcome for current order state.
The separate decision schema allows receipt encoding and replay comparison;
its existence alone does not make a decision durable.

Control transitions currently have no independent global client-command key.
Retries of the original reservation retain its stable business identity, but
general idempotent administrative APIs need a subsequent durable command/result
contract. Genesis-plus-full-log replay is not a state snapshot, compaction,
membership transfer or recovery from missing historical files.

## Fixed vectors

`tests/golden_vectors.rs` embeds independently assembled bytes and SHA-256
digests. Python `struct.pack` / integer `to_bytes` and `hashlib` were used to
construct the fixtures from this specification without calling the Rust codec.

| Vector | Body / envelope bytes | SHA-256 |
| --- | --- | --- |
| Genesis with segments 65 and 4 | 68 / 79 | `2e3d2dd7b032ca8b351e8c36f604ce4228b38691598f5cd279f03fc5c6fd4986` |
| Reservation crossing a 64-bit word boundary | 316 / 328 | `9ebb8eef9ce9a4e0a7187716ad308e46c5b986904a9079bb991c3bcb49d259b7` |
| Original Held result | 20 / 31 | `1ae46454186abdfda06fd8d1696d32ea8b8ce41992e687682e4dbd25dbc95ef7` |

These are Rust replay schemas, not Rust-to-Move production interoperability
proofs. The test suite also exercises all error/action codes, malformed wire,
unsigned numeric boundaries, bounded genesis and owner/cancellation replay.
