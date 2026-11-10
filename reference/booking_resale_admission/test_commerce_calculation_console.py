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
from calculated_booking_quote_source import _calculator
from test_commerce_calculation_client import HERE, POPEN


FIXTURES = HERE / 'fixtures'
PREFIX = 'reference/booking_resale_admission/fixtures/commerce_console_'


def answers(name='journey'):
    return (FIXTURES / ('commerce_console_' + name + '.txt')).read_text()


def decimal_text(amount):
    """Format fixture integers without floats or invoking the conversion under test."""
    places = amount['asset']['decimals']
    digits = amount['atoms'].zfill(places + 1)
    return digits[:-places] + '.' + digits[-places:] if places else digits


def compose(legs, decimal_entry=False):
    rows = ['compose_legs_decimal' if decimal_entry else 'compose_legs', str(len(legs))]
    for leg in legs:
        asset = leg['amount']['asset']
        rows.extend([leg['legId'], leg['providerRef'], leg['routeRef'], asset['namespace'],
                     asset['reference'], str(asset['decimals']), asset['maxAtoms'],
                     decimal_text(leg['amount']) if decimal_entry else leg['amount']['atoms']])
    return '\n'.join(rows) + '\n'


def compose_quote(request, decimal_entry=False):
    rows = ['compose_quote_decimal' if decimal_entry else 'compose_quote',
            request['orderId'], str(request['orderVersion'])]
    rows.extend(request['scope'][field] for field in ('issuerId', 'eventId', 'performanceId'))
    rows.extend([request['policyRef'], str(request['expiresAt']), str(len(request['lines']))])
    for line in request['lines']:
        asset = line['gross']['asset']
        rows.extend([line['lineId'], line['inventoryId'], asset['namespace'], asset['reference'],
                     str(asset['decimals']), asset['maxAtoms'],
                     decimal_text(line['gross']) if decimal_entry else line['gross']['atoms']])
    rows.append(str(len(request['discounts'])))
    for rule in request['discounts']:
        rows.extend([rule['ruleId'], rule['bearerRef'], rule['kind'], rule['value'],
                     json.dumps(rule['eligibleLineIds']), json.dumps(rule['capAtoms'])])
    return '\n'.join(rows) + '\n'


def quote_fixture(name='quote'):
    return json.loads((FIXTURES / ('commerce_console_' + name + '.json')).read_text())


def decimal_inputs(name='journey'):
    quote = quote_fixture('quote' if name == 'journey' else name + '_quote')
    legs = quote_fixture('legs' if name == 'journey' else name + '_legs')
    for amount in ([line['gross'] for line in quote['lines']] + [leg['amount'] for leg in legs]):
        amount['asset'].update(namespace='fixture', reference='local:decimal-unit',
                               decimals=6 if name == 'precision' else 2)
    return quote, legs


def decimal_journey(name='journey', quote_decimal=True, legs_decimal=True):
    quote, legs = decimal_inputs(name)
    ids = ['L2'] if name == 'journey' else ['L1']
    return (compose_quote(quote, quote_decimal) + 'simulate_quote\nSUBMIT_QUOTE\n' +
            compose(legs, legs_decimal) + 'plan_payments\n999\nSUBMIT_PLAN\n' + pick(ids) +
            'propose_line_refund\nSUBMIT_REFUND\nshow\nquit\n')


def pick(ids):
    return 'pick_lines\n' + str(len(ids)) + '\n' + ''.join(value + '\n' for value in ids)


def json_selection(script):
    """Equivalent explicit JSON selection for a synthetic picker transcript."""
    rows = iter(script.splitlines())
    result = []
    for row in rows:
        if row == 'pick_lines':
            ids = [next(rows) for _ in range(int(next(rows)))]
            result.extend(['select_lines', json.dumps(ids)])
        else:
            result.append(row)
    return '\n'.join(result) + '\n'


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

    def test_bundle_journey_file_parity(self):
        commerce = _calculator()['commerce']
        # These entry points must only run in calculator children, never composition/client code.
        with patch.object(commerce, 'build_quote', side_effect=AssertionError('in-process calculation')), \
             patch.object(commerce, 'plan_payments', side_effect=AssertionError('in-process calculation')), \
             patch.object(commerce, 'propose_line_refund', side_effect=AssertionError('in-process calculation')), \
             patch('time.time', side_effect=AssertionError('implicit clock')):
            for name in ('journey', 'precision', 'free'):
                with self.subTest(name=name), \
                     patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                    status, guided, output, errors = self.run_journey(answers('bundle_' + name))
                    self.assertEqual(launch.call_count, 3)
                    fstatus, loaded, _, ferrors = self.run_journey(answers(name))
                    self.assertEqual((status, errors, fstatus, ferrors), (0, '', 0, ''))
                    self.assertEqual(guided.exchanges, loaded.exchanges)
                    request = decode_input(guided.exchanges[0].request_bytes)['args']
                    preview = 'composed_quote=' + codec().canonical(request)
                    self.assertIn(preview, output)
                    self.assertLess(output.index(preview), output.index('Type literal SUBMIT_QUOTE'))
                    for exchange in guided.exchanges:
                        self.assertEqual(exchange.response['result']['evidenceClass'], 'CALCULATION_ONLY')
                    self.assertIs(guided.exchanges[-1].response['result']['executionAuthorized'], False)
                    if name == 'precision':
                        self.assertEqual(request['lines'][0]['gross']['atoms'], '9007199254740993')
                    if name == 'free':
                        self.assertEqual(request['discounts'], [])
                        self.assertEqual(guided.exchanges[-1].response['result']['originalRoutes'], [])

    def test_bundle_driver_refusals_preserve_input_and_dispatch_once(self):
        mutations = [
            ('DUPLICATE_LINE', lambda q: q['lines'][1].update(lineId='L1')),
            ('DUPLICATE_INVENTORY', lambda q: q['lines'][1].update(inventoryId='inv-1')),
            ('DUPLICATE_DISCOUNT_RULE', lambda q: q['discounts'][1].update(ruleId='coupon')),
            ('DUPLICATE_ID', lambda q: q['discounts'][0].update(eligibleLineIds=['L1', 'L1'])),
            ('UNKNOWN_DISCOUNT_LINE', lambda q: q['discounts'][0].update(eligibleLineIds=['missing'])),
            ('MIXED_QUOTE_ASSETS', lambda q: q['lines'][1]['gross']['asset'].update(reference='USD')),
            ('DISCOUNT_EXCEEDS_PAYABLE', lambda q: q['discounts'][0].update(value='60001')),
        ]
        for expected, mutate in mutations:
            request = quote_fixture(); mutate(request)
            with self.subTest(error=expected), \
                 patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                status, client, output, errors = self.run_journey(compose_quote(request) +
                                                  'simulate_quote\nSUBMIT_QUOTE\nshow\nquit\n')
                self.assertEqual((status, errors, launch.call_count), (1, '', 1))
                self.assertEqual(len(client.exchanges), 1)
                self.assertEqual(decode_input(client.exchanges[0].request_bytes)['args'], request)
                self.assertEqual(client.exchanges[0].response['error'], expected)
                self.assertIn('"error":"' + expected + '"', output)
                self.assertEqual(client.history, ())
        status, client, _, errors = self.run_journey(answers('bundle_boundaries'))
        self.assertEqual((status, errors), (1, ''))
        self.assertEqual([e.response['error'] for e in client.exchanges], [m[0] for m in mutations])

    def test_bundle_literal_strings_caps_and_array_order(self):
        request = quote_fixture()
        request['lines'].reverse()
        request['discounts'].reverse()
        request['discounts'][0]['eligibleLineIds'].reverse()
        request['discounts'][0]['capAtoms'] = '1234'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'quote.json'; path.write_text(json.dumps(request))
            suffix = 'simulate_quote\nSUBMIT_QUOTE\nquit\n'
            status, guided, _, errors = self.run_journey(compose_quote(request) + suffix)
            fstatus, loaded, _, ferrors = self.run_journey('load_quote\n' + str(path) + '\n' + suffix)
        self.assertEqual((status, errors, fstatus, ferrors), (0, '', 0, ''))
        self.assertEqual(guided.exchanges, loaded.exchanges)
        self.assertEqual(decode_input(guided.exchanges[0].request_bytes)['args'], request)
        request['orderId'] = ' synthetic "order" '
        request['policyRef'] = ''
        request['lines'][0]['gross']['atoms'] = '00030000'
        request['lines'][0]['gross']['asset']['maxAtoms'] = ' 00100 '
        request['lines'][0]['gross']['asset']['decimals'] = -1
        request['discounts'][0]['kind'] = 'bps'
        request['discounts'][0]['value'] = ' 01000 '
        request['discounts'][0]['capAtoms'] = ''
        with patch('commerce_calculation_client.subprocess.Popen') as launch:
            status, _, output, errors = self.run_journey(compose_quote(request).replace('\n', '\r\n') + 'quit\n')
        self.assertEqual((status, errors), (0, ''))
        self.assertIn('composed_quote=' + codec().canonical(request), output)
        launch.assert_not_called()

    def test_bundle_integer_json_and_encoding_failures_never_publish(self):
        rows = compose_quote(quote_fixture('precision_quote')).splitlines()
        invalid = ('', 'true', '"1"', '1.0', '1e0', '-0', '9007199254740993', '{}', '\ud800')
        cases = []
        for index in (2, 7, 8, 13, 16):
            for value in invalid:
                cases.append(rows[:index] + [value])
        for index, values in ((8, ('-1', '0', '301')), (16, ('-1', '65'))):
            cases.extend(rows[:index] + [value] for value in values)
        discount_rows = compose_quote(quote_fixture()).splitlines()
        # Eligibility/cap are typed JSON; duplicates and membership are left to the driver.
        for index, values in ((35, ('', 'null', '{}', '[1]', '"L1"', '["L1",]')),
                              (36, ('', '0', 'false', '[]', '{}', '"unterminated'))):
            cases.extend(discount_rows[:index] + [value] for value in values)
        for literal in ('e\u0301', '\ud800', 'x' * codec().MAX_INPUT_BYTES):
            cases.append(rows[:1] + [literal] + rows[2:])
        for rows in cases:
            with self.subTest(prefix=repr(rows)[:160]), \
                 patch('commerce_calculation_client.subprocess.Popen') as launch:
                status, _, output, errors = self.run_journey('\n'.join(rows) +
                                                     '\nsimulate_quote\nshow\nquit\n')
                self.assertEqual((status, errors), (1, ''))
                self.assertNotIn('composed_quote=', output)
                self.assertIn('input_error=', output)
                self.assertIn('Load a quote request first.', output)
                launch.assert_not_called()

    def test_bundle_replacement_clears_input_quote_and_dependents(self):
        prefix = answers('bundle_journey').rsplit('\nshow\n', 1)[0] + '\n'
        same = compose_quote(quote_fixture())
        malformed = [same.splitlines()[:index] + [value] for index, value in
                     ((2, 'true'), (35, '[1]'), (36, '0'), (1, 'e\u0301'))]
        # For encoding failure, supply the rest of the candidate too.
        malformed[-1] += same.splitlines()[2:]
        replacements = [(same, 0)] + [('\n'.join(rows) + '\n', 1) for rows in malformed]
        for replacement, expected in replacements:
            with self.subTest(replacement=replacement):
                status, client, output, errors = self.run_journey(prefix + replacement +
                    ('simulate_quote\n' if expected else '') +
                    'propose_line_refund\nplan_payments\nshow\nquit\n')
                self.assertEqual((status, errors, len(client.exchanges)), (expected, '', 3))
                self.assertIn('active={"plan":null,"quote":null,"refund":null}', output)
                self.assertIn('Active quote, plan and explicit line selection are required.', output)
                self.assertIn('A successful active quote and loaded legs are required.', output)
                if expected:
                    self.assertIn('Load a quote request first.', output)
        # Re-simulation and re-planning can reuse stored legs, but never old line selection.
        status, client, output, errors = self.run_journey(prefix + same +
            'simulate_quote\nSUBMIT_QUOTE\nplan_payments\n999\nSUBMIT_PLAN\npropose_line_refund\nquit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (0, '', 5))
        self.assertIn('Active quote, plan and explicit line selection are required.', output)
        refused = quote_fixture(); refused['lines'][1]['lineId'] = 'L1'
        status, client, output, errors = self.run_journey(prefix + compose_quote(refused) +
            'simulate_quote\nSUBMIT_QUOTE\npropose_line_refund\nshow\nquit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (1, '', 4))
        self.assertIn('active={"plan":null,"quote":null,"refund":null}', output)
        self.assertIn('Historical successful exchanges (not active selections)', output)
        self.assertEqual(self.run_journey(answers('bundle_replacement'))[0], 0)

    def test_bundle_eof_decline_and_each_confirmation_launch_counts(self):
        composition = compose_quote(quote_fixture()).splitlines()
        # EOF at every quote prompt, initially and while replacing all active dependents.
        for prefix, calls in (('', 0), (answers('bundle_journey').rsplit('\nshow\n', 1)[0] + '\n', 3)):
            for length in range(1, len(composition) + 1):
                with self.subTest(calls=calls, length=length), \
                     patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                    status, client, output, errors = self.run_journey(prefix +
                        '\n'.join(composition[:length]) + '\n')
                    self.assertEqual((status, errors, launch.call_count), (0, '', calls))
                    self.assertEqual(len(client.exchanges), calls)
                    self.assertIn('EOF; no further calculations submitted.', output)
                    self.assertEqual(output.count('composed_quote='),
                                     int(bool(prefix)) + int(length == len(composition)))
        script = answers('bundle_journey')
        for index, literal in enumerate(('SUBMIT_QUOTE', 'SUBMIT_PLAN', 'SUBMIT_REFUND')):
            for suffix in ('no\nquit\n', ''):
                with self.subTest(literal=literal, suffix=suffix), \
                     patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                    status, client, _, errors = self.run_journey(script.split(literal + '\n')[0] + suffix)
                    self.assertEqual((status, errors, launch.call_count), (0, '', index))
                    self.assertEqual(len(client.exchanges), index)
        with patch('commerce_calculation_client.subprocess.Popen') as launch:
            self.assertEqual(self.run_journey(answers('bundle_decline'))[0], 0)
            launch.assert_not_called()

    def test_decimal_journey_atom_parity(self):
        commerce = _calculator()['commerce']
        with patch.object(commerce, 'build_quote', side_effect=AssertionError('in-process calculation')), \
             patch.object(commerce, 'plan_payments', side_effect=AssertionError('in-process calculation')), \
             patch.object(commerce, 'propose_line_refund', side_effect=AssertionError('in-process calculation')), \
             patch('time.time', side_effect=AssertionError('implicit clock')):
            for name in ('journey', 'precision', 'free'):
                status, atom, _, errors = self.run_journey(decimal_journey(name, False, False))
                self.assertEqual((status, errors), (0, ''))
                for quote_decimal, legs_decimal in ((True, True), (True, False), (False, True)):
                    with self.subTest(name=name, quote=quote_decimal, legs=legs_decimal), \
                         patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                        status, client, output, errors = self.run_journey(
                            decimal_journey(name, quote_decimal, legs_decimal))
                        self.assertEqual((status, errors, launch.call_count), (0, '', 3))
                        # Frozen request/reply bytes include every result and all three hashes.
                        self.assertEqual(client.exchanges, atom.exchanges)
                        quote, legs = decimal_inputs(name)
                        amounts = []
                        if quote_decimal:
                            amounts += [('lines[' + str(i) + '].gross', line['gross'], 'SUBMIT_QUOTE')
                                        for i, line in enumerate(quote['lines'])]
                        if legs_decimal:
                            amounts += [('legs[' + str(i) + '].amount', leg['amount'], 'SUBMIT_PLAN')
                                        for i, leg in enumerate(legs)]
                        self.assertEqual(output.count('decimal_conversion='), len(amounts))
                        for field, amount, literal in amounts:
                            preview = 'decimal_conversion=' + codec().canonical(
                                dict(field=field, decimalInput=decimal_text(amount), **amount))
                            self.assertIn(preview, output)
                            composed = 'composed_quote=' if field.startswith('lines') else 'composed_legs='
                            self.assertLess(output.index(preview), output.index(composed))
                            self.assertLess(output.index(preview), output.index('Type literal ' + literal))
                        self.assertEqual(decode_input(client.exchanges[0].request_bytes)['args']['discounts'],
                                         quote['discounts'])
                        self.assertTrue(all(e.response['result']['evidenceClass'] == 'CALCULATION_ONLY'
                                            for e in client.exchanges))
                        self.assertIs(client.exchanges[-1].response['result']['executionAuthorized'], False)
                        if name == 'precision' and quote_decimal:
                            self.assertIn('"decimalInput":"9007199254.740993"', output)
                        if name == 'free':
                            self.assertEqual(client.exchanges[-1].response['result']['originalRoutes'], [])
                self.assertEqual(answers('decimal_' + name), decimal_journey(name))

    def test_decimal_precision_boundaries(self):
        maximum = str(2**128 - 1)
        for decimals in (0, 2, 6, 18, 38):
            for atoms in ('0', '1', '9007199254740993', maximum):
                quote, legs = decimal_inputs('precision')
                quote['lines'][0]['gross']['asset']['decimals'] = decimals
                quote['lines'][0]['gross']['atoms'] = atoms
                legs[0]['amount'] = json.loads(json.dumps(quote['lines'][0]['gross']))
                # A free quote uses an explicit zero leg count, never a zero payment leg.
                if atoms == '0':
                    legs = []
                def script(decimal):
                    return (compose_quote(quote, decimal) + 'simulate_quote\nSUBMIT_QUOTE\n' +
                            compose(legs, decimal) + 'plan_payments\n999\nSUBMIT_PLAN\n' +
                            pick(['L1']) + 'propose_line_refund\nSUBMIT_REFUND\nquit\n')
                with self.subTest(decimals=decimals, atoms=atoms):
                    status, client, _, errors = self.run_journey(script(True))
                    astatus, atom, _, aerrors = self.run_journey(script(False))
                    self.assertEqual((status, errors, astatus, aerrors), (0, '', 0, ''))
                    self.assertEqual(len(client.exchanges), 3)
                    self.assertEqual(client.exchanges, atom.exchanges)
                    self.assertEqual(client.exchanges[0].response['result']['totals']['payableAtoms'], atoms)
        # Within-precision trailing zeroes survive the conversion preview exactly; CRLF only is removed.
        script = compose_quote(decimal_inputs('precision')[0], True).replace('9007199254.740993', '1.200000')
        status, _, output, errors = self.run_journey((script + 'quit\n').replace('\n', '\r\n'))
        self.assertEqual((status, errors), (0, ''))
        self.assertIn('"decimalInput":"1.200000"', output)
        self.assertIn('"atoms":"1200000"', output)
        # The caller's limit can be lower than the parser's global u128 bound.
        quote, legs = decimal_inputs('precision')
        for amount in (quote['lines'][0]['gross'], legs[0]['amount']):
            amount['asset'].update(decimals=2, maxAtoms='100')
            amount['atoms'] = '100'
        for script, marker in ((compose_quote(quote, True), 'composed_quote='),
                               (compose(legs, True), 'composed_legs=')):
            status, _, output, errors = self.run_journey(script + 'quit\n')
            self.assertEqual((status, errors), (0, ''))
            self.assertIn(marker, output)
            with patch('commerce_calculation_client.subprocess.Popen') as launch:
                status, _, output, errors = self.run_journey(script.replace('1.00\n', '1.01\n') + 'quit\n')
                self.assertEqual((status, errors), (1, ''))
                self.assertNotIn(marker, output)
                self.assertNotIn('decimal_conversion=', output)
                launch.assert_not_called()

    def test_decimal_conversion_failures_publish_and_submit_nothing(self):
        quote, legs = decimal_inputs('precision')
        # Positions are the interface prompts, not private calculator layout.
        variants = [(compose_quote(quote, True).splitlines(), 'composed_quote=',
                     ((11, ('', 'Fiat', ' fixture')), (12, ('', 'bad reference')),
                      (13, ('', 'true', '"6"', '6.0', '6e0', '-1', '39')),
                      (14, ('', '0', '01', '1e3', ' 100', str(2**128))),
                      (15, ('', '1e6', '1E6', ' 1', '1 ', '+1', '-0', '.5', '01',
                            '1.0000000', str(2**128), 'NaN', '０', '1\t', '9' * 81)))),
                    (compose(legs, True).splitlines(), 'composed_legs=',
                     ((5, ('', 'Fiat')), (6, ('', 'bad reference')),
                      (7, ('', 'true', '"6"', '6.0', '-1', '39')),
                      (8, ('', '0', '01', str(2**128))),
                      (9, ('', '1e6', ' 1', '1 ', '1.0000000', str(2**128)))))]
        for rows, marker, fields in variants:
            for index, values in fields:
                for value in values:
                    with self.subTest(marker=marker, index=index, value=value), \
                         patch('commerce_calculation_client.subprocess.Popen') as launch:
                        status, client, output, errors = self.run_journey(
                            '\n'.join(rows[:index] + [value]) + '\nsimulate_quote\nshow\nquit\n')
                        self.assertEqual((status, errors), (1, ''))
                        self.assertIn('input_error=', output)
                        self.assertNotIn(marker, output)
                        self.assertNotIn('decimal_conversion=', output)
                        self.assertEqual(client.exchanges, [])
                        launch.assert_not_called()
        # No partial conversions escape if a later amount or final CE1 encoding fails.
        quote, legs = decimal_inputs()
        for compose_input, marker in ((compose_quote(quote, True), 'composed_quote='),
                                      (compose(legs, True), 'composed_legs=')):
            for bad in (compose_input.rsplit('186.00', 1)[0] + '1e6\n' if '186.00' in compose_input
                        else compose_input.replace('300.00', '1e6'),
                        compose_input.replace('synthetic-bundle', 'e\u0301').replace('original-card', 'e\u0301')):
                status, _, output, errors = self.run_journey(bad + 'quit\n')
                self.assertEqual((status, errors), (1, ''))
                self.assertNotIn(marker, output)
                self.assertNotIn('decimal_conversion=', output)

    def test_decimal_driver_refusals_remain_explicit_and_exact(self):
        cases = []
        for key, value in (('reference', 'local:other'), ('decimals', 6), ('maxAtoms', '999999')):
            quote, _ = decimal_inputs()
            quote['lines'][1]['gross']['asset'][key] = value
            cases.append((compose_quote(quote, True) + 'simulate_quote\nSUBMIT_QUOTE\n',
                          'MIXED_QUOTE_ASSETS' if key == 'reference' else 'ASSET_METADATA_CONFLICT', quote))
        quote, legs = decimal_inputs()
        for line in quote['lines']:
            line['gross']['asset']['maxAtoms'] = '30000'
        cases.append((compose_quote(quote, True) + 'simulate_quote\nSUBMIT_QUOTE\n',
                      'INVALID_ASSET_AMOUNT', quote))
        for key, value in (('reference', 'local:other'), ('decimals', 6), ('maxAtoms', '999999')):
            quote, legs = decimal_inputs()
            legs[0]['amount']['asset'][key] = value
            cases.append((compose_quote(quote, True) + 'simulate_quote\nSUBMIT_QUOTE\n' +
                          compose(legs, True) + 'plan_payments\n999\nSUBMIT_PLAN\n',
                          'PAYMENT_ASSET_MISMATCH', None))
        quote, legs = decimal_inputs('free')
        legs = decimal_inputs('precision')[1]
        legs[0]['amount'] = json.loads(json.dumps(quote['lines'][0]['gross']))
        cases.append((compose_quote(quote, True) + 'simulate_quote\nSUBMIT_QUOTE\n' +
                      compose(legs, True) + 'plan_payments\n999\nSUBMIT_PLAN\n',
                      'EMPTY_PAYMENT_LEG', None))
        for script, expected, request in cases:
            with self.subTest(expected=expected), \
                 patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                status, client, output, errors = self.run_journey(script + 'show\nquit\n')
                self.assertEqual((status, errors, launch.call_count), (1, '', 1 if request else 2))
                self.assertEqual(client.exchanges[-1].response['error'], expected)
                self.assertIn('decimal_conversion=', output)
                if request:
                    self.assertEqual(decode_input(client.exchanges[-1].request_bytes)['args'], request)
        status, client, _, errors = self.run_journey(answers('decimal_boundaries'))
        self.assertEqual((status, errors), (1, ''))
        self.assertEqual([e.response['error'] for e in client.exchanges if not e.response['ok']],
                         ['MIXED_QUOTE_ASSETS', 'INVALID_ASSET_AMOUNT', 'PAYMENT_ASSET_MISMATCH',
                          'EMPTY_PAYMENT_LEG'])

    def test_decimal_eof_decline_and_conversion_failure(self):
        quote, legs = decimal_inputs()
        for composition, marker in ((compose_quote(quote, True), 'composed_quote='),
                                    (compose(legs, True), 'composed_legs=')):
            rows = composition.splitlines()
            for length in range(1, len(rows)):
                with self.subTest(marker=marker, length=length), \
                     patch('commerce_calculation_client.subprocess.Popen') as launch:
                    status, _, output, errors = self.run_journey('\n'.join(rows[:length]) + '\n')
                    self.assertEqual((status, errors), (0, ''))
                    self.assertNotIn(marker, output)
                    self.assertNotIn('decimal_conversion=', output)
                    launch.assert_not_called()
        for index, literal in enumerate(('SUBMIT_QUOTE', 'SUBMIT_PLAN', 'SUBMIT_REFUND')):
            for suffix in ('no\nquit\n', ''):
                with self.subTest(literal=literal, suffix=suffix), \
                     patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                    status, client, _, errors = self.run_journey(
                        answers('decimal_journey').split(literal + '\n')[0] + suffix)
                    self.assertEqual((status, errors, launch.call_count), (0, '', index))
                    self.assertEqual(len(client.exchanges), index)
        with patch('commerce_calculation_client.subprocess.Popen') as launch:
            self.assertEqual(self.run_journey(answers('decimal_decline'))[0], 0)
            launch.assert_not_called()

    def test_decimal_replacement_invalidates_dependents(self):
        for prefix_name, decimal_entry in (('bundle_journey', True), ('decimal_journey', False),
                                           ('decimal_journey', True)):
            prefix = answers(prefix_name).rsplit('\nshow\n', 1)[0] + '\n'
            quote, legs = decimal_inputs() if prefix_name == 'decimal_journey' else (quote_fixture(), quote_fixture('legs'))
            for kind in ('quote', 'legs'):
                same = compose_quote(quote, decimal_entry) if kind == 'quote' else compose(legs, decimal_entry)
                changed = same.replace('inv-1', 'changed-inventory') if kind == 'quote' else same.replace('original-card', 'changed-route')
                malformed = ('compose_quote_decimal\nbroken\ntrue\n' if kind == 'quote'
                             else 'compose_legs_decimal\ntrue\n')
                invalid_conversion = (compose_quote(quote, True).replace('100.00\n', '1e6\n')
                                      .replace('10000\n', '1e6\n') if kind == 'quote' else
                                      compose(legs, True).replace('300.00\n', '1e6\n')
                                      .replace('30000\n', '1e6\n'))
                interrupted = '\n'.join(same.splitlines()[:-1]) + '\n'
                for replacement, expected in ((same, 0), (changed, 0), (malformed, 1),
                                               (invalid_conversion, 1), (interrupted, 0)):
                    with self.subTest(prefix=prefix_name, kind=kind, replacement=replacement[:90]):
                        tail = '' if replacement == interrupted else (
                            ('simulate_quote\n' if kind == 'quote' and expected else '') +
                            'propose_line_refund\nshow\nquit\n')
                        status, client, output, errors = self.run_journey(prefix + replacement + tail)
                        self.assertEqual((status, errors, len(client.exchanges)), (expected, '', 3))
                        if tail:
                            quote_hash = client.exchanges[0].response['result']['quoteHash']
                            active = dict(plan=None, quote=None if kind == 'quote' else quote_hash, refund=None)
                            self.assertIn('active=' + codec().canonical(active), output)
                            self.assertIn('Active quote, plan and explicit line selection are required.', output)
                # Recalculate after a valid replacement: the previous line selection stays invalid.
                recalculate = ('simulate_quote\nSUBMIT_QUOTE\n' if kind == 'quote' else '')
                status, client, output, errors = self.run_journey(prefix + same + recalculate +
                    'plan_payments\n999\nSUBMIT_PLAN\npropose_line_refund\nquit\n')
                self.assertEqual((status, errors, len(client.exchanges)), (0, '', 5 if kind == 'quote' else 4))
                self.assertIn('Active quote, plan and explicit line selection are required.', output)
        self.assertEqual(self.run_journey(answers('decimal_replacement'))[0], 0)

    def test_picker_journey_json_parity(self):
        commerce = _calculator()['commerce']
        with patch.object(commerce, 'build_quote', side_effect=AssertionError('parent arithmetic')), \
             patch.object(commerce, 'plan_payments', side_effect=AssertionError('parent arithmetic')), \
             patch.object(commerce, 'propose_line_refund', side_effect=AssertionError('parent arithmetic')), \
             patch('time.time', side_effect=AssertionError('implicit clock')):
            for name in ('journey', 'precision', 'free'):
                script = answers('picker_' + name)
                with self.subTest(name=name):
                    status, guided, output, errors = self.run_journey(script)
                    jstatus, explicit, _, jerrors = self.run_journey(json_selection(script))
                    self.assertEqual((status, errors, jstatus, jerrors), (0, '', 0, ''))
                    self.assertEqual(guided.exchanges, explicit.exchanges)
                    self.assertEqual(len(guided.exchanges), 3)
                    quote, plan, refund = [e.response['result'] for e in guided.exchanges]
                    display = output.split('quoteHash=')[1].split('Explicit selected line count')[0]
                    self.assertTrue(display.startswith(quote['quoteHash'] + '\n'))
                    self.assertIn('asset=' + codec().canonical(quote['asset']), display)
                    for row in quote['lines']:
                        shown = {field: row[field] for field in ('lineId', 'inventoryId',
                                 'grossAtoms', 'discountAtoms', 'payableAtoms')}
                        self.assertIn('refund_line=' + codec().canonical(shown), display)
                    ids = ['L3', 'L1'] if name == 'journey' else ['L1']
                    request = decode_input(guided.exchanges[-1].request_bytes)['args']
                    self.assertEqual(request['line_ids'], ids)
                    self.assertEqual(request['quote'], quote)
                    self.assertEqual(request['payment_plan'], plan)
                    self.assertEqual(request['expected_plan_hash'], plan['planHash'])
                    self.assertIn('selected_lines=' + codec().canonical(ids), output)
                    self.assertTrue(all(e.response['result']['evidenceClass'] == 'CALCULATION_ONLY'
                                        for e in guided.exchanges))
                    self.assertIs(refund['executionAuthorized'], False)
                    if name == 'precision':
                        self.assertEqual(refund['customerRefund']['atoms'], '9007199254740993')
                    if name == 'free':
                        self.assertEqual(refund['originalRoutes'], [])

    def test_picker_selection_and_confirmation_launch_counts(self):
        script = answers('picker_journey')
        for suffix, count in (('show\nquit\n', 2),
                              ('propose_line_refund\nno\nquit\n', 2),
                              ('propose_line_refund\nSUBMIT_REFUND\nquit\n', 3)):
            with self.subTest(suffix=suffix), \
                 patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                status, client, output, errors = self.run_journey(
                    script.split('propose_line_refund\n')[0] + suffix)
                self.assertEqual((status, errors, launch.call_count, len(client.exchanges)), (0, '', count, count))
                self.assertLess(output.index('selected_lines='), output.index('action: ', output.index('selected_lines=')))
        # The count bound permits MAX_LINES; duplicates are left for driver validation.
        ids = ['L1'] * _calculator()['commerce'].MAX_LINES
        status, client, output, errors = self.run_journey(script.split('pick_lines\n')[0] + pick(ids) + 'quit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (0, '', 2))
        self.assertIn('selected_lines=' + codec().canonical(ids), output)

    def test_picker_driver_refusals_preserve_input(self):
        script = answers('picker_boundaries')
        status, guided, output, errors = self.run_journey(script)
        jstatus, explicit, _, jerrors = self.run_journey(json_selection(script))
        self.assertEqual((status, errors, jstatus, jerrors), (1, '', 1, ''))
        self.assertEqual(guided.exchanges, explicit.exchanges)
        self.assertEqual(len(guided.history), 2)
        self.assertEqual([e.response['error'] for e in guided.exchanges[2:]][:3],
                         ['INVALID_ID_LIST', 'DUPLICATE_ID', 'UNKNOWN_REFUND_LINE'])
        ids_cases = [[], ['L1', 'L1'], ['missing'], [''], [' L1 ']]
        for exchange, ids in zip(guided.exchanges[2:], ids_cases):
            self.assertEqual(decode_input(exchange.request_bytes)['args']['line_ids'], ids)
            self.assertFalse(exchange.response['ok'])
            self.assertIn('selected_lines=' + codec().canonical(ids), output)
        self.assertEqual(len(guided.exchanges), 7)
        # CRLF strips terminators only; quotes and spaces remain literal IDs.
        prefix = answers('picker_journey').split('pick_lines\n')[0]
        ids = ['"L1"', ' L2 ', '']
        status, client, output, errors = self.run_journey((prefix + pick(ids) +
                                      'propose_line_refund\nSUBMIT_REFUND\nquit\n').replace('\n', '\r\n'))
        self.assertEqual((status, errors, len(client.exchanges)), (1, '', 3))
        self.assertEqual(decode_input(client.exchanges[-1].request_bytes)['args']['line_ids'], ids)

    def test_picker_replacement_invalidates_selection_and_refund(self):
        prefix = answers('picker_journey').rsplit('\nshow\n', 1)[0] + '\n'
        invalid = ('', '-1', '301', 'true', '"1"', '1.0', '1e0', '-0', '9007199254740993', '{}', '\ud800')
        replacements = [('pick_lines\n' + value + '\n', 1) for value in invalid]
        replacements += [(pick([value]), 1) for value in ('e\u0301', '\ud800', 'x' * codec().MAX_INPUT_BYTES)]
        replacements += [(pick(ids), 0) for ids in (['L3', 'L1'], ['L2'])]
        replacements += [('select_lines\n[1]\n', 1), ('select_lines\n["L2"]\n', 0)]
        for replacement, expected in replacements:
            with self.subTest(replacement=repr(replacement)[:100]):
                status, client, output, errors = self.run_journey(prefix + replacement +
                    ('propose_line_refund\n' if expected else '') + 'show\nquit\n')
                self.assertEqual((status, errors, len(client.exchanges)), (expected, '', 3))
                q, p = [e.response['result'] for e in client.exchanges[:2]]
                active = json.loads(output.rsplit('active=', 1)[1].splitlines()[0])
                self.assertEqual(active, dict(quote=q['quoteHash'], plan=p['planHash'], refund=None))
                if expected:
                    self.assertIn('Active quote, plan and explicit line selection are required.', output)
                    self.assertEqual(output.count('selected_lines='), 1)
        # Replacing an explicit JSON selection with the picker clears its refund too.
        status, client, output, errors = self.run_journey(json_selection(prefix) + pick(['L2']) +
                    'show\npropose_line_refund\nSUBMIT_REFUND\nquit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (0, '', 4))
        self.assertIn('"refund":null', output)
        self.assertEqual(decode_input(client.exchanges[-1].request_bytes)['args']['line_ids'], ['L2'])
        self.assertEqual(self.run_journey(answers('picker_replacement'))[0], 0)

    def test_picker_missing_inputs_and_upstream_invalidation(self):
        prefix = answers('picker_journey').rsplit('\nshow\n', 1)[0] + '\n'
        # All quote/payment input paths must also invalidate picker-created state.
        changes = [('load_quote\n' + PREFIX + 'quote.json\n', 0, False),
                   (compose_quote(quote_fixture()), 0, False),
                   ('simulate_quote\nno\n', 0, False),
                   ('load_legs\n' + PREFIX + 'legs.json\n', 0, True),
                   ('compose_legs\n0\n', 0, True),
                   ('plan_payments\n999\nSUBMIT_PLAN\n', 1, True)]
        for change, extra, has_quote in changes:
            with self.subTest(change=change):
                status, client, output, errors = self.run_journey(prefix + change +
                    'propose_line_refund\nshow\nquit\n')
                self.assertEqual((status, errors, len(client.exchanges)), (0, '', 3 + extra))
                self.assertIn('Active quote, plan and explicit line selection are required.', output)
                active = json.loads(output.rsplit('active=', 1)[1].splitlines()[0])
                self.assertEqual(active['quote'] is not None, has_quote)
                self.assertIsNone(active['refund'])
        refused = quote_fixture(); refused['lines'][1]['lineId'] = 'L1'
        for initial, expected, calls in (('', 0, 0),
                (prefix + 'load_quote\n' + PREFIX + 'quote.json\n', 0, 3),
                (compose_quote(refused) + 'simulate_quote\nSUBMIT_QUOTE\n', 1, 1)):
            status, client, output, errors = self.run_journey(initial +
                'pick_lines\npropose_line_refund\nquit\n')
            self.assertEqual((status, errors, len(client.exchanges)), (expected, '', calls))
            self.assertIn('A successful active quote is required to pick lines.', output)
            self.assertEqual(output.count('Explicit selected line count:'), int(calls == 3))
        # Quote alone allows selection; submitting still requires a payment plan.
        initial = answers('picker_journey').split('compose_legs\n')[0]
        status, client, output, errors = self.run_journey(initial + pick(['L1']) +
            'propose_line_refund\nquit\n')
        self.assertEqual((status, errors, len(client.exchanges)), (0, '', 1))
        self.assertIn('selected_lines=["L1"]', output)
        self.assertIn('Active quote, plan and explicit line selection are required.', output)

    def test_picker_eof_and_decline(self):
        script = answers('picker_journey')
        selection = ['pick_lines', '2', 'L3', 'L1']
        for initial, calls in ((script.split('pick_lines\n')[0], 2),
                               (script.rsplit('\nshow\n', 1)[0] + '\n', 3)):
            for length in range(1, len(selection) + 1):
                with self.subTest(calls=calls, length=length):
                    status, client, output, errors = self.run_journey(initial +
                        '\n'.join(selection[:length]) + '\n')
                    self.assertEqual((status, errors, len(client.exchanges)), (0, '', calls))
                    self.assertIn('EOF; no further calculations submitted.', output)
                    self.assertEqual(output.count('selected_lines='),
                                     int(calls == 3) + int(length == len(selection)))
        for suffix in ('', 'no\nshow\nquit\n'):
            status, client, _, errors = self.run_journey(script.split('SUBMIT_REFUND\n')[0] + suffix)
            self.assertEqual((status, errors, len(client.exchanges)), (0, '', 2))
        self.assertEqual(self.run_journey(answers('picker_decline'))[0], 0)

    def test_picker_refund_uncertainty_fences(self):
        for failure in ('malformed', 'launch'):
            children = []
            def fail_refund(*args, **kwargs):
                if len(children) < 2:
                    child = POPEN(*args, **kwargs)
                elif failure == 'launch':
                    raise OSError('synthetic launch failure')
                else:
                    child = POPEN([sys.executable, '-B', '-c',
                                   'import sys; sys.stdin.buffer.read(); print("malformed")'], **kwargs)
                children.append(child)
                return child
            with self.subTest(failure=failure), \
                 patch('commerce_calculation_client.subprocess.Popen', side_effect=fail_refund) as launch:
                status, client, _, errors = self.run_journey(answers('picker_journey') * 2)
                self.assertEqual((status, launch.call_count, len(client.history)), (2, 3, 2))
                self.assertIsInstance(client.uncertainty, CalculationUncertainty)
                request = decode_input(client.uncertainty.request_bytes)
                self.assertEqual(request['action'], 'propose_line_refund')
                self.assertEqual(request['args']['line_ids'], ['L3', 'L1'])
                with self.assertRaisesRegex(RuntimeError, 'client fenced'):
                    client.request(request)
                self.assertEqual(launch.call_count, 3)
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
