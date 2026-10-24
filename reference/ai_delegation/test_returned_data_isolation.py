"""Offline AID replay (A) and source-informed copy characterization (B).

Synthetic fixtures only. Copy ownership is not defined by the contract; these
observations neither enable execution nor raise a capability grade.
"""

from copy import deepcopy
import unittest

from ai_delegation_property_support import (
    new_mock, mk_limits, mk_scope, mk_period, check_envelope, digest_of,
)


def _mutated(test, target, edit):
    before = deepcopy(target)
    edit(target)
    test.assertNotEqual(target, before)


def _corrupt(test, target):
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


def _issue():
    return "issue_grant", dict(actor="human-a", grant_id="g-1", agent_id="agent-1",
                               authority=["QUERY", "PROPOSE"],
                               scope=mk_scope(subjects=("sub-1", "sub-2")),
                               limits=mk_limits(), period=mk_period())


def _tool(tool, args):
    return "call_tool", dict(actor="agent-1", grant_id="g-1", tool=tool, args=args, now=12)


def _action(identifier, amount):
    return _tool("propose_action", dict(proposal_id=identifier, surface="surf-a",
                                        subject="sub-1", amount=amount, kind="kind-a"))


def _change():
    return _tool("propose_grant_change", dict(proposal_id="p-2", requested=dict(
        limits=mk_limits(), scope=mk_scope(subjects=("sub-1",)),
        authority=["QUERY", "PROPOSE"], period=mk_period(), note="fixture-ask")))


def _decide(identifier, decision):
    return "decide_proposal", dict(actor="human-a", proposal_id=identifier, decision=decision, now=12)


def _script():
    # Entries: command, charged (amount, count), safe to replay at every later stage.
    return [
        (_issue(), (0, 0), True),
        (_action("p-1", 5), (5, 1), True),
        (_change(), (5, 2), True),
        (_action("p-3", 7), (12, 3), True),
        (_decide("p-3", "APPROVE"), (12, 3), True),
        (_action("p-4", 3), (15, 4), True),
        (_tool("withdraw_proposal", dict(proposal_id="p-4")), (12, 3), False),
        (_action("p-5", 4), (16, 4), True),
        (_decide("p-5", "REJECT"), (12, 3), True),
        (("revoke_grant", dict(actor="human-a", grant_id="g-1", reason="stop")), (7, 1), True),
        (("revoke_grant", dict(actor="human-a", grant_id="g-1", reason="rotate")), (7, 1), False),
    ]


def _call(machine, command):
    method, args = deepcopy(command)
    return getattr(machine, method)(**args)


def _views(machine):
    state = machine.canonical_state()
    return ([machine.view_grant(row["grant_id"]) for row in state["grants"]]
            + [machine.view_proposal(row["proposal_id"]) for row in state["proposals"]])


def _assert_same(test, subject, control):
    test.assertEqual(_views(subject), deepcopy(_views(control)))
    test.assertEqual(subject.canonical_state(), deepcopy(control.canonical_state()))
    test.assertEqual(subject.state_digest(), control.state_digest())
    test.assertEqual(subject.state_digest(), digest_of(subject.canonical_state()))
    for view in _views(subject):
        check_envelope(view, "returned-data isolation")


def _expected_duplicate(control, command):
    method, args = command
    if method in ("issue_grant", "revoke_grant"):
        kind, view = "grant", control.view_grant(args["grant_id"])
    else:
        identifier = args["proposal_id"] if method == "decide_proposal" else args["args"]["proposal_id"]
        kind, view = "proposal", control.view_proposal(identifier)
    return dict(duplicate=True, **{kind: deepcopy(view)})


def _assert_charged(test, machine, expected):
    rows = [row for row in machine.canonical_state()["proposals"]
            if row["phase"] in ("PROPOSED", "HUMAN_APPROVED")]
    test.assertEqual((sum(row["amount"] or 0 for row in rows), len(rows)), expected)


def _pair():
    subject, control = new_mock(), new_mock()
    for command in (_issue(), _action("p-1", 5), _change()):
        _call(subject, command)
        _call(control, command)
    return subject, control


class ReturnedResultReplayTests(unittest.TestCase):
    """Class A: §7 / DLG-25/26 return current records, never frozen first results."""

    def test_corrupted_first_and_duplicate_results_do_not_change_duplicates(self):
        subject, control = new_mock(), new_mock()
        history = []
        for command, charged, replayable in _script():
            with self.subTest(command=command):
                first = _call(subject, command)
                self.assertEqual(first, deepcopy(_call(control, command)))
                _corrupt(self, first)
                if replayable:
                    history.append(deepcopy(command))
                # Immediately and after every later transition, compare whole envelopes.
                for prior in history:
                    expected = _expected_duplicate(control, prior)
                    duplicate = _call(subject, prior)
                    self.assertEqual(duplicate, expected)
                    _corrupt(self, duplicate)
                    self.assertEqual(_call(subject, prior), expected)
                    _assert_same(self, subject, control)
                    _assert_charged(self, subject, charged)
        self.assertEqual(subject.view_grant("g-1")["phase"], "REVOKED")
        self.assertEqual(subject.view_grant("g-1")["reason"], "stop")
        self.assertEqual(subject.view_proposal("p-1")["phase"], "VOIDED_BY_REVOCATION")
        self.assertEqual(subject.view_proposal("p-2")["phase"], "VOIDED_BY_REVOCATION")
        self.assertEqual(subject.view_proposal("p-4")["phase"], "WITHDRAWN")
        self.assertEqual(subject.view_proposal("p-5")["phase"], "HUMAN_REJECTED")


class CopyIsolationCharacterizationTests(unittest.TestCase):
    """Class B: public copies and object lifetime, beyond replay predicates."""

    def test_views_and_canonical_state_are_detached(self):
        subject, control = _pair()
        for snapshot in [*_views(subject), subject.canonical_state()]:
            # Includes scope.subjects, limits, period, memo.limits and state lists.
            _corrupt(self, snapshot)
            _assert_same(self, subject, control)

    def test_retained_snapshots_survive_later_transitions(self):
        subject, control = new_mock(), new_mock()
        retained = []
        for command, charged, _ in _script():
            before = subject.canonical_state()
            result = _call(subject, command)
            self.assertEqual(result, _call(control, command))
            if result["duplicate"]:
                self.assertEqual(subject.canonical_state(), before)
            else:
                self.assertNotEqual(subject.canonical_state(), before)
            for snapshot, expected in retained:
                self.assertEqual(snapshot, expected)
            for snapshot in [result, *_views(subject), subject.canonical_state()]:
                retained.append((snapshot, deepcopy(snapshot)))
            _assert_same(self, subject, control)
            _assert_charged(self, subject, charged)
        for snapshot, expected in retained:
            self.assertEqual(snapshot, expected)
            _corrupt(self, snapshot)
            _assert_same(self, subject, control)

    def test_inputs_detached_after_call(self):
        subject, control = new_mock(), new_mock()
        for command in (_issue(), _action("p-1", 5), _change()):
            method, args = deepcopy(command)
            first = getattr(subject, method)(**args)
            self.assertEqual(first, _call(control, command))
            if method == "issue_grant":
                for name in ("authority", "scope", "limits", "period"):
                    _corrupt(self, args[name])
                    _assert_same(self, subject, control)
            else:
                if "requested" in args["args"]:
                    _corrupt(self, args["args"]["requested"])
                    _assert_same(self, subject, control)
                _corrupt(self, args["args"])
                _assert_same(self, subject, control)
            self.assertEqual(_call(subject, command), _expected_duplicate(control, command))
            _assert_same(self, subject, control)


if __name__ == "__main__":
    unittest.main()
