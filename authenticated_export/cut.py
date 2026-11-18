"""Source cut and projection watermark documents (contract §§1-2).

A source cut is the committed position of one shard inside one MVCC snapshot:
snapshot identity plus per-table row counts and content hashes. A projection
watermark is the source position already applied, recorded separately. A WAL
LSN alone is provenance, never a cut. For FULL_SNAPSHOT the watermark must
equal the cut; for INCREMENTAL it is the cumulative prefix up to endCursor and
must not exceed the cut. Lag (cut rows beyond the applied prefix) is reported,
never hidden.

Local position shape: {rowCount, contentSha256}, where contentSha256 is the
sha256 of the canonical JSON list of mapped row documents in primary-key
order (crc column included). The prefix hash of a partial incremental
watermark is an authenticated statement about the source: a consumer without
source access can check the count ordering, the boundary equality and the lag
arithmetic, but re-reading the source is required to re-derive a partial
prefix hash. That limit is recorded in the package README, not hidden.
"""

from __future__ import annotations

import hashlib

from readiness.codec import canonical_json

from authenticated_export import FULL_SNAPSHOT, MODES
from authenticated_export.errors import ExportError
from authenticated_export.mapping import TABLES


def content_position(rows):
    """{rowCount, contentSha256} of mapped rows already in primary-key order."""
    return {
        'rowCount': len(rows),
        'contentSha256': hashlib.sha256(canonical_json(rows).encode('utf-8')).hexdigest(),
    }


def position_of(entry):
    """The {rowCount, contentSha256} position carried by a cut table entry."""
    return {'rowCount': entry['rowCount'], 'contentSha256': entry['contentSha256']}


def make_cut(shard_id, snapshot_id, xmin, xmax, positions):
    """One shard cut. positions: {table: {rowCount, contentSha256}}."""
    return {
        'shardId': shard_id,
        'committedPosition': {
            'snapshotId': snapshot_id,
            'xmin': xmin,
            'xmax': xmax,
            'tables': [
                {'table': table, **positions[table]} for table in TABLES
            ],
        },
    }


def cut_fingerprint(cut):
    """Content fingerprint binding the per-table positions of the cut."""
    tables = cut['committedPosition']['tables']
    return hashlib.sha256(canonical_json(tables).encode('utf-8')).hexdigest()


def make_watermark(table, position, snapshot_id, lag_row_count):
    return {
        'table': table,
        'appliedSourcePosition': dict(position),
        'appliedAtSnapshot': snapshot_id,
        'lagRowCount': lag_row_count,
    }


def position_leq(applied, cut):
    """Count ordering with hash equality at the boundary.

    A partial prefix hash cannot be re-derived from the cut alone; when the
    counts are equal the positions must be identical.
    """
    if applied['rowCount'] > cut['rowCount']:
        return False
    if applied['rowCount'] == cut['rowCount']:
        return applied['contentSha256'] == cut['contentSha256']
    return True


def check_watermarks(cut, watermarks, mode):
    """Fail closed unless every watermark is consistent with the cut."""
    if mode not in MODES:
        raise ExportError('EXPORT_MODE')
    position = cut['committedPosition']
    by_table = {entry['table']: entry for entry in position['tables']}
    if len(watermarks) != len(TABLES):
        raise ExportError('EXPORT_WATERMARK')
    seen = set()
    for watermark in watermarks:
        table = watermark['table']
        if table not in by_table or table in seen:
            raise ExportError('EXPORT_WATERMARK')
        seen.add(table)
        applied = watermark['appliedSourcePosition']
        lag = watermark['lagRowCount']
        if watermark['appliedAtSnapshot'] != position['snapshotId']:
            raise ExportError('EXPORT_WATERMARK')
        if not position_leq(applied, by_table[table]):
            raise ExportError('EXPORT_WATERMARK')
        if applied['rowCount'] + lag != by_table[table]['rowCount']:
            raise ExportError('EXPORT_WATERMARK')
        if mode == FULL_SNAPSHOT:
            if applied != position_of(by_table[table]) or lag != 0:
                raise ExportError('EXPORT_WATERMARK')
    return True


def check_snapshot_identity(cut, snapshot_id, xmin, xmax):
    """The cut must carry a real snapshot identity, never an LSN alone."""
    position = cut['committedPosition']
    if position['snapshotId'] != snapshot_id:
        raise ExportError('EXPORT_CUT')
    if position['xmin'] != xmin or position['xmax'] != xmax:
        raise ExportError('EXPORT_CUT')
