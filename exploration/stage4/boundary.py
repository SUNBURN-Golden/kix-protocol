"""FSM boundary over a candidate store. Same public calls as readiness.boundary."""

from __future__ import annotations

import threading

from readiness.machines import MACHINES, RESTORE
from readiness.store import ReadinessFault, StoreError


class ReadinessError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ReadinessClosed(ReadinessError):
    pass


class ExploreBoundary:
    """One candidate store and the same wrapped machines as FsmBoundary."""

    def __init__(self, store):
        self.failed = False
        self._lock = threading.Lock()
        self.store = store
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
                raise
            after = machine.export_journal()
            if after[:len(before)] != before:
                self.failed = True
                raise ReadinessError('JOURNAL_REWRITE')
            new_entries = after[len(before):]
            if not new_entries:
                if machine.state_digest() != digest_before:
                    self.failed = True
                    raise ReadinessError('UNJOURNALED_MUTATION')
                return result
            try:
                for index, entry in enumerate(new_entries):
                    self.store.append(
                        {'kind': 'fsm_commit', 'machine': machine_name, 'entry': entry},
                        fault=fault if index == 0 else None,
                    )
            except (ReadinessFault, StoreError):
                self.failed = True
                raise
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

    def _guard_unchanged(self, machine, before, digest_before):
        try:
            changed = machine.export_journal() != before or machine.state_digest() != digest_before
        except Exception:
            self.failed = True
            return
        if changed:
            self.failed = True
