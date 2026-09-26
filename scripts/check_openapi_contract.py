#!/usr/bin/env python3
"""Fail if the contract-only OpenAPI catalogue drifts from protocol_contract.json.

The catalogue is a local-call analogue. It does not describe a live HTTP server.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / 'reference/v0.3-rc1/protocol_contract.json'
OPENAPI_PATH = ROOT / 'docs/contracts/openapi/kix-protocol.contract-only.openapi.json'
SPEC_ENVELOPE = 'reference/v0.1/KIX_프로토콜_통합명세_v0.1.md §9.1'
LOCAL_CALL = 'reference/v0.3-rc1/core.py Core.execute'
PLACEHOLDER_PATH = '/x-kix-contract-only/local-call'
GENERIC_OPERATION_ID = 'invokeLocalCall'


def git_blob_id(data):
    header = b'blob ' + str(len(data)).encode('ascii') + b'\0'
    return hashlib.sha1(header + data).hexdigest()


def render(document):
    return json.dumps(document, ensure_ascii=False, indent=2) + '\n'


def build_document(contract, source_bytes):
    """Canonical OpenAPI 3.1 catalogue. Command schemas are copied, not rewritten."""
    commands = contract['commands']
    names = list(commands)
    sha256 = hashlib.sha256(source_bytes).hexdigest()
    blob = git_blob_id(source_bytes)
    schemas = {name: copy.deepcopy(schema) for name, schema in commands.items()}
    schemas['LocalCallEnvelope'] = {
        'type': 'object',
        'additionalProperties': False,
        'description': (
            'Fixed parameter list of the Python local call '
            'Core.execute(operation_id, actor, action, body). '
            'additionalProperties false records that fixed list. '
            'It is not an HTTP media type and not a field of protocol_contract.json. '
            'protocolDomain and actorContext are named by the v0.1 specification '
            'and are recorded under x-kix-specification-envelope. They are not '
            'extra arguments of the current Python call. No authentication scheme, '
            'retry policy, or transport guarantee is defined.'
        ),
        'required': ['operationId', 'actor', 'action', 'body'],
        'properties': {
            'operationId': {
                'type': 'string',
                'description': (
                    'Per-invocation identity. First argument of Core.execute. '
                    'This is not the command name. The command name is action. '
                    'No HTTP Idempotency-Key or retry policy is defined.'
                ),
                'x-kix-reference-model-observed': {
                    'check': 'ident',
                    'error': 'INVALID_ID',
                    'rule': (
                        'non-empty string, length at most 100, '
                        'no leading or trailing whitespace'
                    ),
                    'sameInvocation': (
                        'In the reference model, the same operationId with the same '
                        'actor, action, and body returns the stored receipt. A different '
                        'fingerprint for the same operationId is OPERATION_ID_CONFLICT. '
                        'That is an in-process SQLite rule, not an HTTP retry contract.'
                    ),
                    'notInExportedCommandSchema': True,
                },
            },
            'actor': {
                'type': 'string',
                'description': (
                    'Second argument of Core.execute. The v0.1 specification names '
                    'the corresponding envelope field actorContext and says it must be '
                    'an authentication and signature-verification result. This Python '
                    'call does not take actorContext. The fixture actor string is not '
                    'that result and is not authority. This document defines no '
                    'authentication scheme.'
                ),
                'x-kix-specification-field': 'actorContext',
                'x-kix-reference-model-observed': {
                    'check': 'ident',
                    'error': 'INVALID_ID',
                    'rule': (
                        'non-empty string, length at most 100, '
                        'no leading or trailing whitespace'
                    ),
                    'notInExportedCommandSchema': True,
                },
            },
            'action': {
                'type': 'string',
                'enum': names,
                'description': (
                    'Command name. Third argument of Core.execute. '
                    'Selects the body schema. Equal to a key of '
                    'protocol_contract.json commands.'
                ),
            },
            'body': {
                'description': (
                    'Fourth argument of Core.execute. Validate it against '
                    'components.schemas[action]. Several actions share an identical '
                    'body schema, so the action name is the discriminator. '
                    'unknownFields REJECT is the exported catalogue rule.'
                ),
            },
        },
        'allOf': [
            {
                'if': {
                    'properties': {'action': {'const': name}},
                    'required': ['action'],
                },
                'then': {
                    'properties': {
                        'body': {'$ref': '#/components/schemas/' + name},
                    },
                },
            }
            for name in names
        ],
        'x-kix-body-domain-check': {
            'specificationField': 'protocolDomain',
            'localCall': 'body.domain is compared with the pinned domain',
            'error': 'DOMAIN_MISMATCH',
            'pinnedDomain': contract['domain'],
            'notASeparatePythonArgument': True,
            'constNotAddedToCommandSchema': True,
        },
    }
    operations = [
        {
            'operationId': name,
            'action': name,
            'x-kix-transport': 'contract-only-placeholder',
            'x-kix-not-a-published-http-service': True,
            'requestBodySchema': '#/components/schemas/' + name,
            'localCallParameters': ['operationId', 'actor', 'action', 'body'],
            'description': (
                'Local-call analogue of this command. Not bound to an HTTP path. '
                'operationId here is the command name (Python action), not the '
                'per-invocation operationId argument.'
            ),
        }
        for name in names
    ]
    return {
        'openapi': '3.1.0',
        'info': {
            'title': 'KIX protocol local-call catalogue (contract-only)',
            'version': '0.3-rc1+sha256:' + sha256,
            'summary': 'Contract-only. No live HTTP server. No production endpoint.',
            'description': (
                'CONTRACT-ONLY catalogue of the KIX v0.3-rc1 local call. '
                'There is no live HTTP server and no production endpoint. '
                'The version is pinned to the sha256 of '
                'reference/v0.3-rc1/protocol_contract.json.\n\n'
                'This document does not publish a REST resource tree, an '
                'authentication scheme, a retry policy, or a transport guarantee. '
                'The single path exists only so this file is an OpenAPI document. '
                'It is marked x-kix-transport: contract-only-placeholder and is '
                'not protocol law. POST is an OpenAPI grammar slot, not a '
                'published HTTP method of the protocol.\n\n'
                'The authoritative local call is Core.execute(operationId, actor, '
                'action, body). Each command key is one action. The body schema '
                'is that command JSON Schema, copied under components.schemas. '
                'x-kix-local-call-operations[].operationId is the command name. '
                'unknownFields, sourceAuthentication, handlerConstraints, and '
                'additionalProperties false are preserved from the source. '
                'The exported catalogue is not a full business validator.\n\n'
                'Specification envelope fields are protocolDomain, operationId, '
                'actorContext, action, and body. The Python function takes '
                'operationId, actor, action, and body, and checks body.domain. '
                'A caller-supplied actor string must not be treated as authority.'
            ),
        },
        'x-kix-contract-status': 'contract-only',
        'x-kix-live-http-server': False,
        'x-kix-production-endpoint': False,
        'x-kix-omitted-commands': [],
        'x-kix-source': {
            'path': 'reference/v0.3-rc1/protocol_contract.json',
            'gitBlob': blob,
            'sha256': sha256,
            'domain': contract['domain'],
            'unknownFields': contract['unknownFields'],
            'sourceAuthentication': contract['sourceAuthentication'],
            'handlerConstraints': contract['handlerConstraints'],
            'commandCount': len(names),
        },
        'x-kix-specification-envelope': {
            'source': SPEC_ENVELOPE,
            'fields': ['protocolDomain', 'operationId', 'actorContext', 'action', 'body'],
            'pythonLocalCall': {
                'source': LOCAL_CALL,
                'parameters': ['operationId', 'actor', 'action', 'body'],
                'bodyDomainCheck': 'body.domain must equal x-kix-source.domain',
            },
            'actorContext': (
                'Named by the specification as an authentication and signature '
                'verification result. The current Python local call does not take '
                'this argument. No authentication scheme is defined here.'
            ),
            'protocolDomain': (
                'Named by the specification. The Python local call checks '
                'body.domain rather than a separate argument.'
            ),
            'sourceAuthenticationMeaning': (
                'FIXTURE_ONLY is the exported label. It is not an HTTP security '
                'scheme and not production authentication.'
            ),
        },
        'x-kix-action-body-map': {
            name: '#/components/schemas/' + name for name in names
        },
        'x-kix-local-call-operations': operations,
        'x-kix-reference-receipt-observed': {
            'sources': [SPEC_ENVELOPE, LOCAL_CALL],
            'keys': ['domain', 'operationId', 'sequence', 'action', 'result'],
            'note': (
                'The specification says a receipt carries domain, operationId, '
                'sequence, action, and result. The reference model stores that '
                'in-process receipt. result is handler-specific and is not in '
                'protocol_contract.json, so this catalogue does not schema it. '
                'The specification also says an external consumer stores its own '
                'cursor and receipt id. No message broker or consumer is defined. '
                'These keys are not an HTTP response contract.'
            ),
        },
        'paths': {
            PLACEHOLDER_PATH: {
                'post': {
                    'operationId': GENERIC_OPERATION_ID,
                    'x-kix-transport': 'contract-only-placeholder',
                    'x-kix-not-a-published-http-service': True,
                    'summary': 'Local-call analogue. Not a published HTTP operation.',
                    'description': (
                        'Placeholder path required to carry one OpenAPI operation. '
                        'It is not a published HTTP service and not protocol law. '
                        'Command identities are x-kix-local-call-operations, not '
                        'this operationId.'
                    ),
                    'requestBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/LocalCallEnvelope'},
                            },
                        },
                    },
                    'responses': {
                        'default': {
                            'description': (
                                'OpenAPI requires a responses object. '
                                'protocol_contract.json defines no response schema. '
                                'This entry is not a live HTTP response and the '
                                'status code is not a transport contract. Observed '
                                'in-process receipt keys are x-kix-reference-receipt-observed.'
                            ),
                            'x-kix-transport': 'contract-only-placeholder',
                            'x-kix-http-status': 'not-a-transport-contract',
                        },
                    },
                },
            },
        },
        'components': {'schemas': schemas},
    }


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def validate(contract, source_bytes, document):
    """Independent checks against the source contract. Returns error strings."""
    errors = []
    commands = contract['commands']
    names = list(commands)

    def need(condition, message):
        if not condition:
            errors.append(message)

    need(document.get('openapi') == '3.1.0', 'openapi version must be 3.1.0')
    info = document.get('info') or {}
    description = info.get('description') or ''
    need('no live HTTP server' in description, 'description must state no live HTTP server')
    need('no production endpoint' in description, 'description must state no production endpoint')
    need(info.get('summary') == 'Contract-only. No live HTTP server. No production endpoint.',
         'summary must state contract-only and no live server or production endpoint')
    sha256 = hashlib.sha256(source_bytes).hexdigest()
    blob = git_blob_id(source_bytes)
    need(info.get('version') == '0.3-rc1+sha256:' + sha256, 'info.version is not pinned to the source sha256')
    need(document.get('x-kix-contract-status') == 'contract-only', 'x-kix-contract-status must be contract-only')
    need(document.get('x-kix-live-http-server') is False, 'x-kix-live-http-server must be false')
    need(document.get('x-kix-production-endpoint') is False, 'x-kix-production-endpoint must be false')
    need(document.get('x-kix-omitted-commands') == [], 'omitted command list must stay empty')

    source = document.get('x-kix-source') or {}
    need(source.get('path') == 'reference/v0.3-rc1/protocol_contract.json', 'source path drift')
    need(source.get('gitBlob') == blob, 'source git blob drift')
    need(source.get('sha256') == sha256, 'source sha256 drift')
    need(source.get('domain') == contract['domain'], 'domain drift')
    need(source.get('unknownFields') == contract['unknownFields'], 'unknownFields drift')
    need(source.get('sourceAuthentication') == contract['sourceAuthentication'],
         'sourceAuthentication drift')
    need(source.get('handlerConstraints') == contract['handlerConstraints'],
         'handlerConstraints drift')
    need(source.get('commandCount') == len(names), 'commandCount drift')
    need(contract['unknownFields'] == 'REJECT', 'source unknownFields is not REJECT')
    need(contract['sourceAuthentication'] == 'FIXTURE_ONLY', 'sourceAuthentication is not FIXTURE_ONLY')

    for key, value in _walk(document):
        if key in ('servers', 'security', 'securitySchemes', 'url'):
            errors.append('forbidden transport or auth field: ' + key)
        if isinstance(value, str) and ('http://' in value or 'https://' in value or 'localhost' in value.lower()):
            errors.append('forbidden endpoint string near key ' + key)

    schemas = ((document.get('components') or {}).get('schemas')) or {}
    need(set(schemas) == set(names) | {'LocalCallEnvelope'},
         'schema names drifted from protocol_contract.json commands')
    for name, schema in commands.items():
        if schemas.get(name) != schema:
            errors.append('command schema drift: ' + name)
        elif schema.get('additionalProperties') is not False:
            errors.append('additionalProperties is not false: ' + name)

    envelope = schemas.get('LocalCallEnvelope') or {}
    need(envelope.get('additionalProperties') is False, 'LocalCallEnvelope must reject unknown fields')
    need(envelope.get('required') == ['operationId', 'actor', 'action', 'body'],
         'local-call parameter list drift')
    need((envelope.get('properties') or {}).get('action', {}).get('enum') == names,
         'action enum drift')
    branches = {}
    for entry in envelope.get('allOf') or []:
        const = (((entry.get('if') or {}).get('properties') or {}).get('action') or {}).get('const')
        ref = (((entry.get('then') or {}).get('properties') or {}).get('body') or {}).get('$ref')
        branches[const] = ref
    need(list(branches) == names, 'action/body discriminator drift')
    for name in names:
        need(branches.get(name) == '#/components/schemas/' + name, 'body $ref drift: ' + name)

    mapping = document.get('x-kix-action-body-map') or {}
    need(list(mapping) == names, 'x-kix-action-body-map key drift')
    for name in names:
        need(mapping.get(name) == '#/components/schemas/' + name, 'action map $ref drift: ' + name)

    operations = document.get('x-kix-local-call-operations') or []
    operation_ids = [item.get('operationId') for item in operations]
    need(operation_ids == names, 'local-call operationIds drifted from command keys')
    for item in operations:
        need(item.get('x-kix-transport') == 'contract-only-placeholder',
             'command analogue missing contract-only-placeholder: ' + str(item.get('operationId')))
        need(item.get('x-kix-not-a-published-http-service') is True,
             'command analogue must not claim an HTTP service: ' + str(item.get('operationId')))

    paths = document.get('paths') or {}
    need(list(paths) == [PLACEHOLDER_PATH], 'placeholder path set drift')
    post = (paths.get(PLACEHOLDER_PATH) or {}).get('post') or {}
    need(post.get('operationId') == GENERIC_OPERATION_ID, 'generic operationId drift')
    need(GENERIC_OPERATION_ID not in names, 'generic operationId collides with a command')
    need(post.get('x-kix-transport') == 'contract-only-placeholder',
         'placeholder path must be marked contract-only-placeholder')
    need(post.get('x-kix-not-a-published-http-service') is True,
         'placeholder path must not claim an HTTP service')
    response = (post.get('responses') or {}).get('default') or {}
    need(response.get('x-kix-http-status') == 'not-a-transport-contract',
         'placeholder response must not be a transport contract')
    return errors


def self_test(contract, source_bytes):
    document = build_document(contract, source_bytes)
    if validate(contract, source_bytes, document):
        print('self-test: canonical document failed validation', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['components']['schemas']['abort_effect'].pop('additionalProperties')
    if not any('abort_effect' in item for item in validate(contract, source_bytes, broken)):
        print('self-test: dropped additionalProperties was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    del broken['components']['schemas']['capture']
    if not validate(contract, source_bytes, broken):
        print('self-test: missing command was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['servers'] = [{'url': 'https://example.invalid'}]
    if not validate(contract, source_bytes, broken):
        print('self-test: servers entry was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['x-kix-contract-status'] = 'live'
    if not validate(contract, source_bytes, broken):
        print('self-test: live status was accepted', file=sys.stderr)
        return 1
    print('self-test: pass')
    return 0


def main(argv):
    source_bytes = SOURCE_PATH.read_bytes()
    contract = json.loads(source_bytes)
    document = build_document(contract, source_bytes)
    if '--self-test' in argv:
        return self_test(contract, source_bytes)
    if '--write' in argv:
        OPENAPI_PATH.parent.mkdir(parents=True, exist_ok=True)
        OPENAPI_PATH.write_text(render(document), encoding='utf-8')
        print('wrote ' + str(OPENAPI_PATH.relative_to(ROOT)))
        return 0
    if not OPENAPI_PATH.is_file():
        print('missing ' + str(OPENAPI_PATH), file=sys.stderr)
        return 1
    actual = json.loads(OPENAPI_PATH.read_text(encoding='utf-8'))
    errors = validate(contract, source_bytes, actual)
    if actual != document:
        errors.append('committed OpenAPI document != canonical derivation')
    if errors:
        print('openapi contract pin failed:', file=sys.stderr)
        for item in errors:
            print('- ' + item, file=sys.stderr)
        return 1
    print(
        'openapi contract pin ok: commands=%d sha256=%s gitBlob=%s'
        % (len(contract['commands']), hashlib.sha256(source_bytes).hexdigest(), git_blob_id(source_bytes))
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
