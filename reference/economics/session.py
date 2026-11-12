"""One explicit, sequential, in-memory economics reference session.

Composes the unchanged layers (see the package docstring). Every operation is
caller-driven with caller-supplied ids, keys, amounts and fixture policy
documents; there is no wall clock, no network, no retry and no background
work. Views are detached copies.

Composition boundaries (recorded, not invented):

- The fixture money layers (Core, settlement FSM, payment effects) are
  KRW-only and cap at ``10**12``. u128 quotes above the bound are refused,
  never narrowed. Non-KRW asset groups compose quote/plan/capture admission
  and refund calculation; their settlement binding is refused, never
  converted. There is no FX.
- The Core journey binds per order group (one synthetic event/trade carrying
  the group payable), not per line; per-line rights issuance is booking-layer
  scope. The settlement policy's residual payee must equal the event
  organizer and its fee payee must be ``platform`` so the FSM obligation faces
  and the Core PRIMARY allocations are the same faces.
- Partial refunds compose at the settlement FSM (B5 REQUESTER, distribution
  continues); full refunds additionally reverse the Core event and send one
  published REFUND intent. See refunds.py.
- Cross-machine atomicity is not claimed. Every readable precondition is
  checked before the first write; a failure after a write is a blocker for
  manual review, never an automatic retry.
"""
import copy

from assets import KRW
from common import Rejected, digest, external_id, ident, inventory_id
from lifecycle import REFUND_PROFILES
from mock_settlement import MONEY_MAX
from settlement_fsm import SettlementMachine
from resale_fsm import ResaleMachine

from integration_gate.catalogue import reference_types
from reference.payment_effects.payment_effect_session import PaymentEffectSession

from reference.economics import EVIDENCE_CLASS, FLAGS, EconomicsLocalError
from reference.economics import quotes
from reference.economics.captures import CaptureLedger, DurableCaptureLedger
from reference.economics.refunds import (
    RefundDesk, authorize_refund, is_full_refund, reservation_check,
)
from reference.economics.payouts import PayoutDesk, resale_seller_payout

Core, _Rejected = reference_types()

_GROUP_FIELDS = {'groupId', 'policyRef', 'expiresAt', 'lines', 'discounts',
                 'legs', 'settlementPolicyRef', 'eventPolicy', 'buyer',
                 'debtorRole', 'paymentId'}
_EVENT_POLICY_FIELDS = {'organizerRole', 'resaleCap', 'resaleFeeBps',
                        'resaleOrganizerBps', 'resaleAllowed', 'refundProfile'}
_REFUNDABLE_PHASES = ('SETTLED', 'DISTRIBUTED', 'COMPLETED')


def _ident(value, label):
    try:
        return ident(value)
    except Rejected:
        raise EconomicsLocalError('ID_INVALID:' + label) from None


def _op(*parts):
    return 'econ-' + digest(list(parts))


def _bps(value, label):
    if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 10000:
        raise EconomicsLocalError('BPS_INVALID:' + label)
    return value


class EconomicsSession:
    def __init__(self, *, assets, policies, budgets, capture_ledger=None):
        self._assets = assets
        self._policies = policies
        self._core = Core(':memory:')
        self._effects = PaymentEffectSession(self._core)
        self._settlement = SettlementMachine()
        self._resale = ResaleMachine()
        self._captures = (capture_ledger if capture_ledger is not None
                          else CaptureLedger(budgets))
        self._refund_desk = RefundDesk(self._core, self._effects, self._settlement)
        self._payout_desk = PayoutDesk(self._core, self._effects, self._settlement)
        self._orders = {}
        self._effect_bindings = {}
        self._journeys = {}
        self._closed = False

    @classmethod
    def over_durable(cls, unit, *, assets, policies):
        """Optional binding: capture admission persists through the unchanged
        stage-5 DurableUnit on the pinned local PostgreSQL (default off)."""
        return cls(assets=assets, policies=policies, budgets=unit.spec,
                   capture_ledger=DurableCaptureLedger(unit))

    # -- plumbing -----------------------------------------------------------
    def _require_open(self):
        if self._closed:
            raise EconomicsLocalError('SESSION_CLOSED')

    def _group(self, order_id, group_id):
        order = self._orders.get(order_id)
        if order is None:
            raise EconomicsLocalError('ORDER_NOT_FOUND')
        group = order['groups'].get(group_id)
        if group is None:
            raise EconomicsLocalError('GROUP_NOT_FOUND')
        return order, group

    def close(self):
        if not self._closed:
            self._closed = True
            self._effects.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    # -- order creation -----------------------------------------------------
    def create_order(self, order_id, *, order_version, scope, groups, now_ms):
        self._require_open()
        order_id = _ident(order_id, 'orderId')
        if order_id in self._orders:
            raise EconomicsLocalError('ORDER_EXISTS')
        if type(scope) is not dict or set(scope) != {'issuerId', 'eventId', 'performanceId'}:
            raise EconomicsLocalError('SCOPE_FIELDS_INVALID')
        scope = {key: _ident(value, 'scope.' + key) for key, value in scope.items()}
        if type(groups) is not list or not groups:
            raise EconomicsLocalError('GROUPS_INVALID')
        if type(now_ms) is not int or isinstance(now_ms, bool) or now_ms < 0:
            raise EconomicsLocalError('TIME_INVALID')
        # Pass 1: pure calculation + authentication for every group. No writes.
        prepared, seen = [], set()
        for member in groups:
            if type(member) is not dict or set(member) != _GROUP_FIELDS:
                raise EconomicsLocalError('GROUP_FIELDS_INVALID')
            group_id = _ident(member['groupId'], 'groupId')
            if group_id in seen:
                raise EconomicsLocalError('GROUP_DUPLICATE')
            seen.add(group_id)
            request = quotes.quote_request(
                order_id, order_version=order_version, scope=scope,
                policy_ref=member['policyRef'], expires_at=member['expiresAt'],
                lines=member['lines'], discounts=member['discounts'])
            quote = quotes.build_quote(self._assets, self._policies, request)
            payable = quotes.require_money_bound(quote)
            plan = quotes.plan_payments(self._assets, quote, member['legs'],
                                        quote['quoteHash'], now_ms)
            for leg in plan['legs']:
                quotes.require_leg_bound(int(leg['amount']['atoms']))
            buyer = _ident(member['buyer'], 'buyer')
            free = payable == 0
            krw_executable = quote['asset'] == KRW.to_dict()
            binds_money = (not free) and krw_executable
            if not binds_money:
                # Free orders and non-KRW paid groups never enter the fixture
                # money pipeline (KRW-only Core/FSM/effects); money fields must
                # be absent. Non-KRW groups compose calculation + capture only.
                if (member['settlementPolicyRef'] is not None
                        or member['eventPolicy'] is not None
                        or member['debtorRole'] is not None
                        or member['paymentId'] is not None):
                    raise EconomicsLocalError(
                        'FREE_ORDER_MONEY_FIELDS' if free else 'NON_KRW_MONEY_FIELDS')
                policy_doc = event_policy = None
                debtor = payment_id = None
            else:
                policy_doc = self._policies.authenticate(
                    member['settlementPolicyRef'], 'PRIMARY_FEE_BPS')
                event_policy = member['eventPolicy']
                if type(event_policy) is not dict or set(event_policy) != _EVENT_POLICY_FIELDS:
                    raise EconomicsLocalError('EVENT_POLICY_FIELDS_INVALID')
                organizer = _ident(event_policy['organizerRole'], 'organizerRole')
                if type(event_policy['resaleCap']) is not int or not 0 < event_policy['resaleCap'] <= MONEY_MAX:
                    raise EconomicsLocalError('EVENT_RESALE_CAP_INVALID')
                _bps(event_policy['resaleFeeBps'], 'resaleFeeBps')
                _bps(event_policy['resaleOrganizerBps'], 'resaleOrganizerBps')
                if event_policy['resaleFeeBps'] + event_policy['resaleOrganizerBps'] > 10000:
                    raise EconomicsLocalError('EVENT_SPLIT_EXCEEDS_BASIS')
                if type(event_policy['resaleAllowed']) is not bool:
                    raise EconomicsLocalError('EVENT_RESALE_ALLOWED_INVALID')
                if event_policy['refundProfile'] not in REFUND_PROFILES:
                    raise EconomicsLocalError('EVENT_REFUND_PROFILE_INVALID')
                if (policy_doc['residual_payee'] != organizer
                        or policy_doc['fee_payee'] != 'platform'):
                    raise EconomicsLocalError('PAYEE_BINDING_MISMATCH')
                debtor = _ident(member['debtorRole'], 'debtorRole')
                try:
                    payment_id = external_id(member['paymentId'])
                except Rejected:
                    raise EconomicsLocalError('PAYMENT_ID_INVALID') from None
            prepared.append({
                'groupId': group_id, 'quote': quote, 'plan': plan,
                'payable': payable, 'free': free, 'buyer': buyer,
                'policyDoc': policy_doc, 'eventPolicy': event_policy,
                'debtorRole': debtor, 'paymentId': payment_id,
                'krwExecutable': krw_executable, 'bindsMoney': binds_money,
            })
        # Pass 2: apply. KRW paid groups bind the settlement FSM and the Core
        # journey; non-KRW paid groups stay calculation + capture admission.
        order = {'orderId': order_id, 'orderVersion': order_version,
                 'scope': dict(scope), 'groups': {}}
        for spec in prepared:
            group_id = spec['groupId']
            record = {
                'groupId': group_id, 'quote': spec['quote'], 'plan': spec['plan'],
                'asset': spec['quote']['asset'], 'payable': spec['payable'],
                'buyer': spec['buyer'], 'free': spec['free'],
                'krwExecutable': spec['krwExecutable'],
                'phase': 'COMPLETED' if spec['free'] else 'CREATED',
                'settlementId': None, 'eventId': None, 'tradeId': None,
                'externalOrderId': None, 'ticketId': None, 'inventoryId': None,
                'debtorRole': spec['debtorRole'], 'paymentId': spec['paymentId'],
                'refundedLines': set(), 'refundReserved': {},
                'payoutsPrepared': {},
            }
            if spec['bindsMoney']:
                self._bind_money_journey(order_id, record, spec, scope)
            for leg in spec['plan']['legs']:
                self._captures.add_leg(order_id, group_id, leg['legId'],
                                       int(leg['amount']['atoms']))
            order['groups'][group_id] = record
        self._orders[order_id] = order
        return self.view(order_id)

    def _bind_money_journey(self, order_id, record, spec, scope):
        group_id = record['groupId']
        payable = spec['payable']
        policy_doc, event_policy = spec['policyDoc'], spec['eventPolicy']
        settlement_id = 'st-' + digest([order_id, group_id])
        event_id = 'ev-' + digest([order_id, group_id])
        trade_id = 't-' + digest([order_id, group_id, 'primary'])
        seat_inventory = inventory_id(scope['issuerId'], event_id,
                                      scope['performanceId'], group_id)
        self._settlement.initiate(
            settlement_id, idempotency_key=_op(order_id, group_id, 'initiate'),
            trade_id=trade_id, gross=payable, debtor_role=spec['debtorRole'],
            policy=policy_doc)
        self._settlement.authorize(
            settlement_id, idempotency_key=_op(order_id, group_id, 'authorize'))
        domain = self._core.DOMAIN
        self._core.execute(_op(order_id, group_id, 'create-event'), 'operator',
                           'create_event', {
                               'domain': domain, 'eventId': event_id,
                               'organizer': event_policy['organizerRole'],
                               'policy': {
                                   'primaryPrice': payable,
                                   'resaleCap': event_policy['resaleCap'],
                                   'primaryFeeBps': policy_doc['fee_bps'],
                                   'resaleFeeBps': event_policy['resaleFeeBps'],
                                   'resaleOrganizerBps': event_policy['resaleOrganizerBps'],
                                   'resaleAllowed': event_policy['resaleAllowed'],
                                   'refundProfile': event_policy['refundProfile']},
                               'seats': [group_id],
                               'issuerId': scope['issuerId'],
                               'sessionId': scope['performanceId']})
        prepared = self._core.execute(
            _op(order_id, group_id, 'prepare-trade'), spec['buyer'],
            'prepare_trade', {
                'domain': domain, 'tradeId': trade_id,
                'inventoryId': seat_inventory, 'expectedInventoryVersion': 0,
                'buyer': spec['buyer'], 'amount': payable,
                'expectedVersion': 0})['result']
        record.update(settlementId=settlement_id, eventId=event_id,
                      tradeId=trade_id,
                      externalOrderId=prepared['externalOrderId'],
                      ticketId=prepared['ticketId'], inventoryId=seat_inventory)

    # -- captures -----------------------------------------------------------
    def submit_capture(self, order_id, group_id, leg_id, capture_id, *,
                       amount, buyer, nonce, now_ms):
        self._require_open()
        self._group(order_id, group_id)
        return self._captures.submit(
            order_id=order_id, group_id=group_id, leg_id=leg_id,
            capture_id=capture_id, amount=amount, buyer=buyer, nonce=nonce,
            now_ms=now_ms)

    def complete_capture(self, capture_id, *, outcome, source_id, now_ms):
        self._require_open()
        return self._captures.complete(capture_id, outcome=outcome,
                                       source_id=source_id, now_ms=now_ms)

    # -- settlement ---------------------------------------------------------
    def settle_group(self, order_id, group_id, *, movement_id, idempotency_key):
        self._require_open()
        _, group = self._group(order_id, group_id)
        if group['free']:
            raise EconomicsLocalError('FREE_ORDER_NO_SETTLEMENT')
        if not group['krwExecutable']:
            raise EconomicsLocalError('FIXTURE_MONEY_KRW_ONLY')
        if group['phase'] != 'CREATED':
            raise EconomicsLocalError('GROUP_NOT_OPEN')
        for leg in group['plan']['legs']:
            if not self._captures.fully_captured(order_id, group_id, leg['legId']):
                raise EconomicsLocalError('CAPTURES_INCOMPLETE')
        payable = group['payable']
        settlement_id = group['settlementId']
        self._settlement.capture(
            settlement_id, idempotency_key=_op(order_id, group_id, 'capture', idempotency_key))
        self._settlement.commit(
            settlement_id, idempotency_key=_op(order_id, group_id, 'commit', idempotency_key),
            movement_id=movement_id, gross=payable, amount=payable,
            fee=0, tax=0, held=0, adjustment=0)
        domain, scope = self._core.DOMAIN, dict(self._core.SCOPE)
        self._core.execute(
            _op(order_id, group_id, 'core-capture', idempotency_key), 'pg-adapter',
            'capture', {
                'domain': domain, 'scope': scope, 'provenance': 'synthetic',
                'tradeId': group['tradeId'], 'orderId': group['externalOrderId'],
                'paymentId': group['paymentId'], 'amount': payable,
                'currency': 'KRW', 'buyer': group['buyer']})
        self._core.execute(
            _op(order_id, group_id, 'core-settle', idempotency_key, movement_id),
            'pg-adapter', 'settle_capture', {
                'domain': domain, 'scope': scope, 'provenance': 'synthetic',
                'tradeId': group['tradeId'], 'paymentId': group['paymentId'],
                'amount': payable, 'grossAmount': payable,
                'feeAmount': 0, 'taxAmount': 0, 'heldAmount': 0,
                'adjustmentAmount': 0, 'feeBearer': 'platform',
                'contractRef': 'fixture:settlement:v1',
                'movementId': movement_id, 'sourceId': movement_id,
                'currency': 'KRW'})
        self._core.execute(
            _op(order_id, group_id, 'core-commit', idempotency_key), 'operator',
            'commit_trade', {'domain': domain, 'tradeId': group['tradeId']})
        obligations = {row['payee']: row['face']
                       for row in self._settlement.view(settlement_id)['claim']['obligations']}
        allocations = {a['payee']: a['amount'] for a in
                       self._core.snapshot()['trades'][group['tradeId']]['allocations']}
        if obligations != allocations:
            raise EconomicsLocalError('FACE_MISMATCH')
        group['phase'] = 'SETTLED'
        return {'settlement': self._settlement.view(settlement_id),
                'allocations': self._core.snapshot()['trades'][group['tradeId']]['allocations'],
                'evidenceClass': EVIDENCE_CLASS, **FLAGS}

    def distribute_group(self, order_id, group_id, *, order, idempotency_key):
        self._require_open()
        _, group = self._group(order_id, group_id)
        if group['free'] or not group['krwExecutable']:
            raise EconomicsLocalError('GROUP_NOT_DISTRIBUTABLE')
        if group['phase'] != 'SETTLED':
            raise EconomicsLocalError('GROUP_NOT_SETTLED')
        result = self._payout_desk.distribute(
            group['settlementId'], order=order,
            idempotency_key=_op(order_id, group_id, 'distribute', idempotency_key))
        group['phase'] = 'DISTRIBUTED'
        return result

    def complete_group(self, order_id, group_id):
        self._require_open()
        _, group = self._group(order_id, group_id)
        if group['free']:
            raise EconomicsLocalError('FREE_ORDER_ALREADY_COMPLETED')
        if not group['krwExecutable']:
            raise EconomicsLocalError('FIXTURE_MONEY_KRW_ONLY')
        if group['phase'] not in ('SETTLED', 'DISTRIBUTED'):
            raise EconomicsLocalError('GROUP_NOT_COMPLETABLE')
        self._core.execute(_op(order_id, group_id, 'complete-event'), 'operator',
                           'complete_event',
                           {'domain': self._core.DOMAIN, 'eventId': group['eventId']})
        group['phase'] = 'COMPLETED'
        return {'phase': group['phase'], 'evidenceClass': EVIDENCE_CLASS, **FLAGS}

    # -- payouts ------------------------------------------------------------
    def prepare_payout(self, order_id, group_id, *, effect_id, payee, amount):
        self._require_open()
        _, group = self._group(order_id, group_id)
        if group['free'] or not group['krwExecutable']:
            raise EconomicsLocalError('GROUP_NOT_PAYABLE')
        if group['phase'] != 'COMPLETED':
            raise EconomicsLocalError('GROUP_NOT_COMPLETED')
        claim = self._settlement.view(group['settlementId'])['claim']
        if claim['distribution_order'] is None:
            raise EconomicsLocalError('PAYOUT_NOT_DISTRIBUTED')
        obligation = next((row for row in claim['obligations']
                           if row['payee'] == payee), None)
        if obligation is None:
            raise EconomicsLocalError('PAYOUT_PAYEE_UNKNOWN')
        prepared = group['payoutsPrepared'].get(payee, 0)
        if type(amount) is not int or amount <= 0 or prepared + amount > obligation['distributed']:
            raise EconomicsLocalError('PAYOUT_EXCEEDS_DISTRIBUTED')
        result = self._payout_desk.prepare_payout(
            trade_id=group['tradeId'], effect_id=effect_id, payee=payee,
            amount=amount,
            operation_id=_op(order_id, group_id, 'payout-prepare', effect_id))
        self._effect_bindings[effect_id] = {'orderId': order_id,
                                            'groupId': group_id,
                                            'kind': 'PAYOUT', 'payee': payee}
        group['payoutsPrepared'][payee] = prepared + amount
        return result

    def send_effect(self, effect_id):
        self._require_open()
        if effect_id not in self._effect_bindings:
            raise EconomicsLocalError('EFFECT_NOT_BOUND')
        return self._payout_desk.send(
            effect_id, operation_id=_op(effect_id, 'send'))

    def observe_effect(self, effect_id, *, phase, source_id, amount,
                       provider_operation_id=None, status=None, movement_id=None,
                       fence_ref=None, fence_provenance=None):
        self._require_open()
        if effect_id not in self._effect_bindings:
            raise EconomicsLocalError('EFFECT_NOT_BOUND')
        return self._payout_desk.observe(
            effect_id, phase=phase, source_id=source_id, amount=amount,
            provider_operation_id=provider_operation_id, status=status,
            movement_id=movement_id, fence_ref=fence_ref,
            fence_provenance=fence_provenance,
            operation_id=_op(effect_id, 'observe', source_id))

    # -- refunds ------------------------------------------------------------
    def refund_lines(self, order_id, group_id, *, line_ids, refund_id,
                     authorization, refund_policy_ref, reason, idempotency_key,
                     route_profile=None, effect_id=None):
        self._require_open()
        _, group = self._group(order_id, group_id)
        if group['free']:
            raise EconomicsLocalError('FREE_ORDER_NO_REFUND')
        if not group['krwExecutable']:
            raise EconomicsLocalError('FIXTURE_MONEY_KRW_ONLY')
        if group['phase'] not in _REFUNDABLE_PHASES:
            raise EconomicsLocalError('GROUP_NOT_REFUNDABLE')
        proposal = quotes.propose_line_refund(
            self._assets, group['quote'], group['plan'], line_ids,
            group['plan']['planHash'])
        self._policies.authenticate(refund_policy_ref, 'REFUND_FROZEN_LINE_PRICE')
        authorize_refund(proposal, authorization)
        leg_confirmed = {
            leg['legId']: self._captures.leg_view(order_id, group_id, leg['legId'])['confirmed']
            for leg in group['plan']['legs']}
        reservations = reservation_check(
            group['quote'], proposal, leg_confirmed=leg_confirmed,
            refund_reserved=group['refundReserved'],
            refunded_lines=group['refundedLines'])
        customer = int(proposal['customerRefund']['atoms'])
        full = is_full_refund(group['quote'], proposal)
        if full:
            if route_profile not in ('CASH_REFUND_FIXTURE', 'PG_ORIGINAL_CANCEL_FIXTURE'):
                raise EconomicsLocalError('REFUND_ROUTE_REQUIRED')
            _ident(effect_id, 'effectId')
            if effect_id in self._effect_bindings:
                raise EconomicsLocalError('REFUND_EFFECT_EXISTS')
        self._refund_desk.bind(
            group['settlementId'], refund_id=refund_id, amount=customer,
            beneficiary_role=group['buyer'], reason=reason,
            idempotency_key=_op(order_id, group_id, 'refund-bind', idempotency_key))
        reversal = None
        if full:
            reversal = self._refund_desk.full_reversal(
                event_id=group['eventId'], trade_id=group['tradeId'],
                effect_id=effect_id, amount=customer, buyer=group['buyer'],
                route_profile=route_profile,
                operation_id=_op(order_id, group_id, 'refund-exec', idempotency_key))
            self._effect_bindings[effect_id] = {'orderId': order_id,
                                                'groupId': group_id,
                                                'kind': 'REFUND',
                                                'payee': group['buyer']}
            group['phase'] = 'REFUNDED'
        group['refundedLines'] |= set(proposal['lineIds'])
        for leg_id, amount in reservations.items():
            group['refundReserved'][leg_id] = group['refundReserved'].get(leg_id, 0) + amount
        claim = self._settlement.view(group['settlementId'])['claim']
        return {'proposal': proposal, 'refundId': refund_id,
                'kind': 'FULL' if full else 'PARTIAL',
                'bearer': claim['refund_bearer_policy'],
                'distributionBlocked': claim['distribution_blocked'],
                'effectId': effect_id if full else None,
                'reversal': reversal, 'evidenceClass': EVIDENCE_CLASS, **FLAGS}

    def observe_refund_acceptance(self, order_id, group_id, *, source_id,
                                  amount, idempotency_key):
        self._require_open()
        _, group = self._group(order_id, group_id)
        if group['settlementId'] is None:
            raise EconomicsLocalError('GROUP_NOT_REFUNDABLE')
        return self._refund_desk.observe_acceptance(
            group['settlementId'], source_id=source_id, amount=amount,
            idempotency_key=_op(order_id, group_id, 'refund-accept', idempotency_key))

    # -- resale -------------------------------------------------------------
    def resale_payout(self, journey, *, now_ms):
        self._require_open()
        journey_id = journey.get('journeyId') if type(journey) is dict else None
        if journey_id in self._journeys:
            raise EconomicsLocalError('JOURNEY_EXISTS')
        result = resale_seller_payout(self._core, self._effects, self._resale,
                                      journey, now_ms=now_ms)
        self._journeys[journey_id] = result['resaleTradeId']
        return result

    # -- views --------------------------------------------------------------
    def view(self, order_id=None):
        self._require_open()
        orders = {}
        selected = ([order_id] if order_id is not None
                    else sorted(self._orders))
        for oid in selected:
            if oid not in self._orders:
                raise EconomicsLocalError('ORDER_NOT_FOUND')
            order = self._orders[oid]
            groups = {}
            for gid, group in order['groups'].items():
                detached = copy.deepcopy({k: v for k, v in group.items()
                                          if k != 'refundedLines'})
                detached['refundedLines'] = sorted(group['refundedLines'])
                if group['settlementId'] is not None:
                    detached['settlement'] = self._settlement.view(group['settlementId'])
                groups[gid] = detached
            orders[oid] = {'orderId': oid, 'orderVersion': order['orderVersion'],
                           'scope': dict(order['scope']), 'groups': groups}
        effect_ids = sorted(self._effect_bindings)
        return {'evidenceClass': EVIDENCE_CLASS, **FLAGS,
                'orders': orders,
                'captures': self._captures.view(),
                'effectBindings': copy.deepcopy(self._effect_bindings),
                'effects': self._effects.view(effect_ids=effect_ids,
                                              trade_ids=[], accounts=[])['effects'],
                'journeys': dict(self._journeys)}