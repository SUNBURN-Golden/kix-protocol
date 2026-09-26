"""Load the published 40-command contract. Does not add commands."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from integration_gate.constants import PROTOCOL_CONTRACT
from integration_gate.schema import unsupported_schema

ROOT = Path(__file__).resolve().parents[1]


class CatalogueError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class Catalogue:
    def __init__(self, contract, source_bytes):
        self.contract = contract
        self.commands = contract['commands']
        self.names = list(self.commands)
        self.domain = contract['domain']
        self.source_bytes = source_bytes
        self.sha256 = hashlib.sha256(source_bytes).hexdigest()
        self.git_blob = git_blob_id(source_bytes)


def git_blob_id(data):
    header = b'blob ' + str(len(data)).encode('ascii') + b'\0'
    return hashlib.sha1(header + data).hexdigest()


def load_catalogue(root=None):
    root = Path(root) if root is not None else ROOT
    path = root / PROTOCOL_CONTRACT
    try:
        source_bytes = path.read_bytes()
        contract = json.loads(source_bytes)
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
    for name, schema in commands.items():
        if not isinstance(name, str) or not name.isidentifier() or not name.islower():
            raise CatalogueError('REFUSING_CONTRACT')
        if unsupported_schema(schema, name):
            raise CatalogueError('REFUSING_CONTRACT')
    return Catalogue(contract, source_bytes)


def reference_types():
    """Import the in-memory reference core. No live adapter is imported."""
    root = str(ROOT / 'reference' / 'v0.3-rc1')
    if root not in sys.path:
        sys.path.insert(0, root)
    from common import Rejected
    from core import Core
    return Core, Rejected
