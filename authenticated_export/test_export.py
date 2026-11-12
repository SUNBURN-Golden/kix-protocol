"""PostgreSQL-bound tests of the authenticated export over the stage-5 store.

Needs the pinned local PostgreSQL 17.11 (/usr/lib/postgresql/17/bin) and
psycopg; skips gracefully when the backend is absent so it can live alongside
the offline suite (the durable/test_economics_binding.py pattern). All writes
go through the unchanged durable public API with synthetic fixture values;
the exporter itself only reads, inside one SERIALIZABLE READ ONLY snapshot,
and never takes the writer lock. Not wired into CI.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POSTGRES = '/usr/lib/postgresql/17/bin/postgres'
INITDB = '/usr/lib/postgresql/17/bin/initdb'

try:
    import psycopg  # noqa: F401
    HAVE_PSYCOPG = True
except ImportError:
    HAVE_PSYCOPG = False

HAVE_BACKEND = HAVE_PSYCOPG and os.path.exists(POSTGRES) and os.path.exists(INITDB)

from readiness.codec import strict_loads
from readiness.store import StoreError

from authenticated_export import FULL_SNAPSHOT, INCREMENTAL
from authenticated_export import exporter, files, mapping, verify
from authenticated_export.errors import ExportError
from authenticated_export.rollback import RollbackRegistry

if HAVE_BACKEND:
    from durable import schema as durable_schema
    from durable.backend import DurablePostgresBackend
    from durable.budgets import CLASSES, BudgetSpec, ClassLimit
    from durable.cluster import PinnedPostgresCluster
    from durable.model import Command
    from durable.normalize import ProviderItem, Scope
    from durable.schema import CRC_TABLES, store_key

    from authenticated_export import source as export_source

OBSERVED = {}

# Test-only fixture key. Never a secret, never stored by the package.
KEY = b'fixture-export-key-0001'
KEY_VERSION = 'fixture-key/1'
CREATED_AT = 1_760_000_000_000
U128_MAX_TEXT = str((1 << 128) - 1)
SCOPE = Scope('fixture-provider', 'fixture-account', 'fixture-env', 'fixture-profile-1')
_LSN = re.compile(r'^[0-9A-F]+/[0-9A-F]+$')
_SNAPSHOT = re.compile(r'^\d+:\d+:')


def spec():
    # Fixtures only. Not an approved limit of any kind.
    limit = ClassLimit(1000, 1_000_000, 3_600_000)
    return BudgetSpec(**{name: limit for name in CLASSES})


def command(command_id='c1', slot='0', nonce='0', amount='10001'):
    return Command(command_id, 'fixture-show', slot, amount, 'buyer-1', nonce)


def raw_delivery(entries, delivery='t-1'):
    return json.dumps({'delivery': delivery, 'entries': entries}, sort_keys=True).encode()


def entry(key='k1', amount=10001, operation='op-1'):
    return {
        'key': key, 'kind': 'capture', 'amount': amount, 'currency': 'KRW',
        'method': 'fixture-method', 'status': 'DONE', 'at': '2026-11-12T09:00:00',
        'offset': None, 'operation': operation,
    }


def fixture_lookup(raw):
    document = json.loads(raw.decode().strip())
    items = []
    for one in document['entries']:
        operation = None
        if one['operation'] is not None:
            operation = {'provider': 'fixture-provider', 'account': 'fixture-account',
                         'operation': one['operation']}
        items.append(ProviderItem(
            fact_key=one['key'], kind=one['kind'], amount_krw=one['amount'],
            currency=one['currency'], method=one['method'], status=one['status'],
            occurred_at_text=one['at'], occurred_offset=one['offset'], operation=operation,
        ))
    return items


def seed(unit):
    """Write fixture rows through the public API into all eleven tables."""
    assert unit.apply(command('c1', '0', '0', U128_MAX_TEXT), 1000)['outcome'] == 'new_success'
    # Same slot, different command: business rejection, no order/intent.
    assert unit.apply(command('c2', '0', '0'), 1001)['outcome'] == 'business_rejected'
    # Same command id, different payload: conflict retained + observation.
    assert unit.apply(command('c1', '0', '9'), 1002)['outcome'] == 'conflict_retained'
    unit.inbox.receive(
        SCOPE, raw_delivery([entry('k1'), entry('k2', operation=None)]),
        verification_result='FIXTURE_UNVERIFIED', received_ms=1000, now_ms=1000,
        lookup_fn=fixture_lookup, apply_fn=lambda item: None,
    )
    unit.outbox.record_attempt('intent-c1', 1003)


def lsn_value(text):
    hi, lo = text.split('/')
    return (int(hi, 16) << 32) + int(lo, 16)


def read_rows(directory, table):
    path = Path(directory) / files.table_path(table)
    return [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]


@unittest.skipUnless(HAVE_BACKEND, 'pinned local PostgreSQL 17.11 + psycopg required')
class ExportPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix='kixs7test-')
        cls.cluster = PinnedPostgresCluster(cls.root)
        cls.cluster.start()
        OBSERVED['version'] = cls.cluster.version
        OBSERVED['settings'] = cls.cluster.settings
        cls.backend = DurablePostgresBackend(cls.cluster)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='kixs7case-', dir=self.root)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.store = str(Path(self.tmp) / 'store')
        self.unit = self.backend.open_unit(self.store, spec())
        self.addCleanup(self.unit.close)

    def source(self, store=None):
        return export_source.PostgresExportSource(self.cluster, self.store if store is None else store)

    def export(self, name='out', mode=FULL_SNAPSHOT, store=None, **kwargs):
        directory = str(Path(self.tmp) / name)
        manifest = exporter.export_source(
            self.source(store), directory, mode=mode, key=KEY,
            key_version=KEY_VERSION, created_at=CREATED_AT, **kwargs,
        )
        return directory, manifest

    def assertCode(self, code, fn, *args, **kwargs):
        with self.assertRaises(ExportError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_full_export_matches_table_counts_and_verifies(self):
        seed(self.unit)
        counts = self.unit.table_counts()
        self.assertTrue(all(counts[table] > 0 for table in CRC_TABLES))
        directory, manifest = self.export()
        report = verify.verify_export(directory, KEY)
        self.assertTrue(report['verified'])
        self.assertEqual(report['rowCount'], sum(counts.values()))
        position = manifest['sourceShardCuts'][0]['committedPosition']
        for entry in position['tables']:
            self.assertEqual(entry['rowCount'], counts[entry['table']])
        rows = read_rows(directory, 'command_result')
        by_id = {row['command_id']: row for row in rows}
        # u128-max survives the PG round trip as lossless decimal text.
        self.assertEqual(by_id['c1']['amount_u128'], U128_MAX_TEXT)
        self.assertEqual(int(by_id['c1']['amount_u128']), (1 << 128) - 1)
        self.assertEqual(by_id['c2']['outcome'], 'business_rejected')
        trace = verify.audit_trace(directory, key=KEY)
        self.assertTrue(trace['linksResolved'])
        self.assertEqual(trace['sourceCut'], manifest['sourceShardCuts'][0])

    def test_snapshot_isolation_hides_mid_capture_commit(self):
        seed(self.unit)
        capture = self.source().capture()
        try:
            before = capture.rows('command_result')
            lsn_start = capture.lsn_start
            # The writer commits on its own connection mid-capture.
            self.assertEqual(
                self.unit.apply(command('c-mid', '5', '0'), 2000)['outcome'], 'new_success',
            )
            after = capture.rows('command_result')
            self.assertEqual(before, after)
            self.assertNotIn('c-mid', [row['command_id'] for row in after])
            lsn_end = capture.lsn_end()
            # WAL provenance advanced; it is never the cut.
            self.assertGreater(lsn_value(lsn_end), lsn_value(lsn_start))
        finally:
            capture.close()
        fresh = self.source().capture()
        try:
            ids = [row['command_id'] for row in fresh.rows('command_result')]
            self.assertIn('c-mid', ids)
        finally:
            fresh.close()

    def test_restart_reexport_is_content_identical(self):
        seed(self.unit)
        dir_a, manifest_a = self.export('a')
        self.unit.close()
        reopened = self.backend.open_unit(self.store, spec())
        try:
            dir_b, manifest_b = self.export('b')
        finally:
            reopened.close()
        for table in mapping.TABLES:
            self.assertEqual(
                (Path(dir_a) / files.table_path(table)).read_bytes(),
                (Path(dir_b) / files.table_path(table)).read_bytes(),
                table,
            )
        self.assertEqual(
            (Path(dir_a) / files.MAPPING_FILE).read_bytes(),
            (Path(dir_b) / files.MAPPING_FILE).read_bytes(),
        )
        self.assertEqual(
            manifest_a['sourceShardCuts'][0]['committedPosition']['tables'],
            manifest_b['sourceShardCuts'][0]['committedPosition']['tables'],
        )
        self.assertTrue(verify.verify_export(dir_b, KEY)['verified'])

    def test_incremental_delta_after_write_and_redelivery(self):
        seed(self.unit)
        dir_first, first = self.export('inc1', mode=INCREMENTAL)
        self.assertTrue(verify.verify_export(dir_first, KEY, expected_mode=INCREMENTAL)['verified'])
        start = first['incremental']['endCursor']
        self.assertEqual(start['command_result'], ['c2'])
        self.assertEqual(
            self.unit.apply(command('c4', '2', '0'), 3000)['outcome'], 'new_success',
        )
        dir_second, second = self.export('inc2', mode=INCREMENTAL, start_cursor=start)
        expected_delta = {
            'command_result': [('c4',)],
            'slot_hold': [('fixture-show', '2')],
            'minimal_order': [('order-c4',)],
            'outbox_intent': [('intent-c4',)],
            # ledger.entry_id is not append-monotonic: 'cmd:c4' sorts below
            # the prior endCursor ('obs:...'), so it is outside (start, end].
            # Characterization of table-keyset/1, recorded in the README.
        }
        for table in mapping.TABLES:
            rows = read_rows(dir_second, table)
            pks = [tuple(row[column] for column in mapping.PRIMARY_KEYS[table]) for row in rows]
            self.assertEqual(pks, expected_delta.get(table, []), table)
        # The cut still contains the below-cursor insert and the prefix
        # watermark counts everything <= endCursor as covered by the cursor
        # claim; lag beyond the prefix stays visible (here zero).
        ledger_cut = next(e for e in second['sourceShardCuts'][0]['committedPosition']['tables']
                          if e['table'] == 'ledger')
        ledger_wm = next(w for w in second['projectionAppliedSourceWatermarks']
                         if w['table'] == 'ledger')
        first_ledger_cut = next(e for e in first['sourceShardCuts'][0]['committedPosition']['tables']
                                if e['table'] == 'ledger')
        self.assertEqual(ledger_cut['rowCount'], first_ledger_cut['rowCount'] + 1)
        self.assertEqual(ledger_wm['appliedSourcePosition']['rowCount'], ledger_cut['rowCount'])
        self.assertEqual(ledger_wm['lagRowCount'], 0)
        self.assertEqual(second['incremental']['endCursor']['command_result'], ['c4'])
        for watermark in second['projectionAppliedSourceWatermarks']:
            self.assertEqual(watermark['lagRowCount'], 0)
        self.assertTrue(verify.verify_export(dir_second, KEY)['verified'])
        # Redelivery of the same cursor range is byte-identical (PK dedup).
        dir_again, _ = self.export('inc3', mode=INCREMENTAL, start_cursor=start)
        for table in mapping.TABLES:
            self.assertEqual(
                (Path(dir_second) / files.table_path(table)).read_bytes(),
                (Path(dir_again) / files.table_path(table)).read_bytes(),
                table,
            )
        self.assertTrue(verify.verify_export(dir_again, KEY)['verified'])

    def test_bounded_end_cursor_reports_lag(self):
        seed(self.unit)
        end = {table: None for table in mapping.TABLES}
        end['command_result'] = ['c1']
        directory, manifest = self.export(mode=INCREMENTAL, end_cursor=end)
        watermark = next(w for w in manifest['projectionAppliedSourceWatermarks']
                         if w['table'] == 'command_result')
        cut_entry = manifest['sourceShardCuts'][0]['committedPosition']['tables'][0]
        self.assertEqual(watermark['appliedSourcePosition']['rowCount'], 1)
        self.assertEqual(cut_entry['rowCount'], 2)
        self.assertEqual(watermark['lagRowCount'], 1)
        self.assertEqual(
            [row['command_id'] for row in read_rows(directory, 'command_result')], ['c1'],
        )
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])

    def test_crc_corruption_fails_closed(self):
        seed(self.unit)
        self.backend.corrupt_unit_table(self.store, 'command_result')
        self.assertCode('EXPORT_CHECKSUM', self.source().capture)

    def test_schema_drift_fails_closed(self):
        scratch = str(Path(self.tmp) / 'scratch')
        unit = self.backend.open_unit(scratch, spec())
        unit.apply(command('c1', '0', '0'), 1)
        unit.close()
        conn = self.cluster.connect()
        try:
            conn.execute('SET search_path TO d%s' % store_key(scratch))
            conn.execute('ALTER TABLE command_result DROP COLUMN admitted_bytes')
        finally:
            conn.close()
        self.assertCode('EXPORT_SCHEMA', self.source(scratch).capture)

    def test_missing_schema_fails_closed(self):
        absent = str(Path(self.tmp) / 'never-opened')
        self.assertCode('EXPORT_SOURCE', self.source(absent).capture)

    def test_empty_store_exports_and_verifies(self):
        directory, manifest = self.export()
        self.assertEqual(manifest['content']['rowCount'], 0)
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])

    def test_rollback_registry_across_real_exports(self):
        seed(self.unit)
        dir_a, manifest_a = self.export('a')
        self.unit.apply(command('c5', '3', '0'), 4000)
        dir_b, manifest_b = self.export('b')
        self.assertNotEqual(manifest_a['exportId'], manifest_b['exportId'])
        path = Path(self.tmp) / 'registry.json'
        verify.verify_export(dir_a, KEY, registry=RollbackRegistry(path), export_seq=1)
        self.assertCode(
            'EXPORT_ROLLBACK', verify.verify_export, dir_b, KEY,
            registry=RollbackRegistry(path), export_seq=1,
        )
        verify.verify_export(dir_b, KEY, registry=RollbackRegistry(path), export_seq=2)
        last = RollbackRegistry(path).last(manifest_b['sourceClusterId'])
        self.assertEqual(last, {'exportSeq': 2, 'exportId': manifest_b['exportId']})

    def test_export_takes_no_writer_lock(self):
        seed(self.unit)
        # The open unit holds the single-writer file lock; the export still
        # succeeds because it only opens its own read-only connection.
        directory, _ = self.export()
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])
        # Contrast: a second writer on the same directory is refused.
        with self.assertRaises(StoreError) as caught:
            self.backend.open_unit(self.store, spec())
        self.assertEqual(caught.exception.code, 'JOURNAL_LOCKED')

    def test_mapping_pin_matches_durable_schema(self):
        self.assertEqual(mapping.TABLES, CRC_TABLES)
        for table in CRC_TABLES:
            self.assertEqual(
                export_source._SELECT_COLUMNS[table], durable_schema._COLUMNS[table], table,
            )
        conn = self.cluster.connect()
        try:
            name = 'd' + store_key(self.store)
            conn.execute('SET search_path TO %s' % name)
            self.assertEqual(
                export_source.schema_fingerprint(conn, name),
                export_source.SCHEMA_FINGERPRINT,
            )
        finally:
            conn.close()

    def test_provenance_and_snapshot_identity(self):
        seed(self.unit)
        _, manifest = self.export()
        provenance = manifest['provenance']
        self.assertRegex(provenance['observedLsnAtStart'], _LSN)
        self.assertRegex(provenance['observedLsnAtEnd'], _LSN)
        self.assertGreaterEqual(
            lsn_value(provenance['observedLsnAtEnd']),
            lsn_value(provenance['observedLsnAtStart']),
        )
        self.assertEqual(provenance['createdAt'], CREATED_AT)
        snapshot = manifest['fullSnapshot']
        self.assertEqual(snapshot['isolationLevel'], 'SERIALIZABLE READ ONLY')
        self.assertRegex(snapshot['snapshotId'], _SNAPSHOT)
        position = manifest['sourceShardCuts'][0]['committedPosition']
        self.assertEqual(snapshot['snapshotId'], position['snapshotId'])
        self.assertEqual(snapshot['xmin'], position['xmin'])
        self.assertEqual(snapshot['xmax'], position['xmax'])


if __name__ == '__main__':
    unittest.main()
