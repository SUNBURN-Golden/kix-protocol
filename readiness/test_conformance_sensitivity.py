"""Negative controls: the conformance suite must fail on faulty backends.

Each adapter below subclasses LocalReadinessAdapter and breaks exactly one
property that a BackendConformance case checks. Every faulty adapter is run
through its mapped case programmatically and must NOT pass, and the same case
run against the unmodified LocalReadinessAdapter must pass. The fault-to-case
map and the uncovered-property gaps are kept in readiness/CONFORMANCE.md.

These are in-process test doubles over the local readiness wrapper. This is
not a power-loss proof, not a PostgreSQL or other candidate-backend test, and
not a backend adoption. Run directly:

    python3 -m unittest readiness.test_conformance_sensitivity
"""

from __future__ import annotations

import unittest

from readiness.boundary import FsmBoundary
from readiness.codec import canonical_json
from readiness.conformance import BackendConformance, ReservationError
from readiness.local_adapter import LocalReadinessAdapter
from readiness.migrate import SCHEMA_VERSION
from readiness.store import ReadinessFault, ReadinessStore

FAULT_CASE_MAP = {
    'drop_on_reopen': 'test_budget_rejection_preserves_records_and_replay_identity',
    'replay_append_twice': 'test_settlement_cash_survives_restart_and_a_torn_commit',
    'partial_consumes_slot': 'test_partial_attempt_does_not_consume_a_record_slot',
    'crash_attempt_durable': 'test_crash_before_durable_leaves_the_attempt_out_of_the_record_budget',
    'budget_ignored': 'test_budget_rejection_preserves_records_and_replay_identity',
    'double_hold': 'test_concurrent_reservation_holds_occupy_the_slot_once',
    'leaky_handle': 'test_settlement_cash_survives_restart_and_a_torn_commit',
    'ai_drop_acknowledged': 'test_ai_delegation_registry_opens_once_and_issue_replays_across_restart',
    'ai_partial_retained': 'test_ai_delegation_torn_revoke_recovers_and_replays_once',
    'ai_crash_attempt_durable': 'test_ai_delegation_crash_before_durable_issue_leaves_no_grant',
    'reward_drop_acknowledged': 'test_reward_open_observe_and_hold_replay_across_restart',
    'reward_partial_retained': 'test_reward_torn_mark_eligible_recovers_and_replays_once',
    'reward_crash_attempt_durable': 'test_reward_crash_before_durable_observe_leaves_no_reward',
}


class DropAcknowledgedBoundaryAdapter(LocalReadinessAdapter):
    """Lose one selected machine's acknowledged entry before normal recovery."""

    def __init__(self, machine_name):
        self.machine_name = machine_name

    def open_boundary(self, directory):
        machine_name = self.machine_name

        class DropAcknowledgedBoundary(FsmBoundary):
            def _recover(self):
                for index in range(len(self.store.records) - 1, -1, -1):
                    record = self.store.records[index]
                    if record.get('kind') == 'fsm_commit' and record.get('machine') == machine_name:
                        self.store.records.pop(index)
                        break
                super()._recover()

        return DropAcknowledgedBoundary(directory)


class PersistFaultAttemptAdapter(LocalReadinessAdapter):
    """Commit an attempt requested as torn or crashed, then report its fault.

    The partial mutant incorrectly commits the whole attempt; it does not
    simulate physical media tearing. Only this handle's append is wrapped.
    """

    def __init__(self, machine_name, fault_kind):
        self.machine_name = machine_name
        self.fault_kind = fault_kind

    def open_boundary(self, directory):
        boundary = FsmBoundary(directory)
        append = boundary.store.append

        def persist_attempt(body, fault=None):
            if (body.get('kind') == 'fsm_commit'
                    and body.get('machine') == self.machine_name
                    and fault == self.fault_kind):
                append(body)
                raise ReadinessFault({
                    'partial': 'PARTIAL_WRITE',
                    'crash_before_durable': 'CRASH_BEFORE_DURABLE',
                }[fault])
            return append(body, fault=fault)

        boundary.store.append = persist_attempt
        return boundary


class DropOnReopenAdapter(LocalReadinessAdapter):
    """A reopened store silently drops the last acknowledged record."""

    @staticmethod
    def open_store(directory):
        store = ReadinessStore.open(directory)
        if store.records:
            store.records.pop()
        return store


class _ReplayAsNew:
    """Lose the operation identity when dispatching a duplicate distribution."""

    def __init__(self, machine):
        self._machine = machine

    def __getattr__(self, name):
        return getattr(self._machine, name)

    def distribute(self, settlement_id, *, idempotency_key, order):
        return self._machine.distribute(
            settlement_id,
            idempotency_key=idempotency_key + '-fault-replay',
            order=order,
        )


class _ReplayTwiceBoundary(FsmBoundary):
    def call(self, machine_name, fn, *, fault=None):
        result = super().call(machine_name, fn, fault=fault)
        if machine_name == 'settlement' and result.get('duplicate'):
            # Dispatch the same caller's operation again as a fresh command.
            # The real FSM and append path apply a second journal entry.
            return super().call(
                machine_name, lambda machine: fn(_ReplayAsNew(machine)),
            )
        return result


class ReplayTwiceAdapter(LocalReadinessAdapter):
    """An operation replay is wrongly dispatched as a new application."""

    @staticmethod
    def open_boundary(directory):
        return _ReplayTwiceBoundary(directory)


class _SlottingPartialStore(ReadinessStore):
    """A torn attempt still consumes the record slot and the byte budget."""

    def append(self, body, fault=None):
        if fault != 'partial':
            return super().append(body, fault=fault)
        try:
            return super().append(body, fault=fault)
        except ReadinessFault:
            # Keep the real torn write/recovery behavior; corrupt only live
            # record/byte accounting by charging the unacknowledged attempt.
            record = dict(
                body, schema=SCHEMA_VERSION,
                protocolTruth=False, productionConformance=False,
            )
            self.records.append(record)
            self.committed_bytes += 8 + len(canonical_json(record).encode('utf-8'))
            raise


class PartialSlotAdapter(LocalReadinessAdapter):
    @staticmethod
    def open_store(directory):
        return _SlottingPartialStore.open(directory)


class _DurableCrashStore(ReadinessStore):
    """A crash_before_durable attempt is committed before it reports."""

    def append(self, body, fault=None):
        if fault != 'crash_before_durable':
            return super().append(body, fault=fault)
        before = list(self.records)
        size = self.committed_bytes
        super().append(body)
        # Hide the attempt from live accounting, as the correct adapter does;
        # only recovery exposes the incorrectly durable record.
        self.records = before
        self.committed_bytes = size
        raise ReadinessFault('CRASH_BEFORE_DURABLE')


class CrashDurableAdapter(LocalReadinessAdapter):
    @staticmethod
    def open_store(directory):
        return _DurableCrashStore.open(directory)


class _BudgetBlindStore(ReadinessStore):
    """Ignore one budget dimension while preserving the other predicate."""

    def budget_decision(self, extra, max_records, max_bytes):
        if self.ignored_limit == 'records':
            max_records = len(self.records) + 1
        else:
            max_bytes = self.committed_bytes + extra + 1
        return super().budget_decision(extra, max_records, max_bytes)


class BudgetBlindAdapter(LocalReadinessAdapter):
    def __init__(self, ignored_limit):
        self.ignored_limit = ignored_limit

    def open_store(self, directory):
        store = _BudgetBlindStore.open(directory)
        store.ignored_limit = self.ignored_limit
        return store


class _HoldLossHidden:
    """Passes calls through but reports a losing hold on one slot as a win."""

    def __init__(self, machine):
        self._machine = machine

    def __getattr__(self, name):
        return getattr(self._machine, name)

    def hold(self, *args, **kwargs):
        try:
            return self._machine.hold(*args, **kwargs)
        except ReservationError as exc:
            if exc.code == 'SLOT_OCCUPIED':
                return {'duplicate': False}
            raise


class _SecondHoldWins(FsmBoundary):
    def call(self, machine_name, fn, *, fault=None):
        if machine_name != 'reservation':
            return super().call(machine_name, fn, fault=fault)
        return super().call(
            machine_name,
            lambda machine: fn(_HoldLossHidden(machine)),
            fault=fault,
        )


class DoubleHoldAdapter(LocalReadinessAdapter):
    @staticmethod
    def open_boundary(directory):
        return _SecondHoldWins(directory)


class _LeakyHandleBoundary(FsmBoundary):
    """close() never releases the journal handle after an injected fault."""

    def close(self):
        if self.failed:
            return
        super().close()


class LeakyHandleAdapter(LocalReadinessAdapter):
    def __init__(self):
        self.handles = []

    def open_boundary(self, directory):
        boundary = _LeakyHandleBoundary(directory)
        self.handles.append(boundary)
        return boundary

    def cleanup(self):
        # Retain the leak until the conformance case observes JOURNAL_LOCKED,
        # then bypass the mutant close() so the outer test leaks no resources.
        for boundary in self.handles:
            FsmBoundary.close(boundary)
        self.handles.clear()


class _CaseResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.error_codes = []

    def addError(self, test, err):
        self.error_codes.append(getattr(err[1], 'code', None))
        super().addError(test, err)


def _run_case(adapter, case_name):
    suite = type(
        'BoundConformance',
        (BackendConformance, unittest.TestCase),
        {'backend': adapter, '__module__': __name__},
    )
    case = suite(case_name)
    result = _CaseResult()
    try:
        case.run(result)
    finally:
        if isinstance(adapter, LeakyHandleAdapter):
            adapter.cleanup()
    return result


class ConformanceSensitivityTests(unittest.TestCase):
    def _assert_no_nonexecutions(self, result):
        self.assertEqual(result.skipped, [])
        self.assertEqual(result.expectedFailures, [])
        self.assertEqual(result.unexpectedSuccesses, [])

    def _assert_fault_is_caught(self, adapter, case_name, *, error_code=None, recovery_assertion=None):
        caught = _run_case(adapter, case_name)
        self.assertEqual(caught.testsRun, 1)
        self._assert_no_nonexecutions(caught)
        self.assertFalse(
            caught.wasSuccessful(),
            f'{case_name} unexpectedly passed for {type(adapter).__name__}',
        )
        offenders = [test.id() for test, _traceback in caught.failures + caught.errors]
        self.assertEqual(len(offenders), 1)
        self.assertEqual(offenders[0].rsplit('.', 1)[-1], case_name)
        if error_code is None:
            self.assertEqual(caught.errors, [], caught.errors)
            self.assertEqual(len(caught.failures), 1)
            if recovery_assertion is not None:
                self.assertIn(recovery_assertion, caught.failures[0][1])
        else:
            self.assertEqual(caught.failures, [])
            self.assertEqual(caught.error_codes, [error_code], caught.errors)
        control = _run_case(LocalReadinessAdapter(), case_name)
        self.assertEqual(control.testsRun, 1)
        self._assert_no_nonexecutions(control)
        self.assertTrue(
            control.wasSuccessful(),
            f'control run of {case_name}: {control.failures + control.errors}',
        )

    def test_drop_on_reopen_is_caught(self):
        self._assert_fault_is_caught(
            DropOnReopenAdapter(), FAULT_CASE_MAP['drop_on_reopen'],
        )

    def test_replay_append_twice_is_caught(self):
        self._assert_fault_is_caught(
            ReplayTwiceAdapter(), FAULT_CASE_MAP['replay_append_twice'],
        )

    def test_partial_consumes_slot_is_caught(self):
        self._assert_fault_is_caught(
            PartialSlotAdapter(), FAULT_CASE_MAP['partial_consumes_slot'],
        )

    def test_crash_attempt_durable_is_caught(self):
        self._assert_fault_is_caught(
            CrashDurableAdapter(), FAULT_CASE_MAP['crash_attempt_durable'],
        )

    def test_budget_ignored_is_caught(self):
        for limit in ('records', 'bytes'):
            with self.subTest(limit=limit):
                self._assert_fault_is_caught(
                    BudgetBlindAdapter(limit), FAULT_CASE_MAP['budget_ignored'],
                )

    def test_double_hold_is_caught(self):
        self._assert_fault_is_caught(
            DoubleHoldAdapter(), FAULT_CASE_MAP['double_hold'],
        )

    def test_leaky_handle_is_caught(self):
        self._assert_fault_is_caught(
            LeakyHandleAdapter(), FAULT_CASE_MAP['leaky_handle'],
            error_code='JOURNAL_LOCKED',
        )

    def test_ai_drop_acknowledged_is_caught(self):
        self._assert_fault_is_caught(
            DropAcknowledgedBoundaryAdapter('ai_delegation'),
            FAULT_CASE_MAP['ai_drop_acknowledged'],
            recovery_assertion='self.assertEqual(machine.state_digest(), digest)',
        )

    def test_ai_partial_retained_is_caught(self):
        self._assert_fault_is_caught(
            PersistFaultAttemptAdapter('ai_delegation', 'partial'),
            FAULT_CASE_MAP['ai_partial_retained'],
            recovery_assertion="self.assertEqual(machine.view_grant(AI_GRANT)['phase'], 'ACTIVE')",
        )

    def test_ai_crash_attempt_durable_is_caught(self):
        self._assert_fault_is_caught(
            PersistFaultAttemptAdapter('ai_delegation', 'crash_before_durable'),
            FAULT_CASE_MAP['ai_crash_attempt_durable'],
            recovery_assertion='AssertionError: expected AiDelegationError',
        )

    def test_reward_drop_acknowledged_is_caught(self):
        self._assert_fault_is_caught(
            DropAcknowledgedBoundaryAdapter('reward'),
            FAULT_CASE_MAP['reward_drop_acknowledged'],
            recovery_assertion='self.assertEqual(machine.state_digest(), digest)',
        )

    def test_reward_partial_retained_is_caught(self):
        self._assert_fault_is_caught(
            PersistFaultAttemptAdapter('reward', 'partial'),
            FAULT_CASE_MAP['reward_partial_retained'],
            recovery_assertion="self.assertEqual(machine.view(reward_rid())['phase'], 'HELD')",
        )

    def test_reward_crash_attempt_durable_is_caught(self):
        self._assert_fault_is_caught(
            PersistFaultAttemptAdapter('reward', 'crash_before_durable'),
            FAULT_CASE_MAP['reward_crash_attempt_durable'],
            recovery_assertion='AssertionError: expected TokenRewardError',
        )

    def test_unmodified_adapter_passes_every_case(self):
        names = sorted(
            name for name in dir(BackendConformance)
            if name.startswith('test_') and callable(getattr(BackendConformance, name))
        )
        for name in names:
            with self.subTest(case=name):
                result = _run_case(LocalReadinessAdapter(), name)
                self.assertEqual(result.testsRun, 1)
                self._assert_no_nonexecutions(result)
                self.assertTrue(result.wasSuccessful(), result.failures + result.errors)


if __name__ == '__main__':
    unittest.main()
