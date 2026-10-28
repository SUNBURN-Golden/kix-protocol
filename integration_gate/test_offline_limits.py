"""Offline default/AST evidence; never build or start the integration gate."""
import ast
from collections import Counter
import hashlib
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


EXPECTED_GATE_OPENAPI_SHA256 = 'd05beb48c234b924af086b886ce9bb524dc34407ad2e4a57f1e8af84255820f6'


class OfflineGapTests(unittest.TestCase):
    def test_gate_openapi_rendered_bytes_are_pinned(self):
        from integration_gate.openapi_doc import build_document, render
        from integration_gate.server import parse_args

        committed = (ROOT / 'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json').read_bytes()
        self.assertTrue(committed.endswith(b'\n'))
        for argv, expected in (([], None),
                               (['--browser-origin', 'http://127.0.0.1:5173'],
                                ['http://127.0.0.1:5173'])):
            with self.subTest(argv=argv):
                self.assertEqual(parse_args(argv).browser_origin, expected)
                rendered = render(build_document(ROOT)).encode('utf-8')
                self.assertEqual(rendered, committed)
                for data in (committed, rendered):
                    self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED_GATE_OPENAPI_SHA256)

    def _assert_transport_isolation(self, server_source, document_source):
        server = ast.parse(server_source)
        document = ast.parse(document_source)

        def functions(tree):
            return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

        def contains(tree, source):
            expected = ast.dump(ast.parse(source).body[0])
            self.assertTrue(any(ast.dump(node) == expected for node in ast.walk(tree)), source)

        funcs = functions(server)
        classes = {node.name: functions(node) for node in server.body if isinstance(node, ast.ClassDef)}
        # Pin every current browser-origin reference's scope, including CLI -> startup
        # -> server attribute -> Host/origin/preflight flow. Extra consumers fail.
        scopes = dict(funcs)
        for cls, methods in classes.items():
            scopes.update({cls + '.' + name: method for name, method in methods.items()})
        references = Counter({name: sum(
            (isinstance(node, ast.Name) and node.id in ('browser_origin', 'browser_origins'))
            or (isinstance(node, ast.Attribute) and node.attr == 'browser_origin')
            for node in ast.walk(scope)) for name, scope in scopes.items()})
        self.assertEqual(+references, Counter({
            'main': 8, 'build_server': 3, 'GateServer.__init__': 2,
            'GateHandler.route': 3, 'GateHandler._preflight': 1,
            '_origin_is_allowed': 2, '_preflight_acceptable': 1,
        }))
        contains(funcs['parse_args'], "parser.add_argument('--browser-origin', action='append')")
        contains(funcs['main'], 'browser_origins = args.browser_origin')
        contains(funcs['main'], 'browser_origin = None if browser_origins is None else browser_origins[0]')
        contains(funcs['build_server'], """if browser_origin is not None and browser_origin != BROWSER_ALLOWED_ORIGIN:
            raise GateStartupError('REFUSING_BROWSER_ORIGIN')""")
        for scope, callee in ((funcs['main'], 'build_server'), (funcs['build_server'], 'GateServer')):
            calls = [node for node in ast.walk(scope) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == callee]
            self.assertEqual(len(calls), 1)
            self.assertEqual([(kw.arg, ast.unparse(kw.value)) for kw in calls[0].keywords
                              if kw.arg == 'browser_origin'], [('browser_origin', 'browser_origin')])
        contains(classes['GateServer']['__init__'], 'self.browser_origin = browser_origin')
        contains(classes['GateHandler']['route'], """if self.server.browser_origin is not None and not _loopback_host_header(
            self.headers, self.server.server_address[1]):
            self._send(400, _error('BAD_REQUEST'))
            return""")
        contains(classes['GateHandler']['route'], """if _origin_is_allowed(self.headers, self.server.browser_origin):
            self._cors = True""")
        contains(classes['GateHandler']['route'], """if method == 'OPTIONS' and self.server.browser_origin is not None:
            if self._preflight(path):
                return
            self._cors = False""")
        contains(classes['GateHandler']['_preflight'], """if not _preflight_acceptable(self.headers, path, self.server.browser_origin):
            return False""")
        contains(classes['GateHandler']['_preflight'], 'self._send(204, None, allow=allow, preflight=True)')
        contains(funcs['_origin_is_allowed'], """if browser_origin is None:
            return False""")
        contains(funcs['_origin_is_allowed'], 'return _one_header(headers, ORIGIN_HEADER) == browser_origin')
        contains(funcs['_preflight_acceptable'], """if not _origin_is_allowed(headers, browser_origin):
            return False""")
        validators = [node for node in ast.walk(server) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Name) and node.func.id == 'validate_gate_document']
        self.assertEqual([ast.unparse(node) for node in validators], ['validate_gate_document(root)'])

        # The document module can import only its existing data/stdlib dependencies.
        for node in ast.walk(document):
            if isinstance(node, ast.Import):
                self.assertTrue(all(alias.name in ('copy', 'json', 'sys') for alias in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                self.assertIn(node.module, ('__future__', 'pathlib',
                                           'integration_gate.catalogue', 'integration_gate.constants'))
                self.assertFalse(any('browser' in alias.name.lower() or alias.name == '*'
                                     for alias in node.names))
        self.assertFalse(any(isinstance(node, ast.Name) and
                             ('browser' in node.id.lower() or node.id in ('server', 'args'))
                             or isinstance(node, ast.Attribute) and
                             ('browser' in node.attr.lower() or node.attr == 'environ')
                             for node in ast.walk(document)))
        doc_funcs = functions(document)
        self.assertEqual(ast.unparse(doc_funcs['build_document'].args), 'root=None')
        self.assertEqual(ast.unparse(doc_funcs['render'].args), 'document')
        for name in ('build_document', 'render'):
            self.assertFalse(any(isinstance(node, ast.Name) and node.id == 'sys'
                                 for node in ast.walk(doc_funcs[name])))

        send = classes['GateHandler']['_send']
        # CORS and preflight branches may append header lines only. Body is derived
        # from status/payload before either branch, then appended unchanged to packet.
        contains(send, """if self._cors:
            lines.append('Access-Control-Allow-Origin: ' + BROWSER_ALLOWED_ORIGIN)
            lines.append('Vary: Origin')""")
        contains(send, """if preflight:
            lines.append('Access-Control-Allow-Methods: ' + allow)
            lines.append('Access-Control-Allow-Headers: ' + ', '.join(BROWSER_ALLOWED_REQUEST_HEADERS))""")
        self.assertEqual(sum(isinstance(node, ast.Attribute) and node.attr == '_cors'
                             for node in ast.walk(send)), 1)
        self.assertEqual(sum(isinstance(node, ast.Name) and node.id == 'preflight'
                             for node in ast.walk(send)), 1)
        # Extra payload reads (including payload.update or item assignment) fail.
        self.assertEqual(sum(isinstance(node, ast.Name) and node.id == 'payload'
                             for node in ast.walk(send)), 4)
        body_branch = next(node for node in send.body if isinstance(node, ast.If)
                           and ast.unparse(node.test) == 'status == 204')
        contains(body_branch, "body = b''")
        contains(body_branch, "body = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')")
        body_writes = [node for node in ast.walk(send) if isinstance(node, ast.Name)
                       and node.id in ('body', 'payload') and isinstance(node.ctx, ast.Store)]
        self.assertEqual(len(body_writes), 2)
        self.assertTrue(all(node in list(ast.walk(body_branch)) for node in body_writes))
        contains(send, "packet = ('\\r\\n'.join(lines) + '\\r\\n\\r\\n').encode('ascii') + body")
        contains(send, 'self.wfile.write(packet)')

    def test_browser_origin_is_transport_only_statically(self):
        server = (ROOT / 'integration_gate/server.py').read_text(encoding='utf-8')
        document = (ROOT / 'integration_gate/openapi_doc.py').read_text(encoding='utf-8')
        self._assert_transport_isolation(server, document)
        for label, bad_server, bad_document in (
            ('document dependency', server,
             document.replace('catalogue = load_catalogue(root)',
                              'catalogue = load_catalogue(args.browser_origin)')),
            ('CORS payload mutation', server.replace(
                "if self._cors:\n            lines.append",
                "if self._cors:\n            payload['cors'] = True\n            lines.append"), document),
        ):
            with self.subTest(label=label):
                self.assertNotEqual((bad_server, bad_document), (server, document))
                with self.assertRaises(AssertionError):
                    self._assert_transport_isolation(bad_server, bad_document)

    def _assert_core_conflict(self, alternate_actor, alternate_action):
        from integration_gate.catalogue import reference_types
        from integration_gate.test_http_gate import POLICY

        Core, Rejected = reference_types()
        core = Core(':memory:')
        self.addCleanup(core.db.close)
        core.execute('event', 'operator', 'create_event', {
            'domain': core.DOMAIN, 'eventId': 'show', 'organizer': 'organizer',
            'policy': dict(POLICY), 'seats': ['A1'],
        })
        body = {'domain': core.DOMAIN, 'eventId': 'show'}
        original = ('close', 'operator', 'close_sales', body)
        receipt = core.execute(*original)
        self.assertEqual(receipt['operationId'], 'close')
        self.assertEqual(receipt['action'], 'close_sales')
        self.assertEqual(receipt['sequence'], 2)
        self.assertIn('result', receipt)
        snapshot = core.snapshot()
        self.assertEqual(core.execute(*original), receipt)
        self.assertEqual(core.snapshot(), snapshot)
        with self.assertRaises(Rejected) as caught:
            core.execute('close', alternate_actor, alternate_action, body)
        self.assertEqual(str(caught.exception), 'OPERATION_ID_CONFLICT')
        self.assertEqual(core.snapshot(), snapshot)
        self.assertEqual(core.execute(*original), receipt)
        self.assertEqual(core.snapshot(), snapshot)
        # The alternate tuple is valid with a fresh identity: no schema/role
        # rejection can masquerade as the fingerprint conflict above.
        control = core.execute('fresh', alternate_actor, alternate_action, body)
        self.assertEqual(control['operationId'], 'fresh')
        self.assertEqual(control['action'], alternate_action)
        self.assertEqual(control['sequence'], receipt['sequence'] + 1)

    def test_core_actor_only_conflict_preserves_receipt(self):
        self._assert_core_conflict('organizer', 'close_sales')

    def test_core_action_only_conflict_preserves_receipt(self):
        self._assert_core_conflict('operator', 'open_admission')

    def test_unprefixed_admission_names_are_not_dispatchable(self):
        from integration_gate.catalogue import load_catalogue
        from integration_gate.fsm_host import FsmHost

        catalogue = load_catalogue(ROOT)
        host = FsmHost()
        for name in ('authorize_admission', 'consume_admission'):
            with self.subTest(excluded=name):
                for surface in (catalogue.commands, catalogue.names,
                                catalogue.fsm_commands, catalogue.fsm_name_set):
                    self.assertNotIn(name, surface)
                # Implementation characterization: lookup fails before body access.
                # This is not an HTTP error contract or a new FsmRejected code.
                with self.assertRaises(KeyError) as caught:
                    host.call(name, {})
                self.assertEqual(caught.exception.args, (name,))
        for name, machine, op in (
            ('admission_consume', 'admission', 'consume'),
            ('reservation_authorize_admission', 'reservation', 'authorize_admission'),
        ):
            with self.subTest(included=name):
                for surface in (catalogue.commands, catalogue.names,
                                catalogue.fsm_commands, catalogue.fsm_name_set):
                    self.assertIn(name, surface)
                spec = catalogue.fsm['commands'][name]
                self.assertEqual((spec['machine'], spec['op']), (machine, op))


if __name__ == '__main__':
    unittest.main()
