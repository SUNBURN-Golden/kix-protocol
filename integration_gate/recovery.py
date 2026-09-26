"""Replay committed local-call receipts into a fresh reference Core.

The journal is a readiness log. The Core remains the semantic source for the
replayed commands. A digest mismatch fails closed and does not drop the record.
"""

from __future__ import annotations

from readiness.codec import receipt_digest
from readiness.store import StoreError


def replay_core(core, records):
    for record in records:
        if record.get('kind') != 'core_commit' or record.get('machine') != 'integration_core':
            raise StoreError('UNEXPECTED_RECORD')
        receipt = core.execute(
            record['operationId'],
            record['actor'],
            record['action'],
            record['body'],
        )
        if receipt_digest(receipt) != record['receiptDigest']:
            raise StoreError('RECEIPT_MISMATCH')
        if not isinstance(receipt, dict):
            raise StoreError('RECEIPT_MISMATCH')
