"""Equal-condition local exploration runner. Does not rank candidates."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from exploration.stage4.adapters import FoundationAdapter, PostgresAdapter
from exploration.stage4.budget import (
    CPU_CORES,
    SETTINGS,
    TOTAL_DISK_CAP_BYTES,
    TOTAL_RAM_CAP_BYTES,
)
from exploration.stage4.clusters import FoundationCluster, PostgresCluster, quiesce_package_fdb
from exploration.stage4.exercise import exercise_candidate
from exploration.stage4.host import collect_host, locked_blobs_match

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / 'validation' / '2026-10-08-k-stage4-local-exploration'
_CANDIDATES = ('postgresql', 'foundationdb')


def _hwm(pid):
    text = Path('/proc/%s/status' % pid).read_text()
    for line in text.splitlines():
        if line.startswith('VmHWM:'):
            return int(line.split()[1]) * 1024
    return 0


def _json_ready(value):
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


def _write_json(path, payload):
    path.write_text(json.dumps(_json_ready(payload), indent=2, sort_keys=True) + '\n')


def _durability(candidate, cluster):
    if candidate == 'postgresql':
        return {
            'ack': 'commit return after local WAL flush (synchronous_commit=on, fsync=on, full_page_writes=on)',
            'hardware_flush_verified': False,
            'independent_failure_domain': False,
            'durability_equal_to_other_candidate': False,
            'reason': (
                'Local PostgreSQL WAL flush on this virtual disk is not equated to a '
                'single-process FoundationDB commit. Power and OS crash were not injected.'
            ),
            'settings': cluster.settings,
            'version': cluster.version,
        }
    configuration = (cluster.status or {}).get('configuration')
    return {
        'ack': 'FoundationDB commit return',
        'configuration': configuration,
        'status': cluster.status,
        'version': cluster.version,
        'process_count': 1,
        'independent_failure_domain': False,
        'hardware_flush_verified': False,
        'durability_equal_to_other_candidate': False,
        'reason': (
            'One local FoundationDB process is not an independent failure domain. '
            'Its commit is not equated to PostgreSQL synchronous_commit. '
            'Power and OS crash were not injected.'
        ),
    }


def child(candidate, out):
    if candidate not in _CANDIDATES:
        raise SystemExit('unknown candidate')
    os.sched_setaffinity(0, set(CPU_CORES))
    affinity = sorted(os.sched_getaffinity(0))
    if affinity != list(CPU_CORES):
        raise SystemExit('cpu affinity was not applied: %s' % affinity)
    dest = Path(out) / candidate
    dest.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='kixs4-%s-' % candidate))
    cluster = PostgresCluster(root) if candidate == 'postgresql' else FoundationCluster(root)
    try:
        cluster.start()
        adapter = PostgresAdapter(cluster) if candidate == 'postgresql' else FoundationAdapter(cluster)
        measured = exercise_candidate(cluster, adapter)
        cluster.note_rss()
        disk_bytes = cluster.disk_bytes()
        server_bytes = cluster.peak_server_bytes
        client_bytes = _hwm(os.getpid())
        within_cap = (
            server_bytes + client_bytes <= TOTAL_RAM_CAP_BYTES
            and disk_bytes <= TOTAL_DISK_CAP_BYTES
        )
        summary = {
            'exploration_data': True,
            'candidate': candidate,
            'production_conformance': False,
            'production_readiness': False,
            'protocol_truth': False,
            'adoption': False,
            'ranking': None,
            'slo': None,
            'chain_inventory_writer': False,
            'sql_and_chain_concurrent_writers': False,
            'public_endpoint': False,
            'resource_budget': {
                'cpu_cores': list(CPU_CORES),
                'applied_affinity': affinity,
                'total_ram_cap_bytes': TOTAL_RAM_CAP_BYTES,
                'total_disk_cap_bytes': TOTAL_DISK_CAP_BYTES,
                'server_hwm_bytes': server_bytes,
                'client_hwm_bytes': client_bytes,
                'disk_bytes': disk_bytes,
                'within_cap': within_cap,
            },
            'workload_settings': SETTINGS,
            'durability': _durability(candidate, cluster),
            'money': 'UNDETERMINED — 사용자/운영 책임자',
            'functional_ok': measured['functional_ok'],
            'low_load_holds': measured['low_load_holds'],
            'input_fingerprint': measured['input_fingerprint'],
            'workloads': measured['workloads'],
            'probes': measured['probes'],
            'valid': bool(measured['functional_ok'] and within_cap),
        }
        _write_samples(dest / 'samples.csv', measured['workloads'])
        _write_json(dest / 'summary.json', summary)
        if not summary['valid']:
            raise SystemExit(2)
    finally:
        cluster.stop()
        shutil.rmtree(root, ignore_errors=True)


def _write_samples(path, workloads):
    fields = (
        'workload', 'index', 'command_id', 'outcome', 'service_ns',
        'scheduled_latency_ns', 'log_delta', 'admitted_entries', 'capacity_reason',
    )
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for workload in workloads:
            for sample in workload['samples']:
                writer.writerow(sample)


def _listeners():
    completed = subprocess.run(['ss', '-ltn'], check=False, capture_output=True, text=True)
    return completed.stdout


def parent(out):
    quiesce_package_fdb()
    host = collect_host()
    if not locked_blobs_match(host):
        raise SystemExit('locked kernel blobs do not match')
    listeners = _listeners()
    host['candidate_ports_before_start'] = [
        line for line in listeners.splitlines()
        if any(token in line for token in (':5432', ':4500', ':4501'))
    ]
    if host['candidate_ports_before_start']:
        raise SystemExit('candidate port is already listening: %s' % host['candidate_ports_before_start'])
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / 'host.json', host)
    for candidate in _CANDIDATES:
        subprocess.run(
            [sys.executable, '-m', 'exploration.stage4.run', 'child', candidate, str(out)],
            cwd=ROOT,
            check=True,
        )
    summaries = []
    for candidate in _CANDIDATES:
        summaries.append(json.loads((out / candidate / 'summary.json').read_text()))
    fingerprint = summaries[0]['input_fingerprint']
    if any(item['input_fingerprint'] != fingerprint for item in summaries):
        raise SystemExit('workload fingerprint differs between candidates')
    if any(item['ranking'] is not None for item in summaries):
        raise SystemExit('a candidate summary ranked a winner')
    if any(item['durability']['durability_equal_to_other_candidate'] for item in summaries):
        raise SystemExit('durability was marked equal')
    if any(not item['valid'] for item in summaries):
        raise SystemExit('a candidate run was not valid')
    manifest = {
        'exploration_data': True,
        'comparison_authority': 'docs/DEVELOPMENT_PLAN.md §9',
        'not_a_second_comparison_table': True,
        'ranking': None,
        'slo': None,
        'adoption': False,
        'input_fingerprint': fingerprint,
        'candidates': list(_CANDIDATES),
        'files': [
            'host.json',
            'postgresql/summary.json',
            'postgresql/samples.csv',
            'foundationdb/summary.json',
            'foundationdb/samples.csv',
        ],
    }
    _write_json(out / 'manifest.json', manifest)


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    if len(argv) >= 2 and argv[1] == 'child':
        child(argv[2], argv[3])
        return 0
    out = argv[1] if len(argv) > 1 else str(DEFAULT_OUTPUT)
    parent(out)
    return 0


if __name__ == '__main__':
    main()
