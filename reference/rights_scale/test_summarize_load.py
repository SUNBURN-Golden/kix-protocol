"""Source-informed offline checks for summarize_load.py.

Builds a synthetic report from the generator's own expected end-state (no
localnet) and checks the pass/fail rules: page conservation, full sample
coverage, shield-count shortfall, and unknown probe branches.
Small synthetic fixtures also characterize summary arithmetic and CSV encoding
with independently calculated literal expectations. Mixed-outcome service
statistics are not successful-purchase latency or performance measurements.
"""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import load_plan  # noqa: E402
import summarize_load  # noqa: E402


def _page(index, counts):
    start = index * load_plan.PAGE_SIZE
    end = min(start + load_plan.PAGE_SIZE, load_plan.SEATS)
    occupied = counts['reserved'] + counts['issued'] + counts['retired']
    return {'index': index, 'start': start, 'end': end, 'free': counts['free'],
            'reserved': counts['reserved'], 'issued': counts['issued'],
            'retired': counts['retired'], 'occupied': occupied, 'delegated_to': None}


def _snapshot(name, expected):
    pages = []
    for key, counts in expected['pages'].items():
        pages.append(_page(int(key), counts))
    pages.sort(key=lambda p: p['index'])
    snap = {'pages': pages, 'grants': [], 'private': {'zk_enabled': False}}
    if name == 'private':
        snap['private'] = {
            'zk_enabled': True,
            'leaf_count': expected['leaf_count'],
            'nullifiers': expected['nullifiers'],
            'challenges': expected['challenges'],
            'revocations': expected['revocations'],
            'cacheNoteRootMatch': True,
            'cacheRevocationRootMatch': True,
        }
    if name == 'delegated':
        snap['grants'] = [
            {'label': label, 'id': '0x' + label, 'open': state['open'],
             'generation': state['generation']}
            for label, state in expected['grants'].items()]
        bind = {int(k): v for k, v in expected['page_delegated_to'].items()}
        for page in pages:
            label = bind.get(page['index'])
            if page['index'] in bind:
                page['delegated_to'] = ('0x' + label) if label else None
    return snap


def _report(doc):
    samples = []
    for name, steps in doc['paths'].items():
        for step in steps:
            samples.append({'path': name, 'phase': step['phase'], 'seq': step['seq'],
                            'op': step['op'], 'outcome_kind': 'ok', 'expect': step['expect'],
                            'expect_mismatch': False, 'service_ms': 1, 'gas': None})
    # Shields are the coverage numerator. Mark them ok, which they already are.
    return {
        'samples': samples,
        'snapshots': {name: _snapshot(name, doc['expected'][name]) for name in doc['paths']},
        'requested': doc['requested'],
        'actual': {},
        'settings': doc['settings'],
    }


class TestSummarizeRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(json.dumps(load_plan.assign_phases(load_plan.expand(
            {'shield_count': 16, 'consume_count': 2, 'invalidation_count': 1}))))

    def test_matching_snapshot_passes(self):
        report = _report(self.doc)
        for name in self.doc['paths']:
            summary, _samples = summarize_load.summarize_path(
                name, report, self.doc['expected'], [])
            self.assertEqual(summary['status'], 'PASSED_MEASUREMENT', name)

    def test_page_divergence_fails(self):
        report = _report(self.doc)
        report['snapshots']['public']['pages'][0]['free'] += 1
        summary, _samples = summarize_load.summarize_path(
            'public', report, self.doc['expected'], [])
        self.assertEqual(summary['status'], 'FAILED_MEASUREMENT')

    def test_a_failed_path_is_reported_separately(self):
        # RS-C14: per-path results are reported separately; one path's
        # failure is not pooled into another path's verdict.
        report = _report(self.doc)
        report['snapshots']['public']['pages'][0]['free'] += 1
        for name in ('private', 'delegated'):
            summary, _samples = summarize_load.summarize_path(
                name, report, self.doc['expected'], [])
            self.assertEqual(summary['status'], 'PASSED_MEASUREMENT', name)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'report.json').write_text(json.dumps(report))
            (root / 'scenarios.json').write_text(json.dumps(self.doc))
            import subprocess
            result = subprocess.run(
                [sys.executable, str(HERE / 'summarize_load.py'),
                 '--report', str(root / 'report.json'),
                 '--scenarios', str(root / 'scenarios.json'),
                 '--out', str(root / 'out')],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads((root / 'out' / 'receipt.json').read_text())
            self.assertEqual(receipt['paths']['public']['status'], 'FAILED_MEASUREMENT')
            self.assertEqual(receipt['paths']['private']['status'], 'PASSED_MEASUREMENT')
            self.assertEqual(receipt['paths']['delegated']['status'], 'PASSED_MEASUREMENT')
            self.assertEqual(receipt['failed_paths'], ['public'])

    def test_unknown_branch_fails(self):
        report = _report(self.doc)
        probe = next(s for s in report['samples'] if s['op'] == 'parallel')
        probe['outcome_kind'] = 'probe'
        probe['branches'] = [{'outcome_kind': 'unknown', 'op': 'issue'}]
        summary, _samples = summarize_load.summarize_path(
            probe['path'], report, self.doc['expected'], [])
        self.assertEqual(summary['status'], 'FAILED_MEASUREMENT')
        self.assertEqual(summary['counts']['branch_unknowns'], 1)

    def test_main_records_shield_shortfall(self):
        report = _report(self.doc)
        for sample in report['samples']:
            if sample['op'] == 'shield':
                sample['outcome_kind'] = 'abort'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'report.json').write_text(json.dumps(report))
            (root / 'scenarios.json').write_text(json.dumps(self.doc))
            import subprocess
            result = subprocess.run(
                [sys.executable, str(HERE / 'summarize_load.py'),
                 '--report', str(root / 'report.json'),
                 '--scenarios', str(root / 'scenarios.json'),
                 '--out', str(root / 'out')],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads((root / 'out' / 'receipt.json').read_text())
            self.assertEqual(receipt['status'], 'FAILED_MEASUREMENT')
            self.assertTrue(receipt['coverage']['shortfalls'])


def _arithmetic_samples():
    # Omitted keys, nulls and measured zero deliberately differ by metric.
    return [
        {'path': 'public', 'op': 'issue', 'outcome_kind': 'ok',
         'service_ms': 10, 'build_ms': 0, 'proof_ms': None,
         'gas': {'computation': '9007199254740993',
                 'storage': '9007199254740997', 'rebate': '9007199254741001'}},
        {'path': 'public', 'op': 'issue', 'outcome_kind': 'abort',
         'service_ms': 30, 'proof_ms': 6, 'witness_ms': None,
         'gas': {'computation': '2', 'rebate': '0'}},
        {'path': 'public', 'op': 'issue', 'outcome_kind': 'client_refused',
         'service_ms': 0, 'build_ms': 4,
         'gas': {'computation': '0', 'storage': '0', 'rebate': None}},
        {'path': 'public', 'op': 'issue', 'outcome_kind': 'ok',
         'service_ms': None, 'build_ms': None, 'proof_ms': None, 'gas': None},
        {'path': 'public', 'op': 'issue', 'outcome_kind': 'abort'},
    ]


class TestSummaryArithmetic(unittest.TestCase):
    """Current aggregation behavior, not a new measurement contract."""

    def test_stats_fixed_cases(self):
        cases = [
            ([], None),
            ([None, None], None),
            ([7], {'n': 1, 'min': 7, 'max': 7, 'mean': 7,
                   'p50': 7, 'p95': 7, 'p99': 7}),
            ([None, 0], {'n': 1, 'min': 0, 'max': 0, 'mean': 0,
                         'p50': 0, 'p95': 0, 'p99': 0}),
            ([9, 1, 9, 3, 3], {'n': 5, 'min': 1, 'max': 9, 'mean': 5,
                               'p50': 3, 'p95': 9, 'p99': 9}),
            ([1, 2, 2], {'n': 3, 'min': 1, 'max': 2, 'mean': 1.67,
                         'p50': 2, 'p95': 2, 'p99': 2}),
        ]
        for values, expected in cases:
            with self.subTest(values=values):
                self.assertEqual(summarize_load.stats(values), expected)

    def test_nearest_rank_boundaries(self):
        # Hand-calculated one-based ranks; n=20/100 hit exact boundaries.
        cases = [
            (19, 10, 10, 19, 19),
            (20, 10.5, 10, 19, 20),
            (21, 11, 11, 20, 21),
            (99, 50, 50, 95, 99),
            (100, 50.5, 50, 95, 99),
            (101, 51, 51, 96, 100),
        ]
        for n, mean, p50, p95, p99 in cases:
            with self.subTest(n=n):
                self.assertEqual(summarize_load.stats(list(range(n, 0, -1))),
                                 {'n': n, 'min': 1, 'max': n, 'mean': mean,
                                  'p50': p50, 'p95': p95, 'p99': p99})

    def test_metric_specific_counts_and_mixed_outcomes(self):
        samples = _arithmetic_samples()
        summary, _ = summarize_load.summarize_path(
            'public', {'samples': samples}, {}, [])
        entry = summary['by_op']['issue']
        self.assertEqual(entry['outcomes'], {'ok': 2, 'abort': 2, 'client_refused': 1})
        # All measured outcomes contribute: (10 + 30 + 0)/3 = 13.33.
        self.assertEqual(entry['service_ms'],
                         {'n': 3, 'min': 0, 'max': 30, 'mean': 13.33,
                          'p50': 10, 'p95': 30, 'p99': 30})
        self.assertEqual(entry['build_ms'],
                         {'n': 2, 'min': 0, 'max': 4, 'mean': 2,
                          'p50': 0, 'p95': 4, 'p99': 4})
        self.assertEqual(entry['proof_ms'],
                         {'n': 1, 'min': 6, 'max': 6, 'mean': 6,
                          'p50': 6, 'p95': 6, 'p99': 6})
        self.assertIsNone(entry['witness_ms'])
        # The sole measured ok service is 10. Mixed p99=30 is not purchase p99.
        self.assertEqual([s['service_ms'] for s in samples
                          if s['outcome_kind'] == 'ok' and s.get('service_ms') is not None],
                         [10])

    def test_gas_totals_preserve_large_integers(self):
        samples = _arithmetic_samples() + [
            {'path': 'public', 'op': 'consume', 'outcome_kind': 'ok'},
            {'path': 'public', 'op': 'zero_gas', 'outcome_kind': 'ok',
             'gas': {'computation': '0', 'storage': '0', 'rebate': '0'}},
        ]
        summary, _ = summarize_load.summarize_path(
            'public', {'samples': samples}, {}, [])
        entry = summary['by_op']['issue']
        self.assertEqual(entry['gas_total'],
                         {'computation': 9007199254740995,
                          'storage': 9007199254740997, 'rebate': 9007199254741001})
        for value in entry['gas_total'].values():
            self.assertIs(type(value), int)
        self.assertEqual({k: v['n'] for k, v in entry['gas'].items()},
                         {'computation': 3, 'storage': 2, 'rebate': 2})
        # Integer extrema/percentiles stay exact; large float means are not an oracle.
        for metric, maximum in [('computation', 9007199254740993),
                                ('storage', 9007199254740997),
                                ('rebate', 9007199254741001)]:
            with self.subTest(metric=metric):
                self.assertEqual(entry['gas'][metric]['min'], 0)
                for field in ('max', 'p95', 'p99'):
                    self.assertEqual(entry['gas'][metric][field], maximum)
        self.assertEqual(summary['by_op']['consume']['gas'],
                         {'computation': None, 'storage': None, 'rebate': None})
        self.assertEqual(summary['by_op']['consume']['gas_total'], {})
        zero = {'n': 1, 'min': 0, 'max': 0, 'mean': 0, 'p50': 0, 'p95': 0, 'p99': 0}
        self.assertEqual(summary['by_op']['zero_gas']['gas'],
                         {'computation': zero, 'storage': zero, 'rebate': zero})
        self.assertEqual(summary['by_op']['zero_gas']['gas_total'],
                         {'computation': 0, 'storage': 0, 'rebate': 0})

    def test_path_and_operation_aggregates_are_distinct(self):
        samples = _arithmetic_samples()
        samples.insert(1, {'path': 'private', 'op': 'issue',
                           'outcome_kind': 'ok', 'service_ms': 101})
        samples.insert(3, {'path': 'delegated', 'op': 'issue',
                           'outcome_kind': 'ok', 'service_ms': 201})
        samples.insert(5, {'path': 'public', 'op': 'consume',
                           'outcome_kind': 'ok', 'service_ms': 301})
        summaries = {name: summarize_load.summarize_path(
            name, {'samples': samples}, {}, [])[0]
            for name in ('public', 'private', 'delegated')}
        self.assertEqual(set(summaries['public']['by_op']), {'issue', 'consume'})
        self.assertEqual(set(summaries['private']['by_op']), {'issue'})
        self.assertEqual(set(summaries['delegated']['by_op']), {'issue'})
        self.assertEqual(summaries['public']['by_op']['issue']['service_ms'],
                         {'n': 3, 'min': 0, 'max': 30, 'mean': 13.33,
                          'p50': 10, 'p95': 30, 'p99': 30})
        for path, op, value in [('private', 'issue', 101),
                                ('delegated', 'issue', 201),
                                ('public', 'consume', 301)]:
            with self.subTest(path=path, op=op):
                self.assertEqual(summaries[path]['by_op'][op], {
                    'outcomes': {'ok': 1},
                    'service_ms': {'n': 1, 'min': value, 'max': value,
                                   'mean': value, 'p50': value, 'p95': value, 'p99': value},
                    'build_ms': None, 'proof_ms': None, 'witness_ms': None,
                    'gas': {'computation': None, 'storage': None, 'rebate': None},
                    'gas_total': {},
                })


class TestSummaryCsv(unittest.TestCase):
    def test_parent_and_probe_csv_preserve_fields(self):
        doc = load_plan.assign_phases(load_plan.expand(
            {'shield_count': 16, 'consume_count': 2, 'invalidation_count': 1}))
        # Keep three synthetic parents and a valid snapshot; no workload execution.
        steps = doc['paths']['public']
        doc['paths'] = {'public': [steps[0], steps[1], steps[5]]}
        doc['requested'] = {}
        report = _report(doc)
        first, second, probe = report['samples']
        first.update(signer='parent-a', digest='digest-a', outcome_kind='abort',
                     abort=17, module='synthetic_module', error='also recorded',
                     service_ms=12, build_ms=0, step_ms=15, proof_ms=2,
                     witness_ms=3, scheduled_ms=20, parallel_k=0,
                     congestion_reject_count=0, expect={'abort': 17}, recovered=True,
                     gas={'computation': '9007199254740993', 'storage': '0',
                          'rebate': '9007199254741001'},
                     detail={'text': 'parent, "quoted"\nnext'})
        second.update(outcome_kind='client_refused', service_ms=None,
                      error='client, "refused"\nretry', expect=None, detail=None)
        probe.update(outcome_kind='probe', signer='parent-probe', digest='digest-p',
                     service_ms=40, build_ms=4, step_ms=44, proof_ms=0,
                     witness_ms=0, scheduled_ms=50, parallel_k=2,
                     congestion_reject_count=1, recovered=False,
                     gas={'computation': '5', 'storage': '6', 'rebate': '0'},
                     detail={'text': 'probe, "parent"\nnext'}, branches=[
                         {'op': 'issue', 'slot': 512, 'slots': [512, 513],
                          'signer': 'branch-a', 'digest': 'digest-ba',
                          'outcome_kind': 'ok', 'service_ms': 9000, 'build_ms': 0,
                          'gas': {'computation': '9007199254740997',
                                  'storage': '0', 'rebate': '9007199254741001'},
                          'detail': {'text': 'branch, "quoted"\nnext'}},
                         {'op': 'consume', 'slot': 0, 'signer': 'branch-b',
                          'outcome_kind': 'abort', 'abort': 23,
                          'error': 'branch, "failed"\nnext', 'service_ms': 0,
                          'build_ms': None, 'gas': None, 'detail': None},
                     ])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'report.json').write_text(json.dumps(report))
            (root / 'scenarios.json').write_text(json.dumps(doc))
            result = subprocess.run(
                [sys.executable, '-B', str(HERE / 'summarize_load.py'),
                 '--report', str(root / 'report.json'),
                 '--scenarios', str(root / 'scenarios.json'),
                 '--out', str(root / 'out')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            path_dir = root / 'out' / 'public'
            with (path_dir / 'samples.csv').open(newline='') as stream:
                parents = list(csv.DictReader(stream))
            with (path_dir / 'probes.csv').open(newline='') as stream:
                branches = list(csv.DictReader(stream))
            summary = json.loads((path_dir / 'summary.json').read_text())

        self.assertEqual(len(parents), 3)
        self.assertEqual(len(branches), 2)
        self.assertEqual(parents, [
            {'path': 'public', 'phase': 'stage.create', 'seq': '0',
             'op': 'create_show', 'signer': 'parent-a', 'digest': 'digest-a',
             'outcome_kind': 'abort', 'abort': '17', 'module': 'synthetic_module',
             'error': 'also recorded', 'abort_or_error': '17',
             'service_ms': '12', 'build_ms': '0', 'step_ms': '15', 'proof_ms': '2',
             'witness_ms': '3', 'scheduled_ms': '20', 'parallel_k': '0',
             'congestion_reject_count': '0', 'expect_mismatch': 'False',
             'recovered': 'True', 'gas_computation': '9007199254740993',
             'gas_storage': '0', 'gas_rebate': '9007199254741001',
             'expect': '{"abort":17}', 'detail': '{"text":"parent, \\"quoted\\"\\nnext"}'},
            {'path': 'public', 'phase': 'stage.create', 'seq': '1',
             'op': 'claim_pages', 'signer': '', 'digest': '',
             'outcome_kind': 'client_refused', 'abort': '', 'module': '',
             'error': 'client, "refused"\nretry',
             'abort_or_error': 'client, "refused"\nretry',
             'service_ms': '', 'build_ms': '', 'step_ms': '', 'proof_ms': '',
             'witness_ms': '', 'scheduled_ms': '', 'parallel_k': '',
             'congestion_reject_count': '', 'expect_mismatch': 'False',
             'recovered': '', 'gas_computation': '', 'gas_storage': '', 'gas_rebate': '',
             'expect': 'null', 'detail': ''},
            {'path': 'public', 'phase': 'probe.concurrent', 'seq': '5',
             'op': 'parallel', 'signer': 'parent-probe', 'digest': 'digest-p',
             'outcome_kind': 'probe', 'abort': '', 'module': '', 'error': '',
             'abort_or_error': '', 'service_ms': '40', 'build_ms': '4', 'step_ms': '44',
             'proof_ms': '0', 'witness_ms': '0', 'scheduled_ms': '50', 'parallel_k': '2',
             'congestion_reject_count': '1', 'expect_mismatch': 'False',
             'recovered': 'False', 'gas_computation': '5', 'gas_storage': '6',
             'gas_rebate': '0', 'expect': '"any"',
             'detail': '{"text":"probe, \\"parent\\"\\nnext"}'},
        ])
        self.assertEqual(branches, [
            {'path': 'public', 'phase': 'probe.concurrent', 'seq': '5',
             'probe': 'parallel', 'branch': '0', 'op': 'issue', 'slot': '512',
             'slots': '[512, 513]', 'signer': 'branch-a', 'digest': 'digest-ba',
             'outcome_kind': 'ok', 'abort': '', 'error': '',
             'service_ms': '9000', 'build_ms': '0',
             'gas_computation': '9007199254740997', 'gas_storage': '0',
             'gas_rebate': '9007199254741001',
             'detail': '{"text":"branch, \\"quoted\\"\\nnext"}'},
            {'path': 'public', 'phase': 'probe.concurrent', 'seq': '5',
             'probe': 'parallel', 'branch': '1', 'op': 'consume', 'slot': '0',
             'slots': 'null', 'signer': 'branch-b', 'digest': '',
             'outcome_kind': 'abort', 'abort': '23',
             'error': 'branch, "failed"\nnext', 'service_ms': '0', 'build_ms': '',
             'gas_computation': '', 'gas_storage': '', 'gas_rebate': '', 'detail': ''},
        ])
        self.assertEqual(json.loads(parents[0]['detail']), {'text': 'parent, "quoted"\nnext'})
        self.assertEqual(json.loads(parents[2]['detail']), {'text': 'probe, "parent"\nnext'})
        self.assertEqual(json.loads(branches[0]['detail']), {'text': 'branch, "quoted"\nnext'})
        # Branch-only ops and their timings/gas do not enter parent aggregates.
        self.assertEqual(set(summary['by_op']), {'create_show', 'claim_pages', 'parallel'})
        self.assertEqual(summary['counts']['steps'], 3)
        self.assertEqual(summary['by_op']['parallel']['outcomes'], {'probe': 1})
        self.assertEqual(summary['by_op']['parallel']['service_ms'],
                         {'n': 1, 'min': 40, 'max': 40, 'mean': 40,
                          'p50': 40, 'p95': 40, 'p99': 40})
        self.assertEqual(summary['by_op']['parallel']['gas_total'],
                         {'computation': 5, 'storage': 6, 'rebate': 0})


if __name__ == '__main__':
    unittest.main()
