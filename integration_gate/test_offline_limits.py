"""Offline gate evidence without starting listeners or workers."""
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import socket
from tempfile import TemporaryDirectory
from threading import Lock
import unittest
from unittest.mock import Mock, patch

from reference.booking_resale_admission import commerce_tuple_assertions as commerce

ROOT = Path(__file__).resolve().parents[1]
COMMERCE_FIXTURES = ROOT / 'reference/booking_resale_admission/fixtures'
COMMERCE_BINDING_INDEX = ROOT / 'docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json'
COMMERCE_VECTORS = ROOT / 'sdk/conformance/vectors'
HISTORICAL_GATE_PINS = {
    'docs/contracts/openapi/kix-protocol.integration-gate.openapi.json':
        'sdk/compat/inputs/integration-gate.bootstrap-2.openapi.json',
    'integration_gate/server.py': 'sdk/compat/inputs/server.commerce-fixture-8ba7f6c-1.py.txt',
}
COMMERCE_REVISION = 'commerce-fixture-8ba7f6c-1'
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


EXPECTED_GATE_OPENAPI_SHA256 = '5f2a72827347799059e1b7ee4b950350016a501e5bb648e39002b5aa4aecb3df'


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
        contains(classes['GateHandler']['route'], """if path not in READ_PATHS and _origin_is_allowed(self.headers, self.server.browser_origin):
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
        contains(funcs['_preflight_acceptable'], """if path in READ_PATHS or not _origin_is_allowed(headers, browser_origin):
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
                                           'integration_gate.catalogue', 'integration_gate.constants',
                                           'integration_gate.read_schema'))
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


class CommerceJourneyEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from integration_gate.catalogue import load_catalogue

        cls.journey = json.loads(
            (COMMERCE_FIXTURES / 'commerce_journey_conformance_v1.json').read_bytes()
        )
        cls.fixture = json.loads(
            (COMMERCE_FIXTURES / 'commerce_journey_envelope_cases_v1.json').read_bytes()
        )
        cls.commands = load_catalogue(ROOT).commands

    def _envelope(self, step):
        return {
            'operationId': self.fixture['operation_id_prefix'] + step['id'],
            'actor': self.fixture['actor'],
            'action': step['action'],
            'body': step['body'],
        }

    def test_every_journey_envelope_is_preserved(self):
        from integration_gate.schema import parse_envelope

        steps = self.journey['steps']
        self.assertEqual(len(steps), 44)
        self.assertEqual(len({step['action'] for step in steps}), 27)
        for step in steps:
            with self.subTest(step=step['id']):
                envelope = self._envelope(step)
                expected = deepcopy(tuple(envelope.values()))
                parsed = parse_envelope(envelope, self.commands)
                self.assertEqual(parsed, expected)
                # JSON comparison also distinguishes booleans from equal-valued integers.
                self.assertEqual(
                    json.dumps(parsed[3], sort_keys=True), json.dumps(expected[3], sort_keys=True)
                )

    def test_shared_faults_are_rejected_by_the_parser(self):
        from integration_gate.schema import EnvelopeError, parse_envelope

        read_queries = json.loads(COMMERCE_BINDING_INDEX.read_bytes())['readQueries']
        count, items = read_queries['count'], read_queries['items']
        self.assertEqual(count, 13)
        self.assertEqual(len(items), count)
        read_names = []
        for item in items:
            self.assertEqual(item['status'], 'NOT_BOUND', item['name'])
            read_names.append(item['name'])
        self.assertEqual(len(set(read_names)), count)
        self.assertCountEqual(read_names, self.journey['final_expect']['read_queries'])

        baseline = self._envelope(next(
            step for step in self.journey['steps'] if step['id'] == self.fixture['base_step']
        ))
        self.assertEqual(baseline['action'], 'reservation_observe_payment')
        mutations = {
            '/body/idempotency_key': 'delete',
            '/body/amount': 'set',
            '/body/unexpected': 'set',
            '/action': 'set',
        }
        self.assertEqual(self.fixture['fixture_version'], 1)
        self.assertCountEqual(
            [case['mutation']['path'] for case in self.fixture['cases']], list(mutations)
        )
        read_case = next(case for case in self.fixture['cases'] if case['mutation']['path'] == '/action')
        self.assertEqual(read_case['id'], 'not-bound-read')
        self.assertEqual(read_case['gate_error'], 'UNKNOWN_ACTION')
        self.assertIsNone(read_case['gate_detail'])
        self.assertIn(read_case['mutation']['value'], read_names)
        cases = [case for case in self.fixture['cases'] if case is not read_case]
        cases.extend({
            **read_case,
            'id': f"{read_case['id']}:{name}",
            'mutation': {**read_case['mutation'], 'value': name},
        } for name in read_names)

        for case in cases:
            with self.subTest(case=case['id']):
                mutation = case['mutation']
                path = mutation['path']
                self.assertEqual(mutation['op'], mutations[path])
                envelope = deepcopy(baseline)
                parent, field = path.rsplit('/', 1)
                target = envelope['body'] if parent == '/body' else envelope
                if mutation['op'] == 'delete':
                    del target[field]
                else:
                    target[field] = mutation['value']
                with self.assertRaises(EnvelopeError) as caught:
                    parse_envelope(envelope, self.commands)
                self.assertEqual(caught.exception.error, case['gate_error'])
                self.assertEqual(caught.exception.detail, case['gate_detail'])

        expected = deepcopy(tuple(baseline.values()))
        parsed = parse_envelope(baseline, self.commands)
        self.assertEqual(parsed, expected)
        self.assertEqual(json.dumps(parsed[3], sort_keys=True), json.dumps(expected[3], sort_keys=True))


class _CommerceDispatchCase(unittest.TestCase):
    def _dispatch_gate(self, store):
        from integration_gate.server import GateServer

        # Initialize the dispatch state on this thread without opening a listener.
        gate = GateServer.__new__(GateServer)
        gate.catalogue = self.catalogue
        gate.store = store
        gate.core = None
        gate._admit_lock = Lock()
        gate._accepting = gate._core_failed = gate._diverged = gate._draining = False
        gate._writes_fenced = False
        gate._ensure_core_on_worker()
        self.addCleanup(gate.core.db.close)
        return gate


class CommerceReadinessTests(_CommerceDispatchCase):
    @classmethod
    def setUpClass(cls):
        from integration_gate.catalogue import load_catalogue

        table_path = ROOT / 'docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json'
        cls.table = json.loads(table_path.read_bytes())
        cls.corpus = json.loads(
            (COMMERCE_VECTORS / 'commerce-fixture-tuple.vectors.json').read_bytes()
        )
        cls.catalogue = load_catalogue(ROOT)

    def _listed_vectors(self):
        self.assertEqual(
            self.table['record_schema_version'], 'kix-commerce-fixture-tuple-conformance/1'
        )
        self.assertEqual(self.corpus['record_schema_version'], 'kix-commerce-fixture-vectors/1')
        by_id = {vector['id']: vector for vector in self.corpus['vectors']}
        self.assertEqual(len(by_id), len(self.corpus['vectors']))

        tuples = self.table['tuples']
        self.assertEqual(len(tuples), 28)
        selected = {}
        for row in sorted(tuples, key=lambda row: row['action']):
            action = row['action']
            control_ids = {
                vector_id for entry in row['contexts'] for vector_id in entry['control_vector_ids']
            }
            vector_id, context, step = min(
                (vector_id, entry['context'], step)
                for entry in row['contexts']
                for step, ids in entry['steps'].items()
                for vector_id in ids
                if vector_id not in control_ids
            )
            vector = by_id[vector_id]
            self.assertEqual(
                (vector['context'], vector['commerce_step'], vector['envelope']['action']),
                (context, step, action), vector_id
            )
            selected[action] = vector
        self.assertEqual(len(selected), 28)
        self.assertEqual(len({vector['id'] for vector in selected.values()}), 28)
        return selected

    def test_all_listed_actions_refused(self):
        from integration_gate.schema import parse_envelope
        from readiness.store import ReadinessStore

        selected = self._listed_vectors()
        directory = self.enterContext(TemporaryDirectory())
        store = ReadinessStore.open(directory)
        self.addCleanup(store.close)
        committed_bytes = store.committed_bytes
        gate = self._dispatch_gate(store)

        cases = []
        with (
            patch.object(gate.fsm, 'call', wraps=gate.fsm.call) as fsm_call,
            patch.object(store, 'append', wraps=store.append) as append,
        ):
            for action, vector in selected.items():
                vector_id = vector['id']
                with self.subTest(action=action, vector_id=vector_id):
                    envelope = vector['envelope']
                    expected = deepcopy(tuple(
                        envelope[field] for field in ('operationId', 'actor', 'action', 'body')
                    ))
                    parsed = parse_envelope(envelope, self.catalogue.commands)
                    self.assertEqual(json.dumps(parsed, sort_keys=True),
                                     json.dumps(expected, sort_keys=True))
                    self.assertIn(action, self.catalogue.fsm_name_set)
                    status, payload, observation = gate.perform(*parsed)
                    self.assertEqual(status, 422)
                    self.assertEqual(payload['error'], 'READINESS_FSM_REFUSED')
                    self.assertIs(payload['rejected'], True)
                    self.assertEqual(observation['journalDecision'], 'not_attempted')
                    fsm_call.assert_not_called()
                    append.assert_not_called()
                    self.assertEqual(store.records, [])
                    self.assertEqual(store.committed_bytes, committed_bytes)
                    cases.append(dict(action=action, vector_id=vector_id,
                                      status=status, payload=payload))

        record = json.loads((COMMERCE_VECTORS / 'commerce-readiness-refusals.vectors.json').read_bytes())
        self.assertEqual(record, {'profile_revision': COMMERCE_REVISION, 'cases': cases})

    def test_listed_clock_without_readiness(self):
        from integration_gate.schema import parse_envelope

        vector = self._listed_vectors()['reservation_set_clock']
        self.assertEqual(vector['id'], 'booking-admission/reservation-clock')
        self.assertEqual(vector['setup'], [])
        receipts = json.loads((COMMERCE_FIXTURES / 'commerce_journey_receipts_v1.json').read_bytes())
        expected = receipts['steps'][0]['receipt']
        gate = self._dispatch_gate(store=None)

        parsed = parse_envelope(vector['envelope'], self.catalogue.commands)
        expected_body = deepcopy(vector['envelope']['body'])
        with patch.object(gate.fsm, 'call', wraps=gate.fsm.call) as fsm_call:
            status, receipt, observation = gate.perform(*parsed)
            fsm_call.assert_called_once_with('reservation_set_clock', expected_body)
        self.assertEqual(status, 200)
        self.assertEqual(observation['journalDecision'], 'inactive')
        self.assertEqual(json.dumps(receipt, sort_keys=True), json.dumps(expected, sort_keys=True))


class CommerceGateDispatchTests(_CommerceDispatchCase):
    # Consumer pin from docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md.
    MANIFEST_SHA256 = '76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f'

    def setUp(self):
        from integration_gate.catalogue import load_catalogue

        table, files, self.schema_digests = self._verified_evidence()
        corpus = json.loads(files[commerce.VECTORS])
        self.assertEqual(corpus['record_schema_version'], 'kix-commerce-fixture-vectors/1')
        self.tuples = table['tuples']
        self.targets, self.controls = self._target_inventory(table, corpus['vectors'])
        self.golden_steps = json.loads(files[commerce.RECEIPTS])['steps']
        self.receipts = self._expected_receipts(files)
        self.catalogue = load_catalogue(ROOT)

    def _verified_evidence(self):
        from integration_gate.catalogue import git_blob_id

        manifest_path = ROOT / f'sdk/compat/manifests/manifest.{COMMERCE_REVISION}.json'
        raw = manifest_path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.MANIFEST_SHA256)
        self.assertEqual(manifest_path.with_suffix('.json.sha256').read_text(encoding='utf-8'),
                         self.MANIFEST_SHA256 + '\n')
        manifest = json.loads(raw)
        self.assertEqual(manifest['manifest_schema_version'], 'kix-compat-manifest/1')
        self.assertEqual(manifest['profile_kind'], 'SEMANTIC_CONFORMANCE')
        self.assertEqual(manifest['profile_revision'], COMMERCE_REVISION)
        profile_raw = (ROOT / f'sdk/compat/profiles/{COMMERCE_REVISION}.profile.json').read_bytes()
        self.assertEqual(hashlib.sha256(profile_raw).hexdigest(), manifest['profile_sha256'])
        profile = json.loads(profile_raw)
        for field in ('manifest_schema_version', 'profile_kind', 'profile_revision', 'vectors'):
            self.assertEqual(profile[field], manifest[field], field)
        self.assertEqual(profile['grants'],
                         'commerce-fixture-tuples-only: see commerce-fixture-qualification-table')
        self.assertEqual(Counter((ref['name'], ref['path']) for ref in manifest['vectors']), {
            ('commerce-fixture-qualification-table', commerce.TABLE): 1,
            ('commerce-fixture-request-to-receipt', commerce.VECTORS): 1,
            ('commerce-fixture-prior-inputs', commerce.INPUTS): 1,
            ('commerce-fixture-prior-receipts', commerce.RECEIPTS): 1,
        })
        files = {}
        for ref in manifest['vectors']:
            path = ref['path']
            files[path] = (ROOT / path).read_bytes()
            self.assertEqual(hashlib.sha256(files[path]).hexdigest(), ref['sha256'], path)

        table = json.loads(files[commerce.TABLE])
        self.assertEqual(table['record_schema_version'], 'kix-commerce-fixture-tuple-conformance/1')
        self.assertEqual(table['producer'], manifest['producer'])
        for group in ('producer', 'earlier_evidence'):
            for pin in table['pins'][group]:
                path = pin['path']
                # The producer's gate files are pinned by their historical bytes. The
                # current gate is checked by its own tests.
                archived = HISTORICAL_GATE_PINS.get(path, path)
                data = files[path] if path in files else (ROOT / archived).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), pin['sha256'], path)
                self.assertEqual(git_blob_id(data), pin['gitBlob'], path)
        return table, files, profile['catalogue']['schema_digests']

    def _target_inventory(self, table, vectors):
        from integration_gate.constants import LOCAL_CALL_PATH

        by_id = {vector['id']: vector for vector in vectors}
        self.assertEqual(len(by_id), len(vectors), 'duplicate vector ID')
        rows = table['tuples']
        self.assertEqual(len(rows), 28)
        self.assertEqual(len({row['action'] for row in rows}), 28)
        targets = {}
        controls = {}
        for row in rows:
            self.assertEqual((row['method'], row['path']), ('POST', LOCAL_CALL_PATH))
            for context in row['contexts']:
                for vid in context['control_vector_ids']:
                    self.assertNotIn(vid, controls, f'duplicate control vector ID: {vid}')
                    vector = by_id[vid]
                    self.assertEqual(
                        (vector['context'], vector['envelope']['action']),
                        (context['context'], row['action']), vid,
                    )
                    self.assertNotIn('commerce_step', vector, vid)
                    controls[vid] = vector
                for step, ids in context['steps'].items():
                    for vid in ids:
                        self.assertNotIn(vid, targets, 'duplicate listed vector ID')
                        vector = by_id[vid]
                        self.assertEqual(
                            (vector['context'], vector['commerce_step'], vector['envelope']['action']),
                            (context['context'], step, row['action']), vid,
                        )
                        targets[vid] = vector
        self.assertEqual(len(targets), 63)
        self.assertEqual(len(controls), 53)
        self.assertFalse(controls.keys() & targets.keys(), 'control ID listed as a target')
        self.assertEqual(controls.keys() | targets.keys(), by_id.keys())
        return targets, controls

    def _expected_receipts(self, files):
        from integration_gate.catalogue import git_blob_id

        direct = {
            vid: commerce.resolve_receipt_ref(self, vector, self.golden_steps)
            for vid, vector in self.targets.items() if 'receipt_ref' in vector['expected']
        }
        corpus_raw = files[commerce.VECTORS]
        fixture_pin = {
            'path': commerce.VECTORS,
            'sha256': hashlib.sha256(corpus_raw).hexdigest(),
            'gitBlob': git_blob_id(corpus_raw),
        }
        market, booking = (
            json.loads((ROOT / path).read_bytes())
            for path in (commerce.MARKET_RECEIPTS, commerce.BOOKING_BRANCH_RECEIPTS)
        )
        self.assertEqual(market['fixture'], fixture_pin, commerce.MARKET_RECEIPTS)
        self.assertEqual(booking['fixture'], fixture_pin, commerce.BOOKING_BRANCH_RECEIPTS)
        market = market['receipts']
        booking = booking['receipts']
        self.assertEqual((len(direct), len(market), len(booking)), (32, 14, 10))
        self.assertEqual(
            Counter(direct.keys()) + Counter(market.keys()) + Counter(booking.keys()),
            Counter(vid for vid, v in self.targets.items() if v['expected']['kind'] == 'accept'),
            'each first acceptance must have exactly one receipt source',
        )
        return direct | market | booking

    def _expected_outcome(self, vector):
        expected = vector['expected']
        self.assertIn(expected['kind'], {'accept', 'business-reject', 'duplicate'})
        if expected['kind'] == 'accept':
            return 200, self.receipts[vector['id']]
        if expected['kind'] == 'duplicate':
            return 200, commerce.resolve_receipt_ref(self, vector, self.golden_steps)
        return 422, {'error': expected['code'], 'rejected': True}

    def _assert_outcome(self, observed, expected):
        self.assertEqual(
            commerce.canonical(observed), commerce.canonical(expected),
            'Commerce dispatch outcome differs',
        )

    def _parse_and_dispatch(self, gate, vector):
        from integration_gate.schema import parse_envelope

        fixture_envelope = vector['envelope']
        fixture_body = fixture_envelope['body']
        self.assertNotEqual(fixture_envelope['operationId'], fixture_body['idempotency_key'])
        expected_args = commerce.canonical(tuple(
            fixture_envelope[field] for field in ('operationId', 'actor', 'action', 'body')
        ))
        parsed = parse_envelope(deepcopy(fixture_envelope), self.catalogue.commands)
        self.assertEqual(commerce.canonical(parsed), expected_args)
        return gate.perform(*parsed)

    def _assert_unchanged(self, vector, before, after):
        vid = vector['id']
        self.assertEqual(after.keys(), before.keys(), vid)
        for name, (state, journal) in after.items():
            old_state, old_journal = before[name]
            self.assertEqual(commerce.canonical(journal), commerce.canonical(old_journal),
                             f'{vid}: {name} journal')
            self.assertEqual(state, old_state, f'{vid}: {name} state')

    def _check_dispatch(self, gate, vector):
        before = commerce.snapshot(gate.fsm)
        status, payload, observation = self._parse_and_dispatch(gate, vector)
        after = commerce.snapshot(gate.fsm)
        self._assert_outcome((status, payload), self._expected_outcome(vector))
        self.assertEqual(observation['journalDecision'], 'inactive')
        if vector['expected']['kind'] == 'accept':
            envelope = vector['envelope']
            spec = self.catalogue.fsm['commands'][envelope['action']]
            commerce.check_journal(
                self, spec, envelope['body'], before, after, vector['expected']['journal_delta'],
            )
        else:
            self._assert_unchanged(vector, before, after)
        return status, payload

    def _replay_setup(self, target):
        gate = self._dispatch_gate(store=None)
        setup = target['setup']
        outcomes = {}
        for index, vid in enumerate(setup):
            self.assertIn(vid, self.targets, 'setup must refer to a listed vector')
            entry = self.targets[vid]
            self.assertEqual(entry['context'], target['context'], vid)
            self.assertEqual(entry['setup'], setup[:index], vid)
            try:
                outcomes[vid] = deepcopy(self._check_dispatch(gate, entry))
            except AssertionError as error:
                error.add_note(f'Setup vector {vid}, after {setup[:index]}')
                raise
        self.assertEqual(set(gate.fsm.machines), {
            'reservation', 'resale', 'admission', 'settlement', 'credit',
        }, target['id'])
        return gate, outcomes

    def _replay_target(self, target):
        gate, _ = self._replay_setup(target)
        return self._check_dispatch(gate, target)

    def _check_duplicate_consume(self, vector, observed, setup_outcomes):
        self.assertEqual(vector['id'], 'booking-admission/replay-consume-B')
        first_id = 'booking-admission/consume-B'
        refused_id = 'booking-admission/double-consume'
        self.assertEqual(vector['replay_of'], first_id)
        self.assertEqual(vector['setup'][-2:], [first_id, refused_id])
        self._assert_outcome(setup_outcomes[refused_id], (
            422, {'error': 'ALREADY_CONSUMED', 'rejected': True},
        ))
        first = self.targets[first_id]['envelope']
        replay = vector['envelope']
        self.assertNotEqual(first['operationId'], replay['operationId'])
        self.assertEqual(commerce.canonical(replay), commerce.canonical({
            **first, 'operationId': replay['operationId'],
        }))
        self.assertEqual(vector['input_index'], 43)
        _, first_receipt = setup_outcomes[first_id]
        self._assert_outcome(observed, (200, {**first_receipt, 'duplicate': True, 'applied': None}))

    def _check_missing_payment_ref(self, gate, vector):
        from integration_gate.schema import EnvelopeError

        self.assertEqual(vector['id'], 'resale-market/missing-payment-ref')
        self.assertEqual(vector['envelope']['action'], 'resale_observe_resale_payment')
        self.assertNotIn('payment_ref', vector['envelope']['body'])
        with (
            patch.object(gate, 'perform', wraps=gate.perform) as perform,
            patch.object(gate.fsm, 'call', wraps=gate.fsm.call) as fsm_call,
        ):
            before = commerce.snapshot(gate.fsm)
            with self.assertRaises(EnvelopeError) as error:
                self._parse_and_dispatch(gate, vector)
            after = commerce.snapshot(gate.fsm)
            self.assertEqual(error.exception.error, 'SCHEMA_REJECTED')
            self.assertEqual(error.exception.error, vector['expected']['code'])
            perform.assert_not_called()
            fsm_call.assert_not_called()
        self._assert_unchanged(vector, before, after)

    def test_control_outcomes(self):
        executed = Counter()
        counts = Counter()
        for vid, vector in self.controls.items():
            with self.subTest(vector=vid, setup=vector['setup']):
                gate, setup_outcomes = self._replay_setup(vector)
                kind = vector['expected']['kind']
                if kind == 'schema-reject':
                    self._check_missing_payment_ref(gate, vector)
                else:
                    self.assertIn(kind, {'business-reject', 'duplicate'})
                    observed = self._check_dispatch(gate, vector)
                    if kind == 'duplicate':
                        self._check_duplicate_consume(vector, observed, setup_outcomes)
                executed[vid] += 1
                counts[vector['context'], kind] += 1
        self.assertEqual(executed, Counter(self.controls.keys()))
        self.assertEqual(counts, {
            ('booking-resale', 'business-reject'): 17,
            ('booking-admission', 'business-reject'): 9,
            ('booking-admission', 'duplicate'): 1,
            ('booking-refund', 'business-reject'): 12,
            ('resale-market', 'business-reject'): 13,
            ('resale-market', 'schema-reject'): 1,
        })

    def test_listed_outcomes(self):
        counts = Counter()
        for vid, vector in self.targets.items():
            with self.subTest(vector=vid, setup=vector['setup']):
                status, _ = self._replay_target(vector)
                counts[vector['context'], status] += 1
        self.assertEqual(counts, {
            ('booking-resale', 200): 18, ('booking-resale', 422): 4,
            ('booking-admission', 200): 10, ('booking-admission', 422): 2,
            ('booking-refund', 200): 14, ('booking-refund', 422): 1,
            ('resale-market', 200): 14,
        })

    def test_nullable_body_fields(self):
        from integration_gate.schema import ENVELOPE_FIELDS, EnvelopeError

        fixture = json.loads((COMMERCE_VECTORS / 'commerce-nullable-fields.vectors.json').read_bytes())
        self.assertEqual(fixture['profile_revision'], COMMERCE_REVISION)
        cases = fixture['cases']
        present_values = {'null': None, 'string': 'fixture-alternate', 'boolean': True}
        representations = ('omitted', *present_values)
        positions = {}
        for row in self.tuples:
            action = row['action']
            schema = self.catalogue.commands[action]
            digest = hashlib.sha256(commerce.canonical(schema).encode('utf-8')).hexdigest()
            self.assertEqual(digest, row['body_schema_sha256'], action)
            self.assertEqual(digest, self.schema_digests[action], action)
            nullable = []
            for field, spec in schema['properties'].items():
                declared = spec['type']
                types = declared if isinstance(declared, list) else [declared]
                if field not in schema['required'] and 'null' in types:
                    self.assertCountEqual(types, ('string', 'null'), f'{action}.{field}')
                    nullable.append(field)
            if not nullable:
                continue
            vector_id = min(vid for vid, vector in self.targets.items()
                            if vector['envelope']['action'] == action)
            for field in nullable:
                positions[action, field] = vector_id
        self.assertEqual(len(positions), 10)
        self.assertEqual(len({action for action, _ in positions}), 8)
        self.assertCountEqual(
            [(case['action'], case['field'], case['representation']) for case in cases],
            [(action, field, representation) for action, field in positions
             for representation in representations],
        )

        for case in cases:
            action, field = case['action'], case['field']
            representation, envelope = case['representation'], case['envelope']
            with self.subTest(action=action, field=field, representation=representation):
                vector_id = positions[action, field]
                self.assertEqual(case['vector_id'], vector_id)
                expected = deepcopy(self.targets[vector_id]['envelope'])
                self.assertNotEqual(expected['body'].get(field), present_values['string'])
                omitted = representation == 'omitted'
                if omitted:
                    expected['body'].pop(field, None)
                else:
                    expected['body'][field] = present_values[representation]
                self.assertEqual(commerce.canonical(envelope), commerce.canonical(expected))

                gate = Mock(spec=['perform'])
                if representation == 'boolean':
                    with self.assertRaises(EnvelopeError) as caught:
                        self._parse_and_dispatch(gate, case)
                    self.assertEqual(caught.exception.error, 'SCHEMA_REJECTED')
                    self.assertEqual(caught.exception.detail, f'body.{field}: expected string or null')
                    gate.perform.assert_not_called()
                else:
                    self._parse_and_dispatch(gate, case)
                    expected_args = tuple(expected[key] for key in ENVELOPE_FIELDS)
                    gate.perform.assert_called_once_with(*expected_args)
                    args = gate.perform.call_args.args
                    self.assertEqual(field in args[3], not omitted)
                    self.assertEqual(commerce.canonical(args), commerce.canonical(expected_args))

    def test_distribution_order(self):
        from integration_gate.schema import EnvelopeError

        fixture = json.loads(
            (COMMERCE_VECTORS / 'commerce-distribution-order.vectors.json').read_bytes()
        )
        vector_id = 'booking-resale/distribute-resale'
        self.assertEqual(fixture['profile_revision'], COMMERCE_REVISION)
        self.assertEqual(fixture['vector_id'], vector_id)
        self.assertEqual(fixture['cases'], [
            {'id': 'original', 'order': ['organizer-1', 'platform-1']},
            {'id': 'string', 'order': 'organizer-1'},
            {'id': 'duplicate', 'order': ['organizer-1', 'platform-1', 'organizer-1']},
            {'id': 'missing', 'order': ['organizer-1']},
            {'id': 'unknown', 'order': ['organizer-1', 'platform-1', 'unknown-1']},
        ])
        original = self.targets[vector_id]
        commit_id = 'booking-resale/settle-resale-commit'
        self.assertEqual(len(original['setup']), 18)
        self.assertEqual(original['setup'][-3:], [
            'booking-resale/accept-A-before-commit', commit_id, 'booking-resale/accept-A',
        ])
        self.assertEqual(original['expected']['receipt_ref'], f'{commerce.RECEIPTS}#/steps/25/receipt')
        self.assertEqual(original['expected']['journal_delta'], {'settlement': 1})
        refusal_codes = {
            'duplicate': 'DISTRIBUTION_ORDER_DUPLICATE',
            'missing': 'DISTRIBUTION_ORDER_MISMATCH',
            'unknown': 'DISTRIBUTION_ORDER_MISMATCH',
        }

        for case in fixture['cases']:
            case_id = case['id']
            with self.subTest(case=case_id):
                gate, setup_outcomes = self._replay_setup(original)
                status, commit = setup_outcomes[commit_id]
                self.assertEqual(status, 200)
                self.assertEqual(commit['settlement']['phase'], 'COMMITTED')
                self.assertIsNone(commit['settlement']['claim']['distribution_order'])

                vector = deepcopy(original)
                envelope = vector['envelope']
                envelope['body']['order'] = deepcopy(case['order'])
                self.assertEqual(envelope == original['envelope'], case_id == 'original')
                with (
                    patch.object(gate, 'perform', wraps=gate.perform) as perform,
                    patch.object(gate.fsm, 'call', wraps=gate.fsm.call) as fsm_call,
                ):
                    if case_id == 'string':
                        before = commerce.snapshot(gate.fsm)
                        with self.assertRaises(EnvelopeError) as caught:
                            self._parse_and_dispatch(gate, vector)
                        self.assertEqual(caught.exception.error, 'SCHEMA_REJECTED')
                        self.assertEqual(caught.exception.detail, 'body.order: expected array')
                        perform.assert_not_called()
                        fsm_call.assert_not_called()
                        self._assert_unchanged(vector, before, commerce.snapshot(gate.fsm))
                        continue

                    if case_id in refusal_codes:
                        vector['expected'] = {'kind': 'business-reject', 'code': refusal_codes[case_id]}
                    self._check_dispatch(gate, vector)
                    perform.assert_called_once_with(
                        envelope['operationId'], envelope['actor'], envelope['action'], envelope['body'],
                    )
                    fsm_call.assert_called_once_with(envelope['action'], envelope['body'])

    def test_rewritten_fsm_idempotency_key_fails(self):
        from integration_gate.server import GateServer

        vector = self.targets['resale-market/market-cancel-LISTED']
        target_operation_id = vector['envelope']['operationId']
        perform = GateServer.perform

        def rewrite_key(gate, operation_id, actor, action, body):
            if operation_id == target_operation_id:
                body['idempotency_key'] = operation_id
            return perform(gate, operation_id, actor, action, body)

        with patch.object(GateServer, 'perform', rewrite_key):
            with self.assertRaisesRegex(AssertionError, 'journal idempotency key'):
                self._replay_target(vector)

    def test_swapped_outcomes_fail(self):
        for left, right in (
            ('resale-market/market-cancel-LISTED', 'resale-market/market-cancel-BUY_HELD'),
            ('booking-resale/hold-over-capacity', 'booking-resale/hold-occupied-slot'),
        ):
            for vid, other in ((left, right), (right, left)):
                vector = self.targets[vid]
                with self.subTest(vector=vid, swapped_with=other, setup=vector['setup']):
                    observed = self._replay_target(vector)
                    swapped = deepcopy(self._expected_outcome(self.targets[other]))
                    with self.assertRaisesRegex(AssertionError, 'Commerce dispatch outcome differs'):
                        self._assert_outcome(observed, swapped)


if __name__ == '__main__':
    unittest.main()
