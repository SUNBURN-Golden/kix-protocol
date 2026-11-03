"""Focused combined input and executable transcript evidence; no sockets."""

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

from admission_cli import _DISPATCH as ADMISSION_DISPATCH
from admission_fixture import FixtureError
from booking_cli import _DISPATCH as BOOKING_DISPATCH
from fake_presentation_source import SyntheticPresentationFault
from fake_resale_offer_source import SyntheticResaleOfferFault
from resale_cli import _DISPATCH as RESALE_DISPATCH
from test_resale_cli import RecordedPaymentDeskChecks
from ticket_operations_cli import _SETTLEMENT_DISPATCH, dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from test_ticket_operations_session import (FIXTURE, HERE, assert_booking_journey, fixture,
                                            machines, requests, snapshot)


def run(session, rows):
    output = io.StringIO()
    with redirect_stdout(output):
        code = run_requests(session, [json.dumps(row) for row in rows])
    return code, [json.loads(line) for line in output.getvalue().splitlines()]


class TicketOperationsFixtureTests(unittest.TestCase):
    def load(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return load_fixture(path)

    def assert_structural(self, value):
        with patch("ticket_operations_session.SettlementMachine") as construct:
            with self.assertRaises(FixtureError):
                self.load(value)
            construct.assert_not_called()

    def test_all_fixture_setup_and_recording_fields_are_exact(self):
        base = fixture()
        for field in base:
            with self.subTest(field=field):
                value = deepcopy(base)
                del value[field]
                self.assert_structural(value)
        for index, entry in enumerate(base["setup"]):
            for field in entry:
                value = deepcopy(base)
                del value["setup"][index][field]
                self.assert_structural(value)
            for field in entry["body"]:
                value = deepcopy(base)
                del value["setup"][index]["body"][field]
                self.assert_structural(value)
        for name in ("offers", "presentations"):
            for field in base[name][0]:
                value = deepcopy(base)
                del value[name][0][field]
                self.assert_structural(value)
            for update in ({"extra": 1}, {"fault": "bad"}, {"recorded_text": None}):
                value = deepcopy(base)
                value[name][0].update(update)
                self.assert_structural(value)
            value = deepcopy(base)
            value[name].append(deepcopy(value[name][0]))
            self.assert_structural(value)
            for entries in ({}, [None], [{"fault": None}]):
                self.assert_structural(base | {name: entries})
        for update in ({"extra": 1}, {"fixture_version": True}, {"fixture_version": 2},
                       {"provenance": "LIVE"}, {"setup": []}, {"setup": {}},):
            self.assert_structural(base | update)
        self.assert_structural([])

    def test_setup_is_allowlisted_and_requires_explicit_clocks_binding_and_adoption(self):
        base = fixture()
        for machine, operation in (("reservation", "set_clock"), ("resale", "set_clock"),
                                   ("admission", "set_clock"), ("reservation", "confirm"),
                                   ("reservation", "bind_settlement"), ("reservation", "issue"),
                                   ("resale", "adopt_issued"), ("admission", "adopt_issued")):
            value = deepcopy(base)
            value["setup"] = [e for e in value["setup"]
                              if (e["machine"], e["operation"]) != (machine, operation)]
            self.assert_structural(value)
        for update in ({"machine": []}, {"machine": "unknown"}, {"operation": []},
                       {"operation": "consume"}, {"operation": "__init__"},
                       {"body": []}, {"subject_id": None}, {"idempotency_key": True}):
            value = deepcopy(base)
            value["setup"][0].update(update)
            self.assert_structural(value)

    def test_caller_values_are_used_and_record_text_is_validated_only_when_fetched(self):
        base = fixture()
        def rename(value):
            if type(value) is dict:
                return {key: rename(item) for key, item in value.items()}
            if type(value) is list:
                return [rename(item) for item in value]
            if type(value) is str and value in ("issue-1", "buyer-1", "buyer-2", "reserve-1"):
                return "custom-" + value
            return value
        base["setup"] = rename(base["setup"])
        session = self.load(base)
        self.assertEqual(session.resale.view_right("custom-issue-1")["right"]["holder_role"], "custom-buyer-1")
        self.assertEqual(session.admission.view("custom-issue-1")["holder_role"], "custom-buyer-1")
        for surface, name, identity, fault_type in (
            ("resale", "offers", {"offer_id": "offer-1"}, SyntheticResaleOfferFault),
            ("admission", "presentations", {"operation": "authorize_admission", "presentation_id": "ticket-1"}, SyntheticPresentationFault),
        ):
            payloads = [{"recorded_text": "{"}] + [{"fault": fault.value} for fault in fault_type]
            for payload in payloads:
                value = fixture()
                value[name] = [identity | payload]
                session = self.load(value)
                before = snapshot(machines(session))
                request = requests("cancel" if surface == "resale" else "admission")[0]
                code, rows = run(session, [request])
                self.assertEqual(code, 1)
                self.assertIn("type", rows[0]["error"])
                self.assertEqual(snapshot(machines(session)), before)
                self.assertEqual(len(getattr(session, surface)._adapter._source.calls), 1)

    def test_fixture_json_rejects_duplicate_keys_nonfinite_overflow(self):
        for text in ('{"x":1,"x":2}', '{"setup":[{"body":{"x":1,"x":2}}]}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}', '{'):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"
                path.write_text(text)
                with patch("ticket_operations_session.SettlementMachine") as construct:
                    with self.assertRaises(FixtureError):
                        load_fixture(path)
                    construct.assert_not_called()


class TicketOperationsCliTests(unittest.TestCase):
    def test_source_backed_adoption_shared_only_exact_arguments(self):
        class StringSubclass(str):
            pass

        for surface in ("resale", "admission"):
            valid = dict(surface=surface, operation="adopt_issued_from_booking", arguments=dict(
                reservation_id="reserve-1", right_id="issue-1", idempotency_key="handoff"))
            session = load_fixture(FIXTURE)
            receipt = {"opaque": object()}
            with patch.object(session, "adopt_issued_from_booking", return_value=receipt) as adopt:
                self.assertIs(dispatch_request(session, valid)["receipt"], receipt)
                adopt.assert_called_once_with(surface=surface, **valid["arguments"])
            variants = [valid | {"surface": wrong} for wrong in ("booking", "settlement")]
            with self.assertRaises(FixtureError):
                dispatch_request(session, valid | {"operation": StringSubclass(valid["operation"])})
            variants += [valid | {"arguments": bad} for bad in ([], None, {},
                valid["arguments"] | {"show_id": "forbidden"},
                *[{k: v for k, v in valid["arguments"].items() if k != missing}
                  for missing in valid["arguments"]])]
            for bad in variants:
                before = snapshot(machines(session))
                with patch.object(session, "adopt_issued_from_booking") as adopt:
                    code, output = run(session, [bad, valid])
                    self.assertEqual((code, len(output)), (2, 1))
                    self.assertEqual(output[0]["error"]["type"], "FixtureError")
                    adopt.assert_not_called()
                self.assertEqual(snapshot(machines(session)), before)
            for module in ("resale_cli", "admission_cli", "booking_cli"):
                cli = __import__(module)
                with self.assertRaises(FixtureError):
                    cli.dispatch_request(Mock(), {k: v for k, v in valid.items() if k != "surface"})

    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(HERE / "ticket_operations_cli.py"), *args],
                              input=stdin, capture_output=True, text=True, cwd=HERE.parent, check=False)

    def test_three_transcripts_file_and_stdin_exact_session_results(self):
        errors = {"cancel": ["LISTING_LOCKED", "LISTING_LOCKED"],
                  "admission": ["ADMISSION_LOCKED", "ALREADY_CONSUMED"],
                  "transfer": ["STALE_VERSION", "STALE_VERSION"]}
        for scenario in errors:
            rows = requests(scenario)
            expected_code, expected = run(load_fixture(FIXTURE), rows)
            self.assertEqual(expected_code, 1)
            self.assertEqual([row["error"]["code"] for row in expected if "error" in row], errors[scenario])
            path = HERE / "fixtures" / f"ticket_operations_{scenario}.jsonl"
            for selector, stdin in ((str(path), None), ("-", path.read_text())):
                result = self.cli("--fixture", str(FIXTURE), "--requests", selector, stdin=stdin)
                self.assertEqual((result.returncode, result.stderr), (1, ""))
                self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)
            if scenario == "cancel":
                self.assertEqual(expected[2]["receipt"]["listing"]["phase"], "CANCELLED")
                self.assertEqual(expected[-1]["view"]["phase"], "AUTHORIZED")
            elif scenario == "admission":
                self.assertEqual(expected[4]["receipt"], expected[0]["receipt"] | {"duplicate": True, "applied": None})
                self.assertEqual(expected[-1]["view"]["phase"], "CONSUMED")
            else:
                self.assertEqual(expected[7]["receipt"], expected[4]["receipt"] | {"duplicate": True, "applied": None})
                self.assertEqual(expected[8]["view"]["phase"], "CLOSED")
                self.assertEqual(expected[9]["view"]["right"]["version"], 2)
                self.assertEqual(expected[-1]["view"]["presentation"]["decision"], "STALE_VERSION")
                self.assertFalse(expected[-1]["view"]["venue_credential_reissued"])

    def test_booking_transcripts_file_and_stdin(self):
        for scenario in ("booking", "booking_admission"):
            with self.subTest(scenario=scenario):
                code, expected = run(load_fixture(FIXTURE), requests(scenario))
                self.assertEqual(code, 1)
                assert_booking_journey(self, scenario, expected)
                path = HERE / "fixtures" / f"ticket_operations_{scenario}.jsonl"
                for selector, stdin in ((str(path), None), ("-", path.read_text())):
                    result = self.cli("--fixture", str(FIXTURE), "--requests", selector, stdin=stdin)
                    self.assertEqual((result.returncode, result.stderr), (1, ""))
                    self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], expected)

    def test_booking_prerequisites_stop_without_binding_keys_or_undoing_prior_effects(self):
        from test_booking_session import requests as standalone_requests
        mutations = {r["operation"]: r for r in standalone_requests("booking_boundaries")}
        for operation in ("register_show", "hold", "release", "confirm", "cancel"):
            session = load_fixture(FIXTURE)
            before = snapshot(machines(session))
            request = {"surface": "booking", **mutations[operation]}
            with patch.object(session.booking._machine, operation,
                              side_effect=AssertionError("prerequisite must precede FSM")):
                code, rows = run(session, [request, requests("booking")[2]])
            self.assertEqual((code, len(rows)), (2, 1))
            self.assertEqual(rows[0]["error"]["type"], "BookingInputError")
            self.assertEqual(snapshot(machines(session)), before)
        session = load_fixture(FIXTURE)
        clock = requests("booking")[2]
        bad_clock = deepcopy(clock)
        bad_clock["arguments"]["subject_id"] = "wrong"
        code, rows = run(session, [bad_clock, requests("booking")[6], clock])
        self.assertEqual((code, len(rows)), (2, 2))
        self.assertIn("code", rows[0]["error"])
        self.assertEqual(rows[1]["error"]["type"], "BookingInputError")
        # Views/reconciliation work before initialization; successful replay counts.
        self.assertEqual(run(session, requests("booking_admission")[:2])[0], 0)
        self.assertEqual(run(session, [clock, requests("booking")[6]])[0], 0)
        confirm = requests("booking")[7]
        before = snapshot(machines(session))
        for quote in (None, "", " bad ", [], True, 1, "x" * 101):
            bad = deepcopy(confirm)
            bad["arguments"]["quote_ref"] = quote
            code, rows = run(session, [requests("booking")[3], bad, confirm])
            self.assertEqual((code, len(rows)), (2, 2))
            self.assertEqual(rows[0]["error"], {"code": "SLOT_OCCUPIED"})
            self.assertEqual(rows[1]["error"]["type"], "BookingInputError")
            self.assertEqual(snapshot(machines(session)), before)
        self.assertEqual(run(session, [confirm])[0], 0)  # same key unbound by local errors
        self.assertEqual(session.resale._adapter._source.calls, ())
        self.assertEqual(session.admission._adapter._source.calls, ())
        with patch("ticket_operations_cli._booking", side_effect=RuntimeError("programming fault")):
            with self.assertRaisesRegex(RuntimeError, "programming fault"):
                run(session, [confirm])

    def test_all_selectors_delegate_to_existing_dispatch_with_original_arguments(self):
        for surface, selectors in (("booking", BOOKING_DISPATCH), ("resale", RESALE_DISPATCH),
                                   ("admission", ADMISSION_DISPATCH)):
            for operation in selectors:
                with self.subTest(surface=surface, operation=operation):
                    session = Mock()
                    nested = {"operation": operation, "arguments": {"opaque": object()}}
                    result = {"operation": operation, "receipt": object()}
                    with patch("ticket_operations_cli._" + surface, return_value=result) as dispatch:
                        self.assertEqual(dispatch_request(session, {"surface": surface, **nested}),
                                         {"surface": surface, **result})
                        kwargs = {"quote_adapter": None} if surface == "booking" else {}
                        dispatch.assert_called_once_with(getattr(session, surface), nested, **kwargs)
        # Argument validation, including optional buyer_role, remains delegated.
        for buyer in ("omitted", None, "buyer-2"):
            transcript = requests("transfer")
            rows = [transcript[0], transcript[2]]
            if buyer == "omitted":
                del rows[1]["arguments"]["buyer_role"]
            else:
                rows[1]["arguments"]["buyer_role"] = buyer
            self.assertEqual(run(load_fixture(FIXTURE), rows)[0], 0)

    def test_strict_surface_operation_and_argument_failures_stop_stream(self):
        valid = requests("cancel")[0]
        variants = [[], None, {}, {k: v for k, v in valid.items() if k != "surface"},
                    valid | {"extra": 1}, valid | {"surface": []}, valid | {"surface": None},
                    valid | {"surface": "settlement"}, valid | {"surface": "Resale"},
                    valid | {"surface": "admission"}, valid | {"operation": "adopt_issued"},
                    valid | {"operation": []}, valid | {"arguments": []},
                    requests("admission")[0] | {"surface": "resale"}]
        for surface, selectors in (("booking", BOOKING_DISPATCH), ("resale", RESALE_DISPATCH),
                                   ("admission", ADMISSION_DISPATCH), ("settlement", _SETTLEMENT_DISPATCH)):
            for operation, (_, fields, _) in selectors.items():
                args = dict.fromkeys(fields, "x")
                for field in fields:
                    variants.append(dict(surface=surface, operation=operation,
                                         arguments={k: v for k, v in args.items() if k != field}))
                variants.append(dict(surface=surface, operation=operation, arguments=args | {"extra": 1}))
        variants += [dict(surface="booking", operation=op, arguments={})
                     for op in ("observe_payment", "authorize_admission",
                                "consume", "cancel_show", "restore", "export_journal", "canonical_state")]
        for request in variants:
            with self.subTest(request=request):
                session = load_fixture(FIXTURE)
                before = snapshot(machines(session))
                status, rows = run(session, [request, valid])
                self.assertEqual(status, 2)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["error"]["type"], "FixtureError")
                self.assertEqual(snapshot(machines(session)), before)
                self.assertEqual(session.resale._adapter._source.calls, ())
                self.assertEqual(session.admission._adapter._source.calls, ())

    def test_bad_json_stops_and_structural_error_overrides_previous_refusal(self):
        texts = ['{', '\n', 'true', '[]',
                 '{"surface":"resale","surface":"admission","operation":"view","arguments":{}}',
                 '{"surface":"resale","operation":"view","arguments":{"listing_id":"a","listing_id":"b"}}']
        texts += ['{"surface":"booking","operation":"view","arguments":{"reservation_id":"a","reservation_id":"b"}}',
                  '{"surface":"booking","operation":"view","operation":"cancel","arguments":{}}']
        texts += ['{"surface":"' + surface + '","operation":"view","arguments":{"' + identity + '":' + n + '}}'
                  for surface, identity in (("resale", "listing_id"), ("booking", "reservation_id"))
                  for n in ('NaN', 'Infinity', '-Infinity', '1e999')]
        for text in texts:
            session = load_fixture(FIXTURE)
            before = snapshot(machines(session))
            with redirect_stdout(io.StringIO()) as output:
                code = run_requests(session, [text, json.dumps(requests("cancel")[0])])
            self.assertEqual(code, 2)
            self.assertEqual(len(output.getvalue().splitlines()), 1)
            self.assertEqual(snapshot(machines(session)), before)
        status, rows = run(load_fixture(FIXTURE), requests("cancel")[:2] + [{}])
        self.assertEqual(status, 2)
        self.assertEqual(rows[1]["error"], {"code": "LISTING_LOCKED"})
        self.assertEqual(rows[2]["error"]["type"], "FixtureError")

    def test_exit_zero_file_setup_and_usage_failures_and_importability(self):
        self.assertEqual(run(load_fixture(FIXTURE), [])[0], 0)
        self.assertEqual(run(load_fixture(FIXTURE), [requests("admission")[-1]])[0], 0)
        for args in ((), ("--fixture", str(FIXTURE), "--requests", "/absent"),
                     ("--fixture", "/absent", "--requests", "-")):
            self.assertEqual(self.cli(*args, stdin="").returncode, 2)
        for value in ({}, fixture()):
            if value:
                next(e for e in value["setup"] if e["operation"] == "hold")["body"]["slot"] = 100
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"
                path.write_text(json.dumps(value))
                result = self.cli("--fixture", str(path), "--requests", "-", stdin="")
                self.assertEqual(result.returncode, 2)
                self.assertIsNone(json.loads(result.stdout)["surface"])
        env = dict(os.environ, PYTHONPATH=str(HERE) + os.pathsep + os.environ.get("PYTHONPATH", ""), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c",
                                 "import ticket_operations_session, ticket_operations_fixture, ticket_operations_cli"],
                                env=env, cwd=tempfile.gettempdir(), capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        with patch("ticket_operations_cli._admission", side_effect=RuntimeError("programming fault")):
            with self.assertRaisesRegex(RuntimeError, "programming fault"):
                run(load_fixture(FIXTURE), [requests("admission")[0]])


    def test_reconcile_file_stdin_and_direct_fsm_parity(self):
        from test_booking_cli import check_reconcile_cli
        check_reconcile_cli(self, 'ticket_operations')


class TicketRecordedPaymentCliTests(RecordedPaymentDeskChecks, unittest.TestCase):
    shared = True
    prefix = "ticket_operations"
    payment_fixture = HERE / "fixtures" / "ticket_operations_payment_session.json"
    constructor = "ticket_operations_session.SettlementMachine"
    loader = staticmethod(load_fixture)
    run_rows = staticmethod(run)
