"""Offline checks for summarize_load.py.

Builds a synthetic report from the generator's own expected end-state (no
localnet) and checks the pass/fail rules: page conservation, full sample
coverage, shield-count shortfall, and unknown probe branches.
"""
import json
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


if __name__ == '__main__':
    unittest.main()
