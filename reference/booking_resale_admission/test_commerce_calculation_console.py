"""Consent, snapshot dependency and terminal composition, using the real driver."""

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from commerce_calculation_client import CommerceCalculationClient, CalculationUncertainty, codec, decode_input
from commerce_calculation_console import run_console
from test_commerce_calculation_client import HERE, POPEN


FIXTURES = HERE / 'fixtures'
PREFIX = 'reference/booking_resale_admission/fixtures/commerce_console_'


def answers(name='journey'):
    return (FIXTURES / ('commerce_console_' + name + '.txt')).read_text()


def compose(legs):
    rows = ['compose_legs', str(len(legs))]
    for leg in legs:
        asset = leg['amount']['asset']
        rows.extend([leg['legId'], leg['providerRef'], leg['routeRef'], asset['namespace'],
                     asset['reference'], str(asset['decimals']), asset['maxAtoms'], leg['amount']['atoms']])
    return '\n'.join(rows) + '\n'


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

    def test_guided_split_refund_journey_and_file_parity(self):
        for name in ('journey', 'free', 'precision'):
            with self.subTest(name=name), patch('time.time', side_effect=AssertionError('no implicit clock')):
                status, guided, output, errors = self.run_journey(answers('guided_' + name))
                fstatus, loaded, _, ferrors = self.run_journey(answers(name))
                self.assertEqual((status, errors, fstatus, ferrors), (0, '', 0, ''))
                self.assertEqual(len(guided.exchanges), 3)
                # Includes complete requests, replies, plan hashes and refund outputs.
                self.assertEqual(guided.exchanges, loaded.exchanges)
                legs = decode_input(guided.exchanges[1].request_bytes)['args']['legs']
                preview = 'composed_legs=' + codec().canonical(legs)
                self.assertIn(preview, output)
                self.assertLess(output.index(preview), output.index('proposed={"action":"plan_payments"'))
                self.assertLess(output.index(preview), output.index('Type literal SUBMIT_PLAN'))
                refund = guided.history[-1].response['result']
                if name == 'journey':
                    self.assertEqual([leg['legId'] for leg in legs], ['card', 'bank'])
                    self.assertEqual(refund['lineIds'], ['L2'])
                elif name == 'free':
                    self.assertEqual(legs, [])
                    self.assertEqual(refund['originalRoutes'], [])
                else:
                    self.assertEqual(legs[0]['amount']['atoms'], '9007199254740993')
                    self.assertEqual(refund['customerRefund']['atoms'], '9007199254740993')

    def test_guided_driver_refusals_are_visible_without_correction_or_retry(self):
        status, client, output, errors = self.run_journey(answers('guided_boundaries'))
        self.assertEqual((status, errors, len(client.exchanges)), (1, '', 5))
        expected = ['DUPLICATE_PAYMENT_LEG', 'PAYMENT_ASSET_MISMATCH',
                    'PAYMENT_TOTAL_MISMATCH', 'QUOTE_EXPIRED']
        self.assertEqual([e.response['error'] for e in client.exchanges[1:]], expected)
        for error in expected:
            self.assertIn('"error":"' + error + '"', output)
        self.assertEqual(len(client.history), 1)
        # Zero count is explicit even on a paid quote: the driver refuses the total.
        prefix = answers('guided_journey').split('compose_legs\n')[0]
        status, client, output, errors = self.run_journey(prefix +
                    'compose_legs\n0\nplan_payments\n999\nSUBMIT_PLAN\nquit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (1, '', 2))
        self.assertEqual(client.exchanges[-1].response['error'], 'PAYMENT_TOTAL_MISMATCH')

    def test_guided_replacement_invalidates_plan_refund_and_selection(self):
        prefix = answers('guided_journey').split('show\n')[0]
        same = answers('guided_journey').split('compose_legs\n')[1].split('plan_payments\n')[0]
        cases = [('compose_legs\n' + same, 0, True),
                 ('compose_legs\ntrue\n', 1, False),
                 ('compose_legs\n1\nnew\nprovider\nroute\nfiat\nKRW\n1.5\n', 1, False),
                 ('compose_legs\n1\ne\u0301\np\nr\nfiat\nKRW\n0\n100\n1\n', 1, False)]
        for replacement, expected, complete in cases:
            with self.subTest(replacement=replacement):
                status, client, output, errors = self.run_journey(prefix + replacement +
                    'propose_line_refund\nshow\nplan_payments\n' +
                    ('999\nSUBMIT_PLAN\npropose_line_refund\n' if complete else '') + 'quit\n')
                self.assertEqual((status, errors), (expected, ''))
                self.assertEqual(len(client.exchanges), 4 if complete else 3)
                self.assertIn('active={"plan":null,"quote":"', output)
                self.assertIn('"refund":null}', output)
                self.assertIn('Active quote, plan and explicit line selection are required.', output)
                if not complete:
                    self.assertIn('A successful active quote and loaded legs are required.', output)
                self.assertIn('Historical successful exchanges (not active selections)', output)

        status, client, output, errors = self.run_journey(answers('guided_replacement'))
        self.assertEqual((status, errors, len(client.exchanges)), (0, '', 4))
        self.assertEqual(output.count('Active quote, plan and explicit line selection are required.'), 2)

    def test_guided_integer_and_encoding_failures_never_publish_candidate(self):
        invalid_count = ('', '-1', '17', 'true', '"1"', '1.0', '1e0', '-0', '9007199254740993', '{}')
        for count in invalid_count:
            with self.subTest(count=count), patch('commerce_calculation_client.subprocess.Popen') as launch:
                status, _, output, errors = self.run_journey('compose_legs\n' + count +
                                                            '\nplan_payments\nquit\n')
                self.assertEqual((status, errors), (1, ''))
                self.assertIn('input_error=', output)
                self.assertNotIn('composed_legs=', output)
                launch.assert_not_called()
        for value in ('true', '"0"', '0.0', '-0', '9007199254740993', '\ud800'):
            with self.subTest(decimals=value):
                status, client, output, errors = self.run_journey(
                    'compose_legs\n1\nid\np\nr\nfiat\nKRW\n' + value + '\nquit\n')
                self.assertEqual((status, errors, len(client.exchanges)), (1, '', 0))
                self.assertNotIn('composed_legs=', output)
        for literal in ('e\u0301', '\ud800', 'x' * codec().MAX_INPUT_BYTES):
            script = 'compose_legs\n1\n' + literal + '\np\nr\nfiat\nKRW\n0\n100\n1\nquit\n'
            status, client, output, errors = self.run_journey(script)
            self.assertEqual((status, errors, len(client.exchanges)), (1, '', 0))
            self.assertIn('input_error=', output)
            self.assertNotIn('composed_legs=', output)

    def test_guided_literal_strings_order_and_driver_owned_validation(self):
        legs = json.loads((FIXTURES / 'commerce_console_legs.json').read_text())[::-1]
        legs[0]['providerRef'] = ' synthetic provider '
        legs[0]['routeRef'] = ''
        legs[0]['amount']['asset']['decimals'] = -1
        legs[0]['amount']['asset']['maxAtoms'] = ' 000100 '
        legs[0]['amount']['atoms'] = '00018600'
        prefix = answers('guided_journey').split('compose_legs\n')[0]
        status, client, output, errors = self.run_journey(prefix + compose(legs) +
                                                       'plan_payments\n999\nSUBMIT_PLAN\nquit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (1, '', 2))
        self.assertEqual(decode_input(client.exchanges[-1].request_bytes)['args']['legs'], legs)
        self.assertIn('composed_legs=' + codec().canonical(legs), output)
        self.assertFalse(client.exchanges[-1].response['ok'])
        # CRLF removes only terminators; quotes, spaces, empty text and atom spellings survive.
        with patch('commerce_calculation_client.subprocess.Popen') as launch:
            status, _, output, errors = self.run_journey(compose(legs).replace('\n', '\r\n') + 'quit\n')
        self.assertEqual((status, errors), (0, ''))
        self.assertIn('composed_legs=' + codec().canonical(legs), output)
        launch.assert_not_called()

    def test_guided_eof_at_every_prompt_and_decline_submit_nothing_further(self):
        script = answers('guided_journey')
        composition = script.split('compose_legs\n')[1].split('plan_payments\n')[0]
        prefix = script.split('compose_legs\n')[0]
        # Also enter replacement after a successful refund; partial EOF keeps history only.
        for initial, calls in ((prefix, 1), (script.split('show\n')[0], 3)):
            for length in range(len(composition.splitlines()) + 1):
                with self.subTest(calls=calls, length=length):
                    partial = '\n'.join(composition.splitlines()[:length])
                    status, client, output, errors = self.run_journey(initial + 'compose_legs\n' +
                                                                      partial + ('\n' if length else ''))
                    self.assertEqual((status, errors, len(client.exchanges)), (0, '', calls))
                    self.assertIn('EOF; no further calculations submitted.', output)
        for suffix in ('no\npropose_line_refund\nquit\n', ''):
            status, client, _, errors = self.run_journey(script.split('SUBMIT_PLAN\n')[0] + suffix)
            self.assertEqual((status, errors, len(client.exchanges)), (0, '', 1))
        self.assertEqual(self.run_journey(answers('guided_decline'))[0], 0)

    def test_guided_plan_uncertainty_fences_after_successful_quote(self):
        children = []
        def fail_plan(*args, **kwargs):
            if not children:
                child = POPEN(*args, **kwargs)
            else:
                child = POPEN([sys.executable, '-B', '-c',
                               'import sys; sys.stdin.buffer.read(); print("malformed")'], **kwargs)
            children.append(child)
            return child
        with patch('commerce_calculation_client.subprocess.Popen', side_effect=fail_plan) as launch:
            status, client, _, errors = self.run_journey(answers('guided_journey') * 2)
            self.assertEqual((status, launch.call_count, len(client.history)), (2, 2, 1))
            self.assertIsInstance(client.uncertainty, CalculationUncertainty)
            self.assertEqual(decode_input(client.uncertainty.request_bytes)['action'], 'plan_payments')
            with self.assertRaisesRegex(RuntimeError, 'client fenced'):
                client.request({'action': 'simulate_quote', 'args': {}})
            self.assertEqual(launch.call_count, 2)
        self.assertIn('FENCED', errors)
        self.assertTrue(all(child.returncode is not None for child in children))

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
