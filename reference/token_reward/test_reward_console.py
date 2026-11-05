"""Source-informed console composition; existing suites own FSM predicates."""

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reward_cli import _error, dispatch_request
from reward_console import main, run_console
from reward_fixture import FixtureError, load_fixture
from test_reward_session import FIXTURES, OPERATIONS, requests
from tl4_support import human_approval
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE, TokenRewardError, _canonical


HERE = Path(__file__).resolve().parent
FIXTURE = FIXTURES / 'reward_session.json'
CONSOLE = HERE / 'reward_console.py'
# Test-owned prompt contract; do not derive transcripts from implementation tables.
ORDER = {
    'observe': ('reward_key', 'source_view', 'rule_version', 'amount', 'source_kind'),
    'hold': ('reward_id_value',),
    'mark_eligible': ('reward_id_value', 'window_closed', 'source_view', 'abuse_clear'),
    'submit': ('reward_id_value', 'approval_ref', 'signed_bytes_digest', 'spend_pool'),
    'observe_transfer_effects': ('reward_id_value', 'effects_digest', 'outcome'),
    'reconcile_unknown': ('reward_id_value', 'same_digest', 'resolution'),
    'observe_source_cancel': ('reward_id_value', 'source_view', 'reason'),
    'observe_krw_refund': ('reward_id_value', 'source_view', 'reason'),
    'supersede': ('reward_id_value', 'approval_ref', 'rule_version'),
    'view': ('reward_id_value',), 'reward_ids': (), 'pool_view': (),
}
READS = {'view', 'reward_ids', 'pool_view'}
OPTIONALS = {'mark_eligible': {'abuse_kind', 'recipient_cap', 'program_cap'},
             'submit': {'budget_ceiling', 'execution_permit'}}
STRUCTURED = {'reward_key', 'source_view', 'approval_ref', 'window_closed', 'abuse_clear'}


def answers(row, confirmation='SUBMIT'):
    op, args = row['operation'], row['arguments']
    lines = [op] + [_canonical(args[key]) if key in STRUCTURED else str(args[key])
                    for key in ORDER[op]]
    if op in OPTIONALS:
        lines.append(_canonical({k: v for k, v in args.items() if k in OPTIONALS[op]}))
    if op not in READS:
        lines += [args['idempotency_key'], confirmation]
    return lines


def script(lines):
    return io.StringIO('\n'.join(lines) + '\n')


def printed(prefix, output):
    return [json.loads(line) for line in re.findall(prefix + r'=(\{[^\n]+\})', output)]


def mutation_examples():
    rows = requests('participation')[:5]
    rows += [next(r for r in requests('cancellation') if r['operation'] == op)
             for op in ('observe_source_cancel', 'observe_krw_refund')]
    rows += requests('unknown_resolution')[:1]
    rows.append({'operation': 'supersede', 'arguments': {
        'reward_id_value': rows[1]['arguments']['reward_id_value'],
        'approval_ref': human_approval('console-supersession'),
        'rule_version': 'synthetic-rule-v2', 'idempotency_key': 'console-supersession'}})
    return rows


class RewardConsoleTests(unittest.TestCase):
    def drive(self, lines, *, stream=None, output=None, errors=None, dispatch=None):
        output = io.StringIO() if output is None else output
        errors = io.StringIO() if errors is None else errors
        session = load_fixture(FIXTURE)
        calls = []

        def record(active, row):
            self.assertIs(active, session)
            calls.append(deepcopy(row))
            return (dispatch or dispatch_request)(active, row)

        with patch('reward_console.dispatch_request', side_effect=record):
            status = run_console(session, input_stream=stream if stream is not None else script(lines),
                                 output_stream=output, error_stream=errors)
        return status, calls, output.getvalue(), errors.getvalue()

    def parity(self, calls, output):
        session, expected = load_fixture(FIXTURE), []
        for row in calls:
            self.assertEqual(set(row), {'operation', 'arguments'})
            try:
                expected.append(dispatch_request(session, row))
            except TokenRewardError as error:
                expected.append(_error(row['operation'], error))
        replies = printed('desk', output)
        self.assertEqual(replies, expected)
        self.assertEqual(printed('proposed', output), [r for r in calls if r['operation'] not in READS])
        for reply in replies:
            self.assertEqual(reply['provenance'], PROVENANCE)
            receipt = reply.get('receipt')
            view = reply.get('view') or (receipt or {}).get('reward')
            if view:
                self.assertTrue(view['non_transferable_until_chargeback_end'])
                self.assertEqual(view['unit'], 'POINT_F4')
            for body in (receipt, view):
                if body:
                    for flag in ALWAYS_FALSE_FLAGS:
                        self.assertIs(body[flag], False)
        return replies

    def invoke(self, text, *, fixture=FIXTURE):
        return subprocess.run([sys.executable, '-B', str(CONSOLE), '--fixture', str(fixture)],
                              input=text, text=True, encoding='utf-8', capture_output=True,
                              timeout=20, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def test_success_transcript(self):
        text = (FIXTURES / 'reward_console_journey.txt').read_text(encoding='utf-8')
        status, calls, output, errors = self.drive(text.splitlines())
        self.assertEqual((status, errors), (0, ''))
        self.assertEqual(calls, requests('participation'))
        replies = self.parity(calls, output)
        self.assertEqual(replies[5]['receipt'], replies[0]['receipt'] | {'duplicate': True, 'applied': None})
        self.assertEqual(replies[5]['receipt']['reward']['phase'], 'OBSERVED')
        self.assertEqual(replies[-3]['view']['phase'], 'ISSUED')
        self.assertEqual(len(replies[-1]['pool_view']['spends']), 1)
        self.assertIn('Historical action snapshot', output)
        self.assertIn('Current session observation', output)
        first, second = self.invoke(text), self.invoke(text)
        self.assertEqual((first.returncode, first.stderr), (0, ''))
        self.assertEqual((second.returncode, second.stderr), (0, ''))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stdout, output)

    def test_boundary_transcript_sticky_exit(self):
        text = (FIXTURES / 'reward_console_boundaries.txt').read_text(encoding='utf-8')
        status, calls, output, errors = self.drive(text.splitlines())
        self.assertEqual((status, errors), (1, ''))
        self.assertEqual(calls, requests('boundaries'))
        replies = self.parity(calls, output)
        self.assertEqual([r['error']['code'] for r in replies if 'error' in r],
                         ['WINDOW_OPEN', 'POOL_FORBIDDEN_FOR_TOKEN_SPEND',
                          'POOL_FORBIDDEN_FOR_TOKEN_SPEND', 'POOL_FORBIDDEN_FOR_TOKEN_SPEND',
                          'AI_APPROVAL_REJECTED'])
        self.assertIn('receipt', replies[3])  # Accepted action after refusal.
        self.assertIn('pool_view', replies[-1])  # Reads do not clear status 1.
        result = self.invoke(text)
        self.assertEqual((result.returncode, result.stderr, result.stdout), (1, '', output))

    def test_other_selectors_and_explicit_unknown_resolution(self):
        journeys = [requests('cancellation'),
                    requests('unknown_pending') + requests('unknown_resolution'),
                    requests('participation')[:5] + mutation_examples()[-1:]]
        seen = set()
        for rows in journeys:
            with self.subTest(operations=[r['operation'] for r in rows]):
                lines = [v for row in rows for v in answers(row)]
                status, calls, output, errors = self.drive(lines + ['quit'])
                self.assertEqual((status, errors), (int(any('error' in r for r in printed('desk', output))), ''))
                self.assertEqual(calls, rows)  # No implicit reads, resends, transitions or compensation.
                replies = self.parity(calls, output)
                seen.update(r['operation'] for r in calls)
                if rows[0]['arguments']['idempotency_key'] == 'unknown-observe':
                    views = [r['view'] for r in replies if 'view' in r]
                    self.assertEqual([v['phase'] for v in views], ['UNKNOWN', 'UNKNOWN', 'ISSUED'])
        self.assertEqual(seen, set(OPERATIONS))

    def test_all_mutations_literal_confirmation_and_fresh_fields(self):
        for row in mutation_examples():
            for decline in ('submit', ' SUBMIT', 'SUBMIT ', 'SUBMIT\t', '', 'no'):
                with self.subTest(operation=row['operation'], decline=decline):
                    newer = deepcopy(row)
                    newer['arguments']['idempotency_key'] += '-fresh'
                    if row['operation'] == 'observe':
                        newer['arguments']['reward_key']['recipient'] = 'fresh-recipient'
                    else:
                        newer['arguments']['reward_id_value'] = 'fresh-reward'
                    def accepted(session, request):
                        return {'operation': request['operation'], 'provenance': PROVENANCE, 'receipt': {}}
                    lines = answers(row, decline) + answers(newer) + answers(row, 'no') + ['quit']
                    status, calls, output, errors = self.drive(lines, dispatch=accepted)
                    self.assertEqual((status, calls, errors), (0, [newer], ''))
                    self.assertEqual(printed('proposed', output), [row, newer, row])
                    self.assertEqual(output.count('Declined; no request sent.'), 2)

    def test_proposal_is_complete_and_flushed_before_confirmation(self):
        row = requests('participation')[0]
        output = io.StringIO()
        pending = iter(answers(row) + ['quit'])
        class CheckingInput:
            def readline(inner):
                line = next(pending)
                if line == 'SUBMIT':
                    self.assertEqual(printed('proposed', output.getvalue()), [row])
                    self.assertNotIn('desk=', output.getvalue())
                    self.assertGreater(output.flush.call_count, 0)
                return line + '\r\n'
        with patch.object(output, 'flush', wraps=output.flush):
            status, calls, _, errors = self.drive([], stream=CheckingInput(), output=output)
        self.assertEqual((status, calls, errors), (0, [row], ''))

    def test_omitted_null_optionals_and_opaque_metadata_forward_unchanged(self):
        for explicit in (False, True):
            rows = requests('participation')[:4]
            rows[0]['arguments']['source_view']['metadata']['extra'] = {'opaque': [False, None, 1.25]}
            for row in rows:
                for key in OPTIONALS.get(row['operation'], ()):
                    row['arguments'].pop(key, None)
                    if explicit:
                        row['arguments'][key] = None
            if explicit:
                rows[-1]['arguments']['approval_ref']['prior_record'] = None
            status, calls, output, errors = self.drive([v for row in rows for v in answers(row)] + ['quit'])
            self.assertEqual((status, calls, errors), (0, rows, ''))
            self.parity(calls, output)
            self.assertEqual('prior_record' in calls[-1]['arguments']['approval_ref'], explicit)
        # Existing UNKNOWN fixture also forwards a non-null execution permit.
        rows = requests('unknown_pending')
        status, calls, output, errors = self.drive([v for row in rows for v in answers(row)] + ['quit'])
        self.assertEqual((status, calls, errors), (1, rows, ''))
        self.parity(calls, output)

    def test_prompt_syntax_errors_discard_selection_without_dispatch(self):
        observe = answers(requests('participation')[0])
        eligible = answers(requests('participation')[2])
        submit = answers(requests('participation')[3])
        cases = [observe[:i] + [bad] for i, bad in (
            (1, '{}'), (1, 'null'), (1, '{'), (1, '{"x":1,"x":2}'),
            (2, '[]'), (2, '{"x":NaN}'), (2, '{"x":1e9999}'),
            (2, '{"x":"\\ud800"}'), (3, ''), (3, ' v1'),
            (4, '1.0'), (4, '1e3'), (4, '+1'), (4, ' 1'), (4, 'true'),
            (4, '9' * 5000), (5, ''), (6, ''))]
        cases += [eligible[:2] + [bad] for bad in ('1', '"true"', 'null', 'True')]
        cases += [eligible[:4] + ['0'], eligible[:5] + ['null'],
                  eligible[:5] + ['{"unknown":null}'],
                  submit[:2] + ['[]'], submit[:2] + ['{}'],
                  submit[:2] + [_canonical(human_approval() | {'evidence_refs': {}})],
                  submit[:5] + ['{"execution_permit":{}}'],
                  submit[:5] + ['{"budget_ceiling":0,"budget_ceiling":1}']]
        for lines in cases:
            with self.subTest(lines=lines):
                status, calls, output, errors = self.drive(lines + ['quit'])
                self.assertEqual((status, calls, errors), (0, [], ''))
                self.assertIn('input_error=', output)
                self.assertNotIn('proposed=', output)

    def test_economic_predicates_are_left_to_fsm(self):
        row = requests('participation')[0]
        row['arguments']['amount'] = -1
        status, calls, output, errors = self.drive(answers(row) + ['quit'])
        self.assertEqual((status, calls, errors), (1, [row], ''))
        self.assertEqual(self.parity(calls, output)[0]['error']['code'], 'INVALID_AMOUNT')
        row['arguments']['amount'] = 999999999999
        row['arguments']['source_kind'] = 'CALLER_UNSUPPORTED'
        status, calls, output, errors = self.drive(answers(row) + ['quit'])
        self.assertEqual((status, errors), (1, ''))
        self.assertEqual(calls[0]['arguments']['amount'], 999999999999)
        self.assertEqual(self.parity(calls, output)[0]['error']['code'], 'SOURCE_KIND_UNSUPPORTED')

    def test_quit_unknown_menu_and_reads_have_no_implicit_dispatch(self):
        status, calls, output, errors = self.drive(['unknown', 'quit'])
        self.assertEqual((status, calls, errors), (0, [], ''))
        self.assertIn('Unknown action', output)
        rows = [{'operation': op, 'arguments': {}} for op in ('reward_ids', 'pool_view')]
        status, calls, output, errors = self.drive(['reward_ids', 'pool_view', 'quit'])
        self.assertEqual((status, calls, errors), (0, rows, ''))
        self.parity(calls, output)
        self.assertNotIn('proposed=', output)

    def test_eof_at_every_prompt_and_confirmation_stops(self):
        for row in mutation_examples():
            lines = answers(row)
            for cut in range(len(lines)):
                with self.subTest(operation=row['operation'], cut=cut):
                    status, calls, _, errors = self.drive([], stream=script(lines[:cut]) if cut else io.StringIO())
                    self.assertEqual((status, calls), (2, []))
                    self.assertIn('EOFError', errors)
        for failure in (KeyboardInterrupt('interrupt'), OSError('input failed'), UnicodeError('bad input')):
            lines = script(answers(requests('participation')[0]))
            class BrokenInput:
                def readline(inner):
                    line = lines.readline()
                    if line:
                        return line
                    raise failure
            status, calls, output, errors = self.drive([], stream=BrokenInput())
            self.assertEqual((status, len(calls)), (2, 1))
            self.assertEqual(json.loads(errors.split('FENCED: ')[1])['last_reply'], printed('desk', output)[0])

    def test_dispatch_format_and_unexpected_failure_stop_queued_actions(self):
        row = requests('participation')[0]
        for failure in (FixtureError('bad dispatch'), RuntimeError('unexpected'), KeyboardInterrupt('interrupt')):
            def broken(session, request):
                raise failure
            status, calls, output, errors = self.drive(answers(row) + ['pool_view', 'quit'], dispatch=broken)
            self.assertEqual((status, calls), (2, [row]))
            detail = json.loads(errors.split('FENCED: ')[1])
            if isinstance(failure, FixtureError):
                self.assertEqual(detail['last_reply'], _error('observe', failure))
                self.assertEqual(printed('desk', output), [detail['last_reply']])
            else:
                self.assertIsNone(detail['last_reply'])

    def test_output_and_diagnostic_failure_cannot_resume(self):
        row = requests('participation')[0]
        for fail_on in ('proposed=', 'desk=', 'Historical action snapshot', 'flush'):
            class BrokenOutput(io.StringIO):
                def write(inner, text):
                    if fail_on != 'flush' and text.startswith(fail_on):
                        raise OSError('output failed')
                    return super().write(text)
                def flush(inner):
                    if fail_on == 'flush':
                        raise OSError('flush failed')
            output = BrokenOutput()
            status, calls, _, errors = self.drive(answers(row) + ['pool_view', 'quit'], output=output)
            self.assertEqual(status, 2)
            self.assertEqual(len(calls), int(fail_on in ('desk=', 'Historical action snapshot')))
            detail = json.loads(errors.split('FENCED: ')[1])
            self.assertEqual(detail['last_reply'] is not None, bool(calls))
        class BrokenDiagnostic(io.StringIO):
            def write(inner, text):
                raise RuntimeError('diagnostic failed')
        status, calls, _, _ = self.drive([], stream=io.StringIO(), errors=BrokenDiagnostic())
        self.assertEqual((status, calls), (2, []))

    def test_setup_required_fixture_once_and_failures_exit_two(self):
        with patch('reward_console.load_fixture', wraps=load_fixture) as load, \
                patch('reward_console.dispatch_request') as dispatch, \
                patch('sys.stdin', script(['quit'])), patch('sys.stdout', io.StringIO()), \
                patch('sys.stderr', io.StringIO()):
            self.assertEqual(main(['--fixture', str(FIXTURE)]), 0)
        load.assert_called_once_with(FIXTURE)
        dispatch.assert_not_called()
        result = subprocess.run([sys.executable, '-B', str(CONSOLE)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'bad.json'
            for content in ('{', '{}', FIXTURE.read_text().replace('MOCK_TOKEN_REWARD_ONLY', 'LIVE'),
                            FIXTURE.read_text().replace('500', '-1')):
                path.write_text(content, encoding='utf-8')
                result = self.invoke('pool_view\nquit\n', fixture=path)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('desk=', result.stdout)
                self.assertIn('FENCED: ', result.stderr)
            result = self.invoke('quit\n', fixture=Path(temp) / 'missing.json')
            self.assertEqual(result.returncode, 2)

    def test_import_and_execution_without_sockets_or_child_launch(self):
        code = '''
from unittest.mock import patch
with patch('socket.socket', side_effect=AssertionError('socket')), \\
     patch('socket.create_connection', side_effect=AssertionError('connect')), \\
     patch('subprocess.Popen', side_effect=AssertionError('child')):
    import reward_console
    raise SystemExit(reward_console.main())
'''
        result = subprocess.run([sys.executable, '-B', '-c', code, '--fixture', str(FIXTURE)], cwd=HERE,
                                input=(FIXTURES / 'reward_console_journey.txt').read_text(),
                                capture_output=True, text=True, timeout=20)
        self.assertEqual((result.returncode, result.stderr), (0, ''))
        self.assertEqual(len(printed('desk', result.stdout)), len(requests('participation')))


if __name__ == '__main__':
    unittest.main()
