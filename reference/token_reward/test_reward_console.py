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
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE, TokenRewardError, _canonical, reward_id


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
SOURCE_FLAGS = ('funds_executed', 'bank_debit_observed', 'legal_debtor_bound',
                'external_return_closed', 'durable')
SOURCE_FIELDS = ('phase', 'currency') + SOURCE_FLAGS


def answers(row, confirmation='SUBMIT'):
    op, args = row['operation'], row['arguments']
    lines = [op] + [_canonical(args[key]) if key in STRUCTURED else str(args[key])
                    for key in ORDER[op]]
    if op in OPTIONALS:
        lines.append(_canonical({k: v for k, v in args.items() if k in OPTIONALS[op]}))
    if op not in READS:
        lines += [args['idempotency_key'], confirmation]
    return lines


def guided_answers(row, confirmation='SUBMIT', *, guided=('reward_key', 'source_view', 'approval_ref')):
    """Test-owned prompt sequence; preserve explicit omission and caller text."""
    lines = answers(row, confirmation)
    for name in reversed(ORDER[row['operation']]):
        if name not in guided or name not in {'reward_key', 'source_view', 'approval_ref'}:
            continue
        index = 1 + ORDER[row['operation']].index(name)
        value = row['arguments'][name]
        if name == 'reward_key':
            composed = [value[k] for k in ('program', 'source_op_id', 'recipient', 'kind')]
        elif name == 'source_view':
            composed = [value['phase'], value['currency']]
            composed += [_canonical(value[k]) for k in SOURCE_FLAGS]
            composed += [_canonical({k: v for k, v in value.items() if k not in SOURCE_FIELDS})]
        else:
            composed = [value['record_id'], _canonical(value['generation'])]
            composed += [value[k] for k in ('authority_id', 'actor_type', 'action', 'scope_ref')]
            composed += [str(len(value['evidence_refs']))] + value['evidence_refs']
            composed += (['include', _canonical(value['prior_record'])]
                         if 'prior_record' in value else ['omit'])
        lines[index:index + 1] = [':guided'] + composed
    return lines


def invalid_guided_inputs():
    approval = ['submit', 'caller-reward', ':guided', 'caller-record']
    for bad in ('true', 'null', '1.0', '1e3', '"1"', '{', '9' * 5000):
        yield approval + [bad]
    count = approval + ['1', 'caller-authority', 'HUMAN', 'point-payout', 'caller-scope']
    for bad in ('-1', 'true', 'null', '1.0', '"1"', '[]', '{', '9' * 5000):
        yield count + [bad]
    for bad in ('', 'OMIT', ' include', 'null'):
        yield count + ['0', bad]
    for bad in ('false', '1', '{}', '[]', '{', '"\\ud800"'):
        yield count + ['0', 'include', bad]
    yield ['observe', ':guided', '\ud800', 'source', 'recipient', 'kind']
    yield count + ['1', '\ud800', 'omit']


class GuidedCompositionTests:
    """New composition paths, exercised with each existing desk harness."""

    def test_source_guided_raw_parity(self):
        for scenario in ('participation', 'cancellation'):
            rows = requests(scenario)
            raw = self.guided_drive([v for row in rows for v in answers(row)] + ['quit'])
            for mixed in (False, True):
                with self.subTest(scenario=scenario, mixed=mixed):
                    lines = [v for i, row in enumerate(rows) for v in guided_answers(
                        row, guided=() if mixed and i % 2 else ('source_view',))]
                    status, calls, output, errors = self.guided_drive(lines + ['quit'])
                    self.assertEqual((status, calls, errors), (0, rows, ''))
                    self.assertEqual(printed('proposed', output), printed('proposed', raw[2]))
                    self.assertEqual(printed('desk', output), printed('desk', raw[2]))
                    replies = self.parity(calls, output)
                    if scenario == 'cancellation':
                        self.assertEqual([r['view']['phase'] for r in replies if 'view' in r],
                                         ['REVERSED', 'CLAWBACK_CLAIM'])
                        refund = next(r['receipt'] for r in replies if r['operation'] == 'observe_krw_refund')
                        self.assertEqual((refund['reward']['phase'], refund['reward']['krw_phase']),
                                         ('ISSUED', 'KRW_REFUND_NOTED'))
                        self.assertNotEqual(refund['effect']['krw_effect_id'], refund['reward']['token_effect_id'])

    def test_source_metadata_preservation_and_fresh_snapshots(self):
        rows = requests('participation')[:3]
        # No metadata wrapper or identity extraction; each selection has its own assertions.
        rows[0]['arguments']['source_view'] = {k: v for k, v in rows[0]['arguments']['source_view'].items()
                                              if k in SOURCE_FIELDS}
        extra = {'metadata': {'phase': 'CANCELLED', 'currency': None, 'funds_executed': True,
                              'sequence': 9007199254740993, 'negative': -9007199254740993,
                              'opaque': [None, False, '한글:e\u0301', {'durable': True}]},
                 'source_op_id': 'opaque-does-not-replace-key', 'unwrapped': [3, 2, 1], 'nullable': None}
        rows[2]['arguments']['source_view'].update(extra)
        raw = self.guided_drive([v for row in rows for v in answers(row)] + ['quit'])
        status, calls, output, errors = self.guided_drive([v for row in rows for v in guided_answers(row)] + ['quit'])
        self.assertEqual((status, calls, errors), (0, rows, ''))
        self.assertEqual(printed('desk', output), printed('desk', raw[2]))
        replies = self.parity(calls, output)
        self.assertEqual(replies[0]['receipt']['reward']['source_view'], rows[0]['arguments']['source_view'])
        self.assertEqual(replies[2]['receipt']['reward']['source_view'], rows[2]['arguments']['source_view'])
        self.assertEqual(replies[2]['receipt']['reward']['source_op_id'],
                         rows[0]['arguments']['reward_key']['source_op_id'])

    def test_source_domain_refusal_parity(self):
        # Reuse valid prefixes so all four selectors exercise the existing source predicate.
        cancellation = requests('cancellation')
        prefixes = [([], requests('participation')[0]),
                    (requests('participation')[:2], requests('participation')[2]),
                    (cancellation[:2], cancellation[2]),
                    (cancellation[:9], cancellation[9])]
        invalid = [('phase', v, 'SOURCE_NOT_COMMITTED') for v in ('', ' ', ' COMMITTED', 'COMMITTED ', 'CANCELLED')]
        invalid += [('currency', v, 'CURRENCY_UNSUPPORTED') for v in ('', ' ', ' KRW', 'KRW ', 'USD')]
        invalid += [(k, True, 'SOURCE_VIEW_REJECTED') for k in SOURCE_FLAGS]
        for prefix, template in prefixes:
            for name, value, code in invalid:
                with self.subTest(operation=template['operation'], field=name, value=value):
                    row = deepcopy(template)
                    row['arguments']['source_view'][name] = value
                    rows = prefix + [row]
                    raw = self.guided_drive([v for r in rows for v in answers(r)] + ['quit'])
                    status, calls, output, errors = self.guided_drive(
                        [v for r in rows for v in guided_answers(r, guided=('source_view',))] + ['quit'])
                    self.assertEqual((status, calls, errors), (1, rows, ''))
                    self.assertEqual(printed('proposed', output), printed('proposed', raw[2]))
                    self.assertEqual(printed('desk', output), printed('desk', raw[2]))
                    self.assertEqual(self.parity(calls, output)[-1]['error']['code'], code)
        rows = requests('boundaries')[:3]
        status, calls, output, errors = self.guided_drive([v for r in rows for v in guided_answers(r)] + ['quit'])
        self.assertEqual((status, calls, errors), (1, rows, ''))
        self.assertEqual(self.parity(calls, output)[-1]['error']['code'], 'WINDOW_OPEN')
        # Raw JSON still forwards incomplete and wrongly typed source snapshots to the FSM.
        for snapshot in ({}, {'phase': 'COMMITTED'}, {'phase': 'COMMITTED', 'currency': 'KRW'},
                         dict(requests('participation')[0]['arguments']['source_view'], durable=0)):
            row = requests('participation')[0]
            row['arguments']['source_view'] = snapshot
            status, calls, output, errors = self.guided_drive(answers(row) + ['quit'])
            self.assertEqual((status, calls, errors), (1, [row], ''))
            self.parity(calls, output)

    def test_source_incomplete_no_dispatch(self):
        rows = [r for r in mutation_examples() if 'source_view' in r['arguments']]
        for row in rows:
            lines = guided_answers(row, guided=('source_view',))
            status, calls, output, errors = self.guided_drive(
                guided_answers(row, 'no', guided=('source_view',)) + ['quit'])
            self.assertEqual((status, calls, errors), (0, [], ''))
            self.assertEqual(printed('proposed', output), [row])
            for cut in range(1, len(lines)):
                with self.subTest(operation=row['operation'], cut=cut):
                    status, calls, output, errors = self.guided_drive(lines[:cut])
                    self.assertEqual((status, calls, printed('desk', output)), (2, [], []))
                    self.assertIn('EOFError', errors)
            start = lines.index(':guided') + 1
            cases = []
            for offset in range(2, 7):
                cases += [lines[:start + offset] + [bad] for bad in
                          ('', '0', '1', 'null', '"false"', '[]', '{}', 'False', '{')]
            extras = ('null', '[]', 'false', '1', '"text"', '{', '{"x":NaN}',
                      '{"x":1e9999}', '{"x":1,"x":2}', '{"x":"\\ud800"}')
            cases += [lines[:start + 7] + [bad] for bad in extras]
            cases += [lines[:start + 7] + [_canonical({k: row['arguments']['source_view'][k]})]
                      for k in SOURCE_FIELDS]  # Even identical collisions are refused.
            cases += [lines[:start] + ['\ud800', 'KRW'] + ['false'] * 5 + ['{}']]
            for invalid in cases:
                with self.subTest(operation=row['operation'], invalid=repr(invalid)):
                    status, calls, output, errors = self.guided_drive(invalid + ['quit'])
                    self.assertEqual((status, calls, errors), (0, [], ''))
                    self.assertIn('input_error=', output)
                    self.assertEqual(printed('proposed', output), [])

    def test_source_transcripts(self):
        for name, scenario, status in (('journey', 'participation', 0),
                                        ('cancellation', 'cancellation', 0),
                                        ('boundaries', 'boundaries', 1)):
            lines = (FIXTURES / ('reward_console_source_' + name + '.txt')).read_text(encoding='utf-8').splitlines()
            actual, calls, output, errors = self.guided_drive(lines)
            self.assertEqual((actual, calls, errors), (status, requests(scenario), ''))
            raw = self.guided_drive([v for r in requests(scenario) for v in answers(r)] + ['quit'])
            self.assertEqual(printed('desk', output), printed('desk', raw[2]))
            proposals = [r for r in requests(scenario) if r['operation'] not in READS]
            if name == 'boundaries':
                self.assertEqual(output.count('input_error='), 3)
                self.assertEqual(output.count('Declined; no request sent.'), 1)
                proposals.insert(0, requests(scenario)[0])
            self.assertEqual(printed('proposed', output), proposals)

    def test_guided_raw_envelope_parity(self):
        scenarios = [requests('participation'),
                     requests('unknown_pending') + requests('unknown_resolution'),
                     requests('participation')[:5] + mutation_examples()[-1:]]
        for rows in scenarios:
            raw = self.guided_drive([v for row in rows for v in answers(row)] + ['quit'])
            for mixed in (False, True):
                with self.subTest(mixed=mixed, scenario=rows[0]['arguments']['idempotency_key']):
                    lines = [v for i, row in enumerate(rows) for v in guided_answers(
                        row, guided=('approval_ref',) if mixed and i % 2 == 0
                        else ('reward_key', 'approval_ref'))]
                    status, calls, output, errors = self.guided_drive(lines + ['quit'])
                    self.assertEqual((status, calls, errors), (raw[0], rows, ''))
                    self.assertEqual(printed('proposed', output), printed('proposed', raw[2]))
                    self.assertEqual(printed('desk', output), printed('desk', raw[2]))
                    self.parity(calls, output)

    def test_guided_opaque_values_precision_and_prior_record(self):
        for prior in ('omit', None, 'prior|한글:e\u0301'):
            rows = requests('participation')[:4]
            rows[0]['arguments']['reward_key'].update(
                program='프로그램|:e\u0301', source_op_id='source|:雪', recipient='한글:|', kind='kind|:')
            for row in rows[1:]:
                row['arguments']['reward_id_value'] = reward_id(**rows[0]['arguments']['reward_key'])
            approval = rows[-1]['arguments']['approval_ref']
            approval.update(record_id='record|雪', authority_id='caller|authority',
                            scope_ref='scope:e\u0301',
                            evidence_refs=['second|雪', 'first:e\u0301', 'second|雪'])
            if prior != 'omit':
                approval['prior_record'] = prior
            raw = self.guided_drive([v for r in rows for v in answers(r)] + ['quit'])
            status, calls, output, errors = self.guided_drive(
                [v for r in rows for v in guided_answers(r)] + ['quit'])
            self.assertEqual((status, calls, errors), (0, rows, ''))
            self.assertEqual(raw[0], 0)
            self.assertEqual(printed('desk', output), printed('desk', raw[2]))
            self.assertEqual(printed('proposed', output), rows)
            self.parity(calls, output)
        row = requests('participation')[0]
        row['arguments']['reward_key']['program'] = '  caller|프로그램\t'
        raw = self.guided_drive(answers(row) + ['quit'])
        status, calls, output, errors = self.guided_drive(guided_answers(row) + ['quit'])
        self.assertEqual((status, calls, errors), (1, [row], ''))
        self.assertEqual(printed('desk', output), printed('desk', raw[2]))
        self.parity(calls, output)
        # Empty evidence and a caller AI actor reach the existing domain predicates.
        for change in ({'evidence_refs': []}, {'actor_type': 'AI'}, {'generation': -1},
                       {'generation': 2**80 + 1}, {'record_id': '  caller|雪  '},
                       {'evidence_refs': ['']}, {'actor_type': ''}):
            rows = requests('participation')[:4]
            rows[-1]['arguments']['approval_ref'].update(change)
            raw = self.guided_drive([v for r in rows for v in answers(r)] + ['quit'])
            status, calls, output, errors = self.guided_drive(
                [v for r in rows for v in guided_answers(r)] + ['quit'])
            self.assertEqual((status, calls, errors), (1, rows, ''))
            self.assertEqual(printed('desk', output), printed('desk', raw[2]))
            self.parity(calls, output)

    def test_guided_fixture_transcripts(self):
        for name, scenario, expected in (('journey', 'participation', 0), ('boundaries', 'boundaries', 1)):
            text = (FIXTURES / ('reward_console_guided_' + name + '.txt')).read_text(encoding='utf-8')
            status, calls, output, errors = self.guided_drive(text.splitlines())
            self.assertEqual((status, calls, errors), (expected, requests(scenario), ''))
            raw = self.guided_drive([v for r in requests(scenario) for v in answers(r)] + ['quit'])
            self.assertEqual(printed('desk', output), printed('desk', raw[2]))
            if name == 'boundaries':
                self.assertEqual(output.count('input_error='), 3)
                self.assertEqual(output.count('Declined; no request sent.'), 1)

    def test_guided_decline_invalid_and_eof_no_dispatch(self):
        rows = [requests('participation')[0], requests('participation')[3], mutation_examples()[-1]]
        rows[-1]['arguments']['approval_ref']['prior_record'] = 'explicit-prior'
        for row in rows:
            lines = guided_answers(row)
            status, calls, output, errors = self.guided_drive(guided_answers(row, 'no') + ['quit'])
            self.assertEqual((status, calls, errors), (0, [], ''))
            self.assertEqual(printed('proposed', output), [row])
            for cut in range(len(lines)):
                with self.subTest(operation=row['operation'], cut=cut):
                    status, calls, output, errors = self.guided_drive(lines[:cut])
                    self.assertEqual((status, calls, printed('desk', output)), (2, [], []))
                    self.assertIn('EOFError', errors)
        for lines in invalid_guided_inputs():
            with self.subTest(invalid=repr(lines)):
                status, calls, output, errors = self.guided_drive(lines + ['quit'])
                self.assertEqual((status, calls, errors), (0, [], ''))
                self.assertIn('input_error=', output)
                self.assertNotIn('proposed=', output)


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


class RewardConsoleTests(GuidedCompositionTests, unittest.TestCase):
    def guided_drive(self, lines):
        return self.drive(lines)

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
        pending = iter(guided_answers(row) + ['quit'])
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


class RewardGuidedInitializationTests(unittest.TestCase):
    def drive(self, text, *, output=None, input_stream=None):
        from reward_console import run_guided_console
        output = io.StringIO() if output is None else output
        errors = io.StringIO()
        status = run_guided_console(cleanup_timeout=1,
            input_stream=io.StringIO(text) if input_stream is None else input_stream,
            output_stream=output, error_stream=errors)
        return status, output.getvalue(), errors.getvalue()

    def test_every_opening_prompt_and_confirmation_eof_launches_nothing(self):
        lines = ['0', '0', '0', '500', '500', 'SUBMIT']
        with patch('reward_console.RewardClient.launch_from_fixture') as launch, \
                patch('reward_client.subprocess.Popen') as popen:
            for count in range(len(lines)):
                status, _, errors = self.drive('\n'.join(lines[:count]) + ('\n' if count else ''))
                self.assertEqual(status, 2)
                self.assertIn('EOFError', errors)
            launch.assert_not_called()
            popen.assert_not_called()

    def test_invalid_values_and_declines_do_not_start_child(self):
        from token_reward_model import MONEY_MAX
        with patch('reward_console.RewardClient.launch_from_fixture') as launch, \
                patch('reward_client.subprocess.Popen') as popen:
            for pool_index in range(5):
                for invalid in ('', 'true', 'false', '-1', str(MONEY_MAX + 1), '0.0', 'null',
                                '"0"', '{}', 'NaN', '1e999', '{"x":0,"x":0}'):
                    lines = ['0'] * 5
                    lines[pool_index] = invalid
                    status, output, errors = self.drive('\n'.join(lines + ['SUBMIT', 'pool_view', 'quit']) + '\n')
                    self.assertEqual(status, 2, (pool_index, invalid, output, errors))
            for decline in ('no', 'submit', ' SUBMIT', 'SUBMIT ', ''):
                status, output, errors = self.drive('0\n0\n0\n0\n0\n' + decline + '\n')
                self.assertEqual((status, errors), (0, ''))
                self.assertIn('Initialization declined', output)
                self.assertEqual(printed('initialization', output)[0]['opening_balances'], {
                    'CUSTOMER_DEPOSIT': 0, 'ORGANIZER_SETTLEMENT': 0, 'REFUND_RESERVE': 0,
                    'PROTOCOL_REVENUE': 0, 'TOKEN_TREASURY_REWARD': 0})
            launch.assert_not_called()
            popen.assert_not_called()

    def test_preview_flush_and_input_failures_never_launch(self):
        class FailedPreview(io.StringIO):
            def flush(self):
                if 'initialization=' in self.getvalue():
                    raise OSError('preview flush failed')
                return super().flush()
        class FailedInput:
            def readline(self):
                raise KeyboardInterrupt('caller interrupted')
        with patch('reward_console.RewardClient.launch_from_fixture') as launch:
            self.assertEqual(self.drive('0\n0\n0\n0\n0\nSUBMIT\n', output=FailedPreview())[0], 2)
            self.assertEqual(self.drive('', input_stream=FailedInput())[0], 2)
            launch.assert_not_called()

    def test_full_preview_is_flushed_before_literal_confirmation_and_launch(self):
        from token_reward_model import MONEY_MAX
        expected = {'fixture_version': 1, 'provenance': PROVENANCE, 'opening_balances': {
            'CUSTOMER_DEPOSIT': 0, 'ORGANIZER_SETTLEMENT': MONEY_MAX, 'REFUND_RESERVE': 2,
            'PROTOCOL_REVENUE': 3, 'TOKEN_TREASURY_REWARD': 4}}
        output = io.StringIO()
        pending = iter(['0', str(MONEY_MAX), '2', '3', '4', 'SUBMIT', 'quit'])
        from unittest.mock import Mock
        client = Mock()
        client.initialized_reply = {'operation': 'initialize', 'provenance': PROVENANCE,
                                    'initialized': expected}
        client.close.return_value = 0
        class CheckedInput:
            def readline(inner):
                value = next(pending)
                if value == 'SUBMIT':
                    self.assertEqual(printed('initialization', output.getvalue()), [expected])
                    self.assertGreater(output.flush.call_count, 0)
                    launch.assert_not_called()
                return value + '\n'
        with patch.object(output, 'flush', wraps=output.flush), \
                patch('reward_console.RewardClient.launch_from_fixture', return_value=client) as launch:
            status, text, errors = self.drive('', input_stream=CheckedInput(), output=output)
        self.assertEqual((status, errors), (0, ''))
        launch.assert_called_once_with(expected, cleanup_timeout=1)
        self.assertEqual(printed('initialized', text), [client.initialized_reply])
        client.request.assert_not_called()
        client.close.assert_called_once()

    def test_guided_options_and_invalid_cleanup_are_prelaunch_errors(self):
        options = [[], ['--mode', 'in-process'], ['--mode', 'subprocess'],
                   ['--fixture', str(FIXTURE), '--mode', 'subprocess', '--cleanup-timeout', '1']]
        with patch('reward_console.RewardClient.launch_from_fixture') as launch, \
                patch('reward_console.load_fixture') as load, \
                patch('sys.stderr', io.StringIO()), patch('sys.stdin', io.StringIO()) as input_stream:
            for opts in options:
                with self.assertRaises(SystemExit) as error:
                    main(['--guided-init'] + opts)
                self.assertEqual(error.exception.code, 2)
            for value in ('0', '-1', 'nan', 'inf'):
                self.assertEqual(main(['--guided-init', '--mode', 'subprocess',
                                       '--cleanup-timeout=' + value]), 2)
            self.assertEqual(input_stream.tell(), 0)
            launch.assert_not_called()
            load.assert_not_called()

    def test_startup_uncertainty_stops_queued_business_actions_and_retains_phase(self):
        from reward_client import RewardTransportUncertainty
        fixture = json.loads(FIXTURE.read_text())
        error = RewardTransportUncertainty(fixture, (_canonical(fixture) + '\n').encode(),
                                           b'{', phase='initialize')
        error.__cause__ = OSError('lost startup acknowledgement')
        with patch('reward_console.RewardClient.launch_from_fixture', side_effect=error) as launch:
            status, output, errors = self.drive('0\n0\n0\n500\n500\nSUBMIT\npool_view\nquit\n')
        self.assertEqual(status, 2)
        self.assertNotIn('Actions:', output)
        self.assertNotIn('desk=', output)
        self.assertIn('"phase":"initialize"', errors)
        self.assertIn('lost startup acknowledgement', errors)
        launch.assert_called_once()


if __name__ == '__main__':
    unittest.main()
