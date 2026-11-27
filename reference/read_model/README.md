# Read-model candidate fixtures

**Candidate evidence pending the `read-model-reference` merge. The read-model
implementation is not merged and these fixtures are not conformance evidence.**

Node `plan-read-model-contract-fixture-prep`. Contract read:
[docs/contracts/READ_MODEL_QUERIES.md](../../docs/contracts/READ_MODEL_QUERIES.md)
draft 0.1 (13 owner-decided query names) and
[docs/contracts/READ_MODEL_SOURCE_MAP.md](../../docs/contracts/READ_MODEL_SOURCE_MAP.md).

## What is here

| Path | Content |
|---|---|
| `generate_fixtures.py` | Deterministic, stdlib-only fixture generator. Drives the five reference machines (`ReservationMachine`, `ResaleMachine`, `AdmissionMachine`, `SettlementMachine`, `CreditMachine`) through their public `REPLAYABLE` commands under `SEED = 20261020`, then emits the vectors below. No `def list_shows(`, `def list_bookings(`, `def list_open_listings(` exists here or in the machine modules. |
| `vectors/manifest.json` | `fixture_version`, `seed`, `read_schema_version: "0.1"`, `fixture_mode: "REFERENCE_IN_MEMORY"`, generator path, per-file sha256, per-machine `{journal_entries, logical_time_ms?}` watermark. |
| `vectors/reservation.json` | `list_shows`, `get_show`, `get_booking`, `list_bookings` vectors. |
| `vectors/resale.json` | `get_right`, `get_presentation`, `list_open_listings`, `get_listing` vectors. |
| `vectors/admission.json` | `get_admission`, `get_credential` vectors (including every `*_SOURCE_UNAVAILABLE` decision and `SETTLEMENT_SOURCE_REQUIRED`). |
| `vectors/settlement.json` | `get_settlement` vectors (`INITIATED` claim null, `CAPTURED`, `COMMITTED`). |
| `vectors/credit.json` | `get_credit_advance`, `get_credit_claim` vectors. |
| `../booking_resale_admission/test_read_model_fixtures.py` | Stdlib `unittest` self-check; discovered by the existing `protocol.yml` suite loop. |

## Regenerate / check

```bash
python3 reference/read_model/generate_fixtures.py            # writes vectors/
python3 reference/read_model/generate_fixtures.py --check    # byte-compares to committed files
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission
```

Determinism: `random.Random(SEED)` derives every hex ref; iteration is
sorted-only; output is the machines' canonical JSON
(`json.dumps(sort_keys=True, ensure_ascii=False, separators=(",",":"), allow_nan=False)`)
plus a trailing newline per file.

## What the vectors bind — and what stays NOT_BOUND

- Point `expected.ok` bodies are the literal `view*` dicts; the proposed
  envelope adds `read_schema_version`, `fixture_mode`, `accepted_through`
  (`journal_entries`, and `logical_time_ms` only where the machine has a
  clock), `query_input_canonical`, and `query_digest: "NOT_BOUND"` (hash
  algorithm undecided).
- List entries carry `population` (`FIXTURE_ORDERING identifier-asc; sort key
  UNDETERMINED`), `pages` at explicit `fixture_limit` (a fixture parameter —
  not a decided default or cap), `cursor_cases` (`FIXTURE_CURSOR_V1` format:
  canonical JSON of `(query, scope, ordering, snapshot)` + position; modeled
  rejections `CURSOR_MISMATCH` / `SNAPSHOT_CHANGED` / `INVALID_LIMIT` with
  `error_code: "NOT_BOUND"`), and `visibility` (`NOT_BOUND` with a
  `RECOMMENDATION_NOT_DECISION` `recommended_subset`).
- `list_open_listings.open_phase_predicate` is `NOT_BOUND`: the open-phase
  set is an `UNDETERMINED · Astra` value.
- The five `ReadObservationV1` keys and `subject_scope`/`profile_revision`
  are absent everywhere; the self-check asserts their absence.
- Snapshot-change vectors are minted against the pre-final-`set_clock`
  digest; the accepted `set_clock` then makes them stale — this models the
  section-5 snapshot-change rejection, not an implementation.

## Non-claims

- No query implementation, wire binding, catalogue/`protocol_contract.json`
  change, or OpenAPI edit exists in this node.
- Vectors pin the current in-memory `view*` output; they are replayable
  inputs for `p-sdk-1`, `contract-compatibility-profile` and future
  read-model acceptance runs — not conformance evidence, not a decision on
  any `UNDETERMINED` value, and not proof of payment, issuance, admission,
  durability or chain finality.
