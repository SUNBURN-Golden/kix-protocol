"""Source-informed shared-graph handoff parity, replay and executable transcripts."""

from copy import deepcopy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from issued_ticket_adapter import InvalidIssuedTicketRecord, IssuedTicketSourceError
from test_admission_session import assert_flags
from test_resale_fsm import assert_not_final as resale_flags
from test_reservation_fsm import assert_not_final as booking_flags
from test_ticket_fulfillment import FIXTURE, HERE, fixture, requests as manual_requests, run, session_from
from test_ticket_operations_session import direct_call, direct_graph, machines, outcome, snapshot
from ticket_operations_cli import dispatch_request


def rows(scenario="issued_handoff"):
    return [json.loads(line) for line in
            (HERE / "fixtures" / f"ticket_operations_{scenario}.jsonl").read_text().splitlines()]


def expected_adoption(request):
    # Independent, preexisting manual fixture values; no source extraction code.
    body = deepcopy(manual_requests()[3]["arguments"])
    if request["arguments"]["reservation_id"] == "reserve-1":
        body.update(reservation_id="reserve-1", right_id="issue-1", slot=0, buyer_role="buyer-1",
                    order_id="order-1", payment_ref="ab" * 32, quote_ref="quote-1")
    body.update(request["arguments"])
    return request | {"operation": "adopt_issued", "arguments": body}


class TicketIssuedHandoffTests(unittest.TestCase):
    def graph(self):
        self.value = fixture()
        self.session = session_from(self.value)
        self.control = direct_graph(self.value["setup"])
        self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))
        adapter = self.session._issued_ticket_adapter
        self.assertIs(adapter._source, machines(self.session)[1])
        self.assertIs(adapter._targets["resale"], self.session.resale)
        self.assertIs(adapter._targets["admission"], self.session.admission)

    def step(self, row):
        direct = expected_adoption(row) if row["operation"] == "adopt_issued_from_booking" else row
        actual = outcome(lambda: dispatch_request(self.session, row))
        expected = outcome(lambda: direct_call(self.control, direct, self.value))
        if "error" not in expected:
            expected["operation"] = row["operation"]
        self.assertEqual(actual, expected)
        self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))
        if "error" not in actual:
            {"booking": booking_flags, "resale": resale_flags, "admission": assert_flags}[
                row["surface"]](self, actual.get("receipt", actual.get("view")))
        return actual

    def test_separate_adoptions_lifecycle_replay_exact_calls_and_unrelated_state(self):
        self.graph()
        journey = rows()
        results = []
        for index, row in enumerate(journey):
            before = snapshot(machines(self.session))
            if row["operation"] == "adopt_issued_from_booking":
                selected = getattr(self.session, row["surface"])
                other = self.session.admission if row["surface"] == "resale" else self.session.resale
                with patch.object(selected, "adopt_issued", wraps=selected.adopt_issued) as adopt, \
                        patch.object(other, "adopt_issued", side_effect=AssertionError("second adoption")):
                    result = self.step(row)
                args = expected_adoption(row)["arguments"]
                right = args.pop("right_id")
                adopt.assert_called_once_with(right, **args)
                after = snapshot(machines(self.session))
                for n in set(range(4)) - ({2} if row["surface"] == "resale" else {3}):
                    self.assertEqual(before[n], after[n])
            else:
                result = self.step(row)
            results.append(result)
            if index == 2:
                self.assertEqual(self.session.booking.view("reserve-2")["phase"], "ISSUED")
                self.assertEqual(outcome(lambda: self.session.resale.view_right("issue-2")),
                                 {"error": {"code": "UNKNOWN_RIGHT"}})
            if index == 3:
                self.assertEqual(outcome(lambda: self.session.admission.view("issue-2")),
                                 {"error": {"code": "UNKNOWN_RIGHT"}})
            # Existing source adapters are used only by explicit lifecycle requests.
            self.assertEqual(self.session.resale._adapter._source.calls,
                             () if index < 5 else ("offer-2",))
        self.assertEqual([r["error"]["code"] for r in results if "error" in r],
                         ["LISTING_LOCKED", "LISTING_LOCKED"])
        for first, replay in ((2, 12), (3, 13), (4, 14)):
            self.assertEqual(results[replay]["receipt"],
                             results[first]["receipt"] | {"duplicate": True, "applied": None})
        self.assertEqual(self.session.booking.view("reserve-2")["right"]["version"], 2)
        # Replay explicitly at listing and authorization stages too.
        self.graph()
        for index, row in enumerate(journey[:12]):
            self.step(row)
            if index in (5, 9, 11):
                for adopt in journey[3:5]:
                    self.assertTrue(self.step(adopt)["receipt"]["duplicate"])

    def test_source_failures_bind_no_keys_then_recover_same_key_and_match_direct_refusals(self):
        self.graph()
        for adopt in rows()[3:5]:
            for bad in (adopt, adopt | {"arguments": adopt["arguments"] | {"reservation_id": "missing"}},
                        adopt | {"arguments": adopt["arguments"] | {"right_id": "wrong"}}):
                before = snapshot(machines(self.session))
                with patch.object(self.session.resale, "adopt_issued") as resale, \
                        patch.object(self.session.admission, "adopt_issued") as admission:
                    with self.assertRaises(IssuedTicketSourceError):
                        dispatch_request(self.session, bad)
                    resale.assert_not_called()
                    admission.assert_not_called()
                self.assertEqual(snapshot(machines(self.session)), before)
        for row in rows()[:5]:
            self.step(row)  # formerly locally refused keys succeed, including exact journals
        for adopt in rows()[3:5]:
            result = self.step(adopt | {"arguments": adopt["arguments"] | {"idempotency_key": "fresh"}})
            self.assertEqual(result, {"error": {"code": "ILLEGAL_TRANSITION"}})

    def test_fresh_consumed_adoption_is_target_refusal_and_remains_retained(self):
        self.graph()
        for row in rows()[:3]:
            self.step(row)
        for source in (machines(self.session)[1], self.control[1]):
            source.authorize_admission("entry-source", idempotency_key="source-auth", right_id="issue-2",
                                       version=1, holder_role="buyer-3", gate_role="gate-a",
                                       request="ef" * 32, expires_ms=1060000)
            source.consume("consume-source", idempotency_key="source-consume", right_id="issue-2",
                           version=1, gate_role="gate-a", request="ef" * 32)
        for adopt in rows()[3:5]:
            target = getattr(self.session, adopt["surface"])
            for _ in range(2):
                with patch.object(target, "adopt_issued", wraps=target.adopt_issued) as call:
                    result = self.step(adopt)
                call.assert_called_once()
                self.assertEqual(result, {"error": {"code": "ALREADY_CONSUMED"}})
            # A valid changed body uses the same FSM key and conflicts with retained refusal.
            source = machines(self.session)[1]
            view = source.view("reserve-2") | {"quote_ref": "changed"}
            direct = expected_adoption(adopt)
            direct["arguments"]["quote_ref"] = "changed"
            expected = outcome(lambda: direct_call(self.control, direct, self.value))
            with patch.object(source, "view", return_value=view):
                self.assertEqual(outcome(lambda: dispatch_request(self.session, adopt)), expected)
            self.assertEqual(expected, {"error": {"code": "IDEMPOTENCY_CONFLICT"}})
            self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))

    def test_changed_source_body_conflicts_and_returned_data_is_detached(self):
        self.graph()
        for row in rows()[:3]:
            self.step(row)
        for adopt in rows()[3:5]:
            first = self.step(adopt)
            saved = deepcopy(first["receipt"])
            first["receipt"].clear()
            view = self.session.booking.view("reserve-2")
            view["right"].clear()
            show = self.session.booking.view_show("show-1")
            show["show"]["gate_roles"].clear()
            self.assertEqual(self.step(adopt)["receipt"], saved | {"duplicate": True, "applied": None})
            source = machines(self.session)[1]
            changed = source.view("reserve-2") | {"quote_ref": "changed"}
            direct = expected_adoption(adopt)
            direct["arguments"]["quote_ref"] = "changed"
            expected = outcome(lambda: direct_call(self.control, direct, self.value))
            with patch.object(source, "view", return_value=changed):
                self.assertEqual(outcome(lambda: dispatch_request(self.session, adopt)), expected)
            self.assertEqual(expected, {"error": {"code": "IDEMPOTENCY_CONFLICT"}})
            self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))

    def test_replay_after_transfer_forwards_original_buyer_and_payment(self):
        self.graph()
        # Anchor adoption already happened in explicit fixture setup with these keys.
        adoptions = [dict(surface=surface, operation="adopt_issued_from_booking", arguments=dict(
            reservation_id="reserve-1", right_id="issue-1", idempotency_key=surface + "-adopt-1"))
            for surface in ("resale", "admission")]
        transfer_path = HERE / "fixtures/ticket_operations_transfer.jsonl"
        for row in [json.loads(line) for line in transfer_path.read_text().splitlines()][:5]:
            self.step(row)
        self.assertEqual(self.session.resale.view_right("issue-1")["right"]["holder_role"], "buyer-2")
        for adopt in adoptions:
            self.assertTrue(self.step(adopt)["receipt"]["duplicate"])
        self.assertEqual(self.session.booking.view("reserve-1")["buyer_role"], "buyer-1")

    def test_malformed_source_no_target_key_then_repaired_actual_graph(self):
        for surface in ("resale", "admission"):
            for method, value in (("view", {}), ("view", None), ("view_show", {"show": {}})):
                self.graph()
                for row in rows()[:3]:
                    self.step(row)
                adopt = next(row for row in rows()[3:5] if row["surface"] == surface)
                before = snapshot(machines(self.session))
                with patch.object(machines(self.session)[1], method, return_value=value), \
                        patch.object(getattr(self.session, surface), "adopt_issued") as target:
                    with self.assertRaises(InvalidIssuedTicketRecord):
                        dispatch_request(self.session, adopt)
                    target.assert_not_called()
                self.assertEqual(snapshot(machines(self.session)), before)
                self.step(adopt)

    def test_transcripts_file_and_stdin_every_row_and_exit_conventions(self):
        for scenario in ("issued_handoff", "issued_handoff_boundaries"):
            self.graph()
            expected = []
            for row in rows(scenario):
                try:
                    result = self.step(row)
                    result = result | {"surface": row["surface"], "operation": row["operation"]}
                except IssuedTicketSourceError:
                    # Source errors are local, not FSM operations; compare the CLI envelope.
                    code, output = run(self.session, [row])
                    self.assertEqual(code, 1)
                    result = output[0]
                    self.assertEqual(snapshot(machines(self.session)), snapshot(self.control))
                expected.append(result)
            path = HERE / "fixtures" / f"ticket_operations_{scenario}.jsonl"
            for selector, stdin in ((str(path), None), ("-", path.read_text())):
                result = subprocess.run([sys.executable, str(HERE / "ticket_operations_cli.py"),
                    "--fixture", str(FIXTURE), "--requests", selector], input=stdin,
                    text=True, capture_output=True, check=False)
                self.assertEqual((result.returncode, result.stderr), (1, ""))
                self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
        self.assertEqual(run(session_from(fixture()), rows()[:5])[0], 0)


if __name__ == "__main__":
    unittest.main()
