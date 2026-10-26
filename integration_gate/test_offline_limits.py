"""Offline default/AST evidence; never build or start the integration gate."""
import ast
from pathlib import Path
import re
import socket
import unittest

ROOT = Path(__file__).resolve().parents[1]
_SOCKET_ORIGINALS = {}


class _UnavailableSocket(socket.socket):
    # ssl subclasses socket.socket at import time, so retain a class here.
    def __new__(cls, *args, **kwargs):
        raise OSError('offline test: sockets unavailable')


def _unavailable(*args, **kwargs):
    raise OSError('offline test: sockets unavailable')


def setUpModule():
    # Install before importing the server, so import-time socket use also fails.
    for name in ('socket', 'create_connection', 'socketpair'):
        _SOCKET_ORIGINALS[name] = getattr(socket, name)
        setattr(socket, name, _UnavailableSocket if name == 'socket' else _unavailable)


def tearDownModule():
    for name, original in _SOCKET_ORIGINALS.items():
        setattr(socket, name, original)
    _SOCKET_ORIGINALS.clear()


class OfflineLimitsTests(unittest.TestCase):
    def test_socket_guard_is_active(self):
        for name in _SOCKET_ORIGINALS:
            with self.subTest(name=name):
                with self.assertRaisesRegex(OSError, 'offline test: sockets unavailable'):
                    getattr(socket, name)()

    def test_constants_match_readme_limits(self):
        from integration_gate import constants

        readme = (ROOT / 'docs/contracts/openapi/README.md').read_text(encoding='utf-8')
        matches = re.findall(
            r'본문 상한은 (\d+)바이트, 요청 시간 상한은 (\d+)초, 헤더 상한은 (\d+)바이트',
            readme,
        )
        self.assertEqual(len(matches), 1)
        actual = (constants.MAX_BODY_BYTES, constants.DEFAULT_TIMEOUT_SECONDS,
                  constants.HEADER_LIMIT_BYTES)
        self.assertEqual(actual, (65536, 5.0, 8192))
        self.assertEqual(tuple(map(int, matches[0])), actual)

    def test_server_uses_limit_constants_statically(self):
        tree = ast.parse((ROOT / 'integration_gate/server.py').read_bytes())
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        build = functions['build_server']
        defaults = dict(zip((arg.arg for arg in build.args.args[-len(build.args.defaults):]),
                            build.args.defaults))
        for parameter, constant in (('timeout_seconds', 'DEFAULT_TIMEOUT_SECONDS'),
                                    ('max_body_bytes', 'MAX_BODY_BYTES')):
            self.assertIsInstance(defaults[parameter], ast.Name)
            self.assertEqual(defaults[parameter].id, constant)
            calls = [node for node in ast.walk(functions['parse_args'])
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                     and node.func.attr == 'add_argument' and node.args
                     and isinstance(node.args[0], ast.Constant)
                     and node.args[0].value == '--' + parameter.replace('_', '-')]
            self.assertEqual(len(calls), 1)
            cli_default = next(kw.value for kw in calls[0].keywords if kw.arg == 'default')
            self.assertIsInstance(cli_default, ast.Name)
            self.assertEqual(cli_default.id, constant)

        handler = next(node for node in tree.body
                       if isinstance(node, ast.ClassDef) and node.name == 'GateHandler')
        methods = {node.name: node for node in handler.body if isinstance(node, ast.FunctionDef)}
        header_check = ast.parse('len(self.headers.as_string()) > HEADER_LIMIT_BYTES', mode='eval').body
        self.assertTrue(any(ast.dump(node) == ast.dump(header_check)
                            for node in ast.walk(methods['route'])))
        literals = [node for node in ast.walk(tree) if isinstance(node, ast.Constant)]
        self.assertFalse(any(node.value in (8192, 5.0) for node in literals))
        request_line_literals = [node for node in literals if node.value in (65536, 65537)]
        # Characterization: these separate request-line bounds are not the body limit.
        self.assertCountEqual([node.value for node in request_line_literals], [65536, 65537])
        request_line_nodes = list(ast.walk(methods['handle_one_request']))
        self.assertTrue(all(node in request_line_nodes for node in request_line_literals))

    def test_default_bind_is_loopback_8765_without_binding(self):
        from integration_gate import constants, server

        args = server.parse_args([])
        self.assertEqual(args.host, constants.LOOPBACK_HOST)
        self.assertEqual(args.host, '127.0.0.1')
        self.assertEqual(args.port, 8765)
        readme = (ROOT / 'docs/contracts/openapi/README.md').read_text(encoding='utf-8')
        self.assertIn('기본 바인드는 `127.0.0.1`과 포트 `8765`다.', readme)


if __name__ == '__main__':
    unittest.main()
