"""Transport tests for the non-production loopback integration gate.

These checks compare HTTP results with in-process Core.execute. They do not
claim production readiness, durability, or a live payment, KYC, venue, or bank.
"""
from __future__ import annotations

import io
import json
import socket
import subprocess
import sys
import threading
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from integration_gate.catalogue import load_catalogue, reference_types
from integration_gate.constants import (
    COMMAND_COUNT,
    DEFAULT_TIMEOUT_SECONDS,
    HEALTH_PATH,
    LIVE_HTTP_SERVER_MODE,
    LOCAL_CALL_PATH,
    LOOPBACK_HOST,
    MAX_BODY_BYTES,
    READY_PATH,
)
from integration_gate.openapi_doc import self_test, validate
from integration_gate.schema import problems
from integration_gate.server import build_server, main

ROOT = Path(__file__).resolve().parents[1]
POLICY = {
    'primaryPrice': 100000,
    'resaleCap': 150000,
    'primaryFeeBps': 500,
    'resaleFeeBps': 300,
    'resaleOrganizerBps': 200,
    'resaleAllowed': True,
    'refundProfile': 'FULL_CHAIN_UNWIND_FIXTURE',
}


def _example(schema):
    declared = schema.get('type')
    names = declared if isinstance(declared, list) else [declared]
    for name in names:
        if name == 'string':
            return 'x'
        if name == 'integer':
            return schema.get('minimum', 0)
        if name == 'boolean':
            return False
        if name == 'object':
            return {}
        if name == 'array':
            return []
    raise AssertionError(schema)


def minimal_body(schema, domain):
    body = {}
    for key in schema['required']:
        body[key] = domain if key == 'domain' else _example(schema['properties'][key])
    return body


def _headers(response):
    return {key.lower(): value for key, value in response.getheaders()}


def exchange(port, method, path, payload=None, headers=None, timeout=2):
    import http.client
    conn = http.client.HTTPConnection(LOOPBACK_HOST, port, timeout=timeout)
    data = None
    hdrs = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        hdrs['Content-Type'] = 'application/json'
        hdrs['Content-Length'] = str(len(data))
    if headers:
        hdrs.update(headers)
    conn.request(method, path, body=data, headers=hdrs)
    response = conn.getresponse()
    raw = response.read()
    status = response.status
    header_map = _headers(response)
    conn.close()
    return status, raw, header_map


def parse_json(raw):
    return json.loads(raw.decode('utf-8'))


def assert_gate_headers(test, header_map):
    test.assertEqual(header_map.get('x-kix-production-endpoint'), 'false')
    test.assertEqual(header_map.get('x-kix-transport'), 'integration-gate')
    test.assertTrue(header_map.get('content-type', '').startswith('application/json'))


def envelope(op, actor, action, body):
    return {'operationId': op, 'actor': actor, 'action': action, 'body': body}


def post_call(port, op, actor, action, body, headers=None):
    status, raw, header_map = exchange(
        port, 'POST', LOCAL_CALL_PATH, envelope(op, actor, action, body), headers
    )
    return status, parse_json(raw), header_map


def run_with_server(fn, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, max_body_bytes=MAX_BODY_BYTES):
    httpd = build_server(LOOPBACK_HOST, 0, timeout_seconds, max_body_bytes)
    port = httpd.server_address[1]
    error = []

    def client():
        try:
            wait_ready(port)
            fn(httpd, port)
        except BaseException as exc:
            error.append(exc)
        finally:
            httpd.shutdown()

    worker = threading.Thread(target=client, name='gate-client')
    worker.start()
    try:
        httpd.serve_forever(poll_interval=0.05)
    finally:
        httpd.server_close()
        httpd.close_reference_core()
    worker.join(timeout=5)
    if worker.is_alive():
        raise RuntimeError('client thread did not stop')
    if error:
        raise error[0]


def wait_ready(port):
    deadline = time.monotonic() + 3
    last = None
    while time.monotonic() < deadline:
        try:
            status, raw, _header_map = exchange(port, 'GET', READY_PATH, timeout=0.5)
        except OSError as exc:
            last = exc
            time.sleep(0.02)
            continue
        if status == 200:
            return parse_json(raw)
        last = (status, raw)
        time.sleep(0.02)
    raise RuntimeError(last)


def raw_http(port, payload, timeout=2):
    sock = socket.create_connection((LOOPBACK_HOST, port), timeout=timeout)
    try:
        sock.settimeout(timeout)
        sock.sendall(payload)
        chunks = []
        while True:
            try:
                part = sock.recv(8192)
            except socket.timeout:
                break
            if not part:
                break
            chunks.append(part)
    finally:
        sock.close()
    blob = b''.join(chunks)
    line, _, rest = blob.partition(b'\r\n')
    status = int(line.split()[1])
    _headers_blob, _, body = blob.partition(b'\r\n\r\n')
    return status, body, blob


def start_process():
    proc = subprocess.Popen(
        [sys.executable, '-m', 'integration_gate', '--port', '0'],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    line = proc.stdout.readline().strip()
    if not line.startswith('integration-gate listening 127.0.0.1 '):
        proc.kill()
        proc.wait(timeout=5)
        stderr = proc.stderr.read() if proc.stderr is not None else ''
        stop_process(proc)
        raise RuntimeError(line + '\n' + stderr)
    port = int(line.rsplit(' ', 1)[1])
    wait_ready(port)
    return proc, port


def stop_process(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    for stream in (proc.stdout, proc.stderr):
        if stream is not None and not stream.closed:
            stream.close()


class OpenApiAndSchemaTests(unittest.TestCase):
    def test_integration_gate_document_matches_published_commands(self):
        errors = validate(ROOT)
        self.assertEqual(errors, [])
        catalogue = load_catalogue(ROOT)
        self.assertEqual(len(catalogue.names), COMMAND_COUNT)
        self.assertEqual(self_test(ROOT), 0)

    def test_contract_only_pin_script(self):
        result = subprocess.run(
            [sys.executable, 'scripts/check_openapi_contract.py'],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(
            [sys.executable, 'scripts/check_openapi_contract.py', '--self-test'],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(
            [sys.executable, 'scripts/check_integration_gate_openapi.py', '--self-test'],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_published_schema_rejects_bool_as_integer_and_accepts_null(self):
        catalogue = load_catalogue(ROOT)
        clock = catalogue.commands['advance_clock']
        self.assertEqual(problems({'domain': catalogue.domain, 'now': 1}, clock, 'body'), [])
        self.assertTrue(problems({'domain': catalogue.domain, 'now': True}, clock, 'body'))
        self.assertTrue(problems({'domain': catalogue.domain, 'now': 1.5}, clock, 'body'))
        effect = catalogue.commands['prepare_effect']
        body = minimal_body(effect, catalogue.domain)
        self.assertEqual(problems(body, effect, 'body'), [])
        body['allocationId'] = None
        self.assertEqual(problems(body, effect, 'body'), [])
        body['allocationId'] = 1
        self.assertTrue(problems(body, effect, 'body'))

    def test_refuses_non_loopback_bind(self):
        for host in ('0.0.0.0', 'localhost', '::1'):
            with self.subTest(host=host):
                buf = io.StringIO()
                with redirect_stderr(buf):
                    code = main(['--host', host, '--port', '9'])
                self.assertEqual(code, 2)
                self.assertIn('REFUSING_NON_LOOPBACK_BIND', buf.getvalue())


class TransportTests(unittest.TestCase):
    def test_health_is_not_readiness(self):
        def run(httpd, port):
            status, raw, headers = exchange(port, 'GET', HEALTH_PATH)
            assert_gate_headers(self, headers)
            health = parse_json(raw)
            self.assertEqual(status, 200)
            self.assertEqual(health['status'], 'up')
            self.assertEqual(health['liveHttpServer'], LIVE_HTTP_SERVER_MODE)
            self.assertIs(health['production'], False)
            self.assertIs(health['productionReadiness'], False)
            self.assertNotIn('commandCount', health)
            ready = wait_ready(port)
            self.assertEqual(ready['commandCount'], COMMAND_COUNT)
            self.assertIs(ready['durable'], False)
            self.assertIs(ready['liveMoney'], False)
            self.assertIs(ready['productionReadiness'], False)
            httpd.set_accepting(False)
            status, raw, _headers = exchange(port, 'GET', HEALTH_PATH)
            self.assertEqual(status, 200)
            self.assertEqual(parse_json(raw)['status'], 'up')
            status, raw, headers = exchange(port, 'GET', READY_PATH)
            assert_gate_headers(self, headers)
            blocked = parse_json(raw)
            self.assertEqual(status, 503)
            self.assertEqual(blocked['error'], 'NOT_READY')
            self.assertIs(blocked['rejected'], True)
            status, payload, _headers = post_call(
                port, 'op-blocked', 'operator', 'advance_clock',
                {'domain': load_catalogue(ROOT).domain, 'now': 3},
            )
            self.assertEqual(status, 503)
            self.assertEqual(payload['error'], 'NOT_READY')
            httpd.set_accepting(True)
            status, payload, _headers = post_call(
                port, 'op-ok', 'operator', 'advance_clock',
                {'domain': load_catalogue(ROOT).domain, 'now': 3},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)
            self.assertEqual(payload['result']['logicalTime'], 3)
            self.assertNotIn('rejected', payload)

        run_with_server(run)

    def test_all_forty_commands_have_explicit_rejects(self):
        catalogue = load_catalogue(ROOT)
        Core, Rejected = reference_types()
        seen = []

        def run(_httpd, port):
            for _pass in (1, 2):
                for action in catalogue.names:
                    body = minimal_body(catalogue.commands[action], catalogue.domain)
                    self.assertEqual(problems(body, catalogue.commands[action], 'body'), [])
                    core = Core()
                    try:
                        core.execute('smoke-' + action, 'smoke', action, body)
                        local = None
                    except Rejected as exc:
                        local = str(exc)
                    finally:
                        core.db.close()
                    self.assertIsNotNone(local, action)
                    status, payload, headers = post_call(port, 'smoke-' + action, 'smoke', action, body)
                    assert_gate_headers(self, headers)
                    self.assertEqual(status, 422, (action, payload))
                    self.assertIs(payload['rejected'], True)
                    self.assertEqual(payload['error'], local)
                    self.assertNotEqual(payload['error'], 'UNKNOWN_ACTION')
                    seen.append(action)

        run_with_server(run)
        self.assertEqual(len(set(seen)), COMMAND_COUNT)

    def test_representative_commands_match_local_call(self):
        catalogue = load_catalogue(ROOT)
        domain = catalogue.domain
        Core, Rejected = reference_types()
        scope = dict(Core.SCOPE)
        clock = {'domain': domain, 'now': 5}
        event = {
            'domain': domain,
            'eventId': 'show',
            'organizer': 'organizer',
            'policy': dict(POLICY),
            'seats': ['A1'],
        }
        capture = {
            'domain': domain,
            'tradeId': 'missing',
            'orderId': 'order-1',
            'paymentId': 'pay-1',
            'amount': 1,
            'currency': 'KRW',
            'buyer': 'A',
            'scope': scope,
            'provenance': 'synthetic',
        }
        admit = {
            'domain': domain,
            'ticketId': 'missing',
            'holder': 'A',
            'expectedVersion': 0,
            'admissionEpoch': 0,
        }
        steps = [
            ('op-clock', 'operator', 'advance_clock', clock, 'ok', None),
            ('op-clock', 'operator', 'advance_clock', clock, 'replay', None),
            ('op-clock', 'operator', 'advance_clock', {'domain': domain, 'now': 9}, 'rejected', 'OPERATION_ID_CONFLICT'),
            ('op-back', 'operator', 'advance_clock', {'domain': domain, 'now': 4}, 'rejected', 'INVALID_FIXTURE_CLOCK'),
            ('op-event', 'operator', 'create_event', event, 'ok', None),
            ('op-event', 'operator', 'create_event', event, 'replay', None),
            ('op-close', 'operator', 'close_sales', {'domain': domain, 'eventId': 'show'}, 'ok', None),
            ('op-open', 'operator', 'open_admission', {'domain': domain, 'eventId': 'show'}, 'ok', None),
            ('op-cap', 'pg-adapter', 'capture', capture, 'rejected', 'TRADE_NOT_FOUND'),
            ('op-admit', 'venue', 'admit', admit, 'rejected', 'TICKET_NOT_FOUND'),
            ('op-miss', 'operator', 'cancel_event', {'domain': domain, 'eventId': 'missing'}, 'rejected', 'EVENT_NOT_FOUND'),
        ]

        def local_outcome(core, op, actor, action, body):
            try:
                return ('ok', core.execute(op, actor, action, json.loads(json.dumps(body))))
            except Rejected as exc:
                return ('rejected', str(exc))

        def run(_httpd, port):
            core = Core()
            try:
                first = {}
                for op, actor, action, body, kind, code in steps:
                    local = local_outcome(core, op, actor, action, body)
                    status, payload, _headers = post_call(port, op, actor, action, body)
                    if kind == 'rejected':
                        self.assertEqual(local, ('rejected', code))
                        self.assertEqual(status, 422)
                        self.assertEqual(payload['error'], code)
                        self.assertIs(payload['rejected'], True)
                    else:
                        self.assertEqual(local[0], 'ok')
                        self.assertEqual(status, 200, payload)
                        self.assertEqual(payload, local[1])
                        self.assertEqual(payload['action'], action)
                        self.assertNotIn('rejected', payload)
                        if kind == 'ok':
                            first[op] = payload
                            self.assertGreaterEqual(payload['sequence'], 1)
                        else:
                            self.assertEqual(payload, first[op])
                            self.assertEqual(payload['sequence'], first[op]['sequence'])
                self.assertEqual(first['op-clock']['result']['logicalTime'], 5)
                self.assertEqual(first['op-clock']['sequence'], 1)
                self.assertEqual(first['op-event']['action'], 'create_event')
            finally:
                core.db.close()

        run_with_server(run)

    def test_http_idempotency_key_header_is_not_consulted(self):
        domain = load_catalogue(ROOT).domain

        def run(_httpd, port):
            headers = {'Idempotency-Key': 'same-header'}
            status, first, _headers = post_call(
                port, 'op-a', 'operator', 'advance_clock', {'domain': domain, 'now': 1}, headers
            )
            status2, second, _headers = post_call(
                port, 'op-b', 'operator', 'advance_clock', {'domain': domain, 'now': 2}, headers
            )
            self.assertEqual(status, 200)
            self.assertEqual(status2, 200)
            self.assertEqual(first['result']['logicalTime'], 1)
            self.assertEqual(second['result']['logicalTime'], 2)
            self.assertEqual(second['sequence'], 2)

        run_with_server(run)

    def test_schema_reject_does_not_store_operation_or_echo_values(self):
        domain = load_catalogue(ROOT).domain

        def run(_httpd, port):
            status, raw, _headers = exchange(port, 'POST', LOCAL_CALL_PATH, {
                'operationId': 'op-schema',
                'actor': 'operator',
                'action': 'advance_clock',
                'body': {'domain': domain, 'now': 1, 'evil': 'secret-value'},
            })
            self.assertEqual(status, 400)
            self.assertNotIn(b'secret-value', raw)
            payload = parse_json(raw)
            self.assertEqual(payload['error'], 'SCHEMA_REJECTED')
            self.assertIs(payload['rejected'], True)
            status, payload, _headers = post_call(
                port, 'op-schema', 'operator', 'advance_clock', {'domain': domain, 'now': 4}
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)
            self.assertEqual(payload['result']['logicalTime'], 4)

        run_with_server(run)

    def test_unsupported_paths_methods_and_actions(self):
        domain = load_catalogue(ROOT).domain
        targets = [
            '/',
            '/commands',
            '/commands/create_event',
            '/x-kix-contract-only',
            '/x-kix-contract-only/local-call/',
            '/x-kix-contract-only/local-call/extra',
            '/health/../ready',
            '//health',
            '/ready/',
            '/openapi.json',
            '/metrics',
            '/v1/events',
            '/pg/charge',
            '/kyc/verify',
        ]

        def run(_httpd, port):
            for target in targets:
                status, body, blob = raw_http(
                    port,
                    ('GET %s HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n' % target).encode(),
                )
                self.assertEqual(status, 404, target)
                self.assertEqual(parse_json(body)['error'], 'NOT_FOUND')
                self.assertIn(b'X-Kix-Production-Endpoint: false', blob)
                self.assertNotIn(b'<html', blob.lower())
            status, body, _blob = raw_http(
                port,
                b'GET /health?ready=1 HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n',
            )
            self.assertEqual(status, 400)
            self.assertEqual(parse_json(body)['error'], 'QUERY_NOT_ALLOWED')
            for method in ('GET', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT', 'FOO'):
                status, body, blob = raw_http(
                    port,
                    (
                        '%s %s HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n'
                        % (method, LOCAL_CALL_PATH)
                    ).encode(),
                )
                self.assertEqual(status, 405, method)
                self.assertEqual(parse_json(body)['error'], 'METHOD_NOT_ALLOWED')
                self.assertIn(b'Allow: POST', blob)
            status, body, blob = raw_http(
                port,
                b'POST /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n',
            )
            self.assertEqual(status, 405)
            self.assertIn(b'Allow: GET', blob)
            for action in ('kyc_verify', 'pg_charge', 'bank_transfer', 'venue_scan', 'marketplace_list', 'create_event '):
                status, payload, _headers = post_call(
                    port, 'op-' + action.strip(), 'operator', action, {'domain': domain}
                )
                self.assertEqual(status, 400, action)
                self.assertEqual(payload['error'], 'UNKNOWN_ACTION')
                self.assertIs(payload['rejected'], True)
            status, payload, _headers = post_call(
                port, 'op-after-unknown', 'operator', 'advance_clock', {'domain': domain, 'now': 1}
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)

        run_with_server(run)

    def test_transport_limits_and_malformed_bodies(self):
        domain = load_catalogue(ROOT).domain

        def run(_httpd, port):
            cases = [
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Content-Type: application/json\r\nConnection: close\r\n\r\n{}',
                 411, 'CONTENT_LENGTH_REQUIRED'),
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Content-Type: application/json\r\nContent-Length: 2\r\nContent-Length: 2\r\n'
                 b'Connection: close\r\n\r\n{}',
                 400, 'BAD_CONTENT_LENGTH'),
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Transfer-Encoding: chunked\r\nConnection: close\r\n\r\n0\r\n\r\n',
                 400, 'UNSUPPORTED_TRANSFER'),
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Content-Type: text/plain\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}',
                 415, 'UNSUPPORTED_MEDIA_TYPE'),
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Content-Type: application/json\r\nContent-Length: 1\r\nConnection: close\r\n\r\n{',
                 400, 'INVALID_JSON'),
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Content-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}',
                 400, 'ENVELOPE_INVALID'),
                (b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                 b'Expect: 100-continue\r\nContent-Type: application/json\r\nContent-Length: 2\r\n'
                 b'Connection: close\r\n\r\n{}',
                 417, 'EXPECTATION_FAILED'),
            ]
            for payload, status_code, error in cases:
                status, body, blob = raw_http(port, payload)
                self.assertEqual(status, status_code, body)
                self.assertEqual(parse_json(body)['error'], error)
                self.assertNotIn(b'<html', blob.lower())
            duplicate = (
                '{"operationId":"a","operationId":"b","actor":"operator","action":"advance_clock",'
                '"body":{"domain":"%s","now":1}}' % domain
            ).encode()
            status, body, _blob = raw_http(
                port,
                b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                b'Content-Type: application/json\r\nContent-Length: ' + str(len(duplicate)).encode()
                + b'\r\nConnection: close\r\n\r\n' + duplicate,
            )
            self.assertEqual(status, 400)
            self.assertEqual(parse_json(body)['error'], 'DUPLICATE_KEY')
            status, payload, _headers = post_call(
                port, '  spaced', 'operator', 'advance_clock', {'domain': domain, 'now': 1}
            )
            self.assertEqual(status, 422)
            self.assertEqual(payload['error'], 'INVALID_ID')
            status, raw, _headers = exchange(port, 'POST', LOCAL_CALL_PATH, {
                'operationId': 'op-null-body',
                'actor': 'operator',
                'action': 'advance_clock',
                'body': None,
            })
            self.assertEqual(status, 400)
            self.assertEqual(parse_json(raw)['error'], 'OBJECT_BODY_REQUIRED')
            huge = b'X-Padding: ' + (b'a' * 9000) + b'\r\n'
            status, body, _blob = raw_http(
                port,
                b'GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\n' + huge + b'Connection: close\r\n\r\n',
            )
            self.assertEqual(status, 431)
            self.assertEqual(parse_json(body)['error'], 'HEADER_TOO_LARGE')

        run_with_server(run)

    def test_body_limit_and_request_timeout(self):
        def limited(_httpd, port):
            status, body, _blob = raw_http(
                port,
                b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                b'Content-Type: application/json\r\nContent-Length: 65\r\nConnection: close\r\n\r\n',
            )
            self.assertEqual(status, 413)
            self.assertEqual(parse_json(body)['error'], 'BODY_TOO_LARGE')
            exact = b'{' * 64
            status, body, _blob = raw_http(
                port,
                b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                b'Content-Type: application/json\r\nContent-Length: 64\r\nConnection: close\r\n\r\n'
                + exact,
            )
            self.assertEqual(status, 400)
            self.assertEqual(parse_json(body)['error'], 'INVALID_JSON')

        run_with_server(limited, max_body_bytes=64)

        def timed(_httpd, port):
            started = time.monotonic()
            status, body, _blob = raw_http(
                port,
                b'POST ' + LOCAL_CALL_PATH.encode() + b' HTTP/1.1\r\nHost: 127.0.0.1\r\n'
                b'Content-Type: application/json\r\nContent-Length: 8\r\nConnection: close\r\n\r\n',
                timeout=3,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(status, 408, body)
            self.assertEqual(parse_json(body)['error'], 'REQUEST_TIMEOUT')
            self.assertLess(elapsed, 3)
            status, raw, _headers = exchange(port, 'GET', HEALTH_PATH)
            self.assertEqual(status, 200)
            self.assertIs(parse_json(raw)['production'], False)

        run_with_server(timed, timeout_seconds=0.5)

    def test_restart_drops_in_memory_state(self):
        domain = load_catalogue(ROOT).domain
        event = {
            'domain': domain,
            'eventId': 'show',
            'organizer': 'organizer',
            'policy': dict(POLICY),
            'seats': ['A1'],
        }
        first, port = start_process()
        try:
            status, payload, _headers = post_call(port, 'op-event', 'operator', 'create_event', event)
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)
            status, payload, _headers = post_call(port, 'op-again', 'operator', 'create_event', event)
            self.assertEqual(status, 422)
            self.assertEqual(payload['error'], 'EVENT_EXISTS')
            status, payload, _headers = post_call(
                port, 'op-clock', 'operator', 'advance_clock', {'domain': domain, 'now': 50}
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['result']['logicalTime'], 50)
        finally:
            stop_process(first)
        second, port = start_process()
        try:
            status, payload, _headers = post_call(port, 'op-event-after', 'operator', 'create_event', event)
            self.assertEqual(status, 200, payload)
            self.assertEqual(payload['sequence'], 1)
            self.assertEqual(payload['action'], 'create_event')
            status, payload, _headers = post_call(
                port, 'op-early', 'operator', 'advance_clock', {'domain': domain, 'now': 1}
            )
            self.assertEqual(status, 200, payload)
            self.assertEqual(payload['result']['logicalTime'], 1)
        finally:
            stop_process(second)


if __name__ == '__main__':
    unittest.main()
