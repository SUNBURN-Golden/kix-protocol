"""Console boundaries over the real dispatcher; model coverage is reused."""

from copy import deepcopy
import io
import json
import subprocess
import unittest
from unittest.mock import patch

from reward_fixture import FixtureError, decode_json
from supply_client import SupplyClient
import supply_console
from supply_reconciliation import dispatch_request, supply_output
from test_supply_reconciliation import fixture
from token_reward_model import TokenRewardError, _canonical


def event_lines(event):
    return [event['event_id'], event['op'], str(event['amount']),
            json.dumps(event['approved']), json.dumps(event['path_approved']),
            json.dumps(event['program'], ensure_ascii=False)]


def compose(events):
    return ['replace_events', str(len(events)),
            *(line for event in events for line in event_lines(event))]


def calculate(events):
    return compose(events) + ['calculate', 'CALCULATE']


class SupplyConsoleTests(unittest.TestCase):
    def run_session(self, lines, *, send=dispatch_request, stream=None, output=None, errors=None):
        stdout = output if output is not None else io.StringIO()
        stderr = errors if errors is not None else io.StringIO()
        with patch('supply_console.dispatch_request', side_effect=send) as dispatch:
            status = supply_console.run_console(
                input_stream=stream if stream is not None else io.StringIO('\n'.join(lines) + '\n'),
                output_stream=stdout, error_stream=stderr)
        replies = [decode_json(line) for line in stdout.getvalue().splitlines()]
        return status, replies, stderr.getvalue(), dispatch

    def states(self, stderr):
        return [decode_json(line.split('active=', 1)[1])
                for line in stderr.splitlines() if 'active=' in line]

    def test_fixture_journeys_complete_parity_identity_and_single_calls(self):
        for name in ('match', 'holder_burn', 'unexplained', 'unapproved_mint',
                     'unapproved_path', 'both_causes'):
            with self.subTest(name=name):
                request = fixture(name)
                events = request['arguments']['offchain']['events']
                report_request = {'operation': 'supply_report', 'arguments': {'events': events}}
                returned = []

                def send(value):
                    if value['operation'] == 'reconcile_supply':
                        self.assertIs(value['arguments']['offchain'], returned[0]['result'])
                    reply = dispatch_request(value)
                    returned.append(reply)
                    return reply

                lines = calculate(events) + ['reconcile', str(request['arguments']['chain_supply']),
                                             'RECONCILE', 'show', 'quit']
                status, replies, stderr, dispatch = self.run_session(lines, send=send)
                self.assertEqual(status, 0)
                self.assertEqual(dispatch.call_count, 2)
                self.assertEqual(replies, [dispatch_request(report_request), dispatch_request(request)])
                self.assertIn('proposed=' + _canonical(report_request), stderr)
                self.assertIn('proposed=' + _canonical(request), stderr)
                self.assertEqual(self.states(stderr)[0], {'events': events,
                                 'report': replies[0]['result'], 'comparison': replies[1]['result']})
                for label in ('MOCK_TOKEN_REWARD_ONLY', 'CALCULATION_ONLY', 'SYNTHETIC_SUPPLY_FIGURE'):
                    self.assertIn(label, stderr)
                if name == 'both_causes':
                    # Class B only: TL-4 §6.B does not define simultaneous-cause precedence.
                    self.assertEqual(replies[1]['result']['alarm'], 'UNAPPROVED_PATH')

    def test_full_report_forwarded_without_repair_or_metadata_loss(self):
        for alteration in ('missing', 'changed', 'metadata'):
            with self.subTest(alteration=alteration):
                report = deepcopy(fixture('match')['arguments']['offchain'])
                if alteration == 'missing':
                    del report['minted_total']
                elif alteration == 'changed':
                    report['layer_supply'] = 0
                else:
                    report['extra'] = {'caller': '한글'}
                    report['figure'] = 'caller annotation'
                before = deepcopy(report)
                report_reply = supply_output('supply_report', result=report, extra={'keep': True})

                def send(request):
                    if request['operation'] == 'supply_report':
                        return report_reply
                    self.assertIs(request['arguments']['offchain'], report)
                    return dispatch_request(request)

                status, replies, _, dispatch = self.run_session(
                    calculate([]) + ['reconcile', '7', 'RECONCILE', 'quit'], send=send)
                self.assertEqual(dispatch.call_count, 2)
                self.assertEqual(replies[0], report_reply)
                self.assertEqual(report, before)
                if alteration == 'metadata':
                    self.assertEqual(status, 0)
                    self.assertEqual(replies[1], dispatch_request({'operation': 'reconcile_supply',
                                     'arguments': {'offchain': report, 'chain_supply': 7}}))
                else:
                    self.assertEqual(status, 1)
                    self.assertEqual(replies[1]['error'], {'code': 'SUPPLY_REPORT_MISMATCH'})

    def test_aggregate_domain_errors_only_after_one_confirmed_call(self):
        base = fixture('report')['arguments']['events']
        cases = [(base + [deepcopy(base[0])], 'SUPPLY_EVENT_DUPLICATE'),
                 ([base[-1], base[0]], 'SUPPLY_CONSERVATION')]
        for events, code in cases:
            for confirm in ('no', 'CALCULATE'):
                with self.subTest(code=code, confirm=confirm):
                    status, replies, stderr, dispatch = self.run_session(
                        compose(events) + ['calculate', confirm, 'show', 'quit'])
                    self.assertEqual(dispatch.call_count, int(confirm == 'CALCULATE'))
                    self.assertEqual(status, int(confirm == 'CALCULATE'))
                    self.assertEqual(self.states(stderr)[0]['report'], None)
                    if confirm == 'CALCULATE':
                        with self.assertRaises(TokenRewardError) as caught:
                            dispatch_request({'operation': 'supply_report', 'arguments': {'events': events}})
                        self.assertEqual(caught.exception.code, code)
                        self.assertEqual(replies[0]['error'], {'code': code})

    def test_edits_invalidate_immediately_and_stage_without_partial_install(self):
        events = fixture('report')['arguments']['events']
        replacement = {**events[0], 'event_id': 'new-id'}
        cases = [(['add_event', ':cancel'], events, 0),
                 (['replace_event', ':cancel'], events, 0),
                 (['replace_events', ':cancel'], events, 0),
                 (['replace_events', '1', *event_lines(replacement)[:-1], ':cancel'], events, 0),
                 (['replace_event', '99'], events, 2),
                 (['replace_event', '1', *event_lines(replacement)], [replacement, *events[1:]], 0),
                 (['replace_events', '0'], [], 0),
                 (['add_event', *event_lines(replacement)], [*events, replacement], 0)]
        for edit, expected, edit_status in cases:
            with self.subTest(edit=edit):
                lines = calculate(events) + ['reconcile', '7', 'RECONCILE', *edit, 'show', 'quit']
                status, _, stderr, dispatch = self.run_session(lines)
                self.assertEqual(status, edit_status)
                self.assertEqual(dispatch.call_count, 2)
                self.assertEqual(self.states(stderr)[0], {'events': expected, 'report': None,
                                                         'comparison': None})
        # A cancelled edit must not allow reconciliation to use the old report.
        status, _, stderr, dispatch = self.run_session(
            calculate(events) + ['add_event', ':cancel', 'reconcile', 'show', 'quit'])
        self.assertEqual((status, dispatch.call_count), (2, 1))
        self.assertIsNone(self.states(stderr)[0]['report'])

    def test_recalculation_decline_cancel_or_failure_cannot_reuse_old_selections(self):
        events = fixture('report')['arguments']['events']
        for outcome in ('no', ':cancel', 'CALCULATE'):
            with self.subTest(outcome=outcome):
                count = 0

                def send(request):
                    nonlocal count
                    count += 1
                    if count == 3:
                        raise TokenRewardError('SUPPLY_CONSERVATION')
                    return dispatch_request(request)

                status, replies, stderr, dispatch = self.run_session(
                    calculate(events) + ['reconcile', '7', 'RECONCILE', 'calculate', outcome,
                                         'show', 'reconcile', 'quit'], send=send)
                self.assertEqual(dispatch.call_count, 3 if outcome == 'CALCULATE' else 2)
                self.assertEqual(self.states(stderr)[0]['report'], None)
                self.assertEqual(self.states(stderr)[0]['comparison'], None)
                self.assertEqual(status, 2)  # Last reconcile has no active report.
                self.assertIn('error', replies[-1])

    def test_comparison_decline_cancel_invalid_or_failure_clears_only_comparison(self):
        events = fixture('report')['arguments']['events']
        for attempt in ([':cancel'], ['7', 'no'], ['7', ':cancel'], ['true'], ['7', 'RECONCILE']):
            with self.subTest(attempt=attempt):
                count = 0

                def send(request):
                    nonlocal count
                    count += 1
                    if count == 3:
                        raise TokenRewardError('SUPPLY_REPORT_MISMATCH')
                    return dispatch_request(request)

                lines = calculate(events) + ['reconcile', '7', 'RECONCILE', 'reconcile', *attempt,
                                             'show', 'reconcile', '6', 'RECONCILE', 'show', 'quit']
                # For non-dispatched attempts, do not inject failure on the later valid action.
                sender = send if attempt[-1] == 'RECONCILE' else dispatch_request
                _, _, stderr, dispatch = self.run_session(lines, send=sender)
                first, second = self.states(stderr)
                self.assertIsNotNone(first['report'])
                self.assertIsNone(first['comparison'])
                self.assertEqual(second['comparison']['chain_supply'], 6)
                self.assertEqual(dispatch.call_args.args[0]['arguments']['chain_supply'], 6)

    def test_none_and_deliberate_empty_events_are_distinct_and_show_never_dispatches(self):
        status, replies, stderr, dispatch = self.run_session(
            ['show', 'calculate', 'show', 'replace_events', '0', 'calculate', 'CALCULATE',
             'reconcile', '0', 'RECONCILE', 'quit'])
        self.assertEqual((status, dispatch.call_count), (2, 2))
        self.assertIsNone(self.states(stderr)[0]['events'])
        self.assertEqual(replies[-1]['result']['alarm'], 'MATCH')
        self.assertEqual(replies[-2]['result']['events'], [])
        # Composition counts have no invented supply-amount cap or policy default.
        status, _, _, dispatch = self.run_session(
            ['replace_events', str(10**12 + 1), ':cancel', 'quit'])
        self.assertEqual(status, 0)
        dispatch.assert_not_called()

    def test_each_prompt_eof_cancellation_and_interrupt_before_confirmation_never_dispatch(self):
        event = fixture('report')['arguments']['events'][0]
        prefixes = [['add_event', *event_lines(event)], ['replace_events', '1', *event_lines(event)],
                    compose([event]) + ['replace_event', '1', *event_lines(event)],
                    ['replace_events', '0', 'calculate'],
                    calculate([]) + ['reconcile', '0']]
        # Interrupt or end at every prompt, including both confirmation prompts.
        class Interrupted(io.StringIO):
            def readline(self):
                line = super().readline()
                if not line:
                    raise KeyboardInterrupt()
                return line

        for full in prefixes:
            for index in range(len(full) + 1):
                prefix = full[:index]
                expected_calls = int('CALCULATE' in prefix)
                for boundary in ('eof', 'cancel', 'interrupt'):
                    with self.subTest(prefix=prefix, boundary=boundary):
                        if boundary == 'cancel':
                            lines = prefix + [':cancel', 'quit']
                            status, _, _, dispatch = self.run_session(lines)
                            self.assertEqual(status, 0)
                        else:
                            data = '\n'.join(prefix) + ('\n' if prefix else '')
                            stream = Interrupted(data) if boundary == 'interrupt' else io.StringIO(data)
                            status, _, _, dispatch = self.run_session([], stream=stream)
                            self.assertEqual(status, 2)
                        self.assertEqual(dispatch.call_count, expected_calls)

    def test_invalid_explicit_fields_do_not_dispatch_or_repair(self):
        good = event_lines(fixture('report')['arguments']['events'][0])
        bad = {0: ['', ' spaced', 'x' * 101, '\ud800'], 1: ['', 'mint', ' MINT'],
               2: ['', 'true', '1.0', '1e0', ' 1', '+1', '-1', '0', str(10**12 + 1), '9' * 5000],
               3: ['', 'True', 'null', '1', ' true'], 4: ['', 'False', '0', 'false '],
               5: ['', 'raw', '1', '{}', 'null', '""', '" spaced"', '"\\ud800"']}
        for field, invalids in bad.items():
            for invalid in invalids:
                with self.subTest(field=field, invalid=repr(invalid[:110])):
                    value = good.copy()
                    value[field] = invalid
                    # Full inputs accommodate individual model validation at end of event.
                    status, _, _, dispatch = self.run_session(['add_event', *value, 'quit'])
                    self.assertEqual(status, 2)
                    dispatch.assert_not_called()
        for lines in (['replace_events', '-1'], ['replace_events', 'true'],
                      ['replace_events', ''], ['replace_events', '0', 'replace_event', '1']):
            status, _, _, dispatch = self.run_session([*lines, 'quit'])
            self.assertEqual(status, 2)
            dispatch.assert_not_called()
        for chain in ('', 'true', '"0"', '0.0', '0e0', '-1', str(10**12 + 1)):
            status, _, stderr, dispatch = self.run_session(
                calculate([]) + ['reconcile', chain, 'show', 'quit'])
            self.assertEqual((status, dispatch.call_count), (2, 1))
            self.assertIsNone(self.states(stderr)[0]['comparison'])

    def test_holder_burn_restrictions_burn_null_and_verbatim_unicode(self):
        base = fixture('report')['arguments']['events']
        for approved, program in ((True, None), (False, 'program')):
            holder = {**base[0], 'op': 'HOLDER_BURN', 'approved': approved, 'program': program}
            status, replies, _, dispatch = self.run_session(compose([holder]) + ['quit'])
            self.assertEqual(status, 2)
            dispatch.assert_not_called()
            self.assertEqual(replies[0]['error']['code'], 'HOLDER_BURN_NOT_LAYER')
        events = [dict(base[0], event_id='합성-민팅'), dict(base[-1], program=None)]
        status, replies, _, dispatch = self.run_session(calculate(events) + ['quit'])
        self.assertEqual((status, dispatch.call_count), (0, 1))
        self.assertEqual(replies[0]['result']['events'], events)

    def test_terminal_dispatch_and_io_failures_stop_without_retry(self):
        for error in (FixtureError('bad reply'), RuntimeError('failure'), OSError('closed')):
            with self.subTest(error=error):
                def send(request):
                    raise error
                status, _, _, dispatch = self.run_session(
                    calculate([]) + ['calculate', 'CALCULATE', 'quit'], send=send)
                self.assertEqual((status, dispatch.call_count), (2, 1))

        class FailedOutput(io.StringIO):
            def write(self, value):
                raise OSError('write failed')

        for failure_stream in ('preview', 'result'):
            output = FailedOutput() if failure_stream == 'result' else None
            errors = FailedOutput() if failure_stream == 'preview' else None
            status, _, _, dispatch = self.run_session(
                calculate([]) + ['calculate', 'CALCULATE', 'quit'], output=output, errors=errors)
            self.assertEqual(status, 2)
            self.assertEqual(dispatch.call_count, int(failure_stream == 'result'))

        class FailedPreview(io.StringIO):
            def write(self, value):
                if value.startswith('proposed=') or value.startswith('Type literal'):
                    raise OSError('preview or confirmation prompt write failed')
                return super().write(value)

        status, _, _, dispatch = self.run_session(calculate([]) + ['quit'], errors=FailedPreview())
        self.assertEqual(status, 2)
        dispatch.assert_not_called()

        class FailedRead(io.StringIO):
            def readline(self):
                raise OSError('read failed')

        status, _, _, dispatch = self.run_session([], stream=FailedRead())
        self.assertEqual(status, 2)
        dispatch.assert_not_called()

    def test_domain_status_sticks_after_later_success_and_alarm_executes_nothing(self):
        events = fixture('report')['arguments']['events']
        status, _, _, dispatch = self.run_session(
            calculate(events + [events[0]]) + calculate([]) + ['quit'])
        self.assertEqual((status, dispatch.call_count), (1, 2))


class SupplyConsoleLiveTests(unittest.TestCase):
    def run_session(self, lines, *, errors=None, child=None):
        stdout, stderr = io.StringIO(), errors if errors is not None else io.StringIO()
        requests, responses = [], []
        original = SupplyClient.request

        def send(client, request):
            requests.append(deepcopy(request))
            if request['operation'] == 'reconcile_supply':
                self.assertIs(request['arguments']['offchain'], responses[-1].reply['result'])
            response = original(client, request)
            responses.append(response)
            return response

        process_kwargs = {'wraps': subprocess.Popen} if child is None else {'return_value': child}
        with patch('supply_console.dispatch_request') as fallback, \
                patch('supply_client.subprocess.Popen', **process_kwargs) as launch, \
                patch.object(SupplyClient, 'request', send):
            status = supply_console.run_console(
                input_stream=io.StringIO('\n'.join(lines) + '\n'), output_stream=stdout,
                error_stream=stderr, mode='subprocess', cleanup_timeout=1)
        fallback.assert_not_called()
        return (status, [decode_json(line) for line in stdout.getvalue().splitlines()],
                stderr.getvalue(), launch, requests, responses)

    def test_returned_report_forwarded_whole_and_serialized_without_repair(self):
        events = fixture('report')['arguments']['events']
        status, replies, _, launch, requests, responses = self.run_session(
            calculate(events) + ['reconcile', '7', 'RECONCILE', 'quit'])
        self.assertEqual((status, launch.call_count), (0, 2))
        self.assertEqual(requests[1]['arguments']['offchain'], replies[0]['result'])
        self.assertEqual(replies, [response.reply for response in responses])
        self.assertEqual(replies[1], dispatch_request(requests[1]))

    def test_edits_invalidate_before_cancel_failure_and_replacement(self):
        events = fixture('report')['arguments']['events']
        replacement = {**events[0], 'event_id': 'new-id'}
        for edit in (['add_event', ':cancel'], ['replace_event', ':cancel'],
                     ['replace_events', ':cancel'], ['replace_event', '99'],
                     ['replace_events', '1', *event_lines(replacement)[:-1], ':cancel'],
                     ['replace_event', '1', *event_lines(replacement)],
                     ['replace_events', '0'], ['add_event', *event_lines(replacement)]):
            with self.subTest(edit=edit):
                status, _, stderr, launch, _, _ = self.run_session(
                    calculate(events) + ['reconcile', '7', 'RECONCILE', *edit,
                                         'show', 'reconcile', 'quit'])
                self.assertEqual((status, launch.call_count), (2, 2))
                state = SupplyConsoleTests.states(self, stderr)[0]
                self.assertIsNone(state['report'])
                self.assertIsNone(state['comparison'])

    def test_preview_cancel_decline_invalid_input_and_failed_preview_launch_nothing(self):
        cases = [compose([]) + ['show', 'quit'], compose([]) + ['calculate', 'no', 'quit'],
                 compose([]) + ['calculate', ':cancel', 'quit'], ['add_event', ':cancel', 'quit'],
                 ['replace_events', 'bad', 'quit'], ['calculate', 'quit'],
                 compose([]) + ['calculate']]
        for lines in cases:
            with self.subTest(lines=lines):
                _, _, _, launch, _, _ = self.run_session(lines)
                launch.assert_not_called()

        class FailedPreview(io.StringIO):
            def write(self, value):
                if value.startswith('proposed='):
                    raise OSError('preview failed')
                return super().write(value)

        status, _, _, launch, _, _ = self.run_session(calculate([]) + ['quit'], errors=FailedPreview())
        self.assertEqual(status, 2)
        launch.assert_not_called()

    def test_declined_recalculation_clears_report_and_declined_reconciliation_retains_it(self):
        for outcome in ('no', ':cancel'):
            status, _, stderr, launch, _, _ = self.run_session(
                calculate([]) + ['reconcile', '0', outcome, 'show',
                                 'calculate', outcome, 'show', 'reconcile', 'quit'])
            states = SupplyConsoleTests.states(self, stderr)
            self.assertIsNotNone(states[0]['report'])
            self.assertIsNone(states[0]['comparison'])
            self.assertIsNone(states[1]['report'])
            self.assertEqual((status, launch.call_count), (2, 1))

    def test_domain_rejection_is_sticky_but_allows_explicit_later_calculation(self):
        events = fixture('report')['arguments']['events']
        status, replies, _, launch, _, _ = self.run_session(
            calculate(events + [events[0]]) + calculate([]) + ['quit'])
        self.assertEqual((status, launch.call_count), (1, 2))
        self.assertEqual(replies[0]['error']['code'], 'SUPPLY_EVENT_DUPLICATE')
        self.assertIn('result', replies[1])

    def test_transport_uncertainty_and_exit_two_stop_without_retry_or_fallback(self):
        from test_supply_client import Child, wire
        terminal = supply_output('supply_report', error={'type': 'FixtureError', 'message': 'bad'})
        for child, expected in ((Child(b'invalid'), []), (Child(wire(terminal), 2), [terminal])):
            with self.subTest(expected=expected):
                status, replies, _, launch, _, _ = self.run_session(
                    calculate([]) + ['calculate', 'CALCULATE', 'quit'], child=child)
                self.assertEqual((status, launch.call_count), (2, 1))
                self.assertEqual(replies, expected)


if __name__ == '__main__':
    unittest.main()
