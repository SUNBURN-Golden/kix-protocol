"""Shared synthetic fixture harness for the economics reference tests.

Not a test module (no ``test_`` prefix); unittest discovery imports it as a
helper. Every value here is an explicit caller-supplied synthetic fixture, not
a product default: rates, caps, budgets and expiries are chosen for the test
scenario and labelled synthetic. Nothing reads a wall clock, the network or a
database. The harness only assembles inputs and drives the public session API.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assets import KRW, AssetSpec  # noqa: E402
from durable.budgets import BudgetSpec, ClassLimit  # noqa: E402
from reference.economics import (  # noqa: E402
    AssetAuthentication, EconomicsSession, PolicyAuthentication,
)
from reference.economics import quotes  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / 'fixtures'
KRW_WIRE = KRW.to_dict()
SCOPE = {'issuerId': 'issuer-1', 'eventId': 'event-scope-1', 'performanceId': 'perf-1'}
FAR_FUTURE = 9_999_999_999_999

# Standard synthetic policy set. The fee policy's residual payee equals the
# event organizer and its fee payee is 'platform', the composition binding the
# session enforces so FSM faces and Core PRIMARY allocations coincide.
FEE_BPS = 300
ORGANIZER = 'organizer-1'
PLATFORM = 'platform'
BUYER = 'buyer-1'


def token_wire(reference='fixture-token', decimals=0):
    return AssetSpec('synthetic', reference, decimals, 2**128 - 1).to_dict()


def make_assets(*wires):
    assets = AssetAuthentication()
    assets.register(KRW_WIRE)
    for wire in wires:
        assets.register(wire)
    return assets


def make_policies():
    policies = PolicyAuthentication()
    policies.register('pricing-1', 'QUOTE_PRICING', {'document': {'synthetic': True}})
    policies.register('fee-1', 'PRIMARY_FEE_BPS', {
        'kind': 'PRIMARY_FEE_BPS', 'fee_bps': FEE_BPS,
        'residual_payee': ORGANIZER, 'fee_payee': PLATFORM})
    policies.register('refund-1', 'REFUND_FROZEN_LINE_PRICE', {})
    policies.register('resale-1', 'RESALE_SPLIT_BPS', {
        'organizer_bps': 500, 'platform_bps': 300})
    return policies


def make_budgets(count=1000, nbytes=1_000_000, age_ms=3_600_000):
    limit = ClassLimit(count, nbytes, age_ms)
    return BudgetSpec(inflow=limit, observation=limit, completion=limit,
                      cancel=ClassLimit(100, 100_000, age_ms),
                      recovery=ClassLimit(100, 100_000, age_ms))


def make_session(*, assets=None, policies=None, budgets=None):
    return EconomicsSession(
        assets=assets if assets is not None else make_assets(),
        policies=policies if policies is not None else make_policies(),
        budgets=budgets if budgets is not None else make_budgets())


def event_policy(**over):
    policy = {'organizerRole': ORGANIZER, 'resaleCap': 20000,
              'resaleFeeBps': 300, 'resaleOrganizerBps': 500,
              'resaleAllowed': True, 'refundProfile': 'FULL_CHAIN_UNWIND_FIXTURE'}
    policy.update(over)
    return policy


def group(lines, legs, *, group_id='group-1', discounts=(), free=False, **over):
    member = {
        'groupId': group_id, 'policyRef': 'pricing-1', 'expiresAt': FAR_FUTURE,
        'lines': list(lines), 'discounts': list(discounts), 'legs': list(legs),
        'settlementPolicyRef': None if free else 'fee-1',
        'eventPolicy': None if free else event_policy(),
        'buyer': BUYER, 'debtorRole': None if free else BUYER,
        'paymentId': None if free else 'pay-' + group_id,
    }
    member.update(over)
    return member


def krw_line(line_id, atoms, inventory_id=None):
    return quotes.order_line(line_id, inventory_id or ('inv-' + line_id), KRW_WIRE, str(atoms))


def krw_leg(leg_id, atoms, *, provider='provider-1', route='route-card'):
    return quotes.payment_leg(leg_id, provider, route, KRW_WIRE, str(atoms))


def authorization(proposal):
    return {key: 'evidence-' + key for key in proposal['requiredEvidence']}


def load_fixture(name):
    with open(FIXTURES / name, encoding='utf-8') as handle:
        return json.load(handle)


def capture_and_confirm(session, order_id, group_id, leg_id, capture_id,
                        amount, *, now_ms=1000, buyer=BUYER, nonce=None):
    submitted = session.submit_capture(
        order_id, group_id, leg_id, capture_id, amount=amount, buyer=buyer,
        nonce=nonce if nonce is not None else 'nonce-' + capture_id, now_ms=now_ms)
    assert submitted['outcome'] == 'new_success', submitted
    completed = session.complete_capture(
        capture_id, outcome='CONFIRMED', source_id='src-' + capture_id, now_ms=now_ms + 1)
    assert completed['outcome'] == 'completed', completed
    return submitted


def settle(session, order_id, group_id, *, movement_id='mv-1', key='settle-1'):
    return session.settle_group(order_id, group_id, movement_id=movement_id,
                                idempotency_key=key)


def primary_order(session, *, lines=None, legs=None, order_id='order-1',
                  now_ms=1000, **group_over):
    lines = lines if lines is not None else [krw_line('line-1', 10000)]
    legs = legs if legs is not None else [krw_leg('leg-1', 10000)]
    return session.create_order(order_id, order_version=1, scope=SCOPE,
                                groups=[group(lines, legs, **group_over)], now_ms=now_ms)