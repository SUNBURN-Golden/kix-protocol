"""Offline checks for measurement_gap.py.

Builds the same synthetic expanded workload the summarize_load tests use —
no localnet — and checks the gap report on a complete record and on a
truncated record shaped like the recorded L2 failure (public prefix only,
private and delegated at zero samples, shields 0/requested, a receipt whose
private row says PASSED_MEASUREMENT on nothing).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import load_plan  # noqa: E402
import measurement_gap  # noqa: E402


def _sample(step, path):
    return {'path': path, 'phase': step.get('phase'), 'seq': step['seq'],
            'op': step['op'], 'outcome_kind': 'ok', 'expect': step.get('expect'),
            'expect_mismatch': False, 'service_ms': 1}


def _report(doc, keep=None):
    samples = []
    for name, steps in doc['paths'].items():
        for step in steps:
            if keep is None or keep(name, step):
                samples.append(_sample(step, name))
    return {'samples': samples,
            'snapshots': {name: {'pages': []} for name in doc['paths']},
            'requested': doc['requested'], 'scenarioFingerprint': 'synthetic'}


def _expects(unmeasured):
    return [u['expect'] for u in unmeasured]


class TestMeasurementGap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(json.dumps(load_plan.assign_phases(load_plan.expand(
            {'shield_count': 16, 'consume_count': 2, 'invalidation_count': 1}))))
        # The recorded L2 truncation: a public prefix, nothing else.
        cls.cut = 300   # inside public stage.fill (seqs 24..390)
        cls.truncated = _report(cls.doc, keep=lambda n, s: n == 'public' and s['seq'] < cls.cut)
        cls.truncated['snapshots'] = {}
        # The L2 receipt shape: private PASSED_MEASUREMENT on zero samples,
        # delegated FAILED on an end-state check against an empty snapshot.
        cls.l2_receipt = {
            'status': 'FAILED_MEASUREMENT',
            'paths': {
                'public': {'status': 'PASSED_MEASUREMENT'},
                'private': {'status': 'PASSED_MEASUREMENT'},
                'delegated': {'status': 'FAILED_MEASUREMENT',
                              'failed_checks': ['delegated_grant_states']},
            }}

    def test_complete_record_is_fully_measured(self):
        gap = measurement_gap.build_gap_report(self.doc, _report(self.doc), None)
        for name in self.doc['paths']:
            path = gap['paths'][name]
            self.assertEqual(path['coverage'], 'full', name)
            self.assertEqual(path['measured_steps'], path['planned_steps'], name)
            self.assertEqual(path['predicates']['unmeasured'], [], name)
            self.assertEqual(path['probes']['unmeasured'], [], name)
            self.assertTrue(path['end_state']['evaluable'], name)
            self.assertTrue(path['end_state']['snapshot_present'], name)
        self.assertEqual(gap['coverage']['shields_ok'],
                         gap['coverage']['shields_requested'])
        self.assertEqual(gap['coverage']['shortfalls'], [])

    def test_end_state_check_names(self):
        gap = measurement_gap.build_gap_report(self.doc, _report(self.doc), None)
        checks = {n: p['end_state']['checks'] for n, p in gap['paths'].items()}
        self.assertEqual(checks['public'], ['pages'])
        self.assertEqual(checks['private'],
                         ['pages', 'leaf_count', 'nullifiers', 'challenges', 'revocations'])
        self.assertEqual(checks['delegated'], ['pages', 'grants', 'page_delegated_to'])

    def test_truncated_record_shows_l2_gap_structure(self):
        gap = measurement_gap.build_gap_report(
            self.doc, self.truncated, self.l2_receipt)
        self.assertEqual(gap['record_status'], 'FAILED_MEASUREMENT')
        self.assertEqual(gap['coverage']['shields_requested'],
                         self.doc['requested']['shield_count'])
        self.assertEqual(gap['coverage']['shields_ok'], 0)

        public = gap['paths']['public']
        self.assertEqual(public['coverage'], 'partial')
        self.assertEqual(public['planned_steps'], len(self.doc['paths']['public']))
        self.assertEqual(public['measured_steps'], self.cut)
        # A clean prefix: holes would appear in missing_in_range, none here.
        self.assertEqual(public['measured_seqs']['min'], 0)
        self.assertEqual(public['measured_seqs']['max'], self.cut - 1)
        self.assertEqual(public['measured_seqs']['missing_in_range'], [])
        # All five planned concurrency probes landed before the cut.
        self.assertEqual(len(public['probes']['measured']), 5)
        self.assertTrue(all(p['met'] for p in public['probes']['measured']))
        # The cancel-leg predicates are listed as unmeasured.
        unmeasured = public['predicates']['unmeasured']
        cancel = [u for u in unmeasured if u['phase'] == 'stage.cancel']
        self.assertTrue(cancel)
        self.assertIn({'abort': 1}, _expects(cancel))   # E_CLOSED legs
        for step in self.doc['paths']['public']:
            if step.get('expect') not in ('ok', 'any') and step['seq'] >= self.cut:
                self.assertIn(step['seq'], {u['seq'] for u in unmeasured})

        for name in ('private', 'delegated'):
            path = gap['paths'][name]
            self.assertEqual(path['coverage'], 'none', name)
            self.assertEqual(path['measured_steps'], 0, name)
            self.assertEqual(path['predicates']['measured'], 0, name)
            self.assertFalse(path['end_state']['evaluable'], name)
            self.assertFalse(path['end_state']['snapshot_present'], name)

        private_unmeasured = gap['paths']['private']['predicates']['unmeasured']
        self.assertIn({'abort': 19}, _expects(private_unmeasured))         # E_ROOT boundary
        self.assertIn({'abort': 'zk_gate:2'}, _expects(private_unmeasured))  # invalidations
        probe_names = {p['name'] for p in gap['paths']['private']['probes']['unmeasured']}
        self.assertIn('concurrent_revokes', probe_names)

        delegated_unmeasured = gap['paths']['delegated']['predicates']['unmeasured']
        self.assertIn({'abort': 23}, _expects(delegated_unmeasured))  # E_DELEGATED
        self.assertIn({'abort': 24}, _expects(delegated_unmeasured))  # E_GRANT_CLOSED
        probe_names = {p['name'] for p in gap['paths']['delegated']['probes']['unmeasured']}
        self.assertIn('shared_grant_reads', probe_names)

        # Receipt rows are quoted, not trusted: the vacuous private pass and the
        # snapshot-less delegated check both show up next to coverage 'none'.
        self.assertEqual(gap['paths']['private']['receipt_path_status'],
                         'PASSED_MEASUREMENT')
        self.assertEqual(gap['paths']['delegated']['receipt_path_status'],
                         'FAILED_MEASUREMENT')
        self.assertEqual(gap['paths']['delegated']['receipt_failed_checks'],
                         ['delegated_grant_states'])

        shortfall_paths = {s['path'] for s in gap['coverage']['shortfalls'] if 'path' in s}
        self.assertEqual(shortfall_paths, {'public', 'private', 'delegated'})
        self.assertIn({'shields_requested': self.doc['requested']['shield_count'],
                       'shields_ok': 0}, gap['coverage']['shortfalls'])

    def test_missing_seq_hole_is_listed(self):
        hole_seq = self.doc['paths']['public'][10]['seq']
        report = _report(self.doc,
                         keep=lambda n, s: not (n == 'public' and s['seq'] == hole_seq))
        gap = measurement_gap.build_gap_report(self.doc, report, None)
        public = gap['paths']['public']
        self.assertEqual(public['coverage'], 'partial')
        self.assertEqual(public['measured_seqs']['missing_in_range'], [hole_seq])

    def test_no_receipt_is_tolerated(self):
        gap = measurement_gap.build_gap_report(self.doc, self.truncated, None)
        self.assertIsNone(gap['record_status'])
        self.assertIsNone(gap['paths']['public']['receipt_path_status'])
        self.assertIsNone(gap['paths']['public']['receipt_failed_checks'])

    def _write_record(self, root, report, receipt):
        (root / 'load-scenarios.json').write_text(json.dumps(self.doc))
        (root / 'load-report.json').write_text(json.dumps(report))
        if receipt is not None:
            (root / 'receipt.json').write_text(json.dumps(receipt))

    def test_cli_writes_gap_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_record(root, self.truncated, self.l2_receipt)
            result = subprocess.run(
                [sys.executable, str(HERE / 'measurement_gap.py'),
                 '--record', str(root)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            gap = json.loads((root / 'gap-report.json').read_text())
            self.assertEqual(gap['version'], 'kix-rs4-load-gap-report-v1')
            self.assertEqual({k: v['coverage'] for k, v in gap['paths'].items()},
                             {'public': 'partial', 'private': 'none',
                              'delegated': 'none'})

    def test_cli_explicit_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_record(root, _report(self.doc), None)
            out = root / 'out' / 'gap.json'
            result = subprocess.run(
                [sys.executable, str(HERE / 'measurement_gap.py'),
                 '--report', str(root / 'load-report.json'),
                 '--scenarios', str(root / 'load-scenarios.json'),
                 '--out', str(out)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            gap = json.loads(out.read_text())
            self.assertIsNone(gap['record_status'])

    def test_cli_missing_inputs_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(HERE / 'measurement_gap.py'),
                 '--record', tmp],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
