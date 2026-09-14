"""P0/P2 calculation contracts. No payment, issuance or refund authorization.

Snapshots are recomputed before use. Hashes bind calculations, not the truth of
an external payment or the identity/authority of the snapshot's author.
Schema 2 orderVersion uses positive u32 Version. expiresAt, now and checkedAt
are Unix milliseconds, restricted to CE1's safe JSON integer range.
"""
import json

from assets import AssetRegistry, AssetSpec, Amount
from canonical_encoding import canonical, digest, machine_id
from common import require
from execution_contracts import TimestampMs, Version

SCHEMA = 'kix:commerce:2'
QUOTE_HASH_DOMAIN = 'kix:quote:2'
PAYMENT_PLAN_HASH_DOMAIN = 'kix:payment-plan:2'
REFUND_PROPOSAL_HASH_DOMAIN = 'kix:line-refund-proposal:2'
MAX_LINES = 300
MAX_RULES = 64
MAX_LEGS = 16


def fields(value, names):
    require(type(value) is dict, 'OBJECT_REQUIRED')
    require(all(type(key) is str for key in value), 'STRING_FIELDS_REQUIRED')
    expected = set(names.split())
    require(set(value) == expected, 'INVALID_FIELDS:' + ','.join(sorted(set(value) ^ expected)))


def ident(value):
    return machine_id(value)


def integer(value, minimum=0, maximum=2**53-1):
    require(type(value) is int and minimum <= value <= maximum, 'INVALID_COUNTER')
    return value


def timestamp_ms(value, minimum=0):
    """Explicit typed conversion from this schema's safe-number wire profile."""
    return TimestampMs(integer(value, minimum)).value


def atoms(value, maximum):
    require(type(value) is str and value.isascii() and value.isdecimal()
            and (value == '0' or not value.startswith('0'))
            and len(value) <= 39, 'CANONICAL_ATOMS_REQUIRED')
    result = int(value)
    require(result <= maximum, 'AMOUNT_OVERFLOW')
    return result


def identifiers(values, maximum):
    require(type(values) is list and 0 < len(values) <= maximum, 'INVALID_ID_LIST')
    checked = [ident(value) for value in values]
    require(len(set(checked)) == len(checked), 'DUPLICATE_ID')
    return checked


def proportional(total, capacities):
    """Exact largest-remainder allocation, line ID ascending breaks ties.

    Integer ratios avoid floats. For total <= sum(capacities), no allocation
    exceeds a line's capacity. Input dictionary insertion order is irrelevant.
    """
    require(type(total) is int and total >= 0, 'INVALID_ALLOCATION_TOTAL')
    require(type(capacities) is dict, 'INVALID_CAPACITIES')
    for key in capacities: ident(key)
    require(all(type(v) is int and v >= 0 for v in capacities.values()), 'INVALID_CAPACITY')
    size = sum(capacities.values())
    require(total <= size, 'ALLOCATION_EXCEEDS_CAPACITY')
    if size == 0:
        return {key: 0 for key in sorted(capacities)}
    divided = {key: divmod(total * value, size) for key, value in capacities.items()}
    allocated = {key: divided[key][0] for key in sorted(divided)}
    residual = total - sum(allocated.values())
    for key in sorted(divided, key=lambda key: (-divided[key][1], key))[:residual]:
        allocated[key] += 1
    return allocated


def build_quote(request):
    fields(request, 'schemaVersion orderId orderVersion scope policyRef expiresAt lines discounts')
    require(request['schemaVersion'] == SCHEMA, 'UNSUPPORTED_COMMERCE_SCHEMA')
    ident(request['orderId']); ident(request['policyRef'])
    Version(integer(request['orderVersion'], 1))
    timestamp_ms(request['expiresAt'], 1)
    fields(request['scope'], 'issuerId eventId performanceId')
    for value in request['scope'].values(): ident(value)
    require(type(request['lines']) is list and 0 < len(request['lines']) <= MAX_LINES, 'INVALID_LINES')
    require(type(request['discounts']) is list and len(request['discounts']) <= MAX_RULES, 'INVALID_DISCOUNTS')
    registry = AssetRegistry()
    rows = {}; asset = None; inventory = set()
    for line in request['lines']:
        fields(line, 'lineId inventoryId gross')
        line_id = ident(line['lineId']); unit = ident(line['inventoryId'])
        require(line_id not in rows, 'DUPLICATE_LINE')
        require(unit not in inventory, 'DUPLICATE_INVENTORY')
        inventory.add(unit)
        money = Amount.from_dict(line['gross']); registry.register(money.asset)
        if asset is None: asset = money.asset
        require(money.asset == asset, 'MIXED_QUOTE_ASSETS')
        rows[line_id] = dict(lineId=line_id, inventoryId=unit, grossAtoms=money.atoms,
                             discountAtoms=0, payableAtoms=money.atoms, discounts=[])
    gross = sum(row['grossAtoms'] for row in rows.values())
    Amount(asset, gross)  # Per-asset aggregate bound, not only per-line bound.
    seen_rules = set()
    for rule in request['discounts']:
        fields(rule, 'ruleId bearerRef kind value eligibleLineIds capAtoms')
        rule_id = ident(rule['ruleId']); ident(rule['bearerRef'])
        require(rule_id not in seen_rules, 'DUPLICATE_DISCOUNT_RULE')
        seen_rules.add(rule_id)
        eligible = identifiers(rule['eligibleLineIds'], MAX_LINES)
        require(set(eligible) <= set(rows), 'UNKNOWN_DISCOUNT_LINE')
        remaining = {key: rows[key]['payableAtoms'] for key in eligible}
        basis = sum(remaining.values())
        require(rule['kind'] in ('FIXED', 'BPS'), 'UNSUPPORTED_DISCOUNT_KIND')
        value = atoms(rule['value'], 10000 if rule['kind'] == 'BPS' else asset.max_atoms)
        discount = basis * value // 10000 if rule['kind'] == 'BPS' else value
        if rule['capAtoms'] is not None:
            discount = min(discount, atoms(rule['capAtoms'], asset.max_atoms))
        require(discount <= basis, 'DISCOUNT_EXCEEDS_PAYABLE')
        for key, assigned in proportional(discount, remaining).items():
            rows[key]['discountAtoms'] += assigned
            rows[key]['payableAtoms'] -= assigned
            if assigned:
                rows[key]['discounts'].append(dict(ruleId=rule_id, bearerRef=rule['bearerRef'], atoms=str(assigned)))
    result_rows = []
    for key in sorted(rows):
        row = dict(rows[key])
        for field in ('grossAtoms', 'discountAtoms', 'payableAtoms'): row[field] = str(row[field])
        result_rows.append(row)
    # A CE1 JSON round trip severs aliases to mutable caller input.
    result = dict(schemaVersion=SCHEMA, evidenceClass='CALCULATION_ONLY',
                  request=json.loads(canonical(request)), asset=asset.to_dict(),
                  lines=result_rows,
                  totals=dict(grossAtoms=str(gross),
                              discountAtoms=str(sum(r['discountAtoms'] for r in rows.values())),
                              payableAtoms=str(sum(r['payableAtoms'] for r in rows.values()))))
    result['quoteHash'] = digest(QUOTE_HASH_DOMAIN, result)
    return result


def validate_quote(quote):
    require(type(quote) is dict and 'request' in quote, 'INVALID_QUOTE')
    require(quote.get('schemaVersion') == SCHEMA, 'UNSUPPORTED_COMMERCE_SCHEMA')
    rebuilt = build_quote(quote['request'])
    require(canonical(quote) == canonical(rebuilt), 'QUOTE_CONTENT_MISMATCH')
    return rebuilt


def plan_payments(quote, legs, expected_quote_hash, now):
    quote = validate_quote(quote)
    require(type(expected_quote_hash) is str and quote['quoteHash'] == expected_quote_hash, 'STALE_QUOTE')
    timestamp_ms(now)
    require(now < quote['request']['expiresAt'], 'QUOTE_EXPIRED')
    require(type(legs) is list and len(legs) <= MAX_LEGS, 'INVALID_PAYMENT_LEGS')
    asset = AssetSpec.from_dict(quote['asset'])
    checked = []; seen = set()
    for leg in legs:
        fields(leg, 'legId providerRef routeRef amount')
        leg_id = ident(leg['legId']); ident(leg['providerRef']); ident(leg['routeRef'])
        require(leg_id not in seen, 'DUPLICATE_PAYMENT_LEG'); seen.add(leg_id)
        money = Amount.from_dict(leg['amount'])
        require(money.asset == asset, 'PAYMENT_ASSET_MISMATCH')
        require(money.atoms > 0, 'EMPTY_PAYMENT_LEG')
        checked.append((leg, money))
    require(sum(money.atoms for _, money in checked) == int(quote['totals']['payableAtoms']), 'PAYMENT_TOTAL_MISMATCH')
    remaining = {row['lineId']: int(row['payableAtoms']) for row in quote['lines']}
    output_legs = []
    for leg, money in checked:
        assigned = proportional(money.atoms, remaining)
        for key, value in assigned.items(): remaining[key] -= value
        output_legs.append(dict(legId=leg['legId'], providerRef=leg['providerRef'], routeRef=leg['routeRef'],
                                amount=money.to_dict(), allocations={key: str(value) for key, value in assigned.items()}))
    require(not any(remaining.values()), 'UNALLOCATED_PAYMENT')
    result = dict(schemaVersion=SCHEMA, evidenceClass='CALCULATION_ONLY', quoteHash=quote['quoteHash'],
                  checkedAt=now, legs=output_legs)
    result['planHash'] = digest(PAYMENT_PLAN_HASH_DOMAIN, result)
    return result


def validate_payment_plan(quote, plan):
    fields(plan, 'schemaVersion evidenceClass quoteHash checkedAt legs planHash')
    require(plan['schemaVersion'] == SCHEMA, 'UNSUPPORTED_COMMERCE_SCHEMA')
    require(type(plan['legs']) is list, 'INVALID_PAYMENT_LEGS')
    legs = []
    for leg in plan['legs']:
        fields(leg, 'legId providerRef routeRef amount allocations')
        legs.append({key: value for key, value in leg.items() if key != 'allocations'})
    rebuilt = plan_payments(quote, legs, plan['quoteHash'], plan['checkedAt'])
    require(canonical(plan) == canonical(rebuilt), 'PAYMENT_PLAN_CONTENT_MISMATCH')
    return rebuilt


def propose_line_refund(quote, payment_plan, line_ids, expected_plan_hash):
    """Full selected-line reversal calculation under an explicit frozen policy.

    No repricing of retained lines. Does not assert payment capture, issuance
    failure, refundable capacity or authority. The execution layer must prove
    these and reserve them; repeating this proposal never means paying twice.
    """
    quote = validate_quote(quote)
    plan = validate_payment_plan(quote, payment_plan)
    require(type(expected_plan_hash) is str and plan['planHash'] == expected_plan_hash, 'STALE_PAYMENT_PLAN')
    selected = identifiers(line_ids, MAX_LINES)
    rows = {row['lineId']: row for row in quote['lines']}
    require(set(selected) <= set(rows), 'UNKNOWN_REFUND_LINE')
    asset = AssetSpec.from_dict(quote['asset'])
    routes = []
    for leg in plan['legs']:
        assigned = {key: leg['allocations'][key] for key in sorted(selected)}
        total = sum(int(value) for value in assigned.values())
        if total:
            routes.append(dict(legId=leg['legId'], providerRef=leg['providerRef'], routeRef=leg['routeRef'],
                               amount=Amount(asset, total).to_dict(), allocations=assigned))
    burdens = {}
    for key in selected:
        for discount in rows[key]['discounts']:
            bearer = discount['bearerRef']
            burdens[bearer] = burdens.get(bearer, 0) + int(discount['atoms'])
    customer = sum(int(rows[key]['payableAtoms']) for key in selected)
    gross = sum(int(rows[key]['grossAtoms']) for key in selected)
    require(customer + sum(burdens.values()) == gross, 'REFUND_CONSERVATION_FAILED')
    result = dict(schemaVersion=SCHEMA, evidenceClass='CALCULATION_ONLY',
                  policy='FROZEN_LINE_PRICE_FULL_REVERSAL_V1', quoteHash=quote['quoteHash'], planHash=plan['planHash'],
                  lineIds=sorted(selected), grossReversed=Amount(asset, gross).to_dict(),
                  customerRefund=Amount(asset, customer).to_dict(), originalRoutes=routes,
                  discountBurdenReversal={key: str(burdens[key]) for key in sorted(burdens)},
                  executionAuthorized=False,
                  requiredEvidence=['CONFIRMED_ORIGINAL_PAYMENTS', 'CURRENT_LINE_RIGHT_STATE',
                                    'REFUND_POLICY_AUTHORITY', 'UNRESOLVED_REFUND_RESERVATIONS',
                                    'CURRENT_PROVIDER_REFUNDABLE_CAPACITY'])
    result['proposalHash'] = digest(REFUND_PROPOSAL_HASH_DOMAIN, result)
    return result
