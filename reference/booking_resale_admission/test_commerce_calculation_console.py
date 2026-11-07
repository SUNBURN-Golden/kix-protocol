"""Consent, snapshot dependency and terminal composition, using the real driver."""

import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from commerce_calculation_client import CommerceCalculationClient, CalculationUncertainty, decode_input
from commerce_calculation_console import run_console
from test_commerce_calculation_client import HERE, POPEN


FIXTURES = HERE / 'fixtures'
PREFIX = 'reference/booking_resale_admission/fixtures/commerce_console_'


def answers(name='journey'):
    return (FIXTURES / ('commerce_console_' + name + '.txt')).read_text()


class RecordingClient(CommerceCalculationClient):
    def __init__(self):
        super().__init__(cleanup_timeout=1)
        self.exchanges = []

    def request(self, envelope):
        exchange = super().request(envelope)
        self.exchanges.append(exchange)
        return exchange


class CommerceCalculationConsoleTests(unittest.TestCase):
    def run_journey(self, script, *, client=None, output=None):
        client = client or RecordingClient()
        output = output or io.StringIO()
        errors = io.StringIO()
        status = run_console(client, input_stream=io.StringIO(script), output_stream=output, error_stream=errors)
        return status, client, output.getvalue(), errors.getvalue()

    def test_real_driver_journey_retains_exact_quote_and_plan_for_next_request(self):
        with patch('time.time', side_effect=AssertionError('no implicit business clock')):
            status, client, output, errors = self.run_journey(answers())
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(len(client.history), 3)
        q, p, r = [e.response['result'] for e in client.history]
        preq = decode_input(client.history[1].request_bytes)
        rreq = decode_input(client.history[2].request_bytes)
        self.assertEqual(preq['args']['quote'], q)
        self.assertEqual(preq['args']['expected_quote_hash'], q['quoteHash'])
        self.assertEqual(rreq['args']['quote'], q)
        self.assertEqual(rreq['args']['payment_plan'], p)
        self.assertEqual(rreq['args']['expected_plan_hash'], p['planHash'])
        for exchange in client.history:
            self.assertIn(exchange.reply_bytes.decode().strip(), output)
        self.assertIn('"executionAuthorized":false', output)
        for route in r['originalRoutes']:
            self.assertIn(route['routeRef'], output)
        self.assertNotIn('executionAuthorized', q)
        self.assertNotIn('executionAuthorized', p)

    def test_each_submission_decline_and_eof_send_nothing_further(self):
        script = answers()
        for index, literal in enumerate(('SUBMIT_QUOTE', 'SUBMIT_PLAN', 'SUBMIT_REFUND')):
            prefix = script.split(literal + '\n')[0]
            for suffix in ('no\nquit\n', ''):
                with self.subTest(literal=literal, suffix=suffix):
                    status, client, _, errors = self.run_journey(prefix + suffix)
                    self.assertEqual((status, errors), (0, ''))
                    self.assertEqual(len(client.history), index)
        for script in ('', 'quit\n', answers('decline'),
                       'load_quote\n' + PREFIX + 'quote.json\nload_legs\n' + PREFIX +
                       'legs.json\nselect_lines\n["L2"]\nshow\nquit\n'):
            with self.subTest(script=script), patch('commerce_calculation_client.subprocess.Popen') as launch:
                self.assertEqual(self.run_journey(script)[0], 0)
                launch.assert_not_called()

    def test_quote_replacement_identical_failed_and_declined_invalidate_dependents(self):
        prefix = answers().split('show\n')[0]
        for replacement, expected_status in (
                ('load_quote\n' + PREFIX + 'quote.json\n', 0),
                ('load_quote\n/does/not/exist\n', 1),
                ('simulate_quote\nno\n', 0)):
            status, client, output, errors = self.run_journey(prefix + replacement +
                        'propose_line_refund\nshow\nquit\n')
            self.assertEqual((status, errors), (expected_status, ''))
            self.assertEqual(len(client.history), 3)
            self.assertIn('active={"plan":null,"quote":null,"refund":null}', output)
            self.assertIn('Historical successful exchanges (not active selections)', output)
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / 'bad.json'; bad.write_text('{}')
            script = prefix + 'load_quote\n' + str(bad) + '\nsimulate_quote\nSUBMIT_QUOTE\n'
            status, client, output, errors = self.run_journey(script + 'propose_line_refund\nshow\nquit\n')
            self.assertEqual((status, errors), (1, ''))
            self.assertEqual(len(client.history), 3)
            self.assertEqual(len(client.exchanges), 4)
            self.assertFalse(client.exchanges[-1].response['ok'])
            self.assertIn('active={"plan":null,"quote":null,"refund":null}', output)

    def test_legs_and_plan_input_changes_invalidate_plan_and_line_selection(self):
        prefix = answers().split('show\n')[0]
        changes = [('load_legs\n' + PREFIX + 'legs.json\n', 0, 3),
                   ('load_legs\n/does/not/exist\n', 1, 3),
                   ('plan_payments\n999\nno\n', 0, 3),
                   ('plan_payments\n1000\nSUBMIT_PLAN\n', 1, 4),
                   ('plan_payments\n-0\n', 1, 3)]
        for change, expected, calls in changes:
            with self.subTest(change=change):
                status, client, output, errors = self.run_journey(prefix + change +
                                    'propose_line_refund\nshow\nquit\n')
                self.assertEqual((status, errors), (expected, ''))
                self.assertEqual(len(client.exchanges), calls)
                self.assertIn('Active quote, plan and explicit line selection are required.', output)
                self.assertIn('active={"plan":null,"quote":"', output)
        # A newly successful plan also clears the old selection.
        status, client, output, _ = self.run_journey(prefix +
                    'plan_payments\n999\nSUBMIT_PLAN\npropose_line_refund\nquit\n')
        self.assertEqual((status, len(client.exchanges)), (0, 4))
        self.assertIn('Active quote, plan and explicit line selection are required.', output)

    def test_changed_or_malformed_line_selection_cannot_reactivate_old_refund(self):
        prefix = answers().split('show\n')[0]
        status, client, output, errors = self.run_journey(prefix +
                    'select_lines\n["L1"]\npropose_line_refund\nSUBMIT_REFUND\nquit\n')
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(client.history[-1].response['result']['lineIds'], ['L1'])
        status, client, output, errors = self.run_journey(prefix +
                    'select_lines\n[1]\npropose_line_refund\nshow\nquit\n')
        self.assertEqual((status, errors), (1, ''))
        self.assertEqual(len(client.history), 3)
        self.assertIn('"refund":null', output)

    def test_invalid_original_json_never_promoted_or_submitted(self):
        for raw in (b'{"lines":[],"lines":[]}', b'{"expiresAt":9007199254740993}',
                    b'{"expiresAt":1.5}', b'{"expiresAt":-0}', b'[]', b'\xff', b'{'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'quote.json'; path.write_bytes(raw)
                with patch('commerce_calculation_client.subprocess.Popen') as launch:
                    status, _, _, errors = self.run_journey('load_quote\n' + str(path) +
                                      '\nsimulate_quote\nshow\nquit\n')
                self.assertEqual((status, errors), (1, ''))
                launch.assert_not_called()

    def test_free_and_large_atom_journeys_preserve_wire_strings_and_empty_routes(self):
        for name in ('free', 'precision'):
            with self.subTest(name=name):
                status, client, output, errors = self.run_journey(answers(name))
                self.assertEqual((status, errors), (0, ''))
                q, p, r = [e.response['result'] for e in client.history]
                atoms = q['request']['lines'][0]['gross']['atoms']
                self.assertIs(type(atoms), str)
                self.assertIn('"' + atoms + '"', output)
                if name == 'free':
                    self.assertEqual(p['legs'], [])
                    self.assertEqual(r['originalRoutes'], [])
                else:
                    self.assertEqual(atoms, '9007199254740993')
                    self.assertEqual(r['customerRefund']['atoms'], atoms)

    def test_known_refusals_require_explicit_correction_and_new_submission(self):
        status, client, output, errors = self.run_journey(answers('boundaries'))
        self.assertEqual((status, errors), (1, ''))
        self.assertEqual(len(client.exchanges), 5)
        self.assertEqual([exchange.response['error'] for exchange in client.exchanges if not exchange.response['ok']],
                         ['QUOTE_EXPIRED', 'PAYMENT_TOTAL_MISMATCH', 'UNKNOWN_REFUND_LINE'])
        self.assertEqual(len(client.history), 2)

    def test_transport_failure_stops_console_without_retry_or_fallback(self):
        children = []
        def fail(*args, **kwargs):
            child = POPEN([sys.executable, '-B', '-c',
                           'import sys; sys.stdin.buffer.read(); print("malformed")'], **kwargs)
            children.append(child)
            return child
        with patch('commerce_calculation_client.subprocess.Popen', side_effect=fail) as launch:
            status, client, output, errors = self.run_journey(answers() + answers())
        self.assertEqual(status, 2)
        self.assertEqual(launch.call_count, 1)
        self.assertIn('FENCED', errors)
        self.assertIn('malformed', errors)
        self.assertIsInstance(client.uncertainty, CalculationUncertainty)
        self.assertEqual(client.history, ())
        self.assertIsNotNone(children[0].returncode)

    def test_output_failure_retains_received_success_and_stops(self):
        class BrokenOutput(io.StringIO):
            def write(self, text):
                if text.startswith('driver='):
                    raise OSError('output unavailable')
                return super().write(text)
        status, client, _, errors = self.run_journey(answers(), output=BrokenOutput())
        self.assertEqual((status, len(client.history)), (2, 1))
        self.assertIn('output unavailable', errors)
        self.assertIsNotNone(client.last_exchange)

    def test_cli_journey_and_cleanup_budget_usage_errors(self):
        command = [sys.executable, '-B', str(HERE / 'commerce_calculation_console.py'), '--cleanup-timeout']
        result = subprocess.run(command + ['1'], input=answers(), text=True, capture_output=True,
                                cwd=HERE.parents[1])
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertIn('"executionAuthorized":false', result.stdout)
        for value in ('0', '-1', 'nan', 'inf'):
            result = subprocess.run(command + [value], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
