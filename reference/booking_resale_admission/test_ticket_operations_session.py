"""Source-informed composition evidence; direct controls bypass both adapters."""

from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from admission_fixture import FixtureError
from admission_fsm import AdmissionError, AdmissionMachine
from booking_session import BookingInputError, BookingSession
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from presentation_source import PresentationSourceError
from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine
from resale_offer_source import ResaleOfferSourceError
from settlement_fsm import SettlementError, SettlementMachine
from test_admission_session import assert_flags
from test_resale_fsm import assert_not_final
from test_reservation_fsm import assert_not_final as assert_booking_flags
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
    machine = graph[{"settlement": 0, "booking": 1, "resale": 2, "admission": 3}[surface]]
    args = dict(request["arguments"])
    if operation == "list_resale_inputs":
        return {"surface": surface, "operation": operation,
                "receipt": machine.list_resale(**args)}
    elif operation == "list_resale":
        identity = args.pop("offer_id")
        record = json.loads(next(e["recorded_text"] for e in value["offers"]
                                 if e["offer_id"] == identity))
        del record["offer_id"]
        args.update(record)
    elif operation == "observe_recorded_payment":
        identity = args.pop("recording_id")
        args.update(json.loads(next(e["recorded_text"] for e in value["payments"]
                                    if e["recording_id"] == identity)))
        result = machine.observe_resale_payment(**args)
        return {"surface": surface, "operation": operation, "receipt": result}
    elif operation in ("authorize_admission", "consume"):
        identity = args.pop("presentation_id")
        args.update(json.loads(next(e["recorded_text"] for e in value["presentations"]
                                    if (e["operation"], e["presentation_id"]) == (operation, identity))))
    key = "view" if operation.startswith("view") else "receipt"
    return {"surface": surface, "operation": operation, key: getattr(machine, operation)(**args)}


def outcome(fn):
    try:
        return fn()
    except (AdmissionError, ResaleError, ReservationError, SettlementError) as error:
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
                patch("ticket_operations_session.AdmissionMachine", wraps=AdmissionMachine) as admission_ctor, \
                patch("ticket_operations_session.BookingSession", wraps=BookingSession) as booking_ctor:
            session = TicketOperationsSession(setup=value["setup"], offer_source=offers,
                                              presentation_source=presentations)
            for ctor in (book_ctor, ticket_ctor, resale_ctor, admission_ctor):
                self.assertEqual(ctor.call_count, 1)
        book, tickets, resale, admission = machines(session)
        booking_ctor.assert_called_once_with(tickets)
        self.assertIs(session.booking._machine, tickets)
        self.assertIs(session.settlement._machine, book)
        self.assertEqual(snapshot(machines(session)), snapshot(direct_graph(value["setup"])))
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
        self.assertIsNot(session.booking, second.booking)
        self.assertIs(second.booking._machine, machines(second)[1])
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
        for scenario in ("cancel", "admission", "transfer", "payment_listed", "payment_held",
                         "reconcile", "booking", "booking_admission", "request_inputs"):
            with self.subTest(scenario=scenario):
                path = (HERE / "fixtures" / f"ticket_operations_{scenario}_session.json"
                        if scenario == "request_inputs" else
                        HERE / "fixtures" / "ticket_operations_payment_session.json"
                        if scenario.startswith("payment_") else FIXTURE)
                value = json.loads(path.read_text())
                session, cli = load_fixture(path), load_fixture(path)
                control = direct_graph(value["setup"])
                self.assertEqual(snapshot(machines(session)), snapshot(control))
                fetches = {"resale": [], "admission": [], "payments": []}
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
                        if surface == "booking":
                            assert_booking_flags(self, result)
                        elif surface == "admission":
                            assert_flags(self, result)
                        else:
                            assert_not_final(self, result)
                    self.assertEqual(snapshot(machines(session)), snapshot(control))
                    self.assertEqual(snapshot(machines(cli)), snapshot(control))
                    if operation == "list_resale":
                        fetches[surface].append(args["offer_id"])
                    elif operation == "observe_recorded_payment":
                        fetches["payments"].append(args["recording_id"])
                    elif operation in ("authorize_admission", "consume"):
                        fetches[surface].append((operation, args["presentation_id"]))
                    for desk in (session, cli):
                        self.assertEqual(desk.resale._adapter._source.calls, tuple(fetches["resale"]))
                        if desk.resale._payment_adapter is not None:
                            self.assertIs(desk.resale._payment_adapter._machine, desk.admission._machine._ownership)
                            self.assertEqual(desk.resale._payment_adapter._source.calls, tuple(fetches["payments"]))
                        self.assertEqual(desk.admission._adapter._source.calls, tuple(fetches["admission"]))

    def test_booking_journeys_history_current_state_and_shared_keys(self):
        for scenario in ("booking", "booking_admission"):
            session = load_fixture(FIXTURE)
            graph = machines(session)
            control = direct_graph(fixture()["setup"])
            results = check_reconcile_history(
                self, requests(scenario), graph, control,
                lambda row: dispatch_request(session, row),
                lambda row: direct_call(control, row, fixture()),
                lambda row: graph[{"booking": 1, "resale": 2, "admission": 3}[row["surface"]]])
            assert_booking_journey(self, scenario, results)

    def test_existing_booking_selector_journey_on_shared_graph(self):
        from test_booking_session import requests as standalone_requests
        session = load_fixture(FIXTURE)
        control = direct_graph(fixture()["setup"])
        for original in standalone_requests("booking_boundaries"):
            row = deepcopy(original) | {"surface": "booking"}
            # Isolate the extra synthetic show/keys while preserving clock subject.
            for key in ("show_id", "reservation_id", "order_id", "idempotency_key"):
                if key in row["arguments"]:
                    row["arguments"][key] = "extra-" + row["arguments"][key]
            before = snapshot(machines(session))
            expected = outcome(lambda: direct_call(control, row, fixture()))
            self.assertEqual(outcome(lambda: dispatch_request(session, row)), expected)
            self.assertEqual(snapshot(machines(session)), snapshot(control))
            # Booking operations must not mutate settlement/resale/admission.
            after = snapshot(machines(session))
            self.assertEqual((after[0], after[2:]), (before[0], before[2:]))
            if "error" not in expected:
                assert_booking_flags(self, expected.get("receipt", expected.get("view")))
        self.assertEqual(session.resale._adapter._source.calls, ())
        self.assertEqual(session.admission._adapter._source.calls, ())

    def test_booking_publication_performs_no_fsm_or_source_call(self):
        offers, presentations = Mock(), Mock()

        def publish(machine):
            # Guard only publication: fixture adoption must perform its queries.
            with ExitStack() as guards:
                for name in dir(ReservationMachine):
                    if not name.startswith("_") and callable(getattr(machine, name)):
                        guards.enter_context(patch.object(machine, name,
                            side_effect=AssertionError("booking constructor called " + name)))
                return BookingSession(machine)

        with patch("ticket_operations_session.BookingSession", side_effect=publish):
            session = TicketOperationsSession(setup=fixture()["setup"], offer_source=offers,
                                              presentation_source=presentations)
        self.assertEqual(snapshot(machines(session)), snapshot(direct_graph(fixture()["setup"])))
        self.assertEqual((offers.mock_calls, presentations.mock_calls), ([], []))
        with self.assertRaises(BookingInputError):
            session.booking.cancel("reserve-1", idempotency_key="no-clock")

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
                patch("ticket_operations_session.AdmissionSession") as admission_publish, \
                patch("ticket_operations_session.BookingSession") as booking_publish:
            with self.assertRaises(ReservationError):
                TicketOperationsSession(setup=setup, offer_source=Mock(), presentation_source=Mock())
            booking_publish.assert_not_called()
            resale_publish.assert_not_called()
            admission_publish.assert_not_called()

    def test_reconciliation_history_and_ownership_change_refusal_without_repair(self):
        value = fixture()
        session = load_fixture(FIXTURE)
        graph = machines(session)
        control = direct_graph(value['setup'])
        rows = requests('reconcile')
        results = check_reconcile_history(
            self, rows, graph, control,
            lambda row: dispatch_request(session, row),
            lambda row: direct_call(control, row, value),
            lambda row: graph[2 if row['surface'] == 'resale' else 3])
        self.assertEqual(results[10]['receipt'], results[1]['receipt'] |
                         {'duplicate': True, 'applied': None})
        for result in results[11:13]:
            self.assertEqual(result, {'error': {'code': 'STALE_VERSION'}})
        self.assertEqual(results[13]['receipt'], results[4]['receipt'] |
                         {'duplicate': True, 'applied': None})
        self.assertEqual(results[13]['receipt']['listing']['phase'], 'LISTED')
        self.assertEqual(results[14]['view']['phase'], 'CLOSED')
        self.assertEqual(results[-1]['view']['presentation']['decision'], 'STALE_VERSION')
        self.assertFalse(results[-1]['view']['venue_credential_reissued'])
        self.assertEqual(session.resale._adapter._source.calls, ('offer-1',))
        self.assertEqual(session.admission._adapter._source.calls, (('authorize_admission', 'ticket-1'),))


def check_reconcile_history(test, rows, graph, control, wrapped_call, control_call,
                            machine_for=None):
    """Compare each explicit desk action to a separately constructed FSM graph.

    Snapshots cover business state, digests and accepted journals, intentionally
    excluding process-local receipt bookkeeping, which replay/conflicts exercise.
    """
    receipts = {}
    results = []
    for index, request in enumerate(rows):
        with test.subTest(line=index + 1, request=request):
            before = snapshot(graph)
            expected = outcome(lambda: control_call(request))
            result = outcome(lambda: wrapped_call(request))
            test.assertEqual(result, expected)
            test.assertEqual(snapshot(graph), snapshot(control))
            results.append(result)
            if request['operation'] != 'reconcile':
                continue
            test.assertEqual(snapshot(graph), before)
            if 'error' in result:
                continue
            receipt = result.get('receipt', result)
            test.assertTrue(receipt['matched'])
            key = (request.get('surface'), request['arguments']['idempotency_key'])
            if key in receipts:
                test.assertEqual(receipt, receipts[key] | {'duplicate': True, 'applied': None})
            else:
                machine = graph[-1] if machine_for is None else machine_for(request)
                test.assertFalse(receipt['duplicate'])
                test.assertEqual(receipt['applied'], 'reconcile')
                test.assertEqual(receipt['state_digest'], machine.state_digest())
                test.assertEqual(receipt['entry_count'], len(machine.export_journal()))
                receipts[key] = deepcopy(receipt)
            if 'credential' in receipt:
                assert_flags(test, receipt)
            elif "reservation" in receipt:
                from test_reservation_fsm import assert_not_final as assert_booking_flags
                assert_booking_flags(test, receipt)
            else:
                assert_not_final(test, receipt)
    return results


def assert_booking_journey(test, scenario, results):
    """Explicit product-boundary assertions in addition to direct-FSM parity."""
    if scenario == "booking":
        test.assertEqual([r["error"]["code"] for r in results if "error" in r],
                         ["SLOT_OCCUPIED", "SLOT_OCCUPIED", "IDEMPOTENCY_CONFLICT",
                          "IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT",
                          "UNKNOWN_RESERVATION", "UNKNOWN_RESERVATION", "IDEMPOTENCY_CONFLICT"])
        test.assertEqual(results[2]["receipt"]["duplicate"], True)  # fixture clock replay
        test.assertEqual(results[6]["receipt"]["reservation"]["phase"], "HELD")
        test.assertEqual(results[7]["receipt"]["reservation"]["phase"], "CONFIRMED")
        test.assertEqual(results[10]["receipt"], results[7]["receipt"] |
                         {"duplicate": True, "applied": None})
        current = results[11]["view"]
        test.assertEqual(current["phase"], "CANCELLED")
        for name in ("payment_ref", "issuance_id", "settlement_id", "right"):
            test.assertIsNone(current[name])
        test.assertEqual(results[13]["receipt"], results[8]["receipt"] |
                         {"duplicate": True, "applied": None})
        test.assertEqual(results[13]["receipt"]["reservation"]["phase"], "CONFIRMED")
        test.assertEqual(results[14]["receipt"]["reservation"]["phase"], "CANCELLED")
        test.assertEqual([slot["state"] for slot in results[12]["view"]["show"]["slots"]],
                         ["ISSUED", "FREE"])
    else:
        views = [results[i]["view"] for i in (0, 3, 7)]
        test.assertEqual([v["phase"] for v in views],
                         ["ISSUED", "ADMISSION_AUTHORIZED", "CONSUMED"])
        test.assertEqual([v["right"]["version"] for v in views], [1, 1, 2])
        test.assertEqual([slot["state"] for slot in results[8]["view"]["show"]["slots"]],
                         ["ISSUED", "FREE"])
        for index in (4, 9):
            test.assertEqual(results[index]["receipt"], results[1]["receipt"] |
                             {"duplicate": True, "applied": None})
        test.assertEqual(results[5]["receipt"]["reservation"]["phase"], "ADMISSION_AUTHORIZED")
        test.assertEqual(results[10]["receipt"]["reservation"]["phase"], "CONSUMED")
        test.assertEqual([r["error"]["code"] for r in results if "error" in r],
                         ["IDEMPOTENCY_CONFLICT", "IDEMPOTENCY_CONFLICT"])
