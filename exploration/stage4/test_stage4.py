"""Conformance and functional checks for the stage-4 local exploration."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from readiness.conformance import BackendConformance

from exploration.stage4.adapters import FoundationAdapter, PostgresAdapter
from exploration.stage4.budget import CPU_CORES
from exploration.stage4.clusters import FoundationCluster, PostgresCluster, quiesce_package_fdb
from exploration.stage4.exercise import exercise_candidate
from exploration.stage4.workload import WORKLOAD_ORDER, counts, simulate


def setUpModule():
    os.sched_setaffinity(0, set(CPU_CORES))
    quiesce_package_fdb()


class DecideTests(unittest.TestCase):
    def test_workload_outcomes_are_stable(self):
        expected = {
            'low-load-uniform': {'new_success': 8},
            'uniform': {'new_success': 4, 'business_rejected': 4},
            'hot-seat': {'new_success': 1, 'business_rejected': 7},
            'same-command-retry': {'new_success': 1, 'replayed': 4},
            'history-growth': {'new_success': 1, 'conflict_retained': 5},
            'saturation': {'new_success': 3, 'capacity': 3, 'replayed': 1},
        }
        for name in WORKLOAD_ORDER:
            outcomes, _entries, _observations = simulate(name)
            observed = {key: value for key, value in counts(outcomes).items() if value}
            self.assertEqual(observed, expected[name])
            if name == 'saturation':
                self.assertEqual(outcomes.index('capacity'), 3)
                self.assertEqual(outcomes[-1], 'replayed')


class _ClusterCase(unittest.TestCase):
    cluster_type = None
    adapter_type = None

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix='kixs4test-')
        cls.cluster = cls.cluster_type(cls.root)
        cls.cluster.start()
        cls.backend = cls.adapter_type(cls.cluster)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    def _exercise(self):
        measured = exercise_candidate(self.cluster, self.backend)
        self.assertTrue(measured['functional_ok'], measured['probes'])
        self.assertTrue(measured['low_load_holds'])
        for workload in measured['workloads']:
            self.assertTrue(workload['outcomes_match_simulation'])
            self.assertIs(workload['p99_is_product_slo'], False)
            self.assertTrue(workload['exploration_data'])
        self.assertTrue(measured['probes']['u128']['stored_as_decimal_text'])
        self.assertFalse(measured['probes']['u128']['signed_integer_narrowing'])
        self.assertFalse(measured['probes']['process_crash']['power_os_crash_injected'])
        self.assertFalse(measured['probes']['process_crash']['hardware_flush_verified'])
        self.assertIsNone(measured['probes']['process_crash']['rto_slo'])
        return measured


class PostgresConformance(BackendConformance, _ClusterCase):
    cluster_type = PostgresCluster
    adapter_type = PostgresAdapter

    def test_zz_functional_exploration(self):
        measured = self._exercise()
        retry = next(item for item in measured['workloads'] if item['workload'] == 'same-command-retry')
        replay_deltas = [
            sample['log_delta'] for sample in retry['samples'] if sample['outcome'] == 'replayed'
        ]
        self.assertEqual(replay_deltas, [0, 0, 0, 0])


class FoundationConformance(BackendConformance, _ClusterCase):
    cluster_type = FoundationCluster
    adapter_type = FoundationAdapter

    def test_zz_functional_exploration(self):
        self._exercise()


if __name__ == '__main__':
    unittest.main()
