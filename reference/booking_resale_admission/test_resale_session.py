"""Source-informed session boundary evidence over actual configured local FSMs."""

import json
from pathlib import Path
import unittest
from unittest.mock import Mock, call

from fake_resale_offer_source import FakeResaleOfferSource, SyntheticResaleOfferFault
from fake_resale_payment_source import FakeResalePaymentSource, SyntheticResalePaymentFault
from mock_gates import OFFER_WINDOW_MS
from resale_fixture import load_fixture
from resale_fsm import ResaleError, ResaleMachine
from resale_offer_source import ResaleOfferSourceError
from resale_payment_source import ResalePaymentSourceError
from resale_session import ResaleSession
from test_resale_fsm import assert_not_final

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "resale_session.json"
REQUESTS = HERE / "fixtures" / "resale_requests.jsonl"


def requests():
    return [json.loads(line) for line in REQUESTS.read_text().splitlines()]


def invoke(session, request):
    return getattr(session, request["operation"])(**request["arguments"])


def snapshot(*machines):
    return tuple((m.canonical_state(), m.state_digest(), m.export_journal()) for m in machines)


# Explicit examples for every direct forwarding method, including operations not
# needed by the happy transcript. Selectors/arguments are public session inputs.
_ADOPTION = json.loads((HERE / "fixtures/ticket_operations_fulfillment.jsonl").read_text().splitlines()[3])["arguments"]
FORWARD = (
    ("adopt_issued", "right_id", _ADOPTION),
    ("reconcile", "listing_id", dict(listing_id="l", idempotency_key="k")),
    ("hold_buy", "hold_id", dict(hold_id="h", listing_id="l", buyer_role="buyer", idempotency_key="k")),
    ("release_hold", "hold_id", dict(hold_id="h", buyer_role="buyer", idempotency_key="k")),
    ("cancel_listing", "listing_id", dict(listing_id="l", seller_role="seller", idempotency_key="k")),
    ("observe_resale_payment", "listing_id", dict(listing_id="l", payment_ref="ab" * 32,
                                                amount=8000, buyer_role="buyer", idempotency_key="k")),
    ("bind_settlement", "listing_id", dict(listing_id="l", settlement_id="s", idempotency_key="k")),
    ("accept_resale", "transfer_id", dict(transfer_id="t", listing_id="l", idempotency_key="k")),
    ("close", "listing_id", dict(listing_id="l", idempotency_key="k")),
    ("set_clock", "subject_id", dict(subject_id="clock", now_ms=42, idempotency_key="k")),
    ("view", "listing_id", dict(listing_id="l")),
    ("view_right", "right_id", dict(right_id="r")),
    ("view_presentation", "right_id", dict(right_id="r", version=2, holder_role="buyer")),
)


def request_inputs(**changes):
    return dict(listing_id="request-list-1", right_id="issue-1", version=1,
                seller_role="buyer-1", recipient_role="buyer-2", amount=8000,
                expires_ms=1120000, idempotency_key="request-list-key",
                reservation_id=None) | changes


class ResaleRequestInputsTests(unittest.TestCase):
    def configured(self):
        return load_fixture(HERE / "fixtures/resale_request_inputs_session.json")

    def test_exactly_one_call_opaque_inputs_receipt_and_exception_identity(self):
        for binding in (None, object()):
            arguments = {key: object() for key in request_inputs()}
            arguments["reservation_id"] = binding
            machine, offers, payments = Mock(spec=ResaleMachine), Mock(), Mock()
            session = ResaleSession(machine, offers, payment_source=payments)
            receipt = {"opaque": object()}
            machine.list_resale.return_value = receipt
            for error in (None, ResaleError("FIXTURE_ERROR"), RuntimeError("programming fault")):
                machine.reset_mock()
                machine.list_resale.side_effect = error
                if error is None:
                    self.assertIs(session.list_resale_inputs(**arguments), receipt)
                else:
                    with self.assertRaises(type(error)) as caught:
                        session.list_resale_inputs(**arguments)
                    self.assertIs(caught.exception, error)
                forwarded = dict(arguments)
                subject = forwarded.pop("listing_id")
                self.assertEqual(machine.mock_calls, [call.list_resale(subject, **forwarded)])
                self.assertEqual((offers.mock_calls, payments.mock_calls), ([], []))
            del arguments["reservation_id"]
            machine.reset_mock()
            with self.assertRaises(TypeError):
                session.list_resale_inputs(**arguments)
            self.assertEqual(machine.mock_calls, [])

    def compare(self, session, control, arguments):
        from test_ticket_operations_session import outcome
        result = outcome(lambda: session.list_resale_inputs(**arguments))
        self.assertEqual(result, outcome(lambda: control._machine.list_resale(**arguments)))
        self.assertEqual(snapshot(session._machine._settlement, session._machine._tickets, session._machine),
                         snapshot(control._machine._settlement, control._machine._tickets, control._machine))
        self.assertEqual(session._adapter._source.calls, ())
        self.assertEqual(control._adapter._source.calls, ())
        if "error" not in result:
            assert_not_final(self, result)
        return result

    def test_request_refusals_retained_keys_and_direct_fsm_parity(self):
        for binding in (None, "reserve-1"):
            for code, change in (
                ("STALE_VERSION", {"version": 2}),
                ("NOT_HOLDER", {"seller_role": "other"}),
                ("RESALE_CAP", {"amount": 20001}),
                ("LISTING_WINDOW", {"expires_ms": 1000000}),
                ("LISTING_WINDOW", {"expires_ms": 1000000 + OFFER_WINDOW_MS + 1}),
                ("UNKNOWN_RESERVATION", {"reservation_id": "missing"}),
            ):
                with self.subTest(binding=binding, code=code, change=change):
                    session, control = self.configured(), self.configured()
                    before = snapshot(session._machine, session._machine._tickets, session._machine._settlement)
                    arguments = request_inputs(reservation_id=binding) | change
                    for _ in range(2):
                        self.assertEqual(self.compare(session, control, arguments), {"error": {"code": code}})
                    # Canonical economic state excludes retained first-result bookkeeping.
                    self.assertEqual(snapshot(session._machine, session._machine._tickets,
                                              session._machine._settlement), before)
                    self.assertEqual(self.compare(session, control, request_inputs(reservation_id=binding)),
                                     {"error": {"code": "IDEMPOTENCY_CONFLICT"}})
                    self.assertEqual(self.compare(session, control, request_inputs(
                        reservation_id=binding, idempotency_key="fresh"))["listing"]["phase"], "LISTED")

    def test_replay_after_cancel_and_expiry_and_competing_sale_lock(self):
        for binding in (None, "reserve-1"):
            session, control = self.configured(), self.configured()
            arguments = request_inputs(reservation_id=binding)
            others = snapshot(session._machine._tickets, session._machine._settlement)
            first = self.compare(session, control, arguments)
            duplicate = first | {"duplicate": True, "applied": None}
            self.assertEqual(first["listing"]["phase"], "LISTED")
            self.assertIsNone(first["listing"]["hold_id"])
            self.assertIsNone(first["listing"]["payment_ref"])
            self.assertIsNone(first["listing"]["settlement_id"])
            self.assertEqual(self.compare(session, control, arguments), duplicate)
            for field in arguments:
                if field == "idempotency_key":
                    continue
                changed = arguments | {field: "changed"}
                self.assertEqual(self.compare(session, control, changed),
                                 {"error": {"code": "IDEMPOTENCY_CONFLICT"}})
            competing = arguments | {"listing_id": "competitor", "idempotency_key": "compete"}
            self.assertEqual(self.compare(session, control, competing),
                             {"error": {"code": "RIGHT_SALE_LOCKED"}})
            for desk in (session, control):
                desk.cancel_listing(arguments["listing_id"], seller_role="buyer-1", idempotency_key="cancel")
                desk.set_clock("clock", now_ms=1120000, idempotency_key="later")
            self.assertEqual(self.compare(session, control, arguments), duplicate)
            self.assertEqual(session.view(arguments["listing_id"])["phase"], "CANCELLED")
            self.assertEqual(self.compare(session, control, competing),
                             {"error": {"code": "RIGHT_SALE_LOCKED"}})
            self.assertEqual(self.compare(session, control, competing | {"idempotency_key": "fresh"}),
                             {"error": {"code": "LISTING_WINDOW"}})
            self.assertEqual(snapshot(session._machine._tickets, session._machine._settlement), others)
            self.assertEqual(sum(e["op"] == "list_resale" for e in session._machine.export_journal()), 1)

    def test_admission_lock_refusal_retained_after_lock_expiry(self):
        from mock_gates import ADMISSION_WINDOW_MS
        session, control = self.configured(), self.configured()
        for desk in (session, control):
            desk._machine._tickets.authorize_admission(
                "entry", idempotency_key="entry", right_id="issue-1", version=1,
                holder_role="buyer-1", gate_role="gate-a", request="11" * 32,
                expires_ms=1000000 + ADMISSION_WINDOW_MS)
        self.assertEqual(self.compare(session, control, request_inputs()),
                         {"error": {"code": "ADMISSION_LOCKED"}})
        for desk in (session, control):
            desk._machine._tickets.set_clock("clock", idempotency_key="later",
                                            now_ms=1000000 + ADMISSION_WINDOW_MS)
        self.assertEqual(self.compare(session, control, request_inputs()),
                         {"error": {"code": "ADMISSION_LOCKED"}})
        self.assertEqual(self.compare(session, control, request_inputs(idempotency_key="fresh"))[
            "listing"]["phase"], "LISTED")

    def test_recorded_and_request_paths_share_existing_fsm_replay_identity(self):
        for recorded_first in (True, False):
            session = load_fixture(FIXTURE)
            arguments = request_inputs(listing_id="list-1", idempotency_key="list-key",
                                       reservation_id="reserve-1")
            recorded = lambda: session.list_resale("offer-1", listing_id="list-1", idempotency_key="list-key")
            direct = lambda: session.list_resale_inputs(**arguments)
            first, replay = (recorded, direct) if recorded_first else (direct, recorded)
            receipt = first()
            before = snapshot(session._machine, session._machine._tickets, session._machine._settlement)
            self.assertEqual(replay(), receipt | {"duplicate": True, "applied": None})
            self.assertEqual(snapshot(session._machine, session._machine._tickets, session._machine._settlement), before)
            self.assertEqual(session._adapter._source.calls, ("offer-1",))


class ResaleSessionTests(unittest.TestCase):
    def assert_code(self, code, fn):
        with self.assertRaises(ResaleError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_recorded_payment_requires_explicit_configuration_without_machine_access(self):
        machine = Mock(spec=ResaleMachine)
        offers = Mock()
        with self.assertRaises(ResalePaymentSourceError):
            ResaleSession(machine, offers).observe_recorded_payment(
                "payment-1", listing_id="list-1", idempotency_key="pay")
        self.assertEqual(machine.mock_calls, [])
        offers.fetch.assert_not_called()

    def test_recorded_payment_uses_actual_session_and_requires_separate_transfer(self):
        for held in (False, True):
            with self.subTest(held=held):
                original = load_fixture(FIXTURE)
                machine = original._machine
                rows = requests()
                payment = rows[2]["arguments"]
                body = {k: v for k, v in payment.items() if k != "idempotency_key"}
                payments = FakeResalePaymentSource(recordings={"payment-1": json.dumps(body)})
                session = ResaleSession(machine, original._adapter._source, payment_source=payments)
                invoke(session, rows[0])
                if held:
                    invoke(session, rows[1])
                others = snapshot(machine._tickets, machine._settlement)
                journal = machine.export_journal()
                receipt = session.observe_recorded_payment(
                    "payment-1", listing_id="list-1", idempotency_key=payment["idempotency_key"])
                assert_not_final(self, receipt)
                self.assertEqual(session.view("list-1")["phase"], "PAYMENT_NOTED")
                self.assertEqual(receipt["right"]["holder_role"], "buyer-1")
                self.assertEqual(receipt["right"]["version"], 1)
                self.assertEqual(receipt["listing"]["settlement_gate"], "UNBOUND")
                self.assertEqual([row["op"] for row in machine.export_journal()[len(journal):]],
                                 ["observe_resale_payment"])
                # Source selector does not enter the existing fingerprint.
                self.assertEqual(session.observe_resale_payment(**payment),
                                 receipt | {"duplicate": True, "applied": None})
                transfer = invoke(session, rows[4])
                assert_not_final(self, transfer)
                self.assertEqual(transfer["listing"]["phase"], "TRANSFERRED")
                self.assertEqual(transfer["right"]["version"], 2)
                self.assertEqual(snapshot(machine._tickets, machine._settlement), others)
                self.assertEqual(payments.calls, ("payment-1",))
                self.assertEqual(original._adapter._source.calls, ("offer-1",))

    def test_recorded_payment_faults_and_replay_failure_never_generate_followup(self):
        for fault in SyntheticResalePaymentFault:
            machine, offers = Mock(spec=ResaleMachine), Mock()
            payments = FakeResalePaymentSource(recordings={"payment-1": fault})
            with self.assertRaises(ResalePaymentSourceError):
                ResaleSession(machine, offers, payment_source=payments).observe_recorded_payment(
                    "payment-1", listing_id="list-1", idempotency_key="pay")
            self.assertEqual(payments.calls, ("payment-1",))
            self.assertEqual(machine.mock_calls, [])
            offers.fetch.assert_not_called()
        original = load_fixture(FIXTURE)
        invoke(original, requests()[0])
        body = {k: v for k, v in requests()[2]["arguments"].items() if k != "idempotency_key"}
        payments = Mock()
        payments.fetch.side_effect = [body, ResalePaymentSourceError("synthetic")]
        spy = Mock(wraps=original._machine)
        session = ResaleSession(spy, Mock(), payment_source=payments)
        session.observe_recorded_payment("payment-1", listing_id="list-1", idempotency_key="pay")
        before = snapshot(original._machine, original._machine._tickets, original._machine._settlement)
        spy.reset_mock()
        with self.assertRaises(ResalePaymentSourceError):
            session.observe_recorded_payment("payment-1", listing_id="list-1", idempotency_key="pay")
        self.assertEqual(payments.fetch.call_count, 2)
        self.assertEqual(spy.mock_calls, [])
        self.assertEqual(snapshot(original._machine, original._machine._tickets,
                                  original._machine._settlement), before)

    def test_direct_forwarding_preserves_receipt_and_exception_identity(self):
        for name, subject, arguments in FORWARD:
            with self.subTest(name=name):
                machine, source = Mock(spec=ResaleMachine), Mock()
                method = getattr(machine, name)
                receipt = {"unchanged": object()}
                method.return_value = receipt
                session = ResaleSession(machine, source)
                self.assertIs(getattr(session, name)(**arguments), receipt)
                forwarded = dict(arguments)
                positional = forwarded.pop(subject)
                self.assertEqual(machine.mock_calls, [getattr(call, name)(positional, **forwarded)])
                for error in (ResaleError("FIXTURE_ERROR"), RuntimeError("programming fault")):
                    method.side_effect = error
                    with self.assertRaises(type(error)) as caught:
                        getattr(session, name)(**arguments)
                    self.assertIs(caught.exception, error)
                source.fetch.assert_not_called()
        machine = Mock(spec=ResaleMachine)
        ResaleSession(machine, Mock()).observe_resale_payment(
            "l", payment_ref="ab" * 32, amount=8000, idempotency_key="k")
        machine.observe_resale_payment.assert_called_once_with(
            "l", payment_ref="ab" * 32, amount=8000, buyer_role=None, idempotency_key="k")

    def test_complete_explicit_flow_and_replay_after_close(self):
        session = load_fixture(FIXTURE)
        machine = session._machine
        book, tickets = machine._settlement, machine._tickets
        others = snapshot(book, tickets)
        rows = requests()
        for index, phase in enumerate(("LISTED", "BUY_HELD", "PAYMENT_NOTED", "PAYMENT_NOTED", "TRANSFERRED")):
            receipt = invoke(session, rows[index])
            self.assertEqual(session.view("list-1")["phase"], phase)
            assert_not_final(self, receipt)
            self.assertEqual(receipt["right"]["version"], 1 if index < 4 else 2)
            if index < 3:
                self.assertEqual(session.view("list-1")["settlement_gate"], "UNBOUND")
            self.assertEqual(snapshot(book, tickets), others)
        transfer = receipt
        before = snapshot(machine, tickets, book)
        self.assertEqual(invoke(session, rows[5]), transfer | {"duplicate": True, "applied": None})
        self.assertEqual(snapshot(machine, tickets, book), before)
        invoke(session, rows[6])
        before = snapshot(machine, tickets, book)
        replay = invoke(session, rows[7])
        self.assertEqual(replay, transfer | {"duplicate": True, "applied": None})
        self.assertEqual(replay["listing"]["phase"], "TRANSFERRED")
        self.assertEqual(session.view("list-1")["phase"], "CLOSED")
        self.assertEqual(session.view_right("issue-1")["right"]["version"], 2)
        self.assertEqual(sum(e["op"] == "accept_resale" for e in machine.export_journal()), 1)
        self.assertEqual(snapshot(machine, tickets, book), before)
        self.assertEqual(session._adapter._source.calls, ("offer-1",))
        # Mutating a returned historical receipt cannot corrupt the retained one.
        replay["right"]["version"] = 999
        self.assertEqual(invoke(session, rows[7]), transfer | {"duplicate": True, "applied": None})

    def test_no_implicit_payment_binding_hold_or_close_and_unbound_transfer_works(self):
        session = load_fixture(FIXTURE)
        machine = session._machine
        rows = requests()
        invoke(session, rows[0])
        self.assert_code("ILLEGAL_TRANSITION", lambda: invoke(session, rows[4]))
        self.assertIsNone(session.view("list-1")["payment_ref"])
        self.assertIsNone(session.view("list-1")["settlement_id"])
        payment = dict(rows[2]["arguments"])
        del payment["buyer_role"]
        session.observe_resale_payment(**payment)
        transfer = dict(rows[4]["arguments"], idempotency_key="fresh-unbound")
        others = snapshot(machine._settlement, machine._tickets)
        receipt = session.accept_resale(**transfer)
        self.assertEqual(receipt["listing"]["phase"], "TRANSFERRED")
        self.assertEqual(receipt["listing"]["settlement_gate"], "UNBOUND")
        self.assertFalse(receipt["listing"]["mock_settlement_commit_observed"])
        self.assertIsNone(receipt["listing"]["hold_id"])
        self.assertEqual(snapshot(machine._settlement, machine._tickets), others)
        assert_not_final(self, receipt)

    def test_competing_listing_release_cancel_and_post_payment_error(self):
        session = load_fixture(FIXTURE)
        rows = requests()
        invoke(session, rows[0])
        self.assert_code("RIGHT_SALE_LOCKED", lambda: session.list_resale(
            "offer-1", listing_id="competitor", idempotency_key="compete"))
        invoke(session, rows[1])
        session.release_hold("buy-hold", buyer_role="buyer-2", idempotency_key="release")
        self.assertEqual(session.view("list-1")["phase"], "LISTED")
        session.cancel_listing("list-1", seller_role="buyer-1", idempotency_key="cancel")
        self.assertEqual(session.view("list-1")["phase"], "CANCELLED")
        session.list_resale("offer-1", listing_id="list-2", idempotency_key="list-2")
        session.observe_resale_payment("list-2", payment_ref="cd" * 32, amount=8000, idempotency_key="pay-2")
        self.assert_code("COMPENSATION_UNDEFINED", lambda: session.cancel_listing(
            "list-2", seller_role="buyer-1", idempotency_key="cancel-2"))
        self.assertEqual(session.view("list-2")["phase"], "PAYMENT_NOTED")

    def test_stale_inputs_and_expiry_keep_existing_errors_and_independent_clock(self):
        for change, code in (({"seller_role": "wrong"}, "NOT_HOLDER"), ({"version": 2}, "STALE_VERSION")):
            with self.subTest(code=code):
                original = load_fixture(FIXTURE)
                offer = json.loads(json.loads(FIXTURE.read_text())["offers"][0]["recorded_text"])
                offer.update(change)
                session = ResaleSession(original._machine, FakeResaleOfferSource(
                    recordings={"offer-1": json.dumps(offer)}))
                self.assert_code(code, lambda: invoke(session, requests()[0]))
                self.assertEqual(session.view_right("issue-1")["right"]["version"], 1)
        session = load_fixture(FIXTURE)
        rows = requests()
        invoke(session, rows[0])
        invoke(session, rows[2])
        machine = session._machine
        others = snapshot(machine._tickets, machine._settlement)
        session.set_clock("clock", now_ms=1120000, idempotency_key="expire")
        self.assertEqual(snapshot(machine._tickets, machine._settlement), others)
        self.assertTrue(session.view("list-1")["expired"])
        self.assert_code("LISTING_NOT_OPEN", lambda: invoke(session, rows[4]))
        self.assertEqual(session.view_right("issue-1")["right"]["version"], 1)
        self.assert_code("INVALID_ID", lambda: session.set_clock("other", now_ms=1120001, idempotency_key="bad-clock"))

    def test_views_are_pure_and_detached_with_no_source_fetch(self):
        session = load_fixture(FIXTURE)
        invoke(session, requests()[0])
        machine = session._machine
        before = snapshot(machine, machine._tickets, machine._settlement)
        calls = session._adapter._source.calls
        for _ in range(2):
            listing = session.view("list-1")
            right = session.view_right("issue-1")
            presentation = session.view_presentation("issue-1", version=1, holder_role="buyer-1")
            assert_not_final(self, listing)
            assert_not_final(self, right)
            assert_not_final(self, presentation)
            listing["phase"] = "fake"
            right["right"]["version"] = 999
            presentation["presentation"]["matches_current_right"] = True
        self.assertEqual(snapshot(machine, machine._tickets, machine._settlement), before)
        self.assertEqual(session._adapter._source.calls, calls)

    def test_source_fault_has_one_fetch_and_zero_followup_even_on_replay(self):
        for fault in SyntheticResaleOfferFault:
            machine = Mock(spec=ResaleMachine)
            source = FakeResaleOfferSource(recordings={"offer-1": fault})
            with self.assertRaises(ResaleOfferSourceError):
                invoke(ResaleSession(machine, source), requests()[0])
            self.assertEqual(source.calls, ("offer-1",))
            self.assertEqual(machine.mock_calls, [])
        original = load_fixture(FIXTURE)
        real_source = original._adapter._source
        failing = Mock()
        failing.fetch.side_effect = [real_source.fetch("offer-1"), ResaleOfferSourceError("synthetic")]
        spy = Mock(wraps=original._machine)
        session = ResaleSession(spy, failing)
        invoke(session, requests()[0])
        before = snapshot(original._machine)
        spy.reset_mock()
        with self.assertRaises(ResaleOfferSourceError):
            invoke(session, requests()[0])
        self.assertEqual(failing.fetch.call_count, 2)
        self.assertEqual(spy.mock_calls, [])
        self.assertEqual(snapshot(original._machine), before)

    def test_reconciliation_matches_direct_graph_and_preserves_business_state(self):
        from test_ticket_operations_session import check_reconcile_history, direct_call, direct_graph
        value = json.loads(FIXTURE.read_text())
        session = load_fixture(FIXTURE)
        machine = session._machine
        graph = (machine._settlement, machine._tickets, machine)
        control = direct_graph(value['setup'])[:3]
        rows = [json.loads(line) for line in
                (HERE / 'fixtures' / 'resale_reconcile.jsonl').read_text().splitlines()]
        results = check_reconcile_history(
            self, rows, graph, control, lambda row: invoke(session, row),
            lambda row: direct_call(control, dict(row, surface='resale'), value)[
                'view' if row['operation'].startswith('view') else 'receipt'])
        self.assertEqual(results[7]['listing']['phase'], 'LISTED')
        self.assertEqual(results[8]['phase'], 'CLOSED')
        self.assertNotEqual(results[7]['state_digest'], machine.state_digest())
        self.assertEqual(session._adapter._source.calls, ('offer-1',))

    def test_reconcile_forwards_opaque_identity_and_key_without_source_fetch(self):
        machine, offers, payments = Mock(spec=ResaleMachine), Mock(), Mock()
        session = ResaleSession(machine, offers, payment_source=payments)
        subject, key, receipt = object(), object(), {'opaque': object()}
        machine.reconcile.return_value = receipt
        self.assertIs(session.reconcile(subject, idempotency_key=key), receipt)
        machine.reconcile.assert_called_once_with(subject, idempotency_key=key)
        self.assertEqual(len(machine.mock_calls), 1)
        for error in (ResaleError('SYNTHETIC'), RuntimeError('unexpected failure')):
            machine.reset_mock()
            machine.reconcile.side_effect = error
            with self.assertRaises(type(error)) as caught:
                session.reconcile(subject, idempotency_key=key)
            self.assertIs(caught.exception, error)
            machine.reconcile.assert_called_once_with(subject, idempotency_key=key)
            self.assertEqual(len(machine.mock_calls), 1)
        self.assertEqual((offers.mock_calls, payments.mock_calls), ([], []))
