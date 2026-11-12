"""The local ExportManifestV1-shaped document (contract §3).

Field names are exactly the contract's. This is a local fixture document, not
a registered production wire schema: registering one is DECISION_REQUIRED ·
Astra (contract §3 preamble). FULL_SNAPSHOT carries snapshot/cut metadata and
INCREMENTAL carries cursor metadata; the two are never merged into one
ambiguous commitPosition. signature and keyVersion sit outside the signed
body's hash base the same way as the onsale token pattern: manifestHash is
the sha256 of the canonical body without manifestHash and without signature;
the fixture signature covers the body including manifestHash and keyVersion.
"""

from __future__ import annotations

import hashlib
import re

from readiness.codec import CodecError, canonical_json

from authenticated_export import (
    BOUNDARY_SEMANTICS, CURSOR_KIND, FULL_SNAPSHOT, INCREMENTAL, MODES,
)
from authenticated_export.cut import check_watermarks
from authenticated_export.errors import ExportError
from authenticated_export.mapping import PRIMARY_KEYS, TABLES

# Contract §3 fields, in contract order, plus the fixture authentication
# fields. signature is the only field outside the signed body.
MANIFEST_FIELDS = (
    'exportId', 'exportMode', 'executionProfile',
    'sourceClusterId', 'authorityScope', 'authorityPlacementVersion',
    'sourceShardCuts', 'consistentCutProofOrDecisionBoundary',
    'sourceSchemaVersion', 'kernelSemanticsVersions', 'exportSchemaVersion',
    'projectionAppliedSourceWatermarks',
    'fullSnapshot', 'incremental', 'provenance', 'content',
    'keyVersion', 'signature',
)
_BODY_FIELDS = tuple(name for name in MANIFEST_FIELDS if name != 'signature')

_FULL_SNAPSHOT_FIELDS = ('isolationLevel', 'snapshotId', 'fingerprint', 'xmin', 'xmax')
_INCREMENTAL_FIELDS = ('cursorKind', 'startCursor', 'endCursor', 'boundarySemantics')
_PROVENANCE_FIELDS = ('observedLsnAtStart', 'observedLsnAtEnd', 'createdAt')
_CONTENT_FIELDS = ('rowCount', 'fileCount', 'perFileHash', 'manifestHash', 'partitionManifest')
_CUT_FIELDS = ('shardId', 'committedPosition')
_POSITION_FIELDS = ('snapshotId', 'xmin', 'xmax', 'tables')
_TABLE_POSITION_FIELDS = ('table', 'rowCount', 'contentSha256')
_WATERMARK_FIELDS = ('table', 'appliedSourcePosition', 'appliedAtSnapshot', 'lagRowCount')
_APPLIED_FIELDS = ('rowCount', 'contentSha256')
_FILE_FIELDS = ('path', 'sha256', 'rowCount')

_HEX = re.compile(r'^[0-9a-f]{64}$')


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _text(value):
    return isinstance(value, str) and bool(value)


def _hex(value):
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def _fields(document, names, code):
    if not isinstance(document, dict) or set(document) != set(names):
        raise ExportError(code)


def unsigned_body(manifest):
    """The canonical signed body: every §3 field except the signature."""
    _fields(manifest, MANIFEST_FIELDS, 'EXPORT_FIELDS')
    return {name: manifest[name] for name in _BODY_FIELDS}


def hash_base(manifest):
    """The body without content.manifestHash and without signature."""
    body = unsigned_body(manifest)
    content = dict(body['content'])
    content.pop('manifestHash', None)
    body['content'] = content
    return body


def compute_manifest_hash(manifest):
    return hashlib.sha256(canonical_json(hash_base(manifest)).encode('utf-8')).hexdigest()


def _check_cursor(cursor, code):
    """None or {table: None | [pk values]} with the pinned key shapes."""
    from authenticated_export.mapping import _COLUMNS, INT
    if cursor is None:
        return
    if not isinstance(cursor, dict) or set(cursor) != set(TABLES):
        raise ExportError(code)
    for table in TABLES:
        value = cursor[table]
        if value is None:
            continue
        columns = PRIMARY_KEYS[table]
        if not isinstance(value, list) or len(value) != len(columns):
            raise ExportError(code)
        for column, part in zip(columns, value):
            if _COLUMNS[table][column] == INT:
                if not _is_int(part) or part < 0:
                    raise ExportError(code)
            elif not _text(part):
                raise ExportError(code)


def _check_cut(cut):
    _fields(cut, _CUT_FIELDS, 'EXPORT_CUT')
    if not _text(cut['shardId']):
        raise ExportError('EXPORT_CUT')
    position = cut['committedPosition']
    _fields(position, _POSITION_FIELDS, 'EXPORT_CUT')
    # A WAL LSN alone is provenance, never a cut (contract §§1-2).
    if not _text(position['snapshotId']):
        raise ExportError('EXPORT_CUT')
    if not _is_int(position['xmin']) or position['xmin'] < 0:
        raise ExportError('EXPORT_CUT')
    if not _is_int(position['xmax']) or position['xmax'] < 0:
        raise ExportError('EXPORT_CUT')
    tables = position['tables']
    if not isinstance(tables, list) or len(tables) != len(TABLES):
        raise ExportError('EXPORT_CUT')
    for entry, table in zip(tables, TABLES):
        _fields(entry, _TABLE_POSITION_FIELDS, 'EXPORT_CUT')
        if entry['table'] != table:
            raise ExportError('EXPORT_CUT')
        if not _is_int(entry['rowCount']) or entry['rowCount'] < 0:
            raise ExportError('EXPORT_CUT')
        if not _hex(entry['contentSha256']):
            raise ExportError('EXPORT_CUT')


def validate_manifest(manifest):
    """Structural, mode and cut/watermark validation. Fail closed.

    This checks the document alone. File hashes, the signature and the
    registry are checked by verify.py against the actual export directory.
    """
    _fields(manifest, MANIFEST_FIELDS, 'EXPORT_FIELDS')
    for name in ('exportId', 'executionProfile', 'sourceClusterId', 'authorityScope',
                 'authorityPlacementVersion', 'consistentCutProofOrDecisionBoundary',
                 'sourceSchemaVersion', 'exportSchemaVersion', 'keyVersion'):
        if not _text(manifest[name]):
            raise ExportError('EXPORT_FIELDS')
    mode = manifest['exportMode']
    if mode not in MODES:
        raise ExportError('EXPORT_MODE')
    semantics = manifest['kernelSemanticsVersions']
    if not isinstance(semantics, dict) or not _text(semantics.get('typeMapping')):
        raise ExportError('EXPORT_FIELDS')

    cuts = manifest['sourceShardCuts']
    # Single shard only: the cross-shard coordinator protocol does not exist,
    # so a multi-shard cut cannot be certified here (contract §1).
    if not isinstance(cuts, list) or len(cuts) != 1:
        raise ExportError('EXPORT_CUT')
    cut = cuts[0]
    _check_cut(cut)
    position = cut['committedPosition']

    watermarks = manifest['projectionAppliedSourceWatermarks']
    if not isinstance(watermarks, list):
        raise ExportError('EXPORT_WATERMARK')
    for watermark in watermarks:
        _fields(watermark, _WATERMARK_FIELDS, 'EXPORT_WATERMARK')
        _fields(watermark['appliedSourcePosition'], _APPLIED_FIELDS, 'EXPORT_WATERMARK')
        applied = watermark['appliedSourcePosition']
        if not _is_int(applied['rowCount']) or applied['rowCount'] < 0:
            raise ExportError('EXPORT_WATERMARK')
        if not _hex(applied['contentSha256']):
            raise ExportError('EXPORT_WATERMARK')
        if not _text(watermark['appliedAtSnapshot']):
            raise ExportError('EXPORT_WATERMARK')
        if not _is_int(watermark['lagRowCount']) or watermark['lagRowCount'] < 0:
            raise ExportError('EXPORT_WATERMARK')
    check_watermarks(cut, watermarks, mode)

    if mode == FULL_SNAPSHOT:
        snapshot = manifest['fullSnapshot']
        _fields(snapshot, _FULL_SNAPSHOT_FIELDS, 'EXPORT_MODE')
        if not _text(snapshot['isolationLevel']):
            raise ExportError('EXPORT_MODE')
        if snapshot['snapshotId'] != position['snapshotId']:
            raise ExportError('EXPORT_MODE')
        if not _hex(snapshot['fingerprint']):
            raise ExportError('EXPORT_MODE')
        if snapshot['xmin'] != position['xmin'] or snapshot['xmax'] != position['xmax']:
            raise ExportError('EXPORT_MODE')
        if manifest['incremental'] is not None:
            raise ExportError('EXPORT_MODE')
    else:
        if manifest['fullSnapshot'] is not None:
            raise ExportError('EXPORT_MODE')
        incremental = manifest['incremental']
        _fields(incremental, _INCREMENTAL_FIELDS, 'EXPORT_MODE')
        if incremental['cursorKind'] != CURSOR_KIND:
            raise ExportError('EXPORT_MODE')
        if incremental['boundarySemantics'] != BOUNDARY_SEMANTICS:
            raise ExportError('EXPORT_MODE')
        _check_cursor(incremental['startCursor'], 'EXPORT_CURSOR')
        _check_cursor(incremental['endCursor'], 'EXPORT_CURSOR')

    provenance = manifest['provenance']
    _fields(provenance, _PROVENANCE_FIELDS, 'EXPORT_FIELDS')
    for name in ('observedLsnAtStart', 'observedLsnAtEnd'):
        value = provenance[name]
        if value is not None and not _text(value):
            raise ExportError('EXPORT_FIELDS')
    if not _is_int(provenance['createdAt']) or provenance['createdAt'] < 0:
        raise ExportError('EXPORT_FIELDS')

    content = manifest['content']
    _fields(content, _CONTENT_FIELDS, 'EXPORT_FIELDS')
    if not _is_int(content['rowCount']) or content['rowCount'] < 0:
        raise ExportError('EXPORT_FIELDS')
    per_file = content['perFileHash']
    if not isinstance(per_file, list) or not per_file:
        raise ExportError('EXPORT_FIELDS')
    if not _is_int(content['fileCount']) or content['fileCount'] != len(per_file):
        raise ExportError('EXPORT_FIELDS')
    paths = set()
    total = 0
    for entry in per_file:
        _fields(entry, _FILE_FIELDS, 'EXPORT_FIELDS')
        if not _text(entry['path']) or entry['path'] in paths:
            raise ExportError('EXPORT_FIELDS')
        paths.add(entry['path'])
        if not _hex(entry['sha256']):
            raise ExportError('EXPORT_FIELDS')
        if not _is_int(entry['rowCount']) or entry['rowCount'] < 0:
            raise ExportError('EXPORT_FIELDS')
        total += entry['rowCount']
    if total != content['rowCount']:
        raise ExportError('EXPORT_FIELDS')
    if not _hex(content['manifestHash']):
        raise ExportError('EXPORT_FIELDS')
    if not isinstance(content['partitionManifest'], list):
        raise ExportError('EXPORT_FIELDS')
    if not _hex(manifest['signature']):
        raise ExportError('EXPORT_FIELDS')
    try:
        recomputed = compute_manifest_hash(manifest)
    except (CodecError, TypeError, ValueError) as exc:
        raise ExportError('EXPORT_FIELDS') from exc
    if recomputed != content['manifestHash']:
        raise ExportError('EXPORT_HASH')
    return True


def build_manifest(*, export_id, mode, source_cluster_id, cut, watermarks,
                   full_snapshot, incremental, provenance, content, key_version):
    """Assemble the unsigned document with manifestHash bound in."""
    manifest = {
        'exportId': export_id,
        'exportMode': mode,
        'executionProfile': None,
        'sourceClusterId': source_cluster_id,
        'authorityScope': None,
        'authorityPlacementVersion': None,
        'sourceShardCuts': [cut],
        'consistentCutProofOrDecisionBoundary': None,
        'sourceSchemaVersion': None,
        'kernelSemanticsVersions': None,
        'exportSchemaVersion': None,
        'projectionAppliedSourceWatermarks': watermarks,
        'fullSnapshot': full_snapshot,
        'incremental': incremental,
        'provenance': provenance,
        'content': dict(content),
        'keyVersion': key_version,
        'signature': None,
    }
    from authenticated_export import (
        AUTHORITY_PLACEMENT_VERSION, AUTHORITY_SCOPE, CUT_DECISION_BOUNDARY,
        EXECUTION_PROFILE, EXPORT_SCHEMA_VERSION, SOURCE_SCHEMA_VERSION,
        TYPE_MAPPING_VERSION,
    )
    manifest['executionProfile'] = EXECUTION_PROFILE
    manifest['authorityScope'] = AUTHORITY_SCOPE
    manifest['authorityPlacementVersion'] = AUTHORITY_PLACEMENT_VERSION
    manifest['consistentCutProofOrDecisionBoundary'] = CUT_DECISION_BOUNDARY
    manifest['sourceSchemaVersion'] = SOURCE_SCHEMA_VERSION
    manifest['kernelSemanticsVersions'] = {
        'typeMapping': TYPE_MAPPING_VERSION,
        'sourceModel': SOURCE_SCHEMA_VERSION,
    }
    manifest['exportSchemaVersion'] = EXPORT_SCHEMA_VERSION
    manifest['content']['manifestHash'] = compute_manifest_hash(manifest)
    return manifest
