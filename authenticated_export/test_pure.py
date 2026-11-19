"""Database-free tests of the authenticated export boundary.

Runs anywhere with the stdlib (plus the repo's readiness codec): the source
is an in-memory fixture adapter, so these tests are independent of the
PostgreSQL pin. They cover the contract predicates of runtime/
AUTHENTICATED_EXPORT.md §§1-5: cut vs watermark separation, mode metadata,
fail-closed integrity/authentication, anti-rollback, type mapping and the
audit trace. Fixture rows are synthetic; no product policy value is chosen.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
import zlib
from pathlib import Path

from readiness.codec import canonical_json, strict_loads

from authenticated_export import (
    FULL_SNAPSHOT, INCREMENTAL, TYPE_MAPPING_VERSION,
)
from authenticated_export import auth, cut, exporter, files, mapping, verify
from authenticated_export.errors import ExportError
from authenticated_export.manifest import (
    MANIFEST_FIELDS, compute_manifest_hash, validate_manifest,
)
from authenticated_export.rollback import RollbackRegistry

# Test-only fixture key. Never a secret, never stored by the package.
KEY = b'fixture-export-key-0001'
KEY_VERSION = 'fixture-key/1'
CREATED_AT = 1_760_000_000_000
U128_MAX_TEXT = str((1 << 128) - 1)

SCOPE_DOC = {
    'account': 'fixture-account', 'environment': 'fixture-env',
    'profileVersion': 'fixture-profile-1', 'provider': 'fixture-provider',
}
SCOPE_KEY = canonical_json(SCOPE_DOC)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _crc(table, document, blob=None):
    # Mirror durable.schema.row_crc: the body is the immutable-column
    # document (ledger.is_open is outside the crc by design) and a raw blob
    # is bound by its sha256, never serialized into the body.
    body = {key: value for key, value in document.items()
            if key not in ('raw', 'is_open')}
    if blob is not None:
        body['rawBlobSha256'] = hashlib.sha256(blob).hexdigest()
    return zlib.crc32(canonical_json([table, body]).encode('utf-8')) & 0xFFFFFFFF


def _alias(fact_key):
    return hashlib.sha256(canonical_json([SCOPE_KEY, fact_key]).encode('utf-8')).digest()[:16].hex()


def _fact(fact_key, offset='+09:00'):
    return canonical_json({
        'amountKrw': 10001, 'currency': 'KRW', 'factKey': fact_key, 'kind': 'capture',
        'method': 'fixture-method', 'occurredAtText': '2026-11-12T09:00:00',
        'occurredOffset': offset, 'operation': None, 'scope': SCOPE_DOC, 'status': 'DONE',
    })


def fixture_rows():
    """Synthetic rows for all eleven tables, shaped like stage-5 writes."""
    payload1 = _sha(b'c1-payload')
    payload2 = _sha(b'c2-payload')
    raw = b'{"delivery": "t-1", "entries": []}'
    raw_sha = _sha(raw)
    delivery_id = _sha(canonical_json([SCOPE_KEY, raw_sha]).encode('utf-8'))
    item1 = _sha(canonical_json([delivery_id, 0]).encode('utf-8'))
    item2 = _sha(canonical_json([delivery_id, 1]).encode('utf-8'))
    fact1, fact2 = _fact('k1'), _fact('k2', offset=None)
    obs_id = 'obs-c2-' + payload2

    def stamped(table, document, blob=None):
        document = dict(document)
        document['crc'] = _crc(table, document, blob)
        return document

    rows = {table: [] for table in mapping.TABLES}
    rows['command_result'] = [
        stamped('command_result', {
            'command_id': 'c1', 'payload_sha256': payload1,
            'first_result': canonical_json({'outcome': 'new_success', 'commandId': 'c1'}),
            'outcome': 'new_success', 'amount_u128': U128_MAX_TEXT,
            'admitted_bytes': 120, 'created_ms': 1000,
        }),
        stamped('command_result', {
            'command_id': 'c2', 'payload_sha256': payload2,
            'first_result': canonical_json({'outcome': 'business_rejected', 'commandId': 'c2'}),
            'outcome': 'business_rejected', 'amount_u128': '0',
            'admitted_bytes': 118, 'created_ms': 1001,
        }),
        stamped('command_result', {
            'command_id': 'c3', 'payload_sha256': _sha(b'c3-payload'),
            'first_result': canonical_json({'outcome': 'capacity', 'commandId': 'c3'}),
            'outcome': 'capacity', 'amount_u128': '10001',
            'admitted_bytes': 0, 'created_ms': 1002,
        }),
    ]
    rows['slot_hold'] = [
        stamped('slot_hold', {'show_id': 'fixture-show', 'slot': '0', 'command_id': 'c1'}),
    ]
    rows['minimal_order'] = [
        stamped('minimal_order', {
            'order_id': 'order-c1', 'command_id': 'c1', 'amount_u128': U128_MAX_TEXT,
        }),
    ]
    rows['outbox_intent'] = [
        stamped('outbox_intent', {
            'intent_id': 'intent-c1', 'command_id': 'c1', 'kind': 'FIXTURE_NOT_DISPATCHED',
            'payload_sha256': payload1, 'created_ms': 1000,
        }),
    ]
    rows['outbox_attempt'] = [
        stamped('outbox_attempt', {
            'intent_id': 'intent-c1', 'attempt_no': 1, 'phase': 'ATTEMPTING',
            'result': canonical_json({'intentId': 'intent-c1', 'attemptNo': 1}), 'at_ms': 1000,
        }),
        stamped('outbox_attempt', {
            'intent_id': 'intent-c1', 'attempt_no': 1, 'phase': 'OUTCOME',
            'result': canonical_json({
                'dispatched': False, 'kind': 'FIXTURE_NOT_DISPATCHED', 'unknown': False,
            }),
            'at_ms': 1001,
        }),
    ]
    rows['observation'] = [
        stamped('observation', {
            'observation_id': obs_id, 'command_id': 'c2', 'payload_sha256': payload2,
            'nbytes': 118, 'created_ms': 1001,
        }),
    ]
    rows['ledger'] = [
        stamped('ledger', {
            'entry_id': 'cmd:c1', 'budget_class': 'completion', 'nbytes': 120,
            'created_ms': 1000, 'is_open': True,
        }),
        stamped('ledger', {
            'entry_id': 'inbox:' + delivery_id, 'budget_class': 'inflow',
            'nbytes': len(raw), 'created_ms': 1000, 'is_open': True,
        }),
        stamped('ledger', {
            'entry_id': 'obs:' + obs_id, 'budget_class': 'observation', 'nbytes': 118,
            'created_ms': 1001, 'is_open': True,
        }),
    ]
    rows['event_alias'] = [
        stamped('event_alias', {
            'scope_key': SCOPE_KEY, 'fact_key': 'k1', 'event_item_id': _alias('k1'),
        }),
        stamped('event_alias', {
            'scope_key': SCOPE_KEY, 'fact_key': 'k2', 'event_item_id': _alias('k2'),
        }),
    ]
    rows['inbox_delivery'] = [
        stamped('inbox_delivery', {
            'delivery_id': delivery_id, 'scope_key': SCOPE_KEY, 'raw': raw,
            'raw_sha256': raw_sha, 'headers_json': '{}', 'received_ms': 1000,
            'verification_result': 'FIXTURE_VERIFIED',
        }, blob=raw),
    ]
    rows['inbox_item'] = [
        stamped('inbox_item', {
            'item_id': item1, 'delivery_id': delivery_id, 'item_index': 0,
            'fact_key': 'k1', 'event_item_id': _alias('k1'),
            'evidence_hash': _sha(fact1.encode('utf-8')), 'fact_json': fact1,
            'relation': 'FIRST',
        }),
        stamped('inbox_item', {
            'item_id': item2, 'delivery_id': delivery_id, 'item_index': 1,
            'fact_key': 'k2', 'event_item_id': _alias('k2'),
            'evidence_hash': _sha(fact2.encode('utf-8')), 'fact_json': fact2,
            'relation': 'FIRST',
        }),
    ]
    rows['inbox_state'] = [
        stamped('inbox_state', {'item_id': item1, 'seq': 1, 'state': 'RECEIVED', 'at_ms': 1000}),
        stamped('inbox_state', {'item_id': item2, 'seq': 1, 'state': 'RECEIVED', 'at_ms': 1000}),
    ]
    return rows


class FixtureCapture:
    def __init__(self, rows, cluster_id, snapshot_id, xmin, xmax):
        self._rows = rows
        self.cluster_id = cluster_id
        self.snapshot_id = snapshot_id
        self.xmin = xmin
        self.xmax = xmax
        self.isolation_level = 'SERIALIZABLE READ ONLY'
        self.lsn_start = None
        self.closed = False

    def tables(self):
        return mapping.TABLES

    def rows(self, table):
        return copy.deepcopy(self._rows[table])

    def lsn_end(self):
        return None

    def close(self):
        self.closed = True


class FixtureSource:
    """In-memory source adapter with the same capture protocol as PG."""

    def __init__(self, rows=None, cluster_id='kix-local-durable/fixture0000000000',
                 snapshot_id='fixture-snapshot/1', xmin=100, xmax=200):
        self._rows = fixture_rows() if rows is None else rows
        self._cluster_id = cluster_id
        self._snapshot_id = snapshot_id
        self._xmin = xmin
        self._xmax = xmax
        self.captures = []

    def capture(self):
        capture = FixtureCapture(
            self._rows, self._cluster_id, self._snapshot_id, self._xmin, self._xmax,
        )
        self.captures.append(capture)
        return capture


def load_manifest(directory):
    return strict_loads((Path(directory) / 'manifest.json').read_bytes())


def write_manifest(directory, manifest):
    (Path(directory) / 'manifest.json').write_bytes(
        (canonical_json(manifest) + '\n').encode('utf-8'),
    )


class ExportTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='kix-export-pure-')
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def export(self, name='out', mode=FULL_SNAPSHOT, source=None, **kwargs):
        directory = str(Path(self.tmp) / name)
        manifest = exporter.export_source(
            FixtureSource() if source is None else source, directory,
            mode=mode, key=KEY, key_version=KEY_VERSION, created_at=CREATED_AT, **kwargs,
        )
        return directory, manifest

    def assertCode(self, code, fn, *args, **kwargs):
        with self.assertRaises(ExportError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)


class FullExportTests(ExportTestBase):
    def test_roundtrip_verify_and_report(self):
        directory, manifest = self.export()
        report = verify.verify_export(directory, KEY)
        self.assertTrue(report['verified'])
        self.assertEqual(report['exportMode'], FULL_SNAPSHOT)
        self.assertEqual(report['rowCount'], sum(len(rows) for rows in fixture_rows().values()))
        self.assertEqual(report['fileCount'], len(mapping.TABLES) + 1)
        self.assertEqual(manifest['content']['partitionManifest'], [])

    def test_manifest_exact_contract_fields(self):
        _, manifest = self.export()
        self.assertEqual(set(manifest), set(MANIFEST_FIELDS))
        self.assertEqual(
            set(manifest['content']),
            {'rowCount', 'fileCount', 'perFileHash', 'manifestHash', 'partitionManifest'},
        )
        self.assertEqual(
            set(manifest['fullSnapshot']),
            {'isolationLevel', 'snapshotId', 'fingerprint', 'xmin', 'xmax'},
        )
        self.assertEqual(
            set(manifest['provenance']),
            {'observedLsnAtStart', 'observedLsnAtEnd', 'createdAt'},
        )
        self.assertIsNone(manifest['incremental'])
        self.assertEqual(manifest['exportSchemaVersion'], 'kix-export-manifest-local/1')
        self.assertEqual(manifest['kernelSemanticsVersions']['typeMapping'], TYPE_MAPPING_VERSION)

    def test_watermarks_equal_cut_for_full_snapshot(self):
        _, manifest = self.export()
        position = manifest['sourceShardCuts'][0]['committedPosition']
        by_table = {entry['table']: entry for entry in position['tables']}
        for watermark in manifest['projectionAppliedSourceWatermarks']:
            self.assertEqual(
                watermark['appliedSourcePosition'],
                cut.position_of(by_table[watermark['table']]),
            )
            self.assertEqual(watermark['lagRowCount'], 0)
            self.assertEqual(watermark['appliedAtSnapshot'], position['snapshotId'])

    def test_lsn_only_cut_rejected(self):
        directory, manifest = self.export()
        broken = copy.deepcopy(manifest)
        broken['sourceShardCuts'][0]['committedPosition'] = {'observedLsn': '0/1'}
        self.assertCode('EXPORT_CUT', validate_manifest, broken)
        broken = copy.deepcopy(manifest)
        broken['sourceShardCuts'][0]['committedPosition']['snapshotId'] = ''
        self.assertCode('EXPORT_CUT', validate_manifest, broken)

    def test_multi_shard_cut_rejected(self):
        _, manifest = self.export()
        broken = copy.deepcopy(manifest)
        broken['sourceShardCuts'].append(copy.deepcopy(broken['sourceShardCuts'][0]))
        self.assertCode('EXPORT_CUT', validate_manifest, broken)

    def test_watermark_beyond_cut_rejected(self):
        _, manifest = self.export()
        broken = copy.deepcopy(manifest)
        watermark = broken['projectionAppliedSourceWatermarks'][0]
        watermark['appliedSourcePosition']['rowCount'] += 1
        self.assertCode('EXPORT_WATERMARK', validate_manifest, broken)

    def test_full_watermark_must_equal_cut(self):
        _, manifest = self.export()
        broken = copy.deepcopy(manifest)
        watermark = broken['projectionAppliedSourceWatermarks'][0]
        watermark['appliedSourcePosition']['contentSha256'] = _sha(b'other')
        self.assertCode('EXPORT_WATERMARK', validate_manifest, broken)

    def test_full_snapshot_requires_snapshot_metadata(self):
        _, manifest = self.export()
        broken = copy.deepcopy(manifest)
        broken['fullSnapshot'] = None
        self.assertCode('EXPORT_MODE', validate_manifest, broken)
        broken = copy.deepcopy(manifest)
        broken['incremental'] = {
            'cursorKind': 'table-keyset/1', 'startCursor': None, 'endCursor': None,
            'boundarySemantics': 'startExclusive-endInclusive',
        }
        self.assertCode('EXPORT_MODE', validate_manifest, broken)

    def test_empty_source_exports_and_verifies(self):
        empty = {table: [] for table in mapping.TABLES}
        directory, manifest = self.export(source=FixtureSource(rows=empty))
        self.assertEqual(manifest['content']['rowCount'], 0)
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])

    def test_deterministic_bytes_across_reexport(self):
        dir_a, manifest_a = self.export(name='a')
        dir_b, manifest_b = self.export(name='b')
        self.assertEqual(manifest_a, manifest_b)
        for path in Path(dir_a).rglob('*'):
            if path.is_file():
                other = Path(dir_b) / path.relative_to(dir_a)
                self.assertEqual(path.read_bytes(), other.read_bytes(), str(path))

    def test_capture_closed_after_export(self):
        source = FixtureSource()
        self.export(source=source)
        self.assertTrue(source.captures[0].closed)

    def test_nonempty_directory_refused(self):
        directory, _ = self.export()
        self.assertCode(
            'EXPORT_FILE', exporter.export_source, FixtureSource(), directory,
            mode=FULL_SNAPSHOT, key=KEY, key_version=KEY_VERSION, created_at=CREATED_AT,
        )

    def test_created_at_must_be_epoch_ms_int(self):
        for bad in (True, 1.5, '1000', -1):
            self.assertCode(
                'EXPORT_FIELDS', exporter.export_source, FixtureSource(),
                str(Path(self.tmp) / 'bad'), mode=FULL_SNAPSHOT, key=KEY,
                key_version=KEY_VERSION, created_at=bad,
            )


class IntegrityTests(ExportTestBase):
    def test_tampered_row_file_rejected(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('command_result')
        data = path.read_bytes().replace(b'"c1"', b'"cX"')
        path.write_bytes(data)
        self.assertCode('EXPORT_HASH', verify.verify_export, directory, KEY)

    def test_tampered_manifest_rejected(self):
        directory, manifest = self.export()
        broken = copy.deepcopy(manifest)
        broken['content']['rowCount'] += 1
        write_manifest(directory, broken)
        with self.assertRaises(ExportError):
            verify.verify_export(directory, KEY)

    def test_wrong_key_rejected(self):
        directory, _ = self.export()
        self.assertCode('EXPORT_SIGNATURE', verify.verify_export, directory, b'other-key')

    def test_missing_file_rejected(self):
        directory, _ = self.export()
        (Path(directory) / files.table_path('ledger')).unlink()
        self.assertCode('EXPORT_FILE', verify.verify_export, directory, KEY)

    def test_extra_file_rejected(self):
        directory, _ = self.export()
        (Path(directory) / 'tables' / 'stowaway.jsonl').write_text('{}\n')
        self.assertCode('EXPORT_FILE', verify.verify_export, directory, KEY)

    def test_truncated_file_rejected(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('command_result')
        data = path.read_bytes()
        path.write_bytes(data[:len(data) // 2])
        with self.assertRaises(ExportError):
            verify.verify_export(directory, KEY)

    def test_missing_manifest_rejected(self):
        directory, _ = self.export()
        (Path(directory) / 'manifest.json').unlink()
        self.assertCode('EXPORT_FILE', verify.verify_export, directory, KEY)

    def test_rehash_without_signature_rejected(self):
        """An attacker rewrites a row and re-hashes everything, but cannot sign."""
        directory, manifest = self.export()
        path = Path(directory) / files.table_path('command_result')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        rows[0]['amount_u128'] = '1'
        path.write_bytes(files.file_bytes(rows))
        broken = copy.deepcopy(manifest)
        entry = next(e for e in broken['content']['perFileHash']
                     if e['path'] == files.table_path('command_result'))
        entry['sha256'] = _sha(path.read_bytes())
        position = cut.content_position(rows)
        cut_entry = broken['sourceShardCuts'][0]['committedPosition']['tables'][0]
        cut_entry.update(position)
        broken['projectionAppliedSourceWatermarks'][0]['appliedSourcePosition'] = dict(position)
        fingerprint = cut.cut_fingerprint(broken['sourceShardCuts'][0])
        broken['fullSnapshot']['fingerprint'] = fingerprint
        broken['content']['manifestHash'] = compute_manifest_hash(broken)
        write_manifest(directory, broken)
        self.assertCode('EXPORT_SIGNATURE', verify.verify_export, directory, KEY)

    def test_duplicate_pk_row_rejected(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('ledger')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        data = files.file_bytes(rows + [rows[0]])
        path.write_bytes(data)
        entry = {'path': files.table_path('ledger'), 'sha256': _sha(data), 'rowCount': len(rows) + 1}
        self.assertCode('EXPORT_ROW', files.read_table_file, directory, entry)

    def test_blob_hex_bound_by_sha256(self):
        rows = fixture_rows()['inbox_delivery']
        document = dict(rows[0])
        document['raw'] = bytes(reversed(document['raw']))
        self.assertCode('EXPORT_HASH', mapping.map_row, 'inbox_delivery', document)

    def test_crc_column_is_exported(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('command_result')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        for row in rows:
            self.assertIn('crc', row)
            self.assertEqual(row['crc'], _crc('command_result', {
                key: value for key, value in row.items() if key != 'crc'
            }))


class AuthenticationTests(ExportTestBase):
    def test_key_version_is_signed(self):
        directory, manifest = self.export()
        broken = copy.deepcopy(manifest)
        broken['keyVersion'] = 'fixture-key/2'
        # Re-hash so structural validation passes; the signature must still
        # fail because keyVersion is part of the signed body.
        broken['content']['manifestHash'] = compute_manifest_hash(broken)
        write_manifest(directory, broken)
        self.assertCode('EXPORT_SIGNATURE', verify.verify_export, directory, KEY)

    def test_sign_requires_matching_key_version(self):
        _, manifest = self.export()
        unsigned = dict(manifest)
        unsigned['signature'] = '0' * 64
        self.assertCode('EXPORT_KEY_VERSION', auth.sign, unsigned, KEY, 'other-version')

    def test_empty_key_refused(self):
        _, manifest = self.export()
        self.assertCode('EXPORT_KEY', auth.sign, manifest, b'', KEY_VERSION)
        self.assertFalse(auth.verify(manifest, b''))


class RollbackTests(ExportTestBase):
    def test_rollback_rejects_old_and_equal_seq(self):
        dir_a, _ = self.export(name='a')
        dir_b, _ = self.export(name='b')
        registry = RollbackRegistry(Path(self.tmp) / 'registry.json')
        verify.verify_export(dir_a, KEY, registry=registry, export_seq=5)
        self.assertCode(
            'EXPORT_ROLLBACK', verify.verify_export, dir_b, KEY,
            registry=registry, export_seq=5,
        )
        self.assertCode(
            'EXPORT_ROLLBACK', verify.verify_export, dir_b, KEY,
            registry=registry, export_seq=4,
        )
        self.assertEqual(registry.last('kix-local-durable/fixture0000000000')['exportSeq'], 5)

    def test_advancing_seq_accepted_and_persisted(self):
        dir_a, _ = self.export(name='a')
        dir_b, _ = self.export(name='b')
        path = Path(self.tmp) / 'registry.json'
        verify.verify_export(dir_a, KEY, registry=RollbackRegistry(path), export_seq=1)
        verify.verify_export(dir_b, KEY, registry=RollbackRegistry(path), export_seq=2)
        reopened = RollbackRegistry(path)
        self.assertEqual(reopened.last('kix-local-durable/fixture0000000000')['exportSeq'], 2)

    def test_registry_requires_seq(self):
        directory, _ = self.export()
        registry = RollbackRegistry(Path(self.tmp) / 'registry.json')
        self.assertCode(
            'EXPORT_ROLLBACK', verify.verify_export, directory, KEY, registry=registry,
        )

    def test_corrupt_registry_fails_closed(self):
        path = Path(self.tmp) / 'registry.json'
        path.write_text('{"registryVersion": "wrong", "sources": {}}')
        registry = RollbackRegistry(path)
        directory, _ = self.export()
        self.assertCode(
            'EXPORT_REGISTRY', verify.verify_export, directory, KEY,
            registry=registry, export_seq=1,
        )
        path.write_bytes(b'\xff\xfe not json')
        self.assertCode('EXPORT_REGISTRY', registry.last, 'any')

    def test_bad_seq_refused(self):
        directory, _ = self.export()
        registry = RollbackRegistry(Path(self.tmp) / 'registry.json')
        for bad in (0, -1, True, '1', 1.0):
            self.assertCode(
                'EXPORT_ROLLBACK', verify.verify_export, directory, KEY,
                registry=registry, export_seq=bad,
            )


class TypeMappingTests(ExportTestBase):
    def test_u128_lossless_roundtrip(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('command_result')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        by_id = {row['command_id']: row for row in rows}
        self.assertEqual(by_id['c1']['amount_u128'], U128_MAX_TEXT)
        self.assertEqual(int(by_id['c1']['amount_u128']), (1 << 128) - 1)
        self.assertIsInstance(by_id['c1']['amount_u128'], str)

    def test_no_floats_anywhere_in_export(self):
        directory, _ = self.export()

        def refuse(value):
            raise AssertionError('float in export: %r' % value)

        for path in Path(directory).rglob('*'):
            if path.is_file():
                for line in path.read_bytes().split(b'\n'):
                    if line:
                        json.loads(line, parse_float=refuse, parse_constant=refuse)

    def test_float_and_int_amounts_refused(self):
        row = dict(fixture_rows()['command_result'][0])
        for bad in (1.0, 10001, True, '1e3', '-1', '01', str(1 << 128)):
            broken = dict(row)
            broken['amount_u128'] = bad
            with self.assertRaises(ExportError):
                mapping.map_row('command_result', broken)

    def test_binary32_width_checked(self):
        row = dict(fixture_rows()['command_result'][0])
        for bad in ('a' * 62, 'a' * 66, 'A' * 64, 'g' * 64, 123):
            broken = dict(row)
            broken['payload_sha256'] = bad
            self.assertCode('EXPORT_TYPE', mapping.map_row, 'command_result', broken)

    def test_binary16_width_checked(self):
        row = dict(fixture_rows()['event_alias'][0])
        for bad in ('a' * 30, 'a' * 34, 'A' * 32):
            broken = dict(row)
            broken['event_item_id'] = bad
            self.assertCode('EXPORT_TYPE', mapping.map_row, 'event_alias', broken)

    def test_occurred_time_text_and_offset_preserved(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('inbox_item')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        facts = {row['fact_key']: strict_loads(row['fact_json'].encode()) for row in rows}
        self.assertEqual(facts['k1']['occurredAtText'], '2026-11-12T09:00:00')
        self.assertEqual(facts['k1']['occurredOffset'], '+09:00')
        self.assertIsNone(facts['k2']['occurredOffset'])
        original = {row['fact_key']: row['fact_json']
                    for row in fixture_rows()['inbox_item']}
        for row in rows:
            self.assertEqual(row['fact_json'], original[row['fact_key']])

    def test_vocabulary_pins(self):
        cases = (
            ('command_result', 'outcome', 'bogus'),
            ('inbox_item', 'relation', 'MAYBE'),
            ('inbox_state', 'state', 'PENDING'),
            ('outbox_attempt', 'phase', 'DURING'),
            ('ledger', 'budget_class', 'marketing'),
            ('outbox_intent', 'kind', 'REAL_DISPATCH'),
        )
        for table, column, bad in cases:
            row = dict(fixture_rows()[table][0])
            row[column] = bad
            self.assertCode('EXPORT_VOCAB', mapping.map_row, table, row)

    def test_epoch_ms_unit_and_bool_shapes(self):
        row = dict(fixture_rows()['command_result'][0])
        for bad in (True, '1000', 1.0, -1):
            broken = dict(row)
            broken['created_ms'] = bad
            self.assertCode('EXPORT_TYPE', mapping.map_row, 'command_result', broken)
        ledger = dict(fixture_rows()['ledger'][0])
        ledger['is_open'] = 1
        self.assertCode('EXPORT_TYPE', mapping.map_row, 'ledger', ledger)

    def test_descriptor_pin_enforced_even_with_valid_signature(self):
        directory, manifest = self.export()
        path = Path(directory) / files.MAPPING_FILE
        descriptor = strict_loads(path.read_bytes())
        descriptor['moneyPolicy'] = 'float64 is fine'
        path.write_bytes((canonical_json(descriptor) + '\n').encode('utf-8'))
        broken = copy.deepcopy(manifest)
        entry = next(e for e in broken['content']['perFileHash']
                     if e['path'] == files.MAPPING_FILE)
        entry['sha256'] = _sha(path.read_bytes())
        broken['content']['manifestHash'] = compute_manifest_hash(broken)
        broken = auth.sign(broken, KEY, KEY_VERSION)
        write_manifest(directory, broken)
        self.assertCode('EXPORT_MAPPING', verify.verify_export, directory, KEY)

    def test_mapping_pin_matches_descriptor(self):
        descriptor = mapping.descriptor()
        self.assertEqual(descriptor['version'], TYPE_MAPPING_VERSION)
        self.assertEqual(descriptor['timestampUnit'], 'epoch-milliseconds')
        self.assertEqual(tuple(descriptor['tables']), mapping.TABLES)
        self.assertIn('not used', descriptor['fast64'])


class IncrementalTests(ExportTestBase):
    def test_incremental_requires_cursor_metadata(self):
        directory, manifest = self.export(name='inc', mode=INCREMENTAL)
        broken = copy.deepcopy(manifest)
        broken['incremental'] = None
        self.assertCode('EXPORT_MODE', validate_manifest, broken)
        broken = copy.deepcopy(manifest)
        broken['fullSnapshot'] = {
            'isolationLevel': 'SERIALIZABLE READ ONLY', 'snapshotId': 'fixture-snapshot/1',
            'fingerprint': '0' * 64, 'xmin': 100, 'xmax': 200,
        }
        self.assertCode('EXPORT_MODE', validate_manifest, broken)
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])

    def test_full_snapshot_rejects_cursors(self):
        self.assertCode(
            'EXPORT_CURSOR', exporter.export_source, FixtureSource(),
            str(Path(self.tmp) / 'bad'), mode=FULL_SNAPSHOT, key=KEY,
            key_version=KEY_VERSION, created_at=CREATED_AT,
            start_cursor={table: None for table in mapping.TABLES},
        )

    def test_cursor_boundaries_start_exclusive_end_inclusive(self):
        start = {table: None for table in mapping.TABLES}
        start['command_result'] = ['c1']
        directory, manifest = self.export(mode=INCREMENTAL, start_cursor=start)
        path = Path(directory) / files.table_path('command_result')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        self.assertEqual([row['command_id'] for row in rows], ['c2', 'c3'])
        self.assertEqual(manifest['incremental']['endCursor']['command_result'], ['c3'])
        self.assertTrue(verify.verify_export(directory, KEY, expected_mode=INCREMENTAL)['verified'])

    def test_bounded_end_cursor_reports_lag(self):
        end = {table: None for table in mapping.TABLES}
        end['command_result'] = ['c2']
        directory, manifest = self.export(mode=INCREMENTAL, end_cursor=end)
        watermark = next(w for w in manifest['projectionAppliedSourceWatermarks']
                         if w['table'] == 'command_result')
        cut_entry = manifest['sourceShardCuts'][0]['committedPosition']['tables'][0]
        self.assertEqual(watermark['appliedSourcePosition']['rowCount'], 2)
        self.assertEqual(cut_entry['rowCount'], 3)
        self.assertEqual(watermark['lagRowCount'], 1)
        path = Path(directory) / files.table_path('command_result')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        self.assertEqual([row['command_id'] for row in rows], ['c1', 'c2'])
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])

    def test_caught_up_incremental_watermark_equals_cut(self):
        directory, manifest = self.export(mode=INCREMENTAL)
        position = manifest['sourceShardCuts'][0]['committedPosition']
        by_table = {entry['table']: entry for entry in position['tables']}
        for watermark in manifest['projectionAppliedSourceWatermarks']:
            self.assertEqual(
                watermark['appliedSourcePosition'],
                cut.position_of(by_table[watermark['table']]),
            )
            self.assertEqual(watermark['lagRowCount'], 0)
        self.assertTrue(verify.verify_export(directory, KEY)['verified'])

    def test_redelivery_is_byte_identical_and_dedup_by_pk(self):
        rows = fixture_rows()
        first, manifest_first = self.export(name='d1', mode=INCREMENTAL,
                                            source=FixtureSource(rows=rows))
        start = manifest_first['incremental']['endCursor']
        extended = copy.deepcopy(rows)
        extra = dict(extended['command_result'][0])
        extra['command_id'] = 'c4'
        extra['crc'] = _crc('command_result', {k: v for k, v in extra.items() if k != 'crc'})
        extended['command_result'].append(extra)
        second, manifest_second = self.export(name='d2', mode=INCREMENTAL,
                                              source=FixtureSource(rows=extended),
                                              start_cursor=start)
        path = Path(second) / files.table_path('command_result')
        delta = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        self.assertEqual([row['command_id'] for row in delta], ['c4'])
        third, _ = self.export(name='d3', mode=INCREMENTAL,
                               source=FixtureSource(rows=extended), start_cursor=start)
        for path in Path(second).rglob('*'):
            if path.is_file() and path.name != 'manifest.json':
                other = Path(third) / path.relative_to(second)
                self.assertEqual(path.read_bytes(), other.read_bytes())
        self.assertEqual(
            manifest_second['incremental']['endCursor']['command_result'], ['c4'],
        )
        self.assertTrue(verify.verify_export(second, KEY)['verified'])
        self.assertTrue(verify.verify_export(third, KEY)['verified'])

    def test_end_before_start_refused(self):
        start = {table: None for table in mapping.TABLES}
        end = {table: None for table in mapping.TABLES}
        start['command_result'] = ['c3']
        end['command_result'] = ['c1']
        self.assertCode(
            'EXPORT_CURSOR', exporter.export_source, FixtureSource(),
            str(Path(self.tmp) / 'bad'), mode=INCREMENTAL, key=KEY,
            key_version=KEY_VERSION, created_at=CREATED_AT,
            start_cursor=start, end_cursor=end,
        )

    def test_tampered_delta_outside_cursor_rejected(self):
        start = {table: None for table in mapping.TABLES}
        start['command_result'] = ['c2']
        directory, manifest = self.export(mode=INCREMENTAL, start_cursor=start)
        # Re-hash a delta that smuggles in a row at/below startCursor.
        path = Path(directory) / files.table_path('command_result')
        rows = [strict_loads(line) for line in path.read_bytes().split(b'\n')[:-1]]
        rows.insert(0, copy.deepcopy(fixture_rows()['command_result'][0]))  # c1 <= start
        path.write_bytes(files.file_bytes(rows))
        broken = copy.deepcopy(manifest)
        entry = next(e for e in broken['content']['perFileHash']
                     if e['path'] == files.table_path('command_result'))
        entry['sha256'] = _sha(path.read_bytes())
        entry['rowCount'] = len(rows)
        broken['content']['rowCount'] += 1
        broken['content']['manifestHash'] = compute_manifest_hash(broken)
        broken = auth.sign(broken, KEY, KEY_VERSION)
        write_manifest(directory, broken)
        self.assertCode('EXPORT_CURSOR', verify.verify_export, directory, KEY)


class AuditTraceTests(ExportTestBase):
    def test_trace_resolves_every_link(self):
        directory, manifest = self.export()
        trace = verify.audit_trace(directory, key=KEY)
        self.assertTrue(trace['linksResolved'])
        self.assertEqual(trace['exportId'], manifest['exportId'])
        self.assertEqual(trace['sourceCut'], manifest['sourceShardCuts'][0])
        self.assertEqual(
            trace['projectionAppliedSourceWatermarks'],
            manifest['projectionAppliedSourceWatermarks'],
        )
        self.assertEqual(trace['manifest']['manifestHash'], manifest['content']['manifestHash'])
        self.assertEqual(len(trace['files']), manifest['content']['fileCount'])
        self.assertEqual(
            trace['schemaVersions']['exportSchemaVersion'], manifest['exportSchemaVersion'],
        )
        self.assertEqual(trace['query']['tables'], list(mapping.TABLES))
        by_path = {entry['path']: entry for entry in manifest['content']['perFileHash']}
        for entry in trace['files']:
            self.assertEqual(entry['sha256'], by_path[entry['path']]['sha256'])

    def test_trace_breaks_on_tampered_file(self):
        directory, _ = self.export()
        path = Path(directory) / files.table_path('ledger')
        path.write_bytes(path.read_bytes().replace(b'"cmd:c1"', b'"cmd:cX"'))
        with self.assertRaises(ExportError):
            verify.audit_trace(directory, key=KEY)

    def test_trace_breaks_on_tampered_manifest(self):
        directory, manifest = self.export()
        broken = copy.deepcopy(manifest)
        broken['exportId'] = 'exp-forged'
        write_manifest(directory, broken)
        with self.assertRaises(ExportError):
            verify.audit_trace(directory, key=KEY)

    def test_trace_without_key_still_checks_hashes(self):
        directory, _ = self.export()
        self.assertTrue(verify.audit_trace(directory)['linksResolved'])


if __name__ == '__main__':
    unittest.main()
