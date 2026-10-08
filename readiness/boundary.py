"""Restart boundary around the existing protocol FSMs.

Each accepted FSM journal entry is appended only after the FSM method returns.
Recovery rebuilds machines by calling their public restore methods. The FSMs
remain the semantic source. This boundary does not flip their durable flags
and does not add protocol commands.
"""

from __future__ import annotations

import threading

from readiness.machines import MACHINES, RESTORE
from readiness.migrate import SCHEMA_VERSION
from readiness.observe import boundary_observation
from readiness.store import ReadinessFault, ReadinessStore, StoreError


class ReadinessError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ReadinessClosed(ReadinessError):
    pass


class FsmBoundary:
    """One local journal and the wrapped in-memory machines recovered from it."""

    def __init__(self, directory):
        self.failed = False
        self.last_observation = None
        self._lock = threading.Lock()
        self.store = ReadinessStore.open(directory)
        self.machines = {}
        try:
            self._recover()
        except Exception:
            self.store.close()
            raise

    def machine(self, name):
        if self.failed:
            raise ReadinessClosed('READINESS_CLOSED')
        if name not in RESTORE:
            raise ReadinessError('UNKNOWN_MACHINE')
        return self.machines[name]

    def call(self, machine_name, fn, *, fault=None):
        if machine_name not in RESTORE:
            raise ReadinessError('UNKNOWN_MACHINE')
        with self._lock:
            if self.failed:
                raise ReadinessClosed('READINESS_CLOSED')
            machine = self.machines[machine_name]
            before = machine.export_journal()
            digest_before = machine.state_digest()
            try:
                result = fn(machine)
            except Exception:
                self._guard_unchanged(machine, before, digest_before)
                if self.failed:
                    self._observe(machine_name, 'fault', faultCode='UNJOURNALED_MUTATION')
                else:
                    self._observe(machine_name, 'unchanged', appendedEntries=0)
                raise
            after = machine.export_journal()
            if after[:len(before)] != before:
                self.failed = True
                self._observe(machine_name, 'fault', faultCode='JOURNAL_REWRITE')
                raise ReadinessError('JOURNAL_REWRITE')
            new_entries = after[len(before):]
            if not new_entries:
                if machine.state_digest() != digest_before:
                    self.failed = True
                    self._observe(machine_name, 'fault', faultCode='UNJOURNALED_MUTATION')
                    raise ReadinessError('UNJOURNALED_MUTATION')
                self._observe(machine_name, 'unchanged', appendedEntries=0)
                return result
            try:
                for index, entry in enumerate(new_entries):
                    self.store.append(
                        {'kind': 'fsm_commit', 'machine': machine_name, 'entry': entry},
                        fault=fault if index == 0 else None,
                    )
            except (ReadinessFault, StoreError) as exc:
                self.failed = True
                self._observe(machine_name, 'fault', faultCode=getattr(exc, 'code', None))
                raise
            self._observe(machine_name, 'appended', appendedEntries=len(new_entries))
            return result

    def close(self):
        self.store.close()

    def _recover(self):
        journals = {name: [] for name in MACHINES}
        for record in self.store.records:
            if record.get('kind') != 'fsm_commit':
                raise ReadinessError('UNEXPECTED_RECORD')
            journals[record['machine']].append(record['entry'])
        restored = {}
        for name in MACHINES:
            machine = RESTORE[name](journals[name])
            if machine.export_journal() != journals[name]:
                raise ReadinessError('RECOVERY_DIVERGENCE')
            restored[name] = machine
        self.machines = restored

    def _observe(self, machine_name, decision, **fields):
        self.last_observation = boundary_observation(
            machine_name,
            decision,
            schemaVersion=SCHEMA_VERSION,
            **fields,
        )

    def _guard_unchanged(self, machine, before, digest_before):
        try:
            changed = machine.export_journal() != before or machine.state_digest() != digest_before
        except Exception:
            self.failed = True
            return
        if changed:
            self.failed = True
