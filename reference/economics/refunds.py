"""Line refunds: calculation proposal, authorization, reservation, execution.

Composition of unchanged layers, under the adopted settlement posture
SET-POLICY-DRAFT-0.4 (B5 REQUESTER for partial refunds):

1. ``commerce.propose_line_refund`` — the frozen-line-price full reversal
   calculation (``executionAuthorized=False``; five required evidence items).
2. Authorization gate — the caller must present a non-empty reference for
   every required evidence item; the refund policy reference must be
   authenticated (``REFUND_FROZEN_LINE_PRICE``). Missing evidence refuses
   before any write.
3. Reservation gate — a line is refunded at most once; per leg, reserved
   refunds plus the new route amount never exceed the confirmed captured
   amount. Refusal is atomic (no writes).
4. Settlement FSM ``bind_refund`` — ceiling <= gross. A partial refund keeps
   the B5 REQUESTER bearer, leaves payee faces untouched and does not block
   distribution. A full-gross refund reclassifies
   (``FIXTURE_FULL_GROSS_RECLASS``).
5. Full refunds only: the Core journey reverses via ``cancel_event`` and one
   published REFUND effect (``CASH_REFUND_FIXTURE`` or
   ``PG_ORIGINAL_CANCEL_FIXTURE``) is prepared and sent as a local intent.
   Partial refunds compose at the settlement FSM's requester-borne face plus
   ``observe_mock_cancel_acceptance``: the published Core REFUND route is
   funded by a full-trade reversal liability (``refundDue``), which would
   cancel the event and block the continuing distribution B5 requires. This
   is a composition boundary, recorded as a characterization; no new protocol
   semantics is invented.

No step auto-retries. Cross-machine atomicity is not claimed: the desk
pre-validates every precondition it can read, then applies in the fixed order
above; a failure after the first write is a blocker for manual review.
"""
from finance import ROUTES, cash_reservation
from mock_settlement import MONEY_MAX

from reference.economics import EconomicsLocalError

REFUND_ROUTES = ('CASH_REFUND_FIXTURE', 'PG_ORIGINAL_CANCEL_FIXTURE')


def authorize_refund(proposal, authorization):
    """Every required evidence item needs a caller reference; exact fields."""
    required = proposal['requiredEvidence']
    if type(authorization) is not dict or set(authorization) != set(required):
        raise EconomicsLocalError('REFUND_EVIDENCE_FIELDS')
    missing = [key for key in required
               if type(authorization[key]) is not str
               or not authorization[key].strip()]
    if missing:
        raise EconomicsLocalError('REFUND_EVIDENCE_MISSING:' + ','.join(missing))
    return True


def is_full_refund(quote, proposal):
    return set(proposal['lineIds']) == {row['lineId'] for row in quote['lines']}


def reservation_check(quote, proposal, *, leg_confirmed, refund_reserved,
                      refunded_lines):
    """Atomic per-line / per-leg reservation gate. Returns the leg reservations.

    ``leg_confirmed``: legId -> confirmed captured atoms.
    ``refund_reserved``: legId -> atoms already reserved by prior refunds.
    ``refunded_lines``: set of line ids already refunded.
    """
    selected = set(proposal['lineIds'])
    again = sorted(selected & set(refunded_lines))
    if again:
        raise EconomicsLocalError('LINE_ALREADY_REFUNDED:' + ','.join(again))
    reservations = {}
    for route in proposal['originalRoutes']:
        leg_id = route['legId']
        amount = int(route['amount']['atoms'])
        confirmed = leg_confirmed.get(leg_id)
        if confirmed is None:
            raise EconomicsLocalError('REFUND_LEG_NOT_CAPTURED:' + leg_id)
        reserved = refund_reserved.get(leg_id, 0)
        if reserved + amount > confirmed:
            raise EconomicsLocalError('REFUND_EXCEEDS_CAPTURED:' + leg_id)
        reservations[leg_id] = amount
    customer = int(proposal['customerRefund']['atoms'])
    if customer <= 0:
        raise EconomicsLocalError('REFUND_NOT_POSITIVE')
    if customer > MONEY_MAX:
        raise EconomicsLocalError('AMOUNT_EXCEEDS_FIXTURE_MONEY_BOUND')
    return reservations


class RefundDesk:
    """Settlement binding plus the full-refund Core reversal and REFUND intent."""

    def __init__(self, core, effects, settlement):
        self._core = core
        self._effects = effects
        self._settlement = settlement

    def bind(self, settlement_id, *, refund_id, amount, beneficiary_role,
             reason, idempotency_key):
        return self._settlement.bind_refund(
            settlement_id, idempotency_key=idempotency_key,
            refund_id=refund_id, amount=amount,
            beneficiary_role=beneficiary_role, reason=reason)

    def observe_acceptance(self, settlement_id, *, source_id, amount,
                           idempotency_key):
        return self._settlement.observe_mock_cancel_acceptance(
            settlement_id, idempotency_key=idempotency_key,
            source_id=source_id, amount=amount)

    def full_reversal(self, *, event_id, trade_id, effect_id, amount, buyer,
                      route_profile, operation_id):
        """Cancel the group event, prepare and send one REFUND intent.

        Every readable precondition is checked before the first write. The
        send is a stored local intent (``OUTCOME_UNKNOWN``); observations are
        separate explicit caller operations.
        """
        if route_profile not in REFUND_ROUTES:
            raise EconomicsLocalError('REFUND_ROUTE_UNSUPPORTED')
        if type(amount) is not int or not 0 < amount <= MONEY_MAX:
            raise EconomicsLocalError('REFUND_AMOUNT_INVALID')
        snapshot = self._core.snapshot()
        event = snapshot['events'].get(event_id)
        trade = snapshot['trades'].get(trade_id)
        if event is None or trade is None:
            raise EconomicsLocalError('REFUND_JOURNEY_NOT_FOUND')
        if event['status'] not in ('OPEN', 'COMPLETED'):
            raise EconomicsLocalError('REFUND_EVENT_NOT_REVERSIBLE')
        if trade['status'] != 'COMMITTED' or not trade['captured']:
            raise EconomicsLocalError('REFUND_TRADE_NOT_COMMITTED')
        if effect_id in snapshot['effects']:
            raise EconomicsLocalError('REFUND_EFFECT_EXISTS')
        route = ROUTES[route_profile]
        owed = 'refund:' + trade_id
        pending = list(snapshot['effects'].values())
        if any(x['owed'] == owed and x['state'] == 'EVIDENCE_CONFLICT'
               for x in pending):
            raise EconomicsLocalError('REFUND_OBLIGATION_EVIDENCE_CONFLICT')
        if route['cash']:
            pool = trade['pool']
            reserved = sum(cash_reservation(x) for x in pending
                           if x['pool'] == pool)
            available = snapshot['balances'].get('funds:' + pool, 0) - reserved
            if amount > available:
                raise EconomicsLocalError('REFUND_INSUFFICIENT_CONFIRMED_FUNDS')
        domain = self._core.DOMAIN
        self._core.execute(operation_id + ':cancel', 'operator', 'cancel_event',
                           {'domain': domain, 'eventId': event_id})
        body = {'domain': domain, 'effectId': effect_id, 'tradeId': trade_id,
                'kind': 'REFUND', 'amount': amount,
                'routeProfile': route_profile,
                'contractRef': route['contract']}
        if route['cash']:
            body['beneficiaryAccountRef'] = 'fixture-account:' + buyer
        self._effects.execute(operation_id + ':prepare', 'operator',
                              'prepare_effect', body)
        sent = self._effects.execute(operation_id + ':send', 'operator',
                                     'send_effect',
                                     {'domain': domain, 'effectId': effect_id})
        return {'effectId': effect_id, 'routeProfile': route_profile,
                'dispatch': sent['result']}