#!/usr/bin/env python3
"""Check the non-normative commerce consumer binding index.

The record at ``docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json`` binds
each published core and FSM command, and each of the 13 owner-decided read
query names, to its pinned source, body-schema reference, gate route, offline
journey evidence and exactly one status.

This checker derives the 84 command names from the released catalogue helper,
recomputes every pinned sha256 and Git-blob digest, cross-checks the producer
qualification tuple, re-derives the 44-step offline journey fixture, and
refuses drift, an unknown or missing command, a read query upgraded from
``NOT_BOUND`` and any semantic or consumer qualification claim.

The record is non-normative navigation. ``BOOTSTRAP_SCHEMA_BOUND`` binds
catalogue/schema identity only and is not consumer acceptance. Standard
library only; the released ``integration_gate.catalogue`` helper is reused for
the command set and Git-blob formula.

Exit status is 0 when the record and every pinned artefact agree, 1 otherwise.
``--self-test`` mutates in-memory copies only and requires detection of each
negative control listed in ``self_test``.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration_gate.catalogue import git_blob_id, load_catalogue

RECORD_PATH = 'docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json'

SCHEMA_VERSION = 'kix-commerce-consumer-binding-index/1'
RECORD_KIND = 'NON_NORMATIVE_CONSUMER_BINDING_INDEX'
RECORD_DATE = '2026-11-10'
STATUS_ENUM = (
    'BOOTSTRAP_SCHEMA_BOUND',
    'MOCK_EVIDENCE',
    'HOLD_SEMANTIC',
    'NOT_BOUND',
)
COMMAND_STATUSES = ('BOOTSTRAP_SCHEMA_BOUND', 'MOCK_EVIDENCE')

PRODUCER_PATH = 'docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json'
PROTOCOL_PATH = 'reference/v0.3-rc1/protocol_contract.json'
FSM_PATH = 'docs/contracts/openapi/fsm-command-contract.json'
CONTRACT_ONLY_PATH = 'docs/contracts/openapi/kix-protocol.contract-only.openapi.json'
GATE_PATH = 'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json'
PROFILE_PATH = 'sdk/compat/profiles/bootstrap-2.profile.json'
MANIFEST_PATH = 'sdk/compat/manifests/manifest.bootstrap-2.json'
SIDECAR_PATH = 'sdk/compat/manifests/manifest.bootstrap-2.json.sha256'
CATALOGUE_PATH = 'sdk/generated/catalogue.ts'
JOURNEY_PATH = (
    'reference/booking_resale_admission/fixtures/'
    'commerce_journey_conformance_v1.json'
)
READ_QUERIES_PATH = 'docs/contracts/READ_MODEL_QUERIES.md'
READ_MANIFEST_PATH = 'reference/read_model/vectors/manifest.json'
READ_VECTOR_DIR = 'reference/read_model/vectors'
COMPAT_CONTRACT_PATH = 'docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md'
SD1_RECORD_PATH = 'docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md'

ENVELOPE = 'POST /x-kix-contract-only/local-call {operationId, actor, action, body}'
GATE_ROUTE = '/x-kix-contract-only/local-call'
DEPENDENCIES = [
    'openapi-catalogue-promotion',
    'p-sdk-0',
    'plan-commerce-journey-end-to-end-conformance',
]

REQUIRED_PIN_IDS = (
    'producer_qualification_tuple',
    'protocol_contract_json',
    'fsm_command_contract',
    'contract_only_openapi',
    'integration_gate_openapi',
    'compat_profile',
    'compat_manifest',
    'compat_manifest_sidecar',
    'generated_sdk_catalogue',
    'journey_fixture',
    'read_model_queries',
    'read_model_vectors_manifest',
    'compat_manifest_contract',
    'sd1_addendum',
)

# Index pin id -> producer tuple artifact id. The sidecar id differs.
PIN_PRODUCER_IDS = {
    'protocol_contract_json': 'protocol_contract_json',
    'fsm_command_contract': 'fsm_command_contract',
    'contract_only_openapi': 'contract_only_openapi',
    'integration_gate_openapi': 'integration_gate_openapi',
    'compat_profile': 'compat_profile',
    'compat_manifest': 'compat_manifest',
    'compat_manifest_sidecar': 'manifest_sidecar',
    'generated_sdk_catalogue': 'generated_sdk_catalogue',
    'read_model_vectors_manifest': 'read_model_vector_manifest',
}

PREFIXED_ARTEFACT_PINS = {
    'producer_qualification_tuple': PRODUCER_PATH,
    'protocol_contract_json': PROTOCOL_PATH,
    'fsm_command_contract': FSM_PATH,
    'contract_only_openapi': CONTRACT_ONLY_PATH,
    'integration_gate_openapi': GATE_PATH,
    'compat_profile': PROFILE_PATH,
    'compat_manifest': MANIFEST_PATH,
    'compat_manifest_sidecar': SIDECAR_PATH,
    'generated_sdk_catalogue': CATALOGUE_PATH,
    'journey_fixture': JOURNEY_PATH,
    'read_model_queries': READ_QUERIES_PATH,
    'read_model_vectors_manifest': READ_MANIFEST_PATH,
    'compat_manifest_contract': COMPAT_CONTRACT_PATH,
    'sd1_addendum': SD1_RECORD_PATH,
}

REQUIRED_NON_CLAIMS = (
    'BOOTSTRAP is not consumer acceptance.',
    'This record is non-normative consumer binding navigation only.',
    'Semantic SDK consumption remains HOLD_SEMANTIC and is not qualified.',
    'No read query is published, bound or added to any catalogue.',
    'External kix-commerce-apps consumer expectations are UNVERIFIED.',
    'SD1 remains User-owned and OPEN; no option, waiver or verifier order is chosen.',
)

TOP_LEVEL_KEYS = {
    'record_schema_version',
    'record_kind',
    'normative',
    'record_date',
    'status_enum',
    'status_definitions',
    'basis',
    'pins',
    'profile',
    'surfaces',
    'commands',
    'readQueries',
    'journey',
    'externalConsumerExpectations',
    'sd1',
    'nonClaims',
}
BASIS_KEYS = {
    'observed_origin_main',
    'base_commit',
    'task',
    'dependencies',
    'note',
}
PIN_KEYS = {'id', 'path', 'role', 'sha256', 'gitBlob'}
PROFILE_KEYS = {
    'manifestSchemaVersion',
    'profileKind',
    'profileRevision',
    'grants',
    'semanticConsumerStatus',
    'bootstrapIsConsumerAcceptance',
}
SURFACES_KEYS = {
    'contractOnlyOpenApi',
    'integrationGateOpenApi',
    'envelope',
    'gateRoute',
}
ENVELOPE_KEYS = {'operationId', 'actor', 'action', 'body'}
COMMANDS_KEYS = {'count', 'coreCount', 'fsmCount', 'items'}
CORE_ITEM_KEYS = {
    'name',
    'source',
    'sourcePath',
    'action',
    'envelope',
    'gateRoute',
    'gateDispatch',
    'bodySchemaRef',
    'journeySteps',
    'status',
}
FSM_ITEM_KEYS = CORE_ITEM_KEYS | {'machine', 'op', 'subjectField'}
READ_QUERIES_KEYS = {'count', 'source', 'items'}
READ_ITEM_KEYS = {
    'name',
    'kind',
    'candidateVector',
    'fixtureSha256',
    'status',
    'reason',
}
JOURNEY_KEYS = {
    'fixturePath',
    'fixtureSha256',
    'fixtureVersion',
    'stepCount',
    'uniqueActionCount',
}
EXTERNAL_KEYS = {'consumer', 'status', 'reason'}
SD1_KEYS = {
    'id',
    'owner',
    'userOwned',
    'status',
    'resolved',
    'contract',
    'record',
    'decision',
}

SD1_FORBIDDEN_KEYS = {
    'selected_option',
    'option',
    'options',
    'waiver',
    'verifier_order',
    'resolution',
}
FORBIDDEN_CLAIM_KEYS = {
    'semanticConformance',
    'semantic_conformance',
    'semanticQualification',
    'semantic_qualification',
    'consumerAcceptance',
    'consumer_acceptance',
    'consumerQualified',
    'consumer_qualified',
    'consumerVerified',
    'consumer_verified',
    'productionReady',
    'production_ready',
    'operationalApproval',
    'operational_approval',
    'nMinusOne',
    'n_minus_one',
    'qualified',
    'verified',
}

READ_COUNT = 13


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _is_hex(value, length):
    if not isinstance(value, str) or len(value) != length:
        return False
    return all(char in '0123456789abcdef' for char in value)


def _json(data):
    return json.loads(data.decode('utf-8'))


def load_record(root=ROOT):
    path = Path(root) / RECORD_PATH
    return json.loads(path.read_text(encoding='utf-8')), path


def load_artefacts(record, root=ROOT):
    """Return ``{path: bytes}`` for every pin and read-model candidate vector."""
    root = Path(root)
    paths = set()
    for entry in record.get('pins') or []:
        if isinstance(entry, dict) and isinstance(entry.get('path'), str):
            paths.add(entry['path'])
    try:
        manifest = json.loads(
            (root / READ_MANIFEST_PATH).read_text(encoding='utf-8'))
        for name in (manifest.get('files') or {}):
            paths.add(READ_VECTOR_DIR + '/' + name)
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
    loaded = {}
    for path in sorted(paths):
        try:
            loaded[path] = (root / path).read_bytes()
        except OSError:
            continue
    return loaded


def _extras(problems, label, actual, allowed):
    if not isinstance(actual, dict):
        problems.append(label + ' is not an object')
        return False
    for key in sorted(set(actual) - allowed):
        problems.append('unexpected key %s: %s' % (label, key))
    for key in sorted(allowed - set(actual)):
        problems.append('missing key %s: %s' % (label, key))
    return True


def _status_fields(item):
    return [key for key in item if 'status' in key.lower()]


def _pin_index(record, problems):
    pins = record.get('pins')
    if not isinstance(pins, list) or not pins:
        problems.append('pins are missing')
        return {}
    by_id = {}
    by_path = {}
    for entry in pins:
        if not isinstance(entry, dict):
            problems.append('pin entry is not an object')
            continue
        _extras(problems, 'pin', entry, PIN_KEYS)
        pin_id = entry.get('id')
        path = entry.get('path')
        if not isinstance(pin_id, str) or not pin_id:
            problems.append('pin id missing')
            continue
        if pin_id in by_id:
            problems.append('duplicate pin id: ' + pin_id)
        if not isinstance(path, str) or not path:
            problems.append('pin path missing: ' + pin_id)
            continue
        if path in by_path:
            problems.append('duplicate pin path: ' + path)
        if path == RECORD_PATH:
            problems.append('pin must not point at the record itself: ' + pin_id)
        if not isinstance(entry.get('role'), str) or not entry['role']:
            problems.append('pin role missing: ' + pin_id)
        if not _is_hex(entry.get('sha256'), 64):
            problems.append('pin sha256 malformed: ' + pin_id)
        if not _is_hex(entry.get('gitBlob'), 40):
            problems.append('pin gitBlob malformed: ' + pin_id)
        by_id[pin_id] = entry
        by_path[path] = entry
    for pin_id in REQUIRED_PIN_IDS:
        if pin_id not in by_id:
            problems.append('missing pin id: ' + pin_id)
    for pin_id in sorted(set(by_id) - set(REQUIRED_PIN_IDS)):
        problems.append('unexpected pin id: ' + pin_id)
    for pin_id in REQUIRED_PIN_IDS:
        entry = by_id.get(pin_id)
        if not entry:
            continue
        expected_path = PREFIXED_ARTEFACT_PINS[pin_id]
        if entry.get('path') != expected_path:
            problems.append('pin path drift: %s (%s)' % (pin_id, entry.get('path')))
    return by_id


def _check_pins(record, artefacts, by_id, problems):
    for pin_id, entry in sorted(by_id.items()):
        path = entry.get('path')
        data = artefacts.get(path) if isinstance(path, str) else None
        if data is None:
            problems.append('missing pinned bytes: %s (%s)' % (pin_id, path))
            continue
        if sha256_bytes(data) != entry.get('sha256'):
            problems.append('pin sha256 drift: %s (%s)' % (pin_id, path))
        if git_blob_id(data) != entry.get('gitBlob'):
            problems.append('pin gitBlob drift: %s (%s)' % (pin_id, path))


def _check_producer(record, artefacts, by_id, expected_names, read_names,
                    problems):
    data = artefacts.get(PRODUCER_PATH)
    if data is None:
        problems.append('producer tuple bytes are missing')
        return None
    try:
        producer = _json(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        problems.append('producer tuple is unreadable')
        return None
    producer_artifacts = {
        entry.get('id'): entry
        for entry in producer.get('artifacts') or []
        if isinstance(entry, dict)
    }
    for pin_id, producer_id in sorted(PIN_PRODUCER_IDS.items()):
        ours = by_id.get(pin_id)
        theirs = producer_artifacts.get(producer_id)
        if not ours or not theirs:
            problems.append('producer tuple pin missing: %s' % pin_id)
            continue
        if ours.get('path') != theirs.get('path'):
            problems.append('producer tuple pin path mismatch: ' + pin_id)
        if ours.get('sha256') != theirs.get('sha256'):
            problems.append('producer tuple pin sha256 mismatch: ' + pin_id)
        if ours.get('gitBlob') != theirs.get('gitBlob'):
            problems.append('producer tuple pin gitBlob mismatch: ' + pin_id)
    producer_names = [
        item.get('name')
        for item in (producer.get('commands') or {}).get('items') or []
        if isinstance(item, dict)
    ]
    if producer_names != expected_names:
        problems.append('producer tuple command name set mismatch')
    producer_reads = {
        item.get('name'): item
        for item in (producer.get('read_queries') or {}).get('items') or []
        if isinstance(item, dict)
    }
    if set(producer_reads) != set(read_names):
        problems.append('producer tuple read name set mismatch')
    return producer


def _resolve_pointer(document, pointer):
    if pointer in ('', '/'):
        return document
    if not pointer.startswith('/'):
        return None
    current = document
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() \
                and int(token) < len(current):
            current = current[int(token)]
        else:
            return None
    return current


def _check_commands(record, catalogue, protocol, fsm, producer, problems):
    commands = record.get('commands')
    if not isinstance(commands, dict):
        problems.append('commands are missing')
        return catalogue.names
    _extras(problems, 'commands', commands, COMMANDS_KEYS)
    expected = catalogue.names
    core_names = list(protocol.get('commands') or {})
    fsm_commands = fsm.get('commands') or {}
    if commands.get('count') != len(expected):
        problems.append('command count drift: recorded=%r derived=%d'
                        % (commands.get('count'), len(expected)))
    if commands.get('coreCount') != len(core_names):
        problems.append('core command count drift: recorded=%r derived=%d'
                        % (commands.get('coreCount'), len(core_names)))
    if commands.get('fsmCount') != len(fsm_commands):
        problems.append('fsm command count drift: recorded=%r derived=%d'
                        % (commands.get('fsmCount'), len(fsm_commands)))
    items = commands.get('items')
    if not isinstance(items, list):
        problems.append('command items are not a list')
        items = []
    recorded = [item.get('name') if isinstance(item, dict) else None
                for item in items]
    if recorded != expected:
        for name in expected:
            if name not in recorded:
                problems.append('missing command: ' + name)
        for name in recorded:
            if name not in expected:
                problems.append('unknown command: ' + str(name))
        if len(recorded) != len(set(recorded)):
            problems.append('duplicate command entry')
        if set(recorded) == set(expected) and recorded != expected:
            problems.append('command order drift')
    producer_commands = {
        item.get('name'): item
        for item in ((producer or {}).get('commands') or {}).get('items') or []
        if isinstance(item, dict)
    }

    for item in items:
        if not isinstance(item, dict):
            problems.append('command item is not an object')
            continue
        name = item.get('name')
        is_fsm = isinstance(name, str) and name in fsm_commands
        allowed = FSM_ITEM_KEYS if is_fsm else CORE_ITEM_KEYS
        _extras(problems, 'command item %s' % name, item, allowed)
        status_fields = _status_fields(item)
        if not status_fields:
            problems.append('command status missing: ' + str(name))
        elif status_fields != ['status']:
            problems.append('multiple status fields for command: ' + str(name))
        status = item.get('status')
        if status not in COMMAND_STATUSES:
            problems.append('command status malformed: ' + str(name))
        if name not in expected:
            continue

        producer_item = producer_commands.get(name)
        if producer_item is None:
            problems.append('producer tuple lacks command: ' + name)
        else:
            for field in ('source', 'sourcePath', 'gateRoute', 'gateDispatch'):
                if item.get(field) != producer_item.get(field):
                    problems.append('command %s drift: %s' % (field, name))
            if is_fsm:
                for field in ('machine', 'op'):
                    if item.get(field) != producer_item.get(field):
                        problems.append('command %s drift: %s' % (field, name))
        if item.get('action') != name:
            problems.append('command action drift: ' + name)
        if item.get('envelope') != ENVELOPE:
            problems.append('command envelope drift: ' + name)
        if item.get('gateRoute') != GATE_ROUTE:
            problems.append('command gate route drift: ' + name)

        if is_fsm:
            spec = fsm_commands[name]
            machine = spec.get('machine')
            machine_spec = (fsm.get('machines') or {}).get(machine) or {}
            expected_ref = FSM_PATH + '#/commands/' + name + '/schema'
            expected_dispatch = 'in-process ' + str(machine_spec.get('class'))
            expected_path = machine_spec.get('module')
            if item.get('source') != 'fsm':
                problems.append('command source drift: ' + name)
            if item.get('sourcePath') != expected_path:
                problems.append('command sourcePath drift: ' + name)
            if item.get('machine') != machine:
                problems.append('command machine drift: ' + name)
            if item.get('op') != spec.get('op'):
                problems.append('command op drift: ' + name)
            if item.get('subjectField') != spec.get('subject_field'):
                problems.append('command subjectField drift: ' + name)
            if item.get('gateDispatch') != expected_dispatch:
                problems.append('command gateDispatch drift: ' + name)
        else:
            expected_ref = PROTOCOL_PATH + '#/commands/' + name
            if item.get('source') != 'core':
                problems.append('command source drift: ' + name)
            if item.get('sourcePath') != PROTOCOL_PATH:
                problems.append('command sourcePath drift: ' + name)
            if item.get('gateDispatch') != 'Core.execute':
                problems.append('command gateDispatch drift: ' + name)

        body_ref = item.get('bodySchemaRef')
        if body_ref != expected_ref:
            problems.append('command bodySchemaRef drift: ' + name)
        if isinstance(body_ref, str) and body_ref.count('#') == 1:
            doc_path, pointer = body_ref.split('#', 1)
            if doc_path == PROTOCOL_PATH:
                schema_document = protocol
            elif doc_path == FSM_PATH:
                schema_document = fsm
            else:
                schema_document = None
            if schema_document is None:
                problems.append('body schema ref document drift: ' + name)
            else:
                target = _resolve_pointer(schema_document, pointer)
                if target is None:
                    problems.append('body schema ref does not resolve: ' + name)
                elif not (isinstance(target, dict)
                          and target.get('type') == 'object'):
                    problems.append(
                        'body schema ref is not an object schema: ' + name)
        else:
            problems.append('body schema ref does not resolve: ' + name)

        steps = item.get('journeySteps')
        if not isinstance(steps, list) or not all(
                isinstance(step, str) and step for step in steps):
            problems.append('journey steps malformed: ' + str(name))
            steps = []
        if len(steps) != len(set(steps)):
            problems.append('duplicate journey step reference: ' + str(name))
        expected_status = 'MOCK_EVIDENCE' if steps else 'BOOTSTRAP_SCHEMA_BOUND'
        if status in COMMAND_STATUSES and status != expected_status:
            problems.append(
                'command status does not match journey evidence: ' + str(name))
    return expected


def _check_journey(record, artefacts, items, problems):
    journey = record.get('journey')
    if not isinstance(journey, dict):
        problems.append('journey block is missing')
        return {}
    _extras(problems, 'journey', journey, JOURNEY_KEYS)
    if journey.get('fixturePath') != JOURNEY_PATH:
        problems.append('journey fixture path drift')
    data = artefacts.get(JOURNEY_PATH)
    if data is None:
        problems.append('journey fixture bytes are missing')
        return {}
    if sha256_bytes(data) != journey.get('fixtureSha256'):
        problems.append('journey fixture digest drift')
    try:
        fixture = _json(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        problems.append('journey fixture is unreadable')
        return {}
    steps = fixture.get('steps')
    if not isinstance(steps, list):
        problems.append('journey fixture steps are malformed')
        return {}
    step_action = {}
    for step in steps:
        if not isinstance(step, dict):
            problems.append('journey fixture step is not an object')
            continue
        step_id = step.get('id')
        action = step.get('action')
        if not isinstance(step_id, str) or not step_id:
            problems.append('journey fixture step id is missing')
            continue
        if step_id in step_action:
            problems.append('duplicate journey step id: ' + step_id)
        step_action[step_id] = action
    if journey.get('fixtureVersion') != fixture.get('fixture_version'):
        problems.append('journey fixture version drift')
    if journey.get('stepCount') != len(steps):
        problems.append('journey step count drift: recorded=%r derived=%d'
                        % (journey.get('stepCount'), len(steps)))
    actions = {action for action in step_action.values()}
    if journey.get('uniqueActionCount') != len(actions):
        problems.append('journey action count drift: recorded=%r derived=%d'
                        % (journey.get('uniqueActionCount'), len(actions)))

    referenced = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        steps_list = item.get('journeySteps')
        if not isinstance(steps_list, list):
            continue
        for step_id in steps_list:
            if step_id not in step_action:
                problems.append('unknown journey step: %s (%s)'
                                % (step_id, name))
                continue
            referenced.append(step_id)
            if step_action[step_id] != name:
                problems.append('journey step action mismatch: %s (%r vs %r)'
                                % (step_id, step_action[step_id], name))
    if len(referenced) != len(set(referenced)):
        problems.append('journey step referenced more than once')
    missing = sorted(set(step_action) - set(referenced))
    for step_id in missing:
        problems.append('journey step not referenced: ' + step_id)
    return step_action


def _check_reads(record, catalogue, read_manifest, artefacts, producer, problems):
    read_queries = record.get('readQueries')
    if not isinstance(read_queries, dict):
        problems.append('read queries are missing')
        return []
    _extras(problems, 'readQueries', read_queries, READ_QUERIES_KEYS)
    items = read_queries.get('items')
    if not isinstance(items, list):
        problems.append('read query items are not a list')
        items = []
    manifest_queries = read_manifest.get('queries') or {}
    manifest_files = read_manifest.get('files') or {}
    if read_queries.get('count') != len(items):
        problems.append('read query count drift')
    if read_queries.get('count') != READ_COUNT:
        problems.append('read query count is not 13')
    if read_queries.get('source') != READ_QUERIES_PATH:
        problems.append('read query source drift')
    recorded = [item.get('name') for item in items if isinstance(item, dict)]
    if len(recorded) != len(set(recorded)):
        problems.append('duplicate read query entry')
    for name in manifest_queries:
        if name not in recorded:
            problems.append('missing read query: ' + name)
    producer_reads = {
        item.get('name'): item
        for item in ((producer or {}).get('read_queries') or {}).get('items') or []
        if isinstance(item, dict)
    }
    for item in items:
        if not isinstance(item, dict):
            problems.append('read query item is not an object')
            continue
        _extras(problems, 'read query %s' % item.get('name'), item,
                READ_ITEM_KEYS)
        status_fields = _status_fields(item)
        if not status_fields:
            problems.append('read query status missing: ' + str(item.get('name')))
        elif status_fields != ['status']:
            problems.append('multiple status fields for read query: '
                            + str(item.get('name')))
        name = item.get('name')
        if name not in manifest_queries:
            problems.append('unknown read query: ' + str(name))
            continue
        if item.get('status') != 'NOT_BOUND':
            problems.append('read query is not NOT_BOUND: ' + str(name))
        if item.get('kind') != manifest_queries[name]:
            problems.append('read query kind drift: ' + str(name))
        if item.get('reason') != 'read-model-reference not merged':
            problems.append('read query reason drift: ' + str(name))
        if name in catalogue.names:
            problems.append('read query appears in catalogue: ' + str(name))
        candidate = item.get('candidateVector')
        if not isinstance(candidate, str) or not candidate.startswith(
                READ_VECTOR_DIR + '/'):
            problems.append('read query candidate vector drift: ' + str(name))
            continue
        basename = candidate.rsplit('/', 1)[-1]
        expected_sha = (manifest_files.get(basename) or {}).get('sha256')
        if expected_sha is None:
            problems.append('read query candidate vector drift: ' + str(name))
            continue
        if item.get('fixtureSha256') != expected_sha:
            problems.append('read query fixture digest drift: ' + str(name))
        data = artefacts.get(candidate)
        if data is None:
            problems.append('read query candidate vector missing: ' + str(name))
        elif sha256_bytes(data) != expected_sha:
            problems.append('read query candidate vector bytes drift: '
                            + str(name))
        producer_item = producer_reads.get(name) or {}
        for field in ('kind', 'candidateVector', 'fixtureSha256'):
            if item.get(field) != producer_item.get(field):
                problems.append('read query producer mismatch: %s (%s)'
                                % (field, name))
    return recorded


def _check_profile(record, artefacts, manifest, problems):
    profile = record.get('profile')
    if not isinstance(profile, dict):
        problems.append('profile block is missing')
        return
    _extras(problems, 'profile', profile, PROFILE_KEYS)
    data = artefacts.get(PROFILE_PATH)
    if data is None:
        problems.append('profile bytes are missing')
        return
    try:
        pinned = _json(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        problems.append('profile is unreadable')
        return
    if profile.get('manifestSchemaVersion') != pinned.get(
            'manifest_schema_version'):
        problems.append('profile manifest schema version drift')
    if profile.get('manifestSchemaVersion') != manifest.get(
            'manifest_schema_version'):
        problems.append('profile manifest schema version disagrees with manifest')
    if profile.get('profileKind') != pinned.get('profile_kind'):
        problems.append('profile kind drift')
    if profile.get('profileKind') != 'BOOTSTRAP':
        problems.append('profile kind is not BOOTSTRAP')
    if profile.get('profileRevision') != pinned.get('profile_revision'):
        problems.append('profile revision drift')
    if profile.get('profileRevision') != 'bootstrap-2':
        problems.append('profile revision is not bootstrap-2')
    if profile.get('grants') != pinned.get('grants'):
        problems.append('profile grants drift')
    if profile.get('grants') != 'catalogue-schema-binding only':
        problems.append('profile grants are not catalogue-schema-binding only')
    if profile.get('semanticConsumerStatus') != 'HOLD_SEMANTIC':
        problems.append('semantic consumer status is not HOLD_SEMANTIC')
    if profile.get('bootstrapIsConsumerAcceptance') is not False:
        problems.append('bootstrapIsConsumerAcceptance is not false')


def _check_surfaces(record, problems):
    surfaces = record.get('surfaces')
    if not isinstance(surfaces, dict):
        problems.append('surfaces block is missing')
        return
    _extras(problems, 'surfaces', surfaces, SURFACES_KEYS)
    if surfaces.get('contractOnlyOpenApi') != CONTRACT_ONLY_PATH:
        problems.append('contract-only OpenAPI surface drift')
    if surfaces.get('integrationGateOpenApi') != GATE_PATH:
        problems.append('integration-gate OpenAPI surface drift')
    if surfaces.get('gateRoute') != GATE_ROUTE:
        problems.append('surface gate route drift')
    envelope = surfaces.get('envelope')
    if not isinstance(envelope, dict):
        problems.append('surface envelope is missing')
        return
    _extras(problems, 'surface envelope', envelope, ENVELOPE_KEYS)
    for key in sorted(ENVELOPE_KEYS):
        if not isinstance(envelope.get(key), str) or not envelope[key]:
            problems.append('surface envelope field missing: ' + key)


def _check_external_and_sd1(record, problems):
    external = record.get('externalConsumerExpectations')
    if not isinstance(external, dict):
        problems.append('external consumer expectations are missing')
    else:
        _extras(problems, 'externalConsumerExpectations', external,
                EXTERNAL_KEYS)
        if external.get('consumer') != 'kix-commerce-apps':
            problems.append('external consumer name drift')
        if external.get('status') != 'UNVERIFIED':
            problems.append('external consumer expectations are not UNVERIFIED')
        if not isinstance(external.get('reason'), str) or not external['reason']:
            problems.append('external consumer reason is missing')

    sd1 = record.get('sd1')
    if not isinstance(sd1, dict):
        problems.append('SD1 block is missing')
        return
    _extras(problems, 'sd1', sd1, SD1_KEYS)
    if sd1.get('id') != 'SD1':
        problems.append('SD1 id drift')
    if sd1.get('owner') != 'User':
        problems.append('SD1 owner is not User')
    if sd1.get('userOwned') is not True:
        problems.append('SD1 is not marked userOwned')
    if sd1.get('status') != 'OPEN':
        problems.append('SD1 status is not OPEN')
    if sd1.get('resolved') is not False:
        problems.append('SD1 is marked resolved')
    if sd1.get('contract') != COMPAT_CONTRACT_PATH:
        problems.append('SD1 contract path drift')
    if sd1.get('record') != SD1_RECORD_PATH:
        problems.append('SD1 record path drift')
    if not isinstance(sd1.get('decision'), str) or not sd1['decision']:
        problems.append('SD1 decision statement is missing')
    for key in SD1_FORBIDDEN_KEYS:
        if key in sd1:
            problems.append('SD1 records a forbidden resolution field: ' + key)


def _scan_claims(value, path, problems):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_CLAIM_KEYS:
                problems.append('forbidden semantic claim key: %s.%s'
                                % (path, key))
            _scan_claims(child, path + '.' + str(key), problems)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_claims(child, '%s[%d]' % (path, index), problems)


def _check_non_claims(record, problems):
    non_claims = record.get('nonClaims')
    if not isinstance(non_claims, list) or not all(
            isinstance(claim, str) and claim for claim in non_claims):
        problems.append('nonClaims is not a list of strings')
        return
    for claim in REQUIRED_NON_CLAIMS:
        if claim not in non_claims:
            problems.append('missing non-claim: ' + claim)


def _catalogue_cross_check(record, artefacts, catalogue, by_id, problems):
    protocol = by_id.get('protocol_contract_json') or {}
    fsm = by_id.get('fsm_command_contract') or {}
    data = artefacts.get(PROTOCOL_PATH)
    fsm_data = artefacts.get(FSM_PATH)
    if data is not None:
        if catalogue.sha256 != sha256_bytes(data):
            problems.append('catalogue source digest cross-check drift')
        if catalogue.git_blob != git_blob_id(data):
            problems.append('catalogue source gitBlob cross-check drift')
        if catalogue.sha256 != protocol.get('sha256'):
            problems.append('catalogue source digest disagrees with pin')
        if catalogue.git_blob != protocol.get('gitBlob'):
            problems.append('catalogue source gitBlob disagrees with pin')
    if fsm_data is not None:
        if catalogue.fsm_sha256 != sha256_bytes(fsm_data):
            problems.append('catalogue fsm digest cross-check drift')
        if catalogue.fsm_git_blob != git_blob_id(fsm_data):
            problems.append('catalogue fsm gitBlob cross-check drift')
        if catalogue.fsm_sha256 != fsm.get('sha256'):
            problems.append('catalogue fsm digest disagrees with pin')
        if catalogue.fsm_git_blob != fsm.get('gitBlob'):
            problems.append('catalogue fsm gitBlob disagrees with pin')


def _load_json_artefact(artefacts, path, label, problems):
    data = artefacts.get(path)
    if data is None:
        problems.append(label + ' bytes are missing')
        return None
    try:
        return _json(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        problems.append(label + ' is unreadable')
        return None


def validate(record, artefacts, catalogue):
    """Return every recorded-identity problem; empty means the index passes."""
    problems = []
    if not isinstance(record, dict):
        return ['record is not an object']
    _extras(problems, 'record', record, TOP_LEVEL_KEYS)
    if record.get('record_schema_version') != SCHEMA_VERSION:
        problems.append('record schema version drift')
    if record.get('record_kind') != RECORD_KIND:
        problems.append('record kind drift')
    if record.get('normative') is not False:
        problems.append('record must declare normative false')
    if record.get('record_date') != RECORD_DATE:
        problems.append('record date drift')
    if list(record.get('status_enum') or []) != list(STATUS_ENUM):
        problems.append('status enum drift')
    definitions = record.get('status_definitions')
    _extras(problems, 'status_definitions', definitions or {}, set(STATUS_ENUM))
    if isinstance(definitions, dict):
        for status in STATUS_ENUM:
            if not isinstance(definitions.get(status), str) \
                    or not definitions[status]:
                problems.append('status definition missing: ' + status)

    basis = record.get('basis')
    if not isinstance(basis, dict):
        problems.append('basis block is missing')
    else:
        _extras(problems, 'basis', basis, BASIS_KEYS)
        for key in ('observed_origin_main', 'base_commit'):
            if not _is_hex(basis.get(key), 40):
                problems.append('basis commit malformed: ' + key)
        if basis.get('task') != 'plan-commerce-consumer-binding-index':
            problems.append('basis task drift')
        if basis.get('dependencies') != DEPENDENCIES:
            problems.append('basis dependencies drift')
        if not isinstance(basis.get('note'), str) or not basis['note']:
            problems.append('basis note is missing')

    by_id = _pin_index(record, problems)
    _check_pins(record, artefacts, by_id, problems)

    protocol = _load_json_artefact(artefacts, PROTOCOL_PATH,
                                   'protocol contract', problems)
    fsm = _load_json_artefact(artefacts, FSM_PATH, 'fsm command contract',
                              problems)
    manifest = _load_json_artefact(artefacts, MANIFEST_PATH, 'compatibility manifest',
                                   problems)
    read_manifest = _load_json_artefact(artefacts, READ_MANIFEST_PATH,
                                        'read-model manifest', problems)
    if protocol is None or fsm is None or manifest is None \
            or read_manifest is None:
        return problems

    expected_names = _check_commands(record, catalogue, protocol, fsm,
                                     _producer_for(record, artefacts, problems),
                                     problems)
    producer = _producer_for(record, artefacts, problems)
    read_items = record.get('readQueries') or {}
    read_names = [
        item.get('name')
        for item in (read_items.get('items') or [])
        if isinstance(item, dict)
    ]
    _check_producer(record, artefacts, by_id, expected_names, read_names,
                    problems)
    commands = record.get('commands') or {}
    items = commands.get('items') if isinstance(commands, dict) else []
    _check_journey(record, artefacts, items if isinstance(items, list) else [],
                   problems)
    _check_reads(record, catalogue, read_manifest, artefacts, producer, problems)
    _check_profile(record, artefacts, manifest, problems)
    _check_surfaces(record, problems)
    _check_external_and_sd1(record, problems)
    _check_non_claims(record, problems)
    _scan_claims(record, 'record', problems)
    _catalogue_cross_check(record, artefacts, catalogue, by_id, problems)
    return problems


def _producer_for(record, artefacts, problems):
    data = artefacts.get(PRODUCER_PATH)
    if data is None:
        return None
    try:
        return _json(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def self_test():
    root = ROOT
    try:
        record, _ = load_record(root)
        artefacts = load_artefacts(record, root)
        catalogue = load_catalogue(root)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print('self-test: cannot read inputs: %s' % exc, file=sys.stderr)
        return 1
    problems = validate(record, artefacts, catalogue)
    if problems:
        print('self-test: unmodified record failed validation', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1

    def missing_command(mutated):
        removed = mutated['commands']['items'].pop()
        mutated['commands']['count'] -= 1
        if removed.get('source') == 'core':
            mutated['commands']['coreCount'] -= 1
        else:
            mutated['commands']['fsmCount'] -= 1

    def unknown_command(mutated):
        mutated['commands']['items'][0]['name'] = 'selftest_unknown_command'

    def drifted_digest(mutated):
        for entry in mutated['pins']:
            if entry['id'] == 'journey_fixture':
                entry['sha256'] = '0' * 64
                break

    def read_upgraded(mutated):
        mutated['readQueries']['items'][0]['status'] = 'BOOTSTRAP_SCHEMA_BOUND'

    def broken_journey_reference(mutated):
        for item in mutated['commands']['items']:
            if item.get('journeySteps'):
                item['journeySteps'].append('selftest-missing-step')
                break

    def journey_action_mismatch(mutated):
        for item in mutated['commands']['items']:
            if item['name'] == 'reservation_hold':
                item['journeySteps'][0] = 'register-show'
                break

    def multiple_status(mutated):
        mutated['commands']['items'][0]['statuses'] = ['BOOTSTRAP_SCHEMA_BOUND']

    def absent_status(mutated):
        del mutated['commands']['items'][0]['status']

    def unresolved_schema_pointer(mutated):
        mutated['commands']['items'][0]['bodySchemaRef'] = (
            PROTOCOL_PATH + '#/commands/selftest_missing')

    def semantic_claim(mutated):
        mutated['profile']['semanticConsumerStatus'] = 'SEMANTIC_CONFORMANCE'

    controls = (
        ('missing command', missing_command, 'missing command:'),
        ('unknown command', unknown_command,
         'unknown command: selftest_unknown_command'),
        ('drifted artifact digest', drifted_digest,
         'pin sha256 drift: journey_fixture'),
        ('read query upgraded from NOT_BOUND', read_upgraded,
         'read query is not NOT_BOUND'),
        ('broken journey reference', broken_journey_reference,
         'unknown journey step: selftest-missing-step'),
        ('journey action mismatch', journey_action_mismatch,
         'journey step action mismatch: register-show'),
        ('multiple status fields', multiple_status,
         'multiple status fields for command'),
        ('absent status field', absent_status, 'command status missing:'),
        ('unresolved body-schema pointer', unresolved_schema_pointer,
         'body schema ref does not resolve:'),
        ('injected semantic claim', semantic_claim,
         'semantic consumer status is not HOLD_SEMANTIC'),
    )
    for label, mutate, marker in controls:
        mutated = copy.deepcopy(record)
        mutate(mutated)
        found = validate(mutated, artefacts, catalogue)
        if not any(marker in problem for problem in found):
            print('self-test: %s was accepted' % label, file=sys.stderr)
            for problem in found:
                print('- ' + problem, file=sys.stderr)
            return 1
        print('self-test: detected ' + label)
    print('self-test: pass (%d negative controls)' % len(controls))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_consumer_binding_index.py [--self-test]',
              file=sys.stderr)
        return 2
    if argv:
        return self_test()
    try:
        record, _ = load_record(ROOT)
        artefacts = load_artefacts(record, ROOT)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print('consumer binding index check failed:', file=sys.stderr)
        print('- cannot read record/artefacts: %s' % exc, file=sys.stderr)
        return 1
    try:
        catalogue = load_catalogue(ROOT)
    except Exception as exc:  # noqa: BLE001 - refuse closed on helper error
        print('consumer binding index check failed:', file=sys.stderr)
        print('- catalogue refused: ' + type(exc).__name__, file=sys.stderr)
        return 1
    problems = validate(record, artefacts, catalogue)
    if problems:
        print('consumer binding index check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    commands = record['commands']
    mock = sum(1 for item in commands['items']
               if item.get('status') == 'MOCK_EVIDENCE')
    bootstrap = sum(1 for item in commands['items']
                    if item.get('status') == 'BOOTSTRAP_SCHEMA_BOUND')
    journey = record['journey']
    print('consumer binding index ok: commands=%d core=%d fsm=%d '
          'mock=%d bootstrap=%d reads=%d not_bound=%d journey_steps=%d '
          'journey_actions=%d'
          % (commands['count'], commands['coreCount'], commands['fsmCount'],
             mock, bootstrap, record['readQueries']['count'],
             record['readQueries']['count'], journey['stepCount'],
             journey['uniqueActionCount']))
    print('non-normative navigation only; BOOTSTRAP is not consumer acceptance')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
