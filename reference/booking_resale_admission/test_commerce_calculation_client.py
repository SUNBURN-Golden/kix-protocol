"""Source-informed composition tests; arithmetic stays in existing commerce tests."""

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from commerce_calculation_client import (CommerceCalculationClient, CalculationClientStateError,
                                         CalculationUncertainty, codec, decode_input)

HERE = Path(__file__).resolve().parent
DRIVER = HERE.parent / 'v0.3-rc1' / 'commerce_driver.py'
POPEN = subprocess.Popen


def fixture(name):
    return decode_input((HERE / 'fixtures' / ('commerce_console_' + name + '.json')).read_bytes())


def quote_request(name='quote'):
    return dict(action='simulate_quote', args=fixture(name))


def plan_request(quote, legs=None, now=999):
    return dict(action='plan_payments', args=dict(quote=quote, legs=fixture('legs') if legs is None else legs,
                expected_quote_hash=quote['quoteHash'], now=now))


def refund_request(quote, plan, lines=None):
    return dict(action='propose_line_refund', args=dict(quote=quote, payment_plan=plan,
                line_ids=['L2'] if lines is None else lines, expected_plan_hash=plan['planHash']))


class CommerceCalculationClientTests(unittest.TestCase):
    def setUp(self):
        self.client = CommerceCalculationClient(cleanup_timeout=1)

    def send(self, envelope):
        return self.client.request(envelope).response['result']

    def test_real_driver_journey_exact_bytes_and_detached_snapshots(self):
        requests = []
        qreq = quote_request()
        q = self.send(qreq); requests.append(qreq)
        preq = plan_request(q)
        p = self.send(preq); requests.append(preq)
        rreq = refund_request(q, p)
        r = self.send(rreq); requests.append(rreq)
        for exchange, request in zip(self.client.history, requests):
            expected = subprocess.run([sys.executable, str(DRIVER)], input=exchange.request_bytes,
                                      capture_output=True, check=False)
            self.assertEqual(exchange.reply_bytes, expected.stdout)
            self.assertEqual(exchange.returncode, expected.returncode)
            self.assertEqual(decode_input(exchange.request_bytes), request)
            detached = exchange.response
            detached['result'].clear()
            self.assertTrue(exchange.response['result'])
            with self.assertRaises(FrozenInstanceError):
                exchange.reply_bytes = b''
        self.assertEqual(p['quoteHash'], q['quoteHash'])
        self.assertEqual(r['planHash'], p['planHash'])
        self.assertEqual(r['quoteHash'], q['quoteHash'])
        self.assertIs(r['executionAuthorized'], False)
        self.assertEqual([route['routeRef'] for route in r['originalRoutes']],
                         [leg['routeRef'] for leg in p['legs']])
        qreq['args'].clear()
        self.assertTrue(self.client.history[0].response['result']['request'])

    def test_real_driver_rejections_do_not_promote_or_retry(self):
        q = self.send(quote_request())
        p = self.send(plan_request(q))
        cases = []
        stale = plan_request(q); stale['args']['expected_quote_hash'] = 'stale'
        cases.append((stale, 'STALE_QUOTE'))
        cases.append((plan_request(q, now=1000), 'QUOTE_EXPIRED'))
        cases.append((plan_request(q, fixture('bad_legs')), 'PAYMENT_TOTAL_MISMATCH'))
        stale = refund_request(q, p); stale['args']['expected_plan_hash'] = 'stale'
        cases.append((stale, 'STALE_PAYMENT_PLAN'))
        for lines, error in ((['missing'], 'UNKNOWN_REFUND_LINE'), ([], 'INVALID_ID_LIST'),
                             (['L1', 'L1'], 'DUPLICATE_ID')):
            cases.append((refund_request(q, p, lines), error))
        for request, error in cases:
            with self.subTest(error=error), patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
                exchange = self.client.request(request)
                self.assertEqual(exchange.returncode, 2)
                self.assertEqual(exchange.response['error'], error)
                self.assertEqual(len(self.client.history), 2)
                self.assertEqual(launch.call_count, 1)
        # Corrected requests need a separate explicit call; rejection did not fence.
        self.send(plan_request(q))
        self.assertEqual(len(self.client.history), 3)

    def test_fixed_target_single_writer_no_launch_on_import_or_construction(self):
        with patch('commerce_calculation_client.subprocess.Popen', wraps=POPEN) as launch:
            other = CommerceCalculationClient(cleanup_timeout=1)
            self.assertEqual(launch.call_count, 0)
            def spawn(*args, **kwargs):
                with self.assertRaises(CalculationClientStateError):
                    other.request(quote_request())
                self.assertEqual(args[0], [sys.executable, str(DRIVER)])
                self.assertIs(kwargs['shell'], False)
                return POPEN(*args, **kwargs)
            launch.side_effect = spawn
            other.request(quote_request())
            self.assertEqual(launch.call_count, 1)
        probe = subprocess.run([sys.executable, '-B', '-c',
            "import sys; sys.addaudithook(lambda event, args: (_ for _ in ()).throw(AssertionError(event)) "
            "if event.startswith(('subprocess.', 'socket.')) else None); "
            "import commerce_calculation_client, commerce_calculation_console; "
            "commerce_calculation_client.CommerceCalculationClient(cleanup_timeout=1)"],
            cwd=HERE, capture_output=True)
        self.assertEqual((probe.returncode, probe.stdout, probe.stderr), (0, b'', b''))

    def test_ce1_original_token_rejection_and_invalid_local_envelopes_launch_nothing(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":9007199254740993}', b'{"x":1.5}', b'{"x":-0}',
                    b'{} {}', b'\xff', b' ' * (codec().MAX_INPUT_BYTES + 1)):
            with self.subTest(raw=raw[:25]), self.assertRaises(Exception):
                decode_input(raw)
        with patch('commerce_calculation_client.subprocess.Popen') as launch:
            for request in ({'action': 'execute', 'args': {}}, [], {'action': True, 'args': {}},
                            {'action': 'simulate_quote', 'args': {}, 'extra': 1}):
                with self.assertRaises(Exception):
                    self.client.request(request)
            launch.assert_not_called()
        for timeout in (0, -1, True, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                CommerceCalculationClient(cleanup_timeout=timeout)

    def _fault(self, raw, status=0, envelope=None):
        client = CommerceCalculationClient(cleanup_timeout=1)
        children = []
        def launch(*args, **kwargs):
            # Avoid the OS per-argument bound when testing the CE1 output bound.
            expression = (repr(raw[:1]) + ' * ' + str(len(raw))
                          if len(raw) > codec().MAX_INPUT_BYTES else repr(raw))
            child = POPEN([sys.executable, '-B', '-c',
                'import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(' + expression +
                '); sys.stdout.buffer.flush(); raise SystemExit(' + str(status) + ')'], **kwargs)
            children.append(child)
            return child
        with patch('commerce_calculation_client.subprocess.Popen', side_effect=launch) as spawn:
            with self.assertRaises(CalculationUncertainty) as caught:
                client.request(envelope or quote_request())
            self.assertEqual(caught.exception.reply_bytes, raw[:codec().MAX_INPUT_BYTES + 2])
            self.assertIs(client.uncertainty, caught.exception)
            self.assertEqual(client.history, ())
            with self.assertRaises(CalculationClientStateError):
                client.request(quote_request())
            self.assertEqual(spawn.call_count, 1)
        self.assertIsNotNone(children[0].returncode)
        self.assertTrue(children[0].stdin.closed and children[0].stdout.closed)

    def test_malformed_reply_exit_failure_and_schema_hash_binding_fence_without_retry(self):
        for raw, status in ((b'', 1), (b'{', 0), (b'{}', 0), (b'\xff\n', 0),
                            (b'{}\n{}\n', 0), (b'{"ok":true,"ok":false}\n', 0),
                            (b'x' * (codec().MAX_INPUT_BYTES + 2), 0),
                            (b'{"ok":false,"evidenceClass":"CALCULATION_ONLY","error":"X"}\n', 0),
                            (b'{"ok":false,"evidenceClass":"CALCULATION_ONLY","error":1}\n', 2)):
            with self.subTest(raw=raw[:30], status=status):
                self._fault(raw, status)
        good = self.client.request(quote_request()).response
        for mutate in (lambda r: r.update(extra=True), lambda r: r.update(ok=1),
                       lambda r: r.update(evidenceClass='EXECUTION'),
                       lambda r: r['result'].update(quoteHash='bad'),
                       lambda r: r['result'].update(lines={}),
                       lambda r: r['result']['totals'].update(payableAtoms=1)):
            bad = copy.deepcopy(good); mutate(bad)
            self._fault(codec().canonical_bytes(bad) + b'\n')
        self._fault(codec().canonical_bytes(good) + b'\n', 2)
        bad = copy.deepcopy(good)
        bad['result']['request']['orderId'] = 'different'
        bad['result']['quoteHash'] = codec().digest('kix:quote:2',
                    {key: value for key, value in bad['result'].items() if key != 'quoteHash'})
        self._fault(codec().canonical_bytes(bad) + b'\n')

    def test_plan_and_refund_bindings_checked_even_with_rehashed_replies(self):
        q = self.send(quote_request()); preq = plan_request(q)
        p = self.send(preq); rreq = refund_request(q, p)
        r = self.send(rreq)
        cases = [(preq, p, 'planHash', 'kix:payment-plan:2', lambda x: x.update(quoteHash='stale')),
                 (preq, p, 'planHash', 'kix:payment-plan:2', lambda x: x.update(checkedAt=True)),
                 (preq, p, 'planHash', 'kix:payment-plan:2', lambda x: x['legs'][0].update(routeRef='other')),
                 (rreq, r, 'proposalHash', 'kix:line-refund-proposal:2', lambda x: x.update(executionAuthorized=True)),
                 (rreq, r, 'proposalHash', 'kix:line-refund-proposal:2', lambda x: x.update(planHash='stale')),
                 (rreq, r, 'proposalHash', 'kix:line-refund-proposal:2', lambda x: x['originalRoutes'][0].update(routeRef='other')),
                 (rreq, r, 'proposalHash', 'kix:line-refund-proposal:2', lambda x: x.update(lineIds=['L1'])),
                 (rreq, r, 'proposalHash', 'kix:line-refund-proposal:2', lambda x: x.update(requiredEvidence=[]))]
        for request, original, field, domain, mutate in cases:
            bad = copy.deepcopy(original); mutate(bad)
            bad[field] = codec().digest(domain, {key: value for key, value in bad.items() if key != field})
            with self.subTest(action=request['action'], result=bad):
                self._fault(codec().canonical_bytes(dict(ok=True, evidenceClass='CALCULATION_ONLY', result=bad)) + b'\n',
                            envelope=request)

    def test_launch_failure_interrupt_short_write_and_cleanup_escalation(self):
        with patch('commerce_calculation_client.subprocess.Popen', side_effect=OSError('launch failed')) as launch:
            with self.assertRaises(CalculationUncertainty):
                self.client.request(quote_request())
            with self.assertRaises(CalculationClientStateError):
                self.client.request(quote_request())
            self.assertEqual(launch.call_count, 1)
        for fault in ('interrupt', 'short', 'broken'):
            client = CommerceCalculationClient(cleanup_timeout=1)
            child = Mock()
            child.stdin = Mock()
            child.stdin.write.return_value = 0 if fault == 'short' else len(codec().canonical_bytes(quote_request()))
            if fault == 'broken':
                child.stdin.write.side_effect = BrokenPipeError
            child.stdout = Mock()
            child.stdout.read.side_effect = [b'{', KeyboardInterrupt()]
            child.wait.side_effect = [subprocess.TimeoutExpired('worker', 1), 0]
            child.returncode = -9
            with patch('commerce_calculation_client.subprocess.Popen', return_value=child):
                with self.assertRaises(CalculationUncertainty) as caught:
                    client.request(quote_request())
            self.assertEqual(caught.exception.reply_bytes, b'{' if fault == 'interrupt' else b'')
            child.terminate.assert_called_once(); child.kill.assert_called_once()
            self.assertEqual(child.wait.call_count, 2)
            child.stdin.close.assert_called(); child.stdout.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
