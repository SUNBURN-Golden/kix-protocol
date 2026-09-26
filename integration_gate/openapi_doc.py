"""Build and check the integration-gate OpenAPI description.

The contract-only catalogue stays a pin. This document describes the loopback
transport only. It does not add commands, a public host, or a production endpoint.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

from integration_gate.catalogue import ROOT, git_blob_id, load_catalogue
from integration_gate.constants import (
    COMMAND_COUNT,
    CONTRACT_ONLY_OPENAPI,
    DEFAULT_TIMEOUT_SECONDS,
    GENERIC_OPERATION_ID,
    HEADER_LIMIT_BYTES,
    INTEGRATION_GATE_OPENAPI,
    LIVE_HTTP_SERVER_MODE,
    LOCAL_CALL_PATH,
    LOOPBACK_HOST,
    MAX_BODY_BYTES,
)

DESCRIPTION = (
    'Non-production loopback integration gate for the published KIX v0.3-rc1 '
    'local call. There is no production endpoint and no public host. '
    'Successful local HTTP tests are not production approval.\n\n'
    'The only protocol path is POST /x-kix-contract-only/local-call. '
    'The JSON body is the published local-call envelope: operationId, actor, '
    'action, and body. action is one of the published command keys. body is '
    'validated against that command JSON Schema, then passed to '
    'Core.execute(operationId, actor, action, body). No new protocol command '
    'is defined. No REST resource tree is defined for events, tickets, '
    'payments, venues, or marketplaces.\n\n'
    'State is the in-memory reference model. It is not durable across process '
    'restart. Inside one process, the same operationId with the same actor, '
    'action, and body replays the stored receipt. A different fingerprint for '
    'that operationId is OPERATION_ID_CONFLICT. An HTTP Idempotency-Key header '
    'is not consulted.\n\n'
    'External payment, KYC, venue, and bank adapters are not attached. Fixture '
    'reject codes from the reference model stay reject codes. GET /health and '
    'GET /ready are process probes, not protocol commands. Readiness is not '
    'production readiness.\n\n'
    'The contract-only catalogue remains a pin that does not declare a live '
    'server. This document only describes the local integration-gate transport.'
)

LIVE_HTTP_SERVER = {
    'mode': LIVE_HTTP_SERVER_MODE,
    'production': False,
    'publicHost': False,
    'loopbackOnly': True,
    'defaultBindHost': LOOPBACK_HOST,
}


def render(document):
    return json.dumps(document, ensure_ascii=False, indent=2) + '\n'


def build_document(root=None):
    root = Path(root) if root is not None else ROOT
    catalogue = load_catalogue(root)
    names = catalogue.names
    operations = [
        {
            'operationId': name,
            'action': name,
            'x-kix-transport': 'integration-gate',
            'x-kix-production-endpoint': False,
            'x-kix-not-a-public-service': True,
            'requestBodySchema': (
                'kix-protocol.contract-only.openapi.json#/components/schemas/' + name
            ),
            'localCallParameters': ['operationId', 'actor', 'action', 'body'],
            'description': (
                'Published command, dispatched by the loopback gate through '
                'Core.execute. operationId here is the command name (Python '
                'action), not the per-invocation operationId argument. Not a '
                'production operation.'
            ),
        }
        for name in names
    ]
    return {
        'openapi': '3.1.0',
        'info': {
            'title': 'KIX integration-gate local-call transport',
            'version': '0.3-rc1-integration-gate+sha256:' + catalogue.sha256,
            'summary': (
                'Non-production loopback integration gate. '
                'No production endpoint. No public host.'
            ),
            'description': DESCRIPTION,
        },
        'x-kix-contract-status': 'integration-gate',
        'x-kix-live-http-server': copy.deepcopy(LIVE_HTTP_SERVER),
        'x-kix-production-endpoint': False,
        'x-kix-public-host': False,
        'x-kix-omitted-commands': [],
        'x-kix-source': {
            'protocolContract': 'reference/v0.3-rc1/protocol_contract.json',
            'gitBlob': catalogue.git_blob,
            'sha256': catalogue.sha256,
            'domain': catalogue.domain,
            'commandCount': len(names),
            'contractCatalogue': CONTRACT_ONLY_OPENAPI,
            'localCall': 'reference/v0.3-rc1/core.py Core.execute',
            'unknownFields': catalogue.contract['unknownFields'],
            'sourceAuthentication': catalogue.contract['sourceAuthentication'],
        },
        'x-kix-limits': {
            'maxBodyBytes': MAX_BODY_BYTES,
            'requestTimeoutSeconds': DEFAULT_TIMEOUT_SECONDS,
            'headerLimitBytes': HEADER_LIMIT_BYTES,
            'bindHost': LOOPBACK_HOST,
            'durableAcrossRestart': False,
        },
        'x-kix-idempotency': {
            'identity': 'envelope.operationId',
            'sameFingerprint': (
                'Inside one process, Core.execute returns the stored receipt.'
            ),
            'conflict': 'OPERATION_ID_CONFLICT',
            'durableAcrossRestart': False,
            'httpIdempotencyKeyHeader': False,
        },
        'x-kix-external-adapters': {
            'pg': 'forbidden',
            'kyc': 'forbidden',
            'venue': 'forbidden',
            'bank': 'forbidden',
            'note': (
                'The gate calls the in-memory reference Core only. '
                'It adds no live adapter.'
            ),
        },
        'x-kix-transport-probes': {
            'note': (
                'Process probes. Not protocol commands and not OpenAPI path '
                'items. Not a REST resource tree.'
            ),
            'health': {
                'method': 'GET',
                'path': '/health',
                'meaning': 'Process liveness only. Does not check the reference core.',
            },
            'ready': {
                'method': 'GET',
                'path': '/ready',
                'meaning': (
                    'In-memory reference core and the published command catalogue '
                    'are loaded. Not production readiness.'
                ),
            },
        },
        'x-kix-local-call-operations': operations,
        'paths': {
            LOCAL_CALL_PATH: {
                'post': {
                    'operationId': GENERIC_OPERATION_ID,
                    'x-kix-transport': 'integration-gate',
                    'x-kix-production-endpoint': False,
                    'x-kix-not-a-public-service': True,
                    'summary': (
                        'Loopback local-call envelope. Not a production endpoint.'
                    ),
                    'description': (
                        'POST the published envelope to the in-memory reference '
                        'Core.execute. Command identities are '
                        'x-kix-local-call-operations. This path is the published '
                        'local-call envelope, not a new resource tree. Bind is '
                        'IPv4 loopback only.'
                    ),
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': (
                                        'kix-protocol.contract-only.openapi.json'
                                        '#/components/schemas/LocalCallEnvelope'
                                    ),
                                },
                            },
                        },
                    },
                    'responses': {
                        '200': {
                            'description': (
                                'In-process receipt from Core.execute, including '
                                'a replay of the same operationId fingerprint. '
                                'Not evidence of live money movement.'
                            ),
                            'x-kix-production-endpoint': False,
                        },
                        '400': {
                            'description': (
                                'Malformed envelope, unknown action, or published '
                                'schema rejection. rejected is true. Not HTTP 200.'
                            ),
                        },
                        '404': {
                            'description': 'Unsupported path. Fail closed.',
                        },
                        '405': {
                            'description': 'Unsupported method. Fail closed.',
                        },
                        '408': {
                            'description': 'Request timed out before a Core result.',
                        },
                        '411': {
                            'description': 'POST requires a single Content-Length.',
                        },
                        '413': {
                            'description': 'Body larger than the gate limit.',
                        },
                        '415': {
                            'description': 'Media type is not application/json.',
                        },
                        '422': {
                            'description': (
                                'Core.execute raised Rejected. error is that '
                                'reject code. Not HTTP 200.'
                            ),
                        },
                        '503': {
                            'description': (
                                'Process is up but the in-memory core is not '
                                'accepting calls. Not production readiness.'
                            ),
                        },
                    },
                },
            },
        },
    }


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate(root=None, document=None):
    root = Path(root) if root is not None else ROOT
    errors = []

    def need(condition, message):
        if not condition:
            errors.append(message)

    try:
        catalogue = load_catalogue(root)
    except Exception as exc:
        return ['catalogue refused: ' + type(exc).__name__]
    if document is None:
        path = root / INTEGRATION_GATE_OPENAPI
        if not path.is_file():
            return ['missing integration-gate OpenAPI']
        try:
            document = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return ['integration-gate OpenAPI is not JSON']
        if document != build_document(root):
            errors.append('committed integration-gate OpenAPI != canonical derivation')
    names = catalogue.names
    need(len(names) == COMMAND_COUNT, 'command count must stay 40')
    need(document.get('openapi') == '3.1.0', 'openapi version must be 3.1.0')
    info = document.get('info') or {}
    description = info.get('description') or ''
    need('no production endpoint' in description, 'description must deny a production endpoint')
    need('no public host' in description, 'description must deny a public host')
    need('not production approval' in description, 'description must deny production approval')
    need(document.get('x-kix-contract-status') == 'integration-gate', 'status drift')
    need(document.get('x-kix-live-http-server') == LIVE_HTTP_SERVER, 'liveHttpServer marker drift')
    need(document.get('x-kix-production-endpoint') is False, 'production endpoint must be false')
    need(document.get('x-kix-public-host') is False, 'public host must be false')
    need(document.get('x-kix-omitted-commands') == [], 'omitted command list must stay empty')
    source = document.get('x-kix-source') or {}
    need(source.get('sha256') == catalogue.sha256, 'source sha256 drift')
    need(source.get('gitBlob') == git_blob_id(catalogue.source_bytes), 'source git blob drift')
    need(source.get('commandCount') == COMMAND_COUNT, 'source commandCount drift')
    need(source.get('domain') == catalogue.domain, 'domain drift')
    need(source.get('unknownFields') == 'REJECT', 'unknownFields drift')
    need(source.get('sourceAuthentication') == 'FIXTURE_ONLY', 'sourceAuthentication drift')
    limits = document.get('x-kix-limits') or {}
    need(limits.get('maxBodyBytes') == MAX_BODY_BYTES, 'body limit drift')
    need(limits.get('bindHost') == LOOPBACK_HOST, 'bind host drift')
    need(limits.get('durableAcrossRestart') is False, 'restart durability must stay false')
    idempotency = document.get('x-kix-idempotency') or {}
    need(idempotency.get('httpIdempotencyKeyHeader') is False, 'HTTP Idempotency-Key must stay unused')
    need(idempotency.get('durableAcrossRestart') is False, 'idempotency durability must stay false')
    adapters = document.get('x-kix-external-adapters') or {}
    for name in ('pg', 'kyc', 'venue', 'bank'):
        need(adapters.get(name) == 'forbidden', 'adapter must stay forbidden: ' + name)
    operations = document.get('x-kix-local-call-operations') or []
    operation_ids = [item.get('operationId') for item in operations]
    need(operation_ids == names, 'local-call operationIds drifted from command keys')
    need(GENERIC_OPERATION_ID not in names, 'generic operationId collides with a command')
    for item in operations:
        need(item.get('x-kix-production-endpoint') is False, 'command claims a production endpoint')
        need(item.get('x-kix-transport') == 'integration-gate', 'command transport drift')
    paths = document.get('paths') or {}
    need(list(paths) == [LOCAL_CALL_PATH], 'protocol path set drift')
    need('/health' not in paths and '/ready' not in paths, 'probes must not be protocol paths')
    post = (paths.get(LOCAL_CALL_PATH) or {}).get('post') or {}
    need(post.get('operationId') == GENERIC_OPERATION_ID, 'generic operationId drift')
    need(post.get('x-kix-production-endpoint') is False, 'path claims a production endpoint')
    responses = post.get('responses') or {}
    for status in ('200', '400', '404', '405', '408', '413', '422', '503'):
        need(status in responses, 'missing response ' + status)
    need('Not HTTP 200' in (responses.get('422') or {}).get('description', ''),
         '422 must say it is not HTTP 200')
    for key, value in _walk(document):
        if key in ('servers', 'security', 'securitySchemes', 'url'):
            errors.append('forbidden transport or auth field: ' + key)
        if isinstance(value, str) and (
            'http://' in value or 'https://' in value or 'localhost' in value.lower()
        ):
            errors.append('forbidden endpoint string near key ' + key)
        if key == 'x-kix-production-endpoint' and value is not False:
            errors.append('production endpoint flag is not false')
        if key == 'production' and value is not False:
            errors.append('production flag is not false')
    contract_only_path = root / CONTRACT_ONLY_OPENAPI
    try:
        contract_only = json.loads(contract_only_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        errors.append('contract-only catalogue is unreadable')
        return errors
    pinned = [item.get('operationId') for item in contract_only.get('x-kix-local-call-operations') or []]
    need(pinned == names, 'integration gate commands drifted from the contract-only catalogue')
    need(contract_only.get('x-kix-live-http-server') is False,
         'contract-only catalogue must keep liveHttpServer false')
    need(contract_only.get('x-kix-production-endpoint') is False,
         'contract-only catalogue must keep production endpoint false')
    need(list((contract_only.get('paths') or {})) == [LOCAL_CALL_PATH],
         'contract-only path set drift')
    return errors


def self_test(root=None):
    root = Path(root) if root is not None else ROOT
    document = build_document(root)
    if validate(root, document):
        print('self-test: canonical document failed validation', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['x-kix-production-endpoint'] = True
    if not validate(root, broken):
        print('self-test: production endpoint true was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['x-kix-live-http-server']['production'] = True
    if not validate(root, broken):
        print('self-test: liveHttpServer production true was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['servers'] = [{'url': 'https://example.invalid'}]
    if not validate(root, broken):
        print('self-test: servers entry was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['paths']['/events'] = {'get': {'operationId': 'listEvents'}}
    if not validate(root, broken):
        print('self-test: extra path was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['x-kix-local-call-operations'] = list(broken['x-kix-local-call-operations']) + [
        {'operationId': 'kyc_verify', 'x-kix-production-endpoint': False,
         'x-kix-transport': 'integration-gate'}
    ]
    if not validate(root, broken):
        print('self-test: extra command was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['info']['description'] += ' See http://example.invalid/gate.'
    if not validate(root, broken):
        print('self-test: endpoint URL was accepted', file=sys.stderr)
        return 1
    print('self-test: pass')
    return 0


def main(argv):
    root = ROOT
    if '--self-test' in argv:
        return self_test(root)
    document = build_document(root)
    path = root / INTEGRATION_GATE_OPENAPI
    if '--write' in argv:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(document), encoding='utf-8')
        print('wrote ' + str(path.relative_to(root)))
    errors = validate(root)
    if errors:
        print('integration-gate openapi check failed:', file=sys.stderr)
        for item in errors:
            print('- ' + item, file=sys.stderr)
        return 1
    print(
        'integration-gate openapi ok: commands=%d productionEndpoint=false publicHost=false'
        % len(document['x-kix-local-call-operations'])
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
