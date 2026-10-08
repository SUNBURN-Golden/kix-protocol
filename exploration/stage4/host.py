"""Host facts recorded before a candidate process starts."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from exploration.stage4.budget import (
    CPU_CORES,
    FDB_CACHE_MEMORY,
    FDB_MEMORY,
    FDB_PORT,
    FDB_STORAGE_MEMORY,
    FDB_VERSION,
    LOCKED_BLOBS,
    POSTGRES_SHARED_BUFFERS,
    SETTINGS,
    TOTAL_DISK_CAP_BYTES,
    TOTAL_RAM_CAP_BYTES,
)

ROOT = Path(__file__).resolve().parents[2]


def _run(args):
    try:
        completed = subprocess.run(
            args, cwd=ROOT, check=False, capture_output=True, text=True,
        )
    except OSError as exc:
        return {'error': str(exc)}
    return {
        'code': completed.returncode,
        'stdout': completed.stdout.strip(),
        'stderr': completed.stderr.strip(),
    }


def _read(path):
    try:
        return Path(path).read_text().strip()
    except OSError as exc:
        return 'unreadable: %s' % exc


def collect_host():
    blobs = {}
    for path, expected in LOCKED_BLOBS.items():
        observed = _run(['git', 'rev-parse', 'HEAD:%s' % path])
        blobs[path] = {
            'expected': expected,
            'observed': observed.get('stdout'),
            'match': observed.get('stdout') == expected,
        }
    meminfo = {}
    for line in _read('/proc/meminfo').splitlines():
        if line.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:')):
            key, value = line.split(':', 1)
            meminfo[key] = value.strip()
    return {
        'exploration_data': True,
        'recorded_before_candidate_start': True,
        'uname': _run(['uname', '-srvm']),
        'architecture': platform.machine(),
        'cpu_model': _cpu_model(),
        'nproc': os.cpu_count(),
        'meminfo': meminfo,
        'os_release': _read('/etc/os-release'),
        'python': platform.python_version(),
        'disk': {
            'df': _run(['df', '-B1', '/']),
            'lsblk': _run(['lsblk', '-d', '-o', 'NAME,SIZE,ROTA,TYPE,MODEL']),
            'rotational_vda': _read('/sys/block/vda/queue/rotational'),
            'model': _read('/sys/block/vda/device/model'),
            'flush_characteristic': (
                'unverified: virtual disk, no equipment datasheet, '
                'rotational flag is not a hardware flush proof'
            ),
        },
        'git_head': _run(['git', 'rev-parse', 'HEAD']),
        'origin_main': _run(['git', 'rev-parse', 'origin/main']),
        'locked_blobs': blobs,
        'postgres_version': _run(['/usr/lib/postgresql/17/bin/postgres', '--version']),
        'fdbserver_version': _run(['/usr/sbin/fdbserver', '-v']),
        'packages': _run([
            'dpkg-query', '-W',
            'postgresql-17', 'postgresql-client-17', 'python3-psycopg',
            'foundationdb-server', 'foundationdb-clients',
        ]),
        'resource_budget': {
            'cpu_cores': list(CPU_CORES),
            'total_ram_cap_bytes': TOTAL_RAM_CAP_BYTES,
            'total_disk_cap_bytes': TOTAL_DISK_CAP_BYTES,
            'postgres_shared_buffers': POSTGRES_SHARED_BUFFERS,
            'fdb_memory': FDB_MEMORY,
            'fdb_storage_memory': FDB_STORAGE_MEMORY,
            'fdb_cache_memory': FDB_CACHE_MEMORY,
            'fdb_port': FDB_PORT,
            'fdb_version_pin': FDB_VERSION,
            'includes': 'backend process, client, logs, and observation files of that candidate',
            'not_a_product_limit': True,
        },
        'workload_settings': SETTINGS,
        'money': 'UNDETERMINED — 사용자/운영 책임자',
        'chain_inventory_writer': False,
        'public_endpoint': False,
    }


def _cpu_model():
    for line in _read('/proc/cpuinfo').splitlines():
        if line.startswith('model name'):
            return line.split(':', 1)[1].strip()
    return 'unknown'


def locked_blobs_match(host):
    return all(item['match'] for item in host['locked_blobs'].values())
