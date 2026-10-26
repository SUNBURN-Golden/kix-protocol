#!/usr/bin/env python3
"""Fail if the contract-only OpenAPI catalogue drifts from protocol_contract.json.

The catalogue is a local-call analogue. It does not describe a live HTTP server.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from integration_gate.fsm_contract import drift_problems, load_fsm
from integration_gate.openapi_doc import validate as validate_gate
SOURCE_PATH = ROOT / 'reference/v0.3-rc1/protocol_contract.json'
COMMON_PATH = ROOT / 'reference/v0.3-rc1/common.py'
CORE_PATH = ROOT / 'reference/v0.3-rc1/core.py'
OPENAPI_PATH = ROOT / 'docs/contracts/openapi/kix-protocol.contract-only.openapi.json'
GATE_OPENAPI_PATH = ROOT / 'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json'
README_PATH = ROOT / 'docs/contracts/openapi/README.md'
README_PIN_HEADING = '## 핀'
SPEC_ENVELOPE = 'reference/v0.1/KIX_프로토콜_통합명세_v0.1.md §9.1'
LOCAL_CALL = 'reference/v0.3-rc1/core.py Core.execute'
PLACEHOLDER_PATH = '/x-kix-contract-only/local-call'
GENERIC_OPERATION_ID = 'invokeLocalCall'


def git_blob_id(data):
    header = b'blob ' + str(len(data)).encode('ascii') + b'\0'
    return hashlib.sha1(header + data).hexdigest()


def render(document):
    return json.dumps(document, ensure_ascii=False, indent=2) + '\n'


def build_document(contract, source_bytes, fsm, fsm_bytes):
    """Canonical OpenAPI 3.1 catalogue. Core and FSM schemas are copied, not rewritten."""
    core_commands = contract['commands']
    fsm_schemas = {name: spec['schema'] for name, spec in fsm['commands'].items()}
    commands = {}
    commands.update(core_commands)
    commands.update(fsm_schemas)
    names = list(commands)
    fsm_sha256 = hashlib.sha256(fsm_bytes).hexdigest()
    fsm_blob = git_blob_id(fsm_bytes)
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
                    'Selects the body schema. Equal to a core command key or '
                    'an FSM catalogue key of the form machine_op.'
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
                'A caller-supplied actor string must not be treated as authority.\n\n'
                'The 40 core command schemas are copied from '
                'protocol_contract.json. The FSM command schemas are copied from '
                'docs/contracts/openapi/fsm-command-contract.json. Wire names are '
                'machine_op. consume_admission is not a catalogue name. '
                'Queries, reconcile, export_journal, restore, reject, and '
                'attempt_execution are not in this catalogue. '
                'There is still no live HTTP server and no production endpoint.'
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
            'coreCommandCount': len(core_commands),
            'fsmSource': {
                'path': 'docs/contracts/openapi/fsm-command-contract.json',
                'gitBlob': fsm_blob,
                'sha256': fsm_sha256,
                'domain': fsm['domain'],
                'unknownFields': fsm['unknownFields'],
                'sourceAuthentication': fsm['sourceAuthentication'],
                'handlerConstraints': fsm['handlerConstraints'],
                'commandCount': len(fsm_schemas),
            },
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


def readme_pin_problems(readme_text, document, gate_document):
    """Compare the human-readable pin table with both machine-readable sources."""
    lines = readme_text.splitlines()
    if lines.count(README_PIN_HEADING) != 1:
        return ['README pin table expected one heading: ' + README_PIN_HEADING]
    start = lines.index(README_PIN_HEADING) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith('## ')), len(lines))
    rows = {}
    for line in lines[start:end]:
        if not line.startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells == ['항목', '값'] or all(cell and not cell.strip('-:') for cell in cells):
            continue
        rows.setdefault(cells[0], []).append(cells[1:])

    cs = document.get('x-kix-source') or {}
    gs = gate_document.get('x-kix-source') or {}
    expected = {
        '원본 경로': [('contract-only', 'path', cs.get('path')),
                    ('integration-gate', 'protocolContract', gs.get('protocolContract'))],
    }
    for label in ('git blob', 'sha256', 'domain'):
        field = 'gitBlob' if label == 'git blob' else label
        expected[label] = [('contract-only', field, cs.get(field)),
                           ('integration-gate', field, gs.get(field))]
    for label, field in (('원본 경로', 'path'), ('git blob', 'gitBlob'),
                         ('sha256', 'sha256'), ('domain', 'domain')):
        expected['FSM ' + label] = [
            (kind, 'fsmSource.' + field, (source.get('fsmSource') or {}).get(field))
            for kind, source in (('contract-only', cs), ('integration-gate', gs))
        ]
    expected['`x-kix-contract-status`'] = [
        ('contract-only', 'x-kix-contract-status', document.get('x-kix-contract-status')),
    ]
    errors = []
    for label in rows.keys() - expected.keys():
        errors.append('README pin table unexpected row: ' + label)
    for label, sources in expected.items():
        if label not in rows:
            errors.append('README pin table missing row: ' + label)
            continue
        if len(rows[label]) != 1:
            errors.append('README pin table duplicated row: ' + label)
        for kind, field, value in sources:
            if not isinstance(value, str) or rows[label] != [['`' + value + '`']]:
                errors.append('README pin table mismatch: %s != %s %s' % (label, kind, field))
    return errors


def gate_marker_problems(gate_document):
    """Keep the published gate's public/production markers explicitly false."""
    errors = []
    if gate_document.get('x-kix-public-host') is not False:
        errors.append('integration-gate publicHost must be false')
    if (gate_document.get('x-kix-live-http-server') or {}).get('publicHost') is not False:
        errors.append('integration-gate liveHttpServer.publicHost must be false')
    if gate_document.get('x-kix-production-endpoint') is not False:
        errors.append('integration-gate productionEndpoint must be false')
    return errors


def _contains_expression(tree, expression):
    expected = ast.dump(ast.parse(expression, mode='eval').body)
    return any(ast.dump(node) == expected for node in ast.walk(tree))


def _core_execute(core_bytes):
    tree = ast.parse(core_bytes)
    core = next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == 'Core')
    return next(node for node in core.body
                if isinstance(node, ast.FunctionDef) and node.name == 'execute')


def reference_observed_problems(document, common_bytes, core_bytes):
    """Compare observed identifier rules to source ASTs, without importing them."""
    prefix = 'reference-observed: '
    try:
        tree = ast.parse(common_bytes)
        ident = next(node for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name == 'ident')
        bounds = [node.comparators[1].value for node in ast.walk(ident)
                  if isinstance(node, ast.Compare) and len(node.ops) == 2
                  and isinstance(node.ops[0], ast.Lt) and isinstance(node.ops[1], ast.LtE)
                  and isinstance(node.comparators[1], ast.Constant)
                  and type(node.comparators[1].value) is int
                  and _contains_expression(node.left, '0')
                  and _contains_expression(node.comparators[0], 'len(value)')]
        if len(bounds) != 1 or bounds[0] <= 0:
            return [prefix + 'ident source must bound 0 < len(value) <= N']
        bound = bounds[0]
        predicate = ('isinstance(value, str) and 0 < len(value) <= %d '
                     'and value.strip() == value' % bound)
        checks = [node for node in ast.walk(ident)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                  and node.func.id == 'require' and len(node.args) == 2
                  and ast.dump(node.args[0]) == ast.dump(ast.parse(predicate, mode='eval').body)
                  and isinstance(node.args[1], ast.Constant)
                  and isinstance(node.args[1].value, str)]
        if len(checks) != 1:
            return [prefix + 'ident source must require string/length/whitespace with an error code']
        source_error = checks[0].args[1].value
        execute = _core_execute(core_bytes)
    except (SyntaxError, ValueError, StopIteration, UnicodeError):
        return [prefix + 'cannot read ident/Core.execute source AST']
    errors = []
    for parameter in ('operation_id', 'actor'):
        if not _contains_expression(execute, 'ident(%s)' % parameter):
            errors.append(prefix + 'Core.execute must call ident(%s)' % parameter)
    if not _contains_expression(execute, 'require(old[0] == fingerprint, "OPERATION_ID_CONFLICT")'):
        errors.append(prefix + 'Core.execute must retain OPERATION_ID_CONFLICT check')
    envelope = (document.get('components') or {}).get('schemas', {}).get('LocalCallEnvelope') or {}
    properties = envelope.get('properties') or {}
    for name in ('operationId', 'actor'):
        observed = (properties.get(name) or {}).get('x-kix-reference-model-observed') or {}
        for field, expected in (('check', 'ident'), ('error', source_error),
                                ('notInExportedCommandSchema', True)):
            actual = observed.get(field)
            if actual != expected or (expected is True and actual is not True):
                errors.append(prefix + name + '.' + field + ' must be ' + str(expected))
        rule = observed.get('rule')
        rule = rule if isinstance(rule, str) else ''
        lengths = re.findall(r'length at most (\d+)', rule)
        if (lengths != [str(bound)] or 'non-empty' not in rule
                or 'no leading or trailing whitespace' not in rule):
            errors.append(prefix + name + '.rule must match ident bound %d and whitespace rule' % bound)
        if name == 'operationId':
            invocation = observed.get('sameInvocation') or ''
            if 'OPERATION_ID_CONFLICT' not in invocation or 'not an HTTP retry contract' not in invocation:
                errors.append(prefix + 'operationId.sameInvocation must separate conflict from HTTP retry')
    return errors


def envelope_domain_problems(document, contract, core_bytes):
    """Keep specification fields distinct from local parameters and body.domain."""
    errors = []

    def need(condition, message):
        if not condition:
            errors.append('envelope-domain: ' + message)

    specification = document.get('x-kix-specification-envelope') or {}
    need(specification.get('fields') == ['protocolDomain', 'operationId', 'actorContext', 'action', 'body'],
         'specification fields drifted')
    need((specification.get('pythonLocalCall') or {}).get('parameters') ==
         ['operationId', 'actor', 'action', 'body'], 'Python local-call parameters drifted')
    envelope = (document.get('components') or {}).get('schemas', {}).get('LocalCallEnvelope') or {}
    properties = envelope.get('properties') or {}
    for name in ('protocolDomain', 'actorContext', 'domain'):
        need(name not in properties and name not in (envelope.get('required') or []),
             name + ' must not be a local envelope field')
    need((properties.get('actor') or {}).get('x-kix-specification-field') == 'actorContext',
         'actor must map to specification actorContext')
    check = envelope.get('x-kix-body-domain-check') or {}
    for field, expected in (('specificationField', 'protocolDomain'), ('pinnedDomain', contract['domain']),
                            ('notASeparatePythonArgument', True), ('constNotAddedToCommandSchema', True),
                            ('error', 'DOMAIN_MISMATCH')):
        actual = check.get(field)
        need(actual == expected and (expected is not True or actual is True),
             'body-domain ' + field + ' must be ' + str(expected))
    try:
        execute = _core_execute(core_bytes)
    except (SyntaxError, ValueError, StopIteration, UnicodeError):
        need(False, 'cannot read Core.execute source AST')
        return errors
    args = execute.args
    need([arg.arg for arg in args.posonlyargs + args.args] ==
         ['self', 'operation_id', 'actor', 'action', 'body']
         and args.vararg is None and args.kwarg is None
         and not {'actor_context', 'protocol_domain'} & {arg.arg for arg in args.kwonlyargs},
         'Core.execute must keep the fixed local parameters plus keyword-only options')
    need(_contains_expression(execute,
                             'require(isinstance(body, dict) and body.get("domain") == self.DOMAIN, '
                             '"DOMAIN_MISMATCH")'),
         'Core.execute must compare body.domain with self.DOMAIN using DOMAIN_MISMATCH')
    return errors


def validate(contract, source_bytes, document, fsm, fsm_bytes, gate_document=None):
    """Independent checks against both pinned sources. Returns error strings."""
    errors = []
    core_commands = contract['commands']
    fsm_schemas = {name: spec['schema'] for name, spec in fsm['commands'].items()}
    commands = {}
    commands.update(core_commands)
    commands.update(fsm_schemas)
    names = list(commands)
    for item in drift_problems(fsm):
        errors.append(item)

    def need(condition, message):
        if not condition:
            errors.append(message)

    documents = [('contract-only', document)]
    if gate_document is not None:
        documents.append(('integration-gate', gate_document))
        errors.extend(gate_marker_problems(gate_document))
    for label, item in documents:
        for path, path_item in (item.get('paths') or {}).items():
            for key in path_item:
                if key.lower() == 'options':
                    errors.append('OPTIONS operation forbidden: %s %s' % (label, path))

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
    need(source.get('coreCommandCount') == len(core_commands), 'coreCommandCount drift')
    fsm_source = source.get('fsmSource') or {}
    fsm_sha256 = hashlib.sha256(fsm_bytes).hexdigest()
    fsm_blob = git_blob_id(fsm_bytes)
    need(fsm_source.get('path') == 'docs/contracts/openapi/fsm-command-contract.json',
         'fsm source path drift')
    need(fsm_source.get('gitBlob') == fsm_blob, 'fsm source git blob drift')
    need(fsm_source.get('sha256') == fsm_sha256, 'fsm source sha256 drift')
    need(fsm_source.get('domain') == fsm['domain'], 'fsm domain drift')
    need(fsm_source.get('unknownFields') == fsm['unknownFields'], 'fsm unknownFields drift')
    need(fsm_source.get('sourceAuthentication') == fsm['sourceAuthentication'],
         'fsm sourceAuthentication drift')
    need(fsm_source.get('handlerConstraints') == fsm['handlerConstraints'],
         'fsm handlerConstraints drift')
    need(fsm_source.get('commandCount') == len(fsm_schemas), 'fsm commandCount drift')
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
    for name, schema in core_commands.items():
        if schemas.get(name) != schema:
            errors.append('command schema drift: ' + name)
        elif schema.get('additionalProperties') is not False:
            errors.append('additionalProperties is not false: ' + name)
    for name, schema in fsm_schemas.items():
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


def self_test(contract, source_bytes, fsm, fsm_bytes, gate_document, readme_text,
              common_bytes, core_bytes):
    document = build_document(contract, source_bytes, fsm, fsm_bytes)
    if (validate(contract, source_bytes, document, fsm, fsm_bytes, gate_document=gate_document)
            or readme_pin_problems(readme_text, document, gate_document)
            or reference_observed_problems(document, common_bytes, core_bytes)
            or envelope_domain_problems(document, contract, core_bytes)):
        print('self-test: canonical document failed validation', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['components']['schemas']['abort_effect'].pop('additionalProperties')
    if not any('abort_effect' in item for item in validate(contract, source_bytes, broken, fsm, fsm_bytes)):
        print('self-test: dropped additionalProperties was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['components']['schemas']['settlement_initiate'].pop('additionalProperties')
    if not any('settlement_initiate' in item for item in validate(contract, source_bytes, broken, fsm, fsm_bytes)):
        print('self-test: dropped FSM additionalProperties was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    del broken['components']['schemas']['capture']
    if not validate(contract, source_bytes, broken, fsm, fsm_bytes):
        print('self-test: missing command was accepted', file=sys.stderr)
        return 1
    broken_fsm = copy.deepcopy(fsm)
    broken_fsm['machines']['settlement']['replayable'] = [
        op for op in broken_fsm['machines']['settlement']['replayable'] if op != 'initiate'
    ]
    if not any('REPLAYABLE' in item or 'command set' in item for item in drift_problems(broken_fsm)):
        print('self-test: command missing from REPLAYABLE was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['servers'] = [{'url': 'https://example.invalid'}]
    if not validate(contract, source_bytes, broken, fsm, fsm_bytes):
        print('self-test: servers entry was accepted', file=sys.stderr)
        return 1
    broken = copy.deepcopy(document)
    broken['x-kix-contract-status'] = 'live'
    if not validate(contract, source_bytes, broken, fsm, fsm_bytes):
        print('self-test: live status was accepted', file=sys.stderr)
        return 1

    cases = []
    for label, field, value, diagnostic in (
        ('ident bound', 'rule', 'non-empty string, length at most 99, no leading or trailing whitespace',
         'operationId.rule must match ident bound 100'),
        ('ident error', 'error', 'X', 'operationId.error must be INVALID_ID'),
    ):
        broken = copy.deepcopy(document)
        observed = broken['components']['schemas']['LocalCallEnvelope']['properties']['operationId']
        observed['x-kix-reference-model-observed'][field] = value
        cases.append((label, reference_observed_problems(broken, common_bytes, core_bytes),
                      'reference-observed: ' + diagnostic))
    broken = copy.deepcopy(document)
    del broken['components']['schemas']['LocalCallEnvelope']['properties']['actor']['x-kix-reference-model-observed']
    cases.append(('actor observed block removed',
                  reference_observed_problems(broken, common_bytes, core_bytes),
                  'reference-observed: actor.check must be ident'))
    changed_common = common_bytes.replace(b'<= 100', b'<= 64', 1)
    cases.append(('source ident bound drift',
                  reference_observed_problems(document, changed_common, core_bytes),
                  'reference-observed: operationId.rule must match ident bound 64'))
    broken = copy.deepcopy(document)
    broken['components']['schemas']['LocalCallEnvelope']['properties']['protocolDomain'] = {'type': 'string'}
    cases.append(('specification field added to local envelope',
                  envelope_domain_problems(broken, contract, core_bytes),
                  'envelope-domain: protocolDomain must not be a local envelope field'))
    for label, field, value in (
        ('body-domain specification conflation', 'specificationField', 'actorContext'),
        ('body-domain separate argument', 'notASeparatePythonArgument', False),
        ('body-domain pin drift', 'pinnedDomain', 'wrong-domain'),
    ):
        broken = copy.deepcopy(document)
        broken['components']['schemas']['LocalCallEnvelope']['x-kix-body-domain-check'][field] = value
        cases.append((label, envelope_domain_problems(broken, contract, core_bytes),
                      'envelope-domain: body-domain ' + field + ' must be'))
    # Source fixtures remain in memory; never mutate or import pinned reference code.
    for label, original, replacement, diagnostic in (
        ('source trim removed', b' and value.strip() == value', b'',
         'ident source must require string/length/whitespace with an error code'),
        ('source actor validation removed', b'ident(actor)', b'pass',
         'Core.execute must call ident(actor)'),
        ('source conflict changed', b'OPERATION_ID_CONFLICT', b'OTHER_CONFLICT',
         'Core.execute must retain OPERATION_ID_CONFLICT check'),
    ):
        changed_common = common_bytes.replace(original, replacement, 1)
        changed_core = core_bytes.replace(original, replacement, 1)
        cases.append((label, reference_observed_problems(document, changed_common, changed_core),
                      'reference-observed: ' + diagnostic))
    for label, original, replacement, diagnostic in (
        ('source domain comparison changed', b'body.get("domain") == self.DOMAIN',
         b'body.get("domain") != self.DOMAIN', 'Core.execute must compare body.domain'),
        ('source extra envelope argument', b'*, fail_before_commit',
         b'*, protocol_domain=None, fail_before_commit', 'Core.execute must keep the fixed local parameters'),
    ):
        cases.append((label, envelope_domain_problems(
            document, contract, core_bytes.replace(original, replacement, 1)),
            'envelope-domain: ' + diagnostic))
    broken = copy.deepcopy(document)
    broken['components']['schemas']['kyc_verify'] = {'type': 'object', 'additionalProperties': False}
    operation = copy.deepcopy(broken['x-kix-local-call-operations'][0])
    operation.update(operationId='kyc_verify', action='kyc_verify',
                     requestBodySchema='#/components/schemas/kyc_verify')
    broken['x-kix-local-call-operations'].append(operation)
    broken['x-kix-action-body-map']['kyc_verify'] = '#/components/schemas/kyc_verify'
    cases.append(('added command', validate(contract, source_bytes, broken, fsm, fsm_bytes),
                  'schema names drifted'))
    broken = copy.deepcopy(document)
    broken['components']['securitySchemes'] = {'fixture': {'type': 'http', 'scheme': 'bearer'}}
    cases.append(('security scheme', validate(contract, source_bytes, broken, fsm, fsm_bytes),
                  'forbidden transport or auth field: securitySchemes'))
    for label in ('contract-only', 'gate'):
        broken = copy.deepcopy(document)
        broken_gate = copy.deepcopy(gate_document)
        target = broken if label == 'contract-only' else broken_gate
        target['paths'][PLACEHOLDER_PATH]['options'] = {'operationId': 'preflight'}
        cases.append((label + ' OPTIONS',
                      validate(contract, source_bytes, broken, fsm, fsm_bytes,
                               gate_document=broken_gate),
                      'OPTIONS operation forbidden: ' + ('integration-gate' if label == 'gate' else label)))
    for label, field, nested, diagnostic in (
        ('gate publicHost', 'x-kix-public-host', None, 'publicHost must be false'),
        ('gate liveHttpServer.publicHost', 'x-kix-live-http-server', 'publicHost',
         'liveHttpServer.publicHost must be false'),
        ('gate productionEndpoint', 'x-kix-production-endpoint', None,
         'productionEndpoint must be false'),
    ):
        broken_gate = copy.deepcopy(gate_document)
        if nested is None:
            broken_gate[field] = True
        else:
            broken_gate[field][nested] = True
        if not validate_gate(ROOT, broken_gate):
            print('self-test: gate validator accepted ' + label, file=sys.stderr)
            return 1
        cases.append((label, validate(contract, source_bytes, document, fsm, fsm_bytes,
                                      gate_document=broken_gate), diagnostic))
    broken_readme = readme_text.replace(document['x-kix-source']['sha256'], '0' * 64)
    cases.append(('README sha256', readme_pin_problems(broken_readme, document, gate_document),
                  'README pin table mismatch: sha256'))
    broken_readme = '\n'.join(line for line in readme_text.splitlines()
                              if not line.startswith('| FSM domain |'))
    cases.append(('README row removed', readme_pin_problems(broken_readme, document, gate_document),
                  'missing row: FSM domain'))
    row = next(line for line in readme_text.splitlines() if line.startswith('| git blob |'))
    broken_readme = readme_text.replace(row, row + '\n' + row, 1)
    cases.append(('README row duplicated', readme_pin_problems(broken_readme, document, gate_document),
                  'duplicated row: git blob'))
    broken_gate = copy.deepcopy(gate_document)
    broken_gate['x-kix-source']['sha256'] = '0' * 64
    cases.append(('gate pin drift', readme_pin_problems(readme_text, document, broken_gate),
                  '!= integration-gate'))
    for label, errors, expected in cases:
        matching = next((error for error in errors if expected in error), None)
        if matching is None:
            print('self-test: missing diagnostic for ' + label, file=sys.stderr)
            return 1
        print('self-test: detected %s: %s' % (label, matching))
    print('self-test: pass')
    return 0


def main(argv):
    source_bytes = SOURCE_PATH.read_bytes()
    common_bytes = COMMON_PATH.read_bytes()
    core_bytes = CORE_PATH.read_bytes()
    contract = json.loads(source_bytes)
    fsm, fsm_bytes = load_fsm(ROOT)
    document = build_document(contract, source_bytes, fsm, fsm_bytes)
    if '--self-test' in argv:
        gate = json.loads(GATE_OPENAPI_PATH.read_text(encoding='utf-8'))
        readme = README_PATH.read_text(encoding='utf-8')
        return self_test(contract, source_bytes, fsm, fsm_bytes, gate, readme,
                         common_bytes, core_bytes)
    if '--write' in argv:
        OPENAPI_PATH.parent.mkdir(parents=True, exist_ok=True)
        OPENAPI_PATH.write_text(render(document), encoding='utf-8')
        print('wrote ' + str(OPENAPI_PATH.relative_to(ROOT)))
        return 0
    if not OPENAPI_PATH.is_file():
        print('missing ' + str(OPENAPI_PATH), file=sys.stderr)
        return 1
    actual = json.loads(OPENAPI_PATH.read_text(encoding='utf-8'))
    gate = json.loads(GATE_OPENAPI_PATH.read_text(encoding='utf-8'))
    readme = README_PATH.read_text(encoding='utf-8')
    errors = validate(contract, source_bytes, actual, fsm, fsm_bytes, gate_document=gate)
    errors.extend(readme_pin_problems(readme, actual, gate))
    errors.extend(reference_observed_problems(actual, common_bytes, core_bytes))
    errors.extend(envelope_domain_problems(actual, contract, core_bytes))
    if actual != document:
        errors.append('committed OpenAPI document != canonical derivation')
    if errors:
        print('openapi contract pin failed:', file=sys.stderr)
        for item in errors:
            print('- ' + item, file=sys.stderr)
        return 1
    print(
        'openapi contract pin ok: commands=%d core=%d fsm=%d sha256=%s gitBlob=%s'
        % (
            len(document['x-kix-local-call-operations']),
            len(contract['commands']),
            len(fsm['commands']),
            hashlib.sha256(source_bytes).hexdigest(),
            git_blob_id(source_bytes),
        )
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
