"""Pure admission decision for the durable business unit. No I/O, no psycopg.

One command is one atomic unit: identity, payload sha256, first result,
reservation slot, minimal order and an external intent. Replay returns the
stored first result and adds nothing. A conflicting payload for an existing
command id is retained as separate evidence. Capacity writes nothing.
The amounts are decimal strings (u128), never narrowed to a signed integer.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional

from readiness.codec import canonical_json

U128_MAX = (1 << 128) - 1
INTENT_KIND = 'FIXTURE_NOT_DISPATCHED'
_AMOUNT = re.compile(r'^[0-9]{1,40}$')


def validate_amount(text):
    if not isinstance(text, str) or _AMOUNT.fullmatch(text) is None:
        raise ValueError('amount must be a decimal string')
    if int(text) > U128_MAX:
        raise ValueError('amount exceeds u128')
    return text


@dataclass(frozen=True)
class Command:
    command_id: str
    show_id: str
    slot: str
    amount_u128: str
    buyer: str
    payload_nonce: str

    def __post_init__(self):
        validate_amount(self.amount_u128)
        for name in ('command_id', 'show_id', 'slot', 'buyer'):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError('command identity')
        if not isinstance(self.payload_nonce, str):
            raise ValueError('command identity')


def payload_body(command):
    return {
        'showId': command.show_id,
        'commandId': command.command_id,
        'slot': command.slot,
        'buyer': command.buyer,
        'amountU128': command.amount_u128,
        'nonce': command.payload_nonce,
        'chainWriter': False,
    }


def payload_canonical(command):
    return canonical_json(payload_body(command))


def payload_sha256(command):
    return hashlib.sha256(payload_canonical(command).encode('utf-8')).hexdigest()


def payload_nbytes(command):
    return len(payload_canonical(command).encode('utf-8'))


def first_result_canonical(outcome, command, *, order_id, intent_id):
    return canonical_json({
        'localDurableData': True,
        'protocolTruth': False,
        'productionConformance': False,
        'productionReadiness': False,
        'productionEndpoint': False,
        'fundsExecuted': False,
        'chainWriter': False,
        'outcome': outcome,
        'commandId': command.command_id,
        'showId': command.show_id,
        'slot': command.slot if outcome == 'new_success' else None,
        'orderId': order_id,
        'orderAmountU128': command.amount_u128 if order_id else None,
        'externalIntentId': intent_id,
        'externalIntentKind': INTENT_KIND if intent_id else None,
    })


@dataclass
class Usage:
    count: int = 0
    nbytes: int = 0
    oldest_open_ms: Optional[int] = None


@dataclass
class Snapshot:
    """What the decision reads: the existing row for this command, the slot
    holder, whether this exact conflicting payload was already retained, and
    the per-class usage."""

    existing: Optional[dict] = None
    slot_holder: Optional[str] = None
    conflict_retained: bool = False
    usage: dict = field(default_factory=dict)

    def usage_of(self, budget_class):
        return self.usage.get(budget_class) or Usage()


@dataclass
class Decision:
    outcome: str
    budget_class: Optional[str] = None
    store_command: bool = False
    store_slot: bool = False
    store_order: bool = False
    store_intent: bool = False
    store_observation: bool = False
    nbytes: int = 0
    first_result: str = ''
    order_id: Optional[str] = None
    intent_id: Optional[str] = None
    observation_id: Optional[str] = None
    capacity_class: Optional[str] = None
    capacity_reason: Optional[str] = None

    @property
    def writes(self):
        return (
            self.store_command or self.store_slot or self.store_order
            or self.store_intent or self.store_observation
        )


def _capacity(spec, snapshot, budget_class, nbytes, now_ms):
    usage = snapshot.usage_of(budget_class)
    code, reason = spec.check(
        budget_class,
        used_count=usage.count,
        used_bytes=usage.nbytes,
        oldest_open_ms=usage.oldest_open_ms,
        now_ms=now_ms,
        extra_bytes=nbytes,
    )
    if code == 'OK':
        return None
    return Decision(outcome='capacity', capacity_class=budget_class, capacity_reason=reason)


def decide(snapshot, command, spec, now_ms):
    digest = payload_sha256(command)
    existing = snapshot.existing
    if existing is not None:
        if existing['payload_sha256'] == digest:
            return Decision(outcome='replayed', first_result=existing['first_result'])
        if snapshot.conflict_retained:
            return Decision(outcome='conflict_retained', first_result=existing['first_result'])
        nbytes = payload_nbytes(command)
        refused = _capacity(spec, snapshot, 'observation', nbytes, now_ms)
        if refused is not None:
            return refused
        return Decision(
            outcome='conflict_retained',
            budget_class='observation',
            store_observation=True,
            nbytes=nbytes,
            first_result=existing['first_result'],
            observation_id='obs-' + command.command_id + '-' + digest,
        )
    nbytes = payload_nbytes(command)
    refused = _capacity(spec, snapshot, 'inflow', nbytes, now_ms)
    if refused is not None:
        return refused
    if snapshot.slot_holder is not None:
        return Decision(
            outcome='business_rejected',
            budget_class='inflow',
            store_command=True,
            nbytes=nbytes,
            first_result=first_result_canonical(
                'business_rejected', command, order_id=None, intent_id=None,
            ),
        )
    order_id = 'order-' + command.command_id
    intent_id = 'intent-' + command.command_id
    return Decision(
        outcome='new_success',
        budget_class='inflow',
        store_command=True,
        store_slot=True,
        store_order=True,
        store_intent=True,
        nbytes=nbytes,
        first_result=first_result_canonical(
            'new_success', command, order_id=order_id, intent_id=intent_id,
        ),
        order_id=order_id,
        intent_id=intent_id,
    )
