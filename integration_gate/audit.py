"""Structured audit lines for the loopback gate.

Lines describe transport handling. They are not protocol events and they are
not a production conformance log.
"""

from __future__ import annotations

import json
import threading
import time

_LOCK = threading.Lock()


def emit(stream, **fields):
    if 'body' in fields or 'entry' in fields:
        raise RuntimeError('AUDIT_BODY')
    record = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'component': 'integration-gate',
        'protocolTruth': False,
        'productionConformance': False,
        'productionReadiness': False,
        'productionEndpoint': False,
    }
    record.update({key: value for key, value in fields.items() if value is not None})
    if record.get('protocolTruth') is not False or record.get('productionConformance') is not False:
        raise RuntimeError('AUDIT_LABEL')
    if record.get('productionReadiness') is not False or record.get('productionEndpoint') is not False:
        raise RuntimeError('AUDIT_LABEL')
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    with _LOCK:
        stream.write(line + '\n')
        stream.flush()
