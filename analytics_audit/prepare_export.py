"""Freeze, authenticate and load exports before launching analytical engines.

The private temporary copy is verified, traced with a key, and read with hash
binding. Consumers receive in-memory rows, never a path to mutable source files.
The HMAC key is the existing PUBLIC test fixture, not a production trust root.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile

from authenticated_export import FULL_SNAPSHOT
from authenticated_export import exporter, files, mapping, verify
from authenticated_export.errors import ExportError
from authenticated_export.rollback import RollbackRegistry
from authenticated_export.test_pure import (
    CREATED_AT, KEY, KEY_VERSION, FixtureSource, fixture_rows,
)


def admit(directory, *, registry, export_seq, key=KEY):
    with tempfile.TemporaryDirectory(prefix='kix-audit-frozen-') as temporary:
        frozen = Path(temporary) / 'export'
        # Never follow caller-controlled links into unrelated files.
        root = Path(directory)
        if root.is_symlink() or any(p.is_symlink() for p in root.rglob('*')):
            raise ExportError('EXPORT_FILE')
        shutil.copytree(root, frozen, symlinks=True)
        if any(p.is_symlink() for p in frozen.rglob('*')):
            raise ExportError('EXPORT_FILE')
        verify.verify_export(frozen, key, registry=registry, export_seq=export_seq,
                             expected_mode=FULL_SNAPSHOT)
        trace = verify.audit_trace(frozen, key)
        entries = {e['path']: e for e in trace['files']}
        descriptor = files.read_mapping_file(frozen, entries[files.MAPPING_FILE])
        tables = {table: files.read_table_file(frozen, entries[files.table_path(table)])
                  for table in mapping.TABLES}
        return {'mapping': descriptor, 'tables': tables, 'exportTrace': trace}


def synthetic_rows():
    rows = fixture_rows()
    # Additional synthetic command rows exercise precision boundaries, not policy.
    template = rows['command_result'][0]
    amounts = [0, 2**53, 2**53 + 1, 2**63 - 1, 2**63, 2**64 - 1, 2**64, 2**128 - 1]
    for index, amount in enumerate(amounts):
        row = copy.deepcopy(template)
        row.update(command_id='money-%02d' % index, amount_u128=str(amount),
                   admitted_bytes=index, created_ms=1000 + index)
        # Export fixtures characterize mapping, not the durable CRC validator.
        rows['command_result'].append(row)
    return rows


def prepare(source='synthetic'):
    with tempfile.TemporaryDirectory(prefix='kix-audit-source-') as temporary:
        root = Path(temporary)
        if source == 'synthetic':
            adapter = FixtureSource(synthetic_rows())
            exporter.export_source(adapter, root / 'export', mode=FULL_SNAPSHOT,
                                   key=KEY, key_version=KEY_VERSION, created_at=CREATED_AT)
            host = {'fixtureKind': 'synthetic-authenticated-export'}
        else:
            # Import only on the explicitly requested local integration path.
            from durable.cluster import PinnedPostgresCluster
            from durable.backend import DurablePostgresBackend
            from authenticated_export.source import PostgresExportSource
            from authenticated_export.test_export import command, seed, spec
            cluster = PinnedPostgresCluster(root / 'pg')
            try:
                cluster.start()
                backend = DurablePostgresBackend(cluster)
                store = str(root / 'store')
                unit = backend.open_unit(store, spec())
                try:
                    seed(unit)
                    for index, amount in enumerate([0, 2**53, 2**53 + 1, 2**63 - 1,
                                                    2**63, 2**64 - 1, 2**64, 2**128 - 1]):
                        result = unit.apply(command('money-%02d' % index,
                                                    str(index + 10), '0', str(amount)),
                                            2000 + index)
                        assert result['outcome'] == 'new_success', result
                    adapter = PostgresExportSource(cluster, store)
                    exporter.export_source(adapter, root / 'export', mode=FULL_SNAPSHOT,
                                           key=KEY, key_version=KEY_VERSION,
                                           created_at=CREATED_AT)
                finally:
                    unit.close()
                host = {'fixtureKind': 'local-postgres-authenticated-export',
                        'postgresVersion': cluster.version, 'settings': cluster.settings}
            finally:
                cluster.stop()
        bundle = admit(root / 'export', registry=RollbackRegistry(root / 'registry.json'),
                       export_seq=1)
        bundle['source'] = host
        return bundle


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', choices=['synthetic', 'postgres'], default='synthetic')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), sort_keys=True))
