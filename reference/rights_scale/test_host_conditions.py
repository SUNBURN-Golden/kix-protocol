"""Offline checks for host_conditions.py.

Synthetic /proc text, a synthetic proc directory and synthetic JSONL only (one
with an injected clock gap shaped like a ~6.8 h VM suspend). Nothing here reads
the real host's load or memory as a value, runs a load or touches a localnet.
"""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import host_conditions  # noqa: E402

LOADAVG = '14.50 8.25 3.00 5/1234 98765\n'
MEMINFO = ('MemTotal:       16384000 kB\n'
           'MemFree:          100000 kB\n'
           'MemAvailable:     524288 kB\n'
           'SwapTotal:       2097152 kB\n'
           'SwapFree:        1048576 kB\n'
           'HugePages_Total:       0\n')
UPTIME = '12345.67 98765.43\n'
STAT = 'cpu  1 2 3 4 5 6 7 8 9 10\ncpu0 1 2 3 4 5 6 7 8 9 10\nbtime 1792600000\nprocesses 99\n'

INTERVAL = 5.0
EPOCH0 = 1792638000.0
FORBIDDEN_KEYS = {'verdict', 'status', 'pass', 'ok', 'quiet', 'idle'}


def _sample(i, wall=None, mono=None, load1=1.0, avail=1000, cores=8, cpu=8, **extra):
    wall = EPOCH0 + i * INTERVAL if wall is None else wall
    sample = {
        'v': host_conditions.SAMPLE_VERSION,
        'wall_utc': host_conditions._utc(wall), 'wall_epoch_s': wall,
        'mono_s': 100.0 + i * INTERVAL if mono is None else mono,
        'loadavg': {'load1': load1, 'load5': load1 / 2, 'load15': load1 / 4,
                    'runnable': 1, 'total_threads': 100, 'last_pid': 1},
        'mem': {'mem_total_bytes': 8000, 'mem_available_bytes': avail,
                'swap_total_bytes': 500, 'swap_free_bytes': 400},
        'uptime_s': 1000.0 + i * INTERVAL, 'idle_s': 0.0, 'btime': 1792600000,
        'cpu_count': cpu, 'affinity_cores': cores, 'errors': {}}
    sample.update(extra)
    return sample


def _write_jsonl(path, samples):
    path.write_text(''.join(json.dumps(s) + '\n' for s in samples))


def _keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from _keys(item)


def _run(*args):
    return subprocess.run([sys.executable, str(HERE / 'host_conditions.py'), *args],
                          capture_output=True, text=True)


class TestParsers(unittest.TestCase):
    def test_parse_loadavg(self):
        self.assertEqual(host_conditions.parse_loadavg(LOADAVG), {
            'load1': 14.5, 'load5': 8.25, 'load15': 3.0,
            'runnable': 5, 'total_threads': 1234, 'last_pid': 98765})

    def test_parse_loadavg_malformed(self):
        for text in ('', '1 2 3', '1 2 3 x 4', 'a b c 1/2 3', '1 2 3 1/b 4'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                host_conditions.parse_loadavg(text)

    def test_parse_meminfo_bytes(self):
        self.assertEqual(host_conditions.parse_meminfo(MEMINFO), {
            'mem_total_bytes': 16384000 * 1024, 'mem_available_bytes': 524288 * 1024,
            'swap_total_bytes': 2097152 * 1024, 'swap_free_bytes': 1048576 * 1024})

    def test_parse_meminfo_missing_key_is_none(self):
        parsed = host_conditions.parse_meminfo('MemTotal: 10 kB\nSwapFree: 4 kB\n')
        self.assertEqual(parsed['mem_total_bytes'], 10240)
        self.assertIsNone(parsed['mem_available_bytes'])
        self.assertEqual(parsed['swap_free_bytes'], 4096)

    def test_parse_meminfo_malformed_wanted_value(self):
        for text in ('MemAvailable: lots kB\n', 'MemAvailable:\n', 'MemAvailable: 5 MB\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                host_conditions.parse_meminfo(text)

    def test_parse_uptime(self):
        self.assertEqual(host_conditions.parse_uptime(UPTIME),
                         {'uptime_s': 12345.67, 'idle_s': 98765.43})
        for text in ('', '1', '1 2 3', 'a b'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                host_conditions.parse_uptime(text)

    def test_parse_stat_btime(self):
        self.assertEqual(host_conditions.parse_stat_btime(STAT), 1792600000)
        self.assertIsNone(host_conditions.parse_stat_btime('cpu 1 2\n'))
        with self.assertRaises(ValueError):
            host_conditions.parse_stat_btime('btime soon\n')


class TestSampler(unittest.TestCase):
    def _proc(self, root, **overrides):
        files = {'loadavg': LOADAVG, 'meminfo': MEMINFO, 'uptime': UPTIME, 'stat': STAT}
        files.update(overrides)
        for name, text in files.items():
            if text is not None:
                (root / name).write_text(text)
        return root

    def test_read_sample_from_synthetic_proc_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self._proc(Path(tmp))
            with mock.patch.object(host_conditions, 'affinity_cores', return_value=6), \
                    mock.patch.object(host_conditions.os, 'cpu_count', return_value=8):
                sample = host_conditions.read_sample(proc, now=(1792638000.5, 77.0))
        self.assertEqual(sample['v'], 'kix-rs4-host-conditions-sample-v1')
        self.assertEqual(sample['wall_utc'], '2026-10-22T03:00:00.500Z')
        self.assertEqual(sample['wall_epoch_s'], 1792638000.5)
        self.assertEqual(sample['mono_s'], 77.0)
        self.assertEqual(sample['loadavg']['load1'], 14.5)
        self.assertEqual(sample['mem']['mem_available_bytes'], 524288 * 1024)
        self.assertEqual(sample['mem']['swap_free_bytes'], 1048576 * 1024)
        self.assertEqual((sample['uptime_s'], sample['idle_s']), (12345.67, 98765.43))
        self.assertEqual(sample['btime'], 1792600000)
        self.assertEqual((sample['cpu_count'], sample['affinity_cores']), (8, 6))
        self.assertEqual(sample['errors'], {})
        json.dumps(sample)

    def test_read_sample_missing_file_records_error_not_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self._proc(Path(tmp), meminfo=None, uptime='garbage')
            sample = host_conditions.read_sample(proc)
        self.assertIsNone(sample['mem']['mem_available_bytes'])
        self.assertIsNone(sample['uptime_s'])
        self.assertEqual(set(sample['errors']), {'meminfo', 'uptime'})
        self.assertEqual(sample['loadavg']['load1'], 14.5)
        self.assertEqual(sample['btime'], 1792600000)

    def test_affinity_unavailable_is_none(self):
        with mock.patch.object(host_conditions.os, 'sched_getaffinity',
                               side_effect=OSError, create=True):
            self.assertIsNone(host_conditions.affinity_cores())

    def test_sample_loop_writes_count_lines_and_appends(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp) / 'proc'
            proc.mkdir()
            self._proc(proc)
            out = Path(tmp) / 'sub' / 'host-conditions.jsonl'
            self.assertEqual(host_conditions.sample_loop(out, 0.01, count=3, proc=proc), 3)
            self.assertEqual(host_conditions.sample_loop(out, 0.01, count=2, proc=proc), 2)
            lines = out.read_text().splitlines()
        self.assertEqual(len(lines), 5)
        walls = [json.loads(line)['wall_epoch_s'] for line in lines]
        self.assertEqual(walls, sorted(walls))

    def test_sample_loop_stops_on_event(self):
        stop = threading.Event()
        stop.set()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'a.jsonl'
            self.assertEqual(host_conditions.sample_loop(out, 60, stop=stop), 0)
            self.assertEqual(out.read_text(), '')

    def test_sample_loop_stop_during_wait_returns_promptly(self):
        stop = threading.Event()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'a.jsonl'
            timer = threading.Timer(0.2, stop.set)
            timer.start()
            written = host_conditions.sample_loop(out, 3600, stop=stop)
            timer.join()
        self.assertEqual(written, 1)

    @unittest.skipUnless(Path('/proc/loadavg').exists(), 'needs Linux /proc')
    def test_read_sample_on_this_host_does_not_raise(self):
        # Only that a dict comes back; no value is asserted or recorded.
        self.assertIsInstance(host_conditions.read_sample(), dict)


class TestSummary(unittest.TestCase):
    def test_summary_load_stats_raw_and_per_core(self):
        samples = [_sample(0, load1=8.0), _sample(1, load1=16.0), _sample(2, load1=80.0)]
        summary = host_conditions.summarize(samples, INTERVAL, 3)
        self.assertEqual(summary['loadavg']['load1'],
                         {'n': 3, 'min': 8.0, 'median': 16.0, 'max': 80.0})
        self.assertEqual(summary['loadavg']['load1_per_core'],
                         {'n': 3, 'min': 1.0, 'median': 2.0, 'max': 10.0})
        self.assertEqual(summary['loadavg']['load5_per_core'],
                         {'n': 3, 'min': 0.5, 'median': 1.0, 'max': 5.0})
        self.assertEqual(summary['loadavg']['load15_per_core']['max'], 2.5)

    def test_per_core_uses_affinity_not_cpu_count(self):
        summary = host_conditions.summarize([_sample(0, load1=8.0, cores=2, cpu=8)],
                                            INTERVAL, 3)
        self.assertEqual(summary['loadavg']['load1_per_core']['max'], 4.0)

    def test_per_core_falls_back_to_cpu_count(self):
        summary = host_conditions.summarize(
            [_sample(0, load1=8.0, cores=None, cpu=4)], INTERVAL, 3)
        self.assertEqual(summary['loadavg']['load1_per_core']['max'], 2.0)

    def test_per_core_absent_without_any_core_count(self):
        summary = host_conditions.summarize(
            [_sample(0, load1=8.0, cores=None, cpu=None)], INTERVAL, 3)
        self.assertIsNone(summary['loadavg']['load1_per_core'])
        self.assertEqual(summary['loadavg']['load1']['max'], 8.0)

    def test_summary_min_mem_available(self):
        samples = [_sample(0, avail=900), _sample(1, avail=120), _sample(2, avail=5000)]
        mem = host_conditions.summarize(samples, INTERVAL, 3)['mem']
        self.assertEqual(mem['mem_available_bytes'],
                         {'n': 3, 'min': 120, 'median': 900, 'max': 5000})
        self.assertEqual(mem['swap_free_bytes']['min'], 400)

    def test_injected_gap_is_reported(self):
        hole = 24480.0   # about 6.8 h
        samples = [_sample(i) for i in range(5)]
        samples += [_sample(i, wall=EPOCH0 + i * INTERVAL + hole,
                            mono=100.0 + i * INTERVAL + 1.0) for i in range(5, 10)]
        summary = host_conditions.summarize(samples, INTERVAL, 3)
        self.assertEqual(summary['clock_gap_count'], 1)
        gap = summary['clock_gaps'][0]
        self.assertEqual(gap['index'], 5)
        self.assertEqual(gap['wall_gap_s'], INTERVAL + hole)
        self.assertEqual(gap['threshold_s'], 15.0)
        self.assertEqual(gap['mono_gap_s'], INTERVAL + 1.0)
        self.assertEqual(gap['prev_wall_utc'], samples[4]['wall_utc'])
        self.assertEqual(gap['next_wall_utc'], samples[5]['wall_utc'])
        self.assertEqual(summary['largest_wall_gap_s'], INTERVAL + hole)
        self.assertEqual(summary['sample_count'], 10)
        self.assertEqual(summary['span_s'], 9 * INTERVAL + hole)

    def test_no_gap_when_within_factor(self):
        samples = [_sample(0), _sample(1, wall=EPOCH0 + 15.0)]
        # exactly gap_factor x interval is not "exceeding"
        self.assertEqual(host_conditions.summarize(samples, INTERVAL, 3)['clock_gaps'], [])
        samples[1] = _sample(1, wall=EPOCH0 + 15.001)
        self.assertEqual(
            len(host_conditions.summarize(samples, INTERVAL, 3)['clock_gaps']), 1)

    def test_backward_wall_step_is_counted_not_a_gap(self):
        samples = [_sample(0), _sample(1, wall=EPOCH0 - 100.0)]
        summary = host_conditions.summarize(samples, INTERVAL, 3)
        self.assertEqual(summary['clock_gap_count'], 0)
        self.assertEqual(summary['wall_clock_backward_steps'], 1)

    def test_btime_and_uptime_regressions(self):
        samples = [_sample(0), _sample(1, btime=1792600500, uptime_s=2.0), _sample(2)]
        summary = host_conditions.summarize(samples, INTERVAL, 3)
        self.assertEqual(summary['btime_values'], [1792600000, 1792600500])
        self.assertEqual(summary['uptime_regressions'], 1)

    def test_samples_with_errors_counted_and_none_values_tolerated(self):
        broken = _sample(1, loadavg=None, mem={'mem_available_bytes': None},
                         errors={'loadavg': 'x'})
        summary = host_conditions.summarize([_sample(0), broken, _sample(2)], INTERVAL, 3)
        self.assertEqual(summary['samples_with_errors'], 1)
        self.assertEqual(summary['loadavg']['load1']['n'], 2)
        self.assertEqual(summary['mem']['mem_available_bytes']['n'], 2)

    def test_summary_has_no_verdict_keys(self):
        samples = [_sample(0), _sample(1, wall=EPOCH0 + 9999.0, load1=500.0)]
        summary = host_conditions.summarize(samples, INTERVAL, 3)
        self.assertEqual(FORBIDDEN_KEYS & set(_keys(summary)), set())
        self.assertIn('UNDETERMINED (User)', summary['note'])
        self.assertIs(summary['exploration_data'], True)

    def test_empty_gives_zero_count_and_null_stats(self):
        summary = host_conditions.summarize([], INTERVAL, 3)
        self.assertEqual(summary['sample_count'], 0)
        self.assertIsNone(summary['loadavg']['load1'])
        self.assertIsNone(summary['loadavg']['load1_per_core'])
        self.assertIsNone(summary['mem']['mem_available_bytes'])
        self.assertIsNone(summary['span_s'])
        self.assertEqual(summary['clock_gaps'], [])
        self.assertEqual(summary['clock_gap_count'], 0)

    def test_single_sample_has_no_gap(self):
        summary = host_conditions.summarize([_sample(0)], INTERVAL, 3)
        self.assertEqual(summary['clock_gap_count'], 0)
        self.assertEqual(summary['span_s'], 0.0)
        self.assertIsNone(summary['largest_wall_gap_s'])


class TestLoadSamples(unittest.TestCase):
    def test_blank_lines_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 's.jsonl'
            path.write_text(json.dumps(_sample(0)) + '\n\n   \n' + json.dumps(_sample(1)) + '\n')
            self.assertEqual(len(host_conditions.load_samples(path)), 2)

    def test_malformed_inputs_exit(self):
        bad = ['{not json', '[1, 2]', '{"wall_epoch_s": "soon"}', '{"x": 1}',
               '{"wall_epoch_s": true}']
        for text in bad:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 's.jsonl'
                path.write_text(text + '\n')
                with self.assertRaises(SystemExit) as ctx:
                    host_conditions.load_samples(path)
                self.assertTrue(str(ctx.exception).startswith('UNREADABLE_INPUT'))

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            host_conditions.load_samples('/nonexistent/host-conditions.jsonl')


class TestCli(unittest.TestCase):
    def test_summarize_writes_summary_file_beside_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'host-conditions.jsonl'
            _write_jsonl(path, [_sample(0, avail=700), _sample(1, avail=300),
                                _sample(2, wall=EPOCH0 + 24480.0)])
            result = _run('summarize', '--samples', str(path),
                          '--interval', '5', '--gap-factor', '3')
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((Path(tmp) / 'host-conditions-summary.json').read_text())
            digest = json.loads(result.stdout)
        self.assertEqual(summary['version'], 'kix-rs4-host-conditions-summary-v1')
        self.assertEqual(summary['clock_gap_count'], 1)
        self.assertEqual(digest['sample_count'], 3)
        self.assertEqual(digest['clock_gap_count'], 1)
        self.assertEqual(digest['min_mem_available_bytes'], 300)

    def test_summarize_explicit_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 's.jsonl'
            _write_jsonl(path, [_sample(0)])
            out = Path(tmp) / 'deep' / 'x.json'
            result = _run('summarize', '--samples', str(path), '--interval', '5',
                          '--gap-factor', '2', '--out', str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(out.read_text())['gap_factor'], 2.0)

    def test_malformed_jsonl_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 's.jsonl'
            path.write_text('{oops\n')
            result = _run('summarize', '--samples', str(path),
                          '--interval', '5', '--gap-factor', '3')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('UNREADABLE_INPUT', result.stderr)
            self.assertFalse((Path(tmp) / 'host-conditions-summary.json').exists())

    def test_interval_and_gap_factor_are_required_and_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 's.jsonl'
            _write_jsonl(path, [_sample(0)])
            for args in (['--gap-factor', '3'], ['--interval', '5'],
                         ['--interval', '0', '--gap-factor', '3'],
                         ['--interval', '5', '--gap-factor', '-1']):
                with self.subTest(args=args):
                    result = _run('summarize', '--samples', str(path), *args)
                    self.assertEqual(result.returncode, 2)
        self.assertEqual(_run('sample', '--out', 'x').returncode, 2)

    def test_sample_cli_with_synthetic_proc(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp) / 'proc'
            proc.mkdir()
            for name, text in (('loadavg', LOADAVG), ('meminfo', MEMINFO),
                               ('uptime', UPTIME), ('stat', STAT)):
                (proc / name).write_text(text)
            out = Path(tmp) / 'host-conditions.jsonl'
            result = _run('sample', '--out', str(out), '--interval', '0.01',
                          '--count', '4', '--proc', str(proc))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['samples_written'], 4)
            samples = host_conditions.load_samples(out)
        self.assertEqual(len(samples), 4)
        self.assertEqual({s['loadavg']['load1'] for s in samples}, {14.5})

    def test_sample_cli_stops_cleanly_on_sigterm(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'host-conditions.jsonl'
            proc = subprocess.Popen(
                [sys.executable, str(HERE / 'host_conditions.py'), 'sample',
                 '--out', str(out), '--interval', '3600'],
                stdout=subprocess.PIPE, text=True)
            try:
                for _ in range(100):
                    if out.exists() and out.read_text().count('\n') >= 1:
                        break
                    threading.Event().wait(0.1)
                proc.terminate()
                stdout, _ = proc.communicate(timeout=10)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(json.loads(stdout)['samples_written'], 1)
            self.assertEqual(len(host_conditions.load_samples(out)), 1)


class TestModuleHygiene(unittest.TestCase):
    def test_imports_only_stdlib(self):
        import ast
        tree = ast.parse((HERE / 'host_conditions.py').read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split('.')[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or '').split('.')[0])
        self.assertLessEqual(names, set(sys.stdlib_module_names))


if __name__ == '__main__':
    unittest.main()
