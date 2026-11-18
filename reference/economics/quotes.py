"""OrderLine, immutable quotes, free orders, discounts, bundles, multi-asset.

All calculation delegates to the unchanged ``kix:commerce:2`` contracts
(``reference/v0.3-rc1/commerce.py``); this module adds authentication and the
u128 -> fixture-money boundary check. It never narrows an amount: a quote whose
payable total exceeds the composed fixture layers' ``10**12`` money bound is
rejected, not rounded or silently converted (DEVELOPMENT_PLAN.md §11: u128 is
never silently narrowed).

One quote is single-asset (commerce ``MIXED_QUOTE_ASSETS`` is unchanged). A
multi-asset order is a list of per-asset quote groups; there is no FX here.
A bundle is several OrderLines in one quote. A free order is a quote whose
payable total is zero; it plans with zero legs and never enters the money
pipeline. Discounts are commerce FIXED/BPS rules with caller bearers; the
reference model invents no rule, rate or cap.
"""
import commerce
from assets import Amount
from common import Rejected
from mock_settlement import MONEY_MAX

from reference.economics import EconomicsLocalError


def order_line(line_id, inventory_id, asset, atoms):
    """One OrderLine: a commerce line document carrying an exact Amount.

    ``asset`` is the asset wire document, ``atoms`` a decimal string; both are
    validated by the frozen Amount wire constructor (no narrowing).
    """
    return dict(lineId=line_id, inventoryId=inventory_id,
                gross=Amount.from_dict({'asset': asset, 'atoms': atoms}).to_dict())


def payment_leg(leg_id, provider_ref, route_ref, asset, atoms):
    """One caller payment leg document; commerce validates the exact fields."""
    return dict(legId=leg_id, providerRef=provider_ref, routeRef=route_ref,
                amount=Amount.from_dict({'asset': asset, 'atoms': atoms}).to_dict())


def discount_rule(rule_id, bearer_ref, kind, value, eligible_line_ids, cap_atoms=None):
    """One caller discount rule; value/cap are decimal strings, never defaults."""
    return dict(ruleId=rule_id, bearerRef=bearer_ref, kind=kind, value=value,
                eligibleLineIds=list(eligible_line_ids), capAtoms=cap_atoms)


def quote_request(order_id, *, order_version, scope, policy_ref, expires_at,
                  lines, discounts=()):
    return dict(schemaVersion=commerce.SCHEMA, orderId=order_id,
                orderVersion=order_version, scope=dict(scope),
                policyRef=policy_ref, expiresAt=expires_at,
                lines=list(lines), discounts=list(discounts))


def _authenticate_request(assets, policies, request):
    """Authenticate the policy reference and every line asset before calculation.

    Malformed shapes are left to commerce's own field validation; anything that
    carries a policy reference or an asset must present an authenticated one.
    """
    if type(request) is not dict:
        raise EconomicsLocalError('QUOTE_REQUEST_REQUIRED')
    policy_ref = request.get('policyRef')
    if policy_ref is not None:
        policies.authenticate(policy_ref, 'QUOTE_PRICING')
    lines = request.get('lines')
    if type(lines) is list:
        for line in lines:
            if type(line) is dict and type(line.get('gross')) is dict:
                assets.authenticate(line['gross'].get('asset'))


def build_quote(assets, policies, request):
    _authenticate_request(assets, policies, request)
    return commerce.build_quote(request)


def validate_quote(assets, policies, quote):
    """Re-authenticate the embedded request, then commerce rebuild + compare."""
    if type(quote) is dict:
        _authenticate_request(assets, policies, quote.get('request'))
    return commerce.validate_quote(quote)


def plan_payments(assets, quote, legs, expected_quote_hash, now):
    if type(quote) is dict:
        assets.authenticate(quote.get('asset'))
    return commerce.plan_payments(quote, legs, expected_quote_hash, now)


def propose_line_refund(assets, quote, payment_plan, line_ids, expected_plan_hash):
    if type(quote) is dict:
        assets.authenticate(quote.get('asset'))
    return commerce.propose_line_refund(quote, payment_plan, line_ids,
                                        expected_plan_hash)


def is_free(quote):
    return quote['totals']['payableAtoms'] == '0'


def require_money_bound(quote):
    """Refuse, never narrow: the fixture money layers cap at MONEY_MAX.

    The quote itself stays valid u128 calculation evidence; only the binding
    into the Core/settlement fixture journey is refused above the bound.
    """
    payable = int(quote['totals']['payableAtoms'])
    if payable > MONEY_MAX:
        raise EconomicsLocalError('AMOUNT_EXCEEDS_FIXTURE_MONEY_BOUND')
    return payable


def require_leg_bound(amount_atoms):
    if amount_atoms > MONEY_MAX:
        raise EconomicsLocalError('AMOUNT_EXCEEDS_FIXTURE_MONEY_BOUND')
    return amount_atoms


def line_payable(quote, line_id):
    for row in quote['lines']:
        if row['lineId'] == line_id:
            return int(row['payableAtoms'])
    raise EconomicsLocalError('UNKNOWN_LINE')


__all__ = [
    'order_line', 'payment_leg', 'discount_rule', 'quote_request', 'build_quote',
    'validate_quote', 'plan_payments', 'propose_line_refund', 'is_free',
    'require_money_bound', 'require_leg_bound', 'line_payable',
    'MONEY_MAX', 'Rejected',
]