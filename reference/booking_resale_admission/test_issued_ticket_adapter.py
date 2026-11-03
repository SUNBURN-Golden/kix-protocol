"""Source-informed extraction boundaries; targets are spies, no external I/O."""

from copy import deepcopy
import unittest
from unittest.mock import Mock

from admission_fsm import AdmissionError
from issued_ticket_adapter import (
    InvalidIssuedTicketRecord, IssuedTicketAdapter, IssuedTicketSourceError,
)
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleError


def expected_body():
    # Independent expected input, never obtained from adapter extraction.
    return dict(reservation_id="reserve-2", show_id="show-1", slot=1,
                buyer_role="original-buyer", expires_ms=1120000, order_id="order-2",
                amount=10001, quote_ref=None, payment_ref="cd" * 32,
                organizer_role="organizer", capacity=2, gate_roles=["gate-b", "gate-a"],
                primary_price=10001, resale_cap=20000, resale_allowed=False,
                organizer_bps=0, platform_bps=10000)


def records():
    body = expected_body()
    show_fields = {"organizer_role", "capacity", "gate_roles", "primary_price", "resale_cap",
                   "resale_allowed", "organizer_bps", "platform_bps"}
    view = {k: v for k, v in body.items() if k not in show_fields}
    # Current phase/holder/version/payment must never replace the original body.
    view.update(issuance_id="issue-2", phase="CONSUMED", last_amount=999,
                last_payment="ef" * 32, right=dict(right_id="issue-2", show_id="show-1",
                slot=1, holder_role="later-owner", state="CONSUMED", version=2))
    return view, {"show": {k: body[k] for k in show_fields | {"show_id"}}, "extra": True}


class IssuedTicketAdapterTests(unittest.TestCase):
    def graph(self):
        self.source = Mock(spec=ReservationMachine)
        self.view, self.show = records()
        self.source.view.return_value = self.view
        self.source.view_show.return_value = self.show
        self.resale, self.admission = Mock(), Mock()
        self.adapter = IssuedTicketAdapter(self.source, resale=self.resale, admission=self.admission)
        self.source.assert_not_called()
        self.assertEqual(self.source.mock_calls, [])
        self.assertEqual(self.resale.mock_calls + self.admission.mock_calls, [])

    def apply(self, surface="resale", **changes):
        args = dict(surface=surface, reservation_id="reserve-2", right_id="issue-2",
                    idempotency_key="handoff")
        return self.adapter.apply(**(args | changes))

    def test_exact_original_fields_one_selected_call_detached_gates_and_receipt_identity(self):
        for surface in ("resale", "admission"):
            self.graph()
            target, other = ((self.resale, self.admission) if surface == "resale"
                             else (self.admission, self.resale))
            receipt = {"opaque": object()}
            target.adopt_issued.return_value = receipt
            before = deepcopy((self.view, self.show))
            self.assertIs(self.apply(surface), receipt)
            target.adopt_issued.assert_called_once_with(
                "issue-2", idempotency_key="handoff", **expected_body())
            self.assertEqual(len(target.mock_calls), 1)
            self.assertEqual(other.mock_calls, [])
            self.source.view.assert_called_once_with("reserve-2")
            self.source.view_show.assert_called_once_with("show-1")
            self.assertEqual(len(self.source.mock_calls), 2)
            target.adopt_issued.call_args.kwargs["gate_roles"].clear()
            self.assertEqual((self.view, self.show), before)
            self.apply(surface)  # every invocation reads again, no adapter replay/cache
            self.assertEqual(self.source.view.call_count, 2)
            self.assertEqual(self.source.view_show.call_count, 2)
            self.assertEqual(target.adopt_issued.call_count, 2)
            self.assertEqual(target.adopt_issued.call_args.kwargs["gate_roles"], ["gate-b", "gate-a"])

    def test_invalid_selection_and_identifiers_precede_all_source_access(self):
        for field in ("surface", "reservation_id", "right_id", "idempotency_key"):
            for value in (None, [], {}, True, 1, "", " leading", "x" * 101):
                self.graph()
                with self.subTest(field=field, value=value), self.assertRaises(InvalidIssuedTicketRecord):
                    self.apply(**{field: value})
                self.assertEqual(self.source.mock_calls, [])
                self.assertEqual(self.resale.mock_calls + self.admission.mock_calls, [])
        for surface in ("booking", "settlement", "unknown"):
            self.graph()
            with self.assertRaises(InvalidIssuedTicketRecord):
                self.apply(surface)
            self.assertEqual(self.source.mock_calls, [])

    def test_missing_fields_and_containers_fail_before_any_target_then_explicit_repair(self):
        view, show = records()
        changes = [("view", None), ("view", []), ("view", "bad"),
                   ("show", None), ("show", []), ("show", {}), ("show", {"show": []})]
        for field in view:
            if field not in ("phase", "last_amount", "last_payment"):
                changes.append(("view", {k: v for k, v in view.items() if k != field}))
        for field in show["show"]:
            changes.append(("show", {"show": {k: v for k, v in show["show"].items() if k != field}}))
        for field in ("right_id", "show_id", "slot"):
            changes.append(("view", view | {"right": {k: v for k, v in view["right"].items() if k != field}}))
        for name, value in changes:
            with self.subTest(name=name, value=value):
                self.graph()
                method = self.source.view if name == "view" else self.source.view_show
                method.return_value = deepcopy(value)
                with self.assertRaises(InvalidIssuedTicketRecord):
                    self.apply()
                self.assertEqual(self.resale.mock_calls + self.admission.mock_calls, [])
                method.return_value = self.view if name == "view" else self.show
                self.apply()  # same caller key is forwarded only after explicit repair
                self.resale.adopt_issued.assert_called_once_with(
                    "issue-2", idempotency_key="handoff", **expected_body())

    def test_malformed_scalars_shapes_and_identity_disagreements(self):
        bad_view = dict(reservation_id=[None, "wrong"], show_id=[None, ""], slot=[True, "1", -1, 2],
                        buyer_role=[None, ""], expires_ms=[True, -1, 10**15 + 1],
                        order_id=[None, ""], amount=[True, 0, 10**12 + 1], quote_ref=[False, ""],
                        payment_ref=[None, "CD" * 32, "short"], issuance_id=[None, "wrong"],
                        right=[None, [], {}, {"right_id": "wrong", "show_id": "show-1", "slot": 1},
                               {"right_id": "issue-2", "show_id": "wrong", "slot": 1},
                               {"right_id": "issue-2", "show_id": "show-1", "slot": True},
                               {"right_id": "issue-2", "show_id": "show-1", "slot": 0}])
        bad_show = dict(show_id=[None, "wrong"], organizer_role=[False, ""], capacity=[True, 0, 17],
                        gate_roles=[None, (), [], [None], ["dup", "dup"], ["x"] * 17],
                        primary_price=[True, 0], resale_cap=[None, 10**12 + 1],
                        resale_allowed=[None, 1, "true"], organizer_bps=[True, -1, 1, 10001],
                        platform_bps=[None, -1, 10001])
        for name, variants in (("view", bad_view), ("show", bad_show)):
            for field, values in variants.items():
                for value in values:
                    with self.subTest(name=name, field=field, value=value):
                        self.graph()
                        target = self.view if name == "view" else self.show["show"]
                        target[field] = value
                        with self.assertRaises(InvalidIssuedTicketRecord):
                            self.apply()
                        self.assertEqual(self.resale.mock_calls + self.admission.mock_calls, [])

    def test_source_exceptions_wrap_once_and_target_exceptions_propagate_without_retry(self):
        for method in ("view", "view_show"):
            for error in (RuntimeError("unavailable"), IssuedTicketSourceError("source refusal")):
                self.graph()
                getattr(self.source, method).side_effect = error
                with self.assertRaises(IssuedTicketSourceError) as caught:
                    self.apply()
                if isinstance(error, IssuedTicketSourceError):
                    self.assertIs(caught.exception, error)
                else:
                    self.assertIs(caught.exception.__cause__, error)
                self.assertEqual(getattr(self.source, method).call_count, 1)
                self.assertEqual(self.resale.mock_calls + self.admission.mock_calls, [])
        for surface, error in (("resale", ResaleError("OPAQUE")),
                               ("admission", AdmissionError("OPAQUE")),
                               ("resale", RuntimeError("target bug"))):
            self.graph()
            target = self.resale if surface == "resale" else self.admission
            target.adopt_issued.side_effect = error
            with self.assertRaises(type(error)) as caught:
                self.apply(surface)
            self.assertIs(caught.exception, error)
            self.assertEqual(len(target.mock_calls), 1)


if __name__ == "__main__":
    unittest.main()
