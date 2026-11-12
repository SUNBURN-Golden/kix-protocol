"""Distribution and synthetic payouts; the resale seller payout journey.

Primary distribution is the adopted W0 posture: the caller supplies the payee
order; the settlement FSM freezes it on first application. R0 (a canonical
payee order) stays UNDETERMINED — no default order exists here. Payouts are
the published ``BANK_PAYOUT_FIXTURE`` effect over the unchanged Core: an
allocation-bound local intent, then explicit STATUS/FUNDS observations. Faces
are never invented: they come from the settlement obligations / Core
allocations, and every payout amount is checked against both.

Resale seller payout (BRA-OPEN-ITEMS-DRAFT-0.2 option A mock boundary):
``seller_due`` in the resale FSM evidence is a face, not a payout. This module
composes a separate synthetic journey that binds the BRA faces to Core RESALE
allocations (identical floor-division arithmetic) and pays them through
published PAYOUT effects. The resale split stays outside F01 (S0): no
settlement FSM case is created for resale. The BRA machine itself is unchanged
and still reports ``funds_executed=False``.

Every rate, cap, expiry and amount is caller fixture input. All ids are
derived with full domain digests; nothing is truncated. The resale journey's
``primary.slot`` is a 0-based integer (the BRA gate's native seat index); the
Core seat string is ``str(slot)``. The caller's ``expiresMs``/``rightExpiresMs``
must fall inside the unchanged BRA offer window (``now < expires <= now +
900000`` ms); the BRA enforces that fail-closed and this module does not relax
or re-default it.
"""
import re

from common import Rejected, ident, inventory_id
from finance import ROUTES
from lifecycle import REFUND_PROFILES
from mock_gates import _allocation
from mock_settlement import MONEY_MAX

from reference.economics import EVIDENCE_CLASS, FLAGS, EconomicsLocalError

_HEX64 = re.compile(r'[0-9a-f]{64}\Z')
PAYOUT_ROUTE = 'BANK_PAYOUT_FIXTURE'


def _ident(value, label):
    try:
        return ident(value)
    except Rejected:
        raise EconomicsLocalError('JOURNEY_ID_INVALID:' + label) from None


def _money(value, label):
    if type(value) is not int or isinstance(value, bool) or not 0 < value <= MONEY_MAX:
        raise EconomicsLocalError('JOURNEY_AMOUNT_INVALID:' + label)
    return value


def _bps(value, label):
    if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 10000:
        raise EconomicsLocalError('JOURNEY_BPS_INVALID:' + label)
    return value


def _hex64(value, label):
    if type(value) is not str or _HEX64.fullmatch(value) is None:
        raise EconomicsLocalError('JOURNEY_PAYMENT_REF_INVALID:' + label)
    return value


def _op(journey_id, step):
    from common import digest
    return 'op-' + digest([journey_id, step])


class PayoutDesk:
    """W0 distribution plus allocation-bound PAYOUT effects and observations."""

    def __init__(self, core, effects, settlement):
        self._core = core
        self._effects = effects
        self._settlement = settlement

    def distribute(self, settlement_id, *, order, idempotency_key):
        return self._settlement.distribute(
            settlement_id, idempotency_key=idempotency_key, order=order)

    def prepare_payout(self, *, trade_id, effect_id, payee, amount, operation_id):
        if type(amount) is not int or isinstance(amount, bool) or not 0 < amount <= MONEY_MAX:
            raise EconomicsLocalError('PAYOUT_AMOUNT_INVALID')
        snapshot = self._core.snapshot()
        trade = snapshot['trades'].get(trade_id)
        if trade is None:
            raise EconomicsLocalError('PAYOUT_TRADE_NOT_FOUND')
        event = snapshot['events'][trade['event']]
        if event['status'] != 'COMPLETED':
            raise EconomicsLocalError('PAYOUT_EVENT_NOT_COMPLETED')
        if trade['status'] != 'COMMITTED' or trade['reversalRequested']:
            raise EconomicsLocalError('PAYOUT_TRADE_NOT_PAYABLE')
        if effect_id in snapshot['effects']:
            raise EconomicsLocalError('PAYOUT_EFFECT_EXISTS')
        allocation = next((a for a in trade['allocations']
                           if a['payee'] == payee), None)
        if allocation is None:
            raise EconomicsLocalError('PAYOUT_ALLOCATION_NOT_FOUND')
        reserved = sum(x['amount'] - x['appliedAmount']
                       for x in snapshot['effects'].values()
                       if x['kind'] == 'PAYOUT'
                       and x['allocation'] == allocation['id']
                       and x['state'] not in ('DONE', 'ABORTED', 'FAILED_FENCED',
                                              'PARTIALLY_FINALIZED'))
        if amount > allocation['amount'] - allocation['paid'] - reserved:
            raise EconomicsLocalError('PAYOUT_EXCEEDS_ALLOCATION')
        body = {'domain': self._core.DOMAIN, 'effectId': effect_id,
                'tradeId': trade_id, 'kind': 'PAYOUT', 'amount': amount,
                'allocationId': allocation['id'],
                'routeProfile': PAYOUT_ROUTE,
                'contractRef': ROUTES[PAYOUT_ROUTE]['contract'],
                'beneficiaryAccountRef': 'fixture-account:' + payee}
        prepared = self._effects.execute(operation_id, 'operator',
                                         'prepare_effect', body)
        return {'effectId': effect_id, 'allocationId': allocation['id'],
                'payee': payee, 'amount': amount,
                'idempotencyKey': prepared['result']['idempotencyKey']}

    def send(self, effect_id, *, operation_id):
        return self._effects.execute(operation_id, 'operator', 'send_effect',
                                     {'domain': self._core.DOMAIN,
                                      'effectId': effect_id})['result']

    def observe(self, effect_id, *, phase, source_id, amount,
                provider_operation_id=None, status=None, movement_id=None,
                fence_ref=None, fence_provenance=None, operation_id=None):
        """One explicit observation; binding fields come from the stored effect."""
        snapshot = self._core.snapshot()
        effect = snapshot['effects'].get(effect_id)
        if effect is None:
            raise EconomicsLocalError('OBSERVE_EFFECT_NOT_FOUND')
        body = {'domain': self._core.DOMAIN, 'scope': dict(self._core.SCOPE),
                'provenance': 'synthetic', 'effectId': effect_id,
                'phase': phase, 'sourceId': source_id,
                'providerOperationId': provider_operation_id or 'provider-' + effect_id,
                'amount': amount, 'currency': 'KRW',
                'beneficiary': effect['beneficiary'],
                'paymentId': effect['paymentId']}
        if status is not None:
            body['status'] = status
        if movement_id is not None:
            body['movementId'] = movement_id
        if fence_ref is not None:
            body['fenceRef'] = fence_ref
        if fence_provenance is not None:
            body['fenceProvenance'] = fence_provenance
        return self._effects.execute(operation_id or _op(effect_id, 'observe:' + source_id),
                                     'pg-adapter', 'observe_effect', body)['result']


_SHOW_FIELDS = {'showId', 'organizerRole', 'capacity', 'gateRoles',
                'primaryPrice', 'resaleCap', 'resaleAllowed', 'primaryFeeBps',
                'organizerBps', 'platformBps'}
_PRIMARY_FIELDS = {'rightId', 'slot', 'sellerRole', 'paymentId'}
_RESALE_FIELDS = {'listingId', 'transferId', 'buyerRole', 'amount',
                  'paymentRef', 'expiresMs', 'rightExpiresMs'}
_JOURNEY_FIELDS = {'journeyId', 'refundProfile', 'show', 'primary', 'resale',
                   'payouts'}


def _validate_journey(journey, now_ms):
    if type(journey) is not dict or set(journey) != _JOURNEY_FIELDS:
        raise EconomicsLocalError('JOURNEY_FIELDS_INVALID')
    journey_id = _ident(journey['journeyId'], 'journeyId')
    if journey['refundProfile'] not in REFUND_PROFILES:
        raise EconomicsLocalError('JOURNEY_REFUND_PROFILE_INVALID')
    show, primary, resale = journey['show'], journey['primary'], journey['resale']
    if type(show) is not dict or set(show) != _SHOW_FIELDS:
        raise EconomicsLocalError('JOURNEY_SHOW_FIELDS_INVALID')
    if type(primary) is not dict or set(primary) != _PRIMARY_FIELDS:
        raise EconomicsLocalError('JOURNEY_PRIMARY_FIELDS_INVALID')
    if type(resale) is not dict or set(resale) != _RESALE_FIELDS:
        raise EconomicsLocalError('JOURNEY_RESALE_FIELDS_INVALID')
    for name in ('showId', 'organizerRole'):
        _ident(show[name], name)
    if type(show['capacity']) is not int or show['capacity'] <= 0:
        raise EconomicsLocalError('JOURNEY_CAPACITY_INVALID')
    gates = show['gateRoles']
    if type(gates) is not list or not gates:
        raise EconomicsLocalError('JOURNEY_GATE_ROLES_INVALID')
    for gate in gates:
        _ident(gate, 'gateRole')
    primary_price = _money(show['primaryPrice'], 'primaryPrice')
    resale_cap = _money(show['resaleCap'], 'resaleCap')
    if show['resaleAllowed'] is not True:
        raise EconomicsLocalError('JOURNEY_RESALE_NOT_ALLOWED')
    _bps(show['primaryFeeBps'], 'primaryFeeBps')
    organizer_bps = _bps(show['organizerBps'], 'organizerBps')
    platform_bps = _bps(show['platformBps'], 'platformBps')
    if organizer_bps + platform_bps > 10000:
        raise EconomicsLocalError('JOURNEY_SPLIT_EXCEEDS_BASIS')
    for name in ('rightId', 'sellerRole'):
        _ident(primary[name], name)
    if (type(primary['slot']) is not int or isinstance(primary['slot'], bool)
            or not 0 <= primary['slot'] < show['capacity']):
        raise EconomicsLocalError('JOURNEY_SLOT_INVALID')
    _hex64(primary['paymentId'], 'primary.paymentId')
    for name in ('listingId', 'transferId', 'buyerRole'):
        _ident(resale[name], name)
    amount = _money(resale['amount'], 'resale.amount')
    if amount > resale_cap:
        raise EconomicsLocalError('JOURNEY_RESALE_EXCEEDS_CAP')
    _hex64(resale['paymentRef'], 'resale.paymentRef')
    for name in ('expiresMs', 'rightExpiresMs'):
        if type(resale[name]) is not int or resale[name] <= now_ms:
            raise EconomicsLocalError('JOURNEY_EXPIRY_INVALID:' + name)
    seller, organizer = primary['sellerRole'], show['organizerRole']
    buyer = resale['buyerRole']
    if len({seller, organizer, buyer, 'platform'}) != 4:
        raise EconomicsLocalError('JOURNEY_ROLES_NOT_DISTINCT')
    organizer_due, platform_due, seller_due = _allocation(
        amount, organizer_bps, platform_bps)
    faces = {seller: seller_due, organizer: organizer_due, 'platform': platform_due}
    payouts = journey['payouts']
    if type(payouts) is not list or not payouts:
        raise EconomicsLocalError('JOURNEY_PAYOUTS_INVALID')
    seen_effects, per_payee = set(), {}
    for payout in payouts:
        if type(payout) is not dict or set(payout) != {'effectId', 'payee', 'amount'}:
            raise EconomicsLocalError('JOURNEY_PAYOUT_FIELDS_INVALID')
        effect_id = _ident(payout['effectId'], 'payout.effectId')
        if effect_id in seen_effects:
            raise EconomicsLocalError('JOURNEY_PAYOUT_EFFECT_DUPLICATE')
        seen_effects.add(effect_id)
        payee = payout['payee']
        if payee not in faces:
            raise EconomicsLocalError('JOURNEY_PAYOUT_PAYEE_UNKNOWN')
        value = _money(payout['amount'], 'payout.amount')
        per_payee[payee] = per_payee.get(payee, 0) + value
        if per_payee[payee] > faces[payee]:
            raise EconomicsLocalError('JOURNEY_PAYOUT_EXCEEDS_FACE')
    return faces


def resale_seller_payout(core, effects, resale_machine, journey, *, now_ms):
    """One composed synthetic resale journey: BRA faces -> Core allocations ->
    published PAYOUT effects. Pre-validated, then applied in a fixed order.

    The BRA evidence faces and the Core RESALE allocations use the same
    floor-division split; both equalities are verified fail-closed. No
    settlement FSM case is created (S0: the resale split is outside F01).
    """
    if type(now_ms) is not int or isinstance(now_ms, bool) or now_ms < 0:
        raise EconomicsLocalError('JOURNEY_TIME_INVALID')
    faces = _validate_journey(journey, now_ms)
    journey_id = journey['journeyId']
    show, primary, resale = journey['show'], journey['primary'], journey['resale']
    snapshot = core.snapshot()
    for payout in journey['payouts']:
        if payout['effectId'] in snapshot['effects']:
            raise EconomicsLocalError('JOURNEY_EFFECT_EXISTS')
    domain, scope = core.DOMAIN, dict(core.SCOPE)
    event_id = 'ev-' + _op(journey_id, 'show')[3:]
    primary_trade = 't-' + _op(journey_id, 'primary')[3:]
    resale_trade = 't-' + _op(journey_id, 'resale')[3:]
    seat = str(primary['slot'])
    seat_inventory = inventory_id(show['organizerRole'], event_id, 'main', seat)

    def run(step, actor, action, body):
        return core.execute(_op(journey_id, step), actor, action, body)['result']

    # 1. Primary purchase by the future seller (one seat, full fixture price).
    created = run('primary-create', 'operator', 'create_event', {
        'domain': domain, 'eventId': event_id,
        'organizer': show['organizerRole'],
        'policy': {'primaryPrice': show['primaryPrice'],
                   'resaleCap': show['resaleCap'],
                   'primaryFeeBps': show['primaryFeeBps'],
                   'resaleFeeBps': show['platformBps'],
                   'resaleOrganizerBps': show['organizerBps'],
                   'resaleAllowed': True,
                   'refundProfile': journey['refundProfile']},
        'seats': [seat]})
    if created['inventoryIds'] != [seat_inventory]:
        raise EconomicsLocalError('JOURNEY_INVENTORY_BINDING_MISMATCH')
    prepared = run('primary-prepare', primary['sellerRole'], 'prepare_trade', {
        'domain': domain, 'tradeId': primary_trade,
        'inventoryId': seat_inventory, 'expectedInventoryVersion': 0,
        'buyer': primary['sellerRole'], 'amount': show['primaryPrice'],
        'expectedVersion': 0})
    run('primary-capture', 'pg-adapter', 'capture', {
        'domain': domain, 'scope': scope, 'provenance': 'synthetic',
        'tradeId': primary_trade, 'orderId': prepared['externalOrderId'],
        'paymentId': primary['paymentId'], 'amount': show['primaryPrice'],
        'currency': 'KRW', 'buyer': primary['sellerRole']})
    movement = 'mv-' + _op(journey_id, 'primary-deposit')[3:]
    run('primary-settle', 'pg-adapter', 'settle_capture', {
        'domain': domain, 'scope': scope, 'provenance': 'synthetic',
        'tradeId': primary_trade, 'paymentId': primary['paymentId'],
        'amount': show['primaryPrice'], 'grossAmount': show['primaryPrice'],
        'feeAmount': 0, 'taxAmount': 0, 'heldAmount': 0, 'adjustmentAmount': 0,
        'feeBearer': 'platform', 'contractRef': 'fixture:settlement:v1',
        'movementId': movement, 'sourceId': movement, 'currency': 'KRW'})
    run('primary-commit', 'operator', 'commit_trade',
        {'domain': domain, 'tradeId': primary_trade})

    # 2. BRA issuance evidence, listing, payment fact and acceptance (unchanged).
    resale_machine.set_clock('clock',
                             idempotency_key=_op(journey_id, 'clock'),
                             now_ms=now_ms)
    resale_machine.adopt_issued(primary['rightId'],
        idempotency_key=_op(journey_id, 'adopt'),
        show_id=show['showId'], organizer_role=show['organizerRole'],
        capacity=show['capacity'], gate_roles=list(show['gateRoles']),
        primary_price=show['primaryPrice'], resale_cap=show['resaleCap'],
        resale_allowed=True, organizer_bps=show['organizerBps'],
        platform_bps=show['platformBps'], slot=primary['slot'],
        buyer_role=primary['sellerRole'], expires_ms=resale['rightExpiresMs'],
        order_id=prepared['externalOrderId'], amount=show['primaryPrice'],
        payment_ref=primary['paymentId'])
    resale_machine.list_resale(resale['listingId'],
        idempotency_key=_op(journey_id, 'list'), right_id=primary['rightId'],
        version=1, seller_role=primary['sellerRole'],
        recipient_role=resale['buyerRole'], amount=resale['amount'],
        expires_ms=resale['expiresMs'])
    resale_machine.observe_resale_payment(resale['listingId'],
        idempotency_key=_op(journey_id, 'payment'),
        payment_ref=resale['paymentRef'], amount=resale['amount'],
        buyer_role=resale['buyerRole'])
    accepted = resale_machine.accept_resale(resale['transferId'],
        idempotency_key=_op(journey_id, 'accept'),
        listing_id=resale['listingId'])
    evidence = accepted['evidence']
    if (evidence['seller_due'], evidence['organizer_due'], evidence['platform_due']) != (
            faces[primary['sellerRole']], faces[show['organizerRole']], faces['platform']):
        raise EconomicsLocalError('JOURNEY_BRA_FACE_MISMATCH')
    if evidence['amount'] != resale['amount'] or evidence['funds_executed'] is not False:
        raise EconomicsLocalError('JOURNEY_BRA_EVIDENCE_MISMATCH')

    # 3. Core resale trade on the same right; allocations must equal the faces.
    resale_prepared = run('resale-prepare', primary['sellerRole'], 'prepare_trade', {
        'domain': domain, 'tradeId': resale_trade,
        'ticketId': prepared['ticketId'], 'buyer': resale['buyerRole'],
        'amount': resale['amount'], 'expectedVersion': 1})
    run('resale-accept', resale['buyerRole'], 'accept_trade', {
        'domain': domain, 'tradeId': resale_trade,
        'termsHash': resale_prepared['termsHash']})
    run('resale-capture', 'pg-adapter', 'capture', {
        'domain': domain, 'scope': scope, 'provenance': 'synthetic',
        'tradeId': resale_trade, 'orderId': resale_prepared['externalOrderId'],
        'paymentId': resale['paymentRef'], 'amount': resale['amount'],
        'currency': 'KRW', 'buyer': resale['buyerRole']})
    movement = 'mv-' + _op(journey_id, 'resale-deposit')[3:]
    run('resale-settle', 'pg-adapter', 'settle_capture', {
        'domain': domain, 'scope': scope, 'provenance': 'synthetic',
        'tradeId': resale_trade, 'paymentId': resale['paymentRef'],
        'amount': resale['amount'], 'grossAmount': resale['amount'],
        'feeAmount': 0, 'taxAmount': 0, 'heldAmount': 0, 'adjustmentAmount': 0,
        'feeBearer': 'platform', 'contractRef': 'fixture:settlement:v1',
        'movementId': movement, 'sourceId': movement, 'currency': 'KRW'})
    run('resale-commit', 'operator', 'commit_trade',
        {'domain': domain, 'tradeId': resale_trade})
    trade_state = core.snapshot()['trades'][resale_trade]
    allocations = {a['payee']: a for a in trade_state['allocations']}
    for payee, face in faces.items():
        if face == 0:
            if payee in allocations:
                raise EconomicsLocalError('JOURNEY_ZERO_FACE_ALLOCATED')
            continue
        allocation = allocations.get(payee)
        if allocation is None or allocation['amount'] != face:
            raise EconomicsLocalError('JOURNEY_CORE_FACE_MISMATCH')

    # 4. Complete the event, then pay the caller's payout list in caller order.
    run('complete', 'operator', 'complete_event',
        {'domain': domain, 'eventId': event_id})
    desk = PayoutDesk(core, effects, None)
    payouts = []
    for payout in journey['payouts']:
        effect_id, payee, amount = payout['effectId'], payout['payee'], payout['amount']
        prepared_payout = desk.prepare_payout(
            trade_id=resale_trade, effect_id=effect_id, payee=payee,
            amount=amount, operation_id=_op(journey_id, 'payout-prepare:' + effect_id))
        desk.send(effect_id, operation_id=_op(journey_id, 'payout-send:' + effect_id))
        desk.observe(effect_id, phase='STATUS', status='SUCCESS', amount=amount,
                     source_id=_op(journey_id, 'payout-status:' + effect_id),
                     operation_id=_op(journey_id, 'payout-status:' + effect_id))
        final = desk.observe(effect_id, phase='FUNDS', amount=amount,
                             movement_id='mv-' + _op(journey_id, 'payout-funds:' + effect_id)[3:],
                             source_id=_op(journey_id, 'payout-funds:' + effect_id),
                             operation_id=_op(journey_id, 'payout-funds:' + effect_id))
        if final['state'] != 'DONE':
            raise EconomicsLocalError('JOURNEY_PAYOUT_NOT_DONE')
        payouts.append({'effectId': effect_id, 'payee': payee, 'amount': amount,
                        'allocationId': prepared_payout['allocationId'],
                        'state': final['state']})
    return {'journeyId': journey_id, 'evidenceClass': EVIDENCE_CLASS, **FLAGS,
            'eventId': event_id, 'primaryTradeId': primary_trade,
            'resaleTradeId': resale_trade, 'braEvidence': evidence,
            'faces': faces, 'facesMatch': True,
            'coreAllocations': trade_state['allocations'], 'payouts': payouts}