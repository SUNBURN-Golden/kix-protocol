"""Integration-only resale read schemas and request validation."""
from __future__ import annotations

from integration_gate.resale_reads import PAGE_DEFAULT, PAGE_MAX, READ_PATHS
from integration_gate.schema import EnvelopeError, problems


def obj(fields, optional=()):
    return {
        'type': 'object', 'additionalProperties': False, 'properties': fields,
        'required': [name for name in fields if name not in optional],
    }


def ref(name):
    return {'$ref': '#/components/schemas/' + name}


def fields(names, schema):
    return dict.fromkeys(names.split(), schema)


IDENT = {'type': 'string', 'minLength': 1, 'maxLength': 100}
TEXT = {'type': 'string'}
STRING_OR_NULL = {'type': ['string', 'null']}
NUMBER = {'type': 'integer', 'minimum': 0}
NUMBER_OR_NULL = {'type': ['integer', 'null'], 'minimum': 0}
BOOL = {'type': 'boolean'}
FALSE = {'const': False}
TOKEN = {'type': 'string', 'minLength': 64, 'maxLength': 64}
WATERMARK = obj({
    'source': IDENT, 'generation': {'type': 'string', 'minLength': 32, 'maxLength': 32},
    'journal_entries': NUMBER, 'logical_time_ms': NUMBER, 'token': TOKEN,
}, optional=('logical_time_ms',))
ISSUED_WATERMARK = {
    **WATERMARK,
    'properties': {
        **WATERMARK['properties'],
        'source': {'enum': ['resale', 'settlement']},
        'generation': {'type': 'string', 'pattern': '^[0-9a-f]{32}$'},
        'token': {**TOKEN, 'pattern': '^[0-9a-f]{64}$'},
    },
    'if': {'properties': {'source': {'const': 'resale'}}},
    'then': {'required': ['logical_time_ms']},
    'else': {'not': {'required': ['logical_time_ms']}},
}
SUBJECT = obj(fields('action field id', IDENT))
CURSOR = {'type': 'string', 'minLength': 54, 'maxLength': 54}
LIMIT = {'type': 'integer', 'minimum': 1, 'maximum': PAGE_MAX}
RECOVERY = 'get_operation_recovery'


def point_request(required, optional=None):
    extra = {'minimum_watermark': WATERMARK, **(optional or {})}
    return obj({'actor': IDENT, **required, **extra}, optional=extra)


REQUESTS = {
    'list_open_listings': point_request({}, {'limit': LIMIT, 'cursor': CURSOR}),
    'get_listing': point_request({'listing_id': IDENT}),
    'get_right': point_request({'right_id': IDENT}),
    'get_presentation': point_request({'right_id': IDENT, 'version': NUMBER, 'holder_role': IDENT}),
    'get_settlement': point_request({'listing_id': IDENT}),
    RECOVERY: obj({
        'actor': IDENT, 'subject': SUBJECT, 'through': WATERMARK, 'request_cut': BOOL,
        'operation_id': IDENT, 'trace_id': {**IDENT, 'maxLength': 64},
    }, optional=('through', 'request_cut', 'operation_id', 'trace_id')),
}


def parse_read(query, payload):
    if problems(payload, REQUESTS[query]):
        raise EnvelopeError('READ_REQUEST_INVALID')
    if query == RECOVERY:
        if (('operation_id' in payload) == ('trace_id' in payload)
                or ('through' in payload) == ('request_cut' in payload)
                or payload.get('request_cut') is False):
            raise EnvelopeError('READ_REQUEST_INVALID')
    identifiers = [payload[key] for key in (
        'actor', 'listing_id', 'right_id', 'holder_role', 'operation_id', 'trace_id',
    ) if key in payload]
    if query == RECOVERY:
        identifiers.extend(payload['subject'].values())
    if any(value.strip() != value for value in identifiers):
        raise EnvelopeError('INVALID_ID')
    try:
        for value in identifiers:
            value.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise EnvelopeError('INVALID_ID') from exc
    return payload


FLAGS = fields(
    'role_authenticated organizer_authenticated chain_grant_current durable quote_policy_approved '
    'discount_applied provider_fact_live funds_executed buyer_evidence_available chain_owner_current '
    'cross_channel_exclusive admission_routing_production private_proof_verified compensation_defined '
    'economic_finality_claimed venue_credential_reissued', FALSE,
)
REFERENCE = {
    'provenance': {'const': 'MOCK_GATE_ONLY'}, 'lifecycle_authority': {'const': 'IN_MEMORY_FSM'},
    'external_marketplace': {'const': 'UNSUPPORTED'}, **FLAGS,
}
LISTING_SUMMARY = {
    **fields('listing_id show_id phase currency', TEXT),
    **fields('amount expires_ms', NUMBER), 'expired': BOOL,
}
LISTING = {
    **LISTING_SUMMARY, **REFERENCE, **fields('right_id seller_role recipient_role holder_role slot_state', TEXT),
    **fields('buyer_role hold_id payment_ref settlement_id transfer_id slot_right_id', STRING_OR_NULL),
    **fields('version current_version generation accepted_entries', NUMBER),
    'version_after': NUMBER_OR_NULL, 'external_payment': {'const': 'UNSUPPORTED'},
    'settlement_gate': {'enum': ['UNBOUND', 'BOUND', 'MOCK_COMMIT_OBSERVED']},
    **fields('terminal attached mock_settlement_commit_observed ownership_transferred prior_presentation_valid', BOOL),
}
RIGHT = {
    **fields('right_id show_id holder_role state', TEXT), **fields('slot version generation', NUMBER),
    **fields('listing_id admission_id last_payment last_payer', STRING_OR_NULL), 'last_amount': NUMBER_OR_NULL,
}
TICKET = {
    **REFERENCE, **fields('right_id show_id holder_role', TEXT), **fields('slot version', NUMBER),
    **fields('sale_phase reservation_id active_listing_id', STRING_OR_NULL), 'eligible': BOOL,
}
PRESENTATION = {
    **fields('right_id holder_role current_holder_role', TEXT), **fields('version current_version', NUMBER),
    'matches_current_right': BOOL, **fields('venue_credential_reissued admission_routing_production', FALSE),
}
RIGHT_ENVELOPE = {
    **REFERENCE, 'duplicate': FALSE, 'applied': TEXT, 'logical_time_ms': NUMBER,
    'external_payment': {'const': 'UNSUPPORTED'}, 'right': ref('FixtureRight'),
}
PAYMENT_FLAGS = fields('legal_debtor_bound admission_granted right_cancelled bank_debit_observed '
                       'external_return_closed funds_executed', FALSE)
POLICY = obj({**fields('kind residual_payee fee_payee', TEXT), 'fee_bps': NUMBER})
OBLIGATION = obj({'payee': TEXT, **fields('face distributed cancelled_unpaid recovery_due outstanding', NUMBER)})
CLAIM = {
    **PAYMENT_FLAGS, 'provenance': {'const': 'MOCK_SETTLEMENT_ONLY'},
    **fields('claim_id trade_id currency debtor_role refund_bearer_policy', TEXT), 'policy': POLICY,
    'obligations': {'type': 'array', 'items': OBLIGATION},
    **fields('gross receivable_open confirmed_cash non_cash_accounted distributed_cash undistributed_cash '
             'refund_face refund_accepted refund_outstanding pg_adjustment_outstanding recovery_due', NUMBER),
    'distribution_order': {'type': ['array', 'null'], 'items': TEXT},
    'refund_beneficiary': STRING_OR_NULL, **fields('fixture_reclassified distribution_blocked', BOOL),
}
SETTLEMENT = {
    **PAYMENT_FLAGS, 'provenance': {'const': 'MOCK_SETTLEMENT_ONLY'},
    'lifecycle_authority': {'const': 'IN_MEMORY_FSM'}, 'external_payment': {'const': 'UNSUPPORTED'},
    **fields('settlement_id phase trade_id currency debtor_role', TEXT), 'policy': POLICY,
    **fields('gross accepted_entries', NUMBER), **fields('terminal mock_authorized', BOOL),
    **fields('commit_movement_id failure_reason cancel_reason', STRING_OR_NULL),
    **fields('provider_authorization_executed durable', FALSE),
    'claim': {'oneOf': [ref('FixtureClaim'), {'type': 'null'}]},
}


def envelope(body):
    return obj({
        'read_schema_version': {'const': '0.1'}, 'fixture_mode': {'const': 'REFERENCE_IN_MEMORY'},
        'query_digest': {**TOKEN, 'pattern': '^[0-9a-f]{64}$'},
        'accepted_through': ref('FixtureReadWatermark'), 'body': body,
    })


RESPONSES = {
    'list_open_listings': envelope(obj({
        'entries': {'type': 'array', 'items': ref('FixtureListingSummary'), 'maxItems': PAGE_MAX},
        'next_cursor': {**CURSOR, 'type': ['string', 'null']}, 'truncated': BOOL,
    })),
    'get_listing': envelope(ref('FixtureListing')),
    'get_right': envelope(obj({**RIGHT_ENVELOPE, 'applied': {'const': 'view_right'}, 'ticket': ref('FixtureTicket')})),
    'get_presentation': envelope(obj({
        **RIGHT_ENVELOPE, 'applied': {'const': 'view_presentation'}, 'presentation': obj(PRESENTATION),
    })),
    'get_settlement': envelope(obj(SETTLEMENT)),
    RECOVERY: {'oneOf': [
        envelope(obj({'status': {'const': 'ACCEPTED'}, 'retry_granted': FALSE, 'receipt': {
            'type': 'object', 'description': 'Immutable first FSM receipt for the requested action and subject.',
        }})),
        envelope(obj({'status': {'const': 'CUT_AVAILABLE'}, 'retry_granted': FALSE})),
        obj({'status': {'const': 'UNKNOWN'}, 'retry_granted': FALSE}),
    ]},
}

DESCRIPTIONS = {
    'list_open_listings': 'Attached, unexpired LISTED fixture summaries. Sort by first accepted listing position, then listing ID. Cursors bind actor, page size, ordering and snapshot.',
    'get_listing': 'Listing visible to its seller and, after transfer, the current holder.',
    'get_right': 'Separate ticket and right views visible to the current holder.',
    'get_presentation': 'Current holder only. A valid historical comparison may return matches_current_right false.',
    'get_settlement': 'Follow the listing binding when its listing ID matches the settlement trade ID. Visible to the show organizer and settlement debtor fixture.',
    RECOVERY: (
        'Resolve positive retained acceptance for resale or settlement. Supply exactly one identity and '
        'either through for receipt lookup or request_cut: true for a signed source watermark without a receipt. '
        'Cut issuance checks the same actor, identity and subject and works before a listing has a settlement '
        'binding. Evidence mismatches return UNKNOWN. In-memory write deadlines fence writes while the same '
        'worker can still serve reads. No retry is granted.'
    ),
}


def _json_response(description, schema):
    return {'description': description, 'content': {'application/json': {'schema': schema}}}


def read_paths():
    errors = {
        '400': 'Malformed request or invalid fixture fields.', '404': 'Unknown route or unavailable subject.',
        '405': 'Only POST is allowed.', '408': 'Request timed out.', '411': 'Content-Length is required.',
        '413': 'Request body exceeds the gate limit.', '414': 'Request URI is too long.',
        '415': 'Expected application/json.', '417': 'Expect is unsupported.',
        '422': 'Unmet watermark, refused cursor, FSM rejection, or readiness-directory mode.',
        '431': 'Request headers exceed the gate limit.', '500': 'Internal gate error.',
        '503': 'Worker unavailable or admission limit reached.', '505': 'Unsupported HTTP version.',
    }
    paths = {}
    for path, query in READ_PATHS.items():
        schema = REQUESTS[query]
        if query == RECOVERY:
            schema = {
                **schema,
                'properties': {**schema['properties'], 'request_cut': {**BOOL, 'const': True}},
                'allOf': [
                    {'oneOf': [{'required': ['operation_id']}, {'required': ['trace_id']}]},
                    {'oneOf': [{'required': ['through']}, {'required': ['request_cut']}]},
                ],
            }
        elif query == 'list_open_listings':
            props = {**schema['properties'], 'limit': {**LIMIT, 'default': PAGE_DEFAULT}}
            schema = {**schema, 'properties': props}
        paths[path] = {'post': {
            'operationId': query,
            'x-kix-transport': 'integration-gate', 'x-kix-production-endpoint': False,
            'description': DESCRIPTIONS[query] + ' Actor labels are FIXTURE_ONLY. No browser CORS.',
            'requestBody': {'required': True, 'content': {'application/json': {'schema': schema}}},
            'responses': {'200': _json_response('Fixture observation.', RESPONSES[query]), **{
                status: _json_response(description, ref(
                    'FixtureReadAvailabilityError' if status == '503' else 'FixtureReadError',
                ))
                for status, description in errors.items()
            }},
        }}
    return paths


def read_components():
    error = obj({'error': TEXT, 'rejected': {'const': True}, 'detail': TEXT}, optional=('detail',))
    return {'schemas': {
        'FixtureReadWatermark': ISSUED_WATERMARK,
        'FixtureReadError': error,
        'FixtureReadAvailabilityError': {**error, 'additionalProperties': True},
        'FixtureListingSummary': obj(LISTING_SUMMARY),
        'FixtureListing': obj(LISTING),
        'FixtureRight': obj(RIGHT),
        'FixtureTicket': obj(TICKET),
        'FixtureClaim': obj(CLAIM),
    }}
