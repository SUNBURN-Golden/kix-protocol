"""§0 source and contract-only catalog checks for the offline mock."""

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MOCK_SOURCE = Path(__file__).with_name("ai_delegation_mock.py")
IMPORTS = {"__future__", "hashlib", "json"}
ATTRIBUTES = {("hashlib", "sha256"), ("json", "dumps"), ("json", "loads")}
BUILTINS = {"open", "exec", "eval", "compile", "__import__", "getattr", "setattr", "globals", "input", "breakpoint"}
METHODS = {"write", "write_text", "write_bytes", "sign", "send", "sendall", "connect", "urlopen", "Popen", "system", "run", "request", "remove"}


def scan(source):
    """Return AST violations, including aliases and from-imports; never execute source."""
    tree = ast.parse(source)
    violations, modules = [], {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules[alias.asname or alias.name] = alias.name
                if alias.name not in IMPORTS:
                    violations.append("import " + alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module not in IMPORTS:
                violations.append("from " + (node.module or ""))
            for alias in node.names:
                if node.module == "__future__" and alias.name == "annotations" and not node.level:
                    continue
                if (node.module, alias.name) not in ATTRIBUTES:
                    violations.append("imported attribute " + (node.module or "") + "." + alias.name)
    allowed_module_uses = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if (modules.get(node.value.id), node.attr) in ATTRIBUTES:
                allowed_module_uses.add(node.value)
        if isinstance(node, ast.Attribute) and node.attr in METHODS:
            violations.append(f"forbidden attribute {node.attr} at line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in BUILTINS:
                violations.append(f"forbidden builtin {node.id} at line {node.lineno}")
            if node.id in modules and node not in allowed_module_uses:
                violations.append(f"unapproved module use {node.id} at line {node.lineno}")
    return violations


class MockStaticInertnessTests(unittest.TestCase):
    def test_mock_source_has_no_io_network_process_or_signing_call(self):
        """§0, DLG-11 DLG-31: closed imports/calls exclude direct I/O, signing and execution clients."""
        source = MOCK_SOURCE.read_text(encoding="utf-8")
        self.assertEqual(scan(source), [])

    def test_scanner_detects_each_forbidden_form(self):
        """DLG-11 DLG-31: in-memory negative controls exercise all closed-list rules."""
        snippets = ["import " + module for module in (
            "socket", "http", "urllib", "requests", "subprocess", "os", "shutil", "pathlib", "io",
            "tempfile", "ssl", "asyncio", "ctypes", "multiprocessing", "importlib", "hmac", "cryptography")]
        snippets += ['from os import remove', 'from . import json', 'from json import load',
                     'open("x", "w")', 'opener = open; opener("x", "w")',
                     '__import__("http")', 'f.write_text("")',
                     'import hashlib; hashlib.new("x")', 'import json as j; j.load(f)',
                     'import json; serializer = json; serializer.dump({}, f)',
                     'from hashlib import new as digest; digest("x")']
        snippets += [name + "()" for name in BUILTINS]
        snippets += ["obj." + name + "()" for name in METHODS]
        for source in snippets:
            with self.subTest(source=source):
                self.assertTrue(scan(source))

    def test_scanner_accepts_allowed_import_aliases(self):
        """Closed allowlist controls permit only the mock's hash/JSON facilities."""
        self.assertEqual(scan('from __future__ import annotations\nimport hashlib as h\n'
                              'import json as j\nh.sha256(b"x")\nj.loads(j.dumps({}))'), [])
        self.assertEqual(scan('from hashlib import sha256 as digest\ndigest(b"x")'), [])

    def test_mock_names_are_absent_from_protocol_command_catalogs(self):
        """§0 (DLG-10, DLG-12): mock tools and APIs are absent from both command catalogs."""
        tree = ast.parse(MOCK_SOURCE.read_text(encoding="utf-8"))
        tables = {target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
                  for target in node.targets if isinstance(target, ast.Name)}
        allowlist = tables["ALLOWLIST"]
        self.assertIsInstance(allowlist, ast.Call)
        mock_names = set(ast.literal_eval(allowlist.args[0]))
        mock_names.update(ast.literal_eval(tables["DENYLIST"]))
        mock_class = next(node for node in tree.body
                          if isinstance(node, ast.ClassDef) and node.name == "AiDelegationMock")
        mock_names.update(node.name for node in mock_class.body
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and not node.name.startswith("_"))
        contract_path = ROOT / "reference/v0.3-rc1/protocol_contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        openapi_path = ROOT / "docs/contracts/openapi/kix-protocol.contract-only.openapi.json"
        openapi = json.loads(openapi_path.read_text(encoding="utf-8"))
        operation_ids = {item["operationId"] for item in openapi["x-kix-local-call-operations"]}
        for path, path_item in openapi["paths"].items():
            operation_ids.update(path.split("/"))
            operation_ids.update(operation["operationId"] for operation in path_item.values()
                                 if isinstance(operation, dict) and "operationId" in operation)
        self.assertEqual(mock_names.intersection(contract["commands"]), set())
        self.assertEqual(mock_names.intersection(operation_ids), set())


if __name__ == "__main__":
    unittest.main()
