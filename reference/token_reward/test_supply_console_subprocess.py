"""Runnable file-free terminal journeys, UTF-8, exits and import inactivity."""

import os
from pathlib import Path
import subprocess
import sys
import unittest

from reward_fixture import decode_json
from supply_reconciliation import dispatch_request
from test_supply_reconciliation import fixture
from token_reward_model import _canonical


ROOT = Path(__file__).resolve().parent


class SupplyConsoleSubprocessTests(unittest.TestCase):
    mode_args = ()

    def run_console(self, data=b'', *args):
        return subprocess.run([sys.executable, str(ROOT / 'supply_console.py'), *self.mode_args, *args],
                              input=data, capture_output=True, timeout=10,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def test_runnable_fixture_transcripts_match_complete_dispatcher_replies(self):
        for name in ('match', 'holder_burn', 'unexplained', 'unapproved_mint',
                     'unapproved_path', 'both_causes'):
            with self.subTest(name=name):
                process = self.run_console((ROOT / 'fixtures' / f'supply_console_{name}.txt').read_bytes())
                self.assertEqual(process.returncode, 0, process.stderr)
                request = fixture(name)
                report_request = {'operation': 'supply_report', 'arguments': {
                    'events': request['arguments']['offchain']['events']}}
                expected = [dispatch_request(report_request), dispatch_request(request)]
                self.assertEqual(process.stdout.decode('utf-8'),
                                 ''.join(_canonical(value) + '\n' for value in expected))
                self.assertIn(b'proposed=', process.stderr)
                for label in (b'MOCK_TOKEN_REWARD_ONLY', b'CALCULATION_ONLY', b'SYNTHETIC_SUPPLY_FIGURE'):
                    self.assertIn(label, process.stderr)

    def test_duplicate_conservation_and_declined_boundary_transcripts(self):
        for name, code in (('duplicate', 'SUPPLY_EVENT_DUPLICATE'),
                           ('conservation', 'SUPPLY_CONSERVATION')):
            process = self.run_console((ROOT / 'fixtures' / f'supply_console_{name}.txt').read_bytes())
            self.assertEqual(process.returncode, 1, process.stderr)
            self.assertEqual(len(process.stdout.splitlines()), 1)
            self.assertEqual(decode_json(process.stdout.decode())['error'], {'code': code})
        process = self.run_console((ROOT / 'fixtures' / 'supply_console_boundaries.txt').read_bytes())
        self.assertEqual((process.returncode, process.stdout), (0, b''), process.stderr)

    def test_unicode_crlf_and_no_trimming(self):
        data = (ROOT / 'fixtures' / 'supply_console_match.txt').read_text(encoding='utf-8')
        process = self.run_console(data.replace('mint-1', '합성-민팅').replace('\n', '\r\n').encode('utf-8'))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn('합성-민팅', process.stdout.decode('utf-8'))
        process = self.run_console(b'add_event\n spaced\nMINT\n1\ntrue\ntrue\n"p"\nquit\n')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(decode_json(process.stdout.decode())['error'], {'code': 'INVALID_ID'})

    def test_eof_and_invalid_utf8_before_confirmation_emit_no_results(self):
        for data in (b'', b'replace_events\n0\ncalculate\n', b'\xff\n',
                     b'replace_events\n0\ncalculate\n\xff\n'):
            with self.subTest(data=data):
                process = self.run_console(data)
                self.assertEqual((process.returncode, process.stdout), (2, b''))
                self.assertIn(b'terminal_error=', process.stderr)
        # A later invalid line does not consume/retry a prior confirmed calculation.
        process = self.run_console(b'replace_events\n0\ncalculate\nCALCULATE\n\xff\n')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(len(process.stdout.splitlines()), 1)
        self.assertIn('result', decode_json(process.stdout.decode()))

    def test_usage_and_import_start_nothing(self):
        for args in (('--request', '-'), ('--chain', '0'), ('extra',)):
            process = self.run_console(b'', *args)
            self.assertEqual((process.returncode, process.stdout), (2, b''))
            self.assertIn(b'usage:', process.stderr)
        process = subprocess.run([sys.executable, '-c', 'import supply_console, supply_client'], cwd=ROOT,
                                 capture_output=True, timeout=10,
                                 env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual((process.returncode, process.stdout, process.stderr), (0, b'', b''))


class SupplyConsoleLiveSubprocessTests(SupplyConsoleSubprocessTests):
    # Replay every existing terminal regression across the real CLI boundary.
    mode_args = ('--mode', 'subprocess', '--cleanup-timeout', '1')

    def test_explicit_mode_usage_errors(self):
        for args in (('--mode', 'subprocess'),
                     ('--mode', 'subprocess', '--cleanup-timeout', '0'),
                     ('--mode', 'subprocess', '--cleanup-timeout', 'nan'),
                     ('--mode', 'subprocess', '--cleanup-timeout', 'inf'),
                     ('--mode', 'in-process', '--cleanup-timeout', '1')):
            process = subprocess.run([sys.executable, str(ROOT / 'supply_console.py'), *args],
                                     input=b'quit\n', capture_output=True, timeout=10)
            self.assertEqual((process.returncode, process.stdout), (2, b''))
            self.assertIn(b'usage:', process.stderr)


if __name__ == '__main__':
    unittest.main()
