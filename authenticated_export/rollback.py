"""Consumer-side anti-rollback registry (contract §4, fixture boundary).

One local JSON file records, per sourceClusterId, the last accepted exportSeq
and exportId. A manifest presented with a sequence at or below the recorded
one is rejected. The sequence is caller-supplied and monotonic; this module
invents no clock, frequency or retention policy. The production registry,
trust root and anti-rollback policy are DECISION_REQUIRED · Astra; binding
the sequence into a signed production manifest is part of that undecided
policy, so here the sequence travels beside the manifest as a transport
ordinal and the registry binds it to the verified exportId on acceptance.

The registry fails closed on a corrupt file and writes atomically
(temporary file + rename). It is consumer state, never exporter state.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from readiness.codec import CodecError, strict_loads

from authenticated_export.errors import ExportError

REGISTRY_VERSION = 'kix-local-export-rollback/1'


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class RollbackRegistry:
    def __init__(self, path):
        self.path = Path(path)

    def _load(self):
        if not self.path.exists():
            return {'registryVersion': REGISTRY_VERSION, 'sources': {}}
        try:
            document = strict_loads(self.path.read_bytes())
        except (OSError, ValueError, CodecError) as exc:
            raise ExportError('EXPORT_REGISTRY') from exc
        if (
            not isinstance(document, dict)
            or document.get('registryVersion') != REGISTRY_VERSION
            or not isinstance(document.get('sources'), dict)
        ):
            raise ExportError('EXPORT_REGISTRY')
        for cluster_id, entry in document['sources'].items():
            if (
                not isinstance(cluster_id, str)
                or not isinstance(entry, dict)
                or set(entry) != {'exportSeq', 'exportId'}
                or not _is_int(entry['exportSeq'])
                or entry['exportSeq'] < 1
                or not isinstance(entry['exportId'], str)
                or not entry['exportId']
            ):
                raise ExportError('EXPORT_REGISTRY')
        return document

    def last(self, source_cluster_id):
        """The last accepted {exportSeq, exportId}, or None."""
        return self._load()['sources'].get(source_cluster_id)

    def check_and_record(self, manifest, export_seq):
        """Reject seq <= last; otherwise record atomically. Fail closed.

        Call only after the export itself has fully verified: acceptance is
        what advances the registry.
        """
        if not isinstance(manifest, dict):
            raise ExportError('EXPORT_REGISTRY')
        cluster_id = manifest.get('sourceClusterId')
        export_id = manifest.get('exportId')
        if not isinstance(cluster_id, str) or not cluster_id:
            raise ExportError('EXPORT_REGISTRY')
        if not isinstance(export_id, str) or not export_id:
            raise ExportError('EXPORT_REGISTRY')
        if not _is_int(export_seq) or export_seq < 1:
            raise ExportError('EXPORT_ROLLBACK')
        document = self._load()
        known = document['sources'].get(cluster_id)
        if known is not None and export_seq <= known['exportSeq']:
            raise ExportError('EXPORT_ROLLBACK')
        document['sources'][cluster_id] = {'exportSeq': export_seq, 'exportId': export_id}
        self._write(document)
        return True

    def _write(self, document):
        data = (json.dumps(document, indent=2, sort_keys=True) + '\n').encode('utf-8')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), prefix='.registry-')
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.path)
        except OSError as exc:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise ExportError('EXPORT_REGISTRY') from exc
