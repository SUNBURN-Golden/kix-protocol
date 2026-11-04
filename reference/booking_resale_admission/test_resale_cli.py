"""Strict offline fixture/JSONL acceptance and executable transcript regressions."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from admission_fixture import FixtureError
from reservation_fsm import ReservationError, ReservationMachine
from resale_cli import dispatch_request, run_requests
from resale_fixture import load_fixture
from resale_fsm import ResaleError, ResaleMachine
from resale_session import ResaleSession
from settlement_fsm import SettlementMachine
from test_resale_fsm import assert_not_final
from test_resale_session import FIXTURE, FORWARD, HERE, REQUESTS, requests, snapshot


def fixture():
    return json.loads(FIXTURE.read_text())


def run(session, rows):
    out = io.StringIO()
    with redirect_stdout(out):
        status = run_requests(session, [json.dumps(row) + "\n" for row in rows])
    return status, [json.loads(line) for line in out.getvalue().splitlines()]


class ResaleFixtureTests(unittest.TestCase):
    def load(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return load_fixture(path)

    def test_fresh_actual_graph_uses_custom_caller_values_without_binding_defaults(self):
        value = fixture()
        def rename(item):
            if type(item) is dict:
                return {k: rename(v) for k, v in item.items()}
            if type(item) is list:
                return [rename(v) for v in item]
            if type(item) is str and item in ("issue-1", "buyer-1", "buyer-2", "resale-claim"):
                return "custom-" + item
            return item
        value["setup"] = rename(value["setup"])
        value["offers"][0]["recorded_text"] = json.dumps(rename(json.loads(value["offers"][0]["recorded_text"])))
        first, second = self.load(value), self.load(value)
        self.assertIsInstance(first, ResaleSession)
        self.assertIsInstance(first._machine, ResaleMachine)
        self.assertIsInstance(first._machine._tickets, ReservationMachine)
        self.assertIsInstance(first._machine._settlement, SettlementMachine)
        self.assertIs(first._machine._tickets._settlement, first._machine._settlement)
        self.assertIsNot(first._machine, second._machine)
        first.list_resale("offer-1", listing_id="custom-list", idempotency_key="custom-key")
        self.assertEqual(first.view("custom-list")["seller_role"], "custom-buyer-1")
        self.assertIsNone(second.view_right("custom-issue-1")["ticket"]["active_listing_id"])
        self.assertEqual(first._machine._tickets.view("reserve-1")["settlement_gate"], "UNBOUND")
        # No settlement setup at all is required by the synthetic fixture format.
        value["setup"] = [e for e in value["setup"] if e["machine"] != "settlement"]
        self.load(value)

    def test_all_envelope_setup_and_body_fields_required_before_construction(self):
        base = fixture()
        variants = []
        for field in base:
            value = deepcopy(base)
            del value[field]
            variants.append(value)
        for field in base["offers"][0]:
            value = deepcopy(base)
            del value["offers"][0][field]
            variants.append(value)
        for index, entry in enumerate(base["setup"]):
            for field in entry:
                value = deepcopy(base)
                del value["setup"][index][field]
                variants.append(value)
            for field in entry["body"]:
                value = deepcopy(base)
                del value["setup"][index]["body"][field]
                variants.append(value)
        for index, value in enumerate(variants):
            with self.subTest(index=index), patch("resale_fixture.SettlementMachine") as construct:
                with self.assertRaises(FixtureError):
                    self.load(value)
                construct.assert_not_called()

    def test_invalid_shapes_unknown_setup_and_offer_identities_rejected_before_construction(self):
        variants = [[], fixture() | {"extra": 1}, fixture() | {"fixture_version": True},
                    fixture() | {"fixture_version": 2}, fixture() | {"provenance": "LIVE"},
                    fixture() | {"setup": {}}, fixture() | {"setup": []},
                    fixture() | {"offers": {}}, fixture() | {"offers": [None]}]
        for extra in ({"fault": "synthetic_resale_offer_error"}, {"extra": 1}, {"recorded_text": {}},
                      {"offer_id": " bad "}):
            value = fixture()
            value["offers"][0].update(extra)
            variants.append(value)
        for fault in ("bad", {}, None):
            value = fixture()
            value["offers"] = [{"offer_id": "offer-1", "fault": fault}]
            variants.append(value)
        value = fixture()
        value["offers"].append(deepcopy(value["offers"][0]))
        variants.append(value)
        for extra in ({"machine": []}, {"machine": "admission"}, {"operation": []},
                      {"operation": "accept_resale"}, {"subject_id": None}, {"idempotency_key": True},
                      {"body": []}, {"body": {"now_ms": 1000000, "extra": 1}}):
            value = fixture()
            value["setup"][0].update(extra)
            variants.append(value)
        for index, value in enumerate(variants):
            with self.subTest(index=index), patch("resale_fixture.SettlementMachine") as construct:
                with self.assertRaises(FixtureError):
                    self.load(value)
                construct.assert_not_called()

    def test_explicit_clocks_and_matching_issuance_adoption_are_mandatory(self):
        for machine, operation in (("reservation", "set_clock"), ("resale", "set_clock"),
                                   ("reservation", "confirm"), ("reservation", "issue"),
                                   ("resale", "adopt_issued")):
            with self.subTest(machine=machine, operation=operation):
                value = fixture()
                value["setup"] = [e for e in value["setup"]
                                  if (e["machine"], e["operation"]) != (machine, operation)]
                with self.assertRaises(FixtureError):
                    self.load(value)
        for field in ("reservation_id", "order_id", "quote_ref"):
            for invalid in (None, [], "other"):
                if field == "quote_ref" and invalid == "other":
                    continue  # authoritative quote equality is checked by the FSM below
                value = fixture()
                next(e for e in value["setup"] if e["operation"] == "adopt_issued")["body"][field] = invalid
                with self.subTest(field=field, invalid=invalid), self.assertRaises(FixtureError):
                    self.load(value)

    def test_setup_domain_failure_never_publishes_partial_session(self):
        value = fixture()
        next(e for e in value["setup"] if e["operation"] == "hold")["body"]["slot"] = 100
        with patch("resale_fixture.ResaleSession") as publish:
            with self.assertRaises(ReservationError):
                self.load(value)
            publish.assert_not_called()
        value = fixture()
        next(e for e in value["setup"] if e["operation"] == "adopt_issued")["body"]["quote_ref"] = "other"
        with patch("resale_fixture.ResaleSession") as publish:
            with self.assertRaisesRegex(ResaleError, "ORDER_BINDING_CONFLICT"):
                self.load(value)
            publish.assert_not_called()

    def test_bound_uncommitted_refusal_does_not_commit_or_transfer(self):
        value = fixture()
        value["setup"] = [e for e in value["setup"]
                          if not (e["machine"] == "settlement" and e["operation"] == "commit")]
        session = self.load(value)
        machine = session._machine
        before = snapshot(machine._settlement, machine._tickets)
        status, rows = run(session, requests()[:5])
        self.assertEqual(status, 1)
        self.assertEqual(rows[-1]["error"], {"code": "SETTLEMENT_NOT_COMMITTED"})
        self.assertEqual(session.view("list-1")["phase"], "PAYMENT_NOTED")
        self.assertEqual(session.view_right("issue-1")["right"]["version"], 1)
        self.assertEqual(snapshot(machine._settlement, machine._tickets), before)
        self.assertEqual(machine._settlement.view("resale-claim")["phase"], "CAPTURED")
        # Retained first rejection remains an error; wrapper never retries with new keys.
        before = snapshot(machine)
        self.assertEqual(run(session, [requests()[4]])[1][0]["error"], rows[-1]["error"])
        self.assertEqual(snapshot(machine), before)

    def test_recordings_validated_on_fetch_and_synthetic_faults_do_no_followup(self):
        for entry, error_type in (({"recorded_text": "{"}, "InvalidResaleOfferRecord"),
                                  ({"fault": "synthetic_resale_offer_error"}, "ResaleOfferSourceError"),
                                  ({"fault": "synthetic_resale_offer_timeout"}, "ResaleOfferSourceError")):
            value = fixture()
            value["offers"] = [{"offer_id": "offer-1"} | entry]
            session = self.load(value)
            machine = session._machine
            before = snapshot(machine, machine._tickets, machine._settlement)
            status, rows = run(session, [requests()[0], requests()[9]])
            self.assertEqual(status, 1)
            self.assertEqual(rows[0]["error"]["type"], error_type)
            self.assertEqual(rows[1]["view"]["right"]["version"], 1)
            self.assertEqual(snapshot(machine, machine._tickets, machine._settlement), before)
            self.assertEqual(session._adapter._source.calls, ("offer-1",))

    def test_fixture_text_is_strict_before_any_machine_construction(self):
        for text in ('{"x":1,"x":2}', '{"setup":[{"body":{"x":1,"x":2}}]}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}', '{'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"
                path.write_text(text)
                with patch("resale_fixture.SettlementMachine") as construct:
                    with self.assertRaises(FixtureError):
                        load_fixture(path)
                    construct.assert_not_called()


class ResaleCliTests(unittest.TestCase):
    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(HERE / "resale_cli.py"), *args], input=stdin,
                              capture_output=True, text=True, cwd=HERE.parent, check=False)

    def test_transcript_file_and_stdin_success_with_historical_receipts_current_views(self):
        for selector, stdin in ((str(REQUESTS), None), ("-", REQUESTS.read_text())):
            result = self.cli("--fixture", str(FIXTURE), "--requests", selector, stdin=stdin)
            self.assertEqual((result.returncode, result.stderr), (0, ""))
            rows = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows), 12)
            transfer = rows[4]["receipt"]
            self.assertEqual(rows[5]["receipt"], transfer | {"duplicate": True, "applied": None})
            self.assertEqual(rows[7]["receipt"], transfer | {"duplicate": True, "applied": None})
            self.assertEqual(transfer["listing"]["phase"], "TRANSFERRED")
            self.assertEqual(rows[8]["view"]["phase"], "CLOSED")
            self.assertEqual(rows[9]["view"]["right"]["version"], 2)
            self.assertFalse(rows[10]["view"]["presentation"]["matches_current_right"])
            self.assertTrue(rows[11]["view"]["presentation"]["matches_current_right"])
            for row in rows:
                assert_not_final(self, row.get("receipt", row.get("view")))

    def test_every_selector_dispatches_exactly_once_and_payment_buyer_is_optional(self):
        for operation, subject, arguments in FORWARD:
            with self.subTest(operation=operation):
                machine = Mock(spec=ResaleMachine)
                expected = {"unchanged": operation}
                getattr(machine, operation).return_value = expected
                session = ResaleSession(machine, Mock())
                result = dispatch_request(session, dict(operation=operation, arguments=arguments))
                self.assertEqual(result, {"operation": operation,
                                          "view" if operation.startswith("view") else "receipt": expected})
                self.assertEqual(len(machine.mock_calls), 1)
        for buyer in ("omitted", None, "buyer-2"):
            req = deepcopy(requests()[2])
            if buyer == "omitted":
                del req["arguments"]["buyer_role"]
            else:
                req["arguments"]["buyer_role"] = buyer
            session = load_fixture(FIXTURE)
            status, rows = run(session, [requests()[0], req])
            self.assertEqual(status, 0)
            self.assertEqual(rows[-1]["receipt"]["listing"]["phase"], "PAYMENT_NOTED")

    def test_structural_failure_stops_before_dispatch_or_next_line(self):
        variants = [[], None, {}, {"operation": "view"},
                    {"operation": "view", "arguments": {}, "extra": 1},
                    {"operation": "adopt_issued", "arguments": {}},
                    {"operation": "reconcile", "arguments": {}},
                    {"operation": "consume", "arguments": {}},
                    {"operation": "resale_accept_resale", "arguments": {}},
                    {"operation": [], "arguments": {}},
                    {"operation": "view", "arguments": []}]
        examples = [(op, args) for op, _, args in FORWARD]
        examples.append(("list_resale", requests()[0]["arguments"]))
        for operation, arguments in examples:
            for field in arguments:
                if operation == "observe_resale_payment" and field == "buyer_role":
                    continue
                changed = dict(arguments)
                del changed[field]
                variants.append(dict(operation=operation, arguments=changed))
            variants.append(dict(operation=operation, arguments=arguments | {"extra": 1}))
            if operation.startswith("view"):
                variants.append(dict(operation=operation, arguments=arguments | {"idempotency_key": "k"}))
        for req in variants:
            with self.subTest(req=req):
                session = Mock()
                status, rows = run(session, [req, requests()[0]])
                self.assertEqual(status, 2)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["error"]["type"], "FixtureError")
                self.assertEqual(session.mock_calls, [])

    def test_bad_json_duplicate_keys_nonfinite_and_overflow_stop_without_followup(self):
        texts = ('{', '\n', '[]', 'true',
                 '{"operation":"view","operation":"close","arguments":{}}',
                 '{"operation":"view","arguments":{"listing_id":"x","listing_id":"y"}}')
        texts += tuple('{"operation":"view","arguments":{"listing_id":' + x + '}}'
                       for x in ('NaN', 'Infinity', '-Infinity', '1e999'))
        for text in texts:
            with self.subTest(text=text):
                session = Mock()
                out = io.StringIO()
                with redirect_stdout(out):
                    status = run_requests(session, [text, json.dumps(requests()[0])])
                self.assertEqual(status, 2)
                self.assertEqual(len(out.getvalue().splitlines()), 1)
                self.assertEqual(session.mock_calls, [])
        result = self.cli("--fixture", str(FIXTURE), "--requests", "-", stdin=text)
        self.assertEqual(result.returncode, 2)

    def test_domain_rejections_continue_only_with_explicit_lines_and_exit_one(self):
        competitor = deepcopy(requests()[0])
        competitor["arguments"].update(listing_id="competing", idempotency_key="compete")
        cancel = dict(operation="cancel_listing", arguments=dict(
            listing_id="list-1", seller_role="buyer-1", idempotency_key="cancel"))
        rows = [requests()[0], competitor, requests()[2], cancel, requests()[8]]
        result = self.cli("--fixture", str(FIXTURE), "--requests", "-",
                          stdin="".join(json.dumps(row) + "\n" for row in rows))
        self.assertEqual((result.returncode, result.stderr), (1, ""))
        results = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([r["error"] for r in results if "error" in r],
                         [{"code": "RIGHT_SALE_LOCKED"}, {"code": "COMPENSATION_UNDEFINED"}])
        self.assertEqual(results[-1]["view"]["phase"], "PAYMENT_NOTED")
        session = load_fixture(FIXTURE)
        bad_scalar = dict(operation="set_clock", arguments=dict(
            subject_id="clock", idempotency_key="bad", now_ms=True))
        self.assertEqual(run(session, [bad_scalar])[1][0]["error"], {"code": "CLOCK"})
        absent = deepcopy(requests()[0])
        absent["arguments"]["offer_id"] = "absent"
        status, results = run(session, [absent, requests()[0]])
        self.assertEqual(status, 1)
        self.assertEqual(results[0]["error"]["type"], "ResaleOfferNotFound")
        self.assertEqual(results[1]["receipt"]["listing"]["phase"], "LISTED")
        self.assertEqual(session._adapter._source.calls, ("absent", "offer-1"))

    def test_views_via_cli_do_not_mutate_any_machine_or_fetch(self):
        session = load_fixture(FIXTURE)
        run(session, requests()[:7])
        machine = session._machine
        before = snapshot(machine, machine._tickets, machine._settlement)
        calls = session._adapter._source.calls
        self.assertEqual(run(session, requests()[8:])[0], 0)
        self.assertEqual(snapshot(machine, machine._tickets, machine._settlement), before)
        self.assertEqual(session._adapter._source.calls, calls)

    def test_bad_paths_setup_and_usage_exit_two(self):
        for args in (("--fixture", str(FIXTURE), "--requests", str(HERE / "absent")),
                     ("--fixture", str(HERE / "absent"), "--requests", "-"), ()):
            self.assertEqual(self.cli(*args, stdin="").returncode, 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{}')
            result = self.cli("--fixture", str(path), "--requests", "-", stdin="")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["error"]["type"], "FixtureError")
            value = fixture()
            next(e for e in value["setup"] if e["operation"] == "hold")["body"]["slot"] = 100
            path.write_text(json.dumps(value))
            result = self.cli("--fixture", str(path), "--requests", "-", stdin="")
            self.assertEqual(result.returncode, 2)
            self.assertIn("code", json.loads(result.stdout)["error"])

    def test_importable_without_cli_side_effects_and_unexpected_failures_surface(self):
        env = dict(os.environ, PYTHONPATH=str(HERE) + os.pathsep + os.environ.get("PYTHONPATH", ""), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", "import resale_session, resale_fixture, resale_cli"],
                                env=env, cwd=tempfile.gettempdir(), capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        machine = Mock(spec=ResaleMachine)
        machine.view.side_effect = RuntimeError("programming fault")
        with self.assertRaisesRegex(RuntimeError, "programming fault"):
            run(ResaleSession(machine, Mock()), [requests()[8]])


    def test_reconcile_file_stdin_and_direct_fsm_parity(self):
        from test_booking_cli import check_reconcile_cli
        check_reconcile_cli(self, 'resale')


class RequestInputsDeskChecks:
    """Same strict request boundary exercised through both executable desks."""

    def configured(self):
        return self.loader(HERE / "fixtures" / f"{self.prefix}_request_inputs_session.json")

    def desk(self, session):
        return session.resale if self.shared else session

    def graph(self, session):
        desk = self.desk(session)
        machine = desk._machine
        return (machine._settlement, machine._tickets, machine) + (
            (session.admission._machine,) if self.shared else ())

    def request(self, **changes):
        from test_resale_session import request_inputs
        row = dict(operation="list_resale_inputs", arguments=request_inputs(**changes))
        return row | ({"surface": "resale"} if self.shared else {})

    def compare_rows(self, rows):
        from test_ticket_operations_session import direct_call, direct_graph, outcome
        session = self.configured()
        value = json.loads((HERE / "fixtures" / f"{self.prefix}_request_inputs_session.json").read_text())
        self.assertEqual(value["offers"], [])
        control = direct_graph(value["setup"])
        results = []
        for request in rows:
            shared = request if self.shared else request | {"surface": "resale"}
            expected = outcome(lambda: direct_call(control, shared, value))
            code, actual = self.run_rows(session, [request])
            if "error" in expected:
                self.assertEqual((code, actual[0]["error"]), (1, expected["error"]))
            else:
                if not self.shared:
                    del expected["surface"]
                self.assertEqual((code, actual), (0, [expected]))
                assert_not_final(self, actual[0].get("receipt", actual[0].get("view")))
            results += actual
            self.assertEqual(snapshot(*self.graph(session)), snapshot(*(control if self.shared else control[:3])))
            self.assertEqual(self.desk(session)._adapter._source.calls, ())
        return session, results

    def test_request_inputs_empty_offers_file_stdin_and_direct_fsm_parity(self):
        path = HERE / "fixtures" / f"{self.prefix}_request_inputs.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        session, expected = self.compare_rows(rows)
        first = expected[0]["receipt"]
        self.assertEqual(first["listing"]["phase"], "LISTED")
        self.assertIsNone(first["listing"]["hold_id"])
        self.assertIsNone(first["listing"]["payment_ref"])
        self.assertIsNone(first["listing"]["settlement_id"])
        self.assertEqual(expected[1]["receipt"], first | {"duplicate": True, "applied": None})
        self.assertEqual(expected[5]["receipt"], expected[1]["receipt"])
        self.assertEqual(expected[2]["receipt"]["listing"]["phase"], "BUY_HELD")
        self.assertEqual(expected[3]["receipt"]["listing"]["phase"], "LISTED")
        self.assertEqual(expected[4]["receipt"]["listing"]["phase"], "CANCELLED")
        self.assertEqual(expected[6]["view"]["phase"], "CANCELLED")
        self.assertEqual(self.desk(session).view_right("issue-1")["right"]["version"], 1)
        outputs = []
        for selector, stdin in ((str(path), None), ("-", path.read_text())):
            process = subprocess.run([
                sys.executable, str(HERE / f"{self.prefix}_cli.py"),
                "--fixture", str(HERE / "fixtures" / f"{self.prefix}_request_inputs_session.json"),
                "--requests", selector], input=stdin, capture_output=True, text=True, check=False)
            self.assertEqual((process.returncode, process.stderr), (0, ""))
            self.assertEqual([json.loads(line) for line in process.stdout.splitlines()], expected)
            outputs.append(process.stdout)
        self.assertEqual(outputs[0], outputs[1])

    def test_request_inputs_strict_fields_stop_before_any_dispatch(self):
        valid = self.request()
        arguments = valid["arguments"]
        bad = [valid | {"arguments": {k: v for k, v in arguments.items() if k != field}}
               for field in arguments]
        bad += [valid | {"arguments": arguments | {field: "unexpected"}}
                for field in ("extra", "offer_id")]
        bad += [valid | {"arguments": shape} for shape in (None, [], "text", 1)]
        bad += [None, [], "text", valid | {"extra": True}]
        bad += [{k: v for k, v in valid.items() if k != field} for field in valid]
        for request in bad:
            with self.subTest(request=request):
                session = self.configured()
                before = snapshot(*self.graph(session))
                desk = self.desk(session)
                with patch.object(desk._machine, "list_resale", wraps=desk._machine.list_resale) as method:
                    code, results = self.run_rows(session, [request, valid])
                    self.assertEqual((code, len(results)), (2, 1))
                    self.assertEqual(results[0]["error"]["type"], "FixtureError")
                    method.assert_not_called()
                self.assertEqual(snapshot(*self.graph(session)), before)
                self.assertEqual(desk._adapter._source.calls, ())

    def test_request_inputs_domain_errors_continue_only_explicit_lines(self):
        from test_resale_session import request_inputs
        for binding in (None, "reserve-1"):
            for code, change in (("STALE_VERSION", {"version": 2}),
                                 ("NOT_HOLDER", {"seller_role": "other"}),
                                 ("RESALE_CAP", {"amount": 20001}),
                                 ("LISTING_WINDOW", {"expires_ms": 1000000})):
                with self.subTest(binding=binding, code=code):
                    refusal = self.request(**(request_inputs(reservation_id=binding) | change))
                    valid = self.request(reservation_id=binding)
                    fresh = self.request(reservation_id=binding, idempotency_key="fresh")
                    competing = self.request(listing_id="compete", idempotency_key="compete")
                    rows = [refusal, refusal, valid, fresh, fresh, competing]
                    _, expected = self.compare_rows(rows)
                    self.assertEqual([r["error"]["code"] for r in expected if "error" in r],
                                     [code, code, "IDEMPOTENCY_CONFLICT", "RIGHT_SALE_LOCKED"])
                    session = self.configured()
                    status, actual = self.run_rows(session, rows)
                    self.assertEqual((status, actual), (1, expected))
                    # Also check executable exit convention and continued output.
                    process = subprocess.run([
                        sys.executable, str(HERE / f"{self.prefix}_cli.py"),
                        "--fixture", str(HERE / "fixtures" / f"{self.prefix}_request_inputs_session.json"),
                        "--requests", "-"], input="".join(json.dumps(r) + "\n" for r in rows),
                        capture_output=True, text=True, check=False)
                    self.assertEqual((process.returncode, process.stderr), (1, ""))
                    self.assertEqual([json.loads(line) for line in process.stdout.splitlines()], expected)


class ResaleRequestInputsCliTests(RequestInputsDeskChecks, unittest.TestCase):
    shared = False
    prefix = "resale"
    loader = staticmethod(load_fixture)
    run_rows = staticmethod(run)


class RecordedPaymentDeskChecks:
    """Shared acceptance checks for both local entry points, not another FSM model."""

    def configured(self, value=None):
        value = json.loads(self.payment_fixture.read_text()) if value is None else value
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(value))
            return self.loader(path)

    def payment_request(self, recording_id="payment-1", **arguments):
        request = dict(operation="observe_recorded_payment", arguments=dict(
            recording_id=recording_id, listing_id="list-1", idempotency_key="payment-key") | arguments)
        return request | ({"surface": "resale"} if self.shared else {})

    def desk(self, session):
        return session.resale if self.shared else session

    def graph(self, session):
        desk = self.desk(session)
        m = desk._machine
        return (m._settlement, m._tickets, m) + ((session.admission._machine,) if self.shared else ())

    def state(self, session):
        return snapshot(*self.graph(session))

    def scenario(self, phase):
        path = HERE / "fixtures" / f"{self.prefix}_payment_{phase}.jsonl"
        return path, [json.loads(line) for line in path.read_text().splitlines()]

    def test_payment_fixture_strict_before_graph_and_optional_compatibility(self):
        base = json.loads(self.payment_fixture.read_text())
        entry = base["payments"][0]
        bad = [None, {}, "text", [None], [{}], [entry, entry]]
        for field in entry:
            bad.append([{k: v for k, v in entry.items() if k != field}])
        bad += [[entry | update] for update in (
            {"recording_id": " bad "}, {"recording_id": None}, {"recording_id": True},
            {"recorded_text": {}}, {"extra": 1}, {"fault": "synthetic_resale_payment_error"})]
        bad += [[{"recording_id": "p", "fault": fault}] for fault in (None, {}, [], "bad")]
        for payments in bad:
            with self.subTest(payments=payments), patch(self.constructor) as construct:
                with self.assertRaises(FixtureError):
                    self.configured(base | {"payments": payments})
                construct.assert_not_called()
        session = self.configured(base | {"payments": []})
        source = self.desk(session)._payment_adapter._source
        self.assertEqual((dict(source.recordings), source.calls), ({}, ()))
        without = dict(base)
        del without["payments"]
        session = self.configured(without)
        before = self.state(session)
        code, rows = self.run_rows(session, [self.payment_request()])
        self.assertEqual(code, 1)
        self.assertEqual(rows[0]["error"]["type"], "ResalePaymentSourceError")
        self.assertEqual(self.state(session), before)
        first, second = self.configured(), self.configured()
        self.assertIsNot(self.desk(first)._payment_adapter._source,
                         self.desk(second)._payment_adapter._source)
        for a, b in zip(self.graph(first), self.graph(second)):
            self.assertIsNot(a, b)
        self.assertEqual(self.desk(first)._payment_adapter._source.calls, ())

    def test_recorded_transcripts_file_stdin_match_and_pause_before_transfer(self):
        for phase in ("listed", "held"):
            path, requests = self.scenario(phase)
            session = self.configured()
            desk = self.desk(session)
            self.assertIs(desk._payment_adapter._machine, desk._machine)
            if self.shared:
                self.assertIs(session.admission._machine._ownership, desk._payment_adapter._machine)
            payment_index = next(i for i, r in enumerate(requests)
                                 if r["operation"] == "observe_recorded_payment")
            self.assertEqual(self.run_rows(session, requests[:payment_index])[0], 0)
            others = snapshot(*(m for m in self.graph(session) if m is not desk._machine))
            journal = desk._machine.export_journal()
            self.assertEqual(desk.view("list-1")["phase"], "LISTED" if phase == "listed" else "BUY_HELD")
            code, result = self.run_rows(session, [requests[payment_index]])
            self.assertEqual(code, 0)
            receipt = result[0]["receipt"]
            self.assertEqual(receipt["listing"]["phase"], "PAYMENT_NOTED")
            self.assertEqual((receipt["right"]["holder_role"], receipt["right"]["version"]), ("buyer-1", 1))
            self.assertEqual(snapshot(*(m for m in self.graph(session) if m is not desk._machine)), others)
            self.assertEqual([e["op"] for e in desk._machine.export_journal()[len(journal):]],
                             ["observe_resale_payment"])
            code, expected = self.run_rows(self.configured(), requests)
            self.assertEqual(code, 1 if self.shared else 0)
            observations = [r["receipt"] for r in expected if r["operation"] == "observe_recorded_payment"]
            self.assertEqual(observations[1:], [observations[0] | {"duplicate": True, "applied": None}] * 2)
            self.assertEqual(next(r["receipt"] for r in expected if r["operation"] == "accept_resale")["listing"]["phase"], "TRANSFERRED")
            if self.shared:
                self.assertEqual([r["error"] for r in expected if "error" in r],
                                 [{"code": "STALE_VERSION"}] * 2)
            for row in expected:
                if "error" not in row:
                    if row.get("surface") == "admission":
                        from test_admission_session import assert_flags
                        assert_flags(self, row.get("receipt", row.get("view")))
                    else:
                        assert_not_final(self, row.get("receipt", row.get("view")))
            for selector, stdin in ((str(path), None), ("-", path.read_text())):
                process = subprocess.run([sys.executable, str(HERE / f"{self.prefix}_cli.py"),
                                          "--fixture", str(self.payment_fixture), "--requests", selector],
                                         input=stdin, capture_output=True, text=True, check=False)
                self.assertEqual((process.returncode, process.stderr), (code, ""))
                self.assertEqual([json.loads(line) for line in process.stdout.splitlines()], expected)

    def test_payment_boundary_errors_no_mutation_no_retry_and_key_remains_usable(self):
        base = json.loads(self.payment_fixture.read_text())
        good = base["payments"][0]
        body = json.loads(good["recorded_text"])
        cases = [([], "ResalePaymentNotFound"),
                 ([good | {"recorded_text": "{"}], "InvalidResalePaymentRecord"),
                 ([good | {"recorded_text": json.dumps(body | {"listing_id": "other"})}], "InvalidResalePaymentRecord")]
        for fault in ("synthetic_resale_payment_error", "synthetic_resale_payment_timeout"):
            cases.append(([{"recording_id": "payment-1", "fault": fault}], "ResalePaymentSourceError"))
        for payments, kind in cases:
            with self.subTest(kind=kind, payments=payments):
                value = base | {"payments": payments + [good | {"recording_id": "good"}]}
                session = self.configured(value)
                self.run_rows(session, self.scenario("listed")[1][:1])
                before = self.state(session)
                desk = self.desk(session)
                with patch.object(desk._machine, "observe_resale_payment",
                                  wraps=desk._machine.observe_resale_payment) as observe:
                    code, rows = self.run_rows(session, [self.payment_request()])
                    self.assertEqual(code, 1)
                    self.assertEqual(rows[0]["error"]["type"], kind)
                    self.assertIsInstance(rows[0]["error"]["message"], str)
                    observe.assert_not_called()
                self.assertEqual(self.state(session), before)
                self.assertEqual(desk._payment_adapter._source.calls, ("payment-1",))
                self.assertEqual(self.run_rows(session, [self.payment_request("good")])[0], 0)
                self.assertEqual(desk._payment_adapter._source.calls, ("payment-1", "good"))
                # The executable loop also emits local errors and continues only
                # for the next explicit line. Child inherits the socket guard.
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "fixture.json"
                    path.write_text(json.dumps(value))
                    rows = self.scenario("listed")[1][:1] + [self.payment_request(), self.payment_request("good")]
                    process = subprocess.run([sys.executable, str(HERE / f"{self.prefix}_cli.py"),
                                              "--fixture", str(path), "--requests", "-"],
                                             input="".join(json.dumps(r)+"\n" for r in rows),
                                             capture_output=True, text=True, check=False)
                    self.assertEqual((process.returncode, process.stderr), (1, ""))
                    output = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertEqual(output[1]["error"]["type"], kind)
                    self.assertEqual(output[2]["receipt"]["listing"]["phase"], "PAYMENT_NOTED")

    def test_replay_fetches_and_conflicts_preserve_first_result_without_cached_fallback(self):
        from fake_resale_payment_source import FakeResalePaymentSource, SyntheticResalePaymentFault
        session = self.configured()
        desk = self.desk(session)
        self.run_rows(session, self.scenario("listed")[1][:1])
        code, rows = self.run_rows(session, [self.payment_request()])
        first = rows[0]["receipt"]
        body = json.loads(next(iter(desk._payment_adapter._source.recordings.values())))
        source = FakeResalePaymentSource(recordings={
            "alias": json.dumps(body), "changed": json.dumps(body | {"amount": body["amount"]-1}),
            "fault": SyntheticResalePaymentFault.TIMEOUT})
        desk._payment_adapter._source = source
        before = self.state(session)
        code, rows = self.run_rows(session, [self.payment_request("fault"), self.payment_request("alias"),
                                              self.payment_request("changed")])
        self.assertEqual(code, 1)
        self.assertEqual(rows[0]["error"]["type"], "ResalePaymentSourceError")
        self.assertEqual(rows[1]["receipt"], first | {"duplicate": True, "applied": None})
        self.assertEqual(rows[2]["error"], {"code": "IDEMPOTENCY_CONFLICT"})
        self.assertEqual(source.calls, ("fault", "alias", "changed"))
        self.assertEqual(self.state(session), before)

    def test_recorded_paths_and_semantic_refusals_match_direct_fsm_after_every_request(self):
        from test_ticket_operations_session import direct_graph, direct_call, outcome
        for phase in ("listed", "held"):
            for refusal in (None, {"amount": 7999}, {"buyer_role": "other"}):
                with self.subTest(phase=phase, refusal=refusal):
                    value = json.loads(self.payment_fixture.read_text())
                    rows = self.scenario(phase)[1]
                    if refusal is not None:
                        body = json.loads(value["payments"][0]["recorded_text"])
                        value["payments"].append({"recording_id": "refusal",
                                                  "recorded_text": json.dumps(body | refusal)})
                        pay = self.payment_request("refusal")
                        index = next(i for i, r in enumerate(rows)
                                     if r["operation"] == "observe_recorded_payment")
                        rows = rows[:index] + [pay, pay, self.payment_request(),
                                              self.payment_request(idempotency_key="fresh")]
                    session = self.configured(value)
                    control = direct_graph(value["setup"])
                    calls = []
                    for request in rows:
                        wrapped = request if self.shared else request | {"surface": "resale"}
                        expected = outcome(lambda: direct_call(control, wrapped, value))
                        code, results = self.run_rows(session, [request])
                        actual = results[0]
                        if "error" in expected:
                            self.assertEqual(actual["error"], expected["error"])
                            self.assertEqual(code, 1)
                        else:
                            if not self.shared:
                                del expected["surface"]
                            self.assertEqual(actual, expected)
                            self.assertEqual(code, 0)
                        self.assertEqual(self.state(session), snapshot(*(control if self.shared else control[:3])))
                        if request["operation"] == "observe_recorded_payment":
                            calls.append(request["arguments"]["recording_id"])
                        self.assertEqual(self.desk(session)._payment_adapter._source.calls, tuple(calls))
                    if refusal is not None:
                        self.assertEqual(results[0]["receipt"]["listing"]["phase"], "PAYMENT_NOTED")
                        # A changed valid payload bound to the refused key remains
                        # a conflict; a fresh key is the separate accepted request.
                        self.assertEqual(self.run_rows(session, [self.payment_request()])[1][0]["error"],
                                         {"code": "IDEMPOTENCY_CONFLICT"})

    def test_structural_payment_request_has_zero_fetch_and_stops(self):
        valid = self.payment_request()
        bad = [valid | {"arguments": []}, valid | {"arguments": valid["arguments"] | {"buyer_role": "buyer-2"}}]
        for field in valid["arguments"]:
            bad.append(valid | {"arguments": {k:v for k,v in valid["arguments"].items() if k != field}})
        for request in bad:
            session = self.configured()
            before = self.state(session)
            code, rows = self.run_rows(session, [request, valid])
            self.assertEqual((code, len(rows)), (2, 1))
            self.assertEqual(rows[0]["error"]["type"], "FixtureError")
            self.assertEqual(self.desk(session)._payment_adapter._source.calls, ())
            self.assertEqual(self.state(session), before)


class ResaleRecordedPaymentCliTests(RecordedPaymentDeskChecks, unittest.TestCase):
    shared = False
    prefix = "resale"
    payment_fixture = HERE / "fixtures" / "resale_payment_session.json"
    constructor = "resale_fixture.SettlementMachine"
    loader = staticmethod(load_fixture)
    run_rows = staticmethod(run)
