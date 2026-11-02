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
from fake_presentation_source import SyntheticPresentationFault
from fake_resale_offer_source import SyntheticResaleOfferFault
from resale_cli import _DISPATCH as RESALE_DISPATCH
from ticket_operations_cli import dispatch_request, run_requests
from ticket_operations_fixture import load_fixture
from test_ticket_operations_session import FIXTURE, HERE, fixture, machines, requests, snapshot


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

    def test_all_selectors_delegate_to_existing_dispatch_with_original_arguments(self):
        for surface, selectors in (("resale", RESALE_DISPATCH), ("admission", ADMISSION_DISPATCH)):
            for operation in selectors:
                with self.subTest(surface=surface, operation=operation):
                    session = Mock()
                    nested = {"operation": operation, "arguments": {"opaque": object()}}
                    result = {"operation": operation, "receipt": object()}
                    with patch("ticket_operations_cli._" + surface, return_value=result) as dispatch:
                        self.assertEqual(dispatch_request(session, {"surface": surface, **nested}),
                                         {"surface": surface, **result})
                        dispatch.assert_called_once_with(getattr(session, surface), nested)
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
        for surface, selectors in (("resale", RESALE_DISPATCH), ("admission", ADMISSION_DISPATCH)):
            for operation, (_, fields, _) in selectors.items():
                args = dict.fromkeys(fields, "x")
                for field in fields:
                    variants.append(dict(surface=surface, operation=operation,
                                         arguments={k: v for k, v in args.items() if k != field}))
                variants.append(dict(surface=surface, operation=operation, arguments=args | {"extra": 1}))
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
        texts += ['{"surface":"resale","operation":"view","arguments":{"listing_id":' + n + '}}'
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
        env = dict(os.environ, PYTHONPATH=str(HERE), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c",
                                 "import ticket_operations_session, ticket_operations_fixture, ticket_operations_cli"],
                                env=env, cwd=tempfile.gettempdir(), capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        with patch("ticket_operations_cli._admission", side_effect=RuntimeError("programming fault")):
            with self.assertRaisesRegex(RuntimeError, "programming fault"):
                run(load_fixture(FIXTURE), [requests("admission")[0]])
