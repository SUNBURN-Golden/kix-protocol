"""Local acceptance runner for the stage-7 authenticated export.

Records the host, checks the two locked kernel blobs, runs the database-free
suite and the PostgreSQL-bound suite over the unchanged stage-5 durable
layer, and writes host.json and summary.json. It starts only a local
unix-socket PostgreSQL, calls no provider and opens no endpoint. It ranks
nothing, sets no SLO and claims no production conformance: the export is a
local fixture boundary (caller-keyed HMAC, local anti-rollback registry).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from authenticated_export import PINNED_POSTGRES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'validation' / '2026-11-12-k-stage7-authenticated-export'
_SUITES = ('authenticated_export.test_pure', 'authenticated_export.test_export')
_HOST_DROP = (
    'exploration_data', 'fdbserver_version', 'resource_budget', 'workload_settings', 'money',
)


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')


def _host():
    from exploration.stage4.host import collect_host, locked_blobs_match
    host = collect_host()
    for name in _HOST_DROP:
        host.pop(name, None)
    packages = host.get('packages')
    if isinstance(packages, dict) and packages.get('stdout'):
        packages['stdout'] = '\n'.join(
            line for line in packages['stdout'].splitlines() if 'foundationdb' not in line
        )
    host['localDurableData'] = True
    host['localExportFixtureOnly'] = True
    host['recorded_before_suite_start'] = True
    host['public_endpoint'] = False
    host['chain_inventory_writer'] = False
    return host, locked_blobs_match(host)


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    out = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)
    host, blobs_ok = _host()
    _write_json(out / 'host.json', host)
    if not blobs_ok:
        raise SystemExit('locked kernel blobs do not match')
    suite = unittest.defaultTestLoader.loadTestsFromNames(_SUITES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    observed = {}
    try:
        from authenticated_export.test_export import OBSERVED
        observed = dict(OBSERVED)
    except ImportError:
        pass
    problems = [
        {'test': str(test), 'detail': text.strip().splitlines()[-1] if text.strip() else ''}
        for test, text in list(result.failures) + list(result.errors)
    ]
    ok = result.wasSuccessful() and bool(observed.get('version'))
    summary = {
        'localDurableData': True,
        'localExportFixtureOnly': True,
        'protocolTruth': False,
        'productionConformance': False,
        'productionReadiness': False,
        'productionEndpoint': False,
        'chainWriter': False,
        'fundsExecuted': False,
        'fsmDurable': False,
        'adoption': (
            'option A of docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md §6, '
            'local non-production PostgreSQL 17.11 (Debian 17.11-0+deb13u1)'
        ),
        'backend': {
            'pin': PINNED_POSTGRES,
            'observed_version': observed.get('version'),
            'observed_settings': observed.get('settings'),
            'single_process': True,
            'single_writer': True,
            'transport': 'unix socket only',
        },
        'tests': {
            'ran': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'problems': problems,
        },
        'not_verified': {
            'production_signing_scheme_or_trust_root': False,
            'production_anti_rollback_policy': False,
            'cross_shard_consistent_cut': False,
            'arrow_parquet_materialization': False,
            'partial_prefix_hash_rederivation_without_source': False,
            'power_os_crash_injected': False,
            'hardware_flush_verified': False,
        },
        'slo': None,
        'ranking': None,
        'ok': ok,
    }
    _write_json(out / 'summary.json', summary)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
