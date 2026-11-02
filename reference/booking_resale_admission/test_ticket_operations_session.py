"""Source-informed composition evidence; direct controls bypass both adapters."""

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from admission_fixture import FixtureError
from admission_fsm import AdmissionError, AdmissionMachine
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from presentation_source import PresentationSourceError
from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine
from resale_offer_source import ResaleOfferSourceError
from settlement_fsm import SettlementMachine
from test_admission_session import assert_flags
from test_resale_fsm import assert_not_final
from ticket_operations_cli import dispatch_request
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "ticket_operations_session.json"


def fixture():
    return json.loads(FIXTURE.read_text())


def requests(scenario):
    path = HERE / "fixtures" / f"ticket_operations_{scenario}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def machines(session):
    resale, admission = session.resale._machine, session.admission._machine
    return resale._settlement, resale._tickets, resale, admission


def snapshot(graph):
    return tuple((m.canonical_state(), m.state_digest(), m.export_journal()) for m in graph)


def direct_graph(setup):
    # Deliberately construct control independently of the combined constructor.
    book = SettlementMachine()
    tickets = ReservationMachine(settlement_source=book)
    resale = ResaleMachine(ticket_source=tickets, settlement_source=book)
    admission = AdmissionMachine(ticket_source=tickets, ownership_source=resale,
                                 settlement_source=book)
    graph = dict(settlement=book, reservation=tickets, resale=resale, admission=admission)
    for entry in setup:
        getattr(graph[entry["machine"]], entry["operation"])(
            entry["subject_id"], idempotency_key=entry["idempotency_key"], **entry["body"])
    return book, tickets, resale, admission


def direct_call(graph, request, value):
    surface, operation = request["surface"], request["operation"]
    machine = graph[2 if surface == "resale" else 3]
    args = dict(request["arguments"])
    if operation == "list_resale":
        identity = args.pop("offer_id")
        record = json.loads(next(e["recorded_text"] for e in value["offers"]
                                 if e["offer_id"] == identity))
        del record["offer_id"]
        args.update(record)
    elif operation in ("authorize_admission", "consume"):
        identity = args.pop("presentation_id")
        args.update(json.loads(next(e["recorded_text"] for e in value["presentations"]
                                    if (e["operation"], e["presentation_id"]) == (operation, identity))))
    key = "view" if operation.startswith("view") else "receipt"
    return {"surface": surface, "operation": operation, key: getattr(machine, operation)(**args)}


def outcome(fn):
    try:
        return fn()
    except (AdmissionError, ResaleError, ReservationError) as error:
        return {"error": {"code": error.code}}


class TicketOperationsSessionTests(unittest.TestCase):
    def test_one_shared_graph_per_construction_and_custom_inputs(self):
        value = fixture()
        # Caller clocks can be different; admission's existing reservation
        # delegation is preserved, without changing resale's explicit clock.
        for entry in value["setup"]:
            if entry["machine"] == "resale" and entry["operation"] == "set_clock":
                entry["body"]["now_ms"] = 999999
        offers, presentations = FakeResaleOfferSource(recordings={}), FakePresentationSource(recordings={})
        with patch("ticket_operations_session.SettlementMachine", wraps=SettlementMachine) as book_ctor, \
                patch("ticket_operations_session.ReservationMachine", wraps=ReservationMachine) as ticket_ctor, \
                patch("ticket_operations_session.ResaleMachine", wraps=ResaleMachine) as resale_ctor, \
                patch("ticket_operations_session.AdmissionMachine", wraps=AdmissionMachine) as admission_ctor:
            session = TicketOperationsSession(setup=value["setup"], offer_source=offers,
                                              presentation_source=presentations)
            for ctor in (book_ctor, ticket_ctor, resale_ctor, admission_ctor):
                self.assertEqual(ctor.call_count, 1)
        book, tickets, resale, admission = machines(session)
        self.assertIs(tickets._settlement, book)
        self.assertIs(resale._tickets, tickets)
        self.assertIs(resale._settlement, book)
        self.assertIs(admission._tickets, tickets)
        self.assertIs(admission._ownership, resale)
        self.assertIs(admission._settlement, book)
        self.assertIs(session.resale._adapter._source, offers)
        self.assertIs(session.admission._adapter._source, presentations)
        self.assertEqual((offers.calls, presentations.calls), ((), ()))
        second = load_fixture(FIXTURE)
        for first, other in zip(machines(session), machines(second)):
            self.assertIsNot(first, other)
        before = snapshot(machines(second))
        session.resale.set_clock("clock", now_ms=1000001, idempotency_key="custom-clock")
        self.assertEqual(snapshot(machines(second)), before)
        self.assertEqual(json.loads(tickets.canonical_state())["logical_time_ms"], 1000000)
        before = snapshot((book, resale))
        session.admission.set_clock("clock", now_ms=1000002, idempotency_key="admission-next")
        self.assertEqual(snapshot((book, resale)), before)
        self.assertEqual(json.loads(tickets.canonical_state())["logical_time_ms"], 1000002)

    def test_transcripts_session_and_cli_match_direct_graph_after_every_request(self):
        for scenario in ("cancel", "admission", "transfer"):
            with self.subTest(scenario=scenario):
                value = fixture()
                session, cli = load_fixture(FIXTURE), load_fixture(FIXTURE)
                control = direct_graph(value["setup"])
                self.assertEqual(snapshot(machines(session)), snapshot(control))
                fetches = {"resale": [], "admission": []}
                for request in requests(scenario):
                    surface, operation, args = (request[k] for k in ("surface", "operation", "arguments"))
                    expected = outcome(lambda: direct_call(control, request, value))
                    result = outcome(lambda: getattr(getattr(session, surface), operation)(**args))
                    routed = outcome(lambda: dispatch_request(cli, request))
                    if "error" in expected:
                        self.assertEqual(result, expected)
                        self.assertEqual(routed, expected)
                    else:
                        key = "view" if operation.startswith("view") else "receipt"
                        self.assertEqual(result, expected[key])
                        self.assertEqual(routed, expected)
                        if surface == "admission":
                            assert_flags(self, result)
                        else:
                            assert_not_final(self, result)
                    self.assertEqual(snapshot(machines(session)), snapshot(control))
                    self.assertEqual(snapshot(machines(cli)), snapshot(control))
                    if operation == "list_resale":
                        fetches[surface].append(args["offer_id"])
                    elif operation in ("authorize_admission", "consume"):
                        fetches[surface].append((operation, args["presentation_id"]))
                    for desk in (session, cli):
                        self.assertEqual(desk.resale._adapter._source.calls, tuple(fetches["resale"]))
                        self.assertEqual(desk.admission._adapter._source.calls, tuple(fetches["admission"]))

    def test_replay_fetch_failure_and_key_conflicts_leave_shared_graph_unchanged(self):
        for surface, request, error_type in (
            ("resale", requests("cancel")[0], ResaleOfferSourceError),
            ("admission", requests("admission")[0], PresentationSourceError),
        ):
            with self.subTest(surface=surface):
                session = load_fixture(FIXTURE)
                nested = getattr(session, surface)
                source = nested._adapter._source
                args = request["arguments"]
                if surface == "resale":
                    record = source.fetch(args["offer_id"])
                else:
                    record = source.fetch(args["presentation_id"], operation=request["operation"])
                proxy = Mock()
                proxy.fetch.side_effect = [record, error_type("synthetic fetch failure"), record, record]
                nested._adapter._source = proxy
                first = dispatch_request(session, request)
                before = snapshot(machines(session))
                with self.assertRaises(error_type):
                    dispatch_request(session, request)
                self.assertEqual(snapshot(machines(session)), before)
                duplicate = dispatch_request(session, request)
                self.assertEqual(duplicate["receipt"], first["receipt"] | {"duplicate": True, "applied": None})
                changed = deepcopy(request)
                changed["arguments"]["listing_id" if surface == "resale" else "admission_id"] = "other"
                self.assertEqual(outcome(lambda: dispatch_request(session, changed)),
                                 {"error": {"code": "IDEMPOTENCY_CONFLICT"}})
                self.assertEqual(snapshot(machines(session)), before)
                self.assertEqual(proxy.fetch.call_count, 4)

    def test_constructor_rejects_structure_before_graph_and_domain_failure_before_publish(self):
        with patch("ticket_operations_session.SettlementMachine") as construct:
            with self.assertRaises(FixtureError):
                TicketOperationsSession(setup=[], offer_source=Mock(), presentation_source=Mock())
            construct.assert_not_called()
        setup = fixture()["setup"]
        next(e for e in setup if e["operation"] == "hold")["body"]["slot"] = 100
        with patch("ticket_operations_session.ResaleSession") as resale_publish, \
                patch("ticket_operations_session.AdmissionSession") as admission_publish:
            with self.assertRaises(ReservationError):
                TicketOperationsSession(setup=setup, offer_source=Mock(), presentation_source=Mock())
            resale_publish.assert_not_called()
            admission_publish.assert_not_called()
