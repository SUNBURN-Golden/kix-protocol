"""Reusable local readiness fault scenarios; no backend format assumptions.

Adapters provide open_boundary(directory), open_store(directory), and fault_error.
Boundary handles expose call(name, fn, fault=None), machine(name), close().
Store handles expose append, records, committed_bytes, can_accept, has_operation,
and close. Fault names and error codes are the existing readiness interface.
These source-informed scenarios do not establish production conformance.
"""

from __future__ import annotations

import tempfile
import threading
import sys
from pathlib import Path

# The semantic oracle remains the existing public reference FSMs.
ROOT = Path(__file__).resolve().parents[1]
for suite in (
    "settlement_f01_f03",
    "booking_resale_admission",
    "credit_advance_f04",
    "ai_delegation",
    "token_reward",
):
    path = str(ROOT / "reference" / suite)
    if path not in sys.path:
        sys.path.insert(0, path)

from admission_fsm import AdmissionError  # noqa: E402
from ai_delegation_mock import AiDelegationError  # noqa: E402
from credit_fsm import CreditError  # noqa: E402
from mock_gates import ADMISSION_WINDOW_MS, OFFER_WINDOW_MS  # noqa: E402
from reservation_fsm import ReservationError  # noqa: E402
from resale_fsm import ResaleError  # noqa: E402
from settlement_fsm import SettlementMachine  # noqa: E402
from token_reward_model import POOLS, TokenRewardError, reward_id  # noqa: E402

from readiness.ai_delegation_wrap import WrapError  # noqa: E402
from readiness.reward_wrap import WrapError as RewardWrapError  # noqa: E402

PAY = 'ab' * 32
SALE_PAY = 'cd' * 32
REQ = '11' * 32
PRICE = 10_001
T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS
ADMISSION_EXPIRES = T0 + ADMISSION_WINDOW_MS


def show_kwargs():
    return dict(
        organizer_role='organizer',
        capacity=2,
        gate_roles=['gate-a', 'gate-b'],
        primary_price=PRICE,
        resale_cap=20_000,
        resale_allowed=True,
        organizer_bps=1,
        platform_bps=1,
    )


def settlement_policy():
    return {
        'kind': 'PRIMARY_FEE_BPS',
        'fee_bps': 500,
        'residual_payee': 'organizer',
        'fee_payee': 'platform',
    }


def committed_face():
    book = SettlementMachine()
    book.initiate(
        'claim-face',
        idempotency_key='init-face',
        trade_id='trade-face',
        gross=100_000,
        debtor_role='fixture-merchant',
        policy=settlement_policy(),
    )
    book.authorize('claim-face', idempotency_key='auth-face')
    book.capture('claim-face', idempotency_key='cap-face')
    book.commit(
        'claim-face',
        idempotency_key='commit-face',
        movement_id='move-face',
        gross=100_000,
        amount=97_000,
        fee=3_000,
        tax=0,
        held=0,
        adjustment=0,
    )
    return book.view('claim-face')['claim']


def admission_body():
    body = show_kwargs()
    body.update(
        show_id='show-1',
        slot=0,
        buyer_role='buyer-1',
        expires_ms=EXPIRES,
        order_id='order-1',
        amount=PRICE,
        payment_ref=PAY,
        reservation_id=None,
        quote_ref=None,
    )
    return body


def resale_adopt_body():
    body = show_kwargs()
    body.update(
        show_id='show-1',
        slot=0,
        buyer_role='buyer-1',
        expires_ms=EXPIRES,
        order_id='order-1',
        amount=PRICE,
        payment_ref=PAY,
        reservation_id=None,
        quote_ref=None,
    )
    return body


def code(fn, error_type):
    try:
        fn()
    except error_type as exc:
        return exc.code
    raise AssertionError('expected ' + error_type.__name__)


AI_ISSUER = 'human-issuer'
AI_AGENT = 'agent-1'
AI_GRANT = 'g1'


def ai_delegation_issue(machine):
    return machine.issue_grant(
        AI_ISSUER,
        AI_GRANT,
        AI_AGENT,
        ['QUERY', 'PROPOSE'],
        {'surfaces': ['surface-a']},
        {
            'per_action_max': 100,
            'cumulative_max': 1000,
            'count_max': 5,
            'currency': 'KRW',
        },
        {'not_before': 10, 'not_after': 20},
    )


def reward_opening():
    base = {pool: 7 for pool in POOLS}
    base['PROTOCOL_REVENUE'] = 50
    base['TOKEN_TREASURY_REWARD'] = 50
    return base


def reward_key():
    return {
        'program': 'program-1',
        'source_op_id': 'op-1',
        'recipient': 'recipient-1',
        'kind': 'participation',
    }


def reward_source_view():
    return {
        'phase': 'COMMITTED',
        'currency': 'KRW',
        'funds_executed': False,
        'bank_debit_observed': False,
        'legal_debtor_bound': False,
        'external_return_closed': False,
        'durable': False,
    }


def reward_rid():
    return reward_id(**reward_key())


def reward_observe(machine):
    return machine.observe(
        reward_key(),
        idempotency_key='obs-1',
        source_view=reward_source_view(),
        rule_version='rule-v1',
        amount=4,
        source_kind='SETTLEMENT',
    )


def reward_mark_eligible(machine):
    return machine.mark_eligible(
        reward_rid(),
        idempotency_key='elig-1',
        window_closed=True,
        source_view=reward_source_view(),
        abuse_clear=True,
    )


class BackendConformance:
    """Mixin: combine with unittest.TestCase and provide a backend adapter."""

    def test_budget_rejection_preserves_records_and_replay_identity(self):
        # Exercise the existing store admission predicate without HTTP or
        # choosing new product limits. The gate retains command-level coverage.
        with tempfile.TemporaryDirectory() as tmp:
            store = self.backend.open_store(tmp)
            try:
                record = {
                    'kind': 'core_commit', 'machine': 'integration_core',
                    'operationId': 'op-budget', 'actor': 'operator',
                    'action': 'advance_clock', 'body': {'now': 50},
                    'receiptDigest': 'cd' * 32,
                }
                self.assertTrue(store.can_accept(1, 1, store.committed_bytes + 1))
                store.append(record)
                before = list(store.records)
                size = store.committed_bytes
                self.assertFalse(store.can_accept(0, 1, size + 1))
                self.assertFalse(store.can_accept(1, 2, size))
                self.assertTrue(store.can_accept(1, 2, size + 1))
                self.assertEqual(store.records, before)
                self.assertEqual(store.committed_bytes, size)
                self.assertTrue(store.has_operation('op-budget'))
                self.assertFalse(store.has_operation('op-rejected'))
                self.assertIs(before[0]['protocolTruth'], False)
                self.assertIs(before[0]['productionConformance'], False)
            finally:
                store.close()
            recovered = self.backend.open_store(tmp)
            try:
                self.assertEqual(recovered.records, before)
                self.assertTrue(recovered.has_operation('op-budget'))
                self.assertFalse(recovered.can_accept(0, 1, size + 1))
            finally:
                recovered.close()

    def test_settlement_cash_survives_restart_and_a_torn_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._settlement_until_capture(boundary)
                with self.assertRaises(self.backend.fault_error):
                    boundary.call(
                        'settlement',
                        lambda machine: machine.commit('claim-1', idempotency_key='commit-1', **self._commit_body()),
                        fault='partial',
                    )
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                view = recovered.machine('settlement').view('claim-1')
                self.assertEqual(view['phase'], 'CAPTURED')
                self.assertEqual(view['claim']['confirmed_cash'], 0)
                self.assertIs(view['durable'], False)
                self.assertIs(view['funds_executed'], False)
                committed = recovered.call(
                    'settlement',
                    lambda machine: machine.commit('claim-1', idempotency_key='commit-1', **self._commit_body()),
                )
                self.assertFalse(committed['duplicate'])
                self.assertEqual(
                    recovered.machine('settlement').view('claim-1')['claim']['confirmed_cash'],
                    97_000,
                )
                distributed = recovered.call(
                    'settlement',
                    lambda machine: machine.distribute(
                        'claim-1', idempotency_key='dist-1', order=['platform', 'organizer'],
                    ),
                )
                self.assertEqual(distributed['effect'], {'platform': 5_000, 'organizer': 92_000})
                digest = recovered.machine('settlement').state_digest()
                entries = recovered.machine('settlement').export_journal()
            finally:
                recovered.close()
            restarted = self.backend.open_boundary(tmp)
            try:
                machine = restarted.machine('settlement')
                self.assertEqual(machine.state_digest(), digest)
                self.assertEqual(machine.export_journal(), entries)
                self.assertIs(machine.view('claim-1')['durable'], False)
                replay = restarted.call(
                    'settlement',
                    lambda current: current.distribute(
                        'claim-1', idempotency_key='dist-1', order=['platform', 'organizer'],
                    ),
                )
                self.assertTrue(replay['duplicate'])
                self.assertIsNone(replay['applied'])
                claim = machine.view('claim-1')['claim']
                self.assertEqual(claim['confirmed_cash'], 97_000)
                organizer = next(item for item in claim['obligations'] if item['payee'] == 'organizer')
                self.assertEqual(organizer['outstanding'], 3_000)
                self.assertEqual(machine.state_digest(), digest)
            finally:
                restarted.close()

    def test_settlement_crash_before_durable_authorize_applies_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                boundary.call('settlement', lambda machine: machine.initiate('claim-1', idempotency_key='init-1', **self._initiate_body()))
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call(
                        'settlement',
                        lambda machine: machine.authorize('claim-1', idempotency_key='auth-1'),
                        fault='crash_before_durable',
                    )
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                self.assertEqual(recovered.machine('settlement').view('claim-1')['phase'], 'INITIATED')
                authorized = recovered.call(
                    'settlement',
                    lambda machine: machine.authorize('claim-1', idempotency_key='auth-1'),
                )
                self.assertFalse(authorized['duplicate'])
                replay = recovered.call(
                    'settlement',
                    lambda machine: machine.authorize('claim-1', idempotency_key='auth-1'),
                )
                self.assertTrue(replay['duplicate'])
                self.assertEqual(recovered.machine('settlement').view('claim-1')['phase'], 'AUTHORIZED')
                self.assertEqual(
                    [entry['op'] for entry in recovered.machine('settlement').export_journal()],
                    ['initiate', 'authorize'],
                )
            finally:
                recovered.close()

    def test_concurrent_settlement_initiate_posts_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                start = threading.Barrier(2)
                duplicates = []
                errors = []

                def worker():
                    try:
                        start.wait(timeout=2)
                        result = boundary.call(
                            'settlement',
                            lambda machine: machine.initiate(
                                'claim-1', idempotency_key='init-1', **self._initiate_body(),
                            ),
                        )
                        duplicates.append(result['duplicate'])
                    except Exception as exc:
                        errors.append(type(exc).__name__)

                threads = [threading.Thread(target=worker) for _ in range(2)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                    self.assertFalse(thread.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(sorted(duplicates), [False, True])
                view = boundary.machine('settlement').view('claim-1')
                self.assertEqual(view['accepted_entries'], 1)
                self.assertEqual(view['gross'], 100_000)
                self.assertIs(view['funds_executed'], False)
            finally:
                boundary.close()

    def test_reservation_hold_survives_restart_and_a_torn_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._reservation_show(boundary)
                with self.assertRaises(self.backend.fault_error):
                    boundary.call('reservation', lambda machine: self._hold(machine, 'reserve-1', 'hold-1'), fault='partial')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                self.assertEqual(
                    code(lambda: recovered.machine('reservation').view('reserve-1'), ReservationError),
                    'UNKNOWN_RESERVATION',
                )
                held = recovered.call('reservation', lambda machine: self._hold(machine, 'reserve-1', 'hold-1'))
                self.assertFalse(held['duplicate'])
                digest = recovered.machine('reservation').state_digest()
            finally:
                recovered.close()
            restarted = self.backend.open_boundary(tmp)
            try:
                machine = restarted.machine('reservation')
                self.assertEqual(machine.state_digest(), digest)
                self.assertEqual(machine.view('reserve-1')['phase'], 'HELD')
                self.assertEqual(machine.view('reserve-1')['slot_state'], 'RESERVED')
                self.assertIs(machine.view('reserve-1')['durable'], False)
                replay = restarted.call('reservation', lambda current: self._hold(current, 'reserve-1', 'hold-1'))
                self.assertTrue(replay['duplicate'])
                self.assertEqual(
                    code(
                        lambda: restarted.call(
                            'reservation', lambda current: self._hold(current, 'reserve-2', 'hold-2'),
                        ),
                        ReservationError,
                    ),
                    'SLOT_OCCUPIED',
                )
                self.assertEqual(machine.view('reserve-1')['phase'], 'HELD')
                self.assertEqual(
                    [entry['op'] for entry in machine.export_journal() if entry['op'] == 'hold'],
                    ['hold'],
                )
                self.assertEqual(machine.state_digest(), digest)
            finally:
                restarted.close()

    def test_concurrent_reservation_holds_occupy_the_slot_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._reservation_show(boundary)
                start = threading.Barrier(2)
                errors = []
                applied = []

                def worker(reservation, key):
                    try:
                        start.wait(timeout=2)
                        result = boundary.call(
                            'reservation',
                            lambda machine, reservation=reservation, key=key: self._hold(machine, reservation, key),
                        )
                        applied.append(result['duplicate'])
                    except ReservationError as exc:
                        errors.append(exc.code)
                    except Exception as exc:
                        errors.append(type(exc).__name__)

                threads = [
                    threading.Thread(target=worker, args=('reserve-1', 'hold-1')),
                    threading.Thread(target=worker, args=('reserve-2', 'hold-2')),
                ]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                    self.assertFalse(thread.is_alive())
                self.assertEqual(errors, ['SLOT_OCCUPIED'])
                self.assertEqual(applied, [False])
                holds = [
                    entry for entry in boundary.machine('reservation').export_journal()
                    if entry['op'] == 'hold'
                ]
                self.assertEqual(len(holds), 1)
            finally:
                boundary.close()

    def test_resale_transfer_does_not_bump_version_twice_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._resale_until_paid(boundary)
                with self.assertRaises(self.backend.fault_error):
                    boundary.call(
                        'resale',
                        lambda machine: machine.accept_resale(
                            'transfer-1', idempotency_key='transfer-1', listing_id='list-1',
                        ),
                        fault='partial',
                    )
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                listing = recovered.machine('resale').view('list-1')
                self.assertEqual(listing['phase'], 'PAYMENT_NOTED')
                self.assertIs(listing['ownership_transferred'], False)
                self.assertEqual(listing['current_version'], 1)
                self.assertEqual(listing['holder_role'], 'buyer-1')
                self.assertIs(listing['durable'], False)
                transferred = recovered.call(
                    'resale',
                    lambda machine: machine.accept_resale(
                        'transfer-1', idempotency_key='transfer-1', listing_id='list-1',
                    ),
                )
                self.assertFalse(transferred['duplicate'])
                self.assertEqual(transferred['evidence']['version_after'], 2)
                self.assertEqual(transferred['evidence']['to_role'], 'buyer-2')
                digest = recovered.machine('resale').state_digest()
            finally:
                recovered.close()
            restarted = self.backend.open_boundary(tmp)
            try:
                machine = restarted.machine('resale')
                self.assertEqual(machine.state_digest(), digest)
                replay = restarted.call(
                    'resale',
                    lambda current: current.accept_resale(
                        'transfer-1', idempotency_key='transfer-1', listing_id='list-1',
                    ),
                )
                self.assertTrue(replay['duplicate'])
                self.assertEqual(replay['evidence']['version_after'], 2)
                self.assertEqual(
                    code(
                        lambda: restarted.call(
                            'resale',
                            lambda current: current.accept_resale(
                                'transfer-2', idempotency_key='transfer-2', listing_id='list-1',
                            ),
                        ),
                        ResaleError,
                    ),
                    'ILLEGAL_TRANSITION',
                )
                view = machine.view('list-1')
                self.assertEqual(view['holder_role'], 'buyer-2')
                self.assertEqual(view['current_version'], 2)
                self.assertIs(view['funds_executed'], False)
                self.assertIs(view['chain_owner_current'], False)
                self.assertEqual(machine.state_digest(), digest)
            finally:
                restarted.close()

    def test_credit_exposure_is_not_drawn_twice_across_restart(self):
        face = committed_face()
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._credit_until_approved(boundary, face)
                with self.assertRaises(self.backend.fault_error):
                    boundary.call(
                        'credit',
                        lambda machine: machine.draw('adv-1', idempotency_key='draw-1', draw_id='draw-1'),
                        fault='partial',
                    )
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                self.assertEqual(recovered.machine('credit').view('adv-1')['outstanding_exposure'], 0)
                self.assertEqual(recovered.machine('credit').view('adv-1')['phase'], 'APPROVED')
                drawn = recovered.call(
                    'credit',
                    lambda machine: machine.draw('adv-1', idempotency_key='draw-1', draw_id='draw-1'),
                )
                self.assertFalse(drawn['duplicate'])
                self.assertEqual(drawn['effect']['outstanding_exposure'], 80_000)
                self.assertIs(drawn['credit']['durable'], False)
                self.assertIs(drawn['funds_executed'], False)
                digest = recovered.machine('credit').state_digest()
            finally:
                recovered.close()
            restarted = self.backend.open_boundary(tmp)
            try:
                machine = restarted.machine('credit')
                self.assertEqual(machine.state_digest(), digest)
                replay = restarted.call(
                    'credit',
                    lambda current: current.draw('adv-1', idempotency_key='draw-1', draw_id='draw-1'),
                )
                self.assertTrue(replay['duplicate'])
                self.assertEqual(
                    code(
                        lambda: restarted.call(
                            'credit',
                            lambda current: current.draw('adv-1', idempotency_key='draw-2', draw_id='draw-2'),
                        ),
                        CreditError,
                    ),
                    'DUPLICATE_DRAW',
                )
                self.assertEqual(machine.view('adv-1')['outstanding_exposure'], 80_000)
                self.assertEqual(machine.state_digest(), digest)
            finally:
                restarted.close()

    def test_admission_consume_survives_restart_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._admission_until_authorized(boundary)
                with self.assertRaises(self.backend.fault_error):
                    boundary.call('admission', lambda machine: self._consume(machine), fault='partial')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                self.assertEqual(recovered.machine('admission').view('issue-1')['phase'], 'AUTHORIZED')
                self.assertEqual(recovered.machine('admission').view('issue-1')['version'], 1)
                consumed = recovered.call('admission', lambda machine: self._consume(machine))
                self.assertFalse(consumed['duplicate'])
                self.assertEqual(consumed['evidence']['decision'], 'CONSUMED_ONCE')
                self.assertEqual(consumed['evidence']['version_after'], 2)
                self.assertIs(consumed['evidence']['admission_routing_production'], False)
                digest = recovered.machine('admission').state_digest()
            finally:
                recovered.close()
            restarted = self.backend.open_boundary(tmp)
            try:
                machine = restarted.machine('admission')
                self.assertEqual(machine.state_digest(), digest)
                replay = restarted.call('admission', lambda current: self._consume(current))
                self.assertTrue(replay['duplicate'])
                self.assertEqual(replay['evidence']['version_after'], 2)
                self.assertEqual(
                    code(
                        lambda: restarted.call(
                            'admission',
                            lambda current: current.consume(
                                'consume-2',
                                idempotency_key='consume-2',
                                right_id='issue-1',
                                version=2,
                                gate_role='gate-a',
                                request=REQ,
                            ),
                        ),
                        AdmissionError,
                    ),
                    'ALREADY_CONSUMED',
                )
                self.assertEqual(machine.view('issue-1')['phase'], 'CONSUMED')
                self.assertEqual(machine.view('issue-1')['version'], 2)
                self.assertIs(machine.view('issue-1')['durable'], False)
                self.assertEqual(machine.state_digest(), digest)
            finally:
                restarted.close()

    def test_reservation_crash_before_durable_hold_is_absent_until_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._reservation_show(boundary)
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call(
                        'reservation',
                        lambda machine: self._hold(machine, 'reserve-1', 'hold-1'),
                        fault='crash_before_durable',
                    )
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                self.assertEqual(
                    code(lambda: recovered.machine('reservation').view('reserve-1'), ReservationError),
                    'UNKNOWN_RESERVATION',
                )
                held = recovered.call('reservation', lambda machine: self._hold(machine, 'reserve-1', 'hold-1'))
                self.assertFalse(held['duplicate'])
                replay = recovered.call('reservation', lambda machine: self._hold(machine, 'reserve-1', 'hold-1'))
                self.assertTrue(replay['duplicate'])
                self.assertEqual(
                    [entry['op'] for entry in recovered.machine('reservation').export_journal() if entry['op'] == 'hold'],
                    ['hold'],
                )
                self.assertIs(recovered.machine('reservation').view('reserve-1')['durable'], False)
            finally:
                recovered.close()

    def test_ai_delegation_registry_opens_once_and_issue_replays_across_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                opened = self._ai_delegation_opened(boundary)
                self.assertIs(opened['opened'], True)
                self.assertIs(opened['durable'], False)
                self.assertIs(opened['execution_enabled'], False)
                issued = boundary.call('ai_delegation', ai_delegation_issue)
                self.assertFalse(issued['duplicate'])
                self.assertIs(issued['grant']['durable'], False)
                self.assertIs(issued['grant']['execution_enabled'], False)
                digest = boundary.machine('ai_delegation').state_digest()
                journal = boundary.machine('ai_delegation').export_journal()
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                machine = recovered.machine('ai_delegation')
                self.assertEqual(machine.state_digest(), digest)
                self.assertEqual(machine.export_journal(), journal)
                self.assertEqual(machine.view_grant(AI_GRANT)['phase'], 'ACTIVE')
                replay = recovered.call('ai_delegation', ai_delegation_issue)
                self.assertTrue(replay['duplicate'])
                self.assertEqual(replay['grant'], issued['grant'])
                # open_registry carries no idempotency key: the wrap refuses a
                # second open instead of returning a duplicate result (class B).
                self.assertEqual(
                    code(
                        lambda: recovered.call('ai_delegation', self._ai_delegation_open_call()),
                        WrapError,
                    ),
                    'ALREADY_OPEN',
                )
                self.assertEqual(machine.state_digest(), digest)
                self.assertEqual(machine.export_journal(), journal)
            finally:
                recovered.close()

    def test_ai_delegation_torn_revoke_recovers_and_replays_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._ai_delegation_opened(boundary)
                boundary.call('ai_delegation', ai_delegation_issue)
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call(
                        'ai_delegation',
                        lambda machine: machine.revoke_grant(AI_ISSUER, AI_GRANT, 'fixture-reason'),
                        fault='partial',
                    )
                self.assertEqual(raised.exception.code, 'PARTIAL_WRITE')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                machine = recovered.machine('ai_delegation')
                self.assertEqual(machine.view_grant(AI_GRANT)['phase'], 'ACTIVE')
                self.assertIs(machine.view_grant(AI_GRANT)['durable'], False)
                revoked = recovered.call(
                    'ai_delegation',
                    lambda machine: machine.revoke_grant(AI_ISSUER, AI_GRANT, 'fixture-reason'),
                )
                self.assertFalse(revoked['duplicate'])
                self.assertEqual(revoked['grant']['phase'], 'REVOKED')
                self.assertIs(revoked['grant']['durable'], False)
                self.assertIs(revoked['grant']['execution_enabled'], False)
                replay = recovered.call(
                    'ai_delegation',
                    lambda machine: machine.revoke_grant(AI_ISSUER, AI_GRANT, 'fixture-reason'),
                )
                self.assertTrue(replay['duplicate'])
                self.assertEqual(replay['grant']['phase'], 'REVOKED')
                self.assertEqual(
                    [entry['op'] for entry in machine.export_journal()],
                    ['open_registry', 'issue_grant', 'revoke_grant'],
                )
                self.assertEqual(
                    code(lambda: machine.attempt_execution(AI_ISSUER, 'p1'), AiDelegationError),
                    'DELEGATED_EXECUTION_DISABLED',
                )
            finally:
                recovered.close()

    def test_ai_delegation_crash_before_durable_issue_leaves_no_grant(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._ai_delegation_opened(boundary)
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call('ai_delegation', ai_delegation_issue, fault='crash_before_durable')
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                machine = recovered.machine('ai_delegation')
                self.assertEqual(
                    code(lambda: machine.view_grant(AI_GRANT), AiDelegationError),
                    'UNKNOWN_GRANT',
                )
                issued = recovered.call('ai_delegation', ai_delegation_issue)
                self.assertFalse(issued['duplicate'])
                self.assertIs(issued['grant']['durable'], False)
                replay = recovered.call('ai_delegation', ai_delegation_issue)
                self.assertTrue(replay['duplicate'])
                self.assertEqual(replay['grant'], issued['grant'])
                self.assertEqual(
                    [entry['op'] for entry in machine.export_journal()],
                    ['open_registry', 'issue_grant'],
                )
            finally:
                recovered.close()

    def test_reward_open_observe_and_hold_replay_across_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                opened = self._reward_opened(boundary)
                self.assertIs(opened['opened'], True)
                self.assertIs(opened['durable'], False)
                observed = boundary.call('reward', reward_observe)
                self.assertFalse(observed['duplicate'])
                self.assertIs(observed['reward']['durable'], False)
                held = boundary.call(
                    'reward',
                    lambda machine: machine.hold(reward_rid(), idempotency_key='hold-1'),
                )
                self.assertFalse(held['duplicate'])
                self.assertEqual(held['reward']['phase'], 'HELD')
                digest = boundary.machine('reward').state_digest()
                journal = boundary.machine('reward').export_journal()
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                machine = recovered.machine('reward')
                self.assertEqual(machine.state_digest(), digest)
                self.assertEqual(machine.export_journal(), journal)
                self.assertEqual(machine.view(reward_rid())['phase'], 'HELD')
                replay = recovered.call(
                    'reward',
                    lambda machine: machine.hold(reward_rid(), idempotency_key='hold-1'),
                )
                self.assertTrue(replay['duplicate'])
                self.assertIsNone(replay['applied'])
                self.assertEqual(replay['reward'], held['reward'])
                # open carries no idempotency key: the wrap refuses a second
                # open instead of returning a duplicate result (class B).
                self.assertEqual(
                    code(
                        lambda: recovered.call('reward', self._reward_open_call()),
                        RewardWrapError,
                    ),
                    'ALREADY_OPEN',
                )
                self.assertEqual(machine.state_digest(), digest)
                self.assertEqual(machine.export_journal(), journal)
            finally:
                recovered.close()

    def test_reward_torn_mark_eligible_recovers_and_replays_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._reward_opened(boundary)
                boundary.call('reward', reward_observe)
                boundary.call(
                    'reward',
                    lambda machine: machine.hold(reward_rid(), idempotency_key='hold-1'),
                )
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call('reward', reward_mark_eligible, fault='partial')
                self.assertEqual(raised.exception.code, 'PARTIAL_WRITE')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                machine = recovered.machine('reward')
                self.assertEqual(machine.view(reward_rid())['phase'], 'HELD')
                self.assertIs(machine.view(reward_rid())['durable'], False)
                eligible = recovered.call('reward', reward_mark_eligible)
                self.assertFalse(eligible['duplicate'])
                self.assertEqual(eligible['reward']['phase'], 'ELIGIBLE')
                self.assertIs(eligible['reward']['durable'], False)
                replay = recovered.call('reward', reward_mark_eligible)
                self.assertTrue(replay['duplicate'])
                self.assertIsNone(replay['applied'])
                self.assertEqual(replay['reward'], eligible['reward'])
                self.assertEqual(
                    [entry['op'] for entry in machine.export_journal()],
                    ['open', 'observe', 'hold', 'mark_eligible'],
                )
                self.assertIs(machine.view(reward_rid())['durable'], False)
                self.assertEqual(
                    code(lambda: machine.reject_external('TRANSFER'), TokenRewardError),
                    'EXTERNAL_EXECUTION_UNSUPPORTED',
                )
            finally:
                recovered.close()

    def test_reward_crash_before_durable_observe_leaves_no_reward(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                self._reward_opened(boundary)
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call('reward', reward_observe, fault='crash_before_durable')
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
            finally:
                boundary.close()
            recovered = self.backend.open_boundary(tmp)
            try:
                machine = recovered.machine('reward')
                self.assertEqual(
                    code(lambda: machine.view(reward_rid()), TokenRewardError),
                    'UNKNOWN_REWARD',
                )
                observed = recovered.call('reward', reward_observe)
                self.assertFalse(observed['duplicate'])
                self.assertIs(observed['reward']['durable'], False)
                replay = recovered.call('reward', reward_observe)
                self.assertTrue(replay['duplicate'])
                self.assertEqual(replay['reward'], observed['reward'])
                self.assertEqual(
                    [entry['op'] for entry in machine.export_journal()],
                    ['open', 'observe'],
                )
            finally:
                recovered.close()

    def test_crash_before_durable_leaves_the_attempt_out_of_the_record_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.backend.open_store(tmp)
            try:
                store.append(self._core_record('op-kept'))
                before = list(store.records)
                size = store.committed_bytes
                with self.assertRaises(self.backend.fault_error) as raised:
                    store.append(self._core_record('op-crashed'), fault='crash_before_durable')
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
                self.assertEqual(store.records, before)
                self.assertEqual(store.committed_bytes, size)
                self.assertTrue(store.can_accept(1, len(before) + 1, size + 1))
                self.assertFalse(store.has_operation('op-crashed'))
            finally:
                store.close()
            recovered = self.backend.open_store(tmp)
            try:
                self.assertTrue(recovered.has_operation('op-kept'))
                self.assertFalse(recovered.has_operation('op-crashed'))
                self.assertEqual(len(recovered.records), 1)
            finally:
                recovered.close()

    def test_partial_attempt_does_not_consume_a_record_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.backend.open_store(tmp)
            try:
                store.append(self._core_record('op-kept'))
                count = len(store.records)
                size = store.committed_bytes
                with self.assertRaises(self.backend.fault_error) as raised:
                    store.append(self._core_record('op-torn'), fault='partial')
                self.assertEqual(raised.exception.code, 'PARTIAL_WRITE')
                self.assertEqual(len(store.records), count)
                self.assertEqual(store.committed_bytes, size)
                self.assertTrue(store.can_accept(1, count + 1, size + 1))
                self.assertFalse(store.has_operation('op-torn'))
            finally:
                store.close()
            recovered = self.backend.open_store(tmp)
            try:
                self.assertEqual(
                    [record['operationId'] for record in recovered.records],
                    ['op-kept'],
                )
                self.assertTrue(recovered.can_accept(1, 2, recovered.committed_bytes + 1))
            finally:
                recovered.close()

    def _core_record(self, operation_id):
        return {
            'kind': 'core_commit',
            'machine': 'integration_core',
            'operationId': operation_id,
            'actor': 'operator',
            'action': 'advance_clock',
            'body': {'now': 1},
            'receiptDigest': 'ab' * 32,
        }

    def _initiate_body(self):
        return dict(
            trade_id='trade-1',
            gross=100_000,
            debtor_role='fixture-merchant',
            policy=settlement_policy(),
        )

    def _commit_body(self):
        return dict(
            movement_id='move-1',
            gross=100_000,
            amount=97_000,
            fee=3_000,
            tax=0,
            held=0,
            adjustment=0,
        )

    def _settlement_until_capture(self, boundary):
        boundary.call(
            'settlement',
            lambda machine: machine.initiate('claim-1', idempotency_key='init-1', **self._initiate_body()),
        )
        boundary.call('settlement', lambda machine: machine.authorize('claim-1', idempotency_key='auth-1'))
        boundary.call('settlement', lambda machine: machine.capture('claim-1', idempotency_key='cap-1'))

    def _reservation_show(self, boundary):
        boundary.call(
            'reservation',
            lambda machine: machine.set_clock('clock', idempotency_key='clock-1', now_ms=T0),
        )
        boundary.call(
            'reservation',
            lambda machine: machine.register_show('show-1', idempotency_key='show-1', **show_kwargs()),
        )

    def _hold(self, machine, reservation, key):
        return machine.hold(
            reservation,
            idempotency_key=key,
            show_id='show-1',
            slot=0,
            buyer_role='buyer-1',
            expires_ms=EXPIRES,
        )

    def _resale_until_paid(self, boundary):
        boundary.call(
            'resale',
            lambda machine: machine.set_clock('clock', idempotency_key='clock-1', now_ms=T0),
        )
        boundary.call(
            'resale',
            lambda machine: machine.adopt_issued('issue-1', idempotency_key='adopt-1', **resale_adopt_body()),
        )
        boundary.call(
            'resale',
            lambda machine: machine.list_resale(
                'list-1',
                idempotency_key='list-1',
                right_id='issue-1',
                version=1,
                seller_role='buyer-1',
                recipient_role='buyer-2',
                amount=PRICE,
                expires_ms=EXPIRES,
                reservation_id=None,
            ),
        )
        boundary.call(
            'resale',
            lambda machine: machine.observe_resale_payment(
                'list-1',
                idempotency_key='pay-1',
                payment_ref=SALE_PAY,
                amount=PRICE,
            ),
        )

    def _credit_until_approved(self, boundary, face):
        boundary.call(
            'credit',
            lambda machine: machine.offer(
                'adv-1',
                idempotency_key='offer-1',
                face=face,
                amount=80_000,
                beneficiary_role='fixture-label',
            ),
        )
        boundary.call('credit', lambda machine: machine.approve('adv-1', idempotency_key='approve-1'))

    def _admission_until_authorized(self, boundary):
        boundary.call(
            'admission',
            lambda machine: machine.set_clock('clock', idempotency_key='clock-1', now_ms=T0),
        )
        boundary.call(
            'admission',
            lambda machine: machine.adopt_issued('issue-1', idempotency_key='adopt-1', **admission_body()),
        )
        boundary.call(
            'admission',
            lambda machine: machine.authorize_admission(
                'admit-1',
                idempotency_key='admit-1',
                right_id='issue-1',
                version=1,
                holder_role='buyer-1',
                gate_role='gate-a',
                request=REQ,
                expires_ms=ADMISSION_EXPIRES,
            ),
        )

    def _consume(self, machine):
        return machine.consume(
            'consume-1',
            idempotency_key='consume-1',
            right_id='issue-1',
            version=1,
            gate_role='gate-a',
            request=REQ,
        )

    def _ai_delegation_open_call(self):
        return lambda machine: machine.open_registry([AI_ISSUER], [AI_AGENT])

    def _ai_delegation_opened(self, boundary):
        return boundary.call('ai_delegation', self._ai_delegation_open_call())

    def _reward_open_call(self):
        return lambda machine: machine.open(reward_opening())

    def _reward_opened(self, boundary):
        return boundary.call('reward', self._reward_open_call())


def assert_budget_rejection(test, ready_call, command_call, domain):
    """Shared command-level budget scenario over transport-neutral callbacks.

    ready_call returns (status, view); command_call(op, actor, action, body)
    returns (status, receipt). Configure a one-record budget before calling.
    The domain is supplied by the caller, from the existing contract catalogue.
    """
    status, ready = ready_call()
    test.assertEqual(status, 200)
    test.assertIs(ready['durable'], False)
    test.assertIs(ready['localFileJournal'], True)
    test.assertIs(ready['productionReadiness'], False)
    test.assertIs(ready['productionConformance'], False)
    test.assertEqual(ready['journalRecords'], 0)
    status, payload = command_call(
        'op-clock', 'operator', 'advance_clock',
        {'domain': domain, 'now': 50},
    )
    test.assertEqual(status, 200)
    test.assertEqual(payload['result']['logicalTime'], 50)
    status, payload = command_call(
        'op-clock-2', 'operator', 'advance_clock',
        {'domain': domain, 'now': 60},
    )
    test.assertEqual(status, 503)
    test.assertEqual(payload['error'], 'JOURNAL_BUDGET')
    status, payload = command_call(
        'op-clock', 'operator', 'advance_clock',
        {'domain': domain, 'now': 50},
    )
    test.assertEqual(status, 200)
    test.assertEqual(payload['sequence'], 1)
    test.assertEqual(payload['result']['logicalTime'], 50)
