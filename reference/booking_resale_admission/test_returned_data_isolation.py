"""Offline returned-data probes: contract replay (A), copy characterization (B).

Builder-authored and source-informed; synthetic fixtures, no external sources.
Copy ownership is not specified by the contracts. No capability grade changes.
"""

from copy import deepcopy
import unittest

from admission_fsm import AdmissionMachine
from mock_gates import ADMISSION_WINDOW_MS
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine
from test_resale_fsm import show_kwargs, PAY, SALE_PAY, PRICE, T0, EXPIRES
from test_reservation_fsm import REQ


def _mutated(test, target, edit):
    before = deepcopy(target)
    edit(target)
    test.assertNotEqual(target, before)


def _corrupt(test, target):
    """Edit actual nested values before deleting keys and changing list shapes."""
    if isinstance(target, dict):
        for key, value in list(target.items()):
            if isinstance(value, (dict, list)):
                _corrupt(test, value)
            else:
                _mutated(test, target, lambda row, key=key: row.__setitem__(
                    key, "caller-corruption-again" if row[key] == "caller-corruption" else "caller-corruption"))
        if target:
            _mutated(test, target, lambda row: row.pop(next(iter(row))))
    elif isinstance(target, list):
        for value in target:
            if isinstance(value, (dict, list)):
                _corrupt(test, value)
        if target:
            _mutated(test, target, list.clear)
        _mutated(test, target, lambda row: row.append("caller-corruption"))


def _command(method, subject, key, **body):
    return method, subject, dict(idempotency_key=key, **body)


def _call(machine, command):
    method, subject, body = deepcopy(command)
    return getattr(machine, method)(subject, **body)


def _adopt_body(**changes):
    body = dict(show_kwargs(), show_id="show-1", slot=0, buyer_role="buyer-1",
                expires_ms=EXPIRES, order_id="order-1", amount=PRICE,
                payment_ref=PAY, reservation_id=None, quote_ref=None)
    body.update(changes)
    return body


def _script(cls):
    commands = [_command("set_clock", "clock", "clock-1", now_ms=T0)]
    if cls is ReservationMachine:
        commands += [
            _command("register_show", "show-1", "show-1", **show_kwargs()),
            _command("hold", "reserve-1", "hold-1", show_id="show-1", slot=0,
                     buyer_role="buyer-1", expires_ms=EXPIRES),
            _command("confirm", "order-1", "confirm-1", reservation_id="reserve-1",
                     amount=PRICE, quote_ref="quote-1"),
            _command("observe_payment", "order-1", "pay-1", payment_ref=PAY, amount=PRICE),
            _command("issue", "issue-1", "issue-1", order_id="order-1"),
        ]
    else:
        commands.append(_command("adopt_issued", "issue-1", "adopt-1", **_adopt_body()))
    if cls is ResaleMachine:
        commands += [
            _command("list_resale", "list-1", "list-1", right_id="issue-1", version=1,
                     seller_role="buyer-1", recipient_role="buyer-2", amount=PRICE,
                     expires_ms=EXPIRES, reservation_id=None),
            _command("hold_buy", "hold-1", "hold-1", listing_id="list-1", buyer_role="buyer-2"),
            _command("release_hold", "hold-1", "release-1", buyer_role="buyer-2"),
            _command("observe_resale_payment", "list-1", "sale-pay", payment_ref=SALE_PAY,
                     amount=PRICE, buyer_role=None),
            _command("accept_resale", "transfer-1", "transfer-1", listing_id="list-1"),
            _command("close", "list-1", "close-1"),
            _command("list_resale", "list-2", "list-2", right_id="issue-1", version=2,
                     seller_role="buyer-2", recipient_role="buyer-1", amount=PRICE,
                     expires_ms=EXPIRES, reservation_id=None),
        ]
    else:
        external = dict(external_dependency=None) if cls is AdmissionMachine else {}
        commands += [
            _command("authorize_admission", "admit-1", "admit-1", right_id="issue-1",
                     version=1, holder_role="buyer-1", gate_role="gate-a", request=REQ,
                     expires_ms=T0 + ADMISSION_WINDOW_MS, **external),
            _command("consume", "consume-1", "consume-1", right_id="issue-1", version=1,
                     gate_role="gate-a", request=REQ, **external),
        ]
        if cls is ReservationMachine:
            commands += [
                _command("hold", "reserve-2", "hold-2", show_id="show-1", slot=1,
                         buyer_role="buyer-2", expires_ms=EXPIRES),
                _command("release", "reserve-2", "release-2"),
            ]
        else:
            commands.append(_command("adopt_issued", "issue-2", "adopt-2", **_adopt_body(
                slot=1, order_id="order-2", payment_ref=SALE_PAY)))
    commands.append(_command("set_clock", "clock", "clock-2", now_ms=T0 + 1))
    return commands


def _views(machine):
    """Use only queries valid for the current public journal prefix."""
    log = machine.export_journal()
    views = []
    if isinstance(machine, ReservationMachine):
        if any(e["op"] == "register_show" for e in log):
            views.append(machine.view_show("show-1"))
        for entry in log:
            if entry["op"] == "hold":
                views.append(machine.view(entry["subject_id"]))
    elif isinstance(machine, ResaleMachine):
        if any(e["op"] == "adopt_issued" for e in log):
            views += [machine.view_right("issue-1"), machine.view_presentation(
                "issue-1", version=1, holder_role="buyer-1")]
        for entry in log:
            if entry["op"] == "list_resale":
                views.append(machine.view(entry["subject_id"]))
    else:
        for entry in log:
            if entry["op"] == "adopt_issued":
                right = entry["subject_id"]
                views += [machine.view(right), machine.view_credential(
                    right, version=1, holder_role="buyer-1")]
    return views


def _assert_same(test, subject, control):
    test.assertEqual(_views(subject), deepcopy(_views(control)))
    test.assertEqual(subject.canonical_state(), deepcopy(control.canonical_state()))
    test.assertEqual(subject.state_digest(), control.state_digest())
    test.assertEqual(subject.export_journal(), deepcopy(control.export_journal()))


def _expected_replay(first):
    expected = deepcopy(first)
    expected["duplicate"] = True
    expected["applied"] = None
    return expected


def _pair(cls, commands):
    subject, control = cls(), cls()
    for command in commands:
        _call(subject, command)
        _call(control, command)
    return subject, control


class ReturnedResultReplayTests(unittest.TestCase):
    """Class A: BRA contract §§9.4, 10.7, 11.5 freeze first envelopes."""

    def _first_results(self, cls):
        subject, control = cls(), cls()
        history = []
        for command in _script(cls):
            with self.subTest(machine=cls.__name__, command=command[:2]):
                first = _call(subject, command)
                expected = deepcopy(_call(control, command))
                self.assertEqual(first, expected)
                history.append((deepcopy(command), expected))
                _corrupt(self, first)
                # Every accepted prefix: immediate replay and all older envelopes.
                for prior, saved in history:
                    self.assertEqual(_call(subject, prior), _expected_replay(saved))
                _assert_same(self, subject, control)
        restored = cls.restore(subject.export_journal())
        for command, saved in history:
            self.assertEqual(_call(restored, command), _expected_replay(saved))
        _assert_same(self, restored, control)
        if cls is ReservationMachine:
            issued = next(saved for command, saved in history if command[0] == "issue")
            self.assertEqual(issued["evidence"]["version"], 1)
            self.assertEqual(_call(restored, _script(cls)[5])["evidence"]["version"], 1)
            self.assertEqual(restored.view("reserve-1")["right"]["version"], 2)

    def test_reservation_first_results_survive_corruption_transitions_and_restore(self):
        self._first_results(ReservationMachine)

    def test_resale_first_results_survive_corruption_transitions_and_restore(self):
        self._first_results(ResaleMachine)

    def test_admission_first_results_survive_corruption_transitions_and_restore(self):
        self._first_results(AdmissionMachine)

    def test_mutated_duplicate_results_do_not_change_later_replays(self):
        for cls in (ReservationMachine, ResaleMachine, AdmissionMachine):
            subject, control = cls(), cls()
            history = []
            for command in _script(cls):
                first = _call(subject, command)
                self.assertEqual(first, _call(control, command))
                history.append((command, deepcopy(first)))
                duplicate = _call(subject, command)
                self.assertEqual(duplicate, _expected_replay(first))
                _corrupt(self, duplicate)
                self.assertEqual(_call(subject, command), _expected_replay(first))
                _assert_same(self, subject, control)
            for machine in (subject, cls.restore(subject.export_journal())):
                for command, first in history:
                    with self.subTest(machine=cls.__name__, command=command[:2]):
                        duplicate = _call(machine, command)
                        _corrupt(self, duplicate)
                        self.assertEqual(_call(machine, command), _expected_replay(first))
                        _assert_same(self, machine, control)


class CopyIsolationCharacterizationTests(unittest.TestCase):
    """Class B: observed copy behaviour, not additional contract semantics."""

    def test_views_are_detached(self):
        for cls in (ReservationMachine, ResaleMachine, AdmissionMachine):
            subject, control = cls(), cls()
            for command in _script(cls):
                _call(subject, command)
                _call(control, command)
                for view in _views(subject):
                    _corrupt(self, view)
                    _assert_same(self, subject, control)

    def test_nested_journal_export_bodies_are_detached(self):
        for cls in (ReservationMachine, ResaleMachine, AdmissionMachine):
            subject, control = _pair(cls, _script(cls))
            exported = subject.export_journal()
            _corrupt(self, exported)  # bodies, gate_roles, entry metadata, list shape
            _assert_same(self, subject, control)
            fresh = subject.export_journal()
            restored = cls.restore(fresh)
            _corrupt(self, fresh)  # caller still owns the input after restore returns
            _assert_same(self, restored, control)
            _assert_same(self, subject, control)

    def test_retained_snapshots_survive_later_transitions(self):
        for cls in (ReservationMachine, ResaleMachine, AdmissionMachine):
            subject, control = cls(), cls()
            retained = []
            previous = subject.canonical_state()
            for command in _script(cls):
                first = _call(subject, command)
                self.assertEqual(first, _call(control, command))
                self.assertNotEqual(subject.canonical_state(), previous)
                previous = subject.canonical_state()
                for snapshot, expected in retained:
                    self.assertEqual(snapshot, expected)
                for snapshot in [first, *_views(subject), subject.export_journal()]:
                    retained.append((snapshot, deepcopy(snapshot)))
                _assert_same(self, subject, control)
            for snapshot, expected in retained:
                self.assertEqual(snapshot, expected)
                _corrupt(self, snapshot)
                _assert_same(self, subject, control)

    def test_inputs_detached_after_call(self):
        for cls in (ReservationMachine, ResaleMachine, AdmissionMachine):
            subject, control = cls(), cls()
            commands = _script(cls)
            for command in commands[:2]:
                method, identifier, body = deepcopy(command)
                first = getattr(subject, method)(identifier, **body)
                self.assertEqual(first, _call(control, command))
                if "gate_roles" in body:
                    _corrupt(self, body["gate_roles"])
                    _assert_same(self, subject, control)
                    self.assertEqual(_call(subject, command), _expected_replay(first))
            for command in commands[2:]:
                _call(subject, command)
                _call(control, command)
            _assert_same(self, subject, control)


if __name__ == "__main__":
    unittest.main()
