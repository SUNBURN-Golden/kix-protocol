"""Transport tests for the non-production loopback integration gate.

These checks compare HTTP results with in-process Core.execute. They do not
claim production readiness, durability, or a live payment, KYC, venue, or bank.
"""
from __future__ import annotations

import io
import json
import socket
import struct
import subprocess
import sys
import tempfile
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
from readiness.store import ReadinessStore
from readiness.conformance import assert_budget_rejection

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
    test.assertEqual(header_map.get('x-kix-protocol-truth'), 'false')
    test.assertEqual(header_map.get('x-kix-production-conformance'), 'false')
    test.assertEqual(header_map.get('x-kix-transport'), 'integration-gate')
    test.assertTrue(header_map.get('x-request-id'))
    test.assertTrue(header_map.get('content-type', '').startswith('application/json'))


def envelope(op, actor, action, body):
    return {'operationId': op, 'actor': actor, 'action': action, 'body': body}


def post_call(port, op, actor, action, body, headers=None):
    status, raw, header_map = exchange(
        port, 'POST', LOCAL_CALL_PATH, envelope(op, actor, action, body), headers
    )
    return status, parse_json(raw), header_map


def run_with_server(
    fn,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    max_body_bytes=MAX_BODY_BYTES,
    readiness_dir=None,
    max_in_flight=8,
    max_journal_records=4096,
):
    httpd = build_server(
        LOOPBACK_HOST,
        0,
        timeout_seconds,
        max_body_bytes,
        readiness_dir=readiness_dir,
        max_in_flight=max_in_flight,
        max_journal_records=max_journal_records,
    )
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


def _capture_stream(stream, bucket):
    try:
        bucket.append(stream.read())
    except Exception as exc:
        bucket.append(str(exc))


def start_process(extra=None):
    command = [sys.executable, '-m', 'integration_gate', '--port', '0']
    if extra:
        command.extend(extra)
    proc = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    bucket = []
    thread = threading.Thread(target=_capture_stream, args=(proc.stderr, bucket), daemon=True)
    thread.start()
    proc.stderr_bucket = bucket
    proc.stderr_thread = thread
    line = proc.stdout.readline().strip()
    if not line.startswith('integration-gate listening 127.0.0.1 '):
        proc.kill()
        proc.wait(timeout=5)
        thread.join(timeout=2)
        stderr = bucket[0] if bucket else ''
        stop_process(proc)
        raise RuntimeError(line + '\n' + stderr)
    port = int(line.rsplit(' ', 1)[1])
    wait_ready(port)
    return proc, port


def stop_process(proc):
    _finish_process(proc, proc.terminate)


def kill_process(proc):
    _finish_process(proc, proc.kill)


def _finish_process(proc, stop):
    if proc.poll() is None:
        stop()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    if proc.stdout is not None and not proc.stdout.closed:
        proc.stdout.close()
    thread = getattr(proc, 'stderr_thread', None)
    if thread is not None:
        thread.join(timeout=2)


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
            for action in (
                'kyc_verify',
                'pg_charge',
                'bank_transfer',
                'venue_scan',
                'marketplace_list',
                'authorize_admission',
                'consume_admission',
                'create_event ',
            ):
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

    def test_loopback_refusal_still_applies_with_a_readiness_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stderr(buf):
                code = main(['--host', '0.0.0.0', '--port', '9', '--readiness-dir', tmp])
            self.assertEqual(code, 2)
            self.assertIn('REFUSING_NON_LOOPBACK_BIND', buf.getvalue())

    def test_request_id_is_echoed_and_audited(self):
        domain = load_catalogue(ROOT).domain
        captured = io.StringIO()
        previous = sys.stderr
        sys.stderr = captured

        def run(_httpd, port):
            status, payload, headers = post_call(
                port, 'op-trace', 'operator', 'advance_clock',
                {'domain': domain, 'now': 7},
                headers={'X-Request-Id': 'req-1', 'X-Correlation-Id': 'corr-1'},
            )
            assert_gate_headers(self, headers)
            self.assertEqual(status, 200)
            self.assertEqual(headers.get('x-request-id'), 'req-1')
            self.assertEqual(headers.get('x-correlation-id'), 'corr-1')
            self.assertEqual(payload['result']['logicalTime'], 7)
            self.assertIs(payload.get('productionReadiness'), None)
            status, _payload, headers = post_call(
                port, 'op-trace-2', 'operator', 'advance_clock',
                {'domain': domain, 'now': 8},
                headers={'X-Request-Id': 'bad id'},
            )
            self.assertEqual(status, 200)
            self.assertNotEqual(headers.get('x-request-id'), 'bad id')
            self.assertRegex(headers.get('x-request-id'), r'^[0-9a-f]{32}$')

        try:
            run_with_server(run)
        finally:
            sys.stderr = previous
        text = captured.getvalue()
        self.assertIn('"requestId":"req-1"', text)
        self.assertIn('"correlationId":"corr-1"', text)
        self.assertIn('"protocolTruth":false', text)
        self.assertIn('"productionConformance":false', text)
        self.assertIn('"productionEndpoint":false', text)
        self.assertNotIn('production-ready', text.lower())

    def test_drain_keeps_liveness_and_refuses_commands(self):
        domain = load_catalogue(ROOT).domain

        def run(httpd, port):
            httpd.begin_drain()
            status, raw, headers = exchange(port, 'GET', HEALTH_PATH)
            assert_gate_headers(self, headers)
            health = parse_json(raw)
            self.assertEqual(status, 200)
            self.assertEqual(health['status'], 'up')
            self.assertIs(health['productionReadiness'], False)
            self.assertIs(health['productionConformance'], False)
            self.assertIs(health['protocolTruth'], False)
            self.assertIs(health['localFileJournal'], False)
            status, raw, _headers = exchange(port, 'GET', READY_PATH)
            self.assertEqual(status, 503)
            self.assertEqual(parse_json(raw)['error'], 'NOT_READY')
            status, payload, _headers = post_call(
                port, 'op-drained', 'operator', 'advance_clock',
                {'domain': domain, 'now': 9},
            )
            self.assertEqual(status, 503)
            self.assertEqual(payload['error'], 'NOT_READY')
            self.assertIs(payload['productionReadiness'], False)

        run_with_server(run)

    def test_bounded_concurrency_fails_closed(self):
        domain = load_catalogue(ROOT).domain

        def run(httpd, port):
            self.assertEqual(httpd.try_admit(), 'OK')
            try:
                status, raw, _headers = exchange(port, 'GET', HEALTH_PATH)
                self.assertEqual(status, 200)
                self.assertEqual(parse_json(raw)['status'], 'up')
                status, payload, headers = post_call(
                    port, 'op-busy', 'operator', 'advance_clock',
                    {'domain': domain, 'now': 4},
                )
                assert_gate_headers(self, headers)
                self.assertEqual(status, 503)
                self.assertEqual(payload['error'], 'OVERLOADED')
            finally:
                httpd.release_admit()
            status, payload, _headers = post_call(
                port, 'op-after', 'operator', 'advance_clock',
                {'domain': domain, 'now': 4},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['result']['logicalTime'], 4)

        run_with_server(run, max_in_flight=1)

    def test_journal_budget_does_not_apply_the_next_command(self):
        domain = load_catalogue(ROOT).domain

        def run(_httpd, port):
            def ready_call():
                status, raw, _headers = exchange(port, 'GET', READY_PATH)
                return status, parse_json(raw)

            def command_call(*args):
                status, payload, _headers = post_call(port, *args)
                return status, payload

            assert_budget_rejection(self, ready_call, command_call, domain)

        with tempfile.TemporaryDirectory() as tmp:
            run_with_server(run, readiness_dir=tmp, max_journal_records=1)

    def test_killed_gate_replays_one_event_and_drops_a_torn_tail(self):
        domain = load_catalogue(ROOT).domain
        event = {
            'domain': domain,
            'eventId': 'show',
            'organizer': 'organizer',
            'policy': dict(POLICY),
            'seats': ['A1'],
        }
        with tempfile.TemporaryDirectory() as tmp:
            first, port = start_process(['--readiness-dir', tmp])
            try:
                status, payload, headers = post_call(
                    port, 'op-event', 'operator', 'create_event', event,
                )
                assert_gate_headers(self, headers)
                self.assertEqual(status, 200)
                self.assertEqual(payload['sequence'], 1)
                status, ready_raw, _headers = exchange(port, 'GET', READY_PATH)
                ready = parse_json(ready_raw)
                self.assertEqual(status, 200)
                self.assertIs(ready['durable'], False)
                self.assertIs(ready['productionReadiness'], False)
                self.assertIs(ready['localFileJournal'], True)
                self.assertGreaterEqual(ready['journalRecords'], 1)
            finally:
                kill_process(first)
            journal = Path(tmp) / 'journal.v1'
            with journal.open('ab') as handle:
                handle.write(b'\x01\x02\x03')
            second, port = start_process(['--readiness-dir', tmp])
            try:
                status, payload, _headers = post_call(
                    port, 'op-event', 'operator', 'create_event', event,
                )
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload['sequence'], 1)
                self.assertEqual(payload['action'], 'create_event')
                status, payload, _headers = post_call(
                    port, 'op-event-2', 'operator', 'create_event', event,
                )
                self.assertEqual(status, 422)
                self.assertEqual(payload['error'], 'EVENT_EXISTS')
            finally:
                stop_process(second)

    def test_corrupt_journal_and_unknown_schema_do_not_listen(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            store.append({
                'kind': 'core_commit',
                'machine': 'integration_core',
                'operationId': 'op-1',
                'actor': 'operator',
                'action': 'advance_clock',
                'body': {'domain': 'kix:fixture:lifecycle:0.3', 'now': 1},
                'receiptDigest': 'ab' * 32,
            })
            store.close()
            path = Path(tmp) / 'journal.v1'
            data = bytearray(path.read_bytes())
            data[20] ^= 0xFF
            path.write_bytes(data)
            checksum = subprocess.run(
                [sys.executable, '-m', 'integration_gate', '--port', '0', '--readiness-dir', tmp],
                cwd=ROOT, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(checksum.returncode, 2, checksum.stderr)
            self.assertIn('CHECKSUM_MISMATCH', checksum.stderr)
            self.assertNotIn('listening', checksum.stdout)
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            store.close()
            path = Path(tmp) / 'journal.v1'
            data = bytearray(path.read_bytes())
            struct.pack_into('>I', data, 8, 2)
            path.write_bytes(data)
            unknown = subprocess.run(
                [sys.executable, '-m', 'integration_gate', '--port', '0', '--readiness-dir', tmp],
                cwd=ROOT, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(unknown.returncode, 2, unknown.stderr)
            self.assertIn('UNSUPPORTED_SCHEMA', unknown.stderr)
            self.assertNotIn('listening', unknown.stdout)

    def test_budget_rejection_names_the_record_limit_and_omits_the_body(self):
        domain = load_catalogue(ROOT).domain
        captured = io.StringIO()
        previous = sys.stderr
        sys.stderr = captured

        def run(_httpd, port):
            status, payload, _headers = post_call(
                port, 'op-clock', 'operator', 'advance_clock',
                {'domain': domain, 'now': 50},
            )
            self.assertEqual(status, 200, payload)
            status, payload, _headers = post_call(
                port, 'op-clock-2', 'operator', 'advance_clock',
                {'domain': domain, 'now': 60},
            )
            self.assertEqual(status, 503)
            self.assertEqual(payload['error'], 'JOURNAL_BUDGET')

        try:
            with tempfile.TemporaryDirectory() as tmp:
                run_with_server(run, readiness_dir=tmp, max_journal_records=1)
        finally:
            sys.stderr = previous
        rejected = [
            json.loads(line)
            for line in captured.getvalue().splitlines()
            if line.startswith('{') and '"JOURNAL_BUDGET"' in line
        ]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]['journalDecision'], 'budget_rejected')
        self.assertEqual(rejected[0]['budgetLimit'], 'records')
        self.assertEqual(rejected[0]['queued'], 0)
        self.assertIs(rejected[0]['productionReadiness'], False)
        self.assertIs(rejected[0]['protocolTruth'], False)
        self.assertNotIn('body', rejected[0])
        self.assertNotIn('entry', rejected[0])
        self.assertNotIn('now', json.dumps(rejected[0]))

    def test_overload_observation_does_not_queue(self):
        domain = load_catalogue(ROOT).domain
        captured = io.StringIO()
        previous = sys.stderr
        sys.stderr = captured

        def run(httpd, port):
            self.assertEqual(httpd.try_admit(), 'OK')
            try:
                status, payload, _headers = post_call(
                    port, 'op-busy', 'operator', 'advance_clock',
                    {'domain': domain, 'now': 4},
                )
                self.assertEqual(status, 503)
                self.assertEqual(payload['error'], 'OVERLOADED')
            finally:
                httpd.release_admit()

        try:
            run_with_server(run, max_in_flight=1)
        finally:
            sys.stderr = previous
        overloaded = [
            json.loads(line)
            for line in captured.getvalue().splitlines()
            if line.startswith('{') and '"OVERLOADED"' in line
        ]
        self.assertEqual(len(overloaded), 1)
        self.assertEqual(overloaded[0]['admit'], 'OVERLOADED')
        self.assertEqual(overloaded[0]['queued'], 0)
        self.assertEqual(overloaded[0]['journalDecision'], 'not_attempted')
        self.assertIs(overloaded[0]['productionReadiness'], False)
        self.assertNotIn('body', overloaded[0])
        self.assertNotIn('now', json.dumps(overloaded[0]))


if __name__ == '__main__':
    unittest.main()
