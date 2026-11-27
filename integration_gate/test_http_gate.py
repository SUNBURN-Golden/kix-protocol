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
from http.client import RemoteDisconnected
from pathlib import Path
from unittest.mock import patch

from integration_gate.catalogue import load_catalogue, reference_types
from integration_gate.constants import (
    BROWSER_ALLOWED_ORIGIN,
    BROWSER_ALLOWED_REQUEST_HEADERS,
    COMMAND_COUNT,
    CORE_COMMAND_COUNT,
    DEFAULT_TIMEOUT_SECONDS,
    HEADER_LIMIT_BYTES,
    HEALTH_PATH,
    LIVE_HTTP_SERVER_MODE,
    LOCAL_CALL_PATH,
    LOOPBACK_HOST,
    MAX_BODY_BYTES,
    READINESS_FSM_REFUSED,
    READY_PATH,
)
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.openapi_doc import self_test, validate
from integration_gate.resale_reads import READ_PREFIX
from integration_gate.schema import problems
from integration_gate.server import GateHandler, build_server, main
from readiness.codec import receipt_digest
from readiness.store import ReadinessStore, StoreError
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


def assert_no_cors(test, header_map):
    for key in header_map:
        test.assertFalse(key.startswith('access-control-'), key)
    test.assertNotIn('vary', header_map)


def assert_journal_audit(test, captured, request_id, decision, body_marker):
    text = captured.getvalue()
    records = [json.loads(line) for line in text.splitlines()
               if line.startswith('{')]
    matches = [record for record in records
               if record.get('requestId') == request_id]
    test.assertEqual(len(matches), 1, text)
    record = matches[0]
    test.assertEqual(record['journalDecision'], decision)
    for label in ('protocolTruth', 'productionConformance',
                  'productionReadiness', 'productionEndpoint'):
        test.assertIs(record[label], False)
    test.assertNotIn('body', record)
    test.assertNotIn('entry', record)
    test.assertNotIn(body_marker, text)


def raw_message(method, path, header_lines):
    lines = ['%s %s HTTP/1.1' % (method, path)]
    lines.extend(header_lines)
    lines.append('Connection: close')
    return ('\r\n'.join(lines) + '\r\n\r\n').encode('iso-8859-1')


def parse_response(blob):
    head, _, body = blob.partition(b'\r\n\r\n')
    rows = head.split(b'\r\n')
    status = int(rows[0].split()[1])
    headers = {}
    seen = []
    for row in rows[1:]:
        if not row:
            continue
        name, _, value = row.partition(b':')
        key = name.decode('iso-8859-1').lower()
        seen.append(key)
        headers.setdefault(key, value.decode('iso-8859-1').strip())
    return status, body, headers, seen


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
    browser_origin=None,
):
    httpd = build_server(
        LOOPBACK_HOST,
        0,
        timeout_seconds,
        max_body_bytes,
        readiness_dir=readiness_dir,
        max_in_flight=max_in_flight,
        max_journal_records=max_journal_records,
        browser_origin=browser_origin,
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


def wait_admit_idle(httpd, timeout=3):
    """Poll until the gate's admit slot is free. Test harness only."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if httpd.admit.view()['inFlight'] == 0:
            return
        time.sleep(0.005)
    raise AssertionError('admit slot not released')


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
                for action in catalogue.core_names:
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
        self.assertEqual(len(set(seen)), CORE_COMMAND_COUNT)

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

    def test_fsm_commands_match_a_direct_machine_call(self):
        catalogue = load_catalogue(ROOT)
        shadow = FsmHost()

        def invoke(action, body):
            try:
                return 200, shadow.call(action, body)
            except FsmRejected as exc:
                return 422, {'error': exc.code, 'rejected': True}

        def run(_httpd, port):
            for action in catalogue.fsm_names:
                body = minimal_body(catalogue.commands[action], catalogue.domain)
                self.assertEqual(problems(body, catalogue.commands[action], 'body'), [], action)
                status, payload = invoke(action, body)
                http_status, http_payload, _headers = post_call(
                    port, 'fsm-' + action, 'operator', action, body,
                )
                self.assertEqual(http_status, status, (action, http_payload))
                if status == 200:
                    self.assertEqual(http_payload, payload, action)
                else:
                    self.assertEqual(http_payload['error'], payload['error'], action)
                    self.assertIs(http_payload['rejected'], True)

        run_with_server(run)
        self.assertEqual(len(catalogue.fsm_names), 44)

    def test_admission_happy_path_over_http(self):
        booking = str(ROOT / 'reference' / 'booking_resale_admission')
        if booking not in sys.path:
            sys.path.insert(0, booking)
        from mock_gates import ADMISSION_WINDOW_MS, OFFER_WINDOW_MS

        price = 10001
        now = 1000000
        expires = now + OFFER_WINDOW_MS
        admit_expires = now + ADMISSION_WINDOW_MS
        pay = 'ab' * 32
        request = '11' * 32
        show = {
            'organizer_role': 'organizer',
            'capacity': 2,
            'gate_roles': ['gate-a', 'gate-b'],
            'primary_price': price,
            'resale_cap': 20000,
            'resale_allowed': True,
            'organizer_bps': 1,
            'platform_bps': 1,
        }

        def run(_httpd, port):
            steps = [
                ('reservation_set_clock', {'subject_id': 'clock', 'idempotency_key': 'clock-1', 'now_ms': now}),
                ('reservation_register_show', dict(show_id='show-1', idempotency_key='show-1', **show)),
                ('reservation_hold', {
                    'reservation_id': 'reserve-1', 'idempotency_key': 'hold-1', 'show_id': 'show-1',
                    'slot': 0, 'buyer_role': 'buyer-1', 'expires_ms': expires,
                }),
                ('reservation_confirm', {
                    'order_id': 'order-1', 'idempotency_key': 'confirm-1', 'reservation_id': 'reserve-1',
                    'amount': price, 'quote_ref': 'quote-1',
                }),
                ('reservation_observe_payment', {
                    'order_id': 'order-1', 'idempotency_key': 'pay-1', 'payment_ref': pay, 'amount': price,
                }),
                ('reservation_issue', {
                    'issuance_id': 'issue-1', 'idempotency_key': 'issue-1', 'order_id': 'order-1',
                }),
                ('admission_set_clock', {'subject_id': 'clock', 'idempotency_key': 'gate-clock', 'now_ms': now}),
                ('admission_adopt_issued', dict(
                    right_id='issue-1', idempotency_key='adopt-1', show_id='show-1', slot=0,
                    buyer_role='buyer-1', expires_ms=expires, order_id='order-1', amount=price,
                    payment_ref=pay, reservation_id='reserve-1', quote_ref='quote-1', **show,
                )),
                ('admission_authorize_admission', {
                    'admission_id': 'admit-1', 'idempotency_key': 'admit-1', 'right_id': 'issue-1',
                    'version': 1, 'holder_role': 'buyer-1', 'gate_role': 'gate-a', 'request': request,
                    'expires_ms': admit_expires,
                }),
                ('admission_consume', {
                    'consume_id': 'consume-1', 'idempotency_key': 'consume-1', 'right_id': 'issue-1',
                    'version': 1, 'gate_role': 'gate-a', 'request': request,
                }),
            ]
            for index, (action, body) in enumerate(steps):
                status, payload, _headers = post_call(port, 'admit-path-%d' % index, 'operator', action, body)
                self.assertEqual(status, 200, (action, payload))
                self.assertIs(payload['duplicate'], False, action)
            self.assertEqual(payload['evidence']['decision'], 'CONSUMED_ONCE')
            self.assertIs(payload['admission_routing_production'], False)
            self.assertIs(payload['funds_executed'], False)

        run_with_server(run)

    def test_fsm_idempotency_key_replays_without_using_operation_id(self):
        body = {
            'settlement_id': 'claim-1',
            'idempotency_key': 'init-1',
            'trade_id': 'trade-1',
            'gross': 10001,
            'debtor_role': 'fixture-merchant',
            'policy': {
                'kind': 'PRIMARY_FEE_BPS',
                'fee_bps': 0,
                'residual_payee': 'organizer',
                'fee_payee': 'platform',
            },
        }

        def run(_httpd, port):
            first_status, first, _headers = post_call(
                port, 'settle-op-1', 'operator', 'settlement_initiate', body,
            )
            second_status, second, _headers = post_call(
                port, 'settle-op-2', 'operator', 'settlement_initiate', body,
            )
            self.assertEqual(first_status, 200, first)
            self.assertEqual(second_status, 200, second)
            self.assertIs(first['duplicate'], False)
            self.assertIs(second['duplicate'], True)
            self.assertIsNone(second['applied'])
            self.assertIs(second['funds_executed'], False)

        run_with_server(run)

    def test_readiness_directory_refuses_fsm_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            def run(_httpd, port):
                body = {
                    'settlement_id': 'claim-1',
                    'idempotency_key': 'init-1',
                    'trade_id': 'trade-1',
                    'gross': 10001,
                    'debtor_role': 'fixture-merchant',
                    'policy': {'kind': 'PRIMARY_FEE_BPS', 'fee_bps': 0,
                               'residual_payee': 'organizer', 'fee_payee': 'platform'},
                }
                status, payload, _headers = post_call(
                    port, 'fsm-refused', 'operator', 'settlement_initiate', body,
                )
                self.assertEqual(status, 422, payload)
                self.assertEqual(payload['error'], READINESS_FSM_REFUSED)
                self.assertIs(payload['rejected'], True)
                domain = load_catalogue(ROOT).domain
                status, payload, _headers = post_call(
                    port, 'core-still-open', 'operator', 'advance_clock',
                    {'domain': domain, 'now': 1},
                )
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload['sequence'], 1)

            run_with_server(run, readiness_dir=tmp)
            journal = Path(tmp) / 'journal.v1'
            raw = journal.read_bytes()
            self.assertNotIn(b'settlement_initiate', raw)
            self.assertIn(b'advance_clock', raw)

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

    def test_core_receipt_replay_preserves_receipt_and_journal(self):
        domain = load_catalogue(ROOT).domain
        body = {'domain': domain, 'now': 731942}
        captured = io.StringIO()
        original = {}
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / 'journal.v1'

            def commit(httpd, port):
                status, receipt, headers = post_call(
                    port, 'op-receipt-replay', 'operator', 'advance_clock', body,
                    headers={'X-Request-Id': 'req-receipt-original'},
                )
                assert_gate_headers(self, headers)
                self.assertEqual(status, 200, receipt)
                self.assertEqual(receipt['result']['logicalTime'], body['now'])
                self.assertEqual(len(httpd.store.records), 1)
                record = httpd.store.records[0]
                for key, value in envelope(
                        'op-receipt-replay', 'operator', 'advance_clock', body).items():
                    self.assertEqual(record[key], value)
                self.assertEqual(record['kind'], 'core_commit')
                self.assertEqual(record['machine'], 'integration_core')
                self.assertEqual(record['receiptDigest'], receipt_digest(receipt))
                original['receipt'] = receipt
                original['bytes'] = journal.read_bytes()
                original['records'] = list(httpd.store.records)

            def replay(httpd, port):
                self.assertEqual(httpd.store.records, original['records'])
                status, receipt, headers = post_call(
                    port, 'op-receipt-replay', 'operator', 'advance_clock', body,
                    headers={'X-Request-Id': 'req-receipt-replay'},
                )
                assert_gate_headers(self, headers)
                self.assertEqual(status, 200, receipt)
                self.assertEqual(receipt, original['receipt'])
                self.assertEqual(len(httpd.store.records), 1)
                self.assertEqual(httpd.store.records, original['records'])
                self.assertEqual(journal.read_bytes(), original['bytes'])

            with redirect_stderr(captured):
                run_with_server(commit, readiness_dir=tmp)
                run_with_server(replay, readiness_dir=tmp)
            self.assertEqual(journal.read_bytes(), original['bytes'])
        assert_journal_audit(self, captured, 'req-receipt-replay',
                             'replayed', domain)

    def test_checksum_valid_receipt_mismatch_refuses_startup(self):
        domain = load_catalogue(ROOT).domain
        control = {}

        def commit(httpd, port):
            status, receipt, headers = post_call(
                port, 'op-digest-control', 'operator', 'advance_clock',
                {'domain': domain, 'now': 27},
            )
            assert_gate_headers(self, headers)
            self.assertEqual(status, 200, receipt)
            self.assertEqual(len(httpd.store.records), 1)
            control.update(httpd.store.records[0])
            self.assertEqual(control['receiptDigest'], receipt_digest(receipt))

        with tempfile.TemporaryDirectory() as good, tempfile.TemporaryDirectory() as bad:
            run_with_server(commit, readiness_dir=good)
            wrong_digest = ('0' if control['receiptDigest'][0] != '0' else '1')
            wrong_digest += control['receiptDigest'][1:]
            record = {key: value for key, value in control.items()
                      if key not in ('schema', 'protocolTruth', 'productionConformance')}
            record['receiptDigest'] = wrong_digest
            store = ReadinessStore.open(bad)
            try:
                store.append(record)
            finally:
                store.close()
            journal = Path(bad) / 'journal.v1'
            before = journal.read_bytes()
            # Successful reopening proves framing, schema and CRC are valid.
            reopened = ReadinessStore.open(bad)
            try:
                self.assertEqual(reopened.records, [dict(control, receiptDigest=wrong_digest)])
            finally:
                reopened.close()
            self.assertEqual(journal.read_bytes(), before)
            failed = subprocess.run(
                [sys.executable, '-m', 'integration_gate', '--port', '0',
                 '--readiness-dir', bad],
                cwd=ROOT, capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(failed.returncode, 2, failed.stderr)
            self.assertIn('RECEIPT_MISMATCH', failed.stderr)
            self.assertNotIn('listening', failed.stdout + failed.stderr)
            self.assertEqual(journal.read_bytes(), before)

    def test_readiness_disabled_call_audits_inactive(self):
        domain = load_catalogue(ROOT).domain
        captured = io.StringIO()

        def run(_httpd, port):
            status, receipt, headers = post_call(
                port, 'op-inactive-audit', 'operator', 'advance_clock',
                {'domain': domain, 'now': 842173},
                headers={'X-Request-Id': 'req-inactive-audit'},
            )
            assert_gate_headers(self, headers)
            self.assertEqual(status, 200, receipt)
            self.assertEqual(receipt['result']['logicalTime'], 842173)

        with redirect_stderr(captured):
            run_with_server(run)
        assert_journal_audit(self, captured, 'req-inactive-audit', 'inactive', domain)

    def test_append_failure_diverges_and_blocks_subsequent_commands(self):
        domain = load_catalogue(ROOT).domain
        captured = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / 'journal.v1'
            original = {}

            def run(httpd, port):
                original['bytes'] = journal.read_bytes()
                self.assertEqual(httpd.store.records, [])
                with patch.object(httpd.store, 'append',
                                  side_effect=StoreError('JOURNAL_WRITE')) as append:
                    status, payload, headers = post_call(
                        port, 'op-append-failure', 'operator', 'advance_clock',
                        {'domain': domain, 'now': 953284},
                        headers={'X-Request-Id': 'req-diverged-audit'},
                    )
                    append.assert_called_once()
                assert_gate_headers(self, headers)
                self.assertEqual(status, 503)
                self.assertEqual(payload['error'], 'DURABILITY_DIVERGENCE')
                self.assertNotIn('result', payload)
                self.assertNotIn('sequence', payload)
                # The failure injection has ended; the process must stay fenced.
                for op, now in (('op-append-failure', 953284), ('op-after-failure', 953285)):
                    status, payload, headers = post_call(
                        port, op, 'operator', 'advance_clock',
                        {'domain': domain, 'now': now},
                    )
                    assert_gate_headers(self, headers)
                    self.assertEqual(status, 503)
                    self.assertEqual(payload['error'], 'NOT_READY')
                status, raw, headers = exchange(port, 'GET', READY_PATH)
                assert_gate_headers(self, headers)
                self.assertEqual(status, 503)
                self.assertEqual(parse_json(raw)['error'], 'NOT_READY')
                status, raw, headers = exchange(port, 'POST', READ_PREFIX + 'list_open_listings', {
                    'actor': 'viewer',
                })
                assert_gate_headers(self, headers)
                self.assertEqual((status, parse_json(raw)['error']), (503, 'NOT_READY'))
                self.assertEqual(httpd.store.records, [])
                self.assertEqual(journal.read_bytes(), original['bytes'])

            with redirect_stderr(captured):
                run_with_server(run, readiness_dir=tmp)
            self.assertEqual(journal.read_bytes(), original['bytes'])
        assert_journal_audit(self, captured, 'req-diverged-audit', 'diverged', domain)

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


class ResaleReadTransportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = parse_json((ROOT / 'reference/read_model/vectors/resale-read-transport.json').read_bytes())
        source = parse_json((ROOT / self.fixture['source']).read_bytes())
        self.writes = {item['id']: item['envelope'] for item in source['vectors']}

    def read(self, port, query, request, expected_status=200):
        status, raw, headers = exchange(port, 'POST', READ_PREFIX + query, request)
        self.assertEqual(status, expected_status, (query, raw))
        self.assertEqual(headers['cache-control'], 'no-store')
        assert_no_cors(self, headers)
        result = parse_json(raw)
        if 'body' in result:
            self.assertEqual(set(result), {
                'body', 'read_schema_version', 'fixture_mode', 'query_digest', 'accepted_through',
            })
            self.assertEqual(result['read_schema_version'], '0.1')
            self.assertEqual(result['fixture_mode'], 'REFERENCE_IN_MEMORY')
            self.assertEqual(result['query_digest'], receipt_digest({'query': query, 'input': request}))
        return result

    def write(self, port, call, expected_error=None, headers=None):
        status, raw, _ = exchange(port, 'POST', LOCAL_CALL_PATH, call, headers)
        result = parse_json(raw)
        if expected_error:
            self.assertEqual((status, result), (422, {'error': expected_error, 'rejected': True}))
        else:
            self.assertEqual(status, 200, result)
        return result

    def market_setup(self, port):
        for step_id in self.fixture['setup']:
            self.write(port, self.writes[step_id])

    def machine_states(self, httpd):
        return httpd.on_core(lambda: [
            httpd.core.snapshot(), *(machine.canonical_state() for machine in httpd.fsm.machines.values()),
        ], 2)

    def test_bound_companion_visibility_freshness_and_nonmutation(self):
        def run(httpd, port):
            self.market_setup(port)
            with self.subTest('recipient before transfer'):
                self.read(port, 'get_listing', {'actor': 'buyer-2', 'listing_id': 'list-1'}, 404)
            receipts = {}
            for step in self.fixture['bound_companion']:
                result = self.write(port, envelope(
                    'bound-' + step['id'], self.fixture['recovery']['actor'], step['action'], step['body'],
                ), step.get('error'))
                receipts[step['id']] = result
            self.assertEqual(result['listing']['settlement_id'], 'settle-read-1')
            self.assertEqual(result['listing']['settlement_gate'], 'MOCK_COMMIT_OBSERVED')

            before = self.machine_states(httpd)
            public = self.read(port, 'list_open_listings', {'actor': 'viewer'})
            resale = public['accepted_through']
            settlement = self.read(port, 'get_settlement', {'actor': 'organizer', 'listing_id': 'list-1'})
            cuts = {
                'future': {**resale, 'journal_entries': resale['journal_entries'] + 1},
                'settlement': settlement['accepted_through'],
            }
            self.assertEqual(set(resale), {'source', 'generation', 'journal_entries', 'logical_time_ms', 'token'})
            self.assertEqual(set(cuts['settlement']), {'source', 'generation', 'journal_entries', 'token'})
            self.assertEqual(resale['source'], 'resale')
            self.assertEqual(cuts['settlement']['source'], 'settlement')
            self.assertEqual(resale['logical_time_ms'], 1000000)
            self.assertEqual(cuts['settlement']['journal_entries'], 4)
            recovered = self.read(port, 'get_operation_recovery', {
                'actor': self.fixture['recovery']['actor'], 'operation_id': 'bound-commit',
                'subject': {'action': 'settlement_commit', 'field': 'settlement_id', 'id': 'settle-read-1'},
                'through': cuts['settlement'],
            })
            self.assertEqual(recovered['body']['receipt'], receipts['commit'])
            for vector in self.fixture['bound_reads']:
                with self.subTest(vector['id']):
                    request = {**vector['request']}
                    if 'watermark' in vector:
                        request['minimum_watermark'] = cuts[vector['watermark']]
                    result = self.read(port, vector['query'], request, vector.get('status', 200))
                    if 'error' in vector:
                        self.assertEqual(result, {'error': vector['error'], 'rejected': True})
                    for path, expected in vector.get('expect', {}).items():
                        actual = result
                        for field in path.split('.'):
                            actual = actual[field]
                        self.assertEqual(actual, expected, path)
            self.assertEqual(self.machine_states(httpd), before)

        run_with_server(run)

    def test_historical_market_transfer_keeps_null_settlement(self):
        def run(_httpd, port):
            self.market_setup(port)
            receipt = self.write(port, self.writes[self.fixture['original_transfer']])
            listing = self.read(port, 'get_listing', {'actor': 'buyer-2', 'listing_id': 'list-1'})
            for view in (receipt['listing'], listing['body']):
                self.assertIsNone(view['settlement_id'])
                self.assertEqual(view['settlement_gate'], 'UNBOUND')
            self.assertEqual(self.read(port, 'get_settlement', {
                'actor': 'organizer', 'listing_id': 'list-1',
            }, 404), {'error': 'NOT_FOUND', 'rejected': True})

        run_with_server(run)

    def test_unrelated_settlement_binding_is_not_visible(self):
        def run(httpd, port):
            self.market_setup(port)
            for step in self.fixture['bound_companion'][:4]:
                body = step['body']
                if step['id'] == 'initiate':
                    body = {**body, **self.fixture['unrelated_settlement']['initiate_overrides']}
                self.write(port, envelope('unrelated-' + step['id'], 'fixture', step['action'], body))
            listing = self.read(port, 'get_listing', {'actor': 'buyer-1', 'listing_id': 'list-1'})
            self.assertEqual(listing['body']['settlement_id'], 'settle-read-1')
            before = self.machine_states(httpd)
            for request in self.fixture['unrelated_settlement']['denied_reads']:
                with self.subTest(request=request):
                    result = self.read(port, 'get_settlement', request, 404)
                    self.assertEqual(result, {'error': 'NOT_FOUND', 'rejected': True})
            self.assertEqual(self.machine_states(httpd), before)

        run_with_server(run)

    def test_open_list_pagination_and_cursor_fences(self):
        journey = parse_json((ROOT / 'reference/booking_resale_admission/fixtures/'
                              'commerce_journey_conformance_v1.json').read_bytes())
        steps = {step['id']: step for step in journey['steps']}

        def run(httpd, port):
            def invoke(step, **updates):
                item = steps[step]
                return self.write(port, envelope(step + str(bool(updates)), 'fixture', item['action'], {
                    **item['body'], **updates,
                }))

            request = {'actor': 'viewer'}
            empty = self.read(port, 'list_open_listings', request)
            self.assertEqual(empty['body'], {'entries': [], 'next_cursor': None, 'truncated': False})
            for step in journey['steps'][:16]:
                invoke(step['id'])
            invoke('adopt-A', right_id='issue-B', idempotency_key='key-adopt-B', reservation_id='reserve-B',
                   slot=1, buyer_role='buyer-B', order_id='order-B', quote_ref='quote-B',
                   payment_ref=steps['payment-B']['body']['payment_ref'])
            invoke('list-A', listing_id='000-listing-B', idempotency_key='key-list-B', right_id='issue-B',
                   seller_role='buyer-B', recipient_role='buyer-A', reservation_id='reserve-B')
            before = self.machine_states(httpd)
            first = self.read(port, 'list_open_listings', {
                **request, 'limit': 1, 'minimum_watermark': empty['accepted_through'],
            })
            page = first['body']
            self.assertTrue(page['truncated'])
            self.assertEqual(page['entries'], [{
                'listing_id': 'listing-A', 'show_id': 'show-journey', 'phase': 'LISTED',
                'amount': 12000, 'currency': 'KRW', 'expires_ms': 1900000, 'expired': False,
            }])
            next_page = {**request, 'limit': 1, 'cursor': page['next_cursor']}
            second = self.read(port, 'list_open_listings', next_page)
            self.assertEqual(second['accepted_through'], first['accepted_through'])
            self.assertEqual([row['listing_id'] for row in second['body']['entries']], ['000-listing-B'])
            self.assertIsNone(second['body']['next_cursor'])
            self.assertFalse(second['body']['truncated'])
            self.assertEqual(self.machine_states(httpd), before)
            for change in ({'actor': 'other'}, {'limit': 2}, {'cursor': 'A' * 54}):
                self.assertEqual(self.read(port, 'list_open_listings', {**next_page, **change}, 422)['error'],
                                 'READ_CURSOR_REFUSED')
            for limit in (0, 101, True, 1.5):
                self.assertEqual(self.read(port, 'list_open_listings', {**request, 'limit': limit}, 400)['error'],
                                 'READ_REQUEST_INVALID')
            invoke('hold-A')
            self.assertEqual(self.read(port, 'list_open_listings', next_page, 422)['error'], 'READ_CURSOR_REFUSED')
            for step in (None, 'resale-payment-A'):
                if step:
                    invoke(step)
                result = self.read(port, 'list_open_listings', request)
                self.assertEqual([row['listing_id'] for row in result['body']['entries']], ['000-listing-B'])
            invoke('resale-clock', now_ms=1900000, idempotency_key='key-expire')
            self.assertEqual(self.read(port, 'list_open_listings', request)['body']['entries'], [])

        run_with_server(run)

    def test_lost_reply_recovery_never_replays_or_exposes_mismatches(self):
        unknown = {'status': 'UNKNOWN', 'retry_granted': False}
        subject = self.fixture['recovery']['subject']
        trace_id = self.fixture['recovery']['trace_id']
        actor = self.fixture['recovery']['actor']
        original = self.writes[self.fixture['original_transfer']]
        query = 'get_operation_recovery'
        public = {'actor': 'viewer'}
        previous_process = {}

        def run(httpd, port):
            self.market_setup(port)
            before = self.read(port, 'list_open_listings', public)['accepted_through']
            first = []
            send = GateHandler._send

            def withhold_reply(handler, status, payload, **kwargs):
                if handler.request_id == trace_id and status == 200:
                    first.append(payload)
                    handler.close_connection = True
                    return
                send(handler, status, payload, **kwargs)

            with patch.object(GateHandler, '_send', withhold_reply):
                with self.assertRaises(RemoteDisconnected):
                    self.write(port, original, headers={'X-Request-Id': trace_id})
            self.assertEqual(len(first), 1)
            self.assertFalse(first[0]['duplicate'])
            through = self.read(port, 'list_open_listings', public)['accepted_through']
            request = {'actor': actor, 'subject': subject, 'through': through}
            previous_process.update(request, operation_id=original['operationId'])
            after = self.machine_states(httpd)
            for key in ({'operation_id': original['operationId']}, {'trace_id': trace_id}):
                result = self.read(port, query, {**request, **key})
                self.assertEqual(result['accepted_through'], through)
                self.assertEqual(result['body'], {'status': 'ACCEPTED', 'retry_granted': False, 'receipt': first[0]})
            for changes in (
                {'actor': 'outsider'}, {'through': before}, {'operation_id': 'miss'},
                {'subject': {**subject, 'id': 'other'}}, {'subject': {**subject, 'field': 'listing_id'}},
                {'through': {**through, 'token': '0' * 64}},
            ):
                self.assertEqual(self.read(port, query, {**previous_process, **changes}), unknown)
            for malformed in (request, {**previous_process, 'trace_id': trace_id}):
                self.assertEqual(self.read(port, query, malformed, 400)['error'], 'READ_REQUEST_INVALID')
            self.assertEqual(self.machine_states(httpd), after)

            replay = self.write(port, {**original, 'operationId': 'new-operation'},
                                headers={'X-Request-Id': 'new-trace'})
            self.assertTrue(replay['duplicate'])
            self.assertEqual(self.read(port, query, {**previous_process, 'operation_id': 'new-operation'}), unknown)
            self.assertEqual(self.read(port, query, {**request, 'trace_id': 'new-trace'}), unknown)
            self.assertEqual(self.read(port, query, previous_process)['body']['receipt'], first[0])
            self.write(port, {**original, 'actor': 'another-actor'}, headers={'X-Request-Id': trace_id})
            self.assertEqual(self.read(port, query, previous_process), unknown)
            self.assertEqual(self.read(port, query, {**request, 'trace_id': trace_id}), unknown)
            self.assertEqual(self.machine_states(httpd), after)

        run_with_server(run)

        def restarted(_httpd, port):
            self.assertEqual(self.read(port, query, previous_process), unknown)
            self.assertEqual(self.read(port, 'list_open_listings', {
                **public, 'minimum_watermark': previous_process['through'],
            }, 422)['error'], 'READ_WATERMARK_UNMET')

        run_with_server(restarted)

    def test_recovery_eviction_and_capacity_fail_closed(self):
        def run(_httpd, port):
            def clock(n):
                self.write(port, envelope(f'clock-{n}', 'actor', 'resale_set_clock', {
                    'subject_id': 'clock', 'idempotency_key': f'clock-{n}', 'now_ms': n,
                }))

            def recovery(n):
                watermark = self.read(port, 'list_open_listings', {'actor': 'actor'})['accepted_through']
                return self.read(port, 'get_operation_recovery', {
                    'actor': 'actor', 'operation_id': f'clock-{n}', 'through': watermark,
                    'subject': {'action': 'resale_set_clock', 'field': 'subject_id', 'id': 'clock'},
                })

            clock(1)
            self.assertEqual(recovery(1)['body']['receipt']['logical_time_ms'], 1)
            clock(2)
            unknown = {'status': 'UNKNOWN', 'retry_granted': False}
            self.assertEqual(recovery(1), unknown)
            self.assertEqual(recovery(2)['body']['status'], 'ACCEPTED')
            clock(3)
            self.assertEqual(recovery(3), unknown)
            self.assertEqual(recovery(2)['body']['status'], 'ACCEPTED')

        with patch('integration_gate.resale_reads.RECOVERY_RECEIPTS', 1), patch(
            'integration_gate.resale_reads.RECOVERY_IDENTITIES', 4
        ):
            run_with_server(run)

    def test_write_deadline_fences_writes_but_worker_can_serve_recovery(self):
        original = self.writes[self.fixture['original_transfer']]
        trace_id = self.fixture['recovery']['trace_id']
        public = {'actor': 'viewer'}

        def run(httpd, port):
            self.market_setup(port)
            before = self.read(port, 'list_open_listings', public)['accepted_through']
            started = threading.Event()
            finish = threading.Event()
            receipts = []
            call = httpd.fsm.call

            def delayed_call(action, body):
                self.assertEqual(action, original['action'])
                started.set()
                self.assertTrue(finish.wait(5))
                receipt = call(action, body)
                receipts.append(receipt)
                return receipt

            with (
                patch.object(httpd.fsm, 'call', delayed_call),
                patch.object(httpd, 'request_timeout_seconds', 0.25),
            ):
                try:
                    status, raw, _ = exchange(port, 'POST', LOCAL_CALL_PATH, original, {'X-Request-Id': trace_id})
                    self.assertEqual((status, parse_json(raw)), (503, {'error': 'CORE_BUSY', 'rejected': True}))
                    self.assertTrue(started.is_set())
                    self.assertEqual(receipts, [])
                    busy = self.read(port, 'list_open_listings', public, 503)
                    self.assertEqual(busy['error'], 'CORE_BUSY')
                finally:
                    finish.set()
                httpd.on_core(lambda: None, 2)  # Work queued after the retained receipt.

            self.assertEqual(exchange(port, 'GET', READY_PATH)[0], 503)
            status, raw, _ = exchange(port, 'POST', LOCAL_CALL_PATH, original)
            self.assertEqual((status, parse_json(raw)['error']), (503, 'NOT_READY'))
            through = self.read(port, 'list_open_listings', public)['accepted_through']
            self.assertEqual(through['journal_entries'], before['journal_entries'] + 1)
            state = self.machine_states(httpd)
            recovery = self.fixture['recovery']
            self.assertEqual(self.read(port, 'get_operation_recovery', {**recovery, 'through': before}), {
                'status': 'UNKNOWN', 'retry_granted': False,
            })
            request = {'actor': recovery['actor'], 'subject': recovery['subject'], 'through': through}
            for selector in ({'trace_id': trace_id}, {'operation_id': original['operationId']}):
                result = self.read(port, 'get_operation_recovery', {**request, **selector})
                self.assertEqual(result['body'], {'status': 'ACCEPTED', 'retry_granted': False, 'receipt': receipts[0]})
            self.assertEqual(self.machine_states(httpd), state)

        run_with_server(run)

    def test_read_transport_limits_and_browser_scope(self):
        path = READ_PREFIX + 'get_listing'
        request = {'actor': 'fixture', 'listing_id': 'listing'}

        def run(_httpd, port):
            for method, target, status in (
                ('GET', path, 405), ('POST', path + '?value=1', 400), ('POST', READ_PREFIX + 'offers', 404),
            ):
                self.assertEqual(exchange(port, method, target, request)[0], status)
            self.assertEqual(self.read(port, 'get_listing', {**request, 'unexpected': 1}, 400)['error'],
                             'READ_REQUEST_INVALID')
            self.assertEqual(self.read(port, 'get_listing', {**request, 'actor': '\ud800'}, 400)['error'],
                             'INVALID_ID')
            for method, payload, status in (('OPTIONS', None, 405), ('POST', request, 404)):
                actual, _, headers = exchange(port, method, path, payload, {
                    'Origin': BROWSER_ALLOWED_ORIGIN, 'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'content-type',
                })
                self.assertEqual(actual, status)
                assert_no_cors(self, headers)

        run_with_server(run, browser_origin=BROWSER_ALLOWED_ORIGIN)
        with tempfile.TemporaryDirectory() as directory:
            run_with_server(lambda _httpd, port: self.assertEqual(
                self.read(port, 'get_listing', request, 422)['error'], READINESS_FSM_REFUSED,
            ), readiness_dir=directory)


class BrowserAccessTests(unittest.TestCase):
    def test_flag_off_keeps_today_including_origin_and_hostile_host(self):
        domain = load_catalogue(ROOT).domain

        def run(_httpd, port):
            for path, allow in (
                (LOCAL_CALL_PATH, 'POST'),
                (HEALTH_PATH, 'GET'),
                (READY_PATH, 'GET'),
            ):
                status, raw, headers = exchange(
                    port, 'OPTIONS', path,
                    headers={
                        'Origin': BROWSER_ALLOWED_ORIGIN,
                        'Access-Control-Request-Method': allow,
                    },
                )
                self.assertEqual(status, 405, path)
                self.assertEqual(parse_json(raw)['error'], 'METHOD_NOT_ALLOWED')
                self.assertEqual(headers.get('allow'), allow)
                assert_no_cors(self, headers)
            status, raw, headers = exchange(
                port, 'GET', HEALTH_PATH, headers={'Origin': BROWSER_ALLOWED_ORIGIN}
            )
            self.assertEqual(status, 200)
            self.assertEqual(parse_json(raw)['status'], 'up')
            assert_no_cors(self, headers)
            status, payload, headers = post_call(
                port, 'op-off', 'operator', 'advance_clock',
                {'domain': domain, 'now': 1},
                headers={'Origin': BROWSER_ALLOWED_ORIGIN},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)
            assert_no_cors(self, headers)
            for host in _host_cases(port):
                status, body, _headers, _seen = self._raw(
                    port, 'GET', HEALTH_PATH, host, origin=BROWSER_ALLOWED_ORIGIN
                )
                self.assertEqual(status, 200, host)
                self.assertEqual(parse_json(body)['status'], 'up')
                assert_no_cors(self, _headers)

        run_with_server(run)

    def test_preflight_for_the_allowed_origin(self):
        def run(_httpd, port):
            for path, method in (
                (LOCAL_CALL_PATH, 'POST'),
                (HEALTH_PATH, 'GET'),
                (READY_PATH, 'GET'),
            ):
                status, body, headers, seen = self._raw(
                    port, 'OPTIONS', path,
                    ['Host: 127.0.0.1:%d' % port],
                    origin=BROWSER_ALLOWED_ORIGIN,
                    extra=['Access-Control-Request-Method: ' + method],
                )
                self.assertEqual(status, 204, path)
                self.assertEqual(body, b'')
                self.assertEqual(seen.count('access-control-allow-origin'), 1)
                self._assert_preflight(headers, seen, method)
            status, body, headers, seen = self._raw(
                port, 'OPTIONS', LOCAL_CALL_PATH,
                ['Host: 127.0.0.1'],
                origin=BROWSER_ALLOWED_ORIGIN,
                extra=[
                    'Access-Control-Request-Method: POST',
                    'Access-Control-Request-Headers: Content-Type , X-Request-Id',
                ],
            )
            self.assertEqual(status, 204)
            self.assertEqual(body, b'')
            self._assert_preflight(headers, seen, 'POST')
            status, _body, headers, seen = self._raw(
                port, 'OPTIONS', HEALTH_PATH,
                ['Host: 127.0.0.1:%d' % port],
                origin=BROWSER_ALLOWED_ORIGIN,
                extra=[
                    'Access-Control-Request-Method: GET',
                    'Access-Control-Request-Headers: content-type, x-request-id, x-correlation-id',
                ],
            )
            self.assertEqual(status, 204)
            self._assert_preflight(headers, seen, 'GET')

        run_with_server(run, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_preflight_does_not_take_an_admit_slot_or_advance_the_core(self):
        domain = load_catalogue(ROOT).domain

        def run(httpd, port):
            self.assertEqual(httpd.try_admit(), 'OK')
            try:
                status, body, headers, _seen = self._raw(
                    port, 'OPTIONS', LOCAL_CALL_PATH,
                    ['Host: 127.0.0.1:%d' % port],
                    origin=BROWSER_ALLOWED_ORIGIN,
                    extra=['Access-Control-Request-Method: POST'],
                )
                self.assertEqual(status, 204)
                self.assertEqual(body, b'')
                self.assertEqual(
                    headers.get('access-control-allow-origin'), BROWSER_ALLOWED_ORIGIN
                )
            finally:
                httpd.release_admit()
            status, payload, _headers = post_call(
                port, 'op-after-preflight', 'operator', 'advance_clock',
                {'domain': domain, 'now': 2},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)
            self.assertEqual(payload['result']['logicalTime'], 2)

        run_with_server(run, max_in_flight=1, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_refused_origins_and_preflight_shapes_stay_closed(self):
        origins = [
            'http://localhost:5173',
            'http://[::1]:5173',
            'https://127.0.0.1:5173',
            'http://127.0.0.1:5174',
            'null',
            'chrome-extension://x',
            'http://192.168.0.8:5173',
            'http://127.0.0.1:5173/',
            'http://127.0.0.1:5173 ',
            'http://user@127.0.0.1:5173',
            'HTTP://127.0.0.1:5173',
        ]

        def run(_httpd, port):
            host = ['Host: 127.0.0.1:%d' % port]
            for origin in origins:
                status, body, headers, _seen = self._raw(
                    port, 'OPTIONS', LOCAL_CALL_PATH, host,
                    origin=origin,
                    extra=['Access-Control-Request-Method: POST'],
                )
                self.assertEqual(status, 405, origin)
                self.assertEqual(parse_json(body)['error'], 'METHOD_NOT_ALLOWED')
                self.assertEqual(headers.get('allow'), 'POST')
                assert_no_cors(self, headers)
            status, body, headers, _seen = self._raw(
                port, 'OPTIONS', LOCAL_CALL_PATH, host,
                extra=['Access-Control-Request-Method: POST'],
            )
            self.assertEqual(status, 405)
            self.assertEqual(headers.get('allow'), 'POST')
            assert_no_cors(self, headers)
            status, body, headers, _seen = self._raw(
                port, 'OPTIONS', LOCAL_CALL_PATH,
                host + [
                    'Origin: ' + BROWSER_ALLOWED_ORIGIN,
                    'Origin: ' + BROWSER_ALLOWED_ORIGIN,
                ],
                extra=['Access-Control-Request-Method: POST'],
            )
            self.assertEqual(status, 405)
            self.assertEqual(headers.get('allow'), 'POST')
            assert_no_cors(self, headers)
            shapes = [
                ['Access-Control-Request-Method: PUT'],
                ['Access-Control-Request-Method: POST', 'Access-Control-Request-Method: POST'],
                ['Access-Control-Request-Method: POST', 'Access-Control-Request-Headers: authorization'],
                ['Access-Control-Request-Method: POST', 'Access-Control-Request-Headers: cookie'],
                ['Access-Control-Request-Method: POST',
                 'Access-Control-Request-Headers: content-type, content-type'],
                ['Access-Control-Request-Method: POST', 'Access-Control-Request-Headers:'],
                ['Access-Control-Request-Method: POST',
                 'Access-Control-Request-Headers: content-type',
                 'Access-Control-Request-Headers: x-request-id'],
                ['Access-Control-Request-Method: POST',
                 'Access-Control-Request-Private-Network: true'],
                ['Access-Control-Request-Method: GET'],
            ]
            for extra in shapes:
                status, body, headers, _seen = self._raw(
                    port, 'OPTIONS', LOCAL_CALL_PATH, host,
                    origin=BROWSER_ALLOWED_ORIGIN,
                    extra=extra,
                )
                self.assertEqual(status, 405, extra)
                self.assertEqual(parse_json(body)['error'], 'METHOD_NOT_ALLOWED')
                self.assertEqual(headers.get('allow'), 'POST')
                assert_no_cors(self, headers)
            status, body, headers, _seen = self._raw(
                port, 'OPTIONS', HEALTH_PATH, host,
                origin=BROWSER_ALLOWED_ORIGIN,
                extra=['Access-Control-Request-Method: POST'],
            )
            self.assertEqual(status, 405)
            self.assertEqual(headers.get('allow'), 'GET')
            assert_no_cors(self, headers)

        run_with_server(run, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_real_responses_add_cors_only_for_the_allowed_origin(self):
        domain = load_catalogue(ROOT).domain
        missing = {'domain': domain, 'eventId': 'missing'}

        def run(httpd, port):
            status, raw, headers = exchange(port, 'GET', HEALTH_PATH)
            self.assertEqual(status, 200)
            assert_no_cors(self, headers)
            status_on, raw_on, headers_on = exchange(
                port, 'GET', HEALTH_PATH, headers={'Origin': BROWSER_ALLOWED_ORIGIN}
            )
            self.assertEqual(status_on, 200)
            self.assertEqual(raw_on, raw)
            self._assert_simple_cors(headers_on)
            status_other, raw_other, headers_other = exchange(
                port, 'GET', HEALTH_PATH, headers={'Origin': 'http://localhost:5173'}
            )
            self.assertEqual(status_other, 200)
            self.assertEqual(raw_other, raw)
            assert_no_cors(self, headers_other)

            def paired(method, path, payload, origin_headers, plain_headers=None):
                status_a, raw_a, headers_a = exchange(
                    port, method, path, payload=payload, headers=origin_headers
                )
                wait_admit_idle(httpd)
                status_b, raw_b, headers_b = exchange(
                    port, method, path, payload=payload, headers=plain_headers
                )
                wait_admit_idle(httpd)
                self.assertEqual(status_a, status_b)
                self.assertEqual(raw_a, raw_b)
                self._assert_simple_cors(headers_a)
                assert_no_cors(self, headers_b)
                return status_a, parse_json(raw_a)

            status, payload = paired(
                'POST', LOCAL_CALL_PATH, {},
                {'Origin': BROWSER_ALLOWED_ORIGIN},
            )
            self.assertEqual(status, 400)
            self.assertEqual(payload['error'], 'ENVELOPE_INVALID')
            status, payload = paired(
                'POST', LOCAL_CALL_PATH, {},
                {'Origin': BROWSER_ALLOWED_ORIGIN, 'Content-Type': 'text/plain'},
                {'Content-Type': 'text/plain'},
            )
            self.assertEqual(status, 415)
            self.assertEqual(payload['error'], 'UNSUPPORTED_MEDIA_TYPE')
            status_a, payload_a, headers_a = post_call(
                port, 'op-miss-a', 'operator', 'cancel_event', missing,
                headers={'Origin': BROWSER_ALLOWED_ORIGIN},
            )
            wait_admit_idle(httpd)
            status_b, payload_b, headers_b = post_call(
                port, 'op-miss-b', 'operator', 'cancel_event', missing,
            )
            wait_admit_idle(httpd)
            self.assertEqual(status_a, 422)
            self.assertEqual(status_b, 422)
            self.assertEqual(payload_a, payload_b)
            self.assertEqual(payload_a['error'], 'EVENT_NOT_FOUND')
            self._assert_simple_cors(headers_a)
            assert_no_cors(self, headers_b)
            status, payload, headers = post_call(
                port, 'op-ok', 'operator', 'advance_clock',
                {'domain': domain, 'now': 6},
                headers={'Origin': BROWSER_ALLOWED_ORIGIN},
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload['sequence'], 1)
            self.assertEqual(payload['result']['logicalTime'], 6)
            self.assertNotIn('rejected', payload)
            self._assert_simple_cors(headers)
            wait_admit_idle(httpd)
            self.assertEqual(httpd.try_admit(), 'OK')
            try:
                status, payload, headers = post_call(
                    port, 'op-busy', 'operator', 'advance_clock',
                    {'domain': domain, 'now': 7},
                    headers={'Origin': BROWSER_ALLOWED_ORIGIN},
                )
                self.assertEqual(status, 503)
                self.assertEqual(payload['error'], 'OVERLOADED')
                self._assert_simple_cors(headers)
                status_plain, payload_plain, headers_plain = post_call(
                    port, 'op-busy-plain', 'operator', 'advance_clock',
                    {'domain': domain, 'now': 8},
                )
                self.assertEqual(status_plain, 503)
                self.assertEqual(payload_plain, payload)
                assert_no_cors(self, headers_plain)
            finally:
                httpd.release_admit()

        run_with_server(run, max_in_flight=1, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_response_can_complete_while_admit_slot_is_held(self):
        """Characterization of the current handler order, not a contract claim.

        GateHandler writes the response and only then releases the admit slot.
        docs/contracts/READINESS_RUNTIME.md does not define that order.
        """
        domain = load_catalogue(ROOT).domain
        release_gate = threading.Event()

        def run(httpd, port):
            original = httpd.release_admit

            def blocking_release():
                release_gate.wait()
                original()

            httpd.release_admit = blocking_release
            try:
                status, raw, _headers = exchange(
                    port, 'POST', LOCAL_CALL_PATH, payload={},
                    headers={'Content-Type': 'text/plain'},
                )
                self.assertEqual(status, 415)
                self.assertEqual(parse_json(raw)['error'], 'UNSUPPORTED_MEDIA_TYPE')
                self.assertEqual(httpd.admit.view()['inFlight'], 1)
                with self.assertRaises(AssertionError) as caught:
                    wait_admit_idle(httpd, timeout=0.2)
                self.assertEqual(str(caught.exception), 'admit slot not released')
                release_gate.set()
                wait_admit_idle(httpd)
                status, _payload, _headers = post_call(
                    port, 'op-after-release', 'operator', 'advance_clock',
                    {'domain': domain, 'now': 1},
                )
                self.assertEqual(status, 200)
            finally:
                release_gate.set()

        run_with_server(run, max_in_flight=1, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_existing_rejections_stay_ahead_of_cors_and_preflight(self):
        def run(_httpd, port):
            host = 'Host: 127.0.0.1:%d' % port
            cases = [
                ('OPTIONS', '/health?ready=1', [host], 400, 'QUERY_NOT_ALLOWED'),
                ('OPTIONS', '/no-such', [host], 404, 'NOT_FOUND'),
                (
                    'OPTIONS', HEALTH_PATH,
                    [host, 'Expect: 100-continue'],
                    417, 'EXPECTATION_FAILED',
                ),
                (
                    'OPTIONS', HEALTH_PATH,
                    [host, 'Transfer-Encoding: chunked'],
                    400, 'UNSUPPORTED_TRANSFER',
                ),
                (
                    'OPTIONS', HEALTH_PATH,
                    [host, 'X-Pad: ' + ('a' * (HEADER_LIMIT_BYTES + 64))],
                    431, 'HEADER_TOO_LARGE',
                ),
            ]
            for method, path, fields, status_code, error in cases:
                status, body, headers, _seen = self._raw(
                    port, method, path, fields,
                    origin=BROWSER_ALLOWED_ORIGIN,
                    extra=['Access-Control-Request-Method: GET'],
                )
                self.assertEqual(status, status_code, path)
                self.assertEqual(parse_json(body)['error'], error)
                assert_no_cors(self, headers)
            line = b'GET /' + (b'a' * 70000) + b' HTTP/1.1\r\n'
            status, _body, blob = raw_http(port, line)
            self.assertEqual(status, 414)
            self.assertNotIn(b'access-control-', blob.lower())
            self.assertNotIn(b'\r\nvary:', blob.lower())
            status, _body, blob = raw_http(port, b'BAD\r\n\r\n')
            self.assertEqual(status, 400)
            self.assertNotIn(b'access-control-', blob.lower())
            self.assertNotIn(b'\r\nvary:', blob.lower())

        run_with_server(run, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_host_check_applies_only_when_the_flag_is_on(self):
        def run(_httpd, port):
            for host in _host_cases(port):
                allowed = host in (
                    ['Host: 127.0.0.1'],
                    ['Host: 127.0.0.1:%d' % port],
                )
                status, body, headers, _seen = self._raw(
                    port, 'GET', HEALTH_PATH, host, origin=BROWSER_ALLOWED_ORIGIN
                )
                if allowed:
                    self.assertEqual(status, 200, host)
                    self.assertEqual(parse_json(body)['status'], 'up')
                    self._assert_simple_cors(headers)
                else:
                    self.assertEqual(status, 400, host)
                    self.assertEqual(parse_json(body)['error'], 'BAD_REQUEST')
                    assert_no_cors(self, headers)
            status, body, headers, _seen = self._raw(
                port, 'OPTIONS', LOCAL_CALL_PATH,
                ['Host: localhost:%d' % port],
                origin=BROWSER_ALLOWED_ORIGIN,
                extra=['Access-Control-Request-Method: POST'],
            )
            self.assertEqual(status, 400)
            self.assertEqual(parse_json(body)['error'], 'BAD_REQUEST')
            assert_no_cors(self, headers)

        run_with_server(run, browser_origin=BROWSER_ALLOWED_ORIGIN)

    def test_startup_refuses_any_browser_origin_other_than_the_one_value(self):
        refused = [
            ['--browser-origin', 'http://localhost:5173'],
            ['--browser-origin', ''],
            ['--browser-origin', BROWSER_ALLOWED_ORIGIN, '--browser-origin', BROWSER_ALLOWED_ORIGIN],
            ['--browser-origin', BROWSER_ALLOWED_ORIGIN + '/'],
            ['--browser-origin', '*'],
        ]
        for argv in refused:
            buf = io.StringIO()
            with redirect_stderr(buf):
                code = main(argv + ['--port', '9'])
            self.assertEqual(code, 2, argv)
            self.assertIn('REFUSING_BROWSER_ORIGIN', buf.getvalue())
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = main([
                '--host', '0.0.0.0',
                '--browser-origin', BROWSER_ALLOWED_ORIGIN,
                '--port', '9',
            ])
        self.assertEqual(code, 2)
        self.assertIn('REFUSING_NON_LOOPBACK_BIND', buf.getvalue())
        self.assertNotIn('REFUSING_BROWSER_ORIGIN', buf.getvalue())

    def test_environment_does_not_enable_browser_origin(self):
        names = {
            'BROWSER_ORIGIN': BROWSER_ALLOWED_ORIGIN,
            'KIX_BROWSER_ORIGIN': BROWSER_ALLOWED_ORIGIN,
            'INTEGRATION_GATE_BROWSER_ORIGIN': BROWSER_ALLOWED_ORIGIN,
        }
        with patch.dict('os.environ', names):
            proc, port = start_process()
        try:
            status, raw, headers = exchange(
                port, 'OPTIONS', HEALTH_PATH,
                headers={
                    'Origin': BROWSER_ALLOWED_ORIGIN,
                    'Access-Control-Request-Method': 'GET',
                },
            )
            self.assertEqual(status, 405)
            self.assertEqual(parse_json(raw)['error'], 'METHOD_NOT_ALLOWED')
            self.assertEqual(headers.get('allow'), 'GET')
            assert_no_cors(self, headers)
        finally:
            stop_process(proc)

    def test_subprocess_flag_serves_the_opt_in_preflight(self):
        proc, port = start_process(['--browser-origin', BROWSER_ALLOWED_ORIGIN])
        try:
            status, body, headers, seen = self._raw(
                port, 'OPTIONS', READY_PATH,
                ['Host: 127.0.0.1:%d' % port],
                origin=BROWSER_ALLOWED_ORIGIN,
                extra=['Access-Control-Request-Method: GET'],
            )
            self.assertEqual(status, 204)
            self.assertEqual(body, b'')
            self._assert_preflight(headers, seen, 'GET')
        finally:
            stop_process(proc)

    def _raw(self, port, method, path, host_lines, origin=None, extra=None):
        fields = list(host_lines)
        if origin is not None:
            fields.append('Origin: ' + origin)
        if extra:
            fields.extend(extra)
        _status, _body, blob = raw_http(port, raw_message(method, path, fields))
        return parse_response(blob)

    def _assert_simple_cors(self, headers):
        self.assertEqual(headers.get('access-control-allow-origin'), BROWSER_ALLOWED_ORIGIN)
        self.assertEqual(headers.get('vary'), 'Origin')
        for key in headers:
            if key.startswith('access-control-') and key != 'access-control-allow-origin':
                self.fail(key)
        self.assertNotIn('*', headers.get('access-control-allow-origin', ''))

    def _assert_preflight(self, headers, seen, method):
        self.assertEqual(set(seen), {
            'connection',
            'cache-control',
            'x-content-type-options',
            'x-kix-transport',
            'x-kix-production-endpoint',
            'x-kix-protocol-truth',
            'x-kix-production-conformance',
            'x-request-id',
            'x-correlation-id',
            'access-control-allow-origin',
            'vary',
            'access-control-allow-methods',
            'access-control-allow-headers',
            'allow',
        })
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(headers['access-control-allow-origin'], BROWSER_ALLOWED_ORIGIN)
        self.assertEqual(headers['access-control-allow-methods'], method)
        self.assertEqual(
            headers['access-control-allow-headers'],
            ', '.join(BROWSER_ALLOWED_REQUEST_HEADERS),
        )
        self.assertEqual(headers['allow'], method)
        self.assertEqual(headers['vary'], 'Origin')
        self.assertEqual(headers['cache-control'], 'no-store')
        self.assertEqual(headers['x-content-type-options'], 'nosniff')
        self.assertEqual(headers['x-kix-transport'], 'integration-gate')
        self.assertEqual(headers['x-kix-production-endpoint'], 'false')
        self.assertEqual(headers['x-kix-protocol-truth'], 'false')
        self.assertEqual(headers['x-kix-production-conformance'], 'false')
        self.assertEqual(headers['connection'], 'close')
        self.assertTrue(headers['x-request-id'])
        self.assertEqual(headers['x-correlation-id'], headers['x-request-id'])
        self.assertNotIn('content-type', headers)
        self.assertNotIn('content-length', headers)
        for banned in (
            'access-control-allow-credentials',
            'access-control-allow-private-network',
            'access-control-max-age',
            'access-control-expose-headers',
        ):
            self.assertNotIn(banned, headers)
        self.assertNotIn('*', ''.join(headers.values()))


def _host_cases(port):
    return [
        ['Host: evil.example'],
        [],
        ['Host: 127.0.0.1', 'Host: 127.0.0.1'],
        ['Host: 127.0.0.1:1' if port != 1 else 'Host: 127.0.0.1:2'],
        ['Host: localhost:%d' % port],
        ['Host: 127.0.0.1.evil.example'],
        ['Host: 127.0.0.1'],
        ['Host: 127.0.0.1:%d' % port],
    ]


if __name__ == '__main__':
    unittest.main()
