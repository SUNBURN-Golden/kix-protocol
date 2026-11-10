#!/usr/bin/env python3
"""Recompute the non-normative BOOTSTRAP producer-qualification tuple identity.

The record at ``docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json`` pins the
current contract-only OpenAPI document, its FSM command contract, the
integration-gate OpenAPI document, the generated SDK catalogue, the generator,
the toolchain, the BOOTSTRAP profile/manifest/sidecar, both conformance
vectors and the candidate read-model fixtures. It also maps every command to
its core or FSM source and gate route, marks the 13 owner-decided read query
names NOT_BOUND and keeps semantic SDK consumption on HOLD.

This checker asserts identity only. It never qualifies a surface, chooses a
verifier order, publishes a read query or resolves SD1. Standard library only;
the released ``integration_gate.catalogue`` helper is reused for the command
set and Git-blob formula. Wired into the ``Stdlib offline document checks``
step of ``.github/workflows/protocol.yml``.

Exit status is 0 when every recorded digest and structural pin matches, 1
otherwise. ``--self-test`` mutates in-memory copies and requires the checker to
detect a mutated blob digest, a missing command and a mismatched gate source
pin.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration_gate.catalogue import git_blob_id, load_catalogue

RECORD_PATH = 'docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json'
SCHEMA_VERSION = 'kix-producer-qualification-tuple/1'
RECORD_KIND = 'NON_NORMATIVE_PRODUCER_QUALIFICATION'
STATUS_ENUM = ('BOOTSTRAP_SCHEMA_BOUND', 'HOLD_SEMANTIC', 'NOT_BOUND')
LOCAL_CALL_PATH = '/x-kix-contract-only/local-call'

PROTOCOL_PATH = 'reference/v0.3-rc1/protocol_contract.json'
FSM_PATH = 'docs/contracts/openapi/fsm-command-contract.json'
CONTRACT_ONLY_PATH = 'docs/contracts/openapi/kix-protocol.contract-only.openapi.json'
GATE_PATH = 'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json'
CATALOGUE_PATH = 'sdk/generated/catalogue.ts'
GENERATOR_PATH = 'sdk/generate/generate_client.mjs'
TOOLCHAINS_PATH = 'toolchains.json'
PROFILE_PATH = 'sdk/compat/profiles/bootstrap-2.profile.json'
MANIFEST_PATH = 'sdk/compat/manifests/manifest.bootstrap-2.json'
SIDECAR_PATH = 'sdk/compat/manifests/manifest.bootstrap-2.json.sha256'
READ_MANIFEST_PATH = 'reference/read_model/vectors/manifest.json'
READ_QUERIES_SOURCE = 'docs/contracts/READ_MODEL_QUERIES.md'
SD1_RECORD = 'docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md'
SD1_CONTRACT = 'docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md'

READ_FIXTURES = (
    'reference/read_model/vectors/reservation.json',
    'reference/read_model/vectors/resale.json',
    'reference/read_model/vectors/admission.json',
    'reference/read_model/vectors/settlement.json',
    'reference/read_model/vectors/credit.json',
)

REQUIRED_ARTIFACT_IDS = {
    'contract_only_openapi',
    'fsm_command_contract',
    'integration_gate_openapi',
    'protocol_contract_json',
    'generated_sdk_catalogue',
    'sdk_generator',
    'toolchains',
    'compat_profile',
    'compat_manifest',
    'manifest_sidecar',
    'sdk_conformance_canonical',
    'sdk_conformance_mixed',
    'read_model_vector_manifest',
    'read_model_reservation',
    'read_model_resale',
    'read_model_admission',
    'read_model_settlement',
    'read_model_credit',
}

REQUIRED_NON_CLAIMS = (
    'This record is non-normative identity evidence only.',
    'No semantic qualification is made.',
    'No N/N-1 qualification is made.',
    'No production qualification is made.',
    'No audit approval or User approval is made.',
    'No read query is published or bound.',
    'No SD1 resolution, waiver or verifier order is chosen.',
    'The integration gate is not qualified as production.',
)

SD1_FORBIDDEN_KEYS = (
    'selected_option',
    'option',
    'options',
    'waiver',
    'verifier_order',
    'resolution',
    'resolved',
)


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


def load_artifacts(record, root=ROOT):
    """Return ``{path: bytes}`` for every recorded artifact path."""
    root = Path(root)
    loaded = {}
    for entry in record.get('artifacts') or []:
        path = entry.get('path')
        if not isinstance(path, str):
            continue
        try:
            loaded[path] = (root / path).read_bytes()
        except OSError:
            continue
    return loaded


def present_paths(root=ROOT):
    """Recorded non-artifact paths that the record cites for existence."""
    root = Path(root)
    return {
        path for path in (SD1_RECORD, SD1_CONTRACT, READ_QUERIES_SOURCE)
        if (root / path).is_file()
    }


def _artifact_index(records, problems):
    by_id = {}
    by_path = {}
    for entry in records:
        if not isinstance(entry, dict):
            problems.append('artifact entry is not an object')
            continue
        artifact_id = entry.get('id')
        path = entry.get('path')
        if not isinstance(artifact_id, str) or not artifact_id:
            problems.append('artifact id missing')
            continue
        if artifact_id in by_id:
            problems.append('duplicate artifact id: ' + artifact_id)
        if not isinstance(path, str) or not path:
            problems.append('artifact path missing: ' + artifact_id)
            continue
        if path in by_path:
            problems.append('duplicate artifact path: ' + path)
        by_id[artifact_id] = entry
        by_path[path] = entry
        if not isinstance(entry.get('role'), str) or not entry['role']:
            problems.append('artifact role missing: ' + artifact_id)
        if not _is_hex(entry.get('sha256'), 64):
            problems.append('artifact sha256 malformed: ' + artifact_id)
        if 'gitBlob' in entry and not _is_hex(entry.get('gitBlob'), 40):
            problems.append('artifact gitBlob malformed: ' + artifact_id)
    return by_id, by_path


def _check_artifact_digests(records, artifacts, problems):
    for entry in records:
        if not isinstance(entry, dict):
            continue
        artifact_id = entry.get('id')
        path = entry.get('path')
        if not isinstance(path, str):
            continue
        data = artifacts.get(path)
        if data is None:
            problems.append('missing artifact bytes: %s (%s)' % (artifact_id, path))
            continue
        if sha256_bytes(data) != entry.get('sha256'):
            problems.append('sha256 drift: %s (%s)' % (artifact_id, path))
        if 'gitBlob' in entry and git_blob_id(data) != entry.get('gitBlob'):
            problems.append('gitBlob drift: %s (%s)' % (artifact_id, path))


def _check_openapi(contract_only, gate, source_bytes, fsm_bytes, names, problems):
    source_sha = sha256_bytes(source_bytes)
    source_blob = git_blob_id(source_bytes)
    fsm_sha = sha256_bytes(fsm_bytes)
    fsm_blob = git_blob_id(fsm_bytes)

    def need(condition, message):
        if not condition:
            problems.append(message)

    need(contract_only.get('openapi') == '3.1.0', 'contract-only OpenAPI version drift')
    need(contract_only.get('x-kix-contract-status') == 'contract-only',
         'contract-only status drift')
    need(contract_only.get('x-kix-live-http-server') is False,
         'contract-only live-server flag drift')
    need(contract_only.get('x-kix-production-endpoint') is False,
         'contract-only production-endpoint flag drift')
    need(contract_only.get('x-kix-omitted-commands') == [],
         'contract-only omitted-command list drift')
    source = contract_only.get('x-kix-source') or {}
    need(source.get('path') == PROTOCOL_PATH, 'contract-only pin mismatch: source path')
    need(source.get('sha256') == source_sha, 'contract-only pin mismatch: source sha256')
    need(source.get('gitBlob') == source_blob, 'contract-only pin mismatch: source gitBlob')
    need(source.get('commandCount') == len(names),
         'contract-only pin mismatch: commandCount')
    need(source.get('coreCommandCount') == 40,
         'contract-only pin mismatch: coreCommandCount')
    fsm_source = source.get('fsmSource') or {}
    need(fsm_source.get('path') == FSM_PATH, 'contract-only pin mismatch: fsm path')
    need(fsm_source.get('sha256') == fsm_sha, 'contract-only pin mismatch: fsm sha256')
    need(fsm_source.get('gitBlob') == fsm_blob, 'contract-only pin mismatch: fsm gitBlob')
    need(fsm_source.get('commandCount') == 44,
         'contract-only pin mismatch: fsm commandCount')
    contract_ops = [item.get('operationId')
                    for item in contract_only.get('x-kix-local-call-operations') or []]
    need(contract_ops == names, 'contract-only operation set drift')
    need(list(contract_only.get('paths') or {}) == [LOCAL_CALL_PATH],
         'contract-only path set drift')

    need(gate.get('openapi') == '3.1.0', 'integration-gate OpenAPI version drift')
    need(gate.get('x-kix-contract-status') == 'integration-gate',
         'integration-gate status drift')
    need(gate.get('x-kix-production-endpoint') is False,
         'integration-gate production-endpoint flag drift')
    need(gate.get('x-kix-public-host') is False,
         'integration-gate public-host flag drift')
    need(gate.get('x-kix-protocol-truth') is False,
         'integration-gate protocol-truth flag drift')
    need(gate.get('x-kix-production-conformance') is False,
         'integration-gate production-conformance flag drift')
    live = gate.get('x-kix-live-http-server') or {}
    need(live.get('production') is False, 'integration-gate live production flag drift')
    need(live.get('publicHost') is False, 'integration-gate live public-host flag drift')
    need(live.get('loopbackOnly') is True, 'integration-gate loopback flag drift')
    need(gate.get('x-kix-omitted-commands') == [],
         'integration-gate omitted-command list drift')
    gate_source = gate.get('x-kix-source') or {}
    need(gate_source.get('protocolContract') == PROTOCOL_PATH,
         'gate pin mismatch: source path')
    need(gate_source.get('sha256') == source_sha, 'gate pin mismatch: source sha256')
    need(gate_source.get('gitBlob') == source_blob, 'gate pin mismatch: source gitBlob')
    need(gate_source.get('commandCount') == len(names),
         'gate pin mismatch: commandCount')
    need(gate_source.get('coreCommandCount') == 40,
         'gate pin mismatch: coreCommandCount')
    need(gate_source.get('fsmCommandCount') == 44,
         'gate pin mismatch: fsmCommandCount')
    gate_fsm = gate_source.get('fsmSource') or {}
    need(gate_fsm.get('path') == FSM_PATH, 'gate pin mismatch: fsm path')
    need(gate_fsm.get('sha256') == fsm_sha, 'gate pin mismatch: fsm sha256')
    need(gate_fsm.get('gitBlob') == fsm_blob, 'gate pin mismatch: fsm gitBlob')
    need(gate_fsm.get('commandCount') == 44, 'gate pin mismatch: fsm commandCount')
    gate_ops = [item.get('operationId')
                for item in gate.get('x-kix-local-call-operations') or []]
    need(gate_ops == names, 'integration-gate operation set drift')
    need(list(gate.get('paths') or {}) == [LOCAL_CALL_PATH],
         'integration-gate path set drift')
    for item in gate.get('x-kix-local-call-operations') or []:
        need(item.get('x-kix-production-endpoint') is False,
             'integration-gate operation claims a production endpoint')


def _check_commands(record, contract, fsm, problems):
    commands = record.get('commands') or {}
    core_names = list(contract.get('commands') or {})
    fsm_names = list(fsm.get('commands') or {})
    expected = core_names + fsm_names
    items = commands.get('items')
    if not isinstance(items, list):
        problems.append('command items are not a list')
        items = []
    if commands.get('count') != len(expected):
        problems.append('command count drift: recorded=%r derived=%d'
                        % (commands.get('count'), len(expected)))
    if commands.get('coreCount') != len(core_names):
        problems.append('core command count drift: recorded=%r derived=%d'
                        % (commands.get('coreCount'), len(core_names)))
    if commands.get('fsmCount') != len(fsm_names):
        problems.append('fsm command count drift: recorded=%r derived=%d'
                        % (commands.get('fsmCount'), len(fsm_names)))
    recorded = [item.get('name') if isinstance(item, dict) else None for item in items]
    if recorded != expected:
        for name in expected:
            if name not in recorded:
                problems.append('missing command: ' + name)
        for name in recorded:
            if name not in expected:
                problems.append('unexpected command: ' + str(name))
        if recorded != expected and set(recorded) == set(expected):
            problems.append('command order drift')

    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        if name not in expected:
            continue
        if item.get('status') not in STATUS_ENUM or item.get('status') is None:
            problems.append('command status malformed: ' + str(name))
        if item.get('status') != 'BOOTSTRAP_SCHEMA_BOUND':
            problems.append('command is not BOOTSTRAP_SCHEMA_BOUND: ' + str(name))
        if item.get('gateRoute') != LOCAL_CALL_PATH:
            problems.append('command gate route drift: ' + str(name))
        source = item.get('source')
        if name in core_names:
            if source != 'core':
                problems.append('command source drift: ' + str(name))
            if item.get('sourcePath') != PROTOCOL_PATH:
                problems.append('command source path drift: ' + str(name))
            if item.get('gateDispatch') != 'Core.execute':
                problems.append('command gate dispatch drift: ' + str(name))
            if 'machine' in item or 'op' in item:
                problems.append('core command carries FSM fields: ' + str(name))
        else:
            spec = fsm['commands'][name]
            machine = spec['machine']
            expected_source = fsm['machines'][machine]['module']
            expected_dispatch = 'in-process ' + fsm['machines'][machine]['class']
            if source != 'fsm':
                problems.append('command source drift: ' + str(name))
            if item.get('sourcePath') != expected_source:
                problems.append('command source path drift: ' + str(name))
            if item.get('machine') != machine:
                problems.append('command machine drift: ' + str(name))
            if item.get('op') != spec['op']:
                problems.append('command op drift: ' + str(name))
            if item.get('gateDispatch') != expected_dispatch:
                problems.append('command gate dispatch drift: ' + str(name))
    return expected


def _check_fsm(record, fsm, fsm_bytes, expected_names, problems):
    fsm_record = record.get('fsm') or {}
    if fsm_record.get('path') != FSM_PATH:
        problems.append('fsm path drift')
    if fsm_record.get('sha256') != sha256_bytes(fsm_bytes):
        problems.append('fsm sha256 drift')
    if fsm_record.get('gitBlob') != git_blob_id(fsm_bytes):
        problems.append('fsm gitBlob drift')
    machines = list(fsm.get('machines') or {})
    if fsm_record.get('machineCount') != len(machines):
        problems.append('fsm machine count drift')
    actions = fsm_record.get('actions')
    if not isinstance(actions, list):
        problems.append('fsm actions are not a list')
        actions = []
    if fsm_record.get('actionCount') != len(expected_names):
        problems.append('fsm action count drift: recorded=%r derived=%d'
                        % (fsm_record.get('actionCount'), len(expected_names)))
    if [action.get('name') for action in actions if isinstance(action, dict)] != expected_names:
        problems.append('fsm action set or order drift')
    derived_counts = {}
    for name in expected_names:
        spec = fsm['commands'][name]
        derived_counts[spec['machine']] = derived_counts.get(spec['machine'], 0) + 1
    if fsm_record.get('machineCounts') != derived_counts:
        problems.append('fsm machine counts drift')
    for action in actions:
        if not isinstance(action, dict):
            continue
        name = action.get('name')
        if name not in fsm['commands']:
            problems.append('unexpected fsm action: ' + str(name))
            continue
        spec = fsm['commands'][name]
        machine = spec['machine']
        if action.get('machine') != machine:
            problems.append('fsm action machine drift: ' + str(name))
        if action.get('op') != spec['op']:
            problems.append('fsm action op drift: ' + str(name))
        if action.get('module') != fsm['machines'][machine]['module']:
            problems.append('fsm action module drift: ' + str(name))
        if action.get('status') != 'BOOTSTRAP_SCHEMA_BOUND':
            problems.append('fsm action is not BOOTSTRAP_SCHEMA_BOUND: ' + str(name))


def _check_manifest(record, artifacts, manifest, profile, toolchains, read_manifest,
                    by_id, problems):
    def need(condition, message):
        if not condition:
            problems.append(message)

    basis = record.get('basis') or {}
    required = (
        PROTOCOL_PATH, FSM_PATH, CONTRACT_ONLY_PATH, GATE_PATH, GENERATOR_PATH,
        CATALOGUE_PATH, PROFILE_PATH, MANIFEST_PATH, SIDECAR_PATH, TOOLCHAINS_PATH,
        'sdk/conformance/vectors/canonical-encoding.vectors.json',
        'sdk/conformance/vectors/mixed-input.vectors.json',
    )
    missing = [path for path in required if path not in artifacts]
    if missing:
        problems.append('manifest cross-check cannot read artefacts: ' + ', '.join(missing))
        return
    source_bytes = artifacts[PROTOCOL_PATH]
    fsm_bytes = artifacts[FSM_PATH]
    contract = manifest.get('contract') or {}
    contract_only = contract.get('contract_only') or {}
    gate = contract.get('integration_gate') or {}
    need(contract_only.get('path') == CONTRACT_ONLY_PATH,
         'manifest mismatch: contract_only path')
    need(contract_only.get('sha256') == sha256_bytes(artifacts[CONTRACT_ONLY_PATH]),
         'manifest mismatch: contract_only sha256')
    need(contract_only.get('gitBlob') == git_blob_id(artifacts[CONTRACT_ONLY_PATH]),
         'manifest mismatch: contract_only gitBlob')
    need(gate.get('path') == GATE_PATH, 'manifest mismatch: integration_gate path')
    need(gate.get('sha256') == sha256_bytes(artifacts[GATE_PATH]),
         'manifest mismatch: integration_gate sha256')
    need(gate.get('gitBlob') == git_blob_id(artifacts[GATE_PATH]),
         'manifest mismatch: integration_gate gitBlob')
    generator = manifest.get('generator') or {}
    need(generator.get('path') == GENERATOR_PATH, 'manifest mismatch: generator path')
    need(generator.get('sha256') == sha256_bytes(artifacts[GENERATOR_PATH]),
         'manifest mismatch: generator sha256')
    need(generator.get('toolchain') == 'node-%s' % toolchains.get('nodeMajor'),
         'manifest mismatch: generator toolchain')
    sdk_output = manifest.get('sdk_output') or {}
    need(sdk_output.get('path') == CATALOGUE_PATH, 'manifest mismatch: sdk_output path')
    need(sdk_output.get('sha256') == sha256_bytes(artifacts[CATALOGUE_PATH]),
         'manifest mismatch: sdk_output sha256')
    need(manifest.get('profile_sha256') == sha256_bytes(artifacts[PROFILE_PATH]),
         'manifest mismatch: profile_sha256')
    references = manifest.get('source_references') or {}
    extension = references.get('extension_profile') or {}
    need(extension.get('path') == FSM_PATH, 'manifest mismatch: extension path')
    need(extension.get('sha256') == sha256_bytes(fsm_bytes),
         'manifest mismatch: extension sha256')
    need(extension.get('gitBlob') == git_blob_id(fsm_bytes),
         'manifest mismatch: extension gitBlob')
    need(references.get('fixture_profile') == PROTOCOL_PATH,
         'manifest mismatch: fixture_profile path')
    producer = manifest.get('producer') or {}
    need(producer.get('source_commit') == basis.get('catalogue_input_commit'),
         'manifest mismatch: producer source_commit')
    need(producer.get('source_tree') == basis.get('catalogue_input_tree'),
         'manifest mismatch: producer source_tree')
    vectors = manifest.get('vectors') or []
    vector_by_path = {item.get('path'): item.get('sha256') for item in vectors
                      if isinstance(item, dict)}
    for path in ('sdk/conformance/vectors/canonical-encoding.vectors.json',
                 'sdk/conformance/vectors/mixed-input.vectors.json'):
        need(vector_by_path.get(path) == sha256_bytes(artifacts[path]),
             'manifest mismatch: vector ' + path)
    sidecar = artifacts[SIDECAR_PATH].decode('ascii').strip()
    need(sidecar == sha256_bytes(artifacts[MANIFEST_PATH]),
         'manifest mismatch: sidecar content')

    need(profile.get('profile_kind') == 'BOOTSTRAP', 'profile mismatch: profile_kind')
    need(profile.get('profile_revision') == 'bootstrap-2',
         'profile mismatch: profile_revision')
    need(profile.get('manifest_schema_version') == manifest.get('manifest_schema_version'),
         'profile mismatch: manifest_schema_version')
    need(profile.get('grants') == 'catalogue-schema-binding only',
         'profile mismatch: grants')
    catalogue = profile.get('catalogue') or {}
    need(catalogue.get('openapi_path') == CONTRACT_ONLY_PATH,
         'profile mismatch: catalogue openapi path')
    need(catalogue.get('openapi_sha256') == sha256_bytes(artifacts[CONTRACT_ONLY_PATH]),
         'profile mismatch: catalogue openapi sha256')

    need(toolchains.get('nodeMajor') == basis.get('toolchain', {}).get('nodeMajor'),
         'toolchain mismatch: nodeMajor')
    need(toolchains.get('pythonMinor') == basis.get('toolchain', {}).get('pythonMinor'),
         'toolchain mismatch: pythonMinor')
    need(toolchains.get('nodeMajor') == 24, 'toolchain mismatch: nodeMajor is not 24')
    need(toolchains.get('pythonMinor') == '3.12',
         'toolchain mismatch: pythonMinor is not 3.12')
    need(read_manifest.get('fixture_mode') == 'REFERENCE_IN_MEMORY',
         'read-model manifest mismatch: fixture_mode')
    need(str(read_manifest.get('status', '')).startswith('CANDIDATE_FIXTURES'),
         'read-model manifest mismatch: status')
    need('not conformance evidence' in str(read_manifest.get('status', '')),
         'read-model manifest mismatch: conformance non-claim')

    for artifact_id in REQUIRED_ARTIFACT_IDS:
        if artifact_id not in by_id:
            problems.append('missing artifact id: ' + artifact_id)


def _check_read_queries(record, artifacts, read_manifest, expected_catalogue, present,
                        problems):
    read_queries = record.get('read_queries') or {}
    items = read_queries.get('items')
    if not isinstance(items, list):
        problems.append('read query items are not a list')
        items = []
    if read_queries.get('count') != len(items):
        problems.append('read query count drift')
    if read_queries.get('count') != 13:
        problems.append('read query count is not 13')
    if read_queries.get('source') != READ_QUERIES_SOURCE:
        problems.append('read query source drift')
    if READ_QUERIES_SOURCE not in present:
        problems.append('read query source does not exist')
    if read_queries.get('candidateVectorManifest') != READ_MANIFEST_PATH:
        problems.append('read query candidate manifest drift')
    if read_queries.get('implementationStatus') != 'read-model-reference not merged':
        problems.append('read query implementation status drift')
    manifest_queries = read_manifest.get('queries') or {}
    manifest_files = read_manifest.get('files') or {}
    recorded_names = [item.get('name') for item in items if isinstance(item, dict)]
    if len(recorded_names) != len(set(recorded_names)):
        problems.append('duplicate read query name')
    if set(recorded_names) != set(manifest_queries):
        problems.append('read query name set drift')
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get('name')
        if name not in manifest_queries:
            problems.append('unexpected read query: ' + str(name))
            continue
        if item.get('status') != 'NOT_BOUND':
            problems.append('read query is not NOT_BOUND: ' + str(name))
        if item.get('kind') != manifest_queries[name]:
            problems.append('read query kind drift: ' + str(name))
        if item.get('reason') != 'read-model-reference not merged':
            problems.append('read query reason drift: ' + str(name))
        candidate = item.get('candidateVector')
        if candidate not in READ_FIXTURES:
            problems.append('read query candidate vector drift: ' + str(name))
            continue
        expected_sha = (manifest_files.get(Path(candidate).name) or {}).get('sha256')
        if item.get('fixtureSha256') != expected_sha:
            problems.append('read query fixture digest drift: ' + str(name))
        data = artifacts.get(candidate)
        if data is None:
            problems.append('read query candidate vector missing: ' + str(name))
        elif sha256_bytes(data) != expected_sha:
            problems.append('read query candidate vector bytes drift: ' + str(name))
        if name in expected_catalogue:
            problems.append('read query appears in catalogue: ' + str(name))
    for path in READ_FIXTURES:
        if path not in artifacts:
            problems.append('read fixture not pinned: ' + path)


def _check_surfaces(record, by_id, problems):
    surfaces = record.get('surfaces')
    if not isinstance(surfaces, list) or not surfaces:
        problems.append('surfaces are missing')
        return {}
    by_surface = {}
    for surface in surfaces:
        if not isinstance(surface, dict):
            problems.append('surface entry is not an object')
            continue
        surface_id = surface.get('id')
        if not isinstance(surface_id, str) or not surface_id:
            problems.append('surface id missing')
            continue
        if surface_id in by_surface:
            problems.append('duplicate surface id: ' + surface_id)
        by_surface[surface_id] = surface
        status = surface.get('status')
        if status not in STATUS_ENUM:
            problems.append('surface status malformed: ' + surface_id)
        if not isinstance(surface.get('basis'), str) or not surface['basis']:
            problems.append('surface basis missing: ' + surface_id)
        artifact_ids = surface.get('artifact_ids')
        if not isinstance(artifact_ids, list):
            problems.append('surface artifact ids missing: ' + surface_id)
            continue
        for artifact_id in artifact_ids:
            if artifact_id not in by_id:
                problems.append('surface cites unknown artifact: %s: %s'
                                % (surface_id, artifact_id))
    statuses = {surface.get('status') for surface in by_surface.values()}
    if statuses != set(STATUS_ENUM):
        problems.append('surface status coverage drift')
    for surface_id, surface in by_surface.items():
        if surface_id in ('read_query_surface', 'semantic_sdk_consumer'):
            continue
        if surface.get('status') != 'BOOTSTRAP_SCHEMA_BOUND':
            problems.append('unexpected non-bootstrap surface: ' + surface_id)
    if (by_surface.get('read_query_surface') or {}).get('status') != 'NOT_BOUND':
        problems.append('read_query_surface is not NOT_BOUND')
    if (by_surface.get('semantic_sdk_consumer') or {}).get('status') != 'HOLD_SEMANTIC':
        problems.append('semantic_sdk_consumer is not HOLD_SEMANTIC')
    return by_surface


def _check_semantic_and_sd1(record, profile, present, by_surface, problems):
    semantic = record.get('semantic_hold') or {}
    if semantic.get('status') != 'HOLD_SEMANTIC':
        problems.append('semantic hold status is not HOLD_SEMANTIC')
    if semantic.get('grants') != 'catalogue-schema-binding only':
        problems.append('semantic hold grants drift')
    if semantic.get('grants') != profile.get('grants'):
        problems.append('semantic hold grants disagree with profile')
    if semantic.get('surface') != 'semantic_sdk_consumer':
        problems.append('semantic hold surface drift')
    if (by_surface.get('semantic_sdk_consumer') or {}).get('status') != 'HOLD_SEMANTIC':
        problems.append('semantic hold is not reflected by a surface')
    if semantic.get('profileKind') != profile.get('profile_kind'):
        problems.append('semantic hold profile kind drift')
    if semantic.get('profileRevision') != profile.get('profile_revision'):
        problems.append('semantic hold profile revision drift')

    sd1 = record.get('sd1') or {}
    if sd1.get('id') != 'SD1':
        problems.append('SD1 id drift')
    if sd1.get('owner') != 'User':
        problems.append('SD1 owner is not User')
    if sd1.get('status') != 'OPEN':
        problems.append('SD1 status is not OPEN')
    if sd1.get('record') != SD1_RECORD:
        problems.append('SD1 record path drift')
    if sd1.get('contract') != SD1_CONTRACT:
        problems.append('SD1 contract path drift')
    if sd1.get('record') not in present:
        problems.append('SD1 record does not exist')
    if sd1.get('contract') not in present:
        problems.append('SD1 contract does not exist')
    for key in SD1_FORBIDDEN_KEYS:
        if key in sd1:
            problems.append('SD1 records a forbidden resolution field: ' + key)


def validate(record, artifacts, present):
    """Return identity problems for the supplied record and artifact bytes.

    ``artifacts`` maps recorded path -> bytes; ``present`` is the set of
    recorded non-artifact paths that exist. No file I/O happens here.
    """
    problems = []
    if record.get('record_schema_version') != SCHEMA_VERSION:
        problems.append('record schema version drift')
    if record.get('record_kind') != RECORD_KIND:
        problems.append('record kind drift')
    if record.get('normative') is not False:
        problems.append('record must declare normative false')
    if list(record.get('status_enum') or []) != list(STATUS_ENUM):
        problems.append('status enum drift')
    definitions = record.get('status_definitions') or {}
    if set(definitions) != set(STATUS_ENUM):
        problems.append('status definitions drift')
    for status in STATUS_ENUM:
        if not isinstance(definitions.get(status), str) or not definitions[status]:
            problems.append('status definition missing: ' + status)

    basis = record.get('basis') or {}
    for key in ('observed_origin_main', 'base_commit', 'catalogue_input_commit',
                'catalogue_input_tree'):
        if not _is_hex(basis.get(key), 40):
            problems.append('basis commit malformed: ' + key)
    if basis.get('observed_origin_main') != basis.get('base_commit'):
        problems.append('basis observed main and base commit differ')
    toolchain = basis.get('toolchain') or {}
    if not isinstance(toolchain.get('nodeMajor'), int):
        problems.append('basis toolchain nodeMajor malformed')
    if not isinstance(toolchain.get('pythonMinor'), str):
        problems.append('basis toolchain pythonMinor malformed')

    records = record.get('artifacts')
    if not isinstance(records, list) or not records:
        problems.append('artifacts are missing')
        records = []
    by_id, _ = _artifact_index(records, problems)
    _check_artifact_digests(records, artifacts, problems)

    try:
        contract = _json(artifacts[PROTOCOL_PATH])
        fsm = _json(artifacts[FSM_PATH])
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        problems.append('pinned catalogue is unreadable: ' + type(exc).__name__)
        return problems

    expected_names = _check_commands(record, contract, fsm, problems)
    _check_fsm(record, fsm, artifacts[FSM_PATH], list(fsm.get('commands') or {}), problems)

    try:
        contract_only = _json(artifacts[CONTRACT_ONLY_PATH])
        gate = _json(artifacts[GATE_PATH])
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        problems.append('pinned OpenAPI document is unreadable: ' + type(exc).__name__)
        return problems
    _check_openapi(contract_only, gate, artifacts[PROTOCOL_PATH], artifacts[FSM_PATH],
                   expected_names, problems)

    try:
        manifest = _json(artifacts[MANIFEST_PATH])
        profile = _json(artifacts[PROFILE_PATH])
        toolchains = _json(artifacts[TOOLCHAINS_PATH])
        read_manifest = _json(artifacts[READ_MANIFEST_PATH])
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        problems.append('pinned manifest/profile is unreadable: ' + type(exc).__name__)
        return problems
    _check_manifest(record, artifacts, manifest, profile, toolchains, read_manifest,
                    by_id, problems)
    catalogue_names = set(expected_names)
    _check_read_queries(record, artifacts, read_manifest, catalogue_names, present,
                        problems)
    by_surface = _check_surfaces(record, by_id, problems)
    _check_semantic_and_sd1(record, profile, present, by_surface, problems)

    non_claims = record.get('non_claims') or []
    if not isinstance(non_claims, list):
        problems.append('non_claims is not a list')
        non_claims = []
    for claim in REQUIRED_NON_CLAIMS:
        if claim not in non_claims:
            problems.append('missing non-claim: ' + claim)

    if 'sha256' in record:
        problems.append('record must not carry a self-referential digest')
    return problems


def _catalogue_cross_check(record, artifacts):
    """Reuse the released catalogue helper as an independent command-set check."""
    problems = []
    try:
        catalogue = load_catalogue(ROOT)
    except Exception as exc:  # noqa: BLE001 - refuse closed on any helper error
        return ['catalogue refused: ' + type(exc).__name__]
    try:
        contract = _json(artifacts[PROTOCOL_PATH])
        fsm = _json(artifacts[FSM_PATH])
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
        return ['catalogue cross-check cannot read pinned bytes']
    if catalogue.core_names != list(contract.get('commands') or {}):
        problems.append('load_catalogue core command cross-check drift')
    if catalogue.fsm_names != list(fsm.get('commands') or {}):
        problems.append('load_catalogue fsm command cross-check drift')
    if catalogue.sha256 != sha256_bytes(artifacts[PROTOCOL_PATH]):
        problems.append('load_catalogue source digest cross-check drift')
    if catalogue.fsm_sha256 != sha256_bytes(artifacts[FSM_PATH]):
        problems.append('load_catalogue fsm digest cross-check drift')
    return problems


def self_test():
    root = ROOT
    try:
        record, _ = load_record(root)
        artifacts = load_artifacts(record, root)
        present = present_paths(root)
    except (OSError, json.JSONDecodeError) as exc:
        print('self-test: cannot read record: %s' % exc, file=sys.stderr)
        return 1
    problems = validate(record, artifacts, present)
    problems += _catalogue_cross_check(record, artifacts)
    if problems:
        print('self-test: unmodified record failed validation', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1

    mutated = copy.deepcopy(record)
    for entry in mutated.get('artifacts') or []:
        if entry.get('id') == 'contract_only_openapi':
            entry['gitBlob'] = '0' * 40
            break
    else:
        print('self-test: contract-only artifact pin not found', file=sys.stderr)
        return 1
    if not any('gitBlob drift' in item
               for item in validate(mutated, artifacts, present)):
        print('self-test: mutated blob digest was accepted', file=sys.stderr)
        return 1
    print('self-test: detected mutated blob digest')

    mutated = copy.deepcopy(record)
    items = mutated['commands']['items']
    removed = items.pop()
    mutated['commands']['count'] = len(items)
    if removed.get('source') == 'core':
        mutated['commands']['coreCount'] -= 1
    else:
        mutated['commands']['fsmCount'] -= 1
    if not any('missing command' in item
               for item in validate(mutated, artifacts, present)):
        print('self-test: missing command was accepted', file=sys.stderr)
        return 1
    print('self-test: detected missing command')

    gate = json.loads(artifacts[GATE_PATH])
    gate['x-kix-source']['gitBlob'] = '0' * 40
    gate_bytes = (json.dumps(gate, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    mutated_artifacts = dict(artifacts)
    mutated_artifacts[GATE_PATH] = gate_bytes
    mutated = copy.deepcopy(record)
    for entry in mutated.get('artifacts') or []:
        if entry.get('id') == 'integration_gate_openapi':
            entry['sha256'] = sha256_bytes(gate_bytes)
            entry['gitBlob'] = git_blob_id(gate_bytes)
            break
    if not any('gate pin mismatch' in item
               for item in validate(mutated, mutated_artifacts, present)):
        print('self-test: mismatched gate pin was accepted', file=sys.stderr)
        return 1
    print('self-test: detected mismatched gate pin')

    print('self-test: pass')
    return 0


def main(argv):
    if '--self-test' in argv:
        return self_test()
    try:
        record, _ = load_record(ROOT)
        artifacts = load_artifacts(record, ROOT)
    except (OSError, json.JSONDecodeError) as exc:
        print('producer qualification tuple check failed:', file=sys.stderr)
        print('- cannot read record/artifacts: %s' % exc, file=sys.stderr)
        return 1
    problems = validate(record, artifacts, present_paths(ROOT))
    problems += _catalogue_cross_check(record, artifacts)
    if problems:
        print('producer qualification tuple check failed:', file=sys.stderr)
        for item in problems:
            print('- ' + item, file=sys.stderr)
        return 1
    commands = record['commands']
    reads = record['read_queries']
    print('producer qualification tuple identity ok: commands=%d core=%d fsm=%d reads=%d'
          % (commands['count'], commands['coreCount'], commands['fsmCount'], reads['count']))
    print('identity only; no semantic or operational qualification')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
