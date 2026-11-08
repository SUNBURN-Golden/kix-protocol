"""Author-side adapter tests; existing BudgetTests/TL-4 own arithmetic coverage."""

import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import reward_budget_workbench as workbench
from reward_fixture import FixtureError, decode_json
from token_reward_model import (
    MONEY_MAX, PROVENANCE, UNIT, TokenRewardError,
    net_residual_revenue, reward_budget,
)


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures" / "reward_budget"
CLI = ROOT / "reward_budget_workbench.py"
RESIDUAL = decode_json((FIXTURES / "residual.json").read_text())
BUDGET = decode_json((FIXTURES / "budget_floor.json").read_text())


def envelope(operation, key, value):
    return {"operation": operation, "provenance": PROVENANCE, "unit": UNIT,
            "result": {key: value}}


def results(output):
    return [decode_json(line) for line in output.splitlines() if line.startswith("{")]


def guided_request(request, confirmation="CALCULATE"):
    return "\n".join([request["operation"],
                      *(json.dumps(request["arguments"][field])
                        for field in workbench._DISPATCH[request["operation"]][1]),
                      confirmation]) + "\n"


def refusals():
    # Direct-model comparisons, including type preservation and error precedence.
    for request in (RESIDUAL, BUDGET):
        for field in request["arguments"]:
            for value in (True, "1", 1.5, None, -1, MONEY_MAX + 1, 2**53 + 1):
                changed = copy.deepcopy(request)
                changed["arguments"][field] = value
                yield changed
    for changes in ({"ratio_denominator": 0}, {"periods": 0},
                    {"cap": 1, "ratio_numerator": MONEY_MAX,
                     "net_residual": MONEY_MAX, "ratio_denominator": 1}):
        yield dict(BUDGET, arguments=dict(BUDGET["arguments"], **changes))
    for changes in ({"refundable_window_revenue": 101}, {"operating_cost": 100}):
        yield dict(RESIDUAL, arguments=dict(RESIDUAL["arguments"], **changes))


class DispatchTests(unittest.TestCase):
    def test_success_envelopes_and_no_input_mutation(self):
        for name, expected in (("residual", envelope("net_residual_revenue", "net_residual", 40)),
                               ("budget_floor", envelope("reward_budget", "budget_ceiling", 13)),
                               ("budget_cap", envelope("reward_budget", "budget_ceiling", 10))):
            request = decode_json((FIXTURES / (name + ".json")).read_text())
            before = copy.deepcopy(request)
            self.assertEqual(workbench.dispatch_request(request), expected)
            self.assertEqual(request, before)

    def test_shape_missing_every_field_and_unsupported_selectors(self):
        bad = [None, [], 1, {}, {"operation": "reward_budget"},
               dict(BUDGET, extra=1), dict(BUDGET, arguments=[])]
        for selector in ("submit", "__dict__", "reward_id", "REWARD_BUDGET", [], None, True):
            bad.append(dict(BUDGET, operation=selector))
        for request in (RESIDUAL, BUDGET):
            for field in request["arguments"]:
                missing = copy.deepcopy(request)
                del missing["arguments"][field]
                bad.append(missing)
            bad.append(dict(request, arguments=dict(request["arguments"], currency="KRW")))
        for request in bad:
            with self.subTest(request=request), self.assertRaises(FixtureError):
                workbench.dispatch_request(request)

    def test_importable_non_json_values_refused(self):
        for value in (float("nan"), float("inf"), object(), {1}, "\ud800"):
            with self.subTest(value=repr(value)), self.assertRaises(FixtureError):
                workbench.dispatch_request(dict(BUDGET, arguments=dict(BUDGET["arguments"], cap=value)))

    def test_model_errors_propagate_with_original_codes(self):
        for request in refusals():
            function = (reward_budget if request["operation"] == "reward_budget"
                        else net_residual_revenue)
            with self.subTest(request=request):
                with self.assertRaises(TokenRewardError) as direct:
                    function(**request["arguments"])
                with self.assertRaises(TokenRewardError) as dispatched:
                    workbench.dispatch_request(request)
                self.assertEqual(dispatched.exception.code, direct.exception.code)
        original = TokenRewardError("ORIGINAL")
        def refuse(**arguments):
            raise original
        with patch.dict(workbench._DISPATCH,
                        reward_budget=(refuse, workbench._DISPATCH["reward_budget"][1], "budget_ceiling")):
            with self.assertRaises(TokenRewardError) as caught:
                workbench.dispatch_request(BUDGET)
        self.assertIs(caught.exception, original)


class GuidedTests(unittest.TestCase):
    def run_guided(self, text):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(workbench, "dispatch_request", wraps=workbench.dispatch_request) as dispatch:
            status = workbench.run_guided(input_stream=io.StringIO(text),
                                          output_stream=output, error_stream=errors)
        return status, output.getvalue(), errors.getvalue(), dispatch.call_args_list

    def test_explicit_handoff_matches_complete_requests(self):
        for name, cap, ceiling in (("guided_floor", 100, 13), ("guided_cap", 10, 10)):
            status, output, errors, calls = self.run_guided((FIXTURES / (name + ".txt")).read_text())
            self.assertEqual((status, errors), (0, ""))
            self.assertEqual([call.args[0] for call in calls],
                             [RESIDUAL, dict(BUDGET, arguments=dict(BUDGET["arguments"], cap=cap))])
            self.assertEqual(results(output), [envelope("net_residual_revenue", "net_residual", 40),
                                               envelope("reward_budget", "budget_ceiling", ceiling)])
            self.assertIn("periods is not a multiplier", output)
            self.assertIn("UNDETERMINED", output)

    def test_direct_entry_for_both_operations(self):
        for request in (RESIDUAL, BUDGET):
            text = guided_request(request)
            if request is RESIDUAL:
                text += "DECLINE\n"
            status, output, errors, calls = self.run_guided(text)
            self.assertEqual((status, errors), (0, ""))
            self.assertEqual(results(output), [workbench.dispatch_request(request)])
            self.assertEqual([call.args[0] for call in calls], [request])

    def test_declines_and_literal_confirmation(self):
        for request in (RESIDUAL, BUDGET):
            for answer in ("DECLINE", "", "calculate", " CALCULATE", "CALCULATE "):
                status, output, errors, calls = self.run_guided(guided_request(request, answer))
                self.assertEqual((status, errors, calls, results(output)), (0, "", [], []))
        start = guided_request(RESIDUAL)
        for answer in ("DECLINE", "", "use_residual", "USE_RESIDUAL "):
            status, output, errors, calls = self.run_guided(start + answer + "\n")
            self.assertEqual((status, errors, len(calls), len(results(output))), (0, "", 1, 1))
        text = (FIXTURES / "guided_floor.txt").read_text().splitlines()
        text[-1] = "DECLINE"
        status, output, errors, calls = self.run_guided("\n".join(text) + "\n")
        self.assertEqual((status, errors, len(calls), len(results(output))), (0, "", 1, 1))

    def test_eof_at_every_prompt_never_dispatches_incomplete_request(self):
        texts = [(FIXTURES / "guided_floor.txt").read_text(), guided_request(BUDGET)]
        for text in texts:
            lines = text.splitlines(keepends=True)
            for count in range(len(lines)):
                with self.subTest(count=count, operation=lines[0]):
                    status, output, errors, calls = self.run_guided("".join(lines[:count]))
                    self.assertEqual(status, 2)
                    self.assertIn("EOF", errors)
                    expected = int(lines[0].startswith("net_residual") and count >= 9)
                    self.assertEqual(len(calls), expected)
                    self.assertEqual(len(results(output)), expected)

    def test_bad_scalar_or_selection_stops_without_retry(self):
        for scalar in ("{}", "[]", "NaN", "Infinity", '"\\ud800"', "{", ""):
            status, output, errors, calls = self.run_guided("reward_budget\n" + scalar + "\n")
            self.assertEqual((status, calls, results(output)), (2, [], []))
            self.assertIn("FixtureError", errors)
        status, _, _, calls = self.run_guided("submit\n" + guided_request(BUDGET))
        self.assertEqual((status, calls), (2, []))

    def test_decoded_scalar_types_and_large_integer_reach_model_unchanged(self):
        for value in (True, "10", 1.5, None, 2**53 + 1):
            request = dict(BUDGET, arguments=dict(BUDGET["arguments"], cap=value))
            status, output, errors, calls = self.run_guided(guided_request(request))
            self.assertEqual((status, results(output)), (1, []))
            passed = calls[0].args[0]["arguments"]["cap"]
            self.assertIs(type(passed), type(value))
            self.assertEqual(passed, value)
            self.assertEqual(decode_json(errors)["error"], {"code": "INVALID_NONNEGATIVE"})

    def test_complete_preview_flushed_before_each_confirmation(self):
        class Output(io.StringIO):
            flush_count = 0
            def flush(self):
                self.flush_count += 1
        output = Output()
        class Input(io.StringIO):
            def readline(inner):
                line = super().readline()
                if line.strip() == "CALCULATE":
                    preview = [s for s in output.getvalue().splitlines() if s.startswith("Request: ")][-1]
                    request = decode_json(preview.removeprefix("Request: "))
                    self.assertEqual(set(request["arguments"]), set(workbench._DISPATCH[request["operation"]][1]))
                    self.assertGreater(output.flush_count, 0)
                return line
        status = workbench.run_guided(input_stream=Input((FIXTURES / "guided_floor.txt").read_text()),
                                      output_stream=output, error_stream=io.StringIO())
        self.assertEqual(status, 0)


class CliTests(unittest.TestCase):
    def cli(self, *args, text=None):
        return subprocess.run([sys.executable, str(CLI), *map(str, args)], input=text,
                              capture_output=True, text=True, timeout=10)

    def test_file_stdin_guided_identical_success_envelopes(self):
        for name in ("residual", "budget_floor", "budget_cap"):
            path = FIXTURES / (name + ".json")
            request = decode_json(path.read_text())
            guided = guided_request(request) + ("DECLINE\n" if name == "residual" else "")
            runs = [self.cli("--request", path), self.cli("--request", "-", text=path.read_text()),
                    self.cli("--guided", text=guided)]
            for run in runs:
                self.assertEqual((run.returncode, run.stderr), (0, ""))
                self.assertEqual(results(run.stdout), [workbench.dispatch_request(request)])
            self.assertEqual(runs[0].stdout, runs[1].stdout)

    def test_real_guided_fixtures(self):
        for name, expected in (("guided_floor", 13), ("guided_cap", 10), ("guided_decline", None)):
            run = self.cli("--guided", text=(FIXTURES / (name + ".txt")).read_text())
            self.assertEqual((run.returncode, run.stderr), (0, ""))
            replies = results(run.stdout)
            self.assertEqual(replies[0]["result"], {"net_residual": 40})
            self.assertEqual(len(replies), 1 if expected is None else 2)
            if expected is not None:
                self.assertEqual(replies[1]["result"], {"budget_ceiling": expected})

    def test_exact_integer_transport_and_descriptive_periods(self):
        for periods in (1, 9):
            request = dict(BUDGET, arguments={"cap": MONEY_MAX, "ratio_numerator": MONEY_MAX - 1,
                           "ratio_denominator": MONEY_MAX, "net_residual": MONEY_MAX - 1,
                           "periods": periods})
            for args, text in ((("--request", "-"), json.dumps(request)),
                               (("--guided",), guided_request(request))):
                run = self.cli(*args, text=text)
                self.assertEqual((run.returncode, run.stderr), (0, ""))
                self.assertEqual(results(run.stdout)[0]["result"], {"budget_ceiling": 999999999998})
        large = 2**53 + 1
        request = dict(BUDGET, arguments=dict(BUDGET["arguments"], cap=large))
        with patch.object(sys, "stdin", io.StringIO(json.dumps(request))), \
                patch.object(sys, "stdout", io.StringIO()), patch.object(sys, "stderr", io.StringIO()), \
                patch.object(workbench, "dispatch_request", wraps=workbench.dispatch_request) as dispatch:
            self.assertEqual(workbench.main(["--request", "-"]), 1)
        self.assertEqual(dispatch.call_args.args[0]["arguments"]["cap"], large)
        self.assertIs(type(dispatch.call_args.args[0]["arguments"]["cap"]), int)

    def test_cli_preserves_original_error_codes(self):
        requests = [dict(BUDGET, arguments=dict(BUDGET["arguments"], **change))
                    for change in ({"cap": True}, {"cap": 2**53 + 1}, {"ratio_denominator": 0},
                                   {"periods": 0}, {"cap": 1, "ratio_numerator": MONEY_MAX,
                                                    "net_residual": MONEY_MAX, "ratio_denominator": 1})]
        requests += [dict(RESIDUAL, arguments=dict(RESIDUAL["arguments"], **change))
                     for change in ({"refundable_window_revenue": 101}, {"operating_cost": 100})]
        for request in requests:
            with self.assertRaises(TokenRewardError) as direct:
                workbench.dispatch_request(request)
            for args, text in ((("--request", "-"), json.dumps(request)),
                               (("--guided",), guided_request(request))):
                run = self.cli(*args, text=text)
                self.assertEqual(run.returncode, 1)
                self.assertEqual(results(run.stdout), [])
                self.assertEqual(decode_json(run.stderr)["error"], {"code": direct.exception.code})

    def test_malformed_json_missing_fields_and_multiple_documents(self):
        documents = ["", "{", "{}", "[]", "null", json.dumps(BUDGET) + json.dumps(BUDGET),
                     '{"operation":"reward_budget","operation":"reward_budget","arguments":{}}',
                     '{"operation":"reward_budget","arguments":{"cap":1,"cap":2}}',
                     '{"operation":"reward_budget","arguments":{"cap":NaN}}',
                     '{"operation":"reward_budget","arguments":{"cap":Infinity}}',
                     '{"operation":"reward_budget","arguments":{"cap":1e9999}}',
                     '{"operation":"\\ud800","arguments":{}}']
        for request in (BUDGET, RESIDUAL):
            for field in request["arguments"]:
                missing = copy.deepcopy(request)
                del missing["arguments"][field]
                documents.append(json.dumps(missing))
        documents.append(json.dumps(dict(BUDGET, operation="submit")))
        for document in documents:
            with self.subTest(document=document):
                run = self.cli("--request", "-", text=document)
                self.assertEqual((run.returncode, run.stdout), (2, ""))
                self.assertEqual(decode_json(run.stderr)["error"]["type"], "FixtureError")

    def test_io_failure_eof_and_mutually_exclusive_modes(self):
        run = self.cli("--request", FIXTURES / "does-not-exist.json")
        self.assertEqual((run.returncode, run.stdout), (2, ""))
        self.assertEqual(decode_json(run.stderr)["error"]["type"], "FileNotFoundError")
        run = self.cli("--guided", text="")
        self.assertEqual(run.returncode, 2)
        self.assertIn("EOF", run.stderr)
        for args in ((), ("--guided", "--request", "-")):
            run = self.cli(*args, text="")
            self.assertEqual((run.returncode, run.stdout), (2, ""))


if __name__ == "__main__":
    unittest.main()
