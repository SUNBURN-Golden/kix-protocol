"""Source-informed subprocess boundary coverage; arithmetic stays in model tests."""

from copy import deepcopy
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from reward_fixture import FixtureError, decode_json
from supply_client import SupplyClient, SupplyClientStateError, SupplyTransportUncertainty
from supply_reconciliation import dispatch_request, supply_output
from test_supply_reconciliation import fixture
from token_reward_model import _canonical


def wire(value):
    return (_canonical(value) + '\n').encode('utf-8')


def empty_request():
    return {'operation': 'supply_report', 'arguments': {'events': []}}


class Child:
    """Fake only process I/O and lifecycle, with observed binary input."""

    def __init__(self, stdout, returncode=0, stderr=b''):
        self.stdin, self.stdout, self.stderr = (io.BytesIO() for _ in range(3))
        self.returncode = None
        self.status = returncode
        self.output = stdout, stderr
        self.communicate = Mock(side_effect=self.finish)
        self.terminate = Mock()
        self.kill = Mock()
        self.wait = Mock(side_effect=self.reap)

    def reap(self, **kwargs):
        self.returncode = self.status
        return self.status

    def finish(self, input=None, **kwargs):
        if input is not None:
            self.stdin.write(input)
        self.reap()
        for pipe in (self.stdin, self.stdout, self.stderr):
            pipe.close()
        return self.output


class SupplyClientTests(unittest.TestCase):
    def test_real_journeys_full_replies_exits_and_exact_forwarding(self):
        for name in ('match', 'holder_burn', 'unexplained', 'unapproved_mint',
                     'unapproved_path', 'both_causes'):
            with self.subTest(name=name), SupplyClient(cleanup_timeout=1) as client:
                request = fixture(name)
                report_request = {'operation': 'supply_report', 'arguments': {
                    'events': request['arguments']['offchain']['events']}}
                before = deepcopy(report_request)
                with patch('supply_client.subprocess.Popen', wraps=subprocess.Popen) as launch:
                    report = client.request(report_request)
                    comparison_request = {'operation': 'reconcile_supply', 'arguments': {
                        'offchain': report.reply['result'],
                        'chain_supply': request['arguments']['chain_supply']}}
                    comparison = client.request(comparison_request)
                self.assertEqual(launch.call_count, 2)
                for actual, item in ((report, report_request), (comparison, comparison_request)):
                    self.assertEqual((actual.reply, actual.returncode, actual.stdout, actual.stderr),
                                     (dispatch_request(item), 0, wire(dispatch_request(item)), b''))
                self.assertEqual(report_request, before)
                self.assertEqual(comparison_request, request)
                command = [sys.executable, str(Path(__file__).with_name('supply_cli.py').resolve()),
                           '--request', '-']
                for call in launch.call_args_list:
                    self.assertEqual(call.args, (command,))
                    self.assertEqual(call.kwargs, {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE,
                                                  'stderr': subprocess.PIPE, 'shell': False})

    def test_real_rejections_then_success(self):
        events = fixture('report')['arguments']['events']
        conservation = {'operation': 'supply_report', 'arguments': {'events': [events[-1], events[0]]}}
        with SupplyClient(cleanup_timeout=1) as client:
            for request, code in ((fixture('duplicate'), 'SUPPLY_EVENT_DUPLICATE'),
                                  (conservation, 'SUPPLY_CONSERVATION'),
                                  (fixture('tampered'), 'SUPPLY_REPORT_MISMATCH')):
                before = deepcopy(request)
                response = client.request(request)
                self.assertEqual(response.returncode, 1)
                self.assertEqual(response.reply, supply_output(request['operation'], error={'code': code}))
                self.assertEqual(response.stdout, wire(response.reply))
                self.assertEqual(request, before)
            self.assertEqual(client.request(empty_request()).returncode, 0)
            # Nested model predicates retain domain rejection meanings.
            response = client.request({'operation': 'supply_report', 'arguments': {'events': [{}]}})
            self.assertEqual(response.returncode, 1)

    def test_terminal_reply_and_stderr_preserved_without_further_launch(self):
        reply = supply_output('supply_report', error={'type': 'FixtureError', 'message': 'bad'})
        child = Child(wire(reply), 2, b'diagnostic\n')
        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen', return_value=child) as launch:
            response = client.request(empty_request())
            self.assertEqual((response.reply, response.returncode, response.stderr), (reply, 2, b'diagnostic\n'))
            with self.assertRaises(SupplyClientStateError):
                client.request(empty_request())
            launch.assert_called_once()
            child.communicate.assert_called_once_with(input=wire(empty_request()))

    def test_wire_snapshot_preserves_complete_report_and_event_order(self):
        request = fixture('match')
        request['arguments']['offchain']['extra'] = {'verbatim': '합성'}
        before = deepcopy(request)
        child = Child(wire(dispatch_request(request)))
        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen', return_value=child):
            client.request(request)
        child.communicate.assert_called_once_with(input=wire(before))
        self.assertEqual(request, before)

    def test_real_interrupted_child_is_reaped_and_all_pipes_closed(self):
        popen = subprocess.Popen
        children = []

        def launch(*args, **kwargs):
            # Test-only idle child; real OS pipes and termination, no sockets.
            child = popen([sys.executable, '-c', 'import sys; sys.stdin.buffer.read()'], **kwargs)
            children.append(child)
            communicate = child.communicate
            calls = 0

            def interrupt_once(**kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise KeyboardInterrupt()
                return communicate(**kwargs)

            child.communicate = interrupt_once
            return child

        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen', side_effect=launch):
            with self.assertRaises(SupplyTransportUncertainty):
                client.request(empty_request())
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].returncode)
        self.assertTrue(all(pipe.closed for pipe in (children[0].stdin, children[0].stdout, children[0].stderr)))

    def test_strict_decoding_and_exit_agreement_fence(self):
        request = empty_request()
        good = dispatch_request(request)
        variants = []
        for field, invalid in (('operation', 'reconcile_supply'), ('provenance', 'REAL'),
                               ('evidence_class', 'LIVE'), ('notice', ''), ('extra', 1)):
            variants.append(wire({**good, field: invalid}))
        for field in good:
            value = deepcopy(good)
            del value[field]
            variants.append(wire(value))
        variants.extend([b'', b'[]', b'{} {}', b'\xff', b'{"x":1,"x":2}',
                         wire(good) + wire(good), wire(good).replace(b'"minted_total":0', b'"minted_total":NaN'),
                         wire(good).replace(b'"events":[]', b'"events":[],"events":[]'),
                         wire(good).replace(b'CALCULATION_ONLY', b'\\ud800'),
                         wire(good).replace(b'"minted_total":0', b'"minted_total":1e999')])
        for field, invalid in (('events', {}), ('minted_total', False), ('minted_total', '0'),
                               ('minted_total', 0.0), ('layer_supply', -1), ('figure', 'REAL'),
                               ('events', fixture('report')['arguments']['events']), ('extra', 0)):
            value = deepcopy(good)
            value['result'][field] = invalid
            variants.append(wire(value))
        variants.append(wire({**good, 'result': None}))
        variants.append(wire({**good, 'error': {'code': 'NO'}}))
        cases = [(raw, 0) for raw in variants]
        cases += [(wire(good), status) for status in (1, 2, 3, -9, None, False, 0.0)]
        for payload, status in (({'code': 'NO'}, 0), ({'code': 7}, 1),
                                ({'type': 'X', 'message': 'bad'}, 1), ({'code': 'NO'}, 2),
                                ({'type': 'X', 'message': 1}, 2), ({'code': 'NO', 'extra': 1}, 1)):
            cases.append((wire(supply_output('supply_report', error=payload)), status))
        for raw, status in cases:
            with self.subTest(raw=raw, status=status):
                child = Child(raw, status)
                # None is a deliberately broken process status, not a live child.
                with SupplyClient(cleanup_timeout=1) as client, \
                        patch('supply_client.subprocess.Popen', return_value=child) as launch:
                    with self.assertRaises(SupplyTransportUncertainty) as caught:
                        client.request(request)
                    evidence = caught.exception
                    self.assertIs(client.uncertainty, evidence)
                    self.assertEqual((evidence.phase, evidence.request_bytes, evidence.stdout),
                                     ('decode', wire(request), raw))
                    with self.assertRaises(SupplyClientStateError):
                        client.request(request)
                    launch.assert_called_once()

    def test_comparison_types_and_chain_correlation_without_recalculation(self):
        request = fixture('match')
        good = dispatch_request(request)
        for field, invalid in (('chain_supply', 8), ('chain_supply', True), ('offchain_supply', '7'),
                               ('alarm', 'unknown'), ('alarm', []), ('mismatch', 0),
                               ('stop_payout', 1), ('figure', 'REAL'), ('extra', 0)):
            value = deepcopy(good)
            value['result'][field] = invalid
            with self.subTest(field=field, invalid=invalid), SupplyClient(cleanup_timeout=1) as client, \
                    patch('supply_client.subprocess.Popen', return_value=Child(wire(value))):
                with self.assertRaises(SupplyTransportUncertainty):
                    client.request(request)

    def test_offchain_supply_mismatch_retains_evidence_and_fences(self):
        request = fixture('match')
        self.assertEqual(request['arguments']['offchain']['layer_supply'], 7)
        value = dispatch_request(request)
        value['result']['offchain_supply'] = 99
        raw, diagnostic = wire(value), b'diagnostic\n'
        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen',
                      return_value=Child(raw, stderr=diagnostic)) as launch:
            with self.assertRaises(SupplyTransportUncertainty) as caught:
                client.request(request)
            evidence = caught.exception
            self.assertIs(client.uncertainty, evidence)
            self.assertIsInstance(evidence.__cause__, FixtureError)
            self.assertEqual((evidence.phase, evidence.request_bytes, evidence.stdout,
                              evidence.stderr, evidence.returncode),
                             ('decode', wire(request), raw, diagnostic, 0))
            # Neither a repeated comparison nor a different operation may launch.
            for subsequent in (request, empty_request()):
                with self.assertRaises(SupplyClientStateError):
                    client.request(subsequent)
            launch.assert_called_once()

    def test_invalid_inputs_and_construction_launch_nothing(self):
        with patch('supply_client.subprocess.Popen') as launch:
            for timeout in (None, True, 0, -1, float('nan'), float('inf'), '1', 10**400):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    SupplyClient(cleanup_timeout=timeout)
            client = SupplyClient(cleanup_timeout=1)
            for request in ({}, {'operation': [], 'arguments': {}},
                            {'operation': 'other', 'arguments': {}},
                            {'operation': 'supply_report', 'arguments': {'events': [], 'extra': 0}},
                            {'operation': 'supply_report', 'arguments': {'events': '\ud800'}},
                            {'operation': 'supply_report', 'arguments': {'events': float('nan')}}):
                with self.subTest(request=repr(request)), self.assertRaises(FixtureError):
                    client.request(request)
            self.assertIsNone(client.uncertainty)
            client.close()
            client.close()
            with self.assertRaises(SupplyClientStateError):
                client.request(empty_request())
            launch.assert_not_called()

    def test_busy_rejects_request_and_close_without_launch(self):
        with SupplyClient(cleanup_timeout=1) as client, patch('supply_client.subprocess.Popen') as launch:
            client._guard.acquire()
            try:
                for action in (lambda: client.request(empty_request()), client.close):
                    with self.assertRaises(SupplyClientStateError):
                        action()
            finally:
                client._guard.release()
            launch.assert_not_called()

    def test_transport_failure_and_interruption_cleanup_fence_and_retain_evidence(self):
        for error in (OSError('write/read failed'), KeyboardInterrupt(), SystemExit(4)):
            for escalate in (False, True):
                with self.subTest(error=type(error).__name__, escalate=escalate):
                    child = Child(b'partial stdout', -9, b'partial stderr')
                    effects = [error]
                    if escalate:
                        effects.append(subprocess.TimeoutExpired('child', 1))
                    effects.append(child.finish)

                    def communicate(**kwargs):
                        effect = effects.pop(0)
                        if isinstance(effect, BaseException):
                            raise effect
                        return effect(**kwargs)

                    child.communicate.side_effect = communicate
                    with SupplyClient(cleanup_timeout=0.5) as client, \
                            patch('supply_client.subprocess.Popen', return_value=child) as launch:
                        with self.assertRaises(SupplyTransportUncertainty) as caught:
                            client.request(empty_request())
                        self.assertIs(caught.exception.__cause__, error)
                        self.assertEqual((caught.exception.phase, caught.exception.stdout,
                                          caught.exception.stderr, caught.exception.returncode),
                                         ('communicate', b'partial stdout', b'partial stderr', -9))
                        child.terminate.assert_called_once()
                        self.assertEqual(child.kill.call_count, int(escalate))
                        self.assertTrue(all(pipe.closed for pipe in (child.stdin, child.stdout, child.stderr)))
                        with self.assertRaises(SupplyClientStateError):
                            client.request(empty_request())
                        launch.assert_called_once()
        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen', side_effect=OSError('spawn failed')) as launch:
            with self.assertRaises(SupplyTransportUncertainty) as caught:
                client.request(empty_request())
            self.assertEqual((caught.exception.phase, caught.exception.returncode), ('launch', None))
            with self.assertRaises(SupplyClientStateError):
                client.request(empty_request())
            launch.assert_called_once()

    def test_interrupted_cleanup_reaps_and_retains_observed_failure_bytes(self):
        child = Child(b'', -9)
        initial = subprocess.TimeoutExpired('test transport', 1, output=b'observed', stderr=b'diagnostic')
        child.communicate.side_effect = [initial, KeyboardInterrupt()]
        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen', return_value=child):
            with self.assertRaises(SupplyTransportUncertainty) as caught:
                client.request(empty_request())
            self.assertEqual((caught.exception.stdout, caught.exception.stderr,
                              caught.exception.returncode), (b'observed', b'diagnostic', -9))
            self.assertTrue(caught.exception.__notes__)
            child.kill.assert_called_once()
            child.wait.assert_called_once_with(timeout=1)
            self.assertTrue(all(pipe.closed for pipe in (child.stdin, child.stdout, child.stderr)))

    def test_io_failure_after_child_exit_preserves_observed_bytes_and_closes_pipes(self):
        child = Child(b'', -9)
        error = OSError('drain failed after exit')
        error.output, error.stderr = b'observed', b'diagnostic'

        def fail(**kwargs):
            child.returncode = -9
            raise error

        child.communicate.side_effect = fail
        with SupplyClient(cleanup_timeout=1) as client, \
                patch('supply_client.subprocess.Popen', return_value=child):
            with self.assertRaises(SupplyTransportUncertainty) as caught:
                client.request(empty_request())
            self.assertEqual((caught.exception.stdout, caught.exception.stderr,
                              caught.exception.returncode), (b'observed', b'diagnostic', -9))
            self.assertTrue(all(pipe.closed for pipe in (child.stdin, child.stdout, child.stderr)))
            child.terminate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
