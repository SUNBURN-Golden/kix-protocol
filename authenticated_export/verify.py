"""Consumer-side fail-closed verification and the audit trace (contract §§4-5).

verify_export checks, in order: strict manifest parse, structure and mode
metadata, pinned schema/mapping versions, fixture signature, manifestHash,
the exact file set (missing, extra and partial files fail closed), per-file
hashes and row counts, per-row type mapping, primary-key order/uniqueness,
cut/watermark consistency against the actual file content, and optionally the
anti-rollback registry. Nothing is trusted because it is present.

audit_trace resolves query -> exportId -> manifest -> exact source cut and
projection watermarks -> exact files/hashes -> schema and semantics versions,
recomputing every hash from disk. Any broken link raises; a trace is never
returned for a tampered export.

Limits recorded, not hidden: a partial incremental prefix hash is an
authenticated statement about the source (see cut.py); re-deriving it needs
source access. The fixture signature proves possession of the caller key,
not a production trust root.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from readiness.codec import CodecError, strict_loads

from authenticated_export import (
    EXPORT_SCHEMA_VERSION, FULL_SNAPSHOT, SOURCE_SCHEMA_VERSION,
    TYPE_MAPPING_VERSION,
)
from authenticated_export import auth, cut, files, mapping
from authenticated_export.errors import ExportError
from authenticated_export.manifest import validate_manifest


def _load_manifest(directory):
    try:
        data = (Path(directory) / files.MANIFEST_FILE).read_bytes()
    except OSError as exc:
        raise ExportError('EXPORT_FILE') from exc
    try:
        manifest = strict_loads(data)
    except (ValueError, CodecError) as exc:
        raise ExportError('EXPORT_FILE') from exc
    if not isinstance(manifest, dict):
        raise ExportError('EXPORT_FILE')
    return manifest


def _check_versions(manifest):
    if manifest['exportSchemaVersion'] != EXPORT_SCHEMA_VERSION:
        raise ExportError('EXPORT_FIELDS')
    if manifest['sourceSchemaVersion'] != SOURCE_SCHEMA_VERSION:
        raise ExportError('EXPORT_FIELDS')
    if manifest['kernelSemanticsVersions'].get('typeMapping') != TYPE_MAPPING_VERSION:
        raise ExportError('EXPORT_MAPPING')


def _check_incremental_table(table, rows, manifest, cut_entry, watermark):
    incremental = manifest['incremental']
    start = incremental['startCursor'][table]
    end = incremental['endCursor'][table]
    start_pk = None if start is None else tuple(start)
    end_pk = None if end is None else tuple(end)
    for row in rows:
        pk = files.row_pk(table, row)
        if start_pk is not None and pk <= start_pk:
            raise ExportError('EXPORT_CURSOR')
        if end_pk is not None and pk > end_pk:
            raise ExportError('EXPORT_CURSOR')
    expected_end = files.row_pk(table, rows[-1]) if rows else start_pk
    if end_pk != expected_end:
        raise ExportError('EXPORT_CURSOR')
    applied = watermark['appliedSourcePosition']
    if len(rows) > applied['rowCount']:
        raise ExportError('EXPORT_WATERMARK')
    if applied['rowCount'] == cut_entry['rowCount'] and start_pk is None:
        # Caught up from the beginning: the delta is the whole cut content.
        if cut.content_position(rows) != cut.position_of(cut_entry):
            raise ExportError('EXPORT_WATERMARK')


def verify_export(directory, key, *, registry=None, export_seq=None, expected_mode=None):
    """Verify one export directory. Returns a report; raises ExportError."""
    root = Path(directory)
    manifest = _load_manifest(root)
    validate_manifest(manifest)
    if expected_mode is not None and manifest['exportMode'] != expected_mode:
        raise ExportError('EXPORT_MODE')
    _check_versions(manifest)
    if not auth.verify(manifest, key):
        raise ExportError('EXPORT_SIGNATURE')

    content = manifest['content']
    files.check_file_set(root, content['perFileHash'])
    entries = {entry['path']: entry for entry in content['perFileHash']}
    expected_paths = {files.table_path(table) for table in mapping.TABLES}
    expected_paths.add(files.MAPPING_FILE)
    if set(entries) != expected_paths:
        raise ExportError('EXPORT_FILE')
    descriptor = files.read_mapping_file(root, entries[files.MAPPING_FILE])
    if descriptor != mapping.descriptor():
        raise ExportError('EXPORT_MAPPING')

    mode = manifest['exportMode']
    position = manifest['sourceShardCuts'][0]['committedPosition']
    cut_by_table = {entry['table']: entry for entry in position['tables']}
    watermark_by_table = {
        entry['table']: entry for entry in manifest['projectionAppliedSourceWatermarks']
    }
    total = 0
    for table in mapping.TABLES:
        rows = files.read_table_file(root, entries[files.table_path(table)])
        for row in rows:
            mapping.check_mapped_row(table, row)
        total += len(rows)
        if mode == FULL_SNAPSHOT:
            position_here = cut.content_position(rows)
            if position_here != cut.position_of(cut_by_table[table]):
                raise ExportError('EXPORT_CUT')
            if position_here != watermark_by_table[table]['appliedSourcePosition']:
                raise ExportError('EXPORT_WATERMARK')
        else:
            _check_incremental_table(
                table, rows, manifest, cut_by_table[table], watermark_by_table[table],
            )
    if total != content['rowCount']:
        raise ExportError('EXPORT_FIELDS')

    rollback_recorded = False
    if registry is not None:
        if export_seq is None:
            raise ExportError('EXPORT_ROLLBACK')
        registry.check_and_record(manifest, export_seq)
        rollback_recorded = True
    return {
        'exportId': manifest['exportId'],
        'exportMode': mode,
        'sourceClusterId': manifest['sourceClusterId'],
        'rowCount': total,
        'fileCount': content['fileCount'],
        'verified': True,
        'rollbackRecorded': rollback_recorded,
    }


def audit_trace(directory, key=None):
    """Resolve the full audit chain, recomputing every hash from disk.

    query -> exportId -> manifest -> source cut / projection watermarks ->
    files/hashes -> schema and semantics versions. With a key, the fixture
    signature is checked too. Any mismatch raises ExportError.
    """
    root = Path(directory)
    manifest = _load_manifest(root)
    validate_manifest(manifest)
    _check_versions(manifest)
    if key is not None and not auth.verify(manifest, key):
        raise ExportError('EXPORT_SIGNATURE')
    content = manifest['content']
    files.check_file_set(root, content['perFileHash'])
    entries = {entry['path']: entry for entry in content['perFileHash']}

    trace_files = []
    for entry in content['perFileHash']:
        path = root / entry['path']
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ExportError('EXPORT_TRACE') from exc
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry['sha256']:
            raise ExportError('EXPORT_TRACE')
        record = {'path': entry['path'], 'sha256': digest, 'rowCount': entry['rowCount']}
        if entry['path'] != files.MAPPING_FILE:
            rows = files.read_table_file(root, entry)
            for row in rows:
                mapping.check_mapped_row(_table_of(entry['path']), row)
            record['contentSha256'] = cut.content_position(rows)['contentSha256']
        trace_files.append(record)

    mode = manifest['exportMode']
    isolation = (
        manifest['fullSnapshot']['isolationLevel'] if mode == FULL_SNAPSHOT
        else 'SERIALIZABLE READ ONLY (local exporter pin)'
    )
    return {
        'query': {
            'kind': 'local-serializable-snapshot-read',
            'isolationLevel': isolation,
            'tables': list(mapping.TABLES),
        },
        'exportId': manifest['exportId'],
        'manifest': {
            'path': files.MANIFEST_FILE,
            'sha256': hashlib.sha256(
                (root / files.MANIFEST_FILE).read_bytes(),
            ).hexdigest(),
            'manifestHash': content['manifestHash'],
        },
        'sourceCut': manifest['sourceShardCuts'][0],
        'consistentCutProofOrDecisionBoundary': manifest['consistentCutProofOrDecisionBoundary'],
        'projectionAppliedSourceWatermarks': manifest['projectionAppliedSourceWatermarks'],
        'files': trace_files,
        'schemaVersions': {
            'sourceSchemaVersion': manifest['sourceSchemaVersion'],
            'exportSchemaVersion': manifest['exportSchemaVersion'],
            'kernelSemanticsVersions': manifest['kernelSemanticsVersions'],
        },
        'linksResolved': True,
    }


def _table_of(path):
    for table in mapping.TABLES:
        if path == files.table_path(table):
            return table
    raise ExportError('EXPORT_TRACE')
