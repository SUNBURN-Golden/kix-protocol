"""Export orchestration, pure over an injected source adapter.

The source adapter captures one consistent snapshot and yields raw row
documents; this module maps, orders, hashes, manifests and signs. It performs
no I/O against the source itself and takes no writer lock. The PG-bound
adapter lives in source.py; offline tests inject a fixture source.

Source capture protocol (duck-typed):
    cluster_id: str            sourceClusterId label
    snapshot_id: str           MVCC snapshot identity (never an LSN alone)
    xmin, xmax: int            snapshot identity components
    isolation_level: str       e.g. 'SERIALIZABLE READ ONLY'
    lsn_start: str | None      WAL provenance at capture start
    tables() -> tuple          business tables, in pin order
    rows(table) -> list[dict]  raw column documents; inbox_delivery carries
                               'raw' bytes; CRC-verified by the adapter
    lsn_end() -> str | None    WAL provenance at capture end
    close()                    release the snapshot

FULL_SNAPSHOT exports every row of the cut and its watermarks equal the cut.
INCREMENTAL exports the per-table keyset delta (startCursor, endCursor],
records the cumulative applied prefix as the watermark, and reports lag (cut
rows beyond the prefix). Redelivery of the same cursor range is byte-identical:
stable primary-key identity is the dedup key.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from readiness.codec import canonical_json

from authenticated_export import (
    BOUNDARY_SEMANTICS, CURSOR_KIND, FULL_SNAPSHOT, INCREMENTAL, MODES, SHARD_ID,
)
from authenticated_export import auth, cut, files, manifest as manifest_mod, mapping
from authenticated_export.errors import ExportError


def _check_created_at(created_at):
    if not isinstance(created_at, int) or isinstance(created_at, bool) or created_at < 0:
        raise ExportError('EXPORT_FIELDS')


def _normalize_cursor(cursor):
    if cursor is None:
        return {table: None for table in mapping.TABLES}
    manifest_mod._check_cursor(cursor, 'EXPORT_CURSOR')
    return {table: cursor[table] for table in mapping.TABLES}


def _pk_tuple(value):
    return None if value is None else tuple(value)


def _select(table, rows, start_pk, end_pk):
    """Keyset delta (start, end] over rows already in primary-key order."""
    selected = []
    for row in rows:
        pk = files.row_pk(table, row)
        if start_pk is not None and pk <= start_pk:
            continue
        if end_pk is not None and pk > end_pk:
            continue
        selected.append(row)
    return selected


def export_source(source, directory, *, mode, key, key_version, created_at,
                  export_id=None, start_cursor=None, end_cursor=None):
    """Run one export into an empty directory and return the signed manifest.

    created_at is caller-supplied epoch milliseconds (no clock policy). The
    export sequence used for anti-rollback travels beside the manifest at
    verification time; it is not a manifest field (fixture boundary).
    """
    if mode not in MODES:
        raise ExportError('EXPORT_MODE')
    _check_created_at(created_at)
    if mode == FULL_SNAPSHOT and (start_cursor is not None or end_cursor is not None):
        raise ExportError('EXPORT_CURSOR')
    start = _normalize_cursor(start_cursor) if mode == INCREMENTAL else None
    end_bound = _normalize_cursor(end_cursor) if mode == INCREMENTAL else None

    root = Path(directory)
    if root.exists() and any(root.rglob('*')):
        raise ExportError('EXPORT_FILE')

    capture = source.capture()
    try:
        if tuple(capture.tables()) != mapping.TABLES:
            raise ExportError('EXPORT_SOURCE')
        all_rows = {}
        for table in mapping.TABLES:
            mapped = [mapping.map_row(table, document) for document in capture.rows(table)]
            all_rows[table] = files.sort_rows(table, mapped)

        delta = {}
        prefix = {}
        end_cursor = {table: None for table in mapping.TABLES}
        for table in mapping.TABLES:
            rows = all_rows[table]
            if mode == FULL_SNAPSHOT:
                delta[table] = rows
                prefix[table] = rows
                continue
            start_pk = _pk_tuple(start[table])
            bound_pk = _pk_tuple(end_bound[table])
            if start_pk is not None and bound_pk is not None and bound_pk < start_pk:
                raise ExportError('EXPORT_CURSOR')
            selected = _select(table, rows, start_pk, bound_pk)
            delta[table] = selected
            effective_end = files.row_pk(table, selected[-1]) if selected else start_pk
            end_cursor[table] = list(effective_end) if effective_end is not None else None
            prefix[table] = [
                row for row in rows
                if effective_end is not None and files.row_pk(table, row) <= effective_end
            ]

        root.mkdir(parents=True, exist_ok=True)
        per_file = [
            files.write_table_file(root, table, delta[table]) for table in mapping.TABLES
        ]
        per_file.append(files.write_mapping_file(root, mapping.descriptor()))

        positions = {
            table: cut.content_position(all_rows[table]) for table in mapping.TABLES
        }
        source_cut = cut.make_cut(
            SHARD_ID, capture.snapshot_id, capture.xmin, capture.xmax, positions,
        )
        fingerprint = cut.cut_fingerprint(source_cut)
        watermarks = [
            cut.make_watermark(
                table, cut.content_position(prefix[table]), capture.snapshot_id,
                len(all_rows[table]) - len(prefix[table]),
            )
            for table in mapping.TABLES
        ]
        if mode == FULL_SNAPSHOT:
            full_snapshot = {
                'isolationLevel': capture.isolation_level,
                'snapshotId': capture.snapshot_id,
                'fingerprint': fingerprint,
                'xmin': capture.xmin,
                'xmax': capture.xmax,
            }
            incremental = None
        else:
            full_snapshot = None
            incremental = {
                'cursorKind': CURSOR_KIND,
                'startCursor': start,
                'endCursor': end_cursor,
                'boundarySemantics': BOUNDARY_SEMANTICS,
            }
        if export_id is None:
            export_id = 'exp-' + hashlib.sha256(
                canonical_json([
                    capture.cluster_id, mode, capture.snapshot_id,
                    start, end_cursor, fingerprint,
                ]).encode('utf-8'),
            ).hexdigest()[:16]
        document = manifest_mod.build_manifest(
            export_id=export_id,
            mode=mode,
            source_cluster_id=capture.cluster_id,
            cut=source_cut,
            watermarks=watermarks,
            full_snapshot=full_snapshot,
            incremental=incremental,
            provenance={
                'observedLsnAtStart': capture.lsn_start,
                'observedLsnAtEnd': capture.lsn_end(),
                'createdAt': created_at,
            },
            content={
                'rowCount': sum(len(delta[table]) for table in mapping.TABLES),
                'fileCount': len(per_file),
                'perFileHash': per_file,
                'partitionManifest': [],
            },
            key_version=key_version,
        )
        signed = auth.sign(document, key, key_version)
        manifest_mod.validate_manifest(signed)
        (root / files.MANIFEST_FILE).write_bytes(
            (canonical_json(signed) + '\n').encode('utf-8'),
        )
        return signed
    finally:
        capture.close()
