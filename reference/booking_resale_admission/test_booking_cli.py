"""Strict JSONL, executable transcript and actual-machine parity coverage."""

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
from unittest.mock import Mock

from admission_fixture import FixtureError
from booking_cli import dispatch_request, run_requests
from booking_session import BookingSession
from reservation_fsm import REPLAYABLE, ReservationMachine
from test_booking_session import HERE, invoke, requests, snapshot
from test_reservation_fsm import assert_not_final


def run(session, lines):
    out = io.StringIO()
    with redirect_stdout(out):
        status = run_requests(session, lines)
    return status, [json.loads(line) for line in out.getvalue().splitlines()]


def run_rows(session, rows):
    return run(session, [json.dumps(row) + "\n" for row in rows])


class BookingCliTests(unittest.TestCase):
    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(HERE / "booking_cli.py"), *args], input=stdin,
                              capture_output=True, text=True, cwd=HERE.parent, check=False)

    def test_file_and_stdin_transcripts_exact_outcomes_and_nonclaims(self):
        for name, expected_status in (("booking_confirm", 0), ("booking_cancel", 0),
                                      ("booking_boundaries", 1)):
            path = HERE / "fixtures" / f"{name}.jsonl"
            results = []
            for selector, stdin in ((str(path), None), ("-", path.read_text())):
                result = self.cli("--requests", selector, stdin=stdin)
                self.assertEqual((result.returncode, result.stderr), (expected_status, ""))
                rows = [json.loads(line) for line in result.stdout.splitlines()]
                self.assertEqual(len(rows), len(requests(name)))
                results.append(rows)
                for row in rows:
                    if "error" not in row:
                        assert_not_final(self, row.get("receipt", row.get("view")))
            self.assertEqual(*results)
            rows = results[0]
            if name == "booking_confirm":
                self.assertEqual(rows[1]["receipt"]["show"]["slots"][0]["state"], "FREE")
                view = rows[4]["view"]
                self.assertEqual(view["phase"], "CONFIRMED")
                for field in ("payment_ref", "issuance_id", "settlement_id", "right"):
                    self.assertIsNone(view[field])
                self.assertEqual(rows[5]["view"]["show"]["payment_ref_count"], 0)
            elif name == "booking_cancel":
                self.assertEqual(rows[4]["receipt"]["reservation"]["phase"], "CANCELLED")
                self.assertEqual(rows[5]["receipt"], rows[3]["receipt"] |
                                 {"duplicate": True, "applied": None})
                self.assertEqual(rows[6]["view"]["phase"], "CANCELLED")
                self.assertEqual(rows[7]["view"]["show"]["slots"][0]["state"], "FREE")
            else:
                self.assertEqual([row["error"]["code"] for row in rows if "error" in row],
                                 ["SLOT_OCCUPIED", "SLOT_OCCUPIED", "IDEMPOTENCY_CONFLICT",
                                  "PRIMARY_PRICE_MISMATCH", "RESERVATION_EXPIRED", "SLOT_OCCUPIED"])
                self.assertEqual(rows[6]["receipt"]["reservation"]["buyer_role"], "buyer-2")
                self.assertEqual(rows[7]["receipt"], rows[6]["receipt"] |
                                 {"duplicate": True, "applied": None})
                self.assertEqual(rows[12]["receipt"], rows[10]["receipt"] |
                                 {"duplicate": True, "applied": None})
                self.assertEqual(rows[13]["view"]["phase"], "CANCELLED")
                self.assertEqual(rows[16]["view"]["phase"], "HELD")
                self.assertTrue(rows[16]["view"]["expired"])
                self.assertEqual(rows[19]["view"]["show"]["slots"][0]["state"], "RESERVED")
                self.assertEqual(rows[20]["receipt"]["reservation"]["phase"], "RELEASED")
                self.assertEqual(rows[21]["receipt"]["reservation"]["buyer_role"], "buyer-4")

    def test_cli_matches_direct_machine_after_each_explicit_line_and_views_do_not_mutate(self):
        wrapped, direct = ReservationMachine(), ReservationMachine()
        session = BookingSession(wrapped)
        for request in requests("booking_boundaries"):
            before = snapshot(wrapped)
            status, rows = run_rows(session, [request])
            expected = invoke(direct, request)
            if "error" in expected:
                self.assertEqual(status, 1)
                self.assertEqual(rows, [{"operation": request["operation"],
                                         "error": {"code": expected["error"]}}])
            else:
                key = "view" if request["operation"].startswith("view") else "receipt"
                self.assertEqual((status, rows), (0, [{"operation": request["operation"], key: expected}]))
            self.assertEqual(snapshot(wrapped), snapshot(direct))
            if request["operation"].startswith("view"):
                self.assertEqual(snapshot(wrapped), before)

    def test_every_argument_required_extra_arguments_and_excluded_selectors_rejected_without_dispatch(self):
        examples = {r["operation"]: r for r in requests("booking_boundaries")}
        self.assertEqual(set(examples), {"register_show", "set_clock", "hold", "release", "confirm",
                                         "cancel", "view", "view_show"})
        variants = [None, [], True, {}, {"operation": "view"},
                    {"operation": "view", "arguments": {}, "extra": 1},
                    {"operation": [], "arguments": {}}, {"operation": "view", "arguments": []}]
        for request in examples.values():
            for field in request["arguments"]:
                row = deepcopy(request)
                del row["arguments"][field]
                variants.append(row)
            variants.append(request | {"arguments": request["arguments"] | {"extra": 1}})
            if request["operation"].startswith("view"):
                variants.append(request | {"arguments": request["arguments"] | {"idempotency_key": "key"}})
        excluded = (REPLAYABLE - set(examples)) | {"reconcile", "restore", "reject_external", "list_resale",
                    "accept_resale", "lookup", "observe", "initiate", "reservation_hold", "__dict__", ""}
        variants += [{"operation": operation, "arguments": {}} for operation in excluded]
        for req in variants:
            with self.subTest(req=req):
                session = Mock()
                status, rows = run_rows(session, [req, requests()[0]])
                self.assertEqual((status, len(rows)), (2, 1))
                self.assertEqual(rows[0]["error"]["type"], "FixtureError")
                self.assertEqual(session.mock_calls, [])

    def test_malformed_nested_duplicates_nonfinite_and_blank_lines_stop_before_dispatch(self):
        texts = ['{', '', '\n', 'null', '[]', 'true',
                 '{"operation":"view","operation":"cancel","arguments":{}}',
                 '{"operation":"view","arguments":{"reservation_id":"x","reservation_id":"y"}}',
                 '{"operation":"view","arguments":{"reservation_id":{"x":1,"x":2}}}']
        texts += ['{"operation":"view","arguments":{"reservation_id":' + value + '}}'
                  for value in ('NaN', 'Infinity', '-Infinity', '1e999')]
        for text in texts:
            with self.subTest(text=text):
                session = Mock()
                status, rows = run(session, [text, json.dumps(requests()[0])])
                self.assertEqual((status, len(rows)), (2, 1))
                self.assertEqual(rows[0]["error"]["type"], "FixtureError")
                self.assertEqual(session.mock_calls, [])

    def test_input_failure_stops_but_prior_accepted_effects_remain_and_keys_are_not_bound(self):
        machine = ReservationMachine()
        session = BookingSession(machine)
        for rows in ([requests()[1], requests()[0]],):
            status, output = run_rows(session, rows)
            self.assertEqual(status, 2)
            self.assertEqual(output[0]["error"]["type"], "BookingInputError")
            self.assertEqual(machine.export_journal(), [])
        run_rows(session, requests()[:3])
        before = snapshot(machine)
        for quote in (None, " bad "):
            bad = deepcopy(requests()[3])
            bad["arguments"]["quote_ref"] = quote
            status, rows = run_rows(session, [bad, requests()[3]])
            self.assertEqual((status, len(rows)), (2, 1))
            self.assertEqual(rows[0]["error"]["type"], "BookingInputError")
            self.assertEqual(snapshot(machine), before)
        status, rows = run(session, ['{', json.dumps(requests()[3])])
        self.assertEqual(status, 2)
        self.assertEqual(snapshot(machine), before)
        self.assertEqual(run_rows(session, [requests()[3]])[0], 0)

    def test_domain_rejection_continues_only_explicit_lines_and_structural_failure_has_exit_precedence(self):
        machine = ReservationMachine()
        session = BookingSession(machine)
        bad = {"operation": "set_clock", "arguments": {"subject_id": "clock", "now_ms": True,
                                                         "idempotency_key": "bad-clock"}}
        status, rows = run_rows(session, [bad, requests()[0], requests()[1]])
        self.assertEqual(status, 1)
        self.assertEqual(rows[0]["error"], {"code": "CLOCK"})
        self.assertEqual([r["op"] for r in machine.export_journal()], ["set_clock", "register_show"])
        status, rows = run(session, [json.dumps(bad), '{', json.dumps(requests()[2])])
        self.assertEqual((status, len(rows)), (2, 2))
        self.assertEqual(len(machine.export_journal()), 2)
        self.assertEqual(run_rows(BookingSession(ReservationMachine()), [bad])[0], 1)

    def test_usage_file_encoding_empty_input_and_import_side_effects(self):
        for args in ((), ("--requests", str(HERE / "absent-booking-file"))):
            self.assertEqual(self.cli(*args).returncode, 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            path.write_bytes(b'\xff\n')
            result = self.cli("--requests", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["error"]["type"], "UnicodeDecodeError")
        result = self.cli("--requests", "-", stdin="")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        env = dict(os.environ, PYTHONPATH=str(HERE), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c", "import booking_session, booking_cli"], env=env,
                                cwd=tempfile.gettempdir(), capture_output=True, text=True, check=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        machine = Mock(spec=ReservationMachine)
        machine.view.side_effect = RuntimeError("programming fault")
        with self.assertRaisesRegex(RuntimeError, "programming fault"):
            run_rows(BookingSession(machine), [requests()[4]])
