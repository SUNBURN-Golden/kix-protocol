"""Strict fixture and subprocess JSONL acceptance; no sockets or external services."""

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

from admission_cli import dispatch_request, run_requests
from admission_fixture import FixtureError, decode_json, load_fixture
from admission_session import AdmissionSession
from presentation_source import InvalidPresentationRecord
from reservation_fsm import ReservationError
from test_admission_session import assert_flags

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "admission_session.json"
REQUESTS = HERE / "fixtures" / "admission_requests.jsonl"


def fixture():
    return json.loads(FIXTURE.read_text())


def requests():
    return [json.loads(line) for line in REQUESTS.read_text().splitlines()]


class AdmissionFixtureTests(unittest.TestCase):
    def load(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(value))
            return load_fixture(path)

    def test_fresh_real_bound_graph_and_caller_supplied_values(self):
        value = fixture()
        # Replace all caller fixture identifiers and role labels, preserving clock subject.
        def rename(item):
            if isinstance(item, dict):
                return {k: rename(v) for k, v in item.items()}
            if isinstance(item, list):
                return [rename(v) for v in item]
            if type(item) is str and item in ("issue-1", "buyer-1", "gate-a", "gate-b"):
                return "custom-" + item
            return item
        value["setup"] = rename(value["setup"])
        for recording in value["presentations"]:
            recording["recorded_text"] = json.dumps(rename(json.loads(recording["recorded_text"])))
        first, second = self.load(value), self.load(value)
        self.assertIsInstance(first, AdmissionSession)
        req = requests()[1]
        req["arguments"]["gate_role"] = "custom-gate-a"
        dispatch_request(first, req)
        self.assertEqual(first.view("custom-issue-1")["phase"], "AUTHORIZED")
        self.assertEqual(second.view("custom-issue-1")["phase"], "ELIGIBLE")
        assert_flags(self, second.view("custom-issue-1"))

    def test_every_setup_and_envelope_field_is_required_before_construction(self):
        base = fixture()
        variants = []
        for field in base:
            changed = deepcopy(base)
            del changed[field]
            variants.append((field, changed))
        for field in base["presentations"][0]:
            changed = deepcopy(base)
            del changed["presentations"][0][field]
            variants.append((f"presentation {field}", changed))
        for index, entry in enumerate(base["setup"]):
            for field in entry:
                changed = deepcopy(base)
                del changed["setup"][index][field]
                variants.append((f"entry {index} {field}", changed))
            for field in entry["body"]:
                changed = deepcopy(base)
                del changed["setup"][index]["body"][field]
                variants.append((f"body {index} {field}", changed))
        for label, changed in variants:
            with self.subTest(label=label), patch("admission_fixture.SettlementMachine") as construct:
                with self.assertRaises(FixtureError):
                    self.load(changed)
                construct.assert_not_called()

    def test_missing_clocks_issuance_adoption_and_binding_fail_without_defaults(self):
        for machine, operation in (("reservation", "set_clock"), ("resale", "set_clock"),
                                   ("admission", "set_clock"), ("reservation", "issue"),
                                   ("resale", "adopt_issued"), ("admission", "adopt_issued"),
                                   ("reservation", "confirm"), ("reservation", "bind_settlement")):
            with self.subTest(machine=machine, operation=operation):
                value = fixture()
                value["setup"] = [e for e in value["setup"]
                                  if (e["machine"], e["operation"]) != (machine, operation)]
                with self.assertRaises(FixtureError):
                    self.load(value)
        for field in ("reservation_id", "quote_ref"):
            value = fixture()
            next(e for e in value["setup"] if e["operation"] == "adopt_issued")["body"][field] = None
            with self.assertRaises(FixtureError):
                self.load(value)

    def test_rejects_unknown_fields_shapes_versions_operations_and_recording_identities(self):
        variants = [[], fixture() | {"extra": 1}, fixture() | {"fixture_version": True},
                    fixture() | {"fixture_version": 2}, fixture() | {"provenance": "PRODUCTION"},
                    fixture() | {"setup": {}}, fixture() | {"presentations": {}},
                    fixture() | {"presentations": [None]}]
        for extra in ({"fault": "synthetic_presentation_timeout"}, {"extra": 1},
                      {"operation": "view"}, {"operation": []}, {"recorded_text": {}},
                      {"presentation_id": " bad "}):
            value = fixture()
            value["presentations"][0].update(extra)
            variants.append(value)
        value = fixture()
        value["presentations"].append(deepcopy(value["presentations"][0]))
        variants.append(value)
        for extra in ({"operation": "consume"}, {"machine": []}, {"body": {"extra": 1}}):
            value = fixture()
            value["setup"][0].update(extra)
            variants.append(value)
        for value in variants:
            with self.subTest(value=value):
                with self.assertRaises(FixtureError):
                    self.load(value)

    def test_duplicate_keys_constants_overflow_and_invalid_json_reject(self):
        for text in ('{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}',
                     '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e999}', '{'):
            with self.subTest(text=text), self.assertRaises(FixtureError):
                decode_json(text)

    def test_failed_setup_never_publishes_partially_initialized_session(self):
        value = fixture()
        next(e for e in value["setup"] if e["operation"] == "hold")["body"]["slot"] = 100
        with patch("admission_fixture.AdmissionSession") as publish:
            with self.assertRaises(ReservationError):
                self.load(value)
            publish.assert_not_called()

    def test_recorded_text_validation_is_deferred_to_fetch_and_fault_markers_are_local(self):
        value = fixture()
        value["presentations"][0]["recorded_text"] = "{"
        session = self.load(value)
        with self.assertRaises(InvalidPresentationRecord):
            dispatch_request(session, requests()[1])
        for fault in ("synthetic_presentation_error", "synthetic_presentation_timeout", "bad"):
            value = fixture()
            entry = value["presentations"][0]
            del entry["recorded_text"]
            entry["fault"] = fault
            if fault == "bad":
                with self.assertRaises(FixtureError):
                    self.load(value)
            else:
                session = self.load(value)
                out = io.StringIO()
                with redirect_stdout(out):
                    result = run_requests(session, [json.dumps(requests()[1])])
                self.assertEqual(result, 1)
                self.assertEqual(json.loads(out.getvalue())["error"]["type"], "PresentationSourceError")
                self.assertEqual(session.view("issue-1")["phase"], "ELIGIBLE")


class AdmissionCliTests(unittest.TestCase):
    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(HERE / "admission_cli.py"), *args], input=stdin,
                              capture_output=True, text=True, cwd=HERE.parent, check=False)

    def test_runnable_transcript_receipts_views_and_existing_codes(self):
        completed = self.cli("--fixture", str(FIXTURE), "--requests", str(REQUESTS))
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(completed.stderr, "")
        rows = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(rows), 14)
        self.assertEqual(rows[0]["view"]["phase"], "ELIGIBLE")
        self.assertEqual(rows[2]["view"]["phase"], "AUTHORIZED")
        self.assertEqual(rows[2]["view"]["version"], 1)
        self.assertTrue(rows[3]["view"]["presentation"]["fresh"])
        consumed = rows[4]["receipt"]
        self.assertEqual(consumed["credential"]["version"], 2)
        self.assertEqual(rows[5]["receipt"], consumed | {"duplicate": True, "applied": None})
        self.assertEqual(rows[6]["receipt"], rows[1]["receipt"] | {"duplicate": True, "applied": None})
        self.assertEqual(rows[7]["view"]["phase"], "CONSUMED")
        self.assertEqual([r["error"]["code"] for r in rows if "error" in r],
                         ["IDEMPOTENCY_CONFLICT", "STALE_VERSION", "ADMISSION_EXPIRED"])
        self.assertTrue(rows[13]["view"]["admission_expired"])
        self.assertEqual(rows[13]["view"]["version"], 1)
        for row in rows:
            for key in ("view", "receipt"):
                if key in row:
                    assert_flags(self, row[key])

    def test_inprocess_transcript_replay_has_no_extra_effect_or_journal_entry(self):
        session = load_fixture(FIXTURE)
        # Observe the actual graph's journals, rather than infer effect from output.
        machine = session._machine
        all_requests = requests()
        for req in all_requests[:5]:
            dispatch_request(session, req)
        before = machine.canonical_state(), machine._tickets.canonical_state()
        dispatch_request(session, all_requests[5])
        self.assertEqual((machine.canonical_state(), machine._tickets.canonical_state()), before)

    def test_stdin_success_and_missing_presentation_exit_one(self):
        rows = requests()[:5]
        result = self.cli("--fixture", str(FIXTURE), "--requests", "-",
                          stdin="".join(json.dumps(r) + "\n" for r in rows))
        self.assertEqual(result.returncode, 0, result.stderr)
        rows[1]["arguments"]["presentation_id"] = "missing"
        result = self.cli("--fixture", str(FIXTURE), "--requests", "-", stdin=json.dumps(rows[1])+"\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"]["type"], "PresentationNotFound")

    def test_every_session_argument_is_required_and_unknown_input_stops_before_dispatch(self):
        variants = [[], {}, {"operation": "view"}, {"operation": "view", "arguments": {}, "extra": 1},
                    {"operation": "adopt_issued", "arguments": {}}, {"operation": [], "arguments": {}},
                    {"operation": "view", "arguments": []}]
        # Includes all explicit methods and their mandatory arguments.
        unique = {r["operation"]: r for r in requests()}
        adopt = json.loads((HERE / "fixtures/ticket_operations_fulfillment.jsonl").read_text().splitlines()[4])
        unique["adopt_issued"] = {k: v for k, v in adopt.items() if k != "surface"}
        unique["reconcile"] = {"operation": "reconcile",
                               "arguments": {"right_id": "issue-1", "idempotency_key": "recon"}}
        for req in unique.values():
            for field in req["arguments"]:
                value = deepcopy(req)
                del value["arguments"][field]
                variants.append(value)
            value = deepcopy(req)
            value["arguments"]["extra"] = True
            variants.append(value)
        for req in variants:
            with self.subTest(req=req):
                session = Mock()
                out = io.StringIO()
                with redirect_stdout(out):
                    status = run_requests(session, [json.dumps(req), json.dumps(requests()[0])])
                self.assertEqual(status, 2)
                self.assertEqual(len(out.getvalue().splitlines()), 1)
                self.assertEqual(session.mock_calls, [])

    def test_malformed_lines_setup_and_paths_exit_two(self):
        for text in ('{', '\n', '{"operation":"view","operation":"consume","arguments":{}}',
                     '{"operation":"view","arguments":{"right_id":NaN}}'):
            with self.subTest(text=text):
                result = self.cli("--fixture", str(FIXTURE), "--requests", "-", stdin=text)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)["error"]["type"], "FixtureError")
        for args in (("--fixture", str(FIXTURE), "--requests", str(HERE / "absent")),
                     ("--fixture", str(HERE / "absent"), "--requests", "-"), ()):
            self.assertEqual(self.cli(*args, stdin="").returncode, 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{}')
            self.assertEqual(self.cli("--fixture", str(path), "--requests", "-", stdin="").returncode, 2)

    def test_importable_without_cli_side_effects_and_unexpected_failure_is_visible(self):
        env = dict(os.environ, PYTHONPATH=str(HERE), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", "import admission_session, admission_fixture, admission_cli"],
                                env=env, cwd=tempfile.gettempdir(), capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        machine = Mock()
        machine.view.side_effect = RuntimeError("programming fault")
        session = AdmissionSession(machine, Mock())
        with self.assertRaisesRegex(RuntimeError, "programming fault"):
            run_requests(session, [json.dumps(requests()[0])])

    def test_reconcile_file_stdin_and_direct_fsm_parity(self):
        from test_booking_cli import check_reconcile_cli
        check_reconcile_cli(self, 'admission')
