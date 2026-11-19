"""Per-item normalization and the durable event alias.

docs/contracts/ADAPTER_EVENT_IDENTITY.md §4.4: the normalized fact of one item of
an authenticated lookup, never of an unverified webhook body. One delivery with
many items yields one fact and one evidence_hash per item. The delivery
(transmission) id, the receive time and the retry count are not inputs.

Which provider field is the ProviderFactKey is UNDETERMINED (TM04, toss technical).
This module takes the key as an opaque string chosen by the adapter. It names no
provider JSON field. The 16-byte alias is a conflict-checked table entry
(§4.5 "별칭 표"); the candidate derivation below is a local fixture rule, not a
ratified rule (DECISION_REQUIRED · Astra in §9 of that contract).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

from readiness.codec import canonical_json

from durable.errors import AliasConflict, NormalizationError

U128_MAX = (1 << 128) - 1


@dataclass(frozen=True)
class Scope:
    """provider, account (MID alias), environment, profile version."""

    provider: str
    account: str
    environment: str
    profile_version: str

    def __post_init__(self):
        for name in ('provider', 'account', 'environment', 'profile_version'):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise NormalizationError('SCOPE')

    def document(self):
        return {
            'account': self.account,
            'environment': self.environment,
            'profileVersion': self.profile_version,
            'provider': self.provider,
        }

    def key(self):
        return canonical_json(self.document())


@dataclass(frozen=True)
class ProviderItem:
    """One item of an authenticated lookup, mapped by the adapter."""

    fact_key: str
    kind: str
    amount_krw: int
    currency: str
    method: str
    status: str
    occurred_at_text: str
    occurred_offset: Optional[str] = None
    operation: Optional[dict] = None


@dataclass(frozen=True)
class NormalizedFact:
    scope_key: str
    fact_key: str
    fact: dict
    fact_json: str
    evidence_hash: str


def _text(value, code):
    if not isinstance(value, str) or not value:
        raise NormalizationError(code)
    return value


def _operation(operation):
    if operation is None:
        return None
    if not isinstance(operation, dict) or set(operation) != {'provider', 'account', 'operation'}:
        raise NormalizationError('OPERATION')
    for name in ('provider', 'account', 'operation'):
        _text(operation[name], 'OPERATION')
    return {name: operation[name] for name in ('account', 'operation', 'provider')}


def normalize_item(scope, item):
    """Return the per-item normalized fact and its evidence_hash.

    Amounts are KRW integers: bool, float and numeric strings are refused.
    The occurred time keeps the original text and the offset (or None); no
    time zone is assumed. Currency, method and status stay on this item.
    """
    if not isinstance(scope, Scope) or not isinstance(item, ProviderItem):
        raise NormalizationError('INPUT')
    amount = item.amount_krw
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise NormalizationError('AMOUNT_NOT_INTEGER')
    if amount < 0 or amount > U128_MAX:
        raise NormalizationError('AMOUNT_RANGE')
    offset = item.occurred_offset
    if offset is not None and not isinstance(offset, str):
        raise NormalizationError('OFFSET')
    fact = {
        'amountKrw': amount,
        'currency': _text(item.currency, 'CURRENCY'),
        'factKey': _text(item.fact_key, 'FACT_KEY'),
        'kind': _text(item.kind, 'KIND'),
        'method': _text(item.method, 'METHOD'),
        'occurredAtText': _text(item.occurred_at_text, 'OCCURRED_AT'),
        'occurredOffset': offset,
        'operation': _operation(item.operation),
        'scope': scope.document(),
        'status': _text(item.status, 'STATUS'),
    }
    fact_json = canonical_json(fact)
    return NormalizedFact(
        scope_key=scope.key(),
        fact_key=item.fact_key,
        fact=fact,
        fact_json=fact_json,
        evidence_hash=hashlib.sha256(fact_json.encode('utf-8')).hexdigest(),
    )


def normalize_items(scope, items):
    """One fact per item, in input order. Duplicate fact keys inside one
    delivery are kept as given; relation to earlier deliveries is the inbox's job."""
    return [normalize_item(scope, item) for item in items]


def derive_candidate(scope_key, fact_key):
    """Local fixture rule: first 16 bytes of SHA-256, hex. The alias table, not
    this rule, is the authority: a truncation collision is refused on insert."""
    digest = hashlib.sha256(canonical_json([scope_key, fact_key]).encode('utf-8')).digest()
    return digest[:16].hex()


class DictAliasStore:
    """In-memory alias store for tests that need no database."""

    def __init__(self):
        self.by_key = {}
        self.by_id = {}

    def get(self, scope_key, fact_key):
        return self.by_key.get((scope_key, fact_key))

    def get_by_id(self, scope_key, event_item_id):
        return self.by_id.get((scope_key, event_item_id))

    def put(self, scope_key, fact_key, event_item_id):
        self.by_key[(scope_key, fact_key)] = event_item_id
        self.by_id[(scope_key, event_item_id)] = fact_key


def resolve_alias(store, scope_key, fact_key, candidate_fn=derive_candidate):
    """Insert-or-return with a conflict check. Never overwrites a mapping."""
    known = store.get(scope_key, fact_key)
    if known is not None:
        return known
    candidate = candidate_fn(scope_key, fact_key)
    holder = store.get_by_id(scope_key, candidate)
    if holder is not None and holder != fact_key:
        raise AliasConflict()
    store.put(scope_key, fact_key, candidate)
    return candidate
