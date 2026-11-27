"""Fixture resale queries evaluated on the integration gate worker."""
from __future__ import annotations

import base64
from collections import OrderedDict
from dataclasses import dataclass
import hmac
import json
import re
import secrets

from integration_gate.constants import MAX_BODY_BYTES
from readiness.codec import canonical_json, receipt_digest

PAGE_DEFAULT = 20
PAGE_MAX = 100
READ_PREFIX = '/x-kix-contract-only/read/'
READ_SOURCES = {
    'list_open_listings': 'resale',
    'get_listing': 'resale',
    'get_right': 'resale',
    'get_presentation': 'resale',
    'get_settlement': 'settlement',
    'get_operation_recovery': None,
}
READ_PATHS = {READ_PREFIX + query: query for query in READ_SOURCES}
ORDERING = 'listed-journal-position-asc,listing-id-asc'
SUMMARY_FIELDS = ('listing_id', 'show_id', 'amount', 'currency', 'expires_ms', 'expired', 'phase')
RECOVERY_SOURCES = frozenset({'resale', 'settlement'})
RECOVERY_RECEIPTS = 128
RECOVERY_IDENTITIES = 2048
HEX_64 = re.compile(r'[0-9a-f]{64}')
CURSOR = re.compile(r'[A-Za-z0-9_-]{54}')


class ReadRefused(Exception):
    def __init__(self, code, status):
        super().__init__(code)
        self.code = code
        self.status = status


def _not_found():
    return ReadRefused('NOT_FOUND', 404)


@dataclass
class Identity:
    fingerprint: str
    receipt_key: tuple[str, int] | None = None
    ambiguous: bool = False


class ResaleReads:
    def __init__(self, machines, commands):
        self._machines = machines
        self._commands = commands
        self._generation = secrets.token_hex(16)
        self._token_key = secrets.token_bytes(32)
        self._identities = {}
        self._receipts = OrderedDict()

    def _sign(self, purpose, value):
        return hmac.digest(self._token_key, canonical_json([purpose, value]).encode('utf-8'), 'sha256')

    def _position(self, source):
        machine = self._machines[source]
        # Read the existing journal and clock on the worker. Copying the whole
        # journal here would add a growing cost to every correlated write.
        position = {'journal_entries': len(machine._journal)}
        if source == 'resale':
            position['logical_time_ms'] = machine._now
        return position

    def _watermark(self, source):
        cut = {'source': source, 'generation': self._generation, **self._position(source)}
        return {**cut, 'token': self._sign('watermark', cut).hex()}

    def _covers(self, later, earlier):
        token = earlier['token']
        if (earlier['source'] != later['source'] or earlier['generation'] != self._generation
                or ('logical_time_ms' in earlier) != ('logical_time_ms' in later)
                or earlier['journal_entries'] > later['journal_entries']
                or earlier.get('logical_time_ms', 0) > later.get('logical_time_ms', 0)
                or not HEX_64.fullmatch(token)):
            return False
        cut = {key: value for key, value in earlier.items() if key != 'token'}
        return hmac.compare_digest(token, self._sign('watermark', cut).hex())

    def note_attempt(self, operation_id, trace_id, actor, action, body):
        """Fence rebinding even for a refused or out-of-scope local call."""
        # Hash the canonical string using escaped Unicode so existing write
        # envelopes with arbitrary text still follow their original path.
        fingerprint = receipt_digest(json.dumps(
            [operation_id, actor, action, body], sort_keys=True, separators=(',', ':'), allow_nan=True,
        ))
        bound = []
        for kind, value in (('operation_id', operation_id), ('trace_id', trace_id)):
            if not value or len(value) > 100:
                continue
            key = (kind, value)
            identity = self._identities.get(key)
            if identity is None and len(self._identities) < RECOVERY_IDENTITIES:
                identity = self._identities[key] = Identity(fingerprint)
            if identity is None or identity.ambiguous:
                continue
            if identity.fingerprint != fingerprint:
                identity.ambiguous = True
                identity.receipt_key = None
            else:
                bound.append(identity)
        return bound

    def call_fsm(self, call, action, body, actor, identities):
        spec = self._commands[action]
        source, field = spec['machine'], spec['subject_field']
        before = self._position(source) if identities and source in RECOVERY_SOURCES else None
        receipt = call(action, body)
        if before is not None and receipt['duplicate'] is False and receipt['applied'] == spec['op']:
            after = self._position(source)
            if after['journal_entries'] == before['journal_entries'] + 1:
                subject = {'action': action, 'field': field, 'id': body[field]}
                self._note_acceptance(identities, actor, subject, source, after, receipt)
        return receipt

    def _note_acceptance(self, identities, actor, subject, source, position, receipt):
        eligible = [identity for identity in identities if identity.receipt_key is None]
        if not eligible:
            return
        encoded = canonical_json(receipt)
        try:
            if len(encoded.encode('utf-8')) > MAX_BODY_BYTES:
                return
        except UnicodeEncodeError:
            return
        key = (source, position['journal_entries'])
        self._receipts[key] = (actor, subject, position, encoded)
        for identity in eligible:
            identity.receipt_key = key
        if len(self._receipts) > RECOVERY_RECEIPTS:
            # Identity slots are retained as tombstones. An evicted alias must
            # never point to a later acceptance in the same process.
            self._receipts.popitem(last=False)

    def read(self, query, request):
        if query == 'get_operation_recovery':
            through = request['through']
            receipt = self._recover(request, through)
            # UNKNOWN has the same body for all missing or unusable evidence.
            if receipt is None:
                return {'status': 'UNKNOWN', 'retry_granted': False}
            return self._envelope(query, request, through, {
                'status': 'ACCEPTED', 'retry_granted': False, 'receipt': receipt,
            })
        source = READ_SOURCES[query]
        watermark = self._watermark(source)
        if 'minimum_watermark' in request and not self._covers(watermark, request['minimum_watermark']):
            raise ReadRefused('READ_WATERMARK_UNMET', 422)
        try:
            body = self._point_or_page(query, request, watermark)
        except Exception as exc:
            if getattr(exc, 'code', None) in ('UNKNOWN_LISTING', 'UNKNOWN_RIGHT', 'UNKNOWN_SETTLEMENT'):
                raise _not_found() from exc
            raise
        return self._envelope(query, request, watermark, body)

    def _envelope(self, query, request, watermark, body):
        return {
            'read_schema_version': '0.1',
            'fixture_mode': 'REFERENCE_IN_MEMORY',
            'query_digest': receipt_digest({'query': query, 'input': request}),
            'accepted_through': watermark,
            'body': body,
        }

    def _point_or_page(self, query, request, watermark):
        resale = self._machines['resale']
        actor = request['actor']
        if query == 'list_open_listings':
            return self._page(request, watermark)
        if query == 'get_listing':
            listing = resale.view(request['listing_id'])
            if actor == listing['seller_role'] or (
                listing['ownership_transferred'] and actor == listing['holder_role']
            ):
                return listing
            raise _not_found()
        if query == 'get_settlement':
            listing = resale.view(request['listing_id'])
            settlement_id = listing['settlement_id']
            if settlement_id is None:
                raise _not_found()
            settlement = self._machines['settlement'].view(settlement_id)
            # bind_settlement records a pointer. The companion fixture uses
            # the listing ID as the trade subject on the settlement itself.
            if settlement['trade_id'] != listing['listing_id']:
                raise _not_found()
            show = self._machines['reservation'].view_show(listing['show_id'])['show']
            organizer = show['organizer_role']
            if actor in (organizer, settlement['debtor_role']):
                return settlement
            raise _not_found()
        right_id = request['right_id']
        current = resale.view_right(right_id)
        if actor != current['right']['holder_role']:
            raise _not_found()
        if query == 'get_right':
            return current
        return resale.view_presentation(right_id, version=request['version'], holder_role=request['holder_role'])

    def _page(self, request, watermark):
        limit = request.get('limit', PAGE_DEFAULT)
        context = ['list_open_listings', request['actor'], limit, ORDERING, watermark]
        offset = 0
        if 'cursor' in request:
            cursor = request['cursor']
            if not CURSOR.fullmatch(cursor):
                raise ReadRefused('READ_CURSOR_REFUSED', 422)
            raw = base64.urlsafe_b64decode(cursor + '==')
            offset = int.from_bytes(raw[:8], 'big')
            if not offset or not hmac.compare_digest(cursor, self._cursor(context, offset)):
                raise ReadRefused('READ_CURSOR_REFUSED', 422)
        resale = self._machines['resale']
        eligible = sorted(self._open_listing_keys(resale))
        if offset and offset >= len(eligible):
            raise ReadRefused('READ_CURSOR_REFUSED', 422)
        end = offset + limit
        truncated = end < len(eligible)
        views = (resale.view(listing_id) for _, listing_id in eligible[offset:end])
        return {
            'entries': [{key: view[key] for key in SUMMARY_FIELDS} for view in views],
            'next_cursor': self._cursor(context, end) if truncated else None,
            'truncated': truncated,
        }

    @staticmethod
    def _open_listing_keys(resale):
        for position, entry in enumerate(resale._journal, 1):
            if entry['op'] != 'list_resale':
                continue
            listing_id = entry['subject_id']
            listing = resale._listings[listing_id]
            if listing['phase'] == 'LISTED' and resale._now < listing['expires_ms']:
                if resale._public_right(listing['right_id'])['listing_id'] == listing_id:
                    yield position, listing_id

    def _cursor(self, context, offset):
        raw = offset.to_bytes(8, 'big') + self._sign('cursor', [context, offset])
        return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')

    def _recover(self, request, through):
        subject = request['subject']
        command = self._commands.get(subject['action'])
        if (command is None or command['machine'] not in RECOVERY_SOURCES
                or command['subject_field'] != subject['field']):
            return None
        source = command['machine']
        current = self._watermark(source)
        if not self._covers(current, through):
            return None
        selector = 'operation_id' if 'operation_id' in request else 'trace_id'
        identity = self._identities.get((selector, request[selector]))
        if identity is None or identity.ambiguous:
            return None
        record = self._receipts.get(identity.receipt_key)
        if record is None:
            return None
        actor, accepted_subject, position, encoded = record
        if (actor != request['actor'] or accepted_subject != subject
                or identity.receipt_key[0] != source
                or through['journal_entries'] < position['journal_entries']
                or through.get('logical_time_ms', 0) < position.get('logical_time_ms', 0)):
            return None
        return json.loads(encoded)
