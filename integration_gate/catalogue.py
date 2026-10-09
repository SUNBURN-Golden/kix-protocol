"""Load the published core contract and the additive FSM catalogue."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from integration_gate.constants import FSM_COMMAND_COUNT, FSM_CONTRACT, PROTOCOL_CONTRACT
from integration_gate.fsm_contract import drift_problems
from integration_gate.schema import unsupported_schema

ROOT = Path(__file__).resolve().parents[1]


class CatalogueError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class Catalogue:
    def __init__(self, contract, source_bytes, fsm, fsm_bytes):
        self.contract = contract
        self.fsm = fsm
        self.core_commands = contract['commands']
        self.core_names = list(self.core_commands)
        self.fsm_commands = {
            name: spec['schema'] for name, spec in fsm['commands'].items()
        }
        self.fsm_names = list(self.fsm_commands)
        self.fsm_name_set = set(self.fsm_names)
        self.commands = {}
        self.commands.update(self.core_commands)
        self.commands.update(self.fsm_commands)
        self.names = self.core_names + self.fsm_names
        self.domain = contract['domain']
        self.fsm_domain = fsm['domain']
        self.source_bytes = source_bytes
        self.fsm_bytes = fsm_bytes
        self.sha256 = hashlib.sha256(source_bytes).hexdigest()
        self.git_blob = git_blob_id(source_bytes)
        self.fsm_sha256 = hashlib.sha256(fsm_bytes).hexdigest()
        self.fsm_git_blob = git_blob_id(fsm_bytes)


def git_blob_id(data):
    header = b'blob ' + str(len(data)).encode('ascii') + b'\0'
    return hashlib.sha1(header + data).hexdigest()


def _reject_names(commands):
    for name, schema in commands.items():
        if not isinstance(name, str) or not name.isidentifier() or not name.islower():
            raise CatalogueError('REFUSING_CONTRACT')
        if unsupported_schema(schema, name):
            raise CatalogueError('REFUSING_CONTRACT')


def load_catalogue(root=None):
    root = Path(root) if root is not None else ROOT
    path = root / PROTOCOL_CONTRACT
    fsm_path = root / FSM_CONTRACT
    try:
        source_bytes = path.read_bytes()
        contract = json.loads(source_bytes)
        fsm_bytes = fsm_path.read_bytes()
        fsm = json.loads(fsm_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogueError('REFUSING_CONTRACT') from exc
    commands = contract.get('commands')
    if not isinstance(commands, dict) or not commands:
        raise CatalogueError('REFUSING_CONTRACT')
    if contract.get('unknownFields') != 'REJECT':
        raise CatalogueError('REFUSING_CONTRACT')
    if contract.get('sourceAuthentication') != 'FIXTURE_ONLY':
        raise CatalogueError('REFUSING_CONTRACT')
    if not isinstance(contract.get('domain'), str) or not contract['domain']:
        raise CatalogueError('REFUSING_CONTRACT')
    _reject_names(commands)
    if drift_problems(fsm):
        raise CatalogueError('REFUSING_CONTRACT')
    fsm_commands = fsm.get('commands')
    if not isinstance(fsm_commands, dict) or len(fsm_commands) != FSM_COMMAND_COUNT:
        raise CatalogueError('REFUSING_CONTRACT')
    schemas = {name: spec.get('schema') for name, spec in fsm_commands.items()}
    if set(schemas) & set(commands):
        raise CatalogueError('REFUSING_CONTRACT')
    _reject_names(schemas)
    return Catalogue(contract, source_bytes, fsm, fsm_bytes)


def reference_types():
    """Import the in-memory reference core. No live adapter is imported."""
    root = str(ROOT / 'reference' / 'v0.3-rc1')
    if root not in sys.path:
        sys.path.insert(0, root)
    from common import Rejected
    from core import Core
    return Core, Rejected
